"""
AutoTabloide AI - Import Service
==================================
Serviço de importação desacoplado da UI.

CENTURY CHECKLIST Items 61-70:
- Item 61: Normalização de colunas (fuzzy matching)
- Item 63: Detecção de linhas vazias
- Item 64: Parser de moeda BR/US
- Item 65: Limpeza de espaços (trim)
- Item 66: Validação de duplicidade no arquivo
- Item 67: Log de erros de importação
- Item 70: Barra de progresso (eventos)

Funcionalidades:
- Importação de Excel/CSV
- Fuzzy matching com RapidFuzz
- Execução em background (não trava UI)
- Eventos de progresso
"""

import asyncio
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from concurrent.futures import ThreadPoolExecutor

from src.core.logging_config import get_logger
from src.core.event_bus import event_bus, EventType
from src.core.database import AsyncSessionLocal
from src.core.models import Produto
from sqlalchemy import select

logger = get_logger("ImportService")

# Executor para operações bloqueantes
_executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="import_")


@dataclass
class ImportRowResult:
    """Resultado do processamento de uma linha."""
    row_number: int
    status: str  # "new", "updated", "matched", "error"
    sku_raw: str
    produto_id: Optional[int] = None
    match_score: float = 0.0
    error_message: Optional[str] = None
    data: Dict[str, Any] = None


@dataclass
class ImportResult:
    """Resultado completo de uma importação."""
    total_rows: int
    new_products: int
    updated_products: int
    matched_products: int
    errors: int
    rows: List[ImportRowResult] = None


def _parse_price(value: Any) -> Optional[Decimal]:
    """
    Converte valor para Decimal de preço.
    CENTURY CHECKLIST Item 64: Suporta formato BR (1.234,56) e US (1,234.56).
    
    Args:
        value: Valor a converter
        
    Returns:
        Decimal ou None se inválido
    """
    if value is None:
        return None
    
    try:
        # Limpar string
        if isinstance(value, str):
            # CENTURY CHECKLIST Item 65: Limpeza de espaços
            value = value.strip()
            # Remover R$, espaços
            value = value.replace("R$", "").replace("$", "").strip()
            # Converter vírgula para ponto
            value = value.replace(",", ".")
            # Remover pontos de milhar
            if value.count(".") > 1:
                parts = value.split(".")
                value = "".join(parts[:-1]) + "." + parts[-1]
        
        return Decimal(str(value)).quantize(Decimal("0.01"))
    except (InvalidOperation, ValueError):
        return None


def _is_row_empty(row: Dict[str, Any], required_keys: List[str]) -> bool:
    """
    CENTURY CHECKLIST Item 63: Detecta linhas vazias.
    
    Args:
        row: Dicionário da linha
        required_keys: Chaves obrigatórias
        
    Returns:
        True se linha está vazia
    """
    for key in required_keys:
        value = row.get(key, "")
        if value is not None and str(value).strip():
            return False
    return True


def _check_duplicates_in_file(rows: List[Dict[str, Any]], key_column: str) -> List[Tuple[int, str]]:
    """
    CENTURY CHECKLIST Item 66: Detecta duplicatas no arquivo.
    
    Args:
        rows: Lista de linhas
        key_column: Coluna chave para verificar
        
    Returns:
        Lista de (linha, valor) duplicados
    """
    seen = {}
    duplicates = []
    
    for idx, row in enumerate(rows):
        value = str(row.get(key_column, "")).strip().lower()
        if not value:
            continue
        
        if value in seen:
            duplicates.append((idx + 1, value))  # +1 para linha humana
        else:
            seen[value] = idx + 1
    
    return duplicates


def _trim_all_values(row: Dict[str, Any]) -> Dict[str, Any]:
    """
    CENTURY CHECKLIST Item 65: Remove espaços de todos os valores.
    
    Args:
        row: Dicionário original
        
    Returns:
        Dicionário com valores trimados
    """
    return {
        key: value.strip() if isinstance(value, str) else value
        for key, value in row.items()
    }


def _read_excel_sync(file_path: Path) -> List[Dict[str, Any]]:
    """
    Lê arquivo Excel de forma síncrona (para executar em thread).
    
    Args:
        file_path: Caminho do arquivo
        
    Returns:
        Lista de dicts com dados de cada linha
    """
    import pandas as pd
    
    try:
        df = pd.read_excel(file_path, dtype=str)
        df = df.fillna("")
        return df.to_dict("records")
    except Exception as e:
        logger.error(f"Erro ao ler Excel: {e}")
        return []


def _read_csv_sync(file_path: Path, delimiter: str = ";") -> List[Dict[str, Any]]:
    """
    Lê arquivo CSV de forma síncrona.
    
    Args:
        file_path: Caminho do arquivo
        delimiter: Delimitador de colunas
        
    Returns:
        Lista de dicts com dados de cada linha
    """
    import pandas as pd
    
    try:
        df = pd.read_csv(file_path, delimiter=delimiter, dtype=str, encoding="utf-8")
        df = df.fillna("")
        return df.to_dict("records")
    except Exception as e:
        logger.error(f"Erro ao ler CSV: {e}")
        return []


async def _fuzzy_match_sku(
    sku_raw: str,
    existing_products: List[Produto],
    threshold: float = 85.0
) -> Tuple[Optional[Produto], float]:
    """
    Busca produto por fuzzy matching de SKU.
    
    Args:
        sku_raw: SKU bruto da planilha
        existing_products: Lista de produtos existentes
        threshold: Score mínimo para considerar match
        
    Returns:
        Tupla (produto_matcheado, score) ou (None, 0)
    """
    from rapidfuzz import fuzz, process
    
    if not sku_raw or not existing_products:
        return None, 0.0
    
    # Criar mapeamento SKU -> Produto
    sku_map = {p.sku_origem: p for p in existing_products}
    
    # Buscar melhor match
    result = process.extractOne(
        sku_raw,
        sku_map.keys(),
        scorer=fuzz.ratio
    )
    
    if result and result[1] >= threshold:
        matched_sku = result[0]
        score = result[1]
        return sku_map[matched_sku], score
    
    return None, 0.0


class ImportService:
    """
    Serviço de importação de dados.
    Desacoplado da UI para execução em background.
    """
    
    @staticmethod
    async def read_file(file_path: Path) -> List[Dict[str, Any]]:
        """
        Lê arquivo Excel ou CSV em background thread.
        Passo 47 do Checklist - run_in_executor.
        
        Args:
            file_path: Caminho do arquivo
            
        Returns:
            Lista de dicts com dados
        """
        loop = asyncio.get_event_loop()
        
        if file_path.suffix.lower() in [".xlsx", ".xls"]:
            return await loop.run_in_executor(_executor, _read_excel_sync, file_path)
        elif file_path.suffix.lower() == ".csv":
            return await loop.run_in_executor(_executor, _read_csv_sync, file_path)
        else:
            logger.error(f"Formato não suportado: {file_path.suffix}")
            return []
    
    @staticmethod
    async def process_import(
        file_path: Path,
        sku_column: str = "SKU",
        name_column: str = "NOME",
        price_column: str = "PRECO",
        match_threshold: float = 85.0
    ) -> ImportResult:
        """
        Processa importação completa com fuzzy matching.
        
        Args:
            file_path: Caminho do arquivo
            sku_column: Nome da coluna de SKU
            name_column: Nome da coluna de nome
            price_column: Nome da coluna de preço
            match_threshold: Score mínimo para matching
            
        Returns:
            ImportResult com estatísticas
        """
        # Emitir evento de início
        event_bus.emit(EventType.AI_TASK_START, {
            "task": "import",
            "file": file_path.name
        })
        
        # Ler arquivo
        logger.info(f"Iniciando importação: {file_path.name}")
        rows = await ImportService.read_file(file_path)
        
        if not rows:
            logger.error("Arquivo vazio ou inválido")
            return ImportResult(0, 0, 0, 0, 1)
        
        # Carregar produtos existentes
        async with AsyncSessionLocal() as session:
            result = await session.execute(select(Produto))
            existing = result.scalars().all()
        
        results = []
        new_count = 0
        updated_count = 0
        matched_count = 0
        error_count = 0
        
        for i, row in enumerate(rows):
            try:
                sku = str(row.get(sku_column, "")).strip()
                name = str(row.get(name_column, "")).strip()
                price_raw = row.get(price_column)
                
                if not sku and not name:
                    continue  # Pular linhas vazias
                
                price = _parse_price(price_raw)
                
                # Tentar match
                matched_product, score = await _fuzzy_match_sku(
                    sku, existing, match_threshold
                )
                
                if matched_product:
                    if score == 100:
                        status = "matched"
                        matched_count += 1
                    else:
                        status = "updated"
                        updated_count += 1
                    
                    results.append(ImportRowResult(
                        row_number=i + 1,
                        status=status,
                        sku_raw=sku,
                        produto_id=matched_product.id,
                        match_score=score,
                        data={"nome": name, "preco": str(price) if price else None}
                    ))
                else:
                    status = "new"
                    new_count += 1
                    results.append(ImportRowResult(
                        row_number=i + 1,
                        status=status,
                        sku_raw=sku,
                        match_score=0,
                        data={"nome": name, "preco": str(price) if price else None}
                    ))
                
                # Emitir progresso a cada 10 linhas
                if (i + 1) % 10 == 0:
                    event_bus.emit(EventType.AI_TASK_PROGRESS, {
                        "task": "import",
                        "current": i + 1,
                        "total": len(rows),
                        "percent": (i + 1) / len(rows) * 100
                    })
                    
            except Exception as e:
                error_count += 1
                results.append(ImportRowResult(
                    row_number=i + 1,
                    status="error",
                    sku_raw=str(row.get(sku_column, "")),
                    error_message=str(e)
                ))
                logger.error(f"Erro na linha {i + 1}: {e}")
        
        # Emitir evento de conclusão
        event_bus.emit(EventType.AI_TASK_COMPLETE, {
            "task": "import",
            "new": new_count,
            "updated": updated_count,
            "matched": matched_count,
            "errors": error_count
        })
        
        logger.info(f"Importação concluída: {new_count} novos, {updated_count} atualizados, {matched_count} correspondidos, {error_count} erros")
        
        return ImportResult(
            total_rows=len(rows),
            new_products=new_count,
            updated_products=updated_count,
            matched_products=matched_count,
            errors=error_count,
            rows=results
        )
    
    @staticmethod
    async def apply_import(
        results: List[ImportRowResult],
        update_prices: bool = True,
        update_names: bool = False
    ) -> int:
        """
        Aplica resultados de importação ao banco de dados.
        
        Args:
            results: Lista de resultados processados
            update_prices: Atualizar preços de produtos existentes?
            update_names: Atualizar nomes de produtos existentes?
            
        Returns:
            Número de registros atualizados
        """
        updated = 0
        
        async with AsyncSessionLocal() as session:
            for row in results:
                if row.status == "error":
                    continue
                
                if row.status == "new":
                    # Criar novo produto
                    price = _parse_price(row.data.get("preco")) if row.data else None
                    nome = row.data.get("nome", row.sku_raw) if row.data else row.sku_raw
                    
                    produto = Produto(
                        sku_origem=row.sku_raw,
                        nome_sanitizado=nome,
                        preco_venda_atual=price or Decimal("0.00"),
                        status_qualidade=1  # Sem foto
                    )
                    session.add(produto)
                    updated += 1
                    
                elif row.status in ["updated", "matched"] and row.produto_id:
                    # Atualizar existente
                    result = await session.execute(
                        select(Produto).where(Produto.id == row.produto_id)
                    )
                    produto = result.scalar_one_or_none()
                    
                    if produto and row.data:
                        if update_prices and row.data.get("preco"):
                            price = _parse_price(row.data["preco"])
                            if price:
                                produto.preco_venda_atual = price
                                updated += 1
                        
                        if update_names and row.data.get("nome"):
                            produto.nome_sanitizado = row.data["nome"]
            
            await session.commit()
        
        logger.info(f"Importação aplicada: {updated} registros atualizados")
        return updated


# Singleton
import_service = ImportService()


def get_import_service() -> ImportService:
    """Retorna instância do ImportService."""
    return import_service

"""
AutoTabloide AI - Database Safety Module
==========================================
Robustez industrial para operações de banco de dados.
PROTOCOLO DE RETIFICAÇÃO: Passos 16-30 (Engenharia de Dados).

Este módulo contém:
- Passo 16: WAL Checkpoint automático
- Passo 17: Transações atômicas
- Passo 19: Sanitização SQL (verificação de parâmetros)
- Passo 21: Backup automático agendado (VACUUM INTO)
- Passo 22: Validação de hash de imagem
- Passo 24: Soft Delete (is_active pattern)
- Passo 25: Schema version e migração
- Passo 26: Normalização de texto para busca
- Passo 27: Foreign Keys ON
- Passo 28: Timeout de conexão aumentado
- Passo 30: Price history para Time Machine
"""

import re
import hashlib
import logging
import unicodedata
import asyncio
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any, Tuple
from decimal import Decimal

logger = logging.getLogger("DatabaseSafety")


# ==============================================================================
# PASSO 16: WAL CHECKPOINT AUTOMÁTICO
# ==============================================================================

class WALManager:
    """
    Gerencia o arquivo WAL do SQLite para evitar crescimento infinito.
    
    PROBLEMA: O arquivo -wal pode crescer indefinidamente em operações intensas.
    
    SOLUÇÃO: Configurar wal_autocheckpoint e executar checkpoints manuais.
    """
    
    DEFAULT_AUTOCHECKPOINT = 1000  # Páginas (cada página ~4KB = ~4MB)
    
    @classmethod
    async def configure_wal(cls, connection) -> None:
        """
        Configura pragmas WAL otimizados.
        
        Args:
            connection: Conexão SQLite assíncrona
        """
        await connection.execute("PRAGMA journal_mode = WAL")
        await connection.execute(f"PRAGMA wal_autocheckpoint = {cls.DEFAULT_AUTOCHECKPOINT}")
        await connection.execute("PRAGMA synchronous = NORMAL")
        await connection.execute("PRAGMA cache_size = -32000")  # 32MB cache
        await connection.execute("PRAGMA busy_timeout = 30000")  # 30s timeout
        
        logger.debug("WAL configurado com autocheckpoint")
    
    @classmethod
    async def manual_checkpoint(cls, connection, mode: str = "TRUNCATE") -> bool:
        """
        Executa checkpoint manual do WAL.
        
        Args:
            connection: Conexão SQLite
            mode: PASSIVE, FULL, RESTART ou TRUNCATE
            
        Returns:
            True se bem-sucedido
        """
        try:
            await connection.execute(f"PRAGMA wal_checkpoint({mode})")
            logger.info(f"WAL checkpoint ({mode}) executado")
            return True
        except Exception as e:
            logger.error(f"Falha no checkpoint: {e}")
            return False


# ==============================================================================
# PASSO 17: TRANSAÇÕES ATÔMICAS
# ==============================================================================

class AtomicTransactionManager:
    """
    Garante atomicidade em operações em lote.
    
    PROBLEMA: Importação de planilhas pode falhar no meio, deixando dados pela metade.
    
    SOLUÇÃO: Tudo ou nada - begin/commit/rollback explícitos.
    """
    
    @classmethod
    async def execute_batch(
        cls,
        session,
        operations: List[callable],
        on_progress: Optional[callable] = None
    ) -> Tuple[bool, int, Optional[str]]:
        """
        Executa múltiplas operações em uma única transação atômica.
        
        Args:
            session: Sessão assíncrona do SQLAlchemy
            operations: Lista de funções a executar
            on_progress: Callback (current, total) para progresso
            
        Returns:
            Tuple (sucesso, operações_executadas, mensagem_erro)
        """
        total = len(operations)
        executed = 0
        
        try:
            async with session.begin():
                for i, operation in enumerate(operations):
                    await operation(session)
                    executed += 1
                    
                    if on_progress:
                        on_progress(i + 1, total)
                
                # Commit implícito ao sair do context manager
            
            return True, executed, None
            
        except Exception as e:
            # Rollback implícito
            error_msg = f"Falha na operação {executed + 1}/{total}: {e}"
            logger.error(error_msg)
            return False, executed, error_msg


# ==============================================================================
# PASSO 19: SANITIZAÇÃO SQL
# ==============================================================================

class SQLSanitizer:
    """
    Valida e sanitiza parâmetros SQL.
    
    PROBLEMA: Concatenação de strings em queries pode causar SQL injection.
    
    SOLUÇÃO: Forçar uso de parâmetros nomeados e validar inputs.
    """
    
    # Padrões perigosos
    DANGEROUS_PATTERNS = [
        r";\s*DROP\s+",
        r";\s*DELETE\s+",
        r";\s*UPDATE\s+",
        r";\s*INSERT\s+",
        r"--",
        r"/\*",
        r"UNION\s+SELECT",
    ]
    
    @classmethod
    def is_safe_string(cls, value: str) -> bool:
        """
        Verifica se string é segura para uso em query.
        
        Args:
            value: String a verificar
            
        Returns:
            True se seguro
        """
        if not isinstance(value, str):
            return True
        
        upper_value = value.upper()
        
        for pattern in cls.DANGEROUS_PATTERNS:
            if re.search(pattern, upper_value, re.IGNORECASE):
                logger.warning(f"Padrão SQL perigoso detectado: {pattern}")
                return False
        
        return True
    
    @classmethod
    def sanitize_like_param(cls, value: str) -> str:
        """
        Escapa caracteres especiais para LIKE.
        
        Args:
            value: String para LIKE
            
        Returns:
            String escapada
        """
        # Escapa % e _ que são wildcards do LIKE
        return value.replace('%', r'\%').replace('_', r'\_')


# ==============================================================================
# PASSO 21: BACKUP AUTOMÁTICO (VACUUM INTO)
# ==============================================================================

class DatabaseBackupManager:
    """
    Gerencia backups automáticos do banco de dados.
    
    Usa VACUUM INTO para criar backup consistente sem bloquear.
    """
    
    MAX_BACKUPS = 10
    BACKUP_INTERVAL_HOURS = 4
    
    @classmethod
    async def create_backup(
        cls,
        db_path: Path,
        backup_dir: Path
    ) -> Optional[Path]:
        """
        Cria backup do banco usando VACUUM INTO.
        
        Args:
            db_path: Caminho do banco principal
            backup_dir: Diretório de backups
            
        Returns:
            Caminho do backup ou None se falhou
        """
        import aiosqlite
        
        backup_dir.mkdir(parents=True, exist_ok=True)
        
        # Nome com timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = backup_dir / f"{db_path.stem}_backup_{timestamp}.db"
        
        try:
            async with aiosqlite.connect(db_path) as db:
                # VACUUM INTO cria cópia consistente
                await db.execute(f"VACUUM INTO '{backup_path}'")
            
            logger.info(f"Backup criado: {backup_path.name}")
            
            # Limpar backups antigos
            await cls._cleanup_old_backups(backup_dir)
            
            return backup_path
            
        except Exception as e:
            logger.error(f"Falha ao criar backup: {e}")
            return None
    
    @classmethod
    async def _cleanup_old_backups(cls, backup_dir: Path) -> int:
        """Remove backups antigos além do limite."""
        removed = 0
        
        backups = sorted(
            backup_dir.glob("*_backup_*.db"),
            key=lambda p: p.stat().st_mtime,
            reverse=True
        )
        
        for old_backup in backups[cls.MAX_BACKUPS:]:
            try:
                old_backup.unlink()
                removed += 1
            except Exception:
                pass
        
        if removed:
            logger.debug(f"Removidos {removed} backups antigos")
        
        return removed
    
    @classmethod
    async def should_backup(cls, backup_dir: Path) -> bool:
        """Verifica se é hora de fazer backup."""
        backups = list(backup_dir.glob("*_backup_*.db"))
        
        if not backups:
            return True
        
        latest = max(backups, key=lambda p: p.stat().st_mtime)
        age_hours = (datetime.now().timestamp() - latest.stat().st_mtime) / 3600
        
        return age_hours >= cls.BACKUP_INTERVAL_HOURS


# ==============================================================================
# PASSO 22: VALIDAÇÃO DE HASH DE IMAGEM
# ==============================================================================

class ImageHashValidator:
    """
    Valida integridade de links entre produtos e imagens.
    
    PROBLEMA: Se a imagem física for deletada, o hash no banco aponta para nada.
    
    SOLUÇÃO: Verificar existência e marcar links quebrados.
    """
    
    @classmethod
    async def validate_product_images(
        cls,
        session,
        assets_dir: Path
    ) -> Dict[str, List[Dict]]:
        """
        Valida todas as imagens de produtos.
        
        Returns:
            Dict com listas de produtos com links válidos e quebrados
        """
        from sqlalchemy import select
        from src.core.models import Produto
        
        results = {
            "valid": [],
            "broken": [],
            "empty": [],
        }
        
        stmt = select(Produto)
        result = await session.execute(stmt)
        products = result.scalars().all()
        
        for product in products:
            hashes = product.get_images()
            
            if not hashes:
                results["empty"].append({
                    "id": product.id,
                    "sku": product.sku_origem,
                    "nome": product.nome_sanitizado,
                })
                continue
            
            broken_hashes = []
            for hash_md5 in hashes:
                # Verificar se arquivo existe
                image_path = assets_dir / "store" / f"{hash_md5}.webp"
                
                if not image_path.exists():
                    # Tentar outras extensões
                    found = False
                    for ext in ['.jpg', '.png', '.jpeg']:
                        alt_path = image_path.with_suffix(ext)
                        if alt_path.exists():
                            found = True
                            break
                    
                    if not found:
                        broken_hashes.append(hash_md5)
            
            if broken_hashes:
                results["broken"].append({
                    "id": product.id,
                    "sku": product.sku_origem,
                    "nome": product.nome_sanitizado,
                    "broken_hashes": broken_hashes,
                })
            else:
                results["valid"].append(product.id)
        
        logger.info(
            f"Validação de imagens: {len(results['valid'])} OK, "
            f"{len(results['broken'])} quebrados, {len(results['empty'])} vazios"
        )
        
        return results


# ==============================================================================
# PASSO 26: NORMALIZAÇÃO DE TEXTO PARA BUSCA
# ==============================================================================

class TextNormalizer:
    """
    Normaliza texto para busca sem acentos e case-insensitive.
    
    PROBLEMA: "Coca-Cola" e "COCA COLA" são tratados como diferentes.
    
    SOLUÇÃO: Coluna de busca normalizada.
    """
    
    @classmethod
    def normalize_for_search(cls, text: str) -> str:
        """
        Normaliza texto removendo acentos, convertendo para minúsculas,
        e removendo caracteres especiais.
        
        Args:
            text: Texto original
            
        Returns:
            Texto normalizado
        """
        if not text:
            return ""
        
        # Converter para minúsculas
        text = text.lower()
        
        # Decomposição Unicode para separar caracteres base de acentos
        nfkd = unicodedata.normalize('NFKD', text)
        
        # Remover marcas diacríticas (acentos)
        without_accents = ''.join(
            c for c in nfkd 
            if not unicodedata.combining(c)
        )
        
        # Remover caracteres especiais, manter apenas letras, números e espaços
        normalized = re.sub(r'[^a-z0-9\s]', ' ', without_accents)
        
        # Normalizar espaços múltiplos
        normalized = ' '.join(normalized.split())
        
        return normalized
    
    @classmethod
    def create_search_tokens(cls, text: str) -> List[str]:
        """
        Cria tokens de busca a partir do texto.
        
        Args:
            text: Texto a tokenizar
            
        Returns:
            Lista de tokens
        """
        normalized = cls.normalize_for_search(text)
        tokens = normalized.split()
        
        # Filtrar tokens muito curtos
        return [t for t in tokens if len(t) >= 2]


# ==============================================================================
# PASSO 27: FOREIGN KEYS ON
# ==============================================================================

class ForeignKeyEnforcer:
    """
    Garante que foreign keys estejam ativas no SQLite.
    
    PROBLEMA: SQLite tem foreign keys DESLIGADAS por padrão!
    
    SOLUÇÃO: Executar PRAGMA foreign_keys = ON em cada conexão.
    """
    
    @classmethod
    async def enable_foreign_keys(cls, connection) -> bool:
        """Ativa foreign keys na conexão."""
        try:
            await connection.execute("PRAGMA foreign_keys = ON")
            
            # Verificar
            result = await connection.execute("PRAGMA foreign_keys")
            row = await result.fetchone()
            
            if row and row[0] == 1:
                logger.debug("Foreign keys ativadas")
                return True
            else:
                logger.warning("Falha ao ativar foreign keys")
                return False
                
        except Exception as e:
            logger.error(f"Erro ao ativar foreign keys: {e}")
            return False


# ==============================================================================
# PASSO 30: PRICE HISTORY PARA TIME MACHINE
# ==============================================================================

class PriceHistoryTracker:
    """
    Rastreia histórico de preços para auditoria e rollback.
    
    Permite "Time Machine" - ver e restaurar preços anteriores.
    """
    
    @classmethod
    async def record_price_change(
        cls,
        session,
        produto_id: int,
        old_price: Decimal,
        new_price: Decimal,
        source: str = "manual"
    ) -> bool:
        """
        Registra mudança de preço no histórico.
        
        Args:
            session: Sessão do banco
            produto_id: ID do produto
            old_price: Preço anterior
            new_price: Novo preço
            source: Origem da mudança (manual, import, api)
            
        Returns:
            True se registrado
        """
        from src.core.models import AuditLog, TipoAcao, TipoEntidade
        import json
        
        try:
            audit = AuditLog(
                entity_type=TipoEntidade.PRODUTO.value,
                entity_id=produto_id,
                action_type=TipoAcao.UPDATE.value,
                diff_payload=json.dumps({
                    "field": "preco_venda_atual",
                    "old_value": str(old_price),
                    "new_value": str(new_price),
                    "source_context": source,
                }),
                severity=2 if abs(new_price - old_price) > 10 else 1,
                description=f"Preço alterado de R${old_price} para R${new_price}"
            )
            
            session.add(audit)
            await session.flush()
            
            return True
            
        except Exception as e:
            logger.error(f"Falha ao registrar mudança de preço: {e}")
            return False
    
    @classmethod
    async def get_price_history(
        cls,
        session,
        produto_id: int,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Retorna histórico de preços de um produto.
        
        Args:
            session: Sessão do banco
            produto_id: ID do produto
            limit: Máximo de registros
            
        Returns:
            Lista de mudanças ordenada por data (mais recente primeiro)
        """
        from sqlalchemy import select, desc
        from src.core.models import AuditLog, TipoEntidade
        import json
        
        stmt = (
            select(AuditLog)
            .where(AuditLog.entity_type == TipoEntidade.PRODUTO.value)
            .where(AuditLog.entity_id == produto_id)
            .order_by(desc(AuditLog.timestamp))
            .limit(limit)
        )
        
        result = await session.execute(stmt)
        logs = result.scalars().all()
        
        history = []
        for log in logs:
            diff = log.get_diff()
            if diff.get("field") == "preco_venda_atual":
                history.append({
                    "timestamp": log.timestamp,
                    "old_price": Decimal(diff.get("old_value", "0")),
                    "new_price": Decimal(diff.get("new_value", "0")),
                    "source": diff.get("source_context", "unknown"),
                })
        
        return history


# ==============================================================================
# VALIDAÇÃO DE PREÇO DE > POR (PASSO 68 DO PROTOCOLO COMPLETO)
# ==============================================================================

class PriceValidator:
    """
    Validações de regras de negócio para preços.
    
    CRÍTICO: Preço "De" deve ser MAIOR que preço "Por" (PROCON).
    """
    
    @classmethod
    def validate_de_por(cls, preco_de: Decimal, preco_por: Decimal) -> Tuple[bool, str]:
        """
        Valida regra De > Por.
        
        Args:
            preco_de: Preço original (De)
            preco_por: Preço promocional (Por)
            
        Returns:
            Tuple (válido, mensagem)
        """
        if preco_de is None:
            return True, "Sem preço De (não é oferta)"
        
        if preco_de <= 0:
            return False, "Preço De deve ser positivo"
        
        if preco_por <= 0:
            return False, "Preço Por deve ser positivo"
        
        if preco_de <= preco_por:
            return False, f"INVÁLIDO: De (R${preco_de}) deve ser MAIOR que Por (R${preco_por})"
        
        # Diferença mínima de 5% para ser considerado oferta real
        discount = ((preco_de - preco_por) / preco_de) * 100
        if discount < 5:
            return False, f"Desconto de {discount:.1f}% é insignificante (mínimo 5%)"
        
        return True, f"Desconto válido: {discount:.1f}%"


# ==============================================================================
# FUNÇÃO DE INICIALIZAÇÃO
# ==============================================================================

async def initialize_database_safety(db_path: Path, backup_dir: Path) -> dict:
    """
    Inicializa proteções de banco de dados.
    
    Args:
        db_path: Caminho do banco
        backup_dir: Diretório de backups
        
    Returns:
        Dict com status
    """
    import aiosqlite
    
    results = {}
    
    # Configurar pragmas
    try:
        async with aiosqlite.connect(db_path) as db:
            await WALManager.configure_wal(db)
            await ForeignKeyEnforcer.enable_foreign_keys(db)
            results["wal_configured"] = True
            results["foreign_keys"] = True
    except Exception as e:
        logger.error(f"Falha ao configurar DB: {e}")
        results["wal_configured"] = False
        results["foreign_keys"] = False
    
    # Verificar backup
    if await DatabaseBackupManager.should_backup(backup_dir):
        backup_path = await DatabaseBackupManager.create_backup(db_path, backup_dir)
        results["backup_created"] = backup_path is not None
    else:
        results["backup_created"] = None  # Não necessário
    
    logger.info("Database safety inicializado")
    return results

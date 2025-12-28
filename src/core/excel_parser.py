"""
AutoTabloide AI - Excel Parser Industrial Grade
=================================================
Passo 32-33: Parser robusto para Excel/CSV.

Suporta:
- Excel (.xlsx, .xls)
- CSV (com detecção de encoding e delimitador)
- Mapeamento flexível de colunas
"""

from pathlib import Path
from typing import Dict, List, Optional, Tuple
from decimal import Decimal, InvalidOperation
import csv
import chardet
import re


# =============================================================================
# COLUMN MAPPING - Mapeia nomes comuns de colunas
# =============================================================================

COLUMN_ALIASES = {
    "nome": ["nome", "descricao", "produto", "item", "mercadoria", "name", "description"],
    "sku": ["sku", "codigo", "code", "cod", "ref", "referencia", "id"],
    "preco": ["preco", "valor", "price", "vlr", "preco_venda", "preco_atual"],
    "preco_ref": ["preco_de", "preco_ref", "preco_referencia", "valor_de", "de", "original_price"],
    "marca": ["marca", "fabricante", "brand", "fornecedor"],
    "peso": ["peso", "medida", "unidade", "volume", "weight", "un"],
    "categoria": ["categoria", "setor", "departamento", "category", "section"],
}


def _normalize_header(header: str) -> str:
    """Normaliza header para comparação."""
    return header.lower().strip().replace(" ", "_").replace("-", "_")


def _detect_column_mapping(headers: List[str]) -> Dict[str, int]:
    """Detecta mapeamento automático de colunas."""
    mapping = {}
    normalized = [_normalize_header(h) for h in headers]
    
    for field, aliases in COLUMN_ALIASES.items():
        for i, header in enumerate(normalized):
            if header in aliases:
                mapping[field] = i
                break
    
    return mapping


def _parse_price(value: str) -> Optional[Decimal]:
    """Converte string de preço para Decimal."""
    if not value:
        return None
    
    # Remove caracteres não numéricos exceto vírgula e ponto
    clean = re.sub(r'[^\d,\.]', '', value.strip())
    
    if not clean:
        return None
    
    # Detecta formato brasileiro (vírgula decimal) vs americano (ponto decimal)
    if ',' in clean and '.' in clean:
        # Tem ambos - assume brasileiro (1.234,56)
        clean = clean.replace('.', '').replace(',', '.')
    elif ',' in clean:
        # Só vírgula - pode ser decimal
        parts = clean.split(',')
        if len(parts) == 2 and len(parts[1]) <= 2:
            # Assume vírgula decimal
            clean = clean.replace(',', '.')
        else:
            # Assume separador de milhar
            clean = clean.replace(',', '')
    
    try:
        return Decimal(clean)
    except InvalidOperation:
        return None


# =============================================================================
# EXCEL PARSER
# =============================================================================

def parse_excel(filepath: str) -> Tuple[List[Dict], List[str]]:
    """
    Parse arquivo Excel.
    
    Args:
        filepath: Caminho do arquivo .xlsx ou .xls
        
    Returns:
        Tuple[lista de produtos, lista de erros]
    """
    try:
        import openpyxl
    except ImportError:
        return [], ["Biblioteca openpyxl não instalada. Execute: pip install openpyxl"]
    
    errors = []
    items = []
    
    try:
        wb = openpyxl.load_workbook(filepath, read_only=True, data_only=True)
        ws = wb.active
        
        rows = list(ws.iter_rows(values_only=True))
        if not rows:
            return [], ["Planilha vazia"]
        
        # Primeira linha = headers
        headers = [str(h) if h else f"col{i}" for i, h in enumerate(rows[0])]
        mapping = _detect_column_mapping(headers)
        
        if "nome" not in mapping:
            return [], ["Coluna 'Nome' ou 'Descrição' não encontrada"]
        
        # Processa dados
        for row_idx, row in enumerate(rows[1:], start=2):
            if not any(row):  # Linha vazia
                continue
            
            item = {}
            
            # Nome (obrigatório)
            nome_idx = mapping.get("nome")
            if nome_idx is not None and row[nome_idx]:
                item["nome"] = str(row[nome_idx]).strip()
            else:
                errors.append(f"Linha {row_idx}: Nome vazio")
                continue
            
            # SKU
            if "sku" in mapping and row[mapping["sku"]]:
                item["sku"] = str(row[mapping["sku"]]).strip()
            
            # Preço
            if "preco" in mapping and row[mapping["preco"]]:
                preco = _parse_price(str(row[mapping["preco"]]))
                if preco:
                    item["preco"] = preco
            
            # Preço Referência
            if "preco_ref" in mapping and row[mapping["preco_ref"]]:
                preco_ref = _parse_price(str(row[mapping["preco_ref"]]))
                if preco_ref:
                    item["preco_ref"] = preco_ref
            
            # Marca
            if "marca" in mapping and row[mapping["marca"]]:
                item["marca"] = str(row[mapping["marca"]]).strip()
            
            # Peso
            if "peso" in mapping and row[mapping["peso"]]:
                item["peso"] = str(row[mapping["peso"]]).strip()
            
            # Categoria
            if "categoria" in mapping and row[mapping["categoria"]]:
                item["categoria"] = str(row[mapping["categoria"]]).strip()
            
            items.append(item)
        
        wb.close()
        
    except Exception as e:
        return [], [f"Erro ao processar Excel: {e}"]
    
    return items, errors


# =============================================================================
# CSV PARSER
# =============================================================================

def parse_csv(filepath: str) -> Tuple[List[Dict], List[str]]:
    """
    Parse arquivo CSV com detecção automática de encoding e delimitador.
    
    Args:
        filepath: Caminho do arquivo .csv
        
    Returns:
        Tuple[lista de produtos, lista de erros]
    """
    errors = []
    items = []
    
    path = Path(filepath)
    
    # Detecta encoding
    with open(path, 'rb') as f:
        raw = f.read(10000)
        detected = chardet.detect(raw)
        encoding = detected.get('encoding', 'utf-8')
    
    # Detecta delimitador
    with open(path, 'r', encoding=encoding, errors='replace') as f:
        sample = f.read(5000)
        sniffer = csv.Sniffer()
        try:
            dialect = sniffer.sniff(sample)
            delimiter = dialect.delimiter
        except:
            delimiter = ',' if sample.count(',') >= sample.count(';') else ';'
    
    try:
        with open(path, 'r', encoding=encoding, errors='replace') as f:
            reader = csv.reader(f, delimiter=delimiter)
            rows = list(reader)
            
            if not rows:
                return [], ["Arquivo CSV vazio"]
            
            # Primeira linha = headers
            headers = rows[0]
            mapping = _detect_column_mapping(headers)
            
            if "nome" not in mapping:
                return [], ["Coluna 'Nome' ou 'Descrição' não encontrada"]
            
            # Processa dados
            for row_idx, row in enumerate(rows[1:], start=2):
                if not any(cell.strip() for cell in row):
                    continue
                
                item = {}
                
                # Nome (obrigatório)
                nome_idx = mapping.get("nome")
                if nome_idx is not None and nome_idx < len(row) and row[nome_idx].strip():
                    item["nome"] = row[nome_idx].strip()
                else:
                    errors.append(f"Linha {row_idx}: Nome vazio")
                    continue
                
                # SKU
                if "sku" in mapping:
                    idx = mapping["sku"]
                    if idx < len(row) and row[idx].strip():
                        item["sku"] = row[idx].strip()
                
                # Preço
                if "preco" in mapping:
                    idx = mapping["preco"]
                    if idx < len(row) and row[idx].strip():
                        preco = _parse_price(row[idx])
                        if preco:
                            item["preco"] = preco
                
                # Preço Referência
                if "preco_ref" in mapping:
                    idx = mapping["preco_ref"]
                    if idx < len(row) and row[idx].strip():
                        preco_ref = _parse_price(row[idx])
                        if preco_ref:
                            item["preco_ref"] = preco_ref
                
                # Marca
                if "marca" in mapping:
                    idx = mapping["marca"]
                    if idx < len(row) and row[idx].strip():
                        item["marca"] = row[idx].strip()
                
                # Peso
                if "peso" in mapping:
                    idx = mapping["peso"]
                    if idx < len(row) and row[idx].strip():
                        item["peso"] = row[idx].strip()
                
                # Categoria
                if "categoria" in mapping:
                    idx = mapping["categoria"]
                    if idx < len(row) and row[idx].strip():
                        item["categoria"] = row[idx].strip()
                
                items.append(item)
                
    except Exception as e:
        return [], [f"Erro ao processar CSV: {e}"]
    
    return items, errors


# =============================================================================
# UNIFIED PARSER
# =============================================================================

def parse_spreadsheet(filepath: str) -> Tuple[List[Dict], List[str]]:
    """
    Parse planilha (Excel ou CSV).
    
    Detecta formato automaticamente pela extensão.
    
    Args:
        filepath: Caminho do arquivo
        
    Returns:
        Tuple[lista de produtos, lista de erros]
    """
    path = Path(filepath)
    ext = path.suffix.lower()
    
    if ext in ['.xlsx', '.xls']:
        return parse_excel(filepath)
    elif ext == '.csv':
        return parse_csv(filepath)
    else:
        return [], [f"Formato não suportado: {ext}. Use .xlsx, .xls ou .csv"]

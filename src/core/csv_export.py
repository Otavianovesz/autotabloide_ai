"""
AutoTabloide AI - CSV Export
============================
PROTOCOLO DE RETIFICAÇÃO NÍVEL 0 - Fase 2 (Passo 62)
Exportação de produtos para CSV.
"""

from __future__ import annotations
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime
import logging
import csv

logger = logging.getLogger("CSVExport")


def export_products_to_csv(
    products: List[Dict],
    output_path: str = None,
    columns: List[str] = None
) -> str:
    """
    Exporta lista de produtos para CSV.
    
    Args:
        products: Lista de dicts com dados dos produtos
        output_path: Caminho de saída (opcional)
        columns: Colunas a incluir (opcional)
    
    Returns:
        Caminho do arquivo criado
    """
    if not products:
        logger.warning("Nenhum produto para exportar")
        return ""
    
    # Colunas padrão
    default_columns = [
        "id", "nome_sanitizado", "preco_venda_atual", 
        "preco_referencia", "marca_normalizada", "sku_origem",
        "detalhe_peso", "status"
    ]
    columns = columns or default_columns
    
    # Caminho padrão
    if not output_path:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = f"produtos_export_{timestamp}.csv"
    
    try:
        with open(output_path, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=columns, extrasaction="ignore")
            writer.writeheader()
            writer.writerows(products)
        
        logger.info(f"Exportado {len(products)} produtos para {output_path}")
        return output_path
        
    except Exception as e:
        logger.error(f"Erro ao exportar CSV: {e}")
        return ""


def import_products_from_csv(
    file_path: str,
    encoding: str = "utf-8-sig"
) -> List[Dict]:
    """
    Importa produtos de CSV.
    
    Returns:
        Lista de dicts com dados dos produtos
    """
    products = []
    
    try:
        with open(file_path, "r", encoding=encoding) as f:
            reader = csv.DictReader(f)
            products = list(reader)
        
        logger.info(f"Importados {len(products)} produtos de {file_path}")
        
    except Exception as e:
        logger.error(f"Erro ao importar CSV: {e}")
    
    return products

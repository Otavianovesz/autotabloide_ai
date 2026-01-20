"""
AutoTabloide AI - Preflight System
==================================
Verificação de qualidade antes da exportação final.
Item 87 do Protocolo.

Checks:
1. Imagens de baixa resolução (< 150 DPI)
2. Textos estourando a caixa (Bounding Rect > Item Rect)
3. Produtos sem preço
4. Produtos sem imagem
"""

from typing import List, Dict, Any
from dataclasses import dataclass
from PySide6.QtCore import QObject, QRectF
from PySide6.QtGui import QImage
from PySide6.QtWidgets import QGraphicsScene

from ..graphics.smart_items import SmartGraphicsItem, SmartSlotItem

@dataclass
class PreflightIssue:
    severity: str  # 'error', 'warning'
    code: str      # 'LOW_RES', 'TEXT_OVERFLOW', etc 
    message: str
    item: SmartGraphicsItem

class PreflightInspector(QObject):
    """Inspetor de qualidade da cena."""
    
    def __init__(self):
        super().__init__()
        
    def inspect(self, scene: QGraphicsScene) -> List[PreflightIssue]:
        """Executa verificação completa na cena."""
        issues = []
        
        # Filtra apenas itens relevantes (Smart Items)
        items = [i for i in scene.items() if isinstance(i, SmartGraphicsItem)]
        
        for item in items:
            # 1. Check Missing Data (Slots)
            if isinstance(item, SmartSlotItem):
                if not item.product_data:
                    issues.append(PreflightIssue(
                        'warning', 'EMPTY_SLOT', 
                        f"Slot vazio: {item.element_id}", item
                    ))
                    continue # Se ta vazio, nao checka resto
                
                # Check Price
                price = item.product_data.get('preco_venda_atual')
                if not price:
                    issues.append(PreflightIssue(
                        'error', 'MISSING_PRICE',
                        f"Produto sem preço: {item.product_data.get('nome_sanitizado')}", item
                    ))
                    
                # Check Image
                # (Assumindo que SmartSlotItem tem acesso à imagem renderizada ou path)
                # TODO: Implementar check específico se a imagem falhou
                
            # 2. Check Text Overflow
            # Necessita que SmartGraphicsItem exponha seus textos internos ou status de overflow
            if hasattr(item, 'check_overflow'):
                 if item.check_overflow():
                     issues.append(PreflightIssue(
                         'error', 'TEXT_OVERFLOW',
                         f"Texto cortado em: {item.element_id}", item
                     ))

            # 3. Check Image Resolution (DPI)
            # Calculado baseando-se no tamanho original vs tamanho na cena
            if hasattr(item, 'get_image_dpi'):
                dpi = item.get_image_dpi()
                if dpi and dpi < 150:
                    issues.append(PreflightIssue(
                        'warning', 'LOW_RES',
                        f"Baixa resolução ({int(dpi)} DPI): {item.element_id}", item
                    ))
                    
        return issues

"""
AutoTabloide AI - Drag Source Model
===================================
PROTOCOLO DE CONVERGÊNCIA 260 - Fase 2 (Passos 49, 59, 69)
Model com drag source real para arrastar produtos.
"""

from __future__ import annotations
from typing import List, Dict, Any, Optional
import json
import logging

from PySide6.QtCore import (
    Qt, QAbstractTableModel, QModelIndex, QMimeData,
    QByteArray, Signal, Slot
)
from PySide6.QtGui import QPixmap, QIcon

logger = logging.getLogger("DragModel")


class ProductsDragModel(QAbstractTableModel):
    """
    Model de produtos com suporte a drag real.
    
    Features:
    - Drag source com JSON do produto
    - Cursor muda para miniatura
    - Multi-drag support
    - fetchMore para paginação
    """
    
    MIME_TYPE = "application/x-autotabloide-product"
    
    COLUMNS = [
        ("nome_sanitizado", "Produto"),
        ("preco_venda_atual", "Preço"),
        ("marca_normalizada", "Marca"),
        ("status", "Status"),
    ]
    
    products_dropped = Signal(list)  # emitido quando múltiplos selecionados
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._data: List[Dict] = []
        self._total_count = 0
        self._can_fetch_more = True
    
    # =========================================================================
    # QAbstractTableModel Implementation
    # =========================================================================
    
    def rowCount(self, parent=QModelIndex()):
        return len(self._data)
    
    def columnCount(self, parent=QModelIndex()):
        return len(self.COLUMNS)
    
    def data(self, index: QModelIndex, role=Qt.DisplayRole):
        if not index.isValid() or index.row() >= len(self._data):
            return None
        
        product = self._data[index.row()]
        col_key = self.COLUMNS[index.column()][0]
        
        if role == Qt.DisplayRole:
            value = product.get(col_key)
            
            if col_key == "preco_venda_atual":
                return f"R$ {value:.2f}".replace(".", ",") if value else "---"
            
            return str(value) if value else ""
        
        elif role == Qt.UserRole:
            return product
        
        return None
    
    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self.COLUMNS[section][1]
        return None
    
    # =========================================================================
    # Drag & Drop
    # =========================================================================
    
    def flags(self, index: QModelIndex):
        default_flags = super().flags(index)
        if index.isValid():
            return default_flags | Qt.ItemIsDragEnabled
        return default_flags
    
    def supportedDragActions(self):
        return Qt.CopyAction
    
    def mimeTypes(self):
        return [self.MIME_TYPE, "text/plain"]
    
    def mimeData(self, indexes: List[QModelIndex]) -> QMimeData:
        """Cria payload de drag com dados do produto."""
        mime_data = QMimeData()
        
        # Coleta produtos únicos (uma linha pode ter múltiplos índices de coluna)
        rows = set()
        products = []
        
        for index in indexes:
            if index.row() not in rows:
                rows.add(index.row())
                product = self._data[index.row()]
                products.append({
                    "id": product.get("id"),
                    "nome_sanitizado": product.get("nome_sanitizado"),
                    "preco_venda_atual": product.get("preco_venda_atual"),
                    "preco_referencia": product.get("preco_referencia"),
                    "caminho_imagem_final": product.get("caminho_imagem_final"),
                    "marca_normalizada": product.get("marca_normalizada"),
                })
        
        # JSON payload
        json_data = json.dumps(products, ensure_ascii=False)
        mime_data.setData(self.MIME_TYPE, QByteArray(json_data.encode("utf-8")))
        mime_data.setText(json_data)
        
        logger.debug(f"[Drag] Criado payload com {len(products)} produtos")
        
        return mime_data
    
    # =========================================================================
    # Infinite Scroll (fetchMore)
    # =========================================================================
    
    def canFetchMore(self, parent=QModelIndex()):
        return self._can_fetch_more and len(self._data) < self._total_count
    
    def fetchMore(self, parent=QModelIndex()):
        """Carrega mais itens."""
        if not self._can_fetch_more:
            return
        
        from src.qt.core.database_bridge import get_db_bridge
        
        offset = len(self._data)
        get_db_bridge().load_products(offset, 50, self._on_more_loaded)
    
    def _on_more_loaded(self, result):
        """Callback quando mais dados carregam."""
        if not result.success:
            return
        
        if not result.data:
            self._can_fetch_more = False
            return
        
        start = len(self._data)
        end = start + len(result.data) - 1
        
        self.beginInsertRows(QModelIndex(), start, end)
        self._data.extend(result.data)
        self.endInsertRows()
        
        self._total_count = result.total_count
    
    # =========================================================================
    # Data Management
    # =========================================================================
    
    def set_data(self, products: List[Dict], total_count: int = 0):
        """Define dados iniciais."""
        self.beginResetModel()
        self._data = products
        self._total_count = total_count or len(products)
        self._can_fetch_more = total_count > len(products)
        self.endResetModel()
    
    def clear(self):
        """Limpa dados."""
        self.beginResetModel()
        self._data = []
        self._total_count = 0
        self.endResetModel()
    
    def get_product(self, row: int) -> Optional[Dict]:
        """Retorna produto por índice."""
        if 0 <= row < len(self._data):
            return self._data[row]
        return None
    
    def update_product(self, product_id: int, updates: Dict):
        """Atualiza produto na memória."""
        for i, product in enumerate(self._data):
            if product.get("id") == product_id:
                self._data[i].update(updates)
                
                top_left = self.index(i, 0)
                bottom_right = self.index(i, self.columnCount() - 1)
                self.dataChanged.emit(top_left, bottom_right)
                break


# =============================================================================
# HELPER
# =============================================================================

def create_products_drag_model(parent=None) -> ProductsDragModel:
    """Cria model de produtos."""
    return ProductsDragModel(parent)

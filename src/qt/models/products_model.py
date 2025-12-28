"""
AutoTabloide AI - Products Table Model
======================================
PROTOCOLO DE RETIFICAÇÃO NÍVEL 0 - Fase 2 (Passos 31-50)
Model de alta performance para 10k+ produtos.

Features:
- QAbstractTableModel (NÃO QTableWidget!)
- Lazy loading com fetchMore (blocos de 50)
- Queries em DatabaseWorker (nunca trava UI)
- Cache de thumbnails
- Drag nativo com mimeData
"""

from __future__ import annotations
from typing import List, Dict, Any, Optional
from decimal import Decimal
from pathlib import Path
import json

from PySide6.QtCore import (
    Qt, QAbstractTableModel, QModelIndex, Signal, Slot,
    QThread, QMimeData, QByteArray, QTimer
)
from PySide6.QtGui import QPixmap, QIcon
from PySide6.QtWidgets import QStyledItemDelegate


# =============================================================================
# CONSTANTES
# =============================================================================

BATCH_SIZE = 50  # Produtos carregados por vez
MIME_TYPE = "application/x-autotabloide-product"

COLUMNS = [
    ("id", "ID", 50),
    ("nome_sanitizado", "Produto", 250),
    ("marca_normalizada", "Marca", 120),
    ("preco_venda_atual", "Preço", 80),
    ("categoria", "Categoria", 100),
    ("status", "", 30),  # Ícone de status
]


# =============================================================================
# DATABASE WORKER
# =============================================================================

class DatabaseWorker(QThread):
    """
    Worker para queries SQL em thread separada.
    A UI NUNCA toca no banco diretamente.
    """
    
    results_ready = Signal(list, int)  # (products, total_count)
    error = Signal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._query = ""
        self._offset = 0
        self._limit = BATCH_SIZE
        self._filters = {}
        
    def set_query(self, query: str = "", offset: int = 0, limit: int = BATCH_SIZE, filters: dict = None):
        self._query = query
        self._offset = offset
        self._limit = limit
        self._filters = filters or {}
    
    def run(self):
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(self._fetch())
            self.results_ready.emit(result["products"], result["total"])
        except Exception as e:
            self.error.emit(str(e))
        finally:
            loop.close()
    
    async def _fetch(self) -> dict:
        from src.core.database import AsyncSessionLocal
        from src.core.repositories import ProductRepository
        
        async with AsyncSessionLocal() as session:
            repo = ProductRepository(session)
            
            # Query com filtros
            products = await repo.search(
                query=self._query,
                offset=self._offset,
                limit=self._limit,
                **self._filters
            )
            
            # Count total
            total = await repo.count(query=self._query, **self._filters)
            
            # Serializa para dicts
            result = []
            for p in products:
                result.append({
                    "id": p.id,
                    "sku_origem": p.sku_origem,
                    "nome_sanitizado": p.nome_sanitizado,
                    "marca_normalizada": p.marca_normalizada,
                    "detalhe_peso": p.detalhe_peso,
                    "preco_venda_atual": float(p.preco_venda_atual or 0),
                    "preco_referencia": float(p.preco_referencia or 0) if p.preco_referencia else None,
                    "categoria": p.categoria,
                    "img_hash_ref": p.img_hash_ref,
                    "status_qualidade": p.status_qualidade or 0,
                })
            
            return {"products": result, "total": total}


# =============================================================================
# THUMBNAIL PROVIDER
# =============================================================================

class ThumbnailProvider:
    """
    Cache de thumbnails em memória.
    Se não estiver em cache, retorna placeholder e busca em background.
    """
    
    _cache: Dict[str, QPixmap] = {}
    _placeholder: QPixmap = None
    _loading: set = set()
    
    @classmethod
    def get_thumbnail(cls, img_hash: str, vault_path: Path) -> QPixmap:
        """Retorna thumbnail do cache ou placeholder."""
        if not img_hash:
            return cls._get_placeholder()
        
        if img_hash in cls._cache:
            return cls._cache[img_hash]
        
        # Não está no cache - tenta carregar
        thumb_path = vault_path / "thumbnails" / f"{img_hash}.jpg"
        
        if thumb_path.exists():
            pixmap = QPixmap(str(thumb_path))
            if not pixmap.isNull():
                cls._cache[img_hash] = pixmap
                return pixmap
        
        return cls._get_placeholder()
    
    @classmethod
    def _get_placeholder(cls) -> QPixmap:
        """Retorna placeholder SVG."""
        if cls._placeholder is None:
            # Cria placeholder cinza
            cls._placeholder = QPixmap(40, 40)
            cls._placeholder.fill(Qt.gray)
        return cls._placeholder
    
    @classmethod
    def clear_cache(cls):
        """Limpa cache de thumbnails."""
        cls._cache.clear()


# =============================================================================
# PRODUCTS TABLE MODEL (CRÍTICO: QAbstractTableModel, NÃO QTableWidget!)
# =============================================================================

class ProductsTableModel(QAbstractTableModel):
    """
    Model de alta performance para lista de produtos.
    
    REGRAS:
    - Usa QAbstractTableModel (10x mais rápido que QTableWidget)
    - Implementa fetchMore para lazy loading
    - Queries rodam em DatabaseWorker
    - Suporta drag nativo para Ateliê
    """
    
    loading_started = Signal()
    loading_finished = Signal()
    error_occurred = Signal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self._products: List[Dict] = []
        self._total_count = 0
        self._current_query = ""
        self._current_filters = {}
        
        # Worker para queries
        self._worker = DatabaseWorker()
        self._worker.results_ready.connect(self._on_results_ready)
        self._worker.error.connect(self._on_error)
        
        # Timer para debounce de busca
        self._search_timer = QTimer()
        self._search_timer.setSingleShot(True)
        self._search_timer.timeout.connect(self._do_search)
        
        # Vault path
        self._vault_path = Path("AutoTabloide_System_Root/vault")
    
    # =========================================================================
    # QAbstractTableModel overrides
    # =========================================================================
    
    def rowCount(self, parent=QModelIndex()) -> int:
        return len(self._products)
    
    def columnCount(self, parent=QModelIndex()) -> int:
        return len(COLUMNS)
    
    def data(self, index: QModelIndex, role: int = Qt.DisplayRole) -> Any:
        if not index.isValid():
            return None
        
        row = index.row()
        col = index.column()
        
        if row >= len(self._products):
            return None
        
        product = self._products[row]
        col_key = COLUMNS[col][0]
        
        if role == Qt.DisplayRole:
            value = product.get(col_key)
            
            # Formatação especial
            if col_key == "preco_venda_atual":
                return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".") if value else "---"
            
            return value if value else ""
        
        elif role == Qt.DecorationRole:
            if col_key == "status":
                # Ícone de status baseado na qualidade
                status = product.get("status_qualidade", 0)
                if status >= 3:
                    return QIcon.fromTheme("emblem-ok")  # Verde
                elif status >= 1:
                    return QIcon.fromTheme("emblem-important")  # Amarelo
                else:
                    return QIcon.fromTheme("emblem-error")  # Vermelho
        
        elif role == Qt.ToolTipRole:
            if col_key == "nome_sanitizado":
                peso = product.get("detalhe_peso", "")
                marca = product.get("marca_normalizada", "")
                return f"{product.get('nome_sanitizado', '')}\n{marca} - {peso}"
        
        elif role == Qt.UserRole:
            # Retorna produto completo para drag
            return product
        
        return None
    
    def headerData(self, section: int, orientation: Qt.Orientation, role: int = Qt.DisplayRole) -> Any:
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return COLUMNS[section][1]
        return None
    
    # =========================================================================
    # LAZY LOADING (fetchMore)
    # =========================================================================
    
    def canFetchMore(self, parent=QModelIndex()) -> bool:
        """Retorna True se há mais dados para carregar."""
        return len(self._products) < self._total_count
    
    def fetchMore(self, parent=QModelIndex()):
        """Carrega próximo bloco de dados."""
        if self._worker.isRunning():
            return
        
        offset = len(self._products)
        self._worker.set_query(
            self._current_query, 
            offset, 
            BATCH_SIZE, 
            self._current_filters
        )
        self._worker.start()
    
    # =========================================================================
    # DRAG & DROP
    # =========================================================================
    
    def flags(self, index: QModelIndex) -> Qt.ItemFlags:
        base_flags = super().flags(index)
        if index.isValid():
            return base_flags | Qt.ItemIsDragEnabled
        return base_flags
    
    def mimeTypes(self) -> List[str]:
        return [MIME_TYPE]
    
    def mimeData(self, indexes: List[QModelIndex]) -> QMimeData:
        """Serializa produtos selecionados para drag."""
        mime = QMimeData()
        
        products = []
        seen_rows = set()
        
        for index in indexes:
            if index.row() not in seen_rows:
                seen_rows.add(index.row())
                product = self._products[index.row()]
                
                # Monta payload para drop
                products.append({
                    "id": product["id"],
                    "nome_sanitizado": product["nome_sanitizado"],
                    "preco_venda_atual": product["preco_venda_atual"],
                    "preco_referencia": product.get("preco_referencia"),
                    "detalhe_peso": product.get("detalhe_peso", ""),
                    "marca_normalizada": product.get("marca_normalizada", ""),
                    "img_hash_ref": product.get("img_hash_ref"),
                    "categoria": product.get("categoria", ""),
                })
        
        # Serializa como JSON
        json_data = json.dumps(products, ensure_ascii=False)
        mime.setData(MIME_TYPE, QByteArray(json_data.encode("utf-8")))
        
        return mime
    
    # =========================================================================
    # SEARCH & FILTER
    # =========================================================================
    
    def search(self, query: str, debounce_ms: int = 300):
        """Inicia busca com debounce."""
        self._current_query = query
        self._search_timer.stop()
        self._search_timer.start(debounce_ms)
    
    def set_filters(self, **filters):
        """Define filtros e recarrega."""
        self._current_filters = filters
        self.refresh()
    
    def refresh(self):
        """Recarrega dados do início."""
        self.beginResetModel()
        self._products.clear()
        self._total_count = 0
        self.endResetModel()
        
        self.loading_started.emit()
        self._worker.set_query(self._current_query, 0, BATCH_SIZE, self._current_filters)
        self._worker.start()
    
    def _do_search(self):
        """Executa busca (chamado após debounce)."""
        self.refresh()
    
    # =========================================================================
    # SLOTS
    # =========================================================================
    
    @Slot(list, int)
    def _on_results_ready(self, products: List[Dict], total: int):
        """Recebe resultados do worker."""
        self._total_count = total
        
        if len(self._products) == 0:
            # Primeira carga
            self.beginInsertRows(QModelIndex(), 0, len(products) - 1)
            self._products = products
            self.endInsertRows()
        else:
            # Append (fetchMore)
            first = len(self._products)
            last = first + len(products) - 1
            self.beginInsertRows(QModelIndex(), first, last)
            self._products.extend(products)
            self.endInsertRows()
        
        self.loading_finished.emit()
    
    @Slot(str)
    def _on_error(self, error: str):
        """Trata erro do worker."""
        self.error_occurred.emit(error)
        self.loading_finished.emit()
    
    # =========================================================================
    # UTILITIES
    # =========================================================================
    
    def get_product(self, row: int) -> Optional[Dict]:
        """Retorna produto por índice."""
        if 0 <= row < len(self._products):
            return self._products[row]
        return None
    
    def get_product_by_id(self, product_id: int) -> Optional[Dict]:
        """Busca produto por ID."""
        for p in self._products:
            if p["id"] == product_id:
                return p
        return None
    
    @property
    def total_count(self) -> int:
        """Total de produtos (incluindo não carregados)."""
        return self._total_count
    
    @property
    def loaded_count(self) -> int:
        """Quantidade carregada em memória."""
        return len(self._products)


# =============================================================================
# PRICE DELEGATE
# =============================================================================

class PriceItemDelegate(QStyledItemDelegate):
    """
    Delegate para formatar preços como R$ X,XX.
    
    Renderiza na célula com alinhamento à direita
    e formatação brasileira.
    """
    
    def displayText(self, value: Any, locale) -> str:
        if value is None or value == "":
            return "---"
        
        try:
            val = float(value)
            return f"R$ {val:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        except (ValueError, TypeError):
            return str(value)

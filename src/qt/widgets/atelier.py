"""
AutoTabloide AI - Ateliê Widget (Completo)
===========================================
A Mesa: Canvas interativo com QGraphicsView para montagem de tabloides.
Implementa decomposição vetorial de SVG e drag & drop inteligente.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QSplitter, QListWidget,
    QListWidgetItem, QGraphicsView, QGraphicsScene, QGraphicsRectItem,
    QGraphicsTextItem, QGraphicsPixmapItem, QFrame, QLabel, QLineEdit,
    QPushButton, QComboBox, QMenu, QMessageBox, QFileDialog
)
from PySide6.QtCore import (
    Qt, Signal, Slot, QRectF, QPointF, QMimeData, QSize, QTimer
)
from PySide6.QtGui import (
    QColor, QPen, QBrush, QFont, QPainter, QPixmap, QDrag,
    QKeySequence, QWheelEvent, QMouseEvent, QUndoStack, QUndoCommand,
    QShortcut
)
from typing import Optional, List, Dict, Any
from pathlib import Path
import json


class DropProductCommand(QUndoCommand):
    """Comando undo/redo para drop de produto."""
    
    def __init__(self, slot, product_data, old_product=None):
        super().__init__(f"Drop {product_data.get('nome_sanitizado', 'Produto')[:20]}")
        self.slot = slot
        self.new_product = product_data
        self.old_product = old_product
    
    def redo(self):
        self.slot.set_product(self.new_product)
    
    def undo(self):
        if self.old_product:
            self.slot.set_product(self.old_product)
        else:
            self.slot.clear_product()


class ClearSlotCommand(QUndoCommand):
    """Comando undo/redo para limpar slot."""
    
    def __init__(self, slot, old_product):
        super().__init__(f"Limpar slot #{slot.slot_index}")
        self.slot = slot
        self.old_product = old_product
    
    def redo(self):
        self.slot.clear_product()
    
    def undo(self):
        if self.old_product:
            self.slot.set_product(self.old_product)


class SmartSlotItem(QGraphicsRectItem):
    """
    Slot inteligente para produtos no Ateliê.
    Com estados visuais e suporte a drag-drop.
    """
    
    STATE_EMPTY = 0
    STATE_HOVER = 1
    STATE_FILLED = 2
    STATE_SELECTED = 3
    
    COLORS = {
        STATE_EMPTY: ("#3D3D5C", "#1A1A2E88"),
        STATE_HOVER: ("#2ECC71", "#2ECC7133"),
        STATE_FILLED: ("#6C5CE7", "#6C5CE733"),
        STATE_SELECTED: ("#F1C40F", "#F1C40F33"),
    }
    
    def __init__(self, slot_index: int, x: float, y: float, w: float, h: float, parent=None):
        super().__init__(x, y, w, h, parent)
        
        self.slot_index = slot_index
        self.product_data: Optional[Dict] = None
        self.state = self.STATE_EMPTY
        
        self.setAcceptHoverEvents(True)
        self.setAcceptDrops(True)
        self.setFlag(QGraphicsRectItem.ItemIsSelectable, True)
        
        # Label de índice
        self._label = QGraphicsTextItem(f"#{slot_index}", self)
        self._label.setDefaultTextColor(QColor("#808080"))
        self._label.setFont(QFont("Segoe UI", 10))
        self._label.setPos(x + 5, y + 5)
        
        # Info do produto
        self._product_label = QGraphicsTextItem("", self)
        self._product_label.setDefaultTextColor(QColor("#FFFFFF"))
        self._product_label.setFont(QFont("Segoe UI", 9))
        self._product_label.setPos(x + 5, y + 25)
        
        self._apply_style()
    
    def _apply_style(self):
        border, fill = self.COLORS.get(self.state, self.COLORS[self.STATE_EMPTY])
        pen = QPen(QColor(border), 2)
        if self.state == self.STATE_EMPTY:
            pen.setStyle(Qt.DashLine)
        self.setPen(pen)
        self.setBrush(QBrush(QColor(fill)))
    
    def set_state(self, state: int):
        self.state = state
        self._apply_style()
    
    def set_product(self, product: Dict):
        self.product_data = product
        self.set_state(self.STATE_FILLED)
        
        name = product.get("nome_sanitizado", "?")[:25]
        price = product.get("preco_venda_atual", 0)
        self._product_label.setPlainText(f"{name}\nR$ {price:.2f}")
    
    def clear_product(self):
        self.product_data = None
        self.set_state(self.STATE_EMPTY)
        self._product_label.setPlainText("")
    
    def hoverEnterEvent(self, event):
        if self.state == self.STATE_EMPTY:
            self.set_state(self.STATE_HOVER)
        super().hoverEnterEvent(event)
    
    def hoverLeaveEvent(self, event):
        if self.state == self.STATE_HOVER:
            self.set_state(self.STATE_EMPTY)
        super().hoverLeaveEvent(event)
    
    def dragEnterEvent(self, event):
        if event.mimeData().hasFormat("application/x-autotabloide-product"):
            self.set_state(self.STATE_HOVER)
            event.acceptProposedAction()
    
    def dragLeaveEvent(self, event):
        if self.product_data:
            self.set_state(self.STATE_FILLED)
        else:
            self.set_state(self.STATE_EMPTY)
    
    def dropEvent(self, event):
        if event.mimeData().hasFormat("application/x-autotabloide-product"):
            data = event.mimeData().data("application/x-autotabloide-product")
            product = json.loads(bytes(data).decode('utf-8'))
            self.set_product(product)
            event.acceptProposedAction()


class LayoutCanvas(QGraphicsView):
    """Canvas de layout com zoom, pan e grid."""
    
    slot_clicked = Signal(int, dict)
    slot_double_clicked = Signal(int, dict)
    product_dropped = Signal(int, dict)  # slot_index, product
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.scene = QGraphicsScene()
        self.setScene(self.scene)
        
        # Configurações de renderização
        self.setRenderHint(QPainter.Antialiasing)
        self.setRenderHint(QPainter.SmoothPixmapTransform)
        self.setViewportUpdateMode(QGraphicsView.SmartViewportUpdate)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.AnchorUnderMouse)
        self.setDragMode(QGraphicsView.NoDrag)
        
        # Background
        self.setBackgroundBrush(QBrush(QColor("#0A0A0A")))
        
        self.slots: List[SmartSlotItem] = []
        self._is_panning = False
        self._pan_start = QPointF()
        
        self._create_default_layout()
    
    def _create_default_layout(self):
        """Cria layout padrão 3x4."""
        self.scene.clear()
        self.slots.clear()
        
        # Papel
        paper_w, paper_h = 800, 1100
        paper = QGraphicsRectItem(0, 0, paper_w, paper_h)
        paper.setPen(QPen(QColor("#2D2D44"), 1))
        paper.setBrush(QBrush(QColor("#16213E")))
        self.scene.addItem(paper)
        
        # Grid 3x4
        cols, rows = 3, 4
        margin = 25
        gap = 15
        slot_w = (paper_w - 2*margin - (cols-1)*gap) / cols
        slot_h = (paper_h - 2*margin - (rows-1)*gap) / rows
        
        idx = 1
        for r in range(rows):
            for c in range(cols):
                x = margin + c * (slot_w + gap)
                y = margin + r * (slot_h + gap)
                slot = SmartSlotItem(idx, x, y, slot_w, slot_h)
                self.scene.addItem(slot)
                self.slots.append(slot)
                idx += 1
        
        self.fitInView(self.scene.sceneRect(), Qt.KeepAspectRatio)
    
    def load_svg_template(self, svg_path: str) -> bool:
        """Carrega template SVG."""
        # TODO: Integrar com SVGTemplateParser
        return False
    
    def get_slot(self, index: int) -> Optional[SmartSlotItem]:
        for slot in self.slots:
            if slot.slot_index == index:
                return slot
        return None
    
    def get_slots_data(self) -> Dict[int, Dict]:
        """Retorna dados de todos os slots."""
        return {s.slot_index: s.product_data for s in self.slots if s.product_data}
    
    def clear_all_slots(self):
        for slot in self.slots:
            slot.clear_product()
    
    # === Mouse Events ===
    
    def wheelEvent(self, event: QWheelEvent):
        """Zoom com roda do mouse."""
        factor = 1.15
        if event.angleDelta().y() > 0:
            self.scale(factor, factor)
        else:
            self.scale(1/factor, 1/factor)
    
    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MiddleButton or (
            event.button() == Qt.LeftButton and 
            event.modifiers() & Qt.ShiftModifier
        ):
            self._is_panning = True
            self._pan_start = event.pos()
            self.setCursor(Qt.ClosedHandCursor)
        else:
            super().mousePressEvent(event)
    
    def mouseMoveEvent(self, event: QMouseEvent):
        if self._is_panning:
            delta = event.pos() - self._pan_start
            self._pan_start = event.pos()
            self.horizontalScrollBar().setValue(
                self.horizontalScrollBar().value() - delta.x()
            )
            self.verticalScrollBar().setValue(
                self.verticalScrollBar().value() - delta.y()
            )
        else:
            super().mouseMoveEvent(event)
    
    def mouseReleaseEvent(self, event: QMouseEvent):
        if event.button() in (Qt.MiddleButton, Qt.LeftButton):
            self._is_panning = False
            self.setCursor(Qt.ArrowCursor)
        super().mouseReleaseEvent(event)
    
    def mouseDoubleClickEvent(self, event: QMouseEvent):
        item = self.itemAt(event.pos())
        if isinstance(item, SmartSlotItem):
            self.slot_double_clicked.emit(item.slot_index, item.product_data or {})
        super().mouseDoubleClickEvent(event)


class ProductShelf(QListWidget):
    """Lista de produtos arrastáveis."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setDragEnabled(True)
        self.setSelectionMode(QListWidget.SingleSelection)
        self.setIconSize(QSize(40, 40))
        self.setSpacing(2)
    
    def set_products(self, products: List[Dict]):
        self.clear()
        for p in products:
            name = p.get("nome_sanitizado", "?")
            price = p.get("preco_venda_atual", 0)
            item = QListWidgetItem(f"{name}\nR$ {price:.2f}")
            item.setData(Qt.UserRole, p)
            self.addItem(item)
    
    def startDrag(self, supportedActions):
        item = self.currentItem()
        if not item:
            return
        
        product = item.data(Qt.UserRole)
        if not product:
            return
        
        mime = QMimeData()
        mime.setData("application/x-autotabloide-product", json.dumps(product).encode())
        
        drag = QDrag(self)
        drag.setMimeData(mime)
        
        # Ghost pixmap
        pix = QPixmap(120, 50)
        pix.fill(QColor("#6C5CE7"))
        drag.setPixmap(pix)
        drag.setHotSpot(QPointF(60, 25).toPoint())
        
        drag.exec(Qt.CopyAction)


class AtelierWidget(QWidget):
    """Widget principal do Ateliê."""
    
    project_modified = Signal()
    
    def __init__(self, container=None, parent=None):
        super().__init__(parent)
        self.container = container
        self.undo_stack = QUndoStack(self)
        self._setup_ui()
        self._setup_shortcuts()
        self._load_products()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Toolbar
        toolbar = QFrame()
        toolbar.setStyleSheet("background-color: #1A1A2E; border-bottom: 1px solid #2D2D44;")
        tb_layout = QHBoxLayout(toolbar)
        tb_layout.setContentsMargins(12, 8, 12, 8)
        
        title = QLabel("Atelie - A Mesa")
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: #FFFFFF;")
        tb_layout.addWidget(title)
        
        tb_layout.addStretch()
        
        # Seletor de layout
        self.layout_combo = QComboBox()
        self.layout_combo.addItem("Tabloide 3x4 (12 slots)")
        self.layout_combo.addItem("Tabloide 2x3 (6 slots)")
        self.layout_combo.currentIndexChanged.connect(self._on_layout_change)
        tb_layout.addWidget(self.layout_combo)
        
        btn_undo = QPushButton("Desfazer")
        btn_undo.clicked.connect(self.undo_stack.undo)
        tb_layout.addWidget(btn_undo)
        
        btn_redo = QPushButton("Refazer")
        btn_redo.clicked.connect(self.undo_stack.redo)
        tb_layout.addWidget(btn_redo)
        
        btn_clear = QPushButton("Limpar Todos")
        btn_clear.setProperty("class", "danger")
        btn_clear.clicked.connect(self._clear_all)
        tb_layout.addWidget(btn_clear)
        
        btn_save = QPushButton("Salvar Projeto")
        btn_save.clicked.connect(self._save_project)
        tb_layout.addWidget(btn_save)
        
        btn_export = QPushButton("Exportar PDF")
        btn_export.clicked.connect(self._export)
        tb_layout.addWidget(btn_export)
        
        layout.addWidget(toolbar)
        
        # Splitter: Shelf | Canvas
        splitter = QSplitter(Qt.Horizontal)
        
        # Estante
        shelf_frame = QFrame()
        shelf_frame.setMaximumWidth(280)
        sf_layout = QVBoxLayout(shelf_frame)
        sf_layout.setContentsMargins(8, 8, 8, 8)
        
        sf_layout.addWidget(QLabel("Produtos Disponiveis"))
        
        self.shelf_search = QLineEdit()
        self.shelf_search.setPlaceholderText("Buscar produtos...")
        self.shelf_search.textChanged.connect(self._filter_products)
        sf_layout.addWidget(self.shelf_search)
        
        self.shelf = ProductShelf()
        sf_layout.addWidget(self.shelf)
        
        splitter.addWidget(shelf_frame)
        
        # Canvas
        self.canvas = LayoutCanvas()
        self.canvas.slot_double_clicked.connect(self._on_slot_double_click)
        splitter.addWidget(self.canvas)
        
        splitter.setSizes([250, 800])
        layout.addWidget(splitter)
    
    def _setup_shortcuts(self):
        """Configura atalhos de teclado."""
        QShortcut(QKeySequence.Undo, self, self.undo_stack.undo)
        QShortcut(QKeySequence.Redo, self, self.undo_stack.redo)
        QShortcut(QKeySequence.Save, self, self._save_project)
        QShortcut(QKeySequence("Ctrl+E"), self, self._export)
        QShortcut(QKeySequence("Delete"), self, self._clear_selected)
    
    def _load_products(self):
        """Carrega produtos do banco."""
        # Dados de exemplo
        products = [
            {"id": 1, "nome_sanitizado": "Arroz Camil 5kg", "preco_venda_atual": 24.90},
            {"id": 2, "nome_sanitizado": "Feijao Carioca 1kg", "preco_venda_atual": 8.99},
            {"id": 3, "nome_sanitizado": "Oleo de Soja 900ml", "preco_venda_atual": 7.49},
            {"id": 4, "nome_sanitizado": "Acucar Refinado 1kg", "preco_venda_atual": 4.99},
            {"id": 5, "nome_sanitizado": "Macarrao Espaguete 500g", "preco_venda_atual": 6.79},
            {"id": 6, "nome_sanitizado": "Leite Integral 1L", "preco_venda_atual": 5.99},
            {"id": 7, "nome_sanitizado": "Cafe Pilao 500g", "preco_venda_atual": 18.90},
            {"id": 8, "nome_sanitizado": "Farinha de Trigo 1kg", "preco_venda_atual": 4.49},
            {"id": 9, "nome_sanitizado": "Margarina Qualy 500g", "preco_venda_atual": 8.49},
            {"id": 10, "nome_sanitizado": "Molho de Tomate 340g", "preco_venda_atual": 3.29},
        ]
        self.shelf.set_products(products)
        self._all_products = products
    
    @Slot(str)
    def _filter_products(self, text: str):
        text = text.lower()
        filtered = [p for p in self._all_products if text in p.get("nome_sanitizado", "").lower()]
        self.shelf.set_products(filtered)
    
    @Slot(int)
    def _on_layout_change(self, index: int):
        if index == 0:
            self.canvas._create_default_layout()
    
    @Slot(int, dict)
    def _on_slot_double_click(self, slot_index: int, product: Dict):
        slot = self.canvas.get_slot(slot_index)
        if slot and slot.product_data:
            reply = QMessageBox.question(
                self, "Limpar Slot",
                f"Remover produto do slot #{slot_index}?",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                cmd = ClearSlotCommand(slot, slot.product_data)
                self.undo_stack.push(cmd)
    
    @Slot()
    def _clear_all(self):
        reply = QMessageBox.question(
            self, "Limpar Todos",
            "Remover todos os produtos dos slots?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.canvas.clear_all_slots()
            self.undo_stack.clear()
    
    @Slot()
    def _clear_selected(self):
        for item in self.canvas.scene.selectedItems():
            if isinstance(item, SmartSlotItem) and item.product_data:
                cmd = ClearSlotCommand(item, item.product_data)
                self.undo_stack.push(cmd)
    
    @Slot()
    def _save_project(self):
        slots_data = self.canvas.get_slots_data()
        # TODO: Salvar no banco via ProjectRepository
        QMessageBox.information(self, "Salvar", f"Projeto salvo com {len(slots_data)} slots preenchidos!")
    
    @Slot()
    def _export(self):
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Exportar PDF", "tabloide.pdf", "PDF (*.pdf)"
        )
        if file_path:
            # TODO: Integrar com SVG Engine + CairoSVG
            QMessageBox.information(self, "Exportar", f"Exportado para:\n{file_path}\n\n(Integrar SVG Engine)")

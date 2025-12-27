"""
AutoTabloide AI - Atelier Widget
=================================
A Mesa: Canvas interativo com QGraphicsView para montagem de tabloides.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QSplitter, QListWidget,
    QListWidgetItem, QGraphicsView, QGraphicsScene, QGraphicsRectItem,
    QGraphicsTextItem, QGraphicsPixmapItem, QFrame, QLabel, QLineEdit,
    QPushButton, QComboBox, QMenu, QMessageBox
)
from PySide6.QtCore import (
    Qt, Signal, Slot, QRectF, QPointF, QMimeData, QSize
)
from PySide6.QtGui import (
    QColor, QPen, QBrush, QFont, QPainter, QPixmap, QDrag
)
from typing import Optional, List, Dict, Any


class SlotGraphicsItem(QGraphicsRectItem):
    """Item gráfico representando um slot no layout."""
    
    def __init__(
        self, 
        slot_index: int,
        x: float, 
        y: float, 
        width: float, 
        height: float,
        parent=None
    ):
        super().__init__(x, y, width, height, parent)
        self.slot_index = slot_index
        self.product_data: Optional[Dict[str, Any]] = None
        
        # Estilo padrão (vazio)
        self._empty_style()
        
        # Texto de índice
        self.index_label = QGraphicsTextItem(f"#{slot_index}", self)
        self.index_label.setDefaultTextColor(QColor("#808080"))
        self.index_label.setFont(QFont("Segoe UI", 10))
        self.index_label.setPos(x + 5, y + 5)
        
        # Aceita drops
        self.setAcceptDrops(True)
        self.setFlag(QGraphicsRectItem.ItemIsSelectable, True)
    
    def _empty_style(self) -> None:
        """Aplica estilo de slot vazio."""
        self.setPen(QPen(QColor("#3D3D5C"), 2, Qt.DashLine))
        self.setBrush(QBrush(QColor("#1A1A2E44")))
    
    def _filled_style(self) -> None:
        """Aplica estilo de slot preenchido."""
        self.setPen(QPen(QColor("#6C5CE7"), 2))
        self.setBrush(QBrush(QColor("#6C5CE722")))
    
    def _hover_style(self) -> None:
        """Aplica estilo de hover/drag-over."""
        self.setPen(QPen(QColor("#2ECC71"), 3))
        self.setBrush(QBrush(QColor("#2ECC7133")))
    
    def set_product(self, product: Dict[str, Any]) -> None:
        """Define o produto no slot."""
        self.product_data = product
        self._filled_style()
        
        # Atualiza label com nome do produto
        name = product.get("nome_sanitizado", "Produto")
        price = product.get("preco_venda_atual", 0)
        
        self.index_label.setPlainText(f"#{self.slot_index}\n{name}\nR$ {price:.2f}")
        self.index_label.setDefaultTextColor(QColor("#FFFFFF"))
    
    def clear_product(self) -> None:
        """Remove o produto do slot."""
        self.product_data = None
        self._empty_style()
        self.index_label.setPlainText(f"#{self.slot_index}")
        self.index_label.setDefaultTextColor(QColor("#808080"))
    
    def dragEnterEvent(self, event) -> None:
        """Handler de drag enter."""
        if event.mimeData().hasFormat("application/x-autotabloide-product"):
            self._hover_style()
            event.acceptProposedAction()
        else:
            event.ignore()
    
    def dragLeaveEvent(self, event) -> None:
        """Handler de drag leave."""
        if self.product_data:
            self._filled_style()
        else:
            self._empty_style()
    
    def dropEvent(self, event) -> None:
        """Handler de drop."""
        if event.mimeData().hasFormat("application/x-autotabloide-product"):
            # Decodifica dados do produto
            data = event.mimeData().data("application/x-autotabloide-product")
            import json
            product = json.loads(bytes(data).decode('utf-8'))
            self.set_product(product)
            event.acceptProposedAction()
        else:
            event.ignore()


class LayoutCanvas(QGraphicsView):
    """Canvas para visualização e edição do layout."""
    
    slot_clicked = Signal(int, dict)  # slot_index, product_data
    slot_double_clicked = Signal(int, dict)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.scene = QGraphicsScene()
        self.setScene(self.scene)
        
        # Configurações
        self.setRenderHint(QPainter.Antialiasing)
        self.setRenderHint(QPainter.SmoothPixmapTransform)
        self.setViewportUpdateMode(QGraphicsView.SmartViewportUpdate)
        self.setDragMode(QGraphicsView.ScrollHandDrag)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        
        # Background
        self.setBackgroundBrush(QBrush(QColor("#121212")))
        
        # Slots
        self.slots: List[SlotGraphicsItem] = []
        
        # Layout placeholder
        self._create_placeholder_layout()
    
    def _create_placeholder_layout(self) -> None:
        """Cria layout de placeholder (3x4 grid)."""
        self.scene.clear()
        self.slots.clear()
        
        # Dimensões do layout
        layout_width = 800
        layout_height = 1000
        
        # Background do papel
        paper = QGraphicsRectItem(0, 0, layout_width, layout_height)
        paper.setPen(QPen(QColor("#2D2D44"), 1))
        paper.setBrush(QBrush(QColor("#16213e")))
        self.scene.addItem(paper)
        
        # Grid 3x4 de slots
        cols, rows = 3, 4
        margin = 20
        spacing = 15
        slot_width = (layout_width - 2 * margin - (cols - 1) * spacing) / cols
        slot_height = (layout_height - 2 * margin - (rows - 1) * spacing) / rows
        
        slot_index = 1
        for row in range(rows):
            for col in range(cols):
                x = margin + col * (slot_width + spacing)
                y = margin + row * (slot_height + spacing)
                
                slot = SlotGraphicsItem(slot_index, x, y, slot_width, slot_height)
                self.scene.addItem(slot)
                self.slots.append(slot)
                slot_index += 1
        
        # Ajusta view
        self.fitInView(self.scene.sceneRect(), Qt.KeepAspectRatio)
    
    def load_layout(self, layout_data: Dict[str, Any]) -> None:
        """Carrega um layout SVG."""
        # TODO: Implementar carregamento real de SVG
        self._create_placeholder_layout()
    
    def get_slot(self, index: int) -> Optional[SlotGraphicsItem]:
        """Retorna slot pelo índice."""
        for slot in self.slots:
            if slot.slot_index == index:
                return slot
        return None
    
    def wheelEvent(self, event) -> None:
        """Zoom com scroll do mouse."""
        factor = 1.15
        if event.angleDelta().y() > 0:
            self.scale(factor, factor)
        else:
            self.scale(1 / factor, 1 / factor)
    
    def mouseDoubleClickEvent(self, event) -> None:
        """Handler de double-click."""
        super().mouseDoubleClickEvent(event)
        item = self.itemAt(event.pos())
        if isinstance(item, SlotGraphicsItem):
            self.slot_double_clicked.emit(item.slot_index, item.product_data or {})


class ProductShelf(QListWidget):
    """Prateleira de produtos (drag source)."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setDragEnabled(True)
        self.setSelectionMode(QListWidget.SingleSelection)
        self.setIconSize(QSize(48, 48))
        self.setSpacing(4)
        
        # Estilo
        self.setStyleSheet("""
            QListWidget {
                background-color: #1A1A2E;
                border: 1px solid #2D2D44;
                border-radius: 8px;
            }
            QListWidget::item {
                background-color: #16213e;
                border-radius: 6px;
                padding: 8px;
                margin: 2px;
            }
            QListWidget::item:selected {
                background-color: #6C5CE744;
                border: 1px solid #6C5CE7;
            }
            QListWidget::item:hover {
                background-color: #2D2D44;
            }
        """)
    
    def set_products(self, products: List[Dict[str, Any]]) -> None:
        """Define lista de produtos."""
        self.clear()
        for product in products:
            item = QListWidgetItem(
                f"{product.get('nome_sanitizado', 'Produto')}\n"
                f"R$ {product.get('preco_venda_atual', 0):.2f}"
            )
            item.setData(Qt.UserRole, product)
            self.addItem(item)
    
    def startDrag(self, supportedActions) -> None:
        """Inicia drag de produto."""
        item = self.currentItem()
        if not item:
            return
        
        product = item.data(Qt.UserRole)
        if not product:
            return
        
        # Cria mime data
        import json
        mime_data = QMimeData()
        mime_data.setData(
            "application/x-autotabloide-product",
            json.dumps(product).encode('utf-8')
        )
        
        # Cria drag
        drag = QDrag(self)
        drag.setMimeData(mime_data)
        
        # Pixmap de arraste (opcional)
        pixmap = QPixmap(100, 40)
        pixmap.fill(QColor("#6C5CE7"))
        drag.setPixmap(pixmap)
        drag.setHotSpot(QPointF(50, 20).toPoint())
        
        drag.exec(Qt.CopyAction)


class AtelierWidget(QWidget):
    """Widget principal do Ateliê (A Mesa)."""
    
    def __init__(self, container=None, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.container = container
        self._setup_ui()
        self._load_data()
    
    def _setup_ui(self) -> None:
        """Configura interface."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Toolbar
        toolbar = QFrame()
        toolbar.setStyleSheet("""
            QFrame {
                background-color: #1A1A2E;
                border-bottom: 1px solid #2D2D44;
                padding: 8px 16px;
            }
        """)
        toolbar_layout = QHBoxLayout(toolbar)
        toolbar_layout.setContentsMargins(16, 8, 16, 8)
        
        title = QLabel("🎨 Ateliê - A Mesa")
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: #FFFFFF;")
        toolbar_layout.addWidget(title)
        
        toolbar_layout.addStretch()
        
        # Seletor de layout
        self.layout_selector = QComboBox()
        self.layout_selector.addItem("📄 Tabloide 3x4 (12 slots)")
        self.layout_selector.addItem("📄 Tabloide 2x3 (6 slots)")
        self.layout_selector.addItem("📋 Cartaz A4")
        toolbar_layout.addWidget(self.layout_selector)
        
        # Botões de ação
        btn_clear = QPushButton("🗑️ Limpar Todos")
        btn_clear.clicked.connect(self._clear_all_slots)
        toolbar_layout.addWidget(btn_clear)
        
        btn_save = QPushButton("💾 Salvar Projeto")
        btn_save.clicked.connect(self._save_project)
        toolbar_layout.addWidget(btn_save)
        
        btn_export = QPushButton("📤 Exportar")
        btn_export.setProperty("class", "primary")
        btn_export.clicked.connect(self._export)
        toolbar_layout.addWidget(btn_export)
        
        layout.addWidget(toolbar)
        
        # Splitter: Shelf | Canvas
        splitter = QSplitter(Qt.Horizontal)
        splitter.setHandleWidth(2)
        
        # Painel esquerdo: Estante
        shelf_frame = QFrame()
        shelf_frame.setMaximumWidth(300)
        shelf_layout = QVBoxLayout(shelf_frame)
        shelf_layout.setContentsMargins(8, 8, 8, 8)
        shelf_layout.setSpacing(8)
        
        shelf_title = QLabel("📦 Produtos")
        shelf_title.setStyleSheet("font-weight: bold; color: #FFFFFF;")
        shelf_layout.addWidget(shelf_title)
        
        self.shelf_search = QLineEdit()
        self.shelf_search.setPlaceholderText("🔍 Buscar...")
        shelf_layout.addWidget(self.shelf_search)
        
        self.shelf = ProductShelf()
        shelf_layout.addWidget(self.shelf)
        
        splitter.addWidget(shelf_frame)
        
        # Painel direito: Canvas
        self.canvas = LayoutCanvas()
        self.canvas.slot_double_clicked.connect(self._on_slot_double_click)
        splitter.addWidget(self.canvas)
        
        splitter.setSizes([250, 800])
        
        layout.addWidget(splitter)
    
    def _load_data(self) -> None:
        """Carrega dados iniciais."""
        # Produtos de exemplo
        sample_products = [
            {"id": 1, "nome_sanitizado": "Arroz Camil 5kg", "preco_venda_atual": 24.90},
            {"id": 2, "nome_sanitizado": "Feijão Carioca 1kg", "preco_venda_atual": 8.99},
            {"id": 3, "nome_sanitizado": "Óleo de Soja 900ml", "preco_venda_atual": 7.49},
            {"id": 4, "nome_sanitizado": "Açúcar Refinado 1kg", "preco_venda_atual": 4.99},
            {"id": 5, "nome_sanitizado": "Macarrão Espaguete 500g", "preco_venda_atual": 6.79},
            {"id": 6, "nome_sanitizado": "Leite Integral 1L", "preco_venda_atual": 5.99},
            {"id": 7, "nome_sanitizado": "Café Pilão 500g", "preco_venda_atual": 18.90},
            {"id": 8, "nome_sanitizado": "Farinha de Trigo 1kg", "preco_venda_atual": 4.49},
        ]
        self.shelf.set_products(sample_products)
    
    @Slot(int, dict)
    def _on_slot_double_click(self, slot_index: int, product_data: Dict) -> None:
        """Handler de double-click em slot."""
        if product_data:
            QMessageBox.information(
                self,
                "Override de Slot",
                f"Slot #{slot_index}\nProduto: {product_data.get('nome_sanitizado', 'N/A')}\n\n"
                "(Diálogo de override em desenvolvimento)"
            )
        else:
            QMessageBox.information(
                self,
                "Slot Vazio",
                f"Slot #{slot_index} está vazio.\nArraste um produto da estante para preenchê-lo."
            )
    
    @Slot()
    def _clear_all_slots(self) -> None:
        """Limpa todos os slots."""
        reply = QMessageBox.question(
            self,
            "Limpar Todos",
            "Deseja realmente limpar todos os slots?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            for slot in self.canvas.slots:
                slot.clear_product()
    
    @Slot()
    def _save_project(self) -> None:
        """Salva o projeto atual."""
        # TODO: Implementar salvamento
        QMessageBox.information(self, "Salvar", "Projeto salvo! (simulação)")
    
    @Slot()
    def _export(self) -> None:
        """Exporta o layout."""
        # TODO: Implementar exportação
        QMessageBox.information(self, "Exportar", "Exportação em desenvolvimento")

"""
AutoTabloide AI - Atelier View Industrial Grade
================================================
PROTOCOLO DE CONVERGÊNCIA INDUSTRIAL - Fase 2
Passos 16-18, 28-40: AtelierView e AtelierScene completos.

Este é o editor vetorial real, não uma visualização estática.
"""

from __future__ import annotations
from pathlib import Path
from typing import Optional, Dict, List, Any
import json

from PySide6.QtCore import (
    Qt, Signal, Slot, QRectF, QPointF, QSizeF, QTimer
)
from PySide6.QtWidgets import (
    QGraphicsView, QGraphicsScene, QGraphicsItem,
    QGraphicsRectItem, QGraphicsLineItem, QWidget,
    QVBoxLayout, QHBoxLayout, QFrame, QLabel, QPushButton,
    QComboBox, QSpinBox, QSplitter, QListWidget, QListWidgetItem,
    QFileDialog, QMessageBox,
    QMenu
)
from PySide6.QtGui import (
    QPainter, QColor, QPen, QBrush, QFont, QPixmap,
    QKeySequence, QWheelEvent, QMouseEvent, QDragEnterEvent,
    QDropEvent, QShortcut, QTransform, QCursor, QUndoStack, QUndoCommand
)

from ..graphics.smart_items import (
    SmartGraphicsItem, SmartSlotItem, SmartImageItem,
    SmartTextItem, SmartPriceItem
)
from ..rendering.svg_template_parser import SvgTemplateParser, TemplateInfo


# =============================================================================
# CONSTANTES
# =============================================================================

# Tamanhos de papel em mm (convertido para px em 300 DPI)
PAPER_SIZES = {
    "A4": (210, 297),      # 210mm x 297mm
    "A3": (297, 420),      # 297mm x 420mm
    "Letter": (215.9, 279.4),
    "Tabloid": (279.4, 431.8),
}

# DPI padrão para impressão
PRINT_DPI = 300

# Grid snap
GRID_SPACING = 10  # pixels
SNAP_THRESHOLD = 5  # pixels


def mm_to_px(mm: float, dpi: float = PRINT_DPI) -> float:
    """Converte milímetros para pixels."""
    return mm * dpi / 25.4


# =============================================================================
# RULER (Régua) - Passo 18
# =============================================================================

class RulerWidget(QWidget):
    """Régua horizontal ou vertical com marcações."""
    
    HORIZONTAL = 0
    VERTICAL = 1
    
    def __init__(self, orientation: int = HORIZONTAL, parent=None):
        super().__init__(parent)
        self.orientation = orientation
        self.offset = 0
        self.scale = 1.0
        self.mouse_pos = 0
        
        if orientation == self.HORIZONTAL:
            self.setFixedHeight(20)
        else:
            self.setFixedWidth(20)
        
        self.setStyleSheet("background-color: #1A1A2E;")
    
    def set_offset(self, offset: float):
        self.offset = offset
        self.update()
    
    def set_scale(self, scale: float):
        self.scale = scale
        self.update()
    
    def set_mouse_position(self, pos: float):
        self.mouse_pos = pos
        self.update()
    
    def paintEvent(self, event):
        from PySide6.QtGui import QPainter, QPen
        
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor("#1A1A2E"))
        
        pen = QPen(QColor("#404060"))
        painter.setPen(pen)
        
        # Marcações
        step = max(10, int(50 / self.scale))
        
        if self.orientation == self.HORIZONTAL:
            w = self.width()
            for i in range(0, w + step, step):
                x = i
                painter.drawLine(x, 15, x, 20)
                if i % (step * 5) == 0:
                    painter.drawLine(x, 10, x, 20)
                    painter.drawText(x + 2, 12, str(int((x + self.offset) / self.scale)))
            
            # Linha do mouse
            painter.setPen(QPen(QColor("#6C5CE7"), 1))
            painter.drawLine(int(self.mouse_pos), 0, int(self.mouse_pos), 20)
        
        else:
            h = self.height()
            for i in range(0, h + step, step):
                y = i
                painter.drawLine(15, y, 20, y)
                if i % (step * 5) == 0:
                    painter.drawLine(10, y, 20, y)
            
            # Linha do mouse
            painter.setPen(QPen(QColor("#6C5CE7"), 1))
            painter.drawLine(0, int(self.mouse_pos), 20, int(self.mouse_pos))


# =============================================================================
# ATELIER SCENE - Passo 17
# =============================================================================

class AtelierScene(QGraphicsScene):
    """
    Cena do Ateliê com suporte a:
    - Papel com dimensões reais
    - Grid magnético
    - Slots de template
    - Z-Ordering correto
    """
    
    slot_selected = Signal(int, dict)
    slot_modified = Signal(int, dict)
    scene_modified = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Dimensões do papel
        self._paper_width = mm_to_px(210)   # A4
        self._paper_height = mm_to_px(297)
        
        # Grid
        self._grid_spacing = GRID_SPACING
        self._grid_visible = True
        self._snap_enabled = True
        
        # Elementos
        self._paper_item: Optional[QGraphicsRectItem] = None
        self._slots: List[SmartSlotItem] = []
        self._static_items: List[QGraphicsItem] = []
        
        # Template atual
        self._template_info: Optional[TemplateInfo] = None
        self._template_path: Optional[str] = None
        
        # Cria cena inicial
        self._setup_scene()
    
    def _setup_scene(self):
        """Configura cena inicial."""
        # Define tamanho com margem
        margin = 50
        self.setSceneRect(
            -margin,
            -margin,
            self._paper_width + margin * 2,
            self._paper_height + margin * 2
        )
        
        # Papel
        self._paper_item = QGraphicsRectItem(0, 0, self._paper_width, self._paper_height)
        self._paper_item.setPen(QPen(QColor("#2D2D44"), 1))
        self._paper_item.setBrush(QBrush(QColor("#16213E")))
        self._paper_item.setZValue(-100)  # Atrás de tudo
        self.addItem(self._paper_item)
    
    def set_paper_size(self, width_mm: float, height_mm: float):
        """Define tamanho do papel em mm."""
        self._paper_width = mm_to_px(width_mm)
        self._paper_height = mm_to_px(height_mm)
        
        self.setSceneRect(
            -50, -50,
            self._paper_width + 100,
            self._paper_height + 100
        )
        
        if self._paper_item:
            self._paper_item.setRect(0, 0, self._paper_width, self._paper_height)
    
    def load_template(self, svg_path: str) -> bool:
        """
        Carrega template SVG e cria slots.
        
        Passo 19-21: Usa SvgTemplateParser para dissecar o SVG.
        """
        parser = SvgTemplateParser()
        template_info = parser.parse(svg_path)
        
        if not template_info:
            return False
        
        # Limpa cena anterior
        self.clear_slots()
        
        # Atualiza dimensões
        vb = template_info.viewbox
        self._paper_width = vb[2]
        self._paper_height = vb[3]
        
        self.setSceneRect(
            -50, -50,
            self._paper_width + 100,
            self._paper_height + 100
        )
        
        if self._paper_item:
            self._paper_item.setRect(0, 0, self._paper_width, self._paper_height)
        
        # Cria slots baseados no template
        for slot_def in template_info.slots:
            slot = SmartSlotItem(
                slot_index=slot_def.slot_index,
                element_id=slot_def.slot_id,
                x=slot_def.x,
                y=slot_def.y,
                width=slot_def.width,
                height=slot_def.height,
            )
            
            # Conecta sinais
            slot.product_assigned.connect(
                lambda data, idx=slot_def.slot_index: self.slot_modified.emit(idx, data)
            )
            slot.content_changed.connect(self.scene_modified.emit)
            
            self.addItem(slot)
            self._slots.append(slot)
        
        self._template_info = template_info
        self._template_path = svg_path
        
        return True
    
    def create_default_grid(self, cols: int = 3, rows: int = 4):
        """Cria grid padrão de slots."""
        self.clear_slots()
        
        margin = 25
        gap = 15
        available_w = self._paper_width - 2 * margin - (cols - 1) * gap
        available_h = self._paper_height - 2 * margin - (rows - 1) * gap
        
        slot_w = available_w / cols
        slot_h = available_h / rows
        
        index = 1
        for row in range(rows):
            for col in range(cols):
                x = margin + col * (slot_w + gap)
                y = margin + row * (slot_h + gap)
                
                slot = SmartSlotItem(
                    slot_index=index,
                    element_id=f"SLOT_{index:02d}",
                    x=x,
                    y=y,
                    width=slot_w,
                    height=slot_h,
                )
                
                slot.product_assigned.connect(
                    lambda data, idx=index: self.slot_modified.emit(idx, data)
                )
                slot.content_changed.connect(self.scene_modified.emit)
                
                self.addItem(slot)
                self._slots.append(slot)
                index += 1
    
    def clear_slots(self):
        """Remove todos os slots."""
        for slot in self._slots:
            self.removeItem(slot)
        self._slots.clear()
    
    def get_slots(self) -> List[SmartSlotItem]:
        return self._slots
    
    def get_slot(self, index: int) -> Optional[SmartSlotItem]:
        for slot in self._slots:
            if slot.slot_index == index:
                return slot
        return None
    
    def get_empty_slots(self) -> List[SmartSlotItem]:
        return [s for s in self._slots if not s.product_data]
    
    def get_filled_slots(self) -> List[SmartSlotItem]:
        return [s for s in self._slots if s.product_data]
    
    def clear_all_products(self):
        """Remove produtos de todos os slots."""
        for slot in self._slots:
            slot.clear_product()
    
    def snap_to_grid(self, point: QPointF) -> QPointF:
        """Aplica snap ao grid."""
        if not self._snap_enabled:
            return point
        
        x = round(point.x() / self._grid_spacing) * self._grid_spacing
        y = round(point.y() / self._grid_spacing) * self._grid_spacing
        
        return QPointF(x, y)
    
    def drawBackground(self, painter: QPainter, rect: QRectF):
        """Desenha grid de fundo."""
        super().drawBackground(painter, rect)
        
        if not self._grid_visible:
            return
        
        # Grid
        pen = QPen(QColor("#1A1A30"), 0.5)
        painter.setPen(pen)
        
        left = int(rect.left()) - (int(rect.left()) % self._grid_spacing)
        top = int(rect.top()) - (int(rect.top()) % self._grid_spacing)
        
        lines = []
        
        x = left
        while x < rect.right():
            lines.append(((x, rect.top()), (x, rect.bottom())))
            x += self._grid_spacing
        
        y = top
        while y < rect.bottom():
            lines.append(((rect.left(), y), (rect.right(), y)))
            y += self._grid_spacing
        
        for (x1, y1), (x2, y2) in lines:
            painter.drawLine(int(x1), int(y1), int(x2), int(y2))
    
    def serialize(self) -> Dict:
        """Serializa estado da cena."""
        return {
            "paper_width": self._paper_width,
            "paper_height": self._paper_height,
            "template_path": self._template_path,
            "slots": [slot.serialize() for slot in self._slots],
        }
    
    def deserialize(self, data: Dict):
        """Restaura estado da cena."""
        self._paper_width = data.get("paper_width", mm_to_px(210))
        self._paper_height = data.get("paper_height", mm_to_px(297))
        
        if self._paper_item:
            self._paper_item.setRect(0, 0, self._paper_width, self._paper_height)
        
        # Restaura slots
        for slot_data in data.get("slots", []):
            slot = self.get_slot(slot_data.get("slot_index", 0))
            if slot:
                slot.deserialize(slot_data)


# =============================================================================
# ATELIER VIEW - Passo 16
# =============================================================================

class AtelierView(QGraphicsView):
    """
    View principal do Ateliê com:
    - Zoom centrado no cursor (Passo 33)
    - Pan com botão do meio (Passo 34)
    - High DPI rendering (Passo 35)
    - Drop zone (Passo 37-40)
    """
    
    zoom_changed = Signal(float)
    mouse_moved = Signal(float, float)
    
    # Limites de zoom
    MIN_ZOOM = 0.1
    MAX_ZOOM = 5.0
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self._scene = AtelierScene()
        self.setScene(self._scene)
        
        # Configuração de renderização (Passo 35-36)
        self.setRenderHint(QPainter.Antialiasing)
        self.setRenderHint(QPainter.SmoothPixmapTransform)
        self.setRenderHint(QPainter.TextAntialiasing)
        self.setViewportUpdateMode(QGraphicsView.SmartViewportUpdate)
        self.setOptimizationFlag(QGraphicsView.DontAdjustForAntialiasing, True)
        
        # Transformação
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.AnchorUnderMouse)
        
        # Drag & Drop (Passo 37)
        self.setDragMode(QGraphicsView.NoDrag)
        self.setAcceptDrops(True)
        
        # Background
        self.setBackgroundBrush(QBrush(QColor("#0A0A0A")))
        
        # Estado
        self._is_panning = False
        self._pan_start = QPointF()
        self._current_zoom = 1.0
        
        # Mouse tracking
        self.setMouseTracking(True)
        
        # Fit inicial
        QTimer.singleShot(100, self._fit_initial)
    
    def _fit_initial(self):
        """Ajusta zoom para mostrar documento inteiro."""
        self.fitInView(self._scene.sceneRect(), Qt.KeepAspectRatio)
        self._current_zoom = self.transform().m11()
        self.zoom_changed.emit(self._current_zoom)
    
    def get_scene(self) -> AtelierScene:
        return self._scene
    
    def get_current_zoom(self) -> float:
        return self._current_zoom
    
    def set_zoom(self, zoom: float):
        """Define zoom absoluto."""
        zoom = max(self.MIN_ZOOM, min(self.MAX_ZOOM, zoom))
        
        # Reseta e aplica novo zoom
        self.resetTransform()
        self.scale(zoom, zoom)
        self._current_zoom = zoom
        self.zoom_changed.emit(zoom)
    
    def zoom_in(self):
        self.set_zoom(self._current_zoom * 1.2)
    
    def zoom_out(self):
        self.set_zoom(self._current_zoom / 1.2)
    
    def zoom_to_fit(self):
        self._fit_initial()
    
    def zoom_100(self):
        self.set_zoom(1.0)
    
    # === ZOOM COM RODA (Passo 33) ===
    
    def wheelEvent(self, event: QWheelEvent):
        """Zoom com âncora no cursor."""
        factor = 1.15
        
        if event.angleDelta().y() > 0:
            new_zoom = self._current_zoom * factor
        else:
            new_zoom = self._current_zoom / factor
        
        new_zoom = max(self.MIN_ZOOM, min(self.MAX_ZOOM, new_zoom))
        
        if new_zoom != self._current_zoom:
            # Salva posição do cursor na cena
            old_pos = self.mapToScene(event.position().toPoint())
            
            # Aplica zoom
            self.resetTransform()
            self.scale(new_zoom, new_zoom)
            self._current_zoom = new_zoom
            
            # Restaura posição
            new_pos = self.mapToScene(event.position().toPoint())
            delta = new_pos - old_pos
            self.translate(delta.x(), delta.y())
            
            self.zoom_changed.emit(self._current_zoom)
    
    # === PAN (Passo 34) ===
    
    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MiddleButton or (
            event.button() == Qt.LeftButton and
            event.modifiers() & Qt.ShiftModifier
        ):
            self._is_panning = True
            self._pan_start = event.position()
            self.setCursor(Qt.ClosedHandCursor)
        else:
            super().mousePressEvent(event)
    
    def mouseMoveEvent(self, event: QMouseEvent):
        # Emite posição para réguas
        scene_pos = self.mapToScene(event.position().toPoint())
        self.mouse_moved.emit(scene_pos.x(), scene_pos.y())
        
        if self._is_panning:
            delta = event.position() - self._pan_start
            self._pan_start = event.position()
            
            self.horizontalScrollBar().setValue(
                int(self.horizontalScrollBar().value() - delta.x())
            )
            self.verticalScrollBar().setValue(
                int(self.verticalScrollBar().value() - delta.y())
            )
        else:
            super().mouseMoveEvent(event)
    
    def mouseReleaseEvent(self, event: QMouseEvent):
        if event.button() in (Qt.MiddleButton, Qt.LeftButton):
            self._is_panning = False
            self.setCursor(Qt.ArrowCursor)
        super().mouseReleaseEvent(event)
    
    # === DRAG & DROP (Passos 37-40) ===
    
    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasFormat("application/x-autotabloide-product"):
            event.acceptProposedAction()
            # Highlight potencial (Passo 39)
            self._highlight_drop_target(event.position())
        else:
            event.ignore()
    
    def dragMoveEvent(self, event):
        if event.mimeData().hasFormat("application/x-autotabloide-product"):
            self._highlight_drop_target(event.position())
            event.acceptProposedAction()
    
    def dragLeaveEvent(self, event):
        self._clear_highlights()
    
    def dropEvent(self, event: QDropEvent):
        if event.mimeData().hasFormat("application/x-autotabloide-product"):
            scene_pos = self.mapToScene(event.position().toPoint())
            
            # Encontra slot sob o cursor
            items = self._scene.items(scene_pos)
            for item in items:
                if isinstance(item, SmartSlotItem):
                    data = event.mimeData().data("application/x-autotabloide-product")
                    product = json.loads(bytes(data).decode('utf-8'))
                    item.set_product(product)
                    event.acceptProposedAction()
                    self._clear_highlights()
                    return
            
            event.ignore()
        else:
            event.ignore()
        
        self._clear_highlights()
    
    def _highlight_drop_target(self, pos):
        """Destaca slot alvo."""
        scene_pos = self.mapToScene(pos.toPoint())
        items = self._scene.items(scene_pos)
        
        # Limpa highlights anteriores
        for slot in self._scene.get_slots():
            if not slot.isSelected():
                slot.set_state(SmartGraphicsItem.STATE_NORMAL)
        
        # Destaca slot atual
        for item in items:
            if isinstance(item, SmartSlotItem):
                item.set_state(SmartGraphicsItem.STATE_HOVER)
                break
    
    def _clear_highlights(self):
        """Remove todos os highlights."""
        for slot in self._scene.get_slots():
            if not slot.isSelected():
                slot.set_state(SmartGraphicsItem.STATE_NORMAL)


# =============================================================================
# ATELIER WIDGET COMPLETO
# =============================================================================

class AtelierWidget(QWidget):
    """
    Widget completo do Ateliê com:
    - Toolbar
    - Réguas
    - Canvas (AtelierView)
    - Prateleira de produtos
    """
    
    project_modified = Signal()
    
    def __init__(self, container=None, parent=None):
        super().__init__(parent)
        self.container = container
        self.undo_stack = QUndoStack(self)
        
        self._all_products: List[Dict] = []
        
        self._setup_ui()
        self._setup_shortcuts()
        
        # Carrega produtos
        QTimer.singleShot(500, self._load_products)
    
    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Toolbar
        toolbar = self._create_toolbar()
        main_layout.addWidget(toolbar)
        
        # Splitter principal
        splitter = QSplitter(Qt.Horizontal)
        
        # Prateleira
        shelf_widget = self._create_shelf()
        splitter.addWidget(shelf_widget)
        
        # Canvas com réguas
        canvas_widget = self._create_canvas_with_rulers()
        splitter.addWidget(canvas_widget)
        
        splitter.setSizes([250, 800])
        main_layout.addWidget(splitter)
    
    def _create_toolbar(self) -> QFrame:
        toolbar = QFrame()
        toolbar.setStyleSheet("background-color: #1A1A2E; border-bottom: 1px solid #2D2D44;")
        
        layout = QHBoxLayout(toolbar)
        layout.setContentsMargins(12, 8, 12, 8)
        
        # Título
        title = QLabel("Ateliê - A Mesa")
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: #FFFFFF;")
        layout.addWidget(title)
        
        layout.addStretch()
        
        # Seletor de template
        self.template_combo = QComboBox()
        self.template_combo.addItem("Grid 3x4 (12 slots)", ("grid", 3, 4))
        self.template_combo.addItem("Grid 2x3 (6 slots)", ("grid", 2, 3))
        self.template_combo.addItem("Grid 2x2 (4 slots)", ("grid", 2, 2))
        self.template_combo.addItem("Carregar SVG...", "custom")
        self.template_combo.currentIndexChanged.connect(self._on_template_changed)
        layout.addWidget(self.template_combo)
        
        # Zoom
        layout.addWidget(QLabel("Zoom:"))
        self.zoom_spin = QSpinBox()
        self.zoom_spin.setRange(10, 500)
        self.zoom_spin.setValue(100)
        self.zoom_spin.setSuffix("%")
        self.zoom_spin.valueChanged.connect(self._on_zoom_changed)
        layout.addWidget(self.zoom_spin)
        
        # Botões
        btn_auto = QPushButton("Auto-Preencher")
        btn_auto.clicked.connect(self._auto_fill)
        layout.addWidget(btn_auto)
        
        btn_clear = QPushButton("Limpar")
        btn_clear.setProperty("class", "danger")
        btn_clear.clicked.connect(self._clear_all)
        layout.addWidget(btn_clear)
        
        btn_save = QPushButton("Salvar")
        btn_save.clicked.connect(self._save_project)
        layout.addWidget(btn_save)
        
        btn_export = QPushButton("Exportar PDF")
        btn_export.clicked.connect(self._export_pdf)
        layout.addWidget(btn_export)
        
        return toolbar
    
    def _create_shelf(self) -> QFrame:
        frame = QFrame()
        frame.setMaximumWidth(280)
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(8, 8, 8, 8)
        
        layout.addWidget(QLabel("Prateleira de Produtos"))
        
        from PySide6.QtWidgets import QLineEdit
        self.shelf_search = QLineEdit()
        self.shelf_search.setPlaceholderText("Buscar...")
        self.shelf_search.textChanged.connect(self._filter_shelf)
        layout.addWidget(self.shelf_search)
        
        self.shelf_list = QListWidget()
        self.shelf_list.setDragEnabled(True)
        layout.addWidget(self.shelf_list)
        
        self.shelf_count = QLabel("0 produtos")
        self.shelf_count.setStyleSheet("color: #808080;")
        layout.addWidget(self.shelf_count)
        
        return frame
    
    def _create_canvas_with_rulers(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Régua horizontal
        h_layout = QHBoxLayout()
        h_layout.setContentsMargins(0, 0, 0, 0)
        h_layout.setSpacing(0)
        
        corner = QFrame()
        corner.setFixedSize(20, 20)
        corner.setStyleSheet("background-color: #1A1A2E;")
        h_layout.addWidget(corner)
        
        self.h_ruler = RulerWidget(RulerWidget.HORIZONTAL)
        h_layout.addWidget(self.h_ruler)
        
        layout.addLayout(h_layout)
        
        # Canvas + régua vertical
        canvas_layout = QHBoxLayout()
        canvas_layout.setContentsMargins(0, 0, 0, 0)
        canvas_layout.setSpacing(0)
        
        self.v_ruler = RulerWidget(RulerWidget.VERTICAL)
        canvas_layout.addWidget(self.v_ruler)
        
        self.canvas = AtelierView()
        self.canvas.mouse_moved.connect(self._on_mouse_moved)
        self.canvas.zoom_changed.connect(self._on_view_zoom_changed)
        canvas_layout.addWidget(self.canvas)
        
        layout.addLayout(canvas_layout)
        
        return widget
    
    def _setup_shortcuts(self):
        QShortcut(QKeySequence.Undo, self, self.undo_stack.undo)
        QShortcut(QKeySequence.Redo, self, self.undo_stack.redo)
        QShortcut(QKeySequence.Save, self, self._save_project)
        QShortcut(QKeySequence("Ctrl+E"), self, self._export_pdf)
        QShortcut(QKeySequence("Ctrl+="), self, self.canvas.zoom_in)
        QShortcut(QKeySequence("Ctrl+-"), self, self.canvas.zoom_out)
        QShortcut(QKeySequence("Ctrl+0"), self, self.canvas.zoom_100)
        QShortcut(QKeySequence("Ctrl+1"), self, self.canvas.zoom_to_fit)
    
    def _load_products(self):
        """Carrega produtos reais do banco para a prateleira."""
        import asyncio
        import threading
        from PySide6.QtCore import QTimer
        
        async def _fetch_products():
            from src.core.database import AsyncSessionLocal
            from src.core.repositories import ProductRepository
            
            async with AsyncSessionLocal() as session:
                repo = ProductRepository(session)
                products = await repo.search(limit=200)
                
                result = []
                for p in products:
                    result.append({
                        "id": p.id,
                        "nome_sanitizado": p.nome_sanitizado,
                        "preco_venda_atual": float(p.preco_venda_atual or 0),
                        "preco_referencia": float(p.preco_referencia or 0) if p.preco_referencia else None,
                        "marca_normalizada": p.marca_normalizada,
                        "detalhe_peso": p.detalhe_peso,
                        "img_hash_ref": p.img_hash_ref,
                    })
                return result
        
        def _on_loaded(products):
            self._all_products = products
            self._update_shelf()
        
        def _run():
            loop = asyncio.new_event_loop()
            try:
                products = loop.run_until_complete(_fetch_products())
                QTimer.singleShot(0, lambda: _on_loaded(products))
            except Exception as e:
                print(f"[Atelier] Erro ao carregar produtos: {e}")
                QTimer.singleShot(0, lambda: _on_loaded([]))
            finally:
                loop.close()
        
        thread = threading.Thread(target=_run, daemon=True)
        thread.start()
    
    def _update_shelf(self, products: List[Dict] = None):
        products = products or self._all_products
        self.shelf_list.clear()
        
        for p in products:
            text = f"{p.get('nome_sanitizado', '?')}\nR$ {float(p.get('preco_venda_atual', 0)):.2f}"
            item = QListWidgetItem(text)
            item.setData(Qt.UserRole, p)
            self.shelf_list.addItem(item)
        
        self.shelf_count.setText(f"{len(products)} produtos")
    
    def _filter_shelf(self, text: str):
        text = text.lower()
        filtered = [p for p in self._all_products if text in p.get("nome_sanitizado", "").lower()]
        self._update_shelf(filtered)
    
    @Slot(int)
    def _on_template_changed(self, index: int):
        data = self.template_combo.currentData()
        
        if data == "custom":
            path, _ = QFileDialog.getOpenFileName(self, "Carregar SVG", "", "SVG (*.svg)")
            if path:
                if not self.canvas.get_scene().load_template(path):
                    QMessageBox.warning(self, "Erro", "Falha ao carregar template")
        
        elif isinstance(data, tuple) and data[0] == "grid":
            _, cols, rows = data
            self.canvas.get_scene().create_default_grid(cols, rows)
    
    @Slot(int)
    def _on_zoom_changed(self, value: int):
        self.canvas.set_zoom(value / 100.0)
    
    @Slot(float)
    def _on_view_zoom_changed(self, zoom: float):
        self.zoom_spin.blockSignals(True)
        self.zoom_spin.setValue(int(zoom * 100))
        self.zoom_spin.blockSignals(False)
        
        self.h_ruler.set_scale(zoom)
        self.v_ruler.set_scale(zoom)
    
    @Slot(float, float)
    def _on_mouse_moved(self, x: float, y: float):
        self.h_ruler.set_mouse_position(x)
        self.v_ruler.set_mouse_position(y)
    
    @Slot()
    def _auto_fill(self):
        empty = self.canvas.get_scene().get_empty_slots()
        products = [self.shelf_list.item(i).data(Qt.UserRole) 
                    for i in range(self.shelf_list.count())]
        
        filled = 0
        for i, slot in enumerate(empty):
            if i >= len(products):
                break
            slot.set_product(products[i])
            filled += 1
        
        QMessageBox.information(self, "Auto-Preencher", f"{filled} slots preenchidos")
    
    @Slot()
    def _clear_all(self):
        reply = QMessageBox.question(self, "Limpar", "Remover todos os produtos?")
        if reply == QMessageBox.Yes:
            self.canvas.get_scene().clear_all_products()
    
    @Slot()
    def _save_project(self):
        from src.qt.core.project_manager import get_project_manager
        
        scene_data = self.canvas.get_scene().serialize()
        pm = get_project_manager()
        
        # Se já tem path, salva; senão abre dialog
        if pm.current_project and pm.current_project.path:
            pm.update_from_scene(scene_data)
            try:
                pm.save_project()
                self.statusBar().showMessage("Projeto salvo!", 3000) if hasattr(self, 'statusBar') else None
            except Exception as e:
                QMessageBox.critical(self, "Erro", f"Erro ao salvar:\n{str(e)}")
        else:
            path, _ = QFileDialog.getSaveFileName(
                self, "Salvar Projeto",
                "projeto.tabloide",
                "Projeto AutoTabloide (*.tabloide);;JSON (*.json)"
            )
            if path:
                pm.new_project(Path(path).stem)
                pm.update_from_scene(scene_data)
                try:
                    pm.save_project(path)
                    QMessageBox.information(self, "Salvo", f"Projeto salvo em:\n{path}")
                except Exception as e:
                    QMessageBox.critical(self, "Erro", f"Erro ao salvar:\n{str(e)}")
    
    @Slot()
    def _export_pdf(self):
        filled = self.canvas.get_scene().get_filled_slots()
        if not filled:
            QMessageBox.warning(self, "Aviso", "Nenhum slot preenchido!")
            return
        
        path, _ = QFileDialog.getSaveFileName(self, "Exportar PDF", "tabloide.pdf", "PDF (*.pdf)")
        if path:
            scene_data = self.canvas.get_scene().serialize()
            template_path = getattr(self.canvas.get_scene(), '_template_path', None)
            
            if not template_path:
                # Usa template default se não tem SVG carregado
                QMessageBox.warning(self, "Aviso", "Exporte requer um template SVG carregado.")
                return
            
            try:
                from src.rendering.pdf_export import export_atelier_to_pdf
                
                success, message = export_atelier_to_pdf(
                    scene_data=scene_data,
                    template_path=template_path,
                    output_path=path,
                    system_root="AutoTabloide_System_Root"
                )
                
                if success:
                    QMessageBox.information(self, "Exportação Concluída", message)
                else:
                    QMessageBox.warning(self, "Erro na Exportação", message)
                    
            except Exception as e:
                QMessageBox.critical(self, "Erro", f"Erro ao exportar:\n{str(e)}")


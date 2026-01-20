"""
AutoTabloide AI - Smart Graphics Items
======================================
PROTOCOLO DE CONVERGÊNCIA INDUSTRIAL - Fase 2
Passos 22-27: SmartGraphicsItems com interatividade completa.

Cada item é um objeto QGraphicsItem que representa um elemento
editável do SVG. Suporta seleção, redimensionamento, e edição.
"""

from __future__ import annotations
from pathlib import Path
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
import json

from PySide6.QtCore import Qt, QRectF, QPointF, QSizeF, Signal, QObject
from PySide6.QtWidgets import (
    QGraphicsItem, QGraphicsRectItem, QGraphicsTextItem,
    QGraphicsPixmapItem, QGraphicsObject, QWidget,
    QStyleOptionGraphicsItem, QGraphicsSceneMouseEvent,
    QGraphicsSceneHoverEvent, QMenu
)
from PySide6.QtGui import (
    QPainter, QColor, QPen, QBrush, QFont, QPixmap, QImage,
    QTransform, QCursor, QPainterPath
)


# =============================================================================
# HANDLE DE REDIMENSIONAMENTO (Passo 31)
# =============================================================================

class ResizeHandle(QGraphicsRectItem):
    """Handle de canto para redimensionamento."""
    
    # Posições do handle
    TOP_LEFT = 0
    TOP_RIGHT = 1
    BOTTOM_LEFT = 2
    BOTTOM_RIGHT = 3
    
    CURSORS = {
        TOP_LEFT: Qt.SizeFDiagCursor,
        TOP_RIGHT: Qt.SizeBDiagCursor,
        BOTTOM_LEFT: Qt.SizeBDiagCursor,
        BOTTOM_RIGHT: Qt.SizeFDiagCursor,
    }
    
    def __init__(self, position: int, size: float = 8, parent=None):
        super().__init__(parent)
        self.position = position
        self._size = size
        
        self.setRect(-size/2, -size/2, size, size)
        self.setBrush(QBrush(QColor("#FFFFFF")))
        self.setPen(QPen(QColor("#6C5CE7"), 1))
        
        self.setFlag(QGraphicsItem.ItemIsMovable, False)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges, True)
        self.setAcceptHoverEvents(True)
        self.setCursor(self.CURSORS.get(position, Qt.SizeAllCursor))
        
        self.hide()
    
    def mousePressEvent(self, event):
        """Inicia redimensionamento."""
        self._start_pos = event.scenePos()
        self.parentItem().start_resize()
        event.accept()
    
    def mouseMoveEvent(self, event):
        """Calcula novo retângulo."""
        if not self.parentItem() or self.parentItem().is_locked:
            return

        diff = event.scenePos() - self._start_pos
        self.parentItem().resize_step(self.position, diff)
    
    def mouseReleaseEvent(self, event):
        self.parentItem().end_resize()
        super().mouseReleaseEvent(event)



# =============================================================================
# BASE: SMART GRAPHICS ITEM (Passo 22)
# =============================================================================

class SmartGraphicsItem(QGraphicsObject):
    """
    Base class para todos os itens editáveis.
    
    Features:
    - Seleção visual com handles
    - Redimensionamento proporcional/livre
    - Hover states
    - Context menu
    - Serialização
    """
    
    # Sinais
    content_changed = Signal()
    position_changed = Signal(float, float)
    size_changed = Signal(float, float)
    
    # Estados visuais
    STATE_NORMAL = 0
    STATE_HOVER = 1
    STATE_SELECTED = 2
    STATE_DRAGGING = 3
    
    COLORS = {
        STATE_NORMAL: ("#3D3D5C", "#1A1A2E88"),
        STATE_HOVER: ("#00CEC9", "#00CEC933"),
        STATE_SELECTED: ("#6C5CE7", "#6C5CE744"),
        STATE_DRAGGING: ("#FDCB6E", "#FDCB6E55"),
    }
    
    def __init__(
        self,
        element_id: str,
        x: float = 0,
        y: float = 0,
        width: float = 100,
        height: float = 100,
        parent=None
    ):
        super().__init__(parent)
        
        self.element_id = element_id
        self._rect = QRectF(0, 0, width, height)
        self._state = self.STATE_NORMAL
        self._is_resizing = False
        self._resize_handle: Optional[ResizeHandle] = None
        self._resize_start_rect: Optional[QRectF] = None
        self._aspect_locked = True
        
        # Dados do produto
        self.product_data: Optional[Dict] = None
        self._drag_start_pos: Optional[QPointF] = None
        
        self._locked = False
        
        # Configuração
        self.setPos(x, y)
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges, True)
        self.setAcceptHoverEvents(True)
        
        # Handles de resize
        self._handles: List[ResizeHandle] = []
        self._create_handles()
        
    def mousePressEvent(self, event):
        """Captura posição inicial para undo."""
        self._drag_start_pos = self.pos()
        super().mousePressEvent(event)
        
    def mouseReleaseEvent(self, event):
        """Detecta fim do move e cria undo command."""
        super().mouseReleaseEvent(event)
        
        if self._drag_start_pos is not None:
             final_pos = self.pos()
             if final_pos != self._drag_start_pos:
                 from ..core.undo_commands import MoveItemCommand, get_undo_manager
                 # Usa lazy import para evitar ciclo
                 cmd = MoveItemCommand(self, self._drag_start_pos, final_pos)
                 get_undo_manager().push(cmd)
             self._drag_start_pos = None

        
    @property
    def is_locked(self) -> bool:
        return self._locked
        
    def set_locked(self, locked: bool):
        """Define estado de bloqueio."""
        self._locked = locked
        self.setFlag(QGraphicsItem.ItemIsMovable, not locked)
        self.setFlag(QGraphicsItem.ItemIsSelectable, not locked)
        
        if locked:
            self.set_state(self.STATE_NORMAL)
            self._show_handles(False)
            
    def check_overflow(self) -> bool:
        """Verifica se conteúdo excede limites (Preflight)."""
        return False
        
    def get_image_dpi(self) -> Optional[float]:
        """Calcula DPI efetivo da imagem (Preflight)."""
        return None
            
    def start_resize(self):
        """Inicia ciclo de resize."""
        self._is_resizing = True
        self._resize_start_rect = QRectF(self._rect)
        
    def resize_step(self, handle_pos: int, diff: QPointF):
        """Aplica passo de resize."""
        if not self._is_resizing or not self._resize_start_rect:
            return
            
        self.prepareGeometryChange()
        
        r = self._resize_start_rect
        dx = diff.x()
        dy = diff.y()
        
        new_x, new_y = r.x(), r.y()
        new_w, new_h = r.width(), r.height()
        
        # Mapa de lógica por handle
        if handle_pos == ResizeHandle.TOP_LEFT:
            new_x += dx
            new_y += dy
            new_w -= dx
            new_h -= dy
        elif handle_pos == ResizeHandle.TOP_RIGHT:
            new_y += dy
            new_w += dx
            new_h -= dy
        elif handle_pos == ResizeHandle.BOTTOM_LEFT:
            new_x += dx
            new_w -= dx
            new_h += dy
        elif handle_pos == ResizeHandle.BOTTOM_RIGHT:
            new_w += dx
            new_h += dy
            
        # Limita tamanho mínimo
        if new_w < 10: new_w = 10
        if new_h < 10: new_h = 10
        
        self._rect = QRectF(new_x, new_y, new_w, new_h)
        self._update_handles()
        self.size_changed.emit(new_w, new_h)
        self.update()
        
    def end_resize(self):
        """Finaliza resize."""
        if not self._is_resizing or not self._resize_start_rect:
            return

        from ..core.undo_commands import ResizeItemCommand, get_undo_manager
        
        # Cria comando de undo
        final_rect = self._rect
        start_rect = self._resize_start_rect
        
        if final_rect != start_rect:
            cmd = ResizeItemCommand(self, start_rect, final_rect)
            get_undo_manager().push(cmd)
            
        self._is_resizing = False
        self._resize_start_rect = None
        self.content_changed.emit()
        
    def bring_to_front(self):
        """Traz item para frente."""
        if not self.scene(): return
        
        items = self.scene().items()
        max_z = max((i.zValue() for i in items), default=0)
        self.setZValue(max_z + 1)
        
    def send_to_back(self):
        """Envia item para trás."""
        if not self.scene(): return
        
        items = self.scene().items()
        min_z = min((i.zValue() for i in items), default=0)
        self.setZValue(min_z - 1)
    
    def _create_handles(self):
        """Cria handles de redimensionamento nos cantos."""
        for pos in [
            ResizeHandle.TOP_LEFT,
            ResizeHandle.TOP_RIGHT,
            ResizeHandle.BOTTOM_LEFT,
            ResizeHandle.BOTTOM_RIGHT,
        ]:
            handle = ResizeHandle(pos, parent=self)
            self._handles.append(handle)
        
        self._update_handles()
    
    def _update_handles(self):
        """Atualiza posição dos handles."""
        if not self._handles:
            return
        
        r = self._rect
        positions = {
            ResizeHandle.TOP_LEFT: QPointF(r.left(), r.top()),
            ResizeHandle.TOP_RIGHT: QPointF(r.right(), r.top()),
            ResizeHandle.BOTTOM_LEFT: QPointF(r.left(), r.bottom()),
            ResizeHandle.BOTTOM_RIGHT: QPointF(r.right(), r.bottom()),
        }
        
        for handle in self._handles:
            pos = positions.get(handle.position)
            if pos:
                handle.setPos(pos)
    
    def _show_handles(self, show: bool):
        """Mostra/esconde handles."""
        for handle in self._handles:
            handle.setVisible(show)
    
    def boundingRect(self) -> QRectF:
        margin = 5
        return self._rect.adjusted(-margin, -margin, margin, margin)
    
    def paint(
        self,
        painter: QPainter,
        option: QStyleOptionGraphicsItem,
        widget: Optional[QWidget] = None
    ):
        """Desenha o item base com borda de estado."""
        border_color, fill_color = self.COLORS.get(
            self._state, self.COLORS[self.STATE_NORMAL]
        )
        
        # Borda
        pen = QPen(QColor(border_color), 2)
        if self._state == self.STATE_NORMAL:
            pen.setStyle(Qt.DashLine)
        painter.setPen(pen)
        
        # Preenchimento
        painter.setBrush(QBrush(QColor(fill_color)))
        painter.drawRect(self._rect)
    
    def set_state(self, state: int):
        """Define estado visual."""
        if self._state != state:
            self._state = state
            self._show_handles(state == self.STATE_SELECTED)
            self.update()
    
    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemSelectedChange:
            if value:
                self.set_state(self.STATE_SELECTED)
            else:
                self.set_state(self.STATE_NORMAL)
        
        elif change == QGraphicsItem.ItemPositionChange:
            # Smart Snapping (Passo 71)
            if self.scene() and hasattr(self.scene(), "update_smart_guides"):
                 # Apenas snap se estiver sendo movido pelo usuário (selecionado e não redimensionando)
                 if self.isSelected() and not self._is_resizing:
                        snap_x, snap_y = self.scene().update_smart_guides(self, value)
                        if snap_x is not None: value.setX(snap_x)
                        if snap_y is not None: value.setY(snap_y)
            
            self.position_changed.emit(value.x(), value.y())
        
        return super().itemChange(change, value)
    
    def hoverEnterEvent(self, event: QGraphicsSceneHoverEvent):
        if self._state != self.STATE_SELECTED:
            self.set_state(self.STATE_HOVER)
        super().hoverEnterEvent(event)
    
    def hoverLeaveEvent(self, event: QGraphicsSceneHoverEvent):
        if self._state == self.STATE_HOVER:
            self.set_state(self.STATE_NORMAL)
        super().hoverLeaveEvent(event)
    
    def contextMenuEvent(self, event):
        """Menu de contexto."""
        menu = QMenu()
        
        action_edit = menu.addAction("Editar")
        action_clear = menu.addAction("Limpar")
        menu.addSeparator()
        action_lock = menu.addAction("Travar Proporção")
        action_lock.setCheckable(True)
        action_lock.setChecked(self._aspect_locked)
        
        action = menu.exec(event.screenPos())
        
        if action == action_edit:
            self._on_edit_requested()
        elif action == action_clear:
            self._on_clear_requested()
        elif action == action_lock:
            self._aspect_locked = not self._aspect_locked
    
    def _on_edit_requested(self):
        """Override nos filhos."""
        pass
    
    def _on_clear_requested(self):
        """Limpa conteúdo."""
        self.product_data = None
        self.content_changed.emit()
        self.update()
    
    def serialize(self) -> Dict:
        """Serializa para JSON."""
        return {
            "element_id": self.element_id,
            "x": self.pos().x(),
            "y": self.pos().y(),
            "width": self._rect.width(),
            "height": self._rect.height(),
            "product_data": self.product_data,
        }
    
    def deserialize(self, data: Dict):
        """Restaura de JSON."""
        self.setPos(data.get("x", 0), data.get("y", 0))
        self._rect = QRectF(
            0, 0,
            data.get("width", 100),
            data.get("height", 100)
        )
        self.product_data = data.get("product_data")
        self._update_handles()
        self.update()


# =============================================================================
# SMART IMAGE ITEM (Passo 23)
# =============================================================================

class SmartImageItem(SmartGraphicsItem):
    """
    Item de imagem com suporte a:
    - Aspect-Fit (nunca distorce)
    - Crop manual
    - Placeholder quando vazio
    """
    
    def __init__(
        self,
        element_id: str,
        x: float = 0,
        y: float = 0,
        width: float = 100,
        height: float = 100,
        parent=None
    ):
        super().__init__(element_id, x, y, width, height, parent)
        
        self._image: Optional[QImage] = None
        self._image_path: Optional[str] = None
        self._fit_mode = "contain"  # contain, cover, stretch
    
    def set_image(self, image_path: str) -> bool:
        """Define imagem do slot."""
        path = Path(image_path)
        if not path.exists():
            print(f"[SmartImage] Imagem não encontrada: {image_path}")
            return False
        
        image = QImage(str(path))
        if image.isNull():
            print(f"[SmartImage] Falha ao carregar: {image_path}")
            return False
        
        self._image = image
        self._image_path = image_path
        self.update()
        return True
    
    def set_pixmap(self, pixmap: QPixmap):
        """Define via pixmap (converte para QImage)."""
        self._image = pixmap.toImage()
        self._image_path = None
        self.update()
        
    def get_image_dpi(self) -> Optional[float]:
        """Calcula DPI baseado no tamanho atual."""
        if not self._image or self._image.isNull():
            return None
            
        w_dpi = (self._image.width() * 96) / max(1, self._rect.width())
        h_dpi = (self._image.height() * 96) / max(1, self._rect.height())
        return min(w_dpi, h_dpi)
    
    def clear_image(self):
        """Remove imagem."""
        self._image = None
        self._image_path = None
        self.update()
    
    def paint(
        self,
        painter: QPainter,
        option: QStyleOptionGraphicsItem,
        widget: Optional[QWidget] = None
    ):
        # Background
        painter.fillRect(self._rect, QBrush(QColor("#16213E")))
        
        if self._image and not self._image.isNull():
            # Aspect-Fit
            scaled = self._image.scaled(
                int(self._rect.width()),
                int(self._rect.height()),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
            
            # Centraliza
            x = self._rect.x() + (self._rect.width() - scaled.width()) / 2
            y = self._rect.y() + (self._rect.height() - scaled.height()) / 2
            
            painter.drawImage(int(x), int(y), scaled)
        
        else:
            # Placeholder
            painter.setPen(QPen(QColor("#404060"), 1, Qt.DashLine))
            painter.drawRect(self._rect)
            
            painter.setPen(QColor("#606080"))
            painter.drawText(
                self._rect,
                Qt.AlignCenter,
                "Arraste uma\nimagem aqui"
            )
        
        # Borda de estado
        super().paint(painter, option, widget)
    
    def serialize(self) -> Dict:
        data = super().serialize()
        data["image_path"] = self._image_path
        data["fit_mode"] = self._fit_mode
        return data
    
    def deserialize(self, data: Dict):
        super().deserialize(data)
        self._fit_mode = data.get("fit_mode", "contain")
        if data.get("image_path"):
            self.set_image(data["image_path"])


# =============================================================================
# SMART TEXT ITEM (Passo 24)
# =============================================================================

class SmartTextItem(SmartGraphicsItem):
    """
    Item de texto com:
    - Auto-fit (reduz fonte se necessário)
    - Múltiplas linhas
    - Alinhamento configurável
    """
    
    def __init__(
        self,
        element_id: str,
        x: float = 0,
        y: float = 0,
        width: float = 200,
        height: float = 30,
        parent=None
    ):
        super().__init__(element_id, x, y, width, height, parent)
        
        self._text = ""
        self._font_family = "Roboto"
        self._font_size = 14
        self._font_weight = QFont.Normal
        self._text_color = QColor("#FFFFFF")
        self._alignment = Qt.AlignLeft | Qt.AlignVCenter
        self._auto_fit = True
    
    def set_text(self, text: str):
        """Define texto."""
        self._text = text
        self.content_changed.emit()
        self.update()
    
    def get_text(self) -> str:
        return self._text
    
    def set_font(
        self,
        family: str = None,
        size: int = None,
        weight: int = None
    ):
        """Configura fonte."""
        if family:
            self._font_family = family
        if size:
            self._font_size = size
        if weight is not None:
            self._font_weight = weight
        self.update()
    
    def set_color(self, color: QColor):
        """Define cor do texto."""
        self._text_color = color
        self.update()
    
    def set_alignment(self, alignment: int):
        """Define alinhamento."""
        self._alignment = alignment
        self.update()
    
    def paint(
        self,
        painter: QPainter,
        option: QStyleOptionGraphicsItem,
        widget: Optional[QWidget] = None
    ):
        if self._text:
            # Calcula tamanho ideal
            font = QFont(self._font_family, self._font_size, self._font_weight)
            
            if self._auto_fit:
                font = self._calculate_fit_font(painter, font)
            
            painter.setFont(font)
            painter.setPen(self._text_color)
            painter.drawText(self._rect, self._alignment, self._text)
        
        else:
            # Placeholder
            painter.setPen(QPen(QColor("#404060"), 1, Qt.DashLine))
            painter.drawRect(self._rect)
            
            painter.setPen(QColor("#606080"))
            font = QFont("Segoe UI", 9)
            painter.setFont(font)
            painter.drawText(self._rect, Qt.AlignCenter, "Texto")
        
        # Borda de estado
        super().paint(painter, option, widget)
    
    def _calculate_fit_font(self, painter: QPainter, font: QFont) -> QFont:
        """Reduz fonte até caber no retângulo."""
        size = self._font_size
        
        while size > 6:
            font.setPointSize(size)
            painter.setFont(font)
            metrics = painter.fontMetrics()
            text_rect = metrics.boundingRect(
                self._rect.toRect(),
                self._alignment,
                self._text
            )
            
            if (text_rect.width() <= self._rect.width() and
                text_rect.height() <= self._rect.height()):
                break
            
            size -= 1
        
        font.setPointSize(size)
        return font
    
    def serialize(self) -> Dict:
        data = super().serialize()
        data.update({
            "text": self._text,
            "font_family": self._font_family,
            "font_size": self._font_size,
            "font_weight": self._font_weight,
            "text_color": self._text_color.name(),
            "alignment": self._alignment,
            "auto_fit": self._auto_fit,
        })
        return data
    
    def deserialize(self, data: Dict):
        super().deserialize(data)
        self._text = data.get("text", "")
        self._font_family = data.get("font_family", "Roboto")
        self._font_size = data.get("font_size", 14)
        self._font_weight = data.get("font_weight", QFont.Normal)
        if data.get("text_color"):
            self._text_color = QColor(data["text_color"])
        self._alignment = data.get("alignment", Qt.AlignLeft | Qt.AlignVCenter)
        self._auto_fit = data.get("auto_fit", True)


# =============================================================================
# SMART PRICE ITEM (Passo 25)
# =============================================================================

class SmartPriceItem(SmartGraphicsItem):
    """
    Item de preço especializado com:
    - Separação de inteiro/decimal
    - Centavos em superscript
    - Formatação automática BRL
    """
    
    def __init__(
        self,
        element_id: str,
        x: float = 0,
        y: float = 0,
        width: float = 150,
        height: float = 50,
        parent=None
    ):
        super().__init__(element_id, x, y, width, height, parent)
        
        self._price: float = 0.0
        self._show_currency = True
        self._split_decimal = True
        self._currency_symbol = "R$"
        
        # Fontes
        self._currency_font = QFont("Roboto", 14)
        self._integer_font = QFont("Roboto", 36, QFont.Bold)
        self._decimal_font = QFont("Roboto", 18, QFont.Bold)
        
        # Cores
        self._color = QColor("#2ECC71")
    
    def set_price(self, price: float):
        """Define preço."""
        self._price = price
        self.content_changed.emit()
        self.update()
    
    def get_price(self) -> float:
        return self._price
    
    def set_color(self, color: QColor):
        self._color = color
        self.update()
    
    def paint(
        self,
        painter: QPainter,
        option: QStyleOptionGraphicsItem,
        widget: Optional[QWidget] = None
    ):
        if self._price > 0:
            painter.setPen(self._color)
            
            # Formata preço
            price_str = f"{self._price:.2f}".replace(".", ",")
            integer_part, decimal_part = price_str.split(",")
            
            if self._split_decimal:
                self._draw_split_price(painter, integer_part, decimal_part)
            else:
                self._draw_simple_price(painter, price_str)
        
        else:
            # Placeholder
            painter.setPen(QPen(QColor("#404060"), 1, Qt.DashLine))
            painter.drawRect(self._rect)
            
            painter.setPen(QColor("#606080"))
            painter.setFont(QFont("Segoe UI", 9))
            painter.drawText(self._rect, Qt.AlignCenter, "R$ 0,00")
        
        # Borda de estado
        super().paint(painter, option, widget)
    
    def _draw_split_price(
        self,
        painter: QPainter,
        integer: str,
        decimal: str
    ):
        """Desenha preço com centavos em superscript."""
        x = self._rect.x() + 5
        y = self._rect.center().y()
        
        # Símbolo "R$"
        if self._show_currency:
            painter.setFont(self._currency_font)
            metrics = painter.fontMetrics()
            painter.drawText(int(x), int(y + metrics.height() / 3), self._currency_symbol)
            x += metrics.horizontalAdvance(self._currency_symbol) + 3
        
        # Parte inteira
        painter.setFont(self._integer_font)
        metrics = painter.fontMetrics()
        painter.drawText(int(x), int(y + metrics.height() / 3), integer)
        x += metrics.horizontalAdvance(integer)
        
        # Vírgula
        painter.drawText(int(x), int(y + metrics.height() / 3), ",")
        x += metrics.horizontalAdvance(",")
        
        # Parte decimal (superscript)
        painter.setFont(self._decimal_font)
        painter.drawText(int(x), int(y - 5), decimal)
    
    def _draw_simple_price(self, painter: QPainter, price_str: str):
        """Desenha preço completo simples."""
        painter.setFont(self._integer_font)
        
        text = f"{self._currency_symbol} {price_str}" if self._show_currency else price_str
        painter.drawText(
            self._rect,
            Qt.AlignLeft | Qt.AlignVCenter,
            text
        )
    
    def serialize(self) -> Dict:
        data = super().serialize()
        data.update({
            "price": self._price,
            "show_currency": self._show_currency,
            "split_decimal": self._split_decimal,
            "color": self._color.name(),
        })
        return data
    
    def deserialize(self, data: Dict):
        super().deserialize(data)
        self._price = data.get("price", 0.0)
        self._show_currency = data.get("show_currency", True)
        self._split_decimal = data.get("split_decimal", True)
        if data.get("color"):
            self._color = QColor(data["color"])


# =============================================================================
# SMART SLOT ITEM (Container Completo)
# =============================================================================

class SmartSlotItem(SmartGraphicsItem):
    """
    Slot completo que contém imagem, texto e preço.
    Representa um produto no layout.
    """
    
    product_assigned = Signal(dict)
    product_cleared = Signal()
    
    def __init__(
        self,
        slot_index: int,
        element_id: str,
        x: float = 0,
        y: float = 0,
        width: float = 200,
        height: float = 250,
        parent=None
    ):
        super().__init__(element_id, x, y, width, height, parent)
        
        self.slot_index = slot_index
        
        # Sub-itens
        self._image_item: Optional[SmartImageItem] = None
        self._name_item: Optional[SmartTextItem] = None
        self._price_item: Optional[SmartPriceItem] = None
        
        # Aceita drops
        self.setAcceptDrops(True)
    
    def set_product(self, product_data: Dict):
        """Atribui produto ao slot."""
        self.product_data = product_data
        
        # Atualiza sub-itens se existirem
        if self._name_item:
            self._name_item.set_text(product_data.get("nome_sanitizado", ""))
        
        if self._price_item:
            self._price_item.set_price(float(product_data.get("preco_venda_atual", 0)))
        
        self.product_assigned.emit(product_data)
        self.content_changed.emit()
        self.update()
    
    def clear_product(self):
        """Remove produto do slot."""
        self.product_data = None
        
        if self._name_item:
            self._name_item.set_text("")
        if self._price_item:
            self._price_item.set_price(0)
        if self._image_item:
            self._image_item.clear_image()
        
        self.product_cleared.emit()
        self.update()
    
    def paint(
        self,
        painter: QPainter,
        option: QStyleOptionGraphicsItem,
        widget: Optional[QWidget] = None
    ):
        # Background do slot
        painter.fillRect(self._rect, QBrush(QColor("#1A1A2E")))
        
        # Borda de estado
        super().paint(painter, option, widget)
        
        # Info do slot
        if not self.product_data:
            painter.setPen(QColor("#404060"))
            painter.setFont(QFont("Segoe UI", 11))
            painter.drawText(
                self._rect,
                Qt.AlignCenter,
                f"Slot #{self.slot_index}\nArraste um produto"
            )
        else:
            # Desenha preview do produto
            self._draw_product_preview(painter)
    
    def _draw_product_preview(self, painter: QPainter):
        """Desenha preview do produto atribuído."""
        if not self.product_data:
            return
        
        name = self.product_data.get("nome_sanitizado", "?")
        price = self.product_data.get("preco_venda_atual", 0)
        
        # Nome
        painter.setPen(QColor("#FFFFFF"))
        painter.setFont(QFont("Roboto", 11))
        name_rect = QRectF(
            self._rect.x() + 5,
            self._rect.bottom() - 60,
            self._rect.width() - 10,
            25
        )
        painter.drawText(name_rect, Qt.AlignLeft | Qt.AlignVCenter, name[:25])
        
        # Preço
        painter.setPen(QColor("#2ECC71"))
        painter.setFont(QFont("Roboto", 18, QFont.Bold))
        price_rect = QRectF(
            self._rect.x() + 5,
            self._rect.bottom() - 35,
            self._rect.width() - 10,
            30
        )
        painter.drawText(
            price_rect,
            Qt.AlignLeft | Qt.AlignVCenter,
            f"R$ {float(price):.2f}".replace(".", ",")
        )
    
    def dragEnterEvent(self, event):
        """Aceita drops de produtos."""
        if event.mimeData().hasFormat("application/x-autotabloide-product"):
            self.set_state(self.STATE_HOVER)
            event.acceptProposedAction()
        else:
            event.ignore()
    
    def dragLeaveEvent(self, event):
        if self.product_data:
            self.set_state(self.STATE_NORMAL)
        else:
            self.set_state(self.STATE_NORMAL)
    
    def dropEvent(self, event):
        """Processa drop de produto com undo/redo."""
        if event.mimeData().hasFormat("application/x-autotabloide-product"):
            data = event.mimeData().data("application/x-autotabloide-product")
            payload = json.loads(bytes(data).decode('utf-8'))
            
            # ProductsTableModel envia lista - pega primeiro item
            if isinstance(payload, list) and len(payload) > 0:
                product = payload[0]
            else:
                product = payload
            
            # Registra undo antes de modificar
            old_data = self.product_data.copy() if self.product_data else None
            
            try:
                from src.qt.core.undo_redo import get_undo_manager
                get_undo_manager().record_drop(self, product, old_data)
            except ImportError:
                pass
            
            self.set_product(product)
            event.acceptProposedAction()
    
    def check_overflow(self) -> bool:
        """Verifica se nome do produto estoura área."""
        if not self.product_data:
            return False
            
        name = self.product_data.get("nome_sanitizado", "?")
        font = QFont("Roboto", 11)
        metrics = QFontMetrics(font)
        
        # Área definida no paint (aprox)
        name_rect = QRectF(
            self._rect.x() + 5,
            self._rect.bottom() - 60,
            self._rect.width() - 10,
            25
        )
        
        text_rect = metrics.boundingRect(
            name_rect.toRect(),
            Qt.AlignLeft | Qt.AlignVCenter,
            name
        )
        
        # Se bounding rect do texto for maior que o rect disponível
        return text_rect.width() > name_rect.width() or text_rect.height() > name_rect.height()

    def get_image_dpi(self) -> Optional[float]:
        """Tenta calcular DPI da imagem do produto."""
        # Se tiver sub-item
        if self._image_item:
            return self._image_item.get_image_dpi()
            
        # Se tiver produto mas sem sub-item (preview mode)
        # Teria que carregar a imagem para saber resolução.
        # Por performance, ignoramos ou carregamos sob demanda?
        # Vamos assumir que se não tem sub-item, não tem checagem visual precisa.
        return None  # TODO: Implementar check lazy loading
        
    def contextMenuEvent(self, event):
        """Menu de contexto completo para slot."""
        menu = QMenu()
        
        has_product = self.product_data is not None
        
        # Ações para slot com produto
        if has_product:
            action_edit_price = menu.addAction("✏️ Editar Preço")
            action_view_stock = menu.addAction("📦 Ver no Estoque")
            menu.addSeparator()
            action_copy_style = menu.addAction("🎨 Copiar Estilo")
            action_apply_all = menu.addAction("📋 Aplicar Preço em Todos")
            menu.addSeparator()
            action_clear = menu.addAction("🗑️ Limpar Slot")
        else:
            action_edit_price = None
            action_view_stock = None
            action_copy_style = None
            action_apply_all = None
            action_clear = None
        
        menu.addSeparator()
        action_lock = menu.addAction("🔒 Travar Slot")
        action_lock.setCheckable(True)
        action_lock.setChecked(getattr(self, '_locked', False))
        
        # Executa menu
        action = menu.exec(event.screenPos())
        
        if action == action_clear and has_product:
            self._clear_with_undo()
        elif action == action_edit_price and has_product:
            self._show_price_editor()
        elif action == action_lock:
            self._locked = not getattr(self, '_locked', False)
    
    def _clear_with_undo(self):
        """Limpa slot registrando undo."""
        if self.product_data:
            old_data = self.product_data.copy()
            
            try:
                from src.qt.core.undo_redo import get_undo_manager
                get_undo_manager().record_clear(self, old_data)
            except ImportError:
                pass
            
            self.clear_product()
    
    def _show_price_editor(self):
        """Mostra editor inline de preço."""
        from PySide6.QtWidgets import QInputDialog
        
        if not self.product_data:
            return
        
        old_price = float(self.product_data.get('preco_venda_atual', 0))
        
        new_price, ok = QInputDialog.getDouble(
            None,
            "Editar Preço",
            "Novo preço (R$):",
            old_price,
            0.0,
            99999.99,
            2
        )
        
        if ok and new_price != old_price:
            try:
                from src.qt.core.undo_redo import get_undo_manager
                get_undo_manager().record_price_edit(self, old_price, new_price)
            except ImportError:
                pass
            
            self.product_data['preco_venda_atual'] = new_price
            self.update()



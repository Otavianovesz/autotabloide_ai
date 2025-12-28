"""
AutoTabloide AI - Selection Graphics
====================================
PROTOCOLO DE RETIFICAÇÃO NÍVEL 0 - Fase 3 (Passos 121-123)
Gráficos de seleção para o Atelier.
"""

from __future__ import annotations
from typing import List, Optional
import logging

from PySide6.QtCore import Qt, QRectF, QPointF
from PySide6.QtWidgets import QGraphicsItem, QGraphicsRectItem
from PySide6.QtGui import QPainter, QPen, QColor, QBrush

logger = logging.getLogger("Selection")


class SelectionMarquee(QGraphicsRectItem):
    """
    Retângulo de seleção (rubber band).
    Usado para multi-seleção com arraste.
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.setPen(QPen(QColor("#6C5CE7"), 1, Qt.DashLine))
        self.setBrush(QBrush(QColor(108, 92, 231, 30)))  # Semi-transparente
        
        self.setZValue(2000)
        self.hide()
        
        self._start_pos = QPointF()
    
    def start_selection(self, pos: QPointF):
        """Inicia seleção."""
        self._start_pos = pos
        self.setRect(QRectF(pos, pos))
        self.show()
    
    def update_selection(self, pos: QPointF):
        """Atualiza durante arraste."""
        rect = QRectF(self._start_pos, pos).normalized()
        self.setRect(rect)
    
    def end_selection(self) -> QRectF:
        """Finaliza seleção e retorna área."""
        rect = self.rect()
        self.hide()
        return rect


class SelectionHandle(QGraphicsRectItem):
    """
    Handle de redimensionamento para item selecionado.
    """
    
    def __init__(self, position: str, parent=None):
        super().__init__(parent)
        
        self._position = position  # tl, tc, tr, ml, mr, bl, bc, br
        self._size = 8
        
        self.setRect(-self._size/2, -self._size/2, self._size, self._size)
        self.setBrush(QBrush(QColor("#6C5CE7")))
        self.setPen(QPen(QColor("#FFFFFF"), 1))
        
        self.setFlag(QGraphicsItem.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges, True)
        
        self._set_cursor()
        self.setZValue(2001)
    
    def _set_cursor(self):
        cursors = {
            "tl": Qt.SizeFDiagCursor,
            "br": Qt.SizeFDiagCursor,
            "tr": Qt.SizeBDiagCursor,
            "bl": Qt.SizeBDiagCursor,
            "tc": Qt.SizeVerCursor,
            "bc": Qt.SizeVerCursor,
            "ml": Qt.SizeHorCursor,
            "mr": Qt.SizeHorCursor,
        }
        self.setCursor(cursors.get(self._position, Qt.ArrowCursor))
    
    @property
    def position(self) -> str:
        return self._position


class SelectionFrame(QGraphicsItem):
    """
    Frame de seleção com handles.
    Mostra borda + 8 handles de redimensionamento.
    """
    
    def __init__(self, rect: QRectF, parent=None):
        super().__init__(parent)
        
        self._rect = rect
        self._handles: List[SelectionHandle] = []
        
        self.setZValue(2000)
        self._create_handles()
    
    def boundingRect(self) -> QRectF:
        return self._rect.adjusted(-10, -10, 10, 10)
    
    def paint(self, painter: QPainter, option, widget):
        # Borda de seleção
        pen = QPen(QColor("#6C5CE7"), 2)
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)
        painter.drawRect(self._rect)
        
        # Dimensões
        font = painter.font()
        font.setPointSize(9)
        painter.setFont(font)
        painter.setPen(QColor("#6C5CE7"))
        
        w = self._rect.width()
        h = self._rect.height()
        text = f"{w:.0f} × {h:.0f}"
        
        painter.drawText(
            self._rect.bottomLeft() + QPointF(0, 15),
            text
        )
    
    def _create_handles(self):
        """Cria 8 handles de redimensionamento."""
        positions = {
            "tl": self._rect.topLeft(),
            "tc": QPointF(self._rect.center().x(), self._rect.top()),
            "tr": self._rect.topRight(),
            "ml": QPointF(self._rect.left(), self._rect.center().y()),
            "mr": QPointF(self._rect.right(), self._rect.center().y()),
            "bl": self._rect.bottomLeft(),
            "bc": QPointF(self._rect.center().x(), self._rect.bottom()),
            "br": self._rect.bottomRight(),
        }
        
        for pos_name, pos in positions.items():
            handle = SelectionHandle(pos_name, self)
            handle.setPos(pos)
            self._handles.append(handle)
    
    def update_rect(self, rect: QRectF):
        """Atualiza retângulo e reposiciona handles."""
        self._rect = rect
        
        positions = {
            "tl": rect.topLeft(),
            "tc": QPointF(rect.center().x(), rect.top()),
            "tr": rect.topRight(),
            "ml": QPointF(rect.left(), rect.center().y()),
            "mr": QPointF(rect.right(), rect.center().y()),
            "bl": rect.bottomLeft(),
            "bc": QPointF(rect.center().x(), rect.bottom()),
            "br": rect.bottomRight(),
        }
        
        for handle in self._handles:
            if handle.position in positions:
                handle.setPos(positions[handle.position])
        
        self.update()


class AlignmentGuides(QGraphicsItem):
    """
    Guias de alinhamento inteligentes.
    Aparecem quando item está alinhado com outros.
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self._guides: List[tuple] = []  # (orientation, position)
        
        self.setZValue(1999)
    
    def boundingRect(self) -> QRectF:
        return QRectF(-10000, -10000, 20000, 20000)
    
    def paint(self, painter: QPainter, option, widget):
        if not self._guides:
            return
        
        pen = QPen(QColor("#FF6B6B"), 1, Qt.DashLine)
        painter.setPen(pen)
        
        for orientation, position in self._guides:
            if orientation == "horizontal":
                painter.drawLine(-10000, int(position), 10000, int(position))
            else:
                painter.drawLine(int(position), -10000, int(position), 10000)
    
    def set_guides(self, guides: List[tuple]):
        """Define guias a mostrar."""
        self._guides = guides
        self.update()
    
    def clear(self):
        """Limpa guias."""
        self._guides = []
        self.update()


# =============================================================================
# HELPERS
# =============================================================================

def create_selection_marquee() -> SelectionMarquee:
    return SelectionMarquee()


def create_selection_frame(rect: QRectF) -> SelectionFrame:
    return SelectionFrame(rect)

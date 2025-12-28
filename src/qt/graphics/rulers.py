"""
AutoTabloide AI - Ruler Guides
==============================
PROTOCOLO DE RETIFICAÇÃO NÍVEL 0 - Fase 3 (Passos 101, 102)
Réguas e guias para o Atelier.
"""

from __future__ import annotations
from typing import List, Optional
import logging

from PySide6.QtCore import Qt, QRectF, QPointF
from PySide6.QtWidgets import QGraphicsItem, QGraphicsView, QWidget
from PySide6.QtGui import QPainter, QPen, QColor, QFont

logger = logging.getLogger("Rulers")


MM_TO_PT = 2.834645669


class RulerItem(QGraphicsItem):
    """
    Régua para a borda do Atelier.
    Mostra marcações em mm ou cm.
    """
    
    def __init__(
        self,
        orientation: str,  # "horizontal" or "vertical"
        length: float,
        thickness: int = 20,
        parent=None
    ):
        super().__init__(parent)
        self._orientation = orientation
        self._length = length
        self._thickness = thickness
        self._unit = "mm"  # mm or cm
        
        self.setZValue(1001)
    
    def boundingRect(self) -> QRectF:
        if self._orientation == "horizontal":
            return QRectF(-self._thickness, -self._thickness, self._length + self._thickness, self._thickness)
        else:
            return QRectF(-self._thickness, -self._thickness, self._thickness, self._length + self._thickness)
    
    def paint(self, painter: QPainter, option, widget):
        painter.fillRect(self.boundingRect(), QColor("#1A1A2E"))
        
        pen = QPen(QColor("#808080"), 0.5)
        painter.setPen(pen)
        
        font = QFont("Arial", 7)
        painter.setFont(font)
        
        # Intervalo de marcação
        interval_mm = 10 if self._unit == "mm" else 100
        interval_pt = interval_mm * MM_TO_PT
        
        if self._orientation == "horizontal":
            self._draw_horizontal_ruler(painter, interval_pt, interval_mm)
        else:
            self._draw_vertical_ruler(painter, interval_pt, interval_mm)
    
    def _draw_horizontal_ruler(self, painter: QPainter, interval: float, label_interval: int):
        y = 0
        pos = 0.0
        tick = 0
        
        while pos <= self._length:
            is_major = tick % 10 == 0
            tick_height = 12 if is_major else 6
            
            painter.drawLine(QPointF(pos, y), QPointF(pos, y - tick_height))
            
            if is_major:
                label = str(int(tick * label_interval / 10))
                painter.drawText(QPointF(pos + 2, y - 12), label)
            
            pos += interval / 10
            tick += 1
    
    def _draw_vertical_ruler(self, painter: QPainter, interval: float, label_interval: int):
        x = 0
        pos = 0.0
        tick = 0
        
        while pos <= self._length:
            is_major = tick % 10 == 0
            tick_width = 12 if is_major else 6
            
            painter.drawLine(QPointF(x, pos), QPointF(x - tick_width, pos))
            
            if is_major:
                label = str(int(tick * label_interval / 10))
                painter.save()
                painter.translate(x - 14, pos + 3)
                painter.rotate(-90)
                painter.drawText(0, 0, label)
                painter.restore()
            
            pos += interval / 10
            tick += 1


class GuideLineItem(QGraphicsItem):
    """
    Linha guia arrastável.
    """
    
    def __init__(
        self,
        orientation: str,  # "horizontal" or "vertical"
        position: float,
        length: float,
        parent=None
    ):
        super().__init__(parent)
        self._orientation = orientation
        self._position = position
        self._length = length
        
        self.setFlag(QGraphicsItem.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges, True)
        self.setCursor(Qt.SizeVerCursor if orientation == "horizontal" else Qt.SizeHorCursor)
        self.setZValue(999)
    
    def boundingRect(self) -> QRectF:
        if self._orientation == "horizontal":
            return QRectF(0, -2, self._length, 4)
        else:
            return QRectF(-2, 0, 4, self._length)
    
    def paint(self, painter: QPainter, option, widget):
        pen = QPen(QColor("#6C5CE7"), 1, Qt.DashLine)
        painter.setPen(pen)
        
        if self._orientation == "horizontal":
            painter.drawLine(0, 0, self._length, 0)
        else:
            painter.drawLine(0, 0, 0, self._length)
    
    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemPositionChange:
            # Limita movimento a um eixo
            new_pos = value
            if self._orientation == "horizontal":
                new_pos.setX(0)
            else:
                new_pos.setY(0)
            return new_pos
        return super().itemChange(change, value)


class GridOverlay(QGraphicsItem):
    """
    Overlay de grid para alinhamento.
    """
    
    def __init__(
        self,
        width: float,
        height: float,
        grid_size: float = 10 * MM_TO_PT,
        parent=None
    ):
        super().__init__(parent)
        self._width = width
        self._height = height
        self._grid_size = grid_size
        self._visible = False
        
        self.setZValue(997)
    
    def boundingRect(self) -> QRectF:
        return QRectF(0, 0, self._width, self._height)
    
    def paint(self, painter: QPainter, option, widget):
        if not self._visible:
            return
        
        pen = QPen(QColor(100, 100, 100, 50), 0.5)
        painter.setPen(pen)
        
        # Linhas verticais
        x = 0.0
        while x <= self._width:
            painter.drawLine(QPointF(x, 0), QPointF(x, self._height))
            x += self._grid_size
        
        # Linhas horizontais
        y = 0.0
        while y <= self._height:
            painter.drawLine(QPointF(0, y), QPointF(self._width, y))
            y += self._grid_size
    
    def set_visible(self, visible: bool):
        self._visible = visible
        self.update()
    
    def toggle(self):
        self._visible = not self._visible
        self.update()


# =============================================================================
# HELPERS
# =============================================================================

def create_rulers(
    doc_width: float,
    doc_height: float,
    thickness: int = 20
) -> tuple:
    """Cria réguas horizontal e vertical."""
    h_ruler = RulerItem("horizontal", doc_width, thickness)
    v_ruler = RulerItem("vertical", doc_height, thickness)
    return h_ruler, v_ruler


def create_grid(
    doc_width: float,
    doc_height: float,
    grid_mm: float = 10
) -> GridOverlay:
    """Cria overlay de grid."""
    return GridOverlay(doc_width, doc_height, grid_mm * MM_TO_PT)

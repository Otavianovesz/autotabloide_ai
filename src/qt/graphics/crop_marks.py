"""
AutoTabloide AI - Crop Marks and Bleed
======================================
PROTOCOLO DE RETIFICAÇÃO NÍVEL 0 - Fase 4 (Passos 151-155)
Marcas de corte e sangria para impressão profissional.
"""

from __future__ import annotations
from typing import Tuple
import logging

from PySide6.QtCore import Qt, QRectF, QPointF
from PySide6.QtWidgets import QGraphicsItem, QGraphicsRectItem
from PySide6.QtGui import QPainter, QPen, QColor, QBrush

logger = logging.getLogger("CropMarks")


# =============================================================================
# CONSTANTS
# =============================================================================

DEFAULT_BLEED_MM = 3.0
DEFAULT_MARK_LENGTH_MM = 5.0
DEFAULT_MARK_OFFSET_MM = 3.0

MM_TO_PT = 2.834645669  # 1mm = 2.834... points


# =============================================================================
# CROP MARKS ITEM
# =============================================================================

class CropMarksItem(QGraphicsItem):
    """
    Item gráfico para marcas de corte.
    
    Desenha linhas de corte nos 4 cantos do documento.
    """
    
    def __init__(
        self,
        doc_width: float,
        doc_height: float,
        bleed_mm: float = DEFAULT_BLEED_MM,
        mark_length_mm: float = DEFAULT_MARK_LENGTH_MM,
        mark_offset_mm: float = DEFAULT_MARK_OFFSET_MM,
        parent=None
    ):
        super().__init__(parent)
        
        self._doc_width = doc_width
        self._doc_height = doc_height
        self._bleed = bleed_mm * MM_TO_PT
        self._mark_length = mark_length_mm * MM_TO_PT
        self._mark_offset = mark_offset_mm * MM_TO_PT
        
        # Cor das marcas
        self._color = QColor("#000000")
        self._line_width = 0.25 * MM_TO_PT  # 0.25mm
        
        self.setZValue(1000)  # Acima de tudo
    
    def boundingRect(self) -> QRectF:
        extra = self._bleed + self._mark_offset + self._mark_length
        return QRectF(
            -extra, -extra,
            self._doc_width + 2 * extra,
            self._doc_height + 2 * extra
        )
    
    def paint(self, painter: QPainter, option, widget):
        pen = QPen(self._color, self._line_width)
        painter.setPen(pen)
        
        w = self._doc_width
        h = self._doc_height
        bleed = self._bleed
        length = self._mark_length
        offset = self._mark_offset
        
        # Cantos do documento (sem bleed)
        corners = [
            (0, 0),           # Top-left
            (w, 0),           # Top-right
            (0, h),           # Bottom-left
            (w, h),           # Bottom-right
        ]
        
        for cx, cy in corners:
            # Linhas horizontais
            if cx == 0:
                # Esquerda
                x1 = -bleed - offset - length
                x2 = -bleed - offset
            else:
                # Direita
                x1 = w + bleed + offset
                x2 = w + bleed + offset + length
            
            painter.drawLine(QPointF(x1, cy), QPointF(x2, cy))
            
            # Linhas verticais
            if cy == 0:
                # Topo
                y1 = -bleed - offset - length
                y2 = -bleed - offset
            else:
                # Base
                y1 = h + bleed + offset
                y2 = h + bleed + offset + length
            
            painter.drawLine(QPointF(cx, y1), QPointF(cx, y2))


# =============================================================================
# BLEED OVERLAY ITEM
# =============================================================================

class BleedOverlayItem(QGraphicsRectItem):
    """
    Overlay visual mostrando área de sangria.
    Área semi-transparente indicando zona de corte.
    """
    
    def __init__(
        self,
        doc_width: float,
        doc_height: float,
        bleed_mm: float = DEFAULT_BLEED_MM,
        parent=None
    ):
        bleed = bleed_mm * MM_TO_PT
        
        # Rect inclui bleed
        super().__init__(
            -bleed, -bleed,
            doc_width + 2 * bleed,
            doc_height + 2 * bleed,
            parent
        )
        
        self._doc_width = doc_width
        self._doc_height = doc_height
        self._bleed = bleed
        
        # Estilo
        self.setPen(QPen(QColor("#FF0000"), 1, Qt.DashLine))
        self.setBrush(Qt.NoBrush)
        
        self.setZValue(999)
    
    def paint(self, painter: QPainter, option, widget):
        # Desenha borda da sangria
        super().paint(painter, option, widget)
        
        # Desenha área segura (documento sem bleed)
        safe_pen = QPen(QColor("#00FF00"), 1, Qt.DotLine)
        painter.setPen(safe_pen)
        painter.drawRect(0, 0, self._doc_width, self._doc_height)


# =============================================================================
# SAFE MARGIN ITEM
# =============================================================================

class SafeMarginItem(QGraphicsRectItem):
    """
    Margem de segurança interna.
    Área onde texto importante deve ficar.
    """
    
    def __init__(
        self,
        doc_width: float,
        doc_height: float,
        margin_mm: float = 5.0,
        parent=None
    ):
        margin = margin_mm * MM_TO_PT
        
        super().__init__(
            margin, margin,
            doc_width - 2 * margin,
            doc_height - 2 * margin,
            parent
        )
        
        # Estilo
        self.setPen(QPen(QColor("#0088FF"), 0.5, Qt.DotLine))
        self.setBrush(Qt.NoBrush)
        
        self.setZValue(998)


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def create_crop_marks(
    doc_width: float,
    doc_height: float,
    bleed_mm: float = 3.0
) -> CropMarksItem:
    """Cria item de marcas de corte."""
    return CropMarksItem(doc_width, doc_height, bleed_mm)


def create_bleed_overlay(
    doc_width: float,
    doc_height: float,
    bleed_mm: float = 3.0
) -> BleedOverlayItem:
    """Cria overlay de sangria."""
    return BleedOverlayItem(doc_width, doc_height, bleed_mm)


def create_safe_margin(
    doc_width: float,
    doc_height: float,
    margin_mm: float = 5.0
) -> SafeMarginItem:
    """Cria margem de segurança."""
    return SafeMarginItem(doc_width, doc_height, margin_mm)

"""
AutoTabloide AI - Zoom Controls
===============================
PROTOCOLO DE RETIFICAÇÃO NÍVEL 0 - Fase 3 (Passos 100-102)
Controles de zoom e navegação para o Atelier.
"""

from __future__ import annotations
from typing import Optional
import logging

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QPushButton,
    QSlider, QLabel, QToolButton, QFrame
)
from PySide6.QtGui import QIcon

logger = logging.getLogger("ZoomControls")


class ZoomControlsWidget(QWidget):
    """
    Widget com controles de zoom.
    
    Features:
    - Slider de zoom (25% - 400%)
    - Botões +/-
    - Fit to view
    - Reset 100%
    """
    
    zoom_changed = Signal(int)  # percent
    fit_requested = Signal()
    reset_requested = Signal()
    
    MIN_ZOOM = 25
    MAX_ZOOM = 400
    DEFAULT_ZOOM = 100
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._current_zoom = self.DEFAULT_ZOOM
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(8)
        
        # Fit button
        self.btn_fit = QToolButton()
        self.btn_fit.setText("⬜")
        self.btn_fit.setToolTip("Ajustar à tela (Ctrl+0)")
        self.btn_fit.clicked.connect(self.fit_requested.emit)
        layout.addWidget(self.btn_fit)
        
        # Separator
        sep1 = QFrame()
        sep1.setFrameShape(QFrame.VLine)
        layout.addWidget(sep1)
        
        # Zoom out
        self.btn_minus = QToolButton()
        self.btn_minus.setText("−")
        self.btn_minus.setToolTip("Zoom out (-)")
        self.btn_minus.clicked.connect(self._zoom_out)
        layout.addWidget(self.btn_minus)
        
        # Slider
        self.slider = QSlider(Qt.Horizontal)
        self.slider.setRange(self.MIN_ZOOM, self.MAX_ZOOM)
        self.slider.setValue(self.DEFAULT_ZOOM)
        self.slider.setTickInterval(25)
        self.slider.setFixedWidth(120)
        self.slider.valueChanged.connect(self._on_slider_changed)
        layout.addWidget(self.slider)
        
        # Zoom in
        self.btn_plus = QToolButton()
        self.btn_plus.setText("+")
        self.btn_plus.setToolTip("Zoom in (+)")
        self.btn_plus.clicked.connect(self._zoom_in)
        layout.addWidget(self.btn_plus)
        
        # Separator
        sep2 = QFrame()
        sep2.setFrameShape(QFrame.VLine)
        layout.addWidget(sep2)
        
        # Percentage label
        self.zoom_label = QLabel("100%")
        self.zoom_label.setMinimumWidth(45)
        self.zoom_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.zoom_label)
        
        # Reset button
        self.btn_reset = QToolButton()
        self.btn_reset.setText("1:1")
        self.btn_reset.setToolTip("Reset 100% (Ctrl+1)")
        self.btn_reset.clicked.connect(self._reset_zoom)
        layout.addWidget(self.btn_reset)
    
    def _zoom_in(self):
        """Aumenta zoom em 25%."""
        new_zoom = min(self._current_zoom + 25, self.MAX_ZOOM)
        self.set_zoom(new_zoom)
    
    def _zoom_out(self):
        """Diminui zoom em 25%."""
        new_zoom = max(self._current_zoom - 25, self.MIN_ZOOM)
        self.set_zoom(new_zoom)
    
    def _reset_zoom(self):
        """Reseta para 100%."""
        self.set_zoom(self.DEFAULT_ZOOM)
        self.reset_requested.emit()
    
    def _on_slider_changed(self, value: int):
        """Callback do slider."""
        self._current_zoom = value
        self.zoom_label.setText(f"{value}%")
        self.zoom_changed.emit(value)
    
    def set_zoom(self, percent: int):
        """Define zoom."""
        percent = max(self.MIN_ZOOM, min(percent, self.MAX_ZOOM))
        self._current_zoom = percent
        self.slider.blockSignals(True)
        self.slider.setValue(percent)
        self.slider.blockSignals(False)
        self.zoom_label.setText(f"{percent}%")
        self.zoom_changed.emit(percent)
    
    def get_zoom(self) -> int:
        """Retorna zoom atual."""
        return self._current_zoom


class MiniMapWidget(QWidget):
    """
    Mini-mapa para navegação rápida.
    Mostra visão geral do documento.
    """
    
    view_changed = Signal(float, float)  # center_x, center_y
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(150, 200)
        self.setStyleSheet("""
            MiniMapWidget {
                background-color: #1A1A2E;
                border: 1px solid #2D2D44;
                border-radius: 4px;
            }
        """)
        
        self._view_rect = (0, 0, 1, 1)  # normalized
        self._doc_aspect = 0.7  # A3 ratio
    
    def set_view_rect(self, x: float, y: float, w: float, h: float):
        """Define retângulo visível (normalizado 0-1)."""
        self._view_rect = (x, y, w, h)
        self.update()
    
    def paintEvent(self, event):
        from PySide6.QtGui import QPainter, QColor, QPen
        
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Background
        painter.fillRect(self.rect(), QColor("#1A1A2E"))
        
        # Document area
        doc_w = self.width() - 20
        doc_h = int(doc_w / self._doc_aspect)
        doc_x = 10
        doc_y = (self.height() - doc_h) // 2
        
        painter.fillRect(doc_x, doc_y, doc_w, doc_h, QColor("#2D2D44"))
        
        # View rect
        x, y, w, h = self._view_rect
        view_x = doc_x + int(x * doc_w)
        view_y = doc_y + int(y * doc_h)
        view_w = max(10, int(w * doc_w))
        view_h = max(10, int(h * doc_h))
        
        painter.setPen(QPen(QColor("#6C5CE7"), 2))
        painter.drawRect(view_x, view_y, view_w, view_h)
    
    def mousePressEvent(self, event):
        self._navigate_to(event.position())
    
    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.LeftButton:
            self._navigate_to(event.position())
    
    def _navigate_to(self, pos):
        """Navega para posição clicada."""
        doc_w = self.width() - 20
        doc_h = int(doc_w / self._doc_aspect)
        doc_x = 10
        doc_y = (self.height() - doc_h) // 2
        
        x = (pos.x() - doc_x) / doc_w
        y = (pos.y() - doc_y) / doc_h
        
        x = max(0, min(1, x))
        y = max(0, min(1, y))
        
        self.view_changed.emit(x, y)


def create_zoom_controls(parent=None) -> ZoomControlsWidget:
    """Cria widget de controles de zoom."""
    return ZoomControlsWidget(parent)

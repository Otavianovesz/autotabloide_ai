"""
AutoTabloide AI - Sentinel UI Widget
=====================================
PROTOCOLO DE RETIFICAÇÃO NÍVEL 0 - Fase 5 (Passos 176-180)
Widget indicador de status do Sentinel com animações.
"""

from __future__ import annotations
from typing import Optional
from enum import Enum
import logging

from PySide6.QtCore import (
    Qt, Signal, Slot, QTimer, QPropertyAnimation, 
    QEasingCurve, Property, QSize
)
from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLabel, 
    QPushButton, QFrame, QToolTip
)
from PySide6.QtGui import QColor, QPainter, QBrush, QPen

logger = logging.getLogger("SentinelUI")


# =============================================================================
# SENTINEL STATUS
# =============================================================================

class SentinelStatus(Enum):
    """Estados possíveis do Sentinel."""
    OFFLINE = "offline"
    IDLE = "idle"
    LOADING = "loading"
    PROCESSING = "processing"
    ERROR = "error"


STATUS_COLORS = {
    SentinelStatus.OFFLINE: "#7F8C8D",    # Cinza
    SentinelStatus.IDLE: "#2ECC71",        # Verde
    SentinelStatus.LOADING: "#F39C12",     # Laranja
    SentinelStatus.PROCESSING: "#3498DB",  # Azul
    SentinelStatus.ERROR: "#E74C3C",       # Vermelho
}

STATUS_LABELS = {
    SentinelStatus.OFFLINE: "Sentinel Offline",
    SentinelStatus.IDLE: "Sentinel Pronto",
    SentinelStatus.LOADING: "Carregando Modelo...",
    SentinelStatus.PROCESSING: "Processando...",
    SentinelStatus.ERROR: "Erro no Sentinel",
}


# =============================================================================
# ANIMATED STATUS DOT
# =============================================================================

class StatusDot(QWidget):
    """
    Bolinha animada que indica status do Sentinel.
    Pulsa quando processando.
    """
    
    clicked = Signal()
    
    def __init__(self, size: int = 12, parent=None):
        super().__init__(parent)
        self._size = size
        self._color = QColor("#7F8C8D")
        self._pulse_opacity = 1.0
        self._pulsing = False
        
        self.setFixedSize(size + 8, size + 8)
        self.setCursor(Qt.PointingHandCursor)
        
        # Timer para pulse
        self._pulse_timer = QTimer()
        self._pulse_timer.timeout.connect(self._animate_pulse)
        self._pulse_direction = -1
    
    def set_status(self, status: SentinelStatus):
        """Define status e cor."""
        self._color = QColor(STATUS_COLORS.get(status, "#7F8C8D"))
        
        # Ativa pulse para estados ativos
        if status in (SentinelStatus.LOADING, SentinelStatus.PROCESSING):
            self._start_pulse()
        else:
            self._stop_pulse()
        
        self.update()
    
    def _start_pulse(self):
        if not self._pulsing:
            self._pulsing = True
            self._pulse_timer.start(50)
    
    def _stop_pulse(self):
        if self._pulsing:
            self._pulsing = False
            self._pulse_timer.stop()
            self._pulse_opacity = 1.0
            self.update()
    
    def _animate_pulse(self):
        self._pulse_opacity += self._pulse_direction * 0.05
        
        if self._pulse_opacity <= 0.3:
            self._pulse_direction = 1
        elif self._pulse_opacity >= 1.0:
            self._pulse_direction = -1
        
        self.update()
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Sombra/glow
        glow_color = QColor(self._color)
        glow_color.setAlphaF(0.3 * self._pulse_opacity)
        painter.setBrush(QBrush(glow_color))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(2, 2, self._size + 4, self._size + 4)
        
        # Círculo principal
        main_color = QColor(self._color)
        main_color.setAlphaF(self._pulse_opacity)
        painter.setBrush(QBrush(main_color))
        painter.setPen(QPen(self._color.darker(120), 1))
        painter.drawEllipse(4, 4, self._size, self._size)
    
    def mousePressEvent(self, event):
        self.clicked.emit()


# =============================================================================
# SENTINEL INDICATOR WIDGET
# =============================================================================

class SentinelIndicator(QFrame):
    """
    Widget compacto para barra de status mostrando estado do Sentinel.
    
    Features:
    - Dot animado com cor de status
    - Label com descrição
    - Click para abrir painel completo
    """
    
    clicked = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._status = SentinelStatus.OFFLINE
        self._setup_ui()
    
    def _setup_ui(self):
        self.setFrameShape(QFrame.NoFrame)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 2, 8, 2)
        layout.setSpacing(6)
        
        # Status dot
        self.dot = StatusDot(10)
        self.dot.clicked.connect(self.clicked.emit)
        layout.addWidget(self.dot)
        
        # Label
        self.label = QLabel("Sentinel")
        self.label.setStyleSheet("color: #808080; font-size: 11px;")
        layout.addWidget(self.label)
        
        self.setCursor(Qt.PointingHandCursor)
    
    def set_status(self, status: SentinelStatus):
        """Atualiza status."""
        self._status = status
        self.dot.set_status(status)
        self.label.setText(STATUS_LABELS.get(status, "Sentinel"))
        
        # Cor do texto
        if status == SentinelStatus.ERROR:
            self.label.setStyleSheet("color: #E74C3C; font-size: 11px;")
        elif status == SentinelStatus.IDLE:
            self.label.setStyleSheet("color: #2ECC71; font-size: 11px;")
        else:
            self.label.setStyleSheet("color: #808080; font-size: 11px;")
    
    def set_status_from_string(self, status_str: str):
        """Converte string para enum e aplica."""
        mapping = {
            "offline": SentinelStatus.OFFLINE,
            "online": SentinelStatus.IDLE,
            "idle": SentinelStatus.IDLE,
            "loading": SentinelStatus.LOADING,
            "busy": SentinelStatus.PROCESSING,
            "processing": SentinelStatus.PROCESSING,
            "error": SentinelStatus.ERROR,
        }
        status = mapping.get(status_str.lower(), SentinelStatus.OFFLINE)
        self.set_status(status)
    
    def mousePressEvent(self, event):
        self.clicked.emit()
        super().mousePressEvent(event)
    
    def enterEvent(self, event):
        QToolTip.showText(
            self.mapToGlobal(self.rect().bottomLeft()),
            f"Status: {STATUS_LABELS.get(self._status, 'Desconhecido')}\n"
            f"Clique para mais detalhes"
        )
        super().enterEvent(event)


# =============================================================================
# SENTINEL PANEL (EXPANDED VIEW)
# =============================================================================

class SentinelPanel(QFrame):
    """
    Painel expandido com detalhes do Sentinel.
    Mostra logs, status e controles.
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
    
    def _setup_ui(self):
        self.setFrameShape(QFrame.StyledPanel)
        self.setStyleSheet("""
            QFrame {
                background-color: #1A1A2E;
                border: 1px solid #2D2D44;
                border-radius: 8px;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)
        
        # Header
        header = QHBoxLayout()
        
        title = QLabel("🤖 Sentinel AI")
        title.setStyleSheet("font-size: 14px; font-weight: bold; color: #FFFFFF;")
        header.addWidget(title)
        
        header.addStretch()
        
        self.status_label = QLabel("Offline")
        self.status_label.setStyleSheet("color: #7F8C8D;")
        header.addWidget(self.status_label)
        
        layout.addLayout(header)
        
        # Separator
        sep = QFrame()
        sep.setFixedHeight(1)
        sep.setStyleSheet("background-color: #2D2D44;")
        layout.addWidget(sep)
        
        # Stats
        self.stats_label = QLabel("Tarefas: 0 | Tempo: 0s")
        self.stats_label.setStyleSheet("color: #808080; font-size: 11px;")
        layout.addWidget(self.stats_label)
        
        # Controls
        btn_layout = QHBoxLayout()
        
        self.btn_pause = QPushButton("⏸️ Pausar")
        self.btn_pause.setEnabled(False)
        btn_layout.addWidget(self.btn_pause)
        
        self.btn_restart = QPushButton("🔄 Reiniciar")
        btn_layout.addWidget(self.btn_restart)
        
        layout.addLayout(btn_layout)
    
    def update_status(self, status: SentinelStatus, tasks: int = 0, runtime: float = 0):
        """Atualiza status do painel."""
        self.status_label.setText(STATUS_LABELS.get(status, "Desconhecido"))
        self.status_label.setStyleSheet(f"color: {STATUS_COLORS.get(status, '#808080')};")
        
        self.stats_label.setText(f"Tarefas: {tasks} | Tempo: {runtime:.1f}s")
        
        # Habilita pause se processando
        self.btn_pause.setEnabled(status == SentinelStatus.PROCESSING)


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def create_sentinel_indicator(parent=None) -> SentinelIndicator:
    """Cria indicador de Sentinel para status bar."""
    return SentinelIndicator(parent)

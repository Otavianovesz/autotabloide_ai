"""
AutoTabloide AI - Toast Notifications
=====================================
PROTOCOLO DE RETIFICAÇÃO NÍVEL 0 - Fase 6 (Passos 186-188)
Sistema de notificações toast.
"""

from __future__ import annotations
from typing import Optional
from enum import Enum
import logging

from PySide6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, QPoint
from PySide6.QtWidgets import QWidget, QLabel, QHBoxLayout, QPushButton
from PySide6.QtGui import QColor

logger = logging.getLogger("Toast")


class ToastType(Enum):
    INFO = "info"
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"


TOAST_COLORS = {
    ToastType.INFO: ("#3498DB", "#2980B9"),      # Blue
    ToastType.SUCCESS: ("#2ECC71", "#27AE60"),   # Green
    ToastType.WARNING: ("#F39C12", "#D68910"),   # Orange
    ToastType.ERROR: ("#E74C3C", "#C0392B"),     # Red
}

TOAST_ICONS = {
    ToastType.INFO: "ℹ️",
    ToastType.SUCCESS: "✅",
    ToastType.WARNING: "⚠️",
    ToastType.ERROR: "❌",
}


class ToastWidget(QWidget):
    """
    Widget de toast notification.
    Aparece no canto, auto-desaparece.
    """
    
    def __init__(
        self,
        message: str,
        toast_type: ToastType = ToastType.INFO,
        duration: int = 3000,
        parent=None
    ):
        super().__init__(parent)
        self.setWindowFlags(
            Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_ShowWithoutActivating)
        
        self._duration = duration
        self._type = toast_type
        
        self._setup_ui(message)
        self._setup_style()
    
    def _setup_ui(self, message: str):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(12)
        
        # Icon
        icon = QLabel(TOAST_ICONS.get(self._type, "ℹ️"))
        icon.setStyleSheet("font-size: 18px;")
        layout.addWidget(icon)
        
        # Message
        msg = QLabel(message)
        msg.setStyleSheet("color: white; font-size: 13px;")
        msg.setWordWrap(True)
        msg.setMaximumWidth(300)
        layout.addWidget(msg, 1)
        
        # Close button
        close_btn = QPushButton("×")
        close_btn.setFixedSize(20, 20)
        close_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: white;
                border: none;
                font-size: 16px;
            }
            QPushButton:hover {
                background: rgba(255,255,255,0.2);
                border-radius: 10px;
            }
        """)
        close_btn.clicked.connect(self._close)
        layout.addWidget(close_btn)
    
    def _setup_style(self):
        bg, border = TOAST_COLORS.get(self._type, ("#3498DB", "#2980B9"))
        self.setStyleSheet(f"""
            ToastWidget {{
                background-color: {bg};
                border: 2px solid {border};
                border-radius: 8px;
            }}
        """)
    
    def show_toast(self):
        """Mostra o toast com animação."""
        # Posiciona no canto
        if self.parent():
            parent_rect = self.parent().rect()
            x = parent_rect.width() - self.width() - 20
            y = 20
            self.move(x, y)
        
        self.show()
        
        # Slide in
        self._slide_in()
        
        # Auto-hide
        if self._duration > 0:
            QTimer.singleShot(self._duration, self._close)
    
    def _slide_in(self):
        start_pos = self.pos()
        start_pos.setX(start_pos.x() + 100)
        
        self._anim = QPropertyAnimation(self, b"pos")
        self._anim.setDuration(200)
        self._anim.setStartValue(start_pos)
        self._anim.setEndValue(self.pos())
        self._anim.setEasingCurve(QEasingCurve.OutCubic)
        self._anim.start()
    
    def _close(self):
        # Slide out
        end_pos = self.pos()
        end_pos.setX(end_pos.x() + 100)
        
        self._anim = QPropertyAnimation(self, b"pos")
        self._anim.setDuration(150)
        self._anim.setEndValue(end_pos)
        self._anim.setEasingCurve(QEasingCurve.InCubic)
        self._anim.finished.connect(self.deleteLater)
        self._anim.start()


class ToastManager:
    """Gerenciador de toasts."""
    
    _toasts: list = []
    _parent: Optional[QWidget] = None
    
    @classmethod
    def set_parent(cls, parent: QWidget):
        cls._parent = parent
    
    @classmethod
    def show(cls, message: str, toast_type: ToastType = ToastType.INFO, duration: int = 3000):
        """Mostra um toast."""
        toast = ToastWidget(message, toast_type, duration, cls._parent)
        toast.adjustSize()
        toast.show_toast()
        cls._toasts.append(toast)
    
    @classmethod
    def info(cls, message: str, duration: int = 3000):
        cls.show(message, ToastType.INFO, duration)
    
    @classmethod
    def success(cls, message: str, duration: int = 3000):
        cls.show(message, ToastType.SUCCESS, duration)
    
    @classmethod
    def warning(cls, message: str, duration: int = 5000):
        cls.show(message, ToastType.WARNING, duration)
    
    @classmethod
    def error(cls, message: str, duration: int = 0):
        cls.show(message, ToastType.ERROR, duration)


# =============================================================================
# HELPERS
# =============================================================================

def show_toast(message: str, toast_type: str = "info", duration: int = 3000):
    """Helper para mostrar toast."""
    type_map = {
        "info": ToastType.INFO,
        "success": ToastType.SUCCESS,
        "warning": ToastType.WARNING,
        "error": ToastType.ERROR,
    }
    ToastManager.show(message, type_map.get(toast_type, ToastType.INFO), duration)


def toast_success(message: str):
    ToastManager.success(message)


def toast_error(message: str):
    ToastManager.error(message)

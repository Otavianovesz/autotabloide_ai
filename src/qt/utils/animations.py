"""
AutoTabloide AI - Animation Utilities
=====================================
PROTOCOLO DE RETIFICAÇÃO NÍVEL 0 - Fase 6 (Passos 210-212)
Utilitários de animação para UI polish.
"""

from __future__ import annotations
from typing import Optional
import logging

from PySide6.QtCore import (
    Qt, QObject, QPropertyAnimation, QEasingCurve,
    QParallelAnimationGroup, QSequentialAnimationGroup,
    Property, QTimer
)
from PySide6.QtWidgets import QWidget, QGraphicsOpacityEffect
from PySide6.QtGui import QColor

logger = logging.getLogger("Animations")


# =============================================================================
# FADE ANIMATIONS
# =============================================================================

def fade_in(widget: QWidget, duration: int = 300, on_complete=None) -> QPropertyAnimation:
    """Fade in animação."""
    effect = QGraphicsOpacityEffect(widget)
    widget.setGraphicsEffect(effect)
    
    anim = QPropertyAnimation(effect, b"opacity")
    anim.setDuration(duration)
    anim.setStartValue(0.0)
    anim.setEndValue(1.0)
    anim.setEasingCurve(QEasingCurve.OutCubic)
    
    if on_complete:
        anim.finished.connect(on_complete)
    
    anim.start(QPropertyAnimation.DeleteWhenStopped)
    return anim


def fade_out(widget: QWidget, duration: int = 300, on_complete=None) -> QPropertyAnimation:
    """Fade out animação."""
    effect = QGraphicsOpacityEffect(widget)
    widget.setGraphicsEffect(effect)
    
    anim = QPropertyAnimation(effect, b"opacity")
    anim.setDuration(duration)
    anim.setStartValue(1.0)
    anim.setEndValue(0.0)
    anim.setEasingCurve(QEasingCurve.InCubic)
    
    if on_complete:
        anim.finished.connect(on_complete)
    
    anim.start(QPropertyAnimation.DeleteWhenStopped)
    return anim


# =============================================================================
# SLIDE ANIMATIONS
# =============================================================================

def slide_in_left(widget: QWidget, duration: int = 400, offset: int = 100) -> QPropertyAnimation:
    """Slide in da esquerda."""
    start_pos = widget.pos()
    start_pos.setX(start_pos.x() - offset)
    
    anim = QPropertyAnimation(widget, b"pos")
    anim.setDuration(duration)
    anim.setStartValue(start_pos)
    anim.setEndValue(widget.pos())
    anim.setEasingCurve(QEasingCurve.OutCubic)
    
    anim.start(QPropertyAnimation.DeleteWhenStopped)
    return anim


def slide_in_right(widget: QWidget, duration: int = 400, offset: int = 100) -> QPropertyAnimation:
    """Slide in da direita."""
    end_pos = widget.pos()
    start_pos = end_pos.__class__(end_pos.x() + offset, end_pos.y())
    
    anim = QPropertyAnimation(widget, b"pos")
    anim.setDuration(duration)
    anim.setStartValue(start_pos)
    anim.setEndValue(end_pos)
    anim.setEasingCurve(QEasingCurve.OutCubic)
    
    anim.start(QPropertyAnimation.DeleteWhenStopped)
    return anim


# =============================================================================
# SCALE ANIMATIONS
# =============================================================================

def pop_in(widget: QWidget, duration: int = 200) -> QPropertyAnimation:
    """Pop/scale in animação."""
    anim = QPropertyAnimation(widget, b"geometry")
    anim.setDuration(duration)
    
    rect = widget.geometry()
    center = rect.center()
    
    # Start smaller
    start_rect = rect.adjusted(20, 20, -20, -20)
    start_rect.moveCenter(center)
    
    anim.setStartValue(start_rect)
    anim.setEndValue(rect)
    anim.setEasingCurve(QEasingCurve.OutBack)
    
    anim.start(QPropertyAnimation.DeleteWhenStopped)
    return anim


# =============================================================================
# SHAKE ANIMATION
# =============================================================================

def shake(widget: QWidget, intensity: int = 10, duration: int = 400):
    """Shake animação (para erros)."""
    original_pos = widget.pos()
    
    anim = QSequentialAnimationGroup(widget)
    
    # 4 shakes
    for i in range(4):
        # Direita
        a1 = QPropertyAnimation(widget, b"pos")
        a1.setDuration(duration // 8)
        a1.setEndValue(original_pos.__class__(original_pos.x() + intensity, original_pos.y()))
        anim.addAnimation(a1)
        
        # Esquerda
        a2 = QPropertyAnimation(widget, b"pos")
        a2.setDuration(duration // 8)
        a2.setEndValue(original_pos.__class__(original_pos.x() - intensity, original_pos.y()))
        anim.addAnimation(a2)
    
    # Volta ao original
    a_final = QPropertyAnimation(widget, b"pos")
    a_final.setDuration(duration // 8)
    a_final.setEndValue(original_pos)
    anim.addAnimation(a_final)
    
    anim.start(QSequentialAnimationGroup.DeleteWhenStopped)
    return anim


# =============================================================================
# PULSE ANIMATION
# =============================================================================

class PulseEffect(QObject):
    """Efeito de pulse contínuo."""
    
    def __init__(self, widget: QWidget, parent=None):
        super().__init__(parent)
        self._widget = widget
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._pulse)
        self._growing = True
        self._scale = 1.0
    
    def start(self, interval: int = 50):
        self._timer.start(interval)
    
    def stop(self):
        self._timer.stop()
        self._widget.setStyleSheet(self._widget.styleSheet())
    
    def _pulse(self):
        if self._growing:
            self._scale += 0.02
            if self._scale >= 1.1:
                self._growing = False
        else:
            self._scale -= 0.02
            if self._scale <= 1.0:
                self._growing = True


# =============================================================================
# SKELETON LOADING
# =============================================================================

class SkeletonLoader(QWidget):
    """Widget placeholder com animação de loading."""
    
    def __init__(self, width: int = 100, height: int = 20, parent=None):
        super().__init__(parent)
        self.setFixedSize(width, height)
        
        self._offset = 0
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._animate)
        self._timer.start(50)
    
    def _animate(self):
        self._offset = (self._offset + 5) % (self.width() * 2)
        self.update()
    
    def paintEvent(self, event):
        from PySide6.QtGui import QPainter, QLinearGradient
        
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Background
        painter.fillRect(self.rect(), QColor("#2D2D44"))
        
        # Shimmer effect
        gradient = QLinearGradient(self._offset - self.width(), 0, self._offset, 0)
        gradient.setColorAt(0, QColor("#2D2D44"))
        gradient.setColorAt(0.5, QColor("#3D3D54"))
        gradient.setColorAt(1, QColor("#2D2D44"))
        
        painter.fillRect(self.rect(), gradient)
    
    def stop(self):
        self._timer.stop()


# =============================================================================
# HELPERS
# =============================================================================

def animate_color_change(widget: QWidget, from_color: str, to_color: str, duration: int = 500):
    """Anima transição de cor de fundo."""
    # Simples: usa stylesheet
    widget.setStyleSheet(f"background-color: {to_color}; transition: background-color {duration}ms;")

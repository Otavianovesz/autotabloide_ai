"""
AutoTabloide AI - Status Bar Widgets
====================================
Widgets industriais para a barra de status.
PASSO 51: RAM, AI Status, Zoom Control.
"""

import psutil
from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QLabel, QProgressBar, 
    QSlider, QToolButton
)
from PySide6.QtCore import Qt, QTimer, Signal, QSize
from PySide6.QtGui import QColor, QPainter, QIcon

from src.qt.styles.theme import set_class, get_status_color, wait_cursor

# ==============================================================================
# RAM USAGE WIDGET
# ==============================================================================

class RamUsageWidget(QWidget):
    """
    Monitora uso de RAM do sistema/processo.
    Feedback visual crítico para evitar OOM em renderizações pesadas.
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        
        # Label
        self.label = QLabel("RAM")
        set_class(self.label, "status-muted")
        layout.addWidget(self.label)
        
        # Progress Bar
        self.bar = QProgressBar()
        self.bar.setFixedSize(60, 8)
        self.bar.setTextVisible(False)
        self.bar.setRange(0, 100)
        layout.addWidget(self.bar)
        
        # Value Label
        self.value = QLabel("0%")
        set_class(self.value, "status-info")
        self.value.setFixedWidth(40)
        layout.addWidget(self.value)
        
        # Timer (2s)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._update_ram)
        self.timer.start(2000)
        
        self._update_ram()

    def _update_ram(self):
        """Atualiza uso de memória."""
        try:
            mem = psutil.virtual_memory()
            percent = mem.percent
            
            self.bar.setValue(int(percent))
            self.value.setText(f"{percent:.0f}%")
            
            # Alerta de memória alta (>80%)
            if percent > 90:
                set_class(self.value, "status-error")
            elif percent > 75:
                set_class(self.value, "status-warning")
            else:
                set_class(self.value, "status-info")
                
        except Exception:
            pass


# ==============================================================================
# AI STATUS WIDGET (SENTINEL)
# ==============================================================================

class AIStatusWidget(QWidget):
    """
    LED indicador do status do Sentinel (IA).
    Status: Offline (Cinza), Idle (Verde), Processing (Azul), Error (Vermelho).
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)
        
        # LED
        self.led = QLabel()
        self.led.setFixedSize(10, 10)
        self.led.setProperty("class", "led-ok")  # Default
        layout.addWidget(self.led)
        
        # Text
        self.text = QLabel("IA: Ociosa")
        set_class(self.text, "status-muted")
        layout.addWidget(self.text)
        
    def set_status(self, status: str, message: str = ""):
        """
        Define status da IA.
        
        Args:
            status: "idle", "processing", "error", "offline"
            message: Texto opcional (ex: "Gerando Imagem...")
        """
        if status == "processing":
            self.led.setProperty("class", "led-warning") # Amarelo/Laranja p/ processamento
            set_class(self.text, "status-info")
            self.text.setText(message or "Processando...")
            
        elif status == "error":
            self.led.setProperty("class", "led-error")
            set_class(self.text, "status-error")
            self.text.setText("Erro IA")
            
        elif status == "offline":
            self.led.setProperty("class", "led-muted") # Precisa definir led-muted no CSS ou usar style direto
            self.led.setStyleSheet("background-color: #606060; border-radius: 5px;")
            set_class(self.text, "status-muted")
            self.text.setText("Offline")
            
        else: # idle
            self.led.setProperty("class", "led-ok")
            set_class(self.text, "status-success")
            self.text.setText("IA Pronta")
            
        # Força update de estilo
        self.led.style().unpolish(self.led)
        self.led.style().polish(self.led)


# ==============================================================================
# ZOOM CONTROL WIDGET
# ==============================================================================

class ZoomControlWidget(QWidget):
    """
    Controle deslizante de zoom para o Atelier.
    """
    
    zoom_changed = Signal(int)  # 10 to 300
    
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        
        # Icon/Label
        lbl = QLabel("Zoom")
        set_class(lbl, "status-muted")
        layout.addWidget(lbl)
        
        # Slider
        self.slider = QSlider(Qt.Horizontal)
        self.slider.setRange(10, 300)
        self.slider.setValue(100)
        self.slider.setFixedWidth(100)
        self.slider.valueChanged.connect(self._on_value_change)
        layout.addWidget(self.slider)
        
        # Value
        self.value_lbl = QLabel("100%")
        set_class(self.value_lbl, "status-info")
        self.value_lbl.setFixedWidth(35)
        layout.addWidget(self.value_lbl)
        
    def _on_value_change(self, value):
        self.value_lbl.setText(f"{value}%")
        self.zoom_changed.emit(value)
        
    def set_zoom(self, value: int):
        self.slider.setValue(value)

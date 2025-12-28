"""
AutoTabloide AI - Splash Screen
===============================
PROTOCOLO DE CONVERGÊNCIA 260 - Fase 6 (Passos 17, 238)
Splash screen com barra de progresso real.
"""

from __future__ import annotations
from typing import Callable, List
import logging

from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QProgressBar,
    QApplication
)
from PySide6.QtGui import QPixmap, QPainter, QColor, QFont

logger = logging.getLogger("Splash")


class SplashScreen(QWidget):
    """
    Splash screen industrial com progresso real.
    
    Features:
    - Barra de progresso real
    - Mensagens de status
    - Boot sequence
    """
    
    boot_completed = Signal()
    
    def __init__(self):
        super().__init__()
        
        self.setWindowFlags(
            Qt.FramelessWindowHint |
            Qt.WindowStaysOnTopHint |
            Qt.SplashScreen
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        self.setFixedSize(500, 300)
        self._center_on_screen()
        
        self._setup_ui()
        
        self._tasks: List[tuple] = []
        self._current_task = 0
    
    def _center_on_screen(self):
        screen = QApplication.primaryScreen().geometry()
        x = (screen.width() - self.width()) // 2
        y = (screen.height() - self.height()) // 2
        self.move(x, y)
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        
        # Logo/Título
        self.title = QLabel("AutoTabloide AI")
        self.title.setAlignment(Qt.AlignCenter)
        self.title.setStyleSheet("""
            font-size: 32px;
            font-weight: bold;
            color: #6C5CE7;
        """)
        layout.addWidget(self.title)
        
        # Subtítulo
        self.subtitle = QLabel("Engine de Publicidade Varejista")
        self.subtitle.setAlignment(Qt.AlignCenter)
        self.subtitle.setStyleSheet("font-size: 14px; color: #888888;")
        layout.addWidget(self.subtitle)
        
        layout.addStretch()
        
        # Status
        self.status = QLabel("Inicializando...")
        self.status.setAlignment(Qt.AlignCenter)
        self.status.setStyleSheet("font-size: 12px; color: #AAAAAA;")
        layout.addWidget(self.status)
        
        # Progress bar
        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.progress.setTextVisible(False)
        self.progress.setStyleSheet("""
            QProgressBar {
                border: none;
                border-radius: 4px;
                background-color: #2D2D44;
                height: 8px;
            }
            QProgressBar::chunk {
                background-color: #6C5CE7;
                border-radius: 4px;
            }
        """)
        layout.addWidget(self.progress)
        
        # Versão
        self.version = QLabel("v2.0.0 Industrial")
        self.version.setAlignment(Qt.AlignCenter)
        self.version.setStyleSheet("font-size: 10px; color: #666666;")
        layout.addWidget(self.version)
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Background com bordas arredondadas
        painter.setBrush(QColor("#1A1A2E"))
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(self.rect(), 15, 15)
    
    def add_task(self, name: str, task: Callable):
        """Adiciona tarefa ao boot."""
        self._tasks.append((name, task))
    
    def start_boot(self):
        """Inicia sequência de boot."""
        if not self._tasks:
            self.boot_completed.emit()
            return
        
        self._run_next_task()
    
    def _run_next_task(self):
        """Executa próxima tarefa."""
        if self._current_task >= len(self._tasks):
            self.status.setText("Pronto!")
            self.progress.setValue(100)
            QTimer.singleShot(500, self.boot_completed.emit)
            return
        
        name, task = self._tasks[self._current_task]
        
        # Atualiza UI
        self.status.setText(name)
        progress = int((self._current_task / len(self._tasks)) * 100)
        self.progress.setValue(progress)
        
        QApplication.processEvents()
        
        # Executa tarefa
        try:
            task()
        except Exception as e:
            logger.error(f"Boot task failed: {name} - {e}")
        
        self._current_task += 1
        
        # Próxima tarefa
        QTimer.singleShot(100, self._run_next_task)


def create_splash_screen() -> SplashScreen:
    """Cria splash screen."""
    return SplashScreen()


def run_with_splash(
    tasks: List[tuple],
    on_complete: Callable
):
    """
    Executa boot com splash.
    
    tasks: Lista de (nome, callable)
    on_complete: Callback quando terminar
    """
    splash = SplashScreen()
    
    for name, task in tasks:
        splash.add_task(name, task)
    
    splash.boot_completed.connect(lambda: _finish_splash(splash, on_complete))
    
    splash.show()
    splash.start_boot()
    
    return splash


def _finish_splash(splash: SplashScreen, on_complete: Callable):
    """Finaliza splash e chama callback."""
    splash.close()
    on_complete()

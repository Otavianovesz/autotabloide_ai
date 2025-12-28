"""
AutoTabloide AI - Logging Dock
==============================
PROTOCOLO DE RETIFICAÇÃO NÍVEL 0 - Fase 1 (Passo 5)
Dock de logging em tempo real com QTextEdit.
"""

from __future__ import annotations
from typing import Optional
import logging
from logging.handlers import QueueHandler
from queue import Queue
from datetime import datetime

from PySide6.QtCore import Qt, Signal, QObject, QTimer
from PySide6.QtWidgets import (
    QDockWidget, QWidget, QVBoxLayout, QHBoxLayout,
    QTextEdit, QPushButton, QComboBox, QLabel
)
from PySide6.QtGui import QTextCursor, QColor


# =============================================================================
# LOG HANDLER FOR QT
# =============================================================================

class QtLogHandler(logging.Handler):
    """Handler que emite logs para Qt via signal."""
    
    def __init__(self, callback):
        super().__init__()
        self._callback = callback
        self.setFormatter(logging.Formatter(
            '%(asctime)s [%(levelname)s] %(name)s: %(message)s',
            datefmt='%H:%M:%S'
        ))
    
    def emit(self, record):
        msg = self.format(record)
        self._callback(record.levelno, msg)


# =============================================================================
# LOG DOCK WIDGET
# =============================================================================

class LogDockWidget(QDockWidget):
    """
    Dock de logging em tempo real.
    
    Features:
    - Cores por nível (DEBUG, INFO, WARNING, ERROR)
    - Filtro por nível
    - Limpar e exportar
    - Auto-scroll
    """
    
    def __init__(self, parent=None):
        super().__init__("📋 Console", parent)
        self.setObjectName("LogDock")
        self.setAllowedAreas(Qt.BottomDockWidgetArea | Qt.RightDockWidgetArea)
        
        self._max_lines = 1000
        self._min_level = logging.DEBUG
        self._auto_scroll = True
        
        self._setup_ui()
        self._setup_handler()
    
    def _setup_ui(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)
        
        # Toolbar
        toolbar = QHBoxLayout()
        
        toolbar.addWidget(QLabel("Nível:"))
        self.level_combo = QComboBox()
        self.level_combo.addItems(["DEBUG", "INFO", "WARNING", "ERROR"])
        self.level_combo.setCurrentIndex(1)  # INFO
        self.level_combo.currentIndexChanged.connect(self._on_level_changed)
        toolbar.addWidget(self.level_combo)
        
        toolbar.addStretch()
        
        self.btn_clear = QPushButton("🗑️ Limpar")
        self.btn_clear.clicked.connect(self._clear_log)
        toolbar.addWidget(self.btn_clear)
        
        self.btn_export = QPushButton("💾 Exportar")
        self.btn_export.clicked.connect(self._export_log)
        toolbar.addWidget(self.btn_export)
        
        layout.addLayout(toolbar)
        
        # Log area
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setStyleSheet("""
            QTextEdit {
                background-color: #0A0A14;
                color: #B0B0B0;
                font-family: Consolas, 'Courier New', monospace;
                font-size: 11px;
                border: none;
            }
        """)
        layout.addWidget(self.log_text)
        
        self.setWidget(widget)
    
    def _setup_handler(self):
        """Instala handler nos loggers."""
        self._handler = QtLogHandler(self._append_log)
        self._handler.setLevel(logging.DEBUG)
        
        # Adiciona ao root logger
        logging.getLogger().addHandler(self._handler)
    
    def _append_log(self, level: int, message: str):
        """Adiciona linha ao log."""
        if level < self._min_level:
            return
        
        # Define cor
        color = self._get_level_color(level)
        
        # Adiciona texto
        cursor = self.log_text.textCursor()
        cursor.movePosition(QTextCursor.End)
        self.log_text.setTextCursor(cursor)
        
        # Formata com cor
        html = f'<span style="color:{color}">{message}</span><br>'
        cursor.insertHtml(html)
        
        # Limita linhas
        doc = self.log_text.document()
        if doc.lineCount() > self._max_lines:
            cursor.movePosition(QTextCursor.Start)
            cursor.movePosition(QTextCursor.Down, QTextCursor.KeepAnchor, 100)
            cursor.removeSelectedText()
        
        # Auto-scroll
        if self._auto_scroll:
            scrollbar = self.log_text.verticalScrollBar()
            scrollbar.setValue(scrollbar.maximum())
    
    def _get_level_color(self, level: int) -> str:
        """Retorna cor para nível de log."""
        if level >= logging.ERROR:
            return "#E74C3C"  # Vermelho
        elif level >= logging.WARNING:
            return "#F39C12"  # Laranja
        elif level >= logging.INFO:
            return "#2ECC71"  # Verde
        else:
            return "#7F8C8D"  # Cinza
    
    def _on_level_changed(self, index: int):
        """Muda nível mínimo."""
        levels = [logging.DEBUG, logging.INFO, logging.WARNING, logging.ERROR]
        self._min_level = levels[index]
    
    def _clear_log(self):
        """Limpa log."""
        self.log_text.clear()
    
    def _export_log(self):
        """Exporta log para arquivo."""
        from PySide6.QtWidgets import QFileDialog
        
        path, _ = QFileDialog.getSaveFileName(
            self, "Exportar Log",
            f"autotabloide_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
            "Text Files (*.txt)"
        )
        
        if path:
            with open(path, "w", encoding="utf-8") as f:
                f.write(self.log_text.toPlainText())
    
    def log_info(self, message: str):
        """Log direto de info."""
        self._append_log(logging.INFO, f"[INFO] {message}")
    
    def log_error(self, message: str):
        """Log direto de erro."""
        self._append_log(logging.ERROR, f"[ERROR] {message}")


# =============================================================================
# HELPER
# =============================================================================

def create_log_dock(parent=None) -> LogDockWidget:
    """Cria dock de logging."""
    return LogDockWidget(parent)

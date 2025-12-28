"""
AutoTabloide AI - Tooltips and Help System
==========================================
PROTOCOLO DE RETIFICAÇÃO NÍVEL 0 - Fase 6 (Passos 200-205)
Tooltips ricos e sistema de ajuda.
"""

from __future__ import annotations
from typing import Dict, List, Optional
import logging

from PySide6.QtCore import Qt, Signal, QTimer, QPoint
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QDialog, QScrollArea, QGridLayout, QPushButton
)
from PySide6.QtGui import QKeySequence

logger = logging.getLogger("Help")


# =============================================================================
# KEYBOARD SHORTCUTS
# =============================================================================

SHORTCUTS = {
    "Geral": [
        ("Ctrl+S", "Salvar projeto"),
        ("Ctrl+O", "Abrir projeto"),
        ("Ctrl+N", "Novo projeto"),
        ("Ctrl+Z", "Desfazer"),
        ("Ctrl+Shift+Z", "Refazer"),
        ("F1", "Ajuda"),
        ("F5", "Atualizar"),
        ("Escape", "Fechar modal"),
    ],
    "Navegação": [
        ("Ctrl+1", "Dashboard"),
        ("Ctrl+2", "Estoque"),
        ("Ctrl+3", "Ateliê"),
        ("Ctrl+4", "Fábrica"),
        ("Ctrl+5", "Configurações"),
        ("Ctrl+6", "Hospital de Imagens"),
    ],
    "Ateliê": [
        ("Ctrl+A", "Selecionar todos"),
        ("Delete", "Limpar slot"),
        ("Ctrl+D", "Duplicar"),
        ("Ctrl+G", "Agrupar"),
        ("Ctrl+Click", "Multi-seleção"),
        ("+/-", "Zoom in/out"),
        ("Ctrl+0", "Zoom 100%"),
        ("Ctrl+1", "Zoom to fit"),
    ],
    "Estoque": [
        ("Enter", "Editar produto"),
        ("Space", "Drag para Ateliê"),
        ("Ctrl+F", "Buscar"),
        ("Ctrl+I", "Importar Excel"),
    ],
}


# =============================================================================
# RICH TOOLTIP
# =============================================================================

class RichTooltip(QFrame):
    """
    Tooltip rico com título, descrição e atalho.
    Aparece com delay e desaparece automaticamente.
    """
    
    _instance: Optional['RichTooltip'] = None
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(
            Qt.ToolTip | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint
        )
        self.setStyleSheet("""
            RichTooltip {
                background-color: #1A1A2E;
                border: 1px solid #6C5CE7;
                border-radius: 6px;
                padding: 8px;
            }
            QLabel {
                color: #FFFFFF;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(4)
        
        # Title
        self.title_label = QLabel()
        self.title_label.setStyleSheet("font-weight: bold; font-size: 12px;")
        layout.addWidget(self.title_label)
        
        # Description
        self.desc_label = QLabel()
        self.desc_label.setStyleSheet("color: #B0B0B0; font-size: 11px;")
        self.desc_label.setWordWrap(True)
        layout.addWidget(self.desc_label)
        
        # Shortcut
        self.shortcut_label = QLabel()
        self.shortcut_label.setStyleSheet("color: #6C5CE7; font-size: 10px;")
        layout.addWidget(self.shortcut_label)
        
        # Auto-hide timer
        self._hide_timer = QTimer(self)
        self._hide_timer.timeout.connect(self.hide)
    
    @classmethod
    def show_tooltip(cls, pos: QPoint, title: str, description: str = "", shortcut: str = ""):
        """Mostra tooltip na posição especificada."""
        if cls._instance is None:
            cls._instance = cls()
        
        tip = cls._instance
        tip.title_label.setText(title)
        tip.desc_label.setText(description)
        tip.desc_label.setVisible(bool(description))
        
        if shortcut:
            tip.shortcut_label.setText(f"Atalho: {shortcut}")
            tip.shortcut_label.setVisible(True)
        else:
            tip.shortcut_label.setVisible(False)
        
        tip.adjustSize()
        tip.move(pos)
        tip.show()
        
        # Auto-hide após 3 segundos
        tip._hide_timer.start(3000)
    
    @classmethod
    def hide_tooltip(cls):
        """Esconde tooltip."""
        if cls._instance:
            cls._instance.hide()


# =============================================================================
# SHORTCUTS HELP DIALOG
# =============================================================================

class ShortcutsDialog(QDialog):
    """
    Diálogo mostrando todos os atalhos de teclado.
    Acionado por F1.
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("AutoTabloide AI - Atalhos de Teclado")
        self.setMinimumSize(600, 500)
        self.setStyleSheet("""
            QDialog {
                background-color: #0F0F1A;
            }
            QLabel {
                color: #FFFFFF;
            }
        """)
        
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        
        # Header
        header = QLabel("⌨️ Atalhos de Teclado")
        header.setStyleSheet("font-size: 20px; font-weight: bold;")
        layout.addWidget(header)
        
        # Scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; }")
        
        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setSpacing(24)
        
        for category, shortcuts in SHORTCUTS.items():
            group = self._create_group(category, shortcuts)
            content_layout.addWidget(group)
        
        content_layout.addStretch()
        scroll.setWidget(content)
        layout.addWidget(scroll)
        
        # Close button
        close_btn = QPushButton("Fechar")
        close_btn.clicked.connect(self.accept)
        close_btn.setMinimumWidth(100)
        layout.addWidget(close_btn, alignment=Qt.AlignRight)
    
    def _create_group(self, title: str, shortcuts: List[tuple]) -> QFrame:
        """Cria grupo de atalhos."""
        frame = QFrame()
        frame.setStyleSheet("""
            QFrame {
                background-color: #1A1A2E;
                border-radius: 8px;
                padding: 12px;
            }
        """)
        
        layout = QVBoxLayout(frame)
        
        # Title
        title_label = QLabel(title)
        title_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #6C5CE7;")
        layout.addWidget(title_label)
        
        # Grid of shortcuts
        grid = QGridLayout()
        grid.setSpacing(8)
        
        for i, (key, desc) in enumerate(shortcuts):
            row = i // 2
            col = (i % 2) * 2
            
            key_label = QLabel(key)
            key_label.setStyleSheet("""
                background-color: #2D2D44;
                padding: 4px 8px;
                border-radius: 4px;
                font-family: Consolas, monospace;
            """)
            key_label.setFixedWidth(120)
            grid.addWidget(key_label, row, col)
            
            desc_label = QLabel(desc)
            desc_label.setStyleSheet("color: #B0B0B0;")
            grid.addWidget(desc_label, row, col + 1)
        
        layout.addLayout(grid)
        
        return frame


# =============================================================================
# ONBOARDING WELCOME DIALOG
# =============================================================================

class WelcomeDialog(QDialog):
    """
    Diálogo de boas-vindas para primeira execução.
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Bem-vindo ao AutoTabloide AI")
        self.setMinimumSize(500, 400)
        self.setStyleSheet("""
            QDialog {
                background-color: #0F0F1A;
            }
        """)
        
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(40, 40, 40, 40)
        
        # Logo/Title
        title = QLabel("🎨 AutoTabloide AI")
        title.setStyleSheet("font-size: 28px; font-weight: bold; color: #6C5CE7;")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        subtitle = QLabel("Criação profissional de tabloides promocionais")
        subtitle.setStyleSheet("font-size: 14px; color: #808080;")
        subtitle.setAlignment(Qt.AlignCenter)
        layout.addWidget(subtitle)
        
        layout.addSpacing(20)
        
        # Quick tips
        tips = [
            ("📦", "Importe produtos", "Comece importando sua planilha Excel ou adicionando produtos manualmente"),
            ("🎨", "Escolha um template", "Selecione um layout SVG ou crie slots automaticamente"),
            ("🖱️", "Arraste e solte", "Arraste produtos do Estoque para os slots do Ateliê"),
            ("📄", "Exporte PDF", "Exporte PDF em alta qualidade com perfil CMYK"),
        ]
        
        for icon, title, desc in tips:
            tip_frame = QFrame()
            tip_frame.setStyleSheet("""
                QFrame {
                    background-color: #1A1A2E;
                    border-radius: 8px;
                    padding: 12px;
                }
            """)
            
            tip_layout = QHBoxLayout(tip_frame)
            
            icon_label = QLabel(icon)
            icon_label.setStyleSheet("font-size: 24px;")
            tip_layout.addWidget(icon_label)
            
            text_layout = QVBoxLayout()
            title_label = QLabel(title)
            title_label.setStyleSheet("font-weight: bold; color: #FFFFFF;")
            text_layout.addWidget(title_label)
            
            desc_label = QLabel(desc)
            desc_label.setStyleSheet("color: #808080; font-size: 11px;")
            text_layout.addWidget(desc_label)
            
            tip_layout.addLayout(text_layout)
            tip_layout.addStretch()
            
            layout.addWidget(tip_frame)
        
        layout.addStretch()
        
        # Button
        start_btn = QPushButton("Começar")
        start_btn.setStyleSheet("""
            QPushButton {
                background-color: #6C5CE7;
                color: white;
                padding: 12px 32px;
                border-radius: 6px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #5B4DC7;
            }
        """)
        start_btn.clicked.connect(self.accept)
        layout.addWidget(start_btn, alignment=Qt.AlignCenter)


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def show_shortcuts_dialog(parent=None):
    """Mostra diálogo de atalhos."""
    dialog = ShortcutsDialog(parent)
    dialog.exec()


def show_welcome_dialog(parent=None) -> bool:
    """Mostra diálogo de boas-vindas. Retorna True se aceito."""
    dialog = WelcomeDialog(parent)
    return dialog.exec() == QDialog.Accepted


def show_rich_tooltip(widget: QWidget, title: str, description: str = "", shortcut: str = ""):
    """Mostra tooltip rico abaixo do widget."""
    pos = widget.mapToGlobal(widget.rect().bottomLeft())
    pos.setY(pos.y() + 5)
    RichTooltip.show_tooltip(pos, title, description, shortcut)

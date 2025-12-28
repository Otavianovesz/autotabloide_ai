"""
AutoTabloide AI - About Dialog
==============================
PROTOCOLO DE RETIFICAÇÃO NÍVEL 0 - Fase 6 (Passo 201)
Diálogo About com informações do sistema.
"""

from __future__ import annotations
from pathlib import Path
import platform
import sys
import logging

from PySide6.QtCore import Qt, QSysInfo
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFrame, QGridLayout
)
from PySide6.QtGui import QPixmap, QPainter, QColor

logger = logging.getLogger("About")


class AboutDialog(QDialog):
    """
    Diálogo About com informações do sistema.
    """
    
    VERSION = "2.0.0"
    BUILD_DATE = "2024-12-27"
    
    def __init__(self, boot_report=None, parent=None):
        super().__init__(parent)
        self.boot_report = boot_report
        self.setWindowTitle("Sobre AutoTabloide AI")
        self.setMinimumSize(500, 450)
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
        layout.setContentsMargins(30, 30, 30, 30)
        
        # Logo/Title
        title = QLabel("🎨 AutoTabloide AI")
        title.setStyleSheet("font-size: 28px; font-weight: bold; color: #6C5CE7;")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        version = QLabel(f"Versão {self.VERSION} ({self.BUILD_DATE})")
        version.setStyleSheet("font-size: 12px; color: #808080;")
        version.setAlignment(Qt.AlignCenter)
        layout.addWidget(version)
        
        subtitle = QLabel("Sistema Profissional de Tabloides Promocionais")
        subtitle.setStyleSheet("font-size: 14px; color: #B0B0B0;")
        subtitle.setAlignment(Qt.AlignCenter)
        layout.addWidget(subtitle)
        
        layout.addSpacing(10)
        
        # System info
        info_frame = QFrame()
        info_frame.setStyleSheet("""
            QFrame {
                background-color: #1A1A2E;
                border-radius: 8px;
                padding: 16px;
            }
        """)
        
        info_layout = QGridLayout(info_frame)
        info_layout.setSpacing(8)
        
        # Informações do sistema
        infos = [
            ("Sistema:", f"{platform.system()} {platform.release()}"),
            ("Python:", f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"),
            ("Qt:", QSysInfo.buildAbi() if hasattr(QSysInfo, 'buildAbi') else "6.x"),
            ("Arquitetura:", platform.machine()),
        ]
        
        if self.boot_report:
            infos.extend([
                ("GPU:", "Detectada" if self.boot_report.gpu_available else "Não"),
                ("Banco de dados:", "Online" if self.boot_report.database_ok else "Offline"),
                ("Fontes:", f"{len(self.boot_report.fonts_loaded)} carregadas"),
            ])
        
        for i, (label, value) in enumerate(infos):
            lbl = QLabel(label)
            lbl.setStyleSheet("color: #6C5CE7; font-weight: bold;")
            info_layout.addWidget(lbl, i, 0)
            
            val = QLabel(value)
            val.setStyleSheet("color: #B0B0B0;")
            info_layout.addWidget(val, i, 1)
        
        layout.addWidget(info_frame)
        
        layout.addStretch()
        
        # Credits
        credits = QLabel("Desenvolvido com 💜 para varejo brasileiro")
        credits.setStyleSheet("color: #404060; font-size: 11px;")
        credits.setAlignment(Qt.AlignCenter)
        layout.addWidget(credits)
        
        # Close button
        close_btn = QPushButton("Fechar")
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: #6C5CE7;
                color: white;
                padding: 10px 30px;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: #5B4DC7;
            }
        """)
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn, alignment=Qt.AlignCenter)


def show_about_dialog(parent=None, boot_report=None):
    """Mostra diálogo About."""
    dialog = AboutDialog(boot_report, parent)
    dialog.exec()

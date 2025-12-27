"""
AutoTabloide AI - Qt Edition
=============================
Aplicação principal usando PySide6 (Qt for Python).
Implementa robustez industrial com QGraphicsView para Atelier.

Versão: 2.0.0 (Qt Migration)
"""

import sys
import os
from pathlib import Path

# === HIGH DPI SCALING (OBRIGATÓRIO para monitores 4K) ===
os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "1"
os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"

# Adiciona src ao path para imports corretos
sys.path.insert(0, str(Path(__file__).parent))

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt

from src.qt.theme import apply_theme
from src.qt.main_window import MainWindow


def main():
    """Entry point da aplicação Qt."""
    # Cria aplicação
    app = QApplication(sys.argv)
    
    # Aplica Dark Theme
    apply_theme(app)
    
    # Configura nome da aplicação
    app.setApplicationName("AutoTabloide AI")
    app.setApplicationVersion("2.0.0")
    app.setOrganizationName("AutoTabloide")
    
    # Cria janela principal
    # TODO: Injetar container de serviços quando integrar backend
    window = MainWindow(container=None)
    window.show()
    
    # Loop de eventos
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())

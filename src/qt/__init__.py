"""
AutoTabloide AI - Qt Module
============================
Componentes PySide6 para interface gráfica.
"""

from .main_window import MainWindow
from .styles.theme import DARK_THEME_QSS, apply_theme

# Widgets
from .widgets import (
    DashboardWidget, EstoqueWidget, AtelierWidget,
    FactoryWidget, CofreWidget, SettingsWidget
)

# Dialogs
from .dialogs import ImageHandlerDialog

# Workers
from .workers import (
    SentinelWorker, RenderWorker, ImportWorker, ImageProcessWorker
)

__all__ = [
    "MainWindow", "DARK_THEME_QSS", "apply_theme",
    "DashboardWidget", "EstoqueWidget", "AtelierWidget",
    "FactoryWidget", "CofreWidget", "SettingsWidget",
    "ImageHandlerDialog",
    "SentinelWorker", "RenderWorker", "ImportWorker", "ImageProcessWorker"
]

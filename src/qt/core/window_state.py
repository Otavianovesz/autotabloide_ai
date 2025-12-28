"""
AutoTabloide AI - Window State Manager
======================================
PROTOCOLO DE RETIFICAÇÃO NÍVEL 0 - Fase 6 (Passo 212)
Persistência de estado de janelas e docks.
"""

from __future__ import annotations
from pathlib import Path
from typing import Dict, Optional
import logging
import json

from PySide6.QtCore import QSettings, QByteArray
from PySide6.QtWidgets import QMainWindow

logger = logging.getLogger("WindowState")


class WindowStateManager:
    """
    Gerencia persistência de estado de janelas.
    
    Salva/restaura:
    - Posição e tamanho
    - Estado maximizado
    - Posição de docks
    - Splitters
    """
    
    def __init__(self, app_name: str = "AutoTabloideAI"):
        self._settings = QSettings(app_name, app_name)
    
    def save_window_state(self, window: QMainWindow, name: str = "main"):
        """Salva estado da janela."""
        self._settings.setValue(f"{name}/geometry", window.saveGeometry())
        self._settings.setValue(f"{name}/state", window.saveState())
        self._settings.setValue(f"{name}/maximized", window.isMaximized())
        
        logger.debug(f"Estado salvo: {name}")
    
    def restore_window_state(self, window: QMainWindow, name: str = "main") -> bool:
        """Restaura estado da janela."""
        try:
            geometry = self._settings.value(f"{name}/geometry")
            state = self._settings.value(f"{name}/state")
            maximized = self._settings.value(f"{name}/maximized", False)
            
            if geometry:
                window.restoreGeometry(geometry)
            
            if state:
                window.restoreState(state)
            
            if maximized == "true" or maximized is True:
                window.showMaximized()
            
            logger.debug(f"Estado restaurado: {name}")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao restaurar estado: {e}")
            return False
    
    def save_splitter_state(self, sizes: list, name: str):
        """Salva estado de splitter."""
        self._settings.setValue(f"splitter/{name}", sizes)
    
    def restore_splitter_state(self, name: str) -> Optional[list]:
        """Restaura estado de splitter."""
        return self._settings.value(f"splitter/{name}")
    
    def save_value(self, key: str, value):
        """Salva valor genérico."""
        self._settings.setValue(key, value)
    
    def get_value(self, key: str, default=None):
        """Obtém valor genérico."""
        return self._settings.value(key, default)
    
    def clear(self):
        """Limpa todas as configurações."""
        self._settings.clear()


# =============================================================================
# SINGLETON
# =============================================================================

_instance: Optional[WindowStateManager] = None


def get_window_state_manager() -> WindowStateManager:
    """Acesso global ao gerenciador."""
    global _instance
    if _instance is None:
        _instance = WindowStateManager()
    return _instance


def save_window_state(window: QMainWindow, name: str = "main"):
    """Helper para salvar estado."""
    get_window_state_manager().save_window_state(window, name)


def restore_window_state(window: QMainWindow, name: str = "main") -> bool:
    """Helper para restaurar estado."""
    return get_window_state_manager().restore_window_state(window, name)

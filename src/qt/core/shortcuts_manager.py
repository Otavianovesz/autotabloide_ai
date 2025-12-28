"""
AutoTabloide AI - Keyboard Shortcuts Manager
=============================================
PROTOCOLO DE CONVERGÊNCIA 260 - Fase 6 (Passo 28, 241)
Gerenciador centralizado de atalhos de teclado.
"""

from __future__ import annotations
from typing import Dict, Callable, Optional
from dataclasses import dataclass
import logging

from PySide6.QtCore import Qt, QObject, Signal
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QShortcut
from PySide6.QtGui import QKeySequence

logger = logging.getLogger("Shortcuts")


@dataclass
class ShortcutDef:
    """Definição de atalho."""
    key: str
    description: str
    callback: Optional[Callable] = None
    category: str = "Geral"


class ShortcutsManager(QObject):
    """
    Gerenciador centralizado de atalhos.
    
    Features:
    - Registro de atalhos globais
    - Categorização para help dialog
    - Hot-reload de atalhos
    """
    
    shortcut_triggered = Signal(str)  # key
    
    _instance: Optional['ShortcutsManager'] = None
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._shortcuts: Dict[str, QShortcut] = {}
        self._definitions: Dict[str, ShortcutDef] = {}
    
    @classmethod
    def instance(cls, parent=None) -> 'ShortcutsManager':
        if cls._instance is None:
            cls._instance = cls(parent)
        return cls._instance
    
    def register(
        self,
        key: str,
        callback: Callable,
        description: str = "",
        category: str = "Geral",
        context: Qt.ShortcutContext = Qt.ApplicationShortcut
    ):
        """Registra atalho."""
        parent = self.parent() or QApplication.instance()
        
        shortcut = QShortcut(QKeySequence(key), parent)
        shortcut.setContext(context)
        shortcut.activated.connect(callback)
        shortcut.activated.connect(lambda: self.shortcut_triggered.emit(key))
        
        self._shortcuts[key] = shortcut
        self._definitions[key] = ShortcutDef(
            key=key,
            description=description,
            callback=callback,
            category=category
        )
        
        logger.debug(f"[Shortcuts] Registered: {key}")
    
    def unregister(self, key: str):
        """Remove atalho."""
        if key in self._shortcuts:
            self._shortcuts[key].deleteLater()
            del self._shortcuts[key]
            del self._definitions[key]
    
    def get_all(self) -> Dict[str, ShortcutDef]:
        """Retorna todos os atalhos."""
        return dict(self._definitions)
    
    def get_by_category(self) -> Dict[str, list]:
        """Retorna atalhos agrupados por categoria."""
        categories = {}
        
        for key, defn in self._definitions.items():
            if defn.category not in categories:
                categories[defn.category] = []
            categories[defn.category].append(defn)
        
        return categories
    
    def register_defaults(self, main_window):
        """Registra atalhos padrão."""
        # Arquivo
        self.register("Ctrl+N", lambda: None, "Novo Projeto", "Arquivo")
        self.register("Ctrl+O", lambda: None, "Abrir Projeto", "Arquivo")
        self.register("Ctrl+S", lambda: None, "Salvar", "Arquivo")
        self.register("Ctrl+Shift+S", lambda: None, "Salvar Como", "Arquivo")
        self.register("Ctrl+Q", lambda: main_window.close(), "Sair", "Arquivo")
        
        # Edição
        self.register("Ctrl+Z", lambda: None, "Desfazer", "Edição")
        self.register("Ctrl+Y", lambda: None, "Refazer", "Edição")
        self.register("Ctrl+C", lambda: None, "Copiar", "Edição")
        self.register("Ctrl+V", lambda: None, "Colar", "Edição")
        self.register("Delete", lambda: None, "Excluir", "Edição")
        
        # Visualização
        self.register("Ctrl+0", lambda: None, "Ajustar à Tela", "Visualização")
        self.register("Ctrl+1", lambda: None, "Zoom 100%", "Visualização")
        self.register("Ctrl++", lambda: None, "Zoom In", "Visualização")
        self.register("Ctrl+-", lambda: None, "Zoom Out", "Visualização")
        
        # Ajuda
        self.register("F1", lambda: None, "Ajuda", "Ajuda")
        self.register("Ctrl+,", lambda: None, "Preferências", "Ajuda")
        
        logger.info("[Shortcuts] Default shortcuts registered")


# =============================================================================
# HELPER
# =============================================================================

def get_shortcuts_manager() -> ShortcutsManager:
    return ShortcutsManager.instance()


def register_shortcut(key: str, callback: Callable, description: str = ""):
    """Helper para registrar atalho."""
    get_shortcuts_manager().register(key, callback, description)

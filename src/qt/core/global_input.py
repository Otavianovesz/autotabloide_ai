"""
AutoTabloide AI - Global Keyboard Filter & Signals
===================================================
PROTOCOLO DE RETIFICAÇÃO NÍVEL 0 - Fase 1 (Passos 14, 27)
Atalhos globais e sinais para comunicação entre componentes.
"""

from __future__ import annotations
from typing import Dict, Callable, Optional
import logging

from PySide6.QtCore import Qt, QObject, Signal, QEvent
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QKeyEvent, QShortcut, QKeySequence

logger = logging.getLogger("GlobalInput")


# =============================================================================
# GLOBAL KEY FILTER (Passo 14)
# =============================================================================

class GlobalKeyFilter(QObject):
    """
    Filtro global de teclas para atalhos em qualquer lugar da janela.
    
    Atalhos:
    - Ctrl+S: Salvar
    - Ctrl+Z: Desfazer
    - Ctrl+Shift+Z: Refazer
    - Ctrl+1-6: Navegar entre abas
    - Escape: Fechar modal
    - F1: Ajuda
    - F5: Atualizar
    """
    
    # Sinais emitidos quando atalhos são pressionados
    save_requested = Signal()
    undo_requested = Signal()
    redo_requested = Signal()
    help_requested = Signal()
    refresh_requested = Signal()
    escape_pressed = Signal()
    navigate_requested = Signal(int)  # tab index
    
    _instance: Optional['GlobalKeyFilter'] = None
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Mapeamento de atalhos customizados
        self._custom_handlers: Dict[str, Callable] = {}
        
        # Estado atual
        self._enabled = True
        self._current_view = "dashboard"
    
    @classmethod
    def instance(cls) -> 'GlobalKeyFilter':
        """Singleton pattern."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    @classmethod
    def install(cls, app: QApplication) -> 'GlobalKeyFilter':
        """Instala o filtro globalmente."""
        inst = cls.instance()
        app.installEventFilter(inst)
        logger.info("[KeyFilter] Instalado globalmente")
        return inst
    
    def eventFilter(self, obj: QObject, event: QEvent) -> bool:
        """Intercepta eventos de teclado."""
        if not self._enabled:
            return False
        
        if event.type() != QEvent.KeyPress:
            return False
        
        key_event = event
        key = key_event.key()
        modifiers = key_event.modifiers()
        
        # Ctrl+S - Salvar
        if key == Qt.Key_S and modifiers == Qt.ControlModifier:
            self.save_requested.emit()
            return True
        
        # Ctrl+Z - Undo
        if key == Qt.Key_Z and modifiers == Qt.ControlModifier:
            self.undo_requested.emit()
            return True
        
        # Ctrl+Shift+Z ou Ctrl+Y - Redo
        if (key == Qt.Key_Z and modifiers == (Qt.ControlModifier | Qt.ShiftModifier)) or \
           (key == Qt.Key_Y and modifiers == Qt.ControlModifier):
            self.redo_requested.emit()
            return True
        
        # Escape
        if key == Qt.Key_Escape and modifiers == Qt.NoModifier:
            self.escape_pressed.emit()
            return True
        
        # F1 - Ajuda
        if key == Qt.Key_F1:
            self.help_requested.emit()
            return True
        
        # F5 - Refresh
        if key == Qt.Key_F5:
            self.refresh_requested.emit()
            return True
        
        # Ctrl+1 a Ctrl+6 - Navegação
        if modifiers == Qt.ControlModifier:
            if Qt.Key_1 <= key <= Qt.Key_6:
                index = key - Qt.Key_1  # 0-5
                self.navigate_requested.emit(index)
                return True
        
        # Verifica handlers customizados
        key_combo = self._get_key_combo(key, modifiers)
        if key_combo in self._custom_handlers:
            self._custom_handlers[key_combo]()
            return True
        
        return False
    
    def _get_key_combo(self, key: int, modifiers) -> str:
        """Converte key+modifiers para string."""
        parts = []
        if modifiers & Qt.ControlModifier:
            parts.append("Ctrl")
        if modifiers & Qt.ShiftModifier:
            parts.append("Shift")
        if modifiers & Qt.AltModifier:
            parts.append("Alt")
        
        key_str = QKeySequence(key).toString()
        parts.append(key_str)
        
        return "+".join(parts)
    
    def register_shortcut(self, key_combo: str, handler: Callable):
        """Registra atalho customizado."""
        self._custom_handlers[key_combo] = handler
    
    def unregister_shortcut(self, key_combo: str):
        """Remove atalho customizado."""
        self._custom_handlers.pop(key_combo, None)
    
    def set_enabled(self, enabled: bool):
        """Habilita/desabilita o filtro."""
        self._enabled = enabled
    
    def set_current_view(self, view_name: str):
        """Define view atual (para atalhos contextuais)."""
        self._current_view = view_name


# =============================================================================
# GLOBAL SIGNALS (Passo 27)
# =============================================================================

class GlobalSignals(QObject):
    """
    Sinais globais para comunicação entre componentes desacoplados.
    
    Usado para:
    - Notificar atualização de produto (sincroniza Estoque ↔ Ateliê)
    - Notificar conclusão de renderização
    - Broadcast de status (Sentinel, DB, etc)
    """
    
    # Produto
    product_created = Signal(dict)
    product_updated = Signal(int, dict)  # id, data
    product_deleted = Signal(int)
    
    # Projeto
    project_saved = Signal(str)   # path
    project_loaded = Signal(str)  # path
    project_closed = Signal()
    
    # Renderização
    rendering_started = Signal(str)  # job_id
    rendering_progress = Signal(str, int)  # job_id, percent
    rendering_finished = Signal(str, bool, str)  # job_id, success, path
    
    # Serviços
    sentinel_status_changed = Signal(str)  # online/offline/busy
    database_status_changed = Signal(str)  # ok/error
    network_status_changed = Signal(bool)  # online/offline
    
    # UI
    theme_changed = Signal(str)  # theme name
    view_changed = Signal(str)   # view name
    
    # Notificações
    notification = Signal(str, str, str)  # type (info/warning/error), title, message
    
    _instance: Optional['GlobalSignals'] = None
    
    @classmethod
    def instance(cls) -> 'GlobalSignals':
        """Singleton pattern."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_key_filter() -> GlobalKeyFilter:
    """Acesso global ao filtro de teclado."""
    return GlobalKeyFilter.instance()


def get_signals() -> GlobalSignals:
    """Acesso global aos sinais."""
    return GlobalSignals.instance()


def emit_notification(ntype: str, title: str, message: str):
    """Emite notificação global."""
    get_signals().notification.emit(ntype, title, message)


def emit_product_update(product_id: int, data: dict):
    """Emite atualização de produto."""
    get_signals().product_updated.emit(product_id, data)

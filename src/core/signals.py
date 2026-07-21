"""
AutoTabloide AI - Signal Bus
============================
Phase 0.2: Architectural Decision (Battleship Order)

Centraliza todos os eventos de aplicação.
Widgets se inscrevem aqui. Serviços publicam aqui.
Elimina o "spaghetti de sinais".
"""

from PySide6.QtCore import QObject, Signal
from typing import Optional, Dict, Any

class SignalBus(QObject):
    """
    Barramento Global de Sinais.
    Singleton thread-safe (QObject é reentrante, mas cuidado com threads).
    """
    
    # Singleton instance
    _instance: Optional['SignalBus'] = None
    
    # =========================================================================
    # CORE SIGNALS
    # =========================================================================
    
    # Application Lifecycle
    app_ready = Signal()                 # App terminou boot e checks
    shutdown_requested = Signal()        # App vai fechar
    
    # Error Handling
    error_occurred = Signal(str, str)    # title, message
    status_message = Signal(str, int)    # message, timeout_ms (statusbar)
    
    # Project Events
    project_created = Signal(object)     # ProjectData
    project_loaded = Signal(object)      # ProjectData
    project_saved = Signal(str)          # path
    project_closed = Signal()
    project_autosaved = Signal()
    
    # Data/Domain Events
    product_created = Signal(dict)
    product_updated = Signal(dict)
    product_deleted = Signal(str) # ID
    
    inventory_refreshed = Signal() # Full reload requested
    
    # UI/View Navigation
    navigate_to = Signal(str) # 'dashboard', 'editor', 'settings'
    
    def __init__(self):
        super().__init__()
    
    @classmethod
    def instance(cls) -> 'SignalBus':
        """Acesso Singleton."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

# Helper global
def get_signal_bus() -> SignalBus:
    return SignalBus.instance()

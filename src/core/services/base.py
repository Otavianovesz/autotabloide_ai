"""
AutoTabloide AI - Base Service
==============================
Phase 0.1: Service Layer Architecture

Base para todos os serviços de domínio.
Garante acesso padronizado ao Barramento de Sinais e outras infraestruturas.
"""

from PySide6.QtCore import QObject
from typing import Optional
from src.core.signals import SignalBus, get_signal_bus

class BaseService(QObject):
    """
    Classe base para serviços de negócio.
    Serviços devem ser agnósticos de UI (exceto via sinais).
    """
    
    def __init__(self):
        super().__init__()
        self._bus = get_signal_bus()
        
    @property
    def bus(self) -> SignalBus:
        """Acesso ao barramento de eventos."""
        return self._bus
    
    def log_error(self, title: str, message: str):
        """Emite erro para ser tratado pela UI/Log Global."""
        self.bus.error_occurred.emit(title, message)
    
    def log_status(self, message: str, timeout: int = 3000):
        """Emite mensagem para status bar."""
        self.bus.status_message.emit(message, timeout)

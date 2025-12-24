"""
AutoTabloide AI - Sistema de Estado (Pub/Sub)
==============================================
Conforme Auditoria Industrial: State Management desacoplado.
Permite que UI reaja a eventos do backend sem acoplamento direto.
"""

from __future__ import annotations
from typing import Callable, Dict, List, Any, Optional, TypeVar
from enum import Enum, auto
from dataclasses import dataclass, field
from datetime import datetime
import asyncio
import threading
import logging

logger = logging.getLogger("AutoTabloide.EventBus")

T = TypeVar('T')


class EventType(Enum):
    """Tipos de eventos do sistema."""
    # Renderização
    RENDER_START = auto()
    RENDER_PROGRESS = auto()
    RENDER_COMPLETE = auto()
    RENDER_ERROR = auto()
    
    # Dados
    PRODUCT_CREATED = auto()
    PRODUCT_UPDATED = auto()
    PRODUCT_DELETED = auto()
    PRODUCTS_IMPORTED = auto()
    
    # Projetos
    PROJECT_SAVED = auto()
    PROJECT_LOADED = auto()
    PROJECT_DIRTY = auto()
    
    # IA
    AI_TASK_START = auto()
    AI_TASK_COMPLETE = auto()
    AI_SANITIZATION_DONE = auto()
    AI_IMAGE_FOUND = auto()
    
    # Sistema
    DB_CONNECTED = auto()
    DB_ERROR = auto()
    SAFE_MODE_ENTER = auto()
    SAFE_MODE_EXIT = auto()
    
    # UI
    VIEW_CHANGED = auto()
    SNACKBAR_SHOW = auto()
    DIALOG_OPEN = auto()
    DIALOG_CLOSE = auto()


@dataclass
class Event:
    """Estrutura de evento."""
    type: EventType
    data: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    source: Optional[str] = None


# Type alias para handlers
EventHandler = Callable[[Event], None]
AsyncEventHandler = Callable[[Event], Any]  # Coroutine


class EventBus:
    """
    Barramento de Eventos Central (Singleton).
    
    Implementa padrão Pub/Sub para desacoplar componentes.
    Suporta handlers síncronos e assíncronos.
    
    Uso:
        bus = EventBus()
        
        # Subscrever
        bus.subscribe(EventType.RENDER_COMPLETE, my_handler)
        
        # Publicar
        bus.publish(Event(EventType.RENDER_COMPLETE, {"path": "/output.pdf"}))
    """
    
    _instance: Optional['EventBus'] = None
    _lock = threading.Lock()
    
    def __new__(cls) -> 'EventBus':
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._init_bus()
        return cls._instance
    
    def _init_bus(self) -> None:
        """Inicializa estruturas internas."""
        self._handlers: Dict[EventType, List[EventHandler]] = {}
        self._async_handlers: Dict[EventType, List[AsyncEventHandler]] = {}
        self._history: List[Event] = []
        self._max_history = 100
        self._handler_lock = threading.RLock()
    
    def subscribe(
        self, 
        event_type: EventType, 
        handler: EventHandler
    ) -> Callable[[], None]:
        """
        Registra handler para um tipo de evento.
        
        Args:
            event_type: Tipo de evento a escutar
            handler: Função callback
            
        Returns:
            Função para cancelar inscrição (unsubscribe)
        """
        with self._handler_lock:
            if event_type not in self._handlers:
                self._handlers[event_type] = []
            self._handlers[event_type].append(handler)
        
        def unsubscribe():
            with self._handler_lock:
                if event_type in self._handlers:
                    try:
                        self._handlers[event_type].remove(handler)
                    except ValueError:
                        pass
        
        return unsubscribe
    
    def subscribe_async(
        self, 
        event_type: EventType, 
        handler: AsyncEventHandler
    ) -> Callable[[], None]:
        """Registra handler assíncrono."""
        with self._handler_lock:
            if event_type not in self._async_handlers:
                self._async_handlers[event_type] = []
            self._async_handlers[event_type].append(handler)
        
        def unsubscribe():
            with self._handler_lock:
                if event_type in self._async_handlers:
                    try:
                        self._async_handlers[event_type].remove(handler)
                    except ValueError:
                        pass
        
        return unsubscribe
    
    def publish(self, event: Event) -> None:
        """
        Publica evento para todos handlers registrados.
        
        Args:
            event: Evento a publicar
        """
        # Adiciona ao histórico
        self._history.append(event)
        if len(self._history) > self._max_history:
            self._history.pop(0)
        
        logger.debug(f"Event: {event.type.name} from {event.source}")
        
        # Notifica handlers síncronos
        with self._handler_lock:
            handlers = self._handlers.get(event.type, []).copy()
        
        for handler in handlers:
            try:
                handler(event)
            except Exception as e:
                logger.error(f"Erro no handler de {event.type.name}: {e}")
    
    async def publish_async(self, event: Event) -> None:
        """
        Publica evento de forma assíncrona.
        Notifica handlers sync e async.
        """
        # Handlers síncronos
        self.publish(event)
        
        # Handlers assíncronos
        with self._handler_lock:
            async_handlers = self._async_handlers.get(event.type, []).copy()
        
        for handler in async_handlers:
            try:
                await handler(event)
            except Exception as e:
                logger.error(f"Erro no async handler de {event.type.name}: {e}")
    
    def emit(self, event_type: EventType, **data) -> None:
        """
        Atalho para publicar eventos simples.
        
        Uso:
            bus.emit(EventType.RENDER_COMPLETE, path="/output.pdf")
        """
        self.publish(Event(type=event_type, data=data))
    
    def get_history(
        self, 
        event_type: Optional[EventType] = None,
        limit: int = 10
    ) -> List[Event]:
        """Retorna histórico de eventos filtrado."""
        if event_type:
            filtered = [e for e in self._history if e.type == event_type]
        else:
            filtered = self._history.copy()
        
        return filtered[-limit:]
    
    def clear_handlers(self) -> None:
        """Remove todos os handlers (para testes)."""
        with self._handler_lock:
            self._handlers.clear()
            self._async_handlers.clear()


# Instância global
_bus: Optional[EventBus] = None


def get_event_bus() -> EventBus:
    """Obtém o event bus global."""
    global _bus
    if _bus is None:
        _bus = EventBus()
    return _bus


def emit(event_type: EventType, **data) -> None:
    """Atalho global para emitir eventos."""
    get_event_bus().emit(event_type, **data)


def subscribe(event_type: EventType, handler: EventHandler) -> Callable[[], None]:
    """Atalho global para subscrever eventos."""
    return get_event_bus().subscribe(event_type, handler)


# ==============================================================================
# DECORATORS DE REATIVIDADE
# ==============================================================================

def on_event(event_type: EventType):
    """
    Decorator para registrar método como handler de evento.
    
    Uso:
        class MyView:
            @on_event(EventType.PRODUCT_UPDATED)
            def _on_product_update(self, event: Event):
                self.refresh()
    """
    def decorator(func: EventHandler) -> EventHandler:
        # Marca função para registro posterior
        func._event_type = event_type
        return func
    return decorator


class ReactiveComponent:
    """
    Mixin para componentes reativos.
    Registra automaticamente handlers decorados com @on_event.
    """
    
    def __init__(self):
        self._event_unsubscribers: List[Callable] = []
        self._register_event_handlers()
    
    def _register_event_handlers(self) -> None:
        """Registra handlers decorados automaticamente."""
        bus = get_event_bus()
        
        for name in dir(self):
            if name.startswith('_'):
                continue
            
            method = getattr(self, name, None)
            if method and hasattr(method, '_event_type'):
                unsub = bus.subscribe(method._event_type, method)
                self._event_unsubscribers.append(unsub)
    
    def dispose(self) -> None:
        """Remove todos os handlers registrados."""
        for unsub in self._event_unsubscribers:
            unsub()
        self._event_unsubscribers.clear()

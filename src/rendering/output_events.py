"""
AutoTabloide AI - Output Engine Events
========================================
Eventos detalhados para o OutputEngine.
Passo 51 do Checklist 100.

Funcionalidades:
- Eventos de progresso detalhados
- Integração com EventBus
- Callback para UI
"""

from enum import Enum, auto
from typing import Callable, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime

from src.core.event_bus import get_event_bus
from src.core.logging_config import get_logger

logger = get_logger("OutputEvents")


class OutputEventType(Enum):
    """Tipos de eventos do OutputEngine."""
    RENDER_STARTED = auto()
    RENDER_PROGRESS = auto()
    RENDER_COMPLETED = auto()
    RENDER_FAILED = auto()
    
    SLOT_PROCESSING = auto()
    SLOT_COMPLETED = auto()
    
    PDF_GENERATION_STARTED = auto()
    PDF_GENERATION_PROGRESS = auto()
    PDF_GENERATION_COMPLETED = auto()
    PDF_GENERATION_FAILED = auto()
    
    FONT_LOADED = auto()
    FONT_FALLBACK_USED = auto()
    
    IMAGE_EMBEDDED = auto()
    IMAGE_MISSING = auto()


@dataclass
class OutputEvent:
    """Evento do OutputEngine."""
    event_type: OutputEventType
    timestamp: datetime
    data: Dict[str, Any]
    
    # Progresso (0.0 a 1.0)
    progress: float = 0.0
    
    # Mensagem legível
    message: str = ""


class OutputEventEmitter:
    """
    Emissor de eventos do OutputEngine.
    Passo 51 do Checklist - Eventos detalhados no OutputEngine.
    """
    
    def __init__(self):
        self._event_bus = get_event_bus()
        self._listeners: list = []
        self._current_job_id: Optional[str] = None
        self._total_slots: int = 0
        self._processed_slots: int = 0
    
    def add_listener(self, callback: Callable[[OutputEvent], None]) -> None:
        """Adiciona listener para eventos."""
        self._listeners.append(callback)
    
    def remove_listener(self, callback: Callable[[OutputEvent], None]) -> None:
        """Remove listener."""
        if callback in self._listeners:
            self._listeners.remove(callback)
    
    def _emit(self, event: OutputEvent) -> None:
        """Emite evento para todos os listeners."""
        # EventBus
        self._event_bus.emit("output_event", {
            "type": event.event_type.name,
            "progress": event.progress,
            "message": event.message,
            "data": event.data
        })
        
        # Listeners diretos
        for listener in self._listeners:
            try:
                listener(event)
            except Exception as e:
                logger.error(f"Erro em listener de evento: {e}")
    
    def start_render(self, job_id: str, total_slots: int) -> None:
        """Inicia job de renderização."""
        self._current_job_id = job_id
        self._total_slots = total_slots
        self._processed_slots = 0
        
        self._emit(OutputEvent(
            event_type=OutputEventType.RENDER_STARTED,
            timestamp=datetime.now(),
            data={"job_id": job_id, "total_slots": total_slots},
            progress=0.0,
            message=f"Iniciando renderização de {total_slots} slots..."
        ))
    
    def slot_processing(self, slot_id: str, product_name: str) -> None:
        """Marca início de processamento de slot."""
        self._emit(OutputEvent(
            event_type=OutputEventType.SLOT_PROCESSING,
            timestamp=datetime.now(),
            data={"slot_id": slot_id, "product": product_name},
            progress=self._processed_slots / max(self._total_slots, 1),
            message=f"Processando {slot_id}: {product_name}"
        ))
    
    def slot_completed(self, slot_id: str) -> None:
        """Marca conclusão de slot."""
        self._processed_slots += 1
        progress = self._processed_slots / max(self._total_slots, 1)
        
        self._emit(OutputEvent(
            event_type=OutputEventType.SLOT_COMPLETED,
            timestamp=datetime.now(),
            data={"slot_id": slot_id, "processed": self._processed_slots},
            progress=progress,
            message=f"Slot {slot_id} concluído ({self._processed_slots}/{self._total_slots})"
        ))
    
    def font_loaded(self, font_name: str) -> None:
        """Notifica fonte carregada."""
        self._emit(OutputEvent(
            event_type=OutputEventType.FONT_LOADED,
            timestamp=datetime.now(),
            data={"font": font_name},
            message=f"Fonte carregada: {font_name}"
        ))
    
    def font_fallback(self, requested: str, used: str) -> None:
        """Notifica uso de fonte fallback."""
        self._emit(OutputEvent(
            event_type=OutputEventType.FONT_FALLBACK_USED,
            timestamp=datetime.now(),
            data={"requested": requested, "used": used},
            message=f"Fonte '{requested}' não encontrada, usando '{used}'"
        ))
    
    def image_embedded(self, image_hash: str) -> None:
        """Notifica imagem incorporada."""
        self._emit(OutputEvent(
            event_type=OutputEventType.IMAGE_EMBEDDED,
            timestamp=datetime.now(),
            data={"hash": image_hash},
            message=f"Imagem incorporada: {image_hash[:8]}..."
        ))
    
    def image_missing(self, slot_id: str) -> None:
        """Notifica imagem faltando."""
        self._emit(OutputEvent(
            event_type=OutputEventType.IMAGE_MISSING,
            timestamp=datetime.now(),
            data={"slot_id": slot_id},
            message=f"Imagem faltando para slot {slot_id}"
        ))
    
    def pdf_generation_started(self) -> None:
        """Inicia geração de PDF."""
        self._emit(OutputEvent(
            event_type=OutputEventType.PDF_GENERATION_STARTED,
            timestamp=datetime.now(),
            data={},
            progress=0.9,
            message="Gerando arquivo PDF..."
        ))
    
    def pdf_generation_completed(self, path: str, size_kb: float) -> None:
        """PDF gerado com sucesso."""
        self._emit(OutputEvent(
            event_type=OutputEventType.PDF_GENERATION_COMPLETED,
            timestamp=datetime.now(),
            data={"path": path, "size_kb": size_kb},
            progress=1.0,
            message=f"PDF gerado: {size_kb:.1f}KB"
        ))
    
    def render_completed(self, job_id: str, duration_s: float) -> None:
        """Renderização concluída."""
        self._emit(OutputEvent(
            event_type=OutputEventType.RENDER_COMPLETED,
            timestamp=datetime.now(),
            data={"job_id": job_id, "duration_s": duration_s},
            progress=1.0,
            message=f"Renderização concluída em {duration_s:.1f}s"
        ))
    
    def render_failed(self, error: str) -> None:
        """Renderização falhou."""
        self._emit(OutputEvent(
            event_type=OutputEventType.RENDER_FAILED,
            timestamp=datetime.now(),
            data={"error": error},
            progress=0.0,
            message=f"Erro: {error}"
        ))


# Singleton
_output_emitter: Optional[OutputEventEmitter] = None


def get_output_emitter() -> OutputEventEmitter:
    """Retorna instância singleton do emissor."""
    global _output_emitter
    if _output_emitter is None:
        _output_emitter = OutputEventEmitter()
    return _output_emitter

"""
AutoTabloide AI - Render Queue
==============================
PROTOCOLO DE RETIFICAÇÃO NÍVEL 0 - Fase 4 (Passos 143-150)
Fila de renderização para batch export.
"""

from __future__ import annotations
from pathlib import Path
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import logging
import uuid

from PySide6.QtCore import Qt, Signal, QObject, QThread, QTimer

logger = logging.getLogger("RenderQueue")


# =============================================================================
# JOB STATUS
# =============================================================================

class JobStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


# =============================================================================
# RENDER JOB
# =============================================================================

@dataclass
class RenderJob:
    """Um job de renderização na fila."""
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    name: str = ""
    status: JobStatus = JobStatus.PENDING
    progress: int = 0
    
    # Configuração
    scene_data: Dict = field(default_factory=dict)
    template_path: str = ""
    output_path: str = ""
    format: str = "pdf"
    dpi: int = 300
    
    # Metadados
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    error_message: str = ""
    
    @property
    def duration_sec(self) -> float:
        if self.started_at and self.finished_at:
            return (self.finished_at - self.started_at).total_seconds()
        return 0


# =============================================================================
# RENDER WORKER
# =============================================================================

class RenderWorker(QThread):
    """Worker para executar rendering."""
    
    progress = Signal(str, int, str)  # job_id, percent, message
    job_completed = Signal(str, bool, str)  # job_id, success, result
    
    def __init__(self, job: RenderJob, parent=None):
        super().__init__(parent)
        self.job = job
        self._cancelled = False
    
    def run(self):
        job = self.job
        job.status = JobStatus.RUNNING
        job.started_at = datetime.now()
        
        try:
            self.progress.emit(job.id, 10, "Preparando dados...")
            
            # Importa renderer
            from src.rendering.pdf_export import export_atelier_to_pdf
            
            self.progress.emit(job.id, 30, "Gerando SVG final...")
            
            if self._cancelled:
                self._finish(False, "Cancelado")
                return
            
            self.progress.emit(job.id, 50, "Convertendo para PDF...")
            
            # Executa export
            success, message = export_atelier_to_pdf(
                job.scene_data,
                job.template_path,
                job.output_path,
            )
            
            self.progress.emit(job.id, 90, "Finalizando...")
            
            if success:
                self._finish(True, job.output_path)
            else:
                self._finish(False, message)
                
        except Exception as e:
            logger.error(f"Erro no render: {e}")
            self._finish(False, str(e))
    
    def _finish(self, success: bool, result: str):
        self.job.finished_at = datetime.now()
        self.job.status = JobStatus.COMPLETED if success else JobStatus.FAILED
        self.job.progress = 100 if success else 0
        if not success:
            self.job.error_message = result
        
        self.job_completed.emit(self.job.id, success, result)
    
    def cancel(self):
        self._cancelled = True


# =============================================================================
# RENDER QUEUE
# =============================================================================

class RenderQueue(QObject):
    """
    Fila de renderização com execução sequencial.
    
    Features:
    - Adiciona jobs à fila
    - Executa um por vez
    - Notifica progresso
    - Histórico de jobs
    """
    
    job_added = Signal(object)  # RenderJob
    job_started = Signal(str)   # job_id
    job_progress = Signal(str, int, str)  # job_id, percent, message
    job_completed = Signal(str, bool, str)  # job_id, success, result
    queue_empty = Signal()
    
    _instance: Optional['RenderQueue'] = None
    
    def __init__(self):
        super().__init__()
        
        self._queue: List[RenderJob] = []
        self._history: List[RenderJob] = []
        self._current_worker: Optional[RenderWorker] = None
        self._processing = False
    
    @classmethod
    def instance(cls) -> 'RenderQueue':
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    def add_job(self, job: RenderJob) -> str:
        """Adiciona job à fila."""
        self._queue.append(job)
        self.job_added.emit(job)
        
        logger.info(f"[Queue] Job adicionado: {job.id}")
        
        # Inicia processamento se não estiver rodando
        if not self._processing:
            self._process_next()
        
        return job.id
    
    def create_job(
        self,
        scene_data: Dict,
        template_path: str,
        output_path: str,
        name: str = None,
        format: str = "pdf",
        dpi: int = 300
    ) -> str:
        """Cria e adiciona job."""
        job = RenderJob(
            name=name or f"Export_{datetime.now().strftime('%H%M%S')}",
            scene_data=scene_data,
            template_path=template_path,
            output_path=output_path,
            format=format,
            dpi=dpi,
        )
        return self.add_job(job)
    
    def _process_next(self):
        """Processa próximo job da fila."""
        if not self._queue:
            self._processing = False
            self.queue_empty.emit()
            return
        
        self._processing = True
        job = self._queue.pop(0)
        
        self.job_started.emit(job.id)
        logger.info(f"[Queue] Iniciando job: {job.id}")
        
        # Cria worker
        self._current_worker = RenderWorker(job)
        self._current_worker.progress.connect(self.job_progress.emit)
        self._current_worker.job_completed.connect(self._on_job_completed)
        self._current_worker.start()
    
    def _on_job_completed(self, job_id: str, success: bool, result: str):
        """Callback quando job termina."""
        # Move para histórico
        for job in self._queue + [self._current_worker.job]:
            if job.id == job_id:
                self._history.append(job)
                break
        
        self.job_completed.emit(job_id, success, result)
        
        # Processa próximo
        self._current_worker = None
        self._process_next()
    
    def cancel_current(self):
        """Cancela job atual."""
        if self._current_worker:
            self._current_worker.cancel()
    
    def clear_queue(self):
        """Limpa fila pendente."""
        self._queue.clear()
    
    @property
    def pending_count(self) -> int:
        return len(self._queue)
    
    @property
    def is_processing(self) -> bool:
        return self._processing
    
    def get_history(self, limit: int = 10) -> List[RenderJob]:
        """Retorna histórico de jobs."""
        return self._history[-limit:]


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_render_queue() -> RenderQueue:
    """Acesso global à fila."""
    return RenderQueue.instance()


def queue_render(scene_data: Dict, template_path: str, output_path: str) -> str:
    """Enfileira renderização."""
    return get_render_queue().create_job(scene_data, template_path, output_path)

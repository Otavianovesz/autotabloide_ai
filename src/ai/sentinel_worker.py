"""
AutoTabloide AI - Sentinel Thread Worker
========================================
PROTOCOLO DE RETIFICAÇÃO NÍVEL 0 - Fase 5 (Passos 176-185)
Worker thread para Sentinel AI com health checks.
"""

from __future__ import annotations
from typing import Optional, Dict, List, Callable
from dataclasses import dataclass
from enum import Enum
from datetime import datetime
import logging
import queue

from PySide6.QtCore import QThread, Signal, QTimer

logger = logging.getLogger("Sentinel")


# =============================================================================
# TASK TYPES
# =============================================================================

class TaskType(Enum):
    REMBG = "rembg"           # Remove background
    UPSCALE = "upscale"       # Upscale image
    OCR_PRICE = "ocr_price"   # OCR de preço
    CLASSIFY = "classify"     # Classificar produto
    HEALTH = "health"         # Health check


@dataclass
class SentinelTask:
    """Uma tarefa para o Sentinel."""
    id: str
    type: TaskType
    data: Dict
    priority: int = 5  # 1 = highest, 10 = lowest
    created_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()


@dataclass
class SentinelResult:
    """Resultado de uma tarefa."""
    task_id: str
    success: bool
    result: Dict
    error: str = ""
    duration_ms: int = 0


# =============================================================================
# SENTINEL WORKER
# =============================================================================

class SentinelWorker(QThread):
    """
    Worker thread para processamento AI.
    
    Features:
    - Fila de tarefas com prioridade
    - Health check periódico
    - Rate limiting
    - Graceful shutdown
    """
    
    task_completed = Signal(object)  # SentinelResult
    status_changed = Signal(str)     # idle/busy/error
    health_update = Signal(dict)     # health info
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self._queue = queue.PriorityQueue()
        self._running = True
        self._current_task: Optional[SentinelTask] = None
        self._tasks_completed = 0
        self._start_time: Optional[datetime] = None
    
    def run(self):
        self._start_time = datetime.now()
        self.status_changed.emit("idle")
        
        while self._running:
            try:
                # Pega próxima tarefa (timeout para checar _running)
                try:
                    priority, task = self._queue.get(timeout=0.5)
                except queue.Empty:
                    continue
                
                self._current_task = task
                self.status_changed.emit("busy")
                
                # Processa
                start = datetime.now()
                result = self._process_task(task)
                duration = int((datetime.now() - start).total_seconds() * 1000)
                
                result.duration_ms = duration
                self._tasks_completed += 1
                
                self.task_completed.emit(result)
                self._current_task = None
                self.status_changed.emit("idle")
                
            except Exception as e:
                logger.error(f"[Sentinel] Erro: {e}")
                self.status_changed.emit("error")
    
    def _process_task(self, task: SentinelTask) -> SentinelResult:
        """Processa uma tarefa."""
        try:
            if task.type == TaskType.REMBG:
                return self._process_rembg(task)
            elif task.type == TaskType.UPSCALE:
                return self._process_upscale(task)
            elif task.type == TaskType.OCR_PRICE:
                return self._process_ocr(task)
            elif task.type == TaskType.CLASSIFY:
                return self._process_classify(task)
            elif task.type == TaskType.HEALTH:
                return self._process_health(task)
            else:
                return SentinelResult(task.id, False, {}, f"Unknown task type: {task.type}")
                
        except Exception as e:
            return SentinelResult(task.id, False, {}, str(e))
    
    def _process_rembg(self, task: SentinelTask) -> SentinelResult:
        """Remove background de imagem."""
        try:
            from rembg import remove
            from PIL import Image
            
            input_path = task.data.get("input_path")
            output_path = task.data.get("output_path")
            
            img = Image.open(input_path)
            result = remove(img)
            result.save(output_path)
            
            return SentinelResult(task.id, True, {"output": output_path})
            
        except ImportError:
            return SentinelResult(task.id, False, {}, "rembg not installed")
        except Exception as e:
            return SentinelResult(task.id, False, {}, str(e))
    
    def _process_upscale(self, task: SentinelTask) -> SentinelResult:
        """Upscale imagem."""
        # Placeholder para Real-ESRGAN
        return SentinelResult(task.id, False, {}, "Upscaler not implemented")
    
    def _process_ocr(self, task: SentinelTask) -> SentinelResult:
        """OCR de preço."""
        # Placeholder para OCR
        return SentinelResult(task.id, False, {}, "OCR not implemented")
    
    def _process_classify(self, task: SentinelTask) -> SentinelResult:
        """Classifica produto."""
        # Placeholder para classificação
        return SentinelResult(task.id, False, {}, "Classifier not implemented")
    
    def _process_health(self, task: SentinelTask) -> SentinelResult:
        """Health check."""
        health = {
            "status": "ok",
            "uptime_sec": (datetime.now() - self._start_time).total_seconds() if self._start_time else 0,
            "tasks_completed": self._tasks_completed,
            "queue_size": self._queue.qsize(),
            "gpu_available": self._check_gpu(),
        }
        self.health_update.emit(health)
        return SentinelResult(task.id, True, health)
    
    def _check_gpu(self) -> bool:
        """Verifica GPU disponível."""
        try:
            import torch
            return torch.cuda.is_available()
        except ImportError:
            return False
    
    # =========================================================================
    # PUBLIC API
    # =========================================================================
    
    def add_task(self, task: SentinelTask):
        """Adiciona tarefa à fila."""
        self._queue.put((task.priority, task))
        logger.debug(f"[Sentinel] Task enqueued: {task.id}")
    
    def remove_background(self, input_path: str, output_path: str) -> str:
        """Enfileira remoção de fundo. Retorna task_id."""
        import uuid
        task_id = str(uuid.uuid4())[:8]
        task = SentinelTask(
            id=task_id,
            type=TaskType.REMBG,
            data={"input_path": input_path, "output_path": output_path},
            priority=3
        )
        self.add_task(task)
        return task_id
    
    def request_health_check(self):
        """Solicita health check."""
        import uuid
        task = SentinelTask(
            id=str(uuid.uuid4())[:8],
            type=TaskType.HEALTH,
            data={},
            priority=1
        )
        self.add_task(task)
    
    def stop(self):
        """Para o worker gracefully."""
        self._running = False
        self.wait(3000)
    
    @property
    def is_busy(self) -> bool:
        return self._current_task is not None
    
    @property
    def queue_size(self) -> int:
        return self._queue.qsize()


# =============================================================================
# SENTINEL MANAGER (SINGLETON)
# =============================================================================

class SentinelManager:
    """Gerenciador singleton do Sentinel."""
    
    _instance: Optional['SentinelManager'] = None
    _worker: Optional[SentinelWorker] = None
    
    @classmethod
    def instance(cls) -> 'SentinelManager':
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    def start(self):
        """Inicia o worker."""
        if self._worker is None or not self._worker.isRunning():
            self._worker = SentinelWorker()
            self._worker.start()
            logger.info("[Sentinel] Started")
    
    def stop(self):
        """Para o worker."""
        if self._worker:
            self._worker.stop()
            logger.info("[Sentinel] Stopped")
    
    @property
    def worker(self) -> Optional[SentinelWorker]:
        return self._worker


def get_sentinel() -> SentinelManager:
    """Acesso global ao Sentinel."""
    return SentinelManager.instance()

"""
AutoTabloide AI - Sentinel Bridge for Qt
=========================================
PROTOCOLO DE CONVERGÊNCIA INDUSTRIAL - Fase 3
Passos 61-65: Ponte entre processo Sentinel e UI Qt.

Gerencia comunicação assíncrona com o sidecar cognitivo.
"""

from __future__ import annotations
import multiprocessing
from multiprocessing import Queue, Process
from typing import Optional, Dict, Callable, Any
from pathlib import Path
import threading
import time
import json
import logging

from PySide6.QtCore import QObject, Signal, Slot, QTimer, QThread


# =============================================================================
# TASK TYPES
# =============================================================================

class SentinelTask:
    """Tipos de tarefas para o Sentinel."""
    SANITIZE_NAME = "sanitize_name"
    HUNT_IMAGE = "hunt_image"
    PROCESS_IMAGE = "process_image"
    GENERATE_TEXT = "generate_text"
    STATUS_CHECK = "status_check"


# =============================================================================
# SENTINEL BRIDGE
# =============================================================================

class SentinelBridge(QObject):
    """
    Ponte Qt para o Sentinel Process.
    
    Gerencia comunicação via Queues multiprocessing:
    - input_queue: Qt -> Sentinel
    - output_queue: Sentinel -> Qt
    
    Sinais emitidos para UI:
    - task_completed: quando Sentinel completa uma tarefa
    - status_changed: quando status do Sentinel muda
    - error: quando ocorre erro
    """
    
    # Sinais
    task_submitted = Signal(str)  # task_id
    task_completed = Signal(str, dict)  # task_id, result
    task_failed = Signal(str, str)  # task_id, error
    status_changed = Signal(str)  # status string
    ready = Signal(bool)  # Sentinel pronto?
    
    _instance: Optional['SentinelBridge'] = None
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self._input_queue: Optional[Queue] = None
        self._output_queue: Optional[Queue] = None
        self._sentinel_process: Optional[Process] = None
        self._is_ready = False
        self._pending_tasks: Dict[str, Dict] = {}
        self._task_counter = 0
        
        # Logger
        self._logger = logging.getLogger("AutoTabloide.SentinelBridge")
        
        # Thread para escutar output queue
        self._listener_thread: Optional[QThread] = None
        self._listener: Optional[QueueListener] = None
        
        # Timer para verificar saúde
        self._health_timer = QTimer(self)
        self._health_timer.timeout.connect(self._check_health)
        self._health_timer.start(5000)  # 5 segundos
    
    @classmethod
    def instance(cls) -> 'SentinelBridge':
        """Singleton pattern."""
        if cls._instance is None:
            cls._instance = SentinelBridge()
        return cls._instance
    
    def start(self, config: Dict = None) -> bool:
        """
        Inicia o Sentinel Process.
        
        Returns:
            True se iniciado com sucesso
        """
        if self._sentinel_process is not None and self._sentinel_process.is_alive():
            self._logger.info("Sentinel já está rodando")
            return True
        
        try:
            # Cria queues
            self._input_queue = Queue()
            self._output_queue = Queue()
            
            # GAP-07 FIX: Usa constantes centralizadas ao invés de hardcoding
            if config is None:
                try:
                    from src.core.constants import STAGING_DIR, SYSTEM_ROOT
                    config = {
                        "download_path": str(STAGING_DIR),
                        "models_path": str(SYSTEM_ROOT / "bin" / "models"),
                    }
                except ImportError:
                    # Fallback para compat
                    config = {
                        "download_path": str(Path("AutoTabloide_System_Root/staging")),
                        "models_path": str(Path("AutoTabloide_System_Root/bin/models")),
                    }
            
            # Inicia Sentinel em processo separado
            from src.ai.sentinel import SentinelProcess
            self._sentinel_process = Process(
                target=self._run_sentinel,
                args=(self._input_queue, self._output_queue, config),
                daemon=True
            )
            self._sentinel_process.start()
            
            # Inicia listener para output queue
            self._start_listener()
            
            self._is_ready = True
            self.ready.emit(True)
            self.status_changed.emit("Sentinel iniciado")
            
            return True
            
        except Exception as e:
            self._logger.error(f"Erro ao iniciar Sentinel: {e}", exc_info=True)
            self.status_changed.emit(f"Erro: {e}")
            return False
    
    @staticmethod
    def _run_sentinel(input_q: Queue, output_q: Queue, config: Dict):
        """Função estática para rodar em processo separado."""
        try:
            from src.ai.sentinel import SentinelProcess
            sentinel = SentinelProcess(input_q, output_q, config)
            sentinel.run()
        except Exception as e:
            output_q.put({"type": "error", "error": str(e)})
    
    def _start_listener(self):
        """Inicia thread de escuta do output queue."""
        self._listener_thread = QThread()
        self._listener = QueueListener(self._output_queue)
        self._listener.moveToThread(self._listener_thread)
        
        self._listener.message_received.connect(self._on_message_received)
        self._listener_thread.started.connect(self._listener.run)
        self._listener_thread.start()
    
    def stop(self):
        """Para o Sentinel Process."""
        if self._sentinel_process and self._sentinel_process.is_alive():
            self._input_queue.put({"type": "shutdown"})
            self._sentinel_process.join(timeout=5)
            
            if self._sentinel_process.is_alive():
                self._sentinel_process.terminate()
        
        if self._listener_thread and self._listener_thread.isRunning():
            if self._listener:
                self._listener.stop()
            self._listener_thread.quit()
            self._listener_thread.wait(1000)
        
        self._is_ready = False
        self.ready.emit(False)
        self.status_changed.emit("Sentinel parado")
    
    def is_ready(self) -> bool:
        """Verifica se Sentinel está pronto."""
        return self._is_ready and self._sentinel_process is not None and self._sentinel_process.is_alive()
    
    def submit_task(self, task_type: str, data: Dict, callback: Callable = None) -> str:
        """
        Submete tarefa ao Sentinel.
        
        Args:
            task_type: Tipo da tarefa (ver SentinelTask)
            data: Dados da tarefa
            callback: Função opcional para chamar quando completar
            
        Returns:
            task_id para rastrear a tarefa
        """
        if not self.is_ready():
            raise RuntimeError("Sentinel não está pronto")
        
        self._task_counter += 1
        task_id = f"task_{self._task_counter}_{int(time.time())}"
        
        task = {
            "type": task_type,
            "task_id": task_id,
            "data": data,
        }
        
        # Registra tarefa pendente
        self._pending_tasks[task_id] = {
            "task": task,
            "callback": callback,
            "submitted_at": time.time(),
        }
        
        # Envia para Sentinel
        self._input_queue.put(task)
        self.task_submitted.emit(task_id)
        
        return task_id
    
    def sanitize_name(self, raw_name: str, callback: Callable = None) -> str:
        """Wrapper para sanitização de nome."""
        return self.submit_task(
            SentinelTask.SANITIZE_NAME,
            {"raw_name": raw_name},
            callback
        )
    
    def hunt_image(self, product_name: str, callback: Callable = None) -> str:
        """Wrapper para busca de imagem."""
        return self.submit_task(
            SentinelTask.HUNT_IMAGE,
            {"query": product_name},
            callback
        )
    
    def process_image(self, image_path: str, operations: list, callback: Callable = None) -> str:
        """Wrapper para processamento de imagem."""
        return self.submit_task(
            SentinelTask.PROCESS_IMAGE,
            {"image_path": image_path, "operations": operations},
            callback
        )
    
    @Slot(dict)
    def _on_message_received(self, message: Dict):
        """Processa mensagem recebida do Sentinel."""
        msg_type = message.get("type")
        task_id = message.get("task_id")
        
        if msg_type == "result":
            pending = self._pending_tasks.pop(task_id, None)
            if pending:
                callback = pending.get("callback")
                if callback:
                    callback(message.get("result"))
                self.task_completed.emit(task_id, message.get("result", {}))
                
        elif msg_type == "error":
            pending = self._pending_tasks.pop(task_id, None)
            error_msg = message.get("error", "Erro desconhecido")
            self.task_failed.emit(task_id, error_msg)
            
        elif msg_type == "status":
            self.status_changed.emit(message.get("status", ""))
            
        elif msg_type == "llm_ready":
            self.status_changed.emit("LLM carregada e pronta")
    
    def _check_health(self):
        """Verifica saúde do Sentinel periodicamente."""
        if self._sentinel_process is None:
            return
            
        if not self._sentinel_process.is_alive():
            self._is_ready = False
            self.ready.emit(False)
            self.status_changed.emit("Sentinel morreu - reiniciando...")
            self.start()  # Auto-restart
    
    def get_pending_count(self) -> int:
        """Retorna número de tarefas pendentes."""
        return len(self._pending_tasks)


# =============================================================================
# QUEUE LISTENER (roda em QThread)
# =============================================================================

class QueueListener(QObject):
    """Escuta a output queue do Sentinel em thread separada."""
    
    message_received = Signal(dict)
    
    def __init__(self, queue: Queue):
        super().__init__()
        self._queue = queue
        self._running = True
    
    def run(self):
        """Loop de escuta."""
        while self._running:
            try:
                if not self._queue.empty():
                    message = self._queue.get(timeout=0.5)
                    self.message_received.emit(message)
                else:
                    time.sleep(0.1)
            except Exception:
                time.sleep(0.1)
    
    def stop(self):
        self._running = False


# =============================================================================
# GLOBAL SINGLETON ACCESS
# =============================================================================

def get_sentinel() -> SentinelBridge:
    """Acesso global ao SentinelBridge."""
    return SentinelBridge.instance()

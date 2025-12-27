"""
AutoTabloide AI - Database Concurrency
========================================
Gerenciamento de concorrência de escrita no SQLite.
PROTOCOLO DE RETIFICAÇÃO: Passo 23 (Concorrência de escrita).

Implementa locks e filas para evitar conflitos.
"""

import asyncio
import logging
from typing import Optional, Dict, Any, Callable, TypeVar
from dataclasses import dataclass
from contextlib import asynccontextmanager
from datetime import datetime
import threading

logger = logging.getLogger("DBConcurrency")

T = TypeVar('T')


class WriteQueue:
    """
    Fila de operações de escrita.
    
    PASSO 23: Serializa escritas para evitar conflitos.
    """
    
    def __init__(self, max_queue_size: int = 100):
        self.max_queue_size = max_queue_size
        self._queue: asyncio.Queue = None
        self._lock = asyncio.Lock()
        self._running = False
        self._worker_task: Optional[asyncio.Task] = None
    
    async def _ensure_queue(self):
        """Garante que queue existe."""
        if self._queue is None:
            self._queue = asyncio.Queue(maxsize=self.max_queue_size)
    
    async def enqueue(
        self,
        operation: Callable,
        *args,
        priority: int = 1,
        **kwargs
    ) -> Any:
        """
        Enfileira operação de escrita.
        
        Args:
            operation: Função assíncrona a executar
            priority: Prioridade (maior = mais urgente)
            
        Returns:
            Resultado da operação
        """
        await self._ensure_queue()
        
        future = asyncio.Future()
        
        item = {
            "operation": operation,
            "args": args,
            "kwargs": kwargs,
            "future": future,
            "priority": priority,
            "enqueued_at": datetime.now()
        }
        
        await self._queue.put(item)
        
        return await future
    
    async def start_worker(self) -> None:
        """Inicia worker de processamento."""
        await self._ensure_queue()
        self._running = True
        
        async def process():
            while self._running:
                try:
                    item = await asyncio.wait_for(
                        self._queue.get(),
                        timeout=1.0
                    )
                    
                    try:
                        result = await item["operation"](
                            *item["args"],
                            **item["kwargs"]
                        )
                        item["future"].set_result(result)
                    except Exception as e:
                        item["future"].set_exception(e)
                    
                except asyncio.TimeoutError:
                    continue
                except Exception as e:
                    logger.error(f"Erro no worker: {e}")
        
        self._worker_task = asyncio.create_task(process())
    
    def stop_worker(self) -> None:
        """Para worker."""
        self._running = False
        if self._worker_task:
            self._worker_task.cancel()


class DatabaseWriteLock:
    """
    Lock exclusivo para operações de escrita.
    
    Garante que apenas uma escrita ocorra por vez.
    """
    
    def __init__(self):
        self._lock = asyncio.Lock()
        self._current_owner: Optional[str] = None
        self._acquired_at: Optional[datetime] = None
        self._stats = {
            "total_acquires": 0,
            "total_wait_time": 0.0
        }
    
    @asynccontextmanager
    async def acquire(self, owner: str = "unknown"):
        """
        Context manager para adquirir lock.
        
        Args:
            owner: Identificador do owner (para debug)
        """
        start = datetime.now()
        
        async with self._lock:
            wait_time = (datetime.now() - start).total_seconds()
            
            self._current_owner = owner
            self._acquired_at = datetime.now()
            self._stats["total_acquires"] += 1
            self._stats["total_wait_time"] += wait_time
            
            if wait_time > 1.0:
                logger.warning(f"Lock demorou {wait_time:.2f}s para {owner}")
            
            try:
                yield
            finally:
                self._current_owner = None
                self._acquired_at = None
    
    def get_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas do lock."""
        return {
            **self._stats,
            "current_owner": self._current_owner,
            "avg_wait_time": (
                self._stats["total_wait_time"] / self._stats["total_acquires"]
                if self._stats["total_acquires"] > 0 else 0
            )
        }


class ConcurrencyManager:
    """
    Gerenciador central de concorrência.
    
    PASSO 23: Coordena múltiplos writes.
    """
    
    def __init__(self):
        self.write_lock = DatabaseWriteLock()
        self.write_queue = WriteQueue()
        self._initialized = False
    
    async def initialize(self) -> None:
        """Inicializa gerenciador."""
        if not self._initialized:
            await self.write_queue.start_worker()
            self._initialized = True
    
    def shutdown(self) -> None:
        """Encerra gerenciador."""
        self.write_queue.stop_worker()
        self._initialized = False
    
    @asynccontextmanager
    async def write_transaction(self, owner: str = "unknown"):
        """
        Context manager para transação de escrita segura.
        
        Uso:
            async with concurrency.write_transaction("import"):
                await session.add(produto)
                await session.commit()
        """
        async with self.write_lock.acquire(owner):
            yield
    
    async def execute_write(
        self,
        operation: Callable,
        *args,
        **kwargs
    ) -> Any:
        """
        Executa operação de escrita via fila.
        
        Args:
            operation: Função assíncrona
            
        Returns:
            Resultado
        """
        return await self.write_queue.enqueue(operation, *args, **kwargs)


# ==============================================================================
# INSTÂNCIA GLOBAL
# ==============================================================================

_concurrency_manager: Optional[ConcurrencyManager] = None


def get_concurrency_manager() -> ConcurrencyManager:
    """Retorna instância global."""
    global _concurrency_manager
    if _concurrency_manager is None:
        _concurrency_manager = ConcurrencyManager()
    return _concurrency_manager


async def with_write_lock(owner: str = ""):
    """Atalho para adquirir write lock."""
    manager = get_concurrency_manager()
    return manager.write_lock.acquire(owner)

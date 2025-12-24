"""
AutoTabloide AI - Sentinel Watchdog
=====================================
Monitor de saúde do processo Sentinel.
Passos 21-22 do Checklist v2.

Funcionalidades:
- Monitora se Sentinel está vivo
- Reinicia automaticamente se morrer
- Log de falhas
"""

import asyncio
import multiprocessing
import time
from typing import Optional, Callable
from dataclasses import dataclass
from datetime import datetime

from src.core.logging_config import get_logger

logger = get_logger("Watchdog")


@dataclass
class ProcessHealth:
    """Status de saúde de um processo."""
    is_alive: bool
    pid: Optional[int]
    last_check: datetime
    restart_count: int = 0
    last_restart: Optional[datetime] = None


class SentinelWatchdog:
    """
    Monitor de saúde do SentinelProcess.
    Passos 21-22 do Checklist v2.
    
    Reinicia automaticamente se o processo morrer.
    """
    
    def __init__(
        self,
        check_interval: float = 5.0,
        max_restarts: int = 5,
        restart_cooldown: float = 30.0
    ):
        """
        Args:
            check_interval: Intervalo entre checagens (segundos)
            max_restarts: Máximo de reinícios antes de desistir
            restart_cooldown: Tempo mínimo entre reinícios
        """
        self.check_interval = check_interval
        self.max_restarts = max_restarts
        self.restart_cooldown = restart_cooldown
        
        self._sentinel_process: Optional[multiprocessing.Process] = None
        self._sentinel_factory: Optional[Callable] = None
        self._health = ProcessHealth(
            is_alive=False,
            pid=None,
            last_check=datetime.now()
        )
        
        self._running = False
        self._watch_task: Optional[asyncio.Task] = None
    
    def set_sentinel(
        self,
        process: multiprocessing.Process,
        factory: Callable
    ) -> None:
        """
        Define processo Sentinel para monitorar.
        
        Args:
            process: Processo atual do Sentinel
            factory: Função que cria novo processo Sentinel
        """
        self._sentinel_process = process
        self._sentinel_factory = factory
        self._health.pid = process.pid if process else None
    
    async def start(self) -> None:
        """Inicia monitoramento."""
        if self._running:
            return
        
        self._running = True
        self._watch_task = asyncio.create_task(self._watch_loop())
        logger.info("Watchdog iniciado")
    
    async def stop(self) -> None:
        """Para monitoramento."""
        self._running = False
        
        if self._watch_task:
            self._watch_task.cancel()
            try:
                await self._watch_task
            except asyncio.CancelledError:
                pass
        
        logger.info("Watchdog parado")
    
    async def _watch_loop(self) -> None:
        """Loop de monitoramento."""
        while self._running:
            try:
                self._check_health()
                
                if not self._health.is_alive:
                    await self._handle_dead_process()
                
                await asyncio.sleep(self.check_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Erro no watchdog: {e}")
                await asyncio.sleep(self.check_interval)
    
    def _check_health(self) -> None:
        """Verifica se processo está vivo."""
        self._health.last_check = datetime.now()
        
        if self._sentinel_process is None:
            self._health.is_alive = False
            return
        
        self._health.is_alive = self._sentinel_process.is_alive()
        self._health.pid = self._sentinel_process.pid if self._health.is_alive else None
    
    async def _handle_dead_process(self) -> None:
        """Trata processo morto."""
        if self._health.restart_count >= self.max_restarts:
            logger.error(
                f"Sentinel morreu {self.max_restarts} vezes. "
                "Máximo de reinícios atingido. Desistindo."
            )
            return
        
        # Cooldown entre reinícios
        if self._health.last_restart:
            elapsed = (datetime.now() - self._health.last_restart).total_seconds()
            if elapsed < self.restart_cooldown:
                remaining = self.restart_cooldown - elapsed
                logger.warning(f"Aguardando cooldown: {remaining:.1f}s")
                await asyncio.sleep(remaining)
        
        # Tenta reiniciar
        if self._sentinel_factory:
            try:
                logger.warning(
                    f"Sentinel morreu (PID anterior: {self._health.pid}). "
                    f"Reiniciando... (tentativa {self._health.restart_count + 1}/{self.max_restarts})"
                )
                
                # Cria novo processo
                new_process = self._sentinel_factory()
                new_process.start()
                
                self._sentinel_process = new_process
                self._health.restart_count += 1
                self._health.last_restart = datetime.now()
                self._health.pid = new_process.pid
                self._health.is_alive = True
                
                logger.info(f"Sentinel reiniciado. Novo PID: {new_process.pid}")
                
            except Exception as e:
                logger.error(f"Falha ao reiniciar Sentinel: {e}")
    
    def get_health(self) -> ProcessHealth:
        """Retorna status de saúde atual."""
        return self._health
    
    def is_healthy(self) -> bool:
        """Retorna True se Sentinel está saudável."""
        self._check_health()
        return self._health.is_alive


# Singleton
_watchdog: Optional[SentinelWatchdog] = None


def get_watchdog() -> SentinelWatchdog:
    """Retorna instância singleton do watchdog."""
    global _watchdog
    if _watchdog is None:
        _watchdog = SentinelWatchdog()
    return _watchdog


async def start_sentinel_with_watchdog(sentinel_factory: Callable) -> multiprocessing.Process:
    """
    Inicia Sentinel com monitoramento de watchdog.
    
    Args:
        sentinel_factory: Função que cria processo Sentinel
        
    Returns:
        Processo do Sentinel
    """
    process = sentinel_factory()
    process.start()
    
    watchdog = get_watchdog()
    watchdog.set_sentinel(process, sentinel_factory)
    await watchdog.start()
    
    return process

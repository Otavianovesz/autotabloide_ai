"""
AutoTabloide AI - Request Queue with Rate Limiting
====================================================
FASE 2 MOTOR SENTINELA: Fila de requisições com backoff exponencial.

Features:
- RequestQueue: Fila assíncrona com rate limiting
- Exponential Backoff: Retry automático em erros 429
- Circuit Breaker: Proteção contra cascata de falhas
"""

import asyncio
import logging
import time
from typing import Any, Callable, Optional, Dict, List
from dataclasses import dataclass, field
from enum import Enum
from collections import deque

logger = logging.getLogger("RequestQueue")


# ==============================================================================
# PASSO 25: REQUEST QUEUE COM EXPONENTIAL BACKOFF
# ==============================================================================

class RequestPriority(Enum):
    """Prioridades de requisição."""
    HIGH = 1
    NORMAL = 2
    LOW = 3


@dataclass
class RequestItem:
    """Item na fila de requisições."""
    id: str
    request_fn: Callable
    args: tuple = field(default_factory=tuple)
    kwargs: dict = field(default_factory=dict)
    priority: RequestPriority = RequestPriority.NORMAL
    max_retries: int = 3
    timeout: float = 15.0
    created_at: float = field(default_factory=time.time)
    
    # Estado de execução
    attempts: int = 0
    last_error: Optional[str] = None


@dataclass
class RequestResult:
    """Resultado de uma requisição."""
    id: str
    success: bool
    result: Any = None
    error: Optional[str] = None
    attempts: int = 0
    total_time_ms: float = 0.0


class CircuitState(Enum):
    """Estados do Circuit Breaker."""
    CLOSED = "closed"      # Normal, requisições passam
    OPEN = "open"          # Falhas demais, bloqueia requisições
    HALF_OPEN = "half_open"  # Testando se serviço voltou


class CircuitBreaker:
    """
    Circuit Breaker para proteção contra cascata de falhas.
    
    PROBLEMA: Se a API está fora, continuar tentando desperdiça recursos.
    SOLUÇÃO: Após N falhas consecutivas, para de tentar por um tempo.
    """
    
    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0,
        half_open_max_calls: int = 3
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.half_open_max_calls = half_open_max_calls
        
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._last_failure_time: Optional[float] = None
        self._half_open_calls = 0
    
    @property
    def state(self) -> CircuitState:
        """Retorna estado atual, verificando timeout de recuperação."""
        if self._state == CircuitState.OPEN:
            if self._last_failure_time and \
               time.time() - self._last_failure_time >= self.recovery_timeout:
                self._state = CircuitState.HALF_OPEN
                self._half_open_calls = 0
                logger.info("Circuit breaker: OPEN -> HALF_OPEN")
        return self._state
    
    def can_execute(self) -> bool:
        """Verifica se pode executar requisição."""
        state = self.state
        
        if state == CircuitState.CLOSED:
            return True
        elif state == CircuitState.HALF_OPEN:
            return self._half_open_calls < self.half_open_max_calls
        else:  # OPEN
            return False
    
    def record_success(self):
        """Registra sucesso."""
        if self.state == CircuitState.HALF_OPEN:
            self._half_open_calls += 1
            if self._half_open_calls >= self.half_open_max_calls:
                self._state = CircuitState.CLOSED
                self._failure_count = 0
                logger.info("Circuit breaker: HALF_OPEN -> CLOSED (recovered)")
        else:
            self._failure_count = 0
    
    def record_failure(self):
        """Registra falha."""
        self._failure_count += 1
        self._last_failure_time = time.time()
        
        if self._state == CircuitState.HALF_OPEN:
            self._state = CircuitState.OPEN
            logger.warning("Circuit breaker: HALF_OPEN -> OPEN (still failing)")
        elif self._failure_count >= self.failure_threshold:
            self._state = CircuitState.OPEN
            logger.warning(f"Circuit breaker: CLOSED -> OPEN (threshold reached: {self._failure_count})")


class RequestQueue:
    """
    Fila de requisições com rate limiting e exponential backoff.
    
    FASE 2 ITEM 25: Lida com erros 429 (Rate Limit) automaticamente.
    """
    
    def __init__(
        self,
        max_concurrent: int = 5,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        rate_limit_per_minute: int = 30
    ):
        self.max_concurrent = max_concurrent
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.rate_limit_per_minute = rate_limit_per_minute
        
        # Filas por prioridade
        self._queues: Dict[RequestPriority, deque] = {
            RequestPriority.HIGH: deque(),
            RequestPriority.NORMAL: deque(),
            RequestPriority.LOW: deque(),
        }
        
        # Estado
        self._active_requests = 0
        self._results: Dict[str, RequestResult] = {}
        self._lock = asyncio.Lock()
        
        # Rate limiting - tokens por minuto
        self._request_times: deque = deque(maxlen=rate_limit_per_minute)
        
        # Circuit breaker
        self._circuit = CircuitBreaker()
        
        # Workers
        self._running = False
        self._worker_task: Optional[asyncio.Task] = None
    
    def _calculate_backoff(self, attempt: int) -> float:
        """
        Calcula delay com exponential backoff.
        
        Fórmula: min(base * 2^attempt, max_delay)
        Exemplo: 1s, 2s, 4s, 8s, 16s, 32s, 60s...
        """
        delay = min(self.base_delay * (2 ** attempt), self.max_delay)
        # Adiciona jitter (±10%) para evitar thundering herd
        import random
        jitter = delay * 0.1 * (2 * random.random() - 1)
        return delay + jitter
    
    async def _wait_for_rate_limit(self):
        """Aguarda se rate limit foi atingido."""
        now = time.time()
        
        # Remove timestamps antigos (> 1 minuto)
        while self._request_times and now - self._request_times[0] > 60:
            self._request_times.popleft()
        
        # Se atingiu limite, espera
        if len(self._request_times) >= self.rate_limit_per_minute:
            wait_time = 60 - (now - self._request_times[0])
            if wait_time > 0:
                logger.info(f"Rate limit atingido, aguardando {wait_time:.1f}s")
                await asyncio.sleep(wait_time)
        
        # Registra esta requisição
        self._request_times.append(time.time())
    
    async def enqueue(
        self,
        request_fn: Callable,
        *args,
        request_id: Optional[str] = None,
        priority: RequestPriority = RequestPriority.NORMAL,
        max_retries: int = 3,
        timeout: float = 15.0,
        **kwargs
    ) -> str:
        """
        Enfileira requisição para execução.
        
        Args:
            request_fn: Função async a executar
            *args: Argumentos posicionais
            request_id: ID customizado (ou auto-gerado)
            priority: Prioridade da requisição
            max_retries: Máximo de tentativas
            timeout: Timeout por tentativa
            **kwargs: Argumentos nomeados
            
        Returns:
            ID da requisição
        """
        import uuid
        
        request_id = request_id or str(uuid.uuid4())
        
        item = RequestItem(
            id=request_id,
            request_fn=request_fn,
            args=args,
            kwargs=kwargs,
            priority=priority,
            max_retries=max_retries,
            timeout=timeout
        )
        
        async with self._lock:
            self._queues[priority].append(item)
        
        logger.debug(f"Requisição enfileirada: {request_id} (priority={priority.name})")
        return request_id
    
    async def execute_now(
        self,
        request_fn: Callable,
        *args,
        max_retries: int = 3,
        timeout: float = 15.0,
        **kwargs
    ) -> RequestResult:
        """
        Executa requisição imediatamente (sem enfileirar).
        Útil para requisições únicas.
        
        Returns:
            RequestResult com resultado ou erro
        """
        import uuid
        
        item = RequestItem(
            id=str(uuid.uuid4()),
            request_fn=request_fn,
            args=args,
            kwargs=kwargs,
            max_retries=max_retries,
            timeout=timeout
        )
        
        return await self._execute_with_retry(item)
    
    async def _execute_with_retry(self, item: RequestItem) -> RequestResult:
        """Executa item com retry e backoff."""
        start_time = time.time()
        
        while item.attempts < item.max_retries:
            # Verifica circuit breaker
            if not self._circuit.can_execute():
                logger.warning(f"Circuit breaker OPEN, rejeitando {item.id}")
                return RequestResult(
                    id=item.id,
                    success=False,
                    error="Circuit breaker open - service unavailable",
                    attempts=item.attempts
                )
            
            # Rate limiting
            await self._wait_for_rate_limit()
            
            item.attempts += 1
            
            try:
                # Executa com timeout
                result = await asyncio.wait_for(
                    item.request_fn(*item.args, **item.kwargs),
                    timeout=item.timeout
                )
                
                self._circuit.record_success()
                
                return RequestResult(
                    id=item.id,
                    success=True,
                    result=result,
                    attempts=item.attempts,
                    total_time_ms=(time.time() - start_time) * 1000
                )
                
            except asyncio.TimeoutError:
                item.last_error = f"Timeout após {item.timeout}s"
                logger.warning(f"Timeout na requisição {item.id} (tentativa {item.attempts})")
                
            except Exception as e:
                error_str = str(e)
                item.last_error = error_str
                
                # Detecta rate limit (429)
                is_rate_limit = "429" in error_str or "rate limit" in error_str.lower()
                
                if is_rate_limit:
                    logger.warning(f"Rate limit detectado em {item.id}")
                else:
                    self._circuit.record_failure()
                    logger.error(f"Erro na requisição {item.id}: {error_str}")
            
            # Backoff antes de retry
            if item.attempts < item.max_retries:
                delay = self._calculate_backoff(item.attempts)
                logger.info(f"Retry {item.id} em {delay:.1f}s (tentativa {item.attempts + 1})")
                await asyncio.sleep(delay)
        
        return RequestResult(
            id=item.id,
            success=False,
            error=item.last_error or "Max retries exceeded",
            attempts=item.attempts,
            total_time_ms=(time.time() - start_time) * 1000
        )
    
    async def get_result(self, request_id: str, timeout: float = 30.0) -> Optional[RequestResult]:
        """
        Aguarda e retorna resultado de uma requisição.
        
        Args:
            request_id: ID da requisição
            timeout: Tempo máximo de espera
            
        Returns:
            RequestResult ou None se timeout
        """
        start = time.time()
        
        while time.time() - start < timeout:
            if request_id in self._results:
                return self._results.pop(request_id)
            await asyncio.sleep(0.1)
        
        return None
    
    def get_queue_size(self) -> int:
        """Retorna número total de itens na fila."""
        return sum(len(q) for q in self._queues.values())
    
    def get_circuit_state(self) -> str:
        """Retorna estado do circuit breaker."""
        return self._circuit.state.value


# ==============================================================================
# CONVENIENCE FUNCTIONS
# ==============================================================================

# Singleton global
_request_queue: Optional[RequestQueue] = None


def get_request_queue() -> RequestQueue:
    """Retorna instância singleton da RequestQueue."""
    global _request_queue
    if _request_queue is None:
        _request_queue = RequestQueue()
    return _request_queue


async def execute_with_backoff(
    request_fn: Callable,
    *args,
    max_retries: int = 3,
    timeout: float = 15.0,
    **kwargs
) -> RequestResult:
    """
    Atalho para executar requisição com backoff.
    
    Args:
        request_fn: Função async a executar
        *args, **kwargs: Argumentos para a função
        max_retries: Máximo de tentativas
        timeout: Timeout por tentativa
        
    Returns:
        RequestResult
    """
    queue = get_request_queue()
    return await queue.execute_now(
        request_fn,
        *args,
        max_retries=max_retries,
        timeout=timeout,
        **kwargs
    )

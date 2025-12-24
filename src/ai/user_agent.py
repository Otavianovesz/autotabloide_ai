"""
AutoTabloide AI - User Agent Rotation
=======================================
Pool de User-Agents para requisições web.
Passo 97, 98 do Checklist 100.

Funcionalidades:
- Pool de User-Agents realistas
- Rotação automática
- Rate limiting básico
"""

import random
import time
from typing import List, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta

from src.core.logging_config import get_logger

logger = get_logger("UserAgent")


# ==============================================================================
# POOL DE USER AGENTS
# ==============================================================================

USER_AGENTS: List[str] = [
    # Chrome Windows
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
    
    # Chrome Mac
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    
    # Firefox Windows
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0",
    
    # Edge
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",
    
    # Safari
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_1) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15",
]


@dataclass
class RequestRecord:
    """Registro de requisição para rate limiting."""
    timestamp: datetime
    url_domain: str


class UserAgentManager:
    """
    Gerenciador de User-Agent com rotação.
    Passo 97 do Checklist - Rotação de User-Agent.
    """
    
    _instance: Optional["UserAgentManager"] = None
    
    def __new__(cls) -> "UserAgentManager":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if hasattr(self, '_initialized'):
            return
        self._initialized = True
        self._current_index = 0
        self._requests: List[RequestRecord] = []
        self._rate_limit_per_minute = 30
    
    def get_random(self) -> str:
        """Retorna User-Agent aleatório."""
        return random.choice(USER_AGENTS)
    
    def get_next(self) -> str:
        """Retorna próximo User-Agent em sequência."""
        ua = USER_AGENTS[self._current_index % len(USER_AGENTS)]
        self._current_index += 1
        return ua
    
    def get_for_domain(self, domain: str) -> str:
        """
        Retorna User-Agent para um domínio específico.
        Usa mesmo UA para o mesmo domínio (parece mais natural).
        """
        # Hash simples do domínio para selecionar UA
        domain_hash = hash(domain) % len(USER_AGENTS)
        return USER_AGENTS[domain_hash]
    
    def can_request(self, domain: str) -> bool:
        """
        Verifica se pode fazer requisição (rate limiting).
        Passo 98 do Checklist - Rate limiting.
        
        Args:
            domain: Domínio da requisição
            
        Returns:
            True se pode fazer requisição
        """
        now = datetime.now()
        minute_ago = now - timedelta(minutes=1)
        
        # Limpar registros antigos
        self._requests = [r for r in self._requests if r.timestamp > minute_ago]
        
        # Verificar limite global
        if len(self._requests) >= self._rate_limit_per_minute:
            logger.warning(f"Rate limit atingido ({self._rate_limit_per_minute}/min)")
            return False
        
        return True
    
    def record_request(self, domain: str) -> None:
        """Registra uma requisição feita."""
        self._requests.append(RequestRecord(
            timestamp=datetime.now(),
            url_domain=domain
        ))
    
    def wait_if_needed(self, domain: str) -> float:
        """
        Aguarda se necessário para respeitar rate limit.
        
        Args:
            domain: Domínio da requisição
            
        Returns:
            Tempo esperado em segundos
        """
        if self.can_request(domain):
            return 0.0
        
        # Calcula tempo até poder fazer próxima requisição
        if self._requests:
            oldest = min(r.timestamp for r in self._requests)
            wait_until = oldest + timedelta(minutes=1)
            wait_seconds = (wait_until - datetime.now()).total_seconds()
            
            if wait_seconds > 0:
                logger.info(f"Aguardando {wait_seconds:.1f}s para rate limit")
                time.sleep(wait_seconds)
                return wait_seconds
        
        return 0.0
    
    def set_rate_limit(self, requests_per_minute: int) -> None:
        """Define limite de requisições por minuto."""
        self._rate_limit_per_minute = max(1, requests_per_minute)
        logger.info(f"Rate limit definido: {self._rate_limit_per_minute}/min")


# Singleton
ua_manager = UserAgentManager()


def get_ua_manager() -> UserAgentManager:
    """Retorna singleton do UserAgentManager."""
    return ua_manager


def get_random_user_agent() -> str:
    """Atalho para obter User-Agent aleatório."""
    return ua_manager.get_random()

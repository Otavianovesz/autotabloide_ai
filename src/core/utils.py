"""
AutoTabloide AI - Utilitários Industriais
==========================================
Funções helper para normalização, slugify, retry e lifecycle.
Conforme Auditoria: Código resiliente e determinístico.
"""

from __future__ import annotations
import re
import asyncio
import unicodedata
from pathlib import Path
from typing import Callable, TypeVar, Optional, List, Any
from functools import wraps
from datetime import datetime
import hashlib
import shutil
import time

from .constants import UnitPatterns, RenderConfig
from .logging_config import get_logger

logger = get_logger("Utils")

T = TypeVar('T')


# ==============================================================================
# NORMALIZAÇÃO DE UNIDADES (Conforme Vol. IV)
# ==============================================================================

class UnitNormalizer:
    """
    Serviço de normalização de unidades de medida.
    
    Regras:
    - 'ml' sempre minúsculo
    - 'L' sempre maiúsculo (Regra do L)
    - 'kg', 'g' sempre minúsculo
    """
    
    @staticmethod
    def normalize(text: str) -> str:
        """
        Normaliza unidades no texto.
        
        Args:
            text: Texto com unidades
            
        Returns:
            Texto com unidades padronizadas
        """
        result = text
        
        for pattern, replacement in UnitPatterns.PATTERNS.items():
            result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)
        
        return result
    
    @staticmethod
    def extract_weight(text: str) -> Optional[str]:
        """
        Extrai peso/volume do texto.
        
        Args:
            text: Texto (ex: "Coca-Cola 2L Garrafa")
            
        Returns:
            Peso/volume extraído ou None
        """
        # Padrões de peso/volume
        patterns = [
            r'(\d+(?:[,.]\d+)?)\s*(ml|l|lt|litro|kg|g|un|pç|cx)',
            r'(\d+)\s*x\s*(\d+(?:[,.]\d+)?)\s*(ml|l|g)',  # Ex: 12x350ml
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return UnitNormalizer.normalize(match.group(0))
        
        return None


# ==============================================================================
# SLUGIFY (Nomes de Arquivo Seguros)
# ==============================================================================

def slugify(text: str, max_length: int = 100) -> str:
    """
    Converte texto em slug seguro para nomes de arquivo.
    
    Args:
        text: Texto original
        max_length: Comprimento máximo
        
    Returns:
        Slug seguro para NTFS e Linux
        
    Example:
        >>> slugify("Oferta/Verão 2024!")
        'oferta-verao-2024'
    """
    # 1. Normalizar unicode (remove acentos)
    text = unicodedata.normalize('NFKD', text)
    text = text.encode('ascii', 'ignore').decode('ascii')
    
    # 2. Minúsculo
    text = text.lower()
    
    # 3. Substituir espaços e caracteres inválidos por hífen
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[-\s]+', '-', text)
    
    # 4. Remover hífens no início/fim
    text = text.strip('-')
    
    # 5. Truncar
    if len(text) > max_length:
        text = text[:max_length].rsplit('-', 1)[0]
    
    return text or 'untitled'


def safe_filename(name: str, extension: str = '') -> str:
    """
    Gera nome de arquivo seguro com timestamp único.
    
    Args:
        name: Nome base
        extension: Extensão (com ou sem ponto)
        
    Returns:
        Nome de arquivo seguro e único
    """
    slug = slugify(name)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    ext = extension.lstrip('.') if extension else ''
    ext_part = f'.{ext}' if ext else ''
    
    return f"{slug}_{timestamp}{ext_part}"


# ==============================================================================
# RETRY COM EXPONENTIAL BACKOFF (Conforme Auditoria)
# ==============================================================================

class RetryConfig:
    """Configuração de retry."""
    MAX_ATTEMPTS = 3
    BASE_DELAY = 1.0  # segundos
    MAX_DELAY = 30.0  # segundos
    EXPONENTIAL_BASE = 2.0


def retry(
    max_attempts: int = RetryConfig.MAX_ATTEMPTS,
    base_delay: float = RetryConfig.BASE_DELAY,
    max_delay: float = RetryConfig.MAX_DELAY,
    exceptions: tuple = (Exception,),
    on_retry: Optional[Callable[[Exception, int], None]] = None
):
    """
    Decorator para retry com exponential backoff.
    
    Args:
        max_attempts: Número máximo de tentativas
        base_delay: Delay base em segundos
        max_delay: Delay máximo em segundos
        exceptions: Tuple de exceções para retry
        on_retry: Callback chamado a cada retry
        
    Usage:
        @retry(max_attempts=3, exceptions=(NetworkError,))
        def fetch_data():
            ...
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            last_exception = None
            
            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                    
                except exceptions as e:
                    last_exception = e
                    
                    if attempt == max_attempts:
                        logger.error(
                            f"Falha após {max_attempts} tentativas: {func.__name__}"
                        )
                        raise
                    
                    # Calcular delay exponencial
                    delay = min(
                        base_delay * (RetryConfig.EXPONENTIAL_BASE ** (attempt - 1)),
                        max_delay
                    )
                    
                    logger.warning(
                        f"Retry {attempt}/{max_attempts} para {func.__name__}, "
                        f"aguardando {delay:.1f}s: {e}"
                    )
                    
                    if on_retry:
                        on_retry(e, attempt)
                    
                    time.sleep(delay)
            
            raise last_exception
        
        return wrapper
    return decorator


def async_retry(
    max_attempts: int = RetryConfig.MAX_ATTEMPTS,
    base_delay: float = RetryConfig.BASE_DELAY,
    max_delay: float = RetryConfig.MAX_DELAY,
    exceptions: tuple = (Exception,)
):
    """
    Decorator para retry assíncrono com exponential backoff.
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            last_exception = None
            
            for attempt in range(1, max_attempts + 1):
                try:
                    return await func(*args, **kwargs)
                    
                except exceptions as e:
                    last_exception = e
                    
                    if attempt == max_attempts:
                        raise
                    
                    delay = min(
                        base_delay * (RetryConfig.EXPONENTIAL_BASE ** (attempt - 1)),
                        max_delay
                    )
                    
                    logger.warning(
                        f"Async retry {attempt}/{max_attempts}: {e}"
                    )
                    
                    await asyncio.sleep(delay)
            
            raise last_exception
        
        return wrapper
    return decorator


# ==============================================================================
# CANCELAMENTO DE OPERAÇÕES (CancellationToken)
# ==============================================================================

class CancellationToken:
    """
    Token para cancelamento gracioso de operações longas.
    
    Usage:
        token = CancellationToken()
        
        async def long_operation(token):
            for i in range(100):
                if token.is_cancelled:
                    return
                await process_item(i)
        
        # Para cancelar:
        token.cancel()
    """
    
    def __init__(self):
        self._cancelled = False
        self._event = asyncio.Event() if asyncio.get_event_loop().is_running() else None
    
    @property
    def is_cancelled(self) -> bool:
        """Verifica se foi cancelado."""
        return self._cancelled
    
    def cancel(self) -> None:
        """Solicita cancelamento."""
        self._cancelled = True
        if self._event:
            self._event.set()
    
    def reset(self) -> None:
        """Reseta o token para reuso."""
        self._cancelled = False
        if self._event:
            self._event.clear()
    
    def throw_if_cancelled(self) -> None:
        """Lança exceção se cancelado."""
        if self._cancelled:
            raise OperationCancelledError("Operação cancelada pelo usuário")


class OperationCancelledError(Exception):
    """Exceção para operação cancelada."""
    pass


# ==============================================================================
# LIFECYCLE MANAGER (Limpeza de Temp)
# ==============================================================================

class LifecycleManager:
    """
    Gerenciador de ciclo de vida da aplicação.
    
    Responsabilidades:
    - Limpeza de arquivos temporários
    - Gerenciamento de cache
    - Shutdown gracioso
    """
    
    def __init__(self, system_root: Path):
        self.root = Path(system_root)
        self.temp_dir = self.root / "temp"
        self._cleanup_handlers: List[Callable] = []
    
    def register_cleanup(self, handler: Callable) -> None:
        """Registra handler de cleanup para shutdown."""
        self._cleanup_handlers.append(handler)
    
    def cleanup_temp(self, max_age_hours: int = 24) -> int:
        """
        Remove arquivos temporários antigos.
        
        Args:
            max_age_hours: Idade máxima em horas
            
        Returns:
            Número de arquivos removidos
        """
        if not self.temp_dir.exists():
            return 0
        
        removed = 0
        now = datetime.now()
        max_age_seconds = max_age_hours * 3600
        
        for path in self.temp_dir.rglob('*'):
            if not path.is_file():
                continue
            
            try:
                age = now.timestamp() - path.stat().st_mtime
                if age > max_age_seconds:
                    path.unlink()
                    removed += 1
            except Exception as e:
                logger.debug(f"Falha ao remover {path}: {e}")
        
        if removed > 0:
            logger.info(f"Limpeza de temp: {removed} arquivos removidos")
        
        return removed
    
    def cleanup_cache(self, cache_dir: str, max_size_mb: int = 500) -> None:
        """
        Limpa cache mantendo tamanho máximo (LRU).
        
        Args:
            cache_dir: Subdiretório de cache
            max_size_mb: Tamanho máximo em MB
        """
        cache_path = self.root / cache_dir
        if not cache_path.exists():
            return
        
        max_bytes = max_size_mb * 1024 * 1024
        
        # Listar arquivos ordenados por data de acesso (mais antigo primeiro)
        files = sorted(
            cache_path.rglob('*'),
            key=lambda p: p.stat().st_atime if p.is_file() else float('inf')
        )
        
        total_size = sum(f.stat().st_size for f in files if f.is_file())
        
        while total_size > max_bytes and files:
            oldest = files.pop(0)
            if oldest.is_file():
                size = oldest.stat().st_size
                oldest.unlink()
                total_size -= size
                logger.debug(f"Cache LRU: removido {oldest.name}")
    
    def shutdown(self) -> None:
        """Executa shutdown gracioso."""
        logger.info("Iniciando shutdown...")
        
        # Executar handlers registrados
        for handler in self._cleanup_handlers:
            try:
                handler()
            except Exception as e:
                logger.error(f"Erro no cleanup handler: {e}")
        
        # Limpeza final de temp
        self.cleanup_temp(max_age_hours=0)  # Remove tudo
        
        logger.info("Shutdown concluído")


# ==============================================================================
# CONVERSÃO DE UNIDADES (mm ↔ pt ↔ px)
# ==============================================================================

class UnitConverter:
    """
    Conversor de unidades de medida.
    Centraliza conversões mm ↔ pt ↔ px.
    """
    
    @staticmethod
    def mm_to_pt(mm: float) -> float:
        """Milímetros para pontos tipográficos."""
        return RenderConfig.mm_to_pt(mm)
    
    @staticmethod
    def pt_to_mm(pt: float) -> float:
        """Pontos para milímetros."""
        return RenderConfig.pt_to_mm(pt)
    
    @staticmethod
    def mm_to_px(mm: float, dpi: int = 96) -> float:
        """Milímetros para pixels."""
        return RenderConfig.mm_to_px(mm, dpi)
    
    @staticmethod
    def px_to_mm(px: float, dpi: int = 96) -> float:
        """Pixels para milímetros."""
        return px * RenderConfig.MM_PER_INCH / dpi
    
    @staticmethod
    def pt_to_px(pt: float, dpi: int = 96) -> float:
        """Pontos para pixels."""
        return pt * dpi / RenderConfig.PT_PER_INCH
    
    @staticmethod
    def px_to_pt(px: float, dpi: int = 96) -> float:
        """Pixels para pontos."""
        return px * RenderConfig.PT_PER_INCH / dpi


# ==============================================================================
# HASH E CHECKSUM
# ==============================================================================

def compute_file_hash(file_path: Path, algorithm: str = 'sha256') -> str:
    """
    Calcula hash de arquivo.
    
    INDUSTRIAL ROBUSTNESS #107: Usa SHA-256 por padrão
    (mais seguro e sem colisões conhecidas vs MD5).
    
    Args:
        file_path: Caminho do arquivo
        algorithm: 'sha256' (padrão), 'md5', etc.
        
    Returns:
        Hash hexadecimal
    """
    hasher = hashlib.new(algorithm)
    
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            hasher.update(chunk)
    
    return hasher.hexdigest()


def compute_string_hash(text: str, algorithm: str = 'sha256') -> str:
    """
    Calcula hash de string.
    
    INDUSTRIAL ROBUSTNESS #107: Usa SHA-256 por padrão.
    """
    hasher = hashlib.new(algorithm)
    hasher.update(text.encode('utf-8'))
    return hasher.hexdigest()

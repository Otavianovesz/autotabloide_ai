"""
AutoTabloide AI - Memory Management
=====================================
Gerenciamento de memória e otimizações.
Passos 83, 91 do Checklist 100.

Funcionalidades:
- gc.collect após operações pesadas
- Monitoramento de uso de memória
- Limpeza de caches
"""

import gc
from typing import Optional
from functools import wraps

from src.core.logging_config import get_logger

logger = get_logger("Memory")

# Tentar importar psutil para monitoramento
try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False


class MemoryManager:
    """
    Gerenciador de memória da aplicação.
    Passo 83, 91 do Checklist.
    """
    
    _instance: Optional["MemoryManager"] = None
    
    def __new__(cls) -> "MemoryManager":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if hasattr(self, '_initialized'):
            return
        self._initialized = True
        self._operation_count = 0
        self._gc_threshold = 10  # Executar GC a cada N operações
    
    def get_memory_usage(self) -> dict:
        """
        Retorna uso de memória atual.
        Passo 83 - Profiling memória.
        
        Returns:
            Dict com métricas de memória
        """
        if not HAS_PSUTIL:
            return {"available": False}
        
        try:
            process = psutil.Process()
            mem_info = process.memory_info()
            
            return {
                "available": True,
                "rss_mb": mem_info.rss / (1024 * 1024),
                "vms_mb": mem_info.vms / (1024 * 1024),
                "percent": process.memory_percent(),
            }
        except Exception as e:
            logger.warning(f"Erro ao obter memória: {e}")
            return {"available": False, "error": str(e)}
    
    def collect_garbage(self, generation: int = 2) -> dict:
        """
        Força coleta de lixo.
        Passo 91 - gc.collect após lote.
        
        Args:
            generation: Geração a coletar (0, 1 ou 2)
            
        Returns:
            Estatísticas da coleta
        """
        before = self.get_memory_usage()
        
        # Coleta
        collected = gc.collect(generation)
        
        after = self.get_memory_usage()
        
        # Calcular economia
        freed_mb = 0
        if before.get("available") and after.get("available"):
            freed_mb = before["rss_mb"] - after["rss_mb"]
        
        logger.debug(f"GC: {collected} objetos coletados, {freed_mb:.1f}MB liberados")
        
        return {
            "objects_collected": collected,
            "freed_mb": freed_mb,
            "memory_after": after
        }
    
    def clear_caches(self) -> None:
        """
        Limpa caches da aplicação.
        """
        # Limpar cache de fontes do VectorEngine
        try:
            from src.rendering.vector import VectorEngine
            if hasattr(VectorEngine, '_font_cache'):
                VectorEngine._font_cache = {}
                logger.debug("Cache de fontes limpo")
        except Exception:
            pass
        
        # Limpar cache do ImageProcessor
        try:
            from src.ai.vision import ImageProcessor
            if hasattr(ImageProcessor, '_rembg_session'):
                ImageProcessor._rembg_session = None
                logger.debug("Sessão rembg liberada")
        except Exception:
            pass
    
    def after_batch_operation(self) -> None:
        """
        Chamado após operações em lote (renderização, importação).
        Passo 91 - gc.collect após lote.
        """
        self._operation_count += 1
        
        if self._operation_count >= self._gc_threshold:
            self.collect_garbage()
            self._operation_count = 0
    
    def force_cleanup(self) -> dict:
        """
        Executa limpeza completa de memória.
        Útil antes de operações pesadas.
        """
        self.clear_caches()
        result = self.collect_garbage(2)
        return result
    
    def log_memory_status(self) -> None:
        """Loga uso atual de memória."""
        usage = self.get_memory_usage()
        if usage.get("available"):
            logger.info(
                f"Memória: {usage['rss_mb']:.1f}MB RSS, "
                f"{usage['percent']:.1f}% do total"
            )


# Singleton
memory_manager = MemoryManager()


def get_memory_manager() -> MemoryManager:
    """Retorna singleton do MemoryManager."""
    return memory_manager


# ==============================================================================
# DECORATORS
# ==============================================================================

def with_gc_after(func):
    """
    Decorator que executa gc.collect após a função.
    
    Uso:
        @with_gc_after
        def render_batch(...):
            ...
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            result = func(*args, **kwargs)
            return result
        finally:
            memory_manager.after_batch_operation()
    
    return wrapper


def with_gc_after_async(func):
    """
    Decorator assíncrono que executa gc.collect após a função.
    """
    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            result = await func(*args, **kwargs)
            return result
        finally:
            memory_manager.after_batch_operation()
    
    return wrapper


# ==============================================================================
# CONTEXT MANAGER
# ==============================================================================

class MemoryContext:
    """
    Context manager para operações pesadas.
    
    Uso:
        with MemoryContext("Renderização"):
            # operações pesadas
            pass
    """
    
    def __init__(self, operation_name: str = "Operação"):
        self.operation_name = operation_name
        self._before: dict = {}
    
    def __enter__(self):
        self._before = memory_manager.get_memory_usage()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        result = memory_manager.collect_garbage()
        
        if self._before.get("available") and result["memory_after"].get("available"):
            delta = self._before["rss_mb"] - result["memory_after"]["rss_mb"]
            logger.info(f"{self.operation_name}: {delta:.1f}MB liberados")
        
        return False  # Não suprime exceções

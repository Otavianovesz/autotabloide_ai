"""
AutoTabloide AI - Lazy Import System
====================================
PROTOCOLO DE RETIFICAÇÃO NÍVEL 0 - Fase 6 (Passo 207)
Sistema de imports lazy para startup mais rápido.
"""

from __future__ import annotations
from typing import Any, Callable, Dict, Optional
from importlib import import_module
import logging

logger = logging.getLogger("LazyImports")


class LazyModule:
    """Módulo com import lazy."""
    
    def __init__(self, name: str):
        self._name = name
        self._module = None
    
    def _load(self):
        if self._module is None:
            self._module = import_module(self._name)
        return self._module
    
    def __getattr__(self, attr):
        return getattr(self._load(), attr)


class LazyImporter:
    """
    Sistema de imports lazy para acelerar startup.
    
    Usage:
        lazy = LazyImporter()
        lazy.register('PIL', 'PIL.Image')
        img = lazy.PIL.Image.open(...)
    """
    
    def __init__(self):
        self._modules: Dict[str, LazyModule] = {}
    
    def register(self, alias: str, module_name: str):
        """Registra módulo para import lazy."""
        self._modules[alias] = LazyModule(module_name)
    
    def __getattr__(self, name: str):
        if name in self._modules:
            return self._modules[name]
        raise AttributeError(f"Module {name} not registered")


# =============================================================================
# PRE-CONFIGURED LAZY IMPORTS
# =============================================================================

_lazy = LazyImporter()

# Heavy modules
_lazy.register("PIL", "PIL")
_lazy.register("numpy", "numpy")
_lazy.register("pandas", "pandas")
_lazy.register("cv2", "cv2")
_lazy.register("torch", "torch")
_lazy.register("rembg", "rembg")


def get_pil():
    """Lazy PIL import."""
    return _lazy.PIL


def get_numpy():
    """Lazy numpy import."""
    return _lazy.numpy


def get_pandas():
    """Lazy pandas import."""
    return _lazy.pandas


# =============================================================================
# IMPORT TIMING
# =============================================================================

_import_times: Dict[str, float] = {}


def timed_import(module_name: str) -> Any:
    """Import com timing para profiling."""
    import time
    start = time.perf_counter()
    
    module = import_module(module_name)
    
    elapsed = time.perf_counter() - start
    _import_times[module_name] = elapsed
    
    if elapsed > 0.1:  # Log imports lentos
        logger.warning(f"Slow import: {module_name} ({elapsed:.2f}s)")
    
    return module


def get_import_times() -> Dict[str, float]:
    """Retorna tempos de import."""
    return dict(_import_times)

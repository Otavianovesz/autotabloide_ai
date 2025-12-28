"""
AutoTabloide AI - File Watcher
==============================
PROTOCOLO DE RETIFICAÇÃO NÍVEL 0 - Fase 2 (Passo 42)
Monitoramento de diretórios de assets.
"""

from __future__ import annotations
from pathlib import Path
from typing import Set, Dict, Optional, Callable
import logging

from PySide6.QtCore import QObject, Signal, QFileSystemWatcher, QTimer

logger = logging.getLogger("FileWatcher")


class AssetWatcher(QObject):
    """
    Monitora diretórios de assets para mudanças.
    
    Features:
    - Detecta novos arquivos
    - Detecta remoções
    - Detecta modificações
    - Debounce para evitar spam
    """
    
    file_added = Signal(str)      # path
    file_removed = Signal(str)    # path
    file_modified = Signal(str)   # path
    directory_changed = Signal(str)  # dir path
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self._watcher = QFileSystemWatcher()
        self._watched_dirs: Set[str] = set()
        self._file_cache: Dict[str, float] = {}  # path -> mtime
        
        # Debounce timer
        self._debounce_timer = QTimer()
        self._debounce_timer.setSingleShot(True)
        self._debounce_timer.timeout.connect(self._process_changes)
        self._pending_dirs: Set[str] = set()
        
        # Conecta sinais
        self._watcher.directoryChanged.connect(self._on_dir_changed)
        self._watcher.fileChanged.connect(self._on_file_changed)
    
    def watch_directory(self, path: str, recursive: bool = False):
        """Adiciona diretório para monitoramento."""
        dir_path = Path(path)
        
        if not dir_path.exists():
            logger.warning(f"[Watcher] Diretório não existe: {path}")
            return
        
        # Adiciona ao watcher
        self._watcher.addPath(str(dir_path))
        self._watched_dirs.add(str(dir_path))
        
        # Cache arquivos existentes
        self._cache_directory(dir_path)
        
        # Recursivo
        if recursive:
            for subdir in dir_path.rglob("*"):
                if subdir.is_dir():
                    self._watcher.addPath(str(subdir))
                    self._watched_dirs.add(str(subdir))
        
        logger.info(f"[Watcher] Monitorando: {path}")
    
    def unwatch_directory(self, path: str):
        """Remove diretório do monitoramento."""
        if path in self._watched_dirs:
            self._watcher.removePath(path)
            self._watched_dirs.discard(path)
    
    def _cache_directory(self, dir_path: Path):
        """Cacheia arquivos do diretório."""
        for file_path in dir_path.iterdir():
            if file_path.is_file():
                try:
                    self._file_cache[str(file_path)] = file_path.stat().st_mtime
                except OSError:
                    pass
    
    def _on_dir_changed(self, path: str):
        """Callback quando diretório muda."""
        self._pending_dirs.add(path)
        # Debounce: espera 200ms antes de processar
        self._debounce_timer.start(200)
    
    def _on_file_changed(self, path: str):
        """Callback quando arquivo específico muda."""
        self.file_modified.emit(path)
    
    def _process_changes(self):
        """Processa mudanças pendentes."""
        for dir_path in self._pending_dirs:
            self._check_directory_changes(Path(dir_path))
        
        self._pending_dirs.clear()
    
    def _check_directory_changes(self, dir_path: Path):
        """Detecta mudanças em diretório."""
        if not dir_path.exists():
            return
        
        current_files = {}
        for file_path in dir_path.iterdir():
            if file_path.is_file():
                try:
                    current_files[str(file_path)] = file_path.stat().st_mtime
                except OSError:
                    pass
        
        # Detecta novos arquivos
        for path, mtime in current_files.items():
            if path not in self._file_cache:
                self.file_added.emit(path)
                logger.debug(f"[Watcher] Novo: {Path(path).name}")
        
        # Detecta removidos
        for path in list(self._file_cache.keys()):
            if Path(path).parent == dir_path and path not in current_files:
                self.file_removed.emit(path)
                del self._file_cache[path]
                logger.debug(f"[Watcher] Removido: {Path(path).name}")
        
        # Detecta modificados
        for path, mtime in current_files.items():
            if path in self._file_cache and self._file_cache[path] != mtime:
                self.file_modified.emit(path)
                logger.debug(f"[Watcher] Modificado: {Path(path).name}")
        
        # Atualiza cache
        self._file_cache.update(current_files)
        
        # Emite sinal de diretório
        self.directory_changed.emit(str(dir_path))
    
    def watch_image_formats(self) -> Set[str]:
        """Retorna extensões de imagem monitoradas."""
        return {".jpg", ".jpeg", ".png", ".webp", ".tiff", ".bmp"}


# =============================================================================
# SINGLETON
# =============================================================================

_instance: Optional[AssetWatcher] = None


def get_asset_watcher() -> AssetWatcher:
    """Acesso global ao watcher."""
    global _instance
    if _instance is None:
        _instance = AssetWatcher()
    return _instance


def watch_assets_directory(path: str, recursive: bool = True):
    """Helper para monitorar diretório de assets."""
    get_asset_watcher().watch_directory(path, recursive)

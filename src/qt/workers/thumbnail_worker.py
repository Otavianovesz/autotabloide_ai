"""
AutoTabloide AI - Thumbnail Worker
==================================
PROTOCOLO DE CONVERGÊNCIA 260 - Fase 2 (Passos 44-46)
Worker para carregamento assíncrono de thumbnails.
"""

from __future__ import annotations
from pathlib import Path
from typing import Dict, Optional
import logging

from PySide6.QtCore import QObject, Signal, QThread, QMutex, QMutexLocker, QSize
from PySide6.QtGui import QPixmap, QImage

logger = logging.getLogger("ThumbnailWorker")


class ThumbnailRequest:
    """Requisição de thumbnail."""
    def __init__(self, path: str, size: QSize, row: int):
        self.path = path
        self.size = size
        self.row = row


class ThumbnailWorker(QThread):
    """
    Worker para carregar thumbnails em background.
    Não trava a UI durante carregamento.
    """
    
    thumbnail_ready = Signal(int, QPixmap)  # row, pixmap
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._queue: list = []
        self._mutex = QMutex()
        self._running = True
        self._cache: Dict[str, QPixmap] = {}
        self._max_cache = 500
    
    def run(self):
        while self._running:
            request = None
            
            with QMutexLocker(self._mutex):
                if self._queue:
                    request = self._queue.pop(0)
            
            if request:
                pixmap = self._load_thumbnail(request)
                if pixmap and not pixmap.isNull():
                    self.thumbnail_ready.emit(request.row, pixmap)
            else:
                self.msleep(50)
    
    def _load_thumbnail(self, request: ThumbnailRequest) -> Optional[QPixmap]:
        """Carrega e redimensiona thumbnail."""
        # Verifica cache
        cache_key = f"{request.path}_{request.size.width()}x{request.size.height()}"
        
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        # Carrega imagem
        path = Path(request.path)
        
        if not path.exists():
            return None
        
        try:
            img = QImage(str(path))
            
            if img.isNull():
                return None
            
            # Redimensiona
            scaled = img.scaled(
                request.size,
                aspectMode=1,  # KeepAspectRatio
                transformMode=1  # SmoothTransformation
            )
            
            pixmap = QPixmap.fromImage(scaled)
            
            # Adiciona ao cache
            if len(self._cache) < self._max_cache:
                self._cache[cache_key] = pixmap
            
            return pixmap
            
        except Exception as e:
            logger.error(f"Thumbnail error: {e}")
            return None
    
    def request(self, path: str, size: QSize, row: int):
        """Adiciona requisição à fila."""
        with QMutexLocker(self._mutex):
            # Evita duplicatas
            for req in self._queue:
                if req.path == path and req.row == row:
                    return
            
            self._queue.append(ThumbnailRequest(path, size, row))
    
    def clear_queue(self):
        """Limpa fila."""
        with QMutexLocker(self._mutex):
            self._queue.clear()
    
    def clear_cache(self):
        """Limpa cache."""
        self._cache.clear()
    
    def stop(self):
        """Para worker."""
        self._running = False
        self.wait(2000)


class ThumbnailService(QObject):
    """Serviço de thumbnails singleton."""
    
    _instance: Optional['ThumbnailService'] = None
    
    thumbnail_ready = Signal(int, QPixmap)
    
    def __init__(self):
        super().__init__()
        self._worker = ThumbnailWorker()
        self._worker.thumbnail_ready.connect(self.thumbnail_ready.emit)
        self._worker.start()
    
    @classmethod
    def instance(cls) -> 'ThumbnailService':
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    def request(self, path: str, size: tuple, row: int):
        """Requisita thumbnail."""
        self._worker.request(path, QSize(*size), row)
    
    def clear(self):
        """Limpa fila e cache."""
        self._worker.clear_queue()
        self._worker.clear_cache()
    
    def shutdown(self):
        """Encerra serviço."""
        self._worker.stop()


def get_thumbnail_service() -> ThumbnailService:
    return ThumbnailService.instance()

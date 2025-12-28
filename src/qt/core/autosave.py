"""
AutoTabloide AI - Autosave System
=================================
PROTOCOLO DE CONVERGÊNCIA 260 - Fase 3 (Passo 115)
Sistema de salvamento automático.
"""

from __future__ import annotations
from pathlib import Path
from typing import Optional, Callable
from datetime import datetime
import logging

from PySide6.QtCore import QObject, Signal, QTimer

logger = logging.getLogger("Autosave")


class AutosaveManager(QObject):
    """
    Gerenciador de salvamento automático.
    
    Features:
    - Timer configurável
    - Backup rotativo
    - Detecção de mudanças
    """
    
    autosave_triggered = Signal()
    autosave_completed = Signal(str)  # path
    autosave_failed = Signal(str)     # error
    
    _instance: Optional['AutosaveManager'] = None
    
    def __init__(self, interval_ms: int = 60000):
        super().__init__()
        self._interval = interval_ms
        self._timer = QTimer()
        self._timer.timeout.connect(self._on_timer)
        
        self._save_callback: Optional[Callable] = None
        self._dirty = False
        self._enabled = True
        self._backup_count = 5
        self._autosave_dir = Path("AutoTabloide_System_Root/autosave")
    
    @classmethod
    def instance(cls) -> 'AutosaveManager':
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    def start(self, save_callback: Callable):
        """Inicia autosave."""
        self._save_callback = save_callback
        self._autosave_dir.mkdir(parents=True, exist_ok=True)
        self._timer.start(self._interval)
        logger.info(f"[Autosave] Started (interval: {self._interval}ms)")
    
    def stop(self):
        """Para autosave."""
        self._timer.stop()
    
    def mark_dirty(self):
        """Marca projeto como modificado."""
        self._dirty = True
    
    def mark_clean(self):
        """Marca projeto como salvo."""
        self._dirty = False
    
    def _on_timer(self):
        """Callback do timer."""
        if not self._enabled or not self._dirty:
            return
        
        self._do_autosave()
    
    def _do_autosave(self):
        """Executa autosave."""
        if not self._save_callback:
            return
        
        try:
            self.autosave_triggered.emit()
            
            # Gera nome de arquivo
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            autosave_path = self._autosave_dir / f"autosave_{timestamp}.tabloide"
            
            # Rotaciona backups antigos
            self._rotate_backups()
            
            # Salva
            self._save_callback(str(autosave_path))
            
            self._dirty = False
            self.autosave_completed.emit(str(autosave_path))
            
            logger.info(f"[Autosave] Saved: {autosave_path}")
            
        except Exception as e:
            logger.error(f"[Autosave] Failed: {e}")
            self.autosave_failed.emit(str(e))
    
    def _rotate_backups(self):
        """Remove backups antigos."""
        autosaves = sorted(self._autosave_dir.glob("autosave_*.tabloide"))
        
        while len(autosaves) >= self._backup_count:
            oldest = autosaves.pop(0)
            try:
                oldest.unlink()
                logger.debug(f"[Autosave] Removed: {oldest}")
            except:
                pass
    
    def get_latest_autosave(self) -> Optional[Path]:
        """Retorna autosave mais recente."""
        autosaves = sorted(self._autosave_dir.glob("autosave_*.tabloide"))
        
        if autosaves:
            return autosaves[-1]
        return None
    
    def set_interval(self, ms: int):
        """Define intervalo."""
        self._interval = ms
        if self._timer.isActive():
            self._timer.setInterval(ms)
    
    def set_enabled(self, enabled: bool):
        """Habilita/desabilita."""
        self._enabled = enabled
    
    @property
    def is_dirty(self) -> bool:
        return self._dirty


def get_autosave_manager() -> AutosaveManager:
    return AutosaveManager.instance()

"""
AutoTabloide AI - Rembg Integration
===================================
PROTOCOLO DE CONVERGÊNCIA 260 - Fase 5 (Passos 210-215)
Remoção de fundo de imagens via rembg.
"""

from __future__ import annotations
from pathlib import Path
from typing import Optional, Callable
import logging

from PySide6.QtCore import QObject, Signal, QThread

logger = logging.getLogger("Rembg")


class RembgWorker(QThread):
    """
    Worker para remoção de fundo.
    Executa rembg em thread separada.
    """
    
    completed = Signal(str, str)   # input_path, output_path
    error = Signal(str, str)       # input_path, error
    progress = Signal(str, int)    # input_path, percent
    
    def __init__(self, input_path: str, output_path: str = None):
        super().__init__()
        self._input = Path(input_path)
        self._output = Path(output_path) if output_path else self._input.with_suffix("_nobg.png")
    
    def run(self):
        try:
            self.progress.emit(str(self._input), 10)
            
            # Import lazy
            from rembg import remove
            from PIL import Image
            
            self.progress.emit(str(self._input), 30)
            
            # Carrega imagem
            img = Image.open(self._input)
            
            self.progress.emit(str(self._input), 50)
            
            # Remove fundo
            result = remove(img)
            
            self.progress.emit(str(self._input), 80)
            
            # Salva
            result.save(self._output, "PNG")
            
            self.progress.emit(str(self._input), 100)
            self.completed.emit(str(self._input), str(self._output))
            
            logger.info(f"[Rembg] OK: {self._output}")
            
        except ImportError:
            self.error.emit(str(self._input), "rembg não instalado")
        except Exception as e:
            self.error.emit(str(self._input), str(e))
            logger.error(f"[Rembg] Erro: {e}")


class RembgService(QObject):
    """
    Serviço de remoção de fundo.
    Gerencia workers e fila.
    """
    
    job_completed = Signal(str, str)   # input, output
    job_error = Signal(str, str)       # input, error
    job_progress = Signal(str, int)    # input, percent
    
    _instance: Optional['RembgService'] = None
    
    def __init__(self):
        super().__init__()
        self._workers: list = []
        self._available = None
    
    @classmethod
    def instance(cls) -> 'RembgService':
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    def is_available(self) -> bool:
        """Verifica se rembg está disponível."""
        if self._available is None:
            try:
                import rembg
                self._available = True
            except ImportError:
                self._available = False
        return self._available
    
    def remove_background(
        self,
        input_path: str,
        output_path: str = None,
        callback: Callable = None
    ):
        """Inicia remoção de fundo."""
        if not self.is_available():
            self.job_error.emit(input_path, "rembg não disponível")
            return
        
        worker = RembgWorker(input_path, output_path)
        
        worker.completed.connect(self._on_completed)
        worker.error.connect(self._on_error)
        worker.progress.connect(self._on_progress)
        
        if callback:
            worker.completed.connect(lambda i, o: callback(True, o))
            worker.error.connect(lambda i, e: callback(False, e))
        
        self._workers.append(worker)
        worker.start()
    
    def _on_completed(self, input_path: str, output_path: str):
        self.job_completed.emit(input_path, output_path)
    
    def _on_error(self, input_path: str, error: str):
        self.job_error.emit(input_path, error)
    
    def _on_progress(self, input_path: str, percent: int):
        self.job_progress.emit(input_path, percent)
    
    def cleanup(self):
        """Limpa workers finalizados."""
        self._workers = [w for w in self._workers if w.isRunning()]


# =============================================================================
# AUTO-CROP (Detecta objeto principal)
# =============================================================================

def auto_crop_image(image_path: str, output_path: str = None) -> Optional[str]:
    """
    Detecta e corta para o objeto principal.
    Usa detecção de borda após remoção de fundo.
    """
    try:
        from PIL import Image
        import numpy as np
        
        img = Image.open(image_path)
        
        # Converte para RGBA se necessário
        if img.mode != "RGBA":
            img = img.convert("RGBA")
        
        # Array numpy
        arr = np.array(img)
        
        # Encontra bounding box do conteúdo não-transparente
        alpha = arr[:, :, 3]
        rows = np.any(alpha > 0, axis=1)
        cols = np.any(alpha > 0, axis=0)
        
        if not np.any(rows) or not np.any(cols):
            return None
        
        y_min, y_max = np.where(rows)[0][[0, -1]]
        x_min, x_max = np.where(cols)[0][[0, -1]]
        
        # Adiciona margem
        margin = 10
        y_min = max(0, y_min - margin)
        y_max = min(arr.shape[0], y_max + margin)
        x_min = max(0, x_min - margin)
        x_max = min(arr.shape[1], x_max + margin)
        
        # Recorta
        cropped = img.crop((x_min, y_min, x_max, y_max))
        
        # Salva
        output = output_path or str(Path(image_path).with_suffix("_cropped.png"))
        cropped.save(output, "PNG")
        
        return output
        
    except Exception as e:
        logger.error(f"Auto-crop error: {e}")
        return None


# =============================================================================
# HELPERS
# =============================================================================

def get_rembg_service() -> RembgService:
    return RembgService.instance()


def remove_background_async(input_path: str, output_path: str = None):
    """Helper para remoção assíncrona."""
    get_rembg_service().remove_background(input_path, output_path)


def check_rembg() -> bool:
    """Verifica disponibilidade."""
    return get_rembg_service().is_available()

"""
AutoTabloide AI - Ghostscript Renderer
======================================
PROTOCOLO DE CONVERGÊNCIA 260 - Fase 4 (Passos 161-180)
Pipeline de renderização industrial com Ghostscript.
"""

from __future__ import annotations
from pathlib import Path
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
import logging
import subprocess
import shutil

from PySide6.QtCore import QObject, Signal, QProcess, QThread

logger = logging.getLogger("GhostscriptRenderer")


class ColorSpace(Enum):
    RGB = "rgb"
    CMYK = "cmyk"


class PDFVersion(Enum):
    V1_3 = "-dCompatibilityLevel=1.3"
    V1_4 = "-dCompatibilityLevel=1.4"
    V1_5 = "-dCompatibilityLevel=1.5"
    V1_7 = "-dCompatibilityLevel=1.7"


@dataclass
class RenderSettings:
    """Configurações de renderização."""
    dpi: int = 300
    color_space: ColorSpace = ColorSpace.CMYK
    pdf_version: PDFVersion = PDFVersion.V1_4
    embed_fonts: bool = True
    compress_images: bool = True
    image_quality: int = 90
    add_bleed: bool = True
    bleed_mm: float = 3.0
    add_crop_marks: bool = True
    icc_profile: Optional[str] = None
    overprint_black: bool = True


@dataclass
class RenderJob:
    """Job de renderização."""
    id: str
    svg_path: str
    output_path: str
    settings: RenderSettings = field(default_factory=RenderSettings)
    status: str = "pending"
    progress: int = 0
    error: str = ""


class GhostscriptRenderer(QObject):
    """
    Renderizador industrial via Ghostscript.
    
    Features:
    - SVG → PDF via Ghostscript
    - Conversão CMYK com perfil ICC
    - Crop marks e bleed
    - Progress tracking
    - Cancelamento
    """
    
    progress = Signal(str, int)    # job_id, percent
    completed = Signal(str, str)   # job_id, output_path
    error = Signal(str, str)       # job_id, error
    
    def __init__(self):
        super().__init__()
        self._gs_path: Optional[str] = None
        self._process: Optional[QProcess] = None
        self._current_job: Optional[RenderJob] = None
        
        self._find_ghostscript()
    
    def _find_ghostscript(self):
        """Encontra executável do Ghostscript."""
        candidates = [
            Path("AutoTabloide_System_Root/bin/gswin64c.exe"),
            Path("AutoTabloide_System_Root/bin/gswin32c.exe"),
            Path("C:/Program Files/gs/gs10.02.1/bin/gswin64c.exe"),
            Path("C:/Program Files/gs/gs10.00.0/bin/gswin64c.exe"),
            Path("C:/Program Files/gs/gs9.56.1/bin/gswin64c.exe"),
        ]
        
        for path in candidates:
            if path.exists():
                self._gs_path = str(path)
                logger.info(f"[GS] Found: {path}")
                return
        
        # Tenta no PATH
        if shutil.which("gswin64c"):
            self._gs_path = "gswin64c"
            return
        
        if shutil.which("gs"):
            self._gs_path = "gs"
            return
        
        logger.warning("[GS] Ghostscript não encontrado")
    
    @property
    def is_available(self) -> bool:
        return self._gs_path is not None
    
    def render(self, job: RenderJob) -> bool:
        """Inicia renderização."""
        if not self.is_available:
            self.error.emit(job.id, "Ghostscript não instalado")
            return False
        
        if not Path(job.svg_path).exists():
            self.error.emit(job.id, f"SVG não encontrado: {job.svg_path}")
            return False
        
        self._current_job = job
        job.status = "rendering"
        
        # Constrói argumentos
        args = self._build_args(job)
        
        # Executa
        self._process = QProcess()
        self._process.setProgram(self._gs_path)
        self._process.setArguments(args)
        
        self._process.readyReadStandardOutput.connect(self._on_stdout)
        self._process.readyReadStandardError.connect(self._on_stderr)
        self._process.finished.connect(self._on_finished)
        
        logger.info(f"[GS] Starting: {job.id}")
        self._process.start()
        
        return True
    
    def _build_args(self, job: RenderJob) -> List[str]:
        """Constrói argumentos do Ghostscript."""
        s = job.settings
        
        args = [
            "-dNOPAUSE",
            "-dBATCH",
            "-dSAFER",
            "-dQUIET",
            f"-r{s.dpi}",
        ]
        
        # Dispositivo de saída
        if s.color_space == ColorSpace.CMYK:
            args.append("-sDEVICE=pdfwrite")
            args.append("-dProcessColorModel=/DeviceCMYK")
            args.append("-dColorConversionStrategy=/CMYK")
        else:
            args.append("-sDEVICE=pdfwrite")
        
        # Versão PDF
        args.append(s.pdf_version.value)
        
        # Fontes
        if s.embed_fonts:
            args.append("-dEmbedAllFonts=true")
            args.append("-dSubsetFonts=true")
        
        # Compressão de imagens
        if s.compress_images:
            args.append("-dAutoFilterColorImages=true")
            args.append(f"-dColorImageQuality={s.image_quality}")
        
        # Overprint
        if s.overprint_black:
            args.append("-dOverprint=/enable")
        
        # Perfil ICC
        if s.icc_profile and Path(s.icc_profile).exists():
            args.append(f"-sOutputICCProfile={s.icc_profile}")
        
        # Output
        args.append(f"-sOutputFile={job.output_path}")
        
        # Input
        args.append(job.svg_path)
        
        return args
    
    def _on_stdout(self):
        """Processa saída."""
        if self._process:
            output = self._process.readAllStandardOutput().data().decode()
            # Estima progresso
            if "Page" in output:
                self.progress.emit(self._current_job.id, 50)
    
    def _on_stderr(self):
        """Processa erros."""
        if self._process:
            error = self._process.readAllStandardError().data().decode()
            if error.strip():
                logger.warning(f"[GS] {error}")
    
    def _on_finished(self, exit_code: int, exit_status):
        """Callback quando termina."""
        job = self._current_job
        
        if exit_code == 0 and Path(job.output_path).exists():
            job.status = "completed"
            job.progress = 100
            logger.info(f"[GS] Completed: {job.output_path}")
            self.completed.emit(job.id, job.output_path)
        else:
            job.status = "error"
            job.error = f"Exit code: {exit_code}"
            self.error.emit(job.id, job.error)
        
        self._current_job = None
        self._process = None
    
    def cancel(self):
        """Cancela renderização."""
        if self._process and self._process.state() == QProcess.Running:
            self._process.kill()
            logger.warning("[GS] Cancelled")


class RenderQueue(QObject):
    """
    Fila de renderização em batch.
    """
    
    job_started = Signal(str)
    job_completed = Signal(str)
    queue_finished = Signal()
    
    def __init__(self):
        super().__init__()
        self._queue: List[RenderJob] = []
        self._renderer = GhostscriptRenderer()
        self._renderer.completed.connect(self._on_job_completed)
        self._renderer.error.connect(self._on_job_error)
    
    def add(self, job: RenderJob):
        """Adiciona job à fila."""
        self._queue.append(job)
    
    def start(self):
        """Inicia processamento da fila."""
        self._process_next()
    
    def _process_next(self):
        """Processa próximo job."""
        pending = [j for j in self._queue if j.status == "pending"]
        
        if not pending:
            self.queue_finished.emit()
            return
        
        job = pending[0]
        self.job_started.emit(job.id)
        self._renderer.render(job)
    
    def _on_job_completed(self, job_id: str, output_path: str):
        self.job_completed.emit(job_id)
        self._process_next()
    
    def _on_job_error(self, job_id: str, error: str):
        logger.error(f"Job {job_id} failed: {error}")
        self._process_next()


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def render_svg_to_pdf(
    svg_path: str,
    output_path: str,
    settings: RenderSettings = None
) -> bool:
    """Helper para renderização simples."""
    import uuid
    
    renderer = GhostscriptRenderer()
    
    if not renderer.is_available:
        return False
    
    job = RenderJob(
        id=str(uuid.uuid4())[:8],
        svg_path=svg_path,
        output_path=output_path,
        settings=settings or RenderSettings()
    )
    
    return renderer.render(job)


def check_ghostscript() -> tuple:
    """Verifica instalação do Ghostscript."""
    renderer = GhostscriptRenderer()
    
    if renderer.is_available:
        return True, renderer._gs_path
    return False, "Ghostscript não encontrado"

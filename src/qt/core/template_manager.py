"""
AutoTabloide AI - Template Manager
==================================
PROTOCOLO DE RETIFICAÇÃO NÍVEL 0 - Fase 3 (Passos 21, 71-75)
Gerenciamento de templates SVG com thumbnails.
"""

from __future__ import annotations
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import logging
import hashlib

from PySide6.QtCore import Qt, Signal, QObject, QThread
from PySide6.QtGui import QPixmap, QPainter, QColor
from PySide6.QtWidgets import QWidget

logger = logging.getLogger("TemplateManager")


# =============================================================================
# TEMPLATE DATA
# =============================================================================

@dataclass
class TemplateInfo:
    """Informações de um template SVG."""
    path: str
    name: str
    width_mm: float = 297
    height_mm: float = 420
    slot_count: int = 0
    thumbnail_path: Optional[str] = None
    
    @property
    def size_text(self) -> str:
        if self.width_mm == 297 and self.height_mm == 420:
            return "A3"
        elif self.width_mm == 210 and self.height_mm == 297:
            return "A4"
        return f"{self.width_mm}x{self.height_mm}mm"


# =============================================================================
# THUMBNAIL GENERATOR
# =============================================================================

class ThumbnailGeneratorWorker(QThread):
    """Worker para gerar thumbnails em background."""
    
    thumbnail_ready = Signal(str, str)  # template_path, thumbnail_path
    progress = Signal(int, int)  # current, total
    finished = Signal()
    
    def __init__(self, templates: List[str], output_dir: Path, parent=None):
        super().__init__(parent)
        self.templates = templates
        self.output_dir = output_dir
        self._cancelled = False
    
    def run(self):
        self.output_dir.mkdir(parents=True, exist_ok=True)
        total = len(self.templates)
        
        for i, template_path in enumerate(self.templates):
            if self._cancelled:
                break
            
            try:
                thumb_path = self._generate_thumbnail(template_path)
                if thumb_path:
                    self.thumbnail_ready.emit(template_path, thumb_path)
            except Exception as e:
                logger.error(f"Erro ao gerar thumbnail: {e}")
            
            self.progress.emit(i + 1, total)
        
        self.finished.emit()
    
    def _generate_thumbnail(self, svg_path: str) -> Optional[str]:
        """Gera thumbnail de SVG."""
        from pathlib import Path
        
        # Hash para nome único
        file_hash = hashlib.md5(svg_path.encode()).hexdigest()[:8]
        thumb_path = self.output_dir / f"{file_hash}.png"
        
        # Se já existe, retorna
        if thumb_path.exists():
            return str(thumb_path)
        
        try:
            # Tenta usar QSvgRenderer
            from PySide6.QtSvg import QSvgRenderer
            
            renderer = QSvgRenderer(svg_path)
            if not renderer.isValid():
                return None
            
            # Cria pixmap 200x280 (proporção A3)
            pixmap = QPixmap(200, 280)
            pixmap.fill(Qt.white)
            
            painter = QPainter(pixmap)
            renderer.render(painter)
            painter.end()
            
            pixmap.save(str(thumb_path), "PNG")
            return str(thumb_path)
            
        except ImportError:
            logger.warning("QSvgRenderer não disponível")
            return None
    
    def cancel(self):
        self._cancelled = True


# =============================================================================
# TEMPLATE MANAGER
# =============================================================================

class TemplateManager(QObject):
    """
    Gerenciador de templates SVG.
    
    Features:
    - Indexação de templates
    - Geração de thumbnails
    - Cache de informações
    - Detecta slots automaticamente
    """
    
    templates_loaded = Signal(list)  # List[TemplateInfo]
    thumbnail_updated = Signal(str)  # template_path
    
    _instance: Optional['TemplateManager'] = None
    
    def __init__(self, library_dir: Path = None):
        super().__init__()
        
        self.library_dir = library_dir or Path("AutoTabloide_System_Root/library/svg_source")
        self.thumbnail_dir = library_dir.parent / "thumbnails" if library_dir else Path("AutoTabloide_System_Root/library/thumbnails")
        
        self._templates: Dict[str, TemplateInfo] = {}
        self._worker: Optional[ThumbnailGeneratorWorker] = None
    
    @classmethod
    def instance(cls) -> 'TemplateManager':
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    def scan_templates(self):
        """Escaneia diretório por templates."""
        if not self.library_dir.exists():
            logger.warning(f"Diretório de templates não existe: {self.library_dir}")
            return
        
        templates = []
        for svg_path in self.library_dir.glob("*.svg"):
            info = self._parse_template(svg_path)
            if info:
                self._templates[str(svg_path)] = info
                templates.append(info)
        
        logger.info(f"[Templates] {len(templates)} templates encontrados")
        self.templates_loaded.emit(templates)
        
        # Gera thumbnails em background
        if templates:
            self._generate_thumbnails([str(t.path) for t in templates])
    
    def _parse_template(self, path: Path) -> Optional[TemplateInfo]:
        """Extrai informações do template."""
        try:
            from src.qt.utils.svg_parser import SvgTemplateParser
            
            parser = SvgTemplateParser()
            template_def = parser.parse(str(path))
            
            return TemplateInfo(
                path=str(path),
                name=path.stem,
                width_mm=template_def.width_mm if template_def else 297,
                height_mm=template_def.height_mm if template_def else 420,
                slot_count=len(template_def.slots) if template_def else 0,
            )
        except Exception as e:
            logger.error(f"Erro ao parsear {path}: {e}")
            return TemplateInfo(
                path=str(path),
                name=path.stem,
            )
    
    def _generate_thumbnails(self, paths: List[str]):
        """Inicia geração de thumbnails em background."""
        if self._worker and self._worker.isRunning():
            return
        
        self._worker = ThumbnailGeneratorWorker(paths, self.thumbnail_dir)
        self._worker.thumbnail_ready.connect(self._on_thumbnail_ready)
        self._worker.start()
    
    def _on_thumbnail_ready(self, template_path: str, thumb_path: str):
        """Callback quando thumbnail é gerado."""
        if template_path in self._templates:
            self._templates[template_path].thumbnail_path = thumb_path
            self.thumbnail_updated.emit(template_path)
    
    def get_templates(self) -> List[TemplateInfo]:
        """Retorna lista de templates."""
        return list(self._templates.values())
    
    def get_template(self, path: str) -> Optional[TemplateInfo]:
        """Retorna info de um template específico."""
        return self._templates.get(path)
    
    def get_thumbnail(self, path: str) -> Optional[QPixmap]:
        """Retorna thumbnail de um template."""
        info = self._templates.get(path)
        if info and info.thumbnail_path:
            pixmap = QPixmap(info.thumbnail_path)
            if not pixmap.isNull():
                return pixmap
        return None


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_template_manager() -> TemplateManager:
    """Acesso global ao template manager."""
    return TemplateManager.instance()


def scan_templates():
    """Escaneia templates."""
    get_template_manager().scan_templates()

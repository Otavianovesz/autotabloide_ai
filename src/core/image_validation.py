"""
AutoTabloide AI - Image Validation Utilities
=============================================
PROTOCOLO DE RETIFICAÇÃO NÍVEL 0 - Fase 2 (Passos 41-45)
Validação de qualidade de imagens para impressão.
"""

from __future__ import annotations
from pathlib import Path
from typing import Dict, Tuple, Optional, List
from dataclasses import dataclass
from enum import Enum
import logging

from PIL import Image

logger = logging.getLogger("ImageValidation")


# =============================================================================
# QUALITY LEVELS
# =============================================================================

class ImageQuality(Enum):
    """Níveis de qualidade de imagem."""
    EXCELLENT = "excellent"    # >= 300 DPI equivalente
    GOOD = "good"              # >= 150 DPI
    ACCEPTABLE = "acceptable"  # >= 72 DPI
    LOW = "low"                # < 72 DPI
    INVALID = "invalid"        # Arquivo corrompido


QUALITY_COLORS = {
    ImageQuality.EXCELLENT: "#2ECC71",
    ImageQuality.GOOD: "#27AE60",
    ImageQuality.ACCEPTABLE: "#F39C12",
    ImageQuality.LOW: "#E74C3C",
    ImageQuality.INVALID: "#7F8C8D",
}


# =============================================================================
# VALIDATION RESULT
# =============================================================================

@dataclass
class ImageValidationResult:
    """Resultado da validação de imagem."""
    path: str
    valid: bool
    quality: ImageQuality
    width: int = 0
    height: int = 0
    format: str = ""
    mode: str = ""
    file_size_kb: int = 0
    has_alpha: bool = False
    is_cmyk: bool = False
    estimated_dpi: int = 0
    warnings: List[str] = None
    errors: List[str] = None
    
    def __post_init__(self):
        if self.warnings is None:
            self.warnings = []
        if self.errors is None:
            self.errors = []
    
    @property
    def quality_color(self) -> str:
        return QUALITY_COLORS.get(self.quality, "#808080")
    
    @property
    def resolution_text(self) -> str:
        return f"{self.width}×{self.height}" if self.valid else "?"
    
    @property
    def is_print_ready(self) -> bool:
        return self.quality in (ImageQuality.EXCELLENT, ImageQuality.GOOD)


# =============================================================================
# IMAGE VALIDATOR
# =============================================================================

class ImageValidator:
    """
    Valida imagens para uso em tabloides.
    
    Checks:
    - Formato suportado
    - Resolução mínima
    - Modo de cor (RGB/CMYK)
    - Tamanho de arquivo
    - Integridade
    """
    
    SUPPORTED_FORMATS = ["JPEG", "PNG", "WEBP", "TIFF", "BMP", "GIF"]
    
    # Tamanho de impressão típico em cm para estimar DPI
    TYPICAL_PRINT_SIZE_CM = 5.0
    
    # Limites
    MIN_DIMENSION = 50
    MAX_DIMENSION = 10000
    MAX_FILE_SIZE_MB = 50
    
    def validate(self, path: str, target_size_cm: float = None) -> ImageValidationResult:
        """
        Valida uma imagem.
        
        Args:
            path: Caminho da imagem
            target_size_cm: Tamanho de impressão esperado
            
        Returns:
            ImageValidationResult
        """
        target_size_cm = target_size_cm or self.TYPICAL_PRINT_SIZE_CM
        file_path = Path(path)
        
        # Verifica existência
        if not file_path.exists():
            return ImageValidationResult(
                path=str(file_path),
                valid=False,
                quality=ImageQuality.INVALID,
                errors=["Arquivo não encontrado"]
            )
        
        try:
            with Image.open(file_path) as img:
                # Informações básicas
                width, height = img.size
                format_name = img.format or "UNKNOWN"
                mode = img.mode
                file_size_kb = file_path.stat().st_size // 1024
                
                warnings = []
                errors = []
                
                # Verifica formato
                if format_name not in self.SUPPORTED_FORMATS:
                    warnings.append(f"Formato {format_name} pode ter problemas")
                
                # Verifica dimensões
                if width < self.MIN_DIMENSION or height < self.MIN_DIMENSION:
                    errors.append(f"Imagem muito pequena: {width}×{height}")
                
                if width > self.MAX_DIMENSION or height > self.MAX_DIMENSION:
                    warnings.append("Imagem muito grande, pode afetar performance")
                
                # Verifica tamanho do arquivo
                file_size_mb = file_size_kb / 1024
                if file_size_mb > self.MAX_FILE_SIZE_MB:
                    warnings.append(f"Arquivo muito grande: {file_size_mb:.1f}MB")
                
                # Calcula DPI estimado
                target_inches = target_size_cm / 2.54
                min_dim = min(width, height)
                estimated_dpi = int(min_dim / target_inches)
                
                # Determina qualidade
                if estimated_dpi >= 300:
                    quality = ImageQuality.EXCELLENT
                elif estimated_dpi >= 150:
                    quality = ImageQuality.GOOD
                elif estimated_dpi >= 72:
                    quality = ImageQuality.ACCEPTABLE
                    warnings.append(f"Resolução baixa para impressão: ~{estimated_dpi} DPI")
                else:
                    quality = ImageQuality.LOW
                    warnings.append(f"Resolução muito baixa: ~{estimated_dpi} DPI")
                
                # Verifica canal alpha
                has_alpha = mode in ("RGBA", "LA", "PA")
                
                # Verifica CMYK
                is_cmyk = mode == "CMYK"
                
                return ImageValidationResult(
                    path=str(file_path),
                    valid=len(errors) == 0,
                    quality=quality,
                    width=width,
                    height=height,
                    format=format_name,
                    mode=mode,
                    file_size_kb=file_size_kb,
                    has_alpha=has_alpha,
                    is_cmyk=is_cmyk,
                    estimated_dpi=estimated_dpi,
                    warnings=warnings,
                    errors=errors,
                )
                
        except Exception as e:
            logger.error(f"Erro ao validar {path}: {e}")
            return ImageValidationResult(
                path=str(file_path),
                valid=False,
                quality=ImageQuality.INVALID,
                errors=[f"Erro ao abrir: {str(e)}"]
            )
    
    def validate_batch(self, paths: List[str]) -> List[ImageValidationResult]:
        """Valida múltiplas imagens."""
        return [self.validate(p) for p in paths]
    
    def get_quality_summary(self, results: List[ImageValidationResult]) -> Dict:
        """Retorna resumo de qualidade."""
        summary = {
            "total": len(results),
            "valid": sum(1 for r in results if r.valid),
            "excellent": sum(1 for r in results if r.quality == ImageQuality.EXCELLENT),
            "good": sum(1 for r in results if r.quality == ImageQuality.GOOD),
            "acceptable": sum(1 for r in results if r.quality == ImageQuality.ACCEPTABLE),
            "low": sum(1 for r in results if r.quality == ImageQuality.LOW),
            "invalid": sum(1 for r in results if r.quality == ImageQuality.INVALID),
        }
        summary["print_ready"] = summary["excellent"] + summary["good"]
        return summary


# =============================================================================
# QUICK HELPERS
# =============================================================================

def validate_image(path: str) -> ImageValidationResult:
    """Validação rápida de uma imagem."""
    return ImageValidator().validate(path)


def is_print_ready(path: str) -> bool:
    """Verifica se imagem está pronta para impressão."""
    result = validate_image(path)
    return result.is_print_ready


def get_image_quality(path: str) -> ImageQuality:
    """Retorna qualidade da imagem."""
    return validate_image(path).quality


def estimate_dpi(path: str, target_size_cm: float = 5.0) -> int:
    """Estima DPI para tamanho de impressão."""
    return validate_image(path).estimated_dpi

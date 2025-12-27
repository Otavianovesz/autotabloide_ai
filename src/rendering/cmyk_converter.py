"""
AutoTabloide AI - CMYK Conversion System
==========================================
Conversão de imagens RGB para CMYK para impressão.
PROTOCOLO DE RETIFICAÇÃO: Passo 37 (Imagens CMYK na entrada).

Garante que imagens estejam em CMYK antes do PDF final.
"""

import logging
from pathlib import Path
from typing import Optional, Tuple, Dict, Any
from dataclasses import dataclass
from enum import Enum
import subprocess

logger = logging.getLogger("CMYKConverter")


class ColorSpace(Enum):
    """Espaços de cor."""
    RGB = "rgb"
    CMYK = "cmyk"
    GRAYSCALE = "grayscale"
    UNKNOWN = "unknown"


@dataclass
class ImageColorInfo:
    """Informações de cor de uma imagem."""
    colorspace: ColorSpace
    has_profile: bool
    profile_name: Optional[str] = None
    width: int = 0
    height: int = 0
    bit_depth: int = 8


class CMYKConverter:
    """
    Conversor de RGB para CMYK.
    
    PASSO 37: Converte imagens para CMYK antes da impressão.
    """
    
    # Perfis ICC padrão
    DEFAULT_RGB_PROFILE = "sRGB.icc"
    DEFAULT_CMYK_PROFILE = "CoatedFOGRA39.icc"
    
    def __init__(self, profiles_dir: Optional[Path] = None):
        self.profiles_dir = profiles_dir
        
        # Verificar disponibilidade de tools
        self._has_imagemagick = self._check_imagemagick()
        self._has_ghostscript = self._check_ghostscript()
    
    def _check_imagemagick(self) -> bool:
        """Verifica se ImageMagick está disponível."""
        try:
            result = subprocess.run(
                ["magick", "-version"],
                capture_output=True,
                timeout=5
            )
            return result.returncode == 0
        except Exception:
            return False
    
    def _check_ghostscript(self) -> bool:
        """Verifica se Ghostscript está disponível."""
        try:
            result = subprocess.run(
                ["gswin64c", "--version"],
                capture_output=True,
                timeout=5
            )
            return result.returncode == 0
        except Exception:
            return False
    
    def detect_colorspace(self, image_path: Path) -> ImageColorInfo:
        """
        Detecta espaço de cor de uma imagem.
        
        Args:
            image_path: Caminho da imagem
            
        Returns:
            ImageColorInfo
        """
        if not self._has_imagemagick:
            return ImageColorInfo(colorspace=ColorSpace.UNKNOWN, has_profile=False)
        
        try:
            result = subprocess.run(
                [
                    "magick", "identify",
                    "-format", "%[colorspace]|%[profile:icc]|%w|%h|%z",
                    str(image_path)
                ],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                parts = result.stdout.strip().split("|")
                
                colorspace_str = parts[0].lower() if len(parts) > 0 else ""
                profile = parts[1] if len(parts) > 1 and parts[1] else None
                width = int(parts[2]) if len(parts) > 2 and parts[2].isdigit() else 0
                height = int(parts[3]) if len(parts) > 3 and parts[3].isdigit() else 0
                depth = int(parts[4]) if len(parts) > 4 and parts[4].isdigit() else 8
                
                # Mapear colorspace
                if "cmyk" in colorspace_str:
                    cs = ColorSpace.CMYK
                elif "gray" in colorspace_str:
                    cs = ColorSpace.GRAYSCALE
                elif "srgb" in colorspace_str or "rgb" in colorspace_str:
                    cs = ColorSpace.RGB
                else:
                    cs = ColorSpace.UNKNOWN
                
                return ImageColorInfo(
                    colorspace=cs,
                    has_profile=profile is not None,
                    profile_name=profile,
                    width=width,
                    height=height,
                    bit_depth=depth
                )
                
        except Exception as e:
            logger.debug(f"Erro ao detectar colorspace: {e}")
        
        return ImageColorInfo(colorspace=ColorSpace.UNKNOWN, has_profile=False)
    
    def convert_to_cmyk(
        self,
        input_path: Path,
        output_path: Path,
        cmyk_profile: Optional[str] = None,
        rgb_profile: Optional[str] = None
    ) -> bool:
        """
        Converte imagem RGB para CMYK.
        
        Args:
            input_path: Caminho da imagem de entrada
            output_path: Caminho de saída
            cmyk_profile: Perfil CMYK a usar
            rgb_profile: Perfil RGB de entrada (se não embedded)
            
        Returns:
            True se conversão bem-sucedida
        """
        if not self._has_imagemagick:
            logger.error("ImageMagick não disponível para conversão CMYK")
            return False
        
        # Determinar perfis
        cmyk_profile = cmyk_profile or self.DEFAULT_CMYK_PROFILE
        rgb_profile = rgb_profile or self.DEFAULT_RGB_PROFILE
        
        # Construir caminho do perfil
        cmyk_profile_path = self._get_profile_path(cmyk_profile)
        rgb_profile_path = self._get_profile_path(rgb_profile)
        
        try:
            cmd = [
                "magick", str(input_path),
            ]
            
            # Se tem perfil RGB de entrada
            if rgb_profile_path and rgb_profile_path.exists():
                cmd.extend(["-profile", str(rgb_profile_path)])
            
            # Perfil CMYK de saída
            if cmyk_profile_path and cmyk_profile_path.exists():
                cmd.extend(["-profile", str(cmyk_profile_path)])
            else:
                # Conversão simples sem perfil
                cmd.extend(["-colorspace", "CMYK"])
            
            cmd.append(str(output_path))
            
            result = subprocess.run(cmd, capture_output=True, timeout=60)
            
            if result.returncode == 0:
                logger.info(f"Convertido para CMYK: {output_path.name}")
                return True
            else:
                logger.error(f"Erro na conversão: {result.stderr.decode()}")
                return False
                
        except Exception as e:
            logger.error(f"Falha na conversão CMYK: {e}")
            return False
    
    def _get_profile_path(self, profile_name: str) -> Optional[Path]:
        """Retorna caminho do perfil ICC."""
        if not self.profiles_dir:
            return None
        
        path = self.profiles_dir / profile_name
        if path.exists():
            return path
        
        return None
    
    def needs_conversion(self, image_path: Path) -> bool:
        """Verifica se imagem precisa de conversão para CMYK."""
        info = self.detect_colorspace(image_path)
        return info.colorspace != ColorSpace.CMYK
    
    def ensure_cmyk(
        self,
        image_path: Path,
        output_dir: Optional[Path] = None
    ) -> Tuple[Path, bool]:
        """
        Garante que imagem está em CMYK.
        
        Se já está em CMYK, retorna o caminho original.
        Se não está, converte e retorna novo caminho.
        
        Args:
            image_path: Caminho da imagem
            output_dir: Diretório para saída (se None, usa temp)
            
        Returns:
            Tuple (caminho_final, foi_convertido)
        """
        if not self.needs_conversion(image_path):
            return image_path, False
        
        # Gerar caminho de saída
        if output_dir is None:
            output_dir = image_path.parent
        
        output_path = output_dir / f"{image_path.stem}_cmyk.tiff"
        
        if self.convert_to_cmyk(image_path, output_path):
            return output_path, True
        
        return image_path, False


# ==============================================================================
# CAMYK BATCH PROCESSOR
# ==============================================================================

class CMYKBatchProcessor:
    """Processador em lote para múltiplas imagens."""
    
    def __init__(self, converter: CMYKConverter):
        self.converter = converter
    
    def process_directory(
        self,
        input_dir: Path,
        output_dir: Path,
        extensions: Tuple[str, ...] = (".jpg", ".jpeg", ".png", ".tiff")
    ) -> Dict[str, int]:
        """
        Converte todas as imagens RGB de um diretório.
        
        Returns:
            Dict com estatísticas
        """
        stats = {
            "total": 0,
            "converted": 0,
            "already_cmyk": 0,
            "failed": 0
        }
        
        output_dir.mkdir(parents=True, exist_ok=True)
        
        for file_path in input_dir.iterdir():
            if file_path.suffix.lower() in extensions:
                stats["total"] += 1
                
                if not self.converter.needs_conversion(file_path):
                    stats["already_cmyk"] += 1
                    continue
                
                output_path = output_dir / f"{file_path.stem}_cmyk.tiff"
                
                if self.converter.convert_to_cmyk(file_path, output_path):
                    stats["converted"] += 1
                else:
                    stats["failed"] += 1
        
        return stats


# ==============================================================================
# INSTÂNCIA GLOBAL
# ==============================================================================

_converter: Optional[CMYKConverter] = None


def get_cmyk_converter(profiles_dir: Optional[Path] = None) -> CMYKConverter:
    """Retorna instância global do conversor."""
    global _converter
    
    if _converter is None:
        if profiles_dir is None:
            from src.core.constants import SYSTEM_ROOT
            profiles_dir = SYSTEM_ROOT / "library" / "icc"
        
        _converter = CMYKConverter(profiles_dir)
    
    return _converter


def ensure_cmyk(image_path: str) -> Tuple[str, bool]:
    """Função de conveniência para garantir CMYK."""
    converter = get_cmyk_converter()
    result_path, converted = converter.ensure_cmyk(Path(image_path))
    return str(result_path), converted

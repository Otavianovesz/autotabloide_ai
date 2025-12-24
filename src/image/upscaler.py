"""
AutoTabloide AI - Real-ESRGAN Image Upscaler
=============================================
Implementação conforme Vol. IV, Cap. 3.1.

Upscaling de imagens usando Real-ESRGAN para melhorar qualidade
de imagens com resolução insuficiente.
"""

import os
import logging
import subprocess
import tempfile
from pathlib import Path
from typing import Optional, Tuple
import shutil

logger = logging.getLogger("Upscaler")


class UpscalerConfig:
    """Configuração do upscaler."""
    MIN_DIMENSION_TRIGGER = 800  # Ativa upscaling se < 800px em qualquer dimensão
    DEFAULT_SCALE = 4           # Fator de escala padrão
    FALLBACK_SCALE = 2          # Fallback para GPU fraca
    SUPPORTED_FORMATS = ['.jpg', '.jpeg', '.png', '.webp']


class RealESRGANUpscaler:
    """
    Upscaler de imagens usando Real-ESRGAN.
    
    Requisitos:
    - Binário realesrgan-ncnn-vulkan em BIN_DIR
    - Modelo realesrgan-x4plus na pasta de modelos
    
    Ref: Vol. IV, Cap. 3.1
    """
    
    def __init__(self, bin_dir: Path = None):
        self.bin_dir = bin_dir or Path(__file__).parent.parent / "AutoTabloide_System_Root" / "bin"
        self.executable = self._find_executable()
        self.model_dir = self.bin_dir / "models"
        self._available = self._check_availability()
    
    def _find_executable(self) -> Optional[Path]:
        """Encontra o executável do Real-ESRGAN."""
        possible_names = [
            "realesrgan-ncnn-vulkan.exe",  # Windows
            "realesrgan-ncnn-vulkan",       # Linux/macOS
            "realesrgan.exe",
            "realesrgan"
        ]
        
        for name in possible_names:
            path = self.bin_dir / name
            if path.exists():
                return path
        
        # Tenta no PATH do sistema
        for name in possible_names:
            if shutil.which(name):
                return Path(shutil.which(name))
        
        return None
    
    def _check_availability(self) -> bool:
        """Verifica se Real-ESRGAN está disponível."""
        if self.executable is None:
            logger.warning("Real-ESRGAN não encontrado. Upscaling desativado.")
            return False
        
        if not self.executable.exists():
            logger.warning(f"Executável não existe: {self.executable}")
            return False
        
        return True
    
    @property
    def is_available(self) -> bool:
        return self._available
    
    def should_upscale(self, image_path: str) -> bool:
        """
        Determina se imagem precisa de upscaling.
        
        Critério: Qualquer dimensão < MIN_DIMENSION_TRIGGER
        """
        try:
            from PIL import Image
            
            with Image.open(image_path) as img:
                width, height = img.size
                
                needs_upscale = (
                    width < UpscalerConfig.MIN_DIMENSION_TRIGGER or
                    height < UpscalerConfig.MIN_DIMENSION_TRIGGER
                )
                
                if needs_upscale:
                    logger.debug(
                        f"Upscaling necessário: {width}x{height} < {UpscalerConfig.MIN_DIMENSION_TRIGGER}px"
                    )
                
                return needs_upscale
                
        except Exception as e:
            logger.error(f"Erro ao verificar dimensões: {e}")
            return False
    
    def upscale(
        self,
        input_path: str,
        output_path: str = None,
        scale: int = None,
        model: str = "realesrgan-x4plus",
        denoise: int = 0
    ) -> Tuple[bool, str]:
        """
        Executa upscaling de imagem.
        
        Args:
            input_path: Caminho da imagem de entrada
            output_path: Caminho de saída (se None, sobrescreve entrada)
            scale: Fator de escala (2 ou 4)
            model: Modelo a usar
            denoise: Nível de denoise (0-3)
        
        Returns:
            Tuple[sucesso, caminho_saída_ou_erro]
        """
        if not self._available:
            return (False, "Real-ESRGAN não disponível")
        
        input_path = Path(input_path)
        
        if not input_path.exists():
            return (False, f"Arquivo não encontrado: {input_path}")
        
        if input_path.suffix.lower() not in UpscalerConfig.SUPPORTED_FORMATS:
            return (False, f"Formato não suportado: {input_path.suffix}")
        
        # Define saída
        if output_path is None:
            # Cria arquivo temporário, depois substitui
            with tempfile.NamedTemporaryFile(
                suffix=input_path.suffix,
                delete=False
            ) as tmp:
                output_path = tmp.name
                replace_original = True
        else:
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            replace_original = False
        
        # Escala
        scale = scale or UpscalerConfig.DEFAULT_SCALE
        
        # Monta comando
        cmd = [
            str(self.executable),
            "-i", str(input_path),
            "-o", str(output_path),
            "-s", str(scale),
            "-n", model
        ]
        
        if denoise > 0:
            # Modelo com denoise
            cmd.extend(["-n", f"realesrgan-x4plus-anime"])  # Alternativa com denoise
        
        if self.model_dir.exists():
            cmd.extend(["-m", str(self.model_dir)])
        
        try:
            logger.info(f"Executando upscaling: {input_path.name} (x{scale})")
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=120  # 2 min timeout
            )
            
            if result.returncode != 0:
                error = result.stderr or result.stdout or "Erro desconhecido"
                logger.error(f"Real-ESRGAN falhou: {error}")
                return (False, error)
            
            # Verifica se arquivo foi criado
            if not Path(output_path).exists():
                return (False, "Arquivo de saída não foi criado")
            
            # Substitui original se necessário
            if replace_original:
                shutil.move(output_path, input_path)
                output_path = str(input_path)
            
            logger.info(f"Upscaling concluído: {output_path}")
            return (True, str(output_path))
            
        except subprocess.TimeoutExpired:
            logger.error("Timeout no upscaling")
            return (False, "Timeout - imagem muito grande ou GPU lenta")
        except Exception as e:
            logger.error(f"Erro no upscaling: {e}")
            return (False, str(e))
    
    def upscale_if_needed(self, image_path: str) -> Tuple[bool, str]:
        """
        Faz upscaling apenas se necessário.
        
        Returns:
            Tuple[foi_upscalado, caminho_ou_erro]
        """
        if not self.should_upscale(image_path):
            return (False, image_path)  # Já está ok
        
        return self.upscale(image_path)
    
    def upscale_batch(
        self,
        image_paths: list,
        output_dir: str = None,
        scale: int = None
    ) -> list:
        """
        Processa múltiplas imagens em batch.
        
        Returns:
            Lista de Tuple[input, sucesso, output_ou_erro]
        """
        results = []
        
        for path in image_paths:
            if output_dir:
                out_path = Path(output_dir) / Path(path).name
            else:
                out_path = None
            
            success, result = self.upscale(path, out_path, scale)
            results.append((path, success, result))
        
        return results


# Singleton
_upscaler: Optional[RealESRGANUpscaler] = None


def get_upscaler() -> RealESRGANUpscaler:
    """Obtém instância singleton do upscaler."""
    global _upscaler
    if _upscaler is None:
        _upscaler = RealESRGANUpscaler()
    return _upscaler


def upscale_image_if_needed(image_path: str) -> str:
    """
    Convenience function para upscaling condicional.
    
    Returns:
        Caminho da imagem (original ou upscalada)
    """
    upscaler = get_upscaler()
    
    if not upscaler.is_available:
        return image_path
    
    success, result = upscaler.upscale_if_needed(image_path)
    
    if success:
        return result
    
    return image_path

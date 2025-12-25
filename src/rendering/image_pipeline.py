"""
AutoTabloide AI - Pipeline de Processamento de Imagem
=======================================================
Processamento avançado conforme Vol. IV, Cap. 3-4.
Remoção de fundo, upscaling, avaliação de qualidade.
"""

import os
import subprocess
import hashlib
import logging
import shutil
from pathlib import Path
from typing import Optional, Tuple
from enum import Enum

# Imports opcionais para funcionalidades avançadas
try:
    from rembg import remove as rembg_remove
    from PIL import Image
    HAS_REMBG = True
except ImportError:
    HAS_REMBG = False

try:
    import cv2
    import numpy as np
    HAS_OPENCV = True
except ImportError:
    HAS_OPENCV = False

logger = logging.getLogger("ImagePipeline")


class QualityLevel(str, Enum):
    """Níveis de qualidade de imagem conforme Vol. IV, Tab. 3.1"""
    EXCELLENT = "EXCELLENT"    # BRISQUE < 20
    GOOD = "GOOD"             # BRISQUE 20-40
    ACCEPTABLE = "ACCEPTABLE"  # BRISQUE 40-60
    POOR = "POOR"             # BRISQUE > 60


class ImagePipeline:
    """
    Pipeline de Processamento de Imagem Industrial.
    Conforme Vol. IV - Integração com ferramentas de IA visual.
    
    Features:
    - Remoção de fundo (rembg/U2-Net)
    - Upscaling 4x (Real-ESRGAN NCNN)
    - Avaliação de qualidade (BRISQUE simplificado)
    - Smart Crop via saliência
    """
    
    def __init__(self, system_root: str):
        self.system_root = Path(system_root)
        self.bin_dir = self.system_root / "bin"
        self.staging_dir = self.system_root / "staging" / "images"
        self.vault_dir = self.system_root / "vault" / "images"
        
        # Cria diretórios se não existirem
        os.makedirs(self.staging_dir, exist_ok=True)
        os.makedirs(self.vault_dir, exist_ok=True)
        
        # Localiza binário do Real-ESRGAN
        self.esrgan_path = self._find_esrgan()
        
        self._verify_dependencies()

    def _find_esrgan(self) -> Optional[str]:
        """Localiza executável do Real-ESRGAN."""
        candidates = [
            self.bin_dir / "realesrgan-ncnn-vulkan.exe",
            self.bin_dir / "realesrgan-ncnn-vulkan",
        ]
        
        for path in candidates:
            if path.exists():
                return str(path)
        
        # Tenta no PATH
        esrgan = shutil.which("realesrgan-ncnn-vulkan")
        return esrgan

    def _verify_dependencies(self):
        """Verifica dependências disponíveis."""
        status = {
            "rembg": HAS_REMBG,
            "opencv": HAS_OPENCV,
            "esrgan": self.esrgan_path is not None
        }
        
        logger.info(f"ImagePipeline dependencies: {status}")
        
        if not any(status.values()):
            logger.warning(
                "Nenhuma ferramenta de processamento de imagem disponivel. "
                "Instale: pip install rembg opencv-python"
            )

    # ==========================================================================
    # REMOÇÃO DE FUNDO (rembg)
    # ==========================================================================

    def remove_background(
        self, 
        input_path: str, 
        output_path: Optional[str] = None,
        alpha_matting: bool = False
    ) -> str:
        """
        Remove fundo de imagem usando U2-Net via rembg.
        
        Args:
            input_path: Caminho da imagem original
            output_path: Caminho de saída (None = gera automaticamente)
            alpha_matting: Usa alpha matting para bordas mais suaves
            
        Returns:
            Caminho da imagem processada (PNG com transparência)
        """
        if not HAS_REMBG:
            raise ImportError(
                "rembg nao instalado. Execute: pip install rembg[gpu]"
            )
        
        input_path = Path(input_path)
        if not input_path.exists():
            raise FileNotFoundError(f"Imagem nao encontrada: {input_path}")
        
        # Gera output path se não especificado
        if output_path is None:
            output_path = str(self.staging_dir / f"{input_path.stem}_nobg.png")
        
        try:
            # Abre imagem
            with Image.open(input_path) as img:
                # Remove fundo
                output = rembg_remove(
                    img,
                    alpha_matting=alpha_matting,
                    alpha_matting_foreground_threshold=240,
                    alpha_matting_background_threshold=10
                )
                
                # Salva como PNG (mantém transparência)
                output.save(output_path, "PNG")
            
            logger.info(f"Fundo removido: {input_path} -> {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Erro ao remover fundo: {e}")
            raise

    # ==========================================================================
    # UPSCALING (Real-ESRGAN)
    # ==========================================================================

    def upscale(
        self, 
        input_path: str, 
        scale: int = 4,
        output_path: Optional[str] = None,
        model: str = "realesrgan-x4plus"
    ) -> str:
        """
        Aumenta resolução de imagem usando Real-ESRGAN.
        
        Args:
            input_path: Caminho da imagem original
            scale: Fator de escala (2, 3 ou 4)
            output_path: Caminho de saída
            model: Modelo a usar (realesrgan-x4plus, realesrgan-x4plus-anime)
            
        Returns:
            Caminho da imagem ampliada
        """
        if not self.esrgan_path:
            raise RuntimeError(
                "Real-ESRGAN nao encontrado. "
                "Baixe de: https://github.com/xinntao/Real-ESRGAN-ncnn-vulkan"
            )
        
        input_path = Path(input_path)
        if not input_path.exists():
            raise FileNotFoundError(f"Imagem nao encontrada: {input_path}")
        
        # Gera output path
        if output_path is None:
            output_path = str(self.staging_dir / f"{input_path.stem}_x{scale}.png")
        
        # Monta comando
        cmd = [
            self.esrgan_path,
            "-i", str(input_path),
            "-o", output_path,
            "-s", str(scale),
            "-n", model
        ]
        
        try:
            startupinfo = None
            if os.name == 'nt':
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            
            result = subprocess.run(
                cmd,
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                startupinfo=startupinfo,
                timeout=120  # 2 minutos timeout
            )
            
            logger.info(f"Upscale {scale}x concluido: {output_path}")
            return output_path
            
        except subprocess.TimeoutExpired:
            raise RuntimeError("Timeout no upscaling (>2min)")
        except subprocess.CalledProcessError as e:
            logger.error(f"Erro no Real-ESRGAN: {e.stderr}")
            raise RuntimeError(f"Falha no upscaling: {e.stderr}")

    # ==========================================================================
    # AVALIAÇÃO DE QUALIDADE (BRISQUE simplificado)
    # ==========================================================================

    def calculate_quality_score(self, input_path: str) -> Tuple[float, QualityLevel]:
        """
        Calcula score de qualidade da imagem.
        
        Usa BRISQUE simplificado (Blind/Referenceless Image Spatial Quality Evaluator).
        Quanto MENOR o score, MELHOR a qualidade.
        
        Args:
            input_path: Caminho da imagem
            
        Returns:
            Tuple (score numérico, nível de qualidade)
        """
        if not HAS_OPENCV:
            # Fallback: verifica apenas resolução
            return self._quality_by_resolution(input_path)
        
        try:
            # Carrega imagem em escala de cinza
            img = cv2.imread(str(input_path), cv2.IMREAD_GRAYSCALE)
            if img is None:
                raise ValueError(f"Nao foi possivel carregar: {input_path}")
            
            # Calcula Laplaciano (medida de nitidez)
            laplacian = cv2.Laplacian(img, cv2.CV_64F)
            variance = laplacian.var()
            
            # Converte variância para score similar a BRISQUE
            # Maior variância = mais detalhes = melhor qualidade
            # BRISQUE típico: 0-100, menor é melhor
            if variance > 1000:
                score = 10.0  # Muito nítido
            elif variance > 500:
                score = 30.0  # Bom
            elif variance > 100:
                score = 50.0  # Aceitável
            else:
                score = 75.0  # Borrado
            
            # Classifica
            level = self._score_to_level(score)
            
            logger.debug(f"Qualidade {input_path}: score={score:.1f}, level={level.value}")
            return score, level
            
        except Exception as e:
            logger.error(f"Erro ao calcular qualidade: {e}")
            return 50.0, QualityLevel.ACCEPTABLE

    def _quality_by_resolution(self, input_path: str) -> Tuple[float, QualityLevel]:
        """Fallback: avalia qualidade por resolução."""
        try:
            with Image.open(input_path) as img:
                width, height = img.size
                min_dimension = min(width, height)
                
                if min_dimension >= 1200:
                    return 15.0, QualityLevel.EXCELLENT
                elif min_dimension >= 800:
                    return 35.0, QualityLevel.GOOD
                elif min_dimension >= 500:
                    return 55.0, QualityLevel.ACCEPTABLE
                else:
                    return 75.0, QualityLevel.POOR
                    
        except Exception:
            return 50.0, QualityLevel.ACCEPTABLE

    def _score_to_level(self, score: float) -> QualityLevel:
        """Converte score numérico para nível."""
        if score < 20:
            return QualityLevel.EXCELLENT
        elif score < 40:
            return QualityLevel.GOOD
        elif score < 60:
            return QualityLevel.ACCEPTABLE
        else:
            return QualityLevel.POOR

    # ==========================================================================
    # SMART CROP (Detecção de Saliência)
    # ==========================================================================

    def smart_crop(
        self, 
        input_path: str, 
        target_ratio: float = 1.0,
        output_path: Optional[str] = None
    ) -> str:
        """
        Recorta imagem focando na região de maior interesse.
        
        Args:
            input_path: Caminho da imagem original
            target_ratio: Proporção desejada (width/height)
            output_path: Caminho de saída
            
        Returns:
            Caminho da imagem recortada
        """
        if not HAS_OPENCV:
            # Fallback: crop central
            return self._center_crop(input_path, target_ratio, output_path)
        
        try:
            # Carrega imagem
            img = cv2.imread(str(input_path))
            if img is None:
                raise ValueError(f"Nao foi possivel carregar: {input_path}")
            
            h, w = img.shape[:2]
            
            # Detecta saliência usando Spectral Residual
            saliency = cv2.saliency.StaticSaliencySpectralResidual_create()
            success, saliency_map = saliency.computeSaliency(img)
            
            if not success:
                return self._center_crop(input_path, target_ratio, output_path)
            
            # Encontra região de maior saliência
            saliency_map = (saliency_map * 255).astype(np.uint8)
            _, thresh = cv2.threshold(saliency_map, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            
            # Encontra contornos
            contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            if not contours:
                return self._center_crop(input_path, target_ratio, output_path)
            
            # Bounding box que engloba todos os contornos significativos
            x_min, y_min = w, h
            x_max, y_max = 0, 0
            
            for cnt in contours:
                x, y, cw, ch = cv2.boundingRect(cnt)
                x_min = min(x_min, x)
                y_min = min(y_min, y)
                x_max = max(x_max, x + cw)
                y_max = max(y_max, y + ch)
            
            # Expande bbox para margem
            margin = int(min(w, h) * 0.1)
            x_min = max(0, x_min - margin)
            y_min = max(0, y_min - margin)
            x_max = min(w, x_max + margin)
            y_max = min(h, y_max + margin)
            
            # Ajusta para proporção desejada
            crop_w = x_max - x_min
            crop_h = y_max - y_min
            current_ratio = crop_w / crop_h
            
            if current_ratio > target_ratio:
                # Muito largo, ajusta altura
                new_h = int(crop_w / target_ratio)
                diff = new_h - crop_h
                y_min = max(0, y_min - diff // 2)
                y_max = min(h, y_max + diff // 2)
            else:
                # Muito alto, ajusta largura
                new_w = int(crop_h * target_ratio)
                diff = new_w - crop_w
                x_min = max(0, x_min - diff // 2)
                x_max = min(w, x_max + diff // 2)
            
            # Recorta
            cropped = img[y_min:y_max, x_min:x_max]
            
            # Salva
            if output_path is None:
                output_path = str(self.staging_dir / f"{Path(input_path).stem}_smart.png")
            
            cv2.imwrite(output_path, cropped)
            logger.info(f"Smart crop concluido: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Erro no smart crop: {e}")
            return self._center_crop(input_path, target_ratio, output_path)

    def _center_crop(
        self, 
        input_path: str, 
        target_ratio: float,
        output_path: Optional[str]
    ) -> str:
        """Fallback: recorte central."""
        with Image.open(input_path) as img:
            w, h = img.size
            current_ratio = w / h
            
            if current_ratio > target_ratio:
                new_w = int(h * target_ratio)
                left = (w - new_w) // 2
                crop_box = (left, 0, left + new_w, h)
            else:
                new_h = int(w / target_ratio)
                top = (h - new_h) // 2
                crop_box = (0, top, w, top + new_h)
            
            cropped = img.crop(crop_box)
            
            if output_path is None:
                output_path = str(self.staging_dir / f"{Path(input_path).stem}_crop.png")
            
            cropped.save(output_path)
            return output_path

    # ==========================================================================
    # VAULT - Gestão de Imagens
    # ==========================================================================

    def store_in_vault(self, input_path: str) -> str:
        """
        Armazena imagem no vault com nome baseado em hash MD5.
        
        Conforme Vol. I, Cap. 3 - Protocolo do Cofre de Imagens.
        
        Returns:
            Hash MD5 da imagem (serve como identificador)
        """
        input_path = Path(input_path)
        if not input_path.exists():
            raise FileNotFoundError(f"Imagem nao encontrada: {input_path}")
        
        # Calcula hash
        with open(input_path, "rb") as f:
            # INDUSTRIAL ROBUSTNESS #107: SHA-256
            file_hash = hashlib.sha256(f.read()).hexdigest()
        
        # Estrutura hierárquica: AA/BB/AABBCCDD...
        subdir = self.vault_dir / file_hash[:2] / file_hash[2:4]
        os.makedirs(subdir, exist_ok=True)
        
        # Preserva extensão
        ext = input_path.suffix.lower() or ".png"
        dest_path = subdir / f"{file_hash}{ext}"
        
        # Copia se não existir
        if not dest_path.exists():
            shutil.copy2(input_path, dest_path)
            logger.info(f"Imagem armazenada no vault: {file_hash}")
        
        return file_hash

    def get_from_vault(self, file_hash: str) -> Optional[str]:
        """
        Recupera caminho de imagem do vault pelo hash.
        
        Returns:
            Caminho absoluto ou None se não existir
        """
        subdir = self.vault_dir / file_hash[:2] / file_hash[2:4]
        
        # Tenta extensões comuns
        for ext in [".png", ".jpg", ".jpeg", ".webp"]:
            path = subdir / f"{file_hash}{ext}"
            if path.exists():
                return str(path)
        
        return None

    def generate_thumbnail(
        self, 
        source_path: str, 
        size: Tuple[int, int] = (200, 200)
    ) -> str:
        """
        Gera thumbnail da imagem.
        
        Args:
            source_path: Caminho da imagem original
            size: Dimensões do thumbnail (width, height)
            
        Returns:
            Caminho do thumbnail gerado
        """
        source_path = Path(source_path)
        thumb_dir = self.staging_dir / "thumbnails"
        os.makedirs(thumb_dir, exist_ok=True)
        
        thumb_path = thumb_dir / f"{source_path.stem}_thumb.jpg"
        
        with Image.open(source_path) as img:
            # Converte para RGB se necessário (para JPEG)
            if img.mode in ('RGBA', 'P'):
                img = img.convert('RGB')
            
            # Redimensiona mantendo proporção
            img.thumbnail(size, Image.Resampling.LANCZOS)
            
            img.save(thumb_path, "JPEG", quality=85)
        
        return str(thumb_path)

    # ==========================================================================
    # PIPELINE COMPLETO
    # ==========================================================================

    def process_product_image(
        self,
        input_path: str,
        remove_bg: bool = True,
        upscale_if_needed: bool = True,
        min_dimension: int = 800
    ) -> dict:
        """
        Pipeline completo de processamento de imagem de produto.
        
        Args:
            input_path: Caminho da imagem original
            remove_bg: Se deve remover fundo
            upscale_if_needed: Se deve ampliar imagens pequenas
            min_dimension: Dimensão mínima desejada
            
        Returns:
            Dict com resultados do processamento:
            {
                "original_path": str,
                "processed_path": str,
                "vault_hash": str,
                "quality_score": float,
                "quality_level": str,
                "thumbnail_path": str
            }
        """
        result = {
            "original_path": input_path,
            "processed_path": input_path,
            "vault_hash": None,
            "quality_score": None,
            "quality_level": None,
            "thumbnail_path": None
        }
        
        current_path = input_path
        
        try:
            # 1. Avalia qualidade inicial
            score, level = self.calculate_quality_score(current_path)
            result["quality_score"] = score
            result["quality_level"] = level.value
            
            # 2. Upscale se necessário
            if upscale_if_needed and self.esrgan_path:
                with Image.open(current_path) as img:
                    min_dim = min(img.size)
                    
                if min_dim < min_dimension:
                    current_path = self.upscale(current_path)
                    result["processed_path"] = current_path
            
            # 3. Remove fundo se solicitado
            if remove_bg and HAS_REMBG:
                current_path = self.remove_background(current_path)
                result["processed_path"] = current_path
            
            # 4. Armazena no vault
            vault_hash = self.store_in_vault(current_path)
            result["vault_hash"] = vault_hash
            
            # 5. Gera thumbnail
            thumb_path = self.generate_thumbnail(current_path)
            result["thumbnail_path"] = thumb_path
            
            logger.info(f"Pipeline completo para {input_path}: hash={vault_hash}")
            
        except Exception as e:
            logger.error(f"Erro no pipeline de imagem: {e}")
            result["error"] = str(e)
        
        return result

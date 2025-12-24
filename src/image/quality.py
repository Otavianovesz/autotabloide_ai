"""
AutoTabloide AI - Image Quality Assessment (BRISQUE)
=====================================================
Implementação conforme Vol. IV, Cap. 3.2.

Avaliação perceptual de qualidade de imagem usando BRISQUE.
Score 0-100 (0 = melhor qualidade, 100 = pior qualidade).
"""

import logging
from pathlib import Path
from typing import Optional, Tuple
import numpy as np

logger = logging.getLogger("ImageQuality")


class QualityThresholds:
    """Limiares de qualidade para categorização."""
    EXCELLENT = 25      # 0-25: Excelente
    GOOD = 40           # 25-40: Bom
    ACCEPTABLE = 60     # 40-60: Aceitável
    POOR = 80           # 60-80: Ruim
    UNACCEPTABLE = 100  # 80-100: Inaceitável


class ImageQualityAssessor:
    """
    Avaliador de qualidade de imagem usando BRISQUE.
    
    BRISQUE (Blind/Referenceless Image Spatial Quality Evaluator)
    é um modelo no-reference que não requer imagem de referência.
    
    Ref: Vol. IV, Cap. 3.2
    """
    
    def __init__(self):
        self._brisque_model = None
        self._opencv_available = False
        self._loaded = False
        self._load_model()
    
    def _load_model(self):
        """Carrega modelo BRISQUE do OpenCV."""
        try:
            import cv2
            
            # OpenCV contrib tem BRISQUE
            model_path = Path(__file__).parent.parent / "AutoTabloide_System_Root" / "bin" / "brisque_model_live.yml"
            range_path = Path(__file__).parent.parent / "AutoTabloide_System_Root" / "bin" / "brisque_range_live.yml"
            
            if model_path.exists() and range_path.exists():
                self._brisque_model = cv2.quality.QualityBRISQUE_create(
                    str(model_path),
                    str(range_path)
                )
                logger.info("BRISQUE model loaded from custom paths")
            else:
                # Tenta modelo padrão do OpenCV
                self._brisque_model = cv2.quality.QualityBRISQUE_create()
                logger.info("BRISQUE using default OpenCV model")
            
            self._opencv_available = True
            self._loaded = True
            
        except ImportError:
            logger.warning("OpenCV contrib não disponível. BRISQUE desativado.")
            self._opencv_available = False
        except Exception as e:
            logger.warning(f"Erro ao carregar BRISQUE: {e}")
            self._opencv_available = False
    
    def assess(self, image_path: str) -> Tuple[float, str]:
        """
        Avalia qualidade de uma imagem.
        
        Args:
            image_path: Caminho para a imagem
            
        Returns:
            Tuple[score, categoria]
            - score: 0-100 (menor = melhor)
            - categoria: 'excellent', 'good', 'acceptable', 'poor', 'unacceptable'
        """
        if not self._opencv_available:
            return self._fallback_assessment(image_path)
        
        try:
            import cv2
            
            img = cv2.imread(str(image_path))
            if img is None:
                logger.error(f"Não foi possível carregar imagem: {image_path}")
                return (100.0, "unacceptable")
            
            # Computa score BRISQUE
            score = self._brisque_model.compute(img)[0]
            
            # Normaliza para 0-100 (BRISQUE pode dar valores negativos ou > 100)
            score = max(0, min(100, score))
            
            category = self._categorize_score(score)
            
            logger.debug(f"BRISQUE score para {Path(image_path).name}: {score:.2f} ({category})")
            
            return (float(score), category)
            
        except Exception as e:
            logger.error(f"Erro ao avaliar imagem: {e}")
            return self._fallback_assessment(image_path)
    
    def _categorize_score(self, score: float) -> str:
        """Categoriza score em label legível."""
        if score <= QualityThresholds.EXCELLENT:
            return "excellent"
        elif score <= QualityThresholds.GOOD:
            return "good"
        elif score <= QualityThresholds.ACCEPTABLE:
            return "acceptable"
        elif score <= QualityThresholds.POOR:
            return "poor"
        return "unacceptable"
    
    def _fallback_assessment(self, image_path: str) -> Tuple[float, str]:
        """
        Avaliação fallback baseada em heurísticas simples.
        Usa dimensões, tamanho do arquivo e presença de artefatos.
        """
        try:
            from PIL import Image
            
            path = Path(image_path)
            if not path.exists():
                return (100.0, "unacceptable")
            
            # Tamanho do arquivo
            file_size = path.stat().st_size
            
            with Image.open(path) as img:
                width, height = img.size
                
                # Heurísticas simples
                score = 50.0  # Base
                
                # Penaliza imagens muito pequenas
                if width < 200 or height < 200:
                    score += 30
                elif width >= 800 and height >= 800:
                    score -= 15
                
                # Penaliza tamanho de arquivo muito pequeno (possível compressão excessiva)
                kb = file_size / 1024
                if kb < 20:
                    score += 20
                elif kb > 500:
                    score -= 10
                
                # Bonus para formatos sem perda
                if path.suffix.lower() in ['.png', '.tiff', '.bmp']:
                    score -= 10
                
                score = max(0, min(100, score))
                return (score, self._categorize_score(score))
                
        except Exception as e:
            logger.error(f"Fallback assessment failed: {e}")
            return (75.0, "poor")
    
    def assess_batch(self, image_paths: list) -> list:
        """
        Avalia múltiplas imagens em batch.
        
        Returns:
            Lista de Tuple[path, score, category]
        """
        results = []
        for path in image_paths:
            score, category = self.assess(path)
            results.append((path, score, category))
        return results
    
    def get_quality_color(self, score: float) -> str:
        """Retorna cor semântica para o score."""
        if score <= QualityThresholds.EXCELLENT:
            return "#34C759"  # Verde
        elif score <= QualityThresholds.GOOD:
            return "#30D158"  # Verde claro
        elif score <= QualityThresholds.ACCEPTABLE:
            return "#FF9500"  # Laranja
        elif score <= QualityThresholds.POOR:
            return "#FF3B30"  # Vermelho
        return "#AF52DE"      # Roxo (crítico)


# Singleton
_assessor: Optional[ImageQualityAssessor] = None


def get_quality_assessor() -> ImageQualityAssessor:
    """Obtém instância singleton do avaliador de qualidade."""
    global _assessor
    if _assessor is None:
        _assessor = ImageQualityAssessor()
    return _assessor

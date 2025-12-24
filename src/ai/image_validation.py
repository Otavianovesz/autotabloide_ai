"""
AutoTabloide AI - Image Validation Utils
==========================================
Utilitários para validação de imagens.
Passo 28 do Checklist 100.

Funcionalidades:
- Rejeitar imagens brancas/vazias
- Validar dimensões mínimas
- Detectar imagens corrompidas
"""

import io
from typing import Tuple, Optional
from PIL import Image
import numpy as np

from src.core.logging_config import get_logger

logger = get_logger("ImageValidation")


def is_blank_image(image_bytes: bytes, threshold: float = 0.98) -> bool:
    """
    Verifica se imagem é predominantemente branca/vazia.
    Passo 28 do Checklist - Rejeitar imagens brancas.
    
    Args:
        image_bytes: Bytes da imagem
        threshold: Percentual de pixels brancos para considerar vazia (0.0 a 1.0)
        
    Returns:
        True se a imagem é considerada branca/vazia
    """
    try:
        with Image.open(io.BytesIO(image_bytes)) as img:
            # Converte para escala de cinza
            gray = img.convert("L")
            
            # Converte para numpy array
            arr = np.array(gray)
            
            # Conta pixels quase brancos (>250)
            white_pixels = np.sum(arr > 250)
            total_pixels = arr.size
            
            white_ratio = white_pixels / total_pixels
            
            if white_ratio >= threshold:
                logger.warning(f"Imagem branca detectada ({white_ratio*100:.1f}% brancos)")
                return True
            
            return False
            
    except Exception as e:
        logger.error(f"Erro ao verificar imagem branca: {e}")
        return False


def is_solid_color(image_bytes: bytes, tolerance: int = 10) -> Tuple[bool, Optional[Tuple]]:
    """
    Verifica se imagem é uma cor sólida única.
    
    Args:
        image_bytes: Bytes da imagem
        tolerance: Variação de cor tolerada
        
    Returns:
        Tupla (é_sólida, cor_dominante)
    """
    try:
        with Image.open(io.BytesIO(image_bytes)) as img:
            # Redimensiona para análise rápida
            small = img.resize((50, 50), Image.Resampling.LANCZOS)
            
            if small.mode != "RGB":
                small = small.convert("RGB")
            
            arr = np.array(small)
            
            # Calcula variância de cada canal
            r_var = np.var(arr[:, :, 0])
            g_var = np.var(arr[:, :, 1])
            b_var = np.var(arr[:, :, 2])
            
            total_var = r_var + g_var + b_var
            
            if total_var < tolerance ** 2:
                # É cor sólida - pega cor média
                avg_color = tuple(np.mean(arr, axis=(0, 1)).astype(int))
                logger.warning(f"Imagem cor sólida detectada: RGB{avg_color}")
                return True, avg_color
            
            return False, None
            
    except Exception as e:
        logger.error(f"Erro ao verificar cor sólida: {e}")
        return False, None


def validate_image_dimensions(
    image_bytes: bytes,
    min_width: int = 300,
    min_height: int = 300
) -> Tuple[bool, int, int]:
    """
    Valida dimensões mínimas da imagem.
    
    Args:
        image_bytes: Bytes da imagem
        min_width: Largura mínima
        min_height: Altura mínima
        
    Returns:
        Tupla (válida, largura, altura)
    """
    try:
        with Image.open(io.BytesIO(image_bytes)) as img:
            width, height = img.size
            
            is_valid = width >= min_width and height >= min_height
            
            if not is_valid:
                logger.warning(f"Imagem muito pequena: {width}x{height} (mín: {min_width}x{min_height})")
            
            return is_valid, width, height
            
    except Exception as e:
        logger.error(f"Erro ao verificar dimensões: {e}")
        return False, 0, 0


def is_image_corrupted(image_bytes: bytes) -> bool:
    """
    Verifica se imagem está corrompida.
    
    Args:
        image_bytes: Bytes da imagem
        
    Returns:
        True se corrompida
    """
    try:
        with Image.open(io.BytesIO(image_bytes)) as img:
            # Tenta carregar todos os pixels
            img.load()
            
            # Tenta verificar formato
            img.verify()
        
        return False
        
    except Exception as e:
        logger.warning(f"Imagem corrompida: {e}")
        return True


def validate_image_quality(
    image_bytes: bytes,
    min_width: int = 300,
    min_height: int = 300,
    reject_blank: bool = True,
    reject_solid: bool = True
) -> Tuple[bool, str]:
    """
    Validação completa de qualidade de imagem.
    Passo 28 - Consolidado.
    
    Args:
        image_bytes: Bytes da imagem
        min_width: Largura mínima
        min_height: Altura mínima
        reject_blank: Rejeitar imagens brancas
        reject_solid: Rejeitar cores sólidas
        
    Returns:
        Tupla (válida, motivo_rejeição)
    """
    # Verifica corrupção
    if is_image_corrupted(image_bytes):
        return False, "Imagem corrompida ou ilegível"
    
    # Verifica dimensões
    valid_size, w, h = validate_image_dimensions(image_bytes, min_width, min_height)
    if not valid_size:
        return False, f"Dimensões insuficientes: {w}x{h}"
    
    # Verifica branco
    if reject_blank and is_blank_image(image_bytes):
        return False, "Imagem predominantemente branca"
    
    # Verifica cor sólida
    if reject_solid:
        is_solid, color = is_solid_color(image_bytes)
        if is_solid:
            return False, f"Imagem de cor sólida: RGB{color}"
    
    return True, "OK"

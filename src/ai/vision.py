"""
AutoTabloide AI - Image Processor (The Image Doctor)
======================================================
Pipeline de processamento de imagens com IA.
Passos 18-24 do Checklist 100.

Funcionalidades:
- Remoção de fundo (rembg + U2-Net)
- Auto-crop de bordas transparentes (OpenCV)
- Padding configurável
- Cache de processamento via hash
"""

import hashlib
import io
from pathlib import Path
from typing import Optional, Tuple, Union
from PIL import Image
import numpy as np

from src.core.logging_config import get_logger
from src.core.constants import SYSTEM_ROOT

logger = get_logger("ImageProcessor")

# Constantes
ASSETS_STORE = SYSTEM_ROOT / "assets" / "store"
STAGING_DIR = SYSTEM_ROOT / "staging"
PROCESSED_CACHE_DIR = SYSTEM_ROOT / "cache" / "processed"

# Garantir diretórios
ASSETS_STORE.mkdir(parents=True, exist_ok=True)
STAGING_DIR.mkdir(parents=True, exist_ok=True)
PROCESSED_CACHE_DIR.mkdir(parents=True, exist_ok=True)


class ImageProcessor:
    """
    The Image Doctor - Pipeline de processamento industrial.
    
    Responsabilidades:
    1. Remover fundo de imagens de produtos
    2. Cortar bordas transparentes excessivas
    3. Adicionar padding de segurança
    4. Cachear processamentos para evitar retrabalho
    """
    
    _instance: Optional["ImageProcessor"] = None
    _rembg_session = None
    
    def __new__(cls) -> "ImageProcessor":
        """Singleton pattern."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Inicializa o processador."""
        if hasattr(self, '_initialized') and self._initialized:
            return
        self._initialized = True
    
    @staticmethod
    def calculate_hash(image_bytes: bytes) -> str:
        """
        Calcula hash MD5 de bytes de imagem.
        
        Args:
            image_bytes: Bytes da imagem
            
        Returns:
            Hash MD5 como string hex
        """
        # INDUSTRIAL ROBUSTNESS #107: SHA-256 por segurança
        return hashlib.sha256(image_bytes).hexdigest()
    
    def _get_cached_path(self, original_hash: str) -> Optional[Path]:
        """
        Verifica se existe versão processada em cache.
        
        Args:
            original_hash: Hash da imagem original
            
        Returns:
            Caminho do arquivo se existir, None caso contrário
        """
        cached_path = PROCESSED_CACHE_DIR / f"{original_hash}_processed.png"
        if cached_path.exists():
            return cached_path
        return None
    
    def _save_to_cache(self, original_hash: str, processed_bytes: bytes) -> Path:
        """
        Salva imagem processada no cache.
        
        Args:
            original_hash: Hash da imagem original
            processed_bytes: Bytes da imagem processada
            
        Returns:
            Caminho do arquivo salvo
        """
        cached_path = PROCESSED_CACHE_DIR / f"{original_hash}_processed.png"
        cached_path.write_bytes(processed_bytes)
        logger.debug(f"Imagem cacheada: {cached_path.name}")
        return cached_path
    
    def remove_background(self, image_bytes: bytes) -> Tuple[bytes, bool]:
        """
        Remove fundo de imagem usando rembg (U2-Net).
        Passo 19 do Checklist.
        CENTURY CHECKLIST Item 36: Retorna flag indicando sucesso.
        
        Args:
            image_bytes: Bytes da imagem original
            
        Returns:
            Tupla (bytes_resultado, bg_removed_success)
        """
        # CENTURY CHECKLIST Item 37: Validar cabeçalho da imagem
        if not self._validate_image_header(image_bytes):
            logger.warning("Cabeçalho de imagem inválido")
            return image_bytes, False
        
        try:
            from rembg import remove, new_session
            
            # Lazy load da sessão (warm-start)
            if ImageProcessor._rembg_session is None:
                logger.info("Inicializando sessão rembg (U2-Net)...")
                ImageProcessor._rembg_session = new_session("u2net")
            
            # Processa imagem
            output = remove(
                image_bytes,
                session=ImageProcessor._rembg_session,
                alpha_matting=True,
                alpha_matting_foreground_threshold=240,
                alpha_matting_background_threshold=10
            )
            
            logger.debug("Fundo removido com sucesso")
            return output, True
            
        except ImportError:
            logger.warning("rembg não instalado, retornando imagem original")
            return image_bytes, False
        except Exception as e:
            logger.error(f"Erro ao remover fundo: {e}")
            return image_bytes, False
    
    def _validate_image_header(self, image_bytes: bytes) -> bool:
        """
        CENTURY CHECKLIST Item 37: Verifica se bytes são imagem válida.
        Checa magic bytes de PNG, JPEG, GIF, WebP.
        
        Returns:
            True se cabeçalho é válido
        """
        if len(image_bytes) < 10:
            return False
        
        # Magic bytes comuns
        magic = {
            b'\x89PNG': 'PNG',
            b'\xff\xd8\xff': 'JPEG',
            b'GIF87a': 'GIF',
            b'GIF89a': 'GIF',
            b'RIFF': 'WebP',  # WebP é RIFF....WEBP
        }
        
        for header, fmt in magic.items():
            if image_bytes.startswith(header):
                return True
        
        # WebP precisa check especial
        if image_bytes[:4] == b'RIFF' and image_bytes[8:12] == b'WEBP':
            return True
        
        return False
    
    def trim_transparent_borders(self, image: Image.Image, padding_px: int = 10) -> Image.Image:
        """
        Remove bordas transparentes excessivas (Auto-Crop).
        Passo 20 do Checklist.
        
        Args:
            image: Imagem PIL com canal alpha
            padding_px: Pixels de margem a manter
            
        Returns:
            Imagem cortada
        """
        try:
            import cv2
            
            # Converter para numpy array
            if image.mode != 'RGBA':
                image = image.convert('RGBA')
            
            np_image = np.array(image)
            
            # Extrair canal alpha
            alpha = np_image[:, :, 3]
            
            # Encontrar bounding rect de pixels não-transparentes
            coords = cv2.findNonZero(alpha)
            
            if coords is None:
                logger.warning("Imagem totalmente transparente, retornando original")
                return image
            
            x, y, w, h = cv2.boundingRect(coords)
            
            # Aplicar padding
            x = max(0, x - padding_px)
            y = max(0, y - padding_px)
            w = min(np_image.shape[1] - x, w + 2 * padding_px)
            h = min(np_image.shape[0] - y, h + 2 * padding_px)
            
            # Cortar
            cropped = np_image[y:y+h, x:x+w]
            result = Image.fromarray(cropped, 'RGBA')
            
            logger.debug(f"Auto-crop: {image.size} -> {result.size}")
            return result
            
        except ImportError:
            logger.warning("OpenCV não instalado, retornando imagem original")
            return image
        except Exception as e:
            logger.error(f"Erro no auto-crop: {e}")
            return image
    
    def add_padding(self, image: Image.Image, percent: float = 10.0) -> Image.Image:
        """
        Adiciona padding percentual ao redor da imagem.
        Passo 21 do Checklist.
        
        Args:
            image: Imagem PIL
            percent: Porcentagem de padding (10% = 10.0)
            
        Returns:
            Imagem com padding transparente
        """
        try:
            if image.mode != 'RGBA':
                image = image.convert('RGBA')
            
            w, h = image.size
            pad_x = int(w * percent / 100)
            pad_y = int(h * percent / 100)
            
            new_w = w + 2 * pad_x
            new_h = h + 2 * pad_y
            
            # Criar canvas transparente
            canvas = Image.new('RGBA', (new_w, new_h), (0, 0, 0, 0))
            
            # Colar imagem centralizada
            canvas.paste(image, (pad_x, pad_y))
            
            logger.debug(f"Padding adicionado: {image.size} -> {canvas.size}")
            return canvas
            
        except Exception as e:
            logger.error(f"Erro ao adicionar padding: {e}")
            return image
    
    def is_mostly_white(self, image_bytes: bytes, threshold: float = 0.95) -> bool:
        """
        Verifica se imagem é majoritariamente branca/vazia.
        Passo 28 do Checklist - Rejeitar imagens inválidas.
        
        Args:
            image_bytes: Bytes da imagem
            threshold: Proporção mínima de pixels brancos
            
        Returns:
            True se imagem é inválida (maioria branca)
        """
        try:
            image = Image.open(io.BytesIO(image_bytes))
            
            if image.mode in ('RGBA', 'LA'):
                # Para imagens com alpha, verificar transparência
                if image.mode == 'RGBA':
                    alpha = np.array(image)[:, :, 3]
                else:
                    alpha = np.array(image)[:, :, 1]
                
                transparent_ratio = np.sum(alpha < 10) / alpha.size
                return transparent_ratio > threshold
            else:
                # Para imagens sem alpha, verificar brancos
                gray = image.convert('L')
                np_gray = np.array(gray)
                white_ratio = np.sum(np_gray > 250) / np_gray.size
                return white_ratio > threshold
                
        except Exception as e:
            logger.error(f"Erro ao verificar imagem: {e}")
            return False
    
    def process_full_pipeline(
        self,
        image_bytes: bytes,
        remove_bg: bool = True,
        auto_crop: bool = True,
        padding_percent: float = 10.0,
        use_cache: bool = True
    ) -> Tuple[bytes, str]:
        """
        Executa pipeline completo de processamento.
        Passos 18-24 do Checklist.
        
        Args:
            image_bytes: Bytes da imagem original
            remove_bg: Remover fundo?
            auto_crop: Cortar bordas transparentes?
            padding_percent: Porcentagem de padding
            use_cache: Usar cache de processamento?
            
        Returns:
            Tupla (bytes_processados, hash_md5)
        """
        original_hash = self.calculate_hash(image_bytes)
        
        # Verificar cache (Passo 24)
        if use_cache:
            cached = self._get_cached_path(original_hash)
            if cached:
                logger.info(f"Usando cache: {cached.name}")
                cached_bytes = cached.read_bytes()
                return cached_bytes, self.calculate_hash(cached_bytes)
        
        # Validar imagem
        if self.is_mostly_white(image_bytes):
            logger.warning("Imagem rejeitada: maioria branca/vazia")
            return image_bytes, original_hash
        
        # Pipeline
        processed = image_bytes
        
        # 1. Remover fundo
        if remove_bg:
            processed = self.remove_background(processed)
        
        # 2. Abrir como PIL
        image = Image.open(io.BytesIO(processed))
        
        # 3. Auto-crop
        if auto_crop:
            image = self.trim_transparent_borders(image)
        
        # 4. Padding
        if padding_percent > 0:
            image = self.add_padding(image, padding_percent)
        
        # 5. Converter para bytes
        output = io.BytesIO()
        image.save(output, format='PNG', optimize=True)
        result_bytes = output.getvalue()
        
        # 6. Cachear
        if use_cache:
            self._save_to_cache(original_hash, result_bytes)
        
        result_hash = self.calculate_hash(result_bytes)
        logger.info(f"Pipeline completo: {original_hash[:8]} -> {result_hash[:8]}")
        
        return result_bytes, result_hash
    
    def save_to_vault(self, image_bytes: bytes) -> Tuple[Path, str]:
        """
        Salva imagem no Image Vault com nome de hash.
        Conforme protocolo de desduplicação do Codex.
        
        Args:
            image_bytes: Bytes da imagem
            
        Returns:
            Tupla (caminho_absoluto, hash_md5)
        """
        hash_md5 = self.calculate_hash(image_bytes)
        file_path = ASSETS_STORE / f"{hash_md5}.png"
        
        # Verificar duplicata
        if file_path.exists():
            logger.debug(f"Imagem já existe no vault: {hash_md5}")
            return file_path, hash_md5
        
        # Salvar
        file_path.write_bytes(image_bytes)
        logger.info(f"Imagem salva no vault: {hash_md5}.png")
        
        return file_path, hash_md5


# Singleton global
image_processor = ImageProcessor()


def get_image_processor() -> ImageProcessor:
    """
    Retorna instância singleton do ImageProcessor.
    """
    return image_processor

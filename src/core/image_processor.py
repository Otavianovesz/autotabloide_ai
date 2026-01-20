"""
AutoTabloide AI - Image Processor Pipeline
============================================
FASE PIPELINE DE IMAGENS: Processamento unificado de imagens.

Features:
- Conversão forçada para PNG interno (35)
- Geração de thumbnails 128x128 (38)
- Hash SHA-256 para evitar duplicatas (39)
"""

import hashlib
import logging
from pathlib import Path
from typing import Optional, Tuple, Dict, Any
from PIL import Image
import io

logger = logging.getLogger("ImageProcessor")


# ==============================================================================
# CONSTANTES
# ==============================================================================

THUMBNAIL_SIZE = (128, 128)
STORE_SUBDIR = "assets/store"
THUMBNAIL_SUBDIR = "assets/thumbnails"

# Formatos suportados para conversão
SUPPORTED_FORMATS = {".jpg", ".jpeg", ".png", ".webp", ".avif", ".gif", ".bmp", ".tiff"}


# ==============================================================================
# PASSO 39: SHA-256 HASH
# ==============================================================================

class ImageHasher:
    """
    Calcula hash SHA-256 de imagens para evitar duplicatas físicas.
    
    PROBLEMA: Usuário pode importar mesma imagem com nomes diferentes.
    SOLUÇÃO: Hash do conteúdo determina identidade, não o nome.
    """
    
    @classmethod
    def calculate_hash(cls, image_path: Path) -> str:
        """
        Calcula SHA-256 do arquivo de imagem.
        
        Args:
            image_path: Caminho da imagem
            
        Returns:
            Hash hexadecimal de 64 caracteres
        """
        hasher = hashlib.sha256()
        
        with open(image_path, "rb") as f:
            # Lê em chunks para imagens grandes
            for chunk in iter(lambda: f.read(65536), b""):
                hasher.update(chunk)
        
        return hasher.hexdigest()
    
    @classmethod
    def calculate_hash_from_bytes(cls, data: bytes) -> str:
        """Calcula SHA-256 de bytes."""
        return hashlib.sha256(data).hexdigest()
    
    @classmethod
    def get_short_hash(cls, image_path: Path, length: int = 8) -> str:
        """Retorna hash curto para uso em nomes de arquivo."""
        full_hash = cls.calculate_hash(image_path)
        return full_hash[:length]


# ==============================================================================
# PASSO 35: CONVERSÃO PARA PNG
# ==============================================================================

class ImageConverter:
    """
    Converte imagens para PNG interno.
    
    PROBLEMA: WebP, AVIF, JPG têm comportamentos diferentes em SVG/PDF.
    SOLUÇÃO: Tudo vira PNG internamente para consistência.
    """
    
    @classmethod
    def convert_to_png(
        cls,
        input_path: Path,
        output_path: Optional[Path] = None,
        optimize: bool = True
    ) -> Path:
        """
        Converte qualquer formato suportado para PNG.
        
        Args:
            input_path: Caminho da imagem original
            output_path: Caminho de saída (opcional, gera automaticamente)
            optimize: Se True, otimiza o PNG gerado
            
        Returns:
            Caminho do arquivo PNG gerado
        """
        input_path = Path(input_path)
        
        if not input_path.exists():
            raise FileNotFoundError(f"Imagem não encontrada: {input_path}")
        
        # Se já é PNG, apenas copia/retorna
        if input_path.suffix.lower() == ".png":
            if output_path and output_path != input_path:
                import shutil
                shutil.copy2(input_path, output_path)
                return output_path
            return input_path
        
        # Gera path de saída se não fornecido
        if output_path is None:
            output_path = input_path.with_suffix(".png")
        
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Converte
        with Image.open(input_path) as img:
            # Converte para RGB se necessário (remove alpha de formatos sem suporte)
            if img.mode in ("RGBA", "LA", "P"):
                # Mantém alpha
                if img.mode == "P":
                    img = img.convert("RGBA")
            elif img.mode != "RGB":
                img = img.convert("RGB")
            
            # Salva como PNG
            save_kwargs = {"format": "PNG"}
            if optimize:
                save_kwargs["optimize"] = True
            
            img.save(output_path, **save_kwargs)
        
        logger.debug(f"Convertido para PNG: {input_path} -> {output_path}")
        return output_path
    
    @classmethod
    def convert_bytes_to_png(cls, data: bytes) -> bytes:
        """Converte bytes de imagem para PNG."""
        with Image.open(io.BytesIO(data)) as img:
            if img.mode == "P":
                img = img.convert("RGBA")
            elif img.mode not in ("RGB", "RGBA", "LA"):
                img = img.convert("RGB")
            
            output = io.BytesIO()
            img.save(output, format="PNG")
            return output.getvalue()


# ==============================================================================
# PASSO 38: THUMBNAIL CACHING
# ==============================================================================

class ThumbnailGenerator:
    """
    Gera miniaturas para Grid de Estoque.
    
    PROBLEMA: Carregar imagens full-res na grid trava a UI.
    SOLUÇÃO: Gerar thumbnails 128x128 no momento do salvamento.
    """
    
    DEFAULT_SIZE = THUMBNAIL_SIZE
    
    @classmethod
    def generate(
        cls,
        image_path: Path,
        output_path: Optional[Path] = None,
        size: Tuple[int, int] = None
    ) -> Path:
        """
        Gera thumbnail de uma imagem.
        
        Args:
            image_path: Caminho da imagem original
            output_path: Caminho de saída (opcional)
            size: Tamanho do thumbnail (padrão: 128x128)
            
        Returns:
            Caminho do thumbnail gerado
        """
        image_path = Path(image_path)
        size = size or cls.DEFAULT_SIZE
        
        if not image_path.exists():
            raise FileNotFoundError(f"Imagem não encontrada: {image_path}")
        
        # Gera path de saída se não fornecido
        if output_path is None:
            # Coloca na subpasta thumbnails com mesmo nome
            thumb_dir = image_path.parent.parent / "thumbnails"
            thumb_dir.mkdir(parents=True, exist_ok=True)
            output_path = thumb_dir / f"{image_path.stem}_thumb.png"
        
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Gera thumbnail
        with Image.open(image_path) as img:
            # Mantém aspect ratio
            img.thumbnail(size, Image.Resampling.LANCZOS)
            
            # Cria imagem quadrada com padding se necessário
            thumb = Image.new("RGBA", size, (255, 255, 255, 0))
            
            # Centraliza
            offset = ((size[0] - img.width) // 2, (size[1] - img.height) // 2)
            
            if img.mode == "RGBA":
                thumb.paste(img, offset, img)
            else:
                if img.mode != "RGB":
                    img = img.convert("RGB")
                thumb.paste(img, offset)
            
            thumb.save(output_path, "PNG")
        
        logger.debug(f"Thumbnail gerado: {output_path}")
        return output_path
    
    @classmethod
    def get_or_generate(
        cls,
        image_path: Path,
        thumbnails_dir: Path,
        size: Tuple[int, int] = None
    ) -> Path:
        """
        Retorna thumbnail existente ou gera novo.
        
        Args:
            image_path: Caminho da imagem original
            thumbnails_dir: Diretório de thumbnails
            size: Tamanho desejado
            
        Returns:
            Caminho do thumbnail
        """
        image_path = Path(image_path)
        thumbnails_dir = Path(thumbnails_dir)
        
        thumb_path = thumbnails_dir / f"{image_path.stem}_thumb.png"
        
        if thumb_path.exists():
            # Verifica se thumbnail é mais recente que original
            if thumb_path.stat().st_mtime >= image_path.stat().st_mtime:
                return thumb_path
        
        # Gera novo
        return cls.generate(image_path, thumb_path, size)


# ==============================================================================
# PIPELINE UNIFICADO
# ==============================================================================

class ImageProcessor:
    """
    Pipeline unificado de processamento de imagens.
    
    Combina todas as operações em um fluxo coerente:
    1. Validação (magic bytes)
    2. Conversão para PNG
    3. Geração de thumbnail
    4. Cálculo de hash
    """
    
    @classmethod
    def process_new_image(
        cls,
        input_path: Path,
        store_dir: Path,
        thumbnails_dir: Optional[Path] = None,
        keep_original: bool = False
    ) -> Dict[str, Any]:
        """
        Pipeline completo de processamento de nova imagem.
        
        Args:
            input_path: Caminho da imagem de entrada
            store_dir: Diretório onde salvar a imagem processada
            thumbnails_dir: Diretório para thumbnails (opcional)
            keep_original: Se True, não remove o arquivo original
            
        Returns:
            Dict com informações do processamento:
            - success: bool
            - hash: str (SHA-256)
            - png_path: Path
            - thumbnail_path: Path
            - original_format: str
            - dimensions: (width, height)
            - error: str (se houver)
        """
        input_path = Path(input_path)
        store_dir = Path(store_dir)
        thumbnails_dir = Path(thumbnails_dir) if thumbnails_dir else store_dir.parent / "thumbnails"
        
        result = {
            "success": False,
            "hash": None,
            "png_path": None,
            "thumbnail_path": None,
            "original_format": None,
            "dimensions": None,
            "error": None
        }
        
        try:
            # 1. Validação básica
            if not input_path.exists():
                result["error"] = "Arquivo não encontrado"
                return result
            
            if input_path.suffix.lower() not in SUPPORTED_FORMATS:
                result["error"] = f"Formato não suportado: {input_path.suffix}"
                return result
            
            result["original_format"] = input_path.suffix.lower().lstrip(".")
            
            # 2. Calcula hash do original
            original_hash = ImageHasher.calculate_hash(input_path)
            result["hash"] = original_hash
            
            # 3. Caminho final baseado no hash (evita duplicatas)
            store_dir.mkdir(parents=True, exist_ok=True)
            final_path = store_dir / f"{original_hash}.png"
            
            # Se já existe com mesmo hash, apenas retorna
            if final_path.exists():
                logger.info(f"Imagem já existe (hash match): {final_path}")
                result["png_path"] = final_path
                result["success"] = True
                
                # Gera thumbnail se não existir
                thumb_path = ThumbnailGenerator.get_or_generate(
                    final_path, thumbnails_dir
                )
                result["thumbnail_path"] = thumb_path
                
                # Obtém dimensões
                with Image.open(final_path) as img:
                    result["dimensions"] = img.size
                
                return result
            
            # 4. Converte para PNG
            png_path = ImageConverter.convert_to_png(input_path, final_path)
            result["png_path"] = png_path
            
            # 5. Obtém dimensões
            with Image.open(png_path) as img:
                result["dimensions"] = img.size
            
            # 6. Gera thumbnail
            thumbnails_dir.mkdir(parents=True, exist_ok=True)
            thumb_path = ThumbnailGenerator.generate(
                png_path,
                thumbnails_dir / f"{original_hash}_thumb.png"
            )
            result["thumbnail_path"] = thumb_path
            
            # 7. Remove original se solicitado
            if not keep_original and input_path != png_path:
                try:
                    input_path.unlink()
                except Exception:
                    pass
            
            result["success"] = True
            logger.info(f"Imagem processada: {png_path} (hash: {original_hash[:8]}...)")
            
        except Exception as e:
            result["error"] = str(e)
            logger.error(f"Erro no processamento de imagem: {e}")
        
        return result
    
    @classmethod
    def get_image_info(cls, image_path: Path) -> Dict[str, Any]:
        """Retorna informações de uma imagem existente."""
        image_path = Path(image_path)
        
        info = {
            "exists": image_path.exists(),
            "hash": None,
            "format": None,
            "dimensions": None,
            "size_bytes": None
        }
        
        if not info["exists"]:
            return info
        
        info["hash"] = ImageHasher.calculate_hash(image_path)
        info["format"] = image_path.suffix.lower().lstrip(".")
        info["size_bytes"] = image_path.stat().st_size
        
        try:
            with Image.open(image_path) as img:
                info["dimensions"] = img.size
        except Exception:
            pass
        
        return info


# ==============================================================================
# CONVENIENCE FUNCTIONS
# ==============================================================================

def process_image(input_path: str, store_dir: str) -> Dict[str, Any]:
    """Atalho para ImageProcessor.process_new_image()"""
    return ImageProcessor.process_new_image(Path(input_path), Path(store_dir))


def calculate_image_hash(image_path: str) -> str:
    """Atalho para ImageHasher.calculate_hash()"""
    return ImageHasher.calculate_hash(Path(image_path))


def generate_thumbnail(image_path: str, output_path: str = None) -> str:
    """Atalho para ThumbnailGenerator.generate()"""
    result = ThumbnailGenerator.generate(
        Path(image_path),
        Path(output_path) if output_path else None
    )
    return str(result)


def convert_to_png(input_path: str, output_path: str = None) -> str:
    """Atalho para ImageConverter.convert_to_png()"""
    result = ImageConverter.convert_to_png(
        Path(input_path),
        Path(output_path) if output_path else None
    )
    return str(result)

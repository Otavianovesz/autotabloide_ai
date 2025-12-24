"""
AutoTabloide AI - Thumbnail Cache
===================================
Cache de thumbnails para SVG.
Passo 86 do Checklist 100.

Funcionalidades:
- Geração de thumbnails para SVG
- Cache em disco
- Invalidação por hash
"""

import hashlib
from pathlib import Path
from typing import Optional, Tuple
from io import BytesIO

from src.core.logging_config import get_logger
from src.core.constants import SYSTEM_ROOT

logger = get_logger("ThumbnailCache")

# Diretório de cache
THUMB_CACHE_DIR = SYSTEM_ROOT / "cache" / "thumbnails"
THUMB_CACHE_DIR.mkdir(parents=True, exist_ok=True)


class ThumbnailCache:
    """
    Cache de thumbnails para SVG.
    Passo 86 do Checklist - Cache thumbnails SVG.
    """
    
    def __init__(self, cache_dir: Optional[Path] = None):
        """
        Args:
            cache_dir: Diretório de cache (padrão: cache/thumbnails)
        """
        self.cache_dir = cache_dir or THUMB_CACHE_DIR
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self._stats = {"hits": 0, "misses": 0}
    
    def _compute_hash(self, content: bytes) -> str:
        """Computa hash do conteúdo."""
        return hashlib.md5(content).hexdigest()[:16]
    
    def _get_cache_path(self, content_hash: str, width: int, height: int) -> Path:
        """Retorna caminho do cache para um thumbnail."""
        return self.cache_dir / f"{content_hash}_{width}x{height}.png"
    
    def get(self, svg_content: bytes, width: int = 150, height: int = 150) -> Optional[bytes]:
        """
        Obtém thumbnail do cache.
        
        Args:
            svg_content: Conteúdo do SVG
            width: Largura do thumbnail
            height: Altura do thumbnail
            
        Returns:
            Bytes do PNG ou None se não em cache
        """
        content_hash = self._compute_hash(svg_content)
        cache_path = self._get_cache_path(content_hash, width, height)
        
        if cache_path.exists():
            try:
                self._stats["hits"] += 1
                return cache_path.read_bytes()
            except Exception:
                pass
        
        self._stats["misses"] += 1
        return None
    
    def put(self, svg_content: bytes, thumbnail: bytes, width: int = 150, height: int = 150) -> Path:
        """
        Armazena thumbnail no cache.
        
        Args:
            svg_content: Conteúdo original do SVG
            thumbnail: Bytes do PNG gerado
            width: Largura
            height: Altura
            
        Returns:
            Caminho do arquivo criado
        """
        content_hash = self._compute_hash(svg_content)
        cache_path = self._get_cache_path(content_hash, width, height)
        
        try:
            cache_path.write_bytes(thumbnail)
            logger.debug(f"Thumbnail cacheado: {cache_path.name}")
        except Exception as e:
            logger.warning(f"Erro ao cachear thumbnail: {e}")
        
        return cache_path
    
    def generate_thumbnail(
        self,
        svg_content: bytes,
        width: int = 150,
        height: int = 150
    ) -> Optional[bytes]:
        """
        Gera thumbnail de SVG (com cache).
        
        Args:
            svg_content: Conteúdo do SVG
            width: Largura
            height: Altura
            
        Returns:
            Bytes do PNG
        """
        # Verifica cache
        cached = self.get(svg_content, width, height)
        if cached:
            return cached
        
        # Gera thumbnail
        try:
            import cairosvg
            
            png_data = cairosvg.svg2png(
                bytestring=svg_content,
                output_width=width,
                output_height=height
            )
            
            # Cacheia
            self.put(svg_content, png_data, width, height)
            
            return png_data
            
        except ImportError:
            logger.warning("cairosvg não disponível para gerar thumbnails")
            return None
        except Exception as e:
            logger.error(f"Erro ao gerar thumbnail: {e}")
            return None
    
    def invalidate(self, svg_content: bytes) -> int:
        """
        Invalida cache para um SVG.
        
        Args:
            svg_content: Conteúdo do SVG
            
        Returns:
            Número de arquivos removidos
        """
        content_hash = self._compute_hash(svg_content)
        count = 0
        
        for cache_file in self.cache_dir.glob(f"{content_hash}_*.png"):
            try:
                cache_file.unlink()
                count += 1
            except Exception:
                pass
        
        return count
    
    def clear(self) -> int:
        """
        Limpa todo o cache.
        
        Returns:
            Número de arquivos removidos
        """
        count = 0
        
        for cache_file in self.cache_dir.glob("*.png"):
            try:
                cache_file.unlink()
                count += 1
            except Exception:
                pass
        
        logger.info(f"Cache de thumbnails limpo: {count} arquivos")
        return count
    
    def get_stats(self) -> dict:
        """Retorna estatísticas do cache."""
        total = self._stats["hits"] + self._stats["misses"]
        hit_rate = self._stats["hits"] / total * 100 if total > 0 else 0
        
        return {
            "hits": self._stats["hits"],
            "misses": self._stats["misses"],
            "hit_rate": f"{hit_rate:.1f}%",
            "cache_size": sum(f.stat().st_size for f in self.cache_dir.glob("*.png")),
            "cache_count": len(list(self.cache_dir.glob("*.png")))
        }


# Singleton
_thumbnail_cache: Optional[ThumbnailCache] = None


def get_thumbnail_cache() -> ThumbnailCache:
    """Retorna instância singleton do cache."""
    global _thumbnail_cache
    if _thumbnail_cache is None:
        _thumbnail_cache = ThumbnailCache()
    return _thumbnail_cache

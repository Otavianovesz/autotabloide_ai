"""
AutoTabloide AI - Preview Generator
=====================================
Gerador de previews PNG em tempo real.
PROTOCOLO DE RETIFICAÇÃO: Passo 76 (Preview Real PNG).

Gera previews rápidos para visualização no Ateliê.
"""

import asyncio
import logging
import hashlib
from pathlib import Path
from typing import Optional, Dict, Any, Tuple
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass

logger = logging.getLogger("Preview")


@dataclass
class PreviewConfig:
    """Configuração de geração de preview."""
    dpi: int = 72          # DPI baixo para velocidade
    max_width: int = 800   # Largura máxima
    max_height: int = 600  # Altura máxima
    format: str = "PNG"
    quality: int = 80      # Para JPEG
    cache_enabled: bool = True


class PreviewGenerator:
    """
    Gera previews PNG de layouts.
    
    PASSO 76: Preview em tempo real no Ateliê.
    """
    
    def __init__(
        self,
        cache_dir: Path,
        config: Optional[PreviewConfig] = None,
        max_workers: int = 2
    ):
        self.cache_dir = cache_dir
        self.config = config or PreviewConfig()
        self._executor = ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix="Preview")
        
        # Garante diretório de cache
        self.cache_dir.mkdir(parents=True, exist_ok=True)
    
    async def generate_preview(
        self,
        svg_content: str,
        output_path: Optional[Path] = None
    ) -> Optional[Path]:
        """
        Gera preview PNG de um SVG.
        
        Args:
            svg_content: Conteúdo SVG como string
            output_path: Caminho de saída (se None, usa cache)
            
        Returns:
            Caminho do PNG gerado ou None se falhou
        """
        # Verificar cache
        if self.config.cache_enabled:
            cache_key = self._get_cache_key(svg_content)
            cached_path = self.cache_dir / f"{cache_key}.png"
            
            if cached_path.exists():
                logger.debug(f"Preview cache hit: {cache_key}")
                return cached_path
        
        # Gerar em background
        loop = asyncio.get_event_loop()
        
        try:
            result = await loop.run_in_executor(
                self._executor,
                self._generate_sync,
                svg_content,
                output_path or cached_path if self.config.cache_enabled else None
            )
            return result
            
        except Exception as e:
            logger.error(f"Erro ao gerar preview: {e}")
            return None
    
    async def generate_thumbnail(
        self,
        svg_content: str,
        width: int = 200,
        height: int = 150
    ) -> Optional[bytes]:
        """
        Gera thumbnail pequeno como bytes.
        
        Args:
            svg_content: Conteúdo SVG
            width, height: Dimensões do thumbnail
            
        Returns:
            Bytes do PNG ou None
        """
        loop = asyncio.get_event_loop()
        
        try:
            return await loop.run_in_executor(
                self._executor,
                self._generate_thumbnail_sync,
                svg_content,
                width,
                height
            )
        except Exception as e:
            logger.error(f"Erro ao gerar thumbnail: {e}")
            return None
    
    def _generate_sync(
        self,
        svg_content: str,
        output_path: Optional[Path]
    ) -> Optional[Path]:
        """Geração síncrona de preview."""
        try:
            import cairosvg
            
            # Calcular escala para DPI
            scale = self.config.dpi / 96  # 96 é DPI padrão de tela
            
            if output_path:
                cairosvg.svg2png(
                    bytestring=svg_content.encode('utf-8'),
                    write_to=str(output_path),
                    scale=scale,
                    unsafe=True
                )
                return output_path
            else:
                # Retorna bytes (para uso direto)
                png_bytes = cairosvg.svg2png(
                    bytestring=svg_content.encode('utf-8'),
                    scale=scale,
                    unsafe=True
                )
                return png_bytes
                
        except ImportError:
            logger.error("CairoSVG não disponível")
            return None
        except Exception as e:
            logger.error(f"Erro no CairoSVG: {e}")
            return None
    
    def _generate_thumbnail_sync(
        self,
        svg_content: str,
        width: int,
        height: int
    ) -> Optional[bytes]:
        """Geração síncrona de thumbnail."""
        try:
            import cairosvg
            
            png_bytes = cairosvg.svg2png(
                bytestring=svg_content.encode('utf-8'),
                output_width=width,
                output_height=height,
                unsafe=True
            )
            return png_bytes
            
        except Exception as e:
            logger.error(f"Erro ao gerar thumbnail: {e}")
            return None
    
    def _get_cache_key(self, content: str) -> str:
        """Gera chave de cache baseada no conteúdo."""
        return hashlib.md5(content.encode('utf-8')).hexdigest()[:16]
    
    def clear_cache(self) -> int:
        """
        Limpa cache de previews.
        
        Returns:
            Número de arquivos removidos
        """
        count = 0
        for png_file in self.cache_dir.glob("*.png"):
            try:
                png_file.unlink()
                count += 1
            except Exception:
                pass
        
        logger.info(f"Cache de previews limpo: {count} arquivos")
        return count
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas do cache."""
        files = list(self.cache_dir.glob("*.png"))
        total_size = sum(f.stat().st_size for f in files)
        
        return {
            "count": len(files),
            "size_mb": total_size / (1024 * 1024),
            "path": str(self.cache_dir),
        }
    
    def shutdown(self) -> None:
        """Encerra executor."""
        self._executor.shutdown(wait=False)


# ==============================================================================
# COMPARAÇÃO DE PREVIEWS
# ==============================================================================

class PreviewComparator:
    """Compara previews para detectar mudanças."""
    
    @staticmethod
    def content_changed(old_content: str, new_content: str) -> bool:
        """
        Verifica se conteúdo mudou significativamente.
        
        Ignora mudanças em timestamps e IDs únicos.
        """
        import re
        
        # Remover timestamps
        pattern = r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}'
        old_clean = re.sub(pattern, '', old_content)
        new_clean = re.sub(pattern, '', new_content)
        
        # Remover IDs gerados
        id_pattern = r'id="[^"]*_\d+"'
        old_clean = re.sub(id_pattern, '', old_clean)
        new_clean = re.sub(id_pattern, '', new_clean)
        
        return old_clean != new_clean


# ==============================================================================
# INSTÂNCIA GLOBAL
# ==============================================================================

_generator: Optional[PreviewGenerator] = None


def get_preview_generator(cache_dir: Optional[Path] = None) -> PreviewGenerator:
    """Retorna instância global do gerador."""
    global _generator
    
    if _generator is None:
        if cache_dir is None:
            from src.core.constants import SYSTEM_ROOT
            cache_dir = SYSTEM_ROOT / "temp_render" / "preview_cache"
        
        _generator = PreviewGenerator(cache_dir)
    
    return _generator


async def generate_preview(svg_content: str) -> Optional[Path]:
    """Função de conveniência para gerar preview."""
    generator = get_preview_generator()
    return await generator.generate_preview(svg_content)

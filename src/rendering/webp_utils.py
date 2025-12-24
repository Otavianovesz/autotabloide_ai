"""
AutoTabloide AI - WebP Support
================================
Suporte a imagens WebP.
Passo 96 do Checklist 100.

Funcionalidades:
- Detecção de formato WebP
- Conversão para PNG
- Cache de conversões
"""

import io
from pathlib import Path
from typing import Optional, Tuple
from PIL import Image

from src.core.logging_config import get_logger
from src.core.constants import SYSTEM_ROOT

logger = get_logger("WebP")

# Diretório de cache
WEBP_CACHE = SYSTEM_ROOT / "cache" / "webp"
WEBP_CACHE.mkdir(parents=True, exist_ok=True)


def is_webp(file_path: Path) -> bool:
    """
    Verifica se arquivo é WebP.
    
    Args:
        file_path: Caminho do arquivo
        
    Returns:
        True se é WebP
    """
    if not file_path.exists():
        return False
    
    # Verifica extensão
    if file_path.suffix.lower() == '.webp':
        return True
    
    # Verifica header
    try:
        with open(file_path, 'rb') as f:
            header = f.read(12)
            # RIFF....WEBP
            return header[:4] == b'RIFF' and header[8:12] == b'WEBP'
    except Exception:
        return False


def webp_to_png(
    webp_path: Path,
    output_path: Optional[Path] = None,
    use_cache: bool = True
) -> Tuple[bool, Optional[Path]]:
    """
    Converte WebP para PNG.
    Passo 96 do Checklist.
    
    Args:
        webp_path: Caminho do WebP
        output_path: Caminho de saída (opcional)
        use_cache: Usar cache?
        
    Returns:
        Tupla (sucesso, caminho_png)
    """
    if not webp_path.exists():
        logger.error(f"Arquivo não encontrado: {webp_path}")
        return False, None
    
    # Verificar cache
    cache_key = webp_path.stem + "_" + str(webp_path.stat().st_mtime_ns)[:10]
    cached_path = WEBP_CACHE / f"{cache_key}.png"
    
    if use_cache and cached_path.exists():
        logger.debug(f"Usando cache: {cached_path.name}")
        return True, cached_path
    
    # Definir saída
    if output_path is None:
        output_path = cached_path if use_cache else webp_path.with_suffix('.png')
    
    try:
        # Abrir WebP
        with Image.open(webp_path) as img:
            # Converter para RGBA se necessário
            if img.mode not in ('RGB', 'RGBA'):
                img = img.convert('RGBA')
            
            # Salvar como PNG
            img.save(output_path, 'PNG', optimize=True)
        
        logger.info(f"WebP convertido: {output_path.name}")
        return True, output_path
        
    except Exception as e:
        logger.error(f"Erro ao converter WebP: {e}")
        return False, None


def webp_bytes_to_png(webp_bytes: bytes) -> Tuple[bool, Optional[bytes]]:
    """
    Converte bytes WebP para bytes PNG.
    
    Args:
        webp_bytes: Bytes do WebP
        
    Returns:
        Tupla (sucesso, bytes_png)
    """
    try:
        with Image.open(io.BytesIO(webp_bytes)) as img:
            if img.mode not in ('RGB', 'RGBA'):
                img = img.convert('RGBA')
            
            output = io.BytesIO()
            img.save(output, 'PNG', optimize=True)
            
            return True, output.getvalue()
            
    except Exception as e:
        logger.error(f"Erro ao converter WebP bytes: {e}")
        return False, None


def ensure_compatible_format(file_path: Path) -> Path:
    """
    Garante que arquivo está em formato compatível.
    Converte WebP para PNG se necessário.
    
    Args:
        file_path: Caminho do arquivo
        
    Returns:
        Caminho do arquivo compatível
    """
    if is_webp(file_path):
        success, png_path = webp_to_png(file_path)
        if success and png_path:
            return png_path
    
    return file_path

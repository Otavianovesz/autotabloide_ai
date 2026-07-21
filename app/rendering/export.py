"""
Exportação — PNG e PDF no tamanho físico exato
==============================================
O DPI vai gravado no arquivo, então o resultado imprime no tamanho certo.
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image

from app.rendering.units import px_para_mm


def exportar_png(img: Image.Image, caminho: str | Path, dpi: int) -> Path:
    caminho = Path(caminho)
    caminho.parent.mkdir(parents=True, exist_ok=True)
    img.save(str(caminho), "PNG", dpi=(dpi, dpi))
    return caminho


def exportar_pdf(img: Image.Image, caminho: str | Path, dpi: int) -> Path:
    caminho = Path(caminho)
    caminho.parent.mkdir(parents=True, exist_ok=True)
    # resolution define o tamanho físico da página do PDF (px / dpi).
    img.convert("RGB").save(str(caminho), "PDF", resolution=float(dpi))
    return caminho


def exportar_pdf_multipagina(
    imagens: list[Image.Image], caminho: str | Path, dpi: int
) -> Path:
    """PDF com N páginas, cada uma no tamanho físico exato (1 cartaz/página)."""
    if not imagens:
        raise ValueError("nenhuma página para exportar")
    caminho = Path(caminho)
    caminho.parent.mkdir(parents=True, exist_ok=True)
    primeira, *resto = [im.convert("RGB") for im in imagens]
    primeira.save(str(caminho), "PDF", resolution=float(dpi),
                  save_all=True, append_images=resto)
    return caminho


def dimensoes_mm(img: Image.Image, dpi: int) -> tuple[float, float]:
    """Dimensões físicas (largura_mm, altura_mm) da imagem no DPI dado."""
    return (px_para_mm(img.width, dpi), px_para_mm(img.height, dpi))

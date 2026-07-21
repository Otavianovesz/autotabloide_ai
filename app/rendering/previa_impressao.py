"""Prévia de impressão (R-046, Fase 5 — Bloco D).

Mostra a página como sairá no PDF: a área de SANGRIA ao redor (o que a
guilhotina apara) e a MARGEM de segurança por dentro, marcadas em mm — o mesmo
pipeline medido em bytes das fases anteriores (tamanho físico real).
"""

from __future__ import annotations

from PIL import Image, ImageDraw

from app.rendering.units import mm_para_px

# cores das marcas (independentes do tema — é uma prova de impressão)
_COR_SANGRIA = (245, 245, 245)
_COR_MARCA = (0, 0, 0)
_COR_MARGEM = (0, 150, 200)


def previa_impressao(layout, pagina, dados, *, margem_mm: float = 5.0,
                     sangria_mm: float = 3.0, fundo_path=None) -> Image.Image:
    """Compõe a página e a emoldura com sangria + margem marcadas. O resultado
    tem o tamanho físico = página + 2×sangria (em px pelo dpi do layout)."""
    from app.rendering.compositor import compor_pagina

    base = compor_pagina(layout, pagina, dados, fundo_path=fundo_path).convert("RGB")
    dpi = layout.dpi
    s = int(round(mm_para_px(sangria_mm, dpi)))
    m = int(round(mm_para_px(margem_mm, dpi)))
    w, h = base.width, base.height

    tela = Image.new("RGB", (w + 2 * s, h + 2 * s), _COR_SANGRIA)
    tela.paste(base, (s, s))
    d = ImageDraw.Draw(tela)

    # retângulo da PÁGINA (linha de corte) e da MARGEM de segurança
    d.rectangle([s, s, s + w - 1, s + h - 1], outline=_COR_MARCA, width=max(1, dpi // 150))
    d.rectangle([s + m, s + m, s + w - 1 - m, s + h - 1 - m],
                outline=_COR_MARGEM, width=max(1, dpi // 200))

    # marcas de corte (crop marks) nos 4 cantos, na borda da sangria
    t = max(2, mm_para_px(2, dpi))
    for (cx, cy) in [(s, s), (s + w, s), (s, s + h), (s + w, s + h)]:
        d.line([(cx, cy - t), (cx, cy + t)], fill=_COR_MARCA, width=1)
        d.line([(cx - t, cy), (cx + t, cy)], fill=_COR_MARCA, width=1)
    return tela


def tamanho_fisico_mm(layout, *, sangria_mm: float = 3.0) -> tuple[float, float]:
    """O tamanho físico da prévia em mm (página + 2×sangria) — para conferir
    contra o PDF/tamanho real."""
    return (layout.largura_mm + 2 * sangria_mm, layout.altura_mm + 2 * sangria_mm)

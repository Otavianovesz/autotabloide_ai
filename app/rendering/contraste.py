"""Verificador de contraste (R-047, Fase 5 — Bloco D).

Avisa quando um texto (nome/preço/legal) fica pouco legível sobre a foto/arte
por baixo — e sugere a pílula (R-035) ou o contorno (R-034). Mede o contraste
na ÁREA REAL do texto sobre o fundo composto (imagem + arte), pela razão de
contraste do WCAG.
"""

from __future__ import annotations

from app.rendering.model import Regiao, TipoRegiao
from app.rendering.units import mm_para_px

_TIPOS_TEXTO = (TipoRegiao.NOME, TipoRegiao.UNIDADE, TipoRegiao.PRECO,
                TipoRegiao.TEXTO_LEGAL)
# limiar prático: abaixo disso a legibilidade sofre (o WCAG AA de texto grande
# é 3:1; o nome/preço do tabloide é grande, então 3.0 é o alvo).
LIMIAR_CONTRASTE = 3.0


def luminancia_relativa(rgb) -> float:
    """Luminância relativa WCAG de um RGB 0..255."""
    def canal(c: float) -> float:
        c = c / 255.0
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = rgb[0], rgb[1], rgb[2]
    return 0.2126 * canal(r) + 0.7152 * canal(g) + 0.0722 * canal(b)


def razao_contraste(a, b) -> float:
    """Razão de contraste WCAG entre duas cores (>= 1.0; 21 é preto×branco)."""
    la, lb = luminancia_relativa(a), luminancia_relativa(b)
    hi, lo = max(la, lb), min(la, lb)
    return (hi + 0.05) / (lo + 0.05)


def _cor_media(img, box) -> tuple[int, int, int]:
    """Cor média (RGB) da região `box`=(x,y,x2,y2) da imagem."""
    x, y, x2, y2 = box
    x, y = max(0, int(x)), max(0, int(y))
    x2, y2 = min(img.width, int(x2)), min(img.height, int(y2))
    if x2 <= x or y2 <= y:
        return (255, 255, 255)
    recorte = img.crop((x, y, x2, y2)).convert("RGB")
    px = list(recorte.getdata())
    n = len(px) or 1
    return (sum(p[0] for p in px) // n, sum(p[1] for p in px) // n,
            sum(p[2] for p in px) // n)


def _hex_para_rgb(cor: str) -> tuple[int, int, int]:
    from PIL import ImageColor
    try:
        return ImageColor.getrgb(cor)[:3]
    except ValueError:
        return (0, 0, 0)


def avisos_contraste(layout, pagina, dados, *, fundo_path=None,
                     minimo: float = LIMIAR_CONTRASTE) -> list[str]:
    """Lista de avisos de baixa legibilidade. Compõe o FUNDO (arte + imagens,
    com os textos escondidos), mede a cor média sob cada região de texto e
    compara com a cor do texto. Região com pílula/contorno já está protegida
    (não avisa). Nunca em silêncio (I2): devolve o texto do aviso p/ a UI."""
    from app.rendering.compositor import compor_pagina

    textos = [r for s in pagina.slots for r in s.regioes
              if r.tipo in _TIPOS_TEXTO and r.visivel]
    if not textos:
        return []
    escondidos = [(r, r.visivel) for r in textos]
    for r in textos:
        r.visivel = False
    try:
        fundo = compor_pagina(layout, pagina, dados, fundo_path=fundo_path)
    finally:
        for r, vis in escondidos:
            r.visivel = vis

    dpi = layout.dpi
    avisos: list[str] = []
    for r in textos:
        if r.pill or r.contorno or r.sombra:
            continue                       # já protegido (R-034/R-035)
        x = mm_para_px(r.rect.x_mm, dpi)
        y = mm_para_px(r.rect.y_mm, dpi)
        box = (x, y, x + mm_para_px(r.rect.larg_mm, dpi),
               y + mm_para_px(r.rect.alt_mm, dpi))
        media = _cor_media(fundo, box)
        razao = razao_contraste(_hex_para_rgb(r.cor), media)
        if razao < minimo:
            rotulo = r.nome or r.tipo.value
            avisos.append(
                f"“{rotulo}”: texto pouco legível sobre o fundo "
                f"(contraste {razao:.1f}:1) — ligue a pílula ou o contorno")
    return avisos

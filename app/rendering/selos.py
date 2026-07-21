"""
Selos na composição (F4.6)
==========================
Desenha selos (ícones legais/qualidade) num canto do slot:

  * **+18** — automático em bebida alcoólica (o enriquecimento marca `mais18`).
  * **Qualidade Belo Brasil** — quando o produto é marca própria (`marca_propria`).
    Enquanto não há o asset real, usamos um placeholder desenhado.

Vários selos podem coexistir; se caírem no mesmo canto, empilham sem sobrepor.
Cada selo tem canto configurável. A UI (ligar/desligar, canto) é do Bloco D.

Sem dependência de rasterizador SVG: se não houver um PNG de asset, o selo é
desenhado (badge). Um asset real (PNG) pode ser passado por ``imagem_path``.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


class Canto(str, Enum):
    SUPERIOR_ESQUERDO = "SUPERIOR_ESQUERDO"
    SUPERIOR_DIREITO = "SUPERIOR_DIREITO"
    INFERIOR_ESQUERDO = "INFERIOR_ESQUERDO"
    INFERIOR_DIREITO = "INFERIOR_DIREITO"


@dataclass
class Selo:
    tipo: str                       # "MAIS18" | "QUALIDADE" | livre
    canto: Canto = Canto.SUPERIOR_ESQUERDO
    imagem_path: str | None = None  # se houver PNG de asset, usa; senão desenha


def _fonte(fonte_path, tam):
    try:
        return ImageFont.truetype(str(fonte_path), max(6, tam))
    except Exception:
        return ImageFont.load_default()


def _badge_mais18(tam: int, fonte_path) -> Image.Image:
    img = Image.new("RGBA", (tam, tam), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    borda = max(2, tam // 18)
    d.ellipse([0, 0, tam - 1, tam - 1], fill=(198, 20, 20, 255), outline="white", width=borda)
    d.text((tam / 2, tam / 2), "+18", font=_fonte(fonte_path, round(tam * 0.40)),
           fill="white", anchor="mm")
    return img


def _badge_qualidade(tam: int, fonte_path) -> Image.Image:
    """PLACEHOLDER — trocar pelo asset real 'Qualidade Belo Brasil' quando vier."""
    img = Image.new("RGBA", (tam, tam), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    borda = max(2, tam // 18)
    d.ellipse([0, 0, tam - 1, tam - 1], fill=(20, 110, 70, 255), outline="white", width=borda)
    d.multiline_text((tam / 2, tam / 2), "Qualidade\nBelo\nBrasil",
                     font=_fonte(fonte_path, round(tam * 0.17)), fill="white",
                     anchor="mm", align="center", spacing=max(1, tam // 40))
    return img


def _badge_validade(tam: int, fonte_path) -> Image.Image:
    """RG-34: "De olho na validade" — âmbar, automático quando o item tem
    validade cadastrada (item perto de vencer é oferta de giro)."""
    img = Image.new("RGBA", (tam, tam), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    borda = max(2, tam // 18)
    d.ellipse([0, 0, tam - 1, tam - 1], fill=(217, 119, 6, 255),
              outline="white", width=borda)
    d.multiline_text((tam / 2, tam / 2), "De olho na\nVALIDADE",
                     font=_fonte(fonte_path, round(tam * 0.16)), fill="white",
                     anchor="mm", align="center", spacing=max(1, tam // 40))
    return img


def render_selo(selo: Selo, tam: int, fonte_path=None) -> Image.Image:
    if selo.imagem_path and Path(selo.imagem_path).exists():
        return Image.open(selo.imagem_path).convert("RGBA").resize((tam, tam))
    if selo.tipo == "MAIS18":
        return _badge_mais18(tam, fonte_path)
    if selo.tipo == "QUALIDADE":
        return _badge_qualidade(tam, fonte_path)
    if selo.tipo == "VALIDADE":
        return _badge_validade(tam, fonte_path)
    # genérico: círculo com a inicial
    img = Image.new("RGBA", (tam, tam), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.ellipse([0, 0, tam - 1, tam - 1], fill=(60, 60, 60, 255), outline="white", width=max(2, tam // 18))
    d.text((tam / 2, tam / 2), (selo.tipo[:2] or "?"), font=_fonte(fonte_path, round(tam * 0.35)),
           fill="white", anchor="mm")
    return img


def _posicao(canto: Canto, x, y, w, h, tam, margem, i) -> tuple[int, int]:
    """Posição do i-ésimo selo num canto (empilha para dentro sem sobrepor)."""
    desloc = i * (tam + margem)
    esquerda = canto in (Canto.SUPERIOR_ESQUERDO, Canto.INFERIOR_ESQUERDO)
    topo = canto in (Canto.SUPERIOR_ESQUERDO, Canto.SUPERIOR_DIREITO)
    px = x + margem if esquerda else x + w - tam - margem
    py = (y + margem + desloc) if topo else (y + h - tam - margem - desloc)
    return round(px), round(py)


def desenhar_selos(base: Image.Image, anchor_px, selos: list[Selo], fonte_path=None) -> None:
    """Desenha os selos nos cantos do retângulo âncora (px)."""
    x, y, w, h = anchor_px
    tam = max(24, round(min(w, h) * 0.20))
    margem = max(3, round(tam * 0.14))
    por_canto: dict[Canto, list[Selo]] = defaultdict(list)
    for s in selos:
        por_canto[s.canto].append(s)
    for canto, lista in por_canto.items():
        for i, s in enumerate(lista):
            img = render_selo(s, tam, fonte_path)
            base.paste(img, _posicao(canto, x, y, w, h, tam, margem, i), img)

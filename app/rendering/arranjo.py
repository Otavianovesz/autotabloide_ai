"""
Arranjo de múltiplas imagens num slot (F4.5)
============================================
Compõe 1..N imagens dentro do retângulo do slot, num dado modo. Tudo é desenhado
numa camada do tamanho exato do retângulo, então **nada vaza** para os vizinhos.

Modos:
  * ``LEQUE`` — sobrepostas em leque (uma parcialmente atrás da outra). Padrão
    para vários sabores/fragrâncias e para repetir a mesma foto.
  * ``LADO_A_LADO`` — separadas, sem sobrepor. Padrão para dois produtos (Camil e Rei).
  * ``GRADE`` — distribuição em grade (opção).

O modo é parâmetro (DIY, sobrescrevível). Com 1 imagem, o compositor usa o caminho
normal (aspect-fit) — este módulo trata o caso de várias.
"""

from __future__ import annotations

import math
from enum import Enum

from PIL import Image


class ModoArranjo(str, Enum):
    LEQUE = "LEQUE"
    LADO_A_LADO = "LADO_A_LADO"
    GRADE = "GRADE"


def _contain(img: Image.Image, max_w: float, max_h: float) -> Image.Image:
    """Aspect-fit: a imagem cabe inteira em max_w×max_h."""
    escala = min(max_w / img.width, max_h / img.height)
    return img.resize((max(1, round(img.width * escala)), max(1, round(img.height * escala))))


def _colar_centro(camada, img, x, y, w, h) -> None:
    fit = _contain(img, w, h)
    camada.paste(fit, (round(x + (w - fit.width) / 2), round(y + (h - fit.height) / 2)), fit)


def _lado_a_lado(camada, imagens, w, h) -> None:
    n = len(imagens)
    cel = w / n
    for i, img in enumerate(imagens):
        _colar_centro(camada, img, i * cel, 0, cel, h)


def _grade(camada, imagens, w, h) -> None:
    n = len(imagens)
    cols = math.ceil(math.sqrt(n))
    rows = math.ceil(n / cols)
    cw, ch = w / cols, h / rows
    for i, img in enumerate(imagens):
        linha, col = divmod(i, cols)
        _colar_centro(camada, img, col * cw, linha * ch, cw, ch)


def _leque(camada, imagens, w, h) -> None:
    n = len(imagens)
    fits = [_contain(img, w * 0.72, h * 0.92) for img in imagens]
    larg = max(f.width for f in fits)
    passo = min(larg * 0.6, (w - larg) / (n - 1)) if n > 1 else 0
    span = passo * (n - 1) + larg
    x0 = (w - span) / 2
    for i, f in enumerate(fits):
        ang = (i / (n - 1) - 0.5) * 14 if n > 1 else 0  # leque suave: -7°..+7°
        peca = f.rotate(ang, expand=True, resample=Image.BICUBIC) if ang else f
        cx = x0 + i * passo + (larg - peca.width) / 2
        cy = (h - peca.height) / 2
        camada.paste(peca, (round(cx), round(cy)), peca)  # paste clipa na camada


def compor_imagens(
    imagens: list[Image.Image], larg: int, alt: int, modo: ModoArranjo = ModoArranjo.LEQUE
) -> Image.Image:
    """Devolve uma camada RGBA (larg×alt) com as imagens compostas no modo dado."""
    camada = Image.new("RGBA", (larg, alt), (0, 0, 0, 0))
    imgs = [im.convert("RGBA") for im in imagens]
    if not imgs:
        return camada
    if len(imgs) == 1:
        _colar_centro(camada, imgs[0], 0, 0, larg, alt)
    elif modo == ModoArranjo.LADO_A_LADO:
        _lado_a_lado(camada, imgs, larg, alt)
    elif modo == ModoArranjo.GRADE:
        _grade(camada, imgs, larg, alt)
    else:
        _leque(camada, imgs, larg, alt)
    return camada

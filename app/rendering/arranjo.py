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
    """RODADA-125 (o dono, 03/08): "fica duas coisas pequenininhas" —
    o fatiamento em N colunas morreu. Agora é VITRINE EM CAMADAS: fotos
    GRANDES (n=2 → ~75% da zona) sobrepostas de leve, a 1ª na FRENTE e
    maior, as de trás um degrau menores e um fio mais altas; todas
    apoiadas na mesma base (produtos "no chão"). O paste clipa na
    camada — nada vaza (a lei do módulo)."""
    n = len(imagens)
    fator = 0.55 + 0.40 / n              # n=2→0,75 · n=3→0,68 da zona
    fits = [
        _contain(img, w * fator * (1 - 0.07 * i), h * (0.96 - 0.05 * i))
        for i, img in enumerate(imagens)
    ]
    passo = (w * 0.98 - fits[0].width) / (n - 1) if n > 1 else 0
    passo = max(passo, fits[0].width * 0.35)     # sobrepõe, nunca empilha
    span = passo * (n - 1) + fits[0].width
    esc_span = min(1.0, (w * 0.99) / span)       # zona estreita: encolhe junto
    if esc_span < 1.0:
        fits = [f.resize((max(1, round(f.width * esc_span)),
                          max(1, round(f.height * esc_span))))
                for f in fits]
        passo *= esc_span
        span = passo * (n - 1) + fits[0].width
    x0 = (w - span) / 2
    base = h * 0.98
    for i in range(n - 1, -1, -1):               # de trás para a frente
        f = fits[i]
        cx = x0 + i * passo
        cy = base - f.height - (h * 0.02 * i)    # o de trás, um fio acima
        camada.paste(f, (round(cx), round(max(0, cy))), f)


def _grade(camada, imagens, w, h) -> None:
    n = len(imagens)
    cols = math.ceil(math.sqrt(n))
    rows = math.ceil(n / cols)
    cw, ch = w / cols, h / rows
    for i, img in enumerate(imagens):
        linha, col = divmod(i, cols)
        _colar_centro(camada, img, col * cw, linha * ch, cw, ch)


def _leque(camada, imagens, w, h) -> None:
    """RODADA-125 v3 ("continua minúsculo e ruim"): o leque virou
    VITRINE — a 1ª foto (o produto da oferta) DOMINA (~80% da zona) e
    fica NA FRENTE (antes ia ao FUNDO da pilha e todas tinham o mesmo
    fator 0,72); as demais, um degrau menores, ATRÁS, na MESMA base,
    abrindo para as pontas com leve inclinação — cada uma mostra um
    "ombro" que ainda lê como outro produto."""
    n = len(imagens)
    dom = _contain(imagens[0], w * 0.80, h * 0.95)
    base = h * 0.985
    fatia = w * 0.14                    # o ombro visível de cada traseira
    x_dom = (w - dom.width) / 2
    traseiras = []
    for k, img in enumerate(imagens[1:]):
        f = _contain(img, dom.width * 0.72, h * 0.80)
        ang = 7.0 if k % 2 == 0 else -7.0
        f = f.rotate(ang, expand=True, resample=Image.BICUBIC)
        nivel = 1 + k // 2
        if k % 2 == 0:                  # esquerda
            x = x_dom - fatia * nivel
        else:                           # direita
            x = x_dom + dom.width + fatia * nivel - f.width
        traseiras.append((f, max(0.0, min(x, w - f.width))))
    for f, x in reversed(traseiras):    # as mais distantes primeiro
        camada.paste(f, (round(x), round(max(0, base - f.height))), f)
    camada.paste(dom, (round(x_dom),
                       round(max(0, base - dom.height))), dom)


def compor_imagens(
    imagens: list[Image.Image], larg: int, alt: int, modo: ModoArranjo = ModoArranjo.LEQUE
) -> Image.Image:
    """Devolve uma camada RGBA (larg×alt) com as imagens compostas no modo dado.

    v3 (o funil único de N fotos): (a) TODA imagem entra CROPADA pela
    bbox do alfa — a margem transparente do canvas quadrado do acervo
    fazia as fotos de trás "sumirem" (a fatia visível era transparência);
    (b) o TETO do caber é por GEOMETRIA da zona: célula pequena mostra
    menos fotos GRANDES em vez de N minúsculas (a Nivea desenhava 6 —
    a galeria RG-28 furava o teto porque só 3 dos 5 caminhos aparavam)."""
    camada = Image.new("RGBA", (larg, alt), (0, 0, 0, 0))
    imgs = []
    for im in imagens:
        rgba = im.convert("RGBA")
        bb = rgba.getchannel("A").getbbox()
        if bb:
            rgba = rgba.crop(bb)
        imgs.append(rgba)
    if not imgs:
        return camada
    if len(imgs) > 1:
        dom = _contain(imgs[0], larg * 0.80, alt * 0.95)
        fatia = larg * 0.14
        n_max = max(2, 1 + int((larg * 0.92 - dom.width) / fatia)) \
            if fatia > 0 else len(imgs)
        if len(imgs) > n_max:
            # seleção espaçada (as PONTAS sempre entram — a mesma
            # régua do selecionar_fotos_da_celula do serviço)
            idx = [round(i * (len(imgs) - 1) / (n_max - 1))
                   for i in range(n_max)]
            vistos: list[int] = []
            for k in idx:
                if k not in vistos:
                    vistos.append(k)
            imgs = [imgs[k] for k in vistos]
    if len(imgs) == 1:
        _colar_centro(camada, imgs[0], 0, 0, larg, alt)
    elif modo == ModoArranjo.LADO_A_LADO:
        _lado_a_lado(camada, imgs, larg, alt)
    elif modo == ModoArranjo.GRADE:
        _grade(camada, imgs, larg, alt)
    else:
        _leque(camada, imgs, larg, alt)
    return camada

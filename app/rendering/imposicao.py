"""
Imposição 2-em-1 (R-106 da Fase 11)
===================================
Dois cartazes A5 (148×210 mm) numa folha A4 **paisagem** (297×210 mm) para
economizar papel — imposição CONTROLADA.

**Decisão travada:** o 2-em-1 é SÓ no cartaz e SÓ se o dono ligar — NUNCA no
tabloide (o tabloide é 1 item por página no tamanho exato). Este módulo não é
importado por nenhuma tela do tabloide; a Fábrica (cartaz) o chama atrás de um
liga/desliga.

Cada metade da folha recebe uma A5, centrada; a última folha ímpar leva só a
esquerda. Marcas de corte opcionais ajudam o dono a cortar reto. O tamanho
físico é medido com rigor (o A4 sai 297×210 mm, cada metade 148,5 mm).
"""

from __future__ import annotations

from PIL import Image, ImageDraw

from app.rendering.units import mm_para_px

# A4 paisagem: duas A5 retrato lado a lado (148×2 = 296 ≈ 297)
A4_PAISAGEM_MM = (297.0, 210.0)


def _marcas_de_corte(canvas: Image.Image, meia_px: int, dpi: int) -> None:
    """Ticks curtos de corte: a linha central (onde o dono corta as duas A5) e
    os quatro cantos externos. Ticks curtos fora do miolo — não rabiscam a arte."""
    d = ImageDraw.Draw(canvas)
    w, h = canvas.size
    tick = round(mm_para_px(5, dpi))          # 5 mm de tick
    cor = (120, 120, 120)
    # corte central (topo e base)
    d.line((meia_px, 0, meia_px, tick), fill=cor, width=1)
    d.line((meia_px, h - tick, meia_px, h), fill=cor, width=1)
    # cantos externos (L invertido em cada quina)
    for x in (0, w - 1):
        d.line((x, 0, x, tick), fill=cor, width=1)
        d.line((x, h - tick, x, h), fill=cor, width=1)
    for y in (0, h - 1):
        d.line((0, y, tick, y), fill=cor, width=1)
        d.line((w - tick, y, w, y), fill=cor, width=1)


def impor_2em1(imagens_a5: list[Image.Image], dpi: int, *,
               marcas_corte: bool = False,
               folha_mm: tuple[float, float] = A4_PAISAGEM_MM) -> list[Image.Image]:
    """Impõe as imagens A5 em folhas A4 paisagem, 2 por folha.

    Devolve a lista de folhas (RGB). Cada A5 é centrada na sua metade; a folha
    ímpar final leva só a metade esquerda. NÃO redimensiona a A5 (respeita o
    tamanho físico) — assume que ela já veio no mesmo DPI.
    """
    if not imagens_a5:
        raise ValueError("nenhum cartaz A5 para impor")
    larg_mm, alt_mm = folha_mm
    w = round(mm_para_px(larg_mm, dpi))
    h = round(mm_para_px(alt_mm, dpi))
    meia = w // 2

    # Guarda dura (I2): o 2-em-1 NÃO redimensiona — se o cartaz não cabe na
    # metade da folha, RECUSA com erro nominal em vez de cortar/sobrepor calado
    # (o PIL paste corta em silêncio). O 2-em-1 é para A5; A4 não cabe.
    maior = max((im.width for im in imagens_a5), default=0)
    mais_alto = max((im.height for im in imagens_a5), default=0)
    if maior > meia or mais_alto > h:
        raise ValueError(
            "cartaz grande demais para o 2-em-1 (dois por folha) — ele só cabe "
            "num A5 (148×210 mm); escolha o modelo “Meia folha A5” ou desligue "
            "o “Dois por folha”")

    folhas: list[Image.Image] = []
    for i in range(0, len(imagens_a5), 2):
        par = imagens_a5[i:i + 2]
        canvas = Image.new("RGB", (w, h), "white")
        for k, im in enumerate(par):
            im = im.convert("RGB")
            ox = k * meia + max(0, (meia - im.width) // 2)   # centra na metade
            oy = max(0, (h - im.height) // 2)                # centra na vertical
            canvas.paste(im, (ox, oy))
        if marcas_corte:
            _marcas_de_corte(canvas, meia, dpi)
        folhas.append(canvas)
    return folhas

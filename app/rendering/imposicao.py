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


# --- R-144 (FASE 12): etiquetas de prateleira em LOTE -------------------------

A4_RETRATO_MM = (210.0, 297.0)


def impor_etiquetas(etiquetas: list[Image.Image], dpi: int, *,
                    folha_mm: tuple[float, float] = A4_RETRATO_MM,
                    marcas_corte: bool = True) -> list[Image.Image]:
    """R-144: dezenas de etiquetas por folha — a MESMA disciplina do 2-em-1
    (imposição CONTROLADA, só no fluxo do cartaz, nunca no tabloide).

    A grade N×M nasce do tamanho REAL da etiqueta (nada é redimensionado —
    o tamanho físico é sagrado); a grade inteira é centrada na folha e as
    marcas de corte seguem as linhas da grade. Etiqueta maior que a folha é
    RECUSADA com erro nominal (I2 — nunca corta em silêncio)."""
    if not etiquetas:
        raise ValueError("nenhuma etiqueta para impor")
    w = round(mm_para_px(folha_mm[0], dpi))
    h = round(mm_para_px(folha_mm[1], dpi))
    ew = max(im.width for im in etiquetas)
    eh = max(im.height for im in etiquetas)
    cols = w // ew
    linhas = h // eh
    if cols < 1 or linhas < 1:
        raise ValueError(
            "a etiqueta não cabe na folha — escolha um modelo menor "
            "(a etiqueta de prateleira é 100×70 mm) ou uma folha maior")
    por_folha = cols * linhas
    ox0 = (w - cols * ew) // 2               # a grade centrada na folha
    oy0 = (h - linhas * eh) // 2

    folhas: list[Image.Image] = []
    for i in range(0, len(etiquetas), por_folha):
        lote = etiquetas[i:i + por_folha]
        canvas = Image.new("RGB", (w, h), "white")
        for k, im in enumerate(lote):
            c, li = k % cols, k // cols
            canvas.paste(im.convert("RGB"), (ox0 + c * ew, oy0 + li * eh))
        if marcas_corte:
            d = ImageDraw.Draw(canvas)
            cor = (120, 120, 120)
            tick = round(mm_para_px(4, dpi))
            for c in range(cols + 1):        # verticais da grade
                x = ox0 + c * ew
                d.line((x, max(0, oy0 - tick), x, oy0), fill=cor, width=1)
                d.line((x, oy0 + linhas * eh, x,
                        min(h, oy0 + linhas * eh + tick)), fill=cor, width=1)
            for li in range(linhas + 1):     # horizontais da grade
                y = oy0 + li * eh
                d.line((max(0, ox0 - tick), y, ox0, y), fill=cor, width=1)
                d.line((ox0 + cols * ew, y,
                        min(w, ox0 + cols * ew + tick), y), fill=cor, width=1)
        folhas.append(canvas)
    return folhas

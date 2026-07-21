"""Galeria NATIVA da FASE 11 (Cartaz & Fábrica completos + inteligência).

Artefatos-chave (PIL puro, determinístico):
  * biblioteca de layouts de cartaz (A4 retrato/paisagem, A5, etiqueta);
  * cartaz com de/por + preço gigante + "-XX%" CALCULADO + validade no rodapé;
  * cartaz-relâmpago (com marca d'água RASCUNHO) e QR opcional;
  * kit ponta-de-gôndola (cartaz + etiqueta, mesmo dado);
  * 2-em-1 (dois A5 num A4 paisagem com marcas de corte);
  * inteligência só-leitura: saúde do acervo, ranking, histórico de preço.

Rodar::  python -m app.scripts.fotografar_fase11 saida_fase11/claro
         python -m app.scripts.fotografar_fase11 saida_fase11/escuro --tema=escuro
"""

from __future__ import annotations

import sys
from datetime import datetime
from decimal import Decimal
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from app.rendering import cartaz
from app.rendering.compositor import DadosProduto, compor_pagina
from app.rendering.imposicao import impor_2em1
from app.rendering.qr import aplicar_qr
from app.core.paths import SystemRoot

_ESCURO = "--tema=escuro" in sys.argv
FUNDO = (28, 30, 34) if _ESCURO else (245, 245, 247)
TEXTO = (220, 222, 226) if _ESCURO else (40, 44, 52)
LEGENDA = (150, 156, 165) if _ESCURO else (110, 116, 124)
CARD = (44, 47, 52) if _ESCURO else (255, 255, 255)
ACENTO = (245, 158, 11)
SUCESSO = (22, 163, 74)
BARRA_VAZIA = (70, 74, 80) if _ESCURO else (225, 228, 232)


def _fonte(px: int, negrito: bool = False):
    dir_f = SystemRoot().fontes
    for nome in (("Quicksand-Bold.ttf",) if negrito else ("Quicksand-Bold.ttf",)):
        p = dir_f / nome
        if p.exists():
            return ImageFont.truetype(str(p), px)
    return ImageFont.load_default(px)


def _produto_png(destino: Path, cor=(210, 40, 40)) -> str:
    """Um 'produto' simples (garrafa) sobre transparente — a foto oficial."""
    img = Image.new("RGBA", (400, 400), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([150, 90, 250, 340], radius=24, fill=(*cor, 255))
    d.rounded_rectangle([175, 50, 225, 110], radius=10, fill=(cor[0] - 30,
                        cor[1], cor[2], 255))
    d.rectangle([160, 170, 240, 250], fill=(250, 250, 250, 255))
    img.save(destino)
    return str(destino)


def _emoldurar(img: Image.Image, titulo: str, legenda: str = "") -> Image.Image:
    """Põe o cartaz sobre o fundo do tema, com título e legenda."""
    m = 28
    largura = max(img.width + 2 * m, 420)
    tela = Image.new("RGB", (largura, img.height + 110), FUNDO)
    d = ImageDraw.Draw(tela)
    d.text((m, 20), titulo, fill=TEXTO, font=_fonte(26))
    if legenda:
        d.text((m, 54), legenda, fill=LEGENDA, font=_fonte(16))
    # sombra leve do cartaz
    x = (largura - img.width) // 2
    tela.paste(img.convert("RGB"), (x, 86))
    d.rectangle([x - 1, 85, x + img.width, 86 + img.height], outline=(0, 0, 0)
                if not _ESCURO else (10, 10, 10))
    return tela


def _cartaz(fn, dados, *, escala=0.4) -> Image.Image:
    lay = fn()
    img = compor_pagina(lay, lay.paginas[0], dados)
    w = int(img.width * escala)
    h = int(img.height * escala)
    return img.resize((w, h))


def _dados(foto, *, de="12,90", por="9,90", validade="ATÉ 24/07"):
    return DadosProduto("Café Torrado 500g",
                        preco_por=Decimal(por.replace(",", ".")),
                        preco_de=Decimal(de.replace(",", ".")) if de else None,
                        imagem_path=foto, texto_legal=validade)


def _grade(imagens: list[Image.Image], titulos: list[str], cols=2) -> Image.Image:
    m = 20
    cw = max(i.width for i in imagens)
    ch = max(i.height for i in imagens)
    linhas = (len(imagens) + cols - 1) // cols
    tela = Image.new("RGB", (cols * cw + (cols + 1) * m,
                             linhas * (ch + 34) + m), FUNDO)
    d = ImageDraw.Draw(tela)
    for k, (im, tit) in enumerate(zip(imagens, titulos)):
        r, c = divmod(k, cols)
        x = m + c * (cw + m)
        y = m + r * (ch + 34)
        tela.paste(im.convert("RGB"), (x, y))
        d.text((x, y + ch + 6), tit, fill=TEXTO, font=_fonte(16))
    return tela


# --- inteligência (cartões PIL) ----------------------------------------------------

def _card(titulo: str, largura=520, altura=360) -> tuple[Image.Image, ImageDraw.ImageDraw]:
    tela = Image.new("RGB", (largura, altura), FUNDO)
    d = ImageDraw.Draw(tela)
    d.rounded_rectangle([12, 12, largura - 12, altura - 12], radius=14, fill=CARD)
    d.text((30, 28), titulo, fill=TEXTO, font=_fonte(24))
    return tela, d


def _saude() -> Image.Image:
    tela, d = _card("Saúde do acervo")
    metricas = [("Com foto", 82), ("Com código de barras", 61),
                ("Com preço", 95), ("Com categoria", 88)]
    y = 84
    for rot, pct in metricas:
        d.text((30, y), f"{rot}", fill=TEXTO, font=_fonte(17))
        d.rounded_rectangle([30, y + 26, 490, y + 44], radius=9, fill=BARRA_VAZIA)
        cor = SUCESSO if pct >= 80 else ACENTO
        d.rounded_rectangle([30, y + 26, 30 + int(460 * pct / 100), y + 44],
                            radius=9, fill=cor)
        d.text((450, y), f"{pct}%", fill=LEGENDA, font=_fonte(15))
        y += 66
    return tela


def _ranking() -> Image.Image:
    tela, d = _card("Mais ofertados (carros-chefe)")
    dados = [("Arroz Tio João 5kg", 12), ("Café Torrado 500g", 9),
             ("Feijão Carioca 1kg", 8), ("Óleo de Soja 900ml", 7),
             ("Leite Integral 1L", 6)]
    y = 84
    for i, (nome, n) in enumerate(dados, 1):
        d.text((30, y), f"{i}.  {nome}", fill=TEXTO, font=_fonte(18))
        d.text((430, y), f"{n} ed.", fill=LEGENDA, font=_fonte(16))
        y += 48
    return tela


def _historico() -> Image.Image:
    tela, d = _card("Histórico de preço — Arroz Tio João 5kg")
    precos = [26.9, 25.9, 24.9, 23.5, 24.9, 22.9, 19.9]
    lo, hi = min(precos), max(precos)
    x0, x1, y0, y1 = 40, 490, 300, 90
    n = len(precos)

    def _xy(i, v):
        x = x0 + (x1 - x0) * i / (n - 1)
        y = y0 + (y1 - y0) * (v - lo) / (hi - lo)
        return x, y

    pts = [_xy(i, v) for i, v in enumerate(precos)]
    for a, b in zip(pts, pts[1:]):
        d.line([a, b], fill=ACENTO, width=3)
    for i, v in enumerate(precos):
        x, y = _xy(i, v)
        eh_menor = v == lo
        r = 7 if eh_menor else 4
        d.ellipse([x - r, y - r, x + r, y + r],
                  fill=SUCESSO if eh_menor else ACENTO)
    d.text((30, 320), f"Menor preço do histórico: R$ {lo:.2f}".replace(".", ","),
           fill=SUCESSO, font=_fonte(16))
    return tela


# ==================================================================================

def main() -> None:
    saida = Path(sys.argv[1]) if len(sys.argv) > 1 and not sys.argv[1].startswith("--") \
        else Path("saida_fase11") / ("escuro" if _ESCURO else "claro")
    saida.mkdir(parents=True, exist_ok=True)
    foto = _produto_png(saida / "_produto.png")
    qr_texto = "https://belobrasil.com.br/encarte"

    # 1) biblioteca de layouts
    minis, tits = [], []
    for nome, fn in cartaz.PRESETS_CARTAZ.items():
        if nome.startswith("Cartaz 10"):
            continue
        d = _dados(foto)
        minis.append(_cartaz(fn, d, escala=0.28))
        tits.append(nome)
    _grade(minis, tits, cols=2).save(saida / "biblioteca_layouts.png")

    # 2) cartaz de/por com % + preço gigante + validade
    cz = _cartaz(cartaz.layout_cartaz_a5, _dados(foto), escala=0.55)
    _emoldurar(cz, "Cartaz completo",
               "de/por · -23% calculado · preço gigante · validade no rodapé"
               ).save(saida / "cartaz_de_por_desconto.png")

    # 3) cartaz-relâmpago (RASCUNHO)
    from app.rendering.marca_dagua import carimbar_rascunho
    lay = cartaz.layout_cartaz_exemplo()
    relamp = carimbar_rascunho(compor_pagina(lay, lay.paginas[0], _dados(foto)))
    _emoldurar(relamp.resize((int(relamp.width * 0.5), int(relamp.height * 0.5))),
               "Cartaz-relâmpago", "do produto ao PDF num clique (marca RASCUNHO)"
               ).save(saida / "cartaz_relampago.png")

    # 4) QR opcional
    com_qr, _ = aplicar_qr(compor_pagina(lay, lay.paginas[0], _dados(foto)),
                           qr_texto, lado_px=260, margem_px=40)
    _emoldurar(com_qr.resize((int(com_qr.width * 0.5), int(com_qr.height * 0.5))),
               "QR opcional", "link do encarte — gerado localmente, desligado por padrão"
               ).save(saida / "qr_no_cartaz.png")

    # 5) kit ponta-de-gôndola (cartaz + etiqueta)
    d = _dados(foto)
    cartaz_img = _cartaz(cartaz.layout_cartaz_a5, d, escala=0.42)
    etiq_img = _cartaz(cartaz.layout_etiqueta, d, escala=0.66)
    _grade([cartaz_img, etiq_img], ["Cartaz A5", "Etiqueta 100×70 mm"], cols=2
           ).save(saida / "kit_gondola.png")

    # 6) 2-em-1 (A4 paisagem com marcas de corte)
    lay_a5 = cartaz.layout_cartaz_a5()
    a5 = compor_pagina(lay_a5, lay_a5.paginas[0], _dados(foto))
    a5b = compor_pagina(lay_a5, lay_a5.paginas[0],
                        _dados(_produto_png(saida / "_prod2.png", cor=(30, 90, 200)),
                               de="8,90", por="6,49"))
    folha = impor_2em1([a5, a5b], lay_a5.dpi, marcas_corte=True)[0]
    _emoldurar(folha.resize((int(folha.width * 0.34), int(folha.height * 0.34))),
               "Dois por folha (2-em-1)",
               "dois A5 num A4 paisagem, com marcas de corte — só no cartaz"
               ).save(saida / "dois_por_folha.png")

    # 7) inteligência (só leitura)
    _saude().save(saida / "inteligencia_saude.png")
    _ranking().save(saida / "inteligencia_ranking.png")
    _historico().save(saida / "inteligencia_historico.png")

    # 8) GIF: cartaz-relâmpago do Almoxarifado ao PDF em 1 clique
    if not _ESCURO:
        _gif_relampago(saida, foto)

    for lixo in ("_produto.png", "_prod2.png"):
        (saida / lixo).unlink(missing_ok=True)
    print(f"galeria em {saida}")


def _quadro(texto: str, cartaz_img=None, larg=520, alt=680) -> Image.Image:
    q = Image.new("RGB", (larg, alt), FUNDO)
    d = ImageDraw.Draw(q)
    d.text((24, 20), texto, fill=TEXTO, font=_fonte(24))
    if cartaz_img is not None:
        x = (larg - cartaz_img.width) // 2
        q.paste(cartaz_img.convert("RGB"), (x, 70))
    return q


def _gif_relampago(saida: Path, foto: str) -> None:
    """~15 s: seleciona no Almoxarifado → 1 clique → cartaz → RASCUNHO → PDF."""
    from app.rendering.marca_dagua import carimbar_rascunho
    lay = cartaz.layout_cartaz_exemplo()
    dados = _dados(foto)
    cz = compor_pagina(lay, lay.paginas[0], dados)
    esc = 0.42
    cz_p = cz.resize((int(cz.width * esc), int(cz.height * esc)))
    cz_rasc = carimbar_rascunho(cz).resize(cz_p.size)
    prod = Image.open(foto).convert("RGBA").resize((220, 220))
    prod_card = Image.new("RGB", cz_p.size, CARD)
    prod_card.paste(prod, ((cz_p.width - 220) // 2, 120), prod)

    quadros = [
        _quadro("Almoxarifado — “Café Torrado 500g”", prod_card),
        _quadro("Botão direito → Cartaz-relâmpago…", prod_card),
        _quadro("Compondo o cartaz…", cz_p),
        _quadro("Marca RASCUNHO (sem aprovação)", cz_rasc),
        _quadro("PDF pronto — no tamanho exato (10×15 cm)", cz_rasc),
    ]
    duracoes = [1600, 1600, 1400, 1800, 2600]
    quadros[0].save(saida / "relampago_1clique.gif", save_all=True,
                    append_images=quadros[1:], duration=duracoes, loop=0)


if __name__ == "__main__":
    main()

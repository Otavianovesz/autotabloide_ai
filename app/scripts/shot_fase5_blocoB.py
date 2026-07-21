"""FASE 5 — Bloco B (passos 25/31): prova visual da máscara, do enquadramento
e da célula-herói (máscara circular + pílula atrás do nome + preço com
contorno). Sai do COMPOSITOR (Pillow), então o texto é legível.

Uso::

    python -m app.scripts.shot_fase5_blocoB
"""

from __future__ import annotations

from decimal import Decimal
from pathlib import Path

from PIL import Image, ImageDraw

from app.rendering.compositor import DadosProduto, ImagemSlot, compor_pagina
from app.rendering.model import (
    Ajuste, Alinhamento, LayoutDef, Mascara, Pagina, PapelPreco, Regiao,
    Retangulo, Slot, TipoRegiao,
)

SAIDA = Path("saida_fase5")


def _foto_demo(caminho: Path) -> str:
    """Uma foto com conteúdo reconhecível (gradiente + grade) — a máscara e o
    zoom ficam evidentes."""
    im = Image.new("RGB", (400, 400))
    px = im.load()
    for y in range(400):
        for x in range(400):
            px[x, y] = (40 + x // 2, 80 + y // 3, 200 - x // 3)
    d = ImageDraw.Draw(im)
    for i in range(0, 400, 50):
        d.line([(i, 0), (i, 400)], fill=(255, 255, 255), width=2)
        d.line([(0, i), (400, i)], fill=(255, 255, 255), width=2)
    d.ellipse([150, 150, 250, 250], fill=(255, 215, 0))    # miolo amarelo
    im.save(caminho)
    return str(caminho)


def _pagina_mascaras(foto: str):
    regs = []
    for i, m in enumerate((Mascara.RETANGULO, Mascara.ARREDONDADO, Mascara.CIRCULO)):
        regs.append(Regiao(TipoRegiao.IMAGEM, Retangulo(4 + i * 34, 8, 30, 30),
                           ajuste=Ajuste.PREENCHER, mascara=m, mascara_raio_mm=6,
                           nome=m.value))
    lay = LayoutDef(106, 46, dpi=200, paginas=[Pagina([Slot("s", regs)])])
    return compor_pagina(lay, lay.paginas[0], {"s": DadosProduto("x", imagem_path=foto)})


def _pagina_enquadramento(foto: str):
    reg = Regiao(TipoRegiao.IMAGEM, Retangulo(0, 0, 34, 34),
                 ajuste=Ajuste.PREENCHER, mascara=Mascara.RETANGULO)
    base = Image.new("RGB", (1, 1))
    partes = []
    for zoom in (1.0, 1.6, 2.5):
        lay = LayoutDef(34, 34, dpi=200, paginas=[Pagina([Slot("s", [reg])])])
        d = DadosProduto("x", imagens=[ImagemSlot(foto, zoom=zoom)])
        partes.append(compor_pagina(lay, lay.paginas[0], {"s": d}))
    larg = sum(p.width for p in partes) + 20
    faixa = Image.new("RGB", (larg, partes[0].height), (255, 255, 255))
    x = 0
    for p in partes:
        faixa.paste(p, (x, 0)); x += p.width + 10
    return faixa


def _pagina_heroi(foto: str):
    img = Regiao(TipoRegiao.IMAGEM, Retangulo(10, 6, 60, 60),
                 ajuste=Ajuste.PREENCHER, mascara=Mascara.CIRCULO)
    nome = Regiao(TipoRegiao.NOME, Retangulo(4, 68, 72, 12), cor="#ffffff",
                  alinhamento=Alinhamento.CENTRO, tamanho_max_pt=22,
                  pill=True, pill_cor="#111111", pill_opacidade=205)
    preco = Regiao(TipoRegiao.PRECO, Retangulo(4, 82, 72, 20), cor="#ffffff",
                   alinhamento=Alinhamento.CENTRO, tamanho_max_pt=40,
                   papel_preco=PapelPreco.UNICO, contorno=True, cor_efeito="#000000")
    lay = LayoutDef(80, 104, dpi=200, paginas=[Pagina([Slot("s", [img, nome, preco])])])
    d = DadosProduto("Refrigerante Gelado", preco_por=Decimal("5.99"),
                     imagem_path=foto)
    return compor_pagina(lay, lay.paginas[0], {"s": d})


def main() -> None:
    SAIDA.mkdir(parents=True, exist_ok=True)
    foto = _foto_demo(SAIDA / "_foto_demo.png")
    _pagina_mascaras(foto).save(SAIDA / "blocoB_mascaras.png")
    _pagina_enquadramento(foto).save(SAIDA / "blocoB_enquadramento.png")
    _pagina_heroi(foto).save(SAIDA / "blocoB_heroi.png")
    for n in ("blocoB_mascaras", "blocoB_enquadramento", "blocoB_heroi"):
        print(f"salvo: {SAIDA / (n + '.png')}")


if __name__ == "__main__":
    main()

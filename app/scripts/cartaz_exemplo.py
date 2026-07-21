"""
Cartaz de exemplo (para provar o pipeline de renderização)
==========================================================
Gera uma arte de fundo e uma imagem de produto SINTÉTICAS, monta um LayoutDef de
cartaz (10×15 cm) e compõe/exporta. Quando o Otaviano mandar a arte real, é só
trocar ``fundo_path`` e ``imagem_path`` — o resto continua igual.
"""

from __future__ import annotations

from decimal import Decimal
from pathlib import Path

from PIL import Image, ImageDraw

from app.rendering.compositor import DadosProduto, compor_pagina
from app.rendering.model import (
    Ajuste,
    Alinhamento,
    LayoutDef,
    Pagina,
    PapelPreco,
    Regiao,
    Retangulo,
    Slot,
    SubtipoPreco,
    TipoRegiao,
)
from app.rendering.units import mm_para_px


def gerar_arte_sintetica(caminho: Path, larg_mm: float, alt_mm: float, dpi: int) -> Path:
    """Uma arte de fundo fake: faixa vermelha no topo, moldura, rodapé."""
    w = round(mm_para_px(larg_mm, dpi))
    h = round(mm_para_px(alt_mm, dpi))
    img = Image.new("RGB", (w, h), "#fdf6ec")
    d = ImageDraw.Draw(img)
    faixa = round(mm_para_px(22, dpi))
    d.rectangle([0, 0, w, faixa], fill="#d21f26")
    d.rectangle([round(w * 0.06), round(h * 0.015), w - round(w * 0.06), faixa - round(h * 0.01)],
                outline="#ffffff", width=max(2, w // 300))
    borda = max(3, w // 200)
    d.rectangle([borda, borda, w - borda, h - borda], outline="#d21f26", width=borda)
    rodape = round(mm_para_px(6, dpi))
    d.rectangle([0, h - rodape, w, h], fill="#222222")
    caminho.parent.mkdir(parents=True, exist_ok=True)
    img.save(str(caminho), "PNG", dpi=(dpi, dpi))
    return caminho


def gerar_imagem_produto_sintetica(caminho: Path) -> Path:
    """Uma 'garrafa' fake em RGBA com fundo transparente (exercita o alfa)."""
    w, h = 700, 1000
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([230, 40, 470, 180], radius=30, fill=(40, 120, 200, 255))   # tampa
    d.rectangle([300, 180, 400, 260], fill=(40, 120, 200, 255))                     # gargalo
    d.rounded_rectangle([170, 260, 530, 950], radius=90, fill=(70, 160, 230, 255))  # corpo
    d.rounded_rectangle([210, 470, 490, 760], radius=20, fill=(255, 255, 255, 235)) # rótulo
    caminho.parent.mkdir(parents=True, exist_ok=True)
    img.save(str(caminho), "PNG")
    return caminho


def layout_cartaz(larg_mm: float, alt_mm: float, dpi: int, fundo: str | None) -> LayoutDef:
    """Cartaz de gôndola: 1 página, 1 slot, com IMAGEM + NOME + PREÇO (por/de)."""
    slot = Slot(
        id="cartaz",
        regioes=[
            Regiao(TipoRegiao.IMAGEM, Retangulo(12, 24, 76, 72), ajuste=Ajuste.CONTER),
            Regiao(
                TipoRegiao.NOME, Retangulo(6, 98, 88, 16),
                fonte="Roboto-Bold.ttf", tamanho_max_pt=34, cor="#222222",
                alinhamento=Alinhamento.CENTRO, incluir_unidade=True,
            ),
            Regiao(
                TipoRegiao.PRECO, Retangulo(6, 114, 88, 28),
                fonte="Roboto-Bold.ttf", tamanho_max_pt=110, cor="#d21f26",
                alinhamento=Alinhamento.CENTRO,
                subtipo_preco=SubtipoPreco.SEPARADO, papel_preco=PapelPreco.POR,
                tamanho_centavos_pt=48, fonte_centavos="Roboto-Bold.ttf",
            ),
            Regiao(
                TipoRegiao.PRECO, Retangulo(6, 141, 88, 6),
                fonte="Roboto-Regular.ttf", tamanho_max_pt=14, cor="#dddddd",
                alinhamento=Alinhamento.CENTRO,
                subtipo_preco=SubtipoPreco.COMPLETO, papel_preco=PapelPreco.DE,
            ),
        ],
    )
    return LayoutDef(larg_mm, alt_mm, dpi=dpi, arquivo_fundo=fundo, paginas=[Pagina([slot])])


def gerar_cartaz_demo(dir_saida: Path, dpi: int = 300) -> dict:
    """Gera arte + produto sintéticos, compõe e exporta PNG/PDF. Retorna caminhos."""
    from app.rendering.export import dimensoes_mm, exportar_pdf, exportar_png

    dir_saida.mkdir(parents=True, exist_ok=True)
    larg_mm, alt_mm = 100.0, 150.0
    fundo = gerar_arte_sintetica(dir_saida / "arte_fundo.png", larg_mm, alt_mm, dpi)
    produto_img = gerar_imagem_produto_sintetica(dir_saida / "produto.png")

    layout = layout_cartaz(larg_mm, alt_mm, dpi, str(fundo))
    dados = DadosProduto(
        nome="Refrigerante Kitubaina",
        unidade="1,5L",
        preco_por=Decimal("5.50"),
        preco_de=Decimal("6.90"),
        imagem_path=str(produto_img),
    )
    img = compor_pagina(layout, layout.paginas[0], dados, fundo_path=str(fundo))
    png = exportar_png(img, dir_saida / "cartaz.png", dpi)
    pdf = exportar_pdf(img, dir_saida / "cartaz.pdf", dpi)
    larg, alt = dimensoes_mm(img, dpi)
    return {
        "png": str(png), "pdf": str(pdf),
        "px": img.size, "mm": (round(larg, 2), round(alt, 2)),
    }


if __name__ == "__main__":
    import sys

    saida = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("saida_demo")
    print(gerar_cartaz_demo(saida))

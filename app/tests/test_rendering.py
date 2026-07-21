"""Testes da renderização (Fase 2)."""

import json
import warnings

from PIL import Image, ImageChops

from app.core.paths import SystemRoot
from app.rendering.compositor import DadosProduto, compor_pagina
from app.rendering.model import (
    Ajuste,
    LayoutDef,
    Pagina,
    Regiao,
    Retangulo,
    Slot,
    TipoRegiao,
)
from app.rendering.text_fit import ajustar_texto
from app.rendering.units import mm_para_px, pt_para_px, px_para_mm
from app.scripts.cartaz_exemplo import gerar_cartaz_demo

FONTES = SystemRoot().fontes
ROBOTO = FONTES / "Roboto-Regular.ttf"


# --- conversões de unidade ----------------------------------------------------


def test_mm_para_px_300dpi():
    # 100 mm @ 300 dpi = 100/25.4*300 ≈ 1181 px
    assert round(mm_para_px(100, 300)) == 1181
    assert round(px_para_mm(1181, 300)) == 100


# --- modelo serializa para JSON (vai em Layout.estrutura_json) -----------------


def test_layout_roundtrip_json():
    layout = LayoutDef(
        100, 150, dpi=300,
        paginas=[Pagina([Slot("s", [Regiao(TipoRegiao.NOME, Retangulo(1, 2, 3, 4))])])],
    )
    texto = json.dumps(layout.to_dict(), ensure_ascii=False)
    recuperado = LayoutDef.from_dict(json.loads(texto))
    assert recuperado.to_dict() == layout.to_dict()


# --- ajuste de fonte: SÓ REDUZ, NUNCA AUMENTA ---------------------------------


def test_fonte_usa_o_teto_quando_cabe():
    # texto curto numa caixa grande: usa o tamanho máximo (não aumenta além dele).
    aj = ajustar_texto("Oi", ROBOTO, larg_px=1000, alt_px=400, tamanho_max_pt=40, dpi=300)
    assert aj.tamanho_pt == 40
    assert len(aj.linhas) == 1


def test_fonte_reduz_quando_nao_cabe():
    # texto longo numa caixa apertada: precisa reduzir abaixo do teto.
    aj = ajustar_texto(
        "Refrigerante Kitubaina Sabor Guaraná Garrafa 1,5L",
        ROBOTO, larg_px=300, alt_px=120, tamanho_max_pt=40, dpi=300,
    )
    assert aj.tamanho_pt < 40


def test_fonte_quebra_em_varias_linhas():
    aj = ajustar_texto(
        "Palavra Outra Mais Texto Aqui Para Quebrar",
        ROBOTO, larg_px=400, alt_px=2000, tamanho_max_pt=30, dpi=300,
    )
    assert len(aj.linhas) >= 2


# --- imagem: aspect-fit (CONTER) não vaza do retângulo ------------------------


def test_aspect_fit_nao_vaza_do_retangulo(tmp_path):
    dpi = 300
    layout = LayoutDef(
        100, 100, dpi=dpi,
        paginas=[Pagina([Slot("s", [
            Regiao(TipoRegiao.IMAGEM, Retangulo(20, 30, 40, 25), ajuste=Ajuste.CONTER)
        ])])],
    )
    # imagem quadrada opaca vermelha
    prod = Image.new("RGBA", (500, 500), (255, 0, 0, 255))
    p = tmp_path / "prod.png"
    prod.save(p)
    img = compor_pagina(layout, layout.paginas[0], DadosProduto("x", imagem_path=str(p)))

    # onde há vermelho, tem de estar dentro do retângulo da região
    base_branca = Image.new("RGB", img.size, "white")
    bbox = ImageChops.difference(img, base_branca).getbbox()
    x = round(mm_para_px(20, dpi)); y = round(mm_para_px(30, dpi))
    w = round(mm_para_px(40, dpi)); h = round(mm_para_px(25, dpi))
    assert bbox is not None
    assert bbox[0] >= x - 1 and bbox[1] >= y - 1
    assert bbox[2] <= x + w + 1 and bbox[3] <= y + h + 1


# --- exportação no tamanho físico exato ---------------------------------------


def test_exporta_no_tamanho_exato(tmp_path):
    warnings.filterwarnings("ignore")
    info = gerar_cartaz_demo(tmp_path, dpi=300)
    larg_mm, alt_mm = info["mm"]
    assert abs(larg_mm - 100) < 0.1
    assert abs(alt_mm - 150) < 0.1

    # PNG carrega o DPI correto
    im = Image.open(info["png"])
    assert round(im.info["dpi"][0]) == 300

    # PDF: página no tamanho físico exato (via mediabox)
    import pypdf

    box = pypdf.PdfReader(info["pdf"]).pages[0].mediabox
    larg_pdf_mm = float(box.width) / 72 * 25.4
    alt_pdf_mm = float(box.height) / 72 * 25.4
    assert abs(larg_pdf_mm - 100) < 0.1
    assert abs(alt_pdf_mm - 150) < 0.1


def test_preco_de_e_por_desenham(tmp_path):
    # o cartaz demo tem preço "por" (vermelho) e "de": a imagem não pode ficar em branco
    info = gerar_cartaz_demo(tmp_path, dpi=150)
    img = Image.open(info["png"]).convert("RGB")
    cores = img.getcolors(maxcolors=1_000_000)
    # existe vermelho forte do preço "por"
    assert any(c > 50 and r > 150 and g < 90 and b < 90 for c, (r, g, b) in cores)

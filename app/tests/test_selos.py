"""Testes dos selos (F4.6): render, posicionamento por canto, empilhamento, integração."""

from PIL import Image

from app.rendering.selos import Canto, Selo, desenhar_selos, render_selo


def test_render_mais18():
    img = render_selo(Selo("MAIS18"), 100)
    assert img.size == (100, 100)
    assert img.getchannel("A").getbbox() is not None


def test_render_usa_asset_png_se_existir(tmp_path):
    p = tmp_path / "selo.png"
    Image.new("RGBA", (50, 50), (0, 255, 0, 255)).save(p)
    img = render_selo(Selo("QUALQUER", imagem_path=str(p)), 80)
    assert img.size == (80, 80)


def test_desenha_no_canto_superior_esquerdo():
    base = Image.new("RGBA", (400, 400), (0, 0, 0, 0))
    desenhar_selos(base, (0, 0, 400, 400), [Selo("MAIS18", Canto.SUPERIOR_ESQUERDO)])
    assert base.crop((0, 0, 130, 130)).getchannel("A").getbbox() is not None


def test_dois_selos_no_mesmo_canto_empilham():
    base = Image.new("RGBA", (400, 400), (0, 0, 0, 0))
    selos = [Selo("MAIS18", Canto.SUPERIOR_ESQUERDO), Selo("QUALIDADE", Canto.SUPERIOR_ESQUERDO)]
    desenhar_selos(base, (0, 0, 400, 400), selos)
    coluna = base.crop((0, 0, 130, 400)).getchannel("A").getbbox()
    assert coluna is not None and coluna[3] > 130  # estende para baixo (empilhou)


def test_compositor_desenha_selo_quando_mais18(tmp_path):
    from app.rendering.compositor import DadosProduto, compor_pagina
    from app.rendering.model import LayoutDef, Pagina, Regiao, Retangulo, Slot, TipoRegiao

    Image.new("RGBA", (200, 200), (0, 0, 255, 255)).save(tmp_path / "p.png")
    layout = LayoutDef(
        100, 100, dpi=150,
        paginas=[Pagina([Slot("s", [Regiao(TipoRegiao.IMAGEM, Retangulo(10, 10, 80, 80))])])],
    )
    base = dict(nome="Cerveja", imagem_path=str(tmp_path / "p.png"))
    sem = compor_pagina(layout, layout.paginas[0], DadosProduto(**base))
    com = compor_pagina(layout, layout.paginas[0], DadosProduto(**base, mais18=True))
    assert list(sem.getdata()) != list(com.getdata())  # o selo mudou a composição

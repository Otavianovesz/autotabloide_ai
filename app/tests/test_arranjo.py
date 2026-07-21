"""Testes do arranjo de múltiplas imagens (F4.5) — tamanho, não-vazamento, modos."""

from PIL import Image

from app.rendering.arranjo import ModoArranjo, compor_imagens


def _img(cor, w=100, h=200):
    return Image.new("RGBA", (w, h), cor)


def test_camada_tem_tamanho_exato_do_slot():
    c = compor_imagens([_img("red"), _img("blue")], 300, 200, ModoArranjo.LADO_A_LADO)
    assert c.size == (300, 200)


def test_leque_nao_vaza_do_retangulo():
    c = compor_imagens([_img("red")] * 3, 300, 200, ModoArranjo.LEQUE)
    bbox = c.getchannel("A").getbbox()
    assert bbox is not None
    assert bbox[0] >= 0 and bbox[1] >= 0 and bbox[2] <= 300 and bbox[3] <= 200


def test_lado_a_lado_preenche_as_duas_metades():
    c = compor_imagens(
        [_img("red", 200, 200), _img("blue", 200, 200)], 400, 200, ModoArranjo.LADO_A_LADO
    )
    esq = c.crop((0, 0, 200, 200)).getchannel("A").getbbox()
    dir_ = c.crop((200, 0, 400, 200)).getchannel("A").getbbox()
    assert esq is not None and dir_ is not None


def test_uma_imagem_fica_centralizada():
    c = compor_imagens([_img("red", 100, 100)], 300, 300, ModoArranjo.LEQUE)
    esq, topo, dir_, base = c.getchannel("A").getbbox()
    assert abs(esq - (300 - dir_)) <= 2 and abs(topo - (300 - base)) <= 2


def test_compositor_aceita_lista_de_imagens(tmp_path):
    from app.rendering.compositor import DadosProduto, ImagemSlot, compor_pagina
    from app.rendering.model import LayoutDef, Pagina, Regiao, Retangulo, Slot, TipoRegiao

    for i in range(2):
        Image.new("RGBA", (200, 200), (255, 0, 0, 255)).save(tmp_path / f"i{i}.png")
    layout = LayoutDef(
        100, 100, dpi=150,
        paginas=[Pagina([Slot("s", [Regiao(TipoRegiao.IMAGEM, Retangulo(10, 10, 80, 80))])])],
    )
    dados = DadosProduto(
        "x",
        imagens=[ImagemSlot(str(tmp_path / "i0.png")), ImagemSlot(str(tmp_path / "i1.png"))],
        modo_arranjo=ModoArranjo.LADO_A_LADO,
    )
    img = compor_pagina(layout, layout.paginas[0], dados)
    assert img.getbbox() is not None  # desenhou algo

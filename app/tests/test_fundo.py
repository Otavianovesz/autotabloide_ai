"""Testes da F4.2 — a lógica de recorte/normalização (sem rembg, com imagem sintética)."""

from PIL import Image

from app.images.fundo import normalizar, recortar_conteudo


def _canvas_com_bloco():
    """200x200 transparente com um bloco opaco 50x30 em (75, 85)."""
    img = Image.new("RGBA", (200, 200), (0, 0, 0, 0))
    bloco = Image.new("RGBA", (50, 30), (255, 0, 0, 255))
    img.paste(bloco, (75, 85))
    return img


def test_recorta_no_conteudo():
    r = recortar_conteudo(_canvas_com_bloco())
    assert r.size == (50, 30)


def test_recorte_de_transparente_puro_nao_muda():
    vazio = Image.new("RGBA", (100, 100), (0, 0, 0, 0))
    assert recortar_conteudo(vazio).size == (100, 100)


def test_normaliza_para_quadrado_centralizado():
    r = recortar_conteudo(_canvas_com_bloco())
    n = normalizar(r, lado=100, padding_frac=0.1)
    assert n.size == (100, 100)
    # conteúdo centralizado: a bbox do alfa fica ~simétrica no canvas
    bx = n.getchannel("A").getbbox()
    esq, topo, dir_, base = bx
    assert abs(esq - (100 - dir_)) <= 2      # margens horizontais ~iguais
    assert abs(topo - (100 - base)) <= 2     # margens verticais ~iguais
    # respeitou o padding (não encostou na borda)
    assert esq >= 8 and topo >= 8


def test_normaliza_respeita_aspecto():
    # bloco largo (50x30) -> ao normalizar, mantém a proporção (mais largo que alto)
    n = normalizar(recortar_conteudo(_canvas_com_bloco()), lado=200, padding_frac=0.05)
    esq, topo, dir_, base = n.getchannel("A").getbbox()
    assert (dir_ - esq) > (base - topo)

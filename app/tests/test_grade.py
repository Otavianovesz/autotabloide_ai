"""Testes da grade + mapa slot→produto (F5.5)."""

from decimal import Decimal

from PIL import Image

from app.rendering.compositor import DadosProduto, compor_pagina
from app.rendering.grade import detectar_caixas_preco, layout_grade_de_arte
from app.rendering.model import (
    LayoutDef,
    Pagina,
    PapelPreco,
    Regiao,
    Retangulo,
    Slot,
    TipoRegiao,
)

ARTE = "Frente Template.png"


def test_detecta_15_caixas():
    # o template tem 4+4+4+3 = 15 células (o canto inferior-esquerdo é o logo da loja)
    caixas = detectar_caixas_preco(ARTE)
    assert len(caixas) == 15
    ys = sorted({round(y / 50) for _, y, _, _ in caixas})
    assert len(ys) == 4   # 4 linhas


def test_layout_grade_tem_15_slots():
    layout, caixas = layout_grade_de_arte(ARTE)
    assert len(layout.paginas[0].slots) == 15
    # cada célula tem Imagem/Nome/Preço
    tipos = {r.tipo for r in layout.paginas[0].slots[0].regioes}
    assert tipos == {TipoRegiao.IMAGEM, TipoRegiao.NOME, TipoRegiao.PRECO}


def test_mapa_slot_para_produto_desenha_diferente():
    # 2 slots, 2 preços diferentes -> as duas metades da imagem diferem
    slot_a = Slot("a", [Regiao(TipoRegiao.PRECO, Retangulo(2, 2, 46, 26),
                               papel_preco=PapelPreco.POR, tamanho_max_pt=30)])
    slot_b = Slot("b", [Regiao(TipoRegiao.PRECO, Retangulo(52, 2, 46, 26),
                               papel_preco=PapelPreco.POR, tamanho_max_pt=30)])
    layout = LayoutDef(100, 30, dpi=100, paginas=[Pagina([slot_a, slot_b])])
    produtos = [DadosProduto("A", preco_por=Decimal("1.11")),
                DadosProduto("B", preco_por=Decimal("9.99"))]
    img = compor_pagina(layout, layout.paginas[0], produtos)
    esq = img.crop((0, 0, img.width // 2, img.height)).tobytes()
    dir_ = img.crop((img.width // 2, 0, img.width, img.height)).tobytes()
    assert esq != dir_   # produtos diferentes em células diferentes


def test_celula_sem_produto_fica_vazia():
    # lista menor que os slots: o 2º slot não recebe produto (fica só a arte)
    slot_a = Slot("a", [Regiao(TipoRegiao.PRECO, Retangulo(2, 2, 46, 26), tamanho_max_pt=30)])
    slot_b = Slot("b", [Regiao(TipoRegiao.PRECO, Retangulo(52, 2, 46, 26), tamanho_max_pt=30)])
    layout = LayoutDef(100, 30, dpi=100, paginas=[Pagina([slot_a, slot_b])])
    img = compor_pagina(layout, layout.paginas[0], [DadosProduto("A", preco_por=Decimal("1.11"))])
    branco = Image.new("RGB", (img.width // 2, img.height), "white").tobytes()
    assert img.crop((img.width // 2, 0, img.width, img.height)).tobytes() == branco

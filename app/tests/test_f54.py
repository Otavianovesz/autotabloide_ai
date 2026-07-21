"""Testes de interação da F5.4 (canvas): duplicar/excluir, alinhar, snap targets, zoom."""

from PySide6.QtWidgets import QApplication

from app.qt.canvas import CanvasView
from app.qt.editor import Editor
from app.rendering.compositor import DadosProduto
from app.rendering.model import LayoutDef, Pagina, Regiao, Retangulo, Slot, TipoRegiao


def _app():
    return QApplication.instance() or QApplication([])


def _layout2():
    slot = Slot("s", [
        Regiao(TipoRegiao.NOME, Retangulo(10, 10, 30, 10), nome="A"),
        Regiao(TipoRegiao.NOME, Retangulo(50, 30, 30, 10), nome="B"),
    ])
    return LayoutDef(100, 100, dpi=100, paginas=[Pagina([slot])])


def test_duplicar_regiao():
    _app()
    v = CanvasView()
    v.carregar(_layout2(), DadosProduto("x"))
    n0 = len(v.regioes())
    v.duplicar_regiao(v.regioes()[0])
    assert len(v.regioes()) == n0 + 1


def test_excluir_regiao():
    _app()
    v = CanvasView()
    v.carregar(_layout2(), DadosProduto("x"))
    reg = v.regioes()[0]
    v.excluir_regiao(reg)
    assert reg not in v.regioes()


def test_alinhar_esquerda_na_selecao():
    _app()
    v = CanvasView()
    v.carregar(_layout2(), DadosProduto("x"))
    for it in v._itens:
        it.setSelected(True)
    v.alinhar_selecionadas("esq")
    xs = [round(r.rect.x_mm) for r in v.regioes()]
    assert xs[0] == xs[1] == 10   # ambos foram para a esquerda da seleção


def test_alvos_snap_incluem_pagina():
    _app()
    v = CanvasView()
    v.carregar(_layout2(), DadosProduto("x"))
    ax, ay = v.alvos_snap(v._itens[0])
    assert 0.0 in ax and 0.0 in ay          # bordas da página entram como alvo


def test_zoom_altera_transform():
    _app()
    v = CanvasView()
    v.carregar(_layout2(), DadosProduto("x"))
    antes = v.transform().m11()
    v.zoom_mais()
    assert v.transform().m11() > antes


def test_editor_tem_barra():
    _app()
    e = Editor()
    e.carregar(_layout2(), DadosProduto("x"))
    assert e.barra is not None

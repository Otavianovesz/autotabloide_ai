"""Testes das ferramentas de região + painel de propriedades (F5.3) — offscreen."""

from PySide6.QtWidgets import QApplication

from app.qt.canvas import CanvasView
from app.qt.editor import Editor
from app.rendering.compositor import DadosProduto
from app.rendering.model import (
    Alinhamento,
    LayoutDef,
    Pagina,
    Regiao,
    Retangulo,
    Slot,
    TipoRegiao,
)


def _app():
    return QApplication.instance() or QApplication([])


def _layout():
    slot = Slot("s", [Regiao(TipoRegiao.PRECO, Retangulo(10, 10, 40, 20), nome="Preço")])
    return LayoutDef(100, 100, dpi=100, paginas=[Pagina([slot])])


def test_adicionar_regiao_cria_item():
    _app()
    v = CanvasView()
    v.carregar(_layout(), DadosProduto("x"))
    n0 = len(v.regioes())
    v.adicionar_regiao(TipoRegiao.NOME)
    assert len(v.regioes()) == n0 + 1
    assert len(v._itens) == n0 + 1


def test_selecao_emite_a_regiao():
    _app()
    v = CanvasView()
    v.carregar(_layout(), DadosProduto("x"))
    capturado = []
    v.selecao_mudou.connect(capturado.append)
    v._itens[0].setSelected(True)
    assert capturado and capturado[-1] is v.regioes()[0]


def test_painel_edita_alinhamento():
    _app()
    e = Editor()
    e.carregar(_layout(), DadosProduto("x"))
    reg = e.canvas.regioes()[0]
    e.canvas._itens[0].setSelected(True)                 # dispara mostrar(reg)
    e.propriedades.alinha.setCurrentText(Alinhamento.DIREITA.value)
    assert reg.alinhamento == Alinhamento.DIREITA


def test_painel_mostra_grupo_preco():
    _app()
    e = Editor()
    e.carregar(_layout(), DadosProduto("x"))
    e.canvas._itens[0].setSelected(True)
    assert not e.propriedades.grp_preco.isHidden()       # a região é PREÇO
    assert e.propriedades.grp_img.isHidden()


def test_mostrar_moeda_recompoe():
    _app()
    e = Editor()
    e.carregar(_layout(), DadosProduto("x", preco_por=__import__("decimal").Decimal("1.50")))
    reg = e.canvas.regioes()[0]
    e.canvas._itens[0].setSelected(True)
    e.propriedades.moeda.setChecked(False)
    assert reg.mostrar_moeda is False

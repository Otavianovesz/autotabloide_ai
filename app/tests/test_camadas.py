"""Testes das camadas interativas (F5.2) — offscreen. Editar muta o modelo + recompõe."""

from PySide6.QtWidgets import QApplication, QGraphicsItem

from app.qt.canvas import CanvasView
from app.qt.editor import Editor
from app.rendering.compositor import DadosProduto
from app.rendering.model import LayoutDef, Pagina, Regiao, Retangulo, Slot, TipoRegiao


def _app():
    return QApplication.instance() or QApplication([])


def _layout():
    slot = Slot("s", [
        Regiao(TipoRegiao.IMAGEM, Retangulo(10, 10, 80, 50), nome="Imagem"),
        Regiao(TipoRegiao.NOME, Retangulo(10, 65, 80, 15), nome="Nome"),
    ])
    return LayoutDef(100, 100, dpi=100, paginas=[Pagina([slot])])


def test_um_item_por_regiao():
    _app()
    v = CanvasView()
    v.carregar(_layout(), DadosProduto("x"))
    assert len(v._itens) == 2


def test_mover_e_soltar_muta_o_modelo():
    _app()
    v = CanvasView()
    v.carregar(_layout(), DadosProduto("Teste"))
    item = next(it for it in v._itens if it.regiao.tipo == TipoRegiao.NOME)
    antes = item.regiao.rect.x_mm
    item.setPos(*v.mm_para_cena(30, 65))  # move para x=30mm
    v._commit_regiao(item)
    assert item.regiao.rect.x_mm != antes and abs(item.regiao.rect.x_mm - 30) < 1


def test_ocultar_regiao():
    _app()
    v = CanvasView()
    v.carregar(_layout(), DadosProduto("y"))
    reg = v.regioes()[1]
    v.set_visivel(reg, False)
    assert any(it.regiao is reg and not it.isVisible() for it in v._itens)


def test_reordenar_z_order():
    _app()
    v = CanvasView()
    v.carregar(_layout(), DadosProduto("x"))
    primeiro = v.regioes()[0]
    v.mover_regiao(primeiro, 1)
    assert v.regioes()[1] is primeiro


def test_travar_impede_movimento():
    _app()
    v = CanvasView()
    v.carregar(_layout(), DadosProduto("x"))
    reg = v.regioes()[0]
    v.set_travado(reg, True)
    item = next(it for it in v._itens if it.regiao is reg)
    assert not (item.flags() & QGraphicsItem.GraphicsItemFlag.ItemIsMovable)


def test_editor_com_painel():
    _app()
    e = Editor()
    e.carregar(_layout(), DadosProduto("z"))
    assert len(e.canvas._itens) == 2
    assert e.painel.lista.count() == 2

"""Testes da F5.10 — histórico (desfazer/refazer) + copiar/colar no canvas."""

from PySide6.QtWidgets import QApplication

from app.qt.historico import Historico
from app.rendering.model import (
    LayoutDef,
    Pagina,
    Regiao,
    Retangulo,
    Slot,
    TipoRegiao,
)


def _layout(x: float = 10) -> LayoutDef:
    slot = Slot("s", [Regiao(TipoRegiao.NOME, Retangulo(x, 10, 30, 10), nome="Nome")])
    return LayoutDef(100, 100, dpi=100, paginas=[Pagina([slot])])


def _x(estado) -> float:
    """D5: desfazer/refazer devolvem (layout, mapa) — aqui só o layout importa."""
    layout = estado[0] if isinstance(estado, tuple) else estado
    return layout.paginas[0].slots[0].regioes[0].rect.x_mm


# --- Historico puro (sem Qt) ---------------------------------------------------

def test_desfazer_refazer_basico():
    h = Historico()
    for x in (10, 20, 30):
        h.registrar(_layout(x))
    assert h.pode_desfazer() and not h.pode_refazer()
    assert _x(h.desfazer()) == 20
    assert _x(h.desfazer()) == 10
    assert not h.pode_desfazer()          # chegou na base
    assert _x(h.refazer()) == 20
    assert _x(h.refazer()) == 30
    assert not h.pode_refazer()


def test_editar_apos_desfazer_corta_o_futuro():
    h = Historico()
    for x in (10, 20, 30):
        h.registrar(_layout(x))
    h.desfazer()                           # está no 20
    h.registrar(_layout(99))               # novo ramo
    assert not h.pode_refazer()            # o 30 morreu
    assert _x(h.desfazer()) == 20


def test_estado_identico_nao_duplica():
    h = Historico()
    lay = _layout(10)
    h.registrar(lay)
    h.registrar(lay)                       # o MESMO layout, nada mudou
    assert not h.pode_desfazer()
    # nota F5.5b: dois _layout(10) distintos têm uids distintos (I1) — e uids
    # diferentes SÃO estados diferentes; o dedup vale para o mesmo documento.


def test_limite_derruba_o_mais_antigo():
    h = Historico(limite=5)
    for x in range(10):
        h.registrar(_layout(x))
    voltas = 0
    while h.pode_desfazer():
        h.desfazer()
        voltas += 1
    assert voltas == 4                     # 5 estados guardados no máximo


# --- integração com o canvas ------------------------------------------------------

def _app():
    return QApplication.instance() or QApplication([])


def test_canvas_desfaz_mover_e_excluir():
    from app.qt.canvas import CanvasView
    from app.rendering.compositor import DadosProduto

    _app()
    v = CanvasView()
    v.carregar(_layout(10), DadosProduto("x"))
    reg = v.regioes()[0]

    # mover (o caminho do painel) → desfazer volta
    reg.rect.x_mm = 50
    v.notificar_edicao(reg, "rect")
    assert v.desfazer()
    assert v.regioes()[0].rect.x_mm == 10
    assert v.refazer()
    assert v.regioes()[0].rect.x_mm == 50

    # excluir → desfazer ressuscita a região
    v.excluir_regiao(v.regioes()[0])
    assert v.regioes() == []
    assert v.desfazer()
    assert len(v.regioes()) == 1


def test_canvas_copiar_colar_entre_slots():
    from app.qt.canvas import CanvasView
    from app.rendering.compositor import DadosProduto

    _app()
    lay = _layout(10)
    lay.paginas[0].slots.append(Slot("s2", []))
    v = CanvasView()
    v.carregar(lay, DadosProduto("x"))

    v._itens[0].setSelected(True)
    assert v.copiar_selecao()
    copia = v.colar()
    assert copia is not None
    total = sum(len(s.regioes) for s in lay.paginas[0].slots)
    assert total == 2
    assert copia.rect.x_mm == 14           # offset de 4mm

    # colar é desfazível (o canvas restaura um LayoutDef NOVO — olhar v._layout,
    # não a referência antiga; é por isso que Mesa/Editor releem canvas._layout)
    assert v.desfazer()
    assert sum(len(s.regioes) for s in v._layout.paginas[0].slots) == 1

"""Testes da F5.5 completa: propagação da célula-mestre + override por célula."""

from PySide6.QtWidgets import QApplication

from app.rendering.grade import propagar_mestre, slot_mestre
from app.rendering.model import (
    LayoutDef,
    Pagina,
    Regiao,
    Retangulo,
    Slot,
    TipoRegiao,
)


def _regiao_nome(x, y) -> Regiao:
    r = Regiao(TipoRegiao.NOME, Retangulo(x, y, 30, 10),
               nome="Nome", cor="#111111", tamanho_max_pt=16)
    r.de_mestre = True
    return r


def _grade() -> Pagina:
    """Grade sintética: mestra em (10,10) e duas células em (60,10) e (10,80)."""
    mestre = Slot("m", [_regiao_nome(12, 14)], mestre=True, origem_mm=(10, 10))
    c1 = Slot("c1", [_regiao_nome(62, 14)], origem_mm=(60, 10))
    c2 = Slot("c2", [_regiao_nome(12, 84)], origem_mm=(10, 80))
    return Pagina([mestre, c1, c2])


def test_propaga_estilo_para_todas():
    pag = _grade()
    pag.slots[0].regioes[0].cor = "#ff0000"
    propagar_mestre(pag)
    assert all(s.regioes[0].cor == "#ff0000" for s in pag.slots)


def test_override_tem_precedencia_e_sobrevive():
    pag = _grade()
    c1 = pag.slots[1].regioes[0]
    c1.cor = "#00ff00"
    c1.overrides.add("cor")          # a célula sobrescreveu a cor
    pag.slots[0].regioes[0].cor = "#ff0000"
    propagar_mestre(pag)
    assert c1.cor == "#00ff00"                        # override venceu
    assert pag.slots[2].regioes[0].cor == "#ff0000"   # as demais seguiram
    c1.overrides.discard("cor")                       # limpou o override…
    propagar_mestre(pag)
    assert c1.cor == "#ff0000"                        # …volta a seguir a mestra


def test_propaga_geometria_relativa_a_ancora():
    pag = _grade()
    m = pag.slots[0].regioes[0]
    m.rect.x_mm, m.rect.y_mm = 15, 20     # offset da âncora (10,10) = (+5, +10)
    propagar_mestre(pag)
    c1, c2 = pag.slots[1].regioes[0], pag.slots[2].regioes[0]
    assert (c1.rect.x_mm, c1.rect.y_mm) == (65, 20)   # âncora (60,10) + (5,10)
    assert (c2.rect.x_mm, c2.rect.y_mm) == (15, 90)   # âncora (10,80) + (5,10)


def test_override_de_geometria_persiste():
    pag = _grade()
    c1 = pag.slots[1].regioes[0]
    c1.rect.x_mm = 70
    c1.overrides.add("rect")
    pag.slots[0].regioes[0].rect.x_mm = 15
    propagar_mestre(pag)
    assert c1.rect.x_mm == 70                          # posição própria mantida
    assert pag.slots[2].regioes[0].rect.x_mm == 15     # a outra seguiu


def test_regiao_nova_na_mestra_aparece_nas_celulas():
    pag = _grade()
    selo = Regiao(TipoRegiao.SELO, Retangulo(11, 11, 8, 8), nome="Selo")
    selo.de_mestre = True
    pag.slots[0].regioes.append(selo)
    propagar_mestre(pag)
    assert all(any(r.tipo == TipoRegiao.SELO for r in s.regioes)
               for s in pag.slots)
    # geometria relativa: célula c1 (âncora 60,10) recebe o selo em (61,11)
    selo_c1 = next(r for r in pag.slots[1].regioes if r.tipo == TipoRegiao.SELO)
    assert (selo_c1.rect.x_mm, selo_c1.rect.y_mm) == (61, 11)


def test_regiao_removida_da_mestra_some_das_celulas():
    pag = _grade()
    propagar_mestre(pag)
    pag.slots[0].regioes.clear()          # mestra perdeu o Nome
    propagar_mestre(pag)
    assert all(not s.regioes for s in pag.slots)


def test_adicao_propria_da_celula_fica():
    pag = _grade()
    proprio = Regiao(TipoRegiao.SELO, Retangulo(62, 12, 8, 8), nome="Só aqui")
    pag.slots[1].regioes.append(proprio)  # de_mestre=False: adição da célula
    propagar_mestre(pag)
    assert proprio in pag.slots[1].regioes


def test_serializacao_roundtrip_preserva_grade():
    pag = _grade()
    pag.slots[1].regioes[0].overrides.add("cor")
    layout = LayoutDef(100, 100, dpi=100, paginas=[pag])
    clone = LayoutDef.from_dict(layout.to_dict())
    assert slot_mestre(clone.paginas[0]) is clone.paginas[0].slots[0]
    assert clone.paginas[0].slots[1].origem_mm == (60, 10)
    assert clone.paginas[0].slots[1].regioes[0].overrides == {"cor"}
    assert clone.paginas[0].slots[1].regioes[0].de_mestre is True


# --- integração com o canvas (editar no editor marca override / propaga) -------

def _app():
    return QApplication.instance() or QApplication([])


def test_canvas_editar_mestra_propaga_e_celula_vira_override():
    from app.qt.canvas import CanvasView
    from app.rendering.compositor import DadosProduto

    _app()
    pag = _grade()
    layout = LayoutDef(100, 100, dpi=100, paginas=[pag])
    v = CanvasView()
    v.carregar(layout, DadosProduto("x"))

    # editar a MESTRA pelo caminho do painel → propaga para as células
    mestra = pag.slots[0].regioes[0]
    mestra.cor = "#ff0000"
    v.notificar_edicao(mestra, "cor")
    assert pag.slots[1].regioes[0].cor == "#ff0000"

    # editar uma CÉLULA pelo painel → marca override e ganha precedência
    c1 = pag.slots[1].regioes[0]
    c1.cor = "#00ff00"
    v.notificar_edicao(c1, "cor")
    assert "cor" in c1.overrides
    mestra.cor = "#0000ff"
    v.notificar_edicao(mestra, "cor")
    assert c1.cor == "#00ff00"                        # override venceu
    assert pag.slots[2].regioes[0].cor == "#0000ff"   # a outra seguiu

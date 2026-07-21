"""Testes da F5.7 — estilos nomeados com override por instância (§6.5 da doc)."""

import pytest
from PySide6.QtWidgets import QApplication

from app.rendering.estilos import (
    EstiloTexto,
    aplicar_estilo,
    definir_estilo,
    desvincular,
    estilo_da_regiao,
    excluir_estilo,
    reaplicar_estilos,
    restaurar_do_estilo,
)
from app.rendering.model import (
    LayoutDef, Pagina, Regiao, Retangulo, Slot, TipoRegiao,
)


def _layout_com_3_nomes() -> LayoutDef:
    regs = [Regiao(TipoRegiao.NOME, Retangulo(10, 10 + 15 * i, 30, 10),
                   nome=f"N{i}") for i in range(3)]
    return LayoutDef(100, 100, dpi=100, paginas=[Pagina([Slot("s", regs)])])


def _estilo(nome="Estilo Nome", fonte="Quicksand-Bold.ttf",
            pt=22.0, cor="#112233") -> EstiloTexto:
    return EstiloTexto(nome=nome, fonte=fonte, tamanho_max_pt=pt, cor=cor)


def test_definir_estilo_muda_o_conjunto():
    lay = _layout_com_3_nomes()
    est = _estilo()
    for r in lay.paginas[0].slots[0].regioes:
        aplicar_estilo(r, est, respeitar_overrides=False)
    definir_estilo(lay, est)
    assert "Estilo Nome" in lay.estilos
    # trocar a COR do estilo muda em todos que o usam
    est.cor = "#FF0000"
    n = definir_estilo(lay, est)
    assert n == 3
    assert all(r.cor == "#FF0000" for r in lay.paginas[0].slots[0].regioes)


def test_override_por_instancia_prevalece():
    lay = _layout_com_3_nomes()
    est = _estilo()
    regs = lay.paginas[0].slots[0].regioes
    for r in regs:
        aplicar_estilo(r, est, respeitar_overrides=False)
    definir_estilo(lay, est)

    # a instância N1 ganha um ajuste próprio de cor
    regs[1].cor = "#00FF00"
    regs[1].overrides_estilo.add("cor")

    est.cor = "#0000FF"
    est.tamanho_max_pt = 30
    definir_estilo(lay, est)
    assert regs[0].cor == "#0000FF" and regs[2].cor == "#0000FF"
    assert regs[1].cor == "#00FF00"              # o override venceu…
    assert regs[1].tamanho_max_pt == 30          # …só no atributo ajustado

    # restaurar do estilo: volta a seguir por inteiro
    assert restaurar_do_estilo(lay, regs[1])
    assert regs[1].cor == "#0000FF" and not regs[1].overrides_estilo


def test_excluir_estilo_mantem_a_aparencia():
    lay = _layout_com_3_nomes()
    est = _estilo(cor="#445566")
    reg = lay.paginas[0].slots[0].regioes[0]
    aplicar_estilo(reg, est, respeitar_overrides=False)
    definir_estilo(lay, est)
    n = excluir_estilo(lay, "Estilo Nome")
    assert n == 1 and "Estilo Nome" not in lay.estilos
    assert reg.estilo is None and reg.cor == "#445566"   # nada muda na tela


def test_desvincular_e_capturar_da_regiao():
    lay = _layout_com_3_nomes()
    reg = lay.paginas[0].slots[0].regioes[0]
    reg.fonte, reg.tamanho_max_pt, reg.cor = "Quicksand-Bold.ttf", 18.0, "#999999"
    est = estilo_da_regiao(reg, "Capturado")
    assert (est.fonte, est.tamanho_max_pt, est.cor) == \
           ("Quicksand-Bold.ttf", 18.0, "#999999")
    aplicar_estilo(reg, est, respeitar_overrides=False)
    desvincular(reg)
    assert reg.estilo is None and reg.cor == "#999999"


def test_serializacao_roundtrip_com_estilos():
    lay = _layout_com_3_nomes()
    est = _estilo()
    reg = lay.paginas[0].slots[0].regioes[0]
    aplicar_estilo(reg, est, respeitar_overrides=False)
    reg.overrides_estilo.add("cor")
    definir_estilo(lay, est)

    clone = LayoutDef.from_dict(lay.to_dict())
    r2 = clone.paginas[0].slots[0].regioes[0]
    assert clone.estilos["Estilo Nome"]["fonte"] == "Quicksand-Bold.ttf"
    assert r2.estilo == "Estilo Nome" and r2.overrides_estilo == {"cor"}
    assert reaplicar_estilos(clone) == 1         # o vínculo sobreviveu


def test_estilo_propaga_da_mestra_para_as_celulas():
    from app.rendering.grade import propagar_mestre

    regs = [Regiao(TipoRegiao.NOME, Retangulo(12, 12, 30, 10), nome="Nome")]
    for r in regs:
        r.de_mestre = True
    lay = LayoutDef(100, 100, dpi=100, paginas=[Pagina([
        Slot("m", regs, mestre=True, origem_mm=(10, 10)),
        Slot("c1", origem_mm=(60, 10), ref_grupo="m"),
    ])])
    est = _estilo()
    lay.estilos[est.nome] = est.to_dict()
    aplicar_estilo(regs[0], est, respeitar_overrides=False)
    propagar_mestre(lay.paginas[0])
    derivada = lay.paginas[0].slots[1].regioes[0]
    assert derivada.estilo == "Estilo Nome"      # o vínculo propagou
    assert derivada.cor == est.cor


def test_painel_combo_e_novo_estilo():
    """Fumaça da UI: combo popula, escolher aplica, novo estilo entra no layout."""
    QApplication.instance() or QApplication([])
    from app.qt.canvas import CanvasView
    from app.qt.painel_propriedades import PainelPropriedades
    from app.rendering.compositor import DadosProduto

    lay = _layout_com_3_nomes()
    est = _estilo("Estilo Teste")
    lay.estilos[est.nome] = est.to_dict()
    v = CanvasView()
    v.carregar(lay, DadosProduto("x"))
    painel = PainelPropriedades(v)
    v._itens[0].setSelected(True)
    painel.mostrar(v.regioes()[0])
    nomes = [painel.estilo.itemText(i) for i in range(painel.estilo.count())]
    assert nomes == ["(nenhum)", "Estilo Teste"]

    painel.estilo.setCurrentIndex(1)             # escolhe o estilo
    painel._estilo_escolhido(1)
    reg = v.regioes()[0]
    assert reg.estilo == "Estilo Teste" and reg.cor == est.cor

    # editar a cor pelo painel marca override da instância
    painel.mostrar(reg)
    painel._set("cor", "#ABCDEF")
    assert "cor" in reg.overrides_estilo
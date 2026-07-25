"""Fumaça de JANELA REAL (A2) — o que o offscreen não enxerga.

Cada teste confere CONTEÚDO (L3), nunca "não deu exceção". A suíte é
curta: seu papel é provar que o programa de verdade — janela composta,
vida instalada, clique de mouse — se comporta como a bancada offscreen
afirma. Roda antes de cada selo: ``pytest app/tests_janela -q``.
"""

from PySide6.QtGui import QGuiApplication
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QDialog, QWidget

from app.rendering.compositor import DadosProduto
from app.rendering.model import (
    LayoutDef,
    Pagina,
    Regiao,
    Retangulo,
    Slot,
    TipoRegiao,
)
from app.tests import acervo
from app.tests.gestos import botao_por_tooltip, clicar, drenar


def _app():
    return QApplication.instance() or QApplication([])


def test_plataforma_nao_e_offscreen():
    _app()
    assert QGuiApplication.platformName() != "offscreen", (
        "a suíte de janela real está rodando offscreen — o T-01 voltou")


def test_vida_esta_instalada_de_verdade():
    """T-02: a bancada tinha 0 instalações de instalar_vida/polimento.
    Nesta suíte os dois filtros estão VIVOS no QApplication."""
    _app()
    from app.qt.design import animacoes, polimento
    assert animacoes._animador is not None, "instalar_vida não instalou"
    assert animacoes._hover_global is not None
    assert polimento._polidor is not None, "instalar_polimento não instalou"


def test_editor_em_janela_real_clique_cria_regiao(tmp_path, monkeypatch):
    """O gesto nº 1 do editor, com compositing de verdade: clicar o botão
    real da barra cria a região IMAGEM e ela nasce selecionada."""
    from app.core.paths import SystemRoot
    from app.qt.editor import Editor
    monkeypatch.setenv("AUTOTABLOIDE_ROOT", str(tmp_path / "raiz"))
    root = SystemRoot(tmp_path / "raiz").criar_estrutura()
    acervo.copiar_fontes_reais(root.fontes)
    _app()

    lay = LayoutDef(100, 100, dpi=100, paginas=[Pagina([
        Slot("s", [Regiao(TipoRegiao.NOME, Retangulo(10, 10, 40, 10),
                          nome="Nome")]),
    ])])
    e = Editor()
    e.carregar(lay, DadosProduto("x"))
    e.resize(1000, 700)
    e.show()
    QTest.qWaitForWindowExposed(e)

    antes = len(e.canvas.regioes())
    clicar(botao_por_tooltip(e.barra, "Adicionar imagem"))
    regioes = e.canvas.regioes()
    assert len(regioes) == antes + 1
    novas = [r for r in regioes if r.tipo == TipoRegiao.IMAGEM]
    assert len(novas) == 1
    assert e.canvas.selecionada() is novas[0]
    e.close()


def test_veu_do_dialogo_nasce_e_some_no_ciclo_normal():
    """A3 em ação na janela real: com a vida instalada, abrir um diálogo
    sobre uma janela visível CRIA o véu ('veuDialogo'); esconder o
    diálogo o REMOVE. Este é o ciclo NORMAL — o ciclo anormal (morrer sem
    Hide, o véu eterno L-01) é o conserto B2 e ganha o teste vermelho lá."""
    from app.qt.design import animacoes as anim
    _app()
    anim._cache_config["valor"] = True     # determinístico, sem tocar o banco
    anim._cache_config["transp"] = False
    try:
        pai = QWidget()
        pai.resize(500, 400)
        pai.show()
        QTest.qWaitForWindowExposed(pai)

        dlg = QDialog(pai)
        dlg.resize(160, 120)
        dlg.show()
        drenar()
        assert id(dlg) in anim._veus, "o véu do diálogo não nasceu"
        veu = anim._veus[id(dlg)]
        assert veu.objectName() == "veuDialogo"
        assert veu.isVisible()

        dlg.hide()
        drenar()
        assert id(dlg) not in anim._veus, "o Hide não removeu o véu (ciclo normal)"
        pai.close()
    finally:
        anim._cache_config.clear()

"""FASE 2, Bloco F (passos 77-78) — busca global: acha tudo, de qualquer tela."""

import pytest
from PySide6.QtWidgets import QApplication

from app.qt.telas.servico import ItemMesa
from app.rendering.model import LayoutDef, Pagina, Regiao, Retangulo, Slot, TipoRegiao


@pytest.fixture()
def raiz_tmp(tmp_path, monkeypatch):
    monkeypatch.setenv("AUTOTABLOIDE_ROOT", str(tmp_path / "raiz"))
    from app.core.database import Database
    from app.core.paths import SystemRoot

    root = SystemRoot(tmp_path / "raiz").criar_estrutura()
    Database(root).init().engine.dispose()
    return root


def test_busca_acha_os_3_grupos_com_acento_trocado(raiz_tmp):
    """Passo 77: 'acucar' acha 'Açúcar'; projeto/produto/layout por
    fragmento; <2 letras devolve vazio."""
    from app.core import projetos
    from app.core.database import Database
    from app.core.models import Produto
    from app.qt.telas.busca import buscar_global
    from app.rendering.persistencia import salvar_layout

    lay = LayoutDef(100, 100, dpi=100, paginas=[Pagina([
        Slot("s", [Regiao(TipoRegiao.NOME, Retangulo(10, 10, 30, 10))])])])
    item = ItemMesa(descricao="X", preco="1,00", semaforo="VERDE", nome="P")
    projetos.salvar_projeto("Ofertas de Açúcar", "Quintou", "TABLOIDE",
                            lay, [item.to_dict()])
    db = Database().init()
    try:
        with db.Session() as s:
            s.add(Produto(nome_bruto="ACUCAR CRISTAL",
                          nome_sanitizado="Açúcar Cristal Doce Dia 2kg"))
            salvar_layout(s, "Cartaz Açougue 10×15", lay)
            s.commit()
    finally:
        db.engine.dispose()

    r = buscar_global("acucar")          # sem acento acha COM acento
    assert any("Açúcar" in p["nome"] for p in r["projetos"])
    assert any("Açúcar" in p["nome"] for p in r["produtos"])
    r2 = buscar_global("AÇOUGUE")        # com acento e caixa trocada
    assert any("Açougue" in v["nome"] for v in r2["layouts"])
    assert buscar_global("a") == {"projetos": [], "produtos": [],
                                  "layouts": []}


def test_ctrl_k_abre_em_duas_telas(raiz_tmp):
    """Passo 78, REESCRITO na F13/C13 (CF-02): o teste antigo chamava
    ``_paleta_busca.abrir()`` DIRETO e ficou verde por cima de um atalho
    MORTO — com a Mesa visível havia DOIS QShortcut Ctrl+K de janela
    (o do shell e um cru da Mesa), o Qt declarava ambiguidade e nenhum
    disparava. Agora a TECLA é apertada de verdade (L2)."""
    QApplication.instance() or QApplication([])
    from PySide6.QtCore import Qt

    from app.editor_app import montar_janela
    from app.tests.gestos import ativar_janela, drenar, teclar
    shell, editor = montar_janela()
    editor.close()
    shell.setAttribute(Qt.WidgetAttribute.WA_DontShowOnScreen, True)
    shell.resize(1200, 800)
    shell.show()
    ativar_janela(shell)             # atalho de janela exige janela ATIVA
    assert hasattr(shell, "_paleta_busca")
    for tela in ("mesa", "configuracoes"):
        shell.ir_para(tela)
        drenar()                     # o showEvent da Mesa arma os atalhos dela
        teclar(shell, Qt.Key.Key_K, mods=Qt.KeyboardModifier.ControlModifier)
        assert shell._paleta_busca.isVisible(), (
            f"Ctrl+K MORTO na tela '{tela}' — dois donos da mesma tecla "
            "(CF-02/C13)")
        shell._paleta_busca.hide()
    shell.close()

"""Diálogos de confirmação pelo CLIQUE REAL (ORDEM_F13 · Bloco A · A4).

T-03: ``confirmar_pre_voo`` — o portão do I2 ("nunca em silêncio") — era
monkeypatchado em TODO teste que o alcançava; o ``QMessageBox`` real
nunca rodou na bancada. Aqui os dois diálogos de confirmação rodam DE
VERDADE: ``exec()`` de verdade, resposta pelo GESTO (o vigia clica o
botão real dentro do laço de eventos do próprio diálogo), zero
monkeypatch.

O que este arquivo NÃO faz (de propósito): consertar ou afirmar o botão
padrão do Enter (CF-01) — o diálogo destrutivo hoje abre sem
``setDefaultButton``/``setEscapeButton`` e isso é o conserto B3, que
nasce com o próprio teste vermelho no Bloco B.
"""

from PySide6.QtWidgets import QApplication

from app.tests.gestos import vigia_dialogo


def _app():
    return QApplication.instance() or QApplication([])


# ---------------------------------------------------------------------------
# confirmar_destrutivo — app/qt/design/componentes.py
# ---------------------------------------------------------------------------


def test_destrutivo_clicar_o_verbo_confirma():
    from app.qt.design.componentes import confirmar_destrutivo
    _app()
    with vigia_dialogo("Excluir 2 produtos") as v:
        resultado = confirmar_destrutivo(
            None, "Excluir produtos",
            "Isto não tem volta. Excluir mesmo?", "Excluir 2 produtos")
    assert v.disparou, "o QMessageBox real nunca abriu"
    assert resultado is True
    assert "Cancelar" in v.textos_botoes       # o caminho seguro existe


def test_destrutivo_clicar_cancelar_nao_confirma():
    from app.qt.design.componentes import confirmar_destrutivo
    _app()
    with vigia_dialogo("Cancelar") as v:
        resultado = confirmar_destrutivo(
            None, "Excluir produtos",
            "Isto não tem volta. Excluir mesmo?", "Excluir 2 produtos")
    assert v.disparou
    assert resultado is False


# ---------------------------------------------------------------------------
# confirmar_pre_voo — app/qt/telas/prevoo.py (o portão do I2)
# ---------------------------------------------------------------------------


def test_pre_voo_com_avisos_clicar_seguir_segue():
    from app.qt.telas.prevoo import confirmar_pre_voo
    _app()
    avisos = ["“Arroz”: sem imagem", "“Feijão”: preço não entendido"]
    with vigia_dialogo("Exportar mesmo assim") as v:
        resultado = confirmar_pre_voo(None, avisos, "Exportar")
    assert v.disparou, "o QMessageBox real do pré-voo nunca abriu"
    assert resultado is True
    assert v.titulo and "2" in v.titulo        # o nº de pendências no título


def test_pre_voo_com_avisos_clicar_cancelar_barra():
    from app.qt.telas.prevoo import confirmar_pre_voo
    _app()
    with vigia_dialogo("Cancelar") as v:
        resultado = confirmar_pre_voo(None, ["“Arroz”: sem imagem"], "Salvar")
    assert v.disparou
    assert resultado is False
    # o botão de seguir carrega o VERBO da ação (nunca um "OK" genérico)
    assert any(b.startswith("Salvar mesmo assim") for b in v.textos_botoes)


def test_pre_voo_sem_avisos_nem_abre_dialogo():
    from app.qt.telas.prevoo import confirmar_pre_voo
    _app()
    with vigia_dialogo("Cancelar", timeout_ms=300) as v:
        resultado = confirmar_pre_voo(None, [], "Exportar")
    assert resultado is True
    assert not v.disparou                      # sem pendência, sem pergunta

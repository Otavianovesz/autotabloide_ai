"""Configuração comum dos testes.

Roda o Qt em modo "offscreen" para os testes não precisarem de tela/monitor.
"""

import os

# Precisa ser definido ANTES de qualquer import do Qt.
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest  # noqa: E402


def pytest_addoption(parser):
    """F13 · Bloco A · A6: ``--ordem-invertida`` roda os testes coletados
    em ordem INVERSA — a sonda que caça estado vivo vazando entre testes
    (foi ela que provou o vazamento do véu em ``animacoes.py``)."""
    parser.addoption(
        "--ordem-invertida", action="store_true", default=False,
        help="roda os testes em ordem inversa (caça estado vivo entre testes)")


def pytest_collection_modifyitems(config, items):
    if config.getoption("--ordem-invertida"):
        items.reverse()


def pytest_configure(config):
    config.addinivalue_line(
        "markers",
        "lm_real: o teste roda o código REAL de disponibilidade da IA "
        "(sem o bloqueio de bancada do LM Studio)")


@pytest.fixture(autouse=True)
def _lm_studio_fora_da_bancada(monkeypatch, request):
    """LEI DA BANCADA (F13/F): o LM Studio REAL da máquina do dono NÃO
    participa da suíte. Duas baselines do F penduraram porque o app
    estava aberto no desktop: o probe de 3s por chamada (e respostas
    REAIS quando ele responde) torna o placar dependente de um programa
    alheio — o mesmo mal do offscreen antes do conftest. Teste que
    precise do código real de disponibilidade marca @pytest.mark.lm_real
    (ele continua sem rede: o interruptor ia.usar decide antes)."""
    if request.node.get_closest_marker("lm_real"):
        yield
        return
    from app.ai import client
    monkeypatch.setattr(client.ClienteOpenAICompat, "disponivel",
                        lambda self: False)
    yield


def pytest_terminal_summary(terminalreporter, exitstatus, config):
    """F13 · Bloco A · A5: skip por acervo do dono ausente é CONTADO e
    ESTAMPADO no fim do relatório — skip silencioso não é verde."""
    do_dono = [r for r in terminalreporter.stats.get("skipped", [])
               if "REQUER ACERVO DO DONO" in str(getattr(r, "longrepr", ""))]
    if do_dono:
        terminalreporter.write_sep(
            "!", "ACERVO DO DONO AUSENTE", red=True, bold=True)
        terminalreporter.write_line(
            f"{len(do_dono)} teste(s) pulados por falta do acervo do dono "
            "(arte real / fontes reais).")
        terminalreporter.write_line(
            "Este placar NÃO cobre a prova da arte real — "
            "não trate como verde completo.")


@pytest.fixture()
def vida():
    """F13: instala a vida visual (véu/hover) SÓ para o teste que a pedir
    e desinstala no fim — o resto da bancada offscreen segue determinística,
    como o docstring de instalar_vida promete."""
    from PySide6.QtWidgets import QApplication

    from app.qt.design import animacoes as anim
    app = QApplication.instance() or QApplication([])
    anim._cache_config["valor"] = True     # animações ligadas sem tocar o banco
    anim._cache_config["transp"] = False   # véu permitido
    anim.instalar_vida(app)
    yield anim
    if anim._animador is not None:
        app.removeEventFilter(anim._animador)
        anim._animador = None
    if anim._hover_global is not None:
        app.removeEventFilter(anim._hover_global)
        anim._hover_global = None
    anim._cache_config.clear()
    for registro in (anim._veus, anim._hovers, anim._veus_troca):
        for w in list(registro.values()):
            try:
                w.hide()
                w.deleteLater()
            except Exception:
                pass
        registro.clear()


@pytest.fixture(autouse=True)
def _encerrar_qt_apos_teste():
    """Rede de segurança do teardown (lei "verde com crash no exit NÃO é
    verde"; precedente F7.1: QThread viva no fechamento derruba o processo).

    Muitos testes criam ``MesaTela()`` (com ``GerenciadorTrabalhos`` e o timer
    do rascunho) sem encerrar. Após CADA teste: encerra TODOS os workers vivos
    (QThread), fecha as janelas — o ``closeEvent`` da Mesa para o timer e
    encerra os trabalhos dela — e drena os eventos do Qt. Sem isso, um worker/
    timer vivo no teardown causa segfault intermitente."""
    yield
    try:
        from PySide6.QtCore import QCoreApplication, QEvent
        from PySide6.QtWidgets import QApplication
        from app.qt.workers import encerrar_todos
        encerrar_todos(espera_ms=1000)
        app = QApplication.instance()
        if app is not None:
            # FASE 12 (2ª rodada do segfault): ENTREGAR os deleteLater
            # pendentes era a estratégia ERRADA — quando o alvo já foi
            # destruído entre o agendamento e a entrega, a entrega É o
            # access violation. DESCARTÁ-los é seguro: vazamento mínimo
            # dentro do processo de teste; crash, nunca.
            _drop = QEvent.Type.DeferredDelete
            QCoreApplication.removePostedEvents(None, _drop)
            app.closeAllWindows()
            app.processEvents()
            QCoreApplication.removePostedEvents(None, _drop)
            app.processEvents()
    except Exception:
        pass

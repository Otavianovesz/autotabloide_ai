"""Configuração comum dos testes.

Roda o Qt em modo "offscreen" para os testes não precisarem de tela/monitor.
"""

import os

# Precisa ser definido ANTES de qualquer import do Qt.
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest  # noqa: E402


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
        from PySide6.QtCore import QEvent
        from PySide6.QtWidgets import QApplication
        from app.qt.workers import encerrar_todos
        encerrar_todos(espera_ms=1000)
        app = QApplication.instance()
        if app is not None:
            app.closeAllWindows()
            # FASE 12: além do drain simples, ENTREGAR os deleteLater
            # pendentes AGORA — um widget agendado para morrer num teste
            # e destruído no teardown de OUTRO era o segfault intermitente
            # (access violation no _encerrar_qt_apos_teste)
            app.sendPostedEvents(None, QEvent.Type.DeferredDelete)
            app.processEvents()
            app.processEvents()
    except Exception:
        pass

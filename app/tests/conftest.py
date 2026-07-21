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

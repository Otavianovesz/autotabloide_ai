"""Suíte com JANELA REAL (ORDEM_F13 · Bloco A · A2/A3) — SEM offscreen.

T-01: a bancada principal roda ``QT_QPA_PLATFORM=offscreen`` fixo —
hit-test, compositing, foco de janela real e popup ficam fora POR
CONSTRUÇÃO. Esta suíte é pequena de propósito e roda com janela de
verdade, ANTES DE CADA SELO::

    pytest app/tests_janela -q

T-02/A3: ``instalar_vida`` + ``instalar_polimento`` são AUTOUSE aqui —
a suíte visual prova o app COM o circo ligado, porque é assim que o
dono o roda (a bancada offscreen os desliga de propósito e por isso
nunca viu o véu).
"""

import os

# Janela REAL: desfaz um offscreen herdado do ambiente ANTES do Qt subir.
os.environ.pop("QT_QPA_PLATFORM", None)

import pytest  # noqa: E402


@pytest.fixture(autouse=True)
def _vida_e_polimento():
    """A3: a vida visual instalada em TODO teste desta suíte."""
    from PySide6.QtWidgets import QApplication

    from app.qt.design.animacoes import instalar_vida
    from app.qt.design.polimento import instalar_polimento
    app = QApplication.instance() or QApplication([])
    instalar_vida(app)
    instalar_polimento(app)
    yield


@pytest.fixture(autouse=True)
def _encerrar_qt_apos_teste():
    """A MESMA rede de segurança do conftest offscreen (lei da F12:
    DeferredDelete pendente se DESCARTA, nunca se entrega — entregar a
    alvo morto ERA o segfault intermitente)."""
    yield
    try:
        from PySide6.QtCore import QCoreApplication, QEvent
        from PySide6.QtWidgets import QApplication

        from app.qt.workers import encerrar_todos
        encerrar_todos(espera_ms=1000)
        app = QApplication.instance()
        if app is not None:
            _drop = QEvent.Type.DeferredDelete
            QCoreApplication.removePostedEvents(None, _drop)
            app.closeAllWindows()
            app.processEvents()
            QCoreApplication.removePostedEvents(None, _drop)
            app.processEvents()
    except Exception:
        pass

"""Fixture de gesto da bancada (ORDEM_F13_RESGATE · Bloco A · A1).

Lei L2 desta fase: teste de UI prova o GESTO — o clique, a tecla, o
arraste viajando pelo pipeline REAL de eventos do Qt — nunca o método
que mora por baixo do botão. Chamar ``canvas.duplicar_regiao(r)`` não
prova que o menu funciona (T-05); ``keyPressEvent`` direto já mascarou
um bug real de foco (test_isolamento.py, F11.5). Estes helpers são a
porta única: ``QTest``/``QApplication.sendEvent`` por baixo, os nomes
da casa por cima. Todo teste novo da ordem F13 usa isto.
"""

from __future__ import annotations

from contextlib import contextmanager

from PySide6.QtCore import QEvent, QPointF, Qt, QTimer
from PySide6.QtGui import QMouseEvent
from PySide6.QtTest import QTest
from PySide6.QtWidgets import (
    QAbstractButton,
    QApplication,
    QDialog,
    QMessageBox,
    QPushButton,
    QWidget,
)

# ---------------------------------------------------------------------------
# gestos básicos
# ---------------------------------------------------------------------------


def clicar(alvo: QWidget, *, botao=Qt.MouseButton.LeftButton,
           mods=Qt.KeyboardModifier.NoModifier, pos=None) -> None:
    """Clique REAL (press+release pelo pipeline do Qt) num widget.

    ``pos`` em coordenadas locais do widget; padrão = centro. Recusa
    clicar o que o dono não conseguiria clicar (desabilitado não é
    gesto, é trapaça)."""
    assert alvo.isEnabled(), f"gesto impossível: {alvo!r} está desabilitado"
    if pos is None:
        pos = alvo.rect().center()
    QTest.mouseClick(alvo, botao, mods, pos)


def teclar(w: QWidget, tecla, *, mods=Qt.KeyboardModifier.NoModifier) -> None:
    """Tecla REAL no widget (KeyPress+KeyRelease pelo pipeline do Qt)."""
    QTest.keyClick(w, tecla, mods)


def ativar_janela(w: QWidget) -> None:
    """Atalho de JANELA (WindowShortcut) só dispara com a janela ATIVA — e
    offscreen nenhuma janela se ativa sozinha (foi assim que o Ctrl+K
    morto ficou invisível à bancada, CF-02/CF-06). Chamar antes de
    ``teclar`` num teste de atalho."""
    from PySide6.QtWidgets import QApplication
    import warnings
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", DeprecationWarning)
        QApplication.setActiveWindow(w)


def acionar(acao) -> None:
    """Aciona uma ``QAction`` (``trigger()``) ou um botão (``click()``)
    de verdade — o caminho que o menu/a barra percorrem. Recusa acionar
    o que está desabilitado."""
    assert acao.isEnabled(), f"gesto impossível: {acao!r} está desabilitado"
    if isinstance(acao, QAbstractButton):
        acao.click()
    else:
        acao.trigger()


def arrastar(w: QWidget, de, para, *, botao=Qt.MouseButton.LeftButton,
             passos: int = 8) -> None:
    """Arraste REAL: press em ``de``, movimentos intermediários, release
    em ``para`` — tudo por ``QMouseEvent`` via ``QApplication.sendEvent``
    (``QTest.mouseMove`` mexe no cursor da máquina; sendEvent não).

    ``de``/``para`` em coordenadas LOCAIS do widget."""
    de, para = QPointF(de), QPointF(para)
    sem_mod = Qt.KeyboardModifier.NoModifier

    def _ev(tipo, local, botao_ev, botoes):
        global_ = QPointF(w.mapToGlobal(local.toPoint()))
        return QMouseEvent(tipo, local, global_, botao_ev, botoes, sem_mod)

    QApplication.sendEvent(
        w, _ev(QEvent.Type.MouseButtonPress, de, botao, botao))
    for i in range(1, passos + 1):
        p = de + (para - de) * (i / passos)
        QApplication.sendEvent(
            w, _ev(QEvent.Type.MouseMove, p, Qt.MouseButton.NoButton, botao))
    QApplication.sendEvent(
        w, _ev(QEvent.Type.MouseButtonRelease, para, botao,
               Qt.MouseButton.NoButton))
    QApplication.processEvents()


# ---------------------------------------------------------------------------
# gestos sobre um QGraphicsView (o canvas): pontos dados EM CENA
# ---------------------------------------------------------------------------


def clicar_na_cena(view, ponto_cena, **kw) -> None:
    """Clique no viewport do view, no ponto dado em coordenadas de cena."""
    local = view.mapFromScene(QPointF(ponto_cena))
    clicar(view.viewport(), pos=local, **kw)


def arrastar_na_cena(view, de_cena, para_cena, **kw) -> None:
    """Arraste no viewport do view, pontos dados em coordenadas de cena."""
    de = view.mapFromScene(QPointF(de_cena))
    para = view.mapFromScene(QPointF(para_cena))
    arrastar(view.viewport(), QPointF(de), QPointF(para), **kw)


# ---------------------------------------------------------------------------
# achar o controle real (a barra do editor não dá objectName aos botões)
# ---------------------------------------------------------------------------


def botao_por_texto(pai: QWidget, texto: str) -> QAbstractButton:
    """O botão cujo texto (sem espaços das bordas) é ``texto``.
    Falha NOMINAL se achar 0 ou mais de 1 — ambiguidade não se resolve
    em silêncio."""
    achados = [b for b in pai.findChildren(QAbstractButton)
               if b.text().strip() == texto]
    assert len(achados) == 1, (
        f"esperava exatamente 1 botão com texto '{texto}', "
        f"achei {len(achados)}: {[b.text() for b in achados]}")
    return achados[0]


def botao_por_tooltip(pai: QWidget, tooltip: str) -> QAbstractButton:
    """O botão cujo tooltip (parte antes do sufixo ' · atalho') é
    ``tooltip`` — é como a barra do editor identifica seus botões."""
    achados = [b for b in pai.findChildren(QAbstractButton)
               if b.toolTip().split("  ·  ")[0].strip() == tooltip]
    assert len(achados) == 1, (
        f"esperava exatamente 1 botão com tooltip '{tooltip}', "
        f"achei {len(achados)}: {[b.toolTip() for b in achados]}")
    return achados[0]


# ---------------------------------------------------------------------------
# diálogos modais: responder pelo GESTO, nunca por monkeypatch (A4/T-03)
# ---------------------------------------------------------------------------


class _Vigia:
    """O que o vigia viu do diálogo (para asserção depois do ``with``)."""

    def __init__(self) -> None:
        self.disparou = False
        self.disparos = 0
        self.titulo: str | None = None
        self.textos_botoes: list[str] = []
        self.botao_com_foco: str | None = None
        self.botao_padrao: str | None = None
        # o botão pedido NÃO existia no diálogo (o vigia fechou com reject
        # para o teste não pendurar — a asserção fica para depois do with)
        self.faltou_botao: str | None = None


def _dialogo_modal_visivel() -> QDialog | None:
    ativo = QApplication.activeModalWidget()
    if isinstance(ativo, QDialog) and ativo.isVisible():
        return ativo
    for w in QApplication.topLevelWidgets():     # reserva (offscreen)
        if isinstance(w, QDialog) and w.isVisible() and w.isModal():
            return w
    return None


@contextmanager
def vigia_dialogo(texto_botao: str | None = None, *, tecla=None,
                  intervalo_ms: int = 15, timeout_ms: int = 4000,
                  vezes: int = 1):
    """Arma um vigia que responde o PRÓXIMO diálogo modal pelo GESTO:
    clique REAL no botão com esse texto — ou uma tecla no diálogo, se
    ``tecla`` for dada. O vigia roda DENTRO do laço de eventos do
    próprio ``exec()``; nada é monkeypatchado. Com ``vezes=N`` ele se
    rearma e responde N diálogos SEGUIDOS da mesma forma (fluxos que
    abrem mais de um, como o editar nome+preço da estante).

        with vigia_dialogo("Cancelar") as v:
            ...ação que abre o QMessageBox...
        assert v.disparou
    """
    visto = _Vigia()
    timer = QTimer()
    timer.setInterval(intervalo_ms)
    restante = {"ms": timeout_ms}
    respondidos: set[int] = set()

    def _tenta() -> None:
        restante["ms"] -= intervalo_ms
        if restante["ms"] <= 0:
            timer.stop()
            return
        caixa = _dialogo_modal_visivel()
        if caixa is None or id(caixa) in respondidos:
            return
        respondidos.add(id(caixa))
        visto.disparos += 1
        if visto.disparos >= vezes:
            timer.stop()
        visto.disparou = True
        visto.titulo = caixa.windowTitle()
        botoes = (list(caixa.buttons()) if isinstance(caixa, QMessageBox)
                  else caixa.findChildren(QAbstractButton))
        visto.textos_botoes = [b.text() for b in botoes]
        for b in botoes:
            if b.hasFocus():
                visto.botao_com_foco = b.text()
            # Rodada JM: findChildren(QAbstractButton) pega TAMBÉM
            # QCheckBox/QRadioButton, que não têm isDefault() — a
            # AttributeError aqui era engolida pelo laço do Qt e o
            # exec() ficava aberto até o timeout (a doença que o
            # comentário abaixo já descrevia)
            if isinstance(b, QPushButton) and b.isDefault():
                visto.botao_padrao = b.text()
        if tecla is not None:
            QTest.keyClick(caixa, tecla)
            return
        alvo = [b for b in botoes if b.text().strip() == texto_botao]
        if not alvo:
            # nunca ASSERT aqui dentro: exceção em slot é engolida pelo
            # laço do Qt e o exec() ficaria aberto para sempre
            visto.faltou_botao = texto_botao
            caixa.reject()
            return
        QTest.mouseClick(alvo[0], Qt.MouseButton.LeftButton)

    timer.timeout.connect(_tenta)
    timer.start()
    try:
        yield visto
    finally:
        timer.stop()


def drenar(ms: int = 30) -> None:
    """Deixa o laço de eventos respirar (timers, deleteLater agendados
    pelo próprio teste, animações de 1 quadro)."""
    QTest.qWait(ms)

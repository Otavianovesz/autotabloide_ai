"""
Toast — aviso flutuante
=======================
Feedback leve ("Layout salvo", erros) no rodapé da janela: chrome escuro,
ícone semântico, entrada/saída com fade+deslize e auto-dismiss.

Uso::

    from app.qt.design.toast import mostrar_toast
    mostrar_toast(widget_qualquer, "Layout salvo.", tipo="sucesso")
"""

from __future__ import annotations

from PySide6.QtCore import (
    QEasingCurve,
    QPoint,
    QPropertyAnimation,
    Qt,
    QTimer,
)
from PySide6.QtWidgets import (
    QGraphicsOpacityEffect,
    QHBoxLayout,
    QLabel,
    QWidget,
)

from app.qt.design import tokens as t
from app.qt.design.icones import icone

# ícone + cor do ícone por tipo (tons claros: vivem no chrome escuro)
_TIPOS = {
    "sucesso": ("check_circulo", t.SUCESSO_CLARO),
    "erro": ("alerta_circulo", t.PERIGO_CLARO),
    "info": ("info_circulo", t.INFO_CLARO),
}


class Toast(QWidget):
    def __init__(self, janela: QWidget, texto: str, tipo: str = "sucesso",
                 duracao_ms: int = 2600, *, acao: tuple | None = None):
        """``acao=(rotulo, callable)`` põe um botão no toast (FASE 1,
        passos 71-72: "Desfazer" ligado ao undo REAL — janela de 6 s)."""
        super().__init__(janela)
        self.setObjectName("toast")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

        nome_ic, cor_ic = _TIPOS.get(tipo, _TIPOS["info"])
        lay = QHBoxLayout(self)
        lay.setContentsMargins(t.ESP_4, t.ESP_2 + 2, t.ESP_4, t.ESP_2 + 2)
        lay.setSpacing(t.ESP_2)
        ic = QLabel()
        ic.setPixmap(icone(nome_ic, cor=cor_ic, tamanho=17).pixmap(17, 17))
        lay.addWidget(ic)
        lay.addWidget(QLabel(texto))
        if acao is not None:
            from PySide6.QtWidgets import QPushButton
            rotulo, retorno = acao
            botao = QPushButton(rotulo)
            botao.setObjectName("toastAcao")
            botao.setCursor(Qt.CursorShape.PointingHandCursor)

            def _agir() -> None:
                try:
                    retorno()
                finally:
                    self._sair()
            botao.clicked.connect(_agir)
            lay.addSpacing(t.ESP_2)
            lay.addWidget(botao)

        self.adjustSize()
        # FASE 1 (passo 39): fila EMPILHA com espaçamento — um toast por
        # cima do outro era ilegível; cada vivo sobe um degrau
        vivos = [w for w in janela.findChildren(Toast) if w is not self
                 and w.isVisible()]
        degrau = sum(w.height() + 8 for w in vivos)
        x = (janela.width() - self.width()) // 2
        y = janela.height() - self.height() - 28 - degrau
        self.move(x, y + 10)  # nasce 10px abaixo e desliza para o lugar

        # entrada: fade + deslize para cima — pelo MOTOR da casa (passo 39):
        # "Reduzir animações" mostra na hora, zero timer de animação
        from app.qt.design.animacoes import DURACAO_MS, animacoes_ligadas
        self._efeito = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self._efeito)
        self._anim_op = QPropertyAnimation(self._efeito, b"opacity", self)
        self._anim_op.setDuration(DURACAO_MS)
        self._anim_op.setStartValue(0.0)
        self._anim_op.setEndValue(1.0)
        self._anim_pos = QPropertyAnimation(self, b"pos", self)
        self._anim_pos.setDuration(DURACAO_MS)
        self._anim_pos.setStartValue(QPoint(x, y + 10))
        self._anim_pos.setEndValue(QPoint(x, y))
        self._anim_pos.setEasingCurve(QEasingCurve.Type.OutCubic)

        self.show()
        self.raise_()
        if animacoes_ligadas():
            self._anim_op.start()
            self._anim_pos.start()
        else:
            self._efeito.setOpacity(1.0)
            self.move(x, y)
        QTimer.singleShot(duracao_ms, self._sair)

    def _sair(self) -> None:
        from app.qt.design.animacoes import animacoes_ligadas
        if not animacoes_ligadas():
            self.deleteLater()
            return
        self._anim_op.setStartValue(1.0)
        self._anim_op.setEndValue(0.0)
        self._anim_op.finished.connect(self.deleteLater)
        self._anim_op.start()


def mostrar_toast(widget: QWidget, texto: str, tipo: str = "sucesso") -> Toast:
    """Mostra um toast na janela do widget dado."""
    return Toast(widget.window(), texto, tipo)


def mostrar_toast_desfazer(widget: QWidget, texto: str,
                           ao_desfazer) -> Toast:
    """FASE 1 (passos 71-72): toast de ação destrutiva com "Desfazer"
    embutido — 6 s de janela, ligado ao fio de undo REAL do chamador."""
    return Toast(widget.window(), texto, "info", duracao_ms=6000,
                 acao=("Desfazer", ao_desfazer))

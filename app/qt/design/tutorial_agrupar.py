"""
Microtutorial "Como agrupar" (FASE 4, Bloco B — RG-56, passos 25-26)
====================================================================
3 telas que ensinam o conceito mais difícil do app: a célula-mestre.

  1 · marque a célula-mestra  →  2 · replique na grade  →
  3 · ajuste uma cópia sem perder as outras

Abre sozinho na 1ª vez que o dono agrupa (com memória em Config
``tutorial.vistos``, chave ``agrupar``) e fica SEMPRE acessível em
"Ajuda › Como agrupar" — não é pop-up único que some para sempre.
"""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QBrush, QColor, QPainter, QPen
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from app.qt.design import tokens as t
from app.qt.design.tutorial import _marcar_visto, _vistos

CHAVE = "agrupar"

# (título, texto) de cada tela + qual célula da grade 2×2 destacar
_TELAS = [
    ("1 · Marque a célula-mestra",
     "Monte UMA célula do jeito que você quer (imagem, nome, preço) e "
     "clique com o botão direito → “Agrupar como replicável”. Ela vira a "
     "MESTRA — o molde de todas as outras.", "mestra"),
    ("2 · Replique na grade",
     "Com a mestra pronta, carimbe cópias pela grade: botão direito no "
     "fundo → “Carimbar cópia aqui”. Cada cópia nasce igual à mestra, no "
     "lugar que você escolher.", "copias"),
    ("3 · Ajuste uma cópia sem perder as outras",
     "Editou a mestra? Muda em todas. Precisa de um ajuste SÓ numa cópia "
     "(um preço diferente)? Edite a cópia: ela ganha um “ajuste próprio” "
     "(pontinho na região) e para de seguir a mestra só naquilo. Errou? "
     "Botão direito → “Desagrupar” desfaz tudo, sem perder nada.", "ajuste"),
]


class _Ilustracao(QWidget):
    """Grade 2×2 esquemática: âmbar = mestra, violeta = cópia ajustada,
    azul = cópia comum — a mesma linguagem de cor dos badges do canvas."""

    def __init__(self, foco: str):
        super().__init__()
        self._foco = foco
        self.setMinimumHeight(150)

    def paintEvent(self, ev) -> None:  # noqa: N802 (Qt)
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        cw, ch = w * 0.30, h * 0.34
        gx, gy = (w - 2 * cw) / 2 - 10, (h - 2 * ch) / 2
        celulas = [(0, 0), (1, 0), (0, 1), (1, 1)]
        for i, (cx, cy) in enumerate(celulas):
            x, y = gx + cx * (cw + 16), gy + cy * (ch + 14)
            mestra = (i == 0)
            ajuste = (self._foco == "ajuste" and i == 3)
            visivel = mestra or self._foco in ("copias", "ajuste")
            if not visivel:
                cor, alpha = QColor(t.TEXTO_3), 40
            elif mestra:
                cor, alpha = QColor(t.ACENTO), 230        # âmbar = mestra
            elif ajuste:
                cor, alpha = QColor(t.GUIA_SNAP), 230      # violeta = ajustada
            else:
                cor, alpha = QColor(t.SELECAO), 200        # azul = cópia comum
            caneta = QPen(cor, 2.2 if (mestra or ajuste) else 1.4)
            if not visivel:
                caneta.setStyle(Qt.PenStyle.DashLine)
            p.setPen(caneta)
            fundo = QColor(cor)
            fundo.setAlpha(28 if visivel else 12)
            p.setBrush(QBrush(fundo))
            p.drawRoundedRect(int(x), int(y), int(cw), int(ch), 6, 6)
            # o "trio" (3 tracinhos) dentro de cada célula visível
            if visivel:
                p.setPen(QPen(cor, 1.2))
                for k in range(3):
                    ly = y + ch * (0.30 + k * 0.22)
                    p.drawLine(int(x + cw * 0.18), int(ly),
                               int(x + cw * 0.82), int(ly))
            if mestra:
                p.setPen(QPen(QColor(t.ACENTO), 1))
                p.drawText(int(x + 4), int(y + 12), "M")
            elif ajuste:
                p.setPen(QPen(QColor(t.GUIA_SNAP), 1))
                p.drawText(int(x + 4), int(y + 12), "C•")
        p.end()


class TutorialAgrupar(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("tutorialAgrupar")
        self.setWindowTitle("Como agrupar")
        self.setMinimumWidth(460)
        self._pilha = QStackedWidget()
        for titulo, texto, foco in _TELAS:
            pag = QWidget()
            vl = QVBoxLayout(pag)
            vl.setContentsMargins(t.ESP_4, t.ESP_4, t.ESP_4, t.ESP_3)
            vl.setSpacing(t.ESP_3)
            cab = QLabel(titulo)
            cab.setProperty("papel", "titulo")
            corpo = QLabel(texto)
            corpo.setWordWrap(True)
            corpo.setProperty("papel", "legenda")
            vl.addWidget(cab)
            vl.addWidget(_Ilustracao(foco))
            vl.addWidget(corpo)
            vl.addStretch(1)
            self._pilha.addWidget(pag)

        self.pontos = QLabel()
        self.pontos.setProperty("papel", "legenda")
        self.btn_ant = QPushButton("Anterior")
        self.btn_ant.clicked.connect(lambda: self._ir(-1))
        self.btn_prox = QPushButton("Próximo")
        self.btn_prox.setProperty("tipo", "primario")
        self.btn_prox.clicked.connect(self._proximo)
        rodape = QHBoxLayout()
        rodape.addWidget(self.pontos)
        rodape.addStretch(1)
        rodape.addWidget(self.btn_ant)
        rodape.addWidget(self.btn_prox)

        raiz = QVBoxLayout(self)
        raiz.setContentsMargins(0, 0, t.ESP_4, t.ESP_3)
        raiz.addWidget(self._pilha)
        raiz.addLayout(rodape)
        self._atualizar()

    def _ir(self, delta: int) -> None:
        novo = max(0, min(self._pilha.count() - 1,
                          self._pilha.currentIndex() + delta))
        self._pilha.setCurrentIndex(novo)
        self._atualizar()

    def _proximo(self) -> None:
        if self._pilha.currentIndex() >= self._pilha.count() - 1:
            self.accept()
        else:
            self._ir(1)

    def _atualizar(self) -> None:
        i = self._pilha.currentIndex()
        n = self._pilha.count()
        self.pontos.setText(f"{i + 1} de {n}")
        self.btn_ant.setEnabled(i > 0)
        self.btn_prox.setText("Entendi" if i == n - 1 else "Próximo")


def mostrar_tutorial_agrupar(parent, so_se_primeira_vez: bool = False) -> None:
    """Passos 25-26. ``so_se_primeira_vez``: só abre se o dono ainda não
    viu (memória em Config); o menu Ajuda chama sem esse filtro. Segue a lei
    da captura: janela com ``WA_DontShowOnScreen`` mostra/fecha SECO."""
    if so_se_primeira_vez and CHAVE in _vistos():
        return
    _marcar_visto(CHAVE)
    dlg = TutorialAgrupar(parent)
    # SECO (não-bloqueante) quando headless: sem parent, ou a janela do
    # parent está offscreen (foto/teste). exec() modal só com janela real.
    seco = bool(parent is None or parent.window().testAttribute(
        Qt.WidgetAttribute.WA_DontShowOnScreen))
    if seco:
        dlg.setAttribute(Qt.WidgetAttribute.WA_DontShowOnScreen, True)
        dlg.show()
        from PySide6.QtCore import QCoreApplication
        QCoreApplication.processEvents()
        return dlg
    dlg.exec()
    return dlg

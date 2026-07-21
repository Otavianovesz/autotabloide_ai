"""
Aparência (FASE 1, passo 23) — o seletor de tema em CARDS com prévia
====================================================================
Dois cartões clicáveis (Claro/Escuro), cada um com uma prévia em miniatura
PINTADA das cores do tema (janelinha com barra, cartão e botão de acento) —
não um combo seco. Clicar aplica NA HORA (passo 24) e persiste na Config.
"""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QPainter, QPixmap
from PySide6.QtWidgets import QHBoxLayout, QLabel, QVBoxLayout, QWidget

from app.qt.design import tokens as t


def _previa_tema(nome: str, larg: int = 132, alt: int = 84) -> QPixmap:
    """A miniatura do tema: janela + top-bar + cartão + botão de acento."""
    tema = t.TEMAS[nome]
    pm = QPixmap(larg, alt)
    pm.fill(Qt.GlobalColor.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    p.setPen(QColor(tema["BORDA_FORTE"]))
    p.setBrush(QColor(tema["FUNDO_APP"]))
    p.drawRoundedRect(0, 0, larg - 1, alt - 1, 8, 8)
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(QColor(tema["SUPERFICIE"]))          # top-bar
    p.drawRoundedRect(1, 1, larg - 2, 16, 7, 7)
    p.setBrush(QColor(tema["SUPERFICIE"]))          # cartão
    p.drawRoundedRect(10, 24, larg - 20, alt - 46, 6, 6)
    p.setBrush(QColor(tema["TEXTO"]))               # "texto" (linhas)
    p.drawRoundedRect(18, 32, larg - 60, 5, 2, 2)
    p.setBrush(QColor(tema["TEXTO_2"]))
    p.drawRoundedRect(18, 42, larg - 44, 4, 2, 2)
    p.setBrush(QColor(tema["TEXTO_3"]))
    p.drawRoundedRect(18, 50, larg - 76, 4, 2, 2)
    p.setBrush(QColor(tema["PRIMARIA"]))            # botão de acento
    p.drawRoundedRect(larg - 46, alt - 18, 36, 11, 5, 5)
    p.end()
    return pm


class CartaoTema(QWidget):
    clicado = Signal(str)

    def __init__(self, nome: str, rotulo: str, parent=None):
        super().__init__(parent)
        self.nome = nome
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._img = QLabel()
        self._img.setPixmap(_previa_tema(nome))
        self._rotulo = QLabel(rotulo)
        self._rotulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(t.ESP_2, t.ESP_2, t.ESP_2, t.ESP_2)
        lay.setSpacing(t.ESP_1)
        lay.addWidget(self._img, alignment=Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(self._rotulo)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.marcar(False)

    def marcar(self, ativo: bool) -> None:
        borda = t.PRIMARIA if ativo else t.BORDA
        grossura = 2 if ativo else 1
        self.setStyleSheet(
            f"CartaoTema {{ border: {grossura}px solid {borda}; "
            f"border-radius: 10px; background: {t.SUPERFICIE}; }}")
        fonte = self._rotulo.font()
        fonte.setBold(ativo)
        self._rotulo.setFont(fonte)

    def mousePressEvent(self, _ev) -> None:  # noqa: N802 (Qt)
        self.clicado.emit(self.nome)


class SeletorTema(QWidget):
    """Os dois cards lado a lado; clicar troca o tema NA HORA (passo 24)."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._cards = {"claro": CartaoTema("claro", "Claro"),
                       "escuro": CartaoTema("escuro", "Escuro")}
        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(t.ESP_3)
        for card in self._cards.values():
            card.clicado.connect(self._escolher)
            lay.addWidget(card)
        lay.addStretch(1)
        self.sincronizar()

    def sincronizar(self) -> None:
        for nome, card in self._cards.items():
            card.marcar(nome == t.TEMA_ATUAL)
            card._img.setPixmap(_previa_tema(nome))   # prévia sempre fiel

    def _escolher(self, nome: str) -> None:
        if nome == t.TEMA_ATUAL:
            return
        from app.qt.design.tema import trocar_tema
        trocar_tema(nome)                  # aplica na hora + persiste (p. 24)
        self.sincronizar()

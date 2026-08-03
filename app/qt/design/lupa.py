"""
Lupa — ampliar qualquer imagem da UI (pedido do dono, 02/08/2026)
=================================================================
"Eu preciso ver se a gramatura está certa e não consigo aumentar o
tamanho dela pra ver na UI."

Um visualizador só, para TODA imagem do app (a porta única, L11):
roda do mouse dá zoom ancorado no cursor, arrastar move, duplo clique
alterna ajustar↔100%, +/− pelo teclado, 0 ajusta, 1 = tamanho real,
Esc fecha. O rodapé diz o arquivo, o tamanho em pixels e o zoom — o
rótulo da gramatura se lê no 100% (ou além: até 800%).
"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QKeySequence, QPixmap, QShortcut
from PySide6.QtWidgets import (
    QDialog,
    QGraphicsPixmapItem,
    QGraphicsScene,
    QGraphicsView,
    QLabel,
    QPushButton,
    QHBoxLayout,
    QVBoxLayout,
)

from app.qt.design import tokens as t

_ZOOM_MIN = 0.05
_ZOOM_MAX = 8.0


class _Tela(QGraphicsView):
    """A área da imagem: roda = zoom no cursor, arrasto = pan."""

    def __init__(self, dono: "Lupa"):
        super().__init__()
        self._dono = dono
        from PySide6.QtGui import QPainter
        self.setRenderHints(QPainter.RenderHint.SmoothPixmapTransform
                            | QPainter.RenderHint.Antialiasing)
        self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        self.setTransformationAnchor(
            QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setResizeAnchor(
            QGraphicsView.ViewportAnchor.AnchorViewCenter)

    def wheelEvent(self, ev) -> None:  # noqa: N802 (Qt)
        passo = 1.25 if ev.angleDelta().y() > 0 else 0.8
        self._dono.aplicar_zoom(self._dono.zoom * passo)

    def mouseDoubleClickEvent(self, ev) -> None:  # noqa: N802 (Qt)
        self._dono.alternar()


class Lupa(QDialog):
    """``Lupa(caminho, parent).exec()`` — ou a porta ``ampliar_imagem``."""

    def __init__(self, caminho: str, parent=None,
                 titulo: str | None = None):
        super().__init__(parent)
        self._pm = QPixmap(str(caminho))
        nome = titulo or Path(str(caminho)).name
        self.setWindowTitle(f"Lupa — {nome}")
        self.zoom = 1.0

        self._cena = QGraphicsScene(self)
        self._item = QGraphicsPixmapItem(self._pm)
        self._item.setTransformationMode(
            Qt.TransformationMode.SmoothTransformation)
        self._cena.addItem(self._item)
        self._tela = _Tela(self)
        self._tela.setScene(self._cena)

        self._rodape = QLabel("")
        self._rodape.setProperty("papel", "legenda")
        dica = QLabel("roda = zoom · arrastar = mover · duplo clique = "
                      "ajustar/100% · Esc fecha")
        dica.setProperty("papel", "legenda")
        b_ajustar = QPushButton("Ajustar")
        b_ajustar.clicked.connect(self.ajustar)
        b_100 = QPushButton("100%")
        b_100.setToolTip("Tamanho real — o rótulo da gramatura se lê aqui")
        b_100.clicked.connect(lambda: self.aplicar_zoom(1.0))
        rodape = QHBoxLayout()
        rodape.setSpacing(t.ESP_2)
        rodape.addWidget(self._rodape)
        rodape.addStretch(1)
        rodape.addWidget(dica)
        rodape.addWidget(b_ajustar)
        rodape.addWidget(b_100)

        raiz = QVBoxLayout(self)
        raiz.setContentsMargins(t.ESP_2, t.ESP_2, t.ESP_2, t.ESP_2)
        raiz.setSpacing(t.ESP_1)
        raiz.addWidget(self._tela, 1)
        raiz.addLayout(rodape)

        for seq, fn in (("+", lambda: self.aplicar_zoom(self.zoom * 1.25)),
                        ("=", lambda: self.aplicar_zoom(self.zoom * 1.25)),
                        ("-", lambda: self.aplicar_zoom(self.zoom * 0.8)),
                        ("0", self.ajustar),
                        ("1", lambda: self.aplicar_zoom(1.0))):
            QShortcut(QKeySequence(seq), self, fn)

        # nasce grande (a tela quase toda) e AJUSTADO; a L3 clampa
        self.resize(980, 720)
        if self._pm.isNull():
            self._rodape.setText("imagem não pôde ser aberta")

    def showEvent(self, ev) -> None:  # noqa: N802 (Qt)
        super().showEvent(ev)
        from app.qt.design.polimento import clampar_a_tela
        clampar_a_tela(self)
        self.ajustar()

    # --- zoom -----------------------------------------------------------------

    def aplicar_zoom(self, novo: float) -> None:
        novo = max(_ZOOM_MIN, min(_ZOOM_MAX, novo))
        self.zoom = novo
        self._tela.resetTransform()
        self._tela.scale(novo, novo)
        self._atualizar_rodape()

    def ajustar(self) -> None:
        """A imagem inteira na janela (o zoom que couber)."""
        if self._pm.isNull() or self._pm.width() == 0:
            return
        vp = self._tela.viewport().size()
        fator = min(vp.width() / self._pm.width(),
                    vp.height() / self._pm.height())
        self.aplicar_zoom(min(fator, 1.0) if fator > 0 else 1.0)
        self._tela.centerOn(self._item)

    def alternar(self) -> None:
        """Duplo clique: ajustar ↔ 100% (o gesto de conferir gramatura)."""
        if abs(self.zoom - 1.0) < 0.01:
            self.ajustar()
        else:
            self.aplicar_zoom(1.0)

    def _atualizar_rodape(self) -> None:
        if self._pm.isNull():
            return
        self._rodape.setText(
            f"{self._pm.width()}×{self._pm.height()} px · "
            f"zoom {round(self.zoom * 100)}%")


def ampliar_imagem(parent, caminho: str | None,
                   titulo: str | None = None) -> None:
    """A porta única da lupa — chamável de qualquer tela; caminho vazio
    ou arquivo sumido avisa em vez de abrir janela em branco (I2)."""
    if not caminho or not Path(str(caminho)).is_file():
        from app.qt.design.toast import mostrar_toast
        if parent is not None:
            mostrar_toast(parent, "Sem imagem para ampliar aqui.",
                          tipo="erro")
        return
    Lupa(str(caminho), parent).exec()

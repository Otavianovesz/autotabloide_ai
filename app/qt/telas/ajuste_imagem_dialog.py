"""
Ajustar imagem — girar/espelhar/cortar com prévia (polimento F10)
=================================================================
O modelo da curadoria (F10: `girar`, `espelhar`, `cortar` — puros, sobre cópia)
estava pronto sem UI. Este editor pequeno fecha a dívida: prévia ao vivo,
girar ↺/↻, espelhar, corte por SELEÇÃO (arrastar na prévia) e "Começar de
novo". Tudo NÃO-DESTRUTIVO: o resultado vira uma NOVA versão na biblioteca
(a anterior fica no histórico — I1, nada se perde).
"""

from __future__ import annotations

import tempfile
from pathlib import Path

from PIL import Image
from PySide6.QtCore import QPoint, QRect, QSize, Qt
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QRubberBand,
    QVBoxLayout,
)

from app.images import curadoria
from app.qt.canvas import pil_para_qpixmap
from app.qt.design import tokens as t
from app.qt.design.icones import icone


class _Previa(QLabel):
    """A prévia com SELEÇÃO por arrasto (QRubberBand) para o corte."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setMinimumSize(360, 300)
        self._banda = QRubberBand(QRubberBand.Shape.Rectangle, self)
        self._origem: QPoint | None = None
        self.selecao: QRect | None = None      # em coords do WIDGET

    def mousePressEvent(self, ev) -> None:  # noqa: N802 (Qt)
        self._origem = ev.position().toPoint()
        self._banda.setGeometry(QRect(self._origem, QSize()))
        self._banda.show()

    def mouseMoveEvent(self, ev) -> None:  # noqa: N802 (Qt)
        if self._origem is not None:
            self._banda.setGeometry(
                QRect(self._origem, ev.position().toPoint()).normalized())

    def mouseReleaseEvent(self, ev) -> None:  # noqa: N802 (Qt)
        if self._origem is None:
            return
        rect = QRect(self._origem, ev.position().toPoint()).normalized()
        self._origem = None
        if rect.width() < 8 or rect.height() < 8:   # clique ≠ seleção
            self.limpar_selecao()
            return
        self.selecao = rect

    def limpar_selecao(self) -> None:
        self.selecao = None
        self._banda.hide()


class AjusteImagemDialog(QDialog):
    """Girar/espelhar/cortar a foto — o resultado vira NOVA versão."""

    def __init__(self, caminho: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Ajustar imagem")
        self._original = Image.open(caminho).convert("RGBA")
        self._img = self._original.copy()

        raiz = QVBoxLayout(self)
        raiz.setContentsMargins(t.ESP_4, t.ESP_4, t.ESP_4, t.ESP_4)
        raiz.setSpacing(t.ESP_2)
        titulo = QLabel("Ajustar imagem")
        titulo.setProperty("papel", "titulo")
        raiz.addWidget(titulo)
        dica = QLabel("Arraste na prévia para marcar um corte. Nada é "
                      "destrutivo: a foto anterior fica no histórico.")
        dica.setProperty("papel", "legenda")
        dica.setWordWrap(True)
        raiz.addWidget(dica)

        self.previa = _Previa()
        raiz.addWidget(self.previa, 1)

        def _botao(rotulo, nome_icone, dica_txt, fn):
            b = QPushButton(f" {rotulo}")
            b.setIcon(icone(nome_icone, tamanho=16))
            b.setToolTip(dica_txt)
            b.clicked.connect(fn)
            return b

        barra = QHBoxLayout()
        barra.setSpacing(t.ESP_2)
        barra.addWidget(_botao("Girar ⟲", "desfazer",
                               "Gira 90° para a esquerda",
                               lambda: self._aplicar(curadoria.girar, -90)))
        barra.addWidget(_botao("Girar ⟳", "refazer",
                               "Gira 90° para a direita",
                               lambda: self._aplicar(curadoria.girar, 90)))
        barra.addWidget(_botao("Espelhar", "dist_h",
                               "Espelha horizontalmente",
                               lambda: self._aplicar(curadoria.espelhar)))
        self.btn_cortar = _botao("Cortar na seleção", "ajustar",
                                 "Corta a área marcada na prévia",
                                 self._cortar)
        barra.addWidget(self.btn_cortar)
        barra.addWidget(_botao("Começar de novo", "restaurar",
                               "Volta à foto como estava ao abrir",
                               self._reiniciar))
        barra.addStretch(1)
        raiz.addLayout(barra)

        botoes = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok
                                  | QDialogButtonBox.StandardButton.Cancel)
        ok = botoes.button(QDialogButtonBox.StandardButton.Ok)
        ok.setText("Salvar como nova versão")
        ok.setToolTip("A foto ajustada vira a atual; a anterior vai para o "
                      "histórico")
        botoes.button(QDialogButtonBox.StandardButton.Cancel).setText(
            "Cancelar")
        botoes.accepted.connect(self.accept)
        botoes.rejected.connect(self.reject)
        raiz.addWidget(botoes)
        self.resize(560, 560)
        self._repintar()

    # --- operações (todas sobre cópia — curadoria.py é puro) -----------------

    def _aplicar(self, fn, *args) -> None:
        self._img = fn(self._img, *args)
        self.previa.limpar_selecao()
        self._repintar()

    def _reiniciar(self) -> None:
        self._img = self._original.copy()
        self.previa.limpar_selecao()
        self._repintar()

    def _cortar(self) -> None:
        sel = self.previa.selecao
        pm = self.previa.pixmap()
        if sel is None or pm is None or pm.isNull():
            return
        # mapeia a seleção (coords do widget) para a IMAGEM: a prévia é
        # centralizada e escalada — desconta a folga e divide pela escala
        off_x = (self.previa.width() - pm.width()) // 2
        off_y = (self.previa.height() - pm.height()) // 2
        esc = self._img.width / pm.width()
        x0 = max(0, round((sel.left() - off_x) * esc))
        y0 = max(0, round((sel.top() - off_y) * esc))
        x1 = min(self._img.width, round((sel.right() - off_x) * esc))
        y1 = min(self._img.height, round((sel.bottom() - off_y) * esc))
        self._img = curadoria.cortar(self._img, (x0, y0, x1, y1))
        self.previa.limpar_selecao()
        self._repintar()

    def _repintar(self) -> None:
        pm = pil_para_qpixmap(self._img)
        alvo = self.previa.size()
        self.previa.setPixmap(pm.scaled(
            alvo, Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation))

    def resizeEvent(self, ev) -> None:  # noqa: N802 (Qt)
        super().resizeEvent(ev)
        self._repintar()

    # --- resultado -----------------------------------------------------------

    def imagem_final(self) -> Image.Image:
        return self._img

    def caminho_final(self) -> str:
        """Grava o resultado num PNG temporário (o chamador o ingere na
        biblioteca como nova versão)."""
        destino = Path(tempfile.mkdtemp(prefix="ajuste_")) / "ajustada.png"
        self._img.save(destino)
        return str(destino)

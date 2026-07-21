"""
Pincel de refino do recorte (OS F11.5 #31/#32 — F10)
====================================================
O `curadoria.refinar_alfa` existia só como modelo. Aqui vira gesto: o dono
PINTA sobre a foto — "Restaurar" devolve pixel que o rembg comeu (alfa 255),
"Apagar" tira sobra de fundo (alfa 0). Não-destrutivo: trabalha numa CÓPIA;
Aplicar grava um PNG novo (quem chama decide ingerir como versão).
"""

from __future__ import annotations

import tempfile
from pathlib import Path

from PIL import Image
from PySide6.QtCore import Qt
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QRadioButton,
    QSlider,
    QVBoxLayout,
)

from app.qt.design import tokens as t

_LADO_MAX = 480          # a foto aparece no máx. neste lado (o traço escala)


def _qimage_de(img: Image.Image) -> QImage:
    """RGBA → QImage composto sobre xadrez claro (o alfa fica visível)."""
    fundo = Image.new("RGBA", img.size, (245, 245, 245, 255))
    passo = max(8, img.width // 40)
    for x in range(0, img.width, passo * 2):
        for y in range(0, img.height, passo * 2):
            for dx, dy in ((0, 0), (passo, passo)):
                caixa = (x + dx, y + dy,
                         min(x + dx + passo, img.width),
                         min(y + dy + passo, img.height))
                fundo.paste((220, 220, 220, 255), caixa)
    composto = Image.alpha_composite(fundo, img.convert("RGBA"))
    dados = composto.convert("RGBA").tobytes()
    return QImage(dados, composto.width, composto.height,
                  QImage.Format.Format_RGBA8888).copy()


class RefinoDialog(QDialog):
    """Pinte para restaurar/apagar o recorte; Aplicar grava o PNG refinado."""

    def __init__(self, caminho: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Refinar o recorte (pincel)")
        self._original = Image.open(str(caminho)).convert("RGBA")
        self._img = self._original.copy()
        self._esc = min(1.0, _LADO_MAX / max(self._img.size))
        self.caminho_final: str | None = None

        raiz = QVBoxLayout(self)
        raiz.setContentsMargins(t.ESP_4, t.ESP_4, t.ESP_4, t.ESP_4)
        raiz.setSpacing(t.ESP_2)
        titulo = QLabel("Refinar o recorte")
        titulo.setProperty("papel", "titulo")
        raiz.addWidget(titulo)
        legenda = QLabel("Pinte sobre a foto: “Restaurar” devolve o pedaço "
                         "que o recorte comeu; “Apagar” tira a sobra de "
                         "fundo. Nada muda até você Aplicar.")
        legenda.setProperty("papel", "legenda")
        legenda.setWordWrap(True)
        raiz.addWidget(legenda)

        self._tela = QLabel()
        self._tela.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._tela.setMouseTracking(False)
        self._tela.mousePressEvent = self._pincel_press
        self._tela.mouseMoveEvent = self._pincel_move
        raiz.addWidget(self._tela, 1)

        linha = QHBoxLayout()
        self.rb_restaurar = QRadioButton("Restaurar (devolver pixel)")
        self.rb_apagar = QRadioButton("Apagar (tirar sobra)")
        self.rb_restaurar.setChecked(True)
        self.raio = QSlider(Qt.Orientation.Horizontal)
        self.raio.setRange(4, 80)
        self.raio.setValue(18)
        self.raio.setToolTip("Tamanho do pincel")
        btn_zerar = QPushButton("Desfazer tudo")
        btn_zerar.setToolTip("Volta a foto ao estado de antes do pincel")
        btn_zerar.clicked.connect(self._zerar)
        linha.addWidget(self.rb_restaurar)
        linha.addWidget(self.rb_apagar)
        linha.addWidget(QLabel("Pincel:"))
        linha.addWidget(self.raio, 1)
        linha.addWidget(btn_zerar)
        raiz.addLayout(linha)

        botoes = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok
                                  | QDialogButtonBox.StandardButton.Cancel)
        botoes.button(QDialogButtonBox.StandardButton.Ok).setText("Aplicar")
        botoes.button(QDialogButtonBox.StandardButton.Cancel).setText(
            "Cancelar")
        botoes.accepted.connect(self._aplicar)
        botoes.rejected.connect(self.reject)
        raiz.addWidget(botoes)
        self._refrescar()

    # --- pincel -----------------------------------------------------------------

    def _ponto_da_tela(self, ev) -> tuple[int, int] | None:
        """Posição do clique → coordenada da IMAGEM (desfaz a escala e o
        centramento do QLabel)."""
        pm = self._tela.pixmap()
        if pm is None or pm.isNull():
            return None
        ox = (self._tela.width() - pm.width()) // 2
        oy = (self._tela.height() - pm.height()) // 2
        x = (ev.position().x() - ox) / self._esc
        y = (ev.position().y() - oy) / self._esc
        if 0 <= x < self._img.width and 0 <= y < self._img.height:
            return int(x), int(y)
        return None

    def _pincel_press(self, ev) -> None:
        p = self._ponto_da_tela(ev)
        if p is not None:
            self.pintar([p])

    def _pincel_move(self, ev) -> None:
        if ev.buttons() & Qt.MouseButton.LeftButton:
            p = self._ponto_da_tela(ev)
            if p is not None:
                self.pintar([p])

    def pintar(self, pontos: list[tuple[int, int]]) -> None:
        """O gesto (testável sem mouse): aplica o pincel na CÓPIA de
        trabalho e redesenha."""
        from app.images.curadoria import refinar_alfa
        self._img = refinar_alfa(self._img, pontos, int(self.raio.value()),
                                 apagar=self.rb_apagar.isChecked())
        self._refrescar()

    def _zerar(self) -> None:
        self._img = self._original.copy()
        self._refrescar()

    def _refrescar(self) -> None:
        qi = _qimage_de(self._img)
        pm = QPixmap.fromImage(qi)
        if self._esc < 1.0:
            pm = pm.scaled(int(self._img.width * self._esc),
                           int(self._img.height * self._esc),
                           Qt.AspectRatioMode.KeepAspectRatio,
                           Qt.TransformationMode.SmoothTransformation)
        self._tela.setPixmap(pm)

    # --- aplicar ----------------------------------------------------------------

    def _aplicar(self) -> None:
        destino = Path(tempfile.mkdtemp(prefix="atb_refino_")) / "refinada.png"
        self._img.save(destino, "PNG")
        self.caminho_final = str(destino)
        self.accept()

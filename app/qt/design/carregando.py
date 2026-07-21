"""
Indicadores de carregamento
===========================
Para as etapas lentas (IA e imagem): "Enriquecendo nome…", "Buscando imagem…",
"Removendo fundo…". Dois formatos:

- :class:`IndicadorOcupado` — spinner + texto, inline (barra de status, painéis);
- :class:`OverlayOcupado` — véu translúcido sobre um widget, com o indicador
  centralizado (bloqueia visualmente a área ocupada, sem congelar a UI — o
  trabalho pesado roda num worker; o overlay só mostra/esconde).
"""

from __future__ import annotations

from PySide6.QtCore import QEvent, QObject, QRectF, Qt, QTimer
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import QHBoxLayout, QLabel, QVBoxLayout, QWidget

from app.qt.design import tokens as t


from contextlib import contextmanager


@contextmanager
def cursor_espera():
    """FASE 1 (passo 75): operação SÍNCRONA >300 ms mostra a ampulheta —
    nunca congelado mudo. (Trabalho de worker já tem OverlayOcupado.)

    Uso::

        with cursor_espera():
            compor_miniatura(...)
    """
    from PySide6.QtWidgets import QApplication
    app = QApplication.instance()
    if app is not None:
        app.setOverrideCursor(Qt.CursorShape.WaitCursor)
    try:
        yield
    finally:
        if app is not None:
            app.restoreOverrideCursor()


class Spinner(QWidget):
    """Arco girando — leve, sem GIF, na cor primária."""

    def __init__(self, tamanho: int = 18, largura: float = 2.4,
                 cor: str = t.PRIMARIA, parent=None):
        super().__init__(parent)
        self._angulo = 0
        self._largura = largura
        self._cor = QColor(cor)
        self.setFixedSize(tamanho, tamanho)
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._girar)
        self._timer.start(30)

    def _girar(self) -> None:
        self._angulo = (self._angulo + 9) % 360
        self.update()

    def paintEvent(self, _event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        caneta = QPen(self._cor, self._largura)
        caneta.setCapStyle(Qt.PenCapStyle.RoundCap)
        p.setPen(caneta)
        m = self._largura / 2 + 1
        r = QRectF(m, m, self.width() - 2 * m, self.height() - 2 * m)
        p.drawArc(r, -self._angulo * 16, 100 * 16)   # arco de ~100°
        p.end()

    def hideEvent(self, event) -> None:      # não gasta timer escondido
        self._timer.stop()
        super().hideEvent(event)

    def showEvent(self, event) -> None:
        self._timer.start(30)
        super().showEvent(event)


class BarraIndeterminada(QWidget):
    """FASE 1 (passo 44): trilho fino com um "cometa" deslizando em loop —
    o indeterminado da casa (a QProgressBar nativa indeterminada do Windows
    é dura e pisca). Timer só enquanto visível, como o Spinner.

    Nota: indicador de atividade é INFORMAÇÃO ("estou trabalhando"), não
    decoração — por isso se move mesmo com "Reduzir animações", igual ao
    Spinner que já era assim."""

    def __init__(self, largura: int = 200, parent=None):
        super().__init__(parent)
        self._fase = 0.0
        self.setFixedSize(largura, 4)
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._andar)

    def _andar(self) -> None:
        self._fase = (self._fase + 0.018) % 1.0
        self.update()

    def paintEvent(self, _event) -> None:  # noqa: N802 (Qt)
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor(t.PRIMARIA_SUAVE))
        p.drawRoundedRect(self.rect(), 2, 2)
        w = self.width()
        wc = max(24, int(w * 0.3))               # o cometa: 30% do trilho
        x = int(self._fase * (w + wc)) - wc      # entra por fora, sai por fora
        p.setBrush(QColor(t.PRIMARIA))
        p.drawRoundedRect(x, 0, wc, self.height(), 2, 2)
        p.end()

    def hideEvent(self, event) -> None:  # noqa: N802 — não gasta timer escondido
        self._timer.stop()
        super().hideEvent(event)

    def showEvent(self, event) -> None:  # noqa: N802 (Qt)
        self._timer.start(30)
        super().showEvent(event)


class IndicadorOcupado(QWidget):
    """Spinner + texto, lado a lado ("Buscando imagem…")."""

    def __init__(self, texto: str = "", parent=None):
        super().__init__(parent)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(t.ESP_2)
        self._spinner = Spinner()
        self._rotulo = QLabel(texto)
        self._rotulo.setProperty("papel", "legenda")
        lay.addWidget(self._spinner)
        lay.addWidget(self._rotulo)

    def set_texto(self, texto: str) -> None:
        self._rotulo.setText(texto)


class OverlayOcupado(QWidget):
    """Véu translúcido sobre um widget-alvo com o indicador centralizado.

    ``mostrar("Removendo fundo…")`` / ``esconder()``. Acompanha o redimensionar
    do alvo. O trabalho pesado deve rodar fora da thread da UI.
    """

    def __init__(self, alvo: QWidget):
        super().__init__(alvo)
        self.setObjectName("overlayOcupado")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self._alvo = alvo

        caixa = QWidget()
        caixa.setObjectName("overlayCaixa")
        caixa.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        dentro = QVBoxLayout(caixa)
        dentro.setContentsMargins(t.ESP_4, t.ESP_3, t.ESP_4, t.ESP_3)
        dentro.setSpacing(t.ESP_2)
        linha = QHBoxLayout()
        linha.setSpacing(t.ESP_2)
        self._spinner = Spinner(22)
        self._rotulo = QLabel("")
        linha.addWidget(self._spinner)
        linha.addWidget(self._rotulo)
        linha.addStretch(1)
        dentro.addLayout(linha)
        # FASE 1 (passo 44): movimento contínuo — a caixa parada dava
        # sensação de travamento mesmo com o spinner girando
        self._barra = BarraIndeterminada()
        dentro.addWidget(self._barra)

        lay = QVBoxLayout(self)
        lay.addStretch(1)
        h = QHBoxLayout()
        h.addStretch(1)
        h.addWidget(caixa)
        h.addStretch(1)
        lay.addLayout(h)
        lay.addStretch(1)

        alvo.installEventFilter(self)
        self.hide()

    def eventFilter(self, obj: QObject, event: QEvent) -> bool:
        # getattr: na destruição, o lado C++ ainda filtra depois do Python desmontar
        alvo = getattr(self, "_alvo", None)
        if alvo is not None and obj is alvo and event.type() == QEvent.Type.Resize:
            self.setGeometry(alvo.rect())
        return super().eventFilter(obj, event)

    def mostrar(self, texto: str) -> None:
        # RG-04/RG-02 (percepção): tempo decorrido ao lado do status — o
        # dono vê que o app está TRABALHANDO, não travado
        import time

        from PySide6.QtCore import QTimer
        self._texto_base = texto
        if not self.isVisible():
            self._inicio = time.monotonic()
            if not hasattr(self, "_timer"):
                self._timer = QTimer(self)
                self._timer.setInterval(1000)
                self._timer.timeout.connect(self._tic)
            self._timer.start()
        self._tic()
        self.setGeometry(self._alvo.rect())
        self.show()
        self.raise_()

    def _tic(self) -> None:
        import time
        seg = int(time.monotonic() - getattr(self, "_inicio", time.monotonic()))
        sufixo = ""
        if seg >= 3:                     # só aparece quando começa a demorar
            m, s = divmod(seg, 60)
            sufixo = f"   ·  há {m}min{s:02d}s" if m else f"   ·  há {s}s"
        self._rotulo.setText(getattr(self, "_texto_base", "") + sufixo)

    def esconder(self) -> None:
        if hasattr(self, "_timer"):
            self._timer.stop()
        self.hide()

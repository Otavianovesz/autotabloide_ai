"""
Barra de ferramentas do editor (F5.4 + polimento)
=================================================
Botões rotulados e com tooltip: zoom, adicionar região, alinhar, distribuir,
salvar/carregar layout. Age sobre o canvas e o editor.
"""

from __future__ import annotations

from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QMenu,
    QPushButton,
    QToolButton,
    QWidget,
)

from app.rendering.model import TipoRegiao


def _btn(texto: str, tip: str, slot, largura: int | None = None) -> QPushButton:
    b = QPushButton(texto)
    b.setToolTip(tip)
    b.clicked.connect(slot)
    if largura:
        b.setFixedWidth(largura)
    return b


def _sep() -> QFrame:
    f = QFrame()
    f.setFrameShape(QFrame.Shape.VLine)
    f.setFrameShadow(QFrame.Shadow.Sunken)
    return f


class BarraFerramentas(QWidget):
    def __init__(self, editor, parent=None):
        super().__init__(parent)
        c = editor.canvas
        lay = QHBoxLayout(self)
        lay.setContentsMargins(6, 4, 6, 4)
        lay.setSpacing(4)

        # zoom
        lay.addWidget(_btn("－", "Diminuir zoom", c.zoom_menos, 34))
        lay.addWidget(_btn("＋", "Aumentar zoom", c.zoom_mais, 34))
        lay.addWidget(_btn("Ajustar", "Ajustar à tela", c.ajustar))
        lay.addWidget(_sep())

        # adicionar região
        for rot, tipo in [
            ("+ Img", TipoRegiao.IMAGEM), ("+ Nome", TipoRegiao.NOME),
            ("+ Preço", TipoRegiao.PRECO), ("+ Un", TipoRegiao.UNIDADE),
            ("+ Selo", TipoRegiao.SELO),
        ]:
            lay.addWidget(_btn(rot, f"Adicionar região {tipo.value}",
                               lambda _=False, t=tipo: c.adicionar_regiao(t)))
        lay.addWidget(_sep())

        # alinhar (na seleção) — rótulos em texto, sem símbolos cifrados.
        # FASE 1 (passo 57): alinhar+distribuir são os grupos MENOS usados —
        # abaixo de 1200 px eles colapsam num "···" com menu (nada some)
        acoes_alinhar = [
            ("Esq", "esq", "Alinhar à esquerda"), ("Cent", "centro_h", "Centralizar na horizontal"),
            ("Dir", "dir", "Alinhar à direita"), ("Topo", "topo", "Alinhar ao topo"),
            ("Meio", "meio", "Centralizar na vertical"), ("Base", "base", "Alinhar à base"),
        ]
        self._colapsaveis: list[QWidget] = []
        for rot, modo, tip in acoes_alinhar:
            b = _btn(rot, tip, lambda _=False, m=modo: c.alinhar_selecionadas(m))
            self._colapsaveis.append(b)
            lay.addWidget(b)
        sep_a = _sep()
        self._colapsaveis.append(sep_a)
        lay.addWidget(sep_a)

        # distribuir
        for rot, tip, modo in [
            ("Distr. H", "Distribuir igualmente na horizontal", "h"),
            ("Distr. V", "Distribuir igualmente na vertical", "v"),
        ]:
            b = _btn(rot, tip, lambda _=False, m=modo: c.distribuir_selecionadas(m))
            self._colapsaveis.append(b)
            lay.addWidget(b)
        sep_d = _sep()
        self._colapsaveis.append(sep_d)
        lay.addWidget(sep_d)

        # o "···" que herda os grupos colapsados na janela estreita
        self._mais = QToolButton()
        self._mais.setText("···")
        self._mais.setToolTip("Alinhar e distribuir")
        self._mais.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        menu = QMenu(self._mais)
        for rot, modo, tip in acoes_alinhar:
            menu.addAction(tip, lambda m=modo: c.alinhar_selecionadas(m))
        menu.addSeparator()
        menu.addAction("Distribuir igualmente na horizontal",
                       lambda: c.distribuir_selecionadas("h"))
        menu.addAction("Distribuir igualmente na vertical",
                       lambda: c.distribuir_selecionadas("v"))
        self._mais.setMenu(menu)
        self._mais.hide()
        lay.addWidget(self._mais)

        # layout no banco
        lay.addWidget(_btn("Salvar", "Salvar o layout no banco", editor.salvar))
        lay.addWidget(_btn("Carregar", "Carregar um layout salvo", editor.carregar_do_banco))
        lay.addStretch(1)

    LIMIAR_COMPACTO = 1200      # px de largura da janela (passo 57)

    def resizeEvent(self, ev) -> None:  # noqa: N802 (Qt)
        super().resizeEvent(ev)
        compacto = self.width() < self.LIMIAR_COMPACTO
        for w in self._colapsaveis:
            w.setVisible(not compacto)
        self._mais.setVisible(compacto)

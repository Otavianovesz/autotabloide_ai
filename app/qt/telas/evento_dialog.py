"""
Diálogo de Evento (FASE 2, passo 9)
===================================
Criar/editar um evento: nome, cor (paleta de 12), dia da semana opcional
(alimenta o RG-24) e capa opcional. Usado pelo "Novo evento" do Início e
pelo botão direito do cartão (passo 10).
"""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPainter, QPixmap
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QToolButton,
    QWidget,
    QVBoxLayout,
)

from app.qt.design import tokens as t
from app.qt.telas.eventos import PALETA_EVENTOS, cor_para_nome

_DIAS_ROTULOS = ["segunda", "terça", "quarta", "quinta", "sexta",
                 "sábado", "domingo"]


def _swatch(cor: str, lado: int = 22) -> QPixmap:
    pm = QPixmap(lado, lado)
    pm.fill(Qt.GlobalColor.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(QColor(cor))
    p.drawRoundedRect(0, 0, lado, lado, 6, 6)
    p.end()
    return pm


class EventoDialog(QDialog):
    """``valores()`` → (nome, cor, dia_semana | None, capa | None)."""

    def __init__(self, parent=None, *, nome: str = "", cor: str | None = None,
                 dia_semana: int | None = None, titulo: str = "Novo evento"):
        super().__init__(parent)
        self.setWindowTitle(titulo)
        self._cor = cor or (cor_para_nome(nome) if nome
                            else PALETA_EVENTOS[0])
        self._capa: str | None = None

        self.campo_nome = QLineEdit(nome)
        self.campo_nome.setPlaceholderText("ex.: Sexta Verde")
        # a cor sugerida acompanha o nome (estável por hash), até o dono
        # escolher uma na mão
        self._cor_manual = cor is not None
        self.campo_nome.textEdited.connect(self._nome_mudou)

        # paleta de 12 — botões-swatch; o escolhido ganha anel
        self._botoes_cor: list[QToolButton] = []
        linha_cores = QHBoxLayout()
        linha_cores.setSpacing(4)
        for c in PALETA_EVENTOS:
            b = QToolButton()
            b.setObjectName("swatchCor")
            b.setIcon(_swatch(c))
            b.setToolTip(c)
            b.setCheckable(True)
            b.setChecked(c.lower() == self._cor.lower())
            b.clicked.connect(lambda _=False, cc=c: self._escolher_cor(cc))
            self._botoes_cor.append(b)
            linha_cores.addWidget(b)
        linha_cores.addStretch(1)
        caixa_cores = QWidget()
        caixa_cores.setLayout(linha_cores)

        self.combo_dia = QComboBox()
        self.combo_dia.addItem("— sem dia fixo", None)
        for i, rot in enumerate(_DIAS_ROTULOS):
            self.combo_dia.addItem(f"toda {rot}", i)
        if dia_semana is not None:
            self.combo_dia.setCurrentIndex(int(dia_semana) + 1)
        self.combo_dia.setToolTip(
            "Campanha com dia fixo: o Início avisa no dia e a validade "
            "“ATÉ dd/mm” é sugerida sozinha (RG-24)")

        btn_capa = QPushButton(" Escolher imagem…")
        btn_capa.clicked.connect(self._escolher_capa)
        self._capa_lbl = QLabel("(opcional — sem capa, vale a miniatura "
                                "do projeto mais recente)")
        self._capa_lbl.setProperty("papel", "legenda")
        linha_capa = QHBoxLayout()
        linha_capa.addWidget(btn_capa)
        linha_capa.addWidget(self._capa_lbl, 1)
        caixa_capa = QWidget()
        caixa_capa.setLayout(linha_capa)

        form = QFormLayout()
        form.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapLongRows)
        form.addRow("Nome", self.campo_nome)
        form.addRow("Cor", caixa_cores)
        form.addRow("Dia da campanha", self.combo_dia)
        form.addRow("Capa", caixa_capa)

        criar = QPushButton(titulo)
        criar.setProperty("tipo", "primario")
        criar.clicked.connect(self._confirmar)
        cancelar = QPushButton("Cancelar")
        cancelar.clicked.connect(self.reject)
        rodape = QHBoxLayout()
        rodape.addStretch(1)
        rodape.addWidget(cancelar)
        rodape.addWidget(criar)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(t.ESP_4, t.ESP_4, t.ESP_4, t.ESP_4)
        lay.setSpacing(t.ESP_2)
        lay.addLayout(form)
        lay.addLayout(rodape)
        self.setMinimumWidth(520)

        from app.qt.design.polimento import ordenar_tab
        ordenar_tab(self)

    def _nome_mudou(self, texto: str) -> None:
        if not self._cor_manual and texto.strip():
            self._escolher_cor(cor_para_nome(texto), manual=False)

    def _escolher_cor(self, cor: str, manual: bool = True) -> None:
        self._cor = cor
        if manual:
            self._cor_manual = True
        for b, c in zip(self._botoes_cor, PALETA_EVENTOS):
            b.setChecked(c.lower() == cor.lower())

    def _escolher_capa(self) -> None:
        caminho, _ = QFileDialog.getOpenFileName(
            self, "Capa do evento", "",
            "Imagens (*.png *.jpg *.jpeg *.webp)")
        if caminho:
            self._capa = caminho
            from pathlib import Path
            self._capa_lbl.setText(Path(caminho).name)

    def _confirmar(self) -> None:
        if not self.campo_nome.text().strip():
            from app.qt.design.toast import mostrar_toast
            mostrar_toast(self, "Dê um nome ao evento.", tipo="erro")
            return
        self.accept()

    def valores(self) -> tuple[str, str, int | None, str | None]:
        return (self.campo_nome.text().strip(), self._cor,
                self.combo_dia.currentData(), self._capa)

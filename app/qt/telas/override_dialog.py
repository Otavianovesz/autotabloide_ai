"""
Override por slot (F7.3, Etapa B do Bloco E) — o modal da Mesa
==============================================================
Editar UMA célula (nome/preço/foto/arranjo) sem tocar no item da estante.
Campo vazio = herda do item (o placeholder mostra o valor herdado).
Precedência da visão §3.1: override do slot > item da estante > banco.
"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.qt.design import tokens as t
from app.rendering.arranjo import ModoArranjo

_ARRANJOS = [("(do item)", ""), ("Leque", ModoArranjo.LEQUE.value),
             ("Lado a lado", ModoArranjo.LADO_A_LADO.value),
             ("Grade", ModoArranjo.GRADE.value)]


class OverrideDialog(QDialog):
    """Devolve em ``valores()`` só os campos preenchidos (vazio = herda)."""

    def __init__(self, item, atual: dict | None = None, parent=None):
        super().__init__(parent)
        atual = atual or {}
        self.setWindowTitle("Conteúdo desta célula (override)")
        self.setMinimumWidth(420)

        aviso = QLabel("Só esta célula muda — o item da estante e o banco "
                       "ficam como estão. Campo vazio herda do item.")
        aviso.setWordWrap(True)
        aviso.setProperty("papel", "legenda")

        self.campo_nome = QLineEdit(atual.get("nome") or "")
        self.campo_nome.setPlaceholderText(item.nome)
        self.campo_preco = QLineEdit(atual.get("preco") or "")
        self.campo_preco.setPlaceholderText(item.preco or "—")

        self._imagem: str | None = atual.get("imagem") or None
        self._rotulo_img = QLabel()
        self._rotulo_img.setProperty("papel", "legenda")
        btn_trocar = QPushButton("Trocar foto…")
        btn_trocar.clicked.connect(self._escolher_imagem)
        btn_limpar = QPushButton("Usar a do item")
        btn_limpar.clicked.connect(self._limpar_imagem)
        linha_img = QHBoxLayout()
        linha_img.setSpacing(t.ESP_1)
        linha_img.addWidget(self._rotulo_img, 1)
        linha_img.addWidget(btn_trocar)
        linha_img.addWidget(btn_limpar)
        caixa_img = QWidget()
        caixa_img.setLayout(linha_img)

        # R-037 (Fase 5): enquadramento da foto DENTRO desta célula (pan/zoom).
        enq = atual.get("enquadramento") or {}
        self.campo_zoom = QDoubleSpinBox()
        self.campo_zoom.setRange(1.0, 4.0)
        self.campo_zoom.setSingleStep(0.1)
        self.campo_zoom.setValue(float(enq.get("zoom", 1.0)))
        self.campo_zoom.setToolTip("Aproxima a foto dentro do slot (1,0 = inteira)")
        self.foco_x = QDoubleSpinBox()
        self.foco_x.setRange(0.0, 1.0)
        self.foco_x.setSingleStep(0.05)
        self.foco_x.setValue(float(enq.get("foco_x", 0.5)))
        self.foco_y = QDoubleSpinBox()
        self.foco_y.setRange(0.0, 1.0)
        self.foco_y.setSingleStep(0.05)
        self.foco_y.setValue(float(enq.get("foco_y", 0.5)))
        linha_foco = QHBoxLayout()
        linha_foco.setSpacing(t.ESP_1)
        linha_foco.addWidget(QLabel("X")); linha_foco.addWidget(self.foco_x, 1)
        linha_foco.addWidget(QLabel("Y")); linha_foco.addWidget(self.foco_y, 1)
        caixa_foco = QWidget()
        caixa_foco.setLayout(linha_foco)

        self.campo_arranjo = QComboBox()
        for rotulo, _v in _ARRANJOS:
            self.campo_arranjo.addItem(rotulo)
        valores_arr = [v for _r, v in _ARRANJOS]
        if atual.get("arranjo") in valores_arr:
            self.campo_arranjo.setCurrentIndex(
                valores_arr.index(atual["arranjo"]))
        self.campo_arranjo.setToolTip(
            "Como as fotos se dispõem quando o item tem mais de uma (F4.5)")

        form = QFormLayout()
        form.setVerticalSpacing(t.ESP_2)
        form.addRow("Nome nesta célula", self.campo_nome)
        form.addRow("Preço nesta célula", self.campo_preco)
        form.addRow("Foto nesta célula", caixa_img)
        form.addRow("Aproximar (zoom)", self.campo_zoom)
        form.addRow("Enquadrar (foco)", caixa_foco)
        form.addRow("Arranjo das fotos", self.campo_arranjo)

        botoes = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok
                                  | QDialogButtonBox.StandardButton.Cancel)
        botoes.button(QDialogButtonBox.StandardButton.Ok).setText("Aplicar")
        botoes.button(QDialogButtonBox.StandardButton.Cancel).setText("Cancelar")
        botoes.accepted.connect(self.accept)
        botoes.rejected.connect(self.reject)

        raiz = QVBoxLayout(self)
        raiz.setSpacing(t.ESP_2)
        raiz.addWidget(aviso)
        raiz.addLayout(form)
        raiz.addWidget(botoes)
        self._atualizar_rotulo_img()

    def _escolher_imagem(self) -> None:
        caminho, _ = QFileDialog.getOpenFileName(
            self, "Foto só desta célula", "",
            "Imagens (*.png *.jpg *.jpeg *.webp)")
        if caminho:
            self._imagem = caminho
            self._atualizar_rotulo_img()

    def _limpar_imagem(self) -> None:
        self._imagem = None
        self._atualizar_rotulo_img()

    def _atualizar_rotulo_img(self) -> None:
        self._rotulo_img.setText(
            Path(self._imagem).name if self._imagem else "(a do item)")

    def valores(self) -> dict:
        """Só o que foi preenchido — dict vazio = sem override (restaura)."""
        ov: dict = {}
        if self.campo_nome.text().strip():
            ov["nome"] = self.campo_nome.text().strip()
        if self.campo_preco.text().strip():
            ov["preco"] = self.campo_preco.text().strip()
        if self._imagem:
            ov["imagem"] = self._imagem
        arranjo = _ARRANJOS[self.campo_arranjo.currentIndex()][1]
        if arranjo:
            ov["arranjo"] = arranjo
        # enquadramento só entra se saiu do padrão (zoom 1.0, foco centralizado)
        z, fx, fy = (round(self.campo_zoom.value(), 3),
                     round(self.foco_x.value(), 3), round(self.foco_y.value(), 3))
        if z != 1.0 or fx != 0.5 or fy != 0.5:
            ov["enquadramento"] = {"zoom": z, "foco_x": fx, "foco_y": fy}
        return ov

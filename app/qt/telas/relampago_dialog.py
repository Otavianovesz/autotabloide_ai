"""
Opções do cartaz-relâmpago / kit ponta-de-gôndola (polimento F11)
=================================================================
O serviço (R-110/R-113/R-114) sempre aceitou QR e nº de etiquetas — mas nenhum
widget os oferecia. Este diálogo pequeno coleta as opções ANTES do PDF:

  * nº de etiquetas do kit (só no kit);
  * QR opcional (R-114 — DESLIGADO por padrão, decisão travada): link do
    encarte/catálogo, gerado localmente.

O relâmpago segue sempre RASCUNHO (não há projeto aprovado por trás).
"""

from __future__ import annotations

from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLabel,
    QLineEdit,
    QSpinBox,
    QVBoxLayout,
)

from app.qt.design import tokens as t


class RelampagoDialog(QDialog):
    """Opções do cartaz-relâmpago (ou do kit) — 1 clique, poucas escolhas.

    Auditoria do polimento: o acervo só guarda UM preço (o atual) — o cartaz
    saía sempre sem o "de" riscado e sem o −%. Os campos de/por entram aqui:
    o "por" vem preenchido do produto; o "de" (o preço de antes) é do dono.
    """

    def __init__(self, nome_produto: str, *, kit: bool = False,
                 preco_por: str | None = None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Kit ponta-de-gôndola" if kit
                            else "Cartaz-relâmpago")
        self._kit = kit

        raiz = QVBoxLayout(self)
        raiz.setContentsMargins(t.ESP_4, t.ESP_4, t.ESP_4, t.ESP_4)
        raiz.setSpacing(t.ESP_2)

        titulo = QLabel("Kit ponta-de-gôndola" if kit else "Cartaz-relâmpago")
        titulo.setProperty("papel", "titulo")
        raiz.addWidget(titulo)
        alvo = QLabel(f"“{nome_produto}” — do balcão ao PDF num clique.")
        alvo.setProperty("papel", "legenda")
        alvo.setWordWrap(True)
        raiz.addWidget(alvo)

        form = QFormLayout()
        form.setVerticalSpacing(t.ESP_2)

        self.preco_por = QLineEdit(preco_por or "")
        self.preco_por.setPlaceholderText("ex.: 9,99 — o preço da oferta")
        self.preco_por.setToolTip("O preço grande do cartaz (vem do acervo; "
                                  "ajuste se mudou)")
        form.addRow("Preço “por”", self.preco_por)
        self.preco_de = QLineEdit()
        self.preco_de.setPlaceholderText("ex.: 12,99 — o preço de antes")
        self.preco_de.setToolTip("Com o “de”, o cartaz mostra o riscado e o "
                                 "desconto CALCULADO — sem ele, sai só o “por” "
                                 "(o pré-voo avisa)")
        form.addRow("Preço “de”", self.preco_de)

        self.etiquetas = QSpinBox()
        self.etiquetas.setRange(1, 20)
        self.etiquetas.setValue(2)
        self.etiquetas.setToolTip(
            "Quantas etiquetas de prateleira saem junto do cartaz "
            "(mesmo preço e validade — uma fonte de verdade)")
        if kit:
            form.addRow("Etiquetas", self.etiquetas)

        self.com_qr = QCheckBox("Incluir QR (link do encarte)")
        self.com_qr.setToolTip(
            "Um QR opcional no canto do cartaz — gerado no seu computador, "
            "sem serviço externo. Desligado por padrão.")
        self.qr_texto = QLineEdit()
        self.qr_texto.setPlaceholderText("https://… (o link que o QR abre)")
        self.qr_texto.setEnabled(False)
        self.com_qr.toggled.connect(self.qr_texto.setEnabled)
        form.addRow(self.com_qr)
        form.addRow("Link do QR", self.qr_texto)
        raiz.addLayout(form)

        aviso = QLabel("Sai com a marca RASCUNHO — não há projeto aprovado "
                       "por trás (confira o preço antes de pendurar).")
        aviso.setProperty("papel", "legenda")
        aviso.setWordWrap(True)
        raiz.addWidget(aviso)

        botoes = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok
                                  | QDialogButtonBox.StandardButton.Cancel)
        botoes.button(QDialogButtonBox.StandardButton.Ok).setText(
            "Gerar PDF")
        botoes.button(QDialogButtonBox.StandardButton.Cancel).setText(
            "Cancelar")
        botoes.accepted.connect(self.accept)
        botoes.rejected.connect(self.reject)
        raiz.addWidget(botoes)

    # --- resultado -----------------------------------------------------------

    def qr(self) -> str | None:
        """O texto do QR — None quando desligado ou vazio (o padrão)."""
        if not self.com_qr.isChecked():
            return None
        return self.qr_texto.text().strip() or None

    def n_etiquetas(self) -> int:
        return int(self.etiquetas.value()) if self._kit else 1

    def precos(self) -> tuple[str | None, str | None]:
        """(por, de) como digitados — vazio vira None."""
        return (self.preco_por.text().strip() or None,
                self.preco_de.text().strip() or None)

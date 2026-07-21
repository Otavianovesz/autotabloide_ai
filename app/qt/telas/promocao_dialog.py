"""Campo qtd+valor do multi-preço (R-070, Fase 7 — casca visual do Bloco B/D).

O dono monta a promoção por quantidade num formulário — sem digitar o texto na
mão: escolhe o formato ("N por R$X" ou "Leve N pague M"), preenche os números, e
a prévia mostra exatamente o que vai desenhar na região de preço. Reusa
`compor_multi_preco`/`compor_leve_pague` (a lógica mora no modelo, testável).
"""

from __future__ import annotations

from PySide6.QtWidgets import (
    QComboBox, QDialog, QDialogButtonBox, QFormLayout, QLabel, QLineEdit,
    QSpinBox, QVBoxLayout,
)

from app.qt.telas.colagem import compor_leve_pague, compor_multi_preco


class PromocaoDialog(QDialog):
    """Devolve o texto do multi-preço em ``self.resultado`` (None = cancelou ou
    entrada inválida). "Sem promoção" limpa o multi-preço do item."""

    def __init__(self, texto_atual: str | None = None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Promoção por quantidade")
        self.resultado: str | None = None
        self._limpar = False

        self.formato = QComboBox()
        self.formato.addItems(["N por R$ X", "Leve N pague M"])
        self.qtd = QSpinBox()
        self.qtd.setRange(1, 99)
        self.qtd.setValue(3)
        self.valor = QLineEdit()
        self.valor.setPlaceholderText("ex.: 10,00")
        self.pague = QSpinBox()
        self.pague.setRange(1, 99)
        self.pague.setValue(2)

        self._previa = QLabel("")
        self._previa.setProperty("papel", "legenda")

        form = QFormLayout()
        form.addRow("Formato:", self.formato)
        self._l_qtd = QLabel("Quantidade (leve):")
        form.addRow(self._l_qtd, self.qtd)
        self._l_valor = QLabel("Valor total (R$):")
        form.addRow(self._l_valor, self.valor)
        self._l_pague = QLabel("Pague:")
        form.addRow(self._l_pague, self.pague)

        botoes = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok
                                  | QDialogButtonBox.StandardButton.Cancel)
        # 3ª via: tirar a promoção do item (volta ao preço normal)
        self._btn_limpar = botoes.addButton("Sem promoção",
                                            QDialogButtonBox.ButtonRole.ResetRole)
        self._btn_limpar.clicked.connect(self._sem_promocao)
        botoes.accepted.connect(self._confirmar)
        botoes.rejected.connect(self.reject)

        raiz = QVBoxLayout(self)
        raiz.addLayout(form)
        raiz.addWidget(self._previa)
        raiz.addWidget(botoes)

        self._preencher_de(texto_atual)     # editar: abre com os valores atuais
        self.formato.currentIndexChanged.connect(self._atualizar)
        self.qtd.valueChanged.connect(self._atualizar)
        self.valor.textChanged.connect(self._atualizar)
        self.pague.valueChanged.connect(self._atualizar)
        self._atualizar()

    def _preencher_de(self, texto: str | None) -> None:
        """Se já havia promoção, abre com os campos preenchidos (edição)."""
        from app.qt.telas.colagem import _RE_LEVE, parse_multi_preco
        mp = parse_multi_preco(texto or "")
        if mp is None:
            return
        if mp.valor is not None:                 # "N por R$ X"
            self.formato.setCurrentIndex(0)
            self.qtd.setValue(mp.quantidade)
            self.valor.setText(mp.valor)
        else:                                    # "Leve N pague M"
            m = _RE_LEVE.search(texto or "")
            self.formato.setCurrentIndex(1)
            self.qtd.setValue(mp.quantidade)
            if m:
                self.pague.setValue(int(m.group(2)))

    def _texto_atual(self) -> str | None:
        """Compõe o texto do formato escolhido (ou None se inválido)."""
        if self.formato.currentIndex() == 0:
            return compor_multi_preco(self.qtd.value(), self.valor.text())
        return compor_leve_pague(self.qtd.value(), self.pague.value())

    def _atualizar(self, *_):
        leve_pague = self.formato.currentIndex() == 1
        self._l_valor.setVisible(not leve_pague)
        self.valor.setVisible(not leve_pague)
        self._l_pague.setVisible(leve_pague)
        self.pague.setVisible(leve_pague)
        self._l_qtd.setText("Leve:" if leve_pague else "Quantidade:")
        texto = self._texto_atual()
        self._previa.setText(f"Vai aparecer: “{texto}”" if texto
                             else "Preencha os campos (ex.: 3 por R$ 10,00).")

    def _sem_promocao(self):
        self._limpar = True
        self.resultado = None
        self.accept()

    def _confirmar(self):
        texto = self._texto_atual()
        if texto is None:            # I2: não confirma promoção inválida em silêncio
            self._previa.setText("Promoção inválida — confira os números.")
            return
        self.resultado = texto
        self.accept()

    @property
    def limpar(self) -> bool:
        return self._limpar

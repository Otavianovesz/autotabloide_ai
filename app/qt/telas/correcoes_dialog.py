"""
Correções aprendidas (OS F11.5 #43/#53/#91 — R-088)
===================================================
A lista REAL do que o banco aprendeu com os "Aceitar" do dono: cada alias diz
"quando a tabela escrever X, é o produto Y". Aqui dá para VER e REVERTER
(apagar o alias) — na próxima importação aquele texto volta ao amarelo para
o humano decidir. (A "galeria" de antes era um print estático; isto lê o
banco de verdade.)
"""

from __future__ import annotations

from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
)

from app.qt.design import tokens as t
from app.qt.design.componentes import EstadoVazio
from app.qt.telas import servico


class CorrecoesDialog(QDialog):
    """Tabela alias → produto, com reverter por linha (direto no banco)."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Correções aprendidas")
        self.resize(640, 420)
        raiz = QVBoxLayout(self)
        raiz.setContentsMargins(t.ESP_4, t.ESP_4, t.ESP_4, t.ESP_4)
        raiz.setSpacing(t.ESP_2)
        titulo = QLabel("Correções aprendidas")
        titulo.setProperty("papel", "titulo")
        raiz.addWidget(titulo)
        legenda = QLabel("Cada linha é um apelido que o banco aprendeu quando "
                         "você clicou em “Aceitar”: a tabela escreve de um "
                         "jeito, o produto é outro. Reverter apaga o apelido — "
                         "na próxima importação aquele texto volta a ser "
                         "conferido por você.")
        legenda.setProperty("papel", "legenda")
        legenda.setWordWrap(True)
        raiz.addWidget(legenda)

        self.tab = QTableWidget(0, 3)
        self.tab.setHorizontalHeaderLabels(
            ["Quando a tabela escrever…", "…é o produto", ""])
        self.tab.verticalHeader().setVisible(False)
        self.tab.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        from PySide6.QtWidgets import QHeaderView
        cab = self.tab.horizontalHeader()
        cab.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        cab.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self._vazio = EstadoVazio(
            "check_circulo", "Nada aprendido ainda",
            "Aceite um amarelo na conciliação e a correção aparece aqui.")
        raiz.addWidget(self.tab, 1)
        raiz.addWidget(self._vazio, 1)

        botoes = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        botoes.button(QDialogButtonBox.StandardButton.Close).setText("Fechar")
        botoes.rejected.connect(self.reject)
        botoes.accepted.connect(self.accept)
        raiz.addWidget(botoes)
        self.recarregar()

    def recarregar(self) -> None:
        try:
            self.correcoes = servico.correcoes_aprendidas()
        except Exception:
            self.correcoes = []
        self.tab.setRowCount(len(self.correcoes))
        for i, c in enumerate(self.correcoes):
            self.tab.setItem(i, 0, QTableWidgetItem(c["alias"]))
            self.tab.setItem(i, 1, QTableWidgetItem(c["produto"]))
            btn = QPushButton("Reverter")
            btn.setToolTip("Apagar este apelido — volta a ser conferido")
            btn.clicked.connect(
                lambda _=False, aid=c["id"]: self._reverter(aid))
            caixa = QHBoxLayout()
            from PySide6.QtWidgets import QWidget
            w = QWidget()
            caixa.setContentsMargins(2, 2, 2, 2)
            caixa.addWidget(btn)
            w.setLayout(caixa)
            self.tab.setCellWidget(i, 2, w)
        tem = bool(self.correcoes)
        self.tab.setVisible(tem)
        self._vazio.setVisible(not tem)

    def _reverter(self, alias_id: int) -> None:
        if servico.esquecer_correcao(alias_id):
            self.recarregar()

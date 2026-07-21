"""
Importar do banco — busca com multi-seleção acumulativa (Mesa/Fábrica)
======================================================================
O fluxo que o Otaviano pediu: pesquisa "Coca", clica, pesquisa outro termo
**sem perder a seleção** — a cesta acumula; "Importar" traz tudo de uma vez.
"""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
)

from app.qt.design import tokens as t
from app.qt.design.icones import icone
from app.qt.telas import servico

_COR = {"VERDE": t.SUCESSO, "AMARELO": t.ALERTA, "VERMELHO": t.PERIGO}


class ImportarBancoDialog(QDialog):
    """Devolve os produtos escolhidos em ``selecionados`` (linhas planas)."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Importar do banco")
        self.selecionados: list[dict] = []
        self._cesta: dict[int, dict] = {}     # id -> linha (acumula entre buscas)

        titulo = QLabel("Importar do banco")
        titulo.setProperty("papel", "titulo")
        dica = QLabel("Pesquise e clique para adicionar — a cesta acumula entre "
                      "buscas. Duplo-clique remove da cesta.")
        dica.setProperty("papel", "legenda")

        self.busca = QLineEdit()
        self.busca.setPlaceholderText("Buscar produto, marca…")
        self.busca.textChanged.connect(self._rebuscar)

        self.resultados = QListWidget()
        self.resultados.itemClicked.connect(self._adicionar)
        rotulo_res = QLabel("RESULTADOS")
        rotulo_res.setProperty("papel", "secao")

        self.cesta = QListWidget()
        self.cesta.itemDoubleClicked.connect(self._remover)
        self._rotulo_cesta = QLabel("CESTA (0)")
        self._rotulo_cesta.setProperty("papel", "secao")

        cancelar = QPushButton("Cancelar")
        cancelar.clicked.connect(self.reject)
        self.importar = QPushButton(" Importar")
        self.importar.setIcon(icone("caixa", cor=t.ACENTO_TEXTO, tamanho=15))
        self.importar.setProperty("tipo", "primario")
        self.importar.setEnabled(False)
        self.importar.clicked.connect(self._concluir)
        botoes = QHBoxLayout()
        botoes.addStretch(1)
        botoes.addWidget(cancelar)
        botoes.addWidget(self.importar)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(t.ESP_4, t.ESP_4, t.ESP_4, t.ESP_4)
        lay.setSpacing(t.ESP_2)
        lay.addWidget(titulo)
        lay.addWidget(dica)
        lay.addWidget(self.busca)
        lay.addWidget(rotulo_res)
        lay.addWidget(self.resultados, 3)
        lay.addWidget(self._rotulo_cesta)
        lay.addWidget(self.cesta, 2)
        lay.addLayout(botoes)
        self.resize(520, 560)
        self._rebuscar()

    # --- busca / cesta ----------------------------------------------------------

    def _rebuscar(self) -> None:
        self.resultados.clear()
        for d in servico.listar_catalogo(limite=50, texto=self.busca.text().strip()):
            preco = f"  ·  R$ {d['preco']}" if d["preco"] else ""
            ja = "  ✓" if d["id"] in self._cesta else ""
            item = QListWidgetItem(f"{d['nome']}{preco}{ja}")
            item.setData(Qt.ItemDataRole.UserRole, d)
            self.resultados.addItem(item)

    def _adicionar(self, item: QListWidgetItem) -> None:
        d = item.data(Qt.ItemDataRole.UserRole)
        if d["id"] not in self._cesta:
            self._cesta[d["id"]] = d
            self._atualizar_cesta()
            self._rebuscar()

    def _remover(self, item: QListWidgetItem) -> None:
        pid = item.data(Qt.ItemDataRole.UserRole)["id"]
        self._cesta.pop(pid, None)
        self._atualizar_cesta()
        self._rebuscar()

    def _atualizar_cesta(self) -> None:
        self.cesta.clear()
        for d in self._cesta.values():
            item = QListWidgetItem(d["nome"])
            item.setData(Qt.ItemDataRole.UserRole, d)
            self.cesta.addItem(item)
        self._rotulo_cesta.setText(f"CESTA ({len(self._cesta)})")
        self.importar.setEnabled(bool(self._cesta))

    def _concluir(self) -> None:
        self.selecionados = list(self._cesta.values())
        self.accept()

"""
Montar conjunto do acervo — a CESTA (RODADA-125 Onda 3b, 03/08/2026)
====================================================================
O pedido do dono, na letra: "preciso ter liberdade pra caçar esses
dois itens já existentes e colocar ali". Busca à esquerda, a CESTA à
direita: duplo clique joga o produto na cesta, ◀ ▶ reordena (a ordem
é a do desenho), o rádio diz se são SABORES (leque) ou PRODUTOS
DIFERENTES (vitrine/composto), o nome da célula é editável. Espaço
amplia a foto (a lupa). Devolve ``escolha()``.
"""

from __future__ import annotations

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QIcon, QKeySequence, QPixmap, QShortcut
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QRadioButton,
    QVBoxLayout,
)

from app.qt.design import tokens as t
from app.qt.telas import servico


class MontarConjuntoDialog(QDialog):
    """``escolha() -> (produto_ids, tipo, nome_base) | None``."""

    def __init__(self, descricao_linha: str = "", parent=None,
                 sugestao_nome: str = ""):
        super().__init__(parent)
        self.setWindowTitle("Montar conjunto do acervo")
        self.resize(760, 520)

        info = QLabel(
            "Cace no acervo os produtos que ESTA linha é — duplo "
            "clique joga na cesta. A célula sai com as fotos deles; "
            "nada é recriado nem pesquisado de novo.")
        info.setWordWrap(True)
        info.setProperty("papel", "legenda")

        # --- esquerda: a busca ------------------------------------------------
        self.busca = QLineEdit(descricao_linha.split("·")[0][:40])
        self.busca.setPlaceholderText("Digite parte do nome…")
        self.busca.textChanged.connect(self._rebuscar)
        self.resultados = QListWidget()
        self.resultados.setIconSize(QSize(40, 40))
        self.resultados.itemDoubleClicked.connect(
            lambda _it: self._adicionar())
        b_add = QPushButton("Adicionar à cesta ▶")
        b_add.clicked.connect(self._adicionar)
        esq = QVBoxLayout()
        esq.addWidget(QLabel("ACERVO"))
        esq.addWidget(self.busca)
        esq.addWidget(self.resultados, 1)
        esq.addWidget(b_add)

        # --- direita: a cesta -------------------------------------------------
        self.cesta = QListWidget()
        self.cesta.setIconSize(QSize(40, 40))
        subir = QPushButton("◀ Antes")
        subir.clicked.connect(lambda: self._mover(-1))
        descer = QPushButton("Depois ▶")
        descer.clicked.connect(lambda: self._mover(+1))
        tirar = QPushButton("Tirar")
        tirar.clicked.connect(self._tirar)
        ordem = QHBoxLayout()
        ordem.addWidget(subir)
        ordem.addWidget(descer)
        ordem.addWidget(tirar)
        ordem.addStretch(1)
        dire = QVBoxLayout()
        self._rotulo_cesta = QLabel("A CESTA (0)")
        dire.addWidget(self._rotulo_cesta)
        dire.addWidget(self.cesta, 1)
        dire.addLayout(ordem)

        meio = QHBoxLayout()
        meio.setSpacing(t.ESP_3)
        meio.addLayout(esq, 1)
        meio.addLayout(dire, 1)

        # --- o tipo + o nome da célula ---------------------------------------
        self.rb_sabores = QRadioButton(
            "São SABORES do mesmo produto (leque)")
        self.rb_diferentes = QRadioButton(
            "São produtos DIFERENTES (lado a lado)")
        self.rb_diferentes.setChecked(True)
        self.nome_base = QLineEdit(sugestao_nome)
        self.nome_base.setPlaceholderText(
            "Nome na célula (ex.: Biscoito Bulnez e Adoralle · 270 g)")

        botoes = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok
                                  | QDialogButtonBox.StandardButton.Cancel)
        self._ok = botoes.button(QDialogButtonBox.StandardButton.Ok)
        self._ok.setText("Usar estes")
        self._ok.setEnabled(False)
        botoes.button(
            QDialogButtonBox.StandardButton.Cancel).setText("Cancelar")
        botoes.accepted.connect(self.accept)
        botoes.rejected.connect(self.reject)

        raiz = QVBoxLayout(self)
        raiz.setContentsMargins(t.ESP_4, t.ESP_4, t.ESP_4, t.ESP_4)
        raiz.setSpacing(t.ESP_2)
        raiz.addWidget(info)
        raiz.addLayout(meio, 1)
        raiz.addWidget(self.rb_sabores)
        raiz.addWidget(self.rb_diferentes)
        raiz.addWidget(QLabel("Nome na célula:"))
        raiz.addWidget(self.nome_base)
        raiz.addWidget(botoes)

        # a LUPA nas duas listas (Espaço — consistência com a curadoria)
        for lista in (self.resultados, self.cesta):
            atalho = QShortcut(QKeySequence(Qt.Key.Key_Space), lista,
                               lambda li=lista: self._ampliar(li))
            atalho.setContext(Qt.ShortcutContext.WidgetShortcut)

        from app.qt.design.polimento import ordenar_tab
        ordenar_tab(self)
        self._rebuscar()
        self.busca.setFocus()

    def showEvent(self, ev) -> None:  # noqa: N802 (Qt)
        super().showEvent(ev)
        from app.qt.design.polimento import clampar_a_tela
        clampar_a_tela(self)

    # --- busca/cesta ----------------------------------------------------------

    def _rebuscar(self) -> None:
        self.resultados.clear()
        try:
            achados = servico.buscar_produtos_para_vinculo(
                self.busca.text())
        except Exception:
            achados = []
        na_cesta = set(self._ids())
        for a in achados:
            it = QListWidgetItem(a["nome"])
            it.setData(Qt.ItemDataRole.UserRole, a["produto_id"])
            it.setData(Qt.ItemDataRole.UserRole + 1, a.get("imagem"))
            if a["produto_id"] in na_cesta:
                it.setText(f'{a["nome"]}   ✓ na cesta')
            if a.get("imagem"):
                pix = QPixmap(a["imagem"])
                if not pix.isNull():
                    it.setIcon(QIcon(pix))
            self.resultados.addItem(it)
        if self.resultados.count():
            self.resultados.setCurrentRow(0)

    def _adicionar(self) -> None:
        it = self.resultados.currentItem()
        if it is None:
            return
        pid = it.data(Qt.ItemDataRole.UserRole)
        if pid in self._ids():
            return                      # já na cesta — não duplica
        novo = QListWidgetItem(it.text().replace("   ✓ na cesta", ""))
        novo.setData(Qt.ItemDataRole.UserRole, pid)
        novo.setData(Qt.ItemDataRole.UserRole + 1,
                     it.data(Qt.ItemDataRole.UserRole + 1))
        novo.setIcon(it.icon())
        self.cesta.addItem(novo)
        self._atualizou_cesta()

    def _tirar(self) -> None:
        linha = self.cesta.currentRow()
        if linha >= 0:
            self.cesta.takeItem(linha)
            self._atualizou_cesta()

    def _mover(self, delta: int) -> None:
        linha = self.cesta.currentRow()
        nova = linha + delta
        if linha < 0 or not (0 <= nova < self.cesta.count()):
            return
        it = self.cesta.takeItem(linha)
        self.cesta.insertItem(nova, it)
        self.cesta.setCurrentRow(nova)

    def _atualizou_cesta(self) -> None:
        n = self.cesta.count()
        self._rotulo_cesta.setText(f"A CESTA ({n})")
        self._ok.setEnabled(n >= 2)
        self._rebuscar()                 # o "✓ na cesta" acompanha

    def _ampliar(self, lista: QListWidget) -> None:
        it = lista.currentItem()
        if it is None:
            return
        from app.qt.design.lupa import ampliar_imagem
        ampliar_imagem(self, it.data(Qt.ItemDataRole.UserRole + 1))

    def _ids(self) -> list[int]:
        return [self.cesta.item(i).data(Qt.ItemDataRole.UserRole)
                for i in range(self.cesta.count())]

    # --- saída ---------------------------------------------------------------

    def escolha(self) -> tuple[list[int], str, str] | None:
        if self.cesta.count() < 2:
            return None
        tipo = "sabores" if self.rb_sabores.isChecked() else "diferentes"
        return self._ids(), tipo, self.nome_base.text().strip()

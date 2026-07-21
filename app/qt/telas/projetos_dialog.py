"""
Diálogos de projeto salvo — salvar (nome + evento) e abrir (lista com ações)
============================================================================
O "evento" é a pasta temática do Dashboard (ex.: "Terça do Pão"); o combo
sugere os eventos que já existem. Abrir lista tudo, com duplicar/excluir.
"""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QFormLayout,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
)

from app.core import projetos
from app.qt.design import tokens as t
from app.qt.design.componentes import EstadoVazio
from app.qt.design.icones import icone

_ICONE_TIPO = {"TABLOIDE": "grade", "CARTAZ": "impressora"}


class SalvarProjetoDialog(QDialog):
    def __init__(self, sugestao_nome: str = "", parent=None):
        super().__init__(parent)
        self.setWindowTitle("Salvar projeto")
        titulo = QLabel("Salvar projeto")
        titulo.setProperty("papel", "titulo")
        dica = QLabel("Os dados ficam congelados: reabrir mostra o projeto "
                      "exatamente como está agora.")
        dica.setProperty("papel", "legenda")
        dica.setWordWrap(True)

        self.nome = QLineEdit(sugestao_nome)
        self.nome.setPlaceholderText("ex.: Ofertas 08/07")
        self.evento = QComboBox()
        self.evento.setEditable(True)
        eventos = sorted({p["evento"] for p in projetos.listar_projetos()
                          if p["evento"]})
        self.evento.addItems([""] + eventos)
        self.evento.lineEdit().setPlaceholderText("ex.: Terça do Pão (opcional)")

        form = QFormLayout()
        form.setVerticalSpacing(t.ESP_2)
        form.addRow("Nome", self.nome)
        form.addRow("Evento", self.evento)

        cancelar = QPushButton("Cancelar")
        cancelar.clicked.connect(self.reject)
        salvar = QPushButton(" Salvar")
        salvar.setIcon(icone("salvar", cor=t.ACENTO_TEXTO, tamanho=16))
        salvar.setProperty("tipo", "primario")
        salvar.clicked.connect(self._confirmar)
        botoes = QHBoxLayout()
        botoes.addStretch(1)
        botoes.addWidget(cancelar)
        botoes.addWidget(salvar)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(t.ESP_4, t.ESP_4, t.ESP_4, t.ESP_4)
        lay.setSpacing(t.ESP_2)
        lay.addWidget(titulo)
        lay.addWidget(dica)
        lay.addLayout(form)
        lay.addLayout(botoes)
        self.resize(420, 200)

    def _confirmar(self) -> None:
        if self.nome.text().strip():
            self.accept()

    def valores(self) -> tuple[str, str]:
        return self.nome.text().strip(), self.evento.currentText().strip()


class AbrirProjetoDialog(QDialog):
    """Lista os projetos salvos; devolve o id escolhido em ``projeto_id``."""

    def __init__(self, tipo: str | None = None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Abrir projeto")
        self.projeto_id: int | None = None
        self._tipo = tipo

        titulo = QLabel("Abrir projeto")
        titulo.setProperty("papel", "titulo")
        self.lista = QListWidget()
        self.lista.itemDoubleClicked.connect(lambda _it: self._abrir())
        self.lista.itemSelectionChanged.connect(self._habilitar)

        excluir = QPushButton(" Excluir")
        excluir.setIcon(icone("lixeira", tamanho=15))
        excluir.setToolTip("Manda o projeto para a lixeira (reversível)")
        excluir.clicked.connect(self._excluir)
        duplicar = QPushButton(" Duplicar")
        duplicar.setIcon(icone("duplicar", tamanho=15))
        duplicar.setToolTip("Copiar um antigo para fazer o novo")
        duplicar.clicked.connect(self._duplicar)
        cancelar = QPushButton("Cancelar")
        cancelar.setToolTip("Fecha sem abrir nada")
        cancelar.clicked.connect(self.reject)
        self.abrir = QPushButton(" Abrir")
        self.abrir.setIcon(icone("abrir", cor=t.ACENTO_TEXTO, tamanho=15))
        self.abrir.setProperty("tipo", "primario")
        self.abrir.setEnabled(False)
        self.abrir.setToolTip("Reabre o projeto congelado, idêntico ao salvo")
        self.abrir.clicked.connect(self._abrir)

        botoes = QHBoxLayout()
        botoes.addWidget(excluir)
        botoes.addWidget(duplicar)
        botoes.addStretch(1)
        botoes.addWidget(cancelar)
        botoes.addWidget(self.abrir)

        # polimento: sem projetos salvos, um estado vazio com craft — nunca
        # um retângulo branco mudo (o padrão de todo o app)
        self._vazio = EstadoVazio(
            "cofre", "Nenhum projeto salvo ainda",
            "Salve um projeto na Mesa ou na Fábrica para reabri-lo aqui.")
        self._vazio.hide()

        lay = QVBoxLayout(self)
        lay.setContentsMargins(t.ESP_4, t.ESP_4, t.ESP_4, t.ESP_4)
        lay.setSpacing(t.ESP_2)
        lay.addWidget(titulo)
        lay.addWidget(self.lista, 1)
        lay.addWidget(self._vazio, 1)
        lay.addLayout(botoes)
        self.resize(520, 420)
        self._recarregar()

    def _recarregar(self) -> None:
        self.lista.clear()
        for p in projetos.listar_projetos():
            if self._tipo and p["tipo"] != self._tipo:
                continue
            evento = f"{p['evento']}  ·  " if p["evento"] else ""
            item = QListWidgetItem(
                icone(_ICONE_TIPO.get(p["tipo"], "grade"), tamanho=16),
                f"{evento}{p['nome']}   —   {p['tipo'].title()} · {p['criado_em']}")
            item.setData(Qt.ItemDataRole.UserRole, p["id"])
            self.lista.addItem(item)
        tem = self.lista.count() > 0
        self.lista.setVisible(tem)
        self._vazio.setVisible(not tem)
        self._habilitar()

    def _selecionado(self) -> int | None:
        sel = self.lista.selectedItems()
        return sel[0].data(Qt.ItemDataRole.UserRole) if sel else None

    def _habilitar(self) -> None:
        self.abrir.setEnabled(self._selecionado() is not None)

    def _abrir(self) -> None:
        pid = self._selecionado()
        if pid is not None:
            self.projeto_id = pid
            self.accept()

    def _duplicar(self) -> None:
        pid = self._selecionado()
        if pid is None:
            return
        nome, ok = QInputDialog.getText(self, "Duplicar projeto", "Nome do novo:")
        if ok and nome.strip():
            projetos.duplicar_projeto(pid, nome.strip())
            self._recarregar()

    def _excluir(self) -> None:
        pid = self._selecionado()
        if pid is None:
            return
        from app.qt.design.componentes import confirmar_destrutivo
        if confirmar_destrutivo(                  # passo 78: verbo no botão
                self, "Excluir projeto",
                "Este projeto será apagado. Não tem volta.",
                "Excluir projeto"):
            projetos.excluir_projeto(pid)
            self._recarregar()

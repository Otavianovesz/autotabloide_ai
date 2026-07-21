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

from pathlib import Path

from app.core import projetos
from app.qt.design import tokens as t
from app.qt.design.componentes import EstadoVazio
from app.qt.design.icones import icone
from app.qt.design.toast import mostrar_toast

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

        # R-136 (FASE 12): o projeto viaja num arquivo só (.atproj)
        self.btn_exp_atproj = QPushButton(" Levar (.atproj)")
        self.btn_exp_atproj.setIcon(icone("cofre", tamanho=15))
        self.btn_exp_atproj.setToolTip(
            "Empacota o projeto (dados + fotos + arte) num arquivo único "
            "para levar a outro PC")
        self.btn_exp_atproj.clicked.connect(self._exportar_atproj)
        btn_imp_atproj = QPushButton(" Trazer (.atproj)…")
        btn_imp_atproj.setIcon(icone("abrir", tamanho=15))
        btn_imp_atproj.setToolTip(
            "Traz um projeto empacotado de outro PC (com prévia)")
        btn_imp_atproj.clicked.connect(self._importar_atproj)

        botoes = QHBoxLayout()
        botoes.addWidget(excluir)
        botoes.addWidget(duplicar)
        botoes.addWidget(self.btn_exp_atproj)
        botoes.addWidget(btn_imp_atproj)
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
        if hasattr(self, "btn_exp_atproj"):
            self.btn_exp_atproj.setEnabled(self._selecionado() is not None)

    def _exportar_atproj(self) -> None:
        """R-136: o projeto selecionado vira um .atproj único."""
        pid = self._selecionado()
        if pid is None:
            return
        from PySide6.QtWidgets import QFileDialog

        from app.core.atproj import exportar_atproj
        destino, _ = QFileDialog.getSaveFileName(
            self, "Levar o projeto", "projeto.atproj",
            "Projeto AutoTabloide (*.atproj)")
        if not destino:
            return
        try:
            saida = exportar_atproj(pid, destino)
        except Exception as exc:
            mostrar_toast(self, f"Não deu para empacotar: {exc}",
                          tipo="erro")
            return
        mostrar_toast(self, f"Projeto empacotado em {Path(saida).name} — "
                            "leve este arquivo ao outro PC.",
                      tipo="sucesso")

    def _importar_atproj(self) -> None:
        """R-136: traz um .atproj com PRÉVIA antes de criar qualquer coisa."""
        from PySide6.QtWidgets import QFileDialog, QMessageBox

        from app.core.atproj import importar_atproj, ler_manifesto
        arquivo, _ = QFileDialog.getOpenFileName(
            self, "Trazer um projeto", "",
            "Projeto AutoTabloide (*.atproj)")
        if not arquivo:
            return
        m = ler_manifesto(arquivo)
        if m is None:
            mostrar_toast(self, "Este arquivo não é um projeto .atproj "
                                "válido.", tipo="erro")
            return
        resp = QMessageBox.question(
            self, "Trazer este projeto?",
            f"“{m.get('nome')}”"
            + (f" · evento {m['evento']}" if m.get("evento") else "")
            + f"\n{m.get('itens', 0)} item(ns) · "
              f"{m.get('paginas', 0)} página(s) · salvo em "
              f"{m.get('criado_em', '?')}\n\nCriar uma CÓPIA dele neste PC?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if resp != QMessageBox.StandardButton.Yes:
            return
        try:
            novo = importar_atproj(arquivo)
        except Exception as exc:
            mostrar_toast(self, f"Não deu para trazer: {exc}", tipo="erro")
            return
        self._recarregar()
        for i in range(self.lista.count()):
            if self.lista.item(i).data(Qt.ItemDataRole.UserRole) == novo:
                self.lista.setCurrentRow(i)
                break
        mostrar_toast(self, f"“{m.get('nome')}” chegou — abra quando "
                            "quiser.", tipo="sucesso")

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

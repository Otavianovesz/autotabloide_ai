"""
Linha do tempo de versões (FASE 2, passos 60-62)
================================================
Cada salvamento por cima guardou a versão anterior com miniatura. A ÚNICA
ação é "Abrir como novo projeto" — restaurar por cima é PROIBIDO (o
projeto vivo nunca é sobrescrito por versão). Versões são LOCAIS: não
viajam no pacote .atpkg (decisão do caderno, dita na tela).
"""

from __future__ import annotations

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
)

from app.core import projetos
from app.qt.design import tokens as t
from app.qt.design.componentes import EstadoVazio
from app.qt.design.icones import icone


class VersoesDialog(QDialog):
    """``novo_id`` fica preenchido quando uma versão vira projeto novo."""

    def __init__(self, projeto_id: int, nome_projeto: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Versões de “{nome_projeto}”")
        self._projeto_id = projeto_id
        self.novo_id: int | None = None

        titulo = QLabel(f"Versões de “{nome_projeto}”")
        titulo.setProperty("papel", "titulo")
        dica = QLabel("Cada salvamento guardou a versão anterior. Abrir uma "
                      "versão cria um PROJETO NOVO — nada é sobrescrito.\n"
                      "Versões são locais (não viajam no pacote .atpkg).")
        dica.setProperty("papel", "legenda")
        dica.setWordWrap(True)

        self.lista = QListWidget()
        self.lista.setViewMode(QListWidget.ViewMode.IconMode)
        self.lista.setMovement(QListWidget.Movement.Static)
        self.lista.setIconSize(QSize(140, 140))
        self.lista.setResizeMode(QListWidget.ResizeMode.Adjust)
        self.lista.setSpacing(t.ESP_2)
        versoes = projetos.listar_versoes(projeto_id)
        for v in versoes:
            item = QListWidgetItem(
                f"{v['quando']}\n{v['itens']} item(ns) · "
                f"{v['paginas']} página(s)")
            item.setData(Qt.ItemDataRole.UserRole, v["ts"])
            if v["miniatura"]:
                item.setIcon(QIcon(QPixmap(v["miniatura"]).scaled(
                    140, 140, Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation)))
            else:
                item.setIcon(icone("restaurar", tamanho=48))
            self.lista.addItem(item)
        vazio = EstadoVazio(
            "restaurar", "Nenhuma versão ainda",
            "Salve por cima deste projeto e a versão\nanterior aparece aqui.")
        vazio.setVisible(not versoes)
        self.lista.setVisible(bool(versoes))
        self.lista.itemSelectionChanged.connect(self._habilitar)
        self.lista.itemDoubleClicked.connect(lambda _it: self._abrir())

        self.btn_abrir = QPushButton(" Abrir como novo projeto")
        self.btn_abrir.setIcon(icone("duplicar", cor=t.ACENTO_TEXTO,
                                     tamanho=16))
        self.btn_abrir.setProperty("tipo", "primario")
        self.btn_abrir.setEnabled(False)
        self.btn_abrir.setToolTip("Clona a versão como projeto novo "
                                  "(“Nome (versão de DD/MM)”) — o projeto "
                                  "atual continua intocado")
        self.btn_abrir.clicked.connect(self._abrir)
        fechar = QPushButton("Fechar")
        fechar.clicked.connect(self.reject)
        rodape = QHBoxLayout()
        rodape.addStretch(1)
        rodape.addWidget(fechar)
        rodape.addWidget(self.btn_abrir)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(t.ESP_4, t.ESP_4, t.ESP_4, t.ESP_4)
        lay.setSpacing(t.ESP_2)
        lay.addWidget(titulo)
        lay.addWidget(dica)
        lay.addWidget(self.lista, 1)
        lay.addWidget(vazio, 1)
        lay.addLayout(rodape)
        self.resize(640, 480)

    def _habilitar(self) -> None:
        self.btn_abrir.setEnabled(bool(self.lista.selectedItems()))

    def _abrir(self) -> None:
        sel = self.lista.selectedItems()
        if not sel:
            return
        ts = sel[0].data(Qt.ItemDataRole.UserRole)
        self.novo_id = projetos.abrir_versao_como_novo(self._projeto_id, ts)
        if self.novo_id is None:
            from app.qt.design.toast import mostrar_toast
            mostrar_toast(self, "A versão não foi encontrada no disco.",
                          tipo="erro")
            return
        self.accept()

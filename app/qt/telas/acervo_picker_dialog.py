"""
Escolher foto DO ACERVO (polimento F10)
=======================================
A "aba Acervo" da curadoria: as fotos que JÁ estão na biblioteca (uma por
produto, a `atual.png`), em grade com nome — útil para sabores/variantes que
compartilham a foto. Devolve o CAMINHO escolhido; quem chama trata como
"arquivo" no fluxo de sempre (a foto é COPIADA para o produto — nunca
compartilha o mesmo arquivo entre produtos, I1).
"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QVBoxLayout,
)

from app.qt.design import tokens as t
from app.qt.design.componentes import EstadoVazio


def _fotos_do_acervo() -> list[tuple[str, str]]:
    """(nome do produto, caminho absoluto da atual) — só quem TEM foto."""
    from sqlalchemy import select

    from app.core.database import Database
    from app.core.models import Produto
    from app.core.paths import SystemRoot
    raiz = SystemRoot().biblioteca_imagens
    out: list[tuple[str, str]] = []
    db = Database().init()
    try:
        with db.Session() as s:
            for p in s.execute(select(Produto).where(
                    Produto.excluido_em.is_(None)).order_by(
                    Produto.nome_sanitizado)).scalars():
                if not p.caminho_imagem:
                    continue
                caminho = raiz / p.caminho_imagem
                if caminho.exists():
                    out.append((p.nome_sanitizado or "?", str(caminho)))
    except Exception:
        pass                                   # sem banco: lista vazia (I2 na UI)
    finally:
        db.engine.dispose()
    return out


class AcervoPickerDialog(QDialog):
    """Grade de fotos do acervo; devolve o caminho em ``self.caminho``."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Foto do acervo")
        self.caminho: str | None = None
        self._todas = _fotos_do_acervo()

        raiz = QVBoxLayout(self)
        raiz.setContentsMargins(t.ESP_4, t.ESP_4, t.ESP_4, t.ESP_4)
        raiz.setSpacing(t.ESP_2)
        titulo = QLabel("Escolher uma foto do acervo")
        titulo.setProperty("papel", "titulo")
        raiz.addWidget(titulo)

        self.busca = QLineEdit()
        self.busca.setPlaceholderText("Filtrar por nome do produto…")
        self.busca.textChanged.connect(self._filtrar)
        raiz.addWidget(self.busca)

        self.lista = QListWidget()
        self.lista.setViewMode(QListWidget.ViewMode.IconMode)
        self.lista.setMovement(QListWidget.Movement.Static)
        self.lista.setIconSize(QSize(96, 96))
        self.lista.setResizeMode(QListWidget.ResizeMode.Adjust)
        self.lista.setGridSize(QSize(120, 132))
        self.lista.setWordWrap(True)
        self.lista.itemDoubleClicked.connect(lambda _i: self._usar())
        raiz.addWidget(self.lista, 1)

        self._vazio = EstadoVazio(
            "caixa", "Nenhuma foto no acervo ainda",
            "As fotos dos produtos cadastrados aparecem aqui.")
        raiz.addWidget(self._vazio, 1)

        botoes = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok
                                  | QDialogButtonBox.StandardButton.Cancel)
        self._ok = botoes.button(QDialogButtonBox.StandardButton.Ok)
        self._ok.setText("Usar esta")
        self._ok.setEnabled(False)
        botoes.button(QDialogButtonBox.StandardButton.Cancel).setText(
            "Cancelar")
        botoes.accepted.connect(self._usar)
        botoes.rejected.connect(self.reject)
        raiz.addWidget(botoes)
        self.lista.itemSelectionChanged.connect(
            lambda: self._ok.setEnabled(bool(self.lista.selectedItems())))
        self.resize(560, 480)
        self._filtrar("")

    def _filtrar(self, texto: str) -> None:
        alvo = (texto or "").strip().lower()
        self.lista.clear()
        for nome, caminho in self._todas:
            if alvo and alvo not in nome.lower():
                continue
            item = QListWidgetItem(QIcon(QPixmap(caminho)), nome)
            item.setData(Qt.ItemDataRole.UserRole, caminho)
            item.setToolTip(nome)
            self.lista.addItem(item)
        tem = self.lista.count() > 0
        self.lista.setVisible(tem)
        self._vazio.setVisible(not tem)

    def _usar(self) -> None:
        sel = self.lista.selectedItems()
        if not sel:
            return
        caminho = sel[0].data(Qt.ItemDataRole.UserRole)
        if caminho and Path(caminho).exists():
            self.caminho = caminho
            self.accept()

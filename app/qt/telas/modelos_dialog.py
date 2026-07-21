"""Biblioteca de modelos de célula (R-048/R-044, Fase 5 — Bloco C).

Miniatura viva (composta pelo compositor, com conteúdo de exemplo) + nome.
Carimbar aplica o modelo no canvas; dá para salvar a seleção como modelo novo,
renomear e excluir.
"""

from __future__ import annotations

from decimal import Decimal

from PySide6.QtCore import QSize, Qt
from PySide6.QtWidgets import (
    QDialog, QHBoxLayout, QInputDialog, QListWidget, QListWidgetItem,
    QMessageBox, QPushButton, QVBoxLayout,
)

from app.rendering.compositor import DadosProduto, compor_pagina
from app.rendering.model import LayoutDef, Pagina, Slot
from app.rendering.modelos import (
    carimbar_modelo, carregar_modelo, excluir_modelo, listar_modelos,
    modelo_vitrine, renomear_modelo,
)

_VITRINE = "Vitrine (herói)"


def _miniatura(modelo, lado_px=120):
    """Compõe o modelo com conteúdo de exemplo e devolve um QPixmap quadrado."""
    from app.qt.canvas import pil_para_qpixmap
    lay = LayoutDef(60, 60, dpi=int(lado_px / 60 * 25.4),
                    paginas=[Pagina([Slot("s", carimbar_modelo(modelo, 0, 0, 60, 60))])])
    dados = DadosProduto("Produto", preco_por=Decimal("9.99"))
    img = compor_pagina(lay, lay.paginas[0], {"s": dados})
    return pil_para_qpixmap(img).scaled(
        lado_px, lado_px, Qt.AspectRatioMode.KeepAspectRatio,
        Qt.TransformationMode.SmoothTransformation)


class DialogoModelos(QDialog):
    def __init__(self, canvas, parent=None):
        super().__init__(parent)
        self.canvas = canvas
        self.setWindowTitle("Modelos de célula")
        self.setMinimumSize(360, 420)

        self.lista = QListWidget()
        self.lista.setIconSize(QSize(120, 120))
        self.lista.setViewMode(QListWidget.ViewMode.IconMode)
        self.lista.setResizeMode(QListWidget.ResizeMode.Adjust)
        self.lista.setSpacing(8)
        self.lista.itemDoubleClicked.connect(lambda _i: self._carimbar())

        b_carimbar = QPushButton("Carimbar no layout")
        b_carimbar.clicked.connect(self._carimbar)
        b_salvar = QPushButton("Salvar seleção como modelo…")
        b_salvar.clicked.connect(self._salvar_selecao)
        b_renomear = QPushButton("Renomear")
        b_renomear.clicked.connect(self._renomear)
        b_excluir = QPushButton("Excluir")
        b_excluir.clicked.connect(self._excluir)

        botoes = QHBoxLayout()
        for b in (b_carimbar, b_salvar, b_renomear, b_excluir):
            botoes.addWidget(b)

        raiz = QVBoxLayout(self)
        raiz.addWidget(self.lista, 1)
        raiz.addLayout(botoes)
        self._recarregar()

    def _recarregar(self) -> None:
        self.lista.clear()
        # a vitrine de fábrica sempre aparece primeiro (não é apagável)
        for nome, modelo in [(_VITRINE, modelo_vitrine())] + [
                (n, carregar_modelo(n)) for n in listar_modelos()]:
            if modelo is None:
                continue
            it = QListWidgetItem(_miniatura(modelo), nome)
            it.setData(Qt.ItemDataRole.UserRole, nome)
            self.lista.addItem(it)

    def _nome_selecionado(self) -> str | None:
        it = self.lista.currentItem()
        return it.data(Qt.ItemDataRole.UserRole) if it else None

    def _modelo_selecionado(self):
        nome = self._nome_selecionado()
        if nome is None:
            return None
        return modelo_vitrine() if nome == _VITRINE else carregar_modelo(nome)

    def _carimbar(self) -> None:
        modelo = self._modelo_selecionado()
        if modelo is None:
            return
        self.canvas.carimbar_modelo(modelo)
        self.accept()

    def _salvar_selecao(self) -> None:
        nome, ok = QInputDialog.getText(self, "Salvar modelo de célula",
                                        "Nome do modelo:")
        if not ok or not nome.strip():
            return
        if self.canvas.salvar_selecao_como_modelo(nome):
            self._recarregar()
        else:
            QMessageBox.information(self, "Modelos",
                                    "Selecione ao menos uma região primeiro.")

    def _renomear(self) -> None:
        nome = self._nome_selecionado()
        if nome is None or nome == _VITRINE:
            QMessageBox.information(self, "Modelos",
                                    "A vitrine de fábrica não é renomeável.")
            return
        novo, ok = QInputDialog.getText(self, "Renomear modelo",
                                        "Novo nome:", text=nome)
        if ok and novo.strip():
            renomear_modelo(nome, novo.strip())
            self._recarregar()

    def _excluir(self) -> None:
        nome = self._nome_selecionado()
        if nome is None or nome == _VITRINE:
            QMessageBox.information(self, "Modelos",
                                    "A vitrine de fábrica não é apagável.")
            return
        excluir_modelo(nome)
        self._recarregar()

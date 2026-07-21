"""Páginas e histórico visual (R-030/R-042, Fase 5 — Bloco D).

Miniaturas das páginas (navegar, adicionar/duplicar/remover/reordenar) e a
tira do histórico visual (clicar volta àquele estado). Miniaturas compostas
pelo compositor (vivas).
"""

from __future__ import annotations

from PySide6.QtCore import QSize, Qt
from PySide6.QtWidgets import (
    QDialog, QHBoxLayout, QLabel, QListWidget, QListWidgetItem, QPushButton,
    QVBoxLayout,
)


class DialogoPaginas(QDialog):
    def __init__(self, canvas, parent=None):
        super().__init__(parent)
        self.canvas = canvas
        self.setWindowTitle("Páginas e histórico")
        self.setMinimumSize(340, 480)

        self.paginas = QListWidget()
        self.paginas.setIconSize(QSize(120, 160))
        self.paginas.setViewMode(QListWidget.ViewMode.IconMode)
        self.paginas.setResizeMode(QListWidget.ResizeMode.Adjust)
        self.paginas.setSpacing(6)
        self.paginas.itemClicked.connect(self._navegar)

        b_add = QPushButton("Adicionar…")
        b_add.clicked.connect(self._adicionar)
        b_dup = QPushButton("Duplicar")
        b_dup.clicked.connect(self._duplicar)
        b_rem = QPushButton("Remover")
        b_rem.clicked.connect(self._remover)
        b_sobe = QPushButton("↑")
        b_sobe.clicked.connect(lambda: self._mover(-1))
        b_desce = QPushButton("↓")
        b_desce.clicked.connect(lambda: self._mover(1))
        bar = QHBoxLayout()
        for b in (b_add, b_dup, b_rem, b_sobe, b_desce):
            bar.addWidget(b)

        self.historico = QListWidget()
        self.historico.setIconSize(QSize(90, 120))
        self.historico.setViewMode(QListWidget.ViewMode.IconMode)
        self.historico.setFlow(QListWidget.Flow.LeftToRight)
        self.historico.setFixedHeight(150)
        self.historico.itemClicked.connect(self._saltar_historico)

        raiz = QVBoxLayout(self)
        raiz.addWidget(QLabel("Páginas (a ordem vai para o PDF):"))
        raiz.addWidget(self.paginas, 1)
        raiz.addLayout(bar)
        raiz.addWidget(QLabel("Histórico visual (clique para voltar):"))
        raiz.addWidget(self.historico)
        self._recarregar()

    def _recarregar(self) -> None:
        self.paginas.clear()
        for i in range(self.canvas.total_paginas()):
            pm = self.canvas.miniatura_pagina(i)
            it = QListWidgetItem(f"Página {i + 1}")
            if pm is not None:
                it.setIcon(pm)
            it.setData(Qt.ItemDataRole.UserRole, i)
            self.paginas.addItem(it)
        self.paginas.setCurrentRow(self.canvas.pagina_atual)
        self._recarregar_historico()

    def _recarregar_historico(self) -> None:
        self.historico.clear()
        atual = self.canvas.historico_indice()
        for i in range(self.canvas.historico_total()):
            pm = self.canvas.miniatura_estado(i)
            it = QListWidgetItem("• agora" if i == atual else str(i + 1))
            if pm is not None:
                it.setIcon(pm)
            it.setData(Qt.ItemDataRole.UserRole, i)
            self.historico.addItem(it)

    def _pagina_selecionada(self) -> int:
        it = self.paginas.currentItem()
        return it.data(Qt.ItemDataRole.UserRole) if it else self.canvas.pagina_atual

    def _navegar(self, item) -> None:
        self.canvas.ir_para_pagina(item.data(Qt.ItemDataRole.UserRole))

    def _adicionar(self) -> None:
        from PySide6.QtWidgets import QFileDialog
        cam, _ = QFileDialog.getOpenFileName(
            self, "Arte da nova página", "", "Imagens (*.png *.jpg *.jpeg)")
        if cam:
            self.canvas.adicionar_pagina_arte(cam)
            self._recarregar()

    def _duplicar(self) -> None:
        self.canvas.duplicar_pagina_atual()
        self._recarregar()

    def _remover(self) -> None:
        if self.canvas.remover_pagina_atual():
            self._recarregar()

    def _mover(self, delta: int) -> None:
        i = self._pagina_selecionada()
        if self.canvas.mover_pagina(i, i + delta):
            self._recarregar()

    def _saltar_historico(self, item) -> None:
        if self.canvas.ir_para_estado(item.data(Qt.ItemDataRole.UserRole)):
            self._recarregar()

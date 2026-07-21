"""
Faixa de páginas FIXA do editor (OS F11.5 #49/#50/#52 — R-030/R-042)
====================================================================
As miniaturas das páginas numa faixa lateral SEMPRE visível (não mais só num
diálogo): clicar navega, **arrastar reordena** (a ordem vai para o PDF — por
índice de página via `canvas.mover_pagina`, que registra no histórico), e a
miniatura é VIVA com **debounce** (edições em rajada = uma recomposição).
"""

from __future__ import annotations

from PySide6.QtCore import QSize, Qt, QTimer
from PySide6.QtWidgets import (
    QAbstractItemView,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app.qt.design import tokens as t

DEBOUNCE_MS = 400


class FaixaPaginas(QWidget):
    """A faixa vertical de miniaturas — o mapa do documento sempre à vista."""

    def __init__(self, canvas, parent=None):
        super().__init__(parent)
        self.canvas = canvas
        self.setFixedWidth(148)

        titulo = QLabel("Páginas")
        titulo.setProperty("papel", "secao")

        self.lista = QListWidget()
        self.lista.setIconSize(QSize(104, 140))
        self.lista.setSpacing(4)
        self.lista.setDragDropMode(
            QAbstractItemView.DragDropMode.InternalMove)
        self.lista.setDefaultDropAction(Qt.DropAction.MoveAction)
        self.lista.itemClicked.connect(self._navegar)
        self.lista.model().rowsMoved.connect(self._reordenada)
        self.lista.setToolTip("Clique navega · arraste para reordenar "
                              "(a ordem vai para o PDF)")

        v = QVBoxLayout(self)
        v.setContentsMargins(t.ESP_2, t.ESP_2, t.ESP_2, t.ESP_2)
        v.setSpacing(t.ESP_1)
        v.addWidget(titulo)
        v.addWidget(self.lista, 1)

        # #52: debounce — N edições em <400 ms viram UMA recarga de miniatura
        self._debounce = QTimer(self)
        self._debounce.setSingleShot(True)
        self._debounce.setInterval(DEBOUNCE_MS)
        self._debounce.timeout.connect(self._recarregar)
        canvas.editou.connect(lambda _reg: self.agendar_refresh())
        self._recarregar()

    # --- API -----------------------------------------------------------------

    def agendar_refresh(self) -> None:
        """Agenda UMA recarga (debounce): chamadas em rajada colapsam."""
        self._debounce.start()

    def _recarregar(self) -> None:
        atual = self.canvas.pagina_atual
        self.lista.blockSignals(True)
        self.lista.clear()
        for i in range(self.canvas.total_paginas()):
            it = QListWidgetItem(f"Página {i + 1}")
            pm = self.canvas.miniatura_pagina(i)
            if pm is not None:
                it.setIcon(pm)
            it.setData(Qt.ItemDataRole.UserRole, i)
            self.lista.addItem(it)
        if 0 <= atual < self.lista.count():
            self.lista.setCurrentRow(atual)
        self.lista.blockSignals(False)

    def _navegar(self, item) -> None:
        self.canvas.ir_para_pagina(item.data(Qt.ItemDataRole.UserRole))

    def _reordenada(self, _parent, inicio, _fim, _destino, linha) -> None:
        """#50: o drop reordena DE VERDADE no documento (mover_pagina passa
        pelo histórico — desfazer restaura a ordem)."""
        de = inicio
        para = linha if linha < inicio else linha - 1
        self.canvas.mover_pagina(de, para)
        self.agendar_refresh()

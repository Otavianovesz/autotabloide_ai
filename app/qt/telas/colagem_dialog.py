"""Prévia da colagem (R-050, Fase 7 — Bloco A).

"Isto é o que entendi" ANTES de criar: uma tabelinha com nome × preço ×
situação, para o dono confirmar ou ajustar. Preço não entendido (P0.3) aparece
em vermelho — nunca cria em silêncio (I2). Ao confirmar, as linhas caem no
MESMO caminho de conciliação de `importar_ofertas`.
"""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QDialog, QDialogButtonBox, QHeaderView, QLabel, QTableWidget,
    QTableWidgetItem, QVBoxLayout,
)

from app.qt.design import tokens as t
from app.qt.telas.colagem import LinhaColada


class ColagemPreviaDialog(QDialog):
    def __init__(self, linhas: list[LinhaColada], parent=None):
        super().__init__(parent)
        self._linhas = list(linhas)
        self.setWindowTitle("Colar tabela — isto é o que entendi")
        self.setMinimumSize(560, 420)

        n_ok = sum(1 for li in linhas if li.preco_valido)
        cab = QLabel(f"Reconheci {len(linhas)} produto(s) — {n_ok} com preço "
                     "entendido. Confira e ajuste; o vermelho é preço a rever.")
        cab.setWordWrap(True)

        self.tab = QTableWidget(len(linhas), 3)
        self.tab.setHorizontalHeaderLabels(["Nome", "Preço", "Situação"])
        self.tab.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeMode.Stretch)
        for i, li in enumerate(linhas):
            self.tab.setItem(i, 0, QTableWidgetItem(li.nome))
            # multi-preço mostra o texto da promoção na coluna de preço
            self.tab.setItem(i, 1, QTableWidgetItem(li.multi_preco or li.preco or ""))
            if li.multi_preco:
                sit = QTableWidgetItem("promoção")     # R-070: TEM preço
            elif li.preco_valido:
                sit = QTableWidgetItem("ok")
            else:
                sit = QTableWidgetItem(li.aviso or "sem preço")
            sit.setFlags(sit.flags() & ~Qt.ItemFlag.ItemIsEditable)
            if not (li.preco_valido or li.multi_preco):
                # polimento: tokens do tema (o rosa fixo clareava no escuro)
                sit.setBackground(QColor(t.PERIGO_FUNDO))
                sit.setForeground(QColor(t.PERIGO))
            self.tab.setItem(i, 2, sit)
        self.tab.itemChanged.connect(self._revalidar)

        botoes = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok
                                  | QDialogButtonBox.StandardButton.Cancel)
        botoes.button(QDialogButtonBox.StandardButton.Ok).setText(
            "Criar os itens")
        botoes.accepted.connect(self.accept)
        botoes.rejected.connect(self.reject)

        raiz = QVBoxLayout(self)
        raiz.addWidget(cab)
        raiz.addWidget(self.tab, 1)
        raiz.addWidget(botoes)

    def _revalidar(self, cel: QTableWidgetItem) -> None:
        if cel.column() not in (0, 1):
            return
        from app.qt.telas.colagem import parse_multi_preco
        from app.qt.telas.servico import preco_decimal
        lin = cel.row()
        preco = (self.tab.item(lin, 1).text() or "").strip() or None
        sit = self.tab.item(lin, 2)
        transparente = QColor(0, 0, 0, 0)
        if preco and parse_multi_preco(preco) is not None:   # R-070: promoção
            sit.setText("promoção")
            sit.setBackground(transparente)
            sit.setForeground(transparente)      # herda a cor do tema
            return
        valido = bool(preco) and preco_decimal(preco) is not None
        sit.setText("ok" if valido else ("preço a rever" if preco else "sem preço"))
        sit.setBackground(transparente if valido else QColor(t.PERIGO_FUNDO))
        sit.setForeground(transparente if valido else QColor(t.PERIGO))

    def linhas_confirmadas(self) -> list[LinhaColada]:
        """As linhas como ficaram na grade (nome/preço editados). Multi-preço
        editado à mão também é reconhecido (reusa `parse_multi_preco`)."""
        from app.qt.telas.colagem import parse_multi_preco
        from app.qt.telas.servico import preco_decimal
        out: list[LinhaColada] = []
        for i in range(self.tab.rowCount()):
            nome = (self.tab.item(i, 0).text() or "").strip()
            if not nome:
                continue
            preco = (self.tab.item(i, 1).text() or "").strip() or None
            mp = parse_multi_preco(preco) if preco else None
            if mp is not None:                    # promoção: TEM preço, sem valor Decimal
                out.append(LinhaColada(nome, None, True, None, multi_preco=mp.texto))
                continue
            valido = bool(preco) and preco_decimal(preco) is not None
            out.append(LinhaColada(nome, preco, valido))
        return out

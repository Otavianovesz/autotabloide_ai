"""
Fila de importação multi-arquivo (OS F11.5 #2 — R-049)
======================================================
Quando o dono abre VÁRIAS tabelas de uma vez, esta janelinha mostra o estado
de CADA arquivo — na fila · lendo · pronto · erro — em vez de um overlay
mudo. O erro de um arquivo fica visível (I2) sem derrubar os outros.
"""

from __future__ import annotations

from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QGridLayout,
    QLabel,
    QVBoxLayout,
)

from app.qt.design import tokens as t

ESTADOS = {
    "na fila": ("○", "TEXTO_3"),
    "lendo":   ("◐", "INFO"),
    "pronto":  ("●", "SUCESSO"),
    "erro":    ("●", "PERIGO"),
}


class PonteFila(QObject):
    """Leva o progresso do worker (outra thread) para a UI — sinal Qt é
    thread-safe (conexão enfileirada)."""

    mudou = Signal(str, str)               # (nome do arquivo, estado)


class FilaImportacaoDialog(QDialog):
    """A lista de arquivos com o chip de estado ao vivo (não-modal)."""

    def __init__(self, nomes: list[str], parent=None):
        super().__init__(parent)
        self.setWindowTitle("Importando arquivos")
        self.setModal(False)
        raiz = QVBoxLayout(self)
        raiz.setContentsMargins(t.ESP_4, t.ESP_4, t.ESP_4, t.ESP_4)
        raiz.setSpacing(t.ESP_2)
        titulo = QLabel("Importando arquivos")
        titulo.setProperty("papel", "titulo")
        raiz.addWidget(titulo)

        grade = QGridLayout()
        grade.setHorizontalSpacing(t.ESP_2)
        self._chips: dict[str, QLabel] = {}
        self.estados: dict[str, str] = {}
        for i, nome in enumerate(nomes):
            lbl = QLabel(nome)
            lbl.setToolTip(nome)
            chip = QLabel()
            self._chips[nome] = chip
            grade.addWidget(chip, i, 0)
            grade.addWidget(lbl, i, 1)
            self._pintar(nome, "na fila")
        grade.setColumnStretch(1, 1)
        raiz.addLayout(grade)

        botoes = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        botoes.button(QDialogButtonBox.StandardButton.Close).setText("Fechar")
        botoes.rejected.connect(self.reject)
        raiz.addWidget(botoes)
        self.resize(420, min(90 + 26 * len(nomes), 520))

    def _pintar(self, nome: str, estado: str) -> None:
        icone, token = ESTADOS.get(estado, ESTADOS["na fila"])
        cor = getattr(t, token)
        self._chips[nome].setText(
            f'<span style="color:{cor}">{icone}</span> {estado}')
        self.estados[nome] = estado

    def atualizar(self, nome: str, estado: str) -> None:
        if nome in self._chips:
            self._pintar(nome, estado)

    def tudo_pronto(self) -> bool:
        return all(e == "pronto" for e in self.estados.values())

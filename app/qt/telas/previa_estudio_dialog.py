"""
Prévia do Estúdio — antes/depois (OS F11.5 #8, F10)
===================================================
O packshot NÃO entra sozinho: o dono vê a foto original e o resultado lado a
lado e decide Aplicar ou Cancelar (curadoria não-destrutiva, I1 — a original
segue preservada como versão de qualquer jeito).
"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QLabel,
    QVBoxLayout,
    QWidget,
)

from app.qt.design import tokens as t


def _painel(rotulo: str, caminho: str) -> QWidget:
    w = QWidget()
    v = QVBoxLayout(w)
    v.setContentsMargins(0, 0, 0, 0)
    v.setSpacing(t.ESP_1)
    r = QLabel(rotulo)
    r.setProperty("papel", "legenda")
    r.setAlignment(Qt.AlignmentFlag.AlignCenter)
    foto = QLabel("—")
    foto.setAlignment(Qt.AlignmentFlag.AlignCenter)
    foto.setMinimumSize(240, 220)
    pm = QPixmap(str(caminho))
    if not pm.isNull():
        foto.setPixmap(pm.scaled(
            300, 260, Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation))
        # OS F11.5 #41 (mesmo idioma do comparador): resolução + peso
        kb = max(1, Path(caminho).stat().st_size // 1024)
        r.setText(f"{rotulo}  ·  {pm.width()}×{pm.height()} px · {kb} KB")
    v.addWidget(r)
    v.addWidget(foto, 1)
    return w


class PreviaEstudioDialog(QDialog):
    """Antes × depois do packshot; Aplicar = Accepted."""

    def __init__(self, antes: str, depois: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Estúdio — antes e depois")
        raiz = QVBoxLayout(self)
        raiz.setContentsMargins(t.ESP_4, t.ESP_4, t.ESP_4, t.ESP_4)
        raiz.setSpacing(t.ESP_2)
        titulo = QLabel("O packshot ficou assim — aplicar?")
        titulo.setProperty("papel", "titulo")
        raiz.addWidget(titulo)
        lado = QHBoxLayout()
        lado.setSpacing(t.ESP_3)
        lado.addWidget(_painel("ANTES (como está)", antes), 1)
        lado.addWidget(_painel("DEPOIS (packshot)", depois), 1)
        raiz.addLayout(lado, 1)
        nota = QLabel("A foto original vira uma versão — nada se perde; dá "
                      "para restaurar no Histórico de imagens.")
        nota.setProperty("papel", "legenda")
        nota.setWordWrap(True)
        raiz.addWidget(nota)
        botoes = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok
                                  | QDialogButtonBox.StandardButton.Cancel)
        botoes.button(QDialogButtonBox.StandardButton.Ok).setText("Aplicar")
        botoes.button(QDialogButtonBox.StandardButton.Cancel).setText(
            "Cancelar")
        botoes.accepted.connect(self.accept)
        botoes.rejected.connect(self.reject)
        raiz.addWidget(botoes)

"""Rodada JM (B4) — o CHECK de sabores da FAMÍLIA.

O gesto que o dono descreveu montando o Jornal: o produto casado
pertence a uma família ("Sardinha Coqueiro 125g") e ele MARCA quais
sabores estão na oferta — a célula desenha o leque das fotos marcadas
(o multi da F7.1). Membro sem foto entra avisado (o pré-voo cobre, I2).
"""

from __future__ import annotations

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QVBoxLayout,
)

from app.qt.design import tokens as t

_MINIATURA = 48


class SaboresDialog(QDialog):
    """Um check por membro da família; os marcados viram o leque."""

    def __init__(self, nome_familia: str, membros: list[dict],
                 marcados: set[int] | None = None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Sabores na oferta")
        marcados = marcados or set()

        raiz = QVBoxLayout(self)
        raiz.setContentsMargins(t.ESP_4, t.ESP_4, t.ESP_4, t.ESP_4)
        raiz.setSpacing(t.ESP_2)
        titulo = QLabel(f"Quais sabores de “{nome_familia}” "
                        "estão nesta oferta?")
        titulo.setProperty("papel", "titulo")
        titulo.setWordWrap(True)
        raiz.addWidget(titulo)
        legenda = QLabel("As fotos dos marcados viram o leque da célula. "
                         "Sabor sem foto entra sem imagem (o pré-voo avisa).")
        legenda.setProperty("papel", "legenda")
        legenda.setWordWrap(True)
        raiz.addWidget(legenda)

        self.lista = QListWidget()
        self.lista.setIconSize(QSize(_MINIATURA, _MINIATURA))
        for m in membros:
            rotulo = m.get("nome") or "?"
            if not m.get("imagem"):
                rotulo += "   (sem foto)"
            item = QListWidgetItem(rotulo)
            pm = QPixmap(m["imagem"]) if m.get("imagem") else QPixmap()
            if not pm.isNull():
                item.setIcon(pm.scaled(
                    _MINIATURA, _MINIATURA,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation))
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(
                Qt.CheckState.Checked
                if m.get("produto_id") in marcados
                else Qt.CheckState.Unchecked)
            item.setData(Qt.ItemDataRole.UserRole, m)
            self.lista.addItem(item)
        raiz.addWidget(self.lista, 1)

        botoes = QDialogButtonBox()
        botoes.addButton("Cancelar", QDialogButtonBox.ButtonRole.RejectRole)
        b_ok = botoes.addButton("Usar os marcados",
                                QDialogButtonBox.ButtonRole.AcceptRole)
        b_ok.setDefault(True)
        botoes.accepted.connect(self.accept)
        botoes.rejected.connect(self.reject)
        raiz.addWidget(botoes)
        self.resize(420, 360)

    def escolhidos(self) -> list[dict]:
        saida: list[dict] = []
        for i in range(self.lista.count()):
            it = self.lista.item(i)
            if it.checkState() == Qt.CheckState.Checked:
                saida.append(it.data(Qt.ItemDataRole.UserRole))
        return saida

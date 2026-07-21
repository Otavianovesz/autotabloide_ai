"""
Recuperar projeto corrompido (FASE 12, Bloco A — R-137)
=======================================================
Quando o projeto não abre, este diálogo diz O QUE quebrou (PT-BR, sem stack
trace) e oferece os snapshots BONS com prévia ("versão de 16:32 · 38 itens")
— o dono ESCOLHE; nada é sobrescrito em silêncio (I2) e o corrompido vira um
.bak reversível.
"""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QVBoxLayout,
)

from app.qt.design import tokens as t
from app.qt.design.componentes import EstadoVazio


class RecuperacaoDialog(QDialog):
    """Problemas + snapshots; Accepted = `snapshot_escolhido` preenchido."""

    def __init__(self, problemas: list[str], snapshots: list[dict],
                 parent=None):
        super().__init__(parent)
        self.setWindowTitle("Recuperar o projeto")
        self.resize(560, 440)
        self.snapshot_escolhido: dict | None = None
        self._snapshots = list(snapshots)

        raiz = QVBoxLayout(self)
        raiz.setContentsMargins(t.ESP_4, t.ESP_4, t.ESP_4, t.ESP_4)
        raiz.setSpacing(t.ESP_2)
        titulo = QLabel("Este projeto precisa de recuperação")
        titulo.setProperty("papel", "titulo")
        raiz.addWidget(titulo)
        prob = QLabel("O que aconteceu:\n"
                      + "\n".join(f"• {p}" for p in problemas))
        prob.setWordWrap(True)
        raiz.addWidget(prob)

        legenda = QLabel("Escolha um ponto BOM para restaurar — o estado "
                         "danificado fica guardado num .bak (nada se perde):")
        legenda.setProperty("papel", "legenda")
        legenda.setWordWrap(True)
        raiz.addWidget(legenda)

        self.lista = QListWidget()
        for sn in self._snapshots:
            li = QListWidgetItem(
                f"{sn['origem'].capitalize()} de {sn['quando']}  ·  "
                f"{sn['itens']} item(ns)")
            li.setData(Qt.ItemDataRole.UserRole, sn)
            self.lista.addItem(li)
        vazio = EstadoVazio(
            "alerta", "Nenhum snapshot bom encontrado",
            "Sem versões nem rascunho válidos — restaure de um backup do\n"
            "Cofre (Configurações › Backups).")
        raiz.addWidget(self.lista, 1)
        raiz.addWidget(vazio, 1)
        tem = bool(self._snapshots)
        self.lista.setVisible(tem)
        vazio.setVisible(not tem)
        if tem:
            self.lista.setCurrentRow(0)          # o mais novo pré-escolhido

        botoes = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok
                                  | QDialogButtonBox.StandardButton.Cancel)
        self._btn_ok = botoes.button(QDialogButtonBox.StandardButton.Ok)
        self._btn_ok.setText("Restaurar este")
        self._btn_ok.setEnabled(tem)
        botoes.button(QDialogButtonBox.StandardButton.Cancel).setText(
            "Agora não")
        botoes.accepted.connect(self._confirmar)
        botoes.rejected.connect(self.reject)
        raiz.addWidget(botoes)

    def _confirmar(self) -> None:
        item = self.lista.currentItem()
        if item is None:
            return
        self.snapshot_escolhido = item.data(Qt.ItemDataRole.UserRole)
        self.accept()

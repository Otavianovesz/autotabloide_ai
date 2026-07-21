"""
Sobre o AutoTabloide (FASE 1, passo 82)
=======================================
Versão, créditos e o atalho de diagnóstico (abre a pasta de logs — onde o
vigia de travamento grava). Acessível pela engrenagem do Shell.
"""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDialog, QHBoxLayout, QLabel, QPushButton, QVBoxLayout

from app.qt.design import tokens as t

VERSAO = "1.0 — reta final (Fase 1 do PLANO PERFEITO)"


class SobreDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Sobre o AutoTabloide")

        titulo = QLabel("AutoTabloide AI")
        titulo.setProperty("papel", "titulo")
        versao = QLabel(f"Versão {VERSAO}")
        versao.setProperty("papel", "legenda")
        creditos = QLabel(
            "Feito para o Belo Brasil Supermercados.\n"
            "Idealizado por Otaviano — construído com IA local\n"
            "(LM Studio), Python e Qt. Tudo roda NA SUA máquina;\n"
            "nada sai para a nuvem.")
        creditos.setWordWrap(True)

        diagnostico = QPushButton(" Abrir pasta de diagnóstico (logs)")
        from app.qt.design.icones import icone
        diagnostico.setIcon(icone("propriedades", tamanho=16))
        diagnostico.setToolTip(
            "A pasta com os registros do app — se algo travar, o arquivo "
            "travamentos.log de lá ajuda a entender o que houve")
        diagnostico.clicked.connect(self._abrir_logs)
        fechar = QPushButton("Fechar")
        fechar.clicked.connect(self.accept)
        rodape = QHBoxLayout()
        rodape.addWidget(diagnostico)
        rodape.addStretch(1)
        rodape.addWidget(fechar)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(t.ESP_5, t.ESP_4, t.ESP_5, t.ESP_4)
        lay.setSpacing(t.ESP_2)
        lay.addWidget(titulo)
        lay.addWidget(versao)
        lay.addSpacing(t.ESP_2)
        lay.addWidget(creditos)
        lay.addSpacing(t.ESP_3)
        lay.addLayout(rodape)
        self.setFixedWidth(420)

    def _abrir_logs(self) -> None:
        import os

        from app.core.paths import SystemRoot
        pasta = SystemRoot().logs
        pasta.mkdir(parents=True, exist_ok=True)
        try:
            os.startfile(str(pasta))     # Explorer (app é Windows)
        except Exception as e:
            from app.qt.design.toast import mostrar_toast
            mostrar_toast(self, f"Não abri a pasta: {pasta} ({e})",
                          tipo="erro")

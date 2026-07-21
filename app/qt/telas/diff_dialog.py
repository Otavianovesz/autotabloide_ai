"""
O que mudou desde a última edição (OS F11.5 #44/#45 — R-062)
============================================================
O `diff_edicoes` (por chave natural, I1) sempre existiu e era órfão de UI.
Este diálogo o mostra: quem ENTROU, quem SAIU e os PREÇOS que subiram/
desceram (com a seta e a variação) — o dono confere a semana num relance.
"""

from __future__ import annotations

from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QLabel,
    QListWidget,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from app.qt.design import tokens as t
from app.qt.design.componentes import EstadoVazio


def _lista(textos: list[str], vazio: str) -> QWidget:
    w = QWidget()
    v = QVBoxLayout(w)
    v.setContentsMargins(t.ESP_2, t.ESP_2, t.ESP_2, t.ESP_2)
    if not textos:
        v.addWidget(EstadoVazio("check_circulo", vazio, ""))
        return w
    lista = QListWidget()
    for texto in textos:
        lista.addItem(texto)
    v.addWidget(lista)
    return w


class DiffEdicaoDialog(QDialog):
    """As mudanças contra a última edição salva — informativo, nada muda."""

    def __init__(self, diff: dict, parent=None):
        super().__init__(parent)
        self.setWindowTitle("O que mudou desde a última edição")
        self.resize(560, 460)

        raiz = QVBoxLayout(self)
        raiz.setContentsMargins(t.ESP_4, t.ESP_4, t.ESP_4, t.ESP_4)
        raiz.setSpacing(t.ESP_2)
        titulo = QLabel("O que mudou desde a última edição")
        titulo.setProperty("papel", "titulo")
        raiz.addWidget(titulo)

        precos = []
        for it, antigo, novo in diff.get("precos", []):
            from app.qt.telas.servico import preco_decimal
            va, vn = preco_decimal(antigo), preco_decimal(novo)
            seta = ""
            if va is not None and vn is not None and va != vn:
                seta = "  ↑ subiu" if vn > va else "  ↓ desceu"
            precos.append(f"{it.nome}:  {antigo or '—'} → {novo or '—'}{seta}")

        abas = QTabWidget()
        abas.addTab(_lista(precos, "Nenhum preço mudou"),
                    f"Preços ({len(precos)})")
        novos = [it.nome for it in diff.get("novos", [])]
        abas.addTab(_lista(novos, "Nada entrou de novo"),
                    f"Entraram ({len(novos)})")
        sairam = [it.nome for it in diff.get("removidos", [])]
        abas.addTab(_lista(sairam, "Nada saiu"),
                    f"Saíram ({len(sairam)})")
        raiz.addWidget(abas, 1)

        botoes = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        botoes.button(QDialogButtonBox.StandardButton.Close).setText("Fechar")
        botoes.rejected.connect(self.reject)
        botoes.accepted.connect(self.accept)
        raiz.addWidget(botoes)

"""
Importar planilha — o relatório de mesclagem (R-118, Fase 11)
=============================================================
Mostra o que a planilha traz ANTES de gravar (novos, idênticos, ignorados) e
pede a decisão de CADA conflito (mesma chave natural, dados divergentes). Nada
se resolve em silêncio (I2) — o dono escolhe manter o seu, usar a planilha ou
manter os dois. Espelha a disciplina do relatório de mesclagem do pacote.
"""

from __future__ import annotations

from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLabel,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from app.core.portabilidade import Decisao
from app.qt.design import tokens as t
from app.qt.design.componentes import EstadoVazio

_OPCOES = [
    ("Manter o meu (não muda)", Decisao.MANTER_LOCAL),
    ("Usar o da planilha", Decisao.USAR_PACOTE),
    ("Manter os dois", Decisao.MANTER_AMBOS),
]


class ImportarPlanilhaDialog(QDialog):
    def __init__(self, analise, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Importar acervo (Excel)")
        self.resize(560, 480)
        self._analise = analise
        self._combos: dict[str, QComboBox] = {}

        raiz = QVBoxLayout(self)
        raiz.setContentsMargins(t.ESP_4, t.ESP_4, t.ESP_4, t.ESP_4)
        raiz.setSpacing(t.ESP_2)
        titulo = QLabel("Importar acervo (Excel)")
        titulo.setProperty("papel", "titulo")
        raiz.addWidget(titulo)
        resumo = QLabel(f"{len(analise.novos)} produtos novos · "
                        f"{len(analise.identicos)} já iguais · "
                        f"{len(analise.conflitos)} conflitos · "
                        f"{len(analise.ignoradas)} linhas ignoradas")
        resumo.setProperty("papel", "legenda")
        raiz.addWidget(resumo)
        for aviso in analise.avisos[:6]:
            lbl = QLabel("⚠ " + aviso)
            lbl.setWordWrap(True)
            raiz.addWidget(lbl)

        if analise.conflitos:
            raiz.addWidget(QLabel("Decida cada conflito (nada muda sem sua "
                                  "escolha):"))
            area = QScrollArea()
            area.setWidgetResizable(True)
            area.setMinimumHeight(180)
            corpo = QWidget()
            form = QFormLayout(corpo)
            form.setVerticalSpacing(t.ESP_3)
            form.setContentsMargins(t.ESP_2, t.ESP_2, t.ESP_2, t.ESP_2)
            for c in analise.conflitos:
                combo = QComboBox()
                for rot, _dec in _OPCOES:
                    combo.addItem(rot)
                self._combos[c.id_decisao] = combo
                linhas = [f"<b>{c.rotulo}</b>"]
                for campo in c.campos:                # antes → depois de CADA campo
                    linhas.append(
                        f"{campo}: meu «{c.local.get(campo, '—')}» → "
                        f"planilha «{c.linha.get(campo, '—')}»")
                lbl = QLabel("<br>".join(linhas))
                lbl.setWordWrap(True)
                form.addRow(lbl, combo)
            area.setWidget(corpo)
            raiz.addWidget(area, 1)
        else:
            raiz.addWidget(EstadoVazio(
                "check_circulo", "Nenhum conflito",
                "Tudo casa por chave natural — pode importar com segurança."),
                1)

        botoes = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok
            | QDialogButtonBox.StandardButton.Cancel)
        # PT-BR sempre — o StandardButton sai "Cancel" sem tradutor instalado
        botoes.button(QDialogButtonBox.StandardButton.Ok).setText("Importar")
        botoes.button(QDialogButtonBox.StandardButton.Ok).setToolTip(
            "Grava a mesclagem — só com as decisões acima")
        botoes.button(QDialogButtonBox.StandardButton.Cancel).setText("Cancelar")
        botoes.accepted.connect(self.accept)
        botoes.rejected.connect(self.reject)
        raiz.addWidget(botoes)

    def decisoes(self) -> dict:
        """A decisão de cada conflito, por id_decisao."""
        out = {}
        for id_dec, combo in self._combos.items():
            out[id_dec] = _OPCOES[combo.currentIndex()][1]
        return out

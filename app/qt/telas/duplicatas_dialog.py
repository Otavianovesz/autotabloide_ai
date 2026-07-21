"""
Caça-duplicatas — a fusão lado a lado (R-075, polimento pré-F12)
================================================================
O modelo (achar/fundir por chave forte, F9) estava pronto e testado — faltava a
casca. Aqui cada PAR aparece lado a lado (foto + nome + marca + preço), com o
MOTIVO do casamento visível ("mesmo EAN" / "mesmo nome e marca") e a decisão
POR PAR — nada se funde em silêncio (I2).

O que fica é sempre o mais ANTIGO (id menor — o histórico dele é maior); o
repetido vai para a LIXEIRA (soft-delete, reversível) e o jeito de escrever
dele vira alias do que ficou (o banco aprende). Marca diferente nunca é par.
"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from app.qt.design import tokens as t
from app.qt.design.componentes import EstadoVazio


def _mini(caminho: str | None, lado: int = 72) -> QLabel:
    lbl = QLabel()
    lbl.setFixedSize(lado, lado)
    lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
    if caminho and Path(caminho).exists():
        pm = QPixmap(caminho).scaled(
            lado, lado, Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation)
        lbl.setPixmap(pm)
    else:
        lbl.setText("sem\nfoto")
        lbl.setProperty("papel", "legenda")
    return lbl


def _cartao_produto(d: dict, rotulo: str) -> QWidget:
    w = QWidget()
    v = QVBoxLayout(w)
    v.setContentsMargins(t.ESP_2, t.ESP_2, t.ESP_2, t.ESP_2)
    v.setSpacing(t.ESP_1)
    papel = QLabel(rotulo)
    papel.setProperty("papel", "legenda")
    v.addWidget(papel)
    linha = QHBoxLayout()
    linha.setSpacing(t.ESP_2)
    linha.addWidget(_mini(d.get("imagem")))
    dados = QVBoxLayout()
    nome = QLabel(f"<b>{d.get('nome') or '—'}</b>")
    nome.setWordWrap(True)
    dados.addWidget(nome)
    detalhe = QLabel(" · ".join(x for x in (
        d.get("marca") or "", f"R$ {d['preco']}" if d.get("preco") else "",
        d.get("categoria") or "") if x) or "—")
    detalhe.setProperty("papel", "legenda")
    detalhe.setWordWrap(True)
    dados.addWidget(detalhe)
    dados.addStretch(1)
    linha.addLayout(dados, 1)
    v.addLayout(linha)
    return w


class DuplicatasDialog(QDialog):
    """R-075: revisar e fundir os pares de duplicatas do acervo."""

    def __init__(self, pares: list[dict], parent=None):
        super().__init__(parent)
        self.setWindowTitle("Caça-duplicatas")
        self.resize(640, 520)
        self._pares = pares
        self._checks: list[QCheckBox] = []

        raiz = QVBoxLayout(self)
        raiz.setContentsMargins(t.ESP_4, t.ESP_4, t.ESP_4, t.ESP_4)
        raiz.setSpacing(t.ESP_2)
        titulo = QLabel("Caça-duplicatas")
        titulo.setProperty("papel", "titulo")
        raiz.addWidget(titulo)

        if not pares:
            raiz.addWidget(EstadoVazio(
                "check_circulo", "Nenhuma duplicata no acervo",
                "Produtos com o mesmo código de barras ou o mesmo nome e "
                "marca apareceriam aqui."), 1)
        else:
            legenda = QLabel(
                f"{len(pares)} par(es) suspeitos. Fica o mais antigo (com o "
                "histórico); o repetido vai para a LIXEIRA — dá para "
                "restaurar. Marca diferente nunca vira par.")
            legenda.setProperty("papel", "legenda")
            legenda.setWordWrap(True)
            raiz.addWidget(legenda)

            area = QScrollArea()
            area.setWidgetResizable(True)
            corpo = QWidget()
            grade = QGridLayout(corpo)
            grade.setContentsMargins(t.ESP_2, t.ESP_2, t.ESP_2, t.ESP_2)
            grade.setVerticalSpacing(t.ESP_3)
            for lin, par in enumerate(pares):
                chk = QCheckBox()
                chk.setChecked(True)
                chk.setToolTip("Desmarque para deixar este par como está")
                self._checks.append(chk)
                grade.addWidget(chk, lin * 2, 0)
                grade.addWidget(_cartao_produto(par["vencedor"], "FICA"),
                                lin * 2, 1)
                seta = QLabel("←")
                seta.setToolTip(par["motivo"])
                grade.addWidget(seta, lin * 2, 2,
                                Qt.AlignmentFlag.AlignCenter)
                grade.addWidget(
                    _cartao_produto(par["perdedor"],
                                    f"REPETIDO — {par['motivo']}"),
                    lin * 2, 3)
                if lin < len(pares) - 1:
                    sep = QFrame()
                    sep.setFrameShape(QFrame.Shape.HLine)
                    sep.setProperty("papel", "separador")
                    grade.addWidget(sep, lin * 2 + 1, 0, 1, 4)
            grade.setColumnStretch(1, 1)
            grade.setColumnStretch(3, 1)
            area.setWidget(corpo)
            raiz.addWidget(area, 1)

        botoes = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok
                                  | QDialogButtonBox.StandardButton.Cancel)
        ok = botoes.button(QDialogButtonBox.StandardButton.Ok)
        ok.setText("Fundir os marcados")
        ok.setToolTip("Funde os pares marcados — o repetido vai para a "
                      "lixeira (reversível)")
        ok.setEnabled(bool(pares))
        botoes.button(QDialogButtonBox.StandardButton.Cancel).setText(
            "Cancelar")
        botoes.accepted.connect(self.accept)
        botoes.rejected.connect(self.reject)
        raiz.addWidget(botoes)

    def escolhidos(self) -> list[tuple[int, int]]:
        """Os pares MARCADOS, como (vencedor_id, perdedor_id)."""
        out = []
        for chk, par in zip(self._checks, self._pares):
            if chk.isChecked():
                out.append((par["vencedor"]["id"], par["perdedor"]["id"]))
        return out

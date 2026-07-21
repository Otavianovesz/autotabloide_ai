"""
Calendário promocional do ano (FASE 12, Bloco B — R-148)
========================================================
As datas do varejo com cor, chamada sugerida e "faltam N dias" — cada uma
vira um EVENTO do app com um clique (reusa criar_evento, F2/F3). O lembrete
do topo da aba Eventos é desligável aqui (chave local, nunca intrusivo).
"""

from __future__ import annotations

from datetime import date

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPixmap
from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
)

from app.qt.design import tokens as t
from app.qt.design.icones import icone
from app.qt.design.toast import mostrar_toast


def _bolinha(cor_hex: str) -> QPixmap:
    pm = QPixmap(14, 14)
    pm.fill(Qt.GlobalColor.transparent)
    from PySide6.QtGui import QPainter
    p = QPainter(pm)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    p.setBrush(QColor(cor_hex))
    p.setPen(Qt.PenStyle.NoPen)
    p.drawEllipse(1, 1, 12, 12)
    p.end()
    return pm


class CalendarioDialog(QDialog):
    """As datas do ano; “Criar evento” transforma a selecionada em campanha."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Calendário promocional")
        self.resize(560, 480)
        from app.core import calendario
        self._calendario = calendario

        raiz = QVBoxLayout(self)
        raiz.setContentsMargins(t.ESP_4, t.ESP_4, t.ESP_4, t.ESP_4)
        raiz.setSpacing(t.ESP_2)
        titulo = QLabel(f"As datas que vendem — {date.today().year}")
        titulo.setProperty("papel", "titulo")
        raiz.addWidget(titulo)
        legenda = QLabel("Cada data vira um EVENTO do app (com a cor dela) "
                         "num clique — aí é montar a campanha como sempre. "
                         "Sugestão, nunca imposição.")
        legenda.setProperty("papel", "legenda")
        legenda.setWordWrap(True)
        raiz.addWidget(legenda)

        self.lista = QListWidget()
        hoje = date.today()
        for d in self._calendario.datas_do_ano(hoje.year):
            passou = d["data"] < hoje
            falta = (d["data"] - hoje).days
            quando = d["data"].strftime("%d/%m")
            extra = ("já passou" if passou
                     else "é HOJE" if falta == 0
                     else f"faltam {falta} dia(s)")
            li = QListWidgetItem(_bolinha(d["cor"]),
                                 f"{d['nome']}  ·  {quando} ({extra})  —  "
                                 f"“{d['chamada']}”")
            li.setData(Qt.ItemDataRole.UserRole, d)
            if passou:
                li.setForeground(QColor(t.TEXTO_3))
            self.lista.addItem(li)
        raiz.addWidget(self.lista, 1)

        # o lembrete é LOCAL e desligável (passo 23)
        self.chk_lembretes = QCheckBox("Lembrar as próximas datas na aba "
                                       "Eventos")
        self.chk_lembretes.setChecked(self._calendario.lembretes_ligados())
        self.chk_lembretes.toggled.connect(self._lembretes_mudou)
        raiz.addWidget(self.chk_lembretes)

        linha = QHBoxLayout()
        btn_criar = QPushButton(" Criar evento desta data")
        btn_criar.setIcon(icone("calendario", cor=t.ACENTO_TEXTO, tamanho=16))
        btn_criar.setProperty("tipo", "primario")
        btn_criar.clicked.connect(self._criar_evento)
        linha.addStretch(1)
        linha.addWidget(btn_criar)
        raiz.addLayout(linha)

        botoes = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        botoes.button(QDialogButtonBox.StandardButton.Close).setText("Fechar")
        botoes.rejected.connect(self.reject)
        botoes.accepted.connect(self.accept)
        raiz.addWidget(botoes)

    def _lembretes_mudou(self, ligado: bool) -> None:
        try:
            from app.core.database import Database
            from app.core.repositories import ConfigRepositorio
            db = Database().init()
            try:
                with db.Session() as s:
                    ConfigRepositorio(s).set("calendario.lembretes",
                                             bool(ligado))
                    s.commit()
            finally:
                db.engine.dispose()
        except Exception:
            mostrar_toast(self, "Não deu para salvar a preferência.",
                          tipo="erro")

    def _criar_evento(self) -> None:
        item = self.lista.currentItem()
        if item is None:
            mostrar_toast(self, "Escolha uma data na lista.")
            return
        d = item.data(Qt.ItemDataRole.UserRole)
        try:
            self._calendario.criar_evento_comemorativo(d)
        except Exception as exc:
            mostrar_toast(self, f"Não deu para criar: {exc}", tipo="erro")
            return
        mostrar_toast(self, f"Evento “{d['nome']}” criado — monte a "
                            "campanha quando quiser.", tipo="sucesso")

"""F13-DECIMUS/D2 — o popover da validade: escolher, não digitar.

No lugar dos dois ``QInputDialog`` em sequência, UM diálogo compacto
com as respostas prontas — e a sugerida (a cascata do D1: o dia que
está no nome do encarte) JÁ vem marcada. Um clique em "Usar" e acabou.
"""

from __future__ import annotations

from datetime import date, timedelta

from PySide6.QtCore import QDate
from PySide6.QtWidgets import (
    QDateEdit,
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QLabel,
    QRadioButton,
    QVBoxLayout,
)

_DIAS_PT = ("segunda", "terça", "quarta", "quinta", "sexta",
            "sábado", "domingo")


class ValidadeDialog(QDialog):
    """As quatro respostas prontas + o calendário do "Outra data…"."""

    def __init__(self, sugerida: str | None = None, hoje: date | None = None,
                 parent=None):
        super().__init__(parent)
        self.setWindowTitle("Validade da oferta")
        self._hoje = hoje or date.today()

        raiz = QVBoxLayout(self)
        titulo = QLabel("Quando esta oferta vale?")
        titulo.setProperty("papel", "titulo")
        raiz.addWidget(titulo)

        self.op_sugerida = QRadioButton()
        if sugerida:
            rotulo = sugerida
            m = None
            import re
            m = re.search(r"(\d{1,2})/(\d{1,2})", sugerida)
            if m and sugerida.upper().startswith("SOMENTE"):
                try:
                    d = date(self._hoje.year, int(m.group(2)),
                             int(m.group(1)))
                    rotulo = (f"Somente {_DIAS_PT[d.weekday()]}, "
                              f"{d:%d/%m}")
                except (ValueError, IndexError):
                    pass
            self.op_sugerida.setText(f"{rotulo}   (sugerido)")
            self.op_sugerida.setChecked(True)
            raiz.addWidget(self.op_sugerida)
        else:
            self.op_sugerida.hide()
        self._sugerida = sugerida

        self.op_hoje = QRadioButton(f"Somente hoje, {self._hoje:%d/%m}")
        raiz.addWidget(self.op_hoje)

        fim = self._hoje + timedelta(days=6)
        self.op_faixa = QRadioButton(
            f"De {self._hoje:%d/%m} até {fim:%d/%m}")
        raiz.addWidget(self.op_faixa)

        self.op_estoques = QRadioButton("Enquanto durarem os estoques")
        raiz.addWidget(self.op_estoques)

        linha = QHBoxLayout()
        self.op_outra = QRadioButton("Outra data…")
        self.data_outra = QDateEdit(QDate(self._hoje.year, self._hoje.month,
                                          self._hoje.day))
        self.data_outra.setCalendarPopup(True)
        self.data_outra.setDisplayFormat("dd/MM/yyyy")
        # mexer no calendário já escolhe a opção (o gesto natural)
        self.data_outra.dateChanged.connect(
            lambda _d: self.op_outra.setChecked(True))
        linha.addWidget(self.op_outra)
        linha.addWidget(self.data_outra, 1)
        raiz.addLayout(linha)

        if not sugerida:
            self.op_hoje.setChecked(True)

        botoes = QDialogButtonBox()
        botoes.addButton("Cancelar", QDialogButtonBox.ButtonRole.RejectRole)
        b_usar = botoes.addButton("Usar",
                                  QDialogButtonBox.ButtonRole.AcceptRole)
        b_usar.setDefault(True)
        botoes.accepted.connect(self.accept)
        botoes.rejected.connect(self.reject)
        raiz.addWidget(botoes)

    def valor(self) -> str | None:
        """A validade escolhida, no vocabulário que o app já fala
        (SOMENTE dd/mm · OFERTA VÁLIDA DE .. ATÉ .. · texto livre)."""
        if self.op_sugerida.isChecked() and self._sugerida:
            return self._sugerida
        if self.op_hoje.isChecked():
            return f"SOMENTE {self._hoje:%d/%m}"
        if self.op_faixa.isChecked():
            from app.qt.telas.servico import montar_validade_oferta
            fim = self._hoje + timedelta(days=6)
            return montar_validade_oferta(f"{self._hoje:%d/%m}",
                                          f"{fim:%d/%m}")
        if self.op_estoques.isChecked():
            return "enquanto durarem os estoques"
        if self.op_outra.isChecked():
            d = self.data_outra.date()
            return f"SOMENTE {d.day():02d}/{d.month():02d}"
        return None

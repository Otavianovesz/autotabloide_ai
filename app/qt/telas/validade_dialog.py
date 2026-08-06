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

        # Rodada JM (B2A): o par DE/ATÉ arbitrário — o Jornal vale do
        # dia 3 ao 27 e não havia como dizer isso sem digitar à mão
        linha2 = QHBoxLayout()
        self.op_de_ate = QRadioButton("De")
        self.data_de = QDateEdit(QDate(self._hoje.year, self._hoje.month,
                                       self._hoje.day))
        fim_de_ate = self._hoje + timedelta(days=6)
        self.data_ate = QDateEdit(QDate(fim_de_ate.year, fim_de_ate.month,
                                        fim_de_ate.day))
        for de_ou_ate in (self.data_de, self.data_ate):
            de_ou_ate.setCalendarPopup(True)
            de_ou_ate.setDisplayFormat("dd/MM/yyyy")
            de_ou_ate.dateChanged.connect(self._mudou_de_ate)
        linha2.addWidget(self.op_de_ate)
        linha2.addWidget(self.data_de, 1)
        linha2.addWidget(QLabel("até"))
        linha2.addWidget(self.data_ate, 1)
        raiz.addLayout(linha2)
        self.op_de_ate.toggled.connect(lambda _c: self._validar_de_ate())

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
        self._b_usar = b_usar

    def _mudou_de_ate(self, _d) -> None:
        self.op_de_ate.setChecked(True)
        self._validar_de_ate()

    def _validar_de_ate(self) -> None:
        """Até antes do De = intervalo impossível — o "Usar" desabilita
        com a explicação no tooltip (nunca um período de trás p/ frente)."""
        invalido = (self.op_de_ate.isChecked()
                    and self.data_ate.date() < self.data_de.date())
        self._b_usar.setEnabled(not invalido)
        self._b_usar.setToolTip(
            "O “até” está antes do “de” — inverta as datas."
            if invalido else "")

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
        if self.op_de_ate.isChecked():
            from app.qt.telas.servico import montar_validade_oferta
            de = self.data_de.date()
            ate = self.data_ate.date()
            return montar_validade_oferta(
                f"{de.day():02d}/{de.month():02d}",
                f"{ate.day():02d}/{ate.month():02d}")
        return None

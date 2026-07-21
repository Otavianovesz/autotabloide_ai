"""
Perfis de exportação editáveis (OS F11.5 #5 — R-065)
====================================================
`perfis.salvar_perfis` existia sem tela. Aqui o dono cria/edita/duplica os
presets ("WhatsApp", "Impressão"…): nome, formato, tamanho e qualidade —
persistidos na Config (`export.perfis`). Campo vazio = "não usa" (None);
número inválido avisa e não salva torto (I2).
"""

from __future__ import annotations

from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
)

from app.qt.design import tokens as t
from app.rendering.perfis import (
    PERFIS_PADRAO,
    Perfil,
    perfis_configurados,
    salvar_perfis,
)

_COLS = ["Nome", "Formato", "Lado maior (px)", "Largura (px)",
         "Altura (px)", "DPI", "Qualidade"]


class PerfisDialog(QDialog):
    """Tabela editável dos perfis — Salvar persiste na Config."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Perfis de exportação")
        self.resize(700, 380)
        raiz = QVBoxLayout(self)
        raiz.setContentsMargins(t.ESP_4, t.ESP_4, t.ESP_4, t.ESP_4)
        raiz.setSpacing(t.ESP_2)
        titulo = QLabel("Perfis de exportação")
        titulo.setProperty("papel", "titulo")
        raiz.addWidget(titulo)
        legenda = QLabel("O perfil decide o tamanho/formato na hora de "
                         "exportar (ex.: “WhatsApp” encolhe para enviar "
                         "rápido). Deixe um campo de tamanho VAZIO para não "
                         "usá-lo; tudo vazio = tamanho nativo (impressão).")
        legenda.setProperty("papel", "legenda")
        legenda.setWordWrap(True)
        raiz.addWidget(legenda)

        self.tab = QTableWidget(0, len(_COLS))
        self.tab.setHorizontalHeaderLabels(_COLS)
        self.tab.verticalHeader().setVisible(False)
        raiz.addWidget(self.tab, 1)

        linha_botoes = QHBoxLayout()
        btn_novo = QPushButton("Novo")
        btn_novo.setToolTip("Cria um perfil em branco")
        btn_novo.clicked.connect(lambda: self._adicionar(Perfil("Novo perfil")))
        btn_dup = QPushButton("Duplicar")
        btn_dup.setToolTip("Copia o perfil selecionado (para variar sem "
                           "perder o original)")
        btn_dup.clicked.connect(self._duplicar)
        btn_rem = QPushButton("Excluir")
        btn_rem.setToolTip("Remove o perfil selecionado")
        btn_rem.clicked.connect(self._excluir)
        btn_padrao = QPushButton("Restaurar padrão")
        btn_padrao.setToolTip("Volta aos 3 perfis de fábrica")
        btn_padrao.clicked.connect(self._restaurar)
        for b in (btn_novo, btn_dup, btn_rem, btn_padrao):
            linha_botoes.addWidget(b)
        linha_botoes.addStretch(1)
        raiz.addLayout(linha_botoes)

        self._aviso = QLabel("")
        self._aviso.setProperty("papel", "legenda")
        self._aviso.setStyleSheet(f"color: {t.PERIGO};")
        raiz.addWidget(self._aviso)

        botoes = QDialogButtonBox(QDialogButtonBox.StandardButton.Save
                                  | QDialogButtonBox.StandardButton.Cancel)
        botoes.button(QDialogButtonBox.StandardButton.Save).setText("Salvar")
        botoes.button(QDialogButtonBox.StandardButton.Cancel).setText(
            "Cancelar")
        botoes.accepted.connect(self._salvar)
        botoes.rejected.connect(self.reject)
        raiz.addWidget(botoes)

        for p in perfis_configurados():
            self._adicionar(p)

    # --- linhas -----------------------------------------------------------------

    def _adicionar(self, p: Perfil) -> None:
        i = self.tab.rowCount()
        self.tab.insertRow(i)
        self.tab.setItem(i, 0, QTableWidgetItem(p.nome))
        combo = QComboBox()
        combo.addItems(["PNG", "PDF", "JPG"])
        combo.setCurrentText(p.formato)
        self.tab.setCellWidget(i, 1, combo)
        for col, valor in ((2, p.lado_maior_px), (3, p.largura_px),
                           (4, p.altura_px), (5, p.dpi), (6, p.qualidade)):
            self.tab.setItem(i, col, QTableWidgetItem(
                "" if valor is None else str(valor)))

    def _duplicar(self) -> None:
        i = self.tab.currentRow()
        perfis = self._coletar(silencioso=True)
        if perfis is None or not (0 <= i < len(perfis)):
            return
        copia = Perfil.from_dict(perfis[i].to_dict())
        copia.nome = f"{copia.nome} (cópia)"
        self._adicionar(copia)

    def _excluir(self) -> None:
        i = self.tab.currentRow()
        if i >= 0:
            self.tab.removeRow(i)

    def _restaurar(self) -> None:
        self.tab.setRowCount(0)
        for p in PERFIS_PADRAO:
            self._adicionar(Perfil.from_dict(p.to_dict()))

    # --- salvar -----------------------------------------------------------------

    def _coletar(self, silencioso: bool = False) -> list[Perfil] | None:
        """Lê a tabela → [Perfil]. Número inválido → aviso e None (I2)."""
        perfis: list[Perfil] = []
        for i in range(self.tab.rowCount()):
            nome = (self.tab.item(i, 0).text() if self.tab.item(i, 0)
                    else "").strip()
            if not nome:
                if not silencioso:
                    self._aviso.setText(f"Linha {i + 1}: o perfil precisa "
                                        "de um nome.")
                return None
            valores: list[int | None] = []
            for col in (2, 3, 4, 5, 6):
                bruto = (self.tab.item(i, col).text()
                         if self.tab.item(i, col) else "").strip()
                if not bruto:
                    valores.append(None)
                    continue
                try:
                    valores.append(int(bruto))
                except ValueError:
                    if not silencioso:
                        self._aviso.setText(
                            f"Linha {i + 1} ({nome}): “{bruto}” não é um "
                            "número inteiro.")
                    return None
            lado, larg, alt, dpi, qual = valores
            combo = self.tab.cellWidget(i, 1)
            perfis.append(Perfil(
                nome=nome, formato=combo.currentText(),
                lado_maior_px=lado, largura_px=larg, altura_px=alt,
                dpi=dpi if dpi is not None else 300,
                qualidade=qual if qual is not None else 90))
        return perfis

    def _salvar(self) -> None:
        perfis = self._coletar()
        if perfis is None:
            return
        if not perfis:
            self._aviso.setText("Deixe ao menos um perfil (ou restaure o "
                                "padrão).")
            return
        salvar_perfis(perfis)
        self.accept()

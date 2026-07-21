"""
Painel de camadas (F5.2 + sistema de design)
============================================
Lista as regiões do layout com **ícone por tipo**, mostrar/ocultar (olho) e
travar (cadeado) como botões-ícone, e reordenar (z-order). Cada ação chama o
canvas, que muta o modelo e recompõe pelo compositor (WYSIWYG).
"""

from __future__ import annotations

from PySide6.QtCore import QSize, Qt
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from app.qt.design import tokens as t
from app.qt.design.icones import icone
from app.rendering.model import TipoRegiao

# ícone por tipo de região (a leitura instantânea da lista)
ICONE_TIPO = {
    TipoRegiao.IMAGEM: "imagem",
    TipoRegiao.NOME: "texto",
    TipoRegiao.PRECO: "preco",
    TipoRegiao.UNIDADE: "unidade",
    TipoRegiao.SELO: "selo",
    TipoRegiao.TEXTO_LEGAL: "paragrafo",
}


def _toggle(ligado_icone: str, desligado_icone: str, ligado: bool, tip: str,
            ao_mudar) -> QToolButton:
    """Botão-ícone de alternância (olho, cadeado)."""
    b = QToolButton()
    b.setCheckable(True)
    b.setChecked(ligado)
    b.setIconSize(QSize(15, 15))
    b.setToolTip(tip)
    b.setProperty("papel", "linhaCamada")

    def _atualizar(v: bool) -> None:
        b.setIcon(icone(ligado_icone if v else desligado_icone,
                        cor=t.TEXTO_2 if v else t.ICONE_APAGADO, tamanho=15))

    _atualizar(ligado)
    b.toggled.connect(_atualizar)
    b.toggled.connect(ao_mudar)
    return b


class PainelCamadas(QWidget):
    def __init__(self, canvas, parent=None):
        super().__init__(parent)
        self.canvas = canvas
        self.lista = QListWidget()
        self.lista.setVerticalScrollMode(QListWidget.ScrollMode.ScrollPerPixel)

        subir = QPushButton(" Subir")
        subir.setIcon(icone("seta_cima", tamanho=14))
        subir.setToolTip("Trazer para a frente na composição")
        descer = QPushButton(" Descer")
        descer.setIcon(icone("seta_baixo", tamanho=14))
        descer.setToolTip("Levar para trás na composição")
        subir.clicked.connect(lambda: self._mover(-1))
        descer.clicked.connect(lambda: self._mover(1))
        botoes = QHBoxLayout()
        botoes.setSpacing(t.ESP_2)
        botoes.addWidget(subir)
        botoes.addWidget(descer)

        # R-039: a "Arte de fundo" como camada TRAVADA e explícita (o dono
        # não a move sem querer). Fica acima da lista de regiões.
        arte = QWidget()
        ha = QHBoxLayout(arte)
        ha.setContentsMargins(t.ESP_2, 2, t.ESP_1, 2)
        ha.setSpacing(t.ESP_2)
        ic_arte = QLabel()
        ic_arte.setPixmap(icone("imagem", cor=t.TEXTO_3, tamanho=15).pixmap(15, 15))
        rot_arte = QLabel("Arte de fundo")
        rot_arte.setProperty("papel", "legenda")
        self._trava_arte = _toggle(
            "cadeado", "cadeado_aberto", canvas.arte_travada(),
            "A arte fica travada para não se mover sem querer",
            lambda v: canvas.set_arte_travada(v))
        ha.addWidget(ic_arte)
        ha.addWidget(rot_arte, 1)
        ha.addWidget(self._trava_arte)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(t.ESP_2)
        lay.addWidget(arte)
        lay.addWidget(self.lista)
        lay.addLayout(botoes)
        # R-025/026 (Fase 4): raio-x da célula — clicar na linha seleciona a
        # região no canvas; selecionar no canvas destaca a linha (2 vias).
        self.lista.itemClicked.connect(self._clicou_na_lista)
        self._sincronizando = False
        canvas.selecao_mudou.connect(self._destacar_da_selecao)
        canvas.editou.connect(lambda _r: self.recarregar())   # valores vivos
        self.recarregar()

    def recarregar(self) -> None:
        selecionada = self._regiao_selecionada()
        self.lista.clear()
        for reg in self.canvas.regioes():
            item = QListWidgetItem(self.lista)
            item.setData(Qt.ItemDataRole.UserRole, reg)
            linha = self._linha(reg)
            item.setSizeHint(linha.sizeHint())
            self.lista.setItemWidget(item, linha)
            if reg is selecionada:
                self.lista.setCurrentItem(item)

    def _linha(self, reg) -> QWidget:
        w = QWidget()
        h = QHBoxLayout(w)
        h.setContentsMargins(t.ESP_2, 3, t.ESP_1, 3)
        h.setSpacing(t.ESP_2)

        tipo = QLabel()
        tipo.setPixmap(icone(ICONE_TIPO.get(reg.tipo, "camadas"),
                             cor=t.TEXTO_2, tamanho=15).pixmap(15, 15))
        tipo.setToolTip(reg.tipo.value)
        # R-025/026: papel + o CONTEÚDO atual (nome/preço/unidade) numa
        # coluna própria — o "raio-x" da célula, sem caçar no desenho
        coluna = QVBoxLayout()
        coluna.setContentsMargins(0, 0, 0, 0)
        coluna.setSpacing(0)
        nome = QLabel(reg.nome or reg.tipo.value.title())
        coluna.addWidget(nome)
        conteudo = ""
        try:
            conteudo = self.canvas.conteudo_da_regiao(reg)
        except Exception:
            conteudo = ""
        if conteudo:
            val = QLabel(conteudo)
            val.setProperty("papel", "legenda")
            val.setToolTip(conteudo)
            coluna.addWidget(val)

        olho = _toggle("olho", "olho_fechado", reg.visivel, "Mostrar/ocultar",
                       lambda v, r=reg: self.canvas.set_visivel(r, v))
        # cadeado fechado quando TRAVADO; aberto e apagado quando livre
        trava = _toggle("cadeado", "cadeado_aberto", reg.travado,
                        "Travar/destravar",
                        lambda v, r=reg: self.canvas.set_travado(r, v))

        h.addWidget(tipo)
        h.addLayout(coluna, 1)
        h.addWidget(olho)
        h.addWidget(trava)
        return w

    def _clicou_na_lista(self, item) -> None:
        """R-025 (passo 56): clicar na linha seleciona a região no canvas."""
        if self._sincronizando:
            return
        reg = item.data(Qt.ItemDataRole.UserRole)
        if reg is None:
            return
        self._sincronizando = True
        try:
            for it in self.canvas._itens:
                it.setSelected(it.regiao is reg)
            self.canvas._primaria = reg
            self.canvas._emitir_selecao()
        finally:
            self._sincronizando = False

    def _destacar_da_selecao(self, reg) -> None:
        """Passo 56 (via 2): selecionar no canvas destaca a linha na lista."""
        if self._sincronizando:
            return
        self._sincronizando = True
        try:
            for i in range(self.lista.count()):
                it = self.lista.item(i)
                if it.data(Qt.ItemDataRole.UserRole) is reg:
                    self.lista.setCurrentItem(it)
                    break
            else:
                self.lista.setCurrentItem(None)
        finally:
            self._sincronizando = False

    def _regiao_selecionada(self):
        it = self.lista.currentItem()
        return it.data(Qt.ItemDataRole.UserRole) if it is not None else None

    def _mover(self, delta: int) -> None:
        reg = self._regiao_selecionada()
        if reg is not None:
            self.canvas.mover_regiao(reg, delta)
            self.recarregar()

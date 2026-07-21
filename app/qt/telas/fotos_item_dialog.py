"""
Fotos do item — vários sabores/fragrâncias num slot (F7.1, Etapa C do Bloco E)
==============================================================================
A UI do motor F4.5: lista ORDENADA das fotos que o slot desenha (a ordem da
lista é a ordem do arranjo), com adicionar por busca assistida, arquivo,
reordenar e remover — mais o arranjo (leque/lado a lado/grade) por item.

A trava anti-alucinação da visão, na letra: a IA sugere **TERMOS** (chips
clicáveis de sabores prováveis); quem ESCOLHE cada foto é o humano, na
mesma curadoria de sempre. A IA nunca decide imagem nenhuma.
"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.qt.design import tokens as t
from app.qt.design.carregando import OverlayOcupado
from app.qt.design.icones import icone
from app.qt.design.toast import mostrar_toast
from app.qt.workers import GerenciadorTrabalhos, Trabalhador
from app.rendering.arranjo import ModoArranjo

_MINIATURA = 96
_ARRANJOS = [("Leque (padrão)", ModoArranjo.LEQUE.value),
             ("Lado a lado", ModoArranjo.LADO_A_LADO.value),
             ("Grade", ModoArranjo.GRADE.value)]


class FotosItemDialog(QDialog):
    """Devolve ``caminhos()`` (ordem = ordem do desenho) e ``arranjo_escolhido()``."""

    def __init__(self, item, parent=None, sugestor=None):
        super().__init__(parent)
        self._item = item
        # costura do serviço de sugestão (IA real por padrão; injetável)
        self._sugestor = sugestor
        self.setWindowTitle(f"Fotos do item — {item.nome}")
        self.setMinimumSize(560, 480)

        dica = QLabel("A ordem da lista é a ordem do desenho na célula. "
                      "A IA sugere TERMOS de sabores — você escolhe cada foto.")
        dica.setWordWrap(True)
        dica.setProperty("papel", "legenda")

        # --- lista ordenada das fotos ------------------------------------------
        self.lista = QListWidget()
        self.lista.setViewMode(QListWidget.ViewMode.IconMode)
        # RG-10: sem drag — arrastar mudava a POSIÇÃO VISUAL sem mudar a
        # ordem real (que é por linha, movida pelos botões ◀ ▶)
        self.lista.setMovement(QListWidget.Movement.Static)
        self.lista.setIconSize(QSize(_MINIATURA, _MINIATURA))
        self.lista.setResizeMode(QListWidget.ResizeMode.Adjust)
        self.lista.setSpacing(t.ESP_2)
        iniciais = list(item.imagens) if item.imagens else \
            ([item.imagem] if item.imagem else [])
        for cam in iniciais:
            self._adicionar_na_lista(cam)

        subir = QPushButton("◀ Antes")
        subir.setToolTip("Move a foto selecionada uma posição para trás")
        subir.clicked.connect(lambda: self._mover(-1))
        descer = QPushButton("Depois ▶")
        descer.clicked.connect(lambda: self._mover(+1))
        remover = QPushButton(" Remover")
        remover.setIcon(icone("lixeira", tamanho=15))
        remover.clicked.connect(self._remover)
        ordem = QHBoxLayout()
        ordem.setSpacing(t.ESP_1)
        ordem.addWidget(subir)
        ordem.addWidget(descer)
        ordem.addWidget(remover)
        ordem.addStretch(1)

        # --- busca assistida: chips de TERMOS da IA + curadoria humana -----------
        self._chips_caixa = QHBoxLayout()
        self._chips_caixa.setSpacing(t.ESP_1)
        self._chips_rotulo = QLabel("Sugestões da IA: consultando…")
        self._chips_rotulo.setProperty("papel", "legenda")
        self._chips_caixa.addWidget(self._chips_rotulo)
        self._chips_caixa.addStretch(1)

        self.termo = QLineEdit()
        self.termo.setPlaceholderText(f"ex.: {item.nome} uva")
        self.termo.setText(item.nome)
        buscar = QPushButton(" Buscar e escolher…")
        buscar.setIcon(icone("busca", tamanho=15))
        buscar.setToolTip("Busca candidatos e abre a curadoria — você escolhe")
        buscar.clicked.connect(self._buscar)
        arquivo = QPushButton(" Arquivo…")
        arquivo.setIcon(icone("abrir", tamanho=15))
        arquivo.clicked.connect(self._arquivo)
        linha_busca = QHBoxLayout()
        linha_busca.setSpacing(t.ESP_1)
        linha_busca.addWidget(self.termo, 1)
        linha_busca.addWidget(buscar)
        linha_busca.addWidget(arquivo)

        # --- arranjo por item (C2) ------------------------------------------------
        self.arranjo = QComboBox()
        for rotulo, _v in _ARRANJOS:
            self.arranjo.addItem(rotulo)
        valores = [v for _r, v in _ARRANJOS]
        if item.arranjo in valores:
            self.arranjo.setCurrentIndex(valores.index(item.arranjo))
        linha_arr = QHBoxLayout()
        linha_arr.addWidget(QLabel("Arranjo na célula:"))
        linha_arr.addWidget(self.arranjo)
        linha_arr.addStretch(1)

        botoes = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok
                                  | QDialogButtonBox.StandardButton.Cancel)
        botoes.button(QDialogButtonBox.StandardButton.Ok).setText("Aplicar")
        botoes.button(QDialogButtonBox.StandardButton.Cancel).setText("Cancelar")
        botoes.accepted.connect(self.accept)
        botoes.rejected.connect(self.reject)

        raiz = QVBoxLayout(self)
        raiz.setSpacing(t.ESP_2)
        raiz.addWidget(dica)
        raiz.addWidget(self.lista, 1)
        raiz.addLayout(ordem)
        raiz.addLayout(self._chips_caixa)
        raiz.addLayout(linha_busca)
        raiz.addLayout(linha_arr)
        raiz.addWidget(botoes)

        self._overlay = OverlayOcupado(self)
        self._trabalhos = GerenciadorTrabalhos()
        self._sugerir_termos()
        from app.qt.design.polimento import ordenar_tab
        ordenar_tab(self)               # FASE 1 (passo 66): Tab visual

    # --- lista -------------------------------------------------------------------

    def _adicionar_na_lista(self, caminho: str) -> None:
        pm = QPixmap(caminho)
        li = QListWidgetItem()
        if not pm.isNull():
            li.setIcon(pm.scaled(_MINIATURA, _MINIATURA,
                                 Qt.AspectRatioMode.KeepAspectRatio,
                                 Qt.TransformationMode.SmoothTransformation))
        li.setData(Qt.ItemDataRole.UserRole, caminho)
        li.setToolTip(Path(caminho).name)
        self.lista.addItem(li)

    def _mover(self, delta: int) -> None:
        linha = self.lista.currentRow()
        nova = linha + delta
        if linha < 0 or not (0 <= nova < self.lista.count()):
            return
        item = self.lista.takeItem(linha)
        self.lista.insertItem(nova, item)
        self.lista.setCurrentRow(nova)

    def _remover(self) -> None:
        linha = self.lista.currentRow()
        if linha >= 0:
            self.lista.takeItem(linha)

    def caminhos(self) -> list[str]:
        return [self.lista.item(i).data(Qt.ItemDataRole.UserRole)
                for i in range(self.lista.count())]

    def arranjo_escolhido(self) -> str:
        return _ARRANJOS[self.arranjo.currentIndex()][1]

    # --- sugestões da IA (SÓ termos — anti-alucinação) ------------------------------

    def _sugerir_termos(self) -> None:
        nome = self._item.nome
        sugestor = self._sugestor

        def _trabalho(_st):
            if sugestor is not None:
                return sugestor()
            from app.ai.enriquecimento import sugerir_variantes
            from app.qt.telas.servico import _motor_se_disponivel
            return sugerir_variantes(nome, _motor_se_disponivel())

        trab = Trabalhador(_trabalho)
        trab.ok.connect(self._mostrar_chips)
        trab.erro.connect(lambda _m: self._mostrar_chips([]))
        self._trabalhos.rodar(trab)

    def done(self, resultado: int) -> None:  # noqa: N802 (Qt)
        # junta as pontas dos workers ANTES de morrer — QThread viva com o
        # dono destruído derruba o processo (crash nativo, sem traceback)
        self._trabalhos.encerrar()
        super().done(resultado)

    def _mostrar_chips(self, termos: list[str]) -> None:
        if not termos:
            self._chips_rotulo.setText(
                "Sem sugestões da IA — digite o termo da busca.")
            return
        self._chips_rotulo.setText("Sugestões da IA:")
        for termo in termos:
            chip = QPushButton(termo)
            chip.setProperty("tipo", "fantasma")
            chip.setToolTip("Preenche o termo da busca — a escolha da foto "
                            "continua sua")
            chip.clicked.connect(
                lambda _c=False, tm=termo: self.termo.setText(
                    f"{self._item.nome} {tm}"))
            self._chips_caixa.insertWidget(self._chips_caixa.count() - 1, chip)

    # --- adicionar foto ---------------------------------------------------------------

    def _buscar(self) -> None:
        termo = self.termo.text().strip()
        if not termo:
            return

        def _trabalho(st, q=termo):
            from app.qt.telas import servico
            return servico.buscar_candidatos(q, st)

        trab = Trabalhador(_trabalho)
        trab.status.connect(self._overlay.mostrar)
        trab.ok.connect(lambda cands, tm=termo: self._curar(tm, cands))
        trab.erro.connect(self._falhou)
        self._trabalhos.rodar(trab)

    def _curar(self, termo: str, candidatos: list[str]) -> None:
        from app.qt.telas.curadoria_dialog import CuradoriaDialog

        self._overlay.esconder()
        dlg = CuradoriaDialog(termo, candidatos, self, nome_editavel=False)
        if dlg.exec() != CuradoriaDialog.DialogCode.Accepted:
            return
        tipo, valor = dlg.escolha
        if tipo == "nenhuma" or not valor:
            return
        self._tratar_e_adicionar(valor)

    def _arquivo(self) -> None:
        cam, _ = QFileDialog.getOpenFileName(
            self, "Foto do sabor/fragrância", "",
            "Imagens (*.png *.jpg *.jpeg *.webp *.bmp)")
        if cam:
            self._tratar_e_adicionar(cam)

    def _tratar_e_adicionar(self, fonte: str) -> None:
        pid = self._item.produto_id

        def _trabalho(st, f=fonte, p=pid):
            from app.qt.telas import servico
            return servico.preparar_extra(p, f, st)

        trab = Trabalhador(_trabalho)
        trab.status.connect(self._overlay.mostrar)
        trab.ok.connect(self._adicionada)
        trab.erro.connect(self._falhou)
        self._trabalhos.rodar(trab)

    def _adicionada(self, caminho: str) -> None:
        self._overlay.esconder()
        self._adicionar_na_lista(caminho)

    def _falhou(self, msg: str) -> None:
        self._overlay.esconder()
        mostrar_toast(self, msg, tipo="erro")

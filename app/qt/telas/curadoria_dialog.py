"""
Curadoria de imagem — o pop-up de escolher a foto do produto
============================================================
Miniaturas dos candidatos (ddgs) + entrada manual (arquivo / colar / URL) +
"sem imagem" (degrada sem quebrar). Devolve a escolha como ``(tipo, valor)``:
``("arquivo", caminho)``, ``("url", url)`` ou ``("nenhuma", None)``.
"""

from __future__ import annotations

import tempfile
from pathlib import Path

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QFileDialog,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
)

from app.qt.design import tokens as t
from app.qt.design.componentes import EstadoVazio
from app.qt.design.icones import icone

_MINIATURA = 148


class CuradoriaDialog(QDialog):
    def __init__(self, nome_produto: str, candidatos: list[str], parent=None,
                 *, nome_editavel: bool = True,
                 tokens_perdidos: list[str] | None = None):
        super().__init__(parent)
        self.setWindowTitle("Escolher imagem")
        self.escolha: tuple[str, str | None] = ("nenhuma", None)
        self._nome_original = nome_produto

        # A2 (ORDEM_F5_8): o humano corrige o nome ANTES de cadastrar
        # ("Floccao" → "Flocão"; "Po Trink" → "Suco em Pó Trink")
        self.nome = QLineEdit(nome_produto)
        self.nome.setToolTip("Nome final do produto — corrija aqui se o "
                             "enriquecimento errou")
        if not nome_editavel:
            self.nome.setReadOnly(True)
        titulo = self.nome
        dica = QLabel("Escolha um candidato, ou traga a sua própria imagem. "
                      "O fundo será removido automaticamente.")
        dica.setProperty("papel", "legenda")

        # RG-20 (regra dura): a IA descartou palavra do original — o campo
        # acende e o aviso é NOMINAL; quem decide o nome final é o humano
        self.aviso_tokens = QLabel("")
        self.aviso_tokens.setProperty("papel", "legenda")
        self.aviso_tokens.setWordWrap(True)
        if tokens_perdidos:
            from app.qt.design import tokens as tk
            self.nome.setStyleSheet(f"border: 2px solid {tk.ALERTA};")
            self.aviso_tokens.setText(
                "⚠ A IA descartou do nome original: "
                f"{', '.join('“' + t + '”' for t in tokens_perdidos)} — "
                "confira (ou recoloque) antes de criar.")
            self.aviso_tokens.setStyleSheet(f"color: {tk.ALERTA};")
        else:
            self.aviso_tokens.hide()

        # A3 (ORDEM_F5_8): re-busca com termo editável (o antídoto do caso
        # "Mococa → unhas de manicure")
        self.termo = QLineEdit(nome_produto)
        self.termo.setToolTip("Termo da busca de imagem — mude e busque de novo")
        buscar = QPushButton(" Buscar de novo")
        buscar.setIcon(icone("busca", tamanho=15))
        buscar.clicked.connect(self._buscar_de_novo)
        # RG-26: paginação — pede uma leva maior da MESMA busca
        self._n_busca = 6
        self.btn_mais = QPushButton(" Mais resultados")
        self.btn_mais.setIcon(icone("busca", tamanho=15))
        self.btn_mais.setToolTip("Busca mais candidatos com o mesmo termo")
        self.btn_mais.clicked.connect(self._mais_resultados)
        caixa_busca = QHBoxLayout()
        caixa_busca.setSpacing(t.ESP_2)
        caixa_busca.addWidget(self.termo, 1)
        caixa_busca.addWidget(buscar)
        caixa_busca.addWidget(self.btn_mais)

        self.lista = QListWidget()
        self.lista.setViewMode(QListWidget.ViewMode.IconMode)
        self.lista.setMovement(QListWidget.Movement.Static)   # RG-10: sem drag
        self.lista.setIconSize(QSize(_MINIATURA, _MINIATURA))
        self.lista.setResizeMode(QListWidget.ResizeMode.Adjust)
        self.lista.setSpacing(t.ESP_2)
        self.lista.setUniformItemSizes(True)
        # FASE 1 (passo 56): célula da grade nunca menor que 160 px
        self.lista.setGridSize(QSize(max(160, _MINIATURA + 12),
                                     max(160, _MINIATURA + 12)))
        for cam in candidatos:
            pm = QPixmap(cam)
            if pm.isNull():
                continue
            item = QListWidgetItem()
            item.setIcon(pm.scaled(_MINIATURA, _MINIATURA,
                                   Qt.AspectRatioMode.KeepAspectRatio,
                                   Qt.TransformationMode.SmoothTransformation))
            item.setData(Qt.ItemDataRole.UserRole, cam)
            item.setToolTip(f"{pm.width()}×{pm.height()}")
            self.lista.addItem(item)
        self.lista.itemSelectionChanged.connect(self._habilitar)
        self.lista.itemDoubleClicked.connect(lambda _it: self._usar())

        self._vazio = EstadoVazio("imagem", "Nenhum candidato encontrado",
                                  "Sem rede ou busca sem resultado — mude o\n"
                                  "termo e busque de novo, use arquivo/colar/"
                                  "URL, ou siga sem imagem.")
        self._vazio.setVisible(self.lista.count() == 0)
        self.lista.setVisible(self.lista.count() > 0)
        vazio = self._vazio

        arquivo = QPushButton(" Arquivo…")
        arquivo.setIcon(icone("abrir", tamanho=16))
        arquivo.setToolTip("Usar uma imagem do seu computador")
        arquivo.clicked.connect(self._arquivo)
        colar = QPushButton(" Colar")
        colar.setIcon(icone("duplicar", tamanho=16))
        colar.setToolTip("Usar a imagem da área de transferência")
        colar.clicked.connect(self._colar)
        url = QPushButton(" URL…")
        url.setIcon(icone("busca", tamanho=16))
        url.setToolTip("Baixar a imagem de um endereço (http/https)")
        url.clicked.connect(self._url)
        # Polimento F10: a fonte ACERVO — reaproveitar uma foto que já está
        # na biblioteca (útil p/ sabores/variantes do mesmo produto)
        acervo = QPushButton(" Do acervo…")
        acervo.setIcon(icone("caixa", tamanho=16))
        acervo.setToolTip("Escolher uma foto que já está na biblioteca "
                          "de outro produto")
        acervo.clicked.connect(self._do_acervo)
        sem = QPushButton("Sem imagem")
        sem.setToolTip("Seguir sem foto (dá para trocar depois)")
        sem.clicked.connect(self._sem_imagem)
        self.usar = QPushButton(" Usar esta")
        self.usar.setIcon(icone("check_circulo", cor=t.ACENTO_TEXTO, tamanho=16))
        self.usar.setProperty("tipo", "primario")
        self.usar.setEnabled(False)
        self.usar.clicked.connect(self._usar)

        botoes = QHBoxLayout()
        botoes.setSpacing(t.ESP_2)
        for b in (arquivo, colar, url, acervo):
            botoes.addWidget(b)
        botoes.addStretch(1)
        botoes.addWidget(sem)
        botoes.addWidget(self.usar)
        # FASE 1 (passo 56): o diálogo nunca estreita a ponto de cortar a
        # botoeira (mínimo = soma dos botões + respiros)
        minimo = (sum(b.sizeHint().width()
                      for b in (arquivo, colar, url, acervo, sem, self.usar))
                  + 7 * t.ESP_2 + 2 * t.ESP_4)
        self.setMinimumWidth(max(560, minimo))

        lay = QVBoxLayout(self)
        lay.setContentsMargins(t.ESP_4, t.ESP_4, t.ESP_4, t.ESP_4)
        lay.setSpacing(t.ESP_2)
        lay.addWidget(titulo)
        lay.addWidget(self.aviso_tokens)   # RG-20: aviso nominal da perda
        lay.addWidget(dica)
        lay.addLayout(caixa_busca)
        lay.addWidget(self.lista, 1)
        lay.addWidget(vazio, 1)
        lay.addLayout(botoes)
        self.resize(720, 520)

        from app.qt.design.carregando import OverlayOcupado
        from app.qt.workers import GerenciadorTrabalhos
        self._overlay = OverlayOcupado(self)
        self._trabalhos = GerenciadorTrabalhos()

        # RG-06: o botão "Colar" sempre funcionou, o atalho não — Ctrl+V no
        # diálogo cola a imagem (num campo de texto focado, cola texto, como
        # sempre: o campo tem precedência sobre o atalho)
        from PySide6.QtGui import QKeySequence, QShortcut
        atalho_colar = QShortcut(QKeySequence.StandardKey.Paste, self)
        atalho_colar.setContext(Qt.ShortcutContext.WidgetWithChildrenShortcut)
        atalho_colar.activated.connect(self._colar)

        from app.qt.design.polimento import ordenar_tab
        ordenar_tab(self)               # FASE 1 (passo 66): Tab visual

    # --- nome final (A2) ----------------------------------------------------------

    def nome_final(self) -> str:
        """O nome corrigido pelo humano (ou o original, se não mexeu)."""
        return self.nome.text().strip() or self._nome_original

    # --- re-busca (A3) --------------------------------------------------------------

    def _buscar_de_novo(self, *, n: int | None = None) -> None:
        from app.qt.telas import servico
        from app.qt.workers import Trabalhador

        termo = self.termo.text().strip()
        if not termo:
            return
        if n is None:
            self._n_busca = 6              # busca nova recomeça a paginação
        alvo = n or self._n_busca
        trab = Trabalhador(
            lambda st, q=termo, k=alvo: servico.buscar_candidatos(q, st, n=k))
        trab.status.connect(self._overlay.mostrar)
        trab.ok.connect(self._aplicar_candidatos)
        trab.erro.connect(lambda _msg: self._overlay.esconder())
        self._trabalhos.rodar(trab)

    def _mais_resultados(self) -> None:
        """RG-26: a mesma busca, uma leva maior (6 → 12 → 18…)."""
        self._n_busca += 6
        self._buscar_de_novo(n=self._n_busca)

    def _aplicar_candidatos(self, caminhos: list[str]) -> None:
        self._overlay.esconder()
        self.lista.clear()
        for cam in caminhos:
            pm = QPixmap(cam)
            if pm.isNull():
                continue
            item = QListWidgetItem()
            item.setIcon(pm.scaled(_MINIATURA, _MINIATURA,
                                   Qt.AspectRatioMode.KeepAspectRatio,
                                   Qt.TransformationMode.SmoothTransformation))
            item.setData(Qt.ItemDataRole.UserRole, cam)
            item.setToolTip(f"{pm.width()}×{pm.height()}")
            self.lista.addItem(item)
        tem = self.lista.count() > 0
        self._vazio.setVisible(not tem)
        self.lista.setVisible(tem)
        self._habilitar()

    # --- escolhas ---------------------------------------------------------------

    def _habilitar(self) -> None:
        self.usar.setEnabled(bool(self.lista.selectedItems()))

    def _usar(self) -> None:
        sel = self.lista.selectedItems()
        if sel:
            self.escolha = ("arquivo", sel[0].data(Qt.ItemDataRole.UserRole))
            self.accept()

    def _arquivo(self) -> None:
        cam, _ = QFileDialog.getOpenFileName(
            self, "Escolher imagem", "",
            "Imagens (*.png *.jpg *.jpeg *.webp *.bmp)")
        if cam:
            self.escolha = ("arquivo", cam)
            self.accept()

    def _colar(self) -> None:
        img = QApplication.clipboard().image()
        if img.isNull():
            from app.qt.design.toast import mostrar_toast
            mostrar_toast(self, "Não há imagem na área de transferência.",
                          tipo="erro")     # I2: nunca falhar em silêncio
            return
        destino = Path(tempfile.mkdtemp(prefix="atb_colada_")) / "colada.png"
        img.save(str(destino), "PNG")
        self.escolha = ("arquivo", str(destino))
        self.accept()

    def _url(self) -> None:
        url, ok = QInputDialog.getText(self, "Imagem por URL", "Endereço da imagem:")
        if ok and url.strip().startswith(("http://", "https://")):
            self.escolha = ("url", url.strip())
            self.accept()

    def _do_acervo(self) -> None:
        """Polimento F10: escolher uma foto que JÁ está na biblioteca — a
        mesma escolha ("arquivo", caminho) do fluxo de sempre."""
        from app.qt.telas.acervo_picker_dialog import AcervoPickerDialog
        dlg = AcervoPickerDialog(self)
        if dlg.exec() == QDialog.DialogCode.Accepted and dlg.caminho:
            self.escolha = ("arquivo", dlg.caminho)
            self.accept()

    def _sem_imagem(self) -> None:
        self.escolha = ("nenhuma", None)
        self.accept()

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
    QCheckBox,
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
                 tokens_perdidos: list[str] | None = None,
                 possivel_composto: bool = False,
                 componentes: list[str] | None = None,
                 componentes_da_ia: bool = False,
                 mais18: bool = False,
                 sabores: list[str] | None = None,
                 nome_familia_sugerido: str = "",
                 contexto: str = "",
                 posicao: tuple[int, int] | None = None):
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

        # QUINTUSDECIMUS/J13 — a TERCEIRA pergunta: a linha com mais de
        # um item pergunta O QUE ela é. A diferença entre "2 produtos" e
        # "2 sabores" é uma pergunta, não um algoritmo — o dono decide
        # com um rádio. (B3.2 evoluída; `chk_composto` agora É o rádio
        # "2 produtos" — mesma API isChecked/setChecked.)
        from PySide6.QtWidgets import QButtonGroup, QRadioButton
        comps = list(componentes or [])
        sabs = list(sabores or [])
        tem_multi = possivel_composto or len(sabs) >= 2
        self._aviso_composto = QLabel(
            "Esta linha parece ter MAIS DE UM item:")
        self._aviso_composto.setProperty("papel", "legenda")
        self.chk_composto = QRadioButton(
            "São 2 produtos diferentes (criar os dois e compor)")
        self.chk_composto.setToolTip(
            "Cada um vira um produto próprio no acervo e a célula "
            "mostra os dois juntos — separável a qualquer momento")
        self.comp_1 = QLineEdit(comps[0] if len(comps) > 0 else "")
        self.comp_2 = QLineEdit(comps[1] if len(comps) > 1 else "")
        for campo in (self.comp_1, self.comp_2):
            campo.setPlaceholderText("nome do produto…")
        self.rb_sabores = QRadioButton(
            "São SABORES do mesmo produto (criar a família)")
        self.rb_sabores.setToolTip(
            "Um produto por sabor, ligados à família — a célula mostra "
            "o leque; a foto escolhida vai ao 1º sabor")
        self.nome_familia = QLineEdit(nome_familia_sugerido)
        self.nome_familia.setPlaceholderText("nome da família…")
        self.chks_sabores = [QCheckBox(s) for s in sabs]
        for c in self.chks_sabores:
            c.setChecked(True)
        self.rb_um = QRadioButton("É um produto só (o nome é assim mesmo)")
        self._grupo_multi = QButtonGroup(self)
        for rb in (self.chk_composto, self.rb_sabores, self.rb_um):
            self._grupo_multi.addButton(rb)
        if tem_multi:
            # a IA/gesto que JÁ decidiu pré-marca "2 produtos"; sabores
            # detectados sem decisão pré-marcam nada além do neutro
            if componentes_da_ia:
                self.chk_composto.setChecked(True)
            else:
                self.rb_um.setChecked(True)
            for rb in (self.chk_composto, self.rb_sabores, self.rb_um):
                rb.toggled.connect(self._habilitar_multi)
            if not sabs:
                self.rb_sabores.hide()
                self.nome_familia.hide()
            self._habilitar_multi()
        else:
            for w in ([self._aviso_composto, self.chk_composto,
                       self.comp_1, self.comp_2, self.rb_sabores,
                       self.nome_familia, self.rb_um]
                      + self.chks_sabores):
                w.hide()

        # Rodada JM (B3.5): o +18 automático é VISÍVEL e editável (I2) —
        # antes `proposta.mais18` viajava invisível até o banco
        self.chk_mais18 = QCheckBox("+18 (bebida alcoólica)")
        self.chk_mais18.setChecked(bool(mais18))
        self.chk_mais18.setToolTip(
            "Grava bebida alcoólica no produto — o selo +18 entra "
            "sozinho em toda peça (decisão travada da casa)")

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
        # OS F11.5 #46: girar/cortar e o pincel de refino TAMBÉM aqui — o
        # candidato escolhido pode ser arrumado ANTES de virar a oficial
        self.btn_ajustar = QPushButton(" Ajustar…")
        self.btn_ajustar.setIcon(icone("ajustar", tamanho=16))
        self.btn_ajustar.setToolTip("Girar/espelhar/cortar o candidato "
                                    "selecionado antes de usar")
        self.btn_ajustar.setEnabled(False)
        self.btn_ajustar.clicked.connect(self._ajustar_candidato)
        self.btn_refinar = QPushButton(" Refinar…")
        self.btn_refinar.setIcon(icone("ajustar", tamanho=16))
        self.btn_refinar.setToolTip("Pincel no recorte do candidato "
                                    "(restaurar/apagar)")
        self.btn_refinar.setEnabled(False)
        self.btn_refinar.clicked.connect(self._refinar_candidato)
        self.usar = QPushButton(" Usar esta")
        self.usar.setIcon(icone("check_circulo", cor=t.ACENTO_TEXTO, tamanho=16))
        self.usar.setProperty("tipo", "primario")
        self.usar.setEnabled(False)
        self.usar.clicked.connect(self._usar)

        botoes = QHBoxLayout()
        botoes.setSpacing(t.ESP_2)
        for b in (arquivo, colar, url, acervo, self.btn_ajustar,
                  self.btn_refinar):
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
        # QUINTUSDECIMUS/J23: o diálogo DIZ de onde veio e quantas
        # faltam — numa sessão de 42 itens, o dono precisa do contexto
        self._contexto = QLabel("")
        self._contexto.setProperty("papel", "legenda")
        self._contexto.setWordWrap(True)
        partes_ctx = []
        if contexto:
            partes_ctx.append(f"Linha importada: “{contexto}”")
        if posicao:
            partes_ctx.append(f"item {posicao[0]} de {posicao[1]}")
        if partes_ctx:
            self._contexto.setText("  ·  ".join(partes_ctx))
        else:
            self._contexto.hide()

        lay.addWidget(titulo)
        lay.addWidget(self._contexto)            # J23: contexto + n de N
        lay.addWidget(self.aviso_tokens)   # RG-20: aviso nominal da perda
        lay.addWidget(self._aviso_composto)      # J13: a 3ª pergunta
        lay.addWidget(self.chk_composto)
        linha_comp = QHBoxLayout()
        linha_comp.setSpacing(t.ESP_2)
        linha_comp.addWidget(self.comp_1, 1)
        linha_comp.addWidget(self.comp_2, 1)
        lay.addLayout(linha_comp)
        lay.addWidget(self.rb_sabores)
        linha_sab = QHBoxLayout()
        linha_sab.setSpacing(t.ESP_2)
        linha_sab.addWidget(self.nome_familia, 1)
        for c in self.chks_sabores:
            linha_sab.addWidget(c)
        lay.addLayout(linha_sab)
        lay.addWidget(self.rb_um)
        lay.addWidget(self.chk_mais18)           # B3.5: +18 visível
        lay.addWidget(dica)
        lay.addLayout(caixa_busca)
        lay.addWidget(self.lista, 1)
        lay.addWidget(vazio, 1)
        lay.addLayout(botoes)
        # J23: o diálogo em que o dono escolhe 42 fotos seguidas merece
        # espaço — miniaturas maiores, botões nunca cortados
        self.resize(1040, 680)

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

    def showEvent(self, ev) -> None:  # noqa: N802 (Qt)
        super().showEvent(ev)
        from app.qt.design.polimento import clampar_a_tela
        clampar_a_tela(self)            # L3: cabe em qualquer notebook

    def _habilitar_multi(self, *_a) -> None:
        dois = self.chk_composto.isChecked()
        sab = self.rb_sabores.isChecked()
        self.comp_1.setEnabled(dois)
        self.comp_2.setEnabled(dois)
        self.nome_familia.setEnabled(sab)
        for c in self.chks_sabores:
            c.setEnabled(sab)

    # compat com o chamador antigo (B3.2)
    _habilitar_composto = _habilitar_multi

    def componentes_finais(self) -> list[str]:
        """B3.2/J13: os DOIS nomes confirmados pelo humano — [] quando
        a resposta não é "2 produtos" ou algum campo ficou vazio."""
        if not self.chk_composto.isChecked():
            return []
        a = self.comp_1.text().strip()
        b = self.comp_2.text().strip()
        return [a, b] if a and b else []

    def sabores_finais(self) -> tuple[str, list[str]] | None:
        """J13: (nome da família, sabores MARCADOS) quando a resposta é
        "são sabores" — None nas demais respostas ou sem 2+ marcados."""
        if not self.rb_sabores.isChecked():
            return None
        nome = self.nome_familia.text().strip()
        marcados = [c.text() for c in self.chks_sabores if c.isChecked()]
        return (nome, marcados) if nome and len(marcados) >= 2 else None

    def mais18_final(self) -> bool:
        return self.chk_mais18.isChecked()

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
        tem = bool(self.lista.selectedItems())
        self.usar.setEnabled(tem)
        self.btn_ajustar.setEnabled(tem)
        self.btn_refinar.setEnabled(tem)

    def _trocar_candidato(self, novo_caminho: str) -> None:
        """#46: o candidato selecionado passa a apontar para a versão
        arrumada (miniatura e UserRole atualizados juntos — I1)."""
        sel = self.lista.selectedItems()
        if not sel or not novo_caminho:
            return
        item = sel[0]
        pm = QPixmap(novo_caminho)
        if pm.isNull():
            return
        item.setData(Qt.ItemDataRole.UserRole, novo_caminho)
        item.setIcon(pm.scaled(_MINIATURA, _MINIATURA,
                               Qt.AspectRatioMode.KeepAspectRatio,
                               Qt.TransformationMode.SmoothTransformation))
        item.setToolTip(f"{pm.width()}×{pm.height()} (arrumada)")

    def _ajustar_candidato(self) -> None:
        """#46: girar/espelhar/cortar o candidato antes de usar."""
        sel = self.lista.selectedItems()
        if not sel:
            return
        from app.qt.telas.ajuste_imagem_dialog import AjusteImagemDialog
        dlg = AjusteImagemDialog(sel[0].data(Qt.ItemDataRole.UserRole), self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self._trocar_candidato(dlg.caminho_final())

    def _refinar_candidato(self) -> None:
        """#46: o pincel de refino no candidato antes de usar."""
        sel = self.lista.selectedItems()
        if not sel:
            return
        from app.qt.telas.refino_dialog import RefinoDialog
        dlg = RefinoDialog(sel[0].data(Qt.ItemDataRole.UserRole), self)
        if dlg.exec() == QDialog.DialogCode.Accepted and dlg.caminho_final:
            self._trocar_candidato(dlg.caminho_final)

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

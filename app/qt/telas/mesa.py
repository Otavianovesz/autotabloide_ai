"""
Mesa — a montagem do tabloide (F6.4, primeira fatia do Bloco D)
===============================================================
O fluxo que o Otaviano faz hoje na mão, pela interface:

    Importar tabela/foto → conciliação (semáforo) → auto-preencher → exportar.

Usa o layout de grade aberto (Belo Brasil), o canvas WYSIWYG do editor, e o
motor que já existe (OCR, conciliação, enriquecimento, ddgs, rembg, Pillow).
Trabalho pesado em worker (overlay; a UI não congela); degrada com elegância.
"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.qt.canvas import EditorCanvas
from app.qt.design import tokens as t
from app.qt.design.carregando import OverlayOcupado
from app.qt.design.componentes import EstadoVazio, Painel
from app.qt.design.icones import icone
from app.qt.design.toast import mostrar_toast
from app.qt.telas import servico
from app.qt.telas.conciliacao_dialog import ConciliacaoDialog
from app.qt.workers import GerenciadorTrabalhos, Trabalhador
from app.rendering.compositor import DadosProduto, compor_pagina

_COR = {"VERDE": t.SUCESSO, "AMARELO": t.ALERTA, "VERMELHO": t.PERIGO}


class MesaTela(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._layout = None
        self._fundo = None
        self._layout_nome = "Tabloide Belo Brasil"
        self._itens: list[servico.ItemMesa] = []
        # o mapa slot→uid mora no CANVAS (D5: undo versiona {layout, mapa});
        # aqui, `_mapa` é um proxy — ver a property abaixo
        self._validade: str | None = None
        self._registro_selos: list[dict] = []   # RG-33: cache por recomposição
        self._trabalhos = GerenciadorTrabalhos()
        self.ao_salvo = None           # callable(bool) → indicador do rodapé
        self.ao_documento = None       # callable(str) → título da janela (77)
        self._projeto_id = None        # FASE 2 (passo 36): status por projeto

        # --- barra de ações da Mesa -------------------------------------------
        barra = QWidget()
        barra.setObjectName("barraFerramentas")
        hb = QHBoxLayout(barra)
        hb.setContentsMargins(t.ESP_3, t.ESP_1 + 2, t.ESP_3, t.ESP_1 + 2)
        hb.setSpacing(t.ESP_2)
        self.btn_importar = QPushButton(" Importar tabela/foto")
        self.btn_importar.setIcon(icone("abrir", cor=t.ACENTO_TEXTO, tamanho=16))
        self.btn_importar.setProperty("tipo", "primario")
        self.btn_importar.setToolTip(
            "Foto do WhatsApp (OCR) ou tabela .txt — conciliação com o semáforo")
        self.btn_importar.clicked.connect(self._importar)
        # RG-06: desfazer/refazer NA MESA (hoje só o Ateliê tinha) — o canvas
        # já versiona {layout, mapa, overrides}; faltava o gesto
        self.btn_desfazer = QPushButton()
        self.btn_desfazer.setIcon(icone("desfazer", tamanho=16))
        self.btn_desfazer.setFixedWidth(30)
        self.btn_desfazer.setToolTip("Desfazer · Ctrl+Z")
        self.btn_desfazer.clicked.connect(self.desfazer)
        self.btn_refazer = QPushButton()
        self.btn_refazer.setIcon(icone("refazer", tamanho=16))
        self.btn_refazer.setFixedWidth(30)
        self.btn_refazer.setToolTip("Refazer · Ctrl+Y")
        self.btn_refazer.clicked.connect(self.refazer)
        btn_banco = QPushButton(" Do banco")
        btn_banco.setIcon(icone("caixa", tamanho=16))
        btn_banco.setToolTip("Importar do catálogo com busca e multi-seleção")
        btn_banco.clicked.connect(self._importar_do_banco)
        self.btn_preencher = QPushButton(" Auto-preencher")
        self.btn_preencher.setIcon(icone("grade", tamanho=16))
        self.btn_preencher.setToolTip("Preencher a grade na ordem importada")
        self.btn_preencher.setEnabled(False)
        self.btn_preencher.clicked.connect(self._auto_preencher)
        # RG-03: completar as fotos DEPOIS, em fila (a dinâmica "editar
        # primeiro, fotos depois" do dono)
        self.btn_fotos_lote = QPushButton(" Buscar fotos em lote")
        self.btn_fotos_lote.setIcon(icone("imagem", tamanho=16))
        self.btn_fotos_lote.setToolTip(
            "Percorre os itens SEM foto, um a um: busca candidatos, você "
            "escolhe, o fundo é removido — com a fila visível no título")
        self.btn_fotos_lote.setEnabled(False)
        self.btn_fotos_lote.clicked.connect(self._fotos_em_lote)
        # F8/A2: agrupar por categoria = SÓ ordenação prévia (padrão: desligado)
        from PySide6.QtWidgets import QCheckBox
        self.chk_agrupar = QCheckBox("Agrupar por categoria")
        self.chk_agrupar.setToolTip(
            "Ao auto-preencher, ordena por categoria antes (ordem nas "
            "Configurações; “Outros” por último). O vínculo continua por item.")
        # RG-42: capa com heróis (pesquisa §1 — âncora de tráfego)
        self.chk_herois = QCheckBox("Capa com heróis")
        self.chk_herois.setToolTip(
            "Os itens mais BARATOS abrem a página 1 (âncora de tráfego — a "
            "prática do Quintou com a abóbora a 0,19); o resto segue a ordem")
        self.btn_exportar = QPushButton(" Exportar")
        self.btn_exportar.setIcon(icone("salvar", tamanho=16))
        self.btn_exportar.setToolTip(
            "Exportar o tabloide em PNG ou PDF  ·  Ctrl+E")
        self.btn_exportar.setEnabled(False)
        self.btn_exportar.clicked.connect(self._exportar)
        self.btn_salvar_proj = QPushButton(" Salvar projeto")
        self.btn_salvar_proj.setIcon(icone("cofre", tamanho=16))
        self.btn_salvar_proj.setToolTip(
            "Congela o tabloide (dados da época) — reabre idêntico  ·  Ctrl+S")
        self.btn_salvar_proj.setEnabled(False)
        self.btn_salvar_proj.clicked.connect(self._salvar_projeto)
        btn_abrir_proj = QPushButton(" Abrir projeto")
        btn_abrir_proj.setIcon(icone("abrir", tamanho=16))
        btn_abrir_proj.setToolTip("Abrir um projeto congelado  ·  Ctrl+O")
        btn_abrir_proj.clicked.connect(self._abrir_projeto)
        # navegação de páginas (D8.4) — aparece quando o layout tem 2+
        self._btn_pag_ant = QPushButton("‹")
        self._btn_pag_ant.setFixedWidth(28)
        self._btn_pag_ant.clicked.connect(
            lambda: self._ir_pagina(self.area.canvas.pagina_atual - 1))
        self._pag_lbl = QLabel("1/1")
        self._pag_lbl.setProperty("papel", "legenda")
        self._btn_pag_prox = QPushButton("›")
        self._btn_pag_prox.setFixedWidth(28)
        self._btn_pag_prox.clicked.connect(
            lambda: self._ir_pagina(self.area.canvas.pagina_atual + 1))
        # F8.2/B3: DIY por página — desligar seções e editar títulos
        self.chk_secoes_pag = QCheckBox("Seções nesta página")
        self.chk_secoes_pag.setToolTip("Liga/desliga o contorno de categoria "
                                       "SÓ na página atual")
        self.chk_secoes_pag.toggled.connect(self._secoes_da_pagina)
        self.btn_titulos = QPushButton(" Títulos…")
        self.btn_titulos.setIcon(icone("texto", tamanho=14))
        self.btn_titulos.setToolTip("Editar o título de uma seção desta "
                                    "página (ex.: “Limpeza” → “Casa Limpa”)")
        self.btn_titulos.clicked.connect(self._editar_titulo_secao)
        self._validade_lbl = QLabel("")
        self._validade_lbl.setProperty("papel", "legenda")
        # RG-34: clique no rótulo edita a validade DA OFERTA (de/até)
        self._validade_lbl.setToolTip(
            "Clique para editar a validade da OFERTA (de/até) — separada da "
            "validade de cada item (que é a do cartaz)")
        self._validade_lbl.setCursor(Qt.CursorShape.PointingHandCursor)
        self._validade_lbl.mousePressEvent = \
            lambda _ev: self._editar_validade_oferta()
        # RG-53: barra por GRUPOS na ordem do fluxo, com separador visível —
        # o dono acha o botão pela função. Desfazer/refazer abrem; depois
        # Importar · Montar · Salvar/Exportar · Navegar páginas.
        def _sep_barra():
            from PySide6.QtWidgets import QFrame
            f = QFrame()
            f.setProperty("papel", "separador")
            f.setFrameShape(QFrame.Shape.VLine)
            return f

        self._seps_barra = []
        for grupo in (
            [self.btn_desfazer, self.btn_refazer],
            [self.btn_importar, btn_banco],
            [self.btn_preencher, self.btn_fotos_lote,
             self.chk_agrupar, self.chk_herois],
            [self.btn_exportar, self.btn_salvar_proj, btn_abrir_proj],
            [self._btn_pag_ant, self._pag_lbl, self._btn_pag_prox,
             self.chk_secoes_pag, self.btn_titulos],
        ):
            if hb.count() > 0:
                sep = _sep_barra()
                self._seps_barra.append(sep)
                hb.addWidget(sep)
            for w in grupo:
                hb.addWidget(w)
        # FASE 1 (passo 58): "···" herda o que não couber (nada some)
        from PySide6.QtWidgets import QMenu, QToolButton
        self._mais_mesa = QToolButton()
        self._mais_mesa.setText("···")
        self._mais_mesa.setToolTip("Mais ações (janela estreita)")
        self._mais_mesa.setPopupMode(
            QToolButton.ToolButtonPopupMode.InstantPopup)
        self._mais_mesa.setMenu(QMenu(self._mais_mesa))
        self._mais_mesa.hide()
        hb.addWidget(self._mais_mesa)
        hb.addStretch(1)
        # R-061 (Fase 6): indicador discreto "rascunho salvo HH:MM"
        self._rascunho_lbl = QLabel("")
        self._rascunho_lbl.setProperty("papel", "legenda")
        self._rascunho_lbl.setToolTip("Rascunho automático — rede de segurança; "
                                      "não substitui salvar o projeto")
        hb.addWidget(self._rascunho_lbl)
        # R-072 (Fase 7): estatística DISCRETA da montagem (local, offline — sem
        # telemetria). O detalhe (itens/min) mora no tooltip.
        self._t_inicio = None
        self._estatistica_lbl = QLabel("")
        self._estatistica_lbl.setProperty("papel", "legenda")
        hb.addWidget(self._estatistica_lbl)
        # OS F11.5 #42/43 (RG-42): o medidor de densidade fica SEMPRE visível
        # na barra (não só o toast de >90%) — verde com respiro, âmbar cheia,
        # vermelho espremida; a página atual é a medida.
        self._densidade_lbl = QLabel("")
        self._densidade_lbl.setProperty("papel", "legenda")
        self._densidade_lbl.setToolTip(
            "Quanto da página está ocupado por produto (pesquisa 60-30-10: "
            "respiro valoriza as ofertas). Verde ≤70% · âmbar ≤90% · "
            "vermelho >90%")
        hb.addWidget(self._densidade_lbl)
        hb.addWidget(self._validade_lbl)
        self._barra_mesa = barra
        self._barra_layout = hb
        # RG-53 (o conserto do "botões se comendo"): a barra PODE encolher
        # abaixo do conteúdo — senão o window fica preso na largura do conteúdo
        # (~1757px) e a 1280 real transborda, e o reflow nunca dispara.
        barra.setMinimumWidth(1)
        # ordem de sacrifício (o PRIMEIRO da lista é o primeiro a colapsar)
        self._sacrificaveis = [
            (self.btn_titulos, "Títulos das seções…", "botao"),
            (self.chk_secoes_pag, "Seções nesta página", "check"),
            (self.chk_herois, "Capa com heróis", "check"),
            (self.chk_agrupar, "Agrupar por categoria", "check"),
            (btn_abrir_proj, "Abrir projeto", "botao"),
            (self.btn_fotos_lote, "Buscar fotos em lote", "botao"),
        ]

        # --- corpo: canvas + itens ----------------------------------------------
        self.area = EditorCanvas()

        self.lista = QListWidget()
        self.lista.setVerticalScrollMode(QListWidget.ScrollMode.ScrollPerPixel)
        self.lista.itemDoubleClicked.connect(self._editar_item)
        # F7.1: botão direito no item → fotos (sabores) + edição rápida
        self.lista.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.lista.customContextMenuRequested.connect(self._menu_item)
        # FASE 1 (passo 73): estado vazio com AÇÃO — o próximo passo a 1 clique
        btn_vazio = QPushButton(" Importar tabela/foto")
        btn_vazio.setIcon(icone("abrir", tamanho=16))
        btn_vazio.clicked.connect(self._importar)
        self._vazio = EstadoVazio(
            "caixa", "Nenhuma oferta importada",
            "Importe a foto do WhatsApp ou a tabela\n"
            "para começar o tabloide.", acao=btn_vazio)
        caixa_itens = QWidget()
        vi = QVBoxLayout(caixa_itens)
        vi.setContentsMargins(0, 0, 0, 0)
        # R-051 (Fase 6): editar tudo de uma vez numa grade (só teclado)
        self.btn_planilha = QPushButton(" Modo planilha")
        self.btn_planilha.setIcon(icone("propriedades", tamanho=14))
        self.btn_planilha.setToolTip(
            "Editar nome, preço, unidade e categoria de todos os itens numa "
            "grade, só com o teclado")
        self.btn_planilha.setEnabled(False)
        self.btn_planilha.clicked.connect(self._abrir_planilha)
        vi.addWidget(self.btn_planilha)
        # R-054 (Fase 6): barra de filtros da estante (combináveis, com chip)
        from PySide6.QtWidgets import QLineEdit
        self._filtro_barra = QWidget()
        fbl = QHBoxLayout(self._filtro_barra)
        fbl.setContentsMargins(0, 0, 0, 0)
        fbl.setSpacing(t.ESP_1)
        self.chk_sem_foto = QCheckBox("Sem foto")
        self.chk_sem_preco = QCheckBox("Sem preço")
        self.chk_sem_foto.toggled.connect(self._aplicar_filtro)
        self.chk_sem_preco.toggled.connect(self._aplicar_filtro)
        # OS F11.5 #31: filtro por CATEGORIA na barra (o motor sempre aceitou)
        from PySide6.QtWidgets import QComboBox as _QCB
        self.filtro_categoria = _QCB()
        self.filtro_categoria.addItem("Todas")
        self.filtro_categoria.setToolTip("Mostrar só uma categoria")
        self.filtro_categoria.currentTextChanged.connect(
            lambda _t: self._aplicar_filtro())
        self.campo_busca = QLineEdit()
        self.campo_busca.setPlaceholderText("Buscar por nome…")
        self.campo_busca.setClearButtonEnabled(True)
        self.campo_busca.textChanged.connect(self._aplicar_filtro)
        # OS F11.5 #33: limpar TODOS os filtros num clique
        self.btn_limpar_filtros = QPushButton("Limpar")
        self.btn_limpar_filtros.setToolTip("Limpa todos os filtros (1 clique)")
        self.btn_limpar_filtros.clicked.connect(self._limpar_filtros)
        fbl.addWidget(self.chk_sem_foto)
        fbl.addWidget(self.chk_sem_preco)
        fbl.addWidget(self.filtro_categoria)
        fbl.addWidget(self.campo_busca, 1)
        fbl.addWidget(self.btn_limpar_filtros)
        self._chip_filtro = QLabel("")
        self._chip_filtro.setProperty("papel", "legenda")
        # OS F11.5 #43: o PULSO da estante ("· 12 sem foto · 3 sem preço")
        self._pulso_filtro = QLabel("")
        self._pulso_filtro.setProperty("papel", "legenda")
        vi.addWidget(self._filtro_barra)
        vi.addWidget(self._pulso_filtro)
        vi.addWidget(self._chip_filtro)
        # OS F11.5 #40: estado vazio DE FILTRO (nada passou — limpar)
        from app.qt.design.componentes import EstadoVazio as _EV
        self._vazio_filtro = _EV(
            "busca", "Nada passa nesse filtro",
            "Ajuste os filtros ou limpe-os para ver a estante inteira.")
        self._vazio_filtro.hide()
        vi.addWidget(self._vazio_filtro)
        self._filtro_barra.hide()
        vi.addWidget(self._vazio)
        vi.addWidget(self.lista)
        self.lista.hide()
        # R-055: reordenar a estante arrastando (InternalMove); ao soltar,
        # o mapa slot→uid segue a nova ordem por uid (I1)
        self.lista.setDragDropMode(QListWidget.DragDropMode.InternalMove)
        self.lista.model().rowsMoved.connect(self._estante_reordenada)
        # OS F11.5 #44: MULTI-seleção na estante — excluir/duplicar operam
        # no BLOCO selecionado (por uid, nunca por posição)
        from PySide6.QtWidgets import QAbstractItemView
        self.lista.setSelectionMode(
            QAbstractItemView.SelectionMode.ExtendedSelection)

        # RG-07: gestão da estante — limpar tudo (cabeçalho) + contagem viva
        btn_limpar = QPushButton()
        btn_limpar.setIcon(icone("lixeira", tamanho=14))
        btn_limpar.setFixedSize(28, 28)   # passo 50: alvo de clique digno
        btn_limpar.setToolTip("Limpar a estante (remove todos os itens)")
        btn_limpar.clicked.connect(self._limpar_estante)
        lateral = QWidget()
        lateral.setObjectName("lateral")
        vl = QVBoxLayout(lateral)
        vl.setContentsMargins(t.ESP_3, t.ESP_3, t.ESP_3, t.ESP_3)
        self._painel_itens = Painel("Itens da oferta", "caixa", caixa_itens,
                                    acao=btn_limpar)
        vl.addWidget(self._painel_itens)

        # FASE 1 (passo 59): a estante vira splitter com memória (mín. 300)
        from app.qt.design.componentes import splitter_com_memoria
        corpo = splitter_com_memoria("mesa", self.area, lateral,
                                     indice_lateral=1)

        raiz = QVBoxLayout(self)
        raiz.setContentsMargins(0, 0, 0, 0)
        raiz.setSpacing(0)
        raiz.addWidget(barra)
        raiz.addWidget(corpo, 1)

        self._overlay = OverlayOcupado(self)
        # pós-undo/remoção de célula: o canvas avisa e a Mesa realimenta os dados
        self.area.canvas.ao_restaurar = self._pos_undo
        # F7.3: botão direito numa célula → modal de override (só na Mesa)
        self.area.canvas.ao_override = self._abrir_override
        # R-038: arrastar um PNG/JPG sobre a célula troca a foto do item (uid)
        self.area.canvas.ao_soltar_imagem = self._soltar_imagem

        # RG-06: atalhos de desfazer/refazer valendo na Mesa inteira
        from PySide6.QtGui import QKeySequence, QShortcut
        # FASE 1 (passo 68): os atalhos anunciados nos tooltips EXISTEM —
        # e respeitam o estado do botão (Ctrl+E sem itens não exporta nada)
        def _se_ativo(botao, acao):
            return lambda: acao() if botao.isEnabled() else None

        # R-018: teclas do catálogo central (remapeáveis na aba Atalhos)
        from app.qt.design.atalhos import criar_atalho
        for id_atalho, acao in [("mesa.desfazer", self.desfazer),
                                ("mesa.refazer", self.refazer),
                                ("mesa.exportar", _se_ativo(self.btn_exportar,
                                                            self._exportar)),
                                ("mesa.salvar",
                                 _se_ativo(self.btn_salvar_proj,
                                           self._salvar_projeto)),
                                ("mesa.abrir", self._abrir_projeto)]:
            criar_atalho(id_atalho, self, acao)
        # Ctrl+Shift+Z segue espelho FIXO do refazer (convenção)
        sc_rf = QShortcut(QKeySequence("Ctrl+Shift+Z"), self)
        sc_rf.setContext(Qt.ShortcutContext.WidgetWithChildrenShortcut)
        sc_rf.activated.connect(self.refazer)
        # RG-07: Del com o foco NA ESTANTE exclui o item selecionado (o Del
        # do canvas continua excluindo região — contextos separados)
        sc_del = QShortcut(QKeySequence(Qt.Key.Key_Delete), self.lista)
        sc_del.setContext(Qt.ShortcutContext.WidgetShortcut)
        sc_del.activated.connect(self._excluir_item_selecionado)

    # --- desfazer/refazer (RG-06) ---------------------------------------------------

    def desfazer(self) -> None:
        if not self.area.canvas.desfazer():
            mostrar_toast(self, "Nada para desfazer.")

    def refazer(self) -> None:
        if not self.area.canvas.refazer():
            mostrar_toast(self, "Nada para refazer.")

    # --- validade da OFERTA (RG-34) -------------------------------------------------

    def _editar_validade_oferta(self) -> None:
        """De/até PRÓPRIOS da oferta ("OFERTA VÁLIDA DE 17/07 ATÉ 24/07")."""
        from PySide6.QtWidgets import QInputDialog

        de, ok = QInputDialog.getText(
            self, "Validade da oferta",
            "Início (dd/mm — vazio para só “ATÉ”):",)
        if not ok:
            return
        ate, ok = QInputDialog.getText(
            self, "Validade da oferta", "Fim (dd/mm):")
        if not ok:
            return
        self._validade = servico.montar_validade_oferta(de, ate)
        self._validade_lbl.setText(
            f"Validade: {self._validade}" if self._validade else "")
        self._marcar_salvo(False)
        if self._mapa:
            self.area.canvas.atualizar_dados(self._dados_por_slot())
            self.area.canvas.viewport().update()

    # --- gestão da estante (RG-07) --------------------------------------------------

    def _excluir_item_selecionado(self) -> None:
        # OS F11.5 #44: com MULTI-seleção, exclui o bloco inteiro (de trás
        # para frente, para os índices não escorregarem; cada exclusão segue
        # tendo o "Desfazer" do toast por uid)
        linhas = sorted({ix.row() for ix in self.lista.selectedIndexes()},
                        reverse=True)
        if not linhas:
            linha = self.lista.currentRow()
            linhas = [linha] if 0 <= linha < len(self._itens) else []
        for linha in linhas:
            if 0 <= linha < len(self._itens):
                self._excluir_item(linha)

    def _excluir_item(self, linha: int) -> None:
        """Tira o item da estante; a célula dele (se houver) esvazia à vista.

        Gesto de DADOS, como compor/importar: não entra no undo do canvas —
        o inverso explícito agora é o "Desfazer" do toast (FASE 1, 71-72),
        que devolve o item À MESMA linha com os vínculos por uid (I1).
        """
        it = self._itens.pop(linha)
        orfaos = [sid for sid, uid in self._mapa.items() if uid == it.uid]
        vinculos = {sid: it.uid for sid in orfaos}
        for sid in orfaos:
            self._mapa.pop(sid, None)
        # atualizar_dados preserva o histórico do canvas (carregar o zeraria)
        self.area.canvas.atualizar_dados(self._dados_por_slot())
        self.area.canvas.viewport().update()
        self._recarregar_lista()
        self.btn_exportar.setEnabled(bool(self._mapa))
        self._marcar_salvo(False)
        onde = " (a célula dela esvaziou)" if orfaos else ""
        from app.qt.design.toast import mostrar_toast_desfazer
        mostrar_toast_desfazer(
            self, f"“{it.nome}” saiu da estante{onde}.",
            lambda: self._restaurar_estante_parcial(linha, it, vinculos))

    def _restaurar_estante_parcial(self, linha: int, it, vinculos: dict) -> None:
        """O Desfazer do toast: item de volta na linha, vínculos por uid."""
        self._itens.insert(min(linha, len(self._itens)), it)
        self._mapa.update(vinculos)
        self.area.canvas.atualizar_dados(self._dados_por_slot())
        self.area.canvas.viewport().update()
        self._recarregar_lista()
        self.btn_exportar.setEnabled(bool(self._mapa))
        self.btn_preencher.setEnabled(bool(self._itens))
        self._marcar_salvo(False)

    def _limpar_estante(self) -> None:
        if not self._itens:
            mostrar_toast(self, "A estante já está vazia.")
            return
        from app.qt.design.componentes import confirmar_destrutivo
        if not confirmar_destrutivo(              # passo 78: verbo no botão
                self, "Limpar estante",
                f"Tirar TODOS os {len(self._itens)} itens da estante? "
                "(o banco não é tocado — só este tabloide)",
                f"Limpar {len(self._itens)} item(ns)"):
            return
        copia_itens, copia_mapa = list(self._itens), dict(self._mapa)
        self._itens = []
        self._mapa = {}
        self.area.canvas.atualizar_dados({})
        self.area.canvas.viewport().update()
        self._recarregar_lista()
        self.btn_exportar.setEnabled(False)
        self.btn_preencher.setEnabled(False)
        self._marcar_salvo(False)
        from app.qt.design.toast import mostrar_toast_desfazer
        mostrar_toast_desfazer(
            self, f"{len(copia_itens)} item(ns) fora da estante.",
            lambda: self._restaurar_estante_toda(copia_itens, copia_mapa))

    def _restaurar_estante_toda(self, itens: list, mapa: dict) -> None:
        """O Desfazer do toast de limpar: estante e vínculos de volta."""
        self._itens = list(itens)
        self._mapa = dict(mapa)
        self.area.canvas.atualizar_dados(self._dados_por_slot())
        self.area.canvas.viewport().update()
        self._recarregar_lista()
        self.btn_exportar.setEnabled(bool(self._mapa))
        self.btn_preencher.setEnabled(bool(self._itens))
        self._marcar_salvo(False)
        mostrar_toast(self, "Estante limpa — o banco continua intacto.")

    # --- mapa slot→uid (proxy do canvas — D5) --------------------------------------

    @property
    def _mapa(self) -> dict:
        return self.area.canvas.mapa

    @_mapa.setter
    def _mapa(self, valor: dict) -> None:
        self.area.canvas.mapa = dict(valor)

    # --- overrides por slot (proxy do canvas — F7.3, versiona com o undo) ----------

    @property
    def _overrides(self) -> dict:
        return self.area.canvas.overrides

    @_overrides.setter
    def _overrides(self, valor: dict) -> None:
        self.area.canvas.overrides = dict(valor)

    def _abrir_override(self, slot_id: str) -> None:
        """B1: o modal edita UMA célula sem tocar no item da estante."""
        from app.qt.telas.override_dialog import OverrideDialog

        uid = self._mapa.get(slot_id)
        it = next((i for i in self._itens if i.uid == uid), None)
        if it is None:
            mostrar_toast(self, "Esta célula não tem item — preencha a grade "
                                "antes de sobrepor o conteúdo.", tipo="erro")
            return
        dlg = OverrideDialog(it, self._overrides.get(slot_id), self)
        if dlg.exec() != OverrideDialog.DialogCode.Accepted:
            return
        ov = dlg.valores()
        self.area.canvas.set_override(slot_id, ov or None)
        self._marcar_salvo(False)
        mostrar_toast(self, "Override aplicado só nesta célula."
                      if ov else "Célula voltou a seguir o item.")

    def _soltar_imagem(self, slot_id: str, caminho: str) -> None:
        """R-038: uma foto solta sobre a célula troca a imagem do ITEM daquele
        slot (override de conteúdo, POR uid — I1), com aviso de substituição."""
        uid = self._mapa.get(slot_id)
        it = next((i for i in self._itens if i.uid == uid), None)
        if it is None:
            mostrar_toast(self, "Esta célula não tem item — preencha a grade "
                                "antes de trocar a foto.", tipo="erro")
            return
        from app.qt.design.componentes import confirmar_destrutivo
        nome = (it.nome or it.descricao or "este item").strip()
        if not confirmar_destrutivo(
                self, "Trocar a foto?",
                f"Substituir a foto de “{nome}” pela imagem arrastada "
                "(só nesta célula)?", "Trocar"):
            return
        ov = dict(self._overrides.get(slot_id) or {})
        ov["imagem"] = str(caminho)
        self.area.canvas.set_override(slot_id, ov)
        self._marcar_salvo(False)
        mostrar_toast(self, f"Foto de “{nome}” trocada nesta célula.")

    def _pos_undo(self) -> None:
        """Undo restaurou {layout, mapa}: recompõe os dados e a estante."""
        self._layout = self.area.canvas._layout or self._layout
        self.area.canvas.atualizar_dados(self._dados_por_slot(), compor=False)
        self._recarregar_lista()
        self._atualizar_nav()
        self._marcar_salvo(False)

    # --- navegação de páginas (D8.4) ------------------------------------------------

    def _ir_pagina(self, i: int) -> None:
        self.area.canvas.atualizar_dados(self._dados_por_slot(), compor=False)
        self.area.canvas.ir_para_pagina(i)
        self._atualizar_nav()

    def _atualizar_nav(self) -> None:
        c = self.area.canvas
        total = max(1, c.total_paginas())
        self._pag_lbl.setText(f"{c.pagina_atual + 1}/{total}")
        varias = total > 1
        for w in (self._btn_pag_ant, self._pag_lbl, self._btn_pag_prox):
            w.setVisible(varias)
        # F8.2: o checkbox reflete a PÁGINA atual (sem disparar o handler)
        if self._layout is not None and self._layout.paginas:
            pag = self._layout.paginas[min(c.pagina_atual,
                                           len(self._layout.paginas) - 1)]
            self.chk_secoes_pag.blockSignals(True)
            self.chk_secoes_pag.setChecked(pag.secoes_ligadas)
            self.chk_secoes_pag.blockSignals(False)
        self._atualizar_densidade()

    def _atualizar_densidade(self) -> None:
        """OS F11.5 #42/43: o número da densidade da página ATUAL, colorido por
        faixa. Some quando não há montagem (sem mapa) — sem mostrar 0% inútil."""
        pag = self._pagina_atual()
        if pag is None or not self._mapa:
            self._densidade_lbl.setText("")
            return
        try:
            d = servico.densidade_da_pagina(pag, self._dados_por_slot())
        except Exception:
            self._densidade_lbl.setText("")
            return
        if d > 0.9:
            cor, rotulo = t.PERIGO, "espremida"
        elif d > 0.7:
            cor, rotulo = t.ALERTA, "cheia"
        else:
            cor, rotulo = t.SUCESSO, "com respiro"
        self._densidade_lbl.setText(f"● {round(d * 100)}% {rotulo}")
        self._densidade_lbl.setStyleSheet(f"color: {cor};")

    # --- seções por página (F8.2/B3) ------------------------------------------------

    def _pagina_atual(self):
        i = self.area.canvas.pagina_atual
        pags = self._layout.paginas if self._layout else []
        return pags[i] if 0 <= i < len(pags) else None

    def _secoes_da_pagina(self, ligado: bool) -> None:
        pag = self._pagina_atual()
        if pag is None:
            return
        pag.secoes_ligadas = ligado
        self.area.canvas.atualizar_dados(self._dados_por_slot())
        self._marcar_salvo(False)

    def _editar_titulo_secao(self) -> None:
        """B3: título editável por seção, por página."""
        from PySide6.QtWidgets import QInputDialog

        pag = self._pagina_atual()
        if pag is None:
            return
        por_uid = {it.uid: it for it in self._itens}
        ids_pag = {s.id for s in pag.slots}
        categorias = sorted({(por_uid[u].categoria or "").strip() or "Outros"
                             for sid, u in self._mapa.items()
                             if sid in ids_pag and u in por_uid})
        if not categorias:
            mostrar_toast(self, "Nenhuma seção nesta página — preencha a "
                                "grade agrupada antes.", tipo="erro")
            return
        cat, ok = QInputDialog.getItem(self, "Título da seção",
                                       "Qual seção?", categorias, 0, False)
        if not ok:
            return
        atual = (pag.titulos_secoes or {}).get(cat, cat)
        titulo, ok = QInputDialog.getText(self, "Título da seção",
                                          f"Título para “{cat}”:", text=atual)
        if not ok:
            return
        titulo = titulo.strip()
        if titulo and titulo != cat:
            pag.titulos_secoes[cat] = titulo
        else:
            pag.titulos_secoes.pop(cat, None)   # vazio/igual = volta ao padrão
        self.area.canvas.atualizar_dados(self._dados_por_slot())
        self._marcar_salvo(False)

    # --- layout aberto -----------------------------------------------------------

    def carregar_layout(self, layout, fundo_path: str | None,
                        nome_layout: str | None = None) -> None:
        """Usa o layout de grade aberto (ex.: Belo Brasil, 15 células)."""
        import json
        self._layout = layout
        self._fundo = fundo_path
        if nome_layout:
            self._layout_nome = nome_layout
        # RG-08: assinatura do documento carregado — o showEvent compara com
        # o banco e re-sincroniza se o Ateliê editou este layout
        self._assinatura_layout = json.dumps(layout.to_dict(), sort_keys=True)
        self._congelado = False
        self.area.carregar(layout, [], fundo_path)
        self._atualizar_nav()

    def showEvent(self, ev) -> None:  # noqa: N802 (Qt)
        super().showEvent(ev)
        self._sincronizar_do_atelie()
        self._reflow_barra()
        # R-061: uma vez, ao abrir a Mesa — oferece recuperar rascunho de queda
        # e liga o timer do rascunho automático (~2 min).
        if not getattr(self, "_rascunho_iniciado", False):
            self._rascunho_iniciado = True
            self._oferecer_recuperacao()
            from PySide6.QtCore import QTimer
            self._timer_rascunho = QTimer(self)
            self._timer_rascunho.setInterval(120_000)   # ~2 min
            self._timer_rascunho.timeout.connect(self._salvar_rascunho_bg)
            self._timer_rascunho.start()
            # R-017: Ctrl+K abre a paleta de busca/comando também na Mesa
            from PySide6.QtGui import QKeySequence, QShortcut
            sc = QShortcut(QKeySequence("Ctrl+K"), self)
            sc.activated.connect(self._abrir_paleta)
            # R-050: Ctrl+V cola uma tabela do WhatsApp/Excel (prévia + criar)
            sc_v = QShortcut(QKeySequence.StandardKey.Paste, self)
            sc_v.activated.connect(self._colar_tabela)

    def resizeEvent(self, ev) -> None:  # noqa: N802 (Qt)
        super().resizeEvent(ev)
        self._reflow_barra()

    def closeEvent(self, ev) -> None:  # noqa: N802 (Qt)
        """Encerra os PRÓPRIOS recursos ao fechar (lei "verde com crash no exit
        NÃO é verde", F7.1): para o timer do rascunho e encerra os workers
        desta Mesa — nenhuma QThread/QTimer vivo no teardown (segfault)."""
        timer = getattr(self, "_timer_rascunho", None)
        if timer is not None:
            timer.stop()
        try:
            self._trabalhos.encerrar(espera_ms=1000)
        except Exception:
            pass
        super().closeEvent(ev)

    def _reflow_barra(self) -> None:
        """FASE 1 (passo 58): o que couber com 8 px de folga fica na barra;
        o resto colapsa no "···" (checkbox vira ação checável espelhada —
        nada some, nada é cortado)."""
        if not hasattr(self, "_mais_mesa"):
            return
        if self._barra_mesa.width() < 60:
            return          # layout ainda não assentou — medir agora colapsaria
                            # tudo por largura falsa (o resize sintético re-chama)
        esp = t.ESP_2
        sacrificaveis = {id(w) for w, _r, _t in self._sacrificaveis}
        # RG-53: a base é TODO widget fixo da barra (botões, CHECKBOXES,
        # rótulos, separadores, ‹ ›) — não só QPushButton (a medição antiga
        # ignorava os checks e por isso subestimava a largura ocupada).
        base = 2 * t.ESP_3 + esp + self._mais_mesa.sizeHint().width() + esp
        lay = self._barra_layout
        for i in range(lay.count()):
            w = lay.itemAt(i).widget()
            if w is None or w is self._mais_mesa or id(w) in sacrificaveis:
                continue
            base += w.sizeHint().width() + esp
        # folga 24 (era 8): a régua independente do GATE 2.2 flagrou botão
        # espremido 4px a 1280 — a soma de sizeHints subestima as margens
        # internas do layout; a folga maior garante que ninguém encolhe.
        resto = self._barra_mesa.width() - 24 - base
        ficam: list[int] = []
        colapsados = []
        # os MAIS importantes (fim da lista) entram primeiro
        for w, rotulo, tipo in reversed(self._sacrificaveis):
            custo = w.sizeHint().width() + esp
            if resto - custo >= 0:
                resto -= custo
                ficam.append(id(w))
            else:
                colapsados.append((w, rotulo, tipo))
        for w, _r, _t in self._sacrificaveis:
            w.setVisible(id(w) in ficam)
        menu = self._mais_mesa.menu()
        menu.clear()
        for w, rotulo, tipo in colapsados:
            if tipo == "check":
                acao = menu.addAction(rotulo)
                acao.setCheckable(True)
                acao.setChecked(w.isChecked())
                acao.toggled.connect(w.setChecked)
            else:
                # FASE 1 (passo 79): a ação herda o ícone do botão
                acao = menu.addAction(w.icon(), rotulo, w.click)
                acao.setEnabled(w.isEnabled())
        self._mais_mesa.setVisible(bool(colapsados))
        # RG-53 estágio 2 (GATE 2.2): se nem assim coube, os botões fixos
        # ficam SÓ-ÍCONE (texto → tooltip) até a largura voltar
        from app.qt.design.componentes import modo_compacto_botoes
        if not hasattr(self, "_botoes_compactos"):
            self._botoes_compactos = {}
        modo_compacto_botoes(
            lay, self._mais_mesa, sacrificaveis, self._botoes_compactos,
            self._barra_mesa.width() - 24 - 2 * t.ESP_3, esp)

    def _sincronizar_do_atelie(self) -> None:
        """RG-08: editar o layout no Ateliê reflete na Mesa ao trocar de tela.

        Projeto congelado NUNCA re-sincroniza (decisão travada: o projeto
        congela o layout da época). A estante, o mapa (por uid — I1) e os
        overrides sobrevivem: só o documento de layout é recarregado.
        """
        import json
        if getattr(self, "_congelado", False) or not self._layout_nome:
            return
        from app.core.database import Database
        from app.rendering.persistencia import carregar_layout, listar_layouts
        try:
            db = Database().init()
            try:
                with db.Session() as s:
                    row = next((r for r in listar_layouts(s)
                                if r.nome == self._layout_nome), None)
                    novo = carregar_layout(s, row.id) if row else None
            finally:
                db.engine.dispose()
        except Exception:
            return                        # sem banco (teste isolado): segue
        if novo is None:
            return
        assinatura = json.dumps(novo.to_dict(), sort_keys=True)
        if assinatura == getattr(self, "_assinatura_layout", None):
            return                        # nada mudou no Ateliê
        mapa, overrides = dict(self._mapa), dict(self._overrides)
        self.carregar_layout(novo, novo.arquivo_fundo,
                             nome_layout=self._layout_nome)
        self._mapa = mapa                 # vínculo por uid sobrevive (I1)
        self._overrides = overrides
        self._aplicar_mapa()
        self._recarregar_lista()
        mostrar_toast(self, f"Layout “{self._layout_nome}” atualizado do "
                            "Ateliê.")

    # --- projeto salvo congelado (§3.1/§6.8) --------------------------------------

    def _marcar_salvo(self, salvo: bool) -> None:
        self._salvo = salvo                  # dirty flag em memória (R-068)
        if callable(self.ao_salvo):
            self.ao_salvo(salvo)

    def _salvar_projeto(self) -> None:
        from app.core import projetos
        from app.qt.telas.projetos_dialog import SalvarProjetoDialog

        if not self._itens:
            mostrar_toast(self, "Nada para salvar — importe itens antes.", tipo="erro")
            return
        dlg = SalvarProjetoDialog(parent=self)
        if dlg.exec() != SalvarProjetoDialog.DialogCode.Accepted:
            return
        nome, evento = dlg.valores()
        # RG-24: campanha com dia fixo sugere o "ATÉ" quando não há validade
        if not self._validade:
            sugestao = servico.sugerir_validade(evento)
            if sugestao:
                self._validade = sugestao
                self._validade_lbl.setText(f"Validade: {sugestao}")
                mostrar_toast(self, f"Validade sugerida: “{sugestao}” (dia da "
                                    "campanha) — edite se precisar.")
        lay = self.area.canvas._layout or self._layout
        from app.qt.telas.prevoo import confirmar_pre_voo
        avisos = (servico.validar_composicao(lay, self._dados_por_slot())
                  + self._avisos_orfaos())
        if not confirmar_pre_voo(self, avisos, "Salvar"):
            return
        from app.qt.design.carregando import cursor_espera
        with cursor_espera():            # FASE 1 (passo 75): miniatura pesa
            self._projeto_id = projetos.salvar_projeto(
                nome, evento, "TABLOIDE", lay,
                [it.to_dict() for it in self._itens], self._validade,
                nome_layout=self._layout_nome, mapa=self._mapa,
                overrides=self._overrides)
        self._marcar_salvo(True)
        # R-061 (passo 54): salvou de verdade → o rascunho (rede) já cumpriu;
        # descarta para não reoferecer na próxima abertura.
        from app.core.rascunho import descartar_rascunhos
        descartar_rascunhos()
        self._rascunho_lbl.setText("")
        if callable(self.ao_documento):
            self.ao_documento(nome)      # título da janela (passo 77)
        mostrar_toast(self, f"Projeto “{nome}” salvo (dados congelados).")

    def _abrir_projeto(self) -> None:
        from app.core import projetos
        from app.qt.telas.projetos_dialog import AbrirProjetoDialog

        dlg = AbrirProjetoDialog(tipo="TABLOIDE", parent=self)
        if dlg.exec() != AbrirProjetoDialog.DialogCode.Accepted or dlg.projeto_id is None:
            return
        from app.qt.design.carregando import cursor_espera
        with cursor_espera():            # FASE 1 (passo 75)
            p = projetos.abrir_projeto(dlg.projeto_id)
            if p is not None:
                self.abrir_projeto_congelado(p)

    def abrir_projeto_congelado(self, p) -> None:
        """Reabre um ProjetoAberto idêntico (diálogo e Dashboard).

        O casamento slot→item vem do **mapa congelado** (I1) — nunca é
        reconstruído por posição; reordenar a estante não muda nada.
        """
        self._itens = [servico.ItemMesa.from_dict(d) for d in p.itens]
        self._projeto_id = p.id          # FASE 2 (passo 36)
        from app.core.projetos import registrar_ultimo_aberto
        registrar_ultimo_aberto(p.id)    # FASE 2 (passo 48)
        if callable(self.ao_documento):
            self.ao_documento(p.nome)    # título da janela (passo 77)
        self._validade = p.validade_oferta
        self._validade_lbl.setText(
            f"Validade: {self._validade}" if self._validade else "")
        self._overrides = {}          # nada vaza do projeto anterior (F7.3)
        self.carregar_layout(p.layout, p.layout.arquivo_fundo)
        self._mapa = dict(p.mapa) or {
            slot.id: it.uid for slot, it in
            zip(p.layout.paginas[0].slots, self._itens)}   # legado sem mapa
        self._overrides = dict(p.overrides)                # F7.3: volta junto
        # RG-08: congelado NÃO re-sincroniza com o Ateliê (decisão travada)
        self._congelado = True
        self._aplicar_mapa()
        self._recarregar_lista()
        self.btn_preencher.setEnabled(bool(self._itens))
        self.btn_salvar_proj.setEnabled(bool(self._itens))
        self.area.canvas.ajustar()      # enquadra a página reaberta
        self._marcar_salvo(True)
        mostrar_toast(self, f"“{p.nome}” aberto — congelado de {p.criado_em}.")

    # --- importar ------------------------------------------------------------------

    def _importar(self) -> None:
        # R-049 (Fase 7): multi-arquivo — abrir VÁRIAS de uma vez numa fila
        caminhos, _ = QFileDialog.getOpenFileNames(
            self, "Importar ofertas (uma ou várias)", "",
            "Ofertas (*.png *.jpg *.jpeg *.webp *.txt);;Todos (*.*)")
        if not caminhos:
            return
        if len(caminhos) == 1:
            trab = Trabalhador(
                lambda st, c=caminhos[0]: servico.importar_ofertas(c, st))
            trab.ok.connect(self._conciliar)
        else:
            # OS F11.5 #2: a janelinha da fila mostra CADA arquivo mudando de
            # estado (na fila → lendo → pronto/erro); a ponte leva o progresso
            # da thread do worker para a UI por sinal Qt (thread-safe).
            from pathlib import Path as _P

            from app.qt.telas.fila_importacao import (
                FilaImportacaoDialog, PonteFila)
            fila_dlg = FilaImportacaoDialog(
                [_P(c).name for c in caminhos], self)
            ponte = PonteFila(fila_dlg)
            ponte.mudou.connect(fila_dlg.atualizar)
            fila_dlg.show()
            trab = Trabalhador(
                lambda st, cs=caminhos, p=ponte:
                servico.importar_varios(cs, st, progresso_cb=p.mudou.emit))
            trab.ok.connect(lambda res, d=fila_dlg: (
                d.accept() if d.tudo_pronto() else None,
                self._conciliar_varios(res)))
        trab.status.connect(self._overlay.mostrar)
        trab.erro.connect(self._falhou)
        self._trabalhos.rodar(trab)

    def _conciliar_varios(self, resultado_e_erros) -> None:
        """R-049: resultado combinado da fila + avisa os arquivos com erro
        (I2, nunca em silêncio) — o resto seguiu."""
        resultado, erros = resultado_e_erros
        if erros:
            det = "; ".join(f"{n}" for n, _e in erros[:3])
            mostrar_toast(self, f"{len(erros)} arquivo(s) com erro (o resto foi "
                                f"lido): {det}", tipo="erro")
        self._conciliar(resultado)

    def _colar_tabela(self) -> None:
        """R-050 (Fase 7): Ctrl+V — cola uma tabela (WhatsApp/Excel), mostra a
        prévia "isto é o que entendi", e ao confirmar cria os itens pelo MESMO
        caminho de conciliação (reusa P0.3/RG-20)."""
        from PySide6.QtWidgets import QApplication
        texto = QApplication.clipboard().text()
        if not (texto or "").strip():
            return
        from app.qt.telas.colagem import (
            linhas_para_tuplas, multi_precos_de, parse_colagem)
        linhas = parse_colagem(texto)
        if not linhas:
            mostrar_toast(self, "Não reconheci produtos no que foi colado — "
                                "cole nome e preço, um por linha.", tipo="erro")
            return
        from app.qt.telas.colagem_dialog import ColagemPreviaDialog
        dlg = ColagemPreviaDialog(linhas, self)
        if dlg.exec() != ColagemPreviaDialog.DialogCode.Accepted:
            return
        confirmadas = dlg.linhas_confirmadas()
        tuplas = linhas_para_tuplas(confirmadas)
        if tuplas:
            self._importar_tuplas(tuplas, multi_precos_de(confirmadas))

    def _importar_tuplas(self, tuplas, multi_precos=None) -> None:
        """Concilia tuplas (descricao, preco, ean) em worker → estante (o mesmo
        _conciliar do multi-arquivo). 'Dados primeiro, fotos depois': os itens
        nascem sem foto e a busca em lote fica para depois (R-053).
        `multi_precos` (paralelo) leva a promoção "N por R$X" ao ItemMesa."""
        trab = Trabalhador(
            lambda st, t=tuplas, mp=multi_precos:
            servico.conciliar_linhas(t, st, multi_precos=mp))
        trab.status.connect(self._overlay.mostrar)
        trab.ok.connect(self._conciliar)
        trab.erro.connect(self._falhou)
        self._trabalhos.rodar(trab)

    def _importar_do_banco(self) -> None:
        """O pop-up com busca e multi-seleção acumulativa (importar do catálogo)."""
        from app.qt.telas.importar_banco_dialog import ImportarBancoDialog

        dlg = ImportarBancoDialog(self)
        if dlg.exec() != ImportarBancoDialog.DialogCode.Accepted:
            return
        novos = [servico.item_do_catalogo(d) for d in dlg.selecionados]
        ja = {it.produto_id for it in self._itens if it.produto_id}
        novos = [it for it in novos if it.produto_id not in ja]
        self._itens.extend(novos)
        self._recarregar_lista()
        self.btn_preencher.setEnabled(bool(self._itens))
        self.btn_salvar_proj.setEnabled(bool(self._itens))
        self._marcar_salvo(False)
        mostrar_toast(self, f"{len(novos)} item(ns) do banco na estante.")

    def _conciliar(self, resultado: servico.ResultadoMesa) -> None:
        self._overlay.esconder()
        if resultado.aviso:            # RG-04: o cache-hit do OCR fica visível
            mostrar_toast(self, resultado.aviso)
        # Auditoria do dono (validade): a validade ESCRITA NA TABELA (o caso
        # do jornal do mês) era extraída pelo parser e IGNORADA aqui — só
        # valia ao reabrir projeto. A da tabela MANDA; uma já definida à mão
        # não é sobrescrita em silêncio.
        if resultado.validade_oferta and not self._validade:
            self._validade = resultado.validade_oferta
            self._validade_lbl.setText(f"Validade: {self._validade}")
            mostrar_toast(self, "Validade veio da tabela: "
                                f"“{self._validade}”.")
        dlg = ConciliacaoDialog(resultado, self)
        if getattr(dlg, "_tela_cheia", False):
            dlg.showMaximized()        # R-052: fonte-foto abre em tela cheia
        if dlg.exec() != ConciliacaoDialog.DialogCode.Accepted:
            return
        verdes = [it for it in dlg.itens if it.semaforo == "VERDE"]
        fora = len(dlg.itens) - len(verdes)   # P1.5: descarte nunca invisível

        if self._itens:                       # P1.3: segundo import não apaga
            from PySide6.QtWidgets import QMessageBox
            caixa = QMessageBox(self)
            caixa.setWindowTitle("Já existe trabalho na estante")
            caixa.setText(f"A estante tem {len(self._itens)} item(ns). "
                          f"O que fazer com os {len(verdes)} novos?")
            adicionar = caixa.addButton("Adicionar aos atuais",
                                        QMessageBox.ButtonRole.AcceptRole)
            caixa.addButton("Substituir tudo", QMessageBox.ButtonRole.DestructiveRole)
            caixa.exec()
            if caixa.clickedButton() is adicionar:
                ja = {it.produto_id for it in self._itens if it.produto_id}
                verdes = [it for it in verdes if it.produto_id not in ja]
                self._itens.extend(verdes)
            else:
                self._itens = verdes
                self._mapa = {}               # grade será re-preenchida
                self._overrides = {}          # overrides eram do tabloide velho
        else:
            self._itens = verdes

        self._validade = dlg.validade
        self._validade_lbl.setText(
            f"Validade: {self._validade}" if self._validade else "")
        self._recarregar_lista()
        self.btn_preencher.setEnabled(bool(self._itens))
        self.btn_salvar_proj.setEnabled(bool(self._itens))
        self._marcar_salvo(False)      # há trabalho não congelado
        aviso = (f" · {fora} ficaram de fora (🟡/🔴 não resolvidos)"
                 if fora else "")
        mostrar_toast(self, f"{len(self._itens)} itens na estante.{aviso}")
        self._avisar_repeticao()          # R-059: "está no encarte há N semanas"
        self._avisar_foto_repetida()      # R-104: mesma foto em 2+ itens (hash)
        self._avisar_divergencia()        # R-123: mesmo item, preços diferentes

    def _avisar_repeticao(self) -> None:
        """R-059 (+ OS F11.5 #53): o alerta lê o HISTÓRICO em WORKER — a leitura
        das edições salvas (disco) não segura o thread da UI logo após um
        import grande. Avisa sem bloquear (I2); falha de leitura só silencia o
        aviso opcional."""
        itens = list(self._itens)
        trab = Trabalhador(
            lambda st, alvo=itens: servico.alertas_de_repeticao(alvo))

        def _pronto(repetidos):
            if not repetidos:
                return
            nomes = ", ".join(it.nome for it, _ in repetidos[:3])
            extra = "…" if len(repetidos) > 3 else ""
            mostrar_toast(self, f"{len(repetidos)} item(ns) repetem há várias "
                                f"edições ({nomes}{extra}) — que tal variar?")

        trab.ok.connect(_pronto)
        trab.erro.connect(lambda _m: None)     # aviso é opcional
        self._trabalhos.rodar(trab)

    def _avisar_foto_repetida(self) -> None:
        """R-104: a MESMA foto em 2+ itens da edição (por hash de CONTEÚDO) —
        avisa (I2), não bloqueia. Dois produtos com a mesma imagem é quase sempre
        engano."""
        try:
            grupos = servico.fotos_repetidas(self._itens)
        except Exception:
            return
        if not grupos:
            return
        nomes = ", ".join(it.nome for it in grupos[0][1][:3])
        mostrar_toast(self, f"A mesma foto aparece em {len(grupos[0][1])} itens "
                            f"({nomes}) — confira se não trocou.")

    def _perguntar_destino_resto(self, n: int) -> str:
        """#23: a pergunta — devolve 'pagina' | 'fila' | 'fora'."""
        from PySide6.QtWidgets import QMessageBox
        caixa = QMessageBox(self)
        caixa.setWindowTitle("Sobraram itens")
        caixa.setText(f"{n} item(ns) não couberam nesta página. "
                      "O que faço com eles?")
        b_pag = caixa.addButton("Criar página nova e encher",
                                QMessageBox.ButtonRole.AcceptRole)
        b_fila = caixa.addButton("Deixar na estante (fila)",
                                 QMessageBox.ButtonRole.ActionRole)
        b_fora = caixa.addButton("Tirar da oferta",
                                 QMessageBox.ButtonRole.DestructiveRole)
        caixa.setDefaultButton(b_fila)
        caixa.exec()
        clicado = caixa.clickedButton()
        if clicado is b_pag:
            return "pagina"
        if clicado is b_fora:
            return "fora"
        return "fila"

    def _aplicar_destino_resto(self, escolha: str, resto) -> None:
        """#25: executa a escolha. 'fila' = o comportamento clássico (ficam
        na estante, visíveis); 'pagina' duplica a página e enche de novo;
        'fora' tira da estante COM desfazer (nunca some calado)."""
        if escolha == "pagina":
            antes = self.area.canvas.total_paginas()
            self.area.canvas.duplicar_pagina_atual()
            if self.area.canvas.total_paginas() > antes:
                self.encher_pagina()
            return
        if escolha == "fora":
            copia_itens = list(self._itens)
            copia_mapa = dict(self._mapa)
            uids_fora = {it.uid for it in resto}
            self._itens = [it for it in self._itens
                           if it.uid not in uids_fora]
            self._recarregar_lista()
            self._marcar_salvo(False)
            from app.qt.design.toast import mostrar_toast_desfazer
            mostrar_toast_desfazer(
                self, f"{len(uids_fora)} item(ns) fora da oferta.",
                lambda: self._restaurar_estante_toda(copia_itens, copia_mapa))
            return
        mostrar_toast(self, f"{len(resto)} item(ns) seguem na estante "
                            "(fila) — “fora da grade”.")

    def _mostrar_diff_edicao(self) -> None:
        """OS F11.5 #44 (R-062): a comparação com a última edição salva."""
        if not self._itens:
            mostrar_toast(self, "Importe a oferta antes de comparar.")
            return
        diff = servico.diff_contra_ultima_edicao(self._itens)
        if diff is None:
            mostrar_toast(self, "Ainda não há edição salva para comparar.",
                          tipo="info")
            return
        from app.qt.telas.diff_dialog import DiffEdicaoDialog
        DiffEdicaoDialog(diff, self).exec()

    def _exportar_checklist_pdf(self) -> None:
        """OS F11.5 #48 (R-063): o checklist em PDF (conferência no papel)."""
        from PySide6.QtWidgets import QFileDialog
        if not self._itens:
            mostrar_toast(self, "Monte a oferta antes do checklist.")
            return
        destino, _ = QFileDialog.getSaveFileName(
            self, "Exportar checklist", "checklist.pdf", "PDF (*.pdf)")
        if not destino:
            return
        saida = servico.exportar_checklist_pdf(
            self._itens, self._validade, destino)
        mostrar_toast(self, f"Checklist exportado: {Path(saida).name}")

    def _avisar_divergencia(self) -> None:
        """R-123: o MESMO item (por uid, I1) aparecendo com preços diferentes em
        páginas do encarte — avisa (I2), não bloqueia. Divergência real, não
        coincidência de nome."""
        try:
            from app.qt.telas import inteligencia
            div = inteligencia.divergencias_no_mapa(
                self._dados_por_slot(), self._mapa)
        except Exception:
            return
        if not div:
            return
        nomes = ", ".join(d["nome"] for d in div[:3])
        mostrar_toast(self, f"{len(div)} produto(s) com preços diferentes entre "
                            f"páginas ({nomes}) — confira.", tipo="info")

    def _abrir_planilha(self) -> None:
        """R-051: abre o modo planilha (grade editável de todos os itens)."""
        if not self._itens:
            return
        from app.qt.telas.planilha_dialog import DialogoPlanilha
        DialogoPlanilha(self, self).exec()

    def duplicar_item(self, item):
        """R-069 (Fase 6): duplica um item — uid NOVO e próprio (não referência).
        Copia os dados congelados (nome/preço/foto) como ponto de partida
        editável; a cópia NÃO herda override (override é do slot, não do item)."""
        import uuid

        from app.qt.telas import servico
        d = item.to_dict()
        d["uid"] = uuid.uuid4().hex           # identidade nova (I1)
        novo = servico.ItemMesa.from_dict(d)
        try:
            idx = self._itens.index(item) + 1
        except ValueError:
            idx = len(self._itens)
        self._itens.insert(idx, novo)
        self._recarregar_lista()
        self._marcar_salvo(False)
        return novo

    def reordenar_estante(self, nova_ordem) -> None:
        """R-055 (Fase 6): a nova ordem da estante re-atribui o mapa slot→uid
        (por uid, I1): as células ocupáveis (ordem visual) recebem os itens na
        nova ordem. Undo unificado."""
        self._itens = list(nova_ordem)
        if self._layout is None:
            self._recarregar_lista()
            return
        from app.rendering.grade import ocupaveis, ordenar_slots_visualmente
        novo: dict = {}
        fila = list(self._itens)
        for pag in self._layout.paginas:
            slots = ocupaveis(ordenar_slots_visualmente(pag.slots))
            for slot, item in zip(slots, fila):
                novo[slot.id] = item.uid
            fila = fila[len(slots):]
        self.area.canvas.reatribuir_mapa(novo)
        self._recarregar_lista()

    def encher_pagina(self) -> None:
        """R-056 (Fase 7): distribui na PÁGINA ATUAL o que couber (nos slots
        VAZIOS, por uid — I1), com PRÉ-VOO ANTES (avisa item sem foto/preço,
        I2); o resto que não coube fica visível na estante ('fora da grade')."""
        if self._layout is None or not self._itens:
            return
        from app.rendering.grade import ocupaveis, ordenar_slots_visualmente
        pag = self.area.canvas._pagina()
        vazios = [s.id for s in ocupaveis(ordenar_slots_visualmente(pag.slots))
                  if s.id not in self._mapa]
        na_grade = set(self._mapa.values())
        fila = [it for it in self._itens if it.uid not in na_grade]
        if not vazios or not fila:
            mostrar_toast(self, "Nada a distribuir nesta página "
                                "(sem célula vazia ou sem item na fila).")
            return
        mapa_novo, resto, avisos = servico.plano_encher_pagina(fila, vazios)
        from app.qt.telas.prevoo import confirmar_pre_voo
        if avisos and not confirmar_pre_voo(self, avisos, "Encher a página"):
            return
        combinado = dict(self._mapa)
        combinado.update(mapa_novo)
        self.area.canvas.reatribuir_mapa(combinado)
        self._recarregar_lista()
        self._marcar_salvo(False)
        # OS F11.5 #23/#25 (R-056): o RESTO tem destino PERGUNTADO — nova
        # página (e enche de novo), fila (a estante, como sempre) ou fora
        # (sai da estante, com desfazer). Nunca um toast mudo.
        if resto:
            self._aplicar_destino_resto(self._perguntar_destino_resto(
                len(resto)), resto)

    def refletir_planilha(self) -> None:
        """R-051 (passo 27): planilha e canvas são a MESMA fonte de verdade —
        após editar um item (por uid), recompõe o desenho e a estante,
        respeitando o override por slot (via _dados_por_slot)."""
        self._recarregar_lista()
        self.area.canvas.atualizar_dados(self._dados_por_slot())
        self._marcar_salvo(False)

    # --- R-061: rascunho automático (rede de segurança isolada) --------------

    def _estado_para_rascunho(self) -> dict:
        """O conjunto salvável (o mesmo do _salvar_projeto) em dados planos."""
        lay = self.area.canvas._layout or self._layout
        return {
            "nome": getattr(self, "_nome_projeto", "") or "",
            "projeto_id": self._projeto_id,
            "layout": lay.to_dict() if lay is not None else None,
            "itens": [it.to_dict() for it in self._itens],
            "validade": self._validade,
            "mapa": dict(self._mapa),
            "overrides": dict(self._overrides),
        }

    def _salvar_rascunho_bg(self) -> None:
        """Passo 49-50: snapshot silencioso em BACKGROUND (worker; RG-05b cobre
        o shutdown) — não trava a UI, não toca o projeto salvo."""
        if not self._itens:
            return
        estado = self._estado_para_rascunho()
        from app.core.rascunho import salvar_rascunho
        from app.qt.workers import Trabalhador

        def _tarefa(_status_cb):
            salvar_rascunho(estado)
            return True
        trab = Trabalhador(_tarefa)
        trab.ok.connect(lambda _r: self._indicar_rascunho())
        self._trabalhos.rodar(trab)

    def _indicar_rascunho(self) -> None:
        import time
        self._rascunho_lbl.setText(f"✓ rascunho salvo {time.strftime('%H:%M')}")

    def _oferecer_recuperacao(self) -> None:
        """Passo 51: ao reabrir após uma queda, oferece recuperar o rascunho —
        o dono decide (prévia com a hora)."""
        from app.core import rascunho
        if not rascunho.ha_rascunho():
            return
        estado = rascunho.carregar_rascunho()
        if not estado or not estado.get("itens"):
            return
        from PySide6.QtWidgets import QMessageBox
        hora = rascunho.hora_do_rascunho(estado)
        n = len(estado.get("itens", []))
        r = QMessageBox.question(
            self, "Recuperar rascunho?",
            f"Encontrei um rascunho automático de {hora} "
            f"({n} itens) — parece que o app foi fechado sem salvar.\n\n"
            "Quer recuperar esse trabalho?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if r == QMessageBox.StandardButton.Yes:
            self._recuperar_rascunho(estado)
        else:
            rascunho.descartar_rascunhos()

    def _recuperar_rascunho(self, estado: dict) -> None:
        from app.qt.telas import servico
        from app.rendering.model import LayoutDef
        self._itens = [servico.ItemMesa.from_dict(d)
                       for d in estado.get("itens", [])]
        self._validade = estado.get("validade")
        if estado.get("layout"):
            self._layout = LayoutDef.from_dict(estado["layout"])
            self.area.carregar(self._layout, {})
        self._mapa = dict(estado.get("mapa", {}))
        self._overrides = dict(estado.get("overrides", {}))
        self.area.canvas.atualizar_dados(self._dados_por_slot())
        self._recarregar_lista()
        self._marcar_salvo(False)
        mostrar_toast(self, "Rascunho recuperado — confira e salve o projeto.")

    # --- R-017: Ctrl+K na Mesa (a MESMA paleta da F2, fonte de resultados
    #     da Mesa: itens da estante + ações da barra + navegar) ---------------

    def _acoes_da_mesa(self) -> list:
        acoes = [
            ("abrir", "Importar tabela/foto", "", self._importar),
            ("grade", "Auto-preencher a grade", "", self._auto_preencher),
            ("grade", "Encher a página atual", "", self.encher_pagina),
            ("propriedades", "Modo planilha", "", self._abrir_planilha),
            ("texto", "Colar tabela (Ctrl+V)", "", self._colar_tabela),
            ("salvar", "Exportar", "", self._exportar),
            ("salvar", "Exportar em perfis / lote (WhatsApp, Impressão)…", "",
             self._exportar_perfis),
            ("check_circulo", "Aprovar (tira o RASCUNHO)", "",
             self.aprovar_projeto_atual),
            ("lampada", "Revisar a peça com a IA (avisa, não trava)…", "",
             self._revisar),
            ("texto", "Montar pelo texto (chat da oferta)…", "",
             self._chat_oferta),
            ("imagem", "Publicar (Oferta do Dia, carrossel, vídeo)…", "",
             self._publicar),
            ("cofre", "Salvar projeto", "", self._salvar_projeto),
            ("abrir", "Abrir projeto", "", self._abrir_projeto),
            # OS F11.5 #44/#48: o diff e o checklist agora têm porta de UI
            ("restaurar", "O que mudou desde a última edição…", "",
             self._mostrar_diff_edicao),
            ("salvar", "Exportar o checklist em PDF…", "",
             self._exportar_checklist_pdf),
            # OS F11.5 #50/#51 (R-082): variações do mesmo produto
            ("lampada", "Sugerir variações para agrupar (sabores)…", "",
             self._sugerir_variacoes),
        ]
        # OS F11.5 #57: navegar por página e abrir Configurações pela paleta
        canvas = self.area.canvas
        for n in range(canvas.total_paginas()):
            acoes.append(("grade", f"Ir para a página {n + 1}", "",
                          lambda p=n: canvas.ir_para_pagina(p)))
        def _abrir_config():
            shell = self.window()
            if hasattr(shell, "ir_para"):
                shell.ir_para("configuracoes")
        acoes.append(("propriedades", "Abrir Configurações", "",
                      _abrir_config))
        for i, it in enumerate(self._itens):
            acoes.append(("caixa", f"Item: {it.nome}", "",
                          lambda idx=i: self.lista.setCurrentRow(idx)))
        return acoes

    def _abrir_paleta(self) -> None:
        from app.qt.design.paleta_comandos import PaletaComandos
        PaletaComandos(self.window(), self._acoes_da_mesa()).abrir()

    # --- OS F11.5 #50/#51 (R-082): variações do mesmo produto -----------------

    def _sugerir_variacoes(self) -> None:
        """Detecta prováveis variações (sabores/tamanhos da MESMA marca
        conhecida) e pergunta, grupo a grupo, se agrupa num slot só (o modo
        multi da F7.1). Nunca inventa: sem marca confirmada, sem sugestão."""
        from app.core.aprendizado import sugerir_variacoes
        grupos = sugerir_variacoes(self._itens, servico.marcas_do_acervo())
        if not grupos:
            mostrar_toast(self, "Não achei variações da mesma marca para "
                                "agrupar.")
            return
        from PySide6.QtWidgets import QMessageBox
        agrupados = 0
        for grupo in grupos:
            nomes = " · ".join((it.nome or "?") for it in grupo[:4])
            r = QMessageBox.question(
                self, "Variações do mesmo produto?",
                f"Estes parecem sabores/tamanhos do mesmo produto:\n\n"
                f"{nomes}\n\nAgrupar num slot só (as fotos viram o leque "
                "multi)?",
                QMessageBox.StandardButton.Yes
                | QMessageBox.StandardButton.No)
            if r == QMessageBox.StandardButton.Yes:
                self._agrupar_variacoes(grupo)
                agrupados += 1
        if agrupados:
            mostrar_toast(self, f"{agrupados} grupo(s) agrupado(s) — desfazer "
                                "pelo toast se se arrepender.")

    def _agrupar_variacoes(self, grupo) -> None:
        """#51: funde o grupo no PRIMEIRO item (por uid, I1): as fotos de
        todos viram a lista multi (F7.1) e os demais saem da estante — com
        a cópia p/ desfazer (nunca some calado)."""
        if len(grupo) < 2:
            return
        copia_itens = list(self._itens)
        copia_mapa = dict(self._mapa)
        base = grupo[0]
        imagens_antes = list(base.imagens)     # o desfazer devolve o multi
        fotos = []
        for it in grupo:
            fotos.extend(it.imagens or ([it.imagem] if it.imagem else []))
        base.imagens = [f for f in fotos if f]
        uids_fora = {it.uid for it in grupo[1:]}
        self._itens = [it for it in self._itens if it.uid not in uids_fora]
        self._mapa = {sid: u for sid, u in self._mapa.items()
                      if u not in uids_fora}
        self._recarregar_lista()
        self._marcar_salvo(False)
        from app.qt.design.toast import mostrar_toast_desfazer

        def _desfazer(b=base, antes=imagens_antes,
                      itens=copia_itens, mapa=copia_mapa):
            b.imagens = list(antes)
            self._restaurar_estante_toda(itens, mapa)

        mostrar_toast_desfazer(
            self, f"“{base.nome}” virou multi com {len(base.imagens)} foto(s).",
            _desfazer)

    def _publicar(self) -> None:
        """R-139/140/141/142: hub dos formatos sociais + vídeo (reusa o
        compositor). Marca d'água RASCUNHO até a aprovação."""
        if not self._itens:
            mostrar_toast(self, "Importe ou monte a oferta antes de publicar.")
            return
        from app.qt.telas.publicar_dialog import PublicarDialog
        PublicarDialog(self, self).exec()

    def _exportar_perfis(self) -> None:
        """R-065/066/064: perfis (WhatsApp/Impressão/Stories) + fila em lote +
        compartilhar, num diálogo só."""
        if not self._itens:
            mostrar_toast(self, "Monte a oferta antes de exportar.")
            return
        from app.qt.telas.exportar_dialog import ExportarDialog
        ExportarDialog(self, self).exec()

    def _revisar(self) -> None:
        """R-081: a IA revisora LÊ a peça e aponta preço/nome divergente —
        AVISA, nunca trava. Com visão, compara o que vê × os dados; sem visão,
        degrada para heurística com aviso (worker; overlay; não congela)."""
        if not self._itens:
            mostrar_toast(self, "Monte a oferta antes de revisar.")
            return
        paginas = self.paginas_compostas()
        if not paginas:
            mostrar_toast(self, "Nada para revisar.")
            return
        import tempfile
        dados = self._dados_por_slot()
        layout = self.area.canvas._layout or self._layout
        from app.core.paths import SystemRoot
        fontes = SystemRoot().fontes
        # nome ÚNICO por revisão (achado da frota: um caminho fixo compartilhado
        # deixava 2 revisões rápidas sobrescreverem o PNG uma da outra)
        tf = tempfile.NamedTemporaryFile(prefix="revisora_", suffix=".png",
                                         delete=False)
        tf.close()
        png = Path(tf.name)
        paginas[0].save(str(png))

        def _trabalho(st):
            st("A IA está lendo a peça — pode levar alguns instantes…")
            from app.ai.revisora import revisar_export
            motor = servico._motor_se_disponivel()
            return revisar_export(str(png), dados, layout=layout, motor=motor,
                                  fontes_dir=fontes)

        trab = Trabalhador(_trabalho)
        trab.status.connect(self._overlay.mostrar)
        trab.ok.connect(self._mostrar_laudo)
        trab.erro.connect(self._falhou)
        self._trabalhos.rodar(trab)

    def _mostrar_laudo(self, resultado) -> None:
        """O laudo da revisora — avisos (o dono decide). NUNCA veta o export.
        OS F11.5 #23: cada aviso é CLICÁVEL e leva ao item citado (seleciona
        na estante e navega até a página do slot dele)."""
        self._overlay.esconder()
        avisos, deg = resultado
        if not avisos and not deg:
            mostrar_toast(self, "A revisora não achou problemas. 👍",
                          tipo="sucesso")
            return
        from PySide6.QtWidgets import (
            QDialog, QDialogButtonBox, QLabel, QListWidget, QVBoxLayout)
        dlg = QDialog(self)
        dlg.setWindowTitle("Laudo da revisora — avisos (você decide)")
        dlg.resize(560, 420)
        v = QVBoxLayout(dlg)
        v.setContentsMargins(t.ESP_4, t.ESP_4, t.ESP_4, t.ESP_4)
        v.setSpacing(t.ESP_2)
        cab = QLabel(f"A IA leu a peça e anotou {len(avisos)} ponto(s). "
                     "São avisos — o export não fica travado. Clique num "
                     "aviso para ir ao item.")
        cab.setProperty("papel", "legenda")
        cab.setWordWrap(True)
        v.addWidget(cab)
        lista = QListWidget()
        for a in avisos:
            lista.addItem(f"• {a}")
        if deg:
            lista.addItem(f"ℹ {deg}")
        lista.itemClicked.connect(
            lambda li: self._ir_para_aviso(li.text()))
        v.addWidget(lista, 1)
        botoes = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        botoes.button(QDialogButtonBox.StandardButton.Close).setText("Fechar")
        botoes.rejected.connect(dlg.reject)
        botoes.accepted.connect(dlg.accept)
        v.addWidget(botoes)
        dlg.setModal(False)          # o dono clica e VÊ a Mesa reagir atrás
        dlg.show()
        self._laudo_dlg = dlg        # referência viva (e testável)

    def _ir_para_aviso(self, aviso: str) -> str | None:
        """#23: acha o item citado no aviso ('“Nome”: …'), seleciona a linha
        dele na estante e navega até a página do slot. Devolve o uid (teste)."""
        import re
        m = re.search(r"[“\"](.+?)[”\"]", aviso or "")
        if not m:
            return None
        nome = m.group(1).strip().lower()
        alvo = next((it for it in self._itens
                     if (it.nome or "").strip().lower() == nome), None)
        if alvo is None:
            return None
        linha = next((i for i, it in enumerate(self._itens)
                      if it.uid == alvo.uid), -1)
        if linha >= 0:
            self.lista.setCurrentRow(linha)
            self.lista.scrollToItem(self.lista.item(linha))
        sid = next((s for s, u in self._mapa.items() if u == alvo.uid), None)
        if sid is not None and self._layout is not None:
            for i, pag in enumerate(self._layout.paginas):
                if any(s.id == sid for s in pag.slots):
                    if i != self.area.canvas.pagina_atual:
                        self._ir_pagina(i)
                    break
        return alvo.uid

    def _chat_oferta(self) -> None:
        """R-073: o dono cola/descreve as ofertas e a IA monta um RASCUNHO,
        reusando a conciliação. Sempre rascunho para ajustar (nunca publica)."""
        from PySide6.QtWidgets import QInputDialog
        texto, ok = QInputDialog.getMultiLineText(
            self, "Chat da oferta",
            "Cole ou descreva as ofertas (uma por linha: nome e preço):", "")
        if not ok or not (texto or "").strip():
            return
        from app.qt.telas.colagem import (
            linhas_para_tuplas, multi_precos_de, parse_colagem)
        linhas = parse_colagem(texto)
        if not linhas:
            mostrar_toast(self, "Não reconheci ofertas no texto — tente nome e "
                                "preço por linha.", tipo="erro")
            return
        self._importar_tuplas(linhas_para_tuplas(linhas),
                              multi_precos_de(linhas))

    def _atualizar_estatistica(self) -> None:
        """R-072: rodapé discreto da montagem — tempo/itens por minuto, LOCAL
        (sem telemetria). O cronômetro começa quando o 1º item entra na estante;
        o detalhe (itens/min) fica no tooltip para não poluir a barra."""
        import time as _time
        n = len(self._itens)
        if not n:
            self._estatistica_lbl.setText("")
            self._estatistica_lbl.setToolTip("")
            return
        if self._t_inicio is None:
            self._t_inicio = _time.monotonic()
        seg = _time.monotonic() - self._t_inicio
        r = servico.resumo_montagem(seg, n)
        # R-122 (Fase 11, polimento): a META do evento vira o pulso "32/40" na
        # barra — informativa, sem cobrança; sem meta definida, o "N item(ns)"
        # de sempre. Falha de leitura nunca atrapalha a montagem.
        texto, dica_meta = f"{n} item(ns)", ""
        try:
            from app.qt.telas import inteligencia
            evento = getattr(self, "_evento", None)
            if evento:
                p = inteligencia.progresso_meta(evento, n)
                if p["meta"]:
                    texto = p["texto"]        # "32/40"
                    dica_meta = (f" Meta do evento “{evento}”: "
                                 f"{p['meta']} itens"
                                 + (" — atingida! ✓" if p["atingiu"] else "."))
        except Exception:
            pass
        self._estatistica_lbl.setText(texto)
        self._estatistica_lbl.setToolTip(
            f"Montagem desta oferta: {r['resumo']} — cálculo local, "
            "nada sai do seu computador." + dica_meta
            + "\nClique para definir a META de itens do evento (R-122).")
        # OS F11.5 #47 (R-122): clicar na estatística DEFINE a meta
        self._estatistica_lbl.setCursor(Qt.CursorShape.PointingHandCursor)
        self._estatistica_lbl.mousePressEvent = \
            lambda _ev: self._definir_meta_evento()

    def _definir_meta_evento(self) -> None:
        """#47: o dono define a meta de itens do evento (persistida por
        evento; o pulso '32/40' da barra passa a refletir na hora)."""
        evento = (getattr(self, "_evento", None) or "").strip()
        if not evento:
            mostrar_toast(self, "Dê um nome/evento à oferta primeiro — a "
                                "meta é POR evento (ex.: “Quintou”).")
            return
        from PySide6.QtWidgets import QInputDialog

        from app.qt.telas import inteligencia
        atual = inteligencia.meta_evento(evento) or 0
        meta, ok = QInputDialog.getInt(
            self, "Meta do evento",
            f"Quantos itens o encarte de “{evento}” costuma ter?\n"
            "(0 tira a meta — o pulso volta a ser só a contagem)",
            atual, 0, 999)
        if not ok:
            return
        inteligencia.definir_meta_evento(evento, int(meta))
        self._atualizar_estatistica()
        mostrar_toast(self, f"Meta de “{evento}”: "
                            + (f"{meta} itens." if meta else "removida."))

    def contexto_frases(self) -> dict:
        """R-058: contexto VIVO para resolver {data}/{evento} nas frases prontas
        (o diálogo de papel de texto o consulta). {data} = validade da oferta;
        {evento} fica em aberto (visível, I2) se a oferta não tiver nome."""
        ctx: dict = {}
        if self._validade:
            ctx["data"] = self._validade
        ev = getattr(self, "_evento", None)
        if ev:
            ctx["evento"] = ev
        return ctx

    def _recarregar_lista(self) -> None:
        self._reconstruindo = True               # não dispara reordenação
        self.lista.clear()
        self._vazio.setVisible(not self._itens)
        self.lista.setVisible(bool(self._itens))
        self._filtro_barra.setVisible(bool(self._itens))
        self._atualizar_categorias_filtro()      # OS #31: combo vivo
        self.btn_fotos_lote.setEnabled(bool(self._sem_foto()))   # RG-03
        self.btn_planilha.setEnabled(bool(self._itens))          # R-051
        # RG-07: contagem viva no título do painel
        n = len(self._itens)
        self._painel_itens.set_titulo(
            f"Itens da oferta ({n})" if n else "Itens da oferta")
        self._atualizar_estatistica()            # R-072
        na_grade = set(self._mapa.values())
        for it in self._itens:
            extras = []
            if servico.eh_composto(it):
                extras.append("composto (2 em 1)")          # F7.2
            if it.imagens:
                extras.append(f"{len(it.imagens)} fotos")   # F7.1: modo multi
            elif not it.imagem:
                extras.append("sem foto")
            if it.multi_preco:
                extras.append("promoção")            # R-070: TEM preço (formato)
            elif servico.preco_decimal(it.preco) is None:
                extras.append("sem preço")           # I2: visível na estante
            if it.observacao:
                extras.append("obs.")                # R-071: tem observação
            if na_grade and it.uid not in na_grade:
                extras.append("fora da grade")
            sufixo = ("   · " + " · ".join(extras)) if extras else ""
            li = QListWidgetItem(self.lista)
            rotulo = QLabel(
                f'<span style="color:{_COR[it.semaforo]}">●</span> '
                f'{it.nome}  <span style="color:{t.TEXTO_3}">'
                f'{("R$ " + it.preco) if it.preco else ""}{sufixo}</span>')
            rotulo.setToolTip("Duplo-clique: editar nome e preço deste tabloide")
            rotulo.setContentsMargins(t.ESP_2, 3, t.ESP_2, 3)
            li.setSizeHint(rotulo.sizeHint())
            li.setData(Qt.ItemDataRole.UserRole, it.uid)   # R-055: uid por linha
            self.lista.setItemWidget(li, rotulo)
        self._reconstruindo = False
        self._aplicar_filtro()

    def _limpar_filtros(self) -> None:
        """OS F11.5 #33: zera TODOS os filtros num clique."""
        self.chk_sem_foto.setChecked(False)
        self.chk_sem_preco.setChecked(False)
        self.filtro_categoria.setCurrentIndex(0)
        self.campo_busca.clear()

    def _atualizar_categorias_filtro(self) -> None:
        """#31: as categorias PRESENTES na estante povoam o combo (mantém a
        escolha atual quando possível)."""
        atual = self.filtro_categoria.currentText()
        cats = sorted({(it.categoria or servico.OUTROS)
                       for it in self._itens})
        self.filtro_categoria.blockSignals(True)
        self.filtro_categoria.clear()
        self.filtro_categoria.addItem("Todas")
        self.filtro_categoria.addItems(cats)
        i = self.filtro_categoria.findText(atual)
        self.filtro_categoria.setCurrentIndex(i if i >= 0 else 0)
        self.filtro_categoria.blockSignals(False)

    def _aplicar_filtro(self) -> None:
        """R-054 (+ OS F11.5 #31/#32/#40/#43): esconde as linhas que não
        passam; o chip diz O QUE está vendo COM os contadores por critério; o
        pulso resume as pendências mesmo sem filtro; nada passou → estado
        vazio de filtro com a saída à vista."""
        if not hasattr(self, "chk_sem_foto"):
            return
        cat = self.filtro_categoria.currentText()
        visiveis = servico.filtrar_itens(
            self._itens, sem_foto=self.chk_sem_foto.isChecked(),
            sem_preco=self.chk_sem_preco.isChecked(),
            categoria=None if cat in ("", "Todas") else cat,
            busca=self.campo_busca.text())
        uids_ok = {it.uid for it in visiveis}
        for i in range(self.lista.count()):
            li = self.lista.item(i)
            li.setHidden(li.data(Qt.ItemDataRole.UserRole) not in uids_ok)
        # #32: contadores por critério — o dono vê o TAMANHO de cada pendência
        n_sem_foto = len(servico.filtrar_itens(self._itens, sem_foto=True))
        n_sem_preco = len(servico.filtrar_itens(self._itens, sem_preco=True))
        self.chk_sem_foto.setText(f"Sem foto ({n_sem_foto})")
        self.chk_sem_preco.setText(f"Sem preço ({n_sem_preco})")
        # #43: o pulso da estante (sempre que houver pendência)
        pulso = []
        if n_sem_foto:
            pulso.append(f"{n_sem_foto} sem foto")
        if n_sem_preco:
            pulso.append(f"{n_sem_preco} sem preço")
        self._pulso_filtro.setVisible(bool(pulso) and bool(self._itens))
        self._pulso_filtro.setText(" · ".join(pulso))
        ativo = (self.chk_sem_foto.isChecked() or self.chk_sem_preco.isChecked()
                 or cat not in ("", "Todas")
                 or bool(self.campo_busca.text().strip()))
        self._chip_filtro.setVisible(ativo)
        if ativo:
            self._chip_filtro.setText(
                f"Filtro ativo — mostrando {len(visiveis)} de {len(self._itens)} "
                "· “Limpar” zera tudo")
        # #40: nada passou → estado vazio de filtro (a lista some)
        nada = ativo and not visiveis and bool(self._itens)
        self._vazio_filtro.setVisible(nada)
        self.lista.setVisible(bool(self._itens) and not nada)

    def _estante_reordenada(self, *args) -> None:
        """R-055: ao soltar o arrasto, a nova ordem visual vira a ordem da
        estante — o mapa slot→uid segue por uid (I1)."""
        if getattr(self, "_reconstruindo", False):
            return
        ordem = [self.lista.item(i).data(Qt.ItemDataRole.UserRole)
                 for i in range(self.lista.count())]
        por_uid = {it.uid: it for it in self._itens}
        nova = [por_uid[u] for u in ordem if u in por_uid]
        if len(nova) == len(self._itens):
            self.reordenar_estante(nova)

    def _menu_item(self, pos) -> None:
        """F7.1: menu da estante — fotos do item (sabores) + edição rápida."""
        from PySide6.QtWidgets import QMenu

        li = self.lista.itemAt(pos)
        if li is None:
            return
        linha = self.lista.row(li)
        it = self._itens[linha] if 0 <= linha < len(self._itens) else None
        menu = QMenu(self)
        a_fotos = menu.addAction(icone("imagem", tamanho=16),
                                 "Fotos deste item (sabores)…")
        a_fotos.setToolTip("Várias fotos na mesma célula — a IA sugere os "
                           "termos, você escolhe cada foto")
        a_editar = menu.addAction(icone("texto", tamanho=16),
                                  "Editar nome e preço")
        # R-070: promoção por quantidade (campo qtd+valor) — casca do multi-preço
        a_promo = menu.addAction(icone("preco", tamanho=16),
                                 "Promoção por quantidade…")
        a_promo.setToolTip("“3 por R$ 10,00” ou “Leve 3 pague 2” — a região de "
                           "preço desenha a promoção no lugar do valor único")
        # R-071: observação do item ("limite 2 por cliente")
        a_obs = menu.addAction(icone("texto", tamanho=16),
                               "Observação do item…")
        a_obs.setToolTip("Um recado curto (“limite 2 por cliente”) que vira uma "
                         "região de observação; vazio não desenha")
        # F7.2: compor/separar — dois produtos num slot (Camil e Rei)
        a_compor = a_separar = None
        if it is not None and not servico.eh_composto(it):
            a_compor = menu.addAction(icone("duplicar", tamanho=16),
                                      "Compor com outro item (2 num slot)…")
            a_compor.setToolTip("Camil e Rei: dois produtos viram UM item "
                                "composto — separável a qualquer momento")
        elif it is not None:
            a_separar = menu.addAction(icone("restaurar", tamanho=16),
                                       "Separar (desfazer o composto)")
            a_separar.setToolTip("Devolve os dois itens originais à estante")
        # RG-33: selos personalizados deste item
        a_selos = menu.addAction(icone("cofre", tamanho=16),
                                 "Selos deste item…")
        a_selos.setToolTip("Escolher selos do gestor (“Muito Barato”, "
                           "“Destaque”…) só para este item")
        # R-069 (Fase 6): duplicar item — uid novo, independente
        a_dup = menu.addAction(icone("duplicar", tamanho=16), "Duplicar item")
        a_dup.setToolTip("Cria uma cópia editável (identidade própria) — "
                         "editar a cópia não toca o original")
        # RG-07: excluir da estante (o banco não é tocado)
        menu.addSeparator()
        a_del = menu.addAction(icone("lixeira", tamanho=16),
                               "Excluir da estante")
        a_del.setShortcut("Del")
        a_del.setToolTip("Tira o item DESTE tabloide — o cadastro no banco "
                         "continua intacto")
        escolha = menu.exec(self.lista.mapToGlobal(pos))
        if escolha == a_dup and it is not None:
            # OS F11.5 #44: com multi-seleção, duplica o BLOCO (por uid —
            # o snapshot protege dos índices que mudam a cada inserção)
            selecionados = [self._itens[ix.row()]
                            for ix in self.lista.selectedIndexes()
                            if 0 <= ix.row() < len(self._itens)]
            for alvo in (selecionados or [it]):
                self.duplicar_item(alvo)
        elif escolha == a_fotos:
            self._fotos_do_item(li)
        elif escolha == a_editar:
            self._editar_item(li)
        elif escolha == a_promo and it is not None:
            self._promocao_do_item(linha)
        elif escolha == a_obs and it is not None:
            self._observacao_do_item(linha)
        elif a_compor is not None and escolha == a_compor:
            self._compor_item(linha)
        elif a_separar is not None and escolha == a_separar:
            self._executar_separacao(linha)
        elif escolha == a_selos and 0 <= linha < len(self._itens):
            self._selos_do_item(linha)
        elif escolha == a_del and 0 <= linha < len(self._itens):
            self._excluir_item(linha)

    def _selos_do_item(self, linha: int) -> None:
        """RG-33: checkboxes dos selos do gestor — a escolha é POR ITEM e
        congela com o projeto (o ItemMesa serializa a lista)."""
        from PySide6.QtWidgets import (
            QCheckBox, QDialog, QDialogButtonBox, QLabel, QVBoxLayout,
        )

        it = self._itens[linha]
        registro = servico.selos_disponiveis()
        if not registro:
            mostrar_toast(self, "Nenhum selo no gestor — crie os seus em "
                                "Configurações → Selos personalizados.")
            return
        dlg = QDialog(self)
        dlg.setWindowTitle(f"Selos — {it.nome[:40]}")
        lay = QVBoxLayout(dlg)
        lay.addWidget(QLabel("Selos deste item (os automáticos +18/"
                             "Qualidade continuam por conta própria):"))
        caixas = []
        for r in registro:
            cb = QCheckBox(r["nome"])
            cb.setChecked(r["nome"] in (it.selos or []))
            caixas.append(cb)
            lay.addWidget(cb)
        botoes = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok
                                  | QDialogButtonBox.StandardButton.Cancel)
        botoes.accepted.connect(dlg.accept)
        botoes.rejected.connect(dlg.reject)
        lay.addWidget(botoes)
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return
        it.selos = [cb.text() for cb in caixas if cb.isChecked()]
        self._marcar_salvo(False)
        if it.uid in self._mapa.values():
            self.area.canvas.atualizar_dados(self._dados_por_slot())
            self.area.canvas.viewport().update()
        mostrar_toast(self, f"{len(it.selos)} selo(s) neste item.")

    def _fotos_do_item(self, li: QListWidgetItem) -> None:
        """F7.1: abre a curadoria multi (ordem = ordem do desenho no slot)."""
        from app.qt.telas.fotos_item_dialog import FotosItemDialog

        linha = self.lista.row(li)
        if not (0 <= linha < len(self._itens)):
            return
        it = self._itens[linha]
        dlg = FotosItemDialog(it, self)
        if dlg.exec() != FotosItemDialog.DialogCode.Accepted:
            return
        fotos = dlg.caminhos()
        if len(fotos) <= 1:
            it.imagens = []                       # volta ao modo foto única
            it.imagem = fotos[0] if fotos else it.imagem
        else:
            it.imagens = fotos                    # a lista completa, na ordem
            it.imagem = fotos[0]                  # a 1ª vira a "principal"
        it.arranjo = dlg.arranjo_escolhido()
        # RG-28: os sabores agora PERSISTEM no acervo (não só neste projeto)
        if it.produto_id:
            n = servico.salvar_imagens_produto(it.produto_id, fotos)
            if len(fotos) >= 2 and n < len(fotos):
                mostrar_toast(self, f"{len(fotos) - n} foto(s) fora da "
                                    "biblioteca ficam SÓ neste tabloide "
                                    "(o congelamento as preserva).")
        self._marcar_salvo(False)
        self._recarregar_lista()
        if it.uid in self._mapa.values():
            self._aplicar_mapa()                  # o slot recompõe na hora
        mostrar_toast(self, f"{max(1, len(fotos))} foto(s) neste item — "
                            f"arranjo {it.arranjo.replace('_', ' ').lower()}.")

    # --- item composto (F7.2): compor/separar — 1 slot → 1 uid, sempre --------------

    def _compor_item(self, linha: int) -> None:
        """Pergunta o par + nome/preço e delega à lógica testável."""
        from PySide6.QtWidgets import QInputDialog

        a = self._itens[linha]
        outros = [(i, it) for i, it in enumerate(self._itens)
                  if i != linha and not servico.eh_composto(it)]
        if not outros:
            mostrar_toast(self, "Não há outro item simples para compor.",
                          tipo="erro")
            return
        nomes = [it.nome for _i, it in outros]
        escolhido, ok = QInputDialog.getItem(
            self, "Compor 2 num slot", f"Juntar “{a.nome}” com:", nomes,
            0, False)
        if not ok:
            return
        idx_b = outros[nomes.index(escolhido)][0]
        sugestao = servico.nome_composto(a.nome, self._itens[idx_b].nome)
        nome, ok = QInputDialog.getText(
            self, "Compor 2 num slot", "Nome do composto:", text=sugestao)
        if not ok:
            return
        preco, ok = QInputDialog.getText(
            self, "Compor 2 num slot", "Preço ÚNICO da dupla:",
            text=a.preco or "")
        if not ok:
            return
        self._executar_composicao(linha, idx_b, nome.strip() or sugestao,
                                  preco.strip() or None)

    def _executar_composicao(self, idx_a: int, idx_b: int,
                             nome: str | None = None,
                             preco: str | None = None) -> None:
        """A lógica do compor (sem UI): estante e mapa saem CONSISTENTES.

        O composto assume o slot do PRIMEIRO item (se tiver); as entradas do
        segundo saem do mapa (a célula esvazia à vista — nunca dois uids).
        """
        a, b = self._itens[idx_a], self._itens[idx_b]
        comp = servico.compor_itens(a, b, nome, preco)
        self._itens = [it for i, it in enumerate(self._itens)
                       if i not in (idx_a, idx_b)]
        self._itens.insert(min(idx_a, idx_b), comp)
        novo_mapa = {}
        for sid, uid in self._mapa.items():
            if uid == a.uid:
                novo_mapa[sid] = comp.uid          # o composto herda o slot de A
            elif uid == b.uid:
                continue                           # a célula de B esvazia (visível)
            else:
                novo_mapa[sid] = uid
        self._mapa = novo_mapa
        self._marcar_salvo(False)
        self._recarregar_lista()
        self._aplicar_mapa()
        mostrar_toast(self, f"Composto criado: “{comp.nome}” — separável "
                            "pelo botão direito.")

    def _executar_separacao(self, linha: int) -> None:
        """Desfaz o composto: os DOIS originais voltam (uids de sempre);
        o slot do composto fica com o PRIMEIRO deles."""
        comp = self._itens[linha]
        try:
            a, b = servico.separar_item(comp)
        except ValueError as exc:
            mostrar_toast(self, str(exc), tipo="erro")
            return
        self._itens = (self._itens[:linha] + [a, b]
                       + self._itens[linha + 1:])
        self._mapa = {sid: (a.uid if uid == comp.uid else uid)
                      for sid, uid in self._mapa.items()}
        self._marcar_salvo(False)
        self._recarregar_lista()
        self._aplicar_mapa()
        mostrar_toast(self, f"Separado: “{a.nome}” ficou na célula; "
                            f"“{b.nome}” voltou à estante.")

    # --- fotos em lote (RG-03): "editar primeiro, fotos depois" ---------------------

    def _sem_foto(self) -> list[servico.ItemMesa]:
        """Itens do lote: verdes com produto no banco e SEM foto nenhuma."""
        return [it for it in self._itens
                if it.produto_id and not it.imagem and not it.imagens]

    def _fotos_em_lote(self) -> None:
        fila = [it.uid for it in self._sem_foto()]
        if not fila:
            mostrar_toast(self, "Nenhum item sem foto na estante.")
            return
        self._fila_fotos = fila
        self._fila_fotos_total = len(fila)
        self._prefetch_lote: dict[str, list[str]] = {}
        self._prefetch_em_voo = False
        # geração da fila: prefetch de uma fila CANCELADA não aterrissa na nova
        self._fila_geracao = getattr(self, "_fila_geracao", 0) + 1
        mostrar_toast(self, f"Fila de fotos: {len(fila)} item(ns) — a busca "
                            "do próximo roda enquanto você escolhe.")
        self._proximo_foto_lote()

    def _item_por_uid(self, uid: str) -> servico.ItemMesa | None:
        return next((it for it in self._itens if it.uid == uid), None)

    def _proximo_foto_lote(self) -> None:
        while getattr(self, "_fila_fotos", None):
            uid = self._fila_fotos.pop(0)
            it = self._item_por_uid(uid)
            if it is None or it.imagem:
                continue               # sumiu/já resolvido no meio do caminho
            cands = self._prefetch_lote.pop(uid, None)
            if cands is not None:
                self._curar_foto_lote(uid, cands)
                return
            trab = Trabalhador(lambda st, n=it.nome, e=it.ean:
                               servico.buscar_candidatos_para(n, st, ean=e))
            trab.status.connect(self._overlay.mostrar)
            trab.ok.connect(lambda cs, u=uid: self._curar_foto_lote(u, cs))
            trab.erro.connect(lambda m, n=it.nome: self._falhou_foto_lote(n, m))
            self._trabalhos.rodar(trab)
            return
        self._overlay.esconder()
        mostrar_toast(self, "Fila de fotos concluída.")

    def _falhou_foto_lote(self, nome: str, msg: str) -> None:
        """Erro num item NÃO mata a fila em silêncio (revisão da Onda 1):
        avisa qual item falhou e segue para o próximo."""
        self._overlay.esconder()
        mostrar_toast(self, f"“{nome}”: {msg} — pulando para o próximo.",
                      tipo="erro")
        self._proximo_foto_lote()

    def _pre_buscar_lote(self) -> None:
        """A busca do PRÓXIMO da fila roda enquanto a curadoria está aberta."""
        if self._prefetch_em_voo:
            return
        for uid in getattr(self, "_fila_fotos", []):
            if uid in self._prefetch_lote:
                continue
            it = self._item_por_uid(uid)
            if it is None:
                continue
            self._prefetch_em_voo = True
            trab = Trabalhador(lambda _st, n=it.nome, e=it.ean:
                               servico.buscar_candidatos_para(
                                   n, lambda _m: None, ean=e))

            def _guardar(cands, u=uid, ger=self._fila_geracao):
                self._prefetch_em_voo = False
                if ger == self._fila_geracao:   # a fila NOVA não herda a velha
                    self._prefetch_lote[u] = cands

            trab.ok.connect(_guardar)
            trab.erro.connect(lambda _m: setattr(self, "_prefetch_em_voo",
                                                 False))
            self._trabalhos.rodar(trab)
            return

    def _curar_foto_lote(self, uid: str, candidatos: list[str]) -> None:
        from app.qt.telas.curadoria_dialog import CuradoriaDialog

        self._overlay.esconder()
        it = self._item_por_uid(uid)
        if it is None:
            self._proximo_foto_lote()
            return
        self._pre_buscar_lote()        # o próximo busca enquanto você decide
        feitos = self._fila_fotos_total - len(self._fila_fotos)
        dlg = CuradoriaDialog(it.nome, candidatos, self, nome_editavel=False)
        dlg.setWindowTitle(f"Foto {feitos} de {self._fila_fotos_total} — "
                           f"{it.nome}")
        if dlg.exec() != CuradoriaDialog.DialogCode.Accepted:
            restam = len(self._fila_fotos)
            self._fila_fotos = []
            mostrar_toast(self, f"Fila de fotos interrompida — "
                                f"{restam + 1} item(ns) ficaram sem foto.")
            self._recarregar_lista()
            return
        tipo, valor = dlg.escolha
        if tipo == "nenhuma" or not valor:
            self._proximo_foto_lote()
            return

        def _tratar_e_definir(st, v=valor, pid=it.produto_id):
            tratada = servico.tratar_imagem(v, st)
            return servico.definir_imagem(pid, tratada, st)

        trab = Trabalhador(_tratar_e_definir)
        trab.status.connect(self._overlay.mostrar)
        trab.ok.connect(lambda d, u=uid: self._foto_lote_definida(u, d))
        trab.erro.connect(lambda m, n=it.nome: self._falhou_foto_lote(n, m))
        self._trabalhos.rodar(trab)

    def _foto_lote_definida(self, uid: str, dado: dict) -> None:
        it = self._item_por_uid(uid)
        if it is not None:
            it.imagem = dado.get("imagem")
            if it.uid in self._mapa.values():
                self._aplicar_mapa()   # a célula ganha a foto na hora
        self._recarregar_lista()
        self._marcar_salvo(False)
        self._proximo_foto_lote()

    def _editar_item(self, li: QListWidgetItem) -> None:
        """P1.4: edição rápida de nome e preço 'por' na estante."""
        from PySide6.QtWidgets import QInputDialog
        linha = self.lista.row(li)
        if not (0 <= linha < len(self._itens)):
            return
        it = self._itens[linha]
        nome, ok = QInputDialog.getText(self, "Editar item", "Nome no tabloide:",
                                        text=it.nome)
        if not ok:
            return
        preco, ok = QInputDialog.getText(self, "Editar item",
                                         "Preço da oferta (por):",
                                         text=it.preco or "")
        if not ok:
            return
        it.nome = nome.strip() or it.nome
        it.preco = preco.strip() or None
        self._recarregar_lista()
        if it.uid in self._mapa.values():
            self._aplicar_mapa()               # recompõe a grade na hora
        self._marcar_salvo(False)
        # RG-43: dica OPCIONAL de terminação (pesquisa §3) — nunca aplica só
        sugestao = servico.sugerir_terminacao(it.preco)
        if sugestao:
            mostrar_toast(self, f"Dica de preço: R$ {sugestao} no lugar de "
                                f"R$ {it.preco} — terminação 9 vende mais "
                                "(PROCON: o “de” riscado precisa ser real).")

    def _promocao_do_item(self, linha: int) -> None:
        """R-070 (casca): campo qtd+valor da promoção — grava it.multi_preco e
        recompõe a grade. 'Sem promoção' limpa e devolve o preço único."""
        if not (0 <= linha < len(self._itens)):
            return
        it = self._itens[linha]
        from app.qt.telas.promocao_dialog import PromocaoDialog
        dlg = PromocaoDialog(it.multi_preco, self)
        if dlg.exec() != PromocaoDialog.DialogCode.Accepted:
            return
        it.multi_preco = dlg.resultado          # None quando "Sem promoção"
        if dlg.resultado:
            it.preco = None                      # a promoção substitui o valor único
        self._recarregar_lista()
        if it.uid in self._mapa.values():
            self._aplicar_mapa()                 # recompõe na hora
        self._marcar_salvo(False)

    def _observacao_do_item(self, linha: int) -> None:
        """R-071 (casca): observação por item — grava it.observacao (vazio
        limpa; a região de observação é condicional, não desenha vazia)."""
        if not (0 <= linha < len(self._itens)):
            return
        it = self._itens[linha]
        from PySide6.QtWidgets import QInputDialog
        sugest = " · ".join(servico.banco_observacoes()[:3])
        texto, ok = QInputDialog.getText(
            self, "Observação do item",
            f"Recado curto (ex.: {sugest}):", text=it.observacao or "")
        if not ok:
            return
        it.observacao = texto.strip() or None
        if it.uid in self._mapa.values():
            self._aplicar_mapa()
        self._marcar_salvo(False)

    # --- auto-preencher (I1: o MAPA slot→uid é a verdade, nunca a posição) --------

    def _dados_de(self, it: servico.ItemMesa,
                  abreviacoes: dict | None = None) -> DadosProduto:
        # F7.1: `imagens` não-vazia = a lista completa que o slot desenha (F4.5)
        from app.rendering.arranjo import ModoArranjo
        from app.rendering.compositor import ImagemSlot
        try:
            arranjo = ModoArranjo(it.arranjo) if it.arranjo else ModoArranjo.LEQUE
        except ValueError:
            arranjo = ModoArranjo.LEQUE       # valor estranho: leque padrão
        # RG-22: a abreviação vale SÓ para o desenho — banco/estante intactos
        nome = (servico.abreviar_para_tabloide(it.nome, abreviacoes)
                if abreviacoes else it.nome)
        # RG-33: os selos escolhidos do item viram selos_extra do passe final
        extras = (servico.selos_do_item(it.selos, self._registro_selos)
                  if it.selos else [])
        # RG-34: item com validade cadastrada ganha "De olho na validade"
        # AUTOMÁTICO (decisão travada do padrão +18: automático é automático)
        if it.validade:
            from app.rendering.selos import Canto, Selo
            extras = extras + [Selo("VALIDADE",
                                    Canto.INFERIOR_ESQUERDO)]
        return DadosProduto(
            nome,
            selos_extra=extras,
            preco_por=servico.preco_decimal(it.preco),
            multi_preco=it.multi_preco,          # R-070: "3 por R$10"
            observacao=it.observacao,            # R-071: "limite 2 por cliente"
            imagem_path=it.imagem,
            imagens=[ImagemSlot(c) for c in (it.imagens or [])],
            modo_arranjo=arranjo,
            mais18=it.mais18,
            unidade=it.unidade,
            categoria=it.categoria,          # F8.2: as seções derivam daqui
            # RG-34: o de/até já vem como frase completa ("OFERTA VÁLIDA DE
            # …"); o legado ("ATÉ 24/07" do OCR/RG-24) ganha o prefixo
            texto_legal=(self._validade
                         if (self._validade or "").upper().startswith("OFERTA")
                         else f"Ofertas válidas {self._validade}"
                         if self._validade else None),
        )

    def _dados_por_slot(self) -> dict[str, DadosProduto]:
        """Resolve o mapa slot→uid em slot→DadosProduto (o contrato do compositor).

        F7.3: o override do slot entra AQUI — preview, pré-voo, export e
        miniatura enxergam a mesma precedência (override > item > banco).
        """
        por_uid = {it.uid: it for it in self._itens}
        abrev = servico.abreviacoes_tabloide()   # RG-22: lido 1× por recomposição
        self._registro_selos = servico.selos_disponiveis()   # RG-33: idem
        dados: dict[str, DadosProduto] = {}
        for sid, uid in self._mapa.items():
            if uid not in por_uid:
                continue
            d = self._dados_de(por_uid[uid], abrev or None)
            ov = self._overrides.get(sid)
            dados[sid] = servico.aplicar_override(d, ov) if ov else d
        return dados

    def _auto_preencher(self) -> None:
        # o canvas é a verdade (pode ter sido editado/desfeito): exporta o que se vê
        self._layout = self.area.canvas._layout or self._layout
        if self._layout is None:
            mostrar_toast(self, "Nenhum layout aberto.", tipo="erro")
            return
        from app.qt.design.carregando import cursor_espera
        with cursor_espera():            # FASE 1 (passo 75): recompõe tudo
            self._auto_preencher_miolo()

    def _auto_preencher_miolo(self) -> None:
        # cada CLIQUE repreenche: reconstrói o mapa na ordem VISUAL (y,x das
        # âncoras) e SÓ em slots ocupáveis (C5.1+A7). D8.3: as PÁGINAS entram
        # na ordem (1 → 2 → …); "fora da grade" só depois da última.
        # Fora do clique, o vínculo é por identidade (uid).
        from app.rendering.grade import ocupaveis, ordenar_slots_visualmente
        por_pagina: list[int] = []
        slots: list = []
        for pagina in self._layout.paginas:
            uteis = ocupaveis(ordenar_slots_visualmente(pagina.slots))
            slots.extend(uteis)
            por_pagina.append(len(uteis))
        # F8/A2: agrupar = ordenar a fila por categoria ANTES de zipar; o
        # vínculo continua sendo slot→uid (a estante em si não muda de ordem)
        fila = list(self._itens)
        if self.chk_agrupar.isChecked():
            from app.core.database import Database
            db = Database().init()
            try:
                with db.Session() as s:
                    ordem = servico.categorias_ordenadas(s)
            finally:
                db.engine.dispose()
            fila = servico.ordenar_por_categoria(fila, ordem)
        # RG-42: heróis abrem a capa (os mais baratos nos primeiros slots
        # da página 1) — vale por cima da ordem agrupada/importada
        if self.chk_herois.isChecked() and por_pagina:
            fila = servico.ordenar_com_herois(fila, min(4, por_pagina[0]))
        # F8.2: agrupar liga as seções em TODAS as páginas (por página o
        # humano pode desligar depois — B3); desagrupar desliga
        for pag in self._layout.paginas:
            pag.secoes_ligadas = self.chk_agrupar.isChecked()
        self._mapa = {slot.id: it.uid for slot, it in zip(slots, fila)}
        self._aplicar_mapa()
        extra = len(self._itens) - len(self._mapa)
        aviso = f" ({extra} fora da grade)" if extra > 0 else ""
        # RG-42: medidor de densidade — respiro vende (60-30-10 da pesquisa)
        from app.rendering.grade import ocupaveis as _ocup
        dados_slot = self._dados_por_slot()
        densa = [f"pág. {i}" for i, pag in enumerate(self._layout.paginas, 1)
                 if len(_ocup(pag.slots)) > 6
                 and servico.densidade_da_pagina(pag, dados_slot) > 0.9]
        if densa:
            aviso += (f" · {', '.join(densa)} bem cheia(s) — um respiro "
                      "valoriza as ofertas")
        contagem = " + ".join(str(min(n, max(0, len(self._itens) - sum(por_pagina[:i]))))
                              for i, n in enumerate(por_pagina)) \
            if len(por_pagina) > 1 else str(len(self._mapa))
        mostrar_toast(self, f"Preenchido: {contagem} itens por página.{aviso}"
                      if len(por_pagina) > 1
                      else f"Grade preenchida com {len(self._mapa)} itens.{aviso}")
        self._recarregar_lista()

    def _aplicar_mapa(self) -> None:
        """Recompõe o canvas a partir do mapa (usado no preencher e no reabrir)."""
        self.area.carregar(self._layout, self._dados_por_slot(), self._fundo)
        self.btn_exportar.setEnabled(bool(self._mapa))
        self._atualizar_nav()

    # --- exportar -----------------------------------------------------------------

    def _avisos_orfaos(self) -> list[str]:
        """Entradas do mapa/overrides apontando p/ célula removida (I2)."""
        ids = {s.id for pag in self._layout.paginas for s in pag.slots}
        por_uid = {it.uid: it for it in self._itens}
        avisos = [f"“{por_uid[u].nome}” aponta para célula removida"
                  for sid, u in self._mapa.items()
                  if sid not in ids and u in por_uid]
        avisos += [f"override da célula “{sid}” aponta para célula removida"
                   for sid in self._overrides if sid not in ids]
        return avisos

    def paginas_compostas(self):
        """As páginas do tabloide JÁ compostas (lista de PIL Images) — reuso
        único para exportar, formatos sociais e vídeo (uma cadeia só, F8)."""
        self._layout = self.area.canvas._layout or self._layout
        layout, fundo = self._layout, self._fundo
        if layout is None:                   # sem arte carregada: nada a compor
            return []
        dados = self._dados_por_slot()
        return [compor_pagina(layout, pag, dados,
                              fundo_path=fundo if i == 0 else None)
                for i, pag in enumerate(layout.paginas)]

    def esta_aprovado(self) -> bool:
        """R-068: aprovado E sem edição pendente — editar em memória sem salvar
        derruba a aprovação (a marca d'água RASCUNHO volta até reaprovar). Assim
        o buraco "editei mas não salvei, e exportei limpo" não existe."""
        if not getattr(self, "_salvo", False):
            return False
        return servico.pode_exportar_limpo(self._projeto_id)

    def aprovar_projeto_atual(self) -> bool:
        """R-068: aprova SE o checklist da F7 passar (não é clique cego). Salva
        o projeto antes (a aprovação é por id). Devolve True se aprovou."""
        if self._projeto_id is None:
            self._salvar_projeto()
            if self._projeto_id is None:      # o dono cancelou o salvar
                return False
        ok, faltas = servico.aprovar_projeto(
            self._projeto_id, self._itens, self._validade)
        if not ok:
            mostrar_toast(self, "Ainda não dá para aprovar — falta: "
                          + "; ".join(faltas), tipo="erro")
            return False
        mostrar_toast(self, "Projeto APROVADO — a exportação limpa (sem "
                            "“RASCUNHO”) está liberada.", tipo="sucesso")
        return True

    def _exportar(self) -> None:
        from app.qt.telas.prevoo import confirmar_pre_voo

        self._layout = self.area.canvas._layout or self._layout
        dados = self._dados_por_slot()
        avisos = (servico.validar_composicao(self._layout, dados)
                  + self._avisos_orfaos())
        if not confirmar_pre_voo(self, avisos, "Exportar"):   # I2: nada em silêncio
            return
        # R-067: enquanto NÃO aprovado, a peça sai com a marca d'água RASCUNHO
        # (automática — não depende de o dono lembrar). Some só na aprovação.
        marca = not self.esta_aprovado()
        caminho, filtro = QFileDialog.getSaveFileName(
            self, "Exportar tabloide", "tabloide.png",
            "PNG (*.png);;PDF (*.pdf)")
        if not caminho:
            return
        pdf = caminho.lower().endswith(".pdf") or "PDF" in filtro
        layout, fundo = self._layout, self._fundo

        def _trabalho(st):
            # D8.5: compõe TODAS as páginas; PNG = _p1.._pN; PDF = multipágina
            imgs = []
            total = len(layout.paginas)
            for i, pag in enumerate(layout.paginas):
                st(f"Compondo página {i + 1}/{total}…")
                imgs.append(compor_pagina(layout, pag, dados,
                                          fundo_path=fundo if i == 0 else None))
            if marca:                       # R-067: marca d'água RASCUNHO
                from app.rendering.marca_dagua import carimbar_rascunho
                imgs = [carimbar_rascunho(im) for im in imgs]
            st("Gravando o arquivo…")
            from app.rendering.cmyk import pos_processar_export
            from app.rendering.export import (
                exportar_pdf, exportar_pdf_multipagina, exportar_png,
            )
            if pdf:
                if total > 1:
                    saida = exportar_pdf_multipagina(imgs, caminho, layout.dpi)
                else:
                    saida = exportar_pdf(imgs[0], caminho, layout.dpi)
                # F7.5: CMYK opcional — com ele desligado, nenhum byte muda
                return pos_processar_export(saida, st)
            if total == 1:
                return exportar_png(imgs[0], caminho, layout.dpi), None
            base = Path(caminho)
            ultimo = None
            for i, img in enumerate(imgs, start=1):
                ultimo = exportar_png(
                    img, base.with_name(f"{base.stem}_p{i}{base.suffix}"),
                    layout.dpi)
            return ultimo, None

        trab = Trabalhador(_trabalho)
        trab.status.connect(self._overlay.mostrar)
        trab.ok.connect(self._exportado)
        trab.erro.connect(self._falhou)
        self._trabalhos.rodar(trab)

    def _exportado(self, resultado) -> None:
        self._overlay.esconder()
        caminho, aviso = resultado
        sufixo = f" — {aviso}" if aviso else ""
        mostrar_toast(self, f"Tabloide exportado: {Path(caminho).name}{sufixo}")
        from app.qt.design.som import tocar_exportou
        tocar_exportou()                 # FASE 1 (passo 74): opcional
        if self._projeto_id is not None:  # FASE 2 (passo 36): transição
            from app.core.projetos import marcar_status, registrar_export
            marcar_status(self._projeto_id, "exportado")
            registrar_export(self._projeto_id, caminho)   # passo 94

    def _falhou(self, msg: str) -> None:
        self._overlay.esconder()
        mostrar_toast(self, msg, tipo="erro")

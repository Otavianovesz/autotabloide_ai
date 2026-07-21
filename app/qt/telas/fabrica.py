"""
Fábrica — cartazes de gôndola (F6.5)
====================================
O segundo produto do app: **1 item = 1 página**, preço "de" riscado + "por"
grande, validade do item quando perto de vencer, preview ao clicar, e
**exportar = PDF multipágina no tamanho exato** (sem imposição/NUP).

Reusa a máquina da Mesa: importar (tabela/foto) → conciliação com o semáforo.
O cartaz exige descrição + "de" + "por": os incompletos ficam marcados e fora
do PDF (dá para completar no painel do item).
"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.qt.canvas import pil_para_qpixmap
from app.qt.design import tokens as t
from app.qt.design.carregando import OverlayOcupado
from app.qt.design.componentes import EstadoVazio, Painel
from app.qt.design.icones import icone
from app.qt.design.toast import mostrar_toast
from app.qt.telas import servico
from app.qt.telas.conciliacao_dialog import ConciliacaoDialog
from app.qt.workers import GerenciadorTrabalhos, Trabalhador
from app.rendering.cartaz import PRESETS_CARTAZ, layout_cartaz_exemplo
from app.rendering.compositor import DadosProduto, compor_pagina


class FabricaTela(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._layout = layout_cartaz_exemplo()   # placeholder até a arte real
        self._layout_nome = "Cartaz 10×15 — exemplo"
        self._itens: list[servico.ItemMesa] = []
        self._trabalhos = GerenciadorTrabalhos()
        self._atualizando = False
        self.ao_salvo = None           # callable(bool) → indicador do rodapé
        self.ao_documento = None       # callable(str) → título da janela (77)
        self._projeto_id = None        # FASE 2 (passo 36): status por projeto

        # --- barra de ações -----------------------------------------------------
        barra = QWidget()
        barra.setObjectName("barraFerramentas")
        hb = QHBoxLayout(barra)
        hb.setContentsMargins(t.ESP_3, t.ESP_1 + 2, t.ESP_3, t.ESP_1 + 2)
        hb.setSpacing(t.ESP_2)
        importar = QPushButton(" Importar tabela/foto")
        importar.setIcon(icone("abrir", cor=t.ACENTO_TEXTO, tamanho=16))
        importar.setProperty("tipo", "primario")
        importar.setToolTip("Importa a tabela ou a foto das ofertas — "
                            "cada item vira um cartaz")
        importar.clicked.connect(self._importar)
        # R-105 (Fase 11): a biblioteca de layouts de cartaz (A4/A5/etiqueta)
        self.combo_layout = QComboBox()
        self.combo_layout.addItems(list(PRESETS_CARTAZ.keys()))
        self.combo_layout.setToolTip(
            "Modelo do cartaz — 1 item por página no tamanho físico exato")
        self.btn_exportar = QPushButton(" Exportar PDF")
        self.btn_exportar.setIcon(icone("impressora", tamanho=16))
        self.btn_exportar.setToolTip(
            "PDF multipágina — cada página um cartaz no tamanho exato")
        self.btn_exportar.setEnabled(False)
        self.btn_exportar.clicked.connect(self._exportar)
        # R-112 (Fase 11): imprimir direto na fila do Windows
        self.btn_imprimir = QPushButton(" Imprimir")
        self.btn_imprimir.setIcon(icone("impressora", tamanho=16))
        self.btn_imprimir.setToolTip(
            "Manda direto para a impressora, no tamanho físico exato")
        self.btn_imprimir.setEnabled(False)
        self.btn_imprimir.clicked.connect(self._imprimir)
        # R-106 (Fase 11): 2-em-1 (dois A5 por A4) — SÓ no cartaz, só se ligar
        self.chk_2em1 = QCheckBox("Dois por folha")
        self.chk_2em1.setToolTip(
            "2-em-1: dois cartazes A5 numa folha A4 (economiza papel)")
        # R-144 (FASE 12): etiquetas de prateleira em LOTE — dezenas por folha
        self.btn_etiquetas = QPushButton(" Etiquetas em lote")
        self.btn_etiquetas.setIcon(icone("impressora", tamanho=16))
        self.btn_etiquetas.setToolTip(
            "Uma etiqueta (100×70 mm) por item do lote atual, várias por "
            "folha A4 com marcas de corte — para a prateleira inteira")
        self.btn_etiquetas.setEnabled(False)
        self.btn_etiquetas.clicked.connect(self._etiquetas_lote)
        # R-108 (Fase 11): lote por categoria (reusa o filtro da estante)
        self.combo_categoria = QComboBox()
        self.combo_categoria.setToolTip("Imprimir/exportar só uma categoria")
        self.combo_categoria.addItem("Todas as categorias")
        self.btn_salvar_proj = QPushButton(" Salvar projeto")
        self.btn_salvar_proj.setIcon(icone("cofre", tamanho=16))
        self.btn_salvar_proj.setToolTip(
            "Congela os cartazes (dados da época) — reabre idêntico")
        self.btn_salvar_proj.setEnabled(False)
        self.btn_salvar_proj.clicked.connect(self._salvar_projeto)
        btn_abrir_proj = QPushButton(" Abrir projeto")
        btn_abrir_proj.setIcon(icone("abrir", tamanho=16))
        btn_abrir_proj.setToolTip("Abrir um projeto de cartazes congelado")
        btn_abrir_proj.clicked.connect(self._abrir_projeto)
        self._resumo = QLabel("")
        self._resumo.setProperty("papel", "legenda")
        # RG-53 (polimento): a barra da Fábrica ganhou muitos controles (modelo,
        # lote, 2-em-1, imprimir…) e NÃO aplicava o padrão da Mesa — a 720p ela
        # pinava a janela mais larga que a tela. Mesmo remédio: grupos com
        # separador, combos que encolhem, "···" herda o que não couber.
        from PySide6.QtWidgets import QComboBox as _QCB, QFrame, QMenu, QToolButton
        for combo in (self.combo_layout, self.combo_categoria):
            combo.setSizeAdjustPolicy(
                _QCB.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon)
            combo.setMinimumContentsLength(12)

        def _sep_barra():
            f = QFrame()
            f.setProperty("papel", "separador")
            f.setFrameShape(QFrame.Shape.VLine)
            return f

        lbl_modelo = QLabel("Modelo:")
        lbl_lote = QLabel("Lote:")
        for grupo in (
            [importar],
            [lbl_modelo, self.combo_layout],
            [lbl_lote, self.combo_categoria, self.chk_2em1],
            [self.btn_exportar, self.btn_imprimir, self.btn_etiquetas],
            [self.btn_salvar_proj, btn_abrir_proj],
        ):
            if hb.count() > 0:
                hb.addWidget(_sep_barra())
            for w in grupo:
                hb.addWidget(w)
        self._mais_fabrica = QToolButton()
        self._mais_fabrica.setText("···")
        self._mais_fabrica.setToolTip("Mais ações (janela estreita)")
        self._mais_fabrica.setPopupMode(
            QToolButton.ToolButtonPopupMode.InstantPopup)
        self._mais_fabrica.setMenu(QMenu(self._mais_fabrica))
        self._mais_fabrica.hide()
        hb.addWidget(self._mais_fabrica)
        hb.addStretch(1)
        hb.addWidget(self._resumo)
        self._barra_fabrica = barra
        self._barra_layout = hb
        # a barra PODE encolher abaixo do conteúdo (senão a janela fica presa
        # na largura da barra e transborda a 720p — a lição da Mesa)
        barra.setMinimumWidth(1)
        # ordem de sacrifício: o PRIMEIRO colapsa primeiro
        self._sacrificaveis = [
            (btn_abrir_proj, "Abrir projeto", "botao"),
            (self.chk_2em1, "Dois por folha", "check"),
            (self.btn_etiquetas, "Etiquetas em lote", "botao"),
            (self.btn_salvar_proj, "Salvar projeto", "botao"),
            (self.btn_imprimir, "Imprimir", "botao"),
        ]

        # --- corpo: lista + preview/campos ---------------------------------------
        self.lista = QListWidget()
        self.lista.currentRowChanged.connect(self._selecionou)
        self.lista.itemDoubleClicked.connect(self._editar_item)
        # FASE 1 (passo 73): estado vazio com AÇÃO
        btn_vazio = QPushButton(" Importar tabela/foto")
        btn_vazio.setIcon(icone("abrir", tamanho=16))
        btn_vazio.clicked.connect(self._importar)
        self._vazio = EstadoVazio(
            "impressora", "Nenhum cartaz ainda",
            "Importe a tabela/foto das ofertas —\ncada item vira uma página.",
            acao=btn_vazio)
        caixa_lista = QWidget()
        vl = QVBoxLayout(caixa_lista)
        vl.setContentsMargins(0, 0, 0, 0)
        vl.addWidget(self._vazio)
        vl.addWidget(self.lista)
        self.lista.hide()

        self.preview = QLabel("Clique num item para ver o cartaz")
        self.preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview.setMinimumSize(320, 460)
        self.preview.setProperty("papel", "legenda")

        self.campo_por = QLineEdit()
        self.campo_por.setPlaceholderText("ex.: 9,99 — o preço da oferta")
        self.campo_por.editingFinished.connect(self._editou_campos)
        self.campo_de = QLineEdit()
        self.campo_de.setPlaceholderText("ex.: 12,99 (obrigatório no cartaz)")
        self.campo_de.editingFinished.connect(self._editou_campos)
        self.campo_validade = QLineEdit()
        self.campo_validade.setPlaceholderText("só quando perto de vencer")
        self.campo_validade.editingFinished.connect(self._editou_campos)
        form = QFormLayout()
        form.setVerticalSpacing(t.ESP_2)
        form.addRow("Preço “por”", self.campo_por)
        form.addRow("Preço “de”", self.campo_de)
        form.addRow("Validade", self.campo_validade)
        campos = QWidget()
        campos.setLayout(form)

        painel_preview = QWidget()
        vp = QVBoxLayout(painel_preview)
        vp.setContentsMargins(0, 0, 0, 0)
        vp.setSpacing(t.ESP_2)
        vp.addWidget(self.preview, 1)
        vp.addWidget(campos)

        esquerda = QWidget()
        esquerda.setObjectName("lateral")
        ve = QVBoxLayout(esquerda)
        ve.setContentsMargins(t.ESP_3, t.ESP_3, t.ESP_3, t.ESP_3)
        self._painel_cartazes = Painel("Cartazes (1 por página)", "impressora",
                                       caixa_lista)
        ve.addWidget(self._painel_cartazes)

        direita = QWidget()
        vd = QVBoxLayout(direita)
        vd.setContentsMargins(t.ESP_3, t.ESP_3, t.ESP_3, t.ESP_3)
        vd.addWidget(Painel("Cartaz", "imagem", painel_preview))

        # FASE 1 (passo 59): a lista de cartazes em splitter com memória
        from app.qt.design.componentes import splitter_com_memoria
        corpo = splitter_com_memoria("fabrica", esquerda, direita,
                                     indice_lateral=0)

        raiz = QVBoxLayout(self)
        raiz.setContentsMargins(0, 0, 0, 0)
        raiz.setSpacing(0)
        raiz.addWidget(barra)
        raiz.addWidget(corpo, 1)

        self._overlay = OverlayOcupado(self)
        # conectado só agora: evita disparo no addItems antes de a lista existir
        self.combo_layout.currentTextChanged.connect(self._escolher_preset)
        self._atualizar_2em1_disponivel()   # estado inicial do "Dois por folha"

    # --- layout escolhido no Ateliê -----------------------------------------------

    def _escolher_preset(self, nome: str) -> None:
        """R-105: aplica um layout da biblioteca e mostra a prévia no tamanho
        real. Projeto congelado não troca de modelo (decisão travada)."""
        if self._atualizando or nome not in PRESETS_CARTAZ:
            return
        if getattr(self, "_congelado", False):
            mostrar_toast(self, "Projeto congelado não troca de modelo.",
                          tipo="info")
            return
        self._layout = PRESETS_CARTAZ[nome]()
        self._layout_nome = nome            # não está no banco → sync não mexe
        self._atualizar_2em1_disponivel()
        self._marcar_salvo(False)
        it = self._item_atual()
        if it is not None:
            self._compor_preview(it)

    def _atualizar_2em1_disponivel(self) -> None:
        """R-106: o 2-em-1 só cabe num A5 (metade do A4 paisagem). Fora disso,
        desabilita o "Dois por folha" (nunca cortar calado — I2, achado da frota)."""
        lay = self._layout
        cabe = (lay.largura_mm <= 148.5 and lay.altura_mm <= 210.5)
        self.chk_2em1.setEnabled(cabe)
        if not cabe and self.chk_2em1.isChecked():
            self.chk_2em1.setChecked(False)
        self.chk_2em1.setToolTip(
            "2-em-1: dois cartazes A5 numa folha A4 (economiza papel)" if cabe
            else "Só para o modelo A5/etiqueta — o cartaz precisa caber na "
                 "metade da folha")

    def carregar_layout(self, layout, nome_layout: str | None = None) -> None:
        """Usa um layout de cartaz vindo do Ateliê (fim do hardcode)."""
        import json
        self._layout = layout
        if nome_layout:
            self._layout_nome = nome_layout
        # RG-08: assinatura p/ o showEvent re-sincronizar com o Ateliê
        self._assinatura_layout = json.dumps(layout.to_dict(), sort_keys=True)
        self._congelado = False
        self._atualizar_2em1_disponivel()   # 2-em-1 só cabe no A5 (achado da frota)
        it = self._item_atual()
        if it is not None:
            self._compor_preview(it)

    def showEvent(self, ev) -> None:  # noqa: N802 (Qt)
        super().showEvent(ev)
        self._sincronizar_do_atelie()
        self._reflow_barra()             # RG-53: cabe do jeito que abrir

    def resizeEvent(self, ev) -> None:  # noqa: N802 (Qt)
        super().resizeEvent(ev)
        self._reflow_barra()

    def _reflow_barra(self) -> None:
        """RG-53 (portado da Mesa): o que couber com folga fica na barra; o
        resto colapsa no "···" (checkbox vira ação checável espelhada — nada
        some). A medição é GENÉRICA: soma TODO widget fixo (botões, checks,
        rótulos, combos, separadores), não só QPushButton."""
        if not hasattr(self, "_mais_fabrica"):
            return
        if self._barra_fabrica.width() < 60:
            return          # layout ainda não assentou — medir agora colapsaria
                            # tudo por largura falsa (o resize sintético re-chama)
        esp = t.ESP_2
        sacrificaveis = {id(w) for w, _r, _t in self._sacrificaveis}
        base = 2 * t.ESP_3 + esp + self._mais_fabrica.sizeHint().width() + esp
        lay = self._barra_layout
        for i in range(lay.count()):
            w = lay.itemAt(i).widget()
            if w is None or w is self._mais_fabrica or id(w) in sacrificaveis:
                continue
            base += w.sizeHint().width() + esp
        # folga 24 (era 8) — mesmo conserto do GATE 2.2 da Mesa (a soma de
        # sizeHints subestima as margens internas; ninguém encolhe)
        resto = self._barra_fabrica.width() - 24 - base
        ficam: list[int] = []
        colapsados = []
        for w, rotulo, tipo in reversed(self._sacrificaveis):
            custo = w.sizeHint().width() + esp
            if resto - custo >= 0:
                resto -= custo
                ficam.append(id(w))
            else:
                colapsados.append((w, rotulo, tipo))
        for w, _r, _t in self._sacrificaveis:
            w.setVisible(id(w) in ficam)
        menu = self._mais_fabrica.menu()
        menu.clear()
        for w, rotulo, tipo in colapsados:
            if tipo == "check":
                acao = menu.addAction(rotulo)
                acao.setCheckable(True)
                acao.setChecked(w.isChecked())
                acao.toggled.connect(w.setChecked)
                acao.setEnabled(w.isEnabled())
            else:
                acao = menu.addAction(w.icon(), rotulo, w.click)
                acao.setEnabled(w.isEnabled())
        self._mais_fabrica.setVisible(bool(colapsados))
        # RG-53 estágio 2 (GATE 2.2): fixos só-ícone quando nem assim cabe
        from app.qt.design.componentes import modo_compacto_botoes
        if not hasattr(self, "_botoes_compactos"):
            self._botoes_compactos = {}
        modo_compacto_botoes(
            lay, self._mais_fabrica, sacrificaveis, self._botoes_compactos,
            self._barra_fabrica.width() - 24 - 2 * t.ESP_3, esp)

    def _sincronizar_do_atelie(self) -> None:
        """RG-08: salvar o layout de cartaz no Ateliê reflete na Fábrica ao
        trocar de tela (a percepção de 'salvei e não mudou' da auditoria).
        Projeto congelado nunca re-sincroniza (decisão travada)."""
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
            return
        self.carregar_layout(novo, nome_layout=self._layout_nome)
        mostrar_toast(self, f"Layout “{self._layout_nome}” atualizado do "
                            "Ateliê.")

    # --- projeto salvo congelado (§3.1/§6.8) --------------------------------------

    def _marcar_salvo(self, salvo: bool) -> None:
        if callable(self.ao_salvo):
            self.ao_salvo(salvo)

    def _salvar_projeto(self) -> None:
        from app.core import projetos
        from app.qt.telas.prevoo import confirmar_pre_voo
        from app.qt.telas.projetos_dialog import SalvarProjetoDialog

        if not self._itens:
            mostrar_toast(self, "Nada para salvar — importe itens antes.", tipo="erro")
            return
        dlg = SalvarProjetoDialog(parent=self)
        if dlg.exec() != SalvarProjetoDialog.DialogCode.Accepted:
            return
        nome, evento = dlg.valores()
        # A2: o pré-voo do cartaz (PROCON incluso) vale também para SALVAR
        if not confirmar_pre_voo(self, self._avisos_pre_voo(), "Salvar"):
            return
        from app.qt.design.carregando import cursor_espera
        with cursor_espera():            # FASE 1 (passo 75)
            self._projeto_id = projetos.salvar_projeto(
                nome, evento, "CARTAZ", self._layout,
                [it.to_dict() for it in self._itens], None,
                nome_layout=self._layout_nome)
        self._marcar_salvo(True)
        if callable(self.ao_documento):
            self.ao_documento(nome)      # título da janela (passo 77)
        mostrar_toast(self, f"Projeto “{nome}” salvo (dados congelados).")

    def _abrir_projeto(self) -> None:
        from app.core import projetos
        from app.qt.telas.projetos_dialog import AbrirProjetoDialog

        dlg = AbrirProjetoDialog(tipo="CARTAZ", parent=self)
        if dlg.exec() != AbrirProjetoDialog.DialogCode.Accepted or dlg.projeto_id is None:
            return
        from app.qt.design.carregando import cursor_espera
        with cursor_espera():            # FASE 1 (passo 75)
            p = projetos.abrir_projeto(dlg.projeto_id)
            if p is not None:
                self.abrir_projeto_congelado(p)

    def abrir_projeto_congelado(self, p) -> None:
        """Reabre um ProjetoAberto idêntico (usado pelo diálogo e pelo Dashboard)."""
        self._itens = [servico.ItemMesa.from_dict(d) for d in p.itens]
        self._projeto_id = p.id          # FASE 2 (passo 36)
        from app.core.projetos import registrar_ultimo_aberto
        registrar_ultimo_aberto(p.id)    # FASE 2 (passo 48)
        if callable(self.ao_documento):
            self.ao_documento(p.nome)    # título da janela (passo 77)
        self.carregar_layout(p.layout)
        self._congelado = True    # RG-08: congelado não re-sincroniza (travada)
        self._recarregar_lista()
        self.btn_salvar_proj.setEnabled(bool(self._itens))
        if self._itens:
            self.lista.setCurrentRow(0)
        self._marcar_salvo(True)
        mostrar_toast(self, f"“{p.nome}” aberto — congelado de {p.criado_em}.")

    # --- importar (a mesma máquina da Mesa) --------------------------------------

    def _importar(self) -> None:
        caminho, _ = QFileDialog.getOpenFileName(
            self, "Importar oferta", "",
            "Ofertas (*.png *.jpg *.jpeg *.webp *.txt);;Todos (*.*)")
        if not caminho:
            return
        trab = Trabalhador(lambda st, c=caminho: servico.importar_ofertas(c, st))
        trab.status.connect(self._overlay.mostrar)
        trab.ok.connect(self._conciliar)
        trab.erro.connect(self._falhou)
        self._trabalhos.rodar(trab)

    def _conciliar(self, resultado: servico.ResultadoMesa) -> None:
        self._overlay.esconder()
        if resultado.aviso:            # RG-04: o cache-hit do OCR fica visível
            mostrar_toast(self, resultado.aviso)
        dlg = ConciliacaoDialog(resultado, self)
        if getattr(dlg, "_tela_cheia", False):
            dlg.showMaximized()        # R-052: fonte-foto abre em tela cheia
        if dlg.exec() != ConciliacaoDialog.DialogCode.Accepted:
            return
        self._itens = [it for it in dlg.itens if it.semaforo == "VERDE"]
        self._recarregar_lista()
        self.btn_salvar_proj.setEnabled(bool(self._itens))
        self._marcar_salvo(False)
        if self._itens:
            self.lista.setCurrentRow(0)

    # --- lista / completude --------------------------------------------------------

    def _completo(self, it: servico.ItemMesa) -> bool:
        """Cartaz exige descrição + preço 'de' + preço 'por'."""
        return bool(it.nome and servico.preco_decimal(it.preco)
                    and servico.preco_decimal(it.preco_de))

    def _recarregar_lista(self) -> None:
        self._vazio.setVisible(not self._itens)
        self.lista.setVisible(bool(self._itens))
        # FASE 1 (passo 76): contador vivo no título do painel
        self._painel_cartazes.set_titulo(
            f"Cartazes (1 por página) · {len(self._itens)}")
        linha = self.lista.currentRow()
        self.lista.blockSignals(True)
        self.lista.clear()
        for it in self._itens:
            li = QListWidgetItem(self.lista)
            faltas = []
            if not (it.nome or "").strip():
                faltas.append("nome")
            if servico.preco_decimal(it.preco) is None:
                faltas.append("preço “por”")
            if servico.preco_decimal(it.preco_de) is None:
                faltas.append("preço “de”")
            falta = "" if not faltas else \
                f'  <span style="color:{t.ALERTA}">⚠ falta {" e ".join(faltas)}</span>'
            rotulo = QLabel(
                f'{it.nome}<br><span style="color:{t.TEXTO_3}">'
                f'de {it.preco_de or "—"} · por {it.preco or "—"}</span>{falta}')
            rotulo.setToolTip("Duplo-clique: editar nome e preço deste cartaz")
            rotulo.setContentsMargins(t.ESP_2, 3, t.ESP_2, 3)
            li.setSizeHint(rotulo.sizeHint())
            self.lista.setItemWidget(li, rotulo)
        self.lista.blockSignals(False)
        if 0 <= linha < self.lista.count():
            self.lista.setCurrentRow(linha)
        prontos = sum(1 for it in self._itens if self._completo(it))
        self._resumo.setText(
            f"{prontos} de {len(self._itens)} cartazes prontos" if self._itens else "")
        self.btn_exportar.setEnabled(prontos > 0)
        self.btn_imprimir.setEnabled(prontos > 0)
        self.btn_etiquetas.setEnabled(prontos > 0)   # R-144 acompanha o lote
        self._atualizar_categorias()

    def _atualizar_categorias(self) -> None:
        """R-108: popula o lote com as categorias presentes (mantém a escolha)."""
        from app.qt.telas.servico import OUTROS
        atual = self.combo_categoria.currentText()
        cats = sorted({(it.categoria or OUTROS) for it in self._itens})
        self.combo_categoria.blockSignals(True)
        self.combo_categoria.clear()
        self.combo_categoria.addItem("Todas as categorias")
        self.combo_categoria.addItems(cats)
        i = self.combo_categoria.findText(atual)
        self.combo_categoria.setCurrentIndex(i if i >= 0 else 0)
        self.combo_categoria.blockSignals(False)

    def _prontos_para_saida(self) -> list:
        """R-108: os cartazes prontos, filtrados pela categoria do lote (reusa o
        filtro da estante — uma lógica só)."""
        prontos = [it for it in self._itens if self._completo(it)]
        cat = self.combo_categoria.currentText()
        if cat and cat != "Todas as categorias":
            prontos = servico.filtrar_itens(prontos, categoria=cat)
        return prontos

    # --- item selecionado: campos + preview ------------------------------------------

    def _item_atual(self) -> servico.ItemMesa | None:
        i = self.lista.currentRow()
        return self._itens[i] if 0 <= i < len(self._itens) else None

    def _selecionou(self, _linha: int) -> None:
        it = self._item_atual()
        if it is None:
            return
        self._atualizando = True
        self.campo_por.setText(it.preco or "")
        self.campo_de.setText(it.preco_de or "")
        self.campo_validade.setText(it.validade or "")
        self._atualizando = False
        self._compor_preview(it)

    def _editou_campos(self) -> None:
        it = self._item_atual()
        if it is None or self._atualizando:
            return
        it.preco = self.campo_por.text().strip() or None
        it.preco_de = self.campo_de.text().strip() or None
        it.validade = self.campo_validade.text().strip() or None
        self._marcar_salvo(False)
        self._recarregar_lista()
        self._compor_preview(it)

    def _editar_item(self, li: QListWidgetItem) -> None:
        """A1 do Bloco D: nome e preço “por” pelo duplo-clique — paridade com a Mesa."""
        from PySide6.QtWidgets import QInputDialog
        linha = self.lista.row(li)
        if not (0 <= linha < len(self._itens)):
            return
        it = self._itens[linha]
        nome, ok = QInputDialog.getText(self, "Editar cartaz", "Nome no cartaz:",
                                        text=it.nome)
        if not ok:
            return
        preco, ok = QInputDialog.getText(self, "Editar cartaz",
                                         "Preço da oferta (por):",
                                         text=it.preco or "")
        if not ok:
            return
        it.nome = nome.strip() or it.nome
        it.preco = preco.strip() or None
        self._marcar_salvo(False)
        self._recarregar_lista()          # re-seleciona a linha → campos + preview

    def _dados(self, it: servico.ItemMesa) -> DadosProduto:
        return DadosProduto(
            it.nome,
            preco_de=servico.preco_decimal(it.preco_de),
            preco_por=servico.preco_decimal(it.preco),
            imagem_path=it.imagem,
            mais18=it.mais18,
            texto_legal=f"Válido até {it.validade}" if it.validade else None,
        )

    def _compor_preview(self, it: servico.ItemMesa) -> None:
        img = compor_pagina(self._layout, self._layout.paginas[0], self._dados(it))
        pm = pil_para_qpixmap(img)
        alvo = self.preview.size()
        self.preview.setPixmap(pm.scaled(
            alvo, Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation))

    # --- pré-voo (A2 do Bloco D: cartaz=True em TODOS os caminhos) ---------------------

    def _avisos_pre_voo(self) -> list[str]:
        """Pendências por cartaz (I2): foto sumida, preços, “de” ≤ “por” (PROCON).

        A4: 1 item = 1 página — o rótulo diz a página que o cartaz ocupa no
        PDF; item incompleto fica FORA do PDF e é rotulado assim.
        """
        avisos: list[str] = []
        slot_id = self._layout.paginas[0].slots[0].id
        pagina = 0
        # o pré-voo cobre EXATAMENTE o que vai sair — o lote filtrado por
        # categoria, para os números de página baterem com o PDF (achado da frota)
        cat = self.combo_categoria.currentText()
        itens = (servico.filtrar_itens(self._itens, categoria=cat)
                 if cat and cat != "Todas as categorias" else self._itens)
        for it in itens:
            if self._completo(it):
                pagina += 1
                rotulo = f"página {pagina}"
            else:
                rotulo = "fora do PDF"
            pend = servico.validar_composicao(
                self._layout, {slot_id: self._dados(it)}, cartaz=True)
            avisos.extend(p.replace(slot_id, rotulo, 1) for p in pend)
        vistos: set[str] = set()           # aviso de fonte repete por item — 1 basta
        return [a for a in avisos if not (a in vistos or vistos.add(a))]

    # --- exportar ---------------------------------------------------------------------

    def _compor_paginas(self, st, prontos, layout, marca: bool, impor: bool):
        """Compõe as páginas dos cartazes prontos (upscale + marca d'água +
        2-em-1 opcional). Fonte ÚNICA do export e da impressão."""
        from dataclasses import replace

        from app.rendering.model import TipoRegiao
        from app.rendering.units import mm_para_px

        reg_img = next((r for s in layout.paginas[0].slots
                        for r in s.regioes
                        if r.tipo == TipoRegiao.IMAGEM), None)
        lado_alvo = (round(mm_para_px(
            max(reg_img.rect.larg_mm, reg_img.rect.alt_mm), layout.dpi))
            if reg_img is not None else 0)
        paginas = []
        for i, it in enumerate(prontos, 1):
            st(f"Compondo cartaz {i}/{len(prontos)}…")
            d = self._dados(it)
            if d.imagem_path and lado_alvo:       # RG-32: upscale no fluxo
                d = replace(d, imagem_path=servico.upscale_para_cartaz(
                    d.imagem_path, lado_alvo, st))
            paginas.append(compor_pagina(layout, layout.paginas[0], d))
        if marca:                                  # R-067: marca d'água RASCUNHO
            from app.rendering.marca_dagua import carimbar_rascunho
            paginas = [carimbar_rascunho(p) for p in paginas]
        if impor and paginas:                      # R-106: 2-em-1 (só no cartaz)
            st("Impondo dois por folha…")
            from app.rendering.imposicao import impor_2em1
            paginas = impor_2em1(paginas, layout.dpi, marcas_corte=True)
        return paginas

    def _etiquetas_lote(self) -> None:
        """R-144 (FASE 12): as etiquetas do LOTE atual (respeita o filtro de
        categoria) impostas em folhas A4 — pré-voo antes, worker durante."""
        from app.qt.telas.prevoo import confirmar_pre_voo
        if not confirmar_pre_voo(self, self._avisos_pre_voo(),
                                 "Etiquetas em lote"):
            return
        caminho, _ = QFileDialog.getSaveFileName(
            self, "Etiquetas em lote", "etiquetas.pdf", "PDF (*.pdf)")
        if not caminho:
            return
        prontos = self._prontos_para_saida()
        if not prontos:
            mostrar_toast(self, "Nenhum item pronto neste lote.", tipo="info")
            return

        def _trabalho(st, itens=list(prontos), destino=caminho):
            return servico.gerar_etiquetas_lote(itens, destino, st)

        trab = Trabalhador(_trabalho)
        trab.status.connect(self._overlay.mostrar)

        def _pronto(resultado):
            self._overlay.esconder()
            saida, avisos = resultado
            extra = (f" · {len(avisos)} aviso(s) no pré-voo" if avisos else "")
            mostrar_toast(self, f"Etiquetas salvas em "
                                f"{Path(saida).name}{extra}.", tipo="sucesso")
            from app.qt.telas import compartilhar
            compartilhar.abrir_pasta(saida)

        trab.ok.connect(_pronto)
        trab.erro.connect(self._falhou)
        self._trabalhos.rodar(trab)

    def _exportar(self) -> None:
        from app.qt.telas.prevoo import confirmar_pre_voo

        if not confirmar_pre_voo(self, self._avisos_pre_voo(), "Exportar"):
            return
        caminho, _ = QFileDialog.getSaveFileName(
            self, "Exportar cartazes", "cartazes.pdf", "PDF (*.pdf)")
        if not caminho:
            return
        prontos = self._prontos_para_saida()
        if not prontos:
            mostrar_toast(self, "Nenhum cartaz pronto neste lote.", tipo="info")
            return
        fora = len(self._itens) - len(prontos)
        layout = self._layout
        marca = not servico.pode_exportar_limpo(self._projeto_id)
        impor = self.chk_2em1.isChecked()

        def _trabalho(st):
            paginas = self._compor_paginas(st, prontos, layout, marca, impor)
            st("Gravando o PDF…")
            from app.rendering.cmyk import pos_processar_export
            from app.rendering.export import exportar_pdf_multipagina
            # 2-em-1 sai em A4 paisagem; senão, no tamanho do layout
            dpi = layout.dpi
            saida = exportar_pdf_multipagina(paginas, caminho, dpi)
            # F7.5: CMYK opcional — desligado (padrão) não toca um byte
            return pos_processar_export(saida, st)

        trab = Trabalhador(_trabalho)
        trab.status.connect(self._overlay.mostrar)
        trab.ok.connect(lambda res, f=fora: self._exportado(res, f))
        trab.erro.connect(self._falhou)
        self._trabalhos.rodar(trab)

    # --- imprimir direto (R-112) ------------------------------------------------------

    def _imprimir(self) -> None:
        """Compõe fora do thread da UI e pinta na impressora NA thread da UI
        (o QPainter/QPrinter não é thread-safe — a pintura fica na GUI)."""
        from app.qt.telas.prevoo import confirmar_pre_voo

        if not confirmar_pre_voo(self, self._avisos_pre_voo(), "Imprimir"):
            return
        prontos = self._prontos_para_saida()
        if not prontos:
            mostrar_toast(self, "Nenhum cartaz pronto neste lote.", tipo="info")
            return
        layout = self._layout
        marca = not servico.pode_exportar_limpo(self._projeto_id)
        impor = self.chk_2em1.isChecked()

        def _trabalho(st):
            return self._compor_paginas(st, prontos, layout, marca, impor)

        trab = Trabalhador(_trabalho)
        trab.status.connect(self._overlay.mostrar)
        trab.ok.connect(lambda paginas: self._imprimir_paginas(paginas, impor))
        trab.erro.connect(self._falhou)
        self._trabalhos.rodar(trab)

    def _imprimir_paginas(self, paginas, impor: bool) -> None:
        self._overlay.esconder()
        if not paginas:
            return
        from PySide6.QtPrintSupport import (
            QPrintDialog,
            QPrinter,
            QPrintPreviewDialog,
        )

        from app.rendering.cartaz import layout_cartaz_a4_paisagem
        from app.rendering.impressao import configurar_impressora, imprimir_imagens
        # o 2-em-1 já vem em A4 paisagem; senão, o tamanho do layout escolhido
        layout_saida = layout_cartaz_a4_paisagem() if impor else self._layout
        printer = QPrinter(QPrinter.PrinterMode.HighResolution)
        configurar_impressora(printer, layout_saida)
        dlg = QPrintDialog(printer, self)
        dlg.setWindowTitle("Imprimir cartazes")
        if dlg.exec() != QPrintDialog.DialogCode.Accepted:
            return
        # Prévia NATIVA (polimento F11): o dono VÊ as folhas antes de gastar
        # papel — o botão imprimir da prévia manda para a fila; fechar cancela.
        previa = QPrintPreviewDialog(printer, self)
        previa.setWindowTitle("Prévia de impressão — o que sai na bandeja")

        def _pintar(pr):
            try:
                imprimir_imagens(paginas, layout_saida, pr)
            except Exception as e:                 # I2: falha visível, nunca calada
                mostrar_toast(self, f"Prévia falhou: {e}", tipo="erro")

        previa.paintRequested.connect(_pintar)
        if previa.exec() != QPrintPreviewDialog.DialogCode.Accepted:
            mostrar_toast(self, "Impressão cancelada na prévia.", tipo="info")
            return
        mostrar_toast(self, f"{len(paginas)} página(s) enviada(s) à impressora.")

    def closeEvent(self, ev) -> None:  # noqa: N802 (Qt)
        """Lei exit-0: nenhum worker (compor/imprimir) vivo ao fechar a tela."""
        try:
            self._trabalhos.encerrar(espera_ms=1000)
        except Exception:
            pass
        super().closeEvent(ev)

    def _exportado(self, resultado, fora: int) -> None:
        self._overlay.esconder()
        caminho, aviso_cmyk = resultado
        aviso = f" ({fora} ficaram fora — cartaz incompleto)" if fora else ""
        if aviso_cmyk:
            aviso += f" — {aviso_cmyk}"
        mostrar_toast(self, f"Cartazes exportados: {Path(caminho).name}{aviso}")
        from app.qt.design.som import tocar_exportou
        tocar_exportou()                 # FASE 1 (passo 74): opcional
        if self._projeto_id is not None:  # FASE 2 (passo 36): transição
            from app.core.projetos import marcar_status, registrar_export
            marcar_status(self._projeto_id, "exportado")
            registrar_export(self._projeto_id, caminho)   # passo 94

    def _falhou(self, msg: str) -> None:
        self._overlay.esconder()
        mostrar_toast(self, msg, tipo="erro")

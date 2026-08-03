"""
Conciliação com o semáforo — o coração da Mesa
==============================================
Cada linha importada aparece com o veredito 🟢🟡🔴:

- 🟢 existe no banco — nada a fazer;
- 🟡 provável — [Aceitar] confirma o palpite (e o banco APRENDE o alias);
- 🔴 novo — [Criar] roda o fluxo: enriquecer nome → curadoria de imagem →
  remover fundo → cadastrar (tudo em worker, com overlay; a UI não congela).

"Concluir" libera quando não sobra 🔴/🟡 pendente (ou o usuário ignora a linha).
"""

from __future__ import annotations

from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMenu,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app.qt.design import tokens as t
from app.qt.design.carregando import OverlayOcupado
from app.qt.design.toast import mostrar_toast, mostrar_toast_desfazer
from app.qt.telas import servico
from app.qt.telas.curadoria_dialog import CuradoriaDialog
from app.qt.workers import (
    FilaIA,
    GerenciadorTrabalhos,
    Trabalhador,
    TrabalhadorFila,
)

_COR = {"VERDE": t.SUCESSO, "AMARELO": t.ALERTA, "VERMELHO": t.PERIGO}
_ROTULO = {"VERDE": "No banco", "AMARELO": "Conferir", "VERMELHO": "Novo"}


class EscolherProdutoDialog(QDialog):
    """ADENDO 30/07 — o gesto "é ESTE aqui": busca no acervo para o dono
    vincular a linha da importação a um produto que JÁ existe (o app
    aprende o apelido e da próxima vez casa sozinho). Seleção única."""

    def __init__(self, texto_inicial: str = "", parent=None):
        super().__init__(parent)
        self.setWindowTitle("Vincular a um produto do acervo")
        self.resize(520, 460)
        self.produto_id: int | None = None
        self.produto_nome: str = ""

        lay = QVBoxLayout(self)
        info = QLabel("Busque o produto que este item da tabela É — o "
                      "vínculo vira apelido e a próxima importação casa "
                      "sozinha.")
        info.setWordWrap(True)
        info.setProperty("papel", "legenda")
        lay.addWidget(info)
        self.busca = QLineEdit(texto_inicial)
        self.busca.setPlaceholderText("Digite parte do nome…")
        self.busca.textChanged.connect(self._rebuscar)
        lay.addWidget(self.busca)
        self.lista = QListWidget()
        self.lista.setIconSize(QSize(40, 40))
        self.lista.itemDoubleClicked.connect(lambda _it: self._confirmar())
        lay.addWidget(self.lista, 1)
        botoes = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok
                                  | QDialogButtonBox.StandardButton.Cancel)
        botoes.button(QDialogButtonBox.StandardButton.Ok).setText("Vincular")
        botoes.button(
            QDialogButtonBox.StandardButton.Cancel).setText("Cancelar")
        botoes.accepted.connect(self._confirmar)
        botoes.rejected.connect(self.reject)
        lay.addWidget(botoes)
        self._rebuscar()
        self.busca.setFocus()

    def _rebuscar(self) -> None:
        self.lista.clear()
        try:
            achados = servico.buscar_produtos_para_vinculo(
                self.busca.text())
        except Exception:
            achados = []
        for a in achados:
            rot = a["nome"] + (f"   —   R$ {a['preco']}"
                               if a.get("preco") else "")
            it = QListWidgetItem(rot)
            it.setData(Qt.ItemDataRole.UserRole, a["produto_id"])
            it.setData(Qt.ItemDataRole.UserRole + 1, a["nome"])
            if a.get("imagem"):
                pix = QPixmap(a["imagem"])
                if not pix.isNull():
                    it.setIcon(QIcon(pix))
            self.lista.addItem(it)
        if self.lista.count():
            self.lista.setCurrentRow(0)

    def _confirmar(self) -> None:
        it = self.lista.currentItem()
        if it is None:
            return
        self.produto_id = it.data(Qt.ItemDataRole.UserRole)
        self.produto_nome = it.data(Qt.ItemDataRole.UserRole + 1) or ""
        self.accept()


class ConciliacaoDialog(QDialog):
    """Resolve os itens importados até tudo ficar verde (ou ser ignorado)."""

    def __init__(self, resultado: servico.ResultadoMesa, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Conciliação com o banco")
        self.itens = list(resultado.itens)
        self.validade = resultado.validade_oferta
        # R-052 (Fase 7): quando a importação veio de uma FOTO, a conciliação
        # abre em tela cheia com o print ORIGINAL ao lado — o dono confere linha
        # a linha olhando a fonte. É o MESMO serviço/tabela/lógica (paridade por
        # construção); só ganha o painel da foto. (O recorte-por-linha fica p/
        # depois: o OCR ainda não devolve a bbox de cada linha.)
        self.caminho_fonte = resultado.caminho_fonte
        self._trabalhos = GerenciadorTrabalhos()

        titulo = QLabel("Conciliação")
        titulo.setProperty("papel", "titulo")
        self._resumo = QLabel("")
        self._resumo.setProperty("papel", "legenda")

        self.tabela = QTableWidget(0, 5)
        self.tabela.setHorizontalHeaderLabels(
            ["Situação", "Importado", "Preço", "No banco", "Ação"])
        self.tabela.verticalHeader().setVisible(False)
        # ADENDO 30/07: a miniatura do palpite na coluna "No banco"
        self.tabela.setIconSize(QSize(28, 28))
        # OS F11.5 #13: nome e preço IMPORTADOS editáveis inline (duplo clique
        # ou F2) — o dono corrige o erro do OCR na hora, com a foto ao lado.
        # As demais colunas seguem travadas (flag por célula no _recarregar).
        self.tabela.setEditTriggers(
            QTableWidget.EditTrigger.DoubleClicked
            | QTableWidget.EditTrigger.EditKeyPressed)
        self._recarregando = False
        self.tabela.itemChanged.connect(self._celula_editada)
        # OS F11.5 #15: seleção de LINHA ligada — os atalhos de teclado
        # (N = próximo amarelo · A = aceitar · R = rejeitar) agem no focado
        self.tabela.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.tabela.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows)
        from PySide6.QtGui import QKeySequence, QShortcut
        for tecla, fn in (("N", self._ir_proximo_amarelo),
                          ("A", self._aceitar_focado),
                          ("R", self._rejeitar_focado)):
            QShortcut(QKeySequence(tecla), self, fn)
        self.tabela.setToolTip("Atalhos: N = próximo amarelo · A = aceitar · "
                               "R = rejeitar/ignorar")
        self.tabela.horizontalHeader().setStretchLastSection(False)
        # FASE 1 (passo 55): nenhuma coluna vira um fiapo (minimum de 90).
        # F13/D13 (C-10): as colunas de nome eram Stretch — o dono NÃO
        # CONSEGUIA arrastá-las. Viraram Interactive; a largura inicial sai
        # do conteúdo (1ª carga) ou da memória (ui.conciliacao.colunas).
        from PySide6.QtWidgets import QHeaderView
        cab = self.tabela.horizontalHeader()
        cab.setMinimumSectionSize(90)
        cab.setSectionResizeMode(1, QHeaderView.ResizeMode.Interactive)
        cab.setSectionResizeMode(3, QHeaderView.ResizeMode.Interactive)

        rodape = QHBoxLayout()
        self._validade_lbl = QLabel(
            f"Validade da oferta: {self.validade}" if self.validade else "")
        self._validade_lbl.setProperty("papel", "legenda")
        # RG-03: a dinâmica "editar primeiro, fotos depois" — desmarcado, o
        # Criar cadastra SEM foto na hora (as fotos vêm depois, em lote, na
        # Mesa); é o modo rápido para o PC do mercado
        from PySide6.QtWidgets import QCheckBox
        self.chk_fotos = QCheckBox("Buscar fotos automaticamente")
        self.chk_fotos.setChecked(True)
        self.chk_fotos.setToolTip(
            "Desmarque para criar tudo SEM foto rapidinho — depois use "
            "“Buscar fotos em lote” na Mesa para completar.")
        self.chk_fotos.toggled.connect(self._modo_fotos_mudou)
        self.btn_todos = QPushButton("Criar todos sem foto")
        self.btn_todos.setToolTip("Cadastra TODOS os vermelhos de uma vez, "
                                  "sem foto (fila em segundo plano)")
        self.btn_todos.setVisible(False)
        self.btn_todos.clicked.connect(self._criar_todos_sem_foto)
        # OS F11.5 #19 (R-053): seguir SÓ com os verdes num clique — os
        # pendentes ficam FORA (visível no aviso), com desfazer a um clique
        self.btn_verdes = QPushButton("Aceitar todos os verdes")
        self.btn_verdes.setToolTip(
            "Conclui com os itens que casaram com confiança; amarelos e "
            "vermelhos ficam FORA desta oferta (dá para desfazer)")
        self.btn_verdes.clicked.connect(self._aceitar_verdes)
        self.btn_desfazer_verdes = QPushButton("Desfazer")
        self.btn_desfazer_verdes.setToolTip(
            "Volta os itens deixados de fora pelo “Aceitar todos os verdes”")
        self.btn_desfazer_verdes.setVisible(False)
        self.btn_desfazer_verdes.clicked.connect(self._desfazer_verdes)
        cancelar = QPushButton("Cancelar")
        cancelar.clicked.connect(self.reject)
        self.concluir = QPushButton("Concluir")
        self.concluir.setProperty("tipo", "primario")
        self.concluir.clicked.connect(self.accept)
        # OS F11.5 #61/#63/#64: o painel discreto da fila de IA — "o que a IA
        # faz agora" + parar num clique (visível só com a fila viva)
        self._fila_status = QLabel("")
        self._fila_status.setProperty("papel", "legenda")
        self.btn_parar_ia = QPushButton("Parar IA")
        self.btn_parar_ia.setToolTip(
            "Cancela a fila de enriquecimento — os nomes ficam como vieram "
            "(dá para enriquecer um a um no Criar)")
        self.btn_parar_ia.setVisible(False)
        self.btn_parar_ia.clicked.connect(self._parar_fila_ia)
        rodape.addWidget(self._validade_lbl, 1)
        rodape.addWidget(self._fila_status)
        rodape.addWidget(self.btn_parar_ia)
        rodape.addWidget(self.chk_fotos)
        rodape.addWidget(self.btn_verdes)
        rodape.addWidget(self.btn_desfazer_verdes)
        rodape.addWidget(self.btn_todos)
        rodape.addWidget(cancelar)
        rodape.addWidget(self.concluir)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(t.ESP_4, t.ESP_4, t.ESP_4, t.ESP_4)
        lay.setSpacing(t.ESP_2)
        lay.addWidget(titulo)
        lay.addWidget(self._resumo)
        # R-052: a foto ao lado só quando a fonte é imagem existente; senão a
        # tabela ocupa tudo (paridade: a lógica é a MESMA, só muda o miolo).
        painel = self._painel_foto()
        if painel is not None:
            # F13/D13 (C-10): o splitter cru virou o padrão da casa com
            # memória (o mesmo do editor/almoxarifado/cofre/fábrica/mesa)
            from app.qt.design.componentes import splitter_com_memoria
            split = splitter_com_memoria("conciliacao", painel, self.tabela,
                                         indice_lateral=0)
            lay.addWidget(split, 1)
            self._chave_ui = "ui.conciliacao.foto"
            self._geometria_lembrada = self._restaurar_geometria((1200, 760))
            # o chamador só maximiza quando NÃO há geometria lembrada
            self._tela_cheia = not self._geometria_lembrada
        else:
            lay.addWidget(self.tabela, 1)
            self._chave_ui = "ui.conciliacao.tabela"
            self._geometria_lembrada = self._restaurar_geometria((860, 560))
            self._tela_cheia = False
        self.setMinimumSize(700, 460)
        lay.addLayout(rodape)

        self._overlay = OverlayOcupado(self)
        self._recarregar()
        from app.qt.design.polimento import ordenar_tab
        ordenar_tab(self)               # FASE 1 (passo 66): Tab visual

        # RG-02a: enriquecer os VERMELHOS em fila, já — quando o humano
        # clicar em "Criar", o nome estará pronto. Cache POR UID (I1: a
        # tabela reindexa no ignorar; índice não é identidade).
        self._propostas: dict[str, servico.PropostaCriacao] = {}
        self._candidatos: dict[str, list[str]] = {}
        self._pre_busca_em_voo = False
        self._fila_enriquecer = None
        self._fila_criar = None
        vermelhos = [(it.uid, it.descricao) for it in self.itens
                     if it.semaforo == "VERMELHO"]
        if vermelhos:
            estado: dict = {}          # o motor é sondado UMA vez, na thread

            def _enriquecer_um(descricao):
                if "motor" not in estado:
                    estado["motor"] = servico._motor_se_disponivel()
                return servico.enriquecer_descricao(descricao, estado["motor"])

            # OS F11.5 #61/#63/#64 (R-089/R-090): a fila de IA com prioridade
            # VIVA — a linha que o dono seleciona é enriquecida primeiro; o
            # painel discreto diz o que a IA faz agora, com "Parar" a um clique
            rotulos = {uid: f"enriquecendo “{desc[:38]}”"
                       for uid, desc in vermelhos}
            self._fila_enriquecer = FilaIA(vermelhos, _enriquecer_um, rotulos)
            self._fila_enriquecer.item_pronto.connect(self._proposta_pronta)
            self._fila_enriquecer.comecou_item.connect(self._fila_mudou)
            self._fila_enriquecer.fila_terminou.connect(
                lambda: self._fila_mudou("", ""))
            self.tabela.currentCellChanged.connect(self._focar_fila)
            self._trabalhos.rodar(self._fila_enriquecer)

    # --- painel da fila de IA (#61/#63/#64) ---------------------------------------

    def _focar_fila(self, linha: int, _c: int, _lv: int, _lc: int) -> None:
        """R-090: o item que o dono olha vai para a FRENTE da fila."""
        if self._fila_enriquecer is None:
            return
        if 0 <= linha < len(self.itens):
            self._fila_enriquecer.focar(self.itens[linha].uid)

    def _fila_mudou(self, _chave: str, rotulo: str) -> None:
        if not hasattr(self, "_fila_status"):
            return
        if not rotulo:
            self._fila_status.setText("")
            self.btn_parar_ia.setVisible(False)
            return
        n = len(self._fila_enriquecer.pendentes()) \
            if self._fila_enriquecer is not None else 0
        extra = f" · {n} na fila" if n else ""
        self._fila_status.setText(f"IA: {rotulo}{extra}")
        self.btn_parar_ia.setVisible(True)

    def _parar_fila_ia(self) -> None:
        if self._fila_enriquecer is not None:
            self._fila_enriquecer.cancelar()
        self._fila_status.setText("IA parada — os nomes saem sem enriquecer.")
        self.btn_parar_ia.setVisible(False)

    # --- foto original ao lado (R-052) ------------------------------------------

    def _painel_foto(self):
        """A foto ORIGINAL importada, rolável, para o dono conferir cada linha
        olhando a fonte. Devolve o widget ou None (fonte de texto/inexistente)."""
        caminho = self.caminho_fonte
        if not caminho:
            return None
        from pathlib import Path
        if not Path(caminho).is_file():
            return None                    # I2: sumiu — cai no modo tabela, sem quebrar
        from PySide6.QtGui import QPixmap
        pix = QPixmap(caminho)
        if pix.isNull():
            return None
        from PySide6.QtWidgets import QScrollArea
        alvo = QLabel()
        alvo.setPixmap(pix)
        alvo.setScaledContents(False)
        alvo.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)
        rolagem = QScrollArea()
        rolagem.setWidget(alvo)
        rolagem.setWidgetResizable(True)
        rolagem.setToolTip("A tabela/print que você importou — confira as "
                           "linhas olhando aqui do lado.")
        self._foto_lbl = alvo          # guardado p/ o teste inspecionar
        return rolagem

    # --- fila de enriquecimento (RG-02a) -------------------------------------------

    def _linha_do_uid(self, uid: str) -> int | None:
        for i, it in enumerate(self.itens):
            if it.uid == uid:
                return i
        return None                    # foi ignorado no meio — descarta

    def _proposta_pronta(self, uid: str, proposta) -> None:
        self._propostas[uid] = proposta
        linha = self._linha_do_uid(uid)
        if linha is not None and self.itens[linha].semaforo == "VERMELHO":
            celula = self.tabela.item(linha, 3)
            if celula is not None:     # o nome enriquecido já aparece na tabela
                celula.setText(f"→ {proposta.nome}")

    def _modo_fotos_mudou(self, ligado: bool) -> None:
        tem_vermelho = any(it.semaforo == "VERMELHO" for it in self.itens)
        self.btn_todos.setVisible(not ligado and tem_vermelho)

    # --- tabela -----------------------------------------------------------------

    def _chip(self, semaforo: str) -> QLabel:
        chip = QLabel(f'<span style="color:{_COR[semaforo]}">●</span> '
                      f'{_ROTULO[semaforo]}')
        chip.setAlignment(Qt.AlignmentFlag.AlignCenter)
        return chip

    def showEvent(self, ev) -> None:  # noqa: N802 (Qt)
        super().showEvent(ev)
        # L3: o diálogo NUNCA transborda a tela — a 1366×768 os botões
        # Concluir/Cancelar ficavam atrás da barra de tarefas
        from app.qt.design.polimento import clampar_a_tela
        clampar_a_tela(self)

    def _recarregar(self) -> None:
        self._recarregando = True
        try:
            self.tabela.setRowCount(len(self.itens))
            for i, item in enumerate(self.itens):
                self.tabela.setCellWidget(i, 0, self._chip(item.semaforo))
                # passo 55: nome longo elide na célula, mas o tooltip tem TUDO
                cel_imp = QTableWidgetItem(item.descricao)
                cel_imp.setToolTip(item.descricao + "\n(duplo clique edita)")
                self.tabela.setItem(i, 1, cel_imp)
                self.tabela.setItem(i, 2, QTableWidgetItem(item.preco or "—"))
                # QUINTUSDECIMUS/J21: a linha NOVA nunca perde a seta —
                # o recarregar trocava "→ nome a criar" pelo top-1 do
                # fuzzy SEM a seta (a cerveja do dono virava "Doce de
                # Leite" na vitrine). Vermelho mostra SEMPRE o que será
                # criado; candidato de vermelho só existe no Vincular…
                if item.produto_id:
                    banco = item.nome
                elif item.semaforo == "VERMELHO":
                    # o _recarregar roda no __init__ antes da fila nascer
                    prop = getattr(self, "_propostas", {}).get(item.uid)
                    alvo = (prop.nome if prop else item.nome) or ""
                    banco = f"→ {alvo}" if alvo else "—"
                else:
                    banco = item.candidato_nome or "—"
                cel_banco = QTableWidgetItem(banco)
                # ADENDO 30/07: a MINIATURA do palpite responde "é este
                # mesmo?" num relance; o tooltip lista os candidatos
                if item.imagem:
                    pix = QPixmap(item.imagem)
                    if not pix.isNull():
                        cel_banco.setIcon(QIcon(pix))
                dica = banco
                if item.candidatos:
                    dica += "\n\nOutros palpites do banco:"
                    for c in item.candidatos[:5]:
                        dica += (f"\n  • {c.get('nome', '?')} "
                                 f"({c.get('score', 0):.0f})")
                cel_banco.setToolTip(dica)
                # #13: só Importado e Preço editam; "No banco" é do banco
                cel_banco.setFlags(cel_banco.flags()
                                   & ~Qt.ItemFlag.ItemIsEditable)
                self.tabela.setItem(i, 3, cel_banco)
                self.tabela.setCellWidget(i, 4, self._acoes(i, item))
            # F13/D13 (C-10): o ajuste-ao-conteúdo só na 1ª carga — cada
            # recarga ZERAVA a largura que o dono tinha arrastado. Depois
            # da 1ª, a memória (ou o ajuste manual) manda.
            if not getattr(self, "_colunas_prontas", False):
                self.tabela.resizeColumnsToContents()
                larguras = self._ui_get("ui.conciliacao.colunas")
                try:
                    for i, w in enumerate(list(larguras)[:5]):
                        if int(w) > 0:
                            self.tabela.setColumnWidth(i, int(w))
                except Exception:
                    pass                  # memória ausente/torta → conteúdo
                self._colunas_prontas = True
        finally:
            self._recarregando = False
        self._atualizar_resumo()

    def _celula_editada(self, cel: QTableWidgetItem) -> None:
        """#13: a edição inline reflete no ItemMesa (por LINHA da view atual —
        a lista self.itens é a mesma que a tabela exibe).

        ADENDO 30/07: corrigir o texto do OCR RE-CONCILIA a linha na
        hora — muitos vermelhos viram verdes só com o nome certo (antes
        nada recalculava e o dono criava duplicata sem saber)."""
        if self._recarregando:
            return
        linha, col = cel.row(), cel.column()
        if not (0 <= linha < len(self.itens)):
            return
        item = self.itens[linha]
        texto = cel.text().strip()
        if col == 1 and texto and texto != item.descricao:
            item.descricao = texto
            if item.semaforo != "VERDE":
                trab = Trabalhador(lambda st, it=item:
                                   servico.reconciliar_item(it))
                trab.status.connect(self._overlay.mostrar)
                trab.ok.connect(lambda it, u=item.uid:
                                (self._overlay.esconder(),
                                 self._resolvido_uid(u, it)))
                trab.erro.connect(self._falhou)
                self._overlay.mostrar("Reconferindo no banco…")
                self._trabalhos.rodar(trab)
        elif col == 2:
            # QUINTUSDECIMUS/J18: o preço editado é AVALIADO na hora —
            # "de X por Y" separa (por = preço, de = riscado); número
            # limpa a pendência; ilegível avisa (nunca fica calado)
            item.preco = "" if texto in ("", "—") else texto
            dp = servico.preco_de_por(item.preco)
            if dp:
                item.preco_de, item.preco = dp
                item.preco_de_da_tabela = True
            entendido = (not item.preco
                         or servico.preco_decimal(item.preco) is not None)
            if entendido:
                if "preco_ilegivel" in (item.pendencias or []):
                    item.pendencias.remove("preco_ilegivel")
                    if item.semaforo == "AMARELO" and item.produto_id:
                        item.semaforo = "VERDE"
                        item.motivo = ""
                    self._recarregar()
            else:
                mostrar_toast(self, f"Preço “{item.preco}” não entendido "
                                    "— use 5,99 ou “de 8,49 por 6,90”.",
                              tipo="erro")

    def _acoes(self, linha: int, item: servico.ItemMesa) -> QWidget:
        caixa = QWidget()
        h = QHBoxLayout(caixa)
        h.setContentsMargins(2, 2, 2, 2)
        h.setSpacing(t.ESP_1)
        if item.semaforo == "AMARELO":
            aceitar = QPushButton("Aceitar")
            aceitar.setToolTip("Confirmar o palpite do banco (aprende o alias)")
            aceitar.clicked.connect(lambda _=False, li=linha: self._aceitar(li))
            # ADENDO 30/07: "não é esse, é AQUELE" — o menu traz os
            # outros candidatos que o motor calculava e jogava fora,
            # mais a busca no acervo (o vínculo forçado)
            outro = QPushButton("Outro…")
            outro.setToolTip("Vincular a OUTRO produto do banco "
                             "(candidatos ou busca no acervo)")
            outro.clicked.connect(
                lambda _=False, li=linha, b=outro: self._menu_vinculo(li, b))
            criar = QPushButton("É novo")
            criar.setToolTip("Não é esse — criar um produto novo")
            criar.clicked.connect(lambda _=False, li=linha: self._criar(li))
            # RG-47 (revisão da Onda 1): o amarelo TAMBÉM precisa de saída
            # limpa — linha-lixo do OCR sem "Ignorar" encurralava o humano
            # (Aceitar ensinaria um alias ERRADO para sempre)
            ignorar = QPushButton("Ignorar")
            ignorar.setToolTip("Linha errada/lixo do OCR — fora do tabloide, "
                               "sem ensinar nada ao banco")
            ignorar.clicked.connect(lambda _=False, li=linha: self._ignorar(li))
            h.addWidget(aceitar)
            h.addWidget(outro)
            h.addWidget(criar)
            # §13.6/L6: a linha que acendeu "multiplos" tem "Separar em
            # 2" em QUALQUER cor — a porta estava só no verde e o Arroz
            # amarelo (a linha que o dono citou 2×) ficava sem ela
            if "multiplos" in (item.pendencias or []):
                separar_am = QPushButton("Separar em 2")
                separar_am.setToolTip("Dois produtos num preço — criar "
                                      "os dois e compor")
                separar_am.clicked.connect(
                    lambda _=False, li=linha: self._separar_em_dois(li))
                h.addWidget(separar_am)
            h.addWidget(ignorar)
        elif item.semaforo == "VERMELHO":
            # ADENDO 30/07: a queixa 3 do dono — o vermelho OBRIGAVA a
            # duplicata; "Vincular…" aponta o produto que JÁ existe
            vincular = QPushButton("Vincular…")
            vincular.setToolTip("Este item JÁ EXISTE no acervo — escolher "
                                "qual é (o app aprende para a próxima)")
            vincular.clicked.connect(
                lambda _=False, li=linha, b=vincular:
                self._menu_vinculo(li, b))
            criar = QPushButton("Criar")
            criar.setProperty("tipo", "primario")
            criar.setToolTip("Enriquecer o nome, escolher a imagem e cadastrar")
            criar.clicked.connect(lambda _=False, li=linha: self._criar(li))
            ignorar = QPushButton("Ignorar")
            ignorar.setToolTip("Deixar este item fora do tabloide")
            ignorar.clicked.connect(lambda _=False, li=linha: self._ignorar(li))
            h.addWidget(vincular)
            h.addWidget(criar)
            h.addWidget(ignorar)
        else:
            # QUINTUSDECIMUS/J17: o VERDE era a única linha SEM PORTA
            # NENHUMA — e era a linha do Arroz que o dono citou duas
            # vezes. Verde quer dizer "eu resolvo se você não disser
            # nada", nunca "você não pode mais falar".
            trocar = QPushButton("Trocar…")
            trocar.setToolTip("Não é este produto — vincular a OUTRO do "
                              "acervo (candidatos ou busca)")
            trocar.clicked.connect(
                lambda _=False, li=linha, b=trocar:
                self._menu_vinculo(li, b))
            separar = QPushButton("Separar em 2")
            separar.setToolTip("Esta linha são DOIS produtos num preço — "
                               "criar os dois e compor (Camil e Rei)")
            separar.clicked.connect(
                lambda _=False, li=linha: self._separar_em_dois(li))
            h.addWidget(trocar)
            h.addWidget(separar)
        return caixa

    def _separar_em_dois(self, linha: int) -> None:
        """J17: a porta "são 2 produtos" para a linha JÁ CASADA — ignora
        o casamento e abre a curadoria com a pergunta ligada e a
        sugestão determinística nos campos (o humano decide os nomes)."""
        item = self.itens[linha]
        det = servico.dividir_em_dois(item.descricao)
        proposta = servico.PropostaCriacao(
            nome=item.nome or item.descricao,
            mais18=item.mais18, categoria=item.categoria,
            possivel_composto=True,
            sugestao_componentes=det,
            componentes=det,          # pré-preenche os 2 campos editáveis
            # o CLIQUE em "Separar em 2" já é a decisão do dono — o
            # check nasce marcado (desmarcar continua cancelando)
            componentes_da_ia=True)
        trab = Trabalhador(lambda st, n=proposta.nome, e=item.ean:
                           servico.buscar_candidatos_para(n, st, ean=e))
        trab.status.connect(self._overlay.mostrar)
        trab.ok.connect(lambda cs, li=linha, p=proposta:
                        self._curadoria(li, self._com_candidatos(p, cs)))
        trab.erro.connect(self._falhou)
        self._overlay.mostrar("Buscando imagem…")
        self._trabalhos.rodar(trab)

    # --- ADENDO 30/07: o vínculo forçado ("é ESTE aqui") --------------------

    def _menu_vinculo(self, linha: int, botao: QWidget) -> None:
        """Os candidatos que o motor conhece (com score) + a busca."""
        item = self.itens[linha]
        menu = QMenu(self)
        vistos: set[int] = set()
        for c in (item.candidatos or []):
            pid = c.get("produto_id")
            if pid is None or pid in vistos or pid == item.produto_id:
                continue
            vistos.add(pid)
            ac = menu.addAction(f"{c.get('nome', '?')}   ({c.get('score', 0):.0f})")
            ac.triggered.connect(
                lambda _=False, li=linha, p=pid: self._vincular(li, p))
        if vistos:
            menu.addSeparator()
        buscar = menu.addAction("Buscar no acervo…")
        buscar.triggered.connect(
            lambda _=False, li=linha: self._buscar_no_acervo(li))
        menu.exec(botao.mapToGlobal(botao.rect().bottomLeft()))

    def _buscar_no_acervo(self, linha: int) -> None:
        item = self.itens[linha]
        dlg = EscolherProdutoDialog(item.descricao.split("·")[0][:40],
                                    parent=self)
        if dlg.exec() and dlg.produto_id is not None:
            self._vincular(linha, dlg.produto_id)

    def _vincular(self, linha: int, produto_id: int) -> None:
        item = self.itens[linha]
        trab = Trabalhador(lambda st, it=item, p=produto_id:
                           servico.aceitar_correspondencia(it, produto_id=p))
        trab.status.connect(self._overlay.mostrar)
        # por UID (I1): a linha pode mudar de índice enquanto o worker roda
        trab.ok.connect(lambda it, u=item.uid:
                        (self._overlay.esconder(),
                         self._resolvido_uid(u, it)))
        trab.erro.connect(self._falhou)
        self._overlay.mostrar("Vinculando…")
        self._trabalhos.rodar(trab)

    def _atualizar_resumo(self) -> None:
        n = {"VERDE": 0, "AMARELO": 0, "VERMELHO": 0}
        for it in self.itens:
            n[it.semaforo] += 1
        # OS F11.5 #21 (R-053): o texto EXIGIDO pelo passo — verdes aceitos,
        # amarelos para revisar, vermelhos novos
        self._resumo.setText(
            f'<span style="color:{t.SUCESSO}">●</span> {n["VERDE"]} verdes '
            'aceitos   '
            f'<span style="color:{t.ALERTA}">●</span> {n["AMARELO"]} para '
            'revisar   '
            f'<span style="color:{t.PERIGO}">●</span> {n["VERMELHO"]} novos')
        pendentes = n["AMARELO"] + n["VERMELHO"]
        self.concluir.setEnabled(pendentes == 0)
        self.concluir.setToolTip(
            "" if self.concluir.isEnabled()
            else "Resolva (ou ignore) os itens amarelos e vermelhos")
        if hasattr(self, "btn_verdes"):
            self.btn_verdes.setVisible(n["VERDE"] > 0 and pendentes > 0)

    # --- R-053: aceitar todos os verdes (OS F11.5 #19/#22) -----------------------

    def _aceitar_verdes(self) -> None:
        """QUINTUSDECIMUS/J20: o clique que descartava 31 de 42 linhas
        em silêncio MORREU. "Aceitar os verdes" confirma os verdes e as
        demais linhas PERMANECEM na tabela para o dono resolver — quem
        lê o botão entende "resolve os fáceis e me deixa cuidar do
        resto", e agora é isso que ele faz. Nada é removido; remoção de
        linha é decisão explícita (Ignorar, linha a linha)."""
        verdes, amarelos, vermelhos = servico.separar_por_semaforo(self.itens)
        restam = len(amarelos) + len(vermelhos)
        if not verdes:
            return
        mostrar_toast(self, f"{len(verdes)} verde(s) já estão aceitos e "
                            f"entram na oferta. As {restam} linha(s) "
                            "restantes continuam aqui para você resolver "
                            "— nada foi descartado.")

    def _desfazer_verdes(self) -> None:
        """J20: sem descarte, nada a desfazer — mantido para compat de
        chamadores antigos; o botão não fica mais visível."""
        self.btn_desfazer_verdes.setVisible(False)

    # --- OS F11.5 #15: navegação por teclado ------------------------------------

    def _linha_amarela_seguinte(self, a_partir: int | None = None) -> int:
        inicio = (a_partir if a_partir is not None
                  else self.tabela.currentRow() + 1)
        for i in list(range(inicio, len(self.itens))) + \
                list(range(0, inicio)):
            if self.itens[i].semaforo == "AMARELO":
                return i
        return -1

    def _ir_proximo_amarelo(self) -> None:
        i = self._linha_amarela_seguinte()
        if i >= 0:
            self.tabela.setCurrentCell(i, 0)
            self.tabela.scrollToItem(self.tabela.item(i, 0))

    def _aceitar_focado(self) -> None:
        i = self.tabela.currentRow()
        if 0 <= i < len(self.itens) and self.itens[i].semaforo == "AMARELO":
            self._aceitar(i)

    def _rejeitar_focado(self) -> None:
        i = self.tabela.currentRow()
        if 0 <= i < len(self.itens) and self.itens[i].semaforo != "VERDE":
            self._ignorar(i)

    # --- ações ------------------------------------------------------------------

    def _aceitar(self, linha: int) -> None:
        item = self.itens[linha]
        trab = Trabalhador(lambda st, it=item: servico.aceitar_correspondencia(it))
        trab.status.connect(self._overlay.mostrar)
        trab.ok.connect(lambda it, li=linha: self._resolvido(li, it))
        trab.erro.connect(self._falhou)
        self._overlay.mostrar("Confirmando…")
        self._trabalhos.rodar(trab)

    def _ignorar(self, linha: int) -> None:
        # ADENDO 30/07: o atalho R tornava o acidente fácil e não havia
        # volta — agora o toast dá 6 s de "Desfazer" (a linha volta ao
        # MESMO lugar; nada foi ensinado ao banco em nenhum dos casos)
        item = self.itens[linha]
        del self.itens[linha]
        self._recarregar()

        def _voltar(li=linha, it=item):
            self.itens.insert(min(li, len(self.itens)), it)
            self._recarregar()

        mostrar_toast_desfazer(self, f"“{item.descricao[:40]}” ignorado.",
                               _voltar)

    def _criar(self, linha: int) -> None:
        item = self.itens[linha]
        proposta = self._propostas.get(item.uid)

        # RG-03: fotos desligadas = cadastrar SEM foto, na hora (modo rápido)
        if not self.chk_fotos.isChecked():
            if proposta is not None:
                self._cadastrar_ou_revisar(linha, proposta)
            else:                      # a fila ainda não chegou neste item
                trab = Trabalhador(lambda st, d=item.descricao:
                                   servico.enriquecer_descricao(
                                       d, servico._motor_se_disponivel()))
                trab.status.connect(self._overlay.mostrar)
                trab.ok.connect(lambda p, li=linha:
                                self._cadastrar_ou_revisar(li, p))
                trab.erro.connect(self._falhou)
                self._overlay.mostrar("Enriquecendo nome…")
                self._trabalhos.rodar(trab)
            return

        # RG-02a/b: nome pronto pela fila? candidatos pré-buscados?
        if proposta is not None:
            cands = self._candidatos.pop(item.uid, None)
            if cands is not None:      # tudo pronto: curadoria IMEDIATA
                proposta.candidatos = cands
                self._curadoria(linha, proposta)
                return
            trab = Trabalhador(lambda st, n=proposta.nome, e=item.ean:
                               servico.buscar_candidatos_para(n, st, ean=e))
            trab.status.connect(self._overlay.mostrar)
            trab.ok.connect(lambda cs, li=linha, p=proposta:
                            self._curadoria(li, self._com_candidatos(p, cs)))
            trab.erro.connect(self._falhou)
            self._overlay.mostrar("Buscando imagem…")
            self._trabalhos.rodar(trab)
            return

        trab = Trabalhador(lambda st, d=item.descricao, e=item.ean:
                           servico.preparar_criacao(d, st, ean=e))
        trab.status.connect(self._overlay.mostrar)
        trab.ok.connect(lambda prop, li=linha: self._curadoria(li, prop))
        trab.erro.connect(self._falhou)
        self._trabalhos.rodar(trab)

    def _cadastrar_ou_revisar(self, linha: int,
                              proposta: servico.PropostaCriacao) -> None:
        """F13/D6 (C-09): perda de palavra NUNCA passa em silêncio — no
        modo rápido, proposta com tokens_perdidos abre a curadoria (o
        único lugar que AVISA e deixa consertar o nome), mesmo sem
        fotos. Antes ela ia direto ao cadastro e o toast verde dizia
        'pronto' sobre um nome mutilado."""
        if proposta.tokens_perdidos:
            self._curadoria(linha, proposta)
            return
        self._cadastrar(linha, proposta, None)

    @staticmethod
    def _com_candidatos(proposta, candidatos):
        proposta.candidatos = candidatos
        return proposta

    def _pre_buscar_proximo(self, uid_atual: str) -> None:
        """RG-02b: enquanto o humano decide o item ATUAL, a busca do PRÓXIMO
        vermelho roda em segundo plano (uma por vez — o ddgs tem limite)."""
        if self._pre_busca_em_voo:
            return
        uids = [it.uid for it in self.itens if it.semaforo == "VERMELHO"]
        try:
            pos = uids.index(uid_atual)
        except ValueError:
            return
        for uid in uids[pos + 1:]:
            if uid in self._candidatos or uid not in self._propostas:
                continue               # sem nome enriquecido ainda: não busca
            nome = self._propostas[uid].nome
            ean_prox = next((it.ean for it in self.itens if it.uid == uid),
                            None)
            self._pre_busca_em_voo = True

            def _busca(_st, n=nome, e=ean_prox):
                return servico.buscar_candidatos_para(n, lambda _m: None,
                                                      ean=e)

            trab = Trabalhador(_busca)

            def _guardar(cands, u=uid):
                self._pre_busca_em_voo = False
                self._candidatos[u] = cands

            trab.ok.connect(_guardar)
            trab.erro.connect(lambda _m: setattr(
                self, "_pre_busca_em_voo", False))
            self._trabalhos.rodar(trab)
            return

    def _curadoria(self, linha: int, proposta: servico.PropostaCriacao) -> None:
        self._overlay.esconder()
        self._pre_buscar_proximo(self.itens[linha].uid)   # RG-02b
        # Rodada JM (B3): a pergunta "são 2 produtos?" + o +18 visível —
        # a sugestão vem da IA (pré-marcada) ou do sanitize (desmarcada)
        item_cur = self.itens[linha]
        # J13: os sabores DETECTADOS + o nome-base sugerido da família
        base_fam, sabores_det = servico.familia_da_linha(item_cur.descricao)
        # J23: posição na fila de vermelhos ("item n de N")
        verm = [it for it in self.itens if it.semaforo == "VERMELHO"]
        try:
            pos = (verm.index(item_cur) + 1, len(verm))
        except ValueError:
            pos = None
        dlg = CuradoriaDialog(
            proposta.nome, proposta.candidatos, self,
            tokens_perdidos=proposta.tokens_perdidos,
            possivel_composto=(proposta.possivel_composto
                               or len(proposta.componentes) >= 2),
            componentes=(proposta.componentes
                         or proposta.sugestao_componentes),
            componentes_da_ia=proposta.componentes_da_ia,
            mais18=proposta.mais18,
            sabores=sabores_det,
            nome_familia_sugerido=base_fam,
            contexto=item_cur.descricao,
            posicao=pos)
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return
        proposta.nome = dlg.nome_final()   # A2: a correção humana vale
        # B3/J13: o humano é a fonte final — a 3ª pergunta decide o
        # destino: 2 produtos, família de sabores, ou um produto só
        proposta.componentes = dlg.componentes_finais()
        proposta.mais18 = dlg.mais18_final()
        self._sabores_escolhidos = dlg.sabores_finais()
        # SEXTUSDECIMUS/M2+M5 + RODADA-125 Onda 2: linha MULTI → a tela
        # de UM ESPAÇO POR FOTO. Com MARCAS E SABORES juntos (o Biscoito
        # Bulnez e Adoralle × Cream Cracker/Leite/…), os espaços são o
        # CARTESIANO (decisão do dono: uma foto por item declarado); e
        # quem JÁ EXISTE no acervo aparece "✓ já no acervo" — nunca se
        # recria (a pergunta dele sobre duplicatas).
        # Cancelar cancela: o item segue vermelho, nada nasce pela metade.
        sab = self._sabores_escolhidos
        rotulos = (sab[1] if sab
                   else (proposta.componentes
                         if len(proposta.componentes) >= 2 else None))
        if sab and len(proposta.componentes) >= 2 and len(sab[1]) >= 2:
            rotulos = servico.rotulos_marcas_x_sabores(
                proposta.componentes, sab[1])
            self._sabores_escolhidos = (sab[0], rotulos)
        if rotulos and len(rotulos) >= 2:
            from app.qt.telas.fotos_por_sabor_dialog import (
                FotosPorSaborDialog,
            )
            base = sab[0] if sab else ""
            existentes = [servico.membro_do_acervo(
                f"{base} {r}".strip() if sab else r) for r in rotulos]
            fdlg = FotosPorSaborDialog(
                base, rotulos, self,
                titulo=(sab[0] if sab else proposta.nome),
                existentes=existentes)
            if fdlg.exec() != QDialog.DialogCode.Accepted:
                self._sabores_escolhidos = None
                return
            self._cadastrar(linha, proposta, fdlg.fotos())
            return
        tipo, valor = dlg.escolha
        if tipo == "nenhuma":
            self._cadastrar(linha, proposta, None)
            return
        if not servico.garantir_modelo_recorte(self):   # F13/E1 (CA-01)
            self._cadastrar(linha, proposta, None)      # cadastra SEM foto
            return
        # ESTÚDIO (03/08): o corte que come o produto AVISA (I2)
        avisos_rec: list[str] = []
        trab = Trabalhador(lambda st, v=valor: servico.tratar_imagem(
            v, st, aviso_cb=avisos_rec.append))
        trab.status.connect(self._overlay.mostrar)
        trab.ok.connect(lambda tratada, li=linha, p=proposta,
                        av=avisos_rec:
                        (self._cadastrar(li, p, tratada),
                         av and mostrar_toast(self, av[0], tipo="erro")))
        trab.erro.connect(self._falhou)
        self._trabalhos.rodar(trab)

    def _criar_todos_sem_foto(self) -> None:
        """RG-03: TODOS os vermelhos cadastrados de uma vez, sem foto —
        fila em segundo plano, resolvendo POR UID conforme fica pronto."""
        pares = [(it.uid, it) for it in self.itens
                 if it.semaforo == "VERMELHO"]
        if not pares:
            return
        self.btn_todos.setEnabled(False)
        estado: dict = {}
        self._para_revisar = []

        def _criar_um(item):
            if "motor" not in estado:
                estado["motor"] = servico._motor_se_disponivel()
            proposta = self._propostas.get(item.uid) or \
                servico.enriquecer_descricao(item.descricao, estado["motor"])
            # F13/D6 (C-09) + Rodada JM (B3): a política do lote virou
            # função nomeada — perda de palavra E "parece 2 produtos"
            # sem confirmação seguram o item para a curadoria (composto
            # NUNCA nasce por chute); nomeado no fim, I2
            if servico.deve_revisar_no_lote(proposta):
                self._para_revisar.append(item.descricao)
                return item
            if len(proposta.componentes) >= 2:      # RG-29: nasce composto
                return servico.criar_como_composto(
                    item, proposta.componentes, proposta.mais18, None,
                    categoria=proposta.categoria)
            return servico.finalizar_criacao(item, proposta.nome,
                                             proposta.mais18, None,
                                             categoria=proposta.categoria)

        def _fim_do_lote():
            self._overlay.esconder()
            self.btn_todos.setEnabled(True)
            rev = list(self._para_revisar)
            if rev:
                nomes = ", ".join(f"“{d[:28]}”" for d in rev[:3]) \
                    + ("…" if len(rev) > 3 else "")
                mostrar_toast(
                    self,
                    f"{len(rev)} item(ns) FICARAM para revisar (a IA "
                    f"descartou palavra do nome): {nomes} — clique em "
                    "Criar neles; os demais foram criados.")
            else:
                mostrar_toast(self, "Criação em lote concluída — as "
                                    "fotos vêm depois, na Mesa.")

        self._fila_criar = TrabalhadorFila(pares, _criar_um)
        self._fila_criar.item_pronto.connect(self._resolvido_uid)
        self._fila_criar.item_falhou.connect(
            lambda _u, msg: mostrar_toast(self, msg, tipo="erro"))
        self._fila_criar.fila_terminou.connect(_fim_do_lote)
        self._overlay.mostrar("Criando todos sem foto…")
        self._trabalhos.rodar(self._fila_criar)

    def _resolvido_uid(self, uid: str, item: servico.ItemMesa) -> None:
        linha = self._linha_do_uid(uid)
        if linha is not None:
            self.itens[linha] = item
            self._recarregar()

    def _cadastrar(self, linha: int, proposta: servico.PropostaCriacao,
                   tratada: str | list | None) -> None:
        # M2: ``tratada`` pode ser a LISTA paralela da tela de N espaços
        # (sabores/composto) — os dois criadores já falam o plural
        item = self.itens[linha]
        sabores = getattr(self, "_sabores_escolhidos", None)
        self._sabores_escolhidos = None

        def _executar(st, it=item, p=proposta, tr=tratada, sab=sabores):
            if sab:                       # J13: "são sabores" → FAMÍLIA
                nome_fam, lista = sab
                return servico.criar_familia_de_sabores(
                    it, nome_fam, lista, p.mais18, tr,
                    categoria=p.categoria)
            if len(p.componentes) >= 2:             # RG-29: nasce composto
                return servico.criar_como_composto(
                    it, p.componentes, p.mais18, tr, categoria=p.categoria)
            if isinstance(tr, (list, tuple)):       # produto só: a 1ª vale
                tr = next((c for c in tr if c), None)
            return servico.finalizar_criacao(it, p.nome, p.mais18, tr,
                                             categoria=p.categoria)

        trab = Trabalhador(_executar)
        trab.status.connect(self._overlay.mostrar)
        trab.ok.connect(lambda it, li=linha: self._resolvido(li, it))
        trab.erro.connect(self._falhou)
        self._overlay.mostrar("Cadastrando…")
        self._trabalhos.rodar(trab)

    def _resolvido(self, linha: int, item: servico.ItemMesa) -> None:
        self._overlay.esconder()
        self.itens[linha] = item
        self._recarregar()
        mostrar_toast(self, f"“{item.nome}” pronto.", tipo="sucesso")

    def _falhou(self, msg: str) -> None:
        self._overlay.esconder()
        mostrar_toast(self, msg, tipo="erro")

    # --- memória de UI (F13/D13, C-10) --------------------------------------

    @staticmethod
    def _ui_get(chave, padrao=None):
        """Leitura da Config com degradação muda ao padrão (o molde do
        splitter_com_memoria — memória de UI nunca derruba o diálogo)."""
        try:
            from app.core.database import Database
            from app.core.repositories import ConfigRepositorio
            db = Database().init()
            try:
                with db.Session() as s:
                    return ConfigRepositorio(s).get(chave, padrao)
            finally:
                db.engine.dispose()
        except Exception:
            return padrao

    @staticmethod
    def _ui_set(chave, valor) -> None:
        try:
            from app.core.database import Database
            from app.core.repositories import ConfigRepositorio
            db = Database().init()
            try:
                with db.Session() as s:
                    ConfigRepositorio(s).set(chave, valor)
                    s.commit()
            finally:
                db.engine.dispose()
        except Exception:
            pass

    def _restaurar_geometria(self, padrao: tuple[int, int]) -> bool:
        """Devolve True se restaurou da memória (validação dura, como o
        ui.shell: 2 ints, mínimos sãos; qualquer coisa torta → padrão)."""
        bruto = self._ui_get(self._chave_ui)
        try:
            w, h = int(bruto[0]), int(bruto[1])
            if w >= 700 and h >= 460:
                self.resize(w, h)
                return True
        except Exception:
            pass
        self.resize(*padrao)
        return False

    def done(self, resultado: int) -> None:  # noqa: N802 (Qt)
        # F13/D13: grava a memória de UI na saída ÚNICA (accept/reject/
        # Esc/X caem todos aqui) — tamanho da janela e largura de coluna
        if not self.isMaximized():
            self._ui_set(self._chave_ui, [self.width(), self.height()])
        self._ui_set("ui.conciliacao.colunas",
                     [self.tabela.columnWidth(i) for i in range(5)])
        # junta as pontas ANTES de morrer: fila viva com o dono destruído
        # derruba o processo (a lição da Etapa C do Bloco E)
        for fila in (self._fila_enriquecer, self._fila_criar):
            if fila is not None:
                fila.cancelar()
        self._trabalhos.encerrar()
        super().done(resultado)

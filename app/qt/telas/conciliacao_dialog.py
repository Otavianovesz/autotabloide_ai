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

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app.qt.design import tokens as t
from app.qt.design.carregando import OverlayOcupado
from app.qt.design.toast import mostrar_toast
from app.qt.telas import servico
from app.qt.telas.curadoria_dialog import CuradoriaDialog
from app.qt.workers import GerenciadorTrabalhos, Trabalhador, TrabalhadorFila

_COR = {"VERDE": t.SUCESSO, "AMARELO": t.ALERTA, "VERMELHO": t.PERIGO}
_ROTULO = {"VERDE": "No banco", "AMARELO": "Conferir", "VERMELHO": "Novo"}


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
        self.tabela.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.tabela.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        self.tabela.horizontalHeader().setStretchLastSection(False)
        # FASE 1 (passo 55): nenhuma coluna vira um fiapo; as colunas de
        # NOME dividem o espaço (elipse à direita é o padrão da view)
        from PySide6.QtWidgets import QHeaderView
        cab = self.tabela.horizontalHeader()
        cab.setMinimumSectionSize(90)
        cab.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        cab.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)

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
        cancelar = QPushButton("Cancelar")
        cancelar.clicked.connect(self.reject)
        self.concluir = QPushButton("Concluir")
        self.concluir.setProperty("tipo", "primario")
        self.concluir.clicked.connect(self.accept)
        rodape.addWidget(self._validade_lbl, 1)
        rodape.addWidget(self.chk_fotos)
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
            from PySide6.QtWidgets import QSplitter
            split = QSplitter(Qt.Orientation.Horizontal)
            split.addWidget(painel)
            split.addWidget(self.tabela)
            split.setStretchFactor(0, 3)
            split.setStretchFactor(1, 4)
            lay.addWidget(split, 1)
            self.resize(1200, 760)
            self._tela_cheia = True     # o chamador maximiza no exec()
        else:
            lay.addWidget(self.tabela, 1)
            self.resize(860, 560)
            self._tela_cheia = False
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

            self._fila_enriquecer = TrabalhadorFila(vermelhos, _enriquecer_um)
            self._fila_enriquecer.item_pronto.connect(self._proposta_pronta)
            self._trabalhos.rodar(self._fila_enriquecer)

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

    def _recarregar(self) -> None:
        self.tabela.setRowCount(len(self.itens))
        for i, item in enumerate(self.itens):
            self.tabela.setCellWidget(i, 0, self._chip(item.semaforo))
            # passo 55: nome longo elide na célula, mas o tooltip tem TUDO
            cel_imp = QTableWidgetItem(item.descricao)
            cel_imp.setToolTip(item.descricao)
            self.tabela.setItem(i, 1, cel_imp)
            self.tabela.setItem(i, 2, QTableWidgetItem(item.preco or "—"))
            banco = item.nome if item.produto_id else (item.candidato_nome or "—")
            cel_banco = QTableWidgetItem(banco)
            cel_banco.setToolTip(banco)
            self.tabela.setItem(i, 3, cel_banco)
            self.tabela.setCellWidget(i, 4, self._acoes(i, item))
        self.tabela.resizeColumnsToContents()
        self._atualizar_resumo()

    def _acoes(self, linha: int, item: servico.ItemMesa) -> QWidget:
        caixa = QWidget()
        h = QHBoxLayout(caixa)
        h.setContentsMargins(2, 2, 2, 2)
        h.setSpacing(t.ESP_1)
        if item.semaforo == "AMARELO":
            aceitar = QPushButton("Aceitar")
            aceitar.setToolTip("Confirmar o palpite do banco (aprende o alias)")
            aceitar.clicked.connect(lambda _=False, li=linha: self._aceitar(li))
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
            h.addWidget(criar)
            h.addWidget(ignorar)
        elif item.semaforo == "VERMELHO":
            criar = QPushButton("Criar")
            criar.setProperty("tipo", "primario")
            criar.setToolTip("Enriquecer o nome, escolher a imagem e cadastrar")
            criar.clicked.connect(lambda _=False, li=linha: self._criar(li))
            ignorar = QPushButton("Ignorar")
            ignorar.setToolTip("Deixar este item fora do tabloide")
            ignorar.clicked.connect(lambda _=False, li=linha: self._ignorar(li))
            h.addWidget(criar)
            h.addWidget(ignorar)
        else:
            h.addWidget(QLabel("—"))
        return caixa

    def _atualizar_resumo(self) -> None:
        n = {"VERDE": 0, "AMARELO": 0, "VERMELHO": 0}
        for it in self.itens:
            n[it.semaforo] += 1
        self._resumo.setText(
            f'<span style="color:{t.SUCESSO}">●</span> {n["VERDE"]} no banco   '
            f'<span style="color:{t.ALERTA}">●</span> {n["AMARELO"]} conferir   '
            f'<span style="color:{t.PERIGO}">●</span> {n["VERMELHO"]} novos')
        self.concluir.setEnabled(n["AMARELO"] + n["VERMELHO"] == 0)
        self.concluir.setToolTip(
            "" if self.concluir.isEnabled()
            else "Resolva (ou ignore) os itens amarelos e vermelhos")

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
        del self.itens[linha]
        self._recarregar()

    def _criar(self, linha: int) -> None:
        item = self.itens[linha]
        proposta = self._propostas.get(item.uid)

        # RG-03: fotos desligadas = cadastrar SEM foto, na hora (modo rápido)
        if not self.chk_fotos.isChecked():
            if proposta is not None:
                self._cadastrar(linha, proposta, None)
            else:                      # a fila ainda não chegou neste item
                trab = Trabalhador(lambda st, d=item.descricao:
                                   servico.enriquecer_descricao(
                                       d, servico._motor_se_disponivel()))
                trab.status.connect(self._overlay.mostrar)
                trab.ok.connect(lambda p, li=linha: self._cadastrar(li, p, None))
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
        dlg = CuradoriaDialog(proposta.nome, proposta.candidatos, self,
                              tokens_perdidos=proposta.tokens_perdidos)
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return
        proposta.nome = dlg.nome_final()   # A2: a correção humana vale
        tipo, valor = dlg.escolha
        if tipo == "nenhuma":
            self._cadastrar(linha, proposta, None)
            return
        trab = Trabalhador(lambda st, v=valor: servico.tratar_imagem(v, st))
        trab.status.connect(self._overlay.mostrar)
        trab.ok.connect(lambda tratada, li=linha, p=proposta:
                        self._cadastrar(li, p, tratada))
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

        def _criar_um(item):
            if "motor" not in estado:
                estado["motor"] = servico._motor_se_disponivel()
            proposta = self._propostas.get(item.uid) or \
                servico.enriquecer_descricao(item.descricao, estado["motor"])
            if len(proposta.componentes) >= 2:      # RG-29: nasce composto
                return servico.criar_como_composto(
                    item, proposta.componentes, proposta.mais18, None,
                    categoria=proposta.categoria)
            return servico.finalizar_criacao(item, proposta.nome,
                                             proposta.mais18, None,
                                             categoria=proposta.categoria)

        self._fila_criar = TrabalhadorFila(pares, _criar_um)
        self._fila_criar.item_pronto.connect(self._resolvido_uid)
        self._fila_criar.item_falhou.connect(
            lambda _u, msg: mostrar_toast(self, msg, tipo="erro"))
        self._fila_criar.fila_terminou.connect(
            lambda: (self._overlay.esconder(),
                     self.btn_todos.setEnabled(True),
                     mostrar_toast(self, "Criação em lote concluída — as "
                                         "fotos vêm depois, na Mesa.")))
        self._overlay.mostrar("Criando todos sem foto…")
        self._trabalhos.rodar(self._fila_criar)

    def _resolvido_uid(self, uid: str, item: servico.ItemMesa) -> None:
        linha = self._linha_do_uid(uid)
        if linha is not None:
            self.itens[linha] = item
            self._recarregar()

    def _cadastrar(self, linha: int, proposta: servico.PropostaCriacao,
                   tratada: str | None) -> None:
        item = self.itens[linha]

        def _executar(st, it=item, p=proposta, tr=tratada):
            if len(p.componentes) >= 2:             # RG-29: nasce composto
                return servico.criar_como_composto(
                    it, p.componentes, p.mais18, tr, categoria=p.categoria)
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

    def done(self, resultado: int) -> None:  # noqa: N802 (Qt)
        # junta as pontas ANTES de morrer: fila viva com o dono destruído
        # derruba o processo (a lição da Etapa C do Bloco E)
        for fila in (self._fila_enriquecer, self._fila_criar):
            if fila is not None:
                fila.cancelar()
        self._trabalhos.encerrar()
        super().done(resultado)

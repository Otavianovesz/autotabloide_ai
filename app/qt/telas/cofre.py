"""
Cofre — backups e portabilidade (F6.6, Etapa B do Bloco D)
==========================================================
Duas metades sobre os serviços headless:

- **Backups**: snapshots datados do banco (criar/inspecionar/restaurar/apagar).
  Inspecionar é o "modo seguro": olha dentro do snapshot sem tocar no vivo;
  restaurar sempre guarda o estado atual antes (dá para desfazer).
- **Levar & trazer**: exportar tudo num `.atpkg` e importar mesclando — o
  relatório de mesclagem mostra os conflitos e o humano decide POR ITEM
  (manter local / usar do pacote / manter ambos), com "aplicar a todos".
"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from app.core import cofre, portabilidade
from app.core.portabilidade import AnalisePacote, Decisao
from app.qt.design import tokens as t
from app.qt.design.carregando import OverlayOcupado
from app.qt.design.componentes import EstadoVazio, Painel
from app.qt.design.icones import icone
from app.qt.design.toast import mostrar_toast
from app.qt.workers import GerenciadorTrabalhos, Trabalhador

_ROTULOS = {"auto": "automático", "manual": "manual",
            "pre_restauracao": "antes de restaurar"}
_OPCOES_DECISAO = [("Manter o daqui", Decisao.MANTER_LOCAL),
                   ("Usar o do pacote", Decisao.USAR_PACOTE),
                   ("Manter os dois", Decisao.MANTER_AMBOS)]


class MesclagemDialog(QDialog):
    """Relatório de mesclagem: o humano decide cada conflito (I2)."""

    def __init__(self, analise: AnalisePacote, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Relatório de mesclagem")
        self.setMinimumSize(560, 420)
        self._combos: dict[str, QComboBox] = {}

        raiz = QVBoxLayout(self)
        raiz.setContentsMargins(t.ESP_4, t.ESP_4, t.ESP_4, t.ESP_4)
        raiz.setSpacing(t.ESP_2)
        titulo = QLabel("Relatório de mesclagem")
        titulo.setProperty("papel", "titulo")
        raiz.addWidget(titulo)

        resumo = []
        if analise.novos:
            resumo.append(f"{len(analise.novos)} produtos novos")
        if analise.identicos:
            resumo.append(f"{len(analise.identicos)} já idênticos aqui")
        if analise.projetos_novos:
            resumo.append(f"{len(analise.projetos_novos)} projetos novos")
        if analise.layouts_novos:
            resumo.append(f"{len(analise.layouts_novos)} layouts novos")
        if analise.fontes_novas:
            resumo.append(f"{len(analise.fontes_novas)} fontes novas")
        if analise.config_novas:
            resumo.append(f"{len(analise.config_novas)} configurações novas")
        rotulo = QLabel("O pacote traz: " + (", ".join(resumo) or "nada de novo")
                        + ".")
        rotulo.setWordWrap(True)
        raiz.addWidget(rotulo)

        for aviso in (analise.avisos + [f"config “{c}” difere — a local vence"
                                        for c in analise.config_diferentes]):
            lbl = QLabel(f"⚠ {aviso}")
            lbl.setWordWrap(True)
            lbl.setStyleSheet(f"color: {t.ALERTA};")
            raiz.addWidget(lbl)

        if analise.conflitos:
            cab = QLabel(f"<b>{len(analise.conflitos)} conflito(s)</b> — mesma "
                         "identidade, dados diferentes. Decida item a item:")
            cab.setWordWrap(True)
            raiz.addWidget(cab)

            todos = QHBoxLayout()
            todos.addWidget(QLabel("Aplicar a todos:"))
            self._combo_todos = QComboBox()
            for rot, _d in _OPCOES_DECISAO:
                self._combo_todos.addItem(rot)
            btn_todos = QPushButton("Aplicar")
            btn_todos.setToolTip("Repete a mesma decisão em todos os "
                                 "conflitos — depois ajuste os que quiser")
            btn_todos.clicked.connect(self._aplicar_a_todos)
            todos.addWidget(self._combo_todos)
            todos.addWidget(btn_todos)
            todos.addStretch(1)
            raiz.addLayout(todos)

            lista = QWidget()
            vl = QVBoxLayout(lista)
            vl.setContentsMargins(0, 0, 0, 0)
            vl.setSpacing(t.ESP_1)
            for c in analise.conflitos:
                linha = QHBoxLayout()
                detalhe = ", ".join(c.campos)
                lados = ""
                if c.tipo == "produto" and "preço" in c.campos:
                    lados = (f' — aqui {c.local.get("preço")}, '
                             f'no pacote {c.pacote.get("preço")}')
                lbl = QLabel(f"<b>{c.rotulo}</b><br>"
                             f'<span style="color:{t.TEXTO_3}">difere: '
                             f"{detalhe}{lados}</span>")
                lbl.setWordWrap(True)
                combo = QComboBox()
                for rot, _d in _OPCOES_DECISAO:
                    combo.addItem(rot)
                if c.tipo == "layout":       # layout não tem "manter os dois"… tem
                    combo.setToolTip("“Manter os dois” cria o layout com "
                                     "“(importado)” no nome")
                self._combos[c.id_decisao] = combo
                linha.addWidget(lbl, 1)
                linha.addWidget(combo)
                caixa = QWidget()
                caixa.setLayout(linha)
                vl.addWidget(caixa)
            rolagem = QScrollArea()
            rolagem.setWidgetResizable(True)
            rolagem.setWidget(lista)
            raiz.addWidget(rolagem, 1)
        else:
            ok = QLabel("Nenhum conflito — pode aplicar direto.")
            raiz.addWidget(ok)
            raiz.addStretch(1)

        botoes = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok
                                  | QDialogButtonBox.StandardButton.Cancel)
        botoes.button(QDialogButtonBox.StandardButton.Ok).setText(
            "Aplicar mesclagem")
        botoes.button(QDialogButtonBox.StandardButton.Cancel).setText("Cancelar")
        botoes.accepted.connect(self.accept)
        botoes.rejected.connect(self.reject)
        raiz.addWidget(botoes)

    def _aplicar_a_todos(self) -> None:
        i = self._combo_todos.currentIndex()
        for combo in self._combos.values():
            combo.setCurrentIndex(i)

    def decisoes(self) -> dict[str, Decisao]:
        return {chave: _OPCOES_DECISAO[combo.currentIndex()][1]
                for chave, combo in self._combos.items()}


class CofreTela(QWidget):
    """Tela do Cofre: backups à esquerda, pacote .atpkg à direita."""

    def __init__(self, raiz=None, parent=None):
        super().__init__(parent)
        self._raiz = raiz                  # None = System Root padrão
        self._trabalhos = GerenciadorTrabalhos()

        # --- backups ---------------------------------------------------------------
        self.lista = QListWidget()
        self.lista.setToolTip("Snapshots do banco — o mais novo primeiro")
        # FASE 1 (passo 73): estado vazio com AÇÃO
        btn_vazio_bk = QPushButton(" Criar backup agora")
        btn_vazio_bk.setIcon(icone("cofre", tamanho=16))
        btn_vazio_bk.clicked.connect(lambda: self._criar_backup())
        self._vazio = EstadoVazio(
            "cofre", "Nenhum backup ainda",
            "O app cria um automático a cada abertura;\n"
            "clique em “Criar backup agora” para um manual.",
            acao=btn_vazio_bk)

        btn_criar = QPushButton(" Criar backup agora")
        btn_criar.setIcon(icone("cofre", cor=t.ACENTO_TEXTO, tamanho=16))
        btn_criar.setProperty("tipo", "primario")
        btn_criar.clicked.connect(self._criar_backup)
        btn_inspecionar = QPushButton(" Inspecionar")
        btn_inspecionar.setIcon(icone("olho", tamanho=16))
        btn_inspecionar.setToolTip(
            "Modo seguro: olha dentro do snapshot sem tocar no banco vivo")
        btn_inspecionar.clicked.connect(self._inspecionar)
        btn_restaurar = QPushButton(" Restaurar…")
        btn_restaurar.setIcon(icone("desfazer", tamanho=16))
        btn_restaurar.setToolTip("O banco atual vira um snapshot antes — "
                                 "restaurar tem desfazer")
        btn_restaurar.clicked.connect(self._restaurar)
        btn_excluir = QPushButton(" Excluir")
        btn_excluir.setIcon(icone("lixeira", tamanho=16))
        btn_excluir.clicked.connect(self._excluir)

        acoes = QHBoxLayout()
        acoes.setSpacing(t.ESP_1)
        acoes.addWidget(btn_criar)
        acoes.addWidget(btn_inspecionar)
        acoes.addWidget(btn_restaurar)
        acoes.addWidget(btn_excluir)
        acoes.addStretch(1)

        caixa_bk = QWidget()
        vb = QVBoxLayout(caixa_bk)
        vb.setContentsMargins(0, 0, 0, 0)
        vb.setSpacing(t.ESP_2)
        vb.addLayout(acoes)
        vb.addWidget(self._vazio)
        vb.addWidget(self.lista, 1)

        # --- pacote .atpkg ----------------------------------------------------------
        btn_exportar = QPushButton(" Exportar pacote…")
        btn_exportar.setIcon(icone("impressora", cor=t.ACENTO_TEXTO, tamanho=16))
        btn_exportar.setProperty("tipo", "primario")
        btn_exportar.setToolTip("Banco + fotos + fontes + projetos num "
                                "arquivo .atpkg — leve para o outro PC")
        btn_exportar.clicked.connect(self._exportar_pacote)
        btn_importar = QPushButton(" Importar pacote…")
        btn_importar.setIcon(icone("abrir", tamanho=16))
        btn_importar.setToolTip("Mescla com o que já existe aqui — conflitos "
                                "aparecem num relatório para você decidir")
        btn_importar.clicked.connect(self._importar_pacote)
        explica = QLabel(
            "O pacote leva TUDO: banco, biblioteca de imagens, fontes e "
            "projetos congelados.\n\nNa importação, produto casa por "
            "identidade (nome + marca), nunca por número interno — as fotos "
            "são conferidas byte a byte depois do remap.")
        explica.setWordWrap(True)
        explica.setProperty("papel", "legenda")

        caixa_pk = QWidget()
        vp = QVBoxLayout(caixa_pk)
        vp.setContentsMargins(0, 0, 0, 0)
        vp.setSpacing(t.ESP_2)
        vp.addWidget(btn_exportar)
        vp.addWidget(btn_importar)
        vp.addWidget(explica)
        vp.addStretch(1)

        esquerda = QWidget()
        ve = QVBoxLayout(esquerda)
        ve.setContentsMargins(t.ESP_3, t.ESP_3, t.ESP_3, t.ESP_3)
        self._painel_backups = Painel("Backups do banco", "cofre", caixa_bk)
        ve.addWidget(self._painel_backups)

        direita = QWidget()
        vd = QVBoxLayout(direita)
        vd.setContentsMargins(t.ESP_3, t.ESP_3, t.ESP_3, t.ESP_3)
        vd.addWidget(Painel("Levar & trazer (casa ↔ mercado)", "abrir", caixa_pk))

        # FASE 2 (passo 84): a LIXEIRA de 30 dias — excluir sem medo
        self.lista_lixeira = QListWidget()
        self.lista_lixeira.setToolTip(
            "Tudo que você excluiu fica aqui por 30 dias — restaure ou "
            "apague de vez")
        self._vazio_lixeira = EstadoVazio(
            "lixeira", "Lixeira vazia",
            "O que você excluir (projeto, produto, layout)\n"
            "mora aqui por 30 dias antes de sumir de verdade.")
        btn_restaurar_lx = QPushButton(" Restaurar")
        btn_restaurar_lx.setIcon(icone("restaurar", tamanho=15))
        btn_restaurar_lx.clicked.connect(self._restaurar_da_lixeira)
        btn_excluir_lx = QPushButton(" Excluir agora")
        btn_excluir_lx.setIcon(icone("lixeira", tamanho=15))
        btn_excluir_lx.clicked.connect(self._excluir_agora_da_lixeira)
        linha_lx = QHBoxLayout()
        linha_lx.addStretch(1)
        linha_lx.addWidget(btn_restaurar_lx)
        linha_lx.addWidget(btn_excluir_lx)
        caixa_lx = QWidget()
        vlx = QVBoxLayout(caixa_lx)
        vlx.setContentsMargins(t.ESP_2, t.ESP_2, t.ESP_2, t.ESP_2)
        vlx.setSpacing(t.ESP_2)
        vlx.addWidget(self.lista_lixeira, 1)
        vlx.addWidget(self._vazio_lixeira, 1)
        vlx.addLayout(linha_lx)
        self._painel_lixeira = Painel("Lixeira (30 dias)", "lixeira",
                                      caixa_lx)
        vd.addWidget(self._painel_lixeira)

        # FASE 1 (passo 59): splitter com memória (era 380 fixo)
        from PySide6.QtWidgets import QVBoxLayout as _QV
        from app.qt.design.componentes import splitter_com_memoria
        sp = splitter_com_memoria("cofre", esquerda, direita,
                                  indice_lateral=1)
        corpo = _QV(self)
        corpo.setContentsMargins(0, 0, 0, 0)
        corpo.setSpacing(0)
        corpo.addWidget(sp, 1)

        self._overlay = OverlayOcupado(self)
        self.recarregar()

    # --- backups ------------------------------------------------------------------

    def showEvent(self, ev) -> None:  # noqa: N802 (Qt)
        super().showEvent(ev)
        self.recarregar()

    def recarregar(self) -> None:
        self.lista.clear()
        snaps = cofre.listar_snapshots(self._raiz)
        self._vazio.setVisible(not snaps)
        self.lista.setVisible(bool(snaps))
        # FASE 1 (passo 76): contador vivo no título do painel
        self._painel_backups.set_titulo(f"Backups do banco · {len(snaps)}")
        for s in snaps:
            li = QListWidgetItem(
                f'{s["quando"]}  ·  {_ROTULOS.get(s["rotulo"], s["rotulo"])}'
                f'  ·  {s["tamanho_kb"]} KB')
            li.setData(0x0100, s["caminho"])       # Qt.UserRole
            self.lista.addItem(li)
        self._recarregar_lixeira()

    _ICONE_LIXEIRA = {"projeto": "cofre", "produto": "caixa",
                      "layout": "camadas"}

    def _recarregar_lixeira(self) -> None:
        """FASE 2 (passo 84): tipo, nome, quando e dias restantes."""
        from app.core.lixeira import listar_lixeira
        self.lista_lixeira.clear()
        itens = listar_lixeira()
        self._vazio_lixeira.setVisible(not itens)
        self.lista_lixeira.setVisible(bool(itens))
        self._painel_lixeira.set_titulo(f"Lixeira (30 dias) · {len(itens)}")
        for d in itens:
            li = QListWidgetItem(
                icone(self._ICONE_LIXEIRA[d["tipo"]], tamanho=15),
                f'{d["nome"]}  ·  {d["tipo"]}  ·  excluído {d["quando"]}'
                f'  ·  some em {d["dias_restantes"]} dia(s)')
            li.setData(0x0100, (d["tipo"], d["id"], d["nome"]))
            self.lista_lixeira.addItem(li)

    def _item_lixeira(self):
        item = self.lista_lixeira.currentItem()
        if item is None:
            mostrar_toast(self, "Escolha um item da lixeira.", tipo="erro")
            return None
        return item.data(0x0100)

    def _restaurar_da_lixeira(self) -> None:
        alvo = self._item_lixeira()
        if alvo is None:
            return
        from app.core.lixeira import restaurar
        tipo, item_id, nome = alvo
        restaurar(tipo, item_id)
        mostrar_toast(self, f"“{nome}” restaurado — de volta às listas.")
        self._recarregar_lixeira()

    def _excluir_agora_da_lixeira(self) -> None:
        alvo = self._item_lixeira()
        if alvo is None:
            return
        tipo, item_id, nome = alvo
        from app.qt.design.componentes import confirmar_destrutivo
        if not confirmar_destrutivo(
                self, "Excluir agora",
                f"“{nome}” ({tipo}) será apagado DE VEZ, com os arquivos. "
                "Não tem volta.",
                "Excluir agora"):
            return
        from app.core.lixeira import excluir_agora
        excluir_agora(tipo, item_id)
        self._recarregar_lixeira()

    def _snapshot_selecionado(self) -> str | None:
        item = self.lista.currentItem()
        return item.data(0x0100) if item else None

    def _criar_backup(self) -> None:
        try:
            cofre.criar_snapshot(self._raiz, rotulo="manual")
        except FileNotFoundError:
            mostrar_toast(self, "Ainda não há banco para copiar.", tipo="erro")
            return
        self.recarregar()
        mostrar_toast(self, "Backup criado.")

    def _inspecionar(self) -> None:
        caminho = self._snapshot_selecionado()
        if not caminho:
            mostrar_toast(self, "Escolha um snapshot na lista.", tipo="erro")
            return
        info = cofre.inspecionar_snapshot(caminho)
        QMessageBox.information(
            self, "Dentro do snapshot (modo seguro)",
            f"{Path(caminho).name}\n\n"
            f"Produtos: {info['produtos']}\n"
            f"Apelidos aprendidos: {info['aliases']}\n"
            f"Categorias: {info['categorias']}\n"
            f"Layouts: {info['layouts']}\n"
            f"Projetos: {info['projetos']}\n\n"
            "Nada foi alterado — o banco vivo continua como está.")

    def _restaurar(self) -> None:
        caminho = self._snapshot_selecionado()
        if not caminho:
            mostrar_toast(self, "Escolha um snapshot na lista.", tipo="erro")
            return
        from app.qt.design.componentes import confirmar_destrutivo
        if not confirmar_destrutivo(              # passo 78: verbo no botão
                self, "Restaurar snapshot",
                "Voltar o banco para este snapshot?\n\n"
                "O banco ATUAL vira um snapshot antes (dá para desfazer). "
                "Feche e reabra as outras telas depois de restaurar.",
                "Restaurar snapshot"):
            return
        cofre.restaurar_snapshot(caminho, self._raiz)
        self.recarregar()
        mostrar_toast(self, "Banco restaurado — o estado anterior virou snapshot.")

    def _excluir(self) -> None:
        caminho = self._snapshot_selecionado()
        if not caminho:
            mostrar_toast(self, "Escolha um snapshot na lista.", tipo="erro")
            return
        from app.qt.design.componentes import confirmar_destrutivo
        if confirmar_destrutivo(                  # passo 78: verbo no botão
                self, "Excluir snapshot",
                f"{Path(caminho).name} será apagado. Não tem volta.",
                "Excluir snapshot"):
            cofre.excluir_snapshot(caminho)
            self.recarregar()

    # --- pacote -------------------------------------------------------------------

    def _exportar_pacote(self) -> None:
        caminho, _ = QFileDialog.getSaveFileName(
            self, "Exportar pacote", "autotabloide.atpkg",
            "Pacote AutoTabloide (*.atpkg)")
        if not caminho:
            return
        raiz = self._raiz

        def _trabalho(st):
            return portabilidade.exportar_pacote(caminho, raiz, progresso=st)

        trab = Trabalhador(_trabalho)
        trab.status.connect(self._overlay.mostrar)
        trab.ok.connect(lambda p: (self._overlay.esconder(), mostrar_toast(
            self, f"Pacote exportado: {Path(str(p)).name}")))
        trab.erro.connect(self._falhou)
        self._trabalhos.rodar(trab)

    def _importar_pacote(self) -> None:
        caminho, _ = QFileDialog.getOpenFileName(
            self, "Importar pacote", "", "Pacote AutoTabloide (*.atpkg)")
        if not caminho:
            return
        raiz = self._raiz

        def _analisar(st):
            return portabilidade.analisar_pacote(caminho, raiz, progresso=st)

        trab = Trabalhador(_analisar)
        trab.status.connect(self._overlay.mostrar)
        trab.ok.connect(self._analisado)
        trab.erro.connect(self._falhou)
        self._trabalhos.rodar(trab)

    def _analisado(self, analise: AnalisePacote) -> None:
        self._overlay.esconder()
        dlg = MesclagemDialog(analise, self)
        if dlg.exec() != QDialog.DialogCode.Accepted:
            analise.fechar()
            mostrar_toast(self, "Importação cancelada — nada foi alterado.")
            return
        decisoes = dlg.decisoes()
        raiz = self._raiz

        def _aplicar(st):
            try:
                return portabilidade.aplicar_importacao(
                    analise, decisoes, raiz, progresso=st)
            finally:
                analise.fechar()

        trab = Trabalhador(_aplicar)
        trab.status.connect(self._overlay.mostrar)
        trab.ok.connect(self._importado)
        trab.erro.connect(self._falhou)
        self._trabalhos.rodar(trab)

    def _importado(self, rel) -> None:
        self._overlay.esconder()
        detalhes = ""
        if rel.avisos:
            detalhes = "\n\n" + "\n".join(f"⚠ {a}" for a in rel.avisos[:8])
        QMessageBox.information(self, "Mesclagem concluída",
                                rel.resumo() + detalhes)
        self.recarregar()

    def _falhou(self, msg: str) -> None:
        self._overlay.esconder()
        mostrar_toast(self, msg, tipo="erro")

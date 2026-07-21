"""
MODO PAI — a visão à prova de erro (FASE 12, Bloco C — R-150)
=============================================================
O dono pensou no pai: uma tela SÓ com o essencial — ver o que está pronto,
conferir a prévia GRANDE, aprovar, imprimir OU enviar. Botões gigantes,
texto grande, 3 passos, nenhuma ação destrutiva alcançável (não apaga, não
edita preço, não reconfigura). Por baixo é tudo reuso: a aprovação em 2
etapas da F8, a impressão direta da F11 e o compartilhar da F8 — só a casca
é simples. Combina com o somente-leitura (R-131): o PC da loja pode nascer
aqui. Entrar/sair é claro e LEMBRADO (Config `app.modo_pai`).
"""

from __future__ import annotations

import tempfile
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.qt.design import tokens as t
from app.qt.design.componentes import EstadoVazio
from app.qt.design.toast import mostrar_toast
from app.qt.workers import GerenciadorTrabalhos, Trabalhador

_QSS_GIGANTE = ("QPushButton {{ font-size: 17px; font-weight: 600; "
                "padding: 14px 22px; border-radius: 10px; }}")


def modo_pai_lembrado() -> bool:
    try:
        from app.core.database import Database
        from app.core.repositories import ConfigRepositorio
        db = Database().init()
        try:
            with db.Session() as s:
                return bool(ConfigRepositorio(s).get("app.modo_pai", False))
        finally:
            db.engine.dispose()
    except Exception:
        return False


def lembrar_modo_pai(ligado: bool) -> None:
    try:
        from app.core.database import Database
        from app.core.repositories import ConfigRepositorio
        db = Database().init()
        try:
            with db.Session() as s:
                ConfigRepositorio(s).set("app.modo_pai", bool(ligado))
                s.commit()
        finally:
            db.engine.dispose()
    except Exception:
        pass


class ModoPaiTela(QWidget):
    """3 passos: escolher o pronto → conferir → aprovar/imprimir/enviar."""

    def __init__(self, ao_sair=None, parent=None):
        super().__init__(parent)
        self._ao_sair = ao_sair
        self._trabalhos = GerenciadorTrabalhos()
        self._paginas_cache: list | None = None

        titulo = QLabel("O que está pronto")
        titulo.setStyleSheet("font-size: 24px; font-weight: 700;")
        legenda = QLabel("Toque numa oferta, confira a foto e use os botões "
                         "grandes. Nada aqui apaga nem muda os preços.")
        legenda.setProperty("papel", "legenda")
        legenda.setStyleSheet("font-size: 15px;")
        legenda.setWordWrap(True)

        self.lista = QListWidget()
        self.lista.setStyleSheet("QListWidget { font-size: 16px; } "
                                 "QListWidget::item { padding: 12px; }")
        self.lista.setIconSize(QPixmap(120, 90).size())
        self.lista.currentRowChanged.connect(self._selecionou)

        self._previa = QLabel("Escolha uma oferta na lista.")
        self._previa.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._previa.setMinimumSize(380, 300)
        self._previa.setStyleSheet(
            f"background: {t.SUPERFICIE_2}; border-radius: 12px; "
            "font-size: 15px;")
        self._situacao = QLabel("")
        self._situacao.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._situacao.setStyleSheet("font-size: 16px; font-weight: 600;")

        # os 3 botões GIGANTES — e NENHUM destrutivo nesta tela (passo 40)
        self.btn_aprovar = QPushButton("✓  Aprovar esta oferta")
        self.btn_aprovar.setProperty("tipo", "primario")
        self.btn_aprovar.setToolTip("Confere o checklist e tira a marca "
                                    "RASCUNHO — aí pode publicar")
        self.btn_aprovar.clicked.connect(self._aprovar)
        self.btn_imprimir = QPushButton("🖨  Imprimir")
        self.btn_imprimir.setToolTip("Manda direto para a impressora")
        self.btn_imprimir.clicked.connect(self._imprimir)
        self.btn_enviar = QPushButton("📤  Enviar (copiar imagem)")
        self.btn_enviar.setToolTip("Copia a 1ª página — é só COLAR (Ctrl+V) "
                                   "na conversa do WhatsApp")
        self.btn_enviar.clicked.connect(self._enviar)
        for b in (self.btn_aprovar, self.btn_imprimir, self.btn_enviar):
            b.setStyleSheet(_QSS_GIGANTE.format())
            b.setMinimumHeight(56)
            b.setEnabled(False)

        self.btn_sair = QPushButton("Sair do modo simples")
        self.btn_sair.setToolTip("Volta para o aplicativo completo")
        self.btn_sair.clicked.connect(self._sair)

        self._vazio = EstadoVazio(
            "cofre", "Nenhuma oferta pronta ainda",
            "Quando alguém salvar uma oferta na Mesa, ela aparece aqui\n"
            "para você aprovar e imprimir.")

        coluna_esq = QVBoxLayout()
        coluna_esq.addWidget(titulo)
        coluna_esq.addWidget(legenda)
        coluna_esq.addWidget(self.lista, 1)
        coluna_esq.addWidget(self._vazio, 1)
        coluna_dir = QVBoxLayout()
        coluna_dir.addWidget(self._previa, 1)
        coluna_dir.addWidget(self._situacao)
        coluna_dir.addWidget(self.btn_aprovar)
        coluna_dir.addWidget(self.btn_imprimir)
        coluna_dir.addWidget(self.btn_enviar)

        corpo = QHBoxLayout()
        corpo.addLayout(coluna_esq, 2)
        corpo.addSpacing(t.ESP_4)
        corpo.addLayout(coluna_dir, 3)

        rodape = QHBoxLayout()
        rodape.addStretch(1)
        rodape.addWidget(self.btn_sair)

        raiz = QVBoxLayout(self)
        raiz.setContentsMargins(t.ESP_5, t.ESP_4, t.ESP_5, t.ESP_4)
        raiz.setSpacing(t.ESP_3)
        raiz.addLayout(corpo, 1)
        raiz.addLayout(rodape)

    # --- passo 1: a lista dos prontos ---------------------------------------

    def showEvent(self, ev) -> None:  # noqa: N802 (Qt)
        self.recarregar()
        super().showEvent(ev)

    def recarregar(self) -> None:
        from app.core import projetos
        self.lista.blockSignals(True)
        self.lista.clear()
        try:
            lista = projetos.listar_projetos()
        except Exception:
            lista = []
        for p in lista:
            rotulo = f"{p['nome']}"
            if p.get("evento"):
                rotulo = f"{p['evento']}  ·  {rotulo}"
            li = QListWidgetItem(rotulo)
            li.setData(Qt.ItemDataRole.UserRole, p)
            if p.get("miniatura"):
                from PySide6.QtGui import QIcon
                li.setIcon(QIcon(p["miniatura"]))
            self.lista.addItem(li)
        self.lista.blockSignals(False)
        tem = self.lista.count() > 0
        self.lista.setVisible(tem)
        self._vazio.setVisible(not tem)
        if tem:
            self.lista.setCurrentRow(0)

    def _projeto_atual(self) -> dict | None:
        item = self.lista.currentItem()
        return item.data(Qt.ItemDataRole.UserRole) if item else None

    # --- passo 2: conferir ---------------------------------------------------

    def _selecionou(self, _linha: int) -> None:
        p = self._projeto_atual()
        self._paginas_cache = None
        pronto = p is not None
        for b in (self.btn_aprovar, self.btn_imprimir, self.btn_enviar):
            b.setEnabled(pronto)
        if not pronto:
            self._previa.setText("Escolha uma oferta na lista.")
            self._situacao.setText("")
            return
        if p.get("miniatura") and Path(p["miniatura"]).exists():
            pm = QPixmap(p["miniatura"]).scaled(
                640, 480, Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation)
            self._previa.setPixmap(pm)
        else:
            self._previa.setText("Sem prévia — aprove e imprima mesmo assim.")
        self._atualizar_situacao()

    def _atualizar_situacao(self) -> None:
        p = self._projeto_atual()
        if p is None:
            return
        from app.core import projetos
        if projetos.esta_aprovado(p["id"]):
            self._situacao.setText("✅ Aprovada — pode imprimir e enviar")
            self._situacao.setStyleSheet(
                f"font-size: 16px; font-weight: 600; color: {t.SUCESSO};")
        else:
            self._situacao.setText("Ainda não aprovada — sai com a marca "
                                   "RASCUNHO")
            self._situacao.setStyleSheet(
                f"font-size: 16px; font-weight: 600; color: {t.ALERTA};")

    # --- passo 3: aprovar / imprimir / enviar --------------------------------

    def _aprovar(self) -> None:
        """Reusa a aprovação em 2 ETAPAS (F8): o checklist decide, nunca o
        clique cego — a falta aparece em linguagem simples."""
        p = self._projeto_atual()
        if p is None:
            return
        from app.core import projetos as _proj
        from app.qt.telas import servico
        aberto = _proj.abrir_projeto(p["id"])
        if aberto is None:
            mostrar_toast(self, "Esta oferta não abriu — peça ajuda para "
                                "recuperá-la no aplicativo completo.",
                          tipo="erro")
            return
        from app.qt.telas.servico import ItemMesa
        itens = [ItemMesa.from_dict(d) for d in aberto.itens]
        ok, faltas = servico.aprovar_projeto(p["id"], itens,
                                             aberto.validade_oferta)
        if ok:
            mostrar_toast(self, "Oferta aprovada! Pode imprimir e enviar.",
                          tipo="sucesso")
        else:
            mostrar_toast(self, "Falta arrumar antes de aprovar: "
                          + "; ".join(faltas), tipo="erro")
        self._atualizar_situacao()

    def _paginas(self):
        """Compõe as páginas do projeto (com RASCUNHO se não aprovado — a
        marca vale em TODA porta). Devolve (paginas, layout) ou None."""
        if self._paginas_cache is not None:
            return self._paginas_cache
        p = self._projeto_atual()
        if p is None:
            return None
        from app.core import projetos as _proj
        from app.qt.telas import servico
        from app.rendering.compositor import compor_pagina
        from app.rendering.marca_dagua import carimbar_rascunho
        aberto = _proj.abrir_projeto(p["id"])
        if aberto is None:
            return None
        from app.rendering.compositor import DadosProduto
        from app.qt.telas.servico import ItemMesa
        itens = [ItemMesa.from_dict(d) for d in aberto.itens]
        por_uid = {it.uid: it for it in itens}
        dados = {}
        for sid, uid in (aberto.mapa or {}).items():
            it = por_uid.get(uid)
            if it is None:
                continue
            dados[sid] = DadosProduto(
                it.nome, preco_por=servico.preco_decimal(it.preco),
                imagem_path=it.imagem)
        paginas = [compor_pagina(aberto.layout, pag, dados,
                                 fundo_path=aberto.layout.arquivo_fundo
                                 if i == 0 else None)
                   for i, pag in enumerate(aberto.layout.paginas)]
        if not _proj.esta_aprovado(p["id"]):     # a marca vale em TODA porta
            paginas = [carimbar_rascunho(im) for im in paginas]
        self._paginas_cache = (paginas, aberto.layout)
        return self._paginas_cache

    def _imprimir(self) -> None:
        """Reusa a impressão direta da F11 (R-112): tamanho físico em mm +
        orientação via QPageLayout, com prévia nativa."""
        resultado = self._paginas()
        if not resultado or not resultado[0]:
            mostrar_toast(self, "Nada para imprimir nesta oferta.",
                          tipo="erro")
            return
        paginas, layout = resultado
        from PySide6.QtPrintSupport import (
            QPrintDialog, QPrinter, QPrintPreviewDialog)

        from app.rendering.impressao import (
            configurar_impressora, imprimir_imagens)
        printer = QPrinter(QPrinter.PrinterMode.HighResolution)
        configurar_impressora(printer, layout)
        dlg = QPrintDialog(printer, self)
        dlg.setWindowTitle("Imprimir a oferta")
        if dlg.exec() != QPrintDialog.DialogCode.Accepted:
            return
        previa = QPrintPreviewDialog(printer, self)
        previa.setWindowTitle("Prévia — o que sai na bandeja")
        previa.paintRequested.connect(
            lambda pr: imprimir_imagens(paginas, layout, pr))
        previa.exec()

    def _enviar(self) -> None:
        """Copiar a 1ª página — colar na conversa é o gesto que o pai sabe."""
        resultado = self._paginas()
        if not resultado or not resultado[0]:
            mostrar_toast(self, "Nada para enviar nesta oferta.",
                          tipo="erro")
            return
        paginas, _lay = resultado
        destino = Path(tempfile.mkdtemp(prefix="modo_pai_")) / "oferta.png"
        paginas[0].save(destino)
        from app.qt.telas import compartilhar
        if compartilhar.copiar_imagem(destino):
            mostrar_toast(self, "Imagem copiada! Abra a conversa e COLE "
                                "(Ctrl+V).", tipo="sucesso")
        else:
            compartilhar.abrir_pasta(destino)
            mostrar_toast(self, "Abri a pasta com a imagem — arraste para "
                                "a conversa.")

    def _sair(self) -> None:
        lembrar_modo_pai(False)
        if callable(self._ao_sair):
            self._ao_sair()

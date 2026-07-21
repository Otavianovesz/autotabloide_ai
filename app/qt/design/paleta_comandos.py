"""
Command palette (Ctrl+K)
========================
Busca de ações estilo Linear/Figma: um campo no topo da janela filtra todas as
ações do editor; Enter (ou clique) executa; Esc fecha. Cada ação mostra o
ícone e o atalho.

Uso::

    acoes = [("salvar", "Salvar layout", "Ctrl+S", editor.salvar), ...]
    PaletaComandos(janela, acoes).abrir()
"""

from __future__ import annotations

import unicodedata
from typing import Callable

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QColor, QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QFrame,
    QGraphicsDropShadowEffect,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app.qt.design import tokens as t
from app.qt.design.icones import icone

Acao = tuple[str, str, str, Callable]   # (icone, rótulo, atalho, callback)

LARGURA = 520
MAX_VISIVEIS = 9


def _normalizar(s: str) -> str:
    """minúsculas sem acento — busca amigável ("preco" acha "Preço")."""
    return "".join(c for c in unicodedata.normalize("NFD", s.lower())
                   if unicodedata.category(c) != "Mn")


class PaletaComandos(QWidget):
    def __init__(self, janela: QWidget, acoes: list[Acao]):
        super().__init__(janela)
        self.setObjectName("paletaCmd")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self._acoes = acoes

        self.busca = QLineEdit()
        self.busca.setPlaceholderText("Digite um comando…  (Esc fecha)")
        self.busca.textChanged.connect(self._filtrar)
        self.lista = QListWidget()
        self.lista.setIconSize(QSize(16, 16))
        self.lista.itemActivated.connect(self._executar_item)
        self.lista.itemClicked.connect(self._executar_item)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, t.ESP_1)
        lay.setSpacing(0)
        lay.addWidget(self.busca)
        lay.addWidget(self.lista)

        sombra = QGraphicsDropShadowEffect(self)
        blur, dy, alpha = t.SOMBRA_3
        sombra.setBlurRadius(blur)
        sombra.setOffset(0, dy)
        cor = QColor(t.PAGINA_SOMBRA)
        cor.setAlpha(alpha)
        sombra.setColor(cor)
        self.setGraphicsEffect(sombra)

        QShortcut(QKeySequence("Esc"), self.busca,
                  activated=self.fechar).setContext(
            Qt.ShortcutContext.WidgetWithChildrenShortcut)
        self.busca.returnPressed.connect(self._executar_primeiro)
        self.hide()

    # --- abrir / fechar ---------------------------------------------------------

    def abrir(self) -> None:
        janela = self.parentWidget()
        self.setFixedWidth(LARGURA)
        self._filtrar("")
        self.busca.clear()
        self.move((janela.width() - LARGURA) // 2, int(janela.height() * 0.14))
        self.show()
        self.raise_()
        self.busca.setFocus()

    def fechar(self) -> None:
        self.hide()

    def keyPressEvent(self, event) -> None:
        if event.key() == Qt.Key.Key_Escape:
            self.fechar()
            return
        # setas navegam a lista mesmo com o foco na busca
        if event.key() in (Qt.Key.Key_Down, Qt.Key.Key_Up):
            self.lista.keyPressEvent(event)
            return
        super().keyPressEvent(event)

    # --- filtro / execução --------------------------------------------------------

    def _filtrar(self, texto: str) -> None:
        alvo = _normalizar(texto)
        self.lista.clear()
        for nome_ic, rotulo, atalho, cb in self._acoes:
            if alvo and alvo not in _normalizar(rotulo):
                continue
            item = QListWidgetItem(icone(nome_ic, tamanho=16), rotulo)
            item.setData(Qt.ItemDataRole.UserRole, cb)
            if atalho:
                item.setToolTip(atalho)
                item.setText(f"{rotulo}")
                # atalho à direita via texto secundário (list simples e legível)
                item.setData(Qt.ItemDataRole.UserRole + 1, atalho)
            self.lista.addItem(item)
        if self.lista.count():
            self.lista.setCurrentRow(0)
        altura_item = self.lista.sizeHintForRow(0) if self.lista.count() else 28
        visiveis = min(self.lista.count(), MAX_VISIVEIS)
        self.lista.setFixedHeight(max(visiveis, 1) * (altura_item + 2) + 8)
        self.adjustSize()

    def _executar_item(self, item: QListWidgetItem) -> None:
        cb = item.data(Qt.ItemDataRole.UserRole)
        self.fechar()
        if callable(cb):
            cb()

    def _executar_primeiro(self) -> None:
        item = self.lista.currentItem() or (
            self.lista.item(0) if self.lista.count() else None)
        if item is not None:
            self._executar_item(item)


def acoes_do_editor(editor) -> list[Acao]:
    """As ações padrão do editor (as mesmas da barra de ferramentas)."""
    from app.rendering.model import TipoRegiao

    c = editor.canvas
    acoes: list[Acao] = [
        ("desfazer", "Desfazer", "Ctrl+Z", c.desfazer),
        ("refazer", "Refazer", "Ctrl+Shift+Z", c.refazer),
        ("duplicar", "Copiar região selecionada", "Ctrl+C", c.copiar_selecao),
        ("duplicar", "Colar região", "Ctrl+V", c.colar),
        ("zoom_mais", "Aumentar zoom", "Ctrl+=", c.zoom_mais),
        ("zoom_menos", "Diminuir zoom", "Ctrl+-", c.zoom_menos),
        ("ajustar", "Ajustar à tela", "Ctrl+0", c.ajustar),
        ("grade", "Guia Z de leitura (liga/desliga)", "", c.alternar_guia_z),
        ("salvar", "Salvar layout no banco", "Ctrl+S", editor.salvar),
        ("abrir", "Abrir layout do banco", "Ctrl+O", editor.carregar_do_banco),
        ("duplicar", "Duplicar região selecionada", "Ctrl+D", editor._duplicar_selecao),
        ("lixeira", "Excluir região selecionada", "Del", editor._excluir_selecao),
    ]
    from app.qt.design.papel_texto_ui import criar_texto_legal_com_papel
    for nome_ic, tipo, rotulo in [
        ("imagem", TipoRegiao.IMAGEM, "Adicionar imagem"),
        ("texto", TipoRegiao.NOME, "Adicionar nome do produto"),
        ("preco", TipoRegiao.PRECO, "Adicionar preço"),
        ("unidade", TipoRegiao.UNIDADE, "Adicionar unidade"),
        ("selo", TipoRegiao.SELO, "Adicionar selo"),
        ("paragrafo", TipoRegiao.TEXTO_LEGAL, "Adicionar texto legal / aviso"),
    ]:
        if tipo == TipoRegiao.TEXTO_LEGAL:
            # RG-57: abre o diálogo NOMEADO de papel antes de criar
            acoes.append((nome_ic, rotulo, "",
                          lambda: criar_texto_legal_com_papel(c, editor.window())))
        else:
            acoes.append((nome_ic, rotulo, "",
                          lambda tp=tipo: c.adicionar_regiao(tp)))
    for nome_ic, modo, rotulo in [
        ("alinhar_esq", "esq", "Alinhar à esquerda"),
        ("alinhar_cent_h", "centro_h", "Centralizar na horizontal"),
        ("alinhar_dir", "dir", "Alinhar à direita"),
        ("alinhar_topo", "topo", "Alinhar ao topo"),
        ("alinhar_meio", "meio", "Centralizar na vertical"),
        ("alinhar_base", "base", "Alinhar à base"),
    ]:
        acoes.append((nome_ic, rotulo, "",
                      lambda m=modo: c.alinhar_selecionadas(m)))
    acoes.append(("dist_h", "Distribuir na horizontal", "",
                  lambda: c.distribuir_selecionadas("h")))
    acoes.append(("dist_v", "Distribuir na vertical", "",
                  lambda: c.distribuir_selecionadas("v")))

    def _distribuir_mm(eixo):
        from PySide6.QtWidgets import QInputDialog
        mm, ok = QInputDialog.getDouble(
            editor.window(), "Distribuir com espaçamento fixo",
            "Espaço entre as regiões (mm):", 5.0, 0.0, 500.0, 1)
        if ok:
            c.distribuir_espacado(eixo, mm)
    acoes.append(("dist_h", "Distribuir com espaçamento fixo (horizontal)", "",
                  lambda: _distribuir_mm("h")))
    acoes.append(("dist_v", "Distribuir com espaçamento fixo (vertical)", "",
                  lambda: _distribuir_mm("v")))
    return acoes


# =============================================================================
# FASE 2 (Bloco F): busca global — o dropdown do Início e o Ctrl+K usam
# a MESMA renderização de resultados (grupos projeto/produto/layout)
# =============================================================================

_ICONE_GRUPO = {"projetos": "cofre", "produtos": "caixa",
                "layouts": "camadas"}
_ROTULO_GRUPO = {"projetos": "PROJETOS", "produtos": "PRODUTOS",
                 "layouts": "LAYOUTS"}


def popular_resultados(lista, resultados: dict) -> int:
    """Preenche um QListWidget com os grupos; devolve o nº de resultados.
    Cada item guarda ("tipo", dado) no UserRole; cabeçalhos são
    desabilitados. Sem resultado → dica (passo 76)."""
    from PySide6.QtCore import Qt as _Qt
    from PySide6.QtWidgets import QListWidgetItem as _Item
    lista.clear()
    total = 0
    for grupo in ("projetos", "produtos", "layouts"):
        itens = resultados.get(grupo) or []
        if not itens:
            continue
        cab = _Item(_ROTULO_GRUPO[grupo])
        cab.setFlags(_Qt.ItemFlag.NoItemFlags)
        lista.addItem(cab)
        for d in itens:
            if grupo == "projetos":
                rotulo = f'{d["nome"]}  ·  {d["evento"] or "Avulso"}'
            elif grupo == "produtos":
                preco = f'  ·  R$ {d["preco"]}' if d["preco"] else ""
                rotulo = f'{d["nome"]}{preco}'
            else:
                rotulo = f'{d["nome"]}  ·  {d["tipo"].title()}'
            item = _Item(icone(_ICONE_GRUPO[grupo], tamanho=15), rotulo)
            item.setData(_Qt.ItemDataRole.UserRole, (grupo, d))
            lista.addItem(item)
            total += 1
    if total == 0:
        dica = _Item("Nada encontrado — tente parte do nome")
        dica.setFlags(_Qt.ItemFlag.NoItemFlags)
        lista.addItem(dica)
    return total


class PaletaBusca(QFrame):
    """FASE 2 (passo 74): Ctrl+K em QUALQUER tela — a mesma busca global
    do Início numa paleta flutuante (a casca da PaletaComandos)."""

    def __init__(self, janela, ao_escolher):
        super().__init__(janela)
        self.setObjectName("paletaComandos")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self._ao_escolher = ao_escolher

        from PySide6.QtCore import QTimer
        self.busca = QLineEdit()
        self.busca.setObjectName("paletaBusca")
        self.busca.setPlaceholderText(
            "Buscar projeto, produto ou layout…")
        self._debounce = QTimer(self)          # passo 75: 250 ms
        self._debounce.setSingleShot(True)
        self._debounce.setInterval(250)
        self._debounce.timeout.connect(self._buscar)
        self.busca.textChanged.connect(
            lambda _t: self._debounce.start())

        self.lista = QListWidget()
        self.lista.setUniformItemSizes(False)
        self.lista.itemClicked.connect(self._escolher_item)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, t.ESP_1)
        lay.setSpacing(0)
        lay.addWidget(self.busca)
        lay.addWidget(self.lista)

        sombra = QGraphicsDropShadowEffect(self)
        blur, dy, alpha = t.SOMBRA_3
        sombra.setBlurRadius(blur)
        sombra.setOffset(0, dy)
        cor = QColor(t.PAGINA_SOMBRA)
        cor.setAlpha(alpha)
        sombra.setColor(cor)
        self.setGraphicsEffect(sombra)
        self.busca.returnPressed.connect(self._escolher_primeiro)
        self.hide()

    def abrir(self) -> None:
        janela = self.parentWidget()
        self.setFixedWidth(LARGURA)
        self.busca.clear()
        self.lista.clear()
        self._ajustar_altura()
        self.move((janela.width() - LARGURA) // 2,
                  int(janela.height() * 0.14))
        self.show()
        self.raise_()
        self.busca.setFocus()

    def keyPressEvent(self, event) -> None:  # noqa: N802 (Qt)
        if event.key() == Qt.Key.Key_Escape:
            self.hide()
            return
        if event.key() in (Qt.Key.Key_Down, Qt.Key.Key_Up):
            self.lista.keyPressEvent(event)
            return
        super().keyPressEvent(event)

    def _buscar(self) -> None:
        texto = self.busca.text().strip()
        if len(texto) < 2:                     # passo 75: <2 não dispara
            self.lista.clear()
            self._ajustar_altura()
            return
        from app.qt.telas.busca import buscar_global
        popular_resultados(self.lista, buscar_global(texto))
        for i in range(self.lista.count()):    # 1º selecionável
            if self.lista.item(i).flags() & Qt.ItemFlag.ItemIsEnabled:
                self.lista.setCurrentRow(i)
                break
        self._ajustar_altura()

    def _ajustar_altura(self) -> None:
        altura_item = (self.lista.sizeHintForRow(0)
                       if self.lista.count() else 28)
        visiveis = min(self.lista.count(), MAX_VISIVEIS)
        self.lista.setFixedHeight(max(visiveis, 1) * (altura_item + 2) + 8)
        self.adjustSize()

    def _escolher_item(self, item) -> None:
        par = item.data(Qt.ItemDataRole.UserRole)
        if par is None:
            return
        self.hide()
        self._ao_escolher(*par)

    def _escolher_primeiro(self) -> None:
        item = self.lista.currentItem()
        if item is not None:
            self._escolher_item(item)

"""Modo planilha — a casca Qt (R-051, Fase 6 — Bloco B).

Grade editável dos itens da oferta (nome/preço/unidade/categoria) só com o
teclado. A decisão de cada edição está em `planilha.aplicar_edicao`; aqui é a
tabela, o destaque de problema, o undo de célula, o autocompletar de categoria
e o reflexo no canvas por uid.
"""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QComboBox, QDialog, QHeaderView, QStyledItemDelegate, QTableWidget,
    QTableWidgetItem, QVBoxLayout,
)

from app.qt.design import tokens as t
from app.qt.telas import planilha as L


class _DelegadoCategoria(QStyledItemDelegate):
    """Editor de categoria: combo editável com as categorias existentes
    (autocompletar) — não digita livre e cria duplicata (passo 21)."""

    def __init__(self, categorias, parent=None):
        super().__init__(parent)
        self._categorias = categorias

    def createEditor(self, parent, option, index):  # noqa: N802 (Qt)
        combo = QComboBox(parent)
        combo.setEditable(True)
        combo.addItems([""] + list(self._categorias))
        combo.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        return combo

    def setEditorData(self, editor, index):  # noqa: N802
        editor.setCurrentText(index.data() or "")

    def setModelData(self, editor, model, index):  # noqa: N802
        model.setData(index, editor.currentText().strip())


class DialogoPlanilha(QDialog):
    def __init__(self, mesa, parent=None):
        super().__init__(parent)
        self.mesa = mesa
        self.setWindowTitle("Modo planilha — editar tudo de uma vez")
        self.setMinimumSize(720, 480)
        self._carregando = True
        self._undo: list[tuple] = []   # (linha, coluna, texto_antigo)

        tab = QTableWidget(len(mesa._itens), len(L.COLUNAS))
        tab.setHorizontalHeaderLabels(L.COLUNAS)
        tab.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.ResizeMode.Stretch)   # Nome estica
        self.tab = tab
        categorias = self._categorias()
        tab.setItemDelegateForColumn(
            L.COLUNAS.index("Categoria"), _DelegadoCategoria(categorias, tab))

        for lin, item in enumerate(mesa._itens):
            for col, nome_col in enumerate(L.COLUNAS):
                cel = QTableWidgetItem(self._texto_celula(item, nome_col))
                if nome_col == "Foto" or nome_col not in L.EDITAVEIS:
                    cel.setFlags(cel.flags() & ~Qt.ItemFlag.ItemIsEditable)
                tab.setItem(lin, col, cel)
            self._marcar_problemas(lin, item)

        tab.itemChanged.connect(self._celula_mudou)
        raiz = QVBoxLayout(self)
        raiz.setContentsMargins(t.ESP_3, t.ESP_3, t.ESP_3, t.ESP_3)
        raiz.setSpacing(t.ESP_2)
        dica = None
        from PySide6.QtWidgets import QLabel
        dica = QLabel("Ctrl+V cola nome × preço do WhatsApp/Excel e ATUALIZA "
                      "os preços pelo nome; botão direito aplica categoria às "
                      "linhas selecionadas.")
        dica.setProperty("papel", "legenda")
        raiz.addWidget(dica)
        raiz.addWidget(tab)
        # Ctrl+Z: desfaz a última edição de célula (passo 24)
        sc = QShortcut(QKeySequence.StandardKey.Undo, self)
        sc.activated.connect(self._desfazer_celula)
        # Polimento F6 (dívida declarada): Ctrl+V cola tabela; menu de contexto
        # aplica categoria em massa às linhas selecionadas
        sc_v = QShortcut(QKeySequence.StandardKey.Paste, self)
        sc_v.activated.connect(self._colar_tabela)
        tab.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        tab.customContextMenuRequested.connect(self._menu_contexto)
        self._carregando = False

    # --- colar (polimento F6, passo 23) --------------------------------------

    def _colar_tabela(self) -> None:
        """Ctrl+V: cola uma tabela nome × preço (WhatsApp/Excel) e ATUALIZA o
        preço dos itens CASANDO PELO NOME — o uso real: a lista da semana com
        preços novos. Linha sem par fica visível no aviso (I2, nunca some
        calada); preço ambíguo não grava (reusa `aplicar_edicao`/P0.3)."""
        from PySide6.QtWidgets import QApplication

        from app.qt.design.toast import mostrar_toast
        from app.qt.telas.colagem import parse_colagem
        linhas = parse_colagem(QApplication.clipboard().text() or "")
        if not linhas:
            mostrar_toast(self, "Nada reconhecível na área de transferência.",
                          tipo="erro")
            return

        # a MESMA normalização da chave natural (minúsculo, SEM acento) — o
        # WhatsApp vem "CAFE 500G" e a estante tem "Café 500g"; sem tirar o
        # acento, nada casaria (auditoria de lógica do polimento)
        from app.core.portabilidade import _norm

        por_nome = {_norm(it.nome): (lin, it)
                    for lin, it in enumerate(self.mesa._itens)}
        atualizados, sem_par, rejeitados = 0, [], []
        for li in linhas:
            alvo = por_nome.get(_norm(li.nome))
            if alvo is None:
                sem_par.append(li.nome)
                continue
            lin, item = alvo
            texto_preco = li.multi_preco or li.preco
            if not texto_preco:
                continue
            gravou, _aviso = L.aplicar_edicao(item, "Preço", texto_preco)
            if not gravou:
                rejeitados.append(li.nome)
                continue
            atualizados += 1
            self._repor(lin, L.COLUNAS.index("Preço"),
                        self._texto_celula(item, "Preço"))
            self._marcar_problemas(lin, item)
        self.mesa.refletir_planilha()
        partes = [f"{atualizados} preço(s) atualizados"]
        if sem_par:
            partes.append(f"{len(sem_par)} sem par na estante "
                          f"({', '.join(sem_par[:3])}…)" if len(sem_par) > 3
                          else f"{len(sem_par)} sem par ({', '.join(sem_par)})")
        if rejeitados:
            partes.append(f"{len(rejeitados)} com preço não entendido")
        mostrar_toast(self, " · ".join(partes),
                      tipo="sucesso" if atualizados else "info")

    # --- edição em massa (polimento F6, passo 22) ----------------------------

    def _menu_contexto(self, pos) -> None:
        from PySide6.QtWidgets import QInputDialog, QMenu

        from app.qt.design.toast import mostrar_toast
        linhas = sorted({ix.row() for ix in self.tab.selectedIndexes()})
        if not linhas:
            return
        menu = QMenu(self)
        acao = menu.addAction(
            f"Aplicar categoria às {len(linhas)} linha(s) selecionada(s)…")
        if menu.exec(self.tab.viewport().mapToGlobal(pos)) != acao:
            return
        cats = self._categorias()
        cat, ok = QInputDialog.getItem(
            self, "Categoria em massa", "Categoria:", [""] + cats, 0, True)
        if not ok:
            return
        col_cat = L.COLUNAS.index("Categoria")
        for lin in linhas:
            if lin >= len(self.mesa._itens):
                continue
            item = self.mesa._itens[lin]
            L.aplicar_edicao(item, "Categoria", cat.strip())
            self._repor(lin, col_cat, self._texto_celula(item, "Categoria"))
            self._marcar_problemas(lin, item)
        self.mesa.refletir_planilha()
        mostrar_toast(self, f"Categoria “{cat.strip() or '—'}” aplicada a "
                            f"{len(linhas)} item(ns).")

    # --- dados ---------------------------------------------------------------

    def _categorias(self) -> list[str]:
        try:
            from app.core.database import Database
            from app.qt.telas import servico
            db = Database().init()
            try:
                with db.Session() as s:
                    return servico.categorias_ordenadas(s)
            finally:
                db.engine.dispose()
        except Exception:
            return []

    def _texto_celula(self, item, coluna: str) -> str:
        if coluna == "Foto":
            return "" if (item.imagem or item.imagens) else "sem foto"
        return L.valor_da_coluna(item, coluna)

    def _marcar_problemas(self, lin: int, item) -> None:
        for col, nome_col in enumerate(L.COLUNAS):
            cel = self.tab.item(lin, col)
            if cel is None:
                continue
            motivo = L.problema_na_celula(item, nome_col)
            if motivo:
                # polimento: o token de perigo REAL do tema (o fallback antigo
                # hardcodeava um rosa fixo que clareava no tema escuro)
                cel.setBackground(QColor(t.PERIGO_FUNDO))
                cel.setToolTip(motivo)
            else:
                cel.setBackground(QColor(0, 0, 0, 0))
                cel.setToolTip("")

    # --- edição --------------------------------------------------------------

    def _celula_mudou(self, cel: QTableWidgetItem) -> None:
        if self._carregando:
            return
        lin, col = cel.row(), cel.column()
        nome_col = L.COLUNAS[col]
        if nome_col not in L.EDITAVEIS or lin >= len(self.mesa._itens):
            return
        item = self.mesa._itens[lin]
        antigo = L.valor_da_coluna(item, nome_col)
        gravou, aviso = L.aplicar_edicao(item, nome_col, cel.text())
        if not gravou:
            # I2: preço não entendido — reverte a célula e avisa, nunca salva errado
            self._repor(lin, col, antigo)
            self._avisar(aviso, tipo="erro")
            return
        self._undo.append((lin, col, antigo))
        # mostra o valor efetivamente gravado (ex.: nome sanitizado)
        self._repor(lin, col, L.valor_da_coluna(item, nome_col))
        self._marcar_problemas(lin, item)
        self._avisar_override(item, nome_col)
        self.mesa.refletir_planilha()          # reflete no canvas por uid (I1)

    def _repor(self, lin: int, col: int, texto: str) -> None:
        self._carregando = True
        self.tab.item(lin, col).setText(texto)
        self._carregando = False

    def _desfazer_celula(self) -> None:
        if not self._undo:
            return
        lin, col, texto = self._undo.pop()
        item = self.mesa._itens[lin]
        L.aplicar_edicao(item, L.COLUNAS[col], texto)
        self._repor(lin, col, L.valor_da_coluna(item, L.COLUNAS[col]))
        self._marcar_problemas(lin, item)
        self.mesa.refletir_planilha()

    def _avisar_override(self, item, coluna: str) -> None:
        """Passo 28: se o item editado tem override NO campo em alguma célula,
        avisa que aquela célula fica 'presa' até o dono restaurar (I2)."""
        campo = {"Nome": "nome", "Preço": "preco"}.get(coluna)
        if campo is None:
            return
        presos = [sid for sid, uid in self.mesa._mapa.items()
                  if uid == item.uid and campo in (self.mesa._overrides.get(sid) or {})]
        if presos:
            self._avisar(
                f"“{item.nome}”: {len(presos)} célula(s) estão presas pelo "
                "override deste campo — restaure do item para ver a mudança.",
                tipo="info")

    def _avisar(self, texto: str | None, tipo: str = "info") -> None:
        if not texto:
            return
        try:
            from app.qt.design.toast import mostrar_toast
            mostrar_toast(self, texto, tipo=tipo)
        except Exception:
            pass

"""
Ateliê — o estúdio de layouts (F6.2)
====================================
A biblioteca que tira o app do hardcode: lista de layouts do banco (miniatura,
nome e tipo), **Novo layout** (importar arte → grade auto-detectada quando for
tabloide → editor do Bloco C para marcar/ajustar → salvar), editar/duplicar/
renomear/excluir, e **duplo-clique abre na Mesa ou na Fábrica** conforme o
tipo — Mesa e Fábrica passam a receber o layout escolhido.

Duas páginas: biblioteca ⇄ editor (com "← Biblioteca" para voltar).
"""

from __future__ import annotations

from decimal import Decimal
from pathlib import Path

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMenu,
    QMessageBox,
    QPushButton,
    QStackedLayout,
    QVBoxLayout,
    QWidget,
)

from app.core.database import Database
from app.qt.canvas import pil_para_qpixmap
from app.qt.design import tokens as t
from app.qt.design.componentes import EstadoVazio, Painel
from app.qt.design.icones import icone
from app.qt.design.toast import mostrar_toast
from app.rendering.compositor import DadosProduto, compor_pagina
from app.rendering.model import LayoutDef, layout_de_arte
from app.rendering.persistencia import (
    carregar_layout,
    duplicar_layout,
    excluir_layout,
    listar_layouts,
    renomear_layout,
    salvar_layout,
)

_MINIATURA = 150
_TIPOS = ["TABLOIDE", "CARTAZ", "ETIQUETA"]
_EXEMPLO = DadosProduto("Produto Exemplo", preco_por=Decimal("9.99"),
                        preco_de=Decimal("12.99"))


class AtelieTela(QWidget):
    """Biblioteca de layouts + editor embutido (Bloco C)."""

    def __init__(self, ao_abrir=None, parent=None):
        super().__init__(parent)
        self._db = None
        self.ao_abrir = ao_abrir       # callable(LayoutDef, tipo_midia, nome)

        # --- página 0: biblioteca ----------------------------------------------
        barra = QWidget()
        barra.setObjectName("barraFerramentas")
        hb = QHBoxLayout(barra)
        hb.setContentsMargins(t.ESP_3, t.ESP_1 + 2, t.ESP_3, t.ESP_1 + 2)
        hb.setSpacing(t.ESP_2)
        novo = QPushButton(" Novo layout")
        novo.setIcon(icone("imagem", cor=t.ACENTO_TEXTO, tamanho=16))
        novo.setProperty("tipo", "primario")
        novo.setToolTip("Importar a arte de fundo e marcar a grade de células")
        novo.clicked.connect(self._novo)
        dica = QLabel("Duplo-clique abre na Mesa (tabloide) ou na Fábrica (cartaz) "
                      "· botão direito para editar/duplicar/renomear/excluir")
        dica.setProperty("papel", "legenda")
        hb.addWidget(novo)
        hb.addStretch(1)
        hb.addWidget(dica)

        self.lista = QListWidget()
        self.lista.setViewMode(QListWidget.ViewMode.IconMode)
        # RG-10: grade FIXA — arrastar miniatura desorganizava a biblioteca
        self.lista.setMovement(QListWidget.Movement.Static)
        self.lista.setIconSize(QSize(_MINIATURA, _MINIATURA))
        self.lista.setResizeMode(QListWidget.ResizeMode.Adjust)
        self.lista.setSpacing(t.ESP_3)
        self.lista.setWordWrap(True)
        from app.qt.design.componentes import SombraHoverDelegate
        self.lista.setItemDelegate(SombraHoverDelegate(self.lista))  # passo 42
        self.lista.itemDoubleClicked.connect(self._abrir)
        self.lista.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.lista.customContextMenuRequested.connect(self._menu)

        # FASE 1 (passo 73): estado vazio com AÇÃO
        btn_vazio = QPushButton(" Novo layout")
        btn_vazio.setIcon(icone("camadas", tamanho=16))
        btn_vazio.clicked.connect(self._novo)
        self._vazio = EstadoVazio(
            "camadas", "Nenhum layout ainda",
            "Clique em “Novo layout” para importar a sua arte\n"
            "do Illustrator e marcar a grade.", acao=btn_vazio)

        corpo = QWidget()
        vc = QVBoxLayout(corpo)
        vc.setContentsMargins(0, 0, 0, 0)
        vc.addWidget(self._vazio)
        vc.addWidget(self.lista)

        biblioteca = QWidget()
        vb = QVBoxLayout(biblioteca)
        vb.setContentsMargins(0, 0, 0, 0)
        vb.setSpacing(0)
        vb.addWidget(barra)
        caixa = QWidget()
        vx = QVBoxLayout(caixa)
        vx.setContentsMargins(t.ESP_3, t.ESP_3, t.ESP_3, t.ESP_3)
        self._painel_layouts = Painel("Seus layouts", "camadas", corpo)
        vx.addWidget(self._painel_layouts)
        vb.addWidget(caixa, 1)

        # --- página 1: editor (carregado sob demanda) ----------------------------
        self._editor_caixa = QWidget()
        ve = QVBoxLayout(self._editor_caixa)
        ve.setContentsMargins(0, 0, 0, 0)
        ve.setSpacing(0)
        voltar_barra = QWidget()
        voltar_barra.setObjectName("barraFerramentas")
        hv = QHBoxLayout(voltar_barra)
        hv.setContentsMargins(t.ESP_3, t.ESP_1, t.ESP_3, t.ESP_1)
        voltar = QPushButton(" Biblioteca")
        voltar.setIcon(icone("seta_cima", tamanho=14))
        voltar.setProperty("tipo", "fantasma")
        voltar.setToolTip("Voltar para a biblioteca de layouts")
        voltar.clicked.connect(self._voltar)
        self._editando_lbl = QLabel("")
        self._editando_lbl.setProperty("papel", "legenda")
        hv.addWidget(voltar)
        hv.addSpacing(t.ESP_2)
        hv.addWidget(self._editando_lbl)
        hv.addStretch(1)
        ve.addWidget(voltar_barra)
        self._editor = None            # criado no primeiro uso (import pesado)

        self._paginas = QStackedLayout(self)
        self._paginas.addWidget(biblioteca)
        self._paginas.addWidget(self._editor_caixa)
        self.recarregar()

    # --- banco -------------------------------------------------------------------

    def _banco(self) -> Database:
        if self._db is None:
            self._db = Database().init()
        return self._db

    # --- biblioteca ----------------------------------------------------------------

    def recarregar(self) -> None:
        self.lista.clear()
        with self._banco().Session() as s:
            rows = listar_layouts(s)
            dados = [(r.id, r.nome, r.tipo_midia, r.arquivo_fundo,
                      carregar_layout(s, r.id)) for r in rows]
        self._vazio.setVisible(not dados)
        self.lista.setVisible(bool(dados))
        # FASE 1 (passo 76): contador vivo no título do painel
        self._painel_layouts.set_titulo(f"Seus layouts · {len(dados)}")
        for lid, nome, tipo, fundo, ldef in dados:
            item = QListWidgetItem(f"{nome}\n{tipo.title()}")
            item.setData(Qt.ItemDataRole.UserRole, (lid, nome, tipo))
            item.setIcon(self._miniatura(fundo, ldef))
            item.setToolTip(f"{nome} · {tipo.title()}")
            self.lista.addItem(item)

    def selecionar_layout(self, nome: str) -> None:
        """FASE 2 (passo 73): a busca global aterrissa NO layout certo."""
        for i in range(self.lista.count()):
            item = self.lista.item(i)
            dados = item.data(Qt.ItemDataRole.UserRole)
            if dados and dados[1].strip().lower() == nome.strip().lower():
                self.lista.setCurrentItem(item)
                self.lista.scrollToItem(item)
                return

    def _miniatura(self, fundo: str | None, ldef: LayoutDef | None):
        from PySide6.QtGui import QIcon

        from app.rendering.persistencia import resolver_arte
        fundo = resolver_arte(fundo)       # E-A3: o banco guarda relativo
        if fundo and Path(fundo).exists():
            pm = QPixmap(fundo)
        elif ldef is not None:
            try:   # compõe a página de exemplo (cartaz programático etc.)
                pm = pil_para_qpixmap(
                    compor_pagina(ldef, ldef.paginas[0], _EXEMPLO))
            except Exception:
                pm = QPixmap()
        else:
            pm = QPixmap()
        if pm.isNull():
            return icone("imagem", tamanho=48)
        return QIcon(pm.scaled(_MINIATURA, _MINIATURA,
                               Qt.AspectRatioMode.KeepAspectRatio,
                               Qt.TransformationMode.SmoothTransformation))

    # --- novo layout ------------------------------------------------------------------

    def _novo(self) -> None:
        arte, _ = QFileDialog.getOpenFileName(
            self, "Arte de fundo (Illustrator → PNG)", "",
            "Imagens (*.png *.jpg *.jpeg *.webp)")
        if not arte:
            return
        nome, ok = QInputDialog.getText(self, "Novo layout", "Nome do layout:")
        if not ok or not nome.strip():
            return
        tipo, ok = QInputDialog.getItem(
            self, "Tipo de mídia", "Este layout é de:", _TIPOS, 0, False)
        if not ok:
            return

        if tipo == "TABLOIDE":
            try:   # grade auto-detectada (as caixas de preço da arte)
                from app.rendering.grade import layout_grade_de_arte
                ldef, caixas = layout_grade_de_arte(arte)
                aviso = f"Grade detectada: {len(caixas)} células."
            except Exception:
                ldef, aviso = layout_de_arte(arte), "Sem grade detectada — marque no editor."
        else:
            ldef, aviso = layout_de_arte(arte), "Marque as regiões no editor."

        with self._banco().Session() as s:
            row = salvar_layout(s, nome.strip(), ldef, tipo_midia=tipo)
            s.commit()
            lid = row.id
        self.recarregar()
        mostrar_toast(self, f"“{nome.strip()}” criado. {aviso}")
        self._editar(lid, nome.strip())

    # --- ações da lista ------------------------------------------------------------------

    def _dados_item(self, item) -> tuple[int, str, str]:
        return item.data(Qt.ItemDataRole.UserRole)

    def _abrir(self, item) -> None:
        lid, nome, tipo = self._dados_item(item)
        with self._banco().Session() as s:
            ldef = carregar_layout(s, lid)
        if ldef is None or self.ao_abrir is None:
            return
        self.ao_abrir(ldef, tipo, nome)

    def _menu(self, pos) -> None:
        item = self.lista.itemAt(pos)
        if item is None:
            return
        lid, nome, tipo = self._dados_item(item)
        menu = QMenu(self)
        destino = "Mesa" if tipo == "TABLOIDE" else "Fábrica"
        a_abrir = menu.addAction(icone("grade", tamanho=16), f"Abrir na {destino}")
        a_editar = menu.addAction(icone("camadas", tamanho=16), "Editar layout")
        menu.addSeparator()
        a_dup = menu.addAction(icone("duplicar", tamanho=16), "Duplicar")
        a_ren = menu.addAction(icone("texto", tamanho=16), "Renomear")
        menu.addSeparator()
        a_del = menu.addAction(icone("lixeira", tamanho=16), "Excluir")
        escolha = menu.exec(self.lista.mapToGlobal(pos))
        if escolha == a_abrir:
            self._abrir(item)
        elif escolha == a_editar:
            self._editar(lid, nome)
        elif escolha == a_dup:
            with self._banco().Session() as s:
                duplicar_layout(s, lid, f"{nome} cópia")
                s.commit()
            self.recarregar()
        elif escolha == a_ren:
            novo, ok = QInputDialog.getText(self, "Renomear", "Novo nome:", text=nome)
            if ok and novo.strip():
                with self._banco().Session() as s:
                    renomear_layout(s, lid, novo.strip())
                    s.commit()
                self.recarregar()
        elif escolha == a_del:
            from app.qt.design.componentes import confirmar_destrutivo
            if confirmar_destrutivo(              # passo 78: verbo no botão
                    self, "Excluir layout",
                    f"“{nome}” será apagado. Não tem volta.",
                    "Excluir layout"):
                # FASE 2 (passo 82): soft-delete — lixeira do Cofre
                from app.core.lixeira import excluir_suave
                excluir_suave("layout", lid)
                self.recarregar()

    # --- editor embutido ------------------------------------------------------------------

    def _garantir_editor(self):
        if self._editor is None:
            from app.qt.editor import Editor
            self._editor = Editor()
            self._editor_caixa.layout().addWidget(self._editor, 1)
            if callable(getattr(self, "ao_criar_editor", None)):
                self.ao_criar_editor(self._editor)   # RG-05: zoom/salvo no shell
        return self._editor

    def _editar(self, layout_id: int, nome: str) -> None:
        with self._banco().Session() as s:
            ldef = carregar_layout(s, layout_id)
        if ldef is None:
            return
        editor = self._garantir_editor()
        editor.carregar(ldef, _EXEMPLO, fundo_path=ldef.arquivo_fundo)
        editor.nome_layout_atual = nome    # A4: Ctrl+S pré-preenche este nome
        self._editando_lbl.setText(f"Editando: {nome} — salve pela barra (Ctrl+S)")
        self._paginas.setCurrentIndex(1)
        editor.area.canvas.ajustar()

    def _voltar(self) -> None:
        self._paginas.setCurrentIndex(0)
        self.recarregar()      # miniaturas refletem o que foi salvo

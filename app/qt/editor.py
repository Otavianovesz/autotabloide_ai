"""
Editor visual (F5.1–F5.4 + sistema de design)
=============================================
Junta tudo: barra de ferramentas com ícones (design), canvas WYSIWYG com alças
e snapping, painéis de camadas e propriedades em cartões com cabeçalho.
O visual vem do tema global (``aplicar_tema``); aqui só há montagem.
"""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QInputDialog,
    QVBoxLayout,
    QWidget,
)

from app.core.database import Database
from app.qt.design import tokens as t
from app.qt.design.barra_editor import BarraEditor
from app.qt.design.componentes import Painel
from app.qt.painel_camadas import PainelCamadas
from app.qt.painel_propriedades import PainelPropriedades
from app.rendering.compositor import DadosProduto
from app.rendering.model import LayoutDef
from app.rendering.persistencia import carregar_layout, listar_layouts, salvar_layout
from app.qt.canvas import EditorCanvas

# RG-54: painel de 300 + a barra de rolagem vertical (~16px) que aparece a
# 720p — senão a borda direita dos campos ficava cortada
LARGURA_LATERAL = 320


class Editor(QWidget):
    sujo_mudou = Signal(bool)   # False = tudo salvo; True = há edição pendente

    def __init__(self, parent=None):
        super().__init__(parent)
        self._db = None
        self._dados = None
        self._sujo = False
        self.nome_layout_atual = ""   # A4: pré-preenche o "Salvar layout"

        self.area = EditorCanvas()
        self.camadas = PainelCamadas(self.area.canvas)
        self.propriedades = PainelPropriedades(self.area.canvas)
        self.painel = self.camadas  # alias de compatibilidade
        self.barra = BarraEditor(self)

        # RG-54 (passo 44-48): Propriedades num QScrollArea — a 720p ela
        # ROLA por dentro em vez de esticar a janela (o painel forçava
        # ~887 px de altura e cortava o rodapé). Camadas com mínimo sensato
        # (~4 linhas) mas expansível.
        from PySide6.QtWidgets import QScrollArea
        self.camadas.lista.setMinimumHeight(96)   # ~4 linhas, cresce no splitter
        rolagem_prop = QScrollArea()
        rolagem_prop.setWidget(self.propriedades)
        rolagem_prop.setWidgetResizable(True)
        rolagem_prop.setFrameShape(QScrollArea.Shape.NoFrame)
        rolagem_prop.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._rolagem_prop = rolagem_prop

        coluna = QVBoxLayout()
        coluna.setContentsMargins(t.ESP_3, t.ESP_3, t.ESP_3, t.ESP_3)
        coluna.setSpacing(t.ESP_3)
        coluna.addWidget(Painel("Camadas", "camadas", self.camadas), 2)
        coluna.addWidget(Painel("Propriedades", "propriedades", rolagem_prop), 3)
        self._lateral = QWidget()
        self._lateral.setObjectName("lateral")
        self._lateral.setLayout(coluna)

        # FASE 1 (passo 59): splitter com memória em vez de largura fixa —
        # o dono estica Camadas/Propriedades como quiser (cura do D4)
        from app.qt.design.componentes import splitter_com_memoria
        self._corpo = splitter_com_memoria(
            "editor", self.area, self._lateral,
            indice_lateral=1, minimo_lateral=LARGURA_LATERAL)
        corpo = self._corpo

        raiz = QVBoxLayout(self)
        raiz.setContentsMargins(0, 0, 0, 0)
        raiz.setSpacing(0)
        raiz.addWidget(self.barra)
        raiz.addWidget(corpo, 1)

        # qualquer edição suja o documento (o shell mostra "não salvo")
        self.area.canvas.editou.connect(lambda _reg: self._marcar_sujo(True))

        # atalhos de edição sobre a seleção + command palette — R-018:
        # todos nascem do catálogo central (remapeáveis na aba Atalhos).
        # CRÍTICO: ficam AQUI, no __init__, para existirem já no boot (o
        # bloco tinha escorregado para dentro de `alternar_lateral`, que não
        # roda com a lateral visível — achado do arquiteto na reauditoria F4).
        from PySide6.QtCore import Qt as _Qt
        from PySide6.QtGui import QKeySequence, QShortcut
        from app.qt.design.atalhos import criar_atalho
        for id_atalho, acao in [("editor.duplicar", self._duplicar_selecao),
                                ("editor.excluir", self._excluir_selecao),
                                ("editor.paleta", self.abrir_paleta),
                                ("editor.copiar", self.canvas.copiar_selecao),
                                ("editor.colar", self.canvas.colar)]:
            criar_atalho(id_atalho, self, acao)
        # Backspace segue espelho FIXO do excluir (RG-06) — remapear o
        # "Excluir região" não desliga o espelho
        sc = QShortcut(QKeySequence("Backspace"), self)
        sc.setContext(_Qt.ShortcutContext.WidgetWithChildrenShortcut)
        sc.activated.connect(self._excluir_selecao)
        self._paleta = None

    def showEvent(self, ev) -> None:  # noqa: N802 (Qt)
        super().showEvent(ev)
        # RG-54: restaura o estado do painel lateral (uma vez, fora do boot)
        if getattr(self, "_lateral_restaurada", False):
            return
        self._lateral_restaurada = True
        try:
            from app.core.database import Database
            from app.core.repositories import ConfigRepositorio
            db = Database().init()
            try:
                with db.Session() as s:
                    vis = ConfigRepositorio(s).get("editor.lateral_visivel", True)
            finally:
                db.engine.dispose()
            if vis is False:
                self.alternar_lateral(False)
        except Exception:
            pass

    def alternar_lateral(self, mostrar: bool | None = None) -> None:
        """RG-54 (passo 49): recolhe/expande o painel lateral por uma seta —
        telas pequenas ganham o canvas inteiro. Lembra o estado em Config."""
        novo = (not self._lateral.isVisible()) if mostrar is None else mostrar
        self._lateral.setVisible(novo)
        try:
            from app.core.database import Database
            from app.core.repositories import ConfigRepositorio
            db = Database().init()
            try:
                with db.Session() as s:
                    ConfigRepositorio(s).set("editor.lateral_visivel", bool(novo))
                    s.commit()
            finally:
                db.engine.dispose()
        except Exception:
            pass
        if hasattr(self.barra, "atualizar_botao_lateral"):
            self.barra.atualizar_botao_lateral(novo)

    def abrir_paleta(self) -> None:
        """Paleta de comandos (Ctrl+Shift+P): busca e executa qualquer ação
        do editor. FASE 2: o Ctrl+K virou a BUSCA GLOBAL em todas as telas
        (decisão do passo 74 — dois donos do mesmo atalho = ambiguidade Qt,
        nenhum dispararia)."""
        from app.qt.design.paleta_comandos import PaletaComandos, acoes_do_editor
        if self._paleta is None:
            self._paleta = PaletaComandos(self.window(), acoes_do_editor(self))
        self._paleta.abrir()

    def _duplicar_selecao(self) -> None:
        reg = self.canvas.selecionada()
        if reg is not None:
            self.canvas.duplicar_regiao(reg)

    def _excluir_selecao(self) -> None:
        regs = [it.regiao for it in self.canvas.selecionados()]
        if regs:                          # RG-06: a seleção inteira, 1 undo
            self.canvas.excluir_regioes(regs)
            # FASE 1 (71-72): "Desfazer" no toast, ligado ao undo REAL do
            # canvas (excluir_regioes já empilhou 1 passo de histórico)
            from app.qt.design.toast import mostrar_toast_desfazer
            n = len(regs)
            texto = ("1 região excluída." if n == 1
                     else f"{n} regiões excluídas.")
            mostrar_toast_desfazer(self, texto, self.canvas.desfazer)

    @property
    def canvas(self):
        return self.area.canvas

    def carregar(self, layout: LayoutDef, dados: DadosProduto, fundo_path=None) -> None:
        self._dados = dados
        self.area.carregar(layout, dados, fundo_path)
        self.camadas.recarregar()
        if hasattr(self.barra, "sincronizar_grade"):
            self.barra.sincronizar_grade(self.canvas)   # R-028: reflete a página
        self._marcar_sujo(False)

    # --- estado salvo/não salvo -------------------------------------------------

    def _marcar_sujo(self, sujo: bool) -> None:
        if sujo != self._sujo:
            self._sujo = sujo
            self.sujo_mudou.emit(sujo)

    # --- salvar / carregar layout no banco ------------------------------------

    def _banco(self) -> Database:
        if self._db is None:
            self._db = Database().init()
        return self._db

    def salvar(self) -> None:
        layout = self.canvas._layout
        if layout is None:
            return
        nome, ok = QInputDialog.getText(self, "Salvar layout", "Nome do layout:",
                                        text=self.nome_layout_atual)  # A4
        if not ok or not nome.strip():
            return
        with self._banco().Session() as s:
            existentes = {r.nome for r in listar_layouts(s)}
        # P1.6: sobrescrever OUTRO layout pede confirmação; re-salvar o próprio
        # (nome pré-preenchido, inalterado) segue direto
        if nome.strip() in existentes and nome.strip() != self.nome_layout_atual:
            from PySide6.QtWidgets import QMessageBox
            from app.qt.design.componentes import confirmar_destrutivo
            if not confirmar_destrutivo(          # passo 78: verbo no botão
                    self, "Layout já existe",
                    f"Já existe um layout “{nome.strip()}”.", "Sobrescrever"):
                return
        with self._banco().Session() as s:
            salvar_layout(s, nome.strip(), layout)
            s.commit()
        self.nome_layout_atual = nome.strip()
        self._marcar_sujo(False)
        self._avisar(f"Layout “{nome.strip()}” salvo no banco.")

    def carregar_do_banco(self) -> None:
        with self._banco().Session() as s:
            rows = listar_layouts(s)
            if not rows:
                self._avisar("Nenhum layout salvo ainda.", tipo="info")
                return
            nomes = [r.nome for r in rows]
            nome, ok = QInputDialog.getItem(self, "Carregar layout", "Escolha:", nomes, 0, False)
            if not ok:
                return
            row = next(r for r in rows if r.nome == nome)
            layout = carregar_layout(s, row.id)
        self.nome_layout_atual = nome      # A4
        if layout is not None:
            self.area.carregar(layout, self._dados or DadosProduto(""), fundo_path=layout.arquivo_fundo)
            self.camadas.recarregar()
            self._marcar_sujo(False)

    def _avisar(self, texto: str, tipo: str = "sucesso") -> None:
        """Feedback leve (toast). Cai num QMessageBox se o toast não existir."""
        try:
            from app.qt.design.toast import mostrar_toast
            mostrar_toast(self, texto, tipo=tipo)
        except ImportError:
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.information(self, "AutoTabloide", texto)

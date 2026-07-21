"""
Barra de ferramentas do editor — versão do sistema de design
============================================================
Mesmas ações da barra atual (zoom, adicionar região, alinhar, distribuir,
salvar/carregar), mas com ícones de verdade + tooltips, grupos com separadores
e a wordmark do app. Substitui ``app/qt/barra.py`` quando o visual for aprovado.
"""

from __future__ import annotations

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import QFrame, QHBoxLayout, QPushButton, QToolButton, QWidget

from app.qt.design import tokens as t
from app.qt.design.icones import icone
from app.rendering.model import TipoRegiao


def _tool(nome_icone: str, tip: str, slot, atalho: str | None = None,
          dono=None) -> QToolButton:
    """``atalho`` agora é um ID do catálogo central (R-018) — a tecla
    efetiva (customizada ou padrão) entra no tooltip e no QShortcut."""
    from app.qt.design.atalhos import criar_atalho, sequencia
    b = QToolButton()
    b.setIcon(icone(nome_icone))
    b.setIconSize(QSize(20, 20))
    b.setToolTip(f"{tip}  ·  {sequencia(atalho)}" if atalho else tip)
    b.clicked.connect(slot)
    if atalho and dono is not None:
        criar_atalho(atalho, dono, slot)
    return b


def _sep() -> QFrame:
    f = QFrame()
    f.setProperty("papel", "separador")
    f.setFrameShape(QFrame.Shape.VLine)
    return f


class BarraEditor(QWidget):
    def __init__(self, editor, parent=None):
        super().__init__(parent)
        self.setObjectName("barraFerramentas")
        # OS F11.5 #50 (RG-53/54): a barra PODE encolher abaixo do conteúdo —
        # sem isto ela PINAVA a janela na largura do conteúdo (1665px a 125%)
        # e o modo compacto do resizeEvent nunca chegava a disparar (a mesma
        # lição da barra da Mesa).
        self.setMinimumWidth(1)
        c = editor.canvas
        self._c = c
        lay = QHBoxLayout(self)
        lay.setContentsMargins(t.ESP_3, t.ESP_1, t.ESP_3, t.ESP_1)
        lay.setSpacing(2)

        # desfazer / refazer (F5.10)
        lay.addWidget(_tool("desfazer", "Desfazer", c.desfazer,
                            "editor.desfazer", editor))
        lay.addWidget(_tool("refazer", "Refazer", c.refazer,
                            "editor.refazer", editor))
        lay.addWidget(_sep())

        # zoom / enquadrar
        lay.addWidget(_tool("zoom_menos", "Diminuir zoom", c.zoom_menos,
                            "editor.zoom_menos", editor))
        lay.addWidget(_tool("zoom_mais", "Aumentar zoom", c.zoom_mais,
                            "editor.zoom_mais", editor))
        # R-029 (passo 69): "100%" e "Ajustar" SEMPRE visíveis (resposta ao
        # zoom perdido do RG-05) + o nível de zoom em %
        from PySide6.QtWidgets import QLabel as _QLabel
        b100 = QToolButton()
        b100.setText("100%")
        b100.setToolTip("Zoom em 100%")
        b100.clicked.connect(c.zoom_100)
        lay.addWidget(b100)
        lay.addWidget(_tool("ajustar", "Ajustar à tela", c.ajustar,
                            "editor.ajustar", editor))
        bsel = QToolButton()
        bsel.setText("⤢ seleção")
        bsel.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextOnly)
        bsel.setToolTip("Zoom para a seleção (enquadra a região escolhida)")
        bsel.clicked.connect(lambda: c.zoom_para_selecao())
        lay.addWidget(bsel)
        self._zoom_lbl = _QLabel("100%")
        self._zoom_lbl.setProperty("papel", "legenda")
        self._zoom_lbl.setFixedWidth(46)
        self._zoom_lbl.setToolTip("Nível de zoom atual")
        lay.addWidget(self._zoom_lbl)
        c.transformou.connect(self._atualizar_zoom_lbl)
        # R-040 (passo 73): modo raio-x (esconde a arte, mostra as regiões)
        self._btn_raiox = QToolButton()
        self._btn_raiox.setIcon(icone("olho", tamanho=20))
        self._btn_raiox.setIconSize(QSize(20, 20))
        self._btn_raiox.setCheckable(True)
        self._btn_raiox.setToolTip("Raio-x: esconde a arte e mostra só as "
                                   "regiões (por cor)")
        self._btn_raiox.toggled.connect(c.set_raio_x)
        lay.addWidget(self._btn_raiox)
        lay.addWidget(_sep())

        # adicionar região. RG-57: o TEXTO_LEGAL abre o diálogo NOMEADO de
        # papel (validade/dica/legal/livre) antes de nascer; os demais tipos
        # entram direto no centro.
        from app.qt.design.papel_texto_ui import criar_texto_legal_com_papel

        def _acao_add(tp):
            if tp == TipoRegiao.TEXTO_LEGAL:
                return lambda _=False: criar_texto_legal_com_papel(c, c.window())
            return lambda _=False, t=tp: c.adicionar_regiao(t)

        for nome_ic, tipo, tip in [
            ("imagem", TipoRegiao.IMAGEM, "Adicionar imagem"),
            ("texto", TipoRegiao.NOME, "Adicionar nome do produto"),
            ("preco", TipoRegiao.PRECO, "Adicionar preço"),
            ("unidade", TipoRegiao.UNIDADE, "Adicionar unidade/gramatura"),
            ("selo", TipoRegiao.SELO, "Adicionar selo"),
            ("paragrafo", TipoRegiao.TEXTO_LEGAL,
             "Adicionar texto legal / aviso (validade, “Fica a Dica”…)"),
        ]:
            lay.addWidget(_tool(nome_ic, tip, _acao_add(tipo)))
        # R-048/R-044: biblioteca de modelos de célula (trios prontos + vitrine)
        lay.addWidget(_tool("grade", "Modelos de célula (carimbar um trio pronto)",
                            lambda: self._abrir_modelos(editor)))
        # Bloco D: páginas/histórico, prévia de impressão, verificador de contraste
        lay.addWidget(_tool("camadas", "Páginas e histórico visual",
                            lambda: self._abrir_paginas(editor)))
        lay.addWidget(_tool("impressora", "Prévia de impressão (margens e sangria)",
                            lambda: self._abrir_previa(editor)))
        lay.addWidget(_tool("olho", "Verificar contraste do texto sobre a foto",
                            lambda: self._verificar_contraste(editor)))
        lay.addWidget(_sep())

        # alinhar (na seleção) — FASE 1 (passo 57): alinhar+distribuir são
        # os grupos menos usados; abaixo de 1200 px colapsam num "···"
        acoes_alinhar = [
            ("alinhar_esq", "esq", "Alinhar à esquerda"),
            ("alinhar_cent_h", "centro_h", "Centralizar na horizontal"),
            ("alinhar_dir", "dir", "Alinhar à direita"),
            ("alinhar_topo", "topo", "Alinhar ao topo"),
            ("alinhar_meio", "meio", "Centralizar na vertical"),
            ("alinhar_base", "base", "Alinhar à base"),
        ]
        self._colapsaveis: list[QWidget] = []
        for nome_ic, modo, tip in acoes_alinhar:
            b = _tool(nome_ic, tip,
                      lambda _=False, m=modo: c.alinhar_selecionadas(m))
            self._colapsaveis.append(b)
            lay.addWidget(b)
        sep_a = _sep()
        self._colapsaveis.append(sep_a)
        lay.addWidget(sep_a)

        # distribuir
        for nome_ic, tip, modo in [
            ("dist_h", "Distribuir igualmente na horizontal", "h"),
            ("dist_v", "Distribuir igualmente na vertical", "v"),
        ]:
            b = _tool(nome_ic, tip,
                      lambda _=False, m=modo: c.distribuir_selecionadas(m))
            self._colapsaveis.append(b)
            lay.addWidget(b)
        sep_d = _sep()
        self._colapsaveis.append(sep_d)
        lay.addWidget(sep_d)

        # o "···" que herda os grupos colapsados na janela estreita
        from PySide6.QtWidgets import QMenu
        self._mais = QToolButton()
        self._mais.setText("···")
        self._mais.setToolTip("Alinhar e distribuir")
        self._mais.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        menu = QMenu(self._mais)
        for nome_ic, modo, tip in acoes_alinhar:   # passo 79: com ícones
            menu.addAction(icone(nome_ic), tip,
                           lambda m=modo: c.alinhar_selecionadas(m))
        menu.addSeparator()
        menu.addAction(icone("dist_h"), "Distribuir igualmente na horizontal",
                       lambda: c.distribuir_selecionadas("h"))
        menu.addAction(icone("dist_v"), "Distribuir igualmente na vertical",
                       lambda: c.distribuir_selecionadas("v"))
        self._mais.setMenu(menu)
        self._mais.hide()
        lay.addWidget(self._mais)
        lay.addWidget(_sep())

        # R-028 (Fase 4): grade magnética (liga/desliga) + passo em mm, e
        # "limpar guias" (R-027). Refletem o estado da página atual.
        from PySide6.QtWidgets import QDoubleSpinBox
        self._btn_grade = QToolButton()
        self._btn_grade.setIcon(icone("grade", tamanho=20))
        self._btn_grade.setIconSize(QSize(20, 20))
        self._btn_grade.setCheckable(True)
        self._btn_grade.setToolTip("Grade magnética: os objetos imantam nos "
                                   "múltiplos do passo")
        self._btn_grade.toggled.connect(c.set_grade_magnetica)
        lay.addWidget(self._btn_grade)
        self._passo_grade = QDoubleSpinBox()
        self._passo_grade.setRange(0.5, 50.0)
        self._passo_grade.setSingleStep(0.5)
        self._passo_grade.setValue(5.0)
        self._passo_grade.setSuffix(" mm")
        self._passo_grade.setFixedWidth(78)
        self._passo_grade.setToolTip("Passo da grade magnética")
        self._passo_grade.valueChanged.connect(c.set_grade_passo)
        lay.addWidget(self._passo_grade)
        lay.addWidget(_tool("lixeira", "Limpar todas as guias", c.limpar_guias))
        lay.addWidget(_sep())

        # páginas (F5.8/D8.4): navegar, adicionar com arte própria, remover
        from PySide6.QtWidgets import QLabel
        lay.addWidget(_tool("seta_cima", "Página anterior",
                            lambda: c.ir_para_pagina(c.pagina_atual - 1)))
        self._pag_lbl = QLabel("1/1")
        self._pag_lbl.setProperty("papel", "legenda")
        self._pag_lbl.setToolTip("Página atual / total")
        lay.addWidget(self._pag_lbl)
        lay.addWidget(_tool("seta_baixo", "Próxima página",
                            lambda: c.ir_para_pagina(c.pagina_atual + 1)))
        lay.addWidget(_tool("imagem", "Adicionar página (importar a arte dela)",
                            lambda: self._adicionar_pagina(editor)))
        lay.addWidget(_tool("lixeira", "Remover a página atual "
                            "(itens dela voltam à estante; Ctrl+Z desfaz)",
                            lambda: self._remover_pagina(editor)))
        c.editou.connect(lambda _reg: self._atualizar_pag(c))
        self._atualizar_pag(c)

        # RG-56 (passo 26): Ajuda › Como agrupar — sempre acessível (não é
        # pop-up único que some para sempre)
        ajuda = QToolButton()
        ajuda.setIcon(icone("info_circulo"))
        ajuda.setIconSize(QSize(20, 20))
        ajuda.setToolTip("Ajuda")
        ajuda.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        menu_ajuda = QMenu(ajuda)
        menu_ajuda.addAction(
            icone("grade", tamanho=16), "Como agrupar…",
            lambda: c.abrir_tutorial_agrupar(primeira_vez=False))
        ajuda.setMenu(menu_ajuda)
        lay.addWidget(ajuda)
        lay.addStretch(1)
        # R-041 (passo 75): medidas ao vivo (X/Y/L/A em mm ao mover/redim.)
        from PySide6.QtWidgets import QLabel as _QLabel2
        self._medidas_lbl = _QLabel2("")
        self._medidas_lbl.setProperty("papel", "legenda")
        self._medidas_lbl.setToolTip("Posição e tamanho da região em mm")
        lay.addWidget(self._medidas_lbl)
        c.medidas.connect(self._medidas_lbl.setText)
        c.selecao_mudou.connect(lambda _r: self._medidas_lbl.setText(""))
        lay.addStretch(1)

        # RG-54 (passo 49): recolher/expandir o painel lateral (canvas maior
        # nas telas pequenas)
        self._btn_lateral = QToolButton()
        self._btn_lateral.setIconSize(QSize(20, 20))
        self._btn_lateral.setCheckable(True)
        self._btn_lateral.setChecked(True)
        self.atualizar_botao_lateral(True)
        self._btn_lateral.clicked.connect(
            lambda: editor.alternar_lateral())
        lay.addWidget(self._btn_lateral)
        lay.addSpacing(t.ESP_2)

        # layout no banco (à direita: texto + ícone; salvar é a ação primária)
        abrir = QPushButton(" Abrir")
        abrir.setIcon(icone("abrir"))
        abrir.setToolTip("Carregar um layout salvo no banco  ·  Ctrl+O")
        abrir.clicked.connect(editor.carregar_do_banco)
        salvar = QPushButton(" Salvar")
        salvar.setIcon(icone("salvar", cor=t.ACENTO_TEXTO))
        salvar.setProperty("tipo", "primario")
        salvar.setToolTip("Salvar o layout no banco  ·  Ctrl+S")
        salvar.clicked.connect(editor.salvar)
        lay.addWidget(abrir)
        lay.addSpacing(t.ESP_2)
        lay.addWidget(salvar)

        from app.qt.design.atalhos import criar_atalho
        for id_atalho, slot in [("editor.salvar", editor.salvar),
                                ("editor.abrir", editor.carregar_do_banco)]:
            criar_atalho(id_atalho, editor, slot)

    def _atualizar_zoom_lbl(self) -> None:
        """R-029 (passo 70): o % de zoom com clamp são."""
        if hasattr(self, "_zoom_lbl"):
            self._zoom_lbl.setText(f"{self._c.nivel_zoom_pct()}%")

    def _abrir_modelos(self, editor) -> None:
        """R-048: abre a biblioteca de modelos de célula (carimbar/salvar)."""
        from app.qt.telas.modelos_dialog import DialogoModelos
        DialogoModelos(self._c, editor.window()).exec()

    def _abrir_paginas(self, editor) -> None:
        """R-030/R-042: miniaturas das páginas + histórico visual."""
        from app.qt.telas.paginas_dialog import DialogoPaginas
        DialogoPaginas(self._c, editor.window()).exec()

    def _abrir_previa(self, editor) -> None:
        """R-046: prévia de impressão (margens + sangria) da página atual."""
        c = self._c
        if c._layout is None:
            return
        from app.rendering.previa_impressao import previa_impressao
        from app.qt.canvas import pil_para_qpixmap
        from PySide6.QtWidgets import (
            QDialog, QLabel, QScrollArea, QVBoxLayout,
        )
        img = previa_impressao(c._layout, c._pagina(), c._dados,
                               fundo_path=(c._fundo if c.pagina_atual == 0 else None))
        dlg = QDialog(editor.window())
        dlg.setWindowTitle("Prévia de impressão")
        dlg.resize(560, 720)
        lbl = QLabel()
        lbl.setPixmap(pil_para_qpixmap(img))
        rol = QScrollArea()
        rol.setWidget(lbl)
        rol.setWidgetResizable(True)
        lay = QVBoxLayout(dlg)
        lay.addWidget(rol)
        dlg.exec()

    def _verificar_contraste(self, editor) -> None:
        """R-047: acusa textos pouco legíveis sobre a foto (I2, com sugestão)."""
        c = self._c
        if c._layout is None:
            return
        from app.rendering.contraste import avisos_contraste
        avisos = avisos_contraste(
            c._layout, c._pagina(), c._dados,
            fundo_path=(c._fundo if c.pagina_atual == 0 else None))
        try:
            from app.qt.design.toast import mostrar_toast
            if avisos:
                mostrar_toast(editor, avisos[0]
                              + (f"  (+{len(avisos) - 1})" if len(avisos) > 1 else ""),
                              tipo="erro")
            else:
                mostrar_toast(editor, "Contraste ok: os textos estão legíveis.",
                              tipo="sucesso")
        except Exception:
            pass

    def sincronizar_grade(self, canvas) -> None:
        """R-028: reflete a grade magnética/passo da página carregada nos
        controles (sem disparar os sinais)."""
        if canvas._layout is None:
            return
        pag = canvas._pagina()
        self._btn_grade.blockSignals(True)
        self._btn_grade.setChecked(bool(pag.grade_magnetica))
        self._btn_grade.blockSignals(False)
        self._passo_grade.blockSignals(True)
        self._passo_grade.setValue(float(pag.grade_passo_mm))
        self._passo_grade.blockSignals(False)

    def atualizar_botao_lateral(self, visivel: bool) -> None:
        """Reflete o estado do painel lateral no ícone/tooltip do botão."""
        self._btn_lateral.setChecked(visivel)
        self._btn_lateral.setIcon(icone("propriedades", tamanho=20))
        self._btn_lateral.setToolTip(
            "Recolher o painel (canvas maior)" if visivel
            else "Mostrar o painel de camadas e propriedades")

    # RG-54 (reauditoria F4): 1200 era MENOR que a largura de 720p (1280) —
    # o modo compacto nunca ativava e a barra estourava, cortando "Salvar".
    # Acima de 1280 para o compacto valer no pior caso do dono.
    LIMIAR_COMPACTO = 1360      # px de largura

    def resizeEvent(self, ev) -> None:  # noqa: N802 (Qt)
        super().resizeEvent(ev)
        self._aplicar_compacto(self.width())

    def _aplicar_compacto(self, largura: int) -> bool:
        """Decide o modo compacto por LARGURA — recolhe os grupos
        colapsáveis no "···" abaixo do limiar. Extraído do resizeEvent para
        ser testável de forma determinística (a produção chama o mesmo)."""
        compacto = largura < self.LIMIAR_COMPACTO
        for w in self._colapsaveis:
            w.setVisible(not compacto)
        self._mais.setVisible(compacto)
        return compacto

    # --- páginas (D8.4) -----------------------------------------------------------

    def _atualizar_pag(self, c) -> None:
        total = max(1, c.total_paginas())
        self._pag_lbl.setText(f"{c.pagina_atual + 1}/{total}")

    def _adicionar_pagina(self, editor) -> None:
        from PySide6.QtWidgets import QFileDialog
        caminho, _ = QFileDialog.getOpenFileName(
            editor, "Arte da página nova", "",
            "Imagens (*.png *.jpg *.jpeg *.webp)")
        if caminho:
            editor.canvas.adicionar_pagina_arte(caminho)

    def _remover_pagina(self, editor) -> None:
        from PySide6.QtWidgets import QMessageBox
        c = editor.canvas
        if c.total_paginas() <= 1:
            return
        from app.qt.design.componentes import confirmar_destrutivo
        if confirmar_destrutivo(                  # passo 78: verbo no botão
                editor, "Remover página",
                f"Os itens da página {c.pagina_atual + 1} voltam à estante "
                "(Ctrl+Z desfaz tudo).",
                f"Remover página {c.pagina_atual + 1}"):
            c.remover_pagina_atual()

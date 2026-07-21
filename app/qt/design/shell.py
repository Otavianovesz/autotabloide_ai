"""
Shell do aplicativo
===================
A casca que envolve todas as telas: top-bar com wordmark + navegação
(Início, Ateliê, Almoxarifado, Mesa, Fábrica, Cofre, Configurações) e
barra de status refinada (dica contextual, salvo/não salvo, dimensões, zoom).

As telas do Bloco D nascem aqui: ``adicionar_tela()`` registra cada uma no
navegador; as que ainda não existem entram desabilitadas (visão de futuro).
"""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QStackedWidget,
    QStatusBar,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from app.qt.design import tokens as t
from app.qt.design.componentes import Wordmark
from app.qt.design.icones import icone

# Telas do app (ordem da navegação). Ícone + rótulo; Bloco D preenche uma a uma.
# Auditoria do dono (20/07): "Configurações" SAIU da navegação — mora só na
# engrenagem (a aba + o ícone eram redundância); "Eventos" GANHOU aba própria
# entre o Início e o Ateliê (o Início ficou só o dashboard).
TELAS = [
    ("inicio", "Início", "casa"),
    ("eventos", "Eventos", "calendario"),
    ("atelie", "Ateliê", "camadas"),
    ("almoxarifado", "Almoxarifado", "caixa"),
    ("mesa", "Mesa", "grade"),
    ("fabrica", "Fábrica", "impressora"),
    ("cofre", "Cofre", "cofre"),
]
# navegáveis por código mesmo sem botão (a tela de Configurações continua
# existindo — só não tem aba)
TELAS_CHAVES = {c for c, _r, _i in TELAS} | {"configuracoes"}


class Shell(QMainWindow):
    """Janela principal: top-bar de navegação + pilha de telas + status."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("AutoTabloide AI")
        self._botoes: dict[str, QToolButton] = {}
        self._canvases_zoom: dict[str, object] = {}   # tela → canvas (RG-05)
        self._tela_ativa: str | None = None
        # RG-08: salvo/não-salvo POR TELA — o indicador único confundia
        # (uma tela sem documento mostrava o estado de outra)
        self._salvo_por_tela: dict[str, bool] = {}
        # FASE 1 (passo 77): nome do documento por tela → título da janela
        self._doc_por_tela: dict[str, str] = {}

        # --- top-bar ---------------------------------------------------------
        topo = QWidget()
        topo.setObjectName("topBar")
        topo.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        hl = QHBoxLayout(topo)
        hl.setContentsMargins(t.ESP_3, t.ESP_1 + 2, t.ESP_3, t.ESP_1 + 2)
        hl.setSpacing(t.ESP_1)
        hl.addWidget(Wordmark())
        hl.addSpacing(t.ESP_4)
        for chave, rotulo, nome_icone in TELAS:
            b = QToolButton()
            b.setText(rotulo)
            b.setIcon(icone(nome_icone, cor=t.TEXTO_2, tamanho=16))
            b.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
            b.setProperty("nav", "true")
            b.setCheckable(True)
            b.setEnabled(False)  # habilita quando a tela é registrada
            b.clicked.connect(lambda _=False, c=chave: self.ir_para(c))
            self._botoes[chave] = b
            hl.addWidget(b)
        hl.addStretch(1)
        config = QToolButton()
        config.setIcon(icone("engrenagem", cor=t.TEXTO_2, tamanho=18))
        # FASE 1 (passo 82): a engrenagem virou MENU — o toggle de tema
        # (passo 25) continua a 1 clique, e Sobre/diagnóstico moram aqui
        config.setToolTip("Configurações, tema e Sobre")
        config.setProperty("nav", "true")
        config.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        from PySide6.QtWidgets import QMenu
        # FASE 3 (passo 15): a engrenagem é o MENU RÁPIDO — a tela completa
        # de Configurações mora na aba do topo (lugar ÚNICO, sem fantasma)
        menu_cfg = QMenu(config)
        menu_cfg.addAction(icone("olho", tamanho=16),
                           "Alternar tema claro/escuro", self._alternar_tema)
        menu_cfg.addAction(icone("propriedades", tamanho=16),
                           "Configurações completas…",
                           lambda: self.ir_para("configuracoes"))
        menu_cfg.addSeparator()
        menu_cfg.addAction(icone("info_circulo", tamanho=16),
                           "Sobre o AutoTabloide…", self._abrir_sobre)
        config.setMenu(menu_cfg)
        self._botoes["config"] = config
        hl.addWidget(config)

        # --- pilha de telas ---------------------------------------------------
        self._pilha = QStackedWidget()
        self._telas: dict[str, int] = {}

        raiz = QWidget()
        vl = QVBoxLayout(raiz)
        vl.setContentsMargins(0, 0, 0, 0)
        vl.setSpacing(0)
        vl.addWidget(topo)
        vl.addWidget(self._pilha, 1)
        self.setCentralWidget(raiz)

        # --- barra de status --------------------------------------------------
        status = QStatusBar()
        status.setSizeGripEnabled(False)
        self._dica = QLabel("")
        self._dica.setProperty("papel", "legenda")
        status.addWidget(QLabel("  "))
        status.addWidget(self._dica, 1)
        self._salvo = QLabel("")
        self._dimensoes = QLabel("")
        self._dimensoes.setProperty("papel", "legenda")
        self._zoom = QLabel("")
        self._zoom.setProperty("papel", "legenda")
        # FASE 1 (passo 61): largura RESERVADA — o rodapé não dança quando
        # "Zoom 8%" vira "Zoom 8000%" ou "Salvo" vira "Não salvo"
        fm = self._zoom.fontMetrics()
        self._zoom.setMinimumWidth(fm.horizontalAdvance("  ·  Zoom 8000%"))
        self._salvo.setMinimumWidth(fm.horizontalAdvance("● Não salvo") + 8)
        self._dimensoes.setMinimumWidth(
            fm.horizontalAdvance("  ·  9999 × 9999 mm"))
        for w in (self._salvo, self._dimensoes, self._zoom):
            status.addPermanentWidget(w)
        status.addPermanentWidget(QLabel(" "))
        self.setStatusBar(status)
        # RG-08: nada de "Salvo" de fábrica — o indicador só fala quando a
        # tela ativa tem documento com estado conhecido (set_salvo_de)

    # --- telas ----------------------------------------------------------------

    def adicionar_tela(self, chave: str, widget: QWidget) -> None:
        """Registra uma tela e habilita o botão dela na navegação."""
        self._telas[chave] = self._pilha.addWidget(widget)
        if chave in self._botoes:
            self._botoes[chave].setEnabled(True)

    def adicionar_tela_preguicosa(self, chave: str, fabrica) -> None:
        """FASE 3 (passo 93): a tela só é CONSTRUÍDA na primeira visita —
        o boot não paga por tela que o usuário talvez nem abra hoje."""
        if not hasattr(self, "_fabricas"):
            self._fabricas: dict = {}
        self._fabricas[chave] = fabrica
        if chave in self._botoes:
            self._botoes[chave].setEnabled(True)

    def tela(self, chave: str) -> QWidget | None:
        """A instância da tela (materializa a preguiçosa se preciso)."""
        if chave not in self._telas and chave in getattr(self, "_fabricas", {}):
            self.adicionar_tela(chave, self._fabricas.pop(chave)())
        if chave in self._telas:
            return self._pilha.widget(self._telas[chave])
        return None

    def ir_para(self, chave: str) -> None:
        if chave not in self._telas and chave in getattr(self, "_fabricas", {}):
            self.adicionar_tela(chave, self._fabricas.pop(chave)())
        if chave not in self._telas:
            return
        # FASE 1 (passo 38): crossfade suave — nunca "pisca"; com
        # "Reduzir animações" a troca é seca como sempre foi
        from app.qt.design.animacoes import crossfade
        atual = self._pilha.currentWidget()
        destino = self._pilha.widget(self._telas[chave])
        crossfade(self._pilha, atual, destino)
        # O conserto do "desenquadrado": a tela que estava oculta pode carregar
        # geometria VELHA (a janela mudou de tamanho enquanto outra tela estava
        # na frente) — os reflows (RG-53) mediam largura errada e só um resize
        # externo consertava. Um resize SINTÉTICO no tamanho real, após o
        # laço de eventos assentar o layout, re-mede tudo.
        from PySide6.QtCore import QTimer
        QTimer.singleShot(0, lambda w=destino: self._reenquadrar(w))
        for c, b in self._botoes.items():
            b.setChecked(c == chave)
        self._tela_ativa = chave
        # R-150 (frota F12): no Modo Pai a top-bar SOME — a promessa
        # "nenhuma ação destrutiva alcançável" valia só dentro da tela,
        # mas a navegação inteira (Mesa, Cofre, excluir projeto…) seguia
        # a 1 clique. A única saída é o botão "Sair do modo simples".
        topo = self.findChild(QWidget, "topBar")
        if topo is not None:
            topo.setVisible(chave != "modo_pai")
        self._refletir_zoom()
        self._refletir_salvo()
        # RG-17: microtutorial na PRIMEIRA visita de cada tela (Config lembra)
        from app.qt.design.tutorial import mostrar_se_primeira_vez
        mostrar_se_primeira_vez(self, chave)

    def _reenquadrar(self, w: QWidget) -> None:
        """Resize sintético pós-troca: ativa o layout e despacha um
        QResizeEvent com o tamanho REAL — quem reage a resize (as barras
        RG-53, os canvases) re-mede com o número certo."""
        try:
            from shiboken6 import isValid
            if not isValid(w):
                return
        except Exception:
            pass
        if not w.isVisible():
            return
        if w.layout() is not None:
            w.layout().activate()
        from PySide6.QtGui import QResizeEvent
        from PySide6.QtWidgets import QApplication
        QApplication.sendEvent(w, QResizeEvent(w.size(), w.size()))

    # --- zoom honesto por tela (RG-05) -----------------------------------------

    def registrar_zoom(self, chave: str, canvas) -> None:
        """O rodapé mostra o zoom do canvas DA TELA ATIVA. (Antes, o número
        vinha de um canvas invisível e mentia "2%" o tempo todo.)"""
        self._canvases_zoom[chave] = canvas
        canvas.transformou.connect(lambda c=chave: self._zoom_mudou(c))

    def _zoom_mudou(self, chave: str) -> None:
        if chave == self._tela_ativa:
            self.set_zoom(self._canvases_zoom[chave].escala_atual())

    def _refletir_zoom(self) -> None:
        canvas = self._canvases_zoom.get(self._tela_ativa)
        if canvas is not None:
            self.set_zoom(canvas.escala_atual())
        else:
            self._zoom.setText("")       # tela sem canvas: sem número solto

    def _alternar_tema(self) -> None:
        """FASE 1 (passo 25): sol/lua de um clique, persistido na Config."""
        from app.qt.design.tema import trocar_tema
        trocar_tema("escuro" if t.TEMA_ATUAL == "claro" else "claro")

    def _abrir_sobre(self) -> None:
        """FASE 1 (passo 82): versão, créditos e diagnóstico."""
        from app.qt.design.sobre import SobreDialog
        SobreDialog(self).exec()

    def retematizar(self) -> None:
        """FASE 1 (passo 19): refaz os ícones do top-bar na troca de tema
        (ícone é pixmap pintado — o repolimento de QSS não o recolore)."""
        for chave, rotulo, nome_icone in TELAS:
            if chave in self._botoes:
                self._botoes[chave].setIcon(
                    icone(nome_icone, cor=t.TEXTO_2, tamanho=16))
        if "config" in self._botoes:
            self._botoes["config"].setIcon(
                icone("engrenagem", cor=t.TEXTO_2, tamanho=18))

    # --- fechamento ------------------------------------------------------------

    def closeEvent(self, event) -> None:  # noqa: N802 (Qt)
        """RG-05b: nenhum worker vivo ao fechar o app (política global)."""
        self._gravar_estado()           # FASE 1 (passo 60, R-023)
        from app.qt.workers import encerrar_todos
        encerrar_todos()
        super().closeEvent(event)

    # --- memória de janela (FASE 1, passo 60 — R-023) --------------------------

    def _gravar_estado(self) -> None:
        try:
            from app.core.database import Database
            from app.core.repositories import ConfigRepositorio
            g = self.normalGeometry()
            db = Database().init()
            try:
                with db.Session() as s:
                    ConfigRepositorio(s).set("ui.shell", {
                        "geometria": [g.x(), g.y(), g.width(), g.height()],
                        "maximizada": self.isMaximized(),
                        "tela": self._tela_ativa or "inicio",
                    })
                    s.commit()
            finally:
                db.engine.dispose()
        except Exception as e:          # I2: nunca em silêncio total
            print(f"aviso: não gravei o estado da janela ({e})")

    def restaurar_estado(self) -> str:
        """Aplica geometria lembrada e devolve a chave da última tela
        (o chamador navega quando as telas pesadas existirem — RG-01)."""
        try:
            from app.core.database import Database
            from app.core.repositories import ConfigRepositorio
            db = Database().init()
            try:
                with db.Session() as s:
                    estado = ConfigRepositorio(s).get("ui.shell") or {}
            finally:
                db.engine.dispose()
        except Exception:
            estado = {}
        geo = estado.get("geometria")
        if (isinstance(geo, list) and len(geo) == 4
                and all(isinstance(v, int) for v in geo)
                and geo[2] >= 640 and geo[3] >= 480):
            from PySide6.QtCore import QRect
            from PySide6.QtGui import QGuiApplication
            r = QRect(*geo)
            # default são: fora de qualquer tela atual (monitor desligado),
            # volta ao padrão em vez de abrir invisível
            telas = [sc.availableGeometry() for sc
                     in QGuiApplication.screens()]
            if any(tt.intersects(r) for tt in telas):
                self.setGeometry(r)
        if estado.get("maximizada"):
            self.showMaximized()
        tela = estado.get("tela")
        return tela if isinstance(tela, str) and tela in TELAS_CHAVES else \
            "inicio"

    # --- status ----------------------------------------------------------------

    def set_dica(self, texto: str) -> None:
        self._dica.setText(texto)

    def set_zoom(self, fator: float) -> None:
        """Fator 1.0 = 100% (1 px da página : 1 px da tela)."""
        self._zoom.setText(f"  ·  Zoom {fator * 100:.0f}%")

    def set_dimensoes(self, texto: str) -> None:
        self._dimensoes.setText(f"  ·  {texto}")

    def set_salvo(self, salvo: bool) -> None:
        cor, rotulo = (t.SUCESSO, "Salvo") if salvo else (t.ALERTA, "Não salvo")
        self._salvo.setText(f'<span style="color:{cor}">●</span> {rotulo}')

    def set_salvo_de(self, chave: str, salvo: bool) -> None:
        """RG-08: cada tela informa o PRÓPRIO estado; o rodapé mostra o da
        tela ativa (e fica vazio em tela sem documento — Cofre, Config…)."""
        self._salvo_por_tela[chave] = salvo
        if chave == self._tela_ativa:
            self.set_salvo(salvo)
            self._atualizar_titulo()     # o • do título acompanha (passo 77)

    def _refletir_salvo(self) -> None:
        salvo = self._salvo_por_tela.get(self._tela_ativa)
        if salvo is None:
            self._salvo.setText("")      # tela sem documento: sem estado solto
        else:
            self.set_salvo(salvo)
        self._atualizar_titulo()

    # --- título da janela (FASE 1, passo 77) -----------------------------------

    def set_documento_de(self, chave: str, nome: str | None) -> None:
        """Cada tela informa o documento aberto nela; o título mostra o da
        tela ativa: "AutoTabloide — [Projeto] •" (• = não salvo)."""
        if nome:
            self._doc_por_tela[chave] = nome
        else:
            self._doc_por_tela.pop(chave, None)
        if chave == self._tela_ativa:
            self._atualizar_titulo()

    def _atualizar_titulo(self) -> None:
        doc = self._doc_por_tela.get(self._tela_ativa)
        titulo = "AutoTabloide AI"
        if doc:
            titulo += f" — {doc}"
        if self._salvo_por_tela.get(self._tela_ativa) is False:
            titulo += " •"
        self.setWindowTitle(titulo)

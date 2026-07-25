"""
Motor de animação (FASE 1, Bloco D — R-151)
===========================================
Vida sem circo: 150–220 ms, curva OutCubic, e TUDO desligável pela Config
``aparencia.animacoes`` ("ligadas" | "reduzidas") — reduzidas = instantâneo
(máquina fraca do mercado e quem enjoa de movimento).

Helpers únicos (um lugar só): ``fade_in``, ``slide_y``, ``crossfade``.
Toda animação criada aqui se registra viva em ``_VIVAS`` enquanto roda —
o teste do passo 92 prova que "reduzidas" = zero animações ativas.
"""

from __future__ import annotations

from PySide6.QtCore import (
    QAbstractAnimation,
    QEasingCurve,
    QEvent,
    QObject,
    QPoint,
    QPropertyAnimation,
    QRect,
    Qt,
)
from PySide6.QtWidgets import QDialog, QGraphicsOpacityEffect, QWidget

DURACAO_MS = 180                 # o padrão da casa (passo 36)
DURACAO_HOVER_MS = 120
CURVA = QEasingCurve.Type.OutCubic

_VIVAS: list[QAbstractAnimation] = []    # animações em voo (p/ teste e GC)
_cache_config: dict = {}


def animacoes_ligadas() -> bool:
    """Config ``aparencia.animacoes`` (padrão: ligadas) — cache por sessão
    (invalidado por ``recarregar_config`` quando a tela de Config salva)."""
    if "valor" not in _cache_config:
        try:
            from app.core.database import Database
            from app.core.repositories import ConfigRepositorio
            db = Database().init()
            try:
                with db.Session() as s:
                    v = str(ConfigRepositorio(s).get("aparencia.animacoes")
                            or "ligadas")
            finally:
                db.engine.dispose()
            _cache_config["valor"] = (v != "reduzidas")
        except Exception:
            _cache_config["valor"] = True
    return _cache_config["valor"]


def recarregar_config() -> None:
    _cache_config.clear()


def transparencias_reduzidas() -> bool:
    """FASE 3 (passo 29): véus translúcidos desligáveis (máquina fraca).
    Mesmo cache/invalidação das animações."""
    if "transp" not in _cache_config:
        try:
            from app.core.database import Database
            from app.core.repositories import ConfigRepositorio
            db = Database().init()
            try:
                with db.Session() as s:
                    v = str(ConfigRepositorio(s).get(
                        "aparencia.transparencias") or "normais")
            finally:
                db.engine.dispose()
            _cache_config["transp"] = (v == "reduzidas")
        except Exception:
            _cache_config["transp"] = False
    return _cache_config["transp"]


def _registrar(anim: QAbstractAnimation) -> None:
    _VIVAS.append(anim)

    def _fora(*_a) -> None:
        if anim in _VIVAS:
            _VIVAS.remove(anim)

    anim.finished.connect(_fora)
    # animação em loop morta JUNTO com o dono (deleteLater do skeleton)
    # nunca emite finished — o destroyed limpa o registro
    anim.destroyed.connect(_fora)

    # F13/B2 (a prova de ordem invertida do A6 desmontou uma LENDA da
    # casa): stop() NÃO emite finished — finished só sai no fim NATURAL.
    # Toda animação interrompida por stop() (o zoom de ajuste do canvas
    # trocado no meio, o hover) ficava em _VIVAS para sempre. O sinal
    # certo é stateChanged→Stopped, que cobre os dois desfechos.
    def _mudou_estado(novo, _velho=None) -> None:
        if novo == QAbstractAnimation.State.Stopped:
            _fora()

    anim.stateChanged.connect(_mudou_estado)
    # F13/B2 (a prova de ordem invertida do A6): animação FINITA que
    # congelar no meio (modal travando o laço, dono do widget sumindo sem
    # destroyed) se encerra SOZINHA logo depois do prazo dela — nada fica
    # "em voo" para sempre. Loop infinito (skeleton) fica de fora: morre
    # com o dono, via destroyed.
    dur = anim.totalDuration()
    if dur >= 0:
        from PySide6.QtCore import QTimer

        def _prazo() -> None:
            try:
                if anim not in _VIVAS:
                    return
                if anim.state() == QAbstractAnimation.State.Running:
                    anim.stop()          # emite finished → _fora
                else:
                    # parada SEM finished (stop() numa animação que já
                    # estava Stopped não emite nada — o caso do canvas
                    # que a prova invertida pegou): sai do registro direto
                    _fora()
            except RuntimeError:
                _fora()                  # C++ já morto: só limpa o registro

        QTimer.singleShot(dur + 500, _prazo)


def animacoes_ativas() -> int:
    """Quantas animações estão EM VOO agora (o teste do passo 92 usa)."""
    return len(_VIVAS)


registrar = _registrar               # nome público p/ os componentes da casa


def cascata(widgets, passo_ms: int = 60, ms: int = DURACAO_MS) -> None:
    """FASE 2 (passo 31): entrada em fade ESCALONADO — cada widget entra
    ``passo_ms`` depois do anterior (grade de cartões do Início).
    Reduzidas: todos aparecem na hora, zero timers. Janela de CAPTURA
    (WA_DontShowOnScreen) idem — o grab precisa do estado final (lei da
    Fase 1, a mesma do canvas e dos diálogos)."""
    if not animacoes_ligadas() or (
            widgets and widgets[0].window().testAttribute(
                Qt.WidgetAttribute.WA_DontShowOnScreen)):
        for w in widgets:
            w.show()
        return
    from PySide6.QtCore import QTimer
    for i, w in enumerate(widgets):
        w.hide()
        QTimer.singleShot(i * passo_ms, lambda ww=w: fade_in(ww, ms))


def fade_in(widget: QWidget, ms: int = DURACAO_MS) -> None:
    """Aparece em fade — reduzidas: mostra na hora, zero timer."""
    if not animacoes_ligadas():
        widget.setWindowOpacity(1.0)
        widget.show()
        return
    efeito = QGraphicsOpacityEffect(widget)
    widget.setGraphicsEffect(efeito)
    widget.show()
    anim = QPropertyAnimation(efeito, b"opacity", widget)
    anim.setDuration(ms)
    anim.setStartValue(0.0)
    anim.setEndValue(1.0)
    anim.setEasingCurve(CURVA)
    anim.finished.connect(lambda: widget.setGraphicsEffect(None))
    _registrar(anim)
    anim.start(QAbstractAnimation.DeletionPolicy.DeleteWhenStopped)


def slide_y(widget: QWidget, dy: int, ms: int = DURACAO_MS) -> None:
    """Desliza da posição atual+dy até a atual (entrada de toast etc.)."""
    destino = widget.pos()
    if not animacoes_ligadas():
        widget.move(destino)
        widget.show()
        return
    widget.move(destino + QPoint(0, dy))
    widget.show()
    anim = QPropertyAnimation(widget, b"pos", widget)
    anim.setDuration(ms)
    anim.setEndValue(destino)
    anim.setEasingCurve(CURVA)
    _registrar(anim)
    anim.start(QAbstractAnimation.DeletionPolicy.DeleteWhenStopped)


# =============================================================================
# Diálogos (passo 40): fundo escurecido em fade + scale-in 0.98→1.0 do corpo.
# Instalado como filtro GLOBAL pelos entrypoints (main.py / editor_app.main) —
# testes e o script de fotos nunca passam por lá, então ficam sem circo.
# =============================================================================

_veus: dict[int, QWidget] = {}       # id(diálogo) → véu vivo na janela-mãe


class _AnimadorDialogos(QObject):
    """Filtro de app: TODO QDialog nasce animado num lugar só (os 9 diálogos
    abrem por .exec() espalhado — caçá-los um a um seria repetição)."""

    def eventFilter(self, obj, ev):  # noqa: N802 (Qt)
        if isinstance(obj, QDialog):
            if ev.type() == QEvent.Type.Show:
                _entrada_dialogo(obj)
            elif ev.type() == QEvent.Type.Hide:
                _remover_veu(obj)
        return False                 # nunca consome o evento


class _HoverSuave(QObject):
    """Filtro de app (passo 41): o fundo de hover dos botões é um véu
    translúcido que entra/sai em fade de 120 ms — o QSS parou de saltar
    o background (só a borda responde seca, feedback imediato)."""

    def eventFilter(self, obj, ev):  # noqa: N802 (Qt)
        from PySide6.QtWidgets import QPushButton, QToolButton
        if isinstance(obj, (QPushButton, QToolButton)) and obj.isEnabled():
            if ev.type() == QEvent.Type.Enter:
                _hover_entrou(obj)
            elif ev.type() == QEvent.Type.Leave:
                _hover_saiu(obj)
        return False


_hovers: dict[int, QWidget] = {}     # id(botão) → véu de hover vivo


def _hover_entrou(botao: QWidget) -> None:
    if id(botao) in _hovers or transparencias_reduzidas():   # F3 passo 29
        return
    from app.qt.design import tokens as t
    cor = (t.HOVER_VEU_FORTE if botao.property("tipo") == "primario"
           else t.HOVER_VEU)
    veu = QWidget(botao)
    veu.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
    veu.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
    veu.setStyleSheet(
        f"background: {cor}; border-radius: {t.RAIO_CONTROLE}px;")
    veu.setGeometry(botao.rect())
    _hovers[id(botao)] = veu
    botao.destroyed.connect(lambda _=None, b=id(botao): _hovers.pop(b, None))
    # efeito PERMANENTE do véu: entrada e saída animam o mesmo objeto
    # (mouse que passa voando não deixa dois efeitos brigando)
    efeito = QGraphicsOpacityEffect(veu)
    veu.setGraphicsEffect(efeito)
    veu.show()
    if not animacoes_ligadas():
        efeito.setOpacity(1.0)
        return
    efeito.setOpacity(0.0)
    anim = QPropertyAnimation(efeito, b"opacity", veu)
    anim.setDuration(DURACAO_HOVER_MS)
    anim.setStartValue(0.0)
    anim.setEndValue(1.0)
    anim.setEasingCurve(CURVA)
    veu._anim = anim                 # p/ a saída interromper a entrada
    _registrar(anim)
    anim.start()


def _hover_saiu(botao: QWidget) -> None:
    veu = _hovers.pop(id(botao), None)
    if veu is None:
        return
    if not animacoes_ligadas():
        veu.hide()
        veu.deleteLater()
        return
    anterior = getattr(veu, "_anim", None)
    if anterior is not None:
        anterior.stop()              # sai de _VIVAS via stateChanged→Stopped
                                     # (F13/B2: stop() NÃO emite finished)
    efeito = veu.graphicsEffect()
    anim = QPropertyAnimation(efeito, b"opacity", veu)
    anim.setDuration(DURACAO_HOVER_MS)
    anim.setStartValue(efeito.opacity())
    anim.setEndValue(0.0)
    anim.setEasingCurve(CURVA)
    anim.finished.connect(veu.deleteLater)
    veu._anim = anim
    _registrar(anim)
    anim.start()


_animador: _AnimadorDialogos | None = None
_hover_global: _HoverSuave | None = None


def instalar_vida(app) -> None:
    """Chamada única no boot (passos 40-41); idempotente. Testes e scripts
    de foto NÃO chamam — a bancada fica determinística e sem circo."""
    global _animador, _hover_global
    if _animador is None:
        _animador = _AnimadorDialogos()
        app.installEventFilter(_animador)
    if _hover_global is None:
        _hover_global = _HoverSuave()
        app.installEventFilter(_hover_global)


class _VeuDialogo(QWidget):
    """F13/B2 (V-01..05, L-01): o véu escurecido atrás de um diálogo.

    - acompanha o RESIZE da janela-mãe (antes ficava do tamanho velho);
    - morre de verdade em ``morrer()`` (o destroyed do diálogo chama);
    - carrega o objectName "veuDialogo" para a varredura de órfãos."""

    def __init__(self, pai: QWidget) -> None:
        super().__init__(pai)
        self.setObjectName("veuDialogo")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        self.setGeometry(pai.rect())
        pai.installEventFilter(self)

    def eventFilter(self, obj, ev):  # noqa: N802 (Qt)
        if obj is self.parentWidget() and ev.type() == QEvent.Type.Resize:
            self.setGeometry(self.parentWidget().rect())
        return False

    def morrer(self) -> None:
        pai = self.parentWidget()
        if pai is not None:
            pai.removeEventFilter(self)
        self.hide()
        self.deleteLater()


def _matar_veu(chave: int) -> None:
    """Tira do registro E da tela — a linha do V-01 só tirava do dict e o
    véu ficava PARA SEMPRE na janela quando o Hide não passava pelo filtro
    (a tela escura permanente do L-01)."""
    veu = _veus.pop(chave, None)
    if veu is not None:
        try:
            veu.morrer()
        except RuntimeError:
            pass                     # C++ já morto (a janela-mãe se foi)


def _entrada_dialogo(dlg: QDialog) -> None:
    if dlg.testAttribute(Qt.WidgetAttribute.WA_DontShowOnScreen):
        return                       # janela que nunca aparece não anima
    if not animacoes_ligadas() or dlg.property("_anim_entrou"):
        return
    dlg.setProperty("_anim_entrou", True)

    # véu escurecido sobre a janela-mãe (fica SOB o diálogo, que é top-level)
    pai = dlg.parentWidget().window() if dlg.parentWidget() else None
    if (pai is not None and pai.isVisible() and id(dlg) not in _veus
            and not transparencias_reduzidas()):     # F3 passo 29
        from app.qt.design import tokens as t
        veu = _VeuDialogo(pai)
        veu.setStyleSheet(f"background: {t.VEU_DIALOGO};")
        _veus[id(dlg)] = veu
        fade_in(veu, DURACAO_HOVER_MS)
        # F13/B2: o destroyed DESTRÓI o véu (não só o registro)
        dlg.destroyed.connect(lambda _=None, d=id(dlg): _matar_veu(d))

    # corpo: fade + leve scale-in (0.98 → 1.0) via windowOpacity + geometry
    fim = dlg.geometry()
    dx, dy = max(1, fim.width() // 100), max(1, fim.height() // 100)
    inicio = QRect(fim.x() + dx, fim.y() + dy,
                   fim.width() - 2 * dx, fim.height() - 2 * dy)
    dlg.setWindowOpacity(0.0)
    op = QPropertyAnimation(dlg, b"windowOpacity", dlg)
    op.setDuration(DURACAO_MS)
    op.setStartValue(0.0)
    op.setEndValue(1.0)
    op.setEasingCurve(CURVA)
    geo = QPropertyAnimation(dlg, b"geometry", dlg)
    geo.setDuration(DURACAO_MS)
    geo.setStartValue(inicio)
    geo.setEndValue(fim)
    geo.setEasingCurve(CURVA)
    for anim in (op, geo):
        _registrar(anim)
        anim.start(QAbstractAnimation.DeletionPolicy.DeleteWhenStopped)


def _remover_veu(dlg: QDialog) -> None:
    dlg.setProperty("_anim_entrou", False)   # reabrir anima de novo
    _matar_veu(id(dlg))


def varrer_veus_orfaos(janela: QWidget) -> int:
    """F13/B2/B2b (L-01/L-02): rede de segurança da TROCA DE TELA — véu de
    diálogo e foto de crossfade que ficaram na janela SEM registro vivo
    morrem aqui. Devolve quantos morreram (o teste confere o conteúdo)."""
    vivos = {id(v) for v in _veus.values()}
    vivos |= {id(v) for v in _veus_troca.values()}
    n = 0
    for nome in ("veuDialogo", "veuTrocaTela"):
        for w in janela.findChildren(QWidget, nome):
            if id(w) not in vivos:
                try:
                    w.hide()
                    w.deleteLater()
                except RuntimeError:
                    continue
                n += 1
    return n


_veus_troca: dict[int, QWidget] = {}     # container → foto da tela antiga


def crossfade(container, de: QWidget, para: QWidget,
              ms: int = DURACAO_MS) -> None:
    """Troca de tela num QStackedWidget SEM piscar: a tela ANTIGA vira uma
    FOTO estática que desvanece por cima da nova.

    O conserto do "desenquadrado": a versão anterior punha um
    ``QGraphicsOpacityEffect`` na PÁGINA VIVA — no Windows isso renderiza o
    widget num cache e a tela ficava recortada/mal pintada até um resize
    externo (sair/entrar da tela cheia). Efeito gráfico agora SÓ na foto
    (um QLabel morto) — a tela real pinta direto, sempre.

    Reduzidas: troca seca (instantânea), como sempre foi."""
    from PySide6.QtWidgets import QLabel

    indice = container.indexOf(para)
    if indice < 0:
        return
    if not animacoes_ligadas() or de is para or de is None:
        container.setCurrentIndex(indice)
        return
    # troca rápida em cima de troca: some com o véu anterior na hora
    antigo = _veus_troca.pop(id(container), None)
    if antigo is not None:
        antigo.hide()
        antigo.deleteLater()
    foto = de.grab()
    veu = QLabel(container)
    veu.setObjectName("veuTrocaTela")    # F13/B2b: a varredura o encontra
    veu.setPixmap(foto)
    veu.setGeometry(0, 0, container.width(), container.height())
    veu.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
    container.setCurrentIndex(indice)
    veu.show()
    veu.raise_()
    _veus_troca[id(container)] = veu
    efeito = QGraphicsOpacityEffect(veu)
    veu.setGraphicsEffect(efeito)
    anim = QPropertyAnimation(efeito, b"opacity", veu)
    anim.setDuration(ms)
    anim.setStartValue(1.0)
    anim.setEndValue(0.0)
    anim.setEasingCurve(CURVA)

    def _fim(cid=id(container)):
        ov = _veus_troca.pop(cid, None)
        if ov is not None:
            try:
                ov.hide()
                ov.deleteLater()
            except RuntimeError:
                pass                 # C++ já morto junto com o container

    anim.finished.connect(_fim)
    # F13/B2b (L-02): a animação pode morrer PELA METADE quando um modal
    # abre no meio da troca (o rascunho da Mesa abre no showEvent, DENTRO
    # do setCurrentIndex acima) — a foto da tela velha ficava semitransparente
    # por cima para sempre. O prazo garante: passado o tempo dela + folga,
    # a foto morre, animada ou não. _fim é idempotente.
    from PySide6.QtCore import QTimer
    QTimer.singleShot(ms + 400, _fim)
    _registrar(anim)
    anim.start(QAbstractAnimation.DeletionPolicy.DeleteWhenStopped)

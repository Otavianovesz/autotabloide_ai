"""
Componentes do sistema de design
================================
Blocos reutilizáveis: cartão com cabeçalho (Painel), wordmark da marca.
Todos estilizados pelo tema via propriedades ``papel="..."``.
"""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QLinearGradient, QPainter, QPixmap
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QStyle,
    QStyledItemDelegate,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from app.qt.design import tokens as t
from app.qt.design.icones import icone


class SombraHoverDelegate(QStyledItemDelegate):
    """FASE 1 (passo 42): elevação de card em ITEM DE LISTA.

    As prateleiras do Início e a biblioteca do Ateliê são QListWidget em
    IconMode (RG-10) — item de lista não aceita QGraphicsDropShadowEffect,
    então a sombra que "sobe no hover" é pintada: anéis translúcidos de
    ``t.SOMBRA`` sob o retângulo (no escuro o token vira halo claro, o
    mesmo padrão da página no canvas)."""

    def paint(self, painter, option, index):  # noqa: N802 (Qt)
        if option.state & QStyle.StateFlag.State_MouseOver:
            r = option.rect.adjusted(4, 4, -4, -2)
            painter.save()
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            painter.setPen(Qt.PenStyle.NoPen)
            base = QColor(t.SOMBRA)
            for anel, alpha in enumerate((16, 11, 6), start=1):
                base.setAlpha(alpha)
                painter.setBrush(base)
                painter.drawRoundedRect(
                    r.adjusted(-anel, -anel, anel, anel + 2),
                    t.RAIO_CARTAO + anel, t.RAIO_CARTAO + anel)
            painter.restore()
        super().paint(painter, option, index)


class Skeleton(QWidget):
    """FASE 1 (passo 43): retângulos pulsantes enquanto a lista real carrega.

    O pulso é uma animação em loop (0.45 ↔ 1.0 de opacidade) que roda SÓ
    enquanto o widget está visível (hide para o timer — nada de CPU à toa).
    Com "Reduzir animações" fica estático, sem timer nenhum."""

    def __init__(self, linhas: int = 3, altura_linha: int = 72, parent=None):
        super().__init__(parent)
        self._linhas = linhas
        self._altura = altura_linha
        self._pulso = 1.0
        self._anim = None
        self.setMinimumHeight(linhas * (altura_linha + t.ESP_2))

    def showEvent(self, ev) -> None:  # noqa: N802 (Qt)
        super().showEvent(ev)
        from app.qt.design.animacoes import CURVA, animacoes_ligadas, registrar
        if not animacoes_ligadas() or self._anim is not None:
            return
        from PySide6.QtCore import QVariantAnimation
        anim = QVariantAnimation(self)
        anim.setDuration(900)
        anim.setStartValue(0.45)
        anim.setKeyValueAt(0.5, 1.0)
        anim.setEndValue(0.45)
        anim.setLoopCount(-1)
        anim.setEasingCurve(CURVA)
        anim.valueChanged.connect(self._pulsar)
        self._anim = anim
        registrar(anim)
        anim.start()

    def hideEvent(self, ev) -> None:  # noqa: N802 (Qt)
        super().hideEvent(ev)
        if self._anim is not None:
            self._anim.stop()        # stop → finished → sai de _VIVAS
            self._anim = None

    def _pulsar(self, valor) -> None:
        self._pulso = float(valor)
        self.update()

    def paintEvent(self, ev) -> None:  # noqa: N802 (Qt)
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setPen(Qt.PenStyle.NoPen)
        cor = QColor(t.SUPERFICIE_3)
        cor.setAlphaF(cor.alphaF() * self._pulso)
        p.setBrush(cor)
        y = 0
        for _ in range(self._linhas):
            p.drawRoundedRect(0, y, self.width(), self._altura,
                              t.RAIO_CARTAO, t.RAIO_CARTAO)
            y += self._altura + t.ESP_2
        p.end()


class SecaoRecolhivel(QWidget):
    """FASE 1 (passo 45): seção com cabeçalho clicável (chevron) cujo corpo
    recolhe/expande ANIMANDO a altura (180 ms, OutCubic; "Reduzir
    animações" = seco). Substitui QGroupBox nos painéis de propriedades."""

    def __init__(self, titulo: str, corpo: QWidget, parent=None,
                 *, aberta: bool = True):
        super().__init__(parent)
        self._corpo = corpo
        self._cab = QToolButton()
        self._cab.setText(f" {titulo.upper()}")
        self._cab.setCheckable(True)
        self._cab.setChecked(aberta)
        self._cab.setArrowType(Qt.ArrowType.DownArrow if aberta
                               else Qt.ArrowType.RightArrow)
        self._cab.setToolButtonStyle(
            Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        self._cab.setProperty("papel", "secaoCabecalho")
        self._cab.toggled.connect(self._alternar)
        vl = QVBoxLayout(self)
        vl.setContentsMargins(0, 0, 0, 0)
        vl.setSpacing(0)
        vl.addWidget(self._cab)
        vl.addWidget(corpo)
        if not aberta:
            corpo.setMaximumHeight(0)

    def _alternar(self, aberta: bool) -> None:
        self._cab.setArrowType(Qt.ArrowType.DownArrow if aberta
                               else Qt.ArrowType.RightArrow)
        corpo = self._corpo
        alvo = corpo.sizeHint().height() if aberta else 0
        from app.qt.design.animacoes import (
            CURVA, DURACAO_MS, animacoes_ligadas, registrar)
        anterior = getattr(self, "_anim", None)
        if anterior is not None:
            anterior.stop()
        if not animacoes_ligadas() or not self.isVisible():
            corpo.setMaximumHeight(16777215 if aberta else 0)
            return
        from PySide6.QtCore import QPropertyAnimation
        atual = corpo.height()
        anim = QPropertyAnimation(corpo, b"maximumHeight", self)
        anim.setDuration(DURACAO_MS)
        anim.setStartValue(atual)
        anim.setEndValue(alvo)
        anim.setEasingCurve(CURVA)
        if aberta:                       # no fim, volta a crescer livre
            anim.finished.connect(
                lambda c=corpo: c.setMaximumHeight(16777215))
        self._anim = anim
        registrar(anim)
        anim.start()


def confirmar_destrutivo(pai, titulo: str, texto: str, verbo: str) -> bool:
    """FASE 1 (passo 78): confirmação destrutiva SEMPRE com o VERBO no
    botão ("Excluir 3 produtos", "Limpar estante") — nunca "OK"/"Yes".

    Devolve True só se o botão do verbo foi clicado."""
    from PySide6.QtWidgets import QMessageBox
    caixa = QMessageBox(pai)
    caixa.setWindowTitle(titulo)
    caixa.setText(texto)
    caixa.setIcon(QMessageBox.Icon.Warning)
    botao = caixa.addButton(verbo, QMessageBox.ButtonRole.DestructiveRole)
    caixa.addButton("Cancelar", QMessageBox.ButtonRole.RejectRole)
    caixa.exec()
    return caixa.clickedButton() is botao


def splitter_com_memoria(chave: str, esquerda: QWidget, direita: QWidget,
                         *, indice_lateral: int, minimo_lateral: int = 300):
    """FASE 1 (passo 59): painel lateral redimensionável POR SPLITTER, com
    a posição lembrada na Config (``ui.splitter.<chave>``).

    ``indice_lateral`` diz qual dos dois é o painel (0=esquerda, 1=direita);
    o outro é o conteúdo principal, que estica. Mínimo de 300 px no lateral
    (nunca mais "lista de Camadas espremida" — defeito D4)."""
    from PySide6.QtCore import QTimer
    from PySide6.QtWidgets import QSplitter

    sp = QSplitter(Qt.Orientation.Horizontal)
    sp.addWidget(esquerda)
    sp.addWidget(direita)
    lateral = sp.widget(indice_lateral)
    lateral.setMinimumWidth(minimo_lateral)
    sp.setCollapsible(0, False)
    sp.setCollapsible(1, False)
    sp.setStretchFactor(indice_lateral, 0)
    sp.setStretchFactor(1 - indice_lateral, 1)

    def _config():
        from app.core.database import Database
        from app.core.repositories import ConfigRepositorio
        return Database, ConfigRepositorio

    try:                                    # memória: restaura se houver
        Database, ConfigRepositorio = _config()
        db = Database().init()
        try:
            with db.Session() as s:
                guardado = ConfigRepositorio(s).get(f"ui.splitter.{chave}")
        finally:
            db.engine.dispose()
        if (isinstance(guardado, list) and len(guardado) == 2
                and all(isinstance(v, int) and v > 0 for v in guardado)):
            sp.setSizes(guardado)
    except Exception:
        pass                                # default são: sem memória, segue

    gravador = QTimer(sp)                   # debounce: grava 500 ms após soltar
    gravador.setSingleShot(True)
    gravador.setInterval(500)

    def _gravar() -> None:
        try:
            Database, ConfigRepositorio = _config()
            db = Database().init()
            try:
                with db.Session() as s:
                    ConfigRepositorio(s).set(f"ui.splitter.{chave}",
                                             list(sp.sizes()))
                    s.commit()
            finally:
                db.engine.dispose()
        except Exception:
            pass

    gravador.timeout.connect(_gravar)
    sp.splitterMoved.connect(lambda *_: gravador.start())
    return sp


class Painel(QWidget):
    """Cartão com cabeçalho (ícone + título) e um widget de corpo.

    O padrão dos painéis laterais (Camadas, Propriedades) e das telas futuras.
    """

    def __init__(self, titulo: str, nome_icone: str, corpo: QWidget, parent=None,
                 *, acao: QWidget | None = None):
        super().__init__(parent)
        self.setProperty("papel", "cartao")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

        cabecalho = QWidget()
        cabecalho.setProperty("papel", "cartaoCabecalho")
        cabecalho.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        hl = QHBoxLayout(cabecalho)
        hl.setContentsMargins(t.ESP_3, t.ESP_2, t.ESP_3, t.ESP_2)
        hl.setSpacing(t.ESP_2)
        ic = QLabel()
        ic.setPixmap(icone(nome_icone, cor=t.TEXTO_2, tamanho=15).pixmap(15, 15))
        self._rotulo = QLabel(titulo.upper())
        self._rotulo.setProperty("papel", "secao")
        hl.addWidget(ic)
        hl.addWidget(self._rotulo, 1)
        if acao is not None:             # RG-07: ação no cabeçalho (ex.: limpar)
            hl.addWidget(acao)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)
        lay.addWidget(cabecalho)
        corpo_caixa = QWidget()
        cl = QVBoxLayout(corpo_caixa)
        cl.setContentsMargins(t.ESP_2, t.ESP_2, t.ESP_2, t.ESP_2)
        cl.addWidget(corpo)
        lay.addWidget(corpo_caixa, 1)

    def set_titulo(self, titulo: str) -> None:
        """Atualiza o título (ex.: contagem viva — 'Itens da oferta (12)')."""
        self._rotulo.setText(titulo.upper())


class EstadoVazio(QWidget):
    """Estado vazio com craft: ícone grande, título, dica e ação opcional.

    Usado em "nada selecionado", "nenhum layout", telas ainda não construídas…
    """

    def __init__(self, nome_icone: str, titulo: str, legenda: str = "",
                 acao: QWidget | None = None, parent=None):
        super().__init__(parent)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(t.ESP_4, t.ESP_5, t.ESP_4, t.ESP_5)
        lay.setSpacing(t.ESP_2)
        lay.addStretch(1)
        ic = QLabel()
        ic.setPixmap(icone(nome_icone, cor=t.TEXTO_3, tamanho=40).pixmap(40, 40))
        ic.setAlignment(Qt.AlignmentFlag.AlignCenter)
        tit = QLabel(titulo)
        tit.setAlignment(Qt.AlignmentFlag.AlignCenter)
        tit.setStyleSheet(f"font-weight: 600; color: {t.TEXTO_2};")
        lay.addWidget(ic)
        lay.addWidget(tit)
        if legenda:
            leg = QLabel(legenda)
            leg.setAlignment(Qt.AlignmentFlag.AlignCenter)
            leg.setWordWrap(True)
            leg.setProperty("papel", "legenda")
            lay.addWidget(leg)
        if acao is not None:
            caixa = QHBoxLayout()
            caixa.addStretch(1)
            caixa.addWidget(acao)
            caixa.addStretch(1)
            lay.addSpacing(t.ESP_2)
            lay.addLayout(caixa)
        lay.addStretch(2)


class Wordmark(QWidget):
    """Marca do app: selo "A" em gradiente + "AutoTabloide AI"."""

    def __init__(self, parent=None):
        super().__init__(parent)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(t.ESP_2)
        selo = QLabel()
        selo.setPixmap(self._selo())
        nome = QLabel(
            f'<span style="font-weight:700">AutoTabloide</span> '
            f'<span style="color:{t.TEXTO_3}">AI</span>'
        )
        lay.addWidget(selo)
        lay.addWidget(nome)

    @staticmethod
    def _selo(tamanho: int = 22) -> QPixmap:
        pm = QPixmap(tamanho * 2, tamanho * 2)
        pm.fill(Qt.GlobalColor.transparent)
        p = QPainter(pm)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        grad = QLinearGradient(0, 0, tamanho * 2, tamanho * 2)
        grad.setColorAt(0, QColor(t.PRIMARIA))
        grad.setColorAt(1, QColor(t.PRIMARIA_ESCURA))
        p.setBrush(grad)
        p.setPen(Qt.PenStyle.NoPen)
        p.drawRoundedRect(0, 0, tamanho * 2, tamanho * 2, 12, 12)
        p.setPen(QColor(t.ACENTO_TEXTO))
        fonte = p.font()
        fonte.setBold(True)
        fonte.setPixelSize(int(tamanho * 1.25))
        p.setFont(fonte)
        p.drawText(pm.rect(), Qt.AlignmentFlag.AlignCenter, "A")
        p.end()
        pm.setDevicePixelRatio(2)
        return pm


def modo_compacto_botoes(lay, botao_mais, ids_sacrificaveis: set,
                         registro: dict, largura_util: int, esp: int) -> bool:
    """RG-53 — ESTÁGIO 2 (GATE 2.2 da ordem F11.5): quando nem colapsando os
    sacrificáveis no "···" a barra cabe, os botões FIXOS com ícone perdem o
    TEXTO (só ícone; o texto vira tooltip) — e voltam sozinhos quando o
    espaço sobra. Sem isto, o QHBoxLayout espremia os essenciais abaixo do
    próprio sizeHint (botão sem espaço pro texto — a reclamação do dono).

    ``registro`` (dict por tela) guarda {id(botao): (texto, delta_px,
    tooltip_original)} enquanto compacto. Devolve True se compactou agora.
    """
    from PySide6.QtWidgets import QPushButton

    soma = 0
    fixos: list[QPushButton] = []
    for i in range(lay.count()):
        w = lay.itemAt(i).widget()
        if w is None or w.isHidden():
            continue
        soma += w.sizeHint().width() + esp
        if (isinstance(w, QPushButton) and id(w) not in ids_sacrificaveis
                and not w.icon().isNull()
                and (w.text().strip() or id(w) in registro)):
            fixos.append(w)
    if soma > largura_util:
        compactou = False
        for w in fixos:
            if id(w) in registro:
                continue
            texto = w.text()
            antes = w.sizeHint().width()
            w.setText("")
            registro[id(w)] = (texto, antes - w.sizeHint().width(),
                               w.toolTip())
            if not w.toolTip():
                w.setToolTip(texto.strip())
            compactou = True
        return compactou
    # espaço de volta: restaura os textos quando eles CABEM de novo
    delta_total = sum(d for (_t, d, _tt) in registro.values())
    if registro and soma + delta_total <= largura_util:
        for w in fixos:
            if id(w) in registro:
                texto, _d, tooltip = registro.pop(id(w))
                w.setText(texto)
                w.setToolTip(tooltip)
    return False

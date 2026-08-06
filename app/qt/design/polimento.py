"""
Polimento global de controles (FASE 1, Bloco E)
===============================================
Políticas anti-corte aplicadas num lugar só, por filtro de aplicação:

- passo 52: todo QComboBox ganha ``minimumContentsLength`` (nunca vira um
  toco) e o POPUP abre com a largura do maior item (fim do "Qualidade
  máxima (len…" cortado) — clampado à borda da tela.

Instalado pelos entrypoints junto de ``instalar_vida`` — testes e scripts
de foto continuam com o Qt cru, determinístico.
"""

from __future__ import annotations

from PySide6.QtCore import QEvent, QObject
from PySide6.QtWidgets import QAbstractSpinBox, QComboBox, QDoubleSpinBox


class _PolidorGlobal(QObject):
    def eventFilter(self, obj, ev):  # noqa: N802 (Qt)
        tipo = ev.type()
        if tipo == QEvent.Type.Polish and isinstance(obj, QComboBox):
            obj.setMinimumContentsLength(10)
        elif tipo == QEvent.Type.Polish and isinstance(obj, QAbstractSpinBox):
            # passo 53: 4 dígitos + sufixo SEMPRE visíveis (nada de "12…")
            fm = obj.fontMetrics()
            texto = "8.888,88" if isinstance(obj, QDoubleSpinBox) else "8888"
            sufixo = getattr(obj, "suffix", lambda: "")()
            larg = fm.horizontalAdvance(texto + sufixo) + 44  # setas+padding
            obj.setMinimumWidth(max(obj.minimumWidth(), larg))
        elif (tipo == QEvent.Type.Show
              and type(obj).__name__ == "QComboBoxPrivateContainer"):
            combo = obj.parent()
            if isinstance(combo, QComboBox):
                vista = combo.view()
                folga = vista.frameWidth() * 2 + 28   # moldura + rolagem
                alvo = max(combo.width(),
                           vista.sizeHintForColumn(0) + folga)
                tela = obj.screen().availableGeometry()
                alvo = min(alvo, tela.right() - obj.x() - 4)
                if alvo > obj.width():
                    obj.resize(alvo, obj.height())
        return False


_polidor: _PolidorGlobal | None = None


def instalar_polimento(app) -> None:
    """Chamada única no boot; idempotente."""
    global _polidor
    if _polidor is None:
        _polidor = _PolidorGlobal()
        app.installEventFilter(_polidor)


# --- FASE 1 (passo 66 — R-024): Tab na ordem VISUAL -------------------------

def _varrer_layout(lay, saida: list) -> None:
    for i in range(lay.count()):
        item = lay.itemAt(i)
        if item.widget() is not None:
            _coletar_focaveis(item.widget(), saida)
        elif item.layout() is not None:
            _varrer_layout(item.layout(), saida)


def _coletar_focaveis(w, saida: list) -> None:
    from PySide6.QtCore import Qt
    from PySide6.QtWidgets import QScrollArea, QSplitter
    if w.focusPolicy() & Qt.FocusPolicy.TabFocus:
        saida.append(w)
    if isinstance(w, QScrollArea):
        if w.widget() is not None:
            _coletar_focaveis(w.widget(), saida)
        return
    if isinstance(w, QSplitter):
        for i in range(w.count()):
            _coletar_focaveis(w.widget(i), saida)
        return
    if w.layout() is not None:
        _varrer_layout(w.layout(), saida)


def ordenar_tab(raiz) -> None:
    """Encadeia o Tab pela ordem em que os controles APARECEM no layout —
    a ordem de criação (o default do Qt) mentia nos formulários em que o
    campo nasce antes do vizinho de cima. Chamar no FIM do __init__."""
    from PySide6.QtWidgets import QWidget
    focaveis: list = []
    _coletar_focaveis(raiz, focaveis)
    for a, b in zip(focaveis, focaveis[1:]):
        QWidget.setTabOrder(a, b)


def clampar_a_tela(dialogo, tela=None, margem: int = 24) -> None:
    """QUINTUSDECIMUS/L3: nenhum diálogo transborda a tela — a 1366×768
    (o notebook mais comum do mundo) a fileira de botões da conciliação
    ficava atrás da barra de tarefas e a importação NÃO FECHAVA.
    ``availableGeometry`` já desconta a barra; o conteúdo rolável
    (a tabela) encolhe por dentro e os botões ficam sempre visíveis.
    ``tela`` explícita só nos testes (QRect)."""
    if tela is None:
        s = dialogo.screen()
        if s is None:
            return
        tela = s.availableGeometry()
    larg = min(dialogo.width(), tela.width() - margem)
    alt = min(dialogo.height(), tela.height() - margem)
    if (larg, alt) != (dialogo.width(), dialogo.height()):
        dialogo.resize(larg, alt)
    x = tela.x() + max(0, (tela.width() - larg) // 2)
    y = tela.y() + max(0, (tela.height() - alt) // 2)
    if dialogo.y() + alt > tela.y() + tela.height() or dialogo.y() < tela.y():
        dialogo.move(x, y)

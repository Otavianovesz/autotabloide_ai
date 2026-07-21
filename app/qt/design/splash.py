"""
Splash do boot (FASE 1, passo 80)
=================================
Cartão leve com a marca + frase de carregamento, mostrado ANTES do shell
(pintar um pixmap custa ~ms — não atrasa o boot RG-01). Some em fade
quando a janela principal aparece.
"""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont, QPainter, QPixmap
from PySide6.QtWidgets import QSplashScreen

from app.qt.design import tokens as t


def _pixmap_splash(com_texto: bool = True) -> QPixmap:
    """``com_texto=False`` NÃO desenha texto — a 1ª pintura de texto do
    processo paga o banco de fontes do Windows (~1,5 s medidos); o splash
    nasce só com o logo (~1 ms) e o texto entra na repintura agendada."""
    from PySide6.QtCore import QPointF
    from PySide6.QtGui import QPen
    pm = QPixmap(420, 220)
    pm.fill(QColor(t.SUPERFICIE))
    p = QPainter(pm)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    # moldura sutil
    p.setPen(QColor(t.BORDA))
    p.setBrush(Qt.BrushStyle.NoBrush)
    p.drawRect(0, 0, 419, 219)
    # a LOGO da marca (o encarte com a etiqueta) — vetorial, sem fonte
    _ = QPointF, QPen                    # (mantidos p/ o bloco de texto)
    p.drawPixmap(40, 72, pixmap_logo(56))
    if com_texto:
        p.setPen(QColor(t.TEXTO))
        fonte_n = QFont(t.FONTE_UI[0])
        fonte_n.setPointSizeF(19)
        fonte_n.setWeight(QFont.Weight.DemiBold)
        p.setFont(fonte_n)
        p.drawText(112, 72, 280, 34, Qt.AlignmentFlag.AlignVCenter,
                   "AutoTabloide AI")
        p.setPen(QColor(t.TEXTO_3))
        fonte_l = QFont(t.FONTE_UI[0])
        fonte_l.setPointSizeF(9.5)
        p.setFont(fonte_l)
        p.drawText(112, 104, 280, 24, Qt.AlignmentFlag.AlignVCenter,
                   "Preparando o estúdio…")
    p.end()
    return pm


def pixmap_logo(lado: int, laranja: bool = False) -> QPixmap:
    """A LOGO do AutoTabloide (polimento): um encarte inclinado com a
    etiqueta de desconto — 100% vetorial (nenhuma fonte: nítido em 16 px e
    o boot não paga o banco de fontes). ``laranja`` = a variante B (Belo
    Brasil) da chave ``app.icone`` (F3, passo 56)."""
    from PySide6.QtCore import QPointF, QRectF
    from PySide6.QtGui import QLinearGradient, QPen

    pm = QPixmap(lado, lado)
    pm.fill(Qt.GlobalColor.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    # fundo: quadrado arredondado com gradiente diagonal
    g = QLinearGradient(0, 0, lado, lado)
    if laranja:
        g.setColorAt(0.0, QColor("#F59E0B"))
        g.setColorAt(1.0, QColor("#B45309"))
    else:
        g.setColorAt(0.0, QColor("#2E6BEA"))
        g.setColorAt(1.0, QColor("#16202E"))
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(g)
    p.drawRoundedRect(QRectF(0, 0, lado, lado), lado * 0.22, lado * 0.22)
    # a página do encarte, levemente inclinada
    p.save()
    p.translate(lado * 0.46, lado * 0.52)
    p.rotate(-8)
    pw, ph = lado * 0.46, lado * 0.60
    pagina = QRectF(-pw / 2, -ph / 2, pw, ph)
    p.setBrush(QColor(250, 250, 252))
    p.setPen(Qt.PenStyle.NoPen)
    p.drawRoundedRect(pagina, lado * 0.045, lado * 0.045)
    if lado >= 48:                       # detalhes só onde dá para ver
        # a "foto" do produto no topo da página
        p.setBrush(QColor(219, 228, 240))
        p.drawRoundedRect(
            QRectF(-pw / 2 + pw * 0.14, -ph / 2 + ph * 0.10,
                   pw * 0.72, ph * 0.40), lado * 0.02, lado * 0.02)
        # linhas de "texto"
        caneta = QPen(QColor(203, 213, 225), max(1.0, lado * 0.028))
        caneta.setCapStyle(Qt.PenCapStyle.RoundCap)
        p.setPen(caneta)
        for i in range(3):
            y = -ph / 2 + ph * 0.62 + i * ph * 0.13
            p.drawLine(QPointF(-pw / 2 + pw * 0.14, y),
                       QPointF(pw / 2 - pw * (0.14 if i < 2 else 0.40), y))
    p.restore()
    # a etiqueta de desconto (o coração do negócio) com "%" vetorial
    cx, cy, r = lado * 0.68, lado * 0.68, lado * 0.21
    p.setBrush(QColor("#16202E") if laranja else QColor("#DC2626"))
    p.setPen(QPen(QColor(255, 255, 255), max(1.0, lado * 0.028)))
    p.drawEllipse(QPointF(cx, cy), r, r)
    caneta = QPen(QColor(255, 255, 255), max(1.4, lado * 0.045))
    caneta.setCapStyle(Qt.PenCapStyle.RoundCap)
    p.setPen(caneta)
    p.drawLine(QPointF(cx - r * 0.38, cy + r * 0.38),
               QPointF(cx + r * 0.38, cy - r * 0.38))
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(QColor(255, 255, 255))
    d = r * 0.34
    p.drawEllipse(QPointF(cx - r * 0.40, cy - r * 0.40), d / 2, d / 2)
    p.drawEllipse(QPointF(cx + r * 0.40, cy + r * 0.40), d / 2, d / 2)
    p.end()
    return pm


def icone_aplicativo():
    """FASE 1 (passo 83): o ícone da janela/barra do Windows — a LOGO da
    marca em vários tamanhos (vetorial, ver ``pixmap_logo``).

    FASE 3 (passo 56): a chave ``app.icone`` escolhe entre a variante azul
    do AutoTabloide (padrão) e a laranja do Belo Brasil."""
    from PySide6.QtGui import QIcon
    laranja = False
    try:
        from app.core.database import Database
        from app.core.repositories import ConfigRepositorio
        db = Database().init()
        try:
            with db.Session() as s:
                escolha = str(ConfigRepositorio(s).get("app.icone") or "A")
        finally:
            db.engine.dispose()
        laranja = escolha.upper() == "B"
    except Exception:
        pass
    icone = QIcon()
    for lado in (16, 32, 48, 64, 128, 256):
        icone.addPixmap(pixmap_logo(lado, laranja=laranja))
    return icone


def mostrar_splash() -> QSplashScreen:
    """SÓ o logo, de propósito: desenhar TEXTO aqui custaria ~1,5 s (a 1ª
    pintura de texto do processo carrega o banco de fontes do Windows —
    medido) e o splash vive menos que isso. A frase de carregamento é a
    dica do rodapé do shell ("Preparando as demais telas…", RG-01)."""
    splash = QSplashScreen(_pixmap_splash(com_texto=False))
    splash.show()
    return splash


def fechar_splash(splash: QSplashScreen, janela) -> None:
    """Fade de saída (180 ms; 'Reduzir animações' fecha seco)."""
    from app.qt.design.animacoes import CURVA, DURACAO_MS, animacoes_ligadas
    if not animacoes_ligadas():
        splash.finish(janela)
        return
    from PySide6.QtCore import QPropertyAnimation
    anim = QPropertyAnimation(splash, b"windowOpacity", splash)
    anim.setDuration(DURACAO_MS)
    anim.setStartValue(1.0)
    anim.setEndValue(0.0)
    anim.setEasingCurve(CURVA)
    anim.finished.connect(lambda: splash.finish(janela))
    splash._anim = anim                  # segura a referência até o fim
    anim.start()

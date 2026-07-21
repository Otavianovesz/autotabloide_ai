"""
Boas-vindas da PRIMEIRA execução (FASE 1, passo 81)
===================================================
Um cartão de saudação com 3 caminhos — Importar oferta · Criar layout ·
Conhecer o Almoxarifado — cada um navega direto para a tela certa.
Aparece UMA vez (Config ``boasvindas.mostrada``); falha de banco nunca
bloqueia o app (conforto, não requisito — o padrão do tutorial RG-17).
"""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.qt.design import tokens as t
from app.qt.design.icones import icone

_CAMINHOS = [
    ("abrir", "Importar oferta",
     "Foto do WhatsApp ou tabela — o app\nconcilia e monta o tabloide.",
     "mesa"),
    ("camadas", "Criar layout",
     "Importe a sua arte do Illustrator\ne marque a grade uma vez.",
     "atelie"),
    ("caixa", "Conhecer o Almoxarifado",
     "O catálogo dos produtos: fotos,\npreços e o semáforo de qualidade.",
     "almoxarifado"),
]


def _ja_mostrada() -> bool:
    try:
        from app.core.database import Database
        from app.core.repositories import ConfigRepositorio
        db = Database().init()
        try:
            with db.Session() as s:
                return bool(ConfigRepositorio(s).get("boasvindas.mostrada"))
        finally:
            db.engine.dispose()
    except Exception:
        return True                      # sem banco: não incomoda


def _marcar_mostrada() -> None:
    try:
        from app.core.database import Database
        from app.core.repositories import ConfigRepositorio
        db = Database().init()
        try:
            with db.Session() as s:
                ConfigRepositorio(s).set("boasvindas.mostrada", True)
                s.commit()
        finally:
            db.engine.dispose()
    except Exception:
        pass


def cartao_caminho(nome_ic: str, rotulo: str, texto: str, ao_clicar) -> QWidget:
    """FASE 2 (passo 25): o cartão-caminho REUTILIZÁVEL — usado no diálogo
    de boas-vindas e no estado vazio do Início novo."""
    from PySide6.QtWidgets import QFrame
    caixa = QFrame()
    caixa.setProperty("papel", "cartao")
    caixa.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
    caixa.setMinimumSize(190, 150)
    caixa.setCursor(Qt.CursorShape.PointingHandCursor)
    caixa.mousePressEvent = lambda _ev: ao_clicar()
    vl = QVBoxLayout(caixa)
    vl.setContentsMargins(t.ESP_3, t.ESP_3, t.ESP_3, t.ESP_3)
    vl.setSpacing(t.ESP_2)
    ic = QLabel()
    ic.setPixmap(icone(nome_ic, cor=t.PRIMARIA, tamanho=28).pixmap(28, 28))
    ic.setAlignment(Qt.AlignmentFlag.AlignCenter)
    rot = QLabel(rotulo)
    rot.setAlignment(Qt.AlignmentFlag.AlignCenter)
    rot.setStyleSheet(f"font-weight: 600; color: {t.TEXTO};")
    leg = QLabel(texto)
    leg.setAlignment(Qt.AlignmentFlag.AlignCenter)
    leg.setProperty("papel", "legenda")
    vl.addWidget(ic)
    vl.addWidget(rot)
    vl.addWidget(leg)
    vl.addStretch(1)
    return caixa


class BoasVindasDialog(QDialog):
    """Saudação com 3 cartões-caminho; escolher um navega e fecha."""

    def __init__(self, shell):
        super().__init__(shell)
        self._shell = shell
        self.setWindowTitle("Bem-vindo")
        titulo = QLabel("Bem-vindo ao AutoTabloide AI")
        titulo.setProperty("papel", "titulo")
        sub = QLabel("Por onde você quer começar?")
        sub.setProperty("papel", "legenda")

        cartoes = QHBoxLayout()
        cartoes.setSpacing(t.ESP_3)
        for nome_ic, rotulo, texto, destino in _CAMINHOS:
            cartoes.addWidget(self._cartao(nome_ic, rotulo, texto, destino))

        depois = QPushButton("Explorar por conta própria")
        depois.setProperty("tipo", "fantasma")
        depois.clicked.connect(self.reject)
        rodape = QHBoxLayout()
        rodape.addStretch(1)
        rodape.addWidget(depois)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(t.ESP_5, t.ESP_4, t.ESP_5, t.ESP_4)
        lay.setSpacing(t.ESP_3)
        lay.addWidget(titulo)
        lay.addWidget(sub)
        lay.addLayout(cartoes)
        lay.addLayout(rodape)

    def _cartao(self, nome_ic: str, rotulo: str, texto: str,
                destino: str) -> QWidget:
        # QFrame clicável (QPushButton-container esconde o conteúdo e o
        # min-height do QSS de botões achataria o cartão)
        from PySide6.QtWidgets import QFrame
        caixa = QFrame()
        caixa.setProperty("papel", "cartao")
        caixa.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        caixa.setMinimumSize(190, 150)
        caixa.setCursor(Qt.CursorShape.PointingHandCursor)
        caixa.mousePressEvent = lambda _ev, d=destino: self._ir(d)
        vl = QVBoxLayout(caixa)
        vl.setContentsMargins(t.ESP_3, t.ESP_3, t.ESP_3, t.ESP_3)
        vl.setSpacing(t.ESP_2)
        ic = QLabel()
        ic.setPixmap(icone(nome_ic, cor=t.PRIMARIA, tamanho=28).pixmap(28, 28))
        ic.setAlignment(Qt.AlignmentFlag.AlignCenter)
        rot = QLabel(rotulo)
        rot.setAlignment(Qt.AlignmentFlag.AlignCenter)
        rot.setStyleSheet(f"font-weight: 600; color: {t.TEXTO};")
        leg = QLabel(texto)
        leg.setAlignment(Qt.AlignmentFlag.AlignCenter)
        leg.setProperty("papel", "legenda")
        vl.addWidget(ic)
        vl.addWidget(rot)
        vl.addWidget(leg)
        vl.addStretch(1)
        return caixa

    def _ir(self, destino: str) -> None:
        if hasattr(self._shell, "ir_para"):
            self._shell.ir_para(destino)
        self.accept()


def mostrar_se_primeira_execucao(shell) -> None:
    """Chamado no fim do boot (telas prontas); mostra e marca UMA vez."""
    if _ja_mostrada():
        return
    _marcar_mostrada()
    dlg = BoasVindasDialog(shell)
    dlg.open()                           # não-modal ao loop: boot não trava

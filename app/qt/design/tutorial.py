"""
Microtutorial de primeiro uso por tela (RG-17)
==============================================
Na PRIMEIRA visita a cada tela, um cartão curto explica o fluxo dela ("o
tutorial tá bem ruimzinho" — auditoria do dono). "Entendi" fecha e a tela
nunca mais incomoda (persistido na Config `tutorial.vistos`). Falha de
banco nunca atrapalha a navegação — tutorial é conforto, não requisito.
"""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QVBoxLayout

from app.qt.design import tokens as t

TEXTOS: dict[str, tuple[str, str]] = {
    "mesa": ("A Mesa monta o tabloide",
             "1. Importar tabela/foto (OCR) ou “Do banco”\n"
             "2. Conciliação com o semáforo 🟢🟡🔴\n"
             "3. Auto-preencher a grade · 4. Exportar (Ctrl+E)\n"
             "Dica: roda rola · Alt+roda dá zoom · Ctrl+0 enquadra ·\n"
             "Ctrl+S salva o projeto · janela estreita? o resto vive no “···”."),
    "atelie": ("O Ateliê guarda os layouts",
               "Duplo-clique abre o layout na Mesa (tabloide) ou na "
               "Fábrica (cartaz).\nBotão direito edita, duplica, renomeia. "
               "“Novo layout” importa a sua arte do Illustrator."),
    "almoxarifado": ("O Almoxarifado é o catálogo",
                     "Clique num produto para editar no painel à direita.\n"
                     "Bolinhas: 🔴 sem imagem · 🟡 incompleto · 🟢 completo.\n"
                     "Botão direito: trocar imagem, histórico, excluir."),
    "fabrica": ("A Fábrica faz cartazes de gôndola",
                "Cada item vira UMA página no tamanho exato.\n"
                "Preencha descrição + preço “de” + “por” — incompletos "
                "ficam fora do PDF (marcados ⚠)."),
}


def _vistos() -> set[str]:
    try:
        from app.core.database import Database
        from app.core.repositories import ConfigRepositorio
        db = Database().init()
        try:
            with db.Session() as s:
                return set(ConfigRepositorio(s).get("tutorial.vistos") or [])
        finally:
            db.engine.dispose()
    except Exception:
        return set()


def _marcar_visto(chave: str) -> None:
    try:
        from app.core.database import Database
        from app.core.repositories import ConfigRepositorio
        db = Database().init()
        try:
            with db.Session() as s:
                repo = ConfigRepositorio(s)
                vistos = set(repo.get("tutorial.vistos") or [])
                vistos.add(chave)
                repo.set("tutorial.vistos", sorted(vistos))
                s.commit()
        finally:
            db.engine.dispose()
    except Exception:
        pass


class CartaoTutorial(QFrame):
    """Cartão flutuante no rodapé da janela, fechado pelo “Entendi”."""

    def __init__(self, shell, chave: str, titulo: str, texto: str):
        super().__init__(shell)
        self._chave = chave
        self.setObjectName("cartaoTutorial")
        self.setStyleSheet(
            f"#cartaoTutorial {{ background: {t.SUPERFICIE}; "
            f"border: 1px solid {t.BORDA_FORTE}; border-radius: 10px; }}")
        lbl_titulo = QLabel(titulo)
        lbl_titulo.setProperty("papel", "titulo")
        lbl_texto = QLabel(texto)
        lbl_texto.setWordWrap(True)
        botao = QPushButton("Entendi")
        botao.setProperty("tipo", "primario")
        botao.clicked.connect(self._fechar)
        linha = QHBoxLayout()
        linha.addStretch(1)
        linha.addWidget(botao)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(t.ESP_4, t.ESP_3, t.ESP_4, t.ESP_3)
        lay.addWidget(lbl_titulo)
        lay.addWidget(lbl_texto)
        lay.addLayout(linha)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.adjustSize()
        self._reposicionar()
        self.show()
        self.raise_()

    def _reposicionar(self) -> None:
        pai = self.parentWidget()
        if pai is not None:
            self.move((pai.width() - self.width()) // 2,
                      pai.height() - self.height() - 46)

    def _fechar(self) -> None:
        _marcar_visto(self._chave)
        self.deleteLater()


def mostrar_se_primeira_vez(shell, chave: str) -> None:
    """Chamado pelo Shell na troca de tela — mostra o cartão UMA vez."""
    par = TEXTOS.get(chave)
    if par is None or not shell.isVisible() or chave in _vistos():
        return                       # janela invisível: nada a ensinar
    if getattr(shell, "_tutorial_aberto", None) is not None:
        try:
            shell._tutorial_aberto.deleteLater()   # troca rápida de tela
        except RuntimeError:
            pass
    shell._tutorial_aberto = CartaoTutorial(shell, chave, par[0], par[1])

"""
Preview do sistema de design (missão de design, passo 1)
========================================================
Gera dois screenshots do editor com o caso real do Belo Brasil:

- ``saida_design/antes.png``  — o editor como está hoje.
- ``saida_design/depois.png`` — o editor com o sistema de design aplicado
  (tema + barra com ícones + painéis em cartões), SEM tocar nos arquivos
  atuais — a montagem tematizada vive só aqui até o visual ser aprovado.

Rodar (sem abrir janela — usa WA_DontShowOnScreen; a plataforma offscreen do
Qt no Windows não carrega as fontes do sistema e o texto sai em quadrados)::

    python -m app.scripts.preview_design
"""

from __future__ import annotations

import tempfile
from decimal import Decimal
from pathlib import Path

SAIDA = Path("saida_design")


def _caso_real():
    """Layout + dados do gate de fidelidade (Belo Brasil, célula-mestre)."""
    from app.rendering.compositor import DadosProduto
    from app.rendering.model import layout_de_arte
    from app.scripts.cartaz_exemplo import gerar_imagem_produto_sintetica
    from app.scripts.gate_fidelidade import ARTE, DPI, celula_superior_esquerda

    produto = gerar_imagem_produto_sintetica(
        Path(tempfile.gettempdir()) / "atb_produto_exemplo.png")
    layout = layout_de_arte(ARTE, dpi=DPI)
    layout.paginas[0].slots[0].regioes = celula_superior_esquerda(DPI)
    dados = DadosProduto(
        "Abóbora Paulista Listrada", unidade="100g", preco_por=Decimal("0.19"),
        imagem_path=str(produto), texto_legal="Ofertas válidas até 26/05",
    )
    return layout, dados, ARTE


def _screenshot(janela, canvas, arquivo: Path) -> None:
    from PySide6.QtCore import Qt
    from PySide6.QtWidgets import QApplication

    janela.setAttribute(Qt.WidgetAttribute.WA_DontShowOnScreen, True)
    janela.resize(1440, 900)
    janela.show()                       # realiza o layout, sem aparecer na tela
    QApplication.processEvents()
    canvas.ajustar()                    # agora a view tem o tamanho final
    QApplication.processEvents()
    arquivo.parent.mkdir(parents=True, exist_ok=True)
    janela.grab().save(str(arquivo))
    janela.close()


def _antes(layout, dados, arte) -> None:
    from PySide6.QtWidgets import QMainWindow

    from app.qt.editor import Editor

    editor = Editor()
    editor.carregar(layout, dados, fundo_path=arte)
    janela = QMainWindow()
    janela.setWindowTitle("AutoTabloide AI — Editor (antes)")
    janela.setCentralWidget(editor)
    _screenshot(janela, editor.area.canvas, SAIDA / "antes.png")


def _depois(layout, dados, arte) -> None:
    """Montagem tematizada: mesmo Editor, casca nova (barra + cartões + status)."""
    from PySide6.QtGui import QColor
    from PySide6.QtWidgets import (
        QHBoxLayout, QLabel, QMainWindow, QStatusBar, QVBoxLayout, QWidget,
    )

    from app.qt.design import tokens as t
    from app.qt.design.barra_editor import BarraEditor
    from app.qt.design.componentes import Painel
    from app.qt.editor import Editor

    editor = Editor()
    editor.setStyleSheet("")            # o QSS local antigo sai; o tema global manda
    editor.carregar(layout, dados, fundo_path=arte)
    editor.barra.hide()                 # a barra antiga dá lugar à do design

    editor.area.canvas.setBackgroundBrush(QColor(t.CANVAS_FUNDO))

    # os títulos internos antigos saem — o cabeçalho do cartão já os traz
    for painel in (editor.camadas, editor.propriedades):
        rotulo = painel.layout().itemAt(0).widget()
        if isinstance(rotulo, QLabel):
            rotulo.hide()

    # sidebar: painéis em cartões com cabeçalho
    lateral = QWidget()
    lateral.setObjectName("lateral")
    coluna = QVBoxLayout(lateral)
    coluna.setContentsMargins(t.ESP_3, t.ESP_3, t.ESP_3, t.ESP_3)
    coluna.setSpacing(t.ESP_3)
    coluna.addWidget(Painel("Camadas", "camadas", editor.camadas), 2)
    coluna.addWidget(Painel("Propriedades", "propriedades", editor.propriedades), 3)
    lateral.setFixedWidth(300)

    corpo = QWidget()
    hl = QHBoxLayout(corpo)
    hl.setContentsMargins(0, 0, 0, 0)
    hl.setSpacing(0)
    hl.addWidget(editor.area, 1)
    hl.addWidget(lateral)

    raiz = QWidget()
    vl = QVBoxLayout(raiz)
    vl.setContentsMargins(0, 0, 0, 0)
    vl.setSpacing(0)
    vl.addWidget(BarraEditor(editor))
    vl.addWidget(corpo, 1)

    janela = QMainWindow()
    janela.setWindowTitle("AutoTabloide AI — Editor")
    janela.setCentralWidget(raiz)
    status = QStatusBar()
    status.addWidget(QLabel("  Dica: segure espaço e arraste para navegar"))
    direita = QLabel("Layout: Belo Brasil 1080×1300  ·  Zoom: ajustado  ")
    status.addPermanentWidget(direita)
    janela.setStatusBar(status)
    _screenshot(janela, editor.area.canvas, SAIDA / "depois.png")


def main() -> None:
    from PySide6.QtWidgets import QApplication

    from app.qt.design.tema import aplicar_tema

    app = QApplication.instance() or QApplication([])

    layout, dados, arte = _caso_real()
    _antes(layout, dados, arte)

    aplicar_tema(app)                   # o tema entra só para o "depois"
    layout2, dados2, arte2 = _caso_real()
    _depois(layout2, dados2, arte2)

    print(f"Screenshots em {SAIDA.resolve()}: antes.png / depois.png")


if __name__ == "__main__":
    main()

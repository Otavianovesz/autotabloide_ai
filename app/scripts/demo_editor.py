"""
Demo F5.2: editor com camadas interativas. Seleciona a região do NOME e a move,
depois captura o editor (offscreen) mostrando a alça selecionada + o preview recomposto.

Uso::

    python -m app.scripts.demo_editor [saida.png]
"""

from __future__ import annotations

import os
import sys
from decimal import Decimal
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication  # noqa: E402

from app.qt.editor import Editor  # noqa: E402
from app.rendering.compositor import DadosProduto  # noqa: E402
from app.rendering.model import TipoRegiao  # noqa: E402
from app.scripts.cartaz_exemplo import (  # noqa: E402
    gerar_arte_sintetica,
    gerar_imagem_produto_sintetica,
    layout_cartaz,
)


def main(saida: str) -> None:
    p = Path(saida)
    p.parent.mkdir(parents=True, exist_ok=True)
    app = QApplication.instance() or QApplication(sys.argv)

    fundo = gerar_arte_sintetica(p.parent / "fundo.png", 100, 150, 200)
    prod = gerar_imagem_produto_sintetica(p.parent / "prod.png")
    layout = layout_cartaz(100, 150, 200, str(fundo))
    dados = DadosProduto(
        "Refrigerante Kitubaina", unidade="1,5L",
        preco_por=Decimal("5.50"), preco_de=Decimal("6.90"), imagem_path=str(prod),
    )

    ed = Editor()
    ed.resize(900, 900)
    ed.carregar(layout, dados, fundo_path=str(fundo))
    ed.show()
    app.processEvents()
    ed.area.canvas.ajustar()
    app.processEvents()

    # Seleciona o NOME e o move 14mm para cima (simula arrastar + soltar).
    canvas = ed.canvas
    nome = next(it for it in canvas._itens if it.regiao.tipo == TipoRegiao.NOME)
    nome.setPos(nome.x(), nome.y() - canvas.mm_para_cena(0, 14)[1])
    canvas._commit_regiao(nome)
    nome.setSelected(True)
    app.processEvents()

    ed.grab().save(str(p))
    print(f"Editor salvo em {p}  (NOME movido e selecionado)")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "saida_editor/editor.png")

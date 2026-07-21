"""
Demo F5.1: monta o canvas do editor com um cartaz e captura para PNG (offscreen).

Uso::

    python -m app.scripts.demo_canvas [saida.png]
"""

from __future__ import annotations

import os
import sys
from decimal import Decimal
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication  # noqa: E402

from app.qt.canvas import EditorCanvas  # noqa: E402
from app.rendering.compositor import DadosProduto  # noqa: E402
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

    ec = EditorCanvas()
    ec.resize(680, 900)
    ec.carregar(layout, dados, fundo_path=str(fundo))
    ec.show()
    app.processEvents()
    ec.canvas.ajustar()
    app.processEvents()
    ec.grab().save(str(p))
    print(f"Canvas salvo em {p}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "saida_canvas/canvas.png")

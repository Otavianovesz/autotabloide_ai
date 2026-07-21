"""
Demo F5.3: carrega a ARTE REAL + a célula-mestre no Editor completo (canvas +
camadas + propriedades), seleciona o PREÇO e captura (offscreen).

Uso::

    python -m app.scripts.demo_celula_mestre [saida.png] [imagem_produto.png]
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
from app.rendering.model import TipoRegiao, layout_de_arte  # noqa: E402
from app.scripts.gate_fidelidade import ARTE, DPI, celula_superior_esquerda  # noqa: E402


def main(saida: str, imagem_produto: str) -> None:
    p = Path(saida)
    p.parent.mkdir(parents=True, exist_ok=True)
    app = QApplication.instance() or QApplication(sys.argv)

    layout = layout_de_arte(ARTE, dpi=DPI)
    layout.paginas[0].slots[0].regioes = celula_superior_esquerda(DPI)
    dados = DadosProduto(
        "Abóbora Paulista Listrada", unidade="100g",
        preco_por=Decimal("0.19"), imagem_path=imagem_produto,
    )

    ed = Editor()
    ed.resize(1120, 900)
    ed.carregar(layout, dados, fundo_path=ARTE)
    ed.show()
    app.processEvents()
    ed.area.canvas.ajustar()
    app.processEvents()

    for it in ed.canvas._itens:
        if it.regiao.tipo == TipoRegiao.PRECO:
            it.setSelected(True)
    app.processEvents()

    ed.grab().save(str(p))
    print(f"Editor com célula-mestre salvo em {p}")


if __name__ == "__main__":
    saida = sys.argv[1] if len(sys.argv) > 1 else "saida_celula/editor.png"
    prod = sys.argv[2] if len(sys.argv) > 2 else "app/tests/fixtures/jornal_belo_brasil.jpeg"
    main(saida, prod)

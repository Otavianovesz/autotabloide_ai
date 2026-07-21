"""
Demo F5.5: monta a GRADE do tabloide sobre a arte real e preenche as células com
produtos DIFERENTES da fixture do Belo Brasil (mapa slot→produto).

Uso::

    python -m app.scripts.demo_tabloide [saida.png] [imagem_produto.png]
"""

from __future__ import annotations

import sys
import tempfile
from decimal import Decimal
from pathlib import Path

from app.core.sanitize import sanitizar
from app.rendering.compositor import DadosProduto, compor_pagina
from app.rendering.export import exportar_png
from app.rendering.grade import layout_grade_de_arte
from app.scripts.cartaz_exemplo import gerar_imagem_produto_sintetica
from app.scripts.importar_tabela import parse_tabela

ARTE = "Frente Template.png"
FIXTURE = Path("app/tests/fixtures/ofertas_belo_brasil.txt")


def _preco(txt: str | None):
    if not txt:
        return None
    return Decimal(txt.replace("R$", "").replace(" ", "").replace(",", "."))


def main(saida: str, imagem_produto: str) -> None:
    layout, caixas = layout_grade_de_arte(ARTE)
    n = len(layout.paginas[0].slots)

    itens = parse_tabela(FIXTURE)[:n]
    produtos = [
        DadosProduto(nome=sanitizar(desc).nome_sanitizado, preco_por=_preco(preco),
                     imagem_path=imagem_produto)
        for desc, preco in itens
    ]

    img = compor_pagina(layout, layout.paginas[0], produtos, fundo_path=ARTE)
    Path(saida).parent.mkdir(parents=True, exist_ok=True)
    exportar_png(img, saida, layout.dpi)
    print(f"Caixas detectadas: {len(caixas)} | produtos: {len(produtos)} | imagem {img.size}")
    print(f"Tabloide salvo em {saida}")


if __name__ == "__main__":
    saida = sys.argv[1] if len(sys.argv) > 1 else "saida_tabloide/frente.png"
    if len(sys.argv) > 2:
        prod = sys.argv[2]
    else:
        prod = str(gerar_imagem_produto_sintetica(Path(tempfile.gettempdir()) / "atb_prod.png"))
    main(saida, prod)

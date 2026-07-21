"""
Demo F4.6: compõe dois cartazes com selo — (a) Cerveja com +18 automático,
(b) produto marca própria com o selo "Qualidade Belo Brasil" (placeholder).

Uso::

    python -m app.scripts.demo_selos [pasta_saida]
"""

from __future__ import annotations

import sys
from decimal import Decimal
from pathlib import Path

from app.rendering.compositor import DadosProduto, compor_pagina
from app.rendering.export import exportar_png
from app.scripts.cartaz_exemplo import (
    gerar_arte_sintetica,
    gerar_imagem_produto_sintetica,
    layout_cartaz,
)


def main(pasta: str) -> None:
    d = Path(pasta)
    d.mkdir(parents=True, exist_ok=True)
    fundo = gerar_arte_sintetica(d / "fundo.png", 100, 150, 200)
    prod = gerar_imagem_produto_sintetica(d / "prod.png")
    layout = layout_cartaz(100, 150, 200, str(fundo))

    a = DadosProduto(
        "Cerveja Amstel", unidade="269ml", preco_por=Decimal("2.99"),
        preco_de=Decimal("3.49"), imagem_path=str(prod), mais18=True,
    )
    exportar_png(compor_pagina(layout, layout.paginas[0], a, fundo_path=str(fundo)),
                 d / "a_mais18.png", 200)

    b = DadosProduto(
        "Arroz Belo Brasil", unidade="5kg", preco_por=Decimal("17.71"),
        preco_de=Decimal("21.90"), imagem_path=str(prod), marca_propria=True,
    )
    exportar_png(compor_pagina(layout, layout.paginas[0], b, fundo_path=str(fundo)),
                 d / "b_qualidade.png", 200)

    print(f"Gerados em {d}:  a_mais18.png (+18)  |  b_qualidade.png (Qualidade placeholder)")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "saida_selos")

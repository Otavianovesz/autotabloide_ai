"""
Gate de fidelidade (F2/F5.1) — compõe um produto na célula superior-esquerda
da ARTE REAL do tabloide (Frente Template.png, 1080×1300) e exporta 1:1.

A arte já tem a caixa de preço vermelha e o "R$"; a região [PREÇO] desenha só o
número por cima (mostrar_moeda=False). Nome à esquerda (com hífen), imagem em cima.

Uso::

    python -m app.scripts.gate_fidelidade [saida.png] [imagem_produto.png]
"""

from __future__ import annotations

import sys
from decimal import Decimal
from pathlib import Path

from app.rendering.compositor import DadosProduto, compor_pagina
from app.rendering.export import exportar_png
from app.rendering.model import (
    Ajuste,
    Alinhamento,
    PapelPreco,
    Regiao,
    Retangulo,
    SubtipoPreco,
    TipoRegiao,
    layout_de_arte,
)

DPI = 96
ARTE = "Frente Template.png"


def celula_superior_esquerda(dpi: int) -> list[Regiao]:
    """Regiões da célula-mestre (px na arte): imagem grande/centralizada, preço cheio."""
    return [
        Regiao(TipoRegiao.IMAGEM, Retangulo.de_px(28, 280, 215, 176, dpi),
               nome="Imagem", ajuste=Ajuste.CONTER),
        Regiao(
            TipoRegiao.NOME, Retangulo.de_px(12, 458, 138, 68, dpi),
            nome="Nome", fonte="Quicksand-Bold.ttf", tamanho_max_pt=16, cor="#ffffff",
            alinhamento=Alinhamento.ESQUERDA,
        ),
        Regiao(
            TipoRegiao.PRECO, Retangulo.de_px(156, 466, 105, 58, dpi),
            nome="Preço", fonte="Quicksand-Bold.ttf", tamanho_max_pt=56, cor="#ffffff",
            alinhamento=Alinhamento.CENTRO, subtipo_preco=SubtipoPreco.COMPLETO,
            papel_preco=PapelPreco.POR, mostrar_moeda=False,   # a arte já tem "R$"
        ),
    ]


def main(saida: str, imagem_produto: str) -> None:
    layout = layout_de_arte(ARTE, dpi=DPI)
    layout.paginas[0].slots[0].regioes = celula_superior_esquerda(DPI)
    dados = DadosProduto(
        "Abóbora Paulista Listrada", unidade="100g",
        preco_por=Decimal("0.19"), imagem_path=imagem_produto,
    )
    img = compor_pagina(layout, layout.paginas[0], dados, fundo_path=ARTE)
    exportar_png(img, saida, DPI)
    print(f"Gate salvo em {saida} | tamanho {img.size} (deve ser 1080x1300)")


if __name__ == "__main__":
    saida = sys.argv[1] if len(sys.argv) > 1 else "saida_gate/frente.png"
    prod = sys.argv[2] if len(sys.argv) > 2 else "app/tests/fixtures/jornal_belo_brasil.jpeg"
    Path(saida).parent.mkdir(parents=True, exist_ok=True)
    main(saida, prod)

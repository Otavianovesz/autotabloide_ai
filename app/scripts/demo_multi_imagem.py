"""
Demo F4.5: 3 casos de múltiplas imagens no slot, compostos e exportados.
(a) 3 sabores em LEQUE, (b) 2 produtos LADO_A_LADO, (c) a mesma foto 3x em LEQUE.

Uso::

    python -m app.scripts.demo_multi_imagem [pasta_saida]
"""

from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image, ImageDraw

from app.rendering.arranjo import ModoArranjo
from app.rendering.compositor import DadosProduto, ImagemSlot, compor_pagina
from app.rendering.export import exportar_png
from app.rendering.model import LayoutDef, Pagina, Regiao, Retangulo, Slot, TipoRegiao


def _produto(cor, rotulo: str, caminho: Path, w=400, h=600) -> str:
    """Uma 'garrafa' sintética em RGBA transparente, com rótulo."""
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([w * 0.37, 20, w * 0.63, 95], 22, fill=cor)          # tampa
    d.rounded_rectangle([w * 0.24, 95, w * 0.76, h - 40], 45, fill=cor)      # corpo
    d.rectangle([w * 0.30, h * 0.42, w * 0.70, h * 0.66], fill=(255, 255, 255, 235))  # rótulo
    d.text((w * 0.35, h * 0.52), rotulo, fill=(20, 20, 20))
    img.save(caminho)
    return str(caminho)


def _compor(imagens, modo, saida: Path) -> None:
    layout = LayoutDef(
        120, 120, dpi=200,
        paginas=[Pagina([Slot("s", [Regiao(TipoRegiao.IMAGEM, Retangulo(10, 10, 100, 100))])])],
    )
    dados = DadosProduto("", imagens=[ImagemSlot(p) for p in imagens], modo_arranjo=modo)
    img = compor_pagina(layout, layout.paginas[0], dados)
    exportar_png(img, saida, 200)


def main(pasta: str) -> None:
    d = Path(pasta)
    d.mkdir(parents=True, exist_ok=True)
    morango = _produto((225, 45, 65, 255), "Morango", d / "morango.png")
    uva = _produto((120, 55, 175, 255), "Uva", d / "uva.png")
    laranja = _produto((240, 140, 25, 255), "Laranja", d / "laranja.png")
    camil = _produto((35, 140, 70, 255), "Camil", d / "camil.png")
    rei = _produto((200, 45, 45, 255), "Rei", d / "rei.png")

    _compor([morango, uva, laranja], ModoArranjo.LEQUE, d / "a_leque_sabores.png")
    _compor([camil, rei], ModoArranjo.LADO_A_LADO, d / "b_lado_a_lado.png")
    _compor([morango, morango, morango], ModoArranjo.LEQUE, d / "c_repetida.png")
    print(f"Gerados em {d}:")
    for n in ("a_leque_sabores.png", "b_lado_a_lado.png", "c_repetida.png"):
        print(f"  {n}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "saida_multi")

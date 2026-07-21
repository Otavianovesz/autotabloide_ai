"""
Demonstra a F4.2: remove o fundo de uma imagem, recorta e normaliza.

Uso::

    python -m app.scripts.demo_remover_fundo caminho/entrada.jpg [saida.png]

O primeiro uso baixa o modelo birefnet-general (~1 GB, precisa de internet).
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

from PIL import Image

from app.images.fundo import processar_imagem


def main(entrada: str, saida: str | None = None) -> None:
    p_entrada = Path(entrada)
    p_saida = Path(saida) if saida else p_entrada.with_name(p_entrada.stem + "_semfundo.png")

    orig = Image.open(p_entrada).size
    t = time.time()
    destino = processar_imagem(p_entrada, p_saida)
    dt = time.time() - t
    out = Image.open(destino).size
    print(f"({dt:.0f}s) entrada {orig[0]}x{orig[1]}  ->  saída {out[0]}x{out[1]} (RGBA)")
    print(f"Arquivo: {destino}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("uso: python -m app.scripts.demo_remover_fundo <entrada> [saida]")
        raise SystemExit(2)
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None)

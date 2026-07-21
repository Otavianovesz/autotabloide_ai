"""
Demonstra a busca de imagem (F4.1) no DuckDuckGo, para um produto real.

Uso::

    python -m app.scripts.demo_busca_imagem "Óleo de Soja Liza 900ml"
"""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

from app.images.busca import BaixadorWeb, buscar_imagens


def main(nome: str) -> None:
    destino = Path(tempfile.gettempdir()) / "atb_busca" / nome.replace(" ", "_")[:40]
    r = buscar_imagens(nome, BaixadorWeb(min_lado_hint=400), destino, n=8, min_lado=400)

    print(f'Busca: "{r.query}"')
    if r.bloqueado:
        print("⚠️  Nada baixado — sem rede / limite do DuckDuckGo (degradou sem quebrar).")
        return
    print(f"{len(r.candidatos)} candidatos (após dedup + filtro de resolução):")
    for i, c in enumerate(r.candidatos, 1):
        print(f"  {i}. {c.largura}x{c.altura}  {c.caminho.name}  ({c.hash_md5[:8]})")
    print(f"\nArquivos em: {destino}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "Nutella 350g Ferrero")

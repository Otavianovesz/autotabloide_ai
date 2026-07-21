"""
Demo F4.4: ingere uma imagem por 3 caminhos (arquivo, bytes, URL-fake),
troca por outra e mostra o layout em disco (atual + histórico).

Uso::

    python -m app.scripts.demo_biblioteca [caminho_de_uma_imagem]
"""

from __future__ import annotations

import io
import sys
import tempfile
from pathlib import Path

from PIL import Image

from app.images.biblioteca import BibliotecaImagens


def _bytes(cor: str) -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", (300, 300), cor).save(buf, "PNG")
    return buf.getvalue()


def _arvore(bib: BibliotecaImagens, pid: int) -> None:
    print(f"  {bib.caminho_relativo(pid)}   (atual)")
    for v in bib.listar_versoes(pid):
        print(f"  {pid}/versoes/{v.name}   (histórico)")


def main(imagem: str | None = None) -> None:
    with tempfile.TemporaryDirectory() as d:
        bib = BibliotecaImagens(Path(d) / "biblioteca_imagens", baixar_url=lambda u: _bytes("green"))
        pid = 42

        print("1) ingerir por ARQUIVO")
        origem = imagem
        if not origem:
            origem = str(Path(d) / "amostra.png")
            Image.new("RGB", (300, 300), "red").save(origem)
        bib.ingerir(pid, origem)
        _arvore(bib, pid)

        print("\n2) trocar por BYTES (colado)  -> a anterior vai ao histórico")
        bib.ingerir(pid, _bytes("blue"))
        _arvore(bib, pid)

        print("\n3) trocar por URL (baixador fake)  -> mais uma no histórico")
        bib.ingerir(pid, "https://exemplo.com/foto.png")
        _arvore(bib, pid)

        print(f"\nAtual existe: {bib.caminho_atual(pid).exists()} | versões: {len(bib.listar_versoes(pid))}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else None)

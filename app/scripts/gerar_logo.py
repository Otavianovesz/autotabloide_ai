"""Gera a logo do AutoTabloide em disco (polimento).

Salva em ``AutoTabloide_System_Root/assets/``: ``logo.png`` (512 px, p/ docs e
telas), ``logo.ico`` (multi-tamanho, p/ o instalador/atalho da F12) e a
variante ``logo_belo_brasil.png``. O desenho é o MESMO do ícone da janela
(``splash.pixmap_logo``) — uma marca só.

Rodar::  python -m app.scripts.gerar_logo
"""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path


def main() -> int:
    from PySide6.QtWidgets import QApplication

    from app.core.paths import SystemRoot
    from app.qt.design.splash import pixmap_logo
    QApplication.instance() or QApplication([])

    destino = SystemRoot().raiz / "assets"
    destino.mkdir(parents=True, exist_ok=True)

    pixmap_logo(512).save(str(destino / "logo.png"))
    pixmap_logo(512, laranja=True).save(str(destino / "logo_belo_brasil.png"))

    # .ico multi-tamanho via Pillow (o Windows escolhe o lado certo sozinho)
    from PIL import Image
    tmp = Path(tempfile.mkdtemp())
    base = tmp / "logo256.png"
    pixmap_logo(256).save(str(base))
    Image.open(base).save(
        destino / "logo.ico",
        sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64),
               (128, 128), (256, 256)])
    print(f"logo em {destino} (logo.png, logo.ico, logo_belo_brasil.png)")
    return 0


if __name__ == "__main__":
    sys.exit(main())

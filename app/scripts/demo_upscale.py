"""
Demo F4.3: amplia uma imagem com Real-ESRGAN (lógica condicional de aquisição).

Uso::

    python -m app.scripts.demo_upscale caminho/foto.jpg [--ruim 150]

--ruim N reduz a foto para NxN antes (para simular uma foto ruim de baixa resolução).
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

from PIL import Image

from app.core.paths import SystemRoot
from app.images.upscale import UpscalerRealESRGAN, melhorar_para_biblioteca


def main(entrada: str, ruim_px: int | None = None) -> None:
    modelo = SystemRoot().modelos / "RealESRGAN_x4plus.pth"
    if not modelo.exists():
        print(f"Modelo não encontrado em {modelo}. Baixe o RealESRGAN_x4plus.pth.")
        return

    p = Path(entrada)
    if ruim_px:
        ruim = Image.open(p).convert("RGB").resize((ruim_px, ruim_px))
        p = p.with_name(p.stem + f"_ruim{ruim_px}.png")
        ruim.save(p)
        print(f"Simulando foto ruim: {ruim_px}x{ruim_px} ({p.name})")

    up = UpscalerRealESRGAN(modelo)
    destino = p.with_name(p.stem + "_upscaled.png")
    t = time.time()
    r = melhorar_para_biblioteca(p, up, destino, min_util=1000)
    print(f"({time.time() - t:.0f}s) ampliada={r.ampliada}  {r.de} -> {r.para}")
    print(f"Arquivo: {r.caminho}")


if __name__ == "__main__":
    args = sys.argv[1:]
    ruim = None
    if "--ruim" in args:
        i = args.index("--ruim")
        ruim = int(args[i + 1])
        args = args[:i] + args[i + 2 :]
    if not args:
        print("uso: python -m app.scripts.demo_upscale <entrada> [--ruim 150]")
        raise SystemExit(2)
    main(args[0], ruim)

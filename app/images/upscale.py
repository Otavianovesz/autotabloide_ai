"""
Upscale condicional (F4.3) — enxuto
===================================
As buscas do Bing já trazem fotos boas, então upscale é só para os casos raros:

  * **Na aquisição:** se a foto vier pequena (baixa resolução), amplia e guarda a
    base melhorada — resolve o incômodo comum, sem encher o disco.
  * **Sob demanda:** a ampliação extra para formato grande (cartaz > A2) é gerada
    na hora do export, NÃO guardada.

O ampliador é injetável: ``UpscalerRealESRGAN`` (real, via spandrel) em produção;
``UpscalerLanczos`` (sem IA) como base testável/sem modelo.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from PIL import Image


class Upscaler(Protocol):
    escala: int  # fator nativo do modelo (ex.: 4)

    def ampliar(self, img: Image.Image) -> Image.Image: ...


class UpscalerLanczos:
    """Base sem IA (interpolação). Serve de fallback e para testes sem modelo."""

    def __init__(self, escala: int = 4):
        self.escala = escala

    def ampliar(self, img: Image.Image) -> Image.Image:
        return img.resize((img.width * self.escala, img.height * self.escala), Image.LANCZOS)


class UpscalerRealESRGAN:
    """Backend real (Real-ESRGAN x4 via spandrel). 1º uso carrega o modelo."""

    escala = 4

    def __init__(self, modelo_path: str | Path):
        from spandrel import ModelLoader

        self._model = ModelLoader().load_from_file(str(modelo_path)).eval()

    def ampliar(self, img: Image.Image) -> Image.Image:
        import numpy as np
        import torch

        arr = np.asarray(img.convert("RGB"), dtype="float32") / 255.0
        t = torch.from_numpy(arr).permute(2, 0, 1).unsqueeze(0)
        with torch.no_grad():
            out = self._model(t)
        out = out.squeeze(0).permute(1, 2, 0).clamp(0, 1).cpu().numpy()
        return Image.fromarray((out * 255).round().astype("uint8"), "RGB")


# ==============================================================================
# Lógica condicional
# ==============================================================================


@dataclass
class ResultadoUpscale:
    caminho: Path | None
    ampliada: bool
    de: tuple[int, int]
    para: tuple[int, int]


def precisa_upscale(largura: int, altura: int, *, min_util: int = 1000) -> bool:
    """A foto é pequena demais para uso normal (base da biblioteca)?"""
    return min(largura, altura) < min_util


def melhorar_para_biblioteca(
    imagem: str | Path,
    upscaler: Upscaler,
    destino: str | Path,
    *,
    min_util: int = 1000,
) -> ResultadoUpscale:
    """Aquisição: amplia e guarda SÓ se a foto for pequena; senão mantém."""
    destino = Path(destino)
    destino.parent.mkdir(parents=True, exist_ok=True)
    original = Image.open(imagem).convert("RGB")

    if not precisa_upscale(original.width, original.height, min_util=min_util):
        original.save(destino, "PNG")
        return ResultadoUpscale(destino, False, original.size, original.size)

    grande = upscaler.ampliar(original)
    # não guardar maior que o necessário
    if min(grande.size) > min_util:
        f = min_util / min(grande.size)
        grande = grande.resize((round(grande.width * f), round(grande.height * f)), Image.LANCZOS)
    grande.save(destino, "PNG")
    return ResultadoUpscale(destino, True, original.size, grande.size)


def ampliar_sob_demanda(imagem: str | Path, upscaler: Upscaler, alvo_px: int) -> Image.Image:
    """Export (ex.: cartaz A2): amplia sob demanda até ~alvo_px no maior lado; NÃO guarda."""
    original = Image.open(imagem).convert("RGB")
    if max(original.size) >= alvo_px:
        return original
    grande = upscaler.ampliar(original)
    if max(grande.size) > alvo_px:
        f = alvo_px / max(grande.size)
        grande = grande.resize((round(grande.width * f), round(grande.height * f)), Image.LANCZOS)
    return grande

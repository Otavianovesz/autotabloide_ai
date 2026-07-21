"""
Avaliador de foto (OS F11.5 #27/#28/#29 — R-085)
================================================
Nota "boa / atenção / ruim" para a foto do produto, com os MOTIVOS ditos em
português. O degrau garantido roda em CPU pura (numpy):

- **tamanho** — foto pequena estica serrilhada no cartaz (o motivo liga o
  upscale sob demanda da F10);
- **nitidez** — variância do Laplaciano (borrada = variância baixa);
- **alfa** — packshot recortado (fundo transparente) é sinal de foto tratada.

A parte de visão fina (marca-d'água, produto errado) é da IA local quando
ligada — [MÁQUINA DO DONO]; sem ela, a heurística entrega e AVISA (I2).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

# régua do tamanho: abaixo de RUIM_PX estica visivelmente até num A5;
# entre RUIM_PX e ATENCAO_PX depende do slot (o upscale resolve)
LADO_RUIM_PX = 220
LADO_ATENCAO_PX = 450
# régua da nitidez (variância do Laplaciano em 8 bits): foto de packshot
# nítida fica nas centenas; borrão de zoom digital cai abaixo de ~25
NITIDEZ_RUIM = 8.0
NITIDEZ_ATENCAO = 25.0


@dataclass
class AvaliacaoFoto:
    nota: str                       # "boa" | "atencao" | "ruim"
    motivos: list[str] = field(default_factory=list)
    nitidez: float = 0.0
    lados: tuple[int, int] = (0, 0)
    tem_alfa: bool = False
    sugere_upscale: bool = False    # o motivo é TAMANHO → o upscale F10 resolve


def variancia_laplaciano(img) -> float:
    """Nitidez por variância do Laplaciano — numpy puro (sem OpenCV)."""
    import numpy as np
    g = np.asarray(img.convert("L"), dtype=np.float32)
    if g.shape[0] < 3 or g.shape[1] < 3:
        return 0.0
    lap = (-4.0 * g
           + np.roll(g, 1, 0) + np.roll(g, -1, 0)
           + np.roll(g, 1, 1) + np.roll(g, -1, 1))
    return float(lap[1:-1, 1:-1].var())


def avaliar_foto(caminho: str | Path) -> AvaliacaoFoto:
    """A nota da foto, por conteúdo — nunca levanta (foto ilegível = ruim,
    com o motivo dito)."""
    from PIL import Image
    try:
        img = Image.open(str(caminho))
        img.load()
    except Exception:
        return AvaliacaoFoto("ruim", ["não consegui abrir a foto"], 0.0)
    w, h = img.width, img.height
    menor = min(w, h)
    tem_alfa = img.mode in ("RGBA", "LA") or "transparency" in img.info
    nit = variancia_laplaciano(img)

    motivos: list[str] = []
    pontos_ruins = 0
    sugere_upscale = False
    if menor < LADO_RUIM_PX:
        motivos.append(f"muito pequena ({w}×{h} px) — vai serrilhar impressa")
        pontos_ruins += 2
        sugere_upscale = True
    elif menor < LADO_ATENCAO_PX:
        motivos.append(f"pequena ({w}×{h} px) — o upscale resolve")
        pontos_ruins += 1
        sugere_upscale = True
    if nit < NITIDEZ_RUIM:
        motivos.append("parece borrada (baixa nitidez)")
        pontos_ruins += 2
    elif nit < NITIDEZ_ATENCAO:
        motivos.append("nitidez mediana — confira no zoom")
        pontos_ruins += 1
    if tem_alfa and pontos_ruins == 0:
        motivos.append("packshot recortado, pronto para a arte")

    nota = ("ruim" if pontos_ruins >= 2 else
            "atencao" if pontos_ruins == 1 else "boa")
    return AvaliacaoFoto(nota, motivos, nit, (w, h), tem_alfa, sugere_upscale)


ROTULO_NOTA = {"boa": "Foto boa", "atencao": "Foto: atenção",
               "ruim": "Foto ruim"}

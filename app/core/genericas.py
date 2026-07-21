"""Fotos genéricas por categoria (R-099, Fase 10 — Bloco D).

Quando não há a foto real, uma genérica por categoria (uma caixa, uma garrafa)
segura o layout — mas CLARAMENTE marcada como genérica (o dono sabe que é
placeholder; nunca se confunde com a real). Offline (embarcada/gerada 1×),
coerente com o app offline. Marcada por CONVENÇÃO DE CAMINHO reservado
(``_genericas``, como ``_quarentena``/``_upscale_cartaz``) — o pré-voo avisa.
"""

from __future__ import annotations

from pathlib import Path

PASTA_GENERICAS = "_genericas"

# um mínimo de genéricas por "forma" de embalagem (offline, geradas 1×)
FORMAS_PADRAO = {
    "caixa": (200, 150, 120),
    "garrafa": (90, 140, 200),
    "lata": (150, 150, 160),
    "saco": (200, 180, 120),
    "generico": (170, 170, 170),
}


def _dir() -> Path:
    from app.core.paths import SystemRoot
    d = SystemRoot().biblioteca_imagens / PASTA_GENERICAS
    d.mkdir(parents=True, exist_ok=True)
    return d


def eh_generica(caminho) -> bool:
    """True se o caminho é de uma foto genérica (placeholder), pela convenção."""
    return caminho is not None and \
        PASTA_GENERICAS in str(caminho).replace("\\", "/").split("/")


def _slug(nome: str) -> str:
    return "".join(c if c.isalnum() else "_" for c in (nome or "").lower()).strip("_") \
        or "generico"


def garantir_generica(forma: str = "generico") -> str:
    """Gera (1×) e devolve o caminho da genérica de uma FORMA de embalagem. A
    imagem traz um rótulo 'GENÉRICA' visível — nunca passa por foto real."""
    from PIL import Image, ImageDraw
    forma = forma if forma in FORMAS_PADRAO else "generico"
    destino = _dir() / f"{forma}.png"
    if destino.exists():
        return str(destino)
    cor = FORMAS_PADRAO[forma]
    img = Image.new("RGBA", (600, 600), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([120, 120, 480, 480], radius=24, fill=(*cor, 255))
    d.text((300, 300), "GENÉRICA", anchor="mm", fill=(30, 30, 30))
    img.save(str(destino), "PNG")
    return str(destino)


def caminho_generica(categoria: str | None, forma: str = "generico") -> str | None:
    """A genérica para uma categoria/forma (offline). Sempre existe (gera 1×) —
    devolve o caminho. É um PLACEHOLDER marcado, nunca a foto real."""
    try:
        return garantir_generica(forma)
    except Exception:
        return None

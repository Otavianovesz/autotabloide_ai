"""Marca d'água RASCUNHO (R-067, Fase 8 — Bloco B).

Enquanto o projeto não está aprovado, a exportação sai com um "RASCUNHO"
discreto e diagonal sobre a peça — automático (não depende de o dono lembrar),
some só quando ele aprova. Desenha sobre a Image JÁ composta (depois do
compositor, antes de gravar), reusando `fonte_segura` do compositor — uma cadeia
só, sem tocar o motor de composição.
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw


def carimbar_rascunho(img: Image.Image, texto: str = "RASCUNHO",
                      fontes_dir: str | Path | None = None,
                      opacidade: int = 55) -> Image.Image:
    """Devolve uma CÓPIA da peça com a marca d'água diagonal repetida. Discreta
    (cinza semitransparente) mas inconfundível — e como é ladrilhada, não dá para
    recortar fora. Não altera o original."""
    from app.rendering.compositor import fonte_segura
    if fontes_dir is None:
        from app.core.paths import SystemRoot
        fontes_dir = SystemRoot().fontes
    fontes_dir = Path(fontes_dir)

    base = img.convert("RGBA")
    W, H = base.size
    px = max(18, int(min(W, H) * 0.045))
    fonte = fonte_segura(fontes_dir, "Quicksand-Bold.ttf", px)

    palavra = f"{texto}    "
    medida = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
    try:
        tw = int(medida.textlength(palavra, font=fonte))
    except Exception:
        tw = px * len(palavra) // 2
    tw = max(tw, 1)
    th = px
    tile = Image.new("RGBA", (tw, int(th * 1.7)), (0, 0, 0, 0))
    ImageDraw.Draw(tile).text((0, int(th * 0.3)), palavra, font=fonte,
                              fill=(110, 110, 110, opacidade))

    # ladrilha num palco do tamanho da DIAGONAL, gira 30° e recorta ao centro
    diag = int((W ** 2 + H ** 2) ** 0.5) + tile.height
    palco = Image.new("RGBA", (diag, diag), (0, 0, 0, 0))
    passo_y = int(th * 3)
    linha = 0
    y = 0
    while y < diag:
        desloc = -tile.width // 2 if linha % 2 else 0   # xadrez, sem alinhar tudo
        x = desloc - tile.width
        while x < diag:
            palco.alpha_composite(tile, (x, y))
            x += tile.width
        y += passo_y
        linha += 1

    girado = palco.rotate(30, expand=True, resample=Image.BICUBIC)
    ox = (girado.width - W) // 2
    oy = (girado.height - H) // 2
    recorte = girado.crop((ox, oy, ox + W, oy + H))
    return Image.alpha_composite(base, recorte).convert("RGB")

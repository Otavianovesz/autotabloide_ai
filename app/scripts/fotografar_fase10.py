"""Galeria NATIVA da FASE 10 (Imagens II + Estúdio IA).

O artefato-chave é o ANTES→DEPOIS do packshot (foto crua → packshot bonito, o
sonho do dono). Também: degrau 1 × degrau 2 (degradado sem GPU), refino do
recorte, genérica marcada, ganho de disco da WebP. As imagens são PIL (o Estúdio
é PIL); a demonstração usa um rembg FAKE (a bancada não roda o modelo de 1GB nos
scripts) — o pipeline de luz/sombra/enquadramento é o REAL.

Rodar::  python -m app.scripts.fotografar_fase10 saida_fase10/claro
"""

from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter


def _foto_celular(lado: int = 360) -> Image.Image:
    """Uma 'foto de celular' crua: produto sobre fundo bagunçado/colorido."""
    fundo = Image.new("RGB", (lado, lado), (120, 130, 140))
    d = ImageDraw.Draw(fundo)
    for i in range(0, lado, 24):                 # textura de fundo
        d.line([(0, i), (lado, i)], fill=(105, 115, 128), width=8)
    # produto: uma "garrafa" vermelha meio torta e mal iluminada
    prod = Image.new("RGBA", (lado, lado), (0, 0, 0, 0))
    pd = ImageDraw.Draw(prod)
    pd.rounded_rectangle([140, 90, 220, 300], radius=20, fill=(150, 30, 30, 255))
    pd.rounded_rectangle([160, 50, 200, 100], radius=8, fill=(120, 24, 24, 255))
    prod = prod.rotate(-6, resample=Image.BICUBIC)
    fundo.paste(prod, (0, 0), prod)
    return fundo.point(lambda v: int(v * 0.82))   # subexposta (celular)


def _fake_rembg_da_foto(foto: Image.Image):
    """rembg FAKE fiel a ESTA foto: recorta a região do produto (o vermelho)."""
    def _rembg(_img):
        rgba = foto.convert("RGBA")
        px = rgba.load()
        saida = Image.new("RGBA", rgba.size, (0, 0, 0, 0))
        sp = saida.load()
        for y in range(rgba.height):
            for x in range(rgba.width):
                r, g, b, _a = px[x, y]
                if r > 90 and r > g + 40 and r > b + 40:      # o produto vermelho
                    sp[x, y] = (r, g, b, 255)
        return saida
    return _rembg


def _sobre_branco(rgba: Image.Image) -> Image.Image:
    fundo = Image.new("RGB", rgba.size, (250, 250, 250))
    fundo.paste(rgba, (0, 0), rgba)
    return fundo


_ESCURO = "--tema=escuro" in sys.argv
FUNDO = (28, 30, 34) if _ESCURO else (245, 245, 247)
TEXTO = (220, 222, 226) if _ESCURO else (60, 60, 60)
CARD = (245, 245, 245) if _ESCURO else (250, 250, 250)


def _lado_a_lado(a: Image.Image, b: Image.Image, rot_a="ANTES", rot_b="DEPOIS"):
    m, w, h = 24, max(a.width, b.width), max(a.height, b.height)
    tela = Image.new("RGB", (w * 2 + m * 3, h + 60), FUNDO)
    d = ImageDraw.Draw(tela)
    tela.paste(a.convert("RGB"), (m, 50))
    tela.paste(b.convert("RGB"), (m * 2 + w, 50))
    d.text((m, 20), rot_a, fill=TEXTO)
    d.text((m * 2 + w, 20), rot_b, fill=TEXTO)
    d.text((m + w - 6, h // 2 + 50), "→", fill=TEXTO)
    return tela


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    pasta = Path(args[0] if args else "saida_fase10/claro")
    pasta.mkdir(parents=True, exist_ok=True)

    from app.core import genericas
    from app.images import curadoria, estudio

    # --- 1) ANTES → DEPOIS (o flagship) --------------------------------------
    foto = _foto_celular()
    pack = estudio.packshot_degrau1(foto, remover_fundo=_fake_rembg_da_foto(foto),
                                    lado=360)
    _lado_a_lado(foto, _sobre_branco(pack)).save(str(pasta / "estudio_antes_depois.png"))
    print("  estudio_antes_depois.png")

    # --- 2) degrau 1 × degrau 2 (degradado sem GPU) --------------------------
    _img2, aviso = estudio.refinar_com_gerador(pack)
    d2 = Image.new("RGB", pack.size, FUNDO)
    dd = ImageDraw.Draw(d2)
    dd.text((20, 20), "Degrau 2 (gerador):", fill=TEXTO)
    dd.text((20, 50), (aviso or "")[:60], fill=(200, 110, 80))
    dd.text((20, 80), (aviso[60:120] if aviso else ""), fill=(200, 110, 80))
    _lado_a_lado(_sobre_branco(pack), d2, "DEGRAU 1 (garantido)",
                 "DEGRAU 2 (opção)").save(str(pasta / "degrau1_x_degrau2.png"))
    print("  degrau1_x_degrau2.png")

    # --- 3) refino do recorte (antes/depois do pincel) -----------------------
    antes = pack.copy()
    depois = curadoria.refinar_alfa(pack, [(180, 320), (185, 330)], raio=18,
                                    apagar=True)
    _lado_a_lado(_sobre_branco(antes), _sobre_branco(depois),
                 "RECORTE CRU", "APÓS O PINCEL").save(str(pasta / "refino_recorte.png"))
    print("  refino_recorte.png")

    # --- 4) genérica marcada -------------------------------------------------
    g = genericas.garantir_generica("garrafa")
    _sobre_branco(Image.open(g).convert("RGBA")).resize((360, 360)).save(
        str(pasta / "generica_marcada.png"))
    print("  generica_marcada.png")

    # --- 5) WebP: ganho de disco ---------------------------------------------
    png_p = pasta / "_amostra.png"
    pack.save(png_p, "PNG")
    webp_p = curadoria.salvar_webp(pack, pasta / "_amostra.webp", lossless=True)
    ganho = 100 - round(webp_p.stat().st_size / max(1, png_p.stat().st_size) * 100)
    painel = Image.new("RGB", (560, 200), FUNDO)
    pd = ImageDraw.Draw(painel)
    pd.text((20, 20), "Compressão WebP (preserva a transparência)", fill=TEXTO)
    pd.text((20, 70), f"PNG:  {png_p.stat().st_size // 1024} KB", fill=TEXTO)
    pd.text((20, 100), f"WebP: {webp_p.stat().st_size // 1024} KB  "
                       f"(−{max(0, ganho)}% de disco)", fill=(80, 200, 130))
    pd.text((20, 140), "O alfa do packshot recortado é preservado.", fill=TEXTO)
    painel.save(str(pasta / "webp_ganho.png"))
    print("  webp_ganho.png")

    print(f"Galeria da Fase 10 em {pasta.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

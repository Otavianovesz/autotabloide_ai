"""Curadoria de foto NÃO-DESTRUTIVA (Fase 10, Bloco C/D).

Girar/cortar/espelhar (R-094), pincel de refino do recorte (R-103), detector de
fundo-branco (R-095) e compressão WebP com ALFA (R-100). Tudo são operações PURAS
sobre PIL (a original é preservada pelo chamador via `BibliotecaImagens`, I1).
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageStat


# ---- R-094: girar / cortar / espelhar -------------------------------------

def girar(img: Image.Image, graus: int) -> Image.Image:
    """Gira a imagem (90/180/270 sem perda; outros com expand). Preserva o alfa."""
    return img.rotate(-graus, expand=True)          # -graus = sentido horário


def espelhar(img: Image.Image, horizontal: bool = True) -> Image.Image:
    modo = Image.FLIP_LEFT_RIGHT if horizontal else Image.FLIP_TOP_BOTTOM
    return img.transpose(modo)


def cortar(img: Image.Image, caixa) -> Image.Image:
    """Corta pela caixa (x0, y0, x1, y1), sempre dentro dos limites."""
    x0, y0, x1, y1 = caixa
    x0, y0 = max(0, int(x0)), max(0, int(y0))
    x1, y1 = min(img.width, int(x1)), min(img.height, int(y1))
    if x1 <= x0 or y1 <= y0:
        return img.copy()               # cópia mesmo no caso degenerado (sem aliasing)
    return img.crop((x0, y0, x1, y1))


# ---- R-103: pincel de refino do recorte (sobre o canal alfa) ---------------

def refinar_alfa(img: Image.Image, pontos, raio: int,
                 apagar: bool = False) -> Image.Image:
    """Restaura (pixel comido pelo rembg → alfa 255) ou apaga (sobra → alfa 0) o
    recorte, pintando círculos de raio `raio` no canal ALFA. Devolve uma CÓPIA
    (não altera o original — I1). `apagar=False` restaura; `True` apaga."""
    base = img.convert("RGBA").copy()
    alfa = base.getchannel("A")
    d = ImageDraw.Draw(alfa)
    valor = 0 if apagar else 255
    for x, y in pontos:
        d.ellipse([x - raio, y - raio, x + raio, y + raio], fill=valor)
    base.putalpha(alfa)
    return base


# ---- R-095: detector de fundo-branco (pula o rembg) ------------------------

def tem_fundo_branco(img: Image.Image, *, canto_frac: float = 0.12,
                     limiar_claro: float = 242.0,
                     limiar_uniforme: float = 12.0) -> bool:
    """Mede os 4 CANTOS: se todos são claros (média alta) E uniformes (desvio
    baixo), o fundo já é branco → pula o rembg (economiza tempo e não estraga
    foto boa). Determinístico, sem IA."""
    rgb = img.convert("RGB")
    k = max(4, int(min(rgb.width, rgb.height) * canto_frac))
    cantos = [(0, 0, k, k), (rgb.width - k, 0, rgb.width, k),
              (0, rgb.height - k, k, rgb.height),
              (rgb.width - k, rgb.height - k, rgb.width, rgb.height)]
    for cx in cantos:
        st = ImageStat.Stat(rgb.crop(cx))
        if min(st.mean) < limiar_claro:            # canto não é claro
            return False
        if max(st.stddev) > limiar_uniforme:       # canto não é uniforme
            return False
    return True


# ---- R-100: compressão WebP preservando o ALFA -----------------------------

def webp_disponivel() -> bool:
    try:
        from PIL import features
        return bool(features.check("webp"))
    except Exception:
        return False


def salvar_webp(img: Image.Image, destino: str | Path, *, lossless: bool = True,
                qualidade: int = 90) -> Path:
    """Grava a foto em WebP preservando a TRANSPARÊNCIA (RGBA). Lossless por
    padrão (packshot recortado não pode perder o alfa). Devolve o caminho."""
    destino = Path(destino)
    destino.parent.mkdir(parents=True, exist_ok=True)
    img.convert("RGBA").save(str(destino), "WEBP", lossless=lossless,
                             quality=qualidade)
    return destino

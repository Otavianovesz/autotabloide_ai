"""Vídeo — Stories/Reels (R-139) e vídeo-tabloide (R-142). Fase 8, Bloco D.

DECISÃO TRAVADA: o MP4 é OPCIONAL — sai via ffmpeg (binário no PATH); AUSENTE,
degrada COM aviso (I2), nunca trava. Espelha o padrão do `cmyk.py`
(`ghostscript_disponivel` → detector; a função de trabalho devolve
``(resultado, aviso)``, nunca levanta). O mínimo garantido do app é PNG/PDF +
copiar imagem — o vídeo é o luxo.

O vídeo-tabloide REUSA os PNGs/Images já compostos das páginas (não recompõe —
rápido e fiel). Nada de motor de vídeo pesado: só o ffmpeg do sistema.
"""

from __future__ import annotations

import shutil
import subprocess
import tempfile
from pathlib import Path

from PIL import Image

_SEM_FFMPEG = ("O vídeo pede o componente “ffmpeg”, que não foi encontrado neste "
               "computador. Os PNGs das páginas foram salvos normalmente — só o "
               "MP4 não saiu. Instale o ffmpeg para gerar vídeo (opcional).")


def ffmpeg_disponivel() -> str | None:
    """Caminho do ffmpeg ou None (detector, nunca levanta) — como o
    `ghostscript_disponivel` do CMYK."""
    return shutil.which("ffmpeg")


def ffprobe_disponivel() -> str | None:
    return shutil.which("ffprobe")


def _par(n: int) -> int:
    """Dimensão par (yuv420p exige largura/altura pares)."""
    return n - (n % 2)


def _salvar_frames(imagens: list[Image.Image], pasta: Path) -> list[Path]:
    caminhos = []
    for i, im in enumerate(imagens):
        p = pasta / f"frame_{i:04d}.png"
        im.convert("RGB").save(str(p))
        caminhos.append(p)
    return caminhos


def _rodar_ffmpeg(args: list[str], exe: str) -> tuple[bool, str]:
    try:
        r = subprocess.run([exe, *args], capture_output=True, text=True,
                           timeout=120)
        return (r.returncode == 0), (r.stderr or "")
    except Exception as e:                       # timeout/erro do processo
        return False, str(e)


def frames_do_slideshow(imagens: list[Image.Image],
                        seg_por_pagina: float = 2.5, fps: int = 24,
                        fade_s: float = 0.0) -> list[Image.Image]:
    """OS F11.5 #52: a lista EXATA de frames do vídeo-tabloide — cada página
    fica `seg_por_pagina`; com `fade_s` > 0 entra um crossfade (blend
    progressivo) entre páginas consecutivas. Função pura: testável por pixel
    sem ffmpeg."""
    por_pagina = max(1, round(seg_por_pagina * fps))
    n_fade = max(0, round(fade_s * fps))
    base = [im.convert("RGB") for im in imagens]
    frames: list[Image.Image] = []
    for i, im in enumerate(base):
        frames.extend([im] * por_pagina)
        if n_fade and i + 1 < len(base):
            prox = base[i + 1]
            if prox.size != im.size:
                prox = prox.resize(im.size)
            for k in range(1, n_fade + 1):
                frames.append(Image.blend(im, prox, k / (n_fade + 1)))
    return frames


def gerar_video_paginas(imagens: list[Image.Image], caminho: str | Path,
                        seg_por_pagina: float = 2.5,
                        fps: int = 24,
                        fade_s: float = 0.0) -> tuple[Path | None, str | None]:
    """R-142: slideshow MP4 das páginas JÁ compostas (reusa as Images, não
    recompõe). Sem ffmpeg → (None, aviso). Cada página fica `seg_por_pagina`
    segundos; `fade_s` liga o crossfade entre páginas (#52; 0 = corte seco,
    o comportamento clássico intacto)."""
    if not imagens:
        return None, "Não há páginas para o vídeo."
    exe = ffmpeg_disponivel()
    if exe is None:
        return None, _SEM_FFMPEG
    caminho = Path(caminho)
    caminho.parent.mkdir(parents=True, exist_ok=True)
    w = _par(imagens[0].width)
    h = _par(imagens[0].height)
    # cada página vira N frames (contagem/duração EXATAS); o fade acrescenta
    # os frames de blend entre as páginas. Nada de "quirk" de concat.
    frames = frames_do_slideshow(imagens, seg_por_pagina, fps, fade_s)
    with tempfile.TemporaryDirectory() as td:
        pasta = Path(td)
        _salvar_frames(frames, pasta)
        args = ["-y", "-framerate", str(fps),
                "-i", (pasta / "frame_%04d.png").as_posix(),
                "-vf", f"scale={w}:{h}", "-pix_fmt", "yuv420p",
                caminho.as_posix()]
        ok, err = _rodar_ffmpeg(args, exe)
    if not ok:
        return None, f"O ffmpeg não conseguiu gerar o vídeo: {err[-200:]}"
    return caminho, None


def frames_do_story(img: Image.Image, n: int,
                    pulso_rect: tuple[int, int, int, int] | None = None
                    ) -> list[Image.Image]:
    """R-139 (+ OS F11.5 #49/#50): os frames da animação do Story. Sem
    `pulso_rect`, o respiro clássico (zoom suave do card INTEIRO). Com o rect
    (x, y, w, h em px), o card fica PARADO e SÓ aquele trecho — o preço —
    pulsa (zoom local colado por cima). Pura: testável por pixel sem ffmpeg."""
    import math
    base = img.convert("RGB")
    W, H = _par(base.width), _par(base.height)
    base = base.resize((W, H))
    frames: list[Image.Image] = []
    for i in range(n):
        z = 1.0 + 0.06 * (0.5 - 0.5 * math.cos(2 * math.pi * i / n))  # respiro
        if pulso_rect is None:
            nw, nh = int(W * z), int(H * z)
            amp = base.resize((nw, nh))
            frames.append(amp.crop(((nw - W) // 2, (nh - H) // 2,
                                    (nw - W) // 2 + W, (nh - H) // 2 + H)))
            continue
        x, y, w, h = pulso_rect
        quadro = base.copy()
        trecho = base.crop((x, y, x + w, y + h))
        nw, nh = max(1, int(w * z)), max(1, int(h * z))
        amp = trecho.resize((nw, nh))
        quadro.paste(amp, (x - (nw - w) // 2, y - (nh - h) // 2))
        frames.append(quadro)
    return frames


def gerar_video_story(img: Image.Image, caminho: str | Path,
                      dur_s: float = 3.0, fps: int = 24,
                      pulso_rect: tuple[int, int, int, int] | None = None
                      ) -> tuple[Path | None, str | None]:
    """R-139: uma peça vertical com uma animação LEVE — MP4 curto para o
    Status. Sem ffmpeg → (None, aviso). `pulso_rect` (#49/#50) troca o zoom
    global pela animação ISOLADA do preço."""
    exe = ffmpeg_disponivel()
    if exe is None:
        return None, _SEM_FFMPEG
    caminho = Path(caminho)
    caminho.parent.mkdir(parents=True, exist_ok=True)
    n = max(2, int(dur_s * fps))
    frames = frames_do_story(img, n, pulso_rect)
    W, H = frames[0].width, frames[0].height
    with tempfile.TemporaryDirectory() as td:
        pasta = Path(td)
        _salvar_frames(frames, pasta)
        args = ["-y", "-framerate", str(fps),
                "-i", (pasta / "frame_%04d.png").as_posix(),
                "-vf", f"scale={W}:{H}", "-pix_fmt", "yuv420p",
                caminho.as_posix()]
        ok, err = _rodar_ffmpeg(args, exe)
    if not ok:
        return None, f"O ffmpeg não conseguiu gerar o vídeo: {err[-200:]}"
    return caminho, None


def contar_frames(caminho: str | Path) -> int | None:
    """Nº de frames do MP4 (via ffprobe) — a régua do vídeo. None se não der."""
    exe = ffprobe_disponivel()
    if exe is None:
        return None
    try:
        r = subprocess.run(
            [exe, "-v", "error", "-count_frames", "-select_streams", "v:0",
             "-show_entries", "stream=nb_read_frames", "-of", "csv=p=0",
             str(caminho)], capture_output=True, text=True, timeout=60)
        return int((r.stdout or "").strip())
    except Exception:
        return None


def duracao_video(caminho: str | Path) -> float | None:
    exe = ffprobe_disponivel()
    if exe is None:
        return None
    try:
        r = subprocess.run(
            [exe, "-v", "error", "-show_entries", "format=duration",
             "-of", "csv=p=0", str(caminho)],
            capture_output=True, text=True, timeout=60)
        return float((r.stdout or "").strip())
    except Exception:
        return None


def frame_do_video(mp4: str | Path, indice: int,
                   destino: str | Path) -> Path | None:
    """Extrai UM frame do MP4 como PNG (GATE 2.3 da ordem F11.5: a fidelidade
    do vídeo é provada comparando o frame com a página de ORIGEM, por pixel).
    Sem ffmpeg (ou frame inexistente) → None, nunca levanta."""
    exe = ffmpeg_disponivel()
    if exe is None:
        return None
    destino = Path(destino)
    destino.parent.mkdir(parents=True, exist_ok=True)
    ok, _err = _rodar_ffmpeg(
        ["-y", "-i", str(mp4), "-vf", f"select=eq(n\\,{int(indice)})",
         "-vframes", "1", str(destino)], exe)
    return destino if ok and destino.exists() else None

"""GIF do marco (FASE 12, passo 92): do zero ao tabloide em ~15 s.

A história em 6 quadros, com material REAL: as ofertas transcritas de
``arte/quintou/``, o semáforo com os nomes de verdade e a arte composta
pelo marco (``saida_marco/quintou_p1.png``) — com e sem a marca RASCUNHO.

Rodar (depois do selfcheck do marco)::

    python -m app.scripts.gif_fase12
"""

from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

FUNDO = (24, 28, 35)
TEXTO = (235, 238, 243)
APAGADO = (150, 158, 170)
LARG, ALT = 640, 780


def _fonte(tam: int) -> ImageFont.FreeTypeFont:
    for nome in ("seguisb.ttf", "segoeui.ttf", "arial.ttf"):
        try:
            return ImageFont.truetype(nome, tam)
        except OSError:
            continue
    return ImageFont.load_default()


def _quadro(passo: str, titulo: str) -> tuple[Image.Image, ImageDraw.ImageDraw]:
    q = Image.new("RGB", (LARG, ALT), FUNDO)
    d = ImageDraw.Draw(q)
    d.text((24, 18), passo, fill=(91, 141, 239), font=_fonte(20))
    d.text((24, 46), titulo, fill=TEXTO, font=_fonte(24))
    return q, d


def _colar_arte(q: Image.Image, arte: Image.Image, topo: int = 96) -> None:
    alvo = arte.copy()
    alvo.thumbnail((LARG - 48, ALT - topo - 24))
    q.paste(alvo.convert("RGB"), ((LARG - alvo.width) // 2, topo))


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    arte_p1 = Path("saida_marco/quintou_p1.png")
    if not arte_p1.exists():
        print("rode antes: python -m app.scripts.selfcheck_marco_f12")
        return 1
    from app.core.marco import (
        campanhas_do_marco, itens_reais_da_campanha, validade_das_ofertas)
    disponiveis, _falt = campanhas_do_marco()
    camp = next(c for c in disponiveis if c["nome"] == "quintou")
    itens = itens_reais_da_campanha(camp)          # [(nome, preço), ...]
    validade = validade_das_ofertas(camp["ofertas"]) or "SEM VALIDADE"
    arte = Image.open(arte_p1)

    # 1 · a oferta chega (o texto real do WhatsApp)
    q1, d = _quadro("PASSO 1 de 6", "Cole a oferta — WhatsApp, foto ou Excel")
    y = 110
    for nome, preco in itens[:14]:
        d.text((36, y), f"{nome[:38]}  {preco or ''}",
               fill=APAGADO, font=_fonte(19))
        y += 34
    d.text((36, y + 8), f"… {len(itens)} ofertas · {validade}",
           fill=TEXTO, font=_fonte(19))

    # 2 · o semáforo confere
    q2, d = _quadro("PASSO 2 de 6", "O semáforo confere com o acervo")
    cores = {0: (39, 174, 96), 1: (39, 174, 96), 2: (241, 196, 15),
             3: (39, 174, 96), 4: (231, 76, 60)}
    legenda = {0: "já existe", 1: "já existe", 2: "conferir",
               3: "já existe", 4: "novo — 1 clique cria"}
    y = 116
    for i, (nome, _preco) in enumerate(itens[:5]):
        d.ellipse((36, y + 4, 56, y + 24), fill=cores[i])
        d.text((70, y), nome[:30], fill=TEXTO, font=_fonte(20))
        d.text((70, y + 26), legenda[i], fill=APAGADO, font=_fonte(16))
        y += 62
    d.text((36, y + 16), "“Aceitar todos os verdes” resolve o grosso.",
           fill=TEXTO, font=_fonte(20))

    # 3 · auto-preencher
    q3, _ = _quadro("PASSO 3 de 6",
                    "Auto-preencher: cada oferta acha sua célula")
    _colar_arte(q3, arte)

    # 4 · rascunho automático
    from app.rendering.marca_dagua import carimbar_rascunho
    q4, _ = _quadro("PASSO 4 de 6",
                    "Sem aprovação, TODA saída leva RASCUNHO")
    _colar_arte(q4, carimbar_rascunho(arte.copy()))

    # 5 · aprovado
    q5, _ = _quadro("PASSO 5 de 6", "Aprovou (checklist limpo) — a marca some")
    _colar_arte(q5, arte)

    # 6 · exportado
    q6, d = _quadro("PASSO 6 de 6", "PDF na medida real + PNG do WhatsApp")
    _colar_arte(q6, arte, topo=120)
    d.text((24, 84), "quintou.pdf · 285,8 × 344,0 mm · 2 páginas",
           fill=APAGADO, font=_fonte(19))

    quadros = [q1, q2, q3, q4, q5, q6]
    duracoes = [2400, 2600, 2400, 2600, 2200, 2800]
    saida = Path("saida_fase12")
    saida.mkdir(exist_ok=True)
    quadros[0].save(saida / "do_zero_ao_tabloide.gif", save_all=True,
                    append_images=quadros[1:], duration=duracoes, loop=0)
    print(f"GIF ({sum(duracoes) / 1000:.1f}s) em "
          f"{saida / 'do_zero_ao_tabloide.gif'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

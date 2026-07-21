"""
Ajuste de fonte e quebra de linha
=================================
Regra da doc: o tamanho da fonte **só REDUZ, nunca aumenta** até o texto caber.
Quebra de linha automática, com hífen (pyphen, pt-BR), respeitando a largura.

A busca é pelo MAIOR tamanho (<= teto) que cabe na caixa em largura e altura.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pyphen
from PIL import ImageFont

from app.rendering.units import pt_para_px

_DIC = pyphen.Pyphen(lang="pt_BR")


@dataclass
class TextoAjustado:
    fonte: ImageFont.FreeTypeFont
    linhas: list[str]
    tamanho_pt: float
    altura_linha_px: int


def _quebrar_palavra(palavra: str, fonte, max_w: float) -> list[str]:
    """Quebra uma palavra que não cabe, com hífen (fallback: caractere a caractere)."""
    pedacos: list[str] = []
    resto = palavra
    while fonte.getlength(resto) > max_w:
        posicoes = _DIC.positions(resto)
        escolhido = None
        for p in posicoes:
            if fonte.getlength(resto[:p] + "-") <= max_w:
                escolhido = p
            else:
                break
        if escolhido is None:
            corte = 1
            while corte < len(resto) and fonte.getlength(resto[: corte + 1] + "-") <= max_w:
                corte += 1
            pedacos.append(resto[:corte] + "-")
            resto = resto[corte:]
        else:
            pedacos.append(resto[:escolhido] + "-")
            resto = resto[escolhido:]
        if not resto:
            break
    if resto:
        pedacos.append(resto)
    return pedacos


def _quebrar_linhas(texto: str, fonte, max_w: float) -> list[str]:
    linhas: list[str] = []
    atual = ""
    for palavra in texto.split():
        tentativa = palavra if not atual else f"{atual} {palavra}"
        if fonte.getlength(tentativa) <= max_w:
            atual = tentativa
            continue
        # RG-13: hifenização de APROVEITAMENTO (como o Illustrator) — antes
        # de empurrar a palavra inteira para a próxima linha, tenta encher a
        # atual com um prefixo hifenizado (≥2 letras de cada lado; só em
        # palavras de verdade — "500g"/"R$" nunca ganham hífen).
        if atual and palavra.isalpha() and len(palavra) >= 5:
            melhor = None
            for p in _DIC.positions(palavra):
                if p < 2 or len(palavra) - p < 2:
                    continue
                if fonte.getlength(f"{atual} {palavra[:p]}-") <= max_w:
                    melhor = p
                else:
                    break
            if melhor is not None:
                linhas.append(f"{atual} {palavra[:melhor]}-")
                atual = ""
                palavra = palavra[melhor:]   # a sobra segue o fluxo normal
        if atual:
            linhas.append(atual)
            atual = ""
        if fonte.getlength(palavra) <= max_w:
            atual = palavra
        else:
            pedacos = _quebrar_palavra(palavra, fonte, max_w)
            linhas.extend(pedacos[:-1])
            atual = pedacos[-1]
    if atual:
        linhas.append(atual)
    return linhas or [""]


def _truncar_com_reticencias(linhas, fonte, larg_px, alt_linha, alt_px):
    """R-045 (reflow harmônico — OS F11.5 #42): mantém só as linhas que cabem
    na altura e fecha a última com "…". O recuo é CONTROLADO: primeiro por
    PALAVRA inteira (nunca "Choco…" no meio do termo — o corte sai limpo,
    como um diagramador faria); só uma palavra única grande demais cai no
    corte por caractere. O nome CEDE; nunca transborda p/ a região do preço."""
    max_linhas = max(1, int(alt_px // max(1, alt_linha)))
    if len(linhas) <= max_linhas:
        return linhas
    mantidas = linhas[:max_linhas]
    ultima = mantidas[-1].rstrip()
    palavras = ultima.split()
    while len(palavras) > 1 and \
            fonte.getlength(" ".join(palavras) + "…") > larg_px:
        palavras.pop()                       # recua palavra a palavra
    ultima = " ".join(palavras)
    while ultima and fonte.getlength(ultima + "…") > larg_px:
        ultima = ultima[:-1].rstrip()        # última defesa: palavra gigante
    mantidas[-1] = (ultima + "…") if ultima else "…"
    return mantidas


def ajustar_texto(
    texto: str,
    fonte_path: str | Path,
    larg_px: float,
    alt_px: float,
    tamanho_max_pt: float,
    dpi: int,
    tamanho_min_pt: float = 6.0,
    entrelinha: float = 1.12,
) -> TextoAjustado:
    """Maior tamanho <= teto que faz o texto caber (largura E altura)."""
    fonte_path = str(fonte_path)

    def _fonte(px: int):
        """Fonte com fallback (I2): pedida → Roboto ao lado → embutida do Pillow."""
        try:
            return ImageFont.truetype(fonte_path, px)
        except OSError:
            from pathlib import Path
            roboto = Path(fonte_path).parent / "Roboto-Regular.ttf"
            if roboto.exists():
                return ImageFont.truetype(str(roboto), px)
            return ImageFont.load_default(px)

    def tentar(pt: float) -> TextoAjustado | None:
        px = max(1, round(pt_para_px(pt, dpi)))
        fonte = _fonte(px)
        linhas = _quebrar_linhas(texto, fonte, larg_px)
        if any(fonte.getlength(ln) > larg_px + 0.5 for ln in linhas):
            return None
        asc, desc = fonte.getmetrics()
        alt_linha = round((asc + desc) * entrelinha)
        if alt_linha * len(linhas) <= alt_px:
            return TextoAjustado(fonte, linhas, pt, alt_linha)
        return None

    # Se já cabe no teto, usa o teto (nunca aumenta além dele).
    no_teto = tentar(tamanho_max_pt)
    if no_teto is not None:
        return no_teto

    # Busca binária pelo maior tamanho que cabe.
    lo, hi = tamanho_min_pt, tamanho_max_pt
    melhor: TextoAjustado | None = None
    while hi - lo > 0.5:
        meio = (lo + hi) / 2
        res = tentar(meio)
        if res is not None:
            melhor = res
            lo = meio
        else:
            hi = meio
    if melhor is not None:
        return melhor

    # Nem no mínimo coube: o nome CEDE com reticências (R-045) — corta no nº de
    # linhas que cabem na altura e nunca transborda p/ a região vizinha.
    px = max(1, round(pt_para_px(tamanho_min_pt, dpi)))
    fonte = _fonte(px)
    linhas = _quebrar_linhas(texto, fonte, larg_px)
    asc, desc = fonte.getmetrics()
    alt_linha = round((asc + desc) * entrelinha)
    linhas = _truncar_com_reticencias(linhas, fonte, larg_px, alt_linha, alt_px)
    return TextoAjustado(fonte, linhas, tamanho_min_pt, alt_linha)

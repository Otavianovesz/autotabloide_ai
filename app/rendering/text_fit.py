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


_MIN_LETRAS_HIFEN = 8
"""VICESIMUS-OCTAVUS/L25 (o critério do estrangeiro, prática): só se
parte palavra LONGA. As palavras que o hífen estragou no Quintou —
"Cream" (5), "Supre|me" (7), "Gour|met" (7) — são curtas; as comuns
que se partem bem ("Achocolatado", "Instantâneo", "Concentrado") têm
9+. Marca longa (Andorinha, Campilar) é barrada pelo VOCABULÁRIO."""


def _atomo(palavra: str, atomos: frozenset[str] | set[str]) -> bool:
    """L25 — O HÍFEN NÃO ENTRA EM NOME PRÓPRIO: marca, submarca e nome
    de linha são ÁTOMOS (nunca se partem). ``atomos`` chega do
    chamador com o vocabulário de marcas normalizado."""
    if not atomos:
        return False
    import unicodedata
    p = unicodedata.normalize("NFKD", palavra.lower())
    p = "".join(c for c in p if not unicodedata.combining(c)).strip(".,;:")
    return p in atomos


def _quebrar_linhas(texto: str, fonte, max_w: float,
                    sem_hifen: bool = False,
                    atomos: frozenset[str] | set[str] = frozenset()) -> list[str]:
    """F13-BIS/T5: com ``sem_hifen`` a palavra NUNCA é partida — a linha
    estoura a largura e o chamador (``ajustar_texto``) REDUZ O CORPO até
    caber ("CERVEJA ITAPA-VA" na arte real virou prova de artefato)."""
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
        if (not sem_hifen and atual and palavra.isalpha()
                and len(palavra) >= _MIN_LETRAS_HIFEN
                and not _atomo(palavra, atomos)):
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
        if (fonte.getlength(palavra) <= max_w or sem_hifen
                or _atomo(palavra, atomos)):
            # sem_hifen (ou ÁTOMO da L25): inteira, mesmo estourando —
            # quem cede é o corpo, nunca a marca partida ao meio
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


def piso_do_celular(largura_pagina_mm: float) -> float:
    """F13-UNDECIMUS/U1: o piso do tipo é uma REGRA, não um dado.

    A régua do teste do celular (OCTAVUS/C1): o WhatsApp mostra a
    página a ~37% — para o nome ter os 11 px mínimos legíveis no
    celular, a LINHA precisa de 11/0,37 ≈ 30 px na página-régua de
    1080 px de largura. Escalando pela largura real e convertendo a
    pontos (linha ≈ corpo×1,2 × entrelinha 1,12), o piso é função SÓ
    da largura física da página — vale para todo layout, inclusive os
    que o dono desenhar amanhã. Na página dos encartes (285,75 mm) dá
    ~16,8 pt: exatamente a calibração aprovada da Segunda.

    Nunca desce do 6.0 histórico (etiquetas pequenas não são peça de
    celular)."""
    PX_MINIMOS_NO_CELULAR = 11.0
    FATOR_WHATSAPP = 0.37
    PAGINA_REGUA_PX = 1080.0
    ALTURA_DE_LINHA = 1.2 * 1.12          # (asc+desc)/corpo × entrelinha
    if not largura_pagina_mm or largura_pagina_mm <= 0:
        return 6.0
    linha_regua_px = PX_MINIMOS_NO_CELULAR / FATOR_WHATSAPP
    larg_px_96 = largura_pagina_mm / 25.4 * 96.0
    linha_px = linha_regua_px * (larg_px_96 / PAGINA_REGUA_PX)
    piso = (linha_px / ALTURA_DE_LINHA) * 72.0 / 96.0
    return max(6.0, piso)


def ajustar_texto(
    texto: str,
    fonte_path: str | Path,
    larg_px: float,
    alt_px: float,
    tamanho_max_pt: float,
    dpi: int,
    tamanho_min_pt: float = 6.0,
    entrelinha: float = 1.12,
    sem_hifen: bool = False,
    atomos: frozenset[str] | set[str] = frozenset(),
) -> TextoAjustado:
    """Maior tamanho <= teto que faz o texto caber (largura E altura).

    F13-BIS/T5: ``sem_hifen`` faz da hifenização coisa proibida — a
    palavra fica inteira e quem cede é o CORPO (busca binária); se nem
    no mínimo couber, as reticências do R-045 seguram (nunca o hífen)."""
    fonte_path = str(fonte_path)
    # F13-NONUS: piso acima do teto seria desenhar ACIMA do teto no
    # ramo do truncamento — o teto manda
    tamanho_min_pt = min(tamanho_min_pt, tamanho_max_pt)

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

    def tentar(pt: float, ats=atomos) -> TextoAjustado | None:
        px = max(1, round(pt_para_px(pt, dpi)))
        fonte = _fonte(px)
        linhas = _quebrar_linhas(texto, fonte, larg_px, sem_hifen, ats)
        if any(fonte.getlength(ln) > larg_px + 0.5 for ln in linhas):
            return None
        asc, desc = fonte.getmetrics()
        alt_linha = round((asc + desc) * entrelinha)
        if alt_linha * len(linhas) <= alt_px:
            return TextoAjustado(fonte, linhas, pt, alt_linha)
        return None

    def maior_que_cabe(ats) -> TextoAjustado | None:
        """Busca binária pelo maior corpo que cabe com esse vocabulário."""
        lo, hi = tamanho_min_pt, tamanho_max_pt
        achado: TextoAjustado | None = None
        while hi - lo > 0.5:
            meio = (lo + hi) / 2
            res = tentar(meio, ats)
            if res is not None:
                achado = res
                lo = meio
            else:
                hi = meio
        return achado

    # DEGRAUS 1–3 da escada (SEPTIMUS §2): cabe no corpo cheio com a
    # marca INTEIRA (a abreviação já veio decidida pelo nome_fit; aqui
    # o hífen só entra em palavra comum).
    no_teto = tentar(tamanho_max_pt, atomos)
    if no_teto is not None:
        return no_teto
    melhor = maior_que_cabe(atomos)

    # DEGRAU 4 — UNDETRICESIMUS §1 (o despacho do conflito L23×L25):
    # nenhuma das duas leis cede; a L25 vira PREFERÊNCIA ORDENADA. O
    # publicado do dono hifeniza "Itaipa-va" e "Ma-rombi" (as duas são
    # marca), mas isso é a caixa de seleção do Illustrator ligada, não
    # desenho — e quebrar a marca não custa venda, texto pequeno custa.
    # Então: parte-se a marca SÓ quando a alternativa seria encolher o
    # texto. Onde há folga, a marca continua inteira (a L25 vale nos
    # oito sem configuração).
    if atomos and not sem_hifen:
        no_teto_livre = tentar(tamanho_max_pt, frozenset())
        if no_teto_livre is not None:
            return no_teto_livre              # corpo cheio > marca inteira
        livre = maior_que_cabe(frozenset())
        if livre is not None and (melhor is None
                                  or livre.tamanho_pt > melhor.tamanho_pt + 0.01):
            return livre
    if melhor is not None:
        return melhor

    # Nem no mínimo coube: o nome CEDE com reticências (R-045) — corta no nº de
    # linhas que cabem na altura e nunca transborda p/ a região vizinha.
    px = max(1, round(pt_para_px(tamanho_min_pt, dpi)))
    fonte = _fonte(px)
    # UNDETRICESIMUS §2 (o despacho do 2º conflito): o PISO NÃO CEDE —
    # ele nasce de um fato físico (a distância de leitura no celular),
    # enquanto a altura da região é um número digitado. Quem cede é a
    # CAIXA, e isso acontece antes daqui (``compositor.crescer_do_piso``);
    # se a caixa não pôde crescer, a última defesa é esta tesoura — o
    # texto NUNCA vaza (o único resultado proibido dos três).
    # No piso, a marca também cede ao hífen: partir "Itaipa-va" é menos
    # perda que engolir a palavra na elipse (a mesma ordem do degrau 4).
    linhas = _quebrar_linhas(texto, fonte, larg_px, sem_hifen, atomos)
    if not sem_hifen and any(fonte.getlength(ln) > larg_px + 0.5
                             for ln in linhas):
        linhas = _quebrar_linhas(texto, fonte, larg_px, sem_hifen, frozenset())
    asc, desc = fonte.getmetrics()
    alt_linha = round((asc + desc) * entrelinha)
    linhas = _truncar_com_reticencias(linhas, fonte, larg_px, alt_linha, alt_px)
    return TextoAjustado(fonte, linhas, tamanho_min_pt, alt_linha)

"""F13-TER/N2 — o Jornal por SEÇÕES, com quantidade variável.

O motor de FLUXO puro (geometria, sem Qt): as seções vêm ordenadas,
cada uma ganha um cabeçalho fino (fio + versalete, desenhado pelo app
onde a linha CAIU) e os itens fluem em colunas. Os degraus de
degradação são TABELADOS e na ordem declarada da ordem TER §5:

  (a) sobe o número de colunas (``FaixaFluxo.colunas`` — no Jornal
      atual a arte tem réguas de coluna fixas em 5, então a escada
      declara ``(5,)`` e este degrau não existe LÁ; o motor o suporta);
  (b) desce um degrau de ALTURA da célula (``alturas_celula`` —
      tamanhos tabelados, nunca contínuos);
  (c) TRANSBORDA para a próxima faixa (a página 2), e avisa.

Decisões registradas (§5.5/5.6 da ordem):
- a última linha de cada seção nunca fica quebrada: CENTRALIZA
  (mantém o ritmo das colunas; esticar mudaria a largura da célula
  dentro da mesma seção);
- seção de 1 ITEM não ganha linha própria: a célula entra na MESMA
  linha da seção seguinte e o cabeçalho fica INLINE (na largura da
  célula, sobre ela);
- o que não coube em faixa nenhuma é NOMEADO nos avisos (I2), nunca
  cortado em silêncio.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field


@dataclass(frozen=True)
class FaixaFluxo:
    """A banda de conteúdo de UMA página (px 1x da arte)."""

    x: float
    y: float
    largura: float
    altura: float
    colunas: tuple = (5,)                  # degrau (a), em ordem
    alturas_celula: tuple = (202, 178, 156)   # degrau (b), em ordem
    altura_cabecalho: float = 34           # fio + versalete


@dataclass
class BlocoSecao:
    """Uma seção RESOLVIDA numa faixa: cabeçalho + células (px 1x)."""

    secao: str
    faixa: int                             # índice da faixa (página)
    cabecalho: tuple                       # (x, y, w, h)
    cabecalho_inline: bool
    celulas: list = field(default_factory=list)   # [(x, y, w, h)]


@dataclass
class ResultadoFluxo:
    blocos: list = field(default_factory=list)
    avisos: list = field(default_factory=list)


def _degraus(faixa: FaixaFluxo):
    """A escada declarada: (a) todas as colunas no 1º degrau de altura,
    depois (b) desce a altura (nas colunas máximas)."""
    escada = []
    for alt in faixa.alturas_celula:
        for cols in faixa.colunas:
            escada.append((cols, alt))
    # ordena mantendo a intenção: 1º degrau de altura com cada opção de
    # coluna, depois os degraus de altura seguintes (colunas máximas)
    vistos, ordenada = set(), []
    for alt in faixa.alturas_celula:
        for cols in faixa.colunas:
            if (cols, alt) not in vistos:
                vistos.add((cols, alt))
                ordenada.append((cols, alt))
    return ordenada


def _altura_necessaria(secoes, cols, alt, faixa: FaixaFluxo) -> float:
    """Σ(seções) [cabeçalho + ceil(itens/colunas) × altura] — a conta
    declarada do §5.4 (seções de 1 item compartilham linha: contam a
    célula na seção seguinte e nenhum cabeçalho de banda)."""
    total = 0.0
    extras = 0                             # células de seções de 1 item
    for i, (_titulo, n) in enumerate(secoes):
        if n == 1 and i + 1 < len(secoes):
            extras += 1
            continue
        total += faixa.altura_cabecalho
        total += math.ceil((n + extras) / cols) * alt
        extras = 0
    if extras:                             # 1-item no fim: linha própria
        total += faixa.altura_cabecalho + alt
    return total


def montar_fluxo(secoes, faixas) -> ResultadoFluxo:
    """Resolve as seções nas faixas, na escada declarada.

    ``secoes``: [(titulo, n_itens)] na ordem do dono.
    ``faixas``: [FaixaFluxo] na ordem das páginas.
    """
    r = ResultadoFluxo()
    restantes = [(t, int(n)) for t, n in secoes if int(n) > 0]
    for idx_faixa, faixa in enumerate(faixas):
        if not restantes:
            break
        # escolhe o degrau desta faixa: o primeiro em que TUDO que
        # resta caiba NA CAPACIDADE restante (esta faixa + as faixas
        # seguintes) — transbordo previsto não força o degrau mínimo;
        # se nem o último degrau basta, usa-o (melhor aproveitamento)
        # e o excedente final é NOMEADO
        capacidade = faixa.altura + sum(
            f.altura for f in faixas[idx_faixa + 1:])
        escolhido = None
        for cols, alt in _degraus(faixa):
            if _altura_necessaria(restantes, cols, alt,
                                  faixa) <= capacidade:
                escolhido = (cols, alt)
                break
        transborda = escolhido is None
        if transborda:
            escolhido = _degraus(faixa)[-1]
        cols, alt = escolhido
        if escolhido != _degraus(faixa)[0] and not transborda:
            r.avisos.append(
                f"faixa {idx_faixa + 1}: usado o degrau "
                f"{cols} coluna(s) × {alt}px para caber tudo")
        larg = faixa.largura / cols
        y = faixa.y
        pendente_1item = None              # (titulo,) aguardando linha
        proximos: list = []
        for i, (titulo, n) in enumerate(restantes):
            if y >= faixa.y + faixa.altura:
                proximos.append((titulo, n))
                continue
            if n == 1 and i + 1 < len(restantes):
                pendente_1item = titulo    # entra na linha da próxima
                continue
            if y + faixa.altura_cabecalho + alt > faixa.y + faixa.altura:
                if pendente_1item is not None:
                    proximos.append((pendente_1item, 1))
                    pendente_1item = None
                proximos.append((titulo, n))
                continue
            reservadas = 1 if pendente_1item is not None else 0
            bloco = BlocoSecao(
                secao=titulo, faixa=idx_faixa,
                cabecalho=(faixa.x + reservadas * larg, y,
                           faixa.largura - reservadas * larg,
                           faixa.altura_cabecalho),
                cabecalho_inline=False)
            if pendente_1item is not None:
                # decisão registrada: a seção de 1 item compartilha a
                # linha — célula na coluna 1, cabeçalho INLINE sobre ela
                r.blocos.append(BlocoSecao(
                    secao=pendente_1item, faixa=idx_faixa,
                    cabecalho=(faixa.x, y, larg, faixa.altura_cabecalho),
                    cabecalho_inline=True,
                    celulas=[(faixa.x, y + faixa.altura_cabecalho,
                              larg, alt)]))
                pendente_1item = None
            y_itens = y + faixa.altura_cabecalho
            colocadas = 0
            n_restante = n
            primeira_linha_cols = cols - reservadas
            while n_restante > 0:
                if y_itens + alt > faixa.y + faixa.altura:
                    break                   # transbordou no meio
                cols_linha = primeira_linha_cols if colocadas == 0 else cols
                x0 = (faixa.x + reservadas * larg
                      if colocadas == 0 else faixa.x)
                nesta = min(cols_linha, n_restante)
                ultima = nesta == n_restante
                larg_linha = larg
                if ultima and nesta < cols_linha:
                    # QUATER/J1 (contrato invertido): a última linha
                    # NUNCA fica quebrada — as células ESTICAM e
                    # preenchem a banda inteira (centralizar deixava
                    # as colunas das pontas vazias = "esburacado")
                    larg_linha = cols_linha * larg / nesta
                for c in range(nesta):
                    bloco.celulas.append(
                        (x0 + c * larg_linha, y_itens, larg_linha, alt))
                colocadas += nesta
                n_restante -= nesta
                y_itens += alt
                reservadas = 0
                primeira_linha_cols = cols
            r.blocos.append(bloco)
            y = y_itens
            if n_restante > 0:
                proximos.append((f"{titulo} (continuação)", n_restante))
                r.avisos.append(
                    f"a seção “{titulo}” transbordou: {n_restante} "
                    f"item(ns) seguem na faixa {idx_faixa + 2}")
        if pendente_1item is not None:
            proximos.append((pendente_1item, 1))
        restantes = proximos
        if restantes and idx_faixa + 1 < len(faixas):
            nomes = ", ".join(t for t, _ in restantes)
            if not any("transbord" in a for a in r.avisos):
                r.avisos.append(
                    f"transbordou para a faixa {idx_faixa + 2}: {nomes}")
    if restantes:
        sobra = sum(n for _t, n in restantes)
        nomes = ", ".join(t for t, _ in restantes)
        r.avisos.append(
            f"{sobra} item(ns) não coube(ram) em faixa nenhuma "
            f"({nomes}) — reduza itens ou seções")
    return r

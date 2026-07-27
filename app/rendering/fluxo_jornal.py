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

        def _colocar(alt_uso: float):
            """Um passe de colocação com a altura dada — o J16 roda
            dois: o 1º descobre as linhas; se sobrar altura na faixa,
            o 2º recoloca com a altura ESTICADA (uniforme, J2)."""
            blocos: list = []
            avisos: list = []
            y = faixa.y
            pendente = None
            prox: list = []
            n_linhas = 0
            for i, (titulo, n) in enumerate(restantes):
                if y >= faixa.y + faixa.altura:
                    prox.append((titulo, n))
                    continue
                if n == 1 and i + 1 < len(restantes):
                    pendente = titulo      # entra na linha da próxima
                    continue
                if y + faixa.altura_cabecalho + alt_uso > \
                        faixa.y + faixa.altura:
                    if pendente is not None:
                        prox.append((pendente, 1))
                        pendente = None
                    prox.append((titulo, n))
                    continue
                reservadas = 1 if pendente is not None else 0
                bloco = BlocoSecao(
                    secao=titulo, faixa=idx_faixa,
                    cabecalho=(faixa.x + reservadas * larg, y,
                               faixa.largura - reservadas * larg,
                               faixa.altura_cabecalho),
                    cabecalho_inline=False)
                if pendente is not None:
                    # decisão registrada: a seção de 1 item compartilha
                    # a linha — cabeçalho INLINE sobre a própria célula
                    blocos.append(BlocoSecao(
                        secao=pendente, faixa=idx_faixa,
                        cabecalho=(faixa.x, y, larg,
                                   faixa.altura_cabecalho),
                        cabecalho_inline=True,
                        celulas=[(faixa.x, y + faixa.altura_cabecalho,
                                  larg, alt_uso)]))
                    pendente = None
                y_itens = y + faixa.altura_cabecalho
                colocadas = 0
                n_restante = n
                primeira_linha_cols = cols - reservadas
                while n_restante > 0:
                    if y_itens + alt_uso > faixa.y + faixa.altura:
                        break               # transbordou no meio
                    cols_linha = (primeira_linha_cols if colocadas == 0
                                  else cols)
                    x0 = (faixa.x + reservadas * larg
                          if colocadas == 0 else faixa.x)
                    nesta = min(cols_linha, n_restante)
                    ultima = nesta == n_restante
                    larg_linha = larg
                    if ultima and nesta < cols_linha:
                        # QUATER/J1 + SEXTUS (o caso do Oral-B): a
                        # última linha ESTICA até 1,6× — acima disso a
                        # célula vira um deserto com o carimbo órfão;
                        # o resto centraliza (equilíbrio, não buraco)
                        larg_linha = min(cols_linha * larg / nesta,
                                         larg * 1.6)
                        x0 = x0 + (cols_linha * larg
                                   - nesta * larg_linha) / 2
                    for c in range(nesta):
                        bloco.celulas.append(
                            (x0 + c * larg_linha, y_itens,
                             larg_linha, alt_uso))
                    colocadas += nesta
                    n_restante -= nesta
                    y_itens += alt_uso
                    n_linhas += 1
                    reservadas = 0
                    primeira_linha_cols = cols
                blocos.append(bloco)
                y = y_itens
                if n_restante > 0:
                    prox.append((f"{titulo} (continuação)", n_restante))
                    avisos.append(
                        f"a seção “{titulo}” transbordou: {n_restante} "
                        f"item(ns) seguem na faixa {idx_faixa + 2}")
            if pendente is not None:
                prox.append((pendente, 1))
            return blocos, prox, avisos, y, n_linhas

        blocos, proximos, avisos_f, y_fim, n_linhas = _colocar(float(alt))
        # SEXTUS/J16 (a 3ª vida do defeito J5/J13, agora por número):
        # sobrou altura na faixa? A sobra é DISTRIBUÍDA nas linhas —
        # células mais ALTAS (fotos maiores, a página enche), altura
        # UNIFORME (J2 preservado). Teto de 45% do degrau para não
        # deformar a célula.
        sobra = (faixa.y + faixa.altura) - y_fim
        if not proximos and n_linhas and sobra > n_linhas:
            delta = min(sobra / n_linhas, alt * 0.65)
            blocos, proximos, avisos_f, y_fim, n_linhas = _colocar(
                alt + delta)
        r.blocos.extend(blocos)
        r.avisos.extend(avisos_f)
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

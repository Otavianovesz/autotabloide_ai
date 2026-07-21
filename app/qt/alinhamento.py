"""
Alinhamento (F5.4) — lógica pura, testável sem Qt
=================================================
Retângulos são tuplas (x, y, w, h) em px de cena. Funções puras para:
snapping (guias magnéticas), alinhar e distribuir. A parte visual (desenhar as
guias, botões) fica no canvas/toolbar; aqui é só a matemática.
"""

from __future__ import annotations


def snap(rect, alvos_x, alvos_y, limiar: float):
    """Aproxima o rect dos alvos mais próximos (bordas esq/centro/dir e topo/meio/base).

    Retorna (novo_x, novo_y, guias) onde guias = [('x', coord), ('y', coord)] que casaram.
    """
    x, y, w, h = rect

    def melhor(bordas, alvos):
        best = None
        for val in bordas:
            for a in alvos:
                d = a - val
                if abs(d) <= limiar and (best is None or abs(d) < abs(best[0])):
                    best = (d, a)
        return best

    bx = melhor([x, x + w / 2, x + w], alvos_x)
    by = melhor([y, y + h / 2, y + h], alvos_y)
    guias = []
    if bx:
        guias.append(("x", bx[1]))
    if by:
        guias.append(("y", by[1]))
    return x + (bx[0] if bx else 0), y + (by[0] if by else 0), guias


def alinhar(rects, modo: str):
    """modo: esq | centro_h | dir | topo | meio | base. Alinha à caixa da seleção.

    Retorna lista de (nx, ny) — novas posições (topo-esq), mantendo w/h.
    """
    if not rects:
        return []
    esq = min(x for x, y, w, h in rects)
    dir_ = max(x + w for x, y, w, h in rects)
    topo = min(y for x, y, w, h in rects)
    base = max(y + h for x, y, w, h in rects)
    cx, cy = (esq + dir_) / 2, (topo + base) / 2

    saida = []
    for x, y, w, h in rects:
        nx, ny = x, y
        if modo == "esq":
            nx = esq
        elif modo == "dir":
            nx = dir_ - w
        elif modo == "centro_h":
            nx = cx - w / 2
        elif modo == "topo":
            ny = topo
        elif modo == "base":
            ny = base - h
        elif modo == "meio":
            ny = cy - h / 2
        saida.append((nx, ny))
    return saida


def distribuir(rects, eixo: str):
    """Distribui os centros igualmente entre o primeiro e o último (eixo 'h' ou 'v')."""
    if len(rects) < 3:
        return [(x, y) for x, y, w, h in rects]

    def centro(r):
        x, y, w, h = r
        return (x + w / 2) if eixo == "h" else (y + h / 2)

    ordem = sorted(range(len(rects)), key=lambda i: centro(rects[i]))
    c0, c1 = centro(rects[ordem[0]]), centro(rects[ordem[-1]])
    passo = (c1 - c0) / (len(ordem) - 1)

    saida = [None] * len(rects)
    for k, i in enumerate(ordem):
        x, y, w, h = rects[i]
        novo = c0 + passo * k
        saida[i] = (novo - w / 2, y) if eixo == "h" else (x, novo - h / 2)
    return saida


def distribuir_espacamento(rects, eixo: str, espaco: float, *,
                           grade_passo: float | None = None,
                           guias: tuple = (), limiar: float = 2.0):
    """R-033 (+ OS F11.5 #60): distribui com espaçamento FIXO (borda a borda)
    entre os itens, na ordem do eixo, ancorado no primeiro (menor coord) —
    agora RESPEITANDO guias e grade magnética: cada posição distribuída
    snapa à guia do eixo a até ``limiar`` (a guia vence) e, sem guia por
    perto, ao múltiplo da grade (quando ligada). Retorna lista de (nx, ny)."""
    if not rects:
        return []

    def coord(r):
        return r[0] if eixo == "h" else r[1]

    def _snap(v: float) -> float:
        for orient, g in guias:              # guia do MESMO eixo vence
            if orient == ("x" if eixo == "h" else "y") and abs(v - g) <= limiar:
                return g
        if grade_passo and grade_passo > 0:
            perto = round(v / grade_passo) * grade_passo
            if abs(v - perto) <= limiar:
                return perto
        return v

    ordem = sorted(range(len(rects)), key=lambda i: coord(rects[i]))
    saida = [None] * len(rects)
    cursor = coord(rects[ordem[0]])           # âncora = o primeiro
    for i in ordem:
        x, y, w, h = rects[i]
        pos = _snap(cursor)
        if eixo == "h":
            saida[i] = (pos, y)
            cursor = pos + w + espaco
        else:
            saida[i] = (x, pos)
            cursor = pos + h + espaco
    return saida

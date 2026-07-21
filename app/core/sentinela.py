"""Sentinela de preço estranho (R-078, Fase 9 — Bloco B).

"R$79 num sabonete?" — avisa quando o preço foge da faixa histórica do
produto/categoria. É AVISO, nunca trava (decisão travada da fase: a IA/heurística
informa, o dono decide). A faixa é APRENDIDA do acervo (mediana ± k·IQR por
categoria), não um número mágico — calibra com o que a loja realmente vende.
"""

from __future__ import annotations

from decimal import Decimal


def faixas_por_categoria(itens, *, k: float = 3.0) -> dict[str, tuple[Decimal, Decimal]]:
    """Deriva a faixa (mín, máx) de cada categoria a partir dos preços do acervo.
    `itens` = iterável de (categoria, preco_decimal). Categoria sem amostra
    suficiente (< 4) não ganha faixa (evita alarme com pouco dado)."""
    por_cat: dict[str, list[Decimal]] = {}
    for cat, preco in itens:
        if cat and preco is not None:
            por_cat.setdefault(str(cat), []).append(Decimal(str(preco)))
    faixas: dict[str, tuple[Decimal, Decimal]] = {}
    for cat, precos in por_cat.items():
        if len(precos) < 4:
            continue
        ordenados = sorted(precos)
        q1 = ordenados[len(ordenados) // 4]
        q3 = ordenados[(len(ordenados) * 3) // 4]
        iqr = q3 - q1
        margem = iqr * Decimal(str(k)) if iqr > 0 else q3 - q1 or q3
        lo = max(Decimal("0"), q1 - margem)
        hi = q3 + (margem if margem > 0 else q3)
        faixas[cat] = (lo, hi)
    return faixas


def preco_suspeito(preco: Decimal | None, categoria: str | None,
                   faixas: dict[str, tuple[Decimal, Decimal]]) -> str | None:
    """R-078: devolve o AVISO (nunca None se está fora da faixa da categoria) ou
    None se está dentro/sem faixa. Nunca levanta, nunca bloqueia."""
    if preco is None or not categoria:
        return None
    faixa = faixas.get(str(categoria))
    if faixa is None:
        return None
    lo, hi = faixa
    if preco < lo:
        return (f"R$ {preco} parece baixo para “{categoria}” "
                f"(a faixa da loja é R$ {lo}–{hi}) — confira.")
    if preco > hi:
        return (f"R$ {preco} parece alto para “{categoria}” "
                f"(a faixa da loja é R$ {lo}–{hi}) — confira.")
    return None

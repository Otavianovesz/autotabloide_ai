"""O +18 determinístico (Rodada JM, B3.5).

Decisão travada da casa: o selo +18 entra SEMPRE em bebida alcoólica.
Sem o LM Studio, o `mais18` da criação era False CRAVADO — a cerveja
passava sem selo. A heurística é por TOKEN (sem caixa/acento), com a
lista fechada de bebidas do balcão e os vetos que importam ("vinagre"
não é vinho; "sem álcool"/"0,0" não é alcoólica).

O falso positivo é SEGURO (um selo a mais que o dono desmarca na
curadoria — o checkbox é visível, I2); o falso negativo mantém o status
quo. A heurística só LIGA o +18 — nunca desliga o que a IA ligou.
"""

from __future__ import annotations

import unicodedata

BEBIDAS_ALCOOLICAS: frozenset[str] = frozenset({
    "cerveja", "chopp", "chope", "vinho", "espumante", "champagne",
    "champanhe", "vodka", "cachaca", "pinga", "whisky", "whiskey",
    "uisque", "licor", "conhaque", "rum", "gin", "tequila", "sidra",
    "vermute", "catuaba", "jurupinga", "aperitivo", "aguardente",
    "sake", "saque", "campari", "steinhaeger",
})

# vetos por TOKEN: a palavra que desarma a bebida no mesmo nome
_VETOS_TOKEN: frozenset[str] = frozenset({"vinagre", "zero"})
# vetos por TRECHO no texto normalizado
_VETOS_TEXTO: tuple[str, ...] = ("sem alcool", "0,0", "0.0", "0%")


def _norm(texto: str) -> str:
    t = unicodedata.normalize("NFKD", (texto or "").lower())
    return "".join(c for c in t if not unicodedata.combining(c))


def eh_bebida_alcoolica(nome: str | None) -> bool:
    """True quando o nome contém uma bebida alcoólica conhecida e nenhum
    veto ("Vinagre de Vinho" e "Cerveja Sem Alcool" são False)."""
    texto = _norm(nome or "")
    if not texto:
        return False
    tokens = set(texto.replace("-", " ").split())
    if not (tokens & BEBIDAS_ALCOOLICAS):
        return False
    if tokens & _VETOS_TOKEN:
        return False
    return not any(v in texto for v in _VETOS_TEXTO)

"""Migração de layouts antigos para o modelo da Fase 5 (RG-57 — Bloco E).

Roda "de carona" ao ABRIR um layout (não em massa destrutiva): injeta o
``papel_texto`` nas regiões TEXTO_LEGAL de layouts que não o tinham, inferindo
do conteúdo — SEM perder nada. É **idempotente**: região que já declara o
papel não é tocada. O default seguro é "Texto livre".

Como o compositor da Fase 5 já é retro-compatível (LIVRE cai em
``texto_fixo or validade``, byte-idêntico ao legado), esta migração corrige o
RÓTULO/badge e o comportamento futuro — o conteúdo já estava preservado.
"""

from __future__ import annotations

# pistas de texto para inferir o papel (minúsculas, sem acento sensível)
_PISTAS_LEGAL = ("menores de 18", "venda proibida", "moderação", "moderacao",
                 "enquanto durarem", "estoques", "regulamento", "ilustrativa",
                 "unidades participantes")
_PISTAS_VALIDADE = ("válid", "valid", " até ", " ate ", "vencimento",
                    "oferta válida", "oferta valida")


def inferir_papel_texto(texto_fixo: str | None) -> str:
    """Infere o papel de uma região TEXTO_LEGAL antiga a partir do texto fixo.

    - vazio → VALIDADE (o legado: "vazio = usa a validade do projeto");
    - texto de aviso legal (bebida/sorteio/genérico) → LEGAL;
    - texto de validade ("válido até…") → VALIDADE;
    - qualquer outro → LIVRE (seguro; o dono reclassifica se quiser).
    """
    txt = (texto_fixo or "").strip().lower()
    if not txt:
        return "VALIDADE"
    if any(p in txt for p in _PISTAS_LEGAL):
        return "LEGAL"
    if any(p in txt for p in _PISTAS_VALIDADE):
        return "VALIDADE"
    return "LIVRE"


def migrar_papeis_texto_dict(d: dict) -> int:
    """Injeta ``papel_texto`` nas regiões TEXTO_LEGAL SEM a chave (layout
    antigo). Idempotente. Muta ``d`` in-place. Devolve quantas regiões migrou."""
    n = 0
    for pagina in d.get("paginas", []):
        for slot in pagina.get("slots", []):
            for reg in slot.get("regioes", []):
                if reg.get("tipo") != "TEXTO_LEGAL" or "papel_texto" in reg:
                    continue
                reg["papel_texto"] = inferir_papel_texto(reg.get("texto_fixo"))
                n += 1
    return n

"""Aprendizado local e auditável (Fase 9 — Bloco C).

REGRA DURA (decisão travada): o app NUNCA inventa marca, sigla ou protocolo —
só aprende o que o dono CONFIRMOU; ambíguo vira amarelo. Aqui moram:

- **R-087 marca extraída do nome:** acha a marca DENTRO do nome, mas só entre as
  marcas CONHECIDAS (confirmadas). Nenhum token bate → None (não inventa).
- **R-086 sinônimos regionais:** mandioca/macaxeira/aipim tratados como o mesmo
  produto na conciliação — um dicionário editável (o dono acrescenta os da região).
- **R-077 siglas:** a expansão VD→vidro entra no glossário da F3 (uma casa só) —
  aqui só a helper de aplicar; a persistência é a Config `sanitizacao.glossario`.

Tudo local, determinístico e testável sem hardware.
"""

from __future__ import annotations

from app.core.portabilidade import _norm

# semente de sinônimos regionais (R-086) — o dono acrescenta os da região dele.
# cada grupo mapeia para uma forma CANÔNICA (a 1ª do grupo).
SINONIMOS_REGIONAIS_PADRAO: list[list[str]] = [
    ["mandioca", "macaxeira", "aipim"],
    ["abóbora", "jerimum"],
    ["tangerina", "mexerica", "bergamota", "mimosa"],
    ["amendoim", "mendubim"],
]


def extrair_marca(nome: str, marcas_conhecidas) -> str | None:
    """R-087: devolve a marca CONHECIDA que aparece no nome, ou None. NUNCA
    inventa: se nenhum token/expressão do nome bate uma marca confirmada, devolve
    None (ambíguo → amarelo/manual). Marca de 1+ palavras ("Tio João") casa se
    TODAS as palavras dela estão no nome, na ordem."""
    alvo = _norm(nome)
    melhor = None
    for marca in marcas_conhecidas:
        m = _norm(marca)
        if not m:
            continue
        # casa a expressão inteira (com fronteira de palavra) dentro do nome
        if f" {m} " in f" {alvo} ":
            # prefere a marca mais LONGA (mais específica) quando várias batem
            if melhor is None or len(m) > len(_norm(melhor)):
                melhor = marca
    return melhor


def _grupos_canonicos(grupos):
    """dict termo_normalizado -> forma canônica (a 1ª de cada grupo)."""
    mapa: dict[str, str] = {}
    for grupo in grupos:
        if not grupo:
            continue
        canonico = grupo[0]
        for termo in grupo:
            mapa[_norm(termo)] = canonico
    return mapa


def canonizar_sinonimos(nome: str, grupos=None) -> str:
    """R-086: troca cada termo regional pela forma canônica do grupo, para a
    conciliação casar o mesmo produto. Preserva os demais tokens (não descarta
    nada — I2). 'Farofa de macaxeira' → 'Farofa de mandioca'."""
    mapa = _grupos_canonicos(grupos if grupos is not None
                             else SINONIMOS_REGIONAIS_PADRAO)
    saida = []
    for tok in nome.split():
        can = mapa.get(_norm(tok))
        saida.append(can if can is not None else tok)
    return " ".join(saida)


def mesmo_produto_regional(a: str, b: str, grupos=None) -> bool:
    """True se a e b são o mesmo produto a menos de sinônimo regional
    (canonizados batem). Usado pela conciliação para não criar duplicata regional."""
    return _norm(canonizar_sinonimos(a, grupos)) == \
        _norm(canonizar_sinonimos(b, grupos))

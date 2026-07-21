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


def grupos_com_extras(extras=None) -> list[list[str]]:
    """OS F11.5 #47/#81 (R-086): os grupos padrão + os que o DONO acrescentou
    (a Config `sinonimos.regionais`, que viaja com o banco — portátil, I3).
    Grupo inválido/vazio é ignorado sem drama."""
    saida = [list(g) for g in SINONIMOS_REGIONAIS_PADRAO]
    for g in (extras or []):
        termos = [str(t).strip() for t in (g or []) if str(t).strip()]
        if len(termos) >= 2:
            saida.append(termos)
    return saida


def ordenar_tipo_marca(nome: str, marcas_conhecidas) -> str:
    """OS F11.5 #49 (R-087): aplica a ORDEM da casa (Tipo+Marca+resto) quando
    uma marca CONHECIDA aparece fora do lugar — "Camil Arroz 5kg" vira
    "Arroz Camil 5kg". Determinístico e conservador: sem marca conhecida no
    nome, devolve como veio (nunca inventa nem descarta token)."""
    marca = extrair_marca(nome, marcas_conhecidas)
    if not marca:
        return nome
    toks = nome.split()
    alvo = [_norm(t) for t in marca.split()]
    n = len(alvo)
    pos = next((i for i in range(len(toks) - n + 1)
                if [_norm(t) for t in toks[i:i + n]] == alvo), None)
    if pos is None or pos == 1:
        return nome                       # não achei, ou já está após o tipo
    marca_toks = toks[pos:pos + n]
    resto = toks[:pos] + toks[pos + n:]
    if not resto:
        return nome                       # o nome é SÓ a marca — nada a ordenar
    return " ".join([resto[0]] + marca_toks + resto[1:])


_RE_PESO_VARIACAO = None


def _sem_peso(nome: str) -> str:
    import re
    global _RE_PESO_VARIACAO
    if _RE_PESO_VARIACAO is None:
        _RE_PESO_VARIACAO = re.compile(
            r"\b\d+[.,]?\d*\s?(kg|g|l|ml|un)\b", re.IGNORECASE)
    return _RE_PESO_VARIACAO.sub(" ", nome)


def sugerir_variacoes(itens, marcas_conhecidas) -> list[list]:
    """OS F11.5 #50/#51 (R-082): agrupa prováveis VARIAÇÕES do mesmo produto
    (sabores/tamanhos): mesma marca CONHECIDA + mesmo tipo (1º token útil) e
    nomes diferentes entre si. Nunca inventa: item sem marca confirmada não
    entra em sugestão nenhuma. Devolve grupos de 2+ itens."""
    grupos: dict[tuple, list] = {}
    for it in itens:
        nome = (getattr(it, "nome", None) or str(it) or "").strip()
        if not nome:
            continue
        marca = extrair_marca(nome, marcas_conhecidas)
        if not marca:
            continue
        alvo = {_norm(t) for t in marca.split()}
        toks = [t for t in _sem_peso(nome).split() if _norm(t) not in alvo]
        if not toks:
            continue
        chave = (_norm(marca), _norm(toks[0]))
        grupos.setdefault(chave, []).append(it)
    saida = []
    for membros in grupos.values():
        nomes = {(getattr(it, "nome", None) or str(it)).strip().lower()
                 for it in membros}
        if len(membros) >= 2 and len(nomes) >= 2:
            saida.append(membros)
    return saida

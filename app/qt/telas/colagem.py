"""Parser de colagem (R-050, Fase 7 — Bloco A).

Transforma uma tabela COLADA (WhatsApp Web/Excel) em linhas de produto
`(nome, preço)`. LEI: REUSA o parser de preço P0.3 (`servico.preco_decimal`)
e o caminho de criação do RG-20 — NÃO reimplementa. O parser só SEPARA nome ×
preço por heurística (tab/;/|/preço-no-fim), ignora lixo (cabeçalho/total/
linha vazia) e marca o preço não entendido (I2), para a prévia "isto é o que
entendi" mostrar antes de criar.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

# um preço no FIM da linha (WhatsApp: "Arroz Tio João 5kg  R$ 24,90")
_RE_PRECO_FIM = re.compile(r"(R\$\s*)?\d[\d.\s]*[.,]\d{2}\s*$")
# "Nx V,VV" PROIBIDO no fim (WhatsApp: "Refrigerante 2x 5,00") — ambíguo, não é
# promoção ("2 por" é). Achado da frota adversarial: separado por ESPAÇO ele
# escapava e virava preço "5,00" calado; agora é marcado como preço a rever (I2).
_RE_AMBIGUO_FIM = re.compile(r"(\d+\s*x\s*(?:R\$\s*)?\d[\d.]*[.,]\d{2})\s*$", re.I)
# "parece preço": tem dígitos e um separador decimal, ou só dígitos com R$
_RE_PARECE_PRECO = re.compile(r"^(R\$\s*)?\d[\d.\s]*([.,]\d{1,2})?$")
# cabeçalho/rodapé a ignorar (não é produto)
_LIXO = ("produto", "descrição", "descricao", "preço", "preco", "valor",
         "item", "total", "subtotal", "qtd", "quantidade")


@dataclass
class LinhaColada:
    nome: str
    preco: str | None            # texto cru, como veio (None = sem preço)
    preco_valido: bool           # preco_decimal(preco) is not None
    aviso: str | None = None
    # TERTIUSDECIMUS/Q2: o desconto DECLARADO ("LANCHE NA CHAPA COM
    # 20 % de DESCONTO") — item SEM preço que TEM valor comercial; a
    # arte tem a pílula para ele e o pré-voo não reclama
    desconto_pct: int | None = None
    # R-070/passo 62: multi-preço reconhecido NA COLAGEM ("3 por R$10", "leve 3
    # pague 2"). Quando presente, `preco` fica None e a linha TEM preço (não é
    # "sem preço"): é um FORMATO de promoção, não um valor. O "2x 5,00" proibido
    # nunca chega aqui — não casa o padrão (segue rejeitado pelo P0.3).
    multi_preco: str | None = None


def _eh_lixo(linha: str) -> bool:
    baixo = linha.lower().strip(" \t;|-–:")
    if not baixo:
        return True
    # linha só com números/separadores (numeração, total solto)
    if re.fullmatch(r"[\d.,\s;|r$]+", baixo):
        return True
    campos = [p.strip() for p in re.split(r"[;\t|]", baixo) if p.strip()]
    if not campos:
        return True
    # cabeçalho: todos os campos são títulos conhecidos ("Produto;Preço")
    if all(p in _LIXO for p in campos):
        return True
    # rodapé/total: o 1º campo é uma palavra-título ("Total;123,45", "Qtd;42")
    return campos[0] in _LIXO


def _parece_preco(campo: str) -> bool:
    return bool(_RE_PARECE_PRECO.match(campo.strip()))


def _nome_preco(raw: str) -> tuple[str, str | None]:
    """Separa (nome, preço) de uma linha. Preço = último campo que parece
    preço (colunas) ou o preço no fim da linha (WhatsApp)."""
    for sep in ("\t", ";", "|"):
        if sep in raw:
            campos = [c.strip() for c in raw.split(sep) if c.strip()]
            if len(campos) >= 2:
                for i in range(len(campos) - 1, -1, -1):
                    if _parece_preco(campos[i]):
                        nome = " ".join(campos[:i] + campos[i + 1:]).strip()
                        return (nome or campos[0]), campos[i]
                return " ".join(campos[:-1]).strip(), campos[-1]
    # OS F11.5 #6: a VÍRGULA como separador de coluna ("Arroz 5kg, 24,90") —
    # sem colidir com o decimal: só a última ", " (vírgula+ESPAÇO) conta, e
    # só quando o lado direito é um preço inteiro válido
    if ", " in raw:
        nome, _, resto = raw.rpartition(", ")
        if nome.strip() and _parece_preco(resto):
            return nome.strip(" -–:\t"), resto.strip()
    m = _RE_PRECO_FIM.search(raw)
    if m:
        return raw[:m.start()].strip(" -–:\t"), m.group(0).strip()
    return raw.strip(), None


def _split_multi(raw: str) -> "tuple[str, MultiPreco] | None":
    """Se a linha traz um multi-preço ("N por R$X"/"leve N pague M"), devolve
    (nome, MultiPreco); senão None. O nome é tudo ANTES do padrão (o padrão fica
    no fim da linha colada, depois do nome)."""
    for rex in (_RE_N_POR, _RE_LEVE):
        m = rex.search(raw)
        if m:
            nome = raw[:m.start()].strip(" -–:\t;|")
            mp = parse_multi_preco(m.group(0))
            if mp is not None:
                return (nome or raw.strip()), mp
    return None


def parse_colagem(texto: str, *, balde: list | None = None) -> list[LinhaColada]:
    """Uma linha de produto por linha do texto colado; preço validado por P0.3
    (ambíguo → marcado, nunca criado em silêncio). Multi-preço reconhecido como
    FORMATO (R-070) — não confundido com preço inválido.

    F13-DUODECIMUS/T1: a tabela real do dono é 2/3 PROSA promocional
    com números que parecem preço ("LEVE 3… GANHE 25 %", "50 % de
    DESCONTO"). Linha SEM preço de moeda no fim não vira produto:
    prosa COM número vai ao ``balde`` (mostrado ao dono — I2); prosa
    sem número morre em silêncio. A colagem ESTRUTURADA (tab/;/| e
    preço-no-fim) segue como sempre."""
    from app.qt.telas.servico import preco_decimal

    linhas: list[LinhaColada] = []
    for raw in (texto or "").splitlines():
        raw = raw.rstrip()
        # Q4 (a Quarta): "▶"/"•" no início é marcador visual, não texto
        raw = raw.lstrip("▶•·◦> ").rstrip()
        if not raw.strip() or _eh_lixo(raw):
            continue
        # passo 62: multi-preço PRIMEIRO — "Sabão;3 por R$10" é promoção, não
        # um preço "não entendido" (o split ingênuo cairia em vermelho falso).
        multi = _split_multi(raw)
        if multi is not None:
            nome, mp = multi
            if nome:
                linhas.append(LinhaColada(nome, None, True, None,
                                          multi_preco=mp.texto))
            continue
        # o "2x 5,00" PROIBIDO (mesmo separado por espaço) NÃO vira preço válido:
        # é marcado a rever, nunca aceito calado (I2 — valor errado é pior que
        # ausente). Antes escapava na forma WhatsApp (achado da frota).
        amb = _RE_AMBIGUO_FIM.search(raw)
        if amb is not None:
            nome = raw[:amb.start()].strip(" -–:\t;|")
            preco_amb = amb.group(1).strip()
            if nome:
                linhas.append(LinhaColada(
                    nome, preco_amb, False,
                    f"preço “{preco_amb}” não foi entendido — confira "
                    "(ex.: 5,00; ou use “2 por 5,00” se for promoção)."))
            continue
        # Rodada JM (B2B): "…<> S. OFERTA" no fim da linha é PREÇO-TEXTO
        # (o valor varia no mês; a forma escreve SUPER OFERTA) — vem
        # ANTES do balde: a linha real tinha "<>"/"." e morria como
        # prosa-com-número, engolida
        m_so = _RE_SUPER_OFERTA_FIM.search(raw)
        if m_so is not None:
            nome_so = _limpar_nome_de_tabela(raw[:m_so.start()])
            if nome_so:
                linhas.append(LinhaColada(nome_so, None, True,
                                          multi_preco="SUPER OFERTA"))
                continue
        nome, preco = _nome_preco(raw)
        nome = _limpar_nome_de_tabela(nome)
        if not nome:
            continue
        # T1 (a Terça): linha SEM preço só vira item se tiver CARA DE
        # PRODUTO — curta, sem dígito solto, sem pontuação de frase
        # ("Sabonete Dove" da lista de WhatsApp segue virando amarelo).
        # PROSA com número (o 25%/50% da mecânica gravada na arte — T3)
        # vai ao balde VISÍVEL; prosa sem número morre em silêncio.
        if not preco:
            eh_prosa = (re.search(r"[.!?“”\"…<>]|\.{2,}", raw)
                        or len(nome.split()) > 8)
            # Q2 (a Quarta): "LANCHE NA CHAPA COM 20 % de DESCONTO" —
            # item cuja OFERTA é o percentual; linha curta com o padrão
            # vira item-com-desconto (a prosa longa/pontuada continua
            # indo ao balde — o leve-3 da Terça não engana)
            m_desc = re.search(r"(?:com\s+)?(\d{1,3})\s*%\s*(?:de\s*)?"
                               r"desconto", raw, re.IGNORECASE)
            if m_desc and not eh_prosa:
                nome_d = _limpar_nome_de_tabela(
                    raw[:m_desc.start()].strip(" -–:;|"))
                nome_d = re.sub(r"\bcom\s*$", "", nome_d,
                                flags=re.IGNORECASE).strip()
                if nome_d:
                    linhas.append(LinhaColada(
                        nome_d, None, True,
                        desconto_pct=int(m_desc.group(1))))
                    continue
            if re.search(r"\d", raw):
                if balde is not None:
                    balde.append(raw.strip())
                continue
            if eh_prosa:
                continue
            linhas.append(LinhaColada(
                nome, None, False,
                "sem preço — vira amarelo na conciliação"))
            continue
        valido = preco_decimal(preco) is not None
        aviso = None
        if not valido:
            aviso = f"preço “{preco}” não foi entendido — confira (ex.: 5,00)"
        linhas.append(LinhaColada(nome, preco, valido, aviso))
    _remover_codigos_de_coluna(linhas)
    return linhas


# Rodada JM (B1.4): o código de coluna do documento ("T-1") — token
# curto LETRA(S)-NÚMERO na BORDA do nome. A remoção é por FREQUÊNCIA no
# lote: só quando o padrão se repete em ≥3 nomes E ≥30% das linhas ele é
# coluna do documento; um "B-12" isolado (a vitamina) é nome e FICA — o
# caso-limite escrito com a regra.
_RE_CODIGO_COLUNA = re.compile(r"^[A-Za-z]{1,3}-\d{1,3}$")


def _remover_codigos_de_coluna(linhas: list[LinhaColada]) -> None:
    if len(linhas) < 3:
        return
    com_codigo = 0
    for li in linhas:
        tokens = li.nome.split()
        if tokens and (_RE_CODIGO_COLUNA.match(tokens[0])
                       or _RE_CODIGO_COLUNA.match(tokens[-1])):
            com_codigo += 1
    if com_codigo < 3 or com_codigo < 0.3 * len(linhas):
        return
    for li in linhas:
        tokens = li.nome.split()
        while tokens and _RE_CODIGO_COLUNA.match(tokens[-1]):
            tokens.pop()
        while tokens and _RE_CODIGO_COLUNA.match(tokens[0]):
            tokens.pop(0)
        if tokens:
            li.nome = " ".join(tokens)


_RE_SUFIXO_PRECO = re.compile(
    r"[\s_.·–-]*\b(por|s[óo])\b[\s_.·–-]*$", re.IGNORECASE)


def _limpar_nome_de_tabela(nome: str | None) -> str:
    """F13-SEXTUS/S1: a tabela real do dono é um documento de impressão
    com ``______`` entre o nome e o preço e um prefixo "por"/"SÓ" que
    varia de caixa — NADA disso é nome de produto. Come as sequências
    de underscore/pontilhado e a palavra de prefixo no RABO do nome
    (só isolada, nunca dentro de palavra)."""
    if not nome:
        return ""
    # T4 (a Terça): o "À"/"A" ENTRE pontilhados é enfeite de
    # preenchimento do documento ("OSSINHO ___À___100g") — sai ANTES da
    # troca dos underscores; um "à" legítimo no nome (Frango à
    # Passarinho) não tem underscores e fica
    limpo = re.sub(r"_+\s*[àáa]\s*(?=_|\d)", " ", nome,
                   flags=re.IGNORECASE)
    # Rodada JM (B1.4): o "<>" do documento do Jornal é separador
    # visual entre nome e preço — nunca é nome de produto
    limpo = re.sub(r"[<>]+", " ", limpo)
    limpo = re.sub(r"[_]{2,}", " ", limpo)
    limpo = re.sub(r"\s{2,}", " ", limpo).strip(" _.·–-\t")
    while True:
        novo = _RE_SUFIXO_PRECO.sub("", limpo).strip(" _.·–-\t")
        if novo == limpo:
            return limpo
        limpo = novo


def linhas_para_tuplas(linhas: list[LinhaColada]):
    """(descricao, preco, ean) — o MESMO formato que `importar_ofertas`
    consome, para reusar o pipeline de conciliação (P0.3/RG-20) sem duplicar.
    (O multi-preço viaja à parte por `multi_precos_de` — a tupla é só o valor.)"""
    return [(li.nome, li.preco, None) for li in linhas]


def multi_precos_de(linhas: list[LinhaColada]):
    """Lista de multi-preços PARALELA às tuplas (mesma ordem) — propagada ao
    ItemMesa depois da conciliação (`conciliar_linhas(..., multi_precos=...)`)."""
    return [li.multi_preco for li in linhas]


def descontos_de(linhas: list[LinhaColada]):
    """Q2: lista de descontos declarados PARALELA às tuplas (mesma
    ordem) — o "20% de desconto" do Lanche viaja ao ItemMesa."""
    return [li.desconto_pct for li in linhas]


# ----------------------------------------------------------------------------
# Multi-preço (R-070): "3 por R$10" / "leve 3 pague 2" — FORMATO explícito de
# promoção por quantidade. Reconhecido AQUI, não pelo P0.3 (que rejeita
# múltiplos números de propósito). O "2x 5,00" PROIBIDO nunca casa aqui — segue
# rejeitado pelo `preco_decimal` (os dois testados lado a lado, passo 62/95).
# ----------------------------------------------------------------------------

_RE_N_POR = re.compile(r"\b(\d+)\s*por\s*(R\$\s*)?(\d[\d.]*(?:[.,]\d{2})?)", re.I)
_RE_LEVE = re.compile(r"\bleve\s*(\d+)\s*pague\s*(\d+)\b", re.I)

# Rodada JM (B2B, decisão do dono 03/08): "S. OFERTA" no lugar do preço
# = o preço VARIA no mês e o cartaz escreve SUPER OFERTA dentro da forma.
_RE_SUPER_OFERTA = re.compile(r"^s\.?\s*oferta$|^super\s+oferta$", re.I)
_RE_SUPER_OFERTA_FIM = re.compile(r"(s\.?\s*oferta|super\s+oferta)\s*$", re.I)


def preco_texto_oferta(texto: str | None) -> str | None:
    """Reconhece as grafias da tabela ("S. OFERTA", "S.OFERTA", "SUPER
    OFERTA") e devolve o CANÔNICO "SUPER OFERTA" — ou None. Slogans
    ("OFERTA DO DIA") e formatos com dono próprio nunca casam."""
    t = (texto or "").strip().strip("<>_ .·–-")
    if not t:
        return None
    return "SUPER OFERTA" if _RE_SUPER_OFERTA.match(t.strip()) else None


@dataclass
class MultiPreco:
    texto: str                # texto composto para desenho ("3 por R$ 10,00")
    quantidade: int
    valor: str | None = None  # valor total (texto), quando aplicável


def parse_multi_preco(texto: str) -> "MultiPreco | None":
    """Reconhece "N por R$X" e "leve N pague M". Devolve MultiPreco ou None.
    "2x 5,00" (ambíguo/proibido) NUNCA casa — não tem "por" nem "leve/pague"."""
    t = (texto or "").strip()
    m = _RE_N_POR.search(t)
    if m:
        q, valor = int(m.group(1)), m.group(3)
        return MultiPreco(f"{q} por R$ {valor}", q, valor)
    m = _RE_LEVE.search(t)
    if m:
        leve, pague = int(m.group(1)), int(m.group(2))
        return MultiPreco(f"Leve {leve} pague {pague}", leve)
    return None


def compor_multi_preco(qtd: int, valor: str) -> str | None:
    """Compõe "N por R$ X" a partir dos campos qtd+valor (o `PromocaoDialog`).
    Valida o valor pelo P0.3 (não deixa passar valor ruim) e garante round-trip
    por `parse_multi_preco`. Devolve o texto ou None (entrada inválida)."""
    from app.qt.telas.servico import preco_decimal
    valor = (valor or "").strip()
    if qtd < 1 or not valor or preco_decimal(valor) is None:
        return None
    return f"{int(qtd)} por R$ {valor}"


def compor_leve_pague(leve: int, pague: int) -> str | None:
    """Compõe "Leve N pague M" (o outro formato do `PromocaoDialog`). Exige
    leve > pague ≥ 1 (senão não é promoção)."""
    if pague < 1 or leve <= pague:
        return None
    return f"Leve {int(leve)} pague {int(pague)}"

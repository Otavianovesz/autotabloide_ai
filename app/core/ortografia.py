"""Ortografia determinística do vocabulário de mercado (Rodada JM, B1.5).

O OCR devolve nomes sem acento ("ACUCAR", "SABAO") ou com o acento
errado ("PÔ" no lugar de "PÓ") e, às vezes, uma palavra quebrada no
espaço errado ("INTE GRAL"). Nada disso é semântica — é grafia — e a
correção pode ser determinística, desde que o vocabulário seja
INEQUÍVOCO no domínio: só entra no seed a palavra que, num
supermercado, tem uma forma certa única. O ambíguo fica de fora por
regra ("maca" NÃO vira "maçã": maca peruana é produto real de
prateleira — o caso-limite escrito junto com a regra).

A comparação é sem caixa e sem acento (por isso "PÔ" e "PO" caem na
mesma chave "po" → "pó") e a caixa do molde é preservada ("PO"→"PÓ",
"Po"→"Pó", "po"→"pó"). O dono estende o seed pela Config
('sanitizacao.ortografia'), no mesmo padrão do glossário de siglas.
"""

from __future__ import annotations

import re
import unicodedata

# Vocabulário de mercado com forma certa ÚNICA (chave: minúscula, sem
# acento). Conservador de propósito — na dúvida, a palavra NÃO entra.
ACENTOS_MERCADO: dict[str, str] = {
    "acucar": "açúcar",
    "po": "pó",
    "pao": "pão",
    "sabao": "sabão",
    "feijao": "feijão",
    "macarrao": "macarrão",
    "limao": "limão",
    "mamao": "mamão",
    "oleo": "óleo",
    "cafe": "café",
    "cha": "chá",
    "acai": "açaí",
    "pessego": "pêssego",
    "pimentao": "pimentão",
    "requeijao": "requeijão",
    "file": "filé",
    "picole": "picolé",
    "pure": "purê",
    "algodao": "algodão",
    "linguica": "linguiça",
    # QUINTUSDECIMUS/J16 — typos de OCR medidos na tabela real
    "picoca": "pipoca",
}

# Palavra quebrada no espaço errado pelo OCR — bigrama conhecido volta a
# ser UMA palavra. Só o medido no caminho real entra aqui.
BIGRAMAS_QUEBRADOS: dict[str, str] = {
    "inte gral": "integral",
    "de sinfetante": "desinfetante",
    "ole o": "óleo",                # J16: "OLE O de SOJA" da tabela real
    "to scana": "toscana",          # K3: "AZEITONA VERDE TO SCANA"
}

_RE_BORDAS = re.compile(r"^(\W*)(.*?)(\W*)$", re.DOTALL)


def _chave(token: str) -> str:
    """Minúscula e sem acento — a chave de comparação do vocabulário."""
    t = unicodedata.normalize("NFKD", token.lower())
    return "".join(c for c in t if not unicodedata.combining(c))


def com_a_caixa_de(palavra: str, molde: str) -> str:
    """Reveste a palavra com a caixa do molde (o bruto vem em CAIXA
    ALTA; a convenção 1ª-maiúscula continua valendo depois)."""
    if molde.istitle():
        return palavra.capitalize()
    if molde.islower():
        return palavra.lower()
    if molde.isupper():
        return palavra.upper()
    return palavra


def corrigir_acentos(texto: str,
                     extras: tuple[tuple[str, str], ...] = ()) -> str:
    """Corrige a grafia dos tokens conhecidos, preservando a ordem, a
    caixa do molde e a pontuação das bordas. ``extras`` (da Config)
    vence o seed em caso de colisão."""
    if not texto:
        return texto
    # o OCR às vezes devolve o acento DECOMPOSTO (O + circunflexo
    # combinante) — o NFC precompõe antes de qualquer regex/caixa
    texto = unicodedata.normalize("NFC", texto)
    mapa = dict(ACENTOS_MERCADO)
    for errado, certo in extras:
        if errado and certo:
            mapa[_chave(str(errado))] = str(certo)

    # 1) bigramas quebrados (substring com fronteira de palavra)
    for errado, certo in BIGRAMAS_QUEBRADOS.items():
        padrao = re.compile(
            r"\b" + r"\s+".join(map(re.escape, errado.split())) + r"\b",
            re.IGNORECASE)

        def _junta(m: re.Match[str], certo=certo) -> str:
            return com_a_caixa_de(certo, m.group(0).split()[0])

        texto = padrao.sub(_junta, texto)

    # 2) token a token
    saida: list[str] = []
    for token in texto.split(" "):
        m = _RE_BORDAS.match(token)
        pre, nucleo, pos = m.group(1), m.group(2), m.group(3)
        certo = mapa.get(_chave(nucleo)) if nucleo else None
        if certo:
            nucleo = com_a_caixa_de(certo, nucleo)
        saida.append(f"{pre}{nucleo}{pos}")
    return " ".join(saida)

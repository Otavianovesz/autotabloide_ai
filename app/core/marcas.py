"""Vocabulário determinístico de MARCAS do mercado (RODADA-125 v2).

A 2ª prova do dono expôs o "sem padrão nenhum" da célula: a marca ora
ficava na linha grande ("Leite Int. L.V." / "Triângulo"), ora descia
("Leite Integral" / "Parmalat · L.V. · 1L") — porque a divisão era
GEOMÉTRICA (o nome desce só quando não cabe), nunca SEMÂNTICA. A regra
canônica que ele pediu: a linha grande diz O QUE É (tipo); a MARCA
desce ao descritor, sempre.

Para isso o desenho precisa RECONHECER a marca no nome — e o banco real
tem zero marcas preenchidas (medido: 116 produtos, 0 com ``marca``).
Este módulo é o espelho do ``mais18.py``/``ortografia.py``: um seed
CONSERVADOR de marcas inequívocas no domínio do supermercado, somado ao
que o acervo/Config já conhecem. O critério de entrada (o mesmo da
ortografia): só entra a palavra que NUNCA é tipo/qualificador de
produto — o caso-limite escrito junto da regra: "Ninho" fica FORA
(macarrão ninho é produto real), "União" fica FORA (idem, uva união /
uso comum), "Brilhante" fica FORA (adjetivo de prateleira). Na dúvida,
a palavra NÃO entra — o dono estende pela Config (``marcas.proprias``)
ou o acervo aprende na criação (F9: a régua nunca inventa; ela só
reconhece o que é inequívoco ou confirmado).
"""

from __future__ import annotations

import re
import unicodedata

# Marcas inequívocas — as da tabela real do dono primeiro, depois as
# nacionais que nunca são palavra de produto. Multi-palavra permitida.
MARCAS_MERCADO: frozenset[str] = frozenset({
    # a tabela do Jornal do mês (agosto, 2ª prova)
    "omo", "nivea", "pringles", "parmalat", "triangulo", "mabel",
    "yoki", "fugini", "cajamar", "bonare", "gatorade", "amstel",
    "campari", "coqueiro", "mon bijou", "limpol", "doce dia", "somar",
    "tio bonini", "tio jonas", "kitubaina", "kolynos", "bulnez",
    "adoralle",
    # VICESIMUS-QUARTUS §2.2 (o açúcar do Quintou saiu impresso como
    # Doce Dia): a marca da LINHA precisa ser reconhecida para a guarda
    # "marca diferente nunca casa" disparar — Itamaraty nunca é palavra
    # de produto (açúcar/rosquinha do acervo real do dono)
    "itamaraty",
    # "todos" (a marca do açúcar do dono) fica FORA: palavra comum
    # demais — o caso-limite do critério; entra pela Config/acervo
    # encartes anteriores (Quintou/Terça/Segunda) e nacionais inequívocas
    "dori", "ritter", "camil", "prato fino", "tio joao", "kicaldo",
    "piracanjuba", "italac", "elefante", "qualy", "soya", "liza",
    "sadia", "seara", "perdigao", "aurora", "friboi", "ype",
    "minuano", "ariel", "downy", "comfort", "vanish", "colgate",
    "palmolive", "rexona", "heineken", "brahma", "skol", "itaipava",
    "coca-cola", "fanta", "sprite", "pepsi", "senepol",
    # a 1ª prova da hierarquia na página real (03/08): marcas que a
    # régua geométrica salvou por sorte e a semântica deve garantir
    "danone", "gallo", "szura", "concordia", "nestle",
})


def _chave(texto: str) -> str:
    """Minúscula, sem acento, pontuação das bordas fora — a mesma
    disciplina da ortografia."""
    t = unicodedata.normalize("NFKD", (texto or "").lower())
    t = "".join(c for c in t if not unicodedata.combining(c))
    return t.strip("().,;:·")


def marcas_conhecidas(extras: list[str] | tuple[str, ...] = ()) -> set[str]:
    """O vocabulário completo em forma normalizada: o seed + o que o
    chamador somar (acervo/Config). Nunca consulta banco — quem tem
    sessão passa as extras (1× por lote, a lição de desempenho JM)."""
    todas = set(MARCAS_MERCADO)
    for m in extras:
        ch = _chave(str(m))
        if ch:
            todas.add(ch)
    return todas


def marcas_no_nome(nome: str,
                   conhecidas: set[str] | frozenset[str] | None = None,
                   ) -> list[str]:
    """As marcas CONHECIDAS presentes no nome, na ordem em que aparecem,
    com a grafia DO NOME (nunca a do vocabulário — a caixa/acento do
    dono valem). Multi-palavra casa por janela de tokens com fronteira;
    sobreposição prefere a mais longa ("Tio Bonini" vence "Bonini")."""
    if not nome:
        return []
    voc = conhecidas if conhecidas is not None else MARCAS_MERCADO
    tokens = nome.split()
    chaves = [_chave(t) for t in tokens]
    maior_janela = max((len(m.split()) for m in voc), default=1)
    achadas: list[str] = []
    i = 0
    while i < len(chaves):
        melhor_fim = None
        for j in range(min(len(chaves), i + maior_janela), i, -1):
            cand = " ".join(c for c in chaves[i:j] if c)
            if cand and cand in voc:
                melhor_fim = j
                break                      # a janela mais longa primeiro
        if melhor_fim is not None:
            achadas.append(" ".join(tokens[i:melhor_fim]).strip("()"))
            i = melhor_fim
        else:
            i += 1
    return achadas

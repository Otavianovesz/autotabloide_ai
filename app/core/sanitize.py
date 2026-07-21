"""
Sanitização de nomes de produto — camada DETERMINÍSTICA (Fase 1)
================================================================
Aqui só entram regras seguras e previsíveis:

  * caixa: 1ª letra maiúscula, resto minúsculo (respeitando de/da/do... e siglas);
  * unidades: minúsculas (g, kg, ml, mg) exceto **L**; número colado à unidade
    (``5 Kgs`` -> ``5kg``, ``1 LT`` -> ``1L``, ``380 g`` -> ``380g``);
  * limpeza de espaços duplos e lixo óbvio (sequências de ``_`` etc.).

O que as regras **NÃO** fazem (fica para a IA na Fase 3) — mas SINALIZAM como
pendência de alta confiança, para o item ser revisado:

  * erro de digitação semântico (``DE SODORANTE`` -> Desodorante, ``OLE O`` -> Óleo);
  * separar duas marcas (``Carbonell e Gallo``);
  * múltiplos sabores/variantes (``Coco e Leite``, ``FRAGRÂNCIAS``, ``.../...``);
  * detectar categoria e bebida/+18.

IMPORTANTE — o que estas regras **NÃO reordenam**:
o padrão final é Tipo+Marca+Sabor+Peso (peso no fim), mas reordenar com segurança
exige *saber* qual token é marca, sabor ou embalagem — isso é entendimento, ou seja,
trabalho da IA na Fase 3. Aqui só arrumamos caixa/unidades e extraímos o peso; a ordem
dos tokens é preservada. "Já no padrão" quer dizer caixa+unidades corretas, não ordem final.

Regra de ouro: nunca inventar heurística frágil para adivinhar significado.
Ver a memória de projeto "sanitizacao-deterministica".
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field, replace
from decimal import Decimal, InvalidOperation

# ==============================================================================
# CONFIGURAÇÃO (tudo ajustável — os padrões seguem a Documentação-Mestre 3.3)
# ==============================================================================


@dataclass(frozen=True)
class RegrasSanitizacao:
    """Parâmetros configuráveis da sanitização."""

    # Palavras que ficam minúsculas no meio do nome (preposições/conjunções/artigos).
    palavras_minusculas: frozenset[str] = frozenset(
        {
            "de", "da", "do", "das", "dos",
            "e", "ou",
            "em", "na", "no", "nas", "nos",
            "com", "sem", "para", "por",
            "a", "o", "as", "os", "à", "ao", "aos", "às",
            "um", "uma", "uns", "umas",
            "x",  # multiplicador entre números: "12 x 1" fica minúsculo
        }
    )

    # Mapa de unidades -> forma canônica. (a chave é comparada em minúsculo)
    mapa_unidades: tuple[tuple[str, str], ...] = (
        ("mililitros", "ml"), ("mililitro", "ml"), ("mls", "ml"), ("ml", "ml"),
        ("litros", "L"), ("litro", "L"), ("lts", "L"), ("lt", "L"), ("l", "L"),
        ("quilogramas", "kg"), ("quilograma", "kg"), ("quilos", "kg"),
        ("quilo", "kg"), ("kilos", "kg"), ("kilo", "kg"), ("kgs", "kg"), ("kg", "kg"),
        ("miligramas", "mg"), ("miligrama", "mg"), ("mgs", "mg"), ("mg", "mg"),
        ("gramas", "g"), ("grama", "g"), ("grs", "g"), ("gr", "g"), ("g", "g"),
    )

    # Palavras que indicam múltiplas variantes (o item precisa de escolha humana/IA).
    indicadores_variantes: frozenset[str] = frozenset(
        {"sabores", "sabor", "fragrancias", "fragrâncias", "aromas",
         "variados", "varios", "vários", "sortidos", "cores"}
    )

    # Siglas que devem ficar em MAIÚSCULO (glossário editável — espírito DIY).
    # Ex.: "TP" (Tetra Pak). Pode ser sobrescrito pela tabela Config.
    siglas: frozenset[str] = frozenset(
        {"TP", "BB", "XL", "XXL", "TV", "DVD", "CD", "LED"}
    )

    # Glossário de EXPANSÃO de siglas da tabela de ofertas (C1 do Bloco D):
    # "VD" → "vidro", "TP" → "tetra pak"… Vazio por padrão (nada muda sem o
    # usuário pedir); editável pela Config ('sanitizacao.glossario').
    # A expansão roda ANTES da caixa — o resultado ganha a formatação normal.
    glossario_siglas: tuple[tuple[str, str], ...] = ()

    # Caracteres claramente lixo a remover.
    lixo_chars: str = "®©™°"


REGRAS_PADRAO = RegrasSanitizacao()


# ==============================================================================
# RESULTADO
# ==============================================================================


@dataclass
class Pendencia:
    """Um motivo pelo qual o item precisa da IA (Fase 3)."""

    codigo: str
    motivo: str


@dataclass
class ResultadoSanitizacao:
    nome_bruto: str
    nome_sanitizado: str
    peso_valor: Decimal | None = None
    peso_unidade: str | None = None
    pendencias: list[Pendencia] = field(default_factory=list)

    @property
    def precisa_ia(self) -> bool:
        return bool(self.pendencias)


# ==============================================================================
# BLOCOS INTERNOS
# ==============================================================================

_RUNS_LIXO = re.compile(r"[_~]{2,}")        # sequências de _ ou ~ (lixo de OCR)
_MULTI_ESPACO = re.compile(r"\s+")


def _limpar(texto: str, regras: RegrasSanitizacao) -> str:
    """Remove caracteres-lixo, runs de sublinhado e espaços sobrando."""
    for ch in regras.lixo_chars:
        texto = texto.replace(ch, "")
    texto = _RUNS_LIXO.sub(" ", texto)
    return _MULTI_ESPACO.sub(" ", texto).strip()


def _regex_unidades(regras: RegrasSanitizacao) -> re.Pattern[str]:
    chaves = sorted((k for k, _ in regras.mapa_unidades), key=len, reverse=True)
    corpo = "|".join(re.escape(k) for k in chaves)
    # número (com , ou . decimal) seguido, opcionalmente com espaço, da unidade
    return re.compile(rf"(\d+(?:[.,]\d+)?)\s*(?:{corpo})\b", re.IGNORECASE)


def _canonizar_unidade(bruta: str, regras: RegrasSanitizacao) -> str:
    b = bruta.lower()
    for chave, canon in regras.mapa_unidades:
        if b == chave:
            return canon
    return bruta


def _normalizar_unidades(texto: str, regras: RegrasSanitizacao) -> str:
    """Cola número à unidade e canoniza a unidade (5 Kgs -> 5kg, 1 LT -> 1L)."""
    padrao = _regex_unidades(regras)

    def troca(m: re.Match[str]) -> str:
        numero = m.group(1).replace(".", ",")            # decimal no padrão BR
        unidade_bruta = m.group(0)[len(m.group(1)):].strip()
        return f"{numero}{_canonizar_unidade(unidade_bruta, regras)}"

    return padrao.sub(troca, texto)


def _extrair_peso(
    texto: str, regras: RegrasSanitizacao
) -> tuple[Decimal | None, str | None]:
    """Extrai o primeiro (valor, unidade) para gravar nos campos do produto."""
    m = _regex_unidades(regras).search(texto)
    if not m:
        return None, None
    try:
        valor = Decimal(m.group(1).replace(",", "."))
    except InvalidOperation:
        return None, None
    unidade_bruta = m.group(0)[len(m.group(1)):].strip()
    return valor, _canonizar_unidade(unidade_bruta, regras)


def _titulo(token: str, regras: RegrasSanitizacao) -> str:
    if not token:
        return token
    if token[0].isdigit():         # tokens de peso (5kg, 1L, 2x1) ficam intactos
        return token
    return token[0].upper() + token[1:].lower()


def _expandir_glossario(texto: str, regras: RegrasSanitizacao) -> str:
    """Troca siglas do glossário pela forma completa (VD → vidro), por token."""
    if not regras.glossario_siglas:
        return texto
    mapa = {sigla.upper(): expansao
            for sigla, expansao in regras.glossario_siglas if sigla}
    return " ".join(mapa.get(tk.upper(), tk) for tk in texto.split(" ") if tk)


def _aplicar_caixa(texto: str, regras: RegrasSanitizacao) -> str:
    tokens = texto.split(" ")
    saida: list[str] = []
    for i, tk in enumerate(tokens):
        if not tk:
            continue
        if tk[0].isdigit():
            saida.append(tk)                                   # peso: intacto
        elif tk.upper() in regras.siglas:
            saida.append(tk.upper())                           # sigla: TP, BB...
        elif i > 0 and tk.lower() in regras.palavras_minusculas:
            saida.append(tk.lower())                           # de/da/e... no meio
        else:
            saida.append(_titulo(tk, regras))
    return " ".join(saida)


# ==============================================================================
# DETECÇÃO DE PENDÊNCIAS (só sinais estruturais de alta confiança)
# ==============================================================================

_PREPOSICOES_INICIO = {"de", "da", "do", "das", "dos", "e", "ou", "a", "o"}


def _detectar_pendencias(
    nome_bruto: str, texto_norm: str, regras: RegrasSanitizacao
) -> list[Pendencia]:
    """Detecta sinais estruturais de alta confiança.

    ``nome_bruto`` é o texto original (para achar lixo de OCR);
    ``texto_norm`` já vem limpo e com as unidades coladas (``380 g`` -> ``380g``),
    para que unidades soltas não sejam confundidas com letras isoladas.
    """
    pend: list[Pendencia] = []
    tokens = [t for t in texto_norm.split(" ") if t]
    tokens_low = [t.lower() for t in tokens]

    # 1) Lixo de OCR (sequências de sublinhado) — no texto ORIGINAL.
    if _RUNS_LIXO.search(nome_bruto):
        pend.append(Pendencia("lixo", "texto promocional/lixo de OCR — revisar"))

    # 2) Começa com preposição -> provável erro de digitação (DE SODORANTE).
    if tokens_low and tokens_low[0] in _PREPOSICOES_INICIO:
        pend.append(
            Pendencia("prefixo_suspeito",
                      f"começa com '{tokens[0]}' — provável erro de digitação")
        )

    # 3) Letra isolada suspeita (OLE O). Ignora 'x' (multiplicador),
    #    'e'/'ou' (tratados abaixo) e 'a' ('a vácuo').
    for tk in tokens:
        if len(tk) == 1 and tk.isalpha() and tk.lower() not in {"x", "e", "a"}:
            pend.append(
                Pendencia("letra_isolada",
                          f"letra isolada '{tk}' — provável erro de digitação")
            )
            break

    # 4) Múltiplas marcas/sabores/variantes: ' e ', barra, ou palavra indicadora.
    tem_e = " e " in f" {texto_norm.lower()} "
    tem_barra = "/" in texto_norm
    tem_variante = any(t in regras.indicadores_variantes for t in tokens_low)
    if tem_e or tem_barra or tem_variante:
        pend.append(
            Pendencia("multiplos",
                      "possíveis 2 marcas / sabores / variantes — IA/usuário decide")
        )

    return pend


# ==============================================================================
# API PÚBLICA
# ==============================================================================


def formatar_nome(texto: str, regras: RegrasSanitizacao = REGRAS_PADRAO) -> str:
    """
    Formata um nome que JÁ está semanticamente correto (ex.: vindo da IA).

    Aplica só a formatação determinística — limpar, colar unidade (``150 ml`` ->
    ``150ml``), caixa Title Case e siglas. NÃO reordena nem detecta pendências.
    Usado na 2ª etapa do enriquecimento: a IA cuida do sentido, isto do acabamento.
    """
    limpo = _limpar(texto, regras)
    com_unidades = _normalizar_unidades(limpo, regras)
    expandido = _expandir_glossario(com_unidades, regras)
    return _aplicar_caixa(expandido, regras)


def sanitizar(
    nome_bruto: str, regras: RegrasSanitizacao = REGRAS_PADRAO
) -> ResultadoSanitizacao:
    """Sanitiza um nome cru aplicando só as regras determinísticas."""
    limpo = _limpar(nome_bruto, regras)
    peso_valor, peso_unidade = _extrair_peso(limpo, regras)
    com_unidades = _normalizar_unidades(limpo, regras)
    expandido = _expandir_glossario(com_unidades, regras)
    nome = _aplicar_caixa(expandido, regras)

    return ResultadoSanitizacao(
        nome_bruto=nome_bruto,
        nome_sanitizado=nome,
        peso_valor=peso_valor,
        peso_unidade=peso_unidade,
        pendencias=_detectar_pendencias(nome_bruto, com_unidades, regras),
    )

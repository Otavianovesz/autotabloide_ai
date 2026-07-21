"""
Enriquecimento semântico — resolve a lista (b) da sanitização
=============================================================
É a parte que conserta o que as regras determinísticas NÃO conseguem:
erro de digitação (DE SODORANTE→Desodorante), acentos, **reordenar
Tipo+Marca+Sabor+Peso**, categoria e bebida/+18.

⚠️  Só o MODELO REAL prova a qualidade disto. Com o ``MotorIAFake`` validamos só
o encanamento (entra texto → sai estrutura). Sem modelo, cai no determinístico.

Regra travada — 2 marcas / 2 sabores:
  * marcas diferentes que "vão juntas" no mesmo preço  -> ``componentes`` (produtos
    distintos; a composição visual é da Fase 5). NUNCA um nome único remendado.
  * sabores/variantes do MESMO produto -> ``variantes`` (um produto, várias imagens).
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from decimal import Decimal

from app.ai.client import IAIndisponivel, MotorIA
from app.core.sanitize import REGRAS_PADRAO, RegrasSanitizacao, formatar_nome, sanitizar

CATEGORIAS_PADRAO = [
    "Mercearia", "Limpeza", "Bebidas", "Higiene", "Frios", "Padaria",
    "Hortifrúti", "Congelados", "Bazar", "Pet",
]


@dataclass
class Componente:
    """Um produto distinto que compartilha o slot (ex.: Camil e Rei no mesmo preço)."""

    nome_sanitizado: str
    marca: str | None = None


@dataclass
class ProdutoEnriquecido:
    nome_bruto: str
    nome_sanitizado: str
    tipo: str | None = None
    marca: str | None = None
    sabor: str | None = None
    categoria: str | None = None
    peso_valor: Decimal | None = None
    peso_unidade: str | None = None
    bebida_alcoolica: bool = False
    mais18: bool = False
    componentes: list[Componente] = field(default_factory=list)
    variantes: list[str] = field(default_factory=list)
    confianca: float = 0.0
    origem: str = "ia"                 # "ia" ou "deterministico" (degradação)
    observacoes: str | None = None
    # RG-20: palavras do bruto que a IA descartou (regra dura: lista NÃO
    # vazia = o item precisa de revisão humana — nunca aceitar em silêncio)
    tokens_perdidos: list[str] = field(default_factory=list)

    @property
    def multi_produto(self) -> bool:
        return len(self.componentes) > 1


# ==============================================================================
# Prompt
# ==============================================================================

_SISTEMA = """Você padroniza descrições de produtos de supermercado para um encarte.
Devolva SOMENTE um objeto JSON (sem texto fora dele) com as chaves:
  nome_sanitizado, tipo, marca, sabor, categoria, bebida_alcoolica, mais18,
  componentes (lista de {nome_sanitizado, marca}), variantes (lista de textos),
  confianca (0..1), observacoes.

Regras:
- Ordem do nome: {ordem} — o PESO é SEMPRE o
  último (ex.: "Doce de Leite Firmesa Original 400g"; NUNCA "400g Original").
- NUNCA remova palavras da descrição original: sabor, variante ("Original",
  "Tradicional"), apelidos e siglas de marca ("Val", "BBX") FICAM no nome.
  Você reordena, corrige caixa e acentos — não resume.
- Unidades minúsculas (g, kg, ml) exceto L; número colado (500g, 1kg, 2L).
- Corrija erros de digitação e acentos (ex.: "DE SODORANTE"→"Desodorante", "OLE O"→"Óleo").
- categoria: uma de {categorias}.
- Marque bebida_alcoolica e mais18 quando for álcool (cerveja, vinho, vodka...).
- DUAS MARCAS diferentes no mesmo item (ex.: "Carbonell e Gallo") -> preencha
  "componentes" com um produto para cada marca. NÃO junte num nome só.
- SABORES/variantes do mesmo produto (ex.: "Coco e Leite", "Original e Light")
  -> preencha "variantes". Deixe "componentes" vazio nesse caso.
"""

# --- RG-20: a REGRA DURA — nenhuma palavra do bruto pode sumir ---------------------

_STOPWORDS = {"de", "da", "do", "das", "dos", "com", "em", "e", "para", "por",
              "a", "o", "as", "os", "un", "und", "cx", "pct"}


def _normalizar_token(t: str) -> str:
    import unicodedata
    t = unicodedata.normalize("NFKD", t.lower())
    return "".join(c for c in t if c.isalnum())


def tokens_perdidos(bruto: str, sanitizado: str) -> list[str]:
    """RG-20: tokens SIGNIFICATIVOS do bruto que sumiram do sanitizado.

    A auditoria pegou a IA descartando "Original" e "Val" — a regra dura:
    todo token do original precisa sobreviver (reordenado/acentuado é ok:
    a comparação é sem caixa/acento e por SUBSTRING, então o typo corrigido
    "OLE O"→"Óleo" não acusa; já "Huppers"→"Ruppers" ACUSA — typo de
    fornecedor é sugerido, nunca trocado sozinho). Stopwords e fragmentos
    de 1-2 letras ficam de fora para não gritar à toa.
    """
    alvo = [_normalizar_token(t) for t in sanitizado.split()]
    perdidos = []
    for original in bruto.split():
        tok = _normalizar_token(original)
        if len(tok) < 3 or tok in _STOPWORDS:
            continue
        if not any(tok in cand or cand in tok for cand in alvo if cand):
            perdidos.append(original)
    return perdidos


def tokens_inventados(bruto: str, sanitizado: str,
                      permitidos=()) -> list[str]:
    """OS F11.5 #78/#95 — o INVERSO do RG-20: tokens significativos que a IA
    ACRESCENTOU sem existirem no original. Sigla, protocolo e marca nunca
    nascem do nada (decisão travada da F9) — só sobrevive o que veio do bruto
    ou do glossário CONFIRMADO pelo dono (`permitidos`)."""
    base = [_normalizar_token(t) for t in bruto.split()]
    liberados = {_normalizar_token(t)
                 for p in permitidos if p for t in str(p).split()}
    inventados = []
    for original in sanitizado.split():
        tok = _normalizar_token(original)
        if len(tok) < 3 or tok in _STOPWORDS or tok in liberados:
            continue
        if not any(tok in cand or cand in tok for cand in base if cand):
            inventados.append(original)
    return inventados


def remover_inventados(nome: str, bruto: str, permitidos=()) -> str:
    """#78/#95: tira do nome os tokens inventados (a guarda DURA, não pedido
    no prompt). Se sobrar nada, devolve o nome como veio (nunca apaga tudo)."""
    inv = set(tokens_inventados(bruto, nome, permitidos))
    if not inv:
        return nome
    sobrou = " ".join(t for t in nome.split() if t not in inv)
    return sobrou or nome


def dica_alucinada(dica: str, nomes: list[str],
                   marcas_conhecidas=()) -> bool:
    """OS F11.5 #12: checagem anti-alucinação do TEXTO da dica — a dica não
    pode afirmar número de dinheiro/desconto (preço é papel do encarte, nunca
    da dica) nem citar uma MARCA conhecida que não está nos itens da oferta."""
    import re as _re
    d = (dica or "").lower()
    if _re.search(r"(r\$\s?\d|\d+\s?%)", d):
        return True
    toks_dica = {_normalizar_token(t) for t in (dica or "").split()}
    toks_itens = {_normalizar_token(t)
                  for nome in nomes for t in str(nome).split()}
    for marca in marcas_conhecidas or ():
        m_toks = [_normalizar_token(t) for t in str(marca).split()]
        if not m_toks or any(len(t) < 3 for t in m_toks):
            continue
        na_dica = all(t in toks_dica for t in m_toks)
        nos_itens = all(t in toks_itens for t in m_toks)
        if na_dica and not nos_itens:
            return True
    return False


# FASE 3 (passo 51): a ordem do nome é editável na aba Sanitização
ORDEM_NOME_PADRAO = ("Tipo", "Marca", "Sabor/Variante", "Peso")


def ordem_do_nome() -> tuple[str, ...]:
    """A ordem da Config (``sanitizacao.ordem``) — precisa ter os MESMOS
    4 blocos (só reordenados); qualquer coisa diferente cai no padrão."""
    try:
        from app.core.database import Database
        from app.core.repositories import ConfigRepositorio
        db = Database().init()
        try:
            with db.Session() as s:
                bruta = ConfigRepositorio(s).get("sanitizacao.ordem")
        finally:
            db.engine.dispose()
        if (isinstance(bruta, list)
                and sorted(bruta) == sorted(ORDEM_NOME_PADRAO)):
            return tuple(bruta)
    except Exception:
        pass
    return ORDEM_NOME_PADRAO


def _montar_mensagens(nome_bruto: str, categorias: list[str]) -> list[dict]:
    sistema = (_SISTEMA
               .replace("{categorias}", ", ".join(categorias))
               .replace("{ordem}", " + ".join(ordem_do_nome())))
    return [
        {"role": "system", "content": sistema},
        {"role": "user", "content": f'Descrição bruta: "{nome_bruto}"'},
    ]


# ==============================================================================
# Parsing e montagem
# ==============================================================================


def _extrair_json(texto: str) -> dict:
    t = texto.strip()
    if t.startswith("```"):
        t = t.strip("`")
        if t.lower().startswith("json"):
            t = t[4:]
    ini, fim = t.find("{"), t.rfind("}")
    if ini == -1 or fim == -1:
        raise ValueError("resposta sem JSON")
    return json.loads(t[ini : fim + 1])


def _norm_categoria(cat: str | None) -> str | None:
    """Casa a categoria da IA com a lista canônica (ignora caixa); senão capitaliza."""
    if not cat:
        return None
    for c in CATEGORIAS_PADRAO:
        if c.lower() == cat.strip().lower():
            return c
    return cat.strip().capitalize()


def _degradado(nome_bruto: str, base) -> ProdutoEnriquecido:
    """Sem IA: usa só o determinístico da Fase 1 (nome pode não estar na ordem final)."""
    return ProdutoEnriquecido(
        nome_bruto=nome_bruto,
        nome_sanitizado=base.nome_sanitizado,
        peso_valor=base.peso_valor,
        peso_unidade=base.peso_unidade,
        confianca=0.0,
        origem="deterministico",
        observacoes="IA indisponível — resultado apenas determinístico (revisar).",
    )


def _montar(nome_bruto: str, dados: dict, base, regras: RegrasSanitizacao) -> ProdutoEnriquecido:
    # 2ª etapa: o formatador determinístico da F1 arruma caixa/unidade por cima
    # do que a IA devolveu (sentido da IA + acabamento das regras).
    componentes = [
        Componente(
            nome_sanitizado=formatar_nome(c["nome_sanitizado"], regras),
            marca=c.get("marca"),
        )
        for c in dados.get("componentes", [])
        if c.get("nome_sanitizado")
    ]
    nome = dados.get("nome_sanitizado") or base.nome_sanitizado
    return ProdutoEnriquecido(
        nome_bruto=nome_bruto,
        nome_sanitizado=formatar_nome(nome, regras),
        tipo=dados.get("tipo"),
        marca=dados.get("marca"),
        sabor=dados.get("sabor"),
        categoria=_norm_categoria(dados.get("categoria")),
        peso_valor=base.peso_valor,           # peso vem do determinístico (confiável)
        peso_unidade=base.peso_unidade,
        bebida_alcoolica=bool(dados.get("bebida_alcoolica", False)),
        mais18=bool(dados.get("mais18", False)),
        componentes=componentes,
        variantes=[v for v in dados.get("variantes", []) if v],
        confianca=float(dados.get("confianca", 0.0)),
        origem="ia",
        observacoes=dados.get("observacoes"),
    )


# ==============================================================================
# Sugestão de variantes (F7.1, C1 do Bloco E)
# ==============================================================================

def sugerir_variantes(nome: str, motor: MotorIA | None) -> list[str]:
    """A IA sugere TERMOS de busca (sabores/fragrâncias prováveis) — SÓ termos.

    A trava anti-alucinação da visão: **quem escolhe as fotos é o humano**;
    a IA nunca decide imagem nenhuma. Sem motor, sem resposta ou resposta
    ruim → lista vazia (a busca manual continua; sugestão é assistência,
    não dependência).
    """
    if motor is None or not motor.disponivel():
        return []
    try:
        resposta = motor.chat([
            {"role": "system", "content":
             "Você lista variantes plausíveis (sabores, fragrâncias ou "
             "versões) de um produto de supermercado brasileiro. Devolva "
             'SOMENTE JSON: {"variantes": ["termo curto", ...]} — no máximo '
             "6. Se não conhecer o produto, devolva a lista VAZIA. NUNCA "
             "invente variantes improváveis."},
            {"role": "user", "content": nome},
        ], formato_json=True, max_tokens=256)
        dados = json.loads(resposta)
        vistos: set[str] = set()
        saida: list[str] = []
        for v in dados.get("variantes", []):
            v = str(v).strip()
            if v and v.lower() not in vistos:
                vistos.add(v.lower())
                saida.append(v)
        return saida[:6]
    except (IAIndisponivel, json.JSONDecodeError, TypeError, AttributeError):
        return []          # sugestão é opcional: degradar aqui não cala conteúdo


# ==============================================================================
# "Fica a Dica" por IA (RG-25)
# ==============================================================================


def limite_caracteres(larg_mm: float, alt_mm: float,
                      tamanho_pt: float) -> int:
    """RG-25: quantos caracteres CABEM na região (área ÷ tamanho da fonte).

    Heurística documentada: um caractere na fonte de T pt ocupa
    ~0,55·T pt de largura por ~1,3·T pt de altura (1 pt = 0,3528 mm).
    Piso de 40 (dica menor que isso não diz nada) e teto de 600.
    """
    pt_mm = 0.3528
    area_char_mm2 = (0.55 * tamanho_pt * pt_mm) * (1.3 * tamanho_pt * pt_mm)
    if area_char_mm2 <= 0:
        return 40
    return max(40, min(600, int((larg_mm * alt_mm) / area_char_mm2)))


# FASE 3 (passo 45, R-088): o prompt é EDITÁVEL na aba IA (chave
# ``ia.prompt_dica``); {limite} é trocado pelo teto da região na hora.
PROMPT_DICA_PADRAO = (
    "Você escreve o quadro “Fica a Dica” de um encarte de "
    "supermercado brasileiro: UMA dica curta, receita rápida ou "
    "curiosidade simpática usando produtos da oferta. Tom leve, "
    "direto, sem emoji, sem hashtag. Devolva SOMENTE JSON: "
    '{"dica": "texto com NO MÁXIMO {limite} caracteres"}')


def prompt_dica(limite_chars: int) -> str:
    """O prompt do Fica-a-Dica: o da Config se houver, senão o padrão.

    Troca por replace (não .format) — o texto tem chaves de JSON e o
    usuário pode digitar { } sem quebrar nada."""
    texto = ""
    try:
        from app.core.database import Database
        from app.core.repositories import ConfigRepositorio
        db = Database().init()
        try:
            with db.Session() as s:
                texto = str(ConfigRepositorio(s).get("ia.prompt_dica")
                            or "").strip()
        finally:
            db.engine.dispose()
    except Exception:
        texto = ""
    return (texto or PROMPT_DICA_PADRAO).replace("{limite}",
                                                 str(limite_chars))


# R-083: os estilos escolhíveis da dica — a instrução extra por estilo.
ESTILOS_DICA: dict[str, str] = {
    "receita": "Faça no formato de RECEITA rápida (um preparo simples com os itens).",
    "economia": "Foque na ECONOMIA (como render mais, aproveitar, comprar bem).",
    "curiosidade": "Traga uma CURIOSIDADE simpática sobre um dos itens.",
}


def gerar_dica(nomes: list[str], limite_chars: int,
               motor: MotorIA | None, *, estilo: str | None = None,
               evitar: list[str] | None = None,
               marcas_conhecidas: list[str] | None = None) -> str | None:
    """Gera a dica/receita/curiosidade a partir dos itens da oferta.

    `estilo` (R-083: receita·economia·curiosidade) muda o tom; `evitar` (R-083
    memória) lista dicas recentes para não repetir. None = sem motor/sem resposta
    útil (quem chama avisa — I2; a dica é assistência). O limite vem da REGIÃO."""
    if motor is None or not motor.disponivel() or not nomes:
        return None
    instrucao = ESTILOS_DICA.get(estilo or "", "")
    if evitar:
        instrucao += (" NÃO repita nem se pareça com estas dicas recentes: "
                      + " | ".join(evitar[:5]))
    try:
        resposta = motor.chat([
            {"role": "system", "content": prompt_dica(limite_chars)},
            {"role": "user", "content": "Itens da oferta: " + "; ".join(nomes)
             + (f"\n{instrucao}" if instrucao else "")},
        ], formato_json=True, max_tokens=400)
        dica = str(json.loads(resposta).get("dica") or "").strip()
        if not dica:
            return None
        # GATE 2.1 (ordem F11.5): a memória anti-repetição é GUARDA DURA, não
        # pedido educado no prompt — se o modelo devolver uma dica igual (ou
        # contida numa) das recentes, ela é REJEITADA (None; o caller avisa).
        # Assim "não repete" é comportamento provável por teste, não promessa.
        def _norm(s: str) -> str:
            return " ".join(s.lower().split())
        if evitar and any(_norm(dica) == _norm(e) or _norm(dica) in _norm(e)
                          or _norm(e) in _norm(dica)
                          for e in evitar if e and e.strip()):
            return None
        # OS F11.5 #12: anti-alucinação — dica com preço/% inventado ou
        # marca conhecida que NÃO está na oferta é rejeitada (guarda dura)
        if dica_alucinada(dica, nomes, marcas_conhecidas or ()):
            return None
        return dica[:limite_chars]        # o teto da região é lei
    except (IAIndisponivel, json.JSONDecodeError, TypeError, AttributeError):
        return None


_MANCHETES_PADRAO = [
    "Ofertas da semana", "Preços que cabem no seu bolso", "Só nesta semana",
    "Aproveite enquanto dura", "Economia de verdade pra sua casa",
]


def sugerir_manchetes(evento: str | None, motor: MotorIA | None, *,
                      limite_chars: int | None = None) -> list[str]:
    """R-074: sugere CHAMADAS para o evento (o dono escolhe/edita — nunca
    imposição). Sem IA, devolve uma lista padrão (degrada com o app funcionando).
    Respeita o limite da região (não estoura o espaço) quando informado."""
    def _cortar(lista):
        if limite_chars:
            return [m[:limite_chars] for m in lista if m]
        return [m for m in lista if m]

    if motor is None or not motor.disponivel():
        base = _MANCHETES_PADRAO
        if evento:
            base = [f"{evento} — preços que gritam", *base]
        return _cortar(base)[:5]
    try:
        ev = evento or "as ofertas da semana"
        resposta = motor.chat([
            {"role": "system", "content":
             "Você cria manchetes curtas e vendedoras para o topo de um encarte "
             "de supermercado brasileiro. Devolva SOMENTE JSON: "
             '{"manchetes": ["...", "..."]} com 5 opções curtas, sem emoji.'},
            {"role": "user", "content": f"Evento/tema: {ev}"},
        ], formato_json=True, max_tokens=300)
        lista = [str(m).strip() for m in json.loads(resposta).get("manchetes", [])
                 if str(m).strip()]
        return _cortar(lista)[:5] or _cortar(_MANCHETES_PADRAO)[:5]
    except (IAIndisponivel, json.JSONDecodeError, TypeError, AttributeError):
        return _cortar(_MANCHETES_PADRAO)[:5]


# ==============================================================================
# API
# ==============================================================================


def enriquecer(
    nome_bruto: str,
    motor: MotorIA,
    *,
    categorias: list[str] | None = None,
    regras: RegrasSanitizacao = REGRAS_PADRAO,
) -> ProdutoEnriquecido:
    """Enriquece um nome cru. Degrada para o determinístico se a IA não responder."""
    base = sanitizar(nome_bruto, regras)
    if not motor.disponivel():
        return _degradado(nome_bruto, base)
    try:
        resposta = motor.chat(
            _montar_mensagens(nome_bruto, categorias or CATEGORIAS_PADRAO),
            formato_json=True,
        )
        dados = _extrair_json(resposta)
    except (IAIndisponivel, ValueError, json.JSONDecodeError):
        return _degradado(nome_bruto, base)
    if not dados:
        return _degradado(nome_bruto, base)
    enr = _montar(nome_bruto, dados, base, regras)
    # OS F11.5 #78/#95: sigla/protocolo/marca INVENTADA pela IA cai aqui —
    # só sobrevive o que veio do bruto ou do glossário do dono (expansões
    # confirmadas). Guarda dura, roda SEMPRE sobre o nome final.
    permitidos = [exp for _sig, exp in (regras.glossario_siglas or ())]
    enr.nome_sanitizado = remover_inventados(enr.nome_sanitizado, nome_bruto,
                                             permitidos)
    # RG-20: a regra dura roda SEMPRE, sobre o resultado final da IA.
    # Multi-produto (componentes) reparte o nome de propósito — a regra
    # compara contra o conjunto completo (nome + componentes + variantes).
    conjunto = " ".join([enr.nome_sanitizado]
                        + [c.nome_sanitizado for c in enr.componentes]
                        + enr.variantes)
    enr.tokens_perdidos = tokens_perdidos(nome_bruto, conjunto)
    return enr

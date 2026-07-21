"""
Inteligência do negócio — SÓ LEITURA (R-115/117/120/121/122/123/126, Fase 11)
=============================================================================
Serviço direto ao dono: ver o histórico, comparar, medir — sem NUNCA mudar o
acervo e sem NADA sair da máquina (local). Coerente com os vetos e o offline.

**VETADOS — não construir (R-116/119/124/125):** custo/margem/lucro, diário de
alterações, backup em nuvem, ERP. Aqui só entra preço de OFERTA e presença de
dado. A varredura de vetos (Bloco D) prova a ausência.

Todas as funções de série de dados são PURAS e recebem as edições como entrada
(injetável) — os testes ficam determinísticos e o boot não pesa. As datas
vêm de ``projetos.historico_edicoes`` (mais antiga→recente). A identidade é
sempre a **chave natural** (I1), nunca a posição/nome cru.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta
from decimal import Decimal

from app.qt.telas.servico import OUTROS, ItemMesa, chave_natural, preco_decimal


def _itens(ed: dict) -> list[ItemMesa]:
    return [ItemMesa.from_dict(d) for d in ed.get("itens", [])]


def _dia(quando) -> date | None:
    if isinstance(quando, datetime):
        return quando.date()
    return quando if isinstance(quando, date) else None


# --- R-115: histórico de preço por produto -----------------------------------------

@dataclass
class PontoPreco:
    quando: datetime | None
    preco: Decimal
    nome: str
    evento: str


def historico_de_preco(edicoes: list[dict]) -> dict[tuple, list[PontoPreco]]:
    """R-115: por produto (chave natural, I1), a série de preços ao longo das
    edições em que ele entrou. Só pontos com preço ENTENDIDO (preco_decimal);
    sem dado, sem ponto inventado (I2)."""
    serie: dict[tuple, list[PontoPreco]] = {}
    for ed in edicoes:
        vistos: set[tuple] = set()          # 1 ponto por produto POR edição
        for it in _itens(ed):               # (mesmo dedup do ranking, I1 — o
            k = chave_natural(it)           #  "Duplicar item" mantém produto_id
            if k in vistos:                 #  → 2 itens, mesma chave, mesma data)
                continue
            p = preco_decimal(it.preco)
            if p is None:                   # sem preço não consome o slot: uma
                continue                    # cópia posterior com preço ainda conta
            vistos.add(k)
            serie.setdefault(k, []).append(
                PontoPreco(ed.get("criado_em"), p, it.nome, ed.get("evento", "")))
    return serie


def serie_de_um(edicoes: list[dict], item_ou_chave) -> dict:
    """R-115: a série de UM produto + o MENOR preço do histórico marcado.

    ``item_ou_chave`` pode ser um ItemMesa ou a chave natural já pronta.
    Devolve {pontos, menor, menor_marcado} — ``menor`` None se sem histórico."""
    chave = (item_ou_chave if isinstance(item_ou_chave, tuple)
             else chave_natural(item_ou_chave))
    pontos = historico_de_preco(edicoes).get(chave, [])
    menor = min((p.preco for p in pontos), default=None)
    return {"pontos": pontos, "menor": menor,
            "menor_marcado": [p for p in pontos if menor is not None
                              and p.preco == menor]}


# --- R-120: ranking dos mais ofertados ---------------------------------------------

def ranking_ofertados(edicoes: list[dict], top: int | None = None) -> list[dict]:
    """R-120: em quantas edições cada produto entrou — os carros-chefe. Conta
    1 por edição (por chave natural, I1). Ordena por contagem, depois nome."""
    cont: dict[tuple, int] = {}
    nomes: dict[tuple, str] = {}
    for ed in edicoes:
        vistos: set[tuple] = set()
        for it in _itens(ed):
            k = chave_natural(it)
            if k in vistos:
                continue
            vistos.add(k)
            cont[k] = cont.get(k, 0) + 1
            nomes[k] = it.nome
    ordenado = sorted(cont.items(), key=lambda kv: (-kv[1], nomes.get(kv[0], "")))
    saida = [{"chave": k, "nome": nomes[k], "edicoes": n} for k, n in ordenado]
    return saida[:top] if top else saida


# --- R-121: memória sazonal --------------------------------------------------------

def memoria_sazonal(edicoes: list[dict], hoje: date | None = None, *,
                    anos: int = 1, janela_dias: int = 10) -> list[dict]:
    """R-121: "ano passado nesta semana você ofertou X" — os produtos das
    edições ~52 semanas atrás (dentro de ``janela_dias`` do mesmo dia do ano).
    Sugestão, não imposição — lê o histórico por data + chave natural."""
    if hoje is None:
        hoje = date.today()
    alvo = hoje - timedelta(days=365 * anos)
    produtos: dict[tuple, str] = {}
    for ed in edicoes:
        d = _dia(ed.get("criado_em"))
        if d is None or abs((d - alvo).days) > janela_dias:
            continue
        for it in _itens(ed):
            produtos.setdefault(chave_natural(it), it.nome)
    return [{"chave": k, "nome": v} for k, v in produtos.items()]


# --- R-117: relatório da edição ----------------------------------------------------

def relatorio_edicao(itens: list[ItemMesa]) -> dict:
    """R-117: resumo do estado REAL da edição — itens por categoria, faixa de
    preços e quantos sem foto. Conversa com o checklist da F7 (não inventa)."""
    from app.qt.telas.servico import checklist_final

    por_categoria: dict[str, int] = {}
    precos: list[Decimal] = []
    sem_foto = 0
    for it in itens:
        cat = (it.categoria or OUTROS)
        por_categoria[cat] = por_categoria.get(cat, 0) + 1
        p = preco_decimal(it.preco)
        if p is not None:
            precos.append(p)
        if not (it.imagem or it.imagens):
            sem_foto += 1
    medio = (sum(precos) / len(precos)) if precos else None
    return {
        "total": len(itens),
        "por_categoria": dict(sorted(por_categoria.items())),
        "sem_foto": sem_foto,
        "preco_min": min(precos) if precos else None,
        "preco_max": max(precos) if precos else None,
        "preco_medio": medio,
        "checklist": checklist_final(itens, None),
    }


# --- R-123: alerta de preço divergente entre páginas -------------------------------

def divergencia_de_precos(ocorrencias: list[tuple]) -> list[dict]:
    """R-123: `ocorrencias` = lista de (identidade, nome, preco, pagina).

    Agrupa por IDENTIDADE (uid/chave natural, I1) e devolve os grupos com mais
    de um preço DISTINTO — a divergência REAL, não coincidência de nome. Cada
    grupo: {identidade, nome, precos: {preço→[páginas]}}."""
    grupos: dict = {}
    for ident, nome, preco, pagina in ocorrencias:
        g = grupos.setdefault(ident, {"nome": nome, "precos": {}})
        g["precos"].setdefault(preco, []).append(pagina)
    saida = []
    for ident, g in grupos.items():
        if len(g["precos"]) > 1:
            saida.append({
                "identidade": ident, "nome": g["nome"],
                "precos": {str(p): pgs for p, pgs in g["precos"].items()}})
    return saida


def divergencias_no_mapa(dados_por_slot: dict, mapa: dict) -> list[dict]:
    """R-123 direto do estado da Mesa: agrupa os slots pela IDENTIDADE do item
    (uid, I1) e acha os que saem com preços diferentes — o MESMO item em dois
    lugares com preços divergentes (via override). O slot já localiza; não
    precisa do layout. Coincidência de nome (uids diferentes) nunca dispara."""
    oc: list[tuple] = []
    for slot_id, d in dados_por_slot.items():
        if d is None or d.preco_por is None:
            continue
        ident = mapa.get(slot_id) or slot_id
        oc.append((ident, d.nome, d.preco_por, slot_id))
    return divergencia_de_precos(oc)


def ocorrencias_do_encarte(layout, dados_por_slot: dict, mapa: dict) -> list[tuple]:
    """Monta as ocorrências (identidade, nome, preço, página) de um encarte,
    para o alerta de divergência. A identidade é o **uid** do item no slot (I1)
    — o MESMO item em duas páginas com preços diferentes é a divergência real.
    """
    ocorrencias: list[tuple] = []
    for n, pagina in enumerate(getattr(layout, "paginas", []), start=1):
        for slot in pagina.slots:
            d = dados_por_slot.get(slot.id)
            if d is None or d.preco_por is None:
                continue
            ident = mapa.get(slot.id) or slot.id       # uid do item (I1)
            ocorrencias.append((ident, d.nome, d.preco_por, n))
    return ocorrencias


# --- R-122: meta por evento (do dono, informativa) ---------------------------------

def _chave_meta(evento: str) -> str:
    return f"meta.evento.{(evento or '').strip().lower()}"


def definir_meta_evento(evento: str, meta: int, raiz=None) -> None:
    """R-122: o dono define uma meta simples por evento ("40 itens no Quintou").
    Guarda na Config (NÃO no acervo) — é preferência do dono, não dado de produto."""
    from app.core.database import Database
    from app.core.repositories import ConfigRepositorio

    db = Database(raiz).init() if raiz else Database().init()
    try:
        with db.Session() as s:
            ConfigRepositorio(s).set(_chave_meta(evento), int(meta))
            s.commit()
    finally:
        db.engine.dispose()


def meta_evento(evento: str, raiz=None) -> int | None:
    from app.core.database import Database
    from app.core.repositories import ConfigRepositorio

    db = Database(raiz).init() if raiz else Database().init()
    try:
        with db.Session() as s:
            v = ConfigRepositorio(s).get(_chave_meta(evento))
            return int(v) if v is not None else None
    finally:
        db.engine.dispose()


def progresso_meta(evento: str, n_atual: int, raiz=None) -> dict:
    """R-122: o pulso da montagem ("32/40") — informativo, sem cobrança. Sem
    meta definida, devolve só o total atual."""
    meta = meta_evento(evento, raiz=raiz)
    return {"evento": evento, "meta": meta, "atual": n_atual,
            "texto": f"{n_atual}/{meta}" if meta else f"{n_atual} item(ns)",
            "atingiu": bool(meta and n_atual >= meta)}


# --- R-126: saúde do acervo com metas ----------------------------------------------

def saude_acervo(raiz=None) -> dict:
    """R-126: painel de saúde — quantos produtos com foto, com EAN, com preço,
    com categoria (presença de dado, I2). SÓ LEITURA. Sem custo/margem (veto)."""
    from sqlalchemy import select

    from app.core.database import Database
    from app.core.models import Produto

    db = Database(raiz).init() if raiz else Database().init()
    try:
        with db.Session() as s:
            prods = list(s.execute(select(Produto).where(
                Produto.excluido_em.is_(None))).scalars())
            total = len(prods)
            com_foto = sum(1 for p in prods if p.caminho_imagem)
            com_ean = sum(1 for p in prods if (p.ean or "").strip())
            com_preco = sum(1 for p in prods if p.preco_atual is not None)
            com_categoria = sum(1 for p in prods if p.categoria_id is not None)
    finally:
        db.engine.dispose()

    def _pct(n):
        return round(100 * n / total) if total else 0

    return {
        "total": total,
        "com_foto": com_foto, "pct_foto": _pct(com_foto),
        "com_ean": com_ean, "pct_ean": _pct(com_ean),
        "com_preco": com_preco, "pct_preco": _pct(com_preco),
        "com_categoria": com_categoria, "pct_categoria": _pct(com_categoria),
    }


# OS F11.5 #51/#52 (R-126): as METAS simples do acervo — o alvo de cada
# métrica; abaixo do alvo o painel acende "abaixo da meta"
METAS_SAUDE = {"pct_foto": 90, "pct_categoria": 80,
               "pct_preco": 90, "pct_ean": 40}


def saude_com_metas(raiz=None, max_avaliadas: int = 120) -> dict:
    """OS F11.5 #51/#52: a saúde (R-126) com METAS/limiares por métrica +
    a INTEGRIDADE R-129 (órfãs/aponta-pro-nada, só leitura) + a NOTA das
    fotos (avaliador F9, numa amostra) — a visão única do acervo. SÓ LEITURA
    como sempre; qualquer perna que falhe degrada com o campo ausente (I2
    é do chamador exibir o que veio)."""
    s = saude_acervo(raiz)
    s["metas"] = {chave: {"alvo": alvo, "ok": s.get(chave, 0) >= alvo}
                  for chave, alvo in METAS_SAUDE.items()}
    try:                                    # R-129: integridade, só contagem
        from app.core.manutencao import verificar_acervo
        r = verificar_acervo(getattr(raiz, "raiz", raiz))
        s["orfas"] = len(r.get("orfas", []))
        s["sem_arquivo"] = len(r.get("sem_arquivo", []))
    except Exception:
        pass
    try:                                    # F9: nota das fotos (amostra)
        from app.core.paths import SystemRoot

        from app.images.avaliador import avaliar_foto
        raiz_bib = (raiz.biblioteca_imagens if raiz
                    else SystemRoot().biblioteca_imagens)
        ruins = avaliadas = 0
        for pasta in sorted(raiz_bib.iterdir()) if raiz_bib.exists() else []:
            if avaliadas >= max_avaliadas:
                break
            if not pasta.is_dir() or pasta.name.startswith("_"):
                continue
            atual = next((pasta / n for n in ("atual.png", "atual.webp")
                          if (pasta / n).is_file()), None)
            if atual is None:
                continue
            avaliadas += 1
            if avaliar_foto(atual).nota == "ruim":
                ruins += 1
        s["fotos_avaliadas"] = avaliadas
        s["fotos_ruins"] = ruins
    except Exception:
        pass
    return s

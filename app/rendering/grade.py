"""
Grade do tabloide (F5.5)
========================
Auto-detecta as caixas de preço vermelhas da arte, deriva a grade, e replica a
célula-mestre (Imagem/Nome/Preço) em cada posição. Cada célula vira um Slot; a
composição desenha um produto DIFERENTE por slot (mapa slot→produto).

**Propagação da mestra + override por célula:** editar a célula-mestre propaga
estilo e geometria (relativa à âncora de cada célula) para todas as cópias —
exceto os atributos que a célula sobrescreveu (``Regiao.overrides``), que têm
precedência e persistem (mesmo princípio do projeto congelado da visão).

A detecção usa só numpy (o cv2 do ambiente está com ABI quebrada).
"""

from __future__ import annotations

import uuid

from app.rendering.model import (
    Ajuste,
    Alinhamento,
    LayoutDef,
    Pagina,
    PapelPreco,
    Regiao,
    Retangulo,
    Slot,
    SubtipoPreco,
    TipoRegiao,
    layout_de_arte,
)
from app.rendering.units import px_para_mm

DPI_PADRAO = 96

# O que propaga da mestra (estilo). Geometria (rect) propaga à parte, relativa
# à âncora. NÃO propagam: visivel/travado (estado de trabalho de cada célula)
# e nome (rótulo da camada).
ATRIBUTOS_ESTILO = (
    "fonte", "tamanho_max_pt", "tamanho_min_pt", "cor", "alinhamento",
    "incluir_unidade", "subtipo_preco", "papel_preco", "tamanho_centavos_pt",
    "fonte_centavos", "mostrar_moeda", "riscado", "ajuste",
    "estilo",   # F5.7: o VÍNCULO de estilo nomeado propaga (overrides_estilo não)
    "rotacao_graus",   # RG-12: a data deitada da mestra replica nas células
    # Fase 5 (I4): máscara/legibilidade/papel da mestra replicam nas cópias —
    # editar a célula-mestre muda "em todos os lugares" (a lacuna do Bloco F).
    "mascara", "mascara_raio_mm", "pill", "pill_cor", "pill_opacidade",
    "sombra", "contorno", "cor_efeito", "papel_texto",
)


def slot_mestre(pagina: Pagina) -> Slot | None:
    """O primeiro slot-mestre da página (compat; com grupos, use ``mestres``)."""
    return next((s for s in pagina.slots if s.mestre), None)


def mestres(pagina: Pagina) -> list[Slot]:
    """Todos os mestres da página (grade + grupos livres coexistem — D2)."""
    return [s for s in pagina.slots if s.mestre]


def slots_do_grupo(pagina: Pagina, mestre: Slot) -> list[Slot]:
    """As cópias derivadas de um mestre (por identidade: ``ref_grupo``)."""
    return [s for s in pagina.slots if s.ref_grupo == mestre.id]


def mestre_do_slot(pagina: Pagina, slot: Slot) -> Slot | None:
    """RG-56: o MESTRE do grupo de que ``slot`` faz parte — ele mesmo se é
    o mestre, o dono do ``ref_grupo`` se é cópia, None se está solto."""
    if slot.mestre:
        return slot
    if slot.ref_grupo is not None:
        return next((s for s in pagina.slots
                     if s.id == slot.ref_grupo and s.mestre), None)
    return None


def desagrupar_grupo(pagina: Pagina, slot: Slot) -> list[Slot]:
    """RG-56 (Fase 4): dissolve o grupo de que ``slot`` faz parte — o mestre
    E todas as cópias viram slots SOLTOS, cada um carregando seus valores
    ATUAIS. As cópias já têm os valores materializados pela propagação
    (``_propagar_grupo`` grava tudo em cada região); os ``overrides`` viram
    valores próprios. **Nada se perde** (passo 23). Ids preservados (I1): o
    vínculo slot→item do ``mapa`` continua válido. Devolve os slots que
    ficaram soltos (mestre primeiro, depois as cópias na ordem da lista)."""
    mestre = mestre_do_slot(pagina, slot)
    if mestre is None:
        return []
    grupo = [mestre] + slots_do_grupo(pagina, mestre)
    for s in grupo:
        s.mestre = False
        s.ref_grupo = None
        for r in s.regioes:
            r.de_mestre = False        # deixa de receber propagação
            r.ref_mestre = None        # sem vínculo de identidade com a mestra
            r.overrides = set()        # os valores já são próprios (nada se perde)
    return grupo


def _migrar_grupos(pagina: Pagina) -> None:
    """Migração D2: layout antigo (um único mestre, derivadas sem ``ref_grupo``)
    ganha a referência de grupo na carga — uma vez, por identidade."""
    ms = mestres(pagina)
    if len(ms) != 1:
        return
    unico = ms[0]
    for slot in pagina.slots:
        if (slot is not unico and slot.origem_mm is not None
                and slot.ref_grupo is None):
            slot.ref_grupo = unico.id


def _migrar_refs(pagina: Pagina, mestre: Slot) -> None:
    """Migração única: derivadas antigas sem ``ref_mestre`` casam pela ordem.

    Layouts salvos antes da F5.5b não têm uids; ao carregar, cada derivada
    recebe o ``ref_mestre`` da região da mestra na MESMA posição (por tipo) —
    uma vez só; daí em diante o pareamento é por identidade (invariante I4).
    """
    for slot in slots_do_grupo(pagina, mestre):
        for tipo in TipoRegiao:
            fontes = [r for r in mestre.regioes if r.tipo == tipo]
            orfas = [r for r in slot.regioes
                     if r.tipo == tipo and r.de_mestre and r.ref_mestre is None]
            usados = {r.ref_mestre for r in slot.regioes if r.ref_mestre}
            livres = [f for f in fontes if f.uid not in usados]
            for orfa, fonte in zip(orfas, livres):
                orfa.ref_mestre = fonte.uid


def propagar_mestre(pagina: Pagina) -> None:
    """Propaga cada mestre para as cópias DO SEU GRUPO (D2: grupos coexistem).

    Pareamento por **identidade** (``ref_mestre`` → uid da mestra, I4): imune a
    reordenação de z-order. Estilo copia ``ATRIBUTOS_ESTILO`` exceto overrides;
    geometria rebaseia na âncora exceto override de "rect"; região nova na
    mestra nasce nas cópias; removida da mestra, as derivadas órfãs saem
    (adições próprias da cópia ficam).

    A interação com o override de ESTILO nomeado (``overrides_estilo``) está
    na matriz normativa em ``app/rendering/estilos.py`` (E-A4): são conjuntos
    independentes — esta função respeita ``overrides`` e não toca no outro.
    """
    _migrar_grupos(pagina)
    for mestre in mestres(pagina):
        if mestre.origem_mm is not None:
            _propagar_grupo(pagina, mestre)


def _propagar_grupo(pagina: Pagina, mestre: Slot) -> None:
    _migrar_refs(pagina, mestre)
    ox, oy = mestre.origem_mm
    uids_mestre = {r.uid for r in mestre.regioes}
    for slot in slots_do_grupo(pagina, mestre):
        if slot.origem_mm is None:
            continue
        dx, dy = slot.origem_mm[0] - ox, slot.origem_mm[1] - oy
        # órfãs (a mestra perdeu a região) saem; adições próprias ficam
        slot.regioes[:] = [r for r in slot.regioes
                           if not (r.de_mestre and r.ref_mestre not in uids_mestre)]
        por_ref = {r.ref_mestre: r for r in slot.regioes if r.ref_mestre}
        for origem in mestre.regioes:
            destino = por_ref.get(origem.uid)
            if destino is None:                 # mestra ganhou região nova
                destino = Regiao.from_dict(origem.to_dict())
                destino.uid = uuid.uuid4().hex  # identidade própria da derivada
                destino.ref_mestre = origem.uid
                destino.de_mestre = True
                destino.overrides = set()
                slot.regioes.append(destino)
            for attr in ATRIBUTOS_ESTILO:
                if attr not in destino.overrides:
                    setattr(destino, attr, getattr(origem, attr))
            if "rect" not in destino.overrides:
                destino.rect = Retangulo(
                    origem.rect.x_mm + dx, origem.rect.y_mm + dy,
                    origem.rect.larg_mm, origem.rect.alt_mm,
                )

# Offsets (px na arte) das regiões relativos ao canto superior-esquerdo da caixa
# de preço da célula. Derivados da célula-mestre afinada com o Otaviano.
_REL_IMAGEM = (-126, -183, 215, 176)
_REL_NOME = (-142, -5, 138, 68)


def _bandas(mascara_1d) -> list[tuple[int, int]]:
    """Runs contíguos de True em um vetor booleano."""
    bandas, ini = [], None
    for i, v in enumerate(mascara_1d):
        if v and ini is None:
            ini = i
        elif not v and ini is not None:
            bandas.append((ini, i - 1))
            ini = None
    if ini is not None:
        bandas.append((ini, len(mascara_1d) - 1))
    return bandas


def detectar_caixas_preco(caminho_arte: str, cabecalho_frac: float = 0.3) -> list[tuple[int, int, int, int]]:
    """Detecta as caixas de preço vermelhas (blocos), ignorando o cabeçalho."""
    import numpy as np
    from PIL import Image

    im = Image.open(caminho_arte).convert("RGB")
    w, h = im.size
    a = np.asarray(im).astype(int)
    mask = (a[:, :, 0] > 150) & (a[:, :, 1] < 90) & (a[:, :, 2] < 90)
    mask[: int(h * cabecalho_frac), :] = False  # zera o cabeçalho (logo/neon)

    linhas = mask.sum(axis=1) > (w * 0.10)   # bandas com bastante vermelho = linha de caixas
    caixas = []
    for ya, yb in _bandas(linhas):
        sub = mask[ya : yb + 1]
        colmask = sub.sum(axis=0) > ((yb - ya) * 0.25)
        for xa, xb in _bandas(colmask):
            caixas.append((xa, ya, xb - xa, yb - ya))
    return caixas


def montar_slot_celula(caixa, dpi: int, indice: int) -> Slot:
    """Replica a célula-mestre numa caixa detectada (Imagem/Nome/Preço)."""
    bx, by, bw, bh = caixa
    ix, iy, iw, ih = _REL_IMAGEM
    nx, ny, nw, nh = _REL_NOME
    regioes = [
        Regiao(TipoRegiao.IMAGEM, Retangulo.de_px(bx + ix, by + iy, iw, ih, dpi),
               nome="Imagem", ajuste=Ajuste.CONTER),
        Regiao(TipoRegiao.NOME, Retangulo.de_px(bx + nx, by + ny, nw, nh, dpi),
               nome="Nome", fonte="Quicksand-Bold.ttf", tamanho_max_pt=16, cor="#ffffff",
               alinhamento=Alinhamento.ESQUERDA),
        Regiao(TipoRegiao.PRECO, Retangulo.de_px(bx, by, bw, bh, dpi),
               nome="Preço", fonte="Quicksand-Bold.ttf", tamanho_max_pt=56, cor="#ffffff",
               alinhamento=Alinhamento.CENTRO, subtipo_preco=SubtipoPreco.COMPLETO,
               papel_preco=PapelPreco.POR, mostrar_moeda=False),
    ]
    for r in regioes:
        r.de_mestre = True   # todas nascem replicadas da mestra
    return Slot(
        f"celula_{indice}", regioes,
        origem_mm=(px_para_mm(bx, dpi), px_para_mm(by, dpi)),
    )


# =============================================================================
# GRUPOS LIVRES (F5.6 — ORDEM_F5_6 D1/D3/D4)
# =============================================================================

def _id_grupo() -> str:
    """D1: identidade de slot novo é uuid — NUNCA derivada de índice/contagem."""
    return f"grupo_{uuid.uuid4().hex[:8]}"


def agrupar_como_mestre(pagina: Pagina, regioes: list, slot_origem: Slot,
                        mapa: dict | None = None) -> Slot:
    """Cria um grupo replicável a partir de regiões livres (movidas do slot
    de origem). Âncora = canto superior-esquerdo do conjunto.

    C5.3 (higiene na origem): se o slot de origem ficou SEM regiões, não é
    mestre e não tem papel no ``mapa``, ele sai do layout — elimina o slot
    fantasma na raiz (o undo restaura, como manda o D5).
    """
    ancora = (min(r.rect.x_mm for r in regioes),
              min(r.rect.y_mm for r in regioes))
    novo = Slot(_id_grupo(), mestre=True, origem_mm=ancora)
    for r in regioes:
        if r in slot_origem.regioes:
            slot_origem.regioes.remove(r)
        r.de_mestre = True
        r.ref_mestre = None
        novo.regioes.append(r)
    pagina.slots.append(novo)
    if (not slot_origem.regioes and not slot_origem.mestre
            and (mapa is None or slot_origem.id not in mapa)
            and slot_origem in pagina.slots):
        pagina.slots.remove(slot_origem)
    return novo


def carimbar_copia(pagina: Pagina, mestre: Slot, ancora_mm: tuple) -> Slot:
    """D4: carimba uma cópia do grupo na âncora dada. A cópia nasce VAZIA e é
    povoada pela propagação — cada região ganha uid novo e ``ref_mestre``
    apontando para a região do MESTRE do grupo (nunca de outra cópia)."""
    copia = Slot(_id_grupo(), origem_mm=tuple(ancora_mm), ref_grupo=mestre.id)
    pagina.slots.append(copia)
    _propagar_grupo(pagina, mestre)
    return copia


def remover_slot(pagina: Pagina, slot_id: str) -> Slot | None:
    """D3: remove o slot SEM deslocar vizinhos (ids nunca renumeram — D1).

    Remover o MESTRE de um grupo: **promove a cópia mais antiga** (decisão da
    ordem, testada): ela vira o mestre; as demais reapontam ``ref_grupo`` e o
    ``ref_mestre`` de cada região é remapeado para as regiões da promovida.
    """
    slot = next((s for s in pagina.slots if s.id == slot_id), None)
    if slot is None:
        return None
    if slot.mestre:
        copias = slots_do_grupo(pagina, slot)
        if copias:
            promovida = copias[0]                     # a mais antiga (ordem da lista)
            # regiões da promovida viram a FONTE: remapeia as irmãs p/ os uids dela
            remap = {r.ref_mestre: r.uid for r in promovida.regioes if r.ref_mestre}
            promovida.mestre = True
            promovida.ref_grupo = None
            for r in promovida.regioes:
                r.ref_mestre = None
            for irma in copias[1:]:
                irma.ref_grupo = promovida.id
                for r in irma.regioes:
                    if r.ref_mestre in remap:
                        r.ref_mestre = remap[r.ref_mestre]
        # sem cópias: o grupo simplesmente deixa de existir
    pagina.slots.remove(slot)
    return slot


def ordenar_slots_visualmente(slots: list) -> list:
    """Ordem de leitura (y, x das âncoras) p/ o auto-preencher — ORDEM_F5_6 §3."""
    com = [s for s in slots if s.origem_mm is not None]
    sem = [s for s in slots if s.origem_mm is None]
    return sorted(com, key=lambda s: (round(s.origem_mm[1], 1),
                                      round(s.origem_mm[0], 1))) + sem


# Regiões que exibem CONTEÚDO DE PRODUTO (A7.1). TEXTO_LEGAL e SELO são
# decorativos/derivados — um slot só com eles não pode "engolir" um produto.
TIPOS_CONTEUDO = (TipoRegiao.IMAGEM, TipoRegiao.NOME,
                  TipoRegiao.PRECO, TipoRegiao.UNIDADE)


def ocupaveis(slots: list) -> list:
    """C5.1 + A7.1: slot ocupável = slot com região de CONTEÚDO DE PRODUTO.

    A regra mora AQUI, uma vez só — Mesa, pré-voo e testes importam dela.
    Slot sem regiões (C5) ou só-decorativo, ex.: o "Fica a Dica" (A7), não
    recebe produto: com 16+ itens, o 16º seria consumido pelo slot decorativo
    e sumiria do tabloide em silêncio (I2). Lição registrada pelo arquiteto:
    todo TIPO NOVO de slot/região reavalia "ocupável" e o pré-voo.
    """
    return [s for s in slots
            if any(r.tipo in TIPOS_CONTEUDO for r in s.regioes)]


def adicionar_pagina_de_arte(layout: LayoutDef, caminho_arte: str) -> Pagina:
    """F5.8 (D8.1/D8.2): página nova com a própria arte e a própria detecção.

    Slots nascem `celula_<uuid8>` — **únicos no layout inteiro** (D8.1: página
    nova NUNCA reusa `celula_N`); o primeiro é o mestre DA PÁGINA (grupos são
    por página); `pagina.arquivo_fundo` guarda a arte (D8.2).
    """
    dpi = layout.dpi
    caixas = detectar_caixas_preco(caminho_arte)
    pagina = Pagina(arquivo_fundo=str(caminho_arte))
    mestre = None
    for i, c in enumerate(caixas):
        if i == 0:
            slot = montar_slot_celula(c, dpi, i)
            slot.id = f"celula_{uuid.uuid4().hex[:8]}"
            slot.mestre = True
            mestre = slot
        else:
            bx, by, *_ = c
            slot = Slot(f"celula_{uuid.uuid4().hex[:8]}",
                        origem_mm=(px_para_mm(bx, dpi), px_para_mm(by, dpi)),
                        ref_grupo=mestre.id)
        pagina.slots.append(slot)
    if pagina.slots:
        _propagar_grupo(pagina, mestre)
    layout.paginas.append(pagina)
    layout.validar_ids_unicos()          # D8.1: cinto e suspensório
    return pagina


def layout_grade_de_arte(caminho_arte: str, dpi: int = DPI_PADRAO):
    """Monta um LayoutDef com um slot por caixa detectada. Retorna (layout, caixas).

    O primeiro slot é a **célula-mestre**; as demais células nascem VAZIAS (só
    com a âncora) e são povoadas pela própria ``propagar_mestre`` — assim toda
    derivada já nasce com ``ref_mestre`` (I4), sem caminho paralelo de criação.

    D1 (re-detecção): esta função SEMPRE constrói um LayoutDef novo — nunca
    reatribui ``celula_N`` de um layout existente. Se um dia houver
    "re-detectar" sobre layout com slots, os ids novos devem ser uuid.
    """
    caixas = detectar_caixas_preco(caminho_arte)
    layout = layout_de_arte(caminho_arte, dpi=dpi)
    slots = []
    for i, c in enumerate(caixas):
        if i == 0:
            slot = montar_slot_celula(c, dpi, i)
            slot.mestre = True
        else:
            bx, by, *_ = c
            slot = Slot(f"celula_{i}",
                        origem_mm=(px_para_mm(bx, dpi), px_para_mm(by, dpi)),
                        ref_grupo="celula_0")   # D2: grupo da grade, desde o berço
        slots.append(slot)
    layout.paginas[0].slots = slots
    if slots:
        propagar_mestre(layout.paginas[0])
    return layout, caixas

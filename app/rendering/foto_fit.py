"""
A foto tem de encher a zona — ORDEM F13-QUARTUSDECIMUS §1 (Q1)
==============================================================
A régua: toda foto deve ocupar ≥ 85% da área da sua zona. Quando a
proporção da foto e a da zona divergem, é a ZONA que muda de forma —
nunca a foto que encolhe e afunda (o ``ASSENTAR`` escala pela dimensão
limitante e ancora no rodapé: foto quadrada em zona alta vira 56% de
área com um paredão de vazio em cima — as três fixas da Quarta).

A adaptação é RUNTIME (a foto da semana decide a forma da semana) e só
acontece em célula marcada ``zona_flex`` no template — a marca diz "a
arte de fundo aqui é lisa; os textos podem se mover dentro do bbox da
célula". Célula sem a marca, vestida (ADORNO/SELO/FILETE por cima) ou
com rotação nunca é tocada: nelas a régua só MEDE e reporta.

Casos-limite escritos com a regra (a lição do §6 da ordem):

* a garrafa do Óleo em pé numa zona quadrada mede ~33% de área e está
  CERTA — ela enche a altura e o vazio lateral é simétrico; a guarda de
  ganho (só adapta quem ganha ≥15% de área de foto) a deixa em paz;
* a cesta da Terça é célula vestida (ADORNO por cima da foto): o pão
  assenta ATRÁS da borda desenhada — mover a foto descolaria o produto
  da arte; célula vestida nunca entra no plano;
* foto quadrada em zona alta (o defeito da ordem): o plano lateral ou o
  vertical vence — a zona vira o abraço exato da foto (ocupação ~100%)
  e os textos deslocam DENTRO do bbox da célula.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from app.rendering.model import Regiao, Retangulo, TipoRegiao

# a régua da ordem (§1): foto ≥ 85% da área da zona
FRACAO_CHEIA = 0.85
# adaptação estrutural só com ganho REAL de área de foto (evita mexer
# na célula por migalha — e deixa a garrafa em pé, que nada ganharia)
GANHO_MINIMO = 1.15
# respiro entre a foto e os textos realocados (mm)
_GAP_MM = 1.2

_TIPOS_REALOCAVEIS = {TipoRegiao.NOME, TipoRegiao.SUBTITULO,
                      TipoRegiao.UNIDADE, TipoRegiao.PRECO,
                      TipoRegiao.TEXTO_LEGAL}
# elementos de largura RÍGIDA (pílula de preço/desconto não estreita)
_TIPOS_RIGIDOS = {TipoRegiao.PRECO, TipoRegiao.TEXTO_LEGAL}


@dataclass
class MedidaFoto:
    """O que o ASSENTAR faria: frações da zona que a foto ocupa."""

    area_frac: float
    w_frac: float
    h_frac: float


def medir_ocupacao(zona_larg: float, zona_alt: float,
                   img_w: float, img_h: float) -> MedidaFoto:
    """A régua, pura: escala pela dimensão limitante (o que CONTER e
    ASSENTAR fazem) e mede as frações. Unidades: zona em mm, imagem em
    px — as frações são adimensionais."""
    if zona_larg <= 0 or zona_alt <= 0 or img_w <= 0 or img_h <= 0:
        return MedidaFoto(0.0, 0.0, 0.0)
    s = min(zona_larg / img_w, zona_alt / img_h)
    w, h = img_w * s, img_h * s
    return MedidaFoto((w * h) / (zona_larg * zona_alt),
                      w / zona_larg, h / zona_alt)


@dataclass
class PlanoFoto:
    """O veredito do replanejamento de UMA célula — rects substitutos
    por uid, só para esta composição (o modelo nunca muda, I1)."""

    rects: dict[str, Retangulo] = field(default_factory=dict)
    antes: MedidaFoto | None = None
    area_antes_mm2: float = 0.0
    area_depois_mm2: float = 0.0
    arranjo: str = ""                   # "lateral" | "vertical" | "abraco"


@dataclass
class _Cand:
    rects: dict[str, Retangulo]
    area: float
    arranjo: str


def _plano_lateral(foto: Regiao, textos: list[Regiao], bbox, prop):
    """Foto de um lado (assentada no rodapé do bbox), coluna de texto
    do outro — a fronteira entre os dois é a proporção da foto quem
    põe. O lado dos textos é o que eles já ocupavam."""
    x0, y0, x1, y1 = bbox
    bw, bh = x1 - x0, y1 - y0
    if not textos:
        w = min(bw, bh * prop)
        h = w / prop
        return _Cand({foto.uid: Retangulo(x0 + (bw - w) / 2, y1 - h, w, h)},
                     w * h, "lateral")
    larg_rigida = max((r.rect.larg_mm for r in textos
                       if r.tipo in _TIPOS_RIGIDOS), default=0.0)
    # a coluna não pode ESTRANGULAR o nome: preserva ≥85% da largura
    # original da coluna de texto — senão a escada do passo 5 decapita
    # ("Mini" sem "Salgadinhos", visto no OLHAR da 1ª recomposição da
    # Quarta; a foto imponente não paga a página ilegível)
    larg_flexivel = max((r.rect.larg_mm for r in textos
                         if r.tipo not in _TIPOS_RIGIDOS), default=0.0)
    larg_col = max(larg_rigida + 2 * _GAP_MM, 0.35 * bw,
                   0.85 * larg_flexivel)
    disp = bw - _GAP_MM - larg_col
    if disp <= 4.0:
        return None
    w = min(disp, bh * prop)
    h = w / prop
    larg_col_real = bw - w - _GAP_MM
    centro_txt = sum(r.rect.x_mm + r.rect.larg_mm / 2
                     for r in textos) / len(textos)
    if centro_txt >= foto.rect.x_mm + foto.rect.larg_mm / 2:
        fx, cx = x0, x0 + w + _GAP_MM          # textos à direita
    else:
        fx, cx = x1 - w, x0                    # textos à esquerda
    rects = {foto.uid: Retangulo(fx, y1 - h, w, h)}
    for r in textos:
        if r.tipo in _TIPOS_RIGIDOS:
            lw = min(r.rect.larg_mm, larg_col_real)
            rects[r.uid] = Retangulo(cx + (larg_col_real - lw) / 2,
                                     r.rect.y_mm, lw, r.rect.alt_mm)
        else:
            rects[r.uid] = Retangulo(cx, r.rect.y_mm,
                                     larg_col_real, r.rect.alt_mm)
    return _Cand(rects, w * h, "lateral")


def _plano_misto(foto: Regiao, textos: list[Regiao], bbox, prop):
    """Nome/descritor no TOPO na largura total (uma linha limpa), foto
    GRANDE embaixo à esquerda, preço/pílula à direita dela — a sugestão
    literal do dono na ordem ('reposicionar esses textos um pouco mais
    para baixo e deixar essas imagens mais imponentes'). É o arranjo
    que vence nas células BAIXAS onde lateral estrangula o nome e
    vertical mirra a foto."""
    x0, y0, x1, y1 = bbox
    bw = x1 - x0
    flex = sorted([r for r in textos if r.tipo not in _TIPOS_RIGIDOS],
                  key=lambda r: r.rect.y_mm)
    rigidos = [r for r in textos if r.tipo in _TIPOS_RIGIDOS]
    rects: dict[str, Retangulo] = {}
    y = y0
    for r in flex:
        rects[r.uid] = Retangulo(x0, y, bw, r.rect.alt_mm)
        y += r.rect.alt_mm + _GAP_MM
    alt_foto = y1 - y
    if alt_foto < 8.0:
        return None
    larg_rigida = max((r.rect.larg_mm for r in rigidos), default=0.0)
    larg_disp = bw - (larg_rigida + 2 * _GAP_MM if rigidos else 0.0)
    if larg_disp < 8.0:
        return None
    w = min(larg_disp, alt_foto * prop)
    h = w / prop
    if h < 8.0:
        return None                     # foto mirrada não é plano
    fx = x0 if rigidos else x0 + (bw - w) / 2
    rects[foto.uid] = Retangulo(fx, y1 - h, w, h)
    for r in rigidos:
        col = bw - w - _GAP_MM
        lw = min(r.rect.larg_mm, col)
        # a pílula centra na faixa da foto, mas NUNCA vaza o bbox — a
        # frota reproduziu tinta 4,7mm abaixo da célula com foto ~10:1
        # (pílula mais alta que a foto planejada); clamp de fundo, e se
        # nem entre os flexíveis e o rodapé ela cabe, o plano é inviável
        ry = max(y, (y1 - h) + (h - r.rect.alt_mm) / 2)
        ry = min(ry, y1 - r.rect.alt_mm)
        if ry < y - 1e-6:
            return None
        rects[r.uid] = Retangulo(x0 + w + _GAP_MM + (col - lw) / 2, ry,
                                 lw, r.rect.alt_mm)
    return _Cand(rects, w * h, "misto")


def _plano_vertical(foto: Regiao, textos: list[Regiao], bbox, prop):
    """Foto em cima na largura que a proporção pedir, textos empilhados
    embaixo (a saída 2 da ordem — 'o texto desce para baixo dela')."""
    x0, y0, x1, y1 = bbox
    bw, bh = x1 - x0, y1 - y0
    ordenados = sorted(textos, key=lambda r: r.rect.y_mm)
    soma = sum(r.rect.alt_mm for r in ordenados) \
        + _GAP_MM * len(ordenados)
    h = min(bh - soma, bw / prop)
    if h < 8.0:
        return None                     # foto mirrada não é plano
    w = h * prop
    rects = {foto.uid: Retangulo(x0 + (bw - w) / 2, y0, w, h)}
    y = y0 + h
    for r in ordenados:
        y += _GAP_MM
        if r.tipo in _TIPOS_RIGIDOS:
            lw = min(r.rect.larg_mm, bw)
            rects[r.uid] = Retangulo(x0 + (bw - lw) / 2, y,
                                     lw, r.rect.alt_mm)
        else:
            rects[r.uid] = Retangulo(x0, y, bw, r.rect.alt_mm)
        y += r.rect.alt_mm
    return _Cand(rects, w * h, "vertical")


def plano_da_celula(regioes: list[Regiao], img_w: float,
                    img_h: float) -> PlanoFoto | None:
    """O plano de UMA célula para a foto da vez. ``None`` = a geometria
    do template fica como está (foto cheia, célula sem a marca, célula
    vestida, ou ganho que não paga a mudança)."""
    vis = [r for r in regioes if r.visivel]
    fotos = [r for r in vis if r.tipo == TipoRegiao.IMAGEM]
    if len(fotos) != 1 or img_w <= 0 or img_h <= 0:
        return None
    foto = fotos[0]
    if not getattr(foto, "zona_flex", False):
        return None
    textos = [r for r in vis if r.tipo in _TIPOS_REALOCAVEIS]
    # QUINTUSDECIMUS/J25: um ADORNO-FILETE (o "Fio" das linhas do
    # Jornal — 6 px de altura) é SEPARADOR, não roupa: a foto pode
    # crescer sob ele sem descolar arte nenhuma. O ADORNO de verdade
    # (a cesta da Terça) continua vestindo a célula e barrando o plano.
    def _e_filete(r: Regiao) -> bool:
        return (r.tipo == TipoRegiao.ADORNO
                and min(r.rect.larg_mm, r.rect.alt_mm) <= 2.0)
    if any(r.tipo not in _TIPOS_REALOCAVEIS
           and r.tipo != TipoRegiao.IMAGEM and not _e_filete(r)
           for r in vis):
        return None                     # célula vestida — a âncora é da arte
    # rotação DE VERDADE (a data deitada a 90°) barra o plano; o charme
    # decorativo das inclinações do encarte (−6°/−8° dos carimbos do
    # Jornal, J25) é cosmético — o conteúdo gira em torno do centro do
    # rect substituto do mesmo jeito (I1)
    if any(abs((r.rotacao_graus + 180.0) % 360.0 - 180.0) > 8.5
           for r in [foto] + textos):
        return None
    rf = foto.rect
    antes = medir_ocupacao(rf.larg_mm, rf.alt_mm, img_w, img_h)
    if antes.area_frac >= FRACAO_CHEIA:
        return None                     # a régua aprova — nada a fazer
    if antes.h_frac >= FRACAO_CHEIA:
        # o caso-limite DECLARADO da régua (§6): produto em PÉ que já
        # enche a altura da zona (garrafa, saco) — o vazio é lateral e
        # simétrico, o visual "dominando" que o dono aprovou (Q7); o
        # alvo de 85% de área vale para o defeito AFUNDADA (limitada
        # pela largura, paredão de vazio em cima), não para ele
        return None
    prop = img_w / img_h
    s = min(rf.larg_mm / img_w, rf.alt_mm / img_h)
    area_atual = (img_w * s) * (img_h * s)

    todas = [foto] + textos
    bbox = (min(r.rect.x_mm for r in todas),
            min(r.rect.y_mm for r in todas),
            max(r.rect.x_mm + r.rect.larg_mm for r in todas),
            max(r.rect.y_mm + r.rect.alt_mm for r in todas))
    cands = [c for c in (_plano_lateral(foto, textos, bbox, prop),
                         _plano_vertical(foto, textos, bbox, prop),
                         _plano_misto(foto, textos, bbox, prop)) if c]
    if cands:
        melhor = max(cands, key=lambda c: c.area)
        if melhor.area >= GANHO_MINIMO * area_atual:
            return PlanoFoto(melhor.rects, antes, area_atual,
                             melhor.area, melhor.arranjo)
    if antes.h_frac < FRACAO_CHEIA:
        # a rede: a foto está AFUNDADA (limitada pela largura, vazio em
        # cima) e nenhum arranjo pagou a mudança — a zona vira o abraço
        # da foto (ocupação ~100%). Com texto COLADO logo abaixo da
        # zona (o arranjo do adendo: foto em cima, descrição embaixo),
        # o abraço ANCORA NO RODAPÉ — centralizar abriria um vão e
        # mataria o passo 3 da precedência (o nome não poderia mais
        # crescer sobre a foto; foi o "Lanche na" decapitado do OLHAR);
        # sem vizinho colado, centraliza (o caso da coluna lateral)
        w = min(rf.larg_mm, rf.alt_mm * prop)
        h = w / prop
        fundo = rf.y_mm + rf.alt_mm
        colado = any(r.tipo in _TIPOS_REALOCAVEIS and r.visivel
                     and 0.0 <= r.rect.y_mm - fundo <= 2.5
                     for r in regioes)
        y_novo = (fundo - h) if colado \
            else rf.y_mm + (rf.alt_mm - h) / 2
        rect = Retangulo(rf.x_mm + (rf.larg_mm - w) / 2, y_novo, w, h)
        return PlanoFoto({foto.uid: rect}, antes, area_atual,
                         w * h, "abraco")
    return None

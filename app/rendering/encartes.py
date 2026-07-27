"""Os 7 encartes do pacote Belo Brasil — geometria por DADOS (F13/F2).

O detector por cor (``grade.detectar_caixas_preco``) só enxerga caixa de
preço VERMELHA — nenhum encarte novo tem essa grade, e o Jornal nem tem
``id="celula-N"`` no SVG (N-04). A geometria célula-a-célula vem dos
GERADORES do pacote (as listas ``CELLS``/``COLS``/``BXS``), transcrita
aqui na escala 1× do viewBox (1080×1440 px, lidos a 96 dpi). O BASE.png
é 2160×2880 (×2 exato) ⇒ o LayoutDef nasce com dpi=192 e a página fecha
nos MESMOS mm (285,75 × 381) — composição 1:1 com a arte.

Decisões desta transcrição (declaradas na resposta do builder):
- célula FIXA (F1): Terça 1-2, Segunda 1, Quarta fixa-1..3 — produto da
  própria arte, fora do auto-preencher;
- F7/N-01: o 1º slot de foto do combo da Terça nasce ENCOLHIDO (210→194
  px) para não ficar por baixo do selo de 25% gravado no BASE;
- F6/N-06: a validade vira região papel VALIDADE na posição/rotação do
  selo de cada encarte (o rodapé com data foi removido do BASE);
- a rotação de célula usa o CENTRO de cada região como pivô (o modelo é
  por região); nas cestas da Terça o pivô real do gerador é (cx, 1000)
  — em rotações sub-grau a diferença é <2 px, invisível a 96 dpi;
- Quarta: nomes em Nunito-Black (nunca Baloo 2 — F10/N-03: o glifo "ã"
  da instância do pacote é defeituoso e produto variável pode ter "ã").
"""

from __future__ import annotations

from pathlib import Path

from app.rendering.model import (
    Alinhamento,
    AlinhamentoV,
    FormaPreco,
    LayoutDef,
    Pagina,
    PapelTexto,
    Regiao,
    Retangulo,
    Slot,
    TipoRegiao,
    layout_de_arte,
)

# Coordenadas das tabelas: px do viewBox 1080×1440 (a escala dos
# geradores). O BASE.png é ×2 ⇒ dpi 192 na página, 96 nas tabelas —
# os milímetros fecham iguais.
DPI_VIEWBOX = 96
DPI_BASE = 192

# chave → (subpasta em artes/, arquivo(s) BASE.png)
_BASES: dict[str, tuple[str, tuple[str, ...]]] = {
    "segunda-frios": ("segunda-frios", ("segunda-frios-BASE.png",)),
    "terca-do-pao": ("terca-do-pao", ("terca-do-pao-BASE.png",)),
    "quarta-das-ofertas": ("quarta-das-ofertas",
                           ("quarta-das-ofertas-BASE-2160x2880.png",)),
    "quinta-do-peixe": ("quinta-do-peixe", ("quinta-do-peixe-BASE.png",)),
    "sexta-verde": ("sexta-verde", ("sexta-verde-BASE-2160x2880.png",)),
    "sabado-da-carne": ("sabado-da-carne", ("sabado-da-carne-BASE.png",)),
    "jornal-do-mes": ("jornal-do-mes",
                      ("jornal-p1-BASE.png", "jornal-p2-BASE.png")),
}

NOMES_EXIBICAO = {
    "segunda-frios": "Segunda dos Frios",
    "terca-do-pao": "Terça do Pão",
    "quarta-das-ofertas": "Quarta das Ofertas",
    "quinta-do-peixe": "Quinta do Peixe",
    "sexta-verde": "Sexta Verde",
    "sabado-da-carne": "Sábado da Carne",
    "jornal-do-mes": "Jornal do Mês",
}


def _r(x: float, y: float, w: float, h: float) -> Retangulo:
    return Retangulo.de_px(x, y, w, h, DPI_VIEWBOX)


def _mm(v: float) -> float:
    from app.rendering.units import px_para_mm
    return px_para_mm(v, DPI_VIEWBOX)


def _img(x, y, w, h, rot=0.0) -> Regiao:
    return Regiao(TipoRegiao.IMAGEM, _r(x, y, w, h), nome="Foto",
                  rotacao_graus=rot)


def _nome(x, y, w, h, *, fonte, rot=0.0, alin=Alinhamento.CENTRO,
          tam=48.0, cor="#000000") -> Regiao:
    # F13-BIS/T5: nas células estreitas dos encartes, hifenizar é
    # PROIBIDO — o corpo cede ("CERVEJA ITAPA-VA" virou prova)
    return Regiao(TipoRegiao.NOME, _r(x, y, w, h), nome="Nome",
                  fonte=fonte, alinhamento=alin, cor=cor,
                  tamanho_max_pt=tam, sem_hifen=True,
                  alinhamento_v=AlinhamentoV.BASE, rotacao_graus=rot)


def _sub(x, y, w, h, *, fonte, rot=0.0, alin=Alinhamento.CENTRO,
         tam=48.0, cor="#000000") -> Regiao:
    # F13-BIS/T2: a linha de DESCRITOR do modelo (região SUBTITULO)
    return Regiao(TipoRegiao.SUBTITULO, _r(x, y, w, h), nome="Descritor",
                  fonte=fonte, alinhamento=alin, cor=cor,
                  tamanho_max_pt=tam, sem_hifen=True,
                  alinhamento_v=AlinhamentoV.BASE, rotacao_graus=rot)


def _preco(x, y, w, h, *, fonte, rot=0.0, forma=None, forma_cor=None,
           borda=None, cor="#000000", tam=48.0, tam_cent=None,
           centavos_na_base=False, alin=Alinhamento.CENTRO,
           separado=None) -> Regiao:
    from app.rendering.model import SubtipoPreco
    if separado is None:
        separado = forma is not None or tam_cent is not None
    return Regiao(TipoRegiao.PRECO, _r(x, y, w, h), nome="Preço",
                  fonte=fonte, alinhamento=alin, cor=cor,
                  tamanho_max_pt=tam, tamanho_centavos_pt=tam_cent,
                  subtipo_preco=(SubtipoPreco.SEPARADO if separado
                                 else SubtipoPreco.COMPLETO),
                  forma_preco=forma or FormaPreco.TEXTO,
                  forma_cor=forma_cor or "#C0392B",
                  forma_cor_borda=borda,
                  centavos_na_base=centavos_na_base,
                  rotacao_graus=rot)


def _legal(x, y, w, h, *, papel, fonte, texto="", nome="", rot=0.0,
           alin=Alinhamento.CENTRO, tam=48.0, cor="#000000") -> Regiao:
    return Regiao(TipoRegiao.TEXTO_LEGAL, _r(x, y, w, h),
                  nome=nome or papel.value.title(), fonte=fonte,
                  papel_texto=papel, texto_fixo=texto, alinhamento=alin,
                  tamanho_max_pt=tam, cor=cor, sem_hifen=True,
                  alinhamento_v=AlinhamentoV.CENTRO, rotacao_graus=rot)


def _slot(sid: str, regioes: list[Regiao], *, origem: tuple,
          fixa: bool = False) -> Slot:
    return Slot(sid, regioes, fixa=fixa,
                origem_mm=(_mm(origem[0]), _mm(origem[1])))


# Fontes do pacote (arquivo .ttf; a importação copia para a pasta de
# fontes do app). A família de cada papel segue o gerador do encarte.
_F_ARCHIVO = "Archivo-Bold.ttf"
_F_FRAUNCES = "Fraunces-SemiBold.ttf"
_F_FRA_IT = "Fraunces-Italic.ttf"
_F_NUNITO = "Nunito-Black.ttf"
_F_ANTON = "Anton-Regular.ttf"

FONTES_DO_PACOTE = (
    "Anton-Regular.ttf", "Archivo-Bold.ttf", "Archivo-Medium.ttf",
    "Baloo2-Bold.ttf", "Baloo2-ExtraBold.ttf", "Caveat-Bold.ttf",
    "Fraunces-Italic.ttf", "Fraunces-Regular.ttf",
    "Fraunces-SemiBold.ttf", "Nunito-Black.ttf", "Nunito-Bold.ttf",
    "UnifrakturMaguntia.ttf",
)


# ---------------------------------------------------------------------------
# As 8 tabelas (§13 do dossiê / listas dos geradores)
# ---------------------------------------------------------------------------


def _terca() -> list[Slot]:
    """gen_terca_final — F13-BIS: o INTERIOR das células, fiel à espec.

    Tinta da Terça: INK #33200F, MUTE #96826A, TERRA #C94F32 (disco),
    TERRAD #A03A22, CREAM #FFF9EC, rótulo #C77E38. Preço = disco
    escalopado PENDURADO no toldo (r=36, centro cx,952 — cavalga a aba
    da cesta), Fraunces, centavos NA BASE (a espec: sem dy)."""
    slots = [
        # celula-1 FIXA (Pão Francês) — nome em serifa GRANDE na metade
        # direita; o selo "50%" e o painel picotado são da própria arte;
        # o manuscrito Caveat é CONTEÚDO (não está no BASE)
        _slot("celula-1", [
            _img(86, 376, 320, 214),
            _nome(324, 382, 420, 44, fonte=_F_FRAUNCES,
                  tam=30.0, cor="#33200F"),
            _sub(324, 432, 420, 22, fonte=_F_FRA_IT,
                 tam=10.9, cor="#96826A"),
            # (sem a "★" do exemplo: a Caveat não tem o glifo — no
            # modelo a estrela é um path vetorial, adorno da arte)
            _legal(100, 652, 280, 34, papel=PapelTexto.LIVRE,
                   fonte="Caveat-Bold.ttf", nome="Manuscrito",
                   texto="metade do preço, é hoje!", rot=-1.5,
                   tam=21.0, cor="#A03A22"),
        ], origem=(64, 352), fixa=True),
        # celula-2 FIXA (Sonho + Croissant) — DUAS zonas de foto com o
        # "+" da estrutura entre elas; 1º slot ENCOLHIDO 210→194 (F7:
        # o selo de 25% gravado no BASE invadia o canto)
        _slot("celula-2", [
            _img(712, 386, 194, 90),
            _img(712, 524, 210, 90),
            _nome(697, 630, 240, 26, fonte=_F_FRAUNCES,
                  tam=17.2, cor="#33200F"),
            _sub(697, 660, 240, 18, fonte=_F_FRA_IT,
                 tam=9.4, cor="#96826A"),
        ], origem=(688, 352), fixa=True),
    ]
    bxs = (64, 306, 548, 790)
    rots = (-0.7, 0.55, -0.55, 0.7)
    for i, (x, rot) in enumerate(zip(bxs, rots), start=3):
        cx = x + 113                      # BW=226
        prot = -1.5 if (i - 3) % 2 == 0 else 1.5   # o remendo da cesta
        slots.append(_slot(f"celula-{i}", [
            _img(x + 18, 756, 190, 150, rot=rot),
            # o disco pendurado: r=36 centrado em (cx, 952)
            _preco(cx - 36, 916, 72, 72, fonte=_F_FRAUNCES,
                   rot=rot, forma=FormaPreco.ETIQUETA_PENDURADA,
                   forma_cor="#C94F32", borda="#A03A22",
                   cor="#FFF9EC", tam=17.0, tam_cent=11.0,
                   centavos_na_base=True),
            _legal(cx - 95, 1014, 190, 12, papel=PapelTexto.LIVRE,
                   fonte=_F_ARCHIVO, nome="Rótulo",
                   texto="· PADARIA BELO BRASIL ·", rot=prot,
                   tam=6.0, cor="#C77E38"),
            _nome(cx - 95, 1028, 190, 20, fonte=_F_FRAUNCES,
                  tam=11.6, cor="#33200F", rot=prot),
            _sub(cx - 95, 1050, 190, 15, fonte=_F_FRA_IT,
                 tam=7.5, cor="#96826A", rot=prot),
        ], origem=(x, 756)))
    slots.append(_slot("selo-validade", [
        _legal(896, 106, 100, 44, papel=PapelTexto.VALIDADE,
               fonte=_F_FRAUNCES, nome="Validade", rot=8.0,
               tam=16.5, cor="#33200F"),
    ], origem=(876, 106)))
    return slots


def _segunda() -> list[Slot]:
    """gen_segunda3 — F13-BIS: o selo de CERA (medalhão) é a identidade.

    Tinta: INKB #17293B (texto no selo e nomes claros), BUTTER #E9B23A
    (cera), BUTTERD #C08F1F (anel), banda azul #1F4E79 (estrutura) com
    nome BRANCO e descritor #BCD2E4; chips "Nº 0X" são CONTEÚDO."""
    slots = [
        # celula-1 FIXA (Kit Burger) — §3.2.5: o preço do kit EXISTE
        # (selo de cera s=1.15, R=46, centro 734,516; texto NAVY)
        _slot("celula-1", [
            _img(390, 352, 300, 104),
            _nome(380, 458, 320, 34, fonte=_F_FRAUNCES,
                  tam=21.0, cor="#17293B"),
            _sub(380, 540, 320, 24, fonte=_F_FRA_IT,
                 tam=9.4, cor="#6E7F8D"),
            _preco(688, 470, 92, 92, fonte=_F_FRAUNCES,
                   forma=FormaPreco.MEDALHAO_ESTRELA,
                   forma_cor="#E9B23A", borda="#C08F1F",
                   cor="#17293B", tam=23.0, tam_cent=14.6,
                   centavos_na_base=True),
        ], origem=(290, 288), fixa=True),
    ]
    # (id, nº do chip, origem, rot, foto, chip(x,y), selo(cx,cy,R),
    #  nome(cx ou caixa), zona do texto)
    # flancos: texto na BANDA de baixo, selo SOBRE A FOTO; etiquetas:
    # selo morde a banda e o texto DESVIA (tcx do gerador)
    flancos = (
        # nome @ (cx, y+h−40) — DENTRO da banda azul (526/532..578/584)
        (2, (64, 288), -0.6, (84, 314, 170, 116), (76, 302),
         (236, 328, 32), 169, 548),
        (3, (806, 294), 0.5, (826, 320, 170, 116), (818, 308),
         (978, 334, 32), 911, 554),
    )
    for i, origem, rot, foto, (chx, chy), (sx, sy, sr), tcx, ty in flancos:
        slots.append(_slot(f"celula-{i}", [
            _img(*foto, rot=rot),
            _chip_num(chx, chy, f"Nº {i:02d}", rot),
            _preco(sx - sr, sy - sr, sr * 2, sr * 2, fonte=_F_FRAUNCES,
                   rot=rot, forma=FormaPreco.MEDALHAO_ESTRELA,
                   forma_cor="#E9B23A", borda="#C08F1F", cor="#17293B",
                   tam=16.2, tam_cent=10.2, centavos_na_base=True),
            _nome(tcx - 93, ty - 22, 186, 24, fonte=_F_FRAUNCES,
                  tam=11.2, cor="#FFFFFF", rot=rot),
            _sub(tcx - 93, ty + 2, 186, 18, fonte=_F_FRA_IT,
                 tam=7.9, cor="#BCD2E4", rot=rot),
        ], origem=origem))
    # (id, origem, rot, foto, chip, selo(cx,cy,R,s_tam), tcx, y_nome)
    etiquetas = (
        (4, (64, 652), -0.5, (82, 672, 268, 138), (76, 664),
         (328, 886, 38), 180, 906, 13.5, 8.6),
        (5, (388, 644), 0.4, (406, 664, 268, 138), (398, 656),
         (428, 878, 38), 568, 898, 13.5, 8.6),
        (6, (712, 654), -0.5, (730, 674, 268, 138), (722, 666),
         (976, 888, 38), 828, 908, 13.5, 8.6),
        (7, (240, 955), -0.45, (256, 973, 264, 104), (250, 965),
         (496, 1152, 35), 352, 1171, 12.4, 8.2),
        (8, (552, 948), 0.4, (568, 966, 264, 104), (562, 958),
         (592, 1145, 35), 728, 1164, 12.4, 8.2),
    )
    for i, origem, rot, foto, (chx, chy), (sx, sy, sr), tcx, ny, tn, ts \
            in etiquetas:
        slots.append(_slot(f"celula-{i}", [
            _img(*foto, rot=rot),
            _chip_num(chx, chy, f"Nº {i:02d}", rot),
            _preco(sx - sr, sy - sr, sr * 2, sr * 2, fonte=_F_FRAUNCES,
                   rot=rot, forma=FormaPreco.MEDALHAO_ESTRELA,
                   forma_cor="#E9B23A", borda="#C08F1F", cor="#17293B",
                   tam=14.6, tam_cent=9.2, centavos_na_base=True),
            _nome(tcx - 100, ny - 22, 200, 24, fonte=_F_FRAUNCES,
                  tam=tn, cor="#FFFFFF", rot=rot),
            _sub(tcx - 100, ny + 2, 200, 18, fonte=_F_FRA_IT,
                 tam=ts, cor="#BCD2E4", rot=rot),
        ], origem=origem))
    slots.append(_slot("selo-validade", [
        _legal(885, 74, 100, 44, papel=PapelTexto.VALIDADE,
               fonte=_F_FRAUNCES, nome="Validade", rot=10.0,
               tam=16.5, cor="#1F4E79"),
    ], origem=(865, 74)))
    return slots


def _chip_num(x, y, texto, rot=0.0) -> Regiao:
    """O chip "Nº 0X" da Segunda (T4): pill azul + texto branco."""
    r = _legal(x, y, 52, 20, papel=PapelTexto.LIVRE, fonte=_F_ARCHIVO,
               texto=texto, nome="Chip", rot=rot - 2.0,
               tam=7.9, cor="#FFFFFF")
    r.pill = True
    r.pill_cor = "#1F4E79"
    r.pill_opacidade = 255
    return r


def _quarta() -> list[Slot]:
    """gen_final: minis_xy (3 FIXAS na Coluna do Dia) + cards_xy + banner.

    F10/N-03: nomes em Nunito (nunca a instância Baloo 2 do pacote — o
    glifo "ã" é defeituoso e produto variável pode ter "ã"). F9/N-02: a
    3ª fixa usa papel DESCONTO — o % é CALCULADO de (de−por)/de, nunca
    digitado (compatível com o pctpod parametrizado do gerador)."""
    slots = []
    verde, laranja, escuro = "#2E6B3F", "#F58634", "#241D14"
    for i in range(3):                    # minis: RX+20=74, MY0=546, MH+MG=246
        my = 546 + i * 246
        regs = [
            _img(88, my + 14, 112, 204),
            _nome(212, my + 34, 148, 60, fonte=_F_NUNITO,
                  alin=Alinhamento.ESQUERDA, tam=15.4, cor=escuro),
            # a linha do peso do modelo ("BBX 100g" — cola no nome)
            _sub(212, my + 98, 148, 22, fonte="Nunito-Bold.ttf",
                 alin=Alinhamento.ESQUERDA, tam=11.0, cor=escuro),
        ]
        if i < 2:
            # pricepod VERDE (s=0.82), centro (278, my+180), sobrescrito
            regs.append(_preco(228, my + 157, 100, 47, fonte=_F_ANTON,
                               forma=FormaPreco.TAG_ARREDONDADA,
                               forma_cor=verde, borda=escuro,
                               cor="#FFFFFF", tam=22.0, tam_cent=12.3,
                               rot=-1.5))
        else:
            # pctpod LARANJA: o "-XX%" CALCULADO veste a pílula (F9)
            d = _legal(224, my + 156, 108, 48, papel=PapelTexto.DESCONTO,
                       fonte=_F_ANTON, nome="Desconto", rot=-1.5,
                       tam=21.0, cor="#FFFFFF")
            d.forma_preco = FormaPreco.TAG_ARREDONDADA
            d.forma_cor = laranja
            d.forma_cor_borda = escuro
            regs.append(d)
        slots.append(_slot(f"celula-fixa-{i + 1}", regs,
                           origem=(74, my), fixa=True))
    for i, (cx, cy) in enumerate(((410, 44), (729, 44),
                                  (410, 456), (729, 456)), start=1):
        slots.append(_slot(f"celula-var-{i}", [
            _img(cx + 16, cy + 16, 265, 218),
            _nome(cx + 16, cy + 248, 261, 34, fonte=_F_NUNITO,
                  alin=Alinhamento.ESQUERDA, tam=16.5, cor=escuro),
            _sub(cx + 16, cy + 284, 261, 24, fonte="Nunito-Bold.ttf",
                 alin=Alinhamento.ESQUERDA, tam=12.0, cor=escuro),
            _preco(cx + 39, cy + 314, 112, 56, fonte=_F_ANTON,
                   forma=FormaPreco.TAG_ARREDONDADA, forma_cor=laranja,
                   borda=escuro, cor="#FFFFFF", tam=27.0, tam_cent=15.0,
                   rot=-1.5),
        ], origem=(cx, cy)))
    slots.append(_slot("celula-var-5", [
        _img(434, 892, 290, 378),
        _nome(752, 990, 264, 46, fonte=_F_NUNITO,
              alin=Alinhamento.ESQUERDA, tam=20.0, cor=escuro),
        _sub(752, 1040, 264, 26, fonte="Nunito-Bold.ttf",
             alin=Alinhamento.ESQUERDA, tam=14.0, cor=escuro),
        _preco(801, 1087, 130, 63, fonte=_F_ANTON,
               forma=FormaPreco.TAG_ARREDONDADA, forma_cor=laranja,
               borda=escuro, cor="#FFFFFF", tam=31.0, tam_cent=17.0,
               rot=-1.5),
    ], origem=(410, 868)))
    # a DATA no selo preto da Coluna do Dia: Anton AMARELO (a caixa
    # existia VAZIA na 1ª galeria — defeito funcional, §3.3.1)
    slots.append(_slot("selo-validade", [
        _legal(92, 362, 152, 48, papel=PapelTexto.VALIDADE,
               fonte=_F_ANTON, nome="Validade", rot=-2.0,
               tam=28.5, cor="#F7C868"),
    ], origem=(80, 348)))
    return slots


def _peixe() -> list[Slot]:
    """gen_peixe5: CELLS = [(x, y, w, h, tipo)] — o formato mais limpo."""
    cells = (
        (54, 286, 590, 320, "wide"), (666, 286, 360, 320, "vert"),
        (54, 628, 360, 320, "vert"), (436, 628, 590, 320, "wide"),
        (54, 970, 308, 320, "vert"), (384, 970, 308, 320, "vert"),
        (714, 970, 308, 320, "vert"),
    )
    slots = []
    navy, cinza, gold = "#123243", "#7C8B93", "#9A7A16"
    rotulos = {1: "PESCA DO DIA", 4: "CORTE NOBRE"}
    for i, (x, y, w, h, tipo) in enumerate(cells, start=1):
        if tipo == "wide":
            regs = [
                _img(x + w - 286, y + 24, 262, h - 48),
                # o rótulo do destaque vira CAMPO (a heurística
                # "'Camarão' in nome" do gerador morre aqui)
                _legal(x + 32, y + 38, 250, 24, papel=PapelTexto.LIVRE,
                       fonte=_F_ARCHIVO, texto=rotulos[i],
                       nome="Rótulo", tam=9.75, cor=gold,
                       alin=Alinhamento.ESQUERDA),
                _nome(x + 32, y + 62, 260, 82, fonte=_F_FRAUNCES,
                      alin=Alinhamento.ESQUERDA, tam=23.25, cor=navy),
                _sub(x + 32, y + 152, 260, 26, fonte=_F_FRA_IT,
                     alin=Alinhamento.ESQUERDA, tam=12.75, cor=cinza),
                # texto navy PURO com R$ menor — a ÚNICA forma TEXTO
                # legítima do pacote (§3.4 conferido pelo scout)
                _preco(x + 32, y + h - 78, 260, 56, fonte=_F_FRAUNCES,
                       cor=navy, tam=34.5, tam_cent=21.4,
                       centavos_na_base=True,
                       alin=Alinhamento.ESQUERDA),
            ]
        else:
            regs = [
                _img(x + 22, y + 22, w - 44, 140),
                _nome(x + 20, y + 164, w - 40, 62, fonte=_F_FRAUNCES,
                      tam=18.75, cor=navy),
                _sub(x + 20, y + 232, w - 40, 24, fonte=_F_FRA_IT,
                     tam=11.6, cor=cinza),
                _preco(x + 20, y + 254, w - 40, 48, fonte=_F_FRAUNCES,
                       cor=navy, tam=27.75, tam_cent=17.2,
                       centavos_na_base=True),
            ]
        slots.append(_slot(f"celula-{i}", regs, origem=(x, y)))
    slots.append(_slot("selo-validade", [
        _legal(892, 124, 120, 44, papel=PapelTexto.VALIDADE,
               fonte=_F_FRAUNCES, nome="Validade", rot=-7.0,
               tam=23.25, cor=navy),
    ], origem=(877, 124)))
    return slots


def _sexta() -> list[Slot]:
    """gen_verde5: bancas (AX1/AX2) + 9 patches (PXS × 3 linhas)."""
    slots = []
    # (sem as "★" do exemplo: nenhuma fonte do pacote tem o glifo — no
    # SVG o Chromium cai no fallback do sistema; o Pillow não tem)
    rotulos = ("DIRETO DA GRANJA", "COLHEITA DA SEMANA")
    for i, (x, rot) in enumerate(((54, -5.0), (566, 4.0)), start=1):
        cx = x + 230
        slots.append(_slot(f"celula-banca-{i}", [
            _img(x + 36, 486, 388, 92),
            # o rótulo ★ dos heróis é CONTEÚDO (T4 — não está no BASE)
            _legal(x + 40, 588, 380, 24, papel=PapelTexto.LIVRE,
                   fonte=_F_ARCHIVO, texto=rotulos[i - 1], nome="Rótulo",
                   tam=9.8, cor="#DFA637"),
            _nome(x + 40, 610, 380, 34, fonte=_F_FRAUNCES,
                  tam=20.0, cor="#FDF6E9"),
            _sub(x + 40, 648, 380, 22, fonte=_F_FRA_IT,
                 tam=10.5, cor="#BFD3C2"),
            # o OVAL é ESTRUTURA (gravado no BASE) — aqui SÓ o texto
            # coral, Fraunces, centavos na base (a espec do arco_ex)
            _preco(cx - 80, 706, 160, 48, fonte=_F_FRAUNCES, rot=rot,
                   cor="#D6543C", tam=28.5, tam_cent=18.0,
                   centavos_na_base=True),
        ], origem=(x, 380)))
    rots = (-2.0, 2.0, -1.5, 2.5, -2.0, 1.5, -2.5, 2.0, -1.5)
    k = 3
    for r in range(3):                    # PY=782, passo 174 (PH+PGAP)
        for c in range(3):                # PXS = 54, 382, 710
            x, y = 54 + c * 328, 782 + r * 174
            rot = rots[k - 3]
            slots.append(_slot(f"celula-{k}", [
                # F13-BIS: a foto à ESQUERDA é o layout DO MODELO (a
                # ordem §3.5.1 supôs foto-em-cima; o gerador e o
                # PREVIEW dizem o contrário — divergência declarada)
                _img(x + 14, y + 14, 120, 134),
                _nome(x + 148, y + 24, 158, 52, fonte=_F_FRAUNCES,
                      alin=Alinhamento.ESQUERDA, tam=15.0,
                      cor="#123526"),
                _sub(x + 148, y + 78, 158, 20, fonte=_F_FRA_IT,
                     alin=Alinhamento.ESQUERDA, tam=10.1,
                     cor="#6E7A63"),
                # a tag CORAL cheia, sem borda (patch_ex)
                _preco(x + 170, y + 103, 120, 46, fonte=_F_FRAUNCES,
                       rot=rot, forma=FormaPreco.TAG_ARREDONDADA,
                       forma_cor="#D6543C", cor="#FDF6E9",
                       tam=19.5, tam_cent=12.75, centavos_na_base=True),
            ], origem=(x, y)))
            k += 1
    slots.append(_slot("selo-validade", [
        _legal(852, 116, 120, 48, papel=PapelTexto.VALIDADE,
               fonte=_F_FRAUNCES, nome="Validade", rot=-6.0,
               tam=28.5, cor="#FDF6E9"),
    ], origem=(852, 116)))
    return slots


def _sabado() -> list[Slot]:
    """gen_carne_final: masonry por COLS — a ordem visual NÃO é a ordem
    dos ids (o id vem do índice do item, coluna a coluna)."""
    rotf = (-1.5, 2, -2, 1.5, -1.5, 2.5, -2, 1.5, -1.5, 2)
    # (id, x, y, altura) — reconstruído das COLS do gerador
    cels = (
        (1, 390, 528, 228), (2, 710, 528, 228),
        (3, 70, 528, 166), (4, 70, 708, 166),
        (5, 70, 888, 166), (6, 70, 1068, 166),
        (7, 390, 770, 228), (8, 390, 1012, 228),
        (9, 710, 770, 228), (10, 710, 1012, 228),
    )
    slots = []
    ink, mute, red, cream = "#33291F", "#8A7A62", "#B5372A", "#FDF6E9"

    def _bandeira(cx, cy, rot):
        # a bandeirola CAVALGA a borda inferior da célula (cy = borda);
        # RED cheia, ponta à direita, texto CREAM com centavos na base
        return _preco(cx - 56, cy - 20, 112, 40, fonte=_F_FRAUNCES,
                      rot=rot, forma=FormaPreco.ETIQUETA_GIRADA,
                      forma_cor=red, cor=cream, tam=18.75,
                      tam_cent=12.75, centavos_na_base=True)

    for cid, x, y, alt in cels:
        rot = rotf[cid - 1]
        if cid == 1:                       # o "Corte da Semana" (destaque)
            regs = [
                _img(406, 542, 274, 104),
                # texto DOURADO puro (a ordem supôs fita vermelha; o
                # gerador diz Archivo #A8801F + roseta — divergência
                # declarada; a roseta é adorno vetorial, fica de fora)
                _legal(405, 632, 276, 24, papel=PapelTexto.LIVRE,
                       fonte=_F_ARCHIVO, texto="CORTE DA SEMANA",
                       nome="Chamada", tam=8.6, cor="#A8801F"),
                _nome(408, 656, 270, 30, fonte=_F_FRAUNCES,
                      tam=16.5, cor=ink),
                _sub(408, 688, 270, 20, fonte=_F_FRA_IT,
                     tam=10.1, cor=mute),
                _bandeira(x + 153, y + alt, rot),
            ]
        elif alt == 166:                   # célula curta (1ª coluna)
            regs = [
                _img(x + 16, y + 12, 274, 80),
                _nome(x + 18, y + 94, 270, 28, fonte=_F_FRAUNCES,
                      tam=16.5, cor=ink),
                _sub(x + 18, y + 124, 270, 20, fonte=_F_FRA_IT,
                     tam=10.1, cor=mute),
                _bandeira(x + 153, y + alt, rot),
            ]
        else:                              # célula alta (2ª/3ª colunas)
            regs = [
                _img(x + 16, y + 14, 274, 124),
                _nome(x + 18, y + 148, 270, 28, fonte=_F_FRAUNCES,
                      tam=16.5, cor=ink),
                _sub(x + 18, y + 178, 270, 20, fonte=_F_FRA_IT,
                     tam=10.1, cor=mute),
                _bandeira(x + 153, y + alt, rot),
            ]
        slots.append(_slot(f"celula-{cid}", regs, origem=(x, y)))
    slots.append(_slot("selo-validade", [
        _legal(876, 146, 120, 44, papel=PapelTexto.VALIDADE,
               fonte=_F_FRAUNCES, nome="Validade", rot=9.0,
               tam=25.5, cor=red),
    ], origem=(856, 146)))
    return slots


_J_INK, _J_GRAY, _J_LAR, _J_LARD = ("#201B12", "#6E675C",
                                    "#F58634", "#C9641A")


def _jornal_linha(pref: str, slots: list, y: float, n: int,
                  inicio: int) -> None:
    """O ``linha(y, ids)`` do gerador: até 5 colunas, x = 64 + c*198.

    O preço é o CARIMBO perfurado (borda tracejada laranja, texto
    LARD), s=0.78, rot −6/+5 alternando por coluna."""
    for c in range(n):
        x = 64 + c * 198
        rot = -6.0 if (c % 2 == 0) else 5.0
        slots.append(_slot(f"{pref}-l{inicio + c}", [
            _img(x + 4, y, 178, 96),
            _nome(x + 8, y + 96, 170, 24, fonte=_F_FRAUNCES,
                  tam=9.4, cor=_J_INK),
            _sub(x + 8, y + 120, 170, 16, fonte=_F_FRA_IT,
                 tam=7.5, cor=_J_GRAY),
            _preco(x + 49, y + 149, 88, 38, fonte=_F_FRAUNCES, rot=rot,
                   forma=FormaPreco.CARIMBO, forma_cor=_J_LAR,
                   cor=_J_LARD, tam=17.5, tam_cent=11.1,
                   centavos_na_base=True),
        ], origem=(x + 4, y)))


def _jornal_p1() -> list[Slot]:
    """gen_jornal_final::capa() — hero + 4 chamadas + 3 linhas de 5.

    N-04: o BASE zera o ``conteudo-exemplo`` INTEIRO — validade, nº da
    edição, manchete e o período editável (F8) são desenhados pelo app."""
    slots = [
        _slot("jp1-hero", [
            _img(74, 328, 384, 234),
            # a estrela SUPER OFERTA (24 pontas no modelo) sai como
            # medalhão de pétalas VERDE — a aproximação declarada
            _legal(347, 299, 114, 114, papel=PapelTexto.LIVRE,
                   fonte=_F_ARCHIVO, texto="SUPER OFERTA",
                   nome="Splash", rot=-8.0, tam=12.0, cor="#F7F3E9"),
            # a legenda da capa = nome + descritor do produto do hero
            _nome(78, 574, 376, 24, fonte=_F_FRA_IT,
                  tam=9.4, cor=_J_GRAY),
            _sub(78, 600, 376, 18, fonte=_F_FRA_IT,
                 tam=8.0, cor=_J_GRAY),
        ], origem=(74, 328)),
    ]
    splash = slots[0].regioes[1]
    splash.forma_preco = FormaPreco.MEDALHAO_ESTRELA
    splash.forma_cor = "#0F783F"
    splash.forma_cor_borda = "#F7F3E9"
    for i, (x, y) in enumerate(((488, 328), (762, 328),
                                (488, 466), (762, 466)), start=1):
        rot = -5.0 if i % 2 else 4.0
        slots.append(_slot(f"jp1-ch{i}", [
            _img(x, y, 112, 112),
            _nome(x + 112, y + 14, 168, 26, fonte=_F_FRAUNCES,
                  tam=11.6, cor=_J_INK),
            _sub(x + 112, y + 42, 168, 18, fonte=_F_FRA_IT,
                 tam=8.6, cor=_J_GRAY),
            _preco(x + 150, y + 74, 92, 40, fonte=_F_FRAUNCES, rot=rot,
                   forma=FormaPreco.CARIMBO, forma_cor=_J_LAR,
                   cor=_J_LARD, tam=18.4, tam_cent=11.7,
                   centavos_na_base=True),
        ], origem=(x, y)))
    _jornal_linha("jp1", slots, 660, 5, 1)
    _jornal_linha("jp1", slots, 882, 5, 6)
    _jornal_linha("jp1", slots, 1104, 5, 11)
    slots += [
        _slot("jp1-cabecalho", [
            # o período EDITÁVEL do F8 — o BASE regenerado (T6) está
            # limpo, então as caixas voltam a ter TINTA
            _legal(50, 72, 180, 22, papel=PapelTexto.LIVRE,
                   fonte=_F_FRA_IT, nome="Período (orelha)",
                   texto="do dia 1º ao 27,", tam=7.5, cor=_J_GRAY),
            _legal(120, 170, 840, 28, papel=PapelTexto.VALIDADE,
                   fonte="Archivo-Medium.ttf", nome="Validade",
                   tam=7.9, cor=_J_GRAY),
            _legal(870, 56, 160, 24, papel=PapelTexto.LIVRE,
                   fonte=_F_ARCHIVO, texto="Nº 177 · ANO 42",
                   nome="Edição", tam=9.0, cor=_J_INK),
        ], origem=(40, 50)),
        _slot("jp1-manchete", [
            _legal(190, 218, 700, 48, papel=PapelTexto.LIVRE,
                   fonte=_F_FRAUNCES, nome="Manchete",
                   texto="PREÇO BAIXO DO DIA 1º AO 27",
                   tam=35.0, cor=_J_INK),
            _legal(190, 270, 700, 26, papel=PapelTexto.LIVRE,
                   fonte=_F_FRA_IT, nome="Linha-fina",
                   texto="a redação conferiu preço por preço: do "
                         "pacotão de arroz ao café passado, tudo em "
                         "oferta do dia 1º ao 27",
                   tam=10.9, cor=_J_GRAY),
        ], origem=(188, 218)),
        _slot("jp1-dica", [
            # a caixa começa DEPOIS do chip verde da estrutura
            _legal(230, 1324, 770, 42, papel=PapelTexto.DICA,
                   fonte=_F_FRA_IT, nome="Fica a Dica",
                   tam=10.5, cor=_J_INK, alin=Alinhamento.ESQUERDA),
        ], origem=(64, 1314)),
    ]
    return slots


def _jornal_p2() -> list[Slot]:
    """gen_jornal_final::pagina2() — 4 linhas de 5 + linha final de 2."""
    slots: list[Slot] = []
    for i, y in enumerate((132, 334, 566, 768)):
        _jornal_linha("jp2", slots, y, 5, 1 + i * 5)
    _jornal_linha("jp2", slots, 1000, 2, 21)   # a linha final: só 2
    slots += [
        _slot("jp2-cabecalho", [
            # o BASE regenerado (T6) está limpo — o título volta
            _legal(640, 48, 320, 24, papel=PapelTexto.LIVRE,
                   fonte=_F_ARCHIVO, nome="Título da página",
                   texto="PÁGINA 2 · OFERTAS DO DIA 1º AO 27",
                   tam=9.75, cor=_J_INK),
            _legal(640, 72, 320, 22, papel=PapelTexto.VALIDADE,
                   fonte=_F_FRA_IT, nome="Validade",
                   tam=8.25, cor=_J_GRAY),
        ], origem=(640, 48)),
        _slot("jp2-dica", [
            # abaixo do chip verde da estrutura
            _legal(664, 1248, 338, 44, papel=PapelTexto.DICA,
                   fonte=_F_FRA_IT, nome="Fica a Dica",
                   tam=9.0, cor=_J_INK, alin=Alinhamento.ESQUERDA),
        ], origem=(650, 1214)),
    ]
    return slots


_BUILDERS = {
    "segunda-frios": (_segunda,),
    "terca-do-pao": (_terca,),
    "quarta-das-ofertas": (_quarta,),
    "quinta-do-peixe": (_peixe,),
    "sexta-verde": (_sexta,),
    "sabado-da-carne": (_sabado,),
    "jornal-do-mes": (_jornal_p1, _jornal_p2),
}


def chaves_do_pacote(pasta_pacote: str | Path) -> list[str]:
    """As chaves dos encartes cujo BASE.png existe na pasta do pacote."""
    raiz = Path(pasta_pacote)
    achadas = []
    for chave, (sub, bases) in _BASES.items():
        if all((raiz / "artes" / sub / b).exists() for b in bases):
            achadas.append(chave)
    return achadas


def layout_de_encarte(chave: str, pasta_pacote: str | Path) -> LayoutDef:
    """Monta o LayoutDef de um encarte do pacote a partir das TABELAS.

    A página nasce do BASE.png real (2160×2880 ⇒ dpi 192 ⇒ 285,75×381
    mm); o Jornal vira UM layout de duas páginas (fundo POR página,
    seções ligadas — N-05: a arte não traz seção; quem desenha é o app).
    """
    raiz = Path(pasta_pacote)
    sub, bases = _BASES[chave]
    caminhos = [raiz / "artes" / sub / b for b in bases]
    for c in caminhos:
        if not c.exists():
            raise FileNotFoundError(
                f"O encarte “{NOMES_EXIBICAO[chave]}” não está completo no "
                f"pacote: falta {c.name} (procurei em {c.parent})")
    paginas = []
    for caminho, builder in zip(caminhos, _BUILDERS[chave]):
        paginas.append(Pagina(
            slots=builder(),
            arquivo_fundo=str(caminho),
            # F13-BIS §3.7.2: as seções ficam DESLIGADAS no Jornal — o
            # contorno padrão é alienígena sobre o papel creme/laranja
            # (as divisórias da própria arte fazem o papel do N-05);
            # um estilo de seção POR ENCARTE é assunto do G
            secoes_ligadas=False,
        ))
    layout = layout_de_arte(str(caminhos[0]), dpi=DPI_BASE,
                            paginas=paginas)
    layout.validar_ids_unicos()
    return layout


def importar_pacote(session, pasta_pacote: str | Path,
                    raiz=None) -> list[str]:
    """Semeia na biblioteca os encartes COMPLETOS do pacote e copia as
    fontes .ttf para a pasta de fontes do app.

    Upsert por NOME (importar de novo atualiza, nunca duplica);
    ``salvar_layout`` interna as artes (I3 — nada da pasta do pacote
    sobra no JSON). Devolve as chaves importadas; encarte incompleto
    simplesmente não entra (``chaves_do_pacote`` só lista completos —
    e o Ateliê nomeia o que ficou de fora, I2)."""
    import shutil

    from app.core.paths import SystemRoot
    from app.rendering.persistencia import salvar_layout

    raiz = raiz if isinstance(raiz, SystemRoot) else SystemRoot(raiz) \
        if raiz else SystemRoot()
    pasta = Path(pasta_pacote)
    chaves = chaves_do_pacote(pasta)
    for chave in chaves:
        salvar_layout(session, NOMES_EXIBICAO[chave],
                      layout_de_encarte(chave, pasta),
                      tipo_midia="TABLOIDE", raiz=raiz)
    if chaves:
        raiz.fontes.mkdir(parents=True, exist_ok=True)
        for nome in FONTES_DO_PACOTE:
            origem = pasta / "fontes" / nome
            destino = raiz.fontes / nome
            if origem.exists() and not destino.exists():
                shutil.copy(origem, destino)
    return chaves

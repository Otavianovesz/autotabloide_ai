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


def _nome(x, y, w, h, *, fonte, rot=0.0,
          alin=Alinhamento.CENTRO) -> Regiao:
    return Regiao(TipoRegiao.NOME, _r(x, y, w, h), nome="Nome",
                  fonte=fonte, alinhamento=alin,
                  alinhamento_v=AlinhamentoV.BASE, rotacao_graus=rot)


def _sub(x, y, w, h, *, fonte, rot=0.0,
         alin=Alinhamento.CENTRO) -> Regiao:
    return Regiao(TipoRegiao.UNIDADE, _r(x, y, w, h), nome="Gramatura",
                  fonte=fonte, alinhamento=alin,
                  alinhamento_v=AlinhamentoV.BASE, rotacao_graus=rot)


def _preco(x, y, w, h, *, fonte, rot=0.0) -> Regiao:
    return Regiao(TipoRegiao.PRECO, _r(x, y, w, h), nome="Preço",
                  fonte=fonte, alinhamento=Alinhamento.CENTRO,
                  rotacao_graus=rot)


def _legal(x, y, w, h, *, papel, fonte, texto="", nome="", rot=0.0,
           alin=Alinhamento.CENTRO) -> Regiao:
    return Regiao(TipoRegiao.TEXTO_LEGAL, _r(x, y, w, h),
                  nome=nome or papel.value.title(), fonte=fonte,
                  papel_texto=papel, texto_fixo=texto, alinhamento=alin,
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
    """gen_terca_final: HX/HY/HW/HH + CX_/CY_ + BXS/BW/ROT_S."""
    slots = [
        # celula-1 FIXA (Pão Francês; o selo "50%" é da própria arte)
        _slot("celula-1", [
            _img(86, 376, 320, 214),
            _nome(429, 390, 210, 34, fonte=_F_ARCHIVO),
            _sub(429, 428, 210, 24, fonte=_F_FRA_IT),
        ], origem=(64, 352), fixa=True),
        # celula-2 FIXA (Sonho + Croissant) — 1º slot de foto ENCOLHIDO
        # (210→194 px): o selo de 25% (964,392 R54) está gravado no BASE
        # e invadia ~12×60 px do canto (F7/N-01)
        _slot("celula-2", [
            _img(712, 386, 194, 90),
            _img(712, 524, 210, 90),
            _nome(697, 624, 240, 28, fonte=_F_ARCHIVO),
            _sub(697, 656, 240, 20, fonte=_F_FRA_IT),
        ], origem=(688, 352), fixa=True),
    ]
    bxs = (64, 306, 548, 790)
    rots = (-0.7, 0.55, -0.55, 0.7)
    for i, (x, rot) in enumerate(zip(bxs, rots), start=3):
        cx = x + 113                      # BW=226
        slots.append(_slot(f"celula-{i}", [
            _img(x + 18, 756, 190, 150, rot=rot),
            _preco(cx - 55, 900, 110, 52, fonte=_F_ARCHIVO, rot=rot),
            _nome(cx - 95, 1006, 190, 38, fonte=_F_ARCHIVO, rot=rot),
        ], origem=(x, 756)))
    slots.append(_slot("selo-validade", [
        _legal(876, 106, 140, 40, papel=PapelTexto.VALIDADE,
               fonte=_F_FRAUNCES, nome="Validade", rot=8.0),
    ], origem=(876, 106)))
    return slots


def _segunda() -> list[Slot]:
    """gen_segunda3: OCX/OCY/ORX/ORY + FLANCOS + ROW_A/ROW_B."""
    slots = [
        # celula-1 FIXA (Kit Burger, a oval)
        _slot("celula-1", [
            _img(390, 352, 300, 104),
            _nome(380, 452, 320, 36, fonte=_F_ARCHIVO),
            _sub(380, 538, 320, 24, fonte=_F_FRA_IT),
        ], origem=(290, 288), fixa=True),
    ]
    # (id, origem, rot, foto, banda(nome+sub), selo do preço, lado do
    # selo NA BANDA: 'd'/'e' desviam o texto, None = selo sobre a foto)
    dados = (
        (2, (64, 288), -0.6, (84, 314, 170, 116),
         (72, 526, 194), (236, 328), None),
        (3, (806, 294), 0.5, (826, 320, 170, 116),
         (814, 532, 194), (978, 334), None),
        (4, (64, 652), -0.5, (82, 672, 268, 138),
         (69, 883, 294), (328, 886), "d"),
        (5, (388, 644), 0.4, (406, 664, 268, 138),
         (393, 875, 294), (428, 878), "e"),
        (6, (712, 654), -0.5, (730, 674, 268, 138),
         (717, 885, 294), (976, 888), "d"),
        (7, (240, 955), -0.45, (256, 973, 264, 104),
         (245, 1149, 287), (496, 1152), "d"),
        (8, (552, 948), 0.4, (568, 966, 264, 104),
         (557, 1142, 287), (592, 1145), "e"),
    )
    for i, origem, rot, foto, (bx, by, bw), (sx, sy), lado in dados:
        # inspeção visual do fecho: o nome centrado alcançava a área do
        # selo de cera — a caixa de texto DESVIA do selo quando ele
        # morde a banda (o exemplo faz o mesmo, deslocando o nome)
        if lado == "d":
            nx, nw = bx, (sx - 46) - bx
        elif lado == "e":
            nx, nw = sx + 46, (bx + bw) - (sx + 46)
        else:
            nx, nw = bx, bw
        slots.append(_slot(f"celula-{i}", [
            _img(*foto, rot=rot),
            _nome(nx, by, nw, 30, fonte=_F_ARCHIVO, rot=rot),
            _sub(nx, by + 30, nw, 22, fonte=_F_FRA_IT, rot=rot),
            _preco(sx - 42, sy - 38, 84, 76, fonte=_F_ARCHIVO, rot=rot),
        ], origem=origem))
    slots.append(_slot("selo-validade", [
        _legal(865, 74, 140, 40, papel=PapelTexto.VALIDADE,
               fonte=_F_FRAUNCES, nome="Validade", rot=10.0),
    ], origem=(865, 74)))
    return slots


def _quarta() -> list[Slot]:
    """gen_final: minis_xy (3 FIXAS na Coluna do Dia) + cards_xy + banner.

    F10/N-03: nomes em Nunito (nunca a instância Baloo 2 do pacote — o
    glifo "ã" é defeituoso e produto variável pode ter "ã"). F9/N-02: a
    3ª fixa usa papel DESCONTO — o % é CALCULADO de (de−por)/de, nunca
    digitado (compatível com o pctpod parametrizado do gerador)."""
    slots = []
    for i in range(3):                    # minis: RX+20=74, MY0=546, MH+MG=246
        my = 546 + i * 246
        regs = [
            _img(88, my + 14, 112, 204),
            _nome(212, my + 28, 148, 82, fonte=_F_NUNITO,
                  alin=Alinhamento.ESQUERDA),
        ]
        if i < 2:
            regs.append(_preco(218, my + 154, 120, 52, fonte=_F_ANTON))
        else:
            regs.append(_legal(218, my + 154, 120, 52,
                               papel=PapelTexto.DESCONTO, fonte=_F_ANTON,
                               nome="Desconto"))
        slots.append(_slot(f"celula-fixa-{i + 1}", regs,
                           origem=(74, my), fixa=True))
    for i, (cx, cy) in enumerate(((410, 44), (729, 44),
                                  (410, 456), (729, 456)), start=1):
        slots.append(_slot(f"celula-var-{i}", [
            _img(cx + 16, cy + 16, 265, 218),
            _nome(cx + 18, cy + 245, 261, 60, fonte=_F_NUNITO,
                  alin=Alinhamento.ESQUERDA),
            _preco(cx + 35, cy + 316, 120, 52, fonte=_F_ANTON),
        ], origem=(cx, cy)))
    slots.append(_slot("celula-var-5", [
        _img(434, 892, 290, 378),
        _nome(752, 986, 260, 76, fonte=_F_NUNITO,
              alin=Alinhamento.ESQUERDA),
        _preco(806, 1092, 120, 52, fonte=_F_ANTON),
    ], origem=(410, 868)))
    slots.append(_slot("selo-validade", [
        _legal(92, 358, 152, 50, papel=PapelTexto.VALIDADE,
               fonte=_F_NUNITO, nome="Validade", rot=-2.0),
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
    for i, (x, y, w, h, tipo) in enumerate(cells, start=1):
        if tipo == "wide":
            regs = [
                _img(x + w - 286, y + 24, 262, h - 48),
                _nome(x + 32, y + 66, 250, 74, fonte=_F_ARCHIVO,
                      alin=Alinhamento.ESQUERDA),
                _sub(x + 32, y + 142, 250, 26, fonte=_F_FRA_IT,
                     alin=Alinhamento.ESQUERDA),
                _preco(x + 32, y + 240, 250, 54, fonte=_F_ARCHIVO),
            ]
        else:
            regs = [
                _img(x + 22, y + 22, w - 44, 140),
                _nome(x + 20, y + 170, w - 40, 58, fonte=_F_ARCHIVO),
                _sub(x + 20, y + 230, w - 40, 24, fonte=_F_FRA_IT),
                _preco(x + 20, y + 256, w - 40, 46, fonte=_F_ARCHIVO),
            ]
        slots.append(_slot(f"celula-{i}", regs, origem=(x, y)))
    slots.append(_slot("selo-validade", [
        _legal(877, 124, 150, 44, papel=PapelTexto.VALIDADE,
               fonte=_F_FRAUNCES, nome="Validade", rot=-7.0),
    ], origem=(877, 124)))
    return slots


def _sexta() -> list[Slot]:
    """gen_verde5: bancas (AX1/AX2) + 9 patches (PXS × 3 linhas)."""
    slots = []
    for i, (x, rot) in enumerate(((54, -5.0), (566, 4.0)), start=1):
        slots.append(_slot(f"celula-banca-{i}", [
            _img(x + 36, 486, 388, 92),
            _nome(x + 40, 610, 380, 32, fonte=_F_ARCHIVO),
            _sub(x + 40, 642, 380, 24, fonte=_F_FRA_IT),
            _preco(x + 150, 690, 160, 56, fonte=_F_ARCHIVO, rot=rot),
        ], origem=(x, 380)))
    rots = (-2.0, 2.0, -1.5, 2.5, -2.0, 1.5, -2.5, 2.0, -1.5)
    k = 3
    for r in range(3):                    # PY=782, passo 174 (PH+PGAP)
        for c in range(3):                # PXS = 54, 382, 710
            x, y = 54 + c * 328, 782 + r * 174
            rot = rots[k - 3]
            slots.append(_slot(f"celula-{k}", [
                _img(x + 14, y + 14, 120, 134),
                _nome(x + 148, y + 24, 158, 56, fonte=_F_ARCHIVO,
                      alin=Alinhamento.ESQUERDA),
                _preco(x + 170, y + 100, 120, 46, fonte=_F_ARCHIVO,
                       rot=rot),
            ], origem=(x, y)))
            k += 1
    slots.append(_slot("selo-validade", [
        _legal(859, 118, 150, 42, papel=PapelTexto.VALIDADE,
               fonte=_F_FRAUNCES, nome="Validade", rot=-6.0),
    ], origem=(859, 118)))
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
    for cid, x, y, alt in cels:
        rot = rotf[cid - 1]
        # (inspeção visual do fecho: sub e preço NUNCA dividem faixa —
        # a 1ª galeria saiu com "100 g" espremido sobre o "R$")
        if cid == 1:                       # o "Corte da Semana" (destaque)
            regs = [
                _img(406, 542, 274, 104),
                _legal(405, 646, 276, 26, papel=PapelTexto.LIVRE,
                       fonte=_F_FRA_IT, texto="★ CORTE DA SEMANA",
                       nome="Chamada"),
                _nome(408, 670, 270, 30, fonte=_F_ARCHIVO),
                _sub(408, 702, 270, 16, fonte=_F_FRA_IT),
                _preco(483, 722, 120, 32, fonte=_F_ARCHIVO, rot=rot),
            ]
        elif alt == 166:                   # célula curta (1ª coluna)
            regs = [
                _img(x + 16, y + 12, 274, 80),
                _nome(x + 18, y + 92, 270, 28, fonte=_F_ARCHIVO),
                _sub(x + 18, y + 118, 270, 16, fonte=_F_FRA_IT),
                _preco(x + 93, y + 136, 120, 30, fonte=_F_ARCHIVO,
                       rot=rot),
            ]
        else:                              # célula alta (2ª/3ª colunas)
            regs = [
                _img(x + 16, y + 14, 274, 124),
                _nome(x + 18, y + 144, 270, 30, fonte=_F_ARCHIVO),
                _sub(x + 18, y + 174, 270, 16, fonte=_F_FRA_IT),
                _preco(x + 93, y + 194, 120, 32, fonte=_F_ARCHIVO,
                       rot=rot),
            ]
        slots.append(_slot(f"celula-{cid}", regs, origem=(x, y)))
    slots.append(_slot("selo-validade", [
        _legal(856, 146, 160, 44, papel=PapelTexto.VALIDADE,
               fonte=_F_FRAUNCES, nome="Validade", rot=9.0),
    ], origem=(856, 146)))
    return slots


def _jornal_linha(pref: str, slots: list, y: float, n: int,
                  inicio: int) -> None:
    """O ``linha(y, ids)`` do gerador: até 5 colunas, x = 64 + c*198."""
    for c in range(n):
        x = 64 + c * 198
        rot = -5.0 if (c % 2 == 0) else 4.0
        slots.append(_slot(f"{pref}-l{inicio + c}", [
            _img(x + 4, y, 178, 96),
            _nome(x + 8, y + 96, 170, 24, fonte=_F_FRAUNCES),
            _sub(x + 8, y + 120, 170, 18, fonte=_F_FRA_IT),
            _preco(x + 33, y + 130, 120, 40, fonte=_F_ARCHIVO, rot=rot),
        ], origem=(x + 4, y)))


def _jornal_p1() -> list[Slot]:
    """gen_jornal_final::capa() — hero + 4 chamadas + 3 linhas de 5.

    N-04: o BASE zera o ``conteudo-exemplo`` INTEIRO — validade, nº da
    edição, manchete e o período editável (F8) são desenhados pelo app."""
    slots = [
        _slot("jp1-hero", [
            _img(74, 328, 384, 234),
            _nome(78, 574, 376, 28, fonte=_F_FRA_IT),
            _preco(348, 330, 112, 52, fonte=_F_ARCHIVO, rot=-6.0),
        ], origem=(74, 328)),
    ]
    for i, (x, y) in enumerate(((488, 328), (762, 328),
                                (488, 466), (762, 466)), start=1):
        rot = -5.0 if i % 2 else 4.0
        slots.append(_slot(f"jp1-ch{i}", [
            _img(x, y, 112, 112),
            _nome(x + 116, y + 8, 160, 26, fonte=_F_FRAUNCES),
            _sub(x + 116, y + 36, 160, 20, fonte=_F_FRA_IT),
            _preco(x + 136, y + 50, 120, 42, fonte=_F_ARCHIVO, rot=rot),
        ], origem=(x, y)))
    _jornal_linha("jp1", slots, 660, 5, 1)
    _jornal_linha("jp1", slots, 882, 5, 6)
    _jornal_linha("jp1", slots, 1104, 5, 11)
    slots += [
        _slot("jp1-cabecalho", [
            # o período editável (F8) — a ORELHA fica de caixa pronta e
            # SEM tinta: o BASE atual (pré-regeração) ainda traz "mês
            # inteiro de" gravado, e escrever ali duplica o texto
            # (inspeção visual do fecho). Após a regeração o dono liga.
            _legal(50, 72, 180, 22, papel=PapelTexto.LIVRE,
                   fonte=_F_FRA_IT, nome="Período (orelha)"),
            _legal(120, 170, 840, 28, papel=PapelTexto.VALIDADE,
                   fonte=_F_FRAUNCES, nome="Validade"),
            _legal(870, 56, 160, 24, papel=PapelTexto.LIVRE,
                   fonte=_F_ARCHIVO, texto="Nº 177 · ANO 42",
                   nome="Edição"),
        ], origem=(40, 50)),
        _slot("jp1-manchete", [
            # idem: a manchete/linha-fina do BASE atual ainda dizem "O
            # MÊS INTEIRO…" — as caixas nascem VAZIAS até a regeração
            _legal(190, 218, 700, 48, papel=PapelTexto.LIVRE,
                   fonte=_F_FRAUNCES, nome="Manchete"),
            _legal(190, 270, 700, 26, papel=PapelTexto.LIVRE,
                   fonte=_F_FRA_IT, nome="Linha-fina"),
        ], origem=(188, 218)),
        _slot("jp1-dica", [
            _legal(80, 1324, 920, 42, papel=PapelTexto.DICA,
                   fonte=_F_FRA_IT, nome="Fica a Dica"),
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
            # caixa pronta e SEM tinta até a regeração — o BASE atual
            # ainda traz "OFERTAS DO MÊS INTEIRO" gravado nesse lugar
            _legal(640, 48, 320, 24, papel=PapelTexto.LIVRE,
                   fonte=_F_ARCHIVO, nome="Título da página"),
            _legal(640, 72, 320, 22, papel=PapelTexto.VALIDADE,
                   fonte=_F_FRA_IT, nome="Validade"),
        ], origem=(640, 48)),
        _slot("jp2-dica", [
            _legal(664, 1226, 338, 64, papel=PapelTexto.DICA,
                   fonte=_F_FRA_IT, nome="Fica a Dica"),
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
            secoes_ligadas=(chave == "jornal-do-mes"),
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

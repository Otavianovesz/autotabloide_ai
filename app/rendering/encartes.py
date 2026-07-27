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
    # F13-TER: o QUINTOU — o encarte que o dono entrega TODA SEMANA
    # ficou fora do pacote dos 7 (veio do Illustrator, sem gerador).
    # A geometria foi MEDIDA por diff do Fundo limpo contra o Real
    # publicado ("./" = pasta relativa à raiz do pacote, não a artes/)
    # F13-TER §9.4: FRENTE + VERSO — o Quintou é o que ele entrega
    # toda semana (o "fundo" do verso vem em minúsculo do Illustrator)
    "quintou": ("./Quintou", ("Quintou Frente Fundo.png",
                              "Quintou Verso fundo.png")),
}

NOMES_EXIBICAO = {
    "quintou": "Quintou do Real",
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
    from app.rendering.model import Ajuste
    # F13-TER/V1: as fotos dos encartes ASSENTAM — recorte pela bbox do
    # alfa (o quadrado do acervo morre), maior escala que caiba, âncora
    # no rodapé da zona
    return Regiao(TipoRegiao.IMAGEM, _r(x, y, w, h), nome="Foto",
                  rotacao_graus=rot, ajuste=Ajuste.ASSENTAR)


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
        # celula-1 FIXA (Pão Francês) — F13-TER: a zona da foto cresceu
        # ao painel inteiro (84,372,330,268 — para antes do selo 50%,
        # que é circular e não se recola por retângulo); nome +1 degrau
        _slot("celula-1", [
            _img(84, 372, 330, 268),
            _nome(324, 380, 420, 46, fonte=_F_FRAUNCES,
                  tam=33.0, cor="#33200F"),
            _sub(324, 432, 420, 22, fonte=_F_FRA_IT,
                 tam=10.9, cor="#96826A"),
            # (sem a "★" do exemplo: a Caveat não tem o glifo — no
            # modelo a estrela é um path vetorial, adorno da arte)
            _legal(100, 652, 280, 34, papel=PapelTexto.LIVRE,
                   fonte="Caveat-Bold.ttf", nome="Manuscrito",
                   texto="metade do preço, é hoje!", rot=-1.5,
                   tam=21.0, cor="#A03A22"),
        ], origem=(64, 352), fixa=True),
        # celula-2 FIXA (Sonho + Croissant) — zonas estendidas até o
        # claro do selo 25% e do "+" da estrutura (folga 4 px)
        _slot("celula-2", [
            _img(706, 372, 192, 108),
            _img(706, 518, 292, 102),
            _nome(697, 628, 240, 28, fonte=_F_FRAUNCES,
                  tam=18.75, cor="#33200F"),
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
            # V2: o pão desce ATRÁS da cesta (zona até y=1000) e a
            # aba+corpo do vime VOLTAM por cima (adornos do inventário)
            _img(x - 8 + 18, 748, 206, 252, rot=rot),
            Regiao(TipoRegiao.ADORNO, _r(x - 1, 911, 228, 97),
                   nome="Cesta"),
            Regiao(TipoRegiao.ADORNO, _r(x + 10, 903, 101, 39),
                   nome="Pano"),
            # o disco pendurado cresceu R 36→40 (o preço +1 degrau)
            _preco(cx - 40, 912, 80, 80, fonte=_F_FRAUNCES,
                   rot=rot, forma=FormaPreco.ETIQUETA_PENDURADA,
                   forma_cor="#C94F32", borda="#A03A22",
                   cor="#FFF9EC", tam=19.5, tam_cent=12.4,
                   centavos_na_base=True),
            _legal(cx - 95, 1014, 190, 12, papel=PapelTexto.LIVRE,
                   fonte=_F_ARCHIVO, nome="Rótulo",
                   texto="· PADARIA BELO BRASIL ·", rot=prot,
                   tam=6.0, cor="#C77E38"),
            _nome(cx - 95, 1026, 190, 22, fonte=_F_FRAUNCES,
                  tam=13.1, cor="#33200F", rot=prot),
            _sub(cx - 95, 1050, 190, 15, fonte=_F_FRA_IT,
                 tam=7.5, cor="#96826A", rot=prot),
        ], origem=(x, 748)))
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
        # celula-1 FIXA (Kit Burger) — F13-TER: a foto ocupa a oval
        # inteira e a FITA da marca volta por cima; nome +1 degrau
        _slot("celula-1", [
            # (laço TER: a foto até 476 cobria o nome — para em 446)
            _img(384, 356, 312, 90),
            Regiao(TipoRegiao.ADORNO, _r(314, 496, 452, 38),
                   nome="Fita da marca"),
            _nome(380, 452, 320, 40, fonte=_F_FRAUNCES,
                  tam=24.0, cor="#17293B"),
            _sub(380, 540, 320, 24, fonte=_F_FRA_IT,
                 tam=9.4, cor="#6E7F8D"),
            _preco(688, 470, 92, 92, fonte=_F_FRAUNCES,
                   forma=FormaPreco.MEDALHAO_ESTRELA,
                   forma_cor="#E9B23A", borda="#C08F1F",
                   cor="#17293B", tam=25.0, tam_cent=15.8,
                   centavos_na_base=True),
        ], origem=(290, 288), fixa=True),
    ]
    # (id, nº do chip, origem, rot, foto, chip(x,y), selo(cx,cy,R),
    #  nome(cx ou caixa), zona do texto)
    # flancos: texto na BANDA de baixo, selo SOBRE A FOTO; etiquetas:
    # selo morde a banda e o texto DESVIA (tcx do gerador)
    flancos = (
        # F13-TER: foto estendida ATRÁS da banda azul, banda recolada
        (2, (64, 288), -0.6, (78, 302, 182, 248), (68, 522, 202, 60),
         (76, 302), (236, 328, 32), 169, 548),
        (3, (806, 294), 0.5, (820, 308, 182, 248), (810, 528, 202, 60),
         (818, 308), (978, 334, 32), 911, 554),
    )
    for i, origem, rot, foto, banda, (chx, chy), (sx, sy, sr), tcx, ty \
            in flancos:
        slots.append(_slot(f"celula-{i}", [
            _img(*foto, rot=rot),
            Regiao(TipoRegiao.ADORNO, _r(*banda), nome="Banda"),
            _chip_num(chx, chy, f"Nº {i:02d}", rot),
            _preco(sx - sr, sy - sr, sr * 2, sr * 2, fonte=_F_FRAUNCES,
                   rot=rot, forma=FormaPreco.MEDALHAO_ESTRELA,
                   forma_cor="#E9B23A", borda="#C08F1F", cor="#17293B",
                   tam=18.0, tam_cent=11.4, centavos_na_base=True),
            _nome(tcx - 93, ty - 24, 186, 26, fonte=_F_FRAUNCES,
                  tam=12.75, cor="#FFFFFF", rot=rot),
            _sub(tcx - 93, ty + 2, 186, 18, fonte=_F_FRA_IT,
                 tam=7.9, cor="#BCD2E4", rot=rot),
        ], origem=origem))
    # (id, origem, rot, foto ESTENDIDA, adornos [(x,y,w,h)...], chip,
    #  selo(cx,cy,R), tcx, y_nome, tam_nome, tam_sub, tam_preco)
    etiquetas = (
        (4, (64, 652), -0.5, (76, 662, 280, 245),
         ((66, 654, 26, 26), (340, 654, 26, 26), (65, 879, 302, 64)),
         (76, 664), (328, 886, 38), 180, 906, 15.0, 8.6, 21.4),
        (5, (388, 644), 0.4, (400, 654, 280, 245),
         ((390, 646, 26, 26), (664, 646, 26, 26), (389, 871, 302, 64)),
         (398, 656), (428, 878, 38), 568, 898, 15.0, 8.6, 21.4),
        (6, (712, 654), -0.5, (724, 664, 280, 245),
         ((714, 656, 26, 26), (988, 656, 26, 26), (713, 881, 302, 64)),
         (722, 666), (976, 888, 38), 828, 908, 15.0, 8.6, 21.4),
        (7, (240, 955), -0.45, (252, 964, 272, 209),
         ((240, 1145, 296, 62),),
         (250, 965), (496, 1152, 35), 352, 1171, 13.9, 8.2, 19.8),
        (8, (552, 948), 0.4, (564, 957, 272, 209),
         ((552, 1138, 296, 62),),
         (562, 958), (592, 1145, 35), 728, 1164, 13.9, 8.2, 19.8),
    )
    for i, origem, rot, foto, adornos, (chx, chy), (sx, sy, sr), tcx, \
            ny, tn, ts, tp in etiquetas:
        regs = [_img(*foto, rot=rot)]
        regs += [Regiao(TipoRegiao.ADORNO, _r(*a), nome="Adorno")
                 for a in adornos]
        regs += [
            _chip_num(chx, chy, f"Nº {i:02d}", rot),
            _preco(sx - sr, sy - sr, sr * 2, sr * 2, fonte=_F_FRAUNCES,
                   rot=rot, forma=FormaPreco.MEDALHAO_ESTRELA,
                   forma_cor="#E9B23A", borda="#C08F1F", cor="#17293B",
                   tam=tp, tam_cent=round(tp * 0.63, 1),
                   centavos_na_base=True),
            _nome(tcx - 100, ny - 24, 200, 26, fonte=_F_FRAUNCES,
                  tam=tn, cor="#FFFFFF", rot=rot),
            _sub(tcx - 100, ny + 2, 200, 18, fonte=_F_FRA_IT,
                 tam=ts, cor="#BCD2E4", rot=rot),
        ]
        slots.append(_slot(f"celula-{i}", regs, origem=origem))
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
            # F13-TER: zona estendida (inset 8 provado contra o canto)
            _img(82, my + 8, 122, 216),
            _nome(212, my + 34, 148, 60, fonte=_F_NUNITO,
                  alin=Alinhamento.ESQUERDA, tam=17.5, cor=escuro),
            # a linha do peso do modelo ("BBX 100g" — cola no nome)
            _sub(212, my + 98, 148, 22, fonte="Nunito-Bold.ttf",
                 alin=Alinhamento.ESQUERDA, tam=12.0, cor=escuro),
        ]
        if i < 2:
            # pricepod VERDE, centro (278, my+180), sobrescrito
            regs.append(_preco(224, my + 154, 108, 52, fonte=_F_ANTON,
                               forma=FormaPreco.TAG_ARREDONDADA,
                               forma_cor=verde, borda=escuro,
                               cor="#FFFFFF", tam=24.5, tam_cent=13.8,
                               rot=-1.5))
        else:
            # pctpod LARANJA: o "-XX%" CALCULADO veste a pílula (F9)
            d = _legal(224, my + 154, 108, 52, papel=PapelTexto.DESCONTO,
                       fonte=_F_ANTON, nome="Desconto", rot=-1.5,
                       tam=23.0, cor="#FFFFFF")
            d.forma_preco = FormaPreco.TAG_ARREDONDADA
            d.forma_cor = laranja
            d.forma_cor_borda = escuro
            regs.append(d)
        slots.append(_slot(f"celula-fixa-{i + 1}", regs,
                           origem=(74, my), fixa=True))
    for i, (cx, cy) in enumerate(((410, 44), (729, 44),
                                  (410, 456), (729, 456)), start=1):
        slots.append(_slot(f"celula-var-{i}", [
            _img(cx + 8, cy + 8, 281, 236),
            _nome(cx + 16, cy + 248, 261, 34, fonte=_F_NUNITO,
                  alin=Alinhamento.ESQUERDA, tam=18.5, cor=escuro),
            _sub(cx + 16, cy + 284, 261, 24, fonte="Nunito-Bold.ttf",
                 alin=Alinhamento.ESQUERDA, tam=13.0, cor=escuro),
            _preco(cx + 35, cy + 311, 120, 62, fonte=_F_ANTON,
                   forma=FormaPreco.TAG_ARREDONDADA, forma_cor=laranja,
                   borda=escuro, cor="#FFFFFF", tam=30.0, tam_cent=16.8,
                   rot=-1.5),
        ], origem=(cx, cy)))
    slots.append(_slot("celula-var-5", [
        _img(420, 878, 320, 406),
        _nome(752, 990, 264, 46, fonte=_F_NUNITO,
              alin=Alinhamento.ESQUERDA, tam=22.5, cor=escuro),
        _sub(752, 1040, 264, 26, fonte="Nunito-Bold.ttf",
             alin=Alinhamento.ESQUERDA, tam=14.0, cor=escuro),
        _preco(796, 1083, 140, 70, fonte=_F_ANTON,
               forma=FormaPreco.TAG_ARREDONDADA, forma_cor=laranja,
               borda=escuro, cor="#FFFFFF", tam=35.0, tam_cent=19.0,
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
    for i, (x, y, w, h, tipo) in enumerate(cells, start=1):
        if tipo == "wide":
            fx = x + w - 286
            regs = [
                # F13-TER: foto até a moldura; as bordas finas voltam
                _img(fx, y + 3, 283, 314),
                Regiao(TipoRegiao.ADORNO, _r(fx - 3, y + 3, 286, 9),
                       nome="Moldura"),
                Regiao(TipoRegiao.ADORNO, _r(fx + 274, y + 3, 9, 314),
                       nome="Moldura"),
                Regiao(TipoRegiao.ADORNO, _r(fx - 3, y + 308, 286, 9),
                       nome="Moldura"),
                # D2: o rótulo do destaque é etiqueta OPCIONAL — nasce
                # VAZIO (vazio não desenha; nunca um rótulo mentindo)
                _legal(x + 32, y + 38, 250, 24, papel=PapelTexto.LIVRE,
                       fonte=_F_ARCHIVO, texto="",
                       nome="Etiqueta", tam=9.75, cor=gold,
                       alin=Alinhamento.ESQUERDA),
                _nome(x + 32, y + 60, 260, 86, fonte=_F_FRAUNCES,
                      alin=Alinhamento.ESQUERDA, tam=26.0, cor=navy),
                _sub(x + 32, y + 152, 260, 26, fonte=_F_FRA_IT,
                     alin=Alinhamento.ESQUERDA, tam=12.75, cor=cinza),
                # texto navy PURO com R$ menor — a ÚNICA forma TEXTO
                # legítima do pacote (§3.4 conferido pelo scout)
                _preco(x + 32, y + h - 82, 260, 60, fonte=_F_FRAUNCES,
                       cor=navy, tam=38.0, tam_cent=23.5,
                       centavos_na_base=True,
                       alin=Alinhamento.ESQUERDA),
            ]
        else:
            regs = [
                _img(x + 3, y + 3, w - 6, 169),
                Regiao(TipoRegiao.ADORNO, _r(x + 3, y + 3, w - 6, 9),
                       nome="Moldura"),
                Regiao(TipoRegiao.ADORNO, _r(x + 3, y + 3, 9, 169),
                       nome="Moldura"),
                Regiao(TipoRegiao.ADORNO, _r(x + w - 12, y + 3, 9, 169),
                       nome="Moldura"),
                _nome(x + 20, y + 164, w - 40, 62, fonte=_F_FRAUNCES,
                      tam=21.0, cor=navy),
                _sub(x + 20, y + 232, w - 40, 24, fonte=_F_FRA_IT,
                     tam=11.6, cor=cinza),
                _preco(x + 20, y + 250, w - 40, 52, fonte=_F_FRAUNCES,
                       cor=navy, tam=31.0, tam_cent=19.2,
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
    for i, (x, rot) in enumerate(((54, -5.0), (566, 4.0)), start=1):
        cx = x + 230
        slots.append(_slot(f"celula-banca-{i}", [
            # F13-TER: a foto SOBE atrás do toldo listrado, recolado
            _img(x + 36, 402, 388, 188),
            Regiao(TipoRegiao.ADORNO, _r(x - 14, 398, 488, 75),
                   nome="Toldo"),
            # D2: etiqueta OPCIONAL — nasce vazia (o dono escolhe)
            _legal(x + 40, 588, 380, 24, papel=PapelTexto.LIVRE,
                   fonte=_F_ARCHIVO, texto="", nome="Etiqueta",
                   tam=9.8, cor="#DFA637"),
            _nome(x + 40, 608, 380, 36, fonte=_F_FRAUNCES,
                  tam=22.5, cor="#FDF6E9"),
            _sub(x + 40, 648, 380, 22, fonte=_F_FRA_IT,
                 tam=10.5, cor="#BFD3C2"),
            # o OVAL é ESTRUTURA (gravado no BASE) — aqui SÓ o texto
            # coral, Fraunces, centavos na base (a espec do arco_ex)
            _preco(cx - 85, 704, 170, 52, fonte=_F_FRAUNCES, rot=rot,
                   cor="#D6543C", tam=31.0, tam_cent=19.5,
                   centavos_na_base=True),
        ], origem=(x, 380)))
    rots = (-2.0, 2.0, -1.5, 2.5, -2.0, 1.5, -2.5, 2.0, -1.5)
    k = 3
    for r in range(3):                    # PY=782, passo 174 (PH+PGAP)
        for c in range(3):                # PXS = 54, 382, 710
            x, y = 54 + c * 328, 782 + r * 174
            rot = rots[k - 3]
            slots.append(_slot(f"celula-{k}", [
                # F13-BIS: a foto à ESQUERDA é o layout DO MODELO;
                # F13-TER: estendida até a moldura, cantoneiras voltam
                _img(x + 8, y + 8, 132, 146),
                Regiao(TipoRegiao.ADORNO, _r(x + 7, y + 7, 16, 16),
                       nome="Cantoneira"),
                Regiao(TipoRegiao.ADORNO, _r(x + 7, y + 140, 16, 16),
                       nome="Cantoneira"),
                _nome(x + 148, y + 24, 158, 52, fonte=_F_FRAUNCES,
                      alin=Alinhamento.ESQUERDA, tam=17.0,
                      cor="#123526"),
                _sub(x + 148, y + 78, 158, 20, fonte=_F_FRA_IT,
                     alin=Alinhamento.ESQUERDA, tam=10.1,
                     cor="#6E7A63"),
                # a tag CORAL cheia, sem borda (patch_ex)
                _preco(x + 165, y + 100, 130, 50, fonte=_F_FRAUNCES,
                       rot=rot, forma=FormaPreco.TAG_ARREDONDADA,
                       forma_cor="#D6543C", cor="#FDF6E9",
                       tam=22.0, tam_cent=14.0, centavos_na_base=True),
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
        return _preco(cx - 62, cy - 22, 124, 44, fonte=_F_FRAUNCES,
                      rot=rot, forma=FormaPreco.ETIQUETA_GIRADA,
                      forma_cor=red, cor=cream, tam=21.0,
                      tam_cent=14.2, centavos_na_base=True)

    def _molduras(x, y, alt):
        # F13-TER/V2: a borda "à mão" (tinta_rect) volta por cima da
        # foto estendida — topo e as duas laterais
        return [
            Regiao(TipoRegiao.ADORNO, _r(x - 6, y - 6, 318, 12),
                   nome="Moldura"),
            Regiao(TipoRegiao.ADORNO, _r(x - 6, y - 6, 12, alt + 12),
                   nome="Moldura"),
            Regiao(TipoRegiao.ADORNO, _r(x + 300, y - 6, 12, alt + 12),
                   nome="Moldura"),
        ]

    # F13-TER: as células desenham de BAIXO para CIMA — a bandeirola
    # cavalga a borda inferior, e a moldura recolada (ADORNO) da célula
    # de baixo a cobriria se desenhasse depois (pego pela inspeção)
    for cid, x, y, alt in sorted(cels, key=lambda c: -c[2]):
        rot = rotf[cid - 1]
        if cid == 1:                       # o destaque
            regs = [
                _img(390, 528, 306, 128),
                *_molduras(x, y, alt),
                # D2: etiqueta OPCIONAL (nasce vazia; a inspeção põe a
                # que é verdade — texto dourado, sem fita: o gerador)
                _legal(405, 656, 276, 24, papel=PapelTexto.LIVRE,
                       fonte=_F_ARCHIVO, texto="",
                       nome="Etiqueta", tam=8.6, cor="#A8801F"),
                _nome(408, 678, 270, 30, fonte=_F_FRAUNCES,
                      tam=18.5, cor=ink),
                _sub(408, 710, 270, 20, fonte=_F_FRA_IT,
                     tam=10.1, cor=mute),
                _bandeira(x + 153, y + alt, rot),
            ]
        elif alt == 166:                   # célula curta (1ª coluna)
            regs = [
                _img(x, y, 306, 94),
                *_molduras(x, y, alt),
                _nome(x + 18, y + 96, 270, 28, fonte=_F_FRAUNCES,
                      tam=18.5, cor=ink),
                _sub(x + 18, y + 126, 270, 20, fonte=_F_FRA_IT,
                     tam=10.1, cor=mute),
                _bandeira(x + 153, y + alt, rot),
            ]
        else:                              # célula alta (2ª/3ª colunas)
            regs = [
                _img(x, y, 306, 148),
                *_molduras(x, y, alt),
                _nome(x + 18, y + 150, 270, 30, fonte=_F_FRAUNCES,
                      tam=18.5, cor=ink),
                _sub(x + 18, y + 182, 270, 20, fonte=_F_FRA_IT,
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
            # F13-TER: a foto sobe até o fio da linha (recolado)
            _img(x + 4, y - 20, 178, 116),
            Regiao(TipoRegiao.ADORNO, _r(x, y - 20, 186, 6),
                   nome="Fio"),
            _nome(x + 8, y + 96, 170, 24, fonte=_F_FRAUNCES,
                  tam=11.0, cor=_J_INK),
            _sub(x + 8, y + 120, 170, 16, fonte=_F_FRA_IT,
                 tam=8.5, cor=_J_GRAY),
            _preco(x + 45, y + 147, 96, 42, fonte=_F_FRAUNCES, rot=rot,
                   forma=FormaPreco.CARIMBO, forma_cor=_J_LAR,
                   cor=_J_LARD, tam=20.0, tam_cent=12.6,
                   centavos_na_base=True),
        ], origem=(x + 4, y)))


def _jornal_p1() -> list[Slot]:
    """gen_jornal_final::capa() — hero + 4 chamadas + 3 linhas de 5.

    N-04: o BASE zera o ``conteudo-exemplo`` INTEIRO — validade, nº da
    edição, manchete e o período editável (F8) são desenhados pelo app."""
    slots = [
        _slot("jp1-hero", [
            _img(74, 308, 384, 266),
            Regiao(TipoRegiao.ADORNO, _r(236, 308, 226, 3),
                   nome="Fio"),
            # a estrela SUPER OFERTA (24 pontas no modelo) sai como
            # medalhão de pétalas VERDE — a aproximação declarada.
            # D2: etiqueta OPCIONAL — nasce VAZIA (vazia = a forma nem
            # desenha); o dono escolhe o rótulo (a inspeção põe o real)
            _legal(347, 299, 114, 114, papel=PapelTexto.LIVRE,
                   fonte=_F_ARCHIVO, texto="",
                   nome="Splash", rot=-8.0, tam=12.0, cor="#F7F3E9"),
            # a legenda da capa = nome + descritor do produto do hero
            _nome(78, 574, 376, 24, fonte=_F_FRA_IT,
                  tam=9.4, cor=_J_GRAY),
            _sub(78, 600, 376, 18, fonte=_F_FRA_IT,
                 tam=8.0, cor=_J_GRAY),
        ], origem=(74, 328)),
    ]
    splash = next(r for r in slots[0].regioes if r.nome == "Splash")
    splash.forma_preco = FormaPreco.MEDALHAO_ESTRELA
    splash.forma_cor = "#0F783F"
    splash.forma_cor_borda = "#F7F3E9"
    for i, (x, y) in enumerate(((488, 328), (762, 328),
                                (488, 466), (762, 466)), start=1):
        rot = -5.0 if i % 2 else 4.0
        dy = 20 if i <= 2 else 18
        slots.append(_slot(f"jp1-ch{i}", [
            _img(x, y - dy, 112, 112 + dy),
            _nome(x + 112, y + 14, 168, 26, fonte=_F_FRAUNCES,
                  tam=13.0, cor=_J_INK),
            _sub(x + 112, y + 42, 168, 18, fonte=_F_FRA_IT,
                 tam=9.4, cor=_J_GRAY),
            _preco(x + 146, y + 72, 100, 44, fonte=_F_FRAUNCES, rot=rot,
                   forma=FormaPreco.CARIMBO, forma_cor=_J_LAR,
                   cor=_J_LARD, tam=21.0, tam_cent=13.2,
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
            # F13-TER/D1: o Nº/ANO é REAL (muda por edição) — papel
            # EDICAO puxa a edição VIVA do projeto; sem dado fica MUDO
            # (rótulo cravado mentia) e o pré-voo avisa
            _legal(870, 56, 160, 24, papel=PapelTexto.EDICAO,
                   fonte=_F_ARCHIVO, nome="Edição", tam=9.0, cor=_J_INK),
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
        # F13-TER/N3: a tarja "FICA A DICA" da capa SAIU da arte — a
        # dica é UM bloco editorial por edição e mora na página 2
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
            # F13-TER/N3: BLOCO EDITORIAL de verdade — a caixa da arte
            # cresceu (650,1188,366×114) e o corpo ganha 3-4 linhas
            # legíveis em coluna de jornal; o título é o chip verde da
            # própria arte (com o lápis)
            _legal(666, 1226, 336, 70, papel=PapelTexto.DICA,
                   fonte=_F_FRA_IT, nome="Fica a Dica",
                   tam=10.0, cor=_J_INK, alin=Alinhamento.ESQUERDA),
        ], origem=(650, 1188)),
    ]
    return slots


def _quintou() -> list[Slot]:
    """O QUINTOU (1080×1300) — geometria MEDIDA por diff Fundo×Real.

    Grade 4×4 (célula 270×258 a partir de y=270; colunas em x=0/270/
    540/810), posição 13 = o "B" do rodapé (estrutura, fora da grade).
    O Fundo limpo NÃO tem divisórias nem logo: a grade inteira é do
    app. Foto GRANDE assentada direto no tijolo; nome branco à
    esquerda; a etiqueta LISTRADA vermelha (a forma do publicado) no
    canto inferior direito; validade "Até dd/mm" a 90° junto ao B."""
    vermelho, branco = "#CE2418", "#FFFFFF"
    slots = []
    for pos in range(1, 17):
        if pos == 13:                      # o B laranja da estrutura
            continue
        lin, col = divmod(pos - 1, 4)
        x, y = col * 270, 270 + lin * 258
        slots.append(_slot(f"pos-{pos:02d}", [
            _img(x + 10, y + 6, 250, 152),
            _nome(x + 8, y + 162, 152, 88, fonte=_F_ARCHIVO,
                  tam=12.0, cor=branco),
            _preco(x + 158, y + 180, 108, 64, fonte=_F_ARCHIVO,
                   forma=FormaPreco.ETIQUETA_LISTRADA,
                   forma_cor=vermelho, cor=branco, tam=24.0,
                   tam_cent=13.5, centavos_na_base=True),
        ], origem=(x, y)))
    slots.append(_slot("selo-validade", [
        _legal(213, 1078, 54, 196, papel=PapelTexto.VALIDADE,
               fonte=_F_ARCHIVO, nome="Validade", rot=90.0,
               tam=15.0, cor="#E01A1A"),
    ], origem=(213, 1078)))
    # o painel do topo-direito é VAZIO no fundo limpo (a logo do
    # publicado é conteúdo) — as DUAS opções do dono nascem aqui:
    # logo (célula FIXA, foto escolhida) + Fica a Dica ao lado; a
    # inspeção também compõe a variante só-dica (decisão é dele)
    slots.append(_slot("painel-logo", [
        _img(604, 30, 200, 200),
    ], origem=(588, 18), fixa=True))
    slots.append(_slot("painel-dica", [
        _legal(816, 40, 236, 30, papel=PapelTexto.LIVRE,
               fonte=_F_ARCHIVO, texto="FICA A DICA", nome="Título",
               tam=12.0, cor="#1B2A4A", alin=Alinhamento.ESQUERDA),
        _legal(816, 74, 236, 152, papel=PapelTexto.DICA,
               fonte=_F_FRA_IT, nome="Fica a Dica",
               tam=10.0, cor="#33384A", alin=Alinhamento.ESQUERDA),
    ], origem=(810, 18)))
    return slots


def _quintou_verso() -> list[Slot]:
    """O VERSO do Quintou — geometria MEDIDA por diff do "Verso fundo"
    × "Verso Real" (mesma grade 4×4 da frente, célula 270×258 a partir
    de y=270), agora com as 16 POSIÇÕES (o verso não tem o "B" nem o
    painel — a marca neon "Quintou do Real" e o "Só Hoje" são ARTE).
    A validade vive no DISCLAIMER do topo direito (bbox do diff:
    y 7–41, x ~640–1076), em branco, sem rotação."""
    vermelho, branco = "#CE2418", "#FFFFFF"
    slots = []
    for pos in range(1, 17):
        lin, col = divmod(pos - 1, 4)
        x, y = col * 270, 270 + lin * 258
        slots.append(_slot(f"vpos-{pos:02d}", [
            _img(x + 10, y + 6, 250, 152),
            _nome(x + 8, y + 162, 152, 88, fonte=_F_ARCHIVO,
                  tam=12.0, cor=branco),
            _preco(x + 158, y + 180, 108, 64, fonte=_F_ARCHIVO,
                   forma=FormaPreco.ETIQUETA_LISTRADA,
                   forma_cor=vermelho, cor=branco, tam=24.0,
                   tam_cent=13.5, centavos_na_base=True),
        ], origem=(x, y)))
    slots.append(_slot("v-validade", [
        _legal(640, 8, 434, 36, papel=PapelTexto.VALIDADE,
               fonte=_F_ARCHIVO, nome="Validade", tam=9.5,
               cor=branco, alin=Alinhamento.ESQUERDA),
    ], origem=(640, 8)))
    return slots


_BUILDERS = {
    "quintou": (_quintou, _quintou_verso),
    "segunda-frios": (_segunda,),
    "terca-do-pao": (_terca,),
    "quarta-das-ofertas": (_quarta,),
    "quinta-do-peixe": (_peixe,),
    "sexta-verde": (_sexta,),
    "sabado-da-carne": (_sabado,),
    "jornal-do-mes": (_jornal_p1, _jornal_p2),
}


def _pasta_do_encarte(raiz: Path, sub: str) -> Path:
    return raiz / sub[2:] if sub.startswith("./") else raiz / "artes" / sub


def chaves_do_pacote(pasta_pacote: str | Path) -> list[str]:
    """As chaves dos encartes cujo BASE.png existe na pasta do pacote."""
    raiz = Path(pasta_pacote)
    achadas = []
    for chave, (sub, bases) in _BASES.items():
        if all((_pasta_do_encarte(raiz, sub) / b).exists() for b in bases):
            achadas.append(chave)
    return achadas


def _jornal_celula_fluxo(n: int, x: float, y: float, w: float,
                         alt: float) -> Slot:
    """F13-TER/N2: a célula do MIOLO em fluxo — a mesma receita da
    ``_jornal_linha`` (foto + nome Fraunces + descritor itálico +
    CARIMBO), parametrizada pela geometria que o fluxo decidiu. A foto
    encolhe com o degrau de altura (o custo declarado do degrau)."""
    foto_h = max(40.0, alt - 108)
    rot = -6.0 if (n % 2 == 0) else 5.0
    return _slot(f"jf-{n:02d}", [
        _img(x + 6, y + 2, w - 16, foto_h),
        _nome(x + 6, y + foto_h + 4, w - 16, 24, fonte=_F_FRAUNCES,
              tam=11.0, cor=_J_INK),
        _sub(x + 6, y + foto_h + 28, w - 16, 16, fonte=_F_FRA_IT,
             tam=8.5, cor=_J_GRAY),
        _preco(x + (w - 96) / 2, y + alt - 50, 96, 42, fonte=_F_FRAUNCES,
               rot=rot, forma=FormaPreco.CARIMBO, forma_cor=_J_LAR,
               cor=_J_LARD, tam=20.0, tam_cent=12.6,
               centavos_na_base=True),
    ], origem=(x, y))


def _jornal_cabecalho_secao(n: int, titulo: str, caixa: tuple) -> Slot:
    """F13-TER/N2: o cabeçalho de seção do jornal — VERSALETE + FILETE
    (nunca retângulo colorido; o estilo é DO encarte)."""
    x, y, w, h = caixa
    return _slot(f"jsec-{n:02d}", [
        _legal(x + 2, y + 4, min(w - 4, 420), 20, papel=PapelTexto.LIVRE,
               fonte=_F_ARCHIVO, texto=titulo.upper(),
               nome=f"Seção: {titulo}", tam=9.5, cor=_J_INK,
               alin=Alinhamento.ESQUERDA),
        Regiao(TipoRegiao.FILETE, _r(x, y + h - 7, w, 1.6),
               nome="Fio da seção", cor=_J_INK),
    ], origem=(x, y))


# as FAIXAS de fluxo do Jornal (px 1×, medidas da arte regenerada:
# réguas de coluna contínuas em x=64+198c−6; p1 y 656–1296, p2 y
# 128–980). Colunas cravadas em 5 PELA ARTE (degrau (a) não existe
# aqui — declarado); degraus de altura tabelados.
_FAIXAS_JORNAL = (
    dict(x=64.0, y=648.0, largura=990.0, altura=648.0),
    dict(x=64.0, y=116.0, largura=990.0, altura=864.0),
)


def layout_de_encarte(chave: str, pasta_pacote: str | Path,
                      secoes: "list[tuple[str, int]] | None" = None,
                      ) -> LayoutDef:
    """Monta o LayoutDef de um encarte do pacote a partir das TABELAS.

    A página nasce do BASE.png real (2160×2880 ⇒ dpi 192 ⇒ 285,75×381
    mm); o Jornal vira UM layout de duas páginas (fundo POR página,
    seções ligadas — N-05: a arte não traz seção; quem desenha é o app).

    F13-TER/N2: com ``secoes`` (só no Jornal), o MIOLO das duas páginas
    troca a grade fixa pelo FLUXO por seções (cabeçalho fio+versalete +
    células ``jf-NN`` na ordem de leitura); capa (hero/chamadas/
    manchete) e rodapés ficam. Os avisos do fluxo (degrau usado,
    transbordo, o que não coube) saem em ``layout.avisos_fluxo``.
    """
    raiz = Path(pasta_pacote)
    sub, bases = _BASES[chave]
    caminhos = [_pasta_do_encarte(raiz, sub) / b for b in bases]
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
    avisos_fluxo: list[str] = []
    if secoes and chave == "jornal-do-mes":
        from app.rendering.fluxo_jornal import FaixaFluxo, montar_fluxo
        faixas = [FaixaFluxo(colunas=(5,), alturas_celula=(202, 178, 156),
                             altura_cabecalho=34, **f)
                  for f in _FAIXAS_JORNAL]
        fluxo = montar_fluxo(secoes, faixas)
        avisos_fluxo = fluxo.avisos
        for pag in paginas:                # a grade fixa do miolo sai
            pag.slots = [s for s in pag.slots
                         if not s.id.split("-")[1].startswith("l")]
        n_cel = n_sec = 0
        for bloco in fluxo.blocos:
            pag = paginas[bloco.faixa]
            n_sec += 1
            pag.slots.append(_jornal_cabecalho_secao(
                n_sec, bloco.secao, bloco.cabecalho))
            for cx, cy, cw, calt in bloco.celulas:
                n_cel += 1
                pag.slots.append(
                    _jornal_celula_fluxo(n_cel, cx, cy, cw, calt))
    # o Quintou veio do Illustrator em 1× (1080×1300, sem BASE ×2) —
    # os demais têm BASE 2160×2880 (×2 exato do viewBox)
    dpi = DPI_VIEWBOX if chave == "quintou" else DPI_BASE
    layout = layout_de_arte(str(caminhos[0]), dpi=dpi, paginas=paginas)
    layout.validar_ids_unicos()
    layout.avisos_fluxo = avisos_fluxo
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

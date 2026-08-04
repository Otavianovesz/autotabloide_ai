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

# QUATER/L9: a CAMADA de preço do dono por página — o asset é a fonte
# da verdade (etiquetas listradas + divisórias vermelhas, RGBA 4500×
# 5418 alinhado 1:1 à página; o número NUNCA esteve na arte)
_CAMADAS: dict[str, tuple[str, ...]] = {
    "quintou": ("Quintou do Real Frente Preço.png",
                "Quintou do Real Verso Preço.png"),
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


def _img(x, y, w, h, rot=0.0, flex=False) -> Regiao:
    from app.rendering.model import Ajuste
    # F13-TER/V1: as fotos dos encartes ASSENTAM — recorte pela bbox do
    # alfa (o quadrado do acervo morre), maior escala que caiba, âncora
    # no rodapé da zona
    # QUARTUSDECIMUS/Q1: ``flex`` marca célula de arte LISA onde a zona
    # pode mudar de forma conforme a foto da semana (foto_fit)
    return Regiao(TipoRegiao.IMAGEM, _r(x, y, w, h), nome="Foto",
                  rotacao_graus=rot, ajuste=Ajuste.ASSENTAR,
                  zona_flex=flex)


def _nome(x, y, w, h, *, fonte, rot=0.0, alin=Alinhamento.CENTRO,
          tam=48.0, tam_min=None, cor="#000000",
          alin_v=AlinhamentoV.BASE) -> Regiao:
    # F13-BIS/T5: nas células estreitas dos encartes, hifenizar é
    # PROIBIDO — o corpo cede ("CERVEJA ITAPA-VA" virou prova).
    # F13-OCTAVUS/C1 + NONUS/N2: o corpo tem PISO com FAIXA — por
    # padrão o corpo cede no máximo UM degrau (tam−3); abaixo disso a
    # precedência do N1 encurta o nome pelo descritor (nunca encolhe a
    # ilegível, nunca elipsa sem avisar). O 6.0 inerte morreu aqui.
    # UNDEVICESIMUS/H1: o BASE dentro de caixa folgada era uma das
    # duas folgas flutuantes do "jogado" — as células de bloco único
    # pedem TOPO explícito.
    return Regiao(TipoRegiao.NOME, _r(x, y, w, h), nome="Nome",
                  fonte=fonte, alinhamento=alin, cor=cor,
                  tamanho_max_pt=tam,
                  tamanho_min_pt=(tam_min if tam_min is not None
                                  else min(tam, max(tam - 3.0, 6.5))),
                  sem_hifen=True,
                  alinhamento_v=alin_v, rotacao_graus=rot)


def _sub(x, y, w, h, *, fonte, rot=0.0, alin=Alinhamento.CENTRO,
         tam=48.0, tam_min=None, cor="#000000",
         alin_v=AlinhamentoV.BASE) -> Regiao:
    # F13-BIS/T2: a linha de DESCRITOR do modelo (região SUBTITULO).
    # F13-NONUS/N2: com piso — o descritor é 1 linha curta; melhor
    # manter o corpo e ceder meio degrau (tam−1,5) do que virar poeira
    return Regiao(TipoRegiao.SUBTITULO, _r(x, y, w, h), nome="Descritor",
                  fonte=fonte, alinhamento=alin, cor=cor,
                  tamanho_max_pt=tam,
                  tamanho_min_pt=(tam_min if tam_min is not None
                                  else min(tam, max(tam - 1.5, 6.5))),
                  sem_hifen=True,
                  alinhamento_v=alin_v, rotacao_graus=rot)


def _preco(x, y, w, h, *, fonte, rot=0.0, forma=None, forma_cor=None,
           borda=None, cor="#000000", tam=48.0, tam_cent=None,
           centavos_na_base=False, alin=Alinhamento.CENTRO,
           separado=None, moeda=True) -> Regiao:
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
                  mostrar_moeda=moeda,
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
_F_FRA_RE = "Fraunces-Regular.ttf"
_F_NUNITO = "Nunito-Black.ttf"
_F_ANTON = "Anton-Regular.ttf"

FONTES_DO_PACOTE = (
    "Anton-Regular.ttf", "Archivo-Bold.ttf", "Archivo-Medium.ttf",
    "Baloo2-Bold.ttf", "Baloo2-ExtraBold.ttf", "Caveat-Bold.ttf",
    "Fraunces-Italic.ttf", "Fraunces-Regular.ttf",
    "Fraunces-SemiBold.ttf", "Nunito-Black.ttf", "Nunito-Bold.ttf",
    "UnifrakturMaguntia.ttf",
    # QUATER/Q2: a fonte REAL do Quintou (estava na raiz do dono e o
    # app usava Archivo — L9). O PIL carrega .otf; não há filtro.
    "Quicksand-Bold.ttf", "Quicksand-Medium.ttf",
    "Quicksand-Regular.otf", "Quicksand-Light.ttf",
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
            # TERTIUSDECIMUS/A1: o remendo cresceu na ARTE (66→96) e o
            # nome ganhou caixa de 2 LINHAS — o texto nunca mais sai
            # do painel sobre a palha da cesta
            _legal(cx - 95, 1006, 190, 12, papel=PapelTexto.LIVRE,
                   fonte=_F_ARCHIVO, nome="Rótulo",
                   texto="· PADARIA BELO BRASIL ·", rot=prot,
                   tam=6.0, cor="#C77E38"),
            _nome(cx - 95, 1020, 190, 44, fonte=_F_FRAUNCES,
                  tam=13.1, cor="#33200F", rot=prot),
            _sub(cx - 95, 1070, 190, 16, fonte=_F_FRA_IT,
                 tam=7.5, cor="#96826A", rot=prot),
        ], origem=(x, 748)))
    # TERTIUSDECIMUS/A2: SÓ A DATA no miolo limpo MEDIDO por pixel no
    # BASE (y 116–142) — o "Ofertas válidas" atravessava a curva gravada
    selo_t = _legal(896, 114, 100, 30, papel=PapelTexto.VALIDADE,
                    fonte=_F_FRAUNCES, nome="Validade (data)", rot=8.0,
                    tam=16.5, cor="#33200F")
    selo_t.so_data = True
    slots.append(_slot("selo-validade", [selo_t], origem=(876, 106)))
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
            # SEPTIMUS/O2: a zona era um banner LARGO e BAIXO (312×90)
            # — o saco kraft ALTO saía um selo minúsculo (o ASSENTAR
            # limita pela altura). A zona virou alta: o Kit respira.
            _img(444, 336, 192, 112),
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
        # OCTAVUS/C1: as BANDAS da arte cresceram 60→88 (regeneradas)
        # — o tipo sobe ao PISO DO CELULAR (linha ≥30px em 1080; corpo
        # 20pt com piso 18) e cabe em 2 linhas + descritor
        (2, (64, 288), -0.6, (78, 302, 182, 188), (68, 494, 202, 88),
         (76, 302), (236, 328, 32), 169, 548),
        (3, (806, 294), 0.5, (820, 308, 182, 188), (810, 500, 202, 88),
         (818, 308), (978, 334, 32), 911, 554),
    )
    for i, origem, rot, foto, banda, (chx, chy), (sx, sy, sr), tcx, _ty \
            in flancos:
        by = banda[1]
        slots.append(_slot(f"celula-{i}", [
            _img(*foto, rot=rot),
            Regiao(TipoRegiao.ADORNO, _r(*banda), nome="Banda"),
            _chip_num(chx, chy, f"Nº {i:02d}", rot),
            _preco(sx - sr, sy - sr, sr * 2, sr * 2, fonte=_F_FRAUNCES,
                   rot=rot, forma=FormaPreco.MEDALHAO_ESTRELA,
                   forma_cor="#E9B23A", borda="#C08F1F", cor="#17293B",
                   tam=18.0, tam_cent=11.4, centavos_na_base=True),
            # (2 linhas a 19pt = 2×~30px×1,12 ≈ 64px — a caixa de 60
            # truncava "Creme de…" em vez de quebrar; pego no OLHAR)
            _nome(tcx - 93, by + 4, 186, 64, fonte=_F_FRAUNCES,
                  tam=19.0, tam_min=17.0, cor="#FFFFFF", rot=rot),
            _sub(tcx - 93, by + 68, 186, 18, fonte=_F_FRA_IT,
                 tam=11.0, cor="#BCD2E4", rot=rot),
        ], origem=origem))
    # (id, origem, rot, foto ESTENDIDA, adornos [(x,y,w,h)...], chip,
    #  selo(cx,cy,R), tcx, y_nome, tam_nome, tam_sub, tam_preco)
    # SEPTIMUS/O1: fotos das etiquetas 245→186 e 209→160 (o orçamento
    # 55–68% da altura útil) e o TIPO sobe 1 degrau — nem raquítica,
    # nem gulosa; o texto nunca cede
    # OCTAVUS/C1: as BANDAS das etiquetas cresceram (arte regenerada:
    # 56→84 e 53,5→80) — o tipo no piso do celular (20pt/18 e 19pt/17),
    # até 2 linhas + descritor DENTRO da banda
    etiquetas = (
        (4, (64, 652), -0.5, (76, 662, 280, 186),
         ((66, 654, 26, 26), (340, 654, 26, 26), (65, 851, 302, 92)),
         (76, 664), (328, 886, 38), 180, 851, 20.0, 11.0, 21.4),
        (5, (388, 644), 0.4, (400, 654, 280, 186),
         ((390, 646, 26, 26), (664, 646, 26, 26), (389, 843, 302, 92)),
         (398, 656), (428, 878, 38), 568, 843, 20.0, 11.0, 21.4),
        (6, (712, 654), -0.5, (724, 664, 280, 186),
         ((714, 656, 26, 26), (988, 656, 26, 26), (713, 853, 302, 92)),
         (722, 666), (976, 888, 38), 828, 853, 20.0, 11.0, 21.4),
        (7, (240, 955), -0.45, (252, 964, 272, 152),
         ((240, 1119, 296, 88),),
         (250, 965), (496, 1152, 35), 352, 1119, 20.0, 10.5, 19.8),
        (8, (552, 948), 0.4, (564, 957, 272, 152),
         ((552, 1112, 296, 88),),
         (562, 958), (592, 1145, 35), 728, 1112, 20.0, 10.5, 19.8),
    )
    for i, origem, rot, foto, adornos, (chx, chy), (sx, sy, sr), tcx, \
            by, tn, ts, tp in etiquetas:
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
            _nome(tcx - 100, by + 6, 200, 64, fonte=_F_FRAUNCES,
                  tam=tn - 1.0, tam_min=tn - 3.0, cor="#FFFFFF",
                  rot=rot),
            _sub(tcx - 100, by + 70, 200, 18, fonte=_F_FRA_IT,
                 tam=ts, cor="#BCD2E4", rot=rot),
        ]
        slots.append(_slot(f"celula-{i}", regs, origem=origem))
    # OCTAVUS/C3: o selo tem "TODA SEGUNDA"/"LEITERIA" GRAVADOS em
    # curva — o app escreve SÓ A DATA no miolo limpo, MEDIDO por pixel
    # no BASE (a faixa sem tinta: y 82–106, x 890–970)
    selo_data = _legal(884, 78, 92, 30, papel=PapelTexto.VALIDADE,
                       fonte=_F_FRAUNCES, nome="Validade (data)",
                       rot=10.0, tam=16.0, cor="#1F4E79")
    selo_data.so_data = True
    slots.append(_slot("selo-validade", [selo_data], origem=(865, 74)))
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
            # ADENDO do dono (28/07, QUARTUSDECIMUS): "a imagem na
            # parte superior no meio, usando o resto do espaço; a
            # descrição no canto inferior esquerdo; o preço ou
            # desconto no canto inferior direito". Zona LARGA no topo
            # (as fotos do dono são largas — casam), flex por cima
            # (a foto da semana ainda manda na forma, Q1)
            _img(82, my + 8, 274, 132, flex=True),
            # nome em LARGURA TOTAL (o OLHAR provou: 164px perdiam
            # "Mini Salgadinhos"/"Lanche na Chapa" por um fio, e 2
            # linhas de 16,8pt não cabem sob o piso O1 da foto —
            # full-width resolve pela raiz; o passo 3 segue colado)
            _nome(82, my + 144, 274, 36, fonte=_F_NUNITO,
                  alin=Alinhamento.ESQUERDA, tam=17.5, cor=escuro),
            # a linha do peso do modelo ("BBX 100g" — canto inf. esq.)
            _sub(82, my + 184, 164, 20, fonte="Nunito-Bold.ttf",
                 alin=Alinhamento.ESQUERDA, tam=12.0, cor=escuro),
        ]
        if i < 2:
            # pricepod VERDE no canto inferior DIREITO, sobrescrito
            regs.append(_preco(250, my + 178, 106, 52, fonte=_F_ANTON,
                               forma=FormaPreco.TAG_ARREDONDADA,
                               forma_cor=verde, borda=escuro,
                               cor="#FFFFFF", tam=24.5, tam_cent=13.8,
                               rot=-1.5))
        else:
            # pctpod VERDE (QUARTUSDECIMUS/Q3): a cor segue a COLUNA —
            # a identidade da célula fixa — não o tipo do valor; o
            # formato "20% OFF" foi DECIDIDO pelo dono (28/07)
            d = _legal(250, my + 178, 106, 52, papel=PapelTexto.DESCONTO,
                       fonte=_F_ANTON, nome="Desconto", rot=-1.5,
                       tam=23.0, cor="#FFFFFF")
            d.forma_preco = FormaPreco.TAG_ARREDONDADA
            d.forma_cor = verde
            d.forma_cor_borda = escuro
            regs.append(d)
        slots.append(_slot(f"celula-fixa-{i + 1}", regs,
                           origem=(74, my), fixa=True))
    for i, (cx, cy) in enumerate(((410, 44), (729, 44),
                                  (410, 456), (729, 456)), start=1):
        slots.append(_slot(f"celula-var-{i}", [
            # ADENDO do dono (28/07): as livres também são flex — "os
            # outros 5 sejam respeitados caso mudem gramatura e outras
            # questões"; hoje inócuo (a régua mediu todas aprovadas),
            # rede para a foto futura
            _img(cx + 8, cy + 8, 281, 236, flex=True),
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
        _img(420, 878, 320, 406, flex=True),
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
    # A2: só a data no miolo medido; ADENDO do dono (28/07): a data
    # MAIOR — o miolo limpo re-medido por pixel dá y 354–398 (1×),
    # a caixa cresce 28→44 e o corpo 28,5→40
    selo_q = _legal(84, 354, 168, 44, papel=PapelTexto.VALIDADE,
                    fonte=_F_ANTON, nome="Validade (data)", rot=-2.0,
                    tam=40.0, cor="#F7C868")
    selo_q.so_data = True
    slots.append(_slot("selo-validade", [selo_q], origem=(80, 348)))
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
    # A2: só a data no miolo medido (y 144–170 do BASE)
    selo_p = _legal(892, 142, 120, 30, papel=PapelTexto.VALIDADE,
                    fonte=_F_FRAUNCES, nome="Validade (data)", rot=-7.0,
                    tam=23.25, cor=navy)
    selo_p.so_data = True
    slots.append(_slot("selo-validade", [selo_p], origem=(877, 124)))
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
    # A2: só a data no miolo medido (y 154–180 do BASE)
    selo_s = _legal(852, 152, 120, 30, papel=PapelTexto.VALIDADE,
                    fonte=_F_FRAUNCES, nome="Validade (data)", rot=-6.0,
                    tam=28.5, cor="#FDF6E9")
    selo_s.so_data = True
    slots.append(_slot("selo-validade", [selo_s], origem=(852, 116)))
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
    # A2: só a data no miolo medido (y 154–180 do BASE)
    selo_c = _legal(876, 152, 120, 30, papel=PapelTexto.VALIDADE,
                    fonte=_F_FRAUNCES, nome="Validade (data)", rot=9.0,
                    tam=25.5, cor=red)
    selo_c.so_data = True
    slots.append(_slot("selo-validade", [selo_c], origem=(856, 146)))
    return slots


# ORDEM do arquiteto (03/08): o preço era o elemento MAIS importante
# com o PIOR contraste da página — #C9641A dava 3,4:1 sobre o papel
# (mínimo 4,5). O laranja-queimado escureceu para #A85212 (4,6:1);
# o vivo #F58634 segue só em FORMA/borda (nunca texto pequeno).
# ERRATA §13.3 da SEPTIMUSDECIMUS: o cinza #6E675C (5,0:1) some na
# IMPRESSÃO — a régua do encarte é o papel, não a tela. #4A443B dá
# 8,6:1; vale para o Jornal INTEIRO (o guardião de tinta afirma
# cor velha == 0 na página composta — ornamento escurecer não perde).
_J_INK, _J_GRAY, _J_LAR, _J_LARD = ("#201B12", "#4A443B",
                                    "#F58634", "#A85212")


def _jornal_linha(pref: str, slots: list, y: float, n: int,
                  inicio: int) -> None:
    """O ``linha(y, ids)`` do gerador: até 5 colunas, x = 64 + c*198.

    O preço é o CARIMBO perfurado (borda tracejada laranja, texto
    LARD), s=0.78, rot −6/+5 alternando por coluna."""
    for c in range(n):
        x = 64 + c * 198
        rot = -6.0 if (c % 2 == 0) else 5.0
        slots.append(_slot(f"{pref}-l{inicio + c}", [
            # v2 (fotos "cortadas" da 2ª prova): o FIO desenha ANTES da
            # foto — vinha depois na lista e riscava o topo do produto
            # quando a foto enchia a altura (o filete é separador de
            # fundo, nunca risco por cima)
            Regiao(TipoRegiao.ADORNO, _r(x, y - 20, 186, 6),
                   nome="Fio"),
            # F13-TER: a foto sobe até o fio da linha (recolado).
            # J25: zona_flex — o FIO é filete separador, não "veste" a
            # célula (a guarda do foto_fit aprendeu a diferença).
            # DUODEVICESIMUS §1 (a LEI DA PROXIMIDADE): a foto CRESCE
            # (100→116 px) e o carimbo de preço SOBREPÕE o canto
            # inferior direito dela — o clássico dos encartes: o preço
            # "gruda" no produto. Antes: 17,7 mm até o próprio produto
            # e −1,8 mm até o seguinte (o olho agrupava ERRADO).
            _img(x + 4, y - 20, 178, 116, flex=True),
            # o carimbo DEPOIS da foto na lista (L-C: preço é a última
            # camada) — cavalga a borda direita, sobrepondo ~36 px
            _preco(x + 90, y + 60, 96, 42, fonte=_F_ARCHIVO, rot=rot,
                   forma=FormaPreco.CARIMBO, forma_cor=_J_LAR,
                   cor=_J_LARD, tam=23.0, tam_cent=14.5,
                   centavos_na_base=True),
            # UNDEVICESIMUS §2 — O BLOCO É UM SÓ (o "jogado" medido:
            # nome BASE em caixa de 7,4mm + descritor BASE em caixa de
            # 9mm = DUAS folgas flutuantes; célula de 1 linha abria
            # 3,9mm de buraco, a de 2 linhas zero). H1: âncora ÚNICA
            # no TOPO — a sobra cai EMBAIXO do bloco, igual em todas.
            # H2: a entrelinha nome→descritor é POSIÇÃO fixa (22px =
            # 5,8mm ≈ 1,15× o corpo do nome), nunca a altura da caixa.
            # v4 (a LEI do dono) segue: nada é comido — o descritor
            # ainda pode 2 linhas quando o extenso exigir (o conflito
            # H3-contagem × lei-v4 está DECLARADO para o dono).
            _nome(x + 8, y + 108, 170, 24, fonte=_F_FRAUNCES,
                  tam=14.0, cor=_J_INK, alin_v=AlinhamentoV.TOPO),
            # ERRATA §13.3: sem itálico, 11,5/10,5 (o piso DURO do
            # compositor segue como exceção anti-tesoura, K3)
            _sub(x + 8, y + 130, 170, 34, fonte=_F_FRA_RE,
                 tam=11.5, tam_min=10.5, cor=_J_GRAY,
                 alin_v=AlinhamentoV.TOPO),
        ], origem=(x + 4, y)))


def _jornal_p1() -> list[Slot]:
    """gen_jornal_final::capa() — hero + 4 chamadas + 3 linhas de 5.

    N-04: o BASE zera o ``conteudo-exemplo`` INTEIRO — validade, nº da
    edição, manchete e o período editável (F8) são desenhados pelo app."""
    slots = [
        _slot("jp1-hero", [
            # QUATER/J6: a foto do hero ENCOLHEU (384→330) e o splash
            # foi para a direita dela — cavalga a borda, nunca corta o
            # produto (o "SUPER OFERTA" cortava o pacote de arroz)
            _img(74, 308, 330, 266),
            Regiao(TipoRegiao.ADORNO, _r(236, 308, 226, 3),
                   nome="Fio"),
            # a estrela SUPER OFERTA (24 pontas no modelo) sai como
            # medalhão de pétalas VERDE — a aproximação declarada.
            # Rodada JM (B2B): papel OFERTA — o preço-texto do item do
            # herói ("SUPER OFERTA") enche a estrela SOZINHO; o D2
            # continua: sem dado e sem rótulo do dono, a forma nem
            # desenha (texto_fixo nasce vazio e segue editável)
            _legal(384, 296, 106, 106, papel=PapelTexto.OFERTA,
                   fonte=_F_ARCHIVO, texto="",
                   nome="Splash", rot=-8.0, tam=11.5, cor="#F7F3E9"),
            # QUINTUSDECIMUS/J19: a célula-herói DESENHA PREÇO — o
            # carimbo das chamadas, um degrau maior (a hierarquia do
            # herói), no vão entre o Splash e a legenda
            _preco(384, 466, 106, 48, fonte=_F_FRAUNCES, rot=-6.0,
                   forma=FormaPreco.CARIMBO, forma_cor=_J_LAR,
                   cor=_J_LARD, tam=24.0, tam_cent=14.5,
                   centavos_na_base=True),
            # J26: a legenda do herói era o MENOR texto da página
            # inteira — sobe para o corpo das chamadas (o maior produto
            # nunca tem o menor nome)
            _nome(78, 570, 376, 30, fonte=_F_FRAUNCES,
                  tam=15.0, cor=_J_INK),
            # ERRATA §13.3: o descritor de venda sem itálico e maior
            _sub(78, 602, 376, 20, fonte=_F_FRA_RE,
                 tam=11.5, tam_min=10.5, cor=_J_GRAY),
        ], origem=(74, 328)),
    ]
    splash = next(r for r in slots[0].regioes if r.nome == "Splash")
    splash.forma_preco = FormaPreco.MEDALHAO_ESTRELA
    splash.forma_cor = "#0F783F"
    splash.forma_cor_borda = "#F7F3E9"
    for i, (x, y) in enumerate(((488, 328), (762, 328),
                                (488, 466), (762, 466)), start=1):
        # DUODEVICESIMUS item 50: DOIS ângulos fixos no jornal inteiro
        # (−6/+5, os mesmos das linhas) — 4 ângulos diferentes liam
        # como ruído a 42 repetições
        rot = -6.0 if i % 2 else 5.0
        dy = 20 if i <= 2 else 18
        slots.append(_slot(f"jp1-ch{i}", [
            # J25: a foto da chamada enche a zona (zona_flex — a régua
            # da QUARTUSDECIMUS chega ao Jornal)
            _img(x, y - dy, 112, 112 + dy, flex=True),
            # J26: corpos acima do rascunho de jornal — legíveis no
            # celular (nome 13→14,5; descritor 9,4→10,5)
            # v2: largura 168→162 — em x+112, 168 terminava em x+280 e
            # o passo entre chamadas é 274: o fim do texto entrava 6 px
            # na zona de foto da vizinha (que desenha DEPOIS e cobria)
            # v4: o descritor da chamada ganha a 2ª linha (19→26 px,
            # até o topo do carimbo) — a lei do dono vale na capa
            # UNDEVICESIMUS/H1+H2: o bloco único também nas chamadas
            # (âncora no TOPO, gap de posição 23px ≈ 1,15× o corpo)
            _nome(x + 112, y + 14, 162, 24, fonte=_F_FRAUNCES,
                  tam=14.5, cor=_J_INK, alin_v=AlinhamentoV.TOPO),
            # ERRATA §13.3: idem — Regular, 11,5/10,5
            _sub(x + 112, y + 38, 162, 26, fonte=_F_FRA_RE,
                 tam=11.5, tam_min=10.5, cor=_J_GRAY,
                 alin_v=AlinhamentoV.TOPO),
            _preco(x + 146, y + 72, 100, 44, fonte=_F_ARCHIVO, rot=rot,
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
            # QUATER/J7: a linha-fina NÃO repete o período da manchete
            # ("do dia 1º ao 27" duas vezes em duas linhas era eco)
            _legal(190, 270, 700, 26, papel=PapelTexto.LIVRE,
                   fonte=_F_FRA_IT, nome="Linha-fina",
                   texto="a redação conferiu preço por preço: do "
                         "pacotão de arroz ao café passado",
                   tam=10.9, cor=_J_GRAY),
        ], origem=(188, 218)),
        # F13-TER/N3: a tarja "FICA A DICA" da capa SAIU da arte — a
        # dica é UM bloco editorial por edição e mora na página 2
    ]
    return slots


def _jornal_p2() -> list[Slot]:
    """gen_jornal_final::pagina2() — 4 linhas de 5 + linha final de 2.

    ORDEM do arquiteto (03/08, medido em mm): a grade antiga se
    sobrepunha POR CONSTRUÇÃO — célula de 55,3 mm em passos de
    53,5/61,4/53,4/61,4 mm: em 2 das 4 emendas a foto de baixo
    NASCIA dentro do preço de cima (−1,8/−1,9 mm) e era pintada por
    cima (o Suco de Uva sobre o preço da Rosquinha). O passo agora é
    UNIFORME e o MESMO da p1 (222 px = 58,8 mm → folga +3,4 mm):
    o ritmo que o olho procura. As âncoras da ARTE medidas: o bloco
    de pagamento começa em y=1000 (a 4ª linha termina em 987) e o
    expediente em y=1214 (a linha final, à esquerda, termina em 1209)."""
    slots: list[Slot] = []
    for i, y in enumerate((132, 354, 576, 798)):
        _jornal_linha("jp2", slots, y, 5, 1 + i * 5)
    _jornal_linha("jp2", slots, 1020, 2, 21)   # a linha final: só 2
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
            # v2 (a 2ª prova): o EXPEDIENTE — jornal profissional repete
            # nº/edição em TODA página; o dado já viaja pela montagem
            # oficial (condicional: sem edição fica mudo)
            _legal(640, 94, 320, 18, papel=PapelTexto.EDICAO,
                   fonte=_F_ARCHIVO, nome="Edição (expediente)",
                   tam=7.5, cor=_J_GRAY),
        ], origem=(640, 48)),
        _slot("jp2-dica", [
            # F13-TER/N3: BLOCO EDITORIAL de verdade — a caixa da arte
            # cresceu (650,1188,366×114) e o corpo ganha 3-4 linhas
            # legíveis em coluna de jornal; o título é o chip verde da
            # própria arte (com o lápis)
            # ERRATA §13.5: a frase cravada SAIU DO CÓDIGO — dica é
            # conteúdo editorial sobre OS ITENS DA PÁGINA (a definição
            # do dono: "dica dos itens que tem ali pra você fazer um
            # preparo, alguma história"), nunca chamada de compra
            # genérica. O papel nasce MUDO (como o EDICAO): a IA gera
            # citando 2-3 produtos com preço, ou o dono escreve pela
            # porta da Mesa. Sem IA, fica vazio — melhor mudo que
            # genérico (a caixa vazia não desenha, ramo DICA do
            # compositor).
            _legal(666, 1226, 336, 70, papel=PapelTexto.DICA,
                   fonte=_F_FRA_IT, nome="Fica a Dica",
                   texto="",
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
    slots = []
    for pos in range(1, 17):
        if pos == 13:                      # o B laranja da estrutura
            continue
        lin, col = divmod(pos - 1, 4)
        x, y = col * 270, 270 + lin * 258
        slots.append(_slot(f"pos-{pos:02d}", _celula_quintou(x, y),
                           origem=(x, y)))
    # QUATER/Q6 (medido no Real): alvo VISUAL (221,1080,36,192),
    # cap ~34px, #E04444 — sobre o TIJOLO, nunca o logo. O RG-12
    # gira o conteúdo em torno do CENTRO do rect, então o rect é o
    # RETO pré-rotação (196×40 centrado em 238,1176) — a caixa
    # pós-rotação esmagava o texto (o bug das 3 rodadas).
    # TERTIUSDECIMUS/A2: só a data no tijolo (a frase inteira girada
    # não é o publicado — que escrevia "Até 16/07", curto)
    selo_qt = _legal(138, 1146, 200, 60, papel=PapelTexto.VALIDADE,
                     fonte=_F_QUICK, nome="Validade (data)", rot=90.0,
                     tam=34.0, cor="#E04444")
    selo_qt.so_data = True
    slots.append(_slot("selo-validade", [selo_qt], origem=(138, 1146)))
    # o painel do topo-direito: ADENDO do dono (30/07, ao ver a página
    # dele) — "não tem o fica a dica preenchendo o espaço": a decisão
    # A/B do QUATER/Q5 caiu para a DICA (variante A). O título é
    # texto_fixo; o corpo é papel DICA (a IA/editorial sobrescreve; o
    # default é no tom do PRÓPRIO publicado do dono — L9)
    slots.append(_slot("painel-dica", [
        _legal(600, 26, 444, 34, papel=PapelTexto.LIVRE,
               fonte=_F_QUICK, nome="Fica a Dica (título)",
               texto="Fica a Dica", tam=22.0, cor="#241D2E"),
        _legal(600, 62, 444, 172, papel=PapelTexto.DICA,
               fonte=_F_QUICK, nome="Fica a Dica",
               texto=("Que tal usar os produtos do Quintou para fazer "
                      "aquela janta para agradar a família heinn?! "
                      "Aproveite as ofertas de hoje — é só no Quintou "
                      "do Real, e só até durar o estoque!"),
               tam=13.5, cor="#241D2E"),
    ], origem=(588, 18), fixa=True))
    return slots


_F_QUICK = "Quicksand-Bold.ttf"            # QUATER/Q2: a fonte REAL


def _celula_quintou(x: float, y: float) -> list:
    """A célula do Quintou MEDIDA no publicado (QUATER §2): foto usa a
    zona inteira acima do rodapé (y rel 2–195, 92–97% da altura); nome
    em até 3 linhas Quicksand branco CENTRADO na metade esquerda (cap
    ~14px, linhas y rel 198/222/246); etiqueta = a CAMADA do dono em
    (rel 153,189,112,64) — a região só posiciona o NÚMERO (cap ~34px,
    sem "R$" do app: o R$ é gravado na arte)."""
    branco = "#FFFFFF"
    return [
        _img(x + 8, y + 2, 254, 190),
        # ADENDO do dono (30/07): o publicado reduz o corpo dos nomes
        # longos até bem pequeno (nunca corta) — range real 14,5→9,5;
        # o piso do celular cede antes da tesoura (motor)
        _nome(x + 10, y + 192, 134, 62, fonte=_F_QUICK,
              tam=14.5, tam_min=9.5, cor=branco),
        _preco(x + 153, y + 189, 112, 64, fonte=_F_QUICK,
               forma=FormaPreco.ETIQUETA_LISTRADA, forma_cor="#FF0000",
               cor=branco, tam=40.0, tam_cent=40.0,
               centavos_na_base=True, moeda=False),
    ]


def _quintou_verso() -> list[Slot]:
    """O VERSO do Quintou — geometria MEDIDA por diff do "Verso fundo"
    × "Verso Real" (mesma grade 4×4 da frente, célula 270×258 a partir
    de y=270), agora com as 16 POSIÇÕES (o verso não tem o "B" nem o
    painel — a marca neon "Quintou do Real" e o "Só Hoje" são ARTE).
    A validade vive no DISCLAIMER do topo direito (bbox do diff:
    y 7–41, x ~640–1076), em branco, sem rotação."""
    slots = []
    for pos in range(1, 17):
        lin, col = divmod(pos - 1, 4)
        x, y = col * 270, 270 + lin * 258
        slots.append(_slot(f"vpos-{pos:02d}", _celula_quintou(x, y),
                           origem=(x, y)))
    # ADENDO do dono (30/07): o disclaimer do publicado é a FRASE
    # COMPLETA com o aviso das imagens, alinhada à DIREITA — e a DATA
    # em neon VERTICAL no vão entre o "ATÉ" e o "Só Hoje" da arte
    # (o publicado escreve "26#05" ali; o app escreve a data viva)
    slots.append(_slot("v-validade", [
        _legal(640, 6, 434, 18, papel=PapelTexto.LEGAL,
               fonte=_F_QUICK, nome="Aviso legal",
               texto="*Imagens meramente ilustrativas — ofertas "
                     "enquanto durarem os nossos estoques",
               tam=9.5, cor="#FFFFFF", alin=Alinhamento.DIREITA),
        _legal(640, 26, 434, 18, papel=PapelTexto.VALIDADE,
               fonte=_F_QUICK, nome="Validade", tam=9.5,
               cor="#FFFFFF", alin=Alinhamento.DIREITA),
    ], origem=(640, 8)))
    neon = _legal(560, 105, 200, 70, papel=PapelTexto.VALIDADE,
                  fonte=_F_QUICK, nome="Validade (data neon)",
                  rot=90.0, tam=40.0, cor="#E14546")
    neon.so_data = True
    slots.append(_slot("v-data-neon", [neon], origem=(560, 105)))
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
    """A célula DENSA do fluxo (QUINQUE §5, régua ≥55% de foto POR
    NÚMERO): padding zero (J10 — a foto encosta na goteira), nome em
    ATÉ 2 LINHAS com o peso na mesma linha (J11 — sem região de
    descritor; o canal da unidade anexa), carimbo COMPACTO ancorado no
    canto inferior-direito (J14). Foto = (w−6)×(alt−86): a 4 colunas
    (w≈247) e degrau 216, são 58% da célula."""
    # QUATER/J8: giro ±3 — os preços da mesma linha alinham
    rot = -3.0 if (n % 2 == 0) else 3.0
    foto_h = max(40.0, alt - 80)
    return _slot(f"jf-{n:02d}", [
        _img(x + 3, y + 1, w - 6, foto_h),
        _nome(x + 4, y + foto_h + 2, w - 8, 34, fonte=_F_FRAUNCES,
              tam=10.0, cor=_J_INK),
        _preco(x + w - 100, y + alt - 42, 96, 38, fonte=_F_FRAUNCES,
               rot=rot, forma=FormaPreco.CARIMBO, forma_cor=_J_LAR,
               cor=_J_LARD, tam=18.0, tam_cent=11.5,
               centavos_na_base=True),
    ], origem=(x, y))


# QUATER/A4: o cabeçalho de seção do Jornal saiu daqui — quem o desenha
# é o MOTOR ÚNICO (secoes.py, estilo "JORNAL", ligado por página). O
# TipoRegiao.FILETE não é mais GERADO por nenhum layout (legado
# tolerado no compositor por desserialização — LEDGER_I2).


# as FAIXAS de fluxo do Jornal (px 1×). QUATER/J3: as réguas contínuas
# SAÍRAM da arte — a coluna é implícita (goteira branca). QUATER/J5: a
# 3ª faixa é o rodapé À ESQUERDA do bloco de pagamentos (2 colunas) —
# a página enche até o fim, como o estático fazia. O par é
# (índice_da_página, geometria); colunas tabeladas por faixa.
# QUINQUE/§5: 4 COLUNAS (célula 25% mais larga — produto de mercado é
# mais largo que alto), cabeçalho ≤28px (J12), degraus de altura
# maiores (J13: usar a altura toda).
_FAIXAS_JORNAL = (
    (0, dict(x=64.0, y=648.0, largura=990.0, altura=648.0,
             colunas=(4,), alturas_celula=(216, 196, 178),
             altura_cabecalho=28)),
    (1, dict(x=64.0, y=116.0, largura=990.0, altura=864.0,
             colunas=(4,), alturas_celula=(216, 196, 178),
             altura_cabecalho=28)),
    (1, dict(x=64.0, y=1000.0, largura=396.0, altura=196.0,
             colunas=(2,), alturas_celula=(164, 156),
             altura_cabecalho=28)),
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
    # QUATER/L9: as CAMADAS do dono por página (a arte das etiquetas de
    # preço do Quintou — consumida, nunca imitada); ausente = sem camada
    camadas = [_pasta_do_encarte(raiz, sub) / n
               for n in _CAMADAS.get(chave, ())]
    paginas = []
    for i, (caminho, builder) in enumerate(zip(caminhos, _BUILDERS[chave])):
        camada = (str(camadas[i]) if i < len(camadas)
                  and camadas[i].exists() else None)
        paginas.append(Pagina(
            slots=builder(),
            arquivo_camada=camada,
            arquivo_fundo=str(caminho),
            # F13-BIS §3.7.2: as seções nascem DESLIGADAS — o contorno
            # genérico é alienígena sobre o papel creme/laranja.
            # RODADA-125 Onda 2 (decisão do dono, 03/08): o JORNAL tem
            # o SEU estilo de seção ("um jeito próprio, bonitinho") —
            # o cabeçalho tipográfico do broadsheet, MEDIDO na folga
            # real entre fileiras (sem folga, não desenha). O dono liga
            # com o "Agrupar por categoria" (a régua nova só liga onde
            # há estilo próprio) ou no toggle da página.
            secoes_ligadas=False,
            estilo_secoes=("JORNAL" if chave == "jornal-do-mes"
                           else None),
        ))
    avisos_fluxo: list[str] = []
    if secoes and chave == "jornal-do-mes":
        from app.rendering.fluxo_jornal import FaixaFluxo, montar_fluxo
        faixas = [FaixaFluxo(**f) for _pg, f in _FAIXAS_JORNAL]
        paginas_das_faixas = [pg for pg, _f in _FAIXAS_JORNAL]
        fluxo = montar_fluxo(secoes, faixas)
        avisos_fluxo = fluxo.avisos
        for pag in paginas:                # a grade fixa do miolo sai
            pag.slots = [s for s in pag.slots
                         if not s.id.split("-")[1].startswith("l")]
            # QUATER/A4: quem desenha o cabeçalho de seção é o MOTOR
            # ÚNICO (desenhar_secoes, estilo JORNAL, por página) — o
            # fluxo só gera células; nenhum slot jsec/FILETE nasce
            pag.secoes_ligadas = True
            pag.estilo_secoes = "JORNAL"
        n_cel = 0
        for bloco in fluxo.blocos:
            pag = paginas[paginas_das_faixas[bloco.faixa]]
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
        lay = layout_de_encarte(chave, pasta)
        # SEPTIMUS: o upsert NÃO apaga a configuração do dono — o
        # conteudo_fixo (N1: o Kit com a foto escolhida) do layout já
        # existente é PRESERVADO por slot.id na atualização do encarte
        from app.rendering.persistencia import (
            carregar_layout as _carregar,
            listar_layouts as _listar,
        )
        antigo = next((r for r in _listar(session)
                       if r.nome == NOMES_EXIBICAO[chave]), None)
        if antigo is not None:
            velho = _carregar(session, antigo.id, raiz=raiz)
            fixos = {s.id: s.conteudo_fixo
                     for p in (velho.paginas if velho else [])
                     for s in p.slots if s.conteudo_fixo}
            for p in lay.paginas:
                for s in p.slots:
                    if s.id in fixos:
                        s.conteudo_fixo = fixos[s.id]
        salvar_layout(session, NOMES_EXIBICAO[chave], lay,
                      tipo_midia="TABLOIDE", raiz=raiz)
    if chaves:
        raiz.fontes.mkdir(parents=True, exist_ok=True)
        for nome in FONTES_DO_PACOTE:
            origem = pasta / "fontes" / nome
            destino = raiz.fontes / nome
            if origem.exists() and not destino.exists():
                shutil.copy(origem, destino)
        # F13-UNDECIMUS/U2: o CARIMBO do pacote — quando as artes ou os
        # geradores mudarem, o Ateliê avisa que há atualização (o dado
        # importado fica velho e ninguém sabia)
        try:
            from app.core.repositories import ConfigRepositorio
            repo = ConfigRepositorio(session)
            repo.set("encartes.pasta_pacote", str(pasta.resolve()))
            repo.set("encartes.versao_pacote", versao_do_pacote(pasta))
        except Exception:
            pass          # o carimbo é conveniência; o import já valeu
    return chaves


def versao_do_pacote(pasta_pacote: str | Path) -> str:
    """F13-UNDECIMUS/U2: o carimbo de versão do pacote — hash curto de
    (caminho, tamanho, mtime) das artes e dos geradores. Qualquer BASE
    regenerado ou gerador editado muda o carimbo."""
    import hashlib

    raiz = Path(pasta_pacote)
    partes: list[str] = []
    for p in sorted(raiz.rglob("*")):
        if p.is_file() and p.suffix.lower() in (".png", ".py", ".svg"):
            st = p.stat()
            partes.append(f"{p.relative_to(raiz).as_posix()}"
                          f"|{st.st_size}|{st.st_mtime_ns}")
    return hashlib.sha1("\n".join(partes).encode("utf-8")).hexdigest()[:12]


def pacote_desatualizado() -> str | None:
    """F13-UNDECIMUS/U2: a pasta do último pacote importado, SE ela
    estiver mais nova que o carimbo gravado — senão None. Pasta sumida
    ou nunca importado degrada para None em silêncio (é só um aviso;
    noutra máquina o caminho local simplesmente não existe)."""
    try:
        from app.core.database import Database
        from app.core.repositories import ConfigRepositorio
        db = Database().init()
        try:
            with db.Session() as s:
                repo = ConfigRepositorio(s)
                pasta = repo.get("encartes.pasta_pacote")
                versao = repo.get("encartes.versao_pacote")
        finally:
            db.engine.dispose()
        if not pasta or not versao:
            return None
        p = Path(pasta)
        if not p.exists():
            return None
        return str(p) if versao_do_pacote(p) != versao else None
    except Exception:
        return None

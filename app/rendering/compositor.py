"""
Compositor — desenha os elementos dinâmicos sobre a arte de fundo
=================================================================
A arte de fundo (imagem do Illustrator) fica intocada, na camada de baixo.
Por cima, o app desenha imagem do produto, nome e preço (de/por), com Pillow,
no tamanho físico exato definido pelo LayoutDef.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from app.core.paths import SystemRoot
from app.rendering.arranjo import ModoArranjo, compor_imagens
from app.rendering.selos import Canto, Selo, desenhar_selos
from app.rendering.model import (
    Ajuste,
    Alinhamento,
    AlinhamentoV,
    FormaPreco,
    LayoutDef,
    Mascara,
    Pagina,
    PapelPreco,
    PapelTexto,
    Regiao,
    SubtipoPreco,
    TipoRegiao,
)
from app.rendering.text_fit import ajustar_texto, piso_do_celular
from app.rendering.units import mm_para_px, pt_para_px


@dataclass
class ImagemSlot:
    """Uma imagem do slot, com transform opcional (padrão: como veio no recorte).

    R-037 (enquadrar): ``zoom`` (≥1 aproxima) e ``foco_x``/``foco_y`` (ponto
    focal RELATIVO 0..1, I3 portável) reenquadram a foto DENTRO do slot sem
    deformar (a proporção é mantida; o excedente é cortado). Padrão = foto
    inteira, centralizada (comportamento de sempre)."""

    caminho: str
    rotacao: float = 0.0
    flip_h: bool = False
    zoom: float = 1.0
    foco_x: float = 0.5
    foco_y: float = 0.5


@dataclass
class DadosProduto:
    """O conteúdo que preenche as regiões de um slot."""

    nome: str
    preco_por: Decimal | None = None
    preco_de: Decimal | None = None
    imagem_path: str | None = None                 # atalho para 1 imagem
    imagens: list[ImagemSlot] = field(default_factory=list)  # 1..N imagens
    modo_arranjo: ModoArranjo = ModoArranjo.LEQUE
    unidade: str | None = None
    # F13-BIS/T2: o DESCRITOR do item ("senepol · m. própria · 100 g") —
    # a 2ª linha que todo encarte do pacote tem; regiões SUBTITULO o
    # desenham (sem ele, caem na unidade).
    descritor: str | None = None
    # selos
    mais18: bool = False               # +18 automático (bebida alcoólica)
    marca_propria: bool = False        # selo "Qualidade Belo Brasil"
    selos_extra: list[Selo] = field(default_factory=list)  # manuais
    # texto legal/validade da oferta (desenhado nas regiões TEXTO_LEGAL)
    texto_legal: str | None = None
    # R-070 (Fase 7): multi-preço "3 por R$10" — TEXTO que a região de preço
    # desenha no lugar do Decimal (é um FORMATO de promoção por quantidade)
    multi_preco: str | None = None
    # R-071 (Fase 7): observação do item ("limite 2 por cliente") — desenhada
    # nas regiões de papel OBSERVACAO; condicional (vazia = a região não pinta).
    observacao: str | None = None
    # F8.2: categoria do item — as SEÇÕES visuais (contorno+título) derivam
    # dela; sem categoria o item agrupa em "Outros"
    categoria: str | None = None
    # F13-TER/D1: a EDIÇÃO do Jornal ("Nº 178 · ANO 42") — campo do
    # PROJETO que chega aqui pela montagem oficial (como a validade);
    # desenhado nas regiões de papel EDICAO, condicional
    edicao: str | None = None
    # F13-TERTIUSDECIMUS/Q2: o desconto DECLARADO na tabela ("COM 20%
    # DE DESCONTO", item sem preço) — o papel DESCONTO o desenha quando
    # não há de/por para calcular; a arte foi desenhada para isso
    desconto_pct: int | None = None
    # RODADA-125 v2 — a REGRA CANÔNICA da célula: as marcas CONHECIDAS
    # presentes no nome (extraídas na montagem oficial, 1× por lote);
    # a cadeia do nome_fit as desce ao descritor SEMPRE que a célula
    # tem SUBTITULO ("Leite Integral" grande + "Parmalat · 1L"). Vazio
    # = comportamento de sempre (testes/latitude antigos intactos).
    marcas_nome: tuple[str, ...] = ()
    # VICESIMUS-SEPTIMUS §2: o nome pelo GLOSSÁRIO do dono — degrau 2
    # da escada (só entra quando o completo NÃO cabe; a lei v4 manda
    # informação completa sempre que couber)
    nome_abreviado: str | None = None
    # v3: os SABORES declarados viajam também COMO LISTA (não só
    # dissolvidos na prosa do descritor) — o pré-voo compara com as
    # fotos e acusa "anuncia 3 sabores, só 1 tem foto" (a Sardinha)
    sabores: tuple[str, ...] = ()
    # VICESIMUS-TERTIUS/L20: item COMPOSTO (produtos DIFERENTES — o
    # 'Somar e Tio Bonini') — o arranjo NUNCA sobrepõe uma marca à
    # outra (cópia pode sumir atrás; original não)
    composto: bool = False


def percentual_desconto(preco_de: "Decimal | None",
                        preco_por: "Decimal | None") -> int | None:
    """R-109 (Fase 11): o % de desconto CALCULADO de (de−por)/de, arredondado.

    NUNCA digitado — deriva sempre dos dois preços. Devolve None (a região não
    desenha nada) quando não há "de", quando o "de" é ≤ 0, ou quando "de" ≤
    "por" (não há desconto real — casa com a guarda PROCON do pré-voo). Um
    desconto que arredonda para 0% também some (não polui o cartaz)."""
    if preco_de is None or preco_por is None:
        return None
    try:
        de, por = Decimal(preco_de), Decimal(preco_por)
    except (InvalidOperation, TypeError, ValueError):
        return None
    if de <= 0 or por >= de:
        return None
    pct = (de - por) / de * 100
    return int(pct.to_integral_value(rounding=ROUND_HALF_UP))


# QUARTUSDECIMUS/Q4: o formato do papel DESCONTO — DECIDIDO PELO DONO
# (28/07, ao ver as duas opções renderizadas): "deixa 20% off mesmo".
# Vale em toda porta (encarte, cartaz, etiqueta); "menos" fica como a
# alternativa que ele viu e rejeitou.
FORMATO_DESCONTO_PADRAO = "off"


def formato_do_desconto(pct, estilo: str | None = None) -> str:
    """O texto que o papel DESCONTO escreve para um percentual ``pct``."""
    estilo = estilo or FORMATO_DESCONTO_PADRAO
    if estilo == "menos":
        return f"-{pct}% no preço"
    return f"{pct}% OFF"


def texto_composto_legal(reg: "Regiao", dados: "DadosProduto | None" = None,
                         *, em_celula: bool = False) -> str:
    """RG-57: o texto que uma região TEXTO_LEGAL desenha, decidido pelo PAPEL.

    Fonte ÚNICA para o compositor e para a prévia do editor (canvas), para a
    lógica não viver duplicada em três lugares.

    - **VALIDADE**: puxa a validade "de/até" que o evento já formatou
      (``dados.texto_legal``, montado por ``montar_validade_oferta``); só cai
      no ``texto_fixo`` se não houver validade — a região reflete a oferta viva.
    - **DICA / LEGAL / LIVRE**: o texto mora na própria região (``texto_fixo``):
      a IA escreveu a dica, o preset gravou o aviso, o dono digitou o livre.
      A validade legada é o ÚLTIMO recurso (não perder conteúdo antigo, I2).

    O ramo não-VALIDADE (``texto_fixo or validade``) é byte-idêntico à
    heurística legada ``reg.texto_fixo or dados.texto_legal or ""`` — layouts
    antigos (todos ``LIVRE`` por padrão) compõem exatamente igual.
    """
    papel = getattr(reg, "papel_texto", None) or PapelTexto.LIVRE
    validade = ((dados.texto_legal if dados is not None else None) or "")
    fixo = (reg.texto_fixo or "")
    if papel == PapelTexto.VALIDADE:
        texto = validade or fixo
        # F13-OCTAVUS/C3: a região SÓ-DATA escreve "27/07" — o selo
        # tem o resto GRAVADO na arte ("Ofertas válidas" era
        # redundante três vezes e cobria o texto curvo do selo). Sem
        # data no texto, cai no completo (guarda: nunca em silêncio).
        # Rodada JM (B2A): a data é a ÚLTIMA (o FIM da oferta) — num
        # período "DE 03/08 ATÉ 27/08" o selo diz até quando vale
        # (27/08), não o dia em que começou.
        if getattr(reg, "so_data", False) and texto:
            import re as _re
            datas = _re.findall(r"\d{1,2}/\d{1,2}", texto)
            if datas:
                # VICESIMUS-QUINTUS/L23: o texto_fixo vira PREFIXO da
                # data ("Até " + "26/05" — o publicado do Quintou);
                # sem prefixo, só a data, como sempre.
                # UNDETRICESIMUS (achado na PRÓPRIA prova do Peixe): o
                # prefixo só vale se NÃO for uma data — quando o dono
                # (ou um projeto antigo) digitou "30/07" no texto fixo,
                # a concatenação imprimia "30/0730/07" dentro do selo.
                # Prefixo é palavra ("Até "), nunca a data de novo.
                prefixo = "" if _re.search(r"\d{1,2}/\d{1,2}", fixo) else fixo
                return (prefixo + datas[-1]) if prefixo else datas[-1]
        return texto
    if papel == PapelTexto.OBSERVACAO:
        # R-071: a observação do item; condicional — vazia devolve "" (a região
        # não desenha nada). Cai no texto_fixo só se o item não tiver observação
        # (permite uma observação "de layout" fixa sem depender do item).
        obs = (dados.observacao if dados is not None else None) or ""
        return obs or fixo
    if papel == PapelTexto.DESCONTO:
        # R-109: o % CALCULADO de (de−por)/de — condicional (sem "de" ou
        # sem desconto real, a região não pinta). Nunca digitado…
        # TERTIUSDECIMUS/Q2: …exceto quando o desconto É a oferta ("LANCHE
        # NA CHAPA COM 20% DE DESCONTO" — item SEM preço, com percentual
        # DECLARADO na tabela do dono); aí o dado vale
        pct = percentual_desconto(
            dados.preco_de if dados is not None else None,
            dados.preco_por if dados is not None else None)
        if not pct and dados is not None:
            pct = getattr(dados, "desconto_pct", None)
        return formato_do_desconto(pct) if pct else ""
    if papel == PapelTexto.EDICAO:
        # F13-TER/D1: a edição VIVA do projeto ("Nº 178 · ANO 42");
        # condicional — sem dado a região fica MUDA (nunca um número
        # de edição mentindo; o pré-voo avisa que falta)
        return (getattr(dados, "edicao", None) or "") if dados else ""
    if papel == PapelTexto.OFERTA:
        # Rodada JM (B2B): o preço-texto do ITEM enche a estrela
        # ("SUPER OFERTA"); sem dado vale o rótulo fixo do dono;
        # vazio = a forma nem desenha (o D2 do Splash preservado)
        mp = (getattr(dados, "multi_preco", None) or "") if dados else ""
        return mp or fixo
    if papel == PapelTexto.DICA:
        # RODADA-125 v2 (K8 confirmado pela frota): a DICA é EDITORIAL —
        # vazia NÃO desenha nada (condicional como OBSERVACAO); cair no
        # rabo genérico imprimia a VALIDADE pela 2ª vez na caixa "Fica
        # a Dica" da página do dono. A validade-legada como último
        # recurso vale para LIVRE/LEGAL, nunca para a dica.
        return fixo
    # Rodada JM (B2A, decisão do dono 03/08): o texto fixo com período
    # gravado ("do dia 1º ao 27" nas manchetes do Jornal) escreve o
    # período REAL da validade; sem o padrão ou sem par de datas, o
    # fixo volta intacto — layouts antigos compõem byte-idêntico.
    if fixo:
        from app.core.validade import texto_com_periodo_vivo
        return texto_com_periodo_vivo(fixo, validade)
    # UNDETRICESIMUS §3: A VALIDADE É DA PÁGINA — nunca se repete dentro
    # de célula de produto. O rabo legado (LIVRE vazio herda a validade)
    # é o que punha a data nas duas células grandes da Quinta do Peixe:
    # a "Etiqueta" opcional nasce VAZIA de propósito (D2) e vinha
    # imprimindo a data por herança. Fora de célula (o rodapé típico do
    # tabloide, os layouts antigos) o recurso segue valendo — I2.
    return "" if em_celula else validade


# ==============================================================================
# Helpers
# ==============================================================================


def _rect_px(rect, dpi: int) -> tuple[int, int, int, int]:
    return (
        round(mm_para_px(rect.x_mm, dpi)),
        round(mm_para_px(rect.y_mm, dpi)),
        round(mm_para_px(rect.larg_mm, dpi)),
        round(mm_para_px(rect.alt_mm, dpi)),
    )


def _reais_centavos(valor: Decimal) -> tuple[str, str]:
    q = valor.quantize(Decimal("0.01"))
    reais = int(q)
    centavos = int((q - reais) * 100)
    return str(reais), f"{centavos:02d}"


def _y_alinhado(y: int, alt: int, alt_conteudo: float, reg: "Regiao") -> int:
    """F13/C4 (R-01): o Y do bloco de texto pelo alinhamento VERTICAL da
    região. CENTRO é byte-idêntico ao comportamento de sempre; layout
    antigo (sem o campo) cai em CENTRO pela serialização."""
    from app.rendering.model import AlinhamentoV
    av = getattr(reg, "alinhamento_v", AlinhamentoV.CENTRO)
    if av == AlinhamentoV.TOPO:
        return y
    if av == AlinhamentoV.BASE:
        return y + max(0, int(alt - alt_conteudo))
    return y + max(0, int(alt - alt_conteudo) // 2)


def _x_alinhado(x: int, larg: int, larg_conteudo: float, alinhamento: Alinhamento) -> float:
    if alinhamento == Alinhamento.CENTRO:
        return x + (larg - larg_conteudo) / 2
    if alinhamento == Alinhamento.DIREITA:
        return x + (larg - larg_conteudo)
    return x


# ==============================================================================
# Desenho por tipo de região
# ==============================================================================


def _carregar_imagens(dados: DadosProduto) -> list[tuple[ImagemSlot, Image.Image]]:
    """Carrega as imagens do slot aplicando a transform de cada uma.

    Devolve pares (spec, imagem) — a spec carrega o enquadramento (zoom/foco)
    que o desenho aplica DENTRO do slot (R-037)."""
    especs = dados.imagens or (
        [ImagemSlot(dados.imagem_path)] if dados.imagem_path else []
    )
    pares: list[tuple[ImagemSlot, Image.Image]] = []
    for e in especs:
        if not e.caminho or not Path(e.caminho).exists():
            continue
        im = Image.open(e.caminho).convert("RGBA")
        if e.flip_h:
            im = im.transpose(Image.FLIP_LEFT_RIGHT)
        if e.rotacao:
            im = im.rotate(e.rotacao, expand=True, resample=Image.BICUBIC)
        pares.append((e, im))
    return pares


def _forma_mascara(reg: Regiao, rw: int, rh: int, dpi: int) -> Image.Image | None:
    """R-036: a forma de recorte como um alpha L (0..255). None p/ RETANGULO
    (sem recorte — o caminho de sempre segue byte-idêntico)."""
    if reg.mascara == Mascara.RETANGULO:
        return None
    m = Image.new("L", (rw, rh), 0)
    d = ImageDraw.Draw(m)
    if reg.mascara == Mascara.CIRCULO:
        d.ellipse([0, 0, rw - 1, rh - 1], fill=255)
    else:  # ARREDONDADO
        raio = max(0, min(round(mm_para_px(reg.mascara_raio_mm, dpi)),
                          min(rw, rh) // 2))
        d.rounded_rectangle([0, 0, rw - 1, rh - 1], radius=raio, fill=255)
    return m


def _imagem_enquadrada(img: Image.Image, rw: int, rh: int,
                       esp: ImagemSlot, ajuste: Ajuste) -> Image.Image:
    """R-037: reenquadra a foto numa camada (rw×rh) SEM deformar — escala pela
    proporção (fit/cover conforme o ajuste) × zoom, e posiciona pelo ponto
    focal. Foco 0.5/0.5 e zoom 1.0 = centralizado (o de sempre)."""
    if ajuste == Ajuste.PREENCHER:
        base_esc = max(rw / img.width, rh / img.height)
    else:
        base_esc = min(rw / img.width, rh / img.height)
    esc = base_esc * max(esp.zoom, 0.01)
    nw, nh = max(1, round(img.width * esc)), max(1, round(img.height * esc))
    escalada = img.resize((nw, nh))
    camada = Image.new("RGBA", (rw, rh), (0, 0, 0, 0))
    px = round((rw - nw) * esp.foco_x)
    py = round((rh - nh) * esp.foco_y)
    camada.paste(escalada, (px, py), escalada)
    return camada


def _aplicar_mascara(camada: Image.Image, forma: Image.Image | None) -> Image.Image:
    """Multiplica o alpha da camada pela forma (recorte por pixel). Sem forma,
    devolve a própria camada."""
    if forma is None:
        return camada
    from PIL import ImageChops
    camada = camada.copy()
    camada.putalpha(ImageChops.multiply(camada.getchannel("A"), forma))
    return camada


def _um_corpo_so(img: Image.Image) -> bool:
    """§3 da VICESIMUS-SECUNDUS (guarda dura): a foto que JÁ É um
    conjunto (o Detergente com 4 frascos, a Urca com 3) NUNCA se
    repete — leque de leque. Detecção: a projeção horizontal do alfa
    tem mais de um corpo separado por um vale vazio."""
    if img.mode != "RGBA":
        return True
    a = img.getchannel("A").resize((60, 20))
    px = list(a.getdata())
    colunas = [any(px[l * 60 + c] > 32 for l in range(20))
               for c in range(60)]
    corpos = 0
    dentro = False
    for cheio in colunas:
        if cheio and not dentro:
            corpos += 1
            dentro = True
        elif not cheio:
            dentro = False
    return corpos <= 1


def _leque_solo(img: Image.Image, nw: int, nh: int, rw: int,
                rh: int) -> Image.Image | None:
    """L19 (a ideia do DONO) na composição da VICESIMUS-TERTIUS §1-2:

    - alto e fino → HERÓI E FLANCOS: centro 100% a 0°, flancos a 88%
      com −3°/+3°, entrando ~22% ATRÁS do centro e com a base ~4%
      mais alta (é assim que se lê "mais atrás", não "menor");
      SIMÉTRICO — a massa óptica cai no centro (P1). Produto MUITO
      fino: os flancos entram só 10% (o grupo alarga, §4.3).
    - baixo e largo → EMPILHAMENTO: a de trás a 90% deslocada ~18%
      para cima e ~8% para o lado, a do meio a 95%, a da FRENTE a
      100% na base — preenche a zona em pé e leva a etiqueta.

    A cópia da FRENTE/central pinta por último. Devolve a camada RGBA
    (o par de flancos vira 1 quando o trio não cabe), ou None."""
    un = img.resize((max(1, nw), max(1, nh)))
    prop = nw / max(1, nh)
    if prop < 1.0:                       # HERÓI E FLANCOS
        fl = un.resize((max(1, round(nw * 0.88)),
                        max(1, round(nh * 0.88))))
        muito_fino = (nw * 3) < rw * 0.45
        entra = 0.10 if muito_fino else 0.22
        avanco = round(fl.width * (1 - entra))
        sobe = round(nh * 0.04)
        fl_e = fl.rotate(-3, expand=True, resample=2)
        fl_d = fl.rotate(3, expand=True, resample=2)
        larg_total = avanco * 2 + nw
        if larg_total > rw:              # só um flanco (à direita)
            larg_total = avanco + nw
            if larg_total > rw:
                return None
            camada = Image.new("RGBA", (larg_total, nh + sobe + 6),
                               (0, 0, 0, 0))
            camada.alpha_composite(
                fl_d, (avanco + nw - fl_d.width,
                       camada.height - fl_d.height - sobe))
            camada.alpha_composite(un, (0, camada.height - nh))
            return camada
        camada = Image.new("RGBA", (larg_total, nh + sobe + 6),
                           (0, 0, 0, 0))
        camada.alpha_composite(fl_e,
                               (0, camada.height - fl_e.height - sobe))
        camada.alpha_composite(
            fl_d, (larg_total - fl_d.width,
                   camada.height - fl_d.height - sobe))
        camada.alpha_composite(un, (avanco, camada.height - nh))
        return camada
    # BAIXO E LARGO: o EMPILHAMENTO (§2 — a metade que faltava). O
    # achatado costuma ENCHER a largura da zona — deslocar para o
    # lado estouraria sempre; o CONJUNTO escala para caber (3 cópias
    # a ~86% ainda têm ~2,2× a tinta da unidade).
    dx = round(nw * 0.08)
    dy = round(nh * 0.18)
    larg_total = nw + dx * 2
    alt_total = nh + dy * 2
    fit = min(rw / max(1, larg_total), rh / max(1, alt_total), 1.0)
    if fit < 0.60:
        return None                      # nem escalando compensa
    if fit < 1.0:
        nw = max(1, round(nw * fit))
        nh = max(1, round(nh * fit))
        un = img.resize((nw, nh))
        dx = round(nw * 0.08)
        dy = round(nh * 0.18)
        larg_total = nw + dx * 2
        alt_total = nh + dy * 2
    m95 = un.resize((max(1, round(nw * 0.95)),
                     max(1, round(nh * 0.95))))
    t90 = un.resize((max(1, round(nw * 0.90)),
                     max(1, round(nh * 0.90))))
    camada = Image.new("RGBA", (larg_total, alt_total), (0, 0, 0, 0))
    camada.alpha_composite(t90.rotate(2, expand=True, resample=2),
                           (dx * 2, 0))
    camada.alpha_composite(m95.rotate(-2, expand=True, resample=2),
                           (dx, dy))
    camada.alpha_composite(un, (0, alt_total - nh))
    return camada


def _fracao_de_tinta(img: Image.Image) -> float:
    """Fração da caixa da imagem coberta por TINTA (alfa > 32) — a
    régua do P4 (amostra 40×40, barata)."""
    if img.mode != "RGBA":
        return 1.0
    a = img.getchannel("A").resize((40, 40))
    return sum(1 for p in a.getdata() if p > 32) / 1600.0


def _centroide_x(img: Image.Image) -> float:
    """O centro ÓPTICO horizontal (centroide do alfa, px da imagem) —
    P1: garrafa de base larga centra pelo volume aparente."""
    if img.mode != "RGBA":
        return img.width / 2
    a = img.getchannel("A").resize((40, 40))
    px = list(a.getdata())
    soma = peso = 0.0
    for i, p in enumerate(px):
        if p > 32:
            soma += (i % 40) + 0.5
            peso += 1
    if peso == 0:
        return img.width / 2
    return (soma / peso) / 40.0 * img.width


def _desenhar_imagem(base: Image.Image, reg: Regiao, dados: DadosProduto, dpi: int) -> None:
    pares = _carregar_imagens(dados)
    if not pares:
        return
    x, y, rw, rh = _rect_px(reg.rect, dpi)
    forma = _forma_mascara(reg, rw, rh, dpi)

    if len(pares) == 1:
        esp, img = pares[0]
        enquadrada = (esp.zoom != 1.0 or esp.foco_x != 0.5 or esp.foco_y != 0.5)
        if forma is None and not enquadrada:
            # 1 imagem, sem forma nem enquadramento: caminho da F2 —
            # byte-idêntico no CONTER (min nunca estoura a caixa)
            if reg.ajuste == Ajuste.ASSENTAR:
                # F13-TER/V1: mata o QUADRADO do acervo na composição
                # (recorte pela bbox do alfa) e ASSENTA no rodapé
                bbox = (img.getchannel("A").getbbox()
                        if img.mode == "RGBA" else None)
                if bbox:
                    img = img.crop(bbox)
                escala = min(rw / img.width, rh / img.height)
                # VICESIMUS-PRIMUS/P4: NORMALIZAR POR ÁREA DE TINTA —
                # a foto muito CHEIA (saco que enche a caixa) comprime
                # em direção à mediana da página (teto: tinta ≤ 62% da
                # zona); o piso é a escala máxima SEM CORTE (a garrafa
                # fina para no teto físico da altura — nunca se corta
                # foto por uniformidade; o limite é declarado).
                # (o teto vale SÓ para a célula de coluna com mordida
                # — o Jornal; o banner replanejável da Quarta mantém o
                # ganho do Q1: o contrato "a foto sobe do chão" é do
                # dono e uma foto opaca chapada tem tinta 100%)
                if reg.uid in getattr(base, "_p4_uids", ()):
                    frac_alfa = _fracao_de_tinta(img)
                    if frac_alfa > 0:
                        tinta = (frac_alfa * (img.width * escala)
                                 * (img.height * escala)) \
                            / max(rw * rh, 1)
                        if tinta > 0.62:
                            escala *= (0.62 / tinta) ** 0.5
                nw = max(1, round(img.width * escala))
                nh = max(1, round(img.height * escala))
                # VICESIMUS-SECUNDUS/L19 (a ideia do DONO): quando a
                # UNIDADE não preenche (tinta < 38% da zona ≈ 70% da
                # mediana medida) e a foto é UM corpo só, o produto se
                # REPETE — 3 cópias com profundidade e rotação. A
                # ordem do §4: o leque muda a tinta ANTES da etiqueta.
                # VICESIMUS-QUARTUS §1.3 (L22): o leque é CAPACIDADE DO
                # MOTOR, não do layout — o gate de identidade "coluna
                # com mordida" prendia a L19 ao Jornal; qualquer zona
                # ASSENTAR de foto recortada dispara pela régua da
                # tinta. §4.4 da TERTIUS segue: o HERÓI nunca
                # multiplica — agora medido POR PÁGINA (pré-passe: bem
                # maior que a mediana, ou página editorial <3 zonas)
                eh_heroi = reg.uid in getattr(base, "_heroi_uids", ())
                if (img.mode == "RGBA" and not eh_heroi
                        and not getattr(reg, "sem_leque", False)
                        and reg.uid not in getattr(base, "_q1_uids", ())):
                    frac = _fracao_de_tinta(img)
                    tinta_un = frac * nw * nh / max(rw * rh, 1)
                    prop_un = nw / max(1, nh)
                    # §2: o ACHATADO dispara abaixo da mediana (50%) —
                    # a metade da L19 que tinha ficado só escrita
                    limiar = 0.50 if prop_un >= 1.3 else 0.38
                    if tinta_un < limiar and _um_corpo_so(img):
                        conj = _leque_solo(img, nw, nh, rw, rh)
                        if conj is not None:
                            img = conj
                            nw, nh = img.width, img.height
                if img.size != (nw, nh):
                    img = img.resize((nw, nh))
                # VICESIMUS-PRIMUS/P1: a FOTO É ÓPTICA — centra pela
                # MASSA aparente (o centroide horizontal do alfa),
                # nunca pela caixa nem pela margem do texto (L18: cada
                # natureza tem seu eixo; o "esquerda" da §7.2 morreu)
                cx_opt = _centroide_x(img)
                ox = round(x + rw / 2 - cx_opt)
                ox = max(x, min(ox, x + rw - nw))
                oy = y + rh - nh              # P5: a LINHA DE CHÃO
                base.paste(img, (ox, oy), img)
                # §7.3: a SILHUETA pintada (px) — a régua do pouso da
                # etiqueta é a TINTA do produto, nunca a caixa
                if not hasattr(base, "_silhuetas"):
                    base._silhuetas = {}
                base._silhuetas[reg.uid] = (ox, oy, nw, nh)
                return
            if reg.ajuste == Ajuste.PREENCHER:
                escala = max(rw / img.width, rh / img.height)
            else:
                escala = min(rw / img.width, rh / img.height)
            nw, nh = max(1, round(img.width * escala)), max(1, round(img.height * escala))
            img = img.resize((nw, nh))
            ox, oy = x + (rw - nw) // 2, y + (rh - nh) // 2
            if nw > rw or nh > rh:
                # F13/C10 (R-03): PREENCHER estoura por definição (max) —
                # o excedente é RECORTADO para a região; a foto NUNCA
                # invade a célula vizinha (o caminho com máscara já
                # recortava; o rápido, que é o padrão, vazava)
                cx, cy = max(0, x - ox), max(0, y - oy)
                img = img.crop((cx, cy,
                                cx + min(rw, nw), cy + min(rh, nh)))
                ox, oy = max(ox, x), max(oy, y)
            base.paste(img, (ox, oy), img)
            return
        camada = _imagem_enquadrada(img, rw, rh, esp, reg.ajuste)
    else:
        # N imagens: arranjo (leque / lado a lado / grade), camada que não vaza.
        camada = compor_imagens([im for _, im in pares], rw, rh,
                                dados.modo_arranjo,
                                sem_sobrepor=dados.composto)

    camada = _aplicar_mascara(camada, forma)
    base.paste(camada, (x, y), camada)


def _desenhar_pill(base: Image.Image, x: int, y: int, w: int, h: int,
                   cor_hex: str, alpha: int) -> None:
    """R-035: faixa/pílula semitransparente (blend por alpha sobre a base RGB)."""
    if w <= 0 or h <= 0:
        return
    from PIL import ImageColor
    r, g, b = ImageColor.getrgb(cor_hex)
    tile = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(tile)
    d.rounded_rectangle([0, 0, w - 1, h - 1], radius=min(w, h) // 2,
                        fill=(r, g, b, max(0, min(alpha, 255))))
    base.paste(tile, (x, y), tile)


def _texto_com_efeito(draw: ImageDraw.ImageDraw, pos, texto: str, fonte,
                      reg: Regiao) -> None:
    """R-034: desenha o texto com sombra e/ou contorno (por instância). Sem
    efeito, é byte-idêntico ao `draw.text` de sempre (stroke_width=0)."""
    x, y = pos
    stroke = max(1, round(fonte.size * 0.06)) if reg.contorno else 0
    if reg.sombra:
        d = max(1, round(fonte.size * 0.06))
        draw.text((x + d, y + d), texto, font=fonte, fill=reg.cor_efeito,
                  anchor="la", stroke_width=stroke, stroke_fill=reg.cor_efeito)
    draw.text((x, y), texto, font=fonte, fill=reg.cor, anchor="la",
              stroke_width=stroke, stroke_fill=reg.cor_efeito)


_TIPOS_DE_TEXTO = (TipoRegiao.NOME, TipoRegiao.SUBTITULO,
                   TipoRegiao.UNIDADE, TipoRegiao.TEXTO_LEGAL)


class GradeApertada(Exception):
    """UNDETRICESIMUS §2 (degrau 3): a região não comporta UMA linha no
    piso legível E não pode crescer sem invadir a vizinha. A página NÃO
    compõe — a grade é que precisa de mais altura ali. Erro duro, com o
    layout e a região nomeados (nunca um texto vazado em silêncio)."""


def _uma_linha_no_piso_px(reg: Regiao, dpi: int, fontes_dir: Path,
                          entrelinha: float = 1.12) -> int:
    """Altura, em px, de UMA linha no piso declarado da região."""
    from PIL import ImageFont
    px = max(1, round(pt_para_px(reg.tamanho_min_pt, dpi)))
    try:
        fonte = ImageFont.truetype(str(fontes_dir / reg.fonte), px)
    except OSError:
        try:
            fonte = ImageFont.truetype(
                str(fontes_dir / "Roboto-Regular.ttf"), px)
        except OSError:
            return 0                      # sem fonte medível: não cresce
    asc, desc = fonte.getmetrics()
    return round((asc + desc) * entrelinha)


def _piso_e_regra(reg: Regiao, pag) -> bool:
    """O piso desta região é REGRA (a legibilidade no celular) ou é
    DADO (o 6 pt histórico do modelo)?

    Só a primeira manda na caixa. Numa etiqueta de 40 mm o piso do
    celular não se aplica (o próprio ``piso_do_celular`` para no 6.0
    histórico: "peça pequena não é peça de celular") — ali o layout
    declara os dois lados, não há regra a defender, e quem cede é o
    texto pela tesoura de sempre."""
    if reg.tipo != TipoRegiao.NOME or not pag:
        return False
    piso = piso_do_celular(pag[0])
    return piso > 6.0 and reg.tamanho_min_pt >= piso - 0.01


def plano_de_crescimento(reg: Regiao, dpi: int, fontes_dir: Path,
                         caixas: dict, pag) -> tuple[object, str]:
    """A CONTA do §2, sem efeito nenhum: devolve ``(rect_novo, erro)``.

    ``rect_novo`` é None quando a caixa já comporta o piso; ``erro`` é
    a frase nomeada quando não comporta E não pode crescer. É a mesma
    conta que o desenho usa e que o pré-voo pergunta — uma só, para o
    aviso nunca divergir do que a composição vai fazer.
    """
    alt_linha = _uma_linha_no_piso_px(reg, dpi, fontes_dir)
    if alt_linha <= 0:
        return None, ""
    _x, _y, _rw, rh = _rect_px(reg.rect, dpi)
    if alt_linha <= rh:
        return None, ""                   # a caixa comporta o piso
    falta_mm = (alt_linha - rh) / dpi * 25.4
    r = reg.rect
    # ENCOSTAR NÃO É INVADIR: duas caixas coladas (o nome e o descritor
    # do Jornal partilham a borda) davam "colisão" por um fio de ponto
    # flutuante — 0,05 mm é menos de meio pixel a 192 dpi.
    EPS = 0.05

    folga_acima = r.y_mm if pag else 1e9
    folga_abaixo = (pag[1] - (r.y_mm + r.alt_mm)) if pag else 1e9
    vizinho_acima = vizinho_abaixo = "a borda do papel"
    for uid, (x0, y0, x1, y1, rotulo) in caixas.items():
        if uid == reg.uid:
            continue
        if x1 <= r.x_mm + EPS or x0 >= r.x_mm + r.larg_mm - EPS:
            continue                      # não divide faixa vertical
        if y1 <= r.y_mm + EPS and r.y_mm - y1 < folga_acima:
            folga_acima, vizinho_acima = r.y_mm - y1, rotulo
        elif y0 >= r.y_mm + r.alt_mm - EPS \
                and y0 - (r.y_mm + r.alt_mm) < folga_abaixo:
            folga_abaixo, vizinho_abaixo = y0 - (r.y_mm + r.alt_mm), rotulo

    # A caixa cresce para BAIXO (o sentido da leitura); se não houver
    # folga lá, para CIMA; e se nenhum lado sozinho bastar, DIVIDE o
    # que falta entre os dois — é o que um diagramador faria com a
    # sobra da fileira antes de declarar a grade apertada.
    if folga_abaixo >= falta_mm - EPS:
        return replace(r, alt_mm=r.alt_mm + falta_mm), ""
    if folga_acima >= falta_mm - EPS:
        return replace(r, y_mm=r.y_mm - falta_mm,
                       alt_mm=r.alt_mm + falta_mm), ""
    if folga_acima + folga_abaixo >= falta_mm - EPS:
        sobe = max(0.0, falta_mm - max(0.0, folga_abaixo))
        return replace(r, y_mm=r.y_mm - sobe, alt_mm=r.alt_mm + falta_mm), ""
    if not _piso_e_regra(reg, pag):
        return None, ""                   # sem regra em jogo: a tesoura
    return None, (
        f"a região '{reg.nome or reg.tipo.value}' não comporta uma "
        f"linha legível ({reg.tamanho_min_pt:.1f} pt precisa de "
        f"{alt_linha / dpi * 25.4:.2f} mm, a caixa tem "
        f"{r.alt_mm:.2f} mm) e só há {folga_acima:.2f} mm livres "
        f"acima (até {vizinho_acima}) e {folga_abaixo:.2f} mm abaixo "
        f"(até {vizinho_abaixo}) — a grade precisa de mais altura aqui")


def crescer_do_piso(base: Image.Image, reg: Regiao, dpi: int,
                    fontes_dir: Path) -> Regiao:
    """UNDETRICESIMUS §2 — O PISO NÃO CEDE; A CAIXA CEDE (L26).

    O piso do tipo é REGRA (nasce da distância de leitura no celular,
    U1/C1); a altura da região é DADO (um número na tabela de
    geometria). Regra vence dado — o projeto já decidiu isso duas
    vezes. Então, quando nem UMA linha no piso cabe na caixa, a caixa
    cresce (e o crescimento é DECLARADO — I2, nunca calado).

    Três degraus: (1) cresce e registra; (2) se crescer colidir com a
    fileira vizinha, é ``GradeApertada`` — erro duro (o pré-voo pergunta
    ANTES, para o dono ver a frase e não um travamento); (3) em nenhuma
    hipótese o texto vaza.

    A vizinhança chega pela base — as caixas VISÍVEIS da página em mm,
    já com as SUBSTITUIÇÕES do slot (a coluna elástica, o plano Q1, o
    pouso do carimbo). Medir contra o rect do layout acusaria colisão
    onde o desenho tem folga: foi o que a 1ª medição do Jornal mostrou
    (o instrumento errado de novo, conferido antes de acusar).
    """
    caixas = getattr(base, "_caixas_pagina", {})
    novo, erro = plano_de_crescimento(
        reg, dpi, fontes_dir, caixas, getattr(base, "_pagina_mm", None))
    if erro:
        raise GradeApertada(erro)
    if novo is None:
        return reg
    r = reg.rect
    if not hasattr(base, "_crescimentos"):
        base._crescimentos = {}
    base._crescimentos[reg.uid] = (reg.nome or reg.tipo.value,
                                   round(r.alt_mm, 2), round(novo.alt_mm, 2))
    caixas[reg.uid] = (novo.x_mm, novo.y_mm, novo.x_mm + novo.larg_mm,
                       novo.y_mm + novo.alt_mm,
                       caixas.get(reg.uid, (0, 0, 0, 0, ""))[4])
    return replace(reg, rect=novo)


def problemas_de_grade(layout, fontes_dir=None, dpi: int | None = None) -> list[str]:
    """§2 pelo lado do AVISO (I2): as regiões que a composição não vai
    conseguir acomodar — a MESMA conta do desenho, sem compor. O
    pré-voo pergunta isto para o dono ler a frase em vez de levar um
    travamento na hora de exportar."""
    from app.core.paths import SystemRoot

    fontes = Path(fontes_dir) if fontes_dir else SystemRoot().fontes
    dpi_ef = int(dpi) if dpi else getattr(layout, "dpi", 300)
    piso = piso_do_celular(getattr(layout, "largura_mm", 0))
    achados: list[str] = []
    for pg in getattr(layout, "paginas", []):
        caixas = {
            r.uid: (r.rect.x_mm, r.rect.y_mm,
                    r.rect.x_mm + r.rect.larg_mm,
                    r.rect.y_mm + r.rect.alt_mm,
                    f"{r.nome or r.tipo.value} ({s.id})")
            for s in pg.slots for r in s.regioes if r.visivel}
        pag = (layout.largura_mm, layout.altura_mm)
        for slot in pg.slots:
            for reg in slot.regioes:
                if not reg.visivel or reg.tipo not in _TIPOS_DE_TEXTO:
                    continue
                r_ef = reg
                if reg.tipo == TipoRegiao.NOME:
                    r_ef = replace(reg, tamanho_min_pt=min(
                        reg.tamanho_max_pt, max(reg.tamanho_min_pt, piso)))
                _novo, erro = plano_de_crescimento(
                    r_ef, dpi_ef, fontes, caixas, pag)
                if erro:
                    achados.append(f"{slot.id}: {erro}")
    return achados


def _desenhar_texto(
    base: Image.Image,
    draw: ImageDraw.ImageDraw,
    reg: Regiao,
    texto: str,
    dpi: int,
    fontes_dir: Path,
) -> None:
    if not texto:
        return
    reg = crescer_do_piso(base, reg, dpi, fontes_dir)
    x, y, rw, rh = _rect_px(reg.rect, dpi)
    aj = ajustar_texto(
        texto, fontes_dir / reg.fonte, rw, rh, reg.tamanho_max_pt, dpi,
        reg.tamanho_min_pt, sem_hifen=reg.sem_hifen,  # F13-BIS/T5
        # L25: as marcas conhecidas viajam com o DADO e nunca se
        # partem (o vocabulário chega pronto do serviço, 1x por lote)
        atomos=getattr(base, '_atomos_marcas', frozenset()),
    )
    # DUODETRICESIMUS §14 (a rede dos oito): o que foi REALMENTE
    # desenhado fica registrado na base — linhas e corpo final, por
    # região. É a fonte de prova das auditorias (recalcular por fora
    # mede outra coisa: sem a escada, sem os rects substituídos).
    if not hasattr(base, "_texto_desenhado"):
        base._texto_desenhado = {}
    base._texto_desenhado[reg.uid] = {
        "linhas": list(aj.linhas), "pt": aj.tamanho_pt,
        "altura_px": aj.altura_linha_px * len(aj.linhas),
        "tipo": reg.tipo.value, "nome": reg.nome,
        "rect_alt_px": rh, "texto": texto,
        "max_pt": reg.tamanho_max_pt, "min_pt": reg.tamanho_min_pt,
    }
    total_h = aj.altura_linha_px * len(aj.linhas)
    oy = _y_alinhado(y, rh, total_h, reg)     # F13/C4: TOPO/CENTRO/BASE
    # TERTIUSDECIMUS/A1 (a rede do invariante): NENHUM texto desenha
    # fora do rect da região — bloco maior que a caixa não transborda
    # pelo alinhamento (era a 1ª linha da Terça sobre a palha da
    # cesta); o clamp corta ao que cabe — a precedência (N1) é quem
    # evita chegar aqui
    if total_h > rh:
        oy = y
        n_cabem = max(1, int(rh // max(1, aj.altura_linha_px)))
        aj.linhas = aj.linhas[:n_cabem]
    else:
        oy = min(max(oy, y), y + rh - total_h)

    # R-035: pílula atrás do texto (antes das letras), justa ao bloco usado
    if reg.pill:
        larg_max = max((aj.fonte.getlength(l) for l in aj.linhas), default=0.0)
        pad = max(2, round(aj.altura_linha_px * 0.22))
        pw = min(rw, round(larg_max) + 2 * pad)
        ph = min(rh, total_h + 2 * pad)
        px0 = int(_x_alinhado(x, rw, pw, reg.alinhamento))
        _desenhar_pill(base, px0, oy - pad, pw, ph, reg.pill_cor, reg.pill_opacidade)

    ultima = len(aj.linhas) - 1
    for i, linha in enumerate(aj.linhas):
        py = oy + i * aj.altura_linha_px
        palavras = linha.split(" ")
        # justificado: espalha as palavras (menos na última linha)
        if reg.alinhamento == Alinhamento.JUSTIFICADO and i != ultima and len(palavras) > 1:
            larg = sum(aj.fonte.getlength(p) for p in palavras)
            gap = (rw - larg) / (len(palavras) - 1)
            cx = x
            for p in palavras:
                _texto_com_efeito(draw, (cx, py), p, aj.fonte, reg)
                cx += aj.fonte.getlength(p) + gap
        else:
            lw = aj.fonte.getlength(linha)
            lx = _x_alinhado(x, rw, lw, reg.alinhamento)
            _texto_com_efeito(draw, (lx, py), linha, aj.fonte, reg)


def _desenhar_forma_preco(base: Image.Image, reg: Regiao, dpi: int) -> None:
    """F13-BIS/T1: pinta a FORMA da identidade do encarte atrás do preço.

    A caixa da região É a forma (o tamanho vem da tabela do gerador);
    o texto é desenhado por cima pelo caminho de sempre. Todas levam a
    sombra deslocada dos geradores (rgba escura a ~30%). O giro vem do
    ``rotacao_graus`` (a região inteira gira — RG-12)."""
    if reg.forma_preco == FormaPreco.TEXTO:
        return
    x, y, w, h = _rect_px(reg.rect, dpi)
    if w <= 2 or h <= 2:
        return
    m = max(6, h // 4)                    # margem p/ sombra e pétalas
    tile = Image.new("RGBA", (w + 2 * m, h + 2 * m), (0, 0, 0, 0))
    d = ImageDraw.Draw(tile)
    caixa = (m, m, m + w - 1, m + h - 1)
    sombra = tuple(c + 3 for c in caixa[:2]) + \
        tuple(c + 3 for c in caixa[2:])
    cor_sombra = (36, 29, 20, 76)         # o rgba(36,29,20,0.3) do pacote
    borda = reg.forma_cor_borda
    esp = max(2, h // 18)

    if reg.forma_preco == FormaPreco.TAG_ARREDONDADA:
        r = max(3, round(h * 0.28))
        d.rounded_rectangle(sombra, radius=r, fill=cor_sombra)
        d.rounded_rectangle(caixa, radius=r, fill=reg.forma_cor,
                            outline=borda, width=esp if borda else 0)
    elif reg.forma_preco == FormaPreco.PILULA:
        r = h // 2
        d.rounded_rectangle(sombra, radius=r, fill=cor_sombra)
        d.rounded_rectangle(caixa, radius=r, fill=reg.forma_cor,
                            outline=borda, width=esp if borda else 0)
    elif reg.forma_preco == FormaPreco.OVAL:
        d.ellipse(sombra, fill=cor_sombra)
        d.ellipse(caixa, fill=reg.forma_cor,
                  outline=borda, width=esp if borda else 0)
    elif reg.forma_preco == FormaPreco.MEDALHAO_ESTRELA:
        # o selo de cera da Segunda: 18 pétalas em raio R-1 + disco +
        # anel interno (espec do gerador: selo_cera, gen_segunda3:24)
        import math
        cx, cy = m + w / 2, m + h / 2
        R = min(w, h) / 2
        rp = max(3.0, R * 0.175)
        for dx, dy_, cor in ((2, 4, cor_sombra), (0, 0, reg.forma_cor)):
            for k in range(18):
                a = k * math.tau / 18
                px_ = cx + dx + (R - 1) * math.cos(a) * 0.92
                py_ = cy + dy_ + (R - 1) * math.sin(a) * 0.92
                d.ellipse((px_ - rp, py_ - rp, px_ + rp, py_ + rp),
                          fill=cor)
            d.ellipse((cx + dx - R, cy + dy_ - R,
                       cx + dx + R, cy + dy_ + R), fill=cor)
        if borda:
            ri = R - rp
            d.ellipse((cx - ri, cy - ri, cx + ri, cy + ri),
                      outline=borda, width=max(1, round(R * 0.035)))
    elif reg.forma_preco == FormaPreco.ETIQUETA_GIRADA:
        # a bandeirola do açougue: corpo + ponta em seta à DIREITA,
        # sem contorno (espec: bandeira, gen_carne_final:150)
        p = round(h * 0.30)
        pts = [(m, m), (m + w - 1 - p, m),
               (m + w - 1, m + h // 2),
               (m + w - 1 - p, m + h - 1), (m, m + h - 1)]
        d.polygon([(px_ + 3, py_ + 4) for px_, py_ in pts],
                  fill=(33, 26, 18, 64))
        d.polygon(pts, fill=reg.forma_cor,
                  outline=borda, width=esp if borda else 0)
    elif reg.forma_preco == FormaPreco.ETIQUETA_PENDURADA:
        # o disco escalopado da Terça, pendurado por um cordão em "Λ"
        # (espec: disco, gen_terca_final:127) — 18 dentes, anel
        # tracejado interno; o cordão sobe pela margem do tile
        import math
        cx, cy = m + w / 2, m + h / 2
        R = min(w, h) / 2
        rp = max(2.5, R * 0.17)
        fio = "#B99B6B"
        d.line((cx - R * 0.28, cy - R * 0.85, cx, cy - R * 1.18),
               fill=fio, width=2)
        d.line((cx, cy - R * 1.18, cx + R * 0.28, cy - R * 0.85),
               fill=fio, width=2)
        for dx, dy_, cor in ((2, 4, cor_sombra), (0, 0, reg.forma_cor)):
            for k in range(18):
                a = k * math.tau / 18
                px_ = cx + dx + (R - 1) * math.cos(a) * 0.94
                py_ = cy + dy_ + (R - 1) * math.sin(a) * 0.94
                d.ellipse((px_ - rp, py_ - rp, px_ + rp, py_ + rp),
                          fill=cor)
            d.ellipse((cx + dx - R, cy + dy_ - R,
                       cx + dx + R, cy + dy_ + R), fill=cor)
        if borda:
            d.ellipse((cx - R, cy - R, cx + R, cy + R),
                      outline=borda, width=1)
        ri = R * 0.8
        for k in range(24):                # o anel tracejado claro
            a0 = k * 360 / 24
            d.arc((cx - ri, cy - ri, cx + ri, cy + ri),
                  start=a0, end=a0 + 7, fill=reg.cor, width=1)
    elif reg.forma_preco == FormaPreco.ETIQUETA_LISTRADA:
        # a etiqueta do QUINTOU: vermelho com listras diagonais claras
        # (ref.: "Quintou do Real Frente Preço.png" do acervo do dono)
        r = max(3, round(h * 0.12))
        d.rounded_rectangle(sombra, radius=r, fill=cor_sombra)
        d.rounded_rectangle(caixa, radius=r, fill=reg.forma_cor)
        listra = Image.new("RGBA", tile.size, (0, 0, 0, 0))
        dl = ImageDraw.Draw(listra)
        passo = max(12, h // 3)
        for k in range(-(h + w) // passo, (h + w) // passo + 1):
            x0l = m + k * passo
            dl.line((x0l, m + h, x0l + h, m), fill=(255, 255, 255, 115),
                    width=max(4, h // 9))
        recorte = Image.new("L", tile.size, 0)
        ImageDraw.Draw(recorte).rounded_rectangle(caixa, radius=r,
                                                  fill=255)
        listra.putalpha(Image.composite(
            listra.getchannel("A"), Image.new("L", tile.size, 0),
            recorte))
        tile.alpha_composite(listra)
        d = ImageDraw.Draw(tile)
        if borda:
            d.rounded_rectangle(caixa, radius=r, outline=borda,
                                width=esp)
    elif reg.forma_preco == FormaPreco.CARIMBO:
        # o carimbo do Jornal: borda perfurada + moldura interna.
        # DUODEVICESIMUS §1: o carimbo agora CAVALGA a foto do produto
        # (a lei da proximidade) — a etiqueta é OPACA como todo encarte
        # faz: fundo do papel por baixo do número (vazado, o laranja
        # sumia sobre o saco amarelo da Yoki). Sobre o papel creme o
        # fundo é invisível; sobre a foto, ele faz o preço LER.
        cor_c = reg.forma_cor
        d.rounded_rectangle((m, m, m + w - 1, m + h - 1),
                            radius=max(3, round(h * 0.08)),
                            fill="#F7F3E9")
        sw = max(2, round(h * 0.055))
        passo, traco = max(10, w // 9), max(7, w // 14)
        xx = m
        while xx < m + w - 1:              # tracejado em cima e embaixo
            fim = min(xx + traco, m + w - 1)
            d.line((xx, m, fim, m), fill=cor_c, width=sw)
            d.line((xx, m + h - 1, fim, m + h - 1), fill=cor_c, width=sw)
            xx += passo
        yy = m
        while yy < m + h - 1:              # e nas laterais
            fim = min(yy + traco, m + h - 1)
            d.line((m, yy, m, fim), fill=cor_c, width=sw)
            d.line((m + w - 1, yy, m + w - 1, fim), fill=cor_c, width=sw)
            yy += passo
        ins = max(4, round(h * 0.12))
        d.rounded_rectangle((m + ins, m + ins,
                             m + w - 1 - ins, m + h - 1 - ins),
                            radius=max(2, round(h * 0.08)),
                            outline=cor_c, width=1)
    base.paste(tile, (x - m, y - m), tile)


def _desenhar_quadro_dica(base, draw, reg, dpi, fontes_dir) -> None:
    """§7.4.3: a MOLDURA do Fica a Dica (era arte rasterizada na BASE
    do Jornal; caixa vazia com pautas lia como falha de impressão) —
    desenhada pelo app SOMENTE quando há dica. Geometria derivada do
    rect do texto com as margens da arte original (aproximação
    declarada: caixa + tracejado interno + chip verde + losango; o
    lápis ornamental ficou na memória da arte)."""
    x, y, rw, rh = _rect_px(reg.rect, dpi)
    f = mm_para_px(0.2646, dpi)          # 1 px do viewBox 1080, em px
    qx = round(x - 16 * f)
    qy = round(y - 38 * f)
    qw = round(rw + 30 * f)
    qh = round(rh + 44 * f)
    draw.rectangle((qx, qy, qx + qw, qy + qh), outline="#201B12",
                   width=max(1, round(1.3 * f)))
    m = round(4 * f)
    d2 = ImageDraw.Draw(base, "RGBA")
    d2.rectangle((qx + m, qy + m, qx + qw - m, qy + qh - m),
                 outline=(245, 134, 52, 180), width=max(1, round(f)))
    cw, ch = round(126 * f), round(23 * f)
    cx, cy = qx + round(12 * f), qy + round(10 * f)
    draw.rectangle((cx, cy, cx + cw, cy + ch), fill="#0F783F")
    fonte = fonte_segura(fontes_dir, "Archivo-Bold.ttf",
                         round(11.5 * f * 96 / 72))
    draw.text((cx + cw // 2, cy + ch // 2), "FICA A DICA",
              font=fonte, fill="#F7F3E9", anchor="mm")
    lx, ly = cx + cw + round(18 * f), cy + round(11 * f)
    s = round(5 * f)
    draw.polygon([(lx, ly), (lx + s, ly - s), (lx + 2 * s, ly),
                  (lx + s, ly + s)], fill=(245, 134, 52))


def _detalhe_no_rect(base: Image.Image, x: int, y: int, w: int,
                     h: int) -> float:
    """§4.1 da TERTIUS: quanta INFORMAÇÃO visual mora na área (o
    desvio-padrão do recorte em tons de cinza) — a régua do espelho
    da mordida: canto com muito detalhe = provável MARCA/rótulo."""
    x0, y0 = max(0, x), max(0, y)
    x1 = min(base.width, x + max(1, w))
    y1 = min(base.height, y + max(1, h))
    if x1 <= x0 or y1 <= y0:
        return 0.0
    rec = base.crop((x0, y0, x1, y1)).convert("L")
    rec.thumbnail((32, 32))
    px = list(rec.getdata())
    if not px:
        return 0.0
    media = sum(px) / len(px)
    return (sum((p - media) ** 2 for p in px) / len(px)) ** 0.5


def _tinta_no_rect(base: Image.Image, x: int, y: int, w: int,
                   h: int) -> float:
    """Fração de pixels que NÃO são papel na área (dist > 40 do creme
    #F7F3E9) — a régua do pouso da etiqueta (§4.1)."""
    x0, y0 = max(0, x), max(0, y)
    x1 = min(base.width, x + w)
    y1 = min(base.height, y + h)
    if x1 <= x0 or y1 <= y0:
        return 1.0
    reg = base.crop((x0, y0, x1, y1)).convert("RGB")
    reg.thumbnail((48, 24))              # amostra barata
    px = list(reg.getdata())
    fora = sum(1 for r, g, b in px
               if abs(r - 0xF7) + abs(g - 0xF3) + abs(b - 0xE9) > 120)
    return fora / max(1, len(px))


def _canto_mais_vazio(base, reg_preco, regioes, rects_subst, dpi):
    """UNDEVICESIMUS §7.3: a etiqueta que cruza a zona da foto pousa
    pela SILHUETA (a tinta pintada do produto, nunca a caixa):

    - produto ESTREITO (etiqueta > 45% da largura visível — garrafa,
      caixinha): a etiqueta sai da silhueta e pousa AO LADO, dentro
      da zona;
    - produto LARGO: a etiqueta MORDE O CANTO inferior direito
      (~40% dela sobre a tinta) — o centro do produto nunca é coberto
      e a área invadida fica ≤ 25% da tinta.

    Sem silhueta registrada (máscara/arranjo), cai no §4.1: compara a
    posição da arte com a ESPELHADA por densidade de tinta, com
    histerese. Devolve o rect novo em mm, ou None (fica na arte)."""
    from app.rendering.model import Retangulo, TipoRegiao as _TR
    img = next((r for r in regioes
                if r.tipo == _TR.IMAGEM and r.visivel), None)
    if img is None:
        return None
    r_img = rects_subst.get(img.uid) or img.rect
    rp = reg_preco.rect
    # só interessa quando a etiqueta cruza a zona da foto (o Jornal)
    if not (rp.x_mm < r_img.x_mm + r_img.larg_mm
            and rp.x_mm + rp.larg_mm > r_img.x_mm
            and rp.y_mm < r_img.y_mm + r_img.alt_mm
            and rp.y_mm + rp.alt_mm > r_img.y_mm):
        return None

    def _px(v):
        return round(mm_para_px(v, dpi))

    sil = getattr(base, "_silhuetas", {}).get(img.uid)
    if sil:
        ox, oy, nw, nh = sil             # px da tinta pintada
        px_por_mm = mm_para_px(1.0, dpi)
        sil_x0, sil_x1 = ox / px_por_mm, (ox + nw) / px_por_mm
        larg_sil = sil_x1 - sil_x0
        cel_x1 = r_img.x_mm + r_img.larg_mm
        # VICESIMUS-SECUNDUS §1: a etiqueta ESCALA com o produto —
        # tamanho absoluto virava TAMPA no pacote pequeno (o carimbo
        # cobria o Passatempo inteiro). Alvo: largura ≈ 55% da
        # silhueta, com PISO de legibilidade em 72% da arte (o corpo
        # do preço cede junto no desenho); produto que mesmo assim
        # ficaria tampado já cresceu pelo LEQUE (§4: a ordem importa).
        # TERTIUS §2: o ACHATADO tem teto PRÓPRIO (≤35% da largura e
        # ≤40% da altura da silhueta — 25% de área num pacote baixo
        # vira uma faixa atravessando tudo).
        alt_sil = (oy + nh) / px_por_mm - oy / px_por_mm
        fator = max(0.72, min(1.0, 0.55 * larg_sil / rp.larg_mm))
        if larg_sil / max(alt_sil, 0.1) >= 1.3:      # achatado
            fator = max(0.72, min(
                fator,
                0.35 * larg_sil / rp.larg_mm,
                0.40 * alt_sil / rp.alt_mm))
        le = rp.larg_mm * fator
        ae = rp.alt_mm * fator
        # VICESIMUS-PRIMUS/P3 + TERTIUS §4.1: a etiqueta MORDE O
        # PRODUTO — DUAS posições, não quatro: o canto inf-DIREITO por
        # padrão; quando a MARCA mora nele (mais DETALHE de tinta que
        # no esquerdo), espelha para o inf-ESQUERDO. O olho ainda
        # aprende o padrão.
        mordida = min(0.4 * le, 0.5 * larg_sil)
        y_novo = rp.y_mm + (rp.alt_mm - ae)
        alt_px = round(mm_para_px(ae, dpi))
        y_px = round(mm_para_px(y_novo, dpi))
        det_dir = _detalhe_no_rect(
            base, round(mm_para_px(sil_x1 - mordida, dpi)), y_px,
            round(mm_para_px(mordida, dpi)), alt_px)
        det_esq = _detalhe_no_rect(
            base, round(mm_para_px(sil_x0, dpi)), y_px,
            round(mm_para_px(mordida, dpi)), alt_px)
        cel_x0 = r_img.x_mm
        if det_dir > det_esq * 1.6:      # a marca está no direito
            x_novo = max(sil_x0 + mordida - le, cel_x0 - 2.0)
        else:
            x_novo = min(sil_x1 - mordida, cel_x1 - le + 2.0)
        # a BASE da etiqueta fica onde a arte mandou (o bloco de texto
        # vem logo abaixo) — encolher sobe o topo, não desce a base
        if abs(x_novo - rp.x_mm) < 0.5 and fator > 0.99:
            return None
        return Retangulo(x_novo, y_novo, le, ae)

    # fallback §4.1 (sem silhueta): o espelho por densidade
    x_esp = 2 * r_img.x_mm + r_img.larg_mm - rp.x_mm - rp.larg_mm
    if abs(x_esp - rp.x_mm) < 1.0:       # centrado: nada a decidir
        return None
    atual = _tinta_no_rect(base, _px(rp.x_mm), _px(rp.y_mm),
                           _px(rp.larg_mm), _px(rp.alt_mm))
    espelho = _tinta_no_rect(base, _px(x_esp), _px(rp.y_mm),
                             _px(rp.larg_mm), _px(rp.alt_mm))
    if espelho < atual * 0.7:            # claramente mais limpo
        return Retangulo(x_esp, rp.y_mm, rp.larg_mm, rp.alt_mm)
    return None


def _regiao_palco_da_forma(reg: Regiao) -> Regiao:
    """F13-BIS/T1: a sub-caixa ÚTIL da forma, onde o texto do preço vive.

    Numa forma, o texto centraliza NELA (não na caixa da região — o
    medalhão numa caixa larga deixava o texto fora do disco) e tem de
    caber na tinta: cada forma tem seu palco (o disco do medalhão é
    menor que a caixa; a plaquinha pendurada começa abaixo do fio)."""
    import dataclasses

    from app.rendering.model import Retangulo

    x, y, w, h = (reg.rect.x_mm, reg.rect.y_mm,
                  reg.rect.larg_mm, reg.rect.alt_mm)
    f = reg.forma_preco
    if f == FormaPreco.ETIQUETA_LISTRADA:
        # QUATER/L9 (medido no publicado do Quintou): o "R$" pequeno é
        # GRAVADO na arte no topo-centro; o NÚMERO domina a etiqueta
        # (cap ≈ 53% da altura, baseline ≈ 88%). O palco é quase a
        # etiqueta inteira ancorado na BASE — o só-reduz do SEPARADO
        # dita o corpo final pelo palco, então o palco é a régua.
        pw, ph = w * 0.96, h * 0.90
        px_, py_ = x + (w - pw) / 2, y + h * 0.06
        return dataclasses.replace(
            reg, rect=Retangulo(px_, py_, pw, ph),
            alinhamento=Alinhamento.CENTRO,
            alinhamento_v=AlinhamentoV.BASE)
    if f in (FormaPreco.MEDALHAO_ESTRELA, FormaPreco.ETIQUETA_PENDURADA):
        lado = min(w, h)                     # o texto vive no DISCO
        pw, ph = lado * 0.80, lado * 0.52
        px_, py_ = x + (w - pw) / 2, y + (h - ph) / 2
    elif f == FormaPreco.OVAL:
        pw, ph = w * 0.72, h * 0.70
        px_, py_ = x + (w - pw) / 2, y + (h - ph) / 2
    elif f == FormaPreco.ETIQUETA_GIRADA:
        pw, ph = w * 0.76, h * 0.80          # a ponta come a direita
        px_, py_ = x + w * 0.05, y + (h - ph) / 2
    elif f == FormaPreco.CARIMBO:
        pw, ph = w * 0.80, h * 0.66
        px_, py_ = x + (w - pw) / 2, y + (h - ph) / 2
    else:                                    # TAG/PILULA
        pw, ph = w * 0.84, h * 0.80
        px_, py_ = x + (w - pw) / 2, y + (h - ph) / 2
    return dataclasses.replace(
        reg, rect=Retangulo(px_, py_, pw, ph),
        alinhamento=Alinhamento.CENTRO,
        alinhamento_v=AlinhamentoV.CENTRO)


def _cor_dominante_saturada(base: Image.Image, x: int, y: int,
                            w: int, h: int) -> tuple | None:
    """§3.2 (VICESIMUS-QUARTUS): a cor da PRÓPRIA etiqueta — o tom
    saturado mais frequente do miolo (quantizado); listra clara/preta
    (sem saturação) fica de fora. None quando não há cor dominante."""
    if w <= 4 or h <= 4:
        return None
    # o MIOLO do rect (a etiqueta com certeza mora nele) e NEAREST —
    # o resize bilinear MISTURAVA a listra vermelha com o fundo azul e
    # o chapado saía ROXO (visto na 1ª prova do Quintou)
    cx0, cy0 = x + round(w * 0.20), y + round(h * 0.20)
    amostra = base.crop(
        (cx0, cy0, x + w - round(w * 0.20), y + h - round(h * 0.20))
    ).convert("RGB").resize((24, 12), Image.NEAREST)
    freq: dict[tuple, int] = {}
    for r, g, b in amostra.getdata():
        if max(r, g, b) - min(r, g, b) < 40:
            continue
        chave = (r // 24 * 24 + 12, g // 24 * 24 + 12, b // 24 * 24 + 12)
        freq[chave] = freq.get(chave, 0) + 1
    if not freq:
        return None
    return max(freq, key=freq.get)


def _chapado_atras_do_numero(base: Image.Image, reg: Regiao,
                             dpi: int) -> None:
    """VICESIMUS-QUARTUS §3.2 (L22 — vale nos oito): número branco
    sobre HACHURA não se lê — um fundo CHAPADO na cor dominante da
    própria etiqueta entra atrás do palco do número; as listras
    seguem vivas na borda. Vale com a camada do dono E com o
    sintético. Sem cor saturada dominante (arte atípica), não se
    chapa — degradação declarada, nunca um retângulo inventado."""
    x, y, w, h = _rect_px(reg.rect, dpi)
    cor = _cor_dominante_saturada(base, x, y, w, h)
    if cor is None:
        return
    # QUINTUS/L23: o topo fica LIVRE — o "R$" gravado na arte do dono
    # aparece EMPILHADO acima do número (como no publicado dele)
    mx, my_topo, my_base = round(w * 0.06), round(h * 0.30), round(h * 0.10)
    tile = Image.new("RGBA",
                     (max(1, w - 2 * mx), max(1, h - my_topo - my_base)),
                     (0, 0, 0, 0))
    d2 = ImageDraw.Draw(tile)
    d2.rounded_rectangle(
        [0, 0, tile.width - 1, tile.height - 1],
        radius=max(3, round(min(tile.width, tile.height) * 0.18)),
        fill=tuple(cor) + (255,))
    base.paste(tile, (x + mx, y + my_topo), tile)


def corpo_pela_caixa(reg: Regiao, valor, dpi: int,
                     fontes_dir: Path) -> tuple[float, float]:
    """VICESIMUS-SEXTUS/L24: o corpo (pt) que ENCHE o elemento de arte
    — cresce até a largura do conjunto chegar a ~85% OU a altura do
    algarismo chegar a ~88% da caixa, o que bater primeiro (os tetos
    calibrados pela sobreposição com o publicado do Quintou; preço
    curto ganha corpo maior — a variação 55→80 px da referência).
    Devolve ``(pt, altura_do_algarismo_px)``."""
    from app.rendering.units import pt_para_px as _ppx
    _x, _y, rw, rh = _rect_px(reg.rect, dpi)
    reais, centavos = _reais_centavos(valor)
    prefixo = "R$ " if reg.mostrar_moeda else ""
    razao = ((reg.tamanho_centavos_pt or reg.tamanho_max_pt * 0.5)
             / max(reg.tamanho_max_pt, 0.001))
    lo, hi = 4.0, 300.0
    alt_lo = 0.0
    for _ in range(22):
        mid = (lo + hi) / 2
        f_g = fonte_segura(fontes_dir, reg.fonte, round(_ppx(mid, dpi)))
        f_p = fonte_segura(fontes_dir, reg.fonte_centavos or reg.fonte,
                           round(_ppx(mid * razao, dpi)))
        total = (f_p.getlength(prefixo) + f_g.getlength(reais)
                 + f_p.getlength("," + centavos))
        bb = f_g.getbbox(reais)
        alt_alg = (bb[3] - bb[1]) if bb else sum(f_g.getmetrics())
        if total <= rw * 0.85 and alt_alg <= rh * 0.84:
            lo, alt_lo = mid, alt_alg
        else:
            hi = mid
    return lo, alt_lo


def _desenhar_preco(
    base: Image.Image,
    draw: ImageDraw.ImageDraw,
    reg: Regiao,
    dados: DadosProduto,
    dpi: int,
    fontes_dir: Path,
) -> None:
    # R-070: multi-preço ("3 por R$10") é TEXTO — desenha na região POR/ÚNICO
    # (a região DE segue mostrando o preço antigo em Decimal, se houver).
    # Rodada JM (B2B): o preço-texto ganha a MESMA forma do preço
    # numérico ("SUPER OFERTA" sai DENTRO da pílula/estrela do encarte,
    # como o publicado do dono) — antes retornava antes da forma e o
    # texto saía pelado. A guarda L9 da camada vale igual.
    if reg.papel_preco != PapelPreco.DE and dados.multi_preco:
        if reg.forma_preco != FormaPreco.TEXTO:
            if not (reg.forma_preco == FormaPreco.ETIQUETA_LISTRADA
                    and getattr(base, "_tem_camada", False)):
                _desenhar_forma_preco(base, reg, dpi)
            if reg.forma_preco == FormaPreco.ETIQUETA_LISTRADA:
                _chapado_atras_do_numero(base, reg, dpi)   # §3.2
            reg = _regiao_palco_da_forma(reg)
        # RODADA-125 v2 (DECISÃO DO DONO, 03/08 — reverte o K2 do §12.3):
        # o carimbo SUPER OFERTA sai SÓ com o texto — "não pode ter o
        # valor junto": o preço da super-oferta VARIA no mês e não se
        # imprime (o dono conhece o próprio jornal). O valor extraído
        # (L4) segue no ITEM — Excel/cartaz/painel o usam; só a TINTA
        # do carimbo não o mostra. Conflito K2×dono documentado na
        # RODADA_125 para a reauditoria.
        # ORDEM pós-v4.1: carimbo é SELO, nunca prosa — não hifeniza
        # ("SUPER OFER-TA" saiu na capa quando o Archivo-Bold, mais
        # largo, entrou no preço); o corpo cede ou quebra POR PALAVRA.
        from dataclasses import replace as _rp
        _desenhar_texto(base, draw, _rp(reg, sem_hifen=True),
                        dados.multi_preco, dpi, fontes_dir)
        return

    valor = dados.preco_de if reg.papel_preco == PapelPreco.DE else dados.preco_por
    if valor is None:
        return

    # F13-BIS/T1: a forma da identidade do encarte ANTES do texto — e o
    # texto passa a viver no PALCO da forma (centrado nela e coubível
    # na tinta, nunca na caixa larga da região).
    if reg.forma_preco != FormaPreco.TEXTO:
        # QUATER/L9: com a CAMADA do dono na página, a etiqueta
        # verdadeira JÁ ESTÁ pintada — o sintético não desenha (seria
        # a imitação por cima do original); só o palco do número vale
        if not (reg.forma_preco == FormaPreco.ETIQUETA_LISTRADA
                and getattr(base, "_tem_camada", False)):
            _desenhar_forma_preco(base, reg, dpi)
        if (reg.forma_preco == FormaPreco.ETIQUETA_LISTRADA
                and getattr(base, "_tem_camada", False)):
            # VICESIMUS-QUARTUS §3.2 → QUINTUS/L23: o chapado vale SÓ
            # para a camada de listras VAZADAS (o fundo da página
            # vazava pelas listras e o número não se lia); ele NÃO
            # cobre o topo — o "R$" GRAVADO na arte do dono fica
            # visível EMPILHADO acima do número, como no publicado
            # (o R$ inline da QUARTUS era infiel e morreu)
            _chapado_atras_do_numero(base, reg, dpi)
        reg = _regiao_palco_da_forma(reg)

    if reg.subtipo_preco == SubtipoPreco.COMPLETO:
        reais, centavos = _reais_centavos(valor)
        moeda = "R$ " if reg.mostrar_moeda else ""
        texto = f"{moeda}{reais},{centavos}"
        if not reg.riscado:
            _desenhar_texto(base, draw, reg, texto, dpi, fontes_dir)
            return
        # riscado (preço "de" do cartaz): linha única só-reduz + traço no meio
        x, y, rw, rh = _rect_px(reg.rect, dpi)

        def _fonte(pt: float):
            return fonte_segura(fontes_dir, reg.fonte,
                                round(pt_para_px(pt, dpi)))

        fonte = _fonte(reg.tamanho_max_pt)
        w, alt = fonte.getlength(texto), sum(fonte.getmetrics())
        escala = min(1.0, rw / w if w else 1.0, rh / alt if alt else 1.0)
        if escala < 1.0:
            fonte = _fonte(reg.tamanho_max_pt * escala)
            w, alt = fonte.getlength(texto), sum(fonte.getmetrics())
        lx = _x_alinhado(x, rw, w, reg.alinhamento)
        ty = y + (rh - alt) / 2
        draw.text((lx, ty), texto, font=fonte, fill=reg.cor, anchor="la")
        meio = ty + fonte.getmetrics()[0] * 0.62      # meio visual dos algarismos
        esp = max(2, round(alt * 0.07))
        draw.line((lx - esp, meio, lx + w + esp, meio), fill=reg.cor, width=esp)
        return

    # SEPARADO: "R$" e centavos pequenos; reais grande. Centavos sobem (sobrescrito).
    x, y, rw, rh = _rect_px(reg.rect, dpi)
    reais, centavos = _reais_centavos(valor)
    fonte_cent_nome = reg.fonte_centavos or reg.fonte
    pt_grande = reg.tamanho_max_pt
    pt_peq = reg.tamanho_centavos_pt or (pt_grande * 0.5)
    prefixo = "R$ " if reg.mostrar_moeda else ""

    def montar(pt_g: float, pt_p: float):
        f_g = fonte_segura(fontes_dir, reg.fonte, round(pt_para_px(pt_g, dpi)))
        f_p = fonte_segura(fontes_dir, fonte_cent_nome, round(pt_para_px(pt_p, dpi)))
        w_prefixo = f_p.getlength(prefixo)
        w_reais = f_g.getlength(reais)
        w_cent = f_p.getlength("," + centavos)
        return f_g, f_p, w_prefixo, w_reais, w_cent

    # VICESIMUS-SEXTUS/L24: TIPO DENTRO DE ELEMENTO DE ARTE SE
    # DIMENSIONA PELO ELEMENTO — com ``preenche_caixa`` o corpo é
    # CALCULADO para preencher; nunca há max_pt, há teto de caixa.
    if getattr(reg, "preenche_caixa", False):
        pt_grande, _alt = corpo_pela_caixa(reg, valor, dpi, fontes_dir)
        pt_peq = pt_grande * ((reg.tamanho_centavos_pt or
                               reg.tamanho_max_pt * 0.5)
                              / max(reg.tamanho_max_pt, 0.001))

    f_g, f_p, w_prefixo, w_reais, w_cent = montar(pt_grande, pt_peq)
    total_w = w_prefixo + w_reais + w_cent
    asc_g = f_g.getmetrics()[0]
    alt_g = sum(f_g.getmetrics())

    # Só REDUZ para caber na largura e na altura.
    escala = min(1.0, rw / total_w if total_w else 1.0, rh / alt_g if alt_g else 1.0)
    if escala < 1.0 and not getattr(reg, "preenche_caixa", False):
        f_g, f_p, w_prefixo, w_reais, w_cent = montar(pt_grande * escala, pt_peq * escala)
        total_w = w_prefixo + w_reais + w_cent
        asc_g = f_g.getmetrics()[0]
        alt_g = sum(f_g.getmetrics())

    asc_p = f_p.getmetrics()[0]
    cursor = _x_alinhado(x, rw, total_w, reg.alinhamento)
    x0 = cursor                                            # início (p/ o riscado)
    if getattr(reg, "preenche_caixa", False):
        # SEXTUS/L24: o PÉ do algarismo assenta a ~88% da caixa — o
        # ponto MEDIDO no publicado (pé do "9,99" da referência); a
        # centralização pela linha da fonte (asc+desc folgados)
        # empurrava o número para baixo do carimbo
        baseline = y + round(rh * 0.80)
    else:
        baseline = y + (rh + alt_g) / 2 - f_g.getmetrics()[1]  # centraliza

    # UNDEVICESIMUS §4.4: NÚMEROS TABULARES no preço (tnum) — os
    # dígitos ganham a mesma largura e os preços alinham dígito a
    # dígito entre células. BEST-EFFORT declarado: fontes carregadas
    # com layout BASIC (sem Raqm) recusam `features` com KeyError —
    # o refinamento NUNCA derruba o desenho (caiu nas etiquetas em
    # lote do marco na 1ª bancada); sem a feature, sai como sempre.
    def _texto_preco(xy, txt, fonte_d):
        try:
            draw.text(xy, txt, font=fonte_d, fill=reg.cor, anchor="ls",
                      features=["tnum"])
        except (KeyError, TypeError):
            draw.text(xy, txt, font=fonte_d, fill=reg.cor, anchor="ls")
    if prefixo:
        _texto_preco((cursor, baseline), prefixo, f_p)
    cursor += w_prefixo
    _texto_preco((cursor, baseline), reais, f_g)
    cursor += w_reais
    # centavos: sobrescritos (o padrão de sempre) ou na MESMA baseline
    # (F13-BIS/T1 — os selos/discos/bandeiras do pacote)
    baseline_cent = baseline if reg.centavos_na_base \
        else baseline - (asc_g - asc_p)
    _texto_preco((cursor, baseline_cent), "," + centavos, f_p)

    if reg.riscado:   # traço sobre o preço inteiro (o "de" do cartaz)
        meio = baseline - asc_g * 0.32
        esp = max(2, round(alt_g * 0.06))
        draw.line((x0 - esp, meio, cursor + w_cent + esp, meio),
                  fill=reg.cor, width=esp)


# ==============================================================================
# API
# ==============================================================================


def _desenhar_regiao(base, draw, reg, dados, dpi, fontes_dir, tem_regiao_unidade):
    if not reg.visivel:
        return
    if reg.rotacao_graus % 360:          # RG-12: a data deitada do template
        _desenhar_regiao_rotacionada(base, reg, dados, dpi, fontes_dir,
                                     tem_regiao_unidade)
        return
    _desenhar_regiao_reta(base, draw, reg, dados, dpi, fontes_dir,
                          tem_regiao_unidade)


_FUNDO_LIMPO_CACHE: dict = {}


def _desenhar_adorno(base: Image.Image, reg: Regiao, dpi: int,
                     arquivo_fundo: str | None) -> None:
    """F13-TER/V2: recola o recorte do FUNDO ORIGINAL (a cesta, o
    toldo, a banda) por cima da foto já desenhada. O fundo limpo vem do
    arquivo da página (cache por caminho+tamanho); sem fundo, não há o
    que recolar — silêncio correto (a página sintética não tem adorno)."""
    if not arquivo_fundo:
        return
    chave = (arquivo_fundo, base.size)
    fundo = _FUNDO_LIMPO_CACHE.get(chave)
    if fundo is None:
        try:
            fundo = Image.open(arquivo_fundo).convert("RGB") \
                .resize(base.size)
        except OSError:
            return                          # o pré-voo já acusa a arte sumida
        _FUNDO_LIMPO_CACHE.clear()          # 1 página por vez basta
        _FUNDO_LIMPO_CACHE[chave] = fundo
    x, y, w, h = _rect_px(reg.rect, dpi)
    base.paste(fundo.crop((x, y, x + w, y + h)), (x, y))


def _desenhar_regiao_reta(base, draw, reg, dados, dpi, fontes_dir,
                          tem_regiao_unidade):
    if reg.tipo == TipoRegiao.IMAGEM:
        _desenhar_imagem(base, reg, dados, dpi)
    elif reg.tipo == TipoRegiao.NOME:
        texto = nome_com_unidade(dados.nome, dados.unidade, tem_regiao_unidade)
        if getattr(reg, "unidade_caixa_alta", False) and texto:
            # QUINTUS/L23: o publicado grafa a unidade em CAIXA ALTA
            # ("700G", "269ML") — só a exibição; o banco fica como está
            import re as _re
            texto = _re.sub(
                r"\b(\d+(?:[.,]\d+)?\s?)(g|kg|ml|l|un|und|unds)\b\.?",
                lambda m: m.group(1) + m.group(2).upper(),
                texto, flags=_re.IGNORECASE)
        _desenhar_texto(base, draw, reg, texto, dpi, fontes_dir)
    elif reg.tipo == TipoRegiao.UNIDADE:
        _desenhar_texto(base, draw, reg, dados.unidade or "", dpi, fontes_dir)
    elif reg.tipo == TipoRegiao.SUBTITULO:
        # F13-BIS/T2: a linha de descritor do modelo (fallback: unidade)
        # QUARTUSDECIMUS §2: se o completo não cabe na largura, o
        # QUALIFICADOR sai e a unidade fica — nunca "BB-X · 10…"
        # v4 (a lei do dono): o DESENHO cede o corpo até o MESMO piso
        # duro da régua — sem isto o ajustar_texto elipsaria o texto
        # que a régua aprovou em corpo reduzido
        from dataclasses import replace as _rep

        from app.rendering.nome_fit import (
            _PISO_DURO_DESCRITOR,
            descritor_que_cabe,
        )
        reg_sub = (reg if reg.tamanho_min_pt <= _PISO_DURO_DESCRITOR
                   else _rep(reg, tamanho_min_pt=_PISO_DURO_DESCRITOR))
        _desenhar_texto(base, draw, reg_sub,
                        descritor_que_cabe(dados.descritor, dados.unidade,
                                           reg_sub, dpi, fontes_dir) or "",
                        dpi, fontes_dir)
    elif reg.tipo == TipoRegiao.ADORNO:
        # F13-TER/V2: o fundo volta por cima da foto (cesta/toldo/banda)
        _desenhar_adorno(base, reg, dpi,
                         getattr(base, "_arquivo_fundo", None))
    elif reg.tipo == TipoRegiao.FILETE:
        # F13-TER/N2: o fio tipográfico — retângulo chapado na cor da
        # região (o cabeçalho de seção do fluxo o põe onde a linha caiu)
        x, y, w_px, h_px = _rect_px(reg.rect, dpi)
        draw.rectangle((x, y, x + max(1, w_px) - 1, y + max(1, h_px) - 1),
                       fill=reg.cor or "#000000")
    elif reg.tipo == TipoRegiao.PRECO:
        _desenhar_preco(base, draw, reg, dados, dpi, fontes_dir)
    elif reg.tipo == TipoRegiao.TEXTO_LEGAL:
        # RG-57: o PAPEL da região decide o texto (validade viva, dica da IA,
        # aviso do preset, ou o livre) — fonte única com a prévia do editor.
        texto = texto_composto_legal(
            reg, dados, em_celula=getattr(base, "_slot_de_produto", False))
        # F13-BIS/T1: texto legal também pode vestir FORMA — o "-20%"
        # calculado da Quarta mora numa pílula laranja (pctpod); a
        # forma só pinta quando HÁ texto (papel condicional vazio não
        # deixa uma pílula oca na página)
        if texto and reg.forma_preco != FormaPreco.TEXTO:
            _desenhar_forma_preco(base, reg, dpi)
            reg = _regiao_palco_da_forma(reg)
        # UNDEVICESIMUS §7.4.3: o quadro do Fica a Dica saiu da ARTE
        # (caixa vazia com pautas lê como falha de impressão) — o app
        # o desenha SÓ quando há dica; sem texto, nada na página
        if texto and reg.papel_texto == PapelTexto.DICA:
            _desenhar_quadro_dica(base, draw, reg, dpi, fontes_dir)
        _desenhar_texto(base, draw, reg, texto, dpi, fontes_dir)
    # SELO é desenhado num passe final (âncora), não aqui.


def _desenhar_regiao_rotacionada(base, reg, dados, dpi, fontes_dir,
                                 tem_regiao_unidade):
    """RG-12: gira o CONTEÚDO em torno do centro do rect (sentido horário).

    O conteúdo é desenhado reto num palco transparente do tamanho da
    diagonal, girado, e colado de volta com o MESMO centro — o rect do
    modelo nunca muda (âncora e vínculo estáveis, I1). Rotação 0 nem passa
    aqui: o caminho reto fica byte-idêntico ao de sempre.
    """
    import math

    from app.rendering.model import Regiao, Retangulo
    from app.rendering.units import px_para_mm

    x, y, w_px, h_px = _rect_px(reg.rect, dpi)
    lado = int(math.hypot(w_px, h_px)) + 4
    palco = Image.new("RGBA", (lado, lado), (0, 0, 0, 0))
    dp = ImageDraw.Draw(palco)
    copia = Regiao.from_dict(reg.to_dict())
    copia.rotacao_graus = 0.0
    copia.rect = Retangulo(px_para_mm((lado - w_px) / 2, dpi),
                           px_para_mm((lado - h_px) / 2, dpi),
                           reg.rect.larg_mm, reg.rect.alt_mm)
    _desenhar_regiao_reta(palco, dp, copia, dados, dpi, fontes_dir,
                          tem_regiao_unidade)
    # PIL gira anti-horário com ângulo positivo; o modelo é horário
    girado = palco.rotate(-reg.rotacao_graus,
                          resample=Image.Resampling.BICUBIC, expand=False)
    cx, cy = x + w_px // 2, y + h_px // 2
    base.paste(girado, (cx - lado // 2, cy - lado // 2), girado)


def _selos_do_produto(dados: DadosProduto) -> list[Selo]:
    """Selos automáticos (flags do produto) + manuais.

    FASE 3 (passo 71): os automáticos agora vêm do GESTOR (tabela
    ``selos``): canto e arte custom valem; a regra Qualidade pode estar
    desligada. O +18 em bebida é TRAVADO: sai sempre — e sem banco
    (teste puro) tudo cai no clássico (defaults sãos, C3)."""
    try:
        from app.core.selos import config_automaticos
        cfg = config_automaticos()
    except Exception:
        cfg = {"MAIS18": {"ativo": True, "canto": "SUPERIOR_ESQUERDO",
                          "arquivo": None},
               "QUALIDADE": {"ativo": True, "canto": "SUPERIOR_DIREITO",
                             "arquivo": None}}

    def _canto(texto, padrao):
        try:
            return Canto(texto)
        except ValueError:
            return padrao

    selos: list[Selo] = []
    m18 = cfg.get("MAIS18") or {}
    if dados.mais18:                       # decisão travada: SEMPRE sai
        selos.append(Selo("MAIS18",
                          _canto(m18.get("canto"), Canto.SUPERIOR_ESQUERDO),
                          imagem_path=m18.get("arquivo")))
    q = cfg.get("QUALIDADE") or {}
    if dados.marca_propria and q.get("ativo", True):
        selos.append(Selo("QUALIDADE",
                          _canto(q.get("canto"), Canto.SUPERIOR_DIREITO),
                          imagem_path=q.get("arquivo")))
    selos.extend(dados.selos_extra)
    return selos


def _ancora_selos_slot(slot, dpi: int, w: int, h: int,
                       rects_subst: dict | None = None,
                       com_foto: bool = True,
                       ) -> tuple[int, int, int, int]:
    """Onde os selos do slot se ancoram: [SELO] > [IMAGEM] do slot > página.
    ``rects_subst`` (Q1/N1): rect efetivo por uid quando a composição
    replanejou a célula — o selo pousa onde a foto REALMENTE está.

    §15.3: SEM foto (``com_foto=False``) a zona de imagem é um VAZIO — o
    selo ancorado ali flutua encostado no filete e parece da célula
    vizinha. Nesse caso a âncora é a CÉLULA inteira (a caixa envolvente
    das regiões), nunca a zona oca."""
    subst = rects_subst or {}
    selo_rect = imagem_rect = None
    for reg in slot.regioes:
        if reg.tipo == TipoRegiao.SELO and selo_rect is None:
            selo_rect = subst.get(reg.uid, reg.rect)
        elif reg.tipo == TipoRegiao.IMAGEM and imagem_rect is None:
            imagem_rect = subst.get(reg.uid, reg.rect)
    if not com_foto:
        from app.rendering.model import Retangulo
        imagem_rect = None
        if selo_rect is None:
            vis = [subst.get(r.uid, r.rect) for r in slot.regioes
                   if r.visivel]
            if vis:
                x0 = min(r.x_mm for r in vis)
                y0 = min(r.y_mm for r in vis)
                x1 = max(r.x_mm + r.larg_mm for r in vis)
                y1 = max(r.y_mm + r.alt_mm for r in vis)
                selo_rect = Retangulo(x0, y0, x1 - x0, y1 - y0)
    rect = selo_rect or imagem_rect
    return _rect_px(rect, dpi) if rect is not None else (0, 0, w, h)


def fonte_segura(fontes_dir: Path, nome: str, px: int):
    """Carrega a fonte com cadeia de fallback (I2: nunca derrubar a exportação).

    nome pedido → Roboto-Regular.ttf → fonte embutida do Pillow. O pré-voo de
    exportação avisa quando o fallback vai ser usado.
    """
    px = max(1, int(px))
    for candidata in (nome, "Roboto-Regular.ttf"):
        caminho = fontes_dir / candidata
        if caminho.exists():
            return ImageFont.truetype(str(caminho), px)
    return ImageFont.load_default(px)


def nome_com_unidade(nome: str, unidade: str | None,
                     tem_regiao_unidade: bool) -> str:
    """Unidade automática (doc C2) com a guarda S2 da sessão ao vivo:
    NÃO anexa quando o nome JÁ contém a unidade — "Italac 200g" + "200g"
    saía "Italac 200g 200.000g" no tabloide real."""
    if tem_regiao_unidade or not unidade:
        return nome

    def _norm(s: str) -> str:
        return s.lower().replace(" ", "").replace(",", ".")

    if _norm(unidade) in _norm(nome):
        return nome
    return f"{nome} {unidade}"


def _dados_do_slot(dados, lista, i, slot_id=None):
    """``dados``: DadosProduto (mesmo em todos) · lista (por posição — legado;
    prefira o mapa) · **dict slot_id→DadosProduto** (vínculo por identidade, I1)."""
    if isinstance(dados, dict):
        return dados.get(slot_id)
    if lista is None:
        return dados
    return lista[i] if i < len(lista) else None   # célula sem produto -> vazia


def _campo_vivo_da_pagina(dados, campo: str) -> "str | None":
    """F13/D7 + TER/D1: o primeiro valor VIVO de um campo de página
    (validade, edição) nos dados — o dado é um só por página; slot
    decorativo bebe da mesma fonte dos slots mapeados."""
    valores = (dados.values() if isinstance(dados, dict)
               else dados if isinstance(dados, (list, tuple)) else [dados])
    for d in valores:
        if d is not None and getattr(d, campo, None):
            return getattr(d, campo)
    return None


def _texto_legal_da_pagina(dados) -> "str | None":
    """F13/D7: a validade viva da página (ver _campo_vivo_da_pagina)."""
    return _campo_vivo_da_pagina(dados, "texto_legal")


def _dados_do_conteudo_fixo(cf: dict) -> "DadosProduto":
    """F13-TER/N1: o DadosProduto de uma célula FIXA — o conteúdo vive
    no TEMPLATE (produto + foto escolhida pelo dono + preço), então
    compõe em TODA porta sem depender da tabela da semana. Imagem
    relativa resolve contra a biblioteca de imagens da raiz (I3)."""
    from decimal import Decimal, InvalidOperation
    preco = None
    bruto = (cf.get("preco") or "").strip()
    if bruto:
        try:
            preco = Decimal(bruto.replace("R$", "").strip()
                            .replace(".", "").replace(",", "."))
        except InvalidOperation:
            preco = None                    # pré-voo do template acusa
    def _abs(rel):
        rel = (rel or "").strip()
        if not rel:
            return None
        if Path(rel).is_absolute():
            return rel
        try:
            from app.core.paths import SystemRoot
            return str(SystemRoot().biblioteca_imagens / rel)
        except Exception:
            return rel

    img = _abs(cf.get("imagem"))
    # F13-DUODECIMUS/T5: o item fixo PAR ("Sonho + Croissant") — uma
    # foto POR ZONA da célula, na ordem das regiões IMAGEM; o singular
    # "imagem" segue valendo (a mesma foto em todas as zonas)
    imagens = [ImagemSlot(c) for c in
               (_abs(r) for r in cf.get("imagens") or []) if c]
    if imagens and img is None:
        img = imagens[0].caminho
    # QUARTUSDECIMUS (frota): a unidade da fixa é a METADE-UNIDADE do
    # descritor, nunca o descritor inteiro — "marca própria" duplicado
    # em unidade virava "unidade" pelo desempate e bloqueava o passo 4
    from app.rendering.nome_fit import dividir_descritor
    return DadosProduto(
        cf.get("nome") or "", descritor=cf.get("descritor"),
        unidade=dividir_descritor(cf.get("descritor"))[1],
        preco_por=preco, imagem_path=img,
        imagens=imagens,
        desconto_pct=cf.get("desconto_pct"))     # Q2: o 20% do Lanche


def compor_pagina(
    layout: LayoutDef,
    pagina: Pagina,
    dados: "DadosProduto | list[DadosProduto]",
    fontes_dir: str | Path | None = None,
    fundo_path: str | Path | None = None,
    dpi: int | None = None,
) -> Image.Image:
    """Compõe uma página e devolve a imagem.

    ``dados`` pode ser um DadosProduto (mesmo produto em todos os slots) ou uma
    LISTA de DadosProduto (um por slot — o tabloide de vários produtos).

    ``dpi`` sobrepõe o do layout SÓ nesta composição (F13/D2: a prévia do
    editor compõe em 96 e estica de volta ao tamanho da cena; exportar/
    salvar não passam este parâmetro e seguem no dpi do layout).
    """
    fontes_dir = Path(fontes_dir) if fontes_dir else SystemRoot().fontes
    dpi_ef = int(dpi) if dpi else layout.dpi
    w = round(mm_para_px(layout.largura_mm, dpi_ef))
    h = round(mm_para_px(layout.altura_mm, dpi_ef))

    # D8.2: prioridade explícita > arte DA PÁGINA > arte do layout (legado)
    fundo = fundo_path or pagina.arquivo_fundo or layout.arquivo_fundo
    if fundo and Path(fundo).exists():
        base = Image.open(fundo).convert("RGB")
        if base.size != (w, h):
            base = base.resize((w, h))
    else:
        base = Image.new("RGB", (w, h), "white")
    # F13-TER/V2: as regiões ADORNO recolam o FUNDO LIMPO por cima da
    # foto — o caminho viaja com a base (cada composição tem o seu;
    # nenhuma assinatura interna muda)
    base._arquivo_fundo = str(fundo) if fundo else None

    # F13-QUATER/L9: a CAMADA do dono (a arte das etiquetas de preço do
    # Quintou) é COLADA sobre o fundo, escalada à página, com o alfa —
    # o asset é consumido, nunca imitado. Com a camada presente, a
    # forma ETIQUETA_LISTRADA para de desenhar o sintético (a etiqueta
    # verdadeira já está na página) e vira só o PALCO do número.
    base._tem_camada = False
    camada = getattr(pagina, "arquivo_camada", None)
    if camada and Path(camada).exists():
        try:
            sobre = Image.open(camada).convert("RGBA")
            if sobre.size != (w, h):
                sobre = sobre.resize((w, h), Image.LANCZOS)
            base.paste(sobre, (0, 0), sobre)
            base._tem_camada = True
        except OSError:
            pass                      # arte ilegível: compõe sem camada

    lista = dados if isinstance(dados, (list, tuple)) else None

    # F8.2: seções visuais — camada DERIVADA, desenhada DEPOIS do fundo e
    # ANTES do conteúdo (o contorno corre pela folga; o trio nunca é coberto)
    if pagina.secoes_ligadas and isinstance(dados, dict):
        from app.rendering.secoes import (
            calcular_secoes, config_secoes, desenhar_secoes, estilo_secoes,
        )
        categorias = {sid: d.categoria for sid, d in dados.items()
                      if d is not None}
        secoes = calcular_secoes(pagina, categorias)
        if secoes:
            cor, esp = config_secoes()
            estilo, por_cat = estilo_secoes()   # RG-31: o modo escolhido
            # F13-QUATER/A4: o estilo DA PÁGINA vence o global (o
            # Jornal em fluxo compõe JORNAL sem tocar a Config)
            estilo = getattr(pagina, "estilo_secoes", None) or estilo
            # RODADA-125: o estilo JORNAL no estático mede a FOLGA real
            # acima de cada bloco — as caixas viajam POR REGIÃO visível
            # (o bbox de slot mentia: o slot de textos do jornal
            # atravessa a página e o subtítulo da manchete sumia da
            # régua, que riscava o texto)
            caixas = []
            for _s in pagina.slots:
                for _r in _s.regioes:
                    if not getattr(_r, "visivel", True):
                        continue
                    caixas.append((
                        _r.rect.x_mm, _r.rect.y_mm,
                        _r.rect.x_mm + _r.rect.larg_mm,
                        _r.rect.y_mm + _r.rect.alt_mm))
            desenhar_secoes(base, secoes, dpi_ef, cor=cor,
                            espessura_mm=esp, fontes_dir=fontes_dir,
                            estilo=estilo, cores_por_categoria=por_cat,
                            caixas_pagina_mm=caixas)

    # VICESIMUS-QUARTUS §1.3 (a L21 aplicada ao próprio herói): o gate
    # fixo de 60 mm fazia TODA célula do Quintou (67 mm) e do Sábado
    # (81 mm) virar "herói" — e o leque nunca disparava fora do Jornal.
    # "Editorial" é RELATIVO à página: herói é a zona de foto bem MAIOR
    # que a mediana (>60 mm E >1,25× a mediana), ou a página com menos
    # de 3 zonas (cartaz, destaque solo). Medido ANTES do desenho.
    # VICESIMUS-OCTAVUS/L25: as marcas conhecidas da PÁGINA viram
    # ÁTOMOS de hifenização — reunidas 1× (os dados já trazem as do
    # nome, extraídas na montagem oficial); o hífen nunca parte marca.
    _at: set[str] = set()
    for _d in (dados.values() if isinstance(dados, dict)
               else (dados if isinstance(dados, (list, tuple)) else [dados])):
        for _m in (getattr(_d, "marcas_nome", ()) or ()):
            for _pal in str(_m).split():
                import unicodedata as _ud
                _k = _ud.normalize("NFKD", _pal.lower())
                _at.add("".join(c for c in _k if not _ud.combining(c)))
    base._atomos_marcas = frozenset(_at)

    # UNDETRICESIMUS §2: a CAIXA cede ao piso — e para saber se pode
    # crescer, o desenho precisa da VIZINHANÇA (as caixas visíveis da
    # página, em mm) e dos limites do papel. Medidas 1× aqui.
    base._caixas_pagina = {
        r.uid: (r.rect.x_mm, r.rect.y_mm,
                r.rect.x_mm + r.rect.larg_mm, r.rect.y_mm + r.rect.alt_mm,
                f"{r.nome or r.tipo.value} ({s.id})")
        for s in pagina.slots for r in s.regioes if r.visivel}
    base._pagina_mm = (layout.largura_mm, layout.altura_mm)

    zonas_pg = [r.rect.larg_mm for s in pagina.slots
                for r in s.regioes
                if r.tipo == TipoRegiao.IMAGEM and r.visivel]
    base._heroi_uids = set()
    if zonas_pg:
        _med_pg = sorted(zonas_pg)[len(zonas_pg) // 2]
        for s in pagina.slots:
            for r in s.regioes:
                if (r.tipo == TipoRegiao.IMAGEM and r.visivel
                        and r.rect.larg_mm > 60.0
                        and (r.rect.larg_mm > _med_pg * 1.25
                             or len(zonas_pg) < 3)):
                    base._heroi_uids.add(r.uid)

    draw = ImageDraw.Draw(base)
    for i, slot in enumerate(pagina.slots):
        d = _dados_do_slot(dados, lista, i, slot_id=slot.id)
        cf = getattr(slot, "conteudo_fixo", None)
        if d is None and getattr(slot, "fixa", False) and cf:
            # F13-TER/N1: célula FIXA com conteúdo do TEMPLATE — compõe
            # como slot normal (foto escolhida, nome, preço) em toda
            # porta; a fila do auto-preencher continua sem vê-la
            d = _dados_do_conteudo_fixo(cf)
        if d is None:
            # célula sem produto fica com a arte — MAS texto fixo do layout
            # ("Fica a Dica") desenha mesmo assim (A1 da ORDEM_F5_8);
            # via _desenhar_regiao p/ a rotação valer também aqui (RG-12).
            # RG-57: a decisão "tem o que desenhar?" passa pelo mesmo helper de
            # papel (byte-idêntico ao legado, que era todo LIVRE).
            # F13/D7 (P-01, achado estrutural): a VALIDADE VIVA chega ao
            # rodapé FORA de célula — o vazio herda o texto_legal da
            # PÁGINA (o mesmo que os slots mapeados carregam); antes o
            # rodapé típico do tabloide ficava mudo e o marco da F12
            # contornava com texto_fixo.
            vazio = DadosProduto(
                "", texto_legal=_texto_legal_da_pagina(dados),
                edicao=_campo_vivo_da_pagina(dados, "edicao"))
            base._slot_de_produto = False      # rodapé/página: herda
            for reg in slot.regioes:
                if not reg.visivel:
                    continue
                if (reg.tipo == TipoRegiao.TEXTO_LEGAL
                        and texto_composto_legal(reg, vazio)) \
                        or reg.tipo == TipoRegiao.FILETE:
                    # N2: o FILETE decorativo (fio de seção) desenha
                    # mesmo sem produto — é estrutura, não conteúdo
                    _desenhar_regiao(base, draw, reg, vazio,
                                     dpi_ef, fontes_dir, False)
            continue
        # F13-TER: o SUBTITULO também suprime a unidade automática no
        # nome (quem tem linha de descritor não repete o peso no nome)
        tem_unidade = any(r.tipo in (TipoRegiao.UNIDADE,
                                     TipoRegiao.SUBTITULO)
                          and r.visivel for r in slot.regioes)
        from dataclasses import replace as _replace
        # F13-DUODECIMUS/T5: célula com VÁRIAS zonas de foto E várias
        # imagens — a k-ésima zona desenha a k-ésima foto (o par
        # "Sonho + Croissant" da Terça; o arranjo F7.2, que divide UMA
        # região, continua intocado para célula de zona única)
        zonas_img = [r for r in slot.regioes
                     if r.tipo == TipoRegiao.IMAGEM and r.visivel]
        por_zona: dict[str, str] = {}
        if len(zonas_img) > 1 and d.imagens:
            for k, rz in enumerate(zonas_img):
                im = d.imagens[min(k, len(d.imagens) - 1)]
                por_zona[rz.uid] = im.caminho
        # QUARTUSDECIMUS/Q1: a foto tem de encher a zona — o plano da
        # célula roda ANTES da precedência do nome (a cadeia trabalha
        # sobre a célula já replanejada). Só em célula marcada
        # ``zona_flex`` (arte lisa), foto ÚNICA, sem máscara nem
        # enquadramento, no ASSENTAR — o mesmo gate do caminho rápido
        # do desenho, que é onde o defeito da ordem vivia.
        rects_foto: dict = {}
        regioes_cel = slot.regioes
        if (len(zonas_img) == 1 and zonas_img[0].zona_flex
                and zonas_img[0].mascara == Mascara.RETANGULO
                and zonas_img[0].ajuste == Ajuste.ASSENTAR):
            pares_q1 = _carregar_imagens(d)
            if len(pares_q1) == 1:
                esp_q1, img_q1 = pares_q1[0]
                if (esp_q1.zoom == 1.0 and esp_q1.foco_x == 0.5
                        and esp_q1.foco_y == 0.5):
                    bb = (img_q1.getchannel("A").getbbox()
                          if img_q1.mode == "RGBA" else None)
                    iw, ih = ((bb[2] - bb[0], bb[3] - bb[1]) if bb
                              else (img_q1.width, img_q1.height))
                    from app.rendering.foto_fit import plano_da_celula
                    plano = plano_da_celula(slot.regioes, iw, ih)
                    if plano is not None:
                        rects_foto = plano.rects
                        regioes_cel = [
                            _replace(r, rect=rects_foto[r.uid])
                            if r.uid in rects_foto else r
                            for r in slot.regioes]
                        # VICESIMUS-QUARTUS §1.3: onde o plano Q1 ATUOU
                        # (o abraço do banner da Quarta — contrato do
                        # dono), o leque CEDE: são duas estratégias de
                        # preencher e o plano chegou primeiro; onde ele
                        # devolve None, quem preenche é a L19
                        if not hasattr(base, "_q1_uids"):
                            base._q1_uids = set()
                        base._q1_uids.add(zonas_img[0].uid)
        # F13-NONUS/N1: a precedência do nome é CÓDIGO — a cadeia roda
        # para toda célula, aqui, no único ponto que conhece o dado E
        # todas as regiões antes do desenho. O dado da célula é uma
        # CÓPIA (o mesmo DadosProduto pode servir a vários slots).
        # F13-UNDECIMUS/U1: o piso do tipo é a RÉGUA da página, não o
        # dado da região — o 6.0 do banco velho deixa de ser consultado
        from app.rendering.nome_fit import precedencia_do_nome
        from app.rendering.text_fit import piso_do_celular
        piso_nome = piso_do_celular(layout.largura_mm)
        aj_nome = precedencia_do_nome(d.nome, d.descritor, d.unidade,
                                      regioes_cel, dpi_ef, fontes_dir,
                                      piso_pt=piso_nome,
                                      marcas=d.marcas_nome,
                                      nome_abreviado=d.nome_abreviado)
        rects_subst: dict = dict(rects_foto)
        if aj_nome is not None:
            d = _replace(d, nome=aj_nome.nome, descritor=aj_nome.descritor,
                         unidade=None if aj_nome.descritor_saiu
                         else d.unidade)
            rects_subst.update(aj_nome.rects)
        # RODADA-125 v4.1 ("quase descolado, as imagens diminuíram"):
        # a CÉLULA DE COLUNA é ELÁSTICA — o texto mede o que realmente
        # usa, ancora no preço e a FOTO cresce até encostar nele (a
        # caixa de 3 linhas é reserva do caso cheio, não custo fixo).
        # Só quando a precedência não negociou banda (passos 3/4).
        if aj_nome is not None and not aj_nome.rects \
                and not aj_nome.descritor_saiu:
            from app.rendering.nome_fit import compactar_coluna
            rects_subst.update(compactar_coluna(
                regioes_cel, d.nome, d.descritor, d.unidade, dpi_ef,
                fontes_dir, rects_subst, piso_pt=piso_nome))
        # UNDETRICESIMUS §2: a vizinhança do crescimento é a EFETIVA —
        # os rects que este slot acabou de substituir (coluna elástica,
        # plano Q1) entram no mapa antes de qualquer desenho
        for _uid, _rc in rects_subst.items():
            if _uid in base._caixas_pagina:
                base._caixas_pagina[_uid] = (
                    _rc.x_mm, _rc.y_mm,
                    _rc.x_mm + _rc.larg_mm, _rc.y_mm + _rc.alt_mm,
                    base._caixas_pagina[_uid][4])
        # VICESIMUS-PRIMUS/P4: a identidade "coluna com mordida" (o
        # preço sobrepõe a foto E há texto abaixo — o Jornal) liga o
        # teto de massa do desenho da foto (uniformidade da fileira)
        _img_slot = next((r for r in slot.regioes
                          if r.tipo == TipoRegiao.IMAGEM
                          and r.visivel), None)
        if _img_slot is not None:
            _ri = rects_subst.get(_img_slot.uid) or _img_slot.rect
            # VICESIMUS-QUINTUS/L23: a mordida é SIGNIFICATIVA (≥3 mm
            # de interseção vertical) — o carimbo do Quintou tocava a
            # zona por 0,9 mm e a célula caía na identidade do Jornal
            # por acidente (o teto P4 encolhia as fotos que no
            # publicado são grandes)
            _morde = any(
                r.tipo == TipoRegiao.PRECO and r.visivel
                and (min(r.rect.y_mm + r.rect.alt_mm,
                         _ri.y_mm + _ri.alt_mm)
                     - max(r.rect.y_mm, _ri.y_mm)) >= 3.0
                and r.rect.x_mm < _ri.x_mm + _ri.larg_mm
                and r.rect.x_mm + r.rect.larg_mm > _ri.x_mm
                for r in slot.regioes)
            _abaixo = any(
                r.tipo in (TipoRegiao.NOME, TipoRegiao.SUBTITULO)
                and r.visivel
                and r.rect.y_mm >= _ri.y_mm + _ri.alt_mm - 1.0
                for r in slot.regioes)
            if _morde and _abaixo:
                if not hasattr(base, "_p4_uids"):
                    base._p4_uids = set()
                base._p4_uids.add(_img_slot.uid)
        # VICESIMUS-SEXTUS §4: A HIERARQUIA NÃO INVERTE — onde o preço
        # ENCHE um elemento de arte (L24), a razão preço÷nome nunca
        # desce de 2,2×: o corpo do NOME ganha teto pela altura REAL
        # do algarismo daquela célula; quem cede é o nome (abrevia e
        # hifeniza), nunca o preço.
        cap_nome_pt = None
        _preco_cx = next((r for r in slot.regioes
                          if r.tipo == TipoRegiao.PRECO and r.visivel
                          and getattr(r, "preenche_caixa", False)), None)
        if _preco_cx is not None and d.preco_por is not None:
            _pt_pc, _alt_pc = corpo_pela_caixa(_preco_cx, d.preco_por,
                                               dpi_ef, fontes_dir)
            if _alt_pc > 0:
                cap_nome_pt = (_alt_pc / 2.2) * 72.0 / dpi_ef
        # UNDETRICESIMUS §3: esta é célula DE PRODUTO (tem foto e nome) —
        # a validade da página não se repete aqui dentro
        base._slot_de_produto = bool(zonas_img) and any(
            r.tipo == TipoRegiao.NOME and r.visivel for r in slot.regioes)
        for reg in slot.regioes:
            novo_rect = rects_subst.get(reg.uid)
            campos: dict = {}
            if novo_rect:
                campos["rect"] = novo_rect
            # UNDEVICESIMUS §4.1: a etiqueta que CAVALGA a foto pousa
            # no canto MAIS VAZIO dela — ia sempre ao mesmo canto e
            # podia cobrir o rótulo (a Nutella, a tampa do Danone).
            # Mede a tinta JÁ PINTADA na base (a foto real, não a
            # caixa) nas duas posições e fica com a mais limpa.
            if (reg.tipo == TipoRegiao.PRECO and reg.visivel
                    and novo_rect is None):
                r_alt = _canto_mais_vazio(base, reg, slot.regioes,
                                          rects_subst, dpi_ef)
                if r_alt is not None:
                    campos["rect"] = r_alt
                # o pouso FINAL fica registrado (diagnóstico §4 da
                # VICESIMUS: folga/invasão medem-se no efetivo)
                if not hasattr(base, "_pousos"):
                    base._pousos = {}
                base._pousos[reg.uid] = r_alt or reg.rect
            if reg.tipo == TipoRegiao.NOME and reg.visivel \
                    and not (aj_nome is not None and aj_nome.piso_cedeu):
                # (piso_cedeu: sem SUBTITULO o piso cede antes da
                # tesoura — o mínimo original da região vale, Quintou)
                min_ef = min(reg.tamanho_max_pt,
                             max(reg.tamanho_min_pt, piso_nome))
                if min_ef != reg.tamanho_min_pt:
                    campos["tamanho_min_pt"] = min_ef
            if (reg.tipo == TipoRegiao.NOME and reg.visivel
                    and cap_nome_pt is not None
                    and reg.tamanho_max_pt > cap_nome_pt):
                # SEXTUS §4: o teto do nome pela hierarquia 2,2× —
                # nunca abaixo do mínimo da própria região (sanidade)
                campos["tamanho_max_pt"] = max(cap_nome_pt,
                                               reg.tamanho_min_pt)
            reg_f = _replace(reg, **campos) if campos else reg
            d_reg = d
            if reg.uid in por_zona:
                d_reg = _replace(d, imagem_path=por_zona[reg.uid],
                                 imagens=[])
            _desenhar_regiao(base, draw, reg_f, d_reg, dpi_ef, fontes_dir,
                             tem_unidade)
        # selos (+18, Qualidade) por slot, ancorados na célula — nos
        # rects EFETIVOS (o Q1 pode ter movido a zona da foto)
        selos = _selos_do_produto(d)
        if selos:
            anc = _ancora_selos_slot(
                slot, dpi_ef, w, h, rects_subst,
                com_foto=bool(d.imagem_path or d.imagens))
            # VICESIMUS §3.3: o selo é AVISO LEGAL — nunca sobre a
            # tinta do produto (o +18 pousava no gargalo do Campari).
            # Com a silhueta registrada e faixa livre ao lado, a
            # âncora desvia para o vão à direita da tinta.
            uid_img = next((r.uid for r in slot.regioes
                            if r.tipo == TipoRegiao.IMAGEM
                            and r.visivel), None)
            sil = getattr(base, "_silhuetas", {}).get(uid_img)
            if sil:
                ox, oy_sil, nw, _nh = sil
                ax, ay, aw, ah = anc
                livre = (ax + aw) - (ox + nw)
                if livre > mm_para_px(9, dpi_ef):
                    anc = (ox + nw, ay, livre, ah)
                # VICESIMUS-QUARTUS §3.6 (L22 — a irmã vertical do
                # §3.3): o selo ENCOSTA no produto — com a foto
                # ASSENTADA no chão, o canto superior da zona é vazio
                # e o selo BB flutuava solto entre as células do
                # Quintou; a âncora desce até o topo da TINTA (com um
                # respiro de 2 mm), nunca fica pendurada no nada
                ax2, ay2, aw2, ah2 = anc
                respiro = round(mm_para_px(2, dpi_ef))
                if oy_sil - respiro > ay2:
                    corte = (oy_sil - respiro) - ay2
                    anc = (ax2, ay2 + corte, aw2, max(1, ah2 - corte))
            desenhar_selos(base, anc, selos,
                           fontes_dir / "Roboto-Bold.ttf")
    return base

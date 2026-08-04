"""
Compositor — desenha os elementos dinâmicos sobre a arte de fundo
=================================================================
A arte de fundo (imagem do Illustrator) fica intocada, na camada de baixo.
Por cima, o app desenha imagem do produto, nome e preço (de/por), com Pillow,
no tamanho físico exato definido pelo LayoutDef.
"""

from __future__ import annotations

from dataclasses import dataclass, field
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
from app.rendering.text_fit import ajustar_texto
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
    # v3: os SABORES declarados viajam também COMO LISTA (não só
    # dissolvidos na prosa do descritor) — o pré-voo compara com as
    # fotos e acusa "anuncia 3 sabores, só 1 tem foto" (a Sardinha)
    sabores: tuple[str, ...] = ()


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


def texto_composto_legal(reg: "Regiao", dados: "DadosProduto | None" = None) -> str:
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
                return datas[-1]
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
    return validade


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
                nw = max(1, round(img.width * escala))
                nh = max(1, round(img.height * escala))
                img = img.resize((nw, nh))
                # §7.2 (a decisão B): região com alinhamento ESQUERDA
                # encosta a foto no eixo do texto — um eixo por coluna
                if reg.alinhamento == Alinhamento.ESQUERDA:
                    ox = x
                elif reg.alinhamento == Alinhamento.DIREITA:
                    ox = x + rw - nw
                else:
                    ox = x + (rw - nw) // 2
                oy = y + rh - nh              # o produto assenta
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
        camada = compor_imagens([im for _, im in pares], rw, rh, dados.modo_arranjo)

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
    x, y, rw, rh = _rect_px(reg.rect, dpi)
    aj = ajustar_texto(
        texto, fontes_dir / reg.fonte, rw, rh, reg.tamanho_max_pt, dpi,
        reg.tamanho_min_pt, sem_hifen=reg.sem_hifen   # F13-BIS/T5
    )
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
        sil_y1 = (oy + nh) / px_por_mm
        larg_sil = sil_x1 - sil_x0
        cel_x1 = r_img.x_mm + r_img.larg_mm
        # a base da etiqueta fica onde a arte mandou (o bloco de
        # texto vem logo abaixo); só o X e a MORDIDA mudam
        if rp.larg_mm > 0.45 * larg_sil:
            # AO LADO da silhueta (garrafa/caixinha) — se couber
            x_lado = sil_x1 + 0.8
            if x_lado + rp.larg_mm <= cel_x1 + 2.0:
                return Retangulo(min(x_lado, cel_x1 + 2.0 - rp.larg_mm),
                                 rp.y_mm, rp.larg_mm, rp.alt_mm)
            # não coube ao lado: morde o canto mesmo assim (mínimo
            # de invasão que o canto permite)
            x_novo = min(sil_x1 - 0.25 * rp.larg_mm,
                         cel_x1 - rp.larg_mm + 2.0)
            return Retangulo(x_novo, rp.y_mm, rp.larg_mm, rp.alt_mm)
        # produto LARGO: morde o canto inf-dir (~40% sobre a tinta —
        # invasão ≈ 40%×45% ≈ 18% da largura, longe do centro)
        x_novo = min(sil_x1 - 0.4 * rp.larg_mm,
                     cel_x1 - rp.larg_mm + 2.0)
        if abs(x_novo - rp.x_mm) < 0.5:
            return None
        return Retangulo(x_novo, rp.y_mm, rp.larg_mm, rp.alt_mm)

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

    f_g, f_p, w_prefixo, w_reais, w_cent = montar(pt_grande, pt_peq)
    total_w = w_prefixo + w_reais + w_cent
    asc_g = f_g.getmetrics()[0]
    alt_g = sum(f_g.getmetrics())

    # Só REDUZ para caber na largura e na altura.
    escala = min(1.0, rw / total_w if total_w else 1.0, rh / alt_g if alt_g else 1.0)
    if escala < 1.0:
        f_g, f_p, w_prefixo, w_reais, w_cent = montar(pt_grande * escala, pt_peq * escala)
        total_w = w_prefixo + w_reais + w_cent
        asc_g = f_g.getmetrics()[0]
        alt_g = sum(f_g.getmetrics())

    asc_p = f_p.getmetrics()[0]
    cursor = _x_alinhado(x, rw, total_w, reg.alinhamento)
    x0 = cursor                                            # início (p/ o riscado)
    baseline = y + (rh + alt_g) / 2 - f_g.getmetrics()[1]  # centraliza vertical

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
        texto = texto_composto_legal(reg, dados)
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
                                      marcas=d.marcas_nome)
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
            if reg.tipo == TipoRegiao.NOME and reg.visivel \
                    and not (aj_nome is not None and aj_nome.piso_cedeu):
                # (piso_cedeu: sem SUBTITULO o piso cede antes da
                # tesoura — o mínimo original da região vale, Quintou)
                min_ef = min(reg.tamanho_max_pt,
                             max(reg.tamanho_min_pt, piso_nome))
                if min_ef != reg.tamanho_min_pt:
                    campos["tamanho_min_pt"] = min_ef
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
            desenhar_selos(base,
                           _ancora_selos_slot(
                               slot, dpi_ef, w, h, rects_subst,
                               com_foto=bool(d.imagem_path or d.imagens)),
                           selos, fontes_dir / "Roboto-Bold.ttf")
    return base

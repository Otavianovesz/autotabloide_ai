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
        return validade or fixo
    if papel == PapelTexto.OBSERVACAO:
        # R-071: a observação do item; condicional — vazia devolve "" (a região
        # não desenha nada). Cai no texto_fixo só se o item não tiver observação
        # (permite uma observação "de layout" fixa sem depender do item).
        obs = (dados.observacao if dados is not None else None) or ""
        return obs or fixo
    if papel == PapelTexto.DESCONTO:
        # R-109: "-XX%" CALCULADO de (de−por)/de — condicional (sem "de" ou
        # sem desconto real, a região não pinta). Nunca digitado.
        pct = percentual_desconto(
            dados.preco_de if dados is not None else None,
            dados.preco_por if dados is not None else None)
        return f"-{pct}%" if pct else ""
    return fixo or validade


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
            # 1 imagem, sem forma nem enquadramento: caminho da F2, byte-idêntico
            if reg.ajuste == Ajuste.PREENCHER:
                escala = max(rw / img.width, rh / img.height)
            else:
                escala = min(rw / img.width, rh / img.height)
            nw, nh = max(1, round(img.width * escala)), max(1, round(img.height * escala))
            img = img.resize((nw, nh))
            base.paste(img, (x + (rw - nw) // 2, y + (rh - nh) // 2), img)
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
        texto, fontes_dir / reg.fonte, rw, rh, reg.tamanho_max_pt, dpi, reg.tamanho_min_pt
    )
    total_h = aj.altura_linha_px * len(aj.linhas)
    oy = y + max(0, (rh - total_h) // 2)  # centraliza o bloco na vertical

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
    if reg.papel_preco != PapelPreco.DE and dados.multi_preco:
        _desenhar_texto(base, draw, reg, dados.multi_preco, dpi, fontes_dir)
        return

    valor = dados.preco_de if reg.papel_preco == PapelPreco.DE else dados.preco_por
    if valor is None:
        return

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

    if prefixo:
        draw.text((cursor, baseline), prefixo, font=f_p, fill=reg.cor, anchor="ls")
    cursor += w_prefixo
    draw.text((cursor, baseline), reais, font=f_g, fill=reg.cor, anchor="ls")
    cursor += w_reais
    # centavos alinhados ao topo do número grande (sobrescrito)
    baseline_cent = baseline - (asc_g - asc_p)
    draw.text((cursor, baseline_cent), "," + centavos, font=f_p, fill=reg.cor, anchor="ls")

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


def _desenhar_regiao_reta(base, draw, reg, dados, dpi, fontes_dir,
                          tem_regiao_unidade):
    if reg.tipo == TipoRegiao.IMAGEM:
        _desenhar_imagem(base, reg, dados, dpi)
    elif reg.tipo == TipoRegiao.NOME:
        texto = nome_com_unidade(dados.nome, dados.unidade, tem_regiao_unidade)
        _desenhar_texto(base, draw, reg, texto, dpi, fontes_dir)
    elif reg.tipo == TipoRegiao.UNIDADE:
        _desenhar_texto(base, draw, reg, dados.unidade or "", dpi, fontes_dir)
    elif reg.tipo == TipoRegiao.PRECO:
        _desenhar_preco(base, draw, reg, dados, dpi, fontes_dir)
    elif reg.tipo == TipoRegiao.TEXTO_LEGAL:
        # RG-57: o PAPEL da região decide o texto (validade viva, dica da IA,
        # aviso do preset, ou o livre) — fonte única com a prévia do editor.
        _desenhar_texto(base, draw, reg,
                        texto_composto_legal(reg, dados),
                        dpi, fontes_dir)
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


def _ancora_selos_slot(slot, dpi: int, w: int, h: int) -> tuple[int, int, int, int]:
    """Onde os selos do slot se ancoram: [SELO] > [IMAGEM] do slot > página."""
    selo_rect = imagem_rect = None
    for reg in slot.regioes:
        if reg.tipo == TipoRegiao.SELO and selo_rect is None:
            selo_rect = reg.rect
        elif reg.tipo == TipoRegiao.IMAGEM and imagem_rect is None:
            imagem_rect = reg.rect
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


def compor_pagina(
    layout: LayoutDef,
    pagina: Pagina,
    dados: "DadosProduto | list[DadosProduto]",
    fontes_dir: str | Path | None = None,
    fundo_path: str | Path | None = None,
) -> Image.Image:
    """Compõe uma página e devolve a imagem.

    ``dados`` pode ser um DadosProduto (mesmo produto em todos os slots) ou uma
    LISTA de DadosProduto (um por slot — o tabloide de vários produtos).
    """
    fontes_dir = Path(fontes_dir) if fontes_dir else SystemRoot().fontes
    w = round(mm_para_px(layout.largura_mm, layout.dpi))
    h = round(mm_para_px(layout.altura_mm, layout.dpi))

    # D8.2: prioridade explícita > arte DA PÁGINA > arte do layout (legado)
    fundo = fundo_path or pagina.arquivo_fundo or layout.arquivo_fundo
    if fundo and Path(fundo).exists():
        base = Image.open(fundo).convert("RGB")
        if base.size != (w, h):
            base = base.resize((w, h))
    else:
        base = Image.new("RGB", (w, h), "white")

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
            desenhar_secoes(base, secoes, layout.dpi, cor=cor,
                            espessura_mm=esp, fontes_dir=fontes_dir,
                            estilo=estilo, cores_por_categoria=por_cat)

    draw = ImageDraw.Draw(base)
    for i, slot in enumerate(pagina.slots):
        d = _dados_do_slot(dados, lista, i, slot_id=slot.id)
        if d is None:
            # célula sem produto fica com a arte — MAS texto fixo do layout
            # ("Fica a Dica") desenha mesmo assim (A1 da ORDEM_F5_8);
            # via _desenhar_regiao p/ a rotação valer também aqui (RG-12).
            # RG-57: a decisão "tem o que desenhar?" passa pelo mesmo helper de
            # papel (byte-idêntico ao legado, que era todo LIVRE).
            vazio = DadosProduto("")
            for reg in slot.regioes:
                if (reg.visivel and reg.tipo == TipoRegiao.TEXTO_LEGAL
                        and texto_composto_legal(reg, vazio)):
                    _desenhar_regiao(base, draw, reg, vazio,
                                     layout.dpi, fontes_dir, False)
            continue
        tem_unidade = any(r.tipo == TipoRegiao.UNIDADE and r.visivel for r in slot.regioes)
        for reg in slot.regioes:
            _desenhar_regiao(base, draw, reg, d, layout.dpi, fontes_dir, tem_unidade)
        # selos (+18, Qualidade) por slot, ancorados na célula
        selos = _selos_do_produto(d)
        if selos:
            desenhar_selos(base, _ancora_selos_slot(slot, layout.dpi, w, h), selos,
                           fontes_dir / "Roboto-Bold.ttf")
    return base

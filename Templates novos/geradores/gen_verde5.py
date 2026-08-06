# -*- coding: utf-8 -*-
"""Sexta Verde v5 GALA (bancas retas) — rótulo de caixa de fruta com toldos, bilhete numerado, raminhos e texturas."""
import base64, os

W, H = 1080, 1440
CREAMBG = '#F5EFDE'
CREAM2  = '#F8F1E0'
GREEN   = '#1E4D33'
GREEND  = '#123526'
CORAL   = '#D6543C'
CORALD  = '#B8432F'
MUST    = '#DFA637'
TINT    = '#E9EBD6'
INKF    = '#123526'
MUTE    = '#6E7A63'
SLOTC   = '#A9B49B'

_RAIZ = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')  # F8/N-08: raiz do pacote
logo_b64 = base64.b64encode(open(os.path.join(_RAIZ, 'brand', 'logo_semfundo.png'), 'rb').read()).decode()

def txt(x, y, s, ff='Archivo', fw='500', fs=16, fill=GREEN, anchor='start', ls=None, style=None, rot=None):
    if ' ' in ff and not ff.startswith("'"):
        ff = f"'{ff}'"
    a  = f' letter-spacing="{ls}"' if ls else ''
    a += f' font-style="{style}"' if style else ''
    a += f' transform="rotate({rot} {x} {y})"' if rot is not None else ''
    return (f'<text x="{x}" y="{y}" text-anchor="{anchor}" font-family="{ff}" font-weight="{fw}" '
            f'font-size="{fs}" fill="{fill}"{a}>{s}</text>')

def folha(x, y, s=1.0, rot=0, fill=GREEN, sw=2.4, op=1.0):
    return (f'<g transform="translate({x} {y}) rotate({rot}) scale({s})" opacity="{op}">'
            f'<path d="M0 0 Q20 -18 44 0 Q20 18 0 0 Z" fill="none" stroke="{fill}" stroke-width="{sw}" stroke-linejoin="round"/>'
            f'<path d="M4 0 H38" fill="none" stroke="{fill}" stroke-width="{sw*0.8}" stroke-linecap="round"/></g>')

def raminho(x, y, rot):
    """Raminho de canto: talo com 2 folhas e 3 frutinhas."""
    return (f'<g transform="translate({x} {y}) rotate({rot})">'
            f'<path d="M0 0 Q18 -4 34 -14" fill="none" stroke="{GREEN}" stroke-width="2.2" stroke-linecap="round"/>'
            + folha(6, -4, 0.34, rot=-38) + folha(18, -8, 0.30, rot=-6)
            + f'<circle cx="34" cy="-16" r="3.2" fill="{CORAL}"/><circle cx="40" cy="-10" r="2.5" fill="{CORAL}"/>'
            f'<circle cx="39" cy="-19" r="2.2" fill="{MUST}"/></g>')

# ---------- fundo com textura ----------
defs = f'''<defs>
<pattern id="pontinhos" width="26" height="26" patternUnits="userSpaceOnUse">
  <circle cx="13" cy="13" r="1" fill="{GREEN}"/>
</pattern>
<pattern id="listras" width="12" height="12" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">
  <rect width="6" height="12" fill="{CORAL}" opacity="0.35"/>
</pattern>
<clipPath id="topoclip"><rect x="48" y="48" width="984" height="322"/></clipPath>
</defs>'''

# raios vintage atrás do título
import math as _m
_rays = []
for k in range(36):
    a0 = _m.radians(k*10); a1 = _m.radians(k*10+5)
    x0, y0 = 540+680*_m.cos(a0), 250-680*_m.sin(a0)
    x1, y1 = 540+680*_m.cos(a1), 250-680*_m.sin(a1)
    _rays.append(f'<path d="M540 250 L{x0:.0f} {y0:.0f} L{x1:.0f} {y1:.0f} Z" fill="#EDE4CB" opacity="0.55"/>')
raios = '<g id="raios-vintage" clip-path="url(#topoclip)">' + ''.join(_rays) + '</g>'

fundo = (f'<g id="fundo"><rect width="{W}" height="{H}" fill="{CREAMBG}"/>'
         f'<rect width="{W}" height="{H}" fill="url(#pontinhos)" opacity="0.05"/></g>')

moldura = ('<g id="moldura">'
    f'<path d="M30 30 H{W-30} V{H-148} H30 Z M46 46 H{W-46} V{H-164} H46 Z" fill-rule="evenodd" fill="url(#listras)"/>'
    f'<rect x="28" y="28" width="{W-56}" height="{H-56-118}" fill="none" stroke="{GREEN}" stroke-width="2.4"/>'
    f'<rect x="46" y="46" width="{W-92}" height="{H-92-118}" fill="none" stroke="{GREEN}" stroke-width="1.1" opacity="0.6"/>'
    + raminho(72, 78, 10)
    + f'<g transform="translate({W-72} 78) scale(-1 1)">' + raminho(0, 0, 10) + '</g>'
    + '</g>')

# ---------- cabeçalho ----------
arc = f'''<path id="arcotopo" d="M 240 152 A 800 800 0 0 1 840 152" fill="none"/>
<text font-family="Archivo" font-weight="700" font-size="19" fill="{CORAL}" letter-spacing="7">
  <textPath href="#arcotopo" startOffset="50%" text-anchor="middle">BELO BRASIL SUPERMERCADOS</textPath>
</text>'''

titulo = f'''<g id="titulo">
{arc}
<text x="546" y="272" text-anchor="middle" font-family="Fraunces" font-weight="600" font-size="168" fill="{GREEND}" opacity="0.9" transform="translate(5 5)">VERDE</text>
<text x="546" y="272" text-anchor="middle" font-family="Fraunces" font-weight="600" font-size="168" fill="{GREEN}">VERDE</text>
<text x="546" y="272" text-anchor="middle" font-family="Fraunces" font-weight="600" font-size="168" fill="none" stroke="{CREAMBG}" stroke-width="1.3" opacity="0.85">VERDE</text>
<g id="banderola-sexta" transform="translate(330 134) rotate(-7)">
  <path d="M4 60 L190 64 L188 4 L2 0 L17 30 Z" fill="{CORALD}" transform="translate(3 4)" opacity="0.5"/>
  <path d="M0 0 H186 L172 28 L186 56 H0 L14 28 Z" fill="{CORAL}"/>
  <path d="M0 0 H186 L172 28 L186 56 H0 L14 28 Z" fill="none" stroke="{GREEND}" stroke-width="1.4" opacity="0.35"/>
  <text x="97" y="41" text-anchor="middle" font-family="Caveat" font-weight="700" font-size="50" fill="#FDF6E9">Sexta</text>
</g>
</g>'''

ribbon = f'''<g id="fita">
<path d="M292 300 L238 300 L262 327 L238 354 L292 354 Z" fill="{CORALD}"/>
<path d="M788 300 L842 300 L818 327 L842 354 L788 354 Z" fill="{CORALD}"/>
<path d="M292 354 L292 366 L310 354 Z" fill="{GREEND}"/>
<path d="M788 354 L788 366 L770 354 Z" fill="{GREEND}"/>
<rect x="292" y="294" width="496" height="60" fill="{CORAL}"/>
{txt(540, 331, 'HORTIFRÚTI FRESQUINHO · TODA SEXTA-FEIRA', ff='Archivo', fw='700', fs=17, fill='#FDF6E9', anchor='middle', ls=3)}
</g>'''

ticket = f'''<g id="bilhete-data" transform="translate(934 140) rotate(-6)">
<rect x="-78" y="-45" width="156" height="90" rx="10" fill="{CORAL}"/>
<circle cx="-78" cy="0" r="8" fill="{CREAMBG}"/>
<circle cx="78" cy="0" r="8" fill="{CREAMBG}"/>
<line x1="34" y1="-37" x2="34" y2="37" stroke="{CREAMBG}" stroke-width="2" stroke-dasharray="4 6"/>
<text x="-22" y="-27" text-anchor="middle" font-family="Archivo" font-weight="700" font-size="8.5" fill="#F4C9BC" letter-spacing="2">BILHETE Nº 031</text>
<text x="52" y="5" text-anchor="middle" font-family="Archivo" font-weight="700" font-size="11" fill="#FDF6E9" letter-spacing="1" transform="rotate(-90 52 3)">SÓ HOJE</text>
</g>'''
ticket_ex = f'''<g transform="translate(934 140) rotate(-6)">
<text x="-22" y="17" text-anchor="middle" font-family="Fraunces" font-weight="600" font-size="38" fill="#FDF6E9">31/07</text>
</g>'''

# ---------- barraquinhas de feira (retas, com toldo de beiral) ----------
AX1, AX2, AW, AY, AH = 54, 566, 460, 380, 348

def toldo_reto(x, y, w):
    """Toldo listrado com beiral saliente, cumeeira e barrado ondulado."""
    ox, ow = x-12, w+24          # beiral p/ fora da banca
    stripes = []
    n = 13
    sw_ = ow/n
    for i in range(n):
        cor = CORAL if i % 2 == 0 else '#F8EFDD'
        stripes.append(f'<rect x="{ox+i*sw_}" y="{y+26}" width="{sw_+0.5}" height="46" fill="{cor}"/>')
        stripes.append(f'<circle cx="{ox+i*sw_+sw_/2}" cy="{y+72}" r="{sw_/2}" fill="{cor}"/>')
    return (''.join(stripes)
            + f'<rect x="{ox}" y="{y+20}" width="{ow}" height="8" rx="4" fill="{GREEND}"/>')

def arco(x, y, w, h, idx):
    return (f'<g id="celula-banca-{idx}">'
            f'<rect x="{x}" y="{y+40}" width="{w}" height="{h-40}" rx="5" fill="{GREEN}"/>'
            f'<rect x="{x+13}" y="{y+92}" width="{w-26}" height="{h-40-105}" rx="4" fill="none" stroke="{CREAMBG}" stroke-width="1.6" opacity="0.6"/>'
            + toldo_reto(x, y, w) +
            f'</g>')

def tag_pendurada(cx, cy, rot):
    return (f'<g class="tag" transform="translate({cx} {cy}) rotate({rot})">'
            f'<path d="M-36 -42 Q-30 -56 -24 -42" fill="none" stroke="{GREEND}" stroke-width="2.4"/>'
            f'<ellipse cx="0" cy="0" rx="82" ry="44" fill="#FDF6E9" stroke="{CORAL}" stroke-width="3"/>'
            f'<ellipse cx="0" cy="0" rx="74" ry="37" fill="none" stroke="{CORAL}" stroke-width="1" opacity="0.6"/>'
            f'<circle cx="-30" cy="-28" r="4" fill="none" stroke="{GREEND}" stroke-width="2.2"/>'
            f'</g>')

arcos = ('<g id="bancas-destaque">' + arco(AX1, AY, AW, AH, 1) + arco(AX2, AY, AW, AH, 2)
         + tag_pendurada(AX1+AW/2, AY+AH, -5) + tag_pendurada(AX2+AW/2, AY+AH, 4) + '</g>')

ARCO_ITENS = [
    (['Ovo Branco Mantiqueira'], 'bandeja com 30 unidades', ('19',',99'), '★ DIRETO DA GRANJA ★', -5),
    (['Uva Vitória'], 'bandeja 450 g · sem semente', ('8',',88'), '★ COLHEITA DA SEMANA ★', 4),
]

def arco_ex(x, y, w, h, item):
    nls, sub, (pv, pc), label, rot = item
    cx = x+w/2
    out = []
    out.append(f'<rect x="{x+36}" y="{y+106}" width="{w-72}" height="{h-256}" rx="10" '
               f'fill="#FFFFFF" fill-opacity="0.06" stroke="{SLOTC}" stroke-width="2" stroke-dasharray="9 8"/>')
    sy = y+106+(h-256)/2
    out.append(f'<g transform="translate({cx-14} {sy-22})" fill="none" stroke="#C8D3BC" stroke-width="2.2" stroke-linecap="round" opacity="0.9">'
               f'<rect x="3" y="8" width="22" height="15" rx="3"/><circle cx="14" cy="15" r="4.5"/><path d="M10 8l2-4h5L19 8"/></g>')
    out.append(txt(cx, sy+14, 'foto do produto', ff='Archivo', fw='500', fs=12.5, fill='#C8D3BC', anchor='middle'))
    out.append(txt(cx, y+h-122, label, ff='Archivo', fw='700', fs=13, fill=MUST, anchor='middle', ls=3))
    out.append(txt(cx, y+h-88, nls[0], ff='Fraunces', fw='600', fs=27, fill='#FDF6E9', anchor='middle'))
    out.append(txt(cx, y+h-62, sub, ff='Fraunces', fw='400', fs=14, fill='#BFD3C2', anchor='middle', style='italic'))
    out.append(f'<g transform="translate({cx} {y+h}) rotate({rot})">'
               f'<text x="0" y="12" text-anchor="middle" font-family="Fraunces" font-weight="600" font-size="38" fill="{CORAL}">'
               f'<tspan font-size="17" fill="{MUTE}">R$ </tspan>{pv}<tspan font-size="24">{pc}</tspan></text></g>')
    return ''.join(out)

# ---------- patchwork ----------
PY, PH, PGAP = 782, 162, 12
PW = 316
PXS = [54, 54+PW+PGAP, 54+2*(PW+PGAP)]
PATCH_ITENS = [
    (['Tomate Salada', 'e Itália'], 'kg', ('4',',94'), -2),
    (['Brócolis', 'Ninja'], 'unidade', ('7',',88'), 2),
    (['Maçã Fuji', 'e Gala'], 'kg', ('11',',91'), -1.5),
    (['Caqui', 'Fuiu'], 'kg', ('11',',91'), 2.5),
    (['Cebola', 'Extra'], 'kg', ('6',',44'), -2),
    (['Limão', 'Taiti'], 'kg', ('2',',90'), 1.5),
    (['Murcot'], 'kg', ('6',',66'), -2.5),
    (['Batata', 'Noiva'], 'kg', ('6',',69'), 2),
    (['Cenoura', 'Top'], 'kg', ('7',',22'), -1.5),
]

def patch_cell(x, y, w, h, idx, dark, rot_leaf):
    fill = TINT if dark else '#FBF7EA'
    tick = 9
    cant = ''.join(
        f'<path d="M{cx0} {cy0+t1} L{cx0} {cy0} L{cx0+t0} {cy0}" fill="none" stroke="{GREEN}" stroke-width="1.6" opacity="0.6"/>'
        for cx0, cy0, t0, t1 in [(x+10, y+10, tick, tick), (x+w-10, y+10, -tick, tick),
                                 (x+10, y+h-10, tick, -tick), (x+w-10, y+h-10, -tick, -tick)])
    return (f'<g id="celula-{idx}">'
            f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{fill}" stroke="{GREEN}" stroke-width="1.8"/>'
            f'<rect x="{x+6}" y="{y+6}" width="{w-12}" height="{h-12}" fill="none" stroke="{GREEN}" stroke-width="0.8" opacity="0.35"/>'
            + cant
            + folha(x+w-54, y+h-26, 0.44, rot=rot_leaf, fill=GREEN, op=0.13)
            # TRICESIMUS-PRIMUS §2: o "LOTE 01..09" SAIU. A tabela do dono
            # nao tem lote nenhum — era rotulo decorativo que o app criou,
            # e num encarte de hortifruti "lote" sugere ao cliente
            # quantidade limitada, coisa que ele nao prometeu. Numeracao
            # decorativa nunca inventa informacao comercial.
            + f'</g>')

patch = ['<g id="patchwork">']
k = 0
for r in range(3):
    for c in range(3):
        x = PXS[c]; y = PY + r*(PH+PGAP)
        patch.append(patch_cell(x, y, PW, PH, k+3, (r+c) % 2 == 0, -25 + 17*k))
        k += 1
patch.append('</g>')
patch = ''.join(patch)

def patch_ex(x, y, w, h, item):
    nls, sub, (pv, pc), rot = item
    out = []
    out.append(f'<rect x="{x+14}" y="{y+14}" width="120" height="{h-28}" rx="8" fill="#FFFFFF" fill-opacity="0.4" '
               f'stroke="{SLOTC}" stroke-width="2" stroke-dasharray="7 7"/>')
    out.append(f'<g transform="translate({x+60} {y+h/2-16})" fill="none" stroke="{SLOTC}" stroke-width="2.2" stroke-linecap="round">'
               f'<rect x="3" y="8" width="22" height="15" rx="3"/><circle cx="14" cy="15" r="4.5"/><path d="M10 8l2-4h5L19 8"/></g>')
    tx = x+152
    for j, n in enumerate(nls):
        out.append(txt(tx, y+46+j*25, n, ff='Fraunces', fw='600', fs=20, fill=INKF))
    out.append(txt(tx, y+46+len(nls)*25, sub, ff='Fraunces', fw='400', fs=13.5, fill=MUTE, style='italic'))
    tgx, tgy = x+w-86, y+h-36
    out.append(f'<g transform="translate({tgx} {tgy}) rotate({rot})">'
               f'<rect x="-60" y="-23" width="120" height="46" rx="8" fill="{CORAL}"/>'
               f'<text x="0" y="9" text-anchor="middle" font-family="Fraunces" font-weight="600" font-size="26" fill="#FDF6E9">'
               f'<tspan font-size="12.5" opacity="0.85">R$ </tspan>{pv}<tspan font-size="17">{pc}</tspan></text></g>')
    return ''.join(out)

# ---------- guirlanda com frutinhas ----------
gu = []
for i in range(8):
    gx = 400 + i*36
    gu.append(folha(gx, 366 + (4 if i % 2 else 0), 0.30, rot=(16 if i % 2 else -16)))
    if i < 7:
        gu.append(f'<circle cx="{gx+30}" cy="{370 if i % 2 else 366}" r="2.2" fill="{CORAL}"/>')
guirlanda = ('<g id="guirlanda">' + ''.join(gu)
    + f'<circle cx="388" cy="368" r="3" fill="{CORAL}"/><circle cx="694" cy="368" r="3" fill="{CORAL}"/></g>')

# ---------- rodapé ----------
lw = 168; lh = round(lw*625/1218)
foot = f'''<g id="rodape">
<rect x="0" y="1322" width="{W}" height="118" fill="{GREEND}"/>
<line x1="0" y1="1322" x2="{W}" y2="1322" stroke="{MUST}" stroke-width="1.4" opacity="0.7"/>
<image x="46" y="{1322+(118-lh)//2}" width="{lw}" height="{lh}" href="data:image/png;base64,{logo_b64}"/>
<text x="238" y="1366" font-family="Archivo" font-weight="500" font-size="13.5" fill="#C9D4C0"><tspan fill="{MUST}" font-weight="700">Ofertas válidas somente na sexta-feira, 31/07,</tspan> ou enquanto durarem os estoques</text>
<text x="238" y="1390" font-family="Archivo" font-weight="500" font-size="13.5" fill="#C9D4C0">Imagens meramente ilustrativas • Av. Brasília, 319 – Campo Verde/MT</text>
<text x="238" y="1414" font-family="Archivo" font-weight="500" font-size="13.5" fill="#C9D4C0">✆ (66) 9969-4009 • @belobrasilsupermercado</text>
<text x="948" y="1398" text-anchor="middle" font-family="Caveat" font-weight="700" font-size="40" fill="{MUST}" transform="rotate(-2 948 1390)">Se é B, é show!</text>
</g>'''

HEAD = f'''<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink"
 width="{W}" height="{H}" viewBox="0 0 {W} {H}" font-kerning="normal">
<title>Sexta Verde — Belo Brasil (rótulo de caixa de fruta, definitiva)</title>
{defs}'''

estrutura = fundo + raios + moldura + titulo + ribbon + ticket + guirlanda + arcos + patch

ex = ['<g id="conteudo-exemplo">', ticket_ex]
ex.append(arco_ex(AX1, AY, AW, AH, ARCO_ITENS[0]))
ex.append(arco_ex(AX2, AY, AW, AH, ARCO_ITENS[1]))
k = 0
for r in range(3):
    for c in range(3):
        x = PXS[c]; y = PY + r*(PH+PGAP)
        ex.append(patch_ex(x, y, PW, PH, PATCH_ITENS[k]))
        k += 1
ex.append('</g>')
exemplo = ''.join(ex)

master = HEAD + estrutura + foot + exemplo + '</svg>'
base = HEAD + estrutura + foot.replace('sexta-feira, 31/07,', 'sexta-feira') + '</svg>'

_SAIDA = os.path.join(_RAIZ, 'artes', 'sexta-verde')
os.makedirs(_SAIDA, exist_ok=True)
open(os.path.join(_SAIDA, 'sexta-verde-MASTER.svg'), 'w', encoding='utf-8').write(master)
open(os.path.join(_SAIDA, 'sexta-verde-BASE.svg'), 'w', encoding='utf-8').write(base)
print('svg ok')

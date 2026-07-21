"""
Seções visuais por categoria (F8.2) — contorno + título
=======================================================
O visual da visão original: um contorno arredondado (azul, por padrão)
abraçando as células da mesma categoria, com o título ("Limpeza") no topo.

**A 3ª aplicação da lei do tipo novo, resolvida POR CONSTRUÇÃO:** a seção é
DECORATIVA e vive como camada DERIVADA — recalculada do mapa+categorias a
cada composição. Ela NUNCA vira slot nem região: o "ocupável" e o pré-voo
nem sabem que ela existe (e há teste provando que layout com seções não
consome item nem gera aviso falso). A página guarda só o liga/desliga e os
títulos editados (`Pagina.secoes_ligadas` / `titulos_secoes`).

Desenho: as seções entram DEPOIS do fundo e ANTES do conteúdo — o contorno
corre pela folga entre as células e jamais cobre o trio imagem×nome×preço
(o adversarial B4 amostra os pixels para provar).
"""

from __future__ import annotations

from dataclasses import dataclass, field

from app.rendering.model import Pagina, Retangulo

COR_PADRAO = "#1D4ED8"          # o azul da visão
ESPESSURA_PADRAO_MM = 0.8
MARGEM_MM = 1.0                 # folga do contorno (RG-31: 1.6 invadia a
                                # folga da célula vizinha nas artes reais)
RAIO_MM = 2.5
TITULO_PT = 11.0

# RG-31: os ESTILOS de seção ("a borda atual: feia") — modo global na Config
ESTILOS_SECAO = ("CONTORNO", "SO_TITULO", "PILL", "SEM_DESENHO")
ESTILO_PADRAO = "CONTORNO"

# paleta fixa p/ "cor por categoria" (determinística por nome — a MESMA
# categoria tem a MESMA cor em toda composição/reabertura)
PALETA_CATEGORIAS = ["#1D4ED8", "#0F766E", "#B45309", "#7C3AED", "#BE185D",
                     "#166534", "#B91C1C", "#0E7490", "#A16207", "#4338CA"]


def cor_da_categoria(categoria: str) -> str:
    """Cor estável por categoria (crc32 — determinístico entre sessões;
    o hash() do Python é salgado por processo e mudaria a cada abertura)."""
    import zlib
    chave = zlib.crc32((categoria or "Outros").lower().encode("utf-8"))
    return PALETA_CATEGORIAS[chave % len(PALETA_CATEGORIAS)]


@dataclass
class Secao:
    """Um bloco contíguo de células da MESMA categoria (já em sub-retângulos)."""

    categoria: str
    titulo: str
    retangulos: list[Retangulo] = field(default_factory=list)  # 1 por linha
    n_celulas: int = 0        # RG-49: run de 1 célula não ganha caixa (passo 36)


def _bbox_slot(slot) -> Retangulo | None:
    """A caixa da célula = união dos retângulos das regiões dela."""
    if not slot.regioes:
        return None
    x0 = min(r.rect.x_mm for r in slot.regioes)
    y0 = min(r.rect.y_mm for r in slot.regioes)
    x1 = max(r.rect.x_mm + r.rect.larg_mm for r in slot.regioes)
    y1 = max(r.rect.y_mm + r.rect.alt_mm for r in slot.regioes)
    return Retangulo(x0, y0, x1 - x0, y1 - y0)


def _uniao(caixas: list[Retangulo]) -> Retangulo:
    x0 = min(c.x_mm for c in caixas)
    y0 = min(c.y_mm for c in caixas)
    x1 = max(c.x_mm + c.larg_mm for c in caixas)
    y1 = max(c.y_mm + c.alt_mm for c in caixas)
    return Retangulo(x0, y0, x1 - x0, y1 - y0)


def _contorno_uniao(draw, rects_px, cor, esp: int, raio: int) -> None:
    """RG-49 (passos 34-35): UM contorno de união externo para as N linhas
    da seção — SEM borda entre linhas irmãs. Recebe os sub-retângulos por
    linha (px), já em ordem visual (topo→base).

    - fecha os vãos verticais entre linhas contíguas (o ponto médio vira a
      fronteira compartilhada — o traço da divisória some);
    - mesma largura em todas as linhas → 1 retângulo arredondado (cantos
      lisos da visão);
    - larguras diferentes (última linha com menos células) → o PERÍMETRO
      externo ortogonal (staircase), sem nenhum segmento horizontal interno.
    """
    rs = [list(r) for r in rects_px]                 # cópias mutáveis
    # fecha os vãos: fronteira compartilhada = ponto médio entre as linhas
    for i in range(len(rs) - 1):
        meio = (rs[i][3] + rs[i + 1][1]) / 2.0
        rs[i][3] = meio
        rs[i + 1][1] = meio
    xs0 = [r[0] for r in rs]
    xs1 = [r[2] for r in rs]
    mesma_largura = (max(xs0) - min(xs0) <= 1) and (max(xs1) - min(xs1) <= 1)
    if len(rs) == 1 or mesma_largura:
        x0, y0 = min(xs0), rs[0][1]
        x1, y1 = max(xs1), rs[-1][3]
        draw.rounded_rectangle((x0, y0, x1, y1), radius=raio,
                               outline=cor, width=esp)
        return
    # perímetro ortogonal (linhas de larguras diferentes): desce pela
    # direita com degraus, atravessa a base, sobe pela esquerda com degraus
    pontos = []
    for i, r in enumerate(rs):                       # lado DIREITO (topo→base)
        pontos.append((r[2], r[1]))                  # canto sup-dir da linha
        pontos.append((r[2], r[3]))                  # desce até a base da linha
    for r in reversed(rs):                           # lado ESQUERDO (base→topo)
        pontos.append((r[0], r[3]))                  # canto inf-esq da linha
        pontos.append((r[0], r[1]))                  # sobe até o topo da linha
    pontos.append(pontos[0])                         # fecha o polígono
    draw.line(pontos, fill=cor, width=esp, joint="curve")


def calcular_secoes(pagina: Pagina,
                    categorias_por_slot: dict[str, str | None]) -> list[Secao]:
    """Runs de células CONTÍGUAS (ordem visual) com a mesma categoria.

    Célula sem item (fora do dicionário) quebra o run. Sem categoria =
    "Outros". Run que atravessa quebra de linha vira um sub-retângulo por
    linha — célula não-retangular não quebra o desenho (B1).
    """
    from app.rendering.grade import ocupaveis, ordenar_slots_visualmente

    ordenados = ocupaveis(ordenar_slots_visualmente(pagina.slots))
    runs: list[tuple[str, list]] = []          # (categoria, [slots])
    for slot in ordenados:
        if slot.id not in categorias_por_slot:
            runs.append(("", []))              # célula vazia quebra o run
            continue
        cat = (categorias_por_slot[slot.id] or "").strip() or "Outros"
        if runs and runs[-1][0] == cat and runs[-1][1]:
            runs[-1][1].append(slot)
        else:
            runs.append((cat, [slot]))

    secoes: list[Secao] = []
    for cat, slots in runs:
        if not slots:
            continue
        caixas = [b for b in (_bbox_slot(s) for s in slots) if b is not None]
        if not caixas:
            continue
        # sub-retângulo POR LINHA — RG-31: a "mesma linha" agora é por
        # SOBREPOSIÇÃO VERTICAL dos intervalos (o topo±2mm quebrava em grade
        # real com regiões de alturas diferentes e a união saía atravessando
        # células — a captura da Mesa com o Quintou)
        def _mesma_linha(a: Retangulo, b: Retangulo) -> bool:
            topo = max(a.y_mm, b.y_mm)
            base = min(a.y_mm + a.alt_mm, b.y_mm + b.alt_mm)
            menor = min(a.alt_mm, b.alt_mm)
            return menor > 0 and (base - topo) >= 0.5 * menor

        linhas: list[list[Retangulo]] = []
        for caixa in caixas:                   # já em ordem visual (y, x)
            if linhas and _mesma_linha(linhas[-1][0], caixa):
                linhas[-1].append(caixa)
            else:
                linhas.append([caixa])
        retangulos = []
        for grupo in linhas:
            u = _uniao(grupo)
            retangulos.append(Retangulo(u.x_mm - MARGEM_MM, u.y_mm - MARGEM_MM,
                                        u.larg_mm + 2 * MARGEM_MM,
                                        u.alt_mm + 2 * MARGEM_MM))
        titulo = (pagina.titulos_secoes or {}).get(cat, cat)
        secoes.append(Secao(categoria=cat, titulo=titulo,
                            retangulos=retangulos, n_celulas=len(slots)))
    return secoes


def config_secoes(raiz=None) -> tuple[str, float]:
    """(cor, espessura_mm) da Config — defaults sãos (C3): azul da visão."""
    try:
        from app.core.database import Database
        from app.core.repositories import ConfigRepositorio

        db = Database(raiz) if raiz is not None else Database()
        db.init()
        try:
            with db.Session() as s:
                cfg = ConfigRepositorio(s)
                cor = str(cfg.get("secoes.cor") or COR_PADRAO)
                esp = float(cfg.get("secoes.espessura_mm",
                                    ESPESSURA_PADRAO_MM))
        finally:
            db.engine.dispose()
        if not cor.startswith("#") or len(cor) != 7:
            cor = COR_PADRAO
        if not (0.1 <= esp <= 5.0):
            esp = ESPESSURA_PADRAO_MM
        return cor, esp
    except Exception:
        return COR_PADRAO, ESPESSURA_PADRAO_MM


def estilo_secoes(raiz=None) -> tuple[str, bool]:
    """RG-31: (estilo, cor_por_categoria) da Config — default são."""
    try:
        from app.core.database import Database
        from app.core.repositories import ConfigRepositorio

        db = Database(raiz) if raiz is not None else Database()
        db.init()
        try:
            with db.Session() as s:
                cfg = ConfigRepositorio(s)
                estilo = str(cfg.get("secoes.estilo") or ESTILO_PADRAO)
                por_cat = bool(cfg.get("secoes.cores_por_categoria", False))
        finally:
            db.engine.dispose()
        if estilo not in ESTILOS_SECAO:
            estilo = ESTILO_PADRAO
        return estilo, por_cat
    except Exception:
        return ESTILO_PADRAO, False


def desenhar_secoes(base, secoes: list[Secao], dpi: int, *,
                    cor: str = COR_PADRAO,
                    espessura_mm: float = ESPESSURA_PADRAO_MM,
                    fontes_dir=None,
                    estilo: str = ESTILO_PADRAO,
                    cores_por_categoria: bool = False) -> None:
    """Desenha as seções NA IMAGEM (antes do conteúdo), no ESTILO escolhido.

    RG-31 — os estilos de verdade:
      CONTORNO    — o retângulo arredondado da visão (com as curas do bug);
      SO_TITULO   — só a etiqueta, sem borda nenhuma;
      PILL        — fundo suave translúcido atrás do bloco + etiqueta;
      SEM_DESENHO — agrupar SEM desenhar (o modo pedido pelo dono).

    Curas do bug da captura da Mesa: o título agora mora DENTRO do
    retângulo (a cavalo da borda ele invadia a célula de cima), e a cor
    pode ser POR CATEGORIA (paleta estável).
    """
    from PIL import Image, ImageDraw

    from app.rendering.compositor import fonte_segura
    from app.rendering.units import mm_para_px, pt_para_px

    if estilo == "SEM_DESENHO" or not secoes:
        return
    if fontes_dir is None:
        from app.core.paths import SystemRoot
        fontes_dir = SystemRoot().fontes
    esp_px = max(1, round(mm_para_px(espessura_mm, dpi)))
    raio_px = round(mm_para_px(RAIO_MM, dpi))
    fonte = fonte_segura(fontes_dir, "Roboto-Bold.ttf",
                         round(pt_para_px(TITULO_PT, dpi)))
    # camada RGBA própria: o PILL precisa de transparência, e compor a
    # camada inteira de uma vez mantém o contorno atrás do conteúdo
    camada = Image.new("RGBA", base.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(camada)

    def _pill_cor(c: str) -> tuple:
        r, g, b = (int(c[i:i + 2], 16) for i in (1, 3, 5))
        return (r, g, b, 42)               # bem suave — fundo, não tinta

    for secao in secoes:
        cor_secao = (cor_da_categoria(secao.categoria)
                     if cores_por_categoria else cor)
        # sub-retângulos por linha (px), com clamp às bordas da folha
        rects_px = []
        for r in secao.retangulos:
            x0 = max(round(mm_para_px(r.x_mm, dpi)), esp_px)
            y0 = max(round(mm_para_px(r.y_mm, dpi)), esp_px)
            x1 = min(round(mm_para_px(r.x_mm + r.larg_mm, dpi)),
                     base.width - esp_px)
            y1 = min(round(mm_para_px(r.y_mm + r.alt_mm, dpi)),
                     base.height - esp_px)
            rects_px.append((x0, y0, x1, y1))
        if not rects_px:
            continue
        if estilo == "CONTORNO":
            # RG-49: UM contorno de união (sem divisória entre linhas
            # irmãs). Run de EXATAMENTE 1 célula NÃO ganha caixa — só o
            # rótulo (passo 36); n_celulas=0 (Secao sintético) desenha.
            if secao.n_celulas != 1:
                _contorno_uniao(draw, rects_px, cor_secao, esp_px, raio_px)
        elif estilo == "PILL":
            # fundo suave por linha (é preenchimento, não traço: não há
            # divisória interna a curar)
            for (x0, y0, x1, y1) in rects_px:
                draw.rounded_rectangle((x0, y0, x1, y1), radius=raio_px,
                                       fill=_pill_cor(cor_secao))
        # título: DENTRO do canto superior-esquerdo da 1ª linha (RG-31)
        if secao.titulo:
            x0, y0, x1, y1 = rects_px[0]
            caixa_txt = draw.textbbox((0, 0), secao.titulo, font=fonte)
            larg_txt = caixa_txt[2] - caixa_txt[0]
            alt_txt = caixa_txt[3] - caixa_txt[1]
            pad = esp_px * 2
            ex0 = x0 + esp_px + pad
            ey0 = y0 + esp_px + pad
            draw.rounded_rectangle(
                (ex0 - pad, ey0 - pad,
                 ex0 + larg_txt + pad, ey0 + alt_txt + pad),
                radius=pad, fill=cor_secao)
            draw.text((ex0, ey0 - caixa_txt[1]), secao.titulo,
                      font=fonte, fill="#FFFFFF")
    base.paste(camada, (0, 0), camada)

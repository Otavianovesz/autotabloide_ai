"""
Layouts de cartaz de gôndola (F6.5 + R-105 da Fase 11)
======================================================
Cartaz = 1 item por página, no tamanho físico exato (mm), RGB padrão. Este
módulo traz a **biblioteca de layouts prontos** — o placeholder 10×15 cm que
provou o mecanismo e, na Fase 11, os formatos que o dono usa no balcão: A4
retrato, A4 paisagem, meia folha (A5) e etiqueta de prateleira.

Cada layout tem as mesmas regiões (a MESMA cadeia produto→slot do tabloide):
nome no topo, imagem ao centro, preço "de" **riscado**, o **% de desconto**
CALCULADO ((de−por)/de, R-109), o preço "por" grande (reais + centavos
sobrescritos, autoajustado a 5 metros, R-107) e a **validade** no rodapé
(papel VALIDADE — puxa a data da oferta e nunca fica vazia, RG-58).

Os tamanhos ficam em mm; as posições são frações da folha, então o mesmo
desenho serve para qualquer formato sem "escorregar". Quando a arte real do
Illustrator chegar, basta ``layout_de_arte`` + reposicionar — o mecanismo não
muda.
"""

from __future__ import annotations

from app.rendering.model import (
    Ajuste,
    Alinhamento,
    LayoutDef,
    Pagina,
    PapelPreco,
    PapelTexto,
    Regiao,
    Retangulo,
    Slot,
    SubtipoPreco,
    TipoRegiao,
)

LARGURA_MM = 100.0    # 10×15 cm (retrato) — placeholder até a arte real
ALTURA_MM = 150.0
DPI = 300

# cores (herdadas do placeholder que o dono já validou)
_COR_NOME = "#16202E"
_COR_DE = "#5A6472"
_COR_POR = "#DC2626"
_COR_VALIDADE = "#5A6472"
_COR_DESCONTO = "#DC2626"
_FONTE = "Quicksand-Bold.ttf"


def _cartaz_padrao(largura_mm: float, altura_mm: float, *, dpi: int = DPI,
                   com_imagem: bool = True) -> LayoutDef:
    """Monta um cartaz genérico no tamanho físico dado (mm).

    As regiões são posicionadas por FRAÇÃO da folha útil (descontada a margem),
    então A4/A5/etiqueta saem proporcionais sem código repetido. ``com_imagem``
    desligado (etiqueta pequena) dá todo o espaço ao texto e ao preço.
    """
    m = min(largura_mm, altura_mm) * 0.05          # margem proporcional
    W, H = largura_mm - 2 * m, altura_mm - 2 * m   # folha útil

    def rect(fx: float, fy: float, fw: float, fh: float) -> Retangulo:
        return Retangulo(m + fx * W, m + fy * H, fw * W, fh * H)

    regioes: list[Regiao] = []
    if com_imagem:
        y_nome, h_nome = 0.00, 0.14
        y_img, h_img = 0.16, 0.40
        y_de, h_de = 0.58, 0.08
        y_por, h_por = 0.66, 0.26
        y_val, h_val = 0.93, 0.07
    else:                                           # etiqueta: texto+preço mandam
        y_nome, h_nome = 0.00, 0.24
        y_img, h_img = 0.0, 0.0
        y_de, h_de = 0.28, 0.12
        y_por, h_por = 0.42, 0.44
        y_val, h_val = 0.90, 0.10

    # NOME (topo)
    regioes.append(Regiao(
        TipoRegiao.NOME, rect(0.0, y_nome, 1.0, h_nome),
        nome="Nome", fonte=_FONTE, tamanho_max_pt=40, cor=_COR_NOME,
        alinhamento=Alinhamento.CENTRO))

    # IMAGEM (centro) — só quando cabe
    if com_imagem:
        regioes.append(Regiao(
            TipoRegiao.IMAGEM, rect(0.0, y_img, 1.0, h_img),
            nome="Imagem", ajuste=Ajuste.CONTER))

    # PREÇO "de" riscado (esquerda da linha) + DESCONTO calculado (direita)
    regioes.append(Regiao(
        TipoRegiao.PRECO, rect(0.0, y_de, 0.58, h_de),
        nome="Preço de", fonte=_FONTE, tamanho_max_pt=22, cor=_COR_DE,
        alinhamento=Alinhamento.DIREITA,
        subtipo_preco=SubtipoPreco.COMPLETO, papel_preco=PapelPreco.DE,
        riscado=True))
    regioes.append(Regiao(
        TipoRegiao.TEXTO_LEGAL, rect(0.62, y_de - 0.02, 0.38, h_de + 0.04),
        nome="Desconto", fonte=_FONTE, tamanho_max_pt=40, cor=_COR_DESCONTO,
        alinhamento=Alinhamento.CENTRO, papel_texto=PapelTexto.DESCONTO))

    # PREÇO "por" gigante (reais + centavos sobrescritos, autoajustado)
    regioes.append(Regiao(
        TipoRegiao.PRECO, rect(0.0, y_por, 1.0, h_por),
        nome="Preço por", fonte=_FONTE, tamanho_max_pt=96, cor=_COR_POR,
        alinhamento=Alinhamento.CENTRO,
        subtipo_preco=SubtipoPreco.SEPARADO, papel_preco=PapelPreco.POR))

    # VALIDADE no rodapé (papel VALIDADE: puxa a data da oferta, RG-58)
    regioes.append(Regiao(
        TipoRegiao.TEXTO_LEGAL, rect(0.0, y_val, 1.0, h_val),
        nome="Validade", fonte=_FONTE, tamanho_max_pt=12, cor=_COR_VALIDADE,
        alinhamento=Alinhamento.CENTRO, papel_texto=PapelTexto.VALIDADE))

    return LayoutDef(
        largura_mm=largura_mm, altura_mm=altura_mm, dpi=dpi,
        paginas=[Pagina([Slot("cartaz", regioes)])],
    )


# --- a biblioteca (R-105): formatos prontos ---------------------------------------

def layout_cartaz_exemplo() -> LayoutDef:
    """Cartaz placeholder 10×15 cm — o formato que provou o de/por riscado."""
    return _cartaz_padrao(LARGURA_MM, ALTURA_MM)


def layout_cartaz_a4_retrato() -> LayoutDef:
    """A4 em pé (210×297 mm) — o cartaz grande da ponta de gôndola."""
    return _cartaz_padrao(210.0, 297.0)


def layout_cartaz_a4_paisagem() -> LayoutDef:
    """A4 deitado (297×210 mm) — faixa larga sobre a prateleira."""
    return _cartaz_padrao(297.0, 210.0)


def layout_cartaz_a5() -> LayoutDef:
    """Meia folha A5 (148×210 mm) — o formato do 2-em-1 (dois por A4)."""
    return _cartaz_padrao(148.0, 210.0)


def layout_etiqueta() -> LayoutDef:
    """Etiqueta de prateleira (100×70 mm) — só nome + de/por + validade."""
    return _cartaz_padrao(100.0, 70.0, com_imagem=False)


# nome exibido na Fábrica → construtor. A ordem é a da lista suspensa.
PRESETS_CARTAZ: dict[str, callable] = {
    "Cartaz 10×15 — exemplo": layout_cartaz_exemplo,
    "A4 retrato (210×297 mm)": layout_cartaz_a4_retrato,
    "A4 paisagem (297×210 mm)": layout_cartaz_a4_paisagem,
    "Meia folha A5 (148×210 mm)": layout_cartaz_a5,
    "Etiqueta de prateleira (100×70 mm)": layout_etiqueta,
}

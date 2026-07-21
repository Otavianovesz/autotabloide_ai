"""Formatos sociais (R-141 Oferta do Dia, R-140 carrossel, R-145 faixa, R-139
Story) — Fase 8, Blocos C/E.

DECISÃO DE ARQUITETURA TRAVADA: o formato social é só OUTRO ``LayoutDef`` com
outra proporção + a MESMA cadeia produto→slot. NADA de motor novo: reusa
``compor_pagina`` (o compositor medido nas fases anteriores), a célula vitrine
(R-044) e o ``DadosProduto`` do tabloide. O mesmo item (por uid) cai num card
social sem duplicar identidade (I1).
"""

from __future__ import annotations

from dataclasses import dataclass

from PIL import Image

from app.rendering.compositor import DadosProduto, compor_pagina
from app.rendering.model import (
    Ajuste,
    Alinhamento,
    LayoutDef,
    Pagina,
    PapelPreco,
    Regiao,
    Retangulo,
    Slot,
    SubtipoPreco,
    TipoRegiao,
)
from app.rendering.modelos import carimbar_modelo, modelo_vitrine
from app.rendering.units import px_para_mm


@dataclass
class FormatoSocial:
    nome: str
    largura_px: int
    altura_px: int
    dpi: int = 96
    molde: str = "vitrine"     # "vitrine" (1 preço) | "oferta" (de/por gigante)


# a biblioteca de proporções (passo 39) — o dono escolhe o nome, não o pixel
FORMATOS: dict[str, FormatoSocial] = {
    "oferta_do_dia": FormatoSocial("Oferta do Dia", 1080, 1080, molde="oferta"),
    "oferta_do_dia_alto": FormatoSocial("Oferta do Dia (alto)", 1080, 1350,
                                        molde="oferta"),
    "carrossel": FormatoSocial("Card de carrossel", 1080, 1080),
    "story": FormatoSocial("Story / Reels", 1080, 1920),
    "faixa": FormatoSocial("Faixa / banner", 1920, 1080),
}


def _regioes_oferta(larg_mm: float, alt_mm: float) -> list[Regiao]:
    """Herói com de/por (R-141): foto grande, nome com pílula, "de" riscado e
    "por" GIGANTE. Posições em fração da caixa, p/ qualquer proporção social.
    OS F11.5 #31 (R-044): a foto e o nome REUSAM o estilo do modelo VITRINE
    (ajuste, pílula, cores vêm DELE — mudar a vitrine muda o card junto); só
    o preço é o par de/por próprio do herói social."""
    vit = {d["tipo"]: d for d in modelo_vitrine().regioes}
    foto_v, nome_v = vit["IMAGEM"], vit["NOME"]

    def rt(fx, fy, fw, fh):
        return Retangulo(fx * larg_mm, fy * alt_mm, fw * larg_mm, fh * alt_mm)
    return [
        Regiao(TipoRegiao.IMAGEM, rt(0.06, 0.05, 0.88, 0.52),
               nome="Foto", ajuste=Ajuste[foto_v["ajuste"]]),
        Regiao(TipoRegiao.NOME, rt(0.05, 0.58, 0.90, 0.12), nome="Nome",
               alinhamento=Alinhamento.CENTRO, tamanho_max_pt=34,
               cor=nome_v["cor"], pill=nome_v["pill"],
               pill_cor=nome_v["pill_cor"],
               pill_opacidade=nome_v["pill_opacidade"]),
        Regiao(TipoRegiao.PRECO, rt(0.30, 0.71, 0.40, 0.07), nome="Preço de",
               alinhamento=Alinhamento.CENTRO, tamanho_max_pt=22, cor="#5A6472",
               subtipo_preco=SubtipoPreco.COMPLETO, papel_preco=PapelPreco.DE,
               riscado=True),
        Regiao(TipoRegiao.PRECO, rt(0.06, 0.78, 0.88, 0.20), nome="Preço por",
               alinhamento=Alinhamento.CENTRO, tamanho_max_pt=90, cor="#DC2626",
               subtipo_preco=SubtipoPreco.SEPARADO, papel_preco=PapelPreco.POR),
    ]


def layout_social(formato: str, fundo: str | None = None) -> LayoutDef:
    """Um LayoutDef declarado para a proporção social — mm/dpi que reproduzem os
    px alvo (I3: sem caminho absoluto além do `fundo` que o chamador der)."""
    f = FORMATOS[formato]
    larg_mm = px_para_mm(f.largura_px, f.dpi)
    alt_mm = px_para_mm(f.altura_px, f.dpi)
    if f.molde == "oferta":
        regioes = _regioes_oferta(larg_mm, alt_mm)
    else:
        regioes = carimbar_modelo(modelo_vitrine(), 0, 0, larg_mm, alt_mm)
    return LayoutDef(largura_mm=larg_mm, altura_mm=alt_mm, dpi=f.dpi,
                     arquivo_fundo=fundo,
                     paginas=[Pagina([Slot("card", regioes)])])


def compor_social(formato: str, dados: DadosProduto,
                  fundo: str | None = None) -> Image.Image:
    """Compõe UM card social a partir de UM DadosProduto (o mesmo item por uid).
    O tamanho de saída em px bate com o formato (régua de bytes)."""
    lay = layout_social(formato, fundo)
    return compor_pagina(lay, lay.paginas[0], {"card": dados})


def compor_carrossel(dados_lista: list[DadosProduto],
                     formato: str = "carrossel",
                     fundo: str | None = None) -> list[Image.Image]:
    """R-140: N cards (1 por produto), NA ORDEM dada — cada card é uma página de
    1 slot herói. Devolve a lista de Images (o chamador numera os arquivos).
    OS F11.5 #40: `fundo` (a arte do projeto) atravessa até cada card."""
    return [compor_social(formato, d, fundo) for d in dados_lista]

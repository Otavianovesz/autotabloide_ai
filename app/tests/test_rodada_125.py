"""RODADA-125 (03/08/2026) — a auditoria do Jornal que o DONO montou no
automático e mandou em fotos: "quero esse jornal perfeitamente
ajustado". Cada teste nasce de um defeito VISÍVEL nas páginas dele."""

import pytest
from PIL import Image


def test_dois_pesos_no_fim_descem_juntos():
    """Na página dele: "400 g · 500g", "1,5 L · 1,6L", "90 g · 102g" —
    grafia mista porque o 2º peso ficava preso no nome. A oferta
    multi-tamanho desce os DOIS: "400 g ou 500 g"."""
    from app.core.sanitize import separar_peso

    assert separar_peso("MILHO PIPOCA YOKI 400g 500g") == \
        ("MILHO PIPOCA YOKI", "400 g ou 500 g")
    assert separar_peso("REFRIGERANTE KITUBAINA 1,5L 1,6L") == \
        ("REFRIGERANTE KITUBAINA", "1,5 L ou 1,6 L")
    assert separar_peso("CREME DENTAL KOLYNOS 90g 102g") == \
        ("CREME DENTAL KOLYNOS", "90 g ou 102 g")
    # um peso só: como sempre
    assert separar_peso("Leite Condensado Triangulo 395g") == \
        ("Leite Condensado Triangulo", "395 g")
    # multiplicador NÃO abre a cascata (o kit é um peso só)
    assert separar_peso("Kit 4x120g") == ("Kit", "4x120 g")
    # peso no MEIO segue intocado (a lei da camada)
    assert separar_peso("Oferta 200g no Pacote") == \
        ("Oferta 200g no Pacote", None)


def test_vitrine_em_camadas_fotos_grandes():
    """A queixa literal: "fica duas coisas pequeneninhas". Na vitrine
    nova cada foto ocupa ≥60% da altura da zona (n=2) e as duas se
    SOBREPÕEM (o span é menor que a soma das larguras)."""
    from app.rendering.arranjo import ModoArranjo, compor_imagens

    a = Image.new("RGBA", (400, 600), (200, 40, 40, 255))
    b = Image.new("RGBA", (400, 600), (40, 40, 200, 255))
    c = compor_imagens([a, b], 460, 380, ModoArranjo.LADO_A_LADO)
    alfa = c.getchannel("A")
    bbox = alfa.getbbox()
    assert bbox is not None
    altura_util = bbox[3] - bbox[1]
    assert altura_util >= 380 * 0.85, (
        f"as fotos continuam pequenas: {altura_util}px de {380}")
    # sobreposição real POR CONTEÚDO: existe coluna x onde as DUAS
    # cores aparecem (o fatiado antigo nunca tinha)
    tem_verm = set()
    tem_azul = set()
    for x in range(0, c.width, 2):
        for y in range(0, c.height, 4):
            p = c.getpixel((x, y))
            if p[3] > 128:
                if p[0] > 150:
                    tem_verm.add(x)
                elif p[2] > 150:
                    tem_azul.add(x)
    # a 1ª (frente) sobressai; a 2ª fica parcialmente coberta — no
    # fatiado antigo as larguras visíveis eram IGUAIS
    assert len(tem_azul) < len(tem_verm), (
        f"sem camadas: azul {len(tem_azul)} ≥ verm {len(tem_verm)}")


def test_agrupar_nao_liga_secoes_em_encarte_que_veta():
    """Achado 1 das seções: o Jornal da biblioteca nasce com seções
    DESLIGADAS de propósito e o agrupar as ligava no CONTORNO global —
    chips sobre títulos, molduras cortando colunas (as fotos do dono).
    Agora o desenho só liga onde a página tem estilo PRÓPRIO."""
    from app.qt.telas.servico import aplicar_secoes_do_agrupar
    from app.rendering.model import LayoutDef, Pagina

    jornal = Pagina([], secoes_ligadas=False)          # sem estilo: veta
    fluxo = Pagina([], secoes_ligadas=False, estilo_secoes="JORNAL")
    aplicar_secoes_do_agrupar([jornal, fluxo], True)
    assert jornal.secoes_ligadas is False, (
        "o agrupar voltou a ligar seção em encarte que a veta")
    assert fluxo.secoes_ligadas is True
    aplicar_secoes_do_agrupar([jornal, fluxo], False)
    assert fluxo.secoes_ligadas is False

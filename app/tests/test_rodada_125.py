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


def _raiz(tmp_path, monkeypatch):
    from app.core.database import Database
    from app.core.paths import SystemRoot
    monkeypatch.setenv("AUTOTABLOIDE_ROOT", str(tmp_path / "raiz"))
    r = SystemRoot(tmp_path / "raiz")
    Database(r).init().engine.dispose()
    return r


def test_onda2_sabor_existente_e_casado_nunca_recriado(tmp_path,
                                                       monkeypatch):
    """A pergunta do dono: "quando já existe um sabor no banco... como
    ele não correlaciona o que já existe?" — agora correlaciona: o
    existente é CASADO (mesmo com grafia diferente, pela chave), só o
    novo nasce; reimportar não duplica nada."""
    from app.core.models import Produto
    from app.qt.telas import servico
    from app.tests import acervo

    _raiz(tmp_path, monkeypatch)
    f1 = tmp_path / "branco.png"
    acervo.foto_de_bancada(f1, (240, 240, 240))
    # o dono já tinha criado o Branco (com foto) numa sessão anterior
    it0 = servico.ItemMesa("X", "4,94", "VERMELHO", "X")
    servico.finalizar_criacao(it0, "Bis Lacta Xtra 45g Branco", False,
                              str(f1))
    id_branco = it0.produto_id

    # hoje a linha traz Branco + Oreo — o Branco NÃO pode renascer
    item = servico.ItemMesa("BIS EXTRA 45 g BRANCO e OREO", "4,94",
                            "VERMELHO", "Bis")
    servico.criar_familia_de_sabores(
        item, "Bis Lacta Xtra 45g", ["Branco", "Oreo"], False, None)
    from app.core.database import Database
    db = Database().init()
    try:
        with db.Session() as s:
            ativos = s.query(Produto).filter(
                Produto.excluido_em.is_(None)).all()
            assert len(ativos) == 2, (
                f"duplicou: {[p.nome_sanitizado for p in ativos]}")
            branco = s.get(Produto, id_branco)
            assert branco.familia_id, "o existente não entrou na família"
    finally:
        db.engine.dispose()

    # reimportar a MESMA linha: continua 2 (idempotente)
    item2 = servico.ItemMesa("BIS EXTRA 45 g BRANCO e OREO", "4,94",
                             "VERMELHO", "Bis")
    servico.criar_familia_de_sabores(
        item2, "Bis Lacta Xtra 45g", ["Branco", "Oreo"], False, None)
    db = Database().init()
    try:
        with db.Session() as s:
            n = s.query(Produto).filter(
                Produto.excluido_em.is_(None)).count()
            assert n == 2, "reimportar recriou produto"
    finally:
        db.engine.dispose()


def test_onda2_cartesiano_e_a_regua_do_caber():
    """A decisão do dono: Bulnez e Adoralle × Cream Cracker/Leite/
    Maisena = 6 itens ("o ideal é ter as 6 fotos, isso se couber; se
    não, selecionar adequadamente")."""
    from app.qt.telas.servico import (
        MAX_FOTOS_CELULA,
        rotulos_marcas_x_sabores,
        selecionar_fotos_da_celula,
    )

    rot = rotulos_marcas_x_sabores(
        ["Bulnez", "Adoralle"], ["Cream Cracker", "Leite", "Maisena"])
    assert len(rot) == 6
    assert rot[0] == "Bulnez Cream Cracker"
    assert rot[3] == "Adoralle Cream Cracker"    # marca-major
    # 6 fotos numa célula de 4: a seleção espaçada pega as DUAS marcas
    fotos = [f"foto_{r}" for r in rot]
    sel = selecionar_fotos_da_celula(fotos)
    assert len(sel) == MAX_FOTOS_CELULA
    assert any("Bulnez" in f for f in sel)
    assert any("Adoralle" in f for f in sel)
    # 4 ou menos: todas entram
    assert selecionar_fotos_da_celula(fotos[:3]) == fotos[:3]


def test_onda2_secao_do_jornal_medida_na_folga(tmp_path):
    """A seção PRÓPRIA do Jornal ("bonitinho mas tem que funcionar"):
    o cabeçalho tipográfico desenha NA FOLGA entre fileiras — e quando
    a folga não existe, NÃO desenha (ausente é melhor que por cima do
    conteúdo, a lição das fotos)."""
    from PIL import Image
    from app.rendering.secoes import Secao, desenhar_secoes
    from app.rendering.model import Retangulo
    from app.tests import acervo

    fontes = tmp_path / "fontes"
    fontes.mkdir()
    acervo.copiar_fontes_reais(fontes)

    def _pinta(folga_mm, larg_vizinho=100):
        base = Image.new("RGB", (400, 400), (245, 240, 230))
        # fileira de cima termina em y=40mm; o bloco da seção começa
        # em 40+folga (dpi=25 ≈ 1mm por px)
        sec = Secao(categoria="Mercearia", titulo="Mercearia",
                    retangulos=[Retangulo(20, 40 + folga_mm, 300, 60)],
                    n_celulas=3)
        caixas = [(20, 10, 20 + larg_vizinho, 40),
                  (20, 40 + folga_mm, 320, 100 + folga_mm)]
        desenhar_secoes(base, [sec], 25, fontes_dir=fontes,
                        estilo="JORNAL", caixas_pagina_mm=caixas)
        return base

    def _tinta(im, y0=0, y1=400):
        return sum(1 for p in im.crop((15, y0, 350, y1)).getdata()
                   if p[0] < 120 and p[1] < 120)

    # folga de 8mm com vizinho ESTREITO (célula comum): desenha na folga
    com = _pinta(8.0)
    assert _tinta(com, 40, 53) > 50, "o cabeçalho não desenhou na folga"
    assert _tinta(com, 0, 39) == 0, "invadiu a fileira de cima"
    # SEM folga (0.5mm): não desenha nada — nem por cima do vizinho
    assert _tinta(_pinta(0.5)) == 0, "desenhou sem folga"
    # vizinho LARGO (manchete/subtítulo — território editorial): a
    # mesma folga de 8mm NÃO basta — melhor calar que riscar texto
    assert _tinta(_pinta(8.0, larg_vizinho=290)) == 0, (
        "riscou a área editorial (a manchete da prova real)")

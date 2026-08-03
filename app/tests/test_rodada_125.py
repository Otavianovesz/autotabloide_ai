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


def test_onda3_linha_multi_casa_com_o_conjunto_do_acervo(tmp_path,
                                                         monkeypatch):
    """O print do dono (03/08): "os itens com mais de uma marca ou
    sabor não conseguem ser associados com o que já salvei". Agora a
    linha multi casa com o CONJUNTO: todos os membros existem → VERDE
    montado com as fotos DELES, sem curadoria; parcial NÃO inventa."""
    from app.qt.telas import servico
    from app.tests import acervo

    _raiz(tmp_path, monkeypatch)
    f1 = tmp_path / "p.png"
    acervo.foto_de_bancada(f1, (200, 60, 60))
    # o dono JÁ criou os dois sabores (com foto no 1º) numa sessão
    a = servico.ItemMesa("X", "26,66", "VERMELHO", "X")
    servico.finalizar_criacao(a, "Amaciante Mon Bijou 5L Proteção",
                              False, str(f1))
    b = servico.ItemMesa("Y", "26,66", "VERMELHO", "Y")
    servico.finalizar_criacao(b, "Amaciante Mon Bijou 5L Clássico",
                              False, None)

    cj = servico.conjunto_do_acervo(
        "AMACIANTE MON BIJOU 5L PROTEÇÃO e CLASSICO")
    assert cj is not None and cj["tipo"] == "familia", (
        f"o conjunto não foi reconhecido: {cj}")
    assert len(cj["membros"]) == 2
    item = servico.item_do_conjunto(
        "AMACIANTE MON BIJOU 5L PROTEÇÃO e CLASSICO", "26,66", None, cj)
    assert item.semaforo == "VERDE" and item.via == "conjunto"
    assert len(item.imagens) == 1          # a foto que o acervo TEM
    assert item.sabores and "Proteção" in item.sabores[0]
    # parcial: some um membro → None (nada nasce verde calado)
    assert servico.conjunto_do_acervo(
        "AMACIANTE MON BIJOU 5L PROTEÇÃO e INEXISTENTE") is None


def test_onda3_composto_do_acervo(tmp_path, monkeypatch):
    """"ARROZ SOMAR e TIO BONINI": os dois já existem → a linha nasce
    o COMPOSTO deles (2 fotos, 1 preço), nada recriado."""
    from app.qt.telas import servico
    from app.tests import acervo

    _raiz(tmp_path, monkeypatch)
    f1 = tmp_path / "s.png"
    acervo.foto_de_bancada(f1, (60, 200, 60))
    f2 = tmp_path / "t.png"
    acervo.foto_de_bancada(f2, (60, 60, 200))
    a = servico.ItemMesa("X", "18,81", "VERMELHO", "X")
    servico.finalizar_criacao(a, "Arroz Somar 5 kg", False, str(f1))
    b = servico.ItemMesa("Y", "18,81", "VERMELHO", "Y")
    servico.finalizar_criacao(b, "Arroz Tio Bonini 5 kg", False,
                              str(f2))

    cj = servico.conjunto_do_acervo("ARROZ SOMAR e TIO BONINI 5 Kgs")
    assert cj is not None and cj["tipo"] == "composto", f"cj={cj}"
    item = servico.item_do_conjunto(
        "ARROZ SOMAR e TIO BONINI 5 Kgs", "18,81", None, cj)
    assert item.semaforo == "VERDE" and item.via == "conjunto"
    assert len(item.imagens) == 2, "as DUAS fotos do acervo na célula"
    assert servico.eh_composto(item)


def test_onda3b_montar_conjunto_manual(tmp_path, monkeypatch):
    """O pedido do dono: "liberdade pra caçar esses dois itens já
    existentes e colocar ali". A cesta monta a linha com N produtos do
    acervo — sabores (leque) ou diferentes (composto) — sem recriar."""
    from app.qt.telas import servico
    from app.tests import acervo

    _raiz(tmp_path, monkeypatch)
    f1 = tmp_path / "a.png"
    acervo.foto_de_bancada(f1, (200, 60, 60))
    a = servico.ItemMesa("X", "9,90", "VERMELHO", "X")
    servico.finalizar_criacao(a, "Suco Aurora Uva 1,5L", False, str(f1))
    b = servico.ItemMesa("Y", "9,90", "VERMELHO", "Y")
    servico.finalizar_criacao(b, "Suco Aurora Laranja 1,5L", False,
                              None)

    linha = servico.ItemMesa("SUCO AURORA 1,5L SABORES", "9,90",
                             "AMARELO", "Suco Aurora")
    uid0 = linha.uid
    novo = servico.montar_conjunto_manual(
        linha, [a.produto_id, b.produto_id], "sabores",
        "Suco Aurora 1,5L")
    assert novo.semaforo == "VERDE" and novo.via == "conjunto"
    assert novo.uid == uid0, "a identidade da linha mudou (I1)"
    assert novo.nome == "Suco Aurora 1,5L"
    assert len(novo.imagens) == 1          # só a foto que o acervo tem
    assert any("Uva" in s for s in novo.sabores)
    # diferentes com 2 → o composto separável de sempre
    linha2 = servico.ItemMesa("SUCOS", "9,90", "AMARELO", "Sucos")
    comp = servico.montar_conjunto_manual(
        linha2, [a.produto_id, b.produto_id], "diferentes", "")
    assert servico.eh_composto(comp)
    # cesta magra: erro dito, nunca silêncio
    import pytest as _pt
    with _pt.raises(ValueError):
        servico.montar_conjunto_manual(linha2, [a.produto_id],
                                       "sabores", "Z")


def test_onda3b_dialogo_da_cesta(tmp_path, monkeypatch):
    """O gesto: buscar, duplo clique enche a cesta, 2+ habilita o
    Usar; a escolha devolve (ids, tipo, nome)."""
    from PySide6.QtWidgets import QApplication
    QApplication.instance() or QApplication([])
    from app.qt.telas import servico
    from app.qt.telas.montar_conjunto_dialog import MontarConjuntoDialog

    _raiz(tmp_path, monkeypatch)
    a = servico.ItemMesa("X", "1,00", "VERMELHO", "X")
    servico.finalizar_criacao(a, "Arroz Camil 5 kg", False, None)
    b = servico.ItemMesa("Y", "1,00", "VERMELHO", "Y")
    servico.finalizar_criacao(b, "Arroz Prato Fino 5 kg", False, None)

    dlg = MontarConjuntoDialog("ARROZ CAMIL e PRATO FINO",
                               sugestao_nome="Arroz Camil e Prato Fino")
    try:
        dlg.busca.setText("Arroz")
        assert dlg.resultados.count() >= 2, "a busca não achou os dois"
        assert not dlg._ok.isEnabled()
        dlg.resultados.setCurrentRow(0)
        dlg._adicionar()
        dlg.resultados.setCurrentRow(1)
        dlg._adicionar()
        assert dlg._ok.isEnabled(), "2 na cesta tinha de habilitar"
        assert "✓ na cesta" in dlg.resultados.item(0).text()
        dlg.resultados.setCurrentRow(0)
        dlg._adicionar()                     # repetido não duplica
        assert dlg.cesta.count() == 2
        esc = dlg.escolha()
        assert esc is not None
        ids, tipo, nome = esc
        assert len(ids) == 2 and tipo == "diferentes"
        assert nome == "Arroz Camil e Prato Fino"
    finally:
        dlg.done(0)

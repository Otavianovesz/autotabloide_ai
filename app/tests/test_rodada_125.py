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
    # v2: o par quase-igual (razão ≤1,10) é RELEITURA do OCR — o dono
    # confirmou o 1,6 como erro; ver test_v2_falso_multi_tamanho_do_ocr
    assert separar_peso("REFRIGERANTE KITUBAINA 1,5L 1,6L") == \
        ("REFRIGERANTE KITUBAINA", "1,5 L")
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


def test_v2_falso_multi_tamanho_do_ocr():
    """A 2ª prova: "Kitubaina 1,5 L · 1,6L" — o 1,6 era RELEITURA do
    OCR (o dono confirmou). Razão ≤1,10 na mesma unidade = um peso só;
    diferença real (Kolynos 90/102, razão 1,13 — dois tubos REAIS)
    segue "ou"."""
    from app.core.sanitize import separar_peso

    assert separar_peso("REFRIGERANTE KITUBAINA 1,5L 1,6LT") == \
        ("REFRIGERANTE KITUBAINA", "1,5 L")
    assert separar_peso("CREME DENTAL KOLYNOS 90g 102g") == \
        ("CREME DENTAL KOLYNOS", "90 g ou 102 g")


def test_v2_vocabulario_da_segunda_prova():
    """Limpoll→Limpol, Waffer→Wafer, JONAD→Jonas, TODO S→Todos,
    Leite/Sabão ganham o "em"."""
    from app.core.ortografia import corrigir_acentos

    assert corrigir_acentos("DETG. LIMPOLL 500 ml") == \
        "DETG. LIMPOL 500 ml"
    assert corrigir_acentos("WAFFER BULNEZ 60g") == "WAFER BULNEZ 60g"
    assert corrigir_acentos("TEMPERO TIO JONAD 1 Kg TODO S") == \
        "TEMPERO TIO JONAS 1 Kg TODOS"
    assert corrigir_acentos("LEITE PO NINHO 380g") == \
        "LEITE EM PÓ NINHO 380g"
    assert corrigir_acentos("SABAO PO OMO 1.6 Kgs") == \
        "SABÃO EM PÓ OMO 1.6 Kgs"


def _celula_de_linha(tmp_path):
    """Uma célula generosa NOME+SUBTITULO (tudo cabe) — para provar que
    a divisão da v2 é SEMÂNTICA, não geométrica."""
    from app.rendering.model import Regiao, Retangulo, TipoRegiao
    from app.tests import acervo

    fontes = tmp_path / "fontes"
    if not fontes.exists():
        fontes.mkdir()
        acervo.copiar_fontes_reais(fontes)
    nome_f = next(fontes.glob("*.ttf")).name
    regioes = [
        Regiao(tipo=TipoRegiao.NOME, rect=Retangulo(0, 0, 120, 14),
               fonte=nome_f, tamanho_max_pt=14, tamanho_min_pt=9),
        Regiao(tipo=TipoRegiao.SUBTITULO, rect=Retangulo(0, 14, 120, 8),
               fonte=nome_f, tamanho_max_pt=9, tamanho_min_pt=6),
    ]
    return regioes, fontes


def test_v2_hierarquia_canonica_da_celula(tmp_path):
    """A REGRA CANÔNICA da 2ª prova ("não tem padrão nenhum nas
    nomenclaturas... Cadê a hierarquia?"): a linha grande diz O QUE É;
    a MARCA conhecida desce ao descritor SEMPRE — mesmo quando o nome
    caberia inteiro. Os casos são as células reais da página dele."""
    from app.rendering.nome_fit import precedencia_do_nome

    regioes, fontes = _celula_de_linha(tmp_path)

    def _aj(nome, unidade=None, marcas=(), descritor=None):
        return precedencia_do_nome(nome, descritor, unidade, regioes,
                                   96, fontes, marcas=marcas)

    # os dois leites saem com a MESMA hierarquia (a queixa literal)
    aj = _aj("Leite Integral Triângulo", "1 L", marcas=("Triângulo",))
    assert aj.nome == "Leite Integral"
    assert aj.descritor == "Triângulo · 1 L"
    aj = _aj("Leite Integral Parmalat", "1 L", marcas=("Parmalat",))
    assert aj.nome == "Leite Integral"
    assert aj.descritor == "Parmalat · 1 L"

    # "Doce Dia" nunca é partida — desce INTEIRA como marca
    aj = _aj("Açúcar Cristal Doce Dia 2kg", "2 kg", marcas=("Doce Dia",))
    assert aj.nome == "Açúcar Cristal"
    assert aj.descritor == "Doce Dia · 2 kg"

    # o composto sai equilibrado: tipo grande, as DUAS marcas juntas
    aj = _aj("Arroz Somar e Tio Bonini · 5 kg", "5 kg",
             marcas=("Somar", "Tio Bonini"))
    assert aj.nome == "Arroz"
    assert aj.descritor == "Somar e Tio Bonini · 5 kg"

    # embalagens por componente viajam com as marcas
    aj = _aj("Milho Verde Fugini (pouch) e Bonare (lata) · 170 g",
             "170 g", marcas=("Fugini", "Bonare"))
    assert aj.nome == "Milho Verde"
    assert aj.descritor == "Fugini (pouch) e Bonare (lata) · 170 g"

    # sem marca CONHECIDA nada muda (F9: a régua nunca inventa)
    aj = _aj("Leite Integral Triângulo", "1 L")
    assert aj.nome == "Leite Integral Triângulo"

    # marca no token 0 não divide (o tipo não pode sumir)
    aj = _aj("Nivea Sabonete", "85 g", marcas=("Nivea",))
    assert aj.nome == "Nivea Sabonete"


def test_v2_peso_nao_duplica_na_celula(tmp_path):
    """As 5 células da 2ª prova ("Sabão em Pó Omo 1,6kg / … · 1,6kg"):
    o peso que mora no MEIO do nome do banco e é IGUAL à unidade sai
    da exibição — a unidade já o leva ao descritor. O peso aparece UMA
    vez no par nome/descritor; a embalagem colada a ele desce junto."""
    from app.rendering.nome_fit import precedencia_do_nome

    regioes, fontes = _celula_de_linha(tmp_path)

    def _aj(nome, unidade, marcas=()):
        return precedencia_do_nome(nome, None, unidade, regioes,
                                   96, fontes, marcas=marcas)

    aj = _aj("Sabão em Pó Omo 1,6kg Caixeta L. Perfeita", "1,6 kg",
             marcas=("Omo",))
    assert aj.nome == "Sabão em Pó"
    junto = f"{aj.nome} {aj.descritor}"
    assert junto.count("1,6") == 1, junto
    assert "Omo" in aj.descritor and "Caixeta" in aj.descritor

    # "Batata 104g Tubo Pringles" → tipo grande; marca · tubo · 104 g
    aj = _aj("Batata 104g Tubo Pringles", "104 g", marcas=("Pringles",))
    assert aj.nome == "Batata"
    assert aj.descritor == "Pringles · Tubo · 104 g"

    # unidade DIFERENTE do peso do nome: o peso do nome fica (é
    # informação distinta, nunca se descarta em silêncio)
    aj = _aj("Café Torrado 500g", "1 kg")
    assert "500 g" in (aj.descritor or "") or "500g" in aj.nome


def test_v2_biscoito_marcas_e_sabores(tmp_path, monkeypatch):
    """A linha real da 2ª prova: "BISCOITO BULNEZ e ADORALLE 270 g
    C. CRACKER/LEITE/AGUA E SAL" — o dono: "não consegui criar cada um
    com seus sabores específicos, ele não deixou e nem sugeriu"."""
    from app.qt.telas.servico import (dividir_em_dois, familia_da_linha,
                                      marcas_e_sabores_da_linha)

    _raiz(tmp_path, monkeypatch)
    linha = "BISCOITO BULNEZ e ADORALLE 270 g C. CRACKER/LEITE/AGUA E SAL"
    # (1) "AGUA E SAL" é UM sabor consagrado — 3 sabores, nunca 4
    _, sabores = familia_da_linha(linha)
    assert len(sabores) == 3, sabores
    assert any("sal" in s.lower() for s in sabores)
    # (2) a barra do RABO não veta as marcas da FRENTE
    comps = dividir_em_dois(linha)
    assert len(comps) == 2, comps
    assert "Bulnez" in comps[0] and "Adoralle" in comps[1]
    # os casos-limite seguem: a Sardinha dá 3 sabores ("oleo e limão"
    # não é consagrado); o Arroz dá 2 componentes e zero sabores
    _, s2 = familia_da_linha("SARDINHA COQUEIRO 125 g TOMATE / OLEO e LIMAO")
    assert len(s2) == 3, s2
    assert familia_da_linha("ARROZ SOMAR e TIO BONINI 5 Kgs")[1] == []
    assert len(dividir_em_dois("ARROZ SOMAR e TIO BONINI 5 Kgs")) == 2
    # (5) o cartesiano: marcas separadas e a base LIMPA (sem as marcas —
    # o nome de família nunca mais carrega "Bulnez e Adoralle")
    base, marcas, ss = marcas_e_sabores_da_linha(linha)
    assert [m.lower() for m in marcas] == ["bulnez", "adoralle"]
    assert len(ss) == 3
    assert "bulnez" not in base.lower() and "adoralle" not in base.lower()
    assert "270" in base


def test_v2_biscoito_conjunto_cartesiano_do_acervo(tmp_path, monkeypatch):
    """Criados os 6 uma vez (marca × sabor), a MESMA linha reimportada
    nasce VERDE montada — o ciclo completo do cartesiano."""
    from app.qt.telas import servico
    from app.tests import acervo

    _raiz(tmp_path, monkeypatch)
    f1 = tmp_path / "b.png"
    acervo.foto_de_bancada(f1, (200, 160, 60))
    nomes = ["Biscoito Bulnez Cream Cracker 270g",
             "Biscoito Bulnez Leite 270g",
             "Biscoito Bulnez Agua e Sal 270g",
             "Biscoito Adoralle Cream Cracker 270g",
             "Biscoito Adoralle Leite 270g",
             "Biscoito Adoralle Agua e Sal 270g"]
    for i, n in enumerate(nomes):
        it = servico.ItemMesa(f"I{i}", "8,99", "VERMELHO", f"I{i}")
        servico.finalizar_criacao(it, n, False,
                                  str(f1) if i == 0 else None)

    linha = "BISCOITO BULNEZ e ADORALLE 270 g CREAM CRACKER/LEITE/AGUA E SAL"
    cj = servico.conjunto_do_acervo(linha)
    assert cj is not None and cj["tipo"] == "familia", f"cj={cj}"
    assert len(cj["membros"]) == 6
    item = servico.item_do_conjunto(linha, "8,99", None, cj)
    assert item.semaforo == "VERDE" and item.via == "conjunto"
    # v4 (a lei do dono: o Biscoito DIZ as marcas): o nome carrega
    # "Bulnez e Adoralle" (a hierarquia as desce ao descritor) e os
    # SABORES exibidos são os FATORADOS por extenso — nunca os 6
    # rótulos do cartesiano nem a contagem "8 sabores" (vetada)
    assert "Bulnez e Adoralle" in item.nome, item.nome
    assert len(item.sabores) == 3
    assert not any("Bulnez" in s for s in item.sabores)
    # parcial não inventa: sem um dos 6, o conjunto cala
    linha2 = "BISCOITO BULNEZ e ADORALLE 270 g CREAM CRACKER/LEITE/MAISENA"
    assert servico.conjunto_do_acervo(linha2) is None


def test_v2_dica_nunca_desenha_validade():
    """K8 confirmado pela frota: a região DICA sem texto caía no rabo
    genérico do texto_composto_legal e imprimia a VALIDADE na caixa
    "Fica a Dica". A dica é EDITORIAL: vazia não desenha NADA; e o
    jp2-dica do Jornal nasce com default editorial (a degradação sem
    IA nunca mais mostra data ali)."""
    from app.rendering.compositor import DadosProduto, texto_composto_legal
    from app.rendering.model import PapelTexto, Regiao, Retangulo, TipoRegiao

    d = DadosProduto("X", texto_legal="OFERTA VÁLIDA DE 03/08 ATÉ 27/08")
    dica_vazia = Regiao(TipoRegiao.TEXTO_LEGAL, Retangulo(0, 0, 50, 10),
                        papel_texto=PapelTexto.DICA, texto_fixo="")
    assert texto_composto_legal(dica_vazia, d) == ""
    dica_cheia = Regiao(TipoRegiao.TEXTO_LEGAL, Retangulo(0, 0, 50, 10),
                        papel_texto=PapelTexto.DICA,
                        texto_fixo="Prove com arroz soltinho.")
    assert texto_composto_legal(dica_cheia, d) == "Prove com arroz soltinho."
    # a região LIVRE continua com o último-recurso de sempre (I2)
    livre = Regiao(TipoRegiao.TEXTO_LEGAL, Retangulo(0, 0, 50, 10),
                   papel_texto=PapelTexto.LIVRE, texto_fixo="")
    assert "03/08" in texto_composto_legal(livre, d)
    # e o Jornal do pacote nasce com a dica editorial preenchida
    from app.rendering import encartes
    slots = encartes._jornal_p2()
    dica = next(r for s in slots if s.id == "jp2-dica" for r in s.regioes
                if getattr(r, "papel_texto", None) == PapelTexto.DICA)
    assert dica.texto_fixo and "válida" not in dica.texto_fixo.lower()


def test_v2_celula_lateral_nunca_inverte():
    """A capa do Kolynos: célula de CHAMADA (foto à esquerda, textos à
    direita) com foto DEITADA — o plano misto reordenava a célula
    (título no vão, foto embaixo). Célula LATERAL só aceita plano
    lateral/abraço: os textos seguem AO LADO da foto."""
    from app.rendering.foto_fit import plano_da_celula
    from app.rendering.model import Regiao, Retangulo, TipoRegiao

    regioes = [
        Regiao(TipoRegiao.IMAGEM, Retangulo(0, 0, 30, 36),
               zona_flex=True),
        Regiao(TipoRegiao.NOME, Retangulo(30, 4, 44, 8)),
        Regiao(TipoRegiao.SUBTITULO, Retangulo(30, 12, 44, 5)),
        Regiao(TipoRegiao.PRECO, Retangulo(39, 19, 27, 12)),
    ]
    # foto deitada (larga): ocupação < 85% → o plano roda
    plano = plano_da_celula(regioes, 400.0, 200.0)
    if plano is not None:
        assert plano.arranjo in ("lateral", "abraco"), plano.arranjo
        # nenhum texto pode parar DENTRO da faixa da foto original
        # (empilhado sobre o vão) — o nome segue à direita
        rn = plano.rects.get(regioes[1].uid)
        if rn is not None:
            assert rn.x_mm >= 28.0, f"o nome invadiu a foto: {rn}"

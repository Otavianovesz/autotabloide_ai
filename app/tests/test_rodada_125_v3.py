"""RODADA-125 v3 (03/08/2026) — a 3ª prova do dono: "ele COME
informações que eram pra ser completas", "fiz três sabores de sardinha
e ele ignorou", "não consigo arrastar da tabela pro slot", "mais de um
item no slot continua minúsculo". Cada teste nasce de uma queixa."""

import pytest
from PIL import Image


@pytest.fixture()
def raiz_env(tmp_path, monkeypatch):
    # o MESMO seed do test_os_f11_5 — a raiz "crua" (Database().init()
    # solto) derrubava a MesaTela isolada no 0xC0000409 da COND-10
    from app.tests import seeds_portabilidade as seeds
    root = seeds.raiz(tmp_path, "raiz")
    monkeypatch.setenv("AUTOTABLOIDE_ROOT", str(root.raiz))
    return root


def _celula_estreita(tmp_path, larg=42):
    """Uma célula com SUBTITULO APERTADO — o palco da tesoura."""
    from app.rendering.model import Regiao, Retangulo, TipoRegiao
    from app.tests import acervo

    fontes = tmp_path / "fontes"
    if not fontes.exists():
        fontes.mkdir()
        acervo.copiar_fontes_reais(fontes)
    nome_f = next(fontes.glob("*.ttf")).name
    reg = Regiao(TipoRegiao.SUBTITULO, Retangulo(0, 0, larg, 5),
                 fonte=nome_f, tamanho_max_pt=9, tamanho_min_pt=7)
    return reg, fontes


def test_v3_descritor_nunca_come_calado(tmp_path):
    """A LEI do dono (4ª prova): informação de venda sai POR EXTENSO —
    a forma compacta "N sabores" foi VETADA (risco legal). A escada:
    o CORPO CEDE até o piso duro e o texto sai INTEIRO; só num caso
    patológico a tesoura corta — e o que cai volta NOMEADO (I2)."""
    from app.rendering.nome_fit import descritor_que_cabe_ex

    # célula APERTADA mas realista (a linha do Jornal tem 36px/3
    # linhas): o completo sai INTEIRO — o corpo cede, nada é comido
    reg, fontes = _celula_estreita(tmp_path, larg=60)
    completo = "Coqueiro · Tomate, Óleo ou Limão · 125 g"
    texto, cortado = descritor_que_cabe_ex(completo, "125 g", reg, 96,
                                           fontes)
    assert texto == completo and cortado is None, (texto, cortado)
    assert "sabores" not in texto        # a compacta MORREU (vetada)
    # o caso patológico (caixa minúscula): corta, mas NOMEIA o que caiu
    reg3, _ = _celula_estreita(tmp_path, larg=14)
    texto3, cortado3 = descritor_que_cabe_ex(completo, "125 g", reg3,
                                             96, fontes)
    assert "125 g" in texto3             # a unidade NUNCA sai
    if texto3 != completo:
        assert cortado3, "cortou em silêncio"
    # numa região LARGA nada é tocado
    reg2, _ = _celula_estreita(tmp_path, larg=200)
    texto2, cortado2 = descritor_que_cabe_ex(completo, "125 g", reg2,
                                             96, fontes)
    assert texto2 == completo and cortado2 is None


def test_v3_juntar_descritor_conectores_e_tokens():
    """(a) "Fujini e" + "Cajamar" FUNDEM — o " · " nunca cai no meio da
    frase (o "Fujini e · Cajamar" da página); (b) o dedupe é por TOKEN:
    a unidade curta "g" não é mais engolida por ser substring de
    "fugini" (furava a QUARTUSDECIMUS §2)."""
    from app.rendering.nome_fit import _juntar_descritor

    assert _juntar_descritor(["Fujini e", "Cajamar"], None) == \
        "Fujini e Cajamar"
    assert _juntar_descritor(["Fugini", "e Cajamar"], None) == \
        "Fugini e Cajamar"
    assert _juntar_descritor(["Fugini", "g"], None) == "Fugini · g"
    # conector órfão na cauda cai
    assert _juntar_descritor(["Mabel", "e"], None) == "Mabel"
    # parte redundante (todos os tokens já ditos) segue caindo
    assert _juntar_descritor(["500 ml", "Diversos · 500ml"], None) == \
        "500 ml · Diversos"


def test_v3_ordem_canonica_peso_no_fim(tmp_path):
    """"Mabel · 600g Coco e Leite" morreu: o peso SEMPRE fecha o
    descritor — marca · sabores · peso."""
    from app.rendering.model import Regiao, Retangulo, TipoRegiao
    from app.rendering.nome_fit import precedencia_do_nome
    from app.tests import acervo

    fontes = tmp_path / "fontes"
    fontes.mkdir()
    acervo.copiar_fontes_reais(fontes)
    nome_f = next(fontes.glob("*.ttf")).name
    regioes = [
        Regiao(TipoRegiao.NOME, Retangulo(0, 0, 120, 14),
               fonte=nome_f, tamanho_max_pt=14, tamanho_min_pt=9),
        Regiao(TipoRegiao.SUBTITULO, Retangulo(0, 14, 120, 10),
               fonte=nome_f, tamanho_max_pt=9, tamanho_min_pt=6),
    ]
    aj = precedencia_do_nome(
        "Rosquinha Mabel 600g Leite", "Coco ou Leite", "600 g",
        regioes, 96, fontes, marcas=("Mabel",))
    assert aj.nome == "Rosquinha"
    assert aj.descritor.endswith("600 g"), aj.descritor
    assert aj.descritor.index("Mabel") < aj.descritor.index("Coco")


def test_v3_conjunto_com_sabor_sem_foto_avisa(tmp_path, monkeypatch):
    """A Sardinha: o conjunto casou os 3 mas 2 não tinham foto e o item
    nascia VERDE eufórico — agora a pendência e o motivo DIZEM."""
    from app.qt.telas import servico
    from app.tests import acervo

    monkeypatch.setenv("AUTOTABLOIDE_ROOT", str(tmp_path / "raiz"))
    from app.core.database import Database
    from app.core.paths import SystemRoot
    Database(SystemRoot(tmp_path / "raiz")).init().engine.dispose()

    f1 = tmp_path / "t.png"
    acervo.foto_de_bancada(f1, (200, 60, 60))
    nomes = ["Sardinha Coqueiro 125g Tomate",
             "Sardinha Coqueiro 125g Óleo",
             "Sardinha Coqueiro 125g Limão"]
    for i, n in enumerate(nomes):
        it = servico.ItemMesa(f"S{i}", "6,90", "VERMELHO", f"S{i}")
        servico.finalizar_criacao(it, n, False,
                                  str(f1) if i == 0 else None)
    cj = servico.conjunto_do_acervo(
        "SARDINHA COQUEIRO 125 g TOMATE / OLEO e LIMÃO")
    assert cj is not None
    item = servico.item_do_conjunto("SARDINHA...", "6,90", None, cj)
    assert item.semaforo == "VERDE"
    assert "sabor_sem_foto" in (item.pendencias or [])
    assert "SEM FOTO" in (item.motivo or "")
    # e o PRÉ-VOO conta: 3 sabores anunciados, 1 foto
    d = servico.dados_para_desenho(item)
    assert len(d.sabores) == 3 and len(d.imagens) == 1


def test_v3_arrastar_da_estante_ao_slot(raiz_env):
    """O pedido literal: "pegar da tabela ali da direita e colocar no
    slot que eu quiser". O caminho oficial atribuir_uid_ao_slot: alvo
    vazio recebe; ocupado substitui (o deslocado volta à fila); item já
    na grade + alvo ocupado TROCA; 1 uid = 1 célula; undo desfaz."""
    from app.qt.telas.servico import ItemMesa
    from app.tests.test_os_f11_5 import _mesa_com_grade

    itens = [ItemMesa(f"I{i}", f"{i+1},00", "VERDE", f"Item {i}")
             for i in range(3)]
    m = _mesa_com_grade(raiz_env, itens, n_slots=3)
    c = m.area.canvas
    # a estante anexa o uid ao MIME (identidade, I1)
    md = m.lista.mimeData([m.lista.item(0)])
    assert md.hasFormat("application/x-autotabloide-item-uid")
    uid0 = bytes(md.data("application/x-autotabloide-item-uid")).decode()
    assert uid0.splitlines()[0] == itens[0].uid

    # fila → célula vazia
    m._soltar_item("c0", itens[0].uid)
    assert c.mapa["c0"] == itens[0].uid
    # fila → célula ocupada: SUBSTITUI (o antigo volta à fila)
    m._soltar_item("c0", itens[1].uid)
    assert c.mapa["c0"] == itens[1].uid
    assert itens[0].uid not in c.mapa.values()
    # item na grade → outra célula vazia: MOVE (1 uid = 1 célula)
    m._soltar_item("c2", itens[1].uid)
    assert c.mapa.get("c2") == itens[1].uid
    assert list(c.mapa.values()).count(itens[1].uid) == 1
    # dois na grade → TROCA
    m._soltar_item("c1", itens[2].uid)
    m._soltar_item("c1", itens[1].uid)
    assert c.mapa["c1"] == itens[1].uid
    assert c.mapa["c2"] == itens[2].uid
    # undo desfaz o último gesto (o mapa versiona — D5)
    c.desfazer()
    assert c.mapa["c1"] == itens[2].uid


def test_v3_slot_fixo_recusa_drop(raiz_env):
    """Célula da ARTE nunca recebe produto pelo arrasto — o item
    entraria no mapa e sumiria da página em silêncio (I2)."""
    from app.qt.telas.servico import ItemMesa
    from app.tests.test_os_f11_5 import _mesa_com_grade

    itens = [ItemMesa("I0", "1,00", "VERDE", "Item 0")]
    m = _mesa_com_grade(raiz_env, itens, n_slots=2)
    c = m.area.canvas
    c._layout.paginas[0].slots[1].fixa = True     # vira célula da arte
    assert not c.atribuir_uid_ao_slot("c1", itens[0].uid)
    assert "c1" not in c.mapa


def test_v3_vitrine_dominante_na_frente():
    """"Continua minúsculo e ruim": no leque novo a 1ª foto DOMINA
    (~80% da zona) e fica NA FRENTE; as traseiras mostram o ombro. E o
    TETO por geometria: 6 fotos numa zona de linha não entram todas."""
    from app.rendering.arranjo import ModoArranjo, compor_imagens

    cores = [(230, 40, 40), (40, 230, 40), (40, 40, 230),
             (230, 230, 40), (230, 40, 230), (40, 230, 230)]
    imgs = []
    for c in cores:
        im = Image.new("RGBA", (100, 100), (0, 0, 0, 0))
        # produto ~75% do canvas (o packshot padrão do acervo)
        Image.Image.paste(im, Image.new("RGBA", (74, 74), c + (255,)),
                          (13, 13))
        imgs.append(im)

    zona = compor_imagens(imgs[:3], 178, 116, ModoArranjo.LEQUE)
    # o CENTRO é da dominante (a 1ª, vermelha) — antes ela ia ao fundo
    r, g, b, a = zona.getpixel((89, 70))
    assert a > 0 and r > 180 and g < 120, (r, g, b, a)
    # a dominante enche ≥80% da ALTURA da zona (bbox da cor vermelha)
    px = zona.load()
    ys = [y for y in range(116) for x in range(178)
          if px[x, y][3] > 0 and px[x, y][0] > 180 and px[x, y][1] < 120]
    assert ys and (max(ys) - min(ys)) >= 0.75 * 116, \
        f"dominante com {max(ys) - min(ys) if ys else 0}px de altura"
    # os ombros das traseiras aparecem (verde e azul visíveis)
    cores_vistas = set()
    for x in range(0, 178, 2):
        for y in range(0, 116, 2):
            p = px[x, y]
            if p[3] > 0:
                if p[1] > 180 and p[0] < 120:
                    cores_vistas.add("verde")
                if p[2] > 180 and p[0] < 120:
                    cores_vistas.add("azul")
    assert cores_vistas == {"verde", "azul"}, cores_vistas
    # o teto por geometria: 6 fotos → menos que 6 coladas na zona
    zona6 = compor_imagens(imgs, 178, 116, ModoArranjo.LEQUE)
    px6 = zona6.load()
    distintas = set()
    for x in range(0, 178, 2):
        for y in range(0, 116, 2):
            p = px6[x, y]
            if p[3] > 0 and (max(p[:3]) - min(p[:3])) > 100:
                distintas.add((p[0] > 150, p[1] > 150, p[2] > 150))
    assert len(distintas) < 6, "as 6 fotos entraram — o teto não valeu"


def test_v41_celula_de_coluna_elastica(tmp_path):
    """A 5ª prova ("quase descolado, as imagens diminuíram"): a caixa
    de 3 linhas do descritor é RESERVA, não custo — o texto mede o que
    usa, ancora no preço e a FOTO cresce até encostar nele. Descritor
    de 1 linha → foto MAIOR que a original; texto que enche a reserva
    → célula fica como está (a foto nunca diminui)."""
    from app.rendering.model import Regiao, Retangulo, TipoRegiao
    from app.rendering.nome_fit import compactar_coluna
    from app.tests import acervo

    fontes = tmp_path / "fontes"
    fontes.mkdir()
    acervo.copiar_fontes_reais(fontes)
    nome_f = next(fontes.glob("*.ttf")).name
    regioes = [
        # zona_flex como a célula real do Jornal — o compactar tem o
        # MESMO contrato do plano Q1: só célula replanejável (na Sexta
        # Verde, sem flex, a arte do autor manda e nada se move)
        Regiao(TipoRegiao.IMAGEM, Retangulo(0, 0, 47, 26),
               zona_flex=True),
        Regiao(TipoRegiao.NOME, Retangulo(0, 26, 45, 8),
               fonte=nome_f, tamanho_max_pt=13.5, tamanho_min_pt=9),
        Regiao(TipoRegiao.SUBTITULO, Retangulo(0, 34, 45, 10),
               fonte=nome_f, tamanho_max_pt=10, tamanho_min_pt=7),
        Regiao(TipoRegiao.PRECO, Retangulo(10, 45, 26, 11),
               fonte=nome_f),
    ]
    uid_img = regioes[0].uid
    # 1 linha de descritor: a foto CRESCE
    r1 = compactar_coluna(regioes, "Creme Dental", "Kolynos · 90g",
                          "90 g", 192, fontes, {})
    assert r1, "a célula elástica não agiu no caso de 1 linha"
    assert r1[uid_img].alt_mm > 26.0, r1[uid_img]
    # o texto fica ANCORADO no preço (sem vão morto: sub encosta)
    assert abs((r1[regioes[2].uid].y_mm + r1[regioes[2].uid].alt_mm)
               - 45.0) < 1.5
    # descritor que enche a reserva: nada muda (a foto nunca perde)
    r3 = compactar_coluna(
        regioes, "Biscoito",
        "Bulnez e Adoralle · Cream Cracker, Leite, Agua e Sal ou "
        "Maisena · 270 g", "270 g", 192, fontes, {})
    assert not r3 or r3[uid_img].alt_mm >= 26.0
    # célula NÃO-coluna (sem preço) fica intacta
    r4 = compactar_coluna(regioes[:3], "X", "Y", None, 192, fontes, {})
    assert r4 == {}


def test_ordem_arq_a_grade_soma():
    """A LEI da ordem do arquiteto (03/08): ANTES DE MEXER NO MOTOR,
    SOME A TABELA. Cinco rodadas caçaram no foto_fit/nome_fit uma
    sobreposição que estava em 2 linhas de geometria: célula de
    55,3 mm em passo de 53,5 mm (folga −1,8 mm — o Suco de Uva sobre
    o preço da Rosquinha). Este guardião SOMA a grade do Jornal: toda
    emenda com folga ≥ 0 e o passo UNIFORME dentro de cada página."""
    from pathlib import Path

    from app.rendering.encartes import layout_de_encarte
    from app.rendering.model import TipoRegiao

    pacote = Path(__file__).resolve().parents[2] / "Templates novos"
    if not pacote.is_dir():
        import pytest
        pytest.skip("REQUER ACERVO DO DONO: a pasta 'Templates novos/'")
    lay = layout_de_encarte("jornal-do-mes", pacote)
    for pi, pag in enumerate(lay.paginas, 1):
        celulas = []
        for s in pag.slots:
            if not any(r.tipo == TipoRegiao.PRECO for r in s.regioes):
                continue
            if not any(r.tipo == TipoRegiao.SUBTITULO
                       for r in s.regioes):
                continue
            topo = min(r.rect.y_mm for r in s.regioes)
            fundo = max(r.rect.y_mm + r.rect.alt_mm for r in s.regioes)
            x0 = min(r.rect.x_mm for r in s.regioes)
            x1 = max(r.rect.x_mm + r.rect.larg_mm for r in s.regioes)
            celulas.append((s.id, topo, fundo, x0, x1))
        # (1) NENHUMA emenda negativa: célula que fica ABAIXO de outra
        # (com sobreposição horizontal real) nasce DEPOIS do fim dela
        for sid_a, t_a, f_a, xa0, xa1 in celulas:
            for sid_b, t_b, f_b, xb0, xb1 in celulas:
                if t_b <= t_a + 1.0:
                    continue             # b não está abaixo de a
                overlap = min(xa1, xb1) - max(xa0, xb0)
                if overlap < 0.5 * min(xa1 - xa0, xb1 - xb0):
                    continue             # colunas diferentes
                assert t_b >= f_a, (
                    f"p{pi}: {sid_b} (y={t_b:.1f}) nasce DENTRO de "
                    f"{sid_a} (fim {f_a:.1f}) — a grade não soma")
        # (2) o passo é UNIFORME entre as fileiras de LINHA (as células
        # da mesma coluna x — o ritmo que o olho procura)
        por_coluna: dict = {}
        for sid, t, f, x0, x1 in celulas:
            por_coluna.setdefault(round(x0), []).append(t)
        for x0, tops in por_coluna.items():
            tops = sorted(tops)
            passos = [round(b - a, 1) for a, b in zip(tops, tops[1:])]
            assert len(set(passos)) <= 1, (
                f"p{pi} coluna x={x0}: passos irregulares {passos}")


def test_ordem_arq_rosquinha_fatorada():
    """A Rosquinha concatenava os nomes quase completos quando a base
    era curta — o sabor é o que DIFERE entre os irmãos."""
    from app.qt.telas.servico import sabores_fatorados

    membros = ["Rosquinha Mabel 600g Coco", "Rosquinha Mabel 600g Leite"]
    assert sabores_fatorados(membros, "Rosquinha") == ["Coco", "Leite"]
    assert sabores_fatorados(membros, "Rosquinha Mabel 600g") == \
        ["Coco", "Leite"]
    # sabor composto fica inteiro no que difere
    assert sabores_fatorados(["Biscoito 270g Agua e Sal",
                              "Biscoito 270g Maisena"], "Biscoito") == \
        ["Agua e Sal", "Maisena"]
    # 1 membro: o prefixo da família decide como sempre
    assert sabores_fatorados(["Sardinha Coqueiro 125g Tomate"],
                             "Sardinha Coqueiro 125g") == ["Tomate"]


def test_ordem_arq_carimbo_nunca_hifeniza(tmp_path, monkeypatch):
    """"SUPER OFER-TA" saiu na capa quando o Archivo-Bold (mais largo)
    entrou no preço: carimbo é SELO, não prosa — o ramo multi_preco
    desenha SEMPRE com sem_hifen (o corpo cede ou quebra por palavra)."""
    from app.rendering import compositor as comp
    from app.rendering.model import (FormaPreco, Regiao, Retangulo,
                                     TipoRegiao)
    from app.tests import acervo
    from PIL import Image, ImageDraw

    fontes = tmp_path / "fontes"
    fontes.mkdir()
    acervo.copiar_fontes_reais(fontes)
    nome_f = next(fontes.glob("*.ttf")).name

    vistos = []
    original = comp._desenhar_texto

    def espiao(base, draw, reg, texto, dpi, fontes_dir):
        vistos.append((texto, reg.sem_hifen))
        return original(base, draw, reg, texto, dpi, fontes_dir)

    monkeypatch.setattr(comp, "_desenhar_texto", espiao)
    reg = Regiao(TipoRegiao.PRECO, Retangulo(0, 0, 22, 12),
                 fonte=nome_f, tamanho_max_pt=14, tamanho_min_pt=8,
                 forma_preco=FormaPreco.TEXTO)
    base = Image.new("RGB", (200, 120), "white")
    dados = comp.DadosProduto(nome="Arroz", multi_preco="SUPER OFERTA")
    comp._desenhar_preco(base, ImageDraw.Draw(base), reg, dados, 96,
                         fontes)
    assert vistos, "o carimbo não desenhou"
    texto, sem_hifen = vistos[0]
    assert texto == "SUPER OFERTA" and sem_hifen is True, vistos


def test_errata_guardiao_de_tinta_do_cinza(tmp_path):
    """ERRATA §13.4: cor pedida se prova CONTANDO PIXEL na página
    composta, nunca lendo o diff. O cinza velho #6E675C não pode ter
    UM pixel na p2 do Jornal; o novo #4A443B aparece em quantidade
    (o descritor de venda das 22 células). O mesmo comando que o
    arquiteto rodou na reauditoria."""
    from collections import Counter
    from decimal import Decimal
    from pathlib import Path

    from app.rendering.compositor import DadosProduto, compor_pagina
    from app.rendering.encartes import layout_de_encarte
    from app.rendering.model import TipoRegiao

    pacote = Path(__file__).resolve().parents[2] / "Templates novos"
    if not pacote.is_dir():
        import pytest
        pytest.skip("REQUER ACERVO DO DONO: a pasta 'Templates novos/'")
    lay = layout_de_encarte("jornal-do-mes", pacote)
    pag = lay.paginas[1]                 # a p2 (a página da errata)
    dados = {}
    for s in pag.slots:
        if not any(r.tipo == TipoRegiao.IMAGEM and
                   getattr(r, "ocupavel", True) for r in s.regioes):
            continue
        dados[s.id] = DadosProduto(
            nome="Produto de Bancada",
            descritor="Marca da Casa · Sabor Clássico · 500 g",
            preco_por=Decimal("9.99"))
    img = compor_pagina(lay, pag, dados).convert("RGB")
    c = Counter(img.getdata())
    assert c[(0x6E, 0x67, 0x5C)] == 0, (
        f"o cinza VELHO ainda tem {c[(0x6E, 0x67, 0x5C)]} px de tinta")
    assert c[(0x4A, 0x44, 0x3B)] > 5_000, (
        f"o cinza NOVO só tem {c[(0x4A, 0x44, 0x3B)]} px — cadê o "
        "descritor?")


def test_errata_dica_cita_preco_real_nunca_inventado():
    """ERRATA §13.5: a dica pode citar os preços REAIS da página (o
    exemplo do arquiteto: 'almoço de domingo por menos de R$ 12' com
    6,90+1,50+2,99=11,39 somados e arredondados p/ cima). A guarda
    dura confere número a número: valor que a página não soma segue
    REJEITADO; sem lista de preços, dinheiro segue proibido (o
    comportamento da OS F11.5 #12 intacto)."""
    from app.ai.enriquecimento import dica_alucinada

    nomes = ["Sardinha Coqueiro", "Molho Fugini", "Macarrao Dallas"]
    precos = ["6,90", "1,50", "2,99"]
    boa = "Sardinha + molho Fugini + macarrao: almoco por menos de R$ 12"
    assert dica_alucinada(boa, nomes, (), precos=precos) is False
    exata = "So a sardinha: R$ 6,90 no jantar de sexta"
    assert dica_alucinada(exata, nomes, (), precos=precos) is False
    inventada = "Feijoada completa por R$ 90 com os itens da pagina"
    assert dica_alucinada(inventada, nomes, (), precos=precos) is True
    # sem a lista real, QUALQUER dinheiro é invenção (o contrato antigo)
    assert dica_alucinada(boa, nomes, ()) is True
    # % segue proibido mesmo com preços (desconto é papel do encarte)
    assert dica_alucinada("Leve 2 com 20% off", nomes, (),
                          precos=precos) is True


def test_errata_gerar_dica_manda_nome_e_preco():
    """O modelo VÊ 'nome (R$ preço)' — a errata: nome+preço viajam
    juntos; e a dica devolvida com preço real passa a guarda."""
    from app.ai import enriquecimento as enr

    vistos = {}

    class MotorFake:
        def disponivel(self):
            return True

        def chat(self, mensagens, **kw):
            vistos["user"] = mensagens[1]["content"]
            return '{"dica": "Sardinha com macarrao por R$ 9,89"}'

    dica = enr.gerar_dica(["Sardinha", "Macarrao"], 120, MotorFake(),
                          precos=["6,90", "2,99"])
    assert "Sardinha (R$ 6,90)" in vistos["user"], vistos
    assert dica == "Sardinha com macarrao por R$ 9,89"


def test_duodevicesimus_import_leva_a_arte_e_preserva_o_dono(
        tmp_path, monkeypatch):
    """§0 da DUODEVICESIMUS (o item zero): o banco do dono ficou para
    trás e ninguém tinha PROVA de que o reimport entrega. Este teste
    fecha o §0.3: muda um valor no GERADOR → importa → LÊ O BANCO →
    o valor novo chegou (a ARTE é substituída) E o conteudo_fixo do
    dono sobrevive (a guarda SEPTIMUS). L16: a verdade se lê de onde
    o dono compõe."""
    import json
    from pathlib import Path

    from app.core.database import Database
    from app.core.paths import SystemRoot
    from app.rendering import encartes
    from app.rendering.model import TipoRegiao

    pacote = Path(__file__).resolve().parents[2] / "Templates novos"
    if not pacote.is_dir():
        import pytest
        pytest.skip("REQUER ACERVO DO DONO: a pasta 'Templates novos/'")
    raiz = SystemRoot(tmp_path / "raiz")
    db = Database(raiz).init()
    try:
        with db.Session() as s:
            # 1ª importação (o estado do dono) + o Kit dele num slot
            encartes.importar_pacote(s, pacote, raiz=raiz)
            s.commit()
            from app.core.models import Layout
            reg = s.query(Layout).filter(
                Layout.nome == "Jornal do Mês").one()
            d = json.loads(reg.estrutura_json)
            d["paginas"][1]["slots"][0]["conteudo_fixo"] = {
                "produto_id": 77}
            reg.estrutura_json = json.dumps(d)
            s.commit()
        # o GERADOR muda (a cor do preço — o campo da tabela do §0)
        monkeypatch.setattr(encartes, "_J_LARD", "#123456")
        with db.Session() as s:
            encartes.importar_pacote(s, pacote, raiz=raiz)
            s.commit()
            reg = s.query(Layout).filter(
                Layout.nome == "Jornal do Mês").one()
            d = json.loads(reg.estrutura_json)
            precos = [r.get("cor") for p in d["paginas"]
                      for sl in p["slots"] for r in sl["regioes"]
                      if r.get("tipo") == "PRECO"]
            # a ARTE substituiu: a cor nova do gerador ESTÁ no banco
            assert "#123456" in precos, sorted(set(precos))
            assert "#A85212" not in precos
            # e o conteúdo do DONO sobreviveu ao reimport
            fixo = d["paginas"][1]["slots"][0].get("conteudo_fixo")
            assert fixo == {"produto_id": 77}, fixo
    finally:
        db.engine.dispose()


def test_duodevicesimus_lei_da_proximidade_no_banco(tmp_path):
    """§1 da DUODEVICESIMUS: o preço ENCOSTA na foto do próprio
    produto (sobrepõe o canto — dist < 6 mm) e fica LONGE da foto do
    produto seguinte (> 12 mm). Antes: 17,7 mm do próprio e −1,8 mm
    do seguinte — o olho agrupava errado. L16: medido no LAYOUT DO
    BANCO após o import, o mesmo que o dono compõe — nunca só no
    gerador."""
    from pathlib import Path

    from app.core.database import Database
    from app.core.paths import SystemRoot
    from app.rendering import encartes
    from app.rendering.model import TipoRegiao
    from app.rendering.persistencia import carregar_layout, listar_layouts

    pacote = Path(__file__).resolve().parents[2] / "Templates novos"
    if not pacote.is_dir():
        import pytest
        pytest.skip("REQUER ACERVO DO DONO: a pasta 'Templates novos/'")
    raiz = SystemRoot(tmp_path / "raiz")
    db = Database(raiz).init()
    try:
        with db.Session() as s:
            encartes.importar_pacote(s, pacote, raiz=raiz)
            s.commit()
            reg = next(r for r in listar_layouts(s)
                       if r.nome == "Jornal do Mês")
            lay = carregar_layout(s, reg.id, raiz=raiz)
    finally:
        db.engine.dispose()
    medidas = 0
    for pag in lay.paginas:
        fotos_topo = []
        celulas = []
        for sl in pag.slots:
            img = next((r for r in sl.regioes
                        if r.tipo == TipoRegiao.IMAGEM), None)
            pr = next((r for r in sl.regioes
                       if r.tipo == TipoRegiao.PRECO), None)
            sub = next((r for r in sl.regioes
                        if r.tipo == TipoRegiao.SUBTITULO), None)
            if img is None:
                continue
            fotos_topo.append((img.rect.y_mm, img.rect.x_mm,
                               img.rect.x_mm + img.rect.larg_mm))
            if pr is None or sub is None:
                continue                 # herói/chamada: outra métrica
            celulas.append((sl.id, img, pr))
        for sid, img, pr in celulas:
            base_foto = img.rect.y_mm + img.rect.alt_mm
            topo_preco = pr.rect.y_mm
            base_preco = pr.rect.y_mm + pr.rect.alt_mm
            px0 = pr.rect.x_mm
            px1 = pr.rect.x_mm + pr.rect.larg_mm
            em_coluna = (px1 > img.rect.x_mm
                         and px0 < img.rect.x_mm + img.rect.larg_mm
                         and topo_preco >= img.rect.y_mm)
            if em_coluna:
                # (1) o preço PERTENCE ao produto: encosta na foto
                # (<6 mm — no Jornal ele SOBREPÕE o canto, dist < 0)
                assert topo_preco - base_foto < 6.0, (
                    f"{sid}: preço a {topo_preco - base_foto:.1f} mm "
                    "da própria foto — órfão de novo")
                medidas += 1
            # (2) o preço fica LONGE de qualquer foto SEGUINTE que o
            # cruze na horizontal (>12 mm — o produto do vizinho)
            prox = [t for t, x0, x1 in fotos_topo
                    if t > base_preco - 1.0
                    and x1 > px0 and x0 < px1]
            if prox:
                folga = min(prox) - base_preco
                assert folga > 12.0, (
                    f"{sid}: só {folga:.1f} mm até a foto seguinte")
    assert medidas >= 30, f"só {medidas} células de coluna medidas"


def test_undevicesimus_etiqueta_pousa_no_canto_vazio(tmp_path):
    """§4.1 da UNDEVICESIMUS: a etiqueta que cavalga a foto pousa no
    canto MAIS VAZIO — foto carregada à direita empurra a etiqueta
    para a esquerda; foto carregada à esquerda a deixa onde a arte
    mandou (o canto direito). Por PIXEL na página composta."""
    from decimal import Decimal

    from PIL import Image

    from app.rendering.compositor import DadosProduto, compor_pagina
    from app.rendering.model import (
        AlinhamentoV, Alinhamento, FormaPreco, LayoutDef, Pagina,
        Regiao, Retangulo, Slot, TipoRegiao,
    )
    from app.tests import acervo

    fontes = tmp_path / "fontes"
    fontes.mkdir()
    acervo.copiar_fontes_reais(fontes)
    nome_f = next(fontes.glob("*.ttf")).name

    def _pagina(foto_path):
        sl = Slot("c1", [
            Regiao(TipoRegiao.IMAGEM, Retangulo(10, 10, 90, 60)),
            Regiao(TipoRegiao.PRECO, Retangulo(60, 55, 38, 20),
                   fonte=nome_f, tamanho_max_pt=20,
                   forma_preco=FormaPreco.CARIMBO,
                   forma_cor="#F58634", cor="#A85212"),
        ])
        lay = LayoutDef(120.0, 90.0, dpi=96,
                        paginas=[Pagina(slots=[sl])])
        return lay, lay.paginas[0], {
            "c1": DadosProduto(nome="X", preco_por=Decimal("9.99"),
                               imagem_path=str(foto_path))}

    # foto TODA carregada à DIREITA (tinta onde a etiqueta pousaria)
    f_dir = tmp_path / "dir.png"
    im = Image.new("RGBA", (600, 400), (0, 0, 0, 0))
    im.paste((40, 40, 200, 255), (360, 0, 600, 400))
    im.save(f_dir)
    lay, pag, dados = _pagina(f_dir)
    img = compor_pagina(lay, pag, dados, fontes_dir=fontes).convert("RGB")
    # a metade esquerda da faixa da etiqueta tem o laranja da borda
    def _tem_carimbo(img, x0, x1):
        w = img.width
        faixa = img.crop((int(w * x0), 0, int(w * x1), img.height))
        return any(abs(r - 0xF5) < 30 and abs(g - 0x86) < 40
                   and b < 120 for r, g, b in faixa.getdata())
    assert _tem_carimbo(img, 0.0, 0.45), "a etiqueta não fugiu p/ esq."
    # foto carregada à ESQUERDA: a etiqueta FICA no canto da arte (dir.)
    f_esq = tmp_path / "esq.png"
    im2 = Image.new("RGBA", (600, 400), (0, 0, 0, 0))
    im2.paste((40, 40, 200, 255), (0, 0, 240, 400))
    im2.save(f_esq)
    lay2, pag2, dados2 = _pagina(f_esq)
    img2 = compor_pagina(lay2, pag2, dados2,
                         fontes_dir=fontes).convert("RGB")
    assert _tem_carimbo(img2, 0.5, 1.0), "a etiqueta fugiu sem motivo"


def test_undevicesimus_bloco_unico_variancia_zero(tmp_path):
    """§2/§5.1 da UNDEVICESIMUS: o bloco de texto é UM SÓ — a
    distância nome→descritor é IDÊNTICA em todas as células de linha
    (variância zero) e os dois ancoram no TOPO (a sobra cai embaixo,
    nunca entre eles). O "jogado" tinha nome: duas caixas BASE
    flutuando. L16: lido do layout no BANCO após o import."""
    from pathlib import Path

    from app.core.database import Database
    from app.core.paths import SystemRoot
    from app.rendering import encartes
    from app.rendering.model import AlinhamentoV, TipoRegiao
    from app.rendering.persistencia import carregar_layout, listar_layouts

    pacote = Path(__file__).resolve().parents[2] / "Templates novos"
    if not pacote.is_dir():
        import pytest
        pytest.skip("REQUER ACERVO DO DONO: a pasta 'Templates novos/'")
    raiz = SystemRoot(tmp_path / "raiz")
    db = Database(raiz).init()
    try:
        with db.Session() as s:
            encartes.importar_pacote(s, pacote, raiz=raiz)
            s.commit()
            reg = next(r for r in listar_layouts(s)
                       if r.nome == "Jornal do Mês")
            lay = carregar_layout(s, reg.id, raiz=raiz)
    finally:
        db.engine.dispose()
    gaps = set()
    n = 0
    for pag in lay.paginas:
        for sl in pag.slots:
            nome = next((r for r in sl.regioes
                         if r.tipo == TipoRegiao.NOME), None)
            sub = next((r for r in sl.regioes
                        if r.tipo == TipoRegiao.SUBTITULO), None)
            img = next((r for r in sl.regioes
                        if r.tipo == TipoRegiao.IMAGEM), None)
            if nome is None or sub is None or img is None:
                continue
            # só a família das células de COLUNA (bloco abaixo da
            # foto) — o herói é editorial e a chamada é lateral
            if nome.rect.y_mm < img.rect.y_mm + img.rect.alt_mm - 1.0:
                continue
            # H1: âncora única no TOPO — nos dois
            assert nome.alinhamento_v == AlinhamentoV.TOPO, sl.id
            assert sub.alinhamento_v == AlinhamentoV.TOPO, sl.id
            # H2: a entrelinha é POSIÇÃO (topo a topo), não caixa
            gaps.add(round(sub.rect.y_mm - nome.rect.y_mm, 2))
            n += 1
    assert n >= 30, f"só {n} células medidas"
    assert len(gaps) == 1, f"entrelinhas diferentes: {sorted(gaps)}"


def test_s7_um_eixo_por_coluna_no_banco(tmp_path):
    """§7.2: a decisão B com a correção — texto E foto à ESQUERDA nas
    células de coluna (um eixo só; dois eixos disputando liam como
    desalinho). L16: lido do banco após o import. E §7.4.2: ZERO grau
    na grade (a inclinação ficou só nos destaques da capa)."""
    from pathlib import Path

    from app.core.database import Database
    from app.core.paths import SystemRoot
    from app.rendering import encartes
    from app.rendering.model import Alinhamento, TipoRegiao
    from app.rendering.persistencia import carregar_layout, listar_layouts

    pacote = Path(__file__).resolve().parents[2] / "Templates novos"
    if not pacote.is_dir():
        import pytest
        pytest.skip("REQUER ACERVO DO DONO: a pasta 'Templates novos/'")
    raiz = SystemRoot(tmp_path / "raiz")
    db = Database(raiz).init()
    try:
        with db.Session() as s:
            encartes.importar_pacote(s, pacote, raiz=raiz)
            s.commit()
            reg = next(r for r in listar_layouts(s)
                       if r.nome == "Jornal do Mês")
            lay = carregar_layout(s, reg.id, raiz=raiz)
    finally:
        db.engine.dispose()
    n = 0
    for pag in lay.paginas:
        for sl in pag.slots:
            nome = next((r for r in sl.regioes
                         if r.tipo == TipoRegiao.NOME), None)
            sub = next((r for r in sl.regioes
                        if r.tipo == TipoRegiao.SUBTITULO), None)
            img = next((r for r in sl.regioes
                        if r.tipo == TipoRegiao.IMAGEM), None)
            pr = next((r for r in sl.regioes
                       if r.tipo == TipoRegiao.PRECO), None)
            if None in (nome, sub, img, pr):
                continue
            if nome.rect.y_mm < img.rect.y_mm + img.rect.alt_mm - 1.0:
                continue                 # herói/chamada: outra família
            assert nome.alinhamento == Alinhamento.ESQUERDA, sl.id
            assert sub.alinhamento == Alinhamento.ESQUERDA, sl.id
            # VICESIMUS-PRIMUS/P1 (supera o §7.2 DE PROPÓSITO): a
            # FOTO centra (o centro óptico é do motor) — só o TEXTO
            # é tipográfico e assenta na margem (L18)
            assert img.alinhamento == Alinhamento.CENTRO, sl.id
            assert pr.rotacao_graus == 0.0, (sl.id, pr.rotacao_graus)
            n += 1
    assert n >= 30, f"só {n} células medidas"


def test_s7_dica_ou_texto_ou_nada(tmp_path):
    """§7.4.3: a caixa do Fica a Dica saiu da ARTE — COM dica o app
    desenha a moldura + chip verde; SEM dica, NADA na página (caixa
    vazia com pautas lia como falha de impressão). Por pixel."""
    from collections import Counter

    from PIL import Image

    from app.rendering.compositor import DadosProduto, compor_pagina
    from app.rendering.model import (
        LayoutDef, Pagina, PapelTexto, Regiao, Retangulo, Slot,
        TipoRegiao,
    )
    from app.tests import acervo

    fontes = tmp_path / "fontes"
    fontes.mkdir()
    acervo.copiar_fontes_reais(fontes)
    nome_f = next(fontes.glob("*.ttf")).name

    def _pagina(texto):
        sl = Slot("d1", [
            Regiao(TipoRegiao.TEXTO_LEGAL, Retangulo(40, 40, 90, 20),
                   papel_texto=PapelTexto.DICA, texto_fixo=texto,
                   fonte=nome_f, tamanho_max_pt=10),
        ])
        lay = LayoutDef(180.0, 120.0, dpi=96,
                        paginas=[Pagina(slots=[sl])])
        return lay, lay.paginas[0]

    verde = (0x0F, 0x78, 0x3F)
    lay, pag = _pagina("Sardinha com macarrão rende almoço.")
    img = compor_pagina(lay, pag, {"d1": DadosProduto(nome="X")},
                        fontes_dir=fontes).convert("RGB")
    c = Counter(img.getdata())
    assert c[verde] > 500, f"o chip verde não desenhou ({c[verde]}px)"
    lay2, pag2 = _pagina("")
    img2 = compor_pagina(lay2, pag2, {"d1": DadosProduto(nome="X")},
                         fontes_dir=fontes).convert("RGB")
    c2 = Counter(img2.getdata())
    assert c2[verde] == 0, "dica VAZIA desenhou moldura"


def test_vicesimus_a_zona_e_em_pe(tmp_path):
    """L17 da VICESIMUS: ANTES DE ESCALAR, MEÇA A PROPORÇÃO — a zona
    de foto de encarte de mercado nunca é mais larga que alta demais
    (proporção ≤ 1,2; estava 1,53 e o produto em pé parava na altura
    com 71% da caixa vazia). Teste de TABELA, lido do banco (L16)."""
    from pathlib import Path

    from app.core.database import Database
    from app.core.paths import SystemRoot
    from app.rendering import encartes
    from app.rendering.model import TipoRegiao
    from app.rendering.persistencia import carregar_layout, listar_layouts

    pacote = Path(__file__).resolve().parents[2] / "Templates novos"
    if not pacote.is_dir():
        import pytest
        pytest.skip("REQUER ACERVO DO DONO: a pasta 'Templates novos/'")
    raiz = SystemRoot(tmp_path / "raiz")
    db = Database(raiz).init()
    try:
        with db.Session() as s:
            encartes.importar_pacote(s, pacote, raiz=raiz)
            s.commit()
            reg = next(r for r in listar_layouts(s)
                       if r.nome == "Jornal do Mês")
            lay = carregar_layout(s, reg.id, raiz=raiz)
    finally:
        db.engine.dispose()
    n = 0
    for pag in lay.paginas:
        for sl in pag.slots:
            img = next((r for r in sl.regioes
                        if r.tipo == TipoRegiao.IMAGEM), None)
            nome = next((r for r in sl.regioes
                         if r.tipo == TipoRegiao.NOME), None)
            if img is None or nome is None:
                continue
            if nome.rect.y_mm < img.rect.y_mm + img.rect.alt_mm - 1.0:
                continue                 # herói/chamada: outra família
            prop = img.rect.larg_mm / img.rect.alt_mm
            assert prop <= 1.2, (
                f"{sl.id}: zona DEITADA ({prop:.2f}) — o produto em "
                "pé para na altura")
            n += 1
    assert n >= 30, f"só {n} zonas medidas"


def test_vicesimus_etiqueta_encostada_e_sem_barriga(tmp_path):
    """§3.1/§3.2 da VICESIMUS (pelas silhuetas e pousos REGISTRADOS
    na composição): a etiqueta AO LADO fica ENCOSTADA (folga ≤ 3 mm
    da tinta) e a que morde nunca invade mais de 25% da tinta do
    produto — nas duas geometrias (garrafa estreita e saco largo)."""
    from decimal import Decimal

    from PIL import Image

    from app.rendering.compositor import (DadosProduto, compor_pagina,
                                          mm_para_px)
    from app.rendering.model import (
        FormaPreco, LayoutDef, Pagina, Regiao, Retangulo, Slot,
        TipoRegiao,
    )
    from app.tests import acervo

    fontes = tmp_path / "fontes"
    fontes.mkdir()
    acervo.copiar_fontes_reais(fontes)
    nome_f = next(fontes.glob("*.ttf")).name

    from app.rendering.model import Ajuste

    def _celula(sid, x0, foto_path):
        return Slot(sid, [
            Regiao(TipoRegiao.IMAGEM, Retangulo(x0, 10, 47, 40),
                   ajuste=Ajuste.ASSENTAR),
            Regiao(TipoRegiao.PRECO, Retangulo(x0 + 23, 40, 25, 11),
                   fonte=nome_f, tamanho_max_pt=20,
                   forma_preco=FormaPreco.CARIMBO,
                   forma_cor="#F58634", cor="#A85212"),
        ])

    garrafa = tmp_path / "garrafa.png"
    im = Image.new("RGBA", (200, 800), (0, 0, 0, 0))
    im.paste((60, 60, 160, 255), (60, 0, 140, 800))
    im.save(garrafa)
    saco = tmp_path / "saco.png"
    im2 = Image.new("RGBA", (700, 600), (0, 0, 0, 0))
    im2.paste((200, 170, 40, 255), (10, 10, 690, 590))
    im2.save(saco)
    lay = LayoutDef(120.0, 70.0, dpi=96, paginas=[Pagina(slots=[
        _celula("estreita", 5, garrafa), _celula("larga", 60, saco)])])
    pag = lay.paginas[0]
    dados = {
        "estreita": DadosProduto(nome="G", preco_por=Decimal("9.99"),
                                 imagem_path=str(garrafa)),
        "larga": DadosProduto(nome="S", preco_por=Decimal("9.99"),
                              imagem_path=str(saco)),
    }
    img = compor_pagina(lay, pag, dados, fontes_dir=fontes)
    sils = img._silhuetas
    pousos = img._pousos
    ppm = mm_para_px(1.0, 96)
    for sl in pag.slots:
        rimg, rpr = sl.regioes
        ox, oy, nw, nh = sils[rimg.uid]
        sx0, sx1 = ox / ppm, (ox + nw) / ppm
        sy0, sy1 = oy / ppm, (oy + nh) / ppm
        pr = pousos[rpr.uid]
        ix = max(0.0, min(pr.x_mm + pr.larg_mm, sx1) - max(pr.x_mm, sx0))
        iy = max(0.0, min(pr.y_mm + pr.alt_mm, sy1) - max(pr.y_mm, sy0))
        inv = (ix * iy) / max((sx1 - sx0) * (sy1 - sy0), 1e-6)
        assert inv <= 0.25, f"{sl.id}: invade {inv:.0%} da tinta"
        if ix * iy <= 0:                 # pousou AO LADO: encostada
            folga = max(pr.x_mm - sx1, sx0 - (pr.x_mm + pr.larg_mm))
            assert folga <= 3.0, f"{sl.id}: a {folga:.1f} mm da tinta"


def test_vprimus_linha_de_chao(tmp_path):
    """P5 da VICESIMUS-PRIMUS: numa fileira as BASES se alinham (a
    gôndola) — a garrafa em pé e o pacote deitado pisam no mesmo
    chão. O plano Q1 punha a foto deitada no TOPO (arranjo vertical)
    quando o preço morde a foto — célula com mordida tem identidade
    própria e NUNCA é reordenada."""
    from decimal import Decimal

    from PIL import Image

    from app.rendering.compositor import (DadosProduto, compor_pagina,
                                          mm_para_px)
    from app.rendering.model import (
        Ajuste, AlinhamentoV, FormaPreco, LayoutDef, Pagina, Regiao,
        Retangulo, Slot, TipoRegiao,
    )
    from app.tests import acervo

    fontes = tmp_path / "fontes"
    fontes.mkdir()
    acervo.copiar_fontes_reais(fontes)
    nome_f = next(fontes.glob("*.ttf")).name

    def _celula(sid, x0, foto):
        return Slot(sid, [
            Regiao(TipoRegiao.IMAGEM, Retangulo(x0, 10, 42, 37),
                   ajuste=Ajuste.ASSENTAR, zona_flex=True),
            Regiao(TipoRegiao.PRECO, Retangulo(x0 + 20, 33, 24, 11),
                   fonte=nome_f, tamanho_max_pt=18,
                   forma_preco=FormaPreco.CARIMBO,
                   forma_cor="#F58634", cor="#A85212"),
            Regiao(TipoRegiao.NOME, Retangulo(x0, 51, 42, 6),
                   fonte=nome_f, tamanho_max_pt=12,
                   alinhamento_v=AlinhamentoV.TOPO),
        ])

    garrafa = tmp_path / "g.png"
    im = Image.new("RGBA", (200, 800), (0, 0, 0, 0))
    im.paste((60, 60, 160, 255), (60, 0, 140, 800))
    im.save(garrafa)
    deitado = tmp_path / "d.png"
    im2 = Image.new("RGBA", (800, 220), (0, 0, 0, 0))
    im2.paste((190, 60, 40, 255), (10, 10, 790, 210))
    im2.save(deitado)
    lay = LayoutDef(110.0, 70.0, dpi=96, paginas=[Pagina(slots=[
        _celula("empe", 5, garrafa), _celula("deitada", 55, deitado)])])
    pag = lay.paginas[0]
    dados = {
        "empe": DadosProduto(nome="G", preco_por=Decimal("9.99"),
                             imagem_path=str(garrafa)),
        "deitada": DadosProduto(nome="D", preco_por=Decimal("9.99"),
                                imagem_path=str(deitado)),
    }
    img = compor_pagina(lay, pag, dados, fontes_dir=fontes)
    ppm = mm_para_px(1.0, 96)
    bases = []
    for sl in pag.slots:
        rimg = sl.regioes[0]
        _ox, oy, _nw, nh = img._silhuetas[rimg.uid]
        bases.append((oy + nh) / ppm)
    assert abs(bases[0] - bases[1]) <= 1.0, (
        f"bases desalinhadas: {bases} — a deitada flutuou")

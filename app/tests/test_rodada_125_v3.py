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

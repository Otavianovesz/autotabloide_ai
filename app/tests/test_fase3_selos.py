"""FASE 3, Bloco G — o gestor de SELOS como entidade (passos 63-78).

Adversarial por CONTEÚDO (pixel), nunca por "não deu exceção" (I5)."""

from decimal import Decimal

import pytest
from PIL import Image

from app.rendering.compositor import DadosProduto, compor_pagina
from app.rendering.model import (
    LayoutDef, Pagina, Regiao, Retangulo, Slot, TipoRegiao,
)

DPI = 96
PX_MM = DPI / 25.4


@pytest.fixture()
def raiz_tmp(tmp_path, monkeypatch):
    monkeypatch.setenv("AUTOTABLOIDE_ROOT", str(tmp_path / "raiz"))
    from app.core.database import Database
    from app.core.paths import SystemRoot

    root = SystemRoot(tmp_path / "raiz").criar_estrutura()
    Database(root).init().engine.dispose()
    return root


def _sessao():
    from app.core.database import Database
    return Database().init()


def test_migracao_semeia_automaticos_e_importa_legado(raiz_tmp):
    """Passo 64: idempotente; os 2 automáticos nascem; a Config legada
    `selos.personalizados` vira linha manual sem duplicar."""
    from app.core.models import Selo
    from app.core.repositories import ConfigRepositorio
    from app.core.selos import migrar_selos

    db = _sessao()
    try:
        with db.Session() as s:
            ConfigRepositorio(s).set("selos.personalizados",
                                     [{"nome": "Legado", "arquivo": "l.png",
                                       "canto": "INFERIOR_ESQUERDO"}])
            n1 = migrar_selos(s)
            n2 = migrar_selos(s)                 # roda de novo: nada cria
            s.commit()
            todos = s.query(Selo).all()
    finally:
        db.engine.dispose()
    assert n1 == 3 and n2 == 0
    regras = {x.regra for x in todos if x.tipo == "automatico"}
    assert regras == {"bebida_alcoolica", "marca_propria"}
    manual = next(x for x in todos if x.tipo == "manual")
    assert manual.nome == "Legado" and manual.canto == "INFERIOR_ESQUERDO"


def test_selo_manual_do_gestor_compoe_por_pixel(raiz_tmp):
    """Passo 75: criar no GESTOR (tabela) → aplicar ao item → compor →
    o selo está NA ÂNCORA, por pixel."""
    from app.qt.telas import servico

    arte = raiz_tmp.raiz / "arte.png"
    Image.new("RGBA", (80, 80), "#FF00FF").save(arte)
    servico.adicionar_selo_personalizado("Muito Barato", str(arte))

    extras = servico.selos_do_item(["Muito Barato"])
    assert len(extras) == 1
    reg_img = Regiao(TipoRegiao.IMAGEM, Retangulo(10, 10, 60, 60), nome="Img")
    lay = LayoutDef(100, 100, dpi=DPI,
                    paginas=[Pagina([Slot("c", [reg_img])])])
    d = DadosProduto("Produto", preco_por=Decimal("1.00"),
                     selos_extra=extras)
    img = compor_pagina(lay, lay.paginas[0], {"c": d})
    x = round((10 + 60) * PX_MM) - 20
    y = round(10 * PX_MM) + 20
    r, g, b = img.getpixel((x, y))[:3]
    assert r > 200 and b > 200 and g < 80          # o magenta do selo


def test_mais18_automatico_sai_sempre_mesmo_desligando(raiz_tmp):
    """Passo 76 + decisão travada: bebida alcoólica SEMPRE leva +18 — e a
    tentativa de desligar a regra é RECUSADA pelo gestor."""
    from app.core.models import Selo
    from app.core.selos import REGRA_MAIS18, definir_ativo, migrar_selos

    db = _sessao()
    try:
        with db.Session() as s:
            migrar_selos(s)
            m18 = s.query(Selo).filter_by(regra=REGRA_MAIS18).one()
            assert definir_ativo(s, m18.id, False) is False   # recusa
            assert s.get(Selo, m18.id).ativo is True
            s.commit()
    finally:
        db.engine.dispose()

    reg_img = Regiao(TipoRegiao.IMAGEM, Retangulo(10, 10, 60, 60), nome="Img")
    lay = LayoutDef(100, 100, dpi=DPI,
                    paginas=[Pagina([Slot("c", [reg_img])])])
    d = DadosProduto("Cerveja", preco_por=Decimal("3.99"), mais18=True)
    img = compor_pagina(lay, lay.paginas[0], {"c": d})
    # canto SUPERIOR_ESQUERDO da âncora: o vermelho do badge +18
    x = round(10 * PX_MM) + 20
    y = round(10 * PX_MM) + 20
    r, g, b = img.getpixel((x, y))[:3]
    assert r > 150 and g < 100 and b < 100         # vermelho do +18


def test_regra_qualidade_desligada_nao_compoe(raiz_tmp):
    """Passo 66/71: desligar a regra do Qualidade tira o selo do desenho
    (por pixel) — sem tocar a flag do produto."""
    from app.core.models import Selo
    from app.core.selos import REGRA_QUALIDADE, definir_ativo, migrar_selos

    reg_img = Regiao(TipoRegiao.IMAGEM, Retangulo(10, 10, 60, 60), nome="Img")
    lay = LayoutDef(100, 100, dpi=DPI,
                    paginas=[Pagina([Slot("c", [reg_img])])])
    d = DadosProduto("Arroz BBX", preco_por=Decimal("5.00"),
                     marca_propria=True)
    x = round((10 + 60) * PX_MM) - 20              # canto SUP_DIREITO
    y = round(10 * PX_MM) + 20

    db = _sessao()
    try:
        with db.Session() as s:
            migrar_selos(s)
            s.commit()
    finally:
        db.engine.dispose()
    com = compor_pagina(lay, lay.paginas[0], {"c": d}).getpixel((x, y))[:3]

    db = _sessao()
    try:
        with db.Session() as s:
            q = s.query(Selo).filter_by(regra=REGRA_QUALIDADE).one()
            assert definir_ativo(s, q.id, False) is True
            s.commit()
    finally:
        db.engine.dispose()
    sem = compor_pagina(lay, lay.paginas[0], {"c": d}).getpixel((x, y))[:3]
    assert com != sem                              # o selo sumiu do canto
    assert sem == (255, 255, 255)                  # voltou o fundo branco


def test_lei_da_casa_com_gestor_em_tabela(raiz_tmp):
    """Passo 77 (LEI DA CASA, 5ª aplicação): com a TABELA populada e selo
    manual aplicado, região SELO segue não-ocupável e o pré-voo imune —
    nenhum item-fantasma nasce."""
    from app.qt.telas import servico
    from app.rendering.grade import ocupaveis

    arte = raiz_tmp.raiz / "a.png"
    Image.new("RGBA", (40, 40), "#00FF00").save(arte)
    servico.adicionar_selo_personalizado("Destaque", str(arte))

    reg_img = Regiao(TipoRegiao.IMAGEM, Retangulo(10, 10, 60, 60), nome="Img")
    reg_selo = Regiao(TipoRegiao.SELO, Retangulo(70, 10, 20, 20),
                      nome="Selo")
    lay = LayoutDef(100, 100, dpi=DPI,
                    paginas=[Pagina([Slot("c", [reg_img, reg_selo])])])
    ocup = ocupaveis(lay.paginas[0].slots)
    assert [s.id for s in ocup] == ["c"]           # 1 célula, nunca 2
    foto = raiz_tmp.raiz / "foto.png"
    Image.new("RGB", (60, 60), "#123456").save(foto)
    d_com = DadosProduto("P", preco_por=Decimal("1"),
                         imagem_path=str(foto),
                         selos_extra=servico.selos_do_item(["Destaque"]))
    avisos = servico.validar_composicao(lay, {"c": d_com})
    assert not any("selo" in str(a).lower() for a in avisos)


def test_selo_sem_arte_avisa_no_prevoo(raiz_tmp):
    """Passo 73 (I2): selo escolhido cuja ARTE sumiu do disco → aviso
    visível no pré-voo, nunca quadrado vazio silencioso."""
    from app.qt.telas import servico

    arte = raiz_tmp.raiz / "b.png"
    Image.new("RGBA", (40, 40), "#0000FF").save(arte)
    servico.adicionar_selo_personalizado("Sumido", str(arte))
    (raiz_tmp.selos / "sumido.png").unlink()       # a arte some do disco

    reg_img = Regiao(TipoRegiao.IMAGEM, Retangulo(10, 10, 60, 60), nome="Img")
    lay = LayoutDef(100, 100, dpi=DPI,
                    paginas=[Pagina([Slot("c", [reg_img])])])
    foto = raiz_tmp.raiz / "foto.png"
    Image.new("RGB", (60, 60), "#123456").save(foto)
    d = DadosProduto("P", preco_por=Decimal("1"), imagem_path=str(foto),
                     selos_extra=servico.selos_do_item(["Sumido"]))
    avisos = servico.validar_composicao(lay, {"c": d})
    assert any("selo" in str(a).lower() and "sumido" in str(a).lower()
               for a in avisos)


# --- Bloco H: manutenção (passos 87-89) -----------------------------------------------


def test_verificar_instalacao_saudavel_essenciais_verdes(raiz_tmp):
    """Passo 87 (R-134): raiz recém-criada = todos os ESSENCIAIS verdes
    (a IA é opcional — fora do ar não reprova a instalação)."""
    from app.core.manutencao import verificar_instalacao

    # a raiz de teste não tem fonte — planta a Roboto de mentira
    (raiz_tmp.fontes / "Roboto-Regular.ttf").write_bytes(b"fake")
    itens = verificar_instalacao(raiz_tmp.raiz)
    essenciais = [i for i in itens if i["essencial"]]
    assert len(essenciais) == 3
    assert all(i["ok"] for i in essenciais), [
        (i["nome"], i["detalhe"]) for i in essenciais if not i["ok"]]
    assert any(not i["essencial"] for i in itens)      # a IA aparece


def test_integridade_quarentena_orfa_sem_apagar(raiz_tmp):
    """Passo 88 (R-129): foto órfã plantada é detectada e vai para a
    quarentena — o ARQUIVO CONTINUA EXISTINDO (nunca apaga)."""
    from app.core.database import Database
    from app.core.manutencao import (
        PASTA_QUARENTENA, quarentenar_orfas, verificar_acervo,
    )
    from app.core.models import Produto

    db = Database().init()
    try:
        with db.Session() as s:
            s.add(Produto(nome_bruto="ARROZ", nome_sanitizado="Arroz",
                          caminho_imagem="arroz/foto.png"))
            s.commit()
    finally:
        db.engine.dispose()
    bib = raiz_tmp.biblioteca_imagens
    (bib / "arroz").mkdir(parents=True, exist_ok=True)
    Image.new("RGB", (10, 10), "red").save(bib / "arroz" / "foto.png")
    (bib / "solta").mkdir(parents=True, exist_ok=True)
    Image.new("RGB", (10, 10), "blue").save(bib / "solta" / "orfa.png")

    r = verificar_acervo(raiz_tmp.raiz)
    assert [str(p).replace("\\", "/") for p in r["orfas"]] == [
        "solta/orfa.png"]
    assert r["sem_arquivo"] == []

    n = quarentenar_orfas(r["orfas"], raiz_tmp.raiz)
    assert n == 1
    assert not (bib / "solta" / "orfa.png").exists()
    assert (bib / PASTA_QUARENTENA / "solta" / "orfa.png").exists()  # vivo
    # 2ª rodada: nada órfão (a quarentena não conta como órfã)
    assert verificar_acervo(raiz_tmp.raiz)["orfas"] == []


def test_perfil_maquina_fraca_liga_as_4_chaves(raiz_tmp):
    """Passo 89 (R-132): UM toggle liga as 4 chaves; desligar devolve os
    padrões — e o interruptor da IA obedece de verdade."""
    from app.ai.client import ConfigIA
    from app.core.database import Database
    from app.core.manutencao import ativar_perfil_maquina_fraca
    from app.core.repositories import ConfigRepositorio

    ativar_perfil_maquina_fraca(True, raiz_tmp.raiz)
    db = Database().init()
    try:
        with db.Session() as s:
            cfg = ConfigRepositorio(s)
            assert cfg.get("aparencia.animacoes") == "reduzidas"
            assert cfg.get("aparencia.transparencias") == "reduzidas"
            assert cfg.get("ia.usar") is False
            assert cfg.get("imagem.upscale_auto") is False
            assert cfg.get("aparencia.maquina_fraca") is True
    finally:
        db.engine.dispose()
    assert ConfigIA.da_config().usar is False          # consumo real

    ativar_perfil_maquina_fraca(False, raiz_tmp.raiz)
    db = Database().init()
    try:
        with db.Session() as s:
            cfg = ConfigRepositorio(s)
            assert cfg.get("aparencia.animacoes") == "ligadas"
            assert cfg.get("ia.usar") is True
            assert cfg.get("imagem.upscale_auto") is True
    finally:
        db.engine.dispose()


def test_contador_de_erros_e_top3(raiz_tmp):
    """Passo 84 (R-133): registrar soma; top_erros ordena decrescente."""
    from app.core.manutencao import registrar_erro, top_erros

    for _ in range(3):
        registrar_erro("exportar_pdf", raiz_tmp.raiz)
    registrar_erro("buscar_imagem", raiz_tmp.raiz)
    top = top_erros(3, raiz_tmp.raiz)
    assert top[0] == ("exportar_pdf", 3)
    assert ("buscar_imagem", 1) in top

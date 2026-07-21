"""D-B3 (ORDEM_BLOCO_D) — teste ADVERSARIAL da portabilidade (I5).

Roundtrip completo entre duas raízes simulando casa↔mercado. A conferência é
sempre POR CONTEÚDO (bytes da foto, valores) e POR CHAVE NATURAL (nunca por
id): cada produto tem foto de cor única — mesclagem que trocar foto de lugar
é flagrada byte a byte. A sequência é a da ordem, na letra:

  exportar de A → importar em B vazio → alterar em B (novo, preço, foto) →
  exportar de B → importar de volta em A com mesclagem (conflitos no
  relatório, decisões aplicadas, NENHUMA foto trocada) → importar o MESMO
  pacote duas vezes (idempotente, zero duplicatas).
"""

from decimal import Decimal

import pytest
from sqlalchemy import select

from app.core import portabilidade as porta
from app.core.database import Database
from app.core.models import Produto
from app.core.portabilidade import Decisao
from app.tests import seeds_portabilidade as seeds

CORES = {
    ("Coca-Cola 2L", "Coca-Cola"): "#FF0000",
    ("Arroz 5kg", "Camil"): "#00FF00",
    ("Cerveja Amstel 269ml", "Amstel"): "#0000FF",
    ("Feijão 1kg", "Kicaldo"): "#FFFF00",
}
ARROZ_FOTO_NOVA = "#00FFFF"


def _semear_casa(tmp_path):
    """Raiz A ("casa"): 3 produtos com foto única + layout + projeto + fonte."""
    a = seeds.raiz(tmp_path, "casa")
    seeds.add_produto(a, "Coca-Cola 2L", "Coca-Cola", "8.99",
                      seeds.png(CORES[("Coca-Cola 2L", "Coca-Cola")]),
                      categoria="Bebidas", aliases=("COCA COLA 2LT",))
    seeds.add_produto(a, "Arroz 5kg", "Camil", "24.90",
                      seeds.png(CORES[("Arroz 5kg", "Camil")]),
                      categoria="Mercearia")
    seeds.add_produto(a, "Cerveja Amstel 269ml", "Amstel", "2.99",
                      seeds.png(CORES[("Cerveja Amstel 269ml", "Amstel")]),
                      categoria="Bebidas", mais18=True)
    arte = tmp_path / "arte_frente.png"
    arte.write_bytes(seeds.png("#ABCDEF"))
    lid = seeds.add_layout_com_arte(a, "Tabloide Quintou", arte)
    seeds.add_projeto(a, "Quintou 09/07", lid)
    (a.fontes / "MinhaFonte.ttf").write_bytes(b"fonte-de-mentira")
    return a


def _mudar_preco(root, nome, marca, novo: str) -> None:
    db = Database(root).init()
    try:
        with db.Session() as s:
            for p in s.execute(select(Produto)).scalars():
                if porta.chave_natural(p.nome_sanitizado, p.marca) == \
                        porta.chave_natural(nome, marca):
                    p.preco_atual = Decimal(novo)
            s.commit()
    finally:
        db.engine.dispose()


def _trocar_foto(root, nome, marca, cor: str) -> None:
    p = seeds.produto_por_chave(root, nome, marca)
    (root.biblioteca_imagens / p["caminho_imagem"]).write_bytes(seeds.png(cor))


def test_d_b3_roundtrip_casa_mercado(tmp_path):
    casa = _semear_casa(tmp_path)
    mercado = seeds.raiz(tmp_path, "mercado")

    # --- exportar de A -------------------------------------------------------------
    pkg1 = porta.exportar_pacote(tmp_path / "casa_para_mercado", casa)
    assert pkg1.suffix == ".atpkg" and pkg1.exists()

    # I3: a cópia do banco que viaja NÃO carrega caminho de máquina na arte
    import sqlite3
    import zipfile
    with zipfile.ZipFile(pkg1) as z:
        nomes = z.namelist()
        assert "manifesto.json" in nomes and "banco/core.db" in nomes
        assert any(n.startswith("layouts_arte/") for n in nomes)
        assert any(n.startswith("projetos/") for n in nomes)
        z.extract("banco/core.db", tmp_path / "espiar")
    conn = sqlite3.connect(tmp_path / "espiar" / "banco" / "core.db")
    fundos = [r[0] for r in
              conn.execute("SELECT arquivo_fundo FROM layouts").fetchall()]
    conn.close()
    assert all(f is None or f.startswith("layouts_arte/") for f in fundos)

    # --- importar em B VAZIO -------------------------------------------------------
    with porta.analisar_pacote(pkg1, mercado) as analise:
        assert len(analise.novos) == 3 and not analise.conflitos
        assert len(analise.projetos_novos) == 1
        assert analise.layouts_novos == ["Tabloide Quintou"]
        assert "MinhaFonte.ttf" in analise.fontes_novas
        rel = porta.aplicar_importacao(analise, {}, mercado)
    assert len(rel.produtos_novos) == 3 and rel.fotos_verificadas == 3

    # trio nome×preço×imagem POR CONTEÚDO após o remap, por chave natural
    for (nome, marca), cor in list(CORES.items())[:3]:
        p = seeds.produto_por_chave(mercado, nome, marca)
        assert p is not None, f"{nome} não chegou ao mercado"
        assert seeds.foto_de(mercado, nome, marca) == seeds.png(cor)
    assert seeds.produto_por_chave(mercado, "Coca-Cola 2L", "Coca-Cola")[
        "preco"] == "8.99"
    assert seeds.produto_por_chave(
        mercado, "Cerveja Amstel 269ml", "Amstel")["mais18"] is True
    assert (mercado.fontes / "MinhaFonte.ttf").exists()
    # o projeto congelado viajou com a pasta inteira
    c = seeds.contagens(mercado)
    assert c["projetos"] == 1 and c["aliases"] == 1
    # o alias seguiu o REMAP: aponta para a Coca do mercado, não para um id velho
    assert seeds.alias_aponta_para(mercado, "COCA COLA 2LT") == \
        porta.chave_natural("Coca-Cola 2L", "Coca-Cola")

    # --- alterar em B: produto novo, preço mudado, foto trocada ---------------------
    seeds.add_produto(mercado, "Feijão 1kg", "Kicaldo", "7.49",
                      seeds.png(CORES[("Feijão 1kg", "Kicaldo")]),
                      categoria="Mercearia")
    _mudar_preco(mercado, "Coca-Cola 2L", "Coca-Cola", "9.49")
    _trocar_foto(mercado, "Arroz 5kg", "Camil", ARROZ_FOTO_NOVA)

    # --- exportar de B e importar de volta em A com MESCLAGEM ------------------------
    pkg2 = porta.exportar_pacote(tmp_path / "mercado_para_casa", mercado)
    with porta.analisar_pacote(pkg2, casa) as analise2:
        assert [d["nome"] for d in analise2.novos] == ["Feijão 1kg"]
        confl = {c.id_decisao: c for c in analise2.conflitos
                 if c.tipo == "produto"}
        id_coca = "produto:coca-cola 2l|coca-cola"
        id_arroz = "produto:arroz 5kg|camil"
        assert set(confl) == {id_coca, id_arroz}    # Amstel intacta = sem conflito
        assert "preço" in confl[id_coca].campos
        assert "foto" in confl[id_arroz].campos
        # o relatório mostra os dois lados do preço para o humano decidir
        assert confl[id_coca].local["preço"] == "8.99"
        assert confl[id_coca].pacote["preço"] == "9.49"
        assert analise2.projetos_existentes == 1    # uuid não colide nem duplica

        # I2: conflito SEM decisão nunca passa em silêncio
        with pytest.raises(ValueError, match="sem decisão"):
            porta.aplicar_importacao(analise2, {}, casa)

        rel2 = porta.aplicar_importacao(analise2, {
            id_coca: Decisao.USAR_PACOTE,       # o preço do mercado vence
            id_arroz: Decisao.MANTER_LOCAL,     # a foto de casa fica
        }, casa)
    assert ("Coca-Cola 2L (Coca-Cola)", "usar_pacote") in rel2.conflitos_resolvidos

    # decisões aplicadas — e NENHUMA foto trocada de produto (byte a byte)
    assert seeds.produto_por_chave(casa, "Coca-Cola 2L", "Coca-Cola")[
        "preco"] == "9.49"
    esperado_casa = {
        ("Coca-Cola 2L", "Coca-Cola"): CORES[("Coca-Cola 2L", "Coca-Cola")],
        ("Arroz 5kg", "Camil"): CORES[("Arroz 5kg", "Camil")],   # manter local
        ("Cerveja Amstel 269ml", "Amstel"):
            CORES[("Cerveja Amstel 269ml", "Amstel")],
        ("Feijão 1kg", "Kicaldo"): CORES[("Feijão 1kg", "Kicaldo")],
    }
    for (nome, marca), cor in esperado_casa.items():
        assert seeds.foto_de(casa, nome, marca) == seeds.png(cor), \
            f"foto de {nome} não é a esperada — trocou de produto?"

    # --- importar o MESMO pacote de novo: idempotente, zero duplicatas ---------------
    antes = seeds.contagens(casa)
    with porta.analisar_pacote(pkg2, casa) as analise3:
        assert not analise3.novos                   # Feijão agora é idêntico
        confl3 = {c.id_decisao for c in analise3.conflitos if c.tipo == "produto"}
        assert confl3 == {id_arroz}                 # divergência REAL continua visível
        rel3 = porta.aplicar_importacao(
            analise3, {id_arroz: Decisao.MANTER_LOCAL}, casa)
    assert seeds.contagens(casa) == antes           # nada duplicou
    assert not rel3.produtos_novos and rel3.projetos_pulados >= 1
    assert seeds.foto_de(casa, "Arroz 5kg", "Camil") == \
        seeds.png(CORES[("Arroz 5kg", "Camil")])


def test_remap_com_ids_deslocados(tmp_path):
    """O coração do D-B1: id 12 de casa NÃO é o 12 do mercado.

    B já tem produtos próprios ocupando os ids baixos — os importados ganham
    ids NOVOS e as pastas da biblioteca são renomeadas no ato. A prova é por
    bytes: cada foto continua com o SEU produto (chave natural), e a foto que
    já morava em B fica intacta.
    """
    a = seeds.raiz(tmp_path, "a")
    id_coca_a = seeds.add_produto(a, "Coca-Cola 2L", "Coca-Cola", "8.99",
                                  seeds.png("#FF0000"))
    id_arroz_a = seeds.add_produto(a, "Arroz 5kg", "Camil", "24.90",
                                   seeds.png("#00FF00"))
    assert (id_coca_a, id_arroz_a) == (1, 2)

    b = seeds.raiz(tmp_path, "b")
    for i, (nome, cor) in enumerate(
            [("Sabão em Pó", "#FF00FF"), ("Detergente", "#800080"),
             ("Amaciante", "#808000")], start=1):
        assert seeds.add_produto(b, nome, "Omo", "5.00", seeds.png(cor)) == i

    pkg = porta.exportar_pacote(tmp_path / "a.atpkg", a)
    with porta.analisar_pacote(pkg, b) as analise:
        rel = porta.aplicar_importacao(analise, {}, b)
    assert rel.fotos_verificadas == 2

    coca_b = seeds.produto_por_chave(b, "Coca-Cola 2L", "Coca-Cola")
    arroz_b = seeds.produto_por_chave(b, "Arroz 5kg", "Camil")
    # ids REMAPEADOS (os de A estão ocupados em B por outros produtos)
    assert coca_b["id"] not in (id_coca_a, id_arroz_a)
    assert arroz_b["id"] not in (id_coca_a, id_arroz_a)
    # a pasta foi renomeada conforme o remap e o conteúdo é byte-idêntico
    assert coca_b["caminho_imagem"] == f"{coca_b['id']}/atual.png"
    assert seeds.foto_de(b, "Coca-Cola 2L", "Coca-Cola") == seeds.png("#FF0000")
    assert seeds.foto_de(b, "Arroz 5kg", "Camil") == seeds.png("#00FF00")
    # os produtos que já moravam em B não foram tocados (a mesclagem ingênua
    # por id teria colado a foto da Coca em cima do Sabão)
    assert seeds.foto_de(b, "Sabão em Pó", "Omo") == seeds.png("#FF00FF")


def test_manter_ambos_cria_variante_com_foto_propria(tmp_path):
    a = seeds.raiz(tmp_path, "a")
    seeds.add_produto(a, "Café 500g", "Pilão", "18.90", seeds.png("#111111"))
    b = seeds.raiz(tmp_path, "b")
    seeds.add_produto(b, "Café 500g", "Pilão", "21.90", seeds.png("#222222"))

    pkg = porta.exportar_pacote(tmp_path / "a.atpkg", a)
    with porta.analisar_pacote(pkg, b) as analise:
        assert len(analise.conflitos) == 1
        rel = porta.aplicar_importacao(
            analise, {analise.conflitos[0].id_decisao: Decisao.MANTER_AMBOS}, b)
    assert rel.variantes_criadas == ["Café 500g (importado)"]
    # os DOIS existem, cada um com a própria foto (nada sobrescrito)
    assert seeds.foto_de(b, "Café 500g", "Pilão") == seeds.png("#222222")
    assert seeds.foto_de(b, "Café 500g (importado)", "Pilão") == \
        seeds.png("#111111")
    assert seeds.produto_por_chave(b, "Café 500g", "Pilão")["preco"] == "21.90"
    assert seeds.produto_por_chave(
        b, "Café 500g (importado)", "Pilão")["preco"] == "18.90"

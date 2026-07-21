"""Etapa A da ORDEM_F8 (F8.1) — categorização corrigível + agrupamento.

A regra que protege o Otaviano: categoria corrigida por HUMANO nunca é
sobrescrita por passe de IA. Item sem categoria agrupa em "Outros" — nunca
some (I2). O agrupamento é SÓ ordenação prévia; o vínculo segue slot→uid.
"""

import sqlite3

from PySide6.QtWidgets import QApplication
from sqlalchemy import select

from app.ai.fake import MotorIAFake
from app.core.database import Database
from app.core.models import Produto
from app.qt.telas import servico
from app.qt.telas.servico import ItemMesa
from app.tests import seeds_portabilidade as seeds


def _app():
    QApplication.instance() or QApplication([])


# --- migração de schema (banco antigo ganha a coluna nova) --------------------------


def test_migracao_adiciona_coluna_em_banco_antigo(tmp_path):
    caminho = tmp_path / "antigo" / "banco" / "core.db"
    caminho.parent.mkdir(parents=True)
    con = sqlite3.connect(caminho)     # "banco antigo": produtos SEM a coluna
    con.execute("CREATE TABLE produtos (id INTEGER PRIMARY KEY, "
                "nome_bruto VARCHAR, nome_sanitizado VARCHAR)")
    con.execute("INSERT INTO produtos (nome_bruto, nome_sanitizado) "
                "VALUES ('X', 'X')")
    con.commit()
    con.close()

    from app.core.paths import SystemRoot
    root = SystemRoot(tmp_path / "antigo")
    Database(root).init().engine.dispose()          # init migra

    con = sqlite3.connect(caminho)
    colunas = {r[1] for r in con.execute("PRAGMA table_info(produtos)")}
    con.close()
    assert "categoria_origem" in colunas            # a coluna nasceu
    # e re-rodar o init é inofensivo (idempotente)
    Database(root).init().engine.dispose()


# --- a regra: humano vence a IA, sempre ---------------------------------------------


def _motor_categorista(categoria: str, nome: str = "") -> MotorIAFake:
    # "supermercado" aparece no prompt de sistema do enriquecer — casa sempre
    return MotorIAFake(respostas_chat={
        "supermercado": f'{{"nome_sanitizado": "{nome}", '
                        f'"categoria": "{categoria}", '
                        '"bebida_alcoolica": false, "mais18": false, '
                        '"confianca": 0.9}'})


def test_correcao_humana_sobrevive_ao_passe_de_ia(tmp_path, monkeypatch):
    root = seeds.raiz(tmp_path, "raiz")
    monkeypatch.setenv("AUTOTABLOIDE_ROOT", str(root.raiz))
    pid = seeds.add_produto(root, "Sabao em Po Omo 1kg", "Omo", "15.90")

    # 1) humano corrige a categoria no Almoxarifado
    d = servico.editar_produto(pid, categoria="Limpeza Pesada")
    assert d["categoria"] == "Limpeza Pesada"
    db = Database(root).init()
    with db.Session() as s:
        p = s.get(Produto, pid)
        assert p.categoria_origem == "humano"
    db.engine.dispose()

    # 2) o passe de IA quer OUTRA categoria — e NÃO passa por cima. O fake
    #    RENOMEIA o produto de propósito: o editar acontece de verdade e a
    #    guarda da categoria é exercitada (não passa por falta de edição)
    from app.scripts.enriquecer_banco import categorizar_acervo, enriquecer_banco
    motor = _motor_categorista("Bazar", nome="Sabão em Pó Omo 1kg")
    resumo = categorizar_acervo(motor, log=lambda _l: None)
    assert resumo["categorizados"] == 0             # nada faltava
    r2 = enriquecer_banco(motor, log=lambda _l: None)
    assert r2["atualizados"] == 1                   # o nome FOI editado…
    db = Database(root).init()
    with db.Session() as s:
        p = s.get(Produto, pid)
        assert p.nome_sanitizado == "Sabão em Pó Omo 1kg"
        assert p.categoria.nome == "Limpeza Pesada"     # …e o humano venceu
        assert p.categoria_origem == "humano"
    db.engine.dispose()


def test_lote_categoriza_so_o_que_falta(tmp_path, monkeypatch):
    root = seeds.raiz(tmp_path, "raiz")
    monkeypatch.setenv("AUTOTABLOIDE_ROOT", str(root.raiz))
    sem = seeds.add_produto(root, "Cafe Pilao 500g", "Pilão", "18.90")
    com = seeds.add_produto(root, "Coca-Cola 2L", "Coca-Cola", "8.99",
                            categoria="Bebidas")

    from app.scripts.enriquecer_banco import categorizar_acervo
    resumo = categorizar_acervo(_motor_categorista("Mercearia"),
                                log=lambda _l: None)
    assert resumo["categorizados"] == 1             # só o que faltava
    db = Database(root).init()
    with db.Session() as s:
        assert s.get(Produto, sem).categoria.nome == "Mercearia"
        assert s.get(Produto, sem).categoria_origem == "ia"
        assert s.get(Produto, com).categoria.nome == "Bebidas"   # intocado
    db.engine.dispose()


def test_lote_sem_palpite_deixa_vazio(tmp_path, monkeypatch):
    root = seeds.raiz(tmp_path, "raiz")
    monkeypatch.setenv("AUTOTABLOIDE_ROOT", str(root.raiz))
    pid = seeds.add_produto(root, "Coisa Estranha", "Marca")
    from app.scripts.enriquecer_banco import categorizar_acervo
    motor = MotorIAFake(respostas_chat={"supermercado": '{"categoria": null}'})
    resumo = categorizar_acervo(motor, log=lambda _l: None)
    assert resumo["sem_palpite"] == 1
    db = Database(root).init()
    with db.Session() as s:
        assert s.get(Produto, pid).categoria_id is None    # → "Outros" na Mesa
    db.engine.dispose()


# --- o agrupamento: ordenação estável, "Outros" por último ---------------------------


def _it(nome, cat=None):
    return ItemMesa(nome, "1,00", "VERDE", nome, categoria=cat)


def test_ordenar_por_categoria_estavel_e_outros_por_ultimo():
    itens = [_it("a1", "Limpeza"), _it("b1", None), _it("c1", "Bebidas"),
             _it("a2", "Limpeza"), _it("c2", "Bebidas"), _it("b2", "")]
    ordenado = servico.ordenar_por_categoria(itens, ["Bebidas", "Limpeza"])
    assert [i.nome for i in ordenado] == ["c1", "c2", "a1", "a2", "b1", "b2"]
    # sem config: alfabética, "Outros" continua no fim; ordem interna estável
    ordenado2 = servico.ordenar_por_categoria(itens, [])
    assert [i.nome for i in ordenado2] == ["c1", "c2", "a1", "a2", "b1", "b2"]
    # categoria fora da lista vem entre as listadas e "Outros"
    itens.append(_it("d1", "Pet"))
    ordenado3 = servico.ordenar_por_categoria(itens, ["Limpeza"])
    assert [i.nome for i in ordenado3] == \
        ["a1", "a2", "c1", "c2", "d1", "b1", "b2"]


def test_mesa_agrupar_por_categoria_no_preencher(tmp_path, monkeypatch):
    """O toggle liga a ordenação prévia; o mapa continua slot→uid (I1)."""
    _app()
    monkeypatch.setenv("AUTOTABLOIDE_ROOT", str(tmp_path / "raiz"))
    from app.core.paths import SystemRoot
    root = SystemRoot(tmp_path / "raiz").criar_estrutura()
    Database(root).init().engine.dispose()

    from app.qt.telas.mesa import MesaTela
    from app.tests.test_adversarial_vinculo import _grade_4

    mesa = MesaTela()
    mesa.carregar_layout(_grade_4(), None)
    mesa._itens = [_it("Sabão", "Limpeza"), _it("Coca", "Bebidas"),
                   _it("Misterioso", None), _it("Arroz", "Mercearia")]
    slots = [s.id for s in mesa._layout.paginas[0].slots]

    mesa.chk_agrupar.setChecked(False)             # padrão: ordem importada
    mesa._auto_preencher()
    assert mesa._mapa[slots[0]] == mesa._itens[0].uid

    db = Database(root).init()
    with db.Session() as s:
        from app.core.repositories import ConfigRepositorio
        ConfigRepositorio(s).set("categorias.ordem", ["Bebidas", "Mercearia"])
        s.commit()
    db.engine.dispose()

    mesa.chk_agrupar.setChecked(True)              # agrupado: Bebidas primeiro…
    mesa._auto_preencher()
    por_uid = {it.uid: it for it in mesa._itens}
    fila = [por_uid[mesa._mapa[sid]].nome for sid in slots]
    assert fila == ["Coca", "Arroz", "Sabão", "Misterioso"]   # Outros no fim
    # a ESTANTE não mudou de ordem (agrupamento é só na fila do preenchimento)
    assert [it.nome for it in mesa._itens] == \
        ["Sabão", "Coca", "Misterioso", "Arroz"]
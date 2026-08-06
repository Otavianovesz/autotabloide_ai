"""RODADA JORNAL DO MÊS — BLOCO 4: FAMÍLIAS de sabores (03/08/2026).

Decisão do dono: cada sabor é um produto COMPLETO (foto/EAN/preço
próprios) ligado a uma FAMÍLIA ("Sardinha Coqueiro 125g" → Tomate/
Óleo/Limão); na importação ele marca com CHECK quais sabores estão na
oferta e a célula desenha o leque de fotos (o multi da F7.1). Variantes
não existiam no banco — a única mudança de SCHEMA da rodada (aditiva,
v2→v3, padrão E7 com backup).

O leque escolhido vive no ITEM/projeto (congela com ele) — o
`imagens_json` do RG-28 NÃO entra aqui: ele é por-produto e relativo à
pasta DO produto; misturar quebraria I3.

Testes L1 — todos vermelhos no código antigo.
"""

import pytest

from app.core.database import Database
from app.core.paths import SystemRoot
from app.core.repositories import ProdutoRepositorio


@pytest.fixture
def raiz(tmp_path, monkeypatch):
    monkeypatch.setenv("AUTOTABLOIDE_ROOT", str(tmp_path / "raiz"))
    return SystemRoot(tmp_path / "raiz")


# ================================================================== 4.1
# Schema v2→v3 (padrão E7: backup antes do ALTER, idempotente)
# ======================================================================


def test_migracao_v2_para_v3(raiz):
    db = Database(raiz).init()
    db.engine.dispose()
    # fabrica um banco v2: sem a coluna/índice novos e com uv antigo
    import sqlite3
    con = sqlite3.connect(raiz.caminho_banco)
    try:
        con.execute("DROP INDEX IF EXISTS ix_produtos_familia_id")
        con.execute("ALTER TABLE produtos DROP COLUMN familia_id")
        con.execute("DROP TABLE IF EXISTS familias_produto")
        con.execute("PRAGMA user_version = 2")
        con.commit()
    finally:
        con.close()

    db = Database(raiz).init()          # migra: backup + ALTER + índice
    try:
        with db.engine.connect() as conn:
            cols = {r[1] for r in conn.exec_driver_sql(
                "PRAGMA table_info(produtos)")}
            assert "familia_id" in cols
            idx = {r[1] for r in conn.exec_driver_sql(
                "PRAGMA index_list('produtos')")}
            assert "ix_produtos_familia_id" in idx
            tabelas = {r[0] for r in conn.exec_driver_sql(
                "SELECT name FROM sqlite_master WHERE type='table'")}
            assert "familias_produto" in tabelas
            uv = conn.exec_driver_sql("PRAGMA user_version").scalar()
            assert uv == 3
    finally:
        db.engine.dispose()
    from pathlib import Path
    pasta_backups = Path(raiz.caminho_banco).parent.parent / "backups"
    backups = list(pasta_backups.glob("pre_migracao_*.db"))
    assert backups, "migração sem backup viola o E7"


# ================================================================== 4.2
# Repositório e serviço
# ======================================================================


def test_familia_repositorio(raiz):
    from app.core.repositories import FamiliaRepositorio

    db = Database(raiz).init()
    try:
        with db.Session() as s:
            repo = ProdutoRepositorio(s)
            p1 = repo.importar("SARDINHA COQUEIRO TOMATE 125 g").produto
            p2 = repo.importar("SARDINHA COQUEIRO OLEO 125 g").produto
            p3 = repo.importar("SARDINHA COQUEIRO LIMAO 125 g").produto
            s.commit()
            fam = FamiliaRepositorio(s)
            fid = fam.obter_ou_criar("Sardinha Coqueiro 125g")
            assert fam.obter_ou_criar("Sardinha Coqueiro 125g") == fid
            repo.definir_familia([p1.id, p2.id, p3.id], fid)
            s.commit()
            assert {m.id for m in fam.membros(fid)} == {p1.id, p2.id, p3.id}
            # a lixeira some da família (CI-01)
            from datetime import datetime
            repo.editar(p3.id, excluido_em=datetime.now())
            s.commit()
            assert {m.id for m in fam.membros(fid)} == {p1.id, p2.id}
            fam.dissolver(fid)
            s.commit()
            assert fam.membros(fid) == []
            s.refresh(p1)
            assert p1.familia_id is None
    finally:
        db.engine.dispose()


def test_nome_de_familia():
    from app.qt.telas.servico import nome_de_familia

    assert nome_de_familia(["Sardinha Coqueiro 125g Tomate",
                            "Sardinha Coqueiro 125g Óleo e Limão"]) \
        == "Sardinha Coqueiro 125g"
    assert nome_de_familia(["Rosquinha Mabel Coco",
                            "Rosquinha Mabel Chocolate"]) == "Rosquinha Mabel"
    # sem prefixo comum: o primeiro nome serve de sugestão
    assert nome_de_familia(["Coca-Cola 2L", "Fanta Laranja 2L"]) \
        == "Coca-Cola 2L"


def test_criar_familia_e_familia_do_item(raiz):
    from app.qt.telas import servico

    db = Database(raiz).init()
    try:
        with db.Session() as s:
            repo = ProdutoRepositorio(s)
            ids = [repo.importar(n).produto.id for n in (
                "SARDINHA COQUEIRO TOMATE 125 g",
                "SARDINHA COQUEIRO OLEO 125 g",
                "SARDINHA COQUEIRO LIMAO 125 g")]
            s.commit()
    finally:
        db.engine.dispose()

    fid = servico.criar_familia_de(ids, "Sardinha Coqueiro 125g")
    assert isinstance(fid, int)
    fam = servico.familia_do_item(ids[0])
    assert fam is not None
    assert fam["nome"] == "Sardinha Coqueiro 125g"
    assert [m["produto_id"] for m in fam["membros"]] == sorted(ids)
    # produto sem família → None (o caminho comum não muda)
    assert servico.familia_do_item(999999) is None


def test_aplicar_sabores(raiz):
    """O CHECK vira o leque: as fotos dos membros escolhidos entram no
    ITEM na ordem por produto_id (identidade, I1) com arranjo LEQUE."""
    from app.qt.telas.servico import ItemMesa, aplicar_sabores

    membros = [
        {"produto_id": 7, "nome": "Coco", "imagem": "/f/coco.png"},
        {"produto_id": 3, "nome": "Chocolate", "imagem": "/f/choc.png"},
        {"produto_id": 9, "nome": "Leite", "imagem": None},   # sem foto
    ]
    item = ItemMesa(descricao="x", preco="4,99", semaforo="VERDE",
                    nome="Rosquinha Mabel")
    aplicar_sabores(item, membros)
    assert item.imagens == ["/f/choc.png", "/f/coco.png"]   # id 3 antes do 7
    assert item.arranjo == "LEQUE"


def test_conciliar_anexa_a_familia(raiz):
    """Item casado cujo produto pertence a uma família viaja com ela —
    é o dado que acende o "Sabores…" na estante."""
    from app.qt.telas import servico

    db = Database(raiz).init()
    try:
        with db.Session() as s:
            repo = ProdutoRepositorio(s)
            ids = [repo.importar(n).produto.id for n in (
                "SARDINHA COQUEIRO TOMATE 125 g",
                "SARDINHA COQUEIRO OLEO 125 g")]
            s.commit()
    finally:
        db.engine.dispose()
    servico.criar_familia_de(ids, "Sardinha Coqueiro 125g")

    res = servico.conciliar_linhas(
        [("SARDINHA COQUEIRO TOMATE 125 g", "5,99", None)], lambda *_: None)
    (item,) = res.itens
    assert item.semaforo == "VERDE"
    assert item.familia is not None
    assert item.familia["nome"] == "Sardinha Coqueiro 125g"
    assert len(item.familia["membros"]) == 2
    # round-trip: a família congela e volta com o projeto
    clone = servico.ItemMesa.from_dict(item.to_dict())
    assert clone.familia == item.familia


# ================================================================== 4.4
# O degrau por família no agrupador da Mesa
# ======================================================================


def test_sugerir_variacoes_degrau_por_familia():
    """Itens da MESMA família agrupam com CERTEZA — sem exigir marca
    conhecida (o degrau novo vem antes da heurística de marca)."""
    from types import SimpleNamespace

    from app.core.aprendizado import sugerir_variacoes

    fam = {"id": 4, "nome": "Sardinha Coqueiro 125g", "membros": []}
    a = SimpleNamespace(nome="Sardinha Coqueiro Tomate", familia=fam)
    b = SimpleNamespace(nome="Sardinha Coqueiro Óleo", familia=fam)
    c = SimpleNamespace(nome="Arroz Somar 5kg", familia=None)
    grupos = sugerir_variacoes([a, b, c], [])   # SEM marcas conhecidas
    assert any({id(x) for x in g} == {id(a), id(b)} for g in grupos), grupos


# ================================================================== 4.3
# O diálogo do CHECK (headless)
# ======================================================================


def _app():
    from PySide6.QtWidgets import QApplication
    return QApplication.instance() or QApplication([])


def test_sabores_dialog_headless():
    _app()
    from app.qt.telas.sabores_dialog import SaboresDialog

    membros = [
        {"produto_id": 1, "nome": "Tomate", "imagem": None},
        {"produto_id": 2, "nome": "Óleo", "imagem": None},
        {"produto_id": 3, "nome": "Limão", "imagem": None},
    ]
    dlg = SaboresDialog("Sardinha Coqueiro 125g", membros,
                        marcados={2})
    try:
        escolhidos = dlg.escolhidos()
        assert [m["produto_id"] for m in escolhidos] == [2]
        # marcar os outros dois pelo código (o gesto real é o clique)
        for i in range(dlg.lista.count()):
            dlg.lista.item(i).setCheckState(
                __import__("PySide6.QtCore", fromlist=["Qt"]).Qt.CheckState.Checked)
        assert len(dlg.escolhidos()) == 3
    finally:
        dlg.deleteLater()

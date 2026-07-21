"""Testes do CRUD de produtos (Fase 1)."""

from decimal import Decimal

import pytest

from app.core.database import Database
from app.core.paths import SystemRoot
from app.core.repositories import (
    ConfigRepositorio,
    ProdutoRepositorio,
    regras_de_config,
)


@pytest.fixture
def session(tmp_path):
    db = Database(SystemRoot(tmp_path / "raiz")).init()
    s = db.Session()
    try:
        yield s
    finally:
        s.close()


def test_importar_cria_produto(session):
    repo = ProdutoRepositorio(session)
    r = repo.importar("AÇÚCAR CRISTAL DOCE DIA 2 Kgs", preco="5,95")
    assert r.criado
    assert r.produto.nome_sanitizado == "Açúcar Cristal Doce Dia 2kg"
    assert r.produto.preco_atual == Decimal("5.95")
    assert r.produto.peso_unidade == "kg"
    session.commit()
    assert repo.contar() == 1


def test_dedup_por_nome_bruto_atualiza_preco(session):
    repo = ProdutoRepositorio(session)
    a = repo.importar("BOMBRIL 45 g", preco="2,66")
    b = repo.importar("BOMBRIL 45 g", preco="2,90")
    assert not b.criado
    assert a.produto.id == b.produto.id
    assert b.produto.preco_atual == Decimal("2.90")
    assert repo.contar() == 1


def test_importar_registra_alias(session):
    repo = ProdutoRepositorio(session)
    r = repo.importar("NUTELLA 350 g FERRERO")
    assert any(al.alias_raw == "NUTELLA 350 g FERRERO" for al in r.produto.aliases)
    reencontrado = repo.buscar_por_alias("NUTELLA 350 g FERRERO")
    assert reencontrado is not None and reencontrado.id == r.produto.id


def test_editar_produto_e_categoria(session):
    repo = ProdutoRepositorio(session)
    r = repo.importar("BOMBRIL 45 g")
    repo.editar(r.produto.id, marca="Bombril", categoria="Limpeza")
    p = repo.get(r.produto.id)
    assert p.marca == "Bombril"
    assert p.categoria is not None and p.categoria.nome == "Limpeza"


def test_buscar_e_listar(session):
    repo = ProdutoRepositorio(session)
    repo.importar("BOMBRIL 45 g")
    repo.importar("NUTELLA 350 g FERRERO")
    session.commit()
    assert repo.contar() == 2
    assert len(repo.listar()) == 2
    achados = repo.buscar("nutella")
    assert len(achados) == 1 and achados[0].nome_sanitizado.startswith("Nutella")


def test_config_siglas_override(session):
    ConfigRepositorio(session).set("sanitizacao.siglas", ["ABC"])
    regras = regras_de_config(session)
    assert "ABC" in regras.siglas

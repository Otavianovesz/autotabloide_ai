"""Testes do Almoxarifado (F6.3) — catálogo, qualidade, edição, importar do banco."""

import pytest
from PySide6.QtWidgets import QApplication

from app.qt.telas import servico


@pytest.fixture()
def catalogo_tmp(tmp_path, monkeypatch):
    """Raiz isolada com 60 produtos (2 páginas do modelo virtualizado)."""
    monkeypatch.setenv("AUTOTABLOIDE_ROOT", str(tmp_path / "raiz"))
    from app.core.database import Database
    from app.core.paths import SystemRoot
    from app.core.repositories import ProdutoRepositorio

    root = SystemRoot(tmp_path / "raiz").criar_estrutura()
    db = Database(root).init()
    with db.Session() as s:
        repo = ProdutoRepositorio(s)
        for i in range(60):
            repo.importar(f"PRODUTO TESTE {i:02d} 500 g",
                          preco=f"{i + 1},50" if i % 3 else None)
        s.commit()
    db.engine.dispose()
    return root


def test_listar_catalogo_pagina_e_busca(catalogo_tmp):
    pagina1 = servico.listar_catalogo(offset=0, limite=50)
    pagina2 = servico.listar_catalogo(offset=50, limite=50)
    assert len(pagina1) == 50 and len(pagina2) == 10
    achados = servico.listar_catalogo(texto="Teste 07")
    assert len(achados) == 1 and "07" in achados[0]["nome"]


def test_qualidade_semaforo():
    assert servico.qualidade_produto({"imagem": None}) == "VERMELHO"
    assert servico.qualidade_produto(
        {"imagem": "x.png", "preco": None, "categoria": "Mercearia"}) == "AMARELO"
    assert servico.qualidade_produto(
        {"imagem": "x.png", "preco": "5,50", "categoria": ""}) == "AMARELO"
    assert servico.qualidade_produto(
        {"imagem": "x.png", "preco": "5,50", "categoria": "Mercearia"}) == "VERDE"


def test_editar_produto_persiste(catalogo_tmp):
    d = servico.listar_catalogo(limite=1)[0]
    novo = servico.editar_produto(d["id"], nome_sanitizado="Nome Editado",
                                  preco_atual="9,90", categoria="Limpeza",
                                  selo_mais18=True)
    assert novo["nome"] == "Nome Editado"
    assert novo["preco"] == "9,90"
    assert novo["categoria"] == "Limpeza"
    assert novo["mais18"] is True
    relido = servico.listar_catalogo(texto="Nome Editado")[0]
    assert relido["id"] == d["id"]


def test_modelo_virtualizado_busca_por_paginas(catalogo_tmp):
    QApplication.instance() or QApplication([])
    from app.qt.telas.almoxarifado import CatalogoModel

    m = CatalogoModel()
    assert m.rowCount() == 0 and m.canFetchMore()
    m.fetchMore()
    assert m.rowCount() == 50 and m.canFetchMore()   # 1ª página
    m.fetchMore()
    assert m.rowCount() == 60 and not m.canFetchMore()  # acabou


def test_importar_banco_acumula_entre_buscas(catalogo_tmp):
    QApplication.instance() or QApplication([])
    from app.qt.telas.importar_banco_dialog import ImportarBancoDialog

    dlg = ImportarBancoDialog()
    dlg.busca.setText("Teste 01")
    assert dlg.resultados.count() == 1
    dlg._adicionar(dlg.resultados.item(0))
    dlg.busca.setText("Teste 02")            # nova busca…
    dlg._adicionar(dlg.resultados.item(0))
    assert len(dlg._cesta) == 2               # …sem perder a seleção
    dlg._concluir()
    assert {d["nome"] for d in dlg.selecionados} == \
           {"Produto Teste 01 500g", "Produto Teste 02 500g"}


def test_item_do_catalogo_vira_item_verde(catalogo_tmp):
    d = servico.listar_catalogo(texto="Teste 04")[0]
    item = servico.item_do_catalogo(d)
    assert item.semaforo == "VERDE" and item.via == "banco"
    assert item.produto_id == d["id"] and item.nome == d["nome"]
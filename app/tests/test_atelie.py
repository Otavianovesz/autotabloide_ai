"""Testes do Ateliê (F6.2) — persistência CRUD + fumaça da tela (offscreen)."""

from pathlib import Path

import pytest
from PySide6.QtWidgets import QApplication

from app.rendering.cartaz import layout_cartaz_exemplo
from app.rendering.persistencia import (
    carregar_layout,
    duplicar_layout,
    excluir_layout,
    listar_layouts,
    renomear_layout,
    salvar_layout,
)


@pytest.fixture()
def banco_tmp(tmp_path, monkeypatch):
    monkeypatch.setenv("AUTOTABLOIDE_ROOT", str(tmp_path / "raiz"))
    from app.core.database import Database
    from app.core.paths import SystemRoot

    root = SystemRoot(tmp_path / "raiz").criar_estrutura()
    # as miniaturas/preview do Ateliê compõem texto → precisam das fontes
    import shutil
    reais = Path("AutoTabloide_System_Root/fontes")
    if reais.exists():
        for f in reais.glob("*.ttf"):
            shutil.copy(f, root.fontes / f.name)
    db = Database(root).init()
    yield db
    db.engine.dispose()


def test_crud_de_layout(banco_tmp):
    with banco_tmp.Session() as s:
        row = salvar_layout(s, "Cartaz A", layout_cartaz_exemplo(),
                            tipo_midia="CARTAZ")
        s.commit()
        lid = row.id

    with banco_tmp.Session() as s:
        copia = duplicar_layout(s, lid, "Cartaz A cópia")
        renomear_layout(s, lid, "Cartaz A v2")
        s.commit()
        nomes = {r.nome: r.tipo_midia for r in listar_layouts(s)}
        assert nomes == {"Cartaz A v2": "CARTAZ", "Cartaz A cópia": "CARTAZ"}
        # a cópia reconstrói o LayoutDef inteiro (nº de regiões = o do exemplo,
        # derivado da produção — nunca um número mágico, I5)
        ldef = carregar_layout(s, copia.id)
        n_esperado = len(layout_cartaz_exemplo().paginas[0].slots[0].regioes)
        assert ldef is not None
        assert len(ldef.paginas[0].slots[0].regioes) == n_esperado

    with banco_tmp.Session() as s:
        excluir_layout(s, lid)
        s.commit()
        assert [r.nome for r in listar_layouts(s)] == ["Cartaz A cópia"]


def test_atelie_lista_e_abre(banco_tmp):
    QApplication.instance() or QApplication([])
    from app.qt.telas.atelie import AtelieTela

    with banco_tmp.Session() as s:
        salvar_layout(s, "Meu Cartaz", layout_cartaz_exemplo(), tipo_midia="CARTAZ")
        s.commit()

    abertos = []
    tela = AtelieTela(ao_abrir=lambda ldef, tipo, nome: abertos.append((tipo, nome)))
    assert tela.lista.count() == 1
    assert "Meu Cartaz" in tela.lista.item(0).text()

    tela._abrir(tela.lista.item(0))          # duplo-clique → callback com o tipo
    assert abertos == [("CARTAZ", "Meu Cartaz")]


def test_atelie_editar_abre_editor_embutido(banco_tmp):
    QApplication.instance() or QApplication([])
    from app.qt.telas.atelie import AtelieTela

    with banco_tmp.Session() as s:
        row = salvar_layout(s, "Cartaz B", layout_cartaz_exemplo(), tipo_midia="CARTAZ")
        s.commit()
        lid = row.id

    tela = AtelieTela()
    tela._editar(lid, "Cartaz B")
    assert tela._paginas.currentIndex() == 1          # página do editor
    assert tela._editor is not None
    # o layout carregou por inteiro (nº de regiões = o do exemplo real, I5)
    n_esperado = len(layout_cartaz_exemplo().paginas[0].slots[0].regioes)
    assert len(tela._editor.canvas.regioes()) == n_esperado
    tela._voltar()
    assert tela._paginas.currentIndex() == 0

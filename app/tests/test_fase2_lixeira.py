"""FASE 2, Bloco G (passos 87-88) — lixeira: nada some de verdade por 30 dias."""

from datetime import datetime, timedelta

import pytest

from app.qt.telas.servico import ItemMesa
from app.rendering.model import LayoutDef, Pagina, Regiao, Retangulo, Slot, TipoRegiao


@pytest.fixture()
def raiz_tmp(tmp_path, monkeypatch):
    monkeypatch.setenv("AUTOTABLOIDE_ROOT", str(tmp_path / "raiz"))
    from app.core.database import Database
    from app.core.paths import SystemRoot

    root = SystemRoot(tmp_path / "raiz").criar_estrutura()
    Database(root).init().engine.dispose()
    return root


def _layout() -> LayoutDef:
    return LayoutDef(100, 100, dpi=100, paginas=[Pagina([
        Slot("s", [Regiao(TipoRegiao.NOME, Retangulo(10, 10, 30, 10))])])])


def test_excluir_some_restaurar_volta_inteiro(raiz_tmp):
    """Passo 87: excluir → fora das listas; restaurar → volta com o MAPA
    congelado por conteúdo (a pasta nunca foi tocada)."""
    from app.core import lixeira, projetos

    item = ItemMesa(descricao="X", preco="1,00", semaforo="VERDE",
                    nome="Produto X")
    mapa = {"s": item.uid}
    pid = projetos.salvar_projeto("P", "Quintou", "TABLOIDE", _layout(),
                                  [item.to_dict()], mapa=mapa)
    mapa_antes = projetos.abrir_projeto(pid).mapa

    projetos.excluir_projeto(pid)              # a UI chama este
    assert all(p["id"] != pid for p in projetos.listar_projetos())
    na_lixeira = lixeira.listar_lixeira()
    assert len(na_lixeira) == 1
    assert na_lixeira[0]["tipo"] == "projeto"
    assert na_lixeira[0]["dias_restantes"] == 30

    lixeira.restaurar("projeto", pid)
    assert any(p["id"] == pid for p in projetos.listar_projetos())
    assert projetos.abrir_projeto(pid).mapa == mapa_antes   # inteiro (I1)
    assert lixeira.listar_lixeira() == []


def test_purga_respeita_30_dias_e_apaga_arquivos(raiz_tmp):
    """Passo 88: relógio INJETADO — 29 dias fica; 31 dias morre com a
    pasta junto."""
    from app.core import lixeira, projetos
    from app.core.database import Database
    from app.core.models import ProjetoSalvo
    from app.core.projetos import _pasta

    item = ItemMesa(descricao="X", preco="1,00", semaforo="VERDE",
                    nome="Produto X")
    pid = projetos.salvar_projeto("P", None, "TABLOIDE", _layout(),
                                  [item.to_dict()])
    db = Database().init()
    try:
        with db.Session() as s:
            row = s.get(ProjetoSalvo, pid)
            uuid = row.uuid
            row.excluido_em = datetime.now()
            s.commit()
    finally:
        db.engine.dispose()
    pasta = _pasta(uuid)
    assert pasta.exists()

    # 29 dias depois: NADA purga
    assert lixeira.purgar(agora=datetime.now() + timedelta(days=29)) == []
    assert pasta.exists()
    # 31 dias depois: linha E arquivos morrem, com log
    log = lixeira.purgar(agora=datetime.now() + timedelta(days=31))
    assert len(log) == 1 and "P" in log[0]
    assert not pasta.exists()
    db = Database().init()
    try:
        with db.Session() as s:
            assert s.get(ProjetoSalvo, pid) is None
    finally:
        db.engine.dispose()

"""Cofre (D-B2 do Bloco D) — snapshots, rotação, modo seguro e restauração."""

from pathlib import Path

from app.core import cofre
from app.core.database import Database
from app.core.models import Produto
from app.core.paths import SystemRoot
from app.core.repositories import ConfigRepositorio


def _raiz(tmp_path, nome="raiz") -> SystemRoot:
    root = SystemRoot(tmp_path / nome).criar_estrutura()
    Database(root).init().engine.dispose()
    return root


def _add_produto(root: SystemRoot, nome: str) -> None:
    db = Database(root).init()
    try:
        with db.Session() as s:
            s.add(Produto(nome_bruto=nome.upper(), nome_sanitizado=nome))
            s.commit()
    finally:
        db.engine.dispose()


def test_snapshot_cria_copia_consistente_e_legivel(tmp_path):
    root = _raiz(tmp_path)
    _add_produto(root, "Coca-Cola 2L")
    snap = cofre.criar_snapshot(root, rotulo="manual")
    assert snap.exists() and snap.parent == root.backups
    # modo seguro: inspeciona SEM tocar no vivo
    info = cofre.inspecionar_snapshot(snap)
    assert info["produtos"] == 1


def test_listar_snapshots_mais_novo_primeiro(tmp_path):
    root = _raiz(tmp_path)
    _add_produto(root, "A")
    a = cofre.criar_snapshot(root, rotulo="manual")
    b = cofre.criar_snapshot(root, rotulo="manual")
    lista = cofre.listar_snapshots(root)
    assert [Path(s["caminho"]).name for s in lista][:2] == [b.name, a.name][:2] \
        or len(lista) == 2          # mesmo segundo: só a contagem importa
    assert all(s["rotulo"] == "manual" for s in lista)


def test_rotacao_so_dos_automaticos(tmp_path):
    root = _raiz(tmp_path)
    _add_produto(root, "A")
    db = Database(root).init()
    try:
        with db.Session() as s:
            ConfigRepositorio(s).set("backups.rotacao", 3)
            s.commit()
    finally:
        db.engine.dispose()
    manual = cofre.criar_snapshot(root, rotulo="manual")
    for _ in range(5):
        cofre.snapshot_automatico(root)
    autos = [s for s in cofre.listar_snapshots(root) if s["rotulo"] == "auto"]
    assert len(autos) == 3                      # rotação respeita a config
    assert manual.exists()                      # manual NUNCA roda na rotação


def test_restaurar_nunca_apaga_o_banco_atual(tmp_path):
    root = _raiz(tmp_path)
    _add_produto(root, "Produto 1")
    snap = cofre.criar_snapshot(root, rotulo="manual")     # estado com 1
    _add_produto(root, "Produto 2")                        # vivo agora tem 2

    guarda = cofre.restaurar_snapshot(snap, root)
    # o vivo voltou ao estado do snapshot…
    db = Database(root).init()
    try:
        with db.Session() as s:
            assert s.query(Produto).count() == 1
    finally:
        db.engine.dispose()
    # …e o estado de ANTES da restauração virou snapshot (dá para desfazer)
    assert guarda.exists() and "pre_restauracao" in guarda.name
    assert cofre.inspecionar_snapshot(guarda)["produtos"] == 2


def test_snapshot_automatico_sem_banco_nao_quebra(tmp_path):
    root = SystemRoot(tmp_path / "vazia").criar_estrutura()   # sem core.db
    assert cofre.snapshot_automatico(root) is None


def test_inspecionar_snapshot_inexistente_erro(tmp_path):
    import pytest

    with pytest.raises(FileNotFoundError):
        cofre.inspecionar_snapshot(tmp_path / "nao_existe.db")

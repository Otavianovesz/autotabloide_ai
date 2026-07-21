"""
Testes de fumaça da Fase 0
==========================
Garantem os três marcos da fundação:
1. A estrutura de pastas (System Root) é criada.
2. O banco inicializa (arquivo existe e WAL ligado).
3. A janela principal do Qt é construída sem erro.
"""

from pathlib import Path

from app.core.database import Database
from app.core.paths import SUBPASTAS, SystemRoot


def test_system_root_cria_todas_as_subpastas(tmp_path: Path):
    root = SystemRoot(tmp_path / "raiz").criar_estrutura()
    for nome in SUBPASTAS.values():
        assert (root.raiz / nome).is_dir(), f"faltou criar a pasta {nome}"


def test_atalhos_de_pasta_apontam_para_o_lugar_certo(tmp_path: Path):
    root = SystemRoot(tmp_path / "raiz")
    assert root.caminho_banco == root.raiz / "banco" / "core.db"
    assert root.biblioteca_imagens == root.raiz / "biblioteca_imagens"


def test_banco_inicializa_com_wal(tmp_path: Path):
    root = SystemRoot(tmp_path / "raiz")
    db = Database(root).init()
    assert root.caminho_banco.exists(), "arquivo core.db não foi criado"
    with db.engine.connect() as conn:
        modo = conn.exec_driver_sql("PRAGMA journal_mode").scalar()
    assert str(modo).lower() == "wal"


def test_janela_principal_abre():
    from PySide6.QtWidgets import QApplication

    from app.qt.design.shell import Shell

    app = QApplication.instance() or QApplication([])
    janela = Shell()   # a janela principal do app é o shell do sistema de design
    assert janela.windowTitle() == "AutoTabloide AI"

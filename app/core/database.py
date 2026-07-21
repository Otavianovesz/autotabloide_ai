"""
Conexão com o banco de dados (SQLite, síncrono, modo WAL)
=========================================================
Escolhemos SQLAlchemy **síncrono** (não async): é um app de um usuário só,
offline, e o código fica bem mais simples de ler e manter.

Fase 0: cria o arquivo do banco e liga o WAL.
Fase 1: aqui entrará ``Base.metadata.create_all`` para criar as tabelas.
"""

from __future__ import annotations

from pathlib import Path

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.paths import SystemRoot


def criar_engine(caminho_banco: Path) -> Engine:
    """Cria o engine do SQLite ligando WAL e chaves estrangeiras a cada conexão."""
    engine = create_engine(f"sqlite:///{caminho_banco}", future=True)

    @event.listens_for(engine, "connect")
    def _pragmas(dbapi_conn, _record):  # noqa: ANN001
        cur = dbapi_conn.cursor()
        cur.execute("PRAGMA journal_mode=WAL")   # robustez contra corrupção
        cur.execute("PRAGMA foreign_keys=ON")    # respeitar relações entre tabelas
        cur.close()

    return engine


class Database:
    """Gerencia o engine e as sessões do banco principal (core.db)."""

    def __init__(self, root: SystemRoot | None = None):
        self.root = root or SystemRoot()
        self.root.criar_estrutura()
        self.engine = criar_engine(self.root.caminho_banco)
        self.Session = sessionmaker(
            bind=self.engine, class_=Session, expire_on_commit=False
        )

    def init(self) -> "Database":
        """Garante o arquivo do banco (WAL ligado) e cria as tabelas."""
        from app.core.models import Base

        # Abrir uma conexão dispara o PRAGMA WAL e cria o arquivo .db.
        with self.engine.connect() as conn:
            conn.exec_driver_sql("SELECT 1")
        Base.metadata.create_all(self.engine)
        _migrar_schema(self.engine)
        return self


# Colunas que nasceram DEPOIS do schema original — create_all não adiciona
# coluna em tabela existente, então um banco antigo precisa do ALTER (leve e
# idempotente; roda a cada init). tabela → {coluna: tipo SQL}
_COLUNAS_NOVAS: dict[str, dict[str, str]] = {
    "produtos": {"categoria_origem": "VARCHAR(10)",    # F8.1
                 "ean": "VARCHAR(14)",                 # RG-41
                 "imagens_json": "TEXT",               # RG-28
                 "excluido_em": "DATETIME"},           # F2 passo 81
    # FASE 2: evento vira entidade (o TEXTO `evento` fica por compat — a
    # verdade é o id); FK "solta" de propósito: SQLite não adiciona FK via
    # ALTER — a integridade é do serviço de eventos
    "projetos_salvos": {"evento_id": "INTEGER",        # F2 passo 2
                        "status": "VARCHAR(12)",       # F2 passo 35
                        "favorito": "INTEGER",         # F2 passo 50 (0/1)
                        "excluido_em": "DATETIME"},    # F2 passo 81
    "layouts": {"excluido_em": "DATETIME"},            # F2 passo 81
}


def _migrar_schema(engine: Engine) -> None:
    """Adiciona colunas novas a bancos antigos (migração mínima do SQLite)."""
    with engine.connect() as conn:
        for tabela, colunas in _COLUNAS_NOVAS.items():
            existentes = {r[1] for r in conn.exec_driver_sql(
                f"PRAGMA table_info({tabela})")}
            if not existentes:
                continue                        # tabela nem existe ainda
            for coluna, tipo in colunas.items():
                if coluna not in existentes:
                    conn.exec_driver_sql(
                        f"ALTER TABLE {tabela} ADD COLUMN {coluna} {tipo}")
        conn.commit()

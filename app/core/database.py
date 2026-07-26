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
        """Garante o arquivo do banco (WAL ligado) e cria as tabelas.

        F13/E7 (D-11/P7): o banco tem VERSÃO (PRAGMA user_version) e todo
        banco EXISTENTE que vai migrar ganha um backup ANTES do primeiro
        ALTER — dentro do init, a ordem fica certa por construção (no
        entrypoint real a migração rodava antes do snapshot do boot, o
        achado do scout). Falha do backup PROPAGA: migrar sem cópia é
        arriscar o único banco."""
        from app.core.models import Base

        caminho = Path(self.root.caminho_banco)
        ja_existia = caminho.exists() and caminho.stat().st_size > 0
        # Abrir uma conexão dispara o PRAGMA WAL e cria o arquivo .db.
        with self.engine.connect() as conn:
            conn.exec_driver_sql("SELECT 1")
            uv = conn.exec_driver_sql("PRAGMA user_version").scalar() or 0
        if ja_existia and uv < VERSAO_SCHEMA:
            _backup_pre_migracao(caminho)
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


# F13/E7 (D-11): a VERSÃO do schema — suba ao mexer em _COLUNAS_NOVAS ou
# _INDICES_NOVOS. 0 = banco pré-versão (legado); o init de um banco
# existente com versão menor tira backup ANTES de migrar.
VERSAO_SCHEMA = 2

# F13/E9 (D-10): create_all com checkfirst PULA tabela existente — índice
# novo declarado no modelo nunca chegava a banco antigo. O migrador
# aprende CREATE INDEX (idempotente). (tabela, nome, coluna)
_INDICES_NOVOS: tuple = (
    ("produtos", "ix_produtos_excluido_em", "excluido_em"),
    ("layouts", "ix_layouts_excluido_em", "excluido_em"),
    ("layouts", "ix_layouts_nome", "nome"),
    ("projetos_salvos", "ix_projetos_salvos_excluido_em", "excluido_em"),
)


def _backup_pre_migracao(caminho: Path) -> Path:
    """Cópia consistente (API de backup do SQLite) para backups/ ANTES do
    primeiro ALTER num banco existente. E7/P7: sem cópia, não se migra."""
    import sqlite3
    import time
    destino = (caminho.parent.parent / "backups"
               / f"pre_migracao_{time.strftime('%Y%m%d_%H%M%S')}.db")
    destino.parent.mkdir(parents=True, exist_ok=True)
    src = sqlite3.connect(caminho)
    dst = sqlite3.connect(destino)
    try:
        # D-12: a lei do PRAGMA vale também nas conexões cruas
        src.execute("PRAGMA foreign_keys=ON")
        dst.execute("PRAGMA foreign_keys=ON")
        src.backup(dst)
    finally:
        src.close()
        dst.close()
    return destino


def _migrar_schema(engine: Engine) -> None:
    """Adiciona colunas e ÍNDICES novos a bancos antigos (migração mínima
    do SQLite) e grava a versão (PRAGMA user_version). Banco de versão
    FUTURA não é rebaixado — fica registrado em logs/erros.log (aviso,
    não veto: recusar abrir trancaria o dono)."""
    with engine.connect() as conn:
        uv = conn.exec_driver_sql("PRAGMA user_version").scalar() or 0
        # F13/E7 fast-path por LEITURA: o init roda concorrente nas filas
        # (workers) e todo write aqui disputa lock. Conferir é barato
        # (PRAGMAs de leitura); ESCREVER só acontece quando falta algo —
        # e a conferência é sempre pelas COLUNAS/ÍNDICES de verdade, não
        # só pela versão (um banco fabricado com uv alto e coluna
        # faltando — a migração antiga — ainda ganha o ALTER).
        alters: list[str] = []
        for tabela, colunas in _COLUNAS_NOVAS.items():
            existentes = {r[1] for r in conn.exec_driver_sql(
                f"PRAGMA table_info({tabela})")}
            if not existentes:
                continue                        # tabela nem existe ainda
            for coluna, tipo in colunas.items():
                if coluna not in existentes:
                    alters.append(
                        f"ALTER TABLE {tabela} ADD COLUMN {coluna} {tipo}")
        cria_indices: list[str] = []
        for tabela, nome, coluna in _INDICES_NOVOS:
            ja = {r[1] for r in conn.exec_driver_sql(
                f"PRAGMA index_list('{tabela}')")}
            if nome not in ja:
                cria_indices.append(
                    f"CREATE INDEX IF NOT EXISTS {nome} ON {tabela} ({coluna})")
        if uv > VERSAO_SCHEMA:
            try:
                from app.core.erros import registrar_erro_bruto
                registrar_erro_bruto(
                    f"AVISO: o banco tem versão de schema {uv}, este app "
                    f"conhece até {VERSAO_SCHEMA} — feito por uma versão "
                    "mais nova do AutoTabloide? Dados de colunas novas "
                    "podem ser ignorados.")
            except Exception:
                pass
        if not alters and not cria_indices and uv >= VERSAO_SCHEMA:
            return                              # nada a fazer: ZERO write
        for sql in alters + cria_indices:
            conn.exec_driver_sql(sql)
        if uv < VERSAO_SCHEMA:
            conn.exec_driver_sql(f"PRAGMA user_version = {VERSAO_SCHEMA}")
        conn.commit()

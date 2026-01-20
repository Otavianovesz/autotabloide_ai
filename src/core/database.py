"""
AutoTabloide AI - Configuração de Banco de Dados (Dual-Engine)
================================================================
Camada de persistência conforme Vol. I, Cap. 1.3.
SQLite 3 com WAL Mode para concorrência não-bloqueante.

ARQUITETURA DUAL-DATABASE (Passos 1-2 do Checklist 100):
- core.db: Produtos, Projetos, Layouts, SystemConfig
- learning.db: AuditLog, KnowledgeVector, HumanCorrection
"""

import os
import logging
from pathlib import Path
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import event, text

# Configuração de Logging
logger = logging.getLogger("Database")

# ==============================================================================
# CONFIGURAÇÃO DE CAMINHOS (Topologia Vol. I, Cap. 2)
# ==============================================================================

# Resolve caminho absoluto baseado na estrutura do projeto
BASE_DIR = Path(__file__).parent.parent.parent.resolve()
SYSTEM_ROOT = BASE_DIR / "AutoTabloide_System_Root"
DB_DIR = SYSTEM_ROOT / "database"

# Caminhos dos bancos de dados
CORE_DB_PATH = DB_DIR / "core.db"
LEARNING_DB_PATH = DB_DIR / "learning.db"

# URLs de conexão assíncrona
CORE_DATABASE_URL = f"sqlite+aiosqlite:///{CORE_DB_PATH}"
LEARNING_DATABASE_URL = f"sqlite+aiosqlite:///{LEARNING_DB_PATH}"

# Garantia de existência do diretório (Evita crash inicial)
DB_DIR.mkdir(parents=True, exist_ok=True)


# ==============================================================================
# FUNÇÃO DE PRAGMAS (Reutilizável para ambas engines)
# ==============================================================================

def _configure_sqlite_pragmas(dbapi_connection, connection_record):
    """
    Configura PRAGMAs essenciais para performance e integridade.
    Executado a cada nova conexão ao banco.
    """
    cursor = dbapi_connection.cursor()
    
    # WAL Mode: Permite leitura e escrita simultânea (CRÍTICO para UI reativa)
    cursor.execute("PRAGMA journal_mode=WAL")
    
    # NORMAL Sync: Balanceamento entre segurança e performance
    cursor.execute("PRAGMA synchronous=NORMAL")
    
    # Foreign Keys: Garante integridade referencial
    cursor.execute("PRAGMA foreign_keys=ON")
    
    # Cache Size: Aumenta cache para operações pesadas (10MB)
    cursor.execute("PRAGMA cache_size=-10000")
    
    # Temp Store: Armazena temporários em memória
    cursor.execute("PRAGMA temp_store=MEMORY")
    
    # mmap_size: Permite memory-mapped I/O (30MB)
    cursor.execute("PRAGMA mmap_size=30000000")
    
    cursor.close()


# ==============================================================================
# ENGINE CORE (Produtos, Projetos, Layouts)
# ==============================================================================

core_engine = create_async_engine(
    CORE_DATABASE_URL,
    echo=False,
    future=True,
    pool_pre_ping=True,
    pool_recycle=3600,  # Recycle connections after 1 hour to prevent zombies
)

# Aplica PRAGMAs na engine core
event.listens_for(core_engine.sync_engine, "connect")(_configure_sqlite_pragmas)

# Alias para retrocompatibilidade
engine = core_engine
DB_PATH = CORE_DB_PATH
DATABASE_URL = CORE_DATABASE_URL


# ==============================================================================
# ENGINE LEARNING (IA, Auditoria, Vetores)
# ==============================================================================

learning_engine = create_async_engine(
    LEARNING_DATABASE_URL,
    echo=False,
    future=True,
    pool_pre_ping=True,
    pool_recycle=3600,  # Recycle connections after 1 hour to prevent zombies
)

# Aplica PRAGMAs na engine learning
event.listens_for(learning_engine.sync_engine, "connect")(_configure_sqlite_pragmas)


# ==============================================================================
# SESSION FACTORIES
# ==============================================================================

# Factory para core.db
AsyncSessionLocal = async_sessionmaker(
    bind=core_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False
)

# Factory para learning.db
LearningSessionLocal = async_sessionmaker(
    bind=learning_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False
)


async def get_db():
    """
    Dependency Injection para sessões do banco core.
    Uso: async with get_db() as session: ...
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def get_learning_db():
    """
    Dependency Injection para sessões do banco learning.
    Uso: async with get_learning_db() as session: ...
    """
    async with LearningSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


def get_session_sync():
    """
    Retorna factory de sessão core para uso direto (sem generator).
    Uso: session = await get_session_sync()()
    """
    return AsyncSessionLocal


def get_learning_session_sync():
    """
    Retorna factory de sessão learning para uso direto.
    """
    return LearningSessionLocal


# ==============================================================================
# INICIALIZAÇÃO DO SCHEMA (Dual-Database)
# ==============================================================================

async def _run_auto_migrations(conn):
    """
    Auto-migração para adicionar colunas que faltam em tabelas existentes.
    Isso garante compatibilidade quando modelos são atualizados.
    """
    # Colunas a verificar/adicionar na tabela produtos
    # NOTA: SQLite não permite DEFAULT CURRENT_TIMESTAMP em ALTER TABLE
    # Usamos NULL como default e o ORM define o valor
    produtos_migrations = [
        ("created_at", "DATETIME"),  # SQLite não permite dynamic default em ALTER
        ("last_modified", "DATETIME"),
        ("ultimo_preco_impresso", "DECIMAL(10,2)"),
        ("data_ultima_impressao", "DATETIME"),
        ("categoria", "VARCHAR(100)"),
        ("deleted_at", "DATETIME"),  # Para soft-delete
    ]
    
    try:
        # Verifica colunas existentes
        result = await conn.execute(text("PRAGMA table_info(produtos)"))
        existing_cols = {row[1] for row in result.fetchall()}
        
        for col_name, col_def in produtos_migrations:
            if col_name not in existing_cols:
                try:
                    await conn.execute(text(
                        f"ALTER TABLE produtos ADD COLUMN {col_name} {col_def}"
                    ))
                    logger.info(f"Migração: Adicionada coluna '{col_name}' à tabela produtos")
                except Exception as e:
                    logger.debug(f"Coluna {col_name} talvez já exista: {e}")
                    
    except Exception as e:
        logger.debug(f"Auto-migração: tabela produtos pode não existir ainda: {e}")


async def init_db():
    """
    Inicializa os Schemas em ambos os Bancos de Dados.
    Cria todas as tabelas definidas em models.py se não existirem.
    Aplica migrações automáticas para colunas adicionadas após criação inicial.
    """
    from src.core.models import Base, LearningBase
    
    # Inicializa core.db (Produtos, Projetos, Layouts, SystemConfig)
    async with core_engine.begin() as conn:
        # Primeiro, aplica migrações em tabelas existentes
        await _run_auto_migrations(conn)
        
        # Depois, cria tabelas novas se não existirem
        await conn.run_sync(Base.metadata.create_all)
        logger.info(f"Schema CORE inicializado em: {CORE_DB_PATH}")
    
    # Inicializa learning.db (AuditLog, KnowledgeVector, HumanCorrection)
    async with learning_engine.begin() as conn:
        await conn.run_sync(LearningBase.metadata.create_all)
        logger.info(f"Schema LEARNING inicializado em: {LEARNING_DB_PATH}")


async def check_db_health() -> dict:
    """
    Verifica saúde do banco de dados.
    Retorna dict com status e métricas.
    """
    async with AsyncSessionLocal() as session:
        try:
            # Teste de conectividade
            result = await session.execute(text("SELECT 1"))
            result.scalar()
            
            # Verifica WAL
            result = await session.execute(text("PRAGMA journal_mode"))
            journal_mode = result.scalar()
            
            # Verifica integridade
            result = await session.execute(text("PRAGMA integrity_check"))
            integrity = result.scalar()
            
            # Tamanho do banco
            db_size = DB_PATH.stat().st_size if DB_PATH.exists() else 0
            
            # Verifica WAL file
            wal_path = DB_PATH.with_suffix('.db-wal')
            wal_size = wal_path.stat().st_size if wal_path.exists() else 0
            
            return {
                "status": "healthy",
                "journal_mode": journal_mode,
                "integrity": integrity,
                "db_size_bytes": db_size,
                "wal_size_bytes": wal_size,
                "db_path": str(DB_PATH)
            }
            
        except Exception as e:
            logger.error(f"Erro na verificação de saúde do DB: {e}")
            return {
                "status": "error",
                "error": str(e),
                "db_path": str(DB_PATH)
            }


async def vacuum_and_checkpoint():
    """
    Executa manutenção no banco de dados.
    Força checkpoint do WAL e otimiza espaço.
    """
    async with AsyncSessionLocal() as session:
        try:
            # Força checkpoint do WAL (consolida transações)
            await session.execute(text("PRAGMA wal_checkpoint(TRUNCATE)"))
            
            # Analisa estatísticas para otimizador de queries
            await session.execute(text("ANALYZE"))
            
            await session.commit()
            logger.info("Manutenção do banco de dados concluída.")
            
        except Exception as e:
            logger.error(f"Erro na manutenção do DB: {e}")
            raise


async def get_table_counts() -> dict:
    """
    Retorna contagem de registros em cada tabela.
    Útil para dashboard e diagnóstico.
    """
    from src.core.models import Produto, LayoutMeta, ProjetoSalvo, AuditLog
    from sqlalchemy import func, select
    
    async with AsyncSessionLocal() as session:
        counts = {}
        
        # Produtos
        result = await session.execute(select(func.count(Produto.id)))
        counts['produtos'] = result.scalar() or 0
        
        # Layouts
        result = await session.execute(select(func.count(LayoutMeta.id)))
        counts['layouts'] = result.scalar() or 0
        
        # Projetos
        result = await session.execute(select(func.count(ProjetoSalvo.id)))
        counts['projetos'] = result.scalar() or 0
        
        # Logs de Auditoria
        result = await session.execute(select(func.count(AuditLog.id)))
        counts['audit_logs'] = result.scalar() or 0
        
        return counts


# ==============================================================================
# PROTOCOLO MÁQUINA DO TEMPO: Snapshots Atômicos
# ==============================================================================

async def create_atomic_snapshot(output_path: str = None) -> str:
    """
    Cria snapshot atômico do banco de dados usando VACUUM INTO.
    
    PROTOCOLO MÁQUINA DO TEMPO (Vol. V, Cap. 3):
    - Backup a quente (sem parar o sistema)
    - Atômico (tudo ou nada)
    - Consistente (snapshot point-in-time)
    
    Args:
        output_path: Caminho do backup. Se None, gera automaticamente.
        
    Returns:
        Caminho do arquivo de backup criado
    """
    from datetime import datetime
    import os
    
    # Gera caminho se não especificado
    if output_path is None:
        snapshots_dir = DB_PATH.parent / "snapshots"
        os.makedirs(snapshots_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = str(snapshots_dir / f"core_snapshot_{timestamp}.db")
    else:
        # Garante que diretório existe
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    async with AsyncSessionLocal() as session:
        try:
            # VACUUM INTO: cria cópia atômica em um único comando
            # Isso é mais seguro que copiar arquivos manualmente
            await session.execute(text(f"VACUUM INTO '{output_path}'"))
            await session.commit()
            
            logger.info(f"Snapshot atômico criado: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Falha ao criar snapshot: {e}")
            raise


async def restore_from_snapshot(snapshot_path: str, backup_current: bool = True) -> bool:
    """
    Restaura banco de dados a partir de um snapshot.
    
    ATENÇÃO: Esta operação substitui o banco atual!
    
    Args:
        snapshot_path: Caminho do snapshot a restaurar
        backup_current: Se True, faz backup do estado atual antes
        
    Returns:
        True se restauração bem sucedida
    """
    import shutil
    from datetime import datetime
    
    snapshot_file = Path(snapshot_path)
    if not snapshot_file.exists():
        raise FileNotFoundError(f"Snapshot não encontrado: {snapshot_path}")
    
    try:
        # 1. Backup do estado atual (segurança)
        if backup_current:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = DB_PATH.parent / "snapshots" / f"pre_restore_{timestamp}.db"
            await create_atomic_snapshot(str(backup_path))
            logger.info(f"Backup pré-restauração criado: {backup_path}")
        
        # 2. Fecha conexões ativas (importante!)
        await engine.dispose()
        
        # 3. Remove WAL e SHM se existirem
        wal_file = DB_PATH.with_suffix('.db-wal')
        shm_file = DB_PATH.with_suffix('.db-shm')
        
        for f in [wal_file, shm_file]:
            if f.exists():
                f.unlink()
        
        # 4. Substitui o banco
        shutil.copy2(snapshot_path, DB_PATH)
        
        logger.info(f"Banco restaurado de: {snapshot_path}")
        return True
        
    except Exception as e:
        logger.error(f"Falha na restauração: {e}")
        raise


async def list_snapshots() -> list:
    """
    Lista todos os snapshots disponíveis.
    
    Returns:
        Lista de dicts com info de cada snapshot
    """
    import os
    from datetime import datetime
    
    snapshots_dir = DB_PATH.parent / "snapshots"
    if not snapshots_dir.exists():
        return []
    
    snapshots = []
    for f in sorted(snapshots_dir.iterdir(), reverse=True):
        if f.suffix == '.db':
            stat = f.stat()
            snapshots.append({
                "name": f.name,
                "path": str(f),
                "size_bytes": stat.st_size,
                "created_at": datetime.fromtimestamp(stat.st_mtime).isoformat()
            })
    
    return snapshots

"""
AutoTabloide AI - Configuração de Banco de Dados
==================================================
Camada de persistência conforme Vol. I, Cap. 1.3.
SQLite 3 com WAL Mode para concorrência não-bloqueante.
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
DB_PATH = DB_DIR / "core.db"

# URL de conexão assíncrona
DATABASE_URL = f"sqlite+aiosqlite:///{DB_PATH}"

# Garantia de existência do diretório (Evita crash inicial)
os.makedirs(DB_DIR, exist_ok=True)


# ==============================================================================
# ENGINE ASSÍNCRONA
# ==============================================================================

engine = create_async_engine(
    DATABASE_URL,
    echo=False,  # True apenas para debug profundo
    future=True,
    # Configurações de pool para SQLite
    pool_pre_ping=True,
)


# ==============================================================================
# PRAGMAS CRÍTICOS (Lei do Sistema - Vol. I, Cap. 1.3)
# ==============================================================================

@event.listens_for(engine.sync_engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
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
    # logger.debug("SQLite PRAGMAs configurados com sucesso.")


# ==============================================================================
# SESSION FACTORY
# ==============================================================================

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False
)


async def get_db():
    """
    Dependency Injection para sessões de banco de dados.
    Uso: async with get_db() as session: ...
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


def get_session_sync():
    """
    Retorna factory de sessão para uso direto (sem generator).
    Uso: session = await get_session_sync()()
    """
    return AsyncSessionLocal


# ==============================================================================
# INICIALIZAÇÃO DO SCHEMA
# ==============================================================================

async def init_db():
    """
    Inicializa o Schema no Banco de Dados.
    Cria todas as tabelas definidas em models.py se não existirem.
    """
    from src.core.models import Base
    
    async with engine.begin() as conn:
        # Em produção real, usaríamos Alembic para migrações.
        # Para o setup inicial, create_all é aceitável.
        await conn.run_sync(Base.metadata.create_all)
        logger.info(f"Schema do banco de dados inicializado em: {DB_PATH}")


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

import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import event, text

# Caminho absoluto para garantir soberania local e evitar caminhos relativos frágeis
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DB_DIR = os.path.join(BASE_DIR, "AutoTabloide_System_Root", "database") # Adjusted to match project structure
DB_PATH = os.path.join(DB_DIR, "core.db")
DATABASE_URL = f"sqlite+aiosqlite:///{DB_PATH}"

# Garantia de existência do diretório (Evita crash inicial)
os.makedirs(DB_DIR, exist_ok=True)

# Criação da Engine Assíncrona
engine = create_async_engine(
    DATABASE_URL,
    echo=False, # Manter False em produção para evitar poluição de logs
    future=True
)

# CRÍTICO: Configuração de Performance e Concorrência (Lei do Sistema)
@event.listens_for(engine.sync_engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    # WAL: Permite leitura e escrita simultânea
    cursor.execute("PRAGMA journal_mode=WAL")
    # NORMAL: Garante integridade sem o custo excessivo do FULL sync (ideal para disco local)
    cursor.execute("PRAGMA synchronous=NORMAL")
    # FK: Garante integridade referencial (Aliases não podem órfãos)
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()

# Factory de Sessões
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)

async def get_db():
    """Dependency Injection para Sessões de Banco de Dados"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
            
async def init_db():
    """Inicializa o Schema no Banco de Dados"""
    from src.core.models import Base
    async with engine.begin() as conn:
        # Em produção real, usaríamos Alembic para migrações.
        # Para o setup inicial, create_all é aceitável.
        await conn.run_sync(Base.metadata.create_all)

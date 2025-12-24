"""
Alembic Environment Configuration
===================================
Configura as conexões e metadados para migrations.
Passos 7-9 do Checklist 100.
"""

from logging.config import fileConfig
import asyncio
from pathlib import Path
import sys

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context

# Adiciona raiz do projeto ao path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Importa modelos e configurações
from src.core.models import Base, LearningBase
from src.core.database import CORE_DATABASE_URL, LEARNING_DATABASE_URL

# this is the Alembic Config object
config = context.config

# Interpret the config file for Python logging.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Metadatas para migrations
# Por padrão, migra o core.db
target_metadata = Base.metadata

# Para migrar learning.db, use: alembic -x db=learning upgrade head
# Determina qual banco migrar baseado no argumento -x
def get_url():
    db_type = context.get_x_argument(as_dictionary=True).get("db", "core")
    if db_type == "learning":
        return str(LEARNING_DATABASE_URL)
    return str(CORE_DATABASE_URL)


def get_metadata():
    db_type = context.get_x_argument(as_dictionary=True).get("db", "core")
    if db_type == "learning":
        return LearningBase.metadata
    return Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = get_url()
    context.configure(
        url=url,
        target_metadata=get_metadata(),
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(
        connection=connection,
        target_metadata=get_metadata()
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Run migrations in 'online' mode with async engine."""
    configuration = config.get_section(config.config_ini_section)
    configuration["sqlalchemy.url"] = get_url()
    
    connectable = async_engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()

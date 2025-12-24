"""
AutoTabloide AI - Alembic Boot Integration
=============================================
Integração de migrações Alembic no boot.
Passo 9 do Checklist 100.

Uso no main.py:
    from src.core.migrations import run_migrations_on_boot
    run_migrations_on_boot()
"""

import asyncio
from pathlib import Path
from typing import Optional

from src.core.logging_config import get_logger
from src.core.constants import BASE_DIR

logger = get_logger("Migrations")

# Diretório de migrações
ALEMBIC_DIR = BASE_DIR / "alembic"
ALEMBIC_INI = BASE_DIR / "alembic.ini"


def check_alembic_available() -> bool:
    """Verifica se Alembic está configurado."""
    return ALEMBIC_INI.exists() and ALEMBIC_DIR.exists()


def run_migrations_on_boot() -> bool:
    """
    Executa migrações pendentes no boot.
    Passo 9 do Checklist - Script de migração no boot.
    
    Returns:
        True se sucesso
    """
    if not check_alembic_available():
        logger.warning("Alembic não configurado, pulando migrações")
        return True
    
    try:
        from alembic.config import Config
        from alembic import command
        from alembic.script import ScriptDirectory
        from alembic.runtime.migration import MigrationContext
        from sqlalchemy import create_engine
        
        # Carrega configuração
        alembic_cfg = Config(str(ALEMBIC_INI))
        
        # Verifica se há migrações pendentes
        script = ScriptDirectory.from_config(alembic_cfg)
        
        # Para core.db
        core_db = BASE_DIR / "AutoTabloide_System_Root" / "database" / "core.db"
        if core_db.exists():
            engine = create_engine(f"sqlite:///{core_db}")
            with engine.connect() as conn:
                context = MigrationContext.configure(conn)
                current_rev = context.get_current_revision()
                head_rev = script.get_current_head()
                
                if current_rev != head_rev:
                    logger.info(f"Migrações pendentes: {current_rev} -> {head_rev}")
                    command.upgrade(alembic_cfg, "head")
                    logger.info("Migrações aplicadas com sucesso")
                else:
                    logger.debug("Banco já está na versão mais recente")
        
        return True
        
    except ImportError:
        logger.warning("Alembic não instalado")
        return True
    except Exception as e:
        logger.error(f"Erro ao executar migrações: {e}")
        return False


def create_migration(message: str) -> Optional[Path]:
    """
    Cria nova migração.
    
    Args:
        message: Descrição da migração
        
    Returns:
        Caminho do arquivo criado ou None
    """
    if not check_alembic_available():
        logger.error("Alembic não configurado")
        return None
    
    try:
        from alembic.config import Config
        from alembic import command
        
        alembic_cfg = Config(str(ALEMBIC_INI))
        command.revision(alembic_cfg, message=message, autogenerate=True)
        
        logger.info(f"Migração criada: {message}")
        
        # Retorna arquivo mais recente
        versions_dir = ALEMBIC_DIR / "versions"
        if versions_dir.exists():
            files = sorted(versions_dir.glob("*.py"), key=lambda p: p.stat().st_mtime, reverse=True)
            if files:
                return files[0]
        
        return None
        
    except Exception as e:
        logger.error(f"Erro ao criar migração: {e}")
        return None


def get_migration_history() -> list:
    """
    Retorna histórico de migrações.
    
    Returns:
        Lista de dicts com info de cada migração
    """
    if not check_alembic_available():
        return []
    
    try:
        from alembic.config import Config
        from alembic.script import ScriptDirectory
        
        alembic_cfg = Config(str(ALEMBIC_INI))
        script = ScriptDirectory.from_config(alembic_cfg)
        
        history = []
        for rev in script.walk_revisions():
            history.append({
                "revision": rev.revision,
                "down_revision": rev.down_revision,
                "message": rev.doc,
                "date": rev.module.__dict__.get("revision_date")
            })
        
        return history
        
    except Exception as e:
        logger.error(f"Erro ao obter histórico: {e}")
        return []

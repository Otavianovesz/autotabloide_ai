"""
AutoTabloide AI - Data Security Utilities
============================================
Utilitários de segurança de dados.
Passos 41-50 do Checklist v2.

Funcionalidades:
- Migrations automáticas no boot (41)
- Backup pré-migração (42)
- Sanitização de inputs (43) - ver ui_safety.py
- Validação preço negativo (44) - ver ui_safety.py
- View de AuditLog (45)
- Instance lock (46)
- Hash de template (47)
- Validação SKU duplicado (49)
- Limpeza de AuditLog antigo (50)
"""

import asyncio
import hashlib
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Tuple, List, Dict

from src.core.logging_config import get_logger
from src.core.constants import SYSTEM_ROOT

logger = get_logger("DataSecurity")


# Diretórios
DB_DIR = SYSTEM_ROOT / "database"
BACKUP_DIR = SYSTEM_ROOT / "backups"
BACKUP_DIR.mkdir(parents=True, exist_ok=True)


def create_backup_before_migration() -> Optional[Path]:
    """
    Cria backup do banco antes de migração.
    Passo 42 do Checklist v2.
    
    Returns:
        Caminho do backup ou None se falhar
    """
    core_db = DB_DIR / "core.db"
    
    if not core_db.exists():
        logger.debug("Banco core.db não existe, pulando backup")
        return None
    
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = BACKUP_DIR / f"core_pre_migration_{timestamp}.db"
        
        shutil.copy2(core_db, backup_path)
        
        logger.info(f"Backup pré-migração criado: {backup_path}")
        return backup_path
        
    except Exception as e:
        logger.error(f"Erro ao criar backup: {e}")
        return None


def calculate_template_hash(template_path: Path) -> str:
    """
    Calcula hash SHA256 de template SVG.
    Passo 47 do Checklist v2.
    
    Args:
        template_path: Caminho do template
        
    Returns:
        Hash hexadecimal
    """
    if not template_path.exists():
        return ""
    
    sha256 = hashlib.sha256()
    
    with open(template_path, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            sha256.update(chunk)
    
    return sha256.hexdigest()


def verify_template_integrity(
    saved_hash: str,
    template_path: Path
) -> Tuple[bool, str]:
    """
    Verifica integridade do template.
    Passo 47 do Checklist v2.
    
    Args:
        saved_hash: Hash salvo no projeto
        template_path: Caminho atual do template
        
    Returns:
        Tupla (intacto, mensagem)
    """
    if not template_path.exists():
        return False, "Template não encontrado"
    
    current_hash = calculate_template_hash(template_path)
    
    if not saved_hash:
        return True, "Projeto sem hash (versão antiga)"
    
    if saved_hash == current_hash:
        return True, "Template intacto"
    
    return False, "AVISO: Template foi modificado desde a criação do projeto"


async def check_sku_duplicate(sku: str) -> Tuple[bool, Optional[int]]:
    """
    Verifica se SKU já existe no banco.
    Passo 49 do Checklist v2.
    
    Args:
        sku: SKU a verificar
        
    Returns:
        Tupla (existe, id_existente)
    """
    try:
        from src.core.database import AsyncSessionLocal
        from src.core.repositories import ProductRepository
        
        async with AsyncSessionLocal() as session:
            repo = ProductRepository(session)
            existing = await repo.get_by_sku(sku)
            
            if existing:
                return True, existing.id
            
            return False, None
            
    except Exception as e:
        logger.error(f"Erro ao verificar SKU: {e}")
        return False, None


async def cleanup_old_audit_logs(retention_days: int = 365) -> int:
    """
    Remove logs de auditoria antigos.
    Passo 50 do Checklist v2.
    
    Args:
        retention_days: Dias para manter logs
        
    Returns:
        Número de registros removidos
    """
    try:
        from src.core.database import AsyncSessionLocal
        from src.core.models import AuditLog
        from sqlalchemy import delete
        from datetime import datetime, timedelta
        
        cutoff = datetime.now() - timedelta(days=retention_days)
        
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                delete(AuditLog).where(AuditLog.created_at < cutoff)
            )
            await session.commit()
            
            deleted = result.rowcount
            
            if deleted > 0:
                logger.info(f"AuditLog: {deleted} registros antigos removidos (>{retention_days} dias)")
            
            return deleted
            
    except Exception as e:
        logger.error(f"Erro ao limpar AuditLog: {e}")
        return 0


async def get_audit_log_summary(limit: int = 100) -> List[Dict]:
    """
    Retorna resumo do AuditLog para UI.
    Passo 45 do Checklist v2.
    
    Args:
        limit: Máximo de registros
        
    Returns:
        Lista de dicts com logs
    """
    try:
        from src.core.database import AsyncSessionLocal
        from src.core.models import AuditLog
        from sqlalchemy import select
        
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(AuditLog)
                .order_by(AuditLog.created_at.desc())
                .limit(limit)
            )
            logs = result.scalars().all()
            
            return [
                {
                    "id": log.id,
                    "action": log.action,
                    "entity_type": log.entity_type,
                    "entity_id": log.entity_id,
                    "old_value": log.old_value,
                    "new_value": log.new_value,
                    "created_at": log.created_at.isoformat() if log.created_at else None,
                    "user_id": log.user_id
                }
                for log in logs
            ]
            
    except Exception as e:
        logger.error(f"Erro ao obter AuditLog: {e}")
        return []


def run_migrations_with_backup() -> bool:
    """
    Executa migrações com backup prévio.
    Passos 41-42 do Checklist v2.
    
    Returns:
        True se sucesso
    """
    # Backup primeiro
    backup_path = create_backup_before_migration()
    
    try:
        from src.core.migrations import run_migrations_on_boot
        success = run_migrations_on_boot()
        
        if success:
            logger.info("Migrações aplicadas com sucesso")
        
        return success
        
    except Exception as e:
        logger.error(f"Erro nas migrações: {e}")
        
        # Tenta restaurar backup se falhou
        if backup_path and backup_path.exists():
            core_db = DB_DIR / "core.db"
            try:
                shutil.copy2(backup_path, core_db)
                logger.info("Backup restaurado após falha de migração")
            except:
                pass
        
        return False


class AuditLogViewer:
    """
    Visualizador de logs de auditoria.
    Passo 45 - Para integração na UI.
    """
    
    @staticmethod
    async def get_recent(limit: int = 50) -> List[Dict]:
        """Obtém logs recentes."""
        return await get_audit_log_summary(limit)
    
    @staticmethod
    async def get_by_entity(entity_type: str, entity_id: int) -> List[Dict]:
        """Obtém logs de uma entidade específica."""
        try:
            from src.core.database import AsyncSessionLocal
            from src.core.models import AuditLog
            from sqlalchemy import select
            
            async with AsyncSessionLocal() as session:
                result = await session.execute(
                    select(AuditLog)
                    .where(AuditLog.entity_type == entity_type)
                    .where(AuditLog.entity_id == entity_id)
                    .order_by(AuditLog.created_at.desc())
                )
                logs = result.scalars().all()
                
                return [
                    {
                        "id": log.id,
                        "action": log.action,
                        "old_value": log.old_value,
                        "new_value": log.new_value,
                        "created_at": log.created_at.isoformat() if log.created_at else None,
                    }
                    for log in logs
                ]
                
        except Exception as e:
            logger.error(f"Erro: {e}")
            return []

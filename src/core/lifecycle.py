"""
AutoTabloide AI - Lifecycle Management
========================================
Rotinas de inicialização e shutdown do sistema.
Passos 13-15 do Checklist 100.

Funcionalidades:
- Limpeza de logs antigos (>7 dias)
- Limpeza de temp/ no shutdown
- Verificação de integridade no boot
"""

import asyncio
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import List

from src.core.logging_config import get_logger
from src.core.constants import SYSTEM_ROOT
from src.core.settings_service import settings_service

logger = get_logger("Lifecycle")

# Diretórios de manutenção
TEMP_RENDER_DIR = SYSTEM_ROOT / "temp_render"
STAGING_DIR = SYSTEM_ROOT / "staging"
LOGS_DIR = SYSTEM_ROOT / "logs"
CACHE_DIR = SYSTEM_ROOT / "cache"


def ensure_directories() -> None:
    """
    Garante existência de todos os diretórios do sistema.
    Chamado no boot da aplicação.
    """
    directories = [
        SYSTEM_ROOT,
        SYSTEM_ROOT / "database",
        SYSTEM_ROOT / "assets" / "store",
        SYSTEM_ROOT / "assets" / "fonts",
        SYSTEM_ROOT / "library" / "svg_source",
        SYSTEM_ROOT / "library" / "thumbnails",
        SYSTEM_ROOT / "workspace" / "projects",
        SYSTEM_ROOT / "config",
        SYSTEM_ROOT / "snapshots",
        SYSTEM_ROOT / "bin" / "models",
        TEMP_RENDER_DIR,
        STAGING_DIR,
        LOGS_DIR,
        CACHE_DIR / "processed",
    ]
    
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Estrutura de diretórios verificada: {len(directories)} pastas")


def clean_temp_directory() -> int:
    """
    Limpa diretório temp_render completamente.
    Passo 15 do Checklist - Executado no shutdown.
    
    Returns:
        Número de arquivos removidos
    """
    count = 0
    
    try:
        if TEMP_RENDER_DIR.exists():
            for item in TEMP_RENDER_DIR.iterdir():
                try:
                    if item.is_file():
                        item.unlink()
                        count += 1
                    elif item.is_dir():
                        shutil.rmtree(item)
                        count += 1
                except Exception as e:
                    logger.warning(f"Não foi possível remover {item}: {e}")
        
        logger.info(f"Temp limpo: {count} itens removidos")
        
    except Exception as e:
        logger.error(f"Erro ao limpar temp: {e}")
    
    return count


def clean_staging_directory() -> int:
    """
    Limpa diretório de staging (quarentena de downloads).
    
    Returns:
        Número de arquivos removidos
    """
    count = 0
    
    try:
        if STAGING_DIR.exists():
            for item in STAGING_DIR.iterdir():
                try:
                    if item.is_file():
                        item.unlink()
                        count += 1
                except Exception as e:
                    logger.warning(f"Não foi possível remover {item}: {e}")
        
        if count > 0:
            logger.info(f"Staging limpo: {count} arquivos removidos")
        
    except Exception as e:
        logger.error(f"Erro ao limpar staging: {e}")
    
    return count


def clean_old_logs(retention_days: int = 7) -> int:
    """
    Remove arquivos de log mais antigos que retention_days.
    Passo 14 do Checklist.
    
    Args:
        retention_days: Dias para manter logs
        
    Returns:
        Número de arquivos removidos
    """
    count = 0
    cutoff = datetime.now() - timedelta(days=retention_days)
    
    try:
        if LOGS_DIR.exists():
            for log_file in LOGS_DIR.glob("*.log*"):
                try:
                    mtime = datetime.fromtimestamp(log_file.stat().st_mtime)
                    if mtime < cutoff:
                        log_file.unlink()
                        count += 1
                except Exception as e:
                    logger.warning(f"Não foi possível remover {log_file}: {e}")
        
        if count > 0:
            logger.info(f"Logs antigos removidos: {count} arquivos (>{retention_days} dias)")
        
    except Exception as e:
        logger.error(f"Erro ao limpar logs: {e}")
    
    return count


def get_disk_usage() -> dict:
    """
    Retorna uso de disco do sistema.
    
    Returns:
        Dict com tamanhos de cada diretório
    """
    def get_size(path: Path) -> int:
        total = 0
        try:
            if path.is_file():
                return path.stat().st_size
            for item in path.rglob("*"):
                if item.is_file():
                    total += item.stat().st_size
        except Exception:
            pass
        return total
    
    return {
        "database": get_size(SYSTEM_ROOT / "database"),
        "assets": get_size(SYSTEM_ROOT / "assets"),
        "cache": get_size(CACHE_DIR),
        "temp": get_size(TEMP_RENDER_DIR),
        "logs": get_size(LOGS_DIR),
        "total": get_size(SYSTEM_ROOT)
    }


async def startup_routine() -> None:
    """
    Rotina de inicialização do sistema.
    Deve ser chamada uma vez no boot.
    """
    logger.info("=" * 50)
    logger.info("AUTOTABLOIDE AI - INICIALIZAÇÃO")
    logger.info("=" * 50)
    
    # 1. Garantir diretórios
    ensure_directories()
    
    # 2. Limpar temp do boot anterior
    clean_temp_directory()
    
    # 3. Limpar staging
    clean_staging_directory()
    
    # 4. Limpar logs antigos
    retention = settings_service.get("logs.retention_days", 7)
    clean_old_logs(retention)
    
    # 5. Log de métricas
    usage = get_disk_usage()
    logger.info(f"Uso de disco: {usage['total'] / (1024*1024):.1f} MB total")
    
    logger.info("Inicialização concluída")


async def shutdown_routine() -> None:
    """
    Rotina de encerramento do sistema.
    Deve ser chamada no shutdown.
    """
    logger.info("=" * 50)
    logger.info("AUTOTABLOIDE AI - ENCERRANDO")
    logger.info("=" * 50)
    
    # 1. Limpar temp
    clean_temp_directory()
    
    # 2. Limpar staging
    clean_staging_directory()
    
    # 3. Importar e fechar conexões de banco
    try:
        from src.core.database import core_engine, learning_engine
        await core_engine.dispose()
        await learning_engine.dispose()
        logger.info("Conexões de banco fechadas")
    except Exception as e:
        logger.error(f"Erro ao fechar banco: {e}")
    
    logger.info("Encerramento concluído")


def sanitize_filename(name: str) -> str:
    """
    Sanitiza nome de arquivo removendo caracteres inválidos.
    Passo 66 do Checklist.
    
    Args:
        name: Nome original
        
    Returns:
        Nome sanitizado
    """
    # Caracteres inválidos no Windows
    invalid_chars = '<>:"/\\|?*'
    
    result = name
    for char in invalid_chars:
        result = result.replace(char, '_')
    
    # Remover espaços extras
    result = ' '.join(result.split())
    
    # Limitar tamanho
    if len(result) > 200:
        result = result[:200]
    
    return result.strip() or "sem_nome"


def validate_path_security(path: Path, allowed_root: Path = SYSTEM_ROOT) -> bool:
    """
    Valida se um caminho está dentro do diretório permitido.
    Previne path traversal attacks.
    
    Args:
        path: Caminho a validar
        allowed_root: Diretório raiz permitido
        
    Returns:
        True se caminho é seguro
    """
    try:
        resolved = path.resolve()
        allowed = allowed_root.resolve()
        return str(resolved).startswith(str(allowed))
    except Exception:
        return False

"""
AutoTabloide AI - Database Utilities
====================================
PROTOCOLO DE RETIFICAÇÃO NÍVEL 0 - Fase 2 (Passos 46-50)
Utilitários para operações de banco de dados.
"""

from __future__ import annotations
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
import logging
import sqlite3
import json

logger = logging.getLogger("DBUtils")


# =============================================================================
# CONNECTION POOL
# =============================================================================

class ConnectionPool:
    """Pool simples de conexões SQLite."""
    
    _connections: Dict[str, sqlite3.Connection] = {}
    
    @classmethod
    def get(cls, db_path: str) -> sqlite3.Connection:
        """Obtém conexão do pool."""
        if db_path not in cls._connections:
            conn = sqlite3.connect(db_path, check_same_thread=False)
            conn.row_factory = sqlite3.Row
            cls._connections[db_path] = conn
        return cls._connections[db_path]
    
    @classmethod
    def close_all(cls):
        """Fecha todas as conexões."""
        for conn in cls._connections.values():
            conn.close()
        cls._connections.clear()


# =============================================================================
# QUERY HELPERS
# =============================================================================

def fetch_one(db_path: str, query: str, params: tuple = ()) -> Optional[Dict]:
    """Executa query e retorna primeiro resultado."""
    conn = ConnectionPool.get(db_path)
    try:
        cursor = conn.execute(query, params)
        row = cursor.fetchone()
        return dict(row) if row else None
    except Exception as e:
        logger.error(f"Query error: {e}")
        return None


def fetch_all(db_path: str, query: str, params: tuple = ()) -> List[Dict]:
    """Executa query e retorna todos os resultados."""
    conn = ConnectionPool.get(db_path)
    try:
        cursor = conn.execute(query, params)
        return [dict(row) for row in cursor.fetchall()]
    except Exception as e:
        logger.error(f"Query error: {e}")
        return []


def execute(db_path: str, query: str, params: tuple = ()) -> bool:
    """Executa query de modificação."""
    conn = ConnectionPool.get(db_path)
    try:
        conn.execute(query, params)
        conn.commit()
        return True
    except Exception as e:
        logger.error(f"Execute error: {e}")
        return False


def execute_many(db_path: str, query: str, params_list: List[tuple]) -> int:
    """Executa query em lote."""
    conn = ConnectionPool.get(db_path)
    try:
        cursor = conn.executemany(query, params_list)
        conn.commit()
        return cursor.rowcount
    except Exception as e:
        logger.error(f"Execute many error: {e}")
        return 0


# =============================================================================
# BACKUP & RESTORE
# =============================================================================

def backup_database(db_path: str, backup_dir: str = None) -> Optional[str]:
    """Cria backup do banco de dados."""
    import shutil
    
    src = Path(db_path)
    if not src.exists():
        return None
    
    backup_dir = Path(backup_dir) if backup_dir else src.parent / "backups"
    backup_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = backup_dir / f"{src.stem}_{timestamp}{src.suffix}"
    
    try:
        shutil.copy2(src, backup_path)
        logger.info(f"Backup criado: {backup_path}")
        return str(backup_path)
    except Exception as e:
        logger.error(f"Backup error: {e}")
        return None


def vacuum_database(db_path: str):
    """Compacta banco de dados."""
    conn = ConnectionPool.get(db_path)
    try:
        conn.execute("VACUUM")
        logger.info(f"VACUUM executado: {db_path}")
    except Exception as e:
        logger.error(f"Vacuum error: {e}")


# =============================================================================
# INTEGRITY CHECKS
# =============================================================================

def check_integrity(db_path: str) -> bool:
    """Verifica integridade do banco."""
    conn = ConnectionPool.get(db_path)
    try:
        result = conn.execute("PRAGMA integrity_check").fetchone()
        ok = result[0] == "ok"
        if not ok:
            logger.error(f"Integrity check failed: {result[0]}")
        return ok
    except Exception as e:
        logger.error(f"Integrity check error: {e}")
        return False


def get_db_stats(db_path: str) -> Dict:
    """Retorna estatísticas do banco."""
    conn = ConnectionPool.get(db_path)
    stats = {
        "path": db_path,
        "size_mb": Path(db_path).stat().st_size / (1024 * 1024) if Path(db_path).exists() else 0,
        "tables": [],
    }
    
    try:
        tables = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()
        
        for table in tables:
            name = table[0]
            count = conn.execute(f"SELECT COUNT(*) FROM {name}").fetchone()[0]
            stats["tables"].append({"name": name, "count": count})
    except Exception as e:
        logger.error(f"Stats error: {e}")
    
    return stats


# =============================================================================
# MIGRATION HELPERS
# =============================================================================

def table_exists(db_path: str, table_name: str) -> bool:
    """Verifica se tabela existe."""
    conn = ConnectionPool.get(db_path)
    result = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
        (table_name,)
    ).fetchone()
    return result is not None


def column_exists(db_path: str, table_name: str, column_name: str) -> bool:
    """Verifica se coluna existe."""
    conn = ConnectionPool.get(db_path)
    try:
        cursor = conn.execute(f"PRAGMA table_info({table_name})")
        columns = [row[1] for row in cursor.fetchall()]
        return column_name in columns
    except:
        return False


def add_column_if_not_exists(
    db_path: str,
    table_name: str,
    column_name: str,
    column_type: str,
    default: Any = None
) -> bool:
    """Adiciona coluna se não existir."""
    if column_exists(db_path, table_name, column_name):
        return True
    
    query = f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}"
    if default is not None:
        query += f" DEFAULT {default!r}"
    
    return execute(db_path, query)

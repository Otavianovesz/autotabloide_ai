"""
AutoTabloide AI - Mutex de Instância Única
============================================
Previne múltiplas instâncias do aplicativo.
Passo 92 do Checklist 100.

Uso:
    if not acquire_instance_lock():
        print("Outra instância já está rodando!")
        sys.exit(1)
"""

import os
import sys
from pathlib import Path
from typing import Optional

from src.core.logging_config import get_logger
from src.core.constants import SYSTEM_ROOT

logger = get_logger("InstanceLock")

# Arquivo de lock
LOCK_FILE = SYSTEM_ROOT / "config" / ".autotabloide.lock"
_lock_handle = None


def acquire_instance_lock() -> bool:
    """
    Tenta adquirir lock de instância única.
    Passo 92 do Checklist.
    
    Returns:
        True se conseguiu o lock, False se outra instância está rodando
    """
    global _lock_handle
    
    # Garante diretório existe
    LOCK_FILE.parent.mkdir(parents=True, exist_ok=True)
    
    if sys.platform == "win32":
        return _acquire_lock_windows()
    else:
        return _acquire_lock_unix()


def _acquire_lock_windows() -> bool:
    """Implementação Windows usando msvcrt."""
    global _lock_handle
    
    try:
        import msvcrt
        
        # Tenta abrir/criar arquivo de lock
        _lock_handle = open(LOCK_FILE, "w")
        
        # Tenta lock exclusivo (não-bloqueante)
        try:
            msvcrt.locking(_lock_handle.fileno(), msvcrt.LK_NBLCK, 1)
            
            # Escreve PID
            _lock_handle.write(str(os.getpid()))
            _lock_handle.flush()
            
            logger.debug("Lock de instância adquirido")
            return True
            
        except IOError:
            # Lock já existe
            _lock_handle.close()
            _lock_handle = None
            logger.warning("Outra instância do AutoTabloide AI já está rodando")
            return False
            
    except Exception as e:
        logger.error(f"Erro ao adquirir lock: {e}")
        return True  # Em caso de erro, permite execução


def _acquire_lock_unix() -> bool:
    """Implementação Unix usando fcntl."""
    global _lock_handle
    
    try:
        import fcntl
        
        _lock_handle = open(LOCK_FILE, "w")
        
        try:
            fcntl.flock(_lock_handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            
            _lock_handle.write(str(os.getpid()))
            _lock_handle.flush()
            
            logger.debug("Lock de instância adquirido")
            return True
            
        except IOError:
            _lock_handle.close()
            _lock_handle = None
            logger.warning("Outra instância do AutoTabloide AI já está rodando")
            return False
            
    except ImportError:
        # fcntl não disponível
        return True
    except Exception as e:
        logger.error(f"Erro ao adquirir lock: {e}")
        return True


def release_instance_lock() -> None:
    """
    Libera lock de instância.
    Deve ser chamado no shutdown do aplicativo.
    """
    global _lock_handle
    
    if _lock_handle:
        try:
            _lock_handle.close()
            _lock_handle = None
            
            # Remove arquivo de lock
            if LOCK_FILE.exists():
                LOCK_FILE.unlink()
            
            logger.debug("Lock de instância liberado")
            
        except Exception as e:
            logger.warning(f"Erro ao liberar lock: {e}")


def get_running_pid() -> Optional[int]:
    """
    Retorna PID da instância rodando (se houver).
    """
    if not LOCK_FILE.exists():
        return None
    
    try:
        pid_str = LOCK_FILE.read_text().strip()
        return int(pid_str)
    except Exception:
        return None


def is_another_instance_running() -> bool:
    """
    Verifica se outra instância está rodando.
    """
    pid = get_running_pid()
    if pid is None:
        return False
    
    # Verifica se processo existe
    try:
        import psutil
        return psutil.pid_exists(pid)
    except ImportError:
        # Sem psutil, tenta signal
        try:
            os.kill(pid, 0)
            return True
        except OSError:
            return False

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


def bring_existing_window_to_focus() -> bool:
    """
    PASSO 4 DO PROTOCOLO: Traz janela existente para o foco.
    
    Antes de matar o novo processo, tenta trazer a janela existente
    para o primeiro plano para que o usuário saiba onde está.
    
    Returns:
        True se conseguiu trazer para foco
    """
    if sys.platform != "win32":
        return False
    
    pid = get_running_pid()
    if pid is None:
        return False
    
    try:
        import ctypes
        from ctypes import wintypes
        
        user32 = ctypes.windll.user32
        kernel32 = ctypes.windll.kernel32
        
        # Callback para EnumWindows
        EnumWindowsProc = ctypes.WINFUNCTYPE(
            wintypes.BOOL, wintypes.HWND, wintypes.LPARAM
        )
        
        found_hwnd = None
        
        def enum_callback(hwnd, lparam):
            nonlocal found_hwnd
            
            # Obtém PID da janela
            window_pid = wintypes.DWORD()
            user32.GetWindowThreadProcessId(hwnd, ctypes.byref(window_pid))
            
            if window_pid.value == pid:
                # Verifica se é janela principal (não child, visível)
                if user32.IsWindowVisible(hwnd) and not user32.GetParent(hwnd):
                    # Verifica título contém "AutoTabloide"
                    length = user32.GetWindowTextLengthW(hwnd) + 1
                    title = ctypes.create_unicode_buffer(length)
                    user32.GetWindowTextW(hwnd, title, length)
                    
                    if "AutoTabloide" in title.value:
                        found_hwnd = hwnd
                        return False  # Para enumeração
            
            return True
        
        # Enumera todas as janelas
        user32.EnumWindows(EnumWindowsProc(enum_callback), 0)
        
        if found_hwnd:
            # Restaura se minimizada
            SW_RESTORE = 9
            user32.ShowWindow(found_hwnd, SW_RESTORE)
            
            # Traz para frente
            user32.SetForegroundWindow(found_hwnd)
            
            # Força foco
            user32.BringWindowToTop(found_hwnd)
            
            logger.info(f"Janela existente trazida para foco (PID: {pid})")
            return True
        
        return False
        
    except Exception as e:
        logger.debug(f"Não foi possível trazer janela para foco: {e}")
        return False


def acquire_or_focus() -> bool:
    """
    Tenta adquirir lock, se falhar traz janela existente para foco.
    
    PASSO 4 COMPLETO: Em vez de apenas mostrar mensagem,
    traz a janela existente para o primeiro plano.
    
    Returns:
        True se adquiriu lock (pode continuar)
        False se outra instância estava rodando (deve sair)
    """
    if acquire_instance_lock():
        return True
    
    # Não conseguiu lock - tenta trazer janela existente para foco
    bring_existing_window_to_focus()
    
    return False

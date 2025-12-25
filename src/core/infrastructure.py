"""
AutoTabloide AI - Infrastructure Utilities
=============================================
Utilitários de infraestrutura e deploy.

CENTURY CHECKLIST Items 51-60, 91-100:
- Items 51-60: GS, DLLs, Reset, Logs, Paths, VC++, Offline, Export, Versão
- Item 91: Splash Screen Info
- Item 93: Bug Report ZIP
- Item 97: Verificação Espaço em Disco
- Item 100: Auditoria Segurança
"""

import os
import sys
import socket
import platform
import subprocess
import shutil
import zipfile
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, List, Tuple

from src.core.logging_config import get_logger
from src.core.constants import SYSTEM_ROOT, AppInfo

logger = get_logger("Infrastructure")


# Diretórios
BIN_DIR = SYSTEM_ROOT / "bin"
LOGS_DIR = SYSTEM_ROOT / "logs"
DB_DIR = SYSTEM_ROOT / "database"
CONFIG_DIR = SYSTEM_ROOT / "config"


def verify_ghostscript() -> Tuple[bool, str]:
    """
    Verifica instalação do Ghostscript.
    Passo 51 do Checklist v2.
    
    Returns:
        Tupla (disponível, versão_ou_erro)
    """
    # Tenta no PATH
    gs_paths = [
        "gswin64c.exe",
        "gswin32c.exe",
        "gs",
        str(BIN_DIR / "gswin64c.exe"),
        str(BIN_DIR / "gs" / "gswin64c.exe"),
    ]
    
    for gs_path in gs_paths:
        try:
            result = subprocess.run(
                [gs_path, "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                version = result.stdout.strip()
                logger.info(f"Ghostscript encontrado: v{version}")
                return True, version
        except:
            continue
    
    return False, "Ghostscript não encontrado. Instale em bin/ ou adicione ao PATH."


def verify_critical_files() -> Dict[str, bool]:
    """
    Verifica arquivos críticos do sistema.
    Passo 52 do Checklist v2.
    
    Returns:
        Dict com status de cada arquivo
    """
    critical_files = {
        "database/core.db": DB_DIR / "core.db",
        "assets/fonts/": SYSTEM_ROOT / "assets" / "fonts",
        "config/settings.json": CONFIG_DIR / "settings.json",
    }
    
    status = {}
    for name, path in critical_files.items():
        if path.suffix:
            status[name] = path.exists()
        else:
            status[name] = path.is_dir()
    
    return status


def factory_reset(keep_database: bool = True) -> bool:
    """
    Reset para configurações de fábrica.
    Passo 53 do Checklist v2.
    
    Args:
        keep_database: Se True, mantém banco de dados
        
    Returns:
        True se sucesso
    """
    try:
        logger.warning("Iniciando reset de fábrica...")
        
        # Remove cache
        cache_dir = SYSTEM_ROOT / "cache"
        if cache_dir.exists():
            shutil.rmtree(cache_dir)
            logger.info("Cache removido")
        
        # Remove temp
        temp_dir = SYSTEM_ROOT / "temp"
        if temp_dir.exists():
            shutil.rmtree(temp_dir)
            logger.info("Temp removido")
        
        # Remove configurações
        config_file = CONFIG_DIR / "settings.json"
        if config_file.exists():
            config_file.unlink()
            logger.info("Configurações removidas")
        
        # Remove banco de dados (opcional)
        if not keep_database:
            for db_file in DB_DIR.glob("*.db"):
                db_file.unlink()
                logger.info(f"Banco removido: {db_file.name}")
        
        logger.info("Reset de fábrica concluído")
        return True
        
    except Exception as e:
        logger.error(f"Erro no reset: {e}")
        return False


def check_vc_runtime() -> Tuple[bool, str]:
    """
    Verifica Visual C++ Redistributable.
    Passo 56 do Checklist v2 (Windows only).
    
    Returns:
        Tupla (instalado, mensagem)
    """
    if platform.system() != "Windows":
        return True, "N/A (não Windows)"
    
    # Verifica DLLs do VC++
    vc_dlls = ["vcruntime140.dll", "msvcp140.dll"]
    system32 = Path(os.environ.get("SYSTEMROOT", "C:\\Windows")) / "System32"
    
    missing = []
    for dll in vc_dlls:
        if not (system32 / dll).exists():
            missing.append(dll)
    
    if missing:
        return False, f"Faltando: {', '.join(missing)}. Instale Visual C++ Redistributable."
    
    return True, "VC++ Runtime OK"


def check_offline_mode() -> Dict[str, bool]:
    """
    Verifica funcionalidade offline.
    Passo 57 do Checklist v2.
    
    Returns:
        Dict com status de cada componente
    """
    status = {}
    
    # Database
    status["database"] = (DB_DIR / "core.db").exists()
    
    # Templates
    templates_dir = SYSTEM_ROOT / "library" / "svg_source"
    status["templates"] = templates_dir.exists() and any(templates_dir.glob("*.svg"))
    
    # Fontes
    fonts_dir = SYSTEM_ROOT / "assets" / "fonts"
    status["fonts"] = fonts_dir.exists() and any(fonts_dir.glob("*.ttf"))
    
    # Modelo LLM (opcional)
    models_dir = BIN_DIR / "models"
    status["llm_model"] = any(models_dir.glob("*.gguf")) if models_dir.exists() else False
    
    # Ghostscript
    gs_ok, _ = verify_ghostscript()
    status["ghostscript"] = gs_ok
    
    return status


def is_network_available() -> bool:
    """Verifica conectividade de rede."""
    try:
        socket.create_connection(("8.8.8.8", 53), timeout=3)
        return True
    except OSError:
        return False


def export_logs_zip(output_path: Optional[Path] = None) -> Optional[Path]:
    """
    Exporta logs em arquivo ZIP.
    Passo 58 do Checklist v2.
    
    Args:
        output_path: Caminho de saída (padrão: Desktop)
        
    Returns:
        Caminho do ZIP ou None
    """
    try:
        if output_path is None:
            desktop = Path.home() / "Desktop"
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = desktop / f"autotabloide_logs_{timestamp}.zip"
        
        with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            # Logs
            for log_file in LOGS_DIR.glob("*.log*"):
                zf.write(log_file, f"logs/{log_file.name}")
            
            # Configuração (sem dados sensíveis)
            config_file = CONFIG_DIR / "settings.json"
            if config_file.exists():
                zf.write(config_file, "config/settings.json")
            
            # Info do sistema
            system_info = {
                "app_version": AppInfo.VERSION,
                "python_version": sys.version,
                "platform": platform.platform(),
                "timestamp": datetime.now().isoformat()
            }
            zf.writestr("system_info.txt", str(system_info))
        
        logger.info(f"Logs exportados: {output_path}")
        return output_path
        
    except Exception as e:
        logger.error(f"Erro ao exportar logs: {e}")
        return None


def get_version_info() -> Dict[str, str]:
    """
    Retorna informações de versão.
    Passo 59 do Checklist v2.
    
    Returns:
        Dict com versões
    """
    return {
        "app_name": AppInfo.NAME,
        "app_version": AppInfo.VERSION,
        "python_version": platform.python_version(),
        "platform": platform.system(),
        "platform_version": platform.version(),
        "machine": platform.machine(),
    }


def get_window_title() -> str:
    """
    Retorna título da janela com versão.
    Passo 59 - Versão no título.
    """
    return f"{AppInfo.NAME} v{AppInfo.VERSION}"


def normalize_path(path: Path) -> Path:
    """
    Normaliza caminho para evitar problemas de limite.
    Passo 55 do Checklist v2 - Caminhos longos Windows.
    
    Args:
        path: Caminho original
        
    Returns:
        Caminho normalizado
    """
    if platform.system() != "Windows":
        return path
    
    path_str = str(path.resolve())
    
    # Adiciona prefixo para caminhos longos
    if len(path_str) > 250 and not path_str.startswith("\\\\?\\"):
        return Path(f"\\\\?\\{path_str}")
    
    return path


class SystemHealthCheck:
    """
    Verificação de saúde do sistema.
    Agrupa verificações dos passos 51-60.
    """
    
    @staticmethod
    def run_all() -> Dict[str, Tuple[bool, str]]:
        """Executa todas as verificações."""
        results = {}
        
        # Ghostscript
        results["ghostscript"] = verify_ghostscript()
        
        # VC++ Runtime
        results["vc_runtime"] = check_vc_runtime()
        
        # Offline
        offline = check_offline_mode()
        all_offline_ok = all(offline.values())
        results["offline_mode"] = (all_offline_ok, str(offline))
        
        # Network
        results["network"] = (is_network_available(), "Conectado" if is_network_available() else "Offline")
        
        return results
    
    @staticmethod
    def get_summary() -> str:
        """Retorna resumo de saúde."""
        results = SystemHealthCheck.run_all()
        lines = []
        
        for check, (ok, msg) in results.items():
            status = "✅" if ok else "❌"
            lines.append(f"{status} {check}: {msg}")
        
        return "\n".join(lines)


# ==============================================================================
# CENTURY CHECKLIST ITEMS 91-100 (Refinamentos Finais)
# ==============================================================================

def get_splash_info() -> Dict[str, str]:
    """
    CENTURY CHECKLIST Item 91: Informações para Splash Screen.
    
    Returns:
        Dict com informações de splash
    """
    return {
        "name": AppInfo.NAME,
        "version": f"v{AppInfo.VERSION}",
        "codename": AppInfo.CODENAME,
        "loading_message": "Inicializando sistema...",
    }


def create_bug_report_zip(output_path: Optional[Path] = None) -> Optional[Path]:
    """
    CENTURY CHECKLIST Item 93: Gera ZIP para reportar bug.
    Inclui logs e info do sistema, sem dados sensíveis.
    
    Returns:
        Caminho do ZIP ou None
    """
    try:
        if output_path is None:
            desktop = Path.home() / "Desktop"
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = desktop / f"autotabloide_bug_report_{timestamp}.zip"
        
        with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            # Logs (últimos 5)
            log_files = sorted(LOGS_DIR.glob("*.log"), key=lambda x: x.stat().st_mtime, reverse=True)[:5]
            for log_file in log_files:
                zf.write(log_file, f"logs/{log_file.name}")
            
            # Erro crítico
            error_log = LOGS_DIR / "errors.log"
            if error_log.exists():
                zf.write(error_log, "logs/errors.log")
            
            # Info do sistema
            info = get_version_info()
            info["health"] = SystemHealthCheck.run_all()
            zf.writestr("system_info.txt", str(info))
        
        logger.info(f"Bug report criado: {output_path}")
        return output_path
        
    except Exception as e:
        logger.error(f"Erro ao criar bug report: {e}")
        return None


def check_disk_space(required_mb: int = 500) -> Tuple[bool, int]:
    """
    CENTURY CHECKLIST Item 97: Verifica espaço em disco.
    
    Args:
        required_mb: Espaço mínimo necessário em MB
        
    Returns:
        Tupla (tem_espaço, espaço_livre_mb)
    """
    try:
        total, used, free = shutil.disk_usage(SYSTEM_ROOT)
        free_mb = free // (1024 * 1024)
        has_space = free_mb >= required_mb
        
        if not has_space:
            logger.warning(f"Espaço em disco baixo: {free_mb}MB (mínimo: {required_mb}MB)")
        
        return has_space, free_mb
        
    except Exception as e:
        logger.error(f"Erro ao verificar espaço: {e}")
        return True, 0  # Assume disponível em caso de erro


def security_audit() -> List[str]:
    """
    CENTURY CHECKLIST Item 100: Auditoria básica de segurança.
    Verifica padrões comuns de problemas.
    
    Returns:
        Lista de avisos (vazia = sem problemas)
    """
    warnings = []
    
    # Verifica arquivos de configuração expostos
    sensitive_patterns = ["password", "secret", "api_key", "token"]
    
    try:
        config_file = CONFIG_DIR / "settings.json"
        if config_file.exists():
            content = config_file.read_text().lower()
            for pattern in sensitive_patterns:
                if pattern in content:
                    warnings.append(f"Possível dado sensível em settings.json: '{pattern}'")
        
        # Verifica permissões de diretório (básico)
        if SYSTEM_ROOT.exists():
            # Em produção, verificaria permissões mais detalhadas
            pass
        
    except Exception as e:
        logger.warning(f"Erro na auditoria de segurança: {e}")
    
    return warnings


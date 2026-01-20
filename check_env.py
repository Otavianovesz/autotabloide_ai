"""
AutoTabloide AI - Environment Validator
========================================
FASE 1: INFRAESTRUTURA & INTEGRIDADE

Valida dependências críticas (DLLs GTK, Cairo, Visual C++ Runtime)
ANTES da inicialização do aplicativo.

Uso:
    python check_env.py
    
Ou como módulo:
    from check_env import validate_environment
    success, report = validate_environment()
"""

import sys
import os
import ctypes
import platform
from pathlib import Path
from typing import Dict, List, Tuple, Optional


# ==============================================================================
# CONSTANTES
# ==============================================================================

# DLLs críticas para renderização (CairoSVG, Pango, etc.)
CRITICAL_DLLS = {
    "cairo": [
        "cairo.dll",
        "libcairo-2.dll",
    ],
    "pango": [
        "libpango-1.0-0.dll",
        "libpangocairo-1.0-0.dll",
        "libpangoft2-1.0-0.dll",
        "libpangowin32-1.0-0.dll",
    ],
    "glib": [
        "libglib-2.0-0.dll",
        "libgobject-2.0-0.dll",
        "libgio-2.0-0.dll",
    ],
    "pixbuf": [
        "libgdk_pixbuf-2.0-0.dll",
    ],
    "freetype": [
        "libfreetype-6.dll",
        "freetype.dll",
    ],
    "msvc_runtime": [
        "msvcp140.dll",
        "vcruntime140.dll",
        "vcruntime140_1.dll",
    ],
}

# Caminhos comuns onde DLLs podem estar
DLL_SEARCH_PATHS = [
    # GTK instalado via MSYS2
    r"C:\msys64\mingw64\bin",
    # GTK instalado via pacote standalone
    r"C:\GTK\bin",
    r"C:\GTK3\bin",
    # Python site-packages (para wheels com DLLs bundled)
    os.path.join(sys.prefix, "Lib", "site-packages", "cairo"),
    os.path.join(sys.prefix, "Lib", "site-packages", "gi"),
    # PATH do sistema
] + os.environ.get("PATH", "").split(os.pathsep)


# ==============================================================================
# FUNÇÕES DE VALIDAÇÃO
# ==============================================================================

def find_dll(dll_name: str, search_paths: List[str] = None) -> Optional[str]:
    """
    Procura uma DLL em caminhos de busca.
    
    Args:
        dll_name: Nome da DLL (ex: "cairo.dll")
        search_paths: Lista de diretórios para buscar (default: DLL_SEARCH_PATHS)
        
    Returns:
        Caminho completo se encontrada, None caso contrário
    """
    if search_paths is None:
        search_paths = DLL_SEARCH_PATHS
    
    for path in search_paths:
        full_path = Path(path) / dll_name
        if full_path.exists():
            return str(full_path)
    
    return None


def can_load_dll(dll_path: str) -> Tuple[bool, Optional[str]]:
    """
    Tenta carregar uma DLL para verificar se está funcional.
    
    Args:
        dll_path: Caminho completo para a DLL
        
    Returns:
        Tuple (sucesso, mensagem_erro)
    """
    try:
        ctypes.CDLL(dll_path)
        return True, None
    except OSError as e:
        return False, str(e)
    except Exception as e:
        return False, f"Erro inesperado: {e}"


def check_dll_group(
    group_name: str, 
    dll_names: List[str]
) -> Dict:
    """
    Verifica um grupo de DLLs.
    
    Returns:
        Dict com status do grupo
    """
    result = {
        "group": group_name,
        "found": [],
        "missing": [],
        "broken": [],
        "success": False,
    }
    
    for dll_name in dll_names:
        path = find_dll(dll_name)
        
        if path is None:
            result["missing"].append(dll_name)
        else:
            can_load, error = can_load_dll(path)
            if can_load:
                result["found"].append({"name": dll_name, "path": path})
            else:
                result["broken"].append({
                    "name": dll_name, 
                    "path": path, 
                    "error": error
                })
    
    # Sucesso se pelo menos uma DLL do grupo foi encontrada e carregada
    result["success"] = len(result["found"]) > 0
    
    return result


def check_python_packages() -> Dict:
    """
    Verifica pacotes Python críticos.
    """
    packages = {
        "pyside6": {"required": True, "version": None, "ok": False},
        "sqlalchemy": {"required": True, "version": None, "ok": False},
        "cairosvg": {"required": True, "version": None, "ok": False},
        "lxml": {"required": True, "version": None, "ok": False},
        "pillow": {"required": True, "version": None, "ok": False},
        "loguru": {"required": False, "version": None, "ok": False},
    }
    
    for pkg_name, info in packages.items():
        try:
            if pkg_name == "pyside6":
                from PySide6 import __version__
                info["version"] = __version__
                info["ok"] = True
            elif pkg_name == "sqlalchemy":
                import sqlalchemy
                info["version"] = sqlalchemy.__version__
                info["ok"] = True
            elif pkg_name == "cairosvg":
                import cairosvg
                info["version"] = cairosvg.__version__
                info["ok"] = True
            elif pkg_name == "lxml":
                import lxml
                info["version"] = lxml.__version__
                info["ok"] = True
            elif pkg_name == "pillow":
                from PIL import Image
                import PIL
                info["version"] = PIL.__version__
                info["ok"] = True
            elif pkg_name == "loguru":
                import loguru
                info["version"] = loguru.__version__
                info["ok"] = True
        except ImportError:
            pass
        except AttributeError:
            # Alguns pacotes não têm __version__
            info["ok"] = True
            info["version"] = "installed"
    
    return packages


def check_system_requirements() -> Dict:
    """
    Verifica requisitos do sistema.
    """
    result = {
        "os": platform.system(),
        "os_version": platform.version(),
        "python_version": sys.version,
        "python_bits": "64-bit" if sys.maxsize > 2**32 else "32-bit",
        "issues": [],
    }
    
    # Python 64-bit é necessário para algumas DLLs
    if sys.maxsize <= 2**32:
        result["issues"].append("Python 32-bit detectado. Algumas DLLs podem não carregar.")
    
    # Python 3.10+ necessário para algumas features
    if sys.version_info < (3, 10):
        result["issues"].append(f"Python {sys.version_info.major}.{sys.version_info.minor} detectado. Recomendado 3.10+")
    
    return result


# ==============================================================================
# FUNÇÃO PRINCIPAL
# ==============================================================================

def validate_environment(verbose: bool = True) -> Tuple[bool, Dict]:
    """
    Executa validação completa do ambiente.
    
    Args:
        verbose: Se deve imprimir resultados no console
        
    Returns:
        Tuple (sucesso_geral, relatório_detalhado)
    """
    report = {
        "system": None,
        "dlls": {},
        "packages": None,
        "overall_success": True,
        "critical_issues": [],
    }
    
    # 1. Sistema
    if verbose:
        print("=" * 60)
        print("AUTOTABLOIDE AI - ENVIRONMENT VALIDATOR")
        print("=" * 60)
        print()
    
    report["system"] = check_system_requirements()
    
    if verbose:
        print(f"[SISTEMA]")
        print(f"  OS: {report['system']['os']} {report['system']['os_version']}")
        print(f"  Python: {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro} ({report['system']['python_bits']})")
        for issue in report["system"]["issues"]:
            print(f"  [!] {issue}")
        print()
    
    # 2. DLLs (apenas Windows)
    if platform.system() == "Windows":
        if verbose:
            print("[DLLs]")
        
        for group_name, dll_names in CRITICAL_DLLS.items():
            result = check_dll_group(group_name, dll_names)
            report["dlls"][group_name] = result
            
            if verbose:
                status = "[OK]" if result["success"] else "[FAIL]"
                print(f"  {status} {group_name.upper()}")
                
                for found in result["found"]:
                    print(f"      + {found['name']}")
                
                for missing in result["missing"]:
                    print(f"      - {missing} (nao encontrado)")
                
                for broken in result["broken"]:
                    print(f"      ! {broken['name']} (corrompido: {broken['error'][:50]})")
            
            # Cairo é crítico
            if group_name == "cairo" and not result["success"]:
                report["overall_success"] = False
                report["critical_issues"].append(
                    "Cairo DLL nao encontrada. CairoSVG nao funcionara."
                )
        
        if verbose:
            print()
    
    # 3. Pacotes Python
    report["packages"] = check_python_packages()
    
    if verbose:
        print("[PACOTES PYTHON]")
        
        for pkg_name, info in report["packages"].items():
            status = "[OK]" if info["ok"] else "[FAIL]"
            version = info["version"] or "nao instalado"
            req = "(obrigatorio)" if info["required"] else "(opcional)"
            print(f"  {status} {pkg_name}: {version} {req}")
            
            if info["required"] and not info["ok"]:
                report["overall_success"] = False
                report["critical_issues"].append(f"Pacote {pkg_name} nao instalado.")
        
        print()
    
    # 4. Resumo
    if verbose:
        print("=" * 60)
        if report["overall_success"]:
            print("[OK] AMBIENTE OK - Pronto para iniciar AutoTabloide AI")
        else:
            print("[FAIL] PROBLEMAS DETECTADOS:")
            for issue in report["critical_issues"]:
                print(f"   * {issue}")
        print("=" * 60)
    
    return report["overall_success"], report


def get_cairo_installation_instructions() -> str:
    """
    Retorna instruções para instalar Cairo no Windows.
    """
    return """
INSTALAÇÃO DO CAIRO (WINDOWS)
=============================

Opção 1: Via pip (recomendado)
------------------------------
pip install pycairo

Opção 2: MSYS2
--------------
1. Instale MSYS2: https://www.msys2.org/
2. Execute no terminal MSYS2:
   pacman -S mingw-w64-x86_64-gtk3 mingw-w64-x86_64-cairo
3. Adicione C:\\msys64\\mingw64\\bin ao PATH

Opção 3: GTK for Windows
------------------------
1. Baixe: https://github.com/nicm/gtk3-win32
2. Extraia para C:\\GTK
3. Adicione C:\\GTK\\bin ao PATH

Após instalação, execute novamente:
python check_env.py
"""


# ==============================================================================
# ENTRY POINT
# ==============================================================================

if __name__ == "__main__":
    success, report = validate_environment(verbose=True)
    
    if not success:
        print()
        print(get_cairo_installation_instructions())
    
    sys.exit(0 if success else 1)

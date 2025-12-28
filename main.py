"""
AutoTabloide AI - Unified Launcher
==================================
PROTOCOLO DE RETIFICAÇÃO NÍVEL 0 - Passo 3
Bootloader unificado que delega para main_qt.py.
"""

import sys
from pathlib import Path

# Adiciona src ao path
ROOT = Path(__file__).parent.resolve()
sys.path.insert(0, str(ROOT))


def main():
    """Entry point único - delega para Qt."""
    try:
        from main_qt import main as qt_main
        return qt_main()
    except ImportError as e:
        # Fallback: mostra erro amigável
        error_msg = f"Falha ao iniciar: {e}\n\nVerifique se as dependências estão instaladas:\n  poetry install"
        
        if sys.platform == "win32":
            try:
                import ctypes
                ctypes.windll.user32.MessageBoxW(0, error_msg, "AutoTabloide AI - Erro", 0x10)
            except:
                print(error_msg)
        else:
            print(error_msg)
        
        return 1


if __name__ == "__main__":
    sys.exit(main() or 0)

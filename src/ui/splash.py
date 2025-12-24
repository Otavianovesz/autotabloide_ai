"""
AutoTabloide AI - Splash Screen & Dependency Checker
======================================================
Tela de splash e verificação de dependências.
Passos 76, 77 do Checklist 100.

Funcionalidades:
- Splash screen com logo e progresso
- Verificação de dependências externas (Ghostscript, VCRedist)
- Mensagens de erro amigáveis
"""

import sys
import subprocess
from pathlib import Path
from typing import Optional, Tuple, List
import flet as ft

from src.core.logging_config import get_logger
from src.core.constants import SYSTEM_ROOT
from src.ui.design_system import DesignTokens

logger = get_logger("Startup")


# ==============================================================================
# VERIFICADOR DE DEPENDÊNCIAS (Passo 77)
# ==============================================================================

class DependencyChecker:
    """
    Verifica dependências externas do sistema.
    """
    
    @staticmethod
    def check_ghostscript() -> Tuple[bool, str]:
        """
        Verifica se Ghostscript está instalado.
        
        Returns:
            Tupla (encontrado, caminho ou mensagem de erro)
        """
        # Caminhos comuns
        gs_paths = [
            SYSTEM_ROOT / "bin" / "gs" / "gswin64c.exe",  # Bundled
            Path("C:/Program Files/gs/gs10.02.1/bin/gswin64c.exe"),
            Path("C:/Program Files/gs/gs10.00.0/bin/gswin64c.exe"),
            Path("C:/Program Files/gs/gs9.56.1/bin/gswin64c.exe"),
        ]
        
        for gs_path in gs_paths:
            if gs_path.exists():
                return True, str(gs_path)
        
        # Tenta via PATH
        try:
            result = subprocess.run(
                ["gswin64c", "-v"],
                capture_output=True,
                timeout=5
            )
            if result.returncode == 0:
                return True, "gswin64c (PATH)"
        except Exception:
            pass
        
        return False, "Ghostscript não encontrado. Instale de: https://ghostscript.com/"
    
    @staticmethod
    def check_vcredist() -> Tuple[bool, str]:
        """
        Verifica se VCRedist 2019+ está instalado.
        """
        import winreg
        
        try:
            key_paths = [
                r"SOFTWARE\Microsoft\VisualStudio\14.0\VC\Runtimes\x64",
                r"SOFTWARE\WOW6432Node\Microsoft\VisualStudio\14.0\VC\Runtimes\x64"
            ]
            
            for key_path in key_paths:
                try:
                    with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path) as key:
                        version, _ = winreg.QueryValueEx(key, "Version")
                        return True, version
                except FileNotFoundError:
                    continue
            
            return False, "VCRedist 2019+ não encontrado"
            
        except Exception as e:
            return True, f"Não foi possível verificar ({e})"
    
    @staticmethod
    def check_fonts() -> Tuple[bool, List[str]]:
        """
        Verifica se fontes obrigatórias estão presentes.
        """
        fonts_dir = SYSTEM_ROOT / "assets" / "fonts"
        required_fonts = [
            "Roboto-Regular.ttf",
            "Roboto-Bold.ttf",
        ]
        
        missing = []
        for font in required_fonts:
            if not (fonts_dir / font).exists():
                missing.append(font)
        
        if missing:
            return False, missing
        return True, []
    
    @staticmethod
    def run_all_checks() -> List[dict]:
        """
        Executa todas as verificações.
        
        Returns:
            Lista de resultados [{name, ok, message}]
        """
        results = []
        
        # Ghostscript
        ok, msg = DependencyChecker.check_ghostscript()
        results.append({"name": "Ghostscript", "ok": ok, "message": msg})
        
        # VCRedist (apenas Windows)
        if sys.platform == "win32":
            ok, msg = DependencyChecker.check_vcredist()
            results.append({"name": "Visual C++ Runtime", "ok": ok, "message": msg})
        
        # Fontes
        ok, missing = DependencyChecker.check_fonts()
        msg = f"Fontes OK" if ok else f"Faltando: {', '.join(missing)}"
        results.append({"name": "Fontes", "ok": ok, "message": msg})
        
        return results


# ==============================================================================
# SPLASH SCREEN (Passo 76)
# ==============================================================================

class SplashScreen:
    """
    Tela de splash com logo e progresso de inicialização.
    """
    
    def __init__(self, page: ft.Page):
        self.page = page
        self._status_text: Optional[ft.Text] = None
        self._progress_bar: Optional[ft.ProgressBar] = None
        self._checks_column: Optional[ft.Column] = None
    
    def show(self) -> None:
        """Exibe splash screen."""
        self._status_text = ft.Text(
            "Inicializando sistema...",
            size=14,
            color=DesignTokens.TEXT_SECONDARY
        )
        
        self._progress_bar = ft.ProgressBar(
            width=300,
            color=DesignTokens.PRIMARY,
            bgcolor=DesignTokens.SURFACE_LIGHT,
            value=None  # Indeterminate
        )
        
        self._checks_column = ft.Column(
            spacing=4,
            horizontal_alignment=ft.CrossAxisAlignment.START
        )
        
        splash = ft.Container(
            content=ft.Column([
                # Logo
                ft.Container(
                    content=ft.Icon(
                        ft.icons.NEWSPAPER,
                        size=80,
                        color=DesignTokens.PRIMARY
                    ),
                    margin=ft.margin.only(bottom=20)
                ),
                
                # Título
                ft.Text(
                    "AutoTabloide AI",
                    size=32,
                    weight=ft.FontWeight.BOLD,
                    color=DesignTokens.TEXT_PRIMARY
                ),
                
                # Versão
                ft.Text(
                    "v1.0.0 Industrial",
                    size=14,
                    color=DesignTokens.TEXT_SECONDARY
                ),
                
                ft.Container(height=30),
                
                # Progress
                self._progress_bar,
                ft.Container(height=10),
                self._status_text,
                
                ft.Container(height=20),
                
                # Checks
                self._checks_column
            ],
                spacing=4,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER
            ),
            bgcolor=DesignTokens.SURFACE,
            padding=50,
            border_radius=16,
            shadow=ft.BoxShadow(
                spread_radius=2,
                blur_radius=30,
                color=ft.colors.with_opacity(0.3, ft.colors.BLACK)
            )
        )
        
        self.page.add(
            ft.Container(
                content=splash,
                alignment=ft.alignment.center,
                expand=True,
                bgcolor=DesignTokens.BACKGROUND
            )
        )
        self.page.update()
    
    def update_status(self, message: str, progress: Optional[float] = None) -> None:
        """Atualiza mensagem de status."""
        if self._status_text:
            self._status_text.value = message
        
        if self._progress_bar and progress is not None:
            self._progress_bar.value = progress
        
        try:
            self.page.update()
        except Exception:
            pass
    
    def add_check_result(self, name: str, ok: bool, message: str) -> None:
        """Adiciona resultado de verificação."""
        if not self._checks_column:
            return
        
        icon = ft.icons.CHECK_CIRCLE if ok else ft.icons.ERROR
        color = DesignTokens.SUCCESS if ok else DesignTokens.ERROR
        
        self._checks_column.controls.append(
            ft.Row([
                ft.Icon(icon, size=16, color=color),
                ft.Text(f"{name}: ", size=12, weight=ft.FontWeight.BOLD),
                ft.Text(message[:50], size=12, color=DesignTokens.TEXT_SECONDARY)
            ], spacing=4)
        )
        
        try:
            self.page.update()
        except Exception:
            pass
    
    def hide(self) -> None:
        """Remove splash screen."""
        self.page.clean()
        self.page.update()


def run_startup_sequence(page: ft.Page) -> bool:
    """
    Executa sequência completa de startup com splash.
    
    Args:
        page: Página Flet
        
    Returns:
        True se todas as verificações passaram
    """
    import asyncio
    import time
    
    splash = SplashScreen(page)
    splash.show()
    
    all_ok = True
    
    # Verificações de dependência
    splash.update_status("Verificando dependências...", 0.0)
    time.sleep(0.5)
    
    checks = DependencyChecker.run_all_checks()
    for i, check in enumerate(checks):
        splash.add_check_result(check["name"], check["ok"], check["message"])
        if not check["ok"]:
            all_ok = False
        time.sleep(0.3)
        splash.update_status(f"Verificando... ({i+1}/{len(checks)})", (i+1)/len(checks) * 0.5)
    
    # Inicialização do banco
    splash.update_status("Inicializando banco de dados...", 0.6)
    time.sleep(0.5)
    
    # Carregando serviços
    splash.update_status("Carregando serviços...", 0.8)
    time.sleep(0.5)
    
    # Finalizado
    splash.update_status("Pronto!", 1.0)
    time.sleep(0.5)
    
    splash.hide()
    
    return all_ok

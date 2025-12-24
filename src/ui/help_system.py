"""
AutoTabloide AI - Help System
================================
Sistema de ajuda da aplicação.
Passo 78 do Checklist 100.

Funcionalidades:
- Botão ajuda -> PDF
- Geração de PDF de ajuda
- Atalhos de teclado
"""

import subprocess
import webbrowser
from pathlib import Path
from typing import Optional
import flet as ft

from src.core.logging_config import get_logger
from src.core.constants import SYSTEM_ROOT
from src.ui.design_system import DesignTokens

logger = get_logger("Help")

# Diretório de documentação
DOCS_DIR = SYSTEM_ROOT / "docs"
HELP_PDF = DOCS_DIR / "manual_usuario.pdf"


class HelpSystem:
    """
    Sistema de ajuda da aplicação.
    Passo 78 do Checklist - Botão ajuda -> PDF.
    """
    
    @staticmethod
    def open_manual() -> bool:
        """
        Abre manual do usuário em PDF.
        
        Returns:
            True se conseguiu abrir
        """
        if HELP_PDF.exists():
            try:
                # Abre com aplicação padrão
                if subprocess.os.name == 'nt':  # Windows
                    subprocess.Popen(['start', '', str(HELP_PDF)], shell=True)
                else:
                    subprocess.Popen(['xdg-open', str(HELP_PDF)])
                
                logger.info("Manual aberto com sucesso")
                return True
                
            except Exception as e:
                logger.error(f"Erro ao abrir manual: {e}")
                return False
        else:
            logger.warning(f"Manual não encontrado: {HELP_PDF}")
            return False
    
    @staticmethod
    def open_online_help(url: str = "https://github.com/Otavianovesz/autotabloide_ai") -> None:
        """Abre ajuda online no navegador."""
        webbrowser.open(url)
    
    @staticmethod
    def get_keyboard_shortcuts() -> dict:
        """
        Retorna lista de atalhos de teclado.
        
        Returns:
            Dict com categorias e atalhos
        """
        return {
            "Arquivo": {
                "Ctrl+N": "Novo Projeto",
                "Ctrl+O": "Abrir Projeto",
                "Ctrl+S": "Salvar Projeto",
                "Ctrl+Shift+S": "Salvar Como",
                "Ctrl+E": "Exportar PDF",
            },
            "Edição": {
                "Ctrl+Z": "Desfazer",
                "Ctrl+Y": "Refazer",
                "Delete": "Limpar Slot",
                "Ctrl+A": "Selecionar Todos",
            },
            "Navegação": {
                "↑ ↓ ← →": "Navegar entre Slots",
                "Tab": "Próximo Slot",
                "Shift+Tab": "Slot Anterior",
                "F1": "Ajuda",
            },
            "Visualização": {
                "Ctrl+0": "Zoom 100%",
                "Ctrl++": "Aumentar Zoom",
                "Ctrl+-": "Diminuir Zoom",
                "F11": "Tela Cheia",
            }
        }


class HelpButton(ft.IconButton):
    """
    Botão de ajuda para incluir na UI.
    """
    
    def __init__(self, page: ft.Page):
        self.page = page
        super().__init__(
            icon=ft.icons.HELP_OUTLINE,
            tooltip="Ajuda (F1)",
            on_click=self._show_help_menu
        )
    
    def _show_help_menu(self, e) -> None:
        """Mostra menu de ajuda."""
        menu = ft.PopupMenuButton(
            items=[
                ft.PopupMenuItem(
                    text="📖 Manual do Usuário",
                    on_click=lambda _: HelpSystem.open_manual()
                ),
                ft.PopupMenuItem(
                    text="⌨️ Atalhos de Teclado",
                    on_click=lambda _: self._show_shortcuts_dialog()
                ),
                ft.Divider(),
                ft.PopupMenuItem(
                    text="🌐 Ajuda Online",
                    on_click=lambda _: HelpSystem.open_online_help()
                ),
                ft.PopupMenuItem(
                    text="ℹ️ Sobre",
                    on_click=lambda _: self._show_about_dialog()
                ),
            ]
        )
        
        # Mostra menu
        self.page.dialog = ft.AlertDialog(
            title=ft.Text("Ajuda"),
            content=ft.Column([
                ft.ListTile(
                    leading=ft.Icon(ft.icons.BOOK),
                    title=ft.Text("Manual do Usuário"),
                    on_click=lambda _: HelpSystem.open_manual()
                ),
                ft.ListTile(
                    leading=ft.Icon(ft.icons.KEYBOARD),
                    title=ft.Text("Atalhos de Teclado"),
                    on_click=lambda _: self._show_shortcuts_dialog()
                ),
                ft.ListTile(
                    leading=ft.Icon(ft.icons.LANGUAGE),
                    title=ft.Text("Ajuda Online"),
                    on_click=lambda _: HelpSystem.open_online_help()
                ),
            ], spacing=0),
            actions=[ft.TextButton("Fechar", on_click=lambda _: self._close_dialog())],
        )
        self.page.dialog.open = True
        self.page.update()
    
    def _show_shortcuts_dialog(self) -> None:
        """Mostra dialog de atalhos."""
        shortcuts = HelpSystem.get_keyboard_shortcuts()
        
        content = ft.Column([], spacing=10, scroll=ft.ScrollMode.AUTO)
        
        for category, items in shortcuts.items():
            content.controls.append(
                ft.Text(category, weight=ft.FontWeight.BOLD, size=14)
            )
            for key, action in items.items():
                content.controls.append(
                    ft.Row([
                        ft.Container(
                            content=ft.Text(key, weight=ft.FontWeight.W_500),
                            bgcolor=DesignTokens.SURFACE_LIGHT,
                            padding=5,
                            border_radius=4,
                            width=120
                        ),
                        ft.Text(action),
                    ], spacing=10)
                )
            content.controls.append(ft.Container(height=10))
        
        self.page.dialog = ft.AlertDialog(
            title=ft.Text("⌨️ Atalhos de Teclado"),
            content=ft.Container(content=content, width=400, height=400),
            actions=[ft.TextButton("Fechar", on_click=lambda _: self._close_dialog())],
        )
        self.page.dialog.open = True
        self.page.update()
    
    def _show_about_dialog(self) -> None:
        """Mostra dialog Sobre."""
        from src.core.constants import AppInfo
        
        self.page.dialog = ft.AlertDialog(
            title=ft.Text(f"ℹ️ Sobre {AppInfo.NAME}"),
            content=ft.Column([
                ft.Text(f"Versão: {AppInfo.VERSION}", size=14),
                ft.Text(f"Codename: {AppInfo.CODENAME}", size=12),
                ft.Text(f"Autor: {AppInfo.AUTHOR}", size=12),
                ft.Container(height=10),
                ft.Text(
                    "Sistema offline de geração de tabloides com IA.",
                    color=DesignTokens.TEXT_SECONDARY
                ),
            ], spacing=5),
            actions=[ft.TextButton("Fechar", on_click=lambda _: self._close_dialog())],
        )
        self.page.dialog.open = True
        self.page.update()
    
    def _close_dialog(self) -> None:
        """Fecha dialog atual."""
        if self.page.dialog:
            self.page.dialog.open = False
            self.page.update()

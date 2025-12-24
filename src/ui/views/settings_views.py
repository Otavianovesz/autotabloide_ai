"""
AutoTabloide AI - Settings Views
==================================
Telas de configuração para o sistema.
Passos 52-54 do Checklist 100.

Telas:
- Palavras Proibidas (+18) CRUD (53)
- Configuração Ghostscript (54)
"""

import asyncio
import flet as ft
from typing import List, Optional

from src.core.logging_config import get_logger
from src.core.settings_service import SettingsService, get_settings
from src.ui.design_system import DesignTokens

logger = get_logger("SettingsViews")


# ==============================================================================
# PALAVRAS PROIBIDAS CRUD (Passo 53)
# ==============================================================================

class RestrictedWordsView(ft.Column):
    """
    Tela CRUD para gerenciar palavras +18 e whitelist.
    Passo 53 do Checklist.
    """
    
    def __init__(self, page: ft.Page):
        super().__init__()
        self.page = page
        self.settings = get_settings()
        
        # Campos
        self._alcohol_field: Optional[ft.TextField] = None
        self._tobacco_field: Optional[ft.TextField] = None
        self._whitelist_field: Optional[ft.TextField] = None
        
        self._build_ui()
    
    def _build_ui(self) -> None:
        """Constrói interface."""
        # Cabeçalho
        header = ft.Container(
            content=ft.Text(
                "🔞 Palavras Restritivas",
                size=24,
                weight=ft.FontWeight.BOLD
            ),
            margin=ft.margin.only(bottom=20)
        )
        
        # Campo álcool
        self._alcohol_field = ft.TextField(
            label="Palavras de Álcool (separadas por vírgula)",
            value=", ".join(self.settings._cache.get("restricted.alcohol_keywords", [])),
            multiline=True,
            min_lines=3,
            max_lines=5,
            hint_text="cerveja, vodka, whisky, cachaça..."
        )
        
        # Campo tabaco
        self._tobacco_field = ft.TextField(
            label="Palavras de Tabaco (separadas por vírgula)",
            value=", ".join(self.settings._cache.get("restricted.tobacco_keywords", [])),
            multiline=True,
            min_lines=3,
            max_lines=5,
            hint_text="cigarro, tabaco, fumo..."
        )
        
        # Campo whitelist
        self._whitelist_field = ft.TextField(
            label="Whitelist (exceções que contêm palavras acima mas são permitidas)",
            value=", ".join(self.settings._cache.get("restricted.whitelist", [])),
            multiline=True,
            min_lines=3,
            max_lines=5,
            hint_text="vinagre de vinho, vinho tinto..."
        )
        
        # Botões
        save_btn = ft.ElevatedButton(
            "Salvar Configurações",
            icon=ft.icons.SAVE,
            on_click=self._handle_save
        )
        
        reset_btn = ft.OutlinedButton(
            "Restaurar Padrões",
            icon=ft.icons.RESTORE,
            on_click=self._handle_reset
        )
        
        self.controls = [
            header,
            self._alcohol_field,
            ft.Container(height=10),
            self._tobacco_field,
            ft.Container(height=10),
            self._whitelist_field,
            ft.Container(height=20),
            ft.Row([save_btn, reset_btn], spacing=10)
        ]
        self.spacing = 5
        self.scroll = ft.ScrollMode.AUTO
    
    async def _handle_save(self, e) -> None:
        """Salva configurações."""
        try:
            # Parse listas
            alcohol = [w.strip() for w in self._alcohol_field.value.split(",") if w.strip()]
            tobacco = [w.strip() for w in self._tobacco_field.value.split(",") if w.strip()]
            whitelist = [w.strip() for w in self._whitelist_field.value.split(",") if w.strip()]
            
            # Salva
            await self.settings.set("restricted.alcohol_keywords", alcohol, "restricted")
            await self.settings.set("restricted.tobacco_keywords", tobacco, "restricted")
            await self.settings.set("restricted.whitelist", whitelist, "restricted")
            
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text("Configurações salvas!"),
                bgcolor=DesignTokens.SUCCESS
            )
            self.page.snack_bar.open = True
            self.page.update()
            
        except Exception as ex:
            logger.error(f"Erro ao salvar: {ex}")
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text(f"Erro: {ex}"),
                bgcolor=DesignTokens.ERROR
            )
            self.page.snack_bar.open = True
            self.page.update()
    
    async def _handle_reset(self, e) -> None:
        """Restaura padrões."""
        from src.core.settings_service import DEFAULT_SETTINGS
        
        self._alcohol_field.value = ", ".join(
            DEFAULT_SETTINGS["restricted.alcohol_keywords"]["value"]
        )
        self._tobacco_field.value = ", ".join(
            DEFAULT_SETTINGS["restricted.tobacco_keywords"]["value"]
        )
        self._whitelist_field.value = ", ".join(
            DEFAULT_SETTINGS["restricted.whitelist"]["value"]
        )
        self.page.update()


# ==============================================================================
# CONFIGURAÇÃO GHOSTSCRIPT (Passo 54)
# ==============================================================================

class GhostscriptConfigView(ft.Column):
    """
    Tela para configurar caminho do Ghostscript.
    Passo 54 do Checklist.
    """
    
    def __init__(self, page: ft.Page):
        super().__init__()
        self.page = page
        self.settings = get_settings()
        
        self._gs_path_field: Optional[ft.TextField] = None
        self._status_icon: Optional[ft.Icon] = None
        
        self._build_ui()
    
    def _build_ui(self) -> None:
        """Constrói interface."""
        header = ft.Container(
            content=ft.Text(
                "⚙️ Configuração Ghostscript",
                size=24,
                weight=ft.FontWeight.BOLD
            ),
            margin=ft.margin.only(bottom=20)
        )
        
        # Info
        info = ft.Container(
            content=ft.Text(
                "O Ghostscript é necessário para conversão CMYK e geração de PDF/X.",
                size=14,
                color=DesignTokens.TEXT_SECONDARY
            ),
            margin=ft.margin.only(bottom=15)
        )
        
        # Campo de caminho
        self._status_icon = ft.Icon(
            ft.icons.HELP_OUTLINE,
            color=DesignTokens.TEXT_SECONDARY
        )
        
        self._gs_path_field = ft.TextField(
            label="Caminho do Ghostscript (gswin64c.exe)",
            value=self.settings._cache.get("paths.ghostscript", ""),
            hint_text="C:\\Program Files\\gs\\gs10.00.0\\bin\\gswin64c.exe",
            suffix=self._status_icon,
            expand=True
        )
        
        browse_btn = ft.IconButton(
            icon=ft.icons.FOLDER_OPEN,
            tooltip="Procurar",
            on_click=self._handle_browse
        )
        
        detect_btn = ft.ElevatedButton(
            "Auto-Detectar",
            icon=ft.icons.SEARCH,
            on_click=self._handle_detect
        )
        
        test_btn = ft.ElevatedButton(
            "Testar Conexão",
            icon=ft.icons.CHECK,
            on_click=self._handle_test
        )
        
        save_btn = ft.ElevatedButton(
            "Salvar",
            icon=ft.icons.SAVE,
            on_click=self._handle_save
        )
        
        self.controls = [
            header,
            info,
            ft.Row([self._gs_path_field, browse_btn], spacing=5),
            ft.Container(height=15),
            ft.Row([detect_btn, test_btn, save_btn], spacing=10)
        ]
        self.spacing = 5
    
    async def _handle_browse(self, e) -> None:
        """Abre seletor de arquivo."""
        picker = ft.FilePicker(
            on_result=self._on_file_picked
        )
        self.page.overlay.append(picker)
        self.page.update()
        await picker.pick_files_async(
            dialog_title="Selecionar Ghostscript",
            allowed_extensions=["exe"],
            file_type=ft.FilePickerFileType.CUSTOM
        )
    
    def _on_file_picked(self, e: ft.FilePickerResultEvent) -> None:
        """Callback do file picker."""
        if e.files and len(e.files) > 0:
            self._gs_path_field.value = e.files[0].path
            self.page.update()
    
    async def _handle_detect(self, e) -> None:
        """Tenta auto-detectar Ghostscript."""
        from pathlib import Path
        
        possible_paths = [
            Path("C:/Program Files/gs/gs10.02.1/bin/gswin64c.exe"),
            Path("C:/Program Files/gs/gs10.00.0/bin/gswin64c.exe"),
            Path("C:/Program Files/gs/gs9.56.1/bin/gswin64c.exe"),
        ]
        
        for p in possible_paths:
            if p.exists():
                self._gs_path_field.value = str(p)
                self._status_icon.name = ft.icons.CHECK_CIRCLE
                self._status_icon.color = DesignTokens.SUCCESS
                self.page.update()
                return
        
        self._status_icon.name = ft.icons.ERROR
        self._status_icon.color = DesignTokens.ERROR
        self.page.snack_bar = ft.SnackBar(
            content=ft.Text("Ghostscript não encontrado automaticamente"),
            bgcolor=DesignTokens.WARNING
        )
        self.page.snack_bar.open = True
        self.page.update()
    
    async def _handle_test(self, e) -> None:
        """Testa se o Ghostscript funciona."""
        import subprocess
        from pathlib import Path
        
        gs_path = self._gs_path_field.value
        if not gs_path or not Path(gs_path).exists():
            self._status_icon.name = ft.icons.ERROR
            self._status_icon.color = DesignTokens.ERROR
            self.page.update()
            return
        
        try:
            result = subprocess.run(
                [gs_path, "-v"],
                capture_output=True,
                timeout=5
            )
            
            if result.returncode == 0:
                self._status_icon.name = ft.icons.CHECK_CIRCLE
                self._status_icon.color = DesignTokens.SUCCESS
                self.page.snack_bar = ft.SnackBar(
                    content=ft.Text("Ghostscript funcionando!"),
                    bgcolor=DesignTokens.SUCCESS
                )
            else:
                self._status_icon.name = ft.icons.ERROR
                self._status_icon.color = DesignTokens.ERROR
                self.page.snack_bar = ft.SnackBar(
                    content=ft.Text("Ghostscript não respondeu corretamente"),
                    bgcolor=DesignTokens.ERROR
                )
            
            self.page.snack_bar.open = True
            self.page.update()
            
        except Exception as ex:
            logger.error(f"Erro ao testar GS: {ex}")
            self._status_icon.name = ft.icons.ERROR
            self._status_icon.color = DesignTokens.ERROR
            self.page.update()
    
    async def _handle_save(self, e) -> None:
        """Salva caminho."""
        try:
            await self.settings.set("paths.ghostscript", self._gs_path_field.value, "paths")
            
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text("Caminho salvo!"),
                bgcolor=DesignTokens.SUCCESS
            )
            self.page.snack_bar.open = True
            self.page.update()
            
        except Exception as ex:
            logger.error(f"Erro ao salvar: {ex}")

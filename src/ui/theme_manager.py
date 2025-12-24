"""
AutoTabloide AI - Theme Manager
=================================
Gerenciador de temas claro/escuro.
Passo 89 do Checklist 100.

Funcionalidades:
- Tema claro e escuro
- Persistência de preferência
- Cores customizáveis
"""

from enum import Enum
from typing import Dict, Optional
from dataclasses import dataclass

from src.core.logging_config import get_logger
from src.core.settings_service import get_settings

logger = get_logger("ThemeManager")


class ThemeMode(Enum):
    """Modos de tema disponíveis."""
    LIGHT = "light"
    DARK = "dark"
    SYSTEM = "system"


@dataclass
class ThemeColors:
    """Cores de um tema."""
    # Cores primárias
    primary: str
    on_primary: str
    primary_container: str
    
    # Superfícies
    background: str
    surface: str
    surface_variant: str
    
    # Texto
    on_background: str
    on_surface: str
    on_surface_variant: str
    
    # Semânticas
    error: str
    success: str
    warning: str
    
    # Bordas
    outline: str
    outline_variant: str


# Tema Escuro (padrão atual)
DARK_THEME = ThemeColors(
    # Cores primárias
    primary="#6366F1",
    on_primary="#FFFFFF",
    primary_container="#4F46E5",
    
    # Superfícies
    background="#0F0F23",
    surface="#1A1A2E",
    surface_variant="#252538",
    
    # Texto
    on_background="#E8E8F0",
    on_surface="#FFFFFF",
    on_surface_variant="#A0A0B0",
    
    # Semânticas
    error="#EF4444",
    success="#10B981",
    warning="#F59E0B",
    
    # Bordas
    outline="#3D3D5C",
    outline_variant="#2A2A40"
)


# Tema Claro
LIGHT_THEME = ThemeColors(
    # Cores primárias
    primary="#4F46E5",
    on_primary="#FFFFFF",
    primary_container="#E0E7FF",
    
    # Superfícies
    background="#FAFAFA",
    surface="#FFFFFF",
    surface_variant="#F3F4F6",
    
    # Texto
    on_background="#1F2937",
    on_surface="#111827",
    on_surface_variant="#6B7280",
    
    # Semânticas
    error="#DC2626",
    success="#059669",
    warning="#D97706",
    
    # Bordas
    outline="#D1D5DB",
    outline_variant="#E5E7EB"
)


class ThemeManager:
    """
    Gerenciador de temas.
    Passo 89 do Checklist - Tema claro/escuro.
    """
    
    def __init__(self):
        self._current_mode: ThemeMode = ThemeMode.DARK
        self._load_preference()
    
    def _load_preference(self) -> None:
        """Carrega preferência de tema salva."""
        try:
            settings = get_settings()
            saved_mode = settings.get("ui.theme_mode", "dark")
            
            if saved_mode == "light":
                self._current_mode = ThemeMode.LIGHT
            elif saved_mode == "system":
                self._current_mode = ThemeMode.SYSTEM
            else:
                self._current_mode = ThemeMode.DARK
                
        except Exception:
            self._current_mode = ThemeMode.DARK
    
    async def save_preference(self) -> None:
        """Salva preferência de tema."""
        try:
            settings = get_settings()
            await settings.set("ui.theme_mode", self._current_mode.value, "ui")
        except Exception as e:
            logger.error(f"Erro ao salvar preferência de tema: {e}")
    
    @property
    def current_mode(self) -> ThemeMode:
        """Retorna modo atual."""
        return self._current_mode
    
    @property
    def current_theme(self) -> ThemeColors:
        """Retorna tema atual baseado no modo."""
        if self._current_mode == ThemeMode.LIGHT:
            return LIGHT_THEME
        elif self._current_mode == ThemeMode.SYSTEM:
            # Poderia detectar tema do sistema
            # Por ora, retorna escuro
            return DARK_THEME
        else:
            return DARK_THEME
    
    def set_mode(self, mode: ThemeMode) -> None:
        """
        Define modo de tema.
        
        Args:
            mode: Novo modo
        """
        self._current_mode = mode
        logger.info(f"Tema alterado para: {mode.value}")
    
    def toggle(self) -> ThemeMode:
        """
        Alterna entre claro e escuro.
        
        Returns:
            Novo modo
        """
        if self._current_mode == ThemeMode.DARK:
            self._current_mode = ThemeMode.LIGHT
        else:
            self._current_mode = ThemeMode.DARK
        
        return self._current_mode
    
    def get_colors_dict(self) -> Dict[str, str]:
        """
        Retorna cores do tema atual como dict.
        
        Returns:
            Dict com todas as cores
        """
        theme = self.current_theme
        return {
            "primary": theme.primary,
            "on_primary": theme.on_primary,
            "primary_container": theme.primary_container,
            "background": theme.background,
            "surface": theme.surface,
            "surface_variant": theme.surface_variant,
            "on_background": theme.on_background,
            "on_surface": theme.on_surface,
            "on_surface_variant": theme.on_surface_variant,
            "error": theme.error,
            "success": theme.success,
            "warning": theme.warning,
            "outline": theme.outline,
            "outline_variant": theme.outline_variant,
        }


# Singleton
_theme_manager: Optional[ThemeManager] = None


def get_theme_manager() -> ThemeManager:
    """Retorna instância singleton do gerenciador de temas."""
    global _theme_manager
    if _theme_manager is None:
        _theme_manager = ThemeManager()
    return _theme_manager


def get_current_theme() -> ThemeColors:
    """Retorna tema atual."""
    return get_theme_manager().current_theme

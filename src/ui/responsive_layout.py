"""
AutoTabloide AI - Responsive Layout System
============================================
Sistema de layout responsivo para diferentes resoluções.
PROTOCOLO DE RETIFICAÇÃO: Passo 77 (Responsividade 1366x768).

Adapta UI para notebooks com telas menores.
"""

import logging
from typing import Optional, Dict, Any, Tuple, Callable, List
from dataclasses import dataclass
from enum import Enum
import flet as ft

logger = logging.getLogger("ResponsiveLayout")


class ScreenSize(Enum):
    """Categorias de tamanho de tela."""
    SMALL = "small"       # < 1366px (tablets, notebooks antigos)
    MEDIUM = "medium"     # 1366-1920px (notebooks)
    LARGE = "large"       # > 1920px (monitores)


@dataclass
class BreakpointConfig:
    """Configuração de breakpoints."""
    small_max: int = 1366
    medium_max: int = 1920
    
    # Dimensões mínimas
    min_width: int = 1024
    min_height: int = 600


@dataclass
class ResponsiveValues:
    """Valores responsivos para cada tamanho."""
    sidebar_width: int = 250
    rail_width: int = 80
    card_width: int = 200
    grid_columns: int = 4
    font_scale: float = 1.0
    spacing: int = 16
    padding: int = 20
    show_labels: bool = True


class ResponsiveLayoutManager:
    """
    Gerenciador de layout responsivo.
    
    PASSO 77: Suporte a 1366x768.
    """
    
    # Configurações por tamanho de tela
    PRESETS: Dict[ScreenSize, ResponsiveValues] = {
        ScreenSize.SMALL: ResponsiveValues(
            sidebar_width=200,
            rail_width=60,
            card_width=150,
            grid_columns=3,
            font_scale=0.9,
            spacing=12,
            padding=12,
            show_labels=False
        ),
        ScreenSize.MEDIUM: ResponsiveValues(
            sidebar_width=250,
            rail_width=80,
            card_width=180,
            grid_columns=4,
            font_scale=1.0,
            spacing=16,
            padding=16,
            show_labels=True
        ),
        ScreenSize.LARGE: ResponsiveValues(
            sidebar_width=300,
            rail_width=100,
            card_width=220,
            grid_columns=5,
            font_scale=1.0,
            spacing=20,
            padding=20,
            show_labels=True
        ),
    }
    
    def __init__(self, config: Optional[BreakpointConfig] = None):
        self.config = config or BreakpointConfig()
        self._current_size: ScreenSize = ScreenSize.MEDIUM
        self._current_values: ResponsiveValues = self.PRESETS[ScreenSize.MEDIUM]
        self._callbacks: List[Callable[[ResponsiveValues], None]] = []
        self._page: Optional[ft.Page] = None
    
    def attach(self, page: ft.Page) -> None:
        """Anexa ao page do Flet para monitorar resize."""
        self._page = page
        
        # Detectar tamanho inicial
        self._update_size(page.window_width, page.window_height)
        
        # Handler de resize
        def on_resize(e):
            self._update_size(page.window_width, page.window_height)
        
        page.on_resize = on_resize
    
    def _update_size(self, width: int, height: int) -> None:
        """Atualiza tamanho baseado nas dimensões."""
        # Determinar categoria
        if width < self.config.small_max:
            new_size = ScreenSize.SMALL
        elif width < self.config.medium_max:
            new_size = ScreenSize.MEDIUM
        else:
            new_size = ScreenSize.LARGE
        
        # Mudar apenas se diferente
        if new_size != self._current_size:
            self._current_size = new_size
            self._current_values = self.PRESETS[new_size]
            
            logger.info(f"Layout responsivo: {new_size.value} ({width}x{height})")
            
            # Notificar callbacks
            for callback in self._callbacks:
                try:
                    callback(self._current_values)
                except Exception as e:
                    logger.error(f"Erro em callback responsivo: {e}")
    
    def on_change(self, callback: Callable[[ResponsiveValues], None]) -> None:
        """Registra callback para mudanças de tamanho."""
        self._callbacks.append(callback)
    
    @property
    def current(self) -> ResponsiveValues:
        """Retorna valores atuais."""
        return self._current_values
    
    @property
    def size(self) -> ScreenSize:
        """Retorna tamanho atual."""
        return self._current_size
    
    @property
    def is_small(self) -> bool:
        """True se tela é pequena."""
        return self._current_size == ScreenSize.SMALL
    
    @property
    def is_large(self) -> bool:
        """True se tela é grande."""
        return self._current_size == ScreenSize.LARGE
    
    # =========================================================================
    # HELPERS DE LAYOUT
    # =========================================================================
    
    def get_grid_columns(self, container_width: int) -> int:
        """Calcula colunas de grid baseado na largura."""
        card_width = self._current_values.card_width
        spacing = self._current_values.spacing
        
        return max(1, (container_width + spacing) // (card_width + spacing))
    
    def get_text_size(self, base_size: int) -> int:
        """Retorna tamanho de texto escalado."""
        return int(base_size * self._current_values.font_scale)
    
    def should_collapse_sidebar(self) -> bool:
        """Retorna se sidebar deve ser colapsada."""
        return self._current_size == ScreenSize.SMALL
    
    def get_slot_size(self, available_width: int, columns: int) -> Tuple[int, int]:
        """Calcula tamanho de slot para grid."""
        spacing = self._current_values.spacing
        total_spacing = spacing * (columns - 1)
        slot_width = (available_width - total_spacing) // columns
        
        # Aspecto 4:3 para tabloides
        slot_height = int(slot_width * 0.75)
        
        return slot_width, slot_height


# ==============================================================================
# COMPONENTES RESPONSIVOS
# ==============================================================================

class ResponsiveRow(ft.UserControl):
    """Row que quebra em coluna em telas pequenas."""
    
    def __init__(
        self,
        controls: List[ft.Control],
        manager: ResponsiveLayoutManager,
        **kwargs
    ):
        super().__init__()
        self._controls = controls
        self._manager = manager
        self._kwargs = kwargs
    
    def build(self):
        if self._manager.is_small:
            return ft.Column(
                self._controls,
                spacing=self._manager.current.spacing
            )
        else:
            return ft.Row(
                self._controls,
                spacing=self._manager.current.spacing,
                **self._kwargs
            )


class ResponsiveGrid(ft.UserControl):
    """Grid que adapta colunas automaticamente."""
    
    def __init__(
        self,
        controls: List[ft.Control],
        manager: ResponsiveLayoutManager,
        min_card_width: int = 150,
    ):
        super().__init__()
        self._controls = controls
        self._manager = manager
        self._min_card_width = min_card_width
    
    def build(self):
        columns = self._manager.current.grid_columns
        
        return ft.GridView(
            self._controls,
            runs_count=columns,
            child_aspect_ratio=1.33,  # 4:3
            spacing=self._manager.current.spacing,
            run_spacing=self._manager.current.spacing,
        )


# ==============================================================================
# INSTÂNCIA GLOBAL
# ==============================================================================

_layout_manager: Optional[ResponsiveLayoutManager] = None


def get_responsive_manager() -> ResponsiveLayoutManager:
    """Retorna instância global do gerenciador."""
    global _layout_manager
    if _layout_manager is None:
        _layout_manager = ResponsiveLayoutManager()
    return _layout_manager


def setup_responsive_layout(page: ft.Page) -> ResponsiveLayoutManager:
    """Configura layout responsivo para uma página."""
    manager = get_responsive_manager()
    manager.attach(page)
    return manager

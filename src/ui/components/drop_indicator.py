"""
AutoTabloide AI - Drop Indicator
==================================
Indicador visual de drop em slots.
Passo 59 do Checklist 100.

Funcionalidades:
- Indicador verde/vermelho no drop
- Feedback visual para drag & drop
"""

import flet as ft
from typing import Optional, Callable

from src.ui.design_system import DesignTokens


class DropIndicator(ft.Container):
    """
    Indicador visual de drop válido/inválido.
    Passo 59 do Checklist - Indicador verde/vermelho no drop.
    """
    
    def __init__(
        self,
        width: float = 100,
        height: float = 100,
        on_accept: Optional[Callable] = None,
        on_reject: Optional[Callable] = None
    ):
        self.on_accept = on_accept
        self.on_reject = on_reject
        self._is_valid_drop = True
        
        super().__init__(
            width=width,
            height=height,
            border_radius=8,
            border=ft.border.all(2, DesignTokens.BORDER),
            animate=ft.animation.Animation(150, ft.AnimationCurve.EASE_OUT)
        )
    
    def set_drop_state(self, state: str) -> None:
        """
        Define estado do indicador.
        
        Args:
            state: 'valid', 'invalid', 'hover', 'none'
        """
        if state == "valid":
            self.border = ft.border.all(3, DesignTokens.SUCCESS)
            self.bgcolor = ft.colors.with_opacity(0.1, DesignTokens.SUCCESS)
            self._is_valid_drop = True
        elif state == "invalid":
            self.border = ft.border.all(3, DesignTokens.ERROR)
            self.bgcolor = ft.colors.with_opacity(0.1, DesignTokens.ERROR)
            self._is_valid_drop = False
        elif state == "hover":
            self.border = ft.border.all(2, DesignTokens.PRIMARY)
            self.bgcolor = ft.colors.with_opacity(0.05, DesignTokens.PRIMARY)
        else:  # none
            self.border = ft.border.all(2, DesignTokens.BORDER)
            self.bgcolor = None
        
        self.update()
    
    def is_valid_drop(self) -> bool:
        """Retorna se o drop atual é válido."""
        return self._is_valid_drop


class SlotDropZone(ft.DragTarget):
    """
    Zona de drop para slots com indicador visual.
    """
    
    def __init__(
        self,
        slot_id: str,
        on_drop: Callable,
        validate_drop: Optional[Callable] = None,
        width: float = 150,
        height: float = 150
    ):
        """
        Args:
            slot_id: ID do slot
            on_drop: Callback ao soltar item
            validate_drop: Função para validar se drop é permitido
            width: Largura da zona
            height: Altura da zona
        """
        self.slot_id = slot_id
        self._on_drop = on_drop
        self._validate_drop = validate_drop or (lambda _: True)
        
        # Indicador interno
        self._indicator = DropIndicator(width=width, height=height)
        
        super().__init__(
            group="products",
            content=self._indicator,
            on_will_accept=self._handle_will_accept,
            on_accept=self._handle_accept,
            on_leave=self._handle_leave
        )
    
    def _handle_will_accept(self, e) -> None:
        """Chamado quando item entra na zona."""
        # Valida se pode aceitar
        is_valid = self._validate_drop(e.data)
        
        if is_valid:
            self._indicator.set_drop_state("valid")
        else:
            self._indicator.set_drop_state("invalid")
    
    def _handle_accept(self, e) -> None:
        """Chamado quando item é solto."""
        if self._indicator.is_valid_drop():
            self._on_drop(self.slot_id, e.data)
            self._indicator.set_drop_state("none")
        else:
            self._indicator.set_drop_state("none")
    
    def _handle_leave(self, e) -> None:
        """Chamado quando item sai da zona."""
        self._indicator.set_drop_state("none")


class ProductDraggable(ft.Draggable):
    """
    Produto arrastável para uso com SlotDropZone.
    """
    
    def __init__(
        self,
        product_id: int,
        product_name: str,
        content: ft.Control
    ):
        """
        Args:
            product_id: ID do produto
            product_name: Nome para exibição
            content: Conteúdo visual
        """
        self.product_id = product_id
        
        super().__init__(
            group="products",
            content=content,
            content_feedback=ft.Container(
                content=ft.Text(product_name, size=12),
                bgcolor=DesignTokens.PRIMARY,
                padding=10,
                border_radius=8,
                opacity=0.8
            ),
            data=str(product_id)
        )


# ==============================================================================
# HELPER FUNCTIONS
# ==============================================================================

def create_drop_zone_grid(
    num_slots: int,
    on_drop: Callable,
    validate_drop: Optional[Callable] = None,
    columns: int = 4
) -> ft.GridView:
    """
    Cria grid de zonas de drop.
    
    Args:
        num_slots: Número de slots
        on_drop: Callback de drop
        validate_drop: Validador de drop
        columns: Número de colunas
        
    Returns:
        GridView com zonas de drop
    """
    zones = []
    
    for i in range(1, num_slots + 1):
        slot_id = f"SLOT_{i:02d}"
        zone = SlotDropZone(
            slot_id=slot_id,
            on_drop=on_drop,
            validate_drop=validate_drop
        )
        zones.append(zone)
    
    return ft.GridView(
        controls=zones,
        runs_count=columns,
        max_extent=160,
        spacing=10,
        run_spacing=10
    )

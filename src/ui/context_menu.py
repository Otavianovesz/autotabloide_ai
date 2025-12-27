"""
AutoTabloide AI - Context Menu System
=======================================
Sistema de menus de contexto para UI.
PROTOCOLO DE RETIFICAÇÃO: Passo 85 (Menu de contexto).

Menus de contexto ricos para slots, produtos e layouts.
"""

import logging
from typing import Optional, List, Callable, Dict, Any
from dataclasses import dataclass, field
from enum import Enum
import flet as ft

logger = logging.getLogger("ContextMenu")


class MenuItemType(Enum):
    """Tipos de item de menu."""
    ACTION = "action"
    SEPARATOR = "separator"
    SUBMENU = "submenu"
    CHECKBOX = "checkbox"


@dataclass
class ContextMenuItem:
    """Item de menu de contexto."""
    label: str
    item_type: MenuItemType = MenuItemType.ACTION
    icon: Optional[str] = None
    shortcut: Optional[str] = None
    enabled: bool = True
    checked: bool = False
    action: Optional[Callable[[], None]] = None
    submenu: List['ContextMenuItem'] = field(default_factory=list)
    data: Any = None  # Dados extras


@dataclass
class ContextMenuConfig:
    """Configuração do menu de contexto."""
    items: List[ContextMenuItem]
    title: Optional[str] = None
    width: int = 200


class ContextMenuBuilder:
    """
    Builder para criar menus de contexto.
    
    PASSO 85: Menus de contexto completos.
    """
    
    def __init__(self):
        self._items: List[ContextMenuItem] = []
    
    def add_action(
        self,
        label: str,
        action: Callable[[], None],
        icon: Optional[str] = None,
        shortcut: Optional[str] = None,
        enabled: bool = True
    ) -> 'ContextMenuBuilder':
        """Adiciona item de ação."""
        self._items.append(ContextMenuItem(
            label=label,
            item_type=MenuItemType.ACTION,
            icon=icon,
            shortcut=shortcut,
            enabled=enabled,
            action=action
        ))
        return self
    
    def add_separator(self) -> 'ContextMenuBuilder':
        """Adiciona separador."""
        self._items.append(ContextMenuItem(
            label="",
            item_type=MenuItemType.SEPARATOR
        ))
        return self
    
    def add_checkbox(
        self,
        label: str,
        checked: bool,
        action: Callable[[bool], None],
        enabled: bool = True
    ) -> 'ContextMenuBuilder':
        """Adiciona checkbox."""
        def toggle_action():
            action(not checked)
        
        self._items.append(ContextMenuItem(
            label=label,
            item_type=MenuItemType.CHECKBOX,
            checked=checked,
            enabled=enabled,
            action=toggle_action
        ))
        return self
    
    def add_submenu(
        self,
        label: str,
        items: List[ContextMenuItem],
        icon: Optional[str] = None
    ) -> 'ContextMenuBuilder':
        """Adiciona submenu."""
        self._items.append(ContextMenuItem(
            label=label,
            item_type=MenuItemType.SUBMENU,
            icon=icon,
            submenu=items
        ))
        return self
    
    def build(self, title: Optional[str] = None) -> ContextMenuConfig:
        """Constrói configuração do menu."""
        return ContextMenuConfig(items=self._items.copy(), title=title)


class ContextMenuManager:
    """Gerenciador central de menus de contexto."""
    
    def __init__(self, page: ft.Page):
        self.page = page
        self._current_menu: Optional[ft.AlertDialog] = None
    
    def show(
        self,
        config: ContextMenuConfig,
        x: Optional[int] = None,
        y: Optional[int] = None
    ) -> None:
        """
        Exibe menu de contexto.
        
        Args:
            config: Configuração do menu
            x, y: Posição (se None, centraliza)
        """
        # Fechar menu anterior se existir
        self.hide()
        
        # Criar conteúdo do menu
        content = self._build_menu_content(config)
        
        # Criar diálogo como menu
        self._current_menu = ft.AlertDialog(
            modal=False,
            title=ft.Text(config.title) if config.title else None,
            content=ft.Container(
                content=content,
                width=config.width,
                padding=0,
            ),
            actions=[],
            shape=ft.RoundedRectangleBorder(radius=8),
        )
        
        self.page.dialog = self._current_menu
        self._current_menu.open = True
        self.page.update()
    
    def hide(self) -> None:
        """Fecha menu de contexto atual."""
        if self._current_menu:
            self._current_menu.open = False
            self.page.update()
            self._current_menu = None
    
    def _build_menu_content(self, config: ContextMenuConfig) -> ft.Control:
        """Constrói conteúdo visual do menu."""
        items = []
        
        for item in config.items:
            if item.item_type == MenuItemType.SEPARATOR:
                items.append(ft.Divider(height=1))
            else:
                items.append(self._build_menu_item(item))
        
        return ft.Column(
            items,
            spacing=0,
            tight=True,
        )
    
    def _build_menu_item(self, item: ContextMenuItem) -> ft.Control:
        """Constrói item visual do menu."""
        # Ícone
        leading = None
        if item.icon:
            leading = ft.Icon(item.icon, size=18)
        elif item.item_type == MenuItemType.CHECKBOX:
            leading = ft.Icon(
                ft.icons.CHECK if item.checked else ft.icons.CHECK_BOX_OUTLINE_BLANK,
                size=18
            )
        
        # Trailing (shortcut ou seta de submenu)
        trailing = None
        if item.shortcut:
            trailing = ft.Text(
                item.shortcut,
                size=12,
                color=ft.colors.GREY_500,
            )
        elif item.item_type == MenuItemType.SUBMENU:
            trailing = ft.Icon(ft.icons.CHEVRON_RIGHT, size=16)
        
        # Container clicável
        def on_click(e):
            if item.action and item.enabled:
                self.hide()
                item.action()
        
        return ft.Container(
            content=ft.Row(
                [
                    leading if leading else ft.Container(width=18),
                    ft.Container(width=8),
                    ft.Text(
                        item.label,
                        expand=True,
                        color=ft.colors.GREY_500 if not item.enabled else None,
                    ),
                    trailing if trailing else ft.Container(),
                ],
                alignment=ft.MainAxisAlignment.START,
            ),
            padding=ft.padding.symmetric(horizontal=12, vertical=8),
            on_click=on_click if item.enabled else None,
            on_hover=lambda e: self._on_item_hover(e) if item.enabled else None,
            bgcolor=ft.colors.TRANSPARENT,
        )
    
    def _on_item_hover(self, e: ft.ControlEvent) -> None:
        """Handler de hover em item."""
        container = e.control
        if e.data == "true":
            container.bgcolor = ft.colors.with_opacity(0.1, ft.colors.PRIMARY)
        else:
            container.bgcolor = ft.colors.TRANSPARENT
        container.update()


# ==============================================================================
# MENUS PRÉ-DEFINIDOS
# ==============================================================================

def create_slot_context_menu(
    slot_index: int,
    has_product: bool,
    on_clear: Callable,
    on_edit: Callable,
    on_search: Callable,
    on_copy: Callable,
    on_paste: Callable,
    has_clipboard: bool = False
) -> ContextMenuConfig:
    """
    Cria menu de contexto para slot do Ateliê.
    
    Args:
        slot_index: Índice do slot
        has_product: Se slot tem produto
        on_*: Callbacks para cada ação
        has_clipboard: Se há produto copiado
    """
    builder = ContextMenuBuilder()
    
    if has_product:
        builder.add_action(
            "Editar Produto",
            on_edit,
            icon=ft.icons.EDIT,
            shortcut="Enter"
        )
        builder.add_action(
            "Copiar",
            on_copy,
            icon=ft.icons.COPY,
            shortcut="Ctrl+C"
        )
        builder.add_separator()
        builder.add_action(
            "Buscar Imagem",
            on_search,
            icon=ft.icons.IMAGE_SEARCH,
        )
        builder.add_separator()
        builder.add_action(
            "Limpar Slot",
            on_clear,
            icon=ft.icons.DELETE,
            shortcut="Del"
        )
    else:
        builder.add_action(
            "Colar",
            on_paste,
            icon=ft.icons.PASTE,
            shortcut="Ctrl+V",
            enabled=has_clipboard
        )
        builder.add_action(
            "Buscar Produto",
            on_search,
            icon=ft.icons.SEARCH,
        )
    
    return builder.build(title=f"Slot {slot_index + 1}")


def create_product_context_menu(
    product_name: str,
    on_add_to_atelier: Callable,
    on_edit: Callable,
    on_search_image: Callable,
    on_view_history: Callable,
    on_delete: Callable
) -> ContextMenuConfig:
    """Cria menu de contexto para produto no Estoque."""
    builder = ContextMenuBuilder()
    
    builder.add_action(
        "Adicionar ao Ateliê",
        on_add_to_atelier,
        icon=ft.icons.ADD_CIRCLE,
    )
    builder.add_separator()
    builder.add_action(
        "Editar",
        on_edit,
        icon=ft.icons.EDIT,
        shortcut="Enter"
    )
    builder.add_action(
        "Buscar Imagem",
        on_search_image,
        icon=ft.icons.IMAGE_SEARCH,
    )
    builder.add_action(
        "Ver Histórico",
        on_view_history,
        icon=ft.icons.HISTORY,
    )
    builder.add_separator()
    builder.add_action(
        "Arquivar",
        on_delete,
        icon=ft.icons.ARCHIVE,
    )
    
    return builder.build(title=product_name[:30])


def create_layout_context_menu(
    layout_name: str,
    on_select: Callable,
    on_preview: Callable,
    on_duplicate: Callable,
    on_edit: Callable,
    on_delete: Callable
) -> ContextMenuConfig:
    """Cria menu de contexto para layout."""
    builder = ContextMenuBuilder()
    
    builder.add_action(
        "Usar Layout",
        on_select,
        icon=ft.icons.CHECK_CIRCLE,
    )
    builder.add_action(
        "Visualizar",
        on_preview,
        icon=ft.icons.PREVIEW,
    )
    builder.add_separator()
    builder.add_action(
        "Duplicar",
        on_duplicate,
        icon=ft.icons.COPY_ALL,
    )
    builder.add_action(
        "Editar Tags",
        on_edit,
        icon=ft.icons.EDIT,
    )
    builder.add_separator()
    builder.add_action(
        "Excluir",
        on_delete,
        icon=ft.icons.DELETE,
    )
    
    return builder.build(title=layout_name)


# ==============================================================================
# INSTÂNCIA GLOBAL
# ==============================================================================

_menu_manager: Optional[ContextMenuManager] = None


def get_context_menu_manager(page: Optional[ft.Page] = None) -> Optional[ContextMenuManager]:
    """Retorna instância global do gerenciador."""
    global _menu_manager
    
    if page and _menu_manager is None:
        _menu_manager = ContextMenuManager(page)
    
    return _menu_manager


def show_context_menu(
    config: ContextMenuConfig,
    page: ft.Page,
    x: Optional[int] = None,
    y: Optional[int] = None
) -> None:
    """Função de conveniência para exibir menu."""
    manager = get_context_menu_manager(page)
    if manager:
        manager.show(config, x, y)

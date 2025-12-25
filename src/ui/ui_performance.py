"""
AutoTabloide AI - UI Performance Module
========================================
Century Checklist Items 21-35: Melhorias de Performance de UI.
Virtualização, Debounce, Cache, Prevenção de Cliques.
"""

import flet as ft
import asyncio
import threading
from typing import Optional, Callable, List, Dict, Any
from dataclasses import dataclass
from functools import lru_cache


# ==============================================================================
# ITEM 21: Virtualização de Listas (Lazy Loading)
# ==============================================================================

class VirtualizedProductList(ft.UserControl):
    """
    Lista virtualizada de produtos com carregamento sob demanda.
    Resolve o problema de performance do controls.append().
    
    Carrega produtos em páginas de 50, adicionando mais ao scroll.
    """
    
    PAGE_SIZE = 50
    
    def __init__(
        self,
        on_product_select: Optional[Callable[[Dict], None]] = None,
        on_product_drag: Optional[Callable[[Dict], None]] = None,
    ):
        super().__init__()
        self.on_product_select = on_product_select
        self.on_product_drag = on_product_drag
        
        self._all_products: List[Dict] = []
        self._filtered_products: List[Dict] = []
        self._displayed_count = 0
        self._is_loading = False
        self._search_term = ""
        
        self._list_view: Optional[ft.ListView] = None
        self._loading_indicator: Optional[ft.Container] = None
    
    def build(self):
        self._list_view = ft.ListView(
            expand=True,
            spacing=8,
            padding=ft.padding.all(8),
            auto_scroll=False,
            on_scroll=self._on_scroll,
        )
        
        self._loading_indicator = ft.Container(
            content=ft.ProgressRing(width=20, height=20),
            alignment=ft.alignment.center,
            visible=False,
            height=40,
        )
        
        return ft.Column([
            ft.Container(
                content=self._list_view,
                expand=True,
            ),
            self._loading_indicator,
        ], expand=True, spacing=0)
    
    def set_products(self, products: List[Dict]):
        """Define lista completa de produtos."""
        self._all_products = products
        self._apply_filter()
    
    def filter(self, search_term: str):
        """Aplica filtro de busca."""
        self._search_term = search_term.lower().strip()
        self._apply_filter()
    
    def _apply_filter(self):
        """Aplica filtro e reinicia display."""
        if self._search_term:
            self._filtered_products = [
                p for p in self._all_products
                if self._search_term in (p.get("nome", "") or "").lower()
                or self._search_term in (p.get("sku", "") or "").lower()
                or self._search_term in (p.get("marca", "") or "").lower()
            ]
        else:
            self._filtered_products = self._all_products.copy()
        
        self._displayed_count = 0
        self._list_view.controls.clear()
        self._load_more()
    
    def _load_more(self):
        """Carrega próxima página de produtos."""
        if self._is_loading:
            return
        
        remaining = len(self._filtered_products) - self._displayed_count
        if remaining <= 0:
            return
        
        self._is_loading = True
        self._loading_indicator.visible = True
        
        try:
            # Carrega próxima página
            end = min(self._displayed_count + self.PAGE_SIZE, len(self._filtered_products))
            
            for i in range(self._displayed_count, end):
                product = self._filtered_products[i]
                card = self._build_product_card(product)
                self._list_view.controls.append(card)
            
            self._displayed_count = end
            
        finally:
            self._is_loading = False
            self._loading_indicator.visible = False
            self.update()
    
    def _on_scroll(self, e: ft.OnScrollEvent):
        """Handler de scroll para carregar mais."""
        # Carrega mais quando chegar perto do final
        if e.pixels >= e.max_scroll_extent - 200:
            self._load_more()
    
    def _build_product_card(self, product: Dict) -> ft.Control:
        """Constrói card leve de produto."""
        
        def on_click(e):
            if self.on_product_select:
                self.on_product_select(product)
        
        # Card minimalista para performance
        return ft.Container(
            content=ft.Row([
                # Thumbnail placeholder
                ft.Container(
                    width=50,
                    height=50,
                    bgcolor="#2a2a2a",
                    border_radius=4,
                    content=ft.Icon(
                        ft.icons.IMAGE_OUTLINED,
                        size=24,
                        color="#666"
                    ) if not product.get("thumbnail") else ft.Image(
                        src=product["thumbnail"],
                        fit=ft.ImageFit.COVER,
                    ),
                ),
                # Info
                ft.Column([
                    ft.Text(
                        product.get("nome", "Sem nome")[:40],
                        size=13,
                        weight=ft.FontWeight.W_500,
                        max_lines=1,
                        overflow=ft.TextOverflow.ELLIPSIS,
                    ),
                    ft.Text(
                        f"R$ {product.get('preco', 0):.2f}",
                        size=12,
                        color="#4CAF50",
                    ),
                ], spacing=2, expand=True),
            ], spacing=10),
            padding=ft.padding.all(8),
            border_radius=6,
            bgcolor="#1e1e1e",
            on_click=on_click,
            on_hover=lambda e: self._on_card_hover(e),
            data=product,  # Para drag
        )
    
    def _on_card_hover(self, e):
        """Efeito hover."""
        e.control.bgcolor = "#2a2a2a" if e.data == "true" else "#1e1e1e"
        e.control.update()
    
    @property
    def total_count(self) -> int:
        return len(self._all_products)
    
    @property
    def filtered_count(self) -> int:
        return len(self._filtered_products)
    
    @property
    def displayed_count(self) -> int:
        return self._displayed_count


# ==============================================================================
# ITEM 22: Debounce para Busca
# ==============================================================================

class DebouncedSearchField(ft.UserControl):
    """
    Campo de busca com debounce de 300ms.
    Evita chamadas excessivas durante digitação rápida.
    """
    
    def __init__(
        self,
        on_search: Callable[[str], None],
        placeholder: str = "Buscar...",
        debounce_ms: int = 300,
    ):
        super().__init__()
        self.on_search = on_search
        self.placeholder = placeholder
        self.debounce_ms = debounce_ms
        
        self._timer: Optional[threading.Timer] = None
        self._lock = threading.Lock()
        self._text_field: Optional[ft.TextField] = None
    
    def build(self):
        self._text_field = ft.TextField(
            hint_text=self.placeholder,
            prefix_icon=ft.icons.SEARCH,
            on_change=self._on_change,
            border_radius=8,
            content_padding=ft.padding.symmetric(horizontal=16, vertical=8),
            expand=True,
        )
        return self._text_field
    
    def _on_change(self, e):
        """Handler com debounce."""
        with self._lock:
            if self._timer:
                self._timer.cancel()
            
            self._timer = threading.Timer(
                self.debounce_ms / 1000.0,
                lambda: self._execute_search(e.control.value)
            )
            self._timer.start()
    
    def _execute_search(self, term: str):
        """Executa busca após debounce."""
        if self.on_search:
            self.on_search(term)
    
    def clear(self):
        """Limpa o campo."""
        if self._text_field:
            self._text_field.value = ""
            self._text_field.update()
    
    @property
    def value(self) -> str:
        return self._text_field.value if self._text_field else ""


# ==============================================================================
# ITEM 26: Loading Skeleton
# ==============================================================================

class SkeletonLoader(ft.UserControl):
    """
    Esqueletos de loading para feedback visual.
    Mostra retângulos animados enquanto carrega.
    """
    
    def __init__(self, count: int = 5, height: int = 60):
        super().__init__()
        self.count = count
        self.height = height
    
    def build(self):
        skeletons = []
        for _ in range(self.count):
            skeleton = ft.Container(
                content=ft.Row([
                    # Thumbnail skeleton
                    ft.Container(
                        width=50,
                        height=50,
                        border_radius=4,
                        bgcolor="#2a2a2a",
                        animate=ft.animation.Animation(1000, "easeInOut"),
                    ),
                    # Text skeletons
                    ft.Column([
                        ft.Container(
                            width=150,
                            height=14,
                            border_radius=4,
                            bgcolor="#2a2a2a",
                        ),
                        ft.Container(
                            width=80,
                            height=12,
                            border_radius=4,
                            bgcolor="#252525",
                        ),
                    ], spacing=6),
                ], spacing=12),
                padding=ft.padding.all(8),
                height=self.height,
            )
            skeletons.append(skeleton)
        
        return ft.Column(skeletons, spacing=8)


# ==============================================================================
# ITEM 27: Modal de Renderização com Progresso
# ==============================================================================

class RenderProgressModal(ft.UserControl):
    """
    Modal de progresso de renderização que não pode ser fechado.
    Mostra barra de progresso real e status detalhado.
    """
    
    def __init__(self, page: ft.Page):
        super().__init__()
        self.page = page
        self._dialog: Optional[ft.AlertDialog] = None
        self._progress_bar: Optional[ft.ProgressBar] = None
        self._status_text: Optional[ft.Text] = None
        self._detail_text: Optional[ft.Text] = None
    
    def build(self):
        self._progress_bar = ft.ProgressBar(
            width=400,
            value=0,
            color="#4CAF50",
            bgcolor="#333",
        )
        
        self._status_text = ft.Text(
            "Iniciando renderização...",
            size=16,
            weight=ft.FontWeight.W_500,
        )
        
        self._detail_text = ft.Text(
            "",
            size=12,
            color="#888",
        )
        
        content = ft.Container(
            content=ft.Column([
                ft.Icon(ft.icons.PRINT, size=48, color="#4CAF50"),
                self._status_text,
                self._progress_bar,
                self._detail_text,
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=16),
            padding=ft.padding.all(32),
            width=450,
        )
        
        self._dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Gerando Tabloide"),
            content=content,
            actions=[],  # Sem botões - não pode fechar
        )
        
        return self._dialog
    
    def show(self):
        """Exibe o modal."""
        self.page.dialog = self._dialog
        self._dialog.open = True
        self.page.update()
    
    def hide(self):
        """Esconde o modal."""
        self._dialog.open = False
        self.page.update()
    
    def update_progress(self, value: float, status: str = "", detail: str = ""):
        """Atualiza progresso (0.0 a 1.0)."""
        if self._progress_bar:
            self._progress_bar.value = value
        if self._status_text and status:
            self._status_text.value = status
        if self._detail_text:
            self._detail_text.value = detail
        self.update()


# ==============================================================================
# ITEM 29: Tooltips
# ==============================================================================

def with_tooltip(control: ft.Control, message: str) -> ft.Tooltip:
    """Wrapper para adicionar tooltip a qualquer controle."""
    return ft.Tooltip(
        message=message,
        content=control,
        wait_duration=300,
        show_duration=3000,
    )


# ==============================================================================
# ITEM 30: Toast Notifications
# ==============================================================================

class ToastNotification:
    """
    Sistema de notificações toast usando SnackBar.
    Substitui print() e mensagens de console.
    """
    
    def __init__(self, page: ft.Page):
        self.page = page
    
    def success(self, message: str, duration: int = 3000):
        """Notificação de sucesso (verde)."""
        self._show(message, ft.colors.GREEN_700, ft.icons.CHECK_CIRCLE, duration)
    
    def error(self, message: str, duration: int = 5000):
        """Notificação de erro (vermelho)."""
        self._show(message, ft.colors.RED_700, ft.icons.ERROR, duration)
    
    def warning(self, message: str, duration: int = 4000):
        """Notificação de aviso (amarelo)."""
        self._show(message, ft.colors.ORANGE_700, ft.icons.WARNING, duration)
    
    def info(self, message: str, duration: int = 3000):
        """Notificação informativa (azul)."""
        self._show(message, ft.colors.BLUE_700, ft.icons.INFO, duration)
    
    def _show(self, message: str, color: str, icon: str, duration: int):
        """Exibe snackbar."""
        self.page.snack_bar = ft.SnackBar(
            content=ft.Row([
                ft.Icon(icon, color="white", size=20),
                ft.Text(message, color="white"),
            ], spacing=8),
            bgcolor=color,
            duration=duration,
        )
        self.page.snack_bar.open = True
        self.page.update()


# ==============================================================================
# ITEM 32: Estado "Sujo" (Dirty State)
# ==============================================================================

class DirtyStateManager:
    """
    Gerencia estado "sujo" da aplicação.
    Avisa usuário sobre alterações não salvas.
    """
    
    def __init__(self, page: ft.Page):
        self.page = page
        self._is_dirty = False
        self._what_changed: List[str] = []
    
    def mark_dirty(self, reason: str = ""):
        """Marca como alterado."""
        self._is_dirty = True
        if reason and reason not in self._what_changed:
            self._what_changed.append(reason)
    
    def mark_clean(self):
        """Marca como salvo."""
        self._is_dirty = False
        self._what_changed.clear()
    
    @property
    def is_dirty(self) -> bool:
        return self._is_dirty
    
    def confirm_discard(self, callback: Callable[[], None]):
        """Mostra confirmação antes de descartar alterações."""
        if not self._is_dirty:
            callback()
            return
        
        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Alterações não salvas"),
            content=ft.Text(
                "Existem alterações não salvas. Deseja descartar?"
            ),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda _: self._close_dialog()),
                ft.ElevatedButton(
                    "Descartar",
                    bgcolor=ft.colors.RED_700,
                    color="white",
                    on_click=lambda _: self._confirm_and_close(callback)
                ),
            ],
        )
        
        self.page.dialog = dialog
        dialog.open = True
        self.page.update()
    
    def _close_dialog(self):
        if self.page.dialog:
            self.page.dialog.open = False
            self.page.update()
    
    def _confirm_and_close(self, callback: Callable):
        self._close_dialog()
        self.mark_clean()
        callback()


# ==============================================================================
# ITEM 34: Foco Automático em Modais
# ==============================================================================

def auto_focus_modal(dialog: ft.AlertDialog, field: ft.TextField):
    """Configura foco automático em campo do modal."""
    field.autofocus = True
    return dialog


# ==============================================================================
# ITEM 35: Prevenção de Clique Duplo (Button Guard)
# ==============================================================================

class SafeButton(ft.ElevatedButton):
    """
    Botão com proteção contra clique duplo.
    Desabilita automaticamente após clique e reabilita após cooldown.
    """
    
    def __init__(
        self,
        text: str,
        on_click: Callable,
        cooldown_ms: int = 1000,
        **kwargs
    ):
        self._original_on_click = on_click
        self._cooldown = cooldown_ms / 1000.0
        self._is_processing = False
        
        super().__init__(
            text=text,
            on_click=self._guarded_click,
            **kwargs
        )
    
    def _guarded_click(self, e):
        """Handler com proteção de clique duplo."""
        if self._is_processing:
            return
        
        self._is_processing = True
        self.disabled = True
        self.update()
        
        # Executa callback
        try:
            self._original_on_click(e)
        finally:
            # Re-habilita após cooldown
            async def reenable():
                await asyncio.sleep(self._cooldown)
                self._is_processing = False
                self.disabled = False
                self.update()
            
            asyncio.create_task(reenable())


# ==============================================================================
# EXPORTS
# ==============================================================================

__all__ = [
    "VirtualizedProductList",
    "DebouncedSearchField",
    "SkeletonLoader",
    "RenderProgressModal",
    "with_tooltip",
    "ToastNotification",
    "DirtyStateManager",
    "auto_focus_modal",
    "SafeButton",
]

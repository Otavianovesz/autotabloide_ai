"""
AutoTabloide AI - Design System Premium
=========================================
Sistema de design unificado conforme Vol. VI.
Cores, tipografia e componentes reutilizáveis.
"""

import flet as ft
from typing import Optional, Dict, Any
from dataclasses import dataclass
from enum import Enum


# ==============================================================================
# PALETA DE CORES PREMIUM
# ==============================================================================

class ColorScheme:
    """Esquema de cores premium com suporte a gradientes."""
    
    # Backgrounds
    BG_PRIMARY = "#0A0A0F"         # Fundo principal (quase preto azulado)
    BG_SECONDARY = "#12121A"       # Cards/containers
    BG_ELEVATED = "#1A1A2E"        # Containers elevados
    BG_GLASS = "#1E1E2E99"         # Glassmorphism (com alpha)
    BG_HOVER = "#252538"           # Hover state
    
    # Accent Colors
    ACCENT_PRIMARY = "#6C5CE7"     # Roxo vibrante
    ACCENT_SECONDARY = "#00D9FF"   # Cyan neon
    ACCENT_TERTIARY = "#A855F7"    # Violet
    
    # Semantic Colors
    SUCCESS = "#00F5A0"            # Verde neon
    SUCCESS_SOFT = "#00F5A033"     # Verde com alpha
    WARNING = "#FFB800"            # Amarelo dourado
    WARNING_SOFT = "#FFB80033"     # Amarelo com alpha
    ERROR = "#FF4757"              # Vermelho coral
    ERROR_SOFT = "#FF475733"       # Vermelho com alpha
    INFO = "#00D9FF"               # Cyan
    INFO_SOFT = "#00D9FF33"        # Cyan com alpha
    
    # Text Colors
    TEXT_PRIMARY = "#FFFFFF"
    TEXT_SECONDARY = "#A0A0B0"
    TEXT_MUTED = "#6B6B7B"
    TEXT_DISABLED = "#4A4A5A"
    
    # Border Colors
    BORDER_DEFAULT = "#FFFFFF14"   # 8% white
    BORDER_HOVER = "#FFFFFF28"     # 16% white
    BORDER_ACTIVE = "#6C5CE7"      # Accent
    
    # Status Semáforo (Vol. VI)
    QUALITY_PERFECT = "#00F5A0"    # 3 - Verde
    QUALITY_ATTENTION = "#FFB800"  # 2 - Amarelo
    QUALITY_INCOMPLETE = "#FF9500" # 1 - Laranja
    QUALITY_CRITICAL = "#FF4757"   # 0 - Vermelho
    
    # Slot States
    SLOT_EMPTY = "#3A3A4C"
    SLOT_FILLED = "#1E3A5F"
    SLOT_HOVER = "#2D4F6E"
    SLOT_ACTIVE = "#3D5F7E"
    
    @classmethod
    def get_quality_color(cls, status: int) -> str:
        """Retorna cor baseada no status de qualidade."""
        colors = {
            0: cls.QUALITY_CRITICAL,
            1: cls.QUALITY_INCOMPLETE,
            2: cls.QUALITY_ATTENTION,
            3: cls.QUALITY_PERFECT
        }
        return colors.get(status, cls.TEXT_MUTED)
    
    @classmethod
    def with_alpha(cls, hex_color: str, alpha: float) -> str:
        """Adiciona alpha a uma cor hex."""
        alpha_hex = format(int(alpha * 255), '02x')
        return f"{hex_color}{alpha_hex}"


# ==============================================================================
# TIPOGRAFIA
# ==============================================================================

class Typography:
    """Sistema tipográfico consistente."""
    
    # Font Families
    FONT_DISPLAY = "Inter"
    FONT_BODY = "Inter"
    FONT_MONO = "JetBrains Mono"
    
    # Display (Hero text)
    DISPLAY_SIZE = 32
    DISPLAY_WEIGHT = ft.FontWeight.BOLD
    
    # Headings
    H1_SIZE = 28
    H2_SIZE = 24
    H3_SIZE = 20
    H4_SIZE = 18
    HEADING_WEIGHT = ft.FontWeight.W_600
    
    # Body
    BODY_SIZE = 14
    BODY_LARGE_SIZE = 16
    BODY_SMALL_SIZE = 13
    BODY_WEIGHT = ft.FontWeight.NORMAL
    
    # Caption/Labels
    CAPTION_SIZE = 12
    LABEL_SIZE = 11
    
    # Mono (código, SKUs)
    MONO_SIZE = 13


# ==============================================================================
# ESPAÇAMENTO E DIMENSÕES
# ==============================================================================

class Spacing:
    """Sistema de espaçamento consistente."""
    
    # Base unit: 4px
    XS = 4
    SM = 8
    MD = 12
    LG = 16
    XL = 20
    XXL = 24
    XXXL = 32
    
    # Padding padrão para containers
    CARD_PADDING = 16
    SECTION_PADDING = 24
    PAGE_PADDING = 32
    
    # Border radius
    RADIUS_SM = 6
    RADIUS_MD = 10
    RADIUS_LG = 16
    RADIUS_XL = 20
    RADIUS_FULL = 9999


# ==============================================================================
# ANIMAÇÕES
# ==============================================================================

class Animations:
    """Configurações de animação."""
    
    DURATION_FAST = 150
    DURATION_NORMAL = 200
    DURATION_SLOW = 300
    DURATION_LOADING = 800
    
    CURVE_DEFAULT = ft.AnimationCurve.EASE_OUT
    CURVE_BOUNCE = ft.AnimationCurve.EASE_OUT_BACK
    CURVE_SMOOTH = ft.AnimationCurve.EASE_IN_OUT


# ==============================================================================
# COMPONENTES REUTILIZÁVEIS
# ==============================================================================

def create_premium_card(
    content: ft.Control,
    padding: int = Spacing.CARD_PADDING,
    border_radius: int = Spacing.RADIUS_LG,
    hover_enabled: bool = True,
    on_click: callable = None,
    expand: bool = False,
    width: Optional[int] = None,
    height: Optional[int] = None,
) -> ft.Container:
    """
    Cria um card premium com efeito glassmorphism.
    
    Features:
    - Borda translúcida
    - Background com blur effect visual
    - Hover state com transição suave
    """
    
    def on_hover(e):
        if hover_enabled:
            e.control.bgcolor = ColorScheme.BG_HOVER if e.data == "true" else ColorScheme.BG_SECONDARY
            e.control.border = ft.border.all(1, ColorScheme.BORDER_HOVER if e.data == "true" else ColorScheme.BORDER_DEFAULT)
            e.control.update()
    
    return ft.Container(
        content=content,
        padding=padding,
        border_radius=border_radius,
        bgcolor=ColorScheme.BG_SECONDARY,
        border=ft.border.all(1, ColorScheme.BORDER_DEFAULT),
        animate=ft.Animation(Animations.DURATION_NORMAL, Animations.CURVE_DEFAULT),
        on_hover=on_hover if hover_enabled else None,
        on_click=on_click,
        expand=expand,
        width=width,
        height=height,
        shadow=ft.BoxShadow(
            blur_radius=20,
            color="#00000033",
            offset=ft.Offset(0, 4)
        )
    )


def create_gradient_button(
    text: str,
    icon: Optional[str] = None,
    on_click: callable = None,
    width: Optional[int] = None,
    height: int = 44,
    primary: bool = True,
) -> ft.Container:
    """
    Cria um botão com gradiente premium.
    """
    bg_color = ColorScheme.ACCENT_PRIMARY if primary else ColorScheme.BG_ELEVATED
    text_color = ColorScheme.TEXT_PRIMARY
    
    def on_hover(e):
        e.control.bgcolor = ColorScheme.ACCENT_SECONDARY if e.data == "true" and primary else ColorScheme.BG_HOVER
        e.control.update()
    
    content_row = ft.Row(
        [
            ft.Icon(icon, size=18, color=text_color) if icon else ft.Container(),
            ft.Text(text, size=Typography.BODY_SIZE, weight=ft.FontWeight.W_500, color=text_color)
        ],
        spacing=Spacing.SM,
        alignment=ft.MainAxisAlignment.CENTER,
    )
    
    return ft.Container(
        content=content_row,
        bgcolor=bg_color,
        border_radius=Spacing.RADIUS_MD,
        padding=ft.padding.symmetric(horizontal=Spacing.LG, vertical=Spacing.MD),
        width=width,
        height=height,
        alignment=ft.alignment.center,
        animate=ft.Animation(Animations.DURATION_FAST, Animations.CURVE_DEFAULT),
        on_hover=on_hover,
        on_click=on_click,
    )


def create_metric_card(
    title: str,
    value: str,
    icon: str,
    color: str = ColorScheme.INFO,
    trend: Optional[str] = None,  # "+12%" ou "-5%"
) -> ft.Container:
    """
    Cria card de métrica para dashboard.
    """
    trend_color = ColorScheme.SUCCESS if trend and trend.startswith("+") else ColorScheme.ERROR if trend else None
    
    content = ft.Column(
        [
            ft.Row(
                [
                    ft.Container(
                        content=ft.Icon(icon, color=color, size=20),
                        bgcolor=ColorScheme.with_alpha(color, 0.15),
                        border_radius=Spacing.RADIUS_SM,
                        padding=Spacing.SM,
                    ),
                    ft.Container(expand=True),
                    ft.Text(trend, size=Typography.CAPTION_SIZE, color=trend_color) if trend else ft.Container(),
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            ),
            ft.Container(height=Spacing.MD),
            ft.Text(
                value,
                size=Typography.H1_SIZE,
                weight=ft.FontWeight.BOLD,
                color=ColorScheme.TEXT_PRIMARY,
            ),
            ft.Text(
                title,
                size=Typography.CAPTION_SIZE,
                color=ColorScheme.TEXT_SECONDARY,
            ),
        ],
        spacing=Spacing.XS,
    )
    
    return create_premium_card(content, padding=Spacing.LG, expand=True)


def create_status_badge(
    text: str,
    color: str,
    icon: Optional[str] = None,
) -> ft.Container:
    """
    Cria badge de status colorido.
    """
    return ft.Container(
        content=ft.Row(
            [
                ft.Icon(icon, size=14, color=color) if icon else ft.Container(
                    width=8, height=8, border_radius=4, bgcolor=color
                ),
                ft.Text(text, size=Typography.LABEL_SIZE, color=color),
            ],
            spacing=Spacing.SM,
        ),
        padding=ft.padding.symmetric(horizontal=Spacing.MD, vertical=Spacing.XS),
        border_radius=Spacing.RADIUS_SM,
        bgcolor=ColorScheme.with_alpha(color, 0.15),
    )


def create_section_header(
    title: str,
    icon: Optional[str] = None,
    action: Optional[ft.Control] = None,
) -> ft.Container:
    """
    Cria cabeçalho de seção.
    """
    return ft.Container(
        content=ft.Row(
            [
                ft.Icon(icon, size=20, color=ColorScheme.ACCENT_PRIMARY) if icon else ft.Container(),
                ft.Text(title, size=Typography.H4_SIZE, weight=Typography.HEADING_WEIGHT),
                ft.Container(expand=True),
                action if action else ft.Container(),
            ],
            spacing=Spacing.SM,
        ),
        padding=ft.padding.only(bottom=Spacing.MD),
    )


def create_empty_state(
    icon: str,
    title: str,
    description: str,
    action_text: Optional[str] = None,
    on_action: Optional[callable] = None,
) -> ft.Container:
    """
    Cria estado vazio ilustrado.
    """
    controls = [
        ft.Container(
            content=ft.Icon(icon, size=64, color=ColorScheme.TEXT_MUTED),
            bgcolor=ColorScheme.BG_ELEVATED,
            border_radius=Spacing.RADIUS_FULL,
            padding=Spacing.XL,
        ),
        ft.Container(height=Spacing.LG),
        ft.Text(title, size=Typography.H4_SIZE, weight=ft.FontWeight.W_500, color=ColorScheme.TEXT_PRIMARY),
        ft.Text(description, size=Typography.BODY_SIZE, color=ColorScheme.TEXT_SECONDARY, text_align=ft.TextAlign.CENTER),
    ]
    
    if action_text and on_action:
        controls.append(ft.Container(height=Spacing.LG))
        controls.append(create_gradient_button(action_text, on_click=on_action))
    
    return ft.Container(
        content=ft.Column(
            controls,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=Spacing.SM,
        ),
        alignment=ft.alignment.center,
        expand=True,
    )


def create_loading_indicator(
    size: int = 32,
    color: str = ColorScheme.ACCENT_PRIMARY,
) -> ft.Container:
    """
    Cria indicador de carregamento.
    """
    return ft.Container(
        content=ft.ProgressRing(
            width=size,
            height=size,
            stroke_width=3,
            color=color,
        ),
        alignment=ft.alignment.center,
    )


def create_slot_container(
    slot_id: str,
    is_filled: bool = False,
    product_name: Optional[str] = None,
    product_price: Optional[float] = None,
    on_click: Optional[callable] = None,
    on_drop: Optional[callable] = None,
) -> ft.Container:
    """
    Cria container de slot para o Atelier.
    """
    bg_color = ColorScheme.SLOT_FILLED if is_filled else ColorScheme.SLOT_EMPTY
    
    def on_hover(e):
        if e.data == "true":
            e.control.bgcolor = ColorScheme.SLOT_HOVER
            e.control.border = ft.border.all(2, ColorScheme.ACCENT_PRIMARY)
        else:
            e.control.bgcolor = bg_color
            e.control.border = ft.border.all(1, ColorScheme.BORDER_DEFAULT)
        e.control.update()
    
    if is_filled:
        content = ft.Column(
            [
                ft.Text(slot_id, size=Typography.LABEL_SIZE, color=ColorScheme.TEXT_MUTED),
                ft.Container(
                    content=ft.Icon(ft.icons.INVENTORY_2, color=ColorScheme.TEXT_PRIMARY, size=24),
                    bgcolor=ColorScheme.BG_ELEVATED,
                    border_radius=Spacing.RADIUS_MD,
                    padding=Spacing.MD,
                    expand=True,
                    alignment=ft.alignment.center,
                ),
                ft.Text(
                    product_name[:18] + "..." if product_name and len(product_name) > 18 else product_name or "",
                    size=Typography.CAPTION_SIZE,
                    weight=ft.FontWeight.W_500,
                    color=ColorScheme.TEXT_PRIMARY,
                    max_lines=1,
                    overflow=ft.TextOverflow.ELLIPSIS,
                ),
                ft.Text(
                    f"R$ {product_price:.2f}" if product_price else "",
                    size=Typography.BODY_SIZE,
                    weight=ft.FontWeight.BOLD,
                    color=ColorScheme.SUCCESS,
                ),
            ],
            spacing=Spacing.XS,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )
    else:
        content = ft.Column(
            [
                ft.Text(slot_id, size=Typography.LABEL_SIZE, color=ColorScheme.TEXT_MUTED),
                ft.Container(
                    content=ft.Icon(ft.icons.ADD, color=ColorScheme.TEXT_MUTED, size=32),
                    expand=True,
                    alignment=ft.alignment.center,
                ),
                ft.Text("Arraste um produto", size=Typography.LABEL_SIZE, color=ColorScheme.TEXT_MUTED),
            ],
            spacing=Spacing.XS,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )
    
    slot = ft.Container(
        content=content,
        bgcolor=bg_color,
        border=ft.border.all(1, ColorScheme.BORDER_DEFAULT),
        border_radius=Spacing.RADIUS_LG,
        padding=Spacing.MD,
        on_hover=on_hover,
        on_click=on_click,
        animate=ft.Animation(Animations.DURATION_FAST, Animations.CURVE_DEFAULT),
    )
    
    # Wrap com DragTarget para aceitar drops
    return ft.DragTarget(
        group="products",
        content=slot,
        on_accept=on_drop,
        on_will_accept=lambda e: e.control.content.border == ft.border.all(2, ColorScheme.SUCCESS),
    )


def create_product_draggable(
    product: Dict[str, Any],
    on_click: Optional[callable] = None,
) -> ft.Draggable:
    """
    Cria card de produto arrastável para a Estante.
    """
    quality = product.get("quality", 0)
    quality_color = ColorScheme.get_quality_color(quality)
    
    def on_hover(e):
        e.control.bgcolor = ColorScheme.BG_HOVER if e.data == "true" else ColorScheme.BG_SECONDARY
        e.control.update()
    
    card = ft.Container(
        content=ft.Row(
            [
                ft.Container(
                    content=ft.Icon(ft.icons.IMAGE, color=ColorScheme.TEXT_PRIMARY, size=20),
                    bgcolor=quality_color,
                    border_radius=Spacing.RADIUS_SM,
                    width=48,
                    height=48,
                    alignment=ft.alignment.center,
                ),
                ft.Column(
                    [
                        ft.Text(
                            product.get("name", "")[:25],
                            size=Typography.BODY_SMALL_SIZE,
                            weight=ft.FontWeight.W_500,
                            color=ColorScheme.TEXT_PRIMARY,
                            max_lines=1,
                            overflow=ft.TextOverflow.ELLIPSIS,
                        ),
                        ft.Text(
                            f"R$ {product.get('price', 0):.2f}",
                            size=Typography.CAPTION_SIZE,
                            color=ColorScheme.SUCCESS,
                        ),
                    ],
                    spacing=2,
                    expand=True,
                ),
                ft.Icon(ft.icons.DRAG_INDICATOR, color=ColorScheme.TEXT_MUTED, size=16),
            ],
            spacing=Spacing.MD,
        ),
        padding=Spacing.MD,
        bgcolor=ColorScheme.BG_SECONDARY,
        border=ft.border.all(1, ColorScheme.BORDER_DEFAULT),
        border_radius=Spacing.RADIUS_MD,
        on_hover=on_hover,
        on_click=on_click,
        animate=ft.Animation(Animations.DURATION_FAST, Animations.CURVE_DEFAULT),
    )
    
    return ft.Draggable(
        group="products",
        content=card,
        content_feedback=ft.Container(
            content=ft.Text(product.get("name", "")[:15], size=12),
            bgcolor=ColorScheme.ACCENT_PRIMARY,
            padding=Spacing.MD,
            border_radius=Spacing.RADIUS_SM,
        ),
        data=product,
    )


# ==============================================================================
# TEMA GLOBAL FLET
# ==============================================================================

def get_flet_theme() -> ft.Theme:
    """
    Retorna tema Flet configurado.
    """
    return ft.Theme(
        color_scheme_seed=ColorScheme.ACCENT_PRIMARY,
        font_family=Typography.FONT_BODY,
        use_material3=True,
        visual_density=ft.VisualDensity.COMFORTABLE,
    )


def apply_page_theme(page: ft.Page):
    """
    Aplica tema à página Flet.
    """
    page.theme_mode = ft.ThemeMode.DARK
    page.bgcolor = ColorScheme.BG_PRIMARY
    page.padding = 0
    page.theme = get_flet_theme()
    
    # Fontes customizadas
    page.fonts = {
        "Inter": "/assets/fonts/Inter-Regular.ttf",
        "JetBrains Mono": "/assets/fonts/JetBrainsMono-Regular.ttf",
    }

"""
AutoTabloide AI - Widgets Reutilizáveis
========================================
Conforme Auditoria Industrial: Componentização (extração de widgets).
Componentes atômicos para uso em todas as views.
"""

from __future__ import annotations
import flet as ft
from typing import Optional, Callable, List, Dict, Any
from decimal import Decimal
import re

# Design System
try:
    from src.ui.design_system import ColorScheme, Typography, Spacing
except ImportError:
    # Fallbacks se design_system não disponível
    class ColorScheme:
        BG_PRIMARY = "#121212"
        BG_SECONDARY = "#1E1E1E"
        BG_ELEVATED = "#2D2D2D"
        ACCENT_PRIMARY = "#00BCD4"
        SUCCESS = "#4CAF50"
        WARNING = "#FF9800"
        ERROR = "#F44336"
        TEXT_PRIMARY = "#FFFFFF"
        TEXT_MUTED = "#9E9E9E"
        BORDER_DEFAULT = "#424242"


# ==============================================================================
# INPUT MASKING (Vol. VI - Conforme Auditoria)
# ==============================================================================

class MaskedTextField(ft.TextField):
    """
    Campo de texto com máscara de input.
    
    Previne "Garbage In, Garbage Out" filtrando entrada inválida.
    
    Máscaras disponíveis:
    - 'price': Apenas números e vírgula (ex: 19,90)
    - 'integer': Apenas números inteiros
    - 'barcode': Números de 8-14 dígitos
    - 'phone': Formato telefone BR
    - 'cep': Formato CEP (00000-000)
    - 'alphanumeric': Letras e números
    - 'custom': Regex customizado
    """
    
    MASKS = {
        'price': r'[0-9,.]',
        'integer': r'[0-9]',
        'barcode': r'[0-9]',
        'phone': r'[0-9()\-\s]',
        'cep': r'[0-9\-]',
        'alphanumeric': r'[a-zA-Z0-9\s]',
    }
    
    def __init__(
        self,
        mask: str = 'alphanumeric',
        custom_pattern: Optional[str] = None,
        max_length: Optional[int] = None,
        on_valid_change: Optional[Callable[[str], None]] = None,
        **kwargs
    ):
        """
        Args:
            mask: Tipo de máscara ('price', 'integer', etc)
            custom_pattern: Regex customizado (se mask='custom')
            max_length: Comprimento máximo
            on_valid_change: Callback quando valor válido muda
        """
        # Configura input_filter do Flet
        pattern = custom_pattern if mask == 'custom' else self.MASKS.get(mask, r'.')
        
        super().__init__(
            input_filter=ft.InputFilter(
                allow=True,
                regex_string=pattern,
                replacement_string=""
            ),
            max_length=max_length,
            **kwargs
        )
        
        self.mask_type = mask
        self._on_valid_change = on_valid_change
        self.on_change = self._handle_change
    
    def _handle_change(self, e):
        """Processa mudança com formatação automática."""
        value = e.control.value or ""
        
        # Formatação específica por tipo
        if self.mask_type == 'price':
            # Remove pontos extras, mantém apenas última vírgula
            value = self._format_price(value)
        elif self.mask_type == 'cep':
            value = self._format_cep(value)
        elif self.mask_type == 'phone':
            value = self._format_phone(value)
        
        if value != e.control.value:
            e.control.value = value
            e.control.update()
        
        if self._on_valid_change:
            self._on_valid_change(value)
    
    def _format_price(self, value: str) -> str:
        """Formata valor monetário."""
        # Remove tudo exceto números e vírgula
        clean = re.sub(r'[^\d,]', '', value)
        # Garante no máximo uma vírgula
        parts = clean.split(',')
        if len(parts) > 2:
            clean = parts[0] + ',' + ''.join(parts[1:])
        # Limita decimais a 2 dígitos
        if ',' in clean:
            int_part, dec_part = clean.split(',', 1)
            clean = int_part + ',' + dec_part[:2]
        return clean
    
    def _format_cep(self, value: str) -> str:
        """Formata CEP brasileiro."""
        digits = re.sub(r'\D', '', value)[:8]
        if len(digits) > 5:
            return f"{digits[:5]}-{digits[5:]}"
        return digits
    
    def _format_phone(self, value: str) -> str:
        """Formata telefone brasileiro."""
        digits = re.sub(r'\D', '', value)[:11]
        if len(digits) >= 11:
            return f"({digits[:2]}) {digits[2:7]}-{digits[7:]}"
        elif len(digits) >= 7:
            return f"({digits[:2]}) {digits[2:6]}-{digits[6:]}"
        elif len(digits) >= 2:
            return f"({digits[:2]}) {digits[2:]}"
        return digits
    
    def get_decimal_value(self) -> Optional[Decimal]:
        """Retorna valor como Decimal (para campos de preço)."""
        if self.mask_type != 'price' or not self.value:
            return None
        try:
            return Decimal(self.value.replace(',', '.'))
        except:
            return None


class PriceField(MaskedTextField):
    """Campo especializado para preços em Reais."""
    
    def __init__(
        self,
        label: str = "Preço",
        prefix_text: str = "R$ ",
        **kwargs
    ):
        super().__init__(
            mask='price',
            label=label,
            prefix_text=prefix_text,
            text_align=ft.TextAlign.RIGHT,
            keyboard_type=ft.KeyboardType.NUMBER,
            **kwargs
        )


class BarcodeField(MaskedTextField):
    """Campo especializado para código de barras."""
    
    def __init__(
        self,
        label: str = "Código de Barras",
        **kwargs
    ):
        super().__init__(
            mask='barcode',
            label=label,
            max_length=14,
            keyboard_type=ft.KeyboardType.NUMBER,
            prefix_icon=ft.icons.QR_CODE_SCANNER,
            **kwargs
        )


# ==============================================================================
# COMPONENTES DE CARD
# ==============================================================================

class ProductCard(ft.Container):
    """
    Card de produto reutilizável.
    
    Exibe: imagem, nome, preço, semáforo de qualidade.
    Suporta: seleção, hover, clique.
    """
    
    def __init__(
        self,
        product_id: int,
        name: str,
        price: float,
        price_ref: Optional[float] = None,
        image_hash: Optional[str] = None,
        quality_status: int = 0,
        is_selected: bool = False,
        on_click: Optional[Callable] = None,
        on_edit: Optional[Callable] = None,
        on_delete: Optional[Callable] = None,
        compact: bool = False,
    ):
        self.product_id = product_id
        self._is_selected = is_selected
        self._on_click = on_click
        
        # Cores do semáforo de qualidade
        quality_colors = {
            0: ColorScheme.ERROR,      # Crítico
            1: ColorScheme.WARNING,    # Incompleto
            2: "#FFC107",              # Atenção
            3: ColorScheme.SUCCESS,    # Perfeito
        }
        quality_color = quality_colors.get(quality_status, ColorScheme.TEXT_MUTED)
        
        # Conteúdo
        if compact:
            content = self._build_compact(name, price, quality_color)
        else:
            content = self._build_full(name, price, price_ref, quality_color, on_edit, on_delete)
        
        super().__init__(
            content=content,
            bgcolor=ColorScheme.BG_ELEVATED if is_selected else ColorScheme.BG_SECONDARY,
            border_radius=8,
            padding=10 if compact else 15,
            border=ft.border.all(
                2 if is_selected else 1,
                ColorScheme.ACCENT_PRIMARY if is_selected else ColorScheme.BORDER_DEFAULT
            ),
            on_click=self._handle_click,
            on_hover=self._handle_hover,
            animate=ft.animation.Animation(150, ft.AnimationCurve.EASE_OUT),
        )
    
    def _build_compact(self, name: str, price: float, quality_color: str) -> ft.Control:
        """Layout compacto para listas."""
        return ft.Row([
            ft.Container(
                width=8,
                height=8,
                bgcolor=quality_color,
                border_radius=4,
            ),
            ft.Text(
                name,
                size=12,
                weight=ft.FontWeight.W_500,
                expand=True,
                max_lines=1,
                overflow=ft.TextOverflow.ELLIPSIS,
            ),
            ft.Text(
                f"R$ {price:.2f}".replace('.', ','),
                size=12,
                color=ColorScheme.SUCCESS,
                weight=ft.FontWeight.BOLD,
            ),
        ], spacing=10)
    
    def _build_full(
        self, 
        name: str, 
        price: float, 
        price_ref: Optional[float],
        quality_color: str,
        on_edit: Optional[Callable],
        on_delete: Optional[Callable],
    ) -> ft.Control:
        """Layout completo com imagem e ações."""
        # Preço
        price_row = ft.Row([
            ft.Text("R$", size=14, color=ColorScheme.SUCCESS),
            ft.Text(
                f"{price:.2f}".replace('.', ','),
                size=24,
                weight=ft.FontWeight.BOLD,
                color=ColorScheme.SUCCESS,
            ),
        ], spacing=2, alignment=ft.MainAxisAlignment.CENTER)
        
        # Preço De (se houver desconto)
        price_de = None
        if price_ref and price_ref > price:
            price_de = ft.Text(
                f"De: R$ {price_ref:.2f}".replace('.', ','),
                size=11,
                color=ColorScheme.TEXT_MUTED,
                style=ft.TextStyle(decoration=ft.TextDecoration.LINE_THROUGH),
            )
        
        # Ações
        actions = ft.Row([
            ft.IconButton(
                ft.icons.EDIT_OUTLINED,
                icon_size=16,
                icon_color=ColorScheme.TEXT_MUTED,
                tooltip="Editar",
                on_click=lambda e: on_edit(self.product_id) if on_edit else None,
            ),
            ft.IconButton(
                ft.icons.DELETE_OUTLINE,
                icon_size=16,
                icon_color=ColorScheme.ERROR,
                tooltip="Remover",
                on_click=lambda e: on_delete(self.product_id) if on_delete else None,
            ),
        ], spacing=0, alignment=ft.MainAxisAlignment.END)
        
        return ft.Column([
            ft.Row([
                ft.Container(
                    width=10,
                    height=10,
                    bgcolor=quality_color,
                    border_radius=5,
                ),
                ft.Container(expand=True),
                ft.Text("•••", color=ColorScheme.TEXT_MUTED),
            ]),
            ft.Container(height=10),
            ft.Text(
                name,
                size=14,
                weight=ft.FontWeight.W_600,
                max_lines=2,
                overflow=ft.TextOverflow.ELLIPSIS,
            ),
            ft.Container(height=5),
            price_de if price_de else ft.Container(),
            price_row,
            ft.Container(height=5),
            actions if on_edit or on_delete else ft.Container(),
        ], spacing=0)
    
    def _handle_click(self, e):
        if self._on_click:
            self._on_click(self.product_id)
    
    def _handle_hover(self, e):
        if not self._is_selected:
            self.bgcolor = ColorScheme.BG_ELEVATED if e.data == "true" else ColorScheme.BG_SECONDARY
            self.update()


# ==============================================================================
# COMPONENTES DE FEEDBACK
# ==============================================================================

class LoadingOverlay(ft.Container):
    """
    Overlay de carregamento com spinner e mensagem.
    
    Uso:
        overlay = LoadingOverlay("Processando...")
        page.overlay.append(overlay)
        overlay.show()
        # ... operação
        overlay.hide()
    """
    
    def __init__(self, message: str = "Carregando..."):
        self._message = message
        
        super().__init__(
            content=ft.Column([
                ft.ProgressRing(
                    width=50,
                    height=50,
                    stroke_width=4,
                    color=ColorScheme.ACCENT_PRIMARY,
                ),
                ft.Container(height=15),
                ft.Text(
                    message,
                    size=14,
                    color=ColorScheme.TEXT_PRIMARY,
                    weight=ft.FontWeight.W_500,
                ),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER,
               alignment=ft.MainAxisAlignment.CENTER),
            bgcolor=ft.colors.with_opacity(0.8, ColorScheme.BG_PRIMARY),
            expand=True,
            visible=False,
            alignment=ft.alignment.center,
        )
    
    def show(self, message: Optional[str] = None) -> None:
        """Exibe overlay."""
        if message:
            self.content.controls[2].value = message
        self.visible = True
        self.update()
    
    def hide(self) -> None:
        """Oculta overlay."""
        self.visible = False
        self.update()
    
    def set_message(self, message: str) -> None:
        """Atualiza mensagem."""
        self.content.controls[2].value = message
        self.update()


class ConfirmDialog(ft.AlertDialog):
    """
    Diálogo de confirmação padronizado.
    
    Conforme Vol. VI: Foco no botão Cancelar para ações destrutivas.
    """
    
    def __init__(
        self,
        title: str,
        message: str,
        confirm_text: str = "Confirmar",
        cancel_text: str = "Cancelar",
        is_destructive: bool = False,
        on_confirm: Optional[Callable] = None,
        on_cancel: Optional[Callable] = None,
    ):
        self._on_confirm = on_confirm
        self._on_cancel = on_cancel
        
        confirm_color = ColorScheme.ERROR if is_destructive else ColorScheme.ACCENT_PRIMARY
        
        super().__init__(
            modal=True,
            title=ft.Text(title, weight=ft.FontWeight.BOLD),
            content=ft.Text(message, color=ColorScheme.TEXT_MUTED),
            actions=[
                ft.TextButton(
                    cancel_text,
                    on_click=self._handle_cancel,
                    autofocus=is_destructive,  # Foco em Cancelar se destrutivo
                ),
                ft.ElevatedButton(
                    confirm_text,
                    bgcolor=confirm_color,
                    color=ft.colors.WHITE,
                    on_click=self._handle_confirm,
                    autofocus=not is_destructive,
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
    
    def _handle_confirm(self, e):
        self.open = False
        self.update()
        if self._on_confirm:
            self._on_confirm()
    
    def _handle_cancel(self, e):
        self.open = False
        self.update()
        if self._on_cancel:
            self._on_cancel()


# ==============================================================================
# COMPONENTES DE STATUS
# ==============================================================================

class QualitySemaphore(ft.Container):
    """
    Indicador visual de qualidade de dados (semáforo).
    
    Estados:
    - 0: Vermelho - Crítico (dados faltando)
    - 1: Laranja - Incompleto (sem imagem)
    - 2: Amarelo - Atenção (imagem baixa qualidade)
    - 3: Verde - Perfeito (validado)
    """
    
    COLORS = {
        0: ("#F44336", "Dados críticos faltando"),
        1: ("#FF9800", "Produto incompleto"),
        2: ("#FFC107", "Atenção: qualidade baixa"),
        3: ("#4CAF50", "Produto validado"),
    }
    
    def __init__(
        self,
        status: int = 0,
        size: int = 12,
        show_tooltip: bool = True,
    ):
        color, tooltip_text = self.COLORS.get(status, self.COLORS[0])
        
        super().__init__(
            width=size,
            height=size,
            bgcolor=color,
            border_radius=size // 2,
            tooltip=tooltip_text if show_tooltip else None,
        )
    
    def set_status(self, status: int) -> None:
        """Atualiza estado do semáforo."""
        color, tooltip_text = self.COLORS.get(status, self.COLORS[0])
        self.bgcolor = color
        self.tooltip = tooltip_text
        self.update()


class ProgressIndicator(ft.Container):
    """
    Indicador de progresso customizado com porcentagem.
    """
    
    def __init__(
        self,
        value: float = 0.0,
        label: str = "",
        show_percentage: bool = True,
        height: int = 8,
    ):
        self._value = value
        self._label = label
        self._show_percentage = show_percentage
        
        self._bar = ft.ProgressBar(
            value=value,
            color=ColorScheme.ACCENT_PRIMARY,
            bgcolor=ColorScheme.BG_SECONDARY,
            bar_height=height,
        )
        
        self._text = ft.Text(
            f"{int(value * 100)}%",
            size=12,
            color=ColorScheme.TEXT_MUTED,
            visible=show_percentage,
        )
        
        self._label_text = ft.Text(
            label,
            size=12,
            color=ColorScheme.TEXT_PRIMARY,
            visible=bool(label),
        )
        
        super().__init__(
            content=ft.Column([
                ft.Row([
                    self._label_text,
                    ft.Container(expand=True),
                    self._text,
                ], visible=bool(label) or show_percentage),
                self._bar,
            ], spacing=5),
        )
    
    def set_progress(self, value: float, label: Optional[str] = None) -> None:
        """Atualiza progresso."""
        self._value = max(0.0, min(1.0, value))
        self._bar.value = self._value
        self._text.value = f"{int(self._value * 100)}%"
        
        if label is not None:
            self._label_text.value = label
            self._label_text.visible = bool(label)
        
        self.update()

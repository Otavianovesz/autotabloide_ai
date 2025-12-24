"""
AutoTabloide AI - Diff Visual Cofre
=====================================
Componente de diff visual para o Cofre.
Passo 52 do Checklist 100.

Mostra diferenças entre estados de produtos.
"""

import flet as ft
from typing import Optional, Dict, Any
from decimal import Decimal

from src.ui.design_system import DesignTokens


class DiffView(ft.Column):
    """
    Componente de Diff Visual.
    Passo 52 do Checklist - Diff visual no Cofre.
    
    Compara dois estados de um produto e destaca diferenças.
    """
    
    def __init__(self, old_data: Dict[str, Any], new_data: Dict[str, Any]):
        """
        Args:
            old_data: Dados antigos do produto
            new_data: Dados novos do produto
        """
        super().__init__()
        self.old_data = old_data
        self.new_data = new_data
        
        self._build_diff()
    
    def _build_diff(self) -> None:
        """Constrói visualização de diff."""
        # Cabeçalho
        header = ft.Row([
            ft.Text("Antes", weight=ft.FontWeight.BOLD, expand=1),
            ft.Text("Depois", weight=ft.FontWeight.BOLD, expand=1),
        ])
        
        self.controls = [header, ft.Divider()]
        
        # Compara campos
        all_keys = set(self.old_data.keys()) | set(self.new_data.keys())
        
        for key in sorted(all_keys):
            old_val = self.old_data.get(key, "—")
            new_val = self.new_data.get(key, "—")
            
            # Formata valores
            old_str = self._format_value(old_val)
            new_str = self._format_value(new_val)
            
            # Determina se mudou
            changed = old_val != new_val
            
            # Cores
            old_color = DesignTokens.ERROR if changed else DesignTokens.TEXT_SECONDARY
            new_color = DesignTokens.SUCCESS if changed else DesignTokens.TEXT_SECONDARY
            
            row = ft.Row([
                ft.Container(
                    content=ft.Column([
                        ft.Text(key, size=12, color=DesignTokens.TEXT_SECONDARY),
                        ft.Text(old_str, color=old_color),
                    ], spacing=2),
                    expand=1,
                    bgcolor=DesignTokens.ERROR_LIGHT if changed else None,
                    padding=5,
                    border_radius=4
                ),
                ft.Container(
                    content=ft.Column([
                        ft.Text(key, size=12, color=DesignTokens.TEXT_SECONDARY),
                        ft.Text(new_str, color=new_color),
                    ], spacing=2),
                    expand=1,
                    bgcolor=DesignTokens.SUCCESS_LIGHT if changed else None,
                    padding=5,
                    border_radius=4
                ),
            ], spacing=10)
            
            self.controls.append(row)
        
        self.spacing = 5
    
    def _format_value(self, value: Any) -> str:
        """Formata valor para exibição."""
        if value is None:
            return "—"
        if isinstance(value, (float, Decimal)):
            return f"R$ {value:.2f}"
        return str(value)


class DiffModal(ft.AlertDialog):
    """
    Modal de diff visual.
    """
    
    def __init__(
        self,
        title: str,
        old_data: Dict[str, Any],
        new_data: Dict[str, Any],
        on_confirm: Optional[callable] = None,
        on_cancel: Optional[callable] = None
    ):
        self.on_confirm = on_confirm
        self.on_cancel = on_cancel
        
        super().__init__(
            title=ft.Text(title),
            content=ft.Container(
                content=DiffView(old_data, new_data),
                width=500,
                height=400,
            ),
            actions=[
                ft.TextButton("Cancelar", on_click=self._handle_cancel),
                ft.ElevatedButton("Confirmar", on_click=self._handle_confirm),
            ],
            actions_alignment=ft.MainAxisAlignment.END
        )
    
    def _handle_confirm(self, e) -> None:
        if self.on_confirm:
            self.on_confirm()
        self.open = False
        self.update()
    
    def _handle_cancel(self, e) -> None:
        if self.on_cancel:
            self.on_cancel()
        self.open = False
        self.update()

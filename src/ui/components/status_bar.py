"""
AutoTabloide AI - Status Bar with Telemetry (Premium)
======================================================
Implementação conforme Vol. VI, Cap. 1.3.
Design premium com cores do design system.
"""

import flet as ft
import psutil
import asyncio
from typing import Optional, Callable
from datetime import datetime

from src.ui.design_system import ColorScheme, Typography, Spacing, Animations


class TelemetryData:
    """Container para dados de telemetria."""
    
    def __init__(self):
        self.cpu_percent: float = 0.0
        self.ram_percent: float = 0.0
        self.ram_used_gb: float = 0.0
        self.sentinel_status: str = "offline"
        self.db_status: str = "synced"
        self.last_update: datetime = datetime.now()
        self.pending_saves: int = 0


class StatusBarWithTelemetry(ft.UserControl):
    """
    Status bar com telemetria em tempo real.
    Design premium usando design system.
    """
    
    REFRESH_INTERVAL_MS = 2000
    
    def __init__(
        self,
        on_sentinel_click: Callable = None,
        on_db_click: Callable = None,
        **kwargs
    ):
        super().__init__(**kwargs)
        self.on_sentinel_click = on_sentinel_click
        self.on_db_click = on_db_click
        self._telemetry = TelemetryData()
        self._update_task: Optional[asyncio.Task] = None
        
        self._sentinel_badge = None
        self._cpu_text = None
        self._ram_text = None
        self._db_badge = None
        self._clock_text = None
        self._pending_badge = None
    
    def did_mount(self):
        """Inicia loop de atualização quando montado."""
        if self.page:
            self._update_task = self.page.run_task(self._telemetry_loop)
    
    def will_unmount(self):
        """Para loop quando desmontado."""
        if self._update_task:
            self._update_task.cancel()
    
    async def _telemetry_loop(self):
        """Loop de atualização de telemetria."""
        while True:
            try:
                await self._update_telemetry()
                await asyncio.sleep(self.REFRESH_INTERVAL_MS / 1000)
            except asyncio.CancelledError:
                break
            except Exception:
                await asyncio.sleep(5)
    
    async def _update_telemetry(self):
        """Atualiza dados de telemetria."""
        try:
            self._telemetry.cpu_percent = psutil.cpu_percent()
            mem = psutil.virtual_memory()
            self._telemetry.ram_percent = mem.percent
            self._telemetry.ram_used_gb = mem.used / (1024 ** 3)
            self._telemetry.last_update = datetime.now()
            
            if self._cpu_text:
                self._cpu_text.value = f"CPU: {self._telemetry.cpu_percent:.0f}%"
                color = self._get_usage_color(self._telemetry.cpu_percent)
                self._cpu_text.color = color
            
            if self._ram_text:
                self._ram_text.value = f"RAM: {self._telemetry.ram_percent:.0f}%"
                color = self._get_usage_color(self._telemetry.ram_percent)
                self._ram_text.color = color
            
            if self._clock_text:
                self._clock_text.value = self._telemetry.last_update.strftime("%H:%M")
            
            self.update()
            
        except Exception:
            pass
    
    def _get_usage_color(self, percent: float) -> str:
        """Retorna cor baseada no uso."""
        if percent < 50:
            return ColorScheme.SUCCESS
        elif percent < 75:
            return ColorScheme.WARNING
        return ColorScheme.ERROR
    
    def set_sentinel_status(self, status: str):
        """Atualiza status do Sentinel."""
        self._telemetry.sentinel_status = status
        if self._sentinel_badge:
            self._update_sentinel_badge()
            self.update()
    
    def set_db_status(self, status: str):
        """Atualiza status do DB."""
        self._telemetry.db_status = status
        if self._db_badge:
            self._update_db_badge()
            self.update()
    
    def set_pending_saves(self, count: int):
        """Atualiza contagem de saves pendentes."""
        self._telemetry.pending_saves = count
        if self._pending_badge:
            self._pending_badge.visible = count > 0
            self._pending_badge.content.value = str(count)
            self.update()
    
    def _update_sentinel_badge(self):
        """Atualiza visual do badge Sentinel."""
        status = self._telemetry.sentinel_status
        colors = {
            "online": ColorScheme.SUCCESS,
            "busy": ColorScheme.WARNING,
            "offline": ColorScheme.ERROR,
            "error": ColorScheme.ACCENT_TERTIARY
        }
        color = colors.get(status, ColorScheme.TEXT_MUTED)
        
        self._sentinel_badge.bgcolor = ColorScheme.with_alpha(color, 0.2)
        for c in self._sentinel_badge.content.controls:
            if isinstance(c, ft.Icon):
                c.color = color
    
    def _update_db_badge(self):
        """Atualiza visual do badge DB."""
        status = self._telemetry.db_status
        colors = {
            "synced": ColorScheme.SUCCESS,
            "syncing": ColorScheme.WARNING,
            "error": ColorScheme.ERROR
        }
        color = colors.get(status, ColorScheme.TEXT_MUTED)
        self._db_badge.bgcolor = ColorScheme.with_alpha(color, 0.2)
    
    def build(self):
        # Badge do Sentinel
        self._sentinel_badge = ft.Container(
            content=ft.Row([
                ft.Icon(ft.icons.SMART_TOY, size=14, color=ColorScheme.SUCCESS),
                ft.Text("IA", size=Typography.LABEL_SIZE, color=ColorScheme.TEXT_SECONDARY)
            ], spacing=Spacing.XS),
            padding=ft.padding.symmetric(horizontal=Spacing.SM, vertical=Spacing.XS),
            border_radius=Spacing.RADIUS_MD,
            bgcolor=ColorScheme.with_alpha(ColorScheme.SUCCESS, 0.2),
            on_click=lambda e: self.on_sentinel_click() if self.on_sentinel_click else None,
            animate=ft.Animation(Animations.DURATION_FAST, Animations.CURVE_DEFAULT),
        )
        
        # Badge de DB
        self._db_badge = ft.Container(
            content=ft.Row([
                ft.Icon(ft.icons.CLOUD_DONE, size=14, color=ColorScheme.SUCCESS),
                ft.Text("DB", size=Typography.LABEL_SIZE, color=ColorScheme.TEXT_SECONDARY)
            ], spacing=Spacing.XS),
            padding=ft.padding.symmetric(horizontal=Spacing.SM, vertical=Spacing.XS),
            border_radius=Spacing.RADIUS_MD,
            bgcolor=ColorScheme.with_alpha(ColorScheme.SUCCESS, 0.2),
            on_click=lambda e: self.on_db_click() if self.on_db_click else None,
            animate=ft.Animation(Animations.DURATION_FAST, Animations.CURVE_DEFAULT),
        )
        
        # Textos de telemetria
        self._cpu_text = ft.Text("CPU: --", size=Typography.LABEL_SIZE, color=ColorScheme.TEXT_MUTED)
        self._ram_text = ft.Text("RAM: --", size=Typography.LABEL_SIZE, color=ColorScheme.TEXT_MUTED)
        self._clock_text = ft.Text("--:--", size=Typography.LABEL_SIZE, color=ColorScheme.TEXT_MUTED)
        
        # Badge de pendentes
        self._pending_badge = ft.Container(
            content=ft.Text("0", size=10, color=ColorScheme.TEXT_PRIMARY),
            width=18,
            height=18,
            border_radius=9,
            bgcolor=ColorScheme.WARNING,
            alignment=ft.alignment.center,
            visible=False
        )
        
        return ft.Container(
            content=ft.Row([
                # Lado esquerdo - Status
                self._sentinel_badge,
                self._db_badge,
                self._pending_badge,
                
                # Spacer
                ft.Container(expand=True),
                
                # Lado direito - Telemetria
                self._cpu_text,
                ft.Text("│", size=Typography.LABEL_SIZE, color=ColorScheme.BORDER_DEFAULT),
                self._ram_text,
                ft.Text("│", size=Typography.LABEL_SIZE, color=ColorScheme.BORDER_DEFAULT),
                self._clock_text
            ], 
            spacing=Spacing.MD,
            vertical_alignment=ft.CrossAxisAlignment.CENTER),
            height=36,
            padding=ft.padding.symmetric(horizontal=Spacing.LG),
            bgcolor=ColorScheme.BG_SECONDARY,
            border=ft.border.only(top=ft.BorderSide(1, ColorScheme.BORDER_DEFAULT))
        )


def create_status_bar(**kwargs) -> StatusBarWithTelemetry:
    """Factory function para criar status bar."""
    return StatusBarWithTelemetry(**kwargs)

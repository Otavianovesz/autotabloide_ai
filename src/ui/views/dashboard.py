"""
AutoTabloide AI - Dashboard View (Premium)
==========================================
Visão executiva conforme Vol. VI, Cap. 1.
Design premium com glassmorphism e micro-animações.
"""

import flet as ft
import asyncio
from datetime import datetime
from typing import Optional

# Design System
from src.ui.design_system import (
    ColorScheme, Typography, Spacing, Animations,
    create_premium_card, create_metric_card, create_section_header,
    create_gradient_button, create_status_badge, create_empty_state,
    create_loading_indicator
)

# Industrial Components
from src.core.logging_config import get_logger
from src.ui.audio import play_success, play_error

logger = get_logger("DashboardView")


class DashboardView(ft.UserControl):
    """
    Tela inicial com visão executiva do sistema.
    Exibe métricas de produção, saúde do banco e status da IA.
    Auto-refresh a cada 30 segundos conforme Vol. VI.
    """
    
    REFRESH_INTERVAL_SECONDS = 30
    
    def __init__(self, page: ft.Page):
        super().__init__()
        self.page = page
        self._metrics = {}
        self._db_health = {}
        self._is_loading = True
        self._refresh_task = None

    def did_mount(self):
        """Carrega dados ao montar e inicia auto-refresh."""
        self.page.run_task(self._load_dashboard_data)
        self._refresh_task = self.page.run_task(self._auto_refresh_loop)

    def will_unmount(self):
        """Cancela auto-refresh ao desmontar."""
        if self._refresh_task:
            self._refresh_task.cancel()

    async def _auto_refresh_loop(self):
        """Loop de auto-refresh das métricas."""
        import asyncio
        while True:
            try:
                await asyncio.sleep(self.REFRESH_INTERVAL_SECONDS)
                await self._load_dashboard_data()
            except asyncio.CancelledError:
                break
            except Exception:
                await asyncio.sleep(5)

    async def _load_dashboard_data(self):
        """Carrega métricas e status de forma assíncrona."""
        try:
            from src.core.database import check_db_health, get_table_counts
            
            self._db_health = await check_db_health()
            self._metrics = await get_table_counts()
            
        except Exception as e:
            logger.error(f"Erro ao carregar dados: {e}")
            self._metrics = {"produtos": 0, "layouts": 0, "projetos": 0, "audit_logs": 0}
            self._db_health = {"status": "unknown", "journal_mode": "N/A", "integrity": "N/A"}
        
        finally:
            self._is_loading = False
            self.update()

    def _build_metric_card(
        self, 
        title: str, 
        value: str, 
        icon: str, 
        color: str = ColorScheme.INFO,
        trend: Optional[str] = None
    ) -> ft.Container:
        """Constrói um card de métrica premium."""
        trend_color = ColorScheme.SUCCESS if trend and trend.startswith("+") else ColorScheme.ERROR if trend else None
        
        def on_hover(e):
            if e.data == "true":
                e.control.bgcolor = ColorScheme.BG_HOVER
                e.control.scale = 1.02
            else:
                e.control.bgcolor = ColorScheme.BG_SECONDARY
                e.control.scale = 1.0
            e.control.update()
        
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
                ),
                ft.Container(height=Spacing.MD),
                ft.Text(
                    str(value),
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
        
        return ft.Container(
            content=content,
            padding=Spacing.LG,
            border_radius=Spacing.RADIUS_LG,
            bgcolor=ColorScheme.BG_SECONDARY,
            border=ft.border.all(1, ColorScheme.BORDER_DEFAULT),
            expand=True,
            on_hover=on_hover,
            animate=ft.Animation(Animations.DURATION_FAST, Animations.CURVE_DEFAULT),
            animate_scale=ft.Animation(Animations.DURATION_FAST, Animations.CURVE_DEFAULT),
            shadow=ft.BoxShadow(
                blur_radius=20, color="#00000022", offset=ft.Offset(0, 4)
            )
        )

    def _build_status_indicator(
        self, 
        label: str, 
        status: str, 
        is_ok: bool
    ) -> ft.Container:
        """Constrói um indicador de status visual."""
        color = ColorScheme.SUCCESS if is_ok else ColorScheme.ERROR
        icon = ft.icons.CHECK_CIRCLE if is_ok else ft.icons.ERROR
        
        return ft.Container(
            content=ft.Row(
                [
                    ft.Container(
                        width=4,
                        height=40,
                        bgcolor=color,
                        border_radius=2,
                    ),
                    ft.Container(width=Spacing.MD),
                    ft.Icon(icon, color=color, size=18),
                    ft.Container(width=Spacing.SM),
                    ft.Text(label, size=Typography.BODY_SIZE, expand=True),
                    ft.Text(status, size=Typography.BODY_SIZE, color=color, weight=ft.FontWeight.W_500)
                ],
            ),
            padding=ft.padding.symmetric(horizontal=Spacing.SM, vertical=Spacing.SM),
            bgcolor=ColorScheme.BG_ELEVATED,
            border_radius=Spacing.RADIUS_MD,
        )

    def _build_db_health_section(self) -> ft.Container:
        """Constrói seção de saúde do banco de dados."""
        db_status = self._db_health.get("status", "unknown")
        is_healthy = db_status == "healthy"
        
        journal_mode = self._db_health.get("journal_mode", "N/A")
        integrity = self._db_health.get("integrity", "N/A")
        db_size = self._db_health.get("db_size_bytes", 0)
        wal_size = self._db_health.get("wal_size_bytes", 0)
        
        # Formata tamanhos
        db_size_str = f"{db_size / 1024:.1f} KB" if db_size else "N/A"
        wal_size_str = f"{wal_size / 1024:.1f} KB" if wal_size else "0 KB"
        
        content = ft.Column(
            [
                ft.Row(
                    [
                        ft.Icon(ft.icons.STORAGE, color=ColorScheme.ACCENT_PRIMARY, size=22),
                        ft.Container(width=Spacing.SM),
                        ft.Text("Banco de Dados", size=Typography.H4_SIZE, weight=ft.FontWeight.W_600),
                        ft.Container(expand=True),
                        create_status_badge(
                            db_status.upper(),
                            ColorScheme.SUCCESS if is_healthy else ColorScheme.ERROR,
                            ft.icons.CHECK_CIRCLE if is_healthy else ft.icons.ERROR
                        )
                    ]
                ),
                ft.Divider(height=Spacing.LG, color=ColorScheme.BORDER_DEFAULT),
                self._build_status_indicator(
                    "Modo Journal", 
                    journal_mode.upper(), 
                    journal_mode.lower() == "wal"
                ),
                self._build_status_indicator(
                    "Integridade", 
                    integrity.upper(), 
                    integrity.lower() == "ok"
                ),
                ft.Container(height=Spacing.SM),
                ft.Row(
                    [
                        ft.Column([
                            ft.Text("Tamanho", size=Typography.LABEL_SIZE, color=ColorScheme.TEXT_MUTED),
                            ft.Text(db_size_str, size=Typography.BODY_SIZE, weight=ft.FontWeight.W_500),
                        ], spacing=2),
                        ft.Container(width=Spacing.XL),
                        ft.Column([
                            ft.Text("WAL", size=Typography.LABEL_SIZE, color=ColorScheme.TEXT_MUTED),
                            ft.Text(wal_size_str, size=Typography.BODY_SIZE, weight=ft.FontWeight.W_500),
                        ], spacing=2),
                    ]
                )
            ],
            spacing=Spacing.SM,
        )
        
        return ft.Container(
            content=content,
            padding=Spacing.LG,
            bgcolor=ColorScheme.BG_SECONDARY,
            border=ft.border.all(1, ColorScheme.BORDER_DEFAULT),
            border_radius=Spacing.RADIUS_LG,
            expand=True,
            shadow=ft.BoxShadow(blur_radius=20, color="#00000022", offset=ft.Offset(0, 4))
        )

    def _build_quick_actions(self) -> ft.Container:
        """Constrói seção de ações rápidas."""
        
        def on_button_hover(e):
            if e.data == "true":
                e.control.bgcolor = ColorScheme.BG_HOVER
            else:
                e.control.bgcolor = ColorScheme.BG_ELEVATED
            e.control.update()
        
        def create_action_button(text: str, icon: str, color: str, on_click=None):
            return ft.Container(
                content=ft.Row([
                    ft.Container(
                        content=ft.Icon(icon, color=color, size=18),
                        bgcolor=ColorScheme.with_alpha(color, 0.15),
                        border_radius=Spacing.RADIUS_SM,
                        padding=Spacing.SM,
                    ),
                    ft.Container(width=Spacing.MD),
                    ft.Text(text, size=Typography.BODY_SIZE, expand=True),
                    ft.Icon(ft.icons.ARROW_FORWARD_IOS, size=14, color=ColorScheme.TEXT_MUTED),
                ]),
                padding=Spacing.MD,
                bgcolor=ColorScheme.BG_ELEVATED,
                border_radius=Spacing.RADIUS_MD,
                on_hover=on_button_hover,
                on_click=on_click,
                animate=ft.Animation(Animations.DURATION_FAST, Animations.CURVE_DEFAULT),
            )
        
        content = ft.Column(
            [
                ft.Row([
                    ft.Icon(ft.icons.FLASH_ON, color=ColorScheme.WARNING, size=22),
                    ft.Container(width=Spacing.SM),
                    ft.Text("Ações Rápidas", size=Typography.H4_SIZE, weight=ft.FontWeight.W_600),
                ]),
                ft.Divider(height=Spacing.LG, color=ColorScheme.BORDER_DEFAULT),
                create_action_button("Novo Projeto", ft.icons.ADD_CIRCLE, ColorScheme.ACCENT_PRIMARY),
                create_action_button("Importar Dados", ft.icons.UPLOAD_FILE, ColorScheme.INFO),
                create_action_button("Criar Backup", ft.icons.BACKUP, ColorScheme.SUCCESS, 
                                     on_click=self._create_backup),
            ],
            spacing=Spacing.SM,
        )
        
        return ft.Container(
            content=content,
            padding=Spacing.LG,
            bgcolor=ColorScheme.BG_SECONDARY,
            border=ft.border.all(1, ColorScheme.BORDER_DEFAULT),
            border_radius=Spacing.RADIUS_LG,
            expand=True,
            shadow=ft.BoxShadow(blur_radius=20, color="#00000022", offset=ft.Offset(0, 4))
        )

    def _navigate_to(self, index: int):
        """Navega para outra tela."""
        # TODO: Implementar navegação via callback
        pass

    def _create_backup(self, e):
        """Cria backup do sistema."""
        self.page.snack_bar = ft.SnackBar(
            content=ft.Row([
                ft.ProgressRing(width=16, height=16, stroke_width=2, color=ColorScheme.INFO),
                ft.Container(width=Spacing.MD),
                ft.Text("Criando backup...")
            ]),
            bgcolor=ColorScheme.BG_ELEVATED
        )
        self.page.snack_bar.open = True
        self.page.update()
        
        self.page.run_task(self._async_backup)

    async def _async_backup(self):
        """Executa backup de forma assíncrona."""
        try:
            from src.core.database import vacuum_and_checkpoint
            await vacuum_and_checkpoint()
            
            self.page.snack_bar = ft.SnackBar(
                content=ft.Row([
                    ft.Icon(ft.icons.CHECK_CIRCLE, color=ColorScheme.SUCCESS, size=18),
                    ft.Container(width=Spacing.SM),
                    ft.Text("Backup concluído com sucesso!")
                ]),
                bgcolor=ColorScheme.BG_ELEVATED
            )
            self.page.snack_bar.open = True
            self.page.update()
            
        except Exception as e:
            self.page.snack_bar = ft.SnackBar(
                content=ft.Row([
                    ft.Icon(ft.icons.ERROR, color=ColorScheme.ERROR, size=18),
                    ft.Container(width=Spacing.SM),
                    ft.Text(f"Erro: {e}")
                ]),
                bgcolor=ColorScheme.BG_ELEVATED
            )
            self.page.snack_bar.open = True
            self.page.update()

    def build(self):
        if self._is_loading:
            return ft.Container(
                content=ft.Column([
                    create_loading_indicator(48, ColorScheme.ACCENT_PRIMARY),
                    ft.Container(height=Spacing.LG),
                    ft.Text("Carregando dashboard...", color=ColorScheme.TEXT_SECONDARY),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=Spacing.MD),
                alignment=ft.alignment.center,
                expand=True,
            )
        
        # Métricas principais
        produtos_count = self._metrics.get("produtos", 0)
        layouts_count = self._metrics.get("layouts", 0)
        projetos_count = self._metrics.get("projetos", 0)
        audit_count = self._metrics.get("audit_logs", 0)
        
        metrics_row = ft.Row(
            [
                self._build_metric_card(
                    "Produtos", 
                    str(produtos_count), 
                    ft.icons.INVENTORY_2,
                    ColorScheme.SUCCESS
                ),
                self._build_metric_card(
                    "Layouts", 
                    str(layouts_count), 
                    ft.icons.GRID_VIEW,
                    ColorScheme.ACCENT_PRIMARY
                ),
                self._build_metric_card(
                    "Projetos", 
                    str(projetos_count), 
                    ft.icons.FOLDER,
                    ColorScheme.WARNING
                ),
                self._build_metric_card(
                    "Eventos", 
                    str(audit_count), 
                    ft.icons.HISTORY,
                    ColorScheme.TEXT_MUTED
                ),
            ],
            spacing=Spacing.LG,
        )
        
        # Segunda linha: Saúde do sistema + Ações rápidas
        info_row = ft.Row(
            [
                ft.Container(
                    content=self._build_db_health_section(),
                    expand=2
                ),
                ft.Container(
                    content=self._build_quick_actions(),
                    expand=1
                )
            ],
            spacing=Spacing.LG,
        )
        
        # Header premium
        header = ft.Container(
            content=ft.Row(
                [
                    ft.Column(
                        [
                            ft.Text(
                                "AutoTabloide AI", 
                                size=Typography.DISPLAY_SIZE, 
                                weight=ft.FontWeight.BOLD,
                                color=ColorScheme.TEXT_PRIMARY,
                            ),
                            ft.Row([
                                ft.Container(
                                    width=8, height=8, border_radius=4,
                                    bgcolor=ColorScheme.SUCCESS,
                                ),
                                ft.Container(width=Spacing.SM),
                                ft.Text(
                                    f"Dashboard • {datetime.now().strftime('%d/%m/%Y %H:%M')}",
                                    size=Typography.BODY_SIZE,
                                    color=ColorScheme.TEXT_SECONDARY,
                                )
                            ]),
                        ],
                        spacing=Spacing.SM,
                    )
                ]
            ),
            padding=ft.padding.only(bottom=Spacing.XL),
        )
        
        return ft.Container(
            content=ft.Column(
                [
                    header,
                    metrics_row,
                    ft.Container(height=Spacing.LG),
                    info_row,
                ],
                scroll=ft.ScrollMode.AUTO,
                expand=True,
            ),
            padding=Spacing.SECTION_PADDING,
            expand=True,
        )

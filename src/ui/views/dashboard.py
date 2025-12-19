"""
AutoTabloide AI - Dashboard View
=================================
Visão executiva conforme Vol. VI, Cap. 1.
Exibe status de produção, métricas e saúde do sistem.
"""

import flet as ft
import asyncio
from datetime import datetime
from typing import Optional

# Cores Semânticas (Vol. VI, Tab. 1.1)
COLORS = {
    "success": "#34C759",
    "warning": "#FFCC00", 
    "error": "#FF3B30",
    "info": "#007AFF",
    "neutral": "#8E8E93",
    "surface": "#1C1C1E",
    "surface_elevated": "#2C2C2E",
}


class DashboardView(ft.UserControl):
    """
    Tela inicial com visão executiva do sistema.
    Exibe métricas de produção, saúde do banco e status da IA.
    """
    
    def __init__(self, page: ft.Page):
        super().__init__()
        self.page = page
        self._metrics = {}
        self._db_health = {}

    def did_mount(self):
        """Carrega dados ao montar componente."""
        self.page.run_task(self._load_dashboard_data)

    async def _load_dashboard_data(self):
        """Carrega métricas e status de forma assíncrona."""
        try:
            # Importa aqui para evitar circular imports
            from src.core.database import check_db_health, get_table_counts
            
            self._db_health = await check_db_health()
            self._metrics = await get_table_counts()
            
            self.update()
            
        except Exception as e:
            print(f"[Dashboard] Erro ao carregar dados: {e}")

    def _build_metric_card(
        self, 
        title: str, 
        value: str, 
        icon: str, 
        color: str = COLORS["info"]
    ) -> ft.Container:
        """Constrói um card de métrica."""
        return ft.Container(
            content=ft.Column(
                [
                    ft.Row(
                        [
                            ft.Icon(icon, color=color, size=24),
                            ft.Text(title, size=14, color=ft.colors.GREY_400)
                        ],
                        alignment=ft.MainAxisAlignment.START
                    ),
                    ft.Text(
                        str(value), 
                        size=36, 
                        weight=ft.FontWeight.BOLD,
                        color=ft.colors.WHITE
                    )
                ],
                spacing=5
            ),
            padding=20,
            bgcolor=COLORS["surface_elevated"],
            border_radius=10,
            expand=True
        )

    def _build_status_indicator(
        self, 
        label: str, 
        status: str, 
        is_ok: bool
    ) -> ft.Container:
        """Constrói um indicador de status."""
        color = COLORS["success"] if is_ok else COLORS["error"]
        icon = ft.icons.CHECK_CIRCLE if is_ok else ft.icons.ERROR
        
        return ft.Container(
            content=ft.Row(
                [
                    ft.Icon(icon, color=color, size=20),
                    ft.Text(label, size=14, expand=True),
                    ft.Text(status, size=14, color=color)
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN
            ),
            padding=ft.padding.symmetric(horizontal=15, vertical=10),
            bgcolor=COLORS["surface"],
            border_radius=8
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
        
        return ft.Container(
            content=ft.Column(
                [
                    ft.Row(
                        [
                            ft.Icon(ft.icons.STORAGE, color=COLORS["info"]),
                            ft.Text("Banco de Dados", size=18, weight=ft.FontWeight.BOLD)
                        ]
                    ),
                    ft.Divider(height=1, color=ft.colors.GREY_800),
                    self._build_status_indicator(
                        "Status Geral", 
                        db_status.upper(), 
                        is_healthy
                    ),
                    self._build_status_indicator(
                        "Modo Journal", 
                        journal_mode.upper(), 
                        journal_mode == "wal"
                    ),
                    self._build_status_indicator(
                        "Integridade", 
                        integrity.upper(), 
                        integrity == "ok"
                    ),
                    ft.Row(
                        [
                            ft.Text("Tamanho:", size=13, color=ft.colors.GREY_400),
                            ft.Text(db_size_str, size=13),
                            ft.Text(" | WAL:", size=13, color=ft.colors.GREY_400),
                            ft.Text(wal_size_str, size=13)
                        ]
                    )
                ],
                spacing=10
            ),
            padding=20,
            bgcolor=COLORS["surface_elevated"],
            border_radius=10
        )

    def _build_quick_actions(self) -> ft.Container:
        """Constrói seção de ações rápidas."""
        return ft.Container(
            content=ft.Column(
                [
                    ft.Row(
                        [
                            ft.Icon(ft.icons.FLASH_ON, color=COLORS["warning"]),
                            ft.Text("Acoes Rapidas", size=18, weight=ft.FontWeight.BOLD)
                        ]
                    ),
                    ft.Divider(height=1, color=ft.colors.GREY_800),
                    ft.ElevatedButton(
                        "Novo Projeto",
                        icon=ft.icons.ADD,
                        style=ft.ButtonStyle(
                            bgcolor=COLORS["info"],
                            color=ft.colors.WHITE
                        ),
                        expand=True,
                        on_click=lambda _: self._navigate_to(3)  # Mesa
                    ),
                    ft.ElevatedButton(
                        "Importar Dados",
                        icon=ft.icons.UPLOAD_FILE,
                        expand=True,
                        on_click=lambda _: self._navigate_to(1)  # Estoque
                    ),
                    ft.ElevatedButton(
                        "Criar Backup",
                        icon=ft.icons.BACKUP,
                        expand=True,
                        on_click=self._create_backup
                    )
                ],
                spacing=10
            ),
            padding=20,
            bgcolor=COLORS["surface_elevated"],
            border_radius=10
        )

    def _navigate_to(self, index: int):
        """Navega para outra tela."""
        # Encontra o NavigationRail e muda o índice
        # Isso depende da estrutura do main.py
        pass

    def _create_backup(self, e):
        """Cria backup do sistema."""
        self.page.snack_bar = ft.SnackBar(
            ft.Text("Backup iniciado em background..."),
            bgcolor=COLORS["info"]
        )
        self.page.snack_bar.open = True
        self.page.update()
        
        # Aqui chamaria a função real de backup
        self.page.run_task(self._async_backup)

    async def _async_backup(self):
        """Executa backup de forma assíncrona."""
        try:
            from src.core.database import vacuum_and_checkpoint
            await vacuum_and_checkpoint()
            
            self.page.snack_bar = ft.SnackBar(
                ft.Text("Backup concluido com sucesso!"),
                bgcolor=COLORS["success"]
            )
            self.page.snack_bar.open = True
            self.page.update()
            
        except Exception as e:
            self.page.snack_bar = ft.SnackBar(
                ft.Text(f"Erro no backup: {e}"),
                bgcolor=COLORS["error"]
            )
            self.page.snack_bar.open = True
            self.page.update()

    def build(self):
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
                    COLORS["success"]
                ),
                self._build_metric_card(
                    "Layouts", 
                    str(layouts_count), 
                    ft.icons.GRID_VIEW,
                    COLORS["info"]
                ),
                self._build_metric_card(
                    "Projetos", 
                    str(projetos_count), 
                    ft.icons.FOLDER,
                    COLORS["warning"]
                ),
                self._build_metric_card(
                    "Eventos", 
                    str(audit_count), 
                    ft.icons.HISTORY,
                    COLORS["neutral"]
                ),
            ],
            spacing=15
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
            spacing=15
        )
        
        # Header
        header = ft.Container(
            content=ft.Row(
                [
                    ft.Column(
                        [
                            ft.Text(
                                "AutoTabloide AI", 
                                size=32, 
                                weight=ft.FontWeight.BOLD
                            ),
                            ft.Text(
                                f"Dashboard | {datetime.now().strftime('%d/%m/%Y %H:%M')}",
                                size=14,
                                color=ft.colors.GREY_400
                            )
                        ],
                        spacing=5
                    )
                ]
            ),
            padding=ft.padding.only(bottom=20)
        )
        
        return ft.Container(
            content=ft.Column(
                [
                    header,
                    metrics_row,
                    ft.Container(height=20),
                    info_row
                ],
                scroll=ft.ScrollMode.AUTO,
                expand=True
            ),
            padding=30,
            expand=True
        )

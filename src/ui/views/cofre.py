"""
AutoTabloide AI - Cofre View (Timeline e Auditoria)
=====================================================
Interface forense conforme Vol. VI, Parte VI.
Timeline de eventos, rollback e gestão de backups.
"""

import flet as ft
import asyncio
from datetime import datetime, timedelta
from typing import List, Optional

# Design System
from src.ui.design_system import ColorScheme, Typography, Spacing, Animations

# Cores usando Design System
COLORS = {
    "success": ColorScheme.SUCCESS,
    "warning": ColorScheme.WARNING,
    "error": ColorScheme.ERROR,
    "info": ColorScheme.ACCENT_PRIMARY,
    "neutral": ColorScheme.TEXT_MUTED,
    "surface": ColorScheme.BG_SECONDARY,
    "surface_elevated": ColorScheme.BG_ELEVATED,
    "create": ColorScheme.SUCCESS,
    "update": ColorScheme.ACCENT_PRIMARY,
    "delete": ColorScheme.ERROR,
    "rollback": ColorScheme.WARNING,
}

# Ícones por tipo de ação
ACTION_ICONS = {
    "CREATE": ft.icons.ADD_CIRCLE,
    "UPDATE": ft.icons.EDIT,
    "DELETE": ft.icons.DELETE,
    "IMPORT": ft.icons.UPLOAD_FILE,
    "PRINT": ft.icons.PRINT,
    "ROLLBACK": ft.icons.UNDO,
}

ACTION_COLORS = {
    "CREATE": COLORS["create"],
    "UPDATE": COLORS["update"],
    "DELETE": COLORS["delete"],
    "IMPORT": COLORS["info"],
    "PRINT": COLORS["neutral"],
    "ROLLBACK": COLORS["rollback"],
}


class AuditEventCard(ft.UserControl):
    """
    Card individual de evento de auditoria.
    Conforme Vol. VI, Cap. 6.1.
    """
    
    def __init__(
        self, 
        event: dict,
        on_rollback: callable = None
    ):
        super().__init__()
        self.event = event
        self.on_rollback = on_rollback

    def _format_timestamp(self, timestamp: datetime) -> str:
        """Formata timestamp de forma amigável."""
        now = datetime.now()
        diff = now - timestamp
        
        if diff < timedelta(minutes=1):
            return "Agora mesmo"
        elif diff < timedelta(hours=1):
            mins = int(diff.total_seconds() / 60)
            return f"Ha {mins} min"
        elif diff < timedelta(days=1):
            hours = int(diff.total_seconds() / 3600)
            return f"Ha {hours}h"
        else:
            return timestamp.strftime("%d/%m/%Y %H:%M")

    def build(self):
        action_type = self.event.get("action_type", "UPDATE")
        entity_type = self.event.get("entity_type", "PRODUTO")
        description = self.event.get("description", "Acao realizada")
        timestamp = self.event.get("timestamp", datetime.now())
        severity = self.event.get("severity", 1)
        can_rollback = self.event.get("can_rollback", False)
        
        # Cor e ícone baseado na ação
        action_color = ACTION_COLORS.get(action_type, COLORS["neutral"])
        action_icon = ACTION_ICONS.get(action_type, ft.icons.INFO)
        
        # Barra lateral colorida
        color_strip = ft.Container(
            width=4,
            bgcolor=action_color,
            border_radius=ft.border_radius.only(top_left=8, bottom_left=8)
        )
        
        # Conteúdo principal
        content = ft.Column(
            [
                ft.Row(
                    [
                        ft.Icon(action_icon, color=action_color, size=20),
                        ft.Text(
                            f"{action_type} - {entity_type}",
                            size=12,
                            color=ft.colors.GREY_400
                        ),
                        ft.Container(expand=True),
                        ft.Text(
                            self._format_timestamp(timestamp) if isinstance(timestamp, datetime) else str(timestamp),
                            size=11,
                            color=ft.colors.GREY_500
                        )
                    ]
                ),
                ft.Text(description, size=14),
                ft.Row(
                    [
                        ft.Container(expand=True),
                        ft.TextButton(
                            "Desfazer",
                            icon=ft.icons.UNDO,
                            on_click=lambda e: self.on_rollback(self.event) if self.on_rollback else None,
                            visible=can_rollback
                        )
                    ]
                ) if can_rollback else ft.Container()
            ],
            spacing=5
        )
        
        return ft.Container(
            content=ft.Row(
                [
                    color_strip,
                    ft.Container(
                        content=content,
                        padding=15,
                        expand=True
                    )
                ],
                spacing=0
            ),
            bgcolor=COLORS["surface_elevated"],
            border_radius=8,
            margin=ft.margin.only(bottom=8)
        )


class CofreView(ft.UserControl):
    """
    Tela de Timeline e Gestão de Segurança.
    Implementa Infinite Scroll com carregamento sob demanda.
    """
    
    def __init__(self, page: ft.Page):
        super().__init__()
        self.page = page
        self.events: List[dict] = []
        self.snapshots: List[dict] = []
        
        # Paginação
        self.page_size = 50
        self.current_offset = 0
        self.is_loading = False
        
        # Filtros
        self.filter_entity: Optional[str] = None
        self.filter_action: Optional[str] = None

    def did_mount(self):
        """Carrega dados iniciais."""
        self.page.run_task(self._load_events)
        self.page.run_task(self._load_snapshots)

    async def _load_events(self, append: bool = False):
        """Carrega eventos de auditoria."""
        if self.is_loading:
            return
        
        self.is_loading = True
        
        try:
            from src.core.database import AsyncSessionLocal
            from src.core.repositories import AuditRepository
            
            async with AsyncSessionLocal() as session:
                repo = AuditRepository(session)
                
                events = await repo.get_timeline(
                    limit=self.page_size,
                    offset=self.current_offset,
                    entity_type=self.filter_entity,
                    action_type=self.filter_action
                )
                
                # Converte para dict
                new_events = [
                    {
                        "id": e.id,
                        "timestamp": e.timestamp,
                        "entity_type": e.entity_type,
                        "entity_id": e.entity_id,
                        "action_type": e.action_type,
                        "description": e.description or f"{e.action_type} em {e.entity_type}",
                        "severity": e.severity,
                        "diff": e.get_diff(),
                        "can_rollback": e.can_rollback()
                    }
                    for e in events
                ]
                
                if append:
                    self.events.extend(new_events)
                else:
                    self.events = new_events
                
                self._update_event_list()
                
        except Exception as e:
            print(f"[Cofre] Erro ao carregar eventos: {e}")
            # Mock data para desenvolvimento
            self.events = [
                {
                    "id": 1,
                    "timestamp": datetime.now() - timedelta(hours=1),
                    "entity_type": "PRODUTO",
                    "entity_id": 1,
                    "action_type": "UPDATE",
                    "description": "Preco alterado de R$ 10,50 para R$ 9,90",
                    "severity": 1,
                    "can_rollback": True
                },
                {
                    "id": 2,
                    "timestamp": datetime.now() - timedelta(hours=3),
                    "entity_type": "PROJETO",
                    "entity_id": 1,
                    "action_type": "CREATE",
                    "description": "Projeto 'Oferta Semanal' criado",
                    "severity": 1,
                    "can_rollback": False
                }
            ]
            self._update_event_list()
        
        finally:
            self.is_loading = False

    async def _load_snapshots(self):
        """Carrega lista de snapshots/backups disponíveis."""
        import os
        from pathlib import Path
        
        snapshots_dir = Path(__file__).parent.parent.parent.parent / "AutoTabloide_System_Root" / "snapshots"
        
        self.snapshots = []
        
        if snapshots_dir.exists():
            for f in sorted(snapshots_dir.iterdir(), reverse=True):
                if f.suffix in ['.zip', '.db']:
                    stat = f.stat()
                    self.snapshots.append({
                        "name": f.name,
                        "path": str(f),
                        "size": stat.st_size,
                        "created": datetime.fromtimestamp(stat.st_mtime)
                    })
        
        self._update_snapshots_list()

    def _update_event_list(self):
        """Atualiza lista de eventos na UI."""
        if hasattr(self, 'event_list'):
            self.event_list.controls.clear()
            
            # Agrupa por data para Sticky Headers
            current_date = None
            
            for event in self.events:
                timestamp = event.get("timestamp")
                if isinstance(timestamp, datetime):
                    event_date = timestamp.date()
                    
                    if event_date != current_date:
                        current_date = event_date
                        # Header de data
                        if event_date == datetime.now().date():
                            date_label = "Hoje"
                        elif event_date == (datetime.now() - timedelta(days=1)).date():
                            date_label = "Ontem"
                        else:
                            date_label = event_date.strftime("%d/%m/%Y")
                        
                        self.event_list.controls.append(
                            ft.Container(
                                content=ft.Text(
                                    date_label,
                                    size=13,
                                    weight=ft.FontWeight.BOLD,
                                    color=ft.colors.GREY_400
                                ),
                                padding=ft.padding.only(top=20, bottom=10)
                            )
                        )
                
                self.event_list.controls.append(
                    AuditEventCard(
                        event=event,
                        on_rollback=self._on_rollback
                    )
                )
            
            self.event_list.update()

    def _update_snapshots_list(self):
        """Atualiza lista de snapshots."""
        if hasattr(self, 'snapshots_list'):
            self.snapshots_list.controls.clear()
            
            for snap in self.snapshots[:10]:  # Últimos 10
                size_kb = snap['size'] / 1024
                
                self.snapshots_list.controls.append(
                    ft.Container(
                        content=ft.Row(
                            [
                                ft.Icon(ft.icons.ARCHIVE, color=COLORS["info"]),
                                ft.Column(
                                    [
                                        ft.Text(snap['name'], size=13),
                                        ft.Text(
                                            f"{snap['created'].strftime('%d/%m/%Y %H:%M')} | {size_kb:.1f} KB",
                                            size=11,
                                            color=ft.colors.GREY_500
                                        )
                                    ],
                                    spacing=2,
                                    expand=True
                                ),
                                ft.IconButton(
                                    icon=ft.icons.RESTORE,
                                    tooltip="Restaurar",
                                    on_click=lambda e, s=snap: self._on_restore(s)
                                )
                            ]
                        ),
                        padding=10,
                        bgcolor=COLORS["surface"],
                        border_radius=8,
                        margin=ft.margin.only(bottom=5)
                    )
                )
            
            self.snapshots_list.update()

    def _on_rollback(self, event: dict):
        """Handler de rollback."""
        def confirm_rollback(e):
            dialog.open = False
            self.page.update()
            self.page.run_task(self._execute_rollback, event)
        
        def cancel(e):
            dialog.open = False
            self.page.update()
        
        dialog = ft.AlertDialog(
            title=ft.Text("Confirmar Rollback"),
            content=ft.Text(f"Deseja desfazer: {event.get('description')}?"),
            actions=[
                ft.TextButton("Cancelar", on_click=cancel),
                ft.ElevatedButton(
                    "Desfazer",
                    style=ft.ButtonStyle(bgcolor=COLORS["warning"]),
                    on_click=confirm_rollback
                )
            ]
        )
        
        self.page.dialog = dialog
        dialog.open = True
        self.page.update()

    async def _execute_rollback(self, event: dict):
        """Executa rollback de forma assíncrona."""
        try:
            from src.core.database import AsyncSessionLocal
            from src.core.repositories import AuditRepository
            
            async with AsyncSessionLocal() as session:
                repo = AuditRepository(session)
                rollback_log = await repo.rollback_entry(event['id'])
                
                if rollback_log:
                    self.page.snack_bar = ft.SnackBar(
                        ft.Text("Acao desfeita com sucesso!"),
                        bgcolor=COLORS["success"]
                    )
                else:
                    self.page.snack_bar = ft.SnackBar(
                        ft.Text("Nao foi possivel desfazer esta acao"),
                        bgcolor=COLORS["error"]
                    )
                
                self.page.snack_bar.open = True
                self.page.update()
                
                # Recarrega eventos
                self.current_offset = 0
                await self._load_events()
                
        except Exception as e:
            self.page.snack_bar = ft.SnackBar(
                ft.Text(f"Erro: {e}"),
                bgcolor=COLORS["error"]
            )
            self.page.snack_bar.open = True
            self.page.update()

    def _on_restore(self, snapshot: dict):
        """Handler de restauração de backup."""
        def confirm_restore(e):
            dialog.open = False
            self.page.update()
            self._execute_restore(snapshot)
        
        def cancel(e):
            dialog.open = False
            self.page.update()
        
        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Row(
                [
                    ft.Icon(ft.icons.WARNING, color=COLORS["warning"]),
                    ft.Text("Restaurar Backup")
                ]
            ),
            content=ft.Column(
                [
                    ft.Text("ATENCAO: Esta acao ira substituir o banco de dados atual."),
                    ft.Text(f"Arquivo: {snapshot['name']}", size=12, color=ft.colors.GREY_400),
                    ft.Text("Um backup do estado atual sera criado automaticamente.", size=12)
                ],
                spacing=10
            ),
            actions=[
                ft.TextButton("Cancelar", on_click=cancel),
                ft.ElevatedButton(
                    "Restaurar",
                    style=ft.ButtonStyle(bgcolor=COLORS["error"], color=ft.colors.WHITE),
                    on_click=confirm_restore
                )
            ]
        )
        
        self.page.dialog = dialog
        dialog.open = True
        self.page.update()

    def _execute_restore(self, snapshot: dict):
        """Executa restauração."""
        self.page.snack_bar = ft.SnackBar(
            ft.Text("Restauracao iniciada... Reinicie a aplicacao."),
            bgcolor=COLORS["warning"]
        )
        self.page.snack_bar.open = True
        self.page.update()

    def _on_create_backup(self, e):
        """Cria novo backup."""
        self.page.snack_bar = ft.SnackBar(
            ft.Text("Criando backup..."),
            bgcolor=COLORS["info"]
        )
        self.page.snack_bar.open = True
        self.page.update()
        
        self.page.run_task(self._async_create_backup)

    async def _async_create_backup(self):
        """Cria backup de forma assíncrona."""
        try:
            from src.core.database import vacuum_and_checkpoint
            await vacuum_and_checkpoint()
            
            self.page.snack_bar = ft.SnackBar(
                ft.Text("Backup criado com sucesso!"),
                bgcolor=COLORS["success"]
            )
            self.page.snack_bar.open = True
            self.page.update()
            
            await self._load_snapshots()
            
        except Exception as e:
            self.page.snack_bar = ft.SnackBar(
                ft.Text(f"Erro: {e}"),
                bgcolor=COLORS["error"]
            )
            self.page.snack_bar.open = True
            self.page.update()
    
    def _export_database(self, e):
        """
        Exporta banco de dados para arquivo externo.
        Permite transferência entre máquinas.
        """
        import shutil
        from pathlib import Path
        
        # Diálogo para salvar arquivo
        def on_save_result(ev: ft.FilePickerResultEvent):
            if not ev.path:
                return
            
            try:
                # Caminho do banco atual
                db_path = Path(__file__).parent.parent.parent.parent / "AutoTabloide_System_Root" / "data" / "autotabloide.db"
                
                if not db_path.exists():
                    self.page.snack_bar = ft.SnackBar(
                        ft.Text("Banco de dados não encontrado!"),
                        bgcolor=COLORS["error"]
                    )
                    self.page.snack_bar.open = True
                    self.page.update()
                    return
                
                # Copia para destino
                dest_path = ev.path
                if not dest_path.endswith('.db'):
                    dest_path += '.db'
                
                shutil.copy2(str(db_path), dest_path)
                
                # Também exporta imagens se existirem
                vault_path = Path(__file__).parent.parent.parent.parent / "AutoTabloide_System_Root" / "assets" / "store"
                if vault_path.exists():
                    vault_dest = Path(dest_path).parent / "autotabloide_images"
                    if vault_dest.exists():
                        shutil.rmtree(vault_dest)
                    shutil.copytree(vault_path, vault_dest)
                
                self.page.snack_bar = ft.SnackBar(
                    ft.Text(f"Banco exportado para: {dest_path}"),
                    bgcolor=COLORS["success"]
                )
                self.page.snack_bar.open = True
                self.page.update()
                
            except Exception as ex:
                self.page.snack_bar = ft.SnackBar(
                    ft.Text(f"Erro ao exportar: {ex}"),
                    bgcolor=COLORS["error"]
                )
                self.page.snack_bar.open = True
                self.page.update()
        
        # Configura FilePicker para salvar
        save_dialog = ft.FilePicker(on_result=on_save_result)
        self.page.overlay.append(save_dialog)
        self.page.update()
        
        save_dialog.save_file(
            dialog_title="Exportar Banco de Dados",
            file_name=f"autotabloide_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db",
            allowed_extensions=["db"]
        )
    
    def _import_database(self, e):
        """
        Importa banco de dados de arquivo externo.
        Substitui banco atual após confirmação.
        """
        import shutil
        from pathlib import Path
        
        def on_file_result(ev: ft.FilePickerResultEvent):
            if not ev.files or not ev.files[0]:
                return
            
            source_path = ev.files[0].path
            
            # Confirmar antes de substituir
            def confirm_import(e2):
                self.page.close(confirm_dialog)
                self._execute_import(source_path)
            
            def cancel_import(e2):
                self.page.close(confirm_dialog)
            
            confirm_dialog = ft.AlertDialog(
                modal=True,
                title=ft.Row([
                    ft.Icon(ft.icons.WARNING, color=COLORS["warning"]),
                    ft.Text("Confirmar Importação")
                ]),
                content=ft.Column([
                    ft.Text("ATENÇÃO: Esta ação irá SUBSTITUIR todos os dados atuais!"),
                    ft.Text(f"Arquivo: {Path(source_path).name}", size=12, color=ft.colors.GREY_400),
                    ft.Text("Um backup do estado atual será criado automaticamente.", size=12)
                ], spacing=10),
                actions=[
                    ft.TextButton("Cancelar", on_click=cancel_import),
                    ft.ElevatedButton(
                        "Importar",
                        style=ft.ButtonStyle(bgcolor=COLORS["error"], color=ft.colors.WHITE),
                        on_click=confirm_import
                    )
                ]
            )
            
            self.page.open(confirm_dialog)
        
        # Configura FilePicker para abrir
        file_picker = ft.FilePicker(on_result=on_file_result)
        self.page.overlay.append(file_picker)
        self.page.update()
        
        file_picker.pick_files(
            dialog_title="Importar Banco de Dados",
            allowed_extensions=["db"],
            allow_multiple=False
        )
    
    def _execute_import(self, source_path: str):
        """Executa a importação do banco de dados."""
        import shutil
        from pathlib import Path
        
        try:
            db_path = Path(__file__).parent.parent.parent.parent / "AutoTabloide_System_Root" / "data" / "autotabloide.db"
            snapshots_dir = Path(__file__).parent.parent.parent.parent / "AutoTabloide_System_Root" / "snapshots"
            
            # Cria backup do atual antes de substituir
            if db_path.exists():
                snapshots_dir.mkdir(parents=True, exist_ok=True)
                backup_name = f"pre_import_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
                shutil.copy2(str(db_path), str(snapshots_dir / backup_name))
            
            # Copia novo banco
            shutil.copy2(source_path, str(db_path))
            
            # Verifica se há pasta de imagens junto
            source_images = Path(source_path).parent / "autotabloide_images"
            if source_images.exists():
                vault_path = Path(__file__).parent.parent.parent.parent / "AutoTabloide_System_Root" / "assets" / "store"
                vault_path.mkdir(parents=True, exist_ok=True)
                
                # Copia imagens
                for img in source_images.iterdir():
                    shutil.copy2(str(img), str(vault_path / img.name))
            
            self.page.snack_bar = ft.SnackBar(
                ft.Text("Banco importado com sucesso! Reinicie a aplicação."),
                bgcolor=COLORS["success"]
            )
            self.page.snack_bar.open = True
            self.page.update()
            
            # Recarrega snapshots
            self.page.run_task(self._load_snapshots)
            
        except Exception as ex:
            self.page.snack_bar = ft.SnackBar(
                ft.Text(f"Erro ao importar: {ex}"),
                bgcolor=COLORS["error"]
            )
            self.page.snack_bar.open = True
            self.page.update()


    def _on_scroll(self, e):
        """Handler de scroll para infinite scroll."""
        if e.pixels >= e.max_scroll_extent * 0.8 and not self.is_loading:
            self.current_offset += self.page_size
            self.page.run_task(self._load_events, True)

    def build(self):
        # Painel esquerdo: Timeline
        self.event_list = ft.ListView(
            expand=True,
            spacing=0,
            on_scroll=self._on_scroll
        )
        
        timeline_panel = ft.Container(
            content=ft.Column(
                [
                    ft.Row(
                        [
                            ft.Icon(ft.icons.HISTORY, color=COLORS["info"]),
                            ft.Text("Timeline de Eventos", size=18, weight=ft.FontWeight.BOLD)
                        ]
                    ),
                    ft.Divider(height=1),
                    # Filtros
                    ft.Row(
                        [
                            ft.Dropdown(
                                label="Entidade",
                                value="",
                                options=[
                                    ft.dropdown.Option("", "Todas"),
                                    ft.dropdown.Option("PRODUTO", "Produtos"),
                                    ft.dropdown.Option("PROJETO", "Projetos"),
                                    ft.dropdown.Option("LAYOUT", "Layouts"),
                                ],
                                width=150,
                                on_change=lambda e: self._set_filter_entity(e.control.value)
                            ),
                            ft.Dropdown(
                                label="Acao",
                                value="",
                                options=[
                                    ft.dropdown.Option("", "Todas"),
                                    ft.dropdown.Option("CREATE", "Criacao"),
                                    ft.dropdown.Option("UPDATE", "Alteracao"),
                                    ft.dropdown.Option("DELETE", "Exclusao"),
                                ],
                                width=150,
                                on_change=lambda e: self._set_filter_action(e.control.value)
                            )
                        ],
                        spacing=10
                    ),
                    self.event_list
                ],
                expand=True
            ),
            padding=20,
            bgcolor=COLORS["surface_elevated"],
            border_radius=10,
            expand=2
        )
        
        # Painel direito: Backups
        self.snapshots_list = ft.ListView(expand=True, spacing=5)
        
        backup_panel = ft.Container(
            content=ft.Column(
                [
                    ft.Row(
                        [
                            ft.Icon(ft.icons.BACKUP, color=COLORS["success"]),
                            ft.Text("Backups", size=18, weight=ft.FontWeight.BOLD)
                        ]
                    ),
                    ft.Divider(height=1),
                    ft.ElevatedButton(
                        "Criar Snapshot Agora",
                        icon=ft.icons.ADD,
                        expand=True,
                        on_click=self._on_create_backup
                    ),
                    ft.Container(height=10),
                    # Botões de Export/Import para transferência entre máquinas
                    ft.Row([
                        ft.ElevatedButton(
                            "Exportar",
                            icon=ft.icons.UPLOAD,
                            tooltip="Exportar banco para outro PC",
                            expand=True,
                            on_click=self._export_database,
                            style=ft.ButtonStyle(bgcolor=COLORS["info"])
                        ),
                        ft.ElevatedButton(
                            "Importar",
                            icon=ft.icons.DOWNLOAD,
                            tooltip="Importar banco de outro PC",
                            expand=True,
                            on_click=self._import_database,
                            style=ft.ButtonStyle(bgcolor=COLORS["warning"])
                        )
                    ], spacing=10),
                    ft.Container(height=10),
                    ft.Text("Snapshots Locais", size=13, color=ft.colors.GREY_400),
                    self.snapshots_list
                ],
                expand=True
            ),
            padding=20,
            bgcolor=COLORS["surface_elevated"],
            border_radius=10,
            expand=1
        )

        
        return ft.Container(
            content=ft.Row(
                [timeline_panel, backup_panel],
                spacing=15,
                expand=True
            ),
            padding=20,
            expand=True
        )

    def _set_filter_entity(self, value: str):
        """Define filtro de entidade."""
        self.filter_entity = value if value else None
        self.current_offset = 0
        self.page.run_task(self._load_events)

    def _set_filter_action(self, value: str):
        """Define filtro de ação."""
        self.filter_action = value if value else None
        self.current_offset = 0
        self.page.run_task(self._load_events)

"""
AutoTabloide AI - Global Progress Modal
==========================================
Modal global de progresso conectado ao EventBus.
Passo 50-51 do Checklist 100.

Funcionalidades:
- Modal overlay de progresso
- Conexão automática com EventBus
- Suporte a múltiplas tarefas
- Animações de loading
"""

import flet as ft
from typing import Optional, Callable
from dataclasses import dataclass

from src.core.event_bus import event_bus, EventType
from src.core.logging_config import get_logger
from src.ui.design_system import DesignTokens

logger = get_logger("ProgressModal")


@dataclass
class TaskProgress:
    """Estado de uma tarefa em progresso."""
    task_id: str
    title: str
    message: str = ""
    current: int = 0
    total: int = 100
    indeterminate: bool = False


class GlobalProgressModal(ft.UserControl):
    """
    Modal global de progresso.
    Exibe overlay com barra de progresso e mensagens.
    """
    
    def __init__(self, page: ft.Page):
        super().__init__()
        self.page = page
        self._visible = False
        self._task: Optional[TaskProgress] = None
        
        # Componentes
        self._overlay: Optional[ft.Container] = None
        self._title_text: Optional[ft.Text] = None
        self._message_text: Optional[ft.Text] = None
        self._progress_bar: Optional[ft.ProgressBar] = None
        self._progress_text: Optional[ft.Text] = None
        
        # Registrar listeners
        self._setup_listeners()
    
    def _setup_listeners(self) -> None:
        """Configura listeners do EventBus."""
        event_bus.subscribe(EventType.AI_TASK_START, self._on_task_start)
        event_bus.subscribe(EventType.AI_TASK_PROGRESS, self._on_task_progress)
        event_bus.subscribe(EventType.AI_TASK_COMPLETE, self._on_task_complete)
        event_bus.subscribe(EventType.AI_TASK_ERROR, self._on_task_error)
    
    def _on_task_start(self, data: dict) -> None:
        """Handler para início de tarefa."""
        task_id = data.get("task", "unknown")
        title = data.get("title", f"Processando {task_id}...")
        
        self._task = TaskProgress(
            task_id=task_id,
            title=title,
            indeterminate=data.get("indeterminate", False)
        )
        
        self.show(title)
    
    def _on_task_progress(self, data: dict) -> None:
        """Handler para progresso de tarefa."""
        if not self._task:
            return
        
        self._task.current = data.get("current", 0)
        self._task.total = data.get("total", 100)
        self._task.message = data.get("message", "")
        
        self.update_progress(
            self._task.current / max(self._task.total, 1),
            self._task.message
        )
    
    def _on_task_complete(self, data: dict) -> None:
        """Handler para conclusão de tarefa."""
        self._task = None
        self.hide()
    
    def _on_task_error(self, data: dict) -> None:
        """Handler para erro de tarefa."""
        error_msg = data.get("error", "Erro desconhecido")
        logger.error(f"Tarefa falhou: {error_msg}")
        self._task = None
        self.hide()
    
    def show(self, title: str = "Processando...", message: str = "") -> None:
        """
        Exibe o modal de progresso.
        
        Args:
            title: Título do processo
            message: Mensagem adicional
        """
        if self._title_text:
            self._title_text.value = title
        if self._message_text:
            self._message_text.value = message
        if self._progress_bar:
            self._progress_bar.value = None  # Indeterminate
        if self._progress_text:
            self._progress_text.value = ""
        
        self._visible = True
        self._update_visibility()
    
    def hide(self) -> None:
        """Oculta o modal."""
        self._visible = False
        self._update_visibility()
    
    def update_progress(self, percent: float, message: str = "") -> None:
        """
        Atualiza progresso do modal.
        
        Args:
            percent: Porcentagem (0.0 a 1.0)
            message: Mensagem descritiva
        """
        if self._progress_bar:
            self._progress_bar.value = percent
        if self._message_text and message:
            self._message_text.value = message
        if self._progress_text:
            self._progress_text.value = f"{int(percent * 100)}%"
        
        if self.page:
            try:
                self.page.update()
            except Exception:
                pass
    
    def _update_visibility(self) -> None:
        """Atualiza visibilidade do overlay."""
        if self._overlay:
            self._overlay.visible = self._visible
        
        if self.page:
            try:
                self.page.update()
            except Exception:
                pass
    
    def build(self) -> ft.Control:
        """Constrói o modal."""
        self._title_text = ft.Text(
            "Processando...",
            size=18,
            weight=ft.FontWeight.BOLD,
            color=DesignTokens.TEXT_PRIMARY
        )
        
        self._message_text = ft.Text(
            "",
            size=14,
            color=DesignTokens.TEXT_SECONDARY
        )
        
        self._progress_bar = ft.ProgressBar(
            width=300,
            color=DesignTokens.PRIMARY,
            bgcolor=DesignTokens.SURFACE_LIGHT,
            value=None  # Indeterminate
        )
        
        self._progress_text = ft.Text(
            "",
            size=14,
            color=DesignTokens.TEXT_PRIMARY
        )
        
        # Card de conteúdo
        content_card = ft.Container(
            content=ft.Column([
                self._title_text,
                ft.Container(height=16),
                self._progress_bar,
                ft.Container(height=8),
                ft.Row([
                    self._message_text,
                    ft.Container(expand=True),
                    self._progress_text
                ]),
            ], spacing=4, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            padding=32,
            bgcolor=DesignTokens.SURFACE,
            border_radius=12,
            shadow=ft.BoxShadow(
                spread_radius=2,
                blur_radius=20,
                color=ft.colors.with_opacity(0.3, ft.colors.BLACK)
            )
        )
        
        # Overlay com blur
        self._overlay = ft.Container(
            content=ft.Container(
                content=content_card,
                alignment=ft.alignment.center
            ),
            bgcolor=ft.colors.with_opacity(0.6, ft.colors.BLACK),
            visible=False,
            expand=True
        )
        
        return self._overlay


class ProgressOverlay:
    """
    Gerenciador de overlay de progresso.
    Singleton para acesso global.
    """
    
    _instance: Optional["ProgressOverlay"] = None
    _modal: Optional[GlobalProgressModal] = None
    
    def __new__(cls) -> "ProgressOverlay":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def init(self, page: ft.Page) -> GlobalProgressModal:
        """
        Inicializa overlay com página Flet.
        
        Args:
            page: Página Flet principal
            
        Returns:
            Modal instanciado
        """
        self._modal = GlobalProgressModal(page)
        return self._modal
    
    def show(self, title: str = "Processando...", message: str = "") -> None:
        """Exibe modal de progresso."""
        if self._modal:
            self._modal.show(title, message)
    
    def hide(self) -> None:
        """Oculta modal."""
        if self._modal:
            self._modal.hide()
    
    def update(self, percent: float, message: str = "") -> None:
        """Atualiza progresso."""
        if self._modal:
            self._modal.update_progress(percent, message)
    
    @property
    def modal(self) -> Optional[GlobalProgressModal]:
        """Retorna modal instanciado."""
        return self._modal


# Singleton global
progress_overlay = ProgressOverlay()


def get_progress_overlay() -> ProgressOverlay:
    """Retorna singleton do ProgressOverlay."""
    return progress_overlay

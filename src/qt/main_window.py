"""
AutoTabloide AI - Main Window (PySide6)
========================================
Janela principal com navegação, views e integração de serviços.
"""

import sys
import logging
from typing import Optional
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QStackedWidget, QPushButton, QFrame, QLabel, QStatusBar,
    QSizePolicy, QSpacerItem, QApplication, QMessageBox
)
from PySide6.QtCore import Qt, Signal, Slot, QTimer
from PySide6.QtGui import QCloseEvent

from .widgets.dashboard import DashboardWidget
from .widgets.estoque import EstoqueWidget
from .widgets.atelier import AtelierWidget
from .widgets.factory import FactoryWidget
from .widgets.cofre import CofreWidget
from .widgets.settings import SettingsWidget


class NavButton(QPushButton):
    """Botão de navegação da sidebar."""
    
    def __init__(self, text: str, icon_text: str = "", parent=None):
        super().__init__(f"{icon_text}  {text}" if icon_text else text, parent)
        self.setCheckable(True)
        self.setProperty("class", "nav-button")
        self.setCursor(Qt.PointingHandCursor)
        self.setMinimumHeight(44)


class Sidebar(QFrame):
    """Sidebar de navegação estilo Adobe."""
    
    navigation_changed = Signal(int)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("sidebar")
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 16, 0, 16)
        layout.setSpacing(4)
        
        # Logo/Título - using CSS class instead of inline style
        title = QLabel("AutoTabloide AI")
        title.setAlignment(Qt.AlignCenter)
        title.setProperty("class", "title-sidebar")
        layout.addWidget(title)
        
        # Version label - using CSS class
        version = QLabel("v2.0.0 Qt Edition")
        version.setAlignment(Qt.AlignCenter)
        version.setProperty("class", "version-label")
        layout.addWidget(version)
        
        layout.addSpacing(8)
        
        # Botões de navegação
        self.buttons = []
        nav_items = [
            ("Dashboard", "📊", 0),
            ("Estoque", "📦", 1),
            ("Ateliê", "🎨", 2),
            ("Fábrica", "🏭", 3),
            ("Cofre", "🔒", 4),
            ("Configurações", "⚙️", 5),
        ]
        
        for text, icon, index in nav_items:
            btn = NavButton(text, icon)
            btn.clicked.connect(lambda checked, idx=index: self._on_nav_click(idx))
            self.buttons.append(btn)
            layout.addWidget(btn)
        
        # Spacer
        layout.addSpacerItem(QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding))
        
        # Status do Sentinel - using CSS class
        self.sentinel_indicator = QLabel("● Sentinel: Ativo")
        self.sentinel_indicator.setAlignment(Qt.AlignCenter)
        self.sentinel_indicator.setProperty("class", "status-ok")
        layout.addWidget(self.sentinel_indicator)
        
        # Seleciona primeiro botão
        self.buttons[0].setChecked(True)
    
    def _on_nav_click(self, index: int) -> None:
        """Atualiza seleção e emite sinal."""
        for i, btn in enumerate(self.buttons):
            btn.setChecked(i == index)
        self.navigation_changed.emit(index)
    
    def set_sentinel_status(self, active: bool) -> None:
        """Atualiza status do Sentinel using CSS classes."""
        if active:
            self.sentinel_indicator.setText("● Sentinel: Ativo")
            self.sentinel_indicator.setProperty("class", "status-ok")
        else:
            self.sentinel_indicator.setText("● Sentinel: Offline")
            self.sentinel_indicator.setProperty("class", "status-error")
        # Force style refresh
        self.sentinel_indicator.style().unpolish(self.sentinel_indicator)
        self.sentinel_indicator.style().polish(self.sentinel_indicator)


class PlaceholderWidget(QWidget):
    """Widget placeholder para views não implementadas."""
    
    def __init__(self, name: str, description: str = "", parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        
        # Ícone grande - using CSS class
        icon_map = {
            "Estoque": "📦",
            "Ateliê": "🎨",
            "Fábrica": "🏭",
            "Cofre": "🔒",
            "Configurações": "⚙️"
        }
        icon = QLabel(icon_map.get(name, "🔧"))
        icon.setProperty("class", "icon-lg")
        icon.setAlignment(Qt.AlignCenter)
        layout.addWidget(icon)
        
        title = QLabel(name)
        title.setProperty("class", "title-lg")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        subtitle = QLabel(description or "Módulo em desenvolvimento...")
        subtitle.setProperty("class", "subtitle-muted")
        subtitle.setAlignment(Qt.AlignCenter)
        layout.addWidget(subtitle)


class MainWindow(QMainWindow):
    """Janela principal do AutoTabloide AI (Qt Edition)."""
    
    # Signals
    closing = Signal()
    
    # Version
    VERSION = "2.0.0"
    
    def __init__(self, container=None):
        super().__init__()
        
        # Injeção de Dependência
        self.container = container
        
        # Project state tracking
        self._current_project_name: str = None
        self._is_dirty: bool = False
        
        # Configuração da janela
        self._update_window_title()
        self.setMinimumSize(1200, 800)
        self.resize(1400, 900)
        
        # Logger
        self._logger = logging.getLogger("AutoTabloide.MainWindow")
        
        # Setup
        self._setup_ui()
        self._setup_status_bar()
        self._setup_timers()
        self._setup_sentinel_integration()
    
    def _update_window_title(self) -> None:
        """Update window title with project name and dirty indicator."""
        dirty_marker = " *" if self._is_dirty else ""
        project = f" - {self._current_project_name}" if self._current_project_name else " - Sem Projeto"
        self.setWindowTitle(f"AutoTabloide AI v{self.VERSION}{project}{dirty_marker}")
    
    def set_project_name(self, name: str) -> None:
        """Set current project name and update title."""
        self._current_project_name = name
        self._update_window_title()
    
    def set_dirty(self, dirty: bool) -> None:
        """Mark project as having unsaved changes."""
        if self._is_dirty != dirty:
            self._is_dirty = dirty
            self._update_window_title()
    
    def is_dirty(self) -> bool:
        """Check if project has unsaved changes."""
        return self._is_dirty
    
    def _setup_ui(self) -> None:
        """Configura interface principal."""
        # Widget central
        central = QWidget()
        self.setCentralWidget(central)
        
        # Layout horizontal: Sidebar + Content
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Sidebar
        self.sidebar = Sidebar()
        self.sidebar.navigation_changed.connect(self._on_navigation)
        main_layout.addWidget(self.sidebar)
        
        # Content Area (Stacked Widget)
        content_frame = QFrame()
        content_frame.setObjectName("content-area")
        content_layout = QVBoxLayout(content_frame)
        content_layout.setContentsMargins(0, 0, 0, 0)
        
        self.stack = QStackedWidget()
        content_layout.addWidget(self.stack)
        
        main_layout.addWidget(content_frame, 1)  # stretch=1 para expandir
        
        # Adiciona views
        self._create_views()
    
    def _create_views(self) -> None:
        """Cria e adiciona todas as views ao stack."""
        # Dashboard (implementado)
        self.dashboard = DashboardWidget(container=self.container)
        self.dashboard.navigate_to.connect(self._navigate_to_view)
        self.stack.addWidget(self.dashboard)
        
        # Estoque (implementado)
        self.estoque = EstoqueWidget(container=self.container)
        self.stack.addWidget(self.estoque)
        
        # Ateliê (implementado)
        self.atelier = AtelierWidget(container=self.container)
        self.stack.addWidget(self.atelier)
        
        # Fábrica (implementado)
        self.factory = FactoryWidget(container=self.container)
        self.stack.addWidget(self.factory)
        
        # Cofre (implementado)
        self.cofre = CofreWidget(container=self.container)
        self.stack.addWidget(self.cofre)
        
        # Configurações (implementado)
        self.settings = SettingsWidget(container=self.container)
        self.stack.addWidget(self.settings)
    
    @Slot(int)
    def _navigate_to_view(self, index: int) -> None:
        """Navega para uma view específica."""
        self.sidebar._on_nav_click(index)
        self.stack.setCurrentIndex(index)
    
    def _setup_status_bar(self) -> None:
        """Configura barra de status."""
        status = self.statusBar()
        status.showMessage("Pronto")
        
        # Widget de progresso (oculto por padrão)
        self.progress_label = QLabel()
        status.addPermanentWidget(self.progress_label)
    
    def _setup_timers(self) -> None:
        """Configura timers de atualização."""
        # Timer para verificar status do Sentinel
        self.sentinel_timer = QTimer(self)
        self.sentinel_timer.timeout.connect(self._check_sentinel_status)
        self.sentinel_timer.start(5000)  # 5 segundos
    
    def _setup_sentinel_integration(self) -> None:
        """
        Integra com SentinelBridge real.
        GAP-02 FIX: Conecta sinais do SentinelBridge à Sidebar.
        """
        try:
            from .sentinel_bridge import SentinelBridge
            self._sentinel_bridge = SentinelBridge.instance()
            self._sentinel_bridge.ready.connect(self.sidebar.set_sentinel_status)
            self._sentinel_bridge.status_changed.connect(
                lambda msg: self.statusBar().showMessage(f"Sentinel: {msg}", 5000)
            )
            # Verificação inicial
            self.sidebar.set_sentinel_status(self._sentinel_bridge.is_ready())
            self._logger.info("SentinelBridge integrado à MainWindow")
        except ImportError as e:
            self._logger.warning(f"SentinelBridge não disponível: {e}")
            self._sentinel_bridge = None
    
    def _restore_state(self) -> None:
        """Restaura estado da janela."""
        try:
            from .state import get_state_manager
            state = get_state_manager()
            state.restore_window_geometry(self)
            
            # Restaura última view
            last_view = state.get_last_view_index()
            if 0 <= last_view < 6:
                self._navigate_to_view(last_view)
        except Exception as e:
            self._logger.error(f"Erro ao restaurar estado: {e}", exc_info=True)
    
    def _save_state(self) -> None:
        """Salva estado da janela."""
        try:
            from .state import get_state_manager
            state = get_state_manager()
            state.save_window_geometry(self)
            state.set_last_view_index(self.stack.currentIndex())
        except Exception as e:
            self._logger.error(f"Erro ao salvar estado: {e}", exc_info=True)
    
    @Slot(int)
    def _on_navigation(self, index: int) -> None:
        """Alterna view no stack."""
        self.stack.setCurrentIndex(index)
        
        # Atualiza status bar
        view_names = ["Dashboard", "Estoque", "Atelie", "Fabrica", "Cofre", "Configuracoes"]
        self.statusBar().showMessage(f"{view_names[index]} | Pronto")
    
    @Slot()
    def _check_sentinel_status(self) -> None:
        """
        Verifica status do Sentinel.
        GAP-02 FIX: Usa SentinelBridge real ao invés de mock.
        """
        if hasattr(self, '_sentinel_bridge') and self._sentinel_bridge:
            self.sidebar.set_sentinel_status(self._sentinel_bridge.is_ready())
        else:
            # Fallback: tenta verificar via lock file (GAP-03 unification)
            from pathlib import Path
            lock_file = Path("AutoTabloide_System_Root/temp_render/.sentinel.lock")
            self.sidebar.set_sentinel_status(lock_file.exists())
    
    def show_progress(self, message: str, progress: int = -1) -> None:
        """Mostra progresso na status bar."""
        if progress >= 0:
            self.progress_label.setText(f"{message} ({progress}%)")
        else:
            self.progress_label.setText(message)
    
    def hide_progress(self) -> None:
        """Esconde indicador de progresso."""
        self.progress_label.setText("")
    
    def showEvent(self, event) -> None:
        """Chamado quando janela é exibida."""
        super().showEvent(event)
        # Restaura estado após primeiro show
        if not hasattr(self, '_state_restored'):
            self._state_restored = True
            self._restore_state()
    
    def closeEvent(self, event: QCloseEvent) -> None:
        """Handler de fechamento da janela."""
        reply = QMessageBox.question(
            self, 
            "Confirmar Saida",
            "Deseja realmente sair do AutoTabloide AI?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self._save_state()
            self.closing.emit()
            event.accept()
        else:
            event.ignore()

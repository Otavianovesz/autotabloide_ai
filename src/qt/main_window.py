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
from .widgets.status_widgets import RamUsageWidget, AIStatusWidget, ZoomControlWidget



# =============================================================================
# ASSETS (SVG PATHS)
# =============================================================================

ICONS = {
    "Dashboard": "M3 13h8V3H3v10zm0 8h8v-6H3v6zm10 0h8V11h-8v10zm0-18v6h8V3h-8z",  # Dashboard
    "Estoque": "M20 6h-2.18c.11-.31.18-.65.18-1 0-1.66-1.34-3-3-3-1.66 0-3 1.34-3 3 0 .35.07.69.18 1H7.18c.11-.31.18-.65.18-1 0-1.66-1.34-3-3-3-1.66 0-3 1.34-3 3 0 .35.07.69.18 1H2v13c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V6h-2zM7 6c.55 0 1 .45 1 1s-.45 1-1 1-1-.45-1-1 .45-1 1-1zm8 0c.55 0 1 .45 1 1s-.45 1-1 1-1-.45-1-1 .45-1 1-1zm4 13H5V8h14v11z",  # Box
    "Ateliê": "M12 3c-4.97 0-9 4.03-9 9s4.03 9 9 9c.83 0 1.5-.67 1.5-1.5 0-.39-.15-.74-.39-1.01-.23-.26-.38-.61-.38-.99 0-.83.67-1.5 1.5-1.5H16c2.76 0 5-2.24 5-5 0-4.42-4.03-8-9-8zm-5.5 9c-.83 0-1.5-.67-1.5-1.5S5.67 9 6.5 9 8 9.67 8 10.5 7.33 12 6.5 12zm3-4C8.67 8 8 7.33 8 6.5S8.67 5 9.5 5s1.5.67 1.5 1.5S10.33 8 9.5 8zm5 0c-.83 0-1.5-.67-1.5-1.5S13.67 5 14.5 5s1.5.67 1.5 1.5S15.33 8 14.5 8zm3 4c-.83 0-1.5-.67-1.5-1.5S16.67 9 17.5 9s1.5.67 1.5 1.5-.67 1.5-1.5 1.5z",  # Palette
    "Fábrica": "M22 22H2V2h20v20zM11 6v3h2v-3h-2zm-6 0v3h2v-3h-2zm0 6v3h2v-3h-2zm6 0v3h2v-3h-2zm6-6v3h2v-3h-2zm0 6v3h2v-3h-2z", # Generic Grid (Placeholder)
    "Cofre": "M18 8h-1V6c0-2.76-2.24-5-5-5S7 3.24 7 6v2H6c-1.1 0-2 .9-2 2v10c0 1.1.9 2 2 2h12c1.1 0 2-.9 2-2V10c0-1.1-.9-2-2-2zm-6 9c-1.1 0-2-.9-2-2s.9-2 2-2 2 .9 2 2-.9 2-2 2zm3.1-9H8.9V6c0-1.71 1.39-3 3.1-3 1.71 0 3.1 1.29 3.1 3v2z", # Lock
    "Configurações": "M19.14 12.94c.04-.3.06-.61.06-.94 0-.32-.02-.64-.07-.94l2.03-1.58c.18-.14.23-.41.12-.61l-1.92-3.32c-.12-.22-.37-.29-.59-.22l-2.39.96c-.5-.38-1.03-.7-1.62-.94l-.36-2.54c-.04-.24-.24-.41-.48-.41h-3.84c-.24 0-.43.17-.47.41l-.36 2.54c-.59.24-1.13.57-1.62.94l-2.39-.96c-.22-.08-.47 0-.59.22L6.92 8.87c-.12.21-.08.47.12.61l2.03 1.58c-.05.3-.09.63-.09.94s.02.64.07.94l-2.03 1.58c-.18.14-.23.41-.12.61l1.92 3.32c.12.22.37.29.59.22l2.39-.96c.5.38 1.03.7 1.62.94l.36 2.54c.05.24.24.41.48.41h3.84c.24 0 .44-.17.47-.41l.36-2.54c.59-.24 1.13-.56 1.62-.94l2.39.96c.22.08.47 0 .59-.22l1.92-3.32c.12-.22.07-.47-.12-.61l-2.01-1.58zM12 15.6c-1.98 0-3.6-1.62-3.6-3.6s1.62-3.6 3.6-3.6 3.6 1.62 3.6 3.6-1.62 3.6-3.6 3.6z", # Gear
    "Menu": "M3 18h18v-2H3v2zm0-5h18v-2H3v2zm0-7v2h18V6H3z" # Toggle
}

# =============================================================================
# NAV BUTTON (Passo 77 & 78)
# =============================================================================

class NavButton(QPushButton):
    """Botão de navegação customizado com ícones Vetoriais e Indicador."""
    
    def __init__(self, text: str, icon_key: str, parent=None):
        super().__init__(parent)
        self.setText(text) # Texto é usado apenas para referência ou tooltip quando colapsado
        self.icon_key = icon_key or "Dashboard"
        self.text_label = text
        
        self.setCheckable(True)
        self.setCursor(Qt.PointingHandCursor)
        self.setMinimumHeight(50)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        
        # Estado
        self.is_collapsed = False
        self.is_hovered = False
        
        # Cores (hardcoded do tema para performance no paint)
        self.col_normal = QColor("#8D99AE")
        self.col_hover = QColor("#FFFFFF")
        self.col_active = QColor("#6C5CE7")
        self.col_bg_active = QColor("#6C5CE71A") # 10% opacity
        
        # SVG path
        self.path = QPainterPath()
        from PySide6.QtGui import QPainterPath
        # Parse simples do SVG path string não é trivial sem QPainterPath.addPath (disponível QT 6.4+?)
        # Para compatibilidade, vamos usar QIcon com QPixmap mask colorization se addPath falhar,
        # MAS, como prometido SVG via código, vamos tentar usar parser básico ou QFont com icon font?
        # NÃO. O plano diz "SVG Icons: Paths SVG reais". 
        # A forma mais fácil no Qt é carregar o SVG num QSvgRenderer e pintar.
        # Mas para "mudar de cor via código", pintar o SVG como mascara é o ideal.
        
        # Abordagem SOTA: Carregar Path string.
        # Mas QPainterPath não tem fromStringSvgPath fácil no PySide6 antigo?
        # Vamos usar uma gambiarra robusta: QImage.fromData(svg_bytes) e colorir com CompositionMode.
        pass

    def paintEvent(self, event):
        from PySide6.QtGui import QPainter, QBrush, QPen, QColor, QFont
        
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Determina cores
        if self.isChecked():
            icon_color = self.col_active
            text_color = self.col_active
            bg_color = self.col_bg_active
        elif self.is_hovered:
            icon_color = self.col_hover
            text_color = self.col_hover
            bg_color = QColor("#FFFFFF0D") # 5% white
        else:
            icon_color = self.col_normal
            text_color = self.col_normal
            bg_color = Qt.transparent
            
        # Draw Background
        if self.isChecked() or self.is_hovered:
            rect = self.rect().adjusted(4, 2, -4, -2) # Margem interna
            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(bg_color))
            painter.drawRoundedRect(rect, 8, 8)
            
        # Draw Active Indicator (Left Bar)
        if self.isChecked():
            ind_rect = self.rect()
            ind_rect.setWidth(4)
            ind_rect.setHeight(24)
            ind_rect.moveCenter(self.rect().center())
            ind_rect.moveLeft(0) # Grudado na esquerda
            
            painter.setBrush(QBrush(self.col_active))
            painter.drawRoundedRect(ind_rect, 2, 2)
            
        # Draw Icon (Simulated by drawing SVG Path using QSvgRenderer logic or FontAwesome approach)
        # Para simplificar e garantir funcionamento sem arquivos externos, vamos desenhar o PATH fornecido?
        # PySide6 não desenha SVG path string direto facilmente sem parser.
        # Fallback: Usar Unicode/Emoji se path falhar ou desenhar Texto se não tiver engine de path manual.
        # DECISÃO: Para cumprir "SVG via código", vou usar QPainterPath com coordenadas relativas? Muito complexo.
        # VOU USAR QSvgRenderer carregando BYTES do SVG construído on-the-fly.
        
        from PySide6.QtSvg import QSvgRenderer
        from PySide6.QtCore import QByteArray
        
        # Monta SVG string com fill color dinâmico
        color_hex = icon_color.name()
        path_d = ICONS.get(self.icon_key, "")
        svg_content = f"""<svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
            <path d="{path_d}" fill="{color_hex}"/>
        </svg>"""
        
        renderer = QSvgRenderer(QByteArray(svg_content.encode('utf-8')))
        
        icon_size = 24
        icon_rect = self.rect()
        
        if self.is_collapsed:
            # Centralizado
            x = (self.width() - icon_size) / 2
        else:
            # Esquerda com margem
            x = 16
            
        y = (self.height() - icon_size) / 2
        
        renderer.render(painter, QRectF(x, y, icon_size, icon_size))
        
        # Draw Text
        if not self.is_collapsed:
            font = QFont("Inter") # Ou padrão
            font.setPixelSize(14)
            if self.isChecked(): font.setBold(True)
            
            painter.setFont(font)
            painter.setPen(text_color)
            
            text_rect = self.rect()
            text_rect.setLeft(x + icon_size + 12) # Padding do icone
            text_rect.setRight(self.width() - 10)
            
            painter.drawText(text_rect, Qt.AlignLeft | Qt.AlignVCenter, self.text_label)
            
    def enterEvent(self, event):
        self.is_hovered = True
        self.update()
        super().enterEvent(event)
        
    def leaveEvent(self, event):
        self.is_hovered = False
        self.update()
        super().leaveEvent(event)


# =============================================================================
# SIDEBAR (Passo 76)
# =============================================================================

class Sidebar(QFrame):
    """Sidebar retrátil com animação."""
    
    navigation_changed = Signal(int)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("sidebar")
        
        # Estado
        self.is_collapsed = False
        self.target_width = 250
        
        self.start_width = 250
        self.collapsed_width = 70
        
        # Animação
        from PySide6.QtCore import QPropertyAnimation, QEasingCurve, QSize
        self.anim = QPropertyAnimation(self, b"maximumWidth")
        self.anim.setDuration(300)
        self.anim.setEasingCurve(QEasingCurve.InOutQuad)
        
        self.init_ui()
        
    def init_ui(self):
        self.setMaximumWidth(self.start_width)
        self.setMinimumWidth(self.collapsed_width)
        self.setStyleSheet("background-color: #1A1A2E; border-right: 1px solid #16213E;")
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 10, 0, 10)
        layout.setSpacing(4)
        
        # Header (Toggle)
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(10, 0, 10, 0)
        
        self.toggle_btn = NavButton("", "Menu")
        self.toggle_btn.clicked.connect(self.toggle_sidebar)
        self.toggle_btn.setFixedHeight(40)
        # self.toggle_btn.setFlat(True) # NavButton já cuida do paint
        
        header_layout.addWidget(self.toggle_btn)
        layout.addLayout(header_layout)
        
        layout.addSpacing(10)
        
        # Título e Versão (Escondidos quando colapsado)
        self.title_lbl = QLabel("AutoTabloide AI")
        self.title_lbl.setProperty("class", "title-sidebar")
        self.title_lbl.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.title_lbl)
        
        self.version_lbl = QLabel("v2.0.0 Qt")
        self.version_lbl.setProperty("class", "version-label")
        self.version_lbl.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.version_lbl)
        
        layout.addSpacing(20)
        
        # Botões
        self.nav_buttons = []
        nav_items = [
            ("Dashboard", "Dashboard", 0),
            ("Estoque", "Estoque", 1),
            ("Ateliê", "Ateliê", 2),
            ("Fábrica", "Fábrica", 3),
            ("Cofre", "Cofre", 4),
            ("Configurações", "Configurações", 5),
        ]
        
        for text, icon, idx in nav_items:
            btn = NavButton(text, icon)
            btn.clicked.connect(lambda checked, i=idx: self._on_nav_click(i))
            layout.addWidget(btn)
            self.nav_buttons.append(btn)
            
        layout.addStretch()
        
        # Sentinel
        self.sentinel_indicator = QLabel("● Active")
        self.sentinel_indicator.setAlignment(Qt.AlignCenter)
        self.sentinel_indicator.setProperty("class", "status-ok")
        layout.addWidget(self.sentinel_indicator)
        
        # Seleciona primeiro
        self.nav_buttons[0].setChecked(True)
        
        # Hook animation finished to update layout if needed
        # self.anim.finished.connect(self._on_anim_finished)

    def toggle_sidebar(self):
        start = self.width()
        
        if self.is_collapsed:
            # Expandir
            end = self.start_width
            self.is_collapsed = False
            self.title_lbl.show()
            self.version_lbl.show()
            self.sentinel_indicator.setText("● Sentinel: Ativo")
        else:
            # Colapsar
            end = self.collapsed_width
            self.is_collapsed = True
            self.title_lbl.hide()
            self.version_lbl.hide()
            self.sentinel_indicator.setText("●")
            
        # Atualiza estado dos botões antes da animação para ficar bonito
        for btn in self.nav_buttons:
            btn.is_collapsed = self.is_collapsed
        self.toggle_btn.is_collapsed = self.is_collapsed # Toggle button doesn't move text but centers icon
            
        self.anim.setStartValue(start)
        self.anim.setEndValue(end)
        self.anim.start()
        
    def _on_nav_click(self, index: int):
        for i, btn in enumerate(self.nav_buttons):
            btn.setChecked(i == index)
        self.navigation_changed.emit(index)
        
    def set_sentinel_status(self, active: bool):
        if active:
            self.sentinel_indicator.setProperty("class", "status-ok")
            text = "● Sentinel: Ativo" if not self.is_collapsed else "●"
        else:
            self.sentinel_indicator.setProperty("class", "status-error")
            text = "● Sentinel: Offline" if not self.is_collapsed else "●"
            
        self.sentinel_indicator.setText(text)
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
        """Atualiza título: 'Projeto* - AutoTabloide vX.X'."""
        project = self._current_project_name or "Sem Projeto"
        dirty_marker = "*" if self._is_dirty else ""
        self.setWindowTitle(f"{project}{dirty_marker} - AutoTabloide v{self.VERSION}")
    
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
        self.dashboard.project_selected.connect(self._on_dashboard_project_selected)
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
        """Configura barra de status industrial."""
        status = self.statusBar()
        status.showMessage("Pronto")
        
        # Widgets permanentes (Lado Direito)
        
        # 1. Zoom Control
        self.zoom_widget = ZoomControlWidget(self)
        status.addPermanentWidget(self.zoom_widget)
        
        # 2. AI Status (Sentinel)
        self.ai_status_widget = AIStatusWidget(self)
        status.addPermanentWidget(self.ai_status_widget)
        
        # 3. RAM Usage
        self.ram_widget = RamUsageWidget(self)
        status.addPermanentWidget(self.ram_widget)
        
        # Widget de progresso original (pode ser removido ou mantido como fallback)
        self.progress_label = QLabel()
        # status.addPermanentWidget(self.progress_label)
    
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

    @Slot(int)
    def _on_dashboard_project_selected(self, project_id: int):
        """Handler para seleção de projeto no Dashboard."""
        self._logger.info(f"Projeto selecionado no Dashboard: {project_id}")
        
        # TODO: Implementar carregamento real do projeto no Ateliê via ProjectManager
        # Por enquanto, apenas navega para o Ateliê e mostra feedback
        self._navigate_to_view(2)  # 2 = Ateliê
        
        # Tenta notificar o Ateliê (se tiver método load) ou apenas mostra mensagem
        self.statusBar().showMessage(f"Carregando projeto #{project_id}...", 3000)
        
        # Se Ateliê tivesse load_project:
        # self.atelier.load_project(project_id)

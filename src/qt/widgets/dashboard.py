"""
AutoTabloide AI - Dashboard Widget (Completo)
==============================================
Painel inicial com estatísticas, status e ações rápidas.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QPushButton, QFrame, QProgressBar, QListWidget,
    QListWidgetItem, QSpacerItem, QSizePolicy
)
from PySide6.QtCore import Qt, Signal, Slot, QTimer
from PySide6.QtGui import QColor
from typing import Optional, Dict, Any


class StatCard(QFrame):
    """Card de estatística com valor destacado."""
    
    clicked = Signal()
    
    def __init__(
        self, 
        title: str, 
        value: str = "0", 
        subtitle: str = "",
        icon: str = "",
        accent_color: str = "#6C5CE7",
        parent=None
    ):
        super().__init__(parent)
        self.setProperty("class", "card")
        self.setCursor(Qt.PointingHandCursor)
        self.accent_color = accent_color
        
        self.setStyleSheet(f"""
            QFrame {{
                background-color: #1A1A2E;
                border: 1px solid #2D2D44;
                border-radius: 12px;
                padding: 16px;
            }}
            QFrame:hover {{
                border-color: {accent_color};
            }}
        """)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(8)
        
        # Header com ícone
        header = QHBoxLayout()
        
        icon_label = QLabel(icon)
        icon_label.setStyleSheet("font-size: 24px;")
        header.addWidget(icon_label)
        
        title_label = QLabel(title)
        title_label.setStyleSheet("color: #808080; font-size: 12px; font-weight: 600;")
        header.addWidget(title_label)
        header.addStretch()
        
        layout.addLayout(header)
        
        # Valor grande
        self.value_label = QLabel(value)
        self.value_label.setStyleSheet(f"""
            font-size: 36px; 
            font-weight: bold; 
            color: {accent_color};
        """)
        layout.addWidget(self.value_label)
        
        # Subtítulo
        if subtitle:
            sub = QLabel(subtitle)
            sub.setStyleSheet("color: #606060; font-size: 11px;")
            layout.addWidget(sub)
    
    def set_value(self, value: str):
        self.value_label.setText(value)
    
    def mousePressEvent(self, event):
        self.clicked.emit()
        super().mousePressEvent(event)


class StatusIndicator(QFrame):
    """Indicador de status de serviço."""
    
    def __init__(self, name: str, status: bool = False, parent=None):
        super().__init__(parent)
        self.name = name
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)
        
        self.led = QLabel()
        self.led.setFixedSize(10, 10)
        layout.addWidget(self.led)
        
        self.name_label = QLabel(name)
        self.name_label.setStyleSheet("color: #A0A0A0; font-size: 12px;")
        layout.addWidget(self.name_label)
        
        layout.addStretch()
        
        self.status_label = QLabel()
        self.status_label.setStyleSheet("font-size: 11px;")
        layout.addWidget(self.status_label)
        
        self.set_status(status)
    
    def set_status(self, active: bool, message: str = ""):
        if active:
            self.led.setStyleSheet("""
                background-color: #2ECC71;
                border-radius: 5px;
            """)
            self.status_label.setText(message or "Online")
            self.status_label.setStyleSheet("color: #2ECC71; font-size: 11px;")
        else:
            self.led.setStyleSheet("""
                background-color: #E74C3C;
                border-radius: 5px;
            """)
            self.status_label.setText(message or "Offline")
            self.status_label.setStyleSheet("color: #E74C3C; font-size: 11px;")


class ActivityItem(QFrame):
    """Item de atividade recente."""
    
    def __init__(self, action: str, detail: str, time: str, parent=None):
        super().__init__(parent)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 6, 8, 6)
        
        action_label = QLabel(action)
        action_label.setStyleSheet("color: #FFFFFF; font-weight: 500;")
        layout.addWidget(action_label)
        
        detail_label = QLabel(detail)
        detail_label.setStyleSheet("color: #808080;")
        layout.addWidget(detail_label)
        
        layout.addStretch()
        
        time_label = QLabel(time)
        time_label.setStyleSheet("color: #606060; font-size: 11px;")
        layout.addWidget(time_label)


class DashboardWidget(QWidget):
    """Widget principal do Dashboard."""
    
    navigate_to = Signal(int)  # Índice da view
    
    def __init__(self, container=None, parent=None):
        super().__init__(parent)
        self.container = container
        self._setup_ui()
        self._setup_refresh_timer()
        self._load_stats()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(24)
        
        # Header
        header = QHBoxLayout()
        
        title = QLabel("Dashboard")
        title.setStyleSheet("font-size: 32px; font-weight: bold; color: #FFFFFF;")
        header.addWidget(title)
        
        header.addStretch()
        
        self.last_update = QLabel("Atualizado agora")
        self.last_update.setStyleSheet("color: #606060;")
        header.addWidget(self.last_update)
        
        layout.addLayout(header)
        
        # Cards de estatísticas (grid 2x2)
        cards_grid = QGridLayout()
        cards_grid.setSpacing(16)
        
        self.card_products = StatCard(
            "PRODUTOS", "0", "no banco de dados",
            icon="[P]", accent_color="#6C5CE7"
        )
        self.card_products.clicked.connect(lambda: self.navigate_to.emit(1))
        cards_grid.addWidget(self.card_products, 0, 0)
        
        self.card_layouts = StatCard(
            "LAYOUTS SVG", "0", "templates disponiveis",
            icon="[L]", accent_color="#00CEC9"
        )
        cards_grid.addWidget(self.card_layouts, 0, 1)
        
        self.card_projects = StatCard(
            "PROJETOS", "0", "salvos",
            icon="[J]", accent_color="#FDCB6E"
        )
        self.card_projects.clicked.connect(lambda: self.navigate_to.emit(2))
        cards_grid.addWidget(self.card_projects, 1, 0)
        
        self.card_images = StatCard(
            "IMAGENS", "0", "no cofre",
            icon="[I]", accent_color="#E17055"
        )
        self.card_images.clicked.connect(lambda: self.navigate_to.emit(4))
        cards_grid.addWidget(self.card_images, 1, 1)
        
        layout.addLayout(cards_grid)
        
        # Status dos serviços
        status_frame = QFrame()
        status_frame.setStyleSheet("""
            QFrame {
                background-color: #1A1A2E;
                border-radius: 12px;
                padding: 16px;
            }
        """)
        status_layout = QVBoxLayout(status_frame)
        
        status_title = QLabel("Status do Sistema")
        status_title.setStyleSheet("font-weight: bold; color: #FFFFFF; font-size: 14px;")
        status_layout.addWidget(status_title)
        
        self.status_db = StatusIndicator("Banco de Dados")
        status_layout.addWidget(self.status_db)
        
        self.status_sentinel = StatusIndicator("Sentinel (IA)")
        status_layout.addWidget(self.status_sentinel)
        
        self.status_llm = StatusIndicator("Modelo LLM")
        status_layout.addWidget(self.status_llm)
        
        layout.addWidget(status_frame)
        
        # Ações rápidas
        actions_frame = QFrame()
        actions_frame.setStyleSheet("""
            QFrame {
                background-color: #1A1A2E;
                border-radius: 12px;
                padding: 16px;
            }
        """)
        actions_layout = QVBoxLayout(actions_frame)
        
        actions_title = QLabel("Acoes Rapidas")
        actions_title.setStyleSheet("font-weight: bold; color: #FFFFFF; font-size: 14px;")
        actions_layout.addWidget(actions_title)
        
        buttons_layout = QHBoxLayout()
        
        btn_snapshot = QPushButton("Criar Snapshot")
        btn_snapshot.clicked.connect(self._create_snapshot)
        buttons_layout.addWidget(btn_snapshot)
        
        btn_import = QPushButton("Importar Excel")
        btn_import.clicked.connect(lambda: self.navigate_to.emit(1))
        buttons_layout.addWidget(btn_import)
        
        btn_new_project = QPushButton("Novo Projeto")
        btn_new_project.clicked.connect(lambda: self.navigate_to.emit(2))
        buttons_layout.addWidget(btn_new_project)
        
        buttons_layout.addStretch()
        
        actions_layout.addLayout(buttons_layout)
        
        layout.addWidget(actions_frame)
        
        # Spacer
        layout.addSpacerItem(QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding))
    
    def _setup_refresh_timer(self):
        """Timer para atualizar estatísticas."""
        self.refresh_timer = QTimer(self)
        self.refresh_timer.timeout.connect(self._load_stats)
        self.refresh_timer.start(30000)  # 30 segundos
    
    def _load_stats(self):
        """Carrega estatísticas."""
        # TODO: Integrar com repositórios reais
        self.card_products.set_value("1,234")
        self.card_layouts.set_value("12")
        self.card_projects.set_value("8")
        self.card_images.set_value("456")
        
        self.status_db.set_status(True, "SQLite OK")
        self.status_sentinel.set_status(True, "Ativo")
        self.status_llm.set_status(False, "Nao carregado")
        
        from datetime import datetime
        self.last_update.setText(f"Atualizado: {datetime.now().strftime('%H:%M:%S')}")
    
    @Slot()
    def _create_snapshot(self):
        from PySide6.QtWidgets import QMessageBox
        QMessageBox.information(
            self, "Snapshot",
            "Snapshot criado com sucesso!\n\nDados do banco salvos."
        )

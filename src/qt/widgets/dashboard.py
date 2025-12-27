"""
AutoTabloide AI - Dashboard Widget
===================================
Tela inicial com estatísticas e gestão de backups.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QFrame, QPushButton, QProgressBar
)
from PySide6.QtCore import Qt, Signal, Slot, QTimer
from typing import Optional


class StatCard(QFrame):
    """Card de estatística para dashboard."""
    
    def __init__(
        self, 
        title: str, 
        value: str = "0", 
        icon: str = "📊",
        parent: Optional[QWidget] = None
    ):
        super().__init__(parent)
        self.setProperty("class", "card")
        self.setMinimumSize(200, 120)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(8)
        
        # Header com ícone e título
        header = QHBoxLayout()
        icon_label = QLabel(icon)
        icon_label.setStyleSheet("font-size: 24px;")
        header.addWidget(icon_label)
        
        title_label = QLabel(title)
        title_label.setStyleSheet("color: #A0A0A0; font-size: 12px;")
        header.addWidget(title_label)
        header.addStretch()
        
        layout.addLayout(header)
        
        # Valor principal
        self.value_label = QLabel(value)
        self.value_label.setProperty("class", "card-value")
        self.value_label.setStyleSheet("font-size: 32px; font-weight: bold; color: #6C5CE7;")
        layout.addWidget(self.value_label)
        
        layout.addStretch()
    
    def set_value(self, value: str) -> None:
        """Atualiza o valor do card."""
        self.value_label.setText(value)


class DashboardWidget(QWidget):
    """Widget principal do Dashboard."""
    
    def __init__(self, container=None, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.container = container
        self._setup_ui()
        self._start_refresh_timer()
    
    def _setup_ui(self) -> None:
        """Configura interface do dashboard."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(24)
        
        # Título
        title = QLabel("Dashboard")
        title.setProperty("class", "title")
        title.setStyleSheet("font-size: 28px; font-weight: bold; color: #FFFFFF;")
        layout.addWidget(title)
        
        subtitle = QLabel("Visão geral do sistema AutoTabloide AI")
        subtitle.setProperty("class", "subtitle")
        subtitle.setStyleSheet("color: #808080; font-size: 14px;")
        layout.addWidget(subtitle)
        
        layout.addSpacing(16)
        
        # Grid de Cards
        cards_layout = QGridLayout()
        cards_layout.setSpacing(16)
        
        self.card_products = StatCard("Produtos Cadastrados", "0", "📦")
        self.card_layouts = StatCard("Layouts Disponíveis", "0", "🎨")
        self.card_projects = StatCard("Projetos Salvos", "0", "📁")
        self.card_images = StatCard("Imagens no Cofre", "0", "🖼️")
        
        cards_layout.addWidget(self.card_products, 0, 0)
        cards_layout.addWidget(self.card_layouts, 0, 1)
        cards_layout.addWidget(self.card_projects, 0, 2)
        cards_layout.addWidget(self.card_images, 0, 3)
        
        layout.addLayout(cards_layout)
        
        # Seção de Status
        status_frame = QFrame()
        status_frame.setProperty("class", "card")
        status_frame.setStyleSheet("""
            QFrame { 
                background-color: #1A1A2E; 
                border-radius: 12px; 
                padding: 16px; 
            }
        """)
        status_layout = QVBoxLayout(status_frame)
        
        status_title = QLabel("Status do Sistema")
        status_title.setStyleSheet("font-size: 16px; font-weight: bold; color: #FFFFFF;")
        status_layout.addWidget(status_title)
        
        # Status items
        self.sentinel_status = QLabel("🟢 Sentinel: Ativo")
        self.sentinel_status.setStyleSheet("color: #2ECC71;")
        status_layout.addWidget(self.sentinel_status)
        
        self.database_status = QLabel("🟢 Banco de Dados: Conectado")
        self.database_status.setStyleSheet("color: #2ECC71;")
        status_layout.addWidget(self.database_status)
        
        self.llm_status = QLabel("🟡 LLM: Carregando...")
        self.llm_status.setStyleSheet("color: #F1C40F;")
        status_layout.addWidget(self.llm_status)
        
        layout.addWidget(status_frame)
        
        # Seção de Ações Rápidas
        actions_layout = QHBoxLayout()
        actions_layout.setSpacing(12)
        
        btn_snapshot = QPushButton("📸 Criar Snapshot")
        btn_snapshot.clicked.connect(self._create_snapshot)
        actions_layout.addWidget(btn_snapshot)
        
        btn_refresh = QPushButton("🔄 Atualizar Dados")
        btn_refresh.setProperty("class", "secondary")
        btn_refresh.clicked.connect(self._refresh_data)
        actions_layout.addWidget(btn_refresh)
        
        actions_layout.addStretch()
        
        layout.addLayout(actions_layout)
        
        layout.addStretch()
    
    def _start_refresh_timer(self) -> None:
        """Inicia timer de atualização automática."""
        self.refresh_timer = QTimer(self)
        self.refresh_timer.timeout.connect(self._refresh_data)
        self.refresh_timer.start(30000)  # 30 segundos
    
    @Slot()
    def _refresh_data(self) -> None:
        """Atualiza dados do dashboard."""
        # TODO: Integrar com repositories quando container estiver disponível
        # Por enquanto, apenas mostra dados placeholder
        self.card_products.set_value("0")
        self.card_layouts.set_value("0")
        self.card_projects.set_value("0")
        self.card_images.set_value("0")
    
    @Slot()
    def _create_snapshot(self) -> None:
        """Cria um snapshot de backup."""
        # TODO: Implementar criação de snapshot
        print("[Dashboard] Criando snapshot...")

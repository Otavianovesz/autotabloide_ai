"""
AutoTabloide AI - Settings Widget
==================================
Configurações do sistema.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QScrollArea, QFrame,
    QLabel, QLineEdit, QPushButton, QSpinBox, QDoubleSpinBox,
    QComboBox, QCheckBox, QGroupBox, QFileDialog, QMessageBox,
    QTabWidget
)
from PySide6.QtCore import Qt, Signal, Slot
from typing import Optional
from pathlib import Path


class SettingsWidget(QWidget):
    """Widget de configurações."""
    
    settings_changed = Signal()
    
    def __init__(self, container=None, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.container = container
        self._setup_ui()
    
    def _setup_ui(self) -> None:
        """Configura interface."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        
        # Header
        header = QHBoxLayout()
        
        title = QLabel("⚙️ Configurações")
        title.setStyleSheet("font-size: 28px; font-weight: bold; color: #FFFFFF;")
        header.addWidget(title)
        
        header.addStretch()
        
        btn_reset = QPushButton("🔄 Resetar Padrões")
        btn_reset.setProperty("class", "secondary")
        btn_reset.clicked.connect(self._reset_defaults)
        header.addWidget(btn_reset)
        
        layout.addLayout(header)
        
        # Tabs de configuração
        tabs = QTabWidget()
        
        # Tab 1: Geral
        tabs.addTab(self._create_general_tab(), "📁 Geral")
        
        # Tab 2: Renderização
        tabs.addTab(self._create_render_tab(), "🎨 Renderização")
        
        # Tab 3: IA / LLM
        tabs.addTab(self._create_ai_tab(), "🤖 Inteligência Artificial")
        
        # Tab 4: Importação
        tabs.addTab(self._create_import_tab(), "📥 Importação")
        
        layout.addWidget(tabs)
        
        # Footer: Botões de ação
        footer = QHBoxLayout()
        footer.addStretch()
        
        btn_save = QPushButton("💾 Salvar Configurações")
        btn_save.clicked.connect(self._save_settings)
        footer.addWidget(btn_save)
        
        layout.addLayout(footer)
    
    def _create_general_tab(self) -> QWidget:
        """Cria tab de configurações gerais."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(16)
        
        # Diretórios
        dirs_group = QGroupBox("📁 Diretórios do Sistema")
        dirs_layout = QVBoxLayout(dirs_group)
        
        # System Root
        root_layout = QHBoxLayout()
        root_layout.addWidget(QLabel("Raiz do Sistema:"))
        self.root_path = QLineEdit()
        self.root_path.setPlaceholderText("C:/AutoTabloide_System_Root")
        root_layout.addWidget(self.root_path)
        btn_root = QPushButton("📂")
        btn_root.setMaximumWidth(40)
        btn_root.clicked.connect(lambda: self._browse_folder(self.root_path))
        root_layout.addWidget(btn_root)
        dirs_layout.addLayout(root_layout)
        
        # Assets
        assets_layout = QHBoxLayout()
        assets_layout.addWidget(QLabel("Cofre de Imagens:"))
        self.assets_path = QLineEdit()
        self.assets_path.setPlaceholderText("assets/store")
        assets_layout.addWidget(self.assets_path)
        btn_assets = QPushButton("📂")
        btn_assets.setMaximumWidth(40)
        btn_assets.clicked.connect(lambda: self._browse_folder(self.assets_path))
        assets_layout.addWidget(btn_assets)
        dirs_layout.addLayout(assets_layout)
        
        # Templates
        templates_layout = QHBoxLayout()
        templates_layout.addWidget(QLabel("Templates SVG:"))
        self.templates_path = QLineEdit()
        self.templates_path.setPlaceholderText("library/svg_source")
        templates_layout.addWidget(self.templates_path)
        btn_templates = QPushButton("📂")
        btn_templates.setMaximumWidth(40)
        btn_templates.clicked.connect(lambda: self._browse_folder(self.templates_path))
        templates_layout.addWidget(btn_templates)
        dirs_layout.addLayout(templates_layout)
        
        layout.addWidget(dirs_group)
        
        # Backup
        backup_group = QGroupBox("💾 Backup Automático")
        backup_layout = QVBoxLayout(backup_group)
        
        self.auto_backup = QCheckBox("Habilitar backup automático")
        self.auto_backup.setChecked(True)
        backup_layout.addWidget(self.auto_backup)
        
        interval_layout = QHBoxLayout()
        interval_layout.addWidget(QLabel("Intervalo (horas):"))
        self.backup_interval = QSpinBox()
        self.backup_interval.setMinimum(1)
        self.backup_interval.setMaximum(168)
        self.backup_interval.setValue(24)
        interval_layout.addWidget(self.backup_interval)
        interval_layout.addStretch()
        backup_layout.addLayout(interval_layout)
        
        retention_layout = QHBoxLayout()
        retention_layout.addWidget(QLabel("Manter últimos:"))
        self.backup_retention = QSpinBox()
        self.backup_retention.setMinimum(1)
        self.backup_retention.setMaximum(100)
        self.backup_retention.setValue(10)
        self.backup_retention.setSuffix(" backups")
        retention_layout.addWidget(self.backup_retention)
        retention_layout.addStretch()
        backup_layout.addLayout(retention_layout)
        
        layout.addWidget(backup_group)
        
        layout.addStretch()
        return widget
    
    def _create_render_tab(self) -> QWidget:
        """Cria tab de renderização."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(16)
        
        # DPI
        dpi_group = QGroupBox("🎯 Resolução")
        dpi_layout = QVBoxLayout(dpi_group)
        
        web_layout = QHBoxLayout()
        web_layout.addWidget(QLabel("DPI para Web/Digital:"))
        self.dpi_web = QSpinBox()
        self.dpi_web.setMinimum(72)
        self.dpi_web.setMaximum(300)
        self.dpi_web.setValue(96)
        self.dpi_web.setSuffix(" DPI")
        web_layout.addWidget(self.dpi_web)
        web_layout.addStretch()
        dpi_layout.addLayout(web_layout)
        
        print_layout = QHBoxLayout()
        print_layout.addWidget(QLabel("DPI para Impressão:"))
        self.dpi_print = QSpinBox()
        self.dpi_print.setMinimum(150)
        self.dpi_print.setMaximum(600)
        self.dpi_print.setValue(300)
        self.dpi_print.setSuffix(" DPI")
        print_layout.addWidget(self.dpi_print)
        print_layout.addStretch()
        dpi_layout.addLayout(print_layout)
        
        layout.addWidget(dpi_group)
        
        # Cores
        color_group = QGroupBox("🎨 Gestão de Cores")
        color_layout = QVBoxLayout(color_group)
        
        profile_layout = QHBoxLayout()
        profile_layout.addWidget(QLabel("Perfil ICC padrão:"))
        self.icc_profile = QComboBox()
        self.icc_profile.addItem("SWOP Coated v2")
        self.icc_profile.addItem("Coated FOGRA39")
        self.icc_profile.addItem("sRGB")
        profile_layout.addWidget(self.icc_profile)
        profile_layout.addStretch()
        color_layout.addLayout(profile_layout)
        
        self.preserve_black = QCheckBox("Preservar preto puro (K=100)")
        self.preserve_black.setChecked(True)
        color_layout.addWidget(self.preserve_black)
        
        layout.addWidget(color_group)
        
        # PDF
        pdf_group = QGroupBox("📄 Opções de PDF")
        pdf_layout = QVBoxLayout(pdf_group)
        
        self.embed_fonts = QCheckBox("Converter fontes em curvas")
        self.embed_fonts.setChecked(True)
        pdf_layout.addWidget(self.embed_fonts)
        
        self.add_crop_marks = QCheckBox("Adicionar marcas de corte")
        self.add_crop_marks.setChecked(True)
        pdf_layout.addWidget(self.add_crop_marks)
        
        bleed_layout = QHBoxLayout()
        bleed_layout.addWidget(QLabel("Sangria (bleed):"))
        self.bleed_mm = QDoubleSpinBox()
        self.bleed_mm.setMinimum(0)
        self.bleed_mm.setMaximum(20)
        self.bleed_mm.setValue(3)
        self.bleed_mm.setSuffix(" mm")
        bleed_layout.addWidget(self.bleed_mm)
        bleed_layout.addStretch()
        pdf_layout.addLayout(bleed_layout)
        
        layout.addWidget(pdf_group)
        
        layout.addStretch()
        return widget
    
    def _create_ai_tab(self) -> QWidget:
        """Cria tab de IA/LLM."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(16)
        
        # LLM
        llm_group = QGroupBox("🤖 Modelo de Linguagem (LLM)")
        llm_layout = QVBoxLayout(llm_group)
        
        model_layout = QHBoxLayout()
        model_layout.addWidget(QLabel("Modelo GGUF:"))
        self.llm_path = QLineEdit()
        self.llm_path.setPlaceholderText("models/Llama-3-8b-instruct.Q4_K_M.gguf")
        model_layout.addWidget(self.llm_path)
        btn_model = QPushButton("📂")
        btn_model.setMaximumWidth(40)
        btn_model.clicked.connect(self._browse_model)
        model_layout.addWidget(btn_model)
        llm_layout.addLayout(model_layout)
        
        gpu_layout = QHBoxLayout()
        gpu_layout.addWidget(QLabel("GPU Layers:"))
        self.gpu_layers = QSpinBox()
        self.gpu_layers.setMinimum(0)
        self.gpu_layers.setMaximum(100)
        self.gpu_layers.setValue(0)
        self.gpu_layers.setToolTip("0 = CPU only, >0 = offload para GPU")
        gpu_layout.addWidget(self.gpu_layers)
        gpu_layout.addStretch()
        llm_layout.addLayout(gpu_layout)
        
        ctx_layout = QHBoxLayout()
        ctx_layout.addWidget(QLabel("Context Size:"))
        self.ctx_size = QSpinBox()
        self.ctx_size.setMinimum(512)
        self.ctx_size.setMaximum(32768)
        self.ctx_size.setValue(2048)
        self.ctx_size.setSingleStep(512)
        ctx_layout.addWidget(self.ctx_size)
        ctx_layout.addStretch()
        llm_layout.addLayout(ctx_layout)
        
        layout.addWidget(llm_group)
        
        # Processamento de Imagem
        image_group = QGroupBox("🖼️ Processamento de Imagem")
        image_layout = QVBoxLayout(image_group)
        
        self.auto_remove_bg = QCheckBox("Remover fundo automaticamente")
        self.auto_remove_bg.setChecked(True)
        image_layout.addWidget(self.auto_remove_bg)
        
        self.auto_crop = QCheckBox("Auto-crop inteligente")
        self.auto_crop.setChecked(True)
        image_layout.addWidget(self.auto_crop)
        
        min_res_layout = QHBoxLayout()
        min_res_layout.addWidget(QLabel("Resolução mínima:"))
        self.min_resolution = QSpinBox()
        self.min_resolution.setMinimum(100)
        self.min_resolution.setMaximum(2000)
        self.min_resolution.setValue(500)
        self.min_resolution.setSuffix(" px")
        min_res_layout.addWidget(self.min_resolution)
        min_res_layout.addStretch()
        image_layout.addLayout(min_res_layout)
        
        layout.addWidget(image_group)
        
        layout.addStretch()
        return widget
    
    def _create_import_tab(self) -> QWidget:
        """Cria tab de importação."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(16)
        
        # Excel
        excel_group = QGroupBox("📊 Importação de Excel")
        excel_layout = QVBoxLayout(excel_group)
        
        self.auto_sanitize = QCheckBox("Sanitizar nomes automaticamente (IA)")
        self.auto_sanitize.setChecked(True)
        excel_layout.addWidget(self.auto_sanitize)
        
        self.detect_duplicates = QCheckBox("Detectar duplicatas por SKU")
        self.detect_duplicates.setChecked(True)
        excel_layout.addWidget(self.detect_duplicates)
        
        self.update_prices = QCheckBox("Atualizar preços existentes")
        self.update_prices.setChecked(True)
        excel_layout.addWidget(self.update_prices)
        
        layout.addWidget(excel_group)
        
        # Web Scraping
        scraping_group = QGroupBox("🌐 Web Scraping")
        scraping_layout = QVBoxLayout(scraping_group)
        
        timeout_layout = QHBoxLayout()
        timeout_layout.addWidget(QLabel("Timeout de requisição:"))
        self.scraping_timeout = QSpinBox()
        self.scraping_timeout.setMinimum(5)
        self.scraping_timeout.setMaximum(120)
        self.scraping_timeout.setValue(30)
        self.scraping_timeout.setSuffix(" segundos")
        timeout_layout.addWidget(self.scraping_timeout)
        timeout_layout.addStretch()
        scraping_layout.addLayout(timeout_layout)
        
        self.rotate_ua = QCheckBox("Rotacionar User-Agent")
        self.rotate_ua.setChecked(True)
        scraping_layout.addWidget(self.rotate_ua)
        
        self.respect_robots = QCheckBox("Respeitar robots.txt")
        self.respect_robots.setChecked(True)
        scraping_layout.addWidget(self.respect_robots)
        
        layout.addWidget(scraping_group)
        
        layout.addStretch()
        return widget
    
    def _browse_folder(self, line_edit: QLineEdit) -> None:
        """Abre diálogo para selecionar pasta."""
        folder = QFileDialog.getExistingDirectory(self, "Selecionar Pasta")
        if folder:
            line_edit.setText(folder)
    
    def _browse_model(self) -> None:
        """Abre diálogo para selecionar modelo."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Selecionar Modelo GGUF",
            "",
            "GGUF Files (*.gguf);;All Files (*)"
        )
        if file_path:
            self.llm_path.setText(file_path)
    
    @Slot()
    def _save_settings(self) -> None:
        """Salva configurações."""
        # TODO: Integrar com SettingsService
        QMessageBox.information(
            self,
            "Configurações Salvas",
            "As configurações foram salvas com sucesso!\n\n(Integrar com SettingsService)"
        )
        self.settings_changed.emit()
    
    @Slot()
    def _reset_defaults(self) -> None:
        """Reseta para valores padrão."""
        reply = QMessageBox.question(
            self,
            "Resetar Padrões",
            "Deseja realmente restaurar todas as configurações para os valores padrão?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            # TODO: Implementar reset
            QMessageBox.information(self, "Reset", "Configurações restauradas!")

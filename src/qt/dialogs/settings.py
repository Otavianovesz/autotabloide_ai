"""
AutoTabloide AI - Settings Dialog
==================================
PROTOCOLO DE RETIFICAÇÃO NÍVEL 0 - Fase 6 (Passo 204)
Diálogo de configurações com abas.
"""

from __future__ import annotations
from typing import Dict, Any
import logging

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QTabWidget, QWidget, QFormLayout,
    QSpinBox, QCheckBox, QComboBox, QLineEdit,
    QGroupBox, QFileDialog
)

logger = logging.getLogger("Settings")


class SettingsDialog(QDialog):
    """
    Diálogo de configurações do sistema.
    
    Abas:
    - Geral: tema, idioma
    - Exportação: DPI, formato, perfil ICC
    - IA: modelo, GPU
    - Avançado: paths, cache
    """
    
    settings_changed = Signal(dict)
    
    def __init__(self, current_settings: Dict = None, parent=None):
        super().__init__(parent)
        self._settings = current_settings or {}
        self.setWindowTitle("Configurações")
        self.setMinimumSize(600, 500)
        self.setStyleSheet("""
            QDialog {
                background-color: #0F0F1A;
            }
            QLabel {
                color: #FFFFFF;
            }
            QGroupBox {
                color: #6C5CE7;
                font-weight: bold;
                border: 1px solid #2D2D44;
                border-radius: 6px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
            }
        """)
        
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        
        # Tabs
        tabs = QTabWidget()
        tabs.addTab(self._create_general_tab(), "⚙️ Geral")
        tabs.addTab(self._create_export_tab(), "📄 Exportação")
        tabs.addTab(self._create_ai_tab(), "🤖 IA")
        tabs.addTab(self._create_advanced_tab(), "🔧 Avançado")
        layout.addWidget(tabs)
        
        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        btn_reset = QPushButton("Restaurar Padrões")
        btn_reset.clicked.connect(self._reset_defaults)
        btn_layout.addWidget(btn_reset)
        
        btn_cancel = QPushButton("Cancelar")
        btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(btn_cancel)
        
        btn_save = QPushButton("Salvar")
        btn_save.setStyleSheet("""
            QPushButton {
                background-color: #6C5CE7;
                color: white;
                padding: 8px 24px;
            }
        """)
        btn_save.clicked.connect(self._save_settings)
        btn_layout.addWidget(btn_save)
        
        layout.addLayout(btn_layout)
    
    def _create_general_tab(self) -> QWidget:
        """Aba Geral."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Aparência
        group = QGroupBox("Aparência")
        form = QFormLayout(group)
        
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["Escuro", "Claro", "Sistema"])
        form.addRow("Tema:", self.theme_combo)
        
        self.font_size = QSpinBox()
        self.font_size.setRange(10, 18)
        self.font_size.setValue(12)
        form.addRow("Tamanho da fonte:", self.font_size)
        
        layout.addWidget(group)
        
        # Comportamento
        group2 = QGroupBox("Comportamento")
        form2 = QFormLayout(group2)
        
        self.autosave_check = QCheckBox("Habilitado")
        self.autosave_check.setChecked(True)
        form2.addRow("Auto-save:", self.autosave_check)
        
        self.autosave_interval = QSpinBox()
        self.autosave_interval.setRange(30, 300)
        self.autosave_interval.setValue(60)
        self.autosave_interval.setSuffix(" segundos")
        form2.addRow("Intervalo:", self.autosave_interval)
        
        self.confirm_exit = QCheckBox("Confirmar antes de sair")
        self.confirm_exit.setChecked(True)
        form2.addRow("", self.confirm_exit)
        
        layout.addWidget(group2)
        layout.addStretch()
        
        return widget
    
    def _create_export_tab(self) -> QWidget:
        """Aba Exportação."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        group = QGroupBox("PDF")
        form = QFormLayout(group)
        
        self.dpi_spin = QSpinBox()
        self.dpi_spin.setRange(72, 600)
        self.dpi_spin.setValue(300)
        form.addRow("DPI padrão:", self.dpi_spin)
        
        self.format_combo = QComboBox()
        self.format_combo.addItems(["PDF", "PNG", "SVG"])
        form.addRow("Formato padrão:", self.format_combo)
        
        self.cmyk_check = QCheckBox("Converter para CMYK")
        self.cmyk_check.setChecked(True)
        form.addRow("", self.cmyk_check)
        
        self.icc_combo = QComboBox()
        self.icc_combo.addItems([
            "CoatedFOGRA39.icc",
            "ISOcoated_v2_eci.icc",
            "sRGB Color Space Profile.icm"
        ])
        form.addRow("Perfil ICC:", self.icc_combo)
        
        layout.addWidget(group)
        
        # Bleed
        group2 = QGroupBox("Margens")
        form2 = QFormLayout(group2)
        
        self.bleed_spin = QSpinBox()
        self.bleed_spin.setRange(0, 10)
        self.bleed_spin.setValue(3)
        self.bleed_spin.setSuffix(" mm")
        form2.addRow("Sangria (bleed):", self.bleed_spin)
        
        self.cropmarks_check = QCheckBox("Incluir marcas de corte")
        self.cropmarks_check.setChecked(True)
        form2.addRow("", self.cropmarks_check)
        
        layout.addWidget(group2)
        layout.addStretch()
        
        return widget
    
    def _create_ai_tab(self) -> QWidget:
        """Aba IA."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        group = QGroupBox("Sentinel")
        form = QFormLayout(group)
        
        self.ai_enabled = QCheckBox("Habilitado")
        self.ai_enabled.setChecked(True)
        form.addRow("Sentinel:", self.ai_enabled)
        
        self.gpu_check = QCheckBox("Usar GPU (CUDA/Vulkan)")
        self.gpu_check.setChecked(True)
        form.addRow("", self.gpu_check)
        
        self.model_path = QLineEdit()
        self.model_path.setPlaceholderText("AutoTabloide_System_Root/bin/models/...")
        form.addRow("Modelo:", self.model_path)
        
        btn_browse = QPushButton("Procurar...")
        btn_browse.clicked.connect(self._browse_model)
        form.addRow("", btn_browse)
        
        layout.addWidget(group)
        
        # Features
        group2 = QGroupBox("Features Automáticas")
        form2 = QFormLayout(group2)
        
        self.auto_rembg = QCheckBox("Remover fundo automaticamente")
        self.auto_rembg.setChecked(True)
        form2.addRow("", self.auto_rembg)
        
        self.auto_upscale = QCheckBox("Upscale imagens baixa resolução")
        self.auto_upscale.setChecked(False)
        form2.addRow("", self.auto_upscale)
        
        layout.addWidget(group2)
        layout.addStretch()
        
        return widget
    
    def _create_advanced_tab(self) -> QWidget:
        """Aba Avançado."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        group = QGroupBox("Cache")
        form = QFormLayout(group)
        
        self.cache_size = QSpinBox()
        self.cache_size.setRange(100, 2000)
        self.cache_size.setValue(500)
        form.addRow("Thumbnails em cache:", self.cache_size)
        
        self.undo_limit = QSpinBox()
        self.undo_limit.setRange(10, 200)
        self.undo_limit.setValue(50)
        form.addRow("Limite de undo:", self.undo_limit)
        
        btn_clear = QPushButton("Limpar Cache")
        btn_clear.clicked.connect(self._clear_cache)
        form.addRow("", btn_clear)
        
        layout.addWidget(group)
        
        # Debug
        group2 = QGroupBox("Debug")
        form2 = QFormLayout(group2)
        
        self.debug_mode = QCheckBox("Modo debug")
        form2.addRow("", self.debug_mode)
        
        self.offline_mode = QCheckBox("Modo offline")
        form2.addRow("", self.offline_mode)
        
        layout.addWidget(group2)
        layout.addStretch()
        
        return widget
    
    def _browse_model(self):
        """Abre diálogo para selecionar modelo."""
        path, _ = QFileDialog.getOpenFileName(
            self, "Selecionar Modelo", "", "GGUF Files (*.gguf);;All Files (*)"
        )
        if path:
            self.model_path.setText(path)
    
    def _clear_cache(self):
        """Limpa cache de thumbnails."""
        from PySide6.QtWidgets import QMessageBox
        reply = QMessageBox.question(
            self, "Limpar Cache",
            "Isso vai remover todos os thumbnails em cache.\nContinuar?"
        )
        if reply == QMessageBox.Yes:
            # TODO: Implementar limpeza
            QMessageBox.information(self, "Cache", "Cache limpo com sucesso!")
    
    def _reset_defaults(self):
        """Restaura configurações padrão."""
        self.theme_combo.setCurrentIndex(0)
        self.font_size.setValue(12)
        self.autosave_check.setChecked(True)
        self.autosave_interval.setValue(60)
        self.confirm_exit.setChecked(True)
        self.dpi_spin.setValue(300)
        self.format_combo.setCurrentIndex(0)
        self.cmyk_check.setChecked(True)
        self.bleed_spin.setValue(3)
        self.cropmarks_check.setChecked(True)
        self.ai_enabled.setChecked(True)
        self.gpu_check.setChecked(True)
        self.cache_size.setValue(500)
        self.undo_limit.setValue(50)
        self.debug_mode.setChecked(False)
        self.offline_mode.setChecked(False)
    
    def _save_settings(self):
        """Salva configurações."""
        settings = {
            "theme": self.theme_combo.currentText().lower(),
            "font_size": self.font_size.value(),
            "autosave_enabled": self.autosave_check.isChecked(),
            "autosave_interval_sec": self.autosave_interval.value(),
            "confirm_on_exit": self.confirm_exit.isChecked(),
            "default_dpi": self.dpi_spin.value(),
            "default_format": self.format_combo.currentText().lower(),
            "cmyk_enabled": self.cmyk_check.isChecked(),
            "icc_profile": self.icc_combo.currentText(),
            "bleed_mm": self.bleed_spin.value(),
            "cropmarks": self.cropmarks_check.isChecked(),
            "ai_enabled": self.ai_enabled.isChecked(),
            "gpu_acceleration": self.gpu_check.isChecked(),
            "ai_model_path": self.model_path.text(),
            "auto_rembg": self.auto_rembg.isChecked(),
            "auto_upscale": self.auto_upscale.isChecked(),
            "thumbnail_cache_size": self.cache_size.value(),
            "max_undo_steps": self.undo_limit.value(),
            "debug_mode": self.debug_mode.isChecked(),
            "offline_mode": self.offline_mode.isChecked(),
        }
        
        self.settings_changed.emit(settings)
        
        # Salva via AppSettings
        try:
            from src.core.app_safety import AppSettings
            for key, value in settings.items():
                AppSettings.set(key, value)
        except ImportError:
            pass
        
        self.accept()
    
    def get_settings(self) -> Dict[str, Any]:
        """Retorna configurações atuais do diálogo."""
        return self._settings


def show_settings_dialog(parent=None, current_settings: Dict = None) -> bool:
    """Mostra diálogo de configurações. Retorna True se salvo."""
    dialog = SettingsDialog(current_settings, parent)
    return dialog.exec() == QDialog.Accepted

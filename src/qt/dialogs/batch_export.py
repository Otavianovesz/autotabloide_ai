"""
AutoTabloide AI - Batch Export Dialog
=====================================
PROTOCOLO DE CONVERGÊNCIA 260 - Fase 4 (Passos 191-196)
Diálogo de exportação em lote de projetos.
"""

from __future__ import annotations
from pathlib import Path
from typing import List, Dict, Optional
import logging

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QProgressBar, QPushButton, QListWidget, QListWidgetItem,
    QFileDialog, QCheckBox, QGroupBox, QSpinBox, QComboBox
)

logger = logging.getLogger("BatchExport")


class BatchExportDialog(QDialog):
    """
    Diálogo de exportação em lote.
    
    Features:
    - Lista de projetos
    - Configurações de exportação
    - Barra de progresso
    - Cancelamento
    """
    
    export_started = Signal()
    export_completed = Signal(int, int)  # success, total
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Exportar em Lote")
        self.setMinimumSize(500, 400)
        
        self._projects: List[str] = []
        self._cancelled = False
        
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Lista de projetos
        layout.addWidget(QLabel("Projetos para exportar:"))
        
        self.list_projects = QListWidget()
        layout.addWidget(self.list_projects)
        
        btn_layout = QHBoxLayout()
        self.btn_add = QPushButton("➕ Adicionar")
        self.btn_add.clicked.connect(self._add_projects)
        btn_layout.addWidget(self.btn_add)
        
        self.btn_remove = QPushButton("➖ Remover")
        self.btn_remove.clicked.connect(self._remove_selected)
        btn_layout.addWidget(self.btn_remove)
        
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
        
        # Configurações
        settings_group = QGroupBox("Configurações")
        settings_layout = QVBoxLayout(settings_group)
        
        # DPI
        dpi_layout = QHBoxLayout()
        dpi_layout.addWidget(QLabel("DPI:"))
        self.spin_dpi = QSpinBox()
        self.spin_dpi.setRange(72, 600)
        self.spin_dpi.setValue(300)
        dpi_layout.addWidget(self.spin_dpi)
        dpi_layout.addStretch()
        settings_layout.addLayout(dpi_layout)
        
        # Formato
        format_layout = QHBoxLayout()
        format_layout.addWidget(QLabel("Formato:"))
        self.combo_format = QComboBox()
        self.combo_format.addItems(["PDF (CMYK)", "PDF (RGB)", "PNG", "JPG"])
        format_layout.addWidget(self.combo_format)
        format_layout.addStretch()
        settings_layout.addLayout(format_layout)
        
        # Opções
        self.chk_bleed = QCheckBox("Adicionar sangria (3mm)")
        self.chk_bleed.setChecked(True)
        settings_layout.addWidget(self.chk_bleed)
        
        self.chk_marks = QCheckBox("Adicionar marcas de corte")
        self.chk_marks.setChecked(True)
        settings_layout.addWidget(self.chk_marks)
        
        layout.addWidget(settings_group)
        
        # Progresso
        self.progress = QProgressBar()
        self.progress.setVisible(False)
        layout.addWidget(self.progress)
        
        self.lbl_status = QLabel("")
        layout.addWidget(self.lbl_status)
        
        # Botões
        btn_row = QHBoxLayout()
        
        self.btn_export = QPushButton("📄 Exportar Todos")
        self.btn_export.clicked.connect(self._start_export)
        btn_row.addWidget(self.btn_export)
        
        self.btn_cancel = QPushButton("Cancelar")
        self.btn_cancel.clicked.connect(self.reject)
        btn_row.addWidget(self.btn_cancel)
        
        layout.addLayout(btn_row)
    
    def _add_projects(self):
        """Adiciona projetos."""
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Selecionar Projetos",
            "",
            "Projetos (*.tabloide)"
        )
        
        for f in files:
            if f not in self._projects:
                self._projects.append(f)
                item = QListWidgetItem(Path(f).name)
                item.setData(Qt.UserRole, f)
                self.list_projects.addItem(item)
    
    def _remove_selected(self):
        """Remove selecionados."""
        for item in self.list_projects.selectedItems():
            path = item.data(Qt.UserRole)
            if path in self._projects:
                self._projects.remove(path)
            self.list_projects.takeItem(self.list_projects.row(item))
    
    def _start_export(self):
        """Inicia exportação."""
        if not self._projects:
            return
        
        self.progress.setVisible(True)
        self.progress.setRange(0, len(self._projects))
        self.progress.setValue(0)
        
        self.btn_export.setEnabled(False)
        self._cancelled = False
        
        self.export_started.emit()
        
        # TODO: Implementar exportação real
        success = 0
        
        for i, project in enumerate(self._projects):
            if self._cancelled:
                break
            
            self.lbl_status.setText(f"Exportando: {Path(project).name}")
            self.progress.setValue(i + 1)
            
            # Simula processamento
            from PySide6.QtCore import QThread
            QThread.msleep(500)
            
            success += 1
        
        self.lbl_status.setText(f"Concluído: {success}/{len(self._projects)}")
        self.btn_export.setEnabled(True)
        
        self.export_completed.emit(success, len(self._projects))
    
    def get_settings(self) -> Dict:
        """Retorna configurações."""
        return {
            "dpi": self.spin_dpi.value(),
            "format": self.combo_format.currentText(),
            "add_bleed": self.chk_bleed.isChecked(),
            "add_marks": self.chk_marks.isChecked(),
        }

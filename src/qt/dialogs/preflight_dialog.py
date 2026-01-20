from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QListWidget, QListWidgetItem, QFrame
)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QIcon, QColor, QPixmap

from src.qt.core.preflight import PreflightIssue

class PreflightDialog(QDialog):
    """Dialogo de resultados do Preflight."""
    
    def __init__(self, issues: list[PreflightIssue], parent=None):
        super().__init__(parent)
        self.setWindowTitle("Verificação de Qualidade")
        self.resize(500, 400)
        self.issues = issues
        self._setup_ui()
        
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Header
        header = QLabel("Problemas Encontrados")
        header.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(header)
        
        # List
        self.list_widget = QListWidget()
        layout.addWidget(self.list_widget)
        
        errors = 0
        warnings = 0
        
        for issue in self.issues:
            item = QListWidgetItem()
            
            # Setup icon/color
            if issue.severity == 'error':
                icon = "❌"
                color = "#FF5555"
                errors += 1
            else:
                icon = "⚠️"
                color = "#F1FA8C"
                warnings += 1
                
            item.setText(f"{icon} {issue.message}")
            item.setForeground(QColor(color))
            item.setData(Qt.UserRole, issue)
            self.list_widget.addItem(item)
            
        # Summary
        summary = QLabel(f"Erros: {errors} | Avisos: {warnings}")
        if errors > 0:
            summary.setStyleSheet("color: #FF5555; margin-top: 10px;")
        else:
            summary.setStyleSheet("color: #F1FA8C; margin-top: 10px;")
        layout.addWidget(summary)
            
        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        self.btn_cancel = QPushButton("Cancelar")
        self.btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(self.btn_cancel)
        
        self.btn_export = QPushButton("Exportar Assim Mesmo")
        self.btn_export.clicked.connect(self.accept)
        
        if errors > 0:
            self.btn_export.setEnabled(False)
            self.btn_export.setToolTip("Corrija os erros antes de exportar.")
        
        btn_layout.addWidget(self.btn_export)
        layout.addLayout(btn_layout)
        
        # Double click to select item
        self.list_widget.itemDoubleClicked.connect(self._on_item_double_clicked)
        
    def _on_item_double_clicked(self, item):
        issue = item.data(Qt.UserRole)
        if issue and issue.item:
            # Select item in scene
            for i in issue.item.scene().items():
                i.setSelected(False)
            issue.item.setSelected(True)
            # Zoom to item logic could be added here
            self.reject() # Close to let user fix

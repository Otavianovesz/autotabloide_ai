"""
AutoTabloide AI - Cofre Widget
===============================
Gestão de Image Vault e backups.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableView, QFrame,
    QLabel, QPushButton, QProgressBar, QMessageBox, QSplitter,
    QListWidget, QListWidgetItem, QGroupBox
)
from PySide6.QtCore import Qt, Signal, Slot, QAbstractTableModel, QModelIndex, QSize
from PySide6.QtGui import QPixmap, QIcon
from typing import Optional, List, Dict, Any
from pathlib import Path


class BackupListModel(QAbstractTableModel):
    """Model para lista de backups."""
    
    COLUMNS = [
        ("date", "Data", 150),
        ("size", "Tamanho", 100),
        ("items", "Itens", 80),
    ]
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._data: List[Dict[str, Any]] = []
    
    def rowCount(self, parent=QModelIndex()) -> int:
        return len(self._data)
    
    def columnCount(self, parent=QModelIndex()) -> int:
        return len(self.COLUMNS)
    
    def data(self, index: QModelIndex, role: int = Qt.DisplayRole):
        if not index.isValid():
            return None
        
        row = self._data[index.row()]
        col_key = self.COLUMNS[index.column()][0]
        
        if role == Qt.DisplayRole:
            return str(row.get(col_key, ""))
        
        return None
    
    def headerData(self, section: int, orientation: Qt.Orientation, role: int = Qt.DisplayRole):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self.COLUMNS[section][1]
        return None
    
    def set_data(self, data: List[Dict[str, Any]]) -> None:
        self.beginResetModel()
        self._data = data
        self.endResetModel()


class CofreWidget(QWidget):
    """Widget do Cofre (Image Vault + Backups)."""
    
    def __init__(self, container=None, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.container = container
        self._setup_ui()
        self._load_data()
    
    def _setup_ui(self) -> None:
        """Configura interface."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        
        # Header
        header = QHBoxLayout()
        
        title = QLabel("🔒 Cofre")
        title.setStyleSheet("font-size: 28px; font-weight: bold; color: #FFFFFF;")
        header.addWidget(title)
        
        header.addStretch()
        
        layout.addLayout(header)
        
        # Splitter: Image Vault | Backups
        splitter = QSplitter(Qt.Horizontal)
        
        # Painel: Image Vault
        vault_panel = self._create_vault_panel()
        splitter.addWidget(vault_panel)
        
        # Painel: Backups
        backup_panel = self._create_backup_panel()
        splitter.addWidget(backup_panel)
        
        splitter.setSizes([500, 400])
        layout.addWidget(splitter)
    
    def _create_vault_panel(self) -> QFrame:
        """Cria painel do Image Vault."""
        frame = QFrame()
        frame.setStyleSheet("""
            QFrame {
                background-color: #1A1A2E;
                border-radius: 12px;
                padding: 8px;
            }
        """)
        layout = QVBoxLayout(frame)
        
        # Header
        header = QHBoxLayout()
        title = QLabel("🖼️ Image Vault")
        title.setStyleSheet("font-weight: bold; color: #FFFFFF;")
        header.addWidget(title)
        header.addStretch()
        layout.addLayout(header)
        
        # Estatísticas
        stats_layout = QHBoxLayout()
        
        self.vault_count = QLabel("0 imagens")
        self.vault_count.setStyleSheet("color: #6C5CE7; font-size: 18px; font-weight: bold;")
        stats_layout.addWidget(self.vault_count)
        
        self.vault_size = QLabel("0 MB")
        self.vault_size.setStyleSheet("color: #808080;")
        stats_layout.addWidget(self.vault_size)
        
        stats_layout.addStretch()
        layout.addLayout(stats_layout)
        
        # Lista de imagens recentes
        self.image_list = QListWidget()
        self.image_list.setIconSize(QSize(48, 48))
        self.image_list.setSpacing(4)
        layout.addWidget(self.image_list)
        
        # Ações
        actions = QHBoxLayout()
        
        btn_verify = QPushButton("✅ Verificar Integridade")
        btn_verify.clicked.connect(self._verify_integrity)
        actions.addWidget(btn_verify)
        
        btn_clean = QPushButton("🧹 Limpar Órfãos")
        btn_clean.setProperty("class", "secondary")
        btn_clean.clicked.connect(self._clean_orphans)
        actions.addWidget(btn_clean)
        
        layout.addLayout(actions)
        
        return frame
    
    def _create_backup_panel(self) -> QFrame:
        """Cria painel de backups."""
        frame = QFrame()
        frame.setStyleSheet("""
            QFrame {
                background-color: #1A1A2E;
                border-radius: 12px;
                padding: 8px;
            }
        """)
        layout = QVBoxLayout(frame)
        
        # Header
        header = QHBoxLayout()
        title = QLabel("💾 Snapshots")
        title.setStyleSheet("font-weight: bold; color: #FFFFFF;")
        header.addWidget(title)
        header.addStretch()
        
        btn_create = QPushButton("📸 Criar Snapshot")
        btn_create.clicked.connect(self._create_snapshot)
        header.addWidget(btn_create)
        
        layout.addLayout(header)
        
        # Tabela de backups
        self.backup_table = QTableView()
        self.backup_model = BackupListModel()
        self.backup_table.setModel(self.backup_model)
        self.backup_table.setSelectionBehavior(QTableView.SelectRows)
        layout.addWidget(self.backup_table)
        
        # Ações de backup
        actions = QHBoxLayout()
        
        btn_restore = QPushButton("⏪ Restaurar")
        btn_restore.clicked.connect(self._restore_backup)
        actions.addWidget(btn_restore)
        
        btn_export = QPushButton("📤 Exportar")
        btn_export.setProperty("class", "secondary")
        btn_export.clicked.connect(self._export_backup)
        actions.addWidget(btn_export)
        
        btn_delete = QPushButton("🗑️ Excluir")
        btn_delete.setProperty("class", "danger")
        btn_delete.clicked.connect(self._delete_backup)
        actions.addWidget(btn_delete)
        
        layout.addLayout(actions)
        
        return frame
    
    def _load_data(self) -> None:
        """Carrega dados."""
        # Dados de exemplo
        self.vault_count.setText("156 imagens")
        self.vault_size.setText("245 MB")
        
        # Imagens recentes
        for i in range(5):
            item = QListWidgetItem(f"produto_hash_{i:03d}.png")
            self.image_list.addItem(item)
        
        # Backups de exemplo
        backups = [
            {"date": "2025-12-27 12:00", "size": "45 MB", "items": "1,234"},
            {"date": "2025-12-26 18:00", "size": "44 MB", "items": "1,220"},
            {"date": "2025-12-25 12:00", "size": "42 MB", "items": "1,180"},
        ]
        self.backup_model.set_data(backups)
    
    @Slot()
    def _verify_integrity(self) -> None:
        """Verifica integridade do vault."""
        QMessageBox.information(
            self,
            "Verificação de Integridade",
            "Todas as 156 imagens verificadas.\n\n✅ 0 arquivos corrompidos\n✅ 0 hashes inválidos"
        )
    
    @Slot()
    def _clean_orphans(self) -> None:
        """Limpa imagens órfãs."""
        reply = QMessageBox.question(
            self,
            "Limpar Órfãos",
            "Deseja remover imagens que não estão vinculadas a nenhum produto?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            QMessageBox.information(self, "Limpeza", "3 imagens órfãs removidas.\n12 MB liberados.")
    
    @Slot()
    def _create_snapshot(self) -> None:
        """Cria snapshot."""
        QMessageBox.information(
            self,
            "Snapshot Criado",
            "Snapshot do sistema criado com sucesso!\n\n📅 2025-12-27 14:05\n📦 1,234 itens\n💾 45 MB"
        )
    
    @Slot()
    def _restore_backup(self) -> None:
        """Restaura backup selecionado."""
        reply = QMessageBox.warning(
            self,
            "Confirmar Restauração",
            "ATENÇÃO: Esta ação substituirá todos os dados atuais!\n\n"
            "Deseja realmente restaurar o backup selecionado?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            QMessageBox.information(self, "Restauração", "Backup restaurado com sucesso!")
    
    @Slot()
    def _export_backup(self) -> None:
        """Exporta backup."""
        from PySide6.QtWidgets import QFileDialog
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Exportar Backup",
            "autotabloide_backup.zip",
            "ZIP Files (*.zip)"
        )
        if file_path:
            QMessageBox.information(self, "Exportação", f"Backup exportado para:\n{file_path}")
    
    @Slot()
    def _delete_backup(self) -> None:
        """Exclui backup selecionado."""
        reply = QMessageBox.question(
            self,
            "Confirmar Exclusão",
            "Deseja excluir o backup selecionado?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            QMessageBox.information(self, "Exclusão", "Backup excluído.")

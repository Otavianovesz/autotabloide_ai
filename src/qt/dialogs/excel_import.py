"""
AutoTabloide AI - Excel Import Dialog
=====================================
PROTOCOLO DE RETIFICAÇÃO NÍVEL 0 - Fase 2 (Passos 63-65)
Importação de planilhas Excel com progresso.
"""

from __future__ import annotations
from pathlib import Path
from typing import Dict, List, Optional
import logging

from PySide6.QtCore import Qt, Signal, Slot, QThread
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QProgressBar, QFileDialog,
    QTableWidget, QTableWidgetItem, QTextEdit,
    QCheckBox, QComboBox, QSpinBox
)

logger = logging.getLogger("ExcelImport")


# =============================================================================
# IMPORT WORKER
# =============================================================================

class ExcelImportWorker(QThread):
    """Worker para importar Excel em background."""
    
    progress = Signal(int, str)  # percent, message
    row_imported = Signal(dict)  # row data
    finished = Signal(bool, int, str)  # success, count, message
    
    def __init__(self, file_path: str, mapping: Dict, parent=None):
        super().__init__(parent)
        self.file_path = file_path
        self.mapping = mapping
        self._cancelled = False
    
    def run(self):
        try:
            import pandas as pd
            
            self.progress.emit(10, "Lendo arquivo...")
            
            # Lê Excel
            df = pd.read_excel(self.file_path)
            total = len(df)
            
            if total == 0:
                self.finished.emit(False, 0, "Planilha vazia")
                return
            
            self.progress.emit(20, f"Processando {total} linhas...")
            
            imported = 0
            for i, row in df.iterrows():
                if self._cancelled:
                    self.finished.emit(False, imported, "Cancelado pelo usuário")
                    return
                
                # Mapeia colunas
                product_data = {}
                for field, column in self.mapping.items():
                    if column and column in row:
                        product_data[field] = row[column]
                
                if product_data.get("nome_sanitizado"):
                    self.row_imported.emit(product_data)
                    imported += 1
                
                # Atualiza progresso
                percent = int(20 + (i / total) * 70)
                self.progress.emit(percent, f"Importando {i+1}/{total}...")
            
            self.progress.emit(100, "Concluído!")
            self.finished.emit(True, imported, f"{imported} produtos importados")
            
        except ImportError:
            self.finished.emit(False, 0, "pandas não instalado")
        except Exception as e:
            logger.error(f"Erro na importação: {e}")
            self.finished.emit(False, 0, str(e))
    
    def cancel(self):
        self._cancelled = True


# =============================================================================
# IMPORT DIALOG
# =============================================================================

class ExcelImportDialog(QDialog):
    """
    Diálogo para importar produtos de Excel.
    
    Features:
    - Preview de colunas
    - Mapeamento de campos
    - Barra de progresso
    - Validação prévia
    """
    
    import_completed = Signal(int)  # count
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Importar Planilha Excel")
        self.setMinimumSize(700, 550)
        
        self._file_path: Optional[str] = None
        self._columns: List[str] = []
        self._worker: Optional[ExcelImportWorker] = None
        
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        
        # File selection
        file_layout = QHBoxLayout()
        file_layout.addWidget(QLabel("Arquivo:"))
        
        self.file_label = QLabel("Nenhum arquivo selecionado")
        self.file_label.setStyleSheet("color: #808080;")
        file_layout.addWidget(self.file_label, 1)
        
        btn_browse = QPushButton("Procurar...")
        btn_browse.clicked.connect(self._browse_file)
        file_layout.addWidget(btn_browse)
        
        layout.addLayout(file_layout)
        
        # Mapping section
        layout.addWidget(QLabel("Mapeamento de Colunas:"))
        
        self.mapping_table = QTableWidget(6, 2)
        self.mapping_table.setHorizontalHeaderLabels(["Campo", "Coluna Excel"])
        self.mapping_table.setColumnWidth(0, 200)
        self.mapping_table.setColumnWidth(1, 300)
        
        fields = [
            ("nome_sanitizado", "Nome do Produto *"),
            ("preco_venda_atual", "Preço de Venda"),
            ("preco_referencia", "Preço Anterior"),
            ("marca_normalizada", "Marca"),
            ("detalhe_peso", "Peso/Tamanho"),
            ("sku_origem", "SKU / Código"),
        ]
        
        self.mapping_combos = {}
        for i, (field, label) in enumerate(fields):
            self.mapping_table.setItem(i, 0, QTableWidgetItem(label))
            combo = QComboBox()
            combo.addItem("-- Selecione --")
            self.mapping_combos[field] = combo
            self.mapping_table.setCellWidget(i, 1, combo)
        
        layout.addWidget(self.mapping_table)
        
        # Options
        options_layout = QHBoxLayout()
        
        self.skip_first = QCheckBox("Pular primeira linha (cabeçalho)")
        self.skip_first.setChecked(True)
        options_layout.addWidget(self.skip_first)
        
        options_layout.addStretch()
        
        options_layout.addWidget(QLabel("Limite:"))
        self.limit_spin = QSpinBox()
        self.limit_spin.setRange(0, 10000)
        self.limit_spin.setValue(0)
        self.limit_spin.setSpecialValueText("Sem limite")
        options_layout.addWidget(self.limit_spin)
        
        layout.addLayout(options_layout)
        
        # Progress
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        self.status_label = QLabel("")
        layout.addWidget(self.status_label)
        
        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        self.btn_cancel = QPushButton("Cancelar")
        self.btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(self.btn_cancel)
        
        self.btn_import = QPushButton("Importar")
        self.btn_import.setEnabled(False)
        self.btn_import.clicked.connect(self._start_import)
        btn_layout.addWidget(self.btn_import)
        
        layout.addLayout(btn_layout)
    
    def _browse_file(self):
        """Abre diálogo para selecionar arquivo."""
        path, _ = QFileDialog.getOpenFileName(
            self, "Selecionar Planilha",
            "", "Excel Files (*.xlsx *.xls);;CSV Files (*.csv)"
        )
        
        if path:
            self._file_path = path
            self.file_label.setText(Path(path).name)
            self._load_columns()
    
    def _load_columns(self):
        """Carrega colunas do arquivo."""
        try:
            import pandas as pd
            
            df = pd.read_excel(self._file_path, nrows=0)
            self._columns = list(df.columns)
            
            # Atualiza combos
            for combo in self.mapping_combos.values():
                combo.clear()
                combo.addItem("-- Selecione --")
                combo.addItems(self._columns)
            
            # Auto-mapeia se possível
            self._auto_map()
            
            self.btn_import.setEnabled(True)
            self.status_label.setText(f"✓ {len(self._columns)} colunas encontradas")
            
        except Exception as e:
            self.status_label.setText(f"❌ Erro ao ler: {e}")
    
    def _auto_map(self):
        """Tenta mapear automaticamente."""
        mappings = {
            "nome_sanitizado": ["nome", "product", "produto", "descricao"],
            "preco_venda_atual": ["preco", "price", "valor"],
            "marca_normalizada": ["marca", "brand"],
            "sku_origem": ["sku", "codigo", "code"],
        }
        
        for field, keywords in mappings.items():
            combo = self.mapping_combos.get(field)
            if not combo:
                continue
            
            for i, col in enumerate(self._columns):
                col_lower = col.lower()
                if any(kw in col_lower for kw in keywords):
                    combo.setCurrentIndex(i + 1)
                    break
    
    def _start_import(self):
        """Inicia importação."""
        # Coleta mapeamento
        mapping = {}
        for field, combo in self.mapping_combos.items():
            idx = combo.currentIndex()
            if idx > 0:
                mapping[field] = self._columns[idx - 1]
        
        if "nome_sanitizado" not in mapping:
            self.status_label.setText("❌ Campo 'Nome' é obrigatório")
            return
        
        # Inicia worker
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.btn_import.setEnabled(False)
        
        self._worker = ExcelImportWorker(self._file_path, mapping)
        self._worker.progress.connect(self._on_progress)
        self._worker.finished.connect(self._on_finished)
        self._worker.start()
    
    @Slot(int, str)
    def _on_progress(self, percent: int, message: str):
        self.progress_bar.setValue(percent)
        self.status_label.setText(message)
    
    @Slot(bool, int, str)
    def _on_finished(self, success: bool, count: int, message: str):
        self.progress_bar.setVisible(False)
        
        if success:
            self.status_label.setText(f"✅ {message}")
            self.import_completed.emit(count)
            self.accept()
        else:
            self.status_label.setText(f"❌ {message}")
            self.btn_import.setEnabled(True)


def show_excel_import_dialog(parent=None) -> int:
    """Mostra diálogo de importação. Retorna número de produtos importados."""
    dialog = ExcelImportDialog(parent)
    if dialog.exec() == QDialog.Accepted:
        return dialog._worker._imported if dialog._worker else 0
    return 0

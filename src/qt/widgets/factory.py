"""
AutoTabloide AI - Factory Widget (Producao em Massa)
=====================================================
Interface para geracao de PDFs com imposicao automatica.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QFrame,
    QLabel, QPushButton, QListWidget, QListWidgetItem, QComboBox,
    QSpinBox, QCheckBox, QProgressBar, QFileDialog, QMessageBox,
    QSplitter, QGroupBox, QScrollArea
)
from PySide6.QtCore import Qt, Signal, Slot, QSize, QThread
from PySide6.QtGui import QColor, QPixmap, QPainter
from typing import Optional, List, Dict, Any
from pathlib import Path


class RenderWorkerThread(QThread):
    """Thread worker para renderizacao."""
    
    progress = Signal(int, int, str)  # current, total, message
    finished = Signal(str)  # output_path
    error = Signal(str)
    
    def __init__(self, slots_data: Dict, layout_path: str, output_path: str, parent=None):
        super().__init__(parent)
        self.slots_data = slots_data
        self.layout_path = layout_path
        self.output_path = output_path
    
    def run(self):
        try:
            from src.qt.rendering import SVGEngine
            
            self.progress.emit(10, 100, "Carregando template SVG...")
            
            engine = SVGEngine()
            if not engine.load(self.layout_path):
                self.error.emit("Falha ao carregar template")
                return
            
            self.progress.emit(30, 100, "Injetando dados dos produtos...")
            engine.inject_products(self.slots_data)
            
            self.progress.emit(60, 100, "Gerando PDF...")
            
            if self.output_path.endswith('.pdf'):
                success = engine.render_to_pdf(self.output_path)
            else:
                success = engine.render_to_png(self.output_path)
            
            if success:
                self.progress.emit(100, 100, "Concluido!")
                self.finished.emit(self.output_path)
            else:
                self.error.emit("Falha na renderizacao")
                
        except Exception as e:
            self.error.emit(str(e))


class ImpositionPreview(QFrame):
    """Preview de imposicao N-Up."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(200, 283)  # Proporcao A4
        self.setStyleSheet("""
            QFrame {
                background-color: #FFFFFF;
                border: 1px solid #2D2D44;
                border-radius: 4px;
            }
        """)
        
        self.n_up = 1
        self.pages: List[Dict] = []
    
    def set_n_up(self, n: int):
        self.n_up = n
        self.update()
    
    def set_pages(self, pages: List[Dict]):
        self.pages = pages
        self.update()
    
    def paintEvent(self, event):
        super().paintEvent(event)
        
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        w = self.width() - 20
        h = self.height() - 20
        x_offset = 10
        y_offset = 10
        
        # Grid baseado em N-Up
        if self.n_up == 1:
            rows, cols = 1, 1
        elif self.n_up == 2:
            rows, cols = 1, 2
        elif self.n_up == 4:
            rows, cols = 2, 2
        elif self.n_up == 8:
            rows, cols = 2, 4
        else:
            rows, cols = 1, 1
        
        cell_w = w / cols
        cell_h = h / rows
        
        for r in range(rows):
            for c in range(cols):
                x = x_offset + c * cell_w + 2
                y = y_offset + r * cell_h + 2
                cw = cell_w - 4
                ch = cell_h - 4
                
                painter.setPen(QColor("#2D2D44"))
                painter.setBrush(QColor("#F0F0F0"))
                painter.drawRect(int(x), int(y), int(cw), int(ch))
        
        painter.end()


class FactoryWidget(QWidget):
    """Widget da Fabrica - producao em massa de tabloides."""
    
    render_started = Signal()
    render_finished = Signal(str)
    
    def __init__(self, container=None, parent=None):
        super().__init__(parent)
        self.container = container
        self._render_worker: Optional[RenderWorkerThread] = None
        self._setup_ui()
        self._load_products()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        
        # Header
        header = QHBoxLayout()
        
        title = QLabel("Fabrica de Tabloides")
        title.setStyleSheet("font-size: 28px; font-weight: bold; color: #FFFFFF;")
        header.addWidget(title)
        
        header.addStretch()
        
        self.btn_render = QPushButton("Gerar PDF")
        self.btn_render.clicked.connect(self._start_render)
        header.addWidget(self.btn_render)
        
        layout.addLayout(header)
        
        # Splitter principal
        splitter = QSplitter(Qt.Horizontal)
        
        # === Painel Esquerdo: Selecao de Produtos ===
        left_panel = QFrame()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        
        left_layout.addWidget(QLabel("Produtos para Tabloide:"))
        
        self.product_list = QListWidget()
        self.product_list.setSelectionMode(QListWidget.ExtendedSelection)
        left_layout.addWidget(self.product_list)
        
        btn_layout = QHBoxLayout()
        
        btn_add = QPushButton("Adicionar")
        btn_add.clicked.connect(self._add_product)
        btn_layout.addWidget(btn_add)
        
        btn_remove = QPushButton("Remover")
        btn_remove.clicked.connect(self._remove_product)
        btn_layout.addWidget(btn_remove)
        
        btn_clear = QPushButton("Limpar")
        btn_clear.clicked.connect(self._clear_products)
        btn_layout.addWidget(btn_clear)
        
        left_layout.addLayout(btn_layout)
        
        splitter.addWidget(left_panel)
        
        # === Painel Central: Configuracoes ===
        center_panel = QFrame()
        center_layout = QVBoxLayout(center_panel)
        
        # Layout
        layout_group = QGroupBox("Template")
        lg_layout = QVBoxLayout(layout_group)
        
        self.layout_combo = QComboBox()
        self.layout_combo.addItem("Tabloide A4 - 12 produtos (3x4)")
        self.layout_combo.addItem("Tabloide A4 - 6 produtos (2x3)")
        self.layout_combo.addItem("Tabloide A3 - 24 produtos")
        lg_layout.addWidget(self.layout_combo)
        
        center_layout.addWidget(layout_group)
        
        # Papel
        paper_group = QGroupBox("Papel e Impressao")
        pg_layout = QGridLayout(paper_group)
        
        pg_layout.addWidget(QLabel("Tamanho:"), 0, 0)
        self.paper_combo = QComboBox()
        self.paper_combo.addItems(["A4 (210x297mm)", "A3 (297x420mm)", "Carta (216x279mm)"])
        pg_layout.addWidget(self.paper_combo, 0, 1)
        
        pg_layout.addWidget(QLabel("DPI:"), 1, 0)
        self.dpi_spin = QSpinBox()
        self.dpi_spin.setRange(72, 600)
        self.dpi_spin.setValue(300)
        pg_layout.addWidget(self.dpi_spin, 1, 1)
        
        center_layout.addWidget(paper_group)
        
        # Imposicao
        impo_group = QGroupBox("Imposicao")
        ig_layout = QVBoxLayout(impo_group)
        
        nup_layout = QHBoxLayout()
        nup_layout.addWidget(QLabel("N-Up:"))
        self.nup_combo = QComboBox()
        self.nup_combo.addItems(["1 por folha", "2 por folha", "4 por folha", "8 por folha"])
        self.nup_combo.currentIndexChanged.connect(self._on_nup_changed)
        nup_layout.addWidget(self.nup_combo)
        ig_layout.addLayout(nup_layout)
        
        self.chk_crop_marks = QCheckBox("Marcas de corte")
        self.chk_crop_marks.setChecked(True)
        ig_layout.addWidget(self.chk_crop_marks)
        
        self.chk_bleed = QCheckBox("Bleed (3mm)")
        self.chk_bleed.setChecked(True)
        ig_layout.addWidget(self.chk_bleed)
        
        self.chk_cmyk = QCheckBox("Converter para CMYK")
        ig_layout.addWidget(self.chk_cmyk)
        
        center_layout.addWidget(impo_group)
        
        center_layout.addStretch()
        
        splitter.addWidget(center_panel)
        
        # === Painel Direito: Preview ===
        right_panel = QFrame()
        right_layout = QVBoxLayout(right_panel)
        
        right_layout.addWidget(QLabel("Preview:"))
        
        self.preview = ImpositionPreview()
        right_layout.addWidget(self.preview)
        
        self.page_info = QLabel("0 paginas")
        self.page_info.setAlignment(Qt.AlignCenter)
        self.page_info.setStyleSheet("color: #808080;")
        right_layout.addWidget(self.page_info)
        
        right_layout.addStretch()
        
        splitter.addWidget(right_panel)
        
        splitter.setSizes([300, 300, 200])
        layout.addWidget(splitter)
        
        # Progress bar
        self.progress = QProgressBar()
        self.progress.setVisible(False)
        layout.addWidget(self.progress)
        
        self.status_label = QLabel()
        self.status_label.setStyleSheet("color: #808080;")
        layout.addWidget(self.status_label)
    
    def _load_products(self):
        """Carrega produtos de exemplo."""
        products = [
            {"id": 1, "nome_sanitizado": "Arroz Camil 5kg", "preco_venda_atual": 24.90},
            {"id": 2, "nome_sanitizado": "Feijao Carioca 1kg", "preco_venda_atual": 8.99},
            {"id": 3, "nome_sanitizado": "Oleo Soja 900ml", "preco_venda_atual": 7.49},
            {"id": 4, "nome_sanitizado": "Acucar 1kg", "preco_venda_atual": 4.99},
        ]
        
        for p in products:
            item = QListWidgetItem(f"{p['nome_sanitizado']} - R$ {p['preco_venda_atual']:.2f}")
            item.setData(Qt.UserRole, p)
            self.product_list.addItem(item)
        
        self._update_page_count()
    
    def _update_page_count(self):
        count = self.product_list.count()
        slots_per_page = 12  # Depende do layout
        pages = (count + slots_per_page - 1) // slots_per_page
        self.page_info.setText(f"{pages} pagina(s) | {count} produtos")
    
    @Slot()
    def _add_product(self):
        QMessageBox.information(self, "Adicionar", "Selecione produtos do Estoque")
    
    @Slot()
    def _remove_product(self):
        for item in self.product_list.selectedItems():
            self.product_list.takeItem(self.product_list.row(item))
        self._update_page_count()
    
    @Slot()
    def _clear_products(self):
        self.product_list.clear()
        self._update_page_count()
    
    @Slot(int)
    def _on_nup_changed(self, index: int):
        nup_values = [1, 2, 4, 8]
        self.preview.set_n_up(nup_values[index])
    
    @Slot()
    def _start_render(self):
        if self.product_list.count() == 0:
            QMessageBox.warning(self, "Aviso", "Adicione produtos primeiro!")
            return
        
        output_path, _ = QFileDialog.getSaveFileName(
            self, "Salvar PDF", "tabloide.pdf", "PDF (*.pdf)"
        )
        if not output_path:
            return
        
        # Coleta dados dos produtos
        slots_data = {}
        for i in range(self.product_list.count()):
            item = self.product_list.item(i)
            product = item.data(Qt.UserRole)
            slots_data[i + 1] = product
        
        # Inicia worker
        self.progress.setVisible(True)
        self.progress.setValue(0)
        self.btn_render.setEnabled(False)
        
        # Simula renderizacao (sem template real)
        self.progress.setValue(50)
        self.status_label.setText("Gerando PDF...")
        
        # TODO: Usar RenderWorkerThread com template real
        self.progress.setValue(100)
        self.progress.setVisible(False)
        self.btn_render.setEnabled(True)
        self.status_label.setText(f"Exportado: {output_path}")
        
        QMessageBox.information(
            self, "Exportacao",
            f"PDF gerado com sucesso!\n\n{output_path}\n\n"
            "(Para renderizacao real, integre com template SVG)"
        )

"""
AutoTabloide AI - Factory Widget
=================================
Fábrica de Cartazes: Produção em massa com imposição automática.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem,
    QFrame, QLabel, QPushButton, QComboBox, QSpinBox, QGroupBox,
    QProgressBar, QCheckBox, QFileDialog, QMessageBox, QSplitter
)
from PySide6.QtCore import Qt, Signal, Slot, QSize
from PySide6.QtGui import QPixmap
from typing import Optional, List, Dict, Any


class FactoryWidget(QWidget):
    """Widget da Fábrica de Cartazes."""
    
    # Signals
    export_started = Signal()
    export_finished = Signal(str)  # path do arquivo gerado
    
    def __init__(self, container=None, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.container = container
        self._selected_products: List[Dict[str, Any]] = []
        self._setup_ui()
    
    def _setup_ui(self) -> None:
        """Configura interface."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        
        # Header
        header = QHBoxLayout()
        
        title = QLabel("🏭 Fábrica de Cartazes")
        title.setStyleSheet("font-size: 28px; font-weight: bold; color: #FFFFFF;")
        header.addWidget(title)
        
        header.addStretch()
        
        layout.addLayout(header)
        
        # Splitter: Seleção | Configuração | Preview
        splitter = QSplitter(Qt.Horizontal)
        
        # Painel 1: Seleção de Produtos
        selection_panel = self._create_selection_panel()
        splitter.addWidget(selection_panel)
        
        # Painel 2: Configurações de Exportação
        config_panel = self._create_config_panel()
        splitter.addWidget(config_panel)
        
        # Painel 3: Preview
        preview_panel = self._create_preview_panel()
        splitter.addWidget(preview_panel)
        
        splitter.setSizes([300, 250, 400])
        layout.addWidget(splitter)
        
        # Footer: Ações
        footer = QHBoxLayout()
        
        self.progress = QProgressBar()
        self.progress.setVisible(False)
        footer.addWidget(self.progress, 1)
        
        btn_export = QPushButton("📤 Gerar PDF")
        btn_export.setStyleSheet("font-size: 16px; padding: 12px 24px;")
        btn_export.clicked.connect(self._export_pdf)
        footer.addWidget(btn_export)
        
        layout.addLayout(footer)
    
    def _create_selection_panel(self) -> QFrame:
        """Cria painel de seleção de produtos."""
        frame = QFrame()
        frame.setStyleSheet("""
            QFrame {
                background-color: #1A1A2E;
                border-radius: 12px;
                padding: 8px;
            }
        """)
        layout = QVBoxLayout(frame)
        
        title = QLabel("📦 Produtos Selecionados")
        title.setStyleSheet("font-weight: bold; color: #FFFFFF;")
        layout.addWidget(title)
        
        # Botões de ação
        btn_layout = QHBoxLayout()
        
        btn_add = QPushButton("➕ Adicionar")
        btn_add.clicked.connect(self._add_products)
        btn_layout.addWidget(btn_add)
        
        btn_clear = QPushButton("🗑️ Limpar")
        btn_clear.setProperty("class", "danger")
        btn_clear.clicked.connect(self._clear_products)
        btn_layout.addWidget(btn_clear)
        
        layout.addLayout(btn_layout)
        
        # Lista de produtos
        self.product_list = QListWidget()
        self.product_list.setIconSize(QSize(32, 32))
        layout.addWidget(self.product_list)
        
        # Contador
        self.count_label = QLabel("0 produtos selecionados")
        self.count_label.setStyleSheet("color: #808080;")
        layout.addWidget(self.count_label)
        
        return frame
    
    def _create_config_panel(self) -> QFrame:
        """Cria painel de configurações."""
        frame = QFrame()
        frame.setStyleSheet("""
            QFrame {
                background-color: #1A1A2E;
                border-radius: 12px;
                padding: 8px;
            }
        """)
        layout = QVBoxLayout(frame)
        
        title = QLabel("⚙️ Configurações")
        title.setStyleSheet("font-weight: bold; color: #FFFFFF;")
        layout.addWidget(title)
        
        # Layout do cartaz
        layout_group = QGroupBox("Layout")
        layout_group_layout = QVBoxLayout(layout_group)
        
        self.layout_combo = QComboBox()
        self.layout_combo.addItem("📋 Cartaz A4")
        self.layout_combo.addItem("📋 Cartaz A3")
        self.layout_combo.addItem("📋 Etiqueta de Gôndola")
        layout_group_layout.addWidget(self.layout_combo)
        
        layout.addWidget(layout_group)
        
        # Papel de saída
        paper_group = QGroupBox("Papel de Saída")
        paper_group_layout = QVBoxLayout(paper_group)
        
        self.paper_combo = QComboBox()
        self.paper_combo.addItem("📄 A4 (210x297mm)")
        self.paper_combo.addItem("📄 A3 (297x420mm)")
        self.paper_combo.addItem("📄 Letter")
        paper_group_layout.addWidget(self.paper_combo)
        
        layout.addWidget(paper_group)
        
        # NUP (cartazes por página)
        nup_group = QGroupBox("Imposição (N-Up)")
        nup_group_layout = QHBoxLayout(nup_group)
        
        nup_group_layout.addWidget(QLabel("Cartazes por página:"))
        self.nup_spin = QSpinBox()
        self.nup_spin.setMinimum(1)
        self.nup_spin.setMaximum(8)
        self.nup_spin.setValue(2)
        nup_group_layout.addWidget(self.nup_spin)
        
        layout.addWidget(nup_group)
        
        # Opções
        options_group = QGroupBox("Opções")
        options_layout = QVBoxLayout(options_group)
        
        self.crop_marks_check = QCheckBox("Marcas de corte")
        self.crop_marks_check.setChecked(True)
        options_layout.addWidget(self.crop_marks_check)
        
        self.cmyk_check = QCheckBox("Converter para CMYK")
        self.cmyk_check.setChecked(True)
        options_layout.addWidget(self.cmyk_check)
        
        self.filter_unchanged = QCheckBox("Filtrar preços inalterados")
        self.filter_unchanged.setChecked(False)
        options_layout.addWidget(self.filter_unchanged)
        
        layout.addWidget(options_group)
        
        layout.addStretch()
        
        return frame
    
    def _create_preview_panel(self) -> QFrame:
        """Cria painel de preview."""
        frame = QFrame()
        frame.setStyleSheet("""
            QFrame {
                background-color: #16213e;
                border-radius: 12px;
                border: 1px solid #2D2D44;
            }
        """)
        layout = QVBoxLayout(frame)
        
        title = QLabel("👁️ Preview de Imposição")
        title.setStyleSheet("font-weight: bold; color: #FFFFFF;")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # Área de preview
        self.preview_label = QLabel("Selecione produtos e configurações\npara ver o preview")
        self.preview_label.setAlignment(Qt.AlignCenter)
        self.preview_label.setStyleSheet("""
            color: #808080;
            font-size: 14px;
            padding: 48px;
        """)
        layout.addWidget(self.preview_label, 1)
        
        # Info de imposição
        self.imposition_info = QLabel()
        self.imposition_info.setAlignment(Qt.AlignCenter)
        self.imposition_info.setStyleSheet("color: #6C5CE7;")
        layout.addWidget(self.imposition_info)
        
        return frame
    
    @Slot()
    def _add_products(self) -> None:
        """Adiciona produtos à lista."""
        # TODO: Abrir seletor de produtos do banco
        # Dados de exemplo
        sample = [
            {"id": 1, "nome_sanitizado": "Arroz Camil 5kg", "preco": 24.90},
            {"id": 2, "nome_sanitizado": "Feijão Carioca 1kg", "preco": 8.99},
            {"id": 3, "nome_sanitizado": "Óleo de Soja 900ml", "preco": 7.49},
        ]
        
        for product in sample:
            item = QListWidgetItem(
                f"{product['nome_sanitizado']} - R$ {product['preco']:.2f}"
            )
            item.setData(Qt.UserRole, product)
            self.product_list.addItem(item)
            self._selected_products.append(product)
        
        self._update_count()
        self._update_preview()
    
    @Slot()
    def _clear_products(self) -> None:
        """Limpa todos os produtos."""
        self.product_list.clear()
        self._selected_products.clear()
        self._update_count()
        self._update_preview()
    
    def _update_count(self) -> None:
        """Atualiza contador."""
        count = len(self._selected_products)
        self.count_label.setText(f"{count} produtos selecionados")
    
    def _update_preview(self) -> None:
        """Atualiza preview de imposição."""
        count = len(self._selected_products)
        nup = self.nup_spin.value()
        
        if count == 0:
            self.preview_label.setText("Selecione produtos para ver o preview")
            self.imposition_info.setText("")
        else:
            pages = (count + nup - 1) // nup  # Ceiling division
            self.preview_label.setText(f"📄 {count} cartazes\n📑 {pages} páginas")
            self.imposition_info.setText(
                f"Imposição: {nup} cartazes por página\n"
                f"Layout: {self.layout_combo.currentText()}"
            )
    
    @Slot()
    def _export_pdf(self) -> None:
        """Exporta PDF."""
        if not self._selected_products:
            QMessageBox.warning(self, "Aviso", "Selecione produtos para exportar.")
            return
        
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Salvar PDF",
            "cartazes_autotabloide.pdf",
            "PDF Files (*.pdf)"
        )
        
        if file_path:
            self.progress.setVisible(True)
            self.progress.setValue(0)
            
            # TODO: Implementar renderização real com SVG Engine
            # Simulação de progresso
            for i in range(101):
                self.progress.setValue(i)
                QApplication.processEvents()
            
            self.progress.setVisible(False)
            
            QMessageBox.information(
                self,
                "Exportação Concluída",
                f"PDF gerado com sucesso!\n\n{file_path}\n\n(Simulação - integrar SVG Engine)"
            )
            self.export_finished.emit(file_path)


# Importar QApplication para processEvents
from PySide6.QtWidgets import QApplication

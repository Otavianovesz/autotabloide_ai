"""
AutoTabloide AI - Estoque Widget
=================================
Gestão de produtos com tabela virtualizada.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableView, QLineEdit,
    QPushButton, QLabel, QFrame, QHeaderView, QAbstractItemView,
    QMenu, QFileDialog, QMessageBox
)
from PySide6.QtCore import (
    Qt, Signal, Slot, QAbstractTableModel, QModelIndex, 
    QSortFilterProxyModel, QTimer
)
from PySide6.QtGui import QColor, QIcon, QAction
from typing import Optional, List, Dict, Any


class ProductTableModel(QAbstractTableModel):
    """Model para tabela de produtos com virtualização."""
    
    COLUMNS = [
        ("id", "ID", 60),
        ("nome_sanitizado", "Nome do Produto", 250),
        ("marca_normalizada", "Marca", 120),
        ("preco_venda_atual", "Preço", 80),
        ("status_qualidade", "Status", 70),
        ("img_hash_ref", "Imagem", 80),
    ]
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._data: List[Dict[str, Any]] = []
    
    def rowCount(self, parent=QModelIndex()) -> int:
        return len(self._data)
    
    def columnCount(self, parent=QModelIndex()) -> int:
        return len(self.COLUMNS)
    
    def data(self, index: QModelIndex, role: int = Qt.DisplayRole):
        if not index.isValid() or not (0 <= index.row() < len(self._data)):
            return None
        
        row = self._data[index.row()]
        col_key = self.COLUMNS[index.column()][0]
        
        if role == Qt.DisplayRole:
            value = row.get(col_key, "")
            
            # Formatação especial para preço
            if col_key == "preco_venda_atual" and value:
                return f"R$ {float(value):.2f}"
            
            # Formatação especial para status
            if col_key == "status_qualidade":
                status_map = {0: "❌", 1: "📷", 2: "⚠️", 3: "✅"}
                return status_map.get(value, "❓")
            
            # Formatação especial para imagem
            if col_key == "img_hash_ref":
                return "🖼️" if value else "—"
            
            return str(value) if value else ""
        
        elif role == Qt.TextAlignmentRole:
            if col_key in ("preco_venda_atual", "status_qualidade", "img_hash_ref"):
                return Qt.AlignCenter
            return Qt.AlignLeft | Qt.AlignVCenter
        
        elif role == Qt.BackgroundRole:
            status = row.get("status_qualidade", 0)
            if status == 0:
                return QColor("#3D1A1A")  # Vermelho escuro
            elif status == 2:
                return QColor("#3D3A1A")  # Amarelo escuro
        
        return None
    
    def headerData(self, section: int, orientation: Qt.Orientation, role: int = Qt.DisplayRole):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self.COLUMNS[section][1]
        return None
    
    def set_data(self, data: List[Dict[str, Any]]) -> None:
        """Define os dados da tabela."""
        self.beginResetModel()
        self._data = data
        self.endResetModel()
    
    def get_row(self, row: int) -> Optional[Dict[str, Any]]:
        """Retorna dados de uma linha específica."""
        if 0 <= row < len(self._data):
            return self._data[row]
        return None
    
    def add_row(self, data: Dict[str, Any]) -> None:
        """Adiciona uma linha."""
        row = len(self._data)
        self.beginInsertRows(QModelIndex(), row, row)
        self._data.append(data)
        self.endInsertRows()
    
    def remove_row(self, row: int) -> None:
        """Remove uma linha."""
        if 0 <= row < len(self._data):
            self.beginRemoveRows(QModelIndex(), row, row)
            del self._data[row]
            self.endRemoveRows()


class EstoqueWidget(QWidget):
    """Widget de gestão de estoque."""
    
    # Signals
    product_selected = Signal(dict)
    product_double_clicked = Signal(dict)
    
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
        header_layout = QHBoxLayout()
        
        title = QLabel("Estoque de Produtos")
        title.setStyleSheet("font-size: 28px; font-weight: bold; color: #FFFFFF;")
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        # Botão de importar
        btn_import = QPushButton("📥 Importar Excel")
        btn_import.clicked.connect(self._import_excel)
        header_layout.addWidget(btn_import)
        
        # Botão de adicionar
        btn_add = QPushButton("➕ Novo Produto")
        btn_add.setProperty("class", "secondary")
        btn_add.clicked.connect(self._add_product)
        header_layout.addWidget(btn_add)
        
        layout.addLayout(header_layout)
        
        # Barra de busca e filtros
        filter_layout = QHBoxLayout()
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Buscar produtos...")
        self.search_input.textChanged.connect(self._on_search)
        self.search_input.setMinimumWidth(300)
        filter_layout.addWidget(self.search_input)
        
        # Filtros rápidos
        btn_filter_no_image = QPushButton("📷 Sem Imagem")
        btn_filter_no_image.setCheckable(True)
        btn_filter_no_image.clicked.connect(self._toggle_filter_no_image)
        filter_layout.addWidget(btn_filter_no_image)
        
        btn_filter_issues = QPushButton("⚠️ Com Problemas")
        btn_filter_issues.setCheckable(True)
        btn_filter_issues.clicked.connect(self._toggle_filter_issues)
        filter_layout.addWidget(btn_filter_issues)
        
        filter_layout.addStretch()
        
        # Contador
        self.count_label = QLabel("0 produtos")
        self.count_label.setStyleSheet("color: #808080;")
        filter_layout.addWidget(self.count_label)
        
        layout.addLayout(filter_layout)
        
        # Tabela
        self.table = QTableView()
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.table.setSortingEnabled(True)
        self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self._show_context_menu)
        self.table.doubleClicked.connect(self._on_double_click)
        
        # Model
        self.model = ProductTableModel()
        
        # Proxy para filtros
        self.proxy = QSortFilterProxyModel()
        self.proxy.setSourceModel(self.model)
        self.proxy.setFilterCaseSensitivity(Qt.CaseInsensitive)
        self.proxy.setFilterKeyColumn(-1)  # Todas as colunas
        
        self.table.setModel(self.proxy)
        
        # Configurar colunas
        header = self.table.horizontalHeader()
        for i, (_, _, width) in enumerate(ProductTableModel.COLUMNS):
            header.resizeSection(i, width)
        header.setStretchLastSection(True)
        
        layout.addWidget(self.table)
    
    def _load_data(self) -> None:
        """Carrega dados do banco."""
        # TODO: Integrar com ProductRepository via container
        # Dados de exemplo por enquanto
        sample_data = [
            {"id": 1, "nome_sanitizado": "Arroz Camil Tipo 1", "marca_normalizada": "Camil", 
             "preco_venda_atual": 24.90, "status_qualidade": 3, "img_hash_ref": "abc123"},
            {"id": 2, "nome_sanitizado": "Feijão Carioca Camil", "marca_normalizada": "Camil",
             "preco_venda_atual": 8.99, "status_qualidade": 3, "img_hash_ref": "def456"},
            {"id": 3, "nome_sanitizado": "Óleo de Soja Soya", "marca_normalizada": "Soya",
             "preco_venda_atual": 7.49, "status_qualidade": 2, "img_hash_ref": None},
            {"id": 4, "nome_sanitizado": "Açúcar Refinado União", "marca_normalizada": "União",
             "preco_venda_atual": 4.99, "status_qualidade": 1, "img_hash_ref": None},
            {"id": 5, "nome_sanitizado": "Macarrão Espaguete Barilla", "marca_normalizada": "Barilla",
             "preco_venda_atual": 6.79, "status_qualidade": 0, "img_hash_ref": None},
        ]
        self.model.set_data(sample_data)
        self._update_count()
    
    def _update_count(self) -> None:
        """Atualiza contador de produtos."""
        count = self.proxy.rowCount()
        self.count_label.setText(f"{count} produtos")
    
    @Slot(str)
    def _on_search(self, text: str) -> None:
        """Filtra produtos pela busca."""
        self.proxy.setFilterFixedString(text)
        self._update_count()
    
    @Slot()
    def _toggle_filter_no_image(self) -> None:
        """Toggle filtro de produtos sem imagem."""
        # TODO: Implementar filtro real
        pass
    
    @Slot()
    def _toggle_filter_issues(self) -> None:
        """Toggle filtro de produtos com problemas."""
        # TODO: Implementar filtro real
        pass
    
    @Slot()
    def _import_excel(self) -> None:
        """Abre diálogo para importar Excel."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Importar Planilha Excel",
            "",
            "Excel Files (*.xlsx *.xls);;All Files (*)"
        )
        if file_path:
            print(f"[Estoque] Importando: {file_path}")
            # TODO: Implementar importação real
            QMessageBox.information(
                self, 
                "Importação", 
                f"Arquivo selecionado:\n{file_path}\n\n(Importação em desenvolvimento)"
            )
    
    @Slot()
    def _add_product(self) -> None:
        """Abre diálogo para adicionar produto."""
        # TODO: Implementar diálogo de novo produto
        QMessageBox.information(self, "Novo Produto", "Funcionalidade em desenvolvimento")
    
    @Slot()
    def _show_context_menu(self, position) -> None:
        """Mostra menu de contexto."""
        index = self.table.indexAt(position)
        if not index.isValid():
            return
        
        menu = QMenu(self)
        
        action_edit = menu.addAction("✏️ Editar")
        action_image = menu.addAction("🖼️ Gerenciar Imagem")
        menu.addSeparator()
        action_delete = menu.addAction("🗑️ Excluir")
        
        action = menu.exec(self.table.viewport().mapToGlobal(position))
        
        if action == action_edit:
            self._edit_product(index)
        elif action == action_image:
            self._manage_image(index)
        elif action == action_delete:
            self._delete_product(index)
    
    @Slot(QModelIndex)
    def _on_double_click(self, index: QModelIndex) -> None:
        """Handler de double-click."""
        source_index = self.proxy.mapToSource(index)
        row_data = self.model.get_row(source_index.row())
        if row_data:
            self.product_double_clicked.emit(row_data)
            self._manage_image(index)
    
    def _edit_product(self, index: QModelIndex) -> None:
        """Edita produto selecionado."""
        source_index = self.proxy.mapToSource(index)
        row_data = self.model.get_row(source_index.row())
        if row_data:
            # TODO: Abrir diálogo de edição
            QMessageBox.information(
                self, 
                "Editar Produto", 
                f"Editando: {row_data.get('nome_sanitizado', 'N/A')}"
            )
    
    def _manage_image(self, index: QModelIndex) -> None:
        """Abre Image Handler para o produto."""
        source_index = self.proxy.mapToSource(index)
        row_data = self.model.get_row(source_index.row())
        if row_data:
            # TODO: Abrir Image Handler dialog
            QMessageBox.information(
                self, 
                "Image Handler", 
                f"Gerenciando imagem de: {row_data.get('nome_sanitizado', 'N/A')}"
            )
    
    def _delete_product(self, index: QModelIndex) -> None:
        """Exclui produto selecionado."""
        source_index = self.proxy.mapToSource(index)
        row_data = self.model.get_row(source_index.row())
        if row_data:
            reply = QMessageBox.question(
                self,
                "Confirmar Exclusão",
                f"Deseja excluir '{row_data.get('nome_sanitizado', 'N/A')}'?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                self.model.remove_row(source_index.row())
                self._update_count()

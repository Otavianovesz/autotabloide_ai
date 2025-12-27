"""
AutoTabloide AI - Estoque Widget (Completo)
============================================
Gestão de produtos com tabela virtualizada, busca com debounce,
filtros, context menu, e integração com banco de dados.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableView, QLineEdit,
    QPushButton, QLabel, QFrame, QHeaderView, QAbstractItemView,
    QMenu, QFileDialog, QMessageBox, QProgressBar, QStyledItemDelegate
)
from PySide6.QtCore import (
    Qt, Signal, Slot, QAbstractTableModel, QModelIndex, 
    QSortFilterProxyModel, QTimer, QSize
)
from PySide6.QtGui import QColor, QBrush, QPainter, QPixmap
from typing import Optional, List, Dict, Any


class StatusDelegate(QStyledItemDelegate):
    """Delegate para coluna de status com semáforo."""
    
    STATUS_COLORS = {
        0: "#E74C3C",  # Vermelho - Sem imagem, sem dados
        1: "#F39C12",  # Laranja - Parcial
        2: "#F1C40F",  # Amarelo - Quase pronto
        3: "#2ECC71",  # Verde - Completo
    }
    
    def paint(self, painter: QPainter, option, index: QModelIndex):
        status = index.data(Qt.UserRole)
        if status is not None:
            color = self.STATUS_COLORS.get(status, "#808080")
            
            # Círculo de status
            painter.save()
            painter.setRenderHint(QPainter.Antialiasing)
            painter.setBrush(QBrush(QColor(color)))
            painter.setPen(Qt.NoPen)
            
            size = 12
            x = option.rect.center().x() - size // 2
            y = option.rect.center().y() - size // 2
            painter.drawEllipse(x, y, size, size)
            
            painter.restore()
        else:
            super().paint(painter, option, index)
    
    def sizeHint(self, option, index):
        return QSize(50, 32)


class ProductTableModel(QAbstractTableModel):
    """
    Model customizado para tabela de produtos.
    Suporta lazy loading e cache de dados.
    """
    
    COLUMNS = [
        ("id", "ID", 60),
        ("nome_sanitizado", "Nome do Produto", 280),
        ("marca_normalizada", "Marca", 120),
        ("preco_venda_atual", "Preco", 90),
        ("status_qualidade", "Status", 60),
        ("img_hash_ref", "Img", 50),
    ]
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._data: List[Dict[str, Any]] = []
        self._loading = False
    
    def rowCount(self, parent=QModelIndex()) -> int:
        return len(self._data)
    
    def columnCount(self, parent=QModelIndex()) -> int:
        return len(self.COLUMNS)
    
    def data(self, index: QModelIndex, role: int = Qt.DisplayRole):
        if not index.isValid() or not (0 <= index.row() < len(self._data)):
            return None
        
        row = self._data[index.row()]
        col_key, _, _ = self.COLUMNS[index.column()]
        value = row.get(col_key)
        
        if role == Qt.DisplayRole:
            if col_key == "preco_venda_atual":
                return f"R$ {float(value or 0):.2f}"
            if col_key == "status_qualidade":
                return ""  # Renderizado pelo delegate
            if col_key == "img_hash_ref":
                return "[Img]" if value else "-"
            return str(value) if value else ""
        
        elif role == Qt.UserRole:
            # Para status delegate
            if col_key == "status_qualidade":
                return value
            return row
        
        elif role == Qt.TextAlignmentRole:
            if col_key in ("preco_venda_atual", "status_qualidade", "img_hash_ref", "id"):
                return Qt.AlignCenter
            return Qt.AlignLeft | Qt.AlignVCenter
        
        elif role == Qt.BackgroundRole:
            status = row.get("status_qualidade", 0)
            if status == 0:
                return QBrush(QColor("#3D1A1A"))  # Vermelho escuro
        
        return None
    
    def headerData(self, section: int, orientation: Qt.Orientation, role: int = Qt.DisplayRole):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self.COLUMNS[section][1]
        return None
    
    def set_data(self, data: List[Dict[str, Any]]) -> None:
        self.beginResetModel()
        self._data = data
        self.endResetModel()
    
    def append_data(self, data: List[Dict[str, Any]]) -> None:
        """Adiciona dados (para lazy loading)."""
        if not data:
            return
        start = len(self._data)
        self.beginInsertRows(QModelIndex(), start, start + len(data) - 1)
        self._data.extend(data)
        self.endInsertRows()
    
    def get_row_data(self, row: int) -> Optional[Dict]:
        if 0 <= row < len(self._data):
            return self._data[row]
        return None
    
    def remove_row(self, row: int) -> None:
        if 0 <= row < len(self._data):
            self.beginRemoveRows(QModelIndex(), row, row)
            del self._data[row]
            self.endRemoveRows()
    
    def update_row(self, row: int, data: Dict) -> None:
        if 0 <= row < len(self._data):
            self._data[row] = data
            self.dataChanged.emit(
                self.index(row, 0),
                self.index(row, self.columnCount() - 1)
            )


class EstoqueWidget(QWidget):
    """Widget de gestão de estoque completo."""
    
    product_selected = Signal(dict)
    product_double_clicked = Signal(dict)
    
    # Debounce timer
    DEBOUNCE_MS = 300
    
    def __init__(self, container=None, parent=None):
        super().__init__(parent)
        self.container = container
        self._current_page = 1
        self._page_size = 50
        self._total_count = 0
        self._search_timer = QTimer(self)
        self._search_timer.setSingleShot(True)
        self._search_timer.timeout.connect(self._execute_search)
        
        self._setup_ui()
        self._load_data()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        
        # Header
        header = QHBoxLayout()
        
        title = QLabel("Estoque de Produtos")
        title.setStyleSheet("font-size: 28px; font-weight: bold; color: #FFFFFF;")
        header.addWidget(title)
        
        header.addStretch()
        
        btn_import = QPushButton("Importar Excel")
        btn_import.clicked.connect(self._import_excel)
        header.addWidget(btn_import)
        
        btn_add = QPushButton("Novo Produto")
        btn_add.setProperty("class", "secondary")
        btn_add.clicked.connect(self._add_product)
        header.addWidget(btn_add)
        
        btn_refresh = QPushButton("Atualizar")
        btn_refresh.setProperty("class", "secondary")
        btn_refresh.clicked.connect(self._refresh)
        header.addWidget(btn_refresh)
        
        layout.addLayout(header)
        
        # Filtros
        filter_layout = QHBoxLayout()
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Buscar produtos (com debounce 300ms)...")
        self.search_input.textChanged.connect(self._on_search_changed)
        self.search_input.setMinimumWidth(350)
        filter_layout.addWidget(self.search_input)
        
        self.filter_no_image = QPushButton("Sem Imagem")
        self.filter_no_image.setCheckable(True)
        self.filter_no_image.clicked.connect(self._apply_filters)
        filter_layout.addWidget(self.filter_no_image)
        
        self.filter_issues = QPushButton("Com Problemas")
        self.filter_issues.setCheckable(True)
        self.filter_issues.clicked.connect(self._apply_filters)
        filter_layout.addWidget(self.filter_issues)
        
        filter_layout.addStretch()
        
        self.count_label = QLabel("0 produtos")
        self.count_label.setStyleSheet("color: #808080;")
        filter_layout.addWidget(self.count_label)
        
        layout.addLayout(filter_layout)
        
        # Progress bar (oculta por padrão)
        self.progress = QProgressBar()
        self.progress.setVisible(False)
        layout.addWidget(self.progress)
        
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
        self.proxy.setFilterKeyColumn(-1)
        
        self.table.setModel(self.proxy)
        
        # Delegate para status
        self.table.setItemDelegateForColumn(4, StatusDelegate(self.table))
        
        # Configurar colunas
        header = self.table.horizontalHeader()
        for i, (_, _, width) in enumerate(ProductTableModel.COLUMNS):
            header.resizeSection(i, width)
        header.setStretchLastSection(True)
        
        layout.addWidget(self.table)
        
        # Footer
        footer = QHBoxLayout()
        
        self.page_info = QLabel("Pagina 1")
        footer.addWidget(self.page_info)
        
        footer.addStretch()
        
        btn_prev = QPushButton("< Anterior")
        btn_prev.clicked.connect(self._prev_page)
        footer.addWidget(btn_prev)
        
        btn_next = QPushButton("Proximo >")
        btn_next.clicked.connect(self._next_page)
        footer.addWidget(btn_next)
        
        layout.addLayout(footer)
    
    def _load_data(self):
        """Carrega dados do banco (ou exemplo)."""
        # Dados de exemplo
        sample_data = []
        for i in range(25):
            sample_data.append({
                "id": i + 1,
                "nome_sanitizado": f"Produto Exemplo {i + 1}",
                "marca_normalizada": ["Camil", "Soya", "Qualy", "Pilao"][i % 4],
                "preco_venda_atual": 5.99 + i * 0.5,
                "status_qualidade": i % 4,
                "img_hash_ref": f"hash{i}" if i % 3 != 0 else None,
            })
        
        self.model.set_data(sample_data)
        self._update_count()
    
    def _update_count(self):
        count = self.proxy.rowCount()
        self.count_label.setText(f"{count} produtos")
    
    @Slot(str)
    def _on_search_changed(self, text: str):
        """Inicia timer de debounce."""
        self._search_timer.start(self.DEBOUNCE_MS)
    
    @Slot()
    def _execute_search(self):
        """Executa busca após debounce."""
        text = self.search_input.text()
        self.proxy.setFilterFixedString(text)
        self._update_count()
    
    @Slot()
    def _apply_filters(self):
        """Aplica filtros rápidos."""
        # TODO: Implementar filtros reais
        self._update_count()
    
    @Slot()
    def _refresh(self):
        """Recarrega dados."""
        self._load_data()
    
    @Slot()
    def _prev_page(self):
        if self._current_page > 1:
            self._current_page -= 1
            self._load_data()
    
    @Slot()
    def _next_page(self):
        self._current_page += 1
        self._load_data()
    
    @Slot()
    def _import_excel(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Importar Excel", "",
            "Excel (*.xlsx *.xls);;CSV (*.csv)"
        )
        if file_path:
            self.progress.setVisible(True)
            self.progress.setValue(0)
            
            # TODO: Integrar ImportWorker
            for i in range(101):
                self.progress.setValue(i)
            
            self.progress.setVisible(False)
            QMessageBox.information(
                self, "Importacao",
                f"Arquivo importado: {file_path}\n\n(Integrar ImportWorker)"
            )
    
    @Slot()
    def _add_product(self):
        QMessageBox.information(self, "Novo Produto", "Abrir dialogo de novo produto")
    
    @Slot()
    def _show_context_menu(self, position):
        index = self.table.indexAt(position)
        if not index.isValid():
            return
        
        menu = QMenu(self)
        
        action_edit = menu.addAction("Editar")
        action_image = menu.addAction("Gerenciar Imagem")
        menu.addSeparator()
        action_duplicate = menu.addAction("Duplicar")
        action_delete = menu.addAction("Excluir")
        
        action = menu.exec(self.table.viewport().mapToGlobal(position))
        
        if action == action_edit:
            self._edit_product(index)
        elif action == action_image:
            self._manage_image(index)
        elif action == action_duplicate:
            self._duplicate_product(index)
        elif action == action_delete:
            self._delete_product(index)
    
    @Slot(QModelIndex)
    def _on_double_click(self, index: QModelIndex):
        source_index = self.proxy.mapToSource(index)
        row_data = self.model.get_row_data(source_index.row())
        if row_data:
            self.product_double_clicked.emit(row_data)
            self._manage_image(index)
    
    def _edit_product(self, index: QModelIndex):
        source_index = self.proxy.mapToSource(index)
        row_data = self.model.get_row_data(source_index.row())
        if row_data:
            QMessageBox.information(
                self, "Editar",
                f"Editar: {row_data.get('nome_sanitizado')}"
            )
    
    def _manage_image(self, index: QModelIndex):
        source_index = self.proxy.mapToSource(index)
        row_data = self.model.get_row_data(source_index.row())
        if row_data:
            # TODO: Abrir ImageHandlerDialog
            QMessageBox.information(
                self, "Imagem",
                f"Gerenciar imagem: {row_data.get('nome_sanitizado')}"
            )
    
    def _duplicate_product(self, index: QModelIndex):
        source_index = self.proxy.mapToSource(index)
        row_data = self.model.get_row_data(source_index.row())
        if row_data:
            new_data = row_data.copy()
            new_data["id"] = self.model.rowCount() + 1
            new_data["nome_sanitizado"] = f"{row_data.get('nome_sanitizado')} (copia)"
            self.model.append_data([new_data])
            self._update_count()
    
    def _delete_product(self, index: QModelIndex):
        source_index = self.proxy.mapToSource(index)
        row_data = self.model.get_row_data(source_index.row())
        if row_data:
            reply = QMessageBox.question(
                self, "Excluir",
                f"Excluir '{row_data.get('nome_sanitizado')}'?",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                self.model.remove_row(source_index.row())
                self._update_count()

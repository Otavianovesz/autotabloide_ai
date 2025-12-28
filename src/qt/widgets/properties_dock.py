"""
AutoTabloide AI - Properties Dock
=================================
PROTOCOLO DE RETIFICAÇÃO NÍVEL 0 - Fase 3 (Passo 127)
Dock de propriedades para editar itens selecionados.
"""

from __future__ import annotations
from typing import Dict, Optional, Any
import logging

from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtWidgets import (
    QDockWidget, QWidget, QVBoxLayout, QHBoxLayout,
    QFormLayout, QLabel, QLineEdit, QDoubleSpinBox,
    QSpinBox, QComboBox, QPushButton, QGroupBox,
    QScrollArea, QFrame
)

logger = logging.getLogger("Properties")


class PropertiesDock(QDockWidget):
    """
    Dock de propriedades para o item selecionado no Atelier.
    
    Features:
    - Edição de posição/tamanho
    - Edição de preço inline
    - Seletor de fonte/cor
    - Aplicar a todos similares
    """
    
    property_changed = Signal(str, str, object)  # item_id, property, value
    apply_to_all = Signal(str, object)  # property, value
    
    def __init__(self, parent=None):
        super().__init__("📐 Propriedades", parent)
        self.setObjectName("PropertiesDock")
        self.setAllowedAreas(Qt.RightDockWidgetArea | Qt.LeftDockWidgetArea)
        self.setMinimumWidth(280)
        
        self._current_item = None
        self._current_data: Dict = {}
        
        self._setup_ui()
    
    def _setup_ui(self):
        # Scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(12)
        
        # No selection
        self.no_selection = QLabel("Nenhum item selecionado")
        self.no_selection.setStyleSheet("color: #808080; padding: 20px;")
        self.no_selection.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.no_selection)
        
        # Properties container
        self.props_widget = QWidget()
        self.props_widget.setVisible(False)
        props_layout = QVBoxLayout(self.props_widget)
        props_layout.setContentsMargins(0, 0, 0, 0)
        
        # Item info
        info_group = QGroupBox("Item")
        info_layout = QFormLayout(info_group)
        
        self.lbl_type = QLabel("Slot")
        info_layout.addRow("Tipo:", self.lbl_type)
        
        self.lbl_id = QLabel("-")
        info_layout.addRow("ID:", self.lbl_id)
        
        props_layout.addWidget(info_group)
        
        # Position
        pos_group = QGroupBox("Posição")
        pos_layout = QFormLayout(pos_group)
        
        self.spin_x = QDoubleSpinBox()
        self.spin_x.setRange(-10000, 10000)
        self.spin_x.setSuffix(" px")
        self.spin_x.valueChanged.connect(lambda v: self._on_prop_changed("x", v))
        pos_layout.addRow("X:", self.spin_x)
        
        self.spin_y = QDoubleSpinBox()
        self.spin_y.setRange(-10000, 10000)
        self.spin_y.setSuffix(" px")
        self.spin_y.valueChanged.connect(lambda v: self._on_prop_changed("y", v))
        pos_layout.addRow("Y:", self.spin_y)
        
        props_layout.addWidget(pos_group)
        
        # Size
        size_group = QGroupBox("Tamanho")
        size_layout = QFormLayout(size_group)
        
        self.spin_w = QDoubleSpinBox()
        self.spin_w.setRange(10, 5000)
        self.spin_w.setSuffix(" px")
        self.spin_w.valueChanged.connect(lambda v: self._on_prop_changed("width", v))
        size_layout.addRow("Largura:", self.spin_w)
        
        self.spin_h = QDoubleSpinBox()
        self.spin_h.setRange(10, 5000)
        self.spin_h.setSuffix(" px")
        self.spin_h.valueChanged.connect(lambda v: self._on_prop_changed("height", v))
        size_layout.addRow("Altura:", self.spin_h)
        
        props_layout.addWidget(size_group)
        
        # Product (only for slots with product)
        self.product_group = QGroupBox("Produto")
        product_layout = QFormLayout(self.product_group)
        
        self.edit_name = QLineEdit()
        self.edit_name.setReadOnly(True)
        product_layout.addRow("Nome:", self.edit_name)
        
        self.spin_price = QDoubleSpinBox()
        self.spin_price.setRange(0, 99999.99)
        self.spin_price.setPrefix("R$ ")
        self.spin_price.setDecimals(2)
        self.spin_price.valueChanged.connect(lambda v: self._on_prop_changed("price", v))
        product_layout.addRow("Preço:", self.spin_price)
        
        self.btn_apply_price = QPushButton("Aplicar em todos")
        self.btn_apply_price.clicked.connect(
            lambda: self.apply_to_all.emit("price", self.spin_price.value())
        )
        product_layout.addRow("", self.btn_apply_price)
        
        props_layout.addWidget(self.product_group)
        
        # Actions
        actions_group = QGroupBox("Ações")
        actions_layout = QVBoxLayout(actions_group)
        
        self.btn_clear = QPushButton("🗑️ Limpar Slot")
        self.btn_clear.clicked.connect(lambda: self._on_action("clear"))
        actions_layout.addWidget(self.btn_clear)
        
        self.btn_lock = QPushButton("🔒 Travar")
        self.btn_lock.setCheckable(True)
        self.btn_lock.clicked.connect(lambda: self._on_action("lock"))
        actions_layout.addWidget(self.btn_lock)
        
        props_layout.addWidget(actions_group)
        
        props_layout.addStretch()
        layout.addWidget(self.props_widget)
        
        scroll.setWidget(widget)
        self.setWidget(scroll)
    
    def set_item(self, item, data: Dict = None):
        """Define item selecionado."""
        self._current_item = item
        self._current_data = data or {}
        
        if item is None:
            self.no_selection.setVisible(True)
            self.props_widget.setVisible(False)
            return
        
        self.no_selection.setVisible(False)
        self.props_widget.setVisible(True)
        
        # Atualiza UI - bloqueia sinais
        self._block_signals(True)
        
        self.lbl_id.setText(str(data.get("element_id", "-")))
        self.spin_x.setValue(data.get("x", 0))
        self.spin_y.setValue(data.get("y", 0))
        self.spin_w.setValue(data.get("width", 100))
        self.spin_h.setValue(data.get("height", 100))
        
        # Produto
        product = data.get("product_data")
        if product:
            self.product_group.setVisible(True)
            self.edit_name.setText(product.get("nome_sanitizado", ""))
            self.spin_price.setValue(float(product.get("preco_venda_atual", 0)))
        else:
            self.product_group.setVisible(False)
        
        self._block_signals(False)
    
    def clear(self):
        """Limpa seleção."""
        self.set_item(None)
    
    def _block_signals(self, block: bool):
        """Bloqueia/desbloqueia sinais."""
        for widget in [self.spin_x, self.spin_y, self.spin_w, self.spin_h, self.spin_price]:
            widget.blockSignals(block)
    
    def _on_prop_changed(self, prop: str, value: Any):
        """Callback quando propriedade muda."""
        if self._current_item:
            item_id = self._current_data.get("element_id", "")
            self.property_changed.emit(item_id, prop, value)
    
    def _on_action(self, action: str):
        """Callback para ações."""
        if action == "clear" and self._current_item:
            # Emite sinal para limpar
            pass
        elif action == "lock":
            pass


def create_properties_dock(parent=None) -> PropertiesDock:
    """Cria dock de propriedades."""
    return PropertiesDock(parent)

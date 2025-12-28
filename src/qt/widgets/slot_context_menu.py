"""
AutoTabloide AI - Slot Context Menu
====================================
PROTOCOLO DE CONVERGÊNCIA 260 - Fase 3 (Passo 66, 100)
Menu de contexto para slots do Ateliê.
"""

from __future__ import annotations
from typing import Optional, Callable
import logging

from PySide6.QtCore import Signal, QObject
from PySide6.QtWidgets import QMenu, QInputDialog, QMessageBox
from PySide6.QtGui import QAction

logger = logging.getLogger("SlotContextMenu")


class SlotContextMenu(QMenu):
    """
    Menu de contexto para slots.
    
    Actions:
    - Limpar slot
    - Editar override
    - Bloquear/Desbloquear
    - Copiar/Colar produto
    - Ver produto no estoque
    """
    
    clear_requested = Signal()
    edit_requested = Signal()
    lock_toggled = Signal(bool)
    copy_requested = Signal()
    paste_requested = Signal()
    find_in_stock = Signal()
    
    def __init__(self, slot_item, parent=None):
        super().__init__(parent)
        self._slot = slot_item
        self._setup_actions()
    
    def _setup_actions(self):
        """Configura ações do menu."""
        has_product = self._slot.slot_data.product is not None
        is_locked = self._slot.slot_data.locked
        
        # Limpar
        if has_product:
            action_clear = self.addAction("🗑️ Limpar Slot")
            action_clear.triggered.connect(self.clear_requested.emit)
        
        # Editar
        if has_product:
            action_edit = self.addAction("✏️ Editar Override")
            action_edit.triggered.connect(self.edit_requested.emit)
        
        self.addSeparator()
        
        # Copiar/Colar
        if has_product:
            action_copy = self.addAction("📋 Copiar Produto")
            action_copy.triggered.connect(self.copy_requested.emit)
        
        action_paste = self.addAction("📥 Colar Produto")
        action_paste.triggered.connect(self.paste_requested.emit)
        
        self.addSeparator()
        
        # Bloquear
        lock_text = "🔓 Desbloquear" if is_locked else "🔒 Bloquear"
        action_lock = self.addAction(lock_text)
        action_lock.triggered.connect(lambda: self.lock_toggled.emit(not is_locked))
        
        # Ver no estoque
        if has_product:
            self.addSeparator()
            action_find = self.addAction("🔍 Ver no Estoque")
            action_find.triggered.connect(self.find_in_stock.emit)


class OverrideDialog:
    """Diálogo para editar overrides."""
    
    @staticmethod
    def edit_price(parent, current_price: float) -> Optional[float]:
        """Edita preço."""
        value, ok = QInputDialog.getDouble(
            parent,
            "Override de Preço",
            "Novo preço (R$):",
            current_price,
            0, 99999, 2
        )
        return value if ok else None
    
    @staticmethod
    def edit_name(parent, current_name: str) -> Optional[str]:
        """Edita nome."""
        text, ok = QInputDialog.getText(
            parent,
            "Override de Nome",
            "Novo nome:",
            text=current_name
        )
        return text if ok else None
    
    @staticmethod
    def confirm_clear(parent) -> bool:
        """Confirma limpeza."""
        result = QMessageBox.question(
            parent,
            "Limpar Slot",
            "Remover produto deste slot?",
            QMessageBox.Yes | QMessageBox.No
        )
        return result == QMessageBox.Yes


# =============================================================================
# CLIPBOARD
# =============================================================================

class SlotClipboard:
    """Clipboard para copiar/colar produtos entre slots."""
    
    _instance: Optional['SlotClipboard'] = None
    _product: Optional[dict] = None
    
    @classmethod
    def copy(cls, product: dict):
        """Copia produto."""
        cls._product = dict(product) if product else None
    
    @classmethod
    def paste(cls) -> Optional[dict]:
        """Cola produto."""
        return cls._product
    
    @classmethod
    def has_content(cls) -> bool:
        """Verifica se tem conteúdo."""
        return cls._product is not None
    
    @classmethod
    def clear(cls):
        """Limpa clipboard."""
        cls._product = None

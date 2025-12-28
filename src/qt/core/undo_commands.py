"""
AutoTabloide AI - Undo Commands
===============================
PROTOCOLO DE CONVERGÊNCIA 260 - Fase 3 (Passos 112-115)
Comandos de undo/redo para o Ateliê.
"""

from __future__ import annotations
from typing import Dict, Optional, Any
import json
import logging

from PySide6.QtGui import QUndoCommand, QUndoStack

logger = logging.getLogger("UndoCommands")


class DropProductCommand(QUndoCommand):
    """Comando: Soltar produto no slot."""
    
    def __init__(self, slot_item, product: Dict, previous_product: Dict = None):
        super().__init__(f"Drop: {product.get('nome_sanitizado', '')[:20]}")
        self._slot = slot_item
        self._product = product
        self._previous = previous_product
    
    def redo(self):
        self._slot._set_product(self._product)
    
    def undo(self):
        if self._previous:
            self._slot._set_product(self._previous)
        else:
            self._slot.clear_slot()


class ClearSlotCommand(QUndoCommand):
    """Comando: Limpar slot."""
    
    def __init__(self, slot_item, previous_product: Dict):
        super().__init__(f"Clear: Slot {slot_item.slot_data.slot_index}")
        self._slot = slot_item
        self._previous = previous_product
    
    def redo(self):
        self._slot.clear_slot()
    
    def undo(self):
        if self._previous:
            self._slot._set_product(self._previous)


class OverridePriceCommand(QUndoCommand):
    """Comando: Override de preço."""
    
    def __init__(self, slot_item, new_price: float, old_price: float):
        super().__init__(f"Price: R$ {new_price:.2f}")
        self._slot = slot_item
        self._new = new_price
        self._old = old_price
    
    def redo(self):
        self._slot.slot_data.override_price = self._new
        self._slot._price_item.setHtml(self._slot._format_price(self._new))
    
    def undo(self):
        if self._old is not None:
            self._slot.slot_data.override_price = self._old
            self._slot._price_item.setHtml(self._slot._format_price(self._old))
        else:
            self._slot.slot_data.override_price = None
            if self._slot.slot_data.product:
                price = self._slot.slot_data.product.get("preco_venda_atual", 0)
                self._slot._price_item.setHtml(self._slot._format_price(price))


class MoveSlotCommand(QUndoCommand):
    """Comando: Mover slot."""
    
    def __init__(self, slot_item, old_pos, new_pos):
        super().__init__("Move Slot")
        self._slot = slot_item
        self._old = old_pos
        self._new = new_pos
    
    def redo(self):
        self._slot.setPos(self._new)
    
    def undo(self):
        self._slot.setPos(self._old)


class SwapSlotsCommand(QUndoCommand):
    """Comando: Trocar produtos entre slots."""
    
    def __init__(self, slot_a, slot_b):
        super().__init__("Swap Slots")
        self._slot_a = slot_a
        self._slot_b = slot_b
        self._product_a = slot_a.slot_data.product
        self._product_b = slot_b.slot_data.product
    
    def redo(self):
        if self._product_b:
            self._slot_a._set_product(self._product_b)
        else:
            self._slot_a.clear_slot()
        
        if self._product_a:
            self._slot_b._set_product(self._product_a)
        else:
            self._slot_b.clear_slot()
    
    def undo(self):
        if self._product_a:
            self._slot_a._set_product(self._product_a)
        else:
            self._slot_a.clear_slot()
        
        if self._product_b:
            self._slot_b._set_product(self._product_b)
        else:
            self._slot_b.clear_slot()


class BatchClearCommand(QUndoCommand):
    """Comando: Limpar múltiplos slots."""
    
    def __init__(self, slots: list):
        super().__init__(f"Clear {len(slots)} slots")
        self._slots = slots
        self._products = [s.slot_data.product for s in slots]
    
    def redo(self):
        for slot in self._slots:
            slot.clear_slot()
    
    def undo(self):
        for slot, product in zip(self._slots, self._products):
            if product:
                slot._set_product(product)


# =============================================================================
# UNDO STACK MANAGER
# =============================================================================

class UndoManager:
    """Gerenciador de undo/redo."""
    
    _instance: Optional['UndoManager'] = None
    
    def __init__(self):
        self._stack = QUndoStack()
        self._stack.setUndoLimit(100)
    
    @classmethod
    def instance(cls) -> 'UndoManager':
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    @property
    def stack(self) -> QUndoStack:
        return self._stack
    
    def push(self, command: QUndoCommand):
        """Adiciona comando."""
        self._stack.push(command)
    
    def undo(self):
        """Desfaz."""
        if self._stack.canUndo():
            self._stack.undo()
    
    def redo(self):
        """Refaz."""
        if self._stack.canRedo():
            self._stack.redo()
    
    def clear(self):
        """Limpa histórico."""
        self._stack.clear()
    
    @property
    def can_undo(self) -> bool:
        return self._stack.canUndo()
    
    @property
    def can_redo(self) -> bool:
        return self._stack.canRedo()
    
    @property
    def undo_text(self) -> str:
        return self._stack.undoText()
    
    @property
    def redo_text(self) -> str:
        return self._stack.redoText()


def get_undo_manager() -> UndoManager:
    return UndoManager.instance()

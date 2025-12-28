"""
AutoTabloide AI - Undo/Redo Stack
=================================
PROTOCOLO DE RETIFICAÇÃO NÍVEL 0 - Fase 3 (Passo 116)
Sistema de undo/redo para o Ateliê usando QUndoStack.

Cada ação (Drop, Move, Edit, Delete) cria um Command
que pode ser desfeito/refeito.
"""

from __future__ import annotations
from typing import Dict, Optional, Any
from dataclasses import dataclass
import json
import logging

from PySide6.QtGui import QUndoCommand, QUndoStack
from PySide6.QtCore import QObject, Signal

logger = logging.getLogger("UndoRedo")


# =============================================================================
# COMMANDS
# =============================================================================

class SlotDropCommand(QUndoCommand):
    """Comando para soltar produto em slot."""
    
    def __init__(self, slot, product_data: Dict, old_data: Optional[Dict] = None):
        super().__init__(f"Adicionar {product_data.get('nome_sanitizado', 'produto')[:20]}")
        self.slot = slot
        self.new_data = product_data.copy()
        self.old_data = old_data.copy() if old_data else None
    
    def redo(self):
        self.slot.set_product(self.new_data)
    
    def undo(self):
        if self.old_data:
            self.slot.set_product(self.old_data)
        else:
            self.slot.clear_product()


class SlotClearCommand(QUndoCommand):
    """Comando para limpar slot."""
    
    def __init__(self, slot, old_data: Dict):
        name = old_data.get('nome_sanitizado', 'produto')[:20]
        super().__init__(f"Remover {name}")
        self.slot = slot
        self.old_data = old_data.copy()
    
    def redo(self):
        self.slot.clear_product()
    
    def undo(self):
        self.slot.set_product(self.old_data)


class SlotMoveCommand(QUndoCommand):
    """Comando para mover posição do item dentro do slot."""
    
    def __init__(self, slot, old_pos: tuple, new_pos: tuple):
        super().__init__("Mover imagem")
        self.slot = slot
        self.old_pos = old_pos
        self.new_pos = new_pos
    
    def redo(self):
        if hasattr(self.slot, '_image_offset'):
            self.slot._image_offset = self.new_pos
            self.slot.update()
    
    def undo(self):
        if hasattr(self.slot, '_image_offset'):
            self.slot._image_offset = self.old_pos
            self.slot.update()


class PriceEditCommand(QUndoCommand):
    """Comando para editar preço inline."""
    
    def __init__(self, slot, old_price: float, new_price: float):
        super().__init__(f"Alterar preço para R$ {new_price:.2f}")
        self.slot = slot
        self.old_price = old_price
        self.new_price = new_price
    
    def redo(self):
        if self.slot.product_data:
            self.slot.product_data['preco_venda_atual'] = self.new_price
            self.slot.update()
    
    def undo(self):
        if self.slot.product_data:
            self.slot.product_data['preco_venda_atual'] = self.old_price
            self.slot.update()


class SlotSwapCommand(QUndoCommand):
    """Comando para trocar dois slots."""
    
    def __init__(self, slot_a, slot_b, data_a: Optional[Dict], data_b: Optional[Dict]):
        super().__init__("Trocar slots")
        self.slot_a = slot_a
        self.slot_b = slot_b
        self.data_a = data_a.copy() if data_a else None
        self.data_b = data_b.copy() if data_b else None
    
    def redo(self):
        self._swap()
    
    def undo(self):
        self._swap()
    
    def _swap(self):
        # Pega dados atuais
        current_a = self.slot_a.product_data.copy() if self.slot_a.product_data else None
        current_b = self.slot_b.product_data.copy() if self.slot_b.product_data else None
        
        # Troca
        if current_b:
            self.slot_a.set_product(current_b)
        else:
            self.slot_a.clear_product()
        
        if current_a:
            self.slot_b.set_product(current_a)
        else:
            self.slot_b.clear_product()


class BulkClearCommand(QUndoCommand):
    """Comando para limpar vários slots."""
    
    def __init__(self, slots_data: list):
        """
        Args:
            slots_data: Lista de (slot, old_data) tuples
        """
        super().__init__(f"Limpar {len(slots_data)} slots")
        self.slots_data = slots_data
    
    def redo(self):
        for slot, _ in self.slots_data:
            slot.clear_product()
    
    def undo(self):
        for slot, data in self.slots_data:
            if data:
                slot.set_product(data)


# =============================================================================
# UNDO/REDO MANAGER
# =============================================================================

class UndoRedoManager(QObject):
    """
    Gerenciador de undo/redo para o Ateliê.
    Mantém pilha de comandos e emite sinais de mudança.
    """
    
    can_undo_changed = Signal(bool)
    can_redo_changed = Signal(bool)
    stack_changed = Signal()  # Emitido quando qualquer mudança ocorre
    
    _instance: Optional['UndoRedoManager'] = None
    
    def __init__(self, max_undo: int = 50):
        super().__init__()
        self._stack = QUndoStack()
        self._stack.setUndoLimit(max_undo)
        
        # Conecta sinais
        self._stack.canUndoChanged.connect(self.can_undo_changed.emit)
        self._stack.canRedoChanged.connect(self.can_redo_changed.emit)
        self._stack.indexChanged.connect(lambda _: self.stack_changed.emit())
    
    @classmethod
    def instance(cls) -> 'UndoRedoManager':
        """Singleton."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    @property
    def stack(self) -> QUndoStack:
        """Acesso direto ao QUndoStack."""
        return self._stack
    
    def push(self, command: QUndoCommand):
        """Adiciona comando à pilha."""
        self._stack.push(command)
        logger.debug(f"[Undo] Push: {command.text()}")
    
    def undo(self):
        """Desfaz última ação."""
        if self._stack.canUndo():
            self._stack.undo()
            logger.debug("[Undo] Undo executado")
    
    def redo(self):
        """Refaz última ação desfeita."""
        if self._stack.canRedo():
            self._stack.redo()
            logger.debug("[Undo] Redo executado")
    
    def clear(self):
        """Limpa toda a pilha."""
        self._stack.clear()
        logger.debug("[Undo] Stack limpo")
    
    def can_undo(self) -> bool:
        return self._stack.canUndo()
    
    def can_redo(self) -> bool:
        return self._stack.canRedo()
    
    def undo_text(self) -> str:
        """Texto do próximo undo."""
        return self._stack.undoText()
    
    def redo_text(self) -> str:
        """Texto do próximo redo."""
        return self._stack.redoText()
    
    @property
    def count(self) -> int:
        """Número de comandos na pilha."""
        return self._stack.count()
    
    @property
    def index(self) -> int:
        """Índice atual na pilha."""
        return self._stack.index()
    
    # Helpers para criar comandos
    
    def record_drop(self, slot, product_data: Dict, old_data: Optional[Dict] = None):
        """Registra drop de produto."""
        cmd = SlotDropCommand(slot, product_data, old_data)
        self.push(cmd)
    
    def record_clear(self, slot, old_data: Dict):
        """Registra limpeza de slot."""
        cmd = SlotClearCommand(slot, old_data)
        self.push(cmd)
    
    def record_price_edit(self, slot, old_price: float, new_price: float):
        """Registra edição de preço."""
        cmd = PriceEditCommand(slot, old_price, new_price)
        self.push(cmd)
    
    def record_swap(self, slot_a, slot_b, data_a: Optional[Dict], data_b: Optional[Dict]):
        """Registra troca de slots."""
        cmd = SlotSwapCommand(slot_a, slot_b, data_a, data_b)
        self.push(cmd)
    
    def record_bulk_clear(self, slots_data: list):
        """Registra limpeza em massa."""
        cmd = BulkClearCommand(slots_data)
        self.push(cmd)


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_undo_manager() -> UndoRedoManager:
    """Acesso global ao undo manager."""
    return UndoRedoManager.instance()


def undo():
    """Desfaz última ação."""
    get_undo_manager().undo()


def redo():
    """Refaz última ação."""
    get_undo_manager().redo()

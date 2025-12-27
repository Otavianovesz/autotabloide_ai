"""
AutoTabloide AI - Undo/Redo System
====================================
Sistema de desfazer/refazer baseado em delta.
PROTOCOLO DE RETIFICAÇÃO: Passo 74 (Undo/Redo delta).

Implementa Command Pattern para ações reversíveis.
"""

import copy
import logging
from typing import Optional, Any, Dict, List, Callable, TypeVar
from dataclasses import dataclass, field
from datetime import datetime
from abc import ABC, abstractmethod
from enum import Enum

logger = logging.getLogger("UndoRedo")

T = TypeVar('T')


class ActionType(Enum):
    """Tipos de ação para histórico."""
    ADD_PRODUCT = "add_product"
    REMOVE_PRODUCT = "remove_product"
    MOVE_PRODUCT = "move_product"
    EDIT_PRODUCT = "edit_product"
    CLEAR_SLOT = "clear_slot"
    CHANGE_LAYOUT = "change_layout"
    BATCH = "batch"


@dataclass
class UndoableAction(ABC):
    """Ação que pode ser desfeita/refeita."""
    action_type: ActionType
    timestamp: datetime = field(default_factory=datetime.now)
    description: str = ""
    
    @abstractmethod
    def execute(self) -> bool:
        """Executa a ação. Retorna True se bem-sucedida."""
        pass
    
    @abstractmethod
    def undo(self) -> bool:
        """Desfaz a ação. Retorna True se bem-sucedida."""
        pass
    
    def redo(self) -> bool:
        """Refaz a ação (normalmente igual a execute)."""
        return self.execute()


@dataclass
class DeltaAction(UndoableAction):
    """
    Ação baseada em delta (diferença antes/depois).
    
    Armazena apenas o que mudou, não o estado completo.
    """
    target_id: Any = None
    before_state: Dict[str, Any] = field(default_factory=dict)
    after_state: Dict[str, Any] = field(default_factory=dict)
    apply_callback: Optional[Callable[[Any, Dict], bool]] = None
    
    def execute(self) -> bool:
        if self.apply_callback:
            return self.apply_callback(self.target_id, self.after_state)
        return False
    
    def undo(self) -> bool:
        if self.apply_callback:
            return self.apply_callback(self.target_id, self.before_state)
        return False


@dataclass
class BatchAction(UndoableAction):
    """Ação que agrupa múltiplas ações em uma só."""
    actions: List[UndoableAction] = field(default_factory=list)
    
    def __post_init__(self):
        self.action_type = ActionType.BATCH
    
    def execute(self) -> bool:
        for action in self.actions:
            if not action.execute():
                # Rollback parcial
                for done in reversed(self.actions[:self.actions.index(action)]):
                    done.undo()
                return False
        return True
    
    def undo(self) -> bool:
        # Desfaz em ordem reversa
        for action in reversed(self.actions):
            if not action.undo():
                return False
        return True


class UndoRedoManager:
    """
    Gerenciador central de undo/redo.
    
    PASSO 74: Implementa histórico de ações com delta.
    """
    
    DEFAULT_MAX_HISTORY = 50
    
    def __init__(self, max_history: int = DEFAULT_MAX_HISTORY):
        self.max_history = max_history
        self._undo_stack: List[UndoableAction] = []
        self._redo_stack: List[UndoableAction] = []
        self._on_change_callbacks: List[Callable[[], None]] = []
        self._is_applying = False  # Evita loops
    
    def execute(self, action: UndoableAction) -> bool:
        """
        Executa uma ação e adiciona ao histórico.
        
        Args:
            action: Ação a executar
            
        Returns:
            True se executou com sucesso
        """
        if self._is_applying:
            return False
        
        self._is_applying = True
        
        try:
            if action.execute():
                self._undo_stack.append(action)
                self._redo_stack.clear()  # Limpa redo ao fazer nova ação
                
                # Limitar tamanho
                while len(self._undo_stack) > self.max_history:
                    self._undo_stack.pop(0)
                
                self._notify_change()
                logger.debug(f"Ação executada: {action.action_type.value}")
                return True
            
            return False
            
        finally:
            self._is_applying = False
    
    def undo(self) -> bool:
        """
        Desfaz última ação.
        
        Returns:
            True se conseguiu desfazer
        """
        if not self.can_undo:
            return False
        
        if self._is_applying:
            return False
        
        self._is_applying = True
        
        try:
            action = self._undo_stack.pop()
            
            if action.undo():
                self._redo_stack.append(action)
                self._notify_change()
                logger.debug(f"Ação desfeita: {action.action_type.value}")
                return True
            else:
                # Falhou - devolve para stack
                self._undo_stack.append(action)
                return False
                
        finally:
            self._is_applying = False
    
    def redo(self) -> bool:
        """
        Refaz última ação desfeita.
        
        Returns:
            True se conseguiu refazer
        """
        if not self.can_redo:
            return False
        
        if self._is_applying:
            return False
        
        self._is_applying = True
        
        try:
            action = self._redo_stack.pop()
            
            if action.redo():
                self._undo_stack.append(action)
                self._notify_change()
                logger.debug(f"Ação refeita: {action.action_type.value}")
                return True
            else:
                self._redo_stack.append(action)
                return False
                
        finally:
            self._is_applying = False
    
    @property
    def can_undo(self) -> bool:
        """True se há ações para desfazer."""
        return len(self._undo_stack) > 0
    
    @property
    def can_redo(self) -> bool:
        """True se há ações para refazer."""
        return len(self._redo_stack) > 0
    
    @property
    def undo_description(self) -> str:
        """Descrição da próxima ação a desfazer."""
        if self.can_undo:
            action = self._undo_stack[-1]
            return action.description or action.action_type.value
        return ""
    
    @property
    def redo_description(self) -> str:
        """Descrição da próxima ação a refazer."""
        if self.can_redo:
            action = self._redo_stack[-1]
            return action.description or action.action_type.value
        return ""
    
    def clear(self) -> None:
        """Limpa todo o histórico."""
        self._undo_stack.clear()
        self._redo_stack.clear()
        self._notify_change()
    
    def on_change(self, callback: Callable[[], None]) -> None:
        """Registra callback para mudanças no histórico."""
        self._on_change_callbacks.append(callback)
    
    def _notify_change(self) -> None:
        """Notifica callbacks de mudança."""
        for callback in self._on_change_callbacks:
            try:
                callback()
            except Exception as e:
                logger.error(f"Erro em callback undo/redo: {e}")
    
    def get_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Retorna histórico recente para exibição.
        
        Args:
            limit: Máximo de itens
            
        Returns:
            Lista de dicts com info das ações
        """
        history = []
        
        for action in reversed(self._undo_stack[-limit:]):
            history.append({
                "type": action.action_type.value,
                "description": action.description,
                "timestamp": action.timestamp.isoformat(),
                "can_undo": True,
            })
        
        return history


# ==============================================================================
# AÇÕES ESPECÍFICAS DO ATELIÊ
# ==============================================================================

@dataclass
class SlotProductAction(UndoableAction):
    """Ação de adicionar/remover produto de slot."""
    slot_index: int = 0
    product_data: Optional[Dict] = None
    previous_product: Optional[Dict] = None
    update_slot_callback: Optional[Callable[[int, Optional[Dict]], bool]] = None
    
    def execute(self) -> bool:
        if self.update_slot_callback:
            return self.update_slot_callback(self.slot_index, self.product_data)
        return False
    
    def undo(self) -> bool:
        if self.update_slot_callback:
            return self.update_slot_callback(self.slot_index, self.previous_product)
        return False


@dataclass 
class MoveProductAction(UndoableAction):
    """Ação de mover produto entre slots."""
    source_slot: int = 0
    target_slot: int = 0
    source_product: Optional[Dict] = None
    target_product: Optional[Dict] = None
    swap_callback: Optional[Callable[[int, int], bool]] = None
    
    def __post_init__(self):
        self.action_type = ActionType.MOVE_PRODUCT
        self.description = f"Mover produto do slot {self.source_slot} para {self.target_slot}"
    
    def execute(self) -> bool:
        if self.swap_callback:
            return self.swap_callback(self.source_slot, self.target_slot)
        return False
    
    def undo(self) -> bool:
        if self.swap_callback:
            # Swap inverso
            return self.swap_callback(self.target_slot, self.source_slot)
        return False


# ==============================================================================
# INSTÂNCIA GLOBAL
# ==============================================================================

_undo_manager: Optional[UndoRedoManager] = None


def get_undo_manager() -> UndoRedoManager:
    """Retorna instância global do gerenciador."""
    global _undo_manager
    if _undo_manager is None:
        _undo_manager = UndoRedoManager()
    return _undo_manager


def undo() -> bool:
    """Função de conveniência para desfazer."""
    return get_undo_manager().undo()


def redo() -> bool:
    """Função de conveniência para refazer."""
    return get_undo_manager().redo()

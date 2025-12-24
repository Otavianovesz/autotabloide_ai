"""
AutoTabloide AI - Slot Controller (BLoC Pattern)
==================================================
Controlador de slots seguindo padrão BLoC.
Passos 48-49 do Checklist 100.

Funcionalidades:
- Padrão BLoC/Controller para gerenciamento de slots
- Separação de lógica de negócio da UI
- ListView virtualizado para listagens
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Callable, Any
from enum import Enum, auto
import asyncio

from src.core.logging_config import get_logger
from src.core.event_bus import EventBus, get_event_bus

logger = get_logger("SlotController")


# ==============================================================================
# MODELS
# ==============================================================================

class SlotState(Enum):
    """Estado de um slot."""
    EMPTY = auto()
    LOADING = auto()
    FILLED = auto()
    ERROR = auto()


@dataclass
class SlotData:
    """Dados de um slot."""
    slot_id: str
    state: SlotState = SlotState.EMPTY
    product_id: Optional[int] = None
    product_name: Optional[str] = None
    product_price: Optional[float] = None
    product_unit: Optional[str] = None
    image_hash: Optional[str] = None
    error_message: Optional[str] = None
    # Kit - múltiplos produtos
    kit_products: List[int] = field(default_factory=list)


# ==============================================================================
# SLOT CONTROLLER (Passo 48)
# ==============================================================================

class SlotController:
    """
    Controlador BLoC para gerenciamento de slots.
    Passo 48 do Checklist - Padrão BLoC/Controller.
    
    Separa lógica de negócio da apresentação.
    """
    
    def __init__(self, num_slots: int = 12):
        """
        Args:
            num_slots: Número de slots no template
        """
        self._slots: Dict[str, SlotData] = {}
        self._listeners: List[Callable[[str, SlotData], None]] = []
        self._event_bus = get_event_bus()
        
        # Inicializa slots
        for i in range(1, num_slots + 1):
            slot_id = f"SLOT_{i:02d}"
            self._slots[slot_id] = SlotData(slot_id=slot_id)
    
    @property
    def slots(self) -> Dict[str, SlotData]:
        """Retorna todos os slots (read-only)."""
        return self._slots.copy()
    
    def get_slot(self, slot_id: str) -> Optional[SlotData]:
        """Obtém dados de um slot."""
        return self._slots.get(slot_id)
    
    def add_listener(self, callback: Callable[[str, SlotData], None]) -> None:
        """Adiciona listener para mudanças de slot."""
        self._listeners.append(callback)
    
    def remove_listener(self, callback: Callable[[str, SlotData], None]) -> None:
        """Remove listener."""
        if callback in self._listeners:
            self._listeners.remove(callback)
    
    def _notify_listeners(self, slot_id: str) -> None:
        """Notifica todos os listeners sobre mudança."""
        slot_data = self._slots.get(slot_id)
        if slot_data:
            for listener in self._listeners:
                try:
                    listener(slot_id, slot_data)
                except Exception as e:
                    logger.error(f"Erro em listener: {e}")
    
    def set_product(
        self,
        slot_id: str,
        product_id: int,
        product_name: str,
        product_price: float,
        product_unit: str = "",
        image_hash: Optional[str] = None
    ) -> bool:
        """
        Define um produto em um slot.
        
        Args:
            slot_id: ID do slot
            product_id: ID do produto
            product_name: Nome do produto
            product_price: Preço
            product_unit: Unidade (kg, un, etc)
            image_hash: Hash da imagem
            
        Returns:
            True se sucesso
        """
        if slot_id not in self._slots:
            logger.warning(f"Slot não encontrado: {slot_id}")
            return False
        
        self._slots[slot_id] = SlotData(
            slot_id=slot_id,
            state=SlotState.FILLED,
            product_id=product_id,
            product_name=product_name,
            product_price=product_price,
            product_unit=product_unit,
            image_hash=image_hash
        )
        
        self._notify_listeners(slot_id)
        self._event_bus.emit("slot_updated", {"slot_id": slot_id, "action": "filled"})
        
        logger.debug(f"Produto {product_id} adicionado a {slot_id}")
        return True
    
    def clear_slot(self, slot_id: str) -> bool:
        """Limpa um slot."""
        if slot_id not in self._slots:
            return False
        
        self._slots[slot_id] = SlotData(slot_id=slot_id, state=SlotState.EMPTY)
        self._notify_listeners(slot_id)
        self._event_bus.emit("slot_updated", {"slot_id": slot_id, "action": "cleared"})
        
        return True
    
    def clear_all(self) -> int:
        """Limpa todos os slots."""
        count = 0
        for slot_id in self._slots:
            if self._slots[slot_id].state != SlotState.EMPTY:
                self.clear_slot(slot_id)
                count += 1
        return count
    
    def get_filled_slots(self) -> List[SlotData]:
        """Retorna slots preenchidos."""
        return [s for s in self._slots.values() if s.state == SlotState.FILLED]
    
    def get_empty_slots(self) -> List[str]:
        """Retorna IDs de slots vazios."""
        return [s.slot_id for s in self._slots.values() if s.state == SlotState.EMPTY]
    
    def add_to_kit(self, slot_id: str, product_id: int) -> bool:
        """
        Adiciona produto a um kit (múltiplos produtos no slot).
        
        Args:
            slot_id: ID do slot
            product_id: ID do produto a adicionar
            
        Returns:
            True se sucesso
        """
        slot = self._slots.get(slot_id)
        if not slot:
            return False
        
        if product_id not in slot.kit_products:
            slot.kit_products.append(product_id)
            self._notify_listeners(slot_id)
            return True
        
        return False
    
    def export_mapping(self) -> Dict[str, Any]:
        """
        Exporta mapeamento slot->produto para renderização.
        
        Returns:
            Dict com dados de cada slot
        """
        result = {}
        
        for slot_id, slot in self._slots.items():
            if slot.state == SlotState.FILLED:
                result[slot_id] = {
                    "product_id": slot.product_id,
                    "TXT_NOME_PRODUTO": slot.product_name,
                    "TXT_PRECO_INT": str(int(slot.product_price)) if slot.product_price else "",
                    "TXT_PRECO_DEC": f",{int((slot.product_price % 1) * 100):02d}" if slot.product_price else "",
                    "TXT_UNIDADE": slot.product_unit,
                    "ALVO_IMAGEM": slot.image_hash,
                    "kit_products": slot.kit_products
                }
        
        return result


# ==============================================================================
# VIRTUAL LIST (Passo 49)
# ==============================================================================

@dataclass
class VirtualListItem:
    """Item de lista virtual."""
    index: int
    data: Any
    visible: bool = False


class VirtualListController:
    """
    Controlador para ListView virtualizado.
    Passo 49 do Checklist - ListView virtualizado.
    
    Apenas renderiza itens visíveis na viewport.
    """
    
    def __init__(
        self,
        items: List[Any],
        item_height: int = 50,
        viewport_height: int = 500,
        buffer_count: int = 5
    ):
        """
        Args:
            items: Lista de dados
            item_height: Altura de cada item em pixels
            viewport_height: Altura da viewport
            buffer_count: Itens extras acima/abaixo da viewport
        """
        self._items = items
        self.item_height = item_height
        self.viewport_height = viewport_height
        self.buffer_count = buffer_count
        
        self._scroll_offset = 0
        self._visible_range: tuple = (0, 0)
        
        self._update_visible_range()
    
    @property
    def total_items(self) -> int:
        return len(self._items)
    
    @property
    def total_height(self) -> int:
        """Altura total da lista."""
        return self.total_items * self.item_height
    
    @property
    def visible_items(self) -> List[VirtualListItem]:
        """Retorna itens visíveis."""
        start, end = self._visible_range
        return [
            VirtualListItem(index=i, data=self._items[i], visible=True)
            for i in range(start, min(end, self.total_items))
        ]
    
    def set_scroll_offset(self, offset: int) -> None:
        """Atualiza posição de scroll."""
        self._scroll_offset = max(0, offset)
        self._update_visible_range()
    
    def _update_visible_range(self) -> None:
        """Recalcula range de itens visíveis."""
        first_visible = self._scroll_offset // self.item_height
        visible_count = self.viewport_height // self.item_height
        
        # Adiciona buffer
        start = max(0, first_visible - self.buffer_count)
        end = min(self.total_items, first_visible + visible_count + self.buffer_count)
        
        self._visible_range = (start, end)
    
    def get_item_offset(self, index: int) -> int:
        """Retorna offset Y de um item."""
        return index * self.item_height
    
    def update_items(self, items: List[Any]) -> None:
        """Atualiza lista de itens."""
        self._items = items
        self._update_visible_range()
    
    def scroll_to_item(self, index: int) -> int:
        """
        Calcula offset de scroll para mostrar item.
        
        Returns:
            Novo offset de scroll
        """
        if index < 0 or index >= self.total_items:
            return self._scroll_offset
        
        item_top = index * self.item_height
        item_bottom = item_top + self.item_height
        
        # Se já está visível, não muda
        viewport_top = self._scroll_offset
        viewport_bottom = viewport_top + self.viewport_height
        
        if item_top >= viewport_top and item_bottom <= viewport_bottom:
            return self._scroll_offset
        
        # Scroll para mostrar item
        if item_top < viewport_top:
            return item_top
        else:
            return item_bottom - self.viewport_height

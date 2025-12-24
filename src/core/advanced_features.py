"""
AutoTabloide AI - Advanced Features
======================================
Funcionalidades avançadas.
Passos 71-80 do Checklist v2.

Funcionalidades:
- Undo/Redo com Command Pattern (71)
- Preço promocional automático (72)
- Detecção fundo branco (73)
- Cache de renderização (74)
- Zoom no canvas (75)
- Réguas visuais (76)
- Snap to grid (77)
- Export JPG rápido (78)
- Histórico de preços (79)
- Badge "Novo" (80)
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, List, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
import io

from src.core.logging_config import get_logger

logger = get_logger("AdvancedFeatures")


# ============================================================================
# PASSO 71: Undo/Redo com Command Pattern
# ============================================================================

class Command(ABC):
    """Interface para comandos."""
    
    @abstractmethod
    def execute(self) -> None:
        """Executa o comando."""
        pass
    
    @abstractmethod
    def undo(self) -> None:
        """Desfaz o comando."""
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """Descrição do comando."""
        pass


@dataclass
class SetProductCommand(Command):
    """Comando para definir produto em slot."""
    
    slot_id: str
    new_product: Dict[str, Any]
    old_product: Optional[Dict[str, Any]] = None
    slot_ref: Any = None  # Referência ao slot
    
    def execute(self) -> None:
        if self.slot_ref:
            self.slot_ref.set_single_product(self.new_product)
    
    def undo(self) -> None:
        if self.slot_ref:
            if self.old_product:
                self.slot_ref.set_single_product(self.old_product)
            else:
                self.slot_ref.clear()
    
    @property
    def description(self) -> str:
        return f"Definir produto em {self.slot_id}"


@dataclass
class ClearSlotCommand(Command):
    """Comando para limpar slot."""
    
    slot_id: str
    product_backup: Optional[Dict[str, Any]] = None
    slot_ref: Any = None
    
    def execute(self) -> None:
        if self.slot_ref:
            self.slot_ref.clear()
    
    def undo(self) -> None:
        if self.slot_ref and self.product_backup:
            self.slot_ref.set_single_product(self.product_backup)
    
    @property
    def description(self) -> str:
        return f"Limpar {self.slot_id}"


@dataclass
class OverridePriceCommand(Command):
    """Comando para alterar preço."""
    
    slot_id: str
    new_price: float
    old_price: Optional[float] = None
    slot_ref: Any = None
    
    def execute(self) -> None:
        if self.slot_ref:
            self.slot_ref.override_price = self.new_price
    
    def undo(self) -> None:
        if self.slot_ref:
            self.slot_ref.override_price = self.old_price
    
    @property
    def description(self) -> str:
        return f"Alterar preço {self.slot_id}: {self.old_price} → {self.new_price}"


class CommandHistory:
    """
    Gerenciador de histórico de comandos.
    Passo 71 do Checklist v2 - Command Pattern para Undo/Redo.
    
    Uso de memória otimizado: armazena apenas ações, não estados completos.
    """
    
    def __init__(self, max_history: int = 50):
        self.max_history = max_history
        self._undo_stack: List[Command] = []
        self._redo_stack: List[Command] = []
    
    def execute(self, command: Command) -> None:
        """Executa comando e adiciona ao histórico."""
        command.execute()
        self._undo_stack.append(command)
        
        # Limpa redo quando nova ação é feita
        self._redo_stack.clear()
        
        # Limita tamanho
        if len(self._undo_stack) > self.max_history:
            self._undo_stack.pop(0)
        
        logger.debug(f"Comando: {command.description}")
    
    def undo(self) -> Optional[str]:
        """Desfaz último comando."""
        if not self._undo_stack:
            return None
        
        command = self._undo_stack.pop()
        command.undo()
        self._redo_stack.append(command)
        
        logger.debug(f"Undo: {command.description}")
        return command.description
    
    def redo(self) -> Optional[str]:
        """Refaz comando desfeito."""
        if not self._redo_stack:
            return None
        
        command = self._redo_stack.pop()
        command.execute()
        self._undo_stack.append(command)
        
        logger.debug(f"Redo: {command.description}")
        return command.description
    
    def can_undo(self) -> bool:
        return len(self._undo_stack) > 0
    
    def can_redo(self) -> bool:
        return len(self._redo_stack) > 0
    
    def clear(self) -> None:
        """Limpa histórico."""
        self._undo_stack.clear()
        self._redo_stack.clear()


# ============================================================================
# PASSO 72: Preço Promocional Automático
# ============================================================================

@dataclass
class PriceStyle:
    """Estilo visual para preço."""
    color: str
    font_weight: str = "bold"
    show_strikethrough: bool = False
    badge_text: Optional[str] = None


def get_promotional_style(
    price_de: Optional[float],
    price_por: float,
    threshold_percentage: float = 10.0
) -> PriceStyle:
    """
    Determina estilo visual para preço promocional.
    Passo 72 do Checklist v2.
    
    Args:
        price_de: Preço original (De)
        price_por: Preço atual (Por)
        threshold_percentage: Desconto mínimo para destacar
        
    Returns:
        PriceStyle com cores e flags
    """
    if price_de is None or price_de <= price_por:
        # Preço normal
        return PriceStyle(color="#10B981")  # Verde
    
    # Calcula desconto
    discount = ((price_de - price_por) / price_de) * 100
    
    if discount >= 30:
        # Mega promoção (>30% off)
        return PriceStyle(
            color="#EF4444",  # Vermelho
            badge_text=f"-{int(discount)}%",
            show_strikethrough=True
        )
    elif discount >= threshold_percentage:
        # Promoção normal
        return PriceStyle(
            color="#F59E0B",  # Amarelo/laranja
            badge_text=f"-{int(discount)}%",
            show_strikethrough=True
        )
    else:
        return PriceStyle(color="#10B981")


# ============================================================================
# PASSO 73: Detecção de Fundo Branco
# ============================================================================

def detect_white_background(image_bytes: bytes, threshold: float = 0.95) -> Tuple[bool, float]:
    """
    Detecta se imagem tem fundo branco sólido.
    Passo 73 do Checklist v2.
    
    Args:
        image_bytes: Bytes da imagem
        threshold: Porcentagem mínima de branco
        
    Returns:
        Tupla (tem_fundo_branco, porcentagem_branco)
    """
    try:
        from PIL import Image
        import numpy as np
        
        img = Image.open(io.BytesIO(image_bytes)).convert('RGB')
        data = np.array(img)
        
        # Pixels brancos (todos canais > 250)
        white_mask = np.all(data > 250, axis=2)
        white_ratio = np.sum(white_mask) / white_mask.size
        
        return white_ratio >= threshold, white_ratio
        
    except Exception as e:
        logger.error(f"Erro ao detectar fundo: {e}")
        return False, 0.0


# ============================================================================
# PASSO 74: Cache de Renderização
# ============================================================================

class RenderCache:
    """
    Cache de renderização de slots.
    Passo 74 do Checklist v2.
    """
    
    def __init__(self):
        self._cache: Dict[str, Tuple[str, bytes]] = {}  # slot_id -> (hash, rendered)
    
    def _compute_hash(self, slot_data: Dict) -> str:
        """Computa hash do estado do slot."""
        import hashlib
        import json
        
        data_str = json.dumps(slot_data, sort_keys=True, default=str)
        return hashlib.md5(data_str.encode()).hexdigest()[:16]
    
    def get(self, slot_id: str, slot_data: Dict) -> Optional[bytes]:
        """Obtém renderização cacheada."""
        current_hash = self._compute_hash(slot_data)
        
        if slot_id in self._cache:
            cached_hash, rendered = self._cache[slot_id]
            if cached_hash == current_hash:
                return rendered
        
        return None
    
    def put(self, slot_id: str, slot_data: Dict, rendered: bytes) -> None:
        """Armazena renderização."""
        current_hash = self._compute_hash(slot_data)
        self._cache[slot_id] = (current_hash, rendered)
    
    def invalidate(self, slot_id: str) -> None:
        """Invalida cache de um slot."""
        if slot_id in self._cache:
            del self._cache[slot_id]
    
    def clear(self) -> None:
        """Limpa todo o cache."""
        self._cache.clear()


# ============================================================================
# PASSO 75-77: Zoom, Réguas, Snap
# ============================================================================

@dataclass
class CanvasState:
    """Estado do canvas."""
    zoom: float = 1.0
    pan_x: float = 0.0
    pan_y: float = 0.0
    show_rulers: bool = False
    snap_to_grid: bool = False
    grid_size: float = 10.0


class CanvasController:
    """
    Controlador de canvas com zoom e navegação.
    Passos 75-77 do Checklist v2.
    """
    
    MIN_ZOOM = 0.25
    MAX_ZOOM = 4.0
    ZOOM_STEP = 0.1
    
    def __init__(self):
        self.state = CanvasState()
    
    def zoom_in(self) -> float:
        """Aumenta zoom."""
        self.state.zoom = min(self.state.zoom + self.ZOOM_STEP, self.MAX_ZOOM)
        return self.state.zoom
    
    def zoom_out(self) -> float:
        """Diminui zoom."""
        self.state.zoom = max(self.state.zoom - self.ZOOM_STEP, self.MIN_ZOOM)
        return self.state.zoom
    
    def zoom_fit(self, canvas_width: float, canvas_height: float, 
                 content_width: float, content_height: float) -> float:
        """Ajusta zoom para caber no canvas."""
        zoom_x = canvas_width / content_width
        zoom_y = canvas_height / content_height
        self.state.zoom = min(zoom_x, zoom_y, 1.0)
        return self.state.zoom
    
    def reset_zoom(self) -> float:
        """Reseta para 100%."""
        self.state.zoom = 1.0
        self.state.pan_x = 0.0
        self.state.pan_y = 0.0
        return self.state.zoom
    
    def toggle_rulers(self) -> bool:
        """Toggle réguas."""
        self.state.show_rulers = not self.state.show_rulers
        return self.state.show_rulers
    
    def toggle_snap(self) -> bool:
        """Toggle snap to grid."""
        self.state.snap_to_grid = not self.state.snap_to_grid
        return self.state.snap_to_grid
    
    def snap_position(self, x: float, y: float) -> Tuple[float, float]:
        """Ajusta posição para grid."""
        if not self.state.snap_to_grid:
            return x, y
        
        grid = self.state.grid_size
        return round(x / grid) * grid, round(y / grid) * grid


# ============================================================================
# PASSO 79-80: Histórico de Preços e Badge Novo
# ============================================================================

def is_recently_imported(created_at: datetime, days: int = 7) -> bool:
    """
    Verifica se produto foi importado recentemente.
    Passo 80 do Checklist v2.
    
    Args:
        created_at: Data de criação
        days: Dias para considerar "novo"
        
    Returns:
        True se recente
    """
    if created_at is None:
        return False
    
    cutoff = datetime.now() - timedelta(days=days)
    return created_at > cutoff


async def get_price_history(product_id: int, limit: int = 10) -> List[Dict]:
    """
    Obtém histórico de preços de um produto.
    Passo 79 do Checklist v2.
    
    Args:
        product_id: ID do produto
        limit: Máximo de registros
        
    Returns:
        Lista de alterações de preço
    """
    try:
        from src.core.data_security import AuditLogViewer
        
        logs = await AuditLogViewer.get_by_entity("product", product_id)
        
        # Filtra apenas mudanças de preço
        price_changes = [
            log for log in logs
            if "preco" in log.get("action", "").lower()
        ]
        
        return price_changes[:limit]
        
    except Exception as e:
        logger.error(f"Erro ao obter histórico: {e}")
        return []

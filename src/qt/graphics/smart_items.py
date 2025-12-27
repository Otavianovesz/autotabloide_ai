"""
AutoTabloide AI - Smart Product Item
=====================================
QGraphicsItem inteligente para representar produtos no canvas.
Suporta decomposição vetorial de SVG e injeção de dados.
"""

from PySide6.QtWidgets import (
    QGraphicsItem, QGraphicsRectItem, QGraphicsTextItem,
    QGraphicsPixmapItem, QGraphicsDropShadowEffect,
    QStyleOptionGraphicsItem, QWidget, QMenu
)
from PySide6.QtCore import Qt, QRectF, QPointF, Signal, QObject
from PySide6.QtGui import (
    QPainter, QColor, QPen, QBrush, QFont, QPixmap, 
    QTransform, QCursor
)
from typing import Optional, Dict, Any, List
from pathlib import Path
import xml.etree.ElementTree as ET


class SlotSignals(QObject):
    """Signals para SlotItem (QGraphicsItem não herda de QObject)."""
    product_dropped = Signal(int, dict)  # slot_index, product_data
    product_cleared = Signal(int)  # slot_index
    double_clicked = Signal(int, dict)  # slot_index, product_data
    context_menu_requested = Signal(int, object)  # slot_index, QPoint


class SmartSlotItem(QGraphicsRectItem):
    """
    Slot inteligente para produtos no Ateliê.
    
    Corresponde a um grupo #SLOT_XX no SVG.
    Gerencia sub-itens: imagem, nome, preço.
    """
    
    # Estados visuais
    STATE_EMPTY = 0
    STATE_HOVER = 1
    STATE_FILLED = 2
    STATE_SELECTED = 3
    STATE_ERROR = 4
    
    # Cores por estado
    COLORS = {
        STATE_EMPTY: ("#2D2D44", "#3D3D5C"),      # border, fill
        STATE_HOVER: ("#2ECC71", "#2ECC7122"),    # verde
        STATE_FILLED: ("#6C5CE7", "#6C5CE722"),   # roxo
        STATE_SELECTED: ("#F1C40F", "#F1C40F22"), # amarelo
        STATE_ERROR: ("#E74C3C", "#E74C3C22"),    # vermelho
    }
    
    def __init__(
        self, 
        slot_index: int,
        x: float, 
        y: float, 
        width: float, 
        height: float,
        svg_elements: Dict[str, Any] = None,
        parent=None
    ):
        super().__init__(x, y, width, height, parent)
        
        self.slot_index = slot_index
        self.svg_elements = svg_elements or {}
        self.product_data: Optional[Dict[str, Any]] = None
        self.state = self.STATE_EMPTY
        
        # Signals
        self.signals = SlotSignals()
        
        # Configurações
        self.setAcceptHoverEvents(True)
        self.setAcceptDrops(True)
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)
        self.setCursor(QCursor(Qt.PointingHandCursor))
        
        # Sub-itens
        self._image_item: Optional[QGraphicsPixmapItem] = None
        self._name_item: Optional[QGraphicsTextItem] = None
        self._price_int_item: Optional[QGraphicsTextItem] = None
        self._price_dec_item: Optional[QGraphicsTextItem] = None
        self._unit_item: Optional[QGraphicsTextItem] = None
        
        # Índice visual (sempre visível)
        self._index_label = QGraphicsTextItem(f"#{slot_index}", self)
        self._index_label.setDefaultTextColor(QColor("#808080"))
        self._index_label.setFont(QFont("Segoe UI", 9))
        self._index_label.setPos(x + 4, y + 4)
        
        # Aplica estilo inicial
        self._apply_state_style()
    
    def _apply_state_style(self) -> None:
        """Aplica estilo visual baseado no estado."""
        border_color, fill_color = self.COLORS.get(
            self.state, 
            self.COLORS[self.STATE_EMPTY]
        )
        
        pen = QPen(QColor(border_color), 2)
        if self.state == self.STATE_EMPTY:
            pen.setStyle(Qt.DashLine)
        else:
            pen.setStyle(Qt.SolidLine)
        
        self.setPen(pen)
        self.setBrush(QBrush(QColor(fill_color)))
    
    def set_state(self, state: int) -> None:
        """Muda estado visual."""
        self.state = state
        self._apply_state_style()
    
    def is_empty(self) -> bool:
        """Verifica se slot está vazio."""
        return self.product_data is None
    
    def set_product(self, product: Dict[str, Any]) -> None:
        """
        Define o produto no slot.
        
        Injeta imagem, nome e preço nos sub-itens.
        """
        self.product_data = product
        self.set_state(self.STATE_FILLED)
        
        # Atualiza label de índice
        name = product.get("nome_sanitizado", "Produto")[:20]
        price = product.get("preco_venda_atual", 0)
        self._index_label.setPlainText(f"#{self.slot_index}\n{name}\nR$ {price:.2f}")
        self._index_label.setDefaultTextColor(QColor("#FFFFFF"))
        
        # TODO: Renderizar imagem real do produto
        # self._render_product_image(product)
        
        # Emite signal
        self.signals.product_dropped.emit(self.slot_index, product)
    
    def clear_product(self) -> None:
        """Remove o produto do slot."""
        self.product_data = None
        self.set_state(self.STATE_EMPTY)
        
        self._index_label.setPlainText(f"#{self.slot_index}")
        self._index_label.setDefaultTextColor(QColor("#808080"))
        
        # Remove sub-itens
        if self._image_item:
            self.scene().removeItem(self._image_item)
            self._image_item = None
        
        self.signals.product_cleared.emit(self.slot_index)
    
    def _render_product_image(self, product: Dict) -> None:
        """Renderiza imagem do produto no slot."""
        img_hash = product.get("img_hash_ref")
        if not img_hash:
            return
        
        # Caminho do cofre
        # TODO: Pegar do container/settings
        vault_path = Path("assets/store") / f"{img_hash}.png"
        
        if vault_path.exists():
            pixmap = QPixmap(str(vault_path))
            
            # Aspect Fit
            slot_rect = self.rect()
            scaled = pixmap.scaled(
                int(slot_rect.width() - 20),
                int(slot_rect.height() - 60),  # Espaço para texto
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
            
            if self._image_item:
                self._image_item.setPixmap(scaled)
            else:
                self._image_item = QGraphicsPixmapItem(scaled, self)
                # Centraliza
                x_offset = (slot_rect.width() - scaled.width()) / 2
                self._image_item.setPos(
                    slot_rect.x() + x_offset,
                    slot_rect.y() + 30
                )
    
    # === Event Handlers ===
    
    def hoverEnterEvent(self, event) -> None:
        """Mouse entrou no slot."""
        if self.state == self.STATE_EMPTY:
            self.set_state(self.STATE_HOVER)
        super().hoverEnterEvent(event)
    
    def hoverLeaveEvent(self, event) -> None:
        """Mouse saiu do slot."""
        if self.state == self.STATE_HOVER:
            self.set_state(self.STATE_EMPTY)
        super().hoverLeaveEvent(event)
    
    def mouseDoubleClickEvent(self, event) -> None:
        """Double-click no slot."""
        self.signals.double_clicked.emit(self.slot_index, self.product_data or {})
        super().mouseDoubleClickEvent(event)
    
    def contextMenuEvent(self, event) -> None:
        """Menu de contexto."""
        self.signals.context_menu_requested.emit(self.slot_index, event.screenPos())
        event.accept()
    
    def dragEnterEvent(self, event) -> None:
        """Drag entrou no slot."""
        if event.mimeData().hasFormat("application/x-autotabloide-product"):
            self.set_state(self.STATE_HOVER)
            event.acceptProposedAction()
        else:
            event.ignore()
    
    def dragLeaveEvent(self, event) -> None:
        """Drag saiu do slot."""
        if self.product_data:
            self.set_state(self.STATE_FILLED)
        else:
            self.set_state(self.STATE_EMPTY)
    
    def dropEvent(self, event) -> None:
        """Produto foi dropado no slot."""
        if event.mimeData().hasFormat("application/x-autotabloide-product"):
            import json
            data = event.mimeData().data("application/x-autotabloide-product")
            product = json.loads(bytes(data).decode('utf-8'))
            self.set_product(product)
            event.acceptProposedAction()
        else:
            event.ignore()


class SVGTemplateParser:
    """
    Parser de templates SVG para o Ateliê.
    
    Extrai slots (#SLOT_XX) e seus sub-elementos.
    """
    
    # Namespaces SVG comuns
    NAMESPACES = {
        'svg': 'http://www.w3.org/2000/svg',
        'xlink': 'http://www.w3.org/1999/xlink',
    }
    
    def __init__(self, svg_path: str):
        self.svg_path = Path(svg_path)
        self.tree = None
        self.root = None
        self.slots: Dict[int, Dict] = {}
        self.viewbox = (0, 0, 800, 1000)  # default
    
    def parse(self) -> bool:
        """
        Parseia o arquivo SVG.
        
        Returns:
            True se parseou com sucesso
        """
        try:
            self.tree = ET.parse(self.svg_path)
            self.root = self.tree.getroot()
            
            # Extrai viewBox
            viewbox_str = self.root.get("viewBox", "0 0 800 1000")
            parts = viewbox_str.split()
            if len(parts) == 4:
                self.viewbox = tuple(map(float, parts))
            
            # Busca slots
            self._find_slots()
            
            return True
            
        except Exception as e:
            print(f"[SVGParser] Erro ao parsear {self.svg_path}: {e}")
            return False
    
    def _find_slots(self) -> None:
        """Identifica slots no SVG."""
        self.slots.clear()
        
        # Busca por grupos com ID começando com SLOT_
        for elem in self.root.iter():
            elem_id = elem.get("id", "")
            
            if elem_id.upper().startswith("SLOT_"):
                try:
                    # Extrai número do slot
                    slot_num = int(elem_id.split("_")[1])
                    
                    # Extrai bounding box
                    bbox = self._get_bounding_box(elem)
                    
                    # Busca sub-elementos
                    sub_elements = self._find_sub_elements(elem)
                    
                    self.slots[slot_num] = {
                        "id": elem_id,
                        "element": elem,
                        "bbox": bbox,
                        "sub_elements": sub_elements
                    }
                    
                except (ValueError, IndexError):
                    continue
        
        print(f"[SVGParser] Encontrados {len(self.slots)} slots")
    
    def _get_bounding_box(self, elem) -> tuple:
        """Extrai bounding box de um elemento."""
        # Para grupos, tenta pegar do primeiro rect filho
        rect = elem.find(".//{http://www.w3.org/2000/svg}rect")
        if rect is not None:
            return (
                float(rect.get("x", 0)),
                float(rect.get("y", 0)),
                float(rect.get("width", 100)),
                float(rect.get("height", 100))
            )
        
        # Fallback para transform/use
        return (0, 0, 200, 250)
    
    def _find_sub_elements(self, slot_elem) -> Dict:
        """Identifica sub-elementos dentro de um slot."""
        sub = {}
        
        for child in slot_elem.iter():
            child_id = child.get("id", "").upper()
            
            if "ALVO_IMAGEM" in child_id or "IMG" in child_id:
                sub["image"] = child
            elif "NOME" in child_id:
                sub["name"] = child
            elif "PRECO_INT" in child_id:
                sub["price_int"] = child
            elif "PRECO_DEC" in child_id:
                sub["price_dec"] = child
            elif "PRECO" in child_id:
                sub["price_full"] = child
            elif "UNIDADE" in child_id or "PESO" in child_id:
                sub["unit"] = child
            elif "LEGAL" in child_id:
                sub["legal"] = child
        
        return sub
    
    def get_slot_count(self) -> int:
        """Retorna quantidade de slots."""
        return len(self.slots)
    
    def get_viewbox_size(self) -> tuple:
        """Retorna tamanho do viewbox (width, height)."""
        return (self.viewbox[2], self.viewbox[3])

"""
AutoTabloide AI - Smart Slot Item
=================================
PROTOCOLO DE CONVERGÊNCIA 260 - Fase 3 (Passos 86-100)
Item de slot inteligente com drop handling real.
"""

from __future__ import annotations
from pathlib import Path
from typing import Dict, Optional, Any
from dataclasses import dataclass, field
import json
import logging

from PySide6.QtCore import Qt, QRectF, QPointF, Signal, QObject
from PySide6.QtWidgets import (
    QGraphicsItem, QGraphicsRectItem, QGraphicsPixmapItem,
    QGraphicsTextItem, QGraphicsDropShadowEffect,
    QMenu, QMessageBox
)
from PySide6.QtGui import (
    QPainter, QPen, QColor, QBrush, QPixmap,
    QFont, QFontMetrics, QPainterPath
)

logger = logging.getLogger("SmartSlot")


@dataclass
class SlotData:
    """Dados de um slot."""
    slot_id: str
    slot_index: int
    rect: QRectF
    product: Optional[Dict] = None
    override_price: Optional[float] = None
    override_name: Optional[str] = None
    image_offset: QPointF = field(default_factory=lambda: QPointF(0, 0))
    image_scale: float = 1.0
    locked: bool = False


class SmartSlotItem(QGraphicsRectItem):
    """
    Item de slot inteligente para o Ateliê.
    
    Features:
    - Drop zone para produtos
    - Imagem com fitting automático
    - Preço formatado (inteiro + centavos)
    - Override manual
    - Context menu
    """
    
    MIME_TYPE = "application/x-autotabloide-product"
    
    def __init__(
        self,
        slot_id: str,
        slot_index: int,
        rect: QRectF,
        parent=None
    ):
        super().__init__(rect, parent)
        
        self.slot_data = SlotData(
            slot_id=slot_id,
            slot_index=slot_index,
            rect=rect
        )
        
        self._setup_appearance()
        self._setup_children()
        
        # Aceita drops
        self.setAcceptDrops(True)
        self.setAcceptHoverEvents(True)
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)
        
        # Estado
        self._hover = False
        self._drag_over = False
    
    def _setup_appearance(self):
        """Configura aparência do slot."""
        self.setPen(QPen(QColor("#CCCCCC"), 0.5))
        self.setBrush(QBrush(QColor("#FFFFFF")))
        self.setZValue(10)
    
    def _setup_children(self):
        """Cria itens filhos (imagem, texto, preço)."""
        rect = self.rect()
        
        # Área da imagem (60% superior)
        img_height = rect.height() * 0.6
        self._image_rect = QRectF(
            rect.x() + 5,
            rect.y() + 5,
            rect.width() - 10,
            img_height - 10
        )
        
        # Item de imagem
        self._image_item = QGraphicsPixmapItem(self)
        self._image_item.setPos(self._image_rect.topLeft())
        
        # Texto do nome
        self._name_item = QGraphicsTextItem(self)
        self._name_item.setDefaultTextColor(QColor("#333333"))
        self._name_item.setFont(QFont("Roboto", 8))
        self._name_item.setPos(rect.x() + 5, rect.y() + img_height)
        self._name_item.setTextWidth(rect.width() - 10)
        
        # Texto do preço
        self._price_item = QGraphicsTextItem(self)
        self._price_item.setDefaultTextColor(QColor("#E53935"))
        self._price_item.setFont(QFont("Roboto", 14, QFont.Bold))
        self._price_item.setPos(rect.x() + 5, rect.y() + rect.height() - 30)
    
    # =========================================================================
    # DROP HANDLING
    # =========================================================================
    
    def dragEnterEvent(self, event):
        """Produto entra na área."""
        if event.mimeData().hasFormat(self.MIME_TYPE):
            event.acceptProposedAction()
            self._drag_over = True
            self.update()
        else:
            event.ignore()
    
    def dragLeaveEvent(self, event):
        """Produto sai da área."""
        self._drag_over = False
        self.update()
    
    def dropEvent(self, event):
        """Produto solto no slot."""
        self._drag_over = False
        
        if not event.mimeData().hasFormat(self.MIME_TYPE):
            event.ignore()
            return
        
        try:
            # Parseia JSON do payload
            data = event.mimeData().data(self.MIME_TYPE).data()
            products = json.loads(data.decode("utf-8"))
            
            if products:
                product = products[0]  # Primeiro produto
                self._set_product(product)
                
                logger.info(f"[Slot {self.slot_data.slot_index}] Produto: {product.get('nome_sanitizado')}")
                
            event.acceptProposedAction()
            
        except Exception as e:
            logger.error(f"Drop error: {e}")
            event.ignore()
        
        self.update()
    
    def _set_product(self, product: Dict):
        """Define produto no slot."""
        self.slot_data.product = product
        
        # Atualiza nome
        name = product.get("nome_sanitizado", "")
        self._name_item.setPlainText(self._truncate_text(name, 50))
        
        # Atualiza preço
        price = product.get("preco_venda_atual", 0)
        self._price_item.setHtml(self._format_price(price))
        
        # Carrega imagem
        img_path = product.get("caminho_imagem_final")
        if img_path and Path(img_path).exists():
            self._load_image(img_path)
        else:
            self._show_placeholder()
    
    def _load_image(self, path: str):
        """Carrega e ajusta imagem."""
        pixmap = QPixmap(path)
        
        if pixmap.isNull():
            self._show_placeholder()
            return
        
        # Fit na área
        scaled = pixmap.scaled(
            int(self._image_rect.width()),
            int(self._image_rect.height()),
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation
        )
        
        self._image_item.setPixmap(scaled)
        
        # Centraliza
        x_off = (self._image_rect.width() - scaled.width()) / 2
        y_off = (self._image_rect.height() - scaled.height()) / 2
        self._image_item.setPos(
            self._image_rect.x() + x_off,
            self._image_rect.y() + y_off
        )
    
    def _show_placeholder(self):
        """Mostra placeholder quando sem imagem."""
        self._image_item.setPixmap(QPixmap())
    
    def _format_price(self, price: float) -> str:
        """Formata preço com centavos menores."""
        if not price:
            return "---"
        
        inteiro = int(price)
        centavos = int((price - inteiro) * 100)
        
        return (
            f'<span style="font-size:10px;">R$</span> '
            f'<span style="font-size:18px;font-weight:bold;">{inteiro}</span>'
            f'<span style="font-size:10px;vertical-align:super;">,{centavos:02d}</span>'
        )
    
    def _truncate_text(self, text: str, max_len: int) -> str:
        """Trunca texto se necessário."""
        if len(text) <= max_len:
            return text
        return text[:max_len-3] + "..."
    
    # =========================================================================
    # CONTEXT MENU
    # =========================================================================
    
    def contextMenuEvent(self, event):
        """Menu de contexto."""
        menu = QMenu()
        
        if self.slot_data.product:
            action_clear = menu.addAction("🗑️ Limpar Slot")
            action_clear.triggered.connect(self.clear_slot)
            
            action_edit = menu.addAction("✏️ Editar Override")
            action_edit.triggered.connect(self._show_override_dialog)
            
            menu.addSeparator()
        
        action_lock = menu.addAction("🔒 Bloquear" if not self.slot_data.locked else "🔓 Desbloquear")
        action_lock.triggered.connect(self._toggle_lock)
        
        menu.exec(event.screenPos())
    
    def clear_slot(self):
        """Limpa o slot."""
        self.slot_data.product = None
        self.slot_data.override_price = None
        self.slot_data.override_name = None
        
        self._name_item.setPlainText("")
        self._price_item.setPlainText("")
        self._image_item.setPixmap(QPixmap())
        
        self.update()
    
    def _show_override_dialog(self):
        """Mostra diálogo de override para nome e preço customizados."""
        from PySide6.QtWidgets import QDialog, QVBoxLayout, QFormLayout, QLineEdit, QDialogButtonBox
        
        if not self.slot_data.product:
            return
        
        dialog = QDialog()
        dialog.setWindowTitle("Override de Produto")
        dialog.setMinimumWidth(350)
        
        layout = QVBoxLayout(dialog)
        form = QFormLayout()
        
        # Nome override
        name_input = QLineEdit()
        current_name = self.slot_data.override_name or self.slot_data.product.get("nome_sanitizado", "")
        name_input.setText(current_name)
        name_input.setPlaceholderText("Nome customizado...")
        form.addRow("Nome:", name_input)
        
        # Preço override
        price_input = QLineEdit()
        current_price = self.slot_data.override_price or self.slot_data.product.get("preco_venda_atual", 0)
        price_input.setText(f"{float(current_price):.2f}")
        price_input.setPlaceholderText("Preço customizado...")
        form.addRow("Preço:", price_input)
        
        layout.addLayout(form)
        
        # Botões
        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)
        
        if dialog.exec() == QDialog.Accepted:
            # Aplica overrides
            new_name = name_input.text().strip()
            if new_name and new_name != self.slot_data.product.get("nome_sanitizado", ""):
                self.slot_data.override_name = new_name
                self._name_item.setPlainText(self._truncate_text(new_name, 50))
            
            try:
                new_price = float(price_input.text().replace(",", "."))
                if new_price != self.slot_data.product.get("preco_venda_atual", 0):
                    self.slot_data.override_price = new_price
                    self._price_item.setHtml(self._format_price(new_price))
            except ValueError:
                pass  # Mantém preço original se inválido
            
            self.update()
    
    def _toggle_lock(self):
        """Alterna bloqueio."""
        self.slot_data.locked = not self.slot_data.locked
        self.setAcceptDrops(not self.slot_data.locked)
        self.update()
    
    # =========================================================================
    # VISUAL FEEDBACK
    # =========================================================================
    
    def paint(self, painter: QPainter, option, widget):
        """Desenha o slot."""
        super().paint(painter, option, widget)
        
        # Highlight quando drag over
        if self._drag_over:
            painter.setPen(QPen(QColor("#4CAF50"), 3))
            painter.setBrush(QBrush(QColor(76, 175, 80, 50)))
            painter.drawRect(self.rect())
        
        # Locked indicator
        if self.slot_data.locked:
            painter.setPen(QPen(QColor("#FF9800"), 2))
            painter.drawRect(self.rect().adjusted(2, 2, -2, -2))
        
        # Selected
        if self.isSelected():
            painter.setPen(QPen(QColor("#6C5CE7"), 2, Qt.DashLine))
            painter.drawRect(self.rect())
    
    def hoverEnterEvent(self, event):
        self._hover = True
        self.update()
    
    def hoverLeaveEvent(self, event):
        self._hover = False
        self.update()
    
    # =========================================================================
    # SERIALIZATION
    # =========================================================================
    
    def to_dict(self) -> Dict:
        """Serializa para JSON."""
        return {
            "slot_id": self.slot_data.slot_id,
            "slot_index": self.slot_data.slot_index,
            "product_id": self.slot_data.product.get("id") if self.slot_data.product else None,
            "override_price": self.slot_data.override_price,
            "override_name": self.slot_data.override_name,
            "locked": self.slot_data.locked,
        }
    
    def from_dict(self, data: Dict, product: Dict = None):
        """Restaura de JSON."""
        self.slot_data.override_price = data.get("override_price")
        self.slot_data.override_name = data.get("override_name")
        self.slot_data.locked = data.get("locked", False)
        
        if product:
            self._set_product(product)
        
        self.setAcceptDrops(not self.slot_data.locked)

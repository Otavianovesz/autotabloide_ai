"""
AutoTabloide AI - Scene Builder
===============================
PROTOCOLO DE CONVERGÊNCIA 260 - Fase 3 (Passos 81-85)
Constrói QGraphicsScene a partir do SVG template.
"""

from __future__ import annotations
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import logging
import re
import xml.etree.ElementTree as ET

from PySide6.QtCore import Qt, QRectF
from PySide6.QtWidgets import QGraphicsScene, QGraphicsRectItem
from PySide6.QtGui import QColor, QBrush, QPen

from src.qt.graphics.smart_slot import SmartSlotItem

logger = logging.getLogger("SceneBuilder")


MM_TO_PX = 3.7795275591  # 96 DPI


@dataclass
class ParsedSlot:
    """Slot extraído do SVG."""
    slot_id: str
    slot_index: int
    x: float
    y: float
    width: float
    height: float
    img_rect: Optional[QRectF] = None


class SceneBuilder:
    """
    Constrói QGraphicsScene a partir de SVG template.
    
    Features:
    - Parseia IDs de slots (SLOT_01, SLOT_02, etc)
    - Extrai retângulos de imagem
    - Cria SmartSlotItem para cada slot
    - Suporta diferentes templates
    """
    
    def __init__(self, svg_path: str):
        self.svg_path = Path(svg_path)
        self._tree: Optional[ET.ElementTree] = None
        self._root: Optional[ET.Element] = None
        self._viewbox: Tuple[float, float, float, float] = (0, 0, 210, 297)
        self._slots: List[ParsedSlot] = []
    
    def parse(self) -> bool:
        """Parseia o SVG."""
        if not self.svg_path.exists():
            logger.error(f"SVG não encontrado: {self.svg_path}")
            return False
        
        try:
            self._tree = ET.parse(self.svg_path)
            self._root = self._tree.getroot()
            
            # Extrai viewBox
            self._parse_viewbox()
            
            # Encontra slots
            self._find_slots()
            
            logger.info(f"[SceneBuilder] Parsed {len(self._slots)} slots")
            return True
            
        except Exception as e:
            logger.error(f"Parse error: {e}")
            return False
    
    def _parse_viewbox(self):
        """Extrai dimensões do viewBox."""
        viewbox = self._root.get("viewBox")
        if viewbox:
            parts = viewbox.split()
            if len(parts) == 4:
                self._viewbox = tuple(float(p) for p in parts)
    
    def _find_slots(self):
        """Encontra grupos de slot no SVG."""
        self._slots = []
        
        # Busca elementos com ID SLOT_XX
        ns = {"svg": "http://www.w3.org/2000/svg"}
        
        for elem in self._root.iter():
            elem_id = elem.get("id", "")
            
            if elem_id.startswith("SLOT_"):
                slot = self._parse_slot_group(elem, elem_id)
                if slot:
                    self._slots.append(slot)
    
    def _parse_slot_group(self, group: ET.Element, slot_id: str) -> Optional[ParsedSlot]:
        """Parseia um grupo de slot."""
        # Extrai índice
        match = re.search(r"SLOT_(\d+)", slot_id)
        if not match:
            return None
        
        slot_index = int(match.group(1))
        
        # Busca transform
        transform = group.get("transform", "")
        tx, ty = 0.0, 0.0
        
        translate_match = re.search(r"translate\(([\d.-]+),?\s*([\d.-]+)?\)", transform)
        if translate_match:
            tx = float(translate_match.group(1))
            ty = float(translate_match.group(2) or 0)
        
        # Busca primeiro rect para dimensões
        rect_elem = None
        for child in group:
            tag = child.tag.split("}")[-1]  # Remove namespace
            if tag == "rect":
                rect_elem = child
                break
        
        if rect_elem is None:
            # Usa dimensões padrão
            return ParsedSlot(
                slot_id=slot_id,
                slot_index=slot_index,
                x=tx * MM_TO_PX,
                y=ty * MM_TO_PX,
                width=95 * MM_TO_PX,
                height=125 * MM_TO_PX
            )
        
        x = float(rect_elem.get("x", 0)) + tx
        y = float(rect_elem.get("y", 0)) + ty
        w = float(rect_elem.get("width", 95))
        h = float(rect_elem.get("height", 125))
        
        # Converte mm para px
        return ParsedSlot(
            slot_id=slot_id,
            slot_index=slot_index,
            x=x * MM_TO_PX,
            y=y * MM_TO_PX,
            width=w * MM_TO_PX,
            height=h * MM_TO_PX
        )
    
    def build_scene(self) -> QGraphicsScene:
        """Constrói a cena Qt."""
        # Dimensões em pixels
        doc_w = self._viewbox[2] * MM_TO_PX
        doc_h = self._viewbox[3] * MM_TO_PX
        
        scene = QGraphicsScene(0, 0, doc_w, doc_h)
        
        # Background
        bg = QGraphicsRectItem(0, 0, doc_w, doc_h)
        bg.setBrush(QBrush(QColor("#FFFFFF")))
        bg.setPen(QPen(Qt.NoPen))
        bg.setZValue(0)
        scene.addItem(bg)
        
        # Cria SmartSlotItem para cada slot
        for slot in self._slots:
            rect = QRectF(slot.x, slot.y, slot.width, slot.height)
            
            item = SmartSlotItem(
                slot_id=slot.slot_id,
                slot_index=slot.slot_index,
                rect=rect
            )
            
            scene.addItem(item)
            logger.debug(f"[SceneBuilder] Added {slot.slot_id}")
        
        return scene
    
    @property
    def slot_count(self) -> int:
        return len(self._slots)
    
    @property
    def document_size(self) -> Tuple[float, float]:
        """Tamanho do documento em pixels."""
        return (
            self._viewbox[2] * MM_TO_PX,
            self._viewbox[3] * MM_TO_PX
        )


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def build_scene_from_template(svg_path: str) -> Optional[QGraphicsScene]:
    """Constrói cena a partir de template."""
    builder = SceneBuilder(svg_path)
    
    if not builder.parse():
        return None
    
    return builder.build_scene()


def get_available_templates(templates_dir: str = None) -> List[Dict]:
    """Lista templates disponíveis."""
    templates_dir = Path(templates_dir or "AutoTabloide_System_Root/library/svg_source")
    
    templates = []
    
    for svg_path in templates_dir.glob("*.svg"):
        builder = SceneBuilder(str(svg_path))
        if builder.parse():
            templates.append({
                "path": str(svg_path),
                "name": svg_path.stem,
                "slots": builder.slot_count,
                "size": builder.document_size,
            })
    
    return templates

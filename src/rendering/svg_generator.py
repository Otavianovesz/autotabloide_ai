"""
AutoTabloide AI - SVG Generator
================================
PROTOCOLO DE CONVERGÊNCIA 260 - Fase 4 (Passos 161, 171-173)
Gera SVG final com produtos injetados para renderização.
"""

from __future__ import annotations
from pathlib import Path
from typing import Dict, List, Optional
import logging
import xml.etree.ElementTree as ET
import base64
import re

logger = logging.getLogger("SVGGenerator")


MM_TO_PX = 3.7795275591


class SVGGenerator:
    """
    Gera SVG final para renderização.
    
    Features:
    - Injeta imagens de produtos
    - Atualiza textos de preço/nome
    - Adiciona bleed e crop marks
    - Converte imagens para base64
    """
    
    def __init__(self, template_path: str):
        self._template_path = Path(template_path)
        self._tree: Optional[ET.ElementTree] = None
        self._root: Optional[ET.Element] = None
        self._ns = {"svg": "http://www.w3.org/2000/svg", "xlink": "http://www.w3.org/1999/xlink"}
    
    def load_template(self) -> bool:
        """Carrega template."""
        if not self._template_path.exists():
            logger.error(f"Template not found: {self._template_path}")
            return False
        
        try:
            # Registra namespaces
            ET.register_namespace("", "http://www.w3.org/2000/svg")
            ET.register_namespace("xlink", "http://www.w3.org/1999/xlink")
            
            self._tree = ET.parse(self._template_path)
            self._root = self._tree.getroot()
            return True
            
        except Exception as e:
            logger.error(f"Parse error: {e}")
            return False
    
    def inject_product(self, slot_index: int, product: Dict, override_price: float = None):
        """Injeta produto no slot."""
        # Encontra elementos do slot
        slot_id = f"SLOT_{slot_index:02d}"
        img_id = f"IMG_{slot_index:02d}"
        name_id = f"TXT_NOME_{slot_index:02d}"
        price_int_id = f"TXT_PRECO_INT_{slot_index:02d}"
        price_dec_id = f"TXT_PRECO_DEC_{slot_index:02d}"
        
        # Atualiza imagem
        img_path = product.get("caminho_imagem_final")
        if img_path and Path(img_path).exists():
            self._inject_image(img_id, img_path)
        
        # Atualiza nome
        name = product.get("nome_sanitizado", "")
        self._update_text(name_id, name)
        
        # Atualiza preço
        price = override_price or product.get("preco_venda_atual", 0)
        inteiro = int(price)
        centavos = int((price - inteiro) * 100)
        
        self._update_text(price_int_id, str(inteiro))
        self._update_text(price_dec_id, f",{centavos:02d}")
    
    def _inject_image(self, element_id: str, image_path: str):
        """Injeta imagem como base64."""
        elem = self._find_by_id(element_id)
        if elem is None:
            return
        
        # Converte para base64
        try:
            with open(image_path, "rb") as f:
                data = base64.b64encode(f.read()).decode("utf-8")
            
            # Determina mime type
            suffix = Path(image_path).suffix.lower()
            mime = {
                ".png": "image/png",
                ".jpg": "image/jpeg",
                ".jpeg": "image/jpeg",
                ".webp": "image/webp",
            }.get(suffix, "image/png")
            
            # Cria elemento image
            # Obtém dimensões do placeholder
            x = elem.get("x", "0")
            y = elem.get("y", "0")
            w = elem.get("width", "100")
            h = elem.get("height", "100")
            
            # Substitui rect por image
            parent = self._find_parent(elem)
            if parent is not None:
                idx = list(parent).index(elem)
                parent.remove(elem)
                
                img = ET.Element("{http://www.w3.org/2000/svg}image")
                img.set("id", element_id)
                img.set("x", x)
                img.set("y", y)
                img.set("width", w)
                img.set("height", h)
                img.set("{http://www.w3.org/1999/xlink}href", f"data:{mime};base64,{data}")
                img.set("preserveAspectRatio", "xMidYMid slice")
                
                parent.insert(idx, img)
                
        except Exception as e:
            logger.error(f"Image inject error: {e}")
    
    def _update_text(self, element_id: str, text: str):
        """Atualiza conteúdo de texto."""
        elem = self._find_by_id(element_id)
        if elem is not None:
            elem.text = text
    
    def _find_by_id(self, element_id: str) -> Optional[ET.Element]:
        """Encontra elemento por ID."""
        for elem in self._root.iter():
            if elem.get("id") == element_id:
                return elem
        return None
    
    def _find_parent(self, child: ET.Element) -> Optional[ET.Element]:
        """Encontra elemento pai."""
        for elem in self._root.iter():
            if child in list(elem):
                return elem
        return None
    
    def add_bleed(self, bleed_mm: float = 3.0):
        """Adiciona área de sangria."""
        viewbox = self._root.get("viewBox", "0 0 210 297")
        parts = viewbox.split()
        
        if len(parts) == 4:
            x, y, w, h = [float(p) for p in parts]
            # Expande viewbox
            new_viewbox = f"{x-bleed_mm} {y-bleed_mm} {w+2*bleed_mm} {h+2*bleed_mm}"
            self._root.set("viewBox", new_viewbox)
    
    def add_crop_marks(self, bleed_mm: float = 3.0, mark_length: float = 5.0, offset: float = 3.0):
        """Adiciona marcas de corte."""
        viewbox = self._root.get("viewBox", "0 0 210 297")
        parts = viewbox.split()
        
        if len(parts) != 4:
            return
        
        x, y, w, h = [float(p) for p in parts]
        
        # Cria grupo para marcas
        marks = ET.SubElement(self._root, "{http://www.w3.org/2000/svg}g")
        marks.set("id", "CROP_MARKS")
        marks.set("stroke", "#000000")
        marks.set("stroke-width", "0.25")
        marks.set("fill", "none")
        
        # Cantos
        corners = [
            (0, 0),           # Top-left
            (w-2*bleed_mm, 0),           # Top-right
            (0, h-2*bleed_mm),           # Bottom-left
            (w-2*bleed_mm, h-2*bleed_mm),           # Bottom-right
        ]
        
        for cx, cy in corners:
            # Linha horizontal
            line_h = ET.SubElement(marks, "{http://www.w3.org/2000/svg}line")
            line_h.set("x1", str(cx - offset - mark_length))
            line_h.set("y1", str(cy))
            line_h.set("x2", str(cx - offset))
            line_h.set("y2", str(cy))
            
            # Linha vertical
            line_v = ET.SubElement(marks, "{http://www.w3.org/2000/svg}line")
            line_v.set("x1", str(cx))
            line_v.set("y1", str(cy - offset - mark_length))
            line_v.set("x2", str(cx))
            line_v.set("y2", str(cy - offset))
    
    def save(self, output_path: str) -> bool:
        """Salva SVG gerado."""
        try:
            self._tree.write(output_path, encoding="unicode", xml_declaration=True)
            logger.info(f"[SVG] Saved: {output_path}")
            return True
        except Exception as e:
            logger.error(f"Save error: {e}")
            return False
    
    def generate_for_print(
        self,
        output_path: str,
        slot_products: Dict[int, Dict],
        add_bleed: bool = True,
        add_marks: bool = True
    ) -> bool:
        """Gera SVG completo para impressão."""
        if not self.load_template():
            return False
        
        # Injeta produtos
        for slot_index, product in slot_products.items():
            self.inject_product(slot_index, product)
        
        # Adiciona bleed
        if add_bleed:
            self.add_bleed()
        
        # Adiciona crop marks
        if add_marks:
            self.add_crop_marks()
        
        return self.save(output_path)


# =============================================================================
# HELPER
# =============================================================================

def generate_print_svg(
    template_path: str,
    output_path: str,
    slot_products: Dict[int, Dict]
) -> bool:
    """Helper para gerar SVG de impressão."""
    gen = SVGGenerator(template_path)
    return gen.generate_for_print(output_path, slot_products)

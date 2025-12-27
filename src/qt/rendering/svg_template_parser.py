"""
AutoTabloide AI - SVG Template Parser Industrial Grade
=======================================================
PROTOCOLO DE CONVERGÊNCIA INDUSTRIAL - Fase 2
Passos 19-21: Parser de SVG com lxml, Mapeamento de IDs, Smart Items.

Este parser DISSECA o SVG em objetos QGraphicsItem editáveis.
Não é uma visualização estática - é um editor vetorial real.
"""

from __future__ import annotations
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from lxml import etree
import re
import json

from PySide6.QtCore import QRectF, QPointF
from PySide6.QtWidgets import QGraphicsScene

# Namespace SVG
SVG_NS = "http://www.w3.org/2000/svg"
XLINK_NS = "http://www.w3.org/1999/xlink"
NSMAP = {
    "svg": SVG_NS,
    "xlink": XLINK_NS,
}


@dataclass
class SlotDefinition:
    """Definição de um slot detectado no SVG."""
    index: int
    slot_id: str
    x: float
    y: float
    width: float
    height: float
    
    # IDs dos elementos internos
    image_target_id: Optional[str] = None
    name_text_id: Optional[str] = None
    price_text_id: Optional[str] = None
    price_integer_id: Optional[str] = None
    price_decimal_id: Optional[str] = None
    unit_text_id: Optional[str] = None
    de_price_id: Optional[str] = None
    por_price_id: Optional[str] = None
    
    # Metadados
    extra_elements: Dict[str, str] = field(default_factory=dict)


@dataclass
class TemplateInfo:
    """Informações completas do template SVG."""
    path: str
    viewbox: Tuple[float, float, float, float]  # x, y, width, height
    width_mm: float
    height_mm: float
    dpi: float
    
    slots: List[SlotDefinition] = field(default_factory=list)
    static_elements: List[Dict] = field(default_factory=list)
    
    # Metadados
    title: Optional[str] = None
    created_by: Optional[str] = None


class SvgTemplateParser:
    """
    Parser industrial de templates SVG.
    
    REGRA DE OURO: Cada elemento com ID reservado vira um objeto editável.
    
    IDs Reservados (Codex Vol. II):
        - SLOT_XX: Container de slot (grupo)
        - ALVO_IMAGEM_XX: Área de imagem
        - TXT_NOME_XX: Texto do nome do produto
        - TXT_PRECO_XX: Texto do preço completo
        - TXT_PRECO_INTEIRO_XX: Parte inteira do preço
        - TXT_PRECO_DECIMAL_XX: Centavos
        - TXT_PRECO_DE_XX: Preço anterior
        - TXT_PRECO_POR_XX: Preço atual
        - TXT_UNIDADE_XX: Unidade/peso
    """
    
    # Padrões de IDs
    SLOT_PATTERN = re.compile(r'^SLOT_(\d+)$', re.IGNORECASE)
    IMAGE_PATTERN = re.compile(r'^ALVO_IMAGEM(?:_(\d+))?$', re.IGNORECASE)
    NAME_PATTERN = re.compile(r'^TXT_NOME(?:_(\d+))?$', re.IGNORECASE)
    PRICE_PATTERN = re.compile(r'^TXT_PRECO(?:_(\d+))?$', re.IGNORECASE)
    PRICE_INT_PATTERN = re.compile(r'^TXT_PRECO_INTEIRO(?:_(\d+))?$', re.IGNORECASE)
    PRICE_DEC_PATTERN = re.compile(r'^TXT_PRECO_DECIMAL(?:_(\d+))?$', re.IGNORECASE)
    PRICE_DE_PATTERN = re.compile(r'^TXT_PRECO_DE(?:_(\d+))?$', re.IGNORECASE)
    PRICE_POR_PATTERN = re.compile(r'^TXT_PRECO_POR(?:_(\d+))?$', re.IGNORECASE)
    UNIT_PATTERN = re.compile(r'^TXT_UNIDADE(?:_(\d+))?$', re.IGNORECASE)
    
    def __init__(self):
        self._tree: Optional[etree._ElementTree] = None
        self._root: Optional[etree._Element] = None
        self._template_info: Optional[TemplateInfo] = None
        self._element_index: Dict[str, etree._Element] = {}
    
    def parse(self, svg_path: str) -> Optional[TemplateInfo]:
        """
        Faz parsing completo do SVG.
        
        Args:
            svg_path: Caminho do arquivo SVG
            
        Returns:
            TemplateInfo com todos os dados do template
        """
        path = Path(svg_path)
        if not path.exists():
            print(f"[SVGParser] Arquivo não encontrado: {svg_path}")
            return None
        
        try:
            # Parser seguro contra XXE
            parser = etree.XMLParser(
                resolve_entities=False,
                no_network=True,
                remove_comments=True,
            )
            
            self._tree = etree.parse(str(path), parser)
            self._root = self._tree.getroot()
            
            # Extrai ViewBox
            viewbox = self._parse_viewbox()
            width_mm, height_mm = self._parse_dimensions()
            
            # Cria TemplateInfo base
            self._template_info = TemplateInfo(
                path=str(path),
                viewbox=viewbox,
                width_mm=width_mm,
                height_mm=height_mm,
                dpi=300.0,  # Padrão para impressão
            )
            
            # Indexa todos os elementos com ID
            self._build_element_index()
            
            # Detecta e mapeia slots
            self._detect_slots()
            
            # Identifica elementos estáticos
            self._identify_static_elements()
            
            return self._template_info
            
        except Exception as e:
            print(f"[SVGParser] Erro ao parsear: {e}")
            return None
    
    def parse_from_string(self, svg_content: str) -> Optional[TemplateInfo]:
        """Parse SVG a partir de string."""
        try:
            parser = etree.XMLParser(
                resolve_entities=False,
                no_network=True,
            )
            
            self._root = etree.fromstring(svg_content.encode(), parser)
            self._tree = etree.ElementTree(self._root)
            
            viewbox = self._parse_viewbox()
            width_mm, height_mm = self._parse_dimensions()
            
            self._template_info = TemplateInfo(
                path="<string>",
                viewbox=viewbox,
                width_mm=width_mm,
                height_mm=height_mm,
                dpi=300.0,
            )
            
            self._build_element_index()
            self._detect_slots()
            self._identify_static_elements()
            
            return self._template_info
            
        except Exception as e:
            print(f"[SVGParser] Erro ao parsear string: {e}")
            return None
    
    def _parse_viewbox(self) -> Tuple[float, float, float, float]:
        """Extrai dimensões do ViewBox."""
        viewbox_str = self._root.get("viewBox", "0 0 800 600")
        parts = viewbox_str.split()
        
        try:
            return (
                float(parts[0]),
                float(parts[1]),
                float(parts[2]),
                float(parts[3]),
            )
        except (ValueError, IndexError):
            return (0, 0, 800, 600)
    
    def _parse_dimensions(self) -> Tuple[float, float]:
        """Extrai dimensões em mm."""
        width_str = self._root.get("width", "210mm")
        height_str = self._root.get("height", "297mm")
        
        def parse_unit(value: str) -> float:
            """Converte valor com unidade para mm."""
            value = value.strip().lower()
            
            if value.endswith("mm"):
                return float(value[:-2])
            elif value.endswith("cm"):
                return float(value[:-2]) * 10
            elif value.endswith("in"):
                return float(value[:-2]) * 25.4
            elif value.endswith("pt"):
                return float(value[:-2]) * 0.3528
            elif value.endswith("px"):
                # Assume 96 DPI
                return float(value[:-2]) / 96 * 25.4
            else:
                try:
                    return float(value)
                except ValueError:
                    return 210.0  # A4 padrão
        
        return parse_unit(width_str), parse_unit(height_str)
    
    def _build_element_index(self):
        """Cria índice de todos os elementos com ID."""
        self._element_index.clear()
        
        for element in self._root.iter():
            elem_id = element.get("id")
            if elem_id:
                self._element_index[elem_id] = element
    
    def _detect_slots(self):
        """Detecta e mapeia slots do template."""
        slots_dict: Dict[int, SlotDefinition] = {}
        
        for elem_id, element in self._element_index.items():
            # Detecta containers SLOT_XX
            match = self.SLOT_PATTERN.match(elem_id)
            if match:
                slot_index = int(match.group(1))
                bounds = self._get_element_bounds(element)
                
                slot = SlotDefinition(
                    index=slot_index,
                    slot_id=elem_id,
                    x=bounds.x(),
                    y=bounds.y(),
                    width=bounds.width(),
                    height=bounds.height(),
                )
                
                # Busca elementos internos ao slot
                self._find_slot_children(element, slot)
                slots_dict[slot_index] = slot
            
            # Elementos soltos (sem slot pai)
            else:
                self._match_loose_element(elem_id, element, slots_dict)
        
        # Ordena slots
        self._template_info.slots = [
            slots_dict[i] for i in sorted(slots_dict.keys())
        ]
    
    def _get_element_bounds(self, element: etree._Element) -> QRectF:
        """Calcula bounding box de um elemento."""
        tag = self._get_local_tag(element)
        
        if tag == "rect":
            return QRectF(
                float(element.get("x", 0)),
                float(element.get("y", 0)),
                float(element.get("width", 100)),
                float(element.get("height", 100)),
            )
        
        elif tag == "g":
            # Para grupos, combina bounds dos filhos
            min_x, min_y = float('inf'), float('inf')
            max_x, max_y = float('-inf'), float('-inf')
            
            for child in element:
                child_bounds = self._get_element_bounds(child)
                if not child_bounds.isEmpty():
                    min_x = min(min_x, child_bounds.x())
                    min_y = min(min_y, child_bounds.y())
                    max_x = max(max_x, child_bounds.right())
                    max_y = max(max_y, child_bounds.bottom())
            
            if min_x != float('inf'):
                return QRectF(min_x, min_y, max_x - min_x, max_y - min_y)
        
        elif tag == "text":
            x = float(element.get("x", 0))
            y = float(element.get("y", 0))
            # Estimativa baseada em font-size
            font_size = self._parse_font_size(element.get("style", ""))
            return QRectF(x, y - font_size, font_size * 10, font_size * 1.2)
        
        elif tag == "image":
            return QRectF(
                float(element.get("x", 0)),
                float(element.get("y", 0)),
                float(element.get("width", 100)),
                float(element.get("height", 100)),
            )
        
        # Transform
        transform = element.get("transform")
        if transform:
            bounds = self._apply_transform(QRectF(0, 0, 100, 100), transform)
            return bounds
        
        return QRectF()
    
    def _parse_font_size(self, style: str) -> float:
        """Extrai font-size do estilo."""
        match = re.search(r'font-size:\s*(\d+(?:\.\d+)?)', style)
        if match:
            return float(match.group(1))
        return 12.0
    
    def _apply_transform(self, rect: QRectF, transform: str) -> QRectF:
        """Aplica transformação a um retângulo."""
        # Parse translate
        match = re.search(r'translate\(\s*([\d.]+)\s*,\s*([\d.]+)\s*\)', transform)
        if match:
            dx, dy = float(match.group(1)), float(match.group(2))
            return rect.translated(dx, dy)
        return rect
    
    def _get_local_tag(self, element: etree._Element) -> str:
        """Retorna tag sem namespace."""
        tag = element.tag
        if "}" in tag:
            return tag.split("}")[1]
        return tag
    
    def _find_slot_children(self, slot_element: etree._Element, slot: SlotDefinition):
        """Encontra elementos filhos relevantes de um slot."""
        for child in slot_element.iter():
            child_id = child.get("id")
            if not child_id:
                continue
            
            # Imagem
            if self.IMAGE_PATTERN.match(child_id):
                slot.image_target_id = child_id
            
            # Nome
            elif self.NAME_PATTERN.match(child_id):
                slot.name_text_id = child_id
            
            # Preço completo
            elif self.PRICE_PATTERN.match(child_id):
                slot.price_text_id = child_id
            
            # Preço inteiro
            elif self.PRICE_INT_PATTERN.match(child_id):
                slot.price_integer_id = child_id
            
            # Preço decimal
            elif self.PRICE_DEC_PATTERN.match(child_id):
                slot.price_decimal_id = child_id
            
            # Preço De
            elif self.PRICE_DE_PATTERN.match(child_id):
                slot.de_price_id = child_id
            
            # Preço Por
            elif self.PRICE_POR_PATTERN.match(child_id):
                slot.por_price_id = child_id
            
            # Unidade
            elif self.UNIT_PATTERN.match(child_id):
                slot.unit_text_id = child_id
            
            # Outros
            else:
                slot.extra_elements[child_id] = self._get_local_tag(child)
    
    def _match_loose_element(
        self, 
        elem_id: str, 
        element: etree._Element,
        slots_dict: Dict[int, SlotDefinition]
    ):
        """Tenta associar elemento solto a um slot."""
        # Extrai número do ID se houver
        for pattern, setter in [
            (self.IMAGE_PATTERN, "image_target_id"),
            (self.NAME_PATTERN, "name_text_id"),
            (self.PRICE_PATTERN, "price_text_id"),
            (self.PRICE_INT_PATTERN, "price_integer_id"),
            (self.PRICE_DEC_PATTERN, "price_decimal_id"),
            (self.PRICE_DE_PATTERN, "de_price_id"),
            (self.PRICE_POR_PATTERN, "por_price_id"),
            (self.UNIT_PATTERN, "unit_text_id"),
        ]:
            match = pattern.match(elem_id)
            if match:
                slot_num = match.group(1)
                if slot_num:
                    slot_index = int(slot_num)
                    if slot_index not in slots_dict:
                        bounds = self._get_element_bounds(element)
                        slots_dict[slot_index] = SlotDefinition(
                            index=slot_index,
                            slot_id=f"SLOT_{slot_index:02d}",
                            x=bounds.x(),
                            y=bounds.y(),
                            width=bounds.width(),
                            height=bounds.height(),
                        )
                    setattr(slots_dict[slot_index], setter, elem_id)
                break
    
    def _identify_static_elements(self):
        """Identifica elementos que não são editáveis (background)."""
        editable_ids = set()
        
        # Coleta IDs editáveis
        for slot in self._template_info.slots:
            editable_ids.add(slot.slot_id)
            if slot.image_target_id:
                editable_ids.add(slot.image_target_id)
            if slot.name_text_id:
                editable_ids.add(slot.name_text_id)
            if slot.price_text_id:
                editable_ids.add(slot.price_text_id)
            # ... outros
        
        # Elementos não editáveis viram estáticos
        for elem_id, element in self._element_index.items():
            if elem_id not in editable_ids:
                self._template_info.static_elements.append({
                    "id": elem_id,
                    "tag": self._get_local_tag(element),
                })
    
    def get_element_by_id(self, elem_id: str) -> Optional[etree._Element]:
        """Retorna elemento pelo ID."""
        return self._element_index.get(elem_id)
    
    def modify_text(self, elem_id: str, new_text: str) -> bool:
        """Modifica texto de um elemento."""
        element = self.get_element_by_id(elem_id)
        if element is None:
            return False
        
        tag = self._get_local_tag(element)
        if tag == "text":
            # Texto direto
            element.text = new_text
            return True
        
        elif tag == "tspan":
            element.text = new_text
            return True
        
        # Busca tspan filho
        for child in element.iter():
            if self._get_local_tag(child) in ("text", "tspan"):
                child.text = new_text
                return True
        
        return False
    
    def modify_image(self, elem_id: str, image_path: str) -> bool:
        """Modifica referência de imagem."""
        element = self.get_element_by_id(elem_id)
        if element is None:
            return False
        
        # Atualiza href
        element.set(f"{{{XLINK_NS}}}href", image_path)
        element.set("href", image_path)
        
        return True
    
    def to_string(self) -> str:
        """Serializa SVG modificado para string."""
        return etree.tostring(self._root, encoding='unicode', pretty_print=True)
    
    def save(self, output_path: str) -> bool:
        """Salva SVG modificado."""
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(self.to_string())
            return True
        except Exception as e:
            print(f"[SVGParser] Erro ao salvar: {e}")
            return False


# =============================================================================
# TESTES
# =============================================================================
if __name__ == "__main__":
    parser = SvgTemplateParser()
    
    # Teste com SVG de exemplo
    test_svg = '''<?xml version="1.0" encoding="UTF-8"?>
    <svg viewBox="0 0 800 600" width="297mm" height="210mm"
         xmlns="http://www.w3.org/2000/svg"
         xmlns:xlink="http://www.w3.org/1999/xlink">
        <g id="SLOT_01">
            <rect id="ALVO_IMAGEM_01" x="10" y="10" width="180" height="120"/>
            <text id="TXT_NOME_01" x="10" y="150">Nome do Produto</text>
            <text id="TXT_PRECO_01" x="10" y="180">R$ 0,00</text>
        </g>
        <g id="SLOT_02">
            <rect id="ALVO_IMAGEM_02" x="210" y="10" width="180" height="120"/>
            <text id="TXT_NOME_02" x="210" y="150">Produto 2</text>
        </g>
    </svg>'''
    
    info = parser.parse_from_string(test_svg)
    if info:
        print(f"ViewBox: {info.viewbox}")
        print(f"Dimensões: {info.width_mm}mm x {info.height_mm}mm")
        print(f"Slots encontrados: {len(info.slots)}")
        for slot in info.slots:
            print(f"  - Slot {slot.index}: {slot.slot_id}")
            print(f"    Imagem: {slot.image_target_id}")
            print(f"    Nome: {slot.name_text_id}")
            print(f"    Preço: {slot.price_text_id}")

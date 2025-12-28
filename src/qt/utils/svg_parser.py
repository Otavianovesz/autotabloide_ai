"""
AutoTabloide AI - SVG Template Parser for Qt
=============================================
PROTOCOLO DE RETIFICAÇÃO NÍVEL 0 - Fase 3 (Passos 71-80)
Extrai definições de slots do template SVG para uso no Qt Scene Graph.

NÃO renderiza como imagem única - identifica grupos <g id="SLOT_xx">
e calcula BoundingBox para criar SmartSlotItem.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from pathlib import Path
import re
import logging

from lxml import etree

logger = logging.getLogger("SvgTemplateParser")


# =============================================================================
# DATA STRUCTURES
# =============================================================================

@dataclass
class SlotDefinition:
    """Definição de um slot extraída do template."""
    slot_id: str
    slot_index: int
    x: float
    y: float
    width: float
    height: float
    element_type: str = "rect"
    rotation: float = 0.0
    
    # Sub-elementos encontrados
    has_text_nome: bool = False
    has_text_preco: bool = False
    has_text_unidade: bool = False
    has_image_alvo: bool = False
    
    # Posições dos sub-elementos (relativas ao slot)
    nome_rect: Optional[Tuple[float, float, float, float]] = None
    preco_rect: Optional[Tuple[float, float, float, float]] = None
    image_rect: Optional[Tuple[float, float, float, float]] = None


@dataclass
class TemplateDefinition:
    """Definição completa de um template."""
    path: str
    width: float
    height: float
    viewbox: Tuple[float, float, float, float]
    page_count: int = 1
    
    slots: List[SlotDefinition] = field(default_factory=list)
    
    # Elementos globais
    has_legal_text: bool = False
    has_header: bool = False
    has_footer: bool = False
    
    # Background e foreground
    background_elements: List[str] = field(default_factory=list)
    foreground_elements: List[str] = field(default_factory=list)


# =============================================================================
# NAMESPACES
# =============================================================================

NAMESPACES = {
    'svg': 'http://www.w3.org/2000/svg',
    'inkscape': 'http://www.inkscape.org/namespaces/inkscape',
    'xlink': 'http://www.w3.org/1999/xlink'
}


# =============================================================================
# PARSER
# =============================================================================

class SvgTemplateParser:
    """
    Parser de templates SVG para Qt Scene Graph.
    
    REGRA CRÍTICA: Não renderiza SVG como imagem única!
    Em vez disso, extrai posições e dimensões dos slots para
    criar SmartSlotItem interativos no Qt.
    
    Slots são identificados por:
    - <g id="SLOT_01"> ou <rect id="SLOT_01">
    - Grupos contendo TXT_NOME_PRODUTO_01, TXT_PRECO_01, ALVO_IMAGEM_01
    """
    
    # Regex para identificar slots e sub-elementos
    SLOT_PATTERN = re.compile(r'^SLOT_(\d+)$')
    TEXT_NOME_PATTERN = re.compile(r'^TXT_NOME_(?:PRODUTO_)?(\d+)$')
    TEXT_PRECO_PATTERN = re.compile(r'^TXT_PRECO_(?:INT_|DE_|POR_)?(\d+)$')
    TEXT_UNIDADE_PATTERN = re.compile(r'^TXT_UNIDADE_(\d+)$')
    IMAGE_PATTERN = re.compile(r'^(?:ALVO_)?IMAGEM_(\d+)$')
    
    def __init__(self):
        self._tree: Optional[etree._ElementTree] = None
        self._root: Optional[etree._Element] = None
        self._elements: Dict[str, etree._Element] = {}
    
    def parse(self, template_path: str) -> TemplateDefinition:
        """
        Parseia template SVG e extrai definições.
        
        Args:
            template_path: Caminho para o arquivo .svg
            
        Returns:
            TemplateDefinition com slots e metadados
        """
        path = Path(template_path)
        if not path.exists():
            raise FileNotFoundError(f"Template não encontrado: {path}")
        
        # Parser seguro (XXE protection)
        parser = etree.XMLParser(
            resolve_entities=False,
            no_network=True,
            dtd_validation=False
        )
        
        self._tree = etree.parse(str(path), parser)
        self._root = self._tree.getroot()
        
        # Extrai dimensões
        width, height = self._extract_dimensions()
        viewbox = self._extract_viewbox(width, height)
        
        # Indexa elementos por ID
        self._index_elements()
        
        # Extrai slots
        slots = self._extract_slots()
        
        # Detecta elementos globais
        has_legal = any(k.startswith("TXT_LEGAL") for k in self._elements)
        has_header = any(k.startswith("HEADER") for k in self._elements)
        has_footer = any(k.startswith("FOOTER") for k in self._elements)
        
        # Detecta páginas
        page_count = self._detect_pages()
        
        template = TemplateDefinition(
            path=str(path),
            width=width,
            height=height,
            viewbox=viewbox,
            page_count=page_count,
            slots=slots,
            has_legal_text=has_legal,
            has_header=has_header,
            has_footer=has_footer
        )
        
        logger.info(f"Template parseado: {len(slots)} slots, {page_count} páginas")
        return template
    
    def _extract_dimensions(self) -> Tuple[float, float]:
        """Extrai width/height do SVG."""
        width_str = self._root.get('width', '595.28')  # A4 default
        height_str = self._root.get('height', '841.89')
        
        # Remove unidades (px, mm, etc)
        width = self._parse_dimension(width_str)
        height = self._parse_dimension(height_str)
        
        return width, height
    
    def _parse_dimension(self, value: str) -> float:
        """Converte string de dimensão para float."""
        # Remove unidades
        match = re.match(r'^([\d.]+)', value)
        if match:
            return float(match.group(1))
        return 595.28  # Fallback A4
    
    def _extract_viewbox(self, default_w: float, default_h: float) -> Tuple[float, float, float, float]:
        """Extrai ou calcula viewBox."""
        vb = self._root.get('viewBox')
        if vb:
            parts = vb.split()
            if len(parts) == 4:
                return tuple(float(p) for p in parts)
        return (0.0, 0.0, default_w, default_h)
    
    def _index_elements(self):
        """Indexa todos os elementos com ID."""
        self._elements.clear()
        
        for elem in self._root.iter():
            elem_id = elem.get('id')
            if elem_id:
                self._elements[elem_id] = elem
    
    def _extract_slots(self) -> List[SlotDefinition]:
        """Extrai definições de slots."""
        slots = []
        
        for elem_id, elem in self._elements.items():
            match = self.SLOT_PATTERN.match(elem_id)
            if not match:
                continue
            
            slot_index = int(match.group(1))
            
            # Calcula bounding box
            x, y, w, h = self._get_bounding_box(elem)
            
            slot = SlotDefinition(
                slot_id=elem_id,
                slot_index=slot_index,
                x=x, y=y,
                width=w, height=h,
                element_type=self._get_local_name(elem)
            )
            
            # Procura sub-elementos
            self._find_slot_children(slot, elem)
            
            slots.append(slot)
        
        # Ordena por índice
        slots.sort(key=lambda s: s.slot_index)
        
        return slots
    
    def _get_bounding_box(self, elem: etree._Element) -> Tuple[float, float, float, float]:
        """Calcula bounding box de um elemento."""
        tag = self._get_local_name(elem)
        
        if tag == 'rect':
            x = float(elem.get('x', '0'))
            y = float(elem.get('y', '0'))
            w = float(elem.get('width', '100'))
            h = float(elem.get('height', '100'))
            return (x, y, w, h)
        
        elif tag == 'g':
            # Para grupo, precisa calcular de filhos
            return self._calculate_group_bbox(elem)
        
        elif tag == 'image':
            x = float(elem.get('x', '0'))
            y = float(elem.get('y', '0'))
            w = float(elem.get('width', '100'))
            h = float(elem.get('height', '100'))
            return (x, y, w, h)
        
        # Fallback
        return (0, 0, 100, 100)
    
    def _calculate_group_bbox(self, group: etree._Element) -> Tuple[float, float, float, float]:
        """Calcula bbox agregando filhos de um grupo."""
        min_x = float('inf')
        min_y = float('inf')
        max_x = float('-inf')
        max_y = float('-inf')
        
        for child in group.iter():
            if child == group:
                continue
            
            cx, cy, cw, ch = self._get_bounding_box(child)
            min_x = min(min_x, cx)
            min_y = min(min_y, cy)
            max_x = max(max_x, cx + cw)
            max_y = max(max_y, cy + ch)
        
        if min_x == float('inf'):
            return (0, 0, 100, 100)
        
        return (min_x, min_y, max_x - min_x, max_y - min_y)
    
    def _get_local_name(self, elem: etree._Element) -> str:
        """Retorna nome local do elemento (sem namespace)."""
        tag = elem.tag
        if '}' in tag:
            return tag.split('}')[1]
        return tag
    
    def _find_slot_children(self, slot: SlotDefinition, elem: etree._Element):
        """Procura sub-elementos dentro de um slot."""
        suffix = f"_{slot.slot_index:02d}"
        suffix_alt = f"_{slot.slot_index}"
        
        for child_id, child_elem in self._elements.items():
            # Verifica se pertence a este slot
            if not (suffix in child_id or suffix_alt in child_id):
                continue
            
            x, y, w, h = self._get_bounding_box(child_elem)
            # Converte para relativo ao slot
            rel_rect = (x - slot.x, y - slot.y, w, h)
            
            if self.TEXT_NOME_PATTERN.match(child_id):
                slot.has_text_nome = True
                slot.nome_rect = rel_rect
            
            elif self.TEXT_PRECO_PATTERN.match(child_id):
                slot.has_text_preco = True
                slot.preco_rect = rel_rect
            
            elif self.TEXT_UNIDADE_PATTERN.match(child_id):
                slot.has_text_unidade = True
            
            elif self.IMAGE_PATTERN.match(child_id):
                slot.has_image_alvo = True
                slot.image_rect = rel_rect
    
    def _detect_pages(self) -> int:
        """Detecta número de páginas pelo padrão #PAGE_xx."""
        max_page = 1
        
        for elem_id in self._elements:
            match = re.match(r'PAGE_(\d+)', elem_id)
            if match:
                page_num = int(match.group(1))
                max_page = max(max_page, page_num)
        
        return max_page
    
    def get_raw_svg(self) -> bytes:
        """Retorna SVG original como bytes para background rendering."""
        if self._tree is None:
            return b""
        return etree.tostring(self._tree, encoding='utf-8')


# =============================================================================
# HELPER FUNCTION
# =============================================================================

def parse_template(path: str) -> TemplateDefinition:
    """Função helper para parsing rápido."""
    parser = SvgTemplateParser()
    return parser.parse(path)

"""
AutoTabloide AI - Virtual Paper (Paginação Multi-Folha)
========================================================
Sistema de paginação para templates com múltiplas páginas.
Passos 31-34 do Checklist 100.

Funcionalidades:
- Scanning de páginas (#PAGE_01, #PAGE_02, etc)
- Seleção de página ativa
- Renderização por página individual
"""

import re
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from lxml import etree

from src.core.logging_config import get_logger

logger = get_logger("VirtualPaper")


@dataclass
class PageInfo:
    """Informações de uma página do template."""
    page_id: str
    page_number: int
    element: etree._Element
    bounds: Tuple[float, float, float, float]  # x, y, width, height
    slots: List[str]  # IDs dos slots nesta página


class VirtualPaper:
    """
    Gerenciador de paginação multi-folha.
    
    Permite que um único SVG contenha múltiplas páginas/folhas,
    identificadas por grupos com IDs PAGE_01, PAGE_02, etc.
    """
    
    # Regex para identificar grupos de página
    PAGE_PATTERN = re.compile(r'^#?PAGE[_-]?(\d+)$', re.IGNORECASE)
    
    def __init__(self, tree: etree._ElementTree, root: etree._Element):
        """
        Args:
            tree: Árvore DOM do SVG
            root: Elemento raiz do SVG
        """
        self.tree = tree
        self.root = root
        self.pages: Dict[str, PageInfo] = {}
        self._active_page: Optional[str] = None
        
        # Executa scanning inicial
        self.scan_pages()
    
    def scan_pages(self) -> int:
        """
        Escaneia o SVG em busca de grupos de página.
        Passo 31-32 do Checklist.
        
        Procura por elementos <g> com IDs no formato:
        - PAGE_01, PAGE_02, etc
        - #PAGE_1, #PAGE_2, etc
        - PAGE-01, PAGE-02, etc
        
        Returns:
            Número de páginas encontradas
        """
        self.pages.clear()
        
        # Buscar todos os grupos com ID
        for elem in self.root.xpath('//*[@id]'):
            elem_id = elem.get('id', '')
            match = self.PAGE_PATTERN.match(elem_id)
            
            if match:
                page_num = int(match.group(1))
                page_id = f"PAGE_{page_num:02d}"
                
                # Calcular bounds
                bounds = self._calculate_bounds(elem)
                
                # Encontrar slots nesta página
                slots = self._find_slots_in_page(elem)
                
                self.pages[page_id] = PageInfo(
                    page_id=page_id,
                    page_number=page_num,
                    element=elem,
                    bounds=bounds,
                    slots=slots
                )
                
                logger.debug(f"Página encontrada: {page_id} com {len(slots)} slots")
        
        # Se não encontrou páginas explícitas, trata o documento inteiro como página única
        if not self.pages:
            self.pages["PAGE_01"] = PageInfo(
                page_id="PAGE_01",
                page_number=1,
                element=self.root,
                bounds=self._get_viewbox(),
                slots=self._find_all_slots()
            )
            logger.info("Nenhuma página explícita encontrada, usando documento inteiro")
        
        # Define primeira página como ativa
        if self.pages:
            first_page = sorted(self.pages.keys())[0]
            self._active_page = first_page
        
        logger.info(f"Scanning completo: {len(self.pages)} página(s) encontrada(s)")
        return len(self.pages)
    
    def get_page_count(self) -> int:
        """Retorna número total de páginas."""
        return len(self.pages)
    
    def get_page_ids(self) -> List[str]:
        """Retorna lista de IDs de página ordenados."""
        return sorted(self.pages.keys())
    
    def set_active_page(self, page_id: str) -> bool:
        """
        Define página ativa para renderização.
        Passo 33 do Checklist.
        
        Args:
            page_id: ID da página (ex: "PAGE_01")
            
        Returns:
            True se a página existe
        """
        # Normaliza ID
        if not page_id.upper().startswith("PAGE"):
            page_id = f"PAGE_{page_id.zfill(2)}"
        else:
            page_id = page_id.upper().replace("-", "_")
        
        if page_id in self.pages:
            self._active_page = page_id
            logger.debug(f"Página ativa: {page_id}")
            return True
        
        logger.warning(f"Página não encontrada: {page_id}")
        return False
    
    def get_active_page(self) -> Optional[PageInfo]:
        """Retorna informações da página ativa."""
        if self._active_page:
            return self.pages.get(self._active_page)
        return None
    
    def get_slots_for_page(self, page_id: Optional[str] = None) -> List[str]:
        """
        Retorna IDs de slots da página especificada.
        
        Args:
            page_id: ID da página (usa ativa se None)
            
        Returns:
            Lista de IDs de slots
        """
        if page_id is None:
            page_id = self._active_page
        
        if page_id and page_id in self.pages:
            return self.pages[page_id].slots
        
        return []
    
    def _calculate_bounds(self, elem: etree._Element) -> Tuple[float, float, float, float]:
        """Calcula bounding box de um elemento."""
        # Tenta extrair de atributos de transformação
        x = float(elem.get('x', 0))
        y = float(elem.get('y', 0))
        width = float(elem.get('width', 0))
        height = float(elem.get('height', 0))
        
        # Se for um grupo, tenta encontrar dimensões dos filhos
        if elem.tag.endswith('}g') or elem.tag == 'g':
            for child in elem:
                child_tag = child.tag.split('}')[-1] if '}' in child.tag else child.tag
                if child_tag == 'rect':
                    width = max(width, float(child.get('width', 0)))
                    height = max(height, float(child.get('height', 0)))
        
        return (x, y, width, height)
    
    def _get_viewbox(self) -> Tuple[float, float, float, float]:
        """Retorna viewBox do documento."""
        viewbox = self.root.get('viewBox', '0 0 1000 1000')
        parts = [float(x) for x in viewbox.split()]
        if len(parts) >= 4:
            return tuple(parts[:4])
        return (0, 0, 1000, 1000)
    
    def _find_slots_in_page(self, page_elem: etree._Element) -> List[str]:
        """Encontra IDs de slots dentro de uma página."""
        slots = []
        
        for elem in page_elem.iter():
            elem_id = elem.get('id', '')
            if any(prefix in elem_id.upper() for prefix in ['SLOT_', 'TXT_', 'ALVO_', 'IMG_']):
                slots.append(elem_id)
        
        return slots
    
    def _find_all_slots(self) -> List[str]:
        """Encontra todos os slots no documento."""
        return self._find_slots_in_page(self.root)
    
    def hide_other_pages(self) -> None:
        """
        Oculta todas as páginas exceto a ativa.
        Útil para renderização de página única.
        """
        for page_id, page_info in self.pages.items():
            if page_id != self._active_page:
                # Define display: none
                style = page_info.element.get('style', '')
                if 'display:none' not in style:
                    page_info.element.set('style', style + ';display:none')
            else:
                # Garante que página ativa está visível
                style = page_info.element.get('style', '')
                style = style.replace('display:none', '').strip(';')
                page_info.element.set('style', style)
    
    def show_all_pages(self) -> None:
        """Mostra todas as páginas."""
        for page_info in self.pages.values():
            style = page_info.element.get('style', '')
            style = style.replace('display:none', '').strip(';')
            page_info.element.set('style', style)
    
    def extract_page_svg(self, page_id: Optional[str] = None) -> str:
        """
        Extrai SVG de uma única página.
        Passo 34 do Checklist - render_frame aceitar page_id.
        
        Args:
            page_id: ID da página (usa ativa se None)
            
        Returns:
            String SVG contendo apenas a página especificada
        """
        if page_id is None:
            page_id = self._active_page
        
        if not page_id or page_id not in self.pages:
            return ""
        
        # Clone o documento
        import copy
        cloned_root = copy.deepcopy(self.root)
        
        # Remove outras páginas
        for p_id, page_info in self.pages.items():
            if p_id != page_id:
                # Encontra elemento equivalente no clone
                for elem in cloned_root.xpath(f'//*[@id="{page_info.element.get("id")}"]'):
                    parent = elem.getparent()
                    if parent is not None:
                        parent.remove(elem)
        
        return etree.tostring(cloned_root, encoding='unicode', pretty_print=True)


def create_virtual_paper(svg_content: str) -> VirtualPaper:
    """
    Factory function para criar VirtualPaper a partir de string SVG.
    
    Args:
        svg_content: Conteúdo SVG
        
    Returns:
        Instância de VirtualPaper
    """
    if isinstance(svg_content, str):
        svg_content = svg_content.encode('utf-8')
    
    root = etree.fromstring(svg_content)
    tree = etree.ElementTree(root)
    
    return VirtualPaper(tree, root)

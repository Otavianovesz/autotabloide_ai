"""
AutoTabloide AI - Page Pagination for VectorEngine
=====================================================
Extensão do VectorEngine para suporte a paginação.
Passos 31-33 do Checklist v2.

Funcionalidades:
- get_page_count() - conta grupos #PAGE_xx
- render_page(index) - renderiza página específica
- set_active_page(page_id) - ativa página
"""

import re
from typing import Dict, List, Optional, Tuple
from lxml import etree

from src.core.logging_config import get_logger

logger = get_logger("PagePagination")

# Regex para detectar páginas
PAGE_PATTERN = re.compile(r'#?PAGE[_-]?(\d+)', re.IGNORECASE)


class PagePaginationMixin:
    """
    Mixin para adicionar paginação ao VectorEngine.
    Passos 31-33 do Checklist v2.
    
    Uso:
        class VectorEngine(PagePaginationMixin, ...):
            pass
    """
    
    def scan_pages(self) -> List[Dict]:
        """
        Escaneia template para identificar grupos de página.
        Passo 31 do Checklist v2.
        
        Returns:
            Lista de dicts com info de cada página:
            [{"page_id": "PAGE_01", "element_id": "...", "slot_count": 12}, ...]
        """
        if not hasattr(self, 'root') or self.root is None:
            return []
        
        pages = []
        
        # Busca grupos por ID ou Inkscape layer
        for elem in self.root.xpath('//*[@id]'):
            elem_id = elem.get('id', '')
            
            match = PAGE_PATTERN.match(elem_id)
            if match:
                page_num = int(match.group(1))
                
                # Conta slots dentro desta página
                slot_count = len(elem.xpath('.//*[starts-with(@id, "SLOT_")]'))
                
                pages.append({
                    "page_id": f"PAGE_{page_num:02d}",
                    "element_id": elem_id,
                    "page_number": page_num,
                    "slot_count": slot_count,
                    "element": elem
                })
        
        # Ordena por número de página
        pages.sort(key=lambda p: p["page_number"])
        
        logger.debug(f"Páginas encontradas: {len(pages)}")
        return pages
    
    def get_page_count(self) -> int:
        """
        Retorna número de páginas no template.
        Passo 32 do Checklist v2.
        
        Returns:
            Número de páginas (0 se não paginado)
        """
        return len(self.scan_pages())
    
    def get_page_slots(self, page_index: int) -> List[str]:
        """
        Retorna IDs de slots de uma página específica.
        
        Args:
            page_index: Índice da página (0-based)
            
        Returns:
            Lista de IDs de slots
        """
        pages = self.scan_pages()
        
        if page_index < 0 or page_index >= len(pages):
            return []
        
        page = pages[page_index]
        elem = page["element"]
        
        slots = []
        for slot_elem in elem.xpath('.//*[starts-with(@id, "SLOT_")]'):
            slots.append(slot_elem.get('id'))
        
        return slots
    
    def set_active_page(self, page_index: int) -> bool:
        """
        Define qual página está ativa (visível).
        Passo 33 do Checklist v2.
        
        Args:
            page_index: Índice da página (0-based)
            
        Returns:
            True se sucesso
        """
        pages = self.scan_pages()
        
        if not pages:
            # Template não paginado - nada a fazer
            return True
        
        for i, page in enumerate(pages):
            elem = page["element"]
            
            if i == page_index:
                # Mostra página ativa
                elem.set('style', 'display:inline')
                elem.set('visibility', 'visible')
            else:
                # Esconde outras páginas
                elem.set('style', 'display:none')
                elem.set('visibility', 'hidden')
        
        logger.debug(f"Página ativa: {page_index + 1}/{len(pages)}")
        return True
    
    def render_page(self, page_index: int) -> Optional[bytes]:
        """
        Renderiza uma página específica como SVG.
        Passo 34 do Checklist v2.
        
        Args:
            page_index: Índice da página (0-based)
            
        Returns:
            Bytes do SVG ou None se falhar
        """
        if not self.set_active_page(page_index):
            return None
        
        # Retorna SVG atual
        return self.export_svg()
    
    def export_svg(self) -> bytes:
        """
        Exporta SVG atual como bytes.
        
        Returns:
            Bytes do SVG
        """
        return etree.tostring(
            self.root,
            encoding='utf-8',
            xml_declaration=True,
            pretty_print=True
        )


def get_page_info_from_id(element_id: str) -> Optional[int]:
    """
    Extrai número de página de um ID de elemento.
    
    Args:
        element_id: ID do elemento SVG
        
    Returns:
        Número da página ou None
    """
    match = PAGE_PATTERN.match(element_id)
    if match:
        return int(match.group(1))
    return None


def is_paginated_template(root: etree._Element) -> bool:
    """
    Verifica se template usa paginação.
    
    Args:
        root: Elemento raiz do SVG
        
    Returns:
        True se tem grupos #PAGE_xx
    """
    for elem in root.xpath('//*[@id]'):
        elem_id = elem.get('id', '')
        if PAGE_PATTERN.match(elem_id):
            return True
    return False

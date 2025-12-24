"""
AutoTabloide AI - X-Ray Mode Renderer
======================================
Implementação conforme Vol. VI, Cap. 2.2.

Gera visualização de debug para layouts SVG, mostrando
zonas de imagem (verde) e texto (vermelho) para validação.
"""

import logging
from typing import Optional, Dict, Tuple
from pathlib import Path
from lxml import etree

logger = logging.getLogger("XRay")


# Cores para debug
XRAY_COLORS = {
    "image_zone": "#00FF00",   # Verde para #ALVO_IMAGEM
    "text_zone": "#FF0000",    # Vermelho para #TXT_*
    "price_zone": "#FF6600",   # Laranja para preços
    "slot_label": "#FFFF00",   # Amarelo para números de slot
}


class XRayRenderer:
    """
    Renderizador de visualização Raio-X para templates SVG.
    
    Substitui elementos visuais por formas coloridas semitransparentes
    que permitem identificar onde cada tipo de dado será injetado.
    
    Ref: Vol. VI, Cap. 2.2
    """
    
    def __init__(self, svg_path: str):
        """
        Args:
            svg_path: Caminho para o arquivo SVG original
        """
        self.svg_path = Path(svg_path)
        self.tree = None
        self.root = None
        self.namespaces = {
            'svg': 'http://www.w3.org/2000/svg',
            'xlink': 'http://www.w3.org/1999/xlink'
        }
    
    def load(self) -> bool:
        """Carrega o SVG para processamento."""
        try:
            self.tree = etree.parse(str(self.svg_path))
            self.root = self.tree.getroot()
            return True
        except Exception as e:
            logger.error(f"Erro ao carregar SVG: {e}")
            return False
    
    def get_viewbox(self) -> Tuple[float, float, float, float]:
        """Retorna viewBox do SVG."""
        viewbox = self.root.get('viewBox', '0 0 1000 1000')
        parts = viewbox.split()
        return tuple(float(p) for p in parts[:4])
    
    def generate_xray(self) -> Optional[str]:
        """
        Gera visualização X-Ray do template.
        
        Returns:
            String SVG com visualização de debug ou None se erro
        """
        if not self.root:
            if not self.load():
                return None
        
        # Criar cópia do SVG
        xray_root = etree.Element(self.root.tag, attrib=dict(self.root.attrib))
        
        # Copiar defs se existir
        for defs in self.root.findall('.//{http://www.w3.org/2000/svg}defs'):
            xray_root.append(etree.Element('defs'))
        
        # Fundo semitransparente
        viewbox = self.get_viewbox()
        bg = etree.SubElement(xray_root, 'rect')
        bg.set('x', str(viewbox[0]))
        bg.set('y', str(viewbox[1]))
        bg.set('width', str(viewbox[2]))
        bg.set('height', str(viewbox[3]))
        bg.set('fill', '#1a1a1a')
        bg.set('fill-opacity', '0.95')
        
        # Processar elementos
        slot_elements = self._find_slots()
        
        for slot_id, elements in slot_elements.items():
            # Extrair número do slot
            slot_num = slot_id.replace('SLOT_', '').replace('slot_', '')
            
            # Processar cada elemento do slot
            for elem_type, bbox in elements:
                if bbox:
                    self._add_zone(xray_root, bbox, elem_type, slot_num)
        
        # Serializar
        return etree.tostring(xray_root, encoding='unicode', pretty_print=True)
    
    def _find_slots(self) -> Dict:
        """Encontra todos os slots e seus elementos."""
        slots = {}
        
        # Buscar grupos de slot
        for elem in self.root.iter():
            elem_id = elem.get('id') or ''
            
            # Detectar slots
            if elem_id and elem_id.upper().startswith('SLOT_'):
                slot_id = elem_id.upper()
                if slot_id not in slots:
                    slots[slot_id] = []
                
                # Buscar filhos do slot
                for child in elem.iter():
                    child_id = child.get('id', '').upper()
                    bbox = self._get_bbox(child)
                    
                    if 'ALVO_IMAGEM' in child_id:
                        slots[slot_id].append(('image', bbox))
                    elif child_id.startswith('TXT_PRECO'):
                        slots[slot_id].append(('price', bbox))
                    elif child_id.startswith('TXT_'):
                        slots[slot_id].append(('text', bbox))
        
        # Se não encontrou grupos, buscar elementos soltos
        if not slots:
            slots['GLOBAL'] = []
            for elem in self.root.iter():
                elem_id = elem.get('id', '').upper()
                bbox = self._get_bbox(elem)
                
                if 'ALVO_IMAGEM' in elem_id:
                    slots['GLOBAL'].append(('image', bbox))
                elif 'TXT_PRECO' in elem_id:
                    slots['GLOBAL'].append(('price', bbox))
                elif 'TXT_' in elem_id:
                    slots['GLOBAL'].append(('text', bbox))
        
        return slots
    
    def _get_bbox(self, elem) -> Optional[Tuple[float, float, float, float]]:
        """Extrai bounding box de um elemento."""
        try:
            x = float(elem.get('x', 0))
            y = float(elem.get('y', 0))
            w = float(elem.get('width', 0))
            h = float(elem.get('height', 0))
            
            if w > 0 and h > 0:
                return (x, y, w, h)
            
            # Tentar de transform
            transform = elem.get('transform', '')
            if 'translate' in transform:
                # Extrair translate(x, y)
                import re
                match = re.search(r'translate\(([\d.]+)[,\s]+([\d.]+)\)', transform)
                if match:
                    x = float(match.group(1))
                    y = float(match.group(2))
                    return (x, y, 100, 30)  # Tamanho padrão para texto
            
            return None
            
        except (ValueError, TypeError):
            return None
    
    def _add_zone(self, root, bbox: Tuple, zone_type: str, slot_num: str):
        """Adiciona zona de debug ao SVG."""
        x, y, w, h = bbox
        
        # Escolher cor baseada no tipo
        if zone_type == 'image':
            color = XRAY_COLORS['image_zone']
        elif zone_type == 'price':
            color = XRAY_COLORS['price_zone']
        else:
            color = XRAY_COLORS['text_zone']
        
        # Retângulo da zona
        rect = etree.SubElement(root, 'rect')
        rect.set('x', str(x))
        rect.set('y', str(y))
        rect.set('width', str(w))
        rect.set('height', str(h))
        rect.set('fill', color)
        rect.set('fill-opacity', '0.4')
        rect.set('stroke', color)
        rect.set('stroke-width', '2')
        
        # Label do slot (apenas para imagem, que é maior)
        if zone_type == 'image' and slot_num != 'GLOBAL':
            label = etree.SubElement(root, 'text')
            label.set('x', str(x + w/2))
            label.set('y', str(y + h/2))
            label.set('fill', XRAY_COLORS['slot_label'])
            label.set('font-size', str(min(w, h) * 0.3))
            label.set('font-weight', 'bold')
            label.set('text-anchor', 'middle')
            label.set('dominant-baseline', 'middle')
            label.text = slot_num


def render_xray_preview(svg_path: str, output_path: Optional[str] = None) -> Optional[str]:
    """
    Função de conveniência para gerar preview X-Ray.
    
    Args:
        svg_path: Caminho do SVG original
        output_path: Caminho de saída (opcional)
    
    Returns:
        String SVG ou caminho do arquivo salvo
    """
    renderer = XRayRenderer(svg_path)
    xray_svg = renderer.generate_xray()
    
    if xray_svg and output_path:
        Path(output_path).write_text(xray_svg, encoding='utf-8')
        return output_path
    
    return xray_svg


def generate_xray_thumbnail(svg_path: str, thumb_path: str) -> bool:
    """
    Gera thumbnail X-Ray como PNG.
    
    Args:
        svg_path: Caminho do SVG original
        thumb_path: Caminho de saída do thumbnail
    
    Returns:
        True se sucesso
    """
    try:
        import cairosvg
        
        xray_svg = render_xray_preview(svg_path)
        if not xray_svg:
            return False
        
        cairosvg.svg2png(
            bytestring=xray_svg.encode('utf-8'),
            write_to=thumb_path,
            output_width=400,
            output_height=566
        )
        
        return True
        
    except ImportError:
        logger.warning("CairoSVG não disponível para gerar thumbnail")
        return False
    except Exception as e:
        logger.error(f"Erro ao gerar thumbnail X-Ray: {e}")
        return False

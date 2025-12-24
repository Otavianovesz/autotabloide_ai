"""
AutoTabloide AI - SVG Transforms
==================================
Transformações avançadas para SVG.
Passos 37-39 do Checklist 100.

Funcionalidades:
- Z-Index sorting (37)
- Kerning negativo (38)
- Conversão RGB→CMYK 100K (39)
"""

import re
from typing import List, Dict, Optional, Tuple
from lxml import etree

from src.core.logging_config import get_logger

logger = get_logger("SVGTransforms")


# ==============================================================================
# Z-INDEX SORTING (Passo 37)
# ==============================================================================

def sort_by_z_index(root: etree._Element) -> int:
    """
    Ordena elementos por z-index usando data-z-index.
    Passo 37 do Checklist.
    
    Elementos com maior z-index são movidos para o final
    (renderizados por último = aparecem na frente).
    
    Args:
        root: Elemento raiz do SVG
        
    Returns:
        Número de elementos reordenados
    """
    reordered = 0
    
    # Processa cada grupo que pode ter filhos ordenáveis
    for parent in root.iter():
        children = list(parent)
        if len(children) < 2:
            continue
        
        # Extrai z-index de cada filho
        z_indexed = []
        for i, child in enumerate(children):
            z_val = child.get('data-z-index')
            if z_val is not None:
                try:
                    z_indexed.append((int(z_val), i, child))
                except ValueError:
                    z_indexed.append((0, i, child))
            else:
                z_indexed.append((0, i, child))
        
        # Ordena por z-index (estável - mantém ordem original para iguais)
        z_indexed.sort(key=lambda x: (x[0], x[1]))
        
        # Verifica se ordem mudou
        new_order = [item[2] for item in z_indexed]
        if new_order != children:
            # Remove e re-adiciona na ordem correta
            for child in children:
                parent.remove(child)
            for child in new_order:
                parent.append(child)
            reordered += 1
    
    if reordered > 0:
        logger.debug(f"Z-index: {reordered} grupos reordenados")
    
    return reordered


# ==============================================================================
# KERNING NEGATIVO (Passo 38)
# ==============================================================================

def apply_negative_kerning(
    text_element: etree._Element,
    kerning_value: float = -1.0
) -> bool:
    """
    Aplica kerning negativo a um elemento de texto.
    Passo 38 do Checklist - Kerning -1px antes de reduzir fonte.
    
    Args:
        text_element: Elemento <text> ou <tspan>
        kerning_value: Valor de kerning em px (negativo = mais apertado)
        
    Returns:
        True se aplicado
    """
    if text_element.tag not in ('text', 'tspan', 
                                  '{http://www.w3.org/2000/svg}text',
                                  '{http://www.w3.org/2000/svg}tspan'):
        return False
    
    # Aplica via atributo letter-spacing no style
    current_style = text_element.get('style', '')
    
    # Remove letter-spacing existente
    current_style = re.sub(r'letter-spacing:\s*[^;]+;?', '', current_style)
    
    # Adiciona novo kerning
    if current_style and not current_style.endswith(';'):
        current_style += ';'
    current_style += f'letter-spacing:{kerning_value}px'
    
    text_element.set('style', current_style)
    
    logger.debug(f"Kerning {kerning_value}px aplicado a elemento")
    return True


def apply_kerning_to_all_text(
    root: etree._Element,
    kerning_value: float = -1.0
) -> int:
    """
    Aplica kerning a todos os elementos de texto.
    
    Args:
        root: Raiz do SVG
        kerning_value: Valor de kerning
        
    Returns:
        Número de elementos modificados
    """
    count = 0
    
    for elem in root.iter():
        tag = elem.tag.split('}')[-1] if '}' in elem.tag else elem.tag
        if tag in ('text', 'tspan'):
            if apply_negative_kerning(elem, kerning_value):
                count += 1
    
    return count


# ==============================================================================
# RGB → CMYK 100K (Passo 39)
# ==============================================================================

# Padrões de preto RGB
BLACK_RGB_PATTERNS = [
    re.compile(r'#000000', re.IGNORECASE),
    re.compile(r'rgb\s*\(\s*0\s*,\s*0\s*,\s*0\s*\)', re.IGNORECASE),
    re.compile(r'black', re.IGNORECASE),
]

# Valor de substituição (preto puro registrado)
# Nota: SVG padrão não suporta CMYK diretamente, mas podemos
# marcar com atributo customizado para pós-processamento
CMYK_100K_MARKER = "device-cmyk(0, 0, 0, 1)"


def convert_blacks_to_cmyk(root: etree._Element) -> int:
    """
    Converte pretos RGB para marcador CMYK 100K.
    Passo 39 do Checklist.
    
    Adiciona atributo data-cmyk="100K" para pós-processamento
    em ferramentas que suportam CMYK (Ghostscript, Illustrator).
    
    Args:
        root: Raiz do SVG
        
    Returns:
        Número de elementos marcados
    """
    marked = 0
    
    for elem in root.iter():
        modified = False
        
        # Verifica fill
        fill = elem.get('fill', '')
        if _is_black(fill):
            elem.set('data-cmyk-fill', '0,0,0,100')
            modified = True
        
        # Verifica stroke
        stroke = elem.get('stroke', '')
        if _is_black(stroke):
            elem.set('data-cmyk-stroke', '0,0,0,100')
            modified = True
        
        # Verifica style
        style = elem.get('style', '')
        if style:
            # Procura por fill: ou stroke: com preto
            if re.search(r'fill\s*:\s*(#000000|black|rgb\s*\(0,\s*0,\s*0\))', style, re.I):
                elem.set('data-cmyk-fill', '0,0,0,100')
                modified = True
            if re.search(r'stroke\s*:\s*(#000000|black|rgb\s*\(0,\s*0,\s*0\))', style, re.I):
                elem.set('data-cmyk-stroke', '0,0,0,100')
                modified = True
        
        if modified:
            marked += 1
    
    if marked > 0:
        logger.info(f"CMYK: {marked} elementos marcados para preto 100K")
    
    return marked


def _is_black(color_value: str) -> bool:
    """Verifica se um valor de cor é preto RGB."""
    if not color_value:
        return False
    
    color_value = color_value.strip().lower()
    
    if color_value in ('black', '#000', '#000000'):
        return True
    
    if color_value.startswith('rgb'):
        match = re.match(r'rgb\s*\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*\)', color_value)
        if match:
            r, g, b = int(match.group(1)), int(match.group(2)), int(match.group(3))
            return r == 0 and g == 0 and b == 0
    
    return False


# ==============================================================================
# HELPER PARA APLICAR TODAS AS TRANSFORMAÇÕES
# ==============================================================================

def apply_all_transforms(root: etree._Element, options: Dict = None) -> Dict:
    """
    Aplica todas as transformações de uma vez.
    
    Args:
        root: Raiz do SVG
        options: Opções de configuração
        
    Returns:
        Dict com estatísticas
    """
    options = options or {}
    stats = {}
    
    # Z-Index
    if options.get('z_index', True):
        stats['z_index_groups'] = sort_by_z_index(root)
    
    # Kerning (opcional, só se explicitamente pedido)
    if options.get('kerning'):
        kerning_val = options.get('kerning_value', -1.0)
        stats['kerning_applied'] = apply_kerning_to_all_text(root, kerning_val)
    
    # CMYK
    if options.get('cmyk_blacks', True):
        stats['cmyk_marked'] = convert_blacks_to_cmyk(root)
    
    return stats

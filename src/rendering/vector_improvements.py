"""
AutoTabloide AI - Vector Engine Improvements
===============================================
Melhorias para o Motor Vetorial.
Passos 35-40 do Checklist v2.

Funcionalidades:
- Fallback de fontes configurável (35)
- Perfil CMYK (35)
- Conversão texto em curvas (36)
- Sangria/bleed (37)
- Marcas de corte (38)
- EAN-13 com validação (39)
- Cache LRU de fontes (40)
"""

from collections import OrderedDict
from typing import Optional, List, Tuple
from pathlib import Path
from lxml import etree
import re

from src.core.logging_config import get_logger
from src.core.constants import SYSTEM_ROOT

logger = get_logger("VectorImprovements")


# Fontes de fallback configuráveis (passo 35)
FALLBACK_FONTS = [
    "Roboto-Regular.ttf",
    "DejaVuSans.ttf",
    "Arial.ttf",
    "LiberationSans-Regular.ttf",
    "NotoSans-Regular.ttf",
]

# Perfil CMYK padrão
CMYK_PROFILE_PATH = SYSTEM_ROOT / "assets" / "profiles" / "CoatedFOGRA39.icc"


class LRUFontCache:
    """
    Cache LRU para fontes.
    Passo 40 do Checklist v2 - Limite de cache de fontes.
    """
    
    def __init__(self, max_size: int = 50):
        """
        Args:
            max_size: Máximo de fontes em cache
        """
        self.max_size = max_size
        self._cache: OrderedDict = OrderedDict()
    
    def get(self, key: Tuple) -> Optional[any]:
        """Obtém item do cache (move para final)."""
        if key in self._cache:
            self._cache.move_to_end(key)
            return self._cache[key]
        return None
    
    def put(self, key: Tuple, value: any) -> None:
        """Adiciona item ao cache."""
        if key in self._cache:
            self._cache.move_to_end(key)
        else:
            if len(self._cache) >= self.max_size:
                # Remove mais antigo
                oldest = next(iter(self._cache))
                del self._cache[oldest]
                logger.debug(f"Cache de fonte evicted: {oldest[0]}")
            
            self._cache[key] = value
    
    def clear(self) -> None:
        """Limpa cache."""
        self._cache.clear()
    
    def __len__(self) -> int:
        return len(self._cache)


def get_fallback_fonts() -> List[str]:
    """
    Retorna lista de fontes de fallback.
    Passo 35 - Configurável via constants ou settings.
    """
    try:
        from src.core.settings_service import get_settings
        settings = get_settings()
        custom = settings.get("fonts.fallback_list")
        if custom:
            return custom
    except:
        pass
    
    return FALLBACK_FONTS


def add_bleed(root: etree._Element, bleed_mm: float = 3.0) -> etree._Element:
    """
    Adiciona sangria (bleed) ao SVG.
    Passo 37 do Checklist v2.
    
    Args:
        root: Elemento raiz do SVG
        bleed_mm: Sangria em milímetros
        
    Returns:
        Elemento raiz modificado
    """
    viewbox = root.get('viewBox', '0 0 1000 1000')
    parts = [float(x) for x in viewbox.split()]
    
    if len(parts) >= 4:
        # Converte mm para unidades do viewbox (assumindo 1mm = 3.78px a 96dpi)
        bleed_px = bleed_mm * 3.78
        
        # Expande viewbox
        new_viewbox = f"{parts[0] - bleed_px} {parts[1] - bleed_px} {parts[2] + 2*bleed_px} {parts[3] + 2*bleed_px}"
        root.set('viewBox', new_viewbox)
        
        # Atualiza width/height se definidos
        if root.get('width'):
            try:
                width = float(root.get('width').replace('mm', '').replace('px', ''))
                root.set('width', f"{width + 2*bleed_mm}mm")
            except:
                pass
        
        if root.get('height'):
            try:
                height = float(root.get('height').replace('mm', '').replace('px', ''))
                root.set('height', f"{height + 2*bleed_mm}mm")
            except:
                pass
        
        logger.debug(f"Sangria adicionada: {bleed_mm}mm")
    
    return root


def add_crop_marks(root: etree._Element, offset_mm: float = 3.0, length_mm: float = 5.0) -> etree._Element:
    """
    Adiciona marcas de corte ao SVG.
    Passo 38 do Checklist v2.
    
    Args:
        root: Elemento raiz do SVG
        offset_mm: Distância das marcas da borda
        length_mm: Comprimento das marcas
        
    Returns:
        Elemento raiz modificado
    """
    viewbox = root.get('viewBox', '0 0 1000 1000')
    parts = [float(x) for x in viewbox.split()]
    
    if len(parts) < 4:
        return root
    
    x, y, w, h = parts
    
    # Converte mm para unidades
    offset = offset_mm * 3.78
    length = length_mm * 3.78
    stroke_width = 0.5
    
    # Cria grupo para marcas de corte
    ns = "{http://www.w3.org/2000/svg}"
    crop_group = etree.SubElement(root, f"{ns}g")
    crop_group.set('id', 'crop_marks')
    crop_group.set('stroke', '#000000')
    crop_group.set('stroke-width', str(stroke_width))
    crop_group.set('fill', 'none')
    
    # Posições das marcas
    positions = [
        # Canto superior esquerdo
        (x - offset, y, x - offset - length, y),  # horizontal
        (x, y - offset, x, y - offset - length),  # vertical
        # Canto superior direito
        (x + w + offset, y, x + w + offset + length, y),
        (x + w, y - offset, x + w, y - offset - length),
        # Canto inferior esquerdo
        (x - offset, y + h, x - offset - length, y + h),
        (x, y + h + offset, x, y + h + offset + length),
        # Canto inferior direito
        (x + w + offset, y + h, x + w + offset + length, y + h),
        (x + w, y + h + offset, x + w, y + h + offset + length),
    ]
    
    for x1, y1, x2, y2 in positions:
        line = etree.SubElement(crop_group, f"{ns}line")
        line.set('x1', str(x1))
        line.set('y1', str(y1))
        line.set('x2', str(x2))
        line.set('y2', str(y2))
    
    logger.debug("Marcas de corte adicionadas")
    return root


def validate_ean13_checksum(ean: str) -> Tuple[bool, str]:
    """
    Valida dígito verificador EAN-13.
    Passo 39 do Checklist v2.
    
    Args:
        ean: Código EAN-13
        
    Returns:
        Tupla (é_válido, ean_corrigido_ou_erro)
    """
    # Remove espaços e hífens
    ean = re.sub(r'[\s\-]', '', ean)
    
    if not ean.isdigit():
        return False, "EAN deve conter apenas dígitos"
    
    if len(ean) == 12:
        # Calcula dígito verificador
        total = 0
        for i, digit in enumerate(ean):
            weight = 1 if i % 2 == 0 else 3
            total += int(digit) * weight
        
        check_digit = (10 - (total % 10)) % 10
        return True, ean + str(check_digit)
    
    elif len(ean) == 13:
        # Valida dígito verificador
        total = 0
        for i, digit in enumerate(ean[:-1]):
            weight = 1 if i % 2 == 0 else 3
            total += int(digit) * weight
        
        expected = (10 - (total % 10)) % 10
        actual = int(ean[-1])
        
        if expected == actual:
            return True, ean
        else:
            return False, f"Dígito verificador inválido: esperado {expected}, recebido {actual}"
    
    else:
        return False, f"EAN deve ter 12 ou 13 dígitos, recebido {len(ean)}"


def get_gs_cmyk_args() -> List[str]:
    """
    Retorna argumentos do Ghostscript para conversão CMYK.
    Passo 35 do Checklist v2.
    
    Returns:
        Lista de argumentos
    """
    args = [
        "-dNOPAUSE",
        "-dBATCH",
        "-sDEVICE=pdfwrite",
        "-dPDFSETTINGS=/prepress",
        "-sColorConversionStrategy=CMYK",
        "-dProcessColorModel=/DeviceCMYK",
    ]
    
    # Adiciona perfil ICC se existir
    if CMYK_PROFILE_PATH.exists():
        args.append(f"-sOutputICCProfile={CMYK_PROFILE_PATH}")
    
    return args


def get_gs_outline_args() -> List[str]:
    """
    Retorna argumentos do Ghostscript para converter texto em curvas.
    Passo 36 do Checklist v2.
    
    Returns:
        Lista de argumentos
    """
    return [
        "-dNOPAUSE",
        "-dBATCH",
        "-sDEVICE=pdfwrite",
        "-dNoOutputFonts",  # Converte fontes em curvas
        "-dSubsetFonts=false",
    ]


class VectorImprovementsMixin:
    """
    Mixin com melhorias para VectorEngine.
    
    CENTURY CHECKLIST:
    - Items 35-40: Fallback fontes, CMYK, curvas, bleed, crop marks, EAN
    - Item 46: Overprint de preto
    - Item 56: Limpeza de SVG
    - Item 57: Ordenação Z-Index
    """
    
    def apply_bleed(self, bleed_mm: float = 3.0) -> None:
        """Aplica sangria ao template atual."""
        if self.root is not None:
            add_bleed(self.root, bleed_mm)
    
    def apply_crop_marks(self) -> None:
        """Adiciona marcas de corte."""
        if self.root is not None:
            add_crop_marks(self.root)
    
    def validate_barcode(self, ean: str) -> Tuple[bool, str]:
        """Valida código de barras."""
        return validate_ean13_checksum(ean)
    
    def apply_black_overprint(self) -> None:
        """
        CENTURY CHECKLIST Item 46: Aplica overprint em textos pretos.
        Evita contorno branco em pretos se registro da impressora falhar.
        """
        if self.root is None:
            return
        
        ns = {'svg': 'http://www.w3.org/2000/svg'}
        
        # Procura todos os elementos text
        for elem in self.root.iter():
            fill = elem.get('fill', '')
            style = elem.get('style', '')
            
            # Detecta preto puro
            is_black = (
                fill.lower() in ['#000000', '#000', 'black', 'rgb(0,0,0)'] or
                'fill:#000000' in style.lower() or
                'fill:#000' in style.lower() or
                'fill:black' in style.lower()
            )
            
            if is_black:
                # Adiciona atributo de overprint (para PDF)
                elem.set('fill-overprint', 'true')
                elem.set('style', style + ';mix-blend-mode:multiply;' if style else 'mix-blend-mode:multiply;')
        
        logger.debug("Overprint de preto aplicado")
    
    def cleanup_svg_metadata(self) -> None:
        """
        CENTURY CHECKLIST Item 56: Remove metadados proprietários do SVG.
        Limpa atributos Inkscape, Illustrator, etc.
        """
        if self.root is None:
            return
        
        # Namespaces a remover
        remove_prefixes = ['inkscape', 'sodipodi', 'adobe', 'illustrator']
        
        for elem in self.root.iter():
            # Remove atributos com prefixos proprietários
            attrs_to_remove = []
            for attr in elem.attrib:
                for prefix in remove_prefixes:
                    if prefix in attr.lower():
                        attrs_to_remove.append(attr)
                        break
            
            for attr in attrs_to_remove:
                del elem.attrib[attr]
        
        logger.debug("Metadados proprietários removidos do SVG")
    
    def ensure_price_z_order(self) -> None:
        """
        CENTURY CHECKLIST Item 57: Garante que preço fique acima da imagem.
        Move elementos de preço para o final do parent (maior z-index).
        """
        if self.root is None:
            return
        
        # Procura elementos com ID contendo "price" ou "preco"
        for elem in self.root.iter():
            elem_id = elem.get('id', '').lower()
            if any(x in elem_id for x in ['price', 'preco', 'preço', 'valor']):
                parent = elem.getparent()
                if parent is not None:
                    # Remove e re-adiciona no final (maior z-index)
                    parent.remove(elem)
                    parent.append(elem)
        
        logger.debug("Z-order de preços ajustado")
    
    def extend_bleed_elements(self, bleed_mm: float = 3.0) -> None:
        """
        INDUSTRIAL ROBUSTNESS #52: Extrapola elementos de borda para sangria.
        
        Diferente de add_bleed() que só expande o viewbox, este método
        estende fisicamente os elementos que tocam as bordas do documento
        para garantir que não haja borda branca no corte.
        
        Procura por:
        - Retângulos com x=0 ou y=0 ou x+width=viewbox_width
        - Backgrounds que cobrem toda a página
        - Imagens de borda
        """
        if self.root is None:
            return
        
        # Obtém dimensões do viewbox
        viewbox = self.root.get('viewBox', '0 0 1000 1000')
        parts = [float(x) for x in viewbox.split()]
        if len(parts) < 4:
            return
        
        vb_x, vb_y, vb_w, vb_h = parts
        bleed_px = bleed_mm * 3.78  # Conversão mm para px
        
        # Procura elementos de borda
        ns = '{http://www.w3.org/2000/svg}'
        
        for elem in self.root.iter():
            tag = elem.tag.replace(ns, '')
            
            if tag in ['rect', 'image']:
                try:
                    x = float(elem.get('x', '0'))
                    y = float(elem.get('y', '0'))
                    w = float(elem.get('width', '0'))
                    h = float(elem.get('height', '0'))
                    
                    extended = False
                    
                    # Borda esquerda
                    if abs(x - vb_x) < 1:
                        elem.set('x', str(x - bleed_px))
                        elem.set('width', str(w + bleed_px))
                        extended = True
                    
                    # Borda superior
                    if abs(y - vb_y) < 1:
                        elem.set('y', str(y - bleed_px))
                        elem.set('height', str(h + bleed_px))
                        extended = True
                    
                    # Borda direita
                    if abs((x + w) - (vb_x + vb_w)) < 1:
                        elem.set('width', str(w + bleed_px))
                        extended = True
                    
                    # Borda inferior
                    if abs((y + h) - (vb_y + vb_h)) < 1:
                        elem.set('height', str(h + bleed_px))
                        extended = True
                    
                    if extended:
                        logger.debug(f"Elemento {elem.get('id', tag)} estendido para sangria")
                        
                except (ValueError, TypeError):
                    continue
        
        logger.debug(f"Sangria real de {bleed_mm}mm aplicada aos elementos de borda")


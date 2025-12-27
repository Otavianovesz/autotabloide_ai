"""
AutoTabloide AI - SVG Rendering Engine
========================================
Motor de renderização de SVG para produção de tabloides.
Integra lxml para parsing e manipulação vetorial.
"""

from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple
import re
import io
import xml.etree.ElementTree as ET


class SVGElement:
    """Representa um elemento SVG manipulável."""
    
    def __init__(self, element: ET.Element, element_id: str = ""):
        self.element = element
        self.element_id = element_id or element.get("id", "")
        self.tag = element.tag.split("}")[-1]  # Remove namespace
    
    def get_attribute(self, name: str, default: str = "") -> str:
        return self.element.get(name, default)
    
    def set_attribute(self, name: str, value: str) -> None:
        self.element.set(name, value)
    
    def get_text(self) -> str:
        return self.element.text or ""
    
    def set_text(self, text: str) -> None:
        self.element.text = text
    
    def get_style(self) -> Dict[str, str]:
        """Parse style attribute into dict."""
        style_str = self.element.get("style", "")
        if not style_str:
            return {}
        
        result = {}
        for item in style_str.split(";"):
            if ":" in item:
                key, value = item.split(":", 1)
                result[key.strip()] = value.strip()
        return result
    
    def set_style(self, styles: Dict[str, str]) -> None:
        """Set style from dict."""
        style_str = "; ".join(f"{k}: {v}" for k, v in styles.items())
        self.element.set("style", style_str)
    
    def update_style(self, key: str, value: str) -> None:
        """Update single style property."""
        styles = self.get_style()
        styles[key] = value
        self.set_style(styles)


class SVGSlot:
    """Representa um slot de produto no SVG."""
    
    def __init__(self, slot_id: int, group_element: ET.Element):
        self.slot_id = slot_id
        self.group = group_element
        
        # Sub-elementos
        self.image_target: Optional[ET.Element] = None
        self.name_text: Optional[ET.Element] = None
        self.price_int_text: Optional[ET.Element] = None
        self.price_dec_text: Optional[ET.Element] = None
        self.unit_text: Optional[ET.Element] = None
        
        self._find_sub_elements()
    
    def _find_sub_elements(self) -> None:
        """Identifica sub-elementos do slot."""
        for elem in self.group.iter():
            elem_id = (elem.get("id") or "").upper()
            
            if "ALVO_IMAGEM" in elem_id or "IMG" in elem_id:
                self.image_target = elem
            elif "NOME" in elem_id:
                self.name_text = elem
            elif "PRECO_INT" in elem_id:
                self.price_int_text = elem
            elif "PRECO_DEC" in elem_id:
                self.price_dec_text = elem
            elif "UNIDADE" in elem_id or "PESO" in elem_id:
                self.unit_text = elem
    
    def inject_product(self, product: Dict[str, Any]) -> None:
        """Injeta dados do produto no slot."""
        name = product.get("nome_sanitizado", "")
        price = product.get("preco_venda_atual", 0)
        unit = product.get("unidade", "")
        img_hash = product.get("img_hash_ref", "")
        
        # Nome
        if self.name_text is not None:
            self._set_text_content(self.name_text, name)
        
        # Preço - separar inteiro e decimal
        price_int = int(price)
        price_dec = int((price - price_int) * 100)
        
        if self.price_int_text is not None:
            self._set_text_content(self.price_int_text, str(price_int))
        
        if self.price_dec_text is not None:
            self._set_text_content(self.price_dec_text, f",{price_dec:02d}")
        
        # Unidade
        if self.unit_text is not None and unit:
            self._set_text_content(self.unit_text, unit)
        
        # Imagem - requer processamento adicional
        # TODO: Injetar xlink:href com caminho da imagem
    
    def _set_text_content(self, element: ET.Element, text: str) -> None:
        """Define texto em elemento, considerando tspan."""
        # Busca tspan filho
        tspan = element.find(".//{http://www.w3.org/2000/svg}tspan")
        if tspan is not None:
            tspan.text = text
        else:
            element.text = text


class SVGEngine:
    """
    Motor principal de manipulação SVG.
    
    Funcionalidades:
    - Carregar template SVG
    - Identificar slots de produtos
    - Injetar dados nos slots
    - Aplicar text-fitting
    - Gerar SVG final ou rasterizar
    """
    
    SVG_NS = "http://www.w3.org/2000/svg"
    XLINK_NS = "http://www.w3.org/1999/xlink"
    
    def __init__(self):
        self.tree: Optional[ET.ElementTree] = None
        self.root: Optional[ET.Element] = None
        self.slots: Dict[int, SVGSlot] = {}
        self.viewbox: Tuple[float, float, float, float] = (0, 0, 800, 1100)
        self.source_path: Optional[Path] = None
        
        # Registra namespaces
        ET.register_namespace("", self.SVG_NS)
        ET.register_namespace("xlink", self.XLINK_NS)
    
    def load(self, svg_path: str) -> bool:
        """
        Carrega template SVG.
        
        Args:
            svg_path: Caminho do arquivo SVG
            
        Returns:
            True se carregou com sucesso
        """
        try:
            self.source_path = Path(svg_path)
            self.tree = ET.parse(svg_path)
            self.root = self.tree.getroot()
            
            # Parse viewBox
            viewbox_str = self.root.get("viewBox", "0 0 800 1100")
            parts = viewbox_str.split()
            if len(parts) == 4:
                self.viewbox = tuple(map(float, parts))
            
            # Encontra slots
            self._find_slots()
            
            print(f"[SVGEngine] Carregado: {svg_path} ({len(self.slots)} slots)")
            return True
            
        except Exception as e:
            print(f"[SVGEngine] Erro ao carregar: {e}")
            return False
    
    def _find_slots(self) -> None:
        """Identifica slots no documento."""
        self.slots.clear()
        
        for elem in self.root.iter():
            elem_id = elem.get("id", "")
            
            # Busca por SLOT_XX
            match = re.match(r"SLOT_(\d+)", elem_id, re.IGNORECASE)
            if match:
                slot_num = int(match.group(1))
                self.slots[slot_num] = SVGSlot(slot_num, elem)
    
    def get_slot_count(self) -> int:
        """Retorna quantidade de slots."""
        return len(self.slots)
    
    def get_viewbox_size(self) -> Tuple[float, float]:
        """Retorna tamanho do viewbox (width, height)."""
        return (self.viewbox[2], self.viewbox[3])
    
    def inject_products(self, products_by_slot: Dict[int, Dict]) -> None:
        """
        Injeta produtos em múltiplos slots.
        
        Args:
            products_by_slot: Dict {slot_id: product_dict}
        """
        for slot_id, product in products_by_slot.items():
            if slot_id in self.slots:
                self.slots[slot_id].inject_product(product)
    
    def inject_product(self, slot_id: int, product: Dict) -> bool:
        """
        Injeta produto em slot específico.
        
        Args:
            slot_id: Índice do slot
            product: Dados do produto
            
        Returns:
            True se injetou com sucesso
        """
        if slot_id in self.slots:
            self.slots[slot_id].inject_product(product)
            return True
        return False
    
    def to_string(self) -> str:
        """Retorna SVG como string."""
        if self.tree is None:
            return ""
        
        return ET.tostring(self.root, encoding="unicode")
    
    def save(self, output_path: str) -> bool:
        """
        Salva SVG modificado.
        
        Args:
            output_path: Caminho de saída
            
        Returns:
            True se salvou com sucesso
        """
        try:
            self.tree.write(output_path, encoding="utf-8", xml_declaration=True)
            return True
        except Exception as e:
            print(f"[SVGEngine] Erro ao salvar: {e}")
            return False
    
    def render_to_png(self, output_path: str, dpi: int = 300) -> bool:
        """
        Renderiza SVG para PNG.
        
        Requer cairosvg instalado.
        
        Args:
            output_path: Caminho de saída
            dpi: Resolução em DPI
            
        Returns:
            True se renderizou com sucesso
        """
        try:
            import cairosvg
            
            svg_string = self.to_string()
            cairosvg.svg2png(
                bytestring=svg_string.encode('utf-8'),
                write_to=output_path,
                dpi=dpi
            )
            return True
        except ImportError:
            print("[SVGEngine] cairosvg nao instalado")
            return False
        except Exception as e:
            print(f"[SVGEngine] Erro na renderizacao: {e}")
            return False
    
    def render_to_pdf(self, output_path: str) -> bool:
        """
        Renderiza SVG para PDF.
        
        Requer cairosvg instalado.
        
        Args:
            output_path: Caminho de saída
            
        Returns:
            True se renderizou com sucesso
        """
        try:
            import cairosvg
            
            svg_string = self.to_string()
            cairosvg.svg2pdf(
                bytestring=svg_string.encode('utf-8'),
                write_to=output_path
            )
            return True
        except ImportError:
            print("[SVGEngine] cairosvg nao instalado")
            return False
        except Exception as e:
            print(f"[SVGEngine] Erro na renderizacao PDF: {e}")
            return False


class TextFitter:
    """
    Algoritmo de text-fitting para SVG.
    Ajusta tamanho de fonte para caber em área definida.
    """
    
    def __init__(self, max_iterations: int = 10):
        self.max_iterations = max_iterations
    
    def fit_text(
        self, 
        text: str, 
        max_width: float, 
        max_height: float,
        font_size_range: Tuple[float, float] = (8, 48)
    ) -> float:
        """
        Calcula tamanho de fonte ideal.
        
        Algoritmo simplificado baseado em proporção.
        Para precisão real, usar medição com biblioteca gráfica.
        
        Args:
            text: Texto a ajustar
            max_width: Largura máxima
            max_height: Altura máxima
            font_size_range: (min_size, max_size)
            
        Returns:
            Tamanho de fonte calculado
        """
        min_size, max_size = font_size_range
        
        # Estimativa: ~0.6 caracteres por unidade de fonte
        char_width_ratio = 0.6
        
        # Calcula tamanho baseado em largura
        text_len = len(text)
        if text_len == 0:
            return max_size
        
        estimated_width_per_char = max_width / text_len
        width_based_size = estimated_width_per_char / char_width_ratio
        
        # Limita ao range
        result = max(min_size, min(max_size, width_based_size))
        
        # Verifica altura
        if result > max_height * 0.8:
            result = max_height * 0.8
        
        return result

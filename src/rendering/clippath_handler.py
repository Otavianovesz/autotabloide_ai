"""
AutoTabloide AI - ClipPath Handler
====================================
Gerenciamento de ClipPaths complexos em SVG.
PROTOCOLO DE RETIFICAÇÃO: Passo 46 (ClipPaths complexos).

Corrige e otimiza clip-paths em SVGs de layout.
"""

import logging
import re
from typing import Optional, List, Dict, Any, Tuple
from lxml import etree

logger = logging.getLogger("ClipPath")


class ClipPathHandler:
    """
    Gerenciador de ClipPaths SVG.
    
    PASSO 46: Suporta clip-paths complexos sem quebrar.
    """
    
    SVG_NS = "http://www.w3.org/2000/svg"
    NSMAP = {"svg": SVG_NS}
    
    def __init__(self):
        self._clip_id_counter = 0
    
    def _generate_clip_id(self) -> str:
        """Gera ID único para clip-path."""
        self._clip_id_counter += 1
        return f"autotabloide_clip_{self._clip_id_counter}"
    
    def find_clipaths(self, svg_root: etree.Element) -> List[etree.Element]:
        """Encontra todos os clipPaths no SVG."""
        return svg_root.findall(".//{%s}clipPath" % self.SVG_NS)
    
    def find_elements_with_clip(self, svg_root: etree.Element) -> List[etree.Element]:
        """Encontra elementos que usam clip-path."""
        elements = []
        
        for elem in svg_root.iter():
            clip_attr = elem.get("clip-path")
            style = elem.get("style", "")
            
            if clip_attr or "clip-path" in style:
                elements.append(elem)
        
        return elements
    
    def fix_broken_clips(self, svg_root: etree.Element) -> int:
        """
        Corrige referências quebradas de clip-path.
        
        Returns:
            Número de clips corrigidos
        """
        fixed = 0
        
        # Coletar IDs de clips existentes
        existing_clips = set()
        for clip in self.find_clipaths(svg_root):
            clip_id = clip.get("id")
            if clip_id:
                existing_clips.add(clip_id)
        
        # Verificar referências
        for elem in self.find_elements_with_clip(svg_root):
            clip_ref = elem.get("clip-path")
            
            if clip_ref:
                # Extrair ID da referência
                match = re.match(r'url\(#([^)]+)\)', clip_ref)
                if match:
                    ref_id = match.group(1)
                    
                    if ref_id not in existing_clips:
                        # Referência quebrada - remover
                        elem.attrib.pop("clip-path", None)
                        fixed += 1
                        logger.debug(f"Removida referência quebrada: {ref_id}")
        
        if fixed > 0:
            logger.info(f"Corrigidos {fixed} clip-paths quebrados")
        
        return fixed
    
    def create_rect_clip(
        self,
        svg_root: etree.Element,
        x: float,
        y: float,
        width: float,
        height: float,
        rx: float = 0,
        ry: float = 0
    ) -> str:
        """
        Cria clip-path retangular.
        
        Args:
            x, y: Posição
            width, height: Dimensões
            rx, ry: Raios de borda
            
        Returns:
            ID do clip criado
        """
        clip_id = self._generate_clip_id()
        
        # Encontrar ou criar defs
        defs = svg_root.find(".//{%s}defs" % self.SVG_NS)
        if defs is None:
            defs = etree.SubElement(svg_root, "{%s}defs" % self.SVG_NS)
        
        # Criar clipPath
        clip_path = etree.SubElement(defs, "{%s}clipPath" % self.SVG_NS)
        clip_path.set("id", clip_id)
        
        # Adicionar rect
        rect = etree.SubElement(clip_path, "{%s}rect" % self.SVG_NS)
        rect.set("x", str(x))
        rect.set("y", str(y))
        rect.set("width", str(width))
        rect.set("height", str(height))
        
        if rx > 0:
            rect.set("rx", str(rx))
        if ry > 0:
            rect.set("ry", str(ry))
        
        return clip_id
    
    def create_circle_clip(
        self,
        svg_root: etree.Element,
        cx: float,
        cy: float,
        r: float
    ) -> str:
        """
        Cria clip-path circular.
        
        Returns:
            ID do clip criado
        """
        clip_id = self._generate_clip_id()
        
        defs = svg_root.find(".//{%s}defs" % self.SVG_NS)
        if defs is None:
            defs = etree.SubElement(svg_root, "{%s}defs" % self.SVG_NS)
        
        clip_path = etree.SubElement(defs, "{%s}clipPath" % self.SVG_NS)
        clip_path.set("id", clip_id)
        
        circle = etree.SubElement(clip_path, "{%s}circle" % self.SVG_NS)
        circle.set("cx", str(cx))
        circle.set("cy", str(cy))
        circle.set("r", str(r))
        
        return clip_id
    
    def apply_clip(
        self,
        element: etree.Element,
        clip_id: str
    ) -> None:
        """Aplica clip-path a um elemento."""
        element.set("clip-path", f"url(#{clip_id})")
    
    def simplify_complex_clips(
        self,
        svg_root: etree.Element,
        max_path_length: int = 1000
    ) -> int:
        """
        Simplifica clip-paths muito complexos.
        
        Converte paths complexos em bbox simples.
        
        Returns:
            Número de clips simplificados
        """
        simplified = 0
        
        for clip_path in self.find_clipaths(svg_root):
            for path in clip_path.findall(".//{%s}path" % self.SVG_NS):
                d = path.get("d", "")
                
                if len(d) > max_path_length:
                    # Path muito complexo - calcular bbox e substituir
                    bbox = self._estimate_path_bbox(d)
                    
                    if bbox:
                        # Substituir path por rect
                        rect = etree.Element("{%s}rect" % self.SVG_NS)
                        rect.set("x", str(bbox[0]))
                        rect.set("y", str(bbox[1]))
                        rect.set("width", str(bbox[2]))
                        rect.set("height", str(bbox[3]))
                        
                        clip_path.remove(path)
                        clip_path.append(rect)
                        simplified += 1
                        
                        logger.debug(f"Simplificado clip com {len(d)} caracteres")
        
        return simplified
    
    def _estimate_path_bbox(self, d: str) -> Optional[Tuple[float, float, float, float]]:
        """
        Estima bounding box de um path.
        
        Returns:
            Tuple (x, y, width, height) ou None
        """
        try:
            # Extrair coordenadas numéricas
            numbers = re.findall(r'[-+]?\d*\.?\d+', d)
            
            if len(numbers) < 4:
                return None
            
            coords = [float(n) for n in numbers]
            
            # Separar X e Y
            xs = coords[::2]
            ys = coords[1::2]
            
            if not xs or not ys:
                return None
            
            min_x = min(xs)
            max_x = max(xs)
            min_y = min(ys)
            max_y = max(ys)
            
            return (min_x, min_y, max_x - min_x, max_y - min_y)
            
        except Exception:
            return None
    
    def remove_empty_clips(self, svg_root: etree.Element) -> int:
        """
        Remove clip-paths vazios ou inválidos.
        
        Returns:
            Número de clips removidos
        """
        removed = 0
        
        for clip_path in self.find_clipaths(svg_root):
            # Verificar se tem conteúdo válido
            has_content = len(list(clip_path)) > 0
            
            if not has_content:
                clip_id = clip_path.get("id")
                clip_path.getparent().remove(clip_path)
                removed += 1
                logger.debug(f"Removido clip vazio: {clip_id}")
        
        return removed


# ==============================================================================
# FUNÇÕES DE CONVENIÊNCIA
# ==============================================================================

_handler: Optional[ClipPathHandler] = None


def get_clippath_handler() -> ClipPathHandler:
    """Retorna instância global."""
    global _handler
    if _handler is None:
        _handler = ClipPathHandler()
    return _handler


def process_svg_clips(svg_content: str) -> str:
    """
    Processa e corrige clips em SVG.
    
    Args:
        svg_content: SVG como string
        
    Returns:
        SVG processado
    """
    handler = get_clippath_handler()
    
    root = etree.fromstring(svg_content.encode('utf-8'))
    
    # Corrigir referências quebradas
    handler.fix_broken_clips(root)
    
    # Simplificar complexos
    handler.simplify_complex_clips(root)
    
    # Remover vazios
    handler.remove_empty_clips(root)
    
    return etree.tostring(root, encoding='unicode')

"""
AutoTabloide AI - Bleed and Trim System
=========================================
Sistema de sangria e marca de corte configurável.
PROTOCOLO DE RETIFICAÇÃO: Passo 44 (Sangria configurável).

Gerencia bleed, trim marks, e safe zone para impressão.
"""

import logging
from typing import Optional, Tuple, Dict, Any
from dataclasses import dataclass
from lxml import etree

logger = logging.getLogger("Bleed")


@dataclass
class BleedConfig:
    """Configuração de sangria."""
    bleed_mm: float = 3.0      # Sangria padrão
    safe_zone_mm: float = 5.0  # Zona segura (margem interna)
    show_trim_marks: bool = True
    show_bleed_box: bool = False
    trim_mark_length_mm: float = 5.0
    trim_mark_offset_mm: float = 2.0


class BleedManager:
    """
    Gerencia sangria e marcas de corte.
    
    PASSO 44: Sangria configurável para diferentes gráficas.
    """
    
    # Conversões
    MM_TO_PT = 2.83465  # 1mm = 2.83465pt
    
    def __init__(self, config: Optional[BleedConfig] = None):
        self.config = config or BleedConfig()
    
    def mm_to_pt(self, mm: float) -> float:
        """Converte milímetros para pontos."""
        return mm * self.MM_TO_PT
    
    def pt_to_mm(self, pt: float) -> float:
        """Converte pontos para milímetros."""
        return pt / self.MM_TO_PT
    
    def calculate_dimensions(
        self,
        width_mm: float,
        height_mm: float
    ) -> Dict[str, float]:
        """
        Calcula dimensões com sangria.
        
        Args:
            width_mm: Largura final (trim size) em mm
            height_mm: Altura final em mm
            
        Returns:
            Dict com todas as dimensões
        """
        bleed = self.config.bleed_mm
        safe = self.config.safe_zone_mm
        
        return {
            # Tamanho final (corte)
            "trim_width_mm": width_mm,
            "trim_height_mm": height_mm,
            
            # Tamanho com sangria (documento)
            "bleed_width_mm": width_mm + (bleed * 2),
            "bleed_height_mm": height_mm + (bleed * 2),
            
            # Área segura (texto/elementos importantes)
            "safe_width_mm": width_mm - (safe * 2),
            "safe_height_mm": height_mm - (safe * 2),
            
            # Offsets
            "bleed_mm": bleed,
            "safe_zone_mm": safe,
            
            # Em pontos (para SVG)
            "bleed_width_pt": self.mm_to_pt(width_mm + (bleed * 2)),
            "bleed_height_pt": self.mm_to_pt(height_mm + (bleed * 2)),
            "trim_width_pt": self.mm_to_pt(width_mm),
            "trim_height_pt": self.mm_to_pt(height_mm),
            "bleed_pt": self.mm_to_pt(bleed),
            "safe_zone_pt": self.mm_to_pt(safe),
        }
    
    def add_bleed_to_svg(
        self,
        svg_root: etree.Element,
        original_width: float,
        original_height: float
    ) -> etree.Element:
        """
        Adiciona sangria a um SVG existente.
        
        Args:
            svg_root: Raiz do SVG (em pt)
            original_width: Largura original em pt
            original_height: Altura original em pt
            
        Returns:
            SVG modificado com sangria
        """
        bleed_pt = self.mm_to_pt(self.config.bleed_mm)
        
        # Nova dimensão
        new_width = original_width + (bleed_pt * 2)
        new_height = original_height + (bleed_pt * 2)
        
        # Atualizar dimensões do SVG
        svg_root.set('width', f'{new_width}pt')
        svg_root.set('height', f'{new_height}pt')
        svg_root.set('viewBox', f'0 0 {new_width} {new_height}')
        
        # Criar grupo para conteúdo original
        content_group = etree.Element('g')
        content_group.set('transform', f'translate({bleed_pt}, {bleed_pt})')
        
        # Mover conteúdo para o grupo
        for child in list(svg_root):
            svg_root.remove(child)
            content_group.append(child)
        
        svg_root.append(content_group)
        
        # Adicionar marcas de corte se configurado
        if self.config.show_trim_marks:
            trim_marks = self._create_trim_marks(
                original_width, original_height, bleed_pt
            )
            svg_root.append(trim_marks)
        
        return svg_root
    
    def _create_trim_marks(
        self,
        trim_width: float,
        trim_height: float,
        bleed: float
    ) -> etree.Element:
        """Cria marcas de corte em SVG."""
        mark_length = self.mm_to_pt(self.config.trim_mark_length_mm)
        mark_offset = self.mm_to_pt(self.config.trim_mark_offset_mm)
        
        group = etree.Element('g')
        group.set('id', 'trim_marks')
        group.set('stroke', 'black')
        group.set('stroke-width', '0.25')
        group.set('fill', 'none')
        
        # Posições dos cantos (relativo ao documento com bleed)
        corners = [
            # Top-left
            (bleed, bleed),
            # Top-right
            (bleed + trim_width, bleed),
            # Bottom-left
            (bleed, bleed + trim_height),
            # Bottom-right
            (bleed + trim_width, bleed + trim_height),
        ]
        
        for x, y in corners:
            # Marca horizontal esquerda
            line1 = etree.SubElement(group, 'line')
            line1.set('x1', str(x - mark_offset - mark_length))
            line1.set('y1', str(y))
            line1.set('x2', str(x - mark_offset))
            line1.set('y2', str(y))
            
            # Marca vertical superior
            line2 = etree.SubElement(group, 'line')
            line2.set('x1', str(x))
            line2.set('y1', str(y - mark_offset - mark_length))
            line2.set('x2', str(x))
            line2.set('y2', str(y - mark_offset))
        
        return group
    
    def extend_background_to_bleed(
        self,
        svg_root: etree.Element,
        background_color: str = "#FFFFFF"
    ) -> None:
        """
        Estende cor de fundo até a sangria.
        
        Evita bordas brancas após o corte.
        """
        # Obter dimensões do documento
        width = float(svg_root.get('width', '0').replace('pt', ''))
        height = float(svg_root.get('height', '0').replace('pt', ''))
        
        # Criar retângulo de fundo
        bg_rect = etree.Element('rect')
        bg_rect.set('x', '0')
        bg_rect.set('y', '0')
        bg_rect.set('width', str(width))
        bg_rect.set('height', str(height))
        bg_rect.set('fill', background_color)
        bg_rect.set('id', 'bleed_background')
        
        # Inserir como primeiro elemento
        svg_root.insert(0, bg_rect)


# ==============================================================================
# PRESETS PARA GRÁFICAS COMUNS
# ==============================================================================

BLEED_PRESETS: Dict[str, BleedConfig] = {
    "standard": BleedConfig(
        bleed_mm=3.0,
        safe_zone_mm=5.0,
        show_trim_marks=True
    ),
    "wide": BleedConfig(
        bleed_mm=5.0,
        safe_zone_mm=8.0,
        show_trim_marks=True
    ),
    "minimal": BleedConfig(
        bleed_mm=2.0,
        safe_zone_mm=3.0,
        show_trim_marks=True
    ),
    "no_bleed": BleedConfig(
        bleed_mm=0.0,
        safe_zone_mm=5.0,
        show_trim_marks=False
    ),
    "large_format": BleedConfig(
        bleed_mm=10.0,
        safe_zone_mm=15.0,
        show_trim_marks=True,
        trim_mark_length_mm=10.0
    ),
}


def get_bleed_preset(name: str) -> BleedConfig:
    """Retorna preset de bleed pelo nome."""
    return BLEED_PRESETS.get(name, BLEED_PRESETS["standard"])

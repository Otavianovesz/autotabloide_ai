"""
AutoTabloide AI - Visual Traceability
=======================================
Rastreabilidade visual para identificação de tabloides.
PROTOCOLO DE RETIFICAÇÃO: Passo 48 (Rastreabilidade visual).

Adiciona marca d'água e QR code para rastreamento.
"""

import logging
from pathlib import Path
from typing import Optional, Dict, Any
from dataclasses import dataclass
from datetime import datetime
from lxml import etree
import hashlib

logger = logging.getLogger("Traceability")


@dataclass
class TraceabilityInfo:
    """Informações de rastreabilidade."""
    project_id: str
    version: int = 1
    created_at: datetime = None
    operator: str = ""
    machine_id: str = ""
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
    
    @property
    def trace_code(self) -> str:
        """Gera código de rastreabilidade único."""
        data = f"{self.project_id}_{self.version}_{self.created_at.isoformat()}"
        return hashlib.md5(data.encode()).hexdigest()[:12].upper()


class TraceabilityManager:
    """
    Gerencia rastreabilidade visual.
    
    PASSO 48: Identificação única de cada tabloide.
    """
    
    def __init__(self):
        pass
    
    def add_trace_code_to_svg(
        self,
        svg_root: etree.Element,
        info: TraceabilityInfo,
        position: str = "bottom-right"  # "bottom-left", "bottom-right", "top-left", "top-right"
    ) -> etree.Element:
        """
        Adiciona código de rastreabilidade ao SVG.
        
        Args:
            svg_root: Raiz do SVG
            info: Informações de rastreabilidade
            position: Posição do código
            
        Returns:
            SVG modificado
        """
        # Obter dimensões do SVG
        width_str = svg_root.get('width', '0').replace('pt', '').replace('px', '')
        height_str = svg_root.get('height', '0').replace('pt', '').replace('px', '')
        
        try:
            width = float(width_str)
            height = float(height_str)
        except ValueError:
            width, height = 800, 600
        
        # Calcular posição
        x, y = self._calculate_position(position, width, height)
        
        # Criar grupo de rastreabilidade
        group = etree.Element('g')
        group.set('id', 'traceability')
        
        # Código de texto
        code = info.trace_code
        
        text_element = etree.SubElement(group, 'text')
        text_element.set('x', str(x))
        text_element.set('y', str(y))
        text_element.set('font-family', 'Courier New, monospace')
        text_element.set('font-size', '6')
        text_element.set('fill', '#CCCCCC')
        text_element.set('opacity', '0.3')
        text_element.text = f"AT-{code}"
        
        # Adicionar metadata
        metadata = etree.SubElement(group, 'metadata')
        metadata.set('id', 'trace_metadata')
        
        trace_data = etree.SubElement(metadata, 'trace')
        trace_data.set('code', code)
        trace_data.set('project', info.project_id)
        trace_data.set('version', str(info.version))
        trace_data.set('created', info.created_at.isoformat())
        trace_data.set('operator', info.operator)
        trace_data.set('machine', info.machine_id)
        
        svg_root.append(group)
        
        return svg_root
    
    def _calculate_position(
        self,
        position: str,
        width: float,
        height: float
    ) -> tuple:
        """Calcula coordenadas baseado na posição."""
        margin = 5
        
        positions = {
            "bottom-right": (width - margin, height - margin),
            "bottom-left": (margin, height - margin),
            "top-right": (width - margin, margin + 6),
            "top-left": (margin, margin + 6),
        }
        
        return positions.get(position, positions["bottom-right"])
    
    def generate_qr_code_svg(self, data: str, size: int = 50) -> str:
        """
        Gera QR code como SVG.
        
        Args:
            data: Dados para codificar
            size: Tamanho em pixels
            
        Returns:
            String SVG do QR code
        """
        try:
            import qrcode
            from qrcode.image.svg import SvgPathImage
            
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=1,
            )
            qr.add_data(data)
            qr.make(fit=True)
            
            img = qr.make_image(
                image_factory=SvgPathImage,
                fill_color="black"
            )
            
            return img.to_string().decode('utf-8')
            
        except ImportError:
            logger.warning("qrcode not available, skipping QR generation")
            return ""
    
    def add_qr_to_svg(
        self,
        svg_root: etree.Element,
        info: TraceabilityInfo,
        qr_size: int = 30
    ) -> etree.Element:
        """
        Adiciona QR code ao SVG.
        
        Args:
            svg_root: Raiz do SVG
            info: Informações a codificar
            qr_size: Tamanho do QR
            
        Returns:
            SVG modificado
        """
        # Gerar dados do QR
        qr_data = f"AUTOTABLOIDE|{info.trace_code}|{info.project_id}|v{info.version}"
        
        qr_svg = self.generate_qr_code_svg(qr_data, qr_size)
        
        if not qr_svg:
            return svg_root
        
        try:
            # Parsear QR como elemento
            qr_element = etree.fromstring(qr_svg.encode('utf-8'))
            
            # Posicionar no canto
            width_str = svg_root.get('width', '0').replace('pt', '').replace('px', '')
            height_str = svg_root.get('height', '0').replace('pt', '').replace('px', '')
            
            width = float(width_str) if width_str else 800
            height = float(height_str) if height_str else 600
            
            # Criar grupo com transformação
            group = etree.Element('g')
            group.set('id', 'traceability_qr')
            group.set('transform', f'translate({width - qr_size - 5}, {height - qr_size - 5}) scale(0.3)')
            group.set('opacity', '0.15')
            
            group.append(qr_element)
            svg_root.append(group)
            
        except Exception as e:
            logger.debug(f"Erro ao adicionar QR: {e}")
        
        return svg_root
    
    def extract_trace_code(self, svg_root: etree.Element) -> Optional[str]:
        """Extrai código de rastreabilidade de um SVG."""
        trace_elem = svg_root.find('.//trace')
        if trace_elem is not None:
            return trace_elem.get('code')
        return None


# ==============================================================================
# MACHINE ID
# ==============================================================================

def get_machine_id() -> str:
    """Gera ID único da máquina."""
    import uuid
    import platform
    
    # Combinação de fatores
    node = hex(uuid.getnode())[2:]  # MAC address
    platform_str = platform.node()[:8]
    
    return f"{platform_str}_{node[:6]}"


# ==============================================================================
# INSTÂNCIA GLOBAL
# ==============================================================================

_manager: Optional[TraceabilityManager] = None


def get_traceability_manager() -> TraceabilityManager:
    """Retorna instância global."""
    global _manager
    if _manager is None:
        _manager = TraceabilityManager()
    return _manager


def add_traceability(
    svg_content: str,
    project_id: str,
    version: int = 1
) -> str:
    """
    Função de conveniência para adicionar rastreabilidade.
    
    Args:
        svg_content: SVG como string
        project_id: ID do projeto
        version: Versão do tabloide
        
    Returns:
        SVG modificado como string
    """
    manager = get_traceability_manager()
    
    info = TraceabilityInfo(
        project_id=project_id,
        version=version,
        machine_id=get_machine_id()
    )
    
    root = etree.fromstring(svg_content.encode('utf-8'))
    root = manager.add_trace_code_to_svg(root, info)
    
    return etree.tostring(root, encoding='unicode')

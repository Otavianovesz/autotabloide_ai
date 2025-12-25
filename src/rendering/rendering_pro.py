"""
AutoTabloide AI - Professional Rendering Module
=================================================
Century Checklist Items 46-60: Motor Vetorial e Renderização.
Overprint, Sangria, Marcas de Corte, Text Fitting, Metadados XMP.
"""

from __future__ import annotations
import re
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Optional, List, Dict, Tuple, Any
from dataclasses import dataclass
from datetime import datetime
import hashlib
import logging

logger = logging.getLogger("AutoTabloide.Rendering")


# ==============================================================================
# ITEM 46: Overprint de Preto (K=100)
# ==============================================================================

class OverprintManager:
    """
    Gerencia overprint para texto preto.
    Evita contorno branco se registro da impressora falhar.
    """
    
    # Cores que devem ter overprint
    BLACK_COLORS = [
        "#000000", "#000", "black",
        "rgb(0,0,0)", "rgb(0, 0, 0)",
    ]
    
    @classmethod
    def add_overprint_to_svg(cls, svg_content: str) -> str:
        """
        Adiciona atributo de overprint a elementos pretos.
        
        Args:
            svg_content: Conteúdo SVG original
            
        Returns:
            SVG com overprint aplicado
        """
        # Parse SVG
        try:
            root = ET.fromstring(svg_content)
        except ET.ParseError as e:
            logger.error(f"Erro ao parsear SVG: {e}")
            return svg_content
        
        # Procura elementos de texto
        for elem in root.iter():
            fill = elem.get("fill", "").lower()
            style = elem.get("style", "")
            
            # Verifica se é preto
            is_black = any(bc in fill for bc in cls.BLACK_COLORS)
            if not is_black and "fill:" in style.lower():
                for bc in cls.BLACK_COLORS:
                    if bc in style.lower():
                        is_black = True
                        break
            
            if is_black:
                # Adiciona atributos de overprint
                elem.set("style", f"{style}; color-rendering:auto; shape-rendering:geometricPrecision")
                # Marca para overprint no PDF (via atributo customizado)
                elem.set("data-overprint", "true")
        
        return ET.tostring(root, encoding="unicode")
    
    @classmethod
    def get_ghostscript_overprint_args(cls) -> List[str]:
        """Retorna argumentos do Ghostscript para overprint."""
        return [
            "-dOverprint=/enable",
            "-dPDFSETTINGS=/prepress",
        ]


# ==============================================================================
# ITEM 47-48: Sangria e Marcas de Corte
# ==============================================================================

@dataclass
class BleedConfig:
    """Configuração de sangria."""
    bleed_mm: float = 3.0
    crop_marks: bool = True
    crop_mark_length_mm: float = 5.0
    crop_mark_offset_mm: float = 3.0


class BleedAndCropMarks:
    """
    Adiciona sangria e marcas de corte ao documento.
    
    Sangria (Bleed): Extensão da arte além da linha de corte.
    Marcas de Corte (Crop Marks): Linhas que indicam onde cortar.
    """
    
    MM_TO_PT = 2.83465  # 1mm = 2.83465 points
    
    def __init__(self, config: Optional[BleedConfig] = None):
        self.config = config or BleedConfig()
    
    def add_bleed_to_svg(
        self, 
        svg_content: str,
        doc_width_mm: float,
        doc_height_mm: float
    ) -> str:
        """
        Expande SVG para incluir área de sangria.
        
        Args:
            svg_content: SVG original
            doc_width_mm: Largura do documento em mm
            doc_height_mm: Altura do documento em mm
            
        Returns:
            SVG expandido com sangria
        """
        bleed_pt = self.config.bleed_mm * self.MM_TO_PT
        
        try:
            root = ET.fromstring(svg_content)
            
            # Obtém dimensões atuais
            width = float(root.get("width", "0").replace("mm", "").replace("pt", ""))
            height = float(root.get("height", "0").replace("mm", "").replace("pt", ""))
            
            # Calcula novas dimensões com sangria
            new_width = width + (2 * bleed_pt)
            new_height = height + (2 * bleed_pt)
            
            # Atualiza dimensões
            root.set("width", f"{new_width}pt")
            root.set("height", f"{new_height}pt")
            
            # Atualiza viewBox para manter proporção
            viewbox = root.get("viewBox", f"0 0 {width} {height}")
            vb_parts = viewbox.split()
            if len(vb_parts) == 4:
                new_viewbox = f"-{bleed_pt} -{bleed_pt} {new_width} {new_height}"
                root.set("viewBox", new_viewbox)
            
            return ET.tostring(root, encoding="unicode")
            
        except Exception as e:
            logger.error(f"Erro ao adicionar sangria: {e}")
            return svg_content
    
    def generate_crop_marks_svg(
        self,
        doc_width_mm: float,
        doc_height_mm: float
    ) -> str:
        """
        Gera SVG com marcas de corte.
        
        Args:
            doc_width_mm: Largura do documento
            doc_height_mm: Altura do documento
            
        Returns:
            SVG contendo apenas as marcas de corte
        """
        if not self.config.crop_marks:
            return ""
        
        bleed = self.config.bleed_mm * self.MM_TO_PT
        mark_len = self.config.crop_mark_length_mm * self.MM_TO_PT
        offset = self.config.crop_mark_offset_mm * self.MM_TO_PT
        
        width = doc_width_mm * self.MM_TO_PT
        height = doc_height_mm * self.MM_TO_PT
        
        # Posições das marcas
        marks = []
        
        # Canto superior esquerdo
        marks.extend([
            f"M {bleed - offset} {bleed} L {bleed - offset - mark_len} {bleed}",  # Horizontal
            f"M {bleed} {bleed - offset} L {bleed} {bleed - offset - mark_len}",  # Vertical
        ])
        
        # Canto superior direito
        marks.extend([
            f"M {width + bleed + offset} {bleed} L {width + bleed + offset + mark_len} {bleed}",
            f"M {width + bleed} {bleed - offset} L {width + bleed} {bleed - offset - mark_len}",
        ])
        
        # Canto inferior esquerdo
        marks.extend([
            f"M {bleed - offset} {height + bleed} L {bleed - offset - mark_len} {height + bleed}",
            f"M {bleed} {height + bleed + offset} L {bleed} {height + bleed + offset + mark_len}",
        ])
        
        # Canto inferior direito
        marks.extend([
            f"M {width + bleed + offset} {height + bleed} L {width + bleed + offset + mark_len} {height + bleed}",
            f"M {width + bleed} {height + bleed + offset} L {width + bleed} {height + bleed + offset + mark_len}",
        ])
        
        paths = "\n".join([
            f'<path d="{m}" stroke="#000000" stroke-width="0.25" fill="none"/>'
            for m in marks
        ])
        
        total_width = width + (2 * bleed) + (2 * offset) + (2 * mark_len)
        total_height = height + (2 * bleed) + (2 * offset) + (2 * mark_len)
        
        return f'''<svg xmlns="http://www.w3.org/2000/svg" 
            width="{total_width}pt" height="{total_height}pt"
            viewBox="0 0 {total_width} {total_height}">
            <g id="crop-marks">
                {paths}
            </g>
        </svg>'''


# ==============================================================================
# ITEM 50: Fallback de Fonte Robusto
# ==============================================================================

class FontFallbackResolver:
    """
    Resolve fontes com cascata de fallbacks.
    Garante que sempre haverá uma fonte disponível.
    """
    
    FONT_CASCADES = {
        "Roboto-Bold": [
            "Roboto-Bold", "Roboto Bold", "Arial Bold", 
            "Helvetica Bold", "Arial", "Helvetica", "sans-serif"
        ],
        "Roboto-Regular": [
            "Roboto-Regular", "Roboto", "Arial", 
            "Helvetica", "sans-serif"
        ],
        "JetBrainsMono": [
            "JetBrainsMono-Regular", "JetBrains Mono",
            "Consolas", "Courier New", "monospace"
        ],
    }
    
    def __init__(self, fonts_dir: Path):
        self.fonts_dir = fonts_dir
        self._available_fonts: Dict[str, Path] = {}
        self._scan_fonts()
    
    def _scan_fonts(self):
        """Escaneia fontes disponíveis no diretório."""
        if not self.fonts_dir.exists():
            logger.warning(f"Diretório de fontes não existe: {self.fonts_dir}")
            return
        
        for ext in ["*.ttf", "*.otf", "*.woff", "*.woff2"]:
            for font_file in self.fonts_dir.glob(ext):
                self._available_fonts[font_file.stem.lower()] = font_file
                # Também registra sem hífens
                clean_name = font_file.stem.lower().replace("-", "").replace("_", "")
                self._available_fonts[clean_name] = font_file
        
        logger.info(f"Fontes disponíveis: {len(self._available_fonts)}")
    
    def resolve(self, font_name: str) -> Optional[Path]:
        """
        Resolve fonte com fallback.
        
        Args:
            font_name: Nome da fonte desejada
            
        Returns:
            Caminho da fonte encontrada ou None
        """
        # Tenta cascata específica
        cascade = self.FONT_CASCADES.get(font_name, [font_name])
        
        for candidate in cascade:
            clean = candidate.lower().replace("-", "").replace(" ", "")
            if clean in self._available_fonts:
                return self._available_fonts[clean]
        
        # Fallback: qualquer fonte disponível
        if self._available_fonts:
            fallback = next(iter(self._available_fonts.values()))
            logger.warning(f"Fonte '{font_name}' não encontrada, usando fallback: {fallback.name}")
            return fallback
        
        return None
    
    def get_css_fallback(self, font_name: str) -> str:
        """Retorna string CSS com fallbacks."""
        cascade = self.FONT_CASCADES.get(font_name, [font_name, "sans-serif"])
        parts = []
        for f in cascade:
            if " " in f:
                parts.append(f'"{f}"')
            else:
                parts.append(f)
        return ", ".join(parts)
    
    @property
    def available_fonts(self) -> List[str]:
        """Lista de fontes disponíveis."""
        return list(set(p.name for p in self._available_fonts.values()))


# ==============================================================================
# ITEM 51-52: Text Fitting e Kerning
# ==============================================================================

@dataclass
class TextFitResult:
    """Resultado do ajuste de texto."""
    font_size: float
    letter_spacing: float
    lines: List[str]
    fits: bool


class TextFitter:
    """
    Ajusta texto para caber em uma caixa.
    
    Estratégia:
    1. Tenta com tamanho original
    2. Reduz letter-spacing até mínimo
    3. Reduz font-size até mínimo
    4. Se ainda não couber, trunca com "..."
    """
    
    def __init__(
        self,
        min_font_size: float = 6.0,
        min_letter_spacing: float = -0.05,  # em
        font_step: float = 0.5,
        spacing_step: float = 0.01,
    ):
        self.min_font_size = min_font_size
        self.min_letter_spacing = min_letter_spacing
        self.font_step = font_step
        self.spacing_step = spacing_step
    
    def fit(
        self,
        text: str,
        box_width: float,
        box_height: float,
        initial_font_size: float,
        char_width_ratio: float = 0.6,  # Largura média / altura da fonte
        line_height_ratio: float = 1.2,
    ) -> TextFitResult:
        """
        Calcula parâmetros para texto caber na caixa.
        
        Args:
            text: Texto a renderizar
            box_width: Largura da caixa em points
            box_height: Altura da caixa em points
            initial_font_size: Tamanho inicial da fonte
            char_width_ratio: Proporção largura/altura do caractere
            line_height_ratio: Proporção altura da linha / tamanho da fonte
            
        Returns:
            TextFitResult com parâmetros calculados
        """
        font_size = initial_font_size
        letter_spacing = 0.0
        
        while font_size >= self.min_font_size:
            # Calcula métricas
            char_width = font_size * char_width_ratio * (1 + letter_spacing)
            chars_per_line = max(1, int(box_width / char_width))
            line_height = font_size * line_height_ratio
            max_lines = max(1, int(box_height / line_height))
            
            # Tenta quebrar texto
            lines = self._wrap_text(text, chars_per_line)
            
            if len(lines) <= max_lines:
                # Verifica se todas as linhas cabem na largura
                fits = all(len(line) <= chars_per_line for line in lines)
                
                if fits:
                    return TextFitResult(
                        font_size=font_size,
                        letter_spacing=letter_spacing,
                        lines=lines,
                        fits=True
                    )
            
            # Tenta reduzir letter-spacing primeiro
            if letter_spacing > self.min_letter_spacing:
                letter_spacing -= self.spacing_step
                continue
            
            # Reduz tamanho da fonte
            font_size -= self.font_step
            letter_spacing = 0.0  # Reset
        
        # Não coube - trunca
        lines = self._wrap_text(text, chars_per_line)[:max_lines]
        if lines:
            lines[-1] = self._truncate(lines[-1], chars_per_line)
        
        return TextFitResult(
            font_size=self.min_font_size,
            letter_spacing=self.min_letter_spacing,
            lines=lines,
            fits=False
        )
    
    def _wrap_text(self, text: str, chars_per_line: int) -> List[str]:
        """Quebra texto em linhas."""
        words = text.split()
        lines = []
        current_line = ""
        
        for word in words:
            test_line = f"{current_line} {word}".strip()
            
            if len(test_line) <= chars_per_line:
                current_line = test_line
            else:
                if current_line:
                    lines.append(current_line)
                
                # Palavra muito longa - divide
                if len(word) > chars_per_line:
                    while len(word) > chars_per_line:
                        lines.append(word[:chars_per_line])
                        word = word[chars_per_line:]
                    current_line = word
                else:
                    current_line = word
        
        if current_line:
            lines.append(current_line)
        
        return lines
    
    def _truncate(self, text: str, max_len: int) -> str:
        """Trunca texto com elipsis."""
        if len(text) <= max_len:
            return text
        return text[:max_len - 3] + "..."


# ==============================================================================
# ITEM 54: Verificação de Resolução (300 DPI)
# ==============================================================================

class ImageResolutionChecker:
    """
    Verifica se imagens têm resolução adequada para impressão.
    Mínimo recomendado: 300 DPI.
    """
    
    MIN_DPI = 300
    
    @classmethod
    def check_resolution(
        cls,
        image_width_px: int,
        image_height_px: int,
        print_width_mm: float,
        print_height_mm: float
    ) -> Tuple[bool, int, int]:
        """
        Verifica se imagem tem resolução adequada.
        
        Args:
            image_width_px: Largura da imagem em pixels
            image_height_px: Altura da imagem em pixels
            print_width_mm: Largura de impressão em mm
            print_height_mm: Altura de impressão em mm
            
        Returns:
            Tuple (adequate, effective_dpi_x, effective_dpi_y)
        """
        # Converte mm para polegadas (1 inch = 25.4mm)
        print_width_in = print_width_mm / 25.4
        print_height_in = print_height_mm / 25.4
        
        # Calcula DPI efetivo
        dpi_x = int(image_width_px / print_width_in) if print_width_in > 0 else 0
        dpi_y = int(image_height_px / print_height_in) if print_height_in > 0 else 0
        
        min_dpi = min(dpi_x, dpi_y)
        
        return (min_dpi >= cls.MIN_DPI, dpi_x, dpi_y)
    
    @classmethod
    def get_recommendation(cls, effective_dpi: int) -> str:
        """Retorna recomendação baseada no DPI."""
        if effective_dpi >= 300:
            return "Excelente qualidade para impressão"
        elif effective_dpi >= 200:
            return "Qualidade aceitável, pode haver leve perda de nitidez"
        elif effective_dpi >= 150:
            return "Qualidade baixa, recomenda-se imagem maior"
        else:
            return "Qualidade insuficiente para impressão profissional"


# ==============================================================================
# ITEM 55: Metadados XMP para PDF
# ==============================================================================

class XMPMetadataGenerator:
    """Gera metadados XMP para incorporar no PDF."""
    
    @staticmethod
    def generate(
        title: str = "Tabloide",
        creator: str = "AutoTabloide AI",
        subject: str = "",
        keywords: Optional[List[str]] = None,
        project_id: Optional[str] = None
    ) -> str:
        """
        Gera XML de metadados XMP.
        
        Args:
            title: Título do documento
            creator: Software criador
            subject: Assunto/descrição
            keywords: Lista de palavras-chave
            project_id: ID único do projeto
            
        Returns:
            String XML com metadados XMP
        """
        now = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S+00:00")
        keywords_str = ", ".join(keywords) if keywords else ""
        doc_id = project_id or hashlib.md5(f"{title}{now}".encode()).hexdigest()
        
        return f'''<?xpacket begin="\ufeff" id="W5M0MpCehiHzreSzNTczkc9d"?>
<x:xmpmeta xmlns:x="adobe:ns:meta/" x:xmptk="AutoTabloide AI">
  <rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">
    <rdf:Description rdf:about=""
        xmlns:dc="http://purl.org/dc/elements/1.1/"
        xmlns:xmp="http://ns.adobe.com/xap/1.0/"
        xmlns:xmpMM="http://ns.adobe.com/xap/1.0/mm/"
        xmlns:pdf="http://ns.adobe.com/pdf/1.3/"
        xmlns:pdfx="http://ns.adobe.com/pdfx/1.3/">
      <dc:title>
        <rdf:Alt>
          <rdf:li xml:lang="x-default">{title}</rdf:li>
        </rdf:Alt>
      </dc:title>
      <dc:creator>
        <rdf:Seq>
          <rdf:li>{creator}</rdf:li>
        </rdf:Seq>
      </dc:creator>
      <dc:description>
        <rdf:Alt>
          <rdf:li xml:lang="x-default">{subject}</rdf:li>
        </rdf:Alt>
      </dc:description>
      <dc:subject>
        <rdf:Bag>
          <rdf:li>{keywords_str}</rdf:li>
        </rdf:Bag>
      </dc:subject>
      <xmp:CreatorTool>{creator}</xmp:CreatorTool>
      <xmp:CreateDate>{now}</xmp:CreateDate>
      <xmp:ModifyDate>{now}</xmp:ModifyDate>
      <xmpMM:DocumentID>uuid:{doc_id}</xmpMM:DocumentID>
      <pdf:Producer>{creator}</pdf:Producer>
      <pdf:Keywords>{keywords_str}</pdf:Keywords>
      <pdfx:SourceModified>{now}</pdfx:SourceModified>
    </rdf:Description>
  </rdf:RDF>
</x:xmpmeta>
<?xpacket end="w"?>'''


# ==============================================================================
# ITEM 56: Limpeza de SVG
# ==============================================================================

class SVGCleaner:
    """
    Remove metadados desnecessários do SVG.
    Reduz tamanho do arquivo removendo namespaces da Adobe/Inkscape.
    """
    
    # Namespaces a remover
    UNWANTED_NAMESPACES = [
        "inkscape",
        "sodipodi",
        "xmlns:inkscape",
        "xmlns:sodipodi",
        "adobe",
        "illustrator",
    ]
    
    # Atributos a remover
    UNWANTED_ATTRIBUTES = [
        "inkscape:version",
        "inkscape:export-filename",
        "inkscape:export-xdpi",
        "inkscape:export-ydpi",
        "sodipodi:docname",
        "sodipodi:version",
        "xmlns:inkscape",
        "xmlns:sodipodi",
        "xmlns:cc",
        "xmlns:dc",
        "xmlns:rdf",
    ]
    
    @classmethod
    def clean(cls, svg_content: str) -> str:
        """
        Remove metadados desnecessários do SVG.
        
        Args:
            svg_content: Conteúdo SVG original
            
        Returns:
            SVG limpo
        """
        # Remove atributos via regex (mais rápido que parse)
        for attr in cls.UNWANTED_ATTRIBUTES:
            svg_content = re.sub(
                rf'\s*{re.escape(attr)}="[^"]*"', 
                '', 
                svg_content
            )
        
        # Remove elementos de metadados
        svg_content = re.sub(
            r'<metadata>.*?</metadata>',
            '',
            svg_content,
            flags=re.DOTALL
        )
        
        # Remove comentários
        svg_content = re.sub(
            r'<!--.*?-->',
            '',
            svg_content,
            flags=re.DOTALL
        )
        
        # Remove espaços extras
        svg_content = re.sub(r'\n\s*\n', '\n', svg_content)
        
        return svg_content.strip()
    
    @classmethod
    def minify(cls, svg_content: str) -> str:
        """Minifica SVG removendo espaços desnecessários."""
        # Remove quebras de linha
        svg_content = svg_content.replace('\n', ' ')
        # Remove espaços múltiplos
        svg_content = re.sub(r'\s+', ' ', svg_content)
        # Remove espaços antes/depois de tags
        svg_content = re.sub(r'>\s+<', '><', svg_content)
        
        return svg_content.strip()


# ==============================================================================
# ITEM 60: Validação de PDF
# ==============================================================================

class PDFValidator:
    """
    Valida PDF gerado antes de entregar ao usuário.
    """
    
    @staticmethod
    def validate(pdf_path: Path) -> Tuple[bool, str]:
        """
        Valida arquivo PDF.
        
        Args:
            pdf_path: Caminho do PDF
            
        Returns:
            Tuple (valid, message)
        """
        if not pdf_path.exists():
            return (False, "Arquivo não existe")
        
        size = pdf_path.stat().st_size
        
        if size == 0:
            return (False, "Arquivo vazio (0 bytes)")
        
        if size < 100:
            return (False, f"Arquivo muito pequeno ({size} bytes)")
        
        # Verifica header do PDF
        try:
            with open(pdf_path, "rb") as f:
                header = f.read(8)
                if not header.startswith(b"%PDF-"):
                    return (False, "Não é um arquivo PDF válido")
                
                # Verifica EOF
                f.seek(-32, 2)
                tail = f.read()
                if b"%%EOF" not in tail:
                    return (False, "PDF sem marcador de fim (%%EOF)")
        except Exception as e:
            return (False, f"Erro ao ler arquivo: {e}")
        
        return (True, f"PDF válido ({size:,} bytes)")


# ==============================================================================
# EXPORTS
# ==============================================================================

__all__ = [
    "OverprintManager",
    "BleedConfig",
    "BleedAndCropMarks",
    "FontFallbackResolver",
    "TextFitter",
    "TextFitResult",
    "ImageResolutionChecker",
    "XMPMetadataGenerator",
    "SVGCleaner",
    "PDFValidator",
]

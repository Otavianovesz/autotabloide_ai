"""
AutoTabloide AI - PDF Export Pipeline
======================================
PROTOCOLO DE CONVERGÊNCIA INDUSTRIAL - Fase 7
Passos 181-190: Export PDF industrial grade via Ghostscript/CairoSVG.

Suporta:
- Conversão SVG -> PDF de alta fidelidade
- Páginas múltiplas
- CMYK opcional via ICC profiles
"""

from __future__ import annotations
from pathlib import Path
from typing import List, Optional, Dict, Tuple
import subprocess
import tempfile
import shutil
import logging

logger = logging.getLogger("PDFExport")


# =============================================================================
# PDF EXPORTER
# =============================================================================

class PDFExporter:
    """Exporta SVG para PDF de qualidade profissional."""
    
    def __init__(self, system_root: str):
        self.system_root = Path(system_root)
        self.bin_dir = self.system_root / "bin"
        self.profiles_dir = self.system_root / "assets" / "profiles"
        self.temp_dir = self.system_root / "temp_render"
        
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        
        self._ghostscript_path = self._find_ghostscript()
        self._has_cairosvg = self._check_cairosvg()
    
    def _find_ghostscript(self) -> Optional[str]:
        """Localiza Ghostscript."""
        candidates = [
            self.bin_dir / "gswin64c.exe",
            self.bin_dir / "gswin32c.exe",
            self.bin_dir / "gs",
        ]
        
        for path in candidates:
            if path.exists():
                return str(path)
        
        # Tenta no PATH do sistema
        for cmd in ["gswin64c", "gswin32c", "gs"]:
            try:
                result = subprocess.run(
                    [cmd, "--version"],
                    capture_output=True,
                    timeout=5
                )
                if result.returncode == 0:
                    return cmd
            except:
                pass
        
        return None
    
    def _check_cairosvg(self) -> bool:
        """Verifica se CairoSVG está disponível."""
        try:
            import cairosvg
            return True
        except ImportError:
            return False
    
    def export_svg_to_pdf(
        self,
        svg_path: str,
        output_path: str,
        width_mm: float = 297,
        height_mm: float = 420,
        dpi: int = 300
    ) -> bool:
        """
        Exporta SVG para PDF.
        
        Args:
            svg_path: Caminho do SVG
            output_path: Caminho de saída do PDF
            width_mm: Largura em mm
            height_mm: Altura em mm
            dpi: DPI para rasterização
            
        Returns:
            True se sucesso
        """
        if self._has_cairosvg:
            return self._export_via_cairosvg(svg_path, output_path, width_mm, height_mm, dpi)
        else:
            logger.warning("CairoSVG não disponível. Tentando fallback.")
            return self._export_via_inkscape(svg_path, output_path)
    
    def _export_via_cairosvg(
        self,
        svg_path: str,
        output_path: str,
        width_mm: float,
        height_mm: float,
        dpi: int
    ) -> bool:
        """Exporta via CairoSVG."""
        try:
            import cairosvg
            
            # Converte mm para pixels
            width_px = int(width_mm * dpi / 25.4)
            height_px = int(height_mm * dpi / 25.4)
            
            cairosvg.svg2pdf(
                url=svg_path,
                write_to=output_path,
                output_width=width_px,
                output_height=height_px,
                dpi=dpi
            )
            
            logger.info(f"PDF exportado: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Erro CairoSVG: {e}")
            return False
    
    def _export_via_inkscape(self, svg_path: str, output_path: str) -> bool:
        """Fallback via Inkscape CLI."""
        try:
            result = subprocess.run(
                ["inkscape", svg_path, "--export-type=pdf", f"--export-filename={output_path}"],
                capture_output=True,
                timeout=60
            )
            return result.returncode == 0
        except Exception as e:
            logger.error(f"Erro Inkscape: {e}")
            return False
    
    def export_multiple_pages(
        self,
        svg_paths: List[str],
        output_path: str,
        width_mm: float = 297,
        height_mm: float = 420,
        dpi: int = 300
    ) -> bool:
        """
        Exporta múltiplos SVGs para PDF multipáginas.
        
        Args:
            svg_paths: Lista de caminhos SVG
            output_path: Caminho do PDF final
            
        Returns:
            True se sucesso
        """
        if not svg_paths:
            return False
        
        if len(svg_paths) == 1:
            return self.export_svg_to_pdf(svg_paths[0], output_path, width_mm, height_mm, dpi)
        
        # Exporta cada SVG para PDF temporário
        temp_pdfs = []
        
        for i, svg_path in enumerate(svg_paths):
            temp_pdf = self.temp_dir / f"page_{i:03d}.pdf"
            if self.export_svg_to_pdf(svg_path, str(temp_pdf), width_mm, height_mm, dpi):
                temp_pdfs.append(str(temp_pdf))
        
        if not temp_pdfs:
            return False
        
        # Merge PDFs
        success = self._merge_pdfs(temp_pdfs, output_path)
        
        # Cleanup
        for pdf in temp_pdfs:
            Path(pdf).unlink(missing_ok=True)
        
        return success
    
    def _merge_pdfs(self, pdf_paths: List[str], output_path: str) -> bool:
        """Merge múltiplos PDFs via Ghostscript."""
        if not self._ghostscript_path:
            logger.error("Ghostscript não encontrado para merge")
            return self._merge_via_pypdf(pdf_paths, output_path)
        
        try:
            cmd = [
                self._ghostscript_path,
                "-dBATCH",
                "-dNOPAUSE",
                "-q",
                "-sDEVICE=pdfwrite",
                f"-sOutputFile={output_path}",
            ] + pdf_paths
            
            result = subprocess.run(cmd, capture_output=True, timeout=120)
            
            if result.returncode == 0:
                logger.info(f"PDFs merged: {output_path}")
                return True
            else:
                logger.error(f"Ghostscript error: {result.stderr.decode()}")
                return False
                
        except Exception as e:
            logger.error(f"Merge error: {e}")
            return False
    
    def _merge_via_pypdf(self, pdf_paths: List[str], output_path: str) -> bool:
        """Fallback merge via PyPDF2/pypdf."""
        try:
            from pypdf import PdfMerger
            
            merger = PdfMerger()
            for pdf in pdf_paths:
                merger.append(pdf)
            
            merger.write(output_path)
            merger.close()
            
            return True
            
        except ImportError:
            try:
                from PyPDF2 import PdfMerger
                merger = PdfMerger()
                for pdf in pdf_paths:
                    merger.append(pdf)
                merger.write(output_path)
                merger.close()
                return True
            except:
                pass
        except Exception as e:
            logger.error(f"PyPDF merge error: {e}")
        
        return False
    
    def convert_to_cmyk(
        self,
        input_pdf: str,
        output_pdf: str,
        icc_profile: str = "CoatedFOGRA39.icc"
    ) -> bool:
        """
        Converte PDF RGB para CMYK usando perfil ICC.
        
        Args:
            input_pdf: PDF de entrada (RGB)
            output_pdf: PDF de saída (CMYK)
            icc_profile: Nome do perfil ICC
            
        Returns:
            True se sucesso
        """
        if not self._ghostscript_path:
            logger.warning("Ghostscript não disponível para CMYK")
            # Copia sem conversão
            shutil.copy(input_pdf, output_pdf)
            return True
        
        icc_path = self.profiles_dir / icc_profile
        if not icc_path.exists():
            logger.warning(f"ICC profile não encontrado: {icc_path}")
            shutil.copy(input_pdf, output_pdf)
            return True
        
        try:
            cmd = [
                self._ghostscript_path,
                "-dBATCH",
                "-dNOPAUSE",
                "-q",
                "-sDEVICE=pdfwrite",
                "-dColorConversionStrategy=/CMYK",
                "-dProcessColorModel=/DeviceCMYK",
                f"-sDefaultCMYKProfile={icc_path}",
                f"-sOutputFile={output_pdf}",
                input_pdf
            ]
            
            result = subprocess.run(cmd, capture_output=True, timeout=120)
            
            if result.returncode == 0:
                logger.info(f"CMYK conversion complete: {output_pdf}")
                return True
            else:
                logger.warning(f"CMYK conversion failed, copying original")
                shutil.copy(input_pdf, output_pdf)
                return True
                
        except Exception as e:
            logger.error(f"CMYK error: {e}")
            shutil.copy(input_pdf, output_pdf)
            return True


# =============================================================================
# BATCH RENDERER
# =============================================================================

class BatchRenderer:
    """
    Renderiza múltiplas páginas em lote.
    Conforme Vol. III - Factory de Produção.
    """
    
    def __init__(self, system_root: str, template_path: str):
        self.system_root = Path(system_root)
        self.template_path = template_path
        self.staging_dir = self.system_root / "staging"
        
        self.staging_dir.mkdir(parents=True, exist_ok=True)
        
        from src.rendering.vector import VectorEngine
        self.vector_engine = VectorEngine(strict_fonts=False)
    
    def render_pages(
        self,
        pages_data: List[Dict],
        output_format: str = "pdf"
    ) -> Tuple[bool, str]:
        """
        Renderiza múltiplas páginas.
        
        Args:
            pages_data: Lista de dicts com dados de cada página (slots -> produtos)
            output_format: "pdf" ou "svg"
            
        Returns:
            Tuple (success, output_path or error)
        """
        if not pages_data:
            return False, "Sem dados para renderizar"
        
        rendered_svgs = []
        
        for i, page_data in enumerate(pages_data):
            try:
                # Recarrega template limpo para cada página
                self.vector_engine.load_template(self.template_path)
                
                # Renderiza frame
                svg_bytes = self.vector_engine.render_frame(page_data)
                
                # Salva SVG intermediário
                svg_path = self.staging_dir / f"page_{i:03d}.svg"
                with open(svg_path, "wb") as f:
                    f.write(svg_bytes)
                
                rendered_svgs.append(str(svg_path))
                
            except Exception as e:
                logger.error(f"Erro na página {i}: {e}")
                continue
        
        if not rendered_svgs:
            return False, "Nenhuma página renderizada"
        
        if output_format == "svg":
            return True, rendered_svgs[0] if len(rendered_svgs) == 1 else str(self.staging_dir)
        
        # Export para PDF
        exporter = PDFExporter(str(self.system_root))
        output_pdf = self.staging_dir / "output.pdf"
        
        if exporter.export_multiple_pages(rendered_svgs, str(output_pdf)):
            return True, str(output_pdf)
        else:
            return False, "Falha na exportação PDF"


# =============================================================================
# QUICK EXPORT HELPER
# =============================================================================

def export_atelier_to_pdf(
    scene_data: Dict,
    template_path: str,
    output_path: str,
    system_root: str = "AutoTabloide_System_Root"
) -> Tuple[bool, str]:
    """
    Helper rápido para exportar dados do Atelier para PDF.
    
    Args:
        scene_data: Dados serializados da AtelierScene
        template_path: Caminho do template SVG
        output_path: Caminho de saída do PDF
        system_root: Diretório raiz do sistema
        
    Returns:
        Tuple (success, message)
    """
    try:
        from src.rendering.vector import VectorEngine
        
        engine = VectorEngine(strict_fonts=False)
        engine.load_template(template_path)
        
        # Extrai dados dos slots
        slots = scene_data.get("slots", [])
        slot_data = {}
        
        for slot in slots:
            if slot.get("product_data"):
                slot_id = slot.get("element_id", f"SLOT_{slot.get('slot_index', 0):02d}")
                slot_data[slot_id] = slot["product_data"]
        
        if not slot_data:
            return False, "Nenhum slot com produto"
        
        # Renderiza
        svg_bytes = engine.render_frame(slot_data)
        
        # Salva SVG temporário
        temp_svg = Path(system_root) / "staging" / "_export_temp.svg"
        temp_svg.parent.mkdir(parents=True, exist_ok=True)
        
        with open(temp_svg, "wb") as f:
            f.write(svg_bytes)
        
        # Exporta para PDF
        exporter = PDFExporter(system_root)
        
        if exporter.export_svg_to_pdf(str(temp_svg), output_path):
            temp_svg.unlink(missing_ok=True)
            return True, f"PDF exportado: {output_path}"
        else:
            return False, "Falha na conversão para PDF"
        
    except Exception as e:
        return False, f"Erro: {str(e)}"

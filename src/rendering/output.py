"""
AutoTabloide AI - Motor de Saída (PDF/Rasterização)
=====================================================
Renderização final conforme Vol. II, Cap. 7.
Conversão SVG -> PDF com suporte a CMYK via Ghostscript.
"""

import os
import subprocess
import logging
import tempfile
from typing import List, Optional, Tuple
from pathlib import Path

try:
    import cairosvg
    HAS_CAIRO = True
except ImportError:
    HAS_CAIRO = False

try:
    from PyPDF2 import PdfMerger, PdfReader
    HAS_PYPDF = True
except ImportError:
    HAS_PYPDF = False

# Configuração de Logs
logger = logging.getLogger("OutputEngine")


class OutputEngine:
    """
    Motor de Renderização e Ciência de Cores.
    Responsável pela conversão SVG -> PDF e PDF(RGB) -> PDF(CMYK/FOGRA39).
    
    Conforme Vol. II, Cap. 7:
    - Suporte a PDF/X-1a para offset
    - True Black Preservation (K=100%)
    - Combinação multipáginas
    """

    def __init__(self, system_root: str):
        self.system_root = Path(system_root)
        
        # Caminhos Críticos
        self.gs_path = self._find_ghostscript()
        self.icc_profile = self.system_root / "assets" / "profiles" / "CoatedFOGRA39.icc"
        
        # Diretório temporário para intermediários
        self.temp_dir = self.system_root / "temp_render"
        os.makedirs(self.temp_dir, exist_ok=True)
        
        self._verify_assets()

    def _find_ghostscript(self) -> str:
        """Localiza executável do Ghostscript."""
        # 1. Tenta na pasta bin do sistema
        local_gs = self.system_root / "bin" / "gswin64c.exe"
        if local_gs.exists():
            return str(local_gs)
        
        # 2. Tenta no PATH do sistema
        import shutil
        for gs_name in ["gswin64c", "gswin32c", "gs"]:
            gs_path = shutil.which(gs_name)
            if gs_path:
                return gs_path
        
        # 3. Fallback
        logger.warning("Ghostscript não encontrado. Conversão CMYK não disponível.")
        return ""

    def _verify_assets(self):
        """Verifica infraestrutura crítica."""
        if not self.gs_path:
            logger.warning("Ghostscript não disponível. Apenas exportação RGB será possível.")
        
        if not self.icc_profile.exists():
            logger.warning(f"Perfil ICC FOGRA39 ausente: {self.icc_profile}")

    # ==========================================================================
    # RENDERIZAÇÃO SVG -> PDF
    # ==========================================================================

    def render_pdf(
        self, 
        svg_content: bytes, 
        output_path: str,
        dpi: int = 300
    ) -> bool:
        """
        Passo 1: Converte SVG para PDF (ainda em RGB/sRGB).
        
        Args:
            svg_content: Conteúdo SVG como bytes
            output_path: Caminho do PDF de saída
            dpi: Resolução (300 para impressão offset)
        """
        if not HAS_CAIRO:
            raise ImportError("CairoSVG não instalado. Renderização impossível.")
        
        try:
            cairosvg.svg2pdf(
                bytestring=svg_content, 
                write_to=output_path,
                dpi=dpi
            )
            logger.debug(f"PDF RGB renderizado: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Falha na renderização CairoSVG: {e}")
            raise

    def render_png(
        self,
        svg_content: bytes,
        output_path: str,
        width: int = None,
        height: int = None,
        dpi: int = 96
    ) -> bool:
        """
        Renderiza SVG para PNG (thumbnails, previews).
        """
        if not HAS_CAIRO:
            raise ImportError("CairoSVG não instalado.")
        
        try:
            kwargs = {"bytestring": svg_content, "write_to": output_path, "dpi": dpi}
            if width:
                kwargs["output_width"] = width
            if height:
                kwargs["output_height"] = height
            
            cairosvg.svg2png(**kwargs)
            return True
            
        except Exception as e:
            logger.error(f"Falha ao renderizar PNG: {e}")
            raise

    # ==========================================================================
    # CONVERSÃO CMYK (GHOSTSCRIPT)
    # ==========================================================================

    def convert_to_cmyk(
        self, 
        input_pdf: str, 
        output_pdf: str,
        preserve_black: bool = True,
        pdf_standard: str = "pdfx1a"
    ) -> bool:
        """
        Passo 2: Converte PDF RGB para CMYK via Ghostscript.
        
        Conforme Vol. II, Cap. 7.3:
        - Usa perfil ICC FOGRA39 para fidelidade de cores
        - Preserva preto puro (K=100%) para texto nítido
        - Suporte a PDF/X-1a para offset
        
        Args:
            input_pdf: PDF em RGB
            output_pdf: PDF de saída em CMYK
            preserve_black: Mantém texto preto apenas no canal K
            pdf_standard: "pdfx1a" ou "pdfx4"
        """
        if not self.gs_path:
            raise RuntimeError("Ghostscript não disponível para conversão CMYK.")
        
        if not os.path.exists(input_pdf):
            raise FileNotFoundError(f"PDF de entrada não existe: {input_pdf}")

        # Construção do comando Ghostscript
        cmd = [
            self.gs_path,
            "-o", output_pdf,
            "-sDEVICE=pdfwrite",
            "-dPDFSETTINGS=/prepress",  # Alta qualidade
            "-dProcessColorModel=/DeviceCMYK",
            "-sColorConversionStrategy=CMYK",
        ]
        
        # Perfil ICC se disponível
        if self.icc_profile.exists():
            cmd.append(f"-sOutputICCProfile={self.icc_profile}")
        
        # True Black Preservation (Vol. II, Cap. 7.4)
        if preserve_black:
            cmd.extend([
                "-dKPreserve=2",  # Mantém K puro
                "-dOverprint=/enable",
            ])
        
        # PDF/X padrão
        if pdf_standard == "pdfx1a":
            cmd.extend([
                "-dPDFX=true",
                "-dCompatibilityLevel=1.4",
            ])
        
        cmd.extend([
            "-dNOPAUSE",
            "-dBATCH",
            input_pdf
        ])

        try:
            startupinfo = None
            if os.name == 'nt':
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            
            result = subprocess.run(
                cmd,
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                startupinfo=startupinfo,
                timeout=60
            )
            logger.info(f"Conversão CMYK concluída: {output_pdf}")
            return True
            
        except subprocess.TimeoutExpired:
            logger.error("Timeout na conversão CMYK (>60s)")
            raise RuntimeError("Ghostscript timeout")
        except subprocess.CalledProcessError as e:
            logger.error(f"Erro no Ghostscript (Exit {e.returncode}): {e.stderr}")
            raise RuntimeError(f"Falha na conversão CMYK: {e.stderr}")

    # ==========================================================================
    # PDF MULTIPÁGINAS (Vol. II, Cap. 1.3)
    # ==========================================================================

    def merge_pdfs(
        self, 
        pdf_paths: List[str], 
        output_path: str
    ) -> bool:
        """
        Combina múltiplos PDFs em um único arquivo multipáginas.
        
        Conforme Vol. II, Cap. 1.3 - Saída única para gráfica.
        """
        if not HAS_PYPDF:
            raise ImportError("PyPDF2 não instalado para merge de PDFs.")
        
        if not pdf_paths:
            raise ValueError("Lista de PDFs vazia.")
        
        try:
            merger = PdfMerger()
            
            for pdf_path in pdf_paths:
                if os.path.exists(pdf_path):
                    merger.append(pdf_path)
                else:
                    logger.warning(f"PDF não encontrado, ignorando: {pdf_path}")
            
            merger.write(output_path)
            merger.close()
            
            logger.info(f"PDFs combinados ({len(pdf_paths)} páginas): {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Falha ao combinar PDFs: {e}")
            raise

    # ==========================================================================
    # PIPELINE COMPLETO (Batch Processing)
    # ==========================================================================

    def render_batch(
        self,
        svg_contents: List[bytes],
        output_path: str,
        use_cmyk: bool = True,
        cleanup_temp: bool = True
    ) -> str:
        """
        Pipeline completo: Renderiza lista de SVGs e combina em PDF único.
        
        Args:
            svg_contents: Lista de SVGs como bytes
            output_path: Caminho do PDF final
            use_cmyk: Se True, converte para CMYK
            cleanup_temp: Se True, remove arquivos intermediários
            
        Returns:
            Caminho do PDF gerado
        """
        temp_pdfs = []
        
        try:
            for i, svg_content in enumerate(svg_contents):
                # 1. Renderiza SVG -> PDF RGB
                temp_rgb = str(self.temp_dir / f"page_{i:04d}_rgb.pdf")
                self.render_pdf(svg_content, temp_rgb)
                
                if use_cmyk and self.gs_path:
                    # 2. Converte para CMYK
                    temp_cmyk = str(self.temp_dir / f"page_{i:04d}_cmyk.pdf")
                    self.convert_to_cmyk(temp_rgb, temp_cmyk)
                    temp_pdfs.append(temp_cmyk)
                    
                    if cleanup_temp:
                        os.remove(temp_rgb)
                else:
                    temp_pdfs.append(temp_rgb)
            
            # 3. Combina em PDF único
            if len(temp_pdfs) > 1:
                self.merge_pdfs(temp_pdfs, output_path)
            else:
                # Apenas um PDF - copia/renomeia
                import shutil
                shutil.move(temp_pdfs[0], output_path)
            
            logger.info(f"Batch renderizado: {output_path} ({len(svg_contents)} páginas)")
            return output_path
            
        finally:
            # Cleanup
            if cleanup_temp:
                for pdf in temp_pdfs:
                    if os.path.exists(pdf) and pdf != output_path:
                        try:
                            os.remove(pdf)
                        except:
                            pass

    # ==========================================================================
    # MARCAS DE CORTE E SANGRIA (Vol. II, Cap. 6.2)
    # ==========================================================================

    def add_crop_marks(
        self,
        svg_content: bytes,
        bleed_mm: float = 3.0,
        mark_length_mm: float = 5.0
    ) -> bytes:
        """
        Adiciona marcas de corte e área de sangria ao SVG.
        
        Conforme Vol. II, Cap. 6.2 - Padrão gráfico de acabamento.
        
        Args:
            svg_content: SVG original
            bleed_mm: Tamanho da sangria em mm
            mark_length_mm: Comprimento das marcas de corte
        
        Returns:
            SVG modificado com marcas de corte
        """
        from lxml import etree
        
        root = etree.fromstring(svg_content)
        
        # Obtém dimensões
        width = float(root.get('width', '210').replace('mm', '').replace('px', ''))
        height = float(root.get('height', '297').replace('mm', '').replace('px', ''))
        
        # Converte mm para unidades do documento (assumindo 96dpi = 3.78 px/mm)
        scale = 3.78
        bleed = bleed_mm * scale
        mark_len = mark_length_mm * scale
        
        # Grupo para marcas de corte
        marks_group = etree.SubElement(root, '{http://www.w3.org/2000/svg}g')
        marks_group.set('id', 'CROP_MARKS')
        marks_group.set('style', 'stroke:#000000;stroke-width:0.25;fill:none')
        
        # Posições das marcas (4 cantos)
        corners = [
            (0, 0),  # Superior esquerdo
            (width, 0),  # Superior direito
            (0, height),  # Inferior esquerdo
            (width, height)  # Inferior direito
        ]
        
        for cx, cy in corners:
            # Marca horizontal
            h_line = etree.SubElement(marks_group, '{http://www.w3.org/2000/svg}line')
            if cx == 0:
                h_line.set('x1', str(-bleed - mark_len))
                h_line.set('x2', str(-bleed))
            else:
                h_line.set('x1', str(cx + bleed))
                h_line.set('x2', str(cx + bleed + mark_len))
            h_line.set('y1', str(cy))
            h_line.set('y2', str(cy))
            
            # Marca vertical
            v_line = etree.SubElement(marks_group, '{http://www.w3.org/2000/svg}line')
            v_line.set('x1', str(cx))
            v_line.set('x2', str(cx))
            if cy == 0:
                v_line.set('y1', str(-bleed - mark_len))
                v_line.set('y2', str(-bleed))
            else:
                v_line.set('y1', str(cy + bleed))
                v_line.set('y2', str(cy + bleed + mark_len))
        
        return etree.tostring(root, encoding='utf-8')

    # ==========================================================================
    # UTILITÁRIOS
    # ==========================================================================

    def get_pdf_info(self, pdf_path: str) -> dict:
        """Retorna informações sobre um PDF."""
        if not HAS_PYPDF:
            return {"error": "PyPDF2 não instalado"}
        
        try:
            reader = PdfReader(pdf_path)
            info = reader.metadata or {}
            
            return {
                "pages": len(reader.pages),
                "title": info.get('/Title', ''),
                "author": info.get('/Author', ''),
                "creator": info.get('/Creator', ''),
                "size_bytes": os.path.getsize(pdf_path)
            }
        except Exception as e:
            return {"error": str(e)}

    def cleanup_temp_files(self):
        """Remove todos os arquivos temporários."""
        if self.temp_dir.exists():
            import shutil
            for item in self.temp_dir.iterdir():
                if item.is_file():
                    try:
                        item.unlink()
                    except:
                        pass
            logger.info("Arquivos temporários removidos.")

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
            # CRÍTICO (#101 Industrial Robustness): Transparency Flattener
            # PDF/X-1a NÃO suporta transparência nativa!
            # Sem estas flags, PNGs com alpha ou drop-shadows ficam:
            # - Pixelados (rasterização pobre)
            # - Pretos/brancos (canal alpha ignorado)
            # - Causam rejeição pela gráfica
            cmd.extend([
                "-dPDFX=true",
                "-dCompatibilityLevel=1.3",    # PDF 1.3 força achatamento
                "-dHaveTransparency=false",    # CRÍTICO: Achata transparências
                "-dAutoFilterColorImages=false",
                "-dColorImageFilter=/FlateEncode",  # Compressão sem perdas
            ])
        elif pdf_standard == "pdfx4":
            # PDF/X-4 SUPORTA transparência nativa (impressoras modernas)
            cmd.extend([
                "-dPDFX=true",
                "-dCompatibilityLevel=1.6",    # PDF 1.6+ para X-4
                "-dHaveTransparency=true",     # Preserva transparências
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
        # Import MemoryContext for garbage collection after heavy operations
        try:
            from src.core.memory import MemoryContext
            memory_ctx = MemoryContext("BatchRender")
        except ImportError:
            memory_ctx = None
        
        temp_pdfs = []
        
        try:
            if memory_ctx:
                memory_ctx.__enter__()
            
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
            
            # Memory cleanup after heavy operation
            if memory_ctx:
                memory_ctx.__exit__(None, None, None)

    async def batch_render_to_pdf(
        self,
        frames: List[bytes],
        output_path: str,
        dpi: int = 300,
        color_mode: str = "auto"
    ) -> str:
        """
        Wrapper assíncrono para render_batch.
        Roda em thread para não bloquear a UI.
        
        Args:
            frames: Lista de SVGs renderizados
            output_path: Caminho do PDF de saída
            dpi: Resolução (300 padrão)
            color_mode: "auto", "rgb" ou "cmyk"
            
        Returns:
            Caminho do PDF gerado
        """
        import asyncio
        from concurrent.futures import ThreadPoolExecutor
        
        use_cmyk = color_mode == "cmyk" or (color_mode == "auto" and self.gs_path)
        
        loop = asyncio.get_event_loop()
        with ThreadPoolExecutor() as pool:
            result = await loop.run_in_executor(
                pool,
                lambda: self.render_batch(frames, output_path, use_cmyk=use_cmyk)
            )
        
        return result

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

    # ==========================================================================
    # #53: COLOR BARS - Barras de Controle de Cor
    # ==========================================================================
    
    def add_color_bars(
        self,
        svg_content: bytes,
        bar_width_mm: float = 5.0,
        bar_height_mm: float = 10.0
    ) -> bytes:
        """
        Adiciona barras de controle CMYK para calibração de impressora (#53).
        
        Cria 4 retângulos com C=100%, M=100%, Y=100%, K=100% 
        fora da área de sangria para verificação de densidade.
        
        Args:
            svg_content: SVG original
            bar_width_mm: Largura de cada barra
            bar_height_mm: Altura das barras
        """
        from lxml import etree
        
        root = etree.fromstring(svg_content)
        
        # Obtém dimensões
        width = float(root.get('width', '210').replace('mm', '').replace('px', ''))
        height = float(root.get('height', '297').replace('mm', '').replace('px', ''))
        
        # Escala (96dpi = 3.78 px/mm)
        scale = 3.78
        bar_w = bar_width_mm * scale
        bar_h = bar_height_mm * scale
        offset = 15 * scale  # 15mm da borda
        
        # Cores CMYK em RGB (aproximação para SVG)
        colors = [
            ("#00FFFF", "CYAN"),     # Cyan
            ("#FF00FF", "MAGENTA"),  # Magenta
            ("#FFFF00", "YELLOW"),   # Yellow
            ("#000000", "BLACK"),    # Black (K)
        ]
        
        # Grupo para barras
        bars_group = etree.SubElement(root, '{http://www.w3.org/2000/svg}g')
        bars_group.set('id', 'COLOR_BARS')
        
        # Posiciona barras no topo, fora da área de sangria
        for i, (color, name) in enumerate(colors):
            rect = etree.SubElement(bars_group, '{http://www.w3.org/2000/svg}rect')
            rect.set('x', str(offset + (i * (bar_w + 2))))
            rect.set('y', str(-offset - bar_h))  # Acima da página
            rect.set('width', str(bar_w))
            rect.set('height', str(bar_h))
            rect.set('fill', color)
            rect.set('id', f'COLOR_BAR_{name}')
        
        return etree.tostring(root, encoding='utf-8')

    # ==========================================================================
    # #54: REGISTRATION COLOR - Marcas de Registro
    # ==========================================================================
    
    def add_registration_marks(
        self,
        svg_content: bytes,
        mark_size_mm: float = 5.0
    ) -> bytes:
        """
        Adiciona marcas de registro para alinhamento de chapas (#54).
        
        Usa "cor de registro" que imprime em todas as chapas CMYK.
        Em SVG usamos #000000, mas no PDF/X isso é convertido para
        C=100% M=100% Y=100% K=100% pelo perfil.
        
        Args:
            svg_content: SVG original
            mark_size_mm: Tamanho das marcas de registro
        """
        from lxml import etree
        
        root = etree.fromstring(svg_content)
        
        width = float(root.get('width', '210').replace('mm', '').replace('px', ''))
        height = float(root.get('height', '297').replace('mm', '').replace('px', ''))
        
        scale = 3.78
        mark_size = mark_size_mm * scale
        offset = 12 * scale
        
        # Grupo para marcas de registro
        reg_group = etree.SubElement(root, '{http://www.w3.org/2000/svg}g')
        reg_group.set('id', 'REGISTRATION_MARKS')
        # "Cor de registro" - imprime em todas as chapas
        reg_group.set('style', 'stroke:#000000;stroke-width:0.5;fill:none')
        
        # Marcas nos 4 lados (círculo + cruz)
        positions = [
            (width / 2, -offset),           # Topo centro
            (width / 2, height + offset),   # Base centro
            (-offset, height / 2),          # Esquerda centro
            (width + offset, height / 2),   # Direita centro
        ]
        
        for x, y in positions:
            # Círculo externo
            circle = etree.SubElement(reg_group, '{http://www.w3.org/2000/svg}circle')
            circle.set('cx', str(x))
            circle.set('cy', str(y))
            circle.set('r', str(mark_size / 2))
            
            # Cruz central (horizontal)
            h_line = etree.SubElement(reg_group, '{http://www.w3.org/2000/svg}line')
            h_line.set('x1', str(x - mark_size))
            h_line.set('x2', str(x + mark_size))
            h_line.set('y1', str(y))
            h_line.set('y2', str(y))
            
            # Cruz central (vertical)
            v_line = etree.SubElement(reg_group, '{http://www.w3.org/2000/svg}line')
            v_line.set('x1', str(x))
            v_line.set('x2', str(x))
            v_line.set('y1', str(y - mark_size))
            v_line.set('y2', str(y + mark_size))
        
        return etree.tostring(root, encoding='utf-8')

    # ==========================================================================
    # #55: SLUG AREA - Área de Informações Técnicas
    # ==========================================================================
    
    def add_slug_area(
        self,
        svg_content: bytes,
        job_name: str = "",
        date_str: str = "",
        page_info: str = ""
    ) -> bytes:
        """
        Adiciona área de slug com informações técnicas (#55).
        
        O slug fica fora da área de sangria e contém:
        - Nome do trabalho
        - Data de criação
        - Informação de página
        - Marca "AutoTabloide AI"
        
        Args:
            svg_content: SVG original
            job_name: Nome do trabalho/projeto
            date_str: Data de criação
            page_info: Informação de página (ex: "1/4")
        """
        from lxml import etree
        from datetime import datetime
        
        root = etree.fromstring(svg_content)
        
        width = float(root.get('width', '210').replace('mm', '').replace('px', ''))
        height = float(root.get('height', '297').replace('mm', '').replace('px', ''))
        
        scale = 3.78
        slug_offset = 20 * scale  # 20mm abaixo da área de sangria
        
        # Grupo para slug
        slug_group = etree.SubElement(root, '{http://www.w3.org/2000/svg}g')
        slug_group.set('id', 'SLUG_AREA')
        
        # Texto de informação
        if not date_str:
            date_str = datetime.now().strftime("%Y-%m-%d %H:%M")
        
        info_text = f"{job_name} | {date_str} | {page_info} | AutoTabloide AI"
        
        text_elem = etree.SubElement(slug_group, '{http://www.w3.org/2000/svg}text')
        text_elem.set('x', str(width / 2))
        text_elem.set('y', str(height + slug_offset))
        text_elem.set('text-anchor', 'middle')
        text_elem.set('style', 'font-family:sans-serif;font-size:8px;fill:#666666')
        text_elem.text = info_text
        
        return etree.tostring(root, encoding='utf-8')

    # ==========================================================================
    # INDUSTRIAL ROBUSTNESS: UNIFIED PROFESSIONAL PRINT PIPELINE
    # ==========================================================================
    
    def render_professional_pdf(
        self,
        svg_contents: List[bytes],
        output_path: str,
        job_name: str = "Tabloide",
        add_print_marks: bool = True,
        add_bleed: bool = True,
        use_cmyk: bool = True
    ) -> str:
        """
        Pipeline completo para impressão profissional offset.
        
        INTEGRA TODOS OS ITENS INDUSTRIAL:
        - #52: Sangria (bleed)
        - #53: Color Bars
        - #54: Registration Marks
        - #55: Slug Area
        - #101: Transparency Flattening
        
        Args:
            svg_contents: Lista de SVGs como bytes
            output_path: Caminho do PDF final
            job_name: Nome do trabalho para slug
            add_print_marks: Se True, adiciona color bars, registration, slug
            add_bleed: Se True, expande área de sangria
            use_cmyk: Se True, converte para CMYK/FOGRA39
            
        Returns:
            Caminho do PDF gerado
        """
        from datetime import datetime
        
        processed_svgs = []
        total = len(svg_contents)
        
        for i, svg in enumerate(svg_contents):
            processed = svg
            
            if add_print_marks:
                # #53: Color Bars
                processed = self.add_color_bars(processed)
                
                # #54: Registration Marks
                processed = self.add_registration_marks(processed)
                
                # #55: Slug Area
                processed = self.add_slug_area(
                    processed,
                    job_name=job_name,
                    date_str=datetime.now().strftime("%Y-%m-%d %H:%M"),
                    page_info=f"{i+1}/{total}"
                )
            
            processed_svgs.append(processed)
        
        # Renderiza com pipeline CMYK (#101 Transparency)
        return self.render_batch(
            processed_svgs,
            output_path,
            use_cmyk=use_cmyk
        )


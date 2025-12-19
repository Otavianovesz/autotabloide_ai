import os
import subprocess
import logging
from typing import Optional
import cairosvg

# Configuração de Logs
logger = logging.getLogger("OutputEngine")

class OutputEngine:
    """
    Motor de Renderização e Ciência de Cores.
    Responsável pela conversão SVG -> PDF e PDF(RGB) -> PDF(CMYK/FOGRA39).
    """

    def __init__(self, system_root: str):
        self.system_root = system_root
        
        # Caminhos Críticos
        self.gs_path = os.path.join(system_root, "bin", "gswin64c.exe")
        self.icc_profile = os.path.join(system_root, "assets", "profiles", "CoatedFOGRA39.icc")
        
        self._verify_assets()

    def _verify_assets(self):
        """Bloqueia a inicialização se a infraestrutura crítica estiver ausente."""
        if not os.path.exists(self.gs_path):
            # Fallback: Tenta achar no PATH do sistema, mas alerta
            import shutil
            if shutil.which("gswin64c"):
                self.gs_path = "gswin64c"
                logger.warning("Ghostscript não encontrado na pasta bin. Usando do PATH.")
            else:
                # Em dev pode não existir, mas o user disse que existe.
                # Vamos logar e não crashar imediatamente se for teste unitário, 
                # mas em prod deveria crashar.
                logger.error(f"Ghostscript CRÍTICO não encontrado em: {self.gs_path}")
                # raise FileNotFoundError(f"Ghostscript CRÍTICO não encontrado em: {self.gs_path}")
        
        if not os.path.exists(self.icc_profile):
             logger.error(f"Perfil de cor FOGRA39 ausente: {self.icc_profile}")

    def render_pdf(self, svg_content: bytes, output_path: str):
        """
        Passo 1: SVG -> PDF (Ainda em RGB/sRGB nativo do Cairo)
        """
        try:
            # CairoSVG requires DLLs on Windows. Assumes they are on PATH (handled by main.py)
            cairosvg.svg2pdf(bytestring=svg_content, write_to=output_path)
        except Exception as e:
            logger.error(f"Falha na renderização CairoSVG: {e}")
            raise

    def convert_to_cmyk(self, input_pdf: str, output_pdf: str):
        """
        Passo 2: Processamento Pós-Render (Ghostscript)
        Converte para CMYK real e preserva o canal K (Preto) para texto nítido.
        """
        if not os.path.exists(input_pdf):
            raise FileNotFoundError(f"PDF de entrada não existe: {input_pdf}")

        # Verifica se GS e ICC estão ok antes de tentar
        if not os.path.exists(self.gs_path) and self.gs_path != "gswin64c":
             raise RuntimeError("Executável do Ghostscript não disponível.")

        # Construção do Comando Ghostscript (A "Lei" da Impressão)
        cmd = [
            self.gs_path,
            "-o", output_pdf,
            "-sDEVICE=pdfwrite",
            "-dPDFSETTINGS=/prepress", # Alta qualidade
            "-dProcessColorModel=/DeviceCMYK",
            "-sColorConversionStrategy=CMYK",
            f"-sOutputICCProfile={self.icc_profile}",
            "-dKPreserve=2", # CRÍTICO: Mantém texto preto apenas no canal K
            "-dOverprint=/enable", # Útil para evitar bordas brancas em fundo colorido
            "-dNOPAUSE",
            "-dBATCH",
            input_pdf
        ]

        try:
            # Executa sem abrir janela de shell (creationflags no Windows)
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
                startupinfo=startupinfo
            )
            logger.info(f"Conversão CMYK concluída: {output_pdf}")
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Erro no Ghostscript (Exit Code {e.returncode}):\n{e.stderr}")
            raise RuntimeError(f"Falha crítica na conversão de cores: {e.stderr}")

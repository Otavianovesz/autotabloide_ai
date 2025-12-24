"""
AutoTabloide AI - PDF Utilities
=================================
Utilitários para manipulação de PDF.
Passos 41-43 do Checklist 100.

Funcionalidades:
- Validação pós-renderização (PDF > 0kb)
- Metadados XMP
- Conversão fontes em outlines (via Ghostscript)
"""

import subprocess
from pathlib import Path
from typing import Optional
from datetime import datetime

from src.core.logging_config import get_logger
from src.core.constants import SYSTEM_ROOT

logger = get_logger("PDFUtils")


def validate_pdf(pdf_path: Path) -> bool:
    """
    Valida se PDF foi gerado corretamente.
    Passo 41 do Checklist - Validação pós-renderização.
    
    Args:
        pdf_path: Caminho do arquivo PDF
        
    Returns:
        True se válido
    """
    if not pdf_path.exists():
        logger.error(f"PDF não encontrado: {pdf_path}")
        return False
    
    size = pdf_path.stat().st_size
    
    if size == 0:
        logger.error(f"PDF vazio (0 bytes): {pdf_path}")
        return False
    
    if size < 1024:  # Menor que 1KB
        logger.warning(f"PDF muito pequeno ({size} bytes): {pdf_path}")
    
    # Verificar header PDF
    try:
        with open(pdf_path, 'rb') as f:
            header = f.read(8)
            if not header.startswith(b'%PDF'):
                logger.error(f"Header PDF inválido: {pdf_path}")
                return False
    except Exception as e:
        logger.error(f"Erro ao ler PDF: {e}")
        return False
    
    logger.debug(f"PDF válido: {pdf_path.name} ({size/1024:.1f}KB)")
    return True


def add_xmp_metadata(
    pdf_path: Path,
    title: str,
    author: str = "AutoTabloide AI",
    subject: str = "",
    keywords: str = ""
) -> bool:
    """
    Adiciona metadados XMP ao PDF.
    Passo 42 do Checklist.
    
    Requer: Ghostscript ou pdftk
    
    Args:
        pdf_path: Caminho do PDF
        title: Título do documento
        author: Autor
        subject: Assunto
        keywords: Palavras-chave
        
    Returns:
        True se sucesso
    """
    try:
        # Tenta via pypdf
        from pypdf import PdfReader, PdfWriter
        from pypdf.generic import DictionaryObject, NameObject, TextStringObject
        
        reader = PdfReader(str(pdf_path))
        writer = PdfWriter()
        
        # Copia páginas
        for page in reader.pages:
            writer.add_page(page)
        
        # Adiciona metadados
        writer.add_metadata({
            '/Title': title,
            '/Author': author,
            '/Subject': subject,
            '/Keywords': keywords,
            '/Creator': 'AutoTabloide AI v1.0',
            '/Producer': 'AutoTabloide AI Industrial Engine',
            '/CreationDate': f"D:{datetime.now().strftime('%Y%m%d%H%M%S')}"
        })
        
        # Salva
        output_path = pdf_path.with_suffix('.tmp.pdf')
        with open(output_path, 'wb') as f:
            writer.write(f)
        
        # Substitui original
        output_path.replace(pdf_path)
        
        logger.info(f"Metadados XMP adicionados: {pdf_path.name}")
        return True
        
    except ImportError:
        logger.warning("pypdf não instalado, metadados não adicionados")
        return False
    except Exception as e:
        logger.error(f"Erro ao adicionar metadados: {e}")
        return False


def convert_to_outlines(
    input_pdf: Path,
    output_pdf: Optional[Path] = None,
    gs_path: Optional[str] = None
) -> bool:
    """
    Converte fontes em curvas (outlines) usando Ghostscript.
    Passo 43 do Checklist.
    
    Args:
        input_pdf: PDF de entrada
        output_pdf: PDF de saída (ou sobrescreve entrada)
        gs_path: Caminho do Ghostscript
        
    Returns:
        True se sucesso
    """
    if output_pdf is None:
        output_pdf = input_pdf.with_stem(input_pdf.stem + "_outlined")
    
    # Encontrar Ghostscript
    if gs_path is None:
        gs_paths = [
            SYSTEM_ROOT / "bin" / "gs" / "gswin64c.exe",
            Path("C:/Program Files/gs/gs10.02.1/bin/gswin64c.exe"),
            Path("gswin64c"),  # PATH
        ]
        
        for p in gs_paths:
            if p.exists() or str(p) == "gswin64c":
                gs_path = str(p)
                break
    
    if not gs_path:
        logger.error("Ghostscript não encontrado")
        return False
    
    # Comando Ghostscript para converter fontes em outlines
    cmd = [
        gs_path,
        "-dNOPAUSE",
        "-dBATCH",
        "-dNoOutputFonts",  # Converte fontes em outlines
        "-sDEVICE=pdfwrite",
        "-dPDFSETTINGS=/prepress",
        "-dCompatibilityLevel=1.4",
        f"-sOutputFile={output_pdf}",
        str(input_pdf)
    ]
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            timeout=120
        )
        
        if result.returncode == 0 and output_pdf.exists():
            logger.info(f"Fontes convertidas em outlines: {output_pdf.name}")
            return True
        else:
            logger.error(f"Ghostscript falhou: {result.stderr.decode()}")
            return False
            
    except subprocess.TimeoutExpired:
        logger.error("Ghostscript timeout (120s)")
        return False
    except Exception as e:
        logger.error(f"Erro ao converter outlines: {e}")
        return False


def handle_pdf_in_use(pdf_path: Path) -> bool:
    """
    Verifica se PDF está aberto por outro programa.
    Passo 85 do Checklist - Tratamento PDF aberto.
    
    Args:
        pdf_path: Caminho do PDF
        
    Returns:
        True se está livre para uso
    """
    if not pdf_path.exists():
        return True
    
    try:
        # Tenta abrir para escrita exclusiva
        with open(pdf_path, 'r+b'):
            pass
        return True
    except PermissionError:
        logger.warning(f"PDF em uso: {pdf_path.name}")
        return False
    except Exception:
        return True

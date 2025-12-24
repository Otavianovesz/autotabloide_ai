"""
AutoTabloide AI - Barcode Generator
=====================================
Geração de códigos EAN-13 vetoriais.
Passo 40, 87 do Checklist 100.

Funcionalidades:
- EAN-13 vetorial (SVG)
- Validação de dígito verificador
- Cálculo automático de checksum
"""

import re
from typing import Optional, Tuple

# ==============================================================================
# CODIFICAÇÃO EAN-13
# ==============================================================================

# Padrões de codificação L, G e R para dígitos 0-9
L_CODES = [
    "0001101", "0011001", "0010011", "0111101", "0100011",
    "0110001", "0101111", "0111011", "0110111", "0001011"
]

G_CODES = [
    "0100111", "0110011", "0011011", "0100001", "0011101",
    "0111001", "0000101", "0010001", "0001001", "0010111"
]

R_CODES = [
    "1110010", "1100110", "1101100", "1000010", "1011100",
    "1001110", "1010000", "1000100", "1001000", "1110100"
]

# Padrões de paridade para o primeiro dígito
FIRST_DIGIT_PATTERNS = [
    "LLLLLL", "LLGLGG", "LLGGLG", "LLGGGL", "LGLLGG",
    "LGGLLG", "LGGGLL", "LGLGLG", "LGLGGL", "LGGLGL"
]


def calculate_ean13_checksum(digits_12: str) -> int:
    """
    Calcula dígito verificador do EAN-13.
    Passo 87 - Validação de dígito.
    
    Args:
        digits_12: Primeiros 12 dígitos do EAN
        
    Returns:
        Dígito verificador (0-9)
    """
    if len(digits_12) != 12 or not digits_12.isdigit():
        raise ValueError("EAN deve ter exatamente 12 dígitos")
    
    total = 0
    for i, digit in enumerate(digits_12):
        value = int(digit)
        if i % 2 == 0:
            total += value
        else:
            total += value * 3
    
    checksum = (10 - (total % 10)) % 10
    return checksum


def validate_ean13(ean: str) -> bool:
    """
    Valida EAN-13 completo.
    
    Args:
        ean: Código EAN-13 (13 dígitos)
        
    Returns:
        True se válido
    """
    if len(ean) != 13 or not ean.isdigit():
        return False
    
    expected_checksum = calculate_ean13_checksum(ean[:12])
    return int(ean[12]) == expected_checksum


def normalize_ean(code: str) -> Optional[str]:
    """
    Normaliza código de barras para EAN-13.
    Adiciona zeros à esquerda e calcula checksum se necessário.
    
    Args:
        code: Código (pode ter 12 ou 13 dígitos)
        
    Returns:
        EAN-13 válido ou None se inválido
    """
    # Remove caracteres não numéricos
    digits = re.sub(r'\D', '', str(code))
    
    if len(digits) < 12:
        # Adiciona zeros à esquerda
        digits = digits.zfill(12)
    
    if len(digits) == 12:
        # Calcula checksum
        checksum = calculate_ean13_checksum(digits)
        return digits + str(checksum)
    
    if len(digits) == 13:
        if validate_ean13(digits):
            return digits
        else:
            # Recalcula checksum
            return digits[:12] + str(calculate_ean13_checksum(digits[:12]))
    
    return None


def generate_ean13_svg(
    ean: str,
    width: float = 100,
    height: float = 50,
    bar_color: str = "black",
    include_text: bool = True
) -> str:
    """
    Gera código de barras EAN-13 como SVG vetorial.
    Passo 40 do Checklist.
    
    Args:
        ean: Código EAN-13 validado
        width: Largura total em pixels
        height: Altura total em pixels
        bar_color: Cor das barras
        include_text: Incluir números abaixo?
        
    Returns:
        String SVG do código de barras
    """
    # Normaliza e valida
    ean = normalize_ean(ean)
    if not ean:
        raise ValueError(f"Código de barras inválido: {ean}")
    
    # Gerar padrão de barras
    bars = _encode_ean13(ean)
    
    # Calcular dimensões
    bar_width = width / len(bars)
    text_height = height * 0.2 if include_text else 0
    bar_height = height - text_height
    
    # Construir SVG
    svg_parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">'
    ]
    
    # Desenhar barras
    x = 0
    for char in bars:
        if char == "1":
            svg_parts.append(
                f'<rect x="{x}" y="0" width="{bar_width}" height="{bar_height}" fill="{bar_color}"/>'
            )
        x += bar_width
    
    # Adicionar texto
    if include_text:
        font_size = text_height * 0.8
        text_y = height - (text_height * 0.2)
        
        # Formatar: X XXXXXX XXXXXX
        formatted = f"{ean[0]} {ean[1:7]} {ean[7:13]}"
        
        svg_parts.append(
            f'<text x="{width/2}" y="{text_y}" font-family="monospace" '
            f'font-size="{font_size}" text-anchor="middle" fill="{bar_color}">{formatted}</text>'
        )
    
    svg_parts.append('</svg>')
    
    return '\n'.join(svg_parts)


def _encode_ean13(ean: str) -> str:
    """
    Codifica EAN-13 em padrão de barras.
    
    Returns:
        String de 0s e 1s representando barras
    """
    if len(ean) != 13:
        raise ValueError("EAN deve ter 13 dígitos")
    
    first_digit = int(ean[0])
    parity_pattern = FIRST_DIGIT_PATTERNS[first_digit]
    
    # Start guard: 101
    bars = "101"
    
    # Primeiros 6 dígitos (após o primeiro)
    for i, digit in enumerate(ean[1:7]):
        d = int(digit)
        if parity_pattern[i] == "L":
            bars += L_CODES[d]
        else:
            bars += G_CODES[d]
    
    # Middle guard: 01010
    bars += "01010"
    
    # Últimos 6 dígitos
    for digit in ean[7:]:
        d = int(digit)
        bars += R_CODES[d]
    
    # End guard: 101
    bars += "101"
    
    return bars


# ==============================================================================
# UTILITÁRIOS PARA VECTOR ENGINE
# ==============================================================================

def inject_barcode_svg(
    parent_element,
    ean: str,
    x: float,
    y: float,
    width: float,
    height: float
) -> bool:
    """
    Injeta código de barras em elemento SVG existente.
    
    Args:
        parent_element: Elemento lxml pai
        ean: Código EAN
        x, y: Posição
        width, height: Dimensões
        
    Returns:
        True se injetado com sucesso
    """
    from lxml import etree
    
    try:
        svg_content = generate_ean13_svg(ean, width, height)
        
        # Parse e ajusta posição
        barcode_elem = etree.fromstring(svg_content.encode())
        
        # Cria grupo com transformação
        group = etree.SubElement(parent_element, 'g')
        group.set('transform', f'translate({x},{y})')
        
        # Copia elementos do barcode para o grupo
        for child in barcode_elem:
            group.append(child)
        
        return True
        
    except Exception as e:
        import logging
        logging.warning(f"Erro ao injetar barcode: {e}")
        return False

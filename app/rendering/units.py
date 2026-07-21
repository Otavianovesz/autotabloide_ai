"""
Conversões de unidade (o coração da fidelidade)
===============================================
O layout é medido em **milímetros** (tamanho físico real). Só convertemos para
pixels na composição, usando o DPI. Assim o mesmo layout serve para qualquer
resolução sem "escorregar".

  * 1 polegada = 25,4 mm
  * 1 ponto tipográfico (pt) = 1/72 de polegada
"""

from __future__ import annotations

MM_POR_POLEGADA = 25.4
PT_POR_POLEGADA = 72.0


def mm_para_px(mm: float, dpi: int) -> float:
    """Milímetros -> pixels, dado o DPI."""
    return mm / MM_POR_POLEGADA * dpi


def px_para_mm(px: float, dpi: int) -> float:
    """Pixels -> milímetros, dado o DPI."""
    return px * MM_POR_POLEGADA / dpi


def pt_para_px(pt: float, dpi: int) -> float:
    """Pontos de fonte -> pixels, dado o DPI."""
    return pt / PT_POR_POLEGADA * dpi


def px_para_pt(px: float, dpi: int) -> float:
    """Pixels -> pontos de fonte, dado o DPI."""
    return px * PT_POR_POLEGADA / dpi

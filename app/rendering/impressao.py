"""
Impressão direta na fila do Windows (R-112 da Fase 11)
======================================================
Manda o cartaz/lote direto para a impressora (QPrinter), respeitando o
tamanho físico (mm) e a orientação — o que sai na bandeja bate com a prévia.
Sem exportar PDF antes.

A fidelidade de mm vem de ``QPageSize`` em milímetros; a orientação sai de
largura vs. altura do layout. As imagens já vêm compostas por ``compor_pagina``
no DPI do layout, então cada página imprime no tamanho certo.
"""

from __future__ import annotations

from PIL import Image


def tamanho_pagina_mm(layout) -> tuple[float, float]:
    """O tamanho físico (largura_mm, altura_mm) que a impressora deve usar."""
    return (float(layout.largura_mm), float(layout.altura_mm))


def configurar_impressora(printer, layout):
    """Ajusta o QPrinter ao tamanho físico (mm) e à orientação do layout.

    O Qt guarda o ``QPageSize`` sempre em RETRATO e trata a orientação à parte
    (um ``QPageSize(297×210)`` seria normalizado para 210×297). Por isso o
    tamanho é montado no retrato normalizado (menor×maior) e a orientação vem
    de largura vs. altura — via ``QPageLayout``, que aplica os dois de uma vez.
    ``setFullPage`` garante que o mm pedido é o da folha inteira."""
    from PySide6.QtCore import QMarginsF, QSizeF
    from PySide6.QtGui import QPageLayout, QPageSize

    larg_mm, alt_mm = tamanho_pagina_mm(layout)
    paisagem = larg_mm > alt_mm
    menor, maior = (min(larg_mm, alt_mm), max(larg_mm, alt_mm))
    tam = QPageSize(QSizeF(menor, maior), QPageSize.Unit.Millimeter)  # retrato
    orient = (QPageLayout.Orientation.Landscape if paisagem
              else QPageLayout.Orientation.Portrait)
    pag = QPageLayout(tam, orient, QMarginsF(0, 0, 0, 0))
    printer.setPageLayout(pag)
    try:
        printer.setFullPage(True)
    except Exception:
        pass
    return printer


def imprimir_imagens(imagens: list[Image.Image], layout, printer) -> int:
    """Pinta cada imagem numa página da impressora (tamanho físico do layout).

    Devolve quantas páginas foram enviadas. O ``printer`` é injetável — em
    teste, um QPrinter em modo PDF grava um arquivo que a régua de mm mede.
    """
    from PySide6.QtGui import QImage, QPainter

    if not imagens:
        raise ValueError("nada para imprimir")
    configurar_impressora(printer, layout)
    painter = QPainter(printer)
    try:
        n = 0
        for i, img in enumerate(imagens):
            if i > 0:
                printer.newPage()
            rgba = img.convert("RGBA")
            qimg = QImage(rgba.tobytes("raw", "RGBA"), rgba.width, rgba.height,
                          QImage.Format.Format_RGBA8888).copy()
            # preenche a página inteira (a folha já tem a proporção do layout)
            painter.drawImage(painter.viewport(), qimg)
            n += 1
        return n
    finally:
        painter.end()

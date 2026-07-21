"""
Ícones do sistema de design
===========================
Set aberto estilo Lucide/Feather: SVG de traço (24×24, stroke 2, cantos
redondos), embutido no código (sem arquivos externos) e renderizado em 2×
para ficar nítido em qualquer tela. Cor vem dos tokens.

Uso::

    from app.qt.design.icones import icone
    botao.setIcon(icone("zoom_mais"))
"""

from __future__ import annotations

from PySide6.QtCore import QByteArray, Qt
from PySide6.QtGui import QIcon, QPainter, QPixmap
from PySide6.QtSvg import QSvgRenderer

from app.qt.design import tokens

# Corpo dos SVGs (o <svg> externo é montado em _svg). Geometria 24×24.
_ICONES: dict[str, str] = {
    # --- zoom / enquadrar ---
    "zoom_mais": '<circle cx="11" cy="11" r="7"/><path d="m20 20-4.3-4.3"/>'
                 '<path d="M11 8v6M8 11h6"/>',
    "zoom_menos": '<circle cx="11" cy="11" r="7"/><path d="m20 20-4.3-4.3"/>'
                  '<path d="M8 11h6"/>',
    "ajustar": '<path d="M8 3H5a2 2 0 0 0-2 2v3"/><path d="M21 8V5a2 2 0 0 0-2-2h-3"/>'
               '<path d="M3 16v3a2 2 0 0 0 2 2h3"/><path d="M16 21h3a2 2 0 0 0 2-2v-3"/>',
    # --- regiões ---
    "imagem": '<rect x="3" y="3" width="18" height="18" rx="2"/>'
              '<circle cx="8.5" cy="8.5" r="1.5"/><path d="m21 15-5-5L5 21"/>',
    "texto": '<path d="M4 7V4h16v3"/><path d="M9 20h6"/><path d="M12 4v16"/>',
    "preco": '<path d="M11.2 2H4a2 2 0 0 0-2 2v7.2a2 2 0 0 0 .6 1.4l8.3 8.3a2 2 0 0 0 '
             '2.8 0l7.2-7.2a2 2 0 0 0 0-2.8L12.6 2.6a2 2 0 0 0-1.4-.6z"/>'
             '<circle cx="7.5" cy="7.5" r="1"/>',
    "unidade": '<path d="M21.3 8.7 15.3 2.7a1 1 0 0 0-1.4 0L2.7 13.9a1 1 0 0 0 0 '
               '1.4l6 6a1 1 0 0 0 1.4 0L21.3 10a1 1 0 0 0 0-1.3z"/>'
               '<path d="m7.5 10.5 2 2"/><path d="m10.5 7.5 2 2"/><path d="m13.5 4.5 2 2"/>',
    "selo": '<circle cx="12" cy="8" r="6"/><path d="M15.5 13 17 22l-5-3-5 3 1.5-9"/>',
    # --- alinhar (glifos próprios: linha-guia + dois objetos) ---
    "alinhar_esq": '<path d="M4 3v18"/><rect x="8" y="5" width="12" height="5" rx="1"/>'
                   '<rect x="8" y="14" width="7" height="5" rx="1"/>',
    "alinhar_cent_h": '<path d="M12 3v18"/><rect x="5" y="5" width="14" height="5" rx="1"/>'
                      '<rect x="8" y="14" width="8" height="5" rx="1"/>',
    "alinhar_dir": '<path d="M20 3v18"/><rect x="4" y="5" width="12" height="5" rx="1"/>'
                   '<rect x="9" y="14" width="7" height="5" rx="1"/>',
    "alinhar_topo": '<path d="M3 4h18"/><rect x="5" y="8" width="5" height="12" rx="1"/>'
                    '<rect x="14" y="8" width="5" height="7" rx="1"/>',
    "alinhar_meio": '<path d="M3 12h18"/><rect x="5" y="5" width="5" height="14" rx="1"/>'
                    '<rect x="14" y="8" width="5" height="8" rx="1"/>',
    "alinhar_base": '<path d="M3 20h18"/><rect x="5" y="4" width="5" height="12" rx="1"/>'
                    '<rect x="14" y="9" width="5" height="7" rx="1"/>',
    # --- distribuir ---
    "dist_h": '<rect x="3" y="7" width="4" height="10" rx="1"/>'
              '<rect x="10" y="7" width="4" height="10" rx="1"/>'
              '<rect x="17" y="7" width="4" height="10" rx="1"/>',
    "dist_v": '<rect x="7" y="3" width="10" height="4" rx="1"/>'
              '<rect x="7" y="10" width="10" height="4" rx="1"/>'
              '<rect x="7" y="17" width="10" height="4" rx="1"/>',
    # --- arquivo ---
    "salvar": '<path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z"/>'
              '<path d="M17 21v-8H7v8"/><path d="M7 3v5h8"/>',
    "abrir": '<path d="m6 14 1.5-2.9A2 2 0 0 1 9.24 10H20a2 2 0 0 1 1.94 2.5l-1.55 6A2 2 '
             '0 0 1 18.45 20H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h3.93a2 2 0 0 1 1.66.9l.82 '
             '1.2a2 2 0 0 0 1.66.9H18a2 2 0 0 1 2 2v2"/>',
    # --- painéis ---
    "camadas": '<path d="m12 2 10 5-10 5L2 7z"/><path d="m2 12 10 5 10-5"/>'
               '<path d="m2 17 10 5 10-5"/>',
    "propriedades": '<path d="M21 4h-7M10 4H3"/><path d="M21 12h-9M8 12H3"/>'
                    '<path d="M21 20h-5M12 20H3"/><path d="M14 2v4"/><path d="M8 10v4"/>'
                    '<path d="M16 18v4"/>',
    # --- estados / utilitários ---
    "olho": '<path d="M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7-10-7-10-7z"/>'
            '<circle cx="12" cy="12" r="3"/>',
    "olho_fechado": '<path d="M4 4l16 16"/><path d="M9.9 5.2A10.6 10.6 0 0 1 12 5c6.5 '
                    '0 10 7 10 7a17 17 0 0 1-2.9 3.9M6.3 6.3A16.8 16.8 0 0 0 2 12s3.5 '
                    '7 10 7c1.4 0 2.7-.3 3.8-.8"/>',
    "cadeado": '<rect x="4" y="11" width="16" height="10" rx="2"/>'
               '<path d="M8 11V7a4 4 0 0 1 8 0v4"/>',
    "cadeado_aberto": '<rect x="4" y="11" width="16" height="10" rx="2"/>'
                      '<path d="M8 11V7a4 4 0 0 1 7.9-1"/>',
    "seta_cima": '<path d="m18 15-6-6-6 6"/>',
    "seta_baixo": '<path d="m6 9 6 6 6-6"/>',
    "fechar": '<path d="M18 6 6 18M6 6l12 12"/>',
    "restaurar": '<path d="M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8"/>'
                 '<path d="M3 3v5h5"/>',
    "desfazer": '<path d="M9 14 4 9l5-5"/><path d="M4 9h10.5a5.5 5.5 0 0 1 0 11H11"/>',
    "refazer": '<path d="m15 14 5-5-5-5"/><path d="M20 9H9.5a5.5 5.5 0 0 0 0 11H13"/>',
    "busca": '<circle cx="11" cy="11" r="7"/><path d="m20 20-4.3-4.3"/>',
    "duplicar": '<rect x="9" y="9" width="12" height="12" rx="2"/>'
                '<path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/>',
    "lixeira": '<path d="M3 6h18"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6"/>'
               '<path d="M8 6V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>'
               '<path d="M10 11v6M14 11v6"/>',
    "paragrafo": '<path d="M13 4v16M17 4v16"/><path d="M19 4H9.5a4.5 4.5 0 0 0 0 9H13"/>',
    "check_circulo": '<circle cx="12" cy="12" r="10"/><path d="m8.5 12.5 2.5 2.5 5-6"/>',
    "alerta_circulo": '<circle cx="12" cy="12" r="10"/><path d="M12 7v6"/>'
                      '<path d="M12 16.5h.01"/>',
    "info_circulo": '<circle cx="12" cy="12" r="10"/><path d="M12 16v-5"/>'
                    '<path d="M12 8h.01"/>',
    "calendario": '<rect x="3" y="4" width="18" height="18" rx="2"/>'
                  '<path d="M16 2v4M8 2v4M3 10h18"/>',
    "lampada": '<path d="M9 18h6"/><path d="M10 22h4"/>'
               '<path d="M15.1 14A5 5 0 1 0 8.9 14c.6.8 1.1 1.6 1.1 2.5h4c0-.9.5-1.7 1.1-2.5z"/>',
    # --- navegação do shell (telas do Bloco D) ---
    "casa": '<path d="m3 10 9-7 9 7v10a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/>'
            '<path d="M9 22V12h6v10"/>',
    "caixa": '<path d="M21 8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 '
             '2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"/>'
             '<path d="m3.3 7 8.7 5 8.7-5"/><path d="M12 22V12"/>',
    "grade": '<rect x="3" y="3" width="7" height="7" rx="1"/>'
             '<rect x="14" y="3" width="7" height="7" rx="1"/>'
             '<rect x="3" y="14" width="7" height="7" rx="1"/>'
             '<rect x="14" y="14" width="7" height="7" rx="1"/>',
    "impressora": '<path d="M6 9V3h12v6"/><rect x="6" y="14" width="12" height="8" rx="1"/>'
                  '<path d="M6 18H4a2 2 0 0 1-2-2v-5a2 2 0 0 1 2-2h16a2 2 0 0 1 2 2v5a2 '
                  '2 0 0 1-2 2h-2"/>',
    "cofre": '<rect x="2" y="3" width="20" height="5" rx="1"/>'
             '<path d="M4 8v11a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8"/><path d="M10 12h4"/>',
    "engrenagem": '<path d="M12.22 2h-.44a2 2 0 0 0-2 2v.18a2 2 0 0 1-1 1.73l-.43.25a2 '
                  '2 0 0 1-2 0l-.15-.08a2 2 0 0 0-2.73.73l-.22.38a2 2 0 0 0 .73 '
                  '2.73l.15.1a2 2 0 0 1 1 1.72v.51a2 2 0 0 1-1 1.74l-.15.09a2 2 0 0 '
                  '0-.73 2.73l.22.38a2 2 0 0 0 2.73.73l.15-.08a2 2 0 0 1 2 '
                  '0l.43.25a2 2 0 0 1 1 1.73V20a2 2 0 0 0 2 2h.44a2 2 0 0 0 '
                  '2-2v-.18a2 2 0 0 1 1-1.73l.43-.25a2 2 0 0 1 2 0l.15.08a2 2 0 0 0 '
                  '2.73-.73l.22-.39a2 2 0 0 0-.73-2.73l-.15-.08a2 2 0 0 '
                  '1-1-1.74v-.5a2 2 0 0 1 1-1.74l.15-.09a2 2 0 0 0 '
                  '.73-2.73l-.22-.38a2 2 0 0 0-2.73-.73l-.15.08a2 2 0 0 1-2 '
                  '0l-.43-.25a2 2 0 0 1-1-1.73V4a2 2 0 0 0-2-2z"/>'
                  '<circle cx="12" cy="12" r="3"/>',
}

_cache: dict[tuple, QIcon] = {}


def _svg(corpo: str, cor: str) -> bytes:
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" '
        f'stroke="{cor}" stroke-width="2" stroke-linecap="round" '
        f'stroke-linejoin="round">{corpo}</svg>'
    ).encode()


def _pixmap(corpo: str, cor: str, tamanho: int) -> QPixmap:
    render = QSvgRenderer(QByteArray(_svg(corpo, cor)))
    pm = QPixmap(tamanho * 2, tamanho * 2)  # 2× para nitidez (HiDPI)
    pm.fill(Qt.GlobalColor.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    render.render(p)
    p.end()
    pm.setDevicePixelRatio(2)
    return pm


def icone(nome: str, cor: str | None = None, tamanho: int = 20) -> QIcon:
    """Devolve o QIcon nomeado (com variante desabilitada automática).

    FASE 1 (passo 15): sem `cor`, vale o token DO TEMA ATUAL — lido na
    CHAMADA (default congelado no import prenderia o claro para sempre).
    """
    if cor is None:
        cor = tokens.ICONE
    chave = (nome, cor, tamanho)
    if chave not in _cache:
        corpo = _ICONES[nome]
        ic = QIcon(_pixmap(corpo, cor, tamanho))
        ic.addPixmap(
            _pixmap(corpo, tokens.ICONE_APAGADO, tamanho), QIcon.Mode.Disabled
        )
        _cache[chave] = ic
    return _cache[chave]


def nomes_disponiveis() -> list[str]:
    return sorted(_ICONES)

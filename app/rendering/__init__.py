"""
Renderização — motor visual (Fase 2+)
=====================================
Compõe o cartaz/tabloide DESENHANDO texto e imagem por cima de uma arte de fundo
(a imagem do Illustrator, intocada). Não rasteriza SVG.

O modelo de layout é resolução-independente (coordenadas em milímetros); a
conversão para pixels acontece só na hora de compor, a partir do DPI. O mesmo
modelo será lido pelo editor interativo do Qt na Fase 5.
"""

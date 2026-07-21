"""
Camada de interface (Qt / PySide6) — Bloco C.

Regra WYSIWYG: o canvas mostra a imagem renderizada pelo MESMO compositor Pillow
da F2. O Qt cuida só da interação (ver, selecionar, arrastar) — nunca redesenha
texto/imagem por conta própria. Assim o que se vê é idêntico ao que se exporta.
"""

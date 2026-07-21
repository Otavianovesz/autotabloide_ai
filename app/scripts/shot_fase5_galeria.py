"""FASE 5 — galeria do fecho (passos 92/99), caminho NATIVO (texto legível).

Diferente dos scripts de compositor (que já saem legíveis via Pillow), este
captura a CHROME do editor/diálogos — por isso usa o plugin nativo, não o
offscreen (que renderiza a fonte de UI como caixas nesta bancada).

Uso::

    python -m app.scripts.shot_fase5_galeria
"""

from __future__ import annotations

import os
import sys
from decimal import Decimal
from pathlib import Path

os.environ.pop("QT_QPA_PLATFORM", None)   # NATIVO (não offscreen)

from PySide6.QtCore import Qt  # noqa: E402
from PySide6.QtGui import QImage, QPainter  # noqa: E402
from PySide6.QtWidgets import QApplication  # noqa: E402

from app.qt.editor import Editor  # noqa: E402
from app.rendering.compositor import DadosProduto  # noqa: E402
from app.rendering.model import (  # noqa: E402
    Ajuste, Alinhamento, LayoutDef, Mascara, Pagina, PapelPreco, PapelTexto,
    Regiao, Retangulo, Slot, TipoRegiao,
)

SAIDA = Path("saida_fase5")


def _pagina_rica():
    """Uma célula-herói (foto mascarada em círculo + pílula + preço com
    contorno) e os quatro papéis de texto com badge — tudo cabendo na vista."""
    img = Regiao(TipoRegiao.IMAGEM, Retangulo(34, 4, 32, 32),
                 ajuste=Ajuste.PREENCHER, mascara=Mascara.CIRCULO, nome="Foto")
    nome = Regiao(TipoRegiao.NOME, Retangulo(6, 38, 88, 8), cor="#ffffff",
                  alinhamento=Alinhamento.CENTRO, tamanho_max_pt=18,
                  pill=True, pill_cor="#111111", pill_opacidade=205, nome="Nome")
    preco = Regiao(TipoRegiao.PRECO, Retangulo(6, 47, 88, 11), cor="#ffffff",
                   alinhamento=Alinhamento.CENTRO, tamanho_max_pt=30,
                   papel_preco=PapelPreco.UNICO, contorno=True,
                   cor_efeito="#000000", nome="Preço")
    r = lambda y: Retangulo(8, y, 88, 6)  # noqa: E731
    legais = [
        Regiao(TipoRegiao.TEXTO_LEGAL, r(62), nome="Legal",
               papel_texto=PapelTexto.LEGAL,
               texto_fixo="Bebida alcoólica. Venda proibida para menores de 18 anos."),
        Regiao(TipoRegiao.TEXTO_LEGAL, r(72), nome="Validade",
               papel_texto=PapelTexto.VALIDADE),
        Regiao(TipoRegiao.TEXTO_LEGAL, r(82), nome="Dica",
               papel_texto=PapelTexto.DICA, texto_fixo="Combina com pão quentinho."),
        Regiao(TipoRegiao.TEXTO_LEGAL, r(92), nome="Livre",
               papel_texto=PapelTexto.LIVRE, texto_fixo="Promoção da semana!"),
    ]
    return LayoutDef(100, 100, dpi=200,
                     paginas=[Pagina([Slot("s", [img, nome, preco] + legais)])])


def _foto_produto(caminho):
    from PIL import Image, ImageDraw
    im = Image.new("RGB", (300, 300))
    px = im.load()
    for y in range(300):
        for x in range(300):
            px[x, y] = (30 + x // 2, 120 + y // 4, 210 - x // 3)
    ImageDraw.Draw(im).ellipse([110, 110, 190, 190], fill=(255, 210, 40))
    im.save(caminho)
    return str(caminho)


def main() -> None:
    SAIDA.mkdir(parents=True, exist_ok=True)
    app = QApplication.instance() or QApplication(sys.argv)
    from app.qt.design.papel_texto_ui import _dialogo_cls
    from app.qt.design.tema import aplicar_tema

    foto = _foto_produto(SAIDA / "_foto_heroi.png")
    dados = DadosProduto("Refrigerante Gelado", preco_por=Decimal("5.99"),
                         imagem_path=foto,
                         texto_legal="OFERTA VÁLIDA DE 17/07 A 20/07")
    grabs = {}
    for tema in ("claro", "escuro"):
        aplicar_tema(app, tema)
        ed = Editor()
        ed.resize(820, 780)
        ed.carregar(_pagina_rica(), dados)
        ed.show()
        app.processEvents()
        ed.area.canvas.ajustar()
        app.processEvents()
        pm = ed.grab()
        pm.save(str(SAIDA / f"blocoG_editor_{tema}.png"))
        grabs[tema] = pm.toImage()
        print(f"editor {tema}: blocoG_editor_{tema}.png")

        dlg = _dialogo_cls()(None)
        dlg.selecionar(PapelTexto.VALIDADE)
        dlg.resize(430, 350)
        dlg.show()
        app.processEvents()
        dlg.grab().save(str(SAIDA / f"blocoG_dialogo_{tema}.png"))
        print(f"dialogo {tema}: blocoG_dialogo_{tema}.png")

    # passo 99: cartaz claro + escuro lado a lado
    c, e = grabs["claro"], grabs["escuro"]
    larg, alt = c.width() + e.width() + 24, max(c.height(), e.height())
    lado = QImage(larg, alt, QImage.Format.Format_ARGB32)
    lado.fill(Qt.GlobalColor.transparent)
    p = QPainter(lado)
    p.drawImage(0, 0, c)
    p.drawImage(c.width() + 24, 0, e)
    p.end()
    lado.save(str(SAIDA / "blocoG_cartaz_claro_escuro.png"))
    print("lado a lado: blocoG_cartaz_claro_escuro.png")

    aplicar_tema(app, "claro")


if __name__ == "__main__":
    main()

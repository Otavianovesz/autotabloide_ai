"""FASE 5 — Bloco A (passo 14): foto do diálogo nomeado + uma região de cada
papel exibindo seu badge (claro e escuro).

Uso::

    python -m app.scripts.shot_fase5_blocoA
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication  # noqa: E402

from app.qt.editor import Editor  # noqa: E402
from app.rendering.compositor import DadosProduto  # noqa: E402
from app.rendering.model import (  # noqa: E402
    LayoutDef, Pagina, PapelTexto, Regiao, Retangulo, Slot, TipoRegiao,
)

SAIDA = Path("saida_fase5")


def _layout_quatro_papeis():
    r = lambda y: Retangulo(8, y, 84, 12)  # noqa: E731
    regioes = [
        Regiao(TipoRegiao.TEXTO_LEGAL, r(14), nome="Legal",
               papel_texto=PapelTexto.LEGAL,
               texto_fixo="Bebida alcoólica. Venda proibida para menores de 18 anos."),
        Regiao(TipoRegiao.TEXTO_LEGAL, r(40), nome="Validade",
               papel_texto=PapelTexto.VALIDADE),
        Regiao(TipoRegiao.TEXTO_LEGAL, r(66), nome="Dica",
               papel_texto=PapelTexto.DICA,
               texto_fixo="Combina com pão quentinho e um café passado na hora."),
        Regiao(TipoRegiao.TEXTO_LEGAL, r(92), nome="Livre",
               papel_texto=PapelTexto.LIVRE, texto_fixo="Promoção da semana!"),
    ]
    return LayoutDef(100, 112, dpi=200, paginas=[Pagina([Slot("s", regioes)])])


def main() -> None:
    SAIDA.mkdir(parents=True, exist_ok=True)
    app = QApplication.instance() or QApplication(sys.argv)
    from app.qt.design.papel_texto_ui import _dialogo_cls
    from app.qt.design.tema import aplicar_tema

    dados = DadosProduto("Oferta", texto_legal="OFERTA VÁLIDA DE 17/07 A 20/07")

    for tema in ("claro", "escuro"):
        aplicar_tema(app, tema)

        ed = Editor()
        ed.resize(760, 720)
        ed.carregar(_layout_quatro_papeis(), dados)
        ed.show()
        app.processEvents()
        ed.area.canvas.ajustar()
        app.processEvents()
        alvo = SAIDA / f"blocoA_badges_{tema}.png"
        ed.grab().save(str(alvo))
        print(f"badges  {tema}: {alvo}")

        dlg = _dialogo_cls()(None)
        dlg.selecionar(PapelTexto.LEGAL)
        dlg.resize(420, 340)
        dlg.show()
        app.processEvents()
        alvo_d = SAIDA / f"blocoA_dialogo_{tema}.png"
        dlg.grab().save(str(alvo_d))
        print(f"dialogo {tema}: {alvo_d}")

    aplicar_tema(app, "claro")


if __name__ == "__main__":
    main()

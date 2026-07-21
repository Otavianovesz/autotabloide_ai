"""FASE 6 — galeria do fecho (passos 91/99), caminho NATIVO (texto legível).

A barra da Mesa nas larguras, o modo planilha e a estante viva — para o selo
visual do arquiteto. Usa o plugin nativo (não offscreen).

Uso::

    python -m app.scripts.shot_fase6_galeria
"""

from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

os.environ.pop("QT_QPA_PLATFORM", None)
os.environ.setdefault("AUTOTABLOIDE_ROOT", tempfile.mkdtemp(prefix="atb_f6gal_"))

from PySide6.QtWidgets import QApplication  # noqa: E402

SAIDA = Path("saida_fase6")


def main() -> None:
    SAIDA.mkdir(parents=True, exist_ok=True)
    app = QApplication.instance() or QApplication(sys.argv)
    from app.core.database import Database
    from app.core.paths import SystemRoot
    SystemRoot().criar_estrutura()
    Database().init().engine.dispose()
    from app.qt.design.tema import aplicar_tema
    from app.qt.telas import servico
    from app.qt.telas.mesa import MesaTela
    from app.qt.telas.planilha_dialog import DialogoPlanilha

    itens = [
        servico.ItemMesa("Arroz Tio João 5kg", "24,90", "VERDE", "Arroz Tio João 5kg"),
        servico.ItemMesa("Feijão Carioca Camil 1kg", None, "AMARELO", "Feijão Carioca Camil 1kg"),
        servico.ItemMesa("Refrigerante Guaraná 2L", "7,99", "VERDE", "Refrigerante Guaraná 2L"),
        servico.ItemMesa("Sabão em pó OMO 1,6kg", "2x 9,90", "VERMELHO", "Sabão em pó OMO 1,6kg"),
    ]
    for it, cat in zip(itens, ("Grãos", "Grãos", "Bebidas", "Limpeza")):
        it.categoria = cat

    for tema in ("claro", "escuro"):
        aplicar_tema(app, tema)
        m = MesaTela()
        m._itens = list(itens)
        m._recarregar_lista()
        m.resize(1280, 720)
        m.show()
        app.processEvents()
        m._reflow_barra()
        app.processEvents()
        m.grab().save(str(SAIDA / f"blocoG_mesa_1280_{tema}.png"))
        print(f"mesa 1280 {tema}: blocoG_mesa_1280_{tema}.png")

        m.resize(1920, 720)
        app.processEvents()
        m._reflow_barra()
        app.processEvents()
        m.grab().save(str(SAIDA / f"blocoG_mesa_1920_{tema}.png"))
        print(f"mesa 1920 {tema}: blocoG_mesa_1920_{tema}.png")

        dlg = DialogoPlanilha(m, m)
        dlg.resize(720, 320)
        dlg.show()
        app.processEvents()
        dlg.grab().save(str(SAIDA / f"blocoG_planilha_{tema}.png"))
        print(f"planilha {tema}: blocoG_planilha_{tema}.png")

    aplicar_tema(app, "claro")


if __name__ == "__main__":
    main()

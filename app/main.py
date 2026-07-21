"""
Ponto de entrada do AutoTabloide AI
===================================
Prepara o sistema (pastas + banco) e abre o shell do app com a tela inicial.
As telas de produção (Dashboard, Mesa, Fábrica…) chegam no Bloco D.

Rodar com::

    python -m app.main            # tela inicial
    python -m app.main --editor   # direto no editor (caso real)
"""

from __future__ import annotations

import sys

from app.core.database import Database
from app.core.paths import SystemRoot


def preparar_sistema() -> SystemRoot:
    """Cria a estrutura de pastas e inicializa o banco."""
    root = SystemRoot().criar_estrutura()
    Database(root).init()
    return root


def main() -> int:
    if "--editor" in sys.argv:
        from app.editor_app import main as editor_main
        return editor_main()

    from PySide6.QtWidgets import QApplication

    from app.qt.design.componentes import EstadoVazio
    from app.qt.design.shell import Shell
    from app.qt.design.tema import aplicar_tema

    from app.core.cofre import snapshot_automatico
    snapshot_automatico()               # D-B2: backup automático na abertura
    preparar_sistema()
    from app.editor_app import _migrar_artes
    _migrar_artes()                     # E-A3: arte antiga → pasta da raiz
    app = QApplication(sys.argv)
    aplicar_tema(app)
    from app.qt.design.animacoes import instalar_vida
    from app.qt.design.polimento import instalar_polimento
    instalar_vida(app)          # FASE 1 (40-41): diálogos e hover com vida
    instalar_polimento(app)     # FASE 1 (52): combos sem texto cortado

    shell = Shell()
    inicio = EstadoVazio(
        "casa", "Bem-vindo ao AutoTabloide AI",
        "As telas de produção (Mesa, Fábrica, Almoxarifado…) chegam no Bloco D.\n"
        "Por enquanto, o editor de layouts:  python -m app.main --editor",
    )
    shell.adicionar_tela("inicio", inicio)
    shell.ir_para("inicio")
    shell.set_dica("Fundação pronta — banco e pastas inicializados")
    shell.resize(1100, 720)
    shell.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())

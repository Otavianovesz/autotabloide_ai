"""
Fotografar os ESTADOS novos do Bloco F (FASE 1, passo 85)
=========================================================
Splash, toast com Desfazer, boas-vindas, Sobre e estado vazio com ação —
nos DOIS temas. Sai em ``saida_fase1/estados`` e ``estados_escuro``.

Rodar::

    python -m app.scripts.fotografar_estados
"""

from __future__ import annotations

import sys
from pathlib import Path


def _processar(n: int = 4) -> None:
    from PySide6.QtWidgets import QApplication
    for _ in range(n):
        QApplication.processEvents()


def _grab(w, pasta: Path, nome: str) -> None:
    _processar()
    pasta.mkdir(parents=True, exist_ok=True)
    w.grab().save(str(pasta / nome))
    print(f"  {nome}")


def _fotografar_tema(pasta: Path) -> None:
    from PySide6.QtCore import Qt
    from PySide6.QtWidgets import QPushButton, QWidget

    from app.qt.design.boas_vindas import BoasVindasDialog
    from app.qt.design.componentes import EstadoVazio
    from app.qt.design.icones import icone
    from app.qt.design.sobre import SobreDialog
    from app.qt.design.splash import _pixmap_splash
    from app.qt.design.toast import mostrar_toast_desfazer

    pasta.mkdir(parents=True, exist_ok=True)
    _pixmap_splash().save(str(pasta / "splash.png"))
    print("  splash.png")

    # toast com Desfazer numa janela de apoio
    janela = QWidget()
    janela.setAttribute(Qt.WidgetAttribute.WA_DontShowOnScreen, True)
    janela.resize(640, 220)
    janela.show()
    mostrar_toast_desfazer(janela, "3 item(ns) fora da estante.",
                           lambda: None)
    # o toast ENTRA em fade (180 ms) — deixar a animação fechar antes do grab
    import time
    from PySide6.QtWidgets import QApplication
    fim = time.monotonic() + 0.45
    while time.monotonic() < fim:
        QApplication.processEvents()
        time.sleep(0.01)
    _grab(janela, pasta, "toast_desfazer.png")
    janela.close()

    # estado vazio COM ação (o padrão do passo 73)
    caixa = QWidget()
    caixa.setAttribute(Qt.WidgetAttribute.WA_DontShowOnScreen, True)
    caixa.resize(480, 320)
    botao = QPushButton(" Importar tabela/foto")
    botao.setIcon(icone("abrir", tamanho=16))
    vazio = EstadoVazio("caixa", "Nenhuma oferta importada",
                        "Importe a foto do WhatsApp ou a tabela\n"
                        "para começar o tabloide.", acao=botao, parent=caixa)
    vazio.resize(caixa.size())
    caixa.show()
    _grab(caixa, pasta, "vazio_com_acao.png")
    caixa.close()

    dlg = BoasVindasDialog(None)
    dlg.setAttribute(Qt.WidgetAttribute.WA_DontShowOnScreen, True)
    dlg.show()
    _grab(dlg, pasta, "boas_vindas.png")
    dlg.reject()

    sobre = SobreDialog()
    sobre.setAttribute(Qt.WidgetAttribute.WA_DontShowOnScreen, True)
    sobre.show()
    _grab(sobre, pasta, "sobre.png")
    sobre.reject()


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    from PySide6.QtWidgets import QApplication

    from app.qt.design.tema import aplicar_tema

    app = QApplication.instance() or QApplication([])
    for tema, pasta in [("claro", Path("saida_fase1/estados")),
                        ("escuro", Path("saida_fase1/estados_escuro"))]:
        aplicar_tema(app, tema)
        print(f"tema {tema}:")
        _fotografar_tema(pasta)
    aplicar_tema(app, "claro")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

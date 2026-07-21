"""
Fotografar as telas do app (FASE 1, passo 1)
============================================
Abre CADA tela do shell real + os 3 diálogos e salva PNG na pasta pedida —
a prova visual do antes/depois/escuro da Fase 1 (e das fases seguintes).

Rodar::

    python -m app.scripts.fotografar_telas saida_fase1/antes
    python -m app.scripts.fotografar_telas saida_fase1/escuro --tema=escuro
"""

from __future__ import annotations

import sys
from pathlib import Path

# SEM offscreen de propósito: o plugin nativo resolve as fontes da UI
# (o offscreen desta bancada renderizava glifos como caixas); as janelas
# usam WA_DontShowOnScreen — nada pisca na tela do usuário.

TELAS = ["inicio", "atelie", "almoxarifado", "mesa", "fabrica", "cofre",
         "configuracoes"]


def _processar(n: int = 3) -> None:
    from PySide6.QtWidgets import QApplication
    for _ in range(n):
        QApplication.processEvents()


def _grab(widget, pasta: Path, nome: str) -> None:
    _processar()
    pasta.mkdir(parents=True, exist_ok=True)
    widget.grab().save(str(pasta / nome))
    print(f"  {nome}")


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    pasta = Path(args[0] if args else "saida_fase1/antes")
    tema = next((a.split("=", 1)[1] for a in sys.argv[1:]
                 if a.startswith("--tema=")), None)
    # FASE 1 (passos 62-63): fotografar em qualquer tamanho de janela
    tam = next((a.split("=", 1)[1] for a in sys.argv[1:]
                if a.startswith("--tamanho=")), "1440x900")
    larg, alt = (int(v) for v in tam.lower().split("x"))

    from PySide6.QtCore import Qt
    from PySide6.QtWidgets import QApplication

    from app.editor_app import montar_janela
    from app.qt.design.tema import aplicar_tema

    app = QApplication.instance() or QApplication([])
    if tema:
        aplicar_tema(app, tema)          # (ganha o 2º arg no Bloco B)
    else:
        aplicar_tema(app)
    # FASE 1 (Bloco E): o polimento é PRODUÇÃO determinística (mínimos,
    # popups) — entra nas fotos; a vida (animações) fica fora de propósito
    from app.qt.design.polimento import instalar_polimento
    instalar_polimento(app)

    shell, editor = montar_janela()
    shell.setAttribute(Qt.WidgetAttribute.WA_DontShowOnScreen, True)
    shell.resize(larg, alt)
    shell.show()
    _processar()

    # --- as 7 telas do shell -------------------------------------------------
    for chave in TELAS:
        shell.ir_para(chave)
        _grab(shell, pasta, f"tela_{chave}.png")

    # --- o editor com a grade real (dentro do Ateliê é sob demanda; aqui o
    # editor "solto" do montar_janela já carrega a grade do Belo Brasil) ------
    editor.setAttribute(Qt.WidgetAttribute.WA_DontShowOnScreen, True)
    editor.resize(larg, alt)
    editor.show()
    _processar()
    editor.area.canvas.ajustar()
    _grab(editor, pasta, "tela_editor_grade.png")
    editor.close()

    # --- os 3 diálogos -------------------------------------------------------
    from app.qt.telas.conciliacao_dialog import ConciliacaoDialog
    from app.qt.telas.servico import ItemMesa, ResultadoMesa
    itens = [
        ItemMesa("OLEO DE SOJA LIZA 900 ML", "7,71", "VERDE",
                 "Óleo de Soja Liza 900ml"),
        ItemMesa("REFRIG. KITUBAINA 1500ML", "5,50", "AMARELO",
                 "?", candidato_nome="Refrigerante Kitubaina 1,5L"),
        ItemMesa("DOCE DE BANANA VAL 250 G", "6,66", "VERMELHO",
                 "DOCE DE BANANA VAL 250 G"),
    ]
    dlg = ConciliacaoDialog(ResultadoMesa(itens=itens))
    dlg.setAttribute(Qt.WidgetAttribute.WA_DontShowOnScreen, True)
    dlg.resize(980, 560)
    dlg.show()
    _grab(dlg, pasta, "dialogo_conciliacao.png")
    dlg.done(0)

    from app.qt.telas.curadoria_dialog import CuradoriaDialog
    dlg2 = CuradoriaDialog("Doce de Banana Val 250g", [],
                           tokens_perdidos=["VAL"])
    dlg2.setAttribute(Qt.WidgetAttribute.WA_DontShowOnScreen, True)
    dlg2.resize(720, 520)
    dlg2.show()
    _grab(dlg2, pasta, "dialogo_curadoria.png")
    dlg2.reject()

    from app.qt.telas.fotos_item_dialog import FotosItemDialog
    dlg3 = FotosItemDialog(itens[0])
    dlg3.setAttribute(Qt.WidgetAttribute.WA_DontShowOnScreen, True)
    dlg3.resize(760, 560)
    dlg3.show()
    _grab(dlg3, pasta, "dialogo_fotos_item.png")
    dlg3.done(0)                          # encerra o worker de sugestões

    shell.close()
    _processar()
    print(f"Fotos em {pasta.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

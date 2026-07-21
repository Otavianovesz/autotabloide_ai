"""
Screenshots do sistema de design — todas as superfícies e estados
=================================================================
Gera em ``saida_design/`` (sem abrir janela na tela):

- 01_inicio.png       — shell com a tela inicial (estado vazio com craft)
- 02_editor.png       — editor completo, nada selecionado (painel vazio)
- 03_selecao.png      — região selecionada: contorno primário + alças Figma
- 04_hover.png        — estado hover de uma região (antes do clique)
- 05_carregando.png   — overlay "Removendo fundo…" sobre o canvas
- 06_toast.png        — toast "Layout salvo." no rodapé
- 07_ctrlk.png        — command palette (Ctrl+K) filtrando "alinhar"

Rodar::

    python -m app.scripts.screenshots_design
"""

from __future__ import annotations

from pathlib import Path

SAIDA = Path("saida_design")


def _realizar(janela) -> None:
    from PySide6.QtCore import Qt
    from PySide6.QtWidgets import QApplication

    janela.setAttribute(Qt.WidgetAttribute.WA_DontShowOnScreen, True)
    janela.resize(1440, 900)
    janela.show()
    QApplication.processEvents()


def _grab(janela, nome: str) -> None:
    from PySide6.QtWidgets import QApplication

    for _ in range(3):
        QApplication.processEvents()
    SAIDA.mkdir(parents=True, exist_ok=True)
    janela.grab().save(str(SAIDA / nome))
    print(f"  {nome}")


def main() -> None:
    from PySide6.QtWidgets import QApplication

    from app.editor_app import montar_janela
    from app.qt.design.componentes import EstadoVazio
    from app.qt.design.shell import Shell
    from app.qt.design.tema import aplicar_tema

    app = QApplication.instance() or QApplication([])
    aplicar_tema(app)

    # 01 — shell inicial
    shell0 = Shell()
    shell0.adicionar_tela("inicio", EstadoVazio(
        "casa", "Bem-vindo ao AutoTabloide AI",
        "As telas de produção (Mesa, Fábrica, Almoxarifado…) chegam no Bloco D."))
    shell0.ir_para("inicio")
    shell0.set_dica("Fundação pronta — banco e pastas inicializados")
    _realizar(shell0)
    _grab(shell0, "01_inicio.png")
    shell0.close()

    # 02..07 — editor no shell
    shell, editor = montar_janela()
    _realizar(shell)
    editor.area.canvas.ajustar()
    _grab(shell, "02_editor.png")

    # 03 — seleção (contorno primário + alças)
    itens = editor.canvas._itens
    if itens:
        itens[0].setSelected(True)
    _grab(shell, "03_selecao.png")

    # 04 — hover (estado renderizado de passar o mouse, sem clique)
    if itens:
        itens[0].setSelected(False)
        alvo = itens[1] if len(itens) > 1 else itens[0]
        alvo._hover = True
        alvo.update()
    _grab(shell, "04_hover.png")

    # 05 — carregando (overlay de etapa lenta de IA/imagem)
    from app.qt.design.carregando import OverlayOcupado
    overlay = OverlayOcupado(editor.area)
    overlay.mostrar("Removendo fundo…")
    _grab(shell, "05_carregando.png")
    overlay.esconder()

    # 06 — toast de sucesso
    from app.qt.design.toast import mostrar_toast
    toast = mostrar_toast(editor, "Layout salvo.", tipo="sucesso")
    toast._anim_op.stop()
    toast._anim_pos.stop()
    toast._efeito.setOpacity(1.0)
    toast.move(toast._anim_pos.endValue())
    _grab(shell, "06_toast.png")
    toast.hide()
    toast.deleteLater()

    # 07 — command palette filtrando "alinhar"
    editor.abrir_paleta()
    editor._paleta.busca.setText("alinhar")
    _grab(shell, "07_ctrlk.png")
    editor._paleta.fechar()

    shell.close()
    print(f"Screenshots em {SAIDA.resolve()}")


if __name__ == "__main__":
    main()

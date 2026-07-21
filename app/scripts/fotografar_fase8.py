"""Galeria NATIVA da FASE 8 (Exportação e publicação).

Fotografa o que o arquiteto sela no olho: o diálogo de perfis + fila em lote, o
hub Publicar, a MESMA peça com RASCUNHO e sem (aprovada) lado a lado, a Oferta
do Dia, um carrossel (3 cards), uma faixa e um frame de Story. As peças sociais
são PIL (compor_social); os diálogos são Qt nativo (WA_DontShowOnScreen).

SEM offscreen (o plugin nativo resolve as fontes da UI). Encerra com os._exit(0)
(o teardown nativo do Qt no Windows às vezes cai DEPOIS de gravar — não é bug de
produção; a suíte roda offscreen). Rodar::

    python -m app.scripts.fotografar_fase8 saida_fase8/claro
    python -m app.scripts.fotografar_fase8 saida_fase8/escuro --tema=escuro
"""

from __future__ import annotations

import sys
from decimal import Decimal
from pathlib import Path


def _processar(n: int = 3) -> None:
    from PySide6.QtWidgets import QApplication
    for _ in range(n):
        QApplication.processEvents()


def _grab(widget, pasta: Path, nome: str) -> None:
    _processar()
    pasta.mkdir(parents=True, exist_ok=True)
    widget.grab().save(str(pasta / nome))
    print(f"  {nome}")


def _foto(destino: Path, cor) -> str:
    from PIL import Image
    destino.parent.mkdir(parents=True, exist_ok=True)
    Image.new("RGB", (400, 400), cor).save(destino)
    return str(destino)


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    pasta = Path(args[0] if args else "saida_fase8/claro")
    tema = next((a.split("=", 1)[1] for a in sys.argv[1:]
                 if a.startswith("--tema=")), None)

    from PySide6.QtCore import Qt
    from PySide6.QtWidgets import QApplication

    from app.qt.design.tema import aplicar_tema
    app = QApplication.instance() or QApplication([])
    aplicar_tema(app, tema) if tema else aplicar_tema(app)
    from app.qt.design.polimento import instalar_polimento
    instalar_polimento(app)
    DONT = Qt.WidgetAttribute.WA_DontShowOnScreen

    from app.rendering.compositor import DadosProduto
    from app.rendering.marca_dagua import carimbar_rascunho
    from app.rendering.social import compor_carrossel, compor_social

    d = DadosProduto("Arroz Tio João 5kg", preco_por=Decimal("24.90"),
                     preco_de=Decimal("29.90"),
                     imagem_path=_foto(pasta / "_p.png", (40, 90, 200)))

    # --- peças sociais (PIL) -------------------------------------------------
    oferta = compor_social("oferta_do_dia", d)
    oferta.save(str(pasta / "oferta_do_dia.png"))
    print("  oferta_do_dia.png")
    # RASCUNHO × aprovada, lado a lado (a mesma peça)
    carimbar_rascunho(oferta).save(str(pasta / "oferta_RASCUNHO.png"))
    print("  oferta_RASCUNHO.png")
    for i, cor in enumerate([(200, 40, 40), (40, 160, 60), (230, 150, 30)], 1):
        dd = DadosProduto(f"Produto {i}", preco_por=Decimal("9.90"),
                          imagem_path=_foto(pasta / f"_c{i}.png", cor))
        [compor_social("carrossel", dd)][0].save(str(pasta / f"carrossel_card_{i}.png"))
    print("  carrossel_card_1..3.png")
    compor_social("faixa", d).save(str(pasta / "faixa.png"))
    print("  faixa.png")
    compor_social("story", d).save(str(pasta / "story_frame.png"))
    print("  story_frame.png")

    # --- diálogos Qt ---------------------------------------------------------
    from app.qt.telas.mesa import MesaTela
    from app.qt.telas.servico import ItemMesa
    mesa = MesaTela()
    mesa._itens = [
        ItemMesa("Óleo de Soja Liza 900ml", "7,71", "VERDE", "Óleo de Soja Liza 900ml"),
        ItemMesa("Arroz Tio João 5kg", "24,90", "VERDE", "Arroz Tio João 5kg"),
        ItemMesa("Refrigerante Kitubaina 1,5L", "5,50", "VERDE",
                 "Refrigerante Kitubaina 1,5L"),
    ]
    mesa.setAttribute(DONT, True)
    mesa.resize(1280, 760)
    mesa.show()
    _processar()

    from app.qt.telas.exportar_dialog import ExportarDialog
    exp = ExportarDialog(mesa, mesa)
    exp.setAttribute(DONT, True)
    exp.resize(460, 420)
    exp.show()
    _grab(exp, pasta, "dialogo_exportar_perfis.png")
    exp.done(0)

    from app.qt.telas.publicar_dialog import PublicarDialog
    pub = PublicarDialog(mesa, mesa)
    pub.setAttribute(DONT, True)
    pub.resize(470, 380)
    pub.show()
    _grab(pub, pasta, "dialogo_publicar.png")
    pub.done(0)

    mesa.close()
    from app.qt.workers import encerrar_todos
    encerrar_todos(1000)
    app.closeAllWindows()
    _processar()
    print(f"Galeria da Fase 8 em {pasta.resolve()}")
    sys.stdout.flush()
    import os
    os._exit(0)


if __name__ == "__main__":
    raise SystemExit(main())

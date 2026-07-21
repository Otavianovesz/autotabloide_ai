"""Galeria NATIVA da FASE 4 (Editor I) — artefato que faltava (OS F11.5 §2).

Fotografa o editor com um layout real carregado: o estado normal, o raio-X
(estrutura por papel), a seleção de região com as MEDIDAS ao vivo (X/Y/L/A +
cotas até as bordas + a cota região↔região nova do #77), e o aviso COERENTE
do cadeado da arte (#72). GIF curto do fluxo (normal → raio-X → seleção).

SEM offscreen de propósito (fontes nativas); janelas com WA_DontShowOnScreen.
Rodar::

    python -m app.scripts.fotografar_fase4 saida_fase4/claro
    python -m app.scripts.fotografar_fase4 saida_fase4/escuro --tema=escuro
"""

from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path


def _processar(n: int = 3) -> None:
    from PySide6.QtWidgets import QApplication
    for _ in range(n):
        QApplication.processEvents()


def _grab(widget, pasta: Path, nome: str):
    _processar()
    pasta.mkdir(parents=True, exist_ok=True)
    pm = widget.grab()
    pm.save(str(pasta / nome))
    print(f"  {nome}")
    return pm


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    pasta = Path(args[0] if args else "saida_fase4/claro")
    tema = next((a.split("=", 1)[1] for a in sys.argv[1:]
                 if a.startswith("--tema=")), None)

    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tests"))
    import seeds_portabilidade as seeds
    tmp = Path(tempfile.mkdtemp(prefix="f4_"))
    root = seeds.raiz(tmp, "raiz")
    os.environ["AUTOTABLOIDE_ROOT"] = str(root.raiz)

    from PySide6.QtCore import Qt
    from PySide6.QtWidgets import QApplication, QLabel, QVBoxLayout, QWidget

    from app.qt.design.tema import aplicar_tema
    app = QApplication.instance() or QApplication([])
    aplicar_tema(app, tema) if tema else aplicar_tema(app)
    DONT = Qt.WidgetAttribute.WA_DontShowOnScreen

    from decimal import Decimal

    from app.qt.editor import Editor
    from app.rendering.cartaz import layout_cartaz_exemplo
    from app.rendering.compositor import DadosProduto
    e = Editor()
    e.setAttribute(DONT, True)
    e.resize(1360, 800)
    lay = layout_cartaz_exemplo()
    e.canvas.carregar(lay, DadosProduto(
        "Café Torrado 500g", preco_por=Decimal("9.90"),
        preco_de=Decimal("12.90"), texto_legal="SOMENTE 24/07"))
    e.show()
    _processar(6)

    quadros = []
    # 1) estado normal
    quadros.append(_grab(e, pasta, "editor_normal.png"))
    # 2) raio-X (estrutura por papel)
    if hasattr(e.canvas, "set_raio_x"):
        e.canvas.set_raio_x(True)
        quadros.append(_grab(e, pasta, "editor_raio_x.png"))
        e.canvas.set_raio_x(False)
    # 3) seleção + MEDIDAS ao vivo (com a cota região↔região do #77)
    medidas: list[str] = []
    e.canvas.medidas.connect(medidas.append)
    itens = e.canvas._itens
    if itens:
        itens[1].setSelected(True)
        itens[1]._emitir_medidas()
        _processar()
    quadros.append(_grab(e, pasta, "editor_selecao.png"))
    # a régua de medidas REAL num cartão legível (o rodapé mora no shell)
    if medidas:
        cartao = QWidget()
        cartao.setAttribute(DONT, True)
        v = QVBoxLayout(cartao)
        titulo = QLabel("Medidas ao vivo (rodapé)")
        titulo.setProperty("papel", "titulo")
        corpo = QLabel(medidas[-1])
        v.addWidget(titulo)
        v.addWidget(corpo)
        cartao.resize(640, 110)
        cartao.show()
        _grab(cartao, pasta, "medidas_com_cota_vizinha.png")
        cartao.close()
        print("  medida real:", medidas[-1])
    # 4) cadeado da arte — o aviso COERENTE (#72), capturado de verdade
    avisos: list[str] = []
    e.canvas._avisar_info = avisos.append
    e.canvas.set_arte_travada(False)
    if avisos:
        cartao = QWidget()
        cartao.setAttribute(DONT, True)
        v = QVBoxLayout(cartao)
        titulo = QLabel("Cadeado da arte — o aviso do gesto")
        titulo.setProperty("papel", "titulo")
        corpo = QLabel(avisos[0])
        corpo.setWordWrap(True)
        v.addWidget(titulo)
        v.addWidget(corpo)
        cartao.resize(560, 170)
        cartao.show()
        _grab(cartao, pasta, "cadeado_aviso.png")
        cartao.close()
    e.canvas.set_arte_travada(True)

    # GIF do fluxo (normal → raio-X → seleção)
    try:
        from PIL import Image
        pngs = [pasta / "editor_normal.png", pasta / "editor_raio_x.png",
                pasta / "editor_selecao.png"]
        imgs = [Image.open(p).convert("RGB") for p in pngs if p.exists()]
        if len(imgs) >= 2:
            imgs[0].save(pasta / "fluxo_agrupamento.gif", save_all=True,
                         append_images=imgs[1:], duration=1400, loop=0)
            print("  fluxo_agrupamento.gif")
    except Exception as exc:
        print("  (gif pulado:", exc, ")")

    e.close()
    print(f"galeria em {pasta}")
    from app.qt.workers import encerrar_todos
    encerrar_todos(espera_ms=1000)
    app.closeAllWindows()
    _processar()
    os._exit(0)


if __name__ == "__main__":
    raise SystemExit(main())

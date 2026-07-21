"""Testes do canvas base (F5.1) — offscreen. WYSIWYG: preview vem do compositor Pillow."""

from PIL import Image
from PySide6.QtWidgets import QApplication

from app.qt.canvas import CanvasView, EditorCanvas, pil_para_qpixmap
from app.rendering.compositor import DadosProduto
from app.rendering.model import LayoutDef, Pagina, Regiao, Retangulo, Slot, TipoRegiao


def _app():
    return QApplication.instance() or QApplication([])


def _layout():
    return LayoutDef(
        100, 100, dpi=100,
        paginas=[Pagina([Slot("s", [Regiao(TipoRegiao.NOME, Retangulo(10, 10, 80, 20))])])],
    )


def test_pil_para_qpixmap_preserva_tamanho():
    _app()
    pm = pil_para_qpixmap(Image.new("RGBA", (40, 30), (255, 0, 0, 255)))
    assert pm.width() == 40 and pm.height() == 30


def test_canvas_carrega_preview_do_compositor():
    _app()
    v = CanvasView()
    v.carregar(_layout(), DadosProduto("Teste"))
    assert v._bg is not None
    # 100 mm @ 100 dpi ≈ 394 px
    assert 380 < v.scene().sceneRect().width() < 410


def test_mm_roundtrip():
    _app()
    v = CanvasView()
    v.carregar(_layout(), DadosProduto("x"))
    cx, cy = v.mm_para_cena(50, 50)
    mx, my = v.cena_para_mm(cx, cy)
    assert abs(mx - 50) < 0.5 and abs(my - 50) < 0.5


def test_editor_canvas_monta_com_reguas():
    _app()
    ec = EditorCanvas()
    ec.carregar(_layout(), DadosProduto("y"))
    assert ec.canvas._bg is not None
    assert ec.regua_topo is not None and ec.regua_esq is not None

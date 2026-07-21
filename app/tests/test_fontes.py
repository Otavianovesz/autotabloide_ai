"""Testes do seletor de fontes (F5.7 essencial): bundled, cópia de sistema, trap do Pillow."""

import app.qt.fontes as fontes_mod
from app.qt.fontes import fontes_bundled


def test_bundled_inclui_quicksand_e_roboto():
    b = fontes_bundled()
    assert "Quicksand-Bold.ttf" in b
    assert "Roboto-Regular.ttf" in b


def test_garantir_em_fontes_copia_para_fontes(tmp_path, monkeypatch):
    origem = tmp_path / "MinhaFonte.ttf"
    origem.write_bytes(b"conteudo-fake-de-fonte")
    monkeypatch.setenv("AUTOTABLOIDE_ROOT", str(tmp_path / "root"))
    monkeypatch.setattr(fontes_mod, "_mapa_sistema", lambda: {"Minha — MinhaFonte": origem})

    nome = fontes_mod.garantir_em_fontes("Minha — MinhaFonte")
    assert nome == "MinhaFonte.ttf"
    assert (fontes_mod.dir_fontes() / "MinhaFonte.ttf").exists()


def test_painel_lista_quicksand_como_arquivo():
    from PySide6.QtWidgets import QApplication

    from app.qt.editor import Editor
    from app.rendering.compositor import DadosProduto
    from app.rendering.model import LayoutDef, Pagina, Regiao, Retangulo, Slot, TipoRegiao

    QApplication.instance() or QApplication([])
    e = Editor()
    lay = LayoutDef(100, 100, dpi=100,
                    paginas=[Pagina([Slot("s", [Regiao(TipoRegiao.NOME, Retangulo(10, 10, 80, 20))])])])
    e.carregar(lay, DadosProduto("x"))
    valores = [e.propriedades.fonte.itemData(i) for i in range(e.propriedades.fonte.count())]
    assert "Quicksand-Bold.ttf" in valores   # valor é o ARQUIVO (não o nome da família)

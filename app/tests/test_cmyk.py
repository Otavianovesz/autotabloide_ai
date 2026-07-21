"""F7.5 (Etapa E do Bloco E) — exportação CMYK opcional.

O teste-rei (E1): com o CMYK DESLIGADO — o padrão — o caminho RGB fica
byte-idêntico ao de sempre. O Ghostscript real do ambiente valida o
/DeviceCMYK e o tamanho físico; a ausência dele degrada COM aviso (I2).
"""

from decimal import Decimal
from pathlib import Path

from app.core.database import Database
from app.core.repositories import ConfigRepositorio
from app.rendering import cmyk
from app.rendering.cartaz import layout_cartaz_exemplo
from app.rendering.compositor import DadosProduto, compor_pagina
from app.rendering.export import exportar_pdf_multipagina
from app.tests import seeds_portabilidade as seeds


def _pdf_exportado(tmp_path) -> Path:
    lay = layout_cartaz_exemplo()
    dados = DadosProduto("Produto CMYK", preco_de=Decimal("4.99"),
                         preco_por=Decimal("3.99"))
    paginas = [compor_pagina(lay, lay.paginas[0], dados) for _ in range(2)]
    return exportar_pdf_multipagina(paginas, tmp_path / "saida.pdf", lay.dpi)


def _ligar_cmyk(root, perfil: str | None = None) -> None:
    db = Database(root).init()
    with db.Session() as s:
        cfg = ConfigRepositorio(s)
        cfg.set("export.cmyk_pdf", True)
        if perfil is not None:
            cfg.set("export.perfil_icc", perfil)
        s.commit()
    db.engine.dispose()


def test_e1_rei_rgb_desligado_fica_byte_identico(tmp_path):
    """Com o CMYK desligado (padrão), NENHUM byte do export muda."""
    root = seeds.raiz(tmp_path, "raiz")
    pdf = _pdf_exportado(tmp_path)
    antes = pdf.read_bytes()
    caminho, aviso = cmyk.pos_processar_export(pdf, raiz=root)
    assert caminho == pdf and aviso is None
    assert pdf.read_bytes() == antes            # byte-idêntico, literal
    # e PNG nunca é tocado, ligado ou não
    png = tmp_path / "x.png"
    png.write_bytes(b"png-fake")
    _ligar_cmyk(root)
    caminho2, aviso2 = cmyk.pos_processar_export(png, raiz=root)
    assert caminho2 == png and aviso2 is None
    assert png.read_bytes() == b"png-fake"


def test_e2_converte_devicecmyk_tamanho_intacto(tmp_path):
    """Ghostscript real do ambiente: /DeviceCMYK + página no MESMO tamanho."""
    from pypdf import PdfReader

    assert cmyk.ghostscript_disponivel() is not None, \
        "a ordem afirma o Ghostscript no ambiente — instale-o"
    root = seeds.raiz(tmp_path, "raiz")
    _ligar_cmyk(root)
    pdf = _pdf_exportado(tmp_path)
    antes = PdfReader(str(pdf))
    caixa_antes = (float(antes.pages[0].mediabox.width),
                   float(antes.pages[0].mediabox.height))
    n_antes = len(antes.pages)
    assert b"/DeviceCMYK" not in pdf.read_bytes()     # sanidade: era RGB

    caminho, aviso = cmyk.pos_processar_export(pdf, raiz=root)
    assert aviso and "CMYK" in aviso
    assert b"/DeviceCMYK" in caminho.read_bytes()
    depois = PdfReader(str(caminho))
    assert len(depois.pages) == n_antes
    assert abs(float(depois.pages[0].mediabox.width) - caixa_antes[0]) < 0.2
    assert abs(float(depois.pages[0].mediabox.height) - caixa_antes[1]) < 0.2


def test_e2_gs_ausente_degrada_com_aviso(tmp_path, monkeypatch):
    """Sem Ghostscript: o PDF fica em RGB, intocado, e o aviso conta (I2)."""
    root = seeds.raiz(tmp_path, "raiz")
    _ligar_cmyk(root)
    pdf = _pdf_exportado(tmp_path)
    antes = pdf.read_bytes()
    monkeypatch.setattr(cmyk, "ghostscript_disponivel", lambda: None)
    caminho, aviso = cmyk.pos_processar_export(pdf, raiz=root)
    assert caminho == pdf
    assert aviso and "RGB" in aviso and "Ghostscript" in aviso
    assert pdf.read_bytes() == antes            # nada foi tocado


def test_e2_perfil_icc_inexistente_converte_com_aviso(tmp_path):
    root = seeds.raiz(tmp_path, "raiz")
    _ligar_cmyk(root, perfil=str(tmp_path / "nao_existe.icc"))
    pdf = _pdf_exportado(tmp_path)
    caminho, aviso = cmyk.pos_processar_export(pdf, raiz=root)
    assert b"/DeviceCMYK" in caminho.read_bytes()     # converteu mesmo assim
    assert aviso and "perfil ICC" in aviso            # e avisou do perfil


def test_tela_configuracoes_salva_cmyk(tmp_path):
    from PySide6.QtWidgets import QApplication

    QApplication.instance() or QApplication([])
    from app.qt.telas.configuracoes import ConfiguracoesTela

    root = seeds.raiz(tmp_path, "raiz")
    tela = ConfiguracoesTela(raiz=root)
    assert not tela.campo_cmyk.isChecked()            # padrão: RGB (C3)
    tela.campo_cmyk.setChecked(True)
    tela.campo_icc.setText("C:/perfis/fogra39.icc")
    assert tela._salvar() is True
    db = Database(root).init()
    with db.Session() as s:
        cfg = ConfigRepositorio(s)
        assert cfg.get("export.cmyk_pdf") is True
        assert cfg.get("export.perfil_icc") == "C:/perfis/fogra39.icc"
    db.engine.dispose()

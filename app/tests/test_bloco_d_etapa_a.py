"""Etapa A do Bloco D — Fábrica ponta a ponta (ORDEM_BLOCO_D §A).

A1: preço "por" editável pela tela (campo + duplo-clique, paridade com a Mesa).
A2: pré-voo cartaz=True em TODOS os caminhos (exportar E salvar) — PROCON.
A3: gate da arte real — arte 10×15 do Illustrator (300 ppi gravado) entra sem
    ajuste de código e o PDF sai no tamanho físico EXATO (medido com pypdf).
A4: 1 item = 1 página; pré-voo rotulado por página do PDF, como na Mesa.
"""

from decimal import Decimal

from PIL import Image
from PySide6.QtWidgets import QApplication, QDialog

from app.qt.telas import servico
from app.rendering.cartaz import layout_cartaz_exemplo
from app.rendering.compositor import DadosProduto, compor_pagina
from app.rendering.export import exportar_pdf_multipagina
from app.rendering.model import layout_de_arte


def _tela():
    QApplication.instance() or QApplication([])
    from app.qt.telas.fabrica import FabricaTela
    return FabricaTela()


def _item(nome, por="3,99", de="4,99", **kw):
    return servico.ItemMesa(nome, por, "VERDE", nome, preco_de=de, **kw)


# --- A1: preço "por" editável pela tela ------------------------------------------


def test_a1_campo_por_edita_o_preco_do_item():
    f = _tela()
    f._itens = [servico.ItemMesa("A", None, "VERDE", "Produto A", preco_de="4,99")]
    f._recarregar_lista()
    assert not f._completo(f._itens[0])          # sem "por" = incompleto
    assert not f.btn_exportar.isEnabled()

    f.lista.setCurrentRow(0)
    f.campo_por.setText("3,99")
    f._editou_campos()
    assert f._itens[0].preco == "3,99"
    assert f._completo(f._itens[0])
    assert f.btn_exportar.isEnabled()


def test_a1_campos_refletem_o_item_selecionado():
    f = _tela()
    f._itens = [_item("Produto A", por="2,49", de="3,49"),
                _item("Produto B", por="7,90", de="9,90")]
    f._recarregar_lista()
    f.lista.setCurrentRow(1)
    assert f.campo_por.text() == "7,90"
    assert f.campo_de.text() == "9,90"


def test_a1_duplo_clique_edita_nome_e_por(monkeypatch):
    """Paridade com a edição rápida da Mesa (P1.4): nome + preço 'por'."""
    from PySide6.QtWidgets import QInputDialog

    f = _tela()
    f._itens = [_item("Produto A", por="3,99")]
    f._recarregar_lista()

    respostas = iter([("Cerveja Amstel 269ml", True), ("2,99", True)])
    monkeypatch.setattr(QInputDialog, "getText",
                        lambda *a, **kw: next(respostas))
    f._editar_item(f.lista.item(0))
    assert f._itens[0].nome == "Cerveja Amstel 269ml"
    assert f._itens[0].preco == "2,99"


def test_a1_duplo_clique_cancelado_nao_muda_nada(monkeypatch):
    from PySide6.QtWidgets import QInputDialog

    f = _tela()
    f._itens = [_item("Produto A", por="3,99")]
    f._recarregar_lista()
    monkeypatch.setattr(QInputDialog, "getText",
                        lambda *a, **kw: ("qualquer", False))
    f._editar_item(f.lista.item(0))
    assert f._itens[0].nome == "Produto A" and f._itens[0].preco == "3,99"


# --- A2: pré-voo cartaz=True nos DOIS caminhos (PROCON) ---------------------------


def _capturar_pre_voo(monkeypatch, resposta: bool):
    """Intercepta confirmar_pre_voo e devolve a lista onde os avisos caem."""
    import app.qt.telas.prevoo as prevoo
    capturados: list[str] = []

    def fake(parent, avisos, acao="Exportar"):
        capturados.extend(avisos)
        return resposta

    monkeypatch.setattr(prevoo, "confirmar_pre_voo", fake)
    return capturados


def test_a2_pre_voo_procon_no_exportar(monkeypatch):
    from PySide6.QtWidgets import QFileDialog

    f = _tela()
    # "de" MENOR que o "por" — a regra PROCON tem que acusar
    f._itens = [_item("Produto A", por="3,99", de="2,99")]
    f._recarregar_lista()
    capturados = _capturar_pre_voo(monkeypatch, resposta=False)
    monkeypatch.setattr(
        QFileDialog, "getSaveFileName",
        lambda *a, **kw: (_ for _ in ()).throw(
            AssertionError("cancelar o pré-voo tem que parar a exportação")))
    f._exportar()
    assert any("PROCON" in a for a in capturados)


def test_a2_pre_voo_procon_no_salvar_projeto(monkeypatch):
    import app.core.projetos as projetos
    import app.qt.telas.projetos_dialog as pd

    class DlgAceita:
        DialogCode = QDialog.DialogCode

        def __init__(self, parent=None):
            pass

        def exec(self):
            return QDialog.DialogCode.Accepted

        def valores(self):
            return ("Cartazes teste", "Avulsos")

    monkeypatch.setattr(pd, "SalvarProjetoDialog", DlgAceita)
    salvos = []
    monkeypatch.setattr(projetos, "salvar_projeto",
                        lambda *a, **kw: salvos.append(a))

    f = _tela()
    f._itens = [_item("Produto A", por="3,99", de="2,99")]
    f._recarregar_lista()

    # pré-voo recusado → NÃO salva (a pendência PROCON apareceu antes)
    capturados = _capturar_pre_voo(monkeypatch, resposta=False)
    f._salvar_projeto()
    assert any("PROCON" in a for a in capturados)
    assert salvos == []

    # pré-voo aceito → salva
    _capturar_pre_voo(monkeypatch, resposta=True)
    f._salvar_projeto()
    assert len(salvos) == 1


# --- A3: gate da arte real — DPI gravado + PDF no tamanho exato -------------------


def _arte_cartaz_300ppi(tmp_path):
    """Simula o export do Illustrator: 10×15 cm a 300 ppi = 1181×1772 px."""
    p = tmp_path / "cartaz_10x15.png"
    Image.new("RGB", (1181, 1772), "white").save(p, dpi=(300, 300))
    return p


def test_a3_layout_de_arte_le_o_dpi_gravado(tmp_path):
    ldef = layout_de_arte(str(_arte_cartaz_300ppi(tmp_path)))
    assert ldef.dpi == 300
    assert abs(ldef.largura_mm - 100) < 0.5     # 1181 px / 300 ppi = 99,99 mm
    assert abs(ldef.altura_mm - 150) < 0.5


def test_a3_sem_metadado_vale_96_e_dpi_explicito_vence(tmp_path):
    sem = tmp_path / "digital.png"
    Image.new("RGB", (1080, 1300), "white").save(sem)   # sem pHYs
    assert layout_de_arte(str(sem)).dpi == 96
    com = _arte_cartaz_300ppi(tmp_path)
    assert layout_de_arte(str(com), dpi=96).dpi == 96   # o chamador manda


def test_a3_fluxo_arte_real_na_fabrica_sem_ajuste(tmp_path):
    """Ateliê (tipo CARTAZ, sem detecção de grade) → Fábrica → PDF exato."""
    from pypdf import PdfReader

    arte = _arte_cartaz_300ppi(tmp_path)
    ldef = layout_de_arte(str(arte))                     # o caminho do Ateliê
    # regiões posicionadas "no editor" (as do cartaz cabem: mm ≈ os mesmos)
    ldef.paginas[0].slots[0].regioes = \
        layout_cartaz_exemplo().paginas[0].slots[0].regioes

    # a Fábrica aceita o layout e compõe o preview sem ajuste de código
    f = _tela()
    f.carregar_layout(ldef, "Cartaz 10×15 (arte real)")
    f._itens = [_item("Produto 1"), _item("Produto 2")]
    f._recarregar_lista()
    f.lista.setCurrentRow(0)
    assert f.preview.pixmap() is not None and not f.preview.pixmap().isNull()

    # composição 1:1 com a arte — SEM reamostragem que distorça
    dados = DadosProduto("Produto 1", preco_de=Decimal("4.99"),
                         preco_por=Decimal("3.99"))
    img = compor_pagina(ldef, ldef.paginas[0], dados)
    assert img.size == (1181, 1772)

    # A4 junto: 2 itens = 2 páginas; página medida com pypdf (mm do layout)
    pdf = exportar_pdf_multipagina([img, img], tmp_path / "cartazes.pdf", ldef.dpi)
    leitor = PdfReader(str(pdf))
    assert len(leitor.pages) == 2
    caixa = leitor.pages[0].mediabox                     # pontos (1/72")
    larg_pt = ldef.largura_mm / 25.4 * 72
    alt_pt = ldef.altura_mm / 25.4 * 72
    assert abs(float(caixa.width) - larg_pt) < 0.2       # exato ao layout
    assert abs(float(caixa.height) - alt_pt) < 0.2
    assert abs(float(caixa.width) - 100 / 25.4 * 72) < 1.5   # e é o 10×15 real
    assert abs(float(caixa.height) - 150 / 25.4 * 72) < 1.5


# --- A4: pré-voo rotula por página do PDF ----------------------------------------


def test_a4_pre_voo_rotula_pagina_e_fora_do_pdf():
    f = _tela()
    f._itens = [_item("Produto A"),                      # página 1 (sem foto)
                servico.ItemMesa("B", "5,50", "VERDE", "Produto B"),  # sem "de"
                _item("Produto C")]                      # página 2
    f._recarregar_lista()
    avisos = f._avisos_pre_voo()
    assert any(a.startswith("página 1") and "Produto A" in a and "sem foto" in a
               for a in avisos)
    assert any(a.startswith("fora do PDF") and "Produto B" in a
               and "sem preço “de”" in a for a in avisos)
    assert any(a.startswith("página 2") and "Produto C" in a for a in avisos)
    # nenhum rótulo de página pulou/repetiu: 1 item exportável = 1 página
    paginas = sorted({a.split(",")[0].split(" (")[0] for a in avisos
                      if a.startswith("página")})
    assert paginas == ["página 1", "página 2"]

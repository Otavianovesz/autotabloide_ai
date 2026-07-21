"""Testes da Fábrica (F6.5) — cartaz: de/por riscado, PDF multipágina, tela."""

from decimal import Decimal
from pathlib import Path

from PySide6.QtWidgets import QApplication

from app.qt.telas import servico
from app.rendering.cartaz import layout_cartaz_exemplo
from app.rendering.compositor import DadosProduto, compor_pagina
from app.rendering.export import exportar_pdf_multipagina
from app.rendering.model import PapelPreco, TipoRegiao


def _dados(nome="Cerveja Amstel 269ml", de="3,99", por="2,99", validade=None):
    return DadosProduto(
        nome,
        preco_de=Decimal(de.replace(",", ".")) if de else None,
        preco_por=Decimal(por.replace(",", ".")),
        texto_legal=f"Válido até {validade}" if validade else None,
    )


def test_layout_cartaz_tem_de_riscado_e_por():
    lay = layout_cartaz_exemplo()
    regioes = lay.paginas[0].slots[0].regioes
    de = next(r for r in regioes if r.papel_preco == PapelPreco.DE)
    por = next(r for r in regioes if r.papel_preco == PapelPreco.POR)
    assert de.riscado and not por.riscado
    assert any(r.tipo == TipoRegiao.TEXTO_LEGAL for r in regioes)


def test_riscado_muda_a_composicao():
    lay = layout_cartaz_exemplo()
    de = next(r for r in lay.paginas[0].slots[0].regioes
              if r.papel_preco == PapelPreco.DE)
    com = compor_pagina(lay, lay.paginas[0], _dados())
    de.riscado = False
    sem = compor_pagina(lay, lay.paginas[0], _dados())
    assert list(com.getdata()) != list(sem.getdata())   # o traço apareceu


def test_validade_do_item_entra_no_cartaz():
    lay = layout_cartaz_exemplo()
    com = compor_pagina(lay, lay.paginas[0], _dados(validade="15/07"))
    sem = compor_pagina(lay, lay.paginas[0], _dados())
    assert list(com.getdata()) != list(sem.getdata())


def test_pdf_multipagina_uma_pagina_por_cartaz(tmp_path):
    from pypdf import PdfReader

    lay = layout_cartaz_exemplo()
    paginas = [compor_pagina(lay, lay.paginas[0], _dados(nome=f"Produto {i}"))
               for i in range(3)]
    pdf = exportar_pdf_multipagina(paginas, tmp_path / "cartazes.pdf", lay.dpi)
    leitor = PdfReader(str(pdf))
    assert len(leitor.pages) == 3
    caixa = leitor.pages[0].mediabox            # 100×150 mm em pontos (1/72")
    assert abs(float(caixa.width) - 100 / 25.4 * 72) < 1.5
    assert abs(float(caixa.height) - 150 / 25.4 * 72) < 1.5


def test_fabrica_tela_completude_e_preview():
    QApplication.instance() or QApplication([])
    from app.qt.telas.fabrica import FabricaTela

    f = FabricaTela()
    f._itens = [
        servico.ItemMesa("A", "2,99", "VERDE", "Produto A", preco_de="3,99"),
        servico.ItemMesa("B", "5,50", "VERDE", "Produto B"),     # sem o "de"
    ]
    f._recarregar_lista()
    assert f.btn_exportar.isEnabled()            # 1 pronto já libera
    assert f._completo(f._itens[0]) and not f._completo(f._itens[1])

    f.lista.setCurrentRow(0)                     # preview ao clicar
    assert f.preview.pixmap() is not None and not f.preview.pixmap().isNull()

    # completar o "de" pelo campo torna o item pronto
    f.lista.setCurrentRow(1)
    f.campo_de.setText("6,99")
    f._editou_campos()
    assert f._completo(f._itens[1])

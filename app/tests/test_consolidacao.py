"""Testes do checkpoint de consolidação: justificado, unidade automática,
texto legal, persistência de layout e o gate sobre a arte real."""

from decimal import Decimal

import pytest

from app.core.database import Database
from app.core.paths import SystemRoot
from app.rendering.compositor import DadosProduto, compor_pagina
from app.rendering.model import (
    Alinhamento,
    LayoutDef,
    Pagina,
    Regiao,
    Retangulo,
    Slot,
    TipoRegiao,
)
from app.rendering.persistencia import carregar_layout, listar_layouts, salvar_layout
from app.rendering.units import mm_para_px

TEXTO = "um dois tres quatro cinco seis sete oito nove dez"


def _layout_nome(alinhamento, w=50):
    return LayoutDef(
        100, 40, dpi=100,
        paginas=[Pagina([Slot("s", [
            Regiao(TipoRegiao.NOME, Retangulo(2, 2, w, 36), tamanho_max_pt=22, alinhamento=alinhamento)
        ])])],
    )


def test_justificado_muda_a_composicao():
    le = _layout_nome(Alinhamento.ESQUERDA)
    lj = _layout_nome(Alinhamento.JUSTIFICADO)
    ie = compor_pagina(le, le.paginas[0], DadosProduto(TEXTO))
    ij = compor_pagina(lj, lj.paginas[0], DadosProduto(TEXTO))
    assert ie.tobytes() != ij.tobytes()


def test_unidade_anexa_ao_nome_sem_regiao_unidade():
    lay = LayoutDef(120, 30, dpi=100,
                    paginas=[Pagina([Slot("s", [Regiao(TipoRegiao.NOME, Retangulo(2, 2, 116, 26))])])])
    com = compor_pagina(lay, lay.paginas[0], DadosProduto("Arroz", unidade="1kg"))
    sem = compor_pagina(lay, lay.paginas[0], DadosProduto("Arroz", unidade=None))
    assert com.tobytes() != sem.tobytes()   # a unidade entrou no nome


def test_unidade_fora_do_nome_com_regiao_unidade():
    lay = LayoutDef(120, 30, dpi=100, paginas=[Pagina([Slot("s", [
        Regiao(TipoRegiao.NOME, Retangulo(2, 2, 70, 26)),
        Regiao(TipoRegiao.UNIDADE, Retangulo(74, 2, 44, 26)),
    ])])])
    i1 = compor_pagina(lay, lay.paginas[0], DadosProduto("Arroz", unidade="1kg"))
    i2 = compor_pagina(lay, lay.paginas[0], DadosProduto("Arroz", unidade="9kg"))
    nx0, nx1 = round(mm_para_px(2, 100)), round(mm_para_px(72, 100))
    # o NOME não muda com a unidade (unidade vai na região própria)
    assert i1.crop((nx0, 0, nx1, i1.height)).tobytes() == i2.crop((nx0, 0, nx1, i2.height)).tobytes()


def test_texto_legal_desenhado():
    lay = LayoutDef(120, 30, dpi=100,
                    paginas=[Pagina([Slot("s", [Regiao(TipoRegiao.TEXTO_LEGAL, Retangulo(2, 2, 116, 26))])])])
    com = compor_pagina(lay, lay.paginas[0], DadosProduto("x", texto_legal="Ofertas válidas até 26/05"))
    sem = compor_pagina(lay, lay.paginas[0], DadosProduto("x", texto_legal=None))
    assert com.tobytes() != sem.tobytes()


@pytest.fixture
def session(tmp_path):
    db = Database(SystemRoot(tmp_path / "r")).init()
    s = db.Session()
    try:
        yield s
    finally:
        s.close()
        db.engine.dispose()


def test_salvar_e_carregar_layout(session):
    lay = LayoutDef(100, 150, dpi=96, arquivo_fundo="arte.png", paginas=[Pagina([Slot("s", [
        Regiao(TipoRegiao.PRECO, Retangulo(1, 2, 3, 4), nome="Preço", mostrar_moeda=False)
    ])])])
    row = salvar_layout(session, "Cartaz Teste", lay)
    session.commit()
    recuperado = carregar_layout(session, row.id)
    assert recuperado.to_dict() == lay.to_dict()
    assert len(listar_layouts(session)) == 1


def test_salvar_mesmo_nome_atualiza(session):
    lay = LayoutDef(100, 150, dpi=96, paginas=[Pagina([Slot("s", [])])])
    salvar_layout(session, "X", lay)
    salvar_layout(session, "X", lay)
    session.commit()
    assert len(listar_layouts(session)) == 1  # atualizou, não duplicou


def test_gate_compoe_sobre_arte_real_1080x1300():
    from app.rendering.model import layout_de_arte
    from app.scripts.gate_fidelidade import ARTE, DPI, celula_superior_esquerda

    layout = layout_de_arte(ARTE, dpi=DPI)
    layout.paginas[0].slots[0].regioes = celula_superior_esquerda(DPI)
    img = compor_pagina(layout, layout.paginas[0], DadosProduto("Teste", preco_por=Decimal("0.19")))
    assert img.size == (1080, 1300)

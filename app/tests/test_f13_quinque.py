"""ORDEM F13-QUINQUE — ENTREGUE NO APP (L10: a prova de pronto é a
lista do Ateliê na máquina do dono, nunca um PNG numa pasta).

Seis rodadas compuseram em memória e o banco real ficou com os 9
layouts antigos. Estes testes travam o conserto estrutural: a camada
do dono interna/resolve como toda arte (I3), o botão do Ateliê importa
por GESTO e prova por CONTEÚDO, e a célula do Jornal denso cumpre a
régua de ≥55% de foto POR NÚMERO.
"""

from pathlib import Path

import pytest
from PIL import Image

from app.tests import acervo

_PACOTE = Path(__file__).resolve().parents[2] / "Templates novos"


@pytest.fixture()
def raiz_tmp(tmp_path, monkeypatch):
    monkeypatch.setenv("AUTOTABLOIDE_ROOT", str(tmp_path / "raiz"))
    from app.core.paths import SystemRoot
    root = SystemRoot(tmp_path / "raiz").criar_estrutura()
    acervo.copiar_fontes_reais(root.fontes)
    return root


def _requer_pacote():
    if not _PACOTE.exists():
        pytest.skip("REQUER ACERVO DO DONO: a pasta 'Templates novos/'")


def test_a1_camada_interna_e_resolve_como_toda_arte(raiz_tmp):
    """A1/I3: ``Pagina.arquivo_camada`` (a arte de preço do dono) é
    INTERNADA no salvar (cópia em layouts/, caminho relativo no JSON —
    nada da pasta do pacote vaza) e RESOLVIDA no carregar. Sem isso, o
    layout importado quebraria em outra máquina."""
    _requer_pacote()
    from app.core.database import Database
    from app.rendering.encartes import layout_de_encarte
    from app.rendering.persistencia import carregar_layout, salvar_layout

    lay = layout_de_encarte("quintou", _PACOTE)
    db = Database().init()
    try:
        with db.Session() as s:
            row = salvar_layout(s, "Quintou QQ", lay, raiz=raiz_tmp)
            s.commit()
            assert "Templates novos" not in (row.estrutura_json or ""), (
                "o caminho da pasta do pacote vazou no JSON — a CAMADA "
                "não foi internada (I3)")
            volta = carregar_layout(s, row.id, raiz=raiz_tmp)
    finally:
        db.engine.dispose()
    for n, pag in enumerate(volta.paginas, start=1):
        assert pag.arquivo_camada, f"p{n}: a camada sumiu no roundtrip"
        assert Path(pag.arquivo_camada).exists(), (
            f"p{n}: a camada resolvida não existe no disco "
            f"({pag.arquivo_camada})")
        assert str(raiz_tmp.layouts) in str(pag.arquivo_camada), (
            f"p{n}: a camada não resolve para a pasta gerenciada")


def test_a1_galeria_compoe_do_banco_pela_porta(raiz_tmp):
    """A1/L10: o caminho da GALERIA é o caminho do PRODUTO —
    importar_pacote (a porta do botão) → carregar_layout (o banco) →
    compor. A inspeção usa exatamente este helper; se o import falhar,
    a galeria falha — e é isso que se quer."""
    _requer_pacote()
    from app.scripts.inspecao_encartes import layout_do_banco

    lay, layout_id = layout_do_banco("quintou", _PACOTE, raiz_tmp)
    assert layout_id is not None, "o layout não veio do BANCO"
    assert len(lay.paginas) == 2
    assert lay.paginas[0].arquivo_camada and \
        Path(lay.paginas[0].arquivo_camada).exists()
    from app.rendering.compositor import DadosProduto, compor_pagina
    img = compor_pagina(lay, lay.paginas[0],
                        {"pos-01": DadosProduto("Prova")})
    assert img.width > 0


def test_a4_botao_do_atelie_importa_por_gesto(raiz_tmp, monkeypatch):
    """A4/L2: clicar o BOTÃO real do Ateliê, apontar a pasta e provar
    por CONTEÚDO — os 8 encartes no banco (nomes) e um deles ABRE
    (carregar_layout devolve as páginas). "Chamar importar_pacote não
    prova que o botão funciona"."""
    _requer_pacote()
    from PySide6.QtWidgets import QApplication, QFileDialog

    _ = QApplication.instance() or QApplication([])
    from app.core.database import Database
    from app.qt.telas.atelie import AtelieTela
    from app.rendering.encartes import NOMES_EXIBICAO
    from app.rendering.persistencia import carregar_layout, listar_layouts
    from app.tests.gestos import acionar

    monkeypatch.setattr(
        QFileDialog, "getExistingDirectory",
        staticmethod(lambda *a, **k: str(_PACOTE)))
    avisos: list[tuple] = []
    from app.qt.telas import atelie as mod
    for nome_caixa in ("mostrar_toast",):
        if hasattr(mod, nome_caixa):
            monkeypatch.setattr(
                mod, nome_caixa,
                lambda *a, **k: avisos.append(a), raising=False)

    tela = AtelieTela()
    try:
        botao = next(b for b in tela.findChildren(type(tela.findChild(
            __import__("PySide6.QtWidgets", fromlist=["QPushButton"])
            .QPushButton)))
            if "Importar encartes" in (b.text() or ""))
        acionar(botao)
        db = Database().init()
        try:
            with db.Session() as s:
                nomes = {r.nome for r in listar_layouts(s)}
                assert set(NOMES_EXIBICAO.values()) <= nomes, (
                    f"faltou encarte no banco após o GESTO: {nomes}")
                alvo = next(r for r in listar_layouts(s)
                            if r.nome == NOMES_EXIBICAO["quintou"])
                lay = carregar_layout(s, alvo.id)
                assert lay is not None and len(lay.paginas) == 2, (
                    "o encarte importado pelo botão não ABRE")
        finally:
            db.engine.dispose()
    finally:
        tela.deleteLater()


def test_j10_regra_dos_55_por_cento_de_foto():
    """J10–J13 (a régua aferível do §5): no Jornal denso (4 colunas), a
    FOTO de cada célula do fluxo ocupa ≥ 55% da área da célula — é
    número, não gosto. Cabeçalho de seção ≤ 28 px."""
    _requer_pacote()
    from app.rendering.encartes import _FAIXAS_JORNAL, layout_de_encarte
    from app.rendering.model import TipoRegiao

    assert all(f["colunas"] == (4,) for _pg, f in _FAIXAS_JORNAL[:2]), (
        "o miolo do Jornal denso é de 4 COLUNAS (célula 25% mais larga)")
    assert all(f.get("altura_cabecalho", 28) <= 28
               for _pg, f in _FAIXAS_JORNAL), "cabeçalho ≤ 28 px (J12)"

    lay = layout_de_encarte("jornal-do-mes", _PACOTE,
                            secoes=[("Mercearia", 8), ("Bebidas", 4)])
    celulas = [s for p in lay.paginas for s in p.slots
               if s.id.startswith("jf-")]
    assert celulas, "o fluxo não gerou células"
    for s in celulas:
        foto = next(r for r in s.regioes if r.tipo == TipoRegiao.IMAGEM)
        xs = [r.rect.x_mm for r in s.regioes]
        ys = [r.rect.y_mm for r in s.regioes]
        x2 = [r.rect.x_mm + r.rect.larg_mm for r in s.regioes]
        y2 = [r.rect.y_mm + r.rect.alt_mm for r in s.regioes]
        area_cel = (max(x2) - min(xs)) * (max(y2) - min(ys))
        area_foto = foto.rect.larg_mm * foto.rect.alt_mm
        fr = area_foto / area_cel
        assert fr >= 0.55, (
            f"{s.id}: a foto ocupa {fr:.0%} da célula — a régua do §5 "
            "manda ≥ 55%")

"""ORDEM F13-OCTAVUS — O TESTE DO CELULAR (os 2 últimos da Segunda).

C1: o corpo tem PISO (o WhatsApp reduz a 37% — nome ≥30px de linha em
1080) e a página é UNIFORME (≤1,3× entre células). C2: o descritor de
volta. C3: o selo escreve SÓ a data no miolo medido da arte.
"""

from pathlib import Path

import pytest

_PACOTE = Path(__file__).resolve().parents[2] / "Templates novos"


def _requer_pacote():
    if not _PACOTE.exists():
        pytest.skip("REQUER ACERVO DO DONO: a pasta 'Templates novos/'")


def test_c1_piso_do_tipo_e_uniformidade_na_segunda():
    """C1: nas células de produto da Segunda, o corpo do nome tem tam
    ≥19pt com PISO (tamanho_min_pt) ≥17pt — o auto-ajuste nunca desce
    ao ilegível — e a página é UNIFORME: o maior corpo ≤1,3× o menor
    (estava em 2,2×)."""
    _requer_pacote()
    from app.rendering.encartes import layout_de_encarte
    from app.rendering.grade import ocupaveis
    from app.rendering.model import TipoRegiao

    lay = layout_de_encarte("segunda-frios", _PACOTE)
    tams = []
    for s in ocupaveis(lay.paginas[0].slots):
        nome = next(r for r in s.regioes if r.tipo == TipoRegiao.NOME)
        assert nome.tamanho_min_pt >= 17.0, (
            f"{s.id}: piso {nome.tamanho_min_pt}pt — o teste do "
            "celular exige ≥17 (linha ≥~26px em 1080)")
        assert nome.tamanho_max_pt >= 19.0, (
            f"{s.id}: corpo {nome.tamanho_max_pt}pt abaixo do alvo")
        tams.append(nome.tamanho_max_pt)
    assert max(tams) / min(tams) <= 1.3, (
        f"a página não é uniforme: {max(tams)}/{min(tams)} > 1,3×")


def test_c1_o_texto_fit_respeita_o_piso(raiz_tmp=None, tmp_path=None):
    """C1.1: o corpo mínimo é INVIOLÁVEL — texto que não cabe no piso
    TRUNCA com reticências (o pré-voo acusa), nunca encolhe abaixo."""
    from app.tests import acervo
    import tempfile

    fontes = Path(tempfile.mkdtemp()) / "fontes"
    fontes.mkdir()
    acervo.copiar_fontes_reais(fontes)
    from app.rendering.text_fit import ajustar_texto

    aj = ajustar_texto(
        "Um nome comprido demais para caber nesta caixa apertada",
        fontes / "Roboto-Bold.ttf", larg_px=120, alt_px=30,
        tamanho_max_pt=20.0, dpi=96, tamanho_min_pt=18.0)
    assert aj.tamanho_pt >= 18.0, (
        f"o corpo desceu a {aj.tamanho_pt}pt — o piso é inviolável")


def test_c2_o_descritor_esta_de_volta_na_segunda():
    """C2: toda célula de produto da Segunda tem a região SUBTITULO —
    a 2ª linha do modelo (é ela que permite encurtar o nome no passo 5
    do C1)."""
    _requer_pacote()
    from app.rendering.encartes import layout_de_encarte
    from app.rendering.grade import ocupaveis
    from app.rendering.model import TipoRegiao

    lay = layout_de_encarte("segunda-frios", _PACOTE)
    for s in ocupaveis(lay.paginas[0].slots):
        assert any(r.tipo == TipoRegiao.SUBTITULO for r in s.regioes), (
            f"{s.id}: sem a região do DESCRITOR (C2)")


def test_c3_o_selo_escreve_so_a_data():
    """C3: a região do selo é SÓ-DATA — de "Ofertas válidas SOMENTE
    27/07" ela escreve "27/07" (o resto está GRAVADO em curva na
    arte); sem data no texto, cai no completo (nunca em silêncio)."""
    from app.rendering.compositor import DadosProduto, texto_composto_legal
    from app.rendering.model import (
        PapelTexto,
        Regiao,
        Retangulo,
        TipoRegiao,
    )

    reg = Regiao(TipoRegiao.TEXTO_LEGAL, Retangulo(0, 0, 30, 8),
                 papel_texto=PapelTexto.VALIDADE, so_data=True)
    d = DadosProduto("", texto_legal="Ofertas válidas SOMENTE 27/07")
    assert texto_composto_legal(reg, d) == "27/07"
    d2 = DadosProduto("", texto_legal="enquanto durarem os estoques")
    assert texto_composto_legal(reg, d2) == \
        "enquanto durarem os estoques"          # guarda: sem data, completo

    _requer_pacote()
    from app.rendering.encartes import layout_de_encarte
    lay = layout_de_encarte("segunda-frios", _PACOTE)
    selo = next(s for s in lay.paginas[0].slots
                if s.id == "selo-validade")
    assert selo.regioes[0].so_data, "o selo da Segunda não é SÓ-DATA"
    # o roundtrip preserva (aditivo)
    from app.rendering.model import Regiao as _R
    volta = _R.from_dict(selo.regioes[0].to_dict())
    assert volta.so_data is True

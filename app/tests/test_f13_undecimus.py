"""ORDEM F13-UNDECIMUS — a regra não pode ser dado.

115 de 123 regiões de NOME no banco do dono estavam com o piso inerte:
a calibração vivia nas TABELAS do encartes.py e o artefato importado
ficou velho (a QUINQUE pela 4ª vez). U1: o piso do celular vira REGRA
DE RUNTIME — calculado da geometria da página na hora de compor;
``Regiao.tamanho_min_pt`` vira override opcional (só vale se MAIOR que
a regra); o 6.0 velho deixa de ser consultado. U2: pacote atualizado
avisa no Ateliê.
"""

from pathlib import Path

import pytest

_PACOTE = Path(__file__).resolve().parents[2] / "Templates novos"


def _requer_pacote():
    if not _PACOTE.exists():
        pytest.skip("REQUER ACERVO DO DONO: a pasta 'Templates novos/'")


def _fontes_reais(tmp_path):
    from app.tests import acervo
    fontes = tmp_path / "fontes"
    fontes.mkdir(exist_ok=True)
    acervo.copiar_fontes_reais(fontes)
    return fontes


@pytest.fixture()
def raiz_tmp(tmp_path, monkeypatch):
    monkeypatch.setenv("AUTOTABLOIDE_ROOT", str(tmp_path / "raiz"))
    from app.core.database import Database
    from app.core.paths import SystemRoot
    from app.tests import acervo
    root = SystemRoot(tmp_path / "raiz").criar_estrutura()
    acervo.copiar_fontes_reais(root.fontes)
    Database(root).init().engine.dispose()
    return root


# ---------------------------------------------------------------------------
# U1 — o piso do celular é REGRA de runtime
# ---------------------------------------------------------------------------


def test_u1_a_regua_do_celular():
    """U1: piso_pt = f(largura da página, fator 0,37 do WhatsApp, 11px
    mínimos) — e a régua REPRODUZ a calibração aprovada da Segunda
    (~17pt na página de 285,75 mm), que foi feita no olho e no pixel.
    Página menor, piso menor; nunca abaixo do 6 histórico."""
    from app.rendering.text_fit import piso_do_celular

    piso = piso_do_celular(285.75)          # a página dos encartes
    assert 16.2 <= piso <= 17.4, f"a régua não bate com o C1: {piso}"
    a4 = piso_do_celular(210.0)             # cartaz A4
    assert a4 < piso
    assert piso_do_celular(80.0) >= 6.0     # etiqueta: o chão histórico
    assert piso_do_celular(0) >= 6.0        # lixo não derruba a régua


def test_u1_o_dado_velho_deixa_de_ser_consultado(tmp_path):
    """U1 (o cerne): uma região NOME com o 6.0 INERTE do banco velho
    compõe BYTE-IDÊNTICA à mesma região calibrada a 17 — a regra de
    runtime venceu o dado, e reimportar deixou de ser pré-requisito."""
    from dataclasses import replace

    from app.rendering.compositor import DadosProduto, compor_pagina
    from app.rendering.model import (
        LayoutDef, Pagina, Regiao, Retangulo, Slot, TipoRegiao,
    )
    from app.rendering.units import px_para_mm

    fontes = _fontes_reais(tmp_path)
    dpi = 96

    def _r(x, y, w, h):
        return Retangulo(px_para_mm(x, dpi), px_para_mm(y, dpi),
                         px_para_mm(w, dpi), px_para_mm(h, dpi))

    def _lay(min_pt):
        nome = Regiao(TipoRegiao.NOME, _r(60, 900, 200, 64),
                      fonte="Roboto-Bold.ttf", tamanho_max_pt=19.0,
                      tamanho_min_pt=min_pt, sem_hifen=True)
        sub = Regiao(TipoRegiao.SUBTITULO, _r(60, 968, 200, 18),
                     fonte="Roboto-Regular.ttf", tamanho_max_pt=11.0)
        # uid estável entre as duas variantes (senão o byte diverge à toa)
        nome = replace(nome, uid="u1-nome")
        sub = replace(sub, uid="u1-sub")
        return LayoutDef(285.75, 381.0, dpi=192, paginas=[Pagina([
            Slot("c", [nome, sub])])])

    d = {"c": DadosProduto("Salsicha Hot Dog Rezende Especial")}
    velho = compor_pagina(_lay(6.0), _lay(6.0).paginas[0], d,
                          fontes_dir=fontes, dpi=dpi)
    novo = compor_pagina(_lay(17.0), _lay(17.0).paginas[0], d,
                         fontes_dir=fontes, dpi=dpi)
    assert velho.tobytes() == novo.tobytes(), (
        "o 6.0 do banco velho ainda é consultado — a régua não virou "
        "regra de runtime (U1)")


def test_u1_override_maior_que_a_regra_continua_valendo(tmp_path):
    """U1: quem calibrar um piso MAIOR que a régua (a fixa do Kit a 21)
    continua mandando — override para cima vale; para baixo, não."""
    from dataclasses import replace

    from app.rendering.compositor import DadosProduto, compor_pagina
    from app.rendering.model import (
        LayoutDef, Pagina, Regiao, Retangulo, Slot, TipoRegiao,
    )
    from app.rendering.units import px_para_mm

    fontes = _fontes_reais(tmp_path)
    dpi = 96

    def _r(x, y, w, h):
        return Retangulo(px_para_mm(x, dpi), px_para_mm(y, dpi),
                         px_para_mm(w, dpi), px_para_mm(h, dpi))

    def _lay(min_pt, max_pt=24.0):
        nome = replace(Regiao(TipoRegiao.NOME, _r(60, 900, 170, 40),
                              fonte="Roboto-Bold.ttf",
                              tamanho_max_pt=max_pt,
                              tamanho_min_pt=min_pt, sem_hifen=True),
                       uid="u1o-nome")
        sub = replace(Regiao(TipoRegiao.SUBTITULO, _r(60, 944, 170, 18),
                             fonte="Roboto-Regular.ttf",
                             tamanho_max_pt=11.0), uid="u1o-sub")
        return LayoutDef(285.75, 381.0, dpi=192, paginas=[Pagina([
            Slot("c", [nome, sub])])])

    d = {"c": DadosProduto("Linguiça Toscana Aurora Temperada")}
    com_regra = compor_pagina(_lay(6.0), _lay(6.0).paginas[0], d,
                              fontes_dir=fontes, dpi=dpi)
    com_override = compor_pagina(_lay(21.0), _lay(21.0).paginas[0], d,
                                 fontes_dir=fontes, dpi=dpi)
    assert com_regra.tobytes() != com_override.tobytes(), (
        "o override 21 (> régua ~17) foi ignorado — o piso maior tem "
        "de continuar mandando")


# ---------------------------------------------------------------------------
# U2 — pacote desatualizado avisa (e o dado velho se corrige por 1 clique)
# ---------------------------------------------------------------------------


def test_u2_o_carimbo_do_pacote_muda_quando_a_arte_muda(tmp_path):
    """U2: o carimbo é determinístico e sente arte/gerador tocados."""
    from app.rendering.encartes import versao_do_pacote

    pac = tmp_path / "pacote"
    (pac / "artes").mkdir(parents=True)
    (pac / "artes" / "x-BASE.png").write_bytes(b"png1")
    (pac / "geradores").mkdir()
    (pac / "geradores" / "gen.py").write_text("# v1")
    v1 = versao_do_pacote(pac)
    assert v1 == versao_do_pacote(pac), "o carimbo não é determinístico"
    import os
    import time
    os.utime(pac / "artes" / "x-BASE.png",
             ns=(time.time_ns(), time.time_ns() + 999))
    assert versao_do_pacote(pac) != v1, "arte tocada não mudou o carimbo"


def test_u2_o_atelie_avisa_e_o_botao_atualiza(raiz_tmp, monkeypatch):
    """U2 por gesto: import → sem aviso; gerador tocado → o aviso
    aparece no Ateliê; o botão reimporta e o aviso some. O mtime do
    arquivo do acervo é RESTAURADO no fim (só metadado, nunca conteúdo)."""
    _requer_pacote()
    import os

    from app.core.database import Database
    from app.qt.telas.atelie import AtelieTela
    from app.rendering.encartes import importar_pacote, pacote_desatualizado
    from app.tests.gestos import clicar, drenar
    from PySide6.QtWidgets import QApplication
    _ = QApplication.instance() or QApplication([])

    db = Database().init()
    try:
        with db.Session() as s:
            importar_pacote(s, _PACOTE, raiz=raiz_tmp)
            s.commit()
    finally:
        db.engine.dispose()
    assert pacote_desatualizado() is None, "recém-importado já acusa?"

    alvo = next((_PACOTE / "geradores").glob("*.py"))
    st = alvo.stat()
    try:
        os.utime(alvo, ns=(st.st_atime_ns, st.st_mtime_ns + 1_000_000))
        assert pacote_desatualizado() == str(_PACOTE.resolve())

        from PySide6.QtCore import Qt
        tela = AtelieTela()
        tela.setAttribute(Qt.WidgetAttribute.WA_DontShowOnScreen, True)
        tela.show()
        drenar()
        try:
            assert tela._aviso_pacote.isVisibleTo(tela), \
                "o Ateliê não avisou o pacote desatualizado"
            clicar(tela._btn_atualizar_pacote)
            drenar()
            assert pacote_desatualizado() is None, \
                "o botão não re-carimbou o pacote"
            assert not tela._aviso_pacote.isVisibleTo(tela), \
                "o aviso não sumiu depois de atualizar"
        finally:
            tela.deleteLater()
            drenar()
    finally:
        os.utime(alvo, ns=(st.st_atime_ns, st.st_mtime_ns))


def test_u1_a_terca_do_banco_velho_compoe_no_piso(tmp_path):
    """U1 no caso que motivou a ordem: a Terça com as 6 regiões de NOME
    em 6.0 (o artefato velho) compõe com o MESMO resultado do layout
    calibrado da fábrica — sem reimportar nada."""
    _requer_pacote()
    import json

    from app.rendering.compositor import DadosProduto, compor_pagina
    from app.rendering.encartes import layout_de_encarte
    from app.rendering.model import LayoutDef, TipoRegiao

    fontes = _fontes_reais(tmp_path)
    lay = layout_de_encarte("terca-do-pao", _PACOTE)
    # o "banco velho": o mesmo layout com TODOS os pisos de NOME em 6.0
    velho = LayoutDef.from_dict(json.loads(json.dumps(lay.to_dict())))
    for pag in velho.paginas:
        for s in pag.slots:
            for r in s.regioes:
                if r.tipo == TipoRegiao.NOME:
                    r.tamanho_min_pt = 6.0

    d = {"celula-3": DadosProduto(
        "Salsicha Hot Dog Rezende Tradicional Defumada Especial")}
    img_novo = compor_pagina(lay, lay.paginas[0], d,
                             fontes_dir=fontes, dpi=96)
    img_velho = compor_pagina(velho, velho.paginas[0], d,
                              fontes_dir=fontes, dpi=96)
    assert img_novo.tobytes() == img_velho.tobytes(), (
        "o artefato velho da Terça compõe DIFERENTE do calibrado — a "
        "régua de runtime não alcançou o banco do dono")

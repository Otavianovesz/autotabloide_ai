"""FASE 1 (passo 91) — tema: tokens trocam, Config persiste, claro é o padrão."""

import pytest

from app.qt.design import tokens as t


@pytest.fixture()
def raiz_tmp(tmp_path, monkeypatch):
    monkeypatch.setenv("AUTOTABLOIDE_ROOT", str(tmp_path / "raiz"))
    from app.core.database import Database
    from app.core.paths import SystemRoot

    root = SystemRoot(tmp_path / "raiz").criar_estrutura()
    Database(root).init().engine.dispose()
    return root


@pytest.fixture(autouse=True)
def _volta_ao_claro():
    yield
    t.ativar_tema("claro")
    t.ativar_escala(100)


def test_ativar_tema_troca_os_tokens_do_modulo():
    t.ativar_tema("escuro")
    assert t.FUNDO_APP == "#101216"
    assert t.SUPERFICIE == "#181B21"
    assert t.FUNDO == t.FUNDO_APP          # alias acompanha (passo 9)
    assert t.PAGINA_SOMBRA == "#FFFFFF"    # halo claro no escuro (passo 20)
    t.ativar_tema("claro")
    assert t.FUNDO_APP == "#F3F5F8"
    assert t.SUPERFICIE == "#FFFFFF"


def test_tema_desconhecido_cai_no_claro():
    t.ativar_tema("roxo_neon")             # C3: default são, nunca estoura
    assert t.TEMA_ATUAL == "claro"
    assert t.FUNDO_APP == "#F3F5F8"


def test_config_persiste_e_claro_e_padrao(raiz_tmp):
    from app.qt.design.tema import _tema_da_config, trocar_tema

    assert _tema_da_config() == "claro"    # banco novo: padrão travado
    trocar_tema("escuro")                  # sem QApplication: persiste e sai
    assert _tema_da_config() == "escuro"
    trocar_tema("claro")
    assert _tema_da_config() == "claro"


def test_qss_regenerado_segue_o_tema():
    from app.qt.design.tema import construir_qss

    t.ativar_tema("escuro")
    assert "#181B21" in construir_qss()    # superfície escura no QSS
    t.ativar_tema("claro")
    assert "#FFFFFF" in construir_qss()


def test_escala_de_ui_multiplica_e_valida(raiz_tmp):
    t.ativar_escala(150)
    assert t.ALTURA_CONTROLE == 48         # 32 × 1,5
    assert t.TAM_CORPO == pytest.approx(14.25)
    t.ativar_escala(100)
    assert t.ALTURA_CONTROLE == 32
    t.ativar_escala(999)                   # inválida: cai em 100 (C3)
    assert t.ESCALA_ATUAL == 100
    assert t.ALTURA_CONTROLE == 32

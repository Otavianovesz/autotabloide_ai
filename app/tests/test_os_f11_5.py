"""
ORDEM DE SERVIÇO F11.5 — testes de aceite (gates + itens)
=========================================================
Cada teste aqui cobre um item da `docs/ORDEM_SERVICO_F11_5.md`, SEMPRE por
CONTEÚDO (valor/pixel/uid) — reverter a correção correspondente faz o teste
falhar (mutation-proof). Os gates vêm primeiro.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest
from PySide6.QtWidgets import QApplication

from app.tests import seeds_portabilidade as seeds


@pytest.fixture()
def raiz_env(tmp_path, monkeypatch):
    root = seeds.raiz(tmp_path, "raiz")
    monkeypatch.setenv("AUTOTABLOIDE_ROOT", str(root.raiz))
    return root


def _app():
    return QApplication.instance() or QApplication([])


# ============================================================================
# GATE 1 — crash do badge de papel (F5 passo 6)
# ============================================================================

def test_gate1_badge_cobre_todos_os_papeis_do_enum():
    """TODO papel do ENUM (não só os do diálogo) devolve (rótulo, cor #hex,
    ícone existente). Na versão anterior, OBSERVACAO e DESCONTO estouravam
    KeyError NO PAINT — crash alcançável por ação normal do dono."""
    from app.qt.design.icones import nomes_disponiveis
    from app.qt.design.papel_texto_ui import ORDEM_PAPEIS, badge_de_papel
    from app.rendering.model import PapelTexto
    _app()
    icones = set(nomes_disponiveis())
    # o diálogo oferece OBSERVACAO — o caso exato do crash reportado
    assert PapelTexto.OBSERVACAO in ORDEM_PAPEIS
    for papel in PapelTexto:                     # o enum INTEIRO
        rotulo, cor, nome_icone = badge_de_papel(papel)
        assert rotulo and isinstance(rotulo, str), papel
        assert re.fullmatch(r"#[0-9A-Fa-f]{6}", cor), (papel, cor)
        assert nome_icone in icones, (papel, nome_icone)
    # cores DISTINTAS entre os papéis do diálogo (o badge diferencia à vista)
    cores = [badge_de_papel(p)[1] for p in ORDEM_PAPEIS]
    assert len(set(cores)) >= 4


# ============================================================================
# GATE 3 — pré-voo nos formatos sociais (F8, I2)
# ============================================================================

def _mesa_fake(itens):
    """Um duble mínimo do que o PublicarDialog usa da Mesa (QWidget porque o
    diálogo o usa como parent)."""
    from PySide6.QtWidgets import QWidget

    class _M(QWidget):
        def __init__(self):
            super().__init__()
            self._itens = itens

        @staticmethod
        def esta_aprovado():
            return False
    return _M()


def test_gate3_previa_social_avisa_item_incompleto(monkeypatch):
    """Item sem preço/foto AVISA antes de qualquer formato social sair (o
    fluxo antigo exportava calado). Por conteúdo: os avisos nomeiam o item e
    a falta; e com o pré-voo recusado, NADA é gerado (o seletor de pasta nem
    abre). Prova de mutação: remover a chamada do pré-voo em `_gerar` deixa
    `capturados` vazio e o teste falha."""
    from app.qt.telas.publicar_dialog import PublicarDialog
    from app.qt.telas.servico import ItemMesa
    _app()
    itens = [ItemMesa("Coca 2L", "7,99", "VERDE", "Coca 2L",
                      imagem=None),                      # sem foto
             ItemMesa("Sabão", None, "VERDE", "Sabão",
                      imagem=None)]                      # sem preço nem foto
    dlg = PublicarDialog(_mesa_fake(itens))

    # por conteúdo: o pré-voo nomeia item e falta, por modo
    avisos = dlg._avisos_pre_voo("carrossel", None)
    texto = " · ".join(avisos)
    assert "Coca 2L" in texto and "sem foto" in texto
    assert "Sabão" in texto and "sem preço" in texto
    # oferta/story: só o item do destaque entra no pré-voo
    so_um = dlg._avisos_pre_voo("oferta", itens[0])
    assert "Coca 2L" in " ".join(so_um) and "Sabão" not in " ".join(so_um)

    # o _gerar CHAMA o pré-voo e respeita a recusa (nada abre/gera)
    capturados: list[list[str]] = []

    def _confirmar(_pai, avisos, _verbo):
        capturados.append(list(avisos))
        return False                                     # o dono recusou

    monkeypatch.setattr("app.qt.telas.prevoo.confirmar_pre_voo", _confirmar)

    def _boom(*a, **k):                                  # pasta nunca é pedida
        raise AssertionError("exportou sem passar no pré-voo")

    monkeypatch.setattr(
        "app.qt.telas.publicar_dialog.QFileDialog.getExistingDirectory",
        _boom)
    dlg.rb_carrossel.setChecked(True)
    dlg._gerar()
    assert capturados and any("sem preço" in a for a in capturados[0])
    dlg.close()

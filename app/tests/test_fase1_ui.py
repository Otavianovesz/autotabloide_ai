"""FASE 1 (passos 92-93) — animações reduzidas = ZERO em voo; mínimos de campo."""

import time

import pytest
from PySide6.QtCore import QCoreApplication
from PySide6.QtWidgets import QApplication, QWidget

from app.qt.design import tokens as t


@pytest.fixture()
def raiz_tmp(tmp_path, monkeypatch):
    monkeypatch.setenv("AUTOTABLOIDE_ROOT", str(tmp_path / "raiz"))
    from app.core.database import Database
    from app.core.paths import SystemRoot

    root = SystemRoot(tmp_path / "raiz").criar_estrutura()
    Database(root).init().engine.dispose()
    return root


def _app():
    return QApplication.instance() or QApplication([])


def _config_animacoes(valor: str) -> None:
    from app.core.database import Database
    from app.core.repositories import ConfigRepositorio
    db = Database().init()
    try:
        with db.Session() as s:
            ConfigRepositorio(s).set("aparencia.animacoes", valor)
            s.commit()
    finally:
        db.engine.dispose()


def test_minimos_de_campo_nas_telas_principais(raiz_tmp):
    """Passo 93: em 1280×720 (o menor alvo), NENHUM campo visível das
    Configurações fica mais estreito que o mínimo do token.

    Roda ANTES dos testes de animação: o repolimento do aplicar_tema num
    processo com widgets órfãos recém-coletados crasha o Qt (bancada)."""
    from PySide6.QtWidgets import (
        QComboBox, QDoubleSpinBox, QLineEdit, QSpinBox)

    from app.qt.design.tema import aplicar_tema
    app = _app()
    aplicar_tema(app)
    from app.qt.telas.configuracoes import ConfiguracoesTela
    tela = ConfiguracoesTela()
    tela.resize(1280, 680)
    tela.show()
    for _ in range(6):
        QCoreApplication.processEvents()
    estreitos = []
    for tipo in (QLineEdit, QComboBox, QDoubleSpinBox, QSpinBox):
        for w in tela.findChildren(tipo):
            if not w.isVisible():
                continue
            if w.width() < t.LARGURA_MIN_CAMPO - 2:
                estreitos.append((type(w).__name__, w.width(),
                                  w.toolTip()[:40] or w.objectName()))
    assert not estreitos, f"campos espremidos: {estreitos}"
    tela.close()
    QCoreApplication.processEvents()


def test_reduzidas_significa_zero_animacoes_em_voo(raiz_tmp):
    """Passo 92: com a Config em 'reduzidas', NENHUM helper cria animação
    (o registro _VIVAS fica em 0 — instantâneo de verdade, zero timers)."""
    from app.qt.design import animacoes as anim
    _app()
    _config_animacoes("reduzidas")
    anim.recarregar_config()
    try:
        w = QWidget()
        anim.fade_in(w)
        anim.slide_y(w, 12)
        from PySide6.QtWidgets import QStackedWidget
        pilha = QStackedWidget()
        a, b = QWidget(), QWidget()
        pilha.addWidget(a)
        pilha.addWidget(b)
        anim.crossfade(pilha, a, b)
        from app.qt.design.componentes import Skeleton
        esqueleto = Skeleton(parent=None)
        esqueleto.show()                     # loop do pulso NÃO nasce
        QCoreApplication.processEvents()
        assert anim.animacoes_ativas() == 0
        assert pilha.currentWidget() is b    # o EFEITO aconteceu (seco)
        assert w.isVisible()
        esqueleto.hide()
    finally:
        _config_animacoes("ligadas")
        anim.recarregar_config()


def test_ligadas_registra_e_finaliza(raiz_tmp):
    """O contraste do passo 92: 'ligadas' cria animação viva e o registro
    esvazia quando ela termina (nada apodrece em _VIVAS)."""
    from app.qt.design import animacoes as anim
    _app()
    _config_animacoes("ligadas")
    anim.recarregar_config()
    w = QWidget()
    anim.fade_in(w, ms=30)
    assert anim.animacoes_ativas() >= 1
    fim = time.monotonic() + 2.0
    while time.monotonic() < fim and anim.animacoes_ativas():
        QCoreApplication.processEvents()
        time.sleep(0.01)
    assert anim.animacoes_ativas() == 0
    # morte ORDENADA (deleteLater + drenagem) — matar um widget animado
    # pelo GC do Python deixa restos que derrubam o processEvents seguinte
    w.hide()
    w.deleteLater()
    for _ in range(4):
        QCoreApplication.processEvents()



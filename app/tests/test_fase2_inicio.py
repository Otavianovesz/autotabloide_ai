"""FASE 2, Bloco B (passos 32-33) — o Início novo por estado."""

import pytest
from PySide6.QtWidgets import QApplication, QLabel, QPushButton

from app.qt.telas.servico import ItemMesa
from app.rendering.model import LayoutDef, Pagina, Regiao, Retangulo, Slot, TipoRegiao


@pytest.fixture()
def raiz_tmp(tmp_path, monkeypatch):
    monkeypatch.setenv("AUTOTABLOIDE_ROOT", str(tmp_path / "raiz"))
    from app.core.database import Database
    from app.core.paths import SystemRoot

    root = SystemRoot(tmp_path / "raiz").criar_estrutura()
    Database(root).init().engine.dispose()
    return root


def _layout() -> LayoutDef:
    return LayoutDef(100, 100, dpi=100, paginas=[Pagina([
        Slot("s", [Regiao(TipoRegiao.NOME, Retangulo(10, 10, 30, 10))])])])


def _salvar(nome: str, evento: str | None) -> int:
    from app.core import projetos
    item = ItemMesa(descricao="X", preco="1,00", semaforo="VERDE",
                    nome="Produto X")
    return projetos.salvar_projeto(nome, evento, "TABLOIDE", _layout(),
                                   [item.to_dict()])


def _criar_evento(nome: str, dia: int | None = None) -> None:
    from app.core.database import Database
    from app.qt.telas.eventos import criar_evento
    db = Database().init()
    try:
        with db.Session() as s:
            criar_evento(s, nome, dia_semana=dia)
            s.commit()
    finally:
        db.engine.dispose()


def test_inicio_monta_com_0_1_e_n_eventos(raiz_tmp):
    """Passo 32: smoke por estado — 0 (hero), 1 e N eventos, sem erro."""
    QApplication.instance() or QApplication([])
    from app.qt.telas.dashboard import DashboardTela

    dash0 = DashboardTela()                      # 0: hero de boas-vindas
    textos0 = " ".join(w.text() for w in dash0.findChildren(
        QLabel))
    assert "Bem-vindo" in textos0

    from app.qt.telas.dashboard import _CartaoCapa
    _criar_evento("Quintou", dia=3)
    dash1 = DashboardTela()                      # 1 evento (vazio)
    assert any("Quintou" in c._titulo for c in
               dash1._pratileiras.findChildren(_CartaoCapa))

    _salvar("P1", "Sexta Verde")
    _salvar("P2", "Terça do Pão")
    dash_n = DashboardTela()                     # N eventos com projetos
    titulos = [c._titulo for c in
               dash_n._pratileiras.findChildren(_CartaoCapa)]
    assert "Sexta Verde" in titulos and "Terça do Pão" in titulos


def test_produzir_hoje_aparece_no_dia_certo(raiz_tmp):
    """Passo 33: o cartão 'Produzir hoje' aparece EXATAMENTE quando
    hoje.weekday() == evento.dia_semana."""
    from datetime import date

    QApplication.instance() or QApplication([])
    from app.qt.telas.dashboard import DashboardTela

    hoje = date.today().weekday()
    _criar_evento("Campanha de Hoje", dia=hoje)
    _criar_evento("Campanha de Amanhã", dia=(hoje + 1) % 7)
    _salvar("P1", "Campanha de Hoje")

    dash = DashboardTela()
    junto = " ".join(w.text() for w in
                     dash._pratileiras.findChildren(QLabel))
    assert "Produzir hoje:" in junto and "Campanha de Hoje" in junto
    assert "Produzir hoje: Campanha de Amanhã" not in junto

    # e a zona SEM campanha hoje: só o evento de amanhã → chips da semana
    from app.core.database import Database
    from app.core.models import Evento
    db = Database().init()
    try:
        with db.Session() as s:
            ev = s.query(Evento).filter_by(nome="Campanha de Hoje").one()
            ev.dia_semana = (hoje + 2) % 7       # tira a campanha de hoje
            s.commit()
    finally:
        db.engine.dispose()
    dash2 = DashboardTela()
    junto2 = " ".join(w.text() for w in
                      dash2._pratileiras.findChildren(QLabel))
    assert "Produzir hoje:" not in junto2
    botoes = " ".join(b.text() for b in dash2._pratileiras.findChildren(
        QPushButton))
    assert "Campanha de Amanhã" in botoes        # chip da semana

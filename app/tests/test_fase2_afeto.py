"""FASE 2, Bloco D (passos 53-54) — continuar de onde parei + favoritos."""

import pytest
from PySide6.QtWidgets import QApplication

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


def _salvar(nome: str, evento: str | None = None) -> int:
    from app.core import projetos
    item = ItemMesa(descricao="X", preco="1,00", semaforo="VERDE",
                    nome="Produto X")
    return projetos.salvar_projeto(nome, evento, "TABLOIDE", _layout(),
                                   [item.to_dict()])


def test_ultimo_aberto_nos_4_caminhos(raiz_tmp):
    """Passo 53 (reescrito no GATE 2.5 da ordem F11.5 — a versão antiga
    cobria 2 caminhos e ENCENAVA os outros dois): os 4 fluxos REAIS —
    Mesa, Fábrica, dashboard (pelo GESTO de retomar) e duplicar_semana_
    passada (que antes NÃO registrava — prova de mutação: reverter o
    registrar em projetos.py:520 faz o caminho 4 falhar)."""
    QApplication.instance() or QApplication([])
    from PySide6.QtCore import Qt
    from PySide6.QtWidgets import QListWidgetItem

    from app.core import projetos
    from app.qt.telas.dashboard import DashboardTela
    from app.qt.telas.fabrica import FabricaTela
    from app.qt.telas.mesa import MesaTela

    p1 = _salvar("P1")
    p2 = _salvar("P2", "Quintou")

    mesa = MesaTela()                                # caminho 1: Mesa
    mesa.abrir_projeto_congelado(projetos.abrir_projeto(p1))
    assert projetos.ultimo_aberto()["id"] == p1

    fab = FabricaTela()                              # caminho 2: Fábrica
    ab = projetos.abrir_projeto(p2)
    ab.tipo = "CARTAZ"
    fab.abrir_projeto_congelado(ab)
    assert projetos.ultimo_aberto()["id"] == p2

    # caminho 3: o GESTO do dashboard (duplo-clique em "Retomar") dispara o
    # funil real ao_abrir_projeto → Mesa
    abertos: list[int] = []

    def _funil(pid):
        abertos.append(pid)
        mesa.abrir_projeto_congelado(projetos.abrir_projeto(pid))

    dash = DashboardTela(ao_abrir_projeto=_funil)
    item = QListWidgetItem("P1")
    item.setData(Qt.ItemDataRole.UserRole, p1)
    dash._retomar_clicado(item)                      # o gesto real da lista
    assert abertos == [p1]
    assert projetos.ultimo_aberto()["id"] == p1

    # caminho 4: duplicar_semana_passada registra o CLONE sozinho (sem
    # encenação — a chamada manual de registrar era o mascaramento)
    novo = projetos.duplicar_semana_passada("Quintou")
    assert novo is not None
    assert projetos.ultimo_aberto()["id"] == novo
    dash.close()
    mesa.close()
    fab.close()


def test_favorito_reordena_sem_tocar_mapa(raiz_tmp):
    """Passo 54: favorito é SÓ exibição — o mapa congelado não muda byte."""
    from app.core import projetos

    p1 = _salvar("A", "Quintou")
    p2 = _salvar("B", "Quintou")
    mapa_antes = projetos.abrir_projeto(p2).mapa
    projetos.marcar_favorito(p2, True)
    lista = [p for p in projetos.listar_projetos()
             if p["evento"] == "Quintou"]
    ordenada = sorted(lista, key=lambda p: not p.get("favorito"))
    assert ordenada[0]["id"] == p2 and ordenada[0]["favorito"] is True
    assert projetos.abrir_projeto(p2).mapa == mapa_antes   # intacto (I1)
    assert projetos.abrir_projeto(p1).mapa is not None


def test_duplicar_semana_passada(raiz_tmp):
    """FASE 2 (passo 99 — R-009): uuid novo, mapa idêntico por conteúdo,
    validade re-sugerida pelo dia do evento, original INTOCADO."""
    from datetime import date, timedelta

    from app.core import projetos
    from app.core.database import Database
    from app.core.models import ProjetoSalvo
    from app.qt.telas.eventos import criar_evento

    # o evento tem dia fixo = amanhã (a validade sugerida é conhecida)
    amanha = (date.today().weekday() + 1) % 7
    db = Database().init()
    try:
        with db.Session() as s:
            criar_evento(s, "Quintou", dia_semana=amanha)
            s.commit()
    finally:
        db.engine.dispose()

    from app.qt.telas.servico import ItemMesa
    item = ItemMesa(descricao="X", preco="1,00", semaforo="VERDE",
                    nome="Produto X")
    mapa = {"s": item.uid}
    pid = projetos.salvar_projeto("Quintou 10/07", "Quintou", "TABLOIDE",
                                  _layout(), [item.to_dict()], "ATÉ 11/07",
                                  mapa=mapa)
    antes = projetos.abrir_projeto(pid)

    novo = projetos.duplicar_semana_passada("Quintou")
    assert novo is not None and novo != pid
    clone = projetos.abrir_projeto(novo)
    hoje_txt = date.today().strftime("%d/%m")
    assert clone.nome == f"Quintou {hoje_txt}"
    assert clone.mapa == antes.mapa                      # conteúdo (I1)
    data_esperada = date.today() + timedelta(days=1)
    # auditoria do dono (20/07): a campanha de dia fixo vale SÓ NO DIA
    assert clone.validade_oferta == \
        f"SOMENTE {data_esperada.strftime('%d/%m')}"     # re-sugerida
    db = Database().init()
    try:
        with db.Session() as s:
            assert s.get(ProjetoSalvo, novo).status == "rascunho"
            uuids = {p.uuid for p in s.query(ProjetoSalvo).all()}
            assert len(uuids) == 2                       # uuid NOVO
    finally:
        db.engine.dispose()
    depois = projetos.abrir_projeto(pid)
    assert depois.validade_oferta == "ATÉ 11/07"         # original intocado
    assert depois.nome == "Quintou 10/07"

    # dedup (passo 98): duplicar de novo no MESMO dia vira "(2)"
    novo2 = projetos.duplicar_semana_passada("Quintou")
    assert projetos.abrir_projeto(novo2).nome == f"Quintou {hoje_txt} (2)"

"""Testes do Dashboard (F6.1) — pastas por evento, abrir, renomear."""

import pytest
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QLabel, QListWidget

from app.core import projetos
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


def _salvar(nome: str, evento: str | None, tipo: str = "TABLOIDE") -> int:
    item = ItemMesa(descricao="X", preco="1,00", semaforo="VERDE", nome="Produto X")
    return projetos.salvar_projeto(nome, evento, tipo, _layout(), [item.to_dict()])


def test_dashboard_agrupa_por_evento(raiz_tmp):
    """FASE 2 (Bloco B): a home virou GRADE de cartões de evento (★ semana
    antes, Avulsos ao fim); a prateleira vive na VISÃO do evento."""
    QApplication.instance() or QApplication([])
    from app.qt.telas.dashboard import DashboardTela

    _salvar("Ofertas 08/07", "Terça do Pão")
    _salvar("Ofertas 09/07", "Quintou do Real")
    _salvar("Avulso 1", None)

    dash = DashboardTela()
    # FASE 3 (RG-59): os cartões são PINTADOS (_CartaoCapa) — a leitura é
    # pelo conteúdo do widget (título + chips), não por QLabel
    from app.qt.telas.dashboard import _CartaoCapa
    cartoes = dash._pratileiras.findChildren(_CartaoCapa)
    titulos = [c._titulo for c in cartoes]
    chips = " | ".join(" ".join(c._chips) for c in cartoes)
    assert "★ Ofertas da semana" in titulos
    assert "Terça do Pão" in titulos and "Quintou do Real" in titulos
    assert "Avulsos" in titulos
    assert chips.count("1 projeto(s)") >= 3      # contagem por cartão
    # a visão do evento tem a prateleira com o projeto CERTO (conteúdo)
    dash._abrir_evento_por_nome("Quintou do Real")
    lista = dash._visao_evento.findChildren(QListWidget)[0]
    assert lista.count() == 1
    assert "Ofertas 09/07" in lista.item(0).text()


def test_dashboard_abre_pelo_duplo_clique(raiz_tmp):
    QApplication.instance() or QApplication([])
    from app.qt.telas.dashboard import DashboardTela

    pid = _salvar("Meu Projeto", "Evento A", tipo="CARTAZ")
    abertos = []
    dash = DashboardTela(ao_abrir_projeto=abertos.append)
    dash._abrir_evento_por_nome("Evento A")      # passo 27: nada regride
    lista = dash._visao_evento.findChildren(QListWidget)[0]
    dash._abrir(lista.item(0))
    assert abertos == [pid]


def test_renomear_projeto(raiz_tmp):
    pid = _salvar("Nome Velho", "Evento A")
    projetos.renomear_projeto(pid, "Nome Novo", novo_evento="Evento B")
    p = projetos.listar_projetos()[0]
    assert p["nome"] == "Nome Novo" and p["evento"] == "Evento B"


def test_miniatura_e_opcional_sem_fontes(raiz_tmp):
    # na raiz tmp NÃO há fontes → a miniatura falha em silêncio, o projeto salva
    pid = _salvar("Sem Miniatura", None)
    p = projetos.listar_projetos()[0]
    assert p["id"] == pid          # salvou mesmo sem conseguir compor a miniatura
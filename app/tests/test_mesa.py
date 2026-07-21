"""Testes da Mesa (F6.4) — serviço headless + fumaça da tela (offscreen)."""

from decimal import Decimal
from pathlib import Path

import pytest

from app.qt.telas import servico

FIXTURE = Path("app/tests/fixtures/ofertas_belo_brasil.txt")


@pytest.fixture()
def raiz_tmp(tmp_path, monkeypatch):
    """System Root isolado + IA desligada (determinístico e offline)."""
    monkeypatch.setenv("AUTOTABLOIDE_ROOT", str(tmp_path / "raiz"))
    monkeypatch.setattr(servico, "_motor_se_disponivel", lambda: None)
    from app.core.database import Database
    from app.core.paths import SystemRoot

    root = SystemRoot(tmp_path / "raiz").criar_estrutura()
    Database(root).init().engine.dispose()
    return root


def test_preco_decimal():
    assert servico.preco_decimal("R$ 17,71") == Decimal("17.71")
    assert servico.preco_decimal("5,50") == Decimal("5.50")
    assert servico.preco_decimal(None) is None
    assert servico.preco_decimal("abc") is None


def test_importar_banco_vazio_fica_tudo_vermelho(raiz_tmp):
    r = servico.importar_ofertas(FIXTURE, lambda s: None)
    assert len(r.itens) >= 40
    assert all(i.semaforo == "VERMELHO" for i in r.itens)
    assert all(i.produto_id is None for i in r.itens)


def test_importar_banco_cheio_fica_verde(raiz_tmp):
    from app.scripts.importar_tabela import importar_arquivo

    importar_arquivo(FIXTURE, raiz_tmp)   # o catálogo real entra no banco
    r = servico.importar_ofertas(FIXTURE, lambda s: None)
    assert all(i.semaforo == "VERDE" for i in r.itens)   # nome cru → exato
    assert all(i.produto_id is not None for i in r.itens)


def test_aceitar_amarelo_aprende_alias(raiz_tmp):
    from app.core.database import Database
    from app.core.repositories import ProdutoRepositorio

    db = Database(raiz_tmp).init()
    with db.Session() as s:
        repo = ProdutoRepositorio(s)
        pid = repo.importar("REFRIGERANTE KITUBAINA 1,5 LT").produto.id
        s.commit()
    db.engine.dispose()

    item = servico.ItemMesa(
        descricao="REFRIG. KITUBAINA 1500ML", preco="5,50",
        semaforo="AMARELO", nome="?", produto_id=pid)
    item = servico.aceitar_correspondencia(item)
    assert item.semaforo == "VERDE" and item.via == "alias"

    # o banco aprendeu: a MESMA grafia agora casa por alias (exato → verde)
    db = Database(raiz_tmp).init()
    with db.Session() as s:
        repo = ProdutoRepositorio(s)
        assert repo.buscar_por_alias("REFRIG. KITUBAINA 1500ML").id == pid
    db.engine.dispose()


def test_finalizar_criacao_cadastra_no_banco(raiz_tmp):
    item = servico.ItemMesa(
        descricao="OLE O de SOJA LIZA 900ML", preco="7,71",
        semaforo="VERMELHO", nome="OLE O de SOJA LIZA 900ML")
    item = servico.finalizar_criacao(item, "Óleo de Soja Liza 900ml", False, None)
    assert item.semaforo == "VERDE" and item.produto_id is not None

    from app.core.database import Database
    from app.core.repositories import ProdutoRepositorio

    db = Database(raiz_tmp).init()
    with db.Session() as s:
        p = ProdutoRepositorio(s).get(item.produto_id)
        assert p.nome_sanitizado == "Óleo de Soja Liza 900ml"
        assert p.preco_atual == Decimal("7.71")
    db.engine.dispose()


def test_mesa_tela_auto_preencher_e_estado():
    """Fumaça offscreen: a tela constrói, preenche a grade e habilita exportar.

    Usa o System Root real (o compositor precisa das fontes de /fontes).
    """
    from PySide6.QtWidgets import QApplication

    from app.qt.telas.mesa import MesaTela
    from app.rendering.model import (
        LayoutDef, Pagina, Regiao, Retangulo, Slot, TipoRegiao,
    )

    QApplication.instance() or QApplication([])
    layout = LayoutDef(100, 100, dpi=100, paginas=[Pagina([
        Slot("a", [Regiao(TipoRegiao.NOME, Retangulo(10, 10, 80, 10))]),
        Slot("b", [Regiao(TipoRegiao.NOME, Retangulo(10, 30, 80, 10))]),
    ])])
    mesa = MesaTela()
    mesa.carregar_layout(layout, None)
    assert not mesa.btn_preencher.isEnabled()   # nada importado ainda

    mesa._itens = [
        servico.ItemMesa("A", "1,00", "VERDE", "Produto A"),
        servico.ItemMesa("B", "2,00", "VERDE", "Produto B"),
        servico.ItemMesa("C", "3,00", "VERDE", "Produto C"),  # não cabe (2 slots)
    ]
    mesa._recarregar_lista()
    mesa.btn_preencher.setEnabled(True)
    mesa._auto_preencher()
    assert mesa.btn_exportar.isEnabled()
    # F5.5b (I1): o canvas recebe um MAPA slot_id→DadosProduto, não uma lista
    dados = mesa.area.canvas._dados
    assert set(dados) == {"a", "b"}             # C ficou fora da grade
    assert dados["a"].nome == "Produto A"
    assert dados["b"].nome == "Produto B"
    assert mesa._mapa["a"] == mesa._itens[0].uid  # vínculo por identidade

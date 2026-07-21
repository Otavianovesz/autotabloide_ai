"""FASE 2, Bloco E (passos 64-67) — versões: nunca sobrescrever, sempre clonar."""

import time

import pytest

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


def _itens(preco: str) -> list[dict]:
    return [ItemMesa(descricao="X", preco=preco, semaforo="VERDE",
                     nome="Produto X").to_dict()]


def _config(chave, valor):
    from app.core.database import Database
    from app.core.repositories import ConfigRepositorio
    db = Database().init()
    try:
        with db.Session() as s:
            ConfigRepositorio(s).set(chave, valor)
            s.commit()
    finally:
        db.engine.dispose()


def test_salvar_3x_gera_2_versoes_e_poda(raiz_tmp):
    """Passo 64: 3 salvamentos = 2 versões + atual; poda N=2 mantém as 2
    mais novas (a atual nunca é podada — vive fora de versoes/)."""
    from app.core import projetos

    lay = _layout()
    pid = projetos.salvar_projeto("P", None, "TABLOIDE", lay, _itens("1,00"))
    projetos.salvar_projeto("P", None, "TABLOIDE", lay, _itens("2,00"),
                            projeto_id=pid)
    projetos.salvar_projeto("P", None, "TABLOIDE", lay, _itens("3,00"),
                            projeto_id=pid)
    versoes = projetos.listar_versoes(pid)
    assert len(versoes) == 2
    # poda: com máximo 2, um 4º salvar mantém só as 2 mais novas
    _config("projetos.versoes_max", 2)
    projetos.salvar_projeto("P", None, "TABLOIDE", lay, _itens("4,00"),
                            projeto_id=pid)
    versoes = projetos.listar_versoes(pid)
    assert len(versoes) == 2
    # a atual segue viva e íntegra (4,00)
    aberto = projetos.abrir_projeto(pid)
    assert aberto.itens[0]["preco"] == "4,00"


def test_abrir_como_novo_clona_por_conteudo(raiz_tmp):
    """Passo 65: uuid NOVO, mapa/estado da ÉPOCA por conteúdo, original
    intocado — restaurar por cima não existe."""
    from app.core import projetos
    from app.core.database import Database
    from app.core.models import ProjetoSalvo

    lay = _layout()
    itens_v1 = _itens("1,00")
    pid = projetos.salvar_projeto("P", "Quintou", "TABLOIDE", lay, itens_v1)
    projetos.salvar_projeto("P", "Quintou", "TABLOIDE", lay, _itens("2,00"),
                            projeto_id=pid)
    versoes = projetos.listar_versoes(pid)
    novo = projetos.abrir_versao_como_novo(pid, versoes[0]["ts"])
    assert novo is not None and novo != pid

    original = projetos.abrir_projeto(pid)
    clone = projetos.abrir_projeto(novo)
    assert original.itens[0]["preco"] == "2,00"      # vivo intocado
    assert clone.itens[0]["preco"] == "1,00"         # a época, por conteúdo
    assert clone.mapa == {}                          # mapa da época idem
    assert "(versão de" in clone.nome
    db = Database().init()
    try:
        with db.Session() as s:
            uuids = {p.uuid for p in s.query(ProjetoSalvo).all()}
            assert len(uuids) == 2                   # uuid NOVO de verdade
    finally:
        db.engine.dispose()


def test_miniatura_da_versao_existe(raiz_tmp):
    """Passo 66 (+69: perf medida e registrada no caderno)."""
    from app.core import projetos

    lay = _layout()
    pid = projetos.salvar_projeto("P", None, "TABLOIDE", lay, _itens("1,00"))
    t0 = time.perf_counter()
    projetos.salvar_projeto("P", None, "TABLOIDE", lay, _itens("2,00"),
                            projeto_id=pid)
    dt_com_versao = (time.perf_counter() - t0) * 1000
    versoes = projetos.listar_versoes(pid)
    assert len(versoes) == 1
    # a miniatura da versão existe (é a da época — o salvar de 1,00 a gerou)
    assert versoes[0]["miniatura"] is not None
    print(f"salvar com versão: {dt_com_versao:.0f} ms")


def test_adversarial_versoes_nao_tocam_o_vivo(raiz_tmp):
    """Passo 67: fluxo completo (salvar ×3, listar, abrir-como-novo) e o
    MAPA do projeto vivo confere byte a byte com o antes."""
    from app.core import projetos

    lay = _layout()
    itens = _itens("1,00")
    mapa = {"s": itens[0]["uid"]}
    pid = projetos.salvar_projeto("P", None, "TABLOIDE", lay, itens,
                                  mapa=mapa)
    antes = projetos.abrir_projeto(pid).mapa
    projetos.salvar_projeto("P", None, "TABLOIDE", lay, _itens("2,00"),
                            projeto_id=pid, mapa=mapa)
    projetos.salvar_projeto("P", None, "TABLOIDE", lay, _itens("3,00"),
                            projeto_id=pid, mapa=mapa)
    versoes = projetos.listar_versoes(pid)
    projetos.abrir_versao_como_novo(pid, versoes[-1]["ts"])
    depois = projetos.abrir_projeto(pid).mapa
    assert depois == {"s": mapa["s"]} == antes       # intacto (I1)

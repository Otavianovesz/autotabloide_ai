"""FASE 2, Bloco C (passos 43-44) — status por CONTEÚDO, nunca por gesto vazio."""

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


def _itens(preco: str = "1,00") -> list[dict]:
    return [ItemMesa(descricao="X", preco=preco, semaforo="VERDE",
                     nome="Produto X").to_dict()]


def _status(pid: int) -> str:
    from app.core import projetos
    return next(p["status"] for p in projetos.listar_projetos()
                if p["id"] == pid)


def test_exportar_marca_e_so_conteudo_rebaixa(raiz_tmp):
    """Passo 43: exportado fica; re-salvar IGUAL não rebaixa; conteúdo
    mudado (hash) volta a rascunho."""
    from app.core import projetos

    # a MESMA estante entre os salvamentos (como no app: uids estáveis)
    itens = _itens()
    lay = _layout()
    pid = projetos.salvar_projeto("P", "Quintou", "TABLOIDE", lay, itens)
    assert _status(pid) == "rascunho"
    projetos.marcar_status(pid, "exportado")
    assert _status(pid) == "exportado"
    # re-salvar com o MESMO conteúdo: o status não cai à toa
    projetos.salvar_projeto("P", "Quintou", "TABLOIDE", lay, itens,
                            projeto_id=pid)
    assert _status(pid) == "exportado"
    # conteúdo MUDOU (preço): volta a rascunho — por hash, não por salvar
    mudados = [dict(itens[0], preco="2,00")]
    projetos.salvar_projeto("P", "Quintou", "TABLOIDE", lay, mudados,
                            projeto_id=pid)
    assert _status(pid) == "rascunho"


def test_status_sobrevive_a_duplicar_e_reabrir(raiz_tmp):
    """Passo 44: a cópia nasce rascunho; o original mantém o status; abrir
    e reabrir não muda nada."""
    from app.core import projetos

    pid = projetos.salvar_projeto("P", None, "TABLOIDE", _layout(), _itens())
    projetos.marcar_status(pid, "publicado")
    novo = projetos.duplicar_projeto(pid, "P (nova)")
    assert _status(pid) == "publicado"
    assert _status(novo) == "rascunho"
    aberto = projetos.abrir_projeto(pid)
    assert aberto is not None
    assert _status(pid) == "publicado"   # abrir não é transição

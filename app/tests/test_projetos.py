"""Testes do projeto salvo congelado (§3.1/§6.8) — o app guarda o trabalho."""

from pathlib import Path

import pytest
from PIL import Image

from app.core import projetos
from app.qt.telas.servico import ItemMesa
from app.rendering.model import (
    LayoutDef, Pagina, Regiao, Retangulo, Slot, TipoRegiao,
)


@pytest.fixture()
def raiz_tmp(tmp_path, monkeypatch):
    monkeypatch.setenv("AUTOTABLOIDE_ROOT", str(tmp_path / "raiz"))
    from app.core.database import Database
    from app.core.paths import SystemRoot

    root = SystemRoot(tmp_path / "raiz").criar_estrutura()
    Database(root).init().engine.dispose()
    return root


def _layout(n_regioes: int = 1) -> LayoutDef:
    regs = [Regiao(TipoRegiao.NOME, Retangulo(10, 10 + 15 * i, 30, 10))
            for i in range(n_regioes)]
    return LayoutDef(100, 100, dpi=100, paginas=[Pagina([Slot("s", regs)])])


def _item(nome="Açúcar Cristal Doce Dia 2kg", preco="5,95", imagem=None):
    return ItemMesa(descricao="ACUCAR CRISTAL DOCE DIA 2 Kgs", preco=preco,
                    semaforo="VERDE", nome=nome, produto_id=1, imagem=imagem)


def _png(caminho: Path) -> str:
    Image.new("RGB", (60, 60), "red").save(caminho)
    return str(caminho)


def test_congelamento_independe_do_banco(raiz_tmp):
    from app.core.database import Database
    from app.core.repositories import ProdutoRepositorio

    pid = projetos.salvar_projeto(
        "Ofertas 08/07", "Terça do Pão", "TABLOIDE", _layout(),
        [_item().to_dict()], "01/07 ATÉ 27/07")

    # o banco muda DEPOIS de salvar (preço e nome)
    db = Database(raiz_tmp).init()
    with db.Session() as s:
        repo = ProdutoRepositorio(s)
        prod = repo.importar("ACUCAR CRISTAL DOCE DIA 2 Kgs", preco="9.99").produto
        repo.editar(prod.id, nome_sanitizado="Nome Mudado Depois")
        s.commit()
    db.engine.dispose()

    p = projetos.abrir_projeto(pid)
    assert p.nome == "Ofertas 08/07" and p.evento == "Terça do Pão"
    assert p.itens[0]["preco"] == "5,95"                    # preço da ÉPOCA
    assert p.itens[0]["nome"] == "Açúcar Cristal Doce Dia 2kg"
    assert p.validade_oferta == "01/07 ATÉ 27/07"


def test_override_manual_do_projeto_mantido(raiz_tmp):
    item = _item()
    item.nome = "Açúcar DD (abrev.)"       # mudança só deste projeto
    pid = projetos.salvar_projeto("P", None, "TABLOIDE", _layout(),
                                  [item.to_dict()])
    p = projetos.abrir_projeto(pid)
    assert p.itens[0]["nome"] == "Açúcar DD (abrev.)"


def test_imagem_congelada_sobrevive_ao_original(raiz_tmp, tmp_path):
    original = _png(tmp_path / "foto.png")
    pid = projetos.salvar_projeto("P", None, "TABLOIDE", _layout(),
                                  [_item(imagem=original).to_dict()])
    Path(original).unlink()                # a foto original some do mundo

    p = projetos.abrir_projeto(pid)
    congelada = p.itens[0]["imagem"]
    assert congelada and congelada != original
    assert Path(congelada).exists()        # a cópia do projeto vive


def test_arte_de_fundo_congelada(raiz_tmp, tmp_path):
    lay = _layout()
    lay.arquivo_fundo = _png(tmp_path / "arte.png")
    pid = projetos.salvar_projeto("P", None, "TABLOIDE", lay, [])
    Path(lay.arquivo_fundo).unlink()

    p = projetos.abrir_projeto(pid)
    assert p.layout.arquivo_fundo != str(tmp_path / "arte.png")
    assert Path(p.layout.arquivo_fundo).exists()


def test_layout_congelado_inline_nao_muda_com_o_atelie(raiz_tmp):
    pid = projetos.salvar_projeto("P", None, "TABLOIDE", _layout(n_regioes=2),
                                  [], nome_layout="Meu Layout")
    # o layout do Ateliê muda depois (vira 5 regiões)
    from app.core.database import Database
    from app.rendering.persistencia import salvar_layout

    db = Database(raiz_tmp).init()
    with db.Session() as s:
        salvar_layout(s, "Meu Layout", _layout(n_regioes=5))
        s.commit()
    db.engine.dispose()

    p = projetos.abrir_projeto(pid)
    assert len(p.layout.paginas[0].slots[0].regioes) == 2   # o da ÉPOCA


def test_listar_duplicar_excluir(raiz_tmp, tmp_path):
    foto = _png(tmp_path / "f.png")
    pid = projetos.salvar_projeto("Original", "Evento X", "CARTAZ", _layout(),
                                  [_item(imagem=foto).to_dict()])
    assert [p["nome"] for p in projetos.listar_projetos()] == ["Original"]

    novo = projetos.duplicar_projeto(pid, "Cópia da semana")
    lista = projetos.listar_projetos()
    assert {p["nome"] for p in lista} == {"Original", "Cópia da semana"}
    # a cópia tem a PRÓPRIA pasta de imagens (independente da original)
    p2 = projetos.abrir_projeto(novo)
    assert Path(p2.itens[0]["imagem"]).exists()
    p1 = projetos.abrir_projeto(pid)
    assert p1.itens[0]["imagem"] != p2.itens[0]["imagem"]

    projetos.excluir_projeto(pid)
    assert [p["nome"] for p in projetos.listar_projetos()] == ["Cópia da semana"]
    # FASE 2 (passo 82): excluir virou SOFT — a pasta FICA (lixeira de 30
    # dias, R-008); quem a leva é a purga ou o "Excluir agora" do Cofre
    assert Path(p1.itens[0]["imagem"]).exists()
    from app.core import lixeira
    lixeira.excluir_agora("projeto", pid)
    assert not Path(p1.itens[0]["imagem"]).exists()          # agora sim

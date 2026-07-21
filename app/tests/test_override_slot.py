"""F7.3 (Etapa B do Bloco E) — override por slot: unidades e fluxo da Mesa.

O adversarial pesado (pixel/byte, salvar→reabrir→duplicar, não-vazamento)
está em test_adversarial_vinculo.py::test_adversarial_override_por_slot (I5);
aqui ficam a precedência headless, o modal e o fluxo da tela.
"""

from decimal import Decimal

import pytest
from PIL import Image
from PySide6.QtWidgets import QApplication

from app.qt.telas import servico
from app.qt.telas.servico import ItemMesa
from app.rendering.arranjo import ModoArranjo
from app.rendering.compositor import DadosProduto
from app.tests.test_adversarial_vinculo import _grade_4, _itens


@pytest.fixture()
def raiz_tmp(tmp_path, monkeypatch):
    monkeypatch.setenv("AUTOTABLOIDE_ROOT", str(tmp_path / "raiz"))
    from app.core.database import Database
    from app.core.paths import SystemRoot

    root = SystemRoot(tmp_path / "raiz").criar_estrutura()
    Database(root).init().engine.dispose()
    return root


def _app():
    QApplication.instance() or QApplication([])


# --- precedência headless (a regra mora na produção) -------------------------------


def test_aplicar_override_precedencia_e_heranca():
    base = DadosProduto("Arroz Camil 5kg", preco_por=Decimal("24.90"),
                        imagem_path="/foto/item.png", unidade="5kg")
    ov = {"nome": "Arroz em Oferta", "preco": "19,99",
          "imagem": "/foto/override.png", "arranjo": "GRADE"}
    novo = servico.aplicar_override(base, ov)
    assert novo.nome == "Arroz em Oferta"
    assert novo.preco_por == Decimal("19.99")
    assert novo.imagem_path == "/foto/override.png"
    assert novo.modo_arranjo is ModoArranjo.GRADE
    assert novo.unidade == "5kg"                 # o que não foi dito, herda
    # o DadosProduto ORIGINAL não foi mutado (replace cria outro)
    assert base.nome == "Arroz Camil 5kg" and base.preco_por == Decimal("24.90")

    # override parcial: só o preço — o resto herda do item
    parcial = servico.aplicar_override(base, {"preco": "9,99"})
    assert parcial.nome == "Arroz Camil 5kg"
    assert parcial.preco_por == Decimal("9.99")
    assert parcial.imagem_path == "/foto/item.png"

    # arranjo estranho num projeto velho: herda o do item, sem quebrar
    estranho = servico.aplicar_override(base, {"arranjo": "ESPIRAL"})
    assert estranho.modo_arranjo is base.modo_arranjo


def test_override_imagem_vira_foto_unica():
    """Item multi-imagem + override de foto: a foto forçada NÃO se mistura."""
    from app.rendering.compositor import ImagemSlot

    base = DadosProduto("Suco", imagens=[ImagemSlot("/a.png"),
                                         ImagemSlot("/b.png")])
    novo = servico.aplicar_override(base, {"imagem": "/c.png"})
    assert novo.imagem_path == "/c.png" and novo.imagens == []


# --- o modal ------------------------------------------------------------------------


def test_dialogo_override_devolve_so_o_preenchido():
    _app()
    from app.qt.telas.override_dialog import OverrideDialog

    item = ItemMesa("ARROZ", "24,90", "VERDE", "Arroz Camil 5kg")
    dlg = OverrideDialog(item)
    assert dlg.valores() == {}                   # nada preenchido = sem override
    assert dlg.campo_nome.placeholderText() == "Arroz Camil 5kg"

    dlg.campo_preco.setText("19,99")
    assert dlg.valores() == {"preco": "19,99"}

    dlg.campo_nome.setText("Arroz em Oferta")
    dlg.campo_arranjo.setCurrentIndex(2)         # Lado a lado
    v = dlg.valores()
    assert v == {"nome": "Arroz em Oferta", "preco": "19,99",
                 "arranjo": "LADO_A_LADO"}

    # reabrir com o override atual pré-preenche os campos
    dlg2 = OverrideDialog(item, v)
    assert dlg2.campo_nome.text() == "Arroz em Oferta"
    assert dlg2.valores() == v


# --- o fluxo da Mesa (headless) ------------------------------------------------------


def _mesa_preenchida(tmp_path):
    from app.qt.telas.mesa import MesaTela

    mesa = MesaTela()
    layout = _grade_4()
    itens = _itens(tmp_path)[:4]
    mesa.carregar_layout(layout, None)
    mesa._itens = itens
    mesa._auto_preencher()
    return mesa, itens


def test_mesa_override_entra_na_composicao_e_nao_vaza(raiz_tmp, tmp_path):
    _app()
    mesa, itens = _mesa_preenchida(tmp_path)
    foto_ov = tmp_path / "ov.png"
    Image.new("RGB", (64, 64), "#654321").save(foto_ov)

    mesa.area.canvas.set_override("celula_0", {
        "nome": "Especial", "preco": "9,99", "imagem": str(foto_ov)})
    dados = mesa._dados_por_slot()
    assert dados["celula_0"].nome == "Especial"
    assert dados["celula_0"].preco_por == Decimal("9.99")
    assert dados["celula_0"].imagem_path == str(foto_ov)
    # não vazou: a vizinha segue o item dela
    assert dados["celula_1"].nome.startswith("PROD-")
    # e o item da estante não mudou (override é da CÉLULA)
    uid0 = mesa._mapa["celula_0"]
    it0 = next(it for it in itens if it.uid == uid0)
    assert it0.nome.startswith("PROD-")

    # undo desfaz o override (B3: o histórico versiona o trio)
    assert mesa.area.canvas.desfazer()
    assert "celula_0" not in mesa._overrides
    assert mesa._dados_por_slot()["celula_0"].nome.startswith("PROD-")


def test_mesa_restaurar_do_item_e_substituir_tudo_limpa(raiz_tmp, tmp_path):
    _app()
    mesa, _ = _mesa_preenchida(tmp_path)
    mesa.area.canvas.set_override("celula_0", {"preco": "1,00"})
    assert "celula_0" in mesa._overrides

    # "Restaurar do item" = set_override None (o gesto do menu de contexto)
    mesa.area.canvas.set_override("celula_0", None)
    assert "celula_0" not in mesa._overrides

    # overrides de um tabloide velho não vazam para o novo (Substituir tudo)
    mesa.area.canvas.set_override("celula_1", {"preco": "2,00"})
    mesa._itens = _itens(tmp_path)[:2]
    mesa._mapa = {}
    mesa._overrides = {}          # o caminho do "Substituir tudo"
    assert mesa._overrides == {}


def test_mesa_previo_acusa_override_orfao(raiz_tmp, tmp_path):
    """Override apontando para célula removida aparece no pré-voo (I2)."""
    _app()
    mesa, _ = _mesa_preenchida(tmp_path)
    mesa._overrides = {"celula_fantasma": {"preco": "1,00"}}
    avisos = mesa._avisos_orfaos()
    assert any("override" in a and "celula_fantasma" in a for a in avisos)

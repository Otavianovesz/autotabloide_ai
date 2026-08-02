"""RODADA JORNAL DO MÊS — BLOCO 3: composto sem-IA + +18 (03/08/2026).

"ARROZ SOMAR e TIO BONINI 5 Kgs" é UM preço para DOIS produtos — o app
tinha o mecanismo completo do composto (RG-29/F7.2) mas o gatilho era
SÓ a IA: sem LM Studio, `componentes` voltava vazio e o dono era levado
a criar um produto-remendo com as duas marcas no nome (a queixa dele).
A pendência determinística "multiplos" que o sanitize JÁ levantava era
jogada fora, e a curadoria nunca perguntava "são 2 produtos?".

O +18: sem LM, `mais18=False` cravado (a cerveja Amstel passava sem
selo) — e `finalizar_criacao` gravava `selo_mais18` mas NUNCA
`bebida_alcoolica`, o campo que a regra do selo automático e o Excel
leem (o round-trip podia reverter o +18).

Decisões do dono: "Arroz Somar e Tio Bonini · 5 kg"; embalagem por
componente entre parênteses quando difere. Testes L1 (vermelhos antes).
"""

import pytest

from app.core.database import Database
from app.core.paths import SystemRoot


# ================================================================== 3.1
# A pendência "multiplos" viaja e vira sugestão determinística
# ======================================================================


def test_dividir_em_dois_nas_linhas_reais():
    from app.qt.telas.servico import dividir_em_dois

    assert dividir_em_dois("ARROZ SOMAR e TIO BONINI 5 Kgs") \
        == ["Arroz Somar 5kg", "Arroz Tio Bonini 5kg"]
    # o tipo (1º token) replica no 2º componente; o peso comum idem
    assert dividir_em_dois("MOLHO TOMATE FUJINI e CAJAMAR 340g") \
        == ["Molho Tomate Fujini 340g", "Molho Cajamar 340g"]
    # BARRA = sabores/variantes (família), NUNCA composto de marcas
    assert dividir_em_dois("SARDINHA COQUEIRO 125 g TOMATE/OLEO E LIMÃO") \
        == []
    # sem " e " não há o que dividir
    assert dividir_em_dois("ACUCAR CRISTAL DOCE DIA 2 Kgs") == []


def test_pendencia_multiplos_viaja_no_item(tmp_path, monkeypatch):
    monkeypatch.setenv("AUTOTABLOIDE_ROOT", str(tmp_path / "raiz"))
    from app.qt.telas.servico import conciliar_linhas

    res = conciliar_linhas(
        [("ARROZ SOMAR e TIO BONINI 5 Kgs", "18,81", None)],
        lambda *_: None)
    (item,) = res.itens
    assert "multiplos" in item.pendencias


def test_enriquecer_sem_ia_sugere_o_composto():
    """Sem LM: a pendência "multiplos" vira `possivel_composto=True` com
    a sugestão determinística — a curadoria PERGUNTA em vez de o dono
    criar remendo. A decisão é sempre do humano (check desmarcado)."""
    from app.qt.telas.servico import enriquecer_descricao

    p = enriquecer_descricao("ARROZ SOMAR e TIO BONINI 5 Kgs", motor=None)
    assert p.possivel_composto is True
    assert p.sugestao_componentes \
        == ["Arroz Somar 5kg", "Arroz Tio Bonini 5kg"]
    # linha comum segue sem a pergunta
    p2 = enriquecer_descricao("ACUCAR CRISTAL DOCE DIA 2 Kgs", motor=None)
    assert p2.possivel_composto is False


def test_deve_revisar_no_lote():
    """A fila em lote NUNCA cria composto por chute: item que parece 2
    produtos e sem componentes confirmados fica "para revisar" com o
    motivo dito (I2) — como a perda de palavra já fazia."""
    from app.qt.telas.servico import PropostaCriacao, deve_revisar_no_lote

    p = PropostaCriacao(nome="X", mais18=False, categoria=None,
                        possivel_composto=True)
    assert deve_revisar_no_lote(p) is not None
    # com componentes confirmados (a IA decidiu) o lote segue criando
    p.componentes = ["A", "B"]
    assert deve_revisar_no_lote(p) is None
    # perda de palavra continua segurando (C-09)
    p2 = PropostaCriacao(nome="X", mais18=False, categoria=None,
                         tokens_perdidos=["PO"])
    assert deve_revisar_no_lote(p2) is not None
    p3 = PropostaCriacao(nome="X", mais18=False, categoria=None)
    assert deve_revisar_no_lote(p3) is None


# ================================================================== 3.2
# A pergunta na curadoria (headless)
# ======================================================================


def _app():
    from PySide6.QtWidgets import QApplication
    return QApplication.instance() or QApplication([])


def test_curadoria_pergunta_sao_dois_produtos():
    _app()
    from app.qt.telas.curadoria_dialog import CuradoriaDialog

    # sem IA: sugestão determinística, check DESMARCADO (o humano decide)
    dlg = CuradoriaDialog("Arroz Somar e Tio Bonini 5kg", [],
                          possivel_composto=True,
                          componentes=["Arroz Somar 5kg",
                                       "Arroz Tio Bonini 5kg"],
                          componentes_da_ia=False)
    try:
        assert not dlg.chk_composto.isChecked()
        assert dlg.componentes_finais() == []
        dlg.chk_composto.setChecked(True)
        assert dlg.componentes_finais() \
            == ["Arroz Somar 5kg", "Arroz Tio Bonini 5kg"]
        # os nomes são EDITÁVEIS — o humano é a fonte final
        dlg.comp_1.setText("Arroz Branco Somar 5kg")
        assert dlg.componentes_finais()[0] == "Arroz Branco Somar 5kg"
    finally:
        dlg.deleteLater()

    # com IA: componentes vieram do LM → "2 produtos" pré-marcado;
    # escolher "É um produto só" CANCELA (QUINTUSDECIMUS/J13: o check
    # virou a 3ª pergunta em rádios — cancelar é escolher outra resposta)
    dlg2 = CuradoriaDialog("Coração e Língua", [],
                           possivel_composto=True,
                           componentes=["Coração", "Língua"],
                           componentes_da_ia=True)
    try:
        assert dlg2.chk_composto.isChecked()
        dlg2.rb_um.setChecked(True)
        assert dlg2.componentes_finais() == []
    finally:
        dlg2.deleteLater()


def test_curadoria_tem_o_checkbox_mais18():
    """O +18 automático tem que ser VISÍVEL e editável (I2) — antes
    `proposta.mais18` viajava invisível até o banco."""
    _app()
    from app.qt.telas.curadoria_dialog import CuradoriaDialog

    dlg = CuradoriaDialog("Cerveja Amstel Lata 269ml", [], mais18=True)
    try:
        assert dlg.chk_mais18.isChecked()
        dlg.chk_mais18.setChecked(False)
        assert dlg.mais18_final() is False
    finally:
        dlg.deleteLater()


# ================================================================== 3.4
# O nome do composto: "· peso" e embalagem por parênteses
# ======================================================================


def test_nome_composto_com_o_peso_no_descritor():
    from app.qt.telas.servico import nome_composto

    assert nome_composto("Arroz Somar 5kg", "Arroz Tio Bonini 5kg") \
        == "Arroz Somar e Tio Bonini · 5 kg"


def test_nome_composto_com_embalagem_por_componente():
    """A decisão do dono (03/08): embalagem DIFERENTE por marca entra
    entre parênteses — "Milho Verde Fugini (pouch) e Bonare (lata)"."""
    from app.qt.telas.servico import nome_composto

    assert nome_composto("Milho Verde Fugini Pouch 170g",
                         "Milho Verde Bonare Lata 170g") \
        == "Milho Verde Fugini (pouch) e Bonare (lata) · 170 g"


def test_nome_composto_fallbacks_preservados():
    from app.qt.telas.servico import nome_composto

    # pesos diferentes: o formato antigo fica (o "·" só com peso COMUM;
    # prefixo comum preservado, como sempre foi)
    assert nome_composto("Arroz Camil 5kg", "Arroz Rei 1kg") \
        == "Arroz Camil 5kg e Rei 1kg"
    # sem peso nenhum: idem
    assert nome_composto("Coração", "Língua") == "Coração e Língua"


# ================================================================== 3.5
# +18 determinístico + bebida_alcoolica gravada
# ======================================================================


def test_eh_bebida_alcoolica():
    from app.core.mais18 import eh_bebida_alcoolica

    assert eh_bebida_alcoolica("Cerveja Amstel Lata 269ml") is True
    assert eh_bebida_alcoolica("APERITIVO CAMPARI 998 ml") is True
    assert eh_bebida_alcoolica("Vinho Tinto Suave 1,5L") is True
    assert eh_bebida_alcoolica("Vodka Smirnoff 998ml") is True
    # os vetos: vinagre não é vinho; sem álcool não é alcoólica
    assert eh_bebida_alcoolica("Vinagre de Vinho Tinto 750ml") is False
    assert eh_bebida_alcoolica("Cerveja Amstel Sem Alcool") is False
    assert eh_bebida_alcoolica("Cerveja Heineken 0,0 Lata") is False
    assert eh_bebida_alcoolica("Refrigerante Coca-Cola 2L") is False


def test_enriquecer_sem_ia_liga_o_mais18():
    """Sem LM o mais18 era False CRAVADO — a cerveja passava sem selo.
    A heurística determinística LIGA; nunca desliga o que a IA ligou."""
    from app.qt.telas.servico import enriquecer_descricao

    p = enriquecer_descricao("CERVEJA AMSTEL LATA 269 ML", motor=None)
    assert p.mais18 is True
    p2 = enriquecer_descricao("REFRIGERANTE COCA COLA 2 L", motor=None)
    assert p2.mais18 is False


def test_finalizar_criacao_grava_bebida_alcoolica(tmp_path, monkeypatch):
    """O furo do round-trip: selo_mais18 era gravado, bebida_alcoolica
    NÃO — e a regra do selo automático e o Excel leem bebida_alcoolica."""
    monkeypatch.setenv("AUTOTABLOIDE_ROOT", str(tmp_path / "raiz"))
    from app.core.models import Produto
    from app.qt.telas.servico import ItemMesa, finalizar_criacao

    item = ItemMesa(descricao="CERVEJA AMSTEL LATA 269 ML", preco="3,49",
                    semaforo="VERMELHO", nome="Cerveja Amstel Lata 269ml")
    finalizar_criacao(item, "Cerveja Amstel Lata 269ml", True, None)

    db = Database(SystemRoot(tmp_path / "raiz")).init()
    try:
        with db.Session() as s:
            p = s.query(Produto).filter(
                Produto.id == item.produto_id).one()
            assert bool(p.selo_mais18) is True
            assert bool(p.bebida_alcoolica) is True
    finally:
        db.engine.dispose()


# ================================================================== 3.3
# Foto por componente
# ======================================================================


def test_criar_como_composto_com_foto_por_componente(tmp_path, monkeypatch):
    monkeypatch.setenv("AUTOTABLOIDE_ROOT", str(tmp_path / "raiz"))
    from PIL import Image

    from app.core.models import Produto
    from app.qt.telas.servico import ItemMesa, criar_como_composto

    f1 = tmp_path / "a.png"
    f2 = tmp_path / "b.png"
    Image.new("RGBA", (40, 40), (255, 0, 0, 255)).save(f1)
    Image.new("RGBA", (40, 40), (0, 0, 255, 255)).save(f2)

    item = ItemMesa(descricao="MILHO VERDE FUGINI POUCH e BONARE 170 g",
                    preco="2,99", semaforo="VERMELHO", nome="x")
    comp = criar_como_composto(
        item, ["Milho Verde Fugini Pouch 170g",
               "Milho Verde Bonare Lata 170g"],
        False, [str(f1), str(f2)])
    assert comp.via == "composto"

    db = Database(SystemRoot(tmp_path / "raiz")).init()
    try:
        with db.Session() as s:
            fugini = s.query(Produto).filter(
                Produto.nome_sanitizado.contains("Fugini")).one()
            bonare = s.query(Produto).filter(
                Produto.nome_sanitizado.contains("Bonare")).one()
            assert fugini.caminho_imagem, "o 1º componente ficou sem foto"
            assert bonare.caminho_imagem, "o 2º componente ficou sem foto"
    finally:
        db.engine.dispose()


def test_criar_como_composto_compat_com_str(tmp_path, monkeypatch):
    """Compat: os chamadores antigos passam UMA string (a foto vai ao 1º
    componente, como sempre) — a assinatura nova não os quebra."""
    monkeypatch.setenv("AUTOTABLOIDE_ROOT", str(tmp_path / "raiz"))
    from app.qt.telas.servico import ItemMesa, criar_como_composto

    item = ItemMesa(descricao="CORACAO e LINGUA", preco="9,99",
                    semaforo="VERMELHO", nome="x")
    comp = criar_como_composto(item, ["Coração", "Língua"], False, None)
    assert comp.via == "composto"
    assert len(comp.origem_composto) == 2

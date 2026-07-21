"""F7.2 (Etapa D do Bloco E) — item composto "Camil e Rei": unidades e Mesa.

O adversarial da identidade (compor/separar/reabrir sem uid duplicado nem
órfão) está em test_adversarial_vinculo.py::test_adversarial_item_composto.
"""

import pytest
from PySide6.QtWidgets import QApplication

from app.qt.telas import servico
from app.qt.telas.servico import ItemMesa
from app.tests.test_adversarial_vinculo import _grade_4, _itens


def _app():
    QApplication.instance() or QApplication([])


# --- nome montado -------------------------------------------------------------------


def test_nome_composto_prefixo_e_sufixo_comuns():
    assert servico.nome_composto("Arroz Camil 5kg", "Arroz Rei 5kg") == \
        "Arroz Camil e Rei 5kg"
    assert servico.nome_composto("Feijão Preto Kicaldo 1kg",
                                 "Feijão Preto Máximo 1kg") == \
        "Feijão Preto Kicaldo e Máximo 1kg"
    # sem miolo distinto de um dos lados: cai no "A e B" simples
    assert servico.nome_composto("Arroz 5kg", "Arroz Rei 5kg") == \
        "Arroz 5kg e Arroz Rei 5kg"


# --- compor/separar headless ----------------------------------------------------------


def _dupla():
    a = ItemMesa("ARROZ CAMIL", "24,90", "VERDE", "Arroz Camil 5kg",
                 produto_id=7, imagem="/fotos/camil.png", unidade="5kg")
    b = ItemMesa("ARROZ REI", "22,90", "VERDE", "Arroz Rei 5kg",
                 produto_id=9, imagem="/fotos/rei.png", unidade="5kg",
                 mais18=False)
    return a, b


def test_compor_itens_campos_e_identidade():
    a, b = _dupla()
    comp = servico.compor_itens(a, b, preco="39,90")
    assert comp.uid not in (a.uid, b.uid)          # uid PRÓPRIO (1 slot → 1 uid)
    assert comp.nome == "Arroz Camil e Rei 5kg"
    assert comp.preco == "39,90"                   # preço ÚNICO da dupla
    assert [i for i in comp.imagens] == ["/fotos/camil.png", "/fotos/rei.png"]
    assert comp.arranjo == "LADO_A_LADO"           # o padrão da ordem
    assert comp.unidade == "5kg"                   # unidade comum preservada
    assert servico.eh_composto(comp)
    # os produto_id de origem ficam RASTREÁVEIS dentro do composto
    assert [o["produto_id"] for o in comp.origem_composto] == [7, 9]


def test_separar_devolve_exatamente_o_que_existia():
    a, b = _dupla()
    dict_a, dict_b = a.to_dict(), b.to_dict()
    comp = servico.compor_itens(a, b)
    v_a, v_b = servico.separar_item(comp)
    assert v_a.to_dict() == dict_a                 # idênticos, uid incluso
    assert v_b.to_dict() == dict_b
    assert v_a.uid == a.uid and v_b.uid == b.uid


def test_composto_nao_compoe_de_novo_e_normal_nao_separa():
    a, b = _dupla()
    comp = servico.compor_itens(a, b)
    c = ItemMesa("C", "1,00", "VERDE", "Outro")
    with pytest.raises(ValueError, match="profundidade"):
        servico.compor_itens(comp, c)
    with pytest.raises(ValueError, match="não é composto"):
        servico.separar_item(c)


# --- o fluxo da Mesa: estante e mapa consistentes --------------------------------------


def test_mesa_compor_e_separar_mapa_consistente(tmp_path):
    _app()
    from app.qt.telas.mesa import MesaTela

    mesa = MesaTela()
    mesa.carregar_layout(_grade_4(), None)
    itens = _itens(tmp_path)[:4]
    mesa._itens = itens
    mesa._auto_preencher()                         # 4 células, 4 uids
    a, b = itens[0], itens[1]
    slot_a = next(s for s, u in mesa._mapa.items() if u == a.uid)
    slot_b = next(s for s, u in mesa._mapa.items() if u == b.uid)

    mesa._executar_composicao(0, 1, "Dupla 1 e 2", "9,99")
    comp = mesa._itens[0]
    assert servico.eh_composto(comp) and len(mesa._itens) == 3
    assert mesa._mapa[slot_a] == comp.uid          # o composto herdou o slot de A
    assert slot_b not in mesa._mapa                # a célula de B esvaziou (visível)
    valores = list(mesa._mapa.values())
    assert len(set(valores)) == len(valores)       # NUNCA dois slots com o mesmo uid
    assert a.uid not in valores and b.uid not in valores

    mesa._executar_separacao(0)
    assert len(mesa._itens) == 4
    assert mesa._mapa[slot_a] == a.uid             # A voltou à célula dele
    assert comp.uid not in mesa._mapa.values()     # zero órfão do composto
    uids = [it.uid for it in mesa._itens]
    assert a.uid in uids and b.uid in uids and len(set(uids)) == 4
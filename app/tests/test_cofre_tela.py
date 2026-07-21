"""Tela do Cofre (F6.6) — lista de snapshots e diálogo de mesclagem."""

from PySide6.QtWidgets import QApplication

from app.core.portabilidade import AnalisePacote, Conflito, Decisao
from app.tests import seeds_portabilidade as seeds


def _app():
    QApplication.instance() or QApplication([])


def test_cofre_tela_lista_e_cria_backup(tmp_path):
    _app()
    from app.qt.telas.cofre import CofreTela

    root = seeds.raiz(tmp_path, "raiz")
    seeds.add_produto(root, "Coisa", "Marca", "1.00")
    tela = CofreTela(raiz=root)
    assert tela.lista.count() == 0
    tela._criar_backup()
    assert tela.lista.count() == 1
    assert "manual" in tela.lista.item(0).text()


def test_dialogo_mesclagem_decide_por_item_e_aplicar_a_todos():
    _app()
    from app.qt.telas.cofre import MesclagemDialog

    analise = AnalisePacote(
        novos=[{"nome": "Feijão 1kg"}],
        conflitos=[
            Conflito(id_decisao="produto:coca|coca", tipo="produto",
                     rotulo="Coca-Cola 2L (Coca-Cola)", campos=["preço"],
                     local={"preço": "8.99"}, pacote={"preço": "9.49"}),
            Conflito(id_decisao="produto:arroz|camil", tipo="produto",
                     rotulo="Arroz 5kg (Camil)", campos=["foto"]),
        ])
    dlg = MesclagemDialog(analise)

    # padrão conservador: manter o local (nada muda sem gesto explícito)
    assert set(dlg.decisoes().values()) == {Decisao.MANTER_LOCAL}

    # "aplicar a todos" muda os dois de uma vez
    dlg._combo_todos.setCurrentIndex(1)     # Usar o do pacote
    dlg._aplicar_a_todos()
    assert set(dlg.decisoes().values()) == {Decisao.USAR_PACOTE}

    # e a escolha POR ITEM tem a palavra final
    dlg._combos["produto:arroz|camil"].setCurrentIndex(2)   # Manter os dois
    d = dlg.decisoes()
    assert d["produto:coca|coca"] is Decisao.USAR_PACOTE
    assert d["produto:arroz|camil"] is Decisao.MANTER_AMBOS


def test_dialogo_sem_conflitos_nao_exige_nada():
    _app()
    from app.qt.telas.cofre import MesclagemDialog

    dlg = MesclagemDialog(AnalisePacote(novos=[{"nome": "X"}]))
    assert dlg.decisoes() == {}

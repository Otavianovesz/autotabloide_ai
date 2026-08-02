"""RODADA JORNAL DO MÊS — BLOCO 2A: a validade VIVA (03/08/2026).

O rodapé da tabela real diz "OFERTAS VALIDAS 03/08/2026 ATÉ 27/08/2026"
e o app: (a) não tinha parser nenhum (a string viajava CRUA ao chip e ao
desenho); (b) a cascata do calendário preenchia antes e a decisão de
adoção era incoerente (a linha pós-diálogo sobrescrevia até escolha
manual); (c) `avisos_da_validade` lia SÓ a primeira data sem ano — falso
"já passou" do dia 04/08 em diante; (d) a região só-data imprimia a data
de INÍCIO (03/08) no selo; (e) os 3 textos fixos do Jornal ("do dia 1º
ao 27") mentiam quando o mês começava dia 3 — decisão do dono: seguem a
validade viva.

Todos os testes daqui nasceram VERMELHOS no código antigo (L1).
"""

from datetime import date

import pytest


# ================================================================== 2A.1
# O parser nomeado: datas_da_validade
# ======================================================================


def test_parser_do_rodape_real_do_jornal():
    from app.core.validade import datas_da_validade

    de, ate = datas_da_validade(
        "OFERTAS VALIDAS 03/08/2026 ATÉ 27/08/2026")
    assert (de, ate) == (date(2026, 8, 3), date(2026, 8, 27))


def test_parser_dos_formatos_da_casa():
    from app.core.validade import datas_da_validade

    hoje = date(2026, 8, 1)
    assert datas_da_validade("OFERTA VÁLIDA DE 03/08 ATÉ 27/08", hoje) \
        == (date(2026, 8, 3), date(2026, 8, 27))
    assert datas_da_validade("DE 01/08 A 27/08", hoje) \
        == (date(2026, 8, 1), date(2026, 8, 27))
    assert datas_da_validade("SOMENTE 17/08", hoje) \
        == (date(2026, 8, 17), date(2026, 8, 17))
    assert datas_da_validade("ATÉ 24/08", hoje) == (None, date(2026, 8, 24))
    assert datas_da_validade("enquanto durarem os estoques", hoje) \
        == (None, None)
    assert datas_da_validade("", hoje) == (None, None)
    # a virada dez→jan: janeiro citado em dezembro é do ano seguinte
    assert datas_da_validade("SOMENTE 05/01", date(2026, 12, 28)) \
        == (date(2027, 1, 5), date(2027, 1, 5))
    # data que não existe é ignorada (as guardas de aviso cuidam dela)
    assert datas_da_validade("SOMENTE 32/13", hoje) == (None, None)


def test_normalizar_validade_da_tabela():
    """O cru do OCR vira o vocabulário canônico da casa — nunca mais
    "OFERTAS VALIDAS 03/08/2026..." cru no chip e no desenho."""
    from app.qt.telas.servico import normalizar_validade_tabela

    assert normalizar_validade_tabela(
        "OFERTAS VALIDAS 03/08/2026 ATÉ 27/08/2026") \
        == "OFERTA VÁLIDA DE 03/08 ATÉ 27/08"
    assert normalizar_validade_tabela("valido somente 17/08") \
        == "OFERTA VÁLIDA SOMENTE 17/08"
    assert normalizar_validade_tabela("sem data nenhuma") is None


# ================================================================== 2A.2
# A tabela vence a cascata — nunca a escolha do dono
# ======================================================================


def test_validade_vence():
    from app.qt.telas.servico import validade_vence

    tabela = "OFERTA VÁLIDA DE 03/08 ATÉ 27/08"
    # vence o vazio e o palpite do calendário
    assert validade_vence(None, None, tabela) is True
    assert validade_vence("DE 01/08 A 27/08", "cascata", tabela) is True
    # NUNCA a escolha humana (manual/projeto) em silêncio
    assert validade_vence("SOMENTE 05/08", "manual", tabela) is False
    # sem validade na tabela não há o que vencer
    assert validade_vence("DE 01/08 A 27/08", "cascata", None) is False
    assert validade_vence("DE 01/08 A 27/08", "cascata", "   ") is False


# ================================================================== 2A.3
# avisos_da_validade com ano e com o INTERVALO inteiro
# ======================================================================


def test_aviso_ja_passou_compara_com_a_data_fim():
    """O falso positivo que gritaria o mês INTEIRO do Jornal: dia 10/08,
    oferta válida até 27/08 — "já passou" era mentira."""
    from app.qt.telas.servico import avisos_da_validade

    rodape = "OFERTA VÁLIDA DE 03/08 ATÉ 27/08"
    assert avisos_da_validade(rodape, hoje=date(2026, 8, 10)) == []
    assert avisos_da_validade(rodape, hoje=date(2026, 8, 27)) == []
    # passou de verdade → avisa (e continua aviso, nunca veto)
    passado = avisos_da_validade(rodape, hoje=date(2026, 8, 28))
    assert any("já passou" in a for a in passado), passado


def test_aviso_respeita_o_ano_escrito():
    from app.qt.telas.servico import avisos_da_validade

    com_ano = "OFERTAS VALIDAS 03/08/2026 ATÉ 27/08/2026"
    assert avisos_da_validade(com_ano, hoje=date(2026, 8, 15)) == []
    passado = avisos_da_validade(com_ano, hoje=date(2027, 1, 10))
    assert any("já passou" in a for a in passado), passado


def test_aviso_fora_do_mes_considera_o_intervalo():
    from app.qt.telas.servico import avisos_da_validade

    rodape = "OFERTA VÁLIDA DE 28/07 ATÉ 27/08"
    # hoje DENTRO do intervalo que cruza o mês: silêncio
    assert avisos_da_validade(rodape, hoje=date(2026, 8, 10)) == []
    # guardas antigas continuam: data inexistente avisa; sem data, silêncio
    ruim = avisos_da_validade("SOMENTE 32/13", hoje=date(2026, 8, 1))
    assert any("não existe" in a for a in ruim), ruim
    assert avisos_da_validade("enquanto durarem os estoques") == []


# ================================================================== 2A.4
# A região só-data imprime a data-FIM
# ======================================================================


def test_so_data_imprime_a_data_fim():
    """O selo do Jornal deve dizer 27/08 (até quando vale) — imprimia
    03/08, o dia que a oferta COMEÇOU."""
    from app.rendering.compositor import DadosProduto, texto_composto_legal
    from app.rendering.model import (PapelTexto, Regiao, Retangulo,
                                     TipoRegiao)

    reg = Regiao(tipo=TipoRegiao.TEXTO_LEGAL,
                 rect=Retangulo(0, 0, 50, 10),
                 papel_texto=PapelTexto.VALIDADE, so_data=True)
    d = DadosProduto(nome="x",
                     texto_legal="OFERTA VÁLIDA DE 03/08 ATÉ 27/08")
    assert texto_composto_legal(reg, d) == "27/08"
    # data única continua ela mesma
    d2 = DadosProduto(nome="x", texto_legal="SOMENTE 17/08")
    assert texto_composto_legal(reg, d2) == "17/08"


# ================================================================== 2A.6
# Os 3 textos fixos do Jornal seguem a validade viva
# ======================================================================


def test_texto_com_periodo_vivo():
    from app.core.validade import texto_com_periodo_vivo

    validade = "OFERTA VÁLIDA DE 03/08 ATÉ 27/08"
    assert texto_com_periodo_vivo("PREÇO BAIXO DO DIA 1º AO 27",
                                  validade) == "PREÇO BAIXO DO DIA 3 AO 27"
    # caixa do molde preservada; o dia 1 ganha o ordinal
    assert texto_com_periodo_vivo(
        "ofertas do dia 1º ao 27 de todo mês",
        "OFERTA VÁLIDA DE 01/08 ATÉ 29/08") \
        == "ofertas do dia 1º ao 29 de todo mês"
    # sem par parseável (ou validade de 1 dia): o fixo fica INTACTO
    assert texto_com_periodo_vivo("PREÇO BAIXO DO DIA 1º AO 27",
                                  "SOMENTE 17/08") \
        == "PREÇO BAIXO DO DIA 1º AO 27"
    assert texto_com_periodo_vivo("PREÇO BAIXO DO DIA 1º AO 27", None) \
        == "PREÇO BAIXO DO DIA 1º AO 27"
    # texto sem o padrão nunca é tocado (os outros 6 encartes)
    assert texto_com_periodo_vivo("A CARNE MAIS BARATA DA CIDADE",
                                  validade) == "A CARNE MAIS BARATA DA CIDADE"


def test_o_livre_do_compositor_usa_o_periodo_vivo():
    """O caminho de produção: a manchete do Jornal (TEXTO_LEGAL LIVRE
    com texto fixo) recebe o período REAL da oferta na composição."""
    from app.rendering.compositor import DadosProduto, texto_composto_legal
    from app.rendering.model import (PapelTexto, Regiao, Retangulo,
                                     TipoRegiao)

    reg = Regiao(tipo=TipoRegiao.TEXTO_LEGAL,
                 rect=Retangulo(0, 0, 100, 10),
                 papel_texto=PapelTexto.LIVRE,
                 texto_fixo="PREÇO BAIXO DO DIA 1º AO 27")
    d = DadosProduto(nome="x",
                     texto_legal="OFERTA VÁLIDA DE 03/08 ATÉ 27/08")
    assert texto_composto_legal(reg, d) == "PREÇO BAIXO DO DIA 3 AO 27"
    # sem validade parseável o molde fica intacto (layout antigo idem)
    assert texto_composto_legal(reg, DadosProduto(nome="x")) \
        == "PREÇO BAIXO DO DIA 1º AO 27"


# ================================================================== 2A.5
# ValidadeDialog ganha o par de/até arbitrário
# ======================================================================


def _app():
    from PySide6.QtWidgets import QApplication
    return QApplication.instance() or QApplication([])


def test_validade_dialog_par_de_ate():
    _app()
    from PySide6.QtCore import QDate

    from app.qt.telas.validade_dialog import ValidadeDialog

    dlg = ValidadeDialog(hoje=date(2026, 8, 1))
    try:
        dlg.op_de_ate.setChecked(True)
        dlg.data_de.setDate(QDate(2026, 8, 3))
        dlg.data_ate.setDate(QDate(2026, 8, 27))
        assert dlg.valor() == "OFERTA VÁLIDA DE 03/08 ATÉ 27/08"
        # até < de: o "Usar" desabilita (nunca um intervalo impossível)
        dlg.data_ate.setDate(QDate(2026, 7, 30))
        assert not dlg._b_usar.isEnabled()
        dlg.data_ate.setDate(QDate(2026, 8, 27))
        assert dlg._b_usar.isEnabled()
    finally:
        dlg.deleteLater()


# ============================================================ integração
# A Mesa adota a validade da tabela pela regra (janela real)
# ======================================================================


@pytest.fixture()
def raiz_tmp(tmp_path, monkeypatch):
    monkeypatch.setenv("AUTOTABLOIDE_ROOT", str(tmp_path / "raiz"))
    from app.core.database import Database
    from app.core.paths import SystemRoot
    root = SystemRoot(tmp_path / "raiz").criar_estrutura()
    Database(root).init().engine.dispose()
    return root


def test_mesa_adota_tabela_sobre_cascata_e_respeita_manual(raiz_tmp):
    _app()
    from app.qt.telas.mesa import MesaTela

    mesa = MesaTela()
    try:
        cru = "OFERTAS VALIDAS 03/08/2026 ATÉ 27/08/2026"
        # cascata no chip (o que o carregar_layout faz) → a tabela vence
        mesa._validade = "DE 01/08 A 27/08"
        mesa._validade_origem = "cascata"
        assert mesa._adotar_validade_da_tabela(cru) is True
        assert mesa._validade == "OFERTA VÁLIDA DE 03/08 ATÉ 27/08"
        assert mesa._validade_origem == "tabela"
        # escolha manual fica de pé (aviso, nunca sobrescrita calada)
        mesa._validade = "SOMENTE 05/08"
        mesa._validade_origem = "manual"
        assert mesa._adotar_validade_da_tabela(cru) is False
        assert mesa._validade == "SOMENTE 05/08"
    finally:
        mesa.deleteLater()

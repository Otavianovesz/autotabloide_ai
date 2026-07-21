"""S1 e S2 da sessão ao vivo (§14 da ORDEM_F5_6) — com os PARES REAIS.

S1: a conciliação deu VERDE para marcas diferentes na tela do Otaviano
("Campo Largo"→"Aurora"; "Bonare"→"Cajamar e Etti"). Regra: divergência de
marca NUNCA é verde. S2: "Italac 200g 200.000g" — unidade duplicada e Decimal
sem normalizar.
"""

from decimal import Decimal

import pytest

from app.ai.conciliacao import Conciliador, LimiaresConciliacao, Semaforo
from app.core.database import Database
from app.core.paths import SystemRoot
from app.core.repositories import ProdutoRepositorio
from app.qt.telas.servico import _qtd_texto
from app.rendering.compositor import nome_com_unidade


@pytest.fixture()
def sessao(tmp_path, monkeypatch):
    monkeypatch.setenv("AUTOTABLOIDE_ROOT", str(tmp_path / "raiz"))
    root = SystemRoot(tmp_path / "raiz").criar_estrutura()
    db = Database(root).init()
    with db.Session() as s:
        yield s
    db.engine.dispose()


def _semear(s, nomes: list[str]) -> None:
    repo = ProdutoRepositorio(s)
    for n in nomes:
        repo.importar(n)
    s.commit()


# --- S1: os dois pares REAIS que saíram errados na tela --------------------------

def test_s1_campo_largo_nunca_vira_aurora(sessao):
    _semear(sessao, ["Suco de Uva Aurora Integral 1,5L"])
    # limiar baixo FORÇA o caminho do verde — a guarda tem que rebaixar
    conc = Conciliador(sessao, limiares=LimiaresConciliacao(verde=40, amarelo=20))
    v = conc.conciliar("Suco Uva Int. Campo Largo 1,5L")
    assert v.semaforo != Semaforo.VERDE           # NUNCA verde
    assert "aurora" in v.motivo.lower()           # e diz o porquê


def test_s1_bonare_nunca_vira_cajamar(sessao):
    _semear(sessao, ["Milho Verde Cajamar e Etti 170g Lata"])
    conc = Conciliador(sessao, limiares=LimiaresConciliacao(verde=40, amarelo=20))
    v = conc.conciliar("Milho Verde Bonare Lt 170G")
    assert v.semaforo != Semaforo.VERDE
    assert "cajamar" in v.motivo.lower() or "etti" in v.motivo.lower()


def test_s1_match_legitimo_continua_verde(sessao):
    """A guarda não pode matar o verde honesto (cadastro ⊆ oferta)."""
    _semear(sessao, ["Refrigerante Kitubaina 1,5L"])
    conc = Conciliador(sessao, limiares=LimiaresConciliacao(verde=60, amarelo=30))
    v = conc.conciliar("REFRIGERANTE KITUBAINA 1,5 LT")
    assert v.semaforo == Semaforo.VERDE


def test_s1_exato_e_alias_nao_sao_afetados(sessao):
    """Exato/alias são identidade aprendida — a guarda não os toca."""
    repo = ProdutoRepositorio(sessao)
    p = repo.importar("SUCO UVA AURORA 1,5L").produto
    repo.aprender_alias(p.id, "SUCO CASA NOSSA 1,5L")   # correção humana
    sessao.commit()
    conc = Conciliador(sessao)
    assert conc.conciliar("SUCO CASA NOSSA 1,5L").semaforo == Semaforo.VERDE


def test_s1_juiz_tambem_e_rebaixado(sessao):
    """Nem o juiz IA pode dar verde com marca divergente (§14: NUNCA)."""
    _semear(sessao, ["Suco de Uva Aurora Integral 1,5L"])

    class JuizConfiante:
        def disponivel(self):
            return True

        def chat(self, mensagens, formato_json=True):
            return '{"indice": 0, "confianca": 0.99}'

    conc = Conciliador(sessao, motor=JuizConfiante(),
                       limiares=LimiaresConciliacao(verde=95, amarelo=20))
    v = conc.conciliar("Suco Uva Int. Campo Largo 1,5L")
    assert v.semaforo != Semaforo.VERDE


# --- S2: unidade limpa e sem duplicar --------------------------------------------

def test_s2_qtd_texto_normaliza_decimal():
    assert _qtd_texto(Decimal("200.000")) == "200"     # saía "200.000"!
    assert _qtd_texto(Decimal("1.500")) == "1,5"       # saía "1.500"!
    assert _qtd_texto(Decimal("130.000")) == "130"
    assert _qtd_texto(Decimal("0.350")) == "0,35"
    assert _qtd_texto(Decimal("6")) == "6"


def test_s2_nome_nao_duplica_unidade():
    # os três casos REAIS da tela
    assert nome_com_unidade("Creme de Leite Italac 200g", "200g", False) == \
        "Creme de Leite Italac 200g"
    assert nome_com_unidade("Suco de Uva Campo Largo 1,5L", "1,5L", False) == \
        "Suco de Uva Campo Largo 1,5L"
    assert nome_com_unidade("Passatempo Chocolate 130g", "130g", False) == \
        "Passatempo Chocolate 130g"
    # anexa quando o nome NÃO tem a unidade (o comportamento bom continua)
    assert nome_com_unidade("Gelatina Apti", "35g", False) == "Gelatina Apti 35g"
    # com região UNIDADE no slot, nunca anexa
    assert nome_com_unidade("Gelatina Apti", "35g", True) == "Gelatina Apti"
    # variação de grafia (vírgula/ponto, espaços) também é pega
    assert nome_com_unidade("Suco Uva 1.5 L", "1,5L", False) == "Suco Uva 1.5 L"
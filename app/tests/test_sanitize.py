"""Testes da sanitização determinística (Fase 1)."""

from decimal import Decimal
from pathlib import Path

from app.core.sanitize import RegrasSanitizacao, sanitizar

FIXTURE = Path(__file__).parent / "fixtures" / "ofertas_belo_brasil.txt"


def _nomes_da_fixture() -> list[str]:
    linhas = FIXTURE.read_text(encoding="utf-8").splitlines()
    nomes = []
    for ln in linhas:
        ln = ln.strip()
        if ln and not ln.startswith("#"):
            nomes.append(ln.split("|")[0].strip())
    return nomes


# --- caixa + unidades ---------------------------------------------------------


def test_caixa_e_unidade_kg():
    r = sanitizar("AÇÚCAR CRISTAL DOCE DIA 2 Kgs")
    assert r.nome_sanitizado == "Açúcar Cristal Doce Dia 2kg"
    assert r.peso_valor == Decimal("2")
    assert r.peso_unidade == "kg"
    assert not r.precisa_ia


def test_litro_maiusculo():
    assert sanitizar("LEITE L. VIDA TRIANGULO 1 lt").nome_sanitizado == (
        "Leite L. Vida Triangulo 1L"
    )


def test_decimal_com_virgula():
    r = sanitizar("REFRIGERANTE KITUBAINA 1,5 LT")
    assert r.nome_sanitizado == "Refrigerante Kitubaina 1,5L"
    assert r.peso_valor == Decimal("1.5")
    assert r.peso_unidade == "L"


def test_numero_colado_na_unidade():
    assert sanitizar("BATATA PALHA BULNEZ 100 g").nome_sanitizado.endswith("100g")


# --- glossário de siglas ------------------------------------------------------


def test_sigla_tp_fica_maiuscula():
    assert "TP" in sanitizar("CREME de LEITE TP ITALAC 200 g").nome_sanitizado


def test_sigla_configuravel():
    regras = RegrasSanitizacao(siglas=frozenset({"ZZZ"}))
    assert "ZZZ" in sanitizar("PRODUTO ZZZ 100 g", regras).nome_sanitizado


# --- as regras NÃO reordenam (isso é da IA) -----------------------------------


def test_ordem_preservada_nao_reordena():
    # o peso (200g) continua onde estava, antes de "Tetra" — sem reordenar.
    assert sanitizar("CREME LEITE PIRACANJUBA 200 g TETRA").nome_sanitizado == (
        "Creme Leite Piracanjuba 200g Tetra"
    )


# --- pendências (o que vai para a IA) -----------------------------------------


def test_prefixo_suspeito():
    r = sanitizar("DE SODORANTE AEROSOL ABOVE ONE MEN 150 ml")
    assert r.precisa_ia
    assert any(p.codigo == "prefixo_suspeito" for p in r.pendencias)


def test_letra_isolada():
    r = sanitizar("OLE O de SOJA LIZA 900 ml")
    assert any(p.codigo == "letra_isolada" for p in r.pendencias)


def test_multiplas_marcas():
    r = sanitizar("AZEITE E. VIRGEM CARBONELL e GALLO CLÁSSICO 500 ml")
    assert any(p.codigo == "multiplos" for p in r.pendencias)


def test_lixo_de_ocr():
    r = sanitizar("PÃO CASEIRO BB X ___À___100 g___SÓ___")
    assert any(p.codigo == "lixo" for p in r.pendencias)


def test_abreviacao_com_ponto_nao_e_letra_isolada():
    # "L." (Longa Vida) não deve ser sinalizado como letra isolada.
    r = sanitizar("LEITE L. VIDA PARMALAT 1 LT INTEGRAL")
    assert not r.precisa_ia


# --- divisão (a)/(b) na fixture real ------------------------------------------


def test_divisao_da_fixture():
    resultados = [sanitizar(n) for n in _nomes_da_fixture()]
    limpos = [r for r in resultados if not r.precisa_ia]
    pendentes = [r for r in resultados if r.precisa_ia]
    assert len(resultados) == 42
    assert len(limpos) == 24
    assert len(pendentes) == 18

"""ORDEM F13-SEXTUS — A SEGUNDA REAL (o 1º teste ponta a ponta com o
dado do dono: a tabela de 27/07 e a foto do Kit Burguer).

S1: o parser come os prefixos "por"/"SÓ" e as linhas pontilhadas da
tabela impressa. S4/S5: o nome mais longo e o "TP/1,5LT" na vida real.
J18: a guarda de foto com DOIS objetos (o fantasma do Ninho e o
clipart do Sabão viram detecção). J16: o fluxo do Jornal distribui a
altura disponível (a faixa vazia morreu por número).
"""

from pathlib import Path

import pytest
from PIL import Image

# as 8 linhas REAIS da tabela "Segunda 27.07.jpeg" (como o OCR as lê)
LINHAS_REAIS = """KIT BURGUER SENEPOL BBX ______ POR ______ 39,00
CREME DE LEITE ITALAC 200G________ SÓ________ 2,44
LEITE CONDENSADO TRIANGULO 395G________ só ________ 7,44
BATATA PALHA BULNEZ CROCANTE 100G____ SÓ _____ 6,66
AZEITE GALLO EXTRA VIRGEM CLÁSSICO 500ML ____ SÓ ____ 38,80
SUCO DE UVA AURORA TINTO TP/1,5LT _____ POR ______ 19,99
LEITE INTEGRAL PARMALAT 1LT________ POR ________ 5,95
OLEO DE SOJA CONCORDIA 900ML____ só _____ 7,70"""


def test_s1_parser_come_prefixos_e_pontilhados():
    """S1: nenhuma linha da tabela real deixa "POR"/"SÓ"/underscore no
    NOME, e os 8 preços saem exatos — a tabela dele é um documento de
    impressão com ______ entre o nome e o preço."""
    from app.qt.telas.colagem import parse_colagem

    linhas = parse_colagem(LINHAS_REAIS)
    assert len(linhas) == 8, [li.nome for li in linhas]
    precos = [li.preco for li in linhas]
    assert precos == ["39,00", "2,44", "7,44", "6,66", "38,80",
                      "19,99", "5,95", "7,70"], precos
    for li in linhas:
        assert li.preco_valido, f"“{li.nome}”: {li.aviso}"
        assert "_" not in li.nome, f"underscore sobrou: “{li.nome}”"
        ultima = li.nome.split()[-1].lower().strip("_. ")
        assert ultima not in ("por", "só", "so"), (
            f"o prefixo de preço sobrou no nome: “{li.nome}”")
    assert linhas[0].nome == "KIT BURGUER SENEPOL BBX"
    assert linhas[5].nome == "SUCO DE UVA AURORA TINTO TP/1,5LT"


def test_s5_sanitizacao_do_tp_e_do_litro_real():
    """S5: "TP/1,5LT" vira "TP 1,5L" (o L maiúsculo é regra travada; o
    TP é sigla conhecida) e o Azeite Gallo (S4) sai com caixa correta
    sem partir palavra."""
    from app.core.sanitize import sanitizar

    r = sanitizar("SUCO DE UVA AURORA TINTO TP/1,5LT")
    nome = r.nome_sanitizado
    assert "1,5L" in nome.replace(" ", ""), nome
    assert "LT" not in nome.upper().replace("1,5L", "").replace(
        " ", ""), f"o LT sobreviveu: {nome}"
    r2 = sanitizar("AZEITE GALLO EXTRA VIRGEM CLÁSSICO 500ML")
    assert r2.nome_sanitizado.startswith("Azeite Gallo"), r2.nome_sanitizado
    assert "500ml" in r2.nome_sanitizado.replace(" ", ""), r2.nome_sanitizado


def test_j18_guarda_de_foto_com_dois_objetos(tmp_path):
    """J18: foto cujo alfa tem MAIS de um blob desconexo relevante
    (>5% cada) é SUSPEITA — produto + rótulo solto (o Ninho), dois
    objetos, ou clipart. O avaliador marca e diz o motivo; foto de um
    objeto só passa limpa."""
    from app.images.avaliador import avaliar_foto

    dois = Image.new("RGBA", (400, 400), (0, 0, 0, 0))
    for px in range(40, 180):
        for py in range(60, 340):
            dois.putpixel((px, py), (200, 30, 30, 255))
    for px in range(240, 370):
        for py in range(80, 320):
            dois.putpixel((px, py), (30, 30, 200, 255))
    p2 = tmp_path / "dois.png"
    dois.save(p2)
    av = avaliar_foto(p2)
    assert any("objeto" in m.lower() for m in av.motivos), (
        f"a foto com DOIS objetos não foi marcada: {av.motivos}")

    um = Image.new("RGBA", (400, 400), (0, 0, 0, 0))
    for px in range(80, 320):
        for py in range(60, 340):
            um.putpixel((px, py), (200, 30, 30, 255))
    p1 = tmp_path / "um.png"
    um.save(p1)
    av1 = avaliar_foto(p1)
    assert not any("objeto" in m.lower() for m in av1.motivos), (
        f"falso positivo com UM objeto: {av1.motivos}")


def test_j16_fluxo_distribui_a_altura_disponivel():
    """J16 (a 3ª vida do defeito — J5, J13, agora por número): quando o
    conteúdo escolhe um degrau e sobra altura na faixa, a sobra é
    DISTRIBUÍDA nas linhas (células mais altas, uniformes) — a página
    enche; a faixa vazia do rodapé morre. Alvo do arquiteto: razão de
    densidade ≥ 0,95."""
    from app.rendering.fluxo_jornal import FaixaFluxo, montar_fluxo

    faixa = FaixaFluxo(x=0, y=0, largura=800, altura=700,
                       colunas=(4,), alturas_celula=(200, 180),
                       altura_cabecalho=28)
    r = montar_fluxo([("A", 4), ("B", 4)], [faixa])
    fundo = max(c[1] + c[3] for b in r.blocos for c in b.celulas)
    assert fundo >= 0.96 * 700, (
        f"a faixa termina em {fundo}px de 700 — a sobra não foi "
        "distribuída (J16)")
    alturas = {round(c[3], 1) for b in r.blocos for c in b.celulas}
    assert len(alturas) == 1, (
        f"a distribuição quebrou a altura única (J2): {alturas}")

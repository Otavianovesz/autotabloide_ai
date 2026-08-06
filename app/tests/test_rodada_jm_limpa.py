"""RODADA JORNAL DO MÊS — BLOCO 1: a limpa transversal (03/08/2026).

A autocrítica do dono ("você fez só pro caso específico — passa a limpa")
medida contra a tabela REAL do Jornal de agosto: os plurais "5 Kgs"/
"1 LT"/"5 LTS" não casavam NENHUMA régua de peso fora do sanitize; a
metragem "12 x 30M" não existia; o "<>" e o código de coluna "T-1"
ficavam grudados no nome; nada corrigia "PÔ"→"PÓ"/"AÇUCAR"→"AÇÚCAR"; e
a conciliação refazia trabalho (1 GET de 3 s por item ambíguo + fuzzy
refeito por item na categoria-do-vizinho).

Todos os testes daqui nasceram VERMELHOS no código antigo (L1).
"""

import pytest

from app.core.database import Database
from app.core.paths import SystemRoot
from app.core.repositories import ProdutoRepositorio


@pytest.fixture
def session(tmp_path):
    db = Database(SystemRoot(tmp_path / "raiz")).init()
    s = db.Session()
    try:
        yield s
    finally:
        s.close()
        db.engine.dispose()


# ================================================================== 1.1
# Plurais nas três réguas irmãs (conciliação, busca de imagem, nome_fit)
# ======================================================================


def test_peso_canonico_entende_as_linhas_reais_do_jornal():
    """_peso_canonico só casava "998 ml" das 8 linhas medidas — o \\b
    depois de kg|l matava todo plural do documento do dono."""
    from app.ai.conciliacao import _peso_canonico

    assert _peso_canonico("ARROZ SOMAR e TIO BONINI 5 Kgs") == (5000.0, "g")
    assert _peso_canonico("LEITE L. VIDA PARMALAT 1 LT INTE GRAL") == (1000.0, "ml")
    assert _peso_canonico("AMACIANTE MON BIJOU 5 LTS PROTECAO e CLASSICO") \
        == (5000.0, "ml")
    assert _peso_canonico("SABAO PO OMO 1.6 Kgs CAIXETA") == (1600.0, "g")
    assert _peso_canonico("SUCO UVA TP 1.5 LTS") == (1500.0, "ml")
    # guardas do que JÁ funcionava
    assert _peso_canonico("APERITIVO CAMPARI 998 ml") == (998.0, "ml")
    assert _peso_canonico("LEITE PO NINHO 380g") == (380.0, "g")


def test_chave_comparacao_remove_o_peso_plural():
    """Com "Kgs" a medida FICAVA na chave do fuzzy e inflava o score —
    exatamente o que o comentário do regex diz que não pode acontecer."""
    from app.ai.conciliacao import _chave_comparacao

    chave = _chave_comparacao("ACUCAR CRISTAL DOCE DIA 2 Kgs")
    assert "kg" not in chave and "2" not in chave, chave
    chave2 = _chave_comparacao("AMACIANTE MON BIJOU 5 LTS")
    assert "lt" not in chave2 and "5" not in chave2, chave2


def test_desempate_de_irmaos_com_a_grafia_do_jornal(session):
    """O desempate por peso do ADENDO 30/07 NUNCA rodava nos formatos do
    Jornal ("5 Kgs" não casava a régua) — irmãos ficavam empatados."""
    from app.ai.conciliacao import Conciliador

    repo = ProdutoRepositorio(session)
    repo.importar("ARROZ BRANCO SOMAR 1 kg")
    repo.importar("ARROZ BRANCO SOMAR 5 kg")
    session.commit()

    v = Conciliador(session).conciliar("ARROZ BRANCO SOMAR 5 Kgs")
    assert v.produto is not None
    assert "5kg" in (v.produto.nome_sanitizado or "").lower(), (
        f"o peso plural não desempatou: casou {v.produto.nome_sanitizado!r}")


def test_busca_de_imagem_remove_a_gramatura_plural_da_query():
    """A query de foto ia à web COM a gramatura ("MON BIJOU 5 LTS") — a
    causa nº 1 de packshot errado, documentada no próprio busca.py."""
    from app.images.busca import remover_peso

    assert remover_peso("AMACIANTE MON BIJOU 5 LTS") == "AMACIANTE MON BIJOU"
    assert remover_peso("ARROZ SOMAR e TIO BONINI 5 Kgs") \
        == "ARROZ SOMAR e TIO BONINI"
    assert remover_peso("ACUCAR CRISTAL DOCE DIA 2 Kgs") \
        == "ACUCAR CRISTAL DOCE DIA"
    assert remover_peso("SUCO UVA TP 1.5 LTS") == "SUCO UVA TP"
    assert remover_peso("PAPEL HIG. MILLI 12 x 30M F. DUPLA") \
        == "PAPEL HIG. MILLI F. DUPLA"
    # guardas do que JÁ funcionava
    assert remover_peso("APERITIVO CAMPARI 998 ml") == "APERITIVO CAMPARI"
    assert remover_peso("LEITE L. VIDA PARMALAT 1 LT INTEGRAL") \
        == "LEITE L. VIDA PARMALAT INTEGRAL"


def test_dividir_descritor_protege_a_forma_crua():
    """QUARTUSDECIMUS §2 vale também para a grafia crua da tabela: "2
    Kgs"/"1 LT" é UNIDADE (metade protegida), nunca qualificador
    sacrificável — a coluna Unidade da planilha é texto livre."""
    from app.rendering.nome_fit import dividir_descritor

    assert dividir_descritor("2 Kgs") == (None, "2 Kgs")
    assert dividir_descritor("1 LT") == (None, "1 LT")
    assert dividir_descritor("5 LTS") == (None, "5 LTS")
    assert dividir_descritor("30 m") == (None, "30 m")
    assert dividir_descritor("12 rolos") == (None, "12 rolos")
    # a canônica continua protegida e o qualificador continua saindo
    assert dividir_descritor("tinto · 1,5 L") == ("tinto", "1,5 L")


def test_unidades_soltas_incluem_as_formas_cruas():
    """T4 (DUODECIMUS): a unidade solta no fim do nome desce ao
    descritor — agora também nas grafias do documento (KGS, LTS)."""
    from app.rendering.nome_fit import UNIDADES_SOLTAS

    for forma in ("kgs", "lts", "grs", "lt", "gr", "m"):
        assert forma in UNIDADES_SOLTAS, forma


# ================================================================== 1.2
# Metragem (30M) e contagem (rolos/folhas) — unidades que não existiam
# ======================================================================


def test_sanitiza_a_metragem_do_papel_higienico():
    """"12 x 30M" (papel higiênico) não era unidade nenhuma: o 30M
    ficava solto no meio do nome. Metragem exige 2+ dígitos."""
    from app.core.sanitize import sanitizar

    r = sanitizar("PAPEL HIG. MILLI 12 x 30M F. DUPLA")
    assert "30m" in r.nome_sanitizado, r.nome_sanitizado


def test_fita_3m_e_marca_nao_metragem():
    """O caso-limite escrito com a regra (§6): "3M" com UM dígito é
    MARCA (a fita adesiva), nunca metragem — fica intacto."""
    from app.core.sanitize import sanitizar

    r = sanitizar("FITA ADESIVA 3M")
    assert r.nome_sanitizado == "Fita Adesiva 3M", r.nome_sanitizado


def test_separar_peso_corta_metragem_e_contagem_no_fim():
    from app.core.sanitize import separar_peso

    assert separar_peso("Papel Aluminio Wyda 30M") \
        == ("Papel Aluminio Wyda", "30 m")
    assert separar_peso("Papel Higienico Milli 12 Rolos") \
        == ("Papel Higienico Milli", "12 rolos")
    assert separar_peso("Papel Toalha Snob 2 Folhas") \
        == ("Papel Toalha Snob", "2 folhas")


# ================================================================== 1.3
# separar_peso corta o peso também no INÍCIO (nunca no meio — a lei)
# ======================================================================


def test_separar_peso_corta_o_peso_no_inicio():
    """Sobra de divisão/coluna que COMEÇA com o peso: o peso desce ao
    descritor e o nome fica limpo."""
    from app.core.sanitize import separar_peso

    assert separar_peso("1 LT INTE GRAL") == ("INTE GRAL", "1 L")
    assert separar_peso("1.6 Kgs CAIXETA") == ("CAIXETA", "1,6 kg")


def test_separar_peso_leis_preservadas():
    """As leis da camada não mudam: peso no MEIO não é tocado (o peso
    pode qualificar o token seguinte) e nome que é SÓ peso não separa."""
    from app.core.sanitize import separar_peso

    assert separar_peso("Oferta 200g no Pacote") \
        == ("Oferta 200g no Pacote", None)
    assert separar_peso("5kg") == ("5kg", None)
    assert separar_peso("Leite Condensado Triangulo 395g") \
        == ("Leite Condensado Triangulo", "395 g")


# ================================================================== 1.4
# Colagem: o "<>" do documento e o código de coluna "T-1"
# ======================================================================

_TABELA_JORNAL = """\
ARROZ SOMAR e TIO BONINI 5 Kgs T-1 <> R$ 18,81
OLEO de SOJA CONCORDIA 900 ml T-1 <> R$ 6,90
LEITE L. VIDA PARMALAT 1 LT INTE GRAL T-2 <> R$ 4,29
ACUCAR CRISTAL DOCE DIA 2 Kgs T-1 <> R$ 5,99
APERITIVO CAMPARI 998 ml T-3 <> R$ 32,90
"""


def test_colagem_limpa_o_separador_e_o_codigo_de_coluna():
    """A tabela real: "<>" entre nome e preço e a coluna de código
    "T-1" repetida nas linhas — nada disso é nome de produto."""
    from app.qt.telas.colagem import parse_colagem

    linhas = parse_colagem(_TABELA_JORNAL)
    assert len(linhas) == 5
    nomes = [li.nome for li in linhas]
    assert nomes[0] == "ARROZ SOMAR e TIO BONINI 5 Kgs", nomes[0]
    assert nomes[2] == "LEITE L. VIDA PARMALAT 1 LT INTE GRAL", nomes[2]
    for n in nomes:
        assert "<" not in n and ">" not in n, n
        assert "T-1" not in n and "T-2" not in n and "T-3" not in n, n
    assert [li.preco for li in linhas][0] == "R$ 18,81"


def test_codigo_raro_de_borda_nao_e_coluna():
    """A guarda do caso-limite: "B-12" numa linha SÓ é nome (vitamina),
    não código de coluna — a remoção exige o token REPETIDO no lote."""
    from app.qt.telas.colagem import parse_colagem

    linhas = parse_colagem(
        "VITAMINA B-12 SUNDOWN <> R$ 19,90\n"
        "SABONETE DOVE <> R$ 3,50\n"
        "CREME DENTAL COLGATE <> R$ 4,90\n")
    assert linhas[0].nome == "VITAMINA B-12 SUNDOWN", linhas[0].nome


# ================================================================== 1.5
# Ortografia determinística (PÔ→PÓ, AÇUCAR→AÇÚCAR) + o vermelho nasce
# sanitizado + a guarda da IA enxerga tokens de 2 letras
# ======================================================================


def test_corrigir_acentos_do_vocabulario_de_mercado():
    from app.core.ortografia import corrigir_acentos

    assert corrigir_acentos("ACUCAR CRISTAL SOMAR") == "AÇÚCAR CRISTAL SOMAR"
    assert corrigir_acentos("LEITE PÔ NINHO") == "LEITE PÓ NINHO"
    assert corrigir_acentos("SABAO EM PO OMO") == "SABÃO EM PÓ OMO"
    assert corrigir_acentos("Oleo de Soja") == "Óleo de Soja"
    # caixa do molde preservada; já-correto é idempotente
    assert corrigir_acentos("Pão de Queijo") == "Pão de Queijo"
    # ambíguo NUNCA entra no seed: maca peruana é produto real
    assert corrigir_acentos("MACA PERUANA 100G") == "MACA PERUANA 100G"


def test_corrigir_acentos_junta_o_token_quebrado_conhecido():
    """O OCR quebra palavra no espaço errado ("INTE GRAL") — o bigrama
    conhecido é juntado deterministicamente."""
    from app.core.ortografia import corrigir_acentos

    assert corrigir_acentos("LEITE PARMALAT INTE GRAL") \
        == "LEITE PARMALAT INTEGRAL"
    # o 2º bigrama MEDIDO na foto real de agosto
    assert corrigir_acentos("DE SINFETANTE URCA 2 Lts VARIOS") \
        == "DESINFETANTE URCA 2 Lts VARIOS"


def test_sanitizar_passa_pela_ortografia():
    from app.core.sanitize import sanitizar

    # v2 (a 2ª prova do dono): "SABAO PO" ganha o "em" pelo bigrama —
    # "Sabão em Pó", nunca mais "Sabão Pó"
    r = sanitizar("SABAO PO OMO 1.6 Kgs CAIXETA")
    assert r.nome_sanitizado == "Sabão em Pó Omo 1,6kg Caixeta", \
        r.nome_sanitizado
    r2 = sanitizar("ACUCAR CRISTAL DOCE DIA 2 Kgs")
    assert r2.nome_sanitizado == "Açúcar Cristal Doce Dia 2kg", r2.nome_sanitizado


def test_item_vermelho_nasce_sanitizado(tmp_path, monkeypatch):
    """O item NOVO levava a descrição CRUA do OCR como nome do tabloide
    ("ACUCAR... 2 Kgs" ia ao desenho). Agora nasce sanitizado; a
    descrição crua fica preservada (alias/identidade intactos)."""
    monkeypatch.setenv("AUTOTABLOIDE_ROOT", str(tmp_path / "raiz"))
    from app.qt.telas.servico import conciliar_linhas

    res = conciliar_linhas(
        [("ACUCAR CRISTAL DOCE DIA 2 Kgs", "5,99", None)], lambda *_: None)
    (item,) = res.itens
    assert item.semaforo == "VERMELHO"
    assert item.nome == "Açúcar Cristal Doce Dia 2kg", item.nome
    assert item.descricao == "ACUCAR CRISTAL DOCE DIA 2 Kgs"


def test_guarda_da_ia_enxerga_tokens_de_2_letras():
    """"PÓ" tem 2 letras e era invisível à guarda RG-20 — a IA podia
    descartá-lo sem acusação. As unidades (kg, lt, kgs…) são stopwords:
    a canonização "5 LTS"→"5L" nunca grita à toa."""
    from app.ai.enriquecimento import tokens_perdidos

    assert "PO" in tokens_perdidos("LEITE PO NINHO 380g", "Leite Ninho 380g")
    assert tokens_perdidos("AMACIANTE MON BIJOU 5 LTS",
                           "Amaciante Mon Bijou 5L") == []
    # regressões da F13: o que não gritava continua sem gritar
    assert tokens_perdidos("SABAO EM PO YPE", "Sabão em Pó Ypê") == []
    assert "HUPPERS" in tokens_perdidos("FRALDA HUPPERS G", "Fralda Ruppers G")


# ================================================================== 1.6
# Desempenho da conciliação (a "demora" que o dono notou)
# ======================================================================


class _MotorContador:
    """Espião: conta os GETs de disponivel(); nunca responde (o juiz não
    entra — o que se mede é o número de checagens de vida)."""

    def __init__(self):
        self.chamadas = 0

    def disponivel(self) -> bool:
        self.chamadas += 1
        return False


def test_disponivel_e_checado_uma_vez_por_lote(session):
    """Era 1 GET HTTP (timeout 3 s) POR item ambíguo — num lote de 42
    itens do Jornal, até 2 minutos só perguntando se o motor vive."""
    from app.ai.conciliacao import Conciliador

    repo = ProdutoRepositorio(session)
    repo.importar("QUEIJO MUSSARELA PRESIDENTE 500 g")
    repo.importar("PRESUNTO COZIDO PERDIGAO 200 g")
    session.commit()

    from app.ai.conciliacao import LimiaresConciliacao

    motor = _MotorContador()
    # limiares que forçam TODO item com candidato à faixa do juiz —
    # o que se mede é quantas vezes o lote pergunta se o motor vive
    conc = Conciliador(session, motor=motor,
                       limiares=LimiaresConciliacao(verde=100.5, amarelo=1.0))
    for desc in ("QUEIJO MUSSARELA PRESIDENT 480 g",
                 "QUEIJO MUSARELA PRESIDENTE 510 g",
                 "PRESUNTO COZIDO PERDIGAO FATIADO",
                 "PRESUNTO COSIDO PERDIGAO 210 g"):
        conc.conciliar(desc)
    assert motor.chamadas <= 1, (
        f"disponivel() foi chamado {motor.chamadas}× no mesmo lote")


def test_categoria_dos_candidatos_opera_na_lista_ja_calculada():
    """A regra nomeada: a categoria do vizinho sai dos candidatos que o
    veredito JÁ tem — sem refazer fuzzy+embedding por item."""
    from types import SimpleNamespace

    from app.ai.conciliacao import Candidato, categoria_dos_candidatos

    laticinios = SimpleNamespace(nome="Laticínios")
    cands = [
        Candidato(SimpleNamespace(categoria=None), 96.0),
        Candidato(SimpleNamespace(categoria=laticinios), 88.0),
        Candidato(SimpleNamespace(categoria=laticinios), 60.0),
    ]
    assert categoria_dos_candidatos(cands, 75.0) == ("Laticínios", 88.0)
    # abaixo do piso não há palpite
    assert categoria_dos_candidatos(cands, 90.0) == (None, 0.0)
    assert categoria_dos_candidatos([], 75.0) == (None, 0.0)


def test_categoria_do_vizinho_pelo_lote_real(tmp_path, monkeypatch):
    """A/B: o caminho novo preenche a MESMA categoria que o antigo — o
    produto casado sem categoria ganha a do vizinho (D4/C-01), agora sem
    a 2ª passada de fuzzy."""
    monkeypatch.setenv("AUTOTABLOIDE_ROOT", str(tmp_path / "raiz"))
    root = SystemRoot(tmp_path / "raiz")
    db = Database(root).init()
    try:
        with db.Session() as s:
            repo = ProdutoRepositorio(s)
            repo.importar("IOGURTE MORANGO VIGOR 170 g")
            r2 = repo.importar("IOGURTE NATURAL VIGOR 170 g")
            s.commit()
            pid = r2.produto.id
            repo.editar(r2.produto.id, categoria="Laticínios")
            s.commit()
    finally:
        db.engine.dispose()

    from app.qt.telas.servico import conciliar_linhas
    conciliar_linhas([("IOGURTE MORANGO VIGOR 170 g", "3,99", None)],
                     lambda *_: None)

    db = Database(root).init()
    try:
        with db.Session() as s:
            from app.core.models import Produto
            morango = (s.query(Produto)
                       .filter(Produto.nome_sanitizado.contains("Morango"))
                       .one())
            assert morango.id != pid
            assert morango.categoria is not None
            assert morango.categoria.nome == "Laticínios"
    finally:
        db.engine.dispose()

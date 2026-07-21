"""
Testes do OCR e do fluxo completo (passo 4 da Fase 3), com MotorIAFake.
Validam o ENCANAMENTO: foto (stub) -> tabela -> conciliação -> enriquecimento.
"""

import pytest
from PIL import Image

from app.ai.conciliacao import Conciliador, Semaforo
from app.ai.ocr import _extrair_json_obj, ler_tabela
from app.ai.pipeline import processar_tabela
from app.core.database import Database
from app.core.paths import SystemRoot
from app.core.repositories import ProdutoRepositorio
from app.scripts.demo_pipeline import montar_fake_completo


@pytest.fixture
def session(tmp_path):
    db = Database(SystemRoot(tmp_path / "raiz")).init()
    s = db.Session()
    try:
        yield s
    finally:
        s.close()
        db.engine.dispose()


@pytest.fixture
def imagem(tmp_path):
    p = tmp_path / "stub.png"
    Image.new("RGB", (1200, 1600), "white").save(p)
    return str(p)


def test_extrair_json_obj_com_cercas():
    assert _extrair_json_obj('```json\n{"validade_oferta":"x","linhas":[]}\n```') == {
        "validade_oferta": "x",
        "linhas": [],
    }


def test_ler_tabela_fake(imagem):
    tabela = ler_tabela(imagem, montar_fake_completo())
    assert len(tabela.linhas) == 3
    assert tabela.linhas[0].descricao == "BOMBRIL 45 g"
    assert tabela.linhas[0].preco == "2,66"
    assert tabela.validade_oferta == "01/07/2026 até 27/07/2026"


def test_ler_tabela_sem_ia_vazio(imagem):
    from app.ai.fake import MotorIAFake

    tabela = ler_tabela(imagem, MotorIAFake(disponivel=False))
    assert tabela.linhas == [] and tabela.validade_oferta is None


def test_fluxo_completo(session, imagem):
    repo = ProdutoRepositorio(session)
    for nome in ["BOMBRIL 45 g", "REFRIGERANTE KITUBAINA 1,5 LT"]:
        repo.importar(nome)
    session.commit()

    motor = montar_fake_completo()
    conc = Conciliador(session)  # sem juiz -> semáforo fuzzy
    imp = processar_tabela(imagem, motor, conc, motor_enriquecimento=motor)
    assert imp.validade_oferta == "01/07/2026 até 27/07/2026"

    por_desc = {r.linha.descricao: r for r in imp.linhas}
    # existente -> verde
    assert por_desc["BOMBRIL 45 g"].veredito.semaforo == Semaforo.VERDE
    # abreviação -> amarelo
    assert por_desc["REFRI KITUBAINA 1,5 L"].veredito.semaforo == Semaforo.AMARELO
    # novo -> vermelho + enriquecido com 2 componentes (Carbonell/Gallo)
    azeite = por_desc["AZEITE E. VIRGEM CARBONELL e GALLO CLÁSSICO 500 ml"]
    assert azeite.veredito.semaforo == Semaforo.VERMELHO
    assert azeite.enriquecido is not None
    assert {c.marca for c in azeite.enriquecido.componentes} == {"Carbonell", "Gallo"}

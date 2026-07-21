"""
Testes da conciliação (passo 3 da Fase 3).

Exato/alias e fuzzy são REAIS (validam sem modelo). O "juiz" dos ambíguos usa o
MotorIAFake, claramente rotulado.
"""

import pytest

from app.ai.conciliacao import Conciliador, Semaforo
from app.ai.fake import MotorIAFake
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


def _semear(session):
    repo = ProdutoRepositorio(session)
    for nome in [
        "REFRIGERANTE KITUBAINA 1,5 LT",
        "LEITE PÓ NINHO INTEGRAL INSTANTANEO 380 g",
        "SABÃO PÓ TIXAN 1.6 Kgs CAIXETA MACIEZ / PRIMAVERA",
        "BOMBRIL 45 g",
        "NUTELLA 350 g FERRERO",
    ]:
        repo.importar(nome)
    session.commit()


def test_match_exato_verde(session):
    _semear(session)
    v = Conciliador(session).conciliar("BOMBRIL 45 g")
    assert v.semaforo == Semaforo.VERDE
    assert v.via == "exato"
    assert v.produto.nome_sanitizado == "Bombril 45g"


def test_variacao_abreviada_amarelo(session):
    _semear(session)
    v = Conciliador(session).conciliar("REFRI KITUBAINA 1,5 L")
    assert v.semaforo == Semaforo.AMARELO
    assert v.produto.nome_sanitizado.startswith("Refrigerante Kitubaina")


def test_item_novo_vermelho(session):
    _semear(session)
    v = Conciliador(session).conciliar("PILHA DURACELL AA 4 UN")
    assert v.semaforo == Semaforo.VERMELHO
    assert v.produto is None


def test_banco_vazio_da_vermelho(session):
    v = Conciliador(session).conciliar("QUALQUER COISA 1kg")
    assert v.semaforo == Semaforo.VERMELHO


def test_juiz_confirma_mas_divergencia_segura_no_amarelo(session):
    """Contrato S1 (§14 da ORDEM_F5_6): nem o juiz dá verde com termos do
    cadastro ausentes da oferta ("REFRI" ≠ "Refrigerante" → humano decide;
    a confirmação vira alias e da próxima vez é verde por identidade).
    O encanamento do juiz continua provado: o MOTIVO é o da divergência —
    ele só existe se o juiz devolveu a confirmação internamente."""
    _semear(session)
    fake = MotorIAFake(respostas_chat={"REFRI KITUBAINA": '{"indice": 0, "confianca": 0.9}'})
    v = Conciliador(session, motor=fake).conciliar("REFRI KITUBAINA 1,5 L")
    assert v.semaforo == Semaforo.AMARELO
    assert v.via == "juiz"
    assert "refrigerante" in v.motivo.lower()   # a guarda explica o porquê


def test_juiz_fake_marca_novo_como_vermelho(session):
    _semear(session)
    fake = MotorIAFake(respostas_chat={"REFRI KITUBAINA": '{"indice": null, "confianca": 0.8}'})
    v = Conciliador(session, motor=fake).conciliar("REFRI KITUBAINA 1,5 L")
    assert v.semaforo == Semaforo.VERMELHO
    assert v.via == "juiz"


def test_sem_motor_ambiguo_fica_amarelo(session):
    _semear(session)
    v = Conciliador(session, motor=None).conciliar("REFRI KITUBAINA 1,5 L")
    assert v.semaforo == Semaforo.AMARELO


class _EmbedderStub:
    """Embedder determinístico p/ teste: aproxima textos com 'nutel', afasta o resto."""

    def disponivel(self):
        return True

    def embeddings(self, textos):
        return [[1.0, 0.05, 0.0] if "nutel" in t else [0.0, 0.0, 1.0] for t in textos]


def test_sem_embeddings_typo_curto_fica_vermelho(session):
    # fuzzy puro não distingue 'NUTELA' (typo) do ruído -> vermelho.
    _semear(session)
    v = Conciliador(session).conciliar("NUTELA 350G")
    assert v.semaforo == Semaforo.VERMELHO


def test_embeddings_promovem_typo_para_amarelo(session):
    # com a camada de significado, 'NUTELA' encontra 'Nutella' -> amarelo.
    _semear(session)
    v = Conciliador(session, embedder=_EmbedderStub()).conciliar("NUTELA 350G")
    assert v.semaforo == Semaforo.AMARELO
    assert v.produto.nome_sanitizado.startswith("Nutella")

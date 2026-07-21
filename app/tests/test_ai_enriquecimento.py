"""
Testes do cliente de IA e do enriquecimento (passos 1 e 2 da Fase 3).

Tudo roda com o MotorIAFake — valida o ENCANAMENTO (entra texto -> sai estrutura),
não a qualidade da IA.
"""

from decimal import Decimal

from app.ai.client import ClienteOpenAICompat, ConfigIA
from app.ai.enriquecimento import _extrair_json, enriquecer
from app.ai.fake import MotorIAFake
from app.scripts.demo_enriquecimento import montar_fake


def test_fake_casa_resposta_por_trecho_do_prompt():
    fake = MotorIAFake(respostas_chat={"ABACAXI": '{"ok": true}'})
    assert fake.disponivel()
    assert fake.chat([{"role": "user", "content": "tem ABACAXI aqui"}]) == '{"ok": true}'


def test_enriquecer_degrada_sem_ia():
    fake = MotorIAFake(disponivel=False)
    r = enriquecer("BATATA PALHA BULNEZ 100 g", fake)
    assert r.origem == "deterministico"
    assert r.nome_sanitizado == "Batata Palha Bulnez 100g"


def test_enriquecer_json_vazio_degrada():
    fake = MotorIAFake(respostas_chat={})  # sempre devolve "{}"
    r = enriquecer("BATATA PALHA BULNEZ 100 g", fake)
    assert r.origem == "deterministico"


def test_enriquecer_peso_vem_do_deterministico():
    fake = montar_fake()
    r = enriquecer("CERVEJA AMSTEL 269 ml PALITO", fake)
    assert r.peso_valor == Decimal("269")
    assert r.peso_unidade == "ml"


def test_enriquecer_cerveja_categoria_e_mais18():
    r = enriquecer("CERVEJA AMSTEL 269 ml PALITO", montar_fake())
    assert r.origem == "ia"
    assert r.categoria == "Bebidas"
    assert r.bebida_alcoolica and r.mais18


def test_duas_marcas_geram_componentes_nao_nome_remendado():
    r = enriquecer("AZEITE E. VIRGEM CARBONELL e GALLO CLÁSSICO 500 ml", montar_fake())
    assert r.multi_produto
    assert {c.marca for c in r.componentes} == {"Carbonell", "Gallo"}
    assert not r.variantes


def test_dois_sabores_geram_variantes():
    r = enriquecer("ROSQUINHA MABEL 600 g COCO e LEITE", montar_fake())
    assert r.variantes == ["Coco", "Leite"]
    assert not r.componentes


def test_typo_corrigido_pela_ia():
    r = enriquecer("DE SODORANTE AEROSOL ABOVE ONE MEN 150 ml", montar_fake())
    assert r.nome_sanitizado.startswith("Desodorante")


def test_extrair_json_lida_com_cercas():
    assert _extrair_json('```json\n{"a": 1}\n```') == {"a": 1}


def test_cliente_sem_servidor_fica_indisponivel():
    cli = ClienteOpenAICompat(ConfigIA(base_url="http://127.0.0.1:59999/v1"))
    assert cli.disponivel() is False

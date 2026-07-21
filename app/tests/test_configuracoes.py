"""Etapa C do Bloco D (F6.7) — Configurações: C1 config viva, C2 prévia, C3 defaults sãos."""

from decimal import Decimal

from PySide6.QtWidgets import QApplication

from app.ai.client import ConfigIA
from app.ai.conciliacao import Conciliador, LimiaresConciliacao, limiares_de_config
from app.core.configuracao import aplicar_reformatacao, previa_reformatacao
from app.core.database import Database
from app.core.models import Produto
from app.core.repositories import ConfigRepositorio, regras_de_config
from app.core.sanitize import REGRAS_PADRAO, RegrasSanitizacao, formatar_nome, sanitizar
from app.tests import seeds_portabilidade as seeds


# --- C1: glossário de expansão no motor -------------------------------------------


def test_glossario_expande_sigla_no_nome():
    regras = RegrasSanitizacao(glossario_siglas=(("VD", "vidro"),
                                                 ("TP", "tetra pak")))
    assert sanitizar("PEPINO VD 300 G", regras).nome_sanitizado == \
        "Pepino Vidro 300g"
    assert formatar_nome("LEITE TP 1 LT", regras) == "Leite Tetra Pak 1L"
    # sem glossário (padrão), NADA muda — C3: default é o comportamento antigo
    assert sanitizar("PEPINO VD 300 G").nome_sanitizado == "Pepino Vd 300g"


def test_regras_de_config_leem_siglas_e_glossario(tmp_path):
    root = seeds.raiz(tmp_path, "raiz")
    db = Database(root).init()
    try:
        with db.Session() as s:
            cfg = ConfigRepositorio(s)
            cfg.set("sanitizacao.siglas", ["vd"])
            cfg.set("sanitizacao.glossario", {"TP": "tetra pak"})
            s.commit()
            regras = regras_de_config(s)
        assert "VD" in regras.siglas
        assert ("TP", "tetra pak") in regras.glossario_siglas
    finally:
        db.engine.dispose()


def test_regras_de_config_invalidas_caem_no_padrao(tmp_path):
    root = seeds.raiz(tmp_path, "raiz")
    db = Database(root).init()
    try:
        with db.Session() as s:
            cfg = ConfigRepositorio(s)
            cfg.set("sanitizacao.siglas", "não é lista")
            cfg.set("sanitizacao.glossario", [1, 2])
            s.commit()
            regras = regras_de_config(s)
        assert regras.siglas == REGRAS_PADRAO.siglas
        assert regras.glossario_siglas == ()
    finally:
        db.engine.dispose()


# --- C1: limiares do semáforo vivos ------------------------------------------------


def test_limiares_de_config_default_e_validacao(tmp_path):
    root = seeds.raiz(tmp_path, "raiz")
    db = Database(root).init()
    try:
        with db.Session() as s:
            cfg = ConfigRepositorio(s)
            assert limiares_de_config(s) == LimiaresConciliacao()   # sem chaves

            cfg.set("conciliacao.verde", 92.0)
            cfg.set("conciliacao.amarelo", 70.0)
            lim = limiares_de_config(s)
            assert (lim.verde, lim.amarelo) == (92.0, 70.0)

            cfg.set("conciliacao.verde", 50.0)      # incoerente: verde ≤ amarelo
            assert limiares_de_config(s) == LimiaresConciliacao()

            cfg.set("conciliacao.verde", "abobrinha")
            assert limiares_de_config(s) == LimiaresConciliacao()
    finally:
        db.engine.dispose()


def test_limiar_da_config_muda_o_semaforo_de_verdade(tmp_path):
    """O ponto da sessão ao vivo da Etapa D: trocar o limiar MUDA a conciliação."""
    root = seeds.raiz(tmp_path, "raiz")
    seeds.add_produto(root, "Café Pilão Torrado e Moído 500g", "Pilão", "18.90")
    entrada = "CAFE PILAO TORRADO E MOIDO 500G PROMOCAO"

    db = Database(root).init()
    try:
        with db.Session() as s:
            v1 = Conciliador(s).conciliar(entrada)      # limiares padrão (88/62)
            assert v1.semaforo.value == "VERDE" and v1.via == "fuzzy"

            ConfigRepositorio(s).set("conciliacao.verde", 99.5)
            ConfigRepositorio(s).set("conciliacao.amarelo", 10.0)
            s.commit()
            v2 = Conciliador(s).conciliar(entrada)      # relê a Config
            assert v2.semaforo.value == "AMARELO"       # mesmo item, limiar novo
    finally:
        db.engine.dispose()


# --- C1: IA pela Config (LM Studio ↔ Ollama sem código) ----------------------------


def test_config_ia_da_config_e_defaults_saos(tmp_path):
    root = seeds.raiz(tmp_path, "raiz")
    # sem chaves: o padrão de sempre
    assert ConfigIA.da_config(root).base_url == ConfigIA().base_url

    db = Database(root).init()
    with db.Session() as s:
        cfg = ConfigRepositorio(s)
        cfg.set("ia.base_url", "http://127.0.0.1:11434/v1")   # Ollama
        cfg.set("ia.modelo_texto", "llama3.2")
        cfg.set("ia.modelo_visao", "")                        # vazio = padrão
        s.commit()
    db.engine.dispose()

    c = ConfigIA.da_config(root)
    assert c.base_url == "http://127.0.0.1:11434/v1"
    assert c.modelo_texto == "llama3.2"
    assert c.modelo_visao == ConfigIA().modelo_visao          # vazio caiu no padrão

    # banco corrompido NUNCA derruba a IA (C3): cai no padrão
    quebrada = tmp_path / "quebrada"
    (quebrada / "banco").mkdir(parents=True)
    (quebrada / "banco" / "core.db").write_text("isto não é um sqlite")
    assert ConfigIA.da_config(quebrada).base_url == ConfigIA().base_url


# --- C2: prévia + aplicar ao acervo -------------------------------------------------


def test_previa_e_aplicar_reformatacao(tmp_path):
    root = seeds.raiz(tmp_path, "raiz")
    seeds.add_produto(root, "Pepino VD 300g", "Toscano", "11.90")
    seeds.add_produto(root, "Café Pilão 500g", "Pilão", "18.90")

    regras = RegrasSanitizacao(glossario_siglas=(("VD", "vidro"),))
    db = Database(root).init()
    try:
        with db.Session() as s:
            mudancas = previa_reformatacao(s, regras)
            assert mudancas == [("Pepino VD 300g", "Pepino Vidro 300g")]
            # a prévia NÃO gravou nada
            nomes = {p.nome_sanitizado for p in s.query(Produto).all()}
            assert "Pepino VD 300g" in nomes

            assert aplicar_reformatacao(s, regras) == 1
            s.commit()
            nomes = {p.nome_sanitizado for p in s.query(Produto).all()}
            assert "Pepino Vidro 300g" in nomes
            # idempotente: aplicar de novo não muda mais nada
            assert previa_reformatacao(s, regras) == []
    finally:
        db.engine.dispose()


# --- tela (C1+C3): carrega defaults, salva, valida ----------------------------------


def _tela(root):
    QApplication.instance() or QApplication([])
    from app.qt.telas.configuracoes import ConfiguracoesTela
    return ConfiguracoesTela(raiz=root)


def test_tela_carrega_defaults_e_salva(tmp_path):
    root = seeds.raiz(tmp_path, "raiz")
    tela = _tela(root)
    # banco antigo (sem as chaves novas) abre sem erro, com os padrões (C3)
    assert tela.campo_verde.value() == LimiaresConciliacao().verde
    assert tela.campo_rotacao.value() == 10

    tela.campo_siglas.setText("vd, pet")
    # FASE 3 (passo 51): o glossário virou TABELA — a linha "malformada"
    # de antes vira uma linha incompleta (só um lado preenchido)
    tela.campo_glossario.definir({"VD": "vidro", "TP": "tetra pak"})
    tela.campo_glossario._adicionar_linha()          # linha só pela metade
    from PySide6.QtWidgets import QTableWidgetItem
    tela.campo_glossario.tabela.setItem(
        2, 0, QTableWidgetItem("linha malformada"))
    tela.campo_url.setText("http://127.0.0.1:11434/v1")
    tela.campo_verde.setValue(92.0)
    tela.campo_amarelo.setValue(70.0)
    tela.campo_rotacao.setValue(5)
    assert tela._salvar() is True

    db = Database(root).init()
    try:
        with db.Session() as s:
            cfg = ConfigRepositorio(s)
            assert cfg.get("sanitizacao.siglas") == ["VD", "PET"]
            assert cfg.get("sanitizacao.glossario") == {"VD": "vidro",
                                                        "TP": "tetra pak"}
            assert cfg.get("ia.base_url") == "http://127.0.0.1:11434/v1"
            assert cfg.get("conciliacao.verde") == 92.0
            assert cfg.get("backups.rotacao") == 5
    finally:
        db.engine.dispose()


def test_tela_recusa_limiar_incoerente(tmp_path):
    root = seeds.raiz(tmp_path, "raiz")
    tela = _tela(root)
    tela.campo_verde.setValue(50.0)
    tela.campo_amarelo.setValue(70.0)       # amarelo acima do verde
    assert tela._salvar() is False          # nada gravado
    db = Database(root).init()
    try:
        with db.Session() as s:
            assert ConfigRepositorio(s).get("conciliacao.verde") is None
    finally:
        db.engine.dispose()


def test_preco_decimal_de_config_nao_precisa():
    """Guarda de regressão: o glossário NÃO toca tokens numéricos/unidades."""
    regras = RegrasSanitizacao(glossario_siglas=(("L", "lata"),))   # config maldosa
    # "1L" é token de peso (começa com dígito): o glossário não o alcança
    assert formatar_nome("COCA COLA 2 LTS", regras) == "Coca Cola 2L"

"""FASE 3 — Configurações em abas: nada quebra, nada se perde."""

import pytest
from PySide6.QtCore import QCoreApplication
from PySide6.QtWidgets import QApplication


@pytest.fixture()
def raiz_tmp(tmp_path, monkeypatch):
    monkeypatch.setenv("AUTOTABLOIDE_ROOT", str(tmp_path / "raiz"))
    from app.core.database import Database
    from app.core.paths import SystemRoot

    root = SystemRoot(tmp_path / "raiz").criar_estrutura()
    Database(root).init().engine.dispose()
    return root


def _config(chave):
    from app.core.database import Database
    from app.core.repositories import ConfigRepositorio
    db = Database().init()
    try:
        with db.Session() as s:
            return ConfigRepositorio(s).get(chave)
    finally:
        db.engine.dispose()


def test_abas_abrem_e_salvar_na_hora_persiste(raiz_tmp):
    """Passo 23: as 9 abas abrem sem erro; mudar um valor salva SOZINHO
    (debounce) e persiste na Config."""
    QApplication.instance() or QApplication([])
    from app.qt.telas.configuracoes import ConfiguracoesTela

    tela = ConfiguracoesTela()
    assert tela.lista_abas.count() == 9
    for i in range(9):                   # cada aba abre sem estourar
        tela.lista_abas.setCurrentRow(i)
        QCoreApplication.processEvents()
        assert tela._paginas.currentIndex() == i
    # salvar na hora: mexer num valor e drenar o debounce
    tela.campo_rotacao.setValue(7)
    tela._salvar_debounce.stop()
    tela._salvar_na_hora()               # o que o timer faria
    assert _config("backups.rotacao") == 7
    # validação (passo 18): limiar inválido NÃO sobrescreve o válido
    verde_antes = _config("conciliacao.verde")       # o 88 do 1º salvar
    tela.campo_verde.setValue(50.0)
    tela.campo_amarelo.setValue(60.0)
    tela._salvar_debounce.stop()
    tela._salvar_na_hora()
    assert tela.campo_verde.property("invalido") is True
    assert _config("conciliacao.verde") == verde_antes   # intacto
    tela.close()


def test_ultima_aba_lembrada(raiz_tmp):
    """Passo 21: reabrir cai na última aba visitada."""
    QApplication.instance() or QApplication([])
    from app.qt.telas.configuracoes import ConfiguracoesTela

    tela = ConfiguracoesTela()
    indice_ia = next(i for i, a in enumerate(tela._abas) if a[0] == "ia")
    tela.lista_abas.setCurrentRow(indice_ia)
    QCoreApplication.processEvents()
    tela.close()
    tela2 = ConfiguracoesTela()
    assert tela2._abas[tela2.lista_abas.currentRow()][0] == "ia"
    tela2.close()


def test_editar_dia_da_campanha_reflete_no_inicio(raiz_tmp):
    """Passo 39 (Bloco D): mudar o dia do evento PELO CAMINHO das
    Configurações (definir_dia — o mesmo que o EventoDialog usa) muda o
    "Produzir hoje" do Início. Conferido por CONTEÚDO."""
    from datetime import date

    QApplication.instance() or QApplication([])
    from PySide6.QtWidgets import QLabel
    from app.core.database import Database
    from app.qt.telas import eventos as ev_srv
    from app.qt.telas.dashboard import DashboardTela

    hoje = date.today().weekday()
    db = Database().init()
    try:
        with db.Session() as s:
            ev = ev_srv.criar_evento(s, "Quintou")
            ev_srv.definir_dia(s, ev.id, (hoje + 3) % 7)   # NÃO é hoje
            s.commit()
            ev_id = ev.id
    finally:
        db.engine.dispose()

    dash = DashboardTela()
    junto = " ".join(w.text() for w in dash._pratileiras.findChildren(QLabel))
    assert "Produzir hoje:" not in junto

    # o usuário edita o dia na aba Campanhas → cai no dia de hoje
    db = Database().init()
    try:
        with db.Session() as s:
            ev_srv.definir_dia(s, ev_id, hoje)
            s.commit()
    finally:
        db.engine.dispose()
    dash2 = DashboardTela()
    junto2 = " ".join(w.text() for w in
                      dash2._pratileiras.findChildren(QLabel))
    assert "Produzir hoje:" in junto2 and "Quintou" in junto2


def test_regra_de_validade_por_evento_tem_consumo(raiz_tmp):
    """Passo 36 (Bloco D): a regra "válido por N dias" da aba Campanhas
    NÃO é chave de mentira — sugerir_validade a consome. "dia" (ou sem
    regra) mantém o comportamento clássico: a próxima ocorrência."""
    from datetime import date, timedelta

    from app.core.database import Database
    from app.core.repositories import ConfigRepositorio
    from app.qt.telas import eventos as ev_srv
    from app.qt.telas.servico import sugerir_validade

    hoje = date(2026, 7, 15)                      # quarta
    db = Database().init()
    try:
        with db.Session() as s:
            ev = ev_srv.criar_evento(s, "Quintou")
            ev_srv.definir_dia(s, ev.id, 3)       # quinta
            ConfigRepositorio(s).set("eventos.validade_regra",
                                     {"Quintou": 3})
            s.commit()
    finally:
        db.engine.dispose()

    # regra N=3 → hoje+3 (18/07), NÃO a quinta (16/07)
    assert sugerir_validade("Quintou", hoje=hoje) == "ATÉ 18/07"

    # regra "dia" → volta ao clássico: próxima quinta
    db = Database().init()
    try:
        with db.Session() as s:
            ConfigRepositorio(s).set("eventos.validade_regra",
                                     {"Quintou": "dia"})
            s.commit()
    finally:
        db.engine.dispose()
    # auditoria do dono (20/07): a campanha de dia fixo vale SÓ NO DIA
    assert sugerir_validade("Quintou", hoje=hoje) == "SOMENTE 16/07"


def test_frases_prontas_persistem(raiz_tmp):
    """Passo 37: o campo de frases da aba Campanhas grava frases.validade
    (uma por linha, linhas vazias fora)."""
    QApplication.instance() or QApplication([])
    from app.qt.telas.configuracoes import ConfiguracoesTela

    tela = ConfiguracoesTela()
    tela.campo_frases.setPlainText(
        "OFERTA VÁLIDA ATÉ {data}\n\nSÓ NO {evento}\n")
    tela._salvar_debounce.stop()
    tela._salvar_na_hora()
    assert _config("frases.validade") == [
        "OFERTA VÁLIDA ATÉ {data}", "SÓ NO {evento}"]
    tela.close()


def test_testar_conexao_endpoint_falso_mostra_vermelho(raiz_tmp):
    """Checagem 48 (Bloco E): endpoint MORTO -> o teste de conexão pinta
    "Desligado" em vermelho SEM travar a tela (worker)."""
    import time

    QApplication.instance() or QApplication([])
    from app.qt.telas.configuracoes import ConfiguracoesTela

    tela = ConfiguracoesTela()
    tela.campo_url.setText("http://127.0.0.1:9/v1")     # porta morta
    tela._testar_conexao_ia()
    prazo = time.monotonic() + 15.0
    while time.monotonic() < prazo:
        QCoreApplication.processEvents()
        if tela._trabalhos._vivos == [] and tela.btn_testar_ia.isEnabled():
            break
        time.sleep(0.02)
    assert tela.btn_testar_ia.isEnabled()               # nunca fica preso
    assert "Desligado" in tela.rot_status_ia.text()
    assert "PERIGO" not in tela.rot_status_ia.styleSheet()  # cor resolvida
    from app.qt.design import tokens as t
    assert t.PERIGO in tela.rot_status_ia.styleSheet()  # vermelho de fato
    tela._trabalhos.encerrar()
    tela.close()


def test_interruptor_mestre_desliga_a_ia(raiz_tmp):
    """Passo 46: ia.usar=False -> disponivel() é False SEM tocar a rede
    (o modo determinístico assume; chave com consumo real)."""
    from app.ai.client import ClienteOpenAICompat, ConfigIA
    from app.core.database import Database
    from app.core.repositories import ConfigRepositorio

    db = Database().init()
    try:
        with db.Session() as s:
            ConfigRepositorio(s).set("ia.usar", False)
            s.commit()
    finally:
        db.engine.dispose()
    cli = ClienteOpenAICompat(ConfigIA.da_config())
    assert cli.config.usar is False
    assert cli.disponivel() is False

    db = Database().init()
    try:
        with db.Session() as s:
            ConfigRepositorio(s).set("ia.usar", True)
            s.commit()
    finally:
        db.engine.dispose()
    assert ConfigIA.da_config().usar is True


def test_prompt_da_dica_editavel_e_consumido(raiz_tmp):
    """Passo 45 (R-088): o prompt salvo na Config é o que a IA RECEBE no
    gerar_dica ({limite} trocado); vazio -> o padrão do app."""
    from app.ai.enriquecimento import (
        PROMPT_DICA_PADRAO, gerar_dica, prompt_dica,
    )
    from app.core.database import Database
    from app.core.repositories import ConfigRepositorio

    assert "MÁXIMO 120 caracteres" in prompt_dica(120)   # padrão

    db = Database().init()
    try:
        with db.Session() as s:
            ConfigRepositorio(s).set(
                "ia.prompt_dica",
                "Escreva SÓ receitas de família com {limite} letras.")
            s.commit()
    finally:
        db.engine.dispose()
    assert prompt_dica(99) == (
        "Escreva SÓ receitas de família com 99 letras.")

    class MotorEspiao:
        recebido = None
        def disponivel(self):
            return True
        def chat(self, mensagens, **kw):
            MotorEspiao.recebido = mensagens[0]["content"]
            return '{"dica": "Arroz com feijão nunca falha."}'

    dica = gerar_dica(["Arroz 5kg"], 200, MotorEspiao())
    assert dica == "Arroz com feijão nunca falha."
    assert MotorEspiao.recebido == (
        "Escreva SÓ receitas de família com 200 letras.")


def test_sigla_adicionada_na_tabela_muda_a_sanitizacao(raiz_tmp):
    """Passo 58 (Bloco F): adicionar um par na TABELA de glossário e
    salvar muda o formatar_nome de verdade (consumo ponta a ponta)."""
    QApplication.instance() or QApplication([])
    from app.core.database import Database
    from app.core.repositories import regras_de_config
    from app.core.sanitize import formatar_nome
    from app.qt.telas.configuracoes import ConfiguracoesTela

    tela = ConfiguracoesTela()
    tela.campo_glossario.definir({"VD": "vidro"})
    assert tela._salvar(silencioso=True) is True
    tela.close()

    db = Database().init()
    try:
        with db.Session() as s:
            regras = regras_de_config(s)
    finally:
        db.engine.dispose()
    assert "vidro" in formatar_nome("Azeitona VD 200g", regras).lower()


def test_remapear_atalho_persiste_aplica_e_barra_conflito(raiz_tmp):
    """Passo 59 (Bloco F, R-018): remapear persiste na Config e troca a
    tecla do QShortcut VIVO; tecla em uso no mesmo escopo é barrada."""
    QApplication.instance() or QApplication([])
    from PySide6.QtWidgets import QWidget

    from app.qt.design import atalhos as at
    at.recarregar_atalhos()

    dono = QWidget()
    disparos = []
    sc = at.criar_atalho("editor.duplicar", dono, lambda: disparos.append(1))
    assert sc.key().toString() == "Ctrl+D"

    at.aplicar("editor.duplicar", "Ctrl+J")        # remap
    assert sc.key().toString() == "Ctrl+J"         # o VIVO trocou na hora
    assert _config("atalhos.custom") == {"editor.duplicar": "Ctrl+J"}

    # conflito: Ctrl+S já é do "Salvar layout" no MESMO grupo (Ateliê)
    assert at.conflito("editor.duplicar", "Ctrl+S") is not None
    # e "Geral" cruza com todos: Ctrl+K é da busca global
    assert at.conflito("editor.duplicar", "Ctrl+K") is not None
    # tecla livre não acusa
    assert at.conflito("editor.duplicar", "Ctrl+9") is None

    # restaurar: volta o padrão no vivo e limpa a Config
    at.restaurar_padrao()
    assert sc.key().toString() == "Ctrl+D"
    assert _config("atalhos.custom") == {}
    dono.deleteLater()


def test_aplicar_ao_acervo_so_no_confirmar(raiz_tmp, monkeypatch):
    """Passo 60 (Bloco F): a prévia NUNCA aplica sozinha — cancelar deixa
    o acervo intacto; confirmar reformata (C2)."""
    QApplication.instance() or QApplication([])
    from PySide6.QtWidgets import QMessageBox

    from app.core.database import Database
    from app.core.models import Produto
    from app.qt.telas.configuracoes import ConfiguracoesTela

    db = Database().init()
    try:
        with db.Session() as s:
            s.add(Produto(nome_bruto="AZEITONA VD 200G",
                          nome_sanitizado="Azeitona VD 200g"))
            s.commit()
    finally:
        db.engine.dispose()

    tela = ConfiguracoesTela()
    tela.campo_glossario.definir({"VD": "vidro"})

    monkeypatch.setattr(QMessageBox, "exec", lambda self: None)
    # cancelar (clicou o 2º botão) → NADA muda
    monkeypatch.setattr(QMessageBox, "clickedButton",
                        lambda self: self.buttons()[1])
    tela._previa_acervo()
    db = Database().init()
    try:
        with db.Session() as s:
            nome = s.query(Produto).one().nome_sanitizado
    finally:
        db.engine.dispose()
    assert "VD" in nome                       # intacto

    # confirmar (1º botão = "Aplicar ao acervo") → reformata
    monkeypatch.setattr(QMessageBox, "clickedButton",
                        lambda self: self.buttons()[0])
    tela._previa_acervo()
    db = Database().init()
    try:
        with db.Session() as s:
            nome2 = s.query(Produto).one().nome_sanitizado
    finally:
        db.engine.dispose()
    assert "vidro" in nome2.lower()
    tela.close()


def test_de_para_completo_nenhuma_opcao_orfa(raiz_tmp):
    """Passo 94: TODA opção do configuracoes antigo tem lar novo — um
    salvar da tela grava o conjunto completo de chaves (e as novas da
    fase). Se alguém remover um campo sem dar lar, este teste acusa."""
    QApplication.instance() or QApplication([])
    from app.core.database import Database
    from app.core.repositories import ConfigRepositorio
    from app.qt.telas.configuracoes import ConfiguracoesTela

    tela = ConfiguracoesTela()
    assert tela._salvar(silencioso=True) is True
    tela.close()

    db = Database().init()
    try:
        with db.Session() as s:
            chaves = {c.chave for c in
                      s.query(__import__("app.core.models",
                                         fromlist=["Config"]).Config).all()}
    finally:
        db.engine.dispose()
    esperadas = {
        # o de-para do passo 24 (as 25 opções antigas)
        "sanitizacao.siglas", "sanitizacao.glossario",
        "tabloide.abreviacoes", "ia.base_url", "ia.modelo_texto",
        "ia.modelo_visao", "ia.modelo_embeddings", "conciliacao.verde",
        "conciliacao.amarelo", "backups.rotacao", "export.cmyk_pdf",
        "export.perfil_icc", "categorias.ordem", "marcas.proprias",
        "secoes.cor", "secoes.espessura_mm", "secoes.estilo",
        "secoes.cores_por_categoria", "imagem.modelo_rembg",
        # as novas da FASE 3 com consumo
        "ia.prompt_dica", "frases.validade", "sanitizacao.ordem",
        "sanitizacao.palavras_minusculas", "imagem.upscale_auto",
        "imagem.webp", "imagem.detector_fundo_branco",
    }
    faltando = esperadas - chaves
    assert not faltando, f"opções sem lar no salvar: {faltando}"
    # e as fora-do-salvar têm handler próprio (aparência/eventos/selos/
    # atalhos/ícone) — presença da porta na tela:
    for attr in ("chk_animacoes", "chk_transparencias", "chk_som",
                 "combo_escala", "lista_eventos_cfg", "lista_selos",
                 "tabela_atalhos", "combo_icone_app", "chk_usar_ia",
                 "chk_maquina_fraca"):
        assert hasattr(tela, attr), f"porta sumida: {attr}"

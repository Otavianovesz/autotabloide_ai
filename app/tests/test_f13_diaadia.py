"""ADENDO DO DONO (30/07) — o Almoxarifado e o OCR do dia a dia.

O dono usou o app e apontou: (1) não há como criar item no Almoxarifado;
(2) o OCR "não sabe puxar dois itens diferentes"; (3) item existente não
é reconhecido e ele é obrigado a criar duplicata — quer FORÇAR o vínculo.
A frota de scouts reproduziu as causas no banco real: a chave de
comparação (sem peso) COLIDE produtos irmãos e o setdefault esconde o
segundo; só o top-1 chega à UI; o rebaixamento S1 não entende "BB-X";
aliases herdados carregam o marcador "•" e nunca mais casam exato.
"""

import pytest

from app.ai.conciliacao import Conciliador, Semaforo
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


# ------------------------------------------------------------- motor --


def test_m1_irmaos_de_gramatura_sao_ambos_candidatos(session):
    """A causa nº1 do "não sabe puxar dois itens diferentes": a chave de
    comparação remove o peso e o setdefault deixava o 2º produto irmão
    INVISÍVEL — duas linhas do OCR casavam com o mesmo registro. Agora
    os irmãos são ambos candidatos e o PESO da oferta desempata."""
    repo = ProdutoRepositorio(session)
    repo.importar("PAO DE QUEIJO TRADICIONAL 500 g")
    repo.importar("PAO DE QUEIJO TRADICIONAL 1 kg")
    session.commit()

    v1 = Conciliador(session).conciliar("PAO DE QUEIJO TRADICIONAL 1kg")
    assert v1.produto is not None
    assert "1" in (v1.produto.nome_sanitizado or "") and \
        "kg" in (v1.produto.nome_sanitizado or "").lower(), (
        f"o peso não desempatou: casou {v1.produto.nome_sanitizado!r}")
    nomes = {c.produto.nome_sanitizado for c in v1.candidatos}
    assert len(nomes) >= 2, (
        f"o irmão de gramatura sumiu dos candidatos: {nomes}")

    v2 = Conciliador(session).conciliar("PAO DE QUEIJO TRADICIONAL 500G")
    assert v2.produto is not None and "500" in v2.produto.nome_sanitizado, (
        f"a oferta de 500g casou {v2.produto.nome_sanitizado!r}")


def test_m1_duas_linhas_nao_casam_o_mesmo_produto_em_silencio(session):
    """Exclusividade de lote: quando duas linhas do OCR apontam para o
    MESMO produto, a de menor score desce a AMARELO com o motivo dito —
    nunca dois verdes calados no mesmo registro."""
    from app.ai.conciliacao import exclusividade_de_lote

    repo = ProdutoRepositorio(session)
    repo.importar("MORTADELA PERDIGAO 500 g")
    session.commit()

    c = Conciliador(session)
    v_a = c.conciliar("MORTADELA PERDIGAO 500 g")      # exato
    v_b = c.conciliar("MORTADELA PERDIGAO FATIADA 500G")
    # força o cenário: os dois verdes no mesmo produto
    if v_b.semaforo != Semaforo.VERDE:
        v_b.semaforo = Semaforo.VERDE
        v_b.produto = v_a.produto
    exclusividade_de_lote([v_a, v_b])
    assert v_a.semaforo == Semaforo.VERDE
    assert v_b.semaforo == Semaforo.AMARELO
    assert "outra linha" in v_b.motivo.lower(), v_b.motivo


def test_m3_bbx_com_hifen_nao_rebaixa(session):
    """O rebaixamento S1 não entendia "BB-X": os tokens 'bb'/'x' (<3
    chars) não contavam e o 'bbx' do cadastro rebaixava o verde SEMPRE.
    Token do cadastro presente na oferta SEM espaços é presença."""
    repo = ProdutoRepositorio(session)
    repo.importar("FIGADO BOVINO BBX 100 g")
    session.commit()

    v = Conciliador(session).conciliar("FIGADO BOVINO BB-X 100G")
    assert v.semaforo == Semaforo.VERDE, (v.semaforo, v.motivo)


def test_m3_grafia_ocr_proxima_nao_rebaixa(session):
    """Erro de grafia do OCR (uma letra trocada/duplicada) não é
    divergência de marca: o token quase-igual (difflib ≥0,8) é perdoado
    — o score fuzzy continua mandando no semáforo."""
    repo = ProdutoRepositorio(session)
    repo.importar("TOTURGUITA MUSCULO SEM OSSO 100 g")
    session.commit()

    v = Conciliador(session).conciliar("TORTUGUITA MUSCULO SEM OSSO 100G")
    assert v.semaforo == Semaforo.VERDE, (v.semaforo, v.motivo)
    assert "termos ausentes" not in v.motivo, v.motivo


# ------------------------------------------------------ os gestos (UI) --


def _app():
    from PySide6.QtWidgets import QApplication
    return QApplication.instance() or QApplication([])


@pytest.fixture()
def raiz_tmp(tmp_path, monkeypatch):
    monkeypatch.setenv("AUTOTABLOIDE_ROOT", str(tmp_path / "raiz"))
    from app.core.database import Database
    from app.core.paths import SystemRoot
    from app.tests import acervo
    root = SystemRoot(tmp_path / "raiz").criar_estrutura()
    acervo.copiar_fontes_reais(root.fontes)
    Database(root).init().engine.dispose()
    return root


def _esperar(cond, ms=15000):
    from app.tests.gestos import drenar
    import time
    fim = time.time() + ms / 1000
    while time.time() < fim:
        drenar(60)
        if cond():
            return True
    return False


def _sem_fotos(dlg):
    """A fila de busca de fotos (web) na frente do worker atrasa o
    gesto na bancada — modo rápido, como os testes do Bloco D."""
    from app.tests.gestos import clicar, drenar
    if dlg.chk_fotos.isChecked():
        clicar(dlg.chk_fotos)
        drenar()


def test_a1_novo_produto_no_almoxarifado_por_gesto(raiz_tmp):
    """A queixa 1: não havia COMO cadastrar um item avulso. O botão
    "Novo produto…" pergunta o nome, a porta única ``importar`` cria
    (sanitizado, sem duplicar) e o produto está no banco."""
    from PySide6.QtCore import Qt
    from PySide6.QtWidgets import QInputDialog, QPushButton
    from app.qt.telas.almoxarifado import AlmoxarifadoTela
    from app.tests.gestos import clicar, drenar

    _app()
    tela = AlmoxarifadoTela()
    tela.setAttribute(Qt.WidgetAttribute.WA_DontShowOnScreen, True)
    tela.show()
    drenar()
    import app.qt.telas.almoxarifado as mod
    mod.QInputDialog = QInputDialog          # garantia do alvo do patch
    orig = QInputDialog.getText
    QInputDialog.getText = staticmethod(
        lambda *a, **k: ("Pao de Queijo Teste 500g", True))
    try:
        btn = next(b for b in tela.findChildren(QPushButton)
                   if "Novo produto" in b.text())
        clicar(btn)
        drenar(300)
    finally:
        QInputDialog.getText = orig
        tela.close()
    from app.core.database import Database
    from app.core.repositories import ProdutoRepositorio
    db = Database().init()
    try:
        with db.Session() as s:
            achados = ProdutoRepositorio(s).buscar("Pao de Queijo Teste")
            assert achados, "o produto avulso não nasceu no banco"
    finally:
        db.engine.dispose()


def test_a3_vincular_a_produto_existente_por_gesto(raiz_tmp):
    """A queixa 3: o vermelho obrigava a duplicata. O vínculo forçado
    ("é ESTE aqui") liga o item ao produto escolhido, vira VERDE e o
    banco APRENDE o alias — a próxima importação casa sozinha."""
    from PySide6.QtCore import Qt
    from app.qt.telas import servico
    from app.qt.telas.conciliacao_dialog import ConciliacaoDialog
    from app.tests.gestos import drenar

    _app()
    from app.core.database import Database
    from app.core.repositories import ProdutoRepositorio
    db = Database().init()
    try:
        with db.Session() as s:
            r = ProdutoRepositorio(s).importar("Coxa Sobrecoxa 100 g")
            s.commit()
            pid = r.produto.id
    finally:
        db.engine.dispose()

    it = servico.ItemMesa("COXA SOB COXA A 100g POR", "0,77", "VERMELHO",
                          "COXA SOB COXA A 100g POR")
    dlg = ConciliacaoDialog(servico.ResultadoMesa(itens=[it]), None)
    dlg.setAttribute(Qt.WidgetAttribute.WA_DontShowOnScreen, True)
    dlg.show()
    drenar()
    _sem_fotos(dlg)
    try:
        dlg._vincular(0, pid)
        assert _esperar(lambda: dlg.itens[0].semaforo == "VERDE"), (
            "o vínculo não pintou verde")
        assert dlg.itens[0].produto_id == pid
        assert dlg.itens[0].via == "alias"
    finally:
        dlg.close()
    # o banco aprendeu: a MESMA grafia agora casa exata
    from app.ai.conciliacao import Conciliador, Semaforo as Sem
    db = Database().init()
    try:
        with db.Session() as s:
            v = Conciliador(s).conciliar("COXA SOB COXA A 100g POR")
            assert v.semaforo == Sem.VERDE and v.via == "exato", (
                v.semaforo, v.via)
    finally:
        db.engine.dispose()


def test_a4_corrigir_o_texto_reconcilia_a_linha(raiz_tmp):
    """A edição inline do nome RE-CONCILIA na hora — o vermelho por
    erro do OCR vira verde só com o texto certo (antes nada recalculava
    e nascia duplicata)."""
    from PySide6.QtCore import Qt
    from app.qt.telas import servico
    from app.qt.telas.conciliacao_dialog import ConciliacaoDialog
    from app.tests.gestos import drenar

    _app()
    from app.core.database import Database
    from app.core.repositories import ProdutoRepositorio
    db = Database().init()
    try:
        with db.Session() as s:
            ProdutoRepositorio(s).importar("Figado Bovino BBX 100 g")
            s.commit()
    finally:
        db.engine.dispose()

    it = servico.ItemMesa("FGDO BVNO XPTO", "0,99", "VERMELHO",
                          "FGDO BVNO XPTO")
    dlg = ConciliacaoDialog(servico.ResultadoMesa(itens=[it]), None)
    dlg.setAttribute(Qt.WidgetAttribute.WA_DontShowOnScreen, True)
    dlg.show()
    drenar()
    _sem_fotos(dlg)
    try:
        cel = dlg.tabela.item(0, 1)
        cel.setText("FIGADO BOVINO BBX 100G")     # o gesto da correção
        assert _esperar(lambda: dlg.itens[0].semaforo == "VERDE"), (
            f"a correção não re-conciliou ({dlg.itens[0].semaforo})")
    finally:
        dlg.close()


def test_a4_ignorar_tem_desfazer(raiz_tmp):
    """O atalho R tornava o acidente fácil e sem volta — o Ignorar
    agora dá Desfazer (a linha volta ao lugar; nada foi ensinado)."""
    from PySide6.QtCore import Qt
    from app.qt.telas import servico
    import app.qt.telas.conciliacao_dialog as mod
    from app.tests.gestos import drenar

    _app()
    capturado = {}
    orig = mod.mostrar_toast_desfazer
    mod.mostrar_toast_desfazer = (
        lambda w, txt, ao_desfazer: capturado.update(acao=ao_desfazer))
    try:
        it = servico.ItemMesa("QUALQUER COISA 1kg", "1,00", "VERMELHO",
                              "QUALQUER COISA 1kg")
        dlg = mod.ConciliacaoDialog(servico.ResultadoMesa(itens=[it]), None)
        dlg.setAttribute(Qt.WidgetAttribute.WA_DontShowOnScreen, True)
        dlg.show()
        drenar()
        try:
            dlg._ignorar(0)
            assert not dlg.itens, "a linha não saiu"
            assert "acao" in capturado, "o toast de desfazer não apareceu"
            capturado["acao"]()
            assert len(dlg.itens) == 1 and \
                dlg.itens[0].descricao == "QUALQUER COISA 1kg", (
                "o desfazer não devolveu a linha")
        finally:
            dlg.close()
    finally:
        mod.mostrar_toast_desfazer = orig


def test_m4_alias_com_bullet_casa_exato(session):
    """Aliases herdados do OCR antigo carregam o marcador "•" no texto
    cru e nunca mais casavam exato. O match por alias agora é tolerante
    ao enfeite — nos dois sentidos."""
    repo = ProdutoRepositorio(session)
    r = repo.importar("FIGADO BOVINO 100 g")
    repo.aprender_alias(r.produto.id, "• FIGADO BOVINO CONGELADO 100 g")
    session.commit()

    v = Conciliador(session).conciliar("FIGADO BOVINO CONGELADO 100 g")
    assert v.semaforo == Semaforo.VERDE and v.via == "exato", (
        v.semaforo, v.via, v.motivo)

    v2 = Conciliador(session).conciliar("▶ FIGADO BOVINO CONGELADO 100 g")
    assert v2.semaforo == Semaforo.VERDE and v2.via == "exato", (
        v2.semaforo, v2.via, v2.motivo)

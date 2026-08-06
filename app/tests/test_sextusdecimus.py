"""ORDEM F13-SEXTUSDECIMUS — UMA LINHA, UMA CÉLULA (02/08/2026).

O modelo: quantos produtos nascem no banco é assunto do banco; a página
recebe UMA célula por linha da oferta, com N fotos dentro (I6). E a lei
L14: recurso que só atende o primeiro de N não é entregue — ou fecha o
N, ou a tela não oferece.

Testes L1 — vermelhos no código de antes da ordem.
"""

import pytest

from app.core.database import Database
from app.core.paths import SystemRoot


@pytest.fixture
def raiz(tmp_path, monkeypatch):
    monkeypatch.setenv("AUTOTABLOIDE_ROOT", str(tmp_path / "raiz"))
    return SystemRoot(tmp_path / "raiz")


def _fotos_de_bancada(tmp_path, cores):
    from app.tests import acervo
    saida = []
    for i, cor in enumerate(cores):
        f = tmp_path / f"sabor{i}.png"
        acervo.foto_de_bancada(f, cor)
        saida.append(str(f))
    return saida


def _esperar(cond, ms: int = 15000) -> bool:
    """Roda o laço de eventos até a condição. ACHADO da SEXTUSDECIMUS
    (a instrumentação que o §15.3 pediu): o laço apertado de drenar()
    ESFOMEIA o GIL — o worker rasteja e a espera estoura (o mecanismo
    do flake do test_a4). O sleep intercalado solta o GIL de verdade."""
    import time
    from app.tests.gestos import drenar
    fim = time.monotonic() + ms / 1000
    while time.monotonic() < fim:
        drenar(30)
        time.sleep(0.05)        # o GIL vai ao worker (sleep é C puro)
        if cond():
            return True
    return False


# ================================================================== M1+M4
# Cada sabor grava a SUA foto; o item leva a LISTA ao desenho
# ======================================================================


def test_m1_cada_sabor_grava_a_sua_foto(raiz, tmp_path):
    """A pergunta literal do dono ("como é que ele sabe qual sabor eu tô
    selecionando?") respondida: a lista é PARALELA aos sabores — os 3
    produtos nascem COM foto, e o item da estante leva as 3 ao leque."""
    from app.core.models import Produto
    from app.qt.telas import servico

    db = Database(raiz).init()
    db.engine.dispose()
    fotos = _fotos_de_bancada(tmp_path, [(220, 40, 40), (40, 220, 40),
                                         (40, 40, 220)])
    item = servico.ItemMesa("SARDINHA COQUEIRO 125 g TOMATE / OLEO e "
                            "LIMÃO", "6,90", "VERMELHO",
                            "Sardinha Coqueiro 125g")
    servico.criar_familia_de_sabores(
        item, "Sardinha Coqueiro 125g", ["Tomate", "Óleo", "Limão"],
        False, fotos)

    db = Database(raiz).init()
    try:
        with db.Session() as s:
            membros = [p for p in s.query(Produto).all()
                       if p.familia_id]
            assert len(membros) == 3
            sem_foto = [p.nome_sanitizado for p in membros
                        if not p.caminho_imagem]
            assert not sem_foto, (
                f"sabor(es) SEM foto — o N não fechou (L14): {sem_foto}")
    finally:
        db.engine.dispose()
    assert len(item.imagens) == 3, "o leque não recebeu as 3 (M4)"
    assert item.sabores == ["Tomate", "Óleo", "Limão"]
    # compat: o chamador antigo (str/None) continua valendo — 1º sabor
    item2 = servico.ItemMesa("X", "1,00", "VERMELHO", "X")
    servico.criar_familia_de_sabores(item2, "Suco Teste 1L",
                                     ["Uva", "Caju"], False, None)
    assert item2.semaforo == "VERDE"


# ================================================================== M3
# O sabor vai ao DESCRITOR — nunca some da página
# ======================================================================


def test_m3_o_sabor_vai_ao_descritor():
    """§2.2: nome = base da família; descritor = "Tomate, Óleo ou Limão"
    (+ a unidade pela régua de sempre). O cliente descobre o que há."""
    from app.qt.telas import servico

    assert servico.juntar_com_ou(["Tomate"]) == "Tomate"
    assert servico.juntar_com_ou(["Branco", "Oreo"]) == "Branco ou Oreo"
    assert servico.juntar_com_ou(["Tomate", "Óleo", "Limão"]) == \
        "Tomate, Óleo ou Limão"

    it = servico.ItemMesa("BIS LACTA XTRA 45 g BRANCO e OREO", "4,94",
                          "VERDE", "Bis Lacta Xtra 45g")
    it.sabores = ["Branco", "Oreo"]
    d = servico.dados_para_desenho(it)
    assert d.descritor and "Branco ou Oreo" in d.descritor
    # o round-trip do projeto congela os sabores (I1)
    volta = servico.ItemMesa.from_dict(it.to_dict())
    assert volta.sabores == ["Branco", "Oreo"]
    # sem sabores nada muda no caminho comum
    liso = servico.ItemMesa("ARROZ X 5 kg", "20,00", "VERDE", "Arroz X")
    liso.unidade = "5 kg"
    assert servico.dados_para_desenho(liso).descritor == "5 kg"


def test_m3_aplicar_sabores_leva_os_nomes():
    """O gesto pós-casamento (SaboresDialog) também anuncia: os membros
    escolhidos entram no descritor pelo nome do SABOR (sem o prefixo da
    família)."""
    from app.qt.telas import servico

    assert servico.sabor_do_membro("Sardinha Coqueiro 125g Tomate",
                                   "Sardinha Coqueiro 125g") == "Tomate"
    assert servico.sabor_do_membro("Nome Estranho", "Outra Base") == \
        "Nome Estranho"

    it = servico.ItemMesa("SARDINHA", "6,90", "VERDE", "Sardinha")
    it.familia = {"id": 1, "nome": "Sardinha Coqueiro 125g",
                  "membros": []}
    servico.aplicar_sabores(it, [
        {"produto_id": 2, "nome": "Sardinha Coqueiro 125g Óleo",
         "imagem": None},
        {"produto_id": 1, "nome": "Sardinha Coqueiro 125g Tomate",
         "imagem": None},
    ])
    assert it.sabores == ["Tomate", "Óleo"]     # ordem por produto_id


# ================================================================== M5
# O composto usa o mesmo caminho de N fotos
# ======================================================================


def test_m5_cadastrar_com_lista_cria_composto_com_2_fotos(raiz, tmp_path):
    """A queixa dele ("não deixa eu usar duas imagens diferentes"): a
    lista da tela nova atravessa o _cadastrar e cada componente nasce
    com a SUA foto."""
    from app.core.models import Produto
    from app.qt.telas import servico

    db = Database(raiz).init()
    db.engine.dispose()
    fotos = _fotos_de_bancada(tmp_path, [(200, 30, 30), (30, 30, 200)])
    item = servico.ItemMesa("ARROZ SOMAR e TIO BONINI 5 Kg", "18,81",
                            "VERMELHO", "Arroz Somar e Tio Bonini 5 Kg")
    comp = servico.criar_como_composto(
        item, ["Arroz Somar 5 kg", "Arroz Tio Bonini 5 kg"], False,
        fotos)
    db = Database(raiz).init()
    try:
        with db.Session() as s:
            sem = [p.nome_sanitizado for p in s.query(Produto).all()
                   if not p.caminho_imagem]
            assert not sem, f"componente SEM foto (L14): {sem}"
    finally:
        db.engine.dispose()
    assert len(comp.imagens) == 2, "a célula não recebeu as 2 fotos"


# ================================================================== M2
# A tela de um espaço por sabor (gesto)
# ======================================================================


def test_m2_tela_um_espaco_por_sabor(tmp_path):
    """Decisão 2 do dono: um espaço por sabor, busca semeada
    "{base} {sabor}", quadradinho próprio. Tratador injetado — a
    bancada roda sem web e sem rembg."""
    from PySide6.QtWidgets import QApplication, QPushButton
    QApplication.instance() or QApplication([])
    from app.qt.telas.fotos_por_sabor_dialog import FotosPorSaborDialog
    from app.tests import acervo

    foto = tmp_path / "f.png"
    acervo.foto_de_bancada(foto, (10, 200, 10))

    dlg = FotosPorSaborDialog("Bis Lacta Xtra 45g", ["Branco", "Oreo"],
                              tratador=lambda f: f)
    try:
        # a busca de CADA espaço nasce semeada com o nome certo
        dicas = [b.toolTip() for b in dlg.findChildren(QPushButton)
                 if "Buscar" in b.text()]
        assert any("Bis Lacta Xtra 45g Branco" in d for d in dicas)
        assert any("Bis Lacta Xtra 45g Oreo" in d for d in dicas)
        assert dlg.fotos() == [None, None]
        dlg._tratar(1, str(foto))            # o gesto do 2º espaço
        assert _esperar(lambda: dlg.fotos()[1] == str(foto)), \
            "a foto não chegou ao espaço 2"
        assert dlg.fotos() == [None, str(foto)]
        assert "1 de 2" in dlg._resumo.text()
    finally:
        dlg.done(0)


def test_m2_linha_multi_abre_a_tela_e_leva_a_lista(raiz, tmp_path,
                                                   monkeypatch):
    """A costura: curadoria com "são sabores" aceito → a tela de N
    espaços abre e a LISTA dela chega aos criadores (a proposta inteira
    atravessa, nada da metade)."""
    from PySide6.QtWidgets import QApplication
    QApplication.instance() or QApplication([])
    from app.core.models import Produto
    from app.qt.telas import conciliacao_dialog as cd
    from app.qt.telas import fotos_por_sabor_dialog as fps
    from app.qt.telas import servico
    from app.tests.gestos import drenar

    db = Database(raiz).init()
    db.engine.dispose()
    fotos = _fotos_de_bancada(tmp_path, [(250, 100, 0), (0, 100, 250)])
    # o teste é da COSTURA (tela → lista → criadores), não do LM nem da
    # web — sem motor e sem busca o gesto anda no ritmo da bancada (a
    # fila serial de workers ficava atrás do ddgs real); o estado
    # com-IA é a prova §6 na máquina real
    monkeypatch.setattr(servico, "_motor_se_disponivel", lambda: None)
    monkeypatch.setattr(servico, "buscar_candidatos",
                        lambda *a, **k: [])
    monkeypatch.setattr(servico, "buscar_candidatos_para",
                        lambda *a, **k: [])

    # a tela nova "aceita" com as 2 fotos, sem abrir de verdade
    monkeypatch.setattr(fps.FotosPorSaborDialog, "exec",
                        lambda self: 1)
    monkeypatch.setattr(fps.FotosPorSaborDialog, "fotos",
                        lambda self: list(fotos))
    # a curadoria "responde" são-sabores, sem abrir de verdade
    from app.qt.telas.curadoria_dialog import CuradoriaDialog
    monkeypatch.setattr(CuradoriaDialog, "exec", lambda self: 1)
    monkeypatch.setattr(CuradoriaDialog, "sabores_finais",
                        lambda self: ("Bis Lacta Xtra 45g",
                                      ["Branco", "Oreo"]))
    monkeypatch.setattr(CuradoriaDialog, "componentes_finais",
                        lambda self: [])
    monkeypatch.setattr(CuradoriaDialog, "mais18_final",
                        lambda self: False)
    monkeypatch.setattr(CuradoriaDialog, "nome_final",
                        lambda self: "Bis Lacta Xtra 45g")

    item = servico.ItemMesa("BIS EXTRA 45 g BRANCO e OREO", "4,94",
                            "VERMELHO", "Bis Extra 45g Branco e Oreo")
    dlg = cd.ConciliacaoDialog(servico.ResultadoMesa(itens=[item]), None)
    from PySide6.QtCore import Qt
    dlg.setAttribute(Qt.WidgetAttribute.WA_DontShowOnScreen, True)
    dlg.show()
    drenar()
    # a fila de fotos (web real) na frente do worker atrasa o gesto —
    # modo rápido, o padrão do diaadia
    from app.tests.gestos import clicar
    if dlg.chk_fotos.isChecked():
        clicar(dlg.chk_fotos)
        drenar()
    try:
        prop = servico.PropostaCriacao(nome="Bis Lacta Xtra 45g",
                                       mais18=False, categoria=None)
        dlg._curadoria(0, prop)
        assert _esperar(lambda: dlg.itens[0].semaforo == "VERDE"), \
            f"não cadastrou ({dlg.itens[0].semaforo})"
        assert len(dlg.itens[0].imagens) == 2, \
            "a lista da tela não chegou ao leque"
    finally:
        dlg.done(0)
    db = Database(raiz).init()
    try:
        with db.Session() as s:
            com_foto = [p for p in s.query(Produto).all()
                        if p.caminho_imagem and p.familia_id]
            assert len(com_foto) == 2, "os 2 sabores COM foto no banco"
    finally:
        db.engine.dispose()


# ================================================================== M6+M8
# "Salvar" grava POR CIMA; o versionamento sai do coma; o rascunho morre
# ======================================================================


def test_m6_m8_salvar_por_cima_versiona_e_mata_o_rascunho(raiz, tmp_path):
    """O estrago que o arquiteto mediu na tela ("duas edições do 03/08"):
    projeto aberto + Salvar criava SEMPRE um clone. Agora: a MESMA linha
    regrava, a versão anterior aparece em "Versões…" (o menu deixa de
    ser código morto) e o rascunho é descartado (M8)."""
    from PySide6.QtWidgets import QApplication
    QApplication.instance() or QApplication([])
    from app.core import projetos, rascunho
    from app.tests.test_bloco_d_f13 import (
        _ia_desligada, _mesa_com_item, _vigia_salvar_projeto,
    )
    from app.tests.gestos import drenar

    _ia_desligada()
    m = _mesa_com_item(tmp_path)
    try:
        with _vigia_salvar_projeto(nome="Segunda dos Frios 03/08"):
            m._salvar_projeto()
            drenar()
        pid = m._projeto_id
        assert pid is not None and m._projeto_nome == \
            "Segunda dos Frios 03/08"

        # rascunho vivo antes do 2º salvar (M8: salvar por cima limpa)
        rascunho.salvar_rascunho({"itens": [], "projeto_id": pid})
        # edita algo e SALVA de novo — o vigia responde só o PRÉ-VOO;
        # se o diálogo de NOME abrir, é a regressão e o teste acusa
        m._itens[0].preco = "9,99"
        from PySide6.QtCore import QTimer
        from PySide6.QtWidgets import QAbstractButton, QApplication
        from app.tests.gestos import clicar
        flags = {"abriu_nome": False}

        def _tic():
            dlg = QApplication.instance().activeModalWidget()
            if dlg is None or not dlg.isVisible():
                return
            if getattr(dlg, "nome", None) is not None:
                flags["abriu_nome"] = True     # regressão M6!
                dlg.reject()
                return
            b = [x for x in dlg.findChildren(QAbstractButton)
                 if x.text().strip() == "Salvar mesmo assim"]
            if len(b) == 1:
                clicar(b[0])

        timer = QTimer()
        timer.setInterval(15)
        timer.timeout.connect(_tic)
        timer.start()
        try:
            m._salvar_projeto()
            drenar()
        finally:
            timer.stop()
        assert not flags["abriu_nome"], (
            "salvar por cima reabriu o diálogo de nome (M6)")

        assert m._projeto_id == pid, "salvar por cima trocou de id (M6)"
        nomes = [p["nome"] for p in projetos.listar_projetos()]
        assert nomes.count("Segunda dos Frios 03/08") == 1, (
            f"nasceu clone: {nomes}")
        versoes = projetos.listar_versoes(pid)
        assert len(versoes) >= 1, (
            "o versionamento continua em coma — salvar por cima não "
            "gravou a versão anterior")
        assert rascunho.carregar_rascunho() is None, (
            "o rascunho sobreviveu ao salvar (M8)")
    finally:
        m.close()
        drenar()


def test_m6_fabrica_tambem_grava_por_cima(raiz, monkeypatch):
    """O segundo chamador (fabrica.py) tinha a mesma doença — espião no
    núcleo prova que o projeto_id viaja."""
    from PySide6.QtWidgets import QApplication
    QApplication.instance() or QApplication([])
    from PySide6.QtCore import Qt
    from app.core import projetos
    from app.qt.telas import servico
    from app.qt.telas.fabrica import FabricaTela

    capturado = {}

    def _espiao(*a, **k):
        capturado.update(k)
        return 77

    monkeypatch.setattr(projetos, "salvar_projeto", _espiao)
    import app.qt.telas.prevoo as prevoo
    monkeypatch.setattr(prevoo, "confirmar_pre_voo",
                        lambda *a, **k: True)

    f = FabricaTela()
    f.setAttribute(Qt.WidgetAttribute.WA_DontShowOnScreen, True)
    try:
        f._itens = [servico.ItemMesa("X", "1,00", "VERDE", "Produto X")]
        f._projeto_id = 42
        f._projeto_nome = "Cartazes da Semana"
        f._salvar_projeto()          # sem diálogo: regrava direto
        assert capturado.get("projeto_id") == 42, (
            f"o projeto_id não viajou ao núcleo: {capturado}")
    finally:
        f.close()


# ================================================================== M7
# A grade do drill-down recarrega no duplicar
# ======================================================================


def test_m7_grade_do_evento_recarrega(raiz):
    """Reproduzido pelo arquiteto: duplicou, a grade ficou com 3, saiu e
    voltou, virou 4. Agora o recarregar REFAZ a visão aberta."""
    from PySide6.QtWidgets import QApplication, QListWidget
    QApplication.instance() or QApplication([])
    from PySide6.QtCore import Qt
    from app.core import projetos
    from app.qt.telas import servico
    from app.qt.telas.dashboard import DashboardTela
    from app.rendering.model import (
        LayoutDef, Pagina, Regiao, Retangulo, Slot, TipoRegiao,
    )

    lay = LayoutDef(100, 100, dpi=100, paginas=[Pagina([
        Slot("s", [Regiao(TipoRegiao.NOME, Retangulo(10, 10, 30, 10))])])])

    def _salvar(nome):
        it = servico.ItemMesa("X", "1,00", "VERDE", "Produto X")
        return projetos.salvar_projeto(nome, "Segunda dos Frios",
                                       "TABLOIDE", lay, [it.to_dict()])

    _salvar("Segunda 27/07")
    dash = DashboardTela()
    dash.setAttribute(Qt.WidgetAttribute.WA_DontShowOnScreen, True)
    try:
        dash._recarregar_agora()
        dash._abrir_evento_por_nome("Segunda dos Frios")
        assert dash._pilha.currentIndex() == 1

        def _na_grade():
            # só a lista DENTRO do layout vivo (a velha, tirada dele,
            # espera o deleteLater e ainda é filha por um instante)
            total = 0
            for i in range(dash._visao_lay.count()):
                w = dash._visao_lay.itemAt(i).widget()
                if isinstance(w, QListWidget):
                    total += w.count()
            return total

        antes = _na_grade()
        assert antes == 1
        # o gesto do dono: duplicar (aqui pelo núcleo — o menu chama
        # recarregar(), que é o que provamos)
        _salvar("Segunda 03/08")
        dash._recarregar_agora()
        assert dash._pilha.currentIndex() == 1, (
            "o recarregar roubou a tela do evento")
        assert _na_grade() == 2, (
            "a grade do drill-down ficou VELHA — o duplicado só "
            "aparece saindo e voltando (M7)")
    finally:
        dash.close()


# ================================================================== M11
# Fusão automática: quem tem foto vence, com relatório
# ======================================================================


def test_m11_fusao_automatica_mantem_a_que_tem_foto(raiz):
    """Decisão 3 do dono: fundir automático pelas iguais, mantendo a que
    tem foto, com relatório e reversível (lixeira)."""
    from app.core.deduplicacao import fundir_duplicatas_automatico
    from app.core.models import Produto
    from app.core.repositories import ProdutoRepositorio

    db = Database(raiz).init()
    try:
        with db.Session() as s:
            repo = ProdutoRepositorio(s)
            a = repo.importar("Arroz Camil 5 kg").produto   # sem foto
            b = repo.importar("ARROZ CAMIL 5 KG").produto   # mesmo nome
            b.caminho_imagem = f"{b.id}/atual.png"          # COM foto
            c = repo.importar("Feijão Preto 1 kg").produto  # outro
            s.commit()
            ids = (a.id, b.id, c.id)

            rel = fundir_duplicatas_automatico(s)
            s.commit()
            assert rel["total"] == 1, f"relatório: {rel}"
            log = rel["fundidos"][0]
            assert log["vencedor"] == ids[1], (
                "quem TEM FOTO tinha de vencer (decisão 3)")
            assert log["perdedor"] == ids[0]
            assert log["nome_vencedor"]                     # o relatório fala
            perdedor = s.get(Produto, ids[0])
            assert perdedor.excluido_em is not None, "não foi à lixeira"
            assert s.get(Produto, ids[2]).excluido_em is None
    finally:
        db.engine.dispose()


# ================================================================== M9+M10
# Eventos semanais: o cartão enxerga o dia do NOME; duplicar sugere data
# ======================================================================


def test_m9_proximo_evento_soma_o_dia_do_nome(raiz):
    """Medido pelo arquiteto: "Próximo evento: —" com a Segunda amanhã.
    O evento nascido do texto não tem dia gravado — o dia lido do NOME
    soma (L12) e o cartão fala."""
    from PySide6.QtWidgets import QApplication
    QApplication.instance() or QApplication([])
    from PySide6.QtCore import Qt
    from app.core.database import Database as _Db
    from app.qt.telas import eventos as ev
    from app.qt.telas.dashboard import DashboardTela

    db = _Db(raiz).init()
    try:
        with db.Session() as s:
            ev.criar_evento(s, "Segunda dos Frios")   # SEM dia_semana
            s.commit()
    finally:
        db.engine.dispose()

    dash = DashboardTela()
    dash.setAttribute(Qt.WidgetAttribute.WA_DontShowOnScreen, True)
    try:
        visto = {}
        dash._cartoes_numero["evento"].set_valor = \
            lambda v: visto.setdefault("v", v)
        dash._visao_geral_chegou({})
        assert "Segunda dos Frios" in visto.get("v", ""), (
            f"o cartão continua mudo: {visto}")
    finally:
        dash.close()


def test_m10_nome_da_proxima_edicao():
    """"Segunda dos Frios 27/07" duplicada num domingo sugere
    "Segunda dos Frios 03/08" — e duplicada NA própria segunda pula à
    semana seguinte. Sem dia conhecido, o "(nova)" de sempre."""
    from datetime import date
    from app.qt.telas.eventos import nome_da_proxima_edicao

    dom = date(2026, 8, 2)                      # domingo
    assert nome_da_proxima_edicao("Segunda dos Frios 27/07", 0, dom) == \
        "Segunda dos Frios 03/08"
    # na própria segunda 03/08, o nome já diz 03/08 → semana seguinte
    seg = date(2026, 8, 3)
    assert nome_da_proxima_edicao("Segunda dos Frios 03/08", 0, seg) == \
        "Segunda dos Frios 10/08"
    # sem data no nome: anexa
    assert nome_da_proxima_edicao("Segunda dos Frios", 0, dom) == \
        "Segunda dos Frios 03/08"
    # com ano escrito, substitui o bloco inteiro
    assert nome_da_proxima_edicao("Quintou 23/07/2026", 3, dom) == \
        "Quintou 06/08"
    # sem dia conhecido: o comportamento antigo
    assert nome_da_proxima_edicao("Avulso Julho", None, dom) == \
        "Avulso Julho (nova)"

"""BLOCO D da ORDEM_F13 — o dia de 5 minutos, cada item com o vermelho antes (L1).

Cada teste deste arquivo nasceu VERMELHO no código de antes do conserto
correspondente (a rodada vermelha registrada na resposta do builder, no fim
da ordem). Tudo por gesto (L2) ou conteúdo (L3), sobre app/tests/gestos.py.
"""

from contextlib import contextmanager

import pytest
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication

from app.rendering.model import (
    LayoutDef,
    Pagina,
    Regiao,
    Retangulo,
    Slot,
    TipoRegiao,
)
from app.tests import acervo
from app.tests.gestos import (
    botao_por_texto,
    clicar,
    clicar_na_cena,
    drenar,
    vigia_dialogo,
)


def _app():
    return QApplication.instance() or QApplication([])


@pytest.fixture()
def raiz_tmp(tmp_path, monkeypatch):
    monkeypatch.setenv("AUTOTABLOIDE_ROOT", str(tmp_path / "raiz"))
    from app.core.database import Database
    from app.core.paths import SystemRoot
    root = SystemRoot(tmp_path / "raiz").criar_estrutura()
    acervo.copiar_fontes_reais(root.fontes)
    Database(root).init().engine.dispose()
    return root


def _png(caminho, cor=(200, 40, 40)):
    """Foto de bancada NÍTIDA (xadrez 600px): cor chapada tem Laplaciano
    zero e o avaliador (D10, certo!) a marcaria como 'borrada — RUIM'."""
    from PIL import Image
    img = Image.new("RGB", (600, 600), cor)
    branco = Image.new("RGB", (16, 16), (255, 255, 255))
    for x in range(0, 600, 32):
        for y in range(0, 600, 32):
            img.paste(branco, (x, y))
    img.save(caminho)
    return str(caminho)


def _ia_desligada():
    """O interruptor MESTRE (passo 46): disponivel() vira False SEM tocar a
    rede. Sem isto a bancada fala com o LM Studio REAL da máquina (a fila
    de enriquecer do diálogo dispara sozinha ao abrir) e o teste vira
    loteria — achado desta bancada, ver a resposta do builder."""
    from app.core.database import Database
    from app.core.repositories import ConfigRepositorio
    db = Database().init()
    with db.Session() as s:
        ConfigRepositorio(s).set("ia.usar", False)
        s.commit()
    db.engine.dispose()


def _esperar(cond, ms=25000, passo=50):
    """Espera GENEROSA: as filas do diálogo abrem Database().init() POR
    chamada e inits concorrentes no mesmo SQLite pagam ~5s cada por
    contenção (medido nesta bancada — anotado na resposta do builder)."""
    from PySide6.QtTest import QTest
    for _ in range(max(1, ms // passo)):
        if cond():
            return True
        QTest.qWait(passo)
    return cond()


def _mesa_com_item(tmp_path):
    """Mesa REAL com 1 item completo (nome+preço+foto) numa grade de 1
    célula — o mínimo que salva sem NENHUMA pendência de pré-voo."""
    from app.qt.telas import servico
    from app.qt.telas.mesa import MesaTela
    m = MesaTela()
    m.setAttribute(Qt.WidgetAttribute.WA_DontShowOnScreen, True)
    it = servico.ItemMesa("Arroz Tio João 5kg", "24,90", "VERDE",
                          "Arroz Tio João 5kg")
    it.imagem = _png(tmp_path / "arroz.png")
    m._itens = [it]
    lay = LayoutDef(100, 100, dpi=100, paginas=[Pagina([Slot("c", [
        Regiao(TipoRegiao.IMAGEM, Retangulo(10, 10, 40, 20), nome="Foto"),
        Regiao(TipoRegiao.NOME, Retangulo(10, 32, 80, 12), nome="Nome"),
        Regiao(TipoRegiao.PRECO, Retangulo(10, 46, 40, 10), nome="Preço"),
    ])])])
    m._layout = lay
    m.area.carregar(lay, {})
    m._mapa = {"c": it.uid}
    m._recarregar_lista()
    return m


@contextmanager
def _vigia_salvar_projeto(nome="Oferta da semana", evento=None):
    """Responde o SalvarProjetoDialog REAL: digita nome (e evento) pelo
    TECLADO e clica ' Salvar' — o molde do vigia_dialogo (nada de
    monkeypatch). Nunca asserta dentro do timer (lição do Bloco B)."""
    from PySide6.QtCore import QTimer
    from PySide6.QtTest import QTest
    app = _app()
    estado = {"disparou": False, "vistos": set()}
    timer = QTimer()
    timer.setInterval(15)

    def _tic():
        dlg = app.activeModalWidget()
        if dlg is None or not dlg.isVisible():
            return
        campo = getattr(dlg, "nome", None)
        if campo is None:
            # pode ser o PRÉ-VOO do salvar (avisos legítimos do D10) —
            # segue "mesmo assim"; qualquer outro modal é ignorado
            if estado["disparou"]:
                from PySide6.QtWidgets import QAbstractButton
                b = [x for x in dlg.findChildren(QAbstractButton)
                     if x.text().strip() == "Salvar mesmo assim"]
                if len(b) == 1 and id(dlg) not in estado["vistos"]:
                    estado["vistos"].add(id(dlg))
                    clicar(b[0])
            return
        if id(dlg) in estado["vistos"]:
            return
        estado["vistos"].add(id(dlg))
        campo.setFocus()
        QTest.keyClicks(campo, nome)
        if evento:
            ev = dlg.evento.lineEdit()
            ev.setFocus()
            QTest.keyClicks(ev, evento)
        clicar(botao_por_texto(dlg, "Salvar"))
        estado["disparou"] = True

    timer.timeout.connect(_tic)
    timer.start()
    try:
        yield estado
    finally:
        timer.stop()


# ---------------------------------------------------------------------------
# D14 · P-10 — o rascunho automático não ressuscita projeto PRONTO
# ---------------------------------------------------------------------------


def test_d14_projeto_salvo_nao_regrava_rascunho(raiz_tmp, tmp_path):
    """D14 (P-10): salvar o projeto descarta o rascunho (R-061) — mas o
    timer de 2 min continua vivo e o tick seguinte REGRAVA o mesmo estado
    já salvo (nada olha a dirty flag). Na abertura seguinte o app oferece
    'recuperar' um trabalho que está salvo e diz que foi 'fechado sem
    salvar'. O tick com o projeto LIMPO não pode gravar nada."""
    from app.core import rascunho
    _app()
    m = _mesa_com_item(tmp_path)
    m.show()
    try:
        with _vigia_salvar_projeto() as v:
            m._salvar_projeto()
        assert v["disparou"], "o diálogo de salvar nem abriu"
        assert m._salvo, "o salvar não marcou o projeto como salvo"
        assert not rascunho.ha_rascunho(), "o salvar não descartou o rascunho"

        # o tick REAL do timer (o sinal que dispara a cada 2 min)
        m._timer_rascunho.timeout.emit()
        m._trabalhos.encerrar(espera_ms=4000)    # junta o worker, se nasceu
        drenar()
        assert not rascunho.ha_rascunho(), (
            "o tick do timer REGRAVOU o rascunho de um projeto SALVO — a "
            "próxima abertura vai oferecer 'recuperar' trabalho pronto "
            "(P-10)")
    finally:
        m.close()


def test_d14_edicao_depois_do_salvar_volta_a_ter_rede(raiz_tmp, tmp_path):
    """O anti-exagero do D14 (prova de mutação da guarda): editar DEPOIS de
    salvar suja o projeto de novo — o tick seguinte TEM de gravar o
    rascunho (a rede de queda continua existindo para trabalho não
    salvo)."""
    from app.core import rascunho
    _app()
    m = _mesa_com_item(tmp_path)
    m.show()
    try:
        with _vigia_salvar_projeto() as v:
            m._salvar_projeto()
        assert v["disparou"]
        assert not rascunho.ha_rascunho()

        # o gesto da estante que suja o projeto (os 2 diálogos reais)
        with vigia_dialogo("OK", vezes=2) as ve:
            m._editar_item(m.lista.item(0))
        assert ve.disparos == 2, "os diálogos de edição nem abriram"
        assert not m._salvo, "a edição não sujou o projeto"

        m._timer_rascunho.timeout.emit()
        m._trabalhos.encerrar(espera_ms=4000)
        drenar()
        assert rascunho.ha_rascunho(), (
            "com o projeto SUJO o tick não gravou rascunho — a guarda do "
            "D14 exagerou e matou a rede de queda")
    finally:
        m.close()


# ---------------------------------------------------------------------------
# D1 · I-01/VC-020 — o véu do rembg vira RODAPÉ (a tela fica livre)
# ---------------------------------------------------------------------------


def test_d1_veu_virou_rodape_tela_livre_durante_o_trabalho(raiz_tmp):
    """D1 (I-01, VC-020 passo 1): o rembg já roda em thread — era o OVERLAY
    que sequestrava a tela: cobria o alvo inteiro e comia todo clique (e
    só o mouse; o teclado atravessava — a assimetria CF-05). Agora o véu
    é uma FAIXA DE RODAPÉ: narra o trabalho (spinner + decorrido) e o
    miolo da tela continua LIVRE. Prova por hit-test REAL (childAt) +
    clique real no botão resolvido."""
    from PySide6.QtWidgets import QPushButton, QWidget
    from app.qt.design.carregando import OverlayOcupado
    _app()
    tela = QWidget()
    tela.setAttribute(Qt.WidgetAttribute.WA_DontShowOnScreen, True)
    tela.resize(600, 400)
    botao = QPushButton("Continuar trabalhando", tela)
    botao.setGeometry(220, 150, 180, 40)          # o miolo da tela
    cliques = []
    botao.clicked.connect(lambda: cliques.append(1))
    tela.show()
    ov = OverlayOcupado(tela)
    ov.mostrar("Removendo o fundo…")
    drenar()
    assert ov.isVisible()

    # 1) quem está sob o ponto do botão? (hit-test de verdade — hoje o véu
    #    cobre a tela inteira e é ELE quem recebe o mouse ali)
    sob = tela.childAt(botao.geometry().center())
    assert sob is botao, (
        f"o miolo da tela está coberto por {sob!r} durante o trabalho — o "
        "dono fica refém dos 8-26s do rembg (I-01/D1)")
    clicar(botao)
    assert cliques, "o clique real não chegou ao botão"

    # 2) é um RODAPÉ de verdade: gruda no pé do alvo e é BAIXO
    assert ov.geometry().bottom() >= tela.rect().bottom() - 2, (
        "a faixa não está no pé da tela")
    assert ov.height() <= tela.height() // 3, "a 'faixa' ainda é um véu"

    # 3) acompanha o redimensionar do alvo (continua grudada no pé)
    tela.resize(700, 500)
    drenar()
    assert ov.geometry().bottom() >= tela.rect().bottom() - 2
    assert ov.width() == tela.width()

    # 4) e continua narrando
    assert "Removendo o fundo" in ov._rotulo.text()
    ov.esconder()
    assert not ov.isVisible()


# ---------------------------------------------------------------------------
# D2 · X-01/CD-04 — a digitação coalesce (um gesto = um estado)
# ---------------------------------------------------------------------------


def test_d2_digitacao_coalesce_um_estado_e_um_desfazer(raiz_tmp):
    """D2 (X-01 + CD-04): cada tecla no painel custava um compor_pagina
    INTEIRO (~113ms medidos) e um estado de desfazer — apagar um nome
    digitado eram 9 Ctrl+Z (a gravação do dono). A rajada agora coalesce:
    o modelo reflete NA HORA, mas histórico/recomposição fecham no fim do
    gesto — UM desfazer devolve o nome inteiro."""
    from PySide6.QtTest import QTest
    from app.qt.editor import Editor
    from app.rendering.compositor import DadosProduto
    _app()
    e = Editor()
    lay = LayoutDef(100, 100, dpi=100, paginas=[Pagina([Slot("s", [
        Regiao(TipoRegiao.NOME, Retangulo(10, 10, 60, 14), nome="Nome"),
    ])])])
    e.carregar(lay, DadosProduto("x"))
    c = e.canvas
    reg = lay.paginas[0].slots[0].regioes[0]
    item = next(i for i in c._itens if i.regiao is reg)
    from app.tests.gestos import clicar_na_cena
    clicar_na_cena(c, item.mapToScene(item._w / 2, item._h / 2))
    assert c.selecionada() is reg

    campo = e.propriedades.nome
    assert campo.isEnabled()
    campo.setFocus()
    QTest.keyClicks(campo, " Zero")          # 5 teclas REAIS
    assert reg.nome == "Nome Zero", "o modelo não refletiu a digitação"
    drenar(600)                              # o gesto fecha (coalescência)

    from app.tests.gestos import botao_por_tooltip
    clicar(botao_por_tooltip(e.barra, "Desfazer"))
    # o undo RECONSTRÓI o layout do snapshot — repescar a região (a lição
    # do wrapper morto do C, agora no modelo)
    reg2 = c._layout.paginas[0].slots[0].regioes[0]
    assert reg2.nome == "Nome", (
        f"UM desfazer devolveu {reg2.nome!r} — a rajada virou um estado "
        "POR TECLA (CD-04/X-01): apagar um nome digitado é um Ctrl+Z por "
        "letra")


def test_d2_previa_rapida_mantem_cena_e_tamanho(raiz_tmp):
    """Guarda do D2 (prévia em 96 dpi): a composição do preview desce a 96
    dpi, mas o pixmap volta ESTICADO ao tamanho da cena — alças, réguas,
    guias e snap continuam em pixels do dpi do LAYOUT (a armadilha
    apontada pelo scout: sem o re-escalonamento tudo desloca por 3,125×).
    O ganho de tempo entra MEDIDO no quadro do fecho do bloco."""
    from app.qt.canvas import CanvasView
    from app.rendering.compositor import DadosProduto, mm_para_px
    _app()
    lay = LayoutDef(100, 80, dpi=300, paginas=[Pagina([Slot("s", [
        Regiao(TipoRegiao.NOME, Retangulo(10, 10, 60, 14), nome="Nome"),
    ])])])
    c = CanvasView()
    c.resize(400, 300)
    c.carregar(lay, DadosProduto("x"))
    pm = c._bg.pixmap()
    assert pm.width() == round(mm_para_px(100, 300)), (
        "o pixmap do preview não está no tamanho da CENA (dpi do layout) "
        "— alças/réguas/snap deslocam")
    assert pm.height() == round(mm_para_px(80, 300))


# ---------------------------------------------------------------------------
# D6 · C-08/C-09 — a sanitização para de apagar palavra; o aviso chega
# ---------------------------------------------------------------------------


def test_d6_typo_da_ia_devolve_a_palavra_do_dono():
    """D6 raiz (C-08): a IA troca HUPPERS por Ruppers (typo agressivo); a
    guarda #78/#95 via 'Ruppers' como INVENTADO e o removia — a marca
    sumia INTEIRA do nome e a única testemunha era tokens_perdidos, que
    só a curadoria mostra. Substituição agora DEVOLVE a palavra do bruto
    no lugar (com a caixa da convenção); acréscimo puro (INMETRO, NBR)
    continua caindo fora."""
    import json
    from app.ai.enriquecimento import enriquecer, remover_inventados
    from app.ai.fake import MotorIAFake

    fake = MotorIAFake(respostas_chat={"supermercado": json.dumps(
        {"nome_sanitizado": "Salgadinho Ruppers Galinha 50g",
         "confianca": 0.9})})
    enr = enriquecer("SALG. HUPPERS GALINHA 50 G", fake)
    assert "Huppers" in enr.nome_sanitizado, (
        "a marca do dono SUMIU do nome — a guarda removeu o substituto em "
        "vez de devolver a palavra original (C-08/D6): "
        f"{enr.nome_sanitizado!r}")
    assert "Ruppers" not in enr.nome_sanitizado, (
        "o typo da IA ficou no nome — trocar marca sozinho é proibido (F9)")
    assert enr.tokens_perdidos == [], (
        "com a palavra devolvida não há perda a acusar")

    # o acréscimo puro continua morrendo (o contrato antigo, intacto)
    assert remover_inventados("Arroz INMETRO 5kg", "ARROZ 5 KG") == \
        "Arroz 5kg"


def test_d6_modo_rapido_avisa_perda_antes_de_cadastrar(raiz_tmp):
    """D6 furo A (C-09): no modo rápido (fotos desligadas) a proposta com
    tokens_perdidos era cadastrada DIRETO — o único caminho que avisa (a
    curadoria) era pulado e o toast verde dizia 'pronto' sobre um nome
    mutilado. Agora a perda abre a curadoria (aviso nominal + nome
    editável) mesmo sem fotos."""
    from app.qt.telas import servico
    from app.qt.telas.conciliacao_dialog import ConciliacaoDialog
    _app()
    _ia_desligada()
    it = servico.ItemMesa("SALG. HUPPERS GALINHA 50 G", "3,99", "VERMELHO",
                          "SALG. HUPPERS GALINHA 50 G")
    dlg = ConciliacaoDialog(servico.ResultadoMesa(itens=[it]), None)
    dlg.setAttribute(Qt.WidgetAttribute.WA_DontShowOnScreen, True)
    dlg.show()
    drenar()
    try:
        if dlg.chk_fotos.isChecked():
            clicar(dlg.chk_fotos)              # modo rápido, pelo gesto
        assert not dlg.chk_fotos.isChecked()
        # a fila RG-02a resolve o item (degradada, IA off) — SÓ ENTÃO a
        # proposta com perda entra, senão a fila a sobrescreveria (corrida)
        assert _esperar(lambda: it.uid in dlg._propostas), (
            "a fila de enriquecer nem resolveu o item")
        dlg._propostas[it.uid] = servico.PropostaCriacao(
            nome="Salgadinho Galinha 50g", mais18=False, categoria=None,
            tokens_perdidos=["HUPPERS"])

        with vigia_dialogo(tecla=Qt.Key.Key_Escape) as v:
            dlg._criar(0)
            drenar()
        assert v.disparou, (
            "NENHUM aviso abriu — o nome mutilado foi cadastrado em "
            "silêncio no modo rápido (C-09/D6)")
        assert dlg.itens[0].semaforo == "VERMELHO", (
            "o Esc na revisão ainda assim cadastrou o item")
    finally:
        dlg.done(0)
        drenar()


def test_d6_lote_nao_cadastra_nome_com_perda(raiz_tmp):
    """D6 furo B (C-09): o 'Criar todos sem foto' jogava a proposta com
    perda direto no finalizar_criacao — o campo tokens_perdidos viajava
    até a chamada e era DESCARTADO. A política do enriquecer_banco
    (RG-20: perdeu palavra ⇒ não aplica) vale no lote: o item FICA
    vermelho, nomeado para revisão, e NENHUM produto mutilado entra no
    banco (prova por conteúdo)."""
    from app.qt.telas import servico
    from app.qt.telas.conciliacao_dialog import ConciliacaoDialog
    _app()
    _ia_desligada()
    it = servico.ItemMesa("SALG. HUPPERS GALINHA 50 G", "3,99", "VERMELHO",
                          "SALG. HUPPERS GALINHA 50 G")
    dlg = ConciliacaoDialog(servico.ResultadoMesa(itens=[it]), None)
    dlg.setAttribute(Qt.WidgetAttribute.WA_DontShowOnScreen, True)
    dlg.show()
    drenar()
    try:
        if dlg.chk_fotos.isChecked():
            clicar(dlg.chk_fotos)
        assert _esperar(lambda: it.uid in dlg._propostas), (
            "a fila de enriquecer nem resolveu o item")
        dlg._propostas[it.uid] = servico.PropostaCriacao(
            nome="Salgadinho Galinha 50g", mais18=False, categoria=None,
            tokens_perdidos=["HUPPERS"])
        assert dlg.btn_todos.isVisible()
        clicar(dlg.btn_todos)
        assert _esperar(lambda: dlg.btn_todos.isEnabled()), (
            "a fila do lote nem terminou — bancada furada, não prova nada")
        drenar()
        assert dlg.itens[0].semaforo == "VERMELHO", (
            "o lote CADASTROU o nome mutilado em silêncio (C-09/D6)")
        from app.core.database import Database
        from app.core.repositories import ProdutoRepositorio
        db = Database().init()
        with db.Session() as s:
            nomes = [p.nome_sanitizado
                     for p in ProdutoRepositorio(s).listar(limit=10)]
        db.engine.dispose()
        assert "Salgadinho Galinha 50g" not in nomes, (
            "o produto MUTILADO entrou no banco (a marca sumiu) — C-09/D6")
        assert it.descricao in dlg._para_revisar, (
            "quem ficou de fora não foi NOMEADO para revisão (I2)")
    finally:
        dlg.done(0)
        drenar()


@contextmanager
def _vigia_sequencia(textos, timeout_ms=8000):
    """Responde uma SEQUÊNCIA de diálogos modais, cada um pelo clique no
    botão do texto correspondente (fluxos com 2+ modais de textos
    DIFERENTES — dois vigias simultâneos brigariam pelo 1º diálogo).
    Nunca asserta dentro do timer (lição do B): flags para depois."""
    from PySide6.QtCore import QTimer
    app = _app()
    estado = {"respondidos": [], "faltou": None, "vistos": set()}
    fila = list(textos)
    timer = QTimer()
    timer.setInterval(15)

    def _tic():
        if not fila:
            timer.stop()
            return
        dlg = app.activeModalWidget()
        if dlg is None or not dlg.isVisible() or id(dlg) in estado["vistos"]:
            return
        from PySide6.QtWidgets import QAbstractButton
        alvo = fila[0]
        botoes = [b for b in dlg.findChildren(QAbstractButton)
                  if b.text().strip() == alvo]
        if len(botoes) != 1:
            estado["faltou"] = (alvo, [b.text() for b in
                                       dlg.findChildren(QAbstractButton)])
            estado["vistos"].add(id(dlg))
            timer.stop()
            dlg.reject() if hasattr(dlg, "reject") else dlg.close()
            return
        estado["vistos"].add(id(dlg))
        fila.pop(0)
        clicar(botoes[0])
        estado["respondidos"].append(alvo)

    timer.timeout.connect(_tic)
    timer.start()
    try:
        yield estado
    finally:
        timer.stop()


# ---------------------------------------------------------------------------
# D4+D5 · C-01/C-03/VC-051 — categoria pelo VIZINHO, sem exigir o LM
# ---------------------------------------------------------------------------


def test_d4_d5_categoria_pelo_vizinho_sem_lm(raiz_tmp):
    """D4 (C-03): o lote de categorização ABORTAVA sem o LM Studio — mas a
    conciliação sempre soube quem é o vizinho mais parecido (fuzzy 100%
    local) e jogava a resposta fora (VC-051). D5 (C-01): o mecanismo só
    valia para item NOVO; produto já cadastrado sem categoria ficava
    'Outros' para sempre. Os dois degraus, SEM LM, com a lei do humano
    intacta."""
    from app.core.database import Database
    from app.core.repositories import ProdutoRepositorio
    from app.qt.telas import planilha, servico
    from app.scripts.enriquecer_banco import categorizar_acervo
    _app()
    _ia_desligada()
    db = Database().init()
    with db.Session() as s:
        repo = ProdutoRepositorio(s)
        repo.importar("ARROZ TIO JOAO 5KG", categoria="Mercearia")
        repo.importar("DETERGENTE YPE CLEAR 500ML", categoria="Limpeza")
        alvo = repo.importar("ARROZ CAMIL 5KG").produto      # SEM categoria
        alvo_id = alvo.id
        s.commit()
    db.engine.dispose()

    # D4 — o lote funciona SEM LM: o vizinho fuzzy dá a categoria
    resumo = categorizar_acervo(None, log=lambda *_: None)
    assert resumo["categorizados"] >= 1, (
        "o lote ABORTOU sem o LM Studio — o vizinho fuzzy local existia "
        "e ninguém o usava (C-03/D4)")
    assert resumo.get("por_vizinho", 0) >= 1
    db = Database().init()
    with db.Session() as s:
        p = next(x for x in ProdutoRepositorio(s).listar(limit=50)
                 if x.id == alvo_id)
        assert p.categoria is not None and p.categoria.nome == "Mercearia", (
            "o Arroz Camil não herdou a categoria do vizinho Arroz Tio João")
        assert p.categoria_origem == "vizinho"
    db.engine.dispose()

    # D5 — a conciliação conserta o acervo: produto casado SEM categoria
    # ganha a do vizinho na hora da importação
    db = Database().init()
    with db.Session() as s:
        novo = ProdutoRepositorio(s).importar("FEIJAO TIO JOAO 1KG").produto
        novo_id = novo.id
        s.commit()
    db.engine.dispose()
    res = servico.conciliar_linhas([("FEIJAO TIO JOAO 1KG", "8,99", None)],
                                   lambda _m: None)
    assert res.itens and res.itens[0].produto_id == novo_id
    assert res.itens[0].categoria == "Mercearia", (
        "a conciliação casou o produto sem categoria e NÃO consertou o "
        "acervo com o vizinho (C-01/D5)")

    # a lei do humano: a categoria digitada na GRADE marca origem "humano"
    item = res.itens[0]
    ok, aviso = planilha.aplicar_edicao(item, "Categoria", "Padaria")
    assert ok and aviso is None
    db = Database().init()
    with db.Session() as s:
        p = ProdutoRepositorio(s).listar(limit=50)
        p = next(x for x in p if x.id == novo_id)
        assert p.categoria_origem == "humano", (
            "a grade da Mesa gravou categoria SEM marcar 'humano' — o "
            "passe de lote pode vencer o dono (a fresta achada pelo scout)")
    db.engine.dispose()


# ---------------------------------------------------------------------------
# D7 · P-01..P-04/VC-033 — a validade viva + o evento do projeto (trava #3)
# ---------------------------------------------------------------------------


def test_d7_validade_viva_chega_ao_rodape_fora_de_celula(raiz_tmp):
    """D7 (o achado ESTRUTURAL do scout, fora de todos os dossiês): uma
    região 'Validade da oferta' FORA de célula de produto — o rodapé
    típico do tabloide — NUNCA recebia a validade viva: o compositor monta
    um DadosProduto vazio para slot sem produto (compositor.py:670) e a
    validade mora só nos slots MAPEADOS. O marco da F12 contornou com
    texto_fixo (a 'validade por pixel' não provou o caminho vivo). Prova
    por PIXEL no caminho real."""
    from app.qt.telas import servico
    from app.rendering.compositor import compor_pagina, mm_para_px
    from app.rendering.model import PapelTexto
    _app()
    it = servico.ItemMesa("Arroz", "24,90", "VERDE", "Arroz Tio João 5kg")
    rodape = Regiao(TipoRegiao.TEXTO_LEGAL, Retangulo(10, 80, 80, 12),
                    nome="Validade da oferta",
                    papel_texto=PapelTexto.VALIDADE)
    lay = LayoutDef(100, 100, dpi=100, paginas=[Pagina([
        Slot("c1", [Regiao(TipoRegiao.NOME, Retangulo(10, 10, 60, 12),
                           nome="Nome")]),
        Slot("rodape", [rodape]),
    ])])
    dados = {"c1": servico.dados_para_desenho(
        it, validade="OFERTA VÁLIDA ATÉ 31/07/2026")}
    img = compor_pagina(lay, lay.paginas[0], dados)

    x0 = round(mm_para_px(10, 100)); x1 = round(mm_para_px(90, 100))
    y0 = round(mm_para_px(80, 100)); y1 = round(mm_para_px(92, 100))
    recorte = img.convert("L").crop((x0, y0, x1, y1))
    tinta = sum(1 for p in recorte.getdata() if p < 160)
    assert tinta > 30, (
        "o rodapé 'Validade da oferta' saiu VAZIO — a validade viva não "
        "chega a região fora de célula de produto (P-01/D7); o canal não "
        "existe no compositor")


def test_d7_evento_vive_no_projeto_e_a_validade_se_sugere_no_export(
        raiz_tmp, tmp_path, monkeypatch):
    """D7 (a 'uma linha que ressuscita 3 funções'): o evento digitado no
    salvar era JOGADO FORA (mesa.py:839 usa e descarta; reabrir ignora
    p.evento) — meta do evento, pulso 32/40 e {evento} nas frases nasciam
    mortos. E a sugestão de validade só rodava no SALVAR, nunca no
    EXPORT. As duas linhas + a sugestão na porta que faltava."""
    from app.core.database import Database
    from app.core import projetos
    from app.qt.telas import eventos
    from app.qt.telas.mesa import MesaTela
    _app()
    db = Database().init()
    with db.Session() as s:
        eventos.criar_evento(s, "Quintou", dia_semana=3)   # quinta-feira
        s.commit()
    db.engine.dispose()

    m = _mesa_com_item(tmp_path)
    m.show()
    drenar()
    try:
        with _vigia_salvar_projeto(evento="Quintou") as v:
            m._salvar_projeto()
        assert v["disparou"], "o diálogo de salvar nem abriu"
        assert getattr(m, "_evento", None) == "Quintou", (
            "o evento digitado no salvar foi JOGADO FORA (mesa.py:839) — "
            "meta/pulso/{evento} continuam mortos (P-03/D7)")

        # a validade some (o dono limpou); o EXPORT tem de sugerir sozinho
        m._validade = None
        m._validade_lbl.setText("")
        destino = tmp_path / "saida_d7.png"
        from PySide6.QtWidgets import QFileDialog
        monkeypatch.setattr(                     # picker NATIVO (lei do C8)
            QFileDialog, "getSaveFileName",
            staticmethod(lambda *a, **k: (str(destino), "PNG (*.png)")))
        m._exportar()
        drenar()
        assert m._validade, (
            "o EXPORT saiu sem a validade e ninguém sugeriu a da campanha "
            "— a sugestão só roda no salvar (P-02/D7)")

        # a 2ª linha: reabrir o congelado devolve o evento ao projeto
        m2 = MesaTela()
        m2.setAttribute(Qt.WidgetAttribute.WA_DontShowOnScreen, True)
        p = projetos.abrir_projeto(m._projeto_id)
        m2.abrir_projeto_congelado(p)
        try:
            assert getattr(m2, "_evento", None) == "Quintou", (
                "reabrir o projeto IGNOROU p.evento — a Mesa esquece a "
                "campanha do projeto (P-03/D7)")
        finally:
            m2.close()
    finally:
        m.close()


# ---------------------------------------------------------------------------
# D8 · P-05..P-08 — exportar limpo por padrão; Aprovar visível (trava #1)
# ---------------------------------------------------------------------------


def test_d8_etiquetas_saem_limpas_por_padrao_e_rascunho_e_opcao(
        raiz_tmp, tmp_path):
    """D8 (a trava #1 na porta mais testável, a 4ª): o default de
    gerar_etiquetas_lote era rascunho=True — TODA etiqueta nascia
    carimbada e a aprovação era inalcançável (P-05/P-06). A decisão do
    dono (24/07): exportar sai LIMPO por padrão; RASCUNHO vira opção
    EXPLÍCITA. Prova por bytes da imagem embutida no PDF."""
    from pypdf import PdfReader
    from app.qt.telas import servico
    _app()
    it = servico.ItemMesa("Arroz", "24,90", "VERDE", "Arroz Tio João 5kg")

    def _bytes_do_pdf(caminho):
        pagina = PdfReader(str(caminho)).pages[0]
        return pagina.images[0].data

    padrao = tmp_path / "padrao.pdf"
    limpo = tmp_path / "limpo.pdf"
    marcado = tmp_path / "marcado.pdf"
    servico.gerar_etiquetas_lote([it], padrao)
    servico.gerar_etiquetas_lote([it], limpo, rascunho=False)
    servico.gerar_etiquetas_lote([it], marcado, rascunho=True)

    assert _bytes_do_pdf(padrao) == _bytes_do_pdf(limpo), (
        "o DEFAULT ainda carimba RASCUNHO — a trava #1 continua de pé "
        "(P-05/D8): exportar limpo tinha de ser o padrão")
    assert _bytes_do_pdf(marcado) != _bytes_do_pdf(limpo), (
        "rascunho=True não carimba mais NADA — a opção explícita morreu")


def test_d8_botao_aprovar_visivel_na_mesa_e_na_fabrica(raiz_tmp):
    """D8 (P-05/P-07): o 'Aprovar' da Mesa morava SÓ na paleta Ctrl+Shift+P
    (invisível) e a Fábrica NÃO TINHA caminho de aprovar (grep zero). O
    botão existe nas DUAS barras."""
    from app.qt.telas.fabrica import FabricaTela
    from app.qt.telas.mesa import MesaTela
    _app()
    m = MesaTela()
    m.setAttribute(Qt.WidgetAttribute.WA_DontShowOnScreen, True)
    m.resize(1500, 800)
    try:
        botao_por_texto(m, "Aprovar")     # falha NOMINAL se não existir
    finally:
        m.close()
    f = FabricaTela()
    f.setAttribute(Qt.WidgetAttribute.WA_DontShowOnScreen, True)
    f.resize(1500, 800)
    try:
        botao_por_texto(f, "Aprovar")
    finally:
        f.close()


# ---------------------------------------------------------------------------
# D10 · VC-050/VC-040 — o pré-voo ganha o piso da revisora e a nota da foto
# ---------------------------------------------------------------------------


def test_d10_pre_voo_ganha_piso_da_revisora_e_nota_da_foto(raiz_tmp,
                                                           tmp_path):
    """D10: o app JÁ detecta nome cortado por medida (revisora, heurística
    sem IA) e foto ruim (avaliador) — mas só conta no botão 'Revisar' e no
    tooltip do Almoxarifado; o pré-voo (a hora certa) ficava mudo. Os dois
    sinais entram em validar_composicao."""
    from PIL import Image
    from app.qt.telas import servico
    _app()
    foto_ruim = tmp_path / "foto_ruim.png"
    Image.new("RGB", (100, 80), (90, 90, 90)).save(foto_ruim)   # minúscula

    it = servico.ItemMesa(
        "REFRI GUARANA", "7,99", "VERDE",
        "Refrigerante Guaraná Antártica Zero Açúcar 2 Litros Retornável")
    it.imagem = str(foto_ruim)
    lay = LayoutDef(100, 100, dpi=100, paginas=[Pagina([Slot("c1", [
        Regiao(TipoRegiao.IMAGEM, Retangulo(10, 10, 20, 15), nome="Foto"),
        Regiao(TipoRegiao.NOME, Retangulo(10, 27, 18, 6), nome="Nome"),
        Regiao(TipoRegiao.PRECO, Retangulo(10, 35, 20, 8), nome="Preço"),
    ])])])
    avisos = servico.validar_composicao(
        lay, {"c1": servico.dados_para_desenho(it)})

    assert any("cortad" in a.lower() for a in avisos), (
        "o pré-voo NÃO avisa o nome cortado por medida — a heurística "
        "existe na revisora e só sai no botão Revisar (VC-050/D10): "
        f"{avisos}")
    assert any("foto" in a.lower() and
               ("pequena" in a.lower() or "ruim" in a.lower())
               for a in avisos), (
        "o pré-voo NÃO avisa a foto de nota RUIM — o avaliador existe e "
        f"só sai no tooltip do Almoxarifado (VC-040/D10): {avisos}")


# ---------------------------------------------------------------------------
# D11 · C-06/C-07 — o destaque vai para a célula GRANDE (área do slot)
# ---------------------------------------------------------------------------


def test_d11_heroi_vai_para_a_celula_grande(raiz_tmp):
    """D11 (N-choque-2): o auto-preencher era zip POSICIONAL — o herói (o
    preço mais agressivo) caía na 1ª célula da ordem de leitura, mesmo
    quando a arte tem uma célula de DESTAQUE gigante mais abaixo. O herói
    agora vai para a MAIOR célula (área do slot)."""
    from app.qt.telas import servico
    from app.qt.telas.mesa import MesaTela
    _app()
    m = MesaTela()
    m.setAttribute(Qt.WidgetAttribute.WA_DontShowOnScreen, True)
    a = servico.ItemMesa("Arroz", "9,90", "VERDE", "Arroz")
    b = servico.ItemMesa("Feijao", "2,99", "VERDE", "Feijão")   # o herói
    c = servico.ItemMesa("Oleo", "5,50", "VERDE", "Óleo")
    m._itens = [a, b, c]

    def _cel(x, y, w, h):
        return [Regiao(TipoRegiao.NOME, Retangulo(x, y, w, h - 8),
                       nome="Nome"),
                Regiao(TipoRegiao.PRECO,
                       Retangulo(x, y + h - 7, w, 6), nome="Preço")]

    lay = LayoutDef(120, 120, dpi=100, paginas=[Pagina([
        Slot("p1", _cel(10, 10, 30, 25), origem_mm=(10, 10)),
        Slot("p2", _cel(60, 10, 30, 25), origem_mm=(60, 10)),
        Slot("grande", _cel(10, 45, 100, 65), origem_mm=(10, 45)),
    ])])
    m._layout = lay
    m.area.carregar(lay, {})
    m._recarregar_lista()
    # o invariante da produção (4 pontos): habilitado = bool(_itens); o
    # teste semeia a estante direto, então espelha o invariante aqui
    m.btn_preencher.setEnabled(bool(m._itens))
    m.resize(1500, 800)      # RG-53: senão a barra colapsa o checkbox no ···
    m.show()
    drenar()
    try:
        # o checkbox pode estar colapsado no "···" (RG-53 — o espelho é
        # coberto pela FASE 1); o alvo DESTE teste é a POLÍTICA do
        # preenchimento, então o estado entra direto
        m.chk_herois.setChecked(True)
        if m.btn_preencher.isVisible():
            clicar(m.btn_preencher)
        else:                          # botão no "···": o mesmo caminho
            m._auto_preencher()
        drenar()
        assert m._mapa.get("grande") == b.uid, (
            "o HERÓI (R$ 2,99) não foi para a célula GRANDE — o zip "
            "posicional o jogou na 1ª célula da leitura (C-06/D11): "
            f"mapa={m._mapa}")
    finally:
        m.close()


# ---------------------------------------------------------------------------
# D12 · VC-081 — atualizar preços da oferta aberta por chave natural
# ---------------------------------------------------------------------------


def test_d12_atualizar_precos_por_chave_natural(raiz_tmp, tmp_path):
    """D12: a semana é RECORRENTE — reimportar a tabela da semana só tinha
    'Adicionar' (duplica) ou 'Substituir tudo' (ZERA mapa e overrides — a
    montagem inteira morre, mesa.py:1086-1087). O 3º caminho: ATUALIZAR os
    preços dos itens atuais casando por chave natural, preservando mapa,
    overrides e identidade (I1)."""
    from app.qt.telas import servico
    from app.qt.telas.mesa import MesaTela
    _app()
    m = MesaTela()
    m.setAttribute(Qt.WidgetAttribute.WA_DontShowOnScreen, True)
    a = servico.ItemMesa("ARROZ TIO JOAO 5KG", "24,90", "VERDE",
                         "Arroz Tio João 5kg", produto_id=11)
    b = servico.ItemMesa("FEIJAO CARIOCA 1KG", "8,90", "VERDE",
                         "Feijão Carioca 1kg", produto_id=22)
    m._itens = [a, b]
    lay = LayoutDef(100, 100, dpi=100, paginas=[Pagina([
        Slot("c1", [Regiao(TipoRegiao.NOME, Retangulo(10, 10, 35, 12),
                           nome="N1")]),
        Slot("c2", [Regiao(TipoRegiao.NOME, Retangulo(55, 10, 35, 12),
                           nome="N2")]),
    ])])
    m._layout = lay
    m.area.carregar(lay, {})
    m._mapa = {"c1": a.uid, "c2": b.uid}
    m._overrides = {"c1": {"nome": "Arroz do Dono"}}
    m._recarregar_lista()
    m.show()
    drenar()
    try:
        novo = servico.ItemMesa("ARROZ TIO JOAO 5KG", "19,90", "VERDE",
                                "Arroz Tio João 5kg", produto_id=11)
        resultado = servico.ResultadoMesa(itens=[novo])
        with _vigia_sequencia(["Concluir",
                               "Atualizar os preços dos atuais",
                               "Atualizar 1 preço"]) as v:
            m._conciliar(resultado)
            drenar()
        assert v["faltou"] is None, (
            "o caminho da semana recorrente NÃO existe — a caixa só "
            f"oferece Adicionar/Substituir (VC-081/D12): {v['faltou']}")
        assert len(v["respondidos"]) == 3, "a prévia de confirmação não abriu"
        assert a.preco == "19,90", "o preço do item da estante não atualizou"
        assert m._itens == [a, b] and m._itens[0].uid == a.uid, (
            "a atualização trocou os OBJETOS da estante — identidade (I1) "
            "quebrada")
        assert m._mapa == {"c1": a.uid, "c2": b.uid}, (
            "a atualização mexeu no MAPA — a montagem morreu (o mal do "
            "Substituir tudo)")
        assert m._overrides == {"c1": {"nome": "Arroz do Dono"}}, (
            "a atualização apagou os overrides")
        assert not m._salvo, "atualizar preços não sujou o projeto"
    finally:
        m.close()


# ---------------------------------------------------------------------------
# D9 · VC-024/VC-025 — item ↔ célula acesos + miniatura na estante
# ---------------------------------------------------------------------------


def test_d9_estante_e_celula_acesos_nos_dois_sentidos(raiz_tmp, tmp_path):
    """D9 (o painel Links do InDesign): o fio slot↔uid sempre existiu
    (canvas.mapa) e NENHUM lado o mostrava — selecionar na estante não
    acendia a célula, clicar na célula não destacava a linha, e a linha
    era só texto (sem a miniatura da foto). Os dois sentidos + miniatura,
    por gesto."""
    from PySide6.QtWidgets import QLabel
    from app.qt.telas import servico
    from app.qt.telas.mesa import MesaTela
    _app()
    m = MesaTela()
    m.setAttribute(Qt.WidgetAttribute.WA_DontShowOnScreen, True)
    it1 = servico.ItemMesa("Arroz", "24,90", "VERDE", "Arroz")
    it1.imagem = _png(tmp_path / "arroz.png", (200, 40, 40))
    it2 = servico.ItemMesa("Feijao", "8,90", "VERDE", "Feijão")
    it2.imagem = _png(tmp_path / "feijao.png", (40, 40, 200))
    m._itens = [it1, it2]
    lay = LayoutDef(100, 100, dpi=100, paginas=[Pagina([
        Slot("c1", [Regiao(TipoRegiao.NOME, Retangulo(10, 10, 35, 12),
                           nome="N1")]),
        Slot("c2", [Regiao(TipoRegiao.NOME, Retangulo(55, 10, 35, 12),
                           nome="N2")]),
    ])])
    m._layout = lay
    m.area.carregar(lay, {})
    m._mapa = {"c1": it1.uid, "c2": it2.uid}
    m._recarregar_lista()
    m.show()
    drenar()
    try:
        canvas = m.area.canvas
        reg2 = lay.paginas[0].slots[1].regioes[0]
        # 1) estante → canvas: clicar a LINHA do Feijão acende a célula c2
        li = m.lista.item(1)
        clicar(m.lista.viewport(), pos=m.lista.visualItemRect(li).center())
        drenar()
        assert any(i.isSelected() for i in canvas._itens
                   if i.regiao is reg2), (
            "selecionar na estante NÃO acendeu a célula no canvas "
            "(VC-024/D9 — o fio existe e ninguém o mostra)")
        # 2) canvas → estante: clicar a região do Arroz destaca a linha 0
        reg1 = lay.paginas[0].slots[0].regioes[0]
        item1 = next(i for i in canvas._itens if i.regiao is reg1)
        clicar_na_cena(canvas, item1.mapToScene(item1._w / 2, item1._h / 2))
        drenar()
        assert m.lista.currentRow() == 0, (
            "clicar na célula NÃO destacou a linha da estante (VC-024/D9)")
        # 3) a linha tem a MINIATURA da foto (pixmap de verdade, não texto)
        w0 = m.lista.itemWidget(m.lista.item(0))
        thumbs = [lb for lb in w0.findChildren(QLabel)
                  if lb.pixmap() is not None and not lb.pixmap().isNull()]
        assert thumbs, ("a linha da estante segue SÓ texto — sem a "
                        "miniatura da foto (VC-025/D9)")
    finally:
        m.close()


# ---------------------------------------------------------------------------
# D13 · C-10 — a conciliação lembra geometria e largura de coluna
# ---------------------------------------------------------------------------


def test_d13_conciliacao_lembra_geometria_e_largura_de_coluna(raiz_tmp):
    """D13 (C-10): o diálogo abria SEMPRE em 860×560 fixo, as colunas de
    nome eram Stretch (o dono nem conseguia arrastá-las) e cada recarga
    zerava tudo com resizeColumnsToContents. O padrão de memória já
    morava ao lado (splitter_com_memoria, ui.shell) — agora a conciliação
    lembra: tamanho da janela E largura de coluna sobrevivem a fechar e
    reabrir.

    QUINTUSDECIMUS/L3 (contrato editado de propósito): a memória vale
    LIMITADA à tela atual — ``clampar_a_tela`` roda no show. O tamanho
    lembrado aqui é escolhido DENTRO da tela da bancada, para provar a
    memória sem esbarrar na lei nova (que tem teste próprio)."""
    from app.qt.telas import servico
    from app.qt.telas.conciliacao_dialog import ConciliacaoDialog
    _app()
    itens = [servico.ItemMesa("Arroz Tio João 5kg", "24,90", "VERDE",
                              "Arroz Tio João 5kg")]
    dlg = ConciliacaoDialog(servico.ResultadoMesa(itens=itens), None)
    dlg.setAttribute(Qt.WidgetAttribute.WA_DontShowOnScreen, True)
    dlg.show()
    drenar()
    tela = dlg.screen().availableGeometry()
    alvo = (min(1000, tela.width() - 60), min(640, tela.height() - 60))
    # o gesto do dono: ajusta a janela e arrasta a coluna "Importado"
    dlg.resize(*alvo)
    dlg.tabela.horizontalHeader().resizeSection(1, 333)
    drenar()
    dlg.done(0)
    drenar()

    dlg2 = ConciliacaoDialog(servico.ResultadoMesa(itens=itens), None)
    dlg2.setAttribute(Qt.WidgetAttribute.WA_DontShowOnScreen, True)
    dlg2.show()
    drenar()
    try:
        assert (dlg2.width(), dlg2.height()) == alvo, (
            "a janela ESQUECEU o tamanho — abre sempre no default fixo "
            "(C-10/D13)")
        assert dlg2.tabela.columnWidth(1) == 333, (
            "a coluna esqueceu a largura que o dono arrastou (C-10/D13)")
    finally:
        dlg2.done(0)


# ---------------------------------------------------------------------------
# D3 · VC-037 — o detector de fundo branco NASCE ligado
# ---------------------------------------------------------------------------


def test_d3_detector_fundo_branco_nasce_ligado(raiz_tmp, tmp_path):
    """D3 (VC-037): o detector existe, funciona e tem checkbox — mas o
    padrão é DESLIGADO, então quem nunca achou a opção paga 8s de rembg
    em foto que já tem fundo branco. Banco novo, sem NENHUMA config
    gravada: o gate tem de pular o rembg para fundo branco (e continuar
    recortando foto colorida)."""
    from PIL import Image
    from app.images.fundo import _pular_rembg_fundo_branco

    branca = tmp_path / "packshot_fundo_branco.png"
    img = Image.new("RGB", (400, 400), (255, 255, 255))
    for x in range(150, 250):
        for y in range(150, 250):
            img.putpixel((x, y), (180, 30, 30))     # produto no centro
    img.save(branca)

    colorida = tmp_path / "foto_de_celular.png"
    Image.new("RGB", (400, 400), (90, 120, 60)).save(colorida)

    assert _pular_rembg_fundo_branco(branca) is True, (
        "fundo JÁ branco não pulou o rembg — o detector nasce desligado "
        "e o dono paga 8s por foto (VC-037/D3)")
    assert _pular_rembg_fundo_branco(colorida) is False, (
        "foto colorida pulou o rembg — o detector ficou frouxo")

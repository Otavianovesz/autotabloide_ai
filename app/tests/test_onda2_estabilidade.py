"""Onda 2 da REVISAO_GERAL — ESTABILIDADE, com prova.

RG-05 (os travamentos da auditoria do dono): limite de zoom, régua com
passo adaptativo, fit adiado até o viewport real, Ctrl+0, zoom honesto por
tela no rodapé, vigia de travamento e o Almoxarifado sem estado podre após
exclusão/rebusca. RG-05b: gancho GLOBAL de shutdown — nenhum worker vivo
ao fechar a janela principal.
"""

import time
from decimal import Decimal

import pytest
from PySide6.QtCore import QCoreApplication, QEvent, Qt
from PySide6.QtGui import QKeyEvent
from PySide6.QtWidgets import QApplication, QWidget

from app.rendering.compositor import DadosProduto
from app.rendering.model import (
    LayoutDef,
    Pagina,
    Regiao,
    Retangulo,
    Slot,
    TipoRegiao,
)


def _app():
    return QApplication.instance() or QApplication([])


def _layout_min() -> LayoutDef:
    slot = Slot("s", [Regiao(TipoRegiao.NOME, Retangulo(10, 10, 60, 12),
                             nome="Nome")])
    return LayoutDef(100, 100, dpi=100, paginas=[Pagina([slot])])


def _canvas_pronto():
    """Canvas carregado e COM viewport real (visível offscreen)."""
    from app.qt.canvas import CanvasView

    c = CanvasView()
    c.resize(900, 700)
    c.show()
    QCoreApplication.processEvents()
    c.carregar(_layout_min(), DadosProduto("Produto Teste",
                                           preco_por=Decimal("9.99")))
    QCoreApplication.processEvents()
    return c


# --- RG-05: zoom com limite (o travamento da Mesa_350) -------------------------------


def test_zoom_tem_limite_minimo_e_maximo():
    """A roda girada sem fim NUNCA leva a escala a 2% (nem a 8000%)."""
    _app()
    from app.qt.canvas import ESCALA_MAX, ESCALA_MIN

    c = _canvas_pronto()
    for _ in range(80):                    # o gesto da auditoria: roda sem fim
        c.zoom(1 / 1.15)
    assert c.escala_atual() >= ESCALA_MIN - 1e-9
    for _ in range(120):
        c.zoom(1.15)
    assert c.escala_atual() <= ESCALA_MAX + 1e-9


def test_regua_passo_adaptativo_limita_marcas():
    """Em QUALQUER zoom o nº de marcas por régua fica pequeno (o paint de
    milhares de marcas era o peso do 'canvas cinza')."""
    from app.qt.canvas import passo_da_regua

    for px_por_mm in (8.0, 1.0, 0.4, 0.05, 0.001):
        passo = passo_da_regua(px_por_mm)
        marcas_em_1400px = 1400 / (px_por_mm * passo)
        assert marcas_em_1400px <= 40, (px_por_mm, passo)
    assert passo_da_regua(4.0) == 10       # zoom de trabalho: régua fininha


def test_ajustar_com_viewport_minusculo_fica_pendente():
    """O fit do boot (tela ainda sem tamanho REAL) não deixa a escala
    microscópica — fica pendente e acontece no primeiro resize de verdade
    (o 'Zoom 2%' vinha de um fit com o canvas espremido a ~30 px)."""
    _app()
    from app.qt.canvas import CanvasView

    c = CanvasView()
    c.show()                               # com show o viewport é o REAL…
    c.resize(50, 20)                       # …e aqui está espremido (boot)
    QCoreApplication.processEvents()
    c.carregar(_layout_min(), DadosProduto("P", preco_por=Decimal("1.00")))
    assert c.escala_atual() == pytest.approx(1.0)   # nunca 0.02
    assert c._ajuste_pendente
    c.resize(900, 700)
    QCoreApplication.processEvents()
    assert not c._ajuste_pendente          # o fit adiado aconteceu
    assert c.escala_atual() > 0.5          # página ~378px num viewport de 900


def _esperar_animacoes(prazo_s: float = 2.0) -> None:
    """FASE 1 (passo 46): o enquadramento é ANIMADO — o teste espera o
    destino como o usuário vê, usando o registro vivo do motor."""
    import time

    from app.qt.design.animacoes import animacoes_ativas
    fim = time.monotonic() + prazo_s
    while time.monotonic() < fim and animacoes_ativas():
        QCoreApplication.processEvents()
        time.sleep(0.01)
    QCoreApplication.processEvents()


def test_ctrl_zero_enquadra_de_qualquer_zoom():
    """Ctrl+0 é a saída do estado-armadilha (2 min presos na auditoria)."""
    _app()
    c = _canvas_pronto()
    c.ajustar()
    _esperar_animacoes()
    esperada = c.escala_atual()
    for _ in range(30):
        c.zoom(1 / 1.15)
    assert c.escala_atual() != pytest.approx(esperada)
    ev = QKeyEvent(QEvent.Type.KeyPress, Qt.Key.Key_0,
                   Qt.KeyboardModifier.ControlModifier)
    c.keyPressEvent(ev)
    _esperar_animacoes()
    assert c.escala_atual() == pytest.approx(esperada)


def test_rodape_de_zoom_segue_a_tela_ativa():
    """O rodapé mostrava o zoom de um canvas invisível ('Zoom 2%' eterno) —
    agora segue o canvas da tela ativa e apaga em tela sem canvas."""
    _app()
    from app.qt.design.shell import Shell

    shell = Shell()
    c1, c2 = _canvas_pronto(), _canvas_pronto()
    shell.adicionar_tela("mesa", QWidget())
    shell.adicionar_tela("cofre", QWidget())
    shell.registrar_zoom("mesa", c1)
    c1.ajustar()
    shell.ir_para("mesa")
    assert f"{c1.escala_atual() * 100:.0f}%" in shell._zoom.text()

    c2.zoom(1 / 2)                         # canvas de OUTRA tela não fala
    texto_antes = shell._zoom.text()
    shell.registrar_zoom("atelie", c2)
    c2.zoom(1.5)
    assert shell._zoom.text() == texto_antes

    shell.ir_para("cofre")                 # tela sem canvas: sem número solto
    assert shell._zoom.text() == ""


# --- RG-05: vigia de travamento -------------------------------------------------------


def test_vigia_grava_traceback_quando_a_ui_para(tmp_path):
    from app.core.vigia import VigiaTravamento

    log = tmp_path / "logs" / "travamentos.log"
    v = VigiaTravamento(log, limite_s=0.3).iniciar()
    try:
        v.batimento()
        time.sleep(1.0)                    # a "UI" ficou presa
        assert log.exists()
        texto = log.read_text(encoding="utf-8", errors="replace")
        assert "UI presa" in texto
        assert "Thread" in texto           # o faulthandler despejou as pilhas
        um_dump = texto.count("UI presa")
        time.sleep(0.6)                    # MESMO episódio: não duplica
        texto2 = log.read_text(encoding="utf-8", errors="replace")
        assert texto2.count("UI presa") == um_dump
        v.batimento()                      # a UI voltou → episódio novo conta
        time.sleep(1.0)
        texto3 = log.read_text(encoding="utf-8", errors="replace")
        assert texto3.count("UI presa") == um_dump + 1
    finally:
        v.parar()


# --- RG-05b: gancho GLOBAL de shutdown ------------------------------------------------


def test_encerrar_todos_encerra_gerenciadores_de_todas_as_origens():
    _app()
    from app.qt.workers import GerenciadorTrabalhos, Trabalhador, encerrar_todos

    g1, g2 = GerenciadorTrabalhos(), GerenciadorTrabalhos()
    t1 = Trabalhador(lambda st: time.sleep(0.8))
    t2 = Trabalhador(lambda st: time.sleep(0.8))
    g1.rodar(t1)
    g2.rodar(t2)
    # sob carga o start() demora a virar thread NATIVA (o flake que expôs a
    # janela real do encerrar) — a pré-condição espera a largada de verdade
    inicio = time.monotonic()
    while (not (t1.isRunning() or t2.isRunning())
           and time.monotonic() - inicio < 5):
        time.sleep(0.01)
    assert t1.isRunning() or t2.isRunning()
    encerrar_todos(espera_ms=5000)
    assert not t1.isRunning() and not t2.isRunning()


def test_fechar_a_janela_principal_encerra_os_workers():
    """RG-05b na letra: closeEvent do Shell = nenhum worker vivo sem dono."""
    _app()
    from app.qt.design.shell import Shell
    from app.qt.workers import GerenciadorTrabalhos, Trabalhador

    shell = Shell()
    g = GerenciadorTrabalhos()             # como o de qualquer tela/diálogo
    trab = Trabalhador(lambda st: time.sleep(0.8))
    g.rodar(trab)
    assert trab.isRunning()
    shell.close()                          # dispara o closeEvent
    QCoreApplication.processEvents()
    assert not trab.isRunning()


def test_fila_em_andamento_e_cancelada_no_shutdown():
    _app()
    from app.qt.workers import GerenciadorTrabalhos, TrabalhadorFila, encerrar_todos

    g = GerenciadorTrabalhos()
    fila = TrabalhadorFila([(str(i), i) for i in range(50)],
                           lambda v: time.sleep(0.05))
    g.rodar(fila)
    time.sleep(0.1)                        # deixa alguns itens rodarem
    encerrar_todos(espera_ms=3000)
    assert not fila.isRunning()            # cancelou entre itens e saiu


# --- RG-05/RG-09: Almoxarifado sem estado podre ---------------------------------------


@pytest.fixture()
def catalogo_tmp(tmp_path, monkeypatch):
    monkeypatch.setenv("AUTOTABLOIDE_ROOT", str(tmp_path / "raiz"))
    from app.core.database import Database
    from app.core.paths import SystemRoot
    from app.core.repositories import ProdutoRepositorio

    root = SystemRoot(tmp_path / "raiz").criar_estrutura()
    db = Database(root).init()
    with db.Session() as s:
        repo = ProdutoRepositorio(s)
        for i in range(8):
            repo.importar(f"PRODUTO ONDA2 {i} 100 g", preco=f"{i + 1},00")
        s.commit()
    db.engine.dispose()
    return root


def test_excluir_em_worker_e_painel_solto(catalogo_tmp):
    """Excluir roda fora da UI; o painel solta a linha (nada de editar o
    produto ERRADO depois que a lista muda — o suspeito do travamento 1)."""
    _app()
    from app.qt.telas import servico
    from app.qt.telas.almoxarifado import AlmoxarifadoTela

    tela = AlmoxarifadoTela()
    tela.modelo.fetchMore()
    assert tela.modelo.rowCount() == 8
    tela._selecionou(tela.modelo.index(2))
    assert tela._painel.isVisibleTo(tela) and tela._linha_atual == 2

    alvo = tela.modelo._linhas[2]["id"]
    tela._excluir([alvo])
    tela._trabalhos.encerrar(espera_ms=5000)      # espera o worker do teste
    QCoreApplication.processEvents()

    assert tela._linha_atual == -1                # painel solto (RG-05)
    assert not tela._painel.isVisibleTo(tela)
    assert all(d["id"] != alvo
               for d in servico.listar_catalogo(limite=50))   # excluiu mesmo


def test_atualizar_linha_fora_do_alcance_nao_estoura():
    """Worker de imagem terminando após rebusca/exclusão: sem IndexError."""
    _app()
    from app.qt.telas.almoxarifado import CatalogoModel

    m = CatalogoModel()
    assert m.atualizar_linha(3, {"nome": "x"}) is False
    assert m.atualizar_linha(-1, {"nome": "x"}) is False


# --- RG-06: teclado — Delete/Backspace, Ctrl+V, undo/redo na Mesa --------------------


def _canvas_duas_regioes():
    from app.qt.canvas import CanvasView

    c = CanvasView()
    c.resize(900, 700)
    c.show()
    QCoreApplication.processEvents()
    slot = Slot("s", [
        Regiao(TipoRegiao.NOME, Retangulo(10, 10, 60, 12), nome="Nome"),
        Regiao(TipoRegiao.PRECO, Retangulo(10, 30, 60, 12), nome="Preço"),
    ])
    layout = LayoutDef(100, 100, dpi=100, paginas=[Pagina([slot])])
    c.carregar(layout, DadosProduto("P", preco_por=Decimal("1.00")))
    return c


def test_delete_exclui_a_selecao_inteira_e_um_undo_restaura():
    """O menu sempre prometeu 'Excluir · Del' — a tecla agora cumpre, e a
    seleção múltipla sai como UM gesto (1 estado de undo)."""
    _app()
    c = _canvas_duas_regioes()
    assert len(c.regioes()) == 2
    for it in c._itens:
        it.setSelected(True)
    c.keyPressEvent(QKeyEvent(QEvent.Type.KeyPress, Qt.Key.Key_Delete,
                              Qt.KeyboardModifier.NoModifier))
    assert c.regioes() == []
    assert c.desfazer()                    # UM undo…
    assert len(c.regioes()) == 2           # …restaura as DUAS


def test_backspace_tambem_exclui():
    _app()
    c = _canvas_duas_regioes()
    c._itens[0].setSelected(True)
    c.keyPressEvent(QKeyEvent(QEvent.Type.KeyPress, Qt.Key.Key_Backspace,
                              Qt.KeyboardModifier.NoModifier))
    assert len(c.regioes()) == 1


def test_ctrl_v_na_curadoria_cola_imagem():
    """O botão 'Colar' sempre funcionou; o ATALHO não existia (RG-06)."""
    _app()
    from PySide6.QtGui import QImage, QKeySequence, QShortcut
    from app.qt.telas.curadoria_dialog import CuradoriaDialog

    img = QImage(24, 24, QImage.Format.Format_RGB32)
    img.fill(0xFFCC0000)
    QApplication.clipboard().setImage(img)
    dlg = CuradoriaDialog("Produto X", [])
    colar = [s for s in dlg.findChildren(QShortcut)
             if s.key() == QKeySequence(QKeySequence.StandardKey.Paste)]
    assert colar, "a curadoria está sem o atalho Ctrl+V"
    colar[0].activated.emit()
    tipo, caminho = dlg.escolha
    assert tipo == "arquivo" and caminho.endswith("colada.png")


def test_undo_redo_na_mesa_por_botao_e_atalho():
    """RG-06: a Mesa ganhou desfazer/refazer (hoje só o Ateliê tinha)."""
    _app()
    from app.qt.telas.mesa import MesaTela
    from app.tests.test_adversarial_vinculo import _grade_4

    mesa = MesaTela()
    mesa.carregar_layout(_grade_4(), None)
    canvas = mesa.area.canvas
    antes = len(canvas.regioes())
    canvas.excluir_regiao(canvas.regioes()[0])
    depois = len(canvas.regioes())
    assert depois < antes
    mesa.desfazer()                        # o que o botão/Ctrl+Z chamam
    assert len(canvas.regioes()) == antes
    mesa.refazer()                         # botão/Ctrl+Y
    assert len(canvas.regioes()) == depois
    assert mesa.btn_desfazer.toolTip().startswith("Desfazer")
    assert mesa.btn_refazer.toolTip().startswith("Refazer")


# --- RG-07: gestão da estante ---------------------------------------------------------


def _mesa_com_3_itens():
    from app.qt.telas.mesa import MesaTela
    from app.qt.telas.servico import ItemMesa
    from app.tests.test_adversarial_vinculo import _grade_4

    mesa = MesaTela()
    mesa.carregar_layout(_grade_4(), None)
    mesa._itens = [ItemMesa(f"ITEM {i} 100 G", "1,00", "VERDE", f"Item {i}")
                   for i in range(3)]
    mesa.chk_agrupar.setChecked(False)
    mesa._auto_preencher()
    return mesa


def test_excluir_item_da_estante_esvazia_a_celula():
    _app()
    mesa = _mesa_com_3_itens()
    assert len(mesa._mapa) == 3
    uid0 = mesa._itens[0].uid
    mesa._excluir_item(0)
    assert len(mesa._itens) == 2
    assert all(uid != uid0 for uid in mesa._mapa.values())   # célula esvaziou
    assert "(2)" in mesa._painel_itens._rotulo.text()        # contagem viva
    assert mesa.btn_exportar.isEnabled()   # ainda há itens na grade


def test_limpar_estante_confirma_e_zera(monkeypatch):
    _app()
    # FASE 1 (passo 78): a confirmação virou confirmar_destrutivo (verbo
    # no botão) — o teste mocka o helper da casa, não mais o QMessageBox
    import app.qt.design.componentes as comp

    mesa = _mesa_com_3_itens()
    respostas = iter([False, True])
    monkeypatch.setattr(comp, "confirmar_destrutivo",
                        lambda *a, **k: next(respostas))
    mesa._limpar_estante()                 # 1º: o humano desistiu (No)
    assert len(mesa._itens) == 3           # nada mudou
    mesa._limpar_estante()                 # 2º: confirmou (Yes)
    assert mesa._itens == [] and mesa._mapa == {}
    assert not mesa.btn_exportar.isEnabled()
    assert "(“" not in mesa._painel_itens._rotulo.text()
    assert "(3)" not in mesa._painel_itens._rotulo.text()


def test_menu_da_estante_tem_excluir_e_del():
    """O gesto que o dono procurou e não achou: botão direito → excluir."""
    _app()
    mesa = _mesa_com_3_itens()
    # o atalho Del está pendurado NA LISTA (não rouba o Del do canvas)
    from PySide6.QtGui import QKeySequence, QShortcut
    atalhos = [s for s in mesa.lista.findChildren(QShortcut)] + \
              [s for s in mesa.findChildren(QShortcut)
               if s.parent() is mesa.lista]
    assert any(s.key() == QKeySequence(Qt.Key.Key_Delete) for s in atalhos)
    mesa.lista.setCurrentRow(1)
    uid1 = mesa._itens[1].uid
    mesa._excluir_item_selecionado()
    assert all(it.uid != uid1 for it in mesa._itens)


# --- RG-08: dessincronia entre telas --------------------------------------------------


def _salvar_no_banco(nome: str, layout) -> None:
    from app.core.database import Database
    from app.rendering.persistencia import salvar_layout

    db = Database().init()
    try:
        with db.Session() as s:
            salvar_layout(s, nome, layout, tipo_midia="TABLOIDE")
            s.commit()
    finally:
        db.engine.dispose()


def test_mesa_resincroniza_layout_editado_no_atelie(catalogo_tmp):
    """Editar no Ateliê → voltar à Mesa recarrega o layout; estante, mapa
    (por uid — I1) e overrides sobrevivem."""
    _app()
    from app.qt.telas.mesa import MesaTela
    from app.rendering.model import Regiao, Retangulo, TipoRegiao
    from app.tests.test_adversarial_vinculo import _grade_4

    v1 = _grade_4()
    _salvar_no_banco("Grade RG08", v1)
    mesa = MesaTela()
    mesa.carregar_layout(v1, None, nome_layout="Grade RG08")
    from app.qt.telas.servico import ItemMesa
    mesa._itens = [ItemMesa(f"IT {i} 100 G", "1,00", "VERDE", f"Item {i}")
                   for i in range(3)]
    mesa.chk_agrupar.setChecked(False)
    mesa._auto_preencher()
    mapa_antes = dict(mesa._mapa)

    v2 = _grade_4()                        # "o Ateliê editou": região a mais
    v2.paginas[0].slots[0].regioes.append(
        Regiao(TipoRegiao.NOME, Retangulo(1, 1, 20, 6), nome="Etiqueta RG08"))
    _salvar_no_banco("Grade RG08", v2)

    mesa._sincronizar_do_atelie()          # o que o showEvent chama
    nomes = [r.nome for s in mesa._layout.paginas[0].slots for r in s.regioes]
    assert "Etiqueta RG08" in nomes        # o layout novo chegou
    assert mesa._mapa == mapa_antes        # o vínculo por uid sobreviveu

    # sem NOVA edição no banco, re-mostrar não recompõe nada (assinatura bate)
    layout_obj = mesa._layout
    mesa._sincronizar_do_atelie()
    assert mesa._layout is layout_obj


def test_projeto_congelado_nunca_resincroniza(catalogo_tmp):
    """Decisão travada: o projeto congela o layout DA ÉPOCA — mesmo com o
    Ateliê tendo editado o layout de mesmo nome no banco."""
    _app()
    from app.core.projetos import ProjetoAberto
    from app.qt.telas.mesa import MesaTela
    from app.rendering.model import Regiao, Retangulo, TipoRegiao
    from app.tests.test_adversarial_vinculo import _grade_4

    epoca = _grade_4()
    mesa = MesaTela()
    mesa._layout_nome = "Grade RG08c"      # o layout congelado veio DESTE nome
    p = ProjetoAberto(id=1, nome="Congelado", evento=None, tipo="TABLOIDE",
                      layout=epoca, itens=[], criado_em="hoje")
    mesa.abrir_projeto_congelado(p)

    v2 = _grade_4()
    v2.paginas[0].slots[0].regioes.append(
        Regiao(TipoRegiao.NOME, Retangulo(1, 1, 20, 6), nome="Invasora"))
    _salvar_no_banco("Grade RG08c", v2)

    mesa._sincronizar_do_atelie()
    nomes = [r.nome for s in mesa._layout.paginas[0].slots for r in s.regioes]
    assert "Invasora" not in nomes         # o congelado ficou congelado


def test_almoxarifado_rele_o_banco_ao_aparecer(catalogo_tmp):
    """RG-08: produto criado na Mesa aparece no catálogo ao trocar de tela."""
    _app()
    from app.core.database import Database
    from app.core.repositories import ProdutoRepositorio
    from app.qt.telas.almoxarifado import AlmoxarifadoTela

    tela = AlmoxarifadoTela()
    tela.modelo.fetchMore()
    assert tela.modelo.rowCount() == 8
    db = Database().init()
    with db.Session() as s:
        ProdutoRepositorio(s).importar("PRODUTO NOVO DA MESA 1 KG")
        s.commit()
    db.engine.dispose()
    tela.show()                            # showEvent → rebusca
    QCoreApplication.processEvents()
    tela.modelo.fetchMore()
    assert tela.modelo.rowCount() == 9


def test_indicador_salvo_segue_a_tela_ativa():
    """RG-08: 'Salvo' de uma tela não vaza para outra; tela sem documento
    fica sem estado (o indicador único confundia o dono)."""
    _app()
    from app.qt.design.shell import Shell

    shell = Shell()
    shell.adicionar_tela("mesa", QWidget())
    shell.adicionar_tela("cofre", QWidget())
    assert shell._salvo.text() == ""       # nada de "Salvo" de fábrica
    shell.set_salvo_de("mesa", False)      # a Mesa editou (tela NÃO ativa)
    shell.ir_para("cofre")
    assert shell._salvo.text() == ""       # o Cofre não tem documento
    shell.ir_para("mesa")
    assert "Não salvo" in shell._salvo.text()
    shell.set_salvo_de("mesa", True)
    assert "Salvo" in shell._salvo.text()


def test_semear_padrao_nao_sobrescreve_edicao_do_dono(catalogo_tmp):
    """RG-08 (raiz achada na onda): o semeio de boot era upsert e re-gravava
    os layouts padrão TODA abertura — edição do dono neles morria no boot
    seguinte. Agora o semeio só cria os ausentes."""
    _app()
    from app.core.database import Database
    from app.editor_app import _semear_layouts_padrao
    from app.rendering.model import Regiao, Retangulo, TipoRegiao
    from app.rendering.persistencia import (
        carregar_layout,
        listar_layouts,
        salvar_layout,
    )

    _semear_layouts_padrao()               # boot 1: cria os padrões

    def _cartaz():
        db = Database().init()
        try:
            with db.Session() as s:
                row = next(r for r in listar_layouts(s)
                           if r.nome == "Cartaz 10×15 — exemplo")
                return carregar_layout(s, row.id)
        finally:
            db.engine.dispose()

    editado = _cartaz()                    # o dono edita o padrão no Ateliê
    editado.paginas[0].slots[0].regioes.append(
        Regiao(TipoRegiao.NOME, Retangulo(2, 2, 30, 8), nome="Toque do Dono"))
    db = Database().init()
    with db.Session() as s:
        salvar_layout(s, "Cartaz 10×15 — exemplo", editado,
                      tipo_midia="CARTAZ")
        s.commit()
    db.engine.dispose()

    _semear_layouts_padrao()               # boot 2: NÃO pode desfazer
    nomes = [r.nome for s in _cartaz().paginas[0].slots for r in s.regioes]
    assert "Toque do Dono" in nomes


# --- RG-10: grades de miniatura fixas (sem drag) --------------------------------------


def test_listas_de_miniatura_sao_estaticas(catalogo_tmp):
    _app()
    from PySide6.QtWidgets import QListWidget

    from app.qt.telas.almoxarifado import HistoricoImagensDialog
    from app.qt.telas.atelie import AtelieTela
    from app.qt.telas.curadoria_dialog import CuradoriaDialog
    from app.qt.telas.dashboard import DashboardTela

    assert AtelieTela().lista.movement() == QListWidget.Movement.Static
    assert CuradoriaDialog("X", []).lista.movement() == \
        QListWidget.Movement.Static
    assert HistoricoImagensDialog(1).lista.movement() == \
        QListWidget.Movement.Static
    dash = DashboardTela()
    assert dash._prateleira([]).movement() == QListWidget.Movement.Static

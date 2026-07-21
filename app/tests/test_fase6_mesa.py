"""FASE 6 — Mesa I: barra, planilha, filtros, troca/reordenação, rascunho.

Cresce ao longo da fase (um bloco por vez). Bloco A: a barra da Mesa cabe em
qualquer largura (RG-53) — os essenciais nunca vão para o "···".
"""

import shutil
from pathlib import Path

import pytest
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication


def _app():
    return QApplication.instance() or QApplication([])


@pytest.fixture()
def raiz_tmp(tmp_path, monkeypatch):
    monkeypatch.setenv("AUTOTABLOIDE_ROOT", str(tmp_path / "raiz"))
    from app.core.database import Database
    from app.core.paths import SystemRoot
    root = SystemRoot(tmp_path / "raiz").criar_estrutura()
    reais = Path("AutoTabloide_System_Root/fontes")
    if reais.exists():
        for f in reais.glob("*.ttf"):
            shutil.copy(f, root.fontes / f.name)
    Database(root).init().engine.dispose()
    return root


def _mesa_offscreen():
    from app.qt.telas.mesa import MesaTela
    m = MesaTela()
    m.setAttribute(Qt.WidgetAttribute.WA_DontShowOnScreen, True)
    m.show()
    return m


# --- Bloco A: RG-53 — a barra cabe a 720p, essenciais fora do "···" ---------

def _reflow_em(m, largura):
    """Força a largura da barra e roda o reflow (determinístico, sem depender
    do assentamento do layout offscreen)."""
    m.resize(largura, 720)
    m._barra_mesa.resize(largura, m._barra_mesa.height() or 44)
    m._reflow_barra()


def test_barra_mesa_720p_essenciais_e_estouro(raiz_tmp):
    _app()
    m = _mesa_offscreen()
    QApplication.processEvents()
    essenciais = [m.btn_importar, m.btn_preencher, m.btn_exportar,
                  m.btn_salvar_proj, m.btn_desfazer, m.btn_refazer]

    # RG-53: a JANELA pode chegar a 1280 (720p) — a barra não a prende na
    # largura do conteúdo (~1757). Sem o conserto (`barra.setMinimumWidth(1)`),
    # o minimumSizeHint da barra empurraria o mínimo da tela acima de 1280.
    assert m.minimumSizeHint().width() <= 1280

    def _colapsados(m):
        return sum(1 for w, _r, _t in m._sacrificaveis if not w.isVisibleTo(m))

    def _ninguem_espremido(m):
        """GATE 2.2 (ordem F11.5) — MEDIÇÃO INDEPENDENTE: a régua é a
        GEOMETRIA que o Qt concedeu, não a soma de sizeHints que o próprio
        `_reflow_barra` usa (a versão antiga era circular). Se o reflow
        deixar botão demais na barra, o QHBoxLayout espreme alguém abaixo do
        próprio sizeHint (texto cortado de verdade) — e isto falha."""
        m._barra_mesa.layout().activate()
        QApplication.processEvents()
        lay = m._barra_layout
        for i in range(lay.count()):
            w = lay.itemAt(i).widget()
            if w is None or not w.isVisibleTo(m):
                continue
            # largura fixada de propósito (setFixedWidth) é a PRÓPRIA meta —
            # o hint do QSS pode ser maior e não é espremimento
            alvo = min(w.sizeHint().width(), w.maximumWidth())
            assert w.width() >= alvo - 2, (
                type(w).__name__, w.width(), alvo)

    # a 1280: os essenciais ficam; o "···" recolhe o resto (nada corta).
    _reflow_em(m, 1280)
    assert all(w.isVisibleTo(m) for w in essenciais)   # essencial nunca no "···"
    assert m._mais_mesa.isVisibleTo(m)                  # há estouro a 720p
    _ninguem_espremido(m)
    n1280 = _colapsados(m)
    assert n1280 > 0

    # nas 4 larguras da pauta: essenciais SEMPRE visíveis, ninguém espremido
    # (régua independente), e mais espaço = MENOS colapsado.
    ultimos = n1280
    for W in (1366, 1600, 1920):
        _reflow_em(m, W)
        assert all(w.isVisibleTo(m) for w in essenciais)
        _ninguem_espremido(m)
        nW = _colapsados(m)
        assert nW <= ultimos                           # monotônico: nunca corta mais
        ultimos = nW

    # alargando em passos, existe uma largura em que TUDO cabe de verdade —
    # 0 colapsados, "···" some e (régua independente) ninguém espremido.
    W = 2000
    while _colapsados(m) > 0 and W <= 4200:
        _reflow_em(m, W)
        W += 400
    assert _colapsados(m) == 0
    assert not m._mais_mesa.isVisibleTo(m)
    _ninguem_espremido(m)


def test_barra_mesa_sacrificaveis_nao_incluem_essenciais(raiz_tmp):
    """Os itens que podem ir para o "···" são SÓ os secundários — nenhum
    essencial (importar/preencher/exportar/salvar) na lista de sacrifício."""
    _app()
    m = _mesa_offscreen()
    ids_sacrificaveis = {id(w) for w, _r, _t in m._sacrificaveis}
    for essencial in (m.btn_importar, m.btn_preencher, m.btn_exportar,
                      m.btn_salvar_proj, m.btn_desfazer, m.btn_refazer):
        assert id(essencial) not in ids_sacrificaveis


# --- Bloco B: modo planilha (R-051) -----------------------------------------

def _item(nome="Arroz", preco="1,00"):
    from app.qt.telas import servico
    return servico.ItemMesa(nome, preco, "VERDE", nome)


def test_planilha_preco_rejeita_ambiguo_e_grava_valido():
    """Passo 20 (I2): preço válido grava; ambíguo ("2x 5,00") NÃO grava e
    devolve aviso — nunca salva preço errado em silêncio."""
    from app.qt.telas.planilha import aplicar_edicao
    it = _item(preco="1,00")
    ok, aviso = aplicar_edicao(it, "Preço", "9,90")
    assert ok and aviso is None and it.preco == "9,90"
    ok, aviso = aplicar_edicao(it, "Preço", "2x 5,00")
    assert not ok and aviso                      # avisa
    assert it.preco == "9,90"                    # NÃO gravou o lixo


def test_planilha_nome_passa_pela_sanitizacao():
    """Passo 19: o nome editado passa pela sanitização (RG-20)."""
    from app.qt.telas.planilha import aplicar_edicao
    it = _item()
    aplicar_edicao(it, "Nome", "arroz    tio  5kg")
    assert it.nome and "  " not in it.nome       # sanitizado (sem espaço duplo)


def test_planilha_problema_na_celula():
    """Passo 26: célula com problema (sem foto / sem preço) é identificada."""
    from app.qt.telas.planilha import problema_na_celula
    it = _item(preco=None)
    it.imagem = None
    assert problema_na_celula(it, "Foto") == "sem foto"
    assert problema_na_celula(it, "Preço") == "sem preço"
    it.preco = "2x 3,00"
    assert problema_na_celula(it, "Preço") == "preço não entendido"


def test_planilha_reflete_no_canvas_por_uid(raiz_tmp):
    """Passo 27 (I1): editar o preço na planilha reflete no desenho POR UID —
    o slot mapeado ao item mostra o preço novo em _dados_por_slot."""
    from decimal import Decimal

    from app.qt.telas.mesa import MesaTela
    from app.qt.telas.planilha import aplicar_edicao
    from app.rendering.model import (
        LayoutDef, Pagina, Regiao, Retangulo, Slot, TipoRegiao,
    )
    _app()
    m = MesaTela()
    it = _item(preco="1,00")
    m._itens = [it]
    lay = LayoutDef(100, 100, dpi=100, paginas=[Pagina([Slot("c", [
        Regiao(TipoRegiao.IMAGEM, Retangulo(10, 10, 40, 40)),
        Regiao(TipoRegiao.PRECO, Retangulo(10, 52, 40, 10))])])])
    m._layout = lay
    m.area.carregar(lay, {})
    m._mapa = {"c": it.uid}

    aplicar_edicao(it, "Preço", "9,90")           # edição da planilha
    dados = m._dados_por_slot()
    assert dados["c"].preco_por == Decimal("9.90")   # refletiu por uid


def test_planilha_dialogo_edita_celula(raiz_tmp):
    """Smoke da grade: mudar o texto de uma célula grava no ItemMesa."""
    _app()
    m = _mesa_offscreen()
    it = _item(preco="1,00")
    m._itens = [it]
    m._recarregar_lista()
    from app.qt.telas.planilha import COLUNAS
    from app.qt.telas.planilha_dialog import DialogoPlanilha
    dlg = DialogoPlanilha(m, m)
    col_preco = COLUNAS.index("Preço")
    dlg.tab.item(0, col_preco).setText("7,77")    # dispara itemChanged
    assert it.preco == "7,77"


# --- Bloco C: filtros (R-054) ------------------------------------------------

def test_filtrar_itens_combinaveis():
    """R-054/passo 31-32: filtros combináveis (sem foto · sem preço ·
    categoria · busca)."""
    from app.qt.telas import servico
    a = servico.ItemMesa("Arroz", "5,00", "VERDE", "Arroz");  a.imagem = "x.png"; a.categoria = "Grãos"
    b = servico.ItemMesa("Feijão", None, "VERDE", "Feijão");  b.imagem = None;    b.categoria = "Grãos"
    c = servico.ItemMesa("Suco", "2x 3,00", "VERDE", "Suco"); c.imagem = "y.png"; c.categoria = "Bebidas"
    itens = [a, b, c]
    # sem foto → só o Feijão
    assert servico.filtrar_itens(itens, sem_foto=True) == [b]
    # sem preço válido → Feijão (None) e Suco ("2x 3,00" não parseia)
    assert servico.filtrar_itens(itens, sem_preco=True) == [b, c]
    # categoria + busca combinados
    assert servico.filtrar_itens(itens, categoria="Grãos", busca="arr") == [a]
    # sem filtro → todos
    assert servico.filtrar_itens(itens) == itens


# --- Bloco D: rascunho automático (R-061) -----------------------------------

def test_rascunho_isolado_das_versoes_e_recupera(raiz_tmp):
    """R-061/passos 52/54: o rascunho mora em rascunhos/ — NUNCA em projetos/
    nem em versoes/ (não polui as versões manuais, não sobrescreve o salvo);
    e recupera por conteúdo."""
    from app.core import rascunho
    from app.core.paths import SystemRoot
    rascunho.descartar_rascunhos()
    estado = {"nome": "Sexta Verde", "validade": "ATÉ 20/07",
              "itens": [{"uid": "u1", "nome": "Arroz"}],
              "mapa": {"c": "u1"}, "overrides": {}}
    arq = rascunho.salvar_rascunho(estado, ts=1000.0)
    assert arq.parent.name == "rascunhos"
    assert "projetos" not in str(arq) and "versoes" not in str(arq)
    root = SystemRoot().raiz
    if (root / "projetos").exists():
        assert not list((root / "projetos").glob("**/versoes/*"))   # nada em versões
    de_volta = rascunho.carregar_rascunho()
    assert de_volta["nome"] == "Sexta Verde"
    assert de_volta["mapa"] == {"c": "u1"}
    assert rascunho.hora_do_rascunho(de_volta) != "?"


def test_rascunho_rotacao(raiz_tmp):
    """R-061/passo 53: guarda só os últimos N."""
    from app.core import rascunho
    from app.core.rascunho import _lista
    rascunho.descartar_rascunhos()
    for i in range(8):
        rascunho.salvar_rascunho({"n": i}, ts=1000.0 + i, max_manter=3)
    assert len(_lista()) == 3
    assert rascunho.carregar_rascunho()["n"] == 7       # o mais novo


def test_rascunho_mesa_coleta_e_recupera_por_conteudo(raiz_tmp):
    """Passo 60: simular queda → o snapshot da Mesa é coletado, gravado, e uma
    NOVA Mesa recupera por conteúdo (uid preservado, I1)."""
    _app()
    from app.core import rascunho
    from app.qt.telas.mesa import MesaTela
    rascunho.descartar_rascunhos()
    m = MesaTela()
    it = _item("Arroz TIO", "5,00")
    m._itens = [it]
    m._validade = "ATÉ 20/07"
    estado = m._estado_para_rascunho()
    assert estado["itens"][0]["nome"] == "Arroz TIO"
    assert estado["validade"] == "ATÉ 20/07"
    rascunho.salvar_rascunho(estado, ts=1000.0)

    m2 = MesaTela()                                   # "reabre após a queda"
    m2._recuperar_rascunho(rascunho.carregar_rascunho())
    assert len(m2._itens) == 1 and m2._itens[0].nome == "Arroz TIO"
    assert m2._validade == "ATÉ 20/07"
    assert m2._itens[0].uid == it.uid                 # identidade preservada


def test_ctrl_k_mesa_acha_item_e_acao_da_barra(raiz_tmp):
    """Passo 61: o Ctrl+K da Mesa encontra um ITEM da estante e uma AÇÃO da
    barra (a mesma paleta da F2, fonte de resultados da Mesa)."""
    _app()
    from app.qt.telas.mesa import MesaTela
    m = MesaTela()
    m._itens = [_item("Feijão"), _item("Arroz")]
    rotulos = [a[1] for a in m._acoes_da_mesa()]
    assert any("Auto-preencher" in r for r in rotulos)   # ação da barra
    assert any("Item: Feijão" in r for r in rotulos)     # item da estante

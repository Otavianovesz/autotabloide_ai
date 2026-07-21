"""
FASE 4 — Editor I: consertar e destravar (testes do caderno)
============================================================
Bloco A (RG-55 · painel nunca órfão): reprodução + cura POR CONTEÚDO, com a
instrumentação desligável. Os demais blocos adicionam seus testes aqui.
"""

from decimal import Decimal

import pytest
from PySide6.QtCore import QCoreApplication, Qt
from PySide6.QtWidgets import QApplication

from app.rendering.compositor import DadosProduto
from app.rendering.model import (
    LayoutDef, Pagina, Regiao, Retangulo, Slot, TipoRegiao,
)

DPI = 100


def _app():
    return QApplication.instance() or QApplication([])


def _canvas_celula(rot_preco: float = 0.0, overlap: bool = False):
    """Canvas com UMA célula agrupada (imagem+nome+preço). O preço pode
    nascer rotacionado e/ou sob a imagem (os 3 suspeitos do RG-55)."""
    from app.qt.canvas import CanvasView

    c = CanvasView()
    c.resize(600, 500)
    c.show()
    QCoreApplication.processEvents()
    preco_rect = (Retangulo(12, 12, 30, 10) if overlap        # sob a imagem
                  else Retangulo(10, 41, 30, 8))
    trio = Slot("cel", [
        Regiao(TipoRegiao.IMAGEM, Retangulo(10, 10, 40, 40), nome="Img"),
        Regiao(TipoRegiao.NOME, Retangulo(10, 52, 40, 8), nome="Nome"),
        Regiao(TipoRegiao.PRECO, preco_rect, nome="Preço",
               rotacao_graus=rot_preco),
    ])
    lay = LayoutDef(100, 100, dpi=DPI, paginas=[Pagina([trio])])
    c.carregar(lay, DadosProduto("P", preco_por=Decimal("9.99")))
    QCoreApplication.processEvents()
    return c


def _clicar(item, canvas):
    """O gesto do clique frio: o Qt seleciona a região sob o cursor, depois
    a regra da célula (RG-15) roda por cima."""
    item.setSelected(True)
    canvas._emitir_selecao()
    item._selecao_por_clique(False)
    canvas._emitir_selecao()


# --- Bloco A: RG-55, o painel que fica órfão ---------------------------------------

def test_rg55_clique_no_preco_agrupado_mostra_no_painel():
    """Passo 13: o gesto que ANTES esvaziava o painel agora seleciona a
    região e o painel mostra o preço — verificado POR CONTEÚDO (o nome no
    campo, o tipo, o grupo de preço visível), não por 'não deu exceção'."""
    _app()
    from app.qt.painel_propriedades import PainelPropriedades

    c = _canvas_celula(rot_preco=90.0, overlap=True)   # os 3 suspeitos juntos
    painel = PainelPropriedades(c)
    preco = next(it for it in c._itens if it.regiao.nome == "Preço")
    _clicar(preco, c)

    # 1) o trio segue selecionado (mover a célula continua funcionando)
    assert all(it.isSelected() for it in c._itens)
    # 2) mas o painel mostra A REGIÃO CLICADA, nunca órfão (RG-55)
    assert c.selecionada() is preco.regiao
    painel.mostrar(c.selecionada())
    # isVisibleTo(painel): visibilidade relativa ao painel (o top-level não
    # está show()); é o estado que o dono veria com a janela aberta
    assert not painel.vazio.isVisibleTo(painel)        # nada de "Nada selecionado"
    assert painel.reg is preco.regiao
    assert painel.nome.text() == "Preço"               # conteúdo no campo
    assert "preco" in painel.tipo_lbl.text().lower()
    assert painel.grp_preco.isVisibleTo(painel)        # grupo de preço aberto


def test_rg55_resolver_selecao_topo_do_z():
    """Passo 9: resolver_selecao devolve a região CONCRETA no topo do z no
    ponto — cópia/região de cima, nunca 'some'. Aqui o preço (última da
    lista) está sobre a imagem; o ponto comum resolve para o preço."""
    _app()
    c = _canvas_celula(overlap=True)
    preco = next(it for it in c._itens if it.regiao.nome == "Preço")
    pt = preco.mapToScene(preco._w / 2, preco._h / 2)
    r = c.resolver_selecao(pt)
    assert r is preco.regiao                            # a de cima no z
    # ponto claramente fora de qualquer região → None (nunca inventa)
    from PySide6.QtCore import QPointF
    assert c.resolver_selecao(QPointF(-9999, -9999)) is None


def test_rg55_rotacao_mantem_o_vinculo_na_selecao():
    """Passo 8/13: região ROTACIONADA 90° mantém o vínculo — clicar mostra
    ela mesma no painel (o hit-test girado da Onda 3 vale no clique)."""
    _app()
    c = _canvas_celula(rot_preco=90.0)
    preco = next(it for it in c._itens if it.regiao.nome == "Preço")
    _clicar(preco, c)
    assert c.selecionada() is preco.regiao
    assert c.selecionada().rotacao_graus == 90.0


def test_rg55_regiao_solta_continua_direta():
    """Regressão: região SEM irmãs (solta) segue selecionando direto — a
    cura do grupo não muda o caso simples."""
    _app()
    from app.qt.canvas import CanvasView

    c = CanvasView()
    c.resize(500, 400)
    c.show()
    QCoreApplication.processEvents()
    reg = Regiao(TipoRegiao.NOME, Retangulo(10, 10, 40, 10), nome="Solta")
    lay = LayoutDef(100, 100, dpi=DPI, paginas=[Pagina([Slot("s", [reg])])])
    c.carregar(lay, DadosProduto("P"))
    QCoreApplication.processEvents()
    it = c._itens[0]
    _clicar(it, c)
    assert c.selecionada() is reg


def test_rg55_instrumentacao_desligavel():
    """Passo 14: o log de seleção fica DESLIGADO por padrão (custo zero em
    produção) e só captura quando ligado explicitamente."""
    from app.qt.design import diag_selecao

    diag_selecao.desligar()
    diag_selecao.limpar()
    _app()
    c = _canvas_celula()
    preco = next(it for it in c._itens if it.regiao.nome == "Preço")
    _clicar(preco, c)
    assert diag_selecao.registro() == []               # nada capturado (off)

    diag_selecao.ligar()
    _clicar(preco, c)
    assert len(diag_selecao.registro()) > 0            # captura quando ligado
    # e após a cura: NENHUM evento de painel órfão na sequência
    assert not any(e.get("painel_orfao") for e in diag_selecao.registro())
    diag_selecao.desligar()


# --- Bloco B: RG-56, agrupar/desagrupar visível e reversível -----------------------

def _canvas_solta_trio():
    """Canvas com um trio de conteúdo SOLTO (avulso) — pronto p/ agrupar."""
    from app.qt.canvas import CanvasView

    c = CanvasView()
    c.resize(600, 500)
    c.show()
    QCoreApplication.processEvents()
    trio = Slot("livre", [
        Regiao(TipoRegiao.IMAGEM, Retangulo(10, 10, 30, 20), nome="Img"),
        Regiao(TipoRegiao.NOME, Retangulo(10, 32, 30, 8), nome="Nome"),
        Regiao(TipoRegiao.PRECO, Retangulo(10, 41, 30, 8), nome="Preço"),
    ])
    lay = LayoutDef(100, 100, dpi=DPI, paginas=[Pagina([trio])])
    c.carregar(lay, DadosProduto("P", preco_por=Decimal("2.00")))
    QCoreApplication.processEvents()
    return c


def _agrupar_tudo(c):
    for it in c._itens:
        it.setSelected(True)
    c.agrupar_selecao()
    QCoreApplication.processEvents()


def test_rg56_estados_e_legenda_pt_br():
    """Passos 15-21: solta/mestra/cópia — estado e legenda corretos."""
    _app()
    c = _canvas_solta_trio()
    img = c._itens[0].regiao
    assert c.estado_de_grupo(img) == "solta"
    assert "Solta" in c.legenda_de_grupo(img)

    _agrupar_tudo(c)
    m = next(s for s in c._pagina().slots if s.mestre)
    assert c.estado_de_grupo(m.regioes[0]) == "mestra"
    assert "Mestra" in c.legenda_de_grupo(m.regioes[0])

    c.carimbar_grupo(m.id, (50, 50))
    QCoreApplication.processEvents()
    copia = next(s for s in c._pagina().slots if s.ref_grupo == m.id)
    assert c.estado_de_grupo(copia.regioes[0]) == "copia"
    assert "Cópia" in c.legenda_de_grupo(copia.regioes[0])


def test_rg56_lei_da_casa_selo_e_texto_legal_nao_agrupam():
    """Passo 22 (lei da casa reavaliada): SELO e TEXTO_LEGAL nunca viram
    mestre replicável — só imagem/nome/preço/unidade."""
    _app()
    from app.qt.canvas import CanvasView

    c = CanvasView()
    c.resize(600, 500)
    c.show()
    QCoreApplication.processEvents()
    slot = Slot("livre", [
        Regiao(TipoRegiao.SELO, Retangulo(10, 10, 20, 20), nome="Selo"),
        Regiao(TipoRegiao.TEXTO_LEGAL, Retangulo(40, 10, 30, 10), nome="Dica"),
    ])
    lay = LayoutDef(100, 100, dpi=DPI, paginas=[Pagina([slot])])
    c.carregar(lay, DadosProduto("P"))
    QCoreApplication.processEvents()
    for it in c._itens:
        it.setSelected(True)
    assert c.agrupar_selecao() is None                 # recusado (com aviso)
    assert not any(s.mestre for s in c._pagina().slots)


def test_rg56_desagrupar_preserva_ajuste_da_copia_por_conteudo():
    """Passo 23 + 29 (adversarial POR CONTEÚDO): desagrupar dissolve o
    grupo e cada cópia mantém seus valores ATUAIS — o ajuste próprio da
    cópia (cor override) sobrevive, a mestra não é contaminada, nada some."""
    _app()
    c = _canvas_solta_trio()
    _agrupar_tudo(c)
    m = next(s for s in c._pagina().slots if s.mestre)
    preco_mestra = next(r for r in m.regioes if r.tipo == TipoRegiao.PRECO)
    cor_mestra = preco_mestra.cor

    c.carimbar_grupo(m.id, (50, 50))
    QCoreApplication.processEvents()
    copia = next(s for s in c._pagina().slots if s.ref_grupo == m.id)
    preco_copia = next(r for r in copia.regioes if r.tipo == TipoRegiao.PRECO)
    # ajuste PRÓPRIO da cópia: cor diferente, marcada como override
    preco_copia.cor = "#FF0000"
    preco_copia.overrides.add("cor")

    ok = c.desagrupar_regiao(preco_mestra)
    QCoreApplication.processEvents()
    assert ok
    # todos soltos, ids preservados (I1)
    assert all(not s.mestre and s.ref_grupo is None
               for s in c._pagina().slots)
    # o ajuste da cópia SOBREVIVEU como valor próprio; nada de override pendente
    assert preco_copia.cor == "#FF0000"
    assert preco_copia.overrides == set()
    # a mestra NÃO foi contaminada pelo ajuste da cópia
    assert preco_mestra.cor == cor_mestra


def test_rg56_desagrupar_undo_com_mapa_nao_vazio():
    """Passo 24: desfazer um desagrupar restaura o grupo E o mapa fica
    consistente. Com o mapa POPULADO (não {}), a asserção não é vácua:
    agrupar/desagrupar NÃO mudam o mapa (ids preservados, I1) — a
    invariância é conferida com entradas reais."""
    _app()
    c = _canvas_solta_trio()
    _agrupar_tudo(c)
    m = next(s for s in c._pagina().slots if s.mestre)
    c.carimbar_grupo(m.id, (50, 50))
    QCoreApplication.processEvents()
    copia = next(s for s in c._pagina().slots if s.ref_grupo == m.id)
    # POPULA o mapa com entradas REAIS (slot → uid de item)
    c.mapa = {m.id: "item-mestra-uid", copia.id: "item-copia-uid"}
    c._registrar_hist()                                   # baseline com o mapa
    mapa_antes = dict(c.mapa)
    assert mapa_antes and len(mapa_antes) == 2            # não é {} (não-vácuo)

    assert c.desagrupar_regiao(m.regioes[0])
    QCoreApplication.processEvents()
    assert not any(s.mestre for s in c._pagina().slots)   # dissolvido
    assert c.mapa == mapa_antes                           # ids preservados (I1)

    assert c.desfazer()                                   # UM passo
    QCoreApplication.processEvents()
    assert sum(1 for s in c._pagina().slots if s.mestre) == 1  # grupo de volta
    assert c.mapa == mapa_antes                           # o mapa voltou junto


def test_rg56_remover_celula_undo_restaura_mapa_e_layout_juntos():
    """Passo 24 (o caso que DE FATO muta o mapa): remover uma célula da
    grade tira a entrada do mapa E o slot do layout; desfazer restaura os
    DOIS juntos — nunca um sem o outro (D5)."""
    _app()
    c = _canvas_solta_trio()
    _agrupar_tudo(c)
    m = next(s for s in c._pagina().slots if s.mestre)
    c.carimbar_grupo(m.id, (50, 50))
    QCoreApplication.processEvents()
    copia = next(s for s in c._pagina().slots if s.ref_grupo == m.id)
    c.mapa = {m.id: "item-mestra-uid", copia.id: "item-copia-uid"}
    c._registrar_hist()
    mapa_antes = dict(c.mapa)
    n_slots_antes = len(c._pagina().slots)

    # remover a CÓPIA: some do mapa E do layout
    assert c.remover_celula(copia.id)
    QCoreApplication.processEvents()
    assert copia.id not in c.mapa                         # o mapa perdeu a entrada
    assert len(c._pagina().slots) == n_slots_antes - 1    # o layout perdeu o slot

    assert c.desfazer()                                   # UM passo
    QCoreApplication.processEvents()
    assert c.mapa == mapa_antes                           # o mapa VOLTOU
    assert len(c._pagina().slots) == n_slots_antes        # e o layout também


def test_rg56_microtutorial_uma_vez_e_sempre_acessivel(tmp_path, monkeypatch):
    """Passos 25-26: o tutorial abre na 1ª vez (memória) e não repete; o
    caminho da Ajuda ignora a memória (sempre acessível)."""
    monkeypatch.setenv("AUTOTABLOIDE_ROOT", str(tmp_path / "raiz"))
    from app.core.database import Database
    from app.core.paths import SystemRoot
    SystemRoot(tmp_path / "raiz").criar_estrutura()
    Database().init().engine.dispose()

    _app()
    from app.qt.design import tutorial_agrupar as ta
    from app.qt.design.tutorial import _vistos

    assert ta.CHAVE not in _vistos()
    # 1ª vez (headless: mostra seco, marca visto)
    ta.mostrar_tutorial_agrupar(None, so_se_primeira_vez=True)
    assert ta.CHAVE in _vistos()               # marcado
    # 2ª vez com o filtro: NÃO reabre (retorna sem construir) — se abrisse,
    # empilharia outro visto; o teste garante que a memória vale
    ta.mostrar_tutorial_agrupar(None, so_se_primeira_vez=True)   # no-op
    assert ta.CHAVE in _vistos()


def test_rg56_menu_de_cada_estado_oferece_o_inverso_correto():
    """Passos 15-18, 27-29: o menu de contexto de cada estado oferece a
    ação pertinente (fonte única `montar_menu_contexto`) — solta agrupa,
    mestra/cópia desagrupam."""
    _app()
    c = _canvas_solta_trio()

    def rotulos(item):
        menu, _ = item.montar_menu_contexto()
        return [a.text() for a in menu.actions() if a.text()]

    # SOLTA → oferece "Agrupar como replicável", não "Desagrupar"
    r = rotulos(c._itens[0])
    assert "Agrupar como replicável" in r
    assert not any("Desagrupar" in x for x in r)

    _agrupar_tudo(c)
    m = next(s for s in c._pagina().slots if s.mestre)
    im = next(it for it in c._itens if it.regiao is m.regioes[0])
    # MESTRA → "Desagrupar" + "Editar como mestra", nunca "Agrupar"
    r = rotulos(im)
    assert "Desagrupar" in r and "Editar como mestra" in r
    assert not any("Agrupar como" in x for x in r)

    c.carimbar_grupo(m.id, (50, 50))
    QCoreApplication.processEvents()
    cop = next(s for s in c._pagina().slots if s.ref_grupo == m.id)
    ic = next(it for it in c._itens if it.regiao is cop.regioes[0])
    # CÓPIA → "Desagrupar", nunca "Editar como mestra" nem "Agrupar"
    r = rotulos(ic)
    assert "Desagrupar" in r
    assert "Editar como mestra" not in r
    assert not any("Agrupar como" in x for x in r)


# --- Bloco C: RG-49, seções sem linha interna (contorno de união) ------------------

def _secoes_2_linhas():
    """2 células da MESMA categoria, empilhadas (2 linhas) → 1 seção de 2
    sub-retângulos. Devolve (pagina, secoes)."""
    from app.rendering.secoes import calcular_secoes

    a = Slot("a", [Regiao(TipoRegiao.IMAGEM, Retangulo(10, 10, 40, 18),
                          nome="A")])
    b = Slot("b", [Regiao(TipoRegiao.IMAGEM, Retangulo(10, 40, 40, 18),
                          nome="B")])
    pag = Pagina([a, b])
    secoes = calcular_secoes(pag, {"a": "Bebidas", "b": "Bebidas"})
    return pag, secoes


def test_rg49_secao_calcula_uma_secao_de_duas_linhas():
    """Passos 31-33: 2 linhas contíguas da mesma categoria = 1 seção com 2
    sub-retângulos (o run atravessa a quebra de linha)."""
    _pag, secoes = _secoes_2_linhas()
    assert len(secoes) == 1
    assert len(secoes[0].retangulos) == 2
    assert secoes[0].n_celulas == 2


def test_rg49_contorno_uniao_sem_divisoria_interna_por_pixel():
    """Passo 40 (ADVERSARIAL POR PIXEL): a seção de 2 linhas desenha UM
    contorno de união — a faixa ENTRE as linhas irmãs NÃO tem traço (procura
    a AUSÊNCIA), enquanto a borda externa superior EXISTE."""
    from PIL import Image

    from app.rendering.secoes import COR_PADRAO, desenhar_secoes

    _pag, secoes = _secoes_2_linhas()
    dpi = 100
    px_mm = dpi / 25.4
    base = Image.new("RGB", (300, 300), "#FFFFFF")
    desenhar_secoes(base, secoes, dpi=dpi, cor=COR_PADRAO, estilo="CONTORNO")

    r1, r2 = sorted(secoes[0].retangulos, key=lambda r: r.y_mm)
    # a FAIXA INTERNA INTEIRA entre as linhas: da base da linha 1 ao topo da
    # linha 2 (é AQUI que a caixa-por-linha buggada desenha as divisórias —
    # nas bordas das caixas, não só no ponto médio do vão). Varremos toda a
    # faixa (não um único y).
    y_base_l1 = int((r1.y_mm + r1.alt_mm) * px_mm)
    y_topo_l2 = int(r2.y_mm * px_mm)
    # centro horizontal, longe das verticais esquerda/direita da união
    x_ini = int((r1.x_mm + 8) * px_mm)
    x_fim = int((r1.x_mm + r1.larg_mm - 8) * px_mm)
    cor = tuple(int(COR_PADRAO[i:i + 2], 16) for i in (1, 3, 5))

    def _tem_cor(x, y):
        p = base.getpixel((x, y))[:3]
        return all(abs(p[i] - cor[i]) < 60 for i in range(3))

    # NENHUM pixel da cor da seção em NENHUM y da faixa interna (varre a base
    # da linha 1, o vão e o topo da linha 2 — onde a divisória apareceria)
    for y in range(y_base_l1 - 2, y_topo_l2 + 3):
        assert not any(_tem_cor(x, y) for x in range(x_ini, x_fim)), \
            f"divisória interna detectada em y={y} entre linhas irmãs (RG-49)"

    # a seção EXISTE: a borda externa superior (topo da linha 1) tem traço
    y_topo = int(r1.y_mm * px_mm) + 1
    assert any(_tem_cor(x, y_topo) for x in range(x_ini, x_fim)), \
        "a borda externa da seção sumiu"


def test_rg49_sem_divisoria_nos_quatro_estilos():
    """Passo 42: os 4 estilos NÃO deixam traço interno entre linhas irmãs
    (CONTORNO curado; os outros não têm outline — ausência trivial, mas
    conferida)."""
    from PIL import Image

    from app.rendering.secoes import COR_PADRAO, desenhar_secoes

    _pag, secoes = _secoes_2_linhas()
    dpi = 100
    px_mm = dpi / 25.4
    r1, r2 = sorted(secoes[0].retangulos, key=lambda r: r.y_mm)
    y_meio = int(((r1.y_mm + r1.alt_mm) + r2.y_mm) / 2 * px_mm)
    x_ini = int((r1.x_mm + 8) * px_mm)
    x_fim = int((r1.x_mm + r1.larg_mm - 8) * px_mm)
    cor = tuple(int(COR_PADRAO[i:i + 2], 16) for i in (1, 3, 5))

    for estilo in ("CONTORNO", "SO_TITULO", "PILL", "SEM_DESENHO"):
        base = Image.new("RGB", (300, 300), "#FFFFFF")
        desenhar_secoes(base, secoes, dpi=dpi, cor=COR_PADRAO, estilo=estilo)
        achou = False
        for x in range(x_ini, x_fim):
            p = base.getpixel((x, y_meio))[:3]
            if all(abs(p[i] - cor[i]) < 60 for i in range(3)):
                achou = True
                break
        assert not achou, f"traço interno no estilo {estilo}"


def test_rg49_run_de_uma_celula_nao_ganha_caixa():
    """Passo 36: seção de 1 célula, no CONTORNO, NÃO desenha caixa — só o
    rótulo. (Evita a 'caixa boba de item único'.)"""
    from PIL import Image

    from app.rendering.secoes import COR_PADRAO, calcular_secoes, desenhar_secoes

    a = Slot("a", [Regiao(TipoRegiao.IMAGEM, Retangulo(10, 10, 40, 18),
                          nome="A")])
    pag = Pagina([a])
    secoes = calcular_secoes(pag, {"a": "Bebidas"})
    assert secoes[0].n_celulas == 1
    dpi = 100
    px_mm = dpi / 25.4
    base = Image.new("RGB", (300, 300), "#FFFFFF")
    desenhar_secoes(base, secoes, dpi=dpi, cor=COR_PADRAO, estilo="CONTORNO")
    cor = tuple(int(COR_PADRAO[i:i + 2], 16) for i in (1, 3, 5))
    # a borda inferior (longe do rótulo, que fica no topo-esquerda) NÃO tem
    # traço de caixa
    y_base = int((10 + 18 + 1) * px_mm)
    x_meio = int((30) * px_mm)
    p = base.getpixel((x_meio, y_base))[:3]
    assert not all(abs(p[i] - cor[i]) < 60 for i in range(3))


# --- Bloco D: RG-54, formatação do editor a 720p -----------------------------------

def _editor_pronto(tmp_path, monkeypatch):
    monkeypatch.setenv("AUTOTABLOIDE_ROOT", str(tmp_path / "raiz"))
    from app.core.database import Database
    from app.core.paths import SystemRoot
    SystemRoot(tmp_path / "raiz").criar_estrutura()
    Database().init().engine.dispose()
    _app()
    from app.qt.editor import Editor
    ed = Editor()
    ed.setAttribute(Qt.WidgetAttribute.WA_DontShowOnScreen, True)
    ed.resize(1280, 720)
    ed.show()
    QCoreApplication.processEvents()
    trio = Slot("cel", [
        Regiao(TipoRegiao.IMAGEM, Retangulo(20, 15, 60, 45), nome="Imagem"),
        Regiao(TipoRegiao.NOME, Retangulo(20, 62, 60, 10), nome="Nome"),
        Regiao(TipoRegiao.PRECO, Retangulo(20, 74, 60, 18), nome="Preço"),
    ])
    lay = LayoutDef(200, 140, dpi=96, paginas=[Pagina([trio])])
    ed.carregar(lay, DadosProduto("Arroz Camil 5kg", preco_por=Decimal("24.99")))
    QCoreApplication.processEvents()
    return ed


def test_rg54_editor_cabe_em_720p(tmp_path, monkeypatch):
    """Passos 48, 50, 53: o editor cabe em 1280×720 — o painel de
    propriedades ROLA por dentro (não força a janela mais alta) e não há
    barra de rolagem horizontal indevida nele."""
    ed = _editor_pronto(tmp_path, monkeypatch)
    # o painel não força a janela além de 720 (antes exigia ~887)
    assert ed.minimumSizeHint().height() <= 720
    assert ed.height() == 720                       # respeitou o alvo
    # Propriedades está num QScrollArea, com rolagem horizontal DESLIGADA
    from PySide6.QtCore import Qt as _Qt
    assert (ed._rolagem_prop.horizontalScrollBarPolicy()
            == _Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
    # o canvas mantém largura útil (o painel recolhe antes de espremê-lo)
    assert ed.area.width() >= 400
    ed.close()


def test_rg54_painel_lateral_recolhe_e_lembra(tmp_path, monkeypatch):
    """Passo 49: a seta recolhe/expande o painel lateral (telas pequenas
    ganham o canvas) e o estado persiste na Config."""
    ed = _editor_pronto(tmp_path, monkeypatch)
    largura_canvas_antes = ed.area.width()
    assert ed._lateral.isVisible()

    ed.alternar_lateral(False)
    QCoreApplication.processEvents()
    assert not ed._lateral.isVisible()
    assert ed.area.width() > largura_canvas_antes     # canvas ganhou espaço

    from app.core.database import Database
    from app.core.repositories import ConfigRepositorio
    db = Database().init()
    try:
        with db.Session() as s:
            assert ConfigRepositorio(s).get("editor.lateral_visivel") is False
    finally:
        db.engine.dispose()

    ed.alternar_lateral(True)
    QCoreApplication.processEvents()
    assert ed._lateral.isVisible()
    ed.close()


def test_rg54_camadas_mostra_o_trio_inteiro(tmp_path, monkeypatch):
    """Passo 44: a lista de camadas mostra as 3 regiões do trio sem cortar
    (o mínimo dá ~4 linhas)."""
    ed = _editor_pronto(tmp_path, monkeypatch)
    assert ed.camadas.lista.count() == 3            # imagem, nome, preço
    assert ed.camadas.lista.minimumHeight() >= 90
    ed.close()


# --- Bloco E: R-025/026/027/028 (raio-x, guias, grade magnética) -------------------

def _canvas_simples():
    from app.qt.canvas import CanvasView

    c = CanvasView()
    c.resize(500, 400)
    c.show()
    QCoreApplication.processEvents()
    reg = Regiao(TipoRegiao.NOME, Retangulo(10, 10, 30, 10), nome="R")
    lay = LayoutDef(100, 100, dpi=DPI, paginas=[Pagina([Slot("s", [reg])])])
    c.carregar(lay, DadosProduto("P"))
    QCoreApplication.processEvents()
    return c


def test_r027_guia_arrastada_imanta_o_objeto():
    """R-027 (passo 66): uma guia criada entra no serviço de snap — o
    alvo aparece nas coordenadas do serviço unificado (imanta o objeto)."""
    from app.rendering.units import mm_para_px

    _app()
    c = _canvas_simples()
    c.adicionar_guia("x", 50.0)
    assert c._pagina().guias == [("x", 50.0)]
    assert len(c._guias_usuario) == 1                # linha desenhada
    ax, ay = c.alvos_snap(c._itens[0])
    alvo = mm_para_px(50, DPI)
    assert any(abs(a - alvo) < 0.5 for a in ax)      # a guia imanta em x=50mm


def test_r028_grade_magnetica_muda_o_snap():
    """R-028 (passo 66): ligar a grade adiciona os múltiplos do passo ao
    serviço de snap; desligar remove."""
    from app.rendering.units import mm_para_px

    _app()
    c = _canvas_simples()
    alvo_grade = mm_para_px(25, DPI)                 # múltiplo de 5mm
    ax_off, _ = c.alvos_snap(c._itens[0])
    assert not any(abs(a - alvo_grade) < 0.5 for a in ax_off)   # sem grade

    c.set_grade_magnetica(True)
    c.set_grade_passo(5.0)
    ax_on, _ = c.alvos_snap(c._itens[0])
    assert any(abs(a - alvo_grade) < 0.5 for a in ax_on)        # com grade


def test_r027_r028_persistem_por_layout():
    """Passo 64 (I3): guias em mm relativas + grade/passo persistem no
    layout (round-trip do to_dict/from_dict)."""
    _app()
    c = _canvas_simples()
    c.adicionar_guia("y", 30.0)
    c.set_grade_magnetica(True)
    c.set_grade_passo(8.0)
    d = c._layout.to_dict()
    lay2 = LayoutDef.from_dict(d)
    p = lay2.paginas[0]
    assert ("y", 30.0) in p.guias
    assert p.grade_magnetica is True
    assert p.grade_passo_mm == 8.0
    # nenhuma coordenada absoluta em px — as guias são mm (I3)
    assert all(isinstance(g[1], float) for g in p.guias)


def test_r025_r026_raio_x_seleciona_e_mostra_valores():
    """R-025/026 (passo 56/57): o painel de camadas lista o CONTEÚDO de
    cada região e clicar sincroniza a seleção com o canvas — por conteúdo."""
    _app()
    from app.qt.canvas import CanvasView
    from app.qt.painel_camadas import PainelCamadas

    c = CanvasView()
    c.resize(500, 400)
    c.show()
    QCoreApplication.processEvents()
    trio = Slot("cel", [
        Regiao(TipoRegiao.NOME, Retangulo(10, 10, 40, 8), nome="Nome"),
        Regiao(TipoRegiao.PRECO, Retangulo(10, 20, 40, 12), nome="Preço"),
    ])
    lay = LayoutDef(100, 100, dpi=DPI, paginas=[Pagina([trio])])
    c.carregar(lay, DadosProduto("Arroz Camil 5kg", preco_por=Decimal("9.99")))
    QCoreApplication.processEvents()
    painel = PainelCamadas(c)

    # R-026: os valores aparecem (conteudo_da_regiao)
    nome_reg = trio.regioes[0]
    preco_reg = trio.regioes[1]
    assert "Arroz Camil 5kg" in c.conteudo_da_regiao(nome_reg)
    assert "9,99" in c.conteudo_da_regiao(preco_reg)

    # R-025 (via 1): clicar na linha do preço seleciona a região no canvas
    for i in range(painel.lista.count()):
        it = painel.lista.item(i)
        if it.data(Qt.ItemDataRole.UserRole) is preco_reg:
            painel._clicou_na_lista(it)
            break
    assert c.selecionada() is preco_reg

    # via 2: selecionar no canvas destaca a linha certa
    for it in c._itens:
        it.setSelected(it.regiao is nome_reg)
    c._primaria = nome_reg
    c._emitir_selecao()
    atual = painel.lista.currentItem()
    assert atual is not None
    assert atual.data(Qt.ItemDataRole.UserRole) is nome_reg


def test_r028_alt_suspende_o_snap():
    """Passo 63: com Alt pressionado, o itemChange NÃO imanta (posição
    livre) — conferido pelo caminho do snap desligado."""
    _app()
    from PySide6.QtCore import QPointF
    from PySide6.QtWidgets import QApplication

    c = _canvas_simples()
    c.adicionar_guia("x", 50.0)
    it = c._itens[0]
    # posiciona o item bem perto da guia (imantaria sem Alt)
    from app.rendering.units import mm_para_px
    perto = mm_para_px(49.6, DPI)
    # sem Alt: o itemChange devolve a posição IMANTADA (x da guia)
    val = QPointF(perto, 20.0)
    novo = it.itemChange(
        it.GraphicsItemChange.ItemPositionChange, val)
    assert abs(novo.x() - mm_para_px(50, DPI)) < 1.0   # grudou na guia

    # com Alt: devolve a posição LIVRE (não imanta)
    import PySide6.QtWidgets as W
    modo = W.QApplication.keyboardModifiers
    W.QApplication.keyboardModifiers = staticmethod(
        lambda: Qt.KeyboardModifier.AltModifier)
    try:
        novo2 = it.itemChange(
            it.GraphicsItemChange.ItemPositionChange, QPointF(perto, 20.0))
        assert abs(novo2.x() - perto) < 0.5            # ficou livre
    finally:
        W.QApplication.keyboardModifiers = modo


# --- Bloco F: R-029/039/040/041 (zoom, cadeado, raio-x, medidas) -------------------

def test_r041_setas_movem_1mm_e_shift_0_1mm():
    """Passo 76/79: seta move a região EXATAMENTE 1 mm; Shift+seta, 0,1 mm."""
    _app()
    c = _canvas_simples()
    it = c._itens[0]
    it.setSelected(True)
    x0 = it.regiao.rect.x_mm
    c.nudge_selecao(1.0, 0.0)            # seta direita = 1 mm
    assert abs(it.regiao.rect.x_mm - (x0 + 1.0)) < 1e-6
    c.nudge_selecao(0.1, 0.0)            # Shift+seta = 0,1 mm
    assert abs(it.regiao.rect.x_mm - (x0 + 1.1)) < 1e-6
    # sem seleção → não move
    for i in c._itens:
        i.setSelected(False)
    assert c.nudge_selecao(1.0, 0.0) is False


def test_r029_zoom_para_selecao_enquadra():
    """Passo 68/79: zoom-para-seleção enquadra a região (a escala cresce em
    relação ao 'ajustar' à página inteira); sem seleção → False.

    Viewport OFFSCREEN de tamanho fixo (WA_DontShowOnScreen) — determinístico
    no batch headless; a região é bem menor que a página, então o
    enquadramento amplia sem ambiguidade."""
    _app()
    from PySide6.QtCore import QCoreApplication as QC
    from app.qt.canvas import CanvasView
    c = CanvasView()
    c.setAttribute(Qt.WidgetAttribute.WA_DontShowOnScreen, True)
    c.resize(600, 500)
    c.show()
    QC.processEvents()
    reg = Regiao(TipoRegiao.NOME, Retangulo(10, 10, 12, 6), nome="R")   # pequena
    lay = LayoutDef(200, 200, dpi=DPI, paginas=[Pagina([Slot("s", [reg])])])
    c.carregar(lay, DadosProduto("P"))
    QC.processEvents()
    c.ajustar()
    QC.processEvents()
    escala_pagina = c.escala_atual()
    c._itens[0].setSelected(True)
    assert c.zoom_para_selecao() is True
    QC.processEvents()
    assert c.escala_atual() > escala_pagina * 1.5  # enquadrou nítida/mente mais perto
    assert c.escala_atual() <= 8.0                 # respeita o clamp

    for i in c._itens:
        i.setSelected(False)
    assert c.zoom_para_selecao() is False


def test_r029_zoom_100_e_clamp_pct():
    """Passo 69/70: zoom 100% e o nível em % com clamp são."""
    _app()
    c = _canvas_simples()
    c.zoom_100()
    assert c.nivel_zoom_pct() == 100
    # o clamp segura o zoom nos extremos (herda a cura da Onda 2)
    for _ in range(60):
        c.zoom_mais()
    assert c.nivel_zoom_pct() <= 800               # ESCALA_MAX = 8.0


def test_r040_raio_x_esconde_arte_e_mostra_regioes():
    """Passo 73/79: o modo raio-x esconde a arte de fundo (o _bg some) e
    mantém as regiões visíveis (pintadas por papel)."""
    _app()
    c = _canvas_simples()
    assert c.raio_x_ligado() is False
    assert c._bg.isVisible()
    c.set_raio_x(True)
    assert c.raio_x_ligado() is True
    assert not c._bg.isVisible()                   # a arte sumiu
    assert all(it.isVisible() for it in c._itens)  # as regiões ficam
    c.set_raio_x(False)
    assert c._bg.isVisible()                        # a arte volta


def test_r039_arte_travada_por_padrao_e_destrava_com_aviso():
    """Passo 71/72/79: a arte nasce TRAVADA; destravar é gesto consciente
    (o método troca o estado — a arte é fundo de página, não se move)."""
    _app()
    c = _canvas_simples()
    assert c.arte_travada() is True                # travada por padrão
    c.set_arte_travada(False)
    assert c.arte_travada() is False               # destravou (com aviso)
    c.set_arte_travada(True)
    assert c.arte_travada() is True


def test_r041_medidas_ao_vivo_emitem_mm():
    """Passo 75/77: mover a região emite as medidas X/Y/L/A em mm (o rótulo
    ao vivo) — conferido pelo sinal capturado."""
    _app()
    c = _canvas_simples()
    capturado = []
    c.medidas.connect(capturado.append)
    it = c._itens[0]
    it._emitir_medidas()                           # o que o move dispara
    assert capturado
    texto = capturado[-1]
    assert "X " in texto and "L " in texto and "mm" in texto


# --- Reauditoria F4: consertos dos must-fix do arquiteto ---------------------------

def test_fix_atalhos_do_editor_existem_no_boot(tmp_path, monkeypatch):
    """[BLOCKER] os atalhos de edição (duplicar/excluir/copiar/colar/paleta)
    nascem no __init__ e existem JÁ no boot — sem depender de alternar a
    lateral — e não DUPLICAM ao alternar."""
    from PySide6.QtGui import QShortcut

    ed = _editor_pronto(tmp_path, monkeypatch)
    def _teclas():
        return sorted(s.key().toString() for s in ed.findChildren(QShortcut)
                      if s.parent() is ed)
    teclas = _teclas()
    # os atalhos donos do Editor (o Backspace + os do catálogo criados com
    # dono=self) existem no boot
    assert "Ctrl+D" in teclas       # duplicar
    assert "Del" in teclas          # excluir
    assert "Ctrl+C" in teclas       # copiar
    assert "Ctrl+V" in teclas       # colar
    assert "Ctrl+Shift+P" in teclas  # paleta
    assert "Backspace" in teclas
    assert ed._paleta is None       # também inicializado no boot
    n_antes = len(teclas)
    # alternar a lateral 2× NÃO cria atalhos duplicados
    ed.alternar_lateral(False)
    ed.alternar_lateral(True)
    assert len(_teclas()) == n_antes
    ed.close()


def test_fix_barra_cabe_a_720p_sem_cortar_salvar(tmp_path, monkeypatch):
    """[MAJOR RG-54] a 1280 (largura de 720p) o modo compacto ATIVA e a barra
    cabe — a largura mínima da barra fica abaixo de 1280 e o '···' recolhe os
    grupos colapsáveis (Salvar não é cortado)."""
    # raiz própria + reset de ESCALA/fonte ANTES de criar o editor (os
    # widgets cacheiam o minimumSizeHint na fonte de criação; um teste
    # anterior pode ter deixado a escala em 125/150% — a medida do "cabe a
    # 720p" é no zoom de UI padrão, 100%).
    monkeypatch.setenv("AUTOTABLOIDE_ROOT", str(tmp_path / "raiz"))
    from app.core.database import Database
    from app.core.paths import SystemRoot
    SystemRoot(tmp_path / "raiz").criar_estrutura()
    Database().init().engine.dispose()
    _app()
    from app.qt.design.tema import aplicar_tema
    aplicar_tema(_app(), "claro")                  # escala 100% (raiz padrão)
    QCoreApplication.processEvents()

    from app.qt.editor import Editor
    ed = Editor()
    ed.setAttribute(Qt.WidgetAttribute.WA_DontShowOnScreen, True)
    ed.resize(1280, 720)
    ed.show()
    QCoreApplication.processEvents()
    trio = Slot("cel", [Regiao(TipoRegiao.NOME, Retangulo(20, 20, 40, 10),
                               nome="N")])
    ed.carregar(LayoutDef(200, 140, dpi=96, paginas=[Pagina([trio])]),
                DadosProduto("x"))
    QCoreApplication.processEvents()
    b = ed.barra
    # o limiar do compacto é MAIOR que 1280 (senão nunca ativa a 720p)
    assert b.LIMIAR_COMPACTO > 1280
    # a decisão do compacto por LARGURA (a produção chama o mesmo método no
    # resizeEvent). Uso isVisibleTo(b) — reflete o setVisible NA HORA, sem
    # processEvents (que re-dispararia o resizeEvent com a largura real do
    # layout headless e mascararia a medida).
    assert b._aplicar_compacto(b.LIMIAR_COMPACTO + 120) is False   # largo
    assert not b._mais.isVisibleTo(b)              # grupos à mostra
    assert b._aplicar_compacto(1280) is True       # 720p → compacto
    assert b._mais.isVisibleTo(b)                  # o "···" recolheu os grupos
    # o compacto REDUZ a largura mínima da barra pela dos colapsáveis — o
    # mecanismo que impede o corte do Salvar a 720p. Independente de escala
    # (comparação relativa, imune ao vazamento de fonte entre testes headless).
    b._medidas_lbl.setText("")
    lay = b.layout()
    colaps = {id(w) for w in b._colapsaveis}
    largura_colaps = sum(w.minimumSizeHint().width() for w in b._colapsaveis)
    total = sum(lay.itemAt(i).widget().minimumSizeHint().width()
                for i in range(lay.count())
                if lay.itemAt(i).widget() is not None)
    compacto = sum(lay.itemAt(i).widget().minimumSizeHint().width()
                   for i in range(lay.count())
                   if lay.itemAt(i).widget() is not None
                   and id(lay.itemAt(i).widget()) not in colaps)
    assert largura_colaps > 0
    # o conjunto compacto é MENOR que o total (recolheu de verdade); a folga
    # é ~a largura dos colapsáveis menos o "···"
    assert compacto < total
    assert (total - compacto) >= largura_colaps - b._mais.minimumSizeHint().width()
    ed.close()


def test_fix_resolver_selecao_no_caminho_de_producao():
    """[MAJOR RG-55] resolver_selecao NÃO é mais inerte: o `_selecao_por_clique`
    (chamado pelo mousePress real) determina a PRIMÁRIA pelo picking do ponto.
    Com duas regiões empilhadas, clicar resolve a de CIMA — mesmo o handler
    rodando no item de baixo."""
    _app()
    from app.qt.canvas import CanvasView
    baixo = Regiao(TipoRegiao.IMAGEM, Retangulo(10, 10, 40, 40), nome="Baixo")
    cima = Regiao(TipoRegiao.PRECO, Retangulo(15, 15, 20, 20), nome="Cima")
    lay = LayoutDef(100, 100, dpi=DPI,
                    paginas=[Pagina([Slot("s", [baixo, cima])])])
    c = CanvasView()
    c.resize(500, 400)
    c.show()
    QCoreApplication.processEvents()
    c.carregar(lay, DadosProduto("P", preco_por=Decimal("1")))
    QCoreApplication.processEvents()
    it_cima = next(i for i in c._itens if i.regiao is cima)
    it_baixo = next(i for i in c._itens if i.regiao is baixo)
    # ponto SOBRE a região de cima
    pt = it_cima.mapToScene(it_cima._w / 2, it_cima._h / 2)
    # o handler roda no item de BAIXO, mas passa o ponto → resolver devolve CIMA
    it_baixo.setSelected(True)
    it_baixo._selecao_por_clique(False, pt)
    assert c._primaria is cima          # a primária veio do resolver, não do self


def test_fix_grade_magnetica_desenha_linhas():
    """[NIT] a grade magnética agora APARECE: ligá-la muda o desenho do
    fundo do canvas (linhas nos múltiplos do passo) — provado por pixel."""
    _app()
    from PySide6.QtCore import QCoreApplication as QC
    from app.qt.canvas import CanvasView
    c = CanvasView()
    c.setAttribute(Qt.WidgetAttribute.WA_DontShowOnScreen, True)
    c.resize(500, 400)
    c.show()
    QC.processEvents()
    reg = Regiao(TipoRegiao.NOME, Retangulo(10, 10, 40, 10), nome="R")
    lay = LayoutDef(100, 100, dpi=DPI, paginas=[Pagina([Slot("s", [reg])])])
    c.carregar(lay, DadosProduto("P"))
    QC.processEvents()
    antes = c.grab().toImage()
    c.set_grade_magnetica(True)
    c.set_grade_passo(5.0)
    QC.processEvents()
    depois = c.grab().toImage()
    # o fundo mudou (as linhas da grade foram desenhadas)
    assert antes != depois


def test_fix_cadeado_consome_o_estado_da_arte():
    """[NIT] o cadeado não é casca inerte: destravar torna a arte de fundo
    SELECIONÁVEL (o estado é CONSUMIDO em _compor_fundo); travar tira."""
    _app()
    from PySide6.QtCore import QCoreApplication as QC
    from PySide6.QtWidgets import QGraphicsItem
    from app.qt.canvas import CanvasView
    c = CanvasView()
    c.resize(500, 400)
    c.show()
    QC.processEvents()
    reg = Regiao(TipoRegiao.NOME, Retangulo(10, 10, 40, 10), nome="R")
    lay = LayoutDef(100, 100, dpi=DPI, paginas=[Pagina([Slot("s", [reg])])])
    c.carregar(lay, DadosProduto("P"))
    QC.processEvents()
    flag = QGraphicsItem.GraphicsItemFlag.ItemIsSelectable
    # travada por padrão → arte NÃO selecionável
    assert not bool(c._bg.flags() & flag)
    c.set_arte_travada(False)                        # destrava (com aviso)
    assert bool(c._bg.flags() & flag)                # agora selecionável
    c.set_arte_travada(True)
    assert not bool(c._bg.flags() & flag)            # travou de novo

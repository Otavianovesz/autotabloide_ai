"""BLOCO C da ORDEM_F13 — o editor para de brigar (cada item com o
vermelho antes, L1; gesto pela bancada do A, conteúdo por pixel/byte)."""

import pytest
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication

from app.rendering.compositor import DadosProduto, compor_pagina
from app.rendering.model import (
    Ajuste,
    LayoutDef,
    Pagina,
    Regiao,
    Retangulo,
    Slot,
    TipoRegiao,
)
from app.rendering.units import mm_para_px
from app.tests import acervo
from app.tests.gestos import (
    arrastar_na_cena,
    botao_por_texto,
    botao_por_tooltip,
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


# ---------------------------------------------------------------------------
# C10 · R-03 — PREENCHER não vaza da célula (o caminho rápido recorta)
# ---------------------------------------------------------------------------


def test_c10_preencher_nao_vaza_da_celula_no_caminho_rapido(tmp_path):
    """C10 (R-03): `Ajuste.PREENCHER` amplia pelo lado MAIOR por definição —
    o excedente tem de ser RECORTADO para a região. Hoje o caminho rápido
    (1 imagem, sem forma/enquadramento — o PADRÃO) cola a imagem inteira
    centrada e a foto invade as células vizinhas. Prova por pixel FORA do
    rect."""
    from PIL import Image

    foto = tmp_path / "larga.png"
    Image.new("RGB", (400, 100), "#FF0000").save(foto)   # bem mais larga que alta

    dpi = 100
    reg = Regiao(TipoRegiao.IMAGEM, Retangulo(30, 30, 20, 20),
                 ajuste=Ajuste.PREENCHER)
    lay = LayoutDef(80, 80, dpi=dpi, paginas=[Pagina([Slot("s", [reg])])])
    img = compor_pagina(lay, lay.paginas[0],
                        {"s": DadosProduto("X", imagem_path=str(foto))})

    rgb = img.convert("RGB")
    y_meio = round(mm_para_px(40, dpi))                  # meio da região
    x_dentro = round(mm_para_px(40, dpi))
    x_fora_esq = round(mm_para_px(30, dpi)) - 8          # 8px à esquerda do rect
    x_fora_dir = round(mm_para_px(50, dpi)) + 8          # 8px à direita do rect
    assert rgb.getpixel((x_dentro, y_meio)) == (255, 0, 0)   # a foto está lá
    assert rgb.getpixel((x_fora_esq, y_meio)) == (255, 255, 255), (
        "o PREENCHER vazou para a ESQUERDA da célula (R-03)")
    assert rgb.getpixel((x_fora_dir, y_meio)) == (255, 255, 255), (
        "o PREENCHER vazou para a DIREITA da célula (R-03)")


# ---------------------------------------------------------------------------
# DEFINIÇÃO DE PRONTO do Bloco C — a sequência da GRAVAÇÃO, por gesto
# ---------------------------------------------------------------------------


def test_c_dod_sequencia_da_gravacao_tres_criacoes_independentes(
        raiz_tmp, tmp_path):
    """A definição de pronto do Bloco C, na letra: criar IMAGEM, criar
    TEXTO (nome), criar PREÇO pelos BOTÕES reais, arrastar CADA UMA — e
    provar por CONTEÚDO que as três são independentes. Era a sequência
    exata da gravação do dono (E-01/L-07: nasciam no mesmo retângulo,
    grudadas; arrastar uma levava as outras)."""
    from PIL import Image
    from PySide6.QtCore import QPointF

    from app.qt.editor import Editor
    _app()
    e = Editor()
    lay = LayoutDef(100, 100, dpi=100, paginas=[Pagina([])])
    e.carregar(lay, DadosProduto("x"))
    e.canvas.resize(400, 300)
    e.canvas.show()

    regs = {}
    for tooltip, tipo in (("Adicionar imagem", TipoRegiao.IMAGEM),
                          ("Adicionar nome do produto", TipoRegiao.NOME),
                          ("Adicionar preço", TipoRegiao.PRECO)):
        clicar(botao_por_tooltip(e.barra, tooltip))
        regs[tipo] = e.canvas.selecionada()
        assert regs[tipo] is not None and regs[tipo].tipo == tipo

    # três slots DIFERENTES, três retângulos DIFERENTES (nada grudado)
    slots = {t_: e.canvas._slot_de(r) for t_, r in regs.items()}
    assert len({id(s) for s in slots.values()}) == 3
    rects = {(r.rect.x_mm, r.rect.y_mm) for r in regs.values()}
    assert len(rects) == 3

    # arrastar CADA UMA — só ela se move. Na ordem topo→fundo do z (as
    # três nascem em cascata SOBREPOSTAS; o clique pega a de cima — como
    # o dono faria: tira a da frente primeiro)
    deltas = {TipoRegiao.IMAGEM: QPointF(-60, -60),
              TipoRegiao.NOME: QPointF(50, -30),
              TipoRegiao.PRECO: QPointF(-30, 55)}
    for tipo in (TipoRegiao.PRECO, TipoRegiao.NOME, TipoRegiao.IMAGEM):
        reg = regs[tipo]
        antes = {t2: (r2.rect.x_mm, r2.rect.y_mm)
                 for t2, r2 in regs.items() if t2 is not tipo}
        item = next(i for i in e.canvas._itens if i.regiao is reg)
        e.canvas._scene.clearSelection()
        centro = item.mapToScene(item._w / 2, item._h / 2)
        clicar_na_cena(e.canvas, centro)
        arrastar_na_cena(e.canvas, centro, centro + deltas[tipo])
        for t2, pos in antes.items():
            assert (regs[t2].rect.x_mm, regs[t2].rect.y_mm) == \
                pytest.approx(pos), (
                f"arrastar {tipo.value} MOVEU {t2.value} junto — grudadas")

    # por CONTEÚDO: a foto desenha no rect NOVO da IMAGEM (e só nele)
    foto = tmp_path / "p.png"
    Image.new("RGB", (60, 60), "#FF0000").save(foto)
    dados = {slots[TipoRegiao.IMAGEM].id:
             DadosProduto("Arroz", imagem_path=str(foto))}
    img = compor_pagina(lay, lay.paginas[0], dados).convert("RGB")
    ri = regs[TipoRegiao.IMAGEM].rect
    cx = round(mm_para_px(ri.x_mm + ri.larg_mm / 2, 100))
    cy = round(mm_para_px(ri.y_mm + ri.alt_mm / 2, 100))
    assert img.getpixel((cx, cy)) == (255, 0, 0), (
        "a foto não está no rect NOVO da imagem — o arrasto não valeu")
    rn = regs[TipoRegiao.NOME].rect
    nx = round(mm_para_px(rn.x_mm + rn.larg_mm / 2, 100))
    ny = round(mm_para_px(rn.y_mm + rn.alt_mm / 2, 100))
    assert img.getpixel((nx, ny)) != (255, 0, 0), (
        "a foto vazou no rect do NOME — não são independentes")


# ---------------------------------------------------------------------------
# C2 · trava #2 derrubada — clique seleciona SÓ a peça clicada
# ---------------------------------------------------------------------------


def _canvas_celula_dupla():
    """Uma célula com NOME+PREÇO (o 'trio' clássico) num canvas vivo."""
    from app.qt.canvas import CanvasView
    _app()
    lay = LayoutDef(100, 100, dpi=100, paginas=[Pagina([Slot("c", [
        Regiao(TipoRegiao.NOME, Retangulo(10, 10, 40, 12), nome="Nome"),
        Regiao(TipoRegiao.PRECO, Retangulo(10, 30, 40, 12), nome="Preço"),
    ])])])
    c = CanvasView()
    c.resize(400, 300)
    c.show()                # offscreen: visível para os filhos (chip, véu)
    c.carregar(lay, DadosProduto("x"))
    return c, lay


def test_c2_arrastar_uma_peca_move_so_ela():
    """Trava #2 (decisão do dono, 24/07): arrastar uma peça move SÓ ELA —
    o trio (RG-15) caiu. Hoje o PRESS acende a célula inteira e o arrasto
    leva as irmãs junto (o 'não consigo mexer só no preço' da gravação;
    no clique parado o Qt já colapsava no release — o trio mordia no
    ARRASTO)."""
    c, lay = _canvas_celula_dupla()
    nome, preco = lay.paginas[0].slots[0].regioes
    preco_antes = (preco.rect.x_mm, preco.rect.y_mm)
    item_nome = next(i for i in c._itens if i.regiao is nome)
    centro = item_nome.mapToScene(item_nome._w / 2, item_nome._h / 2)
    from PySide6.QtCore import QPointF
    # COND-6 (selo do C, §6): o alvo ORIGINAL, restaurado — o arrasto DESCE
    # em direção ao preço de propósito; antes do conserto, a margem de alça
    # do preço (não selecionado, acima no z) roubava o clique final
    arrastar_na_cena(c, centro, centro + QPointF(60, 45))

    assert (nome.rect.x_mm, nome.rect.y_mm) != (10.0, 10.0), (
        "o arrasto nem moveu a peça agarrada — gesto não chegou")
    assert (preco.rect.x_mm, preco.rect.y_mm) == pytest.approx(preco_antes), (
        "arrastar o NOME levou o PREÇO junto — o trio (RG-15) ainda está "
        "de pé (trava #2)")
    # e o clique parado continua selecionando só a peça (o painel a mostra)
    # — repescando o ITEM depois do commit (o canvas reconstrói as alças;
    # o wrapper antigo pode estar morto)
    item_nome2 = next(i for i in c._itens if i.regiao is nome)
    clicar_na_cena(c, item_nome2.mapToScene(item_nome2._w / 2,
                                            item_nome2._h / 2))
    assert c.selecionada() is nome


def test_cond6_alca_so_existe_em_regiao_selecionada():
    """COND-6 (selo do C, §6): as DUAS portas da alça têm de ser iguais —
    o hover (itens.py:391) já exigia seleção; o press (:417) não exigia
    NADA, então uma região NÃO selecionada capturava o resize se o clique
    caísse a ±TAM de um canto dela (sem aviso de cursor antes — o hover
    negava a alça que o press dava). Gesto: arrastar a partir do CANTO do
    preço, com ninguém selecionado — tem de virar seleção+movimento
    (tamanho INTACTO), nunca resize."""
    c, lay = _canvas_celula_dupla()
    nome, preco = lay.paginas[0].slots[0].regioes
    tamanho_antes = (preco.rect.larg_mm, preco.rect.alt_mm)
    item_preco = next(i for i in c._itens if i.regiao is preco)
    canto = item_preco.mapToScene(0.0, 0.0)
    from PySide6.QtCore import QPointF
    arrastar_na_cena(c, canto, canto + QPointF(40, 30))

    assert (preco.rect.larg_mm, preco.rect.alt_mm) == pytest.approx(
        tamanho_antes), (
        "arrastar o canto de uma região NÃO selecionada REDIMENSIONOU — "
        "o press dá a alça que o hover nega (itens.py:417 vs :391)")


def test_c2_selecionar_a_celula_inteira_e_gesto_explicito():
    """O substituto DELIBERADO do trio: a ação de menu 'Selecionar a
    célula inteira' acende todas as peças do slot — e aí mover move
    junto (o commit multi de sempre)."""
    c, lay = _canvas_celula_dupla()
    nome = lay.paginas[0].slots[0].regioes[0]
    item_nome = next(i for i in c._itens if i.regiao is nome)
    centro = item_nome.mapToScene(item_nome._w / 2, item_nome._h / 2)
    clicar_na_cena(c, centro)

    menu, acoes = item_nome.montar_menu_contexto()
    alvo = next((a for a in acoes
                 if "célula inteira" in a.text().lower()), None)
    assert alvo is not None, (
        "o menu não oferece 'Selecionar a célula inteira' — o gesto "
        "substituto do trio não existe")
    acoes[alvo]()
    selecionadas = {i.regiao.uid for i in c._itens if i.isSelected()}
    assert selecionadas == {r.uid for r in lay.paginas[0].slots[0].regioes}


# ---------------------------------------------------------------------------
# C4 · R-01 — alinhamento VERTICAL de texto (campo novo no modelo)
# ---------------------------------------------------------------------------


def _tinta_vertical(img, reg, dpi):
    """(folga_topo, folga_base) da tinta dentro do rect da região."""
    x0 = round(mm_para_px(reg.rect.x_mm, dpi))
    y0 = round(mm_para_px(reg.rect.y_mm, dpi))
    x1 = round(mm_para_px(reg.rect.x_mm + reg.rect.larg_mm, dpi))
    y1 = round(mm_para_px(reg.rect.y_mm + reg.rect.alt_mm, dpi))
    cinza = img.convert("L").crop((x0, y0, x1, y1))
    caixa = cinza.point(lambda p: 255 if p < 128 else 0).getbbox()
    assert caixa, "nenhum pixel de texto na região"
    return caixa[1], (y1 - y0) - caixa[3]


def test_c4_alinhamento_vertical_topo_centro_base_por_pixel(tmp_path):
    """C4 (R-01): o alinhamento vertical vira CAMPO do modelo
    (TOPO/CENTRO/BASE; padrão CENTRO = o comportamento de sempre,
    byte-idêntico). Prova por pixel nas três posições."""
    from app.rendering.model import AlinhamentoV

    fontes = tmp_path / "fontes"
    acervo.copiar_fontes_reais(fontes)
    dpi = 100

    def _compor(av):
        reg = Regiao(TipoRegiao.NOME, Retangulo(10, 10, 60, 40),
                     nome="Nome", tamanho_max_pt=10.0)
        reg.alinhamento_v = av
        lay = LayoutDef(80, 60, dpi=dpi, paginas=[Pagina([Slot("s", [reg])])])
        img = compor_pagina(lay, lay.paginas[0], {"s": DadosProduto("Ao")},
                            fontes_dir=fontes)
        return _tinta_vertical(img, reg, dpi)

    # a tinta nunca começa no pixel 0 da caixa da linha (ascent/entrelinha
    # do glifo) — a folga tolerada é ~metade de uma linha de 10pt, ordens
    # de grandeza abaixo do CENTRO (~70px nesta caixa)
    topo_t, base_t = _compor(AlinhamentoV.TOPO)
    assert topo_t <= 8, f"TOPO não colou no topo (folga {topo_t}px)"
    topo_c, base_c = _compor(AlinhamentoV.CENTRO)
    assert abs(topo_c - base_c) <= 40          # centrado (o padrão são)
    assert topo_c > 20
    topo_b, base_b = _compor(AlinhamentoV.BASE)
    assert base_b <= 8, f"BASE não colou na base (folga {base_b}px)"

    # serialização round-trip (layout antigo sem a chave cai em CENTRO)
    reg2 = Regiao(TipoRegiao.NOME, Retangulo(1, 1, 10, 10))
    d = reg2.to_dict()
    d.pop("alinhamento_v", None)               # simula layout ANTIGO
    assert Regiao.from_dict(d).alinhamento_v == AlinhamentoV.CENTRO


def test_c4_alinhamento_vertical_propaga_da_mestra():
    """C4: o campo novo entra no ATRIBUTOS_ESTILO — a mestra propaga."""
    from app.rendering.grade import ATRIBUTOS_ESTILO
    assert "alinhamento_v" in ATRIBUTOS_ESTILO


def test_c4_e_vc004_painel_tem_combo_vertical_e_campos_mm(raiz_tmp):
    """C4+VC-004 no PAINEL: o combo 'Alinhar (em pé)' muda o modelo, e os
    campos X/Y/L/A em mm EDITAM a região (o Transform que não existia —
    varredura ao vivo: 'não existe campo de Largura nem Altura')."""
    from app.qt.canvas import CanvasView
    from app.qt.painel_propriedades import PainelPropriedades
    from app.rendering.model import AlinhamentoV
    _app()
    lay = LayoutDef(100, 100, dpi=100, paginas=[Pagina([Slot("s", [
        Regiao(TipoRegiao.NOME, Retangulo(10, 10, 40, 12), nome="Nome",
               rotacao_graus=15.0)])])])
    c = CanvasView()
    c.resize(400, 300)
    c.carregar(lay, DadosProduto("x"))
    painel = PainelPropriedades(c)
    reg = lay.paginas[0].slots[0].regioes[0]
    painel.mostrar(reg)

    painel.alinha_v.setCurrentText("TOPO")
    assert reg.alinhamento_v == AlinhamentoV.TOPO

    assert painel.pos_l.value() == pytest.approx(40.0)   # espelha o modelo
    painel.pos_l.setValue(55.0)                          # edita ROTACIONADA
    painel.pos_a.setValue(20.0)
    painel.pos_x.setValue(12.0)
    assert reg.rect.larg_mm == pytest.approx(55.0)
    assert reg.rect.alt_mm == pytest.approx(20.0)
    assert reg.rect.x_mm == pytest.approx(12.0)


# ---------------------------------------------------------------------------
# VC-010/VC-014 · L-12 — a medida ao vivo LEGÍVEL + guia que diz onde está
# ---------------------------------------------------------------------------


def test_vc010_chip_de_medidas_aparece_no_arrasto_e_some_no_soltar():
    """VC-010 (L-12): o app já calculava X/Y/L/A em mm ao vivo e jogava
    num rótulo de 6px na barra. Agora o ARRASTO mostra um CHIP legível no
    canvas com as medidas — e ele some ao soltar."""
    from PySide6.QtCore import QPointF
    c, lay = _canvas_celula_dupla()
    nome = lay.paginas[0].slots[0].regioes[0]
    item = next(i for i in c._itens if i.regiao is nome)
    centro = item.mapToScene(item._w / 2, item._h / 2)
    clicar_na_cena(c, centro)

    from app.tests.gestos import arrastar
    vp = c.viewport()
    de = c.mapFromScene(centro)
    para = c.mapFromScene(centro + QPointF(40, 30))
    # o press+moves SEM release: o chip tem de estar visível DURANTE
    from PySide6.QtCore import QEvent, Qt as _Qt
    from PySide6.QtGui import QMouseEvent
    sem_mod = _Qt.KeyboardModifier.NoModifier
    ev = QMouseEvent(QEvent.Type.MouseButtonPress, QPointF(de),
                     QPointF(vp.mapToGlobal(de)), _Qt.MouseButton.LeftButton,
                     _Qt.MouseButton.LeftButton, sem_mod)
    QApplication.sendEvent(vp, ev)
    mv = QMouseEvent(QEvent.Type.MouseMove, QPointF(para),
                     QPointF(vp.mapToGlobal(para)), _Qt.MouseButton.NoButton,
                     _Qt.MouseButton.LeftButton, sem_mod)
    QApplication.sendEvent(vp, mv)
    chip = getattr(c, "_chip_medidas", None)
    assert chip is not None and chip.isVisible(), (
        "nenhum chip de medidas no arrasto — a medida segue no rótulo de "
        "6px (L-12/VC-010)")
    assert "mm" in chip.text() and "L" in chip.text()
    rel = QMouseEvent(QEvent.Type.MouseButtonRelease, QPointF(para),
                      QPointF(vp.mapToGlobal(para)), _Qt.MouseButton.LeftButton,
                      _Qt.MouseButton.NoButton, sem_mod)
    QApplication.sendEvent(vp, rel)
    assert not chip.isVisible(), "o chip não sumiu ao soltar"


def test_vc014_guia_de_snap_diz_a_posicao_em_mm():
    """VC-014: a guia de alinhamento carrega a MEDIDA (a posição dela em
    mm) desenhada na cena — hoje é só uma linha muda."""
    from PySide6.QtWidgets import QGraphicsSimpleTextItem
    c, _lay = _canvas_celula_dupla()
    coord = c.mm_para_cena(30.0, 0.0)[0]
    c.mostrar_guias([("x", coord)])
    textos = [i for i in c._scene.items()
              if isinstance(i, QGraphicsSimpleTextItem)]
    assert textos, "a guia de snap continua muda (sem medida) — VC-014"
    assert any("30" in t.text() and "mm" in t.text() for t in textos)
    c.mostrar_guias([])
    assert not [i for i in c._scene.items()
                if isinstance(i, QGraphicsSimpleTextItem)]


# ---------------------------------------------------------------------------
# C8 · E-06/E-07 — "Novo layout" sem lixo (área mínima/proporção + revisão)
# ---------------------------------------------------------------------------


def _arte_com_lixo(tmp_path):
    """3 caixas de preço legítimas + 1 risco fino + 1 respingo — os dois
    últimos NÃO são células."""
    from PIL import Image, ImageDraw
    im = Image.new("RGB", (800, 1000), "white")
    d = ImageDraw.Draw(im)
    vermelho = (200, 30, 30)
    for x in (60, 320, 580):                     # 3 caixas reais 120×70
        d.rectangle([x, 500, x + 120, 570], fill=vermelho)
    d.rectangle([100, 700, 300, 702], fill=vermelho)   # risco fino 200×3
    d.rectangle([600, 820, 630, 840], fill=vermelho)   # respingo 30×20
    arte = tmp_path / "arte_lixo.png"
    im.save(arte)
    return arte


def test_c8_detector_ignora_respingo_e_risco(tmp_path):
    """C8 (E-06): o detector por cor ganha ÁREA MÍNIMA e PROPORÇÃO — um
    risco fino e um respingo vermelhos não viram células. Hoje viram, e a
    grade nasce com lixo."""
    from app.rendering.grade import detectar_caixas_preco
    caixas = detectar_caixas_preco(str(_arte_com_lixo(tmp_path)))
    assert len(caixas) == 3, (
        f"o detector viu {len(caixas)} 'células' — o risco/respingo viraram "
        "caixa (E-06)")
    assert all(cw >= 100 and ch >= 50 for _x, _y, cw, ch in caixas)


def test_c8_novo_layout_pergunta_antes_de_salvar_a_grade(raiz_tmp, tmp_path,
                                                         monkeypatch):
    """C8 (E-07): o 'Novo layout' REVISA antes de salvar — o dono vê
    quantas células a detecção achou e decide (criar com a grade / criar
    sem e marcar no editor). Hoje salva DIRETO no banco e só avisa por
    toast. (Os pickers nativos de arquivo/nome são monkeypatchados — não
    são dirigíveis; a REVISÃO, que é o que se testa, responde pelo clique
    real do vigia.)"""
    from PySide6.QtWidgets import QFileDialog, QInputDialog

    from app.qt.telas.atelie import AtelieTela
    from app.rendering.persistencia import carregar_layout, listar_layouts
    from app.core.database import Database
    _app()
    arte = _arte_com_lixo(tmp_path)
    monkeypatch.setattr(QFileDialog, "getOpenFileName",
                        staticmethod(lambda *a, **k: (str(arte), "png")))
    monkeypatch.setattr(QInputDialog, "getText",
                        staticmethod(lambda *a, **k: ("Layout Novo", True)))
    monkeypatch.setattr(QInputDialog, "getItem",
                        staticmethod(lambda *a, **k: ("TABLOIDE", True)))
    tela = AtelieTela()
    try:
        with vigia_dialogo("Criar sem grade (marcar no editor)") as v:
            tela._novo()
        assert v.disparou, (
            "o Novo layout salvou DIRETO, sem revisão nenhuma (E-07)")
        assert v.faltou_botao is None, f"botões errados: {v.textos_botoes}"
        db = Database().init()
        try:
            with db.Session() as s:
                row = next(r for r in listar_layouts(s)
                           if r.nome == "Layout Novo")
                ldef = carregar_layout(s, row.id)
        finally:
            db.engine.dispose()
        # escolheu SEM grade: nenhuma célula detectada foi persistida (o
        # layout_de_arte traz só o slot-base vazio da página)
        assert not any(s.id.startswith("celula_")
                       for s in ldef.paginas[0].slots)
        assert not any(s.regioes for s in ldef.paginas[0].slots)
    finally:
        tela.close()


# ---------------------------------------------------------------------------
# C6 · E-03 — duplicar duplica a CÉLULA (quando é isso que está na mão)
# ---------------------------------------------------------------------------


def test_c6_menu_oferece_duplicar_a_celula_e_duplica_por_conteudo():
    """C6 (E-03): numa célula de 2+ peças o menu oferece 'Duplicar a
    célula' — nasce um slot NOVO com TODAS as peças copiadas (uids
    frescos, offset, geometria relativa preservada)."""
    c, lay = _canvas_celula_dupla()
    nome = lay.paginas[0].slots[0].regioes[0]
    item_nome = next(i for i in c._itens if i.regiao is nome)
    clicar_na_cena(c, item_nome.mapToScene(item_nome._w / 2,
                                           item_nome._h / 2))

    menu, acoes = item_nome.montar_menu_contexto()
    alvo = next((a for a in acoes if "duplicar a célula" in a.text().lower()),
                None)
    assert alvo is not None, "o menu não oferece 'Duplicar a célula' (E-03)"
    antes = len(lay.paginas[0].slots)
    uids_antes = {r.uid for s in lay.paginas[0].slots for r in s.regioes}
    acoes[alvo]()

    slots = lay.paginas[0].slots
    assert len(slots) == antes + 1, "não nasceu um slot novo"
    novo = slots[-1]
    assert len(novo.regioes) == 2, "a célula não veio INTEIRA"
    assert {r.tipo for r in novo.regioes} == {TipoRegiao.NOME,
                                              TipoRegiao.PRECO}
    assert all(r.uid not in uids_antes for r in novo.regioes)   # I1
    # geometria relativa preservada (o preço 20mm abaixo do nome)
    n2 = next(r for r in novo.regioes if r.tipo == TipoRegiao.NOME)
    p2 = next(r for r in novo.regioes if r.tipo == TipoRegiao.PRECO)
    assert (p2.rect.y_mm - n2.rect.y_mm) == pytest.approx(20.0)


# ---------------------------------------------------------------------------
# C7 · E-04 — carimbar nasce VISÍVEL e selecionado
# ---------------------------------------------------------------------------


def test_c7_carimbar_modelo_nasce_do_tamanho_sensato_e_selecionado():
    """C7 (E-04): carimbar sem caixa-alvo NÃO nasce do tamanho da PÁGINA
    inteira (o 'funciona e é invisível' da gravação) — nasce numa caixa
    central sensata e as regiões novas ficam SELECIONADAS (o dono vê o
    que acabou de carimbar)."""
    from app.rendering.modelos import modelo_vitrine
    c, lay = _canvas_celula_dupla()
    novas = c.carimbar_modelo(modelo_vitrine())
    assert novas, "o carimbo nem criou regiões"
    larg_pagina = lay.largura_mm
    caixa_larg = (max(r.rect.x_mm + r.rect.larg_mm for r in novas)
                  - min(r.rect.x_mm for r in novas))
    assert caixa_larg <= larg_pagina * 0.6, (
        f"o carimbo nasceu com {caixa_larg:.0f}mm de largura numa página "
        f"de {larg_pagina:.0f}mm — o tamanho da página inteira (E-04)")
    selecionadas = {i.regiao.uid for i in c._itens if i.isSelected()}
    assert selecionadas == {r.uid for r in novas}, (
        "as regiões carimbadas não ficaram selecionadas — carimbar segue "
        "invisível (E-04)")


# ---------------------------------------------------------------------------
# C11 · E-09/E-10 — selos com CONTROLE + prévia que os mostra (+COND-5)
# ---------------------------------------------------------------------------


def test_c11_exemplo_do_atelie_mostra_os_selos_por_conteudo(raiz_tmp,
                                                            tmp_path):
    """C11 (E-10): o produto de exemplo do Ateliê carrega mais18 e
    marca_propria — compor com ele DIFERE de compor sem flags (o dono
    fazia tudo certo e nenhum selo aparecia na prévia)."""
    from app.qt.telas.atelie import _EXEMPLO
    assert _EXEMPLO.mais18 and _EXEMPLO.marca_propria

    from PIL import Image
    foto = tmp_path / "p.png"
    Image.new("RGB", (100, 100), "#00AA00").save(foto)
    reg = Regiao(TipoRegiao.IMAGEM, Retangulo(10, 10, 50, 50))
    lay = LayoutDef(80, 80, dpi=100, paginas=[Pagina([Slot("s", [reg])])])
    com = compor_pagina(lay, lay.paginas[0], {"s": DadosProduto(
        "X", imagem_path=str(foto), mais18=True, marca_propria=True)})
    sem = compor_pagina(lay, lay.paginas[0], {"s": DadosProduto(
        "X", imagem_path=str(foto))})
    assert com.tobytes() != sem.tobytes(), "as flags não desenham selo nenhum"


def test_c11_painel_da_regiao_selo_tem_controle_de_canto(raiz_tmp):
    """C11 (E-09): a região SELO deixou de ser painel vazio — os combos de
    canto dos automáticos existem, gravam no GESTOR e valem na composição."""
    from app.core.selos import config_automaticos
    from app.qt.canvas import CanvasView
    from app.qt.painel_propriedades import PainelPropriedades
    _app()
    lay = LayoutDef(100, 100, dpi=100, paginas=[Pagina([Slot("s", [
        Regiao(TipoRegiao.SELO, Retangulo(10, 10, 20, 20), nome="Selo")])])])
    c = CanvasView()
    c.carregar(lay, DadosProduto("x"))
    painel = PainelPropriedades(c)
    reg = lay.paginas[0].slots[0].regioes[0]
    painel.mostrar(reg)
    assert painel.grp_selos.isVisibleTo(painel), (
        "a região SELO segue sem NENHUM controle no painel (E-09)")
    painel.canto_qualidade.setCurrentText("INFERIOR_DIREITO")
    assert config_automaticos()["QUALIDADE"]["canto"] == "INFERIOR_DIREITO", (
        "o combo não gravou no gestor")
    painel.canto_mais18.setCurrentText("INFERIOR_ESQUERDO")
    assert config_automaticos()["MAIS18"]["canto"] == "INFERIOR_ESQUERDO"


def test_cond5_marca_propria_flui_do_item_ate_as_receitas():
    """COND-5 (§5.6 do selo do B): o ItemMesa carrega marca_propria e as
    DUAS receitas (cartaz e tabloide) a entregam — o selo Qualidade tinha
    o mesmo furo que o +18 tinha."""
    from app.qt.telas import servico
    from app.qt.telas.servico import ItemMesa
    it = ItemMesa("Arroz Panelaço 5kg", "19,90", "VERDE",
                  "Arroz Panelaço 5kg", marca_propria=True)
    assert servico.dados_cartaz_de_item(it).marca_propria is True
    assert servico.dados_para_desenho(it).marca_propria is True
    # e o importar-do-banco a puxa do catálogo
    d = {"id": 1, "nome": "Arroz Panelaço 5kg", "nome_bruto": "ARROZ",
         "marca_propria": True}
    assert servico.item_do_catalogo(d).marca_propria is True


# ---------------------------------------------------------------------------
# C12 · E-11 — a mestra propaga o texto_fixo
# ---------------------------------------------------------------------------


def test_c12_mestra_propaga_texto_fixo_e_respeita_override():
    """C12 (E-11 — a "tag inteligente que não funciona"): editar o
    texto_fixo na MESTRA reflete nas células derivadas; célula com
    override próprio fica com o dela. Hoje texto_fixo está fora do
    ATRIBUTOS_ESTILO e a mestra não propaga."""
    from app.rendering.grade import propagar_mestre
    from app.rendering.model import PapelTexto

    m = Regiao(TipoRegiao.TEXTO_LEGAL, Retangulo(2, 2, 30, 8), nome="Tag",
               papel_texto=PapelTexto.LIVRE, texto_fixo="Oferta da semana")
    mestra = Slot("celula_0", [m], mestre=True, origem_mm=(5.0, 5.0))
    copia = Slot("celula_1", [], origem_mm=(45.0, 5.0))
    copia.ref_grupo = mestra.id
    pag = Pagina([mestra, copia])
    propagar_mestre(pag)
    derivada = next(r for r in copia.regioes)
    assert derivada.texto_fixo == "Oferta da semana", (
        "a propagação inicial nem levou o texto (E-11)")

    m.texto_fixo = "Quintou!"
    propagar_mestre(pag)
    assert derivada.texto_fixo == "Quintou!", (
        "editar o texto na MESTRA não refletiu na derivada (E-11)")

    derivada.overrides.add("texto_fixo")
    derivada.texto_fixo = "Só nesta célula"
    m.texto_fixo = "Outra semana"
    propagar_mestre(pag)
    assert derivada.texto_fixo == "Só nesta célula", (
        "o override da célula foi atropelado pela mestra")


def test_c10_conter_segue_byte_identico_na_regiao(tmp_path):
    """Regressão do C10: CONTER (min) nunca estoura a caixa — o conserto
    não pode tocar nesse caminho (nenhum pixel fora, foto dentro)."""
    from PIL import Image

    foto = tmp_path / "larga.png"
    Image.new("RGB", (400, 100), "#0000FF").save(foto)
    dpi = 100
    reg = Regiao(TipoRegiao.IMAGEM, Retangulo(30, 30, 20, 20),
                 ajuste=Ajuste.CONTER)
    lay = LayoutDef(80, 80, dpi=dpi, paginas=[Pagina([Slot("s", [reg])])])
    img = compor_pagina(lay, lay.paginas[0],
                        {"s": DadosProduto("X", imagem_path=str(foto))}).convert("RGB")
    y_meio = round(mm_para_px(40, dpi))
    assert img.getpixel((round(mm_para_px(40, dpi)), y_meio)) == (0, 0, 255)
    assert img.getpixel((round(mm_para_px(30, dpi)) - 8, y_meio)) == (255, 255, 255)

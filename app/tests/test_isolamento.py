"""
Modo de isolamento estilo Illustrator (pedido direto do dono, 21/07/2026)
=========================================================================
Duplo clique ENTRA no grupo/célula (pilha: grupo replicável → célula); dentro
da célula cada peça edita SOZINHA (o trio RG-15 não acende); o resto da
página fica sob um véu com buracos e não responde; Esc volta UM nível; duplo
clique fora sai/troca; Tab pula entre as peças; um chip visível diz onde o
dono está (I2). Escopo por id de SLOT (I1) — sobrevive à reconstrução.

Todos os testes conferem POR CONTEÚDO (flags, mm, path do véu, textos) —
reverter qualquer pedaço da implementação derruba o teste correspondente.
Inclui a prova dos DOIS bugs latentes achados no caminho (o arrasto do trio
não persistia as irmãs; o clique parado envenenava override 'rect' na cópia).
"""

from __future__ import annotations

import pytest
from PySide6.QtCore import QPointF, Qt
from PySide6.QtWidgets import QApplication, QGraphicsItem

from app.rendering.compositor import DadosProduto
from app.rendering.grade import propagar_mestre
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


def _canvas_com_grupo():
    """Mestra + cópia (grupo replicável) + célula solta de 2 peças."""
    from app.qt.canvas import CanvasView
    _app()
    regs = [Regiao(TipoRegiao.NOME, Retangulo(2, 2, 30, 8), nome="Nome"),
            Regiao(TipoRegiao.PRECO, Retangulo(2, 12, 30, 8), nome="Preço")]
    for r in regs:
        r.de_mestre = True
    lay = LayoutDef(200, 100, dpi=96, paginas=[Pagina([
        Slot("celula_m", regs, mestre=True, origem_mm=(0, 0)),
        Slot("celula_c", ref_grupo="celula_m", origem_mm=(60, 0)),
        Slot("solta", [Regiao(TipoRegiao.NOME, Retangulo(120, 2, 40, 8)),
                       Regiao(TipoRegiao.PRECO, Retangulo(120, 12, 40, 8))]),
    ])])
    propagar_mestre(lay.paginas[0])
    c = CanvasView()
    c.carregar(lay, DadosProduto("X"))
    return c, lay


def _item_de(canvas, reg):
    return next(it for it in canvas._itens if it.regiao is reg)


def test_duplo_clique_empilha_grupo_depois_celula():
    """O gesto do Illustrator: 1º duplo clique isola o GRUPO (mestre+cópias),
    o 2º isola a CÉLULA — por conteúdo do escopo (ids de slot, I1)."""
    c, lay = _canvas_com_grupo()
    reg_m = lay.paginas[0].slots[0].regioes[0]
    assert not c.em_isolamento()
    assert c.isolar_por_duplo_clique(reg_m)
    assert c._pilha_isolamento[-1]["nivel"] == "grupo"
    assert c.escopo_isolamento() == {"celula_m", "celula_c"}
    assert c.isolar_por_duplo_clique(reg_m)
    assert c._pilha_isolamento[-1]["nivel"] == "celula"
    assert c.escopo_isolamento() == {"celula_m"}
    assert c.celula_isolada(lay.paginas[0].slots[0])
    # célula SOLTA (sem grupo) com 2+ peças isola DIRETO na célula
    c.sair_isolamento(tudo=True)
    assert c.isolar_por_duplo_clique(lay.paginas[0].slots[2].regioes[0])
    assert c._pilha_isolamento[-1]["nivel"] == "celula"
    assert c.escopo_isolamento() == {"solta"}


def test_fora_do_escopo_fica_inerte_e_volta_ao_sair():
    """Fora do escopo: esmaecida, NÃO selecionável, NÃO móvel e SEM botão de
    mouse nenhum (a frota provou que a ALÇA de resize entrava pelo press
    direto e envenenava a cópia — o NoButton mata press/alça/menu no
    dispatch do Qt). Ao sair, tudo volta."""
    c, lay = _canvas_com_grupo()
    solta = lay.paginas[0].slots[2]
    it_fora = _item_de(c, solta.regioes[0])
    botoes_padrao = it_fora.acceptedMouseButtons()   # o default do Qt
    c.isolar_por_duplo_clique(lay.paginas[0].slots[0].regioes[0])
    flags = it_fora.flags()
    assert not flags & QGraphicsItem.GraphicsItemFlag.ItemIsSelectable
    assert not flags & QGraphicsItem.GraphicsItemFlag.ItemIsMovable
    assert it_fora.opacity() < 1.0
    assert it_fora.acceptedMouseButtons() == Qt.MouseButton.NoButton
    it_fora.setSelected(True)                    # o Qt ignora (flag off)
    assert not it_fora.isSelected()
    c.sair_isolamento(tudo=True)
    flags = it_fora.flags()
    assert flags & QGraphicsItem.GraphicsItemFlag.ItemIsSelectable
    assert flags & QGraphicsItem.GraphicsItemFlag.ItemIsMovable
    assert it_fora.opacity() == 1.0
    assert it_fora.acceptedMouseButtons() == botoes_padrao   # restaurado


def test_clique_na_celula_isolada_nao_acende_o_trio():
    """A cura da queixa: DENTRO da célula isolada o clique seleciona SÓ a
    peça (sem trio, sem oscilação) e o painel mostra ela (RG-55). O diag
    registra o caminho novo. Prova de mutação: sem a guarda no
    _selecao_por_clique, a irmã acende e o teste cai."""
    from app.qt.design import diag_selecao
    c, lay = _canvas_com_grupo()
    solta = lay.paginas[0].slots[2]
    nome, preco = solta.regioes
    c.isolar_por_duplo_clique(nome)              # isola a célula "solta"
    it_nome, it_preco = _item_de(c, nome), _item_de(c, preco)
    diag_selecao.ligar()
    try:
        c._scene.clearSelection()
        it_nome.setSelected(True)
        it_nome._selecao_por_clique(False, None)
        assert not it_preco.isSelected()         # a irmã NÃO acendeu
        assert it_nome.isSelected()
        assert c.selecionada() is nome           # o painel nunca órfão (RG-55)
        eventos = [e["evento"] for e in diag_selecao.registro()]
        assert "clique_isolado" in eventos
        assert "clique_grupo" not in eventos     # o caminho do trio não rodou
    finally:
        diag_selecao.desligar()
    # e o hover também não acende o trio dentro do isolamento
    it_nome._marcar_hover_grupo(True)
    assert not it_preco._hover_grupo


def test_fora_do_isolamento_o_trio_segue_valendo():
    """RG-15 intacto (decisão travada): SEM isolamento, o 1º clique segue
    acendendo o trio da célula — o modo novo não rouba o gesto antigo."""
    c, lay = _canvas_com_grupo()
    solta = lay.paginas[0].slots[2]
    nome, preco = solta.regioes
    it_nome, it_preco = _item_de(c, nome), _item_de(c, preco)
    c._scene.clearSelection()
    it_nome.setSelected(True)
    it_nome._selecao_por_clique(False, None)
    assert it_preco.isSelected()                 # o trio acendeu como sempre


def test_veu_cobre_o_resto_com_buraco_nas_pecas():
    """O véu existe só em isolamento, tem BURACO em cada peça do escopo e
    cobre o resto (conferido pelo path, por ponto). A cor segue o tema."""
    from PySide6.QtGui import QColor

    from app.qt.design import tokens as t
    c, lay = _canvas_com_grupo()
    assert c._veu_isolamento is None
    c.isolar_por_duplo_clique(lay.paginas[0].slots[2].regioes[0])
    veu = c._veu_isolamento
    assert veu is not None
    dentro = QPointF(*c.mm_para_cena(140, 6))    # miolo da peça "Nome"
    fora = QPointF(*c.mm_para_cena(30, 50))      # longe do escopo
    assert not veu.path().contains(dentro)       # buraco na peça
    assert veu.path().contains(fora)             # véu no resto
    assert veu.brush().color() == QColor(255, 255, 255, 150)  # tema claro
    assert veu.acceptedMouseButtons() == Qt.MouseButton.NoButton
    # peças SOBREPOSTAS do escopo (preço sobre a foto — o desenho comum):
    # a INTERSEÇÃO continua buraco (a frota provou que o OddEven re-pintava
    # o véu exatamente no miolo; a subtração é imune)
    solta = lay.paginas[0].slots[2]
    solta.regioes[1].rect = Retangulo(125, 5, 30, 8)   # cruza a peça Nome
    c._atualizar_veu_isolamento()
    intersecao = QPointF(*c.mm_para_cena(130, 7))      # dentro das DUAS
    assert not c._veu_isolamento.path().contains(intersecao)
    # tema escuro → véu escuro (a cor vem do tema, não hardcode do claro)
    t.ativar_tema("escuro")
    try:
        c._atualizar_veu_isolamento()
        assert c._veu_isolamento.brush().color() == QColor(0, 0, 0, 150)
    finally:
        t.ativar_tema("claro")
    c.sair_isolamento(tudo=True)
    assert c._veu_isolamento is None             # saiu: véu some


def test_chip_diz_o_nivel_e_o_botao_sair_sai():
    """I2: o modo NUNCA é silencioso — o chip nomeia o nível (grupo com N
    células / célula) e o botão Sair esvazia a pilha. `isHidden` (não
    `isVisible`): a frota provou que isVisible é False offscreen SEMPRE —
    o assert antigo passava até sem o hide()."""
    c, lay = _canvas_com_grupo()
    reg_m = lay.paginas[0].slots[0].regioes[0]
    c.isolar_por_duplo_clique(reg_m)
    chip = c._chip_isolamento
    assert chip is not None
    assert not chip.isHidden()                   # mostrado DENTRO do modo
    assert "GRUPO (2 células)" in chip._rotulo.text()
    c.isolar_por_duplo_clique(reg_m)
    assert "CÉLULA" in chip._rotulo.text()
    assert "Esc sai" in chip._rotulo.text()
    from PySide6.QtWidgets import QToolButton
    chip.findChild(QToolButton).click()          # o inverso a 1 clique (RG-56)
    assert not c.em_isolamento()
    assert chip.isHidden()                       # o hide() de verdade


def test_esc_volta_um_nivel_e_tab_circula_pelo_caminho_real():
    """Esc = pop de UM nível (grupo→célula→fora); Tab pula entre as peças da
    célula isolada E o foco FICA no canvas. O Tab viaja pelo PIPELINE REAL
    (QApplication.sendEvent → QWidget.event → focusNextPrevChild) num pai
    com outro widget focável — a frota provou que o keyPressEvent direto
    mascarava: no app real o Qt consumia o Tab para a troca de foco e a
    feature estava morta. Prova de mutação: remover o focusNextPrevChild
    novo faz o foco fugir para o vizinho e o teste cair."""
    from PySide6.QtGui import QKeyEvent
    from PySide6.QtWidgets import QApplication, QHBoxLayout, QLineEdit, QWidget
    c, lay = _canvas_com_grupo()
    pai = QWidget()
    h = QHBoxLayout(pai)
    h.addWidget(c)
    vizinho = QLineEdit()                        # o ladrão de foco do app real
    h.addWidget(vizinho)
    c.setFocus()
    reg_m = lay.paginas[0].slots[0].regioes[0]
    c.isolar_por_duplo_clique(reg_m)
    c.isolar_por_duplo_clique(reg_m)
    assert c.escopo_isolamento() == {"celula_m"}

    def _tecla(k):
        ev = QKeyEvent(QKeyEvent.Type.KeyPress, k,
                       Qt.KeyboardModifier.NoModifier)
        QApplication.sendEvent(c, ev)            # o caminho REAL do evento
        return ev

    # Tab circula: Nome → Preço → Nome (por conteúdo da selecionada)
    slot_m = lay.paginas[0].slots[0]
    _tecla(Qt.Key.Key_Tab)
    primeira = c.selecionada()
    assert primeira is not None                  # circulou (não fugiu o foco)
    _tecla(Qt.Key.Key_Tab)
    segunda = c.selecionada()
    assert primeira is not segunda
    assert all(any(r is reg for r in slot_m.regioes)
               for reg in (primeira, segunda))   # ambas são peças do slot
    _tecla(Qt.Key.Key_Tab)
    assert c.selecionada() is primeira           # deu a volta
    # Esc: célula → grupo → fora
    _tecla(Qt.Key.Key_Escape)
    assert c.escopo_isolamento() == {"celula_m", "celula_c"}
    _tecla(Qt.Key.Key_Escape)
    assert not c.em_isolamento()
    # FORA do isolamento o Tab volta a ser travessia de foco normal
    _tecla(Qt.Key.Key_Tab)
    assert c.selecionada() is None or not c.em_isolamento()
    pai.deleteLater()


def test_duplo_clique_fora_troca_ou_sai_pelo_view():
    """O duplo clique que caiu FORA do escopo: numa peça de outro slot,
    TROCA o isolamento; em área vazia, volta um nível — via o handler real
    do view (com QMouseEvent sintético)."""
    from PySide6.QtGui import QMouseEvent
    c, lay = _canvas_com_grupo()
    c.resize(400, 300)
    c.isolar_por_duplo_clique(lay.paginas[0].slots[2].regioes[0])
    assert c.escopo_isolamento() == {"solta"}

    def _dbl(ponto_mm):
        cena = QPointF(*c.mm_para_cena(*ponto_mm))
        local = QPointF(c.mapFromScene(cena))
        ev = QMouseEvent(QMouseEvent.Type.MouseButtonDblClick, local,
                         Qt.MouseButton.LeftButton, Qt.MouseButton.LeftButton,
                         Qt.KeyboardModifier.NoModifier)
        c.mouseDoubleClickEvent(ev)

    _dbl((10, 6))                                # peça da MESTRA (outro slot)
    assert c.em_isolamento()
    assert "celula_m" in c.escopo_isolamento()   # trocou de alvo
    _dbl((100, 90))                              # área vazia da página
    # estava no nível grupo → o duplo clique fora volta um nível (sai)
    assert not c.em_isolamento()


def test_isolamento_sobrevive_reconstrucao_e_cai_com_slot_removido():
    """O escopo é por ID (I1): a reconstrução dos itens (edição/undo/
    propagação) REAPLICA o modo; remover o slot isolado derruba o nível sem
    crash e sem prender o dono num escopo fantasma."""
    c, lay = _canvas_com_grupo()
    solta = lay.paginas[0].slots[2]
    c.isolar_por_duplo_clique(solta.regioes[0])
    c._construir_itens()                         # a reconstrução de sempre
    assert c.escopo_isolamento() == {"solta"}    # o modo sobreviveu
    it_fora = _item_de(c, lay.paginas[0].slots[0].regioes[0])
    assert not (it_fora.flags()
                & QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)
    lay.paginas[0].slots.remove(solta)           # o slot isolado SOME
    c._construir_itens()
    assert not c.em_isolamento()                 # caiu fora, sem crash
    it_m = _item_de(c, lay.paginas[0].slots[0].regioes[0])
    assert it_m.flags() & QGraphicsItem.GraphicsItemFlag.ItemIsSelectable


def test_trocar_de_pagina_sai_do_isolamento():
    """O isolamento é da página em tela — navegar derruba o modo (nada de
    escopo fantasma apontando para slots de outra página)."""
    c, lay = _canvas_com_grupo()
    lay.paginas.append(Pagina([Slot(
        "p2", [Regiao(TipoRegiao.NOME, Retangulo(5, 5, 30, 8))])]))
    c.isolar_por_duplo_clique(lay.paginas[0].slots[2].regioes[0])
    assert c.em_isolamento()
    c.ir_para_pagina(1)
    assert not c.em_isolamento()


def test_mover_peca_isolada_nao_arrasta_a_irma():
    """O objetivo final do dono, por CONTEÚDO (mm no modelo): dentro da
    célula isolada, mover uma peça move SÓ ela — a irmã fica onde estava."""
    c, lay = _canvas_com_grupo()
    solta = lay.paginas[0].slots[2]
    nome, preco = solta.regioes
    c.isolar_por_duplo_clique(nome)
    it_nome = _item_de(c, nome)
    antes_irma = (preco.rect.x_mm, preco.rect.y_mm)
    c._scene.clearSelection()
    it_nome.setSelected(True)
    dx = c.mm_para_cena(10, 0)[0]                # +10 mm em unidades de cena
    it_nome.setPos(it_nome.pos().x() + dx, it_nome.pos().y())
    c._commit_regiao(it_nome)
    assert nome.rect.x_mm == pytest.approx(130, abs=0.1)   # 120 + 10
    assert (preco.rect.x_mm, preco.rect.y_mm) == antes_irma


def test_bug_latente_arrasto_do_trio_persiste_as_irmas():
    """BUG LATENTE 1 (provado antes do conserto): o Qt move as irmãs do trio
    no arrasto, mas só a região AGARRADA era gravada no modelo — as irmãs
    "voltavam" na recomposição. Agora TODAS as selecionadas que saíram do
    lugar commitam juntas. Prova de mutação: reverter o _commit_regiao
    multi-item derruba este teste."""
    c, lay = _canvas_com_grupo()
    solta = lay.paginas[0].slots[2]
    nome, preco = solta.regioes
    it_nome, it_preco = _item_de(c, nome), _item_de(c, preco)
    c._scene.clearSelection()
    it_nome.setSelected(True)
    it_preco.setSelected(True)                   # o trio (2 peças) selecionado
    dx = c.mm_para_cena(15, 0)[0]
    for it in (it_nome, it_preco):               # o arrasto do Qt move ambos
        it.setPos(it.pos().x() + dx, it.pos().y())
    # a IRMÃ ainda ganha um snap DIVERGENTE (a frota provou: cada item snapa
    # sozinho e o commit multi gravaria a célula "desmontada") — o commit
    # deve usar o DELTA do agarrado, não a posição visual da irmã
    it_preco.setPos(it_preco.pos().x() + c.mm_para_cena(1.6, 0)[0],
                    it_preco.pos().y())
    c._commit_regiao(it_nome)                    # o release SÓ no agarrado
    assert nome.rect.x_mm == pytest.approx(135, abs=0.1)
    assert preco.rect.x_mm == pytest.approx(135, abs=0.1)  # MESMO delta (não
    # 136,6): o desenho interno do trio não desmonta no modelo


def test_bug_latente_clique_parado_nao_envenena_a_copia():
    """BUG LATENTE 2 (provado antes do conserto): um clique PARADO numa peça
    de CÓPIA gravava override 'rect' sem edição nenhuma — a cópia parava de
    seguir a mestra em silêncio (I2/I4). Agora o commit só grava o que
    MUDOU de verdade."""
    c, lay = _canvas_com_grupo()
    copia = lay.paginas[0].slots[1]
    reg_copia = copia.regioes[0]
    assert reg_copia.overrides == set()
    it = _item_de(c, reg_copia)
    c._commit_regiao(it)                         # o clique parado de hoje
    assert reg_copia.overrides == set()          # NADA foi envenenado
    # e o movimento REAL continua virando ajuste consciente (I4)
    dx = c.mm_para_cena(5, 0)[0]
    it.setPos(it.pos().x() + dx, it.pos().y())
    c._scene.clearSelection()
    it.setSelected(True)
    c._commit_regiao(it)
    assert "rect" in reg_copia.overrides         # ajuste de verdade marca


def test_menu_de_contexto_ensina_o_gesto_e_tem_o_inverso():
    """RG-56: fora do modo, o menu oferece "Entrar no grupo (isolar)"; dentro,
    "Sair do isolamento" — o inverso a UM clique, sempre."""
    c, lay = _canvas_com_grupo()
    it = _item_de(c, lay.paginas[0].slots[2].regioes[0])
    menu, acoes = it.montar_menu_contexto()
    textos = [a.text() for a in acoes]
    assert any("Entrar no grupo (isolar)" in t for t in textos)
    assert not any("Sair do isolamento" in t for t in textos)
    entrar = next(a for a in acoes if "Entrar no grupo" in a.text())
    acoes[entrar]()
    assert c.em_isolamento()
    menu2, acoes2 = it.montar_menu_contexto()
    textos2 = [a.text() for a in acoes2]
    assert any("Sair do isolamento" in t for t in textos2)
    sair = next(a for a in acoes2 if "Sair do isolamento" in a.text())
    acoes2[sair]()
    assert not c.em_isolamento()


def test_duplo_clique_pelo_item_desarma_o_colapso_rg15():
    """O handler real do item: o duplo clique entra no modo E desarma o
    colapso-no-release do RG-15 (os dois gestos não brigam)."""
    c, lay = _canvas_com_grupo()
    it = _item_de(c, lay.paginas[0].slots[2].regioes[0])
    it._colapsar_no_release = True               # o press do duplo armou

    class _Ev:
        def button(self):
            return Qt.MouseButton.LeftButton

        def modifiers(self):
            return Qt.KeyboardModifier.NoModifier

        def accept(self):
            self.aceito = True

    ev = _Ev()
    it.mouseDoubleClickEvent(ev)
    assert c.em_isolamento()
    assert it._colapsar_no_release is False      # desarmado
    assert getattr(ev, "aceito", False)


def test_troca_de_alvo_preserva_a_profundidade():
    """Achado da frota: no nível CÉLULA, duplo clique numa peça de OUTRA
    célula do MESMO grupo desce DIRETO na célula-alvo (pilha [grupo, alvo]) —
    não sobe pro grupo obrigando um segundo duplo clique."""
    c, lay = _canvas_com_grupo()
    reg_m = lay.paginas[0].slots[0].regioes[0]
    reg_c = lay.paginas[0].slots[1].regioes[0]
    c.isolar_por_duplo_clique(reg_m)             # grupo
    c.isolar_por_duplo_clique(reg_m)             # célula da mestra
    assert c.escopo_isolamento() == {"celula_m"}
    assert c.isolar_por_duplo_clique(reg_c)      # peça da CÓPIA (1 gesto)
    assert c.escopo_isolamento() == {"celula_c"}  # caiu direto na célula B
    assert [n["nivel"] for n in c._pilha_isolamento] == ["grupo", "celula"]


def test_nivel_grupo_degradado_vira_celula():
    """Achado da frota: grupo isolado que perde células até sobrar 1 é
    REBATIZADO para célula (o chip não mente o nível nem ensina gesto
    morto) e níveis duplicados na pilha somem."""
    c, lay = _canvas_com_grupo()
    reg_m = lay.paginas[0].slots[0].regioes[0]
    c.isolar_por_duplo_clique(reg_m)             # grupo (2 células)
    lay.paginas[0].slots.remove(lay.paginas[0].slots[1])   # a cópia some
    c._construir_itens()                         # a validação roda aqui
    assert c.em_isolamento()
    assert c._pilha_isolamento[-1]["nivel"] == "celula"    # rebatizado
    assert "CÉLULA" in c._chip_isolamento._rotulo.text()   # o chip fala certo
    assert c.celula_isolada(lay.paginas[0].slots[0])


def test_menu_nao_oferece_isolar_sem_efeito():
    """Achado da frota (I2): mestre SOLITÁRIO de 1 região não ganha a ação
    "Entrar no grupo (isolar)" — o menu só oferece o que o gesto FAZ."""
    from app.qt.canvas import CanvasView
    _app()
    lay = LayoutDef(200, 100, dpi=96, paginas=[Pagina([
        Slot("mestre_so", [Regiao(TipoRegiao.IMAGEM,
                                  Retangulo(5, 5, 40, 30))],
             mestre=True, origem_mm=(5, 5)),
    ])])
    c = CanvasView()
    c.carregar(lay, DadosProduto("X"))
    it = _item_de(c, lay.paginas[0].slots[0].regioes[0])
    _menu, acoes = it.montar_menu_contexto()
    assert not any("isolar" in a.text().lower() for a in acoes)


def test_alt_troca_suspensa_em_isolamento(monkeypatch):
    """Achado da frota: o Alt+arrastar (troca de conteúdo) fica SUSPENSO em
    isolamento — o 'resto que não responde' não pode responder ao Alt."""
    from PySide6.QtCore import QPointF as _P
    from PySide6.QtGui import QMouseEvent
    c, lay = _canvas_com_grupo()
    c.resize(400, 300)
    chamadas: list = []
    monkeypatch.setattr(c, "iniciar_troca_por_arrasto",
                        lambda p: chamadas.append(p) or True)

    def _alt_press():
        ev = QMouseEvent(QMouseEvent.Type.MouseButtonPress, _P(50, 50),
                         Qt.MouseButton.LeftButton, Qt.MouseButton.LeftButton,
                         Qt.KeyboardModifier.AltModifier)
        c.mousePressEvent(ev)

    c.isolar_por_duplo_clique(lay.paginas[0].slots[2].regioes[0])
    _alt_press()
    assert chamadas == []                        # em isolamento: nem tenta
    c.sair_isolamento(tudo=True)
    _alt_press()
    assert len(chamadas) == 1                    # fora do modo: gesto vivo

"""
ORDEM DE SERVIÇO F11.5 — testes de aceite (gates + itens)
=========================================================
Cada teste aqui cobre um item da `docs/ORDEM_SERVICO_F11_5.md`, SEMPRE por
CONTEÚDO (valor/pixel/uid) — reverter a correção correspondente faz o teste
falhar (mutation-proof). Os gates vêm primeiro.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest
from PySide6.QtWidgets import QApplication

from app.tests import seeds_portabilidade as seeds


@pytest.fixture()
def raiz_env(tmp_path, monkeypatch):
    root = seeds.raiz(tmp_path, "raiz")
    monkeypatch.setenv("AUTOTABLOIDE_ROOT", str(root.raiz))
    return root


def _app():
    return QApplication.instance() or QApplication([])


# ============================================================================
# GATE 1 — crash do badge de papel (F5 passo 6)
# ============================================================================

def test_gate1_badge_cobre_todos_os_papeis_do_enum():
    """TODO papel do ENUM (não só os do diálogo) devolve (rótulo, cor #hex,
    ícone existente). Na versão anterior, OBSERVACAO e DESCONTO estouravam
    KeyError NO PAINT — crash alcançável por ação normal do dono."""
    from app.qt.design.icones import nomes_disponiveis
    from app.qt.design.papel_texto_ui import ORDEM_PAPEIS, badge_de_papel
    from app.rendering.model import PapelTexto
    _app()
    icones = set(nomes_disponiveis())
    # o diálogo oferece OBSERVACAO — o caso exato do crash reportado
    assert PapelTexto.OBSERVACAO in ORDEM_PAPEIS
    for papel in PapelTexto:                     # o enum INTEIRO
        rotulo, cor, nome_icone = badge_de_papel(papel)
        assert rotulo and isinstance(rotulo, str), papel
        assert re.fullmatch(r"#[0-9A-Fa-f]{6}", cor), (papel, cor)
        assert nome_icone in icones, (papel, nome_icone)
    # cores DISTINTAS entre os papéis do diálogo (o badge diferencia à vista)
    cores = [badge_de_papel(p)[1] for p in ORDEM_PAPEIS]
    assert len(set(cores)) >= 4


# ============================================================================
# GATE 3 — pré-voo nos formatos sociais (F8, I2)
# ============================================================================

def _mesa_fake(itens):
    """Um duble mínimo do que o PublicarDialog usa da Mesa (QWidget porque o
    diálogo o usa como parent)."""
    from PySide6.QtWidgets import QWidget

    class _M(QWidget):
        def __init__(self):
            super().__init__()
            self._itens = itens

        @staticmethod
        def esta_aprovado():
            return False
    return _M()


def test_gate3_previa_social_avisa_item_incompleto(monkeypatch):
    """Item sem preço/foto AVISA antes de qualquer formato social sair (o
    fluxo antigo exportava calado). Por conteúdo: os avisos nomeiam o item e
    a falta; e com o pré-voo recusado, NADA é gerado (o seletor de pasta nem
    abre). Prova de mutação: remover a chamada do pré-voo em `_gerar` deixa
    `capturados` vazio e o teste falha."""
    from app.qt.telas.publicar_dialog import PublicarDialog
    from app.qt.telas.servico import ItemMesa
    _app()
    itens = [ItemMesa("Coca 2L", "7,99", "VERDE", "Coca 2L",
                      imagem=None),                      # sem foto
             ItemMesa("Sabão", None, "VERDE", "Sabão",
                      imagem=None)]                      # sem preço nem foto
    dlg = PublicarDialog(_mesa_fake(itens))

    # por conteúdo: o pré-voo nomeia item e falta, por modo
    avisos = dlg._avisos_pre_voo("carrossel", None)
    texto = " · ".join(avisos)
    assert "Coca 2L" in texto and "sem foto" in texto
    assert "Sabão" in texto and "sem preço" in texto
    # oferta/story: só o item do destaque entra no pré-voo
    so_um = dlg._avisos_pre_voo("oferta", itens[0])
    assert "Coca 2L" in " ".join(so_um) and "Sabão" not in " ".join(so_um)

    # o _gerar CHAMA o pré-voo e respeita a recusa (nada abre/gera)
    capturados: list[list[str]] = []

    def _confirmar(_pai, avisos, _verbo):
        capturados.append(list(avisos))
        return False                                     # o dono recusou

    monkeypatch.setattr("app.qt.telas.prevoo.confirmar_pre_voo", _confirmar)

    def _boom(*a, **k):                                  # pasta nunca é pedida
        raise AssertionError("exportou sem passar no pré-voo")

    monkeypatch.setattr(
        "app.qt.telas.publicar_dialog.QFileDialog.getExistingDirectory",
        _boom)
    dlg.rb_carrossel.setChecked(True)
    dlg._gerar()
    assert capturados and any("sem preço" in a for a in capturados[0])
    dlg.close()


# ============================================================================
# §2 — FASE 4 (editor I)
# ============================================================================

def test_f4_72_cadeado_aviso_coerente_com_o_gesto(raiz_env):
    """#72 (opção b, decisão travada arte=fundo): destravar torna a arte
    SELECIONÁVEL — nunca móvel — e o aviso DIZ isso (antes prometia proteção
    contra mover algo que nunca se moveu; texto×comportamento agora batem)."""
    from PySide6.QtWidgets import QGraphicsItem

    from app.qt.canvas import CanvasView
    _app()
    c = CanvasView()
    avisos: list[str] = []
    c._avisar_info = avisos.append           # captura o aviso real
    c.set_arte_travada(False)
    assert avisos and "SELECIONÁ" in avisos[0]        # o que o gesto FAZ
    assert "fixa" in avisos[0]                        # e o que NÃO faz
    assert "Illustrator" in avisos[0]                 # onde se reposiciona
    if c._bg is not None:
        flags = c._bg.flags()
        assert flags & QGraphicsItem.GraphicsItemFlag.ItemIsSelectable
        assert not (flags & QGraphicsItem.GraphicsItemFlag.ItemIsMovable)


def test_f4_77_cota_regiao_a_regiao_por_valor():
    """#77 (R-041): a cota região↔região por VALOR — dois rects conhecidos
    dão o mm exato; sobreposta dá 0; sem vizinha alinhada dá None."""
    from app.qt.itens import cota_entre_rects
    a = (0.0, 0.0, 30.0, 20.0)
    assert cota_entre_rects(a, [(40.0, 0.0, 30.0, 20.0)]) == 10.0   # ao lado
    assert cota_entre_rects(a, [(0.0, 35.0, 30.0, 20.0)]) == 15.0   # abaixo
    assert cota_entre_rects(a, [(10.0, 5.0, 30.0, 20.0)]) == 0.0    # sobrepõe
    assert cota_entre_rects(a, [(200.0, 200.0, 5.0, 5.0)]) is None  # longe
    # a MENOR vizinha vence
    assert cota_entre_rects(a, [(40.0, 0.0, 5.0, 5.0),
                                (33.0, 0.0, 5.0, 5.0)]) == 3.0


@pytest.mark.parametrize("escala", [125, 150])
def test_f4_50_editor_cabe_a_720p_nas_escalas(raiz_env, escala):
    """#50 (RG-54): o editor a 1280×720 nas escalas 125% e 150% — a janela
    não fica presa acima de 1280 (nada corta)."""
    from app.qt.design import tokens as t
    from app.qt.editor import Editor
    _app()
    t.ativar_escala(escala)
    try:
        e = Editor()
        e.resize(1280, 720)
        assert e.minimumSizeHint().width() <= 1280, (
            escala, e.minimumSizeHint().width())
        e.close()
    finally:
        t.ativar_escala(100)


# ============================================================================
# §3 — FASE 5 (editor II)
# ============================================================================

def test_f5_8_dica_gerada_declara_o_papel(raiz_env):
    """#8 (R-088): aplicar a dica gerada põe a região no papel DICA (badge) —
    não fica texto mudo em LIVRE. O teto já é lei em gerar_dica (GATE 2.1)."""
    from app.qt.canvas import CanvasView
    from app.qt.painel_propriedades import PainelPropriedades
    from app.rendering.model import PapelTexto, Regiao, Retangulo, TipoRegiao
    _app()
    canvas = CanvasView()
    p = PainelPropriedades(canvas)
    reg = Regiao(TipoRegiao.TEXTO_LEGAL, Retangulo(0, 0, 60, 12))
    assert reg.papel_texto == PapelTexto.LIVRE
    # sem canvas carregado, definir_papel_texto pode não existir p/ reg solto —
    # o método do painel tem que setar o papel mesmo assim
    try:
        p.aplicar_dica_gerada(reg, "Combina com pão quentinho.")
    except Exception:
        pass
    assert reg.texto_fixo == "Combina com pão quentinho."
    assert reg.papel_texto == PapelTexto.DICA


def test_f5_24_pill_padrao_muda_com_o_tema(raiz_env):
    """#24: o DEFAULT sugerido da pill segue o tema da UI (quem já ajustou
    nunca é tocado — só a sugestão inicial muda)."""
    from app.qt.design.papel_texto_ui import pill_padrao_do_tema
    from app.qt.design.tema import aplicar_tema
    app = _app()
    aplicar_tema(app, "claro")
    claro = pill_padrao_do_tema()
    aplicar_tema(app, "escuro")
    escuro = pill_padrao_do_tema()
    aplicar_tema(app, "claro")
    assert claro != escuro                      # o default MUDA com o tema
    assert claro == ("#000000", 128)            # o clássico no claro


def test_f5_42_truncamento_recua_por_palavra():
    """#42 (R-045): o corte com "…" recua por PALAVRA inteira — nunca
    "Choco…" no meio do termo (prova de mutação: o corte por caractere
    antigo deixaria um prefixo parcial)."""
    from app.rendering.text_fit import ajustar_texto
    from app.core.paths import SystemRoot
    fontes = SystemRoot().fontes / "Roboto-Regular.ttf"
    aj = ajustar_texto(
        "Chocolate Amargo Premiado Extraforte Colossal", str(fontes),
        180, 30, 14, 96, tamanho_min_pt=14)     # min=max: só resta truncar
    ultima = aj.linhas[-1]
    assert ultima.endswith("…")
    miolo = ultima[:-1].strip()
    palavras = set("Chocolate Amargo Premiado Extraforte Colossal".split())
    for p in miolo.split():
        assert p in palavras or p.endswith("-"), (p, ultima)


def test_f5_49_50_52_faixa_de_paginas(raiz_env):
    """#49/50/52: a faixa lateral existe no editor; reordenar pela faixa muda
    a ordem REAL das páginas (histórico registra — desfazer volta); o
    debounce colapsa rajadas numa recarga."""
    from PySide6.QtWidgets import QApplication

    from app.qt.editor import Editor
    from app.rendering.model import LayoutDef, Pagina, Slot
    from app.rendering.compositor import DadosProduto
    _app()
    e = Editor()
    lay = LayoutDef(100, 150, paginas=[Pagina([Slot("a", [])]),
                                       Pagina([Slot("b", [])]),
                                       Pagina([Slot("c", [])])])
    e.area.canvas.carregar(lay, DadosProduto("X"))
    faixa = e.faixa_paginas
    faixa._recarregar()
    assert faixa.lista.count() == 3
    # reordenar: página 0 → depois da 2 (rowsMoved com destino 3)
    ids_antes = [id(p) for p in lay.paginas]
    faixa._reordenada(None, 0, 0, None, 3)
    assert [id(p) for p in lay.paginas] == [ids_antes[1], ids_antes[2],
                                            ids_antes[0]]
    # debounce: 5 rajadas = 1 recarga agendada (timer ativo, dispara uma vez)
    disparos = []
    faixa._debounce.timeout.disconnect()
    faixa._debounce.timeout.connect(lambda: disparos.append(1))
    for _ in range(5):
        faixa.agendar_refresh()
    assert faixa._debounce.isActive()
    fim = __import__("time").monotonic() + 1.2
    while __import__("time").monotonic() < fim and not disparos:
        QApplication.processEvents()
    assert disparos == [1]                      # UMA recarga, não cinco
    e.close()


def test_f5_60_distribuir_respeita_guias_e_grade():
    """#60 (R-033): a distribuição snapa à GUIA do eixo (vence) e à GRADE
    (múltiplos do passo) — por posição exata."""
    from app.qt.alinhamento import distribuir_espacamento
    rects = [(0.0, 0.0, 10.0, 10.0), (23.0, 0.0, 10.0, 10.0),
             (61.0, 0.0, 10.0, 10.0)]
    # grade de 5: o 2º cai em 0+10+esp(4)=14 → snap 15; o 3º em 15+10+4=29 → 30
    pos = distribuir_espacamento(rects, "h", 4.0, grade_passo=5.0, limiar=2.0)
    assert [round(p[0], 1) for p in pos] == [0.0, 15.0, 30.0]
    # guia em 13.5 vence a grade (dentro do limiar)
    pos2 = distribuir_espacamento(rects, "h", 4.0, grade_passo=5.0,
                                  guias=(("x", 13.5),), limiar=2.0)
    assert round(pos2[1][0], 1) == 13.5
    # sem grade/guia: o clássico intacto (retrocompatível)
    pos3 = distribuir_espacamento(rects, "h", 4.0)
    assert [round(p[0], 1) for p in pos3] == [0.0, 14.0, 28.0]


# ============================================================================
# §4 — FASE 6 (Mesa I)
# ============================================================================

def _mesa_viva(raiz_env, itens):
    from PySide6.QtCore import Qt

    from app.qt.telas.mesa import MesaTela
    m = MesaTela()
    m.setAttribute(Qt.WidgetAttribute.WA_DontShowOnScreen, True)
    m.show()
    m._itens = itens
    m._recarregar_lista()
    return m


def test_f6_36_trocar_por_gesto_de_arrasto(raiz_env):
    """#36 (R-057): o DROP do gesto Alt+arrastar troca as duas células —
    por uid no mapa (I1), com undo (o trocar registra histórico)."""
    from PySide6.QtCore import QPointF

    from app.qt.telas.servico import ItemMesa
    from app.rendering.model import (
        Ajuste, LayoutDef, Pagina, Regiao, Retangulo, Slot, TipoRegiao)
    _app()
    a = ItemMesa("A", "1,00", "VERDE", "A")
    b = ItemMesa("B", "2,00", "VERDE", "B")
    m = _mesa_viva(raiz_env, [a, b])
    lay = LayoutDef(200, 100, dpi=96, paginas=[Pagina([
        Slot("c1", [Regiao(TipoRegiao.IMAGEM, Retangulo(5, 5, 80, 80),
                           ajuste=Ajuste.PREENCHER)]),
        Slot("c2", [Regiao(TipoRegiao.IMAGEM, Retangulo(110, 5, 80, 80),
                           ajuste=Ajuste.PREENCHER)]),
    ])])
    canvas = m.area.canvas
    from app.rendering.compositor import DadosProduto
    canvas.carregar(lay, DadosProduto(""))
    canvas.mapa.update({"c1": a.uid, "c2": b.uid})
    # o drop no centro da célula c2, arrastando a c1 → TROCA por uid
    from app.rendering.units import mm_para_px
    esc = canvas._esc if hasattr(canvas, "_esc") else 1.0
    px, py = mm_para_px(150, 96), mm_para_px(45, 96)
    ok = canvas.soltar_troca(QPointF(px, py), "c1")
    assert ok
    assert canvas.mapa["c1"] == b.uid and canvas.mapa["c2"] == a.uid
    # célula vazia NÃO troca (o gesto é entre ocupadas)
    canvas.mapa.pop("c1")
    assert not canvas.soltar_troca(QPointF(px, py), "c1")
    m.close()


def test_f6_68_planilha_grava_cadastro_por_produto_id(raiz_env):
    """#68: editar Nome/Categoria na planilha PERSISTE no banco pelo
    produto_id (I1) — relê o banco e confere; o preço da OFERTA continua do
    projeto (o preco_atual do banco não é tocado pelo 'por')."""
    from app.qt.telas import planilha as L
    from app.qt.telas.servico import ItemMesa
    pid = seeds.add_produto(raiz_env, "Arroz 5kg", "Camil", "24.90",
                            categoria="Mercearia")
    it = ItemMesa("ARROZ 5KG", "19,90", "VERDE", "Arroz 5kg", produto_id=pid)
    ok, aviso = L.aplicar_edicao(it, "Nome", "Arroz Premium 5kg")
    assert ok and aviso is None
    ok, aviso = L.aplicar_edicao(it, "Categoria", "Grãos")
    assert ok and aviso is None
    d = seeds.produto_por_chave(raiz_env, "Arroz Premium 5kg", "Camil")
    assert d is not None                          # o NOME persistiu no banco
    assert d["preco"] == "24.90"                  # o "de" do acervo intacto
    from app.core.database import Database
    from app.core.models import Produto
    db = Database(raiz_env).init()
    try:
        with db.Session() as s:
            p = s.get(Produto, pid)
            assert p.categoria.nome == "Grãos"    # a categoria persistiu
    finally:
        db.engine.dispose()


def test_f6_44_multiselecao_em_bloco(raiz_env):
    """#44: a estante aceita seleção MÚLTIPLA e excluir opera no bloco —
    por uid (os dois selecionados somem; o terceiro fica)."""
    from PySide6.QtWidgets import QAbstractItemView

    from app.qt.telas.servico import ItemMesa
    itens = [ItemMesa(n, "1,00", "VERDE", n) for n in ("A", "B", "C")]
    uid_c = itens[2].uid
    m = _mesa_viva(raiz_env, list(itens))
    assert (m.lista.selectionMode()
            == QAbstractItemView.SelectionMode.ExtendedSelection)
    m.lista.item(0).setSelected(True)
    m.lista.item(1).setSelected(True)
    m._excluir_item_selecionado()
    assert [it.uid for it in m._itens] == [uid_c]
    m.close()


def test_f6_74_adversarial_planilha_edita_so_o_uid_certo(raiz_env):
    """#74/#78 (I1): DOIS itens de MESMO nome na planilha — editar o preço da
    linha 0 muda SÓ aquele uid; o gêmeo de posição seguinte fica intacto.
    (Editar por posição trocaria os dois ou o errado.)"""
    from app.qt.telas.planilha_dialog import DialogoPlanilha
    from app.qt.telas import planilha as L
    from app.qt.telas.servico import ItemMesa
    g1 = ItemMesa("Arroz 5kg", "24,90", "VERDE", "Arroz 5kg")
    g2 = ItemMesa("Arroz 5kg", "24,90", "VERDE", "Arroz 5kg")
    m = _mesa_viva(raiz_env, [g1, g2])
    dlg = DialogoPlanilha(m, m)
    col = L.COLUNAS.index("Preço")
    dlg.tab.item(0, col).setText("9,99")          # dispara _celula_mudou
    assert g1.preco == "9,99"                     # só o uid da linha 0
    assert g2.preco == "24,90"                    # o gêmeo intacto (I1)
    dlg.close()
    m.close()


def test_f6_81_rascunho_com_caminhos_relativos(raiz_env, tmp_path):
    """#81 (I3): o snapshot do rascunho automático não guarda caminho
    absoluto de imagem da BIBLIOTECA (relativo à raiz); um caminho externo
    avulso (fora da biblioteca) é o único absoluto tolerado."""
    import json as _json

    from app.core import rascunho
    from app.qt.telas.servico import ItemMesa
    it = ItemMesa("A", "1,00", "VERDE", "A")
    it.imagem = str(raiz_env.biblioteca_imagens / "7" / "atual.png")
    arq = rascunho.salvar_rascunho({"itens": [it.to_dict()],
                                    "mapa": {}, "overrides": {}})
    dados = _json.loads(Path(arq).read_text(encoding="utf-8"))
    im = dados["itens"][0]["imagem"]
    assert str(raiz_env.raiz) not in im            # nada da raiz absoluta
    assert im.replace("\\", "/") == "7/atual.png"  # relativo à biblioteca
    # e a volta ABSOLUTIZA (o app usa o caminho cheio)
    de_volta = rascunho.carregar_rascunho()
    assert de_volta["itens"][0]["imagem"] == it.imagem


# ============================================================================
# §5 — FASE 7 (Mesa II / produção em massa)
# ============================================================================

def _conciliacao(itens):
    """ConciliacaoDialog com um ResultadoMesa duble (sem VERMELHO → sem fila
    de enriquecimento viva)."""
    from app.qt.telas.conciliacao_dialog import ConciliacaoDialog
    from app.qt.telas.servico import ResultadoMesa
    _app()
    return ConciliacaoDialog(ResultadoMesa(itens=itens), None)


def test_f7_19_22_aceitar_verdes_e_desfazer(raiz_env):
    """#19/#21/#22 (R-053): o botão reduz a lista AOS verdes (por uid), o
    contador diz "verdes aceitos/para revisar/novos", e o Desfazer devolve a
    lista INTEIRA — tudo por conteúdo."""
    from app.qt.telas.servico import ItemMesa
    v1 = ItemMesa("Arroz 5kg", "24,90", "VERDE", "Arroz 5kg")
    v2 = ItemMesa("Feijão 1kg", "7,99", "VERDE", "Feijão 1kg")
    am = ItemMesa("Óleo 900ml", "6,49", "AMARELO", "Óleo 900ml")
    dlg = _conciliacao([v1, am, v2])
    assert "1 para revisar" in dlg._resumo.text()
    assert dlg.btn_verdes.isVisible() or dlg.btn_verdes.isVisibleTo(dlg)
    dlg._aceitar_verdes()
    assert [it.uid for it in dlg.itens] == [v1.uid, v2.uid]   # SÓ os verdes
    assert "2 verdes aceitos" in dlg._resumo.text()
    assert "0 para revisar" in dlg._resumo.text()
    dlg._desfazer_verdes()
    assert [it.uid for it in dlg.itens] == [v1.uid, am.uid, v2.uid]
    dlg.done(0)


def test_f7_15_atalhos_movem_foco_e_estado(raiz_env):
    """#15: N pula ao PRÓXIMO amarelo (com volta ao início); R tira o item
    focado da lista (por uid)."""
    from app.qt.telas.servico import ItemMesa
    itens = [ItemMesa("V1", "1,00", "VERDE", "V1"),
             ItemMesa("A1", "2,00", "AMARELO", "A1"),
             ItemMesa("V2", "3,00", "VERDE", "V2"),
             ItemMesa("A2", "4,00", "AMARELO", "A2")]
    uid_a2 = itens[3].uid
    dlg = _conciliacao(list(itens))
    dlg.tabela.setCurrentCell(0, 0)
    dlg._ir_proximo_amarelo()
    assert dlg.tabela.currentRow() == 1               # foco no 1º amarelo
    dlg._ir_proximo_amarelo()
    assert dlg.tabela.currentRow() == 3               # no seguinte
    dlg._ir_proximo_amarelo()
    assert dlg.tabela.currentRow() == 1               # deu a volta
    dlg.tabela.setCurrentCell(3, 0)
    dlg._rejeitar_focado()                            # R no amarelo focado
    assert uid_a2 not in [it.uid for it in dlg.itens]
    assert len(dlg.itens) == 3
    dlg.done(0)


def test_f7_13_edicao_inline_reflete_no_item(raiz_env):
    """#13: editar Importado/Preço direto na tabela muda o ItemMesa (por
    linha da view = mesma lista); a coluna "No banco" segue TRAVADA."""
    from PySide6.QtCore import Qt as _Qt

    from app.qt.telas.servico import ItemMesa
    it = ItemMesa("ARROZ TP1 5KG", "24,90", "AMARELO", "Arroz 5kg")
    dlg = _conciliacao([it])
    dlg.tabela.item(0, 1).setText("Arroz tipo 1 5kg")
    assert it.descricao == "Arroz tipo 1 5kg"
    dlg.tabela.item(0, 2).setText("19,90")
    assert it.preco == "19,90"
    assert not (dlg.tabela.item(0, 3).flags() & _Qt.ItemFlag.ItemIsEditable)
    dlg.done(0)


def test_f7_44_45_diff_dialog_reflete_o_diff(raiz_env):
    """#44/#45 (R-062): o diálogo lista por CONTEÚDO quem entrou, quem saiu
    e o preço que subiu (com a seta) — direto do diff_edicoes real."""
    from PySide6.QtWidgets import QListWidget

    from app.qt.telas import servico
    from app.qt.telas.diff_dialog import DiffEdicaoDialog
    from app.qt.telas.servico import ItemMesa
    _app()
    ant = [ItemMesa("Arroz 5kg", "10,00", "VERDE", "Arroz 5kg", ean="111"),
           ItemMesa("Feijão 1kg", "5,00", "VERDE", "Feijão 1kg", ean="222")]
    atu = [ItemMesa("Arroz 5kg", "12,00", "VERDE", "Arroz 5kg", ean="111"),
           ItemMesa("Café 500g", "18,00", "VERDE", "Café 500g", ean="333")]
    diff = servico.diff_edicoes(atu, ant)
    dlg = DiffEdicaoDialog(diff)
    from PySide6.QtWidgets import QTabWidget
    tabs = dlg.findChild(QTabWidget)
    assert tabs.tabText(0) == "Preços (1)"
    assert tabs.tabText(1) == "Entraram (1)"
    assert tabs.tabText(2) == "Saíram (1)"
    lista_precos = tabs.widget(0).findChild(QListWidget)
    linha = lista_precos.item(0).text()
    assert "Arroz 5kg" in linha and "10,00 → 12,00" in linha
    assert "subiu" in linha
    assert tabs.widget(1).findChild(QListWidget).item(0).text() == "Café 500g"
    assert tabs.widget(2).findChild(QListWidget).item(0).text() == "Feijão 1kg"
    dlg.close()


def test_f7_48_50_checklist_pdf_com_conteudo(raiz_env, tmp_path):
    """#48/#50 (R-063): o conteúdo do checklist se prova no HTML EXATO que é
    impresso ("1 sem foto", a validade); a TINTA se prova rasterizando o PDF
    com o Ghostscript real (o Qt offscreen imprime texto como curvas — não há
    texto extraível; pixel escuro é a prova do papel)."""
    import subprocess

    from PIL import Image
    from pypdf import PdfReader

    from app.qt.telas import servico
    from app.qt.telas.servico import ItemMesa
    from app.rendering import cmyk
    _app()
    com_foto = ItemMesa("Arroz 5kg", "24,90", "VERDE", "Arroz 5kg")
    foto = tmp_path / "a.png"
    foto.write_bytes(seeds.png("#FF0000"))
    com_foto.imagem = str(foto)
    sem_foto = ItemMesa("Feijão 1kg", "7,99", "VERDE", "Feijão 1kg")
    itens = [com_foto, sem_foto]
    validade = "OFERTA VÁLIDA SOMENTE 21/07"
    # 1) o conteúdo — o HTML impresso carrega o estado REAL do projeto
    html = servico.html_do_checklist(itens, validade)
    assert "Checklist da edição" in html
    assert "1 sem foto" in html                        # o detalhe REAL
    assert "SOMENTE 21/07" in html                     # a validade impressa
    assert "✘" in html and "✔" in html                 # falha E ok marcados
    # 2) o papel — o PDF existe, tem 1 página e TINTA de verdade
    destino = tmp_path / "saida" / "checklist.pdf"
    saida = servico.exportar_checklist_pdf(itens, validade, destino)
    assert Path(saida).is_file()
    assert len(PdfReader(str(saida)).pages) == 1
    gs = cmyk.ghostscript_disponivel()
    assert gs, "a ordem afirma o Ghostscript no ambiente"
    png_out = tmp_path / "chk.png"
    subprocess.run([gs, "-dBATCH", "-dNOPAUSE", "-sDEVICE=png16m", "-r60",
                    f"-sOutputFile={png_out}", str(saida)],
                   check=True, capture_output=True)
    img = Image.open(png_out).convert("L")
    escuros = sum(img.histogram()[:128])
    assert escuros > 200                               # há texto impresso


def _mesa_com_grade(raiz_env, itens, n_slots=2):
    """Mesa viva com layout de `n_slots` células numa página."""
    from app.rendering.compositor import DadosProduto
    from app.rendering.model import (
        Ajuste, LayoutDef, Pagina, Regiao, Retangulo, Slot, TipoRegiao)
    m = _mesa_viva(raiz_env, itens)
    slots = [Slot(f"c{i}", [Regiao(TipoRegiao.IMAGEM,
                                   Retangulo(5 + i * 60, 5, 50, 50),
                                   ajuste=Ajuste.PREENCHER)],
                  origem_mm=(5 + i * 60, 5))
             for i in range(n_slots)]
    lay = LayoutDef(200, 100, dpi=96, paginas=[Pagina(slots)])
    m._layout = lay
    m.area.canvas.carregar(lay, DadosProduto(""))
    return m


def test_f7_23_25_destino_do_resto(raiz_env, monkeypatch):
    """#23/#25 (R-056): cada escolha faz o que promete — 'pagina' cria a
    página e ENCHE (todos os uids no mapa), 'fora' tira da estante (por uid,
    com a cópia p/ desfazer), 'fila' deixa tudo como está."""
    import app.qt.telas.prevoo as prevoo
    from app.qt.telas.servico import ItemMesa
    monkeypatch.setattr(prevoo, "confirmar_pre_voo",
                        lambda *a, **k: True)

    def _itens(n):
        return [ItemMesa(f"P{i}", "1,00", "VERDE", f"P{i}") for i in range(n)]

    # 'pagina': 4 itens em 2 células → nova página, TODOS mapeados
    itens = _itens(4)
    m = _mesa_com_grade(raiz_env, itens)
    monkeypatch.setattr(m, "_perguntar_destino_resto", lambda n: "pagina")
    m.encher_pagina()
    assert m.area.canvas.total_paginas() == 2
    assert set(m._mapa.values()) == {it.uid for it in itens}
    m.close()

    # 'fora': 3 itens em 2 células → o resto SAI da estante (por uid)
    itens = _itens(3)
    m = _mesa_com_grade(raiz_env, itens)
    monkeypatch.setattr(m, "_perguntar_destino_resto", lambda n: "fora")
    m.encher_pagina()
    assert m.area.canvas.total_paginas() == 1
    assert len(m._itens) == 2
    assert itens[2].uid not in [it.uid for it in m._itens]
    m.close()

    # 'fila': nada some, o resto segue visível na estante
    itens = _itens(3)
    m = _mesa_com_grade(raiz_env, itens)
    monkeypatch.setattr(m, "_perguntar_destino_resto", lambda n: "fila")
    m.encher_pagina()
    assert len(m._itens) == 3
    assert len(m._mapa) == 2
    m.close()


def test_f7_2_fila_multiarquivo_estado_por_arquivo(raiz_env, tmp_path):
    """#2 (R-049): o serviço narra o estado POR ARQUIVO (lendo → pronto/erro)
    e o widget da fila pinta cada linha — o erro fica visível (I2)."""
    from app.qt.telas import servico
    from app.qt.telas.fila_importacao import FilaImportacaoDialog
    _app()
    bom = tmp_path / "boa.txt"
    bom.write_text("Arroz 5kg | 24,90\n", encoding="utf-8")
    sumiu = str(tmp_path / "sumiu.txt")
    eventos: list[tuple[str, str]] = []
    servico.importar_varios([str(bom), sumiu], lambda _m: None,
                            progresso_cb=lambda n, e: eventos.append((n, e)))
    assert eventos == [("boa.txt", "lendo"), ("boa.txt", "pronto"),
                       ("sumiu.txt", "lendo"), ("sumiu.txt", "erro")]
    dlg = FilaImportacaoDialog(["boa.txt", "sumiu.txt"])
    assert dlg.estados == {"boa.txt": "na fila", "sumiu.txt": "na fila"}
    for n, e in eventos:
        dlg.atualizar(n, e)
    assert dlg.estados == {"boa.txt": "pronto", "sumiu.txt": "erro"}
    assert not dlg.tudo_pronto()                       # o erro impede o "tudo ok"
    assert "pronto" in dlg._chips["boa.txt"].text()
    dlg.close()


def test_f7_6_virgula_como_separador_na_colagem():
    """#6: a vírgula+ESPAÇO separa nome de preço na colagem — sem colidir com
    o decimal ("24,90" intacto) e sem atrapalhar os separadores fortes."""
    from app.qt.telas.colagem import _nome_preco
    assert _nome_preco("Arroz 5kg, 24,90") == ("Arroz 5kg", "24,90")
    assert _nome_preco("Feijão, tipo 1, 12,50") == ("Feijão, tipo 1", "12,50")
    assert _nome_preco("Queijo 24,90") == ("Queijo", "24,90")   # decimal puro
    assert _nome_preco("Arroz, tipo 1") == ("Arroz, tipo 1", None)
    assert _nome_preco("Coca 2L\t7,99") == ("Coca 2L", "7,99")  # tab ganha


def test_f7_39_frase_nova_do_dono_persiste(raiz_env):
    """#39: o combo soma as frases do DONO às padrão; adicionar grava na
    config (`frases.validade`) e a repetida é recusada."""
    from app.qt.telas import servico
    base = servico.frases_do_combo()
    assert "Imagens meramente ilustrativas" in base     # as padrão estão lá
    nova = "Oferta relâmpago do {evento}"
    assert servico.adicionar_frase_do_combo(nova) is True
    assert nova in servico.frases_do_combo()            # apareceu no combo
    assert servico.adicionar_frase_do_combo(nova) is False   # sem duplicar
    assert servico.frases_do_combo().count(nova) == 1


def test_f7_42_43_densidade_visual_na_barra(raiz_env):
    """#42/#43 (R-060): o medidor é PERMANENTE e muda de faixa por conteúdo —
    1/3 ocupado = "com respiro" (verde); 3/3 = "espremida" (vermelho)."""
    from app.qt.design import tokens as t
    from app.qt.telas.servico import ItemMesa
    itens = [ItemMesa(f"P{i}", "1,00", "VERDE", f"P{i}") for i in range(3)]
    m = _mesa_com_grade(raiz_env, itens, n_slots=3)
    m.area.canvas.mapa["c0"] = itens[0].uid
    m._atualizar_densidade()
    assert "33%" in m._densidade_lbl.text()
    assert "com respiro" in m._densidade_lbl.text()
    assert t.SUCESSO in m._densidade_lbl.styleSheet()
    m.area.canvas.mapa.update({"c1": itens[1].uid, "c2": itens[2].uid})
    m._atualizar_densidade()
    assert "100%" in m._densidade_lbl.text()
    assert "espremida" in m._densidade_lbl.text()
    assert t.PERIGO in m._densidade_lbl.styleSheet()
    m.close()


def test_f7_63_colagem_contra_glossario_nao_inventa_marca(raiz_env):
    """#63: a linha COLADA com marca desconhecida NUNCA vira verde nem ganha
    marca inventada — extrair_marca só devolve marca CONHECIDA (com fronteira
    de palavra) e a conciliação manda o desconhecido p/ vermelho/amarelo."""
    from app.core.aprendizado import extrair_marca
    from app.qt.telas import servico
    from app.qt.telas.colagem import linhas_para_tuplas, parse_colagem
    conhecidas = ["Coca-Cola", "Camil"]
    assert extrair_marca("Refri Zumba 2L", conhecidas) is None
    assert extrair_marca("Arroz Camil 5kg", conhecidas) == "Camil"
    assert extrair_marca("Camila fatiado 200g", conhecidas) is None  # fronteira
    seeds.add_produto(raiz_env, "Refrigerante 2L", "Coca-Cola", "9.90")
    linhas = parse_colagem("Refri Zumba 2L\t7,99")
    res = servico.conciliar_linhas(linhas_para_tuplas(linhas),
                                   lambda _m: None)
    assert len(res.itens) == 1
    it = res.itens[0]
    assert it.semaforo != "VERDE"                  # desconhecido nunca casa só
    if it.semaforo == "VERMELHO":                  # novo: o nome é o colado,
        assert it.nome == "Refri Zumba 2L"         # sem marca inventada


def test_f7_68_69_73_adversarial_itens_de_colagem_e_multiimport(
        raiz_env, tmp_path):
    """#68/#69/#73 (I1/I5): itens nascidos da COLAGEM e do MULTI-IMPORT no
    mesmo tabuleiro — reordenar a estante NÃO muda o que cada célula mostra,
    e a troca de células troca EXATAMENTE o par (nome+preço conferidos)."""
    from app.qt.telas import servico
    from app.qt.telas.colagem import linhas_para_tuplas, parse_colagem
    res_col = servico.conciliar_linhas(
        linhas_para_tuplas(parse_colagem("Colado A\t1,11\nColado B\t2,22")),
        lambda _m: None)
    txt = tmp_path / "multi.txt"
    txt.write_text("Importado C | 3,33\n", encoding="utf-8")
    res_multi, erros = servico.importar_varios([str(txt)], lambda _m: None)
    assert not erros
    itens = list(res_col.itens) + list(res_multi.itens)
    assert len(itens) == 3
    m = _mesa_com_grade(raiz_env, itens, n_slots=3)
    c = m.area.canvas
    c.mapa.update({"c0": itens[0].uid, "c1": itens[1].uid,
                   "c2": itens[2].uid})

    def _foto(sid):
        d = m._dados_por_slot()[sid]
        return (d.nome, str(d.preco_por))

    antes = {sid: _foto(sid) for sid in ("c0", "c1", "c2")}
    assert antes["c0"][0] == "Colado A" and antes["c2"][0] == "Importado C"
    m._itens.reverse()                             # #69: reordenar a estante
    m._recarregar_lista()
    assert {sid: _foto(sid) for sid in ("c0", "c1", "c2")} == antes
    assert c.trocar_conteudo_slots("c0", "c2")     # #73: troca controlada
    assert _foto("c0") == antes["c2"]              # trocou o par exato…
    assert _foto("c2") == antes["c0"]
    assert _foto("c1") == antes["c1"]              # …sem arrastar o vizinho
    m.close()


def test_f7_76_orfa_de_colagem_avisada(raiz_env):
    """#76 (I2): item de colagem apontando p/ célula REMOVIDA aparece no
    aviso de órfãos com o NOME — nunca some calado."""
    from app.qt.telas import servico
    from app.qt.telas.colagem import linhas_para_tuplas, parse_colagem
    res = servico.conciliar_linhas(
        linhas_para_tuplas(parse_colagem("Órfão Colado\t9,99")),
        lambda _m: None)
    m = _mesa_com_grade(raiz_env, list(res.itens), n_slots=1)
    m.area.canvas.mapa["celula_que_sumiu"] = res.itens[0].uid
    avisos = m._avisos_orfaos()
    assert any("Órfão Colado" in a for a in avisos)
    m.close()


def test_f7_80_i4_encher_pagina_em_grade_replicavel(raiz_env, monkeypatch):
    """#80 (I4): encher a página numa grade com célula-MESTRE não toca o
    vínculo ref_mestre (por uid) das cópias, e o conteúdo fica no slot certo
    mesmo com os slots reordenados na lista (identidade, não posição)."""
    import app.qt.telas.prevoo as prevoo
    from app.qt.telas.servico import ItemMesa
    from app.rendering.compositor import DadosProduto
    from app.rendering.grade import propagar_mestre
    from app.rendering.model import (
        LayoutDef, Pagina, Regiao, Retangulo, Slot, TipoRegiao)
    monkeypatch.setattr(prevoo, "confirmar_pre_voo", lambda *a, **k: True)
    regs = [Regiao(TipoRegiao.NOME, Retangulo(2, 2, 30, 8), nome="Nome")]
    for r in regs:
        r.de_mestre = True
    pag = Pagina([Slot("celula_m", regs, mestre=True, origem_mm=(0, 0)),
                  Slot("celula_a", origem_mm=(60, 0)),
                  Slot("celula_b", origem_mm=(120, 0))])
    lay = LayoutDef(200, 100, dpi=96, paginas=[pag])
    propagar_mestre(pag)
    uid_mestre = pag.slots[0].regioes[0].uid
    refs_antes = {s.id: [r.ref_mestre for r in s.regioes]
                  for s in pag.slots[1:]}
    assert all(refs_antes[sid] == [uid_mestre] for sid in refs_antes)
    itens = [ItemMesa(f"P{i}", "1,00", "VERDE", f"P{i}") for i in range(3)]
    m = _mesa_viva(raiz_env, itens)
    m._layout = lay
    m.area.canvas.carregar(lay, DadosProduto(""))
    m.encher_pagina()
    assert set(m._mapa.values()) == {it.uid for it in itens}
    # o vínculo mestra↔cópia sobreviveu ao encher (I4, por uid)
    for s in pag.slots[1:]:
        assert [r.ref_mestre for r in s.regioes] == [uid_mestre]
    # identidade, não posição: embaralhar a LISTA de slots não muda o dono
    por_slot = {sid: m._dados_por_slot()[sid].nome for sid in m._mapa}
    pag.slots.reverse()
    assert {sid: m._dados_por_slot()[sid].nome
            for sid in m._mapa} == por_slot
    m.close()


def test_f6_82_mestra_intacta_apos_reordenar_estante(raiz_env):
    """#82 (I4): reordenar a ESTANTE não toca o vínculo mestra↔cópia
    (ref_mestre por uid) — o layout fica byte-idêntico."""
    import json as _json

    from app.qt.telas.servico import ItemMesa
    from app.rendering.grade import propagar_mestre
    from app.rendering.model import (
        LayoutDef, Pagina, Regiao, Retangulo, Slot, TipoRegiao)
    _app()
    regs = [Regiao(TipoRegiao.NOME, Retangulo(2, 2, 30, 8), nome="Nome")]
    for r in regs:
        r.de_mestre = True
    lay = LayoutDef(200, 100, paginas=[Pagina([
        Slot("celula_0", regs, mestre=True, origem_mm=(0, 0)),
        Slot("celula_1", origem_mm=(60, 0)),
    ])])
    propagar_mestre(lay.paginas[0])
    antes = _json.dumps(lay.to_dict(), sort_keys=True)
    itens = [ItemMesa(n, "1,00", "VERDE", n) for n in ("A", "B", "C")]
    m = _mesa_viva(raiz_env, itens)
    from app.rendering.compositor import DadosProduto
    m.area.canvas.carregar(lay, DadosProduto(""))
    m._itens.reverse()                     # "reordena a estante"
    m._recarregar_lista()
    assert _json.dumps(lay.to_dict(), sort_keys=True) == antes
    m.close()


# ============================================================================
# §6 — FASE 8 (exportação e publicação)
# ============================================================================

def _png_solida(caminho, cor):
    from PIL import Image
    Image.new("RGB", (64, 64), cor).save(str(caminho))
    return str(caminho)


def test_f8_40_card_social_herda_a_arte(tmp_path):
    """#40: com `fundo`, o card social sai com a ARTE do projeto — pixel do
    canto vermelho; sem fundo, o padrão (não-vermelho). Vale para o card
    único E para o carrossel (o fundo atravessa o compor_carrossel)."""
    from app.rendering.compositor import DadosProduto
    from app.rendering.social import compor_carrossel, compor_social
    fundo = _png_solida(tmp_path / "arte.png", (255, 0, 0))
    d = DadosProduto("Produto X")
    com = compor_social("oferta_do_dia", d, fundo=fundo)
    sem = compor_social("oferta_do_dia", d)
    px_com = com.convert("RGB").getpixel((5, 5))
    px_sem = sem.convert("RGB").getpixel((5, 5))
    assert px_com[0] > 200 and px_com[1] < 60          # a arte chegou
    assert px_com != px_sem                            # e não é o padrão
    cards = compor_carrossel([d, d], fundo=fundo)
    assert len(cards) == 2
    for c in cards:
        px = c.convert("RGB").getpixel((5, 5))
        assert px[0] > 200 and px[1] < 60              # em TODOS os cards


def test_f8_31_oferta_do_dia_reusa_o_modelo_vitrine(monkeypatch):
    """#31 (R-044): o estilo da foto/nome do card Oferta do Dia vem DO modelo
    vitrine — mudar a vitrine muda o card (prova de reuso; valores copiados
    à mão não acompanhariam)."""
    from app.rendering import social as S
    from app.rendering.model import TipoRegiao
    lay = S.layout_social("oferta_do_dia")
    nome = next(r for r in lay.paginas[0].slots[0].regioes
                if r.tipo == TipoRegiao.NOME)
    assert nome.pill and nome.pill_cor == "#111111"    # o estilo da vitrine

    def _vitrine_mudada():
        from app.rendering.modelos import modelo_vitrine
        m = modelo_vitrine()
        for d in m.regioes:
            if d["tipo"] == "NOME":
                d["pill_cor"] = "#ABCDEF"
        return m

    monkeypatch.setattr(S, "modelo_vitrine", _vitrine_mudada)
    lay2 = S.layout_social("oferta_do_dia")
    nome2 = next(r for r in lay2.paginas[0].slots[0].regioes
                 if r.tipo == TipoRegiao.NOME)
    assert nome2.pill_cor == "#ABCDEF"                 # acompanhou o modelo


def _mesa_social(itens):
    """Duble da Mesa para o _compor_publicacao (sem widgets da Mesa real)."""
    from decimal import Decimal

    from PySide6.QtWidgets import QWidget

    from app.qt.telas.servico import preco_decimal
    from app.rendering.compositor import DadosProduto

    class _M(QWidget):
        _fundo = None

        def __init__(self):
            super().__init__()
            self._itens = itens

        @staticmethod
        def esta_aprovado():
            return False

        @staticmethod
        def _dados_de(it):
            return DadosProduto(it.nome,
                                preco_por=preco_decimal(it.preco)
                                or Decimal("1.00"),
                                imagem_path=it.imagem)

        @staticmethod
        def paginas_compostas():
            from PIL import Image
            return [Image.new("RGB", (200, 300), (250, 250, 250))]
    return _M()


def test_f8_35_selecao_e_ordem_do_carrossel(tmp_path):
    """#35: desmarcar tira o produto e arrastar muda a ordem — a SAÍDA
    reflete (nº de cards e a FOTO do 1º card, por pixel)."""
    from PySide6.QtCore import Qt

    from app.qt.telas.publicar_dialog import PublicarDialog, _compor_publicacao
    from app.qt.telas.servico import ItemMesa
    _app()
    foto_a = _png_solida(tmp_path / "a.png", (0, 200, 0))     # A = verde
    foto_c = _png_solida(tmp_path / "c.png", (200, 0, 0))     # C = vermelho
    a = ItemMesa("A", "1,00", "VERDE", "A", imagem=foto_a)
    b = ItemMesa("B", "2,00", "VERDE", "B")
    c = ItemMesa("C", "3,00", "VERDE", "C", imagem=foto_c)
    mesa = _mesa_social([a, b, c])
    dlg = PublicarDialog(mesa)
    dlg.lista_carrossel.item(1).setCheckState(Qt.CheckState.Unchecked)  # B sai
    li = dlg.lista_carrossel.takeItem(2)               # C vai pro topo
    dlg.lista_carrossel.insertItem(0, li)
    sel = dlg._itens_do_carrossel()
    assert [it.uid for it in sel] == [c.uid, a.uid]    # ordem + seleção por uid
    saida = tmp_path / "saida"
    saida.mkdir()
    gerados, _aviso, _p = _compor_publicacao(
        mesa, "carrossel", saida, False, None, sel, lambda _m: None)
    assert len(gerados) == 2                           # B ficou fora
    from PIL import Image
    im1 = Image.open(gerados[0]).convert("RGB")
    px = im1.getpixel((im1.width // 2, int(im1.height * 0.30)))
    assert px[0] > 120 and px[0] > px[1] + 60          # o 1º card é o C (foto)
    dlg.close()


def test_f8_7_faixa_e_story_mp4_pelo_caminho_da_ui(tmp_path):
    """#7/#37 (R-145/R-139): o modo "faixa" da UI gera o banner 1920×1080 e o
    Story com MP4 ligado gera PNG + vídeo animado — pelo MESMO miolo que o
    botão usa."""
    from app.qt.telas.publicar_dialog import PublicarDialog, _compor_publicacao
    from app.qt.telas.servico import ItemMesa
    from app.rendering.video import ffmpeg_disponivel
    _app()
    it = ItemMesa("Herói", "9,99", "VERDE", "Herói")
    mesa = _mesa_social([it])
    dlg = PublicarDialog(mesa)
    dlg.rb_faixa.setChecked(True)
    assert dlg._modo() == "faixa"                      # o radio mapeia o modo
    saida = tmp_path / "s1"
    saida.mkdir()
    gerados, _a, _p = _compor_publicacao(
        mesa, "faixa", saida, True, it, [it], lambda _m: None)
    from PIL import Image
    banner = Image.open(gerados[0])
    assert (banner.width, banner.height) == (1920, 1080)
    # Story + MP4 (a ordem afirma o ffmpeg no ambiente)
    assert ffmpeg_disponivel(), "a ordem afirma o ffmpeg no ambiente"
    saida2 = tmp_path / "s2"
    saida2.mkdir()
    gerados2, aviso2, _p2 = _compor_publicacao(
        mesa, "story", saida2, True, it, [it], lambda _m: None,
        story_mp4=True)
    assert aviso2 is None
    assert [Path(g).name for g in gerados2] == ["story.png", "story.mp4"]
    assert Path(gerados2[1]).stat().st_size > 1000
    dlg.close()


def test_f8_94_85_limitacao_visivel_e_abrir_com(tmp_path, monkeypatch):
    """#94/#85: a LIMITAÇÃO honesta do SO aparece na UI (label + tooltip) e o
    "Abrir com…" acorda após gerar, apontando para o arquivo gerado."""
    from app.qt.telas import compartilhar
    from app.qt.telas.publicar_dialog import PublicarDialog
    from app.qt.telas.servico import ItemMesa
    _app()
    mesa = _mesa_social([ItemMesa("X", "1,00", "VERDE", "X")])
    dlg = PublicarDialog(mesa)
    assert dlg._lbl_limitacao.text() == compartilhar.LIMITACAO_SO
    assert dlg.btn_abrir_com.toolTip() == compartilhar.LIMITACAO_SO
    assert not dlg.btn_abrir_com.isEnabled()
    monkeypatch.setattr(compartilhar, "copiar_imagem", lambda _c: True)
    monkeypatch.setattr(compartilhar, "abrir_pasta", lambda _c: True)
    arq = _png_solida(tmp_path / "peca.png", (0, 0, 255))
    dlg._pronto(([arq], None, str(tmp_path)))
    assert dlg.btn_abrir_com.isEnabled()
    abertos: list[str] = []
    monkeypatch.setattr(compartilhar, "abrir_com",
                        lambda c: abertos.append(str(c)) or True)
    dlg._abrir_com()
    assert abertos == [arq]                            # abre O arquivo gerado
    dlg.close()


def test_f8_5_perfis_editaveis_persistem(raiz_env):
    """#5 (R-065): editar um perfil na tela PERSISTE na Config (relido do
    banco); duplicar cria a cópia; número inválido avisa e NÃO salva (I2)."""
    from app.qt.telas.perfis_dialog import PerfisDialog
    from app.rendering.perfis import perfis_configurados
    _app()
    dlg = PerfisDialog()
    assert dlg.tab.rowCount() == 3                     # os padrões de fábrica
    dlg.tab.item(0, 0).setText("Zap do mercado")
    dlg.tab.item(0, 6).setText("70")
    dlg._salvar()
    lidos = perfis_configurados()
    assert lidos[0].nome == "Zap do mercado"           # relido do banco
    assert lidos[0].qualidade == 70
    dlg2 = PerfisDialog()
    assert dlg2.tab.rowCount() == 3
    assert dlg2.tab.item(0, 0).text() == "Zap do mercado"
    dlg2.tab.setCurrentCell(0, 0)
    dlg2._duplicar()
    assert dlg2.tab.rowCount() == 4
    assert "cópia" in dlg2.tab.item(3, 0).text()
    dlg2.tab.item(1, 5).setText("trezentos")           # DPI inválido
    assert dlg2._coletar() is None                     # não salva torto
    assert "não é um número" in dlg2._aviso.text()     # e avisa (I2)
    dlg2.close()


def test_f8_52_fade_e_duracao_por_pagina():
    """#52: `frames_do_slideshow` honra a duração (N frames/página) e o fade
    injeta frames de MISTURA entre páginas — por pixel."""
    from PIL import Image

    from app.rendering.video import frames_do_slideshow
    r = Image.new("RGB", (32, 32), (255, 0, 0))
    g = Image.new("RGB", (32, 32), (0, 255, 0))
    secos = frames_do_slideshow([r, g], seg_por_pagina=2 / 24, fps=24,
                                fade_s=0.0)
    assert len(secos) == 4                             # 2 frames por página
    com_fade = frames_do_slideshow([r, g], seg_por_pagina=2 / 24, fps=24,
                                   fade_s=2 / 24)
    assert len(com_fade) == 6                          # +2 frames de blend
    px0 = com_fade[0].getpixel((16, 16))
    meio = com_fade[2].getpixel((16, 16))              # 1º frame do fade
    fim = com_fade[-1].getpixel((16, 16))
    assert px0 == (255, 0, 0) and fim == (0, 255, 0)
    assert 40 < meio[0] < 220 and 40 < meio[1] < 220   # mistura de verdade


def test_f8_49_50_pulso_isolado_do_preco():
    """#49/#50: com `pulso_rect`, SÓ o preço pulsa — no meio da animação o
    vermelho vaza para fora do rect (zoom local), e um canto LONGE fica
    intacto em todos os frames."""
    from PIL import Image

    from app.rendering.video import frames_do_story
    img = Image.new("RGB", (200, 400), (255, 255, 255))
    for x in range(50, 150):
        for y in range(300, 350):
            img.putpixel((x, y), (200, 0, 0))          # o "preço"
    frames = frames_do_story(img, 8, pulso_rect=(50, 300, 100, 50))
    assert len(frames) == 8
    acima = (100, 299)                                 # 1 px acima do rect
    assert frames[0].getpixel(acima)[0] > 240          # parado no frame 0
    pico = frames[4].getpixel(acima)                   # z máximo (1.06) no meio
    assert pico[0] > 150 and pico[1] < 100             # o preço CRESCEU
    for fr in frames:
        assert fr.getpixel((10, 10)) == (255, 255, 255)  # o resto imóvel


def test_f8_32_preseleciona_o_item_da_mesa(raiz_env):
    """#32: o item selecionado na ESTANTE da Mesa já vem escolhido no combo
    do destaque (por uid)."""
    from app.qt.telas.publicar_dialog import PublicarDialog
    from app.qt.telas.servico import ItemMesa
    itens = [ItemMesa(n, "1,00", "VERDE", n) for n in ("A", "B", "C")]
    m = _mesa_viva(raiz_env, list(itens))
    m.lista.setCurrentRow(1)
    dlg = PublicarDialog(m)
    assert dlg.combo_item.currentData() == itens[1].uid
    dlg.close()
    m.close()


# ============================================================================
# §7 — FASE 9 (conteúdo & IA II)
# ============================================================================

def test_f9_27_28_avaliador_de_foto(tmp_path):
    """#27/#28 (R-085): a nota sai do CONTEÚDO — xadrez grande e nítido é
    "boa"; minúscula é "ruim" com o motivo e a sugestão de upscale; lisa
    (variância zero) acusa borrada; alfa marca packshot."""
    from PIL import Image

    from app.images.avaliador import avaliar_foto, variancia_laplaciano
    xadrez = Image.new("L", (800, 800))
    for x in range(800):
        for y in range(0, 800, 8):
            if (x // 8) % 2 == (y // 8) % 2:
                for k in range(8):
                    xadrez.putpixel((x, min(y + k, 799)), 255)
    p_boa = tmp_path / "boa.png"
    xadrez.convert("RGB").save(p_boa)
    av = avaliar_foto(p_boa)
    assert av.nota == "boa" and av.nitidez > 25

    p_mini = tmp_path / "mini.png"
    xadrez.resize((100, 100)).convert("RGB").save(p_mini)
    av2 = avaliar_foto(p_mini)
    assert av2.nota == "ruim"
    assert any("pequena" in m for m in av2.motivos)
    assert av2.sugere_upscale                      # o motivo liga o upscale

    p_lisa = tmp_path / "lisa.png"
    Image.new("RGB", (800, 800), (200, 200, 200)).save(p_lisa)
    av3 = avaliar_foto(p_lisa)
    assert any("borrada" in m for m in av3.motivos)
    assert variancia_laplaciano(Image.open(p_lisa)) < 8

    p_alfa = tmp_path / "alfa.png"
    Image.new("RGBA", (800, 800), (0, 0, 0, 0)).paste(  # noqa — só o modo
        xadrez.convert("RGBA"))
    xadrez.convert("RGBA").save(p_alfa)
    assert avaliar_foto(p_alfa).tem_alfa


def test_f9_50_51_variacoes_por_marca_e_tipo():
    """#50/#51 (R-082): dois sabores da MESMA marca conhecida viram sugestão;
    outra marca fica fora; sem marca conhecida NUNCA há sugestão (não
    inventa)."""
    from app.core.aprendizado import sugerir_variacoes
    from app.qt.telas.servico import ItemMesa
    dan_a = ItemMesa("x", "1,00", "VERDE", "Iogurte Danone Morango 170g")
    dan_b = ItemMesa("x", "1,00", "VERDE", "Iogurte Danone Coco 170g")
    vig = ItemMesa("x", "1,00", "VERDE", "Iogurte Vigor Morango 170g")
    arroz = ItemMesa("x", "1,00", "VERDE", "Arroz Danone 5kg")  # tipo difere
    grupos = sugerir_variacoes([dan_a, vig, dan_b, arroz],
                               ["Danone", "Vigor"])
    assert len(grupos) == 1
    assert {it.uid for it in grupos[0]} == {dan_a.uid, dan_b.uid}
    assert sugerir_variacoes([dan_a, dan_b], []) == []   # sem marca → nada


def test_f9_51_agrupar_variacoes_vira_multi(raiz_env, tmp_path):
    """#51: agrupar funde no PRIMEIRO (por uid): as fotos viram a lista multi
    (F7.1) e os demais saem da estante e do mapa."""
    from app.qt.telas.servico import ItemMesa
    fa = _png_solida(tmp_path / "a.png", (255, 0, 0))
    fb = _png_solida(tmp_path / "b.png", (0, 255, 0))
    a = ItemMesa("x", "1,00", "VERDE", "Iogurte Danone Morango", imagem=fa)
    b = ItemMesa("x", "1,00", "VERDE", "Iogurte Danone Coco", imagem=fb)
    c = ItemMesa("x", "1,00", "VERDE", "Arroz 5kg")
    m = _mesa_viva(raiz_env, [a, b, c])
    m.area.canvas.mapa["c9"] = b.uid
    m._agrupar_variacoes([a, b])
    assert a.imagens == [fa, fb]                   # o leque multi, na ordem
    assert [it.uid for it in m._itens] == [a.uid, c.uid]
    assert "c9" not in m._mapa                     # o mapa não aponta p/ fantasma
    m.close()


def test_f9_47_81_sinonimo_do_dono_persiste_e_aplica(raiz_env):
    """#47/#81 (R-086): o grupo que o dono acrescenta (Config) entra na
    conciliação — "Sacole" casa o produto "Geladinho" do banco (canonizado
    no fuzzy). Reverter a ligação no Conciliador quebra este teste."""
    from app.core.aprendizado import grupos_com_extras
    from app.core.database import Database
    from app.core.repositories import ConfigRepositorio
    from app.qt.telas import servico
    seeds.add_produto(raiz_env, "Geladinho de Coco", None, "2.50")
    db = Database(raiz_env).init()
    try:
        with db.Session() as s:
            ConfigRepositorio(s).set("sinonimos.regionais",
                                     [["geladinho", "sacole"]])
            s.commit()
    finally:
        db.engine.dispose()
    assert ["geladinho", "sacole"] in grupos_com_extras(
        [["geladinho", "sacole"]])
    res = servico.conciliar_linhas([("Sacole de Coco", "2,00", None)],
                                   lambda _m: None)
    it = res.itens[0]
    assert it.semaforo in ("VERDE", "AMARELO")     # deixou de ser "novo"
    assert "Geladinho" in (it.nome if it.produto_id
                           else it.candidato_nome)


def test_f9_43_correcoes_aprendidas_le_e_reverte_o_banco(raiz_env):
    """#43/#53/#91: a lista vem do BANCO (alias→produto) e o Reverter apaga
    de verdade — na releitura não está mais lá."""
    from app.core.database import Database
    from app.core.repositories import ProdutoRepositorio
    from app.qt.telas import servico
    from app.qt.telas.correcoes_dialog import CorrecoesDialog
    _app()
    pid = seeds.add_produto(raiz_env, "Arroz 5kg", "Camil", "24.90")
    db = Database(raiz_env).init()
    try:
        with db.Session() as s:
            ProdutoRepositorio(s)._garantir_alias(pid, "ARROZ TP1 CAMIL 5KG")
            s.commit()
    finally:
        db.engine.dispose()
    lidas = servico.correcoes_aprendidas()
    assert len(lidas) == 1
    assert lidas[0]["alias"] == "ARROZ TP1 CAMIL 5KG"
    assert lidas[0]["produto"] == "Arroz 5kg"
    dlg = CorrecoesDialog()
    assert dlg.tab.rowCount() == 1
    assert dlg.tab.item(0, 0).text() == "ARROZ TP1 CAMIL 5KG"
    dlg._reverter(lidas[0]["id"])
    assert servico.correcoes_aprendidas() == []    # apagou no banco
    assert dlg.tab.rowCount() == 0
    dlg.close()


def test_f9_25_26_sentinela_calibrada_pelo_historico(raiz_env):
    """#25/#26 (R-078): com UM item só em tela (amostra insuficiente), o
    HISTÓRICO das edições salvas calibra a faixa — o preço absurdo dispara o
    aviso. Reverter a calibração (só projeto) deixa a faixa vazia e o teste
    falha."""
    from decimal import Decimal

    from app.ai.revisora import _heuristicas
    from app.core import projetos
    from app.qt.telas.servico import ItemMesa
    from app.rendering.compositor import DadosProduto
    from app.rendering.model import (
        LayoutDef, Pagina, Regiao, Retangulo, Slot, TipoRegiao)
    lay = LayoutDef(100, 100, dpi=96, paginas=[Pagina([
        Slot("s", [Regiao(TipoRegiao.NOME, Retangulo(5, 5, 40, 10))])])])
    historico = [ItemMesa(f"B{i}", f"{5 + i},00", "VERDE", f"Bebida {i}",
                          categoria="Bebidas") for i in range(5)]
    projetos.salvar_projeto("Edição antiga", None, "TABLOIDE", lay,
                            [it.to_dict() for it in historico])
    dados = {"s": DadosProduto("Refri 2L", preco_por=Decimal("500.00"),
                               categoria="Bebidas")}
    avisos = _heuristicas(None, dados, None)
    assert any("parece alto" in a and "Bebidas" in a for a in avisos)


def test_f9_33_39_fusao_reconcilia_fotos(raiz_env):
    """#33/#39: as fotos do PERDEDOR migram na fusão — vencedor sem foto
    herda a atual como OFICIAL (mesmos bytes); vencedor com foto ganha a do
    perdedor como VERSÃO (conferido por conteúdo)."""
    import hashlib

    from app.core.database import Database
    from app.core.deduplicacao import fundir_no_banco
    from app.core.models import Produto
    bib = raiz_env.biblioteca_imagens
    p1 = seeds.add_produto(raiz_env, "Café 500g", "Pilão", "18.90")
    p2 = seeds.add_produto(raiz_env, "Cafe Torrado 500g", "Pilão", "18.90")
    foto_perd = bib / str(p2) / "atual.png"
    foto_perd.parent.mkdir(parents=True, exist_ok=True)
    foto_perd.write_bytes(seeds.png("#AA0000"))
    h_perd = hashlib.sha256(foto_perd.read_bytes()).hexdigest()
    db = Database(raiz_env).init()
    try:
        with db.Session() as s:
            r = fundir_no_banco(s, p1, p2, biblioteca_raiz=bib)
            s.commit()
            venc = s.get(Produto, p1)
            assert venc.caminho_imagem == f"{p1}/atual.png"
    finally:
        db.engine.dispose()
    assert len(r["fotos_migradas"]) == 1
    atual_venc = bib / str(p1) / "atual.png"
    assert hashlib.sha256(
        atual_venc.read_bytes()).hexdigest() == h_perd   # MESMOS bytes
    # 2ª fusão: o vencedor JÁ tem foto → a do novo perdedor vira VERSÃO
    p3 = seeds.add_produto(raiz_env, "Café Extra 500g", "Pilão", "19.90")
    foto3 = bib / str(p3) / "atual.png"
    foto3.parent.mkdir(parents=True, exist_ok=True)
    foto3.write_bytes(seeds.png("#00AA00"))
    h3 = hashlib.sha256(foto3.read_bytes()).hexdigest()
    db = Database(raiz_env).init()
    try:
        with db.Session() as s:
            r2 = fundir_no_banco(s, p1, p3, biblioteca_raiz=bib)
            s.commit()
    finally:
        db.engine.dispose()
    versoes = list((bib / str(p1) / "versoes").glob("*.png"))
    assert any(hashlib.sha256(v.read_bytes()).hexdigest() == h3
               for v in versoes)                    # preservada por conteúdo


def test_f9_61_63_64_fila_ia_prioriza_e_cancela(raiz_env):
    """#61/#63/#64 (R-089/R-090): focar põe o item na frente (o em curso
    termina) e cancelar para a fila entre itens — ordem conferida por
    conteúdo."""
    import threading

    from PySide6.QtCore import Qt as _Qt

    from app.qt.workers import FilaIA
    _app()
    direto = _Qt.ConnectionType.DirectConnection   # sem loop de eventos
    comecou_a = threading.Event()
    solta = threading.Event()
    ordem: list[str] = []

    def _fn(valor):
        if valor == "va":
            comecou_a.set()
            solta.wait(5)
        return valor

    fila = FilaIA([("a", "va"), ("b", "vb"), ("c", "vc"), ("d", "vd")], _fn)
    fila.item_pronto.connect(lambda ch, _r: ordem.append(ch), direto)
    fila.start()
    assert comecou_a.wait(5)
    fila.focar("d")                    # o dono olhou o item d
    solta.set()
    assert fila.wait(5000)
    assert ordem == ["a", "d", "b", "c"]           # d furou a fila

    comecou_a.clear()
    solta.clear()
    executados: list[str] = []
    fila2 = FilaIA([("a", "va"), ("b", "vb")],
                   lambda v: (comecou_a.set(), solta.wait(5), v)[-1])
    fila2.item_pronto.connect(lambda ch, _r: executados.append(ch), direto)
    fila2.start()
    assert comecou_a.wait(5)
    fila2.cancelar()                   # entre itens: o 'b' nunca roda
    solta.set()
    assert fila2.wait(5000)
    assert executados == ["a"]
    assert fila2.pendentes() == ["b"]              # ficou na fila, visível


def test_f9_61_painel_da_fila_na_conciliacao(raiz_env):
    """#63: o painel diz O QUE a IA faz agora e o Parar cancela — por
    conteúdo do rótulo."""
    from app.qt.telas.servico import ItemMesa
    dlg = _conciliacao([ItemMesa("X", "1,00", "VERDE", "X")])
    dlg._fila_enriquecer = None        # sem fila viva: só o painel
    dlg._fila_mudou("u1", "enriquecendo “ARROZ TP1”")
    assert "IA: enriquecendo “ARROZ TP1”" in dlg._fila_status.text()
    assert dlg.btn_parar_ia.isVisibleTo(dlg)
    dlg._parar_fila_ia()
    assert "parada" in dlg._fila_status.text()
    assert not dlg.btn_parar_ia.isVisibleTo(dlg)
    dlg.done(0)


def test_f9_49_marca_extraida_alimenta_a_ordem(raiz_env):
    """#49 (R-087): a marca CONHECIDA vai para a 2ª posição (Tipo+Marca+…)
    — e o caminho degradado do enriquecer usa isso com as marcas do banco."""
    from app.core.aprendizado import ordenar_tipo_marca
    from app.qt.telas import servico
    assert ordenar_tipo_marca("Camil Arroz Tipo 1 5kg", ["Camil"]) \
        == "Arroz Camil Tipo 1 5kg"
    assert ordenar_tipo_marca("Arroz Camil 5kg", ["Camil"]) \
        == "Arroz Camil 5kg"                       # já no lugar: intacto
    assert ordenar_tipo_marca("Arroz Zumba 5kg", ["Camil"]) \
        == "Arroz Zumba 5kg"                       # marca desconhecida: nada
    seeds.add_produto(raiz_env, "Feijão 1kg", "Camil", "7.99")
    prop = servico.enriquecer_descricao("CAMIL ARROZ TIPO 1 5KG", None)
    assert prop.nome.split()[0].lower() != "camil"  # a marca saiu da frente
    assert "Camil" in prop.nome


def test_f9_78_95_ia_nao_inventa_sigla_nem_protocolo():
    """#78/#95 (negativos): sigla/protocolo/marca que a IA ACRESCENTAR sem
    existir no bruto é REMOVIDA pela guarda dura; a expansão do glossário do
    dono (confirmada) sobrevive."""
    import json as _json

    from app.ai.enriquecimento import (
        enriquecer, remover_inventados, tokens_inventados)
    from app.ai.fake import MotorIAFake
    from app.core.sanitize import REGRAS_PADRAO
    assert tokens_inventados("Arroz 5kg", "Arroz Premium INMETRO 5kg") \
        == ["Premium", "INMETRO"]
    assert remover_inventados("Arroz NBR-14725 5kg", "Arroz 5kg") \
        == "Arroz 5kg"
    assert remover_inventados("Molho Vidro 500g", "Molho VD 500g",
                              permitidos=["Vidro"]) == "Molho Vidro 500g"
    fake = MotorIAFake(respostas_chat={"ARROZ BRANCO": _json.dumps({
        "nome_sanitizado": "Arroz Branco SS INMETRO 5kg",
        "tipo": "Arroz", "mais18": False})})
    enr = enriquecer("ARROZ BRANCO 5KG", fake, regras=REGRAS_PADRAO)
    assert "INMETRO" not in enr.nome_sanitizado    # protocolo nunca nasce
    assert "SS" not in enr.nome_sanitizado.split()  # sigla idem
    assert "Arroz Branco" in enr.nome_sanitizado


def test_f9_12_dica_nao_alucina():
    """#12: dica com preço/% inventado ou marca conhecida FORA da oferta é
    rejeitada (None); a dica legítima passa."""
    import json as _json

    from app.ai.enriquecimento import dica_alucinada, gerar_dica
    from app.ai.fake import MotorIAFake
    assert dica_alucinada("Leve 2 com 50% off", ["Arroz 5kg"])
    assert dica_alucinada("Só R$ 9,99 hoje", ["Arroz 5kg"])
    assert dica_alucinada("Vai bem com Nescau", ["Arroz Camil 5kg"],
                          ["Nescau", "Camil"])
    assert not dica_alucinada("O arroz Camil rende mais soltinho",
                              ["Arroz Camil 5kg"], ["Nescau", "Camil"])
    fake = MotorIAFake(respostas_chat={"Itens da oferta": _json.dumps(
        {"dica": "Aproveite 50% de desconto no arroz"})})
    assert gerar_dica(["Arroz 5kg"], 120, fake) is None
    fake2 = MotorIAFake(respostas_chat={"Itens da oferta": _json.dumps(
        {"dica": "Arroz solto: refogue o alho antes da água"})})
    assert gerar_dica(["Arroz 5kg"], 120, fake2) \
        == "Arroz solto: refogue o alho antes da água"


def test_f9_8_manchetes_respeitam_o_teto(raiz_env):
    """#8: o teto de caracteres vale na FUNÇÃO e na CHAMADA da UI (o contexto
    aperta o limite e a sugestão nunca estoura)."""
    import time

    from PySide6.QtWidgets import QApplication

    import app.ai.enriquecimento as E
    from app.ai.enriquecimento import sugerir_manchetes
    from app.qt.design.papel_texto_ui import _dialogo_cls
    app = _app()
    assert all(len(m) <= 12
               for m in sugerir_manchetes("Quintou", None, limite_chars=12))
    capturado: dict = {}

    def _fake(evento, motor, *, limite_chars=None):
        capturado["limite"] = limite_chars
        return ["Manchete curta"]

    original = E.sugerir_manchetes
    E.sugerir_manchetes = _fake
    try:
        dlg = _dialogo_cls()(None, contexto={"evento": "Quintou",
                                             "limite_manchete": 12})
        dlg._sugerir_manchetes()
        fim = time.time() + 3
        while "limite" not in capturado and time.time() < fim:
            app.processEvents()
            time.sleep(0.01)
        assert capturado.get("limite") == 12       # o teto atravessou a UI
        dlg.done(0)
    finally:
        E.sugerir_manchetes = original


def test_f9_23_laudo_leva_ao_item(raiz_env):
    """#23: clicar no aviso seleciona o item citado na estante (por uid) —
    o laudo deixa de ser um QMessageBox morto."""
    from app.qt.telas.servico import ItemMesa
    a = ItemMesa("x", "1,00", "VERDE", "Arroz 5kg")
    b = ItemMesa("x", None, "VERDE", "Feijão 1kg")
    m = _mesa_viva(raiz_env, [a, b])
    uid = m._ir_para_aviso("“Feijão 1kg”: sem preço (ou preço não entendido)")
    assert uid == b.uid
    assert m.lista.currentRow() == 1               # a estante foi ao item
    assert m._ir_para_aviso("aviso sem nome citado") is None
    m.close()


def test_f8_24_aprovacao_e_da_versao_nao_do_id(raiz_env):
    """#24: a aprovação vale para a VERSÃO aprovada (hash do estado salvo) —
    se o conteúdo salvo muda por qualquer porta (ex.: restaurar versão
    antiga), a marca RASCUNHO volta sozinha, sem depender do fluxo de
    salvar."""
    from app.core import projetos
    from app.core.database import Database
    from app.core.models import ProjetoSalvo
    from app.qt.telas.servico import ItemMesa
    from app.rendering.model import (
        LayoutDef, Pagina, Regiao, Retangulo, Slot, TipoRegiao)
    lay = LayoutDef(100, 100, dpi=96, paginas=[Pagina([
        Slot("s", [Regiao(TipoRegiao.NOME, Retangulo(5, 5, 40, 10))])])])
    it = ItemMesa("X", "1,00", "VERDE", "X")
    pid = projetos.salvar_projeto("Aprovado v1", None, "TABLOIDE", lay,
                                  [it.to_dict()])
    projetos.aprovar(pid)
    assert projetos.esta_aprovado(pid)                 # a versão aprovada
    db = Database().init()                             # muda o SALVO por fora
    try:
        with db.Session() as s:
            row = s.get(ProjetoSalvo, pid)
            row.estado_slots = row.estado_slots.replace("1,00", "9,99")
            s.commit()
    finally:
        db.engine.dispose()
    assert not projetos.esta_aprovado(pid)             # o hash não bate mais


# ============================================================================
# §8 — FASE 10 (imagens II + Estúdio IA)
# ============================================================================

def _quadrado_rgba(lado=200, cor=(200, 30, 30, 255)):
    from PIL import Image
    im = Image.new("RGBA", (lado, lado), (0, 0, 0, 0))
    for x in range(20, lado - 20):
        for y in range(20, lado - 20):
            im.putpixel((x, y), cor)
    return im


def test_f10_57_sombra_acompanha_o_tema():
    """#57 (R-102): a MESMA foto gera sombras DIFERENTES por tema — preta no
    claro, halo claro no escuro (pixel na zona da sombra)."""
    from app.images.estudio import cor_sombra_do_tema, packshot_degrau1
    assert cor_sombra_do_tema("claro") == (0, 0, 0)
    assert cor_sombra_do_tema("escuro") != (0, 0, 0)
    fonte = _quadrado_rgba()
    claro = packshot_degrau1(fonte, remover_fundo=lambda im: im, tema="claro")
    escuro = packshot_degrau1(fonte, remover_fundo=lambda im: im,
                              tema="escuro")
    # a zona da sombra: logo abaixo do produto (produto ocupa até y≈920)
    px_c = claro.getpixel((500, 935))
    px_e = escuro.getpixel((500, 935))
    assert px_c[3] > 0 and px_e[3] > 0                 # há sombra nos dois
    assert px_c[:3] == (0, 0, 0)                       # claro: sombra preta
    assert px_e[0] > 120 and px_e[2] > 120             # escuro: halo claro
    assert px_c[:3] != px_e[:3]


def test_f10_20_flag_gerador_liga_o_degrau2(raiz_env, tmp_path, monkeypatch):
    """#20: a flag persiste na Config; com ela LIGADA o tratar_estudio chama
    o degrau 2; sem GPU o aviso aparece (I2) e o degrau 1 entrega."""
    from app.core.database import Database
    from app.core.repositories import ConfigRepositorio
    from app.qt.telas import servico
    assert servico.estudio_gerador_ligado() is False   # padrão: desligado
    db = Database(raiz_env).init()
    try:
        with db.Session() as s:
            ConfigRepositorio(s).set("estudio.gerador", True)
            s.commit()
    finally:
        db.engine.dispose()
    assert servico.estudio_gerador_ligado() is True    # persistiu

    fonte = tmp_path / "foto.png"
    _quadrado_rgba(120).save(fonte)
    chamado: dict = {}
    monkeypatch.setattr("app.images.estudio.packshot_degrau1",
                        lambda img, **kw: _quadrado_rgba(64))
    monkeypatch.setattr(
        "app.images.estudio.refinar_com_gerador",
        lambda pack, **kw: (chamado.setdefault("sim", True),
                            (None, "Sem GPU — fiquei no degrau 1"))[-1])
    status: list[str] = []
    saida = servico.tratar_estudio(str(fonte), status.append,
                                   com_gerador=True)
    assert chamado.get("sim")                          # o degrau 2 foi tentado
    assert any("Sem GPU" in m for m in status)         # degradou COM aviso
    assert Path(saida).is_file()                       # e o degrau 1 entregou
    chamado.clear()
    servico.tratar_estudio(str(fonte), status.append, com_gerador=False)
    assert not chamado                                 # desligado: nem tenta


def test_f10_51_52_webp_no_armazenamento_e_migracao(raiz_env):
    """#51/#52 (R-100): com a chave ligada a foto NOVA sai em WebP com o ALFA
    preservado; a migração tem prévia (nada muda), converte, atualiza o banco
    e é REVERSÍVEL (roundtrip por pixel)."""
    from PIL import Image

    from app.core.database import Database
    from app.core.models import Produto
    from app.images.biblioteca import BibliotecaImagens
    from app.qt.telas import servico
    bib_raiz = raiz_env.biblioteca_imagens
    bib = BibliotecaImagens(bib_raiz, webp=True)
    pid = seeds.add_produto(raiz_env, "Molho 340g", None, "4.99")
    img = _quadrado_rgba(80)
    tmp = bib_raiz / "_tmp.png"
    tmp.parent.mkdir(parents=True, exist_ok=True)
    img.save(tmp)
    atual = bib.ingerir(pid, str(tmp))
    assert atual.name == "atual.webp"                  # saiu em WebP
    reaberta = Image.open(atual)
    assert reaberta.mode == "RGBA"
    assert reaberta.getpixel((0, 0))[3] == 0           # o alfa sobreviveu
    # convivência: a biblioteca em modo PNG ACHA a webp existente
    assert BibliotecaImagens(bib_raiz).caminho_atual(pid).name == "atual.webp"

    # migração: primeiro um acervo PNG de verdade
    pid2 = seeds.add_produto(raiz_env, "Arroz 5kg", None, "24.90")
    p2 = bib_raiz / str(pid2) / "atual.png"
    p2.parent.mkdir(parents=True, exist_ok=True)
    _quadrado_rgba(60, (10, 200, 10, 255)).save(p2)
    db = Database(raiz_env).init()
    try:
        with db.Session() as s:
            s.get(Produto, pid2).caminho_imagem = f"{pid2}/atual.png"
            s.commit()
    finally:
        db.engine.dispose()
    pixels_antes = list(Image.open(p2).convert("RGBA").tobytes())
    previa = servico.migrar_acervo_webp(True, previa=True)
    assert previa["fotos"] >= 1 and p2.exists()        # prévia NÃO muda nada
    r = servico.migrar_acervo_webp(True)
    assert r["fotos"] >= 1
    assert not p2.exists() and p2.with_suffix(".webp").exists()
    db = Database(raiz_env).init()
    try:
        with db.Session() as s:
            assert s.get(Produto, pid2).caminho_imagem \
                == f"{pid2}/atual.webp"                # o banco acompanhou
    finally:
        db.engine.dispose()
    servico.migrar_acervo_webp(False)                  # REVERSÍVEL
    assert p2.exists()
    assert list(Image.open(p2).convert("RGBA").tobytes()) == pixels_antes


def test_f10_63_82_genericas_nao_viram_orfas(raiz_env):
    """#63/#82: fotos em `_genericas` são de FAMÍLIA por convenção — a
    varredura de órfãs NÃO as lista (reverter o pulo faz este teste falhar)."""
    from app.core.manutencao import verificar_acervo
    gen = raiz_env.biblioteca_imagens / "_genericas" / "refrigerante.png"
    gen.parent.mkdir(parents=True, exist_ok=True)
    gen.write_bytes(seeds.png("#00AA66"))
    solta = raiz_env.biblioteca_imagens / "999" / "atual.png"
    solta.parent.mkdir(parents=True, exist_ok=True)
    solta.write_bytes(seeds.png("#AA0066"))
    r = verificar_acervo(raiz_env.raiz)
    orfas = [str(o).replace("\\", "/") for o in r["orfas"]]
    assert "999/atual.png" in orfas                    # a solta É órfã
    assert not any("_genericas" in o for o in orfas)   # a genérica NUNCA


def test_f10_31_32_pincel_de_refino(tmp_path):
    """#31/#32: o gesto do pincel muda o ALFA de verdade — apagar zera,
    restaurar devolve; Aplicar grava o PNG refinado (por pixel)."""
    from PIL import Image

    from app.qt.telas.refino_dialog import RefinoDialog
    _app()
    fonte = tmp_path / "recorte.png"
    _quadrado_rgba(120).save(fonte)
    dlg = RefinoDialog(str(fonte))
    dlg.raio.setValue(6)
    dlg.rb_apagar.setChecked(True)
    dlg.pintar([(60, 60)])
    assert dlg._img.getpixel((60, 60))[3] == 0         # apagou o alfa
    dlg.rb_restaurar.setChecked(True)
    dlg.pintar([(60, 60)])
    assert dlg._img.getpixel((60, 60))[3] == 255       # restaurou
    dlg.rb_apagar.setChecked(True)
    dlg.pintar([(30, 30)])
    dlg._aplicar()
    assert dlg.caminho_final
    salvo = Image.open(dlg.caminho_final)
    assert salvo.getpixel((30, 30))[3] == 0            # o PNG saiu refinado
    assert salvo.getpixel((90, 90))[3] == 255          # o resto intacto
    dlg.close()


def test_f10_8_41_previa_e_comparador_mostram_regua(raiz_env, tmp_path):
    """#8/#41: a prévia antes/depois e o comparador de versões mostram a
    RÉGUA real (resolução + peso) de cada lado."""
    from app.qt.telas.almoxarifado import HistoricoImagensDialog
    from app.qt.telas.previa_estudio_dialog import PreviaEstudioDialog
    _app()
    a = tmp_path / "a.png"
    b = tmp_path / "b.png"
    _quadrado_rgba(100).save(a)
    _quadrado_rgba(240).save(b)
    dlg = PreviaEstudioDialog(str(a), str(b))
    rotulos = [w.text() for w in dlg.findChildren(
        __import__("PySide6.QtWidgets", fromlist=["QLabel"]).QLabel)]
    assert any("100×100 px" in r for r in rotulos)
    assert any("240×240 px" in r for r in rotulos)
    dlg.close()
    pid = seeds.add_produto(raiz_env, "Café 500g", None, "18.90")
    atual = raiz_env.biblioteca_imagens / str(pid) / "atual.png"
    atual.parent.mkdir(parents=True, exist_ok=True)
    _quadrado_rgba(150).save(atual)
    (atual.parent / "versoes").mkdir(exist_ok=True)
    _quadrado_rgba(90).save(atual.parent / "versoes" / "v1.png")
    hist = HistoricoImagensDialog(pid)
    assert "150×150 px" in hist._foto_atual._info.text()
    hist.lista.item(0).setSelected(True)
    assert "90×90 px" in hist._foto_sel._info.text()
    hist.close()


def test_f10_80_aquecer_esrgan(raiz_env, monkeypatch):
    """#80: sem o modelo no disco → False; com ele, o pré-aquecimento
    CONSTRÓI o upscaler (capturado — reverter a chamada falha aqui)."""
    from app.qt.telas import servico
    servico._upscaler_real.cache_clear()
    assert servico.aquecer_upscaler() is False         # sem o .pth
    modelo = raiz_env.modelos / "RealESRGAN_x4plus.pth"
    modelo.parent.mkdir(parents=True, exist_ok=True)
    modelo.write_bytes(b"fake-modelo")
    construidos: list[str] = []

    class _FakeUp:
        def __init__(self, caminho):
            construidos.append(str(caminho))

    monkeypatch.setattr("app.images.upscale.UpscalerRealESRGAN", _FakeUp)
    servico._upscaler_real.cache_clear()
    assert servico.aquecer_upscaler() is True
    assert construidos == [str(modelo)]                # carregou DE VERDADE
    servico._upscaler_real.cache_clear()


def test_f10_46_curadoria_expoe_ajuste_e_refino(tmp_path):
    """#46: a CuradoriaDialog ganhou Ajustar/Refinar — habilitam com a
    seleção e a troca do candidato atualiza o caminho (por conteúdo)."""
    from PySide6.QtCore import Qt

    from app.qt.telas.curadoria_dialog import CuradoriaDialog
    _app()
    cand = tmp_path / "cand.png"
    novo = tmp_path / "novo.png"
    _quadrado_rgba(100).save(cand)
    _quadrado_rgba(80, (0, 0, 200, 255)).save(novo)
    dlg = CuradoriaDialog("Produto X", [str(cand)])
    assert not dlg.btn_ajustar.isEnabled()
    assert not dlg.btn_refinar.isEnabled()
    dlg.lista.item(0).setSelected(True)
    assert dlg.btn_ajustar.isEnabled() and dlg.btn_refinar.isEnabled()
    dlg._trocar_candidato(str(novo))
    assert dlg.lista.item(0).data(Qt.ItemDataRole.UserRole) == str(novo)
    assert "arrumada" in dlg.lista.item(0).toolTip()
    dlg.close()


def test_f10_49_acervo_vem_antes_da_web(raiz_env, monkeypatch):
    """#49: produto parecido COM foto no acervo entra na frente dos
    resultados da web (a web devolve o dela depois)."""
    from app.qt.telas import servico
    pid = seeds.add_produto(raiz_env, "Refrigerante Cola 2L", None, "8.99")
    foto = raiz_env.biblioteca_imagens / str(pid) / "atual.png"
    foto.parent.mkdir(parents=True, exist_ok=True)
    foto.write_bytes(seeds.png("#111111"))
    from app.core.database import Database
    from app.core.models import Produto
    db = Database(raiz_env).init()
    try:
        with db.Session() as s:
            s.get(Produto, pid).caminho_imagem = f"{pid}/atual.png"
            s.commit()
    finally:
        db.engine.dispose()
    assert servico.candidatos_do_acervo("Refrigerante Cola 2L") \
        == [str(foto)]

    class _R:
        candidatos = []
    monkeypatch.setattr("app.images.busca.buscar_imagens",
                        lambda *a, **k: _R())
    achados = servico.buscar_candidatos_para("Refrigerante Cola 2L",
                                             lambda _m: None)
    assert achados and achados[0] == str(foto)         # o acervo veio antes


def test_f10_72_73_adversariais_foto(raiz_env, tmp_path):
    """#72: trocar a foto OFICIAL de um produto NÃO toca a foto do outro
    (por hash de bytes). #73: o cache do upscale identifica por CONTEÚDO —
    o mesmo byte com outro nome cai no MESMO arquivo de cache."""
    import hashlib

    from app.qt.telas import servico
    pa = seeds.add_produto(raiz_env, "Produto A", None, "1.00")
    pb = seeds.add_produto(raiz_env, "Produto B", None, "2.00")
    for pid, cor in ((pa, "#AA0000"), (pb, "#00AA00")):
        f = raiz_env.biblioteca_imagens / str(pid) / "atual.png"
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_bytes(seeds.png(cor))
    foto_b = raiz_env.biblioteca_imagens / str(pb) / "atual.png"
    h_b = hashlib.sha256(foto_b.read_bytes()).hexdigest()
    nova = tmp_path / "nova.png"
    _quadrado_rgba(64, (0, 0, 250, 255)).save(nova)
    servico.definir_imagem(pa, str(nova), lambda _m: None)
    assert hashlib.sha256(
        foto_b.read_bytes()).hexdigest() == h_b        # B intacto (byte)
    # #73: mesmo CONTEÚDO, nomes diferentes → o MESMO cache
    p1 = tmp_path / "um.png"
    p2 = tmp_path / "dois.png"
    _quadrado_rgba(100).save(p1)
    import shutil as _sh
    _sh.copy2(p1, p2)
    d1 = servico.upscale_para_cartaz(str(p1), 400, lambda _m: None)
    d2 = servico.upscale_para_cartaz(str(p2), 400, lambda _m: None)
    assert d1 == d2 and Path(d1).is_file()


# ============================================================================
# §9 — FASE 11 (inteligência: os 5 menores) e §10 (polimento)
# ============================================================================

def test_f11_47_meta_do_evento_define_e_reflete(raiz_env, monkeypatch):
    """#47 (R-122): o gesto na Mesa DEFINE a meta (persistida por evento) e o
    pulso da barra passa a mostrar N/meta."""
    from app.qt.telas import inteligencia as I
    from app.qt.telas.servico import ItemMesa
    m = _mesa_viva(raiz_env, [ItemMesa("A", "1,00", "VERDE", "A"),
                              ItemMesa("B", "2,00", "VERDE", "B")])
    m._evento = "Quintou"
    monkeypatch.setattr(
        "PySide6.QtWidgets.QInputDialog.getInt",
        staticmethod(lambda *a, **k: (40, True)))
    m._definir_meta_evento()
    assert I.meta_evento("Quintou") == 40              # persistiu
    m._atualizar_estatistica()
    assert m._estatistica_lbl.text() == "2/40"         # o pulso refletiu
    m.close()


def test_f11_45_aba_sazonal_mostra_o_ano_passado(raiz_env, monkeypatch):
    """#45 (R-121): a aba lista o que foi ofertado ~1 ano atrás (por data +
    chave natural); edição recente NÃO entra."""
    from datetime import datetime, timedelta

    from app.qt.telas import inteligencia as I
    from app.qt.telas.inteligencia_dialog import InteligenciaDialog
    from app.qt.telas.servico import ItemMesa
    _app()
    antiga = {"criado_em": datetime.now() - timedelta(days=365),
              "itens": [ItemMesa("x", "9,90", "VERDE",
                                 "Panetone 500g").to_dict()]}
    recente = {"criado_em": datetime.now() - timedelta(days=30),
               "itens": [ItemMesa("x", "5,00", "VERDE",
                                  "Sorvete 2L").to_dict()]}
    sug = I.memoria_sazonal([antiga, recente])
    assert [s["nome"] for s in sug] == ["Panetone 500g"]
    monkeypatch.setattr("app.core.projetos.historico_edicoes",
                        lambda *a, **k: [antiga, recente])
    dlg = InteligenciaDialog()
    nomes = [dlg.lista_sazonal.item(i).text()
             for i in range(dlg.lista_sazonal.count())]
    assert nomes == ["Panetone 500g"]                  # a aba reflete
    dlg.close()


def test_f11_51_52_saude_com_metas_e_integridade(raiz_env):
    """#51/#52 (R-126): a saúde ganha metas (ok/abaixo por limiar), a
    contagem de órfãs (R-129) e a nota das fotos (avaliador F9) — numa
    visão só, por conteúdo."""
    from app.qt.telas.inteligencia import METAS_SAUDE, saude_com_metas
    pid = seeds.add_produto(raiz_env, "Único 1kg", None, "9.99")
    foto = raiz_env.biblioteca_imagens / str(pid) / "atual.png"
    foto.parent.mkdir(parents=True, exist_ok=True)
    foto.write_bytes(seeds.png("#332211"))             # foto minúscula → ruim
    from app.core.database import Database
    from app.core.models import Produto
    db = Database(raiz_env).init()
    try:
        with db.Session() as s:
            s.get(Produto, pid).caminho_imagem = f"{pid}/atual.png"
            s.commit()
    finally:
        db.engine.dispose()
    orfa = raiz_env.biblioteca_imagens / "777" / "atual.png"
    orfa.parent.mkdir(parents=True, exist_ok=True)
    orfa.write_bytes(seeds.png("#AABBCC"))
    s = saude_com_metas(raiz_env)
    assert s["total"] == 1 and s["pct_foto"] == 100
    assert s["metas"]["pct_foto"]["ok"] is True        # 100 ≥ meta 90
    assert s["metas"]["pct_ean"]["alvo"] == METAS_SAUDE["pct_ean"]
    assert s["metas"]["pct_ean"]["ok"] is False        # 0% de EAN: abaixo
    assert s["orfas"] == 1                             # a integridade R-129
    assert s["fotos_avaliadas"] == 2                   # produto + a órfã
    assert s["fotos_ruins"] == 2                       # minúsculas → ruins (F9)


def test_f11_39_relatorio_sai_em_pdf(raiz_env, tmp_path, monkeypatch):
    """#39 (R-117): o relatório exporta em PDF de verdade — o conteúdo se
    prova nas linhas (as MESMAS da tela) e o arquivo sai com página."""
    from pypdf import PdfReader

    from app.qt.telas.inteligencia_dialog import InteligenciaDialog
    from app.qt.telas.servico import ItemMesa
    _app()
    itens = [ItemMesa("x", "10,00", "VERDE", "Arroz 5kg",
                      categoria="Mercearia"),
             ItemMesa("x", "5,00", "VERDE", "Feijão 1kg",
                      categoria="Mercearia")]
    dlg = InteligenciaDialog(itens)
    linhas = dlg.linhas_relatorio()
    assert any("2 itens na edição" in ln for ln in linhas)
    assert any("Mercearia: 2" in ln for ln in linhas)
    destino = tmp_path / "rel.pdf"
    monkeypatch.setattr(
        "PySide6.QtWidgets.QFileDialog.getSaveFileName",
        staticmethod(lambda *a, **k: (str(destino), "PDF (*.pdf)")))
    dlg._exportar_relatorio_pdf()
    assert destino.is_file()
    assert len(PdfReader(str(destino)).pages) >= 1
    dlg.close()


def test_f11_85_orfaos_da_f11_tem_chamador_de_ui():
    """#85: varredura por IDENTIFICADOR — cada função da F11/F7 que a ordem
    apontou como órfã agora tem CHAMADOR fora do módulo em que nasceu (e fora
    dos testes). Reverter qualquer ligação de UI faz este teste falhar."""
    raiz = Path(__file__).resolve().parents[1]        # app/
    alvos = {
        "definir_meta_evento": "inteligencia.py",
        "memoria_sazonal": "inteligencia.py",
        "saude_com_metas": "inteligencia.py",
        "separar_por_semaforo": "servico.py",
        "diff_contra_ultima_edicao": "servico.py",
        "exportar_checklist_pdf": "servico.py",
    }
    for simbolo, arquivo_def in alvos.items():
        chamadores = []
        for py in raiz.rglob("*.py"):
            rel = py.relative_to(raiz).as_posix()
            if rel.startswith("tests/") or py.name == arquivo_def:
                continue
            texto = py.read_text(encoding="utf-8", errors="ignore")
            if f"{simbolo}(" in texto and f"def {simbolo}" not in texto:
                chamadores.append(rel)
        assert chamadores, f"{simbolo} segue órfã (sem chamador de UI)"


def test_pol_6_cor_publicado_vem_do_token(raiz_env):
    """§10 #6: a cor do status "publicado" vem do TOKEN tematizado — no tema
    escuro ela MUDA junto (o hex solto não mudava)."""
    from app.qt.design import tokens as t
    from app.qt.telas.dashboard import DashboardTela
    _app()
    dash = DashboardTela()
    assert dash._cor_status("publicado") == t.PUBLICADO
    claro = dash._cor_status("publicado")
    t.ativar_tema("escuro")
    try:
        escuro = dash._cor_status("publicado")
        assert escuro == t.PUBLICADO and escuro != claro   # tematizada
    finally:
        t.ativar_tema("claro")
    dash.close()

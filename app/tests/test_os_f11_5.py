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

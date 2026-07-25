"""A bancada que enxerga gesto (ORDEM_F13_RESGATE · Bloco A · def. de pronto).

A prova de mutação da varredura (§1.4) quebrou as 6 linhas 🔴 mais
críticas do programa e **5 não deixaram nenhum teste vermelho**. Este
arquivo existe para que CADA uma das 6 mutações, reaplicada, acenda ao
menos um vermelho AQUI — pelo gesto real (L2) ou por conteúdo (L3).

HONESTIDADE DE BANCADA (L6): vários testes abaixo são de
CARACTERIZAÇÃO — fixam o comportamento ATUAL, inclusive onde ele é o
próprio bug (R-02 invertido, E-08 rotação sem resize, E-01
auto-seleção). Isso é deliberado: o Bloco A NÃO conserta os 6 — só faz
a bancada vê-los. Quando os Blocos B/C consertarem, o teste
correspondente flipa junto (vermelho antes, verde depois).

| mutação (§1.4)                      | teste que acende               |
|-------------------------------------|--------------------------------|
| 1 V-01  animacoes.py véu/destroyed  | test_mut1_v01_*                |
| 2 E-01  canvas.py auto-seleção      | test_mut2_e01_*                |
| 3 R-02  painel_camadas deltas       | test_mut3_r02_*                |
| 4 E-08  itens.py guarda de rotação  | test_mut4_e08_*                |
| 5 F-01  servico.py etiqueta em lote | test_mut5_f01_*                |
| 6 R-01  compositor.py Y do texto    | test_mut6_r01_*                |
"""

from decimal import Decimal

import pytest
from PySide6.QtCore import QPointF
from PySide6.QtWidgets import QApplication, QDialog, QWidget

from app.rendering.compositor import DadosProduto, compor_pagina
from app.rendering.model import (
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
)


def _app():
    return QApplication.instance() or QApplication([])


@pytest.fixture()
def raiz(tmp_path, monkeypatch):
    monkeypatch.setenv("AUTOTABLOIDE_ROOT", str(tmp_path / "raiz"))
    from app.core.paths import SystemRoot
    root = SystemRoot(tmp_path / "raiz").criar_estrutura()
    acervo.copiar_fontes_reais(root.fontes)
    return root


# fixture `vida` compartilhada: mora no conftest desde o Bloco B (a COND-2
# também precisa dela)


# ---------------------------------------------------------------------------
# mutação 1 · V-01 — animacoes.py: destroyed → limpa o registro do véu
# ---------------------------------------------------------------------------


def test_mut1_v01_destroyed_limpa_o_registro_do_veu(vida):
    """O caminho REAL do vazamento L-01: o diálogo morre SEM o Hide passar
    pelo filtro (destruição junto com o pai, laço de eventos travado). A
    única linha que limpa o registro nesse caminho é o
    ``dlg.destroyed.connect(... _veus.pop ...)`` — a linha da mutação nº1.
    Para isolá-la, o filtro é removido antes da destruição (o belt sai
    para provar o suspender). NÃO prova que o VÉU some da tela — isso é o
    conserto B2; prova que a bancada VÊ a linha."""
    anim = vida
    app = _app()

    pai = QWidget()
    pai.resize(400, 300)
    pai.show()
    dlg = QDialog(pai)
    dlg.resize(120, 90)
    dlg.show()                      # Show → filtro → _entrada_dialogo → véu
    drenar()
    chave = id(dlg)
    assert chave in anim._veus, "pré-condição: o véu do diálogo nem nasceu"

    app.removeEventFilter(anim._animador)   # o Hide NÃO vai passar pelo filtro
    dlg.deleteLater()
    # entrega o DeferredDelete DESTE diálogo ainda dentro do teste (alvo
    # vivo e conhecido — a lei do conftest só descarta os PENDENTES do
    # teardown, que podem apontar para mortos)
    drenar()
    assert chave not in anim._veus, (
        "o destroyed do diálogo não limpou _veus — a linha "
        "animacoes.py:287 foi quebrada (mutação nº1) ou removida")

    # COND-1 do selo do Bloco A (§4.3): não basta o REGISTRO limpar — o
    # VÉU tem de sair da TELA. Era exatamente o que o teste não provava
    # (tela escura eterna do L-01); nasceu vermelha e o B2 a deixou verde.
    drenar()
    veu_na_tela = pai.findChild(QWidget, "veuDialogo")
    assert veu_na_tela is None or not veu_na_tela.isVisible(), (
        "o véu CONTINUA NA TELA depois do diálogo morrer — a tela escura "
        "do L-01 (COND-1)")

    pai.deleteLater()
    drenar()


# ---------------------------------------------------------------------------
# mutação 2 · E-01 — canvas.py: criar região pelo BOTÃO REAL auto-seleciona
# ---------------------------------------------------------------------------


def _layout_editor():
    return LayoutDef(100, 100, dpi=100, paginas=[Pagina([
        Slot("s", [
            Regiao(TipoRegiao.NOME, Retangulo(10, 10, 40, 10), nome="Nome"),
            Regiao(TipoRegiao.PRECO, Retangulo(10, 24, 40, 10), nome="Preço"),
        ]),
    ])])


def test_mut2_e01_botao_da_barra_cria_regiao_e_ela_nasce_selecionada(
        raiz, tmp_path):
    """GESTO (L2): o clique REAL no botão 'Adicionar imagem' da barra cria
    a região — prova a fiação botão→canvas que o T-05 acusou — e a região
    nasce SELECIONADA (o feedback do painel, RG-55; a linha vigiada pela
    mutação nº2).

    INVERTIDO no C1 (COND-3 do selo — o git log guarda a forma antiga em
    5a4f0d0): a caracterização do E-01 virou a exigência do CERTO —
    **duas criações seguidas NÃO nascem grudadas**: cada uma no seu slot
    avulso, em retângulos DIFERENTES (cascata), sem virar irmã da
    anterior. Era exatamente a sequência da gravação do dono
    (IMAGEM→NOME no mesmo retângulo, E-01/L-07)."""
    from app.qt.editor import Editor
    _app()
    e = Editor()
    e.carregar(_layout_editor(), DadosProduto("x"))
    antes = len(e.canvas.regioes())

    clicar(botao_por_tooltip(e.barra, "Adicionar imagem"))

    regioes = e.canvas.regioes()
    assert len(regioes) == antes + 1, "o botão real não criou a região (fiação)"
    nova = [r for r in regioes if r.tipo == TipoRegiao.IMAGEM]
    assert len(nova) == 1
    sel = e.canvas.selecionada()
    assert sel is nova[0], (
        "a região criada pelo botão não está selecionada (o feedback do "
        "painel morreu — mutação nº2)")

    # C1 (E-01): a 2ª criação com a 1ª ainda selecionada NÃO gruda nela
    clicar(botao_por_tooltip(e.barra, "Adicionar nome do produto"))
    nome = e.canvas.selecionada()            # a recém-criada é a selecionada
    assert nome is not None and nome.tipo == TipoRegiao.NOME
    imagem = nova[0]
    slot_img = e.canvas._slot_de(imagem)
    slot_nome = e.canvas._slot_de(nome)
    assert slot_img is not slot_nome, (
        "a região nova HERDOU o slot da anterior — o tudo-grudado voltou "
        "(E-01/C1)")
    assert (nome.rect.x_mm, nome.rect.y_mm) != \
        (imagem.rect.x_mm, imagem.rect.y_mm), (
        "as duas criações nasceram no MESMO retângulo (E-01/L-07)")


# ---------------------------------------------------------------------------
# mutação 3 · R-02 — painel_camadas.py: a fiação Subir→_mover(-1)
# ---------------------------------------------------------------------------


def test_mut3_r02_botao_subir_mexe_o_indice_para_tras_caracterizacao(
        raiz):
    """GESTO (L2): clique REAL na linha do painel de camadas + clique REAL
    no botão ' Subir'.

    INVERTIDO no C3 (COND-3 do selo; a forma antiga — que FIXAVA o bug
    R-02 — vive no git log em 5a4f0d0): agora o teste exige o CERTO, por
    CONTEÚDO. Duas regiões SOBREPOSTAS na mesma célula; a de TRÁS é
    selecionada pelo painel e 'Subir' a TRAZ PARA A FRENTE — o pixel do
    miolo passa a ser a cor dela (era por isso que 'a imagem atrás do
    preço' nunca acontecia: o botão fazia o oposto do tooltip)."""
    from PySide6.QtCore import Qt
    from app.qt.editor import Editor
    _app()
    e = Editor()
    lay = LayoutDef(100, 100, dpi=100, paginas=[Pagina([Slot("s", [
        Regiao(TipoRegiao.NOME, Retangulo(10, 10, 40, 12), nome="Fundo",
               texto_fixo=None),
        Regiao(TipoRegiao.NOME, Retangulo(10, 10, 40, 12), nome="Frente"),
    ])])])
    e.carregar(lay, DadosProduto("x"))
    slot = e.canvas._layout.paginas[0].slots[0]
    alvo = slot.regioes[0]                       # "Fundo": índice 0 = ATRÁS

    # seleciona pelo painel (gesto): clica a LINHA cujo dado é a região
    lista = e.camadas.lista
    linha = None
    for i in range(lista.count()):
        it = lista.item(i)
        if it.data(Qt.ItemDataRole.UserRole) is alvo:
            linha = it
            break
    assert linha is not None, "a região não está listada no painel de camadas"
    clicar(lista.viewport(), pos=lista.visualItemRect(linha).center())
    assert e.canvas.selecionada() is alvo

    clicar(botao_por_texto(e.camadas, "Subir"))
    assert slot.regioes.index(alvo) == 1, (
        "'Subir' NÃO trouxe a região para a frente (índice maior = "
        "desenhada depois = na frente) — o R-02 voltou")
    # e a lista de camadas mostra a convenção Illustrator: TOPO = FRENTE
    topo = e.camadas.lista.item(0).data(Qt.ItemDataRole.UserRole)
    assert topo is alvo, (
        "a 1ª linha do painel não é a região da FRENTE (convenção "
        "Illustrator, C3)")


# ---------------------------------------------------------------------------
# mutação 4 · E-08 — itens.py: rotação desliga o redimensionar pelas alças
# ---------------------------------------------------------------------------


def test_mut4_e08_arrastar_alca_de_regiao_rotacionada_nao_redimensiona(
        raiz):
    """GESTO (L2): arraste REAL na alça inferior-direita de uma região com
    15° de rotação.

    INVERTIDO no C5 (COND-3 do selo; a forma antiga — que FIXAVA a guarda
    do E-08 — vive no git log em 5a4f0d0): agora o teste exige o CERTO —
    a alça REDIMENSIONA a região girada (a conta roda em coordenadas
    LOCAIS do item, não no scenePos cru) e o canto OPOSTO fica parado na
    cena (a âncora não anda). Era o gesto provado ao vivo em L-08:
    +66,+55 de translação e nenhum resize."""
    from app.qt.canvas import CanvasView
    _app()
    lay = LayoutDef(100, 100, dpi=100, paginas=[Pagina([
        Slot("s", [Regiao(TipoRegiao.NOME, Retangulo(25, 30, 40, 20),
                          nome="Nome", rotacao_graus=15.0)]),
    ])])
    c = CanvasView()
    c.resize(400, 300)
    c.carregar(lay, DadosProduto("x"))
    reg = lay.paginas[0].slots[0].regioes[0]
    larg0, alt0 = reg.rect.larg_mm, reg.rect.alt_mm

    item = c._itens[0]
    centro = item.mapToScene(item._w / 2, item._h / 2)
    clicar_na_cena(c, centro)                    # seleciona pelo clique real
    assert item.isSelected()

    ancora_cena = item.mapToScene(0, 0)          # o canto OPOSTO (sup-esq)
    canto = item.mapToScene(item._w, item._h)    # alça inferior-direita
    arrastar_na_cena(c, canto, canto + QPointF(40, 30))

    assert reg.rect.larg_mm > larg0 + 1.0, (
        "a alça NÃO redimensionou a região rotacionada — o E-08 voltou "
        "(rotação desligando o resize)")
    assert reg.rect.alt_mm > alt0 + 1.0
    item2 = next(i for i in c._itens if i.regiao is reg)
    ancora_depois = item2.mapToScene(0, 0)
    assert abs(ancora_depois.x() - ancora_cena.x()) < 3.0, (
        "o canto oposto ANDOU durante o resize — a âncora não segurou")
    assert abs(ancora_depois.y() - ancora_cena.y()) < 3.0


# ---------------------------------------------------------------------------
# mutação 5 · F-01 — servico.py: a etiqueta em lote carrega o PREÇO
# ---------------------------------------------------------------------------


def test_mut5_f01_etiqueta_em_lote_desenha_o_preco_no_pdf(raiz, tmp_path):
    """CONTEÚDO (L3), pela porta pública inteira (gerar_etiquetas_lote →
    compor → impor → PDF no disco): o preço do item INFLUENCIA os pixels
    da folha. A mutação nº5 (tirar o preço do dict servico.py:1860-1863)
    fez uma etiqueta de gôndola SEM PREÇO virar PDF com 851 verdes — aqui
    ela acende: com e sem preço, a imagem embutida no PDF é a MESMA."""
    from pypdf import PdfReader

    from app.qt.telas import servico
    from app.qt.telas.servico import ItemMesa

    def _folha(nome_arq: str, preco: str) -> bytes:
        item = ItemMesa("Refrigerante Cola 2L", preco, "VERDE",
                        "Refrigerante Cola 2L")
        item.preco = preco
        caminho, _avisos = servico.gerar_etiquetas_lote(
            [item], tmp_path / nome_arq)
        pagina = PdfReader(caminho).pages[0]
        imagens = list(pagina.images)
        assert imagens, "o PDF da etiqueta saiu sem imagem embutida"
        return imagens[0].data

    com_preco = _folha("com_preco.pdf", "9,99")
    sem_preco = _folha("sem_preco.pdf", "")
    assert com_preco != sem_preco, (
        "o preço NÃO muda a etiqueta em lote — o dict de "
        "gerar_etiquetas_lote perdeu o campo (mutação nº5 / F-01)")


# ---------------------------------------------------------------------------
# mutação 6 · R-01 — compositor.py: o bloco de texto centraliza na vertical
# ---------------------------------------------------------------------------


def test_mut6_r01_texto_centralizado_na_vertical_por_pixel(tmp_path):
    """CONTEÚDO (L3): uma linha curta numa caixa alta fica no MEIO da
    caixa (compositor.py:312 — `oy = y + max(0,(rh-total_h)//2)`). A
    mutação nº6 (`oy = y`) cola o texto no topo e este teste acende.
    Nota: centralizar é o único comportamento que EXISTE — alinhamento
    vertical configurável é campo ausente do modelo (C4 do Bloco C); o
    centro seguirá sendo o padrão são depois do C4."""
    fontes = tmp_path / "fontes"
    acervo.copiar_fontes_reais(fontes)

    dpi = 100
    reg = Regiao(TipoRegiao.NOME, Retangulo(10, 10, 60, 40),
                 nome="Nome", tamanho_max_pt=10.0)
    lay = LayoutDef(80, 60, dpi=dpi,
                    paginas=[Pagina([Slot("s", [reg])])])
    img = compor_pagina(lay, lay.paginas[0],
                        {"s": DadosProduto("Ao", preco_por=Decimal("1.00"))},
                        fontes_dir=fontes)

    x0 = round(mm_para_px(10, dpi))
    y0 = round(mm_para_px(10, dpi))
    x1 = round(mm_para_px(10 + 60, dpi))
    y1 = round(mm_para_px(10 + 40, dpi))
    cinza = img.convert("L").crop((x0, y0, x1, y1))
    altura = y1 - y0
    tinta = cinza.point(lambda p: 255 if p < 128 else 0)
    caixa = tinta.getbbox()          # (esq, topo, dir, base) da tinta
    assert caixa, "nenhum pixel de texto na região — fonte/composição falhou"
    folga_topo = caixa[1]
    folga_base = altura - caixa[3]
    # centralizado: a folga de cima é comparável à de baixo e é GRANDE
    # (caixa de 40 mm p/ ~1 linha de 10 pt). Com `oy = y`, folga_topo ≈ 0.
    assert folga_topo > altura // 4, (
        f"texto colado no topo (folga {folga_topo}px de {altura}px) — "
        "o Y do compositor mudou (mutação nº6 / R-01)")
    assert abs(folga_topo - folga_base) <= altura // 4, (
        "o bloco não está centralizado na vertical")

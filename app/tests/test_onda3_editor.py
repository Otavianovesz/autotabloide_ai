"""Onda 3 da REVISAO_GERAL — UX do editor (paridade Illustrator), com prova.

RG-12 (rotação de região): serialização com migração, composição girada em
torno do centro SEM deslocar célula vizinha (por pixel), texto deitado por
conteúdo, propagação da mestra com override local.
"""

from decimal import Decimal

from PySide6.QtCore import Qt

from app.rendering.compositor import DadosProduto, compor_pagina
from app.rendering.model import (
    LayoutDef,
    Pagina,
    Regiao,
    Retangulo,
    Slot,
    TipoRegiao,
)

DPI = 100
PX_MM = DPI / 25.4


def _app():
    from PySide6.QtWidgets import QApplication
    return QApplication.instance() or QApplication([])


def _canvas_zoom_teste():
    from PySide6.QtCore import QCoreApplication

    from app.qt.canvas import CanvasView

    c = CanvasView()
    c.resize(500, 400)
    c.show()
    QCoreApplication.processEvents()
    reg = Regiao(TipoRegiao.NOME, Retangulo(10, 10, 60, 12))
    lay = LayoutDef(100, 100, dpi=DPI, paginas=[Pagina([Slot("s", [reg])])])
    c.carregar(lay, DadosProduto("P"))
    QCoreApplication.processEvents()
    return c


def _tinta_bbox(img, x0_mm, y0_mm, x1_mm, y1_mm):
    """Bounding box (px) dos pixels escuros num recorte em mm."""
    rec = img.crop((round(x0_mm * PX_MM), round(y0_mm * PX_MM),
                    round(x1_mm * PX_MM), round(y1_mm * PX_MM)))
    pontos = [(x, y) for y in range(rec.height) for x in range(rec.width)
              if sum(rec.getpixel((x, y))[:3]) < 300]
    if not pontos:
        return None
    xs = [p[0] for p in pontos]
    ys = [p[1] for p in pontos]
    return (min(xs), min(ys), max(xs), max(ys))


# --- RG-12: rotação -------------------------------------------------------------------


def test_rotacao_serializa_e_layout_antigo_abre_com_zero():
    reg = Regiao(TipoRegiao.NOME, Retangulo(10, 10, 30, 10),
                 rotacao_graus=90.0)
    d = reg.to_dict()
    assert d["rotacao_graus"] == 90.0
    assert Regiao.from_dict(d).rotacao_graus == 90.0
    d.pop("rotacao_graus")                 # layout salvo ANTES do RG-12
    assert Regiao.from_dict(d).rotacao_graus == 0.0


def test_rotacao_nao_desloca_conteudo_de_celula_vizinha():
    """Adversarial da ordem: girar a região de UMA célula não move um pixel
    das outras (o rect do modelo não muda — âncora estável, I1)."""
    def _layout(rot: float) -> LayoutDef:
        a = Slot("cel_a", [Regiao(TipoRegiao.NOME, Retangulo(10, 10, 30, 10),
                                  nome="A", rotacao_graus=rot)])
        b = Slot("cel_b", [Regiao(TipoRegiao.NOME, Retangulo(10, 60, 30, 10),
                                  nome="B")])
        return LayoutDef(100, 100, dpi=DPI, paginas=[Pagina([a, b])])

    dados = {"cel_a": DadosProduto("Sabao Ype", preco_por=Decimal("9.99")),
             "cel_b": DadosProduto("Coca Cola", preco_por=Decimal("7.77"))}
    reta = compor_pagina(_layout(0.0), _layout(0.0).paginas[0], dados)
    girada = compor_pagina(_layout(90.0), _layout(90.0).paginas[0], dados)

    # célula B: pixel-idêntica nas duas composições (com folga em volta)
    caixa_b = (round(5 * PX_MM), round(55 * PX_MM),
               round(95 * PX_MM), round(95 * PX_MM))
    assert reta.crop(caixa_b).tobytes() == girada.crop(caixa_b).tobytes()
    # célula A: o conteúdo girou (mudou de verdade)
    caixa_a = (round(0 * PX_MM), round(0 * PX_MM),
               round(50 * PX_MM), round(45 * PX_MM))
    assert reta.crop(caixa_a).tobytes() != girada.crop(caixa_a).tobytes()


def test_rotacao_90_deita_o_texto():
    """Prova por conteúdo: a 90° a tinta fica mais ALTA que larga (a data
    deitada do template real)."""
    def _compor(rot: float):
        reg = Regiao(TipoRegiao.NOME, Retangulo(35, 45, 30, 8),
                     nome="D", rotacao_graus=rot)
        lay = LayoutDef(100, 100, dpi=DPI,
                        paginas=[Pagina([Slot("c", [reg])])])
        return compor_pagina(lay, lay.paginas[0],
                             {"c": DadosProduto("OFERTA VALIDA HOJE")})

    bb_reto = _tinta_bbox(_compor(0.0), 20, 25, 80, 75)
    bb_deitado = _tinta_bbox(_compor(90.0), 20, 25, 80, 75)
    assert bb_reto and bb_deitado
    larg_r, alt_r = bb_reto[2] - bb_reto[0], bb_reto[3] - bb_reto[1]
    larg_d, alt_d = bb_deitado[2] - bb_deitado[0], bb_deitado[3] - bb_deitado[1]
    assert larg_r > alt_r                  # reto: texto corre na horizontal
    assert alt_d > larg_d                  # deitado: corre na vertical


# --- RG-13: hifenização de aproveitamento + justificado -------------------------------


def test_hifenizacao_aproveita_a_linha():
    """Como o Illustrator: a palavra que não cabe INTEIRA deixa um prefixo
    hifenizado enchendo a linha atual (antes: ia inteira para a próxima)."""
    from PIL import ImageFont

    from app.rendering.text_fit import _quebrar_linhas

    fonte = ImageFont.load_default(24)
    listado = "Rosquinha Tradicional"
    # largura que aceita "Rosquinha Tradi-" mas não a frase inteira
    max_w = fonte.getlength("Rosquinha Tradi-") + 2
    linhas = _quebrar_linhas(listado, fonte, max_w)
    assert linhas[0].endswith("-")         # a linha 1 aproveitou o espaço
    assert " " in linhas[0]                # com as DUAS palavras nela
    assert "".join(linhas).replace("-", "").replace(" ", "") == \
        listado.replace(" ", "")           # nenhuma letra sumiu


def test_hifenizacao_nunca_em_numero_ou_codigo():
    from PIL import ImageFont

    from app.rendering.text_fit import _quebrar_linhas

    fonte = ImageFont.load_default(24)
    max_w = fonte.getlength("Oferta 50") + 2
    linhas = _quebrar_linhas("Oferta 500g", fonte, max_w)
    assert linhas == ["Oferta", "500g"]    # "500g" jamais ganha hífen


def test_justificado_alcanca_a_borda_direita():
    """RG-13: com JUSTIFICADO as linhas cheias tocam a borda direita."""
    from app.rendering.model import Alinhamento

    def _compor(alinh):
        reg = Regiao(TipoRegiao.NOME, Retangulo(10, 10, 40, 30),
                     alinhamento=alinh, tamanho_max_pt=14)
        lay = LayoutDef(100, 100, dpi=DPI,
                        paginas=[Pagina([Slot("c", [reg])])])
        return compor_pagina(lay, lay.paginas[0],
                             {"c": DadosProduto(
                                 "Doce de Leite Firmesa Original")})

    bb_esq = _tinta_bbox(_compor(Alinhamento.ESQUERDA), 10, 10, 50, 40)
    bb_jus = _tinta_bbox(_compor(Alinhamento.JUSTIFICADO), 10, 10, 50, 40)
    assert bb_esq and bb_jus
    assert bb_jus[2] > bb_esq[2]           # o justificado estica até a borda
    larg_regiao_px = 40 * PX_MM
    assert bb_jus[2] >= larg_regiao_px - 8  # rente à borda direita (±2 mm)


# --- RG-16/17/18/19: painéis, tutorial, tamanho efetivo, SELO placeholder -------------


def test_tamanho_efetivo_conta_a_reducao():
    """RG-18: o campo mostra o teto; o rótulo conta o que foi DESENHADO."""
    _app()
    c = _canvas_zoom_teste()
    reg = c.regioes()[0]
    reg.tamanho_max_pt = 200.0             # teto absurdo p/ caixa de 60×12mm
    c.atualizar_dados(DadosProduto(
        "Doce de Leite Firmesa Original 400g Tradicional"))
    efetivo = c.tamanho_efetivo_pt(reg)
    assert efetivo is not None and efetivo < 200.0

    from app.qt.painel_propriedades import PainelPropriedades
    painel = PainelPropriedades(c)
    painel.mostrar(reg)
    assert "desenhado a" in painel.tam_efetivo.text()

    reg2 = Regiao(TipoRegiao.IMAGEM, Retangulo(1, 1, 10, 10))
    assert c.tamanho_efetivo_pt(reg2) is None   # imagem: não se aplica


def test_selo_desenha_placeholder_no_editor():
    """RG-19: a região SELO não aparece mais vazia no canvas do editor."""
    _app()
    from PySide6.QtCore import QRectF
    from PySide6.QtGui import QImage, QPainter

    from app.qt.canvas import CanvasView

    def _tinta_na_area_selo(com_selo: bool):
        c = CanvasView()
        c.resize(600, 500)
        tipo = TipoRegiao.SELO if com_selo else TipoRegiao.IMAGEM
        reg = Regiao(tipo, Retangulo(20, 20, 50, 30), nome="X")
        lay = LayoutDef(100, 100, dpi=DPI, paginas=[Pagina([Slot("s", [reg])])])
        c.carregar(lay, DadosProduto(""))
        img = QImage(400, 400, QImage.Format.Format_RGB32)
        img.fill(0xFFFFFFFF)
        p = QPainter(img)
        c._scene.render(p, QRectF(0, 0, 400, 400))
        p.end()
        def _nao_branco(px):
            r, g, b = (px >> 16) & 0xFF, (px >> 8) & 0xFF, px & 0xFF
            return r + g + b < 690
        return sum(1 for yy in range(85, 205) for xx in range(85, 285)
                   if _nao_branco(img.pixel(xx, yy)))

    # com o placeholder há MUITO mais tinta que o mero contorno tracejado
    assert _tinta_na_area_selo(True) > _tinta_na_area_selo(False) + 50


def test_tutorial_uma_vez_por_tela(tmp_path, monkeypatch):
    """RG-17: cartão na 1ª visita; 'Entendi' persiste; nunca repete."""
    _app()
    monkeypatch.setenv("AUTOTABLOIDE_ROOT", str(tmp_path / "raiz"))
    from app.core.database import Database
    from app.core.paths import SystemRoot
    root = SystemRoot(tmp_path / "raiz").criar_estrutura()
    Database(root).init().engine.dispose()

    from PySide6.QtCore import QCoreApplication
    from PySide6.QtWidgets import QWidget

    from app.qt.design.shell import Shell
    from app.qt.design.tutorial import mostrar_se_primeira_vez

    shell = Shell()
    shell.adicionar_tela("mesa", QWidget())
    shell.show()
    QCoreApplication.processEvents()
    mostrar_se_primeira_vez(shell, "mesa")
    cartao = getattr(shell, "_tutorial_aberto", None)
    assert cartao is not None              # 1ª visita: o cartão apareceu
    cartao._fechar()                       # "Entendi" grava na Config
    shell._tutorial_aberto = None
    mostrar_se_primeira_vez(shell, "mesa")
    assert shell._tutorial_aberto is None  # 2ª visita: silêncio
    mostrar_se_primeira_vez(shell, "cofre")
    assert shell._tutorial_aberto is None  # tela sem texto: nada


def test_janela_invisivel_nao_mostra_tutorial():
    _app()
    from app.qt.design.shell import Shell
    from app.qt.design.tutorial import mostrar_se_primeira_vez

    shell = Shell()                        # SEM show()
    mostrar_se_primeira_vez(shell, "mesa")
    assert getattr(shell, "_tutorial_aberto", None) is None


# --- RG-15: célula como GRUPO ---------------------------------------------------------


def _canvas_celula_trio():
    """Canvas com UMA célula de 3 regiões (imagem+nome+preço) + 1 avulsa."""
    from PySide6.QtCore import QCoreApplication

    from app.qt.canvas import CanvasView

    c = CanvasView()
    c.resize(600, 500)
    c.show()
    QCoreApplication.processEvents()
    trio = Slot("cel", [
        Regiao(TipoRegiao.IMAGEM, Retangulo(10, 10, 30, 20), nome="Img"),
        Regiao(TipoRegiao.NOME, Retangulo(10, 32, 30, 8), nome="Nome"),
        Regiao(TipoRegiao.PRECO, Retangulo(10, 41, 30, 8), nome="Preço"),
    ])
    avulsa = Slot("livre", [Regiao(TipoRegiao.TEXTO_LEGAL,
                                   Retangulo(60, 60, 30, 10), nome="Dica")])
    lay = LayoutDef(100, 100, dpi=DPI, paginas=[Pagina([trio, avulsa])])
    c.carregar(lay, DadosProduto("P", preco_por=Decimal("2.00")))
    QCoreApplication.processEvents()
    return c


def test_clique_frio_seleciona_o_trio_da_celula():
    """RG-15 + RG-55 (Fase 4, decisão travada do passo 11): o 1º clique
    numa região acende a CÉLULA inteira (para mover), MAS o painel mostra
    a região efetivamente clicada — nunca "Nada selecionado" (painel
    órfão do RG-55)."""
    _app()
    c = _canvas_celula_trio()
    nome = next(it for it in c._itens if it.regiao.nome == "Nome")
    nome.setSelected(True)                 # o que o Qt faz no clique…
    nome._selecao_por_clique(False)        # …e a regra da célula por cima
    do_trio = [it for it in c._itens if it.regiao.nome != "Dica"]
    assert all(it.isSelected() for it in do_trio)   # o trio inteiro
    avulsa = next(it for it in c._itens if it.regiao.nome == "Dica")
    assert not avulsa.isSelected()         # a região de OUTRO slot não
    # RG-55: o painel mostra A REGIÃO CLICADA (a primária), não None
    assert c.selecionada() is nome.regiao


def test_segundo_clique_sem_arrasto_entra_na_regiao():
    _app()
    c = _canvas_celula_trio()
    nome = next(it for it in c._itens if it.regiao.nome == "Nome")
    nome.setSelected(True)
    nome._selecao_por_clique(False)        # 1º clique: grupo
    preco = next(it for it in c._itens if it.regiao.nome == "Preço")
    preco._pos_press = preco.pos()
    preco._selecao_por_clique(False)       # 2º clique (grupo já ativo)
    assert preco._colapsar_no_release      # marcado p/ entrar no release…
    preco._colapsar_se_clique_parado()     # …clique parado: colapsa
    assert preco.isSelected()
    assert not nome.isSelected()
    assert c.selecionada() is preco.regiao  # o painel mostra A região


def test_arrasto_do_grupo_nao_colapsa():
    """Clique+arrasto com o grupo ativo MOVE a célula inteira (não entra)."""
    _app()
    c = _canvas_celula_trio()
    nome = next(it for it in c._itens if it.regiao.nome == "Nome")
    nome.setSelected(True)
    nome._selecao_por_clique(False)
    nome._pos_press = nome.pos()
    nome._selecao_por_clique(False)        # 2º clique…
    nome.setPos(nome.x() + 30, nome.y())   # …mas houve ARRASTO
    nome._colapsar_se_clique_parado()
    do_trio = [it for it in c._itens if it.regiao.nome != "Dica"]
    assert all(it.isSelected() for it in do_trio)   # o grupo sobreviveu


def test_ctrl_clique_preserva_selecao_multipla():
    _app()
    c = _canvas_celula_trio()
    nome = next(it for it in c._itens if it.regiao.nome == "Nome")
    nome.setSelected(True)
    nome._selecao_por_clique(True)         # com Ctrl: nada de grupo
    preco = next(it for it in c._itens if it.regiao.nome == "Preço")
    assert not preco.isSelected()


def test_hover_acende_o_trio():
    _app()
    c = _canvas_celula_trio()
    nome = next(it for it in c._itens if it.regiao.nome == "Nome")
    nome._marcar_hover_grupo(True)
    do_trio = [it for it in c._itens
               if it.regiao.nome in ("Img", "Preço")]
    assert all(it._hover_grupo for it in do_trio)
    avulsa = next(it for it in c._itens if it.regiao.nome == "Dica")
    assert not avulsa._hover_grupo
    nome._marcar_hover_grupo(False)
    assert not any(it._hover_grupo for it in do_trio)


# --- RG-14: pesos/variantes da família ------------------------------------------------


def test_variantes_da_familia_bundled(tmp_path, monkeypatch):
    """'quero Black': as irmãs da fonte atual aparecem por ESTILO, e trocar
    o peso é só trocar o arquivo (o compositor nem fica sabendo)."""
    import shutil
    from pathlib import Path

    monkeypatch.setenv("AUTOTABLOIDE_ROOT", str(tmp_path / "raiz"))
    from app.core.paths import SystemRoot
    root = SystemRoot(tmp_path / "raiz").criar_estrutura()
    reais = Path("AutoTabloide_System_Root/fontes")
    for nome in ("Roboto-Regular.ttf", "Roboto-Bold.ttf"):
        origem = reais / nome
        if origem.exists():
            shutil.copy(origem, root.fontes / nome)

    from app.qt.fontes import familia_estilo, variantes_bundled
    fam, estilo = familia_estilo("Roboto-Regular.ttf")
    assert fam == "Roboto" and estilo == "Regular"
    pares = variantes_bundled("Roboto-Regular.ttf")
    assert ("Bold", "Roboto-Bold.ttf") in pares      # a irmã apareceu
    assert ("Regular", "Roboto-Regular.ttf") in pares
    # e a partir da Bold, a família é a MESMA (simetria)
    assert variantes_bundled("Roboto-Bold.ttf") == pares


# --- RG-11: navegação da roda ---------------------------------------------------------


def _roda(canvas, dy: int, mods):
    from PySide6.QtCore import QPoint, QPointF
    from PySide6.QtGui import QWheelEvent

    ev = QWheelEvent(QPointF(200, 200), QPointF(200, 200),
                     QPoint(0, 0), QPoint(0, dy),
                     Qt.MouseButton.NoButton, mods,
                     Qt.ScrollPhase.NoScrollPhase, False)
    canvas.wheelEvent(ev)


def test_roda_rola_ctrl_horizontal_alt_zoom():
    """RG-11 (decisão do dono): roda=rolagem · Ctrl+roda=horizontal ·
    Alt+roda=zoom. Era roda=zoom — o gesto de rolar detonava a escala."""
    _app()
    from PySide6.QtCore import Qt as QtNS

    c = _canvas_zoom_teste()
    c.zoom(3.0)                            # conteúdo maior que o viewport
    escala = c.escala_atual()
    v0 = c.verticalScrollBar().value()
    _roda(c, -120, QtNS.KeyboardModifier.NoModifier)
    assert c.verticalScrollBar().value() != v0      # rolou na vertical…
    assert c.escala_atual() == escala               # …sem mexer no zoom

    h0 = c.horizontalScrollBar().value()
    _roda(c, -120, QtNS.KeyboardModifier.ControlModifier)
    assert c.horizontalScrollBar().value() != h0    # Ctrl: horizontal

    _roda(c, -120, QtNS.KeyboardModifier.AltModifier)
    assert c.escala_atual() < escala                # Alt: zoom (com clamp)


def test_barras_de_rolagem_sempre_visiveis():
    _app()
    from PySide6.QtCore import Qt as QtNS

    c = _canvas_zoom_teste()
    assert c.horizontalScrollBarPolicy() == \
        QtNS.ScrollBarPolicy.ScrollBarAlwaysOn
    assert c.verticalScrollBarPolicy() == \
        QtNS.ScrollBarPolicy.ScrollBarAlwaysOn


def test_rotacao_propaga_da_mestra_e_respeita_override():
    from app.rendering.grade import propagar_mestre

    mestra = Regiao(TipoRegiao.TEXTO_LEGAL, Retangulo(2, 2, 20, 6),
                    texto_fixo="ATÉ 25/07")
    m = Slot("m", [mestra], mestre=True, origem_mm=(0.0, 0.0))
    d1r = Regiao.from_dict(mestra.to_dict())
    d1r.uid = "d1"
    d1r.ref_mestre = mestra.uid
    d1r.de_mestre = True
    d2r = Regiao.from_dict(mestra.to_dict())
    d2r.uid = "d2"
    d2r.ref_mestre = mestra.uid
    d2r.de_mestre = True
    d2r.overrides = {"rotacao_graus"}      # esta célula tem ajuste próprio
    d1 = Slot("d1", [d1r], origem_mm=(30.0, 0.0), ref_grupo="m")
    d2 = Slot("d2", [d2r], origem_mm=(60.0, 0.0), ref_grupo="m")
    pagina = Pagina([m, d1, d2])

    mestra.rotacao_graus = 90.0            # a data deita NA MESTRA
    propagar_mestre(pagina)
    assert d1r.rotacao_graus == 90.0       # derivada acompanha
    assert d2r.rotacao_graus == 0.0        # override local vence (precedência)

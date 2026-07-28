"""ORDEM F13-TERTIUSDECIMUS — os dois acertos da Terça (+ o invariante).

A1: NENHUM texto desenha fora do rect da sua região — era lacuna de
invariante (o nome atravessava a palha da cesta); medível por máscara
de pixel nas 8 páginas. A2: o selo escreve SÓ a data nos OITO (o C3
era regra e tinha ficado numa página — a L11 de novo).
"""

from pathlib import Path

import pytest

_PACOTE = Path(__file__).resolve().parents[2] / "Templates novos"

_CHAVES_8 = ["segunda-frios", "terca-do-pao", "quarta-das-ofertas",
             "quinta-do-peixe", "sexta-verde", "sabado-da-carne",
             "jornal-do-mes", "quintou"]


def _requer_pacote():
    if not _PACOTE.exists():
        pytest.skip("REQUER ACERVO DO DONO: a pasta 'Templates novos/'")


def _fontes_reais(tmp_path):
    from app.tests import acervo
    fontes = tmp_path / "fontes"
    fontes.mkdir(exist_ok=True)
    acervo.copiar_fontes_reais(fontes)
    return fontes


def test_a2_o_selo_escreve_so_a_data_nos_oito():
    """A2: quando o conserto é de REGRA, vale para os oito (L11). Os
    selos redondos com curva gravada são SÓ-DATA; as três exceções são
    DE ARTE, declaradas: o Jornal (p1/p2 — a frase é o conteúdo do
    cabeçalho) e o verso do Quintou (o disclaimer longo do publicado)."""
    _requer_pacote()
    from app.rendering.encartes import layout_de_encarte
    from app.rendering.model import PapelTexto

    so_data_esperado = {
        "segunda-frios": True, "terca-do-pao": True,
        "quarta-das-ofertas": True, "quinta-do-peixe": True,
        "sexta-verde": True, "sabado-da-carne": True,
    }
    for chave, esperado in so_data_esperado.items():
        lay = layout_de_encarte(chave, _PACOTE)
        selo = next(s for p in lay.paginas for s in p.slots
                    if s.id == "selo-validade")
        reg = next(r for r in selo.regioes
                   if r.papel_texto == PapelTexto.VALIDADE)
        assert reg.so_data is esperado, f"{chave}: so_data={reg.so_data}"
    # o Quintou: frente SÓ-DATA (o tijolo), verso é o disclaimer (não)
    lay = layout_de_encarte("quintou", _PACOTE)
    frente = next(s for s in lay.paginas[0].slots if s.id == "selo-validade")
    assert frente.regioes[0].so_data is True
    verso = next(s for s in lay.paginas[1].slots if s.id == "v-validade")
    assert verso.regioes[0].so_data is False
    # o Jornal: a validade é linha de cabeçalho, não selo — completo
    lay = layout_de_encarte("jornal-do-mes", _PACOTE)
    for pag in lay.paginas:
        for s in pag.slots:
            for r in s.regioes:
                if r.papel_texto == PapelTexto.VALIDADE:
                    assert r.so_data is False, "o Jornal virou só-data?"


def test_q2_item_com_percentual_em_vez_de_preco():
    """Q2 (a Quarta): "LANCHE NA CHAPA COM 20 % de DESCONTO" é ITEM com
    valor comercial (o desconto), não prosa nem item-sem-preço: o
    parser entende, o papel DESCONTO desenha o dado, e o pré-voo cala.
    A prosa longa com percentual (o leve-3) segue no balde."""
    from app.qt.telas.colagem import descontos_de, parse_colagem
    from app.rendering.compositor import DadosProduto, texto_composto_legal
    from app.rendering.model import PapelTexto, Regiao, Retangulo, TipoRegiao
    from app.qt.telas.servico import validar_composicao
    from app.rendering.model import LayoutDef, Pagina, Slot

    balde: list[str] = []
    linhas = parse_colagem(
        "▶ LANCHE NA CHAPA COM 20 % de DESCONTO\n"
        "LEVE 3 SONHOS OU 3 CROASONHOS E GANHE 25 % de DESCONTO, ...\n"
        "▶ MILHO VERDE ETTI 170G __ só __ 3,88", balde=balde)
    assert len(linhas) == 2, [li.nome for li in linhas]
    lanche = linhas[0]
    assert lanche.desconto_pct == 20 and lanche.preco is None
    assert lanche.preco_valido, "o desconto declarado é valor comercial"
    assert "DESCONTO" not in lanche.nome.upper(), lanche.nome
    assert descontos_de(linhas) == [20, None]
    assert any("25" in b for b in balde), "o leve-3 fugiu do balde"

    # o papel DESCONTO desenha o dado quando não há de/por
    reg = Regiao(TipoRegiao.TEXTO_LEGAL, Retangulo(0, 0, 20, 8),
                 papel_texto=PapelTexto.DESCONTO)
    assert texto_composto_legal(
        reg, DadosProduto("Lanche", desconto_pct=20)) == "-20%"

    # e o pré-voo NÃO acusa "sem preço" no item com desconto
    lay = LayoutDef(100, 100, dpi=100, paginas=[Pagina([Slot("c", [
        Regiao(TipoRegiao.IMAGEM, Retangulo(10, 10, 30, 30), nome="Foto"),
        Regiao(TipoRegiao.PRECO, Retangulo(10, 45, 30, 8), nome="Preço"),
    ])])])
    avisos = validar_composicao(
        lay, {"c": DadosProduto("Lanche na Chapa", desconto_pct=20,
                                imagem_path="x.png")})
    assert not any("sem preço" in a for a in avisos), avisos


def test_a1_a_banda_nao_cresce_atraves_de_vao_de_arte(tmp_path):
    """A1: o passo 3 da precedência só cresce COLADO na foto — com um
    vão de ARTE entre a foto e a banda (o painel das cestas), crescer
    seria pintar texto sobre o desenho; a cadeia segue ao passo 4/5."""
    from app.rendering.model import Regiao, Retangulo, TipoRegiao
    from app.rendering.nome_fit import precedencia_do_nome
    from app.rendering.units import px_para_mm

    fontes = _fontes_reais(tmp_path)
    dpi = 96

    def _r(x, y, w, h):
        return Retangulo(px_para_mm(x, dpi), px_para_mm(y, dpi),
                         px_para_mm(w, dpi), px_para_mm(h, dpi))

    foto = Regiao(TipoRegiao.IMAGEM, _r(0, 0, 200, 200))
    # o VÃO: 30 px de arte entre a foto e a banda
    nome = Regiao(TipoRegiao.NOME, _r(0, 230, 200, 24),
                  fonte="Roboto-Bold.ttf", tamanho_max_pt=13.0,
                  tamanho_min_pt=13.0, sem_hifen=True)
    sub = Regiao(TipoRegiao.SUBTITULO, _r(0, 258, 200, 14),
                 fonte="Roboto-Regular.ttf", tamanho_max_pt=8.0)
    aj = precedencia_do_nome("Salsicha Hot Dog Rezende Tradicional",
                             None, None, [foto, nome, sub], dpi, fontes)
    assert aj is not None
    assert nome.uid not in aj.rects, (
        "a banda cresceu ATRAVÉS do vão de arte — o texto vai pintar "
        "sobre o desenho (o caso da cesta da Terça)")


def test_a1_nenhum_texto_fora_do_rect_nas_8_por_mascara(tmp_path):
    """A1 (o invariante, medível): compõe cada página COM e SEM os
    textos — todo pixel que mudou tem de estar DENTRO do bbox de
    alguma região da célula (rot-aware, folga de sombra). Tinta de
    texto fora do rect é a pior saída possível: pinta a arte."""
    _requer_pacote()
    import numpy as np
    from app.rendering.compositor import DadosProduto, compor_pagina
    from app.rendering.encartes import layout_de_encarte
    from app.rendering.model import TipoRegiao
    from app.rendering.units import mm_para_px

    fontes = _fontes_reais(tmp_path)
    NOME = "Nome Comprido De Teste Para O Invariante Da Máscara"
    violacoes = []
    for chave in _CHAVES_8:
        lay = layout_de_encarte(chave, _PACOTE)
        for pi, pag in enumerate(lay.paginas):
            alvo = [s for s in pag.slots
                    if any(r.tipo == TipoRegiao.NOME and r.visivel
                           for r in s.regioes)]
            if not alvo:
                continue
            dados = {s.id: DadosProduto(NOME, descritor="descritor teste")
                     for s in alvo}
            com = compor_pagina(lay, pag, dados, fontes_dir=fontes, dpi=96)
            sem = compor_pagina(lay, pag, {}, fontes_dir=fontes, dpi=96)
            a, b = np.asarray(com), np.asarray(sem)
            diff = np.any(a != b, axis=2)
            masc = np.zeros(diff.shape, dtype=bool)
            F = 8                          # folga: sombra/anti-alias
            for s in alvo:
                for r in s.regioes:
                    x = mm_para_px(r.rect.x_mm, 96)
                    y = mm_para_px(r.rect.y_mm, 96)
                    w = mm_para_px(r.rect.larg_mm, 96)
                    h = mm_para_px(r.rect.alt_mm, 96)
                    if r.rotacao_graus % 360:
                        # rot: o palco é a diagonal centrada
                        import math
                        lado = math.hypot(w, h)
                        cx, cy = x + w / 2, y + h / 2
                        x, y = cx - lado / 2, cy - lado / 2
                        w = h = lado
                    y0 = max(0, int(y - F)); y1 = min(diff.shape[0],
                                                      int(y + h + F))
                    x0 = max(0, int(x - F)); x1 = min(diff.shape[1],
                                                      int(x + w + F))
                    masc[y0:y1, x0:x1] = True
            fora = int((diff & ~masc).sum())
            if fora > 20:                  # ruído de compressão tolerado
                violacoes.append(f"{chave} p{pi + 1}: {fora}px de texto "
                                 "FORA das regiões")
    assert not violacoes, "\n".join(violacoes)

"""ORDEM F13-DUODECIMUS — a Terça do Pão (o teste difícil de verdade).

A tabela da Terça quebra três suposições: 2/3 dela é PROSA promocional
com números que parecem preço (T1/T3); são 5 itens para 4 células
livres (T2); e as armadilhas de texto (T4). O parser tem de separar
produto de prosa SEM engolir nada em silêncio (I2).
"""

from pathlib import Path

import pytest

_PACOTE = Path(__file__).resolve().parents[2] / "Templates novos"

# a tabela REAL da Terça (a transcrição da ordem, como o OCR lê)
TABELA_TERCA = '''"HOJE É O DIA DO SONHO E DO CROASONHO, NO BELO BRASIL".
É a terça-feira especial do pão francês do sonho e do croasonho com pedaços de
moranguinho!! Uma enorme diversidade de sabores  LEVE 3 SONHOS OU 3 CROASONHOS
E GANHE 25 % de DESCONTO, ...
VENHA... SABOREAR, e com os preços mais baixos da cidade.  E TEM TAMBEM.......

  <> O PÃO FRANCÊS COM 50 % de DESCONTO <>

• SALSICHA HOT DOG REZENDE KG__só__          9,90
• FIGADO BOVINO ____100 g ___SÓ________      0,99
• OSSINHO _________À_____100g ____só_______  1,81
• COXA SOB COXA_À______100g ____POR____      0,77
• LINGUA e CORAÇÃO ____100g _____Só_______   0,66'''


def _requer_pacote():
    if not _PACOTE.exists():
        pytest.skip("REQUER ACERVO DO DONO: a pasta 'Templates novos/'")


def _app():
    from PySide6.QtWidgets import QApplication
    return QApplication.instance() or QApplication([])


@pytest.fixture()
def raiz_tmp(tmp_path, monkeypatch):
    monkeypatch.setenv("AUTOTABLOIDE_ROOT", str(tmp_path / "raiz"))
    from app.core.database import Database
    from app.core.paths import SystemRoot
    from app.tests import acervo
    root = SystemRoot(tmp_path / "raiz").criar_estrutura()
    acervo.copiar_fontes_reais(root.fontes)
    Database(root).init().engine.dispose()
    return root


# ---------------------------------------------------------------------------
# T1 + T3 — a prosa não vira produto; os percentuais são da arte
# ---------------------------------------------------------------------------


def test_t1_a_prosa_nao_vira_produto_e_o_balde_mostra():
    """T1: só vira item a linha com preço de MOEDA no fim; a prosa com
    número (o 25% do leve-3, o 50% do pão) vai ao BALDE visível; a
    prosa sem número morre em silêncio. Os 5 itens saem exatos."""
    from app.qt.telas.colagem import parse_colagem

    balde: list[str] = []
    linhas = parse_colagem(TABELA_TERCA, balde=balde)

    assert len(linhas) == 5, [li.nome for li in linhas]
    precos = [li.preco for li in linhas]
    assert precos == ["9,90", "0,99", "1,81", "0,77", "0,66"], precos
    for li in linhas:
        assert li.preco_valido, f"“{li.nome}”: {li.aviso}"
        for lixo in ("VENHA", "SABOREAR", "DESCONTO", "CROASONHO",
                     "HOJE", "TAMBEM"):
            assert lixo not in li.nome.upper(), (
                f"a PROSA virou produto: “{li.nome}”")
    # T3: nenhum percentual virou preço
    assert not any(li.preco in ("50", "25", "50,00", "25,00")
                   for li in linhas)
    # o balde MOSTRA a prosa com número (o dono confere que nada útil
    # se perdeu — I2); a prosa sem número não polui
    assert any("50" in b for b in balde), f"o pão 50% sumiu calado: {balde}"
    assert any("25" in b for b in balde), f"o leve-3 sumiu calado: {balde}"
    assert not any("VENHA" in b.upper() for b in balde), balde


def test_t1_o_fluxo_de_colunas_nao_mudou():
    """Guarda de regressão: a colagem ESTRUTURADA (tab/;) e o preço no
    fim continuam virando item como sempre — o T1 só mata a PROSA."""
    from app.qt.telas.colagem import parse_colagem

    linhas = parse_colagem("Arroz Tio João 5kg\t24,90\n"
                           "Feijão Preto;9,90\n"
                           "Leite Integral 12,49")
    assert [li.nome for li in linhas] == \
        ["Arroz Tio João 5kg", "Feijão Preto", "Leite Integral"]
    assert all(li.preco_valido for li in linhas)
    # e o item CURTO sem preço (a lista de WhatsApp) segue amarelo —
    # só a PROSA morreu
    dove = parse_colagem("Sabonete Dove")
    assert len(dove) == 1 and not dove[0].preco_valido


# ---------------------------------------------------------------------------
# T4 — as armadilhas de texto
# ---------------------------------------------------------------------------


def test_t4_o_a_de_enfeite_sai_e_o_nome_fica_inteiro():
    """T4: o "À" entre pontilhados é enfeite de preenchimento e SAI; um
    "à" legítimo dentro do nome (Frango à Passarinho) FICA."""
    from app.qt.telas.colagem import parse_colagem

    linhas = parse_colagem(TABELA_TERCA)
    ossinho = next(li for li in linhas if "OSSINHO" in li.nome.upper())
    assert "À" not in ossinho.nome and " A " not in f" {ossinho.nome} ", \
        ossinho.nome
    coxa = next(li for li in linhas if "COXA" in li.nome.upper())
    assert "À" not in coxa.nome, coxa.nome
    livre = parse_colagem("Frango à Passarinho\t19,90")[0]
    assert "à" in livre.nome, "o À legítimo foi comido"


def test_t4_a_unidade_solta_no_fim_desce_ao_descritor(tmp_path):
    """T4: "SALSICHA HOT DOG REZENDE KG" — o kg solto (sem número)
    desce ao descritor como o peso desce; o nome não fica com rabo."""
    _requer_pacote()
    from app.rendering.encartes import layout_de_encarte
    from app.rendering.nome_fit import precedencia_do_nome
    from app.tests import acervo

    fontes = tmp_path / "fontes"
    fontes.mkdir(exist_ok=True)
    acervo.copiar_fontes_reais(fontes)
    lay = layout_de_encarte("terca-do-pao", _PACOTE)
    cesta = next(s for s in lay.paginas[0].slots if s.id == "celula-3")
    aj = precedencia_do_nome("Salsicha Hot Dog Rezende KG", None, None,
                             cesta.regioes, lay.dpi, fontes)
    assert aj is not None
    assert not aj.nome.lower().endswith(" kg"), aj.nome
    assert aj.descritor and "kg" in aj.descritor.lower(), aj.descritor
    assert "…" not in aj.nome and not aj.elipsa


# ---------------------------------------------------------------------------
# T5 — o par Sonho + Croissant: uma foto POR ZONA da célula fixa
# ---------------------------------------------------------------------------


def test_t5_o_par_de_fotos_uma_por_zona(raiz_tmp, tmp_path):
    """T5 (decisão registrada): ``conteudo_fixo["imagens"]`` é uma
    LISTA — uma foto por zona de foto da célula, na ordem das regiões
    (o arranjo F7.2 não serve: ele divide UMA região; aqui a arte já
    separa as zonas com o “+”). O singular ``imagem`` continua valendo
    (a mesma foto em todas as zonas — compat)."""
    _requer_pacote()
    from PIL import Image
    from app.rendering.compositor import compor_pagina
    from app.rendering.encartes import layout_de_encarte
    from app.rendering.model import TipoRegiao
    from app.rendering.units import mm_para_px
    from app.tests import acervo

    fontes = tmp_path / "fontes"
    fontes.mkdir(exist_ok=True)
    acervo.copiar_fontes_reais(fontes)

    bib = raiz_tmp.biblioteca_imagens
    (bib / "_fixos").mkdir(parents=True, exist_ok=True)
    Image.new("RGBA", (200, 200), (200, 30, 30, 255)).save(
        bib / "_fixos" / "sonho.png")
    Image.new("RGBA", (200, 200), (30, 30, 200, 255)).save(
        bib / "_fixos" / "croissant.png")

    lay = layout_de_encarte("terca-do-pao", _PACOTE)
    pag = lay.paginas[0]
    fixa2 = next(s for s in pag.slots if s.id == "celula-2")
    zonas = [r for r in fixa2.regioes if r.tipo == TipoRegiao.IMAGEM]
    assert len(zonas) == 2, "a celula-2 perdeu uma zona de foto?"
    fixa2.conteudo_fixo = {
        "nome": "Sonho + Croissant", "descritor": "a dupla da terça",
        "preco": "9,90", "preco_da_semana": False,
        "imagens": ["_fixos/sonho.png", "_fixos/croissant.png"],
    }

    img = compor_pagina(lay, pag, {}, fontes_dir=fontes, dpi=96)

    def _cor_media(reg):
        x = round(mm_para_px(reg.rect.x_mm, 96))
        y = round(mm_para_px(reg.rect.y_mm, 96))
        w = round(mm_para_px(reg.rect.larg_mm, 96))
        h = round(mm_para_px(reg.rect.alt_mm, 96))
        rec = img.crop((x + w // 4, y + h // 4,
                        x + 3 * w // 4, y + 3 * h // 4))
        px = list(rec.convert("RGB").getdata())
        n = len(px)
        return tuple(sum(c[i] for c in px) / n for i in range(3))

    c1, c2 = _cor_media(zonas[0]), _cor_media(zonas[1])
    assert c1[0] > c1[2] + 40, f"a zona 1 não é a foto VERMELHA: {c1}"
    assert c2[2] > c2[0] + 40, f"a zona 2 não é a foto AZUL: {c2}"

    # compat: o singular repete a mesma foto nas duas zonas
    fixa2.conteudo_fixo = {"nome": "Sonho", "preco": "9,90",
                           "preco_da_semana": False,
                           "imagem": "_fixos/sonho.png"}
    img2 = compor_pagina(lay, pag, {}, fontes_dir=fontes, dpi=96)
    img = img2
    d1, d2 = _cor_media(zonas[0]), _cor_media(zonas[1])
    assert d1[0] > d1[2] + 40 and d2[0] > d2[2] + 40, (d1, d2)


# ---------------------------------------------------------------------------
# T6 — foto já recortada NÃO é reprocessada (a guarda do alfa útil)
# ---------------------------------------------------------------------------


def test_t6_alfa_util_pula_o_rembg():
    """T6: "pão francês.png" já vem recortado — alfa DE VERDADE pula o
    rembg (reprocessar recorte pronto só degrada); um PNG com alfa todo
    opaco é um JPG disfarçado e NÃO conta."""
    from PIL import Image, ImageDraw
    from app.images.fundo import tem_alfa_util

    recortada = Image.new("RGBA", (100, 100), (0, 0, 0, 0))
    ImageDraw.Draw(recortada).ellipse((20, 20, 80, 80),
                                      fill=(200, 150, 90, 255))
    assert tem_alfa_util(recortada)
    assert not tem_alfa_util(
        Image.new("RGBA", (100, 100), (255, 255, 255, 255)))
    assert not tem_alfa_util(Image.new("RGB", (100, 100), "white"))

    raiz = Path(__file__).resolve().parents[2]
    pao = raiz / "pão frances.png"
    if pao.exists():                      # a foto REAL do dono
        assert tem_alfa_util(Image.open(pao)), \
            "o pão recortado do dono não foi reconhecido como pronto"


# ---------------------------------------------------------------------------
# T2 — o 5º item fica VISÍVEL (fora da grade), nunca some
# ---------------------------------------------------------------------------


def test_t2_o_quinto_item_fica_visivel_e_o_aviso_diz(raiz_tmp, monkeypatch):
    """T2: 5 itens para 4 células livres — o auto-preencher põe 4, o 5º
    CONTINUA na estante marcado "fora da grade", e o aviso diz o que
    fazer. Nada some em silêncio (I2)."""
    from PySide6.QtCore import Qt
    from app.qt.telas import mesa as mod_mesa
    from app.qt.telas import servico
    from app.qt.telas.mesa import MesaTela
    from app.rendering.model import (
        LayoutDef, Pagina, Regiao, Retangulo, Slot, TipoRegiao,
    )
    _app()

    def _cel(x, y):
        return [Regiao(TipoRegiao.NOME, Retangulo(x, y, 30, 10),
                       nome="Nome"),
                Regiao(TipoRegiao.PRECO, Retangulo(x, y + 12, 30, 6),
                       nome="Preço")]

    lay = LayoutDef(150, 150, dpi=100, paginas=[Pagina(
        [Slot(f"c{i}", _cel(10 + i * 35, 10), origem_mm=(10 + i * 35, 10))
         for i in range(4)]
        + [Slot("fx", _cel(10, 40), origem_mm=(10, 40), fixa=True)])])

    m = MesaTela()
    m.setAttribute(Qt.WidgetAttribute.WA_DontShowOnScreen, True)
    m.carregar_layout(lay, None, nome_layout="Terça do Pão")
    m._itens = [servico.ItemMesa(f"Item {i}", f"{i},99", "VERDE",
                                 f"Item {i}") for i in range(1, 6)]
    m._recarregar_lista()
    toasts: list[str] = []
    monkeypatch.setattr(mod_mesa, "mostrar_toast",
                        lambda _p, msg, **k: toasts.append(msg))
    m.show()
    try:
        m._auto_preencher()
        assert len(m._mapa) == 4, m._mapa
        assert "fx" not in m._mapa
        assert m.lista.count() == 5, "o 5º item SUMIU da estante"
        fora = [it for it in m._itens if it.uid not in m._mapa.values()]
        assert len(fora) == 1
        assert any("não coube" in t and "estante" in t for t in toasts), (
            f"o aviso não diz o que fazer: {toasts}")
    finally:
        m.close()

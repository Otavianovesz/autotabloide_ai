"""Etapa B da ORDEM_F8 (F8.2) — seções visuais: cálculo, DIY e a prova da lei.

A lei da casa (3ª aplicação): seção é DECORATIVA — não é slot, não é região,
não entra no mapa. Aqui está a prova de que "ocupável" e o pré-voo nem
sabem que ela existe.
"""

from decimal import Decimal

from PySide6.QtWidgets import QApplication

from app.qt.telas import servico
from app.rendering.compositor import DadosProduto, compor_pagina
from app.rendering.secoes import Secao, calcular_secoes, desenhar_secoes
from app.tests.test_adversarial_vinculo import _grade_4


def _app():
    QApplication.instance() or QApplication([])


def _categorias_grade(pagina, cats):
    """slot_id → categoria, na ordem visual da grade sintética 2×2."""
    return {s.id: c for s, c in zip(pagina.slots, cats)}


# --- B1: runs contíguos, sub-retângulo por linha ------------------------------------


def test_runs_contiguos_e_quebra_de_linha():
    lay = _grade_4()                       # 2×2: linha 1 = c0,c1; linha 2 = c2,c3
    pagina = lay.paginas[0]
    # 3 primeiras células "Limpeza" (atravessa a quebra de linha), última "Bebidas"
    secoes = calcular_secoes(pagina, _categorias_grade(
        pagina, ["Limpeza", "Limpeza", "Limpeza", "Bebidas"]))
    assert [s.categoria for s in secoes] == ["Limpeza", "Bebidas"]
    # o run de Limpeza atravessou a linha → 2 sub-retângulos (um por linha)
    assert len(secoes[0].retangulos) == 2
    assert len(secoes[1].retangulos) == 1
    # sub-retângulos em linhas distintas (o de baixo começa mais abaixo)
    assert secoes[0].retangulos[1].y_mm > secoes[0].retangulos[0].y_mm


def test_celula_vazia_quebra_o_run_e_sem_categoria_e_outros():
    lay = _grade_4()
    pagina = lay.paginas[0]
    cats = _categorias_grade(pagina, ["Limpeza", "Limpeza", None, "Limpeza"])
    del cats[pagina.slots[1].id]           # célula 1 SEM item → quebra o run
    secoes = calcular_secoes(pagina, cats)
    assert [s.categoria for s in secoes] == ["Limpeza", "Outros", "Limpeza"]


def test_titulo_editavel_por_pagina():
    lay = _grade_4()
    pagina = lay.paginas[0]
    pagina.titulos_secoes = {"Limpeza": "Casa Limpa"}
    secoes = calcular_secoes(pagina, _categorias_grade(
        pagina, ["Limpeza", "Limpeza", "Bebidas", "Bebidas"]))
    assert secoes[0].titulo == "Casa Limpa"      # o override da página
    assert secoes[1].titulo == "Bebidas"         # sem override = a categoria


# --- B2: a PROVA da lei — seção não consome item nem gera aviso -----------------------


def test_lei_da_casa_secao_nao_e_ocupavel_nem_gera_aviso(tmp_path):
    from PIL import Image

    from app.rendering.grade import ocupaveis, ordenar_slots_visualmente

    lay = _grade_4()
    pagina = lay.paginas[0]
    ocupaveis_antes = [s.id for s in ocupaveis(pagina.slots)]

    pagina.secoes_ligadas = True           # seções LIGADAS…
    pagina.titulos_secoes = {"Limpeza": "Casa Limpa"}
    # …e NADA muda no ocupável (seção não é slot nem região)
    assert [s.id for s in ocupaveis(pagina.slots)] == ocupaveis_antes
    assert [s.id for s in
            ocupaveis(ordenar_slots_visualmente(pagina.slots))] == \
        ocupaveis_antes

    # pré-voo: grade completa + seções ligadas → ZERO aviso falso
    foto = tmp_path / "p.png"
    Image.new("RGB", (50, 50), "#123456").save(foto)
    dados = {s.id: DadosProduto(f"Item {i}", preco_por=Decimal("1"),
                                imagem_path=str(foto), categoria="Limpeza")
             for i, s in enumerate(pagina.slots)}
    avisos = servico.validar_composicao(lay, dados)
    assert not any("seç" in a.lower() or "secao" in a.lower() for a in avisos)
    assert avisos == []                    # nenhum aviso nenhum, aliás


# --- desenho: liga/desliga por página, título aparece ---------------------------------


def test_secoes_desenham_so_quando_ligadas(tmp_path):
    from PIL import Image

    lay = _grade_4()
    pagina = lay.paginas[0]
    foto = tmp_path / "p.png"
    Image.new("RGB", (50, 50), "#777777").save(foto)
    dados = {s.id: DadosProduto(f"Item {i}", preco_por=Decimal("1"),
                                imagem_path=str(foto), categoria="Limpeza")
             for i, s in enumerate(pagina.slots)}

    desligada = compor_pagina(lay, pagina, dados)
    pagina.secoes_ligadas = True
    ligada = compor_pagina(lay, pagina, dados)
    assert list(desligada.getdata()) != list(ligada.getdata())   # o contorno existe
    # desligar POR PÁGINA volta ao desenho de sempre (B3)
    pagina.secoes_ligadas = False
    de_novo = compor_pagina(lay, pagina, dados)
    assert list(de_novo.getdata()) == list(desligada.getdata())


def test_desenhar_secoes_nao_toca_o_miolo_da_celula():
    """O contorno corre pela folga: o MIOLO dos retângulos fica intacto."""
    from PIL import Image

    from app.rendering.model import Retangulo

    base = Image.new("RGB", (500, 500), "#FFFFFF")
    antes = base.getpixel((250, 250))
    desenhar_secoes(base, [Secao("X", "X", [Retangulo(10, 10, 100, 100)])],
                    dpi=100, fontes_dir=None)
    assert base.getpixel((250, 250)) == antes      # centro intocado
    # a linha existe: meio da aresta SUPERIOR (longe do canto arredondado
    # e da etiqueta do título, que mora à esquerda)
    assert base.getpixel((236, 40)) != antes

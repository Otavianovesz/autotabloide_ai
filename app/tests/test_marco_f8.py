"""Etapa C da ORDEM_F8 — O MARCO em versão de suíte (determinística).

O tabloide categorizado de ~40 itens sobre as DUAS faces reais do Quintou
(+ 1 página extra que os 40 pedem): agrupado por categoria, seções
desenhadas, pré-voo limpo, export PNG×3 + PDF de 3 páginas medido — e o
trio de CADA célula conferido POR PIXEL nas três páginas.

(O selfcheck_f8 roda o mesmo fluxo com o ACERVO REAL clonado — este teste
é a versão sintética exata que a suíte guarda para sempre.)
"""

import colorsys
from decimal import Decimal
from pathlib import Path

import pytest
from PIL import Image
from PySide6.QtWidgets import QApplication

from app.qt.telas import servico
from app.qt.telas.servico import ItemMesa
from app.rendering.compositor import DadosProduto, compor_pagina
from app.rendering.export import exportar_pdf_multipagina, exportar_png
from app.rendering.grade import (
    adicionar_pagina_de_arte,
    layout_grade_de_arte,
    ocupaveis,
    ordenar_slots_visualmente,
)
from app.rendering.model import TipoRegiao
from app.rendering.units import mm_para_px

ARTE = Path("arte/quintou")
CATEGORIAS = ["Mercearia", "Bebidas", "Limpeza", "Higiene", None]  # None→Outros

pytestmark = pytest.mark.skipif(
    not (ARTE / "frente_template.png").exists(),
    reason="arte real do Quintou não está no repositório")


def _cor(i: int) -> tuple[int, int, int]:
    r, g, b = colorsys.hsv_to_rgb((i * 11 % 40) / 40.0, 1.0, 1.0)
    return round(r * 255), round(g * 255), round(b * 255)


def _itens40(tmp_path) -> list[ItemMesa]:
    itens = []
    for i in range(40):
        foto = tmp_path / f"m{i}.png"
        Image.new("RGB", (200, 200), _cor(i)).save(foto)
        itens.append(ItemMesa(
            descricao=f"MARCO-{i}", preco=f"{i + 1},00", semaforo="VERDE",
            nome=f"MARCO-{i}", imagem=str(foto),
            categoria=CATEGORIAS[i % len(CATEGORIAS)]))
    return itens


def test_marco_40_itens_categorizado_ponta_a_ponta(tmp_path, monkeypatch):
    monkeypatch.setenv("AUTOTABLOIDE_ROOT", str(tmp_path / "raiz"))
    QApplication.instance() or QApplication([])
    import shutil
    from pypdf import PdfReader

    from app.core.paths import SystemRoot
    root = SystemRoot(tmp_path / "raiz").criar_estrutura()
    reais = Path("AutoTabloide_System_Root/fontes")
    if reais.exists():                       # a raiz de teste tem as fontes reais
        for f in reais.glob("*.ttf"):
            shutil.copy(f, root.fontes / f.name)

    # frente + verso reais + a página EXTRA que os 40 pedem (45 células)
    layout, _ = layout_grade_de_arte(str(ARTE / "frente_template.png"))
    adicionar_pagina_de_arte(layout, str(ARTE / "verso_template.png"))
    adicionar_pagina_de_arte(layout, str(ARTE / "verso_template.png"))
    ids = [s.id for pag in layout.paginas for s in pag.slots]
    assert len(ids) == 45 and len(set(ids)) == 45

    # ~40 itens com categorias variadas → fila AGRUPADA (Outros no fim)
    itens = _itens40(tmp_path)
    fila = servico.ordenar_por_categoria(itens, ["Mercearia", "Bebidas",
                                                 "Limpeza", "Higiene"])
    assert (fila[0].categoria, fila[-1].categoria) == ("Mercearia", None)

    slots = []
    for pag in layout.paginas:
        slots.extend(ocupaveis(ordenar_slots_visualmente(pag.slots)))
        pag.secoes_ligadas = True                    # seções LIGADAS (F8.2)
    mapa = {s.id: it.uid for s, it in zip(slots, fila)}
    assert len(mapa) == 40                           # 40 nas 45 células

    # pré-voo LIMPO (foto+preço+nome em tudo; seções não geram aviso falso)
    por_uid = {it.uid: it for it in itens}
    dados = {sid: DadosProduto(por_uid[u].nome,
                               preco_por=servico.preco_decimal(por_uid[u].preco),
                               imagem_path=por_uid[u].imagem,
                               categoria=por_uid[u].categoria)
             for sid, u in mapa.items()}
    assert servico.validar_composicao(layout, dados) == []

    # export PNG×3 + PDF de 3 páginas — e o trio POR PIXEL em cada célula
    imgs = []
    for n, pag in enumerate(layout.paginas, start=1):
        img = compor_pagina(layout, pag, dados)
        assert img.size == (1080, 1300)              # 1:1 com a arte real
        exportar_png(img, tmp_path / f"marco_p{n}.png", layout.dpi)
        imgs.append(img)
        for slot in pag.slots:
            uid = mapa.get(slot.id)
            if uid is None:
                continue                             # as 5 células vazias
            reg = next(r for r in slot.regioes if r.tipo == TipoRegiao.IMAGEM)
            cx = round(mm_para_px(reg.rect.x_mm + reg.rect.larg_mm / 2,
                                  layout.dpi))
            cy = round(mm_para_px(reg.rect.y_mm + reg.rect.alt_mm / 2,
                                  layout.dpi))
            esperado = _cor(int(por_uid[uid].nome.split("-")[1]))
            assert img.getpixel((cx, cy))[:3] == esperado, \
                f"página {n}, {slot.id}: o trio trocou de lugar!"

    pdf = exportar_pdf_multipagina(imgs, tmp_path / "marco.pdf", layout.dpi)
    leitor = PdfReader(str(pdf))
    assert len(leitor.pages) == 3

    # o agrupamento rendeu SEÇÕES de verdade (ligado ≠ desligado, página 1)
    for pag in layout.paginas:
        pag.secoes_ligadas = False
    sem_secoes = compor_pagina(layout, layout.paginas[0], dados)
    assert list(imgs[0].getdata()) != list(sem_secoes.getdata())

    # congelar o marco → reabrir → seções/mapa/itens idênticos (spot na pág. 2)
    for pag in layout.paginas:
        pag.secoes_ligadas = True
    from app.core import projetos
    pid = projetos.salvar_projeto("Marco F8", "Quintou", "TABLOIDE", layout,
                                  [it.to_dict() for it in itens], mapa=mapa)
    p = projetos.abrir_projeto(pid)
    assert p.mapa == mapa
    assert all(pag.secoes_ligadas for pag in p.layout.paginas)
    re_uid = {d["uid"]: d for d in p.itens}
    dados2 = {sid: DadosProduto(re_uid[u]["nome"], preco_por=Decimal("1"),
                                imagem_path=re_uid[u]["imagem"],
                                categoria=re_uid[u]["categoria"])
              for sid, u in p.mapa.items()}
    img2 = compor_pagina(p.layout, p.layout.paginas[1], dados2)
    for slot in p.layout.paginas[1].slots:
        uid = p.mapa.get(slot.id)
        if uid is None:
            continue
        reg = next(r for r in slot.regioes if r.tipo == TipoRegiao.IMAGEM)
        cx = round(mm_para_px(reg.rect.x_mm + reg.rect.larg_mm / 2,
                              p.layout.dpi))
        cy = round(mm_para_px(reg.rect.y_mm + reg.rect.alt_mm / 2,
                              p.layout.dpi))
        esperado = _cor(int(re_uid[uid]["nome"].split("-")[1]))
        assert img2.getpixel((cx, cy))[:3] == esperado

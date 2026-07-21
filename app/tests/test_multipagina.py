"""F5.8 Etapa B — D8.1..D8.7 da ORDEM_F5_8, com as DUAS faces reais do Quintou.

O adversarial da multipágina: 30 células com ids ÚNICOS, 30 itens fluindo da
página 1 para a 2 na ordem visual, remoção de página com undo restaurando
página+mapa, congelar/reabrir/duplicar, export PNG×2 e PDF — trio conferido
POR PIXEL nas duas páginas e nenhum uid em duas células.
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
from app.rendering.grade import (
    adicionar_pagina_de_arte, layout_grade_de_arte, ocupaveis,
    ordenar_slots_visualmente,
)
from app.rendering.model import LayoutDef, Pagina, Regiao, Retangulo, Slot, TipoRegiao
from app.rendering.units import mm_para_px

ARTE = Path("arte/quintou")

pytestmark = pytest.mark.skipif(
    not (ARTE / "frente_template.png").exists(),
    reason="arte real do Quintou não está no repositório")


@pytest.fixture()
def raiz_tmp(tmp_path, monkeypatch):
    monkeypatch.setenv("AUTOTABLOIDE_ROOT", str(tmp_path / "raiz"))
    import shutil
    from app.core.database import Database
    from app.core.paths import SystemRoot

    root = SystemRoot(tmp_path / "raiz").criar_estrutura()
    reais = Path("AutoTabloide_System_Root/fontes")
    if reais.exists():
        for f in reais.glob("*.ttf"):
            shutil.copy(f, root.fontes / f.name)
    Database(root).init().engine.dispose()
    return root


def _cor(i: int) -> tuple[int, int, int]:
    """30 cores exatas e distintas (HSV espaçado, saturação/valor cheios)."""
    r, g, b = colorsys.hsv_to_rgb((i * 7 % 30) / 30.0, 1.0, 1.0)
    return round(r * 255), round(g * 255), round(b * 255)


def _itens30(tmp_path) -> list[ItemMesa]:
    itens = []
    for i in range(30):
        foto = tmp_path / f"p{i}.png"
        Image.new("RGB", (200, 200), _cor(i)).save(foto)
        itens.append(ItemMesa(descricao=f"PROD-{i}", preco=f"{i + 1},00",
                              semaforo="VERDE", nome=f"PROD-{i}",
                              imagem=str(foto)))
    return itens


def _fluxo(layout) -> list:
    """O MESMO caminho do auto-preencher (D8.3): páginas na ordem, ocupáveis."""
    slots = []
    for pagina in layout.paginas:
        slots.extend(ocupaveis(ordenar_slots_visualmente(pagina.slots)))
    return slots


def _conferir_paginas(layout, mapa, itens):
    """Compõe CADA página e confere o pixel central da IMAGEM de cada célula."""
    por_uid = {it.uid: it for it in itens}
    dados = {sid: DadosProduto(por_uid[u].nome, preco_por=Decimal("1"),
                               imagem_path=por_uid[u].imagem)
             for sid, u in mapa.items() if u in por_uid}
    for pagina in layout.paginas:
        img = compor_pagina(layout, pagina, dados)
        for slot in pagina.slots:
            uid = mapa.get(slot.id)
            if uid is None or uid not in por_uid:
                continue
            reg = next(r for r in slot.regioes if r.tipo == TipoRegiao.IMAGEM)
            cx = round(mm_para_px(reg.rect.x_mm + reg.rect.larg_mm / 2, layout.dpi))
            cy = round(mm_para_px(reg.rect.y_mm + reg.rect.alt_mm / 2, layout.dpi))
            esperado = _cor(int(por_uid[uid].nome.split("-")[1]))
            assert img.getpixel((cx, cy))[:3] == esperado, \
                f"{slot.id}: imagem não é a de {por_uid[uid].nome}"


def _montar_frente_verso() -> LayoutDef:
    layout, _ = layout_grade_de_arte(str(ARTE / "frente_template.png"))
    adicionar_pagina_de_arte(layout, str(ARTE / "verso_template.png"))
    return layout


def test_d81_ids_unicos_nas_duas_faces():
    layout = _montar_frente_verso()
    ids = [s.id for pag in layout.paginas for s in pag.slots]
    assert len(ids) == 30 and len(set(ids)) == 30      # únicos no layout inteiro
    # página 1 legada mantém celula_N; a página 2 nasce celula_<uuid8>
    assert layout.paginas[0].slots[0].id == "celula_0"
    assert all(len(s.id) == len("celula_") + 8 for s in layout.paginas[1].slots)
    assert layout.paginas[1].arquivo_fundo.endswith("verso_template.png")  # D8.2


def test_d81_from_dict_recusa_id_duplicado():
    lay = LayoutDef(100, 100, dpi=100, paginas=[
        Pagina([Slot("celula_0", [Regiao(TipoRegiao.NOME, Retangulo(1, 1, 5, 5))])]),
        Pagina([Slot("celula_0", [Regiao(TipoRegiao.NOME, Retangulo(1, 1, 5, 5))])]),
    ])
    d = lay.to_dict()                       # to_dict não valida (estado bruto)…
    with pytest.raises(ValueError, match="celula_0"):
        LayoutDef.from_dict(d)              # …a CARGA recusa (D8.1)


def test_d87_fluxo_completo_frente_verso(raiz_tmp, tmp_path):
    QApplication.instance() or QApplication([])
    layout = _montar_frente_verso()
    itens = _itens30(tmp_path)

    # D8.3: 30 itens fluem página 1 → página 2 na ordem visual
    slots = _fluxo(layout)
    assert len(slots) == 30
    mapa = {s.id: it.uid for s, it in zip(slots, itens)}
    p1_ids = {s.id for s in layout.paginas[0].slots}
    assert sum(1 for sid in mapa if sid in p1_ids) == 15   # 15 por página
    # nenhum uid em duas células
    assert len(set(mapa.values())) == len(mapa)
    _conferir_paginas(layout, mapa, itens)                 # pixel nas 2 páginas

    # D8.4: remover a página 2 pelo canvas → itens dela "fora"; undo restaura
    from app.qt.canvas import CanvasView
    v = CanvasView()
    v.mapa = dict(mapa)
    v.carregar(layout, DadosProduto("x"))
    p2_ids = {s.id for s in layout.paginas[1].slots}
    v.ir_para_pagina(1)
    assert v.remover_pagina_atual()
    assert len(v._layout.paginas) == 1
    assert not any(sid in v.mapa for sid in p2_ids)        # mapa limpo
    assert v.desfazer()                                    # D5/D8.6
    assert len(v._layout.paginas) == 2
    assert sum(1 for sid in v.mapa if sid in p2_ids) == 15  # mapa voltou
    layout, mapa = v._layout, dict(v.mapa)
    _conferir_paginas(layout, mapa, itens)

    # D8.6: congelar → reabrir → duplicar, com os DOIS fundos
    from app.core import projetos
    pid = projetos.salvar_projeto("FrenteVerso", None, "TABLOIDE", layout,
                                  [it.to_dict() for it in itens], mapa=mapa)
    p = projetos.abrir_projeto(pid)
    assert len(p.layout.paginas) == 2
    assert p.mapa == mapa
    assert Path(p.layout.paginas[1].arquivo_fundo).exists()   # verso congelado
    reitens = [ItemMesa.from_dict(d) for d in p.itens]
    _conferir_paginas(p.layout, p.mapa, reitens)
    p2 = projetos.abrir_projeto(projetos.duplicar_projeto(pid, "FV 2"))
    _conferir_paginas(p2.layout, p2.mapa,
                      [ItemMesa.from_dict(d) for d in p2.itens])

    # D8.5: exportar PNG×2 + PDF multipágina no tamanho exato
    from pypdf import PdfReader

    from app.rendering.export import exportar_pdf_multipagina, exportar_png
    por_uid = {it.uid: it for it in reitens}
    dados = {sid: DadosProduto(por_uid[u].nome, preco_por=Decimal("1"),
                               imagem_path=por_uid[u].imagem)
             for sid, u in p.mapa.items() if u in por_uid}
    imgs = [compor_pagina(p.layout, pag, dados) for pag in p.layout.paginas]
    for i, img in enumerate(imgs, start=1):
        assert exportar_png(img, tmp_path / f"fv_p{i}.png",
                            p.layout.dpi).exists()
    pdf = exportar_pdf_multipagina(imgs, tmp_path / "fv.pdf", p.layout.dpi)
    assert len(PdfReader(str(pdf)).pages) == 2

    # D8.5: pré-voo rotula a página
    dados_falho = dict(dados)
    alvo = next(iter(p2_ids & set(dados.keys())))
    dados_falho[alvo] = DadosProduto("Sem Foto", preco_por=None)
    avisos = servico.validar_composicao(p.layout, dados_falho)
    assert any(a.startswith("página 2") for a in avisos)
"""Onda 5 da REVISAO_GERAL — VISUAL + o marco, com prova.

RG-31 (seções com estilos + o bug da borda), RG-32 (cartaz), RG-33 (selos),
RG-34 (validade da oferta), RG-42 (presets), RG-43 (assistente de preço).
"""

from decimal import Decimal
from pathlib import Path

import pytest
from PIL import Image

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


@pytest.fixture()
def raiz_tmp(tmp_path, monkeypatch):
    monkeypatch.setenv("AUTOTABLOIDE_ROOT", str(tmp_path / "raiz"))
    from app.core.database import Database
    from app.core.paths import SystemRoot

    root = SystemRoot(tmp_path / "raiz").criar_estrutura()
    Database(root).init().engine.dispose()
    return root


# --- RG-31: estilos de seção ----------------------------------------------------------


def _pagina_2_categorias():
    """4 células em 2 linhas; Limpeza (2) + Bebidas (2)."""
    slots = []
    for i, (x, y) in enumerate([(10, 10), (60, 10), (10, 60), (60, 60)]):
        slots.append(Slot(f"cel_{i}", [
            Regiao(TipoRegiao.NOME, Retangulo(x, y + 22, 30, 8), nome="Nome"),
            Regiao(TipoRegiao.PRECO, Retangulo(x, y + 31, 30, 8), nome="Preço"),
        ]))
    pag = Pagina(slots, secoes_ligadas=True)
    lay = LayoutDef(110, 110, dpi=DPI, paginas=[pag])
    dados = {}
    for i, cat in enumerate(["Limpeza", "Limpeza", "Bebidas", "Bebidas"]):
        dados[f"cel_{i}"] = DadosProduto(f"Item {i}",
                                         preco_por=Decimal("9.99"),
                                         categoria=cat)
    return lay, pag, dados


def _compor_com_estilo(monkeypatch, estilo, por_cat=False):
    import app.rendering.compositor as comp_mod
    import app.rendering.secoes as sec_mod

    monkeypatch.setattr(sec_mod, "estilo_secoes", lambda raiz=None: (estilo, por_cat))
    monkeypatch.setattr(sec_mod, "config_secoes",
                        lambda raiz=None: ("#1D4ED8", 0.8))
    lay, pag, dados = _pagina_2_categorias()
    return comp_mod.compor_pagina(lay, pag, dados)


def test_estilos_de_secao_mudam_o_desenho(monkeypatch, raiz_tmp):
    contorno = _compor_com_estilo(monkeypatch, "CONTORNO")
    pill = _compor_com_estilo(monkeypatch, "PILL")
    so_titulo = _compor_com_estilo(monkeypatch, "SO_TITULO")
    assert contorno.tobytes() != pill.tobytes()
    assert contorno.tobytes() != so_titulo.tobytes()
    assert pill.tobytes() != so_titulo.tobytes()


def test_agrupar_sem_desenhar_e_byte_identico_ao_desligado(monkeypatch,
                                                           raiz_tmp):
    """RG-31: o modo do dono — agrupa (ordenação) sem desenhar NADA."""
    sem = _compor_com_estilo(monkeypatch, "SEM_DESENHO")
    lay, pag, dados = _pagina_2_categorias()
    pag.secoes_ligadas = False
    desligado = compor_pagina(lay, pag, dados)
    assert sem.tobytes() == desligado.tobytes()


def test_cor_por_categoria_e_estavel_e_diferente(monkeypatch, raiz_tmp):
    from app.rendering.secoes import cor_da_categoria

    assert cor_da_categoria("Limpeza") == cor_da_categoria("Limpeza")
    assert cor_da_categoria("Limpeza") != cor_da_categoria("Bebidas")
    unica = _compor_com_estilo(monkeypatch, "CONTORNO", por_cat=False)
    por_cat = _compor_com_estilo(monkeypatch, "CONTORNO", por_cat=True)
    assert unica.tobytes() != por_cat.tobytes()   # a paleta rendeu


def test_titulo_mora_dentro_do_retangulo(monkeypatch, raiz_tmp):
    """A cura do bug da captura: a etiqueta não invade a célula DE CIMA.

    Acima do topo da seção (y < 10mm - margem) não pode haver tinta azul."""
    img = _compor_com_estilo(monkeypatch, "CONTORNO")
    topo_secao_px = round((10 - 1.0 - 0.9) * PX_MM)   # topo - margem - traço
    for y in range(0, max(1, topo_secao_px)):
        for x in range(0, img.width, 3):
            r, g, b = img.getpixel((x, y))[:3]
            assert not (b > 150 and r < 100), \
                f"tinta da seção ACIMA do bloco em ({x},{y}) — etiqueta a cavalo?"


# --- RG-33: gestor de selos personalizados --------------------------------------------


def _registrar_selo(raiz, nome="Muito Barato", cor="#FF00FF"):
    from app.qt.telas import servico

    arte = raiz.raiz / f"arte_{nome}.png"
    Image.new("RGBA", (80, 80), cor).save(arte)
    servico.adicionar_selo_personalizado(nome, str(arte))
    return nome


def test_gestor_adiciona_lista_e_remove(raiz_tmp):
    from app.qt.telas import servico

    _registrar_selo(raiz_tmp, "Muito Barato")
    _registrar_selo(raiz_tmp, "Destaque")
    nomes = [r["nome"] for r in servico.selos_disponiveis()]
    assert nomes == ["Muito Barato", "Destaque"]
    assert (raiz_tmp.selos / "muito_barato.png").exists()   # normalizado PNG
    servico.remover_selo_personalizado("Muito Barato")
    nomes = [r["nome"] for r in servico.selos_disponiveis()]
    assert nomes == ["Destaque"]
    # nome removido do gestor não quebra o item que o usava (some quieto
    # DO DESENHO — o item continua listando; o gestor é a fonte)
    assert servico.selos_do_item(["Muito Barato", "Destaque"]) != []


def test_selo_personalizado_desenha_por_conteudo(raiz_tmp):
    """O selo do dono aparece NO CANTO configurado — por pixel."""
    from app.qt.telas import servico

    _registrar_selo(raiz_tmp, "Barato", cor="#FF00FF")
    extras = servico.selos_do_item(["Barato"])
    assert len(extras) == 1
    reg_img = Regiao(TipoRegiao.IMAGEM, Retangulo(10, 10, 60, 60), nome="Img")
    lay = LayoutDef(100, 100, dpi=DPI,
                    paginas=[Pagina([Slot("c", [reg_img])])])
    d = DadosProduto("Produto", preco_por=Decimal("1.00"),
                     selos_extra=extras)
    img = compor_pagina(lay, lay.paginas[0], {"c": d})
    # canto SUPERIOR_DIREITO da âncora (a região de imagem): magenta lá
    x = round((10 + 60) * PX_MM) - 20
    y = round(10 * PX_MM) + 20
    r, g, b = img.getpixel((x, y))[:3]
    assert r > 200 and b > 200 and g < 80      # o magenta do selo


def test_lei_da_casa_selo_nao_vira_slot_nem_pendencia(raiz_tmp):
    """LEI DA CASA (4ª aplicação): selo é DECORATIVO — ocupável e pré-voo
    nem sabem que ele existe."""
    from app.qt.telas import servico
    from app.rendering.grade import ocupaveis

    _registrar_selo(raiz_tmp, "Destaque")
    reg_img = Regiao(TipoRegiao.IMAGEM, Retangulo(10, 10, 60, 60), nome="Img")
    lay = LayoutDef(100, 100, dpi=DPI,
                    paginas=[Pagina([Slot("c", [reg_img])])])
    antes = [s.id for s in ocupaveis(lay.paginas[0].slots)]
    foto = raiz_tmp.raiz / "foto.png"
    Image.new("RGB", (60, 60), "#123456").save(foto)
    d_sem = DadosProduto("P", preco_por=Decimal("1"), imagem_path=str(foto))
    d_com = DadosProduto("P", preco_por=Decimal("1"), imagem_path=str(foto),
                         selos_extra=servico.selos_do_item(["Destaque"]))
    depois = [s.id for s in ocupaveis(lay.paginas[0].slots)]
    assert antes == depois                     # ocupável imune
    avisos_sem = servico.validar_composicao(lay, {"c": d_sem})
    avisos_com = servico.validar_composicao(lay, {"c": d_com})
    assert avisos_sem == avisos_com            # pré-voo imune


# --- RG-34: validade da oferta + selo automático --------------------------------------


def test_montar_validade_oferta():
    from app.qt.telas.servico import montar_validade_oferta

    assert montar_validade_oferta("17/07", "24/07") == \
        "OFERTA VÁLIDA DE 17/07 ATÉ 24/07"
    assert montar_validade_oferta(None, "24/07") == "ATÉ 24/07"
    assert montar_validade_oferta("", " 24/07 ") == "ATÉ 24/07"
    assert montar_validade_oferta("17/07", "") is None   # sem fim, sem frase
    assert montar_validade_oferta(None, None) is None


def test_selo_validade_desenha_ambar(raiz_tmp):
    from app.rendering.selos import Canto, Selo

    reg_img = Regiao(TipoRegiao.IMAGEM, Retangulo(10, 10, 60, 60), nome="Img")
    lay = LayoutDef(100, 100, dpi=DPI,
                    paginas=[Pagina([Slot("c", [reg_img])])])
    d = DadosProduto("P", preco_por=Decimal("1"),
                     selos_extra=[Selo("VALIDADE",
                                       Canto.INFERIOR_ESQUERDO)])
    img = compor_pagina(lay, lay.paginas[0], {"c": d})
    x = round(10 * PX_MM) + 20                 # canto inferior esquerdo
    y = round((10 + 60) * PX_MM) - 20
    r, g, b = img.getpixel((x, y))[:3]
    assert r > 150 and g > 60 and b < 90       # o âmbar do badge


# --- RG-32: cartaz — upscale no fluxo + área preenchida -------------------------------


def test_upscale_para_cartaz_amplia_com_cache(raiz_tmp, tmp_path):
    from app.qt.telas import servico

    pequena = tmp_path / "pequena.png"
    Image.new("RGB", (200, 200), "#3366CC").save(pequena)
    avisos: list[str] = []
    saida = servico.upscale_para_cartaz(str(pequena), 1000, avisos.append)
    assert saida != str(pequena)               # ampliou (não mudou a original)
    with Image.open(saida) as im:
        assert min(im.size) >= 800             # 200 × 4 (escala do ampliador)
    assert any("upscale" in a.lower() or "ampli" in a.lower()
               for a in avisos)                # sem modelo: aviso honesto (I2)
    with Image.open(pequena) as im:
        assert im.size == (200, 200)           # a original está intacta

    mtime = Path(saida).stat().st_mtime_ns
    saida2 = servico.upscale_para_cartaz(str(pequena), 1000, avisos.append)
    assert saida2 == saida
    assert Path(saida2).stat().st_mtime_ns == mtime   # cache: não recomputou


def test_upscale_nao_toca_foto_ja_grande(raiz_tmp, tmp_path):
    from app.qt.telas import servico

    grande = tmp_path / "grande.png"
    Image.new("RGB", (1200, 1200), "#CC6633").save(grande)
    saida = servico.upscale_para_cartaz(str(grande), 1000, lambda _m: None)
    assert saida == str(grande)                # já tem resolução: intocada


def test_cartaz_placeholder_preenche_a_area():
    from app.rendering.cartaz import layout_cartaz_exemplo
    from app.rendering.model import TipoRegiao

    lay = layout_cartaz_exemplo()
    reg = next(r for s in lay.paginas[0].slots for r in s.regioes
               if r.tipo == TipoRegiao.IMAGEM)
    assert reg.rect.larg_mm >= 0.8 * lay.largura_mm    # RG-32: sem timidez
    assert reg.rect.alt_mm >= 50


# --- RG-42/43: presets de composição + assistente de preço ----------------------------


def test_sugerir_terminacao_charm():
    from app.qt.telas.servico import sugerir_terminacao

    assert sugerir_terminacao("10,00") == "9,99"    # dígito esquerdo quebra
    assert sugerir_terminacao("5,30") == "5,29"
    assert sugerir_terminacao("5,42") == "5,39"
    assert sugerir_terminacao("5,07") == "4,99"
    assert sugerir_terminacao("9,99") is None       # já é charm
    assert sugerir_terminacao("4,90") is None
    assert sugerir_terminacao("0,00") is None       # nunca sugerir ≤ 0
    assert sugerir_terminacao("abc") is None


def test_ordenar_com_herois():
    from app.qt.telas.servico import ItemMesa, ordenar_com_herois

    fila = [ItemMesa(f"I{i}", p, "VERDE", f"I{i}")
            for i, p in enumerate(["9,99", "0,19", None, "4,50", "1,99"])]
    saida = ordenar_com_herois(fila, 2)
    assert [it.preco for it in saida[:2]] == ["0,19", "1,99"]   # os heróis
    assert len(saida) == len(fila)             # ninguém some
    assert {it.uid for it in saida} == {it.uid for it in fila}
    # sem preço nunca vira herói; n_capa=0 é identidade
    assert ordenar_com_herois(fila, 0) == fila


def test_densidade_da_pagina():
    from app.qt.telas.servico import densidade_da_pagina

    slots = [Slot(f"c{i}", [Regiao(TipoRegiao.NOME,
                                   Retangulo(5, 5 + i * 20, 30, 8))])
             for i in range(4)]
    pag = Pagina(slots)
    dados = {"c0": DadosProduto("A"), "c1": DadosProduto("B")}
    assert densidade_da_pagina(pag, dados) == pytest.approx(0.5)
    assert densidade_da_pagina(Pagina([]), {}) == 0.0


def test_guia_z_so_no_editor_nunca_no_export(raiz_tmp):
    """RG-42: o guia Z é overlay do CANVAS — a composição não muda um byte."""
    from PySide6.QtWidgets import QApplication

    QApplication.instance() or QApplication([])
    lay = LayoutDef(100, 100, dpi=DPI, paginas=[Pagina([
        Slot("c", [Regiao(TipoRegiao.NOME, Retangulo(10, 10, 60, 10))])])])
    dados = {"c": DadosProduto("Produto")}
    sem = compor_pagina(lay, lay.paginas[0], dados)
    from app.qt.canvas import CanvasView
    c = CanvasView()
    c.carregar(lay, DadosProduto("Produto"))
    c.alternar_guia_z()
    assert c.guia_z is True
    com = compor_pagina(lay, lay.paginas[0], dados)
    assert sem.tobytes() == com.tobytes()      # export imune ao overlay


# --- RG-35: Início redesenhado --------------------------------------------------------


def test_dashboard_ofertas_da_semana_e_evento_novo(raiz_tmp, monkeypatch):
    from PySide6.QtWidgets import QApplication, QDialog

    QApplication.instance() or QApplication([])
    from app.qt.telas.dashboard import DashboardTela

    dash = DashboardTela()
    # FASE 2 (passo 9): o "Novo evento" virou EventoDialog (entidade com
    # cor/dia/capa) — o teste mocka o diálogo da casa, não mais o QInputDialog
    import app.qt.telas.evento_dialog as ed_mod

    class _DlgFake:
        DialogCode = QDialog.DialogCode

        def __init__(self, *a, **k):
            pass

        def exec(self):
            return QDialog.DialogCode.Accepted

        def valores(self):
            return ("Sexta Verde", "#16A34A", 4, None)

    monkeypatch.setattr(ed_mod, "EventoDialog", _DlgFake)
    dash._novo_evento()
    assert "Sexta Verde" in dash._eventos_extras()
    dash.recarregar()                          # não estoura com prateleira vazia
    # cabeçalho com faixa de cor monta para qualquer evento
    cab = dash._cabecalho_evento("Quintou", 3)
    assert cab is not None


# --- RG-36: a integração da onda em miniatura (o marco pesado é o selfcheck) ----------


def test_marco_miniatura_fluxo_da_onda5(raiz_tmp, monkeypatch):
    """Heróis + seções PILL/cor + selo do gestor + validade de/até, num
    fluxo só — congela e reabre com o trio conferido por conteúdo."""
    from PySide6.QtWidgets import QApplication

    QApplication.instance() or QApplication([])
    import app.rendering.secoes as sec_mod
    from app.core import projetos as proj_mod
    from app.qt.telas import servico
    from app.qt.telas.mesa import MesaTela
    from app.qt.telas.servico import ItemMesa
    from app.tests.test_adversarial_vinculo import _grade_4

    monkeypatch.setattr(sec_mod, "estilo_secoes",
                        lambda raiz=None: ("PILL", True))
    _registrar_selo(raiz_tmp, "Destaque", cor="#00FFFF")

    mesa = MesaTela()
    mesa.carregar_layout(_grade_4(), None, nome_layout="Marco mini")
    mesa._itens = [ItemMesa(f"IT {i} 100 G", p, "VERDE", f"Item {i}",
                            categoria=c)
                   for i, (p, c) in enumerate([("9,99", "Limpeza"),
                                               ("0,50", "Limpeza"),
                                               ("4,44", "Bebidas"),
                                               ("2,22", "Bebidas")])]
    mesa._itens[1].selos = ["Destaque"]
    mesa._validade = servico.montar_validade_oferta("18/07", "24/07")
    mesa.chk_agrupar.setChecked(True)
    mesa.chk_herois.setChecked(True)
    mesa._auto_preencher()
    assert len(mesa._mapa) == 4
    # o herói (0,50) abriu a página
    from app.rendering.grade import ocupaveis, ordenar_slots_visualmente
    primeiro = ocupaveis(ordenar_slots_visualmente(
        mesa._layout.paginas[0].slots))[0]
    por_uid = {it.uid: it for it in mesa._itens}
    assert por_uid[mesa._mapa[primeiro.id]].preco == "0,50"

    pid = proj_mod.salvar_projeto(
        "Marco mini", "Teste", "TABLOIDE", mesa._layout,
        [it.to_dict() for it in mesa._itens], mesa._validade,
        nome_layout="Marco mini", mapa=mesa._mapa)
    p = proj_mod.abrir_projeto(pid)
    assert p.mapa == mesa._mapa
    assert p.validade_oferta == "OFERTA VÁLIDA DE 18/07 ATÉ 24/07"
    itens_reabertos = [ItemMesa.from_dict(d) for d in p.itens]
    assert any(it.selos == ["Destaque"] for it in itens_reabertos)


def test_linha_por_sobreposicao_vertical():
    """A cura do agrupamento: alturas de bbox diferentes na MESMA linha
    visual não geram união atravessada (o caso da grade real)."""
    from app.rendering.secoes import calcular_secoes

    # célula 0 com bbox ALTO (imagem+nome+preço), célula 1 só preço (baixa,
    # mas verticalmente sobreposta) — mesma linha visual
    s0 = Slot("a", [Regiao(TipoRegiao.IMAGEM, Retangulo(10, 10, 30, 30)),
                    Regiao(TipoRegiao.PRECO, Retangulo(10, 42, 30, 8))])
    s1 = Slot("b", [Regiao(TipoRegiao.PRECO, Retangulo(60, 42, 30, 8))])
    pag = Pagina([s0, s1], secoes_ligadas=True)
    secoes = calcular_secoes(pag, {"a": "Mercearia", "b": "Mercearia"})
    assert len(secoes) == 1
    # com o critério antigo (topo±2mm) seriam 2 sub-retângulos; por
    # sobreposição vertical é 1 bloco só — sem borda cruzando o meio
    assert len(secoes[0].retangulos) == 1

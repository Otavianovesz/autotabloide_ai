"""BLOCO F da ORDEM_F13 — os 7 encartes novos (cada item com o vermelho
antes, L1; gesto pela bancada do A, conteúdo por pixel/byte).

F1: a célula FIXA nasce no modelo (Slot.fixa) — Terça (2), Segunda (1) e
Quarta (3) carregam produto fixo DA PRÓPRIA ARTE e não entram na fila do
auto-preencher. Lei do projeto: todo TIPO NOVO de slot reavalia
"ocupável" E o pré-voo (o fantasma renasceu 2×; a 3ª não nasce).
"""

from pathlib import Path

import pytest
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication

from app.rendering.compositor import DadosProduto
from app.rendering.model import (
    LayoutDef,
    Pagina,
    Regiao,
    Retangulo,
    Slot,
    TipoRegiao,
)
from app.tests import acervo
from app.tests.gestos import clicar, clicar_na_cena, drenar


def _app():
    return QApplication.instance() or QApplication([])


@pytest.fixture()
def raiz_tmp(tmp_path, monkeypatch):
    monkeypatch.setenv("AUTOTABLOIDE_ROOT", str(tmp_path / "raiz"))
    from app.core.database import Database
    from app.core.paths import SystemRoot
    root = SystemRoot(tmp_path / "raiz").criar_estrutura()
    acervo.copiar_fontes_reais(root.fontes)
    Database(root).init().engine.dispose()
    return root


# ---------------------------------------------------------------------------
# F1 · A célula FIXA no modelo (+ ocupável + pré-voo + o gesto RG-56)
# ---------------------------------------------------------------------------


def test_f1_slot_fixa_no_modelo_roundtrip_e_migracao():
    """F1: ``Slot.fixa`` existe, sobrevive ao to_dict/from_dict, e um
    layout ANTIGO (dict sem a chave) carrega ``False`` — campo aditivo,
    no mesmo molde de ``rotacao_graus``/``alinhamento_v``."""
    s = Slot("c1", [], fixa=True)
    d = s.to_dict()
    assert d.get("fixa") is True, "to_dict não leva a chave 'fixa'"
    assert Slot.from_dict(d).fixa is True, "from_dict perde a 'fixa'"
    antigo = {"id": "c2", "regioes": []}          # layout pré-F13/F
    assert Slot.from_dict(antigo).fixa is False, (
        "layout antigo tem de carregar fixa=False (migração aditiva)")


def test_f1_ocupaveis_exclui_celula_fixa():
    """F1: a célula FIXA tem foto/nome/preço (vindos da arte), então pela
    regra antiga ela SERIA ocupável — e o auto-preencher despejaria um
    produto da fila por cima do produto fixo (o choque nº 1 do §13 do
    dossiê). A regra vive num ponto só: ``grade.ocupaveis``."""
    from app.rendering.grade import ocupaveis

    def _cel(x):
        return [Regiao(TipoRegiao.IMAGEM, Retangulo(x, 0, 10, 10)),
                Regiao(TipoRegiao.PRECO, Retangulo(x, 12, 10, 5))]

    livre = Slot("livre", _cel(0))
    fixa = Slot("fixa", _cel(20), fixa=True)
    assert [s.id for s in ocupaveis([livre, fixa])] == ["livre"], (
        "a célula FIXA entrou na lista de ocupáveis — o auto-preencher "
        "vai sobrescrever o produto fixo da arte")


def test_f1_auto_preencher_pula_a_fixa_por_conteudo(raiz_tmp):
    """F1 adversarial (I5): a Mesa REAL com uma célula FIXA GIGANTE entre
    duas livres — armadilha dupla: se o filtro faltar, o D11 (herói →
    maior célula) entrega o herói JUSTAMENTE à fixa. Conferido por
    identidade (uid no mapa), nunca por posição."""
    from app.qt.telas import servico
    from app.qt.telas.mesa import MesaTela
    _app()
    m = MesaTela()
    m.setAttribute(Qt.WidgetAttribute.WA_DontShowOnScreen, True)
    a = servico.ItemMesa("Arroz", "9,90", "VERDE", "Arroz")
    b = servico.ItemMesa("Feijao", "2,99", "VERDE", "Feijão")   # o herói
    m._itens = [a, b]

    def _cel(x, y, w, h):
        return [Regiao(TipoRegiao.NOME, Retangulo(x, y, w, h - 8),
                       nome="Nome"),
                Regiao(TipoRegiao.PRECO,
                       Retangulo(x, y + h - 7, w, 6), nome="Preço")]

    lay = LayoutDef(120, 120, dpi=100, paginas=[Pagina([
        Slot("p1", _cel(10, 10, 30, 25), origem_mm=(10, 10)),
        Slot("p2", _cel(60, 10, 40, 30), origem_mm=(60, 10)),
        Slot("fixona", _cel(10, 45, 100, 65), origem_mm=(10, 45),
             fixa=True),                     # a MAIOR célula da página
    ])])
    m._layout = lay
    m.area.carregar(lay, {})
    m._recarregar_lista()
    m.btn_preencher.setEnabled(bool(m._itens))
    m.resize(1500, 800)
    m.show()
    drenar()
    try:
        m.chk_herois.setChecked(True)
        if m.btn_preencher.isVisible():
            clicar(m.btn_preencher)
        else:
            m._auto_preencher()
        drenar()
        assert "fixona" not in m._mapa, (
            "o auto-preencher despejou um item da fila NA CÉLULA FIXA — "
            "o produto fixo da arte foi coberto (choque nº 1 do §13)")
        assert m._mapa.get("p2") == b.uid, (
            "o herói não foi para a MAIOR célula LIVRE (D11 tem de valer "
            "só entre as livres)")
        assert m._mapa.get("p1") == a.uid, "o outro item não entrou na livre"
    finally:
        m.close()
        drenar()


def test_f1_menu_alterna_celula_fixa_rg56(raiz_tmp):
    """F1 + RG-56: todo estado tem o inverso a UM clique — o menu de
    contexto da célula marca e DESMARCA a fixa, pelo mesmo lugar."""
    from app.qt.canvas import CanvasView
    _app()
    lay = LayoutDef(100, 100, dpi=100, paginas=[Pagina([Slot("c", [
        Regiao(TipoRegiao.NOME, Retangulo(10, 10, 40, 12), nome="Nome"),
        Regiao(TipoRegiao.PRECO, Retangulo(10, 30, 40, 12), nome="Preço"),
    ])])])
    c = CanvasView()
    c.resize(400, 300)
    c.show()
    c.carregar(lay, DadosProduto("x"))
    try:
        nome = lay.paginas[0].slots[0].regioes[0]
        item = next(i for i in c._itens if i.regiao is nome)
        clicar_na_cena(c, item.mapToScene(item._w / 2, item._h / 2))

        menu, acoes = item.montar_menu_contexto()
        alvo = next((x for x in acoes
                     if "auto-preencher" in x.text().lower()), None)
        assert alvo is not None, (
            "o menu não oferece marcar a célula como FIXA (RG-56)")
        acoes[alvo]()
        assert lay.paginas[0].slots[0].fixa is True, (
            "a ação do menu não marcou a célula como fixa")

        # o INVERSO a um clique (RG-56) — repescando item e menu (o
        # canvas pode reconstruir os wrappers após o commit)
        item2 = next(i for i in c._itens if i.regiao is nome)
        menu2, acoes2 = item2.montar_menu_contexto()
        alvo2 = next((x for x in acoes2
                      if "auto-preencher" in x.text().lower()), None)
        assert alvo2 is not None, "o inverso sumiu do menu (RG-56)"
        acoes2[alvo2]()
        assert lay.paginas[0].slots[0].fixa is False, (
            "desmarcar a fixa não devolveu a célula ao auto-preencher")
    finally:
        c.close()
        drenar()


# ---------------------------------------------------------------------------
# F2 · O extrator de geometria dos 7 encartes (+ F6 validade, + F7 oclusão)
# ---------------------------------------------------------------------------


def _pacote():
    """A pasta do acervo do dono (fora do git). A5: sem ela o skip é
    NOMEADO e contado no fim — nunca silencioso."""
    from pathlib import Path
    p = Path(__file__).resolve().parents[2] / "Templates novos"
    if not (p / "artes").exists():
        pytest.skip("REQUER ACERVO DO DONO: a pasta 'Templates novos/' "
                    "(os 7 encartes do pacote Belo Brasil)")
    return p


# (encarte → (células ocupáveis, células fixas, validade rot em graus))
_ESPERADO = {
    "terca-do-pao": (4, 2, 8.0),
    "segunda-frios": (7, 1, 10.0),
    "quarta-das-ofertas": (5, 3, -2.0),
    "quinta-do-peixe": (7, 0, -7.0),
    "sexta-verde": (11, 0, -6.0),
    "sabado-da-carne": (10, 0, 9.0),
}


def test_f2_os_sete_encartes_extraem_do_pacote():
    """F2: a geometria dos geradores (CELLS/COLS/BXS do §13) vira
    LayoutDef por DADOS — o detector por cor devolveria zero ou lixo
    (nenhum encarte novo tem grade de caixa vermelha). Confere célula a
    célula: contagens, FIXAS (F1), página em mm (o BASE 2160×2880 é ×2
    do viewBox ⇒ dpi 192 ⇒ 285,75 × 381 mm) e roundtrip com ids únicos."""
    from app.rendering.encartes import layout_de_encarte
    from app.rendering.grade import ocupaveis
    from app.rendering.model import LayoutDef

    pac = _pacote()
    for chave, (n_ocup, n_fixas, _rot) in _ESPERADO.items():
        lay = layout_de_encarte(chave, pac)
        assert lay.largura_mm == pytest.approx(285.75, abs=0.1), chave
        assert lay.altura_mm == pytest.approx(381.0, abs=0.1), chave
        pag = lay.paginas[0]
        assert pag.arquivo_fundo and "BASE" in pag.arquivo_fundo, (
            f"{chave}: a página não aponta ao BASE.png do pacote")
        ocup = ocupaveis(pag.slots)
        fixas = [s for s in pag.slots if s.fixa]
        assert len(ocup) == n_ocup, (
            f"{chave}: {len(ocup)} ocupáveis, esperava {n_ocup}")
        assert len(fixas) == n_fixas, (
            f"{chave}: {len(fixas)} fixas, esperava {n_fixas}")
        # toda célula de produto (livre ou fixa) tem IMAGEM+NOME por
        # conteúdo — sem isso o auto-preencher/composição não tem onde pôr
        for s in ocup + fixas:
            tipos = {r.tipo for r in s.regioes}
            assert TipoRegiao.IMAGEM in tipos and TipoRegiao.NOME in tipos, (
                f"{chave}/{s.id}: célula sem IMAGEM+NOME")
        # roundtrip: ids únicos (D8.1) e a FIXA sobrevive à serialização
        lay2 = LayoutDef.from_dict(lay.to_dict())
        assert [s.fixa for s in lay2.paginas[0].slots] == \
               [s.fixa for s in pag.slots], f"{chave}: fixa se perdeu"


def test_f2_jornal_tem_caminho_proprio_com_42_celulas():
    """F2/N-04: o Jornal não tem ``id="celula-N"`` nenhum — a geometria
    vem das listas ``ch``/``linha(y, ids)`` do gerador. Duas páginas num
    LayoutDef só (ids únicos entre páginas), 20+22 células, Fica-a-Dica
    (F4, papel DICA) nas duas, seções LIGADAS (F5 — a arte não traz
    seção) e validade nas coordenadas do exemplo que o BASE zera."""
    from app.rendering.encartes import layout_de_encarte
    from app.rendering.grade import ocupaveis
    from app.rendering.model import LayoutDef, PapelTexto, TipoRegiao

    lay = layout_de_encarte("jornal-do-mes", _pacote())
    assert len(lay.paginas) == 2, "o Jornal é p1+p2 num layout só"
    p1, p2 = lay.paginas
    assert len(ocupaveis(p1.slots)) == 20, "p1: 20 células de oferta"
    assert len(ocupaveis(p2.slots)) == 22, "p2: 22 células de oferta"
    for n, pag in ((1, p1), (2, p2)):
        # F13-BIS §3.7.2 (contrato INVERTIDO pela reprovação do dono):
        # as seções ficam DESLIGADAS no Jornal — o contorno padrão é
        # alienígena sobre o papel creme/laranja; as divisórias da
        # própria arte cumprem o N-05, e estilo por encarte é do G
        assert not pag.secoes_ligadas, (
            f"p{n}: seções LIGADAS no Jornal — a BIS §3.7.2 as desligou")
        legais = [r for s in pag.slots for r in s.regioes
                  if r.tipo == TipoRegiao.TEXTO_LEGAL]
        papeis = {r.papel_texto for r in legais}
        assert PapelTexto.DICA in papeis, f"p{n}: sem o Fica-a-Dica (F4)"
        assert PapelTexto.VALIDADE in papeis, (
            f"p{n}: sem validade — o BASE zera o exemplo inteiro e a "
            "data morre (N-04/N-06)")
    # roundtrip valida ids únicos entre as DUAS páginas (D8.1)
    LayoutDef.from_dict(lay.to_dict())


def test_f2_f6_validade_rotacionada_por_encarte():
    """F6/N-06: cada encarte tem a validade NA POSIÇÃO DO SELO da arte,
    com a rotação do selo — papel VALIDADE (RG-58: autopreenchida pela
    campanha; o pré-voo só avisa, trava #3)."""
    from app.rendering.encartes import layout_de_encarte
    from app.rendering.model import PapelTexto, TipoRegiao

    pac = _pacote()
    for chave, (_o, _f, rot) in _ESPERADO.items():
        lay = layout_de_encarte(chave, pac)
        vals = [r for s in lay.paginas[0].slots for r in s.regioes
                if r.tipo == TipoRegiao.TEXTO_LEGAL
                and r.papel_texto == PapelTexto.VALIDADE]
        assert vals, f"{chave}: nenhuma região de VALIDADE"
        assert any(v.rotacao_graus == pytest.approx(rot) for v in vals), (
            f"{chave}: validade sem a rotação do selo da arte ({rot}°)")


def test_f2_f7_selo_da_terca_nao_oclui_o_slot():
    """F7/N-01: o selo fixo de 25% (centro 964,392, R54 no viewBox) está
    GRAVADO no BASE da Terça e invade ~12×60 px do 1º slot de foto do
    combo. O extrator ENCOLHE o slot: nenhum canto da caixa de foto cai
    dentro do círculo do selo (a foto não nasce por baixo do carimbo)."""
    from app.rendering.encartes import layout_de_encarte
    from app.rendering.model import TipoRegiao
    from app.rendering.units import px_para_mm

    lay = layout_de_encarte("terca-do-pao", _pacote())
    cx, cy = px_para_mm(964, 96), px_para_mm(392, 96)
    raio = px_para_mm(54, 96)
    fotos = [r for s in lay.paginas[0].slots for r in s.regioes
             if r.tipo == TipoRegiao.IMAGEM]
    assert fotos, "a Terça extraiu sem nenhuma caixa de foto"
    for r in fotos:
        for px_, py_ in ((r.rect.x_mm, r.rect.y_mm),
                         (r.rect.x_mm + r.rect.larg_mm, r.rect.y_mm),
                         (r.rect.x_mm, r.rect.y_mm + r.rect.alt_mm),
                         (r.rect.x_mm + r.rect.larg_mm,
                          r.rect.y_mm + r.rect.alt_mm)):
            dist = ((px_ - cx) ** 2 + (py_ - cy) ** 2) ** 0.5
            assert dist >= raio, (
                "um slot de foto da Terça nasce POR BAIXO do selo de 25% "
                f"gravado na arte (canto a {dist:.1f} mm do centro; "
                f"raio {raio:.1f} mm) — N-01")


def test_f2_importar_pacote_semeia_os_7_e_copia_fontes(raiz_tmp):
    """F2: a porta de USO — importar o pacote semeia os 7 layouts no
    banco (o Jornal com as 2 páginas; upsert por nome, importar de novo
    não duplica) e copia as fontes .ttf do pacote para a pasta de fontes
    do app (as famílias que as regiões declaram). I3: a arte internada
    (nenhum caminho da pasta do pacote sobra no JSON persistido)."""
    from app.core.database import Database
    from app.rendering.encartes import NOMES_EXIBICAO, importar_pacote
    from app.rendering.persistencia import carregar_layout, listar_layouts

    pac = _pacote()
    db = Database().init()
    try:
        with db.Session() as s:
            criados = importar_pacote(s, pac)
            s.commit()
            assert len(criados) == 7, f"esperava 7 encartes: {criados}"
            rows = listar_layouts(s)
            nomes = {r.nome for r in rows}
            assert set(NOMES_EXIBICAO.values()) <= nomes, (
                f"faltou encarte na biblioteca: {nomes}")
            jornal = next(r for r in rows if r.nome == "Jornal do Mês")
            assert "Templates novos" not in (jornal.estrutura_json or ""), (
                "caminho da pasta do pacote vazou no JSON persistido (I3)")
            lay = carregar_layout(s, jornal.id)
            assert len(lay.paginas) == 2, "o Jornal perdeu uma página"
        # importar DE NOVO não duplica (upsert por nome)
        with db.Session() as s:
            importar_pacote(s, pac)
            s.commit()
            assert len(listar_layouts(s)) == len(rows), (
                "importar o pacote 2× duplicou layouts")
    finally:
        db.engine.dispose()
    assert (raiz_tmp.fontes / "Archivo-Bold.ttf").exists(), (
        "as fontes do pacote não foram copiadas — as regiões declaram "
        "essas famílias e a composição cairia no fallback")


# ---------------------------------------------------------------------------
# F3 · destaque por área NO ENCARTE REAL (validação D11+F1; + F9/F10 no app)
# ---------------------------------------------------------------------------


def test_f3_heroi_vai_ao_banner_da_quarta_real(raiz_tmp):
    """F3: na Quarta das Ofertas REAL o herói (preço mais agressivo) cai
    no BANNER (celula-var-5, a maior célula LIVRE — era o que o gerador
    reservava ao destaque) e NUNCA numa das 3 fixas da Coluna do Dia.
    De quebra prova a ponta do app do F9 (a fixa-3 declara papel
    DESCONTO — % calculado, nunca digitado) e do F10 (nenhuma região da
    Quarta usa a instância Baloo 2 do pacote — o "ã" defeituoso)."""
    from app.qt.telas import servico
    from app.qt.telas.mesa import MesaTela
    from app.rendering.encartes import layout_de_encarte
    from app.rendering.model import PapelTexto, TipoRegiao
    _app()
    lay = layout_de_encarte("quarta-das-ofertas", _pacote())

    fixa3 = next(s for s in lay.paginas[0].slots
                 if s.id == "celula-fixa-3")
    assert any(r.tipo == TipoRegiao.TEXTO_LEGAL
               and r.papel_texto == PapelTexto.DESCONTO
               for r in fixa3.regioes), (
        "a 3ª fixa (Lanche na Chapa) não declara papel DESCONTO — o "
        "'20%' voltaria a ser texto digitado (N-02)")
    assert not any("Baloo" in r.fonte
                   for s in lay.paginas[0].slots for r in s.regioes), (
        "região da Quarta usando a instância Baloo 2 do pacote — o "
        "glifo 'ã' é defeituoso (N-03) e produto variável pode ter 'ã'")

    m = MesaTela()
    m.setAttribute(Qt.WidgetAttribute.WA_DontShowOnScreen, True)
    a = servico.ItemMesa("Arroz", "9,90", "VERDE", "Arroz")
    b = servico.ItemMesa("Feijao", "2,99", "VERDE", "Feijão")   # o herói
    c2 = servico.ItemMesa("Oleo", "5,50", "VERDE", "Óleo")
    m._itens = [a, b, c2]
    m._layout = lay
    m.area.carregar(lay, {})
    m._recarregar_lista()
    m.btn_preencher.setEnabled(bool(m._itens))
    m.resize(1500, 800)
    m.show()
    drenar()
    try:
        m.chk_herois.setChecked(True)
        m._auto_preencher()
        drenar()
        assert m._mapa.get("celula-var-5") == b.uid, (
            "o herói não caiu no banner (a maior célula livre) da "
            "Quarta real — o destaque por área (D11) não valeu no "
            "encarte do pacote")
        assert not any(k.startswith("celula-fixa") for k in m._mapa), (
            "o auto-preencher ocupou uma célula FIXA da Coluna do Dia")
    finally:
        m.close()
        drenar()


# ---------------------------------------------------------------------------
# DoD do Bloco F · os 7 MONTADOS com as ofertas reais, por pixel vs PREVIEW
# ---------------------------------------------------------------------------


def _frac_diferente(a, b, caixa, limiar: int = 24) -> float:
    """Fração dos pixels da caixa (x0, y0, x1, y1) que diferem de verdade
    (>limiar em algum canal) entre duas imagens do MESMO tamanho."""
    import numpy as np
    ca = np.asarray(a.crop(caixa).convert("RGB"), dtype=int)
    cb = np.asarray(b.crop(caixa).convert("RGB"), dtype=int)
    if ca.size == 0:
        return 0.0
    return float((np.abs(ca - cb).max(axis=2) > limiar).mean())


def _bbox_do_slot(slot, dpi) -> tuple:
    """A caixa envolvente das regiões do slot, em px inteiros."""
    from app.rendering.units import mm_para_px
    x0 = min(r.rect.x_mm for r in slot.regioes)
    y0 = min(r.rect.y_mm for r in slot.regioes)
    x1 = max(r.rect.x_mm + r.rect.larg_mm for r in slot.regioes)
    y1 = max(r.rect.y_mm + r.rect.alt_mm for r in slot.regioes)
    return (round(mm_para_px(x0, dpi)), round(mm_para_px(y0, dpi)),
            round(mm_para_px(x1, dpi)), round(mm_para_px(y1, dpi)))


@acervo.requer_arte_quintou
def test_f_dod_os_sete_montados_por_pixel_vs_preview(raiz_tmp, tmp_path):
    """DoD do Bloco F: os 7 encartes MONTADOS no app com as ofertas
    REAIS do Quintou (o padrão-ouro do marco), conferidos POR PIXEL
    contra os PREVIEW do pacote — em cada slot de foto onde o EXEMPLO
    pôs conteúdo (PREVIEW ≠ BASE), a composição do app também põe
    (APP ≠ BASE). A validade ROTACIONADA prova tinta (F6, com vs sem).
    Gera a galeria lado-a-lado (app | PREVIEW) em
    ``saida_f13/galeria_bloco_f/`` para a inspeção VISUAL — o selo
    nunca sai só com a suíte verde."""
    from decimal import Decimal

    from PIL import Image

    from app.core.marco import campanhas_do_marco, itens_reais_da_campanha
    from app.qt.telas import servico
    from app.rendering.compositor import DadosProduto, compor_pagina
    from app.rendering.encartes import (
        _BASES, DPI_VIEWBOX, chaves_do_pacote, layout_de_encarte)
    from app.rendering.grade import ocupaveis, ordenar_slots_visualmente
    from app.rendering.model import PapelTexto, TipoRegiao
    from app.rendering.units import mm_para_px

    pac = _pacote()
    assert set(chaves_do_pacote(pac)) == set(_BASES), (
        "o pacote do dono não está completo nesta máquina")

    q = next(c for c in campanhas_do_marco(acervo.RAIZ_REPO / "arte")[0]
             if c["nome"] == "quintou")
    reais = itens_reais_da_campanha(q)
    assert len(reais) >= 30, "as 30 ofertas reais do Quintou"
    fotos = []
    for i, (nome, _p) in enumerate(reais):
        f = tmp_path / f"of{i}.png"
        acervo.foto_de_bancada(f, ((i * 53) % 256, (i * 97) % 256,
                                   (i * 31) % 256))
        fotos.append(str(f))

    # A5: ancorada na raiz do repo, imune ao CWD
    galeria = acervo.RAIZ_REPO / "saida_f13" / "galeria_bloco_f"
    galeria.mkdir(parents=True, exist_ok=True)
    sem_conteudo_no_preview: list[str] = []
    for chave in sorted(_BASES):
        lay = layout_de_encarte(chave, pac)
        for n_pag, pag in enumerate(lay.paginas, start=1):
            slots_prod = [s for s in
                          ocupaveis(ordenar_slots_visualmente(pag.slots))]
            slots_prod += [s for s in pag.slots if s.fixa]
            dados = {}
            for i, s in enumerate(slots_prod):
                nome, preco = reais[i % len(reais)]
                por = servico.preco_decimal(preco)
                dados[s.id] = DadosProduto(
                    nome.upper(), preco_por=por,
                    preco_de=(por + Decimal("1.00")) if por else None,
                    imagem_path=fotos[i % len(fotos)],
                    unidade="100 g", categoria="Mercearia")
            # F6: a validade REAL da peça nas regiões papel VALIDADE
            vals = [r for s in pag.slots for r in s.regioes
                    if r.tipo == TipoRegiao.TEXTO_LEGAL
                    and r.papel_texto == PapelTexto.VALIDADE]
            for v in vals:
                v.texto_fixo = f"OFERTA VÁLIDA {q['validade']}"

            app_full = compor_pagina(lay, pag, dados)     # 2160×2880
            app_1x = app_full.resize((1080, 1440), Image.LANCZOS)
            base_1x = Image.open(pag.arquivo_fundo).resize(
                (1080, 1440), Image.LANCZOS)
            nome_prev = Path(pag.arquivo_fundo).name \
                .replace("-BASE-2160x2880.png", "-PREVIEW.png") \
                .replace("-BASE.png", "-PREVIEW.png")
            preview = Image.open(
                Path(pag.arquivo_fundo).parent / nome_prev)

            # POR PIXEL, slot a slot — duas réguas:
            # (a) rigorosa, no SLOT DE FOTO: a composição do app nunca
            #     sai vazia onde a tabela diz que a foto mora;
            # (b) cruzada com o PREVIEW, no BBOX DA CÉLULA: onde o
            #     exemplo pôs conteúdo (carimbo/bandeira/placeholder), o
            #     app também põe. O miolo da foto não serve de régua no
            #     PREVIEW: o exemplo usa PLACEHOLDER semitransparente,
            #     invisível por pixel sobre célula de fundo claro.
            for s in slots_prod:
                for r in s.regioes:
                    if r.tipo != TipoRegiao.IMAGEM:
                        continue
                    caixa = (round(mm_para_px(r.rect.x_mm, DPI_VIEWBOX)),
                             round(mm_para_px(r.rect.y_mm, DPI_VIEWBOX)),
                             round(mm_para_px(
                                 r.rect.x_mm + r.rect.larg_mm,
                                 DPI_VIEWBOX)),
                             round(mm_para_px(
                                 r.rect.y_mm + r.rect.alt_mm,
                                 DPI_VIEWBOX)))
                    f_app = _frac_diferente(app_1x, base_1x, caixa)
                    assert f_app > 0.03, (
                        f"{chave} p{n_pag}/{s.id}: o slot de foto saiu "
                        f"VAZIO na composição (dif {f_app:.3f}) — a "
                        "célula da tabela não casa com a arte")
                bbox = _bbox_do_slot(s, DPI_VIEWBOX)
                f_prev = _frac_diferente(preview, base_1x, bbox,
                                         limiar=16)
                f_app_cel = _frac_diferente(app_1x, base_1x, bbox,
                                            limiar=16)
                if f_prev > 0.02:
                    assert f_app_cel > 0.02, (
                        f"{chave} p{n_pag}/{s.id}: o EXEMPLO põe "
                        f"conteúdo na célula (dif {f_prev:.3f}) e o app "
                        f"não pôs (dif {f_app_cel:.3f})")
                else:
                    sem_conteudo_no_preview.append(
                        f"{chave} p{n_pag}/{s.id}")

            # F6 por PIXEL: a validade rotacionada deixa TINTA (com/sem)
            if vals:
                for v in vals:
                    v.texto_fixo = ""
                sem_val = compor_pagina(lay, pag, dados)
                for v in vals:
                    v.texto_fixo = f"OFERTA VÁLIDA {q['validade']}"
                v0 = vals[0]
                m0 = 30                     # a rotação espalha além do rect
                cx0 = round(mm_para_px(v0.rect.x_mm, lay.dpi)) - m0
                cy0 = round(mm_para_px(v0.rect.y_mm, lay.dpi)) - m0
                cx1 = round(mm_para_px(v0.rect.x_mm + v0.rect.larg_mm,
                                       lay.dpi)) + m0
                cy1 = round(mm_para_px(v0.rect.y_mm + v0.rect.alt_mm,
                                       lay.dpi)) + m0
                assert app_full.crop((cx0, cy0, cx1, cy1)).tobytes() != \
                    sem_val.crop((cx0, cy0, cx1, cy1)).tobytes(), (
                    f"{chave} p{n_pag}: a validade rotacionada NÃO "
                    "deixou tinta no selo (F6/N-06)")

            # galeria lado-a-lado (app | PREVIEW) para a inspeção visual
            lado = Image.new("RGB", (1080 * 2 + 8, 1440), "#666666")
            lado.paste(app_1x.convert("RGB"), (0, 0))
            lado.paste(preview.convert("RGB"), (1088, 0))
            sufixo = f"-p{n_pag}" if len(lay.paginas) > 1 else ""
            lado.save(galeria / f"{chave}{sufixo}.png")

    # honestidade da régua: o cruzamento com o PREVIEW tem de valer na
    # esmagadora maioria (uma exceção pontual fica NOMEADA no relatório)
    assert len(sem_conteudo_no_preview) <= 3, (
        "slots demais onde o PREVIEW não difere do BASE — a régua do "
        f"DoD não está medindo nada: {sem_conteudo_no_preview}")

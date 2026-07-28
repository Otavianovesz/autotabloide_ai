"""ORDEM F13-QUARTUSDECIMUS — a foto enche a zona; a unidade nunca se perde.

Q2: o descritor tem DUAS metades — o qualificador ("BB-X", "tinto") é
sacrificável; a UNIDADE ("100 g", "kg") é informação comercial e NUNCA
sai por falta de espaço ("R$ 9,90" sem o kg ao lado de vizinhos "100 g"
lê dez vezes mais caro). Q1: a foto tem de encher a zona — senão é a
ZONA que muda de forma, nunca a foto que encolhe e afunda.
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


# ---------------------------------------------------------------- Q2 --


def test_q2_a_unidade_nunca_sai_pelo_passo_4(tmp_path):
    """Q2 (o caso da Salsicha, na letra): nome que não cabe + descritor
    que é SÓ a unidade ("kg"). O passo 4 antigo derrubava o descritor
    para dar a banda inteira ao nome — e o cliente lia 9,90 por 100 g
    num item vendido por quilo. A regra nova: com unidade no descritor,
    o passo 4 NÃO derruba; o nome encurta (passo 5) e a unidade fica."""
    from app.rendering.model import Regiao, Retangulo, TipoRegiao
    from app.rendering.nome_fit import _norm, precedencia_do_nome
    from app.rendering.units import px_para_mm

    fontes = _fontes_reais(tmp_path)
    dpi = 96

    def _r(x, y, w, h):
        return Retangulo(px_para_mm(x, dpi), px_para_mm(y, dpi),
                         px_para_mm(w, dpi), px_para_mm(h, dpi))

    # caixa de 1 linha; a banda nome+sub comporta 2 — o cenário exato
    # em que o passo 4 antigo vencia e engolia o "kg"
    nome = Regiao(TipoRegiao.NOME, _r(0, 0, 150, 24),
                  fonte="Roboto-Bold.ttf", tamanho_max_pt=13.0,
                  tamanho_min_pt=13.0, sem_hifen=True)
    sub = Regiao(TipoRegiao.SUBTITULO, _r(0, 26, 150, 40),
                 fonte="Roboto-Regular.ttf", tamanho_max_pt=8.0)
    aj = precedencia_do_nome("Salsicha Hot Dog Rezende", "kg", "kg",
                             [nome, sub], dpi, fontes)
    assert aj is not None
    assert not aj.descritor_saiu, (
        "o passo 4 derrubou um descritor COM unidade — a informação "
        "comercial saiu da vitrine (QUARTUSDECIMUS §2)")
    texto_final = f"{aj.nome} {aj.descritor or ''}"
    assert _norm("kg") in _norm(texto_final).split("·")[-1] \
        or "kg" in _norm(aj.descritor or ""), (
        f"o kg sumiu: nome={aj.nome!r} descritor={aj.descritor!r}")


def test_q2_sem_unidade_o_descritor_segue_sacrificavel(tmp_path):
    """A outra metade da regra (§2, passo 6): descritor SEM unidade
    nenhuma ("marca própria") continua sacrificável — a banda inteira
    ainda existe para quem não tem informação comercial a perder."""
    from app.rendering.model import Regiao, Retangulo, TipoRegiao
    from app.rendering.nome_fit import precedencia_do_nome
    from app.rendering.units import px_para_mm

    fontes = _fontes_reais(tmp_path)
    dpi = 96

    def _r(x, y, w, h):
        return Retangulo(px_para_mm(x, dpi), px_para_mm(y, dpi),
                         px_para_mm(w, dpi), px_para_mm(h, dpi))

    nome = Regiao(TipoRegiao.NOME, _r(0, 0, 150, 24),
                  fonte="Roboto-Bold.ttf", tamanho_max_pt=13.0,
                  tamanho_min_pt=13.0, sem_hifen=True)
    sub = Regiao(TipoRegiao.SUBTITULO, _r(0, 26, 150, 40),
                 fonte="Roboto-Regular.ttf", tamanho_max_pt=8.0)
    aj = precedencia_do_nome("Salsicha Hot Dog Rezende", "marca própria",
                             None, [nome, sub], dpi, fontes)
    assert aj is not None
    assert aj.descritor_saiu and aj.descritor is None, (
        "sem unidade o passo 4 devia valer como sempre (banda inteira)")


def test_q2_dividir_descritor_reconhece_as_duas_metades():
    """A função nomeada da regra (L11): qualificador × protegido, nos
    formatos reais do acervo. A metade protegida inclui as SIGLAS DE
    EMBALAGEM (TP, L.V.) — a palavra do dono (adendo NONUS 27/07) vale
    também aqui: "tinto" pode sair, o TP nunca (achado da frota)."""
    from app.rendering.nome_fit import dividir_descritor

    assert dividir_descritor("BB-X · 100 g") == ("BB-X", "100 g")
    assert dividir_descritor("kg") == (None, "kg")
    assert dividir_descritor("tinto TP · 1,5 L") == ("tinto", "TP · 1,5 L")
    assert dividir_descritor("L.V. · 1 L") == (None, "L.V. · 1 L")
    assert dividir_descritor("marca própria") == ("marca própria", None)
    assert dividir_descritor("4x120 g") == (None, "4x120 g")
    assert dividir_descritor("12 un.") == (None, "12 un.")
    assert dividir_descritor(None) == (None, None)
    # a unidade do DADO decide o empate quando a parte não parece peso
    assert dividir_descritor("Bandeja · un", "un") == ("Bandeja", "un")


def test_q2_o_desenho_do_sub_sacrifica_o_qualificador_nunca_a_unidade(
        tmp_path):
    """A 2ª porta da perda: o SUBTITULO estreito elipsava por largura
    ("BB-X · 10…"). O desenho agora corta o QUALIFICADOR e mantém a
    unidade inteira — nunca reticências em cima do número."""
    from app.rendering.model import Regiao, Retangulo, TipoRegiao
    from app.rendering.nome_fit import descritor_que_cabe
    from app.rendering.units import px_para_mm

    fontes = _fontes_reais(tmp_path)
    dpi = 96
    estreita = Regiao(
        TipoRegiao.SUBTITULO,
        Retangulo(0, 0, px_para_mm(52, dpi), px_para_mm(14, dpi)),
        fonte="Roboto-Regular.ttf", tamanho_max_pt=8.0,
        tamanho_min_pt=8.0)
    assert descritor_que_cabe("BB-X Especial da Casa · 100 g", "100 g",
                              estreita, dpi, fontes) == "100 g"
    larga = Regiao(
        TipoRegiao.SUBTITULO,
        Retangulo(0, 0, px_para_mm(300, dpi), px_para_mm(14, dpi)),
        fonte="Roboto-Regular.ttf", tamanho_max_pt=8.0,
        tamanho_min_pt=8.0)
    assert descritor_que_cabe("BB-X · 100 g", "100 g",
                              larga, dpi, fontes) == "BB-X · 100 g"


def test_q2_toda_unidade_e_exibida_nas_8_paginas(tmp_path, monkeypatch):
    """O teste que a ordem pede: nas 8 páginas, todo item que tem
    unidade a exibe — espião no caminho de produção (a precedência é o
    ponto único); falha se qualquer célula com unidade no dado sair sem
    ela, ou se o passo 4 calar um descritor com unidade."""
    _requer_pacote()
    from app.rendering import nome_fit
    from app.rendering.compositor import DadosProduto, compor_pagina
    from app.rendering.encartes import layout_de_encarte
    from app.rendering.model import TipoRegiao
    from app.rendering.nome_fit import _norm

    fontes = _fontes_reais(tmp_path)
    capturas = []
    original = nome_fit.precedencia_do_nome

    def espiao(nome, descritor, unidade, *a, **kw):
        aj = original(nome, descritor, unidade, *a, **kw)
        capturas.append((unidade, aj))
        return aj

    monkeypatch.setattr(nome_fit, "precedencia_do_nome", espiao)

    NOME = "Nome Comprido De Teste Para A Unidade Da Vitrine"
    for chave in _CHAVES_8:
        lay = layout_de_encarte(chave, _PACOTE)
        for pag in lay.paginas:
            alvo = [s for s in pag.slots
                    if any(r.tipo == TipoRegiao.NOME and r.visivel
                           for r in s.regioes)]
            if not alvo:
                continue
            dados = {s.id: DadosProduto(NOME, descritor="BB-X · 100 g",
                                        unidade="100 g")
                     for s in alvo}
            compor_pagina(lay, pag, dados, fontes_dir=fontes, dpi=96)

    assert capturas, "a precedência não rodou — o espião ficou surdo"
    perdas = []
    for unidade, aj in capturas:
        if not unidade or aj is None:
            continue                      # sem sub: a unidade vai no nome
        if aj.descritor_saiu:
            perdas.append("descritor_saiu com unidade no dado")
            continue
        visivel = _norm(f"{aj.nome} {aj.descritor or ''}")
        if _norm(unidade) not in visivel:
            perdas.append(f"nome={aj.nome!r} descritor={aj.descritor!r}")
    assert not perdas, "células que PERDERAM a unidade:\n" + "\n".join(perdas)


# ---------------------------------------------------------------- Q1 --


def test_q1_a_regua_mede_o_que_o_assentar_faria():
    """A régua, pura: foto quadrada em zona alta (o caso da Quarta) dá
    ~56% de área; a garrafa em pé numa zona quadrada dá ~33% — e ESTÁ
    CERTA (enche a altura; o vazio lateral é simétrico). O caso-limite
    vive escrito no teste, como o §6 da ordem manda."""
    from app.rendering.foto_fit import medir_ocupacao

    m = medir_ocupacao(244, 432, 1080, 1080)      # a fixa da Quarta
    assert abs(m.area_frac - 244 / 432) < 0.01    # ~0,56
    assert m.w_frac > 0.99 and m.h_frac < 0.60    # afundada

    g = medir_ocupacao(281, 236, 400, 1000)       # a garrafa do Óleo
    assert g.h_frac > 0.99, "a garrafa enche a altura"
    assert g.area_frac < 0.45                     # e a régua de área reprova
    assert medir_ocupacao(100, 100, 0, 0).area_frac == 0.0


def test_q1_a_garrafa_em_pe_nao_regride(tmp_path):
    """Q7 por teste: foto vertical que JÁ enche a altura da zona não
    ganha área com arranjo nenhum — a guarda do ganho (≥15%) deixa a
    célula em paz. O Óleo de Soja continua dominando a célula dele."""
    from app.rendering.foto_fit import plano_da_celula
    from app.rendering.model import Regiao, Retangulo, TipoRegiao

    foto = Regiao(TipoRegiao.IMAGEM, Retangulo(10, 10, 70, 60),
                  zona_flex=True)
    nome = Regiao(TipoRegiao.NOME, Retangulo(10, 72, 70, 10))
    preco = Regiao(TipoRegiao.PRECO, Retangulo(20, 84, 40, 14))
    plano = plano_da_celula([foto, nome, preco], 400, 1000)
    assert plano is None, (
        f"a garrafa em pé foi mexida ({plano.arranjo}): a adaptação só "
        "vale para quem ganha área de verdade")


def test_q1_as_fixas_da_quarta_enchem_a_zona():
    """O alvo da ordem, no arranjo do ADENDO do dono (foto topo-centro
    usando o resto do espaço): para as fotos reais dele E sondas duras,
    a foto acaba CHEIA — ou a zona nova já aprova direto (área ou
    altura ≥85%), ou o plano conserta; quando há plano, tudo fica no
    bbox da célula e a foto não pisa em texto."""
    _requer_pacote()
    from app.rendering.encartes import layout_de_encarte
    from app.rendering.foto_fit import (FRACAO_CHEIA, medir_ocupacao,
                                        plano_da_celula)
    from app.rendering.model import TipoRegiao

    lay = layout_de_encarte("quarta-das-ofertas", _PACOTE)
    fixas = [s for s in lay.paginas[0].slots if s.id.startswith("celula-fixa")]
    assert len(fixas) == 3
    fotos = [(1080, 1080), (1920, 1080), (1000, 667), (1600, 400)]
    for slot in fixas:
        regs = [r for r in slot.regioes if r.visivel]
        bx0 = min(r.rect.x_mm for r in regs)
        by0 = min(r.rect.y_mm for r in regs)
        bx1 = max(r.rect.x_mm + r.rect.larg_mm for r in regs)
        by1 = max(r.rect.y_mm + r.rect.alt_mm for r in regs)
        rf = next(r for r in slot.regioes if r.tipo == TipoRegiao.IMAGEM)
        for iw, ih in fotos:
            plano = plano_da_celula(slot.regioes, iw, ih)
            rect_ef = plano.rects[rf.uid] if plano is not None else rf.rect
            m = medir_ocupacao(rect_ef.larg_mm, rect_ef.alt_mm, iw, ih)
            assert m.area_frac >= FRACAO_CHEIA \
                or m.h_frac >= FRACAO_CHEIA, (
                f"{slot.id} {iw}x{ih}: área {m.area_frac:.0%} / "
                f"altura {m.h_frac:.0%} — a foto ficou pequena")
            if plano is None:
                continue
            eps = 0.15
            for uid, r in plano.rects.items():
                assert r.x_mm >= bx0 - eps and r.y_mm >= by0 - eps \
                    and r.x_mm + r.larg_mm <= bx1 + eps \
                    and r.y_mm + r.alt_mm <= by1 + eps, (
                    f"{slot.id}: rect {uid} saiu do bbox da célula")
            novo = plano.rects[rf.uid]
            for uid, r in plano.rects.items():
                if uid == rf.uid:
                    continue
                ix = max(0.0, min(novo.x_mm + novo.larg_mm,
                                  r.x_mm + r.larg_mm)
                         - max(novo.x_mm, r.x_mm))
                iy = max(0.0, min(novo.y_mm + novo.alt_mm,
                                  r.y_mm + r.alt_mm)
                         - max(novo.y_mm, r.y_mm))
                assert ix * iy < 1.0, (
                    f"{slot.id}: a foto pisou no texto {uid}")


def test_q1_celula_vestida_nunca_entra_no_plano():
    """A cesta da Terça: ADORNO por cima da foto (o pão assenta ATRÁS
    da borda desenhada). Mesmo FORÇANDO a marca zona_flex, a célula
    vestida fica intocada — a âncora é da arte."""
    _requer_pacote()
    from dataclasses import replace
    from app.rendering.encartes import layout_de_encarte
    from app.rendering.foto_fit import plano_da_celula
    from app.rendering.model import TipoRegiao

    lay = layout_de_encarte("terca-do-pao", _PACOTE)
    cesta = next(s for s in lay.paginas[0].slots
                 if any(r.tipo == TipoRegiao.ADORNO for r in s.regioes)
                 and any(r.tipo == TipoRegiao.IMAGEM for r in s.regioes))
    regs = [replace(r, zona_flex=True) if r.tipo == TipoRegiao.IMAGEM
            else r for r in cesta.regioes]
    assert plano_da_celula(regs, 1920, 1080) is None, (
        "célula com ADORNO entrou no plano — o pão descolaria da cesta")


def test_q1_por_pixel_a_foto_sobe_do_chao(tmp_path):
    """Por conteúdo (I5): a MESMA página da Quarta com a MESMA foto
    AFUNDÁVEL (4:1) no BANNER (célula flex de arranjo lateral — nas
    fixas do adendo o abraço ancora no rodapé de propósito), com e sem
    a marca zona_flex — os bytes diferem, e na versão flex a tinta da
    foto COMEÇA mais alto (o paredão de vazio em cima morre)."""
    _requer_pacote()
    from dataclasses import replace as _rep
    import numpy as np
    from PIL import Image
    from app.rendering.compositor import DadosProduto, compor_pagina
    from app.rendering.encartes import layout_de_encarte
    from app.rendering.model import TipoRegiao
    from app.rendering.units import mm_para_px

    from decimal import Decimal

    fontes = _fontes_reais(tmp_path)
    foto = tmp_path / "larga.png"
    Image.new("RGBA", (1600, 400), (255, 0, 255, 255)).save(foto)

    lay = layout_de_encarte("quarta-das-ofertas", _PACOTE)
    pag = lay.paginas[0]
    banner = next(s for s in pag.slots if s.id == "celula-var-5")
    dados = {banner.id: DadosProduto("Kit Da Casa",
                                     preco_por=Decimal("9.99"),
                                     unidade="900 ml",
                                     imagem_path=str(foto))}
    com_flex = compor_pagina(lay, pag, dados, fontes_dir=fontes, dpi=96)

    for s in pag.slots:
        s.regioes = [_rep(r, zona_flex=False) for r in s.regioes]
    sem_flex = compor_pagina(lay, pag, dados, fontes_dir=fontes, dpi=96)

    assert com_flex.tobytes() != sem_flex.tobytes(), (
        "a marca zona_flex não mudou NADA no pixel — o plano não rodou")
    regs = [r for r in banner.regioes if r.visivel]
    x0 = int(mm_para_px(min(r.rect.x_mm for r in regs), 96))
    y0 = int(mm_para_px(min(r.rect.y_mm for r in regs), 96))
    x1 = int(mm_para_px(max(r.rect.x_mm + r.rect.larg_mm
                            for r in regs), 96))
    y1 = int(mm_para_px(max(r.rect.y_mm + r.rect.alt_mm
                            for r in regs), 96))

    def _topo_magenta(img):
        rec = np.asarray(img)[y0:y1, x0:x1]
        mag = ((rec[:, :, 0] > 200) & (rec[:, :, 1] < 60)
               & (rec[:, :, 2] > 200))
        linhas = np.where(mag.any(axis=1))[0]
        return int(linhas.min()) if linhas.size else 10 ** 6

    topo_flex = _topo_magenta(com_flex)
    topo_afundada = _topo_magenta(sem_flex)
    assert topo_flex < topo_afundada - 5, (
        f"a foto não subiu do chão (flex y={topo_flex} vs "
        f"afundada y={topo_afundada})")


def test_q1_roundtrip_zona_flex():
    """Aditivo de modelo exige roundtrip (I5): a marca sobrevive ao
    to_dict/from_dict e o layout antigo (sem a chave) fica False."""
    from app.rendering.model import Regiao, Retangulo, TipoRegiao

    r = Regiao(TipoRegiao.IMAGEM, Retangulo(0, 0, 10, 10), zona_flex=True)
    d = r.to_dict()
    assert d["zona_flex"] is True
    assert Regiao.from_dict(d).zona_flex is True
    d.pop("zona_flex")
    assert Regiao.from_dict(d).zona_flex is False


# ------------------------------------------------------- Q3 · Q4 · Q6 --


def test_q3_a_pilula_do_desconto_e_verde_como_as_irmas(tmp_path):
    """Q3 por pixel: na coluna fixa da Quarta a cor segue a COLUNA — o
    "20% OFF" do Lanche veste o MESMO verde dos preços-da-semana das
    irmãs, não o laranja das células livres."""
    _requer_pacote()
    import numpy as np
    from app.rendering.compositor import DadosProduto, compor_pagina
    from app.rendering.encartes import layout_de_encarte
    from app.rendering.model import PapelTexto
    from app.rendering.units import mm_para_px

    fontes = _fontes_reais(tmp_path)
    lay = layout_de_encarte("quarta-das-ofertas", _PACOTE)
    pag = lay.paginas[0]
    fixa3 = next(s for s in pag.slots if s.id == "celula-fixa-3")
    reg = next(r for r in fixa3.regioes
               if r.papel_texto == PapelTexto.DESCONTO)
    img = compor_pagina(lay, pag,
                        {fixa3.id: DadosProduto("Lanche na Chapa",
                                                desconto_pct=20)},
                        fontes_dir=fontes, dpi=96)
    x0 = int(mm_para_px(reg.rect.x_mm, 96))
    y0 = int(mm_para_px(reg.rect.y_mm, 96))
    x1 = x0 + int(mm_para_px(reg.rect.larg_mm, 96))
    y1 = y0 + int(mm_para_px(reg.rect.alt_mm, 96))
    rec = np.asarray(img)[y0:y1, x0:x1].astype(int)
    verde = ((abs(rec[:, :, 0] - 0x2E) < 30) & (abs(rec[:, :, 1] - 0x6B) < 30)
             & (abs(rec[:, :, 2] - 0x3F) < 30)).sum()
    laranja = ((abs(rec[:, :, 0] - 0xF5) < 30) & (abs(rec[:, :, 1] - 0x86) < 30)
               & (abs(rec[:, :, 2] - 0x34) < 30)).sum()
    assert verde > 200, f"a pílula não é verde ({verde}px)"
    assert laranja < 30, f"sobrou laranja na fixa ({laranja}px)"


def test_q4_os_dois_formatos_do_desconto():
    """Q4: as duas opções renderizáveis para o dono escolher; o padrão
    provisório segue o desenho de referência do pacote ("20% OFF")."""
    from app.rendering.compositor import formato_do_desconto

    assert formato_do_desconto(20) == "20% OFF"
    assert formato_do_desconto(20, "off") == "20% OFF"
    assert formato_do_desconto(20, "menos") == "-20% no preço"


# ------------------------------------------------- os achados da frota --


def test_frota_o_misto_nunca_vaza_o_bbox():
    """A frota reproduziu a pílula pintando 4,7mm ABAIXO da célula com
    foto ~10:1 (o clamp de fundo faltava no plano misto). Agora: para
    qualquer foto, TODO rect do plano fica dentro do bbox da célula —
    ou o plano é descartado."""
    _requer_pacote()
    from app.rendering.encartes import layout_de_encarte
    from app.rendering.foto_fit import plano_da_celula

    lay = layout_de_encarte("quarta-das-ofertas", _PACOTE)
    fixas = [s for s in lay.paginas[0].slots
             if s.id.startswith("celula-fixa")]
    sondas = [(3000, 300), (4000, 300), (2000, 400), (1080, 1080),
              (300, 3000), (5000, 250)]
    for slot in fixas:
        vis = [r for r in slot.regioes if r.visivel]
        bx0 = min(r.rect.x_mm for r in vis)
        by0 = min(r.rect.y_mm for r in vis)
        bx1 = max(r.rect.x_mm + r.rect.larg_mm for r in vis)
        by1 = max(r.rect.y_mm + r.rect.alt_mm for r in vis)
        for iw, ih in sondas:
            plano = plano_da_celula(slot.regioes, iw, ih)
            if plano is None:
                continue
            eps = 0.15
            for uid, r in plano.rects.items():
                assert r.x_mm >= bx0 - eps and r.y_mm >= by0 - eps \
                    and r.x_mm + r.larg_mm <= bx1 + eps \
                    and r.y_mm + r.alt_mm <= by1 + eps, (
                    f"{slot.id} foto {iw}x{ih} ({plano.arranjo}): o "
                    f"rect {uid} vazou o bbox — tinta na arte vizinha")


def test_frota_a_sigla_de_embalagem_nunca_sai_no_desenho(tmp_path):
    """O TP VOLTA, parte 2 (frota): o corte do qualificador no desenho
    do SUBTITULO estreito preservava só a unidade e o TP sumia — a
    palavra do dono (27/07) vale em TODA porta: a sigla de embalagem é
    metade PROTEGIDA."""
    from app.rendering.model import Regiao, Retangulo, TipoRegiao
    from app.rendering.nome_fit import descritor_que_cabe
    from app.rendering.units import px_para_mm

    fontes = _fontes_reais(tmp_path)
    dpi = 96
    estreita = Regiao(
        TipoRegiao.SUBTITULO,
        Retangulo(0, 0, px_para_mm(70, dpi), px_para_mm(14, dpi)),
        fonte="Roboto-Regular.ttf", tamanho_max_pt=8.0,
        tamanho_min_pt=8.0)
    vai = descritor_que_cabe("uva tinto suave TP · 1,5 L", "1,5 L",
                             estreita, dpi, fontes)
    assert "TP" in vai and "1,5 L" in vai, (
        f"a sigla de embalagem saiu do desenho: {vai!r}")


def test_frota_fixa_com_descritor_qualificador_puro():
    """A fixa duplicava o descritor inteiro em ``unidade`` e o desempate
    classificava "marca própria" como unidade — bloqueando o passo 4.
    A unidade da fixa agora é a METADE protegida do descritor."""
    from app.rendering.compositor import _dados_do_conteudo_fixo

    d = _dados_do_conteudo_fixo({"nome": "Kit Churrasco",
                                 "descritor": "marca própria"})
    assert d.unidade is None
    d2 = _dados_do_conteudo_fixo({"nome": "Mini Salgadinhos",
                                  "descritor": "BB-X · 100 g"})
    assert d2.unidade == "100 g"


def test_frota_o_corte_do_descritor_avisa(tmp_path):
    """I2: o corte do qualificador no desenho nunca é silencioso — a
    revisora (o canal degradado do export) anuncia a MESMA decisão que
    o desenho vai tomar."""
    from app.ai.revisora import _heuristicas
    from app.rendering.compositor import DadosProduto
    from app.rendering.model import (LayoutDef, Pagina, Regiao,
                                     Retangulo, Slot, TipoRegiao)
    from app.rendering.units import px_para_mm

    fontes = _fontes_reais(tmp_path)
    dpi = 96

    def _r(x, y, w, h):
        return Retangulo(px_para_mm(x, dpi), px_para_mm(y, dpi),
                         px_para_mm(w, dpi), px_para_mm(h, dpi))

    nome = Regiao(TipoRegiao.NOME, _r(0, 0, 400, 40),
                  fonte="Roboto-Bold.ttf", tamanho_max_pt=13.0)
    sub = Regiao(TipoRegiao.SUBTITULO, _r(0, 44, 52, 14),
                 fonte="Roboto-Regular.ttf", tamanho_max_pt=8.0,
                 tamanho_min_pt=8.0)
    lay = LayoutDef(200, 100, dpi=dpi, paginas=[
        Pagina([Slot("c", [nome, sub])])])
    avisos = _heuristicas(
        lay,
        {"c": DadosProduto("Salgadinho",
                           descritor="BB-X Especial da Casa · 100 g",
                           unidade="100 g")},
        fontes)
    assert any("descritor não coube" in a for a in avisos), avisos


def test_q6_o_lv_desce_ao_descritor_como_o_tp(tmp_path):
    """Q6: "Leite Integral Parmalat L.V. 1L" — o L.V. (Longa Vida) é
    sigla de embalagem como o TP: desce ao descritor com o peso, e o
    nome sai limpo. Com e sem pontos."""
    from app.rendering.model import Regiao, Retangulo, TipoRegiao
    from app.rendering.nome_fit import precedencia_do_nome
    from app.rendering.units import px_para_mm

    fontes = _fontes_reais(tmp_path)
    dpi = 96

    def _r(x, y, w, h):
        return Retangulo(px_para_mm(x, dpi), px_para_mm(y, dpi),
                         px_para_mm(w, dpi), px_para_mm(h, dpi))

    nome = Regiao(TipoRegiao.NOME, _r(0, 0, 400, 60),
                  fonte="Roboto-Bold.ttf", tamanho_max_pt=14.0)
    sub = Regiao(TipoRegiao.SUBTITULO, _r(0, 64, 400, 18),
                 fonte="Roboto-Regular.ttf", tamanho_max_pt=8.0)
    for cru in ("Leite Integral Parmalat L.V. 1L",
                "Leite Integral Parmalat LV 1L"):
        aj = precedencia_do_nome(cru, None, None, [nome, sub], dpi, fontes)
        assert aj is not None, cru
        assert aj.nome == "Leite Integral Parmalat", (cru, aj.nome)
        assert aj.descritor.endswith("1 L"), (cru, aj.descritor)
        assert "L.V." in aj.descritor or "LV" in aj.descritor, (
            cru, aj.descritor)

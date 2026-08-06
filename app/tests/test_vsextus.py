"""ORDEM F13-VICESIMUS-SEXTUS — o número enche o carimbo (05/08).

L24 — TIPO DENTRO DE ELEMENTO DE ARTE SE DIMENSIONA PELO ELEMENTO:
quando o app escreve dentro de algo que o dono desenhou (o carimbo do
Quintou), o corpo é CALCULADO para preencher a caixa — nunca lido de
``tamanho_max_pt``. Preço curto ganha corpo maior (a variação da
referência); a hierarquia preço÷nome não inverte (≥2,2×).
"""

from pathlib import Path

import pytest


def _fontes_reais(tmp_path):
    from app.tests import acervo
    fontes = tmp_path / "fontes"
    fontes.mkdir()
    acervo.copiar_fontes_reais(fontes)
    return fontes


def test_vsextus_corpo_pela_caixa_vem_da_caixa(tmp_path):
    """L24: o corpo do número vem da CAIXA do carimbo, nunca do
    ``tamanho_max_pt`` da região — e respeita os tetos de largura e de
    altura. A mutação que volta ao max_pt fixo deixa este teste
    vermelho.

    **EDITADO DE PROPÓSITO na TRICESIMUS (errata do arquiteto).** A
    versão original exigia que "0,19" (curto) ganhasse corpo MAIOR que
    "11,91" (longo) na mesma caixa — a VARIAÇÃO por célula. Ela nasceu
    da medição de que "a referência varia 55→80 px"; medido de novo, o
    publicado do dono é CONSTANTE (33 px em 14 dos 15 carimbos), e a
    variação por célula é o mosaico que ele reclamou. Quem governa o
    desenho agora é ``corpo_do_preco_da_pagina`` (o pior caso, um corpo
    só na página — L27), guardado em test_undetricesimus.py e na r13 da
    rede dos oito. Esta função continua sendo a MEDIDA, e é isso que
    este teste guarda."""
    from decimal import Decimal

    from app.rendering.compositor import _rect_px, corpo_pela_caixa
    from app.rendering.model import Regiao, Retangulo, TipoRegiao

    fontes = _fontes_reais(tmp_path)
    nome_f = next(fontes.glob("*.ttf")).name
    reg = Regiao(TipoRegiao.PRECO, Retangulo(10, 10, 28, 16),
                 fonte=nome_f, tamanho_max_pt=34.0,
                 tamanho_centavos_pt=34.0, mostrar_moeda=False,
                 preenche_caixa=True)
    pt_curto, alt_curto = corpo_pela_caixa(reg, Decimal("0.19"), 96, fontes)
    pt_longo, alt_longo = corpo_pela_caixa(reg, Decimal("11.91"), 96, fontes)
    _x, _y, rw, rh = _rect_px(reg.rect, 96)
    assert alt_curto <= rh * 0.85
    assert alt_longo <= rh * 0.85
    assert pt_curto >= pt_longo, (pt_curto, pt_longo)
    # e nenhum dos dois é o max_pt da região (o corpo é da CAIXA)
    assert abs(pt_curto - 34.0) > 1.0
    assert abs(pt_longo - 34.0) > 1.0


def test_vsextus_o_numero_enche_o_carimbo_por_pixel(tmp_path, monkeypatch):
    """A prova da rodada em miniatura (L23+L24): a célula REAL do
    Quintou (layout do banco) composta com "0,19" — a TINTA do número
    ocupa ≥60% da largura do carimbo (o corpo antigo, fixo em 34 pt,
    ocupava ~45% e deixava o carimbo vazio)."""
    from decimal import Decimal

    monkeypatch.setenv("AUTOTABLOIDE_ROOT", str(tmp_path / "raiz"))
    from app.core.database import Database
    from app.core.models import Layout
    from app.core.paths import SystemRoot
    from app.rendering.compositor import DadosProduto, compor_pagina
    from app.rendering.encartes import importar_pacote
    from app.rendering.persistencia import carregar_layout

    fontes = _fontes_reais(tmp_path)
    db = Database(SystemRoot(tmp_path / "raiz")).init()
    try:
        with db.Session() as s:
            importar_pacote(s, Path.cwd() / "Templates novos")
            s.commit()
            nomes = {r.nome: r.id for r in s.query(Layout).all()}
            ldef = carregar_layout(s, nomes["Quintou do Real"])
    finally:
        db.engine.dispose()
    pag = ldef.paginas[0]
    img = compor_pagina(ldef, pag,
                        {"pos-01": DadosProduto(
                            "Teste", preco_por=Decimal("0.19"))},
                        fontes_dir=fontes).convert("RGB")
    esc = img.width / 1080.0
    x0, y0 = round(154 * esc), round(463 * esc)
    x1, y1 = round(266 * esc), round(527 * esc)
    xs = [x for y in range(y0, y1) for x in range(x0, x1)
          if (lambda p: p[0] > 220 and p[1] > 220 and p[2] > 220)(
              img.getpixel((x, y)))]
    assert xs, "nenhum número no carimbo"
    larg_tinta = (max(xs) - min(xs) + 1) / (x1 - x0)
    assert larg_tinta >= 0.60, (
        f"o número ocupa só {larg_tinta:.0%} da largura do carimbo")


def test_vsextus_hierarquia_nao_inverte(tmp_path, monkeypatch):
    """§4: na célula com preço-pela-caixa, o NOME ganha teto pela
    altura real do algarismo (razão ≥2,2×) — o cap-height do nome sai
    no MÁXIMO metade da altura do algarismo, por pixel."""
    from decimal import Decimal

    monkeypatch.setenv("AUTOTABLOIDE_ROOT", str(tmp_path / "raiz"))
    from app.core.database import Database
    from app.core.models import Layout
    from app.core.paths import SystemRoot
    from app.rendering.compositor import DadosProduto, compor_pagina
    from app.rendering.encartes import importar_pacote
    from app.rendering.persistencia import carregar_layout

    fontes = _fontes_reais(tmp_path)
    db = Database(SystemRoot(tmp_path / "raiz")).init()
    try:
        with db.Session() as s:
            importar_pacote(s, Path.cwd() / "Templates novos")
            s.commit()
            nomes = {r.nome: r.id for r in s.query(Layout).all()}
            ldef = carregar_layout(s, nomes["Quintou do Real"])
    finally:
        db.engine.dispose()
    pag = ldef.paginas[0]
    img = compor_pagina(ldef, pag,
                        {"pos-01": DadosProduto(
                            "Ab", preco_por=Decimal("0.19"))},
                        fontes_dir=fontes).convert("RGB")
    esc = img.width / 1080.0

    def _alt_branco(x0, y0, x1, y1):
        ys = [y for y in range(round(y0 * esc), round(y1 * esc))
              for x in range(round(x0 * esc), round(x1 * esc))
              if (lambda p: p[0] > 220 and p[1] > 220 and p[2] > 220)(
                  img.getpixel((x, y)))]
        return (max(ys) - min(ys) + 1) if ys else 0

    alt_preco = _alt_branco(154, 485, 266, 527)   # só o número (sem R$)
    alt_nome = _alt_branco(0, 463, 150, 532)      # a faixa do nome
    assert alt_preco > 0 and alt_nome > 0
    assert alt_nome * 2.0 <= alt_preco, (
        f"a hierarquia inverteu (nome {alt_nome}px × preço {alt_preco}px)")


# ============================================== VICESIMUS-SEPTIMUS
# A ESCADA: cabe? desenha. Não? abrevia. Não? hifeniza. Só então reduz.
# ==================================================================


def test_vseptimus_a_escada_abrevia_antes_de_reduzir(tmp_path):
    """§2: o degrau 2 existia (glossário RG-22) mas fora da cadeia —
    a abreviação era decisão PRÉVIA (abreviava mesmo quando cabia) ou
    nada. Agora: nome completo se couber; se não couber, o abreviado
    do glossário entra ANTES de o corpo ceder."""
    from app.rendering.model import (Alinhamento, AlinhamentoV, Regiao,
                                     Retangulo, TipoRegiao)
    from app.rendering.nome_fit import precedencia_do_nome

    fontes = _fontes_reais(tmp_path)
    nome_f = next(fontes.glob("*.ttf")).name
    # a caixa MEDIDA que discrimina os dois (o completo não cabe nem
    # hifenizado; o abreviado cabe) — sem ela o teste não testa nada
    reg = Regiao(TipoRegiao.NOME, Retangulo(0, 0, 26, 11), fonte=nome_f,
                 tamanho_max_pt=12.0, tamanho_min_pt=8.0,
                 alinhamento=Alinhamento.ESQUERDA,
                 alinhamento_v=AlinhamentoV.TOPO)
    longo = "Achocolatado 3 Corações Tradicional 700 g"
    curto = "Achoc. 3 Corações 700 g"
    aj = precedencia_do_nome(longo, None, None, [reg], 96, fontes,
                             nome_abreviado=curto)
    assert aj is not None and aj.nome == curto, aj
    # e o que CABE inteiro nunca é abreviado (a lei v4 do dono)
    aj2 = precedencia_do_nome("Alface", None, None, [reg], 96, fontes,
                              nome_abreviado="Alf.")
    assert aj2 is None or aj2.nome == "Alface", aj2


def test_vseptimus_o_quintou_hifeniza_e_alinha_no_centro():
    """§2 da SEPTIMUS: o publicado HIFENIZA ("Pau-lista", "Cora-ções")
    — o sem_hifen do T5 nasceu de ler o hífen do PRÓPRIO dono como
    artefato, e isso continua valendo.

    **EDITADO DE PROPÓSITO na TRICESIMUS-PRIMUS (3ª errata do
    arquiteto).** O §1 da SEPTIMUS mandava alinhar à ESQUERDA a partir
    de impressão visual — sem medir. A medição de 40 linhas do
    publicado mostrou o contrário: o `x` inicial varia de 7 a 58 e o
    CENTRO é constante em 74,5–77,0. O nome é CENTRADO na faixa de
    texto (a faixa desta região tem centro em 77,0). Regra sobre a arte
    do dono só nasce de medição — L29."""
    from app.rendering.encartes import layout_de_encarte
    from app.rendering.model import Alinhamento, TipoRegiao

    pacote = Path.cwd() / "Templates novos"
    if not pacote.exists():
        pytest.skip("REQUER ACERVO DO DONO: 'Templates novos/'")
    lay = layout_de_encarte("quintou", pacote)
    nomes = [r for s in lay.paginas[0].slots for r in s.regioes
             if r.tipo == TipoRegiao.NOME and r.visivel]
    assert nomes
    for r in nomes:
        assert r.alinhamento == Alinhamento.CENTRO, r.alinhamento
        assert r.sem_hifen is False, "o Quintou voltou a proibir o hífen"


def test_vseptimus_apostrofo_capitaliza_dos_dois_lados():
    """Menor da ordem: "D'Ajuda" (a marca) virava "D'ajuda"; o
    apóstrofo de POSSE ("Hellmann's") não é tocado."""
    from app.core.sanitize import sanitizar

    assert sanitizar("Mostarda D'Ajuda 200G").nome_sanitizado \
        == "Mostarda D'Ajuda 200g"
    assert "Hellmann's" in sanitizar("Hellmann's Supreme").nome_sanitizado


def test_vsextus_preenche_caixa_sobrevive_ao_banco():
    """O flag persiste (a lição do incidente da QUINTUS: campo novo
    fora do to_dict morre no reimport)."""
    from app.rendering.model import Regiao, Retangulo, TipoRegiao

    r = Regiao(TipoRegiao.PRECO, Retangulo(0, 0, 10, 10),
               preenche_caixa=True)
    volta = Regiao.from_dict(r.to_dict())
    assert volta.preenche_caixa is True
    d = r.to_dict(); d.pop("preenche_caixa")
    assert Regiao.from_dict(d).preenche_caixa is False

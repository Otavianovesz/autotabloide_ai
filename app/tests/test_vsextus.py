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


def test_vsextus_corpo_pela_caixa_curto_maior_que_longo(tmp_path):
    """L24: o corpo vem da CAIXA — "0,19" (curto) ganha corpo MAIOR
    que "11,91" (longo) na mesma caixa, e os dois respeitam os tetos
    (~85% da largura, ~84% da altura). A mutação que volta ao max_pt
    fixo deixa os dois iguais e este teste vermelho."""
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
    assert pt_curto > pt_longo, (pt_curto, pt_longo)
    _x, _y, rw, rh = _rect_px(reg.rect, 96)
    assert alt_curto <= rh * 0.85
    assert alt_longo <= rh * 0.85
    # e nenhum dos dois é o max_pt da região (o corpo é da CAIXA)
    assert abs(pt_curto - 34.0) > 1.0


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

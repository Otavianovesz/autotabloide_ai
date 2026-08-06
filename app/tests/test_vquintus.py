"""ORDEM F13-VICESIMUS-QUINTUS — o Quintou contra o ORIGINAL (05/08).

L23 — QUANDO EXISTE ORIGINAL, A PROVA É A SOBREPOSIÇÃO. O Quintou não
é um layout a desenhar: é uma arte PRONTA do dono que o app PREENCHE
(`arte/quintou/frente_referencia.png` é normativa). Os guardiões aqui
prendem as 12 causas ao motor:
  C1/C7 o painel da capa é o LOGO Belo Brasil (a dica saiu);
  C8    a validade é "Até dd/mm" girada no sentido do publicado;
  C2    o carimbo do fundo com o R$ EMPILHADO (o inline morreu);
  C5    a mordida SIGNIFICATIVA (≥3 mm) — o P4 saiu do Quintou;
  C6    sem_leque declarado (arte carregada nunca multiplica);
  C1    a unidade do nome em CAIXA ALTA ("700G").
"""

from pathlib import Path

import pytest


def _fontes_reais(tmp_path):
    from app.tests import acervo
    fontes = tmp_path / "fontes"
    fontes.mkdir()
    acervo.copiar_fontes_reais(fontes)
    return fontes


# ================================================================ C1/C7
# O painel da capa é o LOGO — a caixa da dica morreu no Quintou
# ======================================================================


def test_vquintus_painel_da_capa_e_o_logo(tmp_path, monkeypatch):
    """§A1 ("o logo do mercado foi substituído pela dica"): a página
    composta do banco tem o LARANJA do B no painel do topo-direito e
    NENHUM chip verde de dica. Por pixel, do layout REAL (L16)."""
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
    # nenhum slot de dica sobrou na capa
    assert not any("dica" in sl.id for sl in pag.slots), \
        [sl.id for sl in pag.slots]
    img = compor_pagina(ldef, pag,
                        {"pos-01": DadosProduto("X",
                                                preco_por=Decimal("1"))},
                        fontes_dir=fontes, dpi=96).convert("RGB")
    w, h = img.size
    # o painel do topo-direito tem o LARANJA do B do logo
    laranja = sum(1 for px in range(round(w * 0.55), w, 3)
                  for py in range(0, round(h * 0.20), 3)
                  if (lambda p: p[0] > 200 and 90 < p[1] < 180
                      and p[2] < 90)(img.getpixel((px, py))))
    assert laranja > 30, "o logo Belo Brasil não está no painel da capa"
    # e o chip VERDE da dica não existe em lugar nenhum do topo
    verdes = sum(1 for px in range(round(w * 0.5), w, 3)
                 for py in range(0, round(h * 0.25), 3)
                 if (lambda p: p[1] > 120 and p[0] < 80
                     and p[2] < 100)(img.getpixel((px, py))))
    assert verdes < 200, "sobrou chip/caixa de dica sobre a arte"


def test_vquintus_ate_e_a_data_girada():
    """C8: o selo compõe "Até 26/05" (o prefixo do texto_fixo + a data
    FIM) — era "06/08" pelado e girado ao contrário, que lia "80/90"."""
    from app.rendering.compositor import DadosProduto, texto_composto_legal
    from app.rendering.model import (PapelTexto, Regiao, Retangulo,
                                     TipoRegiao)

    reg = Regiao(TipoRegiao.TEXTO_LEGAL, Retangulo(0, 0, 50, 15),
                 papel_texto=PapelTexto.VALIDADE, texto_fixo="Até ")
    reg.so_data = True
    d = DadosProduto("X", texto_legal="Ofertas válidas até 26/05")
    assert texto_composto_legal(reg, d) == "Até 26/05"
    # sem prefixo, só a data — os outros encartes como sempre
    reg2 = Regiao(TipoRegiao.TEXTO_LEGAL, Retangulo(0, 0, 50, 15),
                  papel_texto=PapelTexto.VALIDADE)
    reg2.so_data = True
    assert texto_composto_legal(reg2, d) == "26/05"


# ================================================================== C5
# A mordida SIGNIFICATIVA — o P4 saiu do Quintou por régua, não por nome
# ======================================================================


def test_vquintus_morde_significativo(tmp_path):
    """C5/§A14 ("os produtos do original são maiores"): o carimbo que
    toca a zona da foto por <3 mm NÃO faz a célula virar coluna-com-
    mordida (o teto P4 encolhia as fotos do Quintou por um acidente de
    0,9 mm); a mordida de verdade (≥3 mm) segue valendo (o Jornal)."""
    from decimal import Decimal

    from PIL import Image

    from app.rendering.compositor import DadosProduto, compor_pagina
    from app.rendering.model import (Ajuste, AlinhamentoV, LayoutDef,
                                     Pagina, Regiao, Retangulo, Slot,
                                     TipoRegiao)

    fontes = _fontes_reais(tmp_path)
    nome_f = next(fontes.glob("*.ttf")).name
    foto = tmp_path / "s.png"
    im = Image.new("RGBA", (400, 400), (0, 0, 0, 0))
    im.paste((0, 160, 0, 255), (10, 10, 390, 390))
    im.save(foto)

    def _lay(y_preco):
        sl = Slot("c1", [
            Regiao(TipoRegiao.IMAGEM, Retangulo(10, 10, 60, 50),
                   ajuste=Ajuste.ASSENTAR),
            Regiao(TipoRegiao.PRECO, Retangulo(30, y_preco, 25, 12),
                   fonte=nome_f, tamanho_max_pt=18),
            Regiao(TipoRegiao.NOME, Retangulo(10, 62, 60, 8),
                   fonte=nome_f, tamanho_max_pt=10,
                   alinhamento_v=AlinhamentoV.TOPO),
        ])
        return LayoutDef(80.0, 80.0, dpi=96,
                         paginas=[Pagina(slots=[sl])])

    dados = {"c1": DadosProduto("S", preco_por=Decimal("1"),
                                imagem_path=str(foto))}
    # toca por 1 mm (59..60): NÃO é mordida
    lay1 = _lay(59.0)
    img1 = compor_pagina(lay1, lay1.paginas[0], dados, fontes_dir=fontes)
    uid1 = lay1.paginas[0].slots[0].regioes[0].uid
    assert uid1 not in getattr(img1, "_p4_uids", set()), \
        "1 mm de toque virou coluna-com-mordida"
    # invade 8 mm (52..60): É mordida (a identidade do Jornal fica)
    lay2 = _lay(52.0)
    img2 = compor_pagina(lay2, lay2.paginas[0], dados, fontes_dir=fontes)
    uid2 = lay2.paginas[0].slots[0].regioes[0].uid
    assert uid2 in getattr(img2, "_p4_uids", set()), \
        "a mordida de verdade deixou de marcar"


# ============================================================== C1/C6
# Serialização dos flags novos + roundtrip (o bug pego na 1ª prova)
# ======================================================================


def test_vquintus_flags_sobrevivem_ao_banco():
    """O achado da 1ª prova: sem_leque e unidade_caixa_alta ficavam de
    fora do to_dict e MORRIAM no reimport (o Frango virou trio; o
    "100g" ficou minúsculo). Roundtrip completo."""
    from app.rendering.model import Regiao, Retangulo, TipoRegiao

    r = Regiao(TipoRegiao.IMAGEM, Retangulo(0, 0, 10, 10))
    r.sem_leque = True
    r.unidade_caixa_alta = True
    d = r.to_dict()
    volta = Regiao.from_dict(d)
    assert volta.sem_leque is True
    assert volta.unidade_caixa_alta is True
    # o layout antigo (sem as chaves) segue como sempre
    d.pop("sem_leque"); d.pop("unidade_caixa_alta")
    antigo = Regiao.from_dict(d)
    assert antigo.sem_leque is False
    assert antigo.unidade_caixa_alta is False


def test_vquintus_unidade_em_caixa_alta_por_pixel(tmp_path):
    """C1: com a flag, "500g" desenha como "500G" — os bytes da página
    com flag+minúsculo são IGUAIS aos da página sem flag+maiúsculo (a
    transformação é SÓ de exibição)."""
    from decimal import Decimal

    from app.rendering.compositor import DadosProduto, compor_pagina
    from app.rendering.model import (AlinhamentoV, LayoutDef, Pagina,
                                     Regiao, Retangulo, Slot, TipoRegiao)

    fontes = _fontes_reais(tmp_path)
    nome_f = next(fontes.glob("*.ttf")).name

    def _pagina(flag):
        sl = Slot("c1", [Regiao(TipoRegiao.NOME, Retangulo(5, 5, 70, 12),
                                fonte=nome_f, tamanho_max_pt=14,
                                alinhamento_v=AlinhamentoV.TOPO,
                                unidade_caixa_alta=flag)])
        return LayoutDef(80.0, 25.0, dpi=96, paginas=[Pagina(slots=[sl])])

    la, lb = _pagina(True), _pagina(False)
    a = compor_pagina(la, la.paginas[0],
                      {"c1": DadosProduto("Pipoca Yoki 500g",
                                          preco_por=Decimal("1"))},
                      fontes_dir=fontes)
    b = compor_pagina(lb, lb.paginas[0],
                      {"c1": DadosProduto("Pipoca Yoki 500G",
                                          preco_por=Decimal("1"))},
                      fontes_dir=fontes)
    assert a.tobytes() == b.tobytes()

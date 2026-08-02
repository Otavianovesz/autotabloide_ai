"""RODADA JORNAL DO MÊS — BLOCO 2B: o preço-texto SUPER OFERTA (03/08).

A tabela do dono escreve "S. OFERTA" no lugar do preço quando o valor
varia dentro do mês — o cartaz publicado escreve "SUPER OFERTA" dentro
da estrela. O app: (a) descartava a linha (colagem → balde) ou deixava
o lixo "S. OFERTA" no campo numérico (OCR); (b) o único canal de texto
no lugar do preço (multi_preco) desenhava SEM a forma (retornava antes
de `_desenhar_forma_preco`); (c) a estrela "Splash" do Jornal era texto
fixo manual, nunca alimentada pelo item; (d) `descontos_de` era código
morto — nenhum chamador da UI passava `descontos=`.

Decisão do dono: "SUPER OFERTA" por extenso, dentro da forma do preço.
Todos os testes daqui nasceram VERMELHOS no código antigo (L1).
"""

import pytest


# ================================================================== 2B.1
# O reconhecimento: "S. OFERTA"/"S.OFERTA"/"SUPER OFERTA" → canônico
# ======================================================================


def test_preco_texto_oferta_nas_tres_grafias():
    from app.qt.telas.colagem import preco_texto_oferta

    assert preco_texto_oferta("S. OFERTA") == "SUPER OFERTA"
    assert preco_texto_oferta("S.OFERTA") == "SUPER OFERTA"
    assert preco_texto_oferta("SUPER OFERTA") == "SUPER OFERTA"
    assert preco_texto_oferta("super oferta") == "SUPER OFERTA"
    # não-casos: slogan e formatos que já têm dono
    assert preco_texto_oferta("OFERTA DO DIA") is None
    assert preco_texto_oferta("3 por R$ 10,00") is None
    assert preco_texto_oferta("5,99") is None
    assert preco_texto_oferta("") is None
    assert preco_texto_oferta(None) is None


def test_classificar_preco_ocr():
    """A regra nomeada do filtro do import: preço-texto vira multi_preco
    canônico; promoção com mecânica segue como era; número é número.
    (QUINTUSDECIMUS/J18: a tupla ganhou o 3º campo — o "de" riscado.)"""
    from app.qt.telas.servico import classificar_preco_ocr

    assert classificar_preco_ocr("S. OFERTA") == (None, "SUPER OFERTA", None)
    assert classificar_preco_ocr("SUPER OFERTA") \
        == (None, "SUPER OFERTA", None)
    assert classificar_preco_ocr("20% de desconto") \
        == (None, "20% de desconto", None)
    assert classificar_preco_ocr("leve 3 pague 2") \
        == (None, "leve 3 pague 2", None)
    assert classificar_preco_ocr("5,99") == ("5,99", None, None)
    assert classificar_preco_ocr(None) == (None, None, None)


def test_colagem_super_oferta_nao_vai_ao_balde():
    """As duas linhas REAIS do documento — antes, engolidas."""
    from app.qt.telas.colagem import parse_colagem

    balde: list[str] = []
    # como no documento real: a coluna de código T-N em todas as linhas
    linhas = parse_colagem(
        "ARROZ SOMAR e TIO BONINI 5 Kgs T-1 <> S. OFERTA\n"
        "OLEO de SOJA CONCORDIA 900 ml T-1 <> S.OFERTA\n"
        "SABAO PO OMO 1.6 Kgs CAIXETA T-1 ___SUPER OFERTA\n"
        "ACUCAR CRISTAL DOCE DIA 2 Kgs T-2 <> R$ 5,99\n", balde=balde)
    assert balde == [], balde
    assert len(linhas) == 4
    assert linhas[0].multi_preco == "SUPER OFERTA"
    assert linhas[0].nome == "ARROZ SOMAR e TIO BONINI 5 Kgs"
    assert linhas[1].multi_preco == "SUPER OFERTA"
    assert linhas[2].multi_preco == "SUPER OFERTA"
    assert linhas[3].multi_preco is None and linhas[3].preco == "R$ 5,99"


# ================================================================== 2B.2
# A forma atrás do preço-texto (por pixel)
# ======================================================================


def test_preco_texto_ganha_a_forma_por_pixel():
    """O multi_preco pulava `_desenhar_forma_preco` — "SUPER OFERTA"
    saía pelado, sem a pílula/estrela do encarte. A prova: a MESMA
    região com forma pinta pixels da COR da forma; sem forma, não."""
    from app.rendering.compositor import DadosProduto, compor_pagina
    from app.rendering.model import (FormaPreco, LayoutDef, Pagina,
                                     PapelPreco, Regiao, Retangulo, Slot,
                                     TipoRegiao)

    def _pagina(forma):
        reg = Regiao(TipoRegiao.PRECO, Retangulo(2, 2, 46, 14),
                     papel_preco=PapelPreco.UNICO, tamanho_max_pt=14)
        reg.forma_preco = forma
        reg.forma_cor = "#0F783F"
        lay = LayoutDef(50, 18, dpi=100,
                        paginas=[Pagina([Slot("c", [reg])])])
        return compor_pagina(
            lay, lay.paginas[0],
            {"c": DadosProduto("X", multi_preco="SUPER OFERTA")})

    com_forma = _pagina(FormaPreco.PILULA).convert("RGB")
    sem_forma = _pagina(FormaPreco.TEXTO).convert("RGB")
    # a cor da forma (verde) aparece SÓ na versão com forma
    def _tem_verde(img):
        return any(g > 80 and g > r + 30 and g > b + 20
                   for r, g, b in img.getdata())
    assert _tem_verde(com_forma), "a forma não foi pintada atrás do texto"
    assert not _tem_verde(sem_forma)


def test_pre_voo_nao_acusa_sem_preco_no_super_oferta(tmp_path, monkeypatch):
    monkeypatch.setenv("AUTOTABLOIDE_ROOT", str(tmp_path / "raiz"))
    from app.qt.telas import servico
    from app.rendering.compositor import DadosProduto
    from app.rendering.model import (LayoutDef, Pagina, PapelPreco, Regiao,
                                     Retangulo, Slot, TipoRegiao)

    reg = Regiao(TipoRegiao.PRECO, Retangulo(2, 2, 46, 14),
                 papel_preco=PapelPreco.UNICO)
    lay = LayoutDef(50, 18, dpi=100, paginas=[Pagina([Slot("c", [reg])])])
    avisos = servico.validar_composicao(
        lay, {"c": DadosProduto("X", multi_preco="SUPER OFERTA")})
    assert not any("sem preço" in a for a in avisos), avisos


# ================================================================== 2B.3
# A estrela do Jornal alimentada (PapelTexto.OFERTA)
# ======================================================================


def test_papel_oferta_escreve_o_preco_texto():
    from app.rendering.compositor import DadosProduto, texto_composto_legal
    from app.rendering.model import (PapelTexto, Regiao, Retangulo,
                                     TipoRegiao)

    reg = Regiao(tipo=TipoRegiao.TEXTO_LEGAL,
                 rect=Retangulo(0, 0, 40, 40),
                 papel_texto=PapelTexto.OFERTA, texto_fixo="")
    d = DadosProduto(nome="Arroz", multi_preco="SUPER OFERTA")
    assert texto_composto_legal(reg, d) == "SUPER OFERTA"
    # sem dado do item, vale o fixo do dono; sem nada, vazio (forma muda)
    reg2 = Regiao(tipo=TipoRegiao.TEXTO_LEGAL,
                  rect=Retangulo(0, 0, 40, 40),
                  papel_texto=PapelTexto.OFERTA, texto_fixo="OFERTÃO")
    assert texto_composto_legal(reg2, DadosProduto(nome="x")) == "OFERTÃO"
    assert texto_composto_legal(reg, DadosProduto(nome="x")) == ""


def test_papel_oferta_roundtrip():
    from app.rendering.model import (PapelTexto, Regiao, Retangulo,
                                     TipoRegiao)

    reg = Regiao(tipo=TipoRegiao.TEXTO_LEGAL,
                 rect=Retangulo(0, 0, 10, 10),
                 papel_texto=PapelTexto.OFERTA)
    d = reg.to_dict()
    assert d["papel_texto"] == "OFERTA"
    assert Regiao.from_dict(d).papel_texto == PapelTexto.OFERTA


def test_a_estrela_do_jornal_tem_papel_oferta():
    """O gerador do Jornal p1: a região Splash (a estrela SUPER OFERTA
    do modelo) nasce com papel OFERTA — alimentada pelo item do herói."""
    from app.rendering.encartes import _jornal_p1
    from app.rendering.model import FormaPreco, PapelTexto

    slots = _jornal_p1()
    splash = next(r for s in slots for r in s.regioes
                  if r.nome == "Splash")
    assert splash.forma_preco == FormaPreco.MEDALHAO_ESTRELA
    assert splash.papel_texto == PapelTexto.OFERTA


# ================================================================== 2B.4
# descontos_de ressuscitado (a mutação que o mataria fica vermelha)
# ======================================================================


def test_desconto_declarado_chega_ao_item_pelo_chat(tmp_path, monkeypatch):
    """montar_pelo_chat reusa a colagem — o "20 % de desconto" da linha
    do Lanche precisa chegar ao ItemMesa.desconto_pct (era código morto:
    a colagem reconhecia e NENHUM chamador repassava)."""
    monkeypatch.setenv("AUTOTABLOIDE_ROOT", str(tmp_path / "raiz"))
    from app.qt.telas.servico import montar_pelo_chat

    res = montar_pelo_chat("LANCHE NA CHAPA COM 20 % de DESCONTO",
                           lambda *_: None)
    (item,) = res.itens
    assert item.desconto_pct == 20

"""ORDEM F13-UNDETRICESIMUS — o despacho dos dois conflitos (L26).

Os guardiões das leis desta rodada, cada um com a mutação que ele mata:

  §1  o DEGRAU 4 da escada — a marca só se parte quando a alternativa
      seria encolher o texto (a L25 vira preferência ordenada);
  §2  o PISO NÃO CEDE, A CAIXA CEDE — a região cresce, o crescimento é
      declarado, a colisão é erro DURO e nomeado, e o texto nunca vaza;
  §2  piso IGUAL ao teto é defeito de layout — o import recusa;
  §3  a validade é da PÁGINA: nunca dentro de célula de produto;
  §5.4 o carimbo pode estar na ARTE (e sobrevive ao banco).

As regras de composição do §3 (as duas classes, a zona do destaque, o
patamar do preço) moram no ``test_os_oito.py`` — é lá que elas valem
para os oito ao mesmo tempo, que é o ponto da L22.
"""

from pathlib import Path

import pytest


def _fontes_reais(tmp_path):
    from app.tests import acervo
    fontes = tmp_path / "fontes"
    fontes.mkdir()
    acervo.copiar_fontes_reais(fontes)
    return fontes


# ==================================================================== §1
# O DEGRAU 4: parte a marca só quando a alternativa é encolher
# ======================================================================


def test_undetricesimus_marca_parte_so_para_nao_encolher(tmp_path):
    """O despacho do CONFLITO A (L23 × L25).

    Duas caixas, o MESMO nome e o MESMO vocabulário de marcas:
      - na LARGA, "Itaipava" cabe inteira → o hífen não a toca;
      - na ESTREITA, ou parte a marca ou o corpo desaba → parte.
    """
    from app.rendering.text_fit import ajustar_texto

    fontes = _fontes_reais(tmp_path)
    fonte = fontes / "Roboto-Bold.ttf"
    atomos = frozenset({"itaipava"})
    texto = "Cerveja Itaipava"
    dpi = 192

    larga = ajustar_texto(texto, fonte, 420, 120, 20.0, dpi, 9.0,
                          atomos=atomos)
    assert not any(l.rstrip().endswith("-") for l in larga.linhas), \
        f"com folga a marca não se parte: {larga.linhas}"

    estreita = ajustar_texto(texto, fonte, 92, 200, 20.0, dpi, 9.0,
                             atomos=atomos)
    partiu = any(l.rstrip().endswith("-") for l in estreita.linhas)
    protegida = ajustar_texto(texto, fonte, 92, 200, 20.0, dpi, 9.0,
                              atomos=atomos, sem_hifen=True)
    assert partiu, (
        "sem espaço, o degrau 4 parte a marca em vez de encolher: "
        f"{estreita.linhas}")
    assert estreita.tamanho_pt > protegida.tamanho_pt, (
        "e o ganho tem de ser o CORPO — se partir a marca não deixasse "
        "o texto maior, não haveria motivo para partir "
        f"({estreita.tamanho_pt:.1f} vs {protegida.tamanho_pt:.1f} pt)")


# ==================================================================== §2
# A CAIXA CEDE (e quando não pode, é erro DURO e nomeado)
# ======================================================================


def _pagina_de_prova(alt_nome_mm, folga_mm):
    """Uma página com UMA célula: nome apertado e o descritor logo
    abaixo, à distância pedida."""
    from app.rendering.model import (
        LayoutDef, Pagina, Regiao, Retangulo, Slot, TipoRegiao,
    )
    nome = Regiao(TipoRegiao.NOME, Retangulo(10, 40, 60, alt_nome_mm),
                  nome="Nome", fonte="Roboto-Bold.ttf",
                  tamanho_max_pt=18.0, tamanho_min_pt=16.6)
    y_sub = 40 + alt_nome_mm + folga_mm
    sub = Regiao(TipoRegiao.SUBTITULO, Retangulo(10, y_sub, 60, 6),
                 nome="Descritor", fonte="Roboto-Regular.ttf",
                 tamanho_max_pt=10.0, tamanho_min_pt=8.0)
    pg = Pagina(slots=[Slot("celula-1", [nome, sub])])
    # largura da página dos encartes: é ela que dá o piso de 16,6 pt
    return (LayoutDef(285.75, 381.0, dpi=192, paginas=[pg]), nome, sub)


def test_undetricesimus_a_caixa_cresce_e_declara(tmp_path):
    """Com folga embaixo, a região CRESCE — e o crescimento aparece no
    registro (I2: nunca calado)."""
    from app.rendering.compositor import compor_pagina
    from app.qt.telas.servico import ItemMesa, dados_para_desenho

    fontes = _fontes_reais(tmp_path)
    ldef, nome, _sub = _pagina_de_prova(alt_nome_mm=5.0, folga_mm=8.0)
    it = ItemMesa(descricao="Café", preco="9,99", semaforo="VERDE",
                  nome="Café")
    dados = {"celula-1": dados_para_desenho(it, None, None)}

    img = compor_pagina(ldef, ldef.paginas[0], dados, fontes_dir=fontes)
    cresc = getattr(img, "_crescimentos", {})
    assert nome.uid in cresc, "a caixa tinha de crescer para o piso"
    _rotulo, antes, depois = cresc[nome.uid]
    assert depois > antes, f"cresceu de {antes} para {depois} mm"
    # e o que foi desenhado CABE (o único resultado proibido é vazar)
    d = img._texto_desenhado[nome.uid]
    assert d["altura_px"] <= d["rect_alt_px"] + 1, \
        "depois de crescer, o bloco tem de caber na caixa"


def test_undetricesimus_grade_apertada_e_erro_nomeado(tmp_path):
    """Sem folga de nenhum lado, a página NÃO compõe — e a frase diz a
    região, a medida que falta e QUEM está no caminho."""
    from app.rendering.compositor import GradeApertada, compor_pagina
    from app.qt.telas.servico import ItemMesa, dados_para_desenho

    fontes = _fontes_reais(tmp_path)
    ldef, _nome, _sub = _pagina_de_prova(alt_nome_mm=5.0, folga_mm=0.0)
    # e nada acima: o nome começa colado no topo da página
    for s in ldef.paginas[0].slots:
        for r in s.regioes:
            r.rect.y_mm -= 40.0
    it = ItemMesa(descricao="Café", preco="9,99", semaforo="VERDE",
                  nome="Café")
    dados = {"celula-1": dados_para_desenho(it, None, None)}

    with pytest.raises(GradeApertada) as e:
        compor_pagina(ldef, ldef.paginas[0], dados, fontes_dir=fontes)
    msg = str(e.value)
    assert "Nome" in msg and "Descritor" in msg, \
        f"a frase nomeia a região e a vizinha: {msg}"
    assert "mm" in msg and "mais altura" in msg, msg


def test_undetricesimus_pre_voo_ve_a_grade_antes_de_compor(tmp_path):
    """O erro duro não pode chegar ao dono como travamento: o pré-voo
    pergunta ANTES, com a MESMA conta do desenho."""
    from app.ai.revisora import heuristicas_do_pre_voo
    from app.qt.telas.servico import ItemMesa, dados_para_desenho

    fontes = _fontes_reais(tmp_path)
    ldef, _n, _s = _pagina_de_prova(alt_nome_mm=5.0, folga_mm=0.0)
    for s in ldef.paginas[0].slots:
        for r in s.regioes:
            r.rect.y_mm -= 40.0
    it = ItemMesa(descricao="Café", preco="9,99", semaforo="VERDE",
                  nome="Café")
    avisos = heuristicas_do_pre_voo(
        ldef, {"celula-1": dados_para_desenho(it, None, None)}, fontes)
    assert any("mais altura" in a for a in avisos), \
        f"o pré-voo tem de anunciar a grade apertada: {avisos}"


def test_undetricesimus_piso_igual_ao_teto_o_import_recusa():
    """§2: região de texto sem margem de manobra é defeito de LAYOUT —
    o import aponta a região em vez de compor torto."""
    from app.rendering.encartes import regioes_de_piso_travado
    from app.rendering.model import (
        LayoutDef, Pagina, Regiao, Retangulo, Slot, TipoRegiao,
    )

    r = Regiao(TipoRegiao.NOME, Retangulo(0, 0, 40, 10), nome="Nome",
               tamanho_max_pt=12.0, tamanho_min_pt=12.0)
    lay = LayoutDef(100, 100, paginas=[Pagina(slots=[Slot("c1", [r])])])
    achados = regioes_de_piso_travado(lay)
    assert achados and "c1/Nome" in achados[0], achados

    r.tamanho_min_pt = 9.0
    assert not regioes_de_piso_travado(lay), \
        "com margem de manobra, o layout passa"


# ==================================================================== §3
# A VALIDADE É DA PÁGINA
# ======================================================================


def test_undetricesimus_validade_nao_entra_em_celula_de_produto():
    """O defeito das duas células grandes do Peixe: a etiqueta OPCIONAL
    nasce vazia e vinha herdando a data da página. Fora de célula (o
    rodapé, os layouts antigos) o recurso continua valendo — I2."""
    from app.rendering.compositor import DadosProduto, texto_composto_legal
    from app.rendering.model import (
        PapelTexto, Regiao, Retangulo, TipoRegiao,
    )

    etiqueta = Regiao(TipoRegiao.TEXTO_LEGAL, Retangulo(0, 0, 40, 6),
                      nome="Etiqueta", papel_texto=PapelTexto.LIVRE,
                      texto_fixo="")
    d = DadosProduto("Tilápia", texto_legal="Válido até 08/08")

    assert texto_composto_legal(etiqueta, d, em_celula=True) == "", \
        "dentro da célula do produto, a etiqueta vazia fica vazia"
    assert texto_composto_legal(etiqueta, d) == "Válido até 08/08", \
        "fora de célula (rodapé/legado), o recurso segue valendo"


def test_undetricesimus_o_selo_nao_escreve_a_data_duas_vezes():
    """Achado da PRÓPRIA prova desta rodada (o selo da Quinta do Peixe
    saiu "30/0730/07"): o texto_fixo vira PREFIXO da data desde a
    QUINTUS ("Até " + "26/05"), mas quando o fixo JÁ É uma data — um
    projeto antigo, ou o dono digitando no campo — a concatenação
    imprimia a data duas vezes dentro do carimbo. Prefixo é palavra."""
    from app.rendering.compositor import DadosProduto, texto_composto_legal
    from app.rendering.model import (
        PapelTexto, Regiao, Retangulo, TipoRegiao,
    )

    d = DadosProduto("x", texto_legal="Válido somente 30/07")

    selo = Regiao(TipoRegiao.TEXTO_LEGAL, Retangulo(0, 0, 30, 10),
                  papel_texto=PapelTexto.VALIDADE, texto_fixo="30/07")
    selo.so_data = True
    assert texto_composto_legal(selo, d) == "30/07", \
        "data no texto fixo não se soma à data viva"

    com_prefixo = Regiao(TipoRegiao.TEXTO_LEGAL, Retangulo(0, 0, 30, 10),
                         papel_texto=PapelTexto.VALIDADE, texto_fixo="Até ")
    com_prefixo.so_data = True
    assert texto_composto_legal(com_prefixo, d) == "Até 30/07", \
        "o prefixo de palavra (o Quintou) continua valendo"


# ========================================= TRICESIMUS-PRIMUS (3ª errata)
# O nome CENTRADO na faixa, a contagem tabela × página, a variante com OU
# ======================================================================


def test_tricesimus_primus_o_nome_do_quintou_e_centrado():
    """3ª errata (MEDIDA pelo arquiteto em 40 linhas do publicado): o
    `x` inicial varia de 7 a 58 e o CENTRO fica em 74,5–77,0 — o nome é
    centrado na FAIXA DE TEXTO. A caixa desta região já tinha o centro
    em 77; era o alinhamento que estava errado."""
    from app.rendering.encartes import _celula_quintou
    from app.rendering.model import Alinhamento, TipoRegiao

    regs = _celula_quintou(0, 0)
    nome = next(r for r in regs if r.tipo == TipoRegiao.NOME)
    assert nome.alinhamento == Alinhamento.CENTRO, \
        "o nome do Quintou é CENTRADO na faixa (a medição do publicado)"
    # e o ALVO de corpo é o número medido, não uma razão derivada (L29)
    assert nome.alvo_caixa_alta_px == 12.0


def test_tricesimus_primus_alvo_medido_sobrevive_ao_banco():
    from app.rendering.model import Regiao, Retangulo, TipoRegiao

    r = Regiao(TipoRegiao.NOME, Retangulo(0, 0, 20, 10))
    r.alvo_caixa_alta_px = 12.0
    assert Regiao.from_dict(r.to_dict()).alvo_caixa_alta_px == 12.0


def test_tricesimus_primus_a_contagem_tabela_x_pagina():
    """§1: sumiu o MAMÃO FORMOSA da Sexta (12 na tabela, 11 na página).
    O pré-voo passa a contar e NOMEAR quem ficou de fora — a guarda dos
    crônicos 1, 2 e 6. Item RISCADO não conta como falta."""
    from app.qt.telas.servico import ItemMesa, itens_fora_da_pagina

    a = ItemMesa(descricao="Batata Noiva", preco="4,22", semaforo="VERDE",
                 nome="Batata Noiva")
    b = ItemMesa(descricao="Mamão Formosa", preco="6,66", semaforo="VERDE",
                 nome="Mamão Formosa")
    c = ItemMesa(descricao="Alho Roxo", preco="25,00", semaforo="VERDE",
                 nome="Alho Roxo")
    c.riscada = True

    assert itens_fora_da_pagina([a, b, c], {"celula-1": a.uid, }) == \
        [f"a tabela tem 3 itens e a página tem 2 — ficaram de fora: "
         f"“Mamão Formosa”"]
    assert itens_fora_da_pagina([a, b], {"c1": a.uid, "c2": b.uid}) == []


def test_tricesimus_primus_a_variante_usa_ou():
    """§3 / crônico 5: o descritor nunca abre com conector — a variante
    partida ao meio se remonta com OU (a forma da família)."""
    from app.rendering.nome_fit import sem_conector_orfao

    assert sem_conector_orfao("Tomate Salada", "e Italiano") == \
        ("Tomate", "Salada ou Italiano")
    assert sem_conector_orfao("Maçã Fuji", "e Gala") == \
        ("Maçã", "Fuji ou Gala")
    # nome de uma palavra só: o conector vira "ou" e nada se perde
    assert sem_conector_orfao("Mexerica", "e Murcot") == \
        ("Mexerica", "ou Murcot")
    # o "e" no MEIO é frase legítima, não se toca
    assert sem_conector_orfao("Granola", "banana e canela · 250 g") == \
        ("Granola", "banana e canela · 250 g")


def test_tricesimus_primus_o_lote_inventado_saiu_da_arte():
    """§2: "LOTE 01..09" não existe na tabela do dono — num encarte de
    hortifrúti sugere quantidade limitada, que ele não prometeu."""
    from pathlib import Path

    pasta = (Path(__file__).resolve().parents[2] / "Templates novos"
             / "artes" / "sexta-verde")
    if not pasta.exists():
        pytest.skip("REQUER ACERVO DO DONO: 'Templates novos/'")
    for svg in pasta.glob("*.svg"):
        assert "LOTE" not in svg.read_text(encoding="utf-8"), \
            f"{svg.name} ainda tem o rótulo inventado"
    ger = (Path(__file__).resolve().parents[2] / "Templates novos"
           / "geradores" / "gen_verde5.py")
    assert "LOTE 0{" not in ger.read_text(encoding="utf-8"), \
        "o gerador ressuscitaria o LOTE na próxima regeração"


# ================================================================== §5.4
# O CARIMBO NA ARTE (e o roundtrip — a lição do incidente da QUINTUS)
# ======================================================================


# ============================================== TRICESIMUS (errata dupla)
# O PREÇO É CONSTANTE (L27) e a hierarquia tem as DUAS pontas
# ======================================================================


def test_tricesimus_o_corpo_do_preco_e_um_so_na_pagina(tmp_path):
    """L27: o publicado do dono tem 33 px em 14 dos 15 carimbos; o app
    chegou a NOVE tamanhos numa página porque a conta era POR CÉLULA.
    Duas células com preços de larguras diferentes têm de sair com o
    MESMO corpo — o do pior caso."""
    from decimal import Decimal

    from app.rendering.compositor import (
        FormaPreco, corpo_do_preco_da_pagina, corpo_pela_caixa,
    )
    from app.rendering.model import Regiao, Retangulo, TipoRegiao

    fontes = _fontes_reais(tmp_path)

    def _carimbo():
        r = Regiao(TipoRegiao.PRECO, Retangulo(0, 0, 30, 17),
                   fonte="Roboto-Bold.ttf", tamanho_max_pt=34.0,
                   tamanho_centavos_pt=21.0,
                   forma_preco=FormaPreco.TEXTO)
        r.preenche_caixa = True
        r.mostrar_moeda = False
        return r

    curto, longo = _carimbo(), _carimbo()
    pt_curto, _ = corpo_pela_caixa(curto, Decimal("4.90"), 192, fontes)
    pt_longo, _ = corpo_pela_caixa(longo, Decimal("199.00"), 192, fontes)
    assert pt_curto > pt_longo, (
        "a conta POR CÉLULA é justamente a que produz o mosaico "
        f"({pt_curto:.1f} vs {pt_longo:.1f} pt) — é ela que a lei corrige")

    pt_pg, alt_pg = corpo_do_preco_da_pagina(
        [(curto, Decimal("4.90")), (longo, Decimal("199.00"))], 192, fontes)
    assert abs(pt_pg - pt_longo) < 0.01, (
        "o corpo da página é o do PIOR CASO — o preço mais longo manda")
    assert alt_pg > 0


def test_tricesimus_a_hierarquia_tem_as_duas_pontas(tmp_path):
    """§3: a regra antiga dava PISO sem TETO e a razão foi a 3,7×. A
    banda 2,4–2,9 se traduz em corpo pela caixa alta REAL da fonte, e
    as duas pontas têm de sair na ordem certa."""
    from app.rendering.compositor import (
        _altura_caixa_alta, corpo_para_caixa_alta,
    )

    fontes = _fontes_reais(tmp_path)
    alt_algarismo = 60.0                      # px do algarismo do preço

    piso = corpo_para_caixa_alta(fontes, "Roboto-Bold.ttf",
                                 alt_algarismo / 2.9, 192,
                                 nunca_abaixo=True)
    teto = corpo_para_caixa_alta(fontes, "Roboto-Bold.ttf",
                                 alt_algarismo / 2.4, 192)
    assert piso < teto, "o piso da banda é menor que o teto"

    # e as pontas ficam DENTRO da banda (o arredondamento do piso para
    # baixo deixava a razão escapar em 2,91 — medido na 1ª prova)
    for corpo, limite in ((piso, 2.9), (teto, 2.4)):
        cap = _altura_caixa_alta(fontes, "Roboto-Bold.ttf", corpo, 192)
        razao = alt_algarismo / cap
        assert 2.4 - 0.01 <= razao <= 2.9 + 0.01, \
            f"corpo {corpo:.2f} pt dá razão {razao:.2f} (alvo {limite})"


def test_undetricesimus_carimbo_na_arte_sobrevive_ao_banco():
    """Flag novo que não viaja no to_dict morre no reimport (foi assim
    que o Frango virou trio na rodada passada). Roundtrip completo."""
    from app.rendering.model import Regiao, Retangulo, TipoRegiao

    r = Regiao(TipoRegiao.PRECO, Retangulo(0, 0, 20, 10))
    r.carimbo_na_arte = True
    assert Regiao.from_dict(r.to_dict()).carimbo_na_arte is True


def test_undetricesimus_a_sexta_declara_o_oval_gravado():
    """A dívida dos "2 de 11 preços sem carimbo" era da RÉGUA: o oval
    das bancas está gravado no BASE do dono. Agora a página o declara."""
    from app.rendering.encartes import _sexta
    from app.rendering.model import TipoRegiao

    bancas = [s for s in _sexta() if s.id.startswith("celula-banca")]
    assert len(bancas) == 2
    for slot in bancas:
        preco = next(r for r in slot.regioes
                     if r.tipo == TipoRegiao.PRECO)
        assert preco.carimbo_na_arte, \
            f"{slot.id}: o oval gravado tem de estar declarado"

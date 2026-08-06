"""ORDEM F13-BIS — encartes FIÉIS (o Bloco F reprovado na inspeção do
dono; cada conserto com o vermelho antes, L1).

§2 — os transversais do motor:
T1: a FORMA do preço vira conceito de 1ª classe (sete formas no desenho,
    uma no app — texto preto — era o diagnóstico-raiz).
T2: a linha de SUBTÍTULO (descritor: "senepol · m. própria · 100 g")
    não existia. Tipo novo ⇒ a lei do ocupável/pré-voo é reavaliada.
T5: hifenização é o ÚLTIMO recurso — antes reduz o corpo; `sem_hifen`
    por região ("CERVEJA ITAPA-VA" na arte real é prova de artefato).
"""

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
from app.tests import acervo


@pytest.fixture()
def raiz_tmp(tmp_path, monkeypatch):
    monkeypatch.setenv("AUTOTABLOIDE_ROOT", str(tmp_path / "raiz"))
    from app.core.paths import SystemRoot
    root = SystemRoot(tmp_path / "raiz").criar_estrutura()
    acervo.copiar_fontes_reais(root.fontes)
    return root


def _pagina_com(reg, larg=100, alt=100):
    lay = LayoutDef(larg, alt, dpi=100,
                    paginas=[Pagina([Slot("c", [reg])])])
    return lay, lay.paginas[0]


def _pixels_da_cor(img, cor_rgb, tol=30) -> int:
    import numpy as np
    a = np.asarray(img.convert("RGB"), dtype=int)
    return int((np.abs(a - np.array(cor_rgb)).max(axis=2) <= tol).sum())


# ---------------------------------------------------------------------------
# T1 · FormaPreco — a forma é de 1ª classe e sai TINTA de verdade
# ---------------------------------------------------------------------------


def test_t1_forma_preco_no_modelo_roundtrip_e_migracao():
    """T1: ``FormaPreco`` existe no modelo; sobrevive ao roundtrip; e
    região antiga (dict sem a chave) carrega TEXTO — o comportamento de
    sempre, byte-compatível."""
    from app.rendering.model import FormaPreco
    r = Regiao(TipoRegiao.PRECO, Retangulo(0, 0, 40, 20),
               forma_preco=FormaPreco.TAG_ARREDONDADA,
               forma_cor="#E2711D", forma_cor_borda="#5B2A00")
    d = r.to_dict()
    r2 = Regiao.from_dict(d)
    assert r2.forma_preco == FormaPreco.TAG_ARREDONDADA
    assert r2.forma_cor == "#E2711D"
    assert r2.forma_cor_borda == "#5B2A00"
    antigo = {"tipo": "PRECO",
              "rect": {"x_mm": 0, "y_mm": 0, "larg_mm": 40, "alt_mm": 20}}
    assert Regiao.from_dict(antigo).forma_preco == FormaPreco.TEXTO, (
        "região antiga tem de continuar TEXTO (o comportamento de sempre)")


@pytest.mark.parametrize("forma", [
    "TAG_ARREDONDADA", "PILULA", "OVAL", "MEDALHAO_ESTRELA",
    "ETIQUETA_GIRADA", "ETIQUETA_PENDURADA", "CARIMBO",
])
def test_t1_cada_forma_deixa_fundo_colorido_por_pixel(raiz_tmp, forma):
    """T1 por CONTEÚDO: cada forma pinta um FUNDO na cor pedida atrás do
    preço (com TEXTO não existe um único pixel dessa cor). Era o
    diagnóstico-raiz: sete formas no desenho, texto preto no app."""
    from decimal import Decimal

    from app.rendering.model import FormaPreco, SubtipoPreco
    cor = "#D62F1F"
    reg = Regiao(TipoRegiao.PRECO, Retangulo(20, 30, 60, 30),
                 nome="Preço", forma_preco=FormaPreco(forma),
                 forma_cor=cor, cor="#FFFFFF",
                 subtipo_preco=SubtipoPreco.SEPARADO)
    lay, pag = _pagina_com(reg)
    dados = {"c": DadosProduto("Pão", preco_por=Decimal("8.90"))}
    img = compor_pagina(lay, pag, dados)

    reg.forma_preco = FormaPreco.TEXTO
    sem_forma = compor_pagina(lay, pag, dados)

    alvo = (0xD6, 0x2F, 0x1F)
    com = _pixels_da_cor(img, alvo)
    sem = _pixels_da_cor(sem_forma, alvo)
    assert sem < 50, "TEXTO não devia pintar fundo nenhum"
    assert com > 800, (
        f"{forma}: a forma não deixou TINTA de fundo (pixels na cor: "
        f"{com}) — o preço segue texto solto (diagnóstico-raiz do BIS)")


def test_t1_moeda_sobrescrita_dentro_da_forma(raiz_tmp, tmp_path):
    """T1: na forma, o "R$" NUNCA sai órfão numa linha com o número
    noutra (a Segunda saiu com `R$`/`1,98` em linhas separadas
    atravessando a célula) — o subtipo SEPARADO dentro da forma mantém
    tudo numa linha só, e o texto sai na cor do texto da forma."""
    from decimal import Decimal

    from app.rendering.model import FormaPreco, SubtipoPreco
    from app.rendering.units import mm_para_px

    # fundo CINZA: numa página branca, "tinta branca" não prova nada
    fundo = tmp_path / "fundo.png"
    Image.new("RGB", (394, 394), "#808080").save(fundo)

    reg = Regiao(TipoRegiao.PRECO, Retangulo(10, 30, 80, 34),
                 nome="Preço", forma_preco=FormaPreco.MEDALHAO_ESTRELA,
                 forma_cor="#E7B54A", cor="#FFFFFF",
                 subtipo_preco=SubtipoPreco.SEPARADO,
                 centavos_na_base=True)   # a espec do selo: SEM dy
    lay, pag = _pagina_com(reg)
    lay.arquivo_fundo = str(fundo)
    img = compor_pagina(lay, pag,
                        {"c": DadosProduto("Q", preco_por=Decimal("1.98"))})
    # prova por conteúdo, SÓ dentro da caixa da região: tinta branca
    # DENSA (o texto) numa faixa vertical única — texto numa linha, não
    # duas. O limiar de 20 px/linha separa TEXTO do filete interno do
    # medalhão (borda branca fina que cruza cada linha do círculo).
    import numpy as np
    x0 = round(mm_para_px(10, 100))
    y0 = round(mm_para_px(30, 100))
    x1 = round(mm_para_px(90, 100))
    y1 = round(mm_para_px(64, 100))
    a = np.asarray(img.crop((x0, y0, x1, y1)).convert("RGB"), dtype=int)
    h = a.shape[0]
    brancos_por_linha = ((np.abs(a - 255).max(axis=2) <= 40).sum(axis=1))
    # >8 px/linha = TEXTO (glifos finos cruzam ~10-30 px por varredura;
    # o anel tracejado do disco cruza ≤6). Bloco contíguo ≥6 linhas =
    # uma linha de texto; o R$ órfão da Segunda daria DOIS blocos.
    linhas = np.where(brancos_por_linha > 8)[0]
    assert linhas.size, "nenhum texto branco dentro da forma"
    blocos, atual = [], [int(linhas[0])]
    for v in linhas[1:]:
        if v - atual[-1] <= 3:
            atual.append(int(v))
        else:
            blocos.append(atual)
            atual = [int(v)]
    blocos.append(atual)
    grandes = [b for b in blocos if len(b) >= 6]
    assert len(grandes) == 1, (
        f"{len(grandes)} blocos de texto dentro da forma — o R$ saiu "
        "numa linha e o número noutra (o R$ órfão da Segunda)")
    assert len(grandes[0]) <= h * 0.62, (
        "o bloco de texto é alto demais — duas linhas empilhadas "
        "dentro da forma")


# ---------------------------------------------------------------------------
# T2 · SUBTITULO — o descritor vira linha própria
# ---------------------------------------------------------------------------


def test_t2_subtitulo_desenha_o_descritor_por_pixel(raiz_tmp):
    """T2: a região SUBTITULO desenha ``dados.descritor`` (o
    "senepol · m. própria · 100 g" do modelo). Sem descritor, cai na
    unidade; sem os dois, não pinta nada."""
    reg = Regiao(TipoRegiao.SUBTITULO, Retangulo(10, 40, 80, 12),
                 nome="Descritor")
    lay, pag = _pagina_com(reg)
    com = compor_pagina(lay, pag, {"c": DadosProduto(
        "Shoulder", descritor="senepol · m. própria · 100 g")})
    so_unidade = compor_pagina(lay, pag, {"c": DadosProduto(
        "Shoulder", unidade="100 g")})
    vazio = compor_pagina(lay, pag, {"c": DadosProduto("Shoulder")})
    assert com.tobytes() != vazio.tobytes(), (
        "SUBTITULO não desenhou o descritor")
    assert so_unidade.tobytes() != vazio.tobytes(), (
        "sem descritor, o SUBTITULO tinha de cair na unidade")


def test_t2_subtitulo_nao_torna_slot_ocupavel():
    """T2 + a lei do tipo novo: SUBTITULO é DESCRITOR — um slot só com
    subtítulo (decorativo) não pode engolir produto da fila (A7), e o
    slot completo continua ocupável pelos tipos de sempre."""
    from app.rendering.grade import ocupaveis
    so_sub = Slot("deco", [Regiao(TipoRegiao.SUBTITULO,
                                  Retangulo(0, 0, 10, 5))])
    completo = Slot("prod", [
        Regiao(TipoRegiao.IMAGEM, Retangulo(20, 0, 10, 10)),
        Regiao(TipoRegiao.NOME, Retangulo(20, 12, 10, 4)),
        Regiao(TipoRegiao.SUBTITULO, Retangulo(20, 16, 10, 3)),
        Regiao(TipoRegiao.PRECO, Retangulo(20, 20, 10, 5)),
    ])
    assert [s.id for s in ocupaveis([so_sub, completo])] == ["prod"], (
        "slot só-subtítulo entrou na fila (a lei do tipo novo falhou)")


# ---------------------------------------------------------------------------
# T5 · sem_hifen — reduzir o corpo vem ANTES do hífen
# ---------------------------------------------------------------------------


def test_t2_montagem_oficial_leva_o_descritor():
    """T2 na ponta dos DADOS: a montagem OFICIAL item→DadosProduto
    (``dados_para_desenho`` — a lição do Modo Pai: UMA montagem) leva o
    descritor composto do que o item carrega hoje (marca própria +
    unidade). A COND-11 injeta descritores ricos direto."""
    from app.qt.telas import servico
    it = servico.ItemMesa("Shoulder", "4,39", "VERDE", "Shoulder",
                          unidade="100 g", marca_propria=True)
    d = servico.dados_para_desenho(it)
    assert d.descritor == "marca própria · 100 g", (
        f"a montagem oficial não compôs o descritor: {d.descritor!r}")
    it2 = servico.ItemMesa("Carvão", "38,01", "VERDE", "Carvão",
                           unidade="saco 6 kg")
    assert servico.dados_para_desenho(it2).descritor == "saco 6 kg"


def test_t5_sem_hifen_reduz_o_corpo_em_vez_de_partir(raiz_tmp):
    """T5: com ``sem_hifen`` a palavra NUNCA é partida ("CERVEJA
    ITAPA-VA" na arte real) — o ajuste reduz o corpo até a palavra
    caber inteira."""
    from app.rendering.text_fit import ajustar_texto
    fonte = raiz_tmp.fontes / "Roboto-Regular.ttf"
    aj_com = ajustar_texto("CERVEJA ITAIPAVA", fonte, 120, 200, 24.0, 100)
    assert any("-" in ln for ln in aj_com.linhas), (
        "pré-condição do teste: a caixa estreita tinha de forçar hífen "
        "no caminho padrão (senão a prova não prova nada)")
    aj_sem = ajustar_texto("CERVEJA ITAIPAVA", fonte, 120, 200, 24.0, 100,
                           sem_hifen=True)
    assert not any("-" in ln for ln in aj_sem.linhas), (
        "sem_hifen ainda partiu a palavra")
    assert aj_sem.tamanho_pt < 24.0, (
        "sem_hifen tinha de REDUZIR o corpo para a palavra caber")

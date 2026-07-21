"""FASE 9 — Conteúdo & IA II.

A IA como COLEGA: revisora do export (com degradação heurística), sentinela de
preço, caça-duplicatas por chave natural, "nunca inventa" (casos negativos),
chat da oferta reusando a conciliação, manchete/dica, fila com prioridade.

TRÊS REGRAS DURAS testadas: (1) a IA nunca bloqueia o export; (2) nunca inventa
marca/sigla; (3) sem IA, tudo degrada com aviso.
"""

import json
import shutil
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace

import pytest

from app.ai.fake import MotorIAFake
from app.rendering.compositor import DadosProduto


@pytest.fixture()
def raiz_tmp(tmp_path, monkeypatch):
    monkeypatch.setenv("AUTOTABLOIDE_ROOT", str(tmp_path / "raiz"))
    from app.core.database import Database
    from app.core.paths import SystemRoot
    root = SystemRoot(tmp_path / "raiz").criar_estrutura()
    reais = Path("AutoTabloide_System_Root/fontes")
    if reais.exists():
        for f in reais.glob("*.ttf"):
            shutil.copy(f, root.fontes / f.name)
    Database(root).init().engine.dispose()
    return root


# ===========================================================================
# R-081 — IA revisora do export (o flagship)
# ===========================================================================

def test_revisora_visao_pega_preco_trocado():
    """R-081/passo 30+90: com visão, a revisora lê a peça e acusa um preço que
    NÃO bate com os dados do projeto. Prova de mutação: sem a comparação
    lido×esperado, o aviso não sairia."""
    from app.ai.revisora import revisar_export
    dados = {"s0": DadosProduto("Sabonete Dove", preco_por=Decimal("5.90"),
                                categoria="Higiene")}
    fake = MotorIAFake(respostas_visao={
        "revisor de encarte": json.dumps({"precos": ["9,90"]})})
    avisos, deg = revisar_export("peca.png", dados, motor=fake)
    assert any("9,90" in a and "não bate" in a for a in avisos)   # pegou a troca
    assert deg is None                                            # visão rodou


def test_revisora_sem_ia_degrada_heuristica_e_nunca_bloqueia():
    """R-081/passo 22+40 (decisão travada): SEM visão, degrada para heurística COM
    aviso e NUNCA bloqueia. Prova de mutação: sem o ramo de degradação, o aviso
    de heurística não existiria."""
    from app.ai.revisora import revisar_export
    dados = {"s0": DadosProduto("Arroz", preco_por=Decimal("5.00"))}
    avisos, deg = revisar_export("peca.png", dados, motor=None)
    assert deg and "heurística" in deg and "não foi bloqueado" in deg
    # a função sempre devolve (avisos, deg) — nunca levanta, nunca "veta"
    assert isinstance(avisos, list)


def test_revisora_heuristica_de_menor_igual_por():
    """R-081: a heurística acusa 'de' ≤ 'por' (risco PROCON) sem visão."""
    from app.ai.revisora import revisar_export
    dados = {"s0": DadosProduto("Café", preco_por=Decimal("10.00"),
                                preco_de=Decimal("8.00"))}
    avisos, _ = revisar_export("peca.png", dados, motor=None)
    assert any("PROCON" in a for a in avisos)


def test_revisora_nao_altera_o_projeto():
    """Passo 77 (I5): a revisora só LÊ — os dados do projeto ficam intactos."""
    from app.ai.revisora import revisar_export
    d = DadosProduto("Arroz", preco_por=Decimal("5.00"), preco_de=Decimal("7.00"))
    antes = (d.nome, d.preco_por, d.preco_de)
    revisar_export("peca.png", {"s0": d}, motor=None)
    assert (d.nome, d.preco_por, d.preco_de) == antes


# ===========================================================================
# R-078 — sentinela de preço estranho
# ===========================================================================

def test_sentinela_preco_fora_de_faixa():
    """R-078/passo 39: faixa APRENDIDA do acervo; preço fora dela vira aviso."""
    from app.core.sentinela import faixas_por_categoria, preco_suspeito
    acervo = [("Higiene", Decimal(v)) for v in ("2", "3", "4", "5", "6", "7")]
    faixas = faixas_por_categoria(acervo)
    assert preco_suspeito(Decimal("79"), "Higiene", faixas)      # R$79 num sabonete
    assert preco_suspeito(Decimal("4"), "Higiene", faixas) is None   # dentro, silêncio
    assert preco_suspeito(Decimal("79"), "SemFaixa", faixas) is None  # sem amostra


# ===========================================================================
# R-075 — caça-duplicatas por CHAVE NATURAL (I1)
# ===========================================================================

def _prod(id, nome, marca=None, ean=None, excluido=None):
    return SimpleNamespace(id=id, nome_sanitizado=nome, marca=marca, ean=ean,
                           excluido_em=excluido, nome_bruto=nome, aliases=[])


def test_caca_duplicatas_por_chave_natural():
    """R-075/passo 32: mesmo nome+marca = par candidato (o mais antigo é o
    vencedor). Prova de mutação: casar por id/posição não acharia o par."""
    from app.core.deduplicacao import achar_duplicatas
    prods = [_prod(1, "Arroz Tio João 5kg", "Tio João"),
             _prod(5, "arroz tio joão 5kg", "tio joão"),   # mesma chave natural
             _prod(2, "Feijão Carioca 1kg", "Camil")]
    pares = achar_duplicatas(prods)
    assert len(pares) == 1
    assert pares[0].a.id == 1 and pares[0].b.id == 5        # vencedor = mais antigo


def test_caca_duplicatas_nao_funde_marcas_diferentes():
    """R-075/passo 76 (I1, caso NEGATIVO): mesmo nome, marca DIFERENTE → chave
    diferente → NUNCA vira par. É a trava contra fundir dois produtos distintos."""
    from app.core.deduplicacao import achar_duplicatas
    prods = [_prod(1, "Leite Integral 1L", "Italac"),
             _prod(2, "Leite Integral 1L", "Piracanjuba")]
    assert achar_duplicatas(prods) == []


def test_caca_duplicatas_ean_e_lixeira():
    """EAN igual = par (chave forte); produto na lixeira (excluído) é ignorado."""
    from datetime import datetime

    from app.core.deduplicacao import achar_duplicatas
    prods = [_prod(1, "Coca 2L", "Coca-Cola", ean="7891"),
             _prod(2, "Refri Cola 2L", "Coca-Cola", ean="7891"),   # mesmo EAN
             _prod(3, "Coca 2L", "Coca-Cola", ean="7891",
                   excluido=datetime.now())]                       # na lixeira
    pares = achar_duplicatas(prods)
    assert len(pares) == 1 and {pares[0].a.id, pares[0].b.id} == {1, 2}


def test_fundir_no_banco_migra_aliases_e_soft_delete(raiz_tmp):
    """R-075/passo 33+35: fundir migra os aliases para o vencedor e SOFT-DELETE o
    perdedor (reversível, lixeira). Prova de mutação: sem o soft-delete, o
    perdedor seguiria ativo (duplicata viva)."""
    from app.core.database import Database
    from app.core.deduplicacao import fundir_no_banco
    from app.core.models import Produto, ProdutoAlias
    db = Database().init()
    try:
        with db.Session() as s:
            v = Produto(nome_bruto="ARROZ TIO JOAO", nome_sanitizado="Arroz Tio João",
                        marca="Tio João")
            p = Produto(nome_bruto="ARROZ T JOAO", nome_sanitizado="Arroz Tio João",
                        marca="Tio João")
            s.add_all([v, p])
            s.flush()
            s.add(ProdutoAlias(produto_id=p.id, alias_raw="ARROZ TJ"))
            s.flush()
            log = fundir_no_banco(s, v.id, p.id)
            s.commit()
            vid, pid = v.id, p.id
        with db.Session() as s:
            assert s.get(Produto, pid).excluido_em is not None    # perdedor na lixeira
            aliases = [a.alias_raw for a in s.query(ProdutoAlias)
                       .filter_by(produto_id=vid)]
            assert "ARROZ TJ" in aliases and "ARROZ T JOAO" in aliases  # migraram
    finally:
        db.engine.dispose()


# ===========================================================================
# R-087 / R-086 — "nunca inventa" marca; sinônimos regionais
# ===========================================================================

def test_extrair_marca_conhecida_e_nao_inventa():
    """R-087/passo 49+58 (REGRA DURA): a marca sai só se for CONHECIDA; marca
    desconhecida no nome → None (não inventa). Prova de mutação: devolver o 1º
    token como marca inventaria."""
    from app.core.aprendizado import extrair_marca
    conhecidas = ["Tio João", "Camil"]
    assert extrair_marca("Arroz Tio João 5kg", conhecidas) == "Tio João"
    assert extrair_marca("Arroz Xanadu 5kg", conhecidas) is None   # Xanadu ≠ conhecida
    assert extrair_marca("Feijão comum 1kg", conhecidas) is None   # sem marca
    # fronteira de PALAVRA (blindagem apontada pela frota): "Camilo" ≠ "Camil" —
    # substring frouxa inventaria a marca "Camil" para "Arroz Camilo".
    assert extrair_marca("Arroz Camilo 5kg", conhecidas) is None


def test_sinonimos_regionais_mesmo_produto():
    """R-086/passo 59: mandioca/macaxeira/aipim = o mesmo produto; produtos
    diferentes NÃO se confundem."""
    from app.core.aprendizado import canonizar_sinonimos, mesmo_produto_regional
    assert mesmo_produto_regional("Farofa de macaxeira", "Farofa de mandioca")
    assert not mesmo_produto_regional("Farofa de mandioca", "Farofa de milho")
    assert canonizar_sinonimos("Bolo de aipim") == "Bolo de mandioca"


# ===========================================================================
# R-073 / R-074 / R-083 — chat da oferta, manchete, dica
# ===========================================================================

def test_chat_da_oferta_reusa_conciliacao(raiz_tmp):
    """R-073/passo 17: o chat cola/descreve e vira RASCUNHO reusando a conciliação
    (não um pipeline novo); o resumo fala a língua do dono."""
    from app.qt.telas import servico
    res = servico.montar_pelo_chat("Arroz Tio João 5kg\t24,90\n"
                                   "Feijão Carioca 1kg;7,99",
                                   lambda *a, **k: None)
    assert len(res.itens) == 2                       # reusou o parser + conciliação
    resumo = servico.resumo_do_resultado(res)
    assert "novo" in resumo or "casei" in resumo     # transparência


def test_colagem_rejeita_2x_500_em_todas_as_formas():
    """[BUG achado pela frota] o "2x 5,00" PROIBIDO era aceito calado como preço
    "5,00" quando separado por ESPAÇO (WhatsApp) — só a forma em coluna rejeitava.
    Agora TODAS as formas marcam preço a rever (I2 — valor errado é pior que
    ausente). Prova de mutação: sem `_RE_AMBIGUO_FIM`, a linha de espaço passaria."""
    from app.qt.telas.colagem import parse_colagem
    for texto in ("Refrigerante 2L 2x 5,00",        # WhatsApp (espaço)
                  "Refrigerante 2L\t2x 5,00",        # Excel (tab)
                  "Refrigerante 2L;2x 5,00"):        # ponto-e-vírgula
        li = parse_colagem(texto)[0]
        assert not li.preco_valido and li.multi_preco is None    # não é promoção
        assert li.aviso and "não foi entendido" in li.aviso      # avisa (I2)
        assert "2x" in li.nome or "2x" in (li.preco or "")       # o "2x" não some


def test_manchetes_degrada_sem_ia_e_respeita_limite():
    """R-074/passo 8+15: sem IA, manchetes viram lista padrão (degrada); respeita
    o teto da região (não estoura)."""
    from app.ai.enriquecimento import sugerir_manchetes
    ms = sugerir_manchetes("Quintou do Real", motor=None, limite_chars=20)
    assert ms and all(len(m) <= 20 for m in ms)


def test_dica_estilo_respeita_teto_e_nao_repete():
    """R-083/passo 11+12 (reescrito no GATE 2.1 da ordem F11.5 — o corpo
    antigo só checava o teto e o nome MASCARAVA a não-repetição):

    1. o teto de caracteres da região é lei;
    2. sem IA devolve None (degrada, I2);
    3. **NÃO REPETE, por conteúdo**: com `evitar=[dica_anterior]`, um modelo
       que insiste na MESMA dica é BARRADO pela guarda dura (None — nunca a
       repetida); e um modelo que devolve outra dica passa, com a nova ≠
       anterior. Prova de mutação: remover a guarda de `gerar_dica` faz o
       caso do modelo-teimoso devolver a dica repetida e o teste falhar."""
    from app.ai.enriquecimento import gerar_dica
    fake = MotorIAFake(respostas_chat={
        "Fica a Dica": json.dumps({"dica": "Arroz soltinho: refogue o alho antes."})})
    d1 = gerar_dica(["Arroz Tio João"], 30, fake, estilo="receita")
    assert d1 is not None and len(d1) <= 30          # teto é lei
    assert gerar_dica(["Arroz"], 30, None) is None    # sem IA → None (degrada)

    # 3a) modelo TEIMOSO (sempre a mesma resposta): com evitar=[d1], a guarda
    # barra — o resultado NUNCA é a dica repetida
    d2 = gerar_dica(["Arroz Tio João"], 30, fake, estilo="receita",
                    evitar=["Arroz soltinho: refogue o alho antes."])
    assert d2 is None                                 # barrada, não repetida

    # 3b) modelo que respeita o evitar (o prompt ganha "NÃO repita"): a
    # resposta nova é DIFERENTE da anterior, por conteúdo
    fake2 = MotorIAFake(respostas_chat={
        "NÃO repita": json.dumps({"dica": "Capriche no feijão novo."}),
        "Fica a Dica": json.dumps({"dica": "Arroz soltinho sempre."}),
    })
    d3 = gerar_dica(["Arroz"], 40, fake2)
    d4 = gerar_dica(["Arroz"], 40, fake2, evitar=[d3])
    assert d3 and d4 and d4 != d3


def test_painel_memoria_de_dica_acumula():
    """GATE 2.1 (caller): cada dica gerada entra no histórico do painel e a
    lista `evitar` da PRÓXIMA geração a contém — a memória existe de fato,
    não só o texto atual."""
    from PySide6.QtWidgets import QApplication

    from app.qt.canvas import CanvasView
    from app.qt.painel_propriedades import PainelPropriedades
    QApplication.instance() or QApplication([])
    p = PainelPropriedades(CanvasView())
    p._registrar_dica("Dica um")
    p._registrar_dica("Dica dois")
    p.texto_fixo.setText("Texto atual")
    evitar = p._dicas_a_evitar()
    assert evitar[0] == "Texto atual"                # o atual vem primeiro
    assert "Dica um" in evitar and "Dica dois" in evitar


# ===========================================================================
# R-089 — fila de IA com prioridade
# ===========================================================================

def test_fila_prioridade_poe_o_foco_na_frente():
    """R-089/passo 62+72: o que o dono está olhando (foco) roda primeiro; o resto
    mantém a ordem. Prova de mutação: sem a reordenação, a ordem original fica."""
    from app.qt.telas import servico
    pares = [("a", 1), ("b", 2), ("c", 3)]
    assert servico.ordenar_por_prioridade(pares, foco="c")[0][0] == "c"
    assert [p[0] for p in servico.ordenar_por_prioridade(pares, foco="c")] == \
           ["c", "a", "b"]                            # foco na frente, resto estável
    assert servico.ordenar_por_prioridade(pares) == pares   # sem foco, intacto


# ===========================================================================
# Integração — a Mesa compõe a peça e a revisora a lê (não bloqueia)
# ===========================================================================

def test_mesa_revisora_le_a_peca_composta_e_nao_bloqueia(raiz_tmp, tmp_path):
    """Integração R-081 (o demo do passo 90): a Mesa compõe a peça REAL, e a
    revisora (com visão) lê um preço que NÃO bate com os dados e acusa — sem
    travar o export. É o "revisora pega o preço trocado num PNG de teste"."""
    from PySide6.QtWidgets import QApplication
    from app.ai.revisora import revisar_export
    from app.core.paths import SystemRoot
    from app.qt.telas.mesa import MesaTela
    from app.qt.telas.servico import ItemMesa
    from app.rendering.cartaz import layout_cartaz_exemplo
    QApplication.instance() or QApplication([])
    m = MesaTela()
    lay = layout_cartaz_exemplo()
    m._layout = lay
    m._fundo = None
    m.area.carregar(lay, {})
    it = ItemMesa("Café Pilão 500g", "10,00", "VERDE", "Café Pilão 500g")
    m._itens = [it]
    m._mapa = {"cartaz": it.uid}
    paginas = m.paginas_compostas()
    assert len(paginas) == 1
    png = tmp_path / "peca.png"
    paginas[0].save(str(png))
    # a visão (fake) lê 99,90 na peça; o projeto diz 10,00 → a revisora acusa
    fake = MotorIAFake(respostas_visao={
        "revisor de encarte": json.dumps({"precos": ["99,90"]})})
    avisos, deg = revisar_export(str(png), m._dados_por_slot(), layout=lay,
                                 motor=fake, fontes_dir=SystemRoot().fontes)
    assert any("99,90" in a for a in avisos)      # pegou o preço trocado
    assert isinstance(avisos, list)               # nunca "veta", só informa
    m.close()


def test_revisora_worker_encerra_no_fechamento(raiz_tmp):
    """[lei exit-0, achado da frota] o worker NOVO da revisora (mesa._revisar)
    roda sob o gerenciador da Mesa e é ENCERRADO no closeEvent — nada nativo vivo
    no teardown. Prova de mutação: sem o `_trabalhos.encerrar()` no closeEvent, o
    worker sobreviveria."""
    import time as _t

    from PySide6.QtWidgets import QApplication
    from app.qt.telas.mesa import MesaTela
    from app.qt.workers import Trabalhador
    QApplication.instance() or QApplication([])
    m = MesaTela()
    # injeta um worker lento no MESMO gerenciador que a revisora usa
    trab = Trabalhador(lambda st: _t.sleep(0.5))
    m._trabalhos.rodar(trab)
    assert trab.isRunning() or trab in m._trabalhos._vivos
    m.close()                                     # closeEvent → encerra
    assert not trab.isRunning()                   # juntado, nada vivo no teardown

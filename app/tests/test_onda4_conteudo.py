"""Onda 4 da REVISAO_GERAL — CONTEÚDO/IA, com prova.

RG-20 (a fundação): a REGRA DURA do enriquecimento — nenhuma palavra do
nome bruto pode sumir do sanitizado; perda = revisão humana, nunca
silêncio. Fakes EXERCITAM a regra (devolvem nome COM perda de verdade —
lição da F8.1: fake que nunca casa é teste que mente).
"""

from pathlib import Path

import pytest

from app.ai.enriquecimento import enriquecer, tokens_perdidos
from app.ai.fake import MotorIAFake


@pytest.fixture()
def raiz_tmp(tmp_path, monkeypatch):
    monkeypatch.setenv("AUTOTABLOIDE_ROOT", str(tmp_path / "raiz"))
    from app.core.database import Database
    from app.core.paths import SystemRoot

    root = SystemRoot(tmp_path / "raiz").criar_estrutura()
    Database(root).init().engine.dispose()
    return root


# --- RG-20: a regra dura ---------------------------------------------------------------


def test_tokens_perdidos_pega_o_caso_real_da_auditoria():
    """"Val" e "Original" sumiram ao vivo — a regra acusa exatamente isso."""
    assert tokens_perdidos("DOCE DE BANANA VAL 250 G",
                           "Doce de Banana 250g") == ["VAL"]
    assert tokens_perdidos("DOCE DE LEITE FIRMESA ORIGINAL 400 G",
                           "Doce de Leite Firmesa 400g") == ["ORIGINAL"]


def test_tokens_perdidos_tolera_typo_corrigido_e_reordenacao():
    """Correção de acento/caixa e reordenação NÃO acusam (é o trabalho da IA)."""
    assert tokens_perdidos("OLE O DE SOJA LIZA 900 ML",
                           "Óleo de Soja Liza 900ml") == []
    assert tokens_perdidos("400 G ORIGINAL FIRMESA DOCE DE LEITE",
                           "Doce de Leite Firmesa Original 400g") == []


def test_tokens_perdidos_acusa_troca_de_marca():
    """Typo de fornecedor (Huppers) é SUGERIDO, nunca trocado sozinho —
    a troca da IA aparece como perda e o humano confirma."""
    perdidos = tokens_perdidos("SALG. HUPPERS GALINHA 50 G",
                               "Salgadinho Ruppers Galinha 50g")
    assert perdidos == ["HUPPERS"]


def test_tokens_perdidos_ignora_stopwords_e_fragmentos():
    assert tokens_perdidos("ARROZ TIO JOAO DE 5 KG", "Arroz Tio Joao 5kg") == []


def test_enriquecer_marca_a_perda_com_fake_que_descarta():
    """O fake DESCARTA "Original" de verdade — e a regra dura pega."""
    fake = MotorIAFake(respostas_chat={
        "supermercado": '{"nome_sanitizado": "Doce de Leite Firmesa 400g", '
                        '"confianca": 0.9}'})
    enr = enriquecer("DOCE DE LEITE FIRMESA ORIGINAL 400 G", fake)
    assert enr.tokens_perdidos == ["ORIGINAL"]

    fake_ok = MotorIAFake(respostas_chat={
        "supermercado": '{"nome_sanitizado": '
                        '"Doce de Leite Firmesa Original 400g"}'})
    enr2 = enriquecer("DOCE DE LEITE FIRMESA ORIGINAL 400 G", fake_ok)
    assert enr2.tokens_perdidos == []


def test_componentes_e_variantes_contam_como_presenca():
    """Multi-produto reparte o nome DE PROPÓSITO — Camil e Rei nos
    componentes não é perda."""
    fake = MotorIAFake(respostas_chat={
        "supermercado": '{"nome_sanitizado": "Arroz Camil 5kg", '
                        '"componentes": [{"nome_sanitizado": "Arroz Camil 5kg"}, '
                        '{"nome_sanitizado": "Arroz Rei 5kg"}]}'})
    enr = enriquecer("ARROZ CAMIL E REI 5 KG", fake)
    assert enr.tokens_perdidos == []


def test_proposta_de_criacao_propaga_a_perda(raiz_tmp, monkeypatch):
    from app.qt.telas import servico

    fake = MotorIAFake(respostas_chat={
        "supermercado": '{"nome_sanitizado": "Doce de Banana 250g"}'})
    p = servico.enriquecer_descricao("DOCE DE BANANA VAL 250 G", fake)
    assert p.tokens_perdidos == ["VAL"]


def test_lote_nao_aplica_nome_com_perda(raiz_tmp):
    """RG-20 no acervo: o passe de lote PULA (e conta) o nome que perdeu
    palavra — o banco fica intacto para o humano revisar."""
    from app.core.database import Database
    from app.core.repositories import ProdutoRepositorio
    from app.scripts.enriquecer_banco import enriquecer_banco

    db = Database().init()
    with db.Session() as s:
        ProdutoRepositorio(s).importar("DOCE DE BANANA VAL 250 G")
        s.commit()
    db.engine.dispose()

    fake = MotorIAFake(respostas_chat={
        "supermercado": '{"nome_sanitizado": "Doce de Banana 250g"}'})
    resumo = enriquecer_banco(fake, log=lambda *_: None)
    assert resumo["revisar"] == 1 and resumo["atualizados"] == 0

    db = Database().init()
    with db.Session() as s:
        p = ProdutoRepositorio(s).listar(limit=5)[0]
        assert "Val" in p.nome_sanitizado      # o nome NÃO foi mutilado
    db.engine.dispose()


# --- RG-23: categoria nasce com o produto ----------------------------------------------


def test_criacao_ja_sai_categorizada(raiz_tmp):
    from app.core.database import Database
    from app.core.repositories import ProdutoRepositorio
    from app.qt.telas import servico
    from app.qt.telas.servico import ItemMesa

    item = ItemMesa("FIGADO BOVINO 100 G", "0,99", "VERMELHO",
                    "FIGADO BOVINO 100 G")
    servico.finalizar_criacao(item, "Fígado Bovino 100g", False, None,
                              categoria="Frios")
    db = Database().init()
    with db.Session() as s:
        p = ProdutoRepositorio(s).get(item.produto_id)
        assert p.categoria.nome == "Frios"
        assert p.categoria_origem == "ia"      # humano pode corrigir depois
    db.engine.dispose()


# --- RG-30: marcas próprias -----------------------------------------------------------


def test_marca_propria_por_token_exato():
    from app.qt.telas.servico import eh_marca_propria, remover_marcas_do_termo

    g = ["BBX", "BB"]
    assert eh_marca_propria("Fígado Bovino BBX 100g", g)
    assert not eh_marca_propria("Sabão Barra 100g", g)      # "BB" ⊄ "Barra"
    assert remover_marcas_do_termo("Fígado Bovino BBX 100g", g) == \
        "Fígado Bovino 100g"
    # termo SÓ com a sigla nunca vira busca vazia
    assert remover_marcas_do_termo("BBX", g) == "BBX"


def test_criacao_marca_propria_automatica(raiz_tmp):
    from app.core.database import Database
    from app.core.repositories import ProdutoRepositorio
    from app.qt.telas import servico
    from app.qt.telas.servico import ItemMesa

    item = ItemMesa("CORACAO E LINGUA BOVINA BBX 100 G", "0,77", "VERMELHO",
                    "CORACAO E LINGUA BOVINA BBX 100 G")
    servico.finalizar_criacao(item, "Coração e Língua Bovina BBX 100g",
                              False, None)
    db = Database().init()
    with db.Session() as s:
        p = ProdutoRepositorio(s).get(item.produto_id)
        assert p.marca_propria is True         # RG-30: automático SEMPRE
    db.engine.dispose()


# --- RG-26: paginação da curadoria ----------------------------------------------------


def test_mais_resultados_pagina_a_busca(raiz_tmp, monkeypatch):
    from PySide6.QtWidgets import QApplication

    QApplication.instance() or QApplication([])
    from app.qt.telas import servico
    from app.qt.telas.curadoria_dialog import CuradoriaDialog

    pedidos: list[int] = []
    monkeypatch.setattr(servico, "buscar_candidatos",
                        lambda nome, st, n=6: pedidos.append(n) or [])
    dlg = CuradoriaDialog("Produto X", [])
    dlg._mais_resultados()
    dlg._trabalhos.encerrar(espera_ms=3000)
    dlg._mais_resultados()
    dlg._trabalhos.encerrar(espera_ms=3000)
    assert pedidos == [12, 18]                 # 6 → 12 → 18 (mesma busca)
    dlg._buscar_de_novo()                      # busca NOVA recomeça do 6
    dlg._trabalhos.encerrar(espera_ms=3000)
    assert pedidos[-1] == 6


# --- RG-44: preset da ordem de setores ------------------------------------------------


def test_preset_setores_preenche_o_campo(raiz_tmp):
    from PySide6.QtWidgets import QApplication

    QApplication.instance() or QApplication([])
    from app.qt.telas.configuracoes import ConfiguracoesTela
    from app.qt.telas.servico import ORDEM_SETORES_LOJA

    tela = ConfiguracoesTela()
    tela._preset_setores()
    texto = tela.campo_categorias.text()
    assert texto.startswith("Hortifrúti")
    assert all(setor in texto for setor in ORDEM_SETORES_LOJA)


# --- RG-41: EAN + cascata Open Food Facts → ddgs --------------------------------------


def test_ean_valido_normaliza():
    from app.images.off import ean_valido

    assert ean_valido("7891234567890") == "7891234567890"
    assert ean_valido(" 789.1234.5678-90 ") == "7891234567890"
    assert ean_valido("12345678") == "12345678"        # EAN-8
    assert ean_valido("1234567") is None               # curto demais
    assert ean_valido("123456789012345") is None       # longo demais
    assert ean_valido("") is None and ean_valido(None) is None


def test_buscar_imagem_off_sem_rede_devolve_none(tmp_path, monkeypatch):
    """I2: sem rede a cascata SEGUE — o OFF nunca estoura nem trava."""
    import urllib.request

    def _sem_rede(*a, **k):
        raise OSError("sem rede")

    monkeypatch.setattr(urllib.request, "urlopen", _sem_rede)
    from app.images.off import buscar_imagem_off
    assert buscar_imagem_off("7891234567890", tmp_path) is None


def test_buscar_imagem_off_baixa_o_packshot(tmp_path, monkeypatch):
    import io
    import urllib.request

    respostas = iter([
        io.BytesIO(b'{"product": {"image_front_url": '
                   b'"https://images.off/x.400.jpg"}}'),
        io.BytesIO(b"JPEGDATA-FAKE"),
    ])

    class _Resp:
        def __init__(self, corpo):
            self._corpo = corpo
        def read(self):
            return self._corpo.read()
        def __enter__(self):
            return self
        def __exit__(self, *a):
            return False

    monkeypatch.setattr(urllib.request, "urlopen",
                        lambda req, timeout=0: _Resp(next(respostas)))
    from app.images import off
    monkeypatch.setattr(off, "urlopen",
                        lambda req, timeout=0: _Resp(next(respostas)),
                        raising=False)
    caminho = off.buscar_imagem_off("7891234567890", tmp_path)
    assert caminho is not None and caminho.endswith("off_7891234567890.jpg")
    assert (tmp_path / "off_7891234567890.jpg").read_bytes() == b"JPEGDATA-FAKE"


def test_migracao_banco_antigo_ganha_coluna_ean(tmp_path, monkeypatch):
    """Banco criado ANTES do RG-41 abre e ganha a coluna (padrão F8.1)."""
    import sqlite3

    monkeypatch.setenv("AUTOTABLOIDE_ROOT", str(tmp_path / "raiz"))
    from app.core.database import Database
    from app.core.paths import SystemRoot

    root = SystemRoot(tmp_path / "raiz").criar_estrutura()
    Database(root).init().engine.dispose()      # cria o schema atual
    caminho = root.caminho_banco
    con = sqlite3.connect(caminho)              # "envelhece" o banco: derruba a coluna
    con.execute("ALTER TABLE produtos DROP COLUMN ean")
    con.commit()
    con.close()

    Database(root).init().engine.dispose()      # o init re-migra
    con = sqlite3.connect(caminho)
    colunas = {r[1] for r in con.execute("PRAGMA table_info(produtos)")}
    con.close()
    assert "ean" in colunas


def test_parse_tabela_ean_e_compat(tmp_path):
    from app.scripts.importar_tabela import parse_tabela, parse_tabela_ean

    arq = tmp_path / "ofertas.txt"
    arq.write_text(
        "ARROZ TIO JOAO 5 KG | 19,90 | 7891234567890\n"
        "7896054900019 FEIJAO CARIOCA 1 KG | 7,50\n"
        "COCA COLA 2 L | 9,99\n", encoding="utf-8")
    linhas = parse_tabela_ean(arq)
    assert linhas[0] == ("ARROZ TIO JOAO 5 KG", "19,90", "7891234567890")
    assert linhas[1] == ("FEIJAO CARIOCA 1 KG", "7,50", "7896054900019")
    assert linhas[2] == ("COCA COLA 2 L", "9,99", None)
    # compat: os 7 consumidores antigos seguem com 2-tuplas
    assert parse_tabela(arq)[0] == ("ARROZ TIO JOAO 5 KG", "19,90")


def test_cascata_poe_o_packshot_oficial_primeiro(raiz_tmp, monkeypatch):
    from app.images import off
    from app.qt.telas import servico

    monkeypatch.setattr(off, "buscar_imagem_off",
                        lambda ean, destino, timeout=8.0: "C:/fake/off.jpg")
    import app.images.busca as busca_mod

    class _R:
        candidatos = []
    monkeypatch.setattr(busca_mod, "buscar_imagens",
                        lambda *a, **k: _R())
    avisos: list[str] = []
    r = servico.buscar_candidatos_para("Arroz Tio João 5kg", avisos.append,
                                       ean="7891234567890")
    assert r[0] == "C:/fake/off.jpg"           # o oficial vem PRIMEIRO
    assert any("código de barras" in a.lower() for a in avisos)


def test_cascata_sem_off_avisa_e_segue(raiz_tmp, monkeypatch):
    from app.images import off
    from app.qt.telas import servico

    monkeypatch.setattr(off, "buscar_imagem_off",
                        lambda ean, destino, timeout=8.0: None)
    import app.images.busca as busca_mod

    class _C:
        caminho = "C:/fake/ddgs.jpg"

    class _R:
        candidatos = [_C()]
    monkeypatch.setattr(busca_mod, "buscar_imagens", lambda *a, **k: _R())
    avisos: list[str] = []
    r = servico.buscar_candidatos_para("Produto X", avisos.append,
                                       ean="7891234567890")
    assert r == ["C:/fake/ddgs.jpg"]           # a cascata seguiu no ddgs
    assert any("não achado" in a.lower() for a in avisos)   # aviso honesto (I2)


def test_ean_persiste_pela_edicao_do_almoxarifado(raiz_tmp):
    from app.qt.telas import servico

    servico.finalizar_criacao(
        servico.ItemMesa("PRODUTO EAN 1 KG", "1,00", "VERMELHO",
                         "PRODUTO EAN 1 KG"),
        "Produto Ean 1kg", False, None)
    d = servico.listar_catalogo(texto="Produto Ean")[0]
    novo = servico.editar_produto(d["id"], ean="7891112223334")
    assert novo["ean"] == "7891112223334"


# --- RG-22: abreviações do tabloide ---------------------------------------------------


def test_abreviar_so_no_tabloide():
    from app.qt.telas.servico import abreviar_para_tabloide

    g = {"Leite Condensado": "Leite Cond.", "Achocolatado": "Achoc."}
    assert abreviar_para_tabloide("Leite Condensado Moça 395g", g) == \
        "Leite Cond. Moça 395g"
    assert abreviar_para_tabloide("LEITE CONDENSADO Italac", g) == \
        "Leite Cond. Italac"                    # ignora caixa
    assert abreviar_para_tabloide("Arroz Camil 5kg", g) == "Arroz Camil 5kg"
    assert abreviar_para_tabloide("Arroz Camil 5kg", {}) == "Arroz Camil 5kg"


def test_abreviacao_frase_longa_tem_precedencia():
    from app.qt.telas.servico import abreviar_para_tabloide

    g = {"Leite Condensado": "L. Cond.", "Leite": "Lt."}
    assert abreviar_para_tabloide("Leite Condensado 395g", g) == \
        "L. Cond. 395g"                         # a frase inteira vence


# --- RG-24: datas inteligentes --------------------------------------------------------


def test_proxima_ocorrencia_do_dia():
    from datetime import date

    from app.qt.telas.servico import proxima_ocorrencia

    sabado = date(2026, 7, 18)                  # 18/07/2026 = sábado
    assert proxima_ocorrencia(4, sabado) == date(2026, 7, 24)   # sexta que vem
    assert proxima_ocorrencia(5, sabado) == sabado              # HOJE conta
    assert proxima_ocorrencia(3, sabado) == date(2026, 7, 23)   # quinta


def test_sugerir_validade_por_evento(raiz_tmp):
    from datetime import date

    from app.core.database import Database
    from app.core.repositories import ConfigRepositorio
    from app.qt.telas.servico import sugerir_validade

    db = Database().init()
    with db.Session() as s:
        ConfigRepositorio(s).set("eventos.dias",
                                 {"Sexta Verde": "sex", "Quintou": "qui"})
        s.commit()
    db.engine.dispose()
    sabado = date(2026, 7, 18)
    # auditoria do dono (20/07): a campanha de dia fixo vale SÓ NO DIA
    assert sugerir_validade("Sexta Verde", sabado) == "SOMENTE 24/07"
    assert sugerir_validade("sexta verde", sabado) == "SOMENTE 24/07"  # caixa
    assert sugerir_validade("Avulsos", sabado) is None   # sem dia: sem palpite


# --- RG-25: Fica a Dica ---------------------------------------------------------------


def test_limite_caracteres_deriva_da_regiao():
    from app.ai.enriquecimento import limite_caracteres

    grande = limite_caracteres(80, 40, 12)
    pequeno = limite_caracteres(30, 10, 12)
    assert grande > pequeno                     # área maior, mais texto
    assert limite_caracteres(5, 3, 48) == 40    # piso: nunca menos de 40
    assert limite_caracteres(500, 500, 6) == 600  # teto


def test_gerar_dica_respeita_o_limite():
    from app.ai.enriquecimento import gerar_dica

    fake = MotorIAFake(respostas_chat={
        "Fica a Dica": '{"dica": "' + "Misture o arroz com o feijão. " * 20
                       + '"}'})
    dica = gerar_dica(["Arroz Camil 5kg", "Feijão Carioca 1kg"], 120, fake)
    assert dica is not None and len(dica) <= 120   # o teto da região é lei
    assert gerar_dica(["Arroz"], 120, None) is None       # sem motor: None
    assert gerar_dica([], 120, fake) is None              # sem itens: None


# --- RG-29: criar como composto na conciliação ----------------------------------------


def test_criar_como_composto_na_conciliacao(raiz_tmp):
    from app.qt.telas import servico
    from app.qt.telas.servico import ItemMesa

    item = ItemMesa("CORACAO E LINGUA BOVINA BBX 100 G", "0,77", "VERMELHO",
                    "CORACAO E LINGUA BOVINA BBX 100 G")
    comp = servico.criar_como_composto(
        item, ["Coração Bovino BBX 100g", "Língua Bovina BBX 100g"],
        False, None, categoria="Frios")
    assert servico.eh_composto(comp)
    assert comp.preco == "0,77"                 # preço único da linha
    assert comp.descricao == item.descricao     # o rastro da linha original
    # os DOIS componentes existem como produtos PRÓPRIOS no banco
    nomes = {d["nome"] for d in servico.listar_catalogo(limite=10)}
    assert "Coração Bovino BBX 100g" in nomes
    assert "Língua Bovina BBX 100g" in nomes
    # separável como qualquer composto (F7.2)
    a, b = servico.separar_item(comp)
    assert a.produto_id and b.produto_id and a.produto_id != b.produto_id


# --- RG-28: multi-fotos por PRODUTO no acervo -----------------------------------------


def _produto_com_extras(raiz):
    """Produto com foto principal + 2 extras REAIS na biblioteca."""
    from PIL import Image

    from app.qt.telas import servico
    from app.qt.telas.servico import ItemMesa

    item = ItemMesa("SABAO YPE 5 X 100 G", "8,00", "VERMELHO",
                    "SABAO YPE 5 X 100 G")
    servico.finalizar_criacao(item, "Sabão Ypê 5x100g", False, None)
    pid = item.produto_id
    pasta = raiz.biblioteca_imagens / str(pid)
    (pasta / "extras").mkdir(parents=True, exist_ok=True)
    cores = ["#FF0000", "#00FF00", "#0000FF"]
    caminhos = []
    for i, cor in enumerate(cores):
        cam = (pasta / "atual.png" if i == 0
               else pasta / "extras" / f"sabor_{i}.png")
        Image.new("RGB", (60, 60), cor).save(cam)
        caminhos.append(str(cam))
    return pid, caminhos


def test_multi_fotos_persistem_no_acervo(raiz_tmp):
    from app.qt.telas import servico

    pid, caminhos = _produto_com_extras(raiz_tmp)
    n = servico.salvar_imagens_produto(pid, caminhos)
    assert n == 3
    d = servico.listar_catalogo(limite=10)[0]
    assert len(d["imagens"]) == 3               # o catálogo devolve a lista…
    assert [Path(c).name for c in d["imagens"]] == \
        ["atual.png", "sabor_1.png", "sabor_2.png"]   # …NA ORDEM

    item = servico.item_do_catalogo(d)          # importar do banco reconstitui
    assert len(item.imagens) == 3

    # ordem NOVA persiste por cima (o humano reordenou no diálogo)
    servico.salvar_imagens_produto(pid, list(reversed(caminhos)))
    d2 = servico.listar_catalogo(limite=10)[0]
    assert [Path(c).name for c in d2["imagens"]][0] == "sabor_2.png"

    # 1 foto só = volta ao modo foto única (campo limpo)
    servico.salvar_imagens_produto(pid, caminhos[:1])
    d3 = servico.listar_catalogo(limite=10)[0]
    assert d3["imagens"] == []


def test_foto_fora_da_biblioteca_nao_persiste(raiz_tmp, tmp_path):
    from PIL import Image

    from app.qt.telas import servico

    pid, caminhos = _produto_com_extras(raiz_tmp)
    solta = tmp_path / "temporaria.png"
    Image.new("RGB", (60, 60), "#ABCDEF").save(solta)
    n = servico.salvar_imagens_produto(pid, caminhos + [str(solta)])
    assert n == 3                               # a de fora ficou de fora
    d = servico.listar_catalogo(limite=10)[0]
    assert all("temporaria" not in c for c in d["imagens"])


def test_multi_fotos_sobrevivem_a_portabilidade_com_remap(raiz_tmp, tmp_path,
                                                          monkeypatch):
    """RG-28 × portabilidade (o terreno sagrado): os caminhos são relativos
    à PASTA do produto — o remap de id por chave natural renomeia a pasta e
    a lista continua apontando certo, byte a byte."""
    from PIL import Image

    from app.core.portabilidade import analisar_pacote, aplicar_importacao, exportar_pacote
    from app.qt.telas import servico

    pid, caminhos = _produto_com_extras(raiz_tmp)
    servico.salvar_imagens_produto(pid, caminhos)
    bytes_sabor2 = Path(caminhos[2]).read_bytes()
    pacote = tmp_path / "leva.atpkg"
    exportar_pacote(pacote)

    # máquina B com ids DESLOCADOS (a mesclagem ingênua por id colaria errado)
    raiz_b = tmp_path / "maquina_b"
    monkeypatch.setenv("AUTOTABLOIDE_ROOT", str(raiz_b))
    from app.core.database import Database
    from app.core.paths import SystemRoot
    from app.core.repositories import ProdutoRepositorio
    root_b = SystemRoot(raiz_b).criar_estrutura()
    db = Database(root_b).init()
    with db.Session() as s:
        repo = ProdutoRepositorio(s)
        for i in range(4):                      # desloca os ids de B
            repo.importar(f"OCUPANTE {i} 1 KG")
        s.commit()
    db.engine.dispose()

    rel = analisar_pacote(pacote)
    aplicar_importacao(rel)

    dados = servico.listar_catalogo(texto="Sabão Ypê")
    assert dados, "o produto não chegou na máquina B"
    d = dados[0]
    assert len(d["imagens"]) == 3               # a lista viajou com o remap
    for cam in d["imagens"]:
        assert Path(cam).exists(), f"foto sumiu no remap: {cam}"
    assert Path(d["imagens"][2]).read_bytes() == bytes_sabor2   # byte a byte


def test_curadoria_mostra_o_aviso_nominal(raiz_tmp):
    from PySide6.QtWidgets import QApplication

    QApplication.instance() or QApplication([])
    from app.qt.telas.curadoria_dialog import CuradoriaDialog

    dlg = CuradoriaDialog("Doce de Banana 250g", [],
                          tokens_perdidos=["VAL"])
    assert "VAL" in dlg.aviso_tokens.text()
    assert not dlg.aviso_tokens.isHidden()
    dlg2 = CuradoriaDialog("Óleo de Soja Liza 900ml", [])
    assert dlg2.aviso_tokens.isHidden()        # sem perda, sem alarme

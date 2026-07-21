"""FASE 7 — Mesa II: produção em massa.

Cresce ao longo da fase. Bloco A: o parser de COLAGEM (R-050) — REUSA o
parser de preço P0.3 (`servico.preco_decimal`), rejeita o ambíguo "2x 5,00"
(I2, nunca cria preço errado em silêncio), e separa nome × preço por colunas
(Excel) ou preço-no-fim (WhatsApp), ignorando lixo (cabeçalho/total).
"""

import shutil
from pathlib import Path

import pytest
from PySide6.QtWidgets import QApplication

from app.qt.telas.colagem import LinhaColada, linhas_para_tuplas, parse_colagem


def _app():
    return QApplication.instance() or QApplication([])


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


def test_colagem_excel_colunas_tab():
    """Tabela do Excel (tab): nome × preço por coluna, preço válido (P0.3)."""
    linhas = parse_colagem("Arroz Tio João 5kg\t24,90\n"
                           "Feijão Carioca 1kg\tR$ 7,99")
    assert len(linhas) == 2
    assert linhas[0].nome == "Arroz Tio João 5kg" and linhas[0].preco == "24,90"
    assert linhas[0].preco_valido and linhas[0].aviso is None
    assert linhas[1].nome == "Feijão Carioca 1kg" and linhas[1].preco_valido


def test_colagem_rejeita_preco_ambiguo_reusa_p03():
    """R-050/passo 7 (I2): o preço colado passa pelo P0.3 — "2x 5,00" é
    rejeitado (não vira preço em silêncio), com aviso. Prova de que REUSA o
    parser: se validasse por conta própria, "2x 5,00" passaria."""
    linhas = parse_colagem("Sabão OMO 1,6kg\t2x 5,00")
    assert len(linhas) == 1
    assert linhas[0].preco == "2x 5,00"
    assert not linhas[0].preco_valido and linhas[0].aviso   # I2: avisa, não engole


def test_colagem_whatsapp_preco_no_fim():
    """WhatsApp (sem separador): o preço no FIM da linha é destacado do nome."""
    linhas = parse_colagem("Refrigerante Guaraná 2L  R$ 6,49")
    assert len(linhas) == 1
    assert linhas[0].nome == "Refrigerante Guaraná 2L"
    assert linhas[0].preco.replace(" ", "") == "R$6,49" or linhas[0].preco_valido


def test_colagem_ignora_lixo():
    """R-050/passo 6+60: cabeçalho, linha de total e linha vazia são ignorados;
    só produtos entram na prévia."""
    texto = ("Produto;Preço\n"          # cabeçalho
             "\n"                         # linha vazia
             "Leite Integral 1L;4,29\n"
             "TOTAL;123,45\n"             # rodapé/total
             "42\n")                      # numeração solta
    linhas = parse_colagem(texto)
    nomes = [li.nome for li in linhas]
    assert nomes == ["Leite Integral 1L"]
    assert linhas[0].preco == "4,29" and linhas[0].preco_valido


def test_colagem_ponto_e_virgula_e_formatos_br():
    """R-050/passo 61: formatos brasileiros normalizados pelo P0.3."""
    linhas = parse_colagem("Azeite Gallo 500ml;R$ 1.299,00\n"
                           "Pão de Forma;5.99")
    assert linhas[0].preco_valido        # "R$ 1.299,00" (milhar) entendido
    assert linhas[1].preco_valido        # "5.99" entendido


def test_colagem_para_tuplas_reusa_pipeline():
    """As linhas viram (descricao, preco, ean) — o MESMO formato que
    `importar_ofertas` consome (reusa a conciliação/RG-20 sem duplicar)."""
    linhas = [LinhaColada("Arroz", "5,00", True),
              LinhaColada("Feijão", None, False)]
    assert linhas_para_tuplas(linhas) == [("Arroz", "5,00", None),
                                          ("Feijão", None, None)]


def test_multi_preco_reconhecido_vs_ambiguo_proibido():
    """R-070/passo 62/95: "3 por 10" e "leve 3 pague 2" são FORMATO
    reconhecido; "2x 5,00" (proibido) NÃO é multi-preço E segue rejeitado pelo
    P0.3 — os dois lado a lado. Prova de mutação: se o regex casasse "2x",
    o assert `is None` cairia."""
    from app.qt.telas.colagem import parse_multi_preco
    from app.qt.telas.servico import preco_decimal

    mp = parse_multi_preco("3 por R$ 10,00")
    assert mp is not None and mp.quantidade == 3 and mp.texto == "3 por R$ 10,00"
    assert parse_multi_preco("Leve 3 pague 2").texto == "Leve 3 pague 2"

    # o proibido: nem multi-preço, nem preço válido
    assert parse_multi_preco("2x 5,00") is None
    assert preco_decimal("2x 5,00") is None


def test_multi_preco_desenha_na_pagina_por_pixel():
    """R-070/passo 62+95: um item multi-preço DESENHA o texto na região de
    preço (por PIXEL) — não é meia-feature; e o pré-voo NÃO o marca 'sem
    preço' (o aviso enganoso que faltava distinguir)."""
    from app.rendering.compositor import DadosProduto, compor_pagina
    from app.rendering.model import (
        LayoutDef, Pagina, PapelPreco, Regiao, Retangulo, Slot, TipoRegiao,
    )
    from app.qt.telas import servico
    reg = Regiao(TipoRegiao.PRECO, Retangulo(2, 2, 46, 14),
                 papel_preco=PapelPreco.UNICO, tamanho_max_pt=14)
    lay = LayoutDef(50, 18, dpi=100, paginas=[Pagina([Slot("c", [reg])])])
    com = compor_pagina(lay, lay.paginas[0],
                       {"c": DadosProduto("X", multi_preco="3 por R$ 10,00")})
    vazio = compor_pagina(lay, lay.paginas[0], {"c": DadosProduto("X")})
    assert list(com.getdata()) != list(vazio.getdata())    # o texto apareceu
    # pré-voo: multi-preço TEM preço — não avisa "sem preço"
    avisos = servico.validar_composicao(
        lay, {"c": DadosProduto("X", multi_preco="3 por R$ 10,00")})
    assert not any("sem preço" in a for a in avisos)
    # e no encher-página: item multi-preço não é acusado de sem preço
    it = _itemesa("Refri", foto=True, preco="")
    it.multi_preco = "3 por R$ 10,00"
    _mapa, _resto, av2 = servico.plano_encher_pagina([it], ["s0"])
    assert not any("sem preço" in a for a in av2)


def test_planilha_reconhece_multi_preco():
    """R-070: digitar "3 por 10" na planilha grava multi_preco (não rejeita
    como preço inválido); "2x 5,00" segue rejeitado."""
    from app.qt.telas import servico
    from app.qt.telas.planilha import aplicar_edicao
    it = servico.ItemMesa("Refri", "5,00", "VERDE", "Refri")
    ok, aviso = aplicar_edicao(it, "Preço", "3 por 10,00")
    assert ok and it.multi_preco and "3 por" in it.multi_preco
    assert it.preco is None
    # "2x 5,00" NÃO é multi-preço → rejeitado
    ok2, aviso2 = aplicar_edicao(it, "Preço", "2x 5,00")
    assert not ok2 and aviso2 and it.multi_preco is None


def test_colar_dialogo_previa_confirma_e_reedita():
    """R-050/passo 9: a prévia mostra o que entendi; editar o preço revalida e
    `linhas_confirmadas` reflete."""
    _app()
    from app.qt.telas.colagem_dialog import ColagemPreviaDialog
    linhas = parse_colagem("Arroz\t24,90\nSabão\t2x 5,00")
    dlg = ColagemPreviaDialog(linhas, None)
    conf = dlg.linhas_confirmadas()
    assert conf[0].preco_valido and not conf[1].preco_valido
    # o dono corrige o preço do Sabão na prévia
    dlg.tab.item(1, 1).setText("9,90")
    conf2 = dlg.linhas_confirmadas()
    assert conf2[1].preco == "9,90" and conf2[1].preco_valido


def test_conciliar_linhas_reusa_pipeline_cria_itens(raiz_tmp):
    """R-050/passo 8+17: as tuplas caem no MESMO caminho de conciliação —
    com o banco vazio viram itens VERMELHOS (novos), preço preservado, uid
    próprio (I1). Reusa importar_ofertas sem duplicar."""
    from app.qt.telas import servico
    linhas = parse_colagem("Arroz Tio João 5kg\t24,90\nFeijão Camil 1kg\t7,99")
    tuplas = linhas_para_tuplas(linhas)
    res = servico.conciliar_linhas(tuplas, lambda _m: None)
    assert len(res.itens) == 2
    assert res.itens[0].descricao == "Arroz Tio João 5kg"
    assert res.itens[0].preco == "24,90"
    assert res.itens[0].semaforo == "VERMELHO"        # banco vazio = novo
    assert res.itens[0].uid and res.itens[0].uid != res.itens[1].uid  # I1


def test_importar_varios_um_erro_nao_derruba_a_fila(raiz_tmp, tmp_path):
    """R-049/passo 4+64 (I2): um arquivo que falha (sumiu do disco) ERRA, mas a
    fila termina — o txt válido é lido, o erro fica marcado, nada se perde."""
    from app.qt.telas import servico
    txt = tmp_path / "ofertas.txt"
    txt.write_text("Arroz Tio João 5kg\t24,90\nFeijão Camil 1kg\t7,99\n",
                   encoding="utf-8")
    sumiu = str(tmp_path / "sumiu.txt")   # não existe → erro na leitura
    res, erros = servico.importar_varios([str(txt), sumiu], lambda _m: None)
    assert len(res.itens) == 2            # o txt válido foi lido apesar do erro
    assert len(erros) == 1 and erros[0][0] == "sumiu.txt"
    assert res.aviso and "erro" in res.aviso.lower()   # I2: visível


# --- Bloco B: aceitar-verdes (R-053) + encher-página (R-056) -----------------

def _itemesa(nome, semaforo="VERDE", foto=True, preco="5,00"):
    from app.qt.telas import servico
    it = servico.ItemMesa(nome, preco, semaforo, nome)
    it.imagem = "x.png" if foto else None
    return it


def test_separar_por_semaforo_so_verdes():
    """R-053/passo 19+22: 'aceitar verdes' separa só os verdes — não toca
    amarelo/vermelho."""
    from app.qt.telas import servico
    itens = [_itemesa("A", "VERDE"), _itemesa("B", "AMARELO"),
             _itemesa("C", "VERDE"), _itemesa("D", "VERMELHO")]
    verdes, amarelos, vermelhos = servico.separar_por_semaforo(itens)
    assert [x.nome for x in verdes] == ["A", "C"]
    assert [x.nome for x in amarelos] == ["B"]
    assert [x.nome for x in vermelhos] == ["D"]


def test_plano_encher_pagina_por_uid_com_prevoo():
    """R-056/passo 23-24+67 (I1/I2): distribui por UID; pré-voo ANTES avisa o
    item sem foto que entrou; o resto que não coube volta na lista."""
    from app.qt.telas import servico
    itens = [_itemesa("A"), _itemesa("B", foto=False), _itemesa("C"),
             _itemesa("D"), _itemesa("E", preco="2x 5,00")]
    slots = ["s0", "s1", "s2"]
    mapa, resto, avisos = servico.plano_encher_pagina(itens, slots)
    # vínculo por UID (I1), não por posição
    assert mapa == {"s0": itens[0].uid, "s1": itens[1].uid, "s2": itens[2].uid}
    assert [x.nome for x in resto] == ["D", "E"]          # o que não coube
    assert any("B" in a and "sem foto" in a for a in avisos)   # pré-voo antes (I2)


# --- Bloco C: diff da edição anterior (R-062) -------------------------------

def test_diff_edicoes_casa_por_chave_natural_nao_posicao():
    """R-062/passo 46+77 (I1): casa o mesmo produto por produto_id, NUNCA por
    posição — embaralhar a ordem não muda o diff. Prova de mutação embutida:
    se casasse por índice, o Arroz (pos 0 antes, pos 1 agora) não seria achado."""
    from app.qt.telas import servico

    def it(nome, pid, preco):
        i = servico.ItemMesa(nome, preco, "VERDE", nome)
        i.produto_id = pid
        return i

    anterior = [it("Arroz", 1, "20,00"), it("Feijão", 2, "8,00"),
                it("Óleo", 3, "9,00")]
    atual = [it("Leite", 4, "5,00"), it("Arroz", 1, "24,90"),   # ordem embaralhada
             it("Óleo", 3, "9,00")]
    d = servico.diff_edicoes(atual, anterior)
    assert [x.nome for x in d["novos"]] == ["Leite"]
    assert [x.nome for x in d["removidos"]] == ["Feijão"]
    assert len(d["precos"]) == 1
    it_mud, antigo, novo = d["precos"][0]
    assert it_mud.nome == "Arroz" and antigo == "20,00" and novo == "24,90"


def test_checklist_final_do_estado_real():
    """R-063/passo 49: o checklist marca sozinho o que está ok, a partir do
    estado REAL (foto/preço/validade/itens)."""
    from app.qt.telas import servico
    itens = [_itemesa("A", foto=True, preco="5,00"),
             _itemesa("B", foto=False, preco="2x 5,00")]   # sem foto, preço ruim
    checklist = dict((p, ok) for p, ok, _d in servico.checklist_final(itens, None))
    assert checklist["Todos os itens têm foto?"] is False       # B sem foto
    assert checklist["Todos os itens têm preço entendido?"] is False  # B "2x 5,00"
    assert checklist["A validade da oferta está definida?"] is False  # None
    assert checklist["Há itens na oferta?"] is True
    # tudo ok quando o estado está completo
    bom = [_itemesa("X", foto=True, preco="5,00")]
    ck = dict((p, ok) for p, ok, _d in servico.checklist_final(bom, "ATÉ 20/07"))
    assert all(ck.values())


# --- Raiz do segfault: nenhum timer/worker vivo no teardown -----------------

def test_mesa_close_encerra_timer_do_rascunho(raiz_tmp):
    """Lei 'verde com crash no exit NÃO é verde' (F7.1): ao fechar, a Mesa PARA
    o timer do rascunho — a raiz do segfault de teardown (QTimer/QThread vivo)."""
    from PySide6.QtCore import Qt

    from app.qt.telas.mesa import MesaTela
    _app()
    m = MesaTela()
    m.setAttribute(Qt.WidgetAttribute.WA_DontShowOnScreen, True)
    m.show()                                     # showEvent liga o timer (~2min)
    QApplication.processEvents()
    assert m._timer_rascunho.isActive()          # está rodando
    m.close()                                    # closeEvent
    assert not m._timer_rascunho.isActive()      # parou — nada vivo no teardown


def test_conciliacao_done_encerra_workers(raiz_tmp):
    """Teste-ESPELHO do `closeEvent` da Mesa (pedido do arquiteto no selo da F7):
    `ConciliacaoDialog.done()` CANCELA as filas e ENCERRA os workers — a mesma
    lição RG-05b/F7.1 (fila viva com o dono destruído derruba o processo). Prova
    de mutação: sem o cancelar/encerrar no done(), a fila fica viva (_cancelado
    False) e o worker sobrevive sob o gerenciador."""
    from app.qt.telas.conciliacao_dialog import ConciliacaoDialog
    from app.qt.telas.servico import ItemMesa, ResultadoMesa
    _app()
    # um VERMELHO faz o diálogo DISPARAR a fila de enriquecimento (worker vivo)
    itens = [ItemMesa("DOCE DE BANANA VAL 250 G", "6,66", "VERMELHO",
                      "DOCE DE BANANA VAL 250 G")]
    dlg = ConciliacaoDialog(ResultadoMesa(itens=itens))
    fila = dlg._fila_enriquecer
    assert fila is not None and fila._cancelado is False   # a fila nasceu viva
    dlg.done(0)                                            # junta as pontas
    assert fila._cancelado is True                # cancelou a fila (por conteúdo)
    QApplication.processEvents()
    assert dlg._trabalhos._vivos == []            # nada vivo sob o dono destruído


# --- R-052: conciliação em TELA CHEIA com a foto ao lado --------------------

def test_conciliacao_tela_cheia_foto_mesmo_servico(raiz_tmp, tmp_path):
    """R-052 (fix #3 do arquiteto): quando a fonte é FOTO, a conciliação abre em
    tela cheia com o print original ao lado — porém lendo do MESMO serviço
    (`conciliar_linhas`). Paridade POR CONSTRUÇÃO: com e sem foto o conjunto de
    itens/semáforo é IDÊNTICO (a foto não muda a conciliação); só o diálogo
    ganha o painel da imagem. O recorte-por-linha fica deferido (sem bbox no OCR).
    """
    from PIL import Image

    from app.qt.telas import servico
    from app.qt.telas.conciliacao_dialog import ConciliacaoDialog
    _app()

    foto = tmp_path / "tabela.png"
    Image.new("RGB", (60, 40), (240, 240, 240)).save(foto)
    linhas = [("Arroz Tio João 5kg", "24,90", None),
              ("Feijão Carioca 1kg", "7,99", None)]
    cb = lambda *a, **k: None                       # noqa: E731

    com = servico.conciliar_linhas(linhas, cb, caminho_fonte=str(foto))
    sem = servico.conciliar_linhas(linhas, cb)      # tabela de texto, sem foto

    # PARIDADE do serviço: mesmos nomes, mesmos semáforos — só a fonte muda
    assert [(i.nome, i.semaforo) for i in com.itens] == \
           [(i.nome, i.semaforo) for i in sem.itens]
    assert com.caminho_fonte == str(foto) and sem.caminho_fonte is None

    # O diálogo com foto abre em tela cheia e mostra a imagem original
    dlg_foto = ConciliacaoDialog(com)
    assert dlg_foto._tela_cheia is True
    assert getattr(dlg_foto, "_foto_lbl", None) is not None
    assert not dlg_foto._foto_lbl.pixmap().isNull()   # a foto REAL, por conteúdo
    # ...e o conjunto de itens do diálogo é o mesmo do caminho sem foto
    dlg_texto = ConciliacaoDialog(sem)
    assert dlg_texto._tela_cheia is False
    assert getattr(dlg_texto, "_foto_lbl", None) is None
    assert [(i.nome, i.semaforo) for i in dlg_foto.itens] == \
           [(i.nome, i.semaforo) for i in dlg_texto.itens]
    dlg_foto.close()
    dlg_texto.close()


# --- R-058: frases prontas com {data}/{evento} ------------------------------

def test_resolver_frase_data_evento_e_faltante_visivel():
    """R-058/passo 37: {data} e {evento} se resolvem sozinhos; a variável SEM
    valor fica VISÍVEL como {chave} e entra em `faltantes` (I2 — nunca some
    calada). Prova de mutação: se resolvesse à toa, faltaria a chave visível."""
    from app.qt.telas import servico
    texto, faltantes = servico.resolver_frase(
        "Ofertas do {evento} — válidas {data}",
        {"evento": "Sexta Verde", "data": "20/07"})
    assert texto == "Ofertas do Sexta Verde — válidas 20/07"
    assert faltantes == []
    # variável sem valor: fica visível e é reportada
    t2, f2 = servico.resolver_frase("Válido {data}", {"evento": "X"})
    assert t2 == "Válido {data}" and f2 == ["data"]


# --- R-059: alerta de repetição ---------------------------------------------

def test_alerta_repeticao_dispara_no_terceiro():
    """R-059/passo 40+56: o alerta dispara no 3º encarte seguido; 2 seguidos
    ainda não; uma edição SEM o produto zera a contagem (informativo, não
    bloqueia). Prova de mutação: contar por posição/total daria outro número."""
    from app.qt.telas import servico
    chave = ("ean", "789")
    hist2 = [{("ean", "789")}, {("ean", "789")}]                 # 2 seguidas
    hist3 = [{("ean", "789")}, {("ean", "789")}, {("ean", "789")}]  # 3 seguidas
    assert servico.alerta_repeticao(chave, hist2) is None
    assert "3 edições" in servico.alerta_repeticao(chave, hist3)
    # o produto sumiu na do meio → a sequência recente é só 1
    quebrado = [{("ean", "789")}, set(), {("ean", "789")}]
    assert servico.semanas_seguidas(chave, quebrado) == 1


# --- R-072: estatística da montagem (offline) -------------------------------

def test_resumo_montagem_itens_por_minuto():
    """R-072/passo 51+57: itens por minuto do estado REAL; local (só um dict, sem
    rede). Prova de mutação: 40 itens / 120s = 20/min (fórmula errada muda)."""
    from app.qt.telas import servico
    r = servico.resumo_montagem(120.0, 40)
    assert r["itens_por_minuto"] == 20.0
    assert r["itens"] == 40 and r["segundos"] == 120.0
    assert "40 itens" in r["resumo"] and "/min" in r["resumo"]
    assert servico.resumo_montagem(0.0, 5)["itens_por_minuto"] == 0.0  # sem divisão por zero


# --- R-071: observação por item (região condicional) ------------------------

def test_observacao_desenha_so_quando_preenchida():
    """R-071/passo 30-31: a observação vira uma região de papel OBSERVACAO —
    CONDICIONAL: desenha o texto do item quando preenchida, e "" quando vazia
    (a região não pinta). Fonte única `texto_composto_legal`. Prova de mutação:
    se ignorasse o papel, cairia no texto_fixo/validade e o teste falharia."""
    from app.rendering.compositor import DadosProduto, texto_composto_legal
    from app.rendering.model import (
        PapelTexto, Regiao, Retangulo, TipoRegiao)
    reg = Regiao(tipo=TipoRegiao.TEXTO_LEGAL, rect=Retangulo(0, 0, 40, 10),
                 papel_texto=PapelTexto.OBSERVACAO)
    com = DadosProduto(nome="Arroz", observacao="Limite de 2 por cliente")
    sem = DadosProduto(nome="Arroz", observacao=None)
    assert texto_composto_legal(reg, com) == "Limite de 2 por cliente"
    assert texto_composto_legal(reg, sem) == ""      # condicional: vazia não pinta
    # e a validade da oferta NÃO vaza para a região de observação
    val = DadosProduto(nome="Arroz", texto_legal="ATÉ 20/07")
    assert texto_composto_legal(reg, val) == ""


def test_observacao_papel_faz_roundtrip_no_layout():
    """R-071 (I3/Bloco E): o papel OBSERVACAO sobrevive a salvar→carregar sem
    virar LIVRE. Prova de mutação: sem o valor no enum, o from_dict quebraria."""
    from app.rendering.model import (
        PapelTexto, Regiao, Retangulo, TipoRegiao)
    reg = Regiao(tipo=TipoRegiao.TEXTO_LEGAL, rect=Retangulo(0, 0, 40, 10),
                 papel_texto=PapelTexto.OBSERVACAO)
    reg2 = Regiao.from_dict(reg.to_dict())
    assert reg2.papel_texto == PapelTexto.OBSERVACAO


def test_banco_observacoes_e_frases_semeados():
    """R-071/R-058: os bancos de observações e de frases vêm semeados (o dono
    escolhe rápido). Prova de mutação: listas vazias reprovariam."""
    from app.qt.telas import servico
    obs = servico.banco_observacoes()
    assert any("por cliente" in o for o in obs)
    assert any("{data}" in f or "{evento}" in f for f in servico.BANCO_FRASES)


def test_planilha_edita_observacao_do_item():
    """R-071 (passo 84 anti-órfão): a observação é editável na planilha da estante
    e grava no item — o laço fecha (planilha → item.observacao → região). Prova
    de mutação: sem a coluna em aplicar_edicao, o texto não gravaria."""
    from app.qt.telas import planilha
    it = _itemesa("Arroz")
    assert "Observação" in planilha.COLUNAS and "Observação" in planilha.EDITAVEIS
    gravou, aviso = planilha.aplicar_edicao(it, "Observação", "Limite de 2 por cliente")
    assert gravou and aviso is None
    assert it.observacao == "Limite de 2 por cliente"
    assert planilha.valor_da_coluna(it, "Observação") == "Limite de 2 por cliente"
    # limpar volta a None (não desenha — condicional)
    planilha.aplicar_edicao(it, "Observação", "")
    assert it.observacao is None


# ===========================================================================
# BLOCO D — robustez do parser e do fluxo (passos 59–72)
# ===========================================================================

@pytest.mark.parametrize("texto,nome_esp,preco_ok", [
    # WhatsApp Web (preço no fim, com/sem R$)
    ("Arroz Tio João 5kg  R$ 24,90", "Arroz Tio João 5kg", True),
    ("Refrigerante Guaraná 2L 6,49", "Refrigerante Guaraná 2L", True),
    # Excel (tab)
    ("Feijão Carioca 1kg\t7,99", "Feijão Carioca 1kg", True),
    # ponto-e-vírgula
    ("Leite Integral 1L;4,29", "Leite Integral 1L", True),
    # pipe
    ("Café Pilão 500g|12,90", "Café Pilão 500g", True),
    # decimal com ponto
    ("Pão de Forma;5.99", "Pão de Forma", True),
    # milhar brasileiro
    ("Azeite Gallo 500ml;R$ 1.299,00", "Azeite Gallo 500ml", True),
    # nome com hífen não confunde o preço no fim
    ("Coca-Cola 2L  R$ 8,99", "Coca-Cola 2L", True),
    # sem preço → amarelo, mas o nome sai limpo
    ("Sabonete Dove", "Sabonete Dove", False),
])
def test_bloco_d_bateria_colagens_reais(texto, nome_esp, preco_ok):
    """Bloco D/passo 59-61: a bateria das variações do mundo real (WhatsApp Web,
    Excel/tab, ;, |, decimal ponto/vírgula, milhar, hífen no nome). O parser
    separa nome × preço e normaliza pelo P0.3, sem palpite no ambíguo."""
    linhas = parse_colagem(texto)
    assert len(linhas) == 1
    assert linhas[0].nome == nome_esp
    assert linhas[0].preco_valido is preco_ok


def test_bloco_d_multi_preco_na_colagem_vs_ambiguo():
    """Bloco D/passo 62: multi-preço reconhecido DENTRO da colagem ("Sabão;3 por
    R$10"); "2x 5,00" NÃO vira multi-preço e cai como preço a rever (I2) — os
    dois lado a lado. Prova de mutação: sem `_split_multi`, a 1ª linha cairia
    em vermelho falso (preço "não entendido")."""
    linhas = parse_colagem("Sabão OMO 1,6kg\t3 por R$ 10,00\n"
                           "Refrigerante 2L;leve 3 pague 2\n"
                           "Detergente Ypê;2x 5,00")
    assert linhas[0].multi_preco == "3 por R$ 10,00" and linhas[0].preco is None
    assert linhas[0].preco_valido                    # promoção TEM preço
    assert linhas[1].multi_preco == "Leve 3 pague 2"
    assert linhas[2].multi_preco is None             # "2x 5,00" não é promoção
    assert not linhas[2].preco_valido                # segue rejeitado (I2)


def test_bloco_d_multi_preco_colado_propaga_ao_item(raiz_tmp):
    """Bloco D: o multi-preço reconhecido na colagem CHEGA ao ItemMesa via
    `conciliar_linhas(multi_precos=...)` — a tupla leva só o valor, a promoção
    viaja à parte. Prova de mutação: sem `multi_precos`, o item ficaria sem
    promoção e cairia como 'sem preço' no pré-voo."""
    from app.qt.telas import servico
    from app.qt.telas.colagem import (
        linhas_para_tuplas, multi_precos_de, parse_colagem)
    _app()
    linhas = parse_colagem("Sabão OMO 1,6kg\t3 por R$ 10,00\n"
                           "Leite Integral 1L;4,29")
    res = servico.conciliar_linhas(
        linhas_para_tuplas(linhas), lambda *a, **k: None,
        multi_precos=multi_precos_de(linhas))
    assert res.itens[0].multi_preco == "3 por R$ 10,00"
    assert res.itens[1].multi_preco is None
    # nenhum acusa "sem preço": o Sabão é promoção (R-070), o Leite tem 4,29
    sem_preco = [it for it in res.itens
                 if servico.preco_decimal(it.preco) is None and not it.multi_preco]
    assert sem_preco == []


def test_bloco_d_multi_import_20_arquivos_1_corrompido(raiz_tmp, tmp_path):
    """Bloco D/passo 64 (I2): 20 arquivos de uma vez, UM corrompido no meio — a
    fila TERMINA, o corrompido fica marcado, e NENHUM outro se perde. Prova de
    mutação: se a fila abortasse no erro, os itens dos arquivos 11–20 sumiriam."""
    from app.qt.telas import servico
    caminhos = []
    for i in range(20):
        f = tmp_path / f"tabela_{i:02d}.txt"
        if i == 10:                                  # o corrompido, no meio
            f.write_bytes(b"\xff\xfe\x00 lixo binario \x80\x81")  # UTF-8 inválido
        else:
            f.write_text(f"Arroz Marca{i} 5kg|{i + 1},00\n"
                         f"Feijão Marca{i} 1kg|{i + 2},50\n", encoding="utf-8")
        caminhos.append(str(f))
    resultado, erros = servico.importar_varios(caminhos, lambda *a, **k: None)
    assert len(erros) == 1 and "tabela_10.txt" in erros[0][0]   # o corrompido, nomeado
    assert len(resultado.itens) == 19 * 2                       # nenhum dos 19 se perdeu
    assert resultado.aviso and "1 de 20" in resultado.aviso     # visível (I2)


# ===========================================================================
# CASCA VISUAL — campo qtd+valor do multi-preço (R-070)
# ===========================================================================

def test_compor_multi_preco_round_trip():
    """Casca R-070: o campo qtd+valor compõe o texto e ele ROUND-TRIPA por
    `parse_multi_preco` (a mesma lógica que desenha/reconhece). Prova de
    mutação: valor inválido não compõe promoção (I2)."""
    from app.qt.telas.colagem import (
        compor_leve_pague, compor_multi_preco, parse_multi_preco)
    t = compor_multi_preco(3, "10,00")
    assert t == "3 por R$ 10,00"
    assert parse_multi_preco(t).quantidade == 3          # round-trip
    assert compor_multi_preco(3, "2x 5,00") is None      # valor ruim → None (I2)
    assert compor_multi_preco(0, "10,00") is None        # qtd < 1
    assert compor_leve_pague(3, 2) == "Leve 3 pague 2"
    assert compor_leve_pague(2, 3) is None               # leve <= pague não é promoção


def test_promocao_dialog_compoe_e_limpa():
    """Casca R-070: o `PromocaoDialog` monta o texto do formato escolhido e o
    botão 'Sem promoção' devolve limpar=True/resultado=None (tira a promoção)."""
    from app.qt.telas.promocao_dialog import PromocaoDialog
    _app()
    dlg = PromocaoDialog("3 por R$ 10,00")
    dlg.qtd.setValue(4)
    dlg.valor.setText("12,00")
    assert dlg._texto_atual() == "4 por R$ 12,00"
    dlg.formato.setCurrentIndex(1)               # "Leve N pague M"
    dlg.qtd.setValue(3)
    dlg.pague.setValue(2)
    assert dlg._texto_atual() == "Leve 3 pague 2"
    dlg._sem_promocao()
    assert dlg.limpar is True and dlg.resultado is None
    dlg.close()


# ===========================================================================
# CASCA VISUAL — frases prontas (R-058), estatística (R-072), alerta (R-059)
# ===========================================================================

def test_frases_selector_resolve_no_dialogo():
    """Casca R-058: o `DialogoPapelTexto` insere uma frase pronta JÁ resolvida
    pelo contexto ({evento} vira o nome real). Reusa `resolver_frase`. Prova de
    mutação: sem passar o contexto, o texto sairia com {evento} literal."""
    from app.qt.design.papel_texto_ui import _dialogo_cls
    from app.rendering.model import PapelTexto
    _app()
    Dlg = _dialogo_cls()
    dlg = Dlg(None, papel=PapelTexto.LIVRE,
              contexto={"data": "20/07", "evento": "Sexta Verde"})
    dlg.selecionar(PapelTexto.LIVRE)
    # combo: idx 0 = "Frases prontas…"; idx 2 = "Ofertas do {evento}"
    assert dlg.combo_frases.itemText(2) == "Ofertas do {evento}"
    dlg._inserir_frase(2)
    assert dlg.edit_livre.text() == "Ofertas do Sexta Verde"
    dlg.close()


def test_alertas_de_repeticao_historico_injetado():
    """Casca R-059: com o histórico injetado, o item que aparece nas 3 edições
    seguidas dispara o alerta; o que não repete, não. Prova de mutação: casar
    por posição em vez de chave natural mudaria quem dispara."""
    from app.qt.telas import servico
    arroz = _itemesa("Arroz")
    arroz.produto_id = 7                       # chave forte estável
    novo = _itemesa("Manteiga")
    novo.produto_id = 9
    hist = [{("pid", 7)}, {("pid", 7)}, {("pid", 7)}]   # arroz nas 3 seguidas
    fora = servico.alertas_de_repeticao([arroz, novo], hist)
    assert [it.nome for it, _aviso in fora] == ["Arroz"]
    assert "3 edições" in fora[0][1]


def test_chaves_edicoes_anteriores_banco_vazio_nao_quebra(raiz_tmp):
    """Casca R-059: sem edições salvas, o histórico é vazio e o alerta não
    dispara (nem quebra o fluxo — I2, aviso é opcional)."""
    from app.qt.telas import servico
    assert servico.chaves_edicoes_anteriores() == []
    assert servico.alertas_de_repeticao([_itemesa("Arroz")]) == []


def test_mesa_estatistica_e_contexto_frases(raiz_tmp):
    """Casca R-072/R-058: a Mesa mostra a estatística no rodapé quando há itens,
    e expõe o contexto das frases ({data} = validade da oferta)."""
    from app.qt.telas.mesa import MesaTela
    _app()
    m = MesaTela()
    m._itens = [_itemesa("A"), _itemesa("B")]
    m._recarregar_lista()
    assert "2 item(ns)" in m._estatistica_lbl.text()      # R-072 no rodapé
    m._validade = "ATÉ 20/07"
    assert m.contexto_frases().get("data") == "ATÉ 20/07"  # R-058 contexto vivo
    m.close()


def test_planilha_mostra_promocao_na_coluna_preco():
    """Casca R-070: a planilha exibe o multi-preço na coluna Preço (não vazio) e
    NÃO o marca como 'sem preço'. Prova de mutação: sem o fallback, a célula
    ficaria vazia e o item de promoção pareceria 'sem preço'."""
    from app.qt.telas import planilha
    it = _itemesa("Sabão", preco="5,00")
    it.preco = None
    it.multi_preco = "3 por R$ 10,00"
    assert planilha.valor_da_coluna(it, "Preço") == "3 por R$ 10,00"
    assert planilha.problema_na_celula(it, "Preço") is None    # tem preço (promoção)

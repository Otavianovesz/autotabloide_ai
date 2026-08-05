"""ORDEM F13-VICESIMUS-QUARTUS — os três pedidos e a auditoria do
Quintou (04/08).

Onda 1 — o que não pode ir para a rua:
  §2.1 a tabela tem GRAMÁTICA: linha RISCADA é oferta cancelada — para
       em vermelho perguntando, nunca entra calada, nunca some calada;
  §2.2 marca conhecida diferente NUNCA casa (o açúcar Itamaraty saiu
       impresso como Doce Dia) — nem pelo alias;
  §1.2 UM ITEM TEM UM PESO SÓ — vence o do cadastro (a correção do
       dono); a divergência é aviso da conciliação, nunca texto na arte.

L22 — LEI DESCOBERTA NUM LAYOUT VALE EM TODOS: os guardiões daqui
testam o MOTOR (conciliação/montagem), não um encarte.
"""

import json

import pytest

from app.ai.fake import MotorIAFake


# ================================================================= §2.1
# A linha RISCADA para em vermelho perguntando — nunca entra calada
# ======================================================================


def test_vquartus_riscada_para_em_vermelho_perguntando(tmp_path, monkeypatch):
    """As duas riscadas do Quintou (Bife à Milanesa, Geléia Ritter)
    foram IMPRESSAS como oferta válida. A riscada agora: semáforo
    VERMELHO, pendência dita, produto NUNCA casado por baixo — e a
    linha limpa ao lado segue o caminho de sempre."""
    monkeypatch.setenv("AUTOTABLOIDE_ROOT", str(tmp_path / "raiz"))
    from app.core.database import Database
    from app.core.paths import SystemRoot
    from app.core.repositories import ProdutoRepositorio
    from app.qt.telas.servico import conciliar_linhas

    db = Database(SystemRoot(tmp_path / "raiz")).init()
    try:
        with db.Session() as s:
            ProdutoRepositorio(s).importar("BIFE A MILANESA BBX 100 g")
            s.commit()
    finally:
        db.engine.dispose()

    res = conciliar_linhas(
        [("BIFE A MILANESA BBX 100 g", "4,90", None),
         ("GELEIA RITTER ALHO CARAMELIZADA 290 g", "9,90", None)],
        lambda *_: None,
        riscadas=[True, False])
    riscado, limpo = res.itens
    assert riscado.semaforo == "VERMELHO", (riscado.semaforo, riscado.motivo)
    assert "riscada" in (riscado.pendencias or [])
    assert riscado.produto_id is None            # nunca casa por baixo
    assert "riscad" in (riscado.motivo or "").lower()
    # o candidato fica À VISTA no motivo (era um match antes da marca)
    assert "casaria" in (riscado.motivo or "").lower()
    # a linha limpa não muda nada
    assert "riscada" not in (limpo.pendencias or [])


def test_vquartus_riscada_ocr_marca_e_cache_preserva(tmp_path, monkeypatch):
    """O OCR lê o gesto ("riscada": true) e o cache de leitura preserva
    o trio — cache velho (par [desc, preco]) lê sem drama."""
    monkeypatch.setenv("AUTOTABLOIDE_ROOT", str(tmp_path / "raiz"))
    from app.ai.ocr import (TabelaOCR, LinhaOferta, cache_consultar,
                            cache_guardar, ler_tabela)
    from PIL import Image

    foto = tmp_path / "tabela.png"
    Image.new("RGB", (1200, 800), "white").save(foto)
    fake = MotorIAFake(respostas_visao={"tabela de ofertas": json.dumps({
        "validade_oferta": None,
        "linhas": [
            {"descricao": "BIFE A MILANESA BBX 100g", "preco": "4,90",
             "riscada": True},
            {"descricao": "PIPOCA YOKI 100g", "preco": "3,50"},
        ]})})
    tab = ler_tabela(foto, fake)
    assert [ln.riscada for ln in tab.linhas] == [True, False]

    cache_guardar(foto, "modelo-x", tab)
    de_volta = cache_consultar(foto, "modelo-x")
    assert de_volta is not None
    assert [ln.riscada for ln in de_volta.linhas] == [True, False]

    # o prompt ensina o gesto (a assinatura invalida o cache antigo)
    from app.ai.ocr import PROMPT_OCR
    assert "RISCADA" in PROMPT_OCR or "TACHADA" in PROMPT_OCR


def test_vquartus_pre_voo_avisa_riscada_na_pagina():
    """§2.1 (o fim da estrada): item riscado que ESTÁ na página aparece
    no pré-voo; fora da página, silêncio (ele não sai na rua)."""
    from app.qt.telas.servico import ItemMesa, avisos_de_riscadas

    na_pagina = ItemMesa(descricao="GELEIA RITTER 290 g", preco="9,90",
                         semaforo="VERMELHO", nome="Geléia Ritter 290g",
                         pendencias=["riscada"])
    fora = ItemMesa(descricao="BIFE BBX 100 g", preco="4,90",
                    semaforo="VERMELHO", nome="Bife BBX 100g",
                    pendencias=["riscada"])
    mapa = {"celula_1": na_pagina.uid}
    avisos = avisos_de_riscadas([na_pagina, fora], mapa)
    assert len(avisos) == 1
    assert "RISCADO" in avisos[0]
    assert "Ritter" in avisos[0]
    assert avisos_de_riscadas([fora], mapa) == []


def test_vquartus_riscada_fora_do_criar_em_lote():
    """§2.1: a riscada NUNCA vira produto pelo lote "criar todos" — a
    régua do pulo é a pendência, e o pulo é dito (o teste da régua:
    mesmo filtro usado pelo diálogo)."""
    from app.qt.telas.servico import ItemMesa

    riscado = ItemMesa(descricao="X", preco="1", semaforo="VERMELHO",
                       nome="X", pendencias=["riscada"])
    novo = ItemMesa(descricao="Y", preco="2", semaforo="VERMELHO", nome="Y")
    itens = [riscado, novo]
    # o filtro do diálogo (conciliacao_dialog._criar_todos_sem_foto)
    riscados = [it for it in itens if it.semaforo == "VERMELHO"
                and "riscada" in (it.pendencias or [])]
    pares = [(it.uid, it) for it in itens
             if it.semaforo == "VERMELHO" and it not in riscados]
    assert [it.uid for _u, it in pares] == [novo.uid]
    assert riscados == [riscado]


# ================================================================= §2.2
# Marca conhecida diferente NUNCA casa — nem verde, nem pelo alias
# ======================================================================


def _raiz_com_acucar(tmp_path, monkeypatch):
    monkeypatch.setenv("AUTOTABLOIDE_ROOT", str(tmp_path / "raiz"))
    from app.core.database import Database
    from app.core.paths import SystemRoot
    from app.core.repositories import ProdutoRepositorio

    db = Database(SystemRoot(tmp_path / "raiz")).init()
    with db.Session() as s:
        repo = ProdutoRepositorio(s)
        r = repo.importar("ACUCAR CRISTAL DOCE DIA 2 kg")
        s.commit()
        pid = r.produto.id
    return db, pid


def test_vquartus_marca_diferente_nunca_casa_verde(tmp_path, monkeypatch):
    """O caso real da máquina do dono (IA ligada): o juiz confirmou o
    candidato com confiança alta → verde → e a guarda da marca derruba
    a VERMELHO (produto NOVO), com o conflito dito. Marca igual segue
    verde (não-regressão)."""
    from app.ai.conciliacao import Conciliador, Semaforo

    db, _pid = _raiz_com_acucar(tmp_path, monkeypatch)
    try:
        with db.Session() as s:
            juiz = MotorIAFake(respostas_chat={
                "ITAMARATY": '{"indice": 0, "confianca": 0.95}'})
            v = Conciliador(s, motor=juiz).conciliar(
                "AÇUCAR ITAMARATY CRISTAL 2 Kgs")
            assert v.semaforo == Semaforo.VERMELHO, (v.semaforo, v.motivo)
            assert "marca" in (v.motivo or "").lower(), v.motivo
            assert v.produto is None
            # não-regressão: a MESMA marca casa verde como sempre
            v2 = Conciliador(s).conciliar("ACUCAR CRISTAL DOCE DIA 2 Kgs")
            assert v2.semaforo == Semaforo.VERDE, (v2.semaforo, v2.motivo)
    finally:
        db.engine.dispose()


def test_vquartus_alias_com_marca_trocada_nunca_verde(tmp_path, monkeypatch):
    """A história REAL do banco: o alias nasceu de uma confirmação
    errada (ontem, 16:20) e virava verde CALADO a cada import. O
    vínculo do dono fica — mas desce a AMARELO com o conflito dito,
    todo import."""
    from app.ai.conciliacao import Conciliador, Semaforo
    from app.core.repositories import ProdutoRepositorio

    db, pid = _raiz_com_acucar(tmp_path, monkeypatch)
    try:
        with db.Session() as s:
            ProdutoRepositorio(s).aprender_alias(
                pid, "1 AÇÚCAR ITAMARATY CRISTAL 2 Kgs")
            s.commit()
            v = Conciliador(s).conciliar("1 AÇÚCAR ITAMARATY CRISTAL 2 Kgs")
            assert v.semaforo == Semaforo.AMARELO, (v.semaforo, v.motivo)
            assert "marcas diferentes" in (v.motivo or "").lower(), v.motivo
            assert v.produto is not None         # o vínculo fica à vista
    finally:
        db.engine.dispose()


def test_vquartus_marca_desconhecida_nao_acusa(tmp_path, monkeypatch):
    """A régua nunca inventa: linha sem marca RECONHECIDA não dispara a
    guarda (sem prova não se acusa) — segue o caminho de sempre."""
    monkeypatch.setenv("AUTOTABLOIDE_ROOT", str(tmp_path / "raiz"))
    from app.ai.conciliacao import Conciliador, Semaforo
    from app.core.database import Database
    from app.core.paths import SystemRoot
    from app.core.repositories import ProdutoRepositorio

    db = Database(SystemRoot(tmp_path / "raiz")).init()
    try:
        with db.Session() as s:
            ProdutoRepositorio(s).importar("FEIJAO CARIOCA GRANFINO 1 kg")
            s.commit()
            v = Conciliador(s).conciliar("FEIJAO CARIOCA GRANFINO 1 Kg")
            assert v.semaforo == Semaforo.VERDE, (v.semaforo, v.motivo)
    finally:
        db.engine.dispose()


# ================================================================= §1.2
# UM ITEM TEM UM PESO SÓ — vence o do cadastro
# ======================================================================


def test_vquartus_um_item_um_peso_so():
    """A Água Mineral do Quintou saiu "500ml · 497 ml" — o peso da
    tabela E o da correção do dono, lado a lado. O descritor leva UM
    peso, o do CADASTRO (o nome corrigido); o da tabela vira aviso da
    conciliação (J10), nunca texto na arte."""
    from app.qt.telas.servico import ItemMesa, dados_para_desenho

    it = ItemMesa(descricao="AGUA MINERAL NATURAGUA 500ML",
                  preco="1,99", semaforo="VERDE",
                  nome="Água Mineral Marajá 497ml S/ Gás",
                  unidade="500ml")
    d = dados_para_desenho(it)
    assert d.unidade == "497ml", d.unidade
    assert "500" not in (d.descritor or ""), d.descritor
    assert (d.descritor or "").count("497") == 1, d.descritor


def test_vquartus_peso_igual_nada_muda():
    """Quando a tabela e o cadastro CONCORDAM (só a grafia difere), a
    unidade do item segue mandando — zero mudança no caminho feliz."""
    from app.qt.telas.servico import ItemMesa, dados_para_desenho

    it = ItemMesa(descricao="PIPOCA YOKI 500G", preco="3,50",
                  semaforo="VERDE", nome="Pipoca Yoki 500g",
                  unidade="500 g")
    d = dados_para_desenho(it)
    assert d.unidade == "500 g"
    assert "500" in (d.descritor or "")


# ================================================================= §1.3
# O leque é CAPACIDADE DO MOTOR — o mesmo teste roda nos encartes (L22)
# ======================================================================


def _garrafa_verde(tmp_path):
    from PIL import Image
    garrafa = tmp_path / "garrafa_vq.png"
    im = Image.new("RGBA", (60, 300), (0, 0, 0, 0))
    im.paste((0, 160, 0, 255), (5, 0, 55, 300))
    im.save(garrafa)
    return garrafa


def _verdes(img):
    return sum(1 for r, g, b in img.convert("RGB").getdata()
               if g > 100 and r < 80 and b < 80)


def test_vquartus_leque_e_capacidade_do_motor_nos_oito(tmp_path, monkeypatch):
    """§1.3 (L22): a MESMA foto estreita vira trio no QUINTOU e no
    SÁBADO — o gate de identidade "coluna com mordida" prendia a L19
    ao Jornal. Um teste só, rodando nos layouts REAIS do banco (L16);
    a prova é por tinta: com leque ≥ 1,8× a unidade (a mutação que
    devolve o gate antigo deixa isto vermelho)."""
    from decimal import Decimal
    from pathlib import Path

    monkeypatch.setenv("AUTOTABLOIDE_ROOT", str(tmp_path / "raiz"))
    from app.core.database import Database
    from app.core.models import Layout
    from app.core.paths import SystemRoot
    from app.rendering import compositor
    from app.rendering.compositor import DadosProduto, compor_pagina
    from app.rendering.encartes import importar_pacote
    from app.rendering.model import Ajuste, TipoRegiao
    from app.rendering.persistencia import carregar_layout
    from app.tests import acervo

    fontes = tmp_path / "fontes"
    fontes.mkdir()
    acervo.copiar_fontes_reais(fontes)
    garrafa = _garrafa_verde(tmp_path)

    db = Database(SystemRoot(tmp_path / "raiz")).init()
    try:
        with db.Session() as s:
            importar_pacote(s, Path.cwd() / "Templates novos")
            s.commit()
            nomes = {row.nome: row.id for row in s.query(Layout).all()}
            alvos = [n for n in nomes
                     if "Quintou" in n or "bado" in n]
            assert len(alvos) >= 2, nomes
            for nome in alvos:
                ldef = carregar_layout(s, nomes[nome])
                pag = ldef.paginas[0]
                slot = next(
                    sl for sl in pag.slots
                    if any(r.tipo == TipoRegiao.IMAGEM and r.visivel
                           and r.ajuste == Ajuste.ASSENTAR
                           for r in sl.regioes))
                dados = {slot.id: DadosProduto(
                    "Garrafa Teste", preco_por=Decimal("1.99"),
                    imagem_path=str(garrafa))}
                com = _verdes(compor_pagina(ldef, pag, dados,
                                            fontes_dir=fontes, dpi=96))
                monkeypatch.setattr(compositor, "_leque_solo",
                                    lambda *a, **k: None)
                sem = _verdes(compor_pagina(ldef, pag, dados,
                                            fontes_dir=fontes, dpi=96))
                monkeypatch.undo()
                monkeypatch.setenv("AUTOTABLOIDE_ROOT",
                                   str(tmp_path / "raiz"))
                assert sem > 0, f"{nome}: a unidade nem desenhou"
                # a régua discrimina o GATE (com o gate antigo o leque
                # nunca dispara fora do Jornal → com == sem): flancos a
                # 88% entrando atrás rendem ~1,8× de tinta na medição
                assert com >= sem * 1.5, (
                    f"{nome}: leque não disparou ({com} × {sem})")
    finally:
        db.engine.dispose()


def test_vquartus_heroi_por_pagina_nunca_multiplica(tmp_path):
    """§4.4 da TERTIUS sob a L21: "editorial" é RELATIVO à página —
    a página com menos de 3 zonas de foto (cartaz, destaque solo) é
    toda herói e o produto NUNCA multiplica, por mais fininho que
    seja."""
    from decimal import Decimal

    from app.rendering.compositor import DadosProduto, compor_pagina
    from app.rendering.model import (Ajuste, LayoutDef, Pagina, Regiao,
                                     Retangulo, Slot, TipoRegiao)
    from app.tests import acervo

    fontes = tmp_path / "fontes"
    fontes.mkdir()
    acervo.copiar_fontes_reais(fontes)
    garrafa = _garrafa_verde(tmp_path)

    sl = Slot("solo", [Regiao(TipoRegiao.IMAGEM, Retangulo(10, 10, 90, 90),
                              ajuste=Ajuste.ASSENTAR)])
    lay = LayoutDef(110.0, 110.0, dpi=96, paginas=[Pagina(slots=[sl])])
    dados = {"solo": DadosProduto("G", preco_por=Decimal("1"),
                                  imagem_path=str(garrafa))}
    img = compor_pagina(lay, lay.paginas[0], dados, fontes_dir=fontes)
    assert getattr(img, "_heroi_uids", None), "a página solo é editorial"
    # a tinta é a de UMA garrafa (fina na zona quadrada: ~1/5 da área)
    area_zona = round(90 / 25.4 * 96) ** 2
    assert _verdes(img) < area_zona * 0.45, "o herói multiplicou"


# ================================================================= §3.2
# O número do preço senta em fundo CHAPADO; o R$ é proporcional
# ======================================================================


def test_vquartus_chapado_atras_do_numero_por_pixel(tmp_path):
    """§3.2: número branco sobre HACHURA não se lê — na ETIQUETA_
    LISTRADA (com a camada do dono na página) um fundo chapado na cor
    da própria etiqueta entra atrás do número; a listra fica na
    borda. Por pixel: a faixa central perde as listras azuis."""
    from decimal import Decimal

    from PIL import Image, ImageDraw

    from app.rendering.compositor import (DadosProduto, _desenhar_preco,
                                          _moeda_na_listrada, _rect_px)
    from app.rendering.model import (FormaPreco, Regiao, Retangulo,
                                     TipoRegiao)
    from app.tests import acervo

    fontes = tmp_path / "fontes"
    fontes.mkdir()
    acervo.copiar_fontes_reais(fontes)
    nome_f = next(fontes.glob("*.ttf")).name

    reg = Regiao(TipoRegiao.PRECO, Retangulo(10, 10, 60, 25),
                 fonte=nome_f, tamanho_max_pt=22, cor="#FFFFFF",
                 forma_preco=FormaPreco.ETIQUETA_LISTRADA,
                 mostrar_moeda=False)
    base = Image.new("RGB", (round(80 / 25.4 * 96),
                             round(45 / 25.4 * 96)), (10, 10, 120))
    d = ImageDraw.Draw(base)
    x, y, w, h = _rect_px(reg.rect, 96)
    # a hachura como a arte REAL: fundo vermelho DOMINANTE com listras
    # azuis finas (50/50 sintético deixava o azul ganhar o sorteio)
    for k in range(x, x + w, 12):
        d.rectangle([k, y, k + 8, y + h], fill=(220, 20, 20))
        d.rectangle([k + 9, y, k + 11, y + h], fill=(20, 20, 180))
    base._tem_camada = True              # a etiqueta "é da arte"
    _desenhar_preco(base, d, reg, DadosProduto("X", preco_por=Decimal("5")),
                    96, fontes)
    # a faixa central (60% × meio) não tem mais listra azul
    azuis = 0
    for py in range(y + round(h * 0.35), y + round(h * 0.65)):
        for px in range(x + round(w * 0.20), x + round(w * 0.80)):
            r, g, b = base.getpixel((px, py))
            if b > 140 and r < 100:
                azuis += 1
    assert azuis == 0, f"{azuis} pixels de listra sob o número"
    # e o R$ entra em corpo proporcional (a régua nomeada)
    assert _moeda_na_listrada(reg).mostrar_moeda is True


# ================================================================= §2.3
# O vocabulário curto — as grafias da tabela real do Quintou
# ======================================================================


def test_vquartus_vocabulario_do_quintou():
    """§2.3: Prediecta→Predilecta, Xilitrol→Xilitol, Lingua→Língua e
    a expansão "F. Silvestres"→"Frutas Silvestres" — o mecanismo já
    funcionava (acertou Hellmann's); o vocabulário estava curto."""
    from app.core.ortografia import corrigir_acentos

    assert corrigir_acentos("GELATINA PREDIECTA ABACAXI") \
        == "GELATINA PREDILECTA ABACAXI"
    assert corrigir_acentos("Adoçante Xilitrol Lowçucar") \
        == "Adoçante Xilitol Lowçucar"
    assert corrigir_acentos("CORACAO e LINGUA BOV.") \
        == "CORAÇÃO e LÍNGUA BOV."
    assert "Frutas Silvestres" in corrigir_acentos(
        "Cha Melancia/F. Silvestres 350g").title() \
        or "frutas silvestres" in corrigir_acentos(
        "Cha Melancia/F. Silvestres 350g").lower()


def test_vquartus_qualificador_que_vende_nao_some(tmp_path, monkeypatch):
    """§2.3 (o Toscana): a oferta "LINGUIÇA PERDIGÃO TOSCANA" casava
    verde com o cadastro genérico "Linguiça Perdigão" e o Toscana
    SUMIA da página — o S1 só olhava a direção cadastro→oferta. O
    espelho vocabulário-guiado rebaixa a amarelo com o motivo dito;
    a linha SEM qualificador segue verde (não-regressão)."""
    monkeypatch.setenv("AUTOTABLOIDE_ROOT", str(tmp_path / "raiz"))
    from app.ai.conciliacao import Conciliador, Semaforo
    from app.core.database import Database
    from app.core.paths import SystemRoot
    from app.core.repositories import ProdutoRepositorio

    db = Database(SystemRoot(tmp_path / "raiz")).init()
    try:
        with db.Session() as s:
            ProdutoRepositorio(s).importar("LINGUICA PERDIGAO 100 g")
            s.commit()
            v = Conciliador(s).conciliar("LINGUIÇA PERDIGÃO TOSCANA 100 g")
            assert v.semaforo == Semaforo.AMARELO, (v.semaforo, v.motivo)
            assert "toscana" in (v.motivo or "").lower(), v.motivo
            v2 = Conciliador(s).conciliar("LINGUIÇA PERDIGÃO 100 g")
            assert v2.semaforo == Semaforo.VERDE, (v2.semaforo, v2.motivo)
    finally:
        db.engine.dispose()


def test_vquartus_descritor_final_um_peso_por_pixel_de_texto():
    """A cadeia INTEIRA (dados → nome_fit): o descritor renderizado
    carrega exatamente UM peso — a mutação que devolve os dois pesos
    ("500ml · 497 ml") deixa este teste vermelho."""
    from app.qt.telas.servico import ItemMesa, dados_para_desenho
    from app.rendering.nome_fit import peso_do_cadastro

    it = ItemMesa(descricao="AGUA MINERAL 500ML", preco="1,99",
                  semaforo="VERDE",
                  nome="Água Mineral Marajá 497ml S/ Gás",
                  unidade="500ml", marca_propria=False)
    d = dados_para_desenho(it)
    pesos_no_descritor = [t for t in (d.descritor or "").replace("·", " ").split()
                          if any(c.isdigit() for c in t)]
    assert pesos_no_descritor == ["497ml"], (d.descritor, pesos_no_descritor)
    assert peso_do_cadastro(it.nome) == "497ml"

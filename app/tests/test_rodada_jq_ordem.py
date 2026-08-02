"""ORDEM F13-QUINTUSDECIMUS — a auditoria AO VIVO do Jornal (01/08).

O arquiteto dirigiu o app na máquina do dono COM A IA LIGADA e provou:
a alegação da rodada anterior era verdadeira com a IA desligada e falsa
com ela ligada. A lei nova (o espelho da trava da F9):

    A IA SOMA, NUNCA SUBSTITUI — todo sinal determinístico continua
    valendo quando a IA está ligada; ela acrescenta, nunca apaga o que
    a régua achou. E toda alegação sobre a IA diz EM QUAL ESTADO foi
    verificada — a bancada roda os DOIS.

Testes L1 da ordem (J1..J27) — vermelhos no código de hoje, cada um no
estado da IA em que o defeito foi visto.
"""

import pytest

from app.ai.fake import MotorIAFake


def _fake_sem_componentes(trecho: str, nome: str) -> MotorIAFake:
    """O cenário REAL da máquina do dono: a IA responde, mas devolve
    ZERO componentes para a linha de duas marcas."""
    import json
    return MotorIAFake(respostas_chat={trecho: json.dumps({
        "nome_sanitizado": nome, "categoria": "Mercearia",
        "mais18": False, "componentes": [], "variantes": []})})


# ==================================================================== J1
# A IA SOMA: o detector determinístico vale COM a IA ligada
# ======================================================================


def test_j1_composto_com_ia_ligada_e_sem_componentes_da_ia():
    """O achado-mãe: com o LM ligado devolvendo zero componentes, o
    `dividir_em_dois` pronto era descartado — a pergunta nunca aparecia
    na máquina do dono. A régua agora SOMA à IA (como o mais18 já
    fazia três linhas acima)."""
    from app.qt.telas.servico import enriquecer_descricao

    fake = _fake_sem_componentes("ARROZ", "Arroz Somar e Tio Bonini 5kg")
    p = enriquecer_descricao("ARROZ SOMAR e TIO BONINI 5 Kgs", motor=fake)
    assert p.possivel_composto is True
    assert p.sugestao_componentes == ["Arroz Somar 5kg",
                                      "Arroz Tio Bonini 5kg"]
    # a sugestão é da RÉGUA, não da IA: o check nasce desmarcado
    assert p.componentes_da_ia is False


def test_j1_com_ia_que_deu_componentes_nada_muda():
    """Quando a IA ACERTA (devolve os componentes), o comportamento de
    sempre fica: pré-marcado, componentes da IA."""
    import json

    from app.qt.telas.servico import enriquecer_descricao
    fake = MotorIAFake(respostas_chat={"CORACAO": json.dumps({
        "nome_sanitizado": "Coração e Língua", "categoria": "Açougue",
        "mais18": False, "variantes": [],
        "componentes": [{"nome_sanitizado": "Coração"},
                        {"nome_sanitizado": "Língua"}]})})
    p = enriquecer_descricao("CORACAO e LINGUA BOVINA", motor=fake)
    assert p.possivel_composto is True
    assert p.componentes_da_ia is True
    assert p.componentes == ["Coração", "Língua"]


# ==================================================================== J9
# Linha com pendência "multiplos" NUNCA sai verde calada
# ======================================================================


def test_j9_multiplos_casado_verde_desce_a_amarelo(tmp_path, monkeypatch):
    """O Arroz Somar e Tio Bonini casou VERDE com "Arroz Tio Bonini" —
    duas marcas viraram uma em silêncio, sem porta. Linha que parece 2
    produtos no MÍNIMO pede conferência."""
    monkeypatch.setenv("AUTOTABLOIDE_ROOT", str(tmp_path / "raiz"))
    from app.core.database import Database
    from app.core.paths import SystemRoot
    from app.core.repositories import ProdutoRepositorio
    from app.qt.telas.servico import conciliar_linhas

    db = Database(SystemRoot(tmp_path / "raiz")).init()
    try:
        with db.Session() as s:
            ProdutoRepositorio(s).importar("ARROZ TIO BONINI 5 kg")
            s.commit()
    finally:
        db.engine.dispose()

    res = conciliar_linhas(
        [("ARROZ SOMAR e TIO BONINI 5 Kgs", "18,81", None)],
        lambda *_: None)
    (item,) = res.itens
    assert item.semaforo == "AMARELO", (item.semaforo, item.via)
    assert "produto" in (item.candidato_nome or "") or item.produto_id
    assert "multiplos" in item.pendencias


# =================================================================== J10
# Peso/volume divergente REBAIXA o verde (nunca casa calado)
# ======================================================================


def test_j10_volume_divergente_rebaixa_verde(tmp_path, monkeypatch):
    """O Kitubaina 1,6L casou verde com o cadastro de 1,3L — produtos
    diferentes. O peso escolhe ENTRE candidatos (ADENDO 30/07); faltava
    ele REJEITAR o verde quando diverge."""
    monkeypatch.setenv("AUTOTABLOIDE_ROOT", str(tmp_path / "raiz"))
    from app.core.database import Database
    from app.core.paths import SystemRoot
    from app.core.repositories import ProdutoRepositorio
    from app.ai.conciliacao import Conciliador, Semaforo

    db = Database(SystemRoot(tmp_path / "raiz")).init()
    try:
        with db.Session() as s:
            ProdutoRepositorio(s).importar("REFRIGERANTE KITUBAINA 1,3 L")
            s.commit()
            v = Conciliador(s).conciliar("REFRIGERANTE KITUBAINA 1,6 LT")
            assert v.semaforo == Semaforo.AMARELO, (v.semaforo, v.motivo)
            assert "volume" in v.motivo.lower() \
                or "peso" in v.motivo.lower(), v.motivo
            # o peso IGUAL continua verde (não-regressão)
            v2 = Conciliador(s).conciliar("REFRIGERANTE KITUBAINA 1,3 LT")
            assert v2.semaforo == Semaforo.VERDE, (v2.semaforo, v2.motivo)
    finally:
        db.engine.dispose()


# =================================================================== J11
# Piso de plausibilidade nos candidatos exibidos
# ======================================================================


def test_j11_candidatos_exibidos_tem_piso(tmp_path, monkeypatch):
    """Ração de gato como candidato para molho de tomate é pior que
    lista vazia. Score < 70 não viaja ao ItemMesa.candidatos."""
    monkeypatch.setenv("AUTOTABLOIDE_ROOT", str(tmp_path / "raiz"))
    from app.core.database import Database
    from app.core.paths import SystemRoot
    from app.core.repositories import ProdutoRepositorio
    from app.qt.telas.servico import conciliar_linhas

    db = Database(SystemRoot(tmp_path / "raiz")).init()
    try:
        with db.Session() as s:
            repo = ProdutoRepositorio(s)
            repo.importar("RACAO GATO KIT E KAT CARNE AO MOLHO 70 g")
            repo.importar("BALA GELATINA FINI TUBES TROPICAL 80 g")
            repo.importar("DOCE DE LEITE FRIMESA ORIGINAL 400 g")
            s.commit()
    finally:
        db.engine.dispose()

    res = conciliar_linhas(
        [("MOLHO TOMATE FUJINI e CAJAMAR 300 g", "1,50", None)],
        lambda *_: None)
    (item,) = res.itens
    ruins = [c for c in (item.candidatos or []) if c["score"] < 70]
    assert ruins == [], f"candidatos abaixo do piso viajaram: {ruins}"


# =================================================================== J18
# "de X por Y" é preço de PRIMEIRA CLASSE; ilegível nunca sai verde
# ======================================================================


def test_j18_de_x_por_y_e_parseado():
    """O padrão mais comum do varejo: Y é o preço, X é o riscado (o
    app já sabe desenhar de/por — é o cartaz)."""
    from app.qt.telas.servico import classificar_preco_ocr

    assert classificar_preco_ocr("de 18,81 por 6,90") \
        == ("6,90", None, "18,81")
    assert classificar_preco_ocr("De R$ 8,49 por R$ 6,90") \
        == ("6,90", None, "8,49")
    # os formatos de sempre seguem intactos (agora com o 3º campo)
    assert classificar_preco_ocr("5,99") == ("5,99", None, None)
    assert classificar_preco_ocr("S. OFERTA") == (None, "SUPER OFERTA", None)
    assert classificar_preco_ocr("20% de desconto") \
        == (None, "20% de desconto", None)
    # a guarda P0.3b fica: "2x 5,00" segue ambíguo (não é de/por)
    assert classificar_preco_ocr("2x 5,00")[0] == "2x 5,00"


def test_j18_o_de_da_tabela_flui_ao_item(tmp_path, monkeypatch):
    monkeypatch.setenv("AUTOTABLOIDE_ROOT", str(tmp_path / "raiz"))
    from app.qt.telas.servico import conciliar_linhas

    res = conciliar_linhas(
        [("ARROZ SOMAR 5 kg", "6,90", None)], lambda *_: None,
        precos_de=["18,81"])
    (item,) = res.itens
    assert item.preco == "6,90"
    assert item.preco_de == "18,81"


def test_j18_preco_ilegivel_nunca_sai_verde_calado(tmp_path, monkeypatch):
    """Na máquina do dono, "18,81 6,90" virou preço `—` numa linha
    VERDE — e o encarte iria ao cliente sem preço nos dois destaques.
    A recusa do P0.3b agora é CAPTURADA: pendência + amarelo + motivo."""
    monkeypatch.setenv("AUTOTABLOIDE_ROOT", str(tmp_path / "raiz"))
    from app.core.database import Database
    from app.core.paths import SystemRoot
    from app.core.repositories import ProdutoRepositorio
    from app.qt.telas.servico import conciliar_linhas

    db = Database(SystemRoot(tmp_path / "raiz")).init()
    try:
        with db.Session() as s:
            ProdutoRepositorio(s).importar("OLEO DE SOJA CONCORDIA 900 ml")
            s.commit()
    finally:
        db.engine.dispose()

    res = conciliar_linhas(
        [("OLEO DE SOJA CONCORDIA 900 ml", "18,81 6,90", None)],
        lambda *_: None)
    (item,) = res.itens
    assert item.semaforo == "AMARELO", (item.semaforo, item.via)
    assert "preco_ilegivel" in item.pendencias
    assert "preço" in (item.motivo or "").lower(), item.motivo


# =================================================================== J13
# A 3ª pergunta: 2 produtos × SABORES × um produto só
# ======================================================================


def test_j13_familia_da_linha_detecta_sabores():
    """O que vem DEPOIS da medida é sabor; o que vem antes é marca —
    a Sardinha dá 3 sabores, o Arroz de 2 marcas dá zero."""
    from app.qt.telas.servico import familia_da_linha

    base, sabores = familia_da_linha(
        "SARDINHA COQUEIRO 125 g TOMATE / OLEO e LIMÃO")
    assert base == "Sardinha Coqueiro 125g"
    assert sabores == ["Tomate", "Óleo", "Limão"]
    base2, sabores2 = familia_da_linha(
        "AMACIANTE MON BIJOU 5 LTS PROTEÇÃO e CLASSICO")
    assert sabores2 == ["Proteção", "Classico"]
    # duas MARCAS antes do peso: NÃO é família (é a pergunta "2 produtos")
    _, sabores3 = familia_da_linha("ARROZ SOMAR e TIO BONINI 5 Kgs")
    assert sabores3 == []


def test_j13_curadoria_tem_a_terceira_pergunta():
    from PySide6.QtWidgets import QApplication
    QApplication.instance() or QApplication([])
    from app.qt.telas.curadoria_dialog import CuradoriaDialog

    dlg = CuradoriaDialog(
        "Sardinha Coqueiro 125g", [],
        sabores=["Tomate", "Óleo", "Limão"],
        nome_familia_sugerido="Sardinha Coqueiro 125g",
        contexto="SARDINHA COQUEIRO 125 g TOMATE / OLEO e LIMÃO",
        posicao=(12, 42))
    try:
        assert dlg.rb_sabores.isVisible() is not None   # existe
        assert dlg.sabores_finais() is None             # nada decidido
        dlg.rb_sabores.setChecked(True)
        nome, marcados = dlg.sabores_finais()
        assert nome == "Sardinha Coqueiro 125g"
        assert marcados == ["Tomate", "Óleo", "Limão"]
        dlg.chks_sabores[1].setChecked(False)           # desmarca o Óleo
        assert dlg.sabores_finais()[1] == ["Tomate", "Limão"]
        # "é um produto só" cancela tudo
        dlg.rb_um.setChecked(True)
        assert dlg.sabores_finais() is None
        assert dlg.componentes_finais() == []
        assert "12 de 42" in dlg._contexto.text()
    finally:
        dlg.deleteLater()


def test_j13_criar_familia_de_sabores(tmp_path, monkeypatch):
    monkeypatch.setenv("AUTOTABLOIDE_ROOT", str(tmp_path / "raiz"))
    from app.qt.telas import servico

    item = servico.ItemMesa(
        descricao="SARDINHA COQUEIRO 125 g TOMATE / OLEO e LIMÃO",
        preco="6,90", semaforo="VERMELHO", nome="x")
    servico.criar_familia_de_sabores(
        item, "Sardinha Coqueiro 125g",
        ["Tomate", "Óleo", "Limão"], False, None)
    assert item.semaforo == "VERDE"
    assert item.familia and len(item.familia["membros"]) == 3
    nomes = {m["nome"] for m in item.familia["membros"]}
    assert "Sardinha Coqueiro 125g Tomate" in nomes


# ============================================================ J16 + J24
# ======================================================================


def test_j16_typos_da_tabela_real():
    from app.core.ortografia import corrigir_acentos

    assert corrigir_acentos("MILHO PICOCA YOKI 400 g") \
        == "MILHO PIPOCA YOKI 400 g"
    assert corrigir_acentos("OLE O de SOJA CONCORCIA 900 ml") \
        == "ÓLEO de SOJA CONCORCIA 900 ml"


def test_j24_validade_de_pagina_sem_slot_ocupado():
    """A manchete é DERIVADA: o período vivo entra mesmo com a página
    vazia — o dado "__pagina__" leva a validade ao compositor."""
    from app.qt.telas.servico import dados_de_pagina
    from app.rendering.compositor import _campo_vivo_da_pagina

    dados = {"__pagina__": dados_de_pagina(
        "OFERTA VÁLIDA DE 03/08 ATÉ 27/08")}
    assert _campo_vivo_da_pagina(dados, "texto_legal") \
        == "OFERTA VÁLIDA DE 03/08 ATÉ 27/08"


# =================================================================== J25
# ======================================================================


def test_j25_o_fio_do_jornal_nao_veste_a_celula():
    """O ADORNO-FILETE (o Fio de 6 px) é separador — o plano roda; o
    ADORNO de verdade (a cesta) continua barrando."""
    from app.rendering.foto_fit import plano_da_celula
    from app.rendering.model import Regiao, Retangulo, TipoRegiao

    def _celula(com_adorno_grande: bool):
        regs = [
            Regiao(TipoRegiao.IMAGEM, Retangulo(2, 2, 47, 30),
                   zona_flex=True),
            Regiao(TipoRegiao.ADORNO, Retangulo(0, 0, 49, 1.5),
                   nome="Fio"),
            Regiao(TipoRegiao.NOME, Retangulo(2, 34, 45, 8)),
        ]
        if com_adorno_grande:
            regs.append(Regiao(TipoRegiao.ADORNO,
                               Retangulo(0, 10, 30, 20), nome="Cesta"))
        return regs

    # foto LARGA (o defeito afundada) → há plano; o fio NÃO barra
    assert plano_da_celula(_celula(False), 200, 100) is not None
    # a cesta (adorno de verdade) barra como sempre
    assert plano_da_celula(_celula(True), 200, 100) is None

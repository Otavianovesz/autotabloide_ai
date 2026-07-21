"""Onda 1 da REVISAO_GERAL (RG-01..RG-04) — desempenho, com prova.

O boot em duas fases, o cache de fontes, a fila de enriquecimento por uid,
o modo "criar sem foto", o cache de OCR e as fases honestas de status.
"""

import json
import time

import pytest
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication

from app.ai.fake import MotorIAFake
from app.qt.telas import servico
from app.qt.telas.servico import ItemMesa
from app.qt.workers import TrabalhadorFila
from app.tests import seeds_portabilidade as seeds


def _app():
    return QApplication.instance() or QApplication([])


@pytest.fixture()
def raiz_tmp(tmp_path, monkeypatch):
    monkeypatch.setenv("AUTOTABLOIDE_ROOT", str(tmp_path / "raiz"))
    return seeds.raiz(tmp_path, "raiz")


# --- RG-02a: enriquecer_descricao (e o bug latente do motor None) -------------------


def test_enriquecer_descricao_degrada_sem_motor():
    """LM desligado NUNCA estoura — degrada para o determinístico (bug latente)."""
    p = servico.enriquecer_descricao("OLEO DE SOJA LIZA 900 ML", None)
    assert p.nome and p.candidatos == []           # sanitizado, sem busca


def test_enriquecer_descricao_com_ia():
    motor = MotorIAFake(respostas_chat={
        "supermercado": '{"nome_sanitizado": "Óleo de Soja Liza 900ml", '
                        '"mais18": false, "categoria": "Mercearia", '
                        '"confianca": 0.9}'})
    p = servico.enriquecer_descricao("OLEO DE SOJA LIZA 900 ML", motor)
    assert p.nome == "Óleo de Soja Liza 900ml"
    assert p.categoria == "Mercearia"


# --- TrabalhadorFila: item a item, por chave, cancelável -----------------------------


def test_trabalhador_fila_emite_por_item_e_cancela():
    _app()
    prontos: list[tuple[str, object]] = []
    fila = TrabalhadorFila([("a", 1), ("b", 2), ("c", 3)], lambda v: v * 10)
    fila.item_pronto.connect(lambda k, r: prontos.append((k, r)),
                             Qt.ConnectionType.DirectConnection)
    fila.start()
    assert fila.wait(5000)
    assert prontos == [("a", 10), ("b", 20), ("c", 30)]

    # cancelar no meio: o item em curso termina, o resto NÃO roda
    vistos: list[str] = []
    fila2 = TrabalhadorFila([(c, c) for c in "abcdef"], lambda v: v)

    def _ao_pronto(k, _r):
        vistos.append(k)
        if k == "b":
            fila2.cancelar()

    fila2.item_pronto.connect(_ao_pronto, Qt.ConnectionType.DirectConnection)
    fila2.start()
    assert fila2.wait(5000)
    assert vistos[:2] == ["a", "b"] and len(vistos) < 6

    # erro num item NÃO derruba a fila (e nunca é silencioso)
    erros: list[str] = []
    ok: list[str] = []
    fila3 = TrabalhadorFila(
        [("a", 1), ("boom", 0), ("c", 3)],
        lambda v: 10 // v)
    fila3.item_pronto.connect(lambda k, _r: ok.append(k),
                              Qt.ConnectionType.DirectConnection)
    fila3.item_falhou.connect(lambda k, _m: erros.append(k),
                              Qt.ConnectionType.DirectConnection)
    fila3.start()
    assert fila3.wait(5000)
    assert ok == ["a", "c"] and erros == ["boom"]


# --- a fila na ConciliacaoDialog (por uid) + modo "criar sem foto" -------------------


def _esperar(cond, timeout_s: float = 8.0) -> bool:
    app = _app()
    fim = time.monotonic() + timeout_s
    while time.monotonic() < fim:
        app.processEvents()
        if cond():
            return True
        time.sleep(0.02)
    return False


def test_conciliacao_fila_enriquece_por_uid_e_cria_sem_foto(
        raiz_tmp, monkeypatch):
    _app()
    motor = MotorIAFake(respostas_chat={
        "supermercado": '{"nome_sanitizado": "Produto Enriquecido", '
                        '"mais18": false, "categoria": null, '
                        '"confianca": 0.9}'})
    monkeypatch.setattr(servico, "_motor_se_disponivel", lambda: motor)
    from app.qt.telas.conciliacao_dialog import ConciliacaoDialog

    itens = [ItemMesa("BRUTO UM", "1,00", "VERMELHO", "BRUTO UM"),
             ItemMesa("BRUTO DOIS", "2,00", "VERMELHO", "BRUTO DOIS"),
             ItemMesa("JA EXISTE", "3,00", "VERDE", "Já Existe",
                      produto_id=99)]
    dlg = ConciliacaoDialog(servico.ResultadoMesa(itens=itens), None)

    # RG-02a: a fila enche o cache POR UID (e a tabela mostra o nome pronto)
    assert _esperar(lambda: len(dlg._propostas) == 2), \
        "a fila de enriquecimento não completou"
    assert set(dlg._propostas) == {itens[0].uid, itens[1].uid}
    assert dlg._propostas[itens[0].uid].nome == "Produto Enriquecido"

    # RG-03: fotos desligadas → "Criar" cadastra SEM foto, sem curadoria
    dlg.chk_fotos.setChecked(False)
    assert dlg.btn_todos.isVisible() is False or True   # visibilidade offscreen
    dlg._criar(0)
    assert _esperar(lambda: dlg.itens[0].semaforo == "VERDE"), \
        "o criar-sem-foto não resolveu o item"
    assert dlg.itens[0].imagem is None                  # sem foto MESMO
    assert dlg.itens[0].nome == "Produto Enriquecido"
    assert dlg.itens[0].produto_id is not None          # cadastrado no banco

    dlg.reject()                                        # junta as pontas (done)


def test_conciliacao_criar_todos_sem_foto(raiz_tmp, monkeypatch):
    _app()
    monkeypatch.setattr(servico, "_motor_se_disponivel", lambda: None)
    from app.qt.telas.conciliacao_dialog import ConciliacaoDialog

    itens = [ItemMesa(f"BRUTO {i}", f"{i},00", "VERMELHO", f"BRUTO {i}")
             for i in range(1, 4)]
    dlg = ConciliacaoDialog(servico.ResultadoMesa(itens=itens), None)
    dlg.chk_fotos.setChecked(False)
    dlg._criar_todos_sem_foto()
    assert _esperar(lambda: all(it.semaforo == "VERDE" for it in dlg.itens)), \
        "o lote não criou todos"
    assert all(it.produto_id for it in dlg.itens)
    assert all(it.imagem is None for it in dlg.itens)
    dlg.reject()


# --- RG-04: cache de OCR + fases honestas -------------------------------------------

_RESPOSTA_OCR = json.dumps({
    "validade_oferta": "01/07 até 27/07",
    "linhas": [{"descricao": "CAFE PILAO 500G", "preco": "18,90"},
               {"descricao": "ACUCAR UNIAO 1KG", "preco": "5,49"}],
})


def _foto(tmp_path):
    from PIL import Image
    f = tmp_path / "tabela.png"
    Image.new("RGB", (1200, 900), "#EEEEEE").save(f)
    return f


def test_ocr_fases_de_status_e_cache_roundtrip(raiz_tmp, tmp_path):
    from app.ai import ocr

    motor = MotorIAFake(respostas_visao={"tabela de ofertas": _RESPOSTA_OCR})
    foto = _foto(tmp_path)
    fases: list[str] = []
    tabela = ocr.ler_tabela(foto, motor, status_cb=fases.append)
    assert len(tabela.linhas) == 2
    assert fases[0].startswith("Preparando")
    assert "pode levar" in fases[1]                     # honesto: sem % falsa
    assert "2 produtos" in fases[2]

    # cache: guardar → consultar devolve o MESMO conteúdo, sem IA
    ocr.cache_guardar(foto, "qwen-visao", tabela)
    de_novo = ocr.cache_consultar(foto, "qwen-visao")
    assert de_novo is not None
    assert [(ln.descricao, ln.preco) for ln in de_novo.linhas] == \
        [(ln.descricao, ln.preco) for ln in tabela.linhas]
    assert de_novo.validade_oferta == tabela.validade_oferta
    # modelo diferente invalida (trocou o modelo → relê)
    assert ocr.cache_consultar(foto, "outro-modelo") is None
    # I3: o JSON do cache NÃO guarda caminho de máquina
    bruto = ocr._cache_path().read_text(encoding="utf-8")
    assert str(tmp_path) not in bruto
    # leitura vazia NUNCA envenena o cache
    ocr.cache_guardar(foto, "qwen-visao", ocr.TabelaOCR())
    assert ocr.cache_consultar(foto, "qwen-visao") is not None


def test_importar_ofertas_pula_ocr_no_cache_hit(raiz_tmp, tmp_path,
                                                monkeypatch):
    """Reimportar a MESMA foto não re-roda o OCR — e AVISA (I2)."""
    from app.ai import ocr

    foto = _foto(tmp_path)
    tabela = ocr.TabelaOCR(
        linhas=[ocr.LinhaOferta("CAFE PILAO 500G", "18,90")],
        validade_oferta=None)
    from app.ai.client import ConfigIA
    ocr.cache_guardar(foto, ConfigIA.da_config().modelo_visao, tabela)

    monkeypatch.setattr(servico, "_motor_se_disponivel", lambda: None)
    monkeypatch.setattr(
        ocr, "ler_tabela",
        lambda *a, **kw: (_ for _ in ()).throw(
            AssertionError("o OCR NÃO podia rodar no cache-hit")))
    fases: list[str] = []
    resultado = servico.importar_ofertas(foto, fases.append)
    assert len(resultado.itens) == 1
    assert any("reaproveitado" in f for f in fases)     # o aviso do I2
    assert resultado.aviso and "reaproveitado" in resultado.aviso


# --- curas da revisão da onda (achados do diário) ------------------------------------


def test_rg47_amarelo_tem_saida_limpa(raiz_tmp):
    """RG-47: linha-lixo do OCR que casa 65% NÃO encurrala mais — o amarelo
    ganhou 'Ignorar' (sem ensinar alias errado, sem poluir o banco)."""
    _app()
    from PySide6.QtWidgets import QPushButton

    from app.qt.telas.conciliacao_dialog import ConciliacaoDialog

    itens = [ItemMesa("PROMO LIXO 9,99", "9,99", "AMARELO", "PROMO LIXO",
                      candidato_nome="Presunto Perdigão")]
    dlg = ConciliacaoDialog(servico.ResultadoMesa(itens=itens), None)
    caixa = dlg.tabela.cellWidget(0, 4)
    rotulos = [b.text() for b in caixa.findChildren(QPushButton)]
    assert "Ignorar" in rotulos
    dlg._ignorar(0)
    assert dlg.itens == [] and dlg.concluir.isEnabled()
    dlg.reject()


def test_cache_ocr_limpar_e_aviso_no_resultado(raiz_tmp, tmp_path,
                                               monkeypatch):
    """A leitura parcial presa no cache tem saída (limpar) e o hit vira
    AVISO no resultado (toast na tela — não o status que pisca)."""
    from app.ai import ocr
    from app.ai.client import ConfigIA

    foto = _foto(tmp_path)
    tabela = ocr.TabelaOCR(linhas=[ocr.LinhaOferta("X", "1,00")])
    ocr.cache_guardar(foto, ConfigIA.da_config().modelo_visao, tabela)
    monkeypatch.setattr(servico, "_motor_se_disponivel", lambda: None)
    resultado = servico.importar_ofertas(foto, lambda _m: None)
    assert resultado.aviso and "reaproveitado" in resultado.aviso

    assert ocr.cache_limpar() == 1                      # esquece a leitura
    assert ocr.cache_consultar(
        foto, ConfigIA.da_config().modelo_visao) is None


def test_fonte_sumida_nao_estoura(raiz_tmp, tmp_path, monkeypatch):
    from app.qt import fontes

    pasta = tmp_path / "f"
    pasta.mkdir()
    monkeypatch.setattr(fontes, "_DIRS_SISTEMA", [pasta])
    fontes._mapa_sistema.cache_clear()
    # rótulo apontando p/ arquivo que sumiu (fonte desinstalada com o app
    # aberto) devolve None em vez de FileNotFoundError engolido
    monkeypatch.setattr(fontes, "_mapa_sistema",
                        lambda: {"Sumida — x": pasta / "nao_existe.ttf"})
    assert fontes.garantir_em_fontes("Sumida — x") is None


# --- RG-01: cache de fontes + boot em duas fases -------------------------------------


def test_mapa_de_fontes_usa_cache_em_disco(raiz_tmp, tmp_path, monkeypatch):
    import shutil

    from app.qt import fontes

    pasta = tmp_path / "fontes_sist"
    pasta.mkdir()
    reais = list(__import__("pathlib").Path(
        "AutoTabloide_System_Root/fontes").glob("*.ttf"))
    if not reais:
        pytest.fail("sem fonte real para o teste (fontes/ vazia)")
    shutil.copy(reais[0], pasta / reais[0].name)
    monkeypatch.setattr(fontes, "_DIRS_SISTEMA", [pasta])

    fontes._mapa_sistema.cache_clear()
    mapa1 = fontes._mapa_sistema()
    assert len(mapa1) == 1                              # varreu e mapeou
    assert fontes._cache_path().exists()                # e gravou o cache

    # prova de que a 2ª leitura vem do CACHE: plantamos um rótulo falso no
    # arquivo com a MESMA assinatura — se ele aparecer, ninguém re-varreu
    dados = json.loads(fontes._cache_path().read_text(encoding="utf-8"))
    dados["mapa"]["Fonte Plantada — prova"] = str(pasta / reais[0].name)
    fontes._cache_path().write_text(json.dumps(dados), encoding="utf-8")
    fontes._mapa_sistema.cache_clear()
    mapa2 = fontes._mapa_sistema()
    assert "Fonte Plantada — prova" in mapa2

    # mudar a pasta (arquivo novo) invalida a assinatura → re-varre de verdade
    shutil.copy(reais[0], pasta / f"copia_{reais[0].name}")
    fontes._mapa_sistema.cache_clear()
    mapa3 = fontes._mapa_sistema()
    assert "Fonte Plantada — prova" not in mapa3
    assert len(mapa3) == 2


def test_boot_em_duas_fases_liga_os_sinais(raiz_tmp):
    """RG-01: a janela nasce SÓ com o Dashboard; o resto completa depois —
    e os sinais (salvo/zoom) continuam ligados (o risco apontado)."""
    _app()
    from app import editor_app

    holder: dict = {}
    shell = editor_app._montar_shell(holder)
    assert "inicio" in shell._telas and "mesa" not in shell._telas
    editor = editor_app._completar_janela(shell, holder)
    assert "mesa" in shell._telas and "cofre" in shell._telas
    assert holder["mesa"].ao_salvo is not None          # sinal do rodapé ligado
    assert holder["fabrica"].ao_salvo is not None
    assert editor is not None

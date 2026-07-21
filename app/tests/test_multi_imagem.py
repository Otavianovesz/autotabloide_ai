"""F7.1 (Etapa C do Bloco E) — multi-imagem: unidades e fluxo da Mesa.

O adversarial por pixel (ordem, leque, congelamento) está em
test_adversarial_vinculo.py::test_adversarial_multi_imagem_por_conteudo.
"""

from PIL import Image
from PySide6.QtWidgets import QApplication

from app.ai.enriquecimento import sugerir_variantes
from app.ai.fake import MotorIAFake
from app.qt.telas.servico import ItemMesa
from app.rendering.arranjo import ModoArranjo
from app.tests.test_adversarial_vinculo import _grade_4, _itens


def _app():
    QApplication.instance() or QApplication([])


# --- IA sugere TERMOS; humano escolhe fotos (anti-alucinação) ----------------------


def test_sugerir_variantes_devolve_termos_dedup():
    motor = MotorIAFake(respostas_chat={
        "Suco Trink": '{"variantes": ["Uva", "uva", "Morango", "Abacaxi", '
                      '"Laranja", "Limão", "Caju", "Manga"]}'})
    termos = sugerir_variantes("Suco Trink 1L", motor)
    assert termos[:3] == ["Uva", "Morango", "Abacaxi"]   # dedup case-insensitive
    assert len(termos) == 6                              # teto de 6


def test_sugerir_variantes_degrada_sem_travar():
    assert sugerir_variantes("X", None) == []
    assert sugerir_variantes("X", MotorIAFake(disponivel=False)) == []
    lixo = MotorIAFake(respostas_chat={"X": "isto não é json"})
    assert sugerir_variantes("X", lixo) == []
    sem_chave = MotorIAFake(respostas_chat={"X": '{"outra": 1}'})
    assert sugerir_variantes("X", sem_chave) == []


# --- ItemMesa: serialização e compatibilidade com projeto velho --------------------


def test_item_mesa_serializa_imagens_e_arranjo():
    it = ItemMesa("A", "1,00", "VERDE", "Produto A",
                  imagens=["/a.png", "/b.png"], arranjo="GRADE")
    d = it.to_dict()
    volta = ItemMesa.from_dict(d)
    assert volta.imagens == ["/a.png", "/b.png"] and volta.arranjo == "GRADE"

    # projeto VELHO (sem as chaves novas) abre com os defaults — sem migração
    velho = {"descricao": "A", "preco": "1,00", "semaforo": "VERDE",
             "nome": "Produto A", "uid": "abc"}
    it2 = ItemMesa.from_dict(velho)
    assert it2.imagens == [] and it2.arranjo is None


# --- Mesa: _dados_de mapeia para o motor F4.5 ---------------------------------------


def test_mesa_dados_de_com_multi_imagem(tmp_path):
    _app()
    from app.qt.telas.mesa import MesaTela

    mesa = MesaTela()
    mesa.carregar_layout(_grade_4(), None)
    it = ItemMesa("A", "1,00", "VERDE", "Produto A", imagem="/solo.png",
                  imagens=["/a.png", "/b.png", "/c.png"], arranjo="LADO_A_LADO")
    d = mesa._dados_de(it)
    assert [im.caminho for im in d.imagens] == ["/a.png", "/b.png", "/c.png"]
    assert d.modo_arranjo is ModoArranjo.LADO_A_LADO

    # arranjo estranho de projeto velho → leque padrão, sem quebrar
    it.arranjo = "ESPIRAL"
    assert mesa._dados_de(it).modo_arranjo is ModoArranjo.LEQUE

    # sem imagens → o caminho single de sempre
    it.imagens, it.arranjo = [], None
    d2 = mesa._dados_de(it)
    assert d2.imagens == [] and d2.imagem_path == "/solo.png"


# --- o diálogo (headless, IA canned) -------------------------------------------------


def _dialogo(tmp_path, monkeypatch, imagens=(), arranjo=None):
    from app.qt.telas.fotos_item_dialog import FotosItemDialog

    fotos = []
    for i, cor in enumerate(["#111111", "#222222"]):
        f = tmp_path / f"f{i}.png"
        Image.new("RGB", (32, 32), cor).save(f)
        fotos.append(str(f))
    it = ItemMesa("A", "1,00", "VERDE", "Suco Trink 1L",
                  imagem=fotos[0], imagens=list(imagens) or [],
                  arranjo=arranjo)
    # sugestor injetado: o teste NUNCA toca IA/banco reais, e o worker
    # termina na hora (o done() do diálogo junta as pontas)
    dlg = FotosItemDialog(it, sugestor=lambda: ["Uva", "Coco"])
    return dlg, fotos, it


def test_dialogo_fotos_ordem_remocao_e_arranjo(tmp_path, monkeypatch):
    _app()
    dlg, fotos, _it = _dialogo(tmp_path, monkeypatch)
    # abriu com a foto única do item como 1ª da lista
    assert dlg.caminhos() == [fotos[0]]

    dlg._adicionar_na_lista(fotos[1])
    assert dlg.caminhos() == [fotos[0], fotos[1]]

    # reordenar: a 2ª vai para ANTES (a ordem é a do desenho)
    dlg.lista.setCurrentRow(1)
    dlg._mover(-1)
    assert dlg.caminhos() == [fotos[1], fotos[0]]

    # remover a 1ª
    dlg.lista.setCurrentRow(0)
    dlg._remover()
    assert dlg.caminhos() == [fotos[0]]

    # arranjo por item (C2)
    dlg.arranjo.setCurrentIndex(1)
    assert dlg.arranjo_escolhido() == "LADO_A_LADO"
    dlg.reject()          # fecha juntando as pontas dos workers (done())


def test_dialogo_chips_preenchem_o_termo_mas_nao_escolhem_foto(tmp_path,
                                                               monkeypatch):
    """Anti-alucinação: o chip só PREENCHE o termo — nenhuma foto entra."""
    _app()
    dlg, _fotos, _it = _dialogo(tmp_path, monkeypatch)
    antes = dlg.caminhos()
    dlg._mostrar_chips(["Uva", "Coco"])
    # os chips existem e clicá-los muda o TERMO, não a lista de fotos
    from PySide6.QtWidgets import QPushButton
    chips = [dlg._chips_caixa.itemAt(i).widget()
             for i in range(dlg._chips_caixa.count())
             if isinstance(dlg._chips_caixa.itemAt(i).widget(), QPushButton)]
    assert [c.text() for c in chips] == ["Uva", "Coco"]
    chips[0].click()
    assert dlg.termo.text() == "Suco Trink 1L Uva"
    assert dlg.caminhos() == antes                 # nenhuma foto apareceu
    dlg.reject()          # fecha juntando as pontas dos workers (done())

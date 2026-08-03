"""ESTÚDIO NO CAMINHO DO DONO (03/08/2026) — a queixa: "quando eu colo
uma foto ruim, ele só vai direto e passa o removedor de fundo (que
inclusive está bem ruim cortando boa parte dos produtos)".

Três consertos, na régua da casa: a LUZ do Estúdio roda no caminho da
curadoria; o recorte que come o produto AVISA (I2, régua nomeada); o
packshot completo (e o degrau 2, quando houver) fica a um clique na
grade de candidatos."""

import pytest
from PIL import Image

from app.core.paths import SystemRoot


@pytest.fixture
def raiz(tmp_path, monkeypatch):
    monkeypatch.setenv("AUTOTABLOIDE_ROOT", str(tmp_path / "raiz"))
    from app.core.database import Database
    r = SystemRoot(tmp_path / "raiz")
    Database(r).init().engine.dispose()
    return r


def _quadrado(lado=200, cor=(200, 30, 30, 255)):
    return Image.new("RGBA", (lado, lado), cor)


def test_recorte_suspeito_e_a_regua_nomeada():
    """Recorte são → None; quase apagado → avisa; esburacado → avisa."""
    from app.images.fundo import recorte_suspeito

    original = _quadrado(200)
    # são: o produto sólido ocupando boa parte
    sao = Image.new("RGBA", (200, 200), (0, 0, 0, 0))
    sao.paste(_quadrado(150), (25, 25))
    assert recorte_suspeito(original, sao) is None
    # quase apagado: sobrou um pinguinho (<8% da original)
    pingo = Image.new("RGBA", (200, 200), (0, 0, 0, 0))
    pingo.paste(_quadrado(30), (85, 85))
    assert "quase apagou" in (recorte_suspeito(original, pingo) or "")
    # esburacado: só dois cantos opostos — o miolo foi comido
    buraco = Image.new("RGBA", (200, 200), (0, 0, 0, 0))
    buraco.paste(_quadrado(45), (0, 0))
    buraco.paste(_quadrado(45), (155, 155))
    assert "comido" in (recorte_suspeito(original, buraco) or "")


def test_luz_de_vitrine_no_pipeline(raiz, tmp_path):
    """A foto escura/apagada sai com o contraste esticado — o
    aprimoramento do Estúdio no caminho comum (fundo branco pula o
    modelo: o teste roda sem o 1 GB)."""
    from app.images.fundo import processar_imagem

    fonte = tmp_path / "escura.png"
    img = Image.new("RGB", (300, 300), (255, 255, 255))
    for x in range(80, 220):
        for y in range(80, 220):
            img.putpixel((x, y), (100 + (x % 40), 90, 90))
    img.save(fonte)

    sem = processar_imagem(fonte, tmp_path / "sem.png")
    com = processar_imagem(fonte, tmp_path / "com.png",
                           luz_de_vitrine=True)
    ext_sem = Image.open(sem).convert("L").getextrema()
    ext_com = Image.open(com).convert("L").getextrema()
    assert (ext_com[1] - ext_com[0]) >= (ext_sem[1] - ext_sem[0]), \
        "a luz de vitrine tinha de esticar o contraste"


def test_tratar_imagem_avisa_quando_o_recorte_come(raiz, tmp_path,
                                                   monkeypatch):
    """O caminho REAL da curadoria: o modelo (fake) come o produto e o
    aviso chega pelo aviso_cb — nunca mais o corte calado."""
    import app.images.fundo as fundo_mod
    from app.qt.telas import servico

    fonte = tmp_path / "produto.png"
    Image.new("RGB", (300, 300), (40, 120, 40)).save(fonte)   # não-branco

    def _modelo_que_come(imagem, modelo="x"):
        r = Image.new("RGBA", (300, 300), (0, 0, 0, 0))
        r.paste(Image.new("RGBA", (20, 20), (40, 120, 40, 255)), (10, 10))
        return r

    monkeypatch.setattr(fundo_mod, "remover_fundo", _modelo_que_come)
    avisos: list[str] = []
    tratada = servico.tratar_imagem(str(fonte), lambda _m: None,
                                    aviso_cb=avisos.append)
    assert tratada and avisos, "o corte comeu e ninguém avisou (I2)"
    assert "Refinar" in avisos[0], "o aviso tem de apontar o remédio"


def test_aprimorar_no_estudio_degrada_com_aviso(raiz, tmp_path,
                                                monkeypatch):
    """O serviço do botão: degrau 1 sempre entrega; com o gerador
    LIGADO mas sem GPU/modelo, degrada COM o aviso honesto (F10)."""
    import app.images.estudio as est_mod
    from app.qt.telas import servico

    fonte = tmp_path / "foto.png"
    _quadrado(120).convert("RGB").save(fonte)
    monkeypatch.setattr(
        est_mod, "packshot_degrau1",
        lambda img, **k: img.convert("RGBA"))
    monkeypatch.setattr(servico, "estudio_gerador_ligado", lambda: True)
    monkeypatch.setattr(est_mod, "gerador_disponivel", lambda: None)

    caminho, aviso = servico.aprimorar_no_estudio(str(fonte),
                                                  lambda _m: None)
    from pathlib import Path
    assert Path(caminho).is_file(), "o degrau 1 tinha de entregar"
    assert aviso and "GPU" in aviso, (
        f"a degradação do degrau 2 tinha de falar da GPU: {aviso!r}")


def test_estudio_na_grade_da_curadoria(raiz, tmp_path, monkeypatch):
    """O gesto: candidato selecionado → Estúdio → a MINIATURA passa a
    apontar o packshot (troca in-place, o padrão do Ajustar)."""
    from PySide6.QtCore import Qt
    from PySide6.QtWidgets import QApplication
    QApplication.instance() or QApplication([])
    from app.qt.telas import servico
    from app.qt.telas.curadoria_dialog import CuradoriaDialog
    from app.tests import acervo
    from app.tests.gestos import drenar

    cand = tmp_path / "cand.png"
    acervo.foto_de_bancada(cand, (30, 60, 220))
    pack = tmp_path / "pack.png"
    acervo.foto_de_bancada(pack, (220, 200, 30))

    monkeypatch.setattr(servico, "garantir_modelo_recorte",
                        lambda w: True)
    monkeypatch.setattr(servico, "aprimorar_no_estudio",
                        lambda c, st: (str(pack), None))

    dlg = CuradoriaDialog("Produto X", [str(cand)])
    dlg.setAttribute(Qt.WidgetAttribute.WA_DontShowOnScreen, True)
    dlg.show()
    drenar()
    try:
        assert not dlg.btn_estudio.isEnabled()
        dlg.lista.setCurrentRow(0)
        assert dlg.btn_estudio.isEnabled()
        dlg._estudio_candidato()
        import time
        fim = time.monotonic() + 15
        troca = lambda: dlg.lista.item(0).data(
            Qt.ItemDataRole.UserRole) == str(pack)
        while time.monotonic() < fim and not troca():
            drenar(30)
            time.sleep(0.05)
        assert troca(), "o candidato não virou o packshot"
    finally:
        dlg.done(0)

"""LUPA — ampliar imagens para conferir a GRAMATURA (pedido do dono,
02/08/2026): "eu preciso ver se a gramatura está certa e não consigo
aumentar o tamanho dela pra ver na UI". Um componente só, ligado na
grade de candidatos da curadoria (o principal), nas telas de fotos e
no painel do Almoxarifado."""

import pytest


@pytest.fixture
def app_qt():
    from PySide6.QtWidgets import QApplication
    return QApplication.instance() or QApplication([])


def _foto(tmp_path, nome="rotulo.png", cor=(120, 40, 200), lado=600):
    from app.tests import acervo
    f = tmp_path / nome
    acervo.foto_de_bancada(f, cor, lado=lado)
    return str(f)


def test_lupa_zoom_e_alternancia(app_qt, tmp_path):
    """O visor: abre AJUSTADO, o zoom aplica no transform, o duplo
    clique alterna ajustar↔100% (o gesto de ler a gramatura) e o
    rodapé diz o tamanho real e o zoom."""
    from PySide6.QtCore import Qt
    from app.qt.design.lupa import Lupa

    dlg = Lupa(_foto(tmp_path, lado=2000))   # maior que a janela
    dlg.setAttribute(Qt.WidgetAttribute.WA_DontShowOnScreen, True)
    dlg.show()
    try:
        dlg.aplicar_zoom(1.0)
        assert abs(dlg._tela.transform().m11() - 1.0) < 0.001
        assert "2000×2000" in dlg._rodape.text()
        assert "100%" in dlg._rodape.text()
        dlg.aplicar_zoom(4.0)
        assert abs(dlg._tela.transform().m11() - 4.0) < 0.001
        assert "400%" in dlg._rodape.text()
        dlg.alternar()                    # estava longe de 100% → vai a 100%
        assert abs(dlg.zoom - 1.0) < 0.001
        dlg.alternar()                    # em 100% → ajusta à janela
        assert dlg.zoom != 1.0
        # os limites seguram o exagero
        dlg.aplicar_zoom(99.0)
        assert dlg.zoom <= 8.0
    finally:
        dlg.done(0)


def test_lupa_sem_imagem_avisa_e_nao_abre(app_qt, tmp_path, monkeypatch):
    """I2: caminho vazio/sumido não abre janela em branco — avisa."""
    from PySide6.QtWidgets import QWidget
    import app.qt.design.lupa as lupa_mod

    abriu = {"n": 0}
    monkeypatch.setattr(lupa_mod.Lupa, "exec",
                        lambda self: abriu.__setitem__("n", abriu["n"] + 1))
    avisos = []
    import app.qt.design.toast as toast_mod
    monkeypatch.setattr(toast_mod, "mostrar_toast",
                        lambda w, m, tipo="info": avisos.append(m))
    w = QWidget()
    lupa_mod.ampliar_imagem(w, None)
    lupa_mod.ampliar_imagem(w, str(tmp_path / "nao_existe.png"))
    assert abriu["n"] == 0
    assert len(avisos) == 2
    # com imagem real, abre
    lupa_mod.ampliar_imagem(w, _foto(tmp_path))
    assert abriu["n"] == 1
    w.deleteLater()


def test_lupa_na_grade_da_curadoria(app_qt, tmp_path, monkeypatch):
    """O principal do pedido: na grade de candidatos BAIXADOS, o botão
    " Ampliar" habilita com a seleção e abre a lupa do candidato."""
    from PySide6.QtCore import Qt
    from app.qt.telas.curadoria_dialog import CuradoriaDialog
    import app.qt.design.lupa as lupa_mod

    caminho = _foto(tmp_path, "candidato.png")
    vistos = []
    monkeypatch.setattr(lupa_mod, "Lupa",
                        lambda cam, parent=None, titulo=None:
                        (vistos.append(cam),
                         type("F", (), {"exec": lambda s: 1})())[1])
    dlg = CuradoriaDialog("Bis Lacta Xtra 45g", [caminho])
    dlg.setAttribute(Qt.WidgetAttribute.WA_DontShowOnScreen, True)
    dlg.show()
    try:
        assert not dlg.btn_lupa.isEnabled()
        dlg.lista.setCurrentRow(0)
        assert dlg.btn_lupa.isEnabled(), (
            "selecionar o candidato tinha de habilitar o Ampliar")
        dlg._ampliar()
        assert vistos == [caminho], "a lupa não abriu o candidato"
    finally:
        dlg.done(0)


def test_lupa_na_tela_por_sabor(app_qt, tmp_path, monkeypatch):
    """O espaço preenchido amplia pela mesma porta única."""
    from app.qt.telas.fotos_por_sabor_dialog import FotosPorSaborDialog
    import app.qt.telas.fotos_por_sabor_dialog as fps_mod

    caminho = _foto(tmp_path)
    vistos = []
    monkeypatch.setattr(
        "app.qt.design.lupa.ampliar_imagem",
        lambda parent, cam, titulo=None: vistos.append((cam, titulo)))
    dlg = FotosPorSaborDialog("Bis", ["Branco", "Oreo"],
                              pre=[caminho, None])
    try:
        dlg._ampliar(0)
        assert vistos == [(caminho, "Branco")]
    finally:
        dlg.done(0)

"""Testes da F4.4 — ingestão (arquivo/bytes/URL), troca e histórico de versões."""

import io

from PIL import Image

from app.images.biblioteca import BibliotecaImagens


def _bytes_img(cor: str) -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", (60, 60), cor).save(buf, "PNG")
    return buf.getvalue()


def test_ingerir_arquivo(tmp_path):
    f = tmp_path / "n.png"
    Image.new("RGB", (60, 60), "red").save(f)
    bib = BibliotecaImagens(tmp_path / "lib")
    p = bib.ingerir(7, f)
    assert p == bib.caminho_atual(7) and p.exists()
    assert bib.caminho_relativo(7) == "7/atual.png"


def test_ingerir_bytes(tmp_path):
    bib = BibliotecaImagens(tmp_path / "lib")
    assert bib.ingerir(7, _bytes_img("blue")).exists()


def test_ingerir_url_com_baixador_fake(tmp_path):
    dados = _bytes_img("green")
    bib = BibliotecaImagens(tmp_path / "lib", baixar_url=lambda u: dados)
    assert bib.ingerir(7, "https://exemplo.com/x.png").exists()


def test_troca_arquiva_a_anterior(tmp_path):
    bib = BibliotecaImagens(tmp_path / "lib")
    bib.ingerir(7, _bytes_img("red"))
    assert bib.listar_versoes(7) == []
    bib.ingerir(7, _bytes_img("blue"))
    assert len(bib.listar_versoes(7)) == 1  # a vermelha foi para o histórico


def test_limite_de_versoes(tmp_path):
    bib = BibliotecaImagens(tmp_path / "lib", max_versoes=2)
    for cor in ["red", "blue", "green", "yellow"]:
        bib.ingerir(7, _bytes_img(cor))
    assert len(bib.listar_versoes(7)) == 2  # só as 2 mais recentes


def test_processador_e_aplicado(tmp_path):
    chamado = {}

    def proc(img):
        chamado["ok"] = True
        return img

    bib = BibliotecaImagens(tmp_path / "lib", processador=proc)
    bib.ingerir(7, _bytes_img("red"))
    assert chamado.get("ok")

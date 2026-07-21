"""Testes da F4.3 — a LÓGICA condicional do upscale (com Lanczos, sem o modelo real)."""

from PIL import Image

from app.images.upscale import (
    UpscalerLanczos,
    ampliar_sob_demanda,
    melhorar_para_biblioteca,
    precisa_upscale,
)


def test_precisa_upscale():
    assert precisa_upscale(150, 200)          # foto ruim
    assert not precisa_upscale(1200, 1500)    # foto boa (Bing)


def test_biblioteca_amplia_so_a_pequena(tmp_path):
    peq = tmp_path / "peq.png"
    Image.new("RGB", (150, 150), "red").save(peq)
    r = melhorar_para_biblioteca(peq, UpscalerLanczos(4), tmp_path / "o1.png", min_util=1000)
    assert r.ampliada
    assert 150 < min(r.para) <= 1000          # ampliou, sem estourar o necessário


def test_biblioteca_mantem_a_boa(tmp_path):
    boa = tmp_path / "boa.png"
    Image.new("RGB", (1200, 1200), "blue").save(boa)
    r = melhorar_para_biblioteca(boa, UpscalerLanczos(4), tmp_path / "o2.png", min_util=1000)
    assert not r.ampliada and r.para == (1200, 1200)


def test_sob_demanda_nao_mexe_se_ja_grande(tmp_path):
    g = tmp_path / "g.png"
    Image.new("RGB", (2000, 2000), "green").save(g)
    out = ampliar_sob_demanda(g, UpscalerLanczos(4), alvo_px=1500)
    assert out.size == (2000, 2000)


def test_sob_demanda_amplia_ate_o_alvo(tmp_path):
    p = tmp_path / "p.png"
    Image.new("RGB", (300, 300), "purple").save(p)
    out = ampliar_sob_demanda(p, UpscalerLanczos(4), alvo_px=1000)
    assert max(out.size) <= 1000 and max(out.size) > 300

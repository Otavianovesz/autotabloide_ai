"""Testes da lógica de alinhamento (F5.4) — puros, sem Qt."""

from app.qt.alinhamento import alinhar, distribuir, snap


def test_snap_cola_na_borda():
    nx, ny, guias = snap((97, 50, 20, 10), [100], [], limiar=6)
    assert nx == 100 and ("x", 100) in guias


def test_snap_fora_do_limiar_nao_cola():
    # rect 80..90 (bordas 80/85/90), alvo 100 -> distância 10 > 6, não cola
    nx, ny, guias = snap((80, 50, 10, 10), [100], [], limiar=6)
    assert nx == 80 and guias == []


def test_alinhar_esquerda():
    rects = [(10, 0, 20, 10), (50, 5, 30, 10), (30, 20, 10, 10)]
    pos = alinhar(rects, "esq")
    assert all(nx == 10 for nx, _ in pos)


def test_alinhar_centro_horizontal():
    rects = [(0, 0, 20, 10), (0, 0, 40, 10)]  # bbox x 0..40 -> centro 20
    pos = alinhar(rects, "centro_h")
    assert pos[0][0] == 10 and pos[1][0] == 0   # centros vão para 20


def test_distribuir_horizontal():
    rects = [(0, 0, 10, 10), (15, 0, 10, 10), (100, 0, 10, 10)]
    pos = distribuir(rects, "h")
    centros = [nx + 5 for nx, _ in pos]
    assert abs(centros[1] - 55) < 0.01   # centro do meio fica equidistante (5, 55, 105)

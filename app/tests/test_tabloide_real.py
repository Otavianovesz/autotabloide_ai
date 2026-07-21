"""Testes do pipeline de integração (F3+F4+F5.5) com fakes — degradação e cache."""

from PIL import Image

import app.scripts.tabloide_real as T
from app.ai.fake import MotorIAFake


class _BaixadorVazio:
    def baixar(self, query, n, destino):
        return []


def test_preparar_degrada_sem_imagem(tmp_path):
    p = T.preparar("BOMBRIL 45 g", "2,66", MotorIAFake(disponivel=False),
                   _BaixadorVazio(), tmp_path / "cache", tmp_path / "stg")
    assert p.nome == "Bombril 45g"          # nome sanitizado (IA off)
    assert p.imagem_path is None            # sem foto, não quebrou
    assert str(p.preco_por) == "2.66"


def test_preparar_usa_cache_sem_baixar(tmp_path):
    cache = tmp_path / "cache"
    cache.mkdir()
    slug = T._slug("Bombril 45g")
    Image.new("RGBA", (50, 50), (255, 0, 0, 255)).save(cache / f"{slug}.png")

    chamado = {"n": 0}

    class Baixador:
        def baixar(self, query, n, destino):
            chamado["n"] += 1
            return []

    p = T.preparar("BOMBRIL 45 g", "2,66", MotorIAFake(disponivel=False),
                   Baixador(), cache, tmp_path / "stg")
    assert p.imagem_path == str(cache / f"{slug}.png")
    assert chamado["n"] == 0                 # cache -> não baixou

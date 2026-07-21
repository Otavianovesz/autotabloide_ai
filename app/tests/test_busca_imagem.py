"""Testes da busca de imagem (F4.1) — pós-processamento, com baixador fake (sem rede)."""

from pathlib import Path

from PIL import Image

from app.images.busca import buscar_imagens, montar_query, remover_peso


class _BaixadorFake:
    """Gera imagens locais: 2 boas distintas, 1 duplicata, 1 pequena demais."""

    def baixar(self, query: str, n: int, destino: Path) -> list[Path]:
        destino.mkdir(parents=True, exist_ok=True)
        Image.new("RGB", (600, 600), "red").save(destino / "a.png")
        Image.new("RGB", (600, 600), "red").save(destino / "a_dup.png")   # duplicata
        Image.new("RGB", (600, 600), "blue").save(destino / "b.png")
        Image.new("RGB", (100, 100), "green").save(destino / "c_small.png")  # pequena
        return sorted(p for p in destino.iterdir() if p.is_file())


class _BaixadorEspiao:
    """Registra a query que recebeu (para checar a remoção de peso)."""

    def __init__(self):
        self.query = None

    def baixar(self, query, n, destino):
        self.query = query
        return []


class _BaixadorVazio:
    def baixar(self, query, n, destino):
        return []


def test_montar_query():
    assert montar_query("Nutella 350g Ferrero", ("produto",)) == "Nutella 350g Ferrero produto"


def test_remover_peso():
    assert remover_peso("Óleo de Soja Liza 900ml") == "Óleo de Soja Liza"
    assert remover_peso("Desodorante Above One Men 150ml") == "Desodorante Above One Men"
    assert remover_peso("Café Instantâneo Nescafé 200g") == "Café Instantâneo Nescafé"
    assert remover_peso("Refrigerante Coca-Cola 2L") == "Refrigerante Coca-Cola"
    assert remover_peso("Cerveja Amstel 12x350ml") == "Cerveja Amstel"
    assert remover_peso("Arroz Camil 1kg") == "Arroz Camil"
    # sem peso: não mexe
    assert remover_peso("Sabão em Pó Omo") == "Sabão em Pó Omo"


def test_busca_remove_peso_da_query(tmp_path):
    espiao = _BaixadorEspiao()
    buscar_imagens("Óleo de Soja Liza 900ml", espiao, tmp_path)
    assert espiao.query == "Óleo de Soja Liza"


def test_dedup_e_filtro_de_resolucao(tmp_path):
    r = buscar_imagens("Nutella 350g Ferrero", _BaixadorFake(), tmp_path, min_lado=400)
    # 4 arquivos -> remove 1 duplicata e 1 pequena -> 2 candidatos
    assert len(r.candidatos) == 2
    assert all(c.largura >= 400 and c.altura >= 400 for c in r.candidatos)
    assert len({c.hash_md5 for c in r.candidatos}) == 2
    assert not r.bloqueado


def test_bloqueio_degrada_sem_quebrar(tmp_path):
    r = buscar_imagens("Qualquer Produto", _BaixadorVazio(), tmp_path)
    assert r.candidatos == []
    assert r.bloqueado is True

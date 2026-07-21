"""
Open Food Facts — packshot por código de barras (RG-41)
=======================================================
A descoberta da pesquisa (PESQUISA_TABLOIDE §5): base ABERTA, API sem chave,
consultável por EAN — packshot oficial com fundo já limpo, e a comunidade
brasileira é ativa. É o 1º degrau da cascata de imagem (depois vem o ddgs).

Contrato honesto (I2): qualquer falha — sem rede, EAN não encontrado, JSON
estranho, download quebrado — devolve ``None`` e o CHAMADOR segue a cascata
avisando; este módulo nunca estoura nem bloqueia (timeout curto).
"""

from __future__ import annotations

import json
import re
from pathlib import Path

_API = "https://world.openfoodfacts.org/api/v2/product/{ean}.json?fields=image_front_url,product_name"
_UA = {"User-Agent": "AutoTabloideAI/1.0 (app desktop offline; contato local)"}


def ean_valido(texto: str | None) -> str | None:
    """Normaliza um EAN/GTIN: só dígitos, 8–14 deles — senão None."""
    if not texto:
        return None
    digitos = re.sub(r"\D", "", str(texto))
    return digitos if 8 <= len(digitos) <= 14 else None


def buscar_imagem_off(ean: str, destino_dir: Path | str,
                      timeout: float = 8.0) -> str | None:
    """Baixa o packshot do Open Food Facts para ``destino_dir``.

    Devolve o caminho do arquivo, ou None (produto sem foto/sem rede/EAN
    inválido) — quem chama segue a cascata.
    """
    from urllib.request import Request, urlopen

    ean = ean_valido(ean)
    if ean is None:
        return None
    try:
        req = Request(_API.format(ean=ean), headers=_UA)
        with urlopen(req, timeout=timeout) as resp:
            dados = json.loads(resp.read().decode("utf-8"))
        url = (dados.get("product") or {}).get("image_front_url")
        if not url:
            return None
        destino = Path(destino_dir)
        destino.mkdir(parents=True, exist_ok=True)
        arquivo = destino / f"off_{ean}.jpg"
        req_img = Request(url, headers=_UA)
        with urlopen(req_img, timeout=timeout) as resp:
            arquivo.write_bytes(resp.read())
        return str(arquivo) if arquivo.stat().st_size > 0 else None
    except Exception:
        return None                      # sem rede/404/JSON ruim → cascata segue

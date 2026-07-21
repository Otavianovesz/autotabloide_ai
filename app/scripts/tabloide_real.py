"""
Tabloide REAL (teste de integração F3+F4+F5.5)
==============================================
Primeira integração ponta a ponta: para cada item da fixture do Belo Brasil,
(1) **enriquece o nome** (Qwen), (2) **busca a imagem** com o nome JÁ enriquecido
(DuckDuckGo, sem peso → 1º candidato → remoção de fundo → recorte), (3) compõe na grade.

Ordem importa: buscar imagem com "De Sodorante" traz lixo; com "Desodorante..."
traz o produto certo. Cacheia a imagem tratada em disco (não rebaixa toda hora).

Degrada com elegância: sem LM Studio → nome só sanitizado; sem imagem → slot sem
foto (não quebra). O auto-pick da 1ª imagem é provisório (curadoria = Mesa/Bloco D).

Uso::

    python -m app.scripts.tabloide_real [saida.png]
"""

from __future__ import annotations

import re
import sys
import tempfile
from decimal import Decimal
from pathlib import Path

from app.ai.client import ClienteOpenAICompat
from app.ai.enriquecimento import enriquecer
from app.core.paths import SystemRoot
from app.images.busca import BaixadorWeb, buscar_imagens
from app.images.fundo import processar_imagem
from app.rendering.compositor import DadosProduto, compor_pagina
from app.rendering.export import exportar_png
from app.rendering.grade import layout_grade_de_arte
from app.scripts.importar_tabela import parse_tabela

ARTE = "Frente Template.png"
FIXTURE = Path("app/tests/fixtures/ofertas_belo_brasil.txt")


def _slug(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", s.lower()).strip("_")[:60] or "item"


def _preco(txt: str | None):
    if not txt:
        return None
    return Decimal(txt.replace("R$", "").replace(" ", "").replace(",", "."))


def preparar(desc, preco, motor, baixador, cache_dir: Path, staging: Path) -> DadosProduto:
    """Um item: enriquece o nome, busca+trata a imagem (cache), devolve DadosProduto."""
    enr = enriquecer(desc, motor)                    # (1) nome primeiro
    nome = enr.nome_sanitizado
    cache = cache_dir / f"{_slug(nome)}.png"
    imagem = None
    if cache.exists():
        imagem = cache
    else:
        try:                                         # (2) imagem com o nome bom
            r = buscar_imagens(nome, baixador, staging / _slug(nome), n=5, min_lado=300)
            if r.candidatos:
                processar_imagem(r.candidatos[0].caminho, cache)  # fundo + recorte
                imagem = cache
        except Exception as exc:
            print(f"      (imagem falhou: {type(exc).__name__})")
    return DadosProduto(
        nome=nome, preco_por=_preco(preco),
        imagem_path=str(imagem) if imagem else None,
        mais18=enr.mais18, marca_propria=False,
    )


def main(saida: str) -> None:
    motor = ClienteOpenAICompat()
    print("LM Studio:", "OK (nomes enriquecidos)" if motor.disponivel() else "OFF (nomes só sanitizados)")
    baixador = BaixadorWeb(min_lado_hint=300)
    cache_dir = SystemRoot().biblioteca_imagens / "_auto"
    cache_dir.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.gettempdir()) / "atb_staging"

    layout, caixas = layout_grade_de_arte(ARTE)
    n = len(layout.paginas[0].slots)
    itens = parse_tabela(FIXTURE)[:n]

    produtos = []
    for i, (desc, preco) in enumerate(itens, 1):
        p = preparar(desc, preco, motor, baixador, cache_dir, staging)
        print(f"[{i:>2}/{n}] {p.nome[:46]:<46} {'foto' if p.imagem_path else 'SEM foto'}")
        produtos.append(p)

    img = compor_pagina(layout, layout.paginas[0], produtos, fundo_path=ARTE)
    Path(saida).parent.mkdir(parents=True, exist_ok=True)
    exportar_png(img, saida, layout.dpi)
    print(f"\nTabloide REAL salvo em {saida}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "saida_tabloide_real/frente.png")

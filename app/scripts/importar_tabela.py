"""
Importar uma tabela de ofertas para o banco
===========================================
Lê um arquivo ``descricao | preco`` (uma oferta por linha) e cadastra os
produtos, sanitizando cada nome. Reaproveita produtos já existentes (dedup
por nome cru ou alias).

Uso::

    python -m app.scripts.importar_tabela app/tests/fixtures/ofertas_belo_brasil.txt
"""

from __future__ import annotations

import sys
from pathlib import Path

from app.core.database import Database
from app.core.paths import SystemRoot
from app.core.repositories import ProdutoRepositorio, regras_de_config


def parse_tabela_ean(caminho: Path) -> list[tuple[str, str | None, str | None]]:
    """RG-41: lê ``descricao | preco | ean`` (as duas últimas opcionais).

    O EAN também é reconhecido COLADO no início da descrição (fornecedor
    manda "7891234567890 ARROZ ...") — vira o campo e sai do nome.
    """
    from app.images.off import ean_valido

    itens: list[tuple[str, str | None, str | None]] = []
    for linha in caminho.read_text(encoding="utf-8").splitlines():
        linha = linha.strip()
        if not linha or linha.startswith("#"):
            continue
        nome, _, resto = linha.partition("|")
        preco, _, coluna_ean = resto.partition("|")
        nome = nome.strip()
        ean = ean_valido(coluna_ean.strip()) if coluna_ean.strip() else None
        if ean is None:                  # código no início da descrição?
            cabeca, _, cauda = nome.partition(" ")
            if cauda and cabeca.isdigit() and ean_valido(cabeca):
                ean = cabeca
                nome = cauda.strip()
        itens.append((nome, preco.strip() or None, ean))
    return itens


def parse_tabela(caminho: Path) -> list[tuple[str, str | None]]:
    """Lê linhas ``descricao | preco`` (compat — o EAN fica no parse_tabela_ean)."""
    return [(nome, preco) for nome, preco, _ean in parse_tabela_ean(caminho)]


def importar_arquivo(caminho: Path, root: SystemRoot | None = None) -> dict:
    """Importa o arquivo e devolve um resumo (total no banco, criados, pendentes IA)."""
    db = Database(root).init()
    criados = 0
    pendentes_ia = 0
    with db.Session() as session:
        repo = ProdutoRepositorio(session)
        regras = regras_de_config(session)
        for nome, preco, ean in parse_tabela_ean(caminho):
            res = repo.importar(nome, preco=preco, regras=regras)
            if ean and not res.produto.ean:      # RG-41: o EAN da tabela entra
                repo.editar(res.produto.id, ean=ean)
            criados += int(res.criado)
            pendentes_ia += int(res.sanitizacao.precisa_ia)
        session.commit()
        total = repo.contar()
    return {"total_no_banco": total, "criados_agora": criados, "pendentes_ia": pendentes_ia}


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("uso: python -m app.scripts.importar_tabela <arquivo>")
        raise SystemExit(2)
    print(importar_arquivo(Path(sys.argv[1])))

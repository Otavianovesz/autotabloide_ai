"""
Migração do AutoTabloide ANTIGO (FASE 12, Bloco E — passos 70-71)
=================================================================
O protótipo antigo (o `src/` que ficou de canteiro) guardava o acervo num
SQLite com a tabela `produtos` (nome_sanitizado, marca_normalizada,
preco_venda_atual, categoria) + `produto_aliases`. Esta migração lê aquele
banco DIRETO por sqlite3 (sem depender do código velho), casa por CHAVE
NATURAL (I1 — nome+marca; o repetido NUNCA duplica) e segue o rito da casa:
PRÉVIA → confirmação → importa. Nada é apagado do banco antigo (só leitura).
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

from app.core.portabilidade import chave_natural


def _ler_banco_antigo(caminho_db: str | Path) -> list[dict]:
    """Os produtos do protótipo, planos. Levanta ValueError se o arquivo não
    tem a tabela esperada (mensagem em PT-BR, sem stack trace)."""
    caminho_db = Path(caminho_db)
    if not caminho_db.is_file():
        raise ValueError("O arquivo do banco antigo não foi encontrado.")
    try:
        con = sqlite3.connect(f"file:{caminho_db}?mode=ro", uri=True)
    except sqlite3.Error as exc:
        raise ValueError(f"Não consegui abrir o banco antigo: {exc}")
    try:
        con.row_factory = sqlite3.Row
        try:
            rows = con.execute(
                "SELECT id, nome_sanitizado, marca_normalizada, "
                "detalhe_peso, categoria, preco_venda_atual "
                "FROM produtos").fetchall()
        except sqlite3.Error:
            raise ValueError("Este arquivo não parece ser o banco do "
                             "AutoTabloide antigo (tabela `produtos` com as "
                             "colunas esperadas não existe).")
        aliases: dict[int, list[str]] = {}
        try:
            for r in con.execute(
                    "SELECT produto_id, alias_raw FROM produto_aliases"):
                aliases.setdefault(r["produto_id"], []).append(r["alias_raw"])
        except sqlite3.Error:
            pass                          # protótipo sem aliases: segue
        saida = []
        for r in rows:
            nome = (r["nome_sanitizado"] or "").strip()
            if not nome:
                continue
            saida.append({
                "nome": nome,
                "marca": (r["marca_normalizada"] or "").strip() or None,
                "peso": (r["detalhe_peso"] or "").strip() or None,
                "categoria": (r["categoria"] or "").strip() or None,
                "preco": r["preco_venda_atual"],
                "aliases": aliases.get(r["id"], []),
            })
        return saida
    finally:
        con.close()


def analisar_banco_antigo(caminho_db: str | Path) -> dict:
    """A PRÉVIA (o rito da casa): quantos produtos o antigo tem, quantos são
    NOVOS aqui e quantos já existem (por chave natural — não duplicam)."""
    from sqlalchemy import select

    from app.core.database import Database
    from app.core.models import Produto
    antigos = _ler_banco_antigo(caminho_db)
    db = Database().init()
    try:
        with db.Session() as s:
            atuais = {chave_natural(p.nome_sanitizado or "", p.marca or "")
                      for p in s.execute(select(Produto)).scalars()}
    finally:
        db.engine.dispose()
    novos = [a for a in antigos
             if chave_natural(a["nome"], a["marca"] or "") not in atuais]
    return {"total_antigo": len(antigos), "novos": len(novos),
            "existentes": len(antigos) - len(novos),
            "produtos_novos": novos}


def migrar_banco_antigo(caminho_db: str | Path,
                        status_cb=lambda _m: None) -> dict:
    """Importa os NOVOS (chave natural; o repetido é pulado e CONTADO — I2)
    com marca, peso, categoria, preço e aliases. O banco antigo não é
    tocado. Devolve {"importados", "pulados", "aliases"}."""
    from decimal import Decimal, InvalidOperation

    from app.core.modo import exigir_escrita
    exigir_escrita()                     # R-131 vale para a migração também
    previa = analisar_banco_antigo(caminho_db)
    from app.core.database import Database
    from app.core.repositories import ProdutoRepositorio
    importados = aliases_n = 0
    db = Database().init()
    try:
        with db.Session() as s:
            repo = ProdutoRepositorio(s)
            for i, a in enumerate(previa["produtos_novos"], 1):
                status_cb(f"Migrando {i}/{previa['novos']}: {a['nome']}…")
                try:
                    preco = (Decimal(str(a["preco"]))
                             if a["preco"] is not None else None)
                except (InvalidOperation, ValueError):
                    preco = None
                res = repo.importar(a["nome"].upper(), preco=preco,
                                    categoria=a["categoria"])
                repo.editar(res.produto.id, nome_sanitizado=a["nome"],
                            marca=a["marca"])
                for al in a["aliases"]:
                    if (al or "").strip():
                        repo._garantir_alias(res.produto.id, al.strip())
                        aliases_n += 1
                importados += 1
            s.commit()
    finally:
        db.engine.dispose()
    return {"importados": importados, "pulados": previa["existentes"],
            "aliases": aliases_n}

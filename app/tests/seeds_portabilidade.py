"""Sementes compartilhadas dos testes de portabilidade (D-B1/D-B3).

Cada produto ganha uma FOTO DE COR ÚNICA — a conferência do roundtrip é
sempre por bytes, por chave natural (nunca por id): se uma mesclagem trocar
fotos entre produtos, a cor entrega na hora.
"""

from __future__ import annotations

import io
import json
import uuid as _uuid
from decimal import Decimal

from PIL import Image
from sqlalchemy import select

from app.core.database import Database
from app.core.models import Categoria, Layout, Produto, ProdutoAlias, ProjetoSalvo
from app.core.paths import SystemRoot


def png(cor: str) -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", (24, 24), cor).save(buf, "PNG")
    return buf.getvalue()


def raiz(tmp_path, nome: str) -> SystemRoot:
    root = SystemRoot(tmp_path / nome).criar_estrutura()
    Database(root).init().engine.dispose()
    return root


def add_produto(root: SystemRoot, nome: str, marca: str | None = None,
                preco: str | None = None, foto: bytes | None = None,
                categoria: str | None = None, aliases: tuple[str, ...] = (),
                mais18: bool = False) -> int:
    db = Database(root).init()
    try:
        with db.Session() as s:
            cat_id = None
            if categoria:
                cat = s.execute(select(Categoria).where(
                    Categoria.nome == categoria)).scalar_one_or_none()
                if cat is None:
                    cat = Categoria(nome=categoria)
                    s.add(cat)
                    s.flush()
                cat_id = cat.id
            p = Produto(
                nome_bruto=nome.upper(), nome_sanitizado=nome, marca=marca,
                preco_atual=Decimal(preco) if preco else None,
                categoria_id=cat_id, selo_mais18=mais18,
                bebida_alcoolica=mais18)
            s.add(p)
            s.flush()
            if foto is not None:
                pasta = root.biblioteca_imagens / str(p.id)
                pasta.mkdir(parents=True, exist_ok=True)
                (pasta / "atual.png").write_bytes(foto)
                p.caminho_imagem = f"{p.id}/atual.png"
            for a in aliases:
                s.add(ProdutoAlias(alias_raw=a, produto_id=p.id))
            s.commit()
            return p.id
    finally:
        db.engine.dispose()


def add_layout_com_arte(root: SystemRoot, nome: str, arte_path) -> int:
    from app.rendering.model import layout_de_arte

    ldef = layout_de_arte(str(arte_path))
    ldef.paginas[0].arquivo_fundo = str(arte_path)   # exercita o fundo por página
    db = Database(root).init()
    try:
        with db.Session() as s:
            row = Layout(nome=nome, arquivo_fundo=str(arte_path),
                         tipo_midia="TABLOIDE",
                         estrutura_json=json.dumps(ldef.to_dict(),
                                                   ensure_ascii=False))
            s.add(row)
            s.commit()
            return row.id
    finally:
        db.engine.dispose()


def add_projeto(root: SystemRoot, nome: str, layout_id: int) -> str:
    uuid_str = str(_uuid.uuid4())
    db = Database(root).init()
    try:
        with db.Session() as s:
            s.add(ProjetoSalvo(
                nome=nome, uuid=uuid_str, layout_id=layout_id,
                evento="Avulsos",
                estado_slots=json.dumps({"tipo": "TABLOIDE"})))
            s.commit()
    finally:
        db.engine.dispose()
    pasta = root.projetos / uuid_str / "imagens"
    pasta.mkdir(parents=True, exist_ok=True)
    (pasta / "00.png").write_bytes(png("#123456"))
    return uuid_str


def _achar(root: SystemRoot, nome: str, marca: str | None):
    from app.core.portabilidade import chave_natural

    db = Database(root).init()
    try:
        with db.Session() as s:
            for p in s.execute(select(Produto)).scalars():
                if chave_natural(p.nome_sanitizado, p.marca) == \
                        chave_natural(nome, marca):
                    return {
                        "id": p.id, "nome": p.nome_sanitizado, "marca": p.marca,
                        "preco": str(p.preco_atual) if p.preco_atual is not None
                        else None,
                        "caminho_imagem": p.caminho_imagem,
                        "mais18": bool(p.selo_mais18),
                    }
        return None
    finally:
        db.engine.dispose()


def produto_por_chave(root: SystemRoot, nome: str,
                      marca: str | None = None) -> dict | None:
    """Produto achado POR CHAVE NATURAL (nunca por id) — dados planos."""
    return _achar(root, nome, marca)


def foto_de(root: SystemRoot, nome: str, marca: str | None = None) -> bytes | None:
    """Bytes da atual.png do produto achado por chave natural."""
    p = _achar(root, nome, marca)
    if p is None or not p["caminho_imagem"]:
        return None
    f = root.biblioteca_imagens / p["caminho_imagem"]
    return f.read_bytes() if f.exists() else None


def alias_aponta_para(root: SystemRoot, alias_raw: str) -> tuple | None:
    """Chave natural do produto que o alias referencia (prova o remap do alias)."""
    from app.core.portabilidade import chave_natural

    db = Database(root).init()
    try:
        with db.Session() as s:
            a = s.execute(select(ProdutoAlias).where(
                ProdutoAlias.alias_raw == alias_raw)).scalar_one_or_none()
            if a is None:
                return None
            return chave_natural(a.produto.nome_sanitizado, a.produto.marca)
    finally:
        db.engine.dispose()


def contagens(root: SystemRoot) -> dict[str, int]:
    db = Database(root).init()
    try:
        with db.Session() as s:
            return {
                "produtos": len(s.execute(select(Produto)).scalars().all()),
                "aliases": len(s.execute(select(ProdutoAlias)).scalars().all()),
                "projetos": len(s.execute(select(ProjetoSalvo)).scalars().all()),
                "layouts": len(s.execute(select(Layout)).scalars().all()),
            }
    finally:
        db.engine.dispose()

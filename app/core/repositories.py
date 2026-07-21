"""
Repositórios (CRUD) — camada de acesso ao banco (síncrona)
==========================================================
Encapsula as queries. A interface (Qt) e os serviços falam com estas classes,
não com o SQLAlchemy direto.

Fase 1: cadastrar/editar/listar produtos, com sanitização determinística no
momento de importar um nome cru.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.core.models import Categoria, Config, Produto, ProdutoAlias
from app.core.sanitize import REGRAS_PADRAO, RegrasSanitizacao, ResultadoSanitizacao, sanitizar


def _para_decimal(valor: Decimal | str | float | None) -> Decimal | None:
    """Converte preço para Decimal com segurança (aceita '5,95' ou '5.95')."""
    if valor is None:
        return None
    if isinstance(valor, Decimal):
        return valor
    if isinstance(valor, str):
        valor = valor.strip().replace("R$", "").replace(" ", "").replace(",", ".")
        if not valor:
            return None
    return Decimal(str(valor))


@dataclass
class ResultadoImport:
    """Resultado de importar um nome cru: o produto e o que a sanitização achou."""

    produto: Produto
    sanitizacao: ResultadoSanitizacao
    criado: bool  # True se foi criado agora; False se já existia


# ==============================================================================
# PRODUTOS
# ==============================================================================


class ProdutoRepositorio:
    def __init__(self, session: Session):
        self.session = session

    # --- leitura ---------------------------------------------------------------

    def get(self, produto_id: int) -> Produto | None:
        return self.session.get(Produto, produto_id)

    def buscar_por_nome_bruto(self, nome_bruto: str) -> Produto | None:
        stmt = select(Produto).where(Produto.nome_bruto == nome_bruto)
        return self.session.execute(stmt).scalar_one_or_none()

    def buscar_por_alias(self, alias_raw: str) -> Produto | None:
        stmt = (
            select(Produto)
            .join(ProdutoAlias)
            .where(ProdutoAlias.alias_raw == alias_raw)
        )
        return self.session.execute(stmt).scalars().first()

    def listar(self, limit: int = 100, offset: int = 0) -> list[Produto]:
        stmt = (
            select(Produto)
            .where(Produto.excluido_em.is_(None))    # F2: lixeira esconde
            .order_by(Produto.nome_sanitizado)
            .limit(limit)
            .offset(offset)
        )
        return list(self.session.execute(stmt).scalars())

    def buscar(self, texto: str, limit: int = 100, offset: int = 0) -> list[Produto]:
        alvo = f"%{texto}%"
        stmt = (
            select(Produto)
            .where(Produto.excluido_em.is_(None))    # F2: lixeira esconde
            .where(
                or_(
                    Produto.nome_sanitizado.ilike(alvo),
                    Produto.nome_bruto.ilike(alvo),
                    Produto.marca.ilike(alvo),
                )
            )
            .order_by(Produto.nome_sanitizado)
            .limit(limit)
            .offset(offset)
        )
        return list(self.session.execute(stmt).scalars())

    def contar(self) -> int:
        return self.session.execute(select(func.count(Produto.id))).scalar_one()

    # --- escrita ---------------------------------------------------------------

    def _garantir_categoria(self, nome: str | None) -> Categoria | None:
        if not nome:
            return None
        stmt = select(Categoria).where(Categoria.nome == nome)
        cat = self.session.execute(stmt).scalar_one_or_none()
        if cat is None:
            cat = Categoria(nome=nome)
            self.session.add(cat)
            self.session.flush()
        return cat

    def _garantir_alias(self, produto_id: int, alias_raw: str) -> None:
        stmt = select(ProdutoAlias).where(
            ProdutoAlias.produto_id == produto_id,
            ProdutoAlias.alias_raw == alias_raw,
        )
        if self.session.execute(stmt).scalar_one_or_none() is None:
            self.session.add(ProdutoAlias(produto_id=produto_id, alias_raw=alias_raw))
            self.session.flush()

    def importar(
        self,
        nome_bruto: str,
        preco: Decimal | str | float | None = None,
        categoria: str | None = None,
        regras: RegrasSanitizacao = REGRAS_PADRAO,
    ) -> ResultadoImport:
        """
        Importa um nome cru: sanitiza, e cria o produto (ou reaproveita o existente,
        casando por nome_bruto exato ou por alias já aprendido).
        """
        res = sanitizar(nome_bruto, regras)
        preco_dec = _para_decimal(preco)

        existente = self.buscar_por_nome_bruto(nome_bruto) or self.buscar_por_alias(
            nome_bruto
        )
        if existente is not None:
            if preco_dec is not None:
                existente.preco_atual = preco_dec
            self._garantir_alias(existente.id, nome_bruto)
            self.session.flush()
            return ResultadoImport(produto=existente, sanitizacao=res, criado=False)

        produto = Produto(
            nome_bruto=nome_bruto,
            nome_sanitizado=res.nome_sanitizado,
            peso_valor=res.peso_valor,
            peso_unidade=res.peso_unidade,
            preco_atual=preco_dec,
            categoria=self._garantir_categoria(categoria),
        )
        self.session.add(produto)
        self.session.flush()
        self._garantir_alias(produto.id, nome_bruto)
        return ResultadoImport(produto=produto, sanitizacao=res, criado=True)

    def aprender_alias(self, produto_id: int, alias_raw: str) -> None:
        """Correção humana vira alias — o banco aprende como a loja escreve."""
        self._garantir_alias(produto_id, alias_raw)

    def editar(self, produto_id: int, **campos) -> Produto:
        """Edita campos de um produto. Preço é convertido para Decimal."""
        produto = self.get(produto_id)
        if produto is None:
            raise ValueError(f"Produto {produto_id} não encontrado")
        if "categoria" in campos:
            produto.categoria = self._garantir_categoria(campos.pop("categoria"))
        if "preco_atual" in campos:
            campos["preco_atual"] = _para_decimal(campos["preco_atual"])
        for chave, valor in campos.items():
            setattr(produto, chave, valor)
        self.session.flush()
        return produto

    def excluir(self, produto_id: int) -> None:
        produto = self.get(produto_id)
        if produto is not None:
            self.session.delete(produto)
            self.session.flush()


# ==============================================================================
# CONFIG
# ==============================================================================


class ConfigRepositorio:
    def __init__(self, session: Session):
        self.session = session

    def get(self, chave: str, padrao=None):
        stmt = select(Config).where(Config.chave == chave)
        cfg = self.session.execute(stmt).scalar_one_or_none()
        return cfg.get_valor() if cfg is not None else padrao

    def set(self, chave: str, valor) -> None:
        stmt = select(Config).where(Config.chave == chave)
        cfg = self.session.execute(stmt).scalar_one_or_none()
        if cfg is None:
            cfg = Config(chave=chave)
            self.session.add(cfg)
        cfg.set_valor(valor)
        self.session.flush()


def regras_de_config(session: Session) -> RegrasSanitizacao:
    """Monta as regras de sanitização aplicando overrides salvos na Config.

    Chaves suportadas (C1 do Bloco D) — qualquer uma ausente/ inválida cai no
    padrão são (C3):
      * 'sanitizacao.siglas'    — lista de siglas que ficam MAIÚSCULAS;
      * 'sanitizacao.glossario' — dicionário de EXPANSÃO ("VD" → "vidro").
    """
    from dataclasses import replace

    cfg = ConfigRepositorio(session)
    regras = REGRAS_PADRAO
    siglas = cfg.get("sanitizacao.siglas")
    if isinstance(siglas, list) and siglas:
        regras = replace(regras,
                         siglas=frozenset(str(s).upper() for s in siglas))
    glossario = cfg.get("sanitizacao.glossario")
    if isinstance(glossario, dict) and glossario:
        regras = replace(regras, glossario_siglas=tuple(
            (str(k), str(v)) for k, v in glossario.items() if k and v))
    # FASE 3 (passo 51): palavras que ficam minúsculas no meio do nome
    minusculas = cfg.get("sanitizacao.palavras_minusculas")
    if isinstance(minusculas, list) and minusculas:
        regras = replace(regras, palavras_minusculas=frozenset(
            str(p).lower() for p in minusculas if str(p).strip()))
    return regras

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


def _alias_limpo(texto: str) -> str:
    """ADENDO 30/07: tira os marcadores de lista que o OCR/colagem
    trazem na frente do nome ("• ", "▶ ", "> ") — enfeite não é
    identidade; o match exato por alias compara os dois lados limpos."""
    return (texto or "").strip().lstrip("•·▶>*–- ").strip()


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
        achado = self.session.execute(stmt).scalars().first()
        if achado is not None:
            return achado
        # ADENDO 30/07: aliases herdados do OCR antigo carregam
        # marcadores ("• FIGADO..."), e a consulta de hoje vem limpa
        # (ou vice-versa) — o match exato compara os DOIS lados limpos
        limpo = _alias_limpo(alias_raw)
        pares = self.session.execute(
            select(ProdutoAlias.produto_id, ProdutoAlias.alias_raw)
        ).all()
        for pid, raw in pares:
            if _alias_limpo(raw) == limpo:
                p = self.session.get(Produto, pid)
                if p is not None and p.excluido_em is None:
                    return p
        return None

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
        # ADENDO 30/07: o alias nasce LIMPO de marcadores de lista do
        # OCR ("• ", "▶ ") — enfeite gravado no cru inutilizava o
        # match exato das importações seguintes
        alias_raw = _alias_limpo(alias_raw) or alias_raw
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

    # F13/B10 (D-07): o hard-delete público `excluir` foi REMOVIDO — zero
    # chamadores (nem produção, nem teste). A exclusão oficial de produto
    # é a lixeira (`excluir_suave("produto", id)`, 30 dias, reversível).

    def definir_familia(self, produto_ids: list[int],
                        familia_id: int | None) -> None:
        """Rodada JM (B4): liga (ou desliga, com None) os produtos à
        família — por id, nunca por posição (I1)."""
        for pid in produto_ids:
            produto = self.get(pid)
            if produto is not None:
                produto.familia_id = familia_id
        self.session.flush()


# ==============================================================================
# FAMÍLIA DE PRODUTOS (Rodada JM, B4)
# ==============================================================================


class FamiliaRepositorio:
    """A família de sabores ("Sardinha Coqueiro 125g") — cada membro é
    um produto completo; a integridade da FK solta é DESTE serviço."""

    def __init__(self, session: Session):
        self.session = session

    def obter_ou_criar(self, nome: str) -> int:
        from app.core.models import FamiliaProduto
        nome = (nome or "").strip()
        stmt = select(FamiliaProduto).where(FamiliaProduto.nome == nome)
        fam = self.session.execute(stmt).scalar_one_or_none()
        if fam is None:
            fam = FamiliaProduto(nome=nome)
            self.session.add(fam)
            self.session.flush()
        return fam.id

    def membros(self, familia_id: int) -> list:
        """Os produtos VIVOS da família (a lixeira não aparece — CI-01),
        ordenados por id (identidade estável)."""
        from app.core.models import Produto
        stmt = (select(Produto)
                .where(Produto.familia_id == familia_id,
                       Produto.excluido_em.is_(None))
                .order_by(Produto.id))
        return list(self.session.execute(stmt).scalars())

    def nome_de(self, familia_id: int) -> str | None:
        from app.core.models import FamiliaProduto
        fam = self.session.get(FamiliaProduto, familia_id)
        return fam.nome if fam is not None else None

    def dissolver(self, familia_id: int) -> None:
        """Zera o vínculo dos membros e remove a família (reversível só
        religando — a família sem membros não significa nada)."""
        from app.core.models import FamiliaProduto, Produto
        for p in self.session.execute(
                select(Produto).where(
                    Produto.familia_id == familia_id)).scalars():
            p.familia_id = None
        fam = self.session.get(FamiliaProduto, familia_id)
        if fam is not None:
            self.session.delete(fam)
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
    # Rodada JM (B1.5): correções de grafia do dono ("fugini" → "fugini"
    # do jeito certo da marca dele) — somadas ao vocabulário de mercado
    ortografia = cfg.get("sanitizacao.ortografia")
    if isinstance(ortografia, dict) and ortografia:
        regras = replace(regras, ortografia=tuple(
            (str(k), str(v)) for k, v in ortografia.items() if k and v))
    # FASE 3 (passo 51): palavras que ficam minúsculas no meio do nome
    minusculas = cfg.get("sanitizacao.palavras_minusculas")
    if isinstance(minusculas, list) and minusculas:
        regras = replace(regras, palavras_minusculas=frozenset(
            str(p).lower() for p in minusculas if str(p).strip()))
    return regras

from decimal import Decimal
from typing import Optional, List
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import NoResultFound

from src.core.models import Produto, ProdutoAlias

class ProductRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_or_update(self, 
                               sku: str, 
                               nome: str, 
                               preco: Decimal, 
                               marca: str = None,
                               peso: str = None,
                               preco_ref: Decimal = None) -> Produto:
        """
        Lógica de Ingestão: Se o SKU existe, atualiza o preço e data.
        Se não existe, cria novo.
        """
        # Tenta buscar existente
        stmt = select(Produto).where(Produto.sku_origem == sku)
        result = await self.session.execute(stmt)
        produto = result.scalar_one_or_none()

        if produto:
            # Atualização (Foco em Preço e Disponibilidade)
            produto.preco_venda_atual = preco
            if preco_ref is not None:
                produto.preco_referencia = preco_ref
            if nome: # Atualiza nome apenas se fornecido
                produto.nome_sanitizado = nome
            # Nota: Não sobrescrevemos marca/peso cegamente se já foram curados manualmente
        else:
            # Criação
            produto = Produto(
                sku_origem=sku,
                nome_sanitizado=nome,
                preco_venda_atual=preco,
                preco_referencia=preco_ref,
                marca_normalizada=marca,
                detalhe_peso=peso,
                status_qualidade=0 # Inicia como 'Novo/Rascunho'
            )
            self.session.add(produto)
        
        await self.session.commit()
        await self.session.refresh(produto)
        return produto

    async def get_by_sku(self, sku: str) -> Optional[Produto]:
        stmt = select(Produto).where(Produto.sku_origem == sku)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def find_by_alias(self, raw_description: str) -> Optional[Produto]:
        """Busca produto através da tabela de aprendizado (Aliases)"""
        stmt = select(Produto).join(ProdutoAlias).where(ProdutoAlias.alias_raw == raw_description)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def add_alias(self, produto_id: int, raw_description: str):
        """Registra um novo alias para aprendizado futuro"""
        # Verifica duplicidade
        stmt = select(ProdutoAlias).where(
            (ProdutoAlias.produto_id == produto_id) & 
            (ProdutoAlias.alias_raw == raw_description)
        )
        result = await self.session.execute(stmt)
        if result.scalar_one_or_none():
            return # Já existe

        alias = ProdutoAlias(produto_id=produto_id, alias_raw=raw_description)
        self.session.add(alias)
        await self.session.commit()

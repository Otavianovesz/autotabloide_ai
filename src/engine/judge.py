import re
from dataclasses import dataclass
from decimal import Decimal
from typing import Optional, List, Tuple
from rapidfuzz import process, fuzz
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.models import Produto, ProdutoAlias
from src.core.repositories import ProductRepository

# STATUS CODES
STATUS_VERDE = "EXISTENTE"       # Match Exato
STATUS_AMARELO = "CANDIDATO"     # Match Fuzzy > 90%
STATUS_VERMELHO = "NOVO"         # Sem Match

@dataclass
class Veredito:
    status: str
    confianca: float
    produto_sugerido: Optional[Produto]
    dados_sanitizados: dict # {sku, nome, preco, etc}

class TheJudge:
    def __init__(self, repository: ProductRepository):
        self.repo = repository

    async def julgar(self, item_input: dict) -> Veredito:
        """
        Orquestra o julgamento de um item de entrada.
        item_input: {'descricao': str, 'preco': Decimal, 'sku_origem': str (opcional)}
        """
        descricao_raw = item_input.get('descricao', '').strip()
        sku_input = item_input.get('sku_origem', descricao_raw).strip() # Se não tem SKU, usa descrição
        preco_input = item_input.get('preco', Decimal('0.00'))

        # 1. MATCH EXATO (SKU ou Alias)
        # Verifica SKU direto
        produto_exato = await self.repo.get_by_sku(sku_input)
        if produto_exato:
            return Veredito(
                status=STATUS_VERDE,
                confianca=1.0,
                produto_sugerido=produto_exato,
                dados_sanitizados=self._preparar_dados(sku_input, descricao_raw, preco_input)
            )

        # Verifica na tabela de Aliases
        produto_alias = await self.repo.find_by_alias(descricao_raw)
        if produto_alias:
            return Veredito(
                status=STATUS_VERDE,
                confianca=1.0, # Confiança total pois foi aprendizado humano prévio
                produto_sugerido=produto_alias,
                dados_sanitizados=self._preparar_dados(sku_input, descricao_raw, preco_input)
            )

        # 2. MATCH FUZZY (Inteligência)
        match_fuzzy = await self._match_fuzzy(descricao_raw)
        if match_fuzzy:
            produto_candidato, score = match_fuzzy
            return Veredito(
                status=STATUS_AMARELO,
                confianca=score / 100.0,
                produto_sugerido=produto_candidato,
                dados_sanitizados=self._preparar_dados(sku_input, descricao_raw, preco_input)
            )

        # 3. NOVO PRODUTO (Sanitização)
        dados_limpos = self._sanitizar(sku_input, descricao_raw, preco_input)
        return Veredito(
            status=STATUS_VERMELHO,
            confianca=0.0,
            produto_sugerido=None,
            dados_sanitizados=dados_limpos
        )

    async def _match_fuzzy(self, descricao: str) -> Optional[Tuple[Produto, float]]:
        """
        Busca aproximada usando Levenshtein.
        NOTA: Para grandes volumes, isso deve ser otimizado (FTS5 ou cache em memória).
        Para operação local (<50k itens), carregar nomes em memória é aceitável.
        """
        # Carrega todos os nomes sanitizados e aliases (Query pode ser pesada, otimizar depois)
        # Aqui, faremos uma busca simplificada: Carregar lista de (id, texto)
        # ATENÇÃO: Em produção real, carregar TUDO pode ser lento. 
        # Vamos assumir que o Repo tem um método `get_all_names_for_matching` ou fazemos query crua aqui.
        
        # Query otimizada para buscar apenas strings para match
        stmt_prod = select(Produto.id, Produto.nome_sanitizado)
        stmt_alias = select(ProdutoAlias.produto_id, ProdutoAlias.alias_raw)
        
        result_prod = await self.repo.session.execute(stmt_prod)
        result_alias = await self.repo.session.execute(stmt_alias)
        
        # Construir lista para rapidfuzz: [(texto, id), ...]
        choices = []
        map_id = {}
        
        for pid, nome in result_prod:
            choices.append(nome)
            map_id[nome] = pid
            
        for pid, alias in result_alias:
            choices.append(alias)
            map_id[alias] = pid # Se houver colisão de texto, o ID é o mesmo ou sobrescreve (ok para match)

        if not choices:
            return None

        # ExtractOne retorna (match, score, index)
        match = process.extractOne(descricao, choices, scorer=fuzz.WRatio)
        
        if match:
            texto_match, score, _ = match
            if score > 90.0:
                produto_id = map_id[texto_match]
                return await self.repo.session.get(Produto, produto_id), score
        
        return None

    def _sanitizar(self, sku: str, descricao: str, preco: Decimal) -> dict:
        """Aplica regras estritas de regex para padronização."""
        nome = descricao.upper() # Trabalha em upper para regex, depois Title Case
        
        # 1. Unidades de Medida
        # '500 GR', '500 Gr' -> '500g'
        nome = re.sub(r'(\d+)\s*(GR|GRAMAS|G)(?!\w)', r'\1g', nome, flags=re.IGNORECASE)
        
        # '1 KG', '1.5 KILO' -> '1kg'
        nome = re.sub(r'(\d+[.,]?\d*)\s*(KG|KILO|QUILO)(S?)(?!\w)', r'\1kg', nome, flags=re.IGNORECASE)
        
        # '1 LITRO', '1000 ML' -> '1L', '1000ml'
        nome = re.sub(r'(\d+)\s*(LITRO|LITROS|LT|L)(?!\w)', r'\1L', nome, flags=re.IGNORECASE)
        nome = re.sub(r'(\d+)\s*(ML)(?!\w)', r'\1ml', nome, flags=re.IGNORECASE)

        # 2. Descrição (Regex genérico para extrair marca poderia vir aqui, mas é complexo sem lista)
        # Vamos confiar no Title Case para limpeza visual
        nome_final = nome.title()
        
        # Ajustes pós-Title (unidades ficaram '500G' ou '1Ml' por causa do title(), corrigir)
        # '500G' -> '500g'
        nome_final = re.sub(r'(\d+)G(?!\w)', r'\1g', nome_final)
        nome_final = re.sub(r'(\d+)Ml(?!\w)', r'\1ml', nome_final)
        nome_final = re.sub(r'(\d+)Kg(?!\w)', r'\1kg', nome_final)
        
        return {
            "sku_origem": sku,
            "nome_sanitizado": nome_final,
            "marca_normalizada": None, # Inferir depois se necessário
            "preco_venda_atual": preco
        }

    def _preparar_dados(self, sku: str, nome: str, preco: Decimal) -> dict:
        return {
            "sku_origem": sku,
            "nome_sanitizado": nome, # Mantém original se já existe
            "preco_venda_atual": preco
        }

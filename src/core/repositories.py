"""
AutoTabloide AI - Repositórios de Dados (Repository Pattern)
=============================================================
Camada de acesso ao banco de dados conforme Vol. I, Cap. 1.3.
Encapsula queries e desacopla lógica de persistência da interface.
"""

from decimal import Decimal
from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import uuid4
import json
import hashlib

from sqlalchemy import select, update, delete, func, or_, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import NoResultFound, IntegrityError

from src.core.models import (
    Produto, ProdutoAlias, LayoutMeta, ProjetoSalvo, 
    AuditLog, KnowledgeVector, HumanCorrection,
    TipoAcao, TipoEntidade, StatusQualidade
)


# ==============================================================================
# REPOSITORY: PRODUTOS
# ==============================================================================

class ProductRepository:
    """Repositório para operações CRUD em Produtos."""
    
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_or_update(
        self, 
        sku: str, 
        nome: str, 
        preco: Decimal, 
        marca: str = None,
        peso: str = None,
        preco_ref: Decimal = None,
        categoria: str = None
    ) -> Produto:
        """
        Lógica de Upsert: Se SKU existe, atualiza; senão, cria novo.
        """
        stmt = select(Produto).where(Produto.sku_origem == sku)
        result = await self.session.execute(stmt)
        produto = result.scalar_one_or_none()

        if produto:
            # Atualização
            produto.preco_venda_atual = preco
            if preco_ref is not None:
                produto.preco_referencia = preco_ref
            if nome:
                produto.nome_sanitizado = nome
            if categoria:
                produto.categoria = categoria
        else:
            # Criação
            produto = Produto(
                sku_origem=sku,
                nome_sanitizado=nome,
                preco_venda_atual=preco,
                preco_referencia=preco_ref,
                marca_normalizada=marca,
                detalhe_peso=peso,
                categoria=categoria,
                status_qualidade=StatusQualidade.INCOMPLETO.value
            )
            self.session.add(produto)
        
        await self.session.commit()
        await self.session.refresh(produto)
        return produto

    async def get_by_id(self, produto_id: int) -> Optional[Produto]:
        """Busca produto por ID."""
        stmt = select(Produto).where(Produto.id == produto_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_sku(self, sku: str) -> Optional[Produto]:
        """Busca produto por SKU."""
        stmt = select(Produto).where(Produto.sku_origem == sku)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def find_by_alias(self, raw_description: str) -> Optional[Produto]:
        """Busca produto através da tabela de aliases."""
        stmt = (
            select(Produto)
            .join(ProdutoAlias)
            .where(ProdutoAlias.alias_raw == raw_description)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def search(
        self, 
        query: str = None, 
        categoria: str = None,
        status: int = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Produto]:
        """Busca paginada com filtros."""
        stmt = select(Produto)
        
        conditions = []
        if query:
            conditions.append(
                or_(
                    Produto.nome_sanitizado.ilike(f"%{query}%"),
                    Produto.sku_origem.ilike(f"%{query}%"),
                    Produto.marca_normalizada.ilike(f"%{query}%")
                )
            )
        if categoria:
            conditions.append(Produto.categoria == categoria)
        if status is not None:
            conditions.append(Produto.status_qualidade == status)
        
        if conditions:
            stmt = stmt.where(and_(*conditions))
        
        stmt = stmt.order_by(Produto.nome_sanitizado).limit(limit).offset(offset)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def count(self, status: int = None) -> int:
        """Conta produtos, opcionalmente filtrado por status."""
        stmt = select(func.count(Produto.id))
        if status is not None:
            stmt = stmt.where(Produto.status_qualidade == status)
        result = await self.session.execute(stmt)
        return result.scalar()

    async def add_alias(self, produto_id: int, raw_description: str, confidence: float = 1.0):
        """Registra um alias para aprendizado futuro."""
        # Verifica duplicidade
        stmt = select(ProdutoAlias).where(
            (ProdutoAlias.produto_id == produto_id) & 
            (ProdutoAlias.alias_raw == raw_description)
        )
        result = await self.session.execute(stmt)
        if result.scalar_one_or_none():
            return  # Já existe

        alias = ProdutoAlias(
            produto_id=produto_id, 
            alias_raw=raw_description,
            confidence=Decimal(str(confidence))
        )
        self.session.add(alias)
        await self.session.commit()

    async def update_quality_status(self, produto_id: int, status: int):
        """Atualiza status de qualidade do produto."""
        stmt = (
            update(Produto)
            .where(Produto.id == produto_id)
            .values(status_qualidade=status)
        )
        await self.session.execute(stmt)
        await self.session.commit()

    async def update_images(self, produto_id: int, hashes: List[str]):
        """Atualiza lista de imagens do produto."""
        stmt = (
            update(Produto)
            .where(Produto.id == produto_id)
            .values(img_hash_ref=json.dumps(hashes))
        )
        await self.session.execute(stmt)
        await self.session.commit()
    
    async def add_image_to_product(self, produto_id: int, img_hash: str):
        """Adiciona uma imagem ao produto e recalcula qualidade."""
        produto = await self.get_by_id(produto_id)
        if not produto:
            return
        
        # Adiciona hash à lista existente
        current_hashes = produto.get_images() if hasattr(produto, 'get_images') else []
        if img_hash not in current_hashes:
            current_hashes.append(img_hash)
            await self.update_images(produto_id, current_hashes)
        
        # Recalcula qualidade
        await self.recalculate_quality_status(produto_id)
    
    async def recalculate_quality_status(self, produto_id: int) -> int:
        """
        Recalcula status de qualidade automaticamente.
        
        Semáforo de Qualidade (Vol. I, Cap. 2.1):
        - 0 (CRÍTICO): Sem preço ou sem nome
        - 1 (INCOMPLETO): Sem imagem associada
        - 2 (ATENÇÃO): Dados completos mas precisa revisão
        - 3 (PERFEITO): Todos os campos completos e validados
        
        Returns:
            Novo status calculado
        """
        produto = await self.get_by_id(produto_id)
        if not produto:
            return 0
        
        # Critérios de avaliação
        has_price = produto.preco_venda_atual is not None and float(produto.preco_venda_atual) > 0
        has_name = produto.nome_sanitizado is not None and len(produto.nome_sanitizado) > 3
        has_images = len(produto.get_images()) > 0 if hasattr(produto, 'get_images') else False
        has_brand = produto.marca_normalizada is not None and len(produto.marca_normalizada) > 0
        
        # Calcula status
        if not has_price or not has_name:
            status = StatusQualidade.CRITICO.value  # 0
        elif not has_images:
            status = StatusQualidade.INCOMPLETO.value  # 1
        elif not has_brand:
            status = StatusQualidade.ATENCAO.value  # 2
        else:
            status = StatusQualidade.PERFEITO.value  # 3
        
        # Atualiza no banco
        await self.update_quality_status(produto_id, status)
        return status
    
    async def recalculate_all_quality(self) -> Dict[int, int]:
        """
        Recalcula qualidade de todos os produtos.
        Útil para migração ou auditoria em massa.
        
        Returns:
            Dict de {produto_id: novo_status}
        """
        stmt = select(Produto)
        result = await self.session.execute(stmt)
        produtos = result.scalars().all()
        
        results = {}
        for produto in produtos:
            new_status = await self.recalculate_quality_status(produto.id)
            results[produto.id] = new_status
        
        return results

    # ==========================================================================
    # PROTOCOLO MEMÓRIA VIVA: Aprendizado de Correções
    # ==========================================================================

    async def learn_correction(
        self, 
        raw_input: str, 
        produto_id: int,
        corrected_field: str, 
        final_value: str
    ):
        """
        PROTOCOLO MEMÓRIA VIVA: Quando o usuário corrige manualmente 
        um campo na UI, o sistema grava essa correção como uma 
        'regra de ouro' para o futuro.
        
        Exemplo: O usuário corrigiu nome de 'CERV SKOL' para 'Cerveja Skol LATA'
        
        Args:
            raw_input: Texto original (como veio do Excel/input)
            produto_id: ID do produto associado
            corrected_field: Campo corrigido (nome_sanitizado, marca, etc)
            final_value: Valor final depois da correção humana
        """
        from datetime import datetime
        
        # Busca alias existente
        stmt = select(ProdutoAlias).where(ProdutoAlias.alias_raw == raw_input)
        result = await self.session.execute(stmt)
        alias = result.scalar_one_or_none()

        if alias:
            # Atualiza override existente
            current_overrides = alias.get_overrides()
            current_overrides[corrected_field] = final_value
            alias.set_overrides(current_overrides)
            alias.usage_count = (alias.usage_count or 0) + 1
            alias.last_confirmed = datetime.now()
            alias.confidence = Decimal("1.0")  # Confirmação humana = 100%
        else:
            # Cria novo aprendizado
            new_alias = ProdutoAlias(
                alias_raw=raw_input,
                produto_id=produto_id,
                override_data=json.dumps({corrected_field: final_value}),
                confidence=Decimal("1.0"),
                usage_count=1,
                last_confirmed=datetime.now()
            )
            self.session.add(new_alias)
        
        await self.session.commit()

    async def get_learned_value(self, raw_input: str, field: str) -> Optional[str]:
        """
        Consulta se existe uma correção aprendida para este input/campo.
        O Sentinel deve chamar ANTES de invocar a LLM.
        
        Returns:
            Valor aprendido ou None se não houver correção
        """
        stmt = select(ProdutoAlias).where(ProdutoAlias.alias_raw == raw_input)
        result = await self.session.execute(stmt)
        alias = result.scalar_one_or_none()
        
        if alias:
            overrides = alias.get_overrides()
            if field in overrides:
                # Incrementa uso
                alias.usage_count = (alias.usage_count or 0) + 1
                await self.session.commit()
                return overrides[field]
        
        return None

    async def get_best_match_alias(self, raw_input: str) -> Optional[Dict[str, Any]]:
        """
        Busca o melhor alias com overrides para um input.
        Retorna dict com produto_id e todos os overrides aprendidos.
        """
        stmt = (
            select(ProdutoAlias)
            .where(ProdutoAlias.alias_raw == raw_input)
            .order_by(ProdutoAlias.confidence.desc(), ProdutoAlias.usage_count.desc())
        )
        result = await self.session.execute(stmt)
        alias = result.scalar_one_or_none()
        
        if alias:
            return {
                "produto_id": alias.produto_id,
                "overrides": alias.get_overrides(),
                "confidence": float(alias.confidence) if alias.confidence else 1.0,
                "usage_count": alias.usage_count or 0
            }
        
        return None


# ==============================================================================
# REPOSITORY: LAYOUTS
# ==============================================================================

class LayoutRepository:
    """Repositório para operações em metadados de templates SVG."""
    
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self,
        nome: str,
        arquivo: str,
        tipo_midia: str,
        capacidade: int,
        fontes: List[str] = None,
        estrutura: dict = None,
        integrity_hash: str = None
    ) -> LayoutMeta:
        """Registra um novo layout no banco."""
        layout = LayoutMeta(
            nome_amigavel=nome,
            arquivo_fonte=arquivo,
            tipo_midia=tipo_midia,
            capacidade_slots=capacidade,
            fontes_requeridas=json.dumps(fontes or []),
            estrutura_json=json.dumps(estrutura or {}),
            integrity_hash=integrity_hash
        )
        self.session.add(layout)
        await self.session.commit()
        await self.session.refresh(layout)
        return layout

    async def get_by_id(self, layout_id: int) -> Optional[LayoutMeta]:
        """Busca layout por ID."""
        stmt = select(LayoutMeta).where(LayoutMeta.id == layout_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_arquivo(self, arquivo: str) -> Optional[LayoutMeta]:
        """Busca layout pelo nome do arquivo fonte."""
        stmt = select(LayoutMeta).where(LayoutMeta.arquivo_fonte == arquivo)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_all(self, tipo_midia: str = None) -> List[LayoutMeta]:
        """Lista todos os layouts, opcionalmente filtrado por tipo."""
        stmt = select(LayoutMeta)
        if tipo_midia:
            stmt = stmt.where(LayoutMeta.tipo_midia == tipo_midia)
        stmt = stmt.order_by(LayoutMeta.nome_amigavel)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def update_thumbnail(self, layout_id: int, thumbnail_path: str):
        """Atualiza caminho do thumbnail."""
        stmt = (
            update(LayoutMeta)
            .where(LayoutMeta.id == layout_id)
            .values(thumbnail_path=thumbnail_path)
        )
        await self.session.execute(stmt)
        await self.session.commit()

    async def delete(self, layout_id: int):
        """Remove um layout."""
        stmt = delete(LayoutMeta).where(LayoutMeta.id == layout_id)
        await self.session.execute(stmt)
        await self.session.commit()


# ==============================================================================
# REPOSITORY: PROJETOS
# ==============================================================================

class ProjectRepository:
    """Repositório para operações em projetos salvos (workspaces)."""
    
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self,
        nome: str,
        layout_id: int,
        estado_slots: dict = None,
        author_id: str = None
    ) -> ProjetoSalvo:
        """Cria um novo projeto."""
        projeto = ProjetoSalvo(
            nome_projeto=nome,
            uuid=str(uuid4()),
            layout_id=layout_id,
            estado_slots=json.dumps(estado_slots or {}),
            author_id=author_id
        )
        self.session.add(projeto)
        await self.session.commit()
        await self.session.refresh(projeto)
        return projeto

    async def get_by_id(self, projeto_id: int) -> Optional[ProjetoSalvo]:
        """Busca projeto por ID."""
        stmt = select(ProjetoSalvo).where(ProjetoSalvo.id == projeto_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_uuid(self, uuid: str) -> Optional[ProjetoSalvo]:
        """Busca projeto por UUID."""
        stmt = select(ProjetoSalvo).where(ProjetoSalvo.uuid == uuid)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_recent(self, limit: int = 20) -> List[ProjetoSalvo]:
        """Lista projetos recentes."""
        stmt = (
            select(ProjetoSalvo)
            .order_by(ProjetoSalvo.last_modified.desc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def save_snapshot(
        self,
        projeto_id: int,
        slots: dict,
        overrides: dict = None,
        layout_hash: str = None
    ):
        """Salva snapshot imutável do estado atual."""
        stmt = (
            update(ProjetoSalvo)
            .where(ProjetoSalvo.id == projeto_id)
            .values(
                estado_slots=json.dumps(slots, ensure_ascii=False),
                overrides_json=json.dumps(overrides or {}, ensure_ascii=False),
                layout_integrity_hash=layout_hash,
                is_dirty=False
            )
        )
        await self.session.execute(stmt)
        await self.session.commit()

    async def set_dirty(self, projeto_id: int, dirty: bool = True):
        """Marca projeto como modificado (para autosave)."""
        stmt = (
            update(ProjetoSalvo)
            .where(ProjetoSalvo.id == projeto_id)
            .values(is_dirty=dirty)
        )
        await self.session.execute(stmt)
        await self.session.commit()

    async def lock(self, projeto_id: int, locked: bool = True):
        """Trava/destrava projeto para edição."""
        stmt = (
            update(ProjetoSalvo)
            .where(ProjetoSalvo.id == projeto_id)
            .values(is_locked=locked)
        )
        await self.session.execute(stmt)
        await self.session.commit()

    async def delete(self, projeto_id: int):
        """Remove um projeto."""
        stmt = delete(ProjetoSalvo).where(ProjetoSalvo.id == projeto_id)
        await self.session.execute(stmt)
        await self.session.commit()

    async def duplicate(self, projeto_id: int, new_name: str) -> ProjetoSalvo:
        """Cria uma cópia profunda do projeto."""
        original = await self.get_by_id(projeto_id)
        if not original:
            raise ValueError(f"Projeto {projeto_id} não encontrado")
        
        copy = ProjetoSalvo(
            nome_projeto=new_name,
            uuid=str(uuid4()),
            layout_id=original.layout_id,
            layout_integrity_hash=original.layout_integrity_hash,
            estado_slots=original.estado_slots,
            overrides_json=original.overrides_json,
            author_id=original.author_id
        )
        self.session.add(copy)
        await self.session.commit()
        await self.session.refresh(copy)
        return copy


# ==============================================================================
# REPOSITORY: AUDIT LOG
# ==============================================================================

class AuditRepository:
    """Repositório para operações de auditoria e rastreabilidade."""
    
    def __init__(self, session: AsyncSession):
        self.session = session

    async def log(
        self,
        entity_type: str,
        entity_id: int,
        action_type: str,
        diff: dict = None,
        user_ref: str = None,
        description: str = None,
        severity: int = 1
    ) -> AuditLog:
        """Registra um evento de auditoria."""
        entry = AuditLog(
            entity_type=entity_type,
            entity_id=entity_id,
            action_type=action_type,
            diff_payload=json.dumps(diff or {}),
            user_ref=user_ref,
            description=description,
            severity=severity
        )
        self.session.add(entry)
        await self.session.commit()
        await self.session.refresh(entry)
        return entry

    async def log_update(
        self,
        entity_type: str,
        entity_id: int,
        field: str,
        old_value: Any,
        new_value: Any,
        source: str = "unknown",
        user_ref: str = None
    ) -> AuditLog:
        """Atalho para registrar uma atualização."""
        diff = {
            "field": field,
            "old_value": old_value,
            "new_value": new_value,
            "source_context": source
        }
        description = f"{field} alterado de '{old_value}' para '{new_value}'"
        return await self.log(
            entity_type=entity_type,
            entity_id=entity_id,
            action_type=TipoAcao.UPDATE.value,
            diff=diff,
            user_ref=user_ref,
            description=description
        )

    async def get_timeline(
        self,
        limit: int = 50,
        offset: int = 0,
        entity_type: str = None,
        entity_id: int = None,
        action_type: str = None
    ) -> List[AuditLog]:
        """Retorna timeline de eventos com paginação."""
        stmt = select(AuditLog)
        
        conditions = []
        if entity_type:
            conditions.append(AuditLog.entity_type == entity_type)
        if entity_id:
            conditions.append(AuditLog.entity_id == entity_id)
        if action_type:
            conditions.append(AuditLog.action_type == action_type)
        
        if conditions:
            stmt = stmt.where(and_(*conditions))
        
        stmt = stmt.order_by(AuditLog.timestamp.desc()).limit(limit).offset(offset)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_by_id(self, log_id: int) -> Optional[AuditLog]:
        """Busca entrada de log por ID."""
        stmt = select(AuditLog).where(AuditLog.id == log_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def rollback_entry(self, log_id: int, user_ref: str = None) -> Optional[AuditLog]:
        """
        Reverte uma ação específica.
        Retorna o novo log de rollback ou None se não reversível.
        """
        original = await self.get_by_id(log_id)
        if not original or not original.can_rollback():
            return None
        
        diff = original.get_diff()
        old_value = diff.get('old_value')
        field = diff.get('field')
        
        # Registra o rollback
        rollback_log = await self.log(
            entity_type=original.entity_type,
            entity_id=original.entity_id,
            action_type=TipoAcao.ROLLBACK.value,
            diff={
                "field": field,
                "old_value": diff.get('new_value'),  # O "novo" vira "antigo"
                "new_value": old_value,  # O "antigo" volta a ser atual
                "original_log_id": log_id
            },
            user_ref=user_ref,
            description=f"Rollback de: {original.description}",
            severity=2
        )
        
        return rollback_log


# ==============================================================================
# REPOSITORY: KNOWLEDGE VECTORS (RAG)
# ==============================================================================

class KnowledgeRepository:
    """Repositório para operações de RAG e embeddings."""
    
    def __init__(self, session: AsyncSession):
        self.session = session

    async def store_embedding(
        self,
        text: str,
        embedding: bytes,
        dimensions: int = 384,
        produto_id: int = None,
        validated_output: str = None,
        priority_boost: float = 1.0
    ) -> KnowledgeVector:
        """Armazena um novo embedding."""
        text_hash = hashlib.md5(text.encode()).hexdigest()
        
        # Verifica duplicidade
        existing = await self.get_by_hash(text_hash)
        if existing:
            return existing
        
        vector = KnowledgeVector(
            source_text=text,
            text_hash=text_hash,
            embedding=embedding,
            dimensions=dimensions,
            produto_id=produto_id,
            validated_output=validated_output,
            priority_boost=Decimal(str(priority_boost))
        )
        self.session.add(vector)
        await self.session.commit()
        await self.session.refresh(vector)
        return vector

    async def get_by_hash(self, text_hash: str) -> Optional[KnowledgeVector]:
        """Busca embedding por hash do texto."""
        stmt = select(KnowledgeVector).where(KnowledgeVector.text_hash == text_hash)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_all_embeddings(self) -> List[KnowledgeVector]:
        """Retorna todos os embeddings para busca KNN."""
        stmt = select(KnowledgeVector).order_by(KnowledgeVector.priority_boost.desc())
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def record_correction(
        self,
        original_input: str,
        ai_prediction: str,
        human_correction: str,
        confidence_delta: float = None
    ) -> HumanCorrection:
        """Registra uma correção humana para aprendizado."""
        input_hash = hashlib.md5(original_input.encode()).hexdigest()
        
        correction = HumanCorrection(
            input_hash=input_hash,
            original_input=original_input,
            ai_prediction=ai_prediction,
            human_correction=human_correction,
            confidence_delta=Decimal(str(confidence_delta)) if confidence_delta else None
        )
        self.session.add(correction)
        await self.session.commit()
        await self.session.refresh(correction)
        return correction

    async def get_pending_corrections(self, limit: int = 100) -> List[HumanCorrection]:
        """Retorna correções pendentes de processamento."""
        stmt = (
            select(HumanCorrection)
            .where(HumanCorrection.processed == False)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def mark_processed(self, correction_id: int):
        """Marca correção como processada."""
        stmt = (
            update(HumanCorrection)
            .where(HumanCorrection.id == correction_id)
            .values(processed=True)
        )
        await self.session.execute(stmt)
        await self.session.commit()

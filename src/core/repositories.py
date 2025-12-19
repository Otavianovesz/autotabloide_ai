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

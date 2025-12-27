"""
AutoTabloide AI - Soft Delete Mixin
=====================================
Mixin para soft delete em modelos SQLAlchemy.
PROTOCOLO DE RETIFICAÇÃO: Passo 24 (Soft Delete).

Produtos NUNCA são deletados, apenas desativados.
Isso permite recuperação e histórico completo.
"""

from datetime import datetime
from typing import Optional, List, TypeVar, Type
from sqlalchemy import Column, Boolean, DateTime, event, select
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession

T = TypeVar('T', bound='SoftDeleteMixin')


class SoftDeleteMixin:
    """
    Mixin que adiciona soft delete a qualquer modelo.
    
    Campos adicionados:
    - is_active: bool - Se registro está ativo (não deletado)
    - deleted_at: datetime - Quando foi "deletado"
    
    Uso:
        class Produto(Base, SoftDeleteMixin):
            __tablename__ = "produtos"
            ...
    """
    
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    deleted_at = Column(DateTime, nullable=True)
    
    def soft_delete(self) -> None:
        """Marca registro como deletado (soft delete)."""
        self.is_active = False
        self.deleted_at = datetime.utcnow()
    
    def restore(self) -> None:
        """Restaura registro soft-deletado."""
        self.is_active = True
        self.deleted_at = None
    
    @property
    def is_deleted(self) -> bool:
        """Verifica se registro está soft-deletado."""
        return not self.is_active
    
    @classmethod
    async def find_active(
        cls: Type[T],
        session: AsyncSession,
        **filters
    ) -> List[T]:
        """
        Busca apenas registros ativos (não deletados).
        
        Args:
            session: Sessão do banco
            **filters: Filtros adicionais
            
        Returns:
            Lista de registros ativos
        """
        stmt = select(cls).where(cls.is_active == True)
        
        for key, value in filters.items():
            if hasattr(cls, key):
                stmt = stmt.where(getattr(cls, key) == value)
        
        result = await session.execute(stmt)
        return result.scalars().all()
    
    @classmethod
    async def find_deleted(
        cls: Type[T],
        session: AsyncSession,
        since: Optional[datetime] = None
    ) -> List[T]:
        """
        Busca registros soft-deletados.
        
        Args:
            session: Sessão do banco
            since: Apenas deletados após esta data
            
        Returns:
            Lista de registros deletados
        """
        stmt = select(cls).where(cls.is_active == False)
        
        if since:
            stmt = stmt.where(cls.deleted_at >= since)
        
        result = await session.execute(stmt)
        return result.scalars().all()
    
    @classmethod
    async def restore_by_id(
        cls: Type[T],
        session: AsyncSession,
        record_id: int
    ) -> Optional[T]:
        """
        Restaura um registro pelo ID.
        
        Args:
            session: Sessão do banco
            record_id: ID do registro
            
        Returns:
            Registro restaurado ou None
        """
        stmt = select(cls).where(
            cls.id == record_id,
            cls.is_active == False
        )
        
        result = await session.execute(stmt)
        record = result.scalar_one_or_none()
        
        if record:
            record.restore()
            await session.commit()
        
        return record
    
    @classmethod
    async def purge_old_deleted(
        cls: Type[T],
        session: AsyncSession,
        older_than_days: int = 90
    ) -> int:
        """
        Remove permanentemente registros deletados há mais de X dias.
        
        CUIDADO: Esta é uma deleção REAL e irreversível!
        
        Args:
            session: Sessão do banco
            older_than_days: Dias desde a deleção
            
        Returns:
            Número de registros removidos
        """
        from datetime import timedelta
        from sqlalchemy import delete
        
        cutoff = datetime.utcnow() - timedelta(days=older_than_days)
        
        stmt = delete(cls).where(
            cls.is_active == False,
            cls.deleted_at < cutoff
        )
        
        result = await session.execute(stmt)
        await session.commit()
        
        return result.rowcount


class AuditedSoftDeleteMixin(SoftDeleteMixin):
    """
    Soft delete com auditoria automática.
    
    Registra quem deletou e motivo.
    """
    
    deleted_by = Column('deleted_by', nullable=True)
    deletion_reason = Column('deletion_reason', nullable=True)
    
    def soft_delete_with_reason(self, deleted_by: str, reason: str = "") -> None:
        """
        Soft delete com registro de quem deletou e motivo.
        
        Args:
            deleted_by: Identificador de quem deletou
            reason: Motivo da deleção
        """
        self.is_active = False
        self.deleted_at = datetime.utcnow()
        self.deleted_by = deleted_by
        self.deletion_reason = reason


# ==============================================================================
# QUERY HELPER
# ==============================================================================

def filter_active_only(query):
    """
    Decorator/filter para queries que devem ignorar soft-deleted.
    
    Uso:
        stmt = filter_active_only(select(Produto))
    """
    # Assume que modelo tem is_active
    return query.filter(query.column_descriptions[0]['entity'].is_active == True)


# ==============================================================================
# MIGRATION HELPER
# ==============================================================================

async def add_soft_delete_columns(session: AsyncSession, table_name: str) -> bool:
    """
    Adiciona colunas de soft delete a uma tabela existente.
    
    Útil para migração de tabelas antigas.
    
    Args:
        session: Sessão do banco
        table_name: Nome da tabela
        
    Returns:
        True se colunas foram adicionadas
    """
    from sqlalchemy import text
    
    try:
        # Verifica se coluna já existe
        result = await session.execute(text(f"PRAGMA table_info({table_name})"))
        columns = [row[1] for row in result.fetchall()]
        
        added = False
        
        if 'is_active' not in columns:
            await session.execute(text(
                f"ALTER TABLE {table_name} ADD COLUMN is_active BOOLEAN DEFAULT 1"
            ))
            added = True
        
        if 'deleted_at' not in columns:
            await session.execute(text(
                f"ALTER TABLE {table_name} ADD COLUMN deleted_at TIMESTAMP"
            ))
            added = True
        
        if added:
            await session.commit()
            
        return added
        
    except Exception as e:
        await session.rollback()
        raise

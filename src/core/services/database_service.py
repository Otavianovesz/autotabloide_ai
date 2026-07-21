"""
AutoTabloide AI - Database Service
==================================
Phase 0.1: Service Layer
Phase 1.1: Async Database Foundation

Serviço central de persistência.
Abstrai a sessão do SQLAlchemy e gerencia transações.
Garante Atomicidade (ACID).
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession
from src.core.services.base import BaseService
from src.core.database import AsyncSessionLocal, LearningSessionLocal, init_db, check_db_health, vacuum_and_checkpoint

class DatabaseService(BaseService):
    """
    Gerencia acesso aos bancos de dados Core e Learning.
    Fornece Context Managers para transações atômicas.
    """
    
    def __init__(self):
        super().__init__()
        # Inicialização lazy ou no boot via initialize()
        
    async def initialize(self):
        """Inicializa schemas e verifica integridade."""
        try:
            await init_db()
            health = await check_db_health()
            
            if health["status"] != "healthy":
                self.log_error("Falha no Banco de Dados", f"Integridade comprometida: {health}")
            else:
                self.bus.status_message.emit("Banco de Dados conectado e verificado.", 3000)
                
        except Exception as e:
            self.log_error("Erro Crítico DB", str(e))
            raise

    @asynccontextmanager
    async def transaction(self) -> AsyncGenerator[AsyncSession, None]:
        """
        Transação Atômica no Core DB.
        Uso:
            async with db_service.transaction() as session:
                await repo.add(item)
        """
        async with AsyncSessionLocal() as session:
            async with session.begin(): # Garante Commit/Rollback atômico
                yield session

    @asynccontextmanager
    async def learning_transaction(self) -> AsyncGenerator[AsyncSession, None]:
        """Transação Atômica no Learning DB."""
        async with LearningSessionLocal() as session:
            async with session.begin():
                yield session

    async def run_maintenance(self):
        """Executa VACUUM e otimização."""
        await vacuum_and_checkpoint()
        self.bus.status_message.emit("Manutenção do banco concluída.", 3000)

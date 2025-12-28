"""
AutoTabloide AI - Database Bridge
=================================
PROTOCOLO DE CONVERGÊNCIA 260 - Fase 2 (Passos 41-55)
Bridge entre UI Qt e SQLAlchemy. A UI nunca toca o banco diretamente.
"""

from __future__ import annotations
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass
import logging

from PySide6.QtCore import QObject, Signal, Slot, QThread, QMutex, QMutexLocker

logger = logging.getLogger("DatabaseBridge")


@dataclass
class QueryResult:
    """Resultado de uma query."""
    success: bool
    data: List[Dict] = None
    error: str = ""
    total_count: int = 0


class DatabaseWorker(QThread):
    """
    Worker thread para operações de banco.
    Executa queries sem travar a UI.
    """
    
    result_ready = Signal(str, object)  # query_id, QueryResult
    error_occurred = Signal(str, str)   # query_id, error
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._queue: List[tuple] = []
        self._mutex = QMutex()
        self._running = True
    
    def run(self):
        """Loop principal do worker."""
        while self._running:
            task = None
            
            with QMutexLocker(self._mutex):
                if self._queue:
                    task = self._queue.pop(0)
            
            if task:
                query_id, operation, args = task
                try:
                    result = self._execute(operation, args)
                    self.result_ready.emit(query_id, result)
                except Exception as e:
                    logger.error(f"DB Error: {e}")
                    self.error_occurred.emit(query_id, str(e))
            else:
                self.msleep(50)
    
    def _execute(self, operation: str, args: Dict) -> QueryResult:
        """Executa operação no banco."""
        from src.database.models import Product
        from src.database.core import get_session
        
        session = get_session()
        
        try:
            if operation == "get_products":
                return self._get_products(session, args)
            elif operation == "get_product":
                return self._get_product(session, args)
            elif operation == "search_products":
                return self._search_products(session, args)
            elif operation == "update_product":
                return self._update_product(session, args)
            elif operation == "count_products":
                return self._count_products(session)
            else:
                return QueryResult(False, error=f"Unknown operation: {operation}")
        finally:
            session.close()
    
    def _get_products(self, session, args: Dict) -> QueryResult:
        """Busca produtos com paginação."""
        from src.database.models import Product
        
        offset = args.get("offset", 0)
        limit = args.get("limit", 50)
        
        query = session.query(Product).filter(Product.deleted == False)
        total = query.count()
        products = query.offset(offset).limit(limit).all()
        
        data = [self._product_to_dict(p) for p in products]
        
        return QueryResult(True, data=data, total_count=total)
    
    def _get_product(self, session, args: Dict) -> QueryResult:
        """Busca produto por ID."""
        from src.database.models import Product
        
        product_id = args.get("id")
        product = session.query(Product).filter(Product.id == product_id).first()
        
        if product:
            return QueryResult(True, data=[self._product_to_dict(product)])
        return QueryResult(False, error="Produto não encontrado")
    
    def _search_products(self, session, args: Dict) -> QueryResult:
        """Busca com filtro."""
        from src.database.models import Product
        
        term = args.get("term", "")
        offset = args.get("offset", 0)
        limit = args.get("limit", 50)
        
        query = session.query(Product).filter(
            Product.deleted == False,
            Product.nome_sanitizado.ilike(f"%{term}%")
        )
        
        total = query.count()
        products = query.offset(offset).limit(limit).all()
        
        data = [self._product_to_dict(p) for p in products]
        
        return QueryResult(True, data=data, total_count=total)
    
    def _update_product(self, session, args: Dict) -> QueryResult:
        """Atualiza produto."""
        from src.database.models import Product
        
        product_id = args.get("id")
        updates = args.get("updates", {})
        
        product = session.query(Product).filter(Product.id == product_id).first()
        
        if not product:
            return QueryResult(False, error="Produto não encontrado")
        
        for key, value in updates.items():
            if hasattr(product, key):
                setattr(product, key, value)
        
        session.commit()
        
        return QueryResult(True, data=[self._product_to_dict(product)])
    
    def _count_products(self, session) -> QueryResult:
        """Conta total de produtos."""
        from src.database.models import Product
        
        total = session.query(Product).filter(Product.deleted == False).count()
        
        return QueryResult(True, data=[], total_count=total)
    
    def _product_to_dict(self, product) -> Dict:
        """Converte Product para dict serializável."""
        return {
            "id": product.id,
            "nome_sanitizado": product.nome_sanitizado,
            "preco_venda_atual": float(product.preco_venda_atual or 0),
            "preco_referencia": float(product.preco_referencia or 0) if product.preco_referencia else None,
            "marca_normalizada": product.marca_normalizada,
            "detalhe_peso": product.detalhe_peso,
            "sku_origem": product.sku_origem,
            "caminho_imagem_final": product.caminho_imagem_final,
            "status": product.status,
        }
    
    def enqueue(self, query_id: str, operation: str, args: Dict = None):
        """Adiciona operação à fila."""
        with QMutexLocker(self._mutex):
            self._queue.append((query_id, operation, args or {}))
    
    def stop(self):
        """Para o worker."""
        self._running = False
        self.wait(2000)


class DatabaseBridge(QObject):
    """
    Bridge principal para acesso ao banco.
    Singleton que gerencia o worker.
    """
    
    products_loaded = Signal(list)        # List[Dict]
    product_updated = Signal(dict)        # Dict
    search_results = Signal(list, int)    # List[Dict], total
    error = Signal(str)                   # error message
    
    _instance: Optional['DatabaseBridge'] = None
    
    def __init__(self):
        super().__init__()
        self._worker = DatabaseWorker()
        self._worker.result_ready.connect(self._on_result)
        self._worker.error_occurred.connect(self._on_error)
        self._worker.start()
        
        self._pending_callbacks: Dict[str, Callable] = {}
    
    @classmethod
    def instance(cls) -> 'DatabaseBridge':
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    def load_products(self, offset: int = 0, limit: int = 50, callback: Callable = None):
        """Carrega produtos paginados."""
        import uuid
        query_id = f"load_{uuid.uuid4().hex[:8]}"
        
        if callback:
            self._pending_callbacks[query_id] = callback
        
        self._worker.enqueue(query_id, "get_products", {"offset": offset, "limit": limit})
    
    def search(self, term: str, offset: int = 0, limit: int = 50, callback: Callable = None):
        """Busca produtos."""
        import uuid
        query_id = f"search_{uuid.uuid4().hex[:8]}"
        
        if callback:
            self._pending_callbacks[query_id] = callback
        
        self._worker.enqueue(query_id, "search_products", {"term": term, "offset": offset, "limit": limit})
    
    def update_product(self, product_id: int, updates: Dict, callback: Callable = None):
        """Atualiza produto."""
        import uuid
        query_id = f"update_{uuid.uuid4().hex[:8]}"
        
        if callback:
            self._pending_callbacks[query_id] = callback
        
        self._worker.enqueue(query_id, "update_product", {"id": product_id, "updates": updates})
    
    def _on_result(self, query_id: str, result: QueryResult):
        """Processa resultado."""
        callback = self._pending_callbacks.pop(query_id, None)
        
        if callback:
            callback(result)
        elif query_id.startswith("load_"):
            self.products_loaded.emit(result.data or [])
        elif query_id.startswith("search_"):
            self.search_results.emit(result.data or [], result.total_count)
        elif query_id.startswith("update_"):
            if result.data:
                self.product_updated.emit(result.data[0])
    
    def _on_error(self, query_id: str, error: str):
        """Processa erro."""
        logger.error(f"Query {query_id} failed: {error}")
        self.error.emit(error)
    
    def shutdown(self):
        """Encerra o worker."""
        self._worker.stop()


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_db_bridge() -> DatabaseBridge:
    """Acesso global ao bridge."""
    return DatabaseBridge.instance()


def load_products_async(offset: int = 0, limit: int = 50):
    """Carrega produtos de forma assíncrona."""
    get_db_bridge().load_products(offset, limit)


def search_products_async(term: str):
    """Busca produtos de forma assíncrona."""
    get_db_bridge().search(term)

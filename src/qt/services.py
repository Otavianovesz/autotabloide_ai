"""
AutoTabloide AI - Database Worker
===================================
Worker thread-safe para operações de banco de dados.
Executa queries SQLAlchemy em thread separada e retorna via Signals.
"""

from PySide6.QtCore import QObject, Signal, Slot, QThread, QMutex
from typing import Optional, List, Dict, Any, Callable
import asyncio
from concurrent.futures import ThreadPoolExecutor


class DatabaseWorker(QThread):
    """
    Worker para operações de banco de dados em background.
    
    Uso:
        worker = DatabaseWorker()
        worker.query_result.connect(on_data_received)
        worker.execute_query("products", "get_all", page=1, limit=50)
    """
    
    # Signals
    query_result = Signal(str, list)  # query_id, data
    query_error = Signal(str, str)  # query_id, error_message
    count_result = Signal(str, int)  # entity, count
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._running = True
        self._queue = []
        self._mutex = QMutex()
        self._executor = ThreadPoolExecutor(max_workers=2)
    
    def run(self):
        """Loop principal do worker."""
        while self._running:
            self._mutex.lock()
            if self._queue:
                task = self._queue.pop(0)
                self._mutex.unlock()
                self._execute_task(task)
            else:
                self._mutex.unlock()
            self.msleep(50)
    
    def stop(self):
        """Para o worker."""
        self._running = False
        self._executor.shutdown(wait=False)
        self.wait()
    
    def _execute_task(self, task: Dict):
        """Executa uma tarefa."""
        query_id = task.get("id", "")
        entity = task.get("entity", "")
        operation = task.get("operation", "")
        params = task.get("params", {})
        
        try:
            result = self._run_query(entity, operation, params)
            self.query_result.emit(query_id, result)
        except Exception as e:
            self.query_error.emit(query_id, str(e))
    
    def _run_query(self, entity: str, operation: str, params: Dict) -> List[Dict]:
        """Executa query no banco."""
        try:
            from src.core.container import get_container
            container = get_container()
            
            if entity == "products":
                repo = container.resolve("ProductRepository")
                return self._query_products(repo, operation, params)
            elif entity == "layouts":
                repo = container.resolve("LayoutRepository")
                return self._query_layouts(repo, operation, params)
            elif entity == "projects":
                repo = container.resolve("ProjectRepository")
                return self._query_projects(repo, operation, params)
            else:
                return []
                
        except Exception as e:
            print(f"[DatabaseWorker] Erro: {e}")
            raise
    
    def _query_products(self, repo, operation: str, params: Dict) -> List[Dict]:
        """Queries de produtos."""
        if operation == "get_all":
            page = params.get("page", 1)
            limit = params.get("limit", 50)
            search = params.get("search", "")
            
            # Executa query async em sync context
            loop = asyncio.new_event_loop()
            try:
                products = loop.run_until_complete(
                    repo.get_paginated(page=page, limit=limit, search=search)
                )
                return [self._product_to_dict(p) for p in products]
            finally:
                loop.close()
        
        elif operation == "count":
            loop = asyncio.new_event_loop()
            try:
                count = loop.run_until_complete(repo.count())
                self.count_result.emit("products", count)
                return []
            finally:
                loop.close()
        
        return []
    
    def _query_layouts(self, repo, operation: str, params: Dict) -> List[Dict]:
        """Queries de layouts."""
        if operation == "get_all":
            loop = asyncio.new_event_loop()
            try:
                layouts = loop.run_until_complete(repo.get_all())
                return [{"id": l.id, "nome": l.nome, "path": l.svg_path} for l in layouts]
            finally:
                loop.close()
        return []
    
    def _query_projects(self, repo, operation: str, params: Dict) -> List[Dict]:
        """Queries de projetos."""
        return []
    
    def _product_to_dict(self, product) -> Dict:
        """Converte produto para dict."""
        return {
            "id": product.id,
            "sku_origem": product.sku_origem,
            "nome_sanitizado": product.nome_sanitizado,
            "marca_normalizada": product.marca_normalizada,
            "preco_venda_atual": float(product.preco_venda_atual or 0),
            "preco_venda_anterior": float(product.preco_venda_anterior or 0),
            "status_qualidade": product.status_qualidade,
            "img_hash_ref": product.img_hash_ref,
            "updated_at": str(product.updated_at) if product.updated_at else None,
        }
    
    # === API Pública ===
    
    def fetch_products(
        self, 
        query_id: str,
        page: int = 1, 
        limit: int = 50,
        search: str = ""
    ):
        """Busca produtos paginados."""
        self._enqueue({
            "id": query_id,
            "entity": "products",
            "operation": "get_all",
            "params": {"page": page, "limit": limit, "search": search}
        })
    
    def count_products(self, query_id: str = "count"):
        """Conta total de produtos."""
        self._enqueue({
            "id": query_id,
            "entity": "products",
            "operation": "count",
            "params": {}
        })
    
    def fetch_layouts(self, query_id: str):
        """Busca todos os layouts."""
        self._enqueue({
            "id": query_id,
            "entity": "layouts",
            "operation": "get_all",
            "params": {}
        })
    
    def _enqueue(self, task: Dict):
        """Adiciona tarefa à fila."""
        self._mutex.lock()
        self._queue.append(task)
        self._mutex.unlock()


class ProductTableModel:
    """
    Model Qt para tabela de produtos com suporte a:
    - Lazy loading
    - Paginação
    - Busca com debounce
    - Cache de dados
    """
    
    # Definido no estoque.py como QAbstractTableModel
    pass


class ServiceConnector(QObject):
    """
    Conecta serviços do backend com a UI Qt.
    
    Centraliza acesso a repositórios e serviços.
    """
    
    # Signals para atualização de UI
    products_updated = Signal()
    layouts_updated = Signal()
    settings_changed = Signal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._container = None
        self._db_worker = None
        self._initialized = False
    
    def initialize(self):
        """Inicializa conexão com backend."""
        if self._initialized:
            return
        
        try:
            from src.core.container import get_container
            self._container = get_container()
            
            # Inicia worker de banco de dados
            self._db_worker = DatabaseWorker()
            self._db_worker.start()
            
            self._initialized = True
            print("[ServiceConnector] Conectado ao backend")
            
        except Exception as e:
            print(f"[ServiceConnector] Erro ao conectar: {e}")
    
    def shutdown(self):
        """Encerra conexões."""
        if self._db_worker:
            self._db_worker.stop()
    
    @property
    def db_worker(self) -> Optional[DatabaseWorker]:
        """Retorna worker de banco de dados."""
        return self._db_worker
    
    def get_service(self, name: str):
        """Obtém serviço do container."""
        if self._container:
            try:
                return self._container.resolve(name)
            except Exception:
                return None
        return None
    
    def get_settings(self) -> Dict:
        """Obtém configurações atuais."""
        settings_service = self.get_service("SettingsService")
        if settings_service:
            return settings_service.get_all()
        return {}
    
    def save_settings(self, key: str, value: Any):
        """Salva configuração."""
        settings_service = self.get_service("SettingsService")
        if settings_service:
            settings_service.set(key, value)
            self.settings_changed.emit(key)

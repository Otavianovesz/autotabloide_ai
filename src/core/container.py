"""
AutoTabloide AI - Container de Injeção de Dependência
======================================================
Padrão Service Locator para gerenciamento de singletons.
Conforme Auditoria Industrial: Desacoplar serviços da UI.
"""

from __future__ import annotations
from typing import TypeVar, Type, Dict, Callable, Any, Optional
from pathlib import Path
import threading

T = TypeVar('T')


class ServiceContainer:
    """
    Container de Injeção de Dependência (Singleton Pattern).
    
    Gerencia instâncias únicas de serviços em toda a aplicação.
    Thread-safe para uso em multiprocessing.
    
    Uso:
        container = ServiceContainer()
        container.register(Database, lambda: Database(path))
        db = container.resolve(Database)
    """
    
    _instance: Optional['ServiceContainer'] = None
    _lock = threading.Lock()
    
    def __new__(cls) -> 'ServiceContainer':
        """Garante singleton do container."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._init_container()
        return cls._instance
    
    def _init_container(self) -> None:
        """Inicializa estruturas internas."""
        self._factories: Dict[Type, Callable[[], Any]] = {}
        self._instances: Dict[Type, Any] = {}
        self._scoped: Dict[str, Dict[Type, Any]] = {}
        self._service_lock = threading.RLock()
    
    def register(
        self, 
        service_type: Type[T], 
        factory: Callable[[], T],
        singleton: bool = True
    ) -> 'ServiceContainer':
        """
        Registra um serviço no container.
        
        Args:
            service_type: Tipo/classe do serviço
            factory: Função que cria a instância
            singleton: Se True, a instância é reutilizada
            
        Returns:
            Self para encadeamento fluente
        """
        with self._service_lock:
            self._factories[service_type] = (factory, singleton)
        return self
    
    def register_instance(
        self, 
        service_type: Type[T], 
        instance: T
    ) -> 'ServiceContainer':
        """
        Registra uma instância existente.
        
        Args:
            service_type: Tipo/classe do serviço
            instance: Instância já criada
            
        Returns:
            Self para encadeamento fluente
        """
        with self._service_lock:
            self._instances[service_type] = instance
        return self
    
    def resolve(self, service_type: Type[T]) -> T:
        """
        Resolve (obtém) um serviço registrado.
        
        Args:
            service_type: Tipo/classe do serviço desejado
            
        Returns:
            Instância do serviço
            
        Raises:
            KeyError: Se o serviço não estiver registrado
        """
        with self._service_lock:
            # 1. Verificar instância já criada
            if service_type in self._instances:
                return self._instances[service_type]
            
            # 2. Verificar factory registrada
            if service_type not in self._factories:
                raise KeyError(
                    f"Serviço '{service_type.__name__}' não registrado. "
                    f"Use container.register() primeiro."
                )
            
            factory, is_singleton = self._factories[service_type]
            instance = factory()
            
            # 3. Cachear se singleton
            if is_singleton:
                self._instances[service_type] = instance
            
            return instance
    
    def try_resolve(self, service_type: Type[T]) -> Optional[T]:
        """
        Tenta resolver um serviço sem lançar exceção.
        
        Args:
            service_type: Tipo/classe do serviço desejado
            
        Returns:
            Instância do serviço ou None se não registrado
        """
        try:
            return self.resolve(service_type)
        except KeyError:
            return None
    
    def is_registered(self, service_type: Type) -> bool:
        """Verifica se um serviço está registrado."""
        with self._service_lock:
            return (
                service_type in self._instances or 
                service_type in self._factories
            )
    
    def clear(self) -> None:
        """Limpa todos os registros (para testes)."""
        with self._service_lock:
            self._factories.clear()
            self._instances.clear()
            self._scoped.clear()
    
    def dispose(self, service_type: Type) -> None:
        """
        Remove e finaliza um serviço específico.
        Chama close() ou dispose() se disponível.
        """
        with self._service_lock:
            if service_type in self._instances:
                instance = self._instances.pop(service_type)
                # Tentar cleanup gracioso
                if hasattr(instance, 'close'):
                    instance.close()
                elif hasattr(instance, 'dispose'):
                    instance.dispose()
                elif hasattr(instance, 'shutdown'):
                    instance.shutdown()


# Instância global do container
_container: Optional[ServiceContainer] = None


def get_container() -> ServiceContainer:
    """
    Obtém o container global.
    
    Returns:
        Instância singleton do ServiceContainer
    """
    global _container
    if _container is None:
        _container = ServiceContainer()
    return _container


def inject(service_type: Type[T]) -> T:
    """
    Atalho para resolver serviços.
    
    Uso:
        db = inject(Database)
        
    Args:
        service_type: Tipo do serviço desejado
        
    Returns:
        Instância do serviço
    """
    return get_container().resolve(service_type)


def register(
    service_type: Type[T], 
    factory: Callable[[], T],
    singleton: bool = True
) -> None:
    """
    Atalho para registrar serviços.
    
    Args:
        service_type: Tipo/classe do serviço
        factory: Função que cria a instância
        singleton: Se True, a instância é reutilizada
    """
    get_container().register(service_type, factory, singleton)


def register_instance(service_type: Type[T], instance: T) -> None:
    """
    Atalho para registrar instância existente.
    
    Args:
        service_type: Tipo/classe do serviço
        instance: Instância já criada
    """
    get_container().register_instance(service_type, instance)


# ==============================================================================
# BOOTSTRAP DE SERVIÇOS (Passo 11 do Checklist 100)
# ==============================================================================

async def bootstrap_services() -> None:
    """
    Registra todos os serviços padrão no container.
    Deve ser chamado uma vez no startup da aplicação.
    
    Serviços registrados:
    - SettingsService: Configurações centralizadas
    - EventBus: Sistema Pub/Sub
    - ProjectManager: Gestão de projetos
    """
    from src.core.settings_service import SettingsService, get_settings
    from src.core.event_bus import event_bus
    from src.core.project_manager import ProjectManager
    
    container = get_container()
    
    # SettingsService (singleton inicializado)
    settings = await get_settings()
    container.register_instance(SettingsService, settings)
    
    # EventBus (já é singleton global)
    from src.core.event_bus import EventBus
    container.register_instance(EventBus, event_bus)
    
    # ProjectManager (factory)
    container.register(ProjectManager, lambda: ProjectManager(), singleton=True)


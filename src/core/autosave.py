"""
AutoTabloide AI - Autosave Service
===================================
Implementação conforme Vol. V, Cap. 3.2.

Salva projetos automaticamente com debounce de 3 segundos.
Previne perda de trabalho sem sobrecarregar o disco.
"""

import asyncio
import logging
from typing import Optional, Callable, Any
from datetime import datetime
from dataclasses import dataclass

logger = logging.getLogger("Autosave")


@dataclass
class AutosaveConfig:
    """Configuração do autosave."""
    debounce_seconds: float = 3.0       # Tempo de espera antes de salvar
    max_interval_seconds: float = 60.0  # Força save após N segundos mesmo sem debounce
    enabled: bool = True


class DebouncedAutosave:
    """
    Serviço de Autosave com Debounce.
    
    Funciona assim:
    1. A cada mudança, chama mark_dirty()
    2. Um timer de 3s é iniciado/reiniciado
    3. Após 3s sem mudanças, salva automaticamente
    4. Se o timer for reiniciado antes de expirar, tudo recomeça
    5. Failsafe: Após 60s da última mudança, salva mesmo que haja edições
    
    Ref: Vol. V, Cap. 3.2
    """
    
    def __init__(
        self,
        save_callback: Callable[[], Any],
        config: AutosaveConfig = None,
        on_status_change: Callable[[bool], None] = None
    ):
        """
        Args:
            save_callback: Função async ou sync a chamar para salvar
            config: Configuração do autosave
            on_status_change: Callback quando status dirty muda (para UI)
        """
        self.save_callback = save_callback
        self.config = config or AutosaveConfig()
        self.on_status_change = on_status_change
        
        self._is_dirty = False
        self._last_change_time: Optional[datetime] = None
        self._debounce_task: Optional[asyncio.Task] = None
        self._failsafe_task: Optional[asyncio.Task] = None
        self._is_saving = False
        self._save_count = 0
    
    @property
    def is_dirty(self) -> bool:
        return self._is_dirty
    
    @property
    def save_count(self) -> int:
        return self._save_count
    
    def mark_dirty(self):
        """
        Marca que há alterações não salvas.
        Inicia ou reinicia o timer de debounce.
        """
        if not self.config.enabled:
            return
        
        was_dirty = self._is_dirty
        self._is_dirty = True
        self._last_change_time = datetime.now()
        
        # Notifica UI se estado mudou
        if not was_dirty and self.on_status_change:
            self.on_status_change(True)
        
        # Cancela timer anterior e inicia novo
        if self._debounce_task and not self._debounce_task.done():
            self._debounce_task.cancel()
        
        self._debounce_task = asyncio.create_task(
            self._debounce_timer()
        )
        
        # Inicia failsafe se não existir
        if self._failsafe_task is None or self._failsafe_task.done():
            self._failsafe_task = asyncio.create_task(
                self._failsafe_timer()
            )
    
    async def _debounce_timer(self):
        """Timer de debounce - salva após N segundos sem mudanças."""
        try:
            await asyncio.sleep(self.config.debounce_seconds)
            await self._execute_save("debounce")
        except asyncio.CancelledError:
            # Timer cancelado por nova mudança - normal
            pass
    
    async def _failsafe_timer(self):
        """Timer de failsafe - salva mesmo durante edição contínua."""
        try:
            await asyncio.sleep(self.config.max_interval_seconds)
            if self._is_dirty:
                await self._execute_save("failsafe")
        except asyncio.CancelledError:
            pass
    
    async def _execute_save(self, trigger: str):
        """Executa o save de fato."""
        if self._is_saving:
            return
        
        self._is_saving = True
        
        try:
            logger.debug(f"Autosave iniciado (trigger: {trigger})")
            
            # Chama callback (suporta sync e async)
            if asyncio.iscoroutinefunction(self.save_callback):
                await self.save_callback()
            else:
                self.save_callback()
            
            self._save_count += 1
            self._is_dirty = False
            
            # Notifica UI
            if self.on_status_change:
                self.on_status_change(False)
            
            logger.info(f"Autosave #{self._save_count} concluído ({trigger})")
            
        except Exception as e:
            logger.error(f"Erro no autosave: {e}")
        finally:
            self._is_saving = False
            
            # Cancela failsafe após save bem-sucedido
            if self._failsafe_task and not self._failsafe_task.done():
                self._failsafe_task.cancel()
    
    async def force_save(self):
        """Força um save imediato, ignorando debounce."""
        if self._debounce_task and not self._debounce_task.done():
            self._debounce_task.cancel()
        
        await self._execute_save("forced")
    
    def cancel(self):
        """Cancela todos os timers pendentes."""
        if self._debounce_task and not self._debounce_task.done():
            self._debounce_task.cancel()
        if self._failsafe_task and not self._failsafe_task.done():
            self._failsafe_task.cancel()
    
    def reset(self):
        """Reseta estado (após carregar novo projeto, por ex.)."""
        self.cancel()
        self._is_dirty = False
        self._last_change_time = None
        
        if self.on_status_change:
            self.on_status_change(False)


class AutosaveManager:
    """
    Gerenciador global de autosave para múltiplos projetos.
    """
    
    def __init__(self):
        self._instances: dict[str, DebouncedAutosave] = {}
    
    def register(
        self,
        project_id: str,
        save_callback: Callable,
        config: AutosaveConfig = None,
        on_status_change: Callable[[bool], None] = None
    ) -> DebouncedAutosave:
        """Registra um novo projeto para autosave."""
        if project_id in self._instances:
            self._instances[project_id].cancel()
        
        instance = DebouncedAutosave(
            save_callback=save_callback,
            config=config,
            on_status_change=on_status_change
        )
        
        self._instances[project_id] = instance
        return instance
    
    def get(self, project_id: str) -> Optional[DebouncedAutosave]:
        """Obtém instância de autosave para um projeto."""
        return self._instances.get(project_id)
    
    def mark_dirty(self, project_id: str):
        """Marca um projeto como dirty."""
        if instance := self._instances.get(project_id):
            instance.mark_dirty()
    
    async def force_save_all(self):
        """Força save de todos os projetos dirty."""
        for instance in self._instances.values():
            if instance.is_dirty:
                await instance.force_save()
    
    def unregister(self, project_id: str):
        """Remove um projeto do gerenciamento."""
        if instance := self._instances.get(project_id):
            instance.cancel()
            del self._instances[project_id]
    
    def cancel_all(self):
        """Cancela todos os timers."""
        for instance in self._instances.values():
            instance.cancel()


# Singleton global
_autosave_manager: Optional[AutosaveManager] = None


def get_autosave_manager() -> AutosaveManager:
    """Obtém instância singleton do gerenciador de autosave."""
    global _autosave_manager
    if _autosave_manager is None:
        _autosave_manager = AutosaveManager()
    return _autosave_manager

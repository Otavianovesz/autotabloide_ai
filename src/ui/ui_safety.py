"""
AutoTabloide AI - UI Safety Utilities
========================================
Utilitários de segurança para UI.
Passos 14, 17, 43 do Checklist v2.

Funcionalidades:
- Spinner com desabilitar botões (14)
- Cleanup de eventos on unmount (17)
- Sanitização de inputs (43)
"""

import re
import asyncio
from typing import Optional, Callable, List, Any
import flet as ft

from src.core.logging_config import get_logger

logger = get_logger("UISafety")


class SafeButton(ft.ElevatedButton):
    """
    Botão que desabilita durante operação assíncrona.
    Passo 14 do Checklist v2 - Feedback visual de loading.
    
    Evita cliques múltiplos durante processamento.
    """
    
    def __init__(
        self,
        text: str,
        on_click_async: Callable,
        loading_text: str = "Aguarde...",
        **kwargs
    ):
        """
        Args:
            text: Texto do botão
            on_click_async: Callback assíncrono
            loading_text: Texto durante loading
        """
        self._original_text = text
        self._loading_text = loading_text
        self._on_click_async = on_click_async
        self._is_loading = False
        
        super().__init__(
            text=text,
            on_click=self._handle_click,
            **kwargs
        )
    
    def _handle_click(self, e) -> None:
        """Processa clique com proteção."""
        if self._is_loading:
            return
        
        self._start_loading()
        
        # Executa callback async
        if self.page:
            self.page.run_task(self._execute_async)
    
    async def _execute_async(self) -> None:
        """Executa callback e restaura estado."""
        try:
            await self._on_click_async()
        except Exception as ex:
            logger.error(f"Erro no callback: {ex}")
        finally:
            self._stop_loading()
    
    def _start_loading(self) -> None:
        """Inicia estado de loading."""
        self._is_loading = True
        self.text = self._loading_text
        self.disabled = True
        self.update()
    
    def _stop_loading(self) -> None:
        """Para estado de loading."""
        self._is_loading = False
        self.text = self._original_text
        self.disabled = False
        self.update()


class EventCleanupMixin:
    """
    Mixin para cleanup automático de eventos.
    Passo 17 do Checklist v2 - Limpeza de eventos on unmount.
    
    Uso:
        class MyView(EventCleanupMixin, ft.Column):
            def did_mount(self):
                self.register_event(self.page, "on_keyboard_event", self._handle_keyboard)
            
            # Cleanup é automático no did_unmount
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._registered_events: List[tuple] = []
    
    def register_event(self, target: Any, event_name: str, handler: Callable) -> None:
        """
        Registra evento para cleanup automático.
        
        Args:
            target: Objeto alvo (ex: self.page)
            event_name: Nome do evento (ex: "on_keyboard_event")
            handler: Função handler
        """
        # Registra no alvo
        if hasattr(target, event_name):
            setattr(target, event_name, handler)
            self._registered_events.append((target, event_name, handler))
            logger.debug(f"Evento registrado: {event_name}")
    
    def unregister_all_events(self) -> None:
        """Remove todos os eventos registrados."""
        for target, event_name, handler in self._registered_events:
            try:
                if hasattr(target, event_name):
                    setattr(target, event_name, None)
                    logger.debug(f"Evento removido: {event_name}")
            except Exception as e:
                logger.warning(f"Erro ao remover evento {event_name}: {e}")
        
        self._registered_events.clear()
    
    def did_unmount(self) -> None:
        """Chamado quando componente é desmontado."""
        self.unregister_all_events()
        
        # Chama super se existir
        if hasattr(super(), 'did_unmount'):
            super().did_unmount()


def sanitize_project_name(name: str) -> str:
    """
    Sanitiza nome de projeto para uso seguro em arquivos.
    Passo 43 do Checklist v2 - Sanitização de inputs.
    
    Args:
        name: Nome original
        
    Returns:
        Nome sanitizado
    """
    if not name:
        return "projeto_sem_nome"
    
    # Remove caracteres inválidos para Windows/Linux
    invalid_chars = r'[<>:"/\\|?*\x00-\x1f]'
    sanitized = re.sub(invalid_chars, '_', name)
    
    # Remove espaços extras
    sanitized = ' '.join(sanitized.split())
    
    # Limita tamanho
    if len(sanitized) > 100:
        sanitized = sanitized[:100]
    
    # Evita nomes reservados do Windows
    reserved = {
        'CON', 'PRN', 'AUX', 'NUL',
        'COM1', 'COM2', 'COM3', 'COM4', 'COM5', 'COM6', 'COM7', 'COM8', 'COM9',
        'LPT1', 'LPT2', 'LPT3', 'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9'
    }
    
    if sanitized.upper() in reserved:
        sanitized = f"_{sanitized}"
    
    return sanitized.strip() or "projeto_sem_nome"


def validate_price(value: str) -> Optional[float]:
    """
    Valida e converte string de preço para float.
    Passo 44 do Checklist v2 - Validação de preço negativo.
    
    Args:
        value: String do preço
        
    Returns:
        Float ou None se inválido
    """
    if not value:
        return None
    
    try:
        # Remove formatação comum
        cleaned = value.replace('R$', '').replace(' ', '')
        
        # Detecta formato brasileiro (1.234,56) vs americano (1,234.56)
        if ',' in cleaned and '.' in cleaned:
            if cleaned.rindex(',') > cleaned.rindex('.'):
                # Formato brasileiro
                cleaned = cleaned.replace('.', '').replace(',', '.')
            else:
                # Formato americano
                cleaned = cleaned.replace(',', '')
        elif ',' in cleaned:
            cleaned = cleaned.replace(',', '.')
        
        price = float(cleaned)
        
        # Validação: preço não pode ser negativo
        if price < 0:
            logger.warning(f"Preço negativo rejeitado: {price}")
            return None
        
        return price
        
    except (ValueError, AttributeError):
        logger.warning(f"Preço inválido: {value}")
        return None

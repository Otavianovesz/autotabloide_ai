"""
AutoTabloide AI - Atalhos de Teclado Globais
=============================================
Conforme Auditoria Industrial: Produtividade via atalhos.
Mapeamento completo de teclas para operações frequentes.
"""

from __future__ import annotations
from typing import Callable, Dict, List, Optional, TYPE_CHECKING
from dataclasses import dataclass
from enum import Enum, auto
import logging

if TYPE_CHECKING:
    import flet as ft

logger = logging.getLogger("AutoTabloide.Keyboard")


class KeyModifier(Enum):
    """Modificadores de tecla."""
    NONE = auto()
    CTRL = auto()
    SHIFT = auto()
    ALT = auto()
    CTRL_SHIFT = auto()
    CTRL_ALT = auto()


@dataclass
class KeyBinding:
    """Definição de atalho de teclado."""
    key: str
    modifier: KeyModifier
    action: str
    description: str
    handler: Optional[Callable] = None
    enabled: bool = True


class KeyboardManager:
    """
    Gerenciador de Atalhos de Teclado.
    
    Registra atalhos globais e por view, processa eventos de teclado.
    
    Atalhos Padrão (Vol. VI):
    - Ctrl+S: Salvar projeto
    - Ctrl+Z: Desfazer
    - Ctrl+Shift+Z: Refazer
    - Ctrl+N: Novo projeto
    - Ctrl+O: Abrir projeto
    - Ctrl+E: Exportar PDF
    - Del: Remover item selecionado
    - F5: Atualizar dados
    - Esc: Cancelar operação / Fechar modal
    """
    
    def __init__(self):
        self._global_bindings: Dict[str, KeyBinding] = {}
        self._view_bindings: Dict[str, Dict[str, KeyBinding]] = {}
        self._current_view: Optional[str] = None
        self._register_defaults()
    
    def _register_defaults(self) -> None:
        """Registra atalhos padrão do sistema."""
        defaults = [
            # Arquivo
            KeyBinding("s", KeyModifier.CTRL, "save", "Salvar projeto"),
            KeyBinding("n", KeyModifier.CTRL, "new", "Novo projeto"),
            KeyBinding("o", KeyModifier.CTRL, "open", "Abrir projeto"),
            KeyBinding("e", KeyModifier.CTRL, "export", "Exportar PDF"),
            KeyBinding("w", KeyModifier.CTRL, "close", "Fechar projeto"),
            
            # Edição
            KeyBinding("z", KeyModifier.CTRL, "undo", "Desfazer"),
            KeyBinding("z", KeyModifier.CTRL_SHIFT, "redo", "Refazer"),
            KeyBinding("y", KeyModifier.CTRL, "redo_alt", "Refazer (alternativo)"),
            KeyBinding("a", KeyModifier.CTRL, "select_all", "Selecionar tudo"),
            KeyBinding("Delete", KeyModifier.NONE, "delete", "Remover selecionado"),
            KeyBinding("Backspace", KeyModifier.NONE, "delete_alt", "Remover (alternativo)"),
            
            # Navegação
            KeyBinding("1", KeyModifier.CTRL, "nav_dashboard", "Ir para Dashboard"),
            KeyBinding("2", KeyModifier.CTRL, "nav_estoque", "Ir para Estoque"),
            KeyBinding("3", KeyModifier.CTRL, "nav_atelier", "Ir para Ateliê"),
            KeyBinding("4", KeyModifier.CTRL, "nav_factory", "Ir para Fábrica"),
            KeyBinding("5", KeyModifier.CTRL, "nav_cofre", "Ir para Cofre"),
            KeyBinding("6", KeyModifier.CTRL, "nav_settings", "Ir para Config"),
            
            # Ações
            KeyBinding("F5", KeyModifier.NONE, "refresh", "Atualizar dados"),
            KeyBinding("Escape", KeyModifier.NONE, "cancel", "Cancelar / Fechar"),
            KeyBinding("Enter", KeyModifier.CTRL, "confirm", "Confirmar ação"),
            KeyBinding("f", KeyModifier.CTRL, "search", "Buscar"),
            KeyBinding("p", KeyModifier.CTRL, "print", "Imprimir"),
            
            # Zoom (para canvas)
            KeyBinding("+", KeyModifier.CTRL, "zoom_in", "Aumentar zoom"),
            KeyBinding("-", KeyModifier.CTRL, "zoom_out", "Diminuir zoom"),
            KeyBinding("0", KeyModifier.CTRL, "zoom_reset", "Resetar zoom"),
        ]
        
        for binding in defaults:
            key = self._make_key(binding.key, binding.modifier)
            self._global_bindings[key] = binding
    
    def _make_key(self, key: str, modifier: KeyModifier) -> str:
        """Cria chave única para o binding."""
        return f"{modifier.name}+{key.lower()}"
    
    def register(
        self,
        key: str,
        modifier: KeyModifier,
        action: str,
        description: str,
        handler: Optional[Callable] = None,
        view: Optional[str] = None
    ) -> None:
        """
        Registra novo atalho.
        
        Args:
            key: Tecla (ex: "s", "Delete", "F5")
            modifier: Modificador (Ctrl, Shift, etc)
            action: Nome da ação
            description: Descrição para help
            handler: Função a executar
            view: Se especificado, atalho só funciona nesta view
        """
        binding = KeyBinding(key, modifier, action, description, handler)
        binding_key = self._make_key(key, modifier)
        
        if view:
            if view not in self._view_bindings:
                self._view_bindings[view] = {}
            self._view_bindings[view][binding_key] = binding
        else:
            self._global_bindings[binding_key] = binding
    
    def set_handler(self, action: str, handler: Callable) -> None:
        """
        Define handler para uma ação existente.
        
        Args:
            action: Nome da ação
            handler: Função a executar
        """
        for binding in self._global_bindings.values():
            if binding.action == action:
                binding.handler = handler
                return
        
        for view_bindings in self._view_bindings.values():
            for binding in view_bindings.values():
                if binding.action == action:
                    binding.handler = handler
                    return
    
    def set_current_view(self, view_name: str) -> None:
        """Define view atual para atalhos contextuais."""
        self._current_view = view_name
    
    def handle_key_event(self, e) -> bool:
        """
        Processa evento de teclado do Flet.
        
        Args:
            e: Evento de teclado (page.on_keyboard_event)
            
        Returns:
            True se evento foi tratado
        """
        if not e.key:
            return False
        
        # Determina modificador
        modifier = KeyModifier.NONE
        if e.ctrl and e.shift:
            modifier = KeyModifier.CTRL_SHIFT
        elif e.ctrl and e.alt:
            modifier = KeyModifier.CTRL_ALT
        elif e.ctrl:
            modifier = KeyModifier.CTRL
        elif e.shift:
            modifier = KeyModifier.SHIFT
        elif e.alt:
            modifier = KeyModifier.ALT
        
        binding_key = self._make_key(e.key, modifier)
        
        # 1. Tenta binding da view atual
        if self._current_view and self._current_view in self._view_bindings:
            binding = self._view_bindings[self._current_view].get(binding_key)
            if binding and binding.enabled and binding.handler:
                logger.debug(f"Keyboard: {binding.action} (view: {self._current_view})")
                binding.handler()
                return True
        
        # 2. Tenta binding global
        binding = self._global_bindings.get(binding_key)
        if binding and binding.enabled and binding.handler:
            logger.debug(f"Keyboard: {binding.action} (global)")
            binding.handler()
            return True
        
        return False
    
    def get_all_bindings(self) -> List[KeyBinding]:
        """Retorna todos os atalhos para exibição em help."""
        bindings = list(self._global_bindings.values())
        for view_bindings in self._view_bindings.values():
            bindings.extend(view_bindings.values())
        return bindings
    
    def get_help_text(self) -> str:
        """Gera texto de ajuda com todos os atalhos."""
        lines = ["Atalhos de Teclado:", "=" * 40]
        
        categories = {
            "Arquivo": ["save", "new", "open", "export", "close", "print"],
            "Edição": ["undo", "redo", "redo_alt", "select_all", "delete", "delete_alt"],
            "Navegação": ["nav_dashboard", "nav_estoque", "nav_atelier", 
                         "nav_factory", "nav_cofre", "nav_settings"],
            "Ações": ["refresh", "cancel", "confirm", "search"],
            "Zoom": ["zoom_in", "zoom_out", "zoom_reset"],
        }
        
        for category, actions in categories.items():
            lines.append(f"\n{category}:")
            for binding in self._global_bindings.values():
                if binding.action in actions:
                    mod = "" if binding.modifier == KeyModifier.NONE else f"{binding.modifier.name}+"
                    lines.append(f"  {mod}{binding.key}: {binding.description}")
        
        return "\n".join(lines)


# Instância global
_keyboard: Optional[KeyboardManager] = None


def get_keyboard_manager() -> KeyboardManager:
    """Obtém o gerenciador de teclado global."""
    global _keyboard
    if _keyboard is None:
        _keyboard = KeyboardManager()
    return _keyboard


def setup_keyboard_handlers(page, handlers: Dict[str, Callable]) -> None:
    """
    Configura handlers de teclado para uma página Flet.
    
    Args:
        page: Página Flet
        handlers: Dict mapeando action -> função
    """
    km = get_keyboard_manager()
    
    # Registra handlers
    for action, handler in handlers.items():
        km.set_handler(action, handler)
    
    # Conecta ao evento do Flet
    def on_keyboard(e):
        km.handle_key_event(e)
    
    page.on_keyboard_event = on_keyboard

"""
AutoTabloide AI - Keyboard Shortcuts
======================================
Sistema de atalhos de teclado para produtividade.
PROTOCOLO DE RETIFICAÇÃO: Passo 78 (Atalhos de teclado).

Referência cruzada com Vol. VI, Cap. 1 - Interface.
"""

import logging
from typing import Dict, Callable, Optional, Any
from dataclasses import dataclass
import flet as ft

logger = logging.getLogger("KeyboardShortcuts")


@dataclass
class ShortcutAction:
    """Define uma ação de atalho."""
    key: str
    modifiers: list  # ['ctrl', 'shift', 'alt']
    action: str  # Nome da ação
    description: str
    callback: Optional[Callable] = None


class KeyboardShortcutManager:
    """
    Gerenciador centralizado de atalhos de teclado.
    
    PASSO 78: Atalhos completos para todas as ações principais.
    """
    
    # Atalhos padrão do sistema
    DEFAULT_SHORTCUTS: Dict[str, ShortcutAction] = {
        # Navegação
        "nav_estoque": ShortcutAction("1", ["ctrl"], "nav_estoque", "Ir para Estoque"),
        "nav_layouts": ShortcutAction("2", ["ctrl"], "nav_layouts", "Ir para Layouts"),
        "nav_atelier": ShortcutAction("3", ["ctrl"], "nav_atelier", "Ir para Ateliê"),
        "nav_projetos": ShortcutAction("4", ["ctrl"], "nav_projetos", "Ir para Projetos"),
        
        # Ações de Arquivo
        "save": ShortcutAction("s", ["ctrl"], "save", "Salvar"),
        "save_as": ShortcutAction("s", ["ctrl", "shift"], "save_as", "Salvar Como"),
        "open": ShortcutAction("o", ["ctrl"], "open", "Abrir Projeto"),
        "new": ShortcutAction("n", ["ctrl"], "new", "Novo Projeto"),
        "export_pdf": ShortcutAction("e", ["ctrl"], "export_pdf", "Exportar PDF"),
        "print": ShortcutAction("p", ["ctrl"], "print", "Imprimir"),
        
        # Edição
        "undo": ShortcutAction("z", ["ctrl"], "undo", "Desfazer"),
        "redo": ShortcutAction("y", ["ctrl"], "redo", "Refazer"),
        "cut": ShortcutAction("x", ["ctrl"], "cut", "Recortar"),
        "copy": ShortcutAction("c", ["ctrl"], "copy", "Copiar"),
        "paste": ShortcutAction("v", ["ctrl"], "paste", "Colar"),
        "select_all": ShortcutAction("a", ["ctrl"], "select_all", "Selecionar Tudo"),
        "delete": ShortcutAction("Delete", [], "delete", "Deletar Seleção"),
        
        # Busca
        "search": ShortcutAction("f", ["ctrl"], "search", "Buscar"),
        "search_next": ShortcutAction("g", ["ctrl"], "search_next", "Próximo Resultado"),
        "search_prev": ShortcutAction("g", ["ctrl", "shift"], "search_prev", "Resultado Anterior"),
        
        # Ateliê
        "clear_slot": ShortcutAction("Delete", [], "clear_slot", "Limpar Slot"),
        "zoom_in": ShortcutAction("+", ["ctrl"], "zoom_in", "Aumentar Zoom"),
        "zoom_out": ShortcutAction("-", ["ctrl"], "zoom_out", "Diminuir Zoom"),
        "zoom_reset": ShortcutAction("0", ["ctrl"], "zoom_reset", "Zoom 100%"),
        "toggle_grid": ShortcutAction("g", ["ctrl"], "toggle_grid", "Mostrar/Ocultar Grid"),
        
        # Sistema
        "settings": ShortcutAction(",", ["ctrl"], "settings", "Configurações"),
        "help": ShortcutAction("F1", [], "help", "Ajuda"),
        "quit": ShortcutAction("q", ["ctrl"], "quit", "Sair"),
        "fullscreen": ShortcutAction("F11", [], "fullscreen", "Tela Cheia"),
        "refresh": ShortcutAction("F5", [], "refresh", "Atualizar"),
        
        # Estoque
        "import": ShortcutAction("i", ["ctrl"], "import", "Importar Planilha"),
        "sync": ShortcutAction("r", ["ctrl"], "sync", "Sincronizar IA"),
        "filter": ShortcutAction("l", ["ctrl"], "filter", "Filtrar Lista"),
    }
    
    def __init__(self):
        self.shortcuts = dict(self.DEFAULT_SHORTCUTS)
        self.callbacks: Dict[str, Callable] = {}
        self._enabled = True
    
    def register_callback(self, action: str, callback: Callable) -> None:
        """
        Registra callback para uma ação.
        
        Args:
            action: Nome da ação (ex: 'save', 'undo')
            callback: Função a ser chamada
        """
        self.callbacks[action] = callback
        logger.debug(f"Callback registrado para: {action}")
    
    def unregister_callback(self, action: str) -> None:
        """Remove callback de uma ação."""
        if action in self.callbacks:
            del self.callbacks[action]
    
    def on_keyboard_event(self, e: ft.KeyboardEvent) -> bool:
        """
        Processa evento de teclado.
        
        Args:
            e: Evento do Flet
            
        Returns:
            True se evento foi consumido
        """
        if not self._enabled:
            return False
        
        # Constrói lista de modifiers
        modifiers = []
        if e.ctrl:
            modifiers.append("ctrl")
        if e.shift:
            modifiers.append("shift")
        if e.alt:
            modifiers.append("alt")
        
        key = e.key.lower() if len(e.key) == 1 else e.key
        
        # Busca shortcut correspondente
        for shortcut in self.shortcuts.values():
            if self._matches(shortcut, key, modifiers):
                return self._execute(shortcut.action)
        
        return False
    
    def _matches(
        self,
        shortcut: ShortcutAction,
        key: str,
        modifiers: list
    ) -> bool:
        """Verifica se tecla pressionada corresponde ao atalho."""
        if shortcut.key.lower() != key.lower():
            return False
        
        return sorted(shortcut.modifiers) == sorted(modifiers)
    
    def _execute(self, action: str) -> bool:
        """Executa callback de uma ação."""
        if action in self.callbacks:
            try:
                self.callbacks[action]()
                logger.debug(f"Ação executada: {action}")
                return True
            except Exception as e:
                logger.error(f"Erro ao executar {action}: {e}")
        
        return False
    
    def enable(self) -> None:
        """Habilita processamento de atalhos."""
        self._enabled = True
    
    def disable(self) -> None:
        """Desabilita processamento de atalhos (durante edição de texto)."""
        self._enabled = False
    
    def get_shortcut_text(self, action: str) -> str:
        """
        Retorna texto legível do atalho.
        
        Args:
            action: Nome da ação
            
        Returns:
            Texto como "Ctrl+S"
        """
        if action not in self.shortcuts:
            return ""
        
        shortcut = self.shortcuts[action]
        parts = []
        
        for mod in shortcut.modifiers:
            parts.append(mod.capitalize())
        
        parts.append(shortcut.key.upper())
        
        return "+".join(parts)
    
    def get_all_shortcuts(self) -> Dict[str, str]:
        """Retorna dict de ação -> descrição com atalho."""
        result = {}
        
        for action, shortcut in self.shortcuts.items():
            key_text = self.get_shortcut_text(action)
            result[action] = f"{shortcut.description} ({key_text})"
        
        return result
    
    def customize_shortcut(
        self,
        action: str,
        key: str,
        modifiers: list
    ) -> bool:
        """
        Personaliza um atalho.
        
        Args:
            action: Nome da ação
            key: Nova tecla
            modifiers: Novos modificadores
            
        Returns:
            True se personalizado com sucesso
        """
        if action not in self.shortcuts:
            return False
        
        # Verificar conflito
        for other_action, shortcut in self.shortcuts.items():
            if other_action != action:
                if shortcut.key == key and shortcut.modifiers == modifiers:
                    logger.warning(f"Conflito de atalho com: {other_action}")
                    return False
        
        old_shortcut = self.shortcuts[action]
        self.shortcuts[action] = ShortcutAction(
            key=key,
            modifiers=modifiers,
            action=action,
            description=old_shortcut.description,
            callback=old_shortcut.callback
        )
        
        return True


# ==============================================================================
# INSTÂNCIA GLOBAL
# ==============================================================================

_keyboard_manager: Optional[KeyboardShortcutManager] = None


def get_keyboard_manager() -> KeyboardShortcutManager:
    """Retorna instância global do gerenciador."""
    global _keyboard_manager
    
    if _keyboard_manager is None:
        _keyboard_manager = KeyboardShortcutManager()
    
    return _keyboard_manager


def setup_keyboard_shortcuts(page: ft.Page, callbacks: Dict[str, Callable]) -> None:
    """
    Configura atalhos de teclado para uma página Flet.
    
    Args:
        page: Página Flet
        callbacks: Dict de action -> callback
    """
    manager = get_keyboard_manager()
    
    # Registra callbacks
    for action, callback in callbacks.items():
        manager.register_callback(action, callback)
    
    # Conecta evento de teclado
    def on_keyboard(e: ft.KeyboardEvent):
        manager.on_keyboard_event(e)
    
    page.on_keyboard_event = on_keyboard
    
    logger.info(f"Atalhos de teclado configurados: {len(callbacks)} ações")

"""
AutoTabloide AI - Application State Manager
=============================================
Gerencia persistência de estado da aplicação:
- Geometria da janela
- Estado dos widgets
- Configurações do usuário
"""

import json
from pathlib import Path
from typing import Optional, Dict, Any

from PySide6.QtCore import QSettings, QByteArray
from PySide6.QtWidgets import QMainWindow


class AppStateManager:
    """
    Gerencia persistência de estado da aplicação.
    
    Uso:
        state = AppStateManager()
        state.save_window_geometry(main_window)
        state.restore_window_geometry(main_window)
    """
    
    APP_NAME = "AutoTabloide AI"
    ORG_NAME = "AutoTabloide"
    
    def __init__(self):
        self.settings = QSettings(self.ORG_NAME, self.APP_NAME)
    
    # === Window Geometry ===
    
    def save_window_geometry(self, window: QMainWindow) -> None:
        """Salva geometria e estado da janela."""
        self.settings.setValue("window/geometry", window.saveGeometry())
        self.settings.setValue("window/state", window.saveState())
        self.settings.setValue("window/maximized", window.isMaximized())
    
    def restore_window_geometry(self, window: QMainWindow) -> bool:
        """
        Restaura geometria e estado da janela.
        
        Returns:
            True se restaurou com sucesso
        """
        geometry = self.settings.value("window/geometry")
        state = self.settings.value("window/state")
        maximized = self.settings.value("window/maximized", False, type=bool)
        
        if geometry:
            window.restoreGeometry(geometry)
        if state:
            window.restoreState(state)
        if maximized:
            window.showMaximized()
            return True
        
        return geometry is not None
    
    # === Recent Files ===
    
    def get_recent_files(self) -> list:
        """Retorna lista de arquivos recentes."""
        return self.settings.value("files/recent", [], type=list)
    
    def add_recent_file(self, file_path: str) -> None:
        """Adiciona arquivo à lista de recentes."""
        recent = self.get_recent_files()
        
        if file_path in recent:
            recent.remove(file_path)
        
        recent.insert(0, file_path)
        recent = recent[:10]  # Limita a 10
        
        self.settings.setValue("files/recent", recent)
    
    def clear_recent_files(self) -> None:
        """Limpa lista de arquivos recentes."""
        self.settings.setValue("files/recent", [])
    
    # === Last Used Layout ===
    
    def get_last_layout(self) -> Optional[str]:
        """Retorna último layout usado."""
        return self.settings.value("layout/last", None)
    
    def set_last_layout(self, layout_path: str) -> None:
        """Define último layout usado."""
        self.settings.setValue("layout/last", layout_path)
    
    # === Sidebar State ===
    
    def get_last_view_index(self) -> int:
        """Retorna índice da última view aberta."""
        return self.settings.value("sidebar/last_view", 0, type=int)
    
    def set_last_view_index(self, index: int) -> None:
        """Define última view aberta."""
        self.settings.setValue("sidebar/last_view", index)
    
    # === Custom Settings ===
    
    def get_custom_setting(self, key: str, default: Any = None) -> Any:
        """Retorna configuração customizada."""
        return self.settings.value(f"custom/{key}", default)
    
    def set_custom_setting(self, key: str, value: Any) -> None:
        """Define configuração customizada."""
        self.settings.setValue(f"custom/{key}", value)
    
    # === Theme ===
    
    def get_theme(self) -> str:
        """Retorna tema atual."""
        return self.settings.value("appearance/theme", "dark")
    
    def set_theme(self, theme: str) -> None:
        """Define tema."""
        self.settings.setValue("appearance/theme", theme)


class ProjectState:
    """
    Estado de um projeto (Ateliê).
    Persistido em JSON.
    """
    
    def __init__(self, project_path: Optional[Path] = None):
        self.project_path = project_path
        self.layout_path: Optional[str] = None
        self.slots_data: Dict[int, Dict] = {}
        self.metadata: Dict[str, Any] = {}
        self.is_modified = False
    
    def set_slot_data(self, slot_index: int, product: Dict) -> None:
        """Define dados de um slot."""
        self.slots_data[slot_index] = product
        self.is_modified = True
    
    def clear_slot(self, slot_index: int) -> None:
        """Limpa um slot."""
        if slot_index in self.slots_data:
            del self.slots_data[slot_index]
            self.is_modified = True
    
    def clear_all(self) -> None:
        """Limpa todos os slots."""
        self.slots_data.clear()
        self.is_modified = True
    
    def to_dict(self) -> Dict:
        """Converte para dicionário."""
        return {
            "layout_path": self.layout_path,
            "slots_data": self.slots_data,
            "metadata": self.metadata,
        }
    
    @classmethod
    def from_dict(cls, data: Dict, path: Optional[Path] = None) -> "ProjectState":
        """Cria a partir de dicionário."""
        state = cls(path)
        state.layout_path = data.get("layout_path")
        state.slots_data = data.get("slots_data", {})
        state.metadata = data.get("metadata", {})
        return state
    
    def save(self, path: Optional[Path] = None) -> bool:
        """Salva projeto em arquivo JSON."""
        save_path = path or self.project_path
        if not save_path:
            return False
        
        try:
            with open(save_path, 'w', encoding='utf-8') as f:
                json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)
            self.project_path = save_path
            self.is_modified = False
            return True
        except Exception as e:
            print(f"[ProjectState] Erro ao salvar: {e}")
            return False
    
    def load(self, path: Path) -> bool:
        """Carrega projeto de arquivo JSON."""
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            self.layout_path = data.get("layout_path")
            self.slots_data = data.get("slots_data", {})
            self.metadata = data.get("metadata", {})
            self.project_path = path
            self.is_modified = False
            return True
        except Exception as e:
            print(f"[ProjectState] Erro ao carregar: {e}")
            return False


# Singleton para acesso global
_state_manager: Optional[AppStateManager] = None


def get_state_manager() -> AppStateManager:
    """Retorna instance singleton do state manager."""
    global _state_manager
    if _state_manager is None:
        _state_manager = AppStateManager()
    return _state_manager

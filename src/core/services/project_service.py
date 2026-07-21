"""
AutoTabloide AI - Project Service
=================================
Phase 0.1: Service Layer

Gerencia o ciclo de vida do projeto (Load, Save, Autosave).
Emite eventos via SignalBus.
Substitui o antigo ProjectManager logic.
"""

import json
import logging
from pathlib import Path
from typing import Optional, List, Dict
from dataclasses import dataclass, field
from datetime import datetime

from PySide6.QtCore import QTimer

from src.core.services.base import BaseService
from src.core.services.file_service import ASSETS_STORE

# =============================================================================
# DATA TRANSFER OBJECTS (DTOs)
# =============================================================================

@dataclass
class ProjectData:
    """Dados serializáveis de um projeto."""
    name: str = "Novo Projeto"
    path: Optional[str] = None
    template_path: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    modified_at: str = field(default_factory=lambda: datetime.now().isoformat())
    
    # Conteúdo
    slots: List[Dict] = field(default_factory=list)
    page_count: int = 1
    current_page: int = 1
    
    # Metadados
    description: str = ""
    tags: List[str] = field(default_factory=list)
    author: str = ""
    
    def to_dict(self) -> Dict:
        return {
            "name": self.name,
            "path": self.path,
            "template_path": self.template_path,
            "created_at": self.created_at,
            "modified_at": datetime.now().isoformat(),
            "slots": self.slots,
            "page_count": self.page_count,
            "current_page": self.current_page,
            "description": self.description,
            "tags": self.tags,
            "author": self.author,
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'ProjectData':
        return cls(
            name=data.get("name", "Projeto"),
            path=data.get("path"),
            template_path=data.get("template_path"),
            created_at=data.get("created_at", datetime.now().isoformat()),
            modified_at=data.get("modified_at", datetime.now().isoformat()),
            slots=data.get("slots", []),
            page_count=data.get("page_count", 1),
            current_page=data.get("current_page", 1),
            description=data.get("description", ""),
            tags=data.get("tags", []),
            author=data.get("author", ""),
        )

# =============================================================================
# SERVICE
# =============================================================================

class ProjectService(BaseService):
    """
    Serviço de gerenciamento de projetos.
    """
    
    _instance: Optional['ProjectService'] = None
    
    def __init__(self):
        super().__init__()
        self._current_project: Optional[ProjectData] = None
        self._is_modified = False
        
        # Paths
        self.workspace_dir = Path("AutoTabloide_System_Root/workspace/projects").resolve()
        self.workspace_dir.mkdir(parents=True, exist_ok=True)
        
        # Autosave
        self._autosave_timer = QTimer()
        self._autosave_timer.timeout.connect(self._autosave)
        self._autosave_interval = 60000 # 60s
        
        # Recent Projects
        self._recent_projects: List[str] = []
        self._load_recent()
        
    @classmethod
    def instance(cls) -> 'ProjectService':
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    # -------------------------------------------------------------------------
    # Public API
    # -------------------------------------------------------------------------

    @property
    def current_project(self) -> Optional[ProjectData]:
        return self._current_project

    def new_project(self, name: str = "Novo Projeto") -> ProjectData:
        self._current_project = ProjectData(name=name)
        self._is_modified = False
        self._start_autosave()
        
        # Notify
        self.bus.project_loaded.emit(self._current_project)
        self.log_status(f"Projeto criado: {name}")
        return self._current_project

    def load_project(self, path: str) -> Optional[ProjectData]:
        file_path = Path(path)
        if not file_path.exists():
            self.log_error("Erro de Arquivo", f"Projeto não encontrado: {path}")
            return None
            
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                
            self._current_project = ProjectData.from_dict(data)
            self._current_project.path = str(file_path)
            self._is_modified = False
            
            self._add_to_recent(str(file_path))
            self._start_autosave()
            
            # Notify
            self.bus.project_loaded.emit(self._current_project)
            self.log_status(f"Projeto carregado: {file_path.name}")
            return self._current_project
            
        except Exception as e:
            self.log_error("Falha ao Carregar", str(e))
            return None

    def save_project(self, path: str = None) -> bool:
        if not self._current_project:
            return False
            
        target_path = Path(path) if path else None
        if not target_path and self._current_project.path:
            target_path = Path(self._current_project.path)
            
        if not target_path:
            # Fallback define name based on project name
            safe_name = "".join(c for c in self._current_project.name if c.isalnum() or c in (' ','-','_')).strip()
            target_path = self.workspace_dir / f"{safe_name}.tabloide"
            
        try:
            # Backup logic could be injected or handled here
            if target_path.exists():
                self._create_backup(target_path)
            
            self._current_project.path = str(target_path)
            self._current_project.modified_at = datetime.now().isoformat()
            
            data = self._current_project.to_dict()
            with open(target_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                
            self._is_modified = False
            self._add_to_recent(str(target_path))
            
            # Notify
            self.bus.project_saved.emit(str(target_path))
            self.log_status(f"Projeto salvo: {target_path.name}")
            return True
            
        except Exception as e:
            self.log_error("Erro ao Salvar", str(e))
            return False

    def close_project(self):
        if self._current_project and self._is_modified:
            self._autosave()
            
        self._current_project = None
        self._is_modified = False
        self._autosave_timer.stop()
        self.bus.project_closed.emit()

    def mark_modified(self):
        self._is_modified = True

    def get_export_filename(self, version: int = 1) -> str:
        """Item 88: Naming Convention."""
        if not self._current_project:
            return "tabloide.pdf"
        date_str = datetime.now().strftime("%Y-%m-%d")
        name = self._current_project.name.replace(" ", "_")
        return f"{date_str}_{name}_v{version}.pdf"

    # -------------------------------------------------------------------------
    # Internal Logic
    # -------------------------------------------------------------------------

    def _start_autosave(self):
        if self._autosave_interval > 0:
            self._autosave_timer.start(self._autosave_interval)

    def _autosave(self):
        if not self._current_project or not self._is_modified:
            return
        
        autosave_path = self.workspace_dir / "autosave.tabloide"
        try:
            data = self._current_project.to_dict()
            with open(autosave_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            self.bus.project_autosaved.emit()
            
        except Exception as e:
            print(f"Autosave erro: {e}")

    def _create_backup(self, path: Path):
        backup_dir = self.workspace_dir / "backups"
        backup_dir.mkdir(exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = backup_dir / f"{path.stem}_{timestamp}{path.suffix}"
        import shutil
        try:
            shutil.copy2(path, backup_path)
        except:
            pass

    def _load_recent(self):
        recent_file = self.workspace_dir / "recent.json"
        if recent_file.exists():
            try:
                with open(recent_file, "r") as f:
                    self._recent_projects = json.load(f)
            except:
                self._recent_projects = []

    def _add_to_recent(self, path: str):
        if path in self._recent_projects:
            self._recent_projects.remove(path)
        self._recent_projects.insert(0, path)
        self._recent_projects = self._recent_projects[:10]
        self._save_recent()

    def _save_recent(self):
        try:
            with open(self.workspace_dir / "recent.json", "w") as f:
                json.dump(self._recent_projects, f)
        except:
            pass

def get_project_service() -> ProjectService:
    return ProjectService.instance()

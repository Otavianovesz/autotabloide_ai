"""
AutoTabloide AI - Project Manager
=================================
PROTOCOLO DE RETIFICAÇÃO NÍVEL 0 - Fase 3 (Passos 102, 103, 115)
Serialização, autosave e gerenciamento de projetos.
"""

from __future__ import annotations
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
import json
import logging

from PySide6.QtCore import QObject, Signal, QTimer

logger = logging.getLogger("ProjectManager")


# =============================================================================
# PROJECT DATA
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
        """Converte para dicionário."""
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
        """Cria a partir de dicionário."""
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
# PROJECT MANAGER
# =============================================================================

class ProjectManager(QObject):
    """
    Gerenciador de projetos com autosave.
    
    Features:
    - Serialização JSON de projetos
    - Autosave a cada 60 segundos
    - Histórico de projetos recentes
    - Backup automático antes de salvar
    """
    
    project_loaded = Signal(object)  # ProjectData
    project_saved = Signal(str)  # path
    project_modified = Signal()
    autosave_triggered = Signal()
    
    _instance: Optional['ProjectManager'] = None
    
    def __init__(self, projects_dir: Path = None, autosave_interval: int = 60):
        super().__init__()
        
        self.projects_dir = projects_dir or Path("AutoTabloide_System_Root/workspace/projects")
        self.projects_dir.mkdir(parents=True, exist_ok=True)
        
        self._current_project: Optional[ProjectData] = None
        self._is_modified = False
        
        # Autosave timer
        self._autosave_timer = QTimer()
        self._autosave_timer.timeout.connect(self._autosave)
        self._autosave_interval = autosave_interval * 1000  # ms
        
        # Histórico de recentes
        self._recent_projects: List[str] = []
        self._load_recent()
    
    @classmethod
    def instance(cls) -> 'ProjectManager':
        """Singleton."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    # =========================================================================
    # PROJECT OPERATIONS
    # =========================================================================
    
    def new_project(self, name: str = "Novo Projeto") -> ProjectData:
        """Cria novo projeto."""
        self._current_project = ProjectData(name=name)
        self._is_modified = False
        
        # Inicia autosave
        self._start_autosave()
        
        self.project_loaded.emit(self._current_project)
        logger.info(f"[Project] Novo projeto: {name}")
        return self._current_project
    
    def load_project(self, path: str) -> Optional[ProjectData]:
        """Carrega projeto de arquivo."""
        file_path = Path(path)
        
        if not file_path.exists():
            logger.error(f"[Project] Arquivo não encontrado: {path}")
            return None
        
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            self._current_project = ProjectData.from_dict(data)
            self._current_project.path = str(file_path)
            self._is_modified = False
            
            # Adiciona aos recentes
            self._add_to_recent(str(file_path))
            
            # Inicia autosave
            self._start_autosave()
            
            self.project_loaded.emit(self._current_project)
            logger.info(f"[Project] Carregado: {file_path.name}")
            
            return self._current_project
            
        except Exception as e:
            logger.error(f"[Project] Erro ao carregar: {e}")
            return None
    
    def save_project(self, path: str = None) -> bool:
        """Salva projeto atual."""
        if not self._current_project:
            return False
        
        save_path = Path(path) if path else (
            Path(self._current_project.path) if self._current_project.path 
            else self.projects_dir / f"{self._current_project.name}.tabloide"
        )
        
        try:
            # Backup antes de salvar
            if save_path.exists():
                self._create_backup(save_path)
            
            # Atualiza caminho
            self._current_project.path = str(save_path)
            
            # Serializa
            data = self._current_project.to_dict()
            
            with open(save_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            self._is_modified = False
            self._add_to_recent(str(save_path))
            
            self.project_saved.emit(str(save_path))
            logger.info(f"[Project] Salvo: {save_path.name}")
            
            return True
            
        except Exception as e:
            logger.error(f"[Project] Erro ao salvar: {e}")
            return False
    
    def close_project(self) -> bool:
        """Fecha projeto atual."""
        if self._is_modified:
            # Força autosave antes de fechar
            self._autosave()
        
        self._current_project = None
        self._is_modified = False
        self._autosave_timer.stop()
        
        logger.info("[Project] Projeto fechado")
        return True
    
    # =========================================================================
    # SCENE INTEGRATION
    # =========================================================================
    
    def update_from_scene(self, scene_data: Dict):
        """Atualiza projeto com dados da cena."""
        if self._current_project:
            self._current_project.slots = scene_data.get("slots", [])
            self._current_project.template_path = scene_data.get("template_path")
            self._is_modified = True
            self.project_modified.emit()
    
    def get_scene_data(self) -> Dict:
        """Retorna dados para reconstruir cena."""
        if not self._current_project:
            return {}
        
        return {
            "slots": self._current_project.slots,
            "template_path": self._current_project.template_path,
            "page_count": self._current_project.page_count,
        }
    
    # =========================================================================
    # AUTOSAVE
    # =========================================================================
    
    def _start_autosave(self):
        """Inicia timer de autosave."""
        if self._autosave_interval > 0:
            self._autosave_timer.start(self._autosave_interval)
    
    def _autosave(self):
        """Executa autosave."""
        if not self._current_project or not self._is_modified:
            return
        
        autosave_path = self.projects_dir / "autosave.tabloide"
        
        try:
            data = self._current_project.to_dict()
            
            with open(autosave_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            self.autosave_triggered.emit()
            logger.debug("[Project] Autosave executado")
            
        except Exception as e:
            logger.error(f"[Project] Erro no autosave: {e}")
    
    def has_autosave(self) -> bool:
        """Verifica se há autosave pendente."""
        autosave_path = self.projects_dir / "autosave.tabloide"
        return autosave_path.exists()
    
    def recover_autosave(self) -> Optional[ProjectData]:
        """Recupera projeto do autosave."""
        return self.load_project(str(self.projects_dir / "autosave.tabloide"))
    
    # =========================================================================
    # BACKUP
    # =========================================================================
    
    def _create_backup(self, path: Path):
        """Cria backup antes de sobrescrever."""
        backup_dir = self.projects_dir / "backups"
        backup_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = backup_dir / f"{path.stem}_{timestamp}{path.suffix}"
        
        try:
            import shutil
            shutil.copy(path, backup_path)
            logger.debug(f"[Project] Backup criado: {backup_path.name}")
        except Exception as e:
            logger.warning(f"[Project] Falha ao criar backup: {e}")
    
    # =========================================================================
    # RECENT PROJECTS
    # =========================================================================
    
    def _load_recent(self):
        """Carrega lista de projetos recentes."""
        recent_file = self.projects_dir / "recent.json"
        
        if recent_file.exists():
            try:
                with open(recent_file, "r", encoding="utf-8") as f:
                    self._recent_projects = json.load(f)
            except:
                self._recent_projects = []
    
    def _add_to_recent(self, path: str):
        """Adiciona projeto aos recentes."""
        if path in self._recent_projects:
            self._recent_projects.remove(path)
        
        self._recent_projects.insert(0, path)
        self._recent_projects = self._recent_projects[:10]  # Max 10
        
        self._save_recent()
    
    def _save_recent(self):
        """Salva lista de recentes."""
        recent_file = self.projects_dir / "recent.json"
        
        try:
            with open(recent_file, "w", encoding="utf-8") as f:
                json.dump(self._recent_projects, f)
        except:
            pass
    
    def get_recent_projects(self) -> List[str]:
        """Retorna lista de projetos recentes."""
        return self._recent_projects.copy()
    
    # =========================================================================
    # PROPERTIES
    # =========================================================================
    
    @property
    def current_project(self) -> Optional[ProjectData]:
        return self._current_project
    
    @property
    def is_modified(self) -> bool:
        return self._is_modified
    
    @property
    def project_name(self) -> str:
        return self._current_project.name if self._current_project else ""


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_project_manager() -> ProjectManager:
    """Acesso global ao project manager."""
    return ProjectManager.instance()

"""
AutoTabloide AI - Recent Projects Manager
=========================================
PROTOCOLO DE CONVERGÊNCIA 260 - Fase 6 (Passo 238)
Gerenciador de projetos recentes.
"""

from __future__ import annotations
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime
import json
import logging

from PySide6.QtCore import QSettings

logger = logging.getLogger("RecentProjects")


class RecentProjectsManager:
    """
    Gerenciador de projetos recentes.
    
    Features:
    - Lista de projetos recentes
    - Thumbnails
    - Persistência via QSettings
    """
    
    MAX_RECENT = 10
    
    _instance: Optional['RecentProjectsManager'] = None
    
    def __init__(self):
        self._settings = QSettings("AutoTabloideAI", "AutoTabloideAI")
        self._recent: List[Dict] = []
        self._load()
    
    @classmethod
    def instance(cls) -> 'RecentProjectsManager':
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    def _load(self):
        """Carrega lista do registro."""
        data = self._settings.value("recent_projects", "[]")
        try:
            self._recent = json.loads(data) if isinstance(data, str) else data or []
        except:
            self._recent = []
    
    def _save(self):
        """Salva lista no registro."""
        self._settings.setValue("recent_projects", json.dumps(self._recent))
    
    def add(self, path: str, name: str = None):
        """Adiciona projeto recente."""
        path = str(Path(path).resolve())
        
        # Remove se já existe
        self._recent = [p for p in self._recent if p.get("path") != path]
        
        # Adiciona no início
        self._recent.insert(0, {
            "path": path,
            "name": name or Path(path).stem,
            "accessed_at": datetime.now().isoformat()
        })
        
        # Limita tamanho
        self._recent = self._recent[:self.MAX_RECENT]
        
        self._save()
    
    def remove(self, path: str):
        """Remove projeto da lista."""
        path = str(Path(path).resolve())
        self._recent = [p for p in self._recent if p.get("path") != path]
        self._save()
    
    def clear(self):
        """Limpa lista."""
        self._recent = []
        self._save()
    
    def get_all(self) -> List[Dict]:
        """Retorna todos os recentes."""
        # Filtra inexistentes
        valid = []
        for p in self._recent:
            if Path(p.get("path", "")).exists():
                valid.append(p)
        
        if len(valid) != len(self._recent):
            self._recent = valid
            self._save()
        
        return list(self._recent)
    
    def get_most_recent(self) -> Optional[Dict]:
        """Retorna mais recente."""
        projects = self.get_all()
        return projects[0] if projects else None


def get_recent_projects() -> RecentProjectsManager:
    return RecentProjectsManager.instance()

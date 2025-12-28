"""
AutoTabloide AI - Project Serializer
====================================
PROTOCOLO DE CONVERGÊNCIA 260 - Fase 3 (Passos 113-115)
Serialização e deserialização de projetos.
"""

from __future__ import annotations
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
import json
import logging

logger = logging.getLogger("ProjectSerializer")


@dataclass
class ProjectMeta:
    """Metadados do projeto."""
    name: str
    created_at: str
    modified_at: str
    template_path: str
    version: str = "2.0"


@dataclass
class SlotState:
    """Estado de um slot."""
    slot_id: str
    slot_index: int
    product_id: Optional[int] = None
    override_name: Optional[str] = None
    override_price: Optional[float] = None
    locked: bool = False


@dataclass 
class ProjectData:
    """Dados completos do projeto."""
    meta: ProjectMeta
    slots: List[SlotState]
    settings: Dict = None


class ProjectSerializer:
    """
    Serializa/deserializa projetos .tabloide
    
    Formato JSON:
    {
        "meta": {...},
        "slots": [...],
        "settings": {...}
    }
    """
    
    EXTENSION = ".tabloide"
    
    def __init__(self):
        self._current_project: Optional[ProjectData] = None
        self._current_path: Optional[Path] = None
        self._dirty = False
    
    def new_project(self, name: str, template_path: str) -> ProjectData:
        """Cria novo projeto."""
        now = datetime.now().isoformat()
        
        self._current_project = ProjectData(
            meta=ProjectMeta(
                name=name,
                created_at=now,
                modified_at=now,
                template_path=template_path
            ),
            slots=[],
            settings={}
        )
        
        self._current_path = None
        self._dirty = True
        
        logger.info(f"[Project] New: {name}")
        return self._current_project
    
    def save(self, path: str = None) -> bool:
        """Salva projeto."""
        if not self._current_project:
            return False
        
        save_path = Path(path) if path else self._current_path
        
        if not save_path:
            return False
        
        # Garante extensão
        if save_path.suffix != self.EXTENSION:
            save_path = save_path.with_suffix(self.EXTENSION)
        
        # Atualiza modified_at
        self._current_project.meta.modified_at = datetime.now().isoformat()
        
        try:
            data = {
                "meta": asdict(self._current_project.meta),
                "slots": [asdict(s) for s in self._current_project.slots],
                "settings": self._current_project.settings or {}
            }
            
            with open(save_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            self._current_path = save_path
            self._dirty = False
            
            logger.info(f"[Project] Saved: {save_path}")
            return True
            
        except Exception as e:
            logger.error(f"Save error: {e}")
            return False
    
    def load(self, path: str) -> Optional[ProjectData]:
        """Carrega projeto."""
        load_path = Path(path)
        
        if not load_path.exists():
            logger.error(f"Project not found: {path}")
            return None
        
        try:
            with open(load_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            self._current_project = ProjectData(
                meta=ProjectMeta(**data["meta"]),
                slots=[SlotState(**s) for s in data.get("slots", [])],
                settings=data.get("settings", {})
            )
            
            self._current_path = load_path
            self._dirty = False
            
            logger.info(f"[Project] Loaded: {load_path}")
            return self._current_project
            
        except Exception as e:
            logger.error(f"Load error: {e}")
            return None
    
    def update_slot(self, slot_state: SlotState):
        """Atualiza estado de slot."""
        if not self._current_project:
            return
        
        # Encontra ou adiciona
        for i, s in enumerate(self._current_project.slots):
            if s.slot_index == slot_state.slot_index:
                self._current_project.slots[i] = slot_state
                self._dirty = True
                return
        
        self._current_project.slots.append(slot_state)
        self._dirty = True
    
    def get_slot_state(self, slot_index: int) -> Optional[SlotState]:
        """Retorna estado do slot."""
        if not self._current_project:
            return None
        
        for s in self._current_project.slots:
            if s.slot_index == slot_index:
                return s
        return None
    
    @property
    def is_dirty(self) -> bool:
        return self._dirty
    
    @property
    def current_path(self) -> Optional[Path]:
        return self._current_path
    
    @property
    def current_project(self) -> Optional[ProjectData]:
        return self._current_project


# =============================================================================
# SINGLETON
# =============================================================================

_instance: Optional[ProjectSerializer] = None


def get_project_serializer() -> ProjectSerializer:
    global _instance
    if _instance is None:
        _instance = ProjectSerializer()
    return _instance

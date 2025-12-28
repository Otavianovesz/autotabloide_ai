"""
AutoTabloide AI - Local Telemetry
=================================
PROTOCOLO DE RETIFICAÇÃO NÍVEL 0 - Fase 6 (Passo 206)
Telemetria local para analytics de uso.
"""

from __future__ import annotations
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass, field, asdict
from datetime import datetime
import logging
import json

logger = logging.getLogger("Telemetry")


@dataclass
class UsageEvent:
    """Evento de uso."""
    event_type: str
    timestamp: str = ""
    data: Dict = field(default_factory=dict)
    
    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()


class LocalTelemetry:
    """
    Telemetria local (não envia dados externos).
    
    Features:
    - Contagem de ações
    - Tempo de uso
    - Erros frequentes
    - Performance
    """
    
    def __init__(self, data_dir: Path = None):
        self._data_dir = data_dir or Path("AutoTabloide_System_Root/logs")
        self._data_dir.mkdir(parents=True, exist_ok=True)
        
        self._events: List[UsageEvent] = []
        self._session_start = datetime.now()
        self._action_counts: Dict[str, int] = {}
        
        self._load_stats()
    
    def track(self, event_type: str, data: Dict = None):
        """Registra evento."""
        event = UsageEvent(event_type, data=data or {})
        self._events.append(event)
        
        # Incrementa contador
        self._action_counts[event_type] = self._action_counts.get(event_type, 0) + 1
        
        logger.debug(f"[Telemetry] {event_type}")
    
    def track_export(self, format: str, pages: int = 1):
        """Registra exportação."""
        self.track("export", {"format": format, "pages": pages})
    
    def track_product_added(self, count: int = 1):
        """Registra produto adicionado."""
        self.track("product_added", {"count": count})
    
    def track_error(self, error_type: str, message: str):
        """Registra erro."""
        self.track("error", {"type": error_type, "message": message})
    
    def track_feature(self, feature: str):
        """Registra uso de feature."""
        self.track("feature_used", {"feature": feature})
    
    def get_session_duration(self) -> float:
        """Retorna duração da sessão em segundos."""
        return (datetime.now() - self._session_start).total_seconds()
    
    def get_stats(self) -> Dict:
        """Retorna estatísticas de uso."""
        return {
            "session_start": self._session_start.isoformat(),
            "session_duration_sec": self.get_session_duration(),
            "total_events": len(self._events),
            "action_counts": self._action_counts,
        }
    
    def save(self):
        """Salva estatísticas."""
        stats_file = self._data_dir / "usage_stats.json"
        
        try:
            stats = self.get_stats()
            
            # Carrega histórico
            history = {}
            if stats_file.exists():
                with open(stats_file, "r") as f:
                    history = json.load(f)
            
            # Atualiza contadores
            for action, count in self._action_counts.items():
                history[action] = history.get(action, 0) + count
            
            history["last_session"] = stats["session_start"]
            history["total_sessions"] = history.get("total_sessions", 0) + 1
            
            with open(stats_file, "w") as f:
                json.dump(history, f, indent=2)
                
        except Exception as e:
            logger.error(f"Erro ao salvar telemetria: {e}")
    
    def _load_stats(self):
        """Carrega estatísticas anteriores."""
        stats_file = self._data_dir / "usage_stats.json"
        
        if stats_file.exists():
            try:
                with open(stats_file, "r") as f:
                    data = json.load(f)
                    logger.info(f"[Telemetry] Sessões anteriores: {data.get('total_sessions', 0)}")
            except:
                pass
    
    def get_top_features(self, limit: int = 5) -> List[tuple]:
        """Retorna features mais usadas."""
        sorted_actions = sorted(
            self._action_counts.items(),
            key=lambda x: x[1],
            reverse=True
        )
        return sorted_actions[:limit]


# =============================================================================
# SINGLETON
# =============================================================================

_instance: Optional[LocalTelemetry] = None


def get_telemetry() -> LocalTelemetry:
    """Acesso global à telemetria."""
    global _instance
    if _instance is None:
        _instance = LocalTelemetry()
    return _instance


def track(event_type: str, data: Dict = None):
    """Helper para tracking."""
    get_telemetry().track(event_type, data)


def save_telemetry():
    """Salva telemetria."""
    get_telemetry().save()

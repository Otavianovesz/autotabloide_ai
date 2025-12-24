"""
AutoTabloide AI - Telemetry (Local)
=====================================
Sistema de telemetria local para métricas de uso.
Passo 93 do Checklist 100.

Funcionalidades:
- Métricas de uso 100% locais
- Export CSV de logs
- Nenhum envio para servidores externos
"""

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
import csv

from src.core.logging_config import get_logger
from src.core.constants import SYSTEM_ROOT

logger = get_logger("Telemetry")

# Arquivo de métricas
TELEMETRY_FILE = SYSTEM_ROOT / "config" / "telemetry.json"
TELEMETRY_FILE.parent.mkdir(parents=True, exist_ok=True)


@dataclass
class UsageMetric:
    """Uma métrica de uso individual."""
    timestamp: str
    event_type: str  # render, import, search, export
    duration_ms: int = 0
    success: bool = True
    details: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.details is None:
            self.details = {}


class LocalTelemetry:
    """
    Sistema de telemetria 100% local.
    Passo 93 do Checklist - Nenhum dado é enviado externamente.
    """
    
    _instance: Optional["LocalTelemetry"] = None
    
    def __new__(cls) -> "LocalTelemetry":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if hasattr(self, '_initialized'):
            return
        self._initialized = True
        self._metrics: List[UsageMetric] = []
        self._session_start = datetime.now()
        self._load_metrics()
    
    def _load_metrics(self) -> None:
        """Carrega métricas do arquivo."""
        if TELEMETRY_FILE.exists():
            try:
                data = json.loads(TELEMETRY_FILE.read_text(encoding='utf-8'))
                self._metrics = [UsageMetric(**m) for m in data.get('metrics', [])]
            except Exception as e:
                logger.warning(f"Erro ao carregar métricas: {e}")
                self._metrics = []
    
    def _save_metrics(self) -> None:
        """Salva métricas no arquivo."""
        try:
            data = {
                'version': '1.0',
                'last_updated': datetime.now().isoformat(),
                'metrics': [asdict(m) for m in self._metrics[-1000:]]  # Mantém últimas 1000
            }
            TELEMETRY_FILE.write_text(
                json.dumps(data, indent=2, ensure_ascii=False),
                encoding='utf-8'
            )
        except Exception as e:
            logger.warning(f"Erro ao salvar métricas: {e}")
    
    def record(
        self,
        event_type: str,
        duration_ms: int = 0,
        success: bool = True,
        **details
    ) -> None:
        """
        Registra uma métrica de uso.
        
        Args:
            event_type: Tipo de evento (render, import, search, export)
            duration_ms: Duração em milissegundos
            success: Se a operação foi bem-sucedida
            **details: Detalhes adicionais
        """
        metric = UsageMetric(
            timestamp=datetime.now().isoformat(),
            event_type=event_type,
            duration_ms=duration_ms,
            success=success,
            details=details if details else None
        )
        
        self._metrics.append(metric)
        
        # Salva a cada 10 eventos
        if len(self._metrics) % 10 == 0:
            self._save_metrics()
    
    def get_summary(self, days: int = 7) -> Dict[str, Any]:
        """
        Retorna resumo de uso dos últimos N dias.
        
        Args:
            days: Número de dias para análise
            
        Returns:
            Dict com estatísticas
        """
        cutoff = datetime.now() - timedelta(days=days)
        recent = [
            m for m in self._metrics
            if datetime.fromisoformat(m.timestamp) > cutoff
        ]
        
        # Agrupar por tipo
        by_type: Dict[str, List[UsageMetric]] = {}
        for m in recent:
            by_type.setdefault(m.event_type, []).append(m)
        
        summary = {
            'period_days': days,
            'total_events': len(recent),
            'by_type': {}
        }
        
        for event_type, metrics in by_type.items():
            durations = [m.duration_ms for m in metrics if m.duration_ms > 0]
            success_count = sum(1 for m in metrics if m.success)
            
            summary['by_type'][event_type] = {
                'count': len(metrics),
                'success_rate': success_count / len(metrics) if metrics else 0,
                'avg_duration_ms': sum(durations) / len(durations) if durations else 0,
            }
        
        return summary
    
    def export_csv(self, output_path: Path, days: int = 30) -> bool:
        """
        Exporta métricas para CSV.
        Passo 90 do Checklist - Export logs CSV.
        
        Args:
            output_path: Caminho do arquivo CSV
            days: Número de dias para exportar
            
        Returns:
            True se exportado com sucesso
        """
        cutoff = datetime.now() - timedelta(days=days)
        recent = [
            m for m in self._metrics
            if datetime.fromisoformat(m.timestamp) > cutoff
        ]
        
        try:
            with open(output_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['timestamp', 'event_type', 'duration_ms', 'success', 'details'])
                
                for m in recent:
                    writer.writerow([
                        m.timestamp,
                        m.event_type,
                        m.duration_ms,
                        m.success,
                        json.dumps(m.details) if m.details else ''
                    ])
            
            logger.info(f"Métricas exportadas: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao exportar CSV: {e}")
            return False
    
    def get_session_duration(self) -> timedelta:
        """Retorna duração da sessão atual."""
        return datetime.now() - self._session_start
    
    def clear_old_metrics(self, keep_days: int = 90) -> int:
        """
        Remove métricas antigas.
        
        Args:
            keep_days: Dias para manter
            
        Returns:
            Número de métricas removidas
        """
        cutoff = datetime.now() - timedelta(days=keep_days)
        original_count = len(self._metrics)
        
        self._metrics = [
            m for m in self._metrics
            if datetime.fromisoformat(m.timestamp) > cutoff
        ]
        
        removed = original_count - len(self._metrics)
        if removed > 0:
            self._save_metrics()
            logger.info(f"Métricas antigas removidas: {removed}")
        
        return removed


# Singleton
telemetry = LocalTelemetry()


def get_telemetry() -> LocalTelemetry:
    """Retorna singleton do LocalTelemetry."""
    return telemetry


# ==============================================================================
# HELPERS
# ==============================================================================

def track_duration(event_type: str):
    """
    Decorator para rastrear duração de funções.
    
    Uso:
        @track_duration("render")
        def render_page(...):
            ...
    """
    from functools import wraps
    import time
    
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start = time.perf_counter()
            success = True
            try:
                result = func(*args, **kwargs)
                return result
            except Exception:
                success = False
                raise
            finally:
                duration_ms = int((time.perf_counter() - start) * 1000)
                telemetry.record(event_type, duration_ms=duration_ms, success=success)
        
        return wrapper
    return decorator


def track_duration_async(event_type: str):
    """Versão assíncrona do decorator."""
    from functools import wraps
    import time
    
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start = time.perf_counter()
            success = True
            try:
                result = await func(*args, **kwargs)
                return result
            except Exception:
                success = False
                raise
            finally:
                duration_ms = int((time.perf_counter() - start) * 1000)
                telemetry.record(event_type, duration_ms=duration_ms, success=success)
        
        return wrapper
    return decorator

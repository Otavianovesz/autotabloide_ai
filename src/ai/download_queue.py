"""
AutoTabloide AI - Persistent Download Queue
==============================================
Fila persistente de downloads com SQLite.
PROTOCOLO DE RETIFICAÇÃO: Passo 57 (Fila persistente).

Downloads sobrevivem a reinícios e crashes.
"""

import asyncio
import logging
import json
from datetime import datetime
from typing import Optional, List, Dict, Any, Callable
from dataclasses import dataclass, field, asdict
from enum import Enum
from pathlib import Path
import sqlite3
import threading

logger = logging.getLogger("DownloadQueue")


class DownloadStatus(Enum):
    """Status de um download."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class DownloadPriority(Enum):
    """Prioridade do download."""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    URGENT = 4


@dataclass
class DownloadTask:
    """Tarefa de download."""
    id: Optional[int] = None
    url: str = ""
    destination: str = ""
    product_id: Optional[int] = None
    priority: DownloadPriority = DownloadPriority.NORMAL
    status: DownloadStatus = DownloadStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte para dict para serialização."""
        return {
            "id": self.id,
            "url": self.url,
            "destination": self.destination,
            "product_id": self.product_id,
            "priority": self.priority.value,
            "status": self.status.value,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "error_message": self.error_message,
            "retry_count": self.retry_count,
            "max_retries": self.max_retries,
            "metadata": json.dumps(self.metadata),
        }
    
    @classmethod
    def from_row(cls, row: tuple) -> 'DownloadTask':
        """Cria instância a partir de row do SQLite."""
        return cls(
            id=row[0],
            url=row[1],
            destination=row[2],
            product_id=row[3],
            priority=DownloadPriority(row[4]),
            status=DownloadStatus(row[5]),
            created_at=datetime.fromisoformat(row[6]) if row[6] else None,
            started_at=datetime.fromisoformat(row[7]) if row[7] else None,
            completed_at=datetime.fromisoformat(row[8]) if row[8] else None,
            error_message=row[9],
            retry_count=row[10],
            max_retries=row[11],
            metadata=json.loads(row[12]) if row[12] else {},
        )


class PersistentDownloadQueue:
    """
    Fila de downloads persistente em SQLite.
    
    PASSO 57: Fila sobrevive a reinícios.
    """
    
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self._lock = threading.RLock()
        self._init_db()
        
        # Callbacks
        self._on_progress: Optional[Callable[[int, float], None]] = None
        self._on_complete: Optional[Callable[[int], None]] = None
        self._on_error: Optional[Callable[[int, str], None]] = None
        
        # Worker
        self._running = False
        self._worker_task: Optional[asyncio.Task] = None
    
    def _init_db(self) -> None:
        """Inicializa schema do banco."""
        with self._lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS download_queue (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    url TEXT NOT NULL,
                    destination TEXT NOT NULL,
                    product_id INTEGER,
                    priority INTEGER DEFAULT 2,
                    status TEXT DEFAULT 'pending',
                    created_at TEXT,
                    started_at TEXT,
                    completed_at TEXT,
                    error_message TEXT,
                    retry_count INTEGER DEFAULT 0,
                    max_retries INTEGER DEFAULT 3,
                    metadata TEXT
                )
            """)
            
            # Índices
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_queue_status 
                ON download_queue(status)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_queue_priority 
                ON download_queue(priority DESC)
            """)
            
            conn.commit()
            conn.close()
            
            # Recuperar downloads em progresso de sessão anterior
            self._recover_interrupted()
    
    def _recover_interrupted(self) -> None:
        """Recupera downloads que estavam em progresso."""
        with self._lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Marcar como pending para re-tentar
            cursor.execute("""
                UPDATE download_queue 
                SET status = 'pending', started_at = NULL
                WHERE status = 'in_progress'
            """)
            
            affected = cursor.rowcount
            conn.commit()
            conn.close()
            
            if affected > 0:
                logger.info(f"Recuperados {affected} downloads interrompidos")
    
    def add(self, task: DownloadTask) -> int:
        """
        Adiciona tarefa à fila.
        
        Returns:
            ID da tarefa
        """
        with self._lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            data = task.to_dict()
            del data["id"]  # Auto-increment
            
            columns = ", ".join(data.keys())
            placeholders = ", ".join(["?" for _ in data])
            
            cursor.execute(
                f"INSERT INTO download_queue ({columns}) VALUES ({placeholders})",
                list(data.values())
            )
            
            task_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            logger.debug(f"Download adicionado: {task_id} - {task.url}")
            return task_id
    
    def get_next(self) -> Optional[DownloadTask]:
        """Retorna próxima tarefa pendente (por prioridade)."""
        with self._lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT * FROM download_queue 
                WHERE status = 'pending'
                ORDER BY priority DESC, created_at ASC
                LIMIT 1
            """)
            
            row = cursor.fetchone()
            conn.close()
            
            if row:
                return DownloadTask.from_row(row)
            return None
    
    def update_status(
        self,
        task_id: int,
        status: DownloadStatus,
        error_message: Optional[str] = None
    ) -> None:
        """Atualiza status de uma tarefa."""
        with self._lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            updates = {"status": status.value}
            
            if status == DownloadStatus.IN_PROGRESS:
                updates["started_at"] = datetime.now().isoformat()
            elif status in [DownloadStatus.COMPLETED, DownloadStatus.FAILED]:
                updates["completed_at"] = datetime.now().isoformat()
            
            if error_message:
                updates["error_message"] = error_message
            
            set_clause = ", ".join(f"{k} = ?" for k in updates.keys())
            
            cursor.execute(
                f"UPDATE download_queue SET {set_clause} WHERE id = ?",
                list(updates.values()) + [task_id]
            )
            
            conn.commit()
            conn.close()
    
    def increment_retry(self, task_id: int) -> bool:
        """
        Incrementa contador de retry.
        
        Returns:
            True se ainda pode re-tentar
        """
        with self._lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE download_queue 
                SET retry_count = retry_count + 1,
                    status = 'pending',
                    started_at = NULL
                WHERE id = ? AND retry_count < max_retries
            """, (task_id,))
            
            affected = cursor.rowcount
            conn.commit()
            conn.close()
            
            return affected > 0
    
    def get_pending_count(self) -> int:
        """Retorna número de downloads pendentes."""
        with self._lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT COUNT(*) FROM download_queue 
                WHERE status IN ('pending', 'in_progress')
            """)
            
            count = cursor.fetchone()[0]
            conn.close()
            return count
    
    def get_all(self, limit: int = 100) -> List[DownloadTask]:
        """Retorna todas as tarefas (para UI)."""
        with self._lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT * FROM download_queue 
                ORDER BY created_at DESC
                LIMIT ?
            """, (limit,))
            
            rows = cursor.fetchall()
            conn.close()
            
            return [DownloadTask.from_row(row) for row in rows]
    
    def clear_completed(self) -> int:
        """Remove downloads completados."""
        with self._lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                DELETE FROM download_queue 
                WHERE status IN ('completed', 'cancelled')
            """)
            
            affected = cursor.rowcount
            conn.commit()
            conn.close()
            
            return affected
    
    def cancel(self, task_id: int) -> bool:
        """Cancela um download pendente."""
        self.update_status(task_id, DownloadStatus.CANCELLED)
        return True
    
    # =========================================================================
    # WORKER ASSÍNCRONO
    # =========================================================================
    
    async def start_worker(self, concurrent: int = 2) -> None:
        """Inicia worker de downloads."""
        self._running = True
        
        async def process_downloads():
            while self._running:
                task = self.get_next()
                
                if task:
                    await self._process_task(task)
                else:
                    await asyncio.sleep(1)
        
        # Múltiplos workers
        workers = [process_downloads() for _ in range(concurrent)]
        self._worker_task = asyncio.gather(*workers)
        
        try:
            await self._worker_task
        except asyncio.CancelledError:
            pass
    
    def stop_worker(self) -> None:
        """Para worker de downloads."""
        self._running = False
        if self._worker_task:
            self._worker_task.cancel()
    
    async def _process_task(self, task: DownloadTask) -> None:
        """Processa uma tarefa de download."""
        import aiohttp
        
        self.update_status(task.id, DownloadStatus.IN_PROGRESS)
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(task.url, timeout=aiohttp.ClientTimeout(total=60)) as response:
                    if response.status != 200:
                        raise Exception(f"HTTP {response.status}")
                    
                    # Salvar arquivo
                    dest = Path(task.destination)
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    
                    with open(dest, 'wb') as f:
                        async for chunk in response.content.iter_chunked(8192):
                            f.write(chunk)
            
            self.update_status(task.id, DownloadStatus.COMPLETED)
            
            if self._on_complete:
                self._on_complete(task.id)
            
            logger.info(f"Download completo: {task.id}")
            
        except Exception as e:
            logger.error(f"Download falhou: {task.id} - {e}")
            
            # Tentar novamente?
            if not self.increment_retry(task.id):
                self.update_status(task.id, DownloadStatus.FAILED, str(e))
                
                if self._on_error:
                    self._on_error(task.id, str(e))


# ==============================================================================
# INSTÂNCIA GLOBAL
# ==============================================================================

_queue: Optional[PersistentDownloadQueue] = None


def get_download_queue(db_path: Optional[Path] = None) -> PersistentDownloadQueue:
    """Retorna instância global da fila."""
    global _queue
    
    if _queue is None:
        if db_path is None:
            from src.core.constants import SYSTEM_ROOT
            db_path = SYSTEM_ROOT / "database" / "download_queue.db"
        
        _queue = PersistentDownloadQueue(db_path)
    
    return _queue


async def queue_download(
    url: str,
    destination: str,
    product_id: Optional[int] = None,
    priority: str = "normal"
) -> int:
    """Função de conveniência para adicionar download."""
    queue = get_download_queue()
    
    task = DownloadTask(
        url=url,
        destination=destination,
        product_id=product_id,
        priority=DownloadPriority[priority.upper()]
    )
    
    return queue.add(task)

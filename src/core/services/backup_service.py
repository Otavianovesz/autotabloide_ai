"""
AutoTabloide AI - Backup Service
==================================
Serviço de backup automático com rotação.
Passos 65, 63-64 do Checklist 100.

Funcionalidades:
- Backup automático a cada X horas
- Rotação de backups (mantém N mais recentes)
- Verificação de integridade de template
"""

import asyncio
import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional, List
import hashlib

from src.core.logging_config import get_logger
from src.core.constants import SYSTEM_ROOT
from src.core.database import create_atomic_snapshot, list_snapshots
from src.core.settings_service import settings_service

logger = get_logger("BackupService")

# Diretórios
SNAPSHOTS_DIR = SYSTEM_ROOT / "snapshots"
SNAPSHOTS_DIR.mkdir(parents=True, exist_ok=True)


class BackupService:
    """
    Serviço de backup automático.
    Gerencia snapshots periódicos e rotação.
    """
    
    _instance: Optional["BackupService"] = None
    _task: Optional[asyncio.Task] = None
    _running: bool = False
    
    def __new__(cls) -> "BackupService":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    async def start_auto_backup(self) -> None:
        """
        Inicia loop de backup automático em background.
        Passo 65 do Checklist.
        """
        if self._running:
            logger.warning("BackupService já está rodando")
            return
        
        self._running = True
        self._task = asyncio.create_task(self._backup_loop())
        logger.info("BackupService iniciado")
    
    async def stop_auto_backup(self) -> None:
        """Para o loop de backup."""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("BackupService parado")
    
    async def _backup_loop(self) -> None:
        """Loop principal de backup."""
        while self._running:
            try:
                # Intervalo configurável (padrão 4 horas)
                interval_hours = settings_service.get("backup.auto_interval_hours", 4)
                interval_seconds = interval_hours * 3600
                
                # Aguarda intervalo
                await asyncio.sleep(interval_seconds)
                
                if not self._running:
                    break
                
                # Executa backup
                await self.create_backup()
                
                # Rotação de backups antigos
                await self.rotate_backups()
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Erro no backup automático: {e}")
                await asyncio.sleep(300)  # Retry em 5 min
    
    async def create_backup(self) -> Optional[Path]:
        """
        Cria backup atômico do banco de dados.
        
        Returns:
            Caminho do backup criado ou None se falhar
        """
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"auto_backup_{timestamp}.db"
            backup_path = SNAPSHOTS_DIR / backup_name
            
            # Usa VACUUM INTO para snapshot atômico
            result_path = await create_atomic_snapshot(str(backup_path))
            
            logger.info(f"Backup criado: {backup_name}")
            return Path(result_path)
            
        except Exception as e:
            logger.error(f"Falha ao criar backup: {e}")
            return None
    
    async def rotate_backups(self) -> int:
        """
        Remove backups antigos mantendo N mais recentes.
        
        Returns:
            Número de backups removidos
        """
        try:
            max_snapshots = settings_service.get("backup.max_snapshots", 10)
            
            # Lista snapshots ordenados por data (mais recente primeiro)
            snapshots = await list_snapshots()
            
            # Filtra apenas backups automáticos
            auto_backups = [s for s in snapshots if "auto_backup" in s["name"]]
            
            # Remove excedentes
            removed = 0
            if len(auto_backups) > max_snapshots:
                for snapshot in auto_backups[max_snapshots:]:
                    try:
                        Path(snapshot["path"]).unlink()
                        removed += 1
                    except Exception as e:
                        logger.warning(f"Não foi possível remover {snapshot['name']}: {e}")
            
            if removed > 0:
                logger.info(f"Rotação: {removed} backups antigos removidos")
            
            return removed
            
        except Exception as e:
            logger.error(f"Erro na rotação de backups: {e}")
            return 0
    
    @staticmethod
    def calculate_file_hash(file_path: Path) -> str:
        """
        Calcula SHA256 de um arquivo.
        Usado para verificação de integridade de templates.
        Passo 64 do Checklist.
        """
        sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                sha256.update(chunk)
        return sha256.hexdigest()
    
    @staticmethod
    def verify_template_integrity(template_path: Path, expected_hash: str) -> bool:
        """
        Verifica se template SVG não foi alterado.
        Passo 64 do Checklist.
        
        Args:
            template_path: Caminho do arquivo SVG
            expected_hash: Hash esperado (salvo no projeto)
            
        Returns:
            True se integridade OK
        """
        if not template_path.exists():
            return False
        
        current_hash = BackupService.calculate_file_hash(template_path)
        return current_hash == expected_hash


# Singleton
backup_service = BackupService()


def get_backup_service() -> BackupService:
    """Retorna singleton do BackupService."""
    return backup_service


# ==============================================================================
# VALIDAÇÃO DE PREÇO (Passo 62)
# ==============================================================================

def validate_price_change(
    old_price: float,
    new_price: float,
    threshold_percent: float = 50.0
) -> dict:
    """
    Valida se variação de preço é suspeita.
    Passo 62 do Checklist - Previne erro de digitação.
    
    Args:
        old_price: Preço anterior
        new_price: Novo preço
        threshold_percent: Porcentagem máxima de variação
        
    Returns:
        Dict com status e mensagem
    """
    if old_price <= 0 or new_price <= 0:
        return {"valid": True, "warning": None}
    
    # Calcula variação percentual
    change_percent = abs((new_price - old_price) / old_price) * 100
    
    if change_percent > threshold_percent:
        direction = "aumento" if new_price > old_price else "redução"
        return {
            "valid": False,
            "warning": f"Atenção: {direction} de {change_percent:.0f}% no preço "
                      f"(R$ {old_price:.2f} → R$ {new_price:.2f}). Confirmar alteração?",
            "change_percent": change_percent
        }
    
    return {"valid": True, "warning": None, "change_percent": change_percent}

"""
AutoTabloide AI - Sistema de Integridade e Self-Healing
========================================================
Conforme Auditoria Industrial: Bootstrap resiliente com autocorreção.
Verifica e repara arquivos críticos automaticamente.
"""

from __future__ import annotations
import json
import shutil
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any, List, Tuple
import hashlib
import sqlite3

from .logging_config import get_logger
from .schemas import SettingsSchema, validate_or_default
from .constants import SystemPaths, DatabaseConfig

logger = get_logger("Integrity")


class IntegrityChecker:
    """
    Verificador de integridade do sistema com capacidade de autocorreção.
    
    Implementa o padrão Self-Healing:
    - Detecta arquivos corrompidos
    - Cria backups antes de reparar
    - Restaura defaults quando necessário
    """
    
    def __init__(self, system_root: Path):
        """
        Args:
            system_root: Caminho raiz do sistema
        """
        self.root = Path(system_root)
        self.issues: List[str] = []
        self.repairs: List[str] = []
    
    def run_full_check(self, auto_repair: bool = True) -> Tuple[bool, List[str]]:
        """
        Executa verificação completa do sistema.
        
        Args:
            auto_repair: Se deve reparar automaticamente
            
        Returns:
            Tuple (sucesso, lista de issues/repairs)
        """
        self.issues.clear()
        self.repairs.clear()
        
        logger.info("Iniciando verificação de integridade...")
        
        # 1. Verificar estrutura de diretórios
        self._check_directories()
        
        # 2. Verificar settings.json
        self._check_settings(auto_repair)
        
        # 3. Verificar banco de dados
        self._check_database(auto_repair)
        
        # 4. Verificar assets críticos
        self._check_critical_assets()
        
        # Resultado
        success = len(self.issues) == 0
        messages = self.repairs if success else self.issues
        
        if success:
            logger.info("✓ Verificação concluída sem problemas.")
        else:
            logger.warning(f"Verificação encontrou {len(self.issues)} problemas.")
        
        return success, messages
    
    def _check_directories(self) -> None:
        """Verifica e cria diretórios obrigatórios."""
        required_dirs = [
            SystemPaths.BIN,
            SystemPaths.CONFIG,
            SystemPaths.DATABASE,
            SystemPaths.ASSETS_STORE,
            SystemPaths.ASSETS_THUMBS,
            SystemPaths.ASSETS_FONTS,
            SystemPaths.STAGING,
            SystemPaths.TEMP,
            SystemPaths.LIBRARY_SVG,
            SystemPaths.LIBRARY_THUMBS,
            SystemPaths.WORKSPACES,
            SystemPaths.SNAPSHOTS,
            SystemPaths.LOGS,
        ]
        
        for dir_path in required_dirs:
            full_path = self.root / dir_path
            if not full_path.exists():
                full_path.mkdir(parents=True, exist_ok=True)
                self.repairs.append(f"Criado diretório: {dir_path}")
                logger.info(f"Criado diretório ausente: {dir_path}")
    
    def _check_settings(self, auto_repair: bool) -> None:
        """
        Verifica settings.json e repara se corrompido.
        """
        settings_path = self.root / SystemPaths.SETTINGS_FILE
        
        if not settings_path.exists():
            if auto_repair:
                self._create_default_settings(settings_path)
                self.repairs.append("Criado settings.json padrão")
            else:
                self.issues.append("settings.json não encontrado")
            return
        
        # Tentar carregar e validar
        try:
            with open(settings_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Validar com Pydantic
            settings = SettingsSchema.model_validate(data)
            logger.debug("settings.json válido")
            
        except json.JSONDecodeError as e:
            self.issues.append(f"settings.json corrompido: {e}")
            if auto_repair:
                self._backup_and_repair_settings(settings_path)
                
        except Exception as e:
            self.issues.append(f"settings.json inválido: {e}")
            if auto_repair:
                self._backup_and_repair_settings(settings_path)
    
    def _create_default_settings(self, path: Path) -> None:
        """Cria settings.json com valores padrão."""
        path.parent.mkdir(parents=True, exist_ok=True)
        
        defaults = SettingsSchema.get_defaults()
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(defaults.model_dump(), f, indent=2, ensure_ascii=False)
        
        logger.info("Criado settings.json com valores padrão")
    
    def _backup_and_repair_settings(self, path: Path) -> None:
        """
        Faz backup do arquivo corrompido e recria.
        Implementa Self-Healing.
        """
        # Criar backup com timestamp
        backup_name = f"settings_{datetime.now():%Y%m%d_%H%M%S}.json.bak"
        backup_path = path.parent / backup_name
        
        try:
            shutil.copy2(path, backup_path)
            logger.info(f"Backup criado: {backup_name}")
            self.repairs.append(f"Backup do corrompido: {backup_name}")
        except Exception as e:
            logger.error(f"Falha ao criar backup: {e}")
        
        # Recriar com padrões
        self._create_default_settings(path)
        self.repairs.append("settings.json restaurado para padrão")
    
    def _check_database(self, auto_repair: bool) -> None:
        """
        Verifica integridade do banco SQLite.
        """
        db_path = self.root / SystemPaths.DATABASE_FILE
        
        if not db_path.exists():
            # Banco será criado pelo ORM
            logger.info("Banco de dados será criado na primeira execução")
            return
        
        try:
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()
            
            # 1. Verificar integridade
            cursor.execute("PRAGMA integrity_check;")
            result = cursor.fetchone()[0]
            
            if result != "ok":
                self.issues.append(f"Banco corrompido: {result}")
                if auto_repair:
                    self._attempt_database_repair(db_path)
                conn.close()
                return
            
            # 2. Verificar WAL mode
            cursor.execute("PRAGMA journal_mode;")
            mode = cursor.fetchone()[0]
            
            if mode.lower() != "wal":
                logger.info("Ativando WAL mode no banco de dados")
                cursor.execute("PRAGMA journal_mode=WAL;")
                self.repairs.append("WAL mode ativado")
            
            # 3. Verificar outras PRAGMAs
            cursor.execute(f"PRAGMA synchronous={DatabaseConfig.SYNCHRONOUS};")
            cursor.execute(f"PRAGMA cache_size={DatabaseConfig.CACHE_SIZE};")
            cursor.execute(f"PRAGMA temp_store={DatabaseConfig.TEMP_STORE};")
            
            conn.commit()
            conn.close()
            logger.debug("Banco de dados verificado com sucesso")
            
        except sqlite3.DatabaseError as e:
            self.issues.append(f"Erro no banco: {e}")
            if auto_repair:
                self._attempt_database_repair(db_path)
    
    def _attempt_database_repair(self, db_path: Path) -> None:
        """
        Tenta reparar banco corrompido.
        
        Estratégia:
        1. Fazer backup
        2. Tentar VACUUM
        3. Se falhar, restaurar último snapshot
        """
        # Backup
        backup_name = f"core_{datetime.now():%Y%m%d_%H%M%S}.db.bak"
        backup_path = db_path.parent / backup_name
        
        try:
            shutil.copy2(db_path, backup_path)
            logger.info(f"Backup do banco: {backup_name}")
            self.repairs.append(f"Backup do banco corrompido: {backup_name}")
        except Exception as e:
            logger.error(f"Falha no backup: {e}")
            return
        
        # Tentar VACUUM
        try:
            conn = sqlite3.connect(str(db_path))
            conn.execute("VACUUM;")
            conn.close()
            self.repairs.append("Banco reparado via VACUUM")
            logger.info("Banco reparado com sucesso via VACUUM")
        except Exception as e:
            logger.error(f"VACUUM falhou: {e}")
            # Marcar para restauração de snapshot
            self.issues.append("Banco irrecuperável - restaure um snapshot")
    
    def _check_critical_assets(self) -> None:
        """Verifica assets críticos (fontes, perfis ICC)."""
        fonts_dir = self.root / SystemPaths.ASSETS_FONTS
        
        required_fonts = [
            "Roboto-Regular.ttf",
            "Roboto-Bold.ttf",
        ]
        
        for font_name in required_fonts:
            font_path = fonts_dir / font_name
            if not font_path.exists():
                self.issues.append(f"Fonte ausente: {font_name}")
                logger.warning(f"Fonte crítica não encontrada: {font_name}")


class SafeModeManager:
    """
    Gerenciador do Modo de Segurança.
    
    Ativado automaticamente após falhas consecutivas de boot.
    """
    
    CONSECUTIVE_FAILURES_THRESHOLD = 3
    
    def __init__(self, system_root: Path):
        self.root = Path(system_root)
        self.flag_file = self.root / SystemPaths.SAFE_MODE_FLAG
        self.crash_counter_file = self.root / "config/.crash_count"
    
    def is_safe_mode(self) -> bool:
        """Verifica se está em modo de segurança."""
        return self.flag_file.exists()
    
    def enter_safe_mode(self, reason: str = "Unknown") -> None:
        """Entra em modo de segurança."""
        self.flag_file.parent.mkdir(parents=True, exist_ok=True)
        
        data = {
            "entered_at": datetime.now().isoformat(),
            "reason": reason
        }
        
        with open(self.flag_file, 'w', encoding='utf-8') as f:
            json.dump(data, f)
        
        logger.warning(f"SAFE MODE ativado: {reason}")
    
    def exit_safe_mode(self) -> bool:
        """
        Tenta sair do modo de segurança.
        
        Returns:
            True se conseguiu sair
        """
        if not self.is_safe_mode():
            return True
        
        try:
            self.flag_file.unlink()
            self._reset_crash_counter()
            logger.info("Saiu do modo de segurança")
            return True
        except Exception as e:
            logger.error(f"Falha ao sair do safe mode: {e}")
            return False
    
    def record_crash(self) -> None:
        """Registra uma falha de boot."""
        count = self._get_crash_count() + 1
        
        with open(self.crash_counter_file, 'w') as f:
            f.write(str(count))
        
        if count >= self.CONSECUTIVE_FAILURES_THRESHOLD:
            self.enter_safe_mode(
                f"Falhas consecutivas de boot: {count}"
            )
    
    def record_success(self) -> None:
        """Registra boot bem-sucedido."""
        self._reset_crash_counter()
    
    def _get_crash_count(self) -> int:
        """Retorna contador de crashes."""
        try:
            if self.crash_counter_file.exists():
                return int(self.crash_counter_file.read_text().strip())
        except:
            pass
        return 0
    
    def _reset_crash_counter(self) -> None:
        """Reseta contador de crashes."""
        try:
            if self.crash_counter_file.exists():
                self.crash_counter_file.unlink()
        except:
            pass


def run_startup_checks(system_root: Path) -> Tuple[bool, bool]:
    """
    Executa verificações de inicialização.
    
    Args:
        system_root: Caminho raiz do sistema
        
    Returns:
        Tuple (sucesso, is_safe_mode)
    """
    safe_mode_mgr = SafeModeManager(system_root)
    checker = IntegrityChecker(system_root)
    
    try:
        success, messages = checker.run_full_check(auto_repair=True)
        
        if success:
            safe_mode_mgr.record_success()
        
        return success, safe_mode_mgr.is_safe_mode()
        
    except Exception as e:
        logger.error(f"Falha na verificação de integridade: {e}")
        safe_mode_mgr.record_crash()
        return False, safe_mode_mgr.is_safe_mode()

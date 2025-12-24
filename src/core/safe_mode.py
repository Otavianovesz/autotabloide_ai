"""
AutoTabloide AI - Safe Mode Bootstrap
=====================================
Implementação conforme Vol. III, Cap. 8.2 e Vol. VI, Cap. 10.

Detecta crashes consecutivos e ativa modo seguro para recuperação.
"""

import os
import json
import logging
import traceback
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Tuple
from dataclasses import dataclass, asdict

logger = logging.getLogger("SafeMode")

# Constantes do Safe Mode
MAX_CONSECUTIVE_FAILURES = 3
BOOT_LOG_RETENTION_HOURS = 24
SAFE_MODE_FEATURES = [
    "database_readonly",      # DB somente leitura
    "no_ai_processing",       # Desativa processamento de IA
    "minimal_ui",             # UI reduzida
    "diagnostic_mode",        # Logs detalhados
]


@dataclass
class BootAttempt:
    """Registro de tentativa de boot."""
    timestamp: str
    success: bool
    error_type: Optional[str] = None
    error_message: Optional[str] = None
    traceback: Optional[str] = None
    version: str = "1.0.0"
    
    def to_dict(self) -> dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: dict) -> "BootAttempt":
        return cls(**data)


class SafeModeController:
    """
    Controlador do Safe Mode.
    
    Responsabilidades:
    - Rastrear tentativas de boot em boot_attempt.log
    - Detectar crashes consecutivos
    - Ativar/desativar modo seguro
    - Resetar estado após boot bem-sucedido
    """
    
    def __init__(self, root_path: Path = None):
        self.root_path = root_path or Path(__file__).parent.parent / "AutoTabloide_System_Root"
        self.config_path = self.root_path / "config"
        self.boot_log_path = self.config_path / "boot_attempt.log"
        self.safe_mode_flag_path = self.config_path / "safe_mode.flag"
        
        # Garante que diretório existe
        self.config_path.mkdir(parents=True, exist_ok=True)
        
        self._is_safe_mode = False
        self._boot_attempts: list[BootAttempt] = []
        self._load_boot_history()
    
    def _load_boot_history(self):
        """Carrega histórico de boots."""
        if not self.boot_log_path.exists():
            self._boot_attempts = []
            return
        
        try:
            with open(self.boot_log_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self._boot_attempts = [
                    BootAttempt.from_dict(item) for item in data
                ]
            
            # Remove entradas antigas
            cutoff = datetime.now() - timedelta(hours=BOOT_LOG_RETENTION_HOURS)
            self._boot_attempts = [
                attempt for attempt in self._boot_attempts
                if datetime.fromisoformat(attempt.timestamp) > cutoff
            ]
        except Exception as e:
            logger.warning(f"Erro ao carregar boot history: {e}")
            self._boot_attempts = []
    
    def _save_boot_history(self):
        """Persiste histórico de boots."""
        try:
            with open(self.boot_log_path, 'w', encoding='utf-8') as f:
                json.dump(
                    [attempt.to_dict() for attempt in self._boot_attempts],
                    f, indent=2, ensure_ascii=False
                )
        except Exception as e:
            logger.error(f"Erro ao salvar boot history: {e}")
    
    def register_boot_start(self) -> bool:
        """
        Registra início de tentativa de boot.
        Retorna True se deve entrar em Safe Mode.
        """
        # Conta falhas consecutivas recentes
        consecutive_failures = self._count_consecutive_failures()
        
        if consecutive_failures >= MAX_CONSECUTIVE_FAILURES:
            logger.warning(
                f"Safe Mode ativado: {consecutive_failures} crashes consecutivos detectados"
            )
            self._activate_safe_mode()
            return True
        
        # Também verifica flag explícita de safe mode
        if self.safe_mode_flag_path.exists():
            logger.info("Safe Mode flag encontrada, ativando modo seguro")
            self._is_safe_mode = True
            return True
        
        return False
    
    def register_boot_success(self):
        """Registra boot bem-sucedido."""
        attempt = BootAttempt(
            timestamp=datetime.now().isoformat(),
            success=True
        )
        self._boot_attempts.append(attempt)
        self._save_boot_history()
        
        # Se estava em safe mode e bootou com sucesso, desativa
        if self._is_safe_mode:
            self._deactivate_safe_mode()
        
        logger.info("Boot bem-sucedido registrado")
    
    def register_boot_failure(self, exception: Exception):
        """Registra falha no boot."""
        attempt = BootAttempt(
            timestamp=datetime.now().isoformat(),
            success=False,
            error_type=type(exception).__name__,
            error_message=str(exception),
            traceback=traceback.format_exc()
        )
        self._boot_attempts.append(attempt)
        self._save_boot_history()
        
        logger.error(f"Boot falhou: {exception}")
    
    def _count_consecutive_failures(self) -> int:
        """Conta falhas consecutivas mais recentes."""
        count = 0
        for attempt in reversed(self._boot_attempts):
            if attempt.success:
                break
            count += 1
        return count
    
    def _activate_safe_mode(self):
        """Ativa Safe Mode e cria flag."""
        self._is_safe_mode = True
        
        try:
            with open(self.safe_mode_flag_path, 'w') as f:
                f.write(datetime.now().isoformat())
        except Exception as e:
            logger.error(f"Erro ao criar safe mode flag: {e}")
    
    def _deactivate_safe_mode(self):
        """Desativa Safe Mode e remove flag."""
        self._is_safe_mode = False
        
        try:
            if self.safe_mode_flag_path.exists():
                self.safe_mode_flag_path.unlink()
        except Exception as e:
            logger.warning(f"Erro ao remover safe mode flag: {e}")
        
        logger.info("Safe Mode desativado")
    
    @property
    def is_safe_mode(self) -> bool:
        return self._is_safe_mode
    
    def get_safe_mode_config(self) -> dict:
        """Retorna configuração do Safe Mode."""
        if not self._is_safe_mode:
            return {"enabled": False, "features": []}
        
        return {
            "enabled": True,
            "features": SAFE_MODE_FEATURES,
            "consecutive_failures": self._count_consecutive_failures(),
            "last_error": self._get_last_error()
        }
    
    def _get_last_error(self) -> Optional[str]:
        """Retorna último erro registrado."""
        for attempt in reversed(self._boot_attempts):
            if not attempt.success and attempt.error_message:
                return attempt.error_message
        return None
    
    def force_safe_mode(self, reason: str = "Manual activation"):
        """Força ativação do Safe Mode."""
        logger.warning(f"Safe Mode forçado: {reason}")
        self._activate_safe_mode()
    
    def clear_safe_mode(self):
        """Limpa Safe Mode e histórico de falhas."""
        self._boot_attempts = [
            a for a in self._boot_attempts if a.success
        ]
        self._save_boot_history()
        self._deactivate_safe_mode()
        logger.info("Safe Mode e histórico de falhas limpos")


# Singleton global
_safe_mode_controller: Optional[SafeModeController] = None


def get_safe_mode_controller() -> SafeModeController:
    """Obtém instância singleton do SafeModeController."""
    global _safe_mode_controller
    if _safe_mode_controller is None:
        _safe_mode_controller = SafeModeController()
    return _safe_mode_controller


def init_safe_mode(root_path: Path = None) -> Tuple[SafeModeController, bool]:
    """
    Inicializa Safe Mode no boot da aplicação.
    Retorna (controller, is_safe_mode).
    """
    global _safe_mode_controller
    _safe_mode_controller = SafeModeController(root_path)
    is_safe = _safe_mode_controller.register_boot_start()
    return _safe_mode_controller, is_safe

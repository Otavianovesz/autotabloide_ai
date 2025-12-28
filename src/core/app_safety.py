"""
AutoTabloide AI - Global Exception Hook & App Settings
=======================================================
PROTOCOLO DE RETIFICAÇÃO NÍVEL 0 - Fase 1 (Passos 10-11)
Captura crashes não tratados e singleton de configurações.
"""

from __future__ import annotations
from pathlib import Path
from typing import Any, Dict, Optional
from dataclasses import dataclass, field
import sys
import traceback
import json
import logging
from datetime import datetime

from PySide6.QtWidgets import QMessageBox, QApplication
from PySide6.QtCore import QSettings

logger = logging.getLogger("AppSafety")


# =============================================================================
# GLOBAL EXCEPTION HOOK (Passo 10)
# =============================================================================

class GlobalExceptionHandler:
    """
    Captura exceções não tratadas antes do crash.
    Mostra QMessageBox crítico e salva crash log.
    """
    
    _instance: Optional['GlobalExceptionHandler'] = None
    
    def __init__(self, log_dir: Path = None):
        self.log_dir = log_dir or Path("logs")
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self._original_hook = sys.excepthook
    
    @classmethod
    def install(cls, log_dir: Path = None) -> 'GlobalExceptionHandler':
        """Instala o hook global."""
        if cls._instance is None:
            cls._instance = cls(log_dir)
            sys.excepthook = cls._instance._handle_exception
            logger.info("[Safety] Global exception hook instalado")
        return cls._instance
    
    @classmethod
    def uninstall(cls):
        """Remove o hook global."""
        if cls._instance:
            sys.excepthook = cls._instance._original_hook
            cls._instance = None
    
    def _handle_exception(self, exc_type, exc_value, exc_tb):
        """Handler chamado em exceções não tratadas."""
        # Formata traceback
        tb_lines = traceback.format_exception(exc_type, exc_value, exc_tb)
        tb_text = "".join(tb_lines)
        
        # Salva crash log
        crash_file = self._save_crash_log(exc_type, exc_value, tb_text)
        
        # Mostra mensagem para usuário
        self._show_crash_dialog(exc_type, exc_value, crash_file)
        
        # Chama hook original
        self._original_hook(exc_type, exc_value, exc_tb)
    
    def _save_crash_log(self, exc_type, exc_value, tb_text: str) -> Path:
        """Salva log do crash."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        crash_file = self.log_dir / f"crash_{timestamp}.log"
        
        with open(crash_file, "w", encoding="utf-8") as f:
            f.write(f"AutoTabloide AI - Crash Report\n")
            f.write(f"{'=' * 50}\n")
            f.write(f"Timestamp: {datetime.now().isoformat()}\n")
            f.write(f"Exception Type: {exc_type.__name__}\n")
            f.write(f"Message: {exc_value}\n")
            f.write(f"\n{'=' * 50}\n")
            f.write(f"Traceback:\n{tb_text}\n")
        
        logger.error(f"[Crash] Log salvo em: {crash_file}")
        return crash_file
    
    def _show_crash_dialog(self, exc_type, exc_value, crash_file: Path):
        """Mostra diálogo de crash."""
        app = QApplication.instance()
        if app is None:
            return
        
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Critical)
        msg.setWindowTitle("AutoTabloide AI - Erro Fatal")
        msg.setText(f"Ocorreu um erro inesperado:\n\n{exc_type.__name__}: {exc_value}")
        msg.setInformativeText(f"Um log de diagnóstico foi salvo em:\n{crash_file}")
        msg.setStandardButtons(QMessageBox.Close)
        msg.exec()


# =============================================================================
# APP SETTINGS SINGLETON (Passo 11)
# =============================================================================

@dataclass
class AppSettings:
    """
    Singleton de configurações da aplicação.
    Acessa settings.json e persiste alterações.
    """
    
    # Paths
    system_root: Path = field(default_factory=lambda: Path("AutoTabloide_System_Root"))
    
    # Aparência
    theme: str = "dark"
    font_size: int = 12
    
    # Exportação
    default_dpi: int = 300
    default_format: str = "pdf"
    cmyk_enabled: bool = True
    icc_profile: str = "CoatedFOGRA39.icc"
    
    # IA
    ai_enabled: bool = True
    ai_model_path: str = ""
    gpu_acceleration: bool = True
    
    # Comportamento
    autosave_enabled: bool = True
    autosave_interval_sec: int = 60
    confirm_on_exit: bool = True
    
    # Rede
    offline_mode: bool = False
    proxy_enabled: bool = False
    proxy_url: str = ""
    
    # Avançado
    debug_mode: bool = False
    max_undo_steps: int = 50
    thumbnail_cache_size: int = 500
    
    _instance: Optional['AppSettings'] = None
    
    @classmethod
    def instance(cls) -> 'AppSettings':
        """Retorna singleton."""
        if cls._instance is None:
            cls._instance = cls()
            cls._instance._load()
        return cls._instance
    
    @classmethod
    def get(cls, key: str, default: Any = None) -> Any:
        """Acesso rápido a configuração."""
        inst = cls.instance()
        return getattr(inst, key, default)
    
    @classmethod
    def set(cls, key: str, value: Any):
        """Define configuração."""
        inst = cls.instance()
        if hasattr(inst, key):
            setattr(inst, key, value)
            inst._save()
    
    def _load(self):
        """Carrega do settings.json."""
        config_file = self.system_root / "config" / "settings.json"
        
        if not config_file.exists():
            logger.info("[Settings] Arquivo não existe, usando defaults")
            return
        
        try:
            with open(config_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            for key, value in data.items():
                if hasattr(self, key) and not key.startswith("_"):
                    setattr(self, key, value)
            
            logger.info(f"[Settings] Carregado de {config_file}")
        except Exception as e:
            logger.error(f"[Settings] Erro ao carregar: {e}")
    
    def _save(self):
        """Salva para settings.json."""
        config_dir = self.system_root / "config"
        config_dir.mkdir(parents=True, exist_ok=True)
        config_file = config_dir / "settings.json"
        
        try:
            data = {}
            for key in dir(self):
                if not key.startswith("_") and not callable(getattr(self, key)):
                    value = getattr(self, key)
                    if isinstance(value, Path):
                        value = str(value)
                    data[key] = value
            
            with open(config_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            logger.debug(f"[Settings] Salvo em {config_file}")
        except Exception as e:
            logger.error(f"[Settings] Erro ao salvar: {e}")
    
    def to_dict(self) -> Dict[str, Any]:
        """Retorna como dicionário."""
        return {
            "theme": self.theme,
            "font_size": self.font_size,
            "default_dpi": self.default_dpi,
            "default_format": self.default_format,
            "cmyk_enabled": self.cmyk_enabled,
            "ai_enabled": self.ai_enabled,
            "gpu_acceleration": self.gpu_acceleration,
            "autosave_enabled": self.autosave_enabled,
            "autosave_interval_sec": self.autosave_interval_sec,
            "offline_mode": self.offline_mode,
            "debug_mode": self.debug_mode,
        }
    
    def reset_to_defaults(self):
        """Reseta para valores padrão."""
        defaults = AppSettings()
        for key in dir(defaults):
            if not key.startswith("_") and not callable(getattr(defaults, key)):
                setattr(self, key, getattr(defaults, key))
        self._save()


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def install_exception_hook(log_dir: Path = None):
    """Instala o hook de exceção global."""
    return GlobalExceptionHandler.install(log_dir)


def get_settings() -> AppSettings:
    """Acesso global ao settings."""
    return AppSettings.instance()


def get_setting(key: str, default: Any = None) -> Any:
    """Acesso rápido a uma configuração."""
    return AppSettings.get(key, default)

"""
AutoTabloide AI - Sistema de Logging Industrial
================================================
Conforme Auditoria: Substituir print() por logging estruturado.
Logs rotacionados, níveis semânticos e captura de exceções.
"""

import logging
import logging.handlers
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional
import traceback


class LoggingConfig:
    """Configuração centralizada de logging."""
    
    # Níveis de log por módulo
    MODULE_LEVELS = {
        "VectorEngine": logging.DEBUG,
        "OutputEngine": logging.DEBUG,
        "Sentinel": logging.INFO,
        "Database": logging.INFO,
        "UI": logging.WARNING,
    }
    
    # Formato de mensagem
    FORMAT_CONSOLE = "%(levelname)s | %(name)s | %(message)s"
    FORMAT_FILE = "%(asctime)s | %(levelname)-8s | %(name)-20s | %(message)s"
    FORMAT_DATE = "%Y-%m-%d %H:%M:%S"
    
    # Rotação de arquivos
    MAX_BYTES = 10 * 1024 * 1024  # 10MB
    BACKUP_COUNT = 5


def setup_logging(
    log_dir: Path,
    level: int = logging.INFO,
    console_output: bool = True,
    file_output: bool = True
) -> logging.Logger:
    """
    Configura o sistema de logging da aplicação.
    
    Args:
        log_dir: Diretório para arquivos de log
        level: Nível mínimo de log (INFO padrão)
        console_output: Se deve logar no console
        file_output: Se deve logar em arquivo
        
    Returns:
        Logger raiz configurado
    """
    # Criar diretório se não existir
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # Logger raiz
    root_logger = logging.getLogger("AutoTabloide")
    root_logger.setLevel(level)
    
    # Limpar handlers existentes
    root_logger.handlers.clear()
    
    # Handler de console (stderr colorido)
    if console_output:
        console_handler = logging.StreamHandler(sys.stderr)
        console_handler.setLevel(level)
        console_handler.setFormatter(
            ColoredFormatter(LoggingConfig.FORMAT_CONSOLE)
        )
        root_logger.addHandler(console_handler)
    
    # Handler de arquivo rotacionado
    if file_output:
        log_file = log_dir / f"autotabloide_{datetime.now():%Y-%m-%d}.log"
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=LoggingConfig.MAX_BYTES,
            backupCount=LoggingConfig.BACKUP_COUNT,
            encoding="utf-8"
        )
        file_handler.setLevel(logging.DEBUG)  # Arquivo captura tudo
        file_handler.setFormatter(
            logging.Formatter(
                LoggingConfig.FORMAT_FILE,
                datefmt=LoggingConfig.FORMAT_DATE
            )
        )
        root_logger.addHandler(file_handler)
    
    # Handler separado para erros críticos
    if file_output:
        error_file = log_dir / "errors.log"
        error_handler = logging.FileHandler(
            error_file,
            mode='a',
            encoding="utf-8"
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(
            logging.Formatter(
                "%(asctime)s | %(name)s\n%(message)s\n" + "=" * 80 + "\n",
                datefmt=LoggingConfig.FORMAT_DATE
            )
        )
        root_logger.addHandler(error_handler)
    
    return root_logger


class ColoredFormatter(logging.Formatter):
    """Formatador com cores ANSI para console."""
    
    COLORS = {
        logging.DEBUG: "\033[36m",      # Cyan
        logging.INFO: "\033[32m",       # Green
        logging.WARNING: "\033[33m",    # Yellow
        logging.ERROR: "\033[31m",      # Red
        logging.CRITICAL: "\033[35m",   # Magenta
    }
    RESET = "\033[0m"
    
    def format(self, record: logging.LogRecord) -> str:
        color = self.COLORS.get(record.levelno, self.RESET)
        record.levelname = f"{color}{record.levelname}{self.RESET}"
        return super().format(record)


def get_logger(name: str) -> logging.Logger:
    """
    Obtém um logger para um módulo específico.
    
    Args:
        name: Nome do módulo (ex: "VectorEngine")
        
    Returns:
        Logger configurado
    """
    logger = logging.getLogger(f"AutoTabloide.{name}")
    
    # Aplicar nível específico do módulo se definido
    if name in LoggingConfig.MODULE_LEVELS:
        logger.setLevel(LoggingConfig.MODULE_LEVELS[name])
    
    return logger


def log_exception(
    logger: logging.Logger,
    message: str,
    exc: Optional[Exception] = None
) -> None:
    """
    Loga uma exceção com traceback completo.
    
    Args:
        logger: Logger a usar
        message: Mensagem descritiva
        exc: Exceção opcional (usa sys.exc_info se não fornecida)
    """
    if exc:
        tb = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))
    else:
        tb = traceback.format_exc()
    
    logger.error(f"{message}\n{tb}")


class LogContext:
    """
    Context manager para logging de operações.
    
    Uso:
        with LogContext(logger, "Renderizando PDF") as log:
            log.info("Página 1 de 10")
            # ... operação
    """
    
    def __init__(
        self, 
        logger: logging.Logger, 
        operation: str,
        level: int = logging.INFO
    ):
        self.logger = logger
        self.operation = operation
        self.level = level
        self.start_time: Optional[datetime] = None
    
    def __enter__(self) -> logging.Logger:
        self.start_time = datetime.now()
        self.logger.log(self.level, f"[INÍCIO] {self.operation}")
        return self.logger
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        elapsed = (datetime.now() - self.start_time).total_seconds()
        
        if exc_type is None:
            self.logger.log(
                self.level, 
                f"[FIM] {self.operation} ({elapsed:.2f}s)"
            )
        else:
            self.logger.error(
                f"[ERRO] {self.operation} ({elapsed:.2f}s): {exc_val}"
            )
        
        return False  # Não suprimir exceções


# Alias para compatibilidade
def setup(log_dir: Path, **kwargs) -> logging.Logger:
    """Alias para setup_logging."""
    return setup_logging(log_dir, **kwargs)

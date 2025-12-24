"""
AutoTabloide AI - Core Package
==============================
Módulos de infraestrutura industrial.
"""

# Utilitários base
from .constants import (
    AppInfo, SystemPaths, DatabaseConfig, RenderConfig,
    Typography, QualityThresholds, AIConfig, UIConfig
)
from .utils import (
    UnitNormalizer, UnitConverter, 
    slugify, safe_filename,
    retry, async_retry,
    CancellationToken, OperationCancelledError,
    LifecycleManager,
    compute_file_hash, compute_string_hash
)
from .container import inject, register, register_instance, ServiceContainer
from .logging_config import setup_logging, get_logger
from .schemas import (
    ProdutoCreate, ProdutoUpdate, ProdutoResponse,
    AISanitizationResult, SlotDataSchema, SettingsSchema
)
from .integrity import IntegrityChecker, SafeModeManager, run_startup_checks
from .event_bus import (
    EventType, Event, EventBus,
    get_event_bus, emit, subscribe,
    on_event, ReactiveComponent
)
from .async_io import (
    read_text, write_text, read_bytes, write_bytes,
    read_json, write_json,
    copy_file, move_file, delete_file, file_exists, list_files
)

__all__ = [
    # Constants
    "AppInfo", "SystemPaths", "DatabaseConfig", "RenderConfig",
    "Typography", "QualityThresholds", "AIConfig", "UIConfig",
    # Utils
    "UnitNormalizer", "UnitConverter",
    "slugify", "safe_filename",
    "retry", "async_retry",
    "CancellationToken", "OperationCancelledError",
    "LifecycleManager",
    "compute_file_hash", "compute_string_hash",
    # Container
    "inject", "register", "register_instance", "ServiceContainer",
    # Logging
    "setup_logging", "get_logger",
    # Schemas
    "ProdutoCreate", "ProdutoUpdate", "ProdutoResponse",
    "AISanitizationResult", "SlotDataSchema", "SettingsSchema",
    # Integrity
    "IntegrityChecker", "SafeModeManager", "run_startup_checks",
    # Event Bus
    "EventType", "Event", "EventBus",
    "get_event_bus", "emit", "subscribe",
    "on_event", "ReactiveComponent",
    # Async IO
    "read_text", "write_text", "read_bytes", "write_bytes",
    "read_json", "write_json",
    "copy_file", "move_file", "delete_file", "file_exists", "list_files",
]

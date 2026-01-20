"""
AutoTabloide AI - Qt Edition (Industrial Grade Entry Point)
============================================================
PROTOCOLO DE CONVERGÊNCIA INDUSTRIAL - 225 Passos
Fase 1: Fundação de Concreto (Passos 1-15)

REGRA DE OURO: Nenhuma UI aparece antes da verificação de integridade.

Versão: 2.0.0 (Industrial Grade)
"""

import sys
import os
import multiprocessing
from pathlib import Path
from typing import Optional, Dict, Tuple, List
from dataclasses import dataclass, field
from datetime import datetime

# === HIGH DPI SCALING (OBRIGATÓRIO para monitores 4K) ===
os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "1"
os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"

# Adiciona src ao path para imports corretos
sys.path.insert(0, str(Path(__file__).parent))

from PySide6.QtWidgets import (
    QApplication, QSplashScreen, QMessageBox, QSystemTrayIcon
)
from PySide6.QtCore import (
    Qt, QTimer, Signal, QObject, QThread, QSharedMemory, QSettings
)
from PySide6.QtGui import QPixmap, QFontDatabase, QFont, QPainter, QColor

# ==============================================================================
# CONSTANTES CRÍTICAS - NÃO MODIFICAR
# ==============================================================================
SYSTEM_ROOT = Path(__file__).parent / "AutoTabloide_System_Root"
VERSION = "2.0.0"

# Diretórios obrigatórios
REQUIRED_DIRS = [
    "bin",
    "bin/models",
    "config", 
    "database",
    "assets/store",
    "assets/profiles",
    "assets/fonts",
    "staging",
    "temp_render",
    "logs",
    "library/svg_source",
    "library/thumbnails",
    "workspace/projects",
    "snapshots",
]

# Fontes obrigatórias
REQUIRED_FONTS = [
    "Roboto-Regular.ttf",
    "Roboto-Bold.ttf",
]

# Binários necessários  
REQUIRED_BINARIES = {
    "ghostscript": ["gswin64c.exe", "gswin32c.exe", "gs"],
    "upscaler": ["realesrgan-ncnn-vulkan.exe", "realesrgan-ncnn-vulkan"],
}

# Perfis ICC
REQUIRED_ICC = [
    "CoatedFOGRA39.icc",
]


@dataclass
class BootReport:
    """Relatório de inicialização do sistema."""
    success: bool = True
    is_safe_mode: bool = False
    directories_ok: bool = False
    fonts_loaded: List[str] = field(default_factory=list)
    fonts_missing: List[str] = field(default_factory=list)
    icc_available: bool = False
    binaries_found: Dict[str, str] = field(default_factory=dict)
    binaries_missing: List[str] = field(default_factory=list)
    database_ok: bool = False
    gpu_available: bool = False
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    repairs: List[str] = field(default_factory=list)


class IndustrialSplashScreen(QSplashScreen):
    """Splash Screen com progresso real de verificação."""
    
    def __init__(self):
        # Cria pixmap base
        pix = QPixmap(500, 300)
        pix.fill(QColor("#0D0D0D"))
        
        # Desenha texto inicial
        painter = QPainter(pix)
        painter.setPen(QColor("#6C5CE7"))
        painter.setFont(QFont("Segoe UI", 24, QFont.Bold))
        painter.drawText(pix.rect(), Qt.AlignCenter, "AutoTabloide AI")
        painter.end()
        
        super().__init__(pix)
        
        self._progress = 0
        self._status = ""
        self._step_count = 15  # Passos da Fase 1
    
    def update_progress(self, step: int, message: str):
        """Atualiza progresso real."""
        self._progress = step
        self._status = message
        
        # Recria pixmap com progresso
        pix = QPixmap(500, 300)
        pix.fill(QColor("#0D0D0D"))
        
        painter = QPainter(pix)
        
        # Título
        painter.setPen(QColor("#6C5CE7"))
        painter.setFont(QFont("Segoe UI", 22, QFont.Bold))
        painter.drawText(20, 50, "AutoTabloide AI")
        
        # Versão
        painter.setPen(QColor("#606060"))
        painter.setFont(QFont("Segoe UI", 10))
        painter.drawText(20, 75, f"v{VERSION} - Industrial Grade")
        
        # Barra de progresso
        bar_x, bar_y = 20, 180
        bar_w, bar_h = 460, 20
        
        # Fundo
        painter.fillRect(bar_x, bar_y, bar_w, bar_h, QColor("#1A1A2E"))
        
        # Progresso
        progress_w = int((step / self._step_count) * bar_w)
        painter.fillRect(bar_x, bar_y, progress_w, bar_h, QColor("#6C5CE7"))
        
        # Texto do passo
        painter.setPen(QColor("#FFFFFF"))
        painter.setFont(QFont("Segoe UI", 11))
        painter.drawText(20, 220, f"[{step}/{self._step_count}] {message}")
        
        # Porcentagem
        pct = int((step / self._step_count) * 100)
        painter.drawText(440, 220, f"{pct}%")
        
        painter.end()
        
        self.setPixmap(pix)
        self.repaint()
        QApplication.processEvents()


class SingleInstanceLock:
    """
    Passo 9: Lock de instância única.
    Impede múltiplas instâncias do Autotabloide (conflito de DB).
    """
    
    def __init__(self, key: str = "AutoTabloide_AI_SingleInstance"):
        self._shared_memory = QSharedMemory(key)
        self._locked = False
    
    def try_lock(self) -> bool:
        """Tenta obter lock. Retorna False se outra instância está rodando."""
        # Limpa memória órfã (crash anterior)
        if self._shared_memory.attach():
            self._shared_memory.detach()
        
        # Tenta criar novo
        if self._shared_memory.create(1):
            self._locked = True
            return True
        
        return False
    
    def release(self):
        """Libera o lock."""
        if self._locked and self._shared_memory.isAttached():
            self._shared_memory.detach()
            self._locked = False


class GlobalSignals(QObject):
    """
    Passo 13: Sinais globais para eventos de sistema.
    Permite que qualquer parte da UI reaja a eventos críticos.
    """
    
    # Sinais de sistema
    database_error = Signal(str)
    database_connected = Signal()
    internet_lost = Signal()
    internet_restored = Signal()
    
    # Sinais do Sentinel
    sentinel_started = Signal()
    sentinel_stopped = Signal()
    sentinel_busy = Signal(str)  # Descrição da tarefa
    sentinel_idle = Signal()
    
    # Sinais de renderização
    render_started = Signal(str)
    render_progress = Signal(int, int)  # atual, total
    render_completed = Signal(str)
    render_failed = Signal(str)
    
    _instance: Optional['GlobalSignals'] = None
    
    @classmethod
    def instance(cls) -> 'GlobalSignals':
        if cls._instance is None:
            cls._instance = GlobalSignals()
        return cls._instance


class DatabaseWorker(QObject):
    """
    Passo 12: Worker dedicado para operações de banco.
    NUNCA execute queries na thread principal (GUI).
    """
    
    result_ready = Signal(object)
    error = Signal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._session = None
    
    async def _get_session(self):
        """Obtém sessão async do banco."""
        if self._session is None:
            from src.core.database import get_db
            async with get_db() as session:
                return session
        return self._session


def ensure_directories(splash: IndustrialSplashScreen) -> Tuple[bool, List[str]]:
    """
    Passo 2: Verifica e cria estrutura de diretórios.
    """
    splash.update_progress(1, "Verificando estrutura de diretórios...")
    
    errors = []
    for dir_rel in REQUIRED_DIRS:
        dir_path = SYSTEM_ROOT / dir_rel
        try:
            dir_path.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            errors.append(f"Falha ao criar {dir_rel}: {e}")
    
    return len(errors) == 0, errors


def run_integrity_check(splash: IndustrialSplashScreen) -> Tuple[bool, bool, List[str]]:
    """
    Passo 2: Executa IntegrityChecker completo.
    """
    splash.update_progress(2, "Executando verificação de integridade...")
    
    try:
        from src.core.integrity import IntegrityChecker, SafeModeManager
        
        checker = IntegrityChecker(SYSTEM_ROOT)
        success, messages = checker.run_full_check(auto_repair=True)
        
        safe_mode_mgr = SafeModeManager(SYSTEM_ROOT)
        is_safe_mode = safe_mode_mgr.is_safe_mode()
        
        if success:
            safe_mode_mgr.record_success()
        
        return success, is_safe_mode, messages
        
    except Exception as e:
        return False, False, [f"Erro na verificação: {e}"]


def validate_write_permissions(splash: IndustrialSplashScreen) -> Tuple[bool, List[str]]:
    """
    Passo 3: Valida permissões de escrita.
    """
    splash.update_progress(3, "Validando permissões de escrita...")
    
    try:
        from src.core.boot_safety import WritePermissionValidator
        
        success, errors = WritePermissionValidator.validate_all(SYSTEM_ROOT)
        return success, errors
        
    except Exception as e:
        return False, [f"Erro na validação: {e}"]


def load_fonts(splash: IndustrialSplashScreen) -> Tuple[List[str], List[str]]:
    """
    Passo 4: Carrega fontes do System Root no QFontDatabase.
    """
    splash.update_progress(4, "Carregando fontes tipográficas...")
    
    fonts_dir = SYSTEM_ROOT / "assets" / "fonts"
    loaded = []
    missing = []
    
    # Verifica fontes obrigatórias
    for font_name in REQUIRED_FONTS:
        font_path = fonts_dir / font_name
        if font_path.exists():
            font_id = QFontDatabase.addApplicationFont(str(font_path))
            if font_id >= 0:
                loaded.append(font_name)
            else:
                missing.append(f"{font_name} (corrompida)")
        else:
            missing.append(font_name)
    
    # Carrega fontes adicionais
    if fonts_dir.exists():
        for font_file in fonts_dir.glob("*.ttf"):
            if font_file.name not in REQUIRED_FONTS:
                font_id = QFontDatabase.addApplicationFont(str(font_file))
                if font_id >= 0:
                    loaded.append(font_file.name)
    
    return loaded, missing


def validate_icc_profiles(splash: IndustrialSplashScreen) -> bool:
    """
    Passo 5: Valida perfis ICC para CMYK.
    """
    splash.update_progress(5, "Validando perfis de cor ICC...")
    
    profiles_dir = SYSTEM_ROOT / "assets" / "profiles"
    
    for icc_name in REQUIRED_ICC:
        icc_path = profiles_dir / icc_name
        if not icc_path.exists():
            return False
    
    return True


def validate_binaries(splash: IndustrialSplashScreen) -> Tuple[Dict[str, str], List[str]]:
    """
    Passo 6: Valida binários externos (Ghostscript, ESRGAN).
    """
    splash.update_progress(6, "Validando binários externos...")
    
    bin_dir = SYSTEM_ROOT / "bin"
    found = {}
    missing = []
    
    for tool_name, candidates in REQUIRED_BINARIES.items():
        tool_found = False
        for candidate in candidates:
            tool_path = bin_dir / candidate
            if tool_path.exists():
                found[tool_name] = str(tool_path)
                tool_found = True
                break
        
        if not tool_found:
            missing.append(tool_name)
    
    return found, missing


def load_settings(splash: IndustrialSplashScreen) -> Dict:
    """
    Passo 7: Carrega settings.json em singleton.
    """
    splash.update_progress(7, "Carregando configurações...")
    
    settings_path = SYSTEM_ROOT / "config" / "settings.json"
    
    try:
        if settings_path.exists():
            import json
            with open(settings_path, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        print(f"[Settings] Erro ao carregar: {e}")
    
    return {}


def setup_logging(splash: IndustrialSplashScreen):
    """
    Passo 8: Configura logging centralizado.
    """
    splash.update_progress(8, "Configurando sistema de logs...")
    
    import logging
    
    log_dir = SYSTEM_ROOT / "logs"
    log_file = log_dir / f"autotabloide_{datetime.now():%Y%m%d}.log"
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
        handlers=[
            logging.FileHandler(str(log_file), encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )


def check_single_instance(splash: IndustrialSplashScreen) -> bool:
    """
    Passo 9: Verifica instância única.
    """
    splash.update_progress(9, "Verificando instância única...")
    
    lock = SingleInstanceLock()
    return lock.try_lock()


def detect_gpu(splash: IndustrialSplashScreen) -> bool:
    """
    Passo 10: Detecta GPU/Vulkan disponível.
    """
    splash.update_progress(10, "Detectando hardware GPU...")
    
    try:
        # Tenta verificar CUDA
        import subprocess
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=name", "--format=csv,noheader"],
            capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0 and result.stdout.strip():
            return True
    except:
        pass
    
    return False


async def init_database(splash: IndustrialSplashScreen) -> bool:
    """
    Passo 11: Inicializa engine do SQLAlchemy.
    """
    splash.update_progress(11, "Inicializando banco de dados...")
    
    try:
        from src.core.database import init_db
        await init_db()
        return True
    except Exception as e:
        print(f"[Database] Erro: {e}")
        return False


def setup_database_worker(splash: IndustrialSplashScreen):
    """
    Passo 12: Cria thread dedicada para database.
    """
    splash.update_progress(12, "Configurando worker de banco...")
    
    # Worker será criado sob demanda


def init_global_signals(splash: IndustrialSplashScreen):
    """
    Passo 13: Inicializa sinais globais.
    """
    splash.update_progress(13, "Inicializando sinais globais...")
    
    GlobalSignals.instance()


def setup_shortcuts(splash: IndustrialSplashScreen):
    """
    Passo 14: Prepara mapeamento de atalhos.
    """
    splash.update_progress(14, "Configurando atalhos de teclado...")
    
    # Atalhos serão registrados na MainWindow


def apply_master_style(app: QApplication, splash: IndustrialSplashScreen, settings: Dict):
    """
    Passo 15: Aplica estilo mestre com variáveis de settings.
    """
    splash.update_progress(15, "Aplicando tema visual...")
    
    try:
        from src.qt.theme import apply_theme
        apply_theme(app)
    except Exception as e:
        print(f"[Theme] Erro: {e}")


def run_boot_sequence(app: QApplication) -> BootReport:
    """
    Executa sequência completa de boot (Passos 1-15).
    """
    report = BootReport()
    
    # Cria splash
    splash = IndustrialSplashScreen()
    splash.show()
    app.processEvents()
    
    try:
        # Passo 1-2: Diretórios e Integridade
        dirs_ok, dir_errors = ensure_directories(splash)
        report.directories_ok = dirs_ok
        if not dirs_ok:
            report.errors.extend(dir_errors)
        
        integrity_ok, is_safe, messages = run_integrity_check(splash)
        report.is_safe_mode = is_safe
        if not integrity_ok:
            report.warnings.extend(messages)
        else:
            report.repairs.extend(messages)
        
        # Passo 3: Permissões
        perms_ok, perm_errors = validate_write_permissions(splash)
        if not perms_ok:
            report.errors.extend(perm_errors)
        
        # Passo 4: Fontes
        loaded, missing = load_fonts(splash)
        report.fonts_loaded = loaded
        report.fonts_missing = missing
        if missing and any(f in REQUIRED_FONTS for f in missing):
            report.warnings.append(f"Fontes críticas ausentes: {missing}")
        
        # Passo 5: ICC
        report.icc_available = validate_icc_profiles(splash)
        if not report.icc_available:
            report.warnings.append("Perfis ICC ausentes - exportação CMYK limitada")
        
        # Passo 6: Binários
        found, missing = validate_binaries(splash)
        report.binaries_found = found
        report.binaries_missing = missing
        if "ghostscript" in missing:
            report.warnings.append("Ghostscript ausente - exportação PDF limitada")
        
        # Passo 7: Settings
        settings = load_settings(splash)
        
        # Passo 8: Logging
        setup_logging(splash)
        
        # Passo 9: Instância única
        if not check_single_instance(splash):
            report.errors.append("Outra instância do Autotabloide está rodando")
            report.success = False
        
        # Passo 10: GPU
        report.gpu_available = detect_gpu(splash)
        
        # Passo 11: Database (sync wrapper)
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            report.database_ok = loop.run_until_complete(init_database(splash))
            
            # Passo 11b: Seed database with demo products if empty
            if report.database_ok:
                splash.update_progress(11, "Verificando dados iniciais...")
                try:
                    from src.core.seed_data import seed_database
                    loop2 = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop2)
                    loop2.run_until_complete(seed_database())
                    loop2.close()
                except Exception as seed_err:
                    print(f"[Seed] Aviso: {seed_err}")
                    
        except Exception as e:
            report.database_ok = False
            report.warnings.append(f"Banco de dados: {e}")
        finally:
            loop.close()
        
        # Passo 12-13: Workers e Signals
        setup_database_worker(splash)
        init_global_signals(splash)
        
        # Passo 14: Shortcuts (preparação)
        setup_shortcuts(splash)
        
        # Passo 15: Estilo
        apply_master_style(app, splash, settings)
        
        # Fecha splash
        splash.finish(None)
        
        # Avalia resultado
        if report.errors:
            report.success = False
        
        return report
        
    except Exception as e:
        splash.finish(None)
        report.success = False
        report.errors.append(f"Erro fatal no boot: {e}")
        return report


def show_boot_errors(report: BootReport):
    """Mostra diálogo com erros/warnings do boot."""
    if report.errors:
        msg = "ERROS CRÍTICOS:\n" + "\n".join(f"• {e}" for e in report.errors)
        if report.warnings:
            msg += "\n\nAVISOS:\n" + "\n".join(f"• {w}" for w in report.warnings)
        
        QMessageBox.critical(None, "Falha na Inicialização", msg)
    
    elif report.warnings:
        msg = "Avisos:\n" + "\n".join(f"• {w}" for w in report.warnings)
        QMessageBox.warning(None, "Inicialização com Avisos", msg)


def main():
    """Entry point industrial da aplicação Qt."""
    
    # Multiprocessing fix para Windows
    multiprocessing.freeze_support()
    
    # Cria aplicação
    app = QApplication(sys.argv)
    app.setApplicationName("AutoTabloide AI")
    app.setApplicationVersion(VERSION)
    app.setOrganizationName("AutoTabloide")
    
    # === BOOT SEQUENCE (Passos 1-15) ===
    report = run_boot_sequence(app)
    
    # Verifica resultado
    if not report.success:
        show_boot_errors(report)
        if report.errors:
            return 1
    elif report.warnings:
        show_boot_errors(report)
    
    # Log do boot
    print(f"[Boot] Concluído - Fontes: {len(report.fonts_loaded)}, "
          f"GPU: {report.gpu_available}, DB: {report.database_ok}")
    
    # === CRIA JANELA PRINCIPAL ===
    try:
        from qasync import QEventLoop
        ASYNC_AVAILABLE = True
    except ImportError:
        ASYNC_AVAILABLE = False
    
    from src.qt.main_window import MainWindow
    from src.qt.bridge import GlobalExceptionHandler, UIWatchdog, setup_async_qt_loop
    
    # Handler de exceções
    exception_handler = GlobalExceptionHandler(app)
    
    # Event loop híbrido
    loop = setup_async_qt_loop(app) if ASYNC_AVAILABLE else None
    
    # Janela principal
    from src.core.container import get_container
    window = MainWindow(container=get_container())
    
    # Injeta report de boot
    window.boot_report = report
    
    # === INTEGRAÇÃO DOS NOVOS MÓDULOS ===
    
    # GlobalKeyFilter para atalhos globais (Ctrl+1-6, Ctrl+S, etc)
    try:
        from src.qt.core.global_input import GlobalKeyFilter, get_signals
        
        key_filter = GlobalKeyFilter.install(app)
        
        # Conecta atalhos à janela
        from src.qt.core.undo_redo import get_undo_manager
        
        key_filter.save_requested.connect(window.save_project if hasattr(window, 'save_project') else lambda: None)
        key_filter.undo_requested.connect(get_undo_manager().undo)
        key_filter.redo_requested.connect(get_undo_manager().redo)
        key_filter.help_requested.connect(lambda: (
            __import__('src.qt.dialogs.help_system', fromlist=['show_shortcuts_dialog']).show_shortcuts_dialog(window)
        ))
        key_filter.navigate_requested.connect(
            lambda idx: window.switch_view(idx) if hasattr(window, 'switch_view') else None
        )
        
        print("[Main] GlobalKeyFilter instalado")
    except ImportError as e:
        print(f"[Main] GlobalKeyFilter não disponível: {e}")
    
    # Watchdog
    watchdog = UIWatchdog(threshold_ms=200, parent=window)
    watchdog.lag_detected.connect(
        lambda ms: print(f"[Watchdog] UI lag: {ms}ms")
    )
    watchdog.start()
    
    # Mostra janela
    window.show()
    
    # Atualiza status
    status_parts = []
    if report.database_ok:
        status_parts.append("DB Online")
    if report.gpu_available:
        status_parts.append("GPU Detectada")
    if report.is_safe_mode:
        status_parts.append("SAFE MODE")
    
    window.statusBar().showMessage(" | ".join(status_parts) or "Sistema pronto")
    
    # Event loop
    if ASYNC_AVAILABLE and loop:
        with loop:
            try:
                loop.run_forever()
            except KeyboardInterrupt:
                pass
        return 0
    else:
        return app.exec()


if __name__ == "__main__":
    sys.exit(main())

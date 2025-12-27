"""
AutoTabloide AI - Qt Edition (Entry Point)
============================================
Aplicação principal usando PySide6 com integração asyncio via qasync.

Versão: 2.0.0 (Qt Migration)
"""

import sys
import os
import asyncio
from pathlib import Path

# === HIGH DPI SCALING (OBRIGATÓRIO para monitores 4K) ===
os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "1"
os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"

# Adiciona src ao path para imports corretos
sys.path.insert(0, str(Path(__file__).parent))

from PySide6.QtWidgets import QApplication, QSplashScreen
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QPixmap, QFont, QFontDatabase

# Tenta importar qasync para integração async
try:
    from qasync import QEventLoop
    ASYNC_AVAILABLE = True
except ImportError:
    ASYNC_AVAILABLE = False
    print("[AVISO] qasync não instalado. Funcionalidade async limitada.")

from src.qt.theme import apply_theme
from src.qt.main_window import MainWindow
from src.qt.bridge import (
    QtEventBusBridge, GlobalExceptionHandler, UIWatchdog,
    setup_async_qt_loop
)


async def bootstrap_app(window: MainWindow):
    """
    Inicializa serviços do backend de forma assíncrona.
    Chamado após a janela abrir para não bloquear startup.
    """
    try:
        # Registra serviços no container
        from src.core.container import get_container, bootstrap_services
        
        container = get_container()
        await bootstrap_services()
        
        # Injeta container na MainWindow
        window.container = container
        
        # Conecta EventBus
        window.event_bridge.connect_to_event_bus()
        
        print("[Bootstrap] Serviços inicializados com sucesso")
        window.statusBar().showMessage("Sistema pronto | Backend conectado")
        
    except Exception as e:
        print(f"[Bootstrap] Erro ao inicializar serviços: {e}")
        window.statusBar().showMessage(f"Aviso: Backend parcialmente carregado")


def create_splash() -> QSplashScreen:
    """Cria splash screen de loading."""
    splash_pix = QPixmap(400, 200)
    splash_pix.fill(Qt.black)
    
    splash = QSplashScreen(splash_pix)
    splash.setStyleSheet("""
        QSplashScreen {
            background-color: #0D0D0D;
            color: #6C5CE7;
            font-size: 18px;
            font-weight: bold;
        }
    """)
    splash.showMessage(
        "AutoTabloide AI v2.0.0\nCarregando...",
        Qt.AlignCenter,
        Qt.white
    )
    return splash


def main():
    """Entry point da aplicação Qt com suporte asyncio."""
    
    # Cria aplicação
    app = QApplication(sys.argv)
    
    # Configura nome da aplicação
    app.setApplicationName("AutoTabloide AI")
    app.setApplicationVersion("2.0.0")
    app.setOrganizationName("AutoTabloide")
    
    # Carrega fontes customizadas se disponíveis
    fonts_dir = Path(__file__).parent / "assets" / "fonts"
    if fonts_dir.exists():
        for font_file in fonts_dir.glob("*.ttf"):
            QFontDatabase.addApplicationFont(str(font_file))
    
    # Aplica Dark Theme
    apply_theme(app)
    
    # Handler global de exceções
    exception_handler = GlobalExceptionHandler(app)
    
    # Configura event loop híbrido (Qt + asyncio)
    if ASYNC_AVAILABLE:
        loop = setup_async_qt_loop(app)
    else:
        loop = None
    
    # Splash screen (opcional)
    # splash = create_splash()
    # splash.show()
    # app.processEvents()
    
    # Cria janela principal
    window = MainWindow(container=None)
    
    # EventBus Bridge
    window.event_bridge = QtEventBusBridge(window)
    
    # UI Watchdog (monitora travamentos)
    watchdog = UIWatchdog(threshold_ms=200, parent=window)
    watchdog.lag_detected.connect(
        lambda ms: print(f"[Watchdog] UI lag: {ms}ms")
    )
    watchdog.start()
    
    # Mostra janela
    window.show()
    
    # Bootstrap assíncrono após janela abrir
    if ASYNC_AVAILABLE:
        QTimer.singleShot(100, lambda: loop.create_task(bootstrap_app(window)))
    else:
        # Fallback síncrono (funcionalidade limitada)
        QTimer.singleShot(100, lambda: print("[Info] Backend async não disponível"))
    
    # Loop de eventos
    if ASYNC_AVAILABLE:
        with loop:
            loop.run_forever()
        return 0
    else:
        return app.exec()


if __name__ == "__main__":
    sys.exit(main())

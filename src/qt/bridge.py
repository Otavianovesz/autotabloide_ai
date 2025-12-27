"""
AutoTabloide AI - Qt/Async Bridge
==================================
Integração do asyncio com Qt Event Loop via qasync.
Ponte entre backend async e frontend síncrono.
"""

import sys
import asyncio
from typing import Optional, Callable, Any
from functools import wraps

from PySide6.QtWidgets import QApplication, QMessageBox
from PySide6.QtCore import QObject, Signal, Slot, QTimer

try:
    from qasync import QEventLoop, asyncSlot, asyncClose
    QASYNC_AVAILABLE = True
except ImportError:
    QASYNC_AVAILABLE = False
    QEventLoop = None
    asyncSlot = lambda: lambda f: f
    asyncClose = lambda f: f


class QtEventBusBridge(QObject):
    """
    Ponte entre EventBus Python e Signals Qt.
    
    Escuta eventos do backend e emite Signals para a UI.
    """
    
    # Signals para eventos de backend
    product_created = Signal(dict)
    product_updated = Signal(int, dict)
    product_deleted = Signal(int)
    
    import_started = Signal(str)  # filename
    import_progress = Signal(int, int, str)  # current, total, message
    import_completed = Signal(int, int)  # success, errors
    
    render_started = Signal(str)  # job_id
    render_progress = Signal(str, int, str)  # job_id, percent, message
    render_completed = Signal(str, str)  # job_id, output_path
    render_error = Signal(str, str)  # job_id, error_message
    
    sentinel_status = Signal(bool, str)  # active, message
    sentinel_llm_loaded = Signal(bool)
    sentinel_response = Signal(str, str)  # request_id, response
    
    settings_changed = Signal(str)  # key that changed (or "all")
    
    database_error = Signal(str)
    network_status = Signal(bool)  # online/offline
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._subscriptions = []
    
    def connect_to_event_bus(self):
        """Conecta ao EventBus do backend."""
        try:
            from src.core.event_bus import get_event_bus, Events
            
            bus = get_event_bus()
            
            # Mapeia eventos do backend para Signals Qt
            self._subscribe(bus, Events.PRODUCT_CREATED, self._on_product_created)
            self._subscribe(bus, Events.PRODUCT_UPDATED, self._on_product_updated)
            self._subscribe(bus, Events.PRODUCT_DELETED, self._on_product_deleted)
            
            print("[QtEventBusBridge] Conectado ao EventBus do backend")
            
        except ImportError as e:
            print(f"[QtEventBusBridge] EventBus não disponível: {e}")
    
    def _subscribe(self, bus, event, handler):
        """Registra subscription."""
        bus.subscribe(event, handler)
        self._subscriptions.append((bus, event, handler))
    
    def disconnect_all(self):
        """Desconecta todos os listeners."""
        for bus, event, handler in self._subscriptions:
            try:
                bus.unsubscribe(event, handler)
            except Exception:
                pass
        self._subscriptions.clear()
    
    # Handlers que convertem eventos Python → Signals Qt
    def _on_product_created(self, data: dict):
        self.product_created.emit(data)
    
    def _on_product_updated(self, product_id: int, data: dict):
        self.product_updated.emit(product_id, data)
    
    def _on_product_deleted(self, product_id: int):
        self.product_deleted.emit(product_id)


class AsyncTaskRunner(QObject):
    """
    Executa coroutines async de forma segura na Thread Qt.
    
    Uso:
        runner = AsyncTaskRunner()
        runner.run_async(my_coroutine(), on_success, on_error)
    """
    
    finished = Signal(object)  # resultado
    error = Signal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
    
    def run_async(
        self, 
        coro, 
        on_success: Optional[Callable] = None,
        on_error: Optional[Callable] = None
    ):
        """
        Agenda coroutine para execução.
        
        Args:
            coro: Coroutine async
            on_success: Callback com resultado
            on_error: Callback com mensagem de erro
        """
        async def wrapper():
            try:
                result = await coro
                if on_success:
                    on_success(result)
                self.finished.emit(result)
            except Exception as e:
                error_msg = str(e)
                if on_error:
                    on_error(error_msg)
                self.error.emit(error_msg)
        
        # Agenda no event loop
        loop = asyncio.get_event_loop()
        loop.create_task(wrapper())


class GlobalExceptionHandler:
    """
    Captura exceções não tratadas e mostra diálogos amigáveis.
    """
    
    def __init__(self, app: QApplication):
        self.app = app
        self._original_hook = sys.excepthook
        sys.excepthook = self._handle_exception
    
    def _handle_exception(self, exc_type, exc_value, exc_tb):
        """Handler global de exceções."""
        # Log detalhado para debug
        import traceback
        error_details = ''.join(traceback.format_exception(exc_type, exc_value, exc_tb))
        
        # Safe print (Windows console encoding)
        try:
            print(f"[ERRO CRITICO]\n{error_details}")
        except UnicodeEncodeError:
            print("[ERRO CRITICO] (detalhes omitidos por encoding)")
        
        # Mensagem amigável para o usuário
        error_map = {
            ValueError: "Valor inválido. Verifique os dados inseridos.",
            FileNotFoundError: "Arquivo não encontrado. Verifique o caminho.",
            PermissionError: "Sem permissão para acessar o recurso.",
            ConnectionError: "Erro de conexão. Verifique sua rede.",
            TimeoutError: "Operação expirou. Tente novamente.",
        }
        
        user_message = error_map.get(exc_type, f"Erro inesperado: {exc_value}")
        
        # Mostra dialog se a aplicação estiver rodando
        try:
            QMessageBox.critical(
                None,
                "Erro Industrial",
                f"{user_message}\n\n"
                f"Tipo: {exc_type.__name__}\n"
                f"Detalhes: {exc_value}",
                QMessageBox.Ok
            )
        except Exception:
            pass
        
        # Não encerra o app, deixa continuar
        # Chama hook original para logging adicional se necessário
        # self._original_hook(exc_type, exc_value, exc_tb)
    
    def restore(self):
        """Restaura exception hook original."""
        sys.excepthook = self._original_hook


class UIWatchdog(QObject):
    """
    Monitora responsividade da UI.
    Detecta travamentos e loga avisos.
    """
    
    lag_detected = Signal(int)  # ms de lag
    
    def __init__(self, threshold_ms: int = 200, parent=None):
        super().__init__(parent)
        self.threshold_ms = threshold_ms
        self._last_tick = 0
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._check)
    
    def start(self, interval_ms: int = 100):
        """Inicia monitoramento."""
        import time
        self._last_tick = time.time() * 1000
        self._timer.start(interval_ms)
    
    def stop(self):
        """Para monitoramento."""
        self._timer.stop()
    
    @Slot()
    def _check(self):
        """Verifica latência."""
        import time
        now = time.time() * 1000
        elapsed = now - self._last_tick
        
        if elapsed > self.threshold_ms + 100:  # 100ms de tolerância
            lag = int(elapsed - 100)
            try:
                print(f"[UIWatchdog] AVISO: Lag detectado: {lag}ms")
            except UnicodeEncodeError:
                pass  # Ignora erro de encoding no console
            self.lag_detected.emit(lag)
        
        self._last_tick = now


def setup_async_qt_loop(app: QApplication) -> asyncio.AbstractEventLoop:
    """
    Configura event loop híbrido Qt/asyncio.
    
    Args:
        app: QApplication instance
        
    Returns:
        Event loop configurado
    """
    if not QASYNC_AVAILABLE:
        raise RuntimeError("qasync não está instalado. Execute: pip install qasync")
    
    loop = QEventLoop(app)
    asyncio.set_event_loop(loop)
    
    return loop


def run_async_in_qt(coro):
    """
    Decorator para executar coroutine async em método Qt.
    
    Uso:
        @run_async_in_qt
        async def load_data(self):
            data = await fetch_data()
            self.update_ui(data)
    """
    if QASYNC_AVAILABLE:
        return asyncSlot()(coro)
    else:
        @wraps(coro)
        def wrapper(*args, **kwargs):
            print("[AVISO] qasync não disponível, executando sync")
            import asyncio
            return asyncio.run(coro(*args, **kwargs))
        return wrapper

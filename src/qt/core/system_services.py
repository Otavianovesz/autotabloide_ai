"""
AutoTabloide AI - Network Watcher & System Tray
================================================
PROTOCOLO DE RETIFICAÇÃO NÍVEL 0 - Fase 1/6 (Passos 20, 208)
Monitoramento de rede e ícone na bandeja do sistema.
"""

from __future__ import annotations
from typing import Optional
import logging
import socket

from PySide6.QtCore import Qt, Signal, Slot, QTimer, QThread
from PySide6.QtWidgets import (
    QSystemTrayIcon, QMenu, QApplication
)
from PySide6.QtGui import QIcon, QPixmap, QPainter, QColor

logger = logging.getLogger("Network")


# =============================================================================
# NETWORK WATCHER
# =============================================================================

class NetworkWatcher(QThread):
    """
    Monitora conectividade de rede em background.
    Testa conexão a intervalos regulares.
    """
    
    status_changed = Signal(bool)  # online/offline
    
    def __init__(self, check_interval: int = 30, parent=None):
        super().__init__(parent)
        self._check_interval = check_interval
        self._running = True
        self._last_status = None
        
        # Hosts para teste (redundância)
        self._test_hosts = [
            ("8.8.8.8", 53),        # Google DNS
            ("1.1.1.1", 53),        # Cloudflare DNS
            ("208.67.222.222", 53), # OpenDNS
        ]
    
    def run(self):
        """Loop de verificação."""
        while self._running:
            status = self._check_connectivity()
            
            # Emite apenas se mudou
            if status != self._last_status:
                self._last_status = status
                self.status_changed.emit(status)
                
                if status:
                    logger.info("[Network] Online")
                else:
                    logger.warning("[Network] Offline")
            
            # Aguarda próximo check
            self.msleep(self._check_interval * 1000)
    
    def _check_connectivity(self) -> bool:
        """Testa conexão TCP a hosts conhecidos."""
        for host, port in self._test_hosts:
            try:
                socket.setdefaulttimeout(3)
                socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((host, port))
                return True
            except socket.error:
                continue
        return False
    
    def stop(self):
        """Para o watcher."""
        self._running = False
        self.wait(2000)
    
    @property
    def is_online(self) -> bool:
        """Último status conhecido."""
        if self._last_status is None:
            return self._check_connectivity()
        return self._last_status


# =============================================================================
# SYSTEM TRAY ICON
# =============================================================================

class SystemTrayManager(QSystemTrayIcon):
    """
    Ícone na bandeja do sistema.
    
    Features:
    - Ícone muda baseado em status
    - Menu de contexto
    - Notificações
    - Minimize to tray
    """
    
    show_window_requested = Signal()
    quit_requested = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self._setup_icon()
        self._setup_menu()
        self._connect_signals()
    
    def _setup_icon(self):
        """Cria ícone programaticamente."""
        # Cria ícone 32x32
        pixmap = QPixmap(32, 32)
        pixmap.fill(Qt.transparent)
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Background circular
        painter.setBrush(QColor("#6C5CE7"))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(2, 2, 28, 28)
        
        # Letra "A"
        painter.setPen(QColor("#FFFFFF"))
        font = painter.font()
        font.setPixelSize(18)
        font.setBold(True)
        painter.setFont(font)
        painter.drawText(pixmap.rect(), Qt.AlignCenter, "A")
        
        painter.end()
        
        self.setIcon(QIcon(pixmap))
        self.setToolTip("AutoTabloide AI")
    
    def _setup_menu(self):
        """Cria menu de contexto."""
        menu = QMenu()
        
        # Ações
        action_show = menu.addAction("📐 Abrir AutoTabloide")
        action_show.triggered.connect(self.show_window_requested.emit)
        
        menu.addSeparator()
        
        self.action_status = menu.addAction("🟢 Online")
        self.action_status.setEnabled(False)
        
        self.action_sentinel = menu.addAction("🤖 Sentinel: Idle")
        self.action_sentinel.setEnabled(False)
        
        menu.addSeparator()
        
        action_quit = menu.addAction("❌ Sair")
        action_quit.triggered.connect(self.quit_requested.emit)
        
        self.setContextMenu(menu)
    
    def _connect_signals(self):
        """Conecta sinais do tray."""
        self.activated.connect(self._on_activated)
    
    def _on_activated(self, reason):
        """Clique no ícone."""
        if reason == QSystemTrayIcon.Trigger:  # Clique simples
            self.show_window_requested.emit()
        elif reason == QSystemTrayIcon.DoubleClick:
            self.show_window_requested.emit()
    
    # =========================================================================
    # STATUS UPDATES
    # =========================================================================
    
    def set_network_status(self, online: bool):
        """Atualiza status de rede."""
        if online:
            self.action_status.setText("🟢 Online")
        else:
            self.action_status.setText("🔴 Offline")
    
    def set_sentinel_status(self, status: str):
        """Atualiza status do Sentinel."""
        icons = {
            "idle": "🟢",
            "busy": "🔵",
            "offline": "⚫",
            "error": "🔴",
        }
        icon = icons.get(status.lower(), "⚪")
        self.action_sentinel.setText(f"{icon} Sentinel: {status.title()}")
    
    def set_processing(self, processing: bool):
        """Muda ícone durante processamento."""
        if processing:
            self._create_processing_icon()
        else:
            self._setup_icon()
    
    def _create_processing_icon(self):
        """Cria ícone animado de processamento."""
        pixmap = QPixmap(32, 32)
        pixmap.fill(Qt.transparent)
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Background laranja = processando
        painter.setBrush(QColor("#F39C12"))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(2, 2, 28, 28)
        
        painter.setPen(QColor("#FFFFFF"))
        font = painter.font()
        font.setPixelSize(18)
        font.setBold(True)
        painter.setFont(font)
        painter.drawText(pixmap.rect(), Qt.AlignCenter, "A")
        
        painter.end()
        
        self.setIcon(QIcon(pixmap))
    
    # =========================================================================
    # NOTIFICATIONS
    # =========================================================================
    
    def notify(self, title: str, message: str, icon_type: str = "info"):
        """Mostra notificação do sistema."""
        icons = {
            "info": QSystemTrayIcon.Information,
            "warning": QSystemTrayIcon.Warning,
            "error": QSystemTrayIcon.Critical,
        }
        self.showMessage(title, message, icons.get(icon_type, QSystemTrayIcon.Information), 5000)
    
    def notify_export_complete(self, path: str):
        """Notifica conclusão de exportação."""
        self.notify(
            "Exportação Concluída",
            f"PDF salvo em:\n{path}",
            "info"
        )
    
    def notify_error(self, message: str):
        """Notifica erro."""
        self.notify("Erro", message, "error")


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def create_network_watcher(interval: int = 30) -> NetworkWatcher:
    """Cria e inicia watcher de rede."""
    watcher = NetworkWatcher(interval)
    watcher.start()
    return watcher


def create_system_tray(parent=None) -> SystemTrayManager:
    """Cria gerenciador de tray."""
    return SystemTrayManager(parent)

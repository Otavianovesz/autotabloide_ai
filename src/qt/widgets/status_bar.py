"""
AutoTabloide AI - Intelligent Status Bar
========================================
PROTOCOLO DE RETIFICAÇÃO NÍVEL 0 - Fase 1 (Passo 15)
Status bar inteligente com indicadores de estado.
"""

from __future__ import annotations
from typing import Optional
import logging

from PySide6.QtCore import Qt, Signal, Slot, QTimer
from PySide6.QtWidgets import (
    QStatusBar, QWidget, QHBoxLayout, QLabel, 
    QFrame, QPushButton
)

logger = logging.getLogger("StatusBar")


# =============================================================================
# INTELLIGENT STATUS BAR
# =============================================================================

class IntelligentStatusBar(QStatusBar):
    """
    Status bar com indicadores em tempo real.
    
    Layout: [Mensagem] ... [Undo] [Sentinel] [Zoom] [DB]
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        self._connect_signals()
    
    def _setup_ui(self):
        """Cria widgets permanentes."""
        # Use global QStatusBar style from theme.qss instead of inline
        # (QStatusBar is styled in theme.qss)
        
        # Container para widgets permanentes
        permanent_widget = QWidget()
        permanent_layout = QHBoxLayout(permanent_widget)
        permanent_layout.setContentsMargins(0, 0, 0, 0)
        permanent_layout.setSpacing(16)
        
        # Undo indicator
        self.undo_label = QLabel("⟲ 0/50")
        self.undo_label.setToolTip("Ações na pilha de undo (Ctrl+Z / Ctrl+Shift+Z)")
        self.undo_label.setProperty("class", "hint")
        permanent_layout.addWidget(self.undo_label)
        
        # Separator
        sep1 = QFrame()
        sep1.setFrameShape(QFrame.VLine)
        sep1.setProperty("class", "separator-v")
        permanent_layout.addWidget(sep1)
        
        # Sentinel indicator
        try:
            from src.qt.widgets.sentinel_ui import SentinelIndicator
            self.sentinel_indicator = SentinelIndicator()
            permanent_layout.addWidget(self.sentinel_indicator)
        except ImportError:
            self.sentinel_indicator = QLabel("Sentinel")
            permanent_layout.addWidget(self.sentinel_indicator)
        
        # Separator
        sep2 = QFrame()
        sep2.setFrameShape(QFrame.VLine)
        sep2.setProperty("class", "separator-v")
        permanent_layout.addWidget(sep2)
        
        # Zoom indicator
        self.zoom_label = QLabel("🔍 100%")
        self.zoom_label.setToolTip("Nível de zoom (+/- para ajustar)")
        self.zoom_label.setProperty("class", "hint")
        permanent_layout.addWidget(self.zoom_label)
        
        # Separator
        sep3 = QFrame()
        sep3.setFrameShape(QFrame.VLine)
        sep3.setProperty("class", "separator-v")
        permanent_layout.addWidget(sep3)
        
        # DB status
        self.db_label = QLabel("💾 OK")
        self.db_label.setToolTip("Status do banco de dados")
        permanent_layout.addWidget(self.db_label)
        
        # Modified indicator
        self.modified_label = QLabel("")
        permanent_layout.addWidget(self.modified_label)
        
        self.addPermanentWidget(permanent_widget)
    
    def _connect_signals(self):
        """Conecta aos sinais globais."""
        try:
            from src.qt.core.undo_redo import get_undo_manager
            
            undo_mgr = get_undo_manager()
            undo_mgr.stack_changed.connect(self._update_undo_display)
        except ImportError:
            pass
        
        try:
            from src.qt.core.global_input import get_signals
            
            signals = get_signals()
            signals.sentinel_status_changed.connect(self._update_sentinel)
            signals.project_saved.connect(lambda _: self._set_modified(False))
        except ImportError:
            pass
    
    # =========================================================================
    # UPDATE METHODS
    # =========================================================================
    
    @Slot()
    def _update_undo_display(self):
        """Atualiza indicador de undo."""
        try:
            from src.qt.core.undo_redo import get_undo_manager
            mgr = get_undo_manager()
            
            count = mgr.count
            index = mgr.index
            limit = 50
            
            self.undo_label.setText(f"⟲ {index}/{count}")
            
            # Cor baseada no estado via CSS class
            if count > 0:
                self.undo_label.setProperty("class", "status-ok")
            else:
                self.undo_label.setProperty("class", "hint")
            self.undo_label.style().unpolish(self.undo_label)
            self.undo_label.style().polish(self.undo_label)
        except ImportError:
            pass
    
    @Slot(str)
    def _update_sentinel(self, status: str):
        """Atualiza status do Sentinel."""
        if hasattr(self.sentinel_indicator, 'set_status_from_string'):
            self.sentinel_indicator.set_status_from_string(status)
    
    def set_zoom(self, percent: int):
        """Atualiza indicador de zoom."""
        self.zoom_label.setText(f"🔍 {percent}%")
    
    def set_db_status(self, ok: bool, message: str = None):
        """Atualiza status do DB."""
        if ok:
            self.db_label.setText("💾 OK")
            self.db_label.setProperty("class", "status-ok")
        else:
            self.db_label.setText("💾 !")
            self.db_label.setProperty("class", "status-error")
        self.db_label.style().unpolish(self.db_label)
        self.db_label.style().polish(self.db_label)
        
        if message:
            self.db_label.setToolTip(message)
    
    def _set_modified(self, modified: bool):
        """Mostra indicador de modificação."""
        if modified:
            self.modified_label.setText("●")
            self.modified_label.setProperty("class", "modified-indicator")
            self.modified_label.setToolTip("Projeto não salvo")
        else:
            self.modified_label.setText("")
            self.modified_label.setProperty("class", "")
        self.modified_label.style().unpolish(self.modified_label)
        self.modified_label.style().polish(self.modified_label)
    
    def set_modified(self, modified: bool):
        """API pública para modificação."""
        self._set_modified(modified)
    
    # =========================================================================
    # MESSAGE OVERRIDES
    # =========================================================================
    
    def showMessage(self, msg: str, timeout: int = 0):
        """Override para adicionar ícones."""
        super().showMessage(msg, timeout)
    
    def show_success(self, msg: str, timeout: int = 3000):
        """Mostra mensagem de sucesso."""
        self.showMessage(f"✅ {msg}", timeout)
    
    def show_warning(self, msg: str, timeout: int = 5000):
        """Mostra aviso."""
        self.showMessage(f"⚠️ {msg}", timeout)
    
    def show_error(self, msg: str, timeout: int = 0):
        """Mostra erro."""
        self.showMessage(f"❌ {msg}", timeout)
    
    def show_info(self, msg: str, timeout: int = 3000):
        """Mostra info."""
        self.showMessage(f"ℹ️ {msg}", timeout)


# =============================================================================
# HELPER
# =============================================================================

def create_intelligent_status_bar(parent=None) -> IntelligentStatusBar:
    """Cria status bar inteligente."""
    return IntelligentStatusBar(parent)

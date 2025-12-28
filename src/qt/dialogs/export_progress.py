"""
AutoTabloide AI - Export Progress Modal
=======================================
PROTOCOLO DE RETIFICAÇÃO NÍVEL 0 - Fase 4 (Passo 148)
Modal com barra de progresso para exportação PDF.
"""

from __future__ import annotations
from typing import Optional
import logging

from PySide6.QtCore import Qt, Signal, Slot, QThread
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QProgressBar, QPushButton, QTextEdit
)

logger = logging.getLogger("ExportProgress")


# =============================================================================
# EXPORT WORKER
# =============================================================================

class ExportWorker(QThread):
    """Worker para exportação em background."""
    
    progress = Signal(int, str)  # percent, message
    finished = Signal(bool, str)  # success, result
    log = Signal(str)
    
    def __init__(self, export_fn, parent=None):
        super().__init__(parent)
        self._export_fn = export_fn
        self._cancelled = False
    
    def run(self):
        try:
            self.progress.emit(10, "Iniciando exportação...")
            
            # Executa função de exportação
            success, result = self._export_fn(
                progress_callback=self._report_progress
            )
            
            if self._cancelled:
                self.finished.emit(False, "Exportação cancelada")
            else:
                self.finished.emit(success, result)
                
        except Exception as e:
            logger.error(f"[Export] Erro: {e}")
            self.finished.emit(False, str(e))
    
    def _report_progress(self, percent: int, message: str):
        """Callback para reportar progresso."""
        if not self._cancelled:
            self.progress.emit(percent, message)
    
    def cancel(self):
        """Marca para cancelamento."""
        self._cancelled = True


# =============================================================================
# EXPORT PROGRESS DIALOG
# =============================================================================

class ExportProgressDialog(QDialog):
    """
    Modal bloqueante com progresso de exportação.
    
    Features:
    - Barra de progresso animada
    - Log de passos em tempo real
    - Botão cancelar
    - Status colorido
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Exportando PDF...")
        self.setMinimumWidth(500)
        self.setMinimumHeight(300)
        self.setModal(True)
        
        self._worker: Optional[ExportWorker] = None
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        
        # Status
        self.status_label = QLabel("Preparando exportação...")
        self.status_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        layout.addWidget(self.status_label)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        layout.addWidget(self.progress_bar)
        
        # Log area
        self.log_area = QTextEdit()
        self.log_area.setReadOnly(True)
        self.log_area.setMaximumHeight(150)
        self.log_area.setStyleSheet("""
            QTextEdit {
                background-color: #1A1A2E;
                color: #B0B0B0;
                font-family: Consolas, monospace;
                font-size: 11px;
            }
        """)
        layout.addWidget(self.log_area)
        
        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        self.cancel_btn = QPushButton("Cancelar")
        self.cancel_btn.clicked.connect(self._on_cancel)
        btn_layout.addWidget(self.cancel_btn)
        
        self.close_btn = QPushButton("Fechar")
        self.close_btn.clicked.connect(self.accept)
        self.close_btn.setEnabled(False)
        btn_layout.addWidget(self.close_btn)
        
        layout.addLayout(btn_layout)
    
    def start_export(self, export_fn):
        """Inicia exportação com função fornecida."""
        self._worker = ExportWorker(export_fn)
        self._worker.progress.connect(self._on_progress)
        self._worker.finished.connect(self._on_finished)
        self._worker.log.connect(self._on_log)
        self._worker.start()
        
        self._log("🚀 Iniciando processo de exportação...")
    
    @Slot(int, str)
    def _on_progress(self, percent: int, message: str):
        """Atualiza progresso."""
        self.progress_bar.setValue(percent)
        self.status_label.setText(message)
        self._log(f"[{percent}%] {message}")
    
    @Slot(bool, str)
    def _on_finished(self, success: bool, result: str):
        """Exportação concluída."""
        self.cancel_btn.setEnabled(False)
        self.close_btn.setEnabled(True)
        
        if success:
            self.progress_bar.setValue(100)
            self.status_label.setText("✅ Exportação concluída!")
            self.status_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #2ECC71;")
            self._log(f"✅ Sucesso: {result}")
        else:
            self.status_label.setText("❌ Exportação falhou")
            self.status_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #E74C3C;")
            self._log(f"❌ Erro: {result}")
    
    @Slot(str)
    def _on_log(self, message: str):
        """Adiciona ao log."""
        self._log(message)
    
    def _log(self, message: str):
        """Adiciona linha ao log."""
        self.log_area.append(message)
        # Scroll para baixo
        scrollbar = self.log_area.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    
    def _on_cancel(self):
        """Cancela exportação."""
        if self._worker and self._worker.isRunning():
            self._worker.cancel()
            self._log("⚠️ Cancelamento solicitado...")
            self.status_label.setText("Cancelando...")
    
    def closeEvent(self, event):
        """Garante que worker seja parado."""
        if self._worker and self._worker.isRunning():
            self._worker.cancel()
            self._worker.wait(2000)
        super().closeEvent(event)


# =============================================================================
# HELPER FUNCTION
# =============================================================================

def show_export_progress(parent, export_fn) -> bool:
    """
    Mostra modal de progresso e executa exportação.
    
    Args:
        parent: Widget pai
        export_fn: Função de exportação que recebe progress_callback
        
    Returns:
        True se exportação foi bem sucedida
    """
    dialog = ExportProgressDialog(parent)
    dialog.start_export(export_fn)
    result = dialog.exec()
    return result == QDialog.Accepted and dialog.progress_bar.value() == 100

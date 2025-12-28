"""
AutoTabloide AI - The Judge Modal (O Juiz)
============================================
PROTOCOLO DE CONVERGÊNCIA INDUSTRIAL - Fase 2
Passos 31-40: Modal de conciliação para importação Excel.

Implementa o fluxo de arbitragem para classificar entradas:
- Verde: Match exato no banco
- Amarelo: Sugestão IA (requer confirmação)
- Vermelho: Novo item (será criado)
"""

from __future__ import annotations
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from decimal import Decimal
import json
import asyncio

from PySide6.QtCore import Qt, Signal, Slot, QThread, QObject
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QComboBox,
    QProgressBar, QFileDialog, QMessageBox, QCheckBox, QFrame,
    QWidget, QStackedWidget
)
from PySide6.QtGui import QColor, QBrush, QFont


# =============================================================================
# MATCH STATUS ENUM
# =============================================================================

class MatchStatus:
    EXACT = "exact"      # Verde - match exato
    FUZZY = "fuzzy"      # Amarelo - sugestão
    NEW = "new"          # Vermelho - novo item


# =============================================================================
# JUDGE WORKER - Processa reconciliação em background
# =============================================================================

class JudgeWorker(QObject):
    """Worker para processamento de reconciliação."""
    
    progress = Signal(int, int)  # current, total
    item_processed = Signal(int, dict)  # row, result
    completed = Signal(list)  # all results
    error = Signal(str)
    
    def __init__(self):
        super().__init__()
        self._items: List[Dict] = []
        self._running = True
    
    def set_items(self, items: List[Dict]):
        """Define itens para processar."""
        self._items = items
    
    @Slot()
    def process(self):
        """Processa reconciliação de todos os itens."""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            results = loop.run_until_complete(self._async_process())
            self.completed.emit(results)
            
        except Exception as e:
            self.error.emit(str(e))
        finally:
            loop.close()
    
    async def _async_process(self) -> List[Dict]:
        """Processamento assíncrono."""
        from src.core.database import AsyncSessionLocal
        from src.core.repositories import ProductRepository
        
        results = []
        total = len(self._items)
        
        async with AsyncSessionLocal() as session:
            repo = ProductRepository(session)
            
            for i, item in enumerate(self._items):
                if not self._running:
                    break
                    
                result = await self._process_item(repo, item)
                results.append(result)
                
                self.progress.emit(i + 1, total)
                self.item_processed.emit(i, result)
        
        return results
    
    async def _process_item(self, repo, item: Dict) -> Dict:
        """Processa um item individual."""
        raw_name = item.get("nome", "") or item.get("descricao", "") or ""
        raw_name = raw_name.strip()
        
        if not raw_name:
            return {
                "status": MatchStatus.NEW,
                "raw": raw_name,
                "suggestion": "Nome vazio",
                "confidence": 0,
                "product_id": None,
                "original": item
            }
        
        # 1. Tenta match exato por alias
        existing = await repo.find_by_alias(raw_name)
        if existing:
            return {
                "status": MatchStatus.EXACT,
                "raw": raw_name,
                "suggestion": existing.nome_sanitizado,
                "confidence": 1.0,
                "product_id": existing.id,
                "original": item
            }
        
        # 2. Tenta match por SKU se disponível
        sku = item.get("sku", "") or item.get("codigo", "")
        if sku:
            by_sku = await repo.get_by_sku(sku.strip())
            if by_sku:
                return {
                    "status": MatchStatus.EXACT,
                    "raw": raw_name,
                    "suggestion": by_sku.nome_sanitizado,
                    "confidence": 1.0,
                    "product_id": by_sku.id,
                    "original": item
                }
        
        # 3. Busca fuzzy por nome similar
        similar = await repo.search(query=raw_name[:20], limit=5)
        if similar:
            # Calcula similaridade simples
            best_match = similar[0]
            score = self._calculate_similarity(raw_name, best_match.nome_sanitizado)
            
            if score >= 0.75:
                return {
                    "status": MatchStatus.FUZZY,
                    "raw": raw_name,
                    "suggestion": best_match.nome_sanitizado,
                    "confidence": score,
                    "product_id": best_match.id,
                    "alternatives": [p.nome_sanitizado for p in similar[:3]],
                    "original": item
                }
        
        # 4. Novo item - sanitiza nome
        sanitized = self._sanitize_name(raw_name)
        return {
            "status": MatchStatus.NEW,
            "raw": raw_name,
            "suggestion": sanitized,
            "confidence": 0,
            "product_id": None,
            "original": item
        }
    
    def _calculate_similarity(self, s1: str, s2: str) -> float:
        """Calcula similaridade Jaccard simples."""
        s1_lower = s1.lower().split()
        s2_lower = s2.lower().split()
        
        s1_set = set(s1_lower)
        s2_set = set(s2_lower)
        
        intersection = len(s1_set & s2_set)
        union = len(s1_set | s2_set)
        
        return intersection / union if union > 0 else 0
    
    def _sanitize_name(self, raw: str) -> str:
        """Sanitização básica de nome (Title Case)."""
        # Remove múltiplos espaços
        clean = " ".join(raw.split())
        
        # Title case inteligente
        words = clean.split()
        result = []
        prepositions = {"de", "da", "do", "das", "dos", "e", "com", "para", "em"}
        
        for i, word in enumerate(words):
            if i == 0 or word.lower() not in prepositions:
                result.append(word.capitalize())
            else:
                result.append(word.lower())
        
        return " ".join(result)
    
    def stop(self):
        self._running = False


# =============================================================================
# JUDGE MODAL - Interface de reconciliação
# =============================================================================

class JudgeModal(QDialog):
    """
    Modal de Conciliação (O Juiz).
    
    Permite ao usuário:
    1. Ver correspondências automáticas
    2. Confirmar/corrigir sugestões
    3. Aprovar criação de novos itens
    """
    
    import_confirmed = Signal(list)  # Lista de itens confirmados
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("O Juiz - Conciliação de Dados")
        self.setMinimumSize(900, 600)
        self.setModal(True)
        
        self._results: List[Dict] = []
        self._worker: Optional[JudgeWorker] = None
        self._thread: Optional[QThread] = None
        
        self._setup_ui()
    
    def _setup_ui(self):
        """Configura interface do modal."""
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        
        # Header
        header = QLabel("⚖️ O Juiz - Conciliação de Importação")
        header.setStyleSheet("""
            font-size: 18px;
            font-weight: bold;
            color: #6C5CE7;
            padding: 8px;
        """)
        layout.addWidget(header)
        
        # Legenda
        legend = QHBoxLayout()
        
        for color, text in [
            ("#27AE60", "Verde: Match Exato"),
            ("#F39C12", "Amarelo: Confirmar"),
            ("#E74C3C", "Vermelho: Novo Item")
        ]:
            label = QLabel(f"● {text}")
            label.setStyleSheet(f"color: {color}; font-weight: bold;")
            legend.addWidget(label)
        
        legend.addStretch()
        layout.addLayout(legend)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #2D2D44;
                border-radius: 4px;
                background-color: #1A1A2E;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: #6C5CE7;
            }
        """)
        layout.addWidget(self.progress_bar)
        
        # Tabela de resultados
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels([
            "Status", "Entrada Original", "Sugestão Sistema", "Confiança", "Ação"
        ])
        
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)
        
        self.table.setColumnWidth(0, 80)
        self.table.setColumnWidth(3, 100)
        self.table.setColumnWidth(4, 120)
        
        self.table.setStyleSheet("""
            QTableWidget {
                background-color: #1A1A2E;
                gridline-color: #2D2D44;
                border: 1px solid #2D2D44;
                border-radius: 8px;
            }
            QTableWidget::item {
                padding: 8px;
            }
            QHeaderView::section {
                background-color: #2D2D44;
                padding: 8px;
                border: none;
                font-weight: bold;
            }
        """)
        layout.addWidget(self.table)
        
        # Status
        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color: #888;")
        layout.addWidget(self.status_label)
        
        # Botões
        buttons = QHBoxLayout()
        
        self.btn_cancel = QPushButton("Cancelar")
        self.btn_cancel.clicked.connect(self.reject)
        
        self.btn_confirm = QPushButton("✓ Confirmar Importação")
        self.btn_confirm.setEnabled(False)
        self.btn_confirm.clicked.connect(self._on_confirm)
        self.btn_confirm.setStyleSheet("""
            QPushButton {
                background-color: #27AE60;
                color: white;
                font-weight: bold;
                padding: 12px 24px;
                border-radius: 6px;
            }
            QPushButton:disabled {
                background-color: #555;
            }
            QPushButton:hover:enabled {
                background-color: #2ECC71;
            }
        """)
        
        buttons.addStretch()
        buttons.addWidget(self.btn_cancel)
        buttons.addWidget(self.btn_confirm)
        
        layout.addLayout(buttons)
    
    def process_items(self, items: List[Dict]):
        """Inicia processamento de itens."""
        self.progress_bar.setVisible(True)
        self.progress_bar.setMaximum(len(items))
        self.progress_bar.setValue(0)
        
        self.table.setRowCount(0)
        self._results = []
        
        # Cria worker em thread separada
        self._thread = QThread()
        self._worker = JudgeWorker()
        self._worker.set_items(items)
        self._worker.moveToThread(self._thread)
        
        # Conecta sinais
        self._thread.started.connect(self._worker.process)
        self._worker.progress.connect(self._on_progress)
        self._worker.item_processed.connect(self._on_item_processed)
        self._worker.completed.connect(self._on_completed)
        self._worker.error.connect(self._on_error)
        
        self._thread.start()
    
    def _on_progress(self, current: int, total: int):
        """Atualiza barra de progresso."""
        self.progress_bar.setValue(current)
        self.status_label.setText(f"Processando {current}/{total}...")
    
    def _on_item_processed(self, row: int, result: Dict):
        """Adiciona item processado à tabela."""
        self.table.insertRow(row)
        
        # Status visual
        status = result["status"]
        if status == MatchStatus.EXACT:
            color = "#27AE60"
            status_text = "✓"
        elif status == MatchStatus.FUZZY:
            color = "#F39C12"
            status_text = "?"
        else:
            color = "#E74C3C"
            status_text = "+"
        
        status_item = QTableWidgetItem(status_text)
        status_item.setBackground(QBrush(QColor(color)))
        status_item.setTextAlignment(Qt.AlignCenter)
        self.table.setItem(row, 0, status_item)
        
        # Entrada original
        raw_item = QTableWidgetItem(result["raw"])
        self.table.setItem(row, 1, raw_item)
        
        # Sugestão
        suggestion_item = QTableWidgetItem(result["suggestion"])
        self.table.setItem(row, 2, suggestion_item)
        
        # Confiança
        conf = result["confidence"]
        conf_text = f"{conf*100:.0f}%" if conf > 0 else "-"
        conf_item = QTableWidgetItem(conf_text)
        conf_item.setTextAlignment(Qt.AlignCenter)
        self.table.setItem(row, 3, conf_item)
        
        # Ação (checkbox para confirmar)
        action = QCheckBox("OK" if status == MatchStatus.EXACT else "Confirmar")
        action.setChecked(status == MatchStatus.EXACT)
        if status == MatchStatus.EXACT:
            action.setEnabled(False)
        action.stateChanged.connect(self._check_can_confirm)
        
        container = QWidget()
        container_layout = QHBoxLayout(container)
        container_layout.addWidget(action)
        container_layout.setAlignment(Qt.AlignCenter)
        container_layout.setContentsMargins(0, 0, 0, 0)
        self.table.setCellWidget(row, 4, container)
    
    def _on_completed(self, results: List[Dict]):
        """Processamento concluído."""
        self._results = results
        self.progress_bar.setVisible(False)
        
        # Conta por status
        exact = sum(1 for r in results if r["status"] == MatchStatus.EXACT)
        fuzzy = sum(1 for r in results if r["status"] == MatchStatus.FUZZY)
        new = sum(1 for r in results if r["status"] == MatchStatus.NEW)
        
        self.status_label.setText(
            f"Concluído: {exact} exatos, {fuzzy} para confirmar, {new} novos"
        )
        
        self._check_can_confirm()
        
        # Cleanup thread
        if self._thread:
            self._thread.quit()
            self._thread.wait()
    
    def _on_error(self, error: str):
        """Erro no processamento."""
        self.progress_bar.setVisible(False)
        self.status_label.setText(f"Erro: {error}")
        QMessageBox.critical(self, "Erro", f"Erro no processamento:\n{error}")
    
    def _check_can_confirm(self):
        """Verifica se todos os itens foram confirmados."""
        all_confirmed = True
        
        for row in range(self.table.rowCount()):
            widget = self.table.cellWidget(row, 4)
            if widget:
                checkbox = widget.findChild(QCheckBox)
                if checkbox and not checkbox.isChecked():
                    all_confirmed = False
                    break
        
        self.btn_confirm.setEnabled(all_confirmed)
    
    def _on_confirm(self):
        """Confirma importação."""
        confirmed = []
        
        for i, result in enumerate(self._results):
            widget = self.table.cellWidget(i, 4)
            if widget:
                checkbox = widget.findChild(QCheckBox)
                if checkbox and checkbox.isChecked():
                    confirmed.append(result)
        
        self.import_confirmed.emit(confirmed)
        self.accept()
    
    def closeEvent(self, event):
        """Limpa recursos ao fechar."""
        if self._worker:
            self._worker.stop()
        if self._thread and self._thread.isRunning():
            self._thread.quit()
            self._thread.wait(1000)
        super().closeEvent(event)


# =============================================================================
# FUNÇÃO HELPER PARA ABRIR MODAL
# =============================================================================

def open_judge_modal(parent, items: List[Dict]) -> Optional[List[Dict]]:
    """
    Abre modal do Juiz e retorna itens confirmados.
    
    Args:
        parent: Widget pai
        items: Lista de dicts com dados da planilha
        
    Returns:
        Lista de itens confirmados ou None se cancelado
    """
    modal = JudgeModal(parent)
    modal.process_items(items)
    
    result = []
    
    def on_confirmed(confirmed):
        nonlocal result
        result = confirmed
    
    modal.import_confirmed.connect(on_confirmed)
    
    if modal.exec() == QDialog.DialogCode.Accepted:
        return result
    return None

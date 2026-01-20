"""
AutoTabloide AI - Fábrica Widget Industrial Grade
==================================================
PROTOCOLO DE CONVERGÊNCIA INDUSTRIAL - Fase 5
Passos 66-74: Renderização e saída real.

Exportação PDF via VectorEngine + Ghostscript.
"""

from __future__ import annotations
from pathlib import Path
from typing import Optional, Dict, List, Any
from datetime import datetime
import subprocess
import json
import tempfile

from PySide6.QtCore import (
    Qt, Signal, Slot, QTimer, QThread, QObject
)
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFrame, QLabel,
    QPushButton, QProgressBar, QListWidget, QListWidgetItem,
    QFileDialog, QMessageBox, QDialog, QTextEdit, QComboBox,
    QSpinBox, QCheckBox, QGroupBox, QGridLayout
)
from PySide6.QtGui import QColor, QFont


# =============================================================================
# RENDER WORKER (Passos 66-72)
# =============================================================================

class RenderWorker(QObject):
    """Worker para renderização em background."""
    
    progress = Signal(int, int, str)  # atual, total, mensagem
    completed = Signal(str)  # caminho do arquivo
    error = Signal(str)
    log = Signal(str)
    
    def __init__(self):
        super().__init__()
        self._jobs: List[Dict] = []
        self._gs_path: Optional[str] = None
        self._icc_path: Optional[str] = None
        self._running = True
    
    def set_config(self, gs_path: str, icc_path: str):
        """Define caminhos de binários."""
        self._gs_path = gs_path
        self._icc_path = icc_path
    
    def add_job(self, job: Dict):
        """Adiciona job de renderização."""
        self._jobs.append(job)
    
    @Slot()
    def process_jobs(self):
        """Processa fila de jobs."""
        total = len(self._jobs)
        
        for i, job in enumerate(self._jobs):
            if not self._running:
                break
            
            self.progress.emit(i + 1, total, f"Renderizando {job.get('name', 'arquivo')}...")
            
            try:
                output_path = self._render_job(job)
                if output_path:
                    self.completed.emit(output_path)
            except Exception as e:
                self.error.emit(str(e))
        
        self._jobs.clear()
    
    def _render_job(self, job: Dict) -> Optional[str]:
        """Renderiza um job específico."""
        template_path = job.get("template_path")
        output_path = job.get("output_path")
        slots_data = job.get("slots_data", {})
        output_format = job.get("format", "pdf")
        colorspace = job.get("colorspace", "rgb")
        
        # Passo 67: Injeção no SVG
        svg_content = self._inject_data_into_svg(template_path, slots_data)
        if not svg_content:
            self.error.emit("Falha ao gerar SVG")
            return None
        
        # Salva SVG temporário
        with tempfile.NamedTemporaryFile(
            mode='w', suffix='.svg', delete=False, encoding='utf-8'
        ) as f:
            f.write(svg_content)
            temp_svg = f.name
        
        self.log.emit(f"SVG temp: {temp_svg}")
        
        # Passo 69-72: Pipeline Ghostscript
        if output_format == "pdf":
            success = self._render_pdf_with_gs(
                temp_svg, output_path, colorspace
            )
            if not success:
                # Fallback para CairoSVG
                success = self._render_pdf_with_cairo(temp_svg, output_path)
        else:
            success = self._render_png(temp_svg, output_path)
        
        # Limpa temp
        Path(temp_svg).unlink(missing_ok=True)
        
        return output_path if success else None
    
    def _inject_data_into_svg(
        self, 
        template_path: str, 
        slots_data: Dict
    ) -> Optional[str]:
        """Injeta dados dos produtos no template SVG."""
        try:
            from src.qt.rendering.svg_template_parser import SvgTemplateParser
            
            parser = SvgTemplateParser()
            template_info = parser.parse(template_path)
            
            if not template_info:
                return None
            
            # Injeta dados em cada slot
            for slot_idx, product_data in slots_data.items():
                slot_def = None
                for s in template_info.slots:
                    if s.index == slot_idx:
                        slot_def = s
                        break
                
                if not slot_def:
                    continue
                
                # Nome
                if slot_def.name_text_id and product_data.get("nome_sanitizado"):
                    parser.modify_text(
                        slot_def.name_text_id,
                        product_data["nome_sanitizado"]
                    )
                
                # Preço
                if slot_def.price_text_id and product_data.get("preco_venda_atual"):
                    price = float(product_data["preco_venda_atual"])
                    price_str = f"R$ {price:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
                    parser.modify_text(slot_def.price_text_id, price_str)
                
                # Imagem
                if slot_def.image_target_id and product_data.get("img_hash_ref"):
                    img_path = f"AutoTabloide_System_Root/assets/store/{product_data['img_hash_ref']}.png"
                    if Path(img_path).exists():
                        parser.modify_image(slot_def.image_target_id, str(Path(img_path).absolute()))
            
            return parser.to_string()
            
        except Exception as e:
            self.log.emit(f"Erro na injeção: {e}")
            return None
    
    def _render_pdf_with_gs(
        self, 
        svg_path: str, 
        output_path: str,
        colorspace: str = "rgb"
    ) -> bool:
        """Renderiza PDF usando Ghostscript (Passos 69-72)."""
        if not self._gs_path or not Path(self._gs_path).exists():
            self.log.emit("Ghostscript não encontrado")
            return False
        
        # Primeiro converte SVG para PDF intermediário
        try:
            import cairosvg
            temp_pdf = output_path + ".temp.pdf"
            cairosvg.svg2pdf(url=svg_path, write_to=temp_pdf)
        except Exception as e:
            self.log.emit(f"CairoSVG falhou: {e}")
            return False
        
        # Passo 70: Argumentos GS com ICC
        gs_args = [
            self._gs_path,
            "-dBATCH",
            "-dNOPAUSE",
            "-dSAFER",
            "-sDEVICE=pdfwrite",
            "-dPDFSETTINGS=/prepress",
            "-dCompatibilityLevel=1.4",
        ]
        
        # Colorspace CMYK com ICC
        if colorspace == "cmyk" and self._icc_path and Path(self._icc_path).exists():
            gs_args.extend([
                "-sColorConversionStrategy=CMYK",
                f"-sOutputICCProfile={self._icc_path}",
            ])
        
        gs_args.extend([
            f"-sOutputFile={output_path}",
            temp_pdf,
        ])
        
        try:
            self.log.emit(f"Executando: {' '.join(gs_args)}")
            
            result = subprocess.run(
                gs_args,
                capture_output=True,
                text=True,
                timeout=120,
            )
            
            if result.returncode != 0:
                self.log.emit(f"GS stderr: {result.stderr}")
                # Passo 72: Tratamento de erro
                error_msg = self._translate_gs_error(result.stderr)
                self.error.emit(error_msg)
                return False
            
            # Limpa temp
            Path(temp_pdf).unlink(missing_ok=True)
            
            return True
            
        except subprocess.TimeoutExpired:
            self.error.emit("Timeout na renderização (120s)")
            return False
        except Exception as e:
            self.log.emit(f"Erro GS: {e}")
            return False
    
    def _render_pdf_with_cairo(self, svg_path: str, output_path: str) -> bool:
        """Fallback: renderiza PDF com CairoSVG."""
        try:
            import cairosvg
            cairosvg.svg2pdf(url=svg_path, write_to=output_path)
            return True
        except Exception as e:
            self.log.emit(f"Cairo falhou: {e}")
            return False
    
    def _render_png(self, svg_path: str, output_path: str) -> bool:
        """Renderiza PNG."""
        try:
            import cairosvg
            cairosvg.svg2png(url=svg_path, write_to=output_path, scale=2)
            return True
        except Exception as e:
            self.log.emit(f"PNG falhou: {e}")
            return False
    
    def _translate_gs_error(self, stderr: str) -> str:
        """Traduz erros do Ghostscript para português."""
        if "undefined" in stderr.lower():
            return "Erro no PDF: fonte ou recurso não encontrado"
        if "ioerror" in stderr.lower():
            return "Erro de I/O: não foi possível ler/escrever arquivo"
        if "color" in stderr.lower():
            return "Erro de conversão de cores"
        return f"Erro no Ghostscript: {stderr[:100]}"
    
    def stop(self):
        self._running = False


# =============================================================================
# RENDER QUEUE WIDGET
# =============================================================================

class RenderQueueWidget(QFrame):
    """Widget de fila de renderização."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background-color: #1A1A2E; border-radius: 8px;")
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        
        header = QLabel("Fila de Renderização")
        header.setStyleSheet("font-weight: bold; color: #FFFFFF;")
        layout.addWidget(header)
        
        self.queue_list = QListWidget()
        self.queue_list.setMaximumHeight(150)
        layout.addWidget(self.queue_list)
        
        self.progress = QProgressBar()
        self.progress.setValue(0)
        layout.addWidget(self.progress)
        
        self.status_label = QLabel("Aguardando...")
        self.status_label.setStyleSheet("color: #808080;")
        layout.addWidget(self.status_label)
    
    def add_job(self, name: str):
        item = QListWidgetItem(f"⏳ {name}")
        self.queue_list.addItem(item)
    
    def update_job(self, index: int, status: str):
        if 0 <= index < self.queue_list.count():
            item = self.queue_list.item(index)
            if status == "done":
                item.setText(item.text().replace("⏳", "✅"))
            elif status == "error":
                item.setText(item.text().replace("⏳", "❌"))
    
    def update_progress(self, current: int, total: int, message: str):
        pct = int((current / max(1, total)) * 100)
        self.progress.setValue(pct)
        self.status_label.setText(message)
    
    def clear(self):
        self.queue_list.clear()
        self.progress.setValue(0)
        self.status_label.setText("Aguardando...")


# =============================================================================
# FÁBRICA WIDGET
# =============================================================================

class FactoryWidget(QWidget):
    """
    Widget da Fábrica (Passos 66-74).
    
    Gerencia renderização em lote e exportação.
    """
    
    def __init__(self, container=None, parent=None):
        super().__init__(parent)
        self.container = container
        
        # Worker thread
        self._render_thread = QThread()
        self._render_worker = RenderWorker()
        self._render_worker.moveToThread(self._render_thread)
        self._render_worker.progress.connect(self._on_progress)
        self._render_worker.completed.connect(self._on_completed)
        self._render_worker.error.connect(self._on_error)
        self._render_worker.log.connect(self._on_log)
        self._render_thread.start()
        
        # Configura binários
        self._configure_binaries()
        
        self._setup_ui()
    
    def _configure_binaries(self):
        """Configura caminhos de binários."""
        gs_path = "AutoTabloide_System_Root/bin/gswin64c.exe"
        icc_path = "AutoTabloide_System_Root/assets/profiles/CoatedFOGRA39.icc"
        
        if Path(gs_path).exists():
            self._render_worker.set_config(gs_path, icc_path)
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        
        # Header
        header = QHBoxLayout()
        
        title = QLabel("Fábrica")
        title.setStyleSheet("font-size: 28px; font-weight: bold; color: #FFFFFF;")
        header.addWidget(title)
        
        header.addStretch()
        
        layout.addLayout(header)
        
        # Configurações de exportação
        config_group = QGroupBox("Configurações de Exportação")
        config_layout = QGridLayout(config_group)
        
        config_layout.addWidget(QLabel("Formato:"), 0, 0)
        self.format_combo = QComboBox()
        self.format_combo.addItem("PDF (Impressão)", "pdf")
        self.format_combo.addItem("PNG (Preview)", "png")
        config_layout.addWidget(self.format_combo, 0, 1)
        
        config_layout.addWidget(QLabel("Espaço de Cor:"), 1, 0)
        self.color_combo = QComboBox()
        self.color_combo.addItem("RGB (Digital)", "rgb")
        self.color_combo.addItem("CMYK (Impressão Offset)", "cmyk")
        config_layout.addWidget(self.color_combo, 1, 1)
        
        config_layout.addWidget(QLabel("DPI:"), 2, 0)
        self.dpi_spin = QSpinBox()
        self.dpi_spin.setRange(72, 600)
        self.dpi_spin.setValue(300)
        config_layout.addWidget(self.dpi_spin, 2, 1)
        
        self.preview_check = QCheckBox("Abrir após exportar")
        self.preview_check.setChecked(True)
        config_layout.addWidget(self.preview_check, 3, 0, 1, 2)
        
        # Filtro "Já Impresso" - Mostra apenas produtos com preço alterado (Fase 4)
        self.changed_only_check = QCheckBox("Mostrar apenas preços alterados (Já Impresso)")
        self.changed_only_check.setToolTip(
            "Filtra para mostrar apenas produtos cujo preço mudou desde a última impressão"
        )
        config_layout.addWidget(self.changed_only_check, 4, 0, 1, 2)
        
        layout.addWidget(config_group)
        
        # Fila de renderização
        self.queue_widget = RenderQueueWidget()
        layout.addWidget(self.queue_widget)
        
        # Botões de ação
        actions = QHBoxLayout()
        
        btn_add = QPushButton("Adicionar Projeto")
        btn_add.clicked.connect(self._add_project)
        actions.addWidget(btn_add)
        
        btn_export = QPushButton("Exportar Selecionados")
        btn_export.clicked.connect(self._export_selected)
        actions.addWidget(btn_export)
        
        btn_export_all = QPushButton("Exportar Todos")
        btn_export_all.clicked.connect(self._export_all)
        actions.addWidget(btn_export_all)
        
        actions.addStretch()
        
        btn_stop = QPushButton("Parar")
        btn_stop.setProperty("class", "danger")
        btn_stop.clicked.connect(self._stop_render)
        actions.addWidget(btn_stop)
        
        layout.addWidget(self._create_actions_frame(actions))
        
        # Log
        log_group = QGroupBox("Log de Renderização")
        log_layout = QVBoxLayout(log_group)
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(150)
        self.log_text.setStyleSheet("background-color: #0D0D0D; color: #808080;")
        log_layout.addWidget(self.log_text)
        
        layout.addWidget(log_group)
        
        layout.addStretch()
    
    def _create_actions_frame(self, layout: QHBoxLayout) -> QFrame:
        frame = QFrame()
        frame.setLayout(layout)
        return frame
    
    @Slot()
    def _add_project(self):
        """Adiciona projeto à fila."""
        path, _ = QFileDialog.getOpenFileName(
            self, "Selecionar Projeto", "",
            "Projeto Tabloide (*.tabloide);;JSON (*.json)"
        )
        if path:
            self.queue_widget.add_job(Path(path).stem)
            self._log(f"Adicionado: {path}")
    
    @Slot()
    def _export_selected(self):
        """Exporta itens selecionados."""
        QMessageBox.information(
            self, "Exportar",
            "Selecione projetos na fila para exportar"
        )
    
    @Slot()
    def _export_all(self):
        """Exporta todos os itens."""
        output_dir = QFileDialog.getExistingDirectory(
            self, "Diretório de Saída"
        )
        if output_dir:
            self._log(f"Exportando para: {output_dir}")
            QTimer.singleShot(0, self._render_worker.process_jobs)
    
    @Slot()
    def _stop_render(self):
        """Para renderização."""
        self._render_worker.stop()
        self._log("Renderização interrompida")
    
    @Slot(int, int, str)
    def _on_progress(self, current: int, total: int, message: str):
        self.queue_widget.update_progress(current, total, message)
    
    @Slot(str)
    def _on_completed(self, path: str):
        self._log(f"✅ Concluído: {path}")
        
        # Passo 73: Preview automático
        if self.preview_check.isChecked():
            import os
            os.startfile(path)
    
    @Slot(str)
    def _on_error(self, error: str):
        self._log(f"❌ Erro: {error}")
        QMessageBox.warning(self, "Erro", error)
    
    @Slot(str)
    def _on_log(self, message: str):
        self._log(message)
    
    def _log(self, message: str):
        """Adiciona mensagem ao log."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.append(f"[{timestamp}] {message}")
    
    def closeEvent(self, event):
        self._render_worker.stop()
        self._render_thread.quit()
        self._render_thread.wait()
        super().closeEvent(event)

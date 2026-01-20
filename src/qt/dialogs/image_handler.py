"""
AutoTabloide AI - Image Handler Dialog
=======================================
Modal para processamento de imagens: busca, upload, remoção de fundo, crop.
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTabWidget, QWidget,
    QLabel, QPushButton, QLineEdit, QGridLayout, QFrame,
    QFileDialog, QProgressBar, QSlider, QMessageBox,
    QScrollArea
)
from PySide6.QtCore import Qt, Signal, Slot, QThread, QSize
from PySide6.QtGui import QPixmap, QImage
from typing import Optional, Dict, Any
from pathlib import Path


class ImageProcessThread(QThread):
    """Thread para processamento de imagem com integração real."""
    
    progress = Signal(int, str)  # valor, mensagem
    finished = Signal(str)  # hash do resultado
    error = Signal(str)
    
    def __init__(self, image_path: str, operations: list, output_dir: str = None, parent=None):
        super().__init__(parent)
        self.image_path = image_path
        self.operations = operations
        self.output_dir = output_dir or "AutoTabloide_System_Root/assets/store"
    
    def run(self):
        """Executa processamento real com PIL e rembg."""
        try:
            import hashlib
            from PIL import Image
            
            self.progress.emit(10, "Carregando imagem...")
            img = Image.open(self.image_path)
            
            if "remove_bg" in self.operations:
                self.progress.emit(40, "Removendo fundo (U2-Net)...")
                try:
                    from rembg import remove
                    img = remove(img)
                except ImportError:
                    self.progress.emit(45, "rembg não disponível, pulando remoção de fundo")
            
            if "autocrop" in self.operations:
                self.progress.emit(60, "Auto-crop inteligente...")
                bbox = img.getbbox()
                if bbox:
                    img = img.crop(bbox)
            
            if "upscale" in self.operations:
                self.progress.emit(75, "Upscale 2x (Lanczos)...")
                new_size = (img.width * 2, img.height * 2)
                img = img.resize(new_size, Image.LANCZOS)
            
            self.progress.emit(90, "Salvando no cofre...")
            
            # Calcula hash do conteúdo
            from io import BytesIO
            buffer = BytesIO()
            if img.mode == 'RGBA':
                img.save(buffer, 'PNG')
                ext = '.png'
            else:
                img.save(buffer, 'JPEG', quality=95)
                ext = '.jpg'
            
            image_bytes = buffer.getvalue()
            img_hash = hashlib.md5(image_bytes).hexdigest()[:16]
            
            # Salva com nome baseado no hash
            output_path = Path(self.output_dir) / f"{img_hash}{ext}"
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_path, 'wb') as f:
                f.write(image_bytes)
            
            self.progress.emit(100, "Concluído!")
            self.finished.emit(img_hash)
            
        except Exception as e:
            self.error.emit(str(e))


class ImageThumbnail(QFrame):
    """Thumbnail clicável de imagem."""
    
    clicked = Signal(str)  # path ou URL
    
    def __init__(self, path: str = "", parent=None):
        super().__init__(parent)
        self.path = path
        self.setFixedSize(100, 100)
        self.setStyleSheet("""
            QFrame {
                background-color: #16213e;
                border: 2px solid #2D2D44;
                border-radius: 8px;
            }
            QFrame:hover {
                border-color: #6C5CE7;
            }
        """)
        self.setCursor(Qt.PointingHandCursor)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setStyleSheet("color: #808080;")
        self.image_label.setText("📷")
        layout.addWidget(self.image_label)
    
    def set_image(self, pixmap: QPixmap) -> None:
        """Define imagem do thumbnail."""
        scaled = pixmap.scaled(
            QSize(92, 92), 
            Qt.KeepAspectRatio, 
            Qt.SmoothTransformation
        )
        self.image_label.setPixmap(scaled)
    
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit(self.path)


class ImageHandlerDialog(QDialog):
    """Diálogo de processamento de imagens."""
    
    image_saved = Signal(str)  # hash da imagem
    
    def __init__(self, product: Dict[str, Any] = None, parent=None):
        super().__init__(parent)
        self.product = product or {}
        self.current_image_path: Optional[str] = None
        self._setup_ui()
    
    def _setup_ui(self) -> None:
        """Configura interface."""
        self.setWindowTitle("🖼️ Image Handler")
        self.setMinimumSize(800, 600)
        self.resize(900, 700)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        
        # Header com info do produto
        header = QFrame()
        header.setStyleSheet("""
            QFrame {
                background-color: #1A1A2E;
                border-radius: 8px;
                padding: 8px;
            }
        """)
        header_layout = QHBoxLayout(header)
        
        product_name = self.product.get("nome_sanitizado", "Produto")
        title = QLabel(f"📦 {product_name}")
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: #FFFFFF;")
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        layout.addWidget(header)
        
        # Tabs de fonte de imagem
        tabs = QTabWidget()
        
        # Tab 1: Busca Automática
        tabs.addTab(self._create_search_tab(), "🔍 Busca Web")
        
        # Tab 2: Upload Manual
        tabs.addTab(self._create_upload_tab(), "📁 Upload")
        
        # Tab 3: Clipboard
        tabs.addTab(self._create_clipboard_tab(), "📋 Clipboard")
        
        layout.addWidget(tabs)
        
        # Área de processamento
        process_frame = QFrame()
        process_frame.setStyleSheet("""
            QFrame {
                background-color: #1A1A2E;
                border-radius: 8px;
                padding: 12px;
            }
        """)
        process_layout = QVBoxLayout(process_frame)
        
        # Preview antes/depois
        preview_layout = QHBoxLayout()
        
        # Imagem original
        original_frame = QFrame()
        original_layout = QVBoxLayout(original_frame)
        QLabel("Original").setStyleSheet("color: #808080;")
        self.original_preview = QLabel()
        self.original_preview.setFixedSize(250, 250)
        self.original_preview.setAlignment(Qt.AlignCenter)
        self.original_preview.setStyleSheet("""
            background-color: #16213e;
            border: 1px solid #2D2D44;
            border-radius: 8px;
        """)
        self.original_preview.setText("Nenhuma imagem")
        original_layout.addWidget(QLabel("Original"))
        original_layout.addWidget(self.original_preview)
        preview_layout.addWidget(original_frame)
        
        # Seta
        arrow = QLabel("➡️")
        arrow.setStyleSheet("font-size: 32px;")
        preview_layout.addWidget(arrow)
        
        # Imagem processada
        processed_frame = QFrame()
        processed_layout = QVBoxLayout(processed_frame)
        self.processed_preview = QLabel()
        self.processed_preview.setFixedSize(250, 250)
        self.processed_preview.setAlignment(Qt.AlignCenter)
        self.processed_preview.setStyleSheet("""
            background-color: #16213e;
            border: 1px solid #2D2D44;
            border-radius: 8px;
        """)
        self.processed_preview.setText("Aguardando...")
        processed_layout.addWidget(QLabel("Processado"))
        processed_layout.addWidget(self.processed_preview)
        preview_layout.addWidget(processed_frame)
        
        process_layout.addLayout(preview_layout)
        
        # Botões de processamento
        buttons_layout = QHBoxLayout()
        
        self.btn_remove_bg = QPushButton("🔮 Remover Fundo")
        self.btn_remove_bg.clicked.connect(self._remove_background)
        buttons_layout.addWidget(self.btn_remove_bg)
        
        self.btn_autocrop = QPushButton("✂️ Auto-Crop")
        self.btn_autocrop.clicked.connect(self._autocrop)
        buttons_layout.addWidget(self.btn_autocrop)
        
        self.btn_upscale = QPushButton("📈 Upscale 2x")
        self.btn_upscale.clicked.connect(self._upscale)
        buttons_layout.addWidget(self.btn_upscale)
        
        process_layout.addLayout(buttons_layout)
        
        # Progress bar
        self.progress = QProgressBar()
        self.progress.setVisible(False)
        process_layout.addWidget(self.progress)
        
        self.status_label = QLabel()
        self.status_label.setStyleSheet("color: #808080;")
        process_layout.addWidget(self.status_label)
        
        layout.addWidget(process_frame)
        
        # Footer
        footer = QHBoxLayout()
        footer.addStretch()
        
        btn_cancel = QPushButton("Cancelar")
        btn_cancel.setProperty("class", "secondary")
        btn_cancel.clicked.connect(self.reject)
        footer.addWidget(btn_cancel)
        
        self.btn_save = QPushButton("💾 Salvar Imagem")
        self.btn_save.clicked.connect(self._save_image)
        self.btn_save.setEnabled(False)
        footer.addWidget(self.btn_save)
        
        layout.addLayout(footer)
    
    def _create_search_tab(self) -> QWidget:
        """Cria tab de busca web."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Barra de busca
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Digite para buscar imagens...")
        self.search_input.setText(self.product.get("nome_sanitizado", ""))
        search_layout.addWidget(self.search_input)
        
        btn_search = QPushButton("🔍 Buscar")
        btn_search.clicked.connect(self._search_images)
        search_layout.addWidget(btn_search)
        
        layout.addLayout(search_layout)
        
        # Grid de resultados
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        
        results_widget = QWidget()
        self.results_grid = QGridLayout(results_widget)
        self.results_grid.setSpacing(8)
        
        # Placeholders
        for i in range(6):
            thumb = ImageThumbnail()
            thumb.clicked.connect(self._select_image)
            self.results_grid.addWidget(thumb, i // 3, i % 3)
        
        scroll.setWidget(results_widget)
        layout.addWidget(scroll)
        
        return widget
    
    def _create_upload_tab(self) -> QWidget:
        """Cria tab de upload."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setAlignment(Qt.AlignCenter)
        
        # Dropzone
        dropzone = QFrame()
        dropzone.setStyleSheet("""
            QFrame {
                background-color: #16213e;
                border: 2px dashed #6C5CE7;
                border-radius: 16px;
                min-height: 200px;
            }
        """)
        dropzone_layout = QVBoxLayout(dropzone)
        dropzone_layout.setAlignment(Qt.AlignCenter)
        
        icon = QLabel("📁")
        icon.setStyleSheet("font-size: 48px;")
        icon.setAlignment(Qt.AlignCenter)
        dropzone_layout.addWidget(icon)
        
        text = QLabel("Arraste uma imagem aqui\nou clique para selecionar")
        text.setStyleSheet("color: #808080; text-align: center;")
        text.setAlignment(Qt.AlignCenter)
        dropzone_layout.addWidget(text)
        
        btn_browse = QPushButton("📂 Selecionar Arquivo")
        btn_browse.clicked.connect(self._browse_file)
        dropzone_layout.addWidget(btn_browse)
        
        layout.addWidget(dropzone)
        
        return widget
    
    def _create_clipboard_tab(self) -> QWidget:
        """Cria tab de clipboard."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setAlignment(Qt.AlignCenter)
        
        icon = QLabel("📋")
        icon.setStyleSheet("font-size: 48px;")
        icon.setAlignment(Qt.AlignCenter)
        layout.addWidget(icon)
        
        text = QLabel("Cole uma imagem com Ctrl+V")
        text.setStyleSheet("color: #808080;")
        text.setAlignment(Qt.AlignCenter)
        layout.addWidget(text)
        
        btn_paste = QPushButton("📋 Colar do Clipboard")
        btn_paste.clicked.connect(self._paste_from_clipboard)
        layout.addWidget(btn_paste)
        
        return widget
    
    @Slot()
    def _search_images(self) -> None:
        """Busca imagens na web."""
        query = self.search_input.text()
        if not query:
            return
        
        # Verifica se há API key configurada para busca web
        try:
            from src.core.settings_service import get_settings
            settings = get_settings()
            api_key = settings.get("google_api_key", "")
            
            if not api_key:
                QMessageBox.information(
                    self,
                    "Configuração Necessária",
                    "🔍 Busca Web de Imagens\n\n"
                    "Esta funcionalidade requer configuração:\n\n"
                    "1. Acesse Configurações → Avançado\n"
                    "2. Insira sua Google Custom Search API Key\n"
                    "3. Configure o Search Engine ID\n\n"
                    "Alternativas disponíveis:\n"
                    "• Use a aba 'Upload Manual' para carregar imagens\n"
                    "• Use Ctrl+V para colar do clipboard"
                )
                return
            
            # Se API key configurada, tentar busca (implementação futura)
            QMessageBox.information(
                self,
                "Em Desenvolvimento", 
                f"Buscando: {query}\n\nIntegração com API em desenvolvimento."
            )
        except Exception:
            QMessageBox.information(
                self,
                "Busca Não Disponível",
                "Use a aba 'Upload Manual' para carregar imagens do seu computador,\n"
                "ou cole uma imagem do clipboard com Ctrl+V."
            )
    
    @Slot(str)
    def _select_image(self, path: str) -> None:
        """Seleciona imagem do grid."""
        self.current_image_path = path
        self.status_label.setText(f"Selecionado: {path}")
    
    @Slot()
    def _browse_file(self) -> None:
        """Abre diálogo de arquivo."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Selecionar Imagem",
            "",
            "Images (*.png *.jpg *.jpeg *.webp);;All Files (*)"
        )
        if file_path:
            self.current_image_path = file_path
            self._load_preview(file_path)
    
    @Slot()
    def _paste_from_clipboard(self) -> None:
        """Cola imagem do clipboard e salva temporariamente."""
        from PySide6.QtWidgets import QApplication
        import tempfile
        
        clipboard = QApplication.clipboard()
        image = clipboard.image()
        
        if image.isNull():
            QMessageBox.warning(self, "Clipboard", "Nenhuma imagem no clipboard!")
        else:
            # Salva temporariamente
            temp_path = Path(tempfile.gettempdir()) / "autotabloide_clipboard.png"
            image.save(str(temp_path), "PNG")
            self.current_image_path = str(temp_path)
            self._load_preview(str(temp_path))
            self.status_label.setText("Imagem carregada do clipboard")
            self.btn_save.setEnabled(True)
    
    def _load_preview(self, path: str) -> None:
        """Carrega preview de imagem."""
        pixmap = QPixmap(path)
        if not pixmap.isNull():
            scaled = pixmap.scaled(
                QSize(250, 250),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
            self.original_preview.setPixmap(scaled)
            self.btn_save.setEnabled(True)
    
    @Slot()
    def _remove_background(self) -> None:
        """Remove fundo da imagem usando rembg via thread."""
        if not self.current_image_path:
            QMessageBox.warning(self, "Aviso", "Selecione uma imagem primeiro!")
            return
        
        self.progress.setVisible(True)
        self.progress.setValue(0)
        
        # Usa ImageProcessThread para processamento real
        self._process_thread = ImageProcessThread(
            self.current_image_path,
            ["remove_bg"]
        )
        self._process_thread.progress.connect(self._on_process_progress)
        self._process_thread.finished.connect(self._on_process_finished)
        self._process_thread.error.connect(self._on_process_error)
        self._process_thread.start()
    
    @Slot()
    def _autocrop(self) -> None:
        """Auto-crop inteligente usando PIL via thread."""
        if not self.current_image_path:
            QMessageBox.warning(self, "Aviso", "Selecione uma imagem primeiro!")
            return
        
        self.progress.setVisible(True)
        self._process_thread = ImageProcessThread(
            self.current_image_path,
            ["autocrop"]
        )
        self._process_thread.progress.connect(self._on_process_progress)
        self._process_thread.finished.connect(self._on_process_finished)
        self._process_thread.error.connect(self._on_process_error)
        self._process_thread.start()
    
    @Slot()
    def _upscale(self) -> None:
        """Upscale 2x usando Lanczos via thread."""
        if not self.current_image_path:
            QMessageBox.warning(self, "Aviso", "Selecione uma imagem primeiro!")
            return
        
        self.progress.setVisible(True)
        self._process_thread = ImageProcessThread(
            self.current_image_path,
            ["upscale"]
        )
        self._process_thread.progress.connect(self._on_process_progress)
        self._process_thread.finished.connect(self._on_process_finished)
        self._process_thread.error.connect(self._on_process_error)
        self._process_thread.start()
    
    @Slot(int, str)
    def _on_process_progress(self, value: int, message: str) -> None:
        """Atualiza progresso do processamento."""
        self.progress.setValue(value)
        self.status_label.setText(message)
    
    @Slot(str)
    def _on_process_finished(self, img_hash: str) -> None:
        """Processamento concluído."""
        self.progress.setVisible(False)
        self.status_label.setText(f"Processado! Hash: {img_hash}")
        self._last_hash = img_hash
        
        # Atualiza preview processado
        assets_dir = Path("AutoTabloide_System_Root/assets/store")
        for ext in ['.png', '.jpg']:
            processed_path = assets_dir / f"{img_hash}{ext}"
            if processed_path.exists():
                self._load_processed_preview(str(processed_path))
                break
    
    @Slot(str)
    def _on_process_error(self, error: str) -> None:
        """Erro no processamento."""
        self.progress.setVisible(False)
        self.status_label.setText(f"Erro: {error}")
        QMessageBox.critical(self, "Erro", f"Erro no processamento:\n{error}")
    
    def _load_processed_preview(self, path: str) -> None:
        """Carrega preview da imagem processada."""
        pixmap = QPixmap(path)
        if not pixmap.isNull():
            scaled = pixmap.scaled(
                QSize(250, 250),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
            self.processed_preview.setPixmap(scaled)
    
    @Slot()
    def _save_image(self) -> None:
        """Salva imagem no cofre com hash calculado."""
        if not self.current_image_path:
            QMessageBox.warning(self, "Aviso", "Nenhuma imagem para salvar!")
            return
        
        # Usa thread para processar e salvar
        self._save_thread = ImageProcessThread(
            self.current_image_path,
            []  # Sem operações, apenas calcula hash e copia
        )
        self._save_thread.finished.connect(self._on_save_finished)
        self._save_thread.error.connect(self._on_process_error)
        self._save_thread.start()
    
    @Slot(str)
    def _on_save_finished(self, img_hash: str) -> None:
        """Imagem salva com sucesso."""
        self.image_saved.emit(img_hash)
        QMessageBox.information(self, "Salvo", f"Imagem salva no cofre!\nHash: {img_hash}")
        self.accept()


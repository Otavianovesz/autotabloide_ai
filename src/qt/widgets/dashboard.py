"""
AutoTabloide AI - Dashboard Widget Industrial Grade
====================================================
PROTOCOLO DE CONVERGÊNCIA INDUSTRIAL
Dashboard com dados reais do banco e monitoramento de sistema.
"""

from __future__ import annotations
from typing import Optional, Dict, Any, List
from datetime import datetime
from pathlib import Path
import asyncio

from PySide6.QtCore import Qt, Signal, Slot, QTimer, QThread, QObject
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QPushButton, QFrame, QProgressBar, QMessageBox,
    QSpacerItem, QSizePolicy
)
from PySide6.QtGui import QColor, QFont


# =============================================================================
# STATS WORKER
# =============================================================================

class StatsWorker(QObject):
    """Worker para carregar estatísticas em background."""
    
    stats_ready = Signal(dict)
    health_ready = Signal(dict)
    
    @Slot()
    def fetch_stats(self):
        """Busca estatísticas do banco."""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                stats = loop.run_until_complete(self._async_fetch_stats())
                self.stats_ready.emit(stats)
            except Exception as e:
                print(f"[Dashboard] Stats erro: {e}")
                self.stats_ready.emit(self._fallback_stats())
            finally:
                loop.close()
                
        except Exception as e:
            print(f"[Dashboard] Erro geral: {e}")
            self.stats_ready.emit(self._fallback_stats())
    
    @Slot()
    def check_health(self):
        """Verifica saúde dos serviços."""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                health = loop.run_until_complete(self._async_check_health())
                self.health_ready.emit(health)
            except Exception as e:
                print(f"[Dashboard] Health erro: {e}")
                self.health_ready.emit(self._fallback_health())
            finally:
                loop.close()
        except:
            self.health_ready.emit(self._fallback_health())
    
    async def _async_fetch_stats(self) -> Dict:
        """Busca contagens reais do banco."""
        try:
            from src.core.database import get_db
            from sqlalchemy import text
            
            stats = {"products": 0, "layouts": 0, "projects": 0, "images": 0}
            
            async with get_db() as session:
                # Conta produtos
                result = await session.execute(text("SELECT COUNT(*) FROM produtos"))
                stats["products"] = result.scalar() or 0
                
                # Conta layouts
                try:
                    result = await session.execute(text("SELECT COUNT(*) FROM layouts_metadata"))
                    stats["layouts"] = result.scalar() or 0
                except:
                    pass
                
                # Conta projetos
                try:
                    result = await session.execute(text("SELECT COUNT(*) FROM projetos"))
                    stats["projects"] = result.scalar() or 0
                except:
                    pass
            
            # Conta imagens no cofre
            store = Path("AutoTabloide_System_Root/assets/store")
            if store.exists():
                stats["images"] = len(list(store.glob("*.png")))
            
            return stats
            
        except Exception as e:
            print(f"[Stats] Erro: {e}")
            return self._fallback_stats()
    
    async def _async_check_health(self) -> Dict:
        """Verifica saúde do sistema."""
        health = {
            "db_ok": False,
            "db_latency": 0,
            "sentinel_ok": False,
            "llm_ok": False,
        }
        
        try:
            from src.core.database import check_db_health
            result = await check_db_health()
            health["db_ok"] = result.get("status") == "healthy"
            health["db_latency"] = result.get("latency_ms", 0)
        except:
            pass
        
        # Sentinel
        sentinel_lock = Path("AutoTabloide_System_Root/temp_render/.sentinel.lock")
        health["sentinel_ok"] = sentinel_lock.exists()
        
        # LLM
        models_path = Path("AutoTabloide_System_Root/bin/models")
        if models_path.exists():
            health["llm_ok"] = len(list(models_path.glob("*.gguf"))) > 0
        
        return health
    
    def _fallback_stats(self) -> Dict:
        return {"products": 0, "layouts": 0, "projects": 0, "images": 0}
    
    def _fallback_health(self) -> Dict:
        return {"db_ok": False, "db_latency": 0, "sentinel_ok": False, "llm_ok": False}


# =============================================================================
# UI COMPONENTS
# =============================================================================

class StatCard(QFrame):
    """Card de estatística visual."""
    
    clicked = Signal()
    
    def __init__(
        self,
        title: str,
        value: str = "0",
        subtitle: str = "",
        icon: str = "",
        accent_color: str = "#6C5CE7",
        parent=None
    ):
        super().__init__(parent)
        self.accent_color = accent_color
        self.setCursor(Qt.PointingHandCursor)
        
        self.setStyleSheet(f"""
            QFrame {{
                background-color: #1A1A2E;
                border: 1px solid #2D2D44;
                border-radius: 12px;
                padding: 16px;
            }}
            QFrame:hover {{
                border-color: {accent_color};
            }}
        """)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(8)
        
        header = QHBoxLayout()
        if icon:
            icon_label = QLabel(icon)
            icon_label.setStyleSheet("font-size: 24px;")
            header.addWidget(icon_label)
        
        title_label = QLabel(title)
        title_label.setStyleSheet("color: #808080; font-size: 12px; font-weight: 600;")
        header.addWidget(title_label)
        header.addStretch()
        layout.addLayout(header)
        
        self.value_label = QLabel(value)
        self.value_label.setStyleSheet(f"font-size: 36px; font-weight: bold; color: {accent_color};")
        layout.addWidget(self.value_label)
        
        if subtitle:
            sub = QLabel(subtitle)
            sub.setStyleSheet("color: #606060; font-size: 11px;")
            layout.addWidget(sub)
    
    def set_value(self, value: str):
        self.value_label.setText(value)
    
    def mousePressEvent(self, event):
        self.clicked.emit()
        super().mousePressEvent(event)


class StatusIndicator(QFrame):
    """Indicador de status LED."""
    
    def __init__(self, name: str, parent=None):
        super().__init__(parent)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)
        
        self.led = QLabel()
        self.led.setFixedSize(10, 10)
        layout.addWidget(self.led)
        
        self.name_label = QLabel(name)
        self.name_label.setStyleSheet("color: #A0A0A0; font-size: 12px;")
        layout.addWidget(self.name_label)
        
        layout.addStretch()
        
        self.status_label = QLabel("Verificando...")
        self.status_label.setStyleSheet("font-size: 11px; color: #606060;")
        layout.addWidget(self.status_label)
        
        self.set_status(False)
    
    def set_status(self, active: bool, message: str = ""):
        if active:
            self.led.setStyleSheet("background-color: #2ECC71; border-radius: 5px;")
            self.status_label.setText(message or "Online")
            self.status_label.setStyleSheet("color: #2ECC71; font-size: 11px;")
        else:
            self.led.setStyleSheet("background-color: #E74C3C; border-radius: 5px;")
            self.status_label.setText(message or "Offline")
            self.status_label.setStyleSheet("color: #E74C3C; font-size: 11px;")


# =============================================================================
# DASHBOARD WIDGET
# =============================================================================

class DashboardWidget(QWidget):
    """Dashboard principal com dados reais."""
    
    navigate_to = Signal(int)
    
    def __init__(self, container=None, parent=None):
        super().__init__(parent)
        self.container = container
        
        # Worker thread
        self._worker_thread = QThread()
        self._stats_worker = StatsWorker()
        self._stats_worker.moveToThread(self._worker_thread)
        self._stats_worker.stats_ready.connect(self._on_stats_received)
        self._stats_worker.health_ready.connect(self._on_health_received)
        self._worker_thread.start()
        
        self._setup_ui()
        self._setup_refresh_timer()
        
        # Carrega com delay
        QTimer.singleShot(500, self._load_all)
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(24)
        
        # Header
        header = QHBoxLayout()
        
        title = QLabel("Dashboard")
        title.setStyleSheet("font-size: 32px; font-weight: bold; color: #FFFFFF;")
        header.addWidget(title)
        
        header.addStretch()
        
        self.last_update = QLabel("Carregando...")
        self.last_update.setStyleSheet("color: #606060;")
        header.addWidget(self.last_update)
        
        layout.addLayout(header)
        
        # Cards
        cards = QGridLayout()
        cards.setSpacing(16)
        
        self.card_products = StatCard("PRODUTOS", "...", "no banco", "📦", "#6C5CE7")
        self.card_products.clicked.connect(lambda: self.navigate_to.emit(1))
        cards.addWidget(self.card_products, 0, 0)
        
        self.card_layouts = StatCard("LAYOUTS", "...", "templates SVG", "🎨", "#00CEC9")
        cards.addWidget(self.card_layouts, 0, 1)
        
        self.card_projects = StatCard("PROJETOS", "...", "salvos", "📋", "#FDCB6E")
        self.card_projects.clicked.connect(lambda: self.navigate_to.emit(2))
        cards.addWidget(self.card_projects, 1, 0)
        
        self.card_images = StatCard("IMAGENS", "...", "no cofre", "🖼️", "#E17055")
        cards.addWidget(self.card_images, 1, 1)
        
        layout.addLayout(cards)
        
        # Status
        status_frame = QFrame()
        status_frame.setStyleSheet("background-color: #1A1A2E; border-radius: 12px; padding: 16px;")
        status_layout = QVBoxLayout(status_frame)
        
        status_title = QLabel("Status do Sistema")
        status_title.setStyleSheet("font-weight: bold; color: #FFFFFF; font-size: 14px;")
        status_layout.addWidget(status_title)
        
        self.status_db = StatusIndicator("Banco de Dados (SQLite WAL)")
        status_layout.addWidget(self.status_db)
        
        self.status_sentinel = StatusIndicator("Sentinel (Processo IA)")
        status_layout.addWidget(self.status_sentinel)
        
        self.status_llm = StatusIndicator("Modelo LLM (GGUF)")
        status_layout.addWidget(self.status_llm)
        
        layout.addWidget(status_frame)
        
        # Ações rápidas
        actions = QFrame()
        actions.setStyleSheet("background-color: #1A1A2E; border-radius: 12px; padding: 16px;")
        actions_layout = QVBoxLayout(actions)
        
        actions_title = QLabel("Ações Rápidas")
        actions_title.setStyleSheet("font-weight: bold; color: #FFFFFF;")
        actions_layout.addWidget(actions_title)
        
        btns = QHBoxLayout()
        
        btn_snapshot = QPushButton("📸 Criar Snapshot")
        btn_snapshot.clicked.connect(self._create_snapshot)
        btns.addWidget(btn_snapshot)
        
        btn_import = QPushButton("📥 Importar Excel")
        btn_import.clicked.connect(lambda: self.navigate_to.emit(1))
        btns.addWidget(btn_import)
        
        btn_new = QPushButton("✨ Novo Projeto")
        btn_new.clicked.connect(lambda: self.navigate_to.emit(2))
        btns.addWidget(btn_new)
        
        btn_factory = QPushButton("🏭 Fábrica")
        btn_factory.clicked.connect(lambda: self.navigate_to.emit(3))
        btns.addWidget(btn_factory)
        
        btns.addStretch()
        actions_layout.addLayout(btns)
        layout.addWidget(actions)
        
        layout.addSpacerItem(QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding))
    
    def _setup_refresh_timer(self):
        self.refresh_timer = QTimer(self)
        self.refresh_timer.timeout.connect(self._load_all)
        self.refresh_timer.start(30000)
    
    def _load_all(self):
        QTimer.singleShot(0, self._stats_worker.fetch_stats)
        QTimer.singleShot(100, self._stats_worker.check_health)
    
    @Slot(dict)
    def _on_stats_received(self, stats: Dict):
        self.card_products.set_value(f"{stats.get('products', 0):,}".replace(",", "."))
        self.card_layouts.set_value(str(stats.get('layouts', 0)))
        self.card_projects.set_value(str(stats.get('projects', 0)))
        self.card_images.set_value(str(stats.get('images', 0)))
        self.last_update.setText(f"Atualizado: {datetime.now().strftime('%H:%M:%S')}")
    
    @Slot(dict)
    def _on_health_received(self, health: Dict):
        db_ok = health.get("db_ok", False)
        latency = health.get("db_latency", 0)
        self.status_db.set_status(db_ok, f"{latency:.1f}ms" if db_ok else "Erro")
        self.status_sentinel.set_status(health.get("sentinel_ok", False))
        self.status_llm.set_status(health.get("llm_ok", False))
    
    @Slot()
    def _create_snapshot(self):
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            from src.core.database import create_atomic_snapshot
            path = loop.run_until_complete(create_atomic_snapshot())
            loop.close()
            
            QMessageBox.information(self, "Snapshot", f"Criado: {path}")
        except Exception as e:
            QMessageBox.warning(self, "Erro", str(e))
    
    def closeEvent(self, event):
        self._worker_thread.quit()
        self._worker_thread.wait()
        super().closeEvent(event)

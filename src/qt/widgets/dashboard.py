"""
AutoTabloide AI - Dashboard Widget Industrial Grade
====================================================
PROTOCOLO DE CONVERGÊNCIA INDUSTRIAL
Dashboard com dados reais, grid de projetos e monitoramento.
"""

from __future__ import annotations
from typing import Optional, Dict, Any, List
from datetime import datetime
from pathlib import Path
import asyncio
import logging
import math

from PySide6.QtCore import Qt, Signal, Slot, QTimer, QThread, QObject, QSize
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QPushButton, QFrame, QScrollArea, QMessageBox,
    QSpacerItem, QSizePolicy, QMenu
)
from PySide6.QtGui import QColor, QFont, QPixmap, QIcon

from src.qt.styles.theme import set_class


# =============================================================================
# WORKER
# =============================================================================

class DashboardWorker(QObject):
    """Worker unificado para carregar dados do dashboard em background."""
    
    stats_ready = Signal(dict)
    health_ready = Signal(dict)
    projects_ready = Signal(list)
    
    def __init__(self):
        super().__init__()
        self._logger = logging.getLogger("AutoTabloide.Dashboard")
    
    @Slot()
    def fetch_all(self):
        """Busca todos os dados (stats, health, projects)."""
        import threading
        
        def _run():
            import asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                # 1. Stats
                try:
                    stats = loop.run_until_complete(self._async_fetch_stats())
                    QTimer.singleShot(0, lambda: self.stats_ready.emit(stats))
                except Exception as e:
                    self._logger.error(f"Stats error: {e}")
                    QTimer.singleShot(0, lambda: self.stats_ready.emit(self._fallback_stats()))
                
                # 2. Health
                try:
                    health = loop.run_until_complete(self._async_check_health())
                    QTimer.singleShot(0, lambda: self.health_ready.emit(health))
                except Exception as e:
                    self._logger.error(f"Health error: {e}")
                    QTimer.singleShot(0, lambda: self.health_ready.emit(self._fallback_health()))
                
                # 3. Projects
                try:
                    projects = loop.run_until_complete(self._async_fetch_projects())
                    QTimer.singleShot(0, lambda: self.projects_ready.emit(projects))
                except Exception as e:
                    self._logger.error(f"Projects fetch error: {e}")
                    QTimer.singleShot(0, lambda: self.projects_ready.emit([]))
                    
            finally:
                loop.close()
        
        thread = threading.Thread(target=_run, daemon=True)
        thread.start()

    async def _async_fetch_stats(self) -> Dict:
        from src.core.database import AsyncSessionLocal
        from sqlalchemy import text
        
        stats = {"products": 0, "layouts": 0, "projects": 0, "images": 0}
        
        async with AsyncSessionLocal() as session:
            # Conta produtos
            r = await session.execute(text("SELECT COUNT(*) FROM produtos"))
            stats["products"] = r.scalar() or 0
            
            # Conta layouts
            try:
                r = await session.execute(text("SELECT COUNT(*) FROM layouts_metadata"))
                stats["layouts"] = r.scalar() or 0
            except: pass
            
            # Conta projetos
            try:
                r = await session.execute(text("SELECT COUNT(*) FROM projetos"))
                stats["projects"] = r.scalar() or 0
            except: pass
        
        # Conta imagens no cofre
        store = Path("AutoTabloide_System_Root/assets/store")
        if store.exists():
            stats["images"] = len(list(store.glob("*.png")))
        
        return stats

    async def _async_check_health(self) -> Dict:
        health = {"db_ok": False, "db_latency": 0, "sentinel_ok": False, "llm_ok": False}
        
        try:
            from src.core.database import check_db_health
            r = await check_db_health()
            health["db_ok"] = r.get("status") == "healthy"
            health["db_latency"] = r.get("latency_ms", 0)
        except: pass
        
        sentinel_lock = Path("AutoTabloide_System_Root/temp_render/.sentinel.lock")
        health["sentinel_ok"] = sentinel_lock.exists()
        
        models_path = Path("AutoTabloide_System_Root/bin/models")
        if models_path.exists():
            health["llm_ok"] = len(list(models_path.glob("*.gguf"))) > 0
            
        return health

    async def _async_fetch_projects(self) -> List[Dict]:
        from src.core.container import get_container
        from src.core.project_manager import ProjectManager
        
        container = get_container()
        pm = container.resolve(ProjectManager)
        return await pm.list_recent(limit=10)

    def _fallback_stats(self) -> Dict:
        return {"products": 0, "layouts": 0, "projects": 0, "images": 0}
    
    def _fallback_health(self) -> Dict:
        return {"db_ok": False, "db_latency": 0, "sentinel_ok": False, "llm_ok": False}


# =============================================================================
# PROJECT CARD
# =============================================================================

class ProjectCard(QFrame):
    """Card visual de projeto com preview."""
    
    opened = Signal(int)  # project_id
    deleted = Signal(int)
    
    def __init__(self, project_data: Dict, parent=None):
        super().__init__(parent)
        self.data = project_data
        self.setCursor(Qt.PointingHandCursor)
        self.setProperty("class", "project-card")
        self.setFixedSize(240, 200)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # 1. Preview Area
        self.preview_lbl = QLabel()
        self.preview_lbl.setAlignment(Qt.AlignCenter)
        self.preview_lbl.setProperty("class", "card-preview")
        self.preview_lbl.setFixedHeight(130)
        
        preview_path = project_data.get("preview_path")
        if preview_path and Path(preview_path).exists():
            pixmap = QPixmap(preview_path)
            if not pixmap.isNull():
                self.preview_lbl.setPixmap(pixmap.scaled(
                    QSize(240, 130), 
                    Qt.KeepAspectRatioByExpanding, 
                    Qt.SmoothTransformation
                ))
            else:
                self.preview_lbl.setText("🖼️")
        else:
            self.preview_lbl.setText("📄") # Placeholder
            
        layout.addWidget(self.preview_lbl)
        
        # 2. Info Area
        info = QFrame()
        info.setProperty("class", "card-info")
        info_layout = QVBoxLayout(info)
        info_layout.setContentsMargins(12, 8, 12, 8)
        info_layout.setSpacing(4)
        
        # Title
        title = QLabel(project_data.get("nome", "Sem Nome"))
        title.setProperty("class", "card-title")
        title.setWordWrap(False)
        info_layout.addWidget(title)
        
        # Meta
        updated = project_data.get("last_modified") or ""
        if updated:
            try:
                dt = datetime.fromisoformat(updated)
                updated = dt.strftime("%d/%m %H:%M")
            except: pass
            
        meta = QLabel(f"{updated} • {project_data.get('layout_nome', 'Custom')}")
        meta.setProperty("class", "card-meta")
        info_layout.addWidget(meta)
        
        layout.addWidget(info)
        
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.opened.emit(self.data["id"])
        elif event.button() == Qt.RightButton:
            self._show_context_menu(event.pos())
            
    def _show_context_menu(self, pos):
        menu = QMenu(self)
        
        open_action = menu.addAction("Abrir Projeto")
        open_action.triggered.connect(lambda: self.opened.emit(self.data["id"]))
        
        menu.addSeparator()
        
        del_action = menu.addAction("Excluir")
        del_action.triggered.connect(self._confirm_delete)
        
        menu.exec(self.mapToGlobal(pos))
        
    def _confirm_delete(self):
        reply = QMessageBox.question(
            self, "Excluir Projeto",
            f"Tem certeza que deseja excluir '{self.data.get('nome')}'?\nEssa ação não pode ser desfeita.",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.deleted.emit(self.data["id"])


# =============================================================================
# PROJECT GRID RESPONSIVA
# =============================================================================

class ProjectGrid(QWidget):
    """Grid responsivo que ajusta colunas baseado na largura."""
    
    project_opened = Signal(int)
    project_deleted = Signal(int)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QGridLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(16)
        self.layout.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        
        self.cards = []
        
    def set_projects(self, projects: List[Dict]):
        # Limpa
        for card in self.cards:
            self.layout.removeWidget(card)
            card.deleteLater()
        self.cards.clear()
        
        # Cria cards
        for p in projects:
            card = ProjectCard(p)
            card.opened.connect(self.project_opened.emit)
            card.deleted.connect(self.project_deleted.emit)
            self.cards.append(card)
            
        self._reflow()
        
    def resizeEvent(self, event):
        self._reflow()
        super().resizeEvent(event)
        
    def _reflow(self):
        """Recalcula posições no grid."""
        if not self.cards: return
        
        width = self.width()
        card_w = 240 + 16 # card width + spacing
        
        cols = max(1, width // card_w)
        
        # Re-adiciona ao layout
        for i, card in enumerate(self.cards):
            row = i // cols
            col = i % cols
            self.layout.addWidget(card, row, col)


# =============================================================================
# COMPONENTS
# =============================================================================

class StatCard(QFrame):
    """Card de estatística."""
    clicked = Signal()
    def __init__(self, title, value="0", subtitle="", icon="", color="#6C5CE7", parent=None):
        super().__init__(parent)
        self.setCursor(Qt.PointingHandCursor)
        self.setProperty("class", "stat-card")
        
        l = QVBoxLayout(self)
        
        h = QHBoxLayout()
        if icon:
            il = QLabel(icon)
            il.setProperty("class", "icon-sm")
            h.addWidget(il)
        tl = QLabel(title)
        tl.setProperty("class", "card-title")
        h.addWidget(tl)
        h.addStretch()
        l.addLayout(h)
        
        self.val = QLabel(value)
        self.val.setProperty("class", "value-accent")
        # Inline style is easier for dynamic color here, but let's try to stick to class if possible
        # Need to dynamically set color. 
        self.val.setStyleSheet(f"color: {color}; font-size: 24px; font-weight: bold;")
        l.addWidget(self.val)
        
        if subtitle:
            sl = QLabel(subtitle)
            sl.setProperty("class", "card-subtitle")
            l.addWidget(sl)
            
    def set_value(self, v): self.val.setText(v)
    def mousePressEvent(self, e): self.clicked.emit(); super().mousePressEvent(e)

class EmptyStateWidget(QFrame):
    """Empty State com Call to Action."""
    action_clicked = Signal()
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setProperty("class", "empty-state")
        l = QVBoxLayout(self)
        l.setAlignment(Qt.AlignCenter)
        l.setSpacing(20)
        
        icon = QLabel("✨")
        icon.setStyleSheet("font-size: 64px;")
        icon.setAlignment(Qt.AlignCenter)
        l.addWidget(icon)
        
        t = QLabel("Comece seu Primeiro Projeto")
        t.setProperty("class", "title-lg")
        t.setAlignment(Qt.AlignCenter)
        l.addWidget(t)
        
        d = QLabel("Crie encartes profissionais em segundos usando nossos templates inteligentes.")
        d.setProperty("class", "text-muted")
        d.setAlignment(Qt.AlignCenter)
        d.setWordWrap(True)
        l.addWidget(d)
        
        btn = QPushButton("Criar Novo Tablóide")
        btn.setProperty("class", "btn-primary") # Assuming btn-primary exists in theme.qss or mapping
        # Let's rely on cta-button from theme.qss or add it
        btn.setStyleSheet("background-color: #6C5CE7; color: white; padding: 12px 24px; border-radius: 8px; font-weight: bold; font-size: 14px;")
        btn.setCursor(Qt.PointingHandCursor)
        btn.clicked.connect(self.action_clicked.emit)
        l.addWidget(btn, alignment=Qt.AlignCenter)


# =============================================================================
# MAIN DASHBOARD
# =============================================================================

class DashboardWidget(QWidget):
    """Dashboard Principal."""
    
    navigate_to = Signal(int)
    project_selected = Signal(int)
    
    def __init__(self, container=None, parent=None):
        super().__init__(parent)
        self.container = container
        
        # Worker setup
        self._worker_thread = QThread()
        self._worker = DashboardWorker()
        self._worker.moveToThread(self._worker_thread)
        self._worker.stats_ready.connect(self._on_stats)
        self._worker.health_ready.connect(self._on_health)
        self._worker.projects_ready.connect(self._on_projects)
        self._worker_thread.start()
        
        self._setup_ui()
        
        # Timer refresh (30s)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._refresh)
        self.timer.start(30000)
        
        # Initial load
        QTimer.singleShot(500, self._refresh)
        
    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Scroll Area principal
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        
        content = QWidget()
        self.layout = QVBoxLayout(content)
        self.layout.setContentsMargins(32, 32, 32, 32)
        self.layout.setSpacing(32)
        
        # 1. Header & Stats
        self._setup_header()
        
        # 2. Quick Actions
        self._setup_actions()
        
        # 3. Projects Section
        proj_header = QHBoxLayout()
        title = QLabel("Projetos Recentes")
        title.setProperty("class", "section-title")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: white;")
        proj_header.addWidget(title)
        proj_header.addStretch()
        self.layout.addLayout(proj_header)
        
        # Stack para alternar entre Grid e Empty State
        from PySide6.QtWidgets import QStackedWidget
        self.proj_stack = QStackedWidget()
        
        # Page 0: Grid
        self.grid = ProjectGrid()
        self.grid.project_opened.connect(self._open_project)
        self.grid.project_deleted.connect(self._delete_project)
        self.proj_stack.addWidget(self.grid)
        
        # Page 1: Empty
        self.empty = EmptyStateWidget()
        self.empty.action_clicked.connect(lambda: self.navigate_to.emit(2)) # 2 = Factory? Check mapping. Usually 2 = Atelier/New?
        self.proj_stack.addWidget(self.empty)
        
        self.layout.addWidget(self.proj_stack)
        self.layout.addStretch()
        
        scroll.setWidget(content)
        main_layout.addWidget(scroll)
        
    def _setup_header(self):
        # Stats Row
        stats = QHBoxLayout()
        stats.setSpacing(16)
        
        self.card_prods = StatCard("PRODUTOS", "...", "cadastrados", "📦", "#6C5CE7")
        self.card_prods.clicked.connect(lambda: self.navigate_to.emit(1))
        stats.addWidget(self.card_prods)
        
        self.card_layouts = StatCard("LAYOUTS", "...", "disponíveis", "🎨", "#00CEC9")
        stats.addWidget(self.card_layouts)
        
        self.card_imgs = StatCard("IMAGENS", "...", "no cofre", "🖼️", "#E17055")
        self.card_imgs.clicked.connect(lambda: self.navigate_to.emit(4)) # Cofre
        stats.addWidget(self.card_imgs)
        
        # System Health (compacto)
        self.health_card = StatCard("SISTEMA", "OK", "Verificando...", "🖥️", "#2ECC71")
        stats.addWidget(self.health_card)
        
        self.layout.addLayout(stats)
        
    def _setup_actions(self):
        actions = QFrame()
        actions.setStyleSheet("background-color: #1A1A2E; border-radius: 12px; padding: 16px;")
        l = QHBoxLayout(actions)
        
        def _add_btn(text, icon, slot, primary=False):
            btn = QPushButton(f" {icon}  {text}")
            btn.setCursor(Qt.PointingHandCursor)
            style = "padding: 12px 20px; border-radius: 8px; font-weight: bold;"
            if primary:
                style += "background-color: #6C5CE7; color: white;"
            else:
                style += "background-color: #2D2D44; color: #A0A0A0; border: 1px solid #3E3E5E;"
            btn.setStyleSheet(style)
            btn.clicked.connect(slot)
            l.addWidget(btn)
            
        _add_btn("Novo Projeto", "✨", lambda: self.navigate_to.emit(2), True) # Atelie
        _add_btn("Importar Excel", "📥", lambda: self.navigate_to.emit(1)) # Estoque (Import)
        _add_btn("Configurações", "⚙️", lambda: self.navigate_to.emit(5)) # Settings
        
        l.addStretch()
        self.layout.addWidget(actions)

    def _refresh(self):
        QTimer.singleShot(0, self._worker.fetch_all)
        
    @Slot(dict)
    def _on_stats(self, s):
        self.card_prods.set_value(f"{s.get('products',0):,}".replace(",", "."))
        self.card_layouts.set_value(str(s.get('layouts',0)))
        self.card_imgs.set_value(str(s.get('images',0)))
        
    @Slot(dict)
    def _on_health(self, h):
        ok = h.get('db_ok') and h.get('sentinel_ok')
        self.health_card.set_value("ONLINE" if ok else "ATENÇÃO")
        self.health_card.val.setStyleSheet(f"color: {'#2ECC71' if ok else '#E74C3C'}; font-size: 24px; font-weight: bold;")
        
    @Slot(list)
    def _on_projects(self, projects):
        if not projects:
            self.proj_stack.setCurrentWidget(self.empty)
        else:
            self.grid.set_projects(projects)
            self.proj_stack.setCurrentWidget(self.grid)

    def _open_project(self, pid):
        # Sinaliza para MainWindow abrir o projeto
        # MainWindow deve ouvir 'project_selected' ou similar. 
        # Vou emitir navigate_to(2) (Atelie) mas preciso passar o ID.
        # Por enquanto, vou emitir um signal customizado que MainWindow precisará conectar.
        # Ou melhor, usar o container para setar o contexto global e navegar.
        
        # TODO: MainWindow integration for opening project
        # Por hora, apenas navega para o Atelie, que deve carregar o "projeto atual"
        # O ideal seria self.project_selected.emit(pid)
        
        # Como o user pediu apenas Dashboard agora, vou assumir que a integração de "Abrir"
        # será feita depois, ou vou tentar injetar no ProjectManager global?
        
        # Hack rápido: setar no container ou similar
        # Mas o correto é emitir signal.
        self.project_selected.emit(pid)
        
    def _delete_project(self, pid):
        # Excluir via ProjectManager (async fire-and-forget for now wrapped in thread)
        import threading
        def _run():
            import asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                from src.core.container import get_container
                from src.core.project_manager import ProjectManager
                pm = get_container().resolve(ProjectManager)
                loop.run_until_complete(pm.delete_project(pid))
                QTimer.singleShot(0, self._refresh)
            finally:
                loop.close()
        threading.Thread(target=_run, daemon=True).start()

    def closeEvent(self, e):
        self._worker_thread.quit()
        self._worker_thread.wait()
        super().closeEvent(e)

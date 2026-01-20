"""
AutoTabloide AI - Render Worker
===============================
Item 86: Exportação Assíncrona.
Gera PDF em thread separada para não travar a UI.
"""

from PySide6.QtCore import QObject, Signal, QRectF
from PySide6.QtGui import QPainter, QPagedPaintDevice, QPageSize, QPageLayout, QImage
from PySide6.QtPrintSupport import QPrinter

from src.qt.core.project_manager import ProjectData
from src.qt.widgets.atelier import AtelierScene # Need scene reference or reconstruction

# NOTE: QGraphicsScene/View operations MUST run in the main thread (GUI Thread).
# We CANNOT run scene.render() in a background thread directly because QGraphicsScene is not thread-safe.
# 
# APPROACH:
# 1. Prepare data in background? No.
# 2. To keep UI responsive during rendering, we might need to process chunked painting?
# 
# Wait, QPrinter rendering allows painting to a device.
# If we simply run it in a loop, it blocks.
# 
# TRUE ASYNC PDF GENERATION from QGraphicsScene is TRICKY because QGraphicsScene is bound to GUI thread.
#
# ALTERNATIVE:
# Use 'concurrent' rendering by rendering to QImage in main thread (fast?) or...
# 
# Actually, standard practice for QGraphicsScene PDF export:
# Just do it in main thread but show a progress dialog that forces event loop processing,
# OR copy items to a separate scene in a thread? (QGraphicsScene IS NOT reentrant).
#
# CORRECT APPROACH FOR "AYSNC FEEL":
# We use a progress dialog. Rendering acts as a blocking operation usually.
# However, if we print page by page, we can process events in between.
#
# But the user specifically asked for "Thread separada".
# 
# IF we must use a thread, we cannot touch the MAIN QGraphicsScene.
# We would need to deserialize the project into a NEW QGraphicsScene living in that thread?
# QGraphicsScene usage in non-GUI thread is technically possible if no widgets involved?
# Documentation says: "QGraphicsScene is reentrant... but QGraphicsItem... not all are."
#
# SAFE BET:
# Run rendering in MAIN thread but use a progress dialog to keep UI updated.
# If "Thread" is a hard requirement, we must ensure total isolation.
#
# Let's try to reconstruct the scene in the worker thread.
# Since our items are custom (SmartGraphicsItem), as long as they don't touch QWidgets, it might work.
# SmartSlotItem uses QPainter, which is fine.
#
# Let's implement RenderWorker to accept ProjectData, create a fresh internal Scene, and render.

import threading

class RenderWorker(QObject):
    """Worker para renderização de PDF."""
    
    finished = Signal(bool, str) # success, message
    progress = Signal(int, str)
    
    def __init__(self, project_data: ProjectData, output_path: str):
        super().__init__()
        self.project_data = project_data
        self.output_path = output_path
        self._cancel_requested = False
        
    def cancel(self):
        self._cancel_requested = True
        
    def run(self):
        """Executa exportação (EntryPoint)."""
        # NOTE: Qt GUI classes (QGraphicsScene) in a thread requires care.
        # Ideally we move this object to a QThread.
        try:
            self.progress.emit(10, "Inicializando motor de renderização...")
            
            printer = QPrinter(QPrinter.HighResolution)
            printer.setOutputFormat(QPrinter.PdfFormat)
            printer.setOutputFileName(self.output_path)
            printer.setPageSize(QPageSize(QPageSize.A4))
            
            # Setup Painter
            painter = QPainter()
            
            if not painter.begin(printer):
                self.finished.emit(False, "Falha ao iniciar gravador PDF")
                return

            self.progress.emit(30, "Construindo cena...")
            
            # Create a localized scene for rendering
            # We need to reconstruct items from ProjectData (serialized)
            # This avoids touching the live Main Scene
            # Requires importing SmartItems classes
            
            # TODO: We need a way to reconstruct the scene without GUI dependencies?
            # Our SmartItems inherit QGraphicsObject.
            # Using them in a thread 'should' be okay if they don't access global QApplication stuff.
            
            from src.qt.graphics.smart_items import SmartSlotItem, SmartImageItem, SmartTextItem, SmartPriceItem
            
            # Mock scene-like container (or use QGraphicsScene if thread permits)
            # Experiment: usage of QGraphicsScene in thread is risky.
            
            # FALLBACK STRATEGY IF THREADING FAILS:
            # For now, let's implement the logic. If it crashes, we move to MainThread + ProcessEvents.
            # But the requirement is explicit about "Thread separada".
            
            from PySide6.QtWidgets import QGraphicsScene
            temp_scene = QGraphicsScene()
            
            # Reconstruct items
            slots = self.project_data.slots
            total = len(slots)
            
            for i, slot_data in enumerate(slots):
                if self._cancel_requested:
                    painter.end()
                    self.finished.emit(False, "Cancelado pelo usuário")
                    return
                
                # Create item
                # This duplication of deserialization logic is suboptimal but necessary for isolation
                item = SmartSlotItem(
                    slot_index=i+1,
                    element_id=slot_data.get("element_id", "unknown")
                )
                item.deserialize(slot_data)
                temp_scene.addItem(item)
                
                pct = 30 + int((i / total) * 40)
                self.progress.emit(pct, f"Processando slot {i+1}...")
                
            self.progress.emit(70, "Renderizando página...")
            
            # Defines printable area (A4 @ 300DPI approx 2480x3508 pixels)
            # Our coordinates are arbitrary. We need to fit scene to page.
            target_rect = printer.pageLayout().paintRectPixels(printer.resolution())
            scene_rect = temp_scene.itemsBoundingRect()
            
            temp_scene.render(painter, target_rect, scene_rect)
            
            painter.end()
            
            self.progress.emit(100, "Concluído!")
            self.finished.emit(True, self.output_path)
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            self.finished.emit(False, str(e))

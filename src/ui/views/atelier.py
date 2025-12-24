"""
AutoTabloide AI - Atelier View (A Mesa)
========================================
Tela de montagem de tabloides conforme Vol. VI, Cap. 4.
Implementa workflow completo: seleção, estante, auto-fill, override.
"""

import flet as ft
import asyncio
import json
from datetime import datetime
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, asdict, field

# Design System
from src.ui.design_system import (
    ColorScheme, Typography, Spacing, Animations
)

# Cores usando Design System
COLORS = {
    "success": ColorScheme.SUCCESS,
    "warning": ColorScheme.WARNING,
    "error": ColorScheme.ERROR,
    "info": ColorScheme.ACCENT_PRIMARY,
    "neutral": ColorScheme.TEXT_MUTED,
    "surface": ColorScheme.BG_SECONDARY,
    "surface_elevated": ColorScheme.BG_ELEVATED,
    "slot_empty": ColorScheme.SLOT_EMPTY,
    "slot_filled": ColorScheme.SLOT_FILLED,
    "slot_hover": ColorScheme.SLOT_HOVER,
}


@dataclass
class ProductInSlot:
    """Dados de um produto dentro de um slot (para Kits)."""
    product_id: int
    product_name: str
    product_price: float
    product_image: Optional[str] = None
    
    @staticmethod
    def from_product(product: Dict) -> "ProductInSlot":
        return ProductInSlot(
            product_id=product.get("id"),
            product_name=product.get("name", ""),
            product_price=product.get("price", 0.0),
            product_image=product.get("image")
        )


@dataclass
class SlotData:
    """
    Dados de um slot no canvas.
    
    Suporta múltiplos produtos (Kits) conforme Vol. VI, Cap. 4.5:
    - Arrastar N produtos para mesmo slot
    - Concatenar nomes: "Produto A + Produto B"
    - Grid de imagens automático se múltiplos hashes
    """
    slot_id: str
    products: List[ProductInSlot] = None  # Lista de produtos (Kits)
    override_name: Optional[str] = None
    override_price: Optional[float] = None
    override_price_de: Optional[float] = None
    
    def __post_init__(self):
        if self.products is None:
            self.products = []
    
    # === Compatibilidade com API anterior (single product) ===
    
    @property
    def product_id(self) -> Optional[int]:
        """Retorna ID do primeiro produto (compatibilidade)."""
        return self.products[0].product_id if self.products else None
    
    @property
    def product_name(self) -> Optional[str]:
        """Retorna nome(s) concatenado(s) para renderização."""
        if not self.products:
            return None
        if len(self.products) == 1:
            return self.products[0].product_name
        # Kits: concatena com " + "
        return " + ".join(p.product_name for p in self.products)
    
    @property
    def product_price(self) -> Optional[float]:
        """Retorna preço do primeiro produto (Kits usam override)."""
        return self.products[0].product_price if self.products else None
    
    @property
    def product_image(self) -> Optional[str]:
        """Retorna imagem do primeiro produto."""
        return self.products[0].product_image if self.products else None
    
    @property
    def all_images(self) -> List[str]:
        """Retorna todas as imagens para grid multi-imagem."""
        return [p.product_image for p in self.products if p.product_image]
    
    @property
    def is_kit(self) -> bool:
        """Verifica se slot tem múltiplos produtos."""
        return len(self.products) > 1
    
    def add_product(self, product: Dict):
        """Adiciona produto ao slot (para Kits)."""
        self.products.append(ProductInSlot.from_product(product))
    
    def clear(self):
        """Limpa todos os produtos do slot."""
        self.products = []
        self.override_name = None
        self.override_price = None
        self.override_price_de = None
    
    def set_single_product(self, product: Dict):
        """Define único produto no slot (substitui existentes)."""
        self.products = [ProductInSlot.from_product(product)]

# Importa mixin de limpeza de eventos
from src.ui.ui_safety import EventCleanupMixin


class AtelierView(EventCleanupMixin, ft.UserControl):
    """
    Tela de Montagem de Tabloides (A Mesa).
    
    Workflow:
    1. Popup inicial para seleção de layout ou projeto
    2. Canvas com slots para drag & drop
    3. Painel lateral (Estante) com produtos
    4. Modal de override por slot
    5. Auto-preenchimento
    6. Undo/Redo
    
    Passo 17: Herda de EventCleanupMixin para limpeza automática de eventos.
    """
    
    def __init__(self, page: ft.Page):
        super().__init__()
        self.page = page
        
        # Estado do projeto
        self.current_layout_id: Optional[int] = None
        self.current_project_id: Optional[int] = None
        self.layout_name: str = ""
        self.slots: Dict[str, SlotData] = {}
        self.slot_capacity: int = 0
        
        # Pilha Undo/Redo
        self.undo_stack: List[Dict] = []
        self.redo_stack: List[Dict] = []
        self.max_undo = 20
        
        # Produtos na estante (carregados do DB)
        self.shelf_products: List[Dict] = []
        self.filtered_products: List[Dict] = []
        self.search_query: str = ""
        
        # Estado da UI
        self.is_initialized: bool = False
        self.is_dirty: bool = False
        
        # Refs para componentes
        self.canvas_ref = ft.Ref[ft.Container]()
        self.shelf_ref = ft.Ref[ft.ListView]()
        self.search_ref = ft.Ref[ft.TextField]()
        
        # X-Ray Mode (Vol. VI, Cap. 2.2)
        self.xray_mode: bool = False
    
    def did_mount(self):
        """Ao montar, exibe popup de seleção e configura atalhos."""
        # Registra atalhos de teclado (Ctrl+Z, Ctrl+Shift+Z)
        self._setup_keyboard_shortcuts()
        
        if not self.is_initialized:
            self.page.run_task(self._show_project_selector)
    
    def _setup_keyboard_shortcuts(self):
        """Configura atalhos de teclado para Undo/Redo."""
        def on_keyboard(e: ft.KeyboardEvent):
            # Ignora se não estiver inicializado
            if not self.is_initialized:
                return
            
            # Ctrl+Z = Undo
            if e.key == "Z" and e.ctrl and not e.shift:
                self._undo()
                return
            
            # Ctrl+Shift+Z = Redo (também Ctrl+Y para compatibilidade)
            if (e.key == "Z" and e.ctrl and e.shift) or (e.key == "Y" and e.ctrl):
                self._redo()
                return
        
        self.page.on_keyboard_event = on_keyboard
    
    async def _show_project_selector(self):
        """Exibe popup de seleção de layout/projeto."""
        await asyncio.sleep(0.1)  # Aguarda UI renderizar
        
        # Carrega layouts disponíveis
        layouts = await self._load_available_layouts()
        projects = await self._load_saved_projects()
        
        # BUILD: Tabs para Novo / Carregar
        layout_cards = [
            self._build_layout_card(layout)
            for layout in layouts
        ]
        
        project_cards = [
            self._build_project_card(project)
            for project in projects
        ]
        
        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Selecionar Layout ou Projeto"),
            content=ft.Container(
                content=ft.Tabs(
                    selected_index=0,
                    tabs=[
                        ft.Tab(
                            text="Novo Projeto",
                            icon=ft.icons.ADD,
                            content=ft.Container(
                                content=ft.Column([
                                    ft.Text("Selecione um layout para iniciar:", size=14),
                                    ft.GridView(
                                        controls=layout_cards if layout_cards else [
                                            ft.Text("Nenhum layout disponivel. Importe templates SVG primeiro.", 
                                                   color=ft.colors.GREY_400)
                                        ],
                                        runs_count=3,
                                        max_extent=200,
                                        child_aspect_ratio=0.8,
                                        spacing=10,
                                        run_spacing=10
                                    )
                                ], scroll=ft.ScrollMode.AUTO),
                                padding=20,
                                height=400,
                                width=600
                            )
                        ),
                        ft.Tab(
                            text="Carregar Projeto",
                            icon=ft.icons.FOLDER_OPEN,
                            content=ft.Container(
                                content=ft.Column([
                                    ft.Text("Projetos salvos:", size=14),
                                    ft.ListView(
                                        controls=project_cards if project_cards else [
                                            ft.Text("Nenhum projeto salvo.", color=ft.colors.GREY_400)
                                        ],
                                        spacing=10
                                    )
                                ], scroll=ft.ScrollMode.AUTO),
                                padding=20,
                                height=400,
                                width=600
                            )
                        )
                    ]
                ),
                width=650,
                height=500
            ),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda e: self._close_dialog())
            ],
            actions_alignment=ft.MainAxisAlignment.END
        )
        
        self.page.dialog = dialog
        dialog.open = True
        self.page.update()
    
    async def _load_available_layouts(self) -> List[Dict]:
        """Carrega layouts disponíveis do banco."""
        try:
            from src.core.repositories import LayoutRepository
            from src.core.database import AsyncSessionLocal
            
            async with AsyncSessionLocal() as session:
                repo = LayoutRepository(session)
                layouts = await repo.get_all()
                return [
                    {
                        "id": l.id,
                        "name": l.nome_amigavel,
                        "type": l.tipo_midia.value if l.tipo_midia else "TABLOIDE",
                        "slots": l.capacidade_slots,
                        "file": l.arquivo_fonte
                    }
                    for l in layouts
                ]
        except Exception as e:
            print(f"[Atelier] Erro ao carregar layouts: {e}")
            return []
    
    async def _load_saved_projects(self) -> List[Dict]:
        """Carrega projetos salvos do banco."""
        try:
            from src.core.repositories import ProjectRepository
            from src.core.database import AsyncSessionLocal
            
            async with AsyncSessionLocal() as session:
                repo = ProjectRepository(session)
                projects = await repo.get_all_projects()
                return [
                    {
                        "id": p.id,
                        "name": p.nome_projeto,
                        "layout_id": p.layout_id,
                        "created": p.created_at.strftime("%d/%m/%Y") if p.created_at else "N/A",
                        "modified": p.updated_at.strftime("%d/%m/%Y") if p.updated_at else "N/A"
                    }
                    for p in projects
                ]
        except Exception as e:
            print(f"[Atelier] Erro ao carregar projetos: {e}")
            return []
    
    def _build_layout_card(self, layout: Dict) -> ft.Container:
        """Constrói card de layout para seleção."""
        type_colors = {
            "TABLOIDE": COLORS["info"],
            "CARTAZ_A4": COLORS["success"],
            "CARTAZ_GIGANTE": COLORS["warning"],
            "ETIQUETA": COLORS["neutral"]
        }
        
        return ft.Container(
            content=ft.Column([
                ft.Container(
                    content=ft.Icon(ft.icons.GRID_VIEW, size=48, color=ft.colors.WHITE54),
                    bgcolor=type_colors.get(layout["type"], COLORS["info"]),
                    border_radius=8,
                    padding=20,
                    alignment=ft.alignment.center
                ),
                ft.Text(layout["name"], size=12, weight=ft.FontWeight.BOLD, 
                       max_lines=2, overflow=ft.TextOverflow.ELLIPSIS),
                ft.Text(f"{layout['slots']} slots | {layout['type']}", 
                       size=10, color=ft.colors.GREY_400)
            ], spacing=5, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            padding=10,
            bgcolor=COLORS["surface"],
            border_radius=10,
            on_click=lambda e, l=layout: self._select_layout(l),
            on_hover=lambda e: self._on_card_hover(e)
        )
    
    def _build_project_card(self, project: Dict) -> ft.Container:
        """Constrói card de projeto para carregamento."""
        return ft.Container(
            content=ft.Row([
                ft.Icon(ft.icons.FOLDER, color=COLORS["warning"]),
                ft.Column([
                    ft.Text(project["name"], weight=ft.FontWeight.BOLD),
                    ft.Text(f"Modificado: {project['modified']}", size=12, color=ft.colors.GREY_400)
                ], expand=True, spacing=2),
                ft.IconButton(
                    ft.icons.OPEN_IN_NEW,
                    tooltip="Abrir projeto",
                    on_click=lambda e, p=project: self._load_project(p)
                )
            ]),
            padding=15,
            bgcolor=COLORS["surface"],
            border_radius=8
        )
    
    def _on_card_hover(self, e):
        """Efeito hover em cards."""
        e.control.bgcolor = COLORS["surface_elevated"] if e.data == "true" else COLORS["surface"]
        e.control.update()
    
    def _close_dialog(self):
        """Fecha diálogo."""
        if self.page.dialog:
            self.page.dialog.open = False
            self.page.update()
    
    def _select_layout(self, layout: Dict):
        """Seleciona layout para novo projeto."""
        self.current_layout_id = layout["id"]
        self.layout_name = layout["name"]
        self.slot_capacity = layout["slots"]
        
        # Inicializa slots vazios
        self.slots = {
            f"SLOT_{i:02d}": SlotData(slot_id=f"SLOT_{i:02d}")
            for i in range(1, self.slot_capacity + 1)
        }
        
        self.is_initialized = True
        self._close_dialog()
        
        # Carrega produtos para a estante
        self.page.run_task(self._load_shelf_products)
        
        self.update()
    
    def _load_project(self, project: Dict):
        """Carrega projeto salvo."""
        self.page.run_task(self._async_load_project, project)
    
    async def _async_load_project(self, project: Dict):
        """Carrega projeto de forma assíncrona."""
        try:
            from src.core.repositories import ProjectRepository
            from src.core.database import AsyncSessionLocal
            
            async with AsyncSessionLocal() as session:
                repo = ProjectRepository(session)
                proj = await repo.get_by_id(project["id"])
                
                if proj:
                    self.current_project_id = proj.id
                    self.current_layout_id = proj.layout_id
                    self.layout_name = project["name"]
                    
                    # Carrega estado dos slots (snapshot imutável)
                    estado = proj.get_slots_state() or {}
                    overrides = proj.get_overrides() or {}
                    
                    self.slots = {}
                    for slot_id, data in estado.items():
                        self.slots[slot_id] = SlotData(
                            slot_id=slot_id,
                            product_id=data.get("produto_id"),
                            product_name=data.get("nome_snapshot"),
                            product_price=data.get("preco_snapshot"),
                            product_image=data.get("img_hash_snapshot"),
                            override_name=overrides.get(slot_id, {}).get("nome"),
                            override_price=overrides.get(slot_id, {}).get("preco"),
                            override_price_de=overrides.get(slot_id, {}).get("preco_de")
                        )
                    
                    self.slot_capacity = len(self.slots)
                    self.is_initialized = True
                    
            self._close_dialog()
            await self._load_shelf_products()
            self.update()
            
        except Exception as e:
            print(f"[Atelier] Erro ao carregar projeto: {e}")
    
    async def _load_shelf_products(self, offset: int = 0, limit: int = 100):
        """
        Carrega produtos para a estante com paginação.
        Passos 11-12 do Checklist v2 - Virtualização via paginação na query.
        
        Args:
            offset: Posição inicial
            limit: Quantidade máxima por página
        """
        try:
            from src.core.repositories import ProductRepository
            from src.core.database import AsyncSessionLocal
            
            async with AsyncSessionLocal() as session:
                repo = ProductRepository(session)
                
                # Paginação na query - não carrega todos de uma vez
                products = await repo.get_all(limit=limit, offset=offset)
                total_count = await repo.count()
                
                new_products = [
                    {
                        "id": p.id,
                        "name": p.nome_sanitizado or p.sku_origem,
                        "price": float(p.preco_venda_atual) if p.preco_venda_atual else 0,
                        "price_de": float(p.preco_referencia) if p.preco_referencia else None,
                        "image": p.get_images()[0] if p.get_images() else None,
                        "quality": p.status_qualidade.value if p.status_qualidade else 0
                    }
                    for p in products
                ]
                
                if offset == 0:
                    self.shelf_products = new_products
                else:
                    self.shelf_products.extend(new_products)
                
                self.filtered_products = self.shelf_products.copy()
                self._shelf_total = total_count
                self._shelf_offset = offset + len(new_products)
                self.update()
                
        except Exception as e:
            print(f"[Atelier] Erro ao carregar produtos: {e}")
    
    def _filter_products(self, e):
        """
        Filtra produtos na estante com debounce.
        Passo 13 do Checklist v2 - Debounce de 300ms.
        """
        query = e.control.value.lower()
        self.search_query = query
        
        # Debounce: cancela timer anterior
        if hasattr(self, '_debounce_timer') and self._debounce_timer:
            self._debounce_timer.cancel()
        
        import threading
        
        def apply_filter():
            if query:
                self.filtered_products = [
                    p for p in self.shelf_products
                    if query in p["name"].lower()
                ]
            else:
                self.filtered_products = self.shelf_products.copy()
            
            # Atualiza na main thread
            if self.page:
                self.page.run_task(self._update_shelf_ui)
        
        # Timer de 300ms
        self._debounce_timer = threading.Timer(0.3, apply_filter)
        self._debounce_timer.start()
    
    async def _update_shelf_ui(self):
        """Atualiza UI da estante."""
        self.update()
    
    def _save_state_for_undo(self):
        """Salva estado atual para undo."""
        state = {slot_id: asdict(slot) for slot_id, slot in self.slots.items()}
        self.undo_stack.append(state)
        
        if len(self.undo_stack) > self.max_undo:
            self.undo_stack.pop(0)
        
        self.redo_stack.clear()
        self.is_dirty = True
    
    def _undo(self, e=None):
        """Desfaz última ação."""
        if not self.undo_stack:
            return
        
        # Salva estado atual para redo
        current = {slot_id: asdict(slot) for slot_id, slot in self.slots.items()}
        self.redo_stack.append(current)
        
        # Restaura estado anterior
        state = self.undo_stack.pop()
        self.slots = {k: SlotData(**v) for k, v in state.items()}
        
        self.update()
    
    def _redo(self, e=None):
        """Refaz ação desfeita."""
        if not self.redo_stack:
            return
        
        # Salva estado atual para undo
        current = {slot_id: asdict(slot) for slot_id, slot in self.slots.items()}
        self.undo_stack.append(current)
        
        # Restaura estado do redo
        state = self.redo_stack.pop()
        self.slots = {k: SlotData(**v) for k, v in state.items()}
        
        self.update()
    
    def _auto_fill(self, e=None):
        """Auto-preenche slots vazios com produtos da estante."""
        self._save_state_for_undo()
        
        product_index = 0
        for slot_id in sorted(self.slots.keys()):
            slot = self.slots[slot_id]
            if not slot.products and product_index < len(self.shelf_products):
                product = self.shelf_products[product_index]
                slot.set_single_product(product)
                product_index += 1
        
        self._show_snackbar(f"Preenchidos {product_index} slots automaticamente", COLORS["success"])
        self.update()
    
    def _clear_all(self, e=None):
        """Limpa todos os slots."""
        self._save_state_for_undo()
        
        for slot in self.slots.values():
            slot.clear()  # Usa novo método que limpa products e overrides
        
        self._show_snackbar("Todos os slots foram limpos", COLORS["warning"])
        self.update()
    
    def _drop_product_on_slot(self, slot_id: str, product: Dict, add_to_kit: bool = False):
        """
        Processa drop de produto em slot.
        
        Args:
            slot_id: ID do slot alvo
            product: Dados do produto
            add_to_kit: Se True, adiciona ao Kit existente; se False, substitui
        """
        self._save_state_for_undo()
        
        slot = self.slots.get(slot_id)
        if slot:
            if add_to_kit and slot.products:
                # Modo Kit: adiciona produto ao slot existente
                slot.add_product(product)
                self._show_snackbar(f"Kit: {len(slot.products)} produtos no slot", COLORS["info"])
            else:
                # Modo padrão: substitui produto
                slot.set_single_product(product)
        
        self.update()
    
    def _open_override_modal(self, slot_id: str):
        """Abre modal de override para slot."""
        slot = self.slots.get(slot_id)
        if not slot or not slot.product_id:
            return
        
        # Campos do modal
        name_field = ft.TextField(
            label="Nome (Override)",
            value=slot.override_name or slot.product_name,
            hint_text="Deixe vazio para usar o original"
        )
        
        price_de_field = ft.TextField(
            label="Preco DE (Anterior)",
            value=str(slot.override_price_de) if slot.override_price_de else "",
            hint_text="Preco de referencia"
        )
        
        price_por_field = ft.TextField(
            label="Preco POR (Atual)",
            value=str(slot.override_price or slot.product_price),
            hint_text="Preco promocional"
        )
        
        def save_override(e):
            self._save_state_for_undo()
            
            slot.override_name = name_field.value if name_field.value != slot.product_name else None
            
            try:
                slot.override_price_de = float(price_de_field.value) if price_de_field.value else None
            except ValueError:
                slot.override_price_de = None
            
            try:
                price = float(price_por_field.value) if price_por_field.value else None
                if price and price != slot.product_price:
                    slot.override_price = price
            except ValueError:
                pass
            
            self._close_dialog()
            self.update()
        
        def clear_slot(e):
            self._save_state_for_undo()
            slot.clear()  # Usa novo método
            self._close_dialog()
            self.update()
        
        dialog = ft.AlertDialog(
            title=ft.Text(f"Editar Slot: {slot_id}"),
            content=ft.Container(
                content=ft.Column([
                    ft.Text(f"Produto: {slot.product_name}", weight=ft.FontWeight.BOLD),
                    ft.Divider(height=10),
                    name_field,
                    ft.Row([price_de_field, price_por_field]),
                ], spacing=15),
                width=400
            ),
            actions=[
                ft.TextButton("Limpar Slot", on_click=clear_slot),
                ft.TextButton("Cancelar", on_click=lambda e: self._close_dialog()),
                ft.ElevatedButton("Salvar", on_click=save_override, 
                                 style=ft.ButtonStyle(bgcolor=COLORS["info"]))
            ]
        )
        
        self.page.dialog = dialog
        dialog.open = True
        self.page.update()
    
    async def _save_project(self):
        """Salva projeto atual."""
        if not self.current_layout_id:
            return
        
        try:
            from src.core.repositories import ProjectRepository
            from src.core.database import AsyncSessionLocal
            
            # Monta estado dos slots (snapshot imutável)
            estado_slots = {}
            overrides = {}
            
            for slot_id, slot in self.slots.items():
                if slot.product_id:
                    estado_slots[slot_id] = {
                        "produto_id": slot.product_id,
                        "nome_snapshot": slot.product_name,
                        "preco_snapshot": slot.product_price,
                        "img_hash_snapshot": slot.product_image
                    }
                    
                    if slot.override_name or slot.override_price or slot.override_price_de:
                        overrides[slot_id] = {
                            "nome": slot.override_name,
                            "preco": slot.override_price,
                            "preco_de": slot.override_price_de
                        }
            
            async with AsyncSessionLocal() as session:
                repo = ProjectRepository(session)
                
                if self.current_project_id:
                    # Atualiza existente
                    await repo.update_project(
                        self.current_project_id,
                        estado_slots=estado_slots,
                        overrides_json=overrides
                    )
                else:
                    # Cria novo
                    project = await repo.create_project(
                        nome=f"Projeto {datetime.now().strftime('%d/%m %H:%M')}",
                        layout_id=self.current_layout_id,
                        estado_slots=estado_slots,
                        overrides_json=overrides
                    )
                    self.current_project_id = project.id
            
            self.is_dirty = False
            self._show_snackbar("Projeto salvo com sucesso!", COLORS["success"])
            
        except Exception as e:
            print(f"[Atelier] Erro ao salvar: {e}")
            self._show_snackbar(f"Erro ao salvar: {e}", COLORS["error"])
    
    def _show_snackbar(self, message: str, color: str):
        """Exibe snackbar."""
        self.page.snack_bar = ft.SnackBar(ft.Text(message), bgcolor=color)
        self.page.snack_bar.open = True
        self.page.update()
    
    def _toggle_xray(self, e):
        """
        Toggle X-Ray Mode (Vol. VI, Cap. 2.2).
        Mostra visualização de debug com zonas coloridas:
        - Verde: Área de imagem (#ALVO_IMAGEM)
        - Vermelho: Área de texto (#TXT_*)
        - Laranja: Área de preço (#TXT_PRECO_*)
        """
        self.xray_mode = not self.xray_mode
        
        if self.xray_mode:
            self._show_snackbar("X-Ray Mode ATIVO - Visualização Debug", COLORS["warning"])
        else:
            self._show_snackbar("X-Ray Mode DESATIVADO", COLORS["info"])
        
        self.update()
    
    def _build_slot(self, slot: SlotData) -> ft.Control:
        """Constrói slot com DragTarget para aceitar produtos arrastados."""
        is_filled = slot.product_id is not None
        display_name = slot.override_name or slot.product_name or "Arraste um produto"
        display_price = slot.override_price or slot.product_price
        
        def on_slot_hover(e):
            if e.data == "true":
                e.control.bgcolor = COLORS["slot_hover"]
                e.control.border = ft.border.all(2, ColorScheme.ACCENT_PRIMARY)
            else:
                e.control.bgcolor = COLORS["surface"]
                e.control.border = ft.border.all(1, ColorScheme.BORDER_DEFAULT)
            e.control.update()
        
        def on_accept_drop(e):
            """Callback quando produto é solto no slot."""
            product = e.src.data
            if product:
                self._drop_product_on_slot(slot.slot_id, product)
        
        def on_will_accept(e):
            """Feedback visual durante drag-over."""
            return True  # Sempre aceita
        
        # Container visual do slot
        slot_visual = ft.Container(
            content=ft.Column([
                ft.Text(slot.slot_id, size=Typography.LABEL_SIZE, color=ColorScheme.TEXT_MUTED),
                ft.Container(
                    content=ft.Icon(
                        ft.icons.INVENTORY_2 if is_filled else ft.icons.ADD,
                        color=ColorScheme.TEXT_PRIMARY if is_filled else ColorScheme.TEXT_MUTED,
                        size=28
                    ),
                    bgcolor=COLORS["slot_filled"] if is_filled else COLORS["slot_empty"],
                    border_radius=Spacing.RADIUS_MD,
                    padding=Spacing.LG,
                    expand=True,
                    alignment=ft.alignment.center
                ),
                ft.Text(
                    display_name[:18] + "..." if len(display_name) > 18 else display_name,
                    size=Typography.CAPTION_SIZE,
                    weight=ft.FontWeight.W_500 if is_filled else ft.FontWeight.NORMAL,
                    color=ColorScheme.TEXT_PRIMARY if is_filled else ColorScheme.TEXT_MUTED,
                    max_lines=1,
                    overflow=ft.TextOverflow.ELLIPSIS,
                ),
                ft.Text(
                    f"R$ {display_price:.2f}" if display_price else "",
                    size=Typography.BODY_SIZE,
                    weight=ft.FontWeight.BOLD,
                    color=ColorScheme.SUCCESS if is_filled else ColorScheme.TEXT_MUTED
                ) if is_filled else ft.Container()
            ], spacing=Spacing.XS, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            padding=Spacing.MD,
            border_radius=Spacing.RADIUS_LG,
            bgcolor=COLORS["surface"],
            border=ft.border.all(1, ColorScheme.BORDER_DEFAULT),
            on_hover=on_slot_hover,
            animate=ft.Animation(Animations.DURATION_FAST, Animations.CURVE_DEFAULT),
        )
        
        # GestureDetector para cliques
        gesture = ft.GestureDetector(
            content=slot_visual,
            on_tap=lambda e, s=slot: self._open_override_modal(s.slot_id) if is_filled else None,
            on_secondary_tap=lambda e, s=slot: self._show_slot_context_menu(s.slot_id, e)
        )
        
        # Envolver com DragTarget para aceitar drops
        return ft.DragTarget(
            group="products",
            content=gesture,
            on_accept=on_accept_drop,
            on_will_accept=on_will_accept,
        )
    

    def _on_slot_hover(self, e):
        """Efeito hover em slots."""
        e.control.bgcolor = COLORS["surface_elevated"] if e.data == "true" else COLORS["surface"]
        e.control.update()
    
    def _show_slot_context_menu(self, slot_id: str, e):
        """
        Exibe menu de contexto para o slot (Vol. VI, Cap. 4.4 - QoL).
        Disparado por clique com botão direito.
        
        Opções:
        - Editar: Abre modal de override
        - Duplicar: Copia para próximo slot vazio
        - Limpar: Remove produto do slot
        - Adicionar +18: Adiciona ícone de restrição de idade
        """
        slot = self.slots.get(slot_id)
        if not slot:
            return
        
        is_filled = bool(slot.products)
        
        def handle_edit(ev):
            self.page.close(context_menu)
            if is_filled:
                self._open_override_modal(slot_id)
        
        def handle_duplicate(ev):
            self.page.close(context_menu)
            if is_filled:
                self._duplicate_slot(slot_id)
        
        def handle_clear(ev):
            self.page.close(context_menu)
            if is_filled:
                self._save_state_for_undo()
                slot.clear()
                self._show_snackbar(f"Slot {slot_id} limpo", COLORS["warning"])
                self.update()
        
        def handle_add_18(ev):
            self.page.close(context_menu)
            if is_filled:
                self._add_age_restriction(slot_id)
        
        # Construir menu
        menu_items = []
        
        if is_filled:
            menu_items.extend([
                ft.ListTile(
                    leading=ft.Icon(ft.icons.EDIT, size=20),
                    title=ft.Text("Editar", size=14),
                    on_click=handle_edit
                ),
                ft.ListTile(
                    leading=ft.Icon(ft.icons.COPY, size=20),
                    title=ft.Text("Duplicar", size=14),
                    on_click=handle_duplicate
                ),
                ft.ListTile(
                    leading=ft.Icon(ft.icons.DELETE, size=20, color=COLORS["error"]),
                    title=ft.Text("Limpar", size=14, color=COLORS["error"]),
                    on_click=handle_clear
                ),
                ft.Divider(height=1),
                ft.ListTile(
                    leading=ft.Icon(ft.icons.NO_DRINKS, size=20, color=COLORS["warning"]),
                    title=ft.Text("Adicionar +18", size=14),
                    subtitle=ft.Text("Ícone de restrição de idade", size=10),
                    on_click=handle_add_18
                ),
            ])
        else:
            menu_items.append(
                ft.ListTile(
                    leading=ft.Icon(ft.icons.INFO_OUTLINE, size=20),
                    title=ft.Text("Slot vazio", size=14, color=ft.colors.GREY_500),
                    subtitle=ft.Text("Arraste um produto para cá", size=10)
                )
            )
        
        context_menu = ft.AlertDialog(
            modal=True,
            title=ft.Row([
                ft.Icon(ft.icons.SETTINGS, size=18),
                ft.Text(f"  {slot_id}", size=14, weight=ft.FontWeight.BOLD)
            ]),
            content=ft.Container(
                content=ft.Column(menu_items, spacing=0, tight=True),
                width=220
            ),
            actions=[
                ft.TextButton("Fechar", on_click=lambda ev: self.page.close(context_menu))
            ]
        )
        
        self.page.open(context_menu)
    
    def _duplicate_slot(self, source_slot_id: str):
        """Duplica conteúdo do slot para o próximo slot vazio."""
        source = self.slots.get(source_slot_id)
        if not source or not source.products:
            return
        
        # Encontra próximo slot vazio
        for slot_id in sorted(self.slots.keys()):
            if slot_id != source_slot_id and not self.slots[slot_id].products:
                self._save_state_for_undo()
                
                # Copia produtos
                target = self.slots[slot_id]
                for p in source.products:
                    target.products.append(ProductInSlot(
                        product_id=p.product_id,
                        product_name=p.product_name,
                        product_price=p.product_price,
                        product_image=p.product_image
                    ))
                
                # Copia overrides se existirem
                target.override_name = source.override_name
                target.override_price = source.override_price
                target.override_price_de = source.override_price_de
                
                self._show_snackbar(f"Duplicado de {source_slot_id} para {slot_id}", COLORS["success"])
                self.update()
                return
        
        self._show_snackbar("Nenhum slot vazio disponível", COLORS["warning"])
    
    def _add_age_restriction(self, slot_id: str):
        """Marca slot para exibir ícone +18 na renderização."""
        slot = self.slots.get(slot_id)
        if not slot:
            return
        
        # Flag de restrição é armazenada nos overrides
        if not hasattr(slot, 'has_age_restriction') or not slot.has_age_restriction:
            # Como SlotData é dataclass, precisamos usar um atributo existente
            # Vamos usar o campo override_name com prefixo especial
            if slot.override_name and "[+18]" in slot.override_name:
                self._show_snackbar("Slot já tem ícone +18", COLORS["warning"])
                return
            
            self._save_state_for_undo()
            
            # Adiciona marcador [+18] ao nome
            original_name = slot.override_name or slot.product_name or ""
            slot.override_name = f"[+18] {original_name}"
            
            self._show_snackbar(f"Ícone +18 adicionado ao {slot_id}", COLORS["success"])
            self.update()
        else:
            self._show_snackbar("Slot já tem ícone +18", COLORS["warning"])

    
    def _build_product_card(self, product: Dict) -> ft.Control:
        """Constrói card de produto ARRASTÁVEL para a estante."""
        quality_color = ColorScheme.get_quality_color(product.get("quality", 0))
        
        def on_hover(e):
            if e.data == "true":
                e.control.bgcolor = ColorScheme.BG_HOVER
                e.control.border = ft.border.all(1, ColorScheme.BORDER_HOVER)
            else:
                e.control.bgcolor = COLORS["surface"]
                e.control.border = ft.border.all(1, ColorScheme.BORDER_DEFAULT)
            e.control.update()
        
        card = ft.Container(
            content=ft.Row([
                ft.Container(
                    content=ft.Icon(ft.icons.IMAGE, color=ColorScheme.TEXT_PRIMARY, size=20),
                    bgcolor=quality_color,
                    border_radius=Spacing.RADIUS_SM,
                    width=48,
                    height=48,
                    alignment=ft.alignment.center
                ),
                ft.Column([
                    ft.Text(
                        product["name"][:25], 
                        size=Typography.BODY_SMALL_SIZE, 
                        weight=ft.FontWeight.W_500,
                        color=ColorScheme.TEXT_PRIMARY,
                        max_lines=1,
                        overflow=ft.TextOverflow.ELLIPSIS,
                    ),
                    ft.Text(
                        f"R$ {product['price']:.2f}", 
                        size=Typography.CAPTION_SIZE, 
                        color=ColorScheme.SUCCESS
                    )
                ], spacing=2, expand=True),
                ft.Icon(ft.icons.DRAG_INDICATOR, color=ColorScheme.TEXT_MUTED, size=16),
            ], spacing=Spacing.MD),
            padding=Spacing.MD,
            bgcolor=COLORS["surface"],
            border=ft.border.all(1, ColorScheme.BORDER_DEFAULT),
            border_radius=Spacing.RADIUS_MD,
            on_hover=on_hover,
            animate=ft.Animation(Animations.DURATION_FAST, Animations.CURVE_DEFAULT),
        )
        
        # Envolver com Draggable para permitir arrastar
        return ft.Draggable(
            group="products",
            content=card,
            content_feedback=ft.Container(
                content=ft.Row([
                    ft.Icon(ft.icons.INVENTORY_2, size=16, color=ColorScheme.TEXT_PRIMARY),
                    ft.Text(product["name"][:12] + "...", size=11, color=ColorScheme.TEXT_PRIMARY),
                ], spacing=Spacing.SM),
                bgcolor=ColorScheme.ACCENT_PRIMARY,
                padding=Spacing.MD,
                border_radius=Spacing.RADIUS_SM,
                shadow=ft.BoxShadow(blur_radius=10, color="#00000066"),
            ),
            data=product,
        )
    
    def _add_to_next_empty_slot(self, product: Dict):
        """Adiciona produto ao próximo slot vazio."""
        for slot_id in sorted(self.slots.keys()):
            if self.slots[slot_id].product_id is None:
                self._drop_product_on_slot(slot_id, product)
                self._show_snackbar(f"Adicionado em {slot_id}", COLORS["info"])
                return
        
        self._show_snackbar("Todos os slots estao ocupados", COLORS["warning"])
    
    def _show_import_menu(self, e):
        """Exibe menu de opções de importação."""
        
        def import_from_db(e):
            self.page.close(dialog)
            self.page.run_task(self._import_from_database)
        
        def import_from_excel(e):
            self.page.close(dialog)
            self.page.run_task(self._import_from_excel)
        
        dialog = ft.AlertDialog(
            title=ft.Text("Importar Dados"),
            content=ft.Column([
                ft.Text("Escolha a fonte de dados:", size=14),
                ft.Container(height=15),
                ft.ListTile(
                    leading=ft.Icon(ft.icons.STORAGE),
                    title=ft.Text("Do Banco de Dados"),
                    subtitle=ft.Text("Selecionar produtos cadastrados"),
                    on_click=import_from_db
                ),
                ft.ListTile(
                    leading=ft.Icon(ft.icons.TABLE_CHART),
                    title=ft.Text("De Planilha Excel/CSV"),
                    subtitle=ft.Text("Importar de arquivo externo"),
                    on_click=import_from_excel
                )
            ], spacing=5, tight=True),
            actions=[ft.TextButton("Cancelar", on_click=lambda e: self.page.close(dialog))]
        )
        self.page.open(dialog)
    
    async def _import_from_database(self):
        """Abre modal de seleção de produtos do banco."""
        from src.core.repositories import ProductRepository
        from src.core.database import AsyncSessionLocal
        
        try:
            async with AsyncSessionLocal() as session:
                repo = ProductRepository(session)
                products = await repo.get_all()
                
                # Criar lista de seleção
                product_list = [
                    {
                        "id": p.id,
                        "name": p.nome_sanitizado or p.sku_origem,
                        "price": float(p.preco_venda_atual) if p.preco_venda_atual else 0,
                        "price_de": float(p.preco_referencia) if p.preco_referencia else None,
                        "image": p.get_images()[0] if p.get_images() else None,
                        "selected": False
                    }
                    for p in products[:100]  # Limitar a 100 para performance
                ]
                
                selected_ids = []
                
                def toggle_selection(product_id: int):
                    if product_id in selected_ids:
                        selected_ids.remove(product_id)
                    else:
                        selected_ids.append(product_id)
                
                def confirm_selection(e):
                    self.page.close(dialog)
                    # Adicionar produtos selecionados à estante
                    for pid in selected_ids:
                        for p in product_list:
                            if p["id"] == pid:
                                self._add_to_next_empty_slot(p)
                    self._show_snackbar(f"{len(selected_ids)} produtos importados", COLORS["success"])
                    self.update()
                
                list_items = []
                for p in product_list:
                    list_items.append(
                        ft.ListTile(
                            leading=ft.Checkbox(
                                value=False,
                                on_change=lambda e, pid=p["id"]: toggle_selection(pid)
                            ),
                            title=ft.Text(p["name"], max_lines=1, overflow=ft.TextOverflow.ELLIPSIS),
                            subtitle=ft.Text(f"R$ {p['price']:.2f}"),
                        )
                    )
                
                dialog = ft.AlertDialog(
                    title=ft.Text("Selecionar Produtos"),
                    content=ft.Container(
                        content=ft.ListView(controls=list_items, height=400),
                        width=400
                    ),
                    actions=[
                        ft.TextButton("Cancelar", on_click=lambda e: self.page.close(dialog)),
                        ft.ElevatedButton("Importar", on_click=confirm_selection)
                    ]
                )
                self.page.open(dialog)
                
        except Exception as e:
            self._show_snackbar(f"Erro ao carregar produtos: {e}", COLORS["error"])
    
    async def _import_from_excel(self):
        """Importa dados de Excel/CSV com conciliação via O Juiz."""
        from src.ui.components.o_juiz_modal import OJuizModal, ConflictItem
        
        # Criar FilePicker
        file_picker = ft.FilePicker(
            on_result=lambda e: self.page.run_task(
                self._process_excel_file, e.files[0].path if e.files else None
            )
        )
        self.page.overlay.append(file_picker)
        self.page.update()
        
        # Abrir seletor de arquivo
        file_picker.pick_files(
            allowed_extensions=["xlsx", "xls", "csv"],
            dialog_title="Selecione a planilha de produtos"
        )
    
    async def _process_excel_file(self, file_path: str):
        """
        Processa arquivo Excel e abre O Juiz para conciliação.
        Passo 1-3 do Checklist v2 - Usa ImportService em vez de pandas direto.
        """
        if not file_path:
            return
        
        from pathlib import Path
        from src.ui.components.o_juiz_modal import OJuizModal, ConflictItem
        from src.core.repositories import ProductRepository
        from src.core.database import AsyncSessionLocal
        from src.core.services.import_service import ImportService
        
        try:
            # Usar ImportService para ler arquivo (roda em background thread)
            file_path_obj = Path(file_path)
            rows = await ImportService.read_file(file_path_obj)
            
            if not rows:
                self._show_snackbar("Arquivo vazio ou inválido", COLORS["error"])
                return
            
            # Detectar colunas (flexível)
            desc_col = None
            price_col = None
            
            # Pegar nomes das colunas da primeira linha
            first_row = rows[0] if rows else {}
            columns = list(first_row.keys())
            
            for col in columns:
                col_lower = col.lower()
                if any(k in col_lower for k in ["desc", "nome", "produto", "item"]):
                    desc_col = col
                elif any(k in col_lower for k in ["preco", "preço", "valor", "price"]):
                    price_col = col
            
            if not desc_col:
                self._show_snackbar("Coluna de descrição não encontrada", COLORS["error"])
                return
            
            # Buscar produtos existentes para correlação
            async with AsyncSessionLocal() as session:
                repo = ProductRepository(session)
                existing_products = await repo.get_all()
                
                existing_map = {
                    p.nome_sanitizado.lower() if p.nome_sanitizado else "": p
                    for p in existing_products
                }
            
            # Gerar itens de conflito para O Juiz
            from rapidfuzz import fuzz
            
            conflict_items = []
            for idx, row in enumerate(rows):
                raw_name = str(row.get(desc_col, "")).strip()
                raw_price_val = row.get(price_col, "0")
                try:
                    raw_price = float(str(raw_price_val).replace(",", ".").replace("R$", "").strip()) if raw_price_val else 0
                except ValueError:
                    raw_price = 0
                
                # Buscar melhor match
                best_match = None
                best_score = 0
                
                for key, product in existing_map.items():
                    if key:
                        score = fuzz.ratio(raw_name.lower(), key)
                        if score > best_score:
                            best_score = score
                            best_match = product
                
                # Determinar confiança
                if best_score >= 90:
                    confidence = "high"
                elif best_score >= 60:
                    confidence = "medium"
                else:
                    confidence = "low"
                
                # Constrói lista de candidatos usando API correta
                candidates = []
                if best_match:
                    from src.ui.components.o_juiz_modal import FuzzyMatchCandidate
                    candidates.append(FuzzyMatchCandidate(
                        id=best_match.id,
                        name=best_match.nome_sanitizado or "",
                        score=best_score,
                        source="database",
                        metadata={"price": float(best_match.preco_venda_atual) if best_match.preco_venda_atual else 0}
                    ))
                
                conflict_items.append(ConflictItem(
                    excel_row=idx + 1,  # +1 para linha humana (1-indexed)
                    excel_value=raw_name,
                    candidates=candidates
                ))
            
            if not conflict_items:
                self._show_snackbar("Nenhum item encontrado na planilha", COLORS["warning"])
                return
            
            # Callback quando O Juiz resolver todos os conflitos
            def on_resolution_complete(resolved_conflicts: List[ConflictItem]):
                """Processa resoluções do O Juiz."""
                added_count = 0
                for conflict in resolved_conflicts:
                    if conflict.resolved and conflict.selected_candidate_id:
                        # Buscar dados do produto aceito
                        for p in existing_products:
                            if p.id == conflict.selected_candidate_id:
                                product_dict = {
                                    "id": p.id,
                                    "name": p.nome_sanitizado or p.sku_origem,
                                    "price": float(p.preco_venda_atual) if p.preco_venda_atual else 0,
                                    "price_de": float(p.preco_referencia) if p.preco_referencia else None,
                                    "image": p.get_images()[0] if p.get_images() else None
                                }
                                self._add_to_next_empty_slot(product_dict)
                                added_count += 1
                                break
                    elif conflict.is_new_entry:
                        # TODO: Criar novo produto a partir do excel_value
                        pass
                
                self._show_snackbar(f"{added_count} produtos importados com sucesso", COLORS["success"])
                self.update()
            
            # Abrir modal O Juiz (API: conflicts, on_resolve, on_cancel)
            from src.ui.components.o_juiz_modal import show_juiz_modal
            show_juiz_modal(
                page=self.page,
                conflicts=conflict_items,
                on_resolve=on_resolution_complete
            )
            
        except ImportError:
            self._show_snackbar("Pandas não instalado. Execute: pip install pandas openpyxl", COLORS["error"])
        except Exception as e:
            self._show_snackbar(f"Erro ao processar arquivo: {e}", COLORS["error"])
    
    def build(self):
        if not self.is_initialized:
            # Tela de espera até seleção de layout
            return ft.Container(
                content=ft.Column([
                    ft.Icon(ft.icons.DESIGN_SERVICES, size=64, color=ft.colors.GREY_600),
                    ft.Text("A Mesa", size=24, weight=ft.FontWeight.BOLD),
                    ft.Text("Selecione um layout ou projeto para iniciar",
                           size=14, color=ft.colors.GREY_400),
                    ft.ElevatedButton(
                        "Selecionar",
                        icon=ft.icons.FOLDER_OPEN,
                        on_click=lambda e: self.page.run_task(self._show_project_selector)
                    )
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=15),
                alignment=ft.alignment.center,
                expand=True
            )
        
        # ===== TOOLBAR =====
        toolbar = ft.Container(
            content=ft.Row([
                ft.Text(f"Mesa: {self.layout_name}", size=18, weight=ft.FontWeight.BOLD),
                ft.Container(expand=True),
                ft.IconButton(ft.icons.UNDO, tooltip="Desfazer (Ctrl+Z)", on_click=self._undo),
                ft.IconButton(ft.icons.REDO, tooltip="Refazer (Ctrl+Shift+Z)", on_click=self._redo),
                ft.VerticalDivider(width=10),
                # X-Ray Mode Toggle (Vol. VI, Cap. 2.2)
                ft.Container(
                    content=ft.Row([
                        ft.Icon(
                            ft.icons.FILTER_B_AND_W, 
                            size=18, 
                            color=COLORS["warning"] if self.xray_mode else ft.colors.GREY_500
                        ),
                        ft.Text(
                            "X-Ray", 
                            size=12, 
                            color=COLORS["warning"] if self.xray_mode else ft.colors.GREY_400
                        )
                    ], spacing=4),
                    padding=ft.padding.symmetric(horizontal=10, vertical=6),
                    border_radius=6,
                    bgcolor=ft.colors.with_opacity(0.2, COLORS["warning"]) if self.xray_mode else None,
                    on_click=self._toggle_xray,
                    tooltip="Modo X-Ray: Visualizar zonas do template"
                ),
                ft.VerticalDivider(width=10),
                ft.ElevatedButton(
                    "Importar Dados",
                    icon=ft.icons.UPLOAD_FILE,
                    on_click=self._show_import_menu
                ),
                ft.ElevatedButton("Auto-Preencher", icon=ft.icons.AUTO_FIX_HIGH, on_click=self._auto_fill),
                ft.ElevatedButton("Limpar Tudo", icon=ft.icons.CLEAR_ALL, on_click=self._clear_all),
                ft.VerticalDivider(width=10),
                ft.ElevatedButton(
                    "Salvar Projeto",
                    icon=ft.icons.SAVE,
                    style=ft.ButtonStyle(bgcolor=COLORS["info"], color=ft.colors.WHITE),
                    on_click=lambda e: self.page.run_task(self._save_project)
                )
            ]),
            padding=ft.padding.symmetric(horizontal=20, vertical=10),
            bgcolor=COLORS["surface"]
        )
        
        # ===== CANVAS (Slots Grid) =====
        slots_grid = ft.GridView(
            controls=[self._build_slot(slot) for slot in self.slots.values()],
            runs_count=4,
            max_extent=180,
            child_aspect_ratio=0.85,
            spacing=15,
            run_spacing=15,
            expand=True,
            padding=20
        )
        
        canvas = ft.Container(
            content=slots_grid,
            ref=self.canvas_ref,
            bgcolor="#0D0D0D",
            border_radius=10,
            expand=2
        )
        
        # ===== ESTANTE (Sidebar de Produtos) =====
        shelf_header = ft.Container(
            content=ft.Column([
                ft.Text("Estante de Produtos", weight=ft.FontWeight.BOLD),
                ft.TextField(
                    ref=self.search_ref,
                    hint_text="Buscar produto...",
                    prefix_icon=ft.icons.SEARCH,
                    on_change=self._filter_products,
                    dense=True
                )
            ], spacing=10),
            padding=15
        )
        
        shelf_list = ft.ListView(
            ref=self.shelf_ref,
            controls=[self._build_product_card(p) for p in self.filtered_products],
            spacing=8,
            padding=15,
            expand=True
        )
        
        shelf = ft.Container(
            content=ft.Column([
                shelf_header,
                ft.Divider(height=1, color=ft.colors.GREY_800),
                shelf_list
            ], expand=True),
            bgcolor=COLORS["surface_elevated"],
            border_radius=10,
            expand=1
        )
        
        # ===== LAYOUT PRINCIPAL =====
        return ft.Container(
            content=ft.Column([
                toolbar,
                ft.Row([canvas, shelf], spacing=15, expand=True)
            ], expand=True),
            padding=20,
            expand=True
        )

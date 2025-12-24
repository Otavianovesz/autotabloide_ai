"""
AutoTabloide AI - Estoque View (Almoxarifado)
==============================================
Gestão de produtos conforme Vol. VI, Parte III.
Interface virtualiada para dezenas de milhares de itens.
"""

import flet as ft
import asyncio
from typing import List, Optional, Dict
from decimal import Decimal

# Design System
from src.ui.design_system import ColorScheme, Typography, Spacing, Animations

# Industrial Components
from src.core.event_bus import emit, EventType, subscribe, get_event_bus
from src.core.logging_config import get_logger
from src.ui.audio import play_success, play_error

logger = get_logger("EstoqueView")

# Cores usando Design System
COLORS = {
    "success": ColorScheme.SUCCESS,
    "warning": ColorScheme.WARNING,
    "error": ColorScheme.ERROR,
    "info": ColorScheme.ACCENT_PRIMARY,
    "neutral": ColorScheme.TEXT_MUTED,
    "surface": ColorScheme.BG_SECONDARY,
    "surface_elevated": ColorScheme.BG_ELEVATED,
    "quality_perfect": ColorScheme.QUALITY_PERFECT,
    "quality_attention": ColorScheme.QUALITY_ATTENTION,
    "quality_incomplete": ColorScheme.QUALITY_INCOMPLETE,
    "quality_critical": ColorScheme.QUALITY_CRITICAL,
}


class ProductRowWidget(ft.UserControl):
    """
    Componente de linha de produto com semáforo de qualidade.
    Conforme Vol. VI, Cap. 3.1.
    """
    
    def __init__(
        self, 
        product: dict,
        on_edit: callable = None,
        on_magic_wand: callable = None,
        on_image_click: callable = None
    ):
        super().__init__()
        self.product = product
        self.on_edit = on_edit
        self.on_magic_wand = on_magic_wand
        self.on_image_click = on_image_click

    def _get_quality_color(self, status: int) -> str:
        """Retorna cor baseada no status de qualidade."""
        colors = {
            0: COLORS["quality_critical"],
            1: COLORS["quality_incomplete"],
            2: COLORS["quality_attention"],
            3: COLORS["quality_perfect"]
        }
        return colors.get(status, COLORS["neutral"])

    def _get_quality_tooltip(self, status: int) -> str:
        """Retorna tooltip explicativo do status."""
        tooltips = {
            0: "Critico: Dados incompletos ou preco zero",
            1: "Sem foto associada",
            2: "Atencao: Imagem baixa resolucao ou preco antigo",
            3: "Perfeito: Dados completos e validados"
        }
        return tooltips.get(status, "Status desconhecido")

    def build(self):
        status = self.product.get("status_qualidade", 0)
        quality_color = self._get_quality_color(status)
        
        # Avatar com semáforo de qualidade
        avatar = ft.Stack(
            [
                # Imagem do produto (placeholder se não tiver)
                ft.Container(
                    content=ft.Icon(ft.icons.IMAGE, color=ft.colors.GREY_600, size=30),
                    width=50,
                    height=50,
                    bgcolor=ft.colors.GREY_900,
                    border_radius=5,
                    alignment=ft.alignment.center
                ),
                # Badge de qualidade
                ft.Container(
                    width=14,
                    height=14,
                    bgcolor=quality_color,
                    border_radius=7,
                    right=0,
                    top=0,
                    tooltip=self._get_quality_tooltip(status)
                )
            ],
            width=50,
            height=50
        )
        
        # SKU
        sku_text = ft.Text(
            self.product.get("sku_origem", "N/A"),
            size=12,
            color=ft.colors.GREY_400,
            width=100,
            font_family="Consolas"  # Monospace para alinhamento
        )
        
        # Nome (editável)
        nome_field = ft.TextField(
            value=self.product.get("nome_sanitizado", ""),
            border=ft.InputBorder.NONE,
            text_size=14,
            expand=True,
            read_only=True,
            on_focus=lambda e: self._enable_edit(e.control)
        )
        
        # Marca
        marca_text = ft.Text(
            self.product.get("marca_normalizada", "-"),
            size=12,
            color=ft.colors.GREY_400,
            width=100
        )
        
        # Preco (formatado em verde)
        preco = self.product.get("preco_venda_atual", 0)
        preco_text = ft.Text(
            f"R$ {float(preco):,.2f}".replace(",", "X").replace(".", ",").replace("X", "."),
            size=14,
            weight=ft.FontWeight.BOLD,
            color=COLORS["success"],
            width=100,
            text_align=ft.TextAlign.RIGHT
        )
        
        # Botão varinha mágica (IA)
        magic_btn = ft.IconButton(
            icon=ft.icons.AUTO_FIX_HIGH,
            icon_color=COLORS["info"],
            tooltip="Sanitizar com IA",
            on_click=lambda e: self.on_magic_wand(self.product) if self.on_magic_wand else None
        )
        
        return ft.Container(
            content=ft.Row(
                [
                    ft.GestureDetector(
                        content=avatar,
                        on_tap=lambda e: self.on_image_click(self.product) if self.on_image_click else None
                    ),
                    sku_text,
                    nome_field,
                    marca_text,
                    preco_text,
                    magic_btn
                ],
                spacing=15,
                vertical_alignment=ft.CrossAxisAlignment.CENTER
            ),
            height=60,
            padding=ft.padding.symmetric(horizontal=10, vertical=5),
            border=ft.border.only(bottom=ft.BorderSide(1, ft.colors.GREY_900)),
            on_hover=self._on_hover
        )

    def _enable_edit(self, control):
        """Habilita edição do campo."""
        control.read_only = False
        control.border = ft.InputBorder.OUTLINE
        control.update()

    def _on_hover(self, e):
        """Efeito hover na linha."""
        if e.data == "true":
            e.control.bgcolor = ft.colors.with_opacity(0.05, ft.colors.WHITE)
        else:
            e.control.bgcolor = None
        e.control.update()


class EstoqueView(ft.UserControl):
    """
    Tela de gestão de estoque/produtos.
    Implementa ListView virtualizada para performance.
    """
    
    def __init__(self, page: ft.Page):
        super().__init__()
        self.page = page
        self.products: List[dict] = []
        self.filtered_products: List[dict] = []
        self.search_query: str = ""
        self.current_status_filter: Optional[int] = None
        
        # Paginação
        self.page_size = 50
        self.current_offset = 0
        self.total_count = 0

    def did_mount(self):
        """Carrega dados iniciais."""
        self.page.run_task(self._load_products)

    async def _load_products(self):
        """Carrega produtos do banco de forma assíncrona."""
        try:
            from src.core.database import AsyncSessionLocal
            from src.core.repositories import ProductRepository
            
            async with AsyncSessionLocal() as session:
                repo = ProductRepository(session)
                
                # Conta total
                self.total_count = await repo.count()
                
                # Busca paginada
                products = await repo.search(
                    query=self.search_query or None,
                    status=self.current_status_filter,
                    limit=self.page_size,
                    offset=self.current_offset
                )
                
                # Converte para dict
                self.products = [
                    {
                        "id": p.id,
                        "sku_origem": p.sku_origem,
                        "nome_sanitizado": p.nome_sanitizado,
                        "marca_normalizada": p.marca_normalizada,
                        "detalhe_peso": p.detalhe_peso,
                        "preco_venda_atual": p.preco_venda_atual,
                        "preco_referencia": p.preco_referencia,
                        "status_qualidade": p.status_qualidade,
                        "categoria": p.categoria,
                        "images": p.get_images()
                    }
                    for p in products
                ]
                
                self._update_list()
                
        except Exception as e:
            logger.error(f"Erro ao carregar produtos: {e}")
            self.products = []
            self._update_list()

    def _update_list(self):
        """Atualiza a lista visual."""
        if hasattr(self, 'product_list'):
            self.product_list.controls.clear()
            
            for product in self.products:
                row = ProductRowWidget(
                    product=product,
                    on_magic_wand=self._on_magic_wand,
                    on_image_click=self._on_image_click
                )
                self.product_list.controls.append(row)
            
            self.product_list.update()
            
            # Atualiza contador
            if hasattr(self, 'count_text'):
                self.count_text.value = f"{len(self.products)} de {self.total_count} produtos"
                self.count_text.update()

    def _on_search(self, e):
        """Handler de busca."""
        self.search_query = e.control.value
        self.current_offset = 0
        self.page.run_task(self._load_products)

    def _on_filter_change(self, e):
        """Handler de mudança de filtro de status."""
        value = e.control.value
        if value == "todos":
            self.current_status_filter = None
        else:
            self.current_status_filter = int(value)
        self.current_offset = 0
        self.page.run_task(self._load_products)

    def _on_magic_wand(self, product: dict):
        """Aciona sanitização via IA."""
        logger.info(f"Magic Wand acionado para produto ID={product.get('id')}")
        
        # Emite evento para o sistema
        emit(EventType.AI_TASK_START, product_id=product['id'], action='sanitize')
        
        self.page.snack_bar = ft.SnackBar(
            ft.Text(f"Sanitizando: {product['nome_sanitizado'][:30]}..."),
            bgcolor=COLORS["info"]
        )
        self.page.snack_bar.open = True
        self.page.update()

    def _on_image_click(self, product: dict):
        """Abre modal do Image Doctor."""
        self._show_image_doctor(product)

    def _show_image_doctor(self, product: dict):
        """Modal do Image Doctor (Vol. VI, Cap. 3.3)."""
        from pathlib import Path
        
        # Estado do modal
        current_image_path = None
        processed_image_path = None
        
        # Referência para atualizar preview
        preview_container = ft.Ref[ft.Container]()
        status_text = ft.Ref[ft.Text]()
        
        def close_modal(e):
            modal.open = False
            self.page.update()
        
        def update_status(msg: str, color: str = ft.colors.GREY_400):
            if status_text.current:
                status_text.current.value = msg
                status_text.current.color = color
                status_text.current.update()
        
        async def handle_remove_background(e):
            """Remove fundo usando rembg."""
            nonlocal processed_image_path
            
            if not current_image_path:
                update_status("Selecione uma imagem primeiro", COLORS["error"])
                return
            
            update_status("Removendo fundo...", COLORS["info"])
            
            try:
                from src.rendering.image_pipeline import ImagePipeline
                system_root = Path(__file__).parent.parent.parent.parent / "AutoTabloide_System_Root"
                pipeline = ImagePipeline(str(system_root))
                
                processed_image_path = await asyncio.to_thread(
                    pipeline.remove_background, current_image_path
                )
                
                update_status("Fundo removido com sucesso!", COLORS["success"])
                play_success()
                
            except ImportError:
                update_status("Instale rembg: pip install rembg", COLORS["error"])
            except Exception as ex:
                update_status(f"Erro: {ex}", COLORS["error"])
        
        async def handle_upscale(e):
            """Aumenta resolução usando Real-ESRGAN."""
            nonlocal processed_image_path
            
            source = processed_image_path or current_image_path
            if not source:
                update_status("Selecione uma imagem primeiro", COLORS["error"])
                return
            
            update_status("Ampliando 4x (pode demorar)...", COLORS["info"])
            
            try:
                from src.rendering.image_pipeline import ImagePipeline
                system_root = Path(__file__).parent.parent.parent.parent / "AutoTabloide_System_Root"
                pipeline = ImagePipeline(str(system_root))
                
                processed_image_path = await asyncio.to_thread(
                    pipeline.upscale, source, 4
                )
                
                update_status("Resolução aumentada 4x!", COLORS["success"])
                play_success()
                
            except Exception as ex:
                update_status(f"Erro no upscale: {ex}", COLORS["error"])
        
        async def handle_save(e):
            """Salva imagem processada no vault."""
            source = processed_image_path or current_image_path
            if not source:
                update_status("Nenhuma imagem para salvar", COLORS["error"])
                return
            
            update_status("Salvando no vault...", COLORS["info"])
            
            try:
                from src.rendering.image_pipeline import ImagePipeline
                from src.core.repositories import ProductRepository
                from src.core.database import AsyncSessionLocal
                
                system_root = Path(__file__).parent.parent.parent.parent / "AutoTabloide_System_Root"
                pipeline = ImagePipeline(str(system_root))
                
                # Armazena no vault
                img_hash = await asyncio.to_thread(pipeline.store_in_vault, source)
                
                # Gera thumbnail
                await asyncio.to_thread(pipeline.generate_thumbnail, source)
                
                # Atualiza produto no banco
                async with AsyncSessionLocal() as session:
                    repo = ProductRepository(session)
                    await repo.add_image_to_product(product['id'], img_hash)
                
                update_status(f"Salvo! Hash: {img_hash[:8]}...", COLORS["success"])
                play_success()
                
                # Emite evento de atualização
                emit(EventType.PRODUCT_UPDATED, product_id=product['id'])
                
                # Fecha modal após breve delay
                await asyncio.sleep(1.5)
                close_modal(None)
                
                # Recarrega lista
                self.page.run_task(self._load_products)
                
            except Exception as ex:
                update_status(f"Erro ao salvar: {ex}", COLORS["error"])
        
        # Conteúdo do modal
        content = ft.Column(
            [
                ft.Text(f"Produto: {product['nome_sanitizado']}", size=18, weight=ft.FontWeight.BOLD),
                ft.Divider(),
                ft.Tabs(
                    tabs=[
                        ft.Tab(
                            text="Busca Web",
                            icon=ft.icons.SEARCH,
                            content=ft.Container(
                                content=ft.Column(
                                    [
                                        ft.TextField(
                                            label="Termo de busca",
                                            value=product['nome_sanitizado'],
                                            expand=True
                                        ),
                                        ft.ElevatedButton(
                                            "Buscar Imagem",
                                            icon=ft.icons.IMAGE_SEARCH,
                                            on_click=lambda e: update_status("Busca enfileirada para o Sentinel...", COLORS["info"])
                                        ),
                                        ft.Container(
                                            content=ft.Text("Resultados aparecerao aqui..."),
                                            height=200,
                                            bgcolor=ft.colors.GREY_900,
                                            border_radius=10,
                                            alignment=ft.alignment.center
                                        )
                                    ],
                                    spacing=15
                                ),
                                padding=20
                            )
                        ),
                        ft.Tab(
                            text="Upload Local",
                            icon=ft.icons.UPLOAD_FILE,
                            content=ft.Container(
                                content=ft.Column(
                                    [
                                        ft.Container(
                                            ref=preview_container,
                                            content=ft.Column(
                                                [
                                                    ft.Icon(ft.icons.CLOUD_UPLOAD, size=50, color=ft.colors.GREY_500),
                                                    ft.Text("Arraste uma imagem ou clique para selecionar")
                                                ],
                                                horizontal_alignment=ft.CrossAxisAlignment.CENTER
                                            ),
                                            height=200,
                                            bgcolor=ft.colors.GREY_900,
                                            border=ft.border.all(2, ft.colors.GREY_700),
                                            border_radius=10,
                                            alignment=ft.alignment.center
                                        )
                                    ]
                                ),
                                padding=20
                            )
                        ),
                    ],
                    expand=True
                ),
                ft.Divider(),
                ft.Text(ref=status_text, value="Selecione ou busque uma imagem", size=12, color=ft.colors.GREY_400),
                ft.Row(
                    [
                        ft.OutlinedButton(
                            "Remover Fundo", 
                            icon=ft.icons.AUTO_FIX_HIGH,
                            on_click=lambda e: self.page.run_task(handle_remove_background, e)
                        ),
                        ft.OutlinedButton(
                            "Upscale 4x", 
                            icon=ft.icons.ZOOM_IN,
                            on_click=lambda e: self.page.run_task(handle_upscale, e)
                        ),
                        ft.Container(expand=True),
                        ft.ElevatedButton(
                            "Salvar",
                            icon=ft.icons.SAVE,
                            style=ft.ButtonStyle(bgcolor=COLORS["success"]),
                            on_click=lambda e: self.page.run_task(handle_save, e)
                        )
                    ]
                )
            ],
            spacing=10,
            height=500
        )
        
        modal = ft.AlertDialog(
            title=ft.Text("Image Doctor"),
            content=content,
            actions=[ft.TextButton("Fechar", on_click=close_modal)],
            actions_alignment=ft.MainAxisAlignment.END
        )
        
        self.page.dialog = modal
        modal.open = True
        self.page.update()


    def _on_import_click(self, e):
        """Abre diálogo de importação."""
        self.page.snack_bar = ft.SnackBar(
            ft.Text("Importacao em desenvolvimento..."),
            bgcolor=COLORS["warning"]
        )
        self.page.snack_bar.open = True
        self.page.update()

    def build(self):
        # Barra de ferramentas
        toolbar = ft.Container(
            content=ft.Row(
                [
                    ft.TextField(
                        hint_text="Buscar produto...",
                        prefix_icon=ft.icons.SEARCH,
                        on_change=self._on_search,
                        expand=True,
                        border_radius=8
                    ),
                    ft.Dropdown(
                        label="Status",
                        value="todos",
                        options=[
                            ft.dropdown.Option("todos", "Todos"),
                            ft.dropdown.Option("0", "Critico"),
                            ft.dropdown.Option("1", "Sem Foto"),
                            ft.dropdown.Option("2", "Atencao"),
                            ft.dropdown.Option("3", "Perfeito"),
                        ],
                        width=150,
                        on_change=self._on_filter_change
                    ),
                    ft.ElevatedButton(
                        "Importar",
                        icon=ft.icons.UPLOAD_FILE,
                        on_click=self._on_import_click
                    )
                ],
                spacing=15
            ),
            padding=15,
            bgcolor=COLORS["surface_elevated"],
            border_radius=10
        )
        
        # Header da lista
        list_header = ft.Container(
            content=ft.Row(
                [
                    ft.Text("", width=50),  # Avatar
                    ft.Text("SKU", width=100, weight=ft.FontWeight.BOLD, size=12),
                    ft.Text("Descricao", expand=True, weight=ft.FontWeight.BOLD, size=12),
                    ft.Text("Marca", width=100, weight=ft.FontWeight.BOLD, size=12),
                    ft.Text("Preco", width=100, weight=ft.FontWeight.BOLD, size=12, text_align=ft.TextAlign.RIGHT),
                    ft.Text("", width=40)  # Ações
                ],
                spacing=15
            ),
            padding=ft.padding.symmetric(horizontal=10, vertical=8),
            border=ft.border.only(bottom=ft.BorderSide(1, ft.colors.GREY_700))
        )
        
        # Lista virtualizada
        self.product_list = ft.ListView(
            expand=True,
            spacing=0,
            padding=0,
            auto_scroll=False
        )
        
        # Rodapé com contagem
        self.count_text = ft.Text("Carregando...", size=12, color=ft.colors.GREY_400)
        footer = ft.Container(
            content=ft.Row(
                [
                    self.count_text,
                    ft.Container(expand=True),
                    ft.IconButton(icon=ft.icons.CHEVRON_LEFT, on_click=self._prev_page),
                    ft.IconButton(icon=ft.icons.CHEVRON_RIGHT, on_click=self._next_page)
                ]
            ),
            padding=10
        )
        
        return ft.Container(
            content=ft.Column(
                [
                    toolbar,
                    ft.Container(height=10),
                    list_header,
                    self.product_list,
                    footer
                ],
                expand=True
            ),
            padding=20,
            expand=True
        )

    def _prev_page(self, e):
        """Página anterior."""
        if self.current_offset > 0:
            self.current_offset = max(0, self.current_offset - self.page_size)
            self.page.run_task(self._load_products)

    def _next_page(self, e):
        """Próxima página."""
        if self.current_offset + self.page_size < self.total_count:
            self.current_offset += self.page_size
            self.page.run_task(self._load_products)

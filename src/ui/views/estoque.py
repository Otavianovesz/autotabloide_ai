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

# Cores Semânticas
COLORS = {
    "success": "#34C759",
    "warning": "#FFCC00",
    "error": "#FF3B30",
    "info": "#007AFF",
    "neutral": "#8E8E93",
    "surface": "#1C1C1E",
    "surface_elevated": "#2C2C2E",
    "quality_perfect": "#34C759",
    "quality_attention": "#FFCC00",
    "quality_incomplete": "#FF9500",
    "quality_critical": "#FF3B30",
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
            print(f"[Estoque] Erro ao carregar produtos: {e}")
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
        self.page.snack_bar = ft.SnackBar(
            ft.Text(f"Sanitizando: {product['nome_sanitizado'][:30]}..."),
            bgcolor=COLORS["info"]
        )
        self.page.snack_bar.open = True
        self.page.update()
        
        # Aqui enviaria para o Sentinel process
        # sentinel_queue.put({"type": "SANITIZE", "id": product["id"], "raw_text": product["nome_sanitizado"]})

    def _on_image_click(self, product: dict):
        """Abre modal do Image Doctor."""
        self._show_image_doctor(product)

    def _show_image_doctor(self, product: dict):
        """Modal do Image Doctor (Vol. VI, Cap. 3.3)."""
        
        def close_modal(e):
            modal.open = False
            self.page.update()
        
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
                                            on_click=lambda e: print("Hunter search...")
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
                ft.Row(
                    [
                        ft.OutlinedButton("Remover Fundo", icon=ft.icons.AUTO_FIX_HIGH),
                        ft.OutlinedButton("Upscale 4x", icon=ft.icons.ZOOM_IN),
                        ft.Container(expand=True),
                        ft.ElevatedButton(
                            "Salvar",
                            icon=ft.icons.SAVE,
                            style=ft.ButtonStyle(bgcolor=COLORS["success"])
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

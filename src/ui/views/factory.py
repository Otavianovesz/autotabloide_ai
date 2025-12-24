"""
AutoTabloide AI - Factory View (Fábrica de Cartazes)
=====================================================
Produção em lote de cartazes data-driven conforme Vol. VI, Cap. 5.
Gera PDF multipáginas a partir de lista de produtos.
"""

import flet as ft
import asyncio
from datetime import datetime
from typing import Optional, List, Dict, Any
from pathlib import Path

# Design System
from src.ui.design_system import ColorScheme, Typography, Spacing, Animations

# Cores usando Design System
COLORS = {
    "success": ColorScheme.SUCCESS,
    "warning": ColorScheme.WARNING,
    "error": ColorScheme.ERROR,
    "info": ColorScheme.ACCENT_PRIMARY,
    "neutral": ColorScheme.TEXT_MUTED,
    "surface": ColorScheme.BG_SECONDARY,
    "surface_elevated": ColorScheme.BG_ELEVATED,
}


class FactoryView(ft.UserControl):
    """
    Fábrica de Cartazes - Produção Data-Driven.
    
    Workflow:
    1. Seleciona layout de cartaz (CARTAZ_A4, CARTAZ_GIGANTE, ETIQUETA)
    2. Importa lista de produtos (DB ou Excel)
    3. Preview dinâmico ao clicar em item
    4. Exporta PDF multipáginas (1 produto = 1 página)
    """
    
    ALLOWED_TYPES = ["CARTAZ_A4", "CARTAZ_GIGANTE", "ETIQUETA"]
    
    def __init__(self, page: ft.Page):
        super().__init__()
        self.page = page
        
        # Estado
        self.selected_layout: Optional[Dict] = None
        self.product_list: List[Dict] = []
        self.selected_product: Optional[Dict] = None
        self.is_rendering: bool = False
        self.render_progress: float = 0.0
        
        # Configurações de exportação
        self.export_dpi: int = 300
        self.color_mode: str = "auto"  # auto, rgb, cmyk
    
    def did_mount(self):
        """Carrega layouts disponíveis."""
        self.page.run_task(self._load_layouts)
    
    async def _load_layouts(self):
        """Carrega layouts do tipo CARTAZ."""
        try:
            from src.core.repositories import LayoutRepository
            from src.core.database import AsyncSessionLocal
            
            async with AsyncSessionLocal() as session:
                repo = LayoutRepository(session)
                layouts = await repo.get_all()
                
                self.available_layouts = [
                    {
                        "id": l.id,
                        "name": l.nome_amigavel,
                        "type": l.tipo_midia.value if l.tipo_midia else "CARTAZ_A4",
                        "file": l.arquivo_fonte
                    }
                    for l in layouts
                    if l.tipo_midia and l.tipo_midia.value in self.ALLOWED_TYPES
                ]
                
                self.update()
                
        except Exception as e:
            print(f"[Factory] Erro ao carregar layouts: {e}")
            self.available_layouts = []
    
    def _on_layout_selected(self, e):
        """Callback ao selecionar layout."""
        layout_id = int(e.control.value)
        self.selected_layout = next(
            (l for l in self.available_layouts if l["id"] == layout_id),
            None
        )
        self.update()
    
    async def _import_from_db(self):
        """Importa produtos do banco de dados."""
        try:
            from src.core.repositories import ProductRepository
            from src.core.database import AsyncSessionLocal
            
            async with AsyncSessionLocal() as session:
                repo = ProductRepository(session)
                products = await repo.get_all()
                
                self.product_list = [
                    {
                        "id": p.id,
                        "name": p.nome_sanitizado or p.sku_origem,
                        "price_de": float(p.preco_referencia) if p.preco_referencia else None,
                        "price_por": float(p.preco_venda_atual) if p.preco_venda_atual else 0,
                        "weight": p.detalhe_peso,
                        "image": p.get_images()[0] if p.get_images() else None
                    }
                    for p in products
                ]
                
                self._show_snackbar(f"{len(self.product_list)} produtos importados", COLORS["success"])
                self.update()
                
        except Exception as e:
            print(f"[Factory] Erro ao importar: {e}")
            self._show_snackbar(f"Erro ao importar: {e}", COLORS["error"])
    
    def _import_from_file(self, e):
        """
        Abre diálogo para importar Excel/CSV.
        Conforme Vol. VI, Cap. 5.2: Valida colunas obrigatórias.
        """
        file_picker = ft.FilePicker(
            on_result=lambda ev: self.page.run_task(
                self._process_import_file, ev.files[0].path if ev.files else None
            )
        )
        self.page.overlay.append(file_picker)
        self.page.update()
        
        file_picker.pick_files(
            allowed_extensions=["xlsx", "xls", "csv"],
            dialog_title="Selecione a planilha de produtos"
        )
    
    async def _process_import_file(self, file_path: str):
        """
        Processa arquivo importado com validação de colunas.
        Conforme Vol. VI, Cap. 5.2: Colunas obrigatórias para PROCON.
        """
        if not file_path:
            return
        
        try:
            import pandas as pd
            
            # Lê arquivo
            if file_path.endswith(".csv"):
                df = pd.read_csv(file_path)
            else:
                df = pd.read_excel(file_path)
            
            # === VALIDAÇÃO DE COLUNAS OBRIGATÓRIAS (Vol. VI, Cap. 5.2) ===
            required_columns = {
                "descricao": ["desc", "descricao", "descrição", "nome", "produto", "item"],
                "preco_de": ["preco_de", "preço_de", "de", "anterior", "referencia"],
                "preco_por": ["preco_por", "preço_por", "por", "atual", "venda", "oferta", "preco", "preço"]
            }
            
            found_columns = {}
            missing_required = []
            
            for key, variants in required_columns.items():
                for col in df.columns:
                    col_lower = col.lower().strip()
                    if any(v in col_lower for v in variants):
                        found_columns[key] = col
                        break
                
                if key not in found_columns:
                    if key != "preco_de":  # Preço De é opcional
                        missing_required.append(key)
            
            # Verifica obrigatórios
            if not found_columns.get("descricao"):
                self._show_snackbar("ERRO: Coluna 'Descrição' não encontrada", COLORS["error"])
                return
            
            if not found_columns.get("preco_por"):
                self._show_snackbar("ERRO: Coluna 'Preço Por' obrigatória", COLORS["error"])
                return
            
            # Extrai dados
            products = []
            col_desc = found_columns.get("descricao")
            col_de = found_columns.get("preco_de")
            col_por = found_columns.get("preco_por")
            
            # Detecta coluna de peso (opcional)
            col_peso = None
            for col in df.columns:
                if any(k in col.lower() for k in ["peso", "gramatura", "unidade", "weight"]):
                    col_peso = col
                    break
            
            for idx, row in df.iterrows():
                try:
                    price_por = float(row[col_por]) if pd.notna(row[col_por]) else 0.0
                    price_de = float(row[col_de]) if col_de and pd.notna(row[col_de]) else None
                    
                    products.append({
                        "id": idx + 1,
                        "name": str(row[col_desc]) if pd.notna(row[col_desc]) else f"Produto {idx+1}",
                        "price_de": price_de,
                        "price_por": price_por,
                        "weight": str(row[col_peso]) if col_peso and pd.notna(row[col_peso]) else None,
                        "image": None
                    })
                except Exception as ex:
                    print(f"[Factory] Erro na linha {idx}: {ex}")
            
            if not products:
                self._show_snackbar("Nenhum produto válido encontrado", COLORS["warning"])
                return
            
            self.product_list = products
            
            # Feedback detalhado
            msg = f"{len(products)} produtos importados"
            if not col_de:
                msg += " (sem Preço De)"
            self._show_snackbar(msg, COLORS["success"])
            self.update()
            
        except ImportError:
            self._show_snackbar("Instale pandas: pip install pandas openpyxl", COLORS["error"])
        except Exception as e:
            print(f"[Factory] Erro ao processar arquivo: {e}")
            self._show_snackbar(f"Erro: {e}", COLORS["error"])
    
    def _on_product_selected(self, product: Dict):
        """Seleciona produto para preview."""
        self.selected_product = product
        self.update()
    
    def _remove_product(self, product: Dict):
        """Remove produto da lista."""
        self.product_list = [p for p in self.product_list if p["id"] != product["id"]]
        if self.selected_product and self.selected_product["id"] == product["id"]:
            self.selected_product = None
        self.update()
    
    def _clear_list(self, e=None):
        """Limpa lista de produtos."""
        self.product_list = []
        self.selected_product = None
        self.update()
    
    async def _export_pdf(self):
        """Exporta PDF multipáginas com todos os produtos."""
        if not self.selected_layout or not self.product_list:
            self._show_snackbar("Selecione layout e importe produtos primeiro", COLORS["warning"])
            return
        
        self.is_rendering = True
        self.render_progress = 0.0
        self.update()
        
        try:
            from src.rendering.vector import VectorEngine
            from src.rendering.output import OutputEngine
            
            # Inicializa engines
            system_root = Path(__file__).parent.parent.parent.parent / "AutoTabloide_System_Root"
            svg_path = system_root / "library" / "svg_source" / self.selected_layout["file"]
            
            if not svg_path.exists():
                self._show_snackbar(f"Template não encontrado: {svg_path.name}", COLORS["error"])
                return
            
            # VectorEngine: Instancia primeiro, depois carrega template
            vector_engine = VectorEngine(strict_fonts=False)  # Flexível para produção
            vector_engine.load_template(str(svg_path))
            
            # OutputEngine: Requer system_root
            output_engine = OutputEngine(str(system_root))
            
            # Lista de frames renderizados
            frames = []
            total = len(self.product_list)
            
            for i, product in enumerate(self.product_list):
                # Atualiza progresso
                self.render_progress = (i + 1) / total
                self.update()
                
                # Prepara dados para o slot único
                slot_data = {
                    "SLOT_01": {
                        "TXT_NOME_PRODUTO": product["name"],
                        "TXT_PRECO_DE": f"R$ {product['price_de']:.2f}" if product["price_de"] else None,
                        "TXT_PRECO_INT": str(int(product["price_por"])),
                        "TXT_PRECO_DEC": f"{int((product['price_por'] % 1) * 100):02d}",
                        "TXT_UNIDADE": product.get("weight", ""),
                        "ALVO_IMAGEM": product.get("image")
                    }
                }
                
                # Renderiza frame
                frame_svg = vector_engine.render_frame(slot_data)
                frames.append(frame_svg)
                
                # Pequena pausa para UI atualizar
                await asyncio.sleep(0.01)
            
            # Gera PDF multipáginas
            output_path = system_root / "output" / f"cartazes_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            await output_engine.batch_render_to_pdf(
                frames=frames,
                output_path=str(output_path),
                dpi=self.export_dpi,
                color_mode=self.color_mode
            )
            
            self._show_snackbar(f"PDF gerado: {output_path.name}", COLORS["success"])
            
        except Exception as e:
            print(f"[Factory] Erro ao exportar: {e}")
            self._show_snackbar(f"Erro na exportacao: {e}", COLORS["error"])
        
        finally:
            self.is_rendering = False
            self.render_progress = 0.0
            self.update()
    
    def _show_snackbar(self, message: str, color: str):
        """Exibe notificação."""
        self.page.snack_bar = ft.SnackBar(ft.Text(message), bgcolor=color)
        self.page.snack_bar.open = True
        self.page.update()
    
    def _build_product_row(self, product: Dict) -> ft.Container:
        """Constrói linha de produto na lista."""
        is_selected = self.selected_product and self.selected_product["id"] == product["id"]
        
        # Validação: precisa ter preço De e Por
        has_price_de = product.get("price_de") is not None
        has_price_por = product.get("price_por", 0) > 0
        is_valid = has_price_de and has_price_por
        
        status_color = COLORS["success"] if is_valid else COLORS["warning"]
        status_icon = ft.icons.CHECK_CIRCLE if is_valid else ft.icons.WARNING
        
        return ft.Container(
            content=ft.Row([
                ft.Icon(status_icon, color=status_color, size=16),
                ft.Column([
                    ft.Text(product["name"], size=12, weight=ft.FontWeight.W_500,
                           max_lines=1, overflow=ft.TextOverflow.ELLIPSIS),
                    ft.Row([
                        ft.Text(f"De: R$ {product['price_de']:.2f}" if has_price_de else "De: N/A",
                               size=10, color=ft.colors.GREY_400),
                        ft.Text(f"Por: R$ {product['price_por']:.2f}",
                               size=10, color=COLORS["success"], weight=ft.FontWeight.BOLD)
                    ], spacing=10)
                ], expand=True, spacing=2),
                ft.IconButton(
                    ft.icons.DELETE_OUTLINE,
                    icon_size=18,
                    icon_color=COLORS["error"],
                    tooltip="Remover",
                    on_click=lambda e, p=product: self._remove_product(p)
                )
            ]),
            padding=10,
            bgcolor=COLORS["slot_filled"] if is_selected else COLORS["surface"],
            border_radius=6,
            on_click=lambda e, p=product: self._on_product_selected(p),
            on_hover=lambda e: self._on_row_hover(e)
        )
    
    def _on_row_hover(self, e):
        """Efeito hover."""
        if e.data == "true":
            e.control.bgcolor = COLORS["surface_elevated"]
        else:
            e.control.bgcolor = COLORS["surface"]
        e.control.update()
    
    def _build_preview_panel(self) -> ft.Container:
        """Constrói painel de preview."""
        if not self.selected_product:
            return ft.Container(
                content=ft.Column([
                    ft.Icon(ft.icons.PREVIEW, size=48, color=ft.colors.GREY_600),
                    ft.Text("Selecione um produto para visualizar", color=ft.colors.GREY_400)
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                   alignment=ft.MainAxisAlignment.CENTER),
                expand=True,
                alignment=ft.alignment.center
            )
        
        product = self.selected_product
        
        # Simula preview do cartaz
        return ft.Container(
            content=ft.Column([
                ft.Text("Preview do Cartaz", size=14, color=ft.colors.GREY_400),
                ft.Container(
                    content=ft.Column([
                        # Área da imagem
                        ft.Container(
                            content=ft.Icon(ft.icons.IMAGE, size=64, color=ft.colors.WHITE54),
                            bgcolor="#2A2A2A",
                            height=150,
                            border_radius=8,
                            alignment=ft.alignment.center
                        ),
                        # Nome do produto
                        ft.Text(
                            product["name"],
                            size=16,
                            weight=ft.FontWeight.BOLD,
                            text_align=ft.TextAlign.CENTER,
                            max_lines=2
                        ),
                        # Peso/Unidade
                        ft.Text(
                            product.get("weight", ""),
                            size=12,
                            color=ft.colors.GREY_400,
                            text_align=ft.TextAlign.CENTER
                        ),
                        # Preço De (riscado)
                        ft.Text(
                            f"De: R$ {product['price_de']:.2f}" if product.get("price_de") else "",
                            size=14,
                            color=ft.colors.GREY_500,
                            style=ft.TextStyle(decoration=ft.TextDecoration.LINE_THROUGH)
                        ) if product.get("price_de") else ft.Container(),
                        # Preço Por (destaque)
                        ft.Row([
                            ft.Text("R$", size=20, color=COLORS["success"]),
                            ft.Text(
                                str(int(product["price_por"])),
                                size=48,
                                weight=ft.FontWeight.BOLD,
                                color=COLORS["success"]
                            ),
                            ft.Text(
                                f",{int((product['price_por'] % 1) * 100):02d}",
                                size=24,
                                color=COLORS["success"]
                            )
                        ], alignment=ft.MainAxisAlignment.CENTER)
                    ], spacing=10, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                    bgcolor=COLORS["surface_elevated"],
                    border_radius=10,
                    padding=20,
                    width=280
                )
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=10),
            expand=True,
            alignment=ft.alignment.center
        )
    
    def build(self):
        # ===== HEADER =====
        header = ft.Container(
            content=ft.Row([
                ft.Column([
                    ft.Text("Fabrica de Cartazes", size=24, weight=ft.FontWeight.BOLD),
                    ft.Text("Producao em lote de cartazes de produto unico", 
                           size=14, color=ft.colors.GREY_400)
                ], spacing=5),
            ]),
            padding=ft.padding.only(bottom=20)
        )
        
        # ===== SELEÇÃO DE LAYOUT =====
        layout_options = [
            ft.dropdown.Option(str(l["id"]), f"{l['name']} ({l['type']})")
            for l in getattr(self, 'available_layouts', [])
        ]
        
        layout_selector = ft.Container(
            content=ft.Row([
                ft.Text("Layout:", size=14),
                ft.Dropdown(
                    options=layout_options if layout_options else [
                        ft.dropdown.Option("0", "Nenhum layout de cartaz disponivel")
                    ],
                    value=str(self.selected_layout["id"]) if self.selected_layout else None,
                    on_change=self._on_layout_selected,
                    width=300
                ),
                ft.Container(expand=True),
                ft.Dropdown(
                    label="DPI",
                    value=str(self.export_dpi),
                    options=[
                        ft.dropdown.Option("150", "150 (Web)"),
                        ft.dropdown.Option("300", "300 (Impressao)"),
                        ft.dropdown.Option("600", "600 (Alta)"),
                    ],
                    width=120,
                    on_change=lambda e: setattr(self, 'export_dpi', int(e.control.value))
                ),
                ft.Dropdown(
                    label="Cor",
                    value=self.color_mode,
                    options=[
                        ft.dropdown.Option("auto", "Automatico"),
                        ft.dropdown.Option("rgb", "RGB"),
                        ft.dropdown.Option("cmyk", "CMYK"),
                    ],
                    width=120,
                    on_change=lambda e: setattr(self, 'color_mode', e.control.value)
                )
            ]),
            padding=ft.padding.symmetric(vertical=10)
        )
        
        # ===== BARRA DE IMPORTAÇÃO =====
        import_bar = ft.Container(
            content=ft.Row([
                ft.ElevatedButton(
                    "Importar do Banco",
                    icon=ft.icons.STORAGE,
                    on_click=lambda e: self.page.run_task(self._import_from_db)
                ),
                ft.ElevatedButton(
                    "Importar Excel/CSV",
                    icon=ft.icons.UPLOAD_FILE,
                    on_click=self._import_from_file
                ),
                ft.Container(expand=True),
                ft.Text(f"{len(self.product_list)} produtos na lista", 
                       color=ft.colors.GREY_400) if self.product_list else ft.Container(),
                ft.IconButton(
                    ft.icons.CLEAR_ALL,
                    tooltip="Limpar lista",
                    on_click=self._clear_list
                ) if self.product_list else ft.Container()
            ]),
            padding=ft.padding.symmetric(vertical=10)
        )
        
        # ===== LISTA DE PRODUTOS =====
        product_list = ft.Container(
            content=ft.Column([
                ft.Text("Lista de Geracao", weight=ft.FontWeight.BOLD),
                ft.ListView(
                    controls=[self._build_product_row(p) for p in self.product_list],
                    spacing=5,
                    expand=True
                ) if self.product_list else ft.Container(
                    content=ft.Text("Importe produtos para iniciar", color=ft.colors.GREY_500),
                    alignment=ft.alignment.center,
                    expand=True
                )
            ], expand=True),
            bgcolor=COLORS["surface"],
            border_radius=10,
            padding=15,
            expand=1
        )
        
        # ===== PREVIEW =====
        preview_panel = ft.Container(
            content=self._build_preview_panel(),
            bgcolor=COLORS["surface"],
            border_radius=10,
            padding=15,
            expand=1
        )
        
        # ===== BARRA DE EXPORTAÇÃO =====
        export_bar = ft.Container(
            content=ft.Row([
                ft.ProgressBar(
                    value=self.render_progress,
                    color=COLORS["info"],
                    bgcolor=COLORS["surface"],
                    expand=True
                ) if self.is_rendering else ft.Container(expand=True),
                ft.Text(
                    f"Renderizando... {int(self.render_progress * 100)}%",
                    color=COLORS["info"]
                ) if self.is_rendering else ft.Container(),
                ft.ElevatedButton(
                    "Exportar PDF",
                    icon=ft.icons.PICTURE_AS_PDF,
                    style=ft.ButtonStyle(bgcolor=COLORS["info"], color=ft.colors.WHITE),
                    disabled=self.is_rendering or not self.product_list or not self.selected_layout,
                    on_click=lambda e: self.page.run_task(self._export_pdf)
                )
            ]),
            padding=ft.padding.symmetric(vertical=15)
        )
        
        # ===== LAYOUT PRINCIPAL =====
        return ft.Container(
            content=ft.Column([
                header,
                layout_selector,
                ft.Divider(height=1, color=ft.colors.GREY_800),
                import_bar,
                ft.Row([product_list, preview_panel], spacing=15, expand=True),
                export_bar
            ], expand=True),
            padding=30,
            expand=True
        )

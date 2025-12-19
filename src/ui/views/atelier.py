import flet as ft
from src.rendering.vector import VectorEngine
# Assumindo que você terá um Singleton ou Injeção de Dependência para o DB
# from src.core.database import get_db 

class AtelierView(ft.UserControl):
    def __init__(self, page: ft.Page):
        super().__init__()
        self.page = page
        self.vector_engine = VectorEngine()
        # Estado temporário (na versão final, virá do DB/State Manager)
        self.current_svg_path = "assets/templates/oferta_master.svg" 
        self.slots_available = [] 
        self.products_buffer = []

    def did_mount(self):
        # Simulação de carga inicial
        self.load_template()
        self.load_products()

    def load_template(self):
        # Carrega o SVG e descobre os slots disponíveis (Ex: SLOT_01, SLOT_02)
        try:
            # Em prod usar path real. Se não existir, avisa.
            self.vector_engine.load_template(self.current_svg_path)
            # O VectorEngine deve expor as chaves do dicionário de slots
            self.slots_available = [k for k in self.vector_engine.slots.keys() if k.startswith("SLOT_")]
        except Exception as e:
            print(f"Erro ao carregar template (pode ser esperado em dev): {e}")
            self.slots_available = ["SLOT_01", "SLOT_02"] # Mock fallback
            
        self.update_canvas()

    def load_products(self):
        # Aqui conectaria ao Repository. Mock para UI:
        self.products_buffer = [
            {"sku": "78910", "nome": "Café Pilão 500g", "preco": 19.90, "detalhe_peso": "500g", "nome_sanitizado": "Café Pilão", "images": []},
            {"sku": "78920", "nome": "Arroz Tio João 5kg", "preco": 24.50, "detalhe_peso": "5kg", "nome_sanitizado": "Arroz Tio João", "images": []},
            {"sku": "78930", "nome": "Sabão Omo 1kg", "preco": 12.99, "detalhe_peso": "1kg", "nome_sanitizado": "Sabão Omo", "images": []},
        ]
        self.update_product_list()

    def update_canvas(self):
        # Renderiza o SVG atual para Base64 para exibir no Flet
        # Nota: Flet não renderiza SVG complexo nativamente bem, 
        # então convertemos para PNG ou usamos ft.Image com src_base64 do SVG (se suportado pelo browser/client)
        # Para robustez, idealmente o VectorEngine teria um método .to_base64_image()
        # Aqui, usaremos um placeholder visual.
        self.canvas_image.src = f"https://placehold.co/600x400?text=Template+Renderizado" # Em prod: self.vector_engine.get_preview_base64()
        self.canvas_image.update()

    def update_product_list(self):
        self.product_list.controls.clear()
        for p in self.products_buffer:
            # Componente Draggable
            draggable = ft.Draggable(
                group="produtos",
                content=ft.Container(
                    content=ft.Column([
                        ft.Text(p['nome'], weight="bold"),
                        ft.Text(f"R$ {p['preco']:.2f}", size=12)
                    ], spacing=2),
                    padding=10,
                    bgcolor=ft.colors.SURFACE_VARIANT,
                    border_radius=5,
                    width=180,
                    border=ft.border.all(1, ft.colors.OUTLINE)
                ),
                content_feedback=ft.Container(
                    content=ft.Text(p['nome'], color=ft.colors.WHITE),
                    padding=10,
                    bgcolor=ft.colors.BLUE,
                    opacity=0.5,
                    border_radius=5
                ),
                data=p # Passa o objeto produto inteiro
            )
            self.product_list.controls.append(draggable)
        self.product_list.update()

    def on_canvas_drop(self, e: ft.DragTargetAcceptEvent):
        # Obtém dados do evento
        src_id = e.src_id
        # Flet Draggable data is connected via ID lookup often, but let's try direct approach or lookup
        # e.control is the target, e.src_id is drift source ID.
        # The data is transferred via 'data' property of draggable if page.get_control works.
        
        try:
            draggable_control = self.page.get_control(src_id)
            product = draggable_control.data
        except:
             return # Falha no drag

        # Lógica "Smart Drop":
        # Como não sabemos a coordenada X,Y exata do slot no XML:
        # Perguntamos ao usuário onde colocar.
        
        def assign_slot(slot_id):
            print(f"Preenchendo {slot_id} com {product['nome']}")
            # Chama a engine para preencher
            try:
                # Adapta dados para formato esperado pelo VectorEngine
                p_data = {
                    'nome_sanitizado': product.get('nome_sanitizado', product['nome']),
                    'detalhe_peso': product.get('detalhe_peso', ''),
                    'images': product.get('images', [])
                }
                
                self.vector_engine.handle_smart_slot(slot_id, p_data)
                self.vector_engine.handle_price_logic(slot_id, product['preco'])
                
                # Feedback visual (Toast)
                self.page.snack_bar = ft.SnackBar(ft.Text(f"Produto inserido em {slot_id}!"))
                self.page.snack_bar.open = True
                
                # Atualizar canvas (re-render)
                # self.update_canvas()
            except Exception as ex:
                print(f"Erro ao preencher slot: {ex}")
            
            dlg.open = False
            self.page.update()

        def close_dlg(_):
            dlg.open = False
            self.page.update()

        # Cria lista de botões para os slots disponíveis
        slot_buttons = []
        if not self.slots_available:
             slot_buttons.append(ft.Text("Nenhum slot disponível no template."))
        
        for slot in self.slots_available:
            slot_buttons.append(
                ft.FilledButton(text=f"Inserir em {slot}", on_click=lambda _, s=slot: assign_slot(s))
            )

        dlg = ft.AlertDialog(
            title=ft.Text(f"Posicionar '{product['nome']}'"),
            content=ft.Column(slot_buttons, height=200, scroll=ft.ScrollMode.AUTO),
            actions=[ft.TextButton("Cancelar", on_click=close_dlg)],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        self.page.dialog = dlg
        dlg.open = True
        self.page.update()

    def build(self):
        # Painel Esquerdo: Produtos
        self.product_list = ft.ListView(expand=True, spacing=10, padding=10)
        left_panel = ft.Container(
            content=ft.Column([
                ft.Text("Inventário", weight="bold", size=16),
                ft.Divider(),
                self.product_list
            ]),
            width=250,
            bgcolor=ft.colors.BACKGROUND,
            border=ft.border.only(right=ft.border.BorderSide(1, ft.colors.OUTLINE))
        )

        # Painel Direito: Canvas (DragTarget)
        self.canvas_image = ft.Image(src="https://placehold.co/600x400?text=Carregando...", fit=ft.ImageFit.CONTAIN)
        
        right_panel = ft.Container(
            content=ft.DragTarget(
                group="produtos",
                content=ft.Container(
                    content=self.canvas_image,
                    alignment=ft.alignment.center,
                    bgcolor=ft.colors.SURFACE, # Fundo neutro
                    border_radius=10,
                ),
                on_accept=self.on_canvas_drop
            ),
            expand=True,
            padding=20,
            bgcolor=ft.colors.SURFACE_VARIANT
        )

        return ft.Row([left_panel, right_panel], expand=True, spacing=0)

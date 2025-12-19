import flet as ft
import asyncio
# from src.rendering.output import OutputEngine

class FactoryView(ft.UserControl):
    def __init__(self, page: ft.Page):
        super().__init__()
        self.page = page
        self.is_processing = False
        # Mock Data Source
        self.batch_data = [
            {"id": 1, "produto": "Cerveja Heineken", "status": "Pronto"},
            {"id": 2, "produto": "Picanha Bovina", "status": "Pendente"},
            {"id": 3, "produto": "Coca-Cola 2L", "status": "Pendente"},
            # ... imagine 50 itens
        ]

    def process_batch(self, e):
        if self.is_processing: return
        self.is_processing = True
        self.btn_process.disabled = True
        self.progress_bar.value = 0
        self.status_text.value = "Iniciando motores..."
        self.update()

        # Inicia a task assíncrona para não travar a UI
        self.page.run_task(self._async_render_loop)

    async def _async_render_loop(self):
        total = len(self.batch_data)
        for i, item in enumerate(self.batch_data):
            # Simula trabalho pesado da OutputEngine
            item['status'] = "Renderizando..."
            self.status_text.value = f"Processando item {i+1}/{total}: {item['produto']}"
            self.update_grid() # Atualiza a tabela visualmente
            
            # Chama OutputEngine Real aqui
            # await asyncio.to_thread(output_engine.render, item) 
            await asyncio.sleep(0.5) # Simulação de tempo de CPU (Ghostscript)
            
            item['status'] = "Concluído"
            self.progress_bar.value = (i + 1) / total
            self.update()

        self.status_text.value = "Lote Finalizado com Sucesso!"
        self.btn_process.disabled = False
        self.is_processing = False
        self.update()

    def update_grid(self):
        # Reconstrói as linhas da tabela (método simples para Flet)
        self.data_table.rows = [
            ft.DataRow(cells=[
                ft.DataCell(ft.Text(str(d['id']))),
                ft.DataCell(ft.Text(d['produto'])),
                ft.DataCell(
                    ft.Icon(ft.icons.CHECK_CIRCLE, color="green") if d['status'] == "Concluído" 
                    else ft.ProgressRing(scale=0.5) if d['status'] == "Renderizando..."
                    else ft.Text(d['status'])
                ),
            ]) for d in self.batch_data
        ]
        self.data_table.update()

    def build(self):
        # Controles de Topo
        self.btn_process = ft.ElevatedButton(
            "Iniciar Produção em Massa", 
            icon=ft.icons.ROCKET_LAUNCH,
            on_click=self.process_batch,
            style=ft.ButtonStyle(bgcolor=ft.colors.RED_700, color=ft.colors.WHITE)
        )
        self.progress_bar = ft.ProgressBar(value=0, color="amber", bgcolor="#222222")
        self.status_text = ft.Text("Aguardando comando...", size=12, italic=True)

        header = ft.Container(
            content=ft.Column([
                ft.Row([ft.Text("Fábrica de Cartazes", size=24, weight="bold"), self.btn_process], alignment="spaceBetween"),
                self.progress_bar,
                self.status_text
            ]),
            padding=10,
            bgcolor=ft.colors.SURFACE_VARIANT,
            border_radius=10
        )

        # Grid de Dados
        self.data_table = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("ID")),
                ft.DataColumn(ft.Text("Produto")),
                ft.DataColumn(ft.Text("Status")),
            ],
            expand=True,
            heading_row_color=ft.colors.BLACK12,
            border=ft.border.all(1, ft.colors.OUTLINE_VARIANT),
            border_radius=10
        )
        self.update_grid() # Carga inicial

        return ft.Column([header, ft.Container(self.data_table, expand=True)], expand=True, spacing=10)

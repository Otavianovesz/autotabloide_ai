import os
import asyncio
import tempfile
import flet as ft
from pathlib import Path

# Imports do Pipeline Real
from src.rendering.vector import VectorEngine
from src.rendering.output import OutputEngine

# Caminho para o sistema
ROOT_DIR = Path(__file__).parent.parent.parent.parent.resolve()
SYSTEM_ROOT = ROOT_DIR / "AutoTabloide_System_Root"

class FactoryView(ft.UserControl):
    def __init__(self, page: ft.Page):
        super().__init__()
        self.page = page
        self.is_processing = False
        
        # Engines de Renderização
        self.output_engine = OutputEngine(str(SYSTEM_ROOT))
        self.template_path = str(SYSTEM_ROOT / "library" / "svg_source" / "cartaz_a4.svg")
        
        # Mock Data Source (Em prod, viria do Repository)
        self.batch_data = [
            {"id": 1, "produto": "Cerveja Heineken 350ml", "preco": 5.99, "status": "Pendente"},
            {"id": 2, "produto": "Picanha Bovina kg", "preco": 49.90, "status": "Pendente"},
            {"id": 3, "produto": "Coca-Cola 2L", "preco": 9.99, "status": "Pendente"},
        ]
        
        # Diretório de saída
        self.output_dir = SYSTEM_ROOT / "temp_render"
        os.makedirs(self.output_dir, exist_ok=True)

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
        rendered_pdfs = []
        
        for i, item in enumerate(self.batch_data):
            item['status'] = "Renderizando..."
            self.status_text.value = f"Processando item {i+1}/{total}: {item['produto']}"
            self.update_grid()
            
            try:
                # 1. Carregar e manipular SVG em thread separada
                pdf_path = await asyncio.to_thread(
                    self._render_single_item, 
                    item, 
                    i
                )
                
                if pdf_path:
                    rendered_pdfs.append(pdf_path)
                    item['status'] = "Concluído"
                else:
                    item['status'] = "Erro"
                    
            except Exception as ex:
                item['status'] = f"Erro: {str(ex)[:20]}"
                print(f"[FACTORY ERROR] {item['produto']}: {ex}")
            
            self.progress_bar.value = (i + 1) / total
            self.update()

        # Resumo final
        success_count = sum(1 for d in self.batch_data if d['status'] == "Concluído")
        self.status_text.value = f"Lote Finalizado! {success_count}/{total} PDFs gerados em {self.output_dir}"
        self.btn_process.disabled = False
        self.is_processing = False
        self.update()

    def _render_single_item(self, item: dict, index: int) -> str:
        """
        Renderiza um único item para PDF CMYK.
        Roda em thread separada via asyncio.to_thread.
        """
        # 1. Instância nova do VectorEngine (thread-safe: nova instância por item)
        vector = VectorEngine()
        
        # Verifica se template existe
        if not os.path.exists(self.template_path):
            # Fallback: Criar SVG mínimo para teste
            temp_svg = tempfile.NamedTemporaryFile(mode='w', suffix='.svg', delete=False)
            temp_svg.write(f'''<svg xmlns="http://www.w3.org/2000/svg" width="595" height="842">
                <rect width="100%" height="100%" fill="white"/>
                <text id="TXT_NOME_PRODUTO" x="50" y="100" style="font-size:40px">{item['produto']}</text>
                <text id="TXT_PRECO_BIG_SLOT_01" x="50" y="200" style="font-size:80px">R$ {item['preco']:.2f}</text>
            </svg>''')
            temp_svg.close()
            vector.load_template(temp_svg.name)
            os.unlink(temp_svg.name)
        else:
            vector.load_template(self.template_path)
        
        # 2. Preencher dados no SVG
        # Nota: A lógica de preço assume que o template tem slots padrão
        try:
            vector.handle_price_logic("SLOT_01", preco_atual=item['preco'])
        except:
            pass # Template pode não ter slots DE/POR
        
        # 3. Exportar SVG manipulado para bytes
        svg_bytes = vector.to_string()
        
        # 4. Renderizar PDF RGB
        pdf_rgb_path = str(self.output_dir / f"item_{index}_rgb.pdf")
        self.output_engine.render_pdf(svg_bytes, pdf_rgb_path)
        
        # 5. Converter para CMYK (Ghostscript)
        pdf_cmyk_path = str(self.output_dir / f"item_{index}_cmyk.pdf")
        try:
            self.output_engine.convert_to_cmyk(pdf_rgb_path, pdf_cmyk_path)
            # Limpa arquivo RGB intermediário
            os.remove(pdf_rgb_path)
            return pdf_cmyk_path
        except Exception as e:
            print(f"[CMYK WARN] Falha na conversão CMYK (usando RGB): {e}")
            # Retorna o RGB se CMYK falhar (degradation graceful apenas aqui)
            return pdf_rgb_path

    def update_grid(self):
        # Reconstrói as linhas da tabela
        self.data_table.rows = [
            ft.DataRow(cells=[
                ft.DataCell(ft.Text(str(d['id']))),
                ft.DataCell(ft.Text(d['produto'])),
                ft.DataCell(ft.Text(f"R$ {d['preco']:.2f}")),
                ft.DataCell(
                    ft.Icon(ft.icons.CHECK_CIRCLE, color="green") if d['status'] == "Concluído" 
                    else ft.ProgressRing(scale=0.5) if d['status'] == "Renderizando..."
                    else ft.Icon(ft.icons.ERROR, color="red") if "Erro" in d['status']
                    else ft.Text(d['status'], size=11)
                ),
            ]) for d in self.batch_data
        ]
        # Only call update() if the control is attached to a page (not during build)
        if self.data_table.page:
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
                ft.DataColumn(ft.Text("Preço")),
                ft.DataColumn(ft.Text("Status")),
            ],
            expand=True,
            heading_row_color=ft.colors.BLACK12,
            border=ft.border.all(1, ft.colors.OUTLINE_VARIANT),
            border_radius=10
        )
        self.update_grid()

        return ft.Column([header, ft.Container(self.data_table, expand=True)], expand=True, spacing=10)

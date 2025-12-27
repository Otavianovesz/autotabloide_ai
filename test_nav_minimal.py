"""
TESTE MÍNIMO ABSOLUTO - NavigationRail
Objetivo: Provar que NavigationRail funciona com layout correto
"""
import flet as ft


def main(page: ft.Page):
    page.title = "TESTE NavigationRail"
    page.padding = 0
    page.spacing = 0
    
    # CRITICAL: NavigationRail não pode ter expand=True
    # Ele precisa estar dentro de container com altura definida
    
    rail = ft.NavigationRail(
        selected_index=0,
        label_type=ft.NavigationRailLabelType.ALL,
        min_width=80,
        min_extended_width=200,
        extended=True,
        # NÃO USAR expand=True aqui!
        group_alignment=-0.9,
        bgcolor="#1a1a2e",
        destinations=[
            ft.NavigationRailDestination(
                icon=ft.icons.HOME_OUTLINED,
                selected_icon=ft.icons.HOME,
                label="Home"
            ),
            ft.NavigationRailDestination(
                icon=ft.icons.SETTINGS_OUTLINED,
                selected_icon=ft.icons.SETTINGS,
                label="Config"
            ),
        ],
    )
    
    # Body simples
    body = ft.Container(
        content=ft.Text("CORPO PRINCIPAL", size=32, color="white"),
        expand=True,
        bgcolor="#16213e",
        alignment=ft.alignment.center,
    )
    
    # SOLUÇÃO CORRETA: Usar Row com expand=True na página
    # O NavigationRail herda altura da Row que expande
    layout = ft.Row(
        controls=[rail, body],
        expand=True,  # Row expande para preencher página
        spacing=0,
    )
    
    # Adicionar à página - único controle com expand
    page.add(layout)


if __name__ == "__main__":
    print("Iniciando teste mínimo em modo WEB (porta 8560)...")
    ft.app(target=main, view=ft.AppView.WEB_BROWSER, port=8560)

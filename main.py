"""
AutoTabloide AI - Entry Point Principal
=========================================
Conforme Vol. VI, Cap. 1 - Shell de Aplicação.
Orquestra inicialização, navegação e ciclo de vida.
"""

import os
import sys
import platform
import asyncio
from pathlib import Path

# ==============================================================================
# CONFIGURAÇÃO DE AMBIENTE (BOOTSTRAP)
# ==============================================================================

ROOT_DIR = Path(__file__).parent.resolve()
SYSTEM_ROOT = ROOT_DIR / "AutoTabloide_System_Root"
BIN_DIR = SYSTEM_ROOT / "bin"

def setup_environment():
    """Configura ambiente de execução com DLLs e paths."""
    if not BIN_DIR.exists():
        print(f"[BOOT ERROR] Diretorio de binarios nao encontrado: {BIN_DIR}")
        print("Execute 'python setup.py' ou verifique a instalacao.")
        sys.exit(1)

    # Adiciona bin ao PATH
    os.environ["PATH"] = str(BIN_DIR) + os.pathsep + os.environ["PATH"]
    
    # Windows 3.8+ - DLL directories
    if platform.system() == "Windows" and hasattr(os, "add_dll_directory"):
        try:
            os.add_dll_directory(str(BIN_DIR))
        except Exception as e:
            print(f"[BOOT WARNING] Falha ao adicionar DLLs: {e}")

def check_integrity():
    """Verificação de integridade antes do boot."""
    try:
        from src.infrastructure.integrity import IntegrityChecker
        checker = IntegrityChecker()
        checker.run()
    except ImportError:
        print("[BOOT] Modulo de integridade nao encontrado. Pulando check.")
    except Exception as e:
        print(f"[BOOT ERROR] Falha na verificacao: {e}")

async def init_database():
    """Inicializa banco de dados de forma assíncrona."""
    try:
        from src.core.database import init_db
        await init_db()
        print("[SYSTEM] Banco de dados inicializado.")
    except Exception as e:
        print(f"[BOOT ERROR] Falha ao inicializar DB: {e}")

# ==============================================================================
# ENTRY POINT
# ==============================================================================

if __name__ == "__main__":
    # 1. Configurar Ambiente
    setup_environment()
    
    # 2. Verificar Integridade
    check_integrity()
    
    # 3. Inicializar Safe Mode (Vol. III, Cap. 8.2)
    from src.core.safe_mode import init_safe_mode, get_safe_mode_controller
    safe_mode_controller, is_safe_mode = init_safe_mode(SYSTEM_ROOT)
    
    if is_safe_mode:
        print("\n[⚠️ SAFE MODE] Sistema em modo de recuperação!")
        print("[⚠️ SAFE MODE] Recursos limitados ativados.")
    
    # 4. Iniciar Aplicação
    try:
        print("\n[SYSTEM] Inicializando AutoTabloide AI...")
        
        import flet as ft
        import multiprocessing
        from src.ai.sentinel import SentinelProcess
        
        # Views
        from src.ui.views.dashboard import DashboardView
        from src.ui.views.estoque import EstoqueView
        from src.ui.views.atelier import AtelierView
        from src.ui.views.factory import FactoryView
        from src.ui.views.cofre import CofreView
        from src.ui.views.settings import SettingsView
        
        # NeuralEngine (processo isolado para IA)
        from src.ai.neural_engine import initialize_neural_engine, shutdown_neural_engine
        
        # Configuração do Sentinel (AI Sidecar)
        sentinel_config = {
            "model_path": str(SYSTEM_ROOT / "bin" / "Llama-3-8b-instruct.Q4_K_M.gguf"),
            "temp_dir": str(SYSTEM_ROOT / "staging" / "downloads")
        }
        
        # Queues IPC
        sentinel_in_q = multiprocessing.Queue()
        sentinel_out_q = multiprocessing.Queue()
        
        # Inicializa Processo Sentinel
        sentinel = SentinelProcess(sentinel_in_q, sentinel_out_q, sentinel_config)
        sentinel.start()
        print(f"[SYSTEM] Sentinel Sidecar PID: {sentinel.pid}")

        def main(page: ft.Page):
            # === Import Design System ===
            from src.ui.design_system import ColorScheme, apply_page_theme
            
            # === Configuração da Página (Vol. VI, Cap. 1.1) ===
            page.title = "AutoTabloide AI - Codex Industrialis"
            
            # Aplica tema premium
            apply_page_theme(page)
            page.scroll = ft.ScrollMode.HIDDEN  # Rolagem gerenciada por componentes
            
            # Dimensões mínimas (Vol. VI, Tab. 1.1)
            page.window_min_width = 1280
            page.window_min_height = 720
            page.window_width = 1400
            page.window_height = 900
            
            # Inicializa DB de forma assíncrona
            page.run_task(init_database)
            
            # Cache de views para preservar estado
            view_cache = {}
            
            def get_view(index: int):
                """Retorna view cacheada ou cria nova."""
                if index not in view_cache:
                    if index == 0:
                        view_cache[index] = DashboardView(page)
                    elif index == 1:
                        view_cache[index] = EstoqueView(page)
                    elif index == 2:
                        view_cache[index] = AtelierView(page)
                    elif index == 3:
                        view_cache[index] = FactoryView(page)
                    elif index == 4:
                        view_cache[index] = CofreView(page)
                    elif index == 5:
                        view_cache[index] = SettingsView(page)
                return view_cache.get(index)
            
            def change_view(e):
                """Handler de navegação."""
                idx = e.control.selected_index
                view = get_view(idx)
                
                if view:
                    body.content = view
                else:
                    body.content = ft.Container(
                        content=ft.Text("Tela nao implementada", size=24),
                        alignment=ft.alignment.center
                    )
                
                # Colapsa nav rail na tela de Montagem (Vol. VI, Cap. 1.2)
                if idx == 2:  # Ateliê/Montagem
                    rail.extended = False
                else:
                    rail.extended = True
                
                body.update()
                rail.update()

            # === Navigation Rail (Vol. VI, Cap. 1.2) ===
            rail = ft.NavigationRail(
                selected_index=0,
                label_type=ft.NavigationRailLabelType.ALL,
                min_width=72,
                min_extended_width=200,
                extended=True,
                group_alignment=-0.9,
                bgcolor=ColorScheme.BG_PRIMARY,
                indicator_color=ColorScheme.ACCENT_PRIMARY,
                destinations=[
                    ft.NavigationRailDestination(
                        icon=ft.icons.DASHBOARD_OUTLINED,
                        selected_icon=ft.icons.DASHBOARD,
                        label="Dashboard"
                    ),
                    ft.NavigationRailDestination(
                        icon=ft.icons.INVENTORY_2_OUTLINED,
                        selected_icon=ft.icons.INVENTORY_2,
                        label="Estoque"
                    ),
                    ft.NavigationRailDestination(
                        icon=ft.icons.BRUSH_OUTLINED,
                        selected_icon=ft.icons.BRUSH,
                        label="Atelie"
                    ),
                    ft.NavigationRailDestination(
                        icon=ft.icons.FACTORY_OUTLINED,
                        selected_icon=ft.icons.FACTORY,
                        label="Fabrica"
                    ),
                    ft.NavigationRailDestination(
                        icon=ft.icons.SHIELD_OUTLINED,
                        selected_icon=ft.icons.SHIELD,
                        label="Cofre"
                    ),
                    ft.NavigationRailDestination(
                        icon=ft.icons.SETTINGS_OUTLINED,
                        selected_icon=ft.icons.SETTINGS,
                        label="Config"
                    ),
                ],
                on_change=change_view
            )

            # === Corpo Principal ===
            body = ft.Container(
                content=DashboardView(page),  # View inicial
                expand=True,
                bgcolor=ColorScheme.BG_PRIMARY,
                padding=0
            )

            # === Barra de Status Inferior (Vol. VI, Cap. 1.3) ===
            # Importa componente de telemetria
            from src.ui.components.status_bar import StatusBarWithTelemetry
            
            status_bar = StatusBarWithTelemetry(
                on_sentinel_click=lambda: print("[UI] Sentinel clicked"),
                on_db_click=lambda: print("[UI] DB clicked")
            )
            
            # Atualiza status inicial do Sentinel
            status_bar.set_sentinel_status("online" if sentinel.is_alive() else "offline")

            # === Layout Principal ===
            page.add(
                ft.Column(
                    [
                        ft.Row(
                            [
                                rail,
                                ft.VerticalDivider(width=1, color=ColorScheme.BORDER_DEFAULT),
                                body
                            ],
                            expand=True,
                            spacing=0
                        ),
                        status_bar
                    ],
                    expand=True,
                    spacing=0
                )
            )
            
            # === Cleanup no Fechamento ===
            def on_window_event(e):
                if e.data == "close":
                    print("[SYSTEM] Encerrando processos...")
                    sentinel_in_q.put({"type": "STOP"})
                    sentinel.join(timeout=2)
                    shutdown_neural_engine()
                    page.window_destroy()
            
            page.window_prevent_close = True
            page.on_window_event = on_window_event

        # Inicia aplicação Flet
        ft.app(target=main)
        
    except ImportError as e:
        print(f"\n[CRITICAL ERROR] Falha ao importar: {e}")
        print("Verifique se ativou o ambiente virtual (poetry shell).")
        if 'sentinel' in locals() and sentinel.is_alive():
            sentinel.terminate()
        input("Pressione ENTER para sair...")
        
    except Exception as e:
        print(f"\n[CRITICAL ERROR] Erro fatal: {e}")
        import traceback
        traceback.print_exc()
        if 'sentinel' in locals() and sentinel.is_alive():
            sentinel.terminate()
        input("Pressione ENTER para sair...")

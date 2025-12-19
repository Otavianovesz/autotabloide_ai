import os
import sys
import platform
import subprocess
from pathlib import Path

# ==============================================================================
# CONFIGURAÇÃO DE AMBIENTE (BOOTSTRAP)
# ==============================================================================
# Executa ANTES de qualquer outro import para garantir que DLLs sejam carregadas
# conforme especificado no Codex Industrialis (Local-First).
# ==============================================================================

ROOT_DIR = Path(__file__).parent.resolve()
SYSTEM_ROOT = ROOT_DIR / "AutoTabloide_System_Root"
BIN_DIR = SYSTEM_ROOT / "bin"

def setup_environment():
    """Configura o ambiente de execução, injetando caminhos de DLLs."""
    if not BIN_DIR.exists():
        print(f"[BOOT ERROR] Diretório de binários não encontrado: {BIN_DIR}")
        print("Execute 'python setup.py' ou verifique a instalação.")
        sys.exit(1)

    # Adiciona bin ao PATH do sistema (para subprocessos e carregamento padrão)
    os.environ["PATH"] = str(BIN_DIR) + os.pathsep + os.environ["PATH"]
    
    # Adiciona dll_directory para Python 3.8+ no Windows (Crítico para CairoSVG/GTK)
    if platform.system() == "Windows" and hasattr(os, "add_dll_directory"):
        try:
            os.add_dll_directory(str(BIN_DIR))
            # print(f"[BOOT] DLLs carregadas de: {BIN_DIR}")
        except Exception as e:
            print(f"[BOOT WARNING] Falha ao adicionar diretório de DLLs: {e}")

def check_integrity():
    """Verificação rápida de integridade antes do boot da UI."""
    try:
        from src.infrastructure.integrity import IntegrityChecker
        checker = IntegrityChecker()
        checker.run()
    except ImportError:
        print("[BOOT] Módulo de integridade não encontrado ou erro de importação. Pulando check detalhado.")
    except Exception as e:
        print(f"[BOOT ERROR] Falha na verificação de integridade: {e}")
        sys.exit(1)

# ==============================================================================
# ENTRY POINT
# ==============================================================================

if __name__ == "__main__":
    # 1. Configurar Ambiente (DLLs, Paths)
    setup_environment()
    
    # 2. Verificar Integridade
    check_integrity()
    
    # 3. Iniciar Aplicação
    try:
        print("\n[SYSTEM] Inicializando AutoTabloide AI...")
        print("[SYSTEM] Todos os sistemas operacionais.")
        
        # Imports tardios para garantir DLL loading
        import flet as ft
        import multiprocessing
        from src.ai.sentinel import SentinelProcess
        from src.ui.views.atelier import AtelierView
        from src.ui.views.factory import FactoryView
        
        # Configuração do Sidecar (Sentinel)
        # Em prod, config viria de arquivo/db
        sentinel_config = {
            "model_path": str(SYSTEM_ROOT / "bin" / "Llama-3-8B-Instruct.Q4_K_M.gguf"),
            "temp_dir": str(SYSTEM_ROOT / "staging" / "downloads")
        }
        
        # Queues de Comunicação
        sentinel_in_q = multiprocessing.Queue()
        sentinel_out_q = multiprocessing.Queue()
        
        # Inicializa Processo em Background
        sentinel = SentinelProcess(sentinel_in_q, sentinel_out_q, sentinel_config)
        sentinel.start()
        print(f"[SYSTEM] Sentinel Sidecar PID: {sentinel.pid}")

        def main(page: ft.Page):
            page.title = "AutoTabloide AI - Codex Industrialis"
            page.theme_mode = ft.ThemeMode.DARK
            page.window_width = 1400
            page.window_height = 900
            page.padding = 0
            
            # State Management simples para navegação
            def change_view(e):
                selected_index = e.control.selected_index
                if selected_index == 0:
                    body.content = ft.Container(
                        content=ft.Text("Dashboard / Visão Geral (Em Breve)", size=30),
                        alignment=ft.alignment.center
                    )
                elif selected_index == 1: # Estoque (Mock)
                     body.content = ft.Container(
                        content=ft.Text("Gestão de Estoque & Juiz (Em Breve)", size=30),
                        alignment=ft.alignment.center
                    )
                elif selected_index == 2: # Ateliê
                    body.content = AtelierView(page)
                elif selected_index == 3: # Fábrica
                    body.content = FactoryView(page)
                
                body.update()

            # Navigation Rail (Menu Lateral)
            rail = ft.NavigationRail(
                selected_index=0,
                label_type=ft.NavigationRailLabelType.ALL,
                min_width=100,
                min_extended_width=200,
                group_alignment=-0.9,
                destinations=[
                    ft.NavigationRailDestination(
                        icon=ft.icons.DASHBOARD_OUTLINED, 
                        selected_icon=ft.icons.DASHBOARD, 
                        label="Geral"
                    ),
                    ft.NavigationRailDestination(
                        icon=ft.icons.INVENTORY_2_OUTLINED, 
                        selected_icon=ft.icons.INVENTORY_2, 
                        label="Estoque"
                    ),
                    ft.NavigationRailDestination(
                        icon_content=ft.Icon(ft.icons.BRUSH_OUTLINED),
                        selected_icon_content=ft.Icon(ft.icons.BRUSH),
                        label="Ateliê"
                    ),
                    ft.NavigationRailDestination(
                        icon=ft.icons.FACTORY_OUTLINED, 
                        selected_icon=ft.icons.FACTORY, 
                        label="Fábrica"
                    ),
                ],
                on_change=change_view
            )

            # Corpo Principal
            body = ft.Container(
                content=ft.Container(
                    content=ft.Text("Bem-vindo ao AutoTabloide AI", size=30),
                    alignment=ft.alignment.center
                ),
                expand=True,
                bgcolor=ft.colors.BACKGROUND,
                padding=20
            )

            page.add(
                ft.Row(
                    [
                        rail,
                        ft.VerticalDivider(width=1),
                        body
                    ],
                    expand=True,
                )
            )
            
            # Cleanup no fechamento da janela
            def on_window_event(e):
                if e.data == "close":
                    print("[SYSTEM] Encerrando Sentinel...")
                    sentinel_in_q.put({"type": "STOP"})
                    # Dá um tempo para o processo morrer
                    sentinel.join(timeout=2)
                    page.window_destroy()
            
            page.window_prevent_close = True
            page.on_window_event = on_window_event

        ft.app(target=main)
        
    except ImportError as e:
        print(f"\n[CRITICAL ERROR] Falha ao importar dependências: {e}")
        print("Verifique se ativou o ambiente virtual (poetry shell) ou instalou as dependências.")
        if 'sentinel' in locals() and sentinel.is_alive():
             sentinel.terminate()
        input("Pressione ENTER para sair...")
    except Exception as e:
        print(f"\n[CRITICAL ERROR] Erro não tratado na execução: {e}")
        if 'sentinel' in locals() and sentinel.is_alive():
             sentinel.terminate()
        input("Pressione ENTER para sair...")

"""
AutoTabloide AI - Entry Point Principal (Refatorado)
=====================================================
Conforme Vol. VI, Cap. 1 - Shell de Aplicação.
Refatorado para usar infraestrutura industrial.
CENTURY CHECKLIST: Items 2, 10 integrados.
"""

import sys
from pathlib import Path

# ==============================================================================
# CONFIGURAÇÃO DE AMBIENTE (BOOTSTRAP)
# ==============================================================================

ROOT_DIR = Path(__file__).parent.resolve()
SYSTEM_ROOT = ROOT_DIR / "AutoTabloide_System_Root"
BIN_DIR = SYSTEM_ROOT / "bin"


def setup_environment() -> None:
    """
    Configura ambiente de execução com DLLs, paths e diretórios.
    
    CHECKLIST ITEMS:
    - #11: Criação de /library/fonts/ no boot
    - #12: Limpeza de /temp_render/ a cada boot
    - #102/105/109: Inicialização de industrial_robustness
    """
    import os
    import platform
    import shutil
    
    if not BIN_DIR.exists():
        BIN_DIR.mkdir(parents=True, exist_ok=True)

    # Adiciona bin ao PATH
    os.environ["PATH"] = str(BIN_DIR) + os.pathsep + os.environ.get("PATH", "")
    
    # Windows 3.8+ - DLL directories
    if platform.system() == "Windows" and hasattr(os, "add_dll_directory"):
        try:
            os.add_dll_directory(str(BIN_DIR))
        except Exception:
            pass  # Ignora silenciosamente
    
    # =========================================================================
    # #11: Criação de diretórios obrigatórios (Vol. I, Tab. 2.1)
    # =========================================================================
    required_dirs = [
        SYSTEM_ROOT / "library" / "fonts",       # #11: Fontes do usuário
        SYSTEM_ROOT / "assets" / "profiles",     # #10: Perfis ICC
        SYSTEM_ROOT / "staging" / "downloads",   # Staging para Hunter
        SYSTEM_ROOT / "logs",                    # Logs do sistema
    ]
    
    for dir_path in required_dirs:
        dir_path.mkdir(parents=True, exist_ok=True)
    
    # =========================================================================
    # #12: Limpeza de /temp_render/ a cada boot (Vol. I, Tab. 2.1)
    # =========================================================================
    temp_render = SYSTEM_ROOT / "temp_render"
    if temp_render.exists():
        try:
            shutil.rmtree(temp_render)
        except Exception:
            # Se falhar, tenta remover arquivos individualmente
            for file in temp_render.glob("*"):
                try:
                    file.unlink()
                except Exception:
                    pass
    temp_render.mkdir(parents=True, exist_ok=True)
    
    # =========================================================================
    # #102/105/109: Inicialização de Industrial Robustness
    # =========================================================================
    try:
        from src.core.industrial_robustness import initialize_industrial_robustness
        initialize_industrial_robustness()
    except ImportError:
        pass  # Módulo não disponível
    
    # =========================================================================
    # CENTURY CHECKLIST: Inicialização de Sistemas Industriais
    # =========================================================================
    try:
        from src.core.century_industrial import initialize_industrial_systems
        # Inicializa MemoryWatchdog, LogCleaner, TempDirectoryManager, etc.
        _industrial_systems = initialize_industrial_systems(SYSTEM_ROOT)
    except ImportError:
        pass  # Módulo não disponível
    except Exception:
        pass  # Falha silenciosa para não bloquear boot


def check_single_instance() -> bool:
    """
    CENTURY CHECKLIST ITEM 2: Verifica se já existe outra instância rodando.
    Retorna True se pode continuar, False se já existe instância.
    """
    try:
        from src.core.instance_lock import acquire_instance_lock
        
        if not acquire_instance_lock():
            # Mostra popup amigável no Windows
            if sys.platform == "win32":
                try:
                    import ctypes
                    ctypes.windll.user32.MessageBoxW(
                        0, 
                        "O AutoTabloide AI já está rodando em outra janela!\n\n"
                        "Verifique a barra de tarefas.",
                        "AutoTabloide AI", 
                        0x40  # MB_ICONINFORMATION
                    )
                except:
                    print("AVISO: Outra instância do AutoTabloide AI já está rodando!")
            return False
        return True
    except ImportError:
        # Módulo não disponível - permite execução
        return True


def check_dependencies() -> bool:
    """
    CENTURY CHECKLIST ITEM 10: Verifica dependências críticas.
    Mostra popup amigável se algo estiver faltando.
    """
    missing = []
    
    # Verifica Flet
    try:
        import flet
    except ImportError:
        missing.append("flet")
    
    # Verifica SQLAlchemy
    try:
        import sqlalchemy
    except ImportError:
        missing.append("sqlalchemy")
    
    if missing:
        msg = (
            f"Dependências faltando:\n\n"
            f"• {', '.join(missing)}\n\n"
            f"Execute: poetry install\n"
            f"Ou: pip install {' '.join(missing)}"
        )
        
        if sys.platform == "win32":
            try:
                import ctypes
                ctypes.windll.user32.MessageBoxW(0, msg, "AutoTabloide AI - Erro", 0x10)
            except:
                print(f"ERRO: {msg}")
        else:
            print(f"ERRO: {msg}")
        
        return False
    
    return True


def setup_logging():
    """Configura sistema de logging industrial."""
    from src.core.logging_config import setup_logging as init_logging, get_logger
    
    log_dir = SYSTEM_ROOT / "logs"
    init_logging(log_dir, console_output=True, file_output=True)
    
    return get_logger("Main")


def run_integrity_checks(logger) -> bool:
    """
    Executa verificações de integridade com self-healing.
    Passos 51-60: Integra SystemHealthCheck do infrastructure.py
    """
    from src.core.integrity import run_startup_checks
    
    success, is_safe_mode = run_startup_checks(SYSTEM_ROOT)
    
    if is_safe_mode:
        logger.warning("⚠️ SAFE MODE: Sistema em modo de recuperação!")
    
    # Verifica saúde do sistema (Ghostscript, VC++, offline mode)
    try:
        from src.core.infrastructure import verify_ghostscript, check_offline_mode
        
        gs_ok, gs_version = verify_ghostscript()
        if gs_ok:
            logger.info(f"Ghostscript v{gs_version} disponível")
        else:
            logger.warning(f"Ghostscript não encontrado: {gs_version}")
        
        offline = check_offline_mode()
        if all([offline.get("database"), offline.get("templates"), offline.get("fonts")]):
            logger.info("Modo offline: Sistema funciona sem internet")
        else:
            missing = [k for k, v in offline.items() if not v]
            logger.warning(f"Modo offline parcial. Faltando: {missing}")
            
    except ImportError:
        logger.debug("infrastructure.py não disponível")
    
    return is_safe_mode


def register_services(logger):
    """Registra serviços no container de DI."""
    from src.core.container import register, register_instance
    from src.core.utils import LifecycleManager
    
    # Registrar LifecycleManager
    lifecycle = LifecycleManager(SYSTEM_ROOT)
    register_instance(LifecycleManager, lifecycle)
    
    logger.info("Serviços registrados no container de DI")
    
    return lifecycle


async def init_database():
    """Inicializa banco de dados de forma assíncrona."""
    from src.core.logging_config import get_logger
    logger = get_logger("Database")
    
    try:
        from src.core.database import init_db
        await init_db()
        logger.info("Banco de dados inicializado com WAL mode")
    except Exception as e:
        logger.error(f"Falha ao inicializar DB: {e}")
        raise


# ==============================================================================
# ENTRY POINT
# ==============================================================================

if __name__ == "__main__":
    # 1. Verificar Dependências (antes de tudo!)
    if not check_dependencies():
        sys.exit(1)
    
    # 2. Verificar Instância Única (CENTURY CHECKLIST ITEM 2)
    if not check_single_instance():
        sys.exit(0)
    
    # 3. Configurar Ambiente
    setup_environment()
    
    # 4. Configurar Logging
    logger = setup_logging()
    logger.info("=" * 60)
    logger.info("AutoTabloide AI - Iniciando...")
    logger.info("=" * 60)
    
    # 5. Integridade e Self-Healing
    is_safe_mode = run_integrity_checks(logger)
    
    # 6. Registrar Serviços (DI Container)
    lifecycle = register_services(logger)
    
    # 5. Iniciar Aplicação
    try:
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
        from src.ai.neural_engine import shutdown_neural_engine
        
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
        logger.info(f"Sentinel Sidecar iniciado (PID: {sentinel.pid})")
        
        # Passo 21-22: Configura Watchdog para reiniciar Sentinel se morrer
        from src.ai.sentinel_watchdog import get_watchdog
        watchdog = get_watchdog()
        
        def create_sentinel():
            """Factory para criar novo Sentinel."""
            return SentinelProcess(sentinel_in_q, sentinel_out_q, sentinel_config)
        
        watchdog.set_sentinel(sentinel, create_sentinel)
        logger.info("Sentinel Watchdog configurado")

        def main(page: ft.Page):
            # === Import Design System ===
            from src.ui.design_system import ColorScheme, apply_page_theme
            from src.core.constants import UIConfig, AppInfo
            
            # === Integração de Keyboard Manager e Event Bus ===
            from src.ui.keyboard import get_keyboard_manager, setup_keyboard_handlers
            from src.core.event_bus import get_event_bus, EventType, emit
            from src.ui.audio import get_audio, init_audio
            
            # Inicializa sistemas
            keyboard = get_keyboard_manager()
            event_bus = get_event_bus()
            audio = init_audio(SYSTEM_ROOT / "assets" / "sounds", enabled=True)
            
            # === Configuração da Página (Vol. VI, Cap. 1.1) ===
            page.title = f"{AppInfo.NAME} v{AppInfo.VERSION}"
            
            # Aplica tema premium
            apply_page_theme(page)
            page.scroll = ft.ScrollMode.HIDDEN
            
            # Dimensões mínimas (Vol. VI, Tab. 1.1)
            page.window_min_width = UIConfig.MIN_WIDTH
            page.window_min_height = UIConfig.MIN_HEIGHT
            page.window_width = 1400
            page.window_height = 900
            
            # Inicializa DB de forma assíncrona
            page.run_task(init_database)
            
            # Cache de views para preservar estado
            view_cache = {}
            
            def get_view(index: int):
                """Retorna view cacheada ou cria nova."""
                if index not in view_cache:
                    view_classes = [
                        DashboardView, EstoqueView, AtelierView,
                        FactoryView, CofreView, SettingsView
                    ]
                    if 0 <= index < len(view_classes):
                        view_cache[index] = view_classes[index](page)
                return view_cache.get(index)
            
            def change_view(e):
                """Handler de navegação."""
                idx = e.control.selected_index
                view = get_view(idx)
                
                if view:
                    body.content = view
                else:
                    body.content = ft.Container(
                        content=ft.Text("Tela não implementada", size=24),
                        alignment=ft.alignment.center
                    )
                
                # Colapsa nav rail na tela de Montagem
                rail.extended = idx != 2
                
                # Atualiza view atual no keyboard manager
                keyboard.set_current_view(["dashboard", "estoque", "atelier", "factory", "cofre", "settings"][idx])
                
                # Emite evento de mudança de view
                emit(EventType.VIEW_CHANGED, view_index=idx)
                
                body.update()
                rail.update()
            
            def navigate_to(index: int):
                """Navega para view pelo índice via atalho."""
                rail.selected_index = index
                # Simula evento de navegação
                class FakeEvent:
                    control = type('obj', (object,), {'selected_index': index})()
                change_view(FakeEvent())
                audio.click()
            
            # === Registra handlers de navegação (Ctrl+1-6) ===
            keyboard.set_handler("nav_dashboard", lambda: navigate_to(0))
            keyboard.set_handler("nav_estoque", lambda: navigate_to(1))
            keyboard.set_handler("nav_atelier", lambda: navigate_to(2))
            keyboard.set_handler("nav_factory", lambda: navigate_to(3))
            keyboard.set_handler("nav_cofre", lambda: navigate_to(4))
            keyboard.set_handler("nav_settings", lambda: navigate_to(5))
            
            # Handler de Escape (cancela modal atual)
            def handle_escape():
                if page.dialog and page.dialog.open:
                    page.dialog.open = False
                    page.update()
            keyboard.set_handler("cancel", handle_escape)
            
            # Conecta evento de teclado do Flet
            page.on_keyboard_event = lambda e: keyboard.handle_key_event(e)

            # === Navigation Rail (Vol. VI, Cap. 1.2) ===
            rail = ft.NavigationRail(
                selected_index=0,
                label_type=ft.NavigationRailLabelType.ALL,
                min_width=UIConfig.RAIL_WIDTH_COLLAPSED,
                min_extended_width=UIConfig.RAIL_WIDTH_EXPANDED,
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
                        label="Ateliê"
                    ),
                    ft.NavigationRailDestination(
                        icon=ft.icons.FACTORY_OUTLINED,
                        selected_icon=ft.icons.FACTORY,
                        label="Fábrica"
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
                content=DashboardView(page),
                expand=True,
                bgcolor=ColorScheme.BG_PRIMARY,
                padding=0
            )

            # === Barra de Status Inferior (Vol. VI, Cap. 1.3) ===
            from src.ui.components.status_bar import StatusBarWithTelemetry
            
            status_bar = StatusBarWithTelemetry(
                on_sentinel_click=lambda: None,
                on_db_click=lambda: None
            )
            
            status_bar.set_sentinel_status("online" if sentinel.is_alive() else "offline")
            
            # === Sentinel IPC Subscriber ===
            async def sentinel_subscriber():
                """Loop que recebe mensagens do Sentinel."""
                import asyncio
                from src.core.logging_config import get_logger
                sub_logger = get_logger("Sentinel.Subscriber")
                
                while True:
                    try:
                        # Checa processo vivo
                        if sentinel.is_alive():
                            if status_bar._telemetry.sentinel_status == "offline":
                                status_bar.set_sentinel_status("online")
                        else:
                            status_bar.set_sentinel_status("offline")
                        
                        # Processa mensagens (non-blocking)
                        while not sentinel_out_q.empty():
                            try:
                                msg = sentinel_out_q.get_nowait()
                                msg_type = msg.get("type", "")
                                
                                if msg_type == "HEARTBEAT":
                                    status_bar.set_sentinel_status("online")
                                elif msg_type == "STATUS":
                                    status_bar.set_sentinel_status(msg.get("status", "online"))
                                elif msg_type == "BUSY":
                                    status_bar.set_sentinel_status("busy")
                            except Exception:
                                break
                        
                        await asyncio.sleep(2)
                        
                    except asyncio.CancelledError:
                        break
                    except Exception as e:
                        sub_logger.error(f"Erro no subscriber: {e}")
                        await asyncio.sleep(5)
            
            page.run_task(sentinel_subscriber)

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
                    from src.core.logging_config import get_logger
                    close_logger = get_logger("Shutdown")
                    close_logger.info("Encerrando aplicação...")
                    
                    # Parar Sentinel
                    sentinel_in_q.put({"type": "STOP"})
                    sentinel.join(timeout=2)
                    
                    # Cleanup de serviços
                    shutdown_neural_engine()
                    lifecycle.shutdown()
                    
                    close_logger.info("Shutdown concluído")
                    page.window_destroy()
            
            page.window_prevent_close = True
            page.on_window_event = on_window_event

        # Inicia aplicação Flet
        logger.info("Iniciando interface Flet...")
        ft.app(target=main)
        
    except ImportError as e:
        logger.critical(f"Falha ao importar: {e}")
        logger.info("Verifique se ativou o ambiente virtual (poetry shell)")
        if 'sentinel' in locals() and sentinel.is_alive():
            sentinel.terminate()
        input("Pressione ENTER para sair...")
        
    except Exception as e:
        logger.critical(f"Erro fatal: {e}", exc_info=True)
        if 'sentinel' in locals() and sentinel.is_alive():
            sentinel.terminate()
        if 'lifecycle' in locals():
            lifecycle.shutdown()
        input("Pressione ENTER para sair...")

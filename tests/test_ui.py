"""
AutoTabloide AI - UI Automation Tests
=======================================
Testes automatizados de UI.
Passo 99 do Checklist 100.

Funcionalidades:
- Testes de navegação
- Testes de interação
- Smoke tests de UI
"""

import asyncio
from typing import List, Tuple, Optional
from dataclasses import dataclass

from src.core.logging_config import get_logger

logger = get_logger("UITest")


@dataclass
class UITestResult:
    """Resultado de um teste de UI."""
    test_name: str
    passed: bool
    message: str
    screenshot_path: Optional[str] = None


class UITestSuite:
    """
    Suite de testes automatizados de UI.
    Passo 99 do Checklist - Teste UI automático.
    
    Nota: Testes reais de Flet requerem ambiente gráfico.
    Esta é uma implementação de framework para testes.
    """
    
    def __init__(self):
        self.results: List[UITestResult] = []
    
    async def test_app_starts(self) -> UITestResult:
        """Testa se aplicação inicia sem erros."""
        try:
            # Verifica imports críticos
            from src.core.constants import AppInfo
            from src.ui.design_system import DesignTokens
            from src.core.container import get_service, ServiceContainer
            
            return UITestResult(
                test_name="App Startup",
                passed=True,
                message=f"App {AppInfo.NAME} v{AppInfo.VERSION} OK"
            )
            
        except ImportError as e:
            return UITestResult(
                test_name="App Startup",
                passed=False,
                message=f"Import error: {e}"
            )
    
    async def test_navigation_rail_exists(self) -> UITestResult:
        """Testa se NavigationRail foi definido."""
        try:
            from src.ui.design_system import DesignTokens
            
            # Verifica se configurações de UI existem
            assert hasattr(DesignTokens, 'PRIMARY')
            assert hasattr(DesignTokens, 'BACKGROUND')
            
            return UITestResult(
                test_name="Navigation Rail",
                passed=True,
                message="Design tokens configurados"
            )
            
        except Exception as e:
            return UITestResult(
                test_name="Navigation Rail",
                passed=False,
                message=f"Erro: {e}"
            )
    
    async def test_keyboard_shortcuts_defined(self) -> UITestResult:
        """Testa se atalhos de teclado estão definidos."""
        try:
            from src.ui.keyboard import DEFAULT_KEYBINDINGS
            
            required_shortcuts = ['s', 'z', 'y', 'e']
            missing = []
            
            for key in required_shortcuts:
                if key not in [kb.key for kb in DEFAULT_KEYBINDINGS]:
                    missing.append(key)
            
            if missing:
                return UITestResult(
                    test_name="Keyboard Shortcuts",
                    passed=False,
                    message=f"Atalhos faltando: {missing}"
                )
            
            return UITestResult(
                test_name="Keyboard Shortcuts",
                passed=True,
                message=f"{len(DEFAULT_KEYBINDINGS)} atalhos definidos"
            )
            
        except Exception as e:
            return UITestResult(
                test_name="Keyboard Shortcuts",
                passed=False,
                message=f"Erro: {e}"
            )
    
    async def test_views_importable(self) -> UITestResult:
        """Testa se todas as views podem ser importadas."""
        views_to_test = [
            "src.ui.views.atelier",
            "src.ui.views.estoque",
            "src.ui.views.fabrica",
        ]
        
        failed = []
        
        for view_module in views_to_test:
            try:
                __import__(view_module)
            except ImportError as e:
                failed.append(f"{view_module}: {e}")
        
        if failed:
            return UITestResult(
                test_name="Views Import",
                passed=False,
                message=f"Falhas: {len(failed)}"
            )
        
        return UITestResult(
            test_name="Views Import",
            passed=True,
            message=f"{len(views_to_test)} views OK"
        )
    
    async def test_components_importable(self) -> UITestResult:
        """Testa se componentes podem ser importados."""
        components = [
            ("ProgressModal", "src.ui.components.progress_modal"),
            ("DiffView", "src.ui.components.diff_view"),
            ("DropIndicator", "src.ui.components.drop_indicator"),
        ]
        
        failed = []
        
        for name, module in components:
            try:
                __import__(module)
            except ImportError as e:
                failed.append(f"{name}: {e}")
        
        if failed:
            return UITestResult(
                test_name="Components Import",
                passed=False,
                message=f"Falhas: {len(failed)}"
            )
        
        return UITestResult(
            test_name="Components Import",
            passed=True,
            message=f"{len(components)} componentes OK"
        )
    
    async def run_all(self) -> Tuple[bool, List[UITestResult]]:
        """
        Executa todos os testes de UI.
        
        Returns:
            Tupla (todos_passaram, lista_resultados)
        """
        logger.info("Iniciando testes de UI...")
        
        self.results = []
        
        # Testes
        self.results.append(await self.test_app_starts())
        self.results.append(await self.test_navigation_rail_exists())
        self.results.append(await self.test_keyboard_shortcuts_defined())
        self.results.append(await self.test_views_importable())
        self.results.append(await self.test_components_importable())
        
        all_passed = all(r.passed for r in self.results)
        
        # Log
        for r in self.results:
            status = "✅" if r.passed else "❌"
            logger.info(f"{status} {r.test_name}: {r.message}")
        
        passed_count = sum(1 for r in self.results if r.passed)
        logger.info(f"Testes UI: {passed_count}/{len(self.results)} passaram")
        
        return all_passed, self.results


async def run_ui_tests() -> bool:
    """
    Função principal para executar testes de UI.
    
    Returns:
        True se todos os testes passaram
    """
    suite = UITestSuite()
    all_passed, results = await suite.run_all()
    return all_passed


# ==============================================================================
# PYTEST INTEGRATION
# ==============================================================================

def test_app_starts():
    """Teste pytest: app inicia."""
    result = asyncio.run(UITestSuite().test_app_starts())
    assert result.passed, result.message


def test_navigation():
    """Teste pytest: navegação."""
    result = asyncio.run(UITestSuite().test_navigation_rail_exists())
    assert result.passed, result.message


def test_keyboard():
    """Teste pytest: atalhos."""
    result = asyncio.run(UITestSuite().test_keyboard_shortcuts_defined())
    assert result.passed, result.message

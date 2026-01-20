"""
AutoTabloide AI - UI Automation Tests
=======================================
Testes automatizados de UI para Qt/PySide6.
Atualizado para refletir migração de Flet para PySide6.

Funcionalidades:
- Testes de imports críticos
- Testes de widgets Qt
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
    Testes de importação e estrutura para Qt/PySide6.
    """
    
    def __init__(self):
        self.results: List[UITestResult] = []
    
    async def test_app_starts(self) -> UITestResult:
        """Testa se aplicação inicia sem erros."""
        try:
            # Verifica imports críticos
            from src.core.constants import AppInfo
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
    
    async def test_qt_framework_available(self) -> UITestResult:
        """Testa se PySide6 está disponível."""
        try:
            from PySide6.QtWidgets import QApplication, QMainWindow, QWidget
            from PySide6.QtCore import Qt, Signal
            from PySide6.QtGui import QPainter, QColor
            
            return UITestResult(
                test_name="Qt Framework",
                passed=True,
                message="PySide6 disponível"
            )
            
        except ImportError as e:
            return UITestResult(
                test_name="Qt Framework",
                passed=False,
                message=f"PySide6 não instalado: {e}"
            )
    
    async def test_main_window_imports(self) -> UITestResult:
        """Testa se MainWindow pode ser importada."""
        try:
            from src.qt.main_window import MainWindow
            
            return UITestResult(
                test_name="MainWindow Import",
                passed=True,
                message="MainWindow importada com sucesso"
            )
            
        except ImportError as e:
            return UITestResult(
                test_name="MainWindow Import",
                passed=False,
                message=f"Erro: {e}"
            )
    
    async def test_widgets_importable(self) -> UITestResult:
        """Testa se widgets Qt podem ser importados."""
        widgets_to_test = [
            ("AtelierWidget", "src.qt.widgets.atelier"),
            ("EstoqueWidget", "src.qt.widgets.estoque"),
            ("FactoryWidget", "src.qt.widgets.factory"),
            ("CofreWidget", "src.qt.widgets.cofre"),
            ("SettingsWidget", "src.qt.widgets.settings"),
        ]
        
        failed = []
        
        for name, module in widgets_to_test:
            try:
                __import__(module)
            except ImportError as e:
                failed.append(f"{name}: {e}")
        
        if failed:
            return UITestResult(
                test_name="Widgets Import",
                passed=False,
                message=f"Falhas: {len(failed)}"
            )
        
        return UITestResult(
            test_name="Widgets Import",
            passed=True,
            message=f"{len(widgets_to_test)} widgets OK"
        )
    
    async def test_dialogs_importable(self) -> UITestResult:
        """Testa se dialogs Qt podem ser importados."""
        dialogs = [
            ("ExcelImportDialog", "src.qt.dialogs.excel_import"),
            ("JudgeModal", "src.qt.dialogs.judge_modal"),
            ("ImageHandlerDialog", "src.qt.dialogs.image_handler"),
            ("BatchExportDialog", "src.qt.dialogs.batch_export"),
        ]
        
        failed = []
        
        for name, module in dialogs:
            try:
                __import__(module)
            except ImportError as e:
                failed.append(f"{name}: {e}")
        
        if failed:
            return UITestResult(
                test_name="Dialogs Import",
                passed=False,
                message=f"Falhas: {len(failed)}"
            )
        
        return UITestResult(
            test_name="Dialogs Import",
            passed=True,
            message=f"{len(dialogs)} dialogs OK"
        )
    
    async def test_graphics_importable(self) -> UITestResult:
        """Testa se módulos graphics podem ser importados."""
        graphics = [
            ("SmartSlot", "src.qt.graphics.smart_slot"),
            ("SmartItems", "src.qt.graphics.smart_items"),
            ("SceneBuilder", "src.qt.graphics.scene_builder"),
        ]
        
        failed = []
        
        for name, module in graphics:
            try:
                __import__(module)
            except ImportError as e:
                failed.append(f"{name}: {e}")
        
        if failed:
            return UITestResult(
                test_name="Graphics Import",
                passed=False,
                message=f"Falhas: {len(failed)}"
            )
        
        return UITestResult(
            test_name="Graphics Import",
            passed=True,
            message=f"{len(graphics)} graphics OK"
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
        self.results.append(await self.test_qt_framework_available())
        self.results.append(await self.test_main_window_imports())
        self.results.append(await self.test_widgets_importable())
        self.results.append(await self.test_dialogs_importable())
        self.results.append(await self.test_graphics_importable())
        
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


def test_qt_framework():
    """Teste pytest: Qt framework."""
    result = asyncio.run(UITestSuite().test_qt_framework_available())
    assert result.passed, result.message


def test_main_window():
    """Teste pytest: MainWindow."""
    result = asyncio.run(UITestSuite().test_main_window_imports())
    assert result.passed, result.message


def test_widgets():
    """Teste pytest: widgets."""
    result = asyncio.run(UITestSuite().test_widgets_importable())
    assert result.passed, result.message


def test_dialogs():
    """Teste pytest: dialogs."""
    result = asyncio.run(UITestSuite().test_dialogs_importable())
    assert result.passed, result.message


def test_graphics():
    """Teste pytest: graphics."""
    result = asyncio.run(UITestSuite().test_graphics_importable())
    assert result.passed, result.message

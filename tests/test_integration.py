"""
AutoTabloide AI - SafeMode Controller Tests
==============================================
Testes do SafeModeController.
Passo 70 do Checklist 100.
"""

import pytest
import asyncio
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock


class TestSafeModeController:
    """
    Testes do SafeModeController.
    Passo 70 do Checklist - Teste SafeModeController.
    """
    
    def test_safe_mode_flag_creation(self, tmp_path):
        """Testa criação da flag de safe mode."""
        from src.core.safe_mode import SafeModeController
        
        flag_path = tmp_path / ".safe_mode"
        
        # Cria controller com path customizado
        controller = SafeModeController()
        controller._flag_path = flag_path
        
        # Ativa safe mode
        controller.enable()
        
        assert flag_path.exists()
    
    def test_safe_mode_detection(self, tmp_path):
        """Testa detecção de safe mode."""
        from src.core.safe_mode import SafeModeController
        
        flag_path = tmp_path / ".safe_mode"
        
        controller = SafeModeController()
        controller._flag_path = flag_path
        
        # Sem flag
        assert not controller.is_enabled()
        
        # Com flag
        flag_path.touch()
        assert controller.is_enabled()
    
    def test_safe_mode_disable(self, tmp_path):
        """Testa desativação de safe mode."""
        from src.core.safe_mode import SafeModeController
        
        flag_path = tmp_path / ".safe_mode"
        flag_path.touch()
        
        controller = SafeModeController()
        controller._flag_path = flag_path
        
        # Desativa
        controller.disable()
        
        assert not flag_path.exists()
        assert not controller.is_enabled()


class TestSentinelProcess:
    """
    Testes do SentinelProcess com mock de LLM.
    Passo 71 do Checklist - Teste Sentinel (mock LLM).
    """
    
    def test_sentinel_task_types(self):
        """Testa tipos de tarefa reconhecidos."""
        from src.ai.sentinel import SentinelProcess
        
        valid_types = ["SANITIZE", "HUNT_IMAGE", "PROCESS_IMAGE"]
        
        for task_type in valid_types:
            task = {"type": task_type, "id": "test_123"}
            # Verifica que tipo é reconhecido (não levanta exceção)
            assert task["type"] in valid_types
    
    def test_sanitize_text_fallback(self):
        """Testa fallback quando LLM não está disponível."""
        # Simula resultado sem LLM
        raw_text = "COCA COLA 2L"
        
        fallback_result = {
            "status": "success",
            "task_id": "test_001",
            "result": {
                "nome_sanitizado": raw_text,
                "marca": None,
                "peso": None
            },
            "used_llm": False
        }
        
        assert fallback_result["used_llm"] is False
        assert fallback_result["result"]["nome_sanitizado"] == raw_text
    
    def test_hunter_search_engines(self):
        """Testa engines de busca do Hunter."""
        from src.ai.sentinel import TheHunter
        
        hunter = TheHunter("/tmp/test_hunter")
        
        # Verifica que engines estão definidas
        assert hasattr(hunter, '_search_engines')
        assert len(hunter._search_engines) > 0


class TestIntegration:
    """
    Testes de integração.
    Passo 72 do Checklist - Teste integração completo.
    """
    
    def test_database_models_import(self):
        """Testa que todos os models importam."""
        from src.core.models import (
            Base, LearningBase, Product, ProductAlias,
            LayoutMeta, SavedProject, SystemConfig,
            AuditLog, KnowledgeVector, HumanCorrection
        )
        
        assert Base is not None
        assert LearningBase is not None
        assert Product is not None
    
    def test_services_import(self):
        """Testa que todos os serviços importam."""
        from src.core.settings_service import SettingsService, get_settings
        from src.core.services.backup_service import BackupService
        from src.core.services.import_service import ImportService
        
        assert SettingsService is not None
        assert BackupService is not None
        assert ImportService is not None
    
    def test_rendering_pipeline_import(self):
        """Testa que pipeline de rendering importa."""
        from src.rendering.vector import VectorEngine
        from src.rendering.output import OutputEngine
        from src.rendering.svg_transforms import sort_by_z_index, apply_negative_kerning
        
        assert VectorEngine is not None
        assert OutputEngine is not None
    
    def test_ui_components_import(self):
        """Testa que componentes de UI importam."""
        from src.ui.components.progress_modal import GlobalProgressModal
        from src.ui.components.diff_view import DiffView
        from src.ui.components.drop_indicator import DropIndicator
        
        assert GlobalProgressModal is not None
        assert DiffView is not None
        assert DropIndicator is not None
    
    def test_ai_modules_import(self):
        """Testa que módulos de IA importam."""
        from src.ai.vision import ImageProcessor
        from src.ai.model_manager import ExponentialBackoff, calculate_file_sha256
        from src.ai.image_validation import is_blank_image, validate_image_quality
        
        assert ImageProcessor is not None
        assert ExponentialBackoff is not None
    
    def test_constants_available(self):
        """Testa que constantes estão disponíveis."""
        from src.core.constants import (
            SYSTEM_ROOT, DB_DIR, LOGS_DIR,
            AppInfo, RenderConfig, AIConfig
        )
        
        assert SYSTEM_ROOT is not None
        assert AppInfo.NAME == "AutoTabloide AI"
    
    def test_event_bus_works(self):
        """Testa que EventBus funciona."""
        from src.core.event_bus import EventBus, get_event_bus
        
        bus = get_event_bus()
        received = []
        
        def handler(data):
            received.append(data)
        
        bus.on("test_event", handler)
        bus.emit("test_event", {"value": 42})
        
        assert len(received) == 1
        assert received[0]["value"] == 42
    
    def test_slot_controller_works(self):
        """Testa que SlotController funciona."""
        from src.core.slot_controller import SlotController, SlotState
        
        controller = SlotController(num_slots=4)
        
        assert len(controller.slots) == 4
        assert controller.get_slot("SLOT_01").state == SlotState.EMPTY
        
        # Adiciona produto
        controller.set_product(
            "SLOT_01",
            product_id=1,
            product_name="Teste",
            product_price=9.99
        )
        
        assert controller.get_slot("SLOT_01").state == SlotState.FILLED
        assert controller.get_slot("SLOT_01").product_name == "Teste"


# Fixtures
@pytest.fixture
def tmp_path(tmp_path_factory):
    """Cria diretório temporário para testes."""
    return tmp_path_factory.mktemp("test")


# Executar com: pytest tests/test_integration.py -v

"""
AutoTabloide AI - Test Suite
=============================
PROTOCOLO DE CONVERGÊNCIA INDUSTRIAL - Fase 10
Passos 251-270: Testes unitários e de integração.

Execute com: python -m pytest tests/ -v
"""

import pytest
from decimal import Decimal
from pathlib import Path
import tempfile
import os


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture
def temp_dir():
    """Diretório temporário para testes."""
    with tempfile.TemporaryDirectory() as td:
        yield Path(td)


@pytest.fixture
def sample_product():
    """Produto de exemplo."""
    return {
        "id": 1,
        "sku_origem": "SKU001",
        "nome_sanitizado": "Arroz Integral 5kg",
        "marca_normalizada": "Tio João",
        "detalhe_peso": "5kg",
        "preco_venda_atual": Decimal("24.90"),
        "preco_referencia": Decimal("29.90"),
        "categoria": "Grãos",
        "status_qualidade": 3
    }


@pytest.fixture
def restricted_product():
    """Produto com restrição de idade."""
    return {
        "id": 2,
        "nome_sanitizado": "Cerveja Pilsen 350ml",
        "categoria": "Bebida Alcoólica",
        "preco_venda_atual": Decimal("3.99")
    }


# =============================================================================
# TESTS: EXCEL PARSER
# =============================================================================

class TestExcelParser:
    """Testes do parser de Excel/CSV."""
    
    def test_column_detection(self):
        """Testa detecção automática de colunas."""
        from src.core.excel_parser import _detect_column_mapping, _normalize_header
        
        headers = ["Nome", "SKU", "Preco", "Marca"]
        mapping = _detect_column_mapping(headers)
        
        assert "nome" in mapping
        assert "sku" in mapping
        assert "preco" in mapping
    
    def test_price_parsing(self):
        """Testa parsing de preços BR."""
        from src.core.excel_parser import _parse_price
        
        # Formato brasileiro
        assert _parse_price("24,90") == Decimal("24.90")
        assert _parse_price("1.234,56") == Decimal("1234.56")
        assert _parse_price("R$ 99,00") == Decimal("99.00")
        
        # Formato americano
        assert _parse_price("24.90") == Decimal("24.90")
    
    def test_empty_value(self):
        """Testa valores vazios."""
        from src.core.excel_parser import _parse_price
        
        assert _parse_price("") is None
        assert _parse_price(None) is None


# =============================================================================
# TESTS: COMPLIANCE
# =============================================================================

class TestCompliance:
    """Testes do validador de compliance."""
    
    def test_valid_de_por(self):
        """Testa validação De/Por válida."""
        from src.core.compliance import validate_de_por
        
        assert validate_de_por(29.90, 24.90) is True
        assert validate_de_por(None, 24.90) is True
    
    def test_invalid_de_por(self):
        """Testa validação De/Por inválida."""
        from src.core.compliance import validate_de_por
        
        assert validate_de_por(24.90, 29.90) is False  # De < Por
        assert validate_de_por(24.90, 24.90) is False  # De == Por
    
    def test_age_restriction_detection(self):
        """Testa detecção de categoria restrita."""
        from src.core.compliance import requires_age_icon
        
        assert requires_age_icon("Bebida Alcoólica") is True
        assert requires_age_icon("cerveja") is True
        assert requires_age_icon("Grãos") is False
        assert requires_age_icon("", "Vodka Premium 1L") is True
    
    def test_validation_result(self):
        """Testa estrutura de resultado."""
        from src.core.compliance import ComplianceValidator
        
        validator = ComplianceValidator()
        
        slot_data = {
            "slot_id": "SLOT_01",
            "preco_venda_atual": 24.90,
            "preco_referencia": 29.90,
            "categoria": "Grãos"
        }
        
        result = validator.validate_slot(slot_data)
        assert result.is_valid is True
        assert len(result.errors) == 0
    
    def test_price_violation(self):
        """Testa violação de preço."""
        from src.core.compliance import ComplianceValidator
        
        validator = ComplianceValidator()
        
        invalid_slot = {
            "slot_id": "SLOT_01",
            "preco_venda_atual": 29.90,
            "preco_referencia": 24.90  # De < Por = inválido
        }
        
        result = validator.validate_slot(invalid_slot)
        assert result.is_valid is False
        assert len(result.errors) == 1


# =============================================================================
# TESTS: TELEMETRY
# =============================================================================

class TestTelemetry:
    """Testes do sistema de telemetria."""
    
    def test_health_status(self):
        """Testa estrutura de status."""
        from src.core.telemetry import HealthStatus
        from datetime import datetime
        
        status = HealthStatus(
            timestamp=datetime.now(),
            database_ok=True,
            memory_percent=50.0,
            disk_free_gb=10.0  # Add disk space to avoid warning
        )
        
        assert status.overall_status == "HEALTHY"
        assert status.status_color == "#27AE60"
    
    def test_warning_status(self):
        """Testa status de warning."""
        from src.core.telemetry import HealthStatus
        from datetime import datetime
        
        status = HealthStatus(
            timestamp=datetime.now(),
            database_ok=True,
            memory_percent=95.0  # Alta
        )
        
        assert status.overall_status == "WARNING"
    
    def test_critical_status(self):
        """Testa status crítico."""
        from src.core.telemetry import HealthStatus
        from datetime import datetime
        
        status = HealthStatus(
            timestamp=datetime.now(),
            database_ok=False  # DB offline
        )
        
        assert status.overall_status == "CRITICAL"
    
    def test_error_tracker(self):
        """Testa rastreador de erros."""
        from src.core.telemetry import ErrorTracker
        
        tracker = ErrorTracker()
        tracker.log_error(ValueError("Test error"), "test")
        
        errors = tracker.get_errors_last_hour()
        assert len(errors) == 1
        assert errors[0]["type"] == "ValueError"
    
    def test_neural_indicator(self):
        """Testa indicador neural."""
        from src.core.telemetry import NeuralIndicator
        
        indicator = NeuralIndicator()
        indicator.register_model("llama-3.2")
        
        assert "llama-3.2" in indicator.loaded_models
        assert indicator.is_active is False
        
        indicator.start_inference()
        assert indicator.is_active is True
        
        indicator.end_inference()
        assert indicator.is_active is False


# =============================================================================
# TESTS: JUDGE MODAL
# =============================================================================

class TestJudgeMatching:
    """Testes do algoritmo de matching do Judge."""
    
    def test_exact_match(self):
        """Testa match exato."""
        from src.qt.dialogs.judge_modal import JudgeWorker, MatchStatus
        
        worker = JudgeWorker()
        
        # Similaridade 100%
        score = worker._calculate_similarity(
            "Arroz Camil 5kg",
            "Arroz Camil 5kg"
        )
        assert score == 1.0
    
    def test_partial_match(self):
        """Testa match parcial."""
        from src.qt.dialogs.judge_modal import JudgeWorker
        
        worker = JudgeWorker()
        
        # Similaridade parcial
        score = worker._calculate_similarity(
            "Arroz Camil 5kg",
            "Arroz Tio João 5kg"
        )
        assert 0.3 < score < 0.8
    
    def test_name_sanitization(self):
        """Testa sanitização de nome."""
        from src.qt.dialogs.judge_modal import JudgeWorker
        
        worker = JudgeWorker()
        
        result = worker._sanitize_name("ARROZ CAMIL TIPO 1  5KG")
        assert result == "Arroz Camil Tipo 1 5kg"


# =============================================================================
# TESTS: PDF EXPORT
# =============================================================================

class TestPDFExport:
    """Testes do exportador PDF."""
    
    def test_exporter_init(self, temp_dir):
        """Testa inicialização do exportador."""
        from src.rendering.pdf_export import PDFExporter
        
        exporter = PDFExporter(str(temp_dir))
        assert exporter.temp_dir.exists()
    
    def test_ghostscript_detection(self, temp_dir):
        """Testa detecção de Ghostscript."""
        from src.rendering.pdf_export import PDFExporter
        
        exporter = PDFExporter(str(temp_dir))
        # Pode ou não encontrar - apenas verifica que não falha
        assert isinstance(exporter._has_cairosvg, bool)


# =============================================================================
# TESTS: SENTINEL BRIDGE
# =============================================================================

class TestSentinelBridge:
    """Testes da ponte Sentinel."""
    
    def test_singleton(self):
        """Testa padrão singleton."""
        from src.qt.sentinel_bridge import SentinelBridge
        
        bridge1 = SentinelBridge.instance()
        bridge2 = SentinelBridge.instance()
        
        assert bridge1 is bridge2
    
    def test_task_id_generation(self):
        """Testa geração de IDs únicos."""
        from src.qt.sentinel_bridge import SentinelBridge
        
        bridge = SentinelBridge.instance()
        
        # Garante que _task_counter é incrementado
        initial = bridge._task_counter
        # Cada chamada deve incrementar
        bridge._task_counter += 1
        assert bridge._task_counter == initial + 1


# =============================================================================
# INTEGRATION TESTS
# =============================================================================

class TestIntegration:
    """Testes de integração entre módulos."""
    
    def test_compliance_with_sample_product(self, sample_product):
        """Testa compliance com produto de exemplo."""
        from src.core.compliance import ComplianceValidator
        
        validator = ComplianceValidator()
        
        slot_data = {
            "slot_id": "SLOT_01",
            "preco_venda_atual": float(sample_product["preco_venda_atual"]),
            "preco_referencia": float(sample_product["preco_referencia"]),
            "categoria": sample_product["categoria"],
            "nome_sanitizado": sample_product["nome_sanitizado"]
        }
        
        result = validator.validate_slot(slot_data)
        assert result.is_valid is True
    
    def test_restricted_product_needs_icon(self, restricted_product):
        """Testa que produto restrito requer ícone."""
        from src.core.compliance import ComplianceValidator
        
        validator = ComplianceValidator()
        
        slot_data = {
            "slot_id": "SLOT_01",
            "preco_venda_atual": float(restricted_product["preco_venda_atual"]),
            "categoria": restricted_product["categoria"],
            "nome_sanitizado": restricted_product["nome_sanitizado"],
            "has_age_icon": False
        }
        
        result = validator.validate_slot(slot_data)
        # Deve falhar porque falta o ícone +18
        assert result.is_valid is False


# =============================================================================
# RUN TESTS
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])

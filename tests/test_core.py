"""
AutoTabloide AI - Testes Unitários Core
=========================================
Testes para módulos críticos do sistema.
Passos 69-72 do Checklist 100.
"""

import pytest
import asyncio
from decimal import Decimal
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock


# ==============================================================================
# TESTES: BARCODE UTILS (Passo 40, 87)
# ==============================================================================

class TestBarcodeUtils:
    """Testes para geração de código de barras EAN-13."""
    
    def test_calculate_checksum_valid(self):
        """Testa cálculo de checksum para EAN válido."""
        from src.rendering.barcode_utils import calculate_ean13_checksum
        
        # 789100011202? -> ? deve ser 8
        checksum = calculate_ean13_checksum("789100011202")
        assert checksum == 8
    
    def test_validate_ean13_valid(self):
        """Testa validação de EAN-13 válido."""
        from src.rendering.barcode_utils import validate_ean13
        
        assert validate_ean13("7891000112028") == True
        assert validate_ean13("0000000000017") == True
    
    def test_validate_ean13_invalid(self):
        """Testa rejeição de EAN-13 inválido."""
        from src.rendering.barcode_utils import validate_ean13
        
        assert validate_ean13("7891000112029") == False  # checksum errado
        assert validate_ean13("123") == False  # muito curto
        assert validate_ean13("abcdefghijklm") == False  # não numérico
    
    def test_normalize_ean(self):
        """Testa normalização de códigos."""
        from src.rendering.barcode_utils import normalize_ean
        
        # 12 dígitos -> adiciona checksum
        result = normalize_ean("789100011202")
        assert result == "7891000112028"
        
        # Código curto -> padding zeros
        result = normalize_ean("12345")
        assert len(result) == 13
    
    def test_generate_svg(self):
        """Testa geração de SVG."""
        from src.rendering.barcode_utils import generate_ean13_svg
        
        svg = generate_ean13_svg("7891000112028")
        
        assert '<svg' in svg
        assert '</svg>' in svg
        assert '<rect' in svg  # Deve ter barras


# ==============================================================================
# TESTES: EXCEPTIONS (Passo 73-74)
# ==============================================================================

class TestExceptions:
    """Testes para hierarquia de exceções."""
    
    def test_base_exception(self):
        """Testa AutoTabloideException."""
        from src.core.exceptions import AutoTabloideException
        
        exc = AutoTabloideException("Erro teste", code="TEST_001")
        
        assert "Erro teste" in str(exc)
        assert exc.code == "TEST_001"
        assert exc.recoverable == True
    
    def test_validation_error(self):
        """Testa ValidationError com campo."""
        from src.core.exceptions import ValidationError
        
        exc = ValidationError("Preço inválido", field="price", value="-10")
        
        assert exc.details["field"] == "price"
        assert "invalid_value" in exc.details
    
    def test_friendly_message(self):
        """Testa mensagens amigáveis."""
        from src.core.exceptions import get_friendly_message, AutoTabloideException
        
        # Exceção customizada
        custom_exc = AutoTabloideException("Mensagem legível")
        msg = get_friendly_message(custom_exc)
        assert msg == "Mensagem legível"


# ==============================================================================
# TESTES: SETTINGS SERVICE (Passo 10-11)
# ==============================================================================

class TestSettingsService:
    """Testes para SettingsService."""
    
    def test_default_settings(self):
        """Testa que valores padrão existem."""
        from src.core.settings_service import DEFAULT_SETTINGS
        
        assert "llm.model_path" in DEFAULT_SETTINGS
        assert "render.dpi_print" in DEFAULT_SETTINGS
        assert DEFAULT_SETTINGS["render.dpi_print"]["value"] == 300
    
    def test_is_restricted(self):
        """Testa detecção de palavras +18."""
        from src.core.settings_service import SettingsService
        
        service = SettingsService()
        # Popula cache manualmente para teste
        service._cache = {
            "restricted.alcohol_keywords": ["cerveja", "vodka"],
            "restricted.tobacco_keywords": ["cigarro"],
            "restricted.whitelist": ["vinagre de vinho"]
        }
        
        assert service.is_restricted("Cerveja Pilsen") == True
        assert service.is_restricted("Suco de Uva") == False
        assert service.is_restricted("Vinagre de vinho") == False  # whitelist


# ==============================================================================
# TESTES: BACKUP SERVICE (Passo 65)
# ==============================================================================

class TestBackupService:
    """Testes para BackupService."""
    
    def test_validate_price_change_normal(self):
        """Testa validação de variação normal."""
        from src.core.services.backup_service import validate_price_change
        
        result = validate_price_change(10.0, 11.0)
        assert result["valid"] == True
    
    def test_validate_price_change_suspicious(self):
        """Testa detecção de variação suspeita."""
        from src.core.services.backup_service import validate_price_change
        
        # Aumento de 100%
        result = validate_price_change(10.0, 20.0)
        assert result["valid"] == False
        assert "aumento" in result["warning"]
        
        # Redução de 80%
        result = validate_price_change(10.0, 2.0)
        assert result["valid"] == False
        assert "redução" in result["warning"]


# ==============================================================================
# TESTES: IMPORT SERVICE (Passo 44-47)
# ==============================================================================

class TestImportService:
    """Testes para ImportService."""
    
    def test_parse_price_valid(self):
        """Testa parsing de preços."""
        from src.core.services.import_service import _parse_price
        
        assert _parse_price("10,50") == Decimal("10.50")
        assert _parse_price("R$ 15,99") == Decimal("15.99")
        assert _parse_price(10.5) == Decimal("10.50")
    
    def test_parse_price_invalid(self):
        """Testa rejeição de preços inválidos."""
        from src.core.services.import_service import _parse_price
        
        assert _parse_price("abc") is None
        assert _parse_price(None) is None


# ==============================================================================
# TESTES: LIFECYCLE (Passo 13-15)
# ==============================================================================

class TestLifecycle:
    """Testes para módulo lifecycle."""
    
    def test_sanitize_filename(self):
        """Testa sanitização de nomes de arquivo."""
        from src.core.lifecycle import sanitize_filename
        
        assert sanitize_filename('arquivo<>normal') == 'arquivo__normal'
        assert sanitize_filename('   espaços   ') == 'espaços'
        assert sanitize_filename('') == 'sem_nome'
    
    def test_validate_path_security(self):
        """Testa validação de path traversal."""
        from src.core.lifecycle import validate_path_security
        from src.core.constants import SYSTEM_ROOT
        
        # Path dentro do sistema -> OK
        assert validate_path_security(SYSTEM_ROOT / "assets" / "test.png") == True
        
        # Path fora do sistema -> Bloqueado (se path existir)
        if Path("C:/Windows").exists():
            assert validate_path_security(Path("C:/Windows/System32")) == False


# ==============================================================================
# TESTES: INSTANCE LOCK (Passo 92)
# ==============================================================================

class TestInstanceLock:
    """Testes para mutex de instância única."""
    
    def test_get_running_pid_no_lock(self):
        """Testa retorno None quando não há lock."""
        from src.core.instance_lock import get_running_pid, LOCK_FILE
        
        # Remove lock se existir
        if LOCK_FILE.exists():
            LOCK_FILE.unlink()
        
        assert get_running_pid() is None


# ==============================================================================
# RUNNER
# ==============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])

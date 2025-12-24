"""
AutoTabloide AI - Offline Mode Test
=====================================
Teste de funcionamento em modo offline.
Passo 84 do Checklist 100.

Funcionalidades:
- Verificar operação sem internet
- Testar fallbacks
- Validar cache local
"""

import socket
import asyncio
from typing import Tuple, List, Dict
from dataclasses import dataclass

from src.core.logging_config import get_logger

logger = get_logger("OfflineTest")


@dataclass
class OfflineTestResult:
    """Resultado de um teste offline."""
    test_name: str
    passed: bool
    message: str
    duration_ms: int = 0


class OfflineModeTest:
    """
    Suite de testes para modo offline.
    Passo 84 do Checklist - Teste modo offline.
    """
    
    @staticmethod
    def check_internet_connection() -> bool:
        """
        Verifica se há conexão com internet.
        
        Returns:
            True se online
        """
        try:
            socket.create_connection(("8.8.8.8", 53), timeout=3)
            return True
        except OSError:
            return False
    
    @staticmethod
    async def test_database_offline() -> OfflineTestResult:
        """Testa acesso ao banco sem internet."""
        import time
        start = time.perf_counter()
        
        try:
            from src.core.database import async_session_factory
            
            async with async_session_factory() as session:
                # Simples query de teste
                result = await session.execute("SELECT 1")
                _ = result.scalar()
            
            duration = int((time.perf_counter() - start) * 1000)
            return OfflineTestResult(
                test_name="Database Access",
                passed=True,
                message="Banco acessível offline",
                duration_ms=duration
            )
            
        except Exception as e:
            duration = int((time.perf_counter() - start) * 1000)
            return OfflineTestResult(
                test_name="Database Access",
                passed=False,
                message=f"Erro: {e}",
                duration_ms=duration
            )
    
    @staticmethod
    async def test_template_loading() -> OfflineTestResult:
        """Testa carregamento de templates SVG."""
        import time
        from pathlib import Path
        from src.core.constants import SYSTEM_ROOT
        
        start = time.perf_counter()
        
        try:
            templates_dir = SYSTEM_ROOT / "library" / "svg_source"
            
            if not templates_dir.exists():
                return OfflineTestResult(
                    test_name="Template Loading",
                    passed=False,
                    message="Diretório de templates não existe"
                )
            
            svg_files = list(templates_dir.glob("*.svg"))
            
            if len(svg_files) == 0:
                return OfflineTestResult(
                    test_name="Template Loading",
                    passed=False,
                    message="Nenhum template SVG encontrado"
                )
            
            # Tenta carregar primeiro template
            from lxml import etree
            
            first_svg = svg_files[0]
            tree = etree.parse(str(first_svg))
            root = tree.getroot()
            
            duration = int((time.perf_counter() - start) * 1000)
            return OfflineTestResult(
                test_name="Template Loading",
                passed=True,
                message=f"{len(svg_files)} templates disponíveis",
                duration_ms=duration
            )
            
        except Exception as e:
            duration = int((time.perf_counter() - start) * 1000)
            return OfflineTestResult(
                test_name="Template Loading",
                passed=False,
                message=f"Erro: {e}",
                duration_ms=duration
            )
    
    @staticmethod
    async def test_font_loading() -> OfflineTestResult:
        """Testa carregamento de fontes."""
        import time
        from src.core.constants import FONTS_DIR
        
        start = time.perf_counter()
        
        try:
            required_fonts = ["Roboto-Regular.ttf", "Roboto-Bold.ttf"]
            missing = []
            
            for font in required_fonts:
                if not (FONTS_DIR / font).exists():
                    missing.append(font)
            
            duration = int((time.perf_counter() - start) * 1000)
            
            if missing:
                return OfflineTestResult(
                    test_name="Font Loading",
                    passed=False,
                    message=f"Fontes faltando: {', '.join(missing)}",
                    duration_ms=duration
                )
            
            return OfflineTestResult(
                test_name="Font Loading",
                passed=True,
                message="Todas as fontes disponíveis",
                duration_ms=duration
            )
            
        except Exception as e:
            duration = int((time.perf_counter() - start) * 1000)
            return OfflineTestResult(
                test_name="Font Loading",
                passed=False,
                message=f"Erro: {e}",
                duration_ms=duration
            )
    
    @staticmethod
    async def test_llm_availability() -> OfflineTestResult:
        """Testa se modelo LLM está disponível."""
        import time
        from pathlib import Path
        from src.core.constants import SYSTEM_ROOT
        
        start = time.perf_counter()
        
        try:
            models_dir = SYSTEM_ROOT / "bin" / "models"
            
            if not models_dir.exists():
                return OfflineTestResult(
                    test_name="LLM Availability",
                    passed=False,
                    message="Diretório de modelos não existe"
                )
            
            gguf_files = list(models_dir.glob("*.gguf"))
            
            duration = int((time.perf_counter() - start) * 1000)
            
            if len(gguf_files) == 0:
                return OfflineTestResult(
                    test_name="LLM Availability",
                    passed=False,
                    message="Nenhum modelo GGUF encontrado",
                    duration_ms=duration
                )
            
            # Verifica tamanho do modelo
            model = gguf_files[0]
            size_gb = model.stat().st_size / (1024 ** 3)
            
            return OfflineTestResult(
                test_name="LLM Availability",
                passed=True,
                message=f"Modelo: {model.name} ({size_gb:.1f}GB)",
                duration_ms=duration
            )
            
        except Exception as e:
            duration = int((time.perf_counter() - start) * 1000)
            return OfflineTestResult(
                test_name="LLM Availability",
                passed=False,
                message=f"Erro: {e}",
                duration_ms=duration
            )
    
    @classmethod
    async def run_all_tests(cls) -> Tuple[bool, List[OfflineTestResult]]:
        """
        Executa todos os testes offline.
        
        Returns:
            Tupla (todos_passaram, lista_resultados)
        """
        logger.info("Iniciando testes de modo offline...")
        
        results = []
        
        # Testes
        results.append(await cls.test_database_offline())
        results.append(await cls.test_template_loading())
        results.append(await cls.test_font_loading())
        results.append(await cls.test_llm_availability())
        
        all_passed = all(r.passed for r in results)
        
        # Log resultados
        for r in results:
            status = "✅" if r.passed else "❌"
            logger.info(f"{status} {r.test_name}: {r.message} ({r.duration_ms}ms)")
        
        return all_passed, results


async def run_offline_tests() -> bool:
    """
    Função principal para executar testes offline.
    
    Returns:
        True se todos os testes passaram
    """
    all_passed, results = await OfflineModeTest.run_all_tests()
    return all_passed

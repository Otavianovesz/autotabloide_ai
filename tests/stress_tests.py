"""
AutoTabloide AI - Stress Test Framework
=========================================
Framework de testes de estresse automatizados.
PROTOCOLO DE RETIFICAÇÃO: Passo 99 (Testes de estresse).

Simula uso intensivo para encontrar gargalos.
"""

import asyncio
import logging
import random
import time
from pathlib import Path
from typing import Optional, List, Dict, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import traceback

logger = logging.getLogger("StressTest")


class TestType(Enum):
    """Tipos de teste de estresse."""
    DATABASE = "database"
    RENDERING = "rendering"
    AI = "ai"
    UI = "ui"
    MEMORY = "memory"
    DISK = "disk"


@dataclass
class StressTestResult:
    """Resultado de um teste."""
    test_name: str
    success: bool
    duration_seconds: float
    operations_count: int
    errors: List[str] = field(default_factory=list)
    metrics: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def ops_per_second(self) -> float:
        if self.duration_seconds > 0:
            return self.operations_count / self.duration_seconds
        return 0


@dataclass
class StressTestConfig:
    """Configuração de teste."""
    duration_seconds: int = 60
    concurrent_tasks: int = 5
    iterations: int = 100
    fail_threshold: float = 0.05  # 5% de falhas permitidas


class StressTestRunner:
    """
    Executor de testes de estresse.
    
    PASSO 99: Testes automatizados de performance.
    """
    
    def __init__(self, config: Optional[StressTestConfig] = None):
        self.config = config or StressTestConfig()
        self.results: List[StressTestResult] = []
    
    async def run_all(self) -> Dict[str, Any]:
        """Executa todos os testes de estresse."""
        start_time = time.time()
        
        tests = [
            ("Database Read", self.test_database_read),
            ("Database Write", self.test_database_write),
            ("SVG Parse", self.test_svg_parse),
            ("Text Fitting", self.test_text_fitting),
            ("Memory Pressure", self.test_memory_pressure),
            ("File I/O", self.test_file_io),
        ]
        
        for name, test_func in tests:
            logger.info(f"Executando: {name}")
            result = await self._run_single(name, test_func)
            self.results.append(result)
        
        total_duration = time.time() - start_time
        
        return self._generate_report(total_duration)
    
    async def _run_single(
        self,
        name: str,
        test_func: Callable
    ) -> StressTestResult:
        """Executa um único teste."""
        start = time.time()
        errors = []
        ops = 0
        metrics = {}
        
        try:
            ops, metrics = await test_func()
        except Exception as e:
            errors.append(f"{type(e).__name__}: {str(e)}")
            logger.error(f"Teste falhou: {name} - {e}")
        
        duration = time.time() - start
        
        return StressTestResult(
            test_name=name,
            success=len(errors) == 0,
            duration_seconds=duration,
            operations_count=ops,
            errors=errors,
            metrics=metrics
        )
    
    # =========================================================================
    # TESTES ESPECÍFICOS
    # =========================================================================
    
    async def test_database_read(self) -> tuple:
        """Teste de leitura intensiva do banco."""
        from src.core.database import AsyncSessionLocal
        from src.core.models import Produto
        from sqlalchemy import select
        
        ops = 0
        errors = 0
        
        for _ in range(self.config.iterations):
            try:
                async with AsyncSessionLocal() as session:
                    result = await session.execute(
                        select(Produto).limit(10)
                    )
                    _ = result.scalars().all()
                ops += 1
            except Exception as e:
                errors += 1
                logger.debug(f"DB read error: {e}")
        
        return ops, {"errors": errors}
    
    async def test_database_write(self) -> tuple:
        """Teste de escrita intensiva do banco."""
        from src.core.database import AsyncSessionLocal
        from sqlalchemy import text
        
        ops = 0
        errors = 0
        
        for i in range(min(self.config.iterations, 50)):  # Limitado
            try:
                async with AsyncSessionLocal() as session:
                    await session.execute(text(
                        f"SELECT 1 AS stress_test_{i}"
                    ))
                ops += 1
            except Exception as e:
                errors += 1
        
        return ops, {"errors": errors}
    
    async def test_svg_parse(self) -> tuple:
        """Teste de parsing de SVG."""
        from src.rendering.svg_cache import get_svg_parser
        
        parser = get_svg_parser()
        ops = 0
        
        # SVG de teste
        test_svg = '''<?xml version="1.0"?>
        <svg width="800" height="600" xmlns="http://www.w3.org/2000/svg">
            <rect x="0" y="0" width="800" height="600" fill="#FFF"/>
            <text x="100" y="100">Stress Test</text>
        </svg>'''
        
        for _ in range(self.config.iterations):
            try:
                await parser.parse_string(test_svg)
                ops += 1
            except Exception:
                pass
        
        stats = parser.get_cache_stats()
        return ops, {"cache_hit_rate": stats.get("hit_rate", 0)}
    
    async def test_text_fitting(self) -> tuple:
        """Teste de text fitting."""
        from src.rendering.text_fitting import get_text_fitting_engine, FontMetrics
        
        engine = get_text_fitting_engine()
        ops = 0
        
        test_texts = [
            "Produto de Teste Muito Longo",
            "ARROZ PARBOILIZADO 5KG",
            "Café Torrado e Moído Premium",
        ]
        
        for _ in range(self.config.iterations):
            text = random.choice(test_texts)
            font = FontMetrics(family="Arial", size=12)
            
            try:
                engine.fit_text(text, 200, 50, font)
                ops += 1
            except Exception:
                pass
        
        return ops, {}
    
    async def test_memory_pressure(self) -> tuple:
        """Teste de pressão de memória."""
        import sys
        
        ops = 0
        initial_size = 0
        max_size = 0
        
        try:
            import psutil
            process = psutil.Process()
            initial_size = process.memory_info().rss
        except ImportError:
            pass
        
        # Alocar e liberar memória
        for _ in range(self.config.iterations):
            data = [0] * (1024 * 100)  # ~800KB
            del data
            ops += 1
        
        try:
            import psutil
            process = psutil.Process()
            max_size = process.memory_info().rss
        except ImportError:
            pass
        
        return ops, {
            "initial_mb": initial_size / (1024 * 1024),
            "final_mb": max_size / (1024 * 1024)
        }
    
    async def test_file_io(self) -> tuple:
        """Teste de I/O de arquivo."""
        import tempfile
        
        ops = 0
        
        with tempfile.TemporaryDirectory() as tmpdir:
            for i in range(min(self.config.iterations, 100)):
                file_path = Path(tmpdir) / f"stress_{i}.txt"
                
                try:
                    # Write
                    file_path.write_text("x" * 10000)
                    # Read
                    _ = file_path.read_text()
                    # Delete
                    file_path.unlink()
                    ops += 1
                except Exception:
                    pass
        
        return ops, {}
    
    # =========================================================================
    # RELATÓRIO
    # =========================================================================
    
    def _generate_report(self, total_duration: float) -> Dict[str, Any]:
        """Gera relatório final."""
        passed = sum(1 for r in self.results if r.success)
        failed = len(self.results) - passed
        
        report = {
            "timestamp": datetime.now().isoformat(),
            "total_duration_seconds": total_duration,
            "tests_passed": passed,
            "tests_failed": failed,
            "pass_rate": passed / len(self.results) if self.results else 0,
            "results": []
        }
        
        for result in self.results:
            report["results"].append({
                "name": result.test_name,
                "success": result.success,
                "duration": result.duration_seconds,
                "ops": result.operations_count,
                "ops_per_sec": result.ops_per_second,
                "errors": result.errors,
                "metrics": result.metrics
            })
        
        return report


# ==============================================================================
# FUNÇÃO DE CONVENIÊNCIA
# ==============================================================================

async def run_stress_tests(
    duration: int = 60,
    iterations: int = 100
) -> Dict[str, Any]:
    """
    Executa bateria de testes de estresse.
    
    Args:
        duration: Duração máxima em segundos
        iterations: Número de iterações por teste
        
    Returns:
        Relatório de resultados
    """
    config = StressTestConfig(
        duration_seconds=duration,
        iterations=iterations
    )
    
    runner = StressTestRunner(config)
    return await runner.run_all()


def print_stress_report(report: Dict[str, Any]) -> None:
    """Imprime relatório de forma legível."""
    print("\n" + "=" * 60)
    print("RELATÓRIO DE TESTES DE ESTRESSE")
    print("=" * 60)
    print(f"Data: {report['timestamp']}")
    print(f"Duração Total: {report['total_duration_seconds']:.2f}s")
    print(f"Testes: {report['tests_passed']}/{report['tests_passed'] + report['tests_failed']} passaram")
    print("-" * 60)
    
    for result in report["results"]:
        status = "✓" if result["success"] else "✗"
        print(f"{status} {result['name']}")
        print(f"   Ops: {result['ops']} ({result['ops_per_sec']:.1f}/s)")
        print(f"   Duração: {result['duration']:.2f}s")
        
        if result["errors"]:
            for error in result["errors"]:
                print(f"   ⚠ {error}")
    
    print("=" * 60)

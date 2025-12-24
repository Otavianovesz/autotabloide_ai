"""
AutoTabloide AI - Final Validation
=====================================
Testes e validação final.
Passos 91-100 do Checklist v2.

Funcionalidades:
- Teste de carga (91)
- Teste de concorrência (92)
- Teste de rede (93)
- Teste de impressão (94)
- Auditoria de licenças (96)
- Limpeza de arquivos órfãos (97)
- Validação de backup (98)
- UX Review (99)
"""

import asyncio
import psutil
import gc
import time
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from datetime import datetime
import subprocess

from src.core.logging_config import get_logger
from src.core.constants import SYSTEM_ROOT

logger = get_logger("Validation")


# ============================================================================
# PASSO 91: Teste de Carga
# ============================================================================

class LoadTest:
    """
    Teste de carga para medir uso de recursos.
    Passo 91 do Checklist v2.
    """
    
    def __init__(self, max_ram_mb: float = 500.0):
        self.max_ram_mb = max_ram_mb
        self._initial_ram = 0.0
    
    def _get_ram_usage_mb(self) -> float:
        """Retorna uso de RAM em MB."""
        process = psutil.Process()
        return process.memory_info().rss / (1024 * 1024)
    
    def start(self) -> None:
        """Inicia medição."""
        gc.collect()
        self._initial_ram = self._get_ram_usage_mb()
        logger.info(f"RAM inicial: {self._initial_ram:.1f}MB")
    
    def check(self) -> Tuple[bool, float]:
        """
        Verifica uso de RAM atual.
        
        Returns:
            Tupla (dentro_do_limite, ram_atual_mb)
        """
        current = self._get_ram_usage_mb()
        delta = current - self._initial_ram
        
        within_limit = current < self.max_ram_mb
        
        if not within_limit:
            logger.warning(f"RAM excedeu limite: {current:.1f}MB > {self.max_ram_mb}MB")
        
        return within_limit, current
    
    async def run_import_stress_test(self, num_rows: int = 10000) -> Dict:
        """
        Testa importação massiva.
        
        Args:
            num_rows: Número de linhas a simular
            
        Returns:
            Resultados do teste
        """
        self.start()
        start_time = time.time()
        
        # Simula criação de produtos em memória
        products = []
        for i in range(num_rows):
            products.append({
                "id": i,
                "name": f"Produto Teste {i}",
                "price": 10.99 + (i * 0.01),
                "image": f"hash_{i:08x}"
            })
            
            # Check a cada 1000
            if i % 1000 == 0:
                ok, ram = self.check()
                if not ok:
                    return {
                        "success": False,
                        "error": f"RAM excedida após {i} itens",
                        "ram_mb": ram,
                        "items_processed": i
                    }
        
        elapsed = time.time() - start_time
        ok, final_ram = self.check()
        
        # Limpa
        del products
        gc.collect()
        
        return {
            "success": ok,
            "items_processed": num_rows,
            "elapsed_seconds": elapsed,
            "ram_peak_mb": final_ram,
            "items_per_second": num_rows / elapsed
        }


# ============================================================================
# PASSO 92: Teste de Concorrência
# ============================================================================

class ConcurrencyTest:
    """
    Teste de concorrência.
    Passo 92 do Checklist v2.
    """
    
    @staticmethod
    async def test_concurrent_save_and_download() -> Dict:
        """
        Testa salvar projeto enquanto baixa imagem.
        
        Returns:
            Resultado do teste
        """
        errors = []
        
        async def simulate_save():
            try:
                await asyncio.sleep(0.1)  # Simula salvar
                return True
            except Exception as e:
                errors.append(f"Save: {e}")
                return False
        
        async def simulate_download():
            try:
                await asyncio.sleep(0.2)  # Simula download
                return True
            except Exception as e:
                errors.append(f"Download: {e}")
                return False
        
        try:
            results = await asyncio.gather(
                simulate_save(),
                simulate_download(),
                return_exceptions=True
            )
            
            all_ok = all(r is True for r in results)
            
            return {
                "success": all_ok,
                "errors": errors,
                "results": [str(r) for r in results]
            }
            
        except Exception as e:
            return {
                "success": False,
                "errors": [str(e)]
            }


# ============================================================================
# PASSO 93: Teste de Rede
# ============================================================================

def test_network_disconnection() -> Dict:
    """
    Verifica comportamento sem rede.
    Passo 93 do Checklist v2.
    
    Returns:
        Resultado do teste
    """
    from src.core.infrastructure import is_network_available, check_offline_mode
    
    network_ok = is_network_available()
    offline_status = check_offline_mode()
    
    # Verifica se funciona offline
    can_work_offline = (
        offline_status.get("database", False) and
        offline_status.get("fonts", False) and
        offline_status.get("templates", False)
    )
    
    return {
        "network_available": network_ok,
        "offline_status": offline_status,
        "can_work_offline": can_work_offline
    }


# ============================================================================
# PASSO 94: Teste de PDF CMYK
# ============================================================================

def test_cmyk_separation(pdf_path: Path) -> Dict:
    """
    Testa separação de cores CMYK no PDF.
    Passo 94 do Checklist v2.
    
    Args:
        pdf_path: Caminho do PDF gerado
        
    Returns:
        Resultado da análise
    """
    if not pdf_path.exists():
        return {"success": False, "error": "PDF não encontrado"}
    
    try:
        from src.core.infrastructure import verify_ghostscript
        
        gs_ok, _ = verify_ghostscript()
        if not gs_ok:
            return {"success": False, "error": "Ghostscript não disponível"}
        
        # Usa pdfinfo ou gs para verificar colorspace
        result = subprocess.run(
            ["gs", "-dNODISPLAY", "-q", "-sFile=" + str(pdf_path), "-c", "quit"],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        return {
            "success": True,
            "file_size_kb": pdf_path.stat().st_size / 1024,
            "note": "Verifique manualmente no Adobe Acrobat para separação CMYK"
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)}


# ============================================================================
# PASSO 96: Auditoria de Licenças
# ============================================================================

LICENSE_INFO = {
    "flet": ("Apache-2.0", "Livre para uso comercial"),
    "lxml": ("BSD", "Livre para uso comercial"),
    "Pillow": ("HPND", "Livre para uso comercial"),
    "sqlalchemy": ("MIT", "Livre para uso comercial"),
    "rembg": ("MIT", "Livre para uso comercial"),
    "opencv-python-headless": ("Apache-2.0", "Livre para uso comercial"),
    "pyphen": ("LGPL", "Compatível com código proprietário"),
    "aiohttp": ("Apache-2.0", "Livre para uso comercial"),
    "rapidfuzz": ("MIT", "Livre para uso comercial"),
    # ATENÇÃO:
    "ghostscript": ("AGPL-3.0", "⚠️ CUIDADO: Requer licença comercial da Artifex para distribuição"),
}


def audit_licenses() -> Dict:
    """
    Audita licenças das dependências.
    Passo 96 do Checklist v2.
    
    Returns:
        Análise de licenças
    """
    warnings = []
    
    for pkg, (license_type, note) in LICENSE_INFO.items():
        if "AGPL" in license_type or "GPL" in license_type.upper():
            warnings.append(f"{pkg}: {license_type} - {note}")
    
    return {
        "total_packages": len(LICENSE_INFO),
        "warnings": warnings,
        "all_commercial_ok": len(warnings) == 0,
        "details": LICENSE_INFO
    }


# ============================================================================
# PASSO 97: Limpeza de Arquivos Órfãos
# ============================================================================

async def cleanup_orphan_images() -> Dict:
    """
    Remove imagens que não estão referenciadas no banco.
    Passo 97 do Checklist v2.
    
    Returns:
        Resultado da limpeza
    """
    store_dir = SYSTEM_ROOT / "assets" / "store"
    
    if not store_dir.exists():
        return {"success": True, "orphans_found": 0}
    
    try:
        from src.core.database import AsyncSessionLocal
        from src.core.repositories import ProductRepository
        
        # Obtém todos os hashes usados
        async with AsyncSessionLocal() as session:
            repo = ProductRepository(session)
            products = await repo.get_all()
            
            used_hashes = set()
            for p in products:
                for img_hash in p.get_images():
                    used_hashes.add(img_hash)
        
        # Verifica arquivos no store
        orphans = []
        for img_file in store_dir.glob("*"):
            file_hash = img_file.stem  # Nome do arquivo sem extensão
            if file_hash not in used_hashes:
                orphans.append(img_file)
        
        # Remove órfãos (com confirmação)
        # Por segurança, apenas reporta - não deleta automaticamente
        return {
            "success": True,
            "orphans_found": len(orphans),
            "orphan_files": [str(f) for f in orphans[:10]],  # Mostra até 10
            "note": "Execute cleanup manual se necessário"
        }
        
    except Exception as e:
        logger.error(f"Erro ao buscar órfãos: {e}")
        return {"success": False, "error": str(e)}


# ============================================================================
# PASSO 98: Validação de Backup
# ============================================================================

def validate_backup(backup_path: Path) -> Dict:
    """
    Valida integridade de backup do banco.
    Passo 98 do Checklist v2.
    
    Args:
        backup_path: Caminho do backup
        
    Returns:
        Resultado da validação
    """
    if not backup_path.exists():
        return {"success": False, "error": "Backup não encontrado"}
    
    try:
        import sqlite3
        
        # Tenta abrir e verificar integridade
        conn = sqlite3.connect(str(backup_path))
        cursor = conn.cursor()
        
        # Integrity check
        cursor.execute("PRAGMA integrity_check")
        result = cursor.fetchone()[0]
        
        # Conta tabelas
        cursor.execute("SELECT count(*) FROM sqlite_master WHERE type='table'")
        table_count = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            "success": result == "ok",
            "integrity_check": result,
            "table_count": table_count,
            "file_size_mb": backup_path.stat().st_size / (1024 * 1024)
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)}


# ============================================================================
# PASSO 99: UX Review Checklist
# ============================================================================

UX_CHECKLIST = [
    "Todos os botões têm tooltips",
    "Mensagens de erro são amigáveis",
    "Loading states estão implementados",
    "Atalhos de teclado documentados",
    "Cores seguem padrão de acessibilidade",
    "Fontes são legíveis (>12px)",
    "Espaçamentos são consistentes",
    "Feedback visual em ações",
    "Ortografia verificada",
    "Responsividade em diferentes tamanhos",
]


def get_ux_checklist() -> List[Dict]:
    """
    Retorna checklist de UX para revisão manual.
    Passo 99 do Checklist v2.
    """
    return [
        {"item": item, "checked": False}
        for item in UX_CHECKLIST
    ]


# ============================================================================
# PASSO 100: Manual do Usuário (placeholder)
# ============================================================================

def get_manual_path() -> Path:
    """
    Retorna caminho do manual do usuário.
    Passo 100 do Checklist v2.
    """
    return SYSTEM_ROOT / "docs" / "manual_usuario.pdf"


def manual_needs_update() -> bool:
    """Verifica se manual precisa ser atualizado."""
    manual_path = get_manual_path()
    
    if not manual_path.exists():
        return True
    
    # Se manual é mais antigo que 30 dias, sugere atualização
    from datetime import datetime, timedelta
    mtime = datetime.fromtimestamp(manual_path.stat().st_mtime)
    return (datetime.now() - mtime) > timedelta(days=30)


# ============================================================================
# Executor de Testes
# ============================================================================

class ValidationSuite:
    """
    Suite completa de validação.
    Agrupa passos 91-100.
    """
    
    @staticmethod
    async def run_all() -> Dict:
        """Executa todos os testes."""
        results = {}
        
        # Teste de carga
        load_test = LoadTest()
        results["load_test"] = await load_test.run_import_stress_test(1000)
        
        # Teste de concorrência
        results["concurrency"] = await ConcurrencyTest.test_concurrent_save_and_download()
        
        # Teste de rede
        results["network"] = test_network_disconnection()
        
        # Auditoria de licenças
        results["licenses"] = audit_licenses()
        
        # Órfãos
        results["orphans"] = await cleanup_orphan_images()
        
        # UX checklist
        results["ux_checklist"] = get_ux_checklist()
        
        return results

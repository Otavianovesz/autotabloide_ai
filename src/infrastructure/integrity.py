"""
AutoTabloide AI - Verificador de Integridade do Sistema
=========================================================
Bootloader estrito conforme auditoria de resiliência.
Protocolo 4: Verificação Hash de binários e assets críticos.
"""

import os
import hashlib
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger("IntegrityChecker")


class AssetStatus(str, Enum):
    """Status de verificação de asset."""
    OK = "OK"
    MISSING = "MISSING"
    CORRUPTED = "CORRUPTED"
    SIZE_MISMATCH = "SIZE_MISMATCH"


@dataclass
class AssetCheck:
    """Resultado de verificação de um asset."""
    path: str
    status: AssetStatus
    expected_hash: Optional[str] = None
    actual_hash: Optional[str] = None
    expected_size: Optional[int] = None
    actual_size: Optional[int] = None


class IntegrityChecker:
    """
    Verificador de Integridade do Sistema.
    
    PROTOCOLO BOOTLOADER ESTRITO:
    - Verifica existência de binários vitais
    - Valida integridade via hash MD5 (opcional, para assets críticos)
    - Detecta arquivos corrompidos (0 bytes)
    - Relatório completo de status
    """
    
    # Assets obrigatórios para funcionamento básico
    # Formato: (caminho relativo, hash esperado ou None, tamanho mínimo em bytes)
    REQUIRED_ASSETS = {
        # Binários vitais
        "bin/gswin64c.exe": (None, 1000),  # Ghostscript (hash varia por versão)
        
        # Perfis ICC para conversão CMYK
        "assets/profiles/CoatedFOGRA39.icc": (None, 500000),
        
        # Diretórios estruturais
        "database": (None, None),  # Diretório deve existir
        "vault/images": (None, None),
        "staging": (None, None),
    }
    
    # Assets opcionais (warning se ausentes)
    OPTIONAL_ASSETS = {
        "bin/realesrgan-ncnn-vulkan.exe": (None, 1000),
        "bin/Llama-3-8B-Instruct.Q4_K_M.gguf": (None, 1000000),
    }
    
    def __init__(self, system_root: Optional[str] = None):
        """
        Args:
            system_root: Raiz do sistema. Se None, auto-detecta.
        """
        if system_root:
            self.system_root = Path(system_root)
        else:
            # Auto-detecta
            self.system_root = Path(__file__).parent.parent.parent / "AutoTabloide_System_Root"
        
        self.check_results: List[AssetCheck] = []
        self.critical_failures: List[str] = []
        self.warnings: List[str] = []

    def run(self, strict_hash: bool = False) -> bool:
        """
        Executa verificação completa de integridade.
        
        Args:
            strict_hash: Se True, valida hashes MD5 (mais lento)
            
        Returns:
            True se todos os assets críticos estão OK
        """
        self.check_results = []
        self.critical_failures = []
        self.warnings = []
        
        logger.info(f"Verificação de integridade: {self.system_root}")
        
        # Verifica se o diretório raiz existe
        if not self.system_root.exists():
            self.critical_failures.append(
                f"CRITICO: Diretorio raiz nao existe: {self.system_root}"
            )
            return False
        
        # Verifica assets obrigatórios
        for rel_path, (expected_hash, min_size) in self.REQUIRED_ASSETS.items():
            check = self._check_asset(rel_path, expected_hash, min_size, strict_hash)
            self.check_results.append(check)
            
            if check.status != AssetStatus.OK:
                self.critical_failures.append(
                    f"CRITICO: {rel_path} -> {check.status.value}"
                )
        
        # Verifica assets opcionais
        for rel_path, (expected_hash, min_size) in self.OPTIONAL_ASSETS.items():
            check = self._check_asset(rel_path, expected_hash, min_size, strict_hash)
            self.check_results.append(check)
            
            if check.status != AssetStatus.OK:
                self.warnings.append(
                    f"AVISO: {rel_path} -> {check.status.value}"
                )
        
        # Log resultados
        self._log_results()
        
        # Retorna True apenas se não houver falhas críticas
        return len(self.critical_failures) == 0

    def _check_asset(
        self, 
        rel_path: str, 
        expected_hash: Optional[str],
        min_size: Optional[int],
        validate_hash: bool
    ) -> AssetCheck:
        """Verifica um asset individual."""
        full_path = self.system_root / rel_path
        
        # 1. Verifica existência
        if not full_path.exists():
            return AssetCheck(
                path=rel_path,
                status=AssetStatus.MISSING
            )
        
        # 2. Se for diretório, apenas verifica existência
        if full_path.is_dir():
            return AssetCheck(
                path=rel_path,
                status=AssetStatus.OK
            )
        
        # 3. Verifica tamanho
        actual_size = full_path.stat().st_size
        
        if actual_size == 0:
            return AssetCheck(
                path=rel_path,
                status=AssetStatus.CORRUPTED,
                actual_size=0
            )
        
        if min_size and actual_size < min_size:
            return AssetCheck(
                path=rel_path,
                status=AssetStatus.SIZE_MISMATCH,
                expected_size=min_size,
                actual_size=actual_size
            )
        
        # 4. Verifica hash se solicitado e esperado
        if validate_hash and expected_hash:
            actual_hash = self._calculate_md5(full_path)
            
            if actual_hash != expected_hash:
                return AssetCheck(
                    path=rel_path,
                    status=AssetStatus.CORRUPTED,
                    expected_hash=expected_hash,
                    actual_hash=actual_hash
                )
        
        return AssetCheck(
            path=rel_path,
            status=AssetStatus.OK,
            actual_size=actual_size
        )

    def _calculate_md5(self, file_path: Path) -> str:
        """Calcula hash MD5 de um arquivo."""
        hash_md5 = hashlib.md5()
        
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        
        return hash_md5.hexdigest()

    def _log_results(self):
        """Loga resultados da verificação."""
        ok_count = sum(1 for r in self.check_results if r.status == AssetStatus.OK)
        total = len(self.check_results)
        
        logger.info(f"Verificação: {ok_count}/{total} assets OK")
        
        for failure in self.critical_failures:
            logger.error(failure)
        
        for warning in self.warnings:
            logger.warning(warning)

    def get_report(self) -> Dict:
        """Retorna relatório estruturado."""
        return {
            "system_root": str(self.system_root),
            "total_checks": len(self.check_results),
            "passed": sum(1 for r in self.check_results if r.status == AssetStatus.OK),
            "failed": len(self.critical_failures),
            "warnings": len(self.warnings),
            "critical_failures": self.critical_failures,
            "warnings_list": self.warnings,
            "details": [
                {
                    "path": r.path,
                    "status": r.status.value,
                    "size": r.actual_size
                }
                for r in self.check_results
            ]
        }


def verify_system_integrity(system_root: Optional[str] = None, strict: bool = False) -> bool:
    """
    Função helper para verificação rápida.
    
    Args:
        system_root: Raiz do sistema
        strict: Se True, falha o processo se integridade falhar
        
    Returns:
        True se sistema íntegro
    """
    checker = IntegrityChecker(system_root)
    result = checker.run()
    
    if strict and not result:
        import sys
        print("\n[CRITICO] Falha na verificação de integridade do sistema:")
        for failure in checker.critical_failures:
            print(f"  - {failure}")
        print("\nO sistema não pode iniciar com segurança.")
        sys.exit(1)
    
    return result


def create_asset_snapshot(system_root: str, output_path: str) -> str:
    """
    Cria snapshot de hashes dos assets para verificação futura.
    
    Útil para distribuição: gera arquivo de referência dos hashes.
    """
    root = Path(system_root)
    hashes = {}
    
    for path in root.rglob("*"):
        if path.is_file():
            rel_path = str(path.relative_to(root))
            hash_md5 = hashlib.md5()
            
            with open(path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
            
            hashes[rel_path] = {
                "md5": hash_md5.hexdigest(),
                "size": path.stat().st_size
            }
    
    import json
    with open(output_path, "w") as f:
        json.dump(hashes, f, indent=2)
    
    return output_path

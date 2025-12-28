"""
AutoTabloide AI - Infrastructure Integrity
==========================================
PROTOCOLO DE CONVERGÊNCIA 260 - Fase 1 (Passos 1-10)
Validação de integridade do sistema no boot.
"""

from __future__ import annotations
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, field
import logging
import hashlib
import subprocess
import sys

logger = logging.getLogger("Integrity")


@dataclass
class IntegrityResult:
    """Resultado da verificação de integridade."""
    passed: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    binaries: Dict[str, bool] = field(default_factory=dict)
    fonts: List[str] = field(default_factory=list)
    profiles: List[str] = field(default_factory=list)


class IntegrityChecker:
    """
    Verificador de integridade industrial.
    
    Valida:
    - Permissões de escrita
    - Binários externos (Ghostscript)
    - Fontes obrigatórias
    - Perfis ICC
    - Schema do banco
    """
    
    def __init__(self, root_dir: Path = None):
        self.root = root_dir or Path("AutoTabloide_System_Root")
        self.result = IntegrityResult(passed=True)
    
    def check_all(self) -> IntegrityResult:
        """Executa todas as verificações."""
        logger.info("[Integrity] Iniciando verificação...")
        
        self._check_directories()
        self._check_write_permissions()
        self._check_binaries()
        self._check_fonts()
        self._check_icc_profiles()
        self._check_database()
        self._check_templates()
        
        if self.result.errors:
            self.result.passed = False
            logger.error(f"[Integrity] FALHA: {len(self.result.errors)} erros")
        else:
            logger.info("[Integrity] OK - Sistema íntegro")
        
        return self.result
    
    def _check_directories(self):
        """Verifica diretórios obrigatórios."""
        required_dirs = [
            "bin",
            "assets/fonts",
            "assets/profiles",
            "database",
            "library/svg_source",
            "projects",
            "exports",
            "temp_render",
            "logs",
        ]
        
        for dir_name in required_dirs:
            dir_path = self.root / dir_name
            if not dir_path.exists():
                try:
                    dir_path.mkdir(parents=True, exist_ok=True)
                    self.result.warnings.append(f"Diretório criado: {dir_name}")
                except Exception as e:
                    self.result.errors.append(f"Não foi possível criar: {dir_name}")
    
    def _check_write_permissions(self):
        """Testa permissões de escrita."""
        test_file = self.root / "temp_render" / ".write_test"
        
        try:
            test_file.write_text("test")
            test_file.unlink()
        except Exception as e:
            self.result.errors.append(f"Sem permissão de escrita: {e}")
    
    def _check_binaries(self):
        """Verifica binários externos."""
        binaries = {
            "ghostscript": ["gswin64c.exe", "gswin32c.exe", "gs"],
        }
        
        for name, options in binaries.items():
            found = False
            
            # Procura no bin/
            for opt in options:
                bin_path = self.root / "bin" / opt
                if bin_path.exists():
                    self.result.binaries[name] = True
                    found = True
                    break
            
            # Procura no PATH do sistema
            if not found:
                for opt in options:
                    if self._check_system_binary(opt):
                        self.result.binaries[name] = True
                        self.result.warnings.append(f"{name}: usando instalação do sistema")
                        found = True
                        break
            
            if not found:
                self.result.binaries[name] = False
                self.result.warnings.append(f"{name} não encontrado - exportação PDF limitada")
    
    def _check_system_binary(self, name: str) -> bool:
        """Verifica se binário está no PATH."""
        try:
            result = subprocess.run(
                [name, "--version"],
                capture_output=True,
                timeout=5
            )
            return result.returncode == 0
        except:
            return False
    
    def _check_fonts(self):
        """Verifica fontes obrigatórias."""
        fonts_dir = self.root / "assets" / "fonts"
        required_fonts = ["Roboto-Regular.ttf", "Roboto-Bold.ttf"]
        
        for font in required_fonts:
            font_path = fonts_dir / font
            if font_path.exists():
                self.result.fonts.append(font)
            else:
                self.result.warnings.append(f"Fonte ausente: {font}")
    
    def _check_icc_profiles(self):
        """Verifica perfis de cor."""
        profiles_dir = self.root / "assets" / "profiles"
        required_profiles = ["CoatedFOGRA39.icc"]
        
        for profile in required_profiles:
            profile_path = profiles_dir / profile
            if profile_path.exists():
                self.result.profiles.append(profile)
            else:
                self.result.warnings.append(f"Perfil ICC ausente: {profile} - CMYK desabilitado")
    
    def _check_database(self):
        """Verifica integridade do banco."""
        db_path = self.root / "database" / "core.db"
        
        if not db_path.exists():
            self.result.warnings.append("Banco não existe - será criado no boot")
            return
        
        # Verifica tamanho
        size = db_path.stat().st_size
        if size == 0:
            self.result.errors.append("Banco corrompido (0 bytes)")
    
    def _check_templates(self):
        """Verifica templates SVG."""
        templates_dir = self.root / "library" / "svg_source"
        
        svg_files = list(templates_dir.glob("*.svg"))
        
        if not svg_files:
            self.result.errors.append("Nenhum template SVG encontrado!")
            return
        
        for svg_path in svg_files:
            try:
                content = svg_path.read_text(encoding="utf-8")
                
                # Verifica IDs obrigatórios
                if "SLOT_01" not in content:
                    self.result.warnings.append(f"{svg_path.name}: faltando SLOT_01")
                
            except Exception as e:
                self.result.errors.append(f"Template inválido: {svg_path.name}")


# =============================================================================
# LOCK DE INSTÂNCIA
# =============================================================================

class InstanceLock:
    """
    Lock de instância única.
    Impede múltiplas instâncias do app.
    """
    
    def __init__(self, lock_name: str = "AutoTabloideAI"):
        self._lock_name = lock_name
        self._lock_file: Optional[Path] = None
        self._locked = False
    
    def acquire(self) -> bool:
        """Tenta adquirir o lock."""
        import tempfile
        
        self._lock_file = Path(tempfile.gettempdir()) / f"{self._lock_name}.lock"
        
        if self._lock_file.exists():
            # Verifica se processo ainda está vivo
            try:
                pid = int(self._lock_file.read_text())
                if self._is_process_alive(pid):
                    return False
            except:
                pass
        
        # Cria novo lock
        self._lock_file.write_text(str(sys.executable))
        self._locked = True
        return True
    
    def release(self):
        """Libera o lock."""
        if self._locked and self._lock_file:
            try:
                self._lock_file.unlink()
            except:
                pass
            self._locked = False
    
    def _is_process_alive(self, pid: int) -> bool:
        """Verifica se processo está vivo."""
        try:
            import psutil
            return psutil.pid_exists(pid)
        except ImportError:
            # Fallback sem psutil
            return False
    
    def __enter__(self):
        if not self.acquire():
            raise RuntimeError("Outra instância do AutoTabloide já está rodando!")
        return self
    
    def __exit__(self, *args):
        self.release()


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def run_integrity_check() -> IntegrityResult:
    """Executa verificação de integridade."""
    return IntegrityChecker().check_all()


def validate_ghostscript() -> Tuple[bool, str]:
    """Valida instalação do Ghostscript."""
    checker = IntegrityChecker()
    checker._check_binaries()
    
    if checker.result.binaries.get("ghostscript"):
        return True, "Ghostscript OK"
    return False, "Ghostscript não encontrado"


def clean_temp_folder():
    """Limpa pasta temporária (Clean Boot)."""
    import shutil
    
    temp_dir = Path("AutoTabloide_System_Root/temp_render")
    if temp_dir.exists():
        shutil.rmtree(temp_dir, ignore_errors=True)
    temp_dir.mkdir(parents=True, exist_ok=True)

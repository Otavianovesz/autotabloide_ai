"""
AutoTabloide AI - File System Service (The Vault)
=================================================
Phase 0.1: Service Layer
Phase 2.1: Content-Addressable Storage (CAS)

Gerencia arquivos de assets usando hash SHA-256.
Garante que arquivos nunca são sobrescritos, apenas deduplicados.
"""

import hashlib
import shutil
from pathlib import Path
from typing import Tuple, Optional
from src.core.services.base import BaseService

SYSTEM_ROOT = Path("AutoTabloide_System_Root").resolve()
ASSETS_STORE = SYSTEM_ROOT / "assets" / "store"

class FileSystemService(BaseService):
    """
    Gerencia armazenamento seguro de arquivos (CAS).
    """
    
    def __init__(self):
        super().__init__()
        self._ensure_directories()
        
    def _ensure_directories(self):
        ASSETS_STORE.mkdir(parents=True, exist_ok=True)
        
    def calculate_hash(self, file_path: Path) -> str:
        """Calcula SHA-256 do arquivo (streaming para memória baixa)."""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            # Ler em chunks de 64k
            for byte_block in iter(lambda: f.read(65536), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
        
    def import_asset(self, source_path: str) -> Tuple[str, str, bool]:
        """
        Importa arquivo para o Vault.
        Retorna (hash, relative_path, is_new).
        
        Se o arquivo já existe (mesmo hash), retorna o existente.
        """
        path = Path(source_path)
        if not path.exists():
            raise FileNotFoundError(f"Arquivo não encontrado: {source_path}")
            
        file_hash = self.calculate_hash(path)
        extension = path.suffix.lower()
        target_name = f"{file_hash}{extension}"
        target_path = ASSETS_STORE / target_name
        
        relative_path = f"assets/store/{target_name}"
        
        if target_path.exists():
            # Deduplicação: verifica se arquivo existente está integro
            if self.verify_file_integrity(target_path, file_hash):
                return file_hash, relative_path, False
            else:
                self.log_error("Integrity Warning", f"Arquivo corrompido detectado e sobrescrito: {target_name}")

        try:
            # Escrita atômica: copia para temp depois renomeia
            temp_path = target_path.with_suffix(".tmp")
            shutil.copy2(path, temp_path)
            
            # Verificação pós-escrita
            written_hash = self.calculate_hash(temp_path)
            if written_hash != file_hash:
                try:
                    temp_path.unlink()
                except:
                    pass
                raise ValueError(f"Hash mismatch: esperado {file_hash}, obtido {written_hash}")
                
            # Move atômico
            temp_path.replace(target_path)
            
            return file_hash, relative_path, True
            
        except Exception as e:
            self.log_error("Erro de IO", f"Falha ao copiar asset: {e}")
            if 'temp_path' in locals() and temp_path.exists():
                try:
                    temp_path.unlink()
                except:
                    pass
            raise

    def verify_file_integrity(self, file_path: Path, expected_hash: str) -> bool:
        """Verifica se arquivo corresponde ao hash esperado."""
        try:
            actual_hash = self.calculate_hash(file_path)
            return actual_hash == expected_hash
        except Exception:
            return False

    def verify_store(self) -> dict:
        """
        Verifica integridade de todo o store.
        Retorna relatório de arquivos corrompidos ou órfãos.
        """
        report = {"total": 0, "corrupted": [], "verified": 0}
        
        if not ASSETS_STORE.exists():
            return report
            
        for file_path in ASSETS_STORE.iterdir():
            if not file_path.is_file():
                continue
                
            report["total"] += 1
            
            # Nome do arquivo deve ser o hash (ignorando extensão)
            expected_hash = file_path.stem
            
            # Validação simples de nome (hex 64 chars)
            if len(expected_hash) != 64:
                # Arquivo com nome fora do padrão CAS
                continue
                
            if self.verify_file_integrity(file_path, expected_hash):
                report["verified"] += 1
            else:
                report["corrupted"].append(str(file_path.name))
                
        return report

    def get_absolute_path(self, relative_path: str) -> Path:
        """Resolve caminho relativo para absoluto."""
        # Remove prefixo se houver barras iniciais
        clean = relative_path.lstrip("/\\")
        return SYSTEM_ROOT / clean

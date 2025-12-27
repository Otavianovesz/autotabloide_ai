"""
AutoTabloide AI - Asset Manifest System
=========================================
Sistema de backup e verificação de manifest de assets.
PROTOCOLO DE RETIFICAÇÃO: Passos 9, 11, 13.

- Passo 9: Backup manifest.txt para hashes de imagens
- Passo 11: Verificação de poetry.lock
- Passo 13: Estrutura updates/
"""

import logging
import hashlib
import json
from pathlib import Path
from typing import Optional, Dict, List, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime

logger = logging.getLogger("AssetManifest")


# ==============================================================================
# PASSO 9: BACKUP MANIFEST.TXT PARA HASHES
# ==============================================================================

@dataclass
class AssetEntry:
    """Entrada no manifest de assets."""
    path: str
    hash: str
    size: int
    modified: str


class AssetManifestManager:
    """
    Gerencia manifest de assets (imagens, fontes, etc).
    
    PASSO 9: Detecta alterações/corrupções em assets críticos.
    """
    
    MANIFEST_FILENAME = "manifest.json"
    
    def __init__(self, assets_dir: Path):
        self.assets_dir = assets_dir
        self.manifest_path = assets_dir / self.MANIFEST_FILENAME
    
    def generate_manifest(
        self,
        extensions: Tuple[str, ...] = (".png", ".jpg", ".jpeg", ".svg", ".ttf", ".otf")
    ) -> Dict[str, AssetEntry]:
        """
        Gera manifest de todos os assets.
        
        Args:
            extensions: Extensões a incluir
            
        Returns:
            Dict de caminho relativo -> AssetEntry
        """
        manifest = {}
        
        for file_path in self.assets_dir.rglob("*"):
            if file_path.is_file() and file_path.suffix.lower() in extensions:
                rel_path = str(file_path.relative_to(self.assets_dir))
                
                # Calcular hash
                file_hash = self._compute_hash(file_path)
                
                manifest[rel_path] = AssetEntry(
                    path=rel_path,
                    hash=file_hash,
                    size=file_path.stat().st_size,
                    modified=datetime.fromtimestamp(file_path.stat().st_mtime).isoformat()
                )
        
        return manifest
    
    def save_manifest(self, manifest: Dict[str, AssetEntry]) -> bool:
        """Salva manifest em arquivo."""
        try:
            data = {
                "generated_at": datetime.now().isoformat(),
                "assets_count": len(manifest),
                "assets": {k: vars(v) for k, v in manifest.items()}
            }
            
            with open(self.manifest_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Manifest salvo: {len(manifest)} assets")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao salvar manifest: {e}")
            return False
    
    def load_manifest(self) -> Optional[Dict[str, AssetEntry]]:
        """Carrega manifest existente."""
        if not self.manifest_path.exists():
            return None
        
        try:
            with open(self.manifest_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            manifest = {}
            for path, entry_data in data.get("assets", {}).items():
                manifest[path] = AssetEntry(**entry_data)
            
            return manifest
            
        except Exception as e:
            logger.error(f"Erro ao carregar manifest: {e}")
            return None
    
    def verify_assets(self) -> Dict[str, Any]:
        """
        Verifica integridade dos assets contra manifest.
        
        Returns:
            Dict com resultado da verificação
        """
        saved = self.load_manifest()
        if saved is None:
            return {"status": "no_manifest", "message": "Manifest não existe"}
        
        current = self.generate_manifest()
        
        missing = []
        modified = []
        new_files = []
        
        # Verificar arquivos do manifest
        for path, entry in saved.items():
            if path not in current:
                missing.append(path)
            elif current[path].hash != entry.hash:
                modified.append(path)
        
        # Verificar novos arquivos
        for path in current:
            if path not in saved:
                new_files.append(path)
        
        is_ok = len(missing) == 0 and len(modified) == 0
        
        return {
            "status": "ok" if is_ok else "changed",
            "total": len(saved),
            "missing": missing,
            "modified": modified,
            "new": new_files,
            "is_valid": is_ok
        }
    
    def _compute_hash(self, file_path: Path) -> str:
        """Calcula hash MD5 de um arquivo."""
        hasher = hashlib.md5()
        
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b''):
                hasher.update(chunk)
        
        return hasher.hexdigest()


# ==============================================================================
# PASSO 11: VERIFICAÇÃO DE POETRY.LOCK
# ==============================================================================

class PoetryLockVerifier:
    """
    Verifica integridade do poetry.lock.
    
    PASSO 11: Detecta se dependências foram alteradas indevidamente.
    """
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.lock_path = project_root / "poetry.lock"
        self.pyproject_path = project_root / "pyproject.toml"
        self.hash_cache_path = project_root / ".poetry_lock_hash"
    
    def get_lock_hash(self) -> Optional[str]:
        """Calcula hash do poetry.lock."""
        if not self.lock_path.exists():
            return None
        
        hasher = hashlib.sha256()
        with open(self.lock_path, 'rb') as f:
            hasher.update(f.read())
        
        return hasher.hexdigest()
    
    def save_hash(self, hash_value: str) -> None:
        """Salva hash para comparação futura."""
        self.hash_cache_path.write_text(hash_value)
    
    def verify(self) -> Dict[str, Any]:
        """
        Verifica se poetry.lock está íntegro.
        
        Returns:
            Dict com status e detalhes
        """
        results = {
            "lock_exists": self.lock_path.exists(),
            "pyproject_exists": self.pyproject_path.exists(),
            "hash_matches": None,
            "message": ""
        }
        
        if not results["lock_exists"]:
            results["message"] = "poetry.lock não encontrado"
            return results
        
        current_hash = self.get_lock_hash()
        
        # Verificar contra hash salvo
        if self.hash_cache_path.exists():
            saved_hash = self.hash_cache_path.read_text().strip()
            results["hash_matches"] = current_hash == saved_hash
            
            if results["hash_matches"]:
                results["message"] = "poetry.lock inalterado"
            else:
                results["message"] = "poetry.lock foi modificado"
        else:
            # Primeiro run - salvar hash
            self.save_hash(current_hash)
            results["hash_matches"] = True
            results["message"] = "Hash inicial registrado"
        
        return results


# ==============================================================================
# PASSO 13: ESTRUTURA UPDATES/
# ==============================================================================

class UpdatesManager:
    """
    Gerencia estrutura de updates.
    
    PASSO 13: Prepara diretório para atualizações futuras.
    """
    
    UPDATES_STRUCTURE = {
        "pending": "Updates pendentes para aplicar",
        "applied": "Updates já aplicados (histórico)",
        "rollback": "Backups para rollback",
    }
    
    def __init__(self, system_root: Path):
        self.updates_dir = system_root / "updates"
    
    def ensure_structure(self) -> Dict[str, Path]:
        """Garante que estrutura updates/ existe."""
        created_dirs = {}
        
        # Criar diretório principal
        self.updates_dir.mkdir(parents=True, exist_ok=True)
        
        # Criar subdiretórios
        for subdir, description in self.UPDATES_STRUCTURE.items():
            path = self.updates_dir / subdir
            path.mkdir(exist_ok=True)
            
            # Criar README
            readme = path / "README.txt"
            if not readme.exists():
                readme.write_text(f"# {subdir.upper()}\n\n{description}\n")
            
            created_dirs[subdir] = path
        
        # Criar arquivo de versão
        version_file = self.updates_dir / "version.json"
        if not version_file.exists():
            version_data = {
                "current_version": "1.0.0",
                "last_update": None,
                "update_history": []
            }
            version_file.write_text(json.dumps(version_data, indent=2))
        
        logger.info("Estrutura updates/ configurada")
        return created_dirs
    
    def get_pending_updates(self) -> List[Dict[str, Any]]:
        """Retorna lista de updates pendentes."""
        pending_dir = self.updates_dir / "pending"
        updates = []
        
        for update_file in pending_dir.glob("*.json"):
            try:
                data = json.loads(update_file.read_text())
                data["file"] = update_file.name
                updates.append(data)
            except Exception:
                pass
        
        return sorted(updates, key=lambda x: x.get("version", "0.0.0"))
    
    def get_current_version(self) -> str:
        """Retorna versão atual."""
        version_file = self.updates_dir / "version.json"
        
        if version_file.exists():
            try:
                data = json.loads(version_file.read_text())
                return data.get("current_version", "1.0.0")
            except Exception:
                pass
        
        return "1.0.0"


# ==============================================================================
# INICIALIZAÇÃO
# ==============================================================================

def initialize_asset_systems(system_root: Path) -> Dict[str, Any]:
    """
    Inicializa todos os sistemas de assets.
    
    Args:
        system_root: Raiz do sistema
        
    Returns:
        Dict com status de cada sistema
    """
    results = {}
    
    # Manifest
    try:
        assets_dir = system_root / "assets" / "store"
        manifest_mgr = AssetManifestManager(assets_dir)
        
        # Verificar ou criar manifest
        if manifest_mgr.manifest_path.exists():
            verify_result = manifest_mgr.verify_assets()
            results["manifest"] = verify_result
        else:
            manifest = manifest_mgr.generate_manifest()
            manifest_mgr.save_manifest(manifest)
            results["manifest"] = {"status": "created", "count": len(manifest)}
    except Exception as e:
        results["manifest"] = {"status": "error", "message": str(e)}
    
    # Poetry.lock
    try:
        project_root = system_root.parent
        poetry_verifier = PoetryLockVerifier(project_root)
        results["poetry"] = poetry_verifier.verify()
    except Exception as e:
        results["poetry"] = {"status": "error", "message": str(e)}
    
    # Updates
    try:
        updates_mgr = UpdatesManager(system_root)
        updates_mgr.ensure_structure()
        results["updates"] = {
            "status": "ok",
            "version": updates_mgr.get_current_version(),
            "pending": len(updates_mgr.get_pending_updates())
        }
    except Exception as e:
        results["updates"] = {"status": "error", "message": str(e)}
    
    return results

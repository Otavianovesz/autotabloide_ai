"""
AutoTabloide AI - Project Template Versioning
================================================
Versionamento de templates em projetos salvos.
Passo 63 do Checklist 100.

Funcionalidades:
- Hash do template usado
- Versão do template
- Verificação de compatibilidade
"""

import hashlib
from pathlib import Path
from typing import Optional, Dict, Any, Tuple
from dataclasses import dataclass
from datetime import datetime

from src.core.logging_config import get_logger

logger = get_logger("TemplateVersion")


@dataclass
class TemplateVersion:
    """Informações de versão de um template."""
    template_path: str
    template_hash: str
    template_name: str
    created_at: datetime
    version: str = "1.0"


def calculate_template_hash(template_path: Path) -> str:
    """
    Calcula hash SHA256 de um template SVG.
    Passo 63 do Checklist - Versão do template no projeto salvo.
    
    Args:
        template_path: Caminho do arquivo SVG
        
    Returns:
        Hash SHA256 hexadecimal (primeiros 16 caracteres)
    """
    if not template_path.exists():
        return ""
    
    sha256 = hashlib.sha256()
    
    with open(template_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    
    return sha256.hexdigest()[:16]


def get_template_version(template_path: Path) -> TemplateVersion:
    """
    Obtém informações de versão de um template.
    
    Args:
        template_path: Caminho do template
        
    Returns:
        TemplateVersion com informações
    """
    return TemplateVersion(
        template_path=str(template_path),
        template_hash=calculate_template_hash(template_path),
        template_name=template_path.stem if template_path else "",
        created_at=datetime.now()
    )


def verify_template_compatibility(
    saved_hash: str,
    current_hash: str
) -> Tuple[bool, str]:
    """
    Verifica compatibilidade entre versões de template.
    
    Args:
        saved_hash: Hash salvo no projeto
        current_hash: Hash atual do template
        
    Returns:
        Tupla (compatível, mensagem)
    """
    if saved_hash == current_hash:
        return True, "Template inalterado"
    
    if not saved_hash:
        return False, "Projeto não tem hash de template salvo"
    
    if not current_hash:
        return False, "Template atual não encontrado"
    
    return False, "Template foi modificado desde a criação do projeto"


class ProjectTemplateMixin:
    """
    Mixin para adicionar suporte a versionamento de template.
    Adiciona campos template_hash e template_version ao projeto.
    """
    
    def set_template_info(self, template_path: Path) -> Dict[str, Any]:
        """
        Define informações do template no projeto.
        
        Args:
            template_path: Caminho do template
            
        Returns:
            Dict com informações do template
        """
        version = get_template_version(template_path)
        
        return {
            "template_path": version.template_path,
            "template_hash": version.template_hash,
            "template_name": version.template_name,
            "template_saved_at": version.created_at.isoformat()
        }
    
    def verify_template(
        self,
        saved_info: Dict[str, Any],
        current_template: Path
    ) -> Tuple[bool, str]:
        """
        Verifica se template ainda é compatível.
        
        Args:
            saved_info: Informações salvas
            current_template: Template atual
            
        Returns:
            Tupla (compatível, mensagem)
        """
        saved_hash = saved_info.get("template_hash", "")
        current_hash = calculate_template_hash(current_template)
        
        return verify_template_compatibility(saved_hash, current_hash)


def embed_template_version_in_project(
    project_data: Dict[str, Any],
    template_path: Path
) -> Dict[str, Any]:
    """
    Incorpora informações de template em dados de projeto.
    Passo 63 - Versão do template no projeto salvo.
    
    Args:
        project_data: Dados do projeto
        template_path: Caminho do template
        
    Returns:
        Dados atualizados com informações de template
    """
    version = get_template_version(template_path)
    
    project_data["_template"] = {
        "path": version.template_path,
        "hash": version.template_hash,
        "name": version.template_name,
        "saved_at": version.created_at.isoformat(),
        "version": version.version
    }
    
    logger.debug(f"Template versionado: {version.template_name} [{version.template_hash}]")
    
    return project_data

"""
AutoTabloide AI - Prompt Templates
====================================
Templates de prompt para LLM.
Passo 23 do Checklist v2.

Funcionalidades:
- Prompts externos configuráveis
- Não requer mudança de código para ajustar
"""

from pathlib import Path
from typing import Dict, Optional
import json

from src.core.logging_config import get_logger
from src.core.constants import SYSTEM_ROOT

logger = get_logger("PromptTemplates")

# Diretório de templates
TEMPLATES_DIR = SYSTEM_ROOT / "config" / "prompts"
TEMPLATES_DIR.mkdir(parents=True, exist_ok=True)


# Templates padrão
DEFAULT_TEMPLATES = {
    "sanitize_product": {
        "system": """Você é um assistente especializado em padronização de nomes de produtos para supermercados brasileiros.
Sua tarefa é receber um nome de produto "sujo" e retornar um JSON com os campos extraídos.""",
        
        "user": """Analise o seguinte nome de produto e extraia as informações:

PRODUTO: {raw_text}

Retorne APENAS um JSON válido no formato:
{{
    "nome_sanitizado": "Nome limpo e padronizado",
    "marca": "Marca se identificável ou null",
    "peso": "Peso/volume se presente ou null",
    "unidade": "un, kg, L, ml, g ou null",
    "categoria": "Categoria do produto ou null"
}}"""
    },
    
    "image_description": {
        "system": "Você é um assistente que descreve imagens de produtos.",
        "user": "Descreva esta imagem de produto em uma frase curta."
    },
    
    "price_validation": {
        "system": "Você valida preços de produtos.",
        "user": "O preço R$ {price} para {product} parece razoável? Responda SIM ou NÃO."
    }
}


class PromptTemplateManager:
    """
    Gerenciador de templates de prompt.
    Passo 23 do Checklist v2 - Prompts configuráveis.
    """
    
    def __init__(self, templates_dir: Optional[Path] = None):
        self.templates_dir = templates_dir or TEMPLATES_DIR
        self.templates_dir.mkdir(parents=True, exist_ok=True)
        self._cache: Dict[str, Dict] = {}
        
        # Inicializa templates padrão se não existirem
        self._ensure_defaults()
    
    def _ensure_defaults(self) -> None:
        """Cria arquivos de template padrão se não existirem."""
        for name, template in DEFAULT_TEMPLATES.items():
            template_file = self.templates_dir / f"{name}.json"
            if not template_file.exists():
                with open(template_file, 'w', encoding='utf-8') as f:
                    json.dump(template, f, ensure_ascii=False, indent=2)
                logger.debug(f"Template padrão criado: {name}")
    
    def get_template(self, name: str) -> Optional[Dict]:
        """
        Obtém template por nome.
        
        Args:
            name: Nome do template (ex: "sanitize_product")
            
        Returns:
            Dict com "system" e "user" prompts
        """
        # Cache hit
        if name in self._cache:
            return self._cache[name]
        
        # Tenta carregar do arquivo
        template_file = self.templates_dir / f"{name}.json"
        
        if template_file.exists():
            try:
                with open(template_file, 'r', encoding='utf-8') as f:
                    template = json.load(f)
                    self._cache[name] = template
                    return template
            except Exception as e:
                logger.error(f"Erro ao carregar template {name}: {e}")
        
        # Fallback para padrão
        if name in DEFAULT_TEMPLATES:
            return DEFAULT_TEMPLATES[name]
        
        return None
    
    def format_prompt(self, name: str, **kwargs) -> Optional[Dict[str, str]]:
        """
        Formata template com variáveis.
        
        Args:
            name: Nome do template
            **kwargs: Variáveis para substituição
            
        Returns:
            Dict com prompts formatados
        """
        template = self.get_template(name)
        if not template:
            return None
        
        try:
            return {
                "system": template.get("system", "").format(**kwargs),
                "user": template.get("user", "").format(**kwargs)
            }
        except KeyError as e:
            logger.error(f"Variável faltando no template {name}: {e}")
            return None
    
    def save_template(self, name: str, system: str, user: str) -> bool:
        """
        Salva ou atualiza template.
        
        Args:
            name: Nome do template
            system: Prompt de sistema
            user: Prompt de usuário
            
        Returns:
            True se sucesso
        """
        try:
            template = {"system": system, "user": user}
            template_file = self.templates_dir / f"{name}.json"
            
            with open(template_file, 'w', encoding='utf-8') as f:
                json.dump(template, f, ensure_ascii=False, indent=2)
            
            # Atualiza cache
            self._cache[name] = template
            logger.info(f"Template salvo: {name}")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao salvar template {name}: {e}")
            return False
    
    def list_templates(self) -> list:
        """Retorna lista de templates disponíveis."""
        templates = []
        
        for f in self.templates_dir.glob("*.json"):
            templates.append(f.stem)
        
        return sorted(templates)


# Singleton
_template_manager: Optional[PromptTemplateManager] = None


def get_template_manager() -> PromptTemplateManager:
    """Retorna instância singleton."""
    global _template_manager
    if _template_manager is None:
        _template_manager = PromptTemplateManager()
    return _template_manager


def get_sanitize_prompt(raw_text: str) -> Dict[str, str]:
    """
    Obtém prompt formatado para sanitização de produto.
    
    Args:
        raw_text: Texto bruto do produto
        
    Returns:
        Dict com system e user prompts
    """
    manager = get_template_manager()
    result = manager.format_prompt("sanitize_product", raw_text=raw_text)
    
    if not result:
        # Fallback hardcoded
        return {
            "system": DEFAULT_TEMPLATES["sanitize_product"]["system"],
            "user": DEFAULT_TEMPLATES["sanitize_product"]["user"].format(raw_text=raw_text)
        }
    
    return result

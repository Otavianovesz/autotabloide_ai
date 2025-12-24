"""
AutoTabloide AI - Settings Service
====================================
Serviço centralizado para leitura/escrita de configurações.
Passo 10-11 do Checklist 100.

Substitui hardcoding de caminhos e configurações espalhadas.
"""

import json
from typing import Any, Optional, Dict, List
from pathlib import Path
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.logging_config import get_logger
from src.core.models import SystemConfig
from src.core.database import AsyncSessionLocal

logger = get_logger("SettingsService")


# ==============================================================================
# CONFIGURAÇÕES PADRÃO DO SISTEMA
# ==============================================================================

DEFAULT_SETTINGS: Dict[str, Dict[str, Any]] = {
    # ===== CAMINHOS =====
    "llm.model_path": {
        "value": "bin/models/gemma-2b-it-q4_k_m.gguf",
        "type": "string",
        "category": "ai",
        "description": "Caminho relativo para o modelo LLM",
        "editable": True
    },
    "ghostscript.path": {
        "value": "bin/gs/gswin64c.exe",
        "type": "string",
        "category": "rendering",
        "description": "Caminho para executável do Ghostscript",
        "editable": True
    },
    
    # ===== IA =====
    "llm.temperature": {
        "value": 0.0,
        "type": "float",
        "category": "ai",
        "description": "Temperatura do LLM (0.0 = determinístico)",
        "editable": True
    },
    "llm.top_p": {
        "value": 0.1,
        "type": "float",
        "category": "ai",
        "description": "Top-P do LLM",
        "editable": True
    },
    "llm.n_gpu_layers": {
        "value": -1,
        "type": "int",
        "category": "ai",
        "description": "Camadas na GPU (-1 = todas)",
        "editable": True
    },
    
    # ===== RENDERIZAÇÃO =====
    "render.dpi_web": {
        "value": 150,
        "type": "int",
        "category": "rendering",
        "description": "DPI para exportação web/redes sociais",
        "editable": True
    },
    "render.dpi_print": {
        "value": 300,
        "type": "int",
        "category": "rendering",
        "description": "DPI para exportação gráfica",
        "editable": True
    },
    "render.convert_to_outlines": {
        "value": True,
        "type": "bool",
        "category": "rendering",
        "description": "Converter fontes em curvas no PDF final",
        "editable": True
    },
    
    # ===== PALAVRAS PROIBIDAS +18 =====
    "restricted.alcohol_keywords": {
        "value": ["cerveja", "vodka", "whisky", "vinho", "cachaça", "rum", "gin", "tequila", "champagne", "espumante"],
        "type": "list",
        "category": "compliance",
        "description": "Palavras que ativam ícone +18 (bebidas)",
        "editable": True
    },
    "restricted.tobacco_keywords": {
        "value": ["cigarro", "tabaco", "charuto", "fumo", "narguilé"],
        "type": "list",
        "category": "compliance",
        "description": "Palavras que ativam ícone +18 (tabaco)",
        "editable": True
    },
    "restricted.whitelist": {
        "value": ["vinho culinário", "vinagre de vinho", "molho de vinho"],
        "type": "list",
        "category": "compliance",
        "description": "Exceções que parecem +18 mas não são",
        "editable": True
    },
    
    # ===== BACKUP =====
    "backup.auto_interval_hours": {
        "value": 4,
        "type": "int",
        "category": "system",
        "description": "Intervalo de backup automático em horas",
        "editable": True
    },
    "backup.max_snapshots": {
        "value": 10,
        "type": "int",
        "category": "system",
        "description": "Número máximo de snapshots a manter",
        "editable": True
    },
    
    # ===== LOGS =====
    "logs.retention_days": {
        "value": 7,
        "type": "int",
        "category": "system",
        "description": "Dias para manter logs antigos",
        "editable": True
    },
    
    # ===== UI =====
    "ui.theme": {
        "value": "dark",
        "type": "string",
        "category": "ui",
        "description": "Tema da interface (dark/light)",
        "editable": True
    },
    "ui.sounds_enabled": {
        "value": True,
        "type": "bool",
        "category": "ui",
        "description": "Habilitar sons de feedback",
        "editable": True
    },
    
    # ===== HUNTER =====
    "hunter.rate_limit_per_minute": {
        "value": 30,
        "type": "int",
        "category": "ai",
        "description": "Limite de requisições por minuto",
        "editable": True
    },
    "hunter.min_image_size": {
        "value": 300,
        "type": "int",
        "category": "ai",
        "description": "Tamanho mínimo de imagem em pixels",
        "editable": True
    },
}


class SettingsService:
    """
    Serviço centralizado de configurações.
    Lê/escreve no banco SystemConfig com cache em memória.
    """
    
    _instance: Optional["SettingsService"] = None
    _cache: Dict[str, Any] = {}
    _initialized: bool = False
    
    def __new__(cls) -> "SettingsService":
        """Singleton pattern."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    async def initialize(self) -> None:
        """
        Inicializa o serviço, populando defaults e carregando cache.
        Deve ser chamado uma vez no startup da aplicação.
        """
        if self._initialized:
            return
        
        await self._seed_defaults()
        await self._load_cache()
        self._initialized = True
        logger.info("SettingsService inicializado com sucesso")
    
    async def _seed_defaults(self) -> None:
        """
        Popula o banco com configurações padrão se não existirem.
        """
        async with AsyncSessionLocal() as session:
            for key, config in DEFAULT_SETTINGS.items():
                # Verifica se já existe
                result = await session.execute(
                    select(SystemConfig).where(SystemConfig.key == key)
                )
                existing = result.scalar_one_or_none()
                
                if existing is None:
                    # Cria nova config
                    new_config = SystemConfig(
                        key=key,
                        value=json.dumps(config["value"], ensure_ascii=False),
                        value_type=config["type"],
                        category=config["category"],
                        description=config["description"],
                        editable=config["editable"]
                    )
                    session.add(new_config)
            
            await session.commit()
    
    async def _load_cache(self) -> None:
        """
        Carrega todas as configurações para cache em memória.
        """
        async with AsyncSessionLocal() as session:
            result = await session.execute(select(SystemConfig))
            configs = result.scalars().all()
            
            for config in configs:
                self._cache[config.key] = config.get_value()
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Obtém valor de configuração do cache.
        
        Args:
            key: Chave da configuração (ex: "llm.model_path")
            default: Valor padrão se não existir
            
        Returns:
            Valor da configuração
        """
        return self._cache.get(key, default)
    
    async def set(self, key: str, value: Any) -> None:
        """
        Define valor de configuração.
        Atualiza cache e persiste no banco.
        
        Args:
            key: Chave da configuração
            value: Novo valor
        """
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(SystemConfig).where(SystemConfig.key == key)
            )
            config = result.scalar_one_or_none()
            
            if config:
                config.set_value(value)
            else:
                # Cria nova config se não existir
                config = SystemConfig(
                    key=key,
                    value_type=type(value).__name__,
                    category="custom",
                    editable=True
                )
                config.set_value(value)
                session.add(config)
            
            await session.commit()
            
        # Atualiza cache
        self._cache[key] = value
        logger.debug(f"Configuração atualizada: {key} = {value}")
    
    async def get_by_category(self, category: str) -> Dict[str, Any]:
        """
        Obtém todas as configurações de uma categoria.
        
        Args:
            category: Nome da categoria (ex: "ai", "rendering")
            
        Returns:
            Dict com configurações da categoria
        """
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(SystemConfig).where(SystemConfig.category == category)
            )
            configs = result.scalars().all()
            
            return {c.key: c.get_value() for c in configs}
    
    async def reset_to_defaults(self, category: Optional[str] = None) -> None:
        """
        Reseta configurações para valores padrão.
        
        Args:
            category: Se especificado, reseta apenas essa categoria
        """
        async with AsyncSessionLocal() as session:
            for key, config in DEFAULT_SETTINGS.items():
                if category and config["category"] != category:
                    continue
                
                result = await session.execute(
                    select(SystemConfig).where(SystemConfig.key == key)
                )
                existing = result.scalar_one_or_none()
                
                if existing:
                    existing.set_value(config["value"])
            
            await session.commit()
        
        await self._load_cache()
        logger.info(f"Configurações resetadas para padrão: {category or 'todas'}")
    
    def get_restricted_keywords(self) -> List[str]:
        """
        Retorna lista combinada de palavras proibidas (+18).
        """
        alcohol = self.get("restricted.alcohol_keywords", [])
        tobacco = self.get("restricted.tobacco_keywords", [])
        return alcohol + tobacco
    
    def get_restricted_whitelist(self) -> List[str]:
        """
        Retorna lista de exceções.
        """
        return self.get("restricted.whitelist", [])
    
    def is_restricted(self, text: str) -> bool:
        """
        Verifica se texto contém palavras restritas.
        
        Args:
            text: Texto a verificar
            
        Returns:
            True se contém palavras +18
        """
        text_lower = text.lower()
        
        # Verifica whitelist primeiro
        for safe_phrase in self.get_restricted_whitelist():
            if safe_phrase.lower() in text_lower:
                return False
        
        # Verifica palavras proibidas
        for keyword in self.get_restricted_keywords():
            if keyword.lower() in text_lower:
                return True
        
        return False


# Singleton global
settings_service = SettingsService()


async def get_settings() -> SettingsService:
    """
    Retorna instância inicializada do SettingsService.
    Uso: settings = await get_settings()
    """
    if not settings_service._initialized:
        await settings_service.initialize()
    return settings_service

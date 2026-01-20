"""
AutoTabloide AI - App Settings (O "Cofre")
============================================
FASE 3: Configurações tipadas com Pydantic e armazenamento seguro.

Features:
- AppSettings: Schema Pydantic tipado com validação
- SecureStorage: Criptografia de API keys usando DPAPI (Windows)
- Safe loading: Fallback para defaults se JSON corrompido
"""

import os
import sys
import json
import base64
import logging
from pathlib import Path
from typing import Optional, List, Any
from pydantic import BaseModel, Field, validator, ValidationError

logger = logging.getLogger("AppSettings")


# ==============================================================================
# SECURE STORAGE (Criptografia de API Keys)
# ==============================================================================

class SecureStorage:
    """
    Armazena dados sensíveis (API keys) com criptografia.
    
    Windows: Usa DPAPI (win32crypt.CryptProtectData)
    Outros: Usa encoding Base64 + machine ID (fallback menos seguro)
    
    IMPORTANTE: A chave é derivada da máquina/usuário.
    API keys NÃO ficam em texto puro no config.
    """
    
    _entropy: bytes = b"AutoTabloideAI_2026_Cofre"  # Salt adicional
    
    @classmethod
    def _get_machine_key(cls) -> bytes:
        """Gera chave única baseada na máquina."""
        import hashlib
        
        # Combina identificadores únicos da máquina
        machine_id_parts = [
            os.environ.get("COMPUTERNAME", ""),
            os.environ.get("USERNAME", ""),
            str(Path.home()),
        ]
        
        combined = "|".join(machine_id_parts).encode("utf-8")
        return hashlib.sha256(combined + cls._entropy).digest()
    
    @classmethod
    def encrypt(cls, plaintext: str) -> str:
        """
        Criptografa texto sensível.
        
        Args:
            plaintext: Texto em claro (ex: API key)
            
        Returns:
            String Base64 do texto criptografado
        """
        if not plaintext:
            return ""
        
        if sys.platform == "win32":
            try:
                import win32crypt
                
                encrypted = win32crypt.CryptProtectData(
                    plaintext.encode("utf-8"),
                    "AutoTabloideAI",  # Description
                    cls._entropy,      # Entropy
                    None,              # Reserved
                    None,              # Prompt
                    0                  # Flags
                )
                return base64.b64encode(encrypted).decode("ascii")
                
            except ImportError:
                logger.warning("win32crypt não disponível, usando fallback")
            except Exception as e:
                logger.error(f"Erro ao criptografar com DPAPI: {e}")
        
        # Fallback: XOR com machine key (menos seguro, mas melhor que plaintext)
        return cls._fallback_encrypt(plaintext)
    
    @classmethod
    def decrypt(cls, ciphertext: str) -> str:
        """
        Descriptografa texto sensível.
        
        Args:
            ciphertext: String Base64 do texto criptografado
            
        Returns:
            Texto em claro original
        """
        if not ciphertext:
            return ""
        
        if sys.platform == "win32":
            try:
                import win32crypt
                
                encrypted = base64.b64decode(ciphertext)
                decrypted = win32crypt.CryptUnprotectData(
                    encrypted,
                    cls._entropy,
                    None,
                    None,
                    0
                )
                return decrypted[1].decode("utf-8")
                
            except ImportError:
                logger.warning("win32crypt não disponível, usando fallback")
            except Exception as e:
                logger.error(f"Erro ao descriptografar com DPAPI: {e}")
                return ""
        
        # Fallback: XOR com machine key
        return cls._fallback_decrypt(ciphertext)
    
    @classmethod
    def _fallback_encrypt(cls, plaintext: str) -> str:
        """Fallback de criptografia usando XOR com machine key."""
        key = cls._get_machine_key()
        plaintext_bytes = plaintext.encode("utf-8")
        
        encrypted = bytes([
            plaintext_bytes[i] ^ key[i % len(key)]
            for i in range(len(plaintext_bytes))
        ])
        
        # Prefixo para identificar fallback
        return "FB:" + base64.b64encode(encrypted).decode("ascii")
    
    @classmethod
    def _fallback_decrypt(cls, ciphertext: str) -> str:
        """Fallback de descriptografia usando XOR com machine key."""
        if not ciphertext.startswith("FB:"):
            return ""  # Formato inválido
        
        try:
            key = cls._get_machine_key()
            encrypted = base64.b64decode(ciphertext[3:])  # Remove "FB:"
            
            decrypted = bytes([
                encrypted[i] ^ key[i % len(key)]
                for i in range(len(encrypted))
            ])
            
            return decrypted.decode("utf-8")
        except Exception as e:
            logger.error(f"Erro no fallback decrypt: {e}")
            return ""
    
    @classmethod
    def is_encrypted(cls, value: str) -> bool:
        """Verifica se valor está criptografado."""
        if not value:
            return False
        # DPAPI produz Base64, fallback tem prefixo FB:
        return value.startswith("FB:") or (len(value) > 50 and value.replace("=", "").isalnum())


# ==============================================================================
# PYDANTIC SETTINGS SCHEMAS
# ==============================================================================

class AISettings(BaseModel):
    """Configurações de IA/LLM."""
    model_path: str = Field(
        default="bin/models/gemma-2b-it-q4_k_m.gguf",
        description="Caminho relativo para o modelo LLM"
    )
    temperature: float = Field(
        default=0.0,
        ge=0.0,
        le=2.0,
        description="Temperatura do LLM (0.0 = determinístico)"
    )
    top_p: float = Field(
        default=0.1,
        ge=0.0,
        le=1.0,
        description="Top-P sampling"
    )
    n_gpu_layers: int = Field(
        default=-1,
        ge=-1,
        description="Camadas na GPU (-1 = todas)"
    )
    # API key criptografada
    openai_api_key_encrypted: str = Field(
        default="",
        description="API key da OpenAI (criptografada)"
    )
    
    def set_openai_key(self, key: str) -> None:
        """Define API key da OpenAI com criptografia."""
        self.openai_api_key_encrypted = SecureStorage.encrypt(key)
    
    def get_openai_key(self) -> str:
        """Retorna API key da OpenAI descriptografada."""
        return SecureStorage.decrypt(self.openai_api_key_encrypted)


class RenderSettings(BaseModel):
    """Configurações de renderização."""
    dpi_web: int = Field(
        default=150,
        ge=72,
        le=600,
        description="DPI para exportação web/redes sociais"
    )
    dpi_print: int = Field(
        default=300,
        ge=150,
        le=1200,
        description="DPI para exportação gráfica"
    )
    convert_to_outlines: bool = Field(
        default=True,
        description="Converter fontes em curvas no PDF final"
    )
    ghostscript_path: str = Field(
        default="bin/gs/gswin64c.exe",
        description="Caminho para executável do Ghostscript"
    )


class ComplianceSettings(BaseModel):
    """Configurações de compliance (+18)."""
    alcohol_keywords: List[str] = Field(
        default=["cerveja", "vodka", "whisky", "vinho", "cachaça", "rum", "gin", "tequila", "champagne", "espumante"],
        description="Palavras que ativam ícone +18 (bebidas)"
    )
    tobacco_keywords: List[str] = Field(
        default=["cigarro", "tabaco", "charuto", "fumo", "narguilé"],
        description="Palavras que ativam ícone +18 (tabaco)"
    )
    whitelist: List[str] = Field(
        default=["vinho culinário", "vinagre de vinho", "molho de vinho"],
        description="Exceções que parecem +18 mas não são"
    )


class BackupSettings(BaseModel):
    """Configurações de backup."""
    auto_interval_hours: int = Field(
        default=4,
        ge=1,
        le=24,
        description="Intervalo de backup automático em horas"
    )
    max_snapshots: int = Field(
        default=10,
        ge=1,
        le=100,
        description="Número máximo de snapshots a manter"
    )


class UISettings(BaseModel):
    """Configurações de interface."""
    theme: str = Field(
        default="dark",
        pattern="^(dark|light)$",
        description="Tema da interface"
    )
    sounds_enabled: bool = Field(
        default=True,
        description="Habilitar sons de feedback"
    )


class HunterSettings(BaseModel):
    """Configurações do Hunter (web scraping)."""
    rate_limit_per_minute: int = Field(
        default=30,
        ge=1,
        le=100,
        description="Limite de requisições por minuto"
    )
    min_image_size: int = Field(
        default=300,
        ge=100,
        le=1000,
        description="Tamanho mínimo de imagem em pixels"
    )


class AppSettings(BaseModel):
    """
    Configurações principais da aplicação.
    
    FASE 3: Schema Pydantic tipado com validação automática.
    Carrega de settings.json com fallback seguro para defaults.
    """
    
    ai: AISettings = Field(default_factory=AISettings)
    render: RenderSettings = Field(default_factory=RenderSettings)
    compliance: ComplianceSettings = Field(default_factory=ComplianceSettings)
    backup: BackupSettings = Field(default_factory=BackupSettings)
    ui: UISettings = Field(default_factory=UISettings)
    hunter: HunterSettings = Field(default_factory=HunterSettings)
    
    class Config:
        validate_assignment = True  # Valida também em setters
        extra = "ignore"  # Ignora campos extras (compatibilidade)


# ==============================================================================
# SAFE LOADING
# ==============================================================================

def get_settings_path() -> Path:
    """Retorna caminho do arquivo settings.json."""
    base_dir = Path(__file__).parent.parent.parent.resolve()
    return base_dir / "AutoTabloide_System_Root" / "settings.json"


def load_settings_safe() -> AppSettings:
    """
    Carrega settings com validação Pydantic.
    
    FASE 3 ITEM 22: Se JSON corrompido ou inválido,
    reseta para defaults seguros em vez de crashar.
    
    Returns:
        AppSettings validado (ou defaults se falhou)
    """
    settings_path = get_settings_path()
    
    if not settings_path.exists():
        logger.info("Arquivo settings.json não existe, usando defaults")
        settings = AppSettings()
        save_settings(settings)
        return settings
    
    try:
        with open(settings_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        # Valida com Pydantic
        settings = AppSettings.model_validate(data)
        logger.debug("Settings carregadas com sucesso")
        return settings
        
    except json.JSONDecodeError as e:
        logger.warning(f"JSON corrompido em settings.json: {e}")
        logger.warning("Resetando para configurações padrão")
        
        # Backup do arquivo corrompido
        backup_path = settings_path.with_suffix(".json.corrupted")
        try:
            settings_path.rename(backup_path)
            logger.info(f"Backup do arquivo corrompido: {backup_path}")
        except Exception:
            pass
        
        settings = AppSettings()
        save_settings(settings)
        return settings
        
    except ValidationError as e:
        logger.warning(f"Validação falhou em settings.json: {e}")
        logger.warning("Usando configurações padrão para campos inválidos")
        
        # Tenta carregar parcialmente
        try:
            with open(settings_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            # Cria settings com defaults e sobrescreve campos válidos
            settings = AppSettings()
            for section_name in ["ai", "render", "compliance", "backup", "ui", "hunter"]:
                if section_name in data and isinstance(data[section_name], dict):
                    section_class = getattr(settings, section_name).__class__
                    try:
                        setattr(settings, section_name, section_class.model_validate(data[section_name]))
                    except ValidationError:
                        pass  # Mantém default da seção
            
            save_settings(settings)
            return settings
            
        except Exception:
            settings = AppSettings()
            save_settings(settings)
            return settings
    
    except Exception as e:
        logger.error(f"Erro inesperado ao carregar settings: {e}")
        return AppSettings()


def save_settings(settings: AppSettings) -> bool:
    """
    Salva settings para arquivo JSON.
    
    Args:
        settings: Instância de AppSettings
        
    Returns:
        True se salvou com sucesso
    """
    settings_path = get_settings_path()
    
    try:
        # Garante diretório existe
        settings_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(settings_path, "w", encoding="utf-8") as f:
            json.dump(settings.model_dump(), f, indent=2, ensure_ascii=False)
        
        logger.debug(f"Settings salvas em: {settings_path}")
        return True
        
    except Exception as e:
        logger.error(f"Erro ao salvar settings: {e}")
        return False


def factory_reset() -> AppSettings:
    """
    Factory Reset: Restaura configurações sem apagar banco de dados.
    
    FASE 3 ITEM 24: Botão de pânico para recuperação.
    
    Returns:
        AppSettings com valores padrão
    """
    logger.warning("FACTORY RESET: Restaurando configurações para padrão")
    
    settings = AppSettings()
    save_settings(settings)
    
    logger.info("Factory reset concluído")
    return settings


# ==============================================================================
# SINGLETON INSTANCE
# ==============================================================================

_settings_instance: Optional[AppSettings] = None


def get_app_settings() -> AppSettings:
    """
    Retorna instância Singleton das configurações.
    
    Returns:
        AppSettings validado
    """
    global _settings_instance
    
    if _settings_instance is None:
        _settings_instance = load_settings_safe()
    
    return _settings_instance


def reload_settings() -> AppSettings:
    """
    Força recarregamento das configurações do disco.
    
    Returns:
        AppSettings recarregado
    """
    global _settings_instance
    _settings_instance = load_settings_safe()
    return _settings_instance

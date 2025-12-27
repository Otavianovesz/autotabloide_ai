"""
AutoTabloide AI - Model Manager
=================================
Gerenciamento de modelos LLM com validação e download.
Passos 25-26, 30 do Checklist 100.

Funcionalidades:
- Validação SHA256 do modelo GGUF (25)
- Download automático do modelo (26)
- Exponential backoff nas requisições (30)
"""

import hashlib
import time
import asyncio
from pathlib import Path
from typing import Optional, Tuple, Callable
from urllib.request import urlretrieve
from urllib.error import URLError

from src.core.logging_config import get_logger
from src.core.constants import SYSTEM_ROOT

logger = get_logger("ModelManager")

# Diretório de modelos
MODELS_DIR = SYSTEM_ROOT / "bin" / "models"
MODELS_DIR.mkdir(parents=True, exist_ok=True)


# ==============================================================================
# HASHES CONHECIDOS DE MODELOS (Passo 25)
# ==============================================================================

KNOWN_MODEL_HASHES = {
    # Llama 3 8B Instruct Q4_K_M
    "Llama-3-8b-instruct.Q4_K_M.gguf": "sha256:...",  # Placeholder
    
    # Adicionar hashes conforme modelos são validados
}


def calculate_file_sha256(file_path: Path) -> str:
    """
    Calcula SHA256 de um arquivo.
    Passo 25 do Checklist - Validação SHA256 do .gguf.
    
    Args:
        file_path: Caminho do arquivo
        
    Returns:
        Hash SHA256 hexadecimal
    """
    sha256 = hashlib.sha256()
    
    with open(file_path, "rb") as f:
        # Lê em chunks para arquivos grandes
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    
    return sha256.hexdigest()


def validate_model_integrity(model_path: Path, expected_hash: Optional[str] = None) -> Tuple[bool, str]:
    """
    Valida integridade do modelo GGUF.
    Passo 25 do Checklist.
    
    Args:
        model_path: Caminho do modelo
        expected_hash: Hash esperado (opcional)
        
    Returns:
        Tupla (válido, hash_calculado)
    """
    if not model_path.exists():
        logger.error(f"Modelo não encontrado: {model_path}")
        return False, ""
    
    # Verifica tamanho mínimo (modelos GGUF são grandes)
    size_mb = model_path.stat().st_size / (1024 * 1024)
    if size_mb < 100:  # Menor que 100MB é suspeito
        logger.warning(f"Modelo muito pequeno ({size_mb:.1f}MB): {model_path.name}")
    
    logger.info(f"Calculando hash do modelo ({size_mb:.0f}MB)... Isso pode demorar.")
    actual_hash = calculate_file_sha256(model_path)
    
    if expected_hash:
        if actual_hash == expected_hash:
            logger.info(f"Modelo validado: {model_path.name}")
            return True, actual_hash
        else:
            logger.error(f"Hash não confere! Esperado: {expected_hash[:16]}..., Obtido: {actual_hash[:16]}...")
            return False, actual_hash
    
    # Se não tem hash esperado, aceita mas avisa
    logger.warning(f"Modelo sem hash de referência: {model_path.name}")
    return True, actual_hash


# ==============================================================================
# DOWNLOAD AUTOMÁTICO (Passo 26)
# ==============================================================================

# URLs de modelos conhecidos (Hugging Face)
MODEL_URLS = {
    # Llama 3 8B Instruct Q4_K_M - Modelo principal
    "Llama-3-8b-instruct.Q4_K_M.gguf": "https://huggingface.co/QuantFactory/Meta-Llama-3-8B-Instruct-GGUF/resolve/main/Meta-Llama-3-8B-Instruct.Q4_K_M.gguf",
}


async def download_model(
    model_name: str,
    url: Optional[str] = None,
    progress_callback: Optional[Callable[[float], None]] = None
) -> Tuple[bool, Optional[Path]]:
    """
    Download automático de modelo GGUF.
    Passo 26 do Checklist.
    
    Args:
        model_name: Nome do modelo
        url: URL de download (ou usa URL conhecida)
        progress_callback: Callback de progresso (0.0 a 1.0)
        
    Returns:
        Tupla (sucesso, caminho)
    """
    # Verifica se já existe
    model_path = MODELS_DIR / model_name
    if model_path.exists():
        logger.info(f"Modelo já existe: {model_name}")
        return True, model_path
    
    # Obtém URL
    download_url = url or MODEL_URLS.get(model_name)
    if not download_url:
        logger.error(f"URL de download não disponível para: {model_name}")
        return False, None
    
    logger.info(f"Iniciando download: {model_name}")
    
    # Download com progresso
    try:
        def reporthook(count, block_size, total_size):
            if progress_callback and total_size > 0:
                progress = count * block_size / total_size
                progress_callback(min(progress, 1.0))
        
        # Download em thread separada
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None,
            lambda: urlretrieve(download_url, str(model_path), reporthook)
        )
        
        logger.info(f"Download concluído: {model_name}")
        return True, model_path
        
    except URLError as e:
        logger.error(f"Erro de rede no download: {e}")
        return False, None
    except Exception as e:
        logger.error(f"Erro no download: {e}")
        return False, None


# ==============================================================================
# EXPONENTIAL BACKOFF (Passo 30)
# ==============================================================================

class ExponentialBackoff:
    """
    Implementa retry com exponential backoff.
    Passo 30 do Checklist.
    """
    
    def __init__(
        self,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        max_retries: int = 5,
        multiplier: float = 2.0
    ):
        """
        Args:
            base_delay: Delay inicial em segundos
            max_delay: Delay máximo em segundos
            max_retries: Número máximo de tentativas
            multiplier: Multiplicador do delay a cada retry
        """
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.max_retries = max_retries
        self.multiplier = multiplier
        self._attempt = 0
    
    def reset(self) -> None:
        """Reseta contador de tentativas."""
        self._attempt = 0
    
    def get_delay(self) -> float:
        """
        Calcula delay para a próxima tentativa.
        
        Returns:
            Delay em segundos
        """
        delay = self.base_delay * (self.multiplier ** self._attempt)
        return min(delay, self.max_delay)
    
    def can_retry(self) -> bool:
        """Verifica se pode tentar novamente."""
        return self._attempt < self.max_retries
    
    async def wait(self) -> bool:
        """
        Aguarda com backoff e incrementa contador.
        
        Returns:
            True se pode continuar, False se esgotou retries
        """
        if not self.can_retry():
            return False
        
        delay = self.get_delay()
        self._attempt += 1
        
        logger.debug(f"Backoff: aguardando {delay:.1f}s (tentativa {self._attempt}/{self.max_retries})")
        await asyncio.sleep(delay)
        
        return True
    
    def wait_sync(self) -> bool:
        """Versão síncrona do wait."""
        if not self.can_retry():
            return False
        
        delay = self.get_delay()
        self._attempt += 1
        
        logger.debug(f"Backoff: aguardando {delay:.1f}s (tentativa {self._attempt}/{self.max_retries})")
        time.sleep(delay)
        
        return True


async def retry_with_backoff(
    func,
    *args,
    backoff: Optional[ExponentialBackoff] = None,
    **kwargs
):
    """
    Executa função com retry e exponential backoff.
    
    Args:
        func: Função assíncrona a executar
        *args: Argumentos posicionais
        backoff: Configuração de backoff
        **kwargs: Argumentos nomeados
        
    Returns:
        Resultado da função
        
    Raises:
        Exception: Se todas as tentativas falharem
    """
    if backoff is None:
        backoff = ExponentialBackoff()
    
    last_error = None
    
    while True:
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            last_error = e
            logger.warning(f"Erro em retry_with_backoff: {e}")
            
            if not await backoff.wait():
                break
    
    raise last_error or Exception("Todas as tentativas falharam")

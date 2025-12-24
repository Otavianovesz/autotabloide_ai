"""
AutoTabloide AI - Code Fixes
===============================
Correções pontuais no código.
Passos 81-90 do Checklist v2.

Funcionalidades:
- Correções de bugs específicos
- Melhorias de robustez
"""

import os
import json
import re
from pathlib import Path
from typing import Optional, Tuple, Any
from decimal import Decimal, InvalidOperation

from src.core.logging_config import get_logger

logger = get_logger("CodeFixes")


# ============================================================================
# PASSO 81: Correção _save_to_cache path
# ============================================================================

def safe_write_cache(data: bytes, cache_path: Path) -> bool:
    """
    Escreve dados no cache com verificação de diretório.
    Passo 81 do Checklist v2.
    
    Args:
        data: Dados a salvar
        cache_path: Caminho do arquivo
        
    Returns:
        True se sucesso
    """
    try:
        # Garante que diretório pai existe
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Escreve atomicamente (temp + rename)
        temp_path = cache_path.with_suffix('.tmp')
        temp_path.write_bytes(data)
        temp_path.rename(cache_path)
        
        return True
        
    except Exception as e:
        logger.error(f"Erro ao escrever cache: {e}")
        return False


# ============================================================================
# PASSO 84: Validação JSON
# ============================================================================

def validate_json_field(value: str) -> Tuple[bool, Optional[Any]]:
    """
    Valida se string é JSON válido.
    Passo 84 do Checklist v2.
    
    Args:
        value: String JSON
        
    Returns:
        Tupla (é_válido, dado_parseado)
    """
    if not value:
        return True, None
    
    try:
        parsed = json.loads(value)
        return True, parsed
    except json.JSONDecodeError as e:
        logger.warning(f"JSON inválido: {e}")
        return False, None


# ============================================================================
# PASSO 85: Tratamento layout inexistente
# ============================================================================

async def safe_load_layout(layout_id: int) -> Optional[dict]:
    """
    Carrega layout com tratamento de erro.
    Passo 85 do Checklist v2.
    
    Args:
        layout_id: ID do layout
        
    Returns:
        Dict do layout ou None
    """
    try:
        from src.core.database import AsyncSessionLocal
        from src.core.repositories import LayoutRepository
        
        async with AsyncSessionLocal() as session:
            repo = LayoutRepository(session)
            layout = await repo.get_by_id(layout_id)
            
            if not layout:
                logger.warning(f"Layout {layout_id} não encontrado")
                return None
            
            return {
                "id": layout.id,
                "name": layout.nome,
                "slots": layout.quantidade_slots,
                "type": layout.formato
            }
            
    except Exception as e:
        logger.error(f"Erro ao carregar layout: {e}")
        return None


# ============================================================================
# PASSO 86: Deep copy de ProductInSlot
# ============================================================================

def deep_copy_product(product_data: dict) -> dict:
    """
    Cria cópia profunda de dados de produto.
    Passo 86 do Checklist v2.
    
    Evita mutação acidental ao duplicar slots.
    
    Args:
        product_data: Dados do produto
        
    Returns:
        Cópia independente
    """
    import copy
    return copy.deepcopy(product_data)


# ============================================================================
# PASSO 88: Caminho com caracteres especiais
# ============================================================================

def safe_font_path(font_path: str) -> str:
    """
    Normaliza caminho de fonte para Windows.
    Passo 88 do Checklist v2.
    
    Args:
        font_path: Caminho original
        
    Returns:
        Caminho normalizado
    """
    # Remove caracteres problemáticos
    safe_path = font_path.replace('/', os.sep).replace('\\', os.sep)
    
    # Resolve caminho absoluto
    path = Path(safe_path).resolve()
    
    return str(path)


# ============================================================================
# PASSO 89: Parse de preço robusto
# ============================================================================

def robust_parse_price(value: str) -> Optional[float]:
    """
    Parse robusto de preços em diversos formatos.
    Passo 89 do Checklist v2.
    
    Suporta:
    - 10.99 (US)
    - 10,99 (BR)
    - 1.000,00 (BR com milhar)
    - 1,000.00 (US com milhar)
    - R$ 10,99
    
    Args:
        value: String do preço
        
    Returns:
        Float ou None se inválido
    """
    if not value:
        return None
    
    # Remove prefixos de moeda
    cleaned = value.strip()
    cleaned = re.sub(r'^[R$€£\s]+', '', cleaned)
    cleaned = cleaned.strip()
    
    if not cleaned:
        return None
    
    try:
        # Detecta formato
        has_comma = ',' in cleaned
        has_dot = '.' in cleaned
        
        if has_comma and has_dot:
            # Formato misto - detecta qual é o decimal
            last_comma = cleaned.rfind(',')
            last_dot = cleaned.rfind('.')
            
            if last_comma > last_dot:
                # Formato BR: 1.000,00
                cleaned = cleaned.replace('.', '').replace(',', '.')
            else:
                # Formato US: 1,000.00
                cleaned = cleaned.replace(',', '')
                
        elif has_comma:
            # Só virgula - assume decimal BR
            # Mas verifica se parece separador de milhar
            parts = cleaned.split(',')
            if len(parts) == 2 and len(parts[1]) == 2:
                # 10,99 - decimal BR
                cleaned = cleaned.replace(',', '.')
            else:
                # 1,000 - milhar US
                cleaned = cleaned.replace(',', '')
        
        result = float(cleaned)
        
        # Validação de range
        if result < 0:
            logger.warning(f"Preço negativo rejeitado: {result}")
            return None
        
        if result > 1000000:
            logger.warning(f"Preço muito alto rejeitado: {result}")
            return None
        
        return round(result, 2)
        
    except (ValueError, InvalidOperation) as e:
        logger.warning(f"Preço inválido '{value}': {e}")
        return None


# ============================================================================
# PASSO 82: Global try/except em _process_task
# ============================================================================

def safe_task_wrapper(task_func):
    """
    Decorator para proteção de tarefas.
    Passo 82 do Checklist v2.
    
    Garante que erros não matam o loop do Sentinel.
    """
    def wrapper(*args, **kwargs):
        try:
            return task_func(*args, **kwargs)
        except Exception as e:
            logger.error(f"Erro em task {task_func.__name__}: {e}", exc_info=True)
            return {
                "status": "error",
                "error": str(e),
                "task": task_func.__name__
            }
    return wrapper


# ============================================================================
# PASSO 83: Session cache
# ============================================================================

class SessionCache:
    """
    Cache de sessão para evitar criações excessivas.
    Passo 83 do Checklist v2.
    """
    
    _instance = None
    _session = None
    
    @classmethod
    def get_session(cls):
        """Retorna sessão cacheada ou cria nova."""
        if cls._session is None:
            from src.core.database import AsyncSessionLocal
            cls._session = AsyncSessionLocal()
        return cls._session
    
    @classmethod
    async def close(cls):
        """Fecha sessão."""
        if cls._session:
            await cls._session.close()
            cls._session = None

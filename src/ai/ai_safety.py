"""
AutoTabloide AI - AI Safety Module
====================================
Robustez industrial para processamento de IA.
PROTOCOLO DE RETIFICAÇÃO: Passos 51-70 (IA e Sentinela).

Este módulo contém:
- Passo 51: Temperature 0.0 fixo
- Passo 52: Gramática GBNF para JSON
- Passo 54: User-Agent rotation
- Passo 55: Validação de imagem baixada
- Passo 56: Upscaler condicional
- Passo 60: Timeout do scraper
- Passo 61: Cache de busca
- Passo 67: Sanitização de prompt
- Passo 68: Detecção +18 automática
- Passo 70: Modo offline
"""

import re
import hashlib
import logging
import random
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any, Tuple
from functools import lru_cache

logger = logging.getLogger("AISafety")


# ==============================================================================
# PASSO 51: TEMPERATURE 0.0 FIXO
# ==============================================================================

class LLMConfigEnforcer:
    """
    Garante configurações determinísticas para LLM local.
    
    CRÍTICO: temperature=0.0 para respostas previsíveis.
    """
    
    # Configurações obrigatórias para produção
    MANDATORY_CONFIG = {
        "temperature": 0.0,
        "top_p": 0.1,
        "top_k": 1,
        "repeat_penalty": 1.1,
        "seed": 42,  # Seed fixo para reprodutibilidade
    }
    
    @classmethod
    def enforce_config(cls, user_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Aplica configurações obrigatórias, sobrescrevendo valores do usuário.
        
        Args:
            user_config: Configuração fornecida pelo usuário
            
        Returns:
            Configuração com valores obrigatórios aplicados
        """
        enforced = user_config.copy()
        
        # Forçar valores mandatórios
        for key, value in cls.MANDATORY_CONFIG.items():
            if key in enforced and enforced[key] != value:
                logger.warning(f"LLM config '{key}' forçado de {enforced[key]} para {value}")
            enforced[key] = value
        
        return enforced
    
    @classmethod
    def get_safe_config(cls) -> Dict[str, Any]:
        """Retorna configuração segura completa."""
        return {
            **cls.MANDATORY_CONFIG,
            "n_ctx": 4096,
            "n_batch": 512,
            "n_threads": 4,
            "verbose": False,
        }


# ==============================================================================
# PASSO 52: GRAMÁTICA GBNF PARA JSON
# ==============================================================================

class GBNFGrammars:
    """
    Gramáticas GBNF para forçar saída JSON estruturada do LLM.
    
    CRÍTICO: Sem gramática, LLM pode retornar texto livre que quebra o parser.
    """
    
    # Gramática para sanitização de produto
    PRODUCT_GRAMMAR = r'''
root ::= "{" ws "\"nome\":" ws string "," ws "\"marca\":" ws (string | "null") "," ws "\"peso\":" ws (string | "null") "," ws "\"categoria\":" ws (string | "null") "}"
string ::= "\"" ([^"\\] | "\\" .)* "\""
ws ::= [ \t\n]*
'''
    
    # Gramática para análise de oferta
    OFFER_GRAMMAR = r'''
root ::= "{" ws "\"tipo\":" ws tipo "," ws "\"valido\":" ws boolean "," ws "\"motivo\":" ws string "}"
tipo ::= "\"normal\"" | "\"oferta\"" | "\"combo\""
boolean ::= "true" | "false"
string ::= "\"" ([^"\\] | "\\" .)* "\""
ws ::= [ \t\n]*
'''
    
    # Gramática para classificação de imagem
    IMAGE_GRAMMAR = r'''
root ::= "{" ws "\"relevante\":" ws boolean "," ws "\"score\":" ws number "," ws "\"descricao\":" ws string "}"
boolean ::= "true" | "false"
number ::= [0-9]+ ("." [0-9]+)?
string ::= "\"" ([^"\\] | "\\" .)* "\""
ws ::= [ \t\n]*
'''
    
    # Gramática genérica para objetos simples
    SIMPLE_JSON_GRAMMAR = r'''
root ::= object
object ::= "{" ws (pair (", " pair)*)? ws "}"
pair ::= string ws ":" ws value
value ::= string | number | "true" | "false" | "null" | object | array
array ::= "[" ws (value (", " value)*)? ws "]"
string ::= "\"" ([^"\\] | "\\" .)* "\""
number ::= "-"? [0-9]+ ("." [0-9]+)?
ws ::= [ \t\n]*
'''
    
    @classmethod
    def get_grammar(cls, task: str) -> str:
        """
        Retorna gramática apropriada para a tarefa.
        
        Args:
            task: Nome da tarefa (product, offer, image, simple)
            
        Returns:
            String da gramática GBNF
        """
        grammars = {
            "product": cls.PRODUCT_GRAMMAR,
            "offer": cls.OFFER_GRAMMAR,
            "image": cls.IMAGE_GRAMMAR,
            "simple": cls.SIMPLE_JSON_GRAMMAR,
        }
        
        return grammars.get(task, cls.SIMPLE_JSON_GRAMMAR)
    
    @classmethod
    def validate_output(cls, output: str, task: str) -> Tuple[bool, Any, str]:
        """
        Valida se saída do LLM é JSON válido.
        
        Args:
            output: Saída do LLM
            task: Tarefa para logging
            
        Returns:
            Tuple (válido, dados_parseados, mensagem)
        """
        try:
            # Tentar encontrar JSON no output
            json_match = re.search(r'\{[^{}]+\}', output, re.DOTALL)
            
            if not json_match:
                return False, None, "Nenhum JSON encontrado na saída"
            
            json_str = json_match.group()
            data = json.loads(json_str)
            
            return True, data, "JSON válido"
            
        except json.JSONDecodeError as e:
            return False, None, f"JSON inválido: {e}"


# ==============================================================================
# PASSO 54: USER-AGENT ROTATION
# ==============================================================================

class UserAgentManager:
    """
    Rotação de User-Agents para evitar bloqueio de scrapers.
    
    PROBLEMA: Usar sempre o mesmo UA resulta em bloqueio.
    """
    
    USER_AGENTS = [
        # Chrome Windows
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
        
        # Firefox Windows
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0",
        
        # Edge
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",
        
        # Chrome Mac
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        
        # Safari
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15",
    ]
    
    _last_index = 0
    
    @classmethod
    def get_random(cls) -> str:
        """Retorna um User-Agent aleatório."""
        return random.choice(cls.USER_AGENTS)
    
    @classmethod
    def get_next(cls) -> str:
        """Retorna próximo User-Agent em rotação."""
        ua = cls.USER_AGENTS[cls._last_index % len(cls.USER_AGENTS)]
        cls._last_index += 1
        return ua
    
    @classmethod
    def get_headers(cls, referer: Optional[str] = None) -> Dict[str, str]:
        """Retorna headers completos para request."""
        headers = {
            "User-Agent": cls.get_next(),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
            "Accept-Encoding": "gzip, deflate, br",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
        }
        
        if referer:
            headers["Referer"] = referer
        
        return headers


# ==============================================================================
# PASSO 55: VALIDAÇÃO DE IMAGEM BAIXADA
# ==============================================================================

class ImageDownloadValidator:
    """
    Valida se arquivo baixado é realmente uma imagem.
    
    PROBLEMA: requests baixa qualquer coisa, incluindo HTML de erro.
    """
    
    # Magic bytes de formatos de imagem suportados
    IMAGE_SIGNATURES = {
        b'\xff\xd8\xff': 'jpeg',
        b'\x89PNG\r\n\x1a\n': 'png',
        b'GIF87a': 'gif',
        b'GIF89a': 'gif',
        b'RIFF': 'webp',  # WebP começa com RIFF
        b'BM': 'bmp',
    }
    
    MIN_SIZE_BYTES = 1024  # Mínimo 1KB para ser imagem válida
    MAX_SIZE_BYTES = 50 * 1024 * 1024  # Máximo 50MB
    
    @classmethod
    def validate(cls, file_path: Path) -> Tuple[bool, str, str]:
        """
        Valida se arquivo é uma imagem válida.
        
        Args:
            file_path: Caminho do arquivo
            
        Returns:
            Tuple (válido, formato, mensagem)
        """
        if not file_path.exists():
            return False, "", "Arquivo não existe"
        
        size = file_path.stat().st_size
        
        if size < cls.MIN_SIZE_BYTES:
            return False, "", f"Arquivo muito pequeno ({size} bytes)"
        
        if size > cls.MAX_SIZE_BYTES:
            return False, "", f"Arquivo muito grande ({size / 1024 / 1024:.1f}MB)"
        
        # Verificar magic bytes
        try:
            with open(file_path, 'rb') as f:
                header = f.read(16)
            
            for signature, format_name in cls.IMAGE_SIGNATURES.items():
                if header.startswith(signature):
                    return True, format_name, f"Imagem {format_name.upper()} válida"
            
            # WebP tem assinatura especial (RIFF....WEBP)
            if header[:4] == b'RIFF' and header[8:12] == b'WEBP':
                return True, 'webp', "Imagem WEBP válida"
            
            return False, "", "Formato de imagem não reconhecido"
            
        except Exception as e:
            return False, "", f"Erro ao ler arquivo: {e}"
    
    @classmethod
    def validate_from_bytes(cls, data: bytes) -> Tuple[bool, str]:
        """
        Valida bytes como imagem.
        
        Args:
            data: Bytes do arquivo
            
        Returns:
            Tuple (válido, formato)
        """
        if len(data) < cls.MIN_SIZE_BYTES:
            return False, ""
        
        if len(data) > cls.MAX_SIZE_BYTES:
            return False, ""
        
        for signature, format_name in cls.IMAGE_SIGNATURES.items():
            if data.startswith(signature):
                return True, format_name
        
        # WebP check
        if data[:4] == b'RIFF' and data[8:12] == b'WEBP':
            return True, 'webp'
        
        return False, ""


# ==============================================================================
# PASSO 56: UPSCALER CONDICIONAL
# ==============================================================================

class UpscalerConditions:
    """
    Define condições para ativar upscaling de imagem.
    
    Real-ESRGAN é pesado, só usar quando necessário.
    """
    
    MIN_DIMENSION = 1000  # Pixels - não upscale imagens grandes
    MIN_DPI_FOR_PRINT = 150  # Se menor, precisa upscale
    
    @classmethod
    def should_upscale(
        cls,
        image_width: int,
        image_height: int,
        target_width_mm: float,
        target_height_mm: float,
        has_gpu: bool = False
    ) -> Tuple[bool, str]:
        """
        Decide se deve fazer upscale da imagem.
        
        Args:
            image_width: Largura em pixels
            image_height: Altura em pixels
            target_width_mm: Largura do slot em mm
            target_height_mm: Altura do slot em mm
            has_gpu: Se há GPU compatível com Vulkan
            
        Returns:
            Tuple (deve_upscalar, motivo)
        """
        # Imagens já grandes não precisam
        if image_width >= cls.MIN_DIMENSION and image_height >= cls.MIN_DIMENSION:
            return False, "Imagem já tem resolução suficiente"
        
        # Calcular DPI efetivo
        dpi_x = (image_width / target_width_mm) * 25.4
        dpi_y = (image_height / target_height_mm) * 25.4
        effective_dpi = min(dpi_x, dpi_y)
        
        if effective_dpi >= cls.MIN_DPI_FOR_PRINT:
            return False, f"DPI suficiente ({effective_dpi:.0f})"
        
        # Precisa upscale, mas verifica GPU
        if not has_gpu:
            return False, "Upscale necessário mas GPU não disponível"
        
        return True, f"DPI baixo ({effective_dpi:.0f}), upscale recomendado"


# ==============================================================================
# PASSO 61: CACHE DE BUSCA
# ==============================================================================

class SearchCache:
    """
    Cache de resultados de busca para evitar requisições repetidas.
    """
    
    _cache: Dict[str, Dict[str, Any]] = {}
    CACHE_TTL_HOURS = 24
    MAX_CACHE_SIZE = 1000
    
    @classmethod
    def get_cache_key(cls, query: str, source: str = "google") -> str:
        """Gera chave de cache para busca."""
        normalized = query.lower().strip()
        return hashlib.md5(f"{source}:{normalized}".encode()).hexdigest()
    
    @classmethod
    def get(cls, query: str, source: str = "google") -> Optional[List[str]]:
        """
        Recupera resultado do cache.
        
        Args:
            query: Termo de busca
            source: Fonte (google, bing, etc)
            
        Returns:
            Lista de URLs ou None se não cacheado
        """
        key = cls.get_cache_key(query, source)
        
        if key not in cls._cache:
            return None
        
        entry = cls._cache[key]
        
        # Verificar TTL
        created = datetime.fromisoformat(entry["created"])
        if datetime.now() - created > timedelta(hours=cls.CACHE_TTL_HOURS):
            del cls._cache[key]
            return None
        
        return entry["results"]
    
    @classmethod
    def set(cls, query: str, results: List[str], source: str = "google") -> None:
        """
        Salva resultado no cache.
        
        Args:
            query: Termo de busca
            results: Lista de URLs encontradas
            source: Fonte
        """
        # Limitar tamanho do cache
        if len(cls._cache) >= cls.MAX_CACHE_SIZE:
            # Remover entradas mais antigas
            oldest = sorted(
                cls._cache.items(),
                key=lambda x: x[1]["created"]
            )[:100]
            for key, _ in oldest:
                del cls._cache[key]
        
        key = cls.get_cache_key(query, source)
        cls._cache[key] = {
            "results": results,
            "created": datetime.now().isoformat(),
        }
    
    @classmethod
    def clear(cls) -> int:
        """Limpa todo o cache. Retorna número de entradas removidas."""
        count = len(cls._cache)
        cls._cache.clear()
        return count


# ==============================================================================
# PASSO 67: SANITIZAÇÃO DE PROMPT
# ==============================================================================

class PromptSanitizer:
    """
    Sanitiza entradas de usuário antes de injetar em prompts.
    
    PROBLEMA: Nomes de produtos podem conter "ignore previous instructions".
    """
    
    # Padrões perigosos de injeção de prompt
    DANGEROUS_PATTERNS = [
        r"ignore\s+(previous|all|the)\s+(instructions?|prompts?)",
        r"disregard\s+(previous|all|the)",
        r"forget\s+everything",
        r"you\s+are\s+now",
        r"pretend\s+(you|to\s+be)",
        r"act\s+as\s+if",
        r"simulate\s+being",
        r"roleplay\s+as",
        r"[<>{}]",  # Marcadores de template
        r"\[\[.*?\]\]",  # Placeholders
        r"\{\{.*?\}\}",
    ]
    
    @classmethod
    def sanitize(cls, text: str, max_length: int = 500) -> str:
        """
        Sanitiza texto para uso seguro em prompt.
        
        Args:
            text: Texto original
            max_length: Comprimento máximo
            
        Returns:
            Texto sanitizado
        """
        if not text:
            return ""
        
        # Truncar
        sanitized = text[:max_length]
        
        # Remover padrões perigosos
        for pattern in cls.DANGEROUS_PATTERNS:
            sanitized = re.sub(pattern, '', sanitized, flags=re.IGNORECASE)
        
        # Normalizar espaços
        sanitized = ' '.join(sanitized.split())
        
        # Escapar aspas
        sanitized = sanitized.replace('"', "'")
        
        return sanitized.strip()
    
    @classmethod
    def create_safe_prompt(cls, template: str, **kwargs) -> str:
        """
        Cria prompt com valores sanitizados.
        
        Args:
            template: Template do prompt com {placeholders}
            **kwargs: Valores para substituir
            
        Returns:
            Prompt seguro
        """
        safe_kwargs = {
            key: cls.sanitize(str(value))
            for key, value in kwargs.items()
        }
        
        return template.format(**safe_kwargs)


# ==============================================================================
# PASSO 68: DETECÇÃO +18 AUTOMÁTICA
# ==============================================================================

class RestrictedProductDetector:
    """
    Detecta automaticamente produtos que requerem ícone +18.
    
    Bebidas alcoólicas, tabaco, etc.
    """
    
    # Palavras-chave que indicam produto +18
    ALCOHOL_KEYWORDS = {
        # Bebidas
        "cerveja", "beer", "chopp", "lager", "pilsen", "ipa", "stout",
        "vinho", "wine", "merlot", "cabernet", "chardonnay", "tinto", "branco",
        "vodka", "whisky", "whiskey", "rum", "cachaça", "pinga", "aguardente",
        "gin", "tequila", "absinto", "licor", "conhaque", "brandy",
        "champagne", "espumante", "prosecco", "cava",
        "sake", "soju", "mezcal", "bourbon",
        
        # Termos genéricos
        "destilado", "fermentado", "alcoólico", "teor alcoólico",
    }
    
    TOBACCO_KEYWORDS = {
        "cigarro", "tabaco", "charuto", "fumo", "cigarrilha",
        "narguilé", "hookah", "vape", "pod", "essência",
        "nicotina", "seda", "filtro de cigarro",
    }
    
    # Whitelist - parecem +18 mas não são
    WHITELIST = {
        "vinho culinário", "vinagre de vinho", "molho de vinho",
        "aroma de cerveja", "extrato de malte",
        "café licor", "essência de baunilha",  # Contém álcool mas é comida
        "chocolate licor", "bombom de licor",
    }
    
    @classmethod
    def is_restricted(cls, product_name: str, category: Optional[str] = None) -> Tuple[bool, str]:
        """
        Detecta se produto é +18.
        
        Args:
            product_name: Nome do produto
            category: Categoria (opcional)
            
        Returns:
            Tuple (é_restrito, motivo)
        """
        text = f"{product_name} {category or ''}".lower()
        
        # Verificar whitelist primeiro
        for safe_term in cls.WHITELIST:
            if safe_term in text:
                return False, f"Whitelist: {safe_term}"
        
        # Verificar álcool
        for keyword in cls.ALCOHOL_KEYWORDS:
            if keyword in text:
                return True, f"Bebida alcoólica detectada: {keyword}"
        
        # Verificar tabaco
        for keyword in cls.TOBACCO_KEYWORDS:
            if keyword in text:
                return True, f"Produto de tabaco detectado: {keyword}"
        
        return False, "Produto não restrito"


# ==============================================================================
# PASSO 70: MODO OFFLINE
# ==============================================================================

class OfflineModeManager:
    """
    Gerencia operação em modo offline.
    
    Quando sem internet, o sistema deve funcionar com limitações claras.
    """
    
    _is_offline: Optional[bool] = None
    _last_check: Optional[datetime] = None
    CHECK_INTERVAL_SECONDS = 60
    
    @classmethod
    def check_connectivity(cls, force: bool = False) -> bool:
        """
        Verifica conectividade com internet.
        
        Args:
            force: Forçar verificação mesmo se recente
            
        Returns:
            True se online
        """
        now = datetime.now()
        
        # Usar cache se verificação recente
        if not force and cls._last_check:
            elapsed = (now - cls._last_check).total_seconds()
            if elapsed < cls.CHECK_INTERVAL_SECONDS and cls._is_offline is not None:
                return not cls._is_offline
        
        # Verificar conectividade
        import socket
        
        try:
            # Tentar conectar ao Google DNS
            socket.create_connection(("8.8.8.8", 53), timeout=3)
            cls._is_offline = False
        except (socket.timeout, OSError):
            cls._is_offline = True
        
        cls._last_check = now
        return not cls._is_offline
    
    @classmethod
    def is_offline(cls) -> bool:
        """Retorna True se está offline."""
        cls.check_connectivity()
        return cls._is_offline or False
    
    @classmethod
    def get_available_features(cls) -> Dict[str, bool]:
        """
        Retorna features disponíveis no estado atual.
        
        Returns:
            Dict de feature -> disponível
        """
        is_online = cls.check_connectivity()
        
        return {
            "image_search": is_online,
            "web_scraping": is_online,
            "price_check": is_online,
            "product_sanitization": True,  # LLM local
            "pdf_generation": True,
            "template_editing": True,
            "database_operations": True,
        }


# ==============================================================================
# FUNÇÃO DE INICIALIZAÇÃO
# ==============================================================================

def initialize_ai_safety() -> dict:
    """
    Inicializa proteções de IA.
    
    Returns:
        Dict com status
    """
    results = {}
    
    # Verificar conectividade
    is_online = OfflineModeManager.check_connectivity()
    results["online"] = is_online
    results["features"] = OfflineModeManager.get_available_features()
    
    # Configuração LLM
    results["llm_config"] = LLMConfigEnforcer.get_safe_config()
    
    logger.info(f"AI safety inicializado (online={is_online})")
    return results

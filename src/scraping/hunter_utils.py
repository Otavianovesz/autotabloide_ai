"""
AutoTabloide AI - Hunter Improvements
========================================
Melhorias para o Hunter (web scraper).
Passos 25, 28-29 do Checklist v2.

Funcionalidades:
- Validação imagem branca antes de salvar (25)
- Rotação de User-Agent (28)
- Detecção de Captcha (29)
"""

import random
import re
from typing import Tuple, Optional, List
from pathlib import Path

from src.core.logging_config import get_logger

logger = get_logger("HunterUtils")


# Lista de User-Agents para rotação (passo 28)
USER_AGENTS = [
    # Chrome Windows
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    # Chrome Mac
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    # Firefox Windows
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0",
    # Firefox Mac
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:121.0) Gecko/20100101 Firefox/121.0",
    # Safari Mac
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
    # Edge Windows
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",
]


class UserAgentRotator:
    """
    Rotação de User-Agent para evitar bloqueios.
    Passo 28 do Checklist v2.
    """
    
    def __init__(self, agents: Optional[List[str]] = None):
        self.agents = agents or USER_AGENTS
        self._index = 0
    
    def get_random(self) -> str:
        """Retorna User-Agent aleatório."""
        return random.choice(self.agents)
    
    def get_next(self) -> str:
        """Retorna próximo User-Agent em sequência."""
        agent = self.agents[self._index]
        self._index = (self._index + 1) % len(self.agents)
        return agent
    
    def get_headers(self) -> dict:
        """Retorna headers completos com User-Agent."""
        return {
            "User-Agent": self.get_random(),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
            "Accept-Encoding": "gzip, deflate",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
        }


# Padrões de detecção de Captcha (passo 29)
CAPTCHA_PATTERNS = [
    r'reCAPTCHA',
    r'recaptcha',
    r'g-recaptcha',
    r'hcaptcha',
    r'captcha',
    r'cf-turnstile',  # Cloudflare
    r'challenge-form',
    r'security check',
    r'verify you are human',
    r'are you a robot',
    r'suspicious activity',
    r'unusual traffic',
    r'blocked',
    r'access denied',
]


def detect_captcha(html_content: str) -> Tuple[bool, Optional[str]]:
    """
    Detecta se HTML contém captcha.
    Passo 29 do Checklist v2.
    
    Args:
        html_content: Conteúdo HTML da página
        
    Returns:
        Tupla (tem_captcha, tipo_detectado)
    """
    if not html_content:
        return False, None
    
    content_lower = html_content.lower()
    
    for pattern in CAPTCHA_PATTERNS:
        if re.search(pattern, content_lower, re.IGNORECASE):
            logger.warning(f"Captcha detectado: {pattern}")
            return True, pattern
    
    # Detecta páginas muito curtas (provavelmente bloqueio)
    if len(html_content) < 500:
        if 'blocked' in content_lower or 'denied' in content_lower:
            return True, "access_denied"
    
    return False, None


def is_valid_image_response(content: bytes, content_type: str = "") -> Tuple[bool, str]:
    """
    Valida se resposta é uma imagem válida.
    Passo 25 do Checklist v2 - Validação antes de salvar.
    
    Args:
        content: Bytes do conteúdo
        content_type: Content-Type do header
        
    Returns:
        Tupla (é_válida, motivo)
    """
    if not content:
        return False, "Conteúdo vazio"
    
    # Verifica magic bytes de imagem
    magic_bytes = {
        b'\x89PNG': 'image/png',
        b'\xff\xd8\xff': 'image/jpeg',
        b'GIF87a': 'image/gif',
        b'GIF89a': 'image/gif',
        b'RIFF': 'image/webp',  # WebP começa com RIFF
    }
    
    is_image = False
    detected_type = None
    
    for magic, img_type in magic_bytes.items():
        if content[:len(magic)] == magic:
            is_image = True
            detected_type = img_type
            break
    
    if not is_image:
        # Pode ser HTML (página de erro ou captcha)
        try:
            text = content[:500].decode('utf-8', errors='ignore').lower()
            if '<html' in text or '<!doctype' in text:
                has_captcha, _ = detect_captcha(text)
                if has_captcha:
                    return False, "Página de captcha retornada"
                return False, "HTML retornado em vez de imagem"
        except:
            pass
        
        return False, "Formato de imagem não reconhecido"
    
    # Verifica tamanho mínimo (imagens muito pequenas são suspeitas)
    if len(content) < 1000:
        return False, f"Imagem muito pequena: {len(content)} bytes"
    
    return True, f"OK ({detected_type})"


def validate_image_content(image_bytes: bytes) -> Tuple[bool, str]:
    """
    Valida qualidade da imagem (branca, muito pequena, etc).
    Integra com ImageValidation.
    
    Args:
        image_bytes: Bytes da imagem
        
    Returns:
        Tupla (é_válida, motivo)
    """
    try:
        from src.ai.image_validation import validate_image_quality
        return validate_image_quality(image_bytes)
    except ImportError:
        # Fallback se módulo não disponível
        return True, "OK (sem validação avançada)"


class HunterImageValidator:
    """
    Validador completo para imagens do Hunter.
    Combina todas as validações.
    """
    
    @staticmethod
    def validate(content: bytes, content_type: str = "") -> Tuple[bool, str]:
        """
        Validação completa de imagem.
        
        Args:
            content: Bytes da imagem
            content_type: Content-Type
            
        Returns:
            Tupla (é_válida, motivo)
        """
        # 1. Valida resposta HTTP
        valid, reason = is_valid_image_response(content, content_type)
        if not valid:
            return False, reason
        
        # 2. Valida qualidade da imagem
        valid, reason = validate_image_content(content)
        if not valid:
            return False, reason
        
        return True, "OK"


# Singleton do rotator
_ua_rotator: Optional[UserAgentRotator] = None


def get_user_agent_rotator() -> UserAgentRotator:
    """Retorna instância singleton do rotator."""
    global _ua_rotator
    if _ua_rotator is None:
        _ua_rotator = UserAgentRotator()
    return _ua_rotator


def get_random_user_agent() -> str:
    """Retorna User-Agent aleatório."""
    return get_user_agent_rotator().get_random()

"""
AutoTabloide AI - Text Utilities
=================================
FASE 2 MOTOR SENTINELA: Utilitários de texto para sanitização.

Features:
- SmartTitleCase: Title Case inteligente respeitando artigos portugueses
- UnitNormalizer: Normalização de unidades de medida
- TextCleaner: Limpeza geral de texto
"""

import re
import logging
from typing import List, Set, Optional

logger = logging.getLogger("TextUtils")


# ==============================================================================
# PASSO 31: SMART TITLE CASE
# ==============================================================================

class SmartTitleCase:
    """
    Title Case inteligente para português brasileiro.
    
    PROBLEMA: str.title() converte "CERVEJA de TRIGO" para "Cerveja De Trigo".
    SOLUÇÃO: Manter artigos e preposições em minúsculo.
    """
    
    # Palavras que devem permanecer em minúsculo (exceto no início)
    LOWERCASE_WORDS: Set[str] = {
        # Preposições
        "de", "da", "do", "das", "dos",
        "em", "na", "no", "nas", "nos",
        "para", "pra", "pro",
        "por", "pelo", "pela", "pelos", "pelas",
        "com", "sem",
        "a", "ao", "à", "às", "aos",
        # Conjunções
        "e", "ou",
        # Artigos (quando não no início)
        "o", "a", "os", "as", "um", "uma", "uns", "umas",
    }
    
    # Palavras que devem permanecer em maiúsculo (siglas, marcas conhecidas)
    UPPERCASE_WORDS: Set[str] = {
        "TV", "DVD", "CD", "USB", "LED", "LCD",
        "HD", "SSD", "RAM", "CPU", "GPU",
        "XL", "XXL", "P", "M", "G", "GG",
        "ML", "KG", "MG", "UN",
    }
    
    @classmethod
    def apply(cls, text: str) -> str:
        """
        Aplica Title Case inteligente.
        
        Args:
            text: Texto para converter
            
        Returns:
            Texto em Title Case inteligente
        """
        if not text:
            return ""
        
        # Divide em palavras preservando espaços múltiplos
        words = text.split()
        result = []
        
        for i, word in enumerate(words):
            word_lower = word.lower()
            word_upper = word.upper()
            
            # Primeira palavra sempre capitalizada
            if i == 0:
                result.append(cls._capitalize_word(word))
            # Verificar se é sigla conhecida
            elif word_upper in cls.UPPERCASE_WORDS:
                result.append(word_upper)
            # Verificar se é artigo/preposição
            elif word_lower in cls.LOWERCASE_WORDS:
                result.append(word_lower)
            # Caso padrão: capitalizar
            else:
                result.append(cls._capitalize_word(word))
        
        return " ".join(result)
    
    @classmethod
    def _capitalize_word(cls, word: str) -> str:
        """Capitaliza palavra, tratando caracteres especiais."""
        if not word:
            return ""
        
        # Se começa com número, manter como está
        if word[0].isdigit():
            return word.lower()
        
        # Capitalizar apenas primeira letra
        return word[0].upper() + word[1:].lower()


# ==============================================================================
# PASSO 32: NORMALIZAÇÃO DE UNIDADES
# ==============================================================================

class UnitNormalizer:
    """
    Normaliza unidades de medida para formato padrão.
    
    PROBLEMA: Planilhas usam "litros", "LTS", "Litro", "L" para mesma unidade.
    SOLUÇÃO: Normalizar tudo para formato canônico.
    """
    
    # Mapeamento de variações para forma canônica
    UNIT_MAPPINGS = {
        # Volume - Litros
        "litros": "L",
        "litro": "L",
        "lts": "L",
        "lt": "L",
        "l": "L",
        # Volume - Mililitros
        "mililitros": "ml",
        "mililitro": "ml",
        "mls": "ml",
        # Peso - Gramas
        "gramas": "g",
        "grama": "g",
        "gr": "g",
        "grs": "g",
        # Peso - Quilos
        "quilos": "kg",
        "quilo": "kg",
        "quilogramas": "kg",
        "quilograma": "kg",
        "kilo": "kg",
        "kilos": "kg",
        # Peso - Miligramas
        "miligramas": "mg",
        "miligrama": "mg",
        "mgs": "mg",
        # Unidades
        "unidades": "un",
        "unidade": "un",
        "und": "un",
        "pç": "un",
        "pc": "un",
        "pcs": "un",
        "peça": "un",
        "peças": "un",
        # Pacotes
        "pacotes": "pct",
        "pacote": "pct",
        "pcts": "pct",
        "pk": "pct",
        # Caixas
        "caixas": "cx",
        "caixa": "cx",
        "cxs": "cx",
        # Dúzias
        "duzias": "dz",
        "duzia": "dz",
        "dúzias": "dz",
        "dúzia": "dz",
    }
    
    # Regex para encontrar números seguidos de unidades
    _PATTERN = re.compile(
        r'(\d+(?:[.,]\d+)?)\s*(' + '|'.join(
            re.escape(k) for k in sorted(UNIT_MAPPINGS.keys(), key=len, reverse=True)
        ) + r')\b',
        re.IGNORECASE
    )
    
    @classmethod
    def normalize(cls, text: str) -> str:
        """
        Normaliza unidades de medida no texto.
        
        Args:
            text: Texto com unidades a normalizar
            
        Returns:
            Texto com unidades normalizadas
        """
        if not text:
            return ""
        
        def replacer(match):
            number = match.group(1)
            unit = match.group(2).lower()
            normalized_unit = cls.UNIT_MAPPINGS.get(unit, unit)
            return f"{number}{normalized_unit}"
        
        return cls._PATTERN.sub(replacer, text)
    
    @classmethod
    def extract_unit(cls, text: str) -> Optional[str]:
        """
        Extrai unidade de medida principal do texto.
        
        Args:
            text: Texto para analisar
            
        Returns:
            Unidade normalizada ou None
        """
        match = cls._PATTERN.search(text)
        if match:
            unit = match.group(2).lower()
            return cls.UNIT_MAPPINGS.get(unit, unit)
        return None
    
    @classmethod
    def extract_value_and_unit(cls, text: str) -> Optional[tuple]:
        """
        Extrai valor numérico e unidade.
        
        Args:
            text: Texto para analisar
            
        Returns:
            Tuple (valor, unidade) ou None
        """
        match = cls._PATTERN.search(text)
        if match:
            value = match.group(1).replace(",", ".")
            unit = match.group(2).lower()
            normalized_unit = cls.UNIT_MAPPINGS.get(unit, unit)
            return (float(value), normalized_unit)
        return None


# ==============================================================================
# TEXT CLEANER (Auxiliar)
# ==============================================================================

class TextCleaner:
    """Limpeza geral de texto para sanitização."""
    
    # Caracteres a remover
    TRASH_CHARS = set("®©™°")
    
    # Padrões de espaços excessivos
    _MULTI_SPACE = re.compile(r'\s+')
    
    # Códigos de produto comuns a remover
    _PRODUCT_CODES = re.compile(r'\b[A-Z]{2,4}\d{4,}\b')
    
    @classmethod
    def clean(cls, text: str) -> str:
        """
        Limpeza básica de texto.
        
        Args:
            text: Texto sujo
            
        Returns:
            Texto limpo
        """
        if not text:
            return ""
        
        # Remove caracteres trash
        for char in cls.TRASH_CHARS:
            text = text.replace(char, "")
        
        # Normaliza espaços
        text = cls._MULTI_SPACE.sub(" ", text)
        
        # Strip
        return text.strip()
    
    @classmethod
    def remove_product_codes(cls, text: str) -> str:
        """Remove códigos de produto do texto."""
        return cls._PRODUCT_CODES.sub("", text).strip()
    
    @classmethod
    def sanitize_for_display(cls, text: str) -> str:
        """
        Pipeline completo de sanitização para exibição.
        
        Args:
            text: Texto bruto
            
        Returns:
            Texto pronto para exibição
        """
        # Limpeza básica
        text = cls.clean(text)
        
        # Normaliza unidades
        text = UnitNormalizer.normalize(text)
        
        # Aplica Title Case inteligente
        text = SmartTitleCase.apply(text)
        
        return text


# ==============================================================================
# CONVENIENCE FUNCTIONS
# ==============================================================================

def smart_title(text: str) -> str:
    """Atalho para SmartTitleCase.apply()"""
    return SmartTitleCase.apply(text)


def normalize_units(text: str) -> str:
    """Atalho para UnitNormalizer.normalize()"""
    return UnitNormalizer.normalize(text)


def sanitize_text(text: str) -> str:
    """Atalho para TextCleaner.sanitize_for_display()"""
    return TextCleaner.sanitize_for_display(text)

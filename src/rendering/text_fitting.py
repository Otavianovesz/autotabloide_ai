"""
AutoTabloide AI - Text Fitting Engine
=======================================
Motor de ajuste de texto com kerning e quebra inteligente.
PROTOCOLO DE RETIFICAÇÃO: Passo 34 (Text Fitting com kerning).

Implementa o algoritmo de ajuste de texto conforme Vol. III, Cap. 2.
"""

import re
import logging
from typing import Optional, Tuple, List, Dict, Any
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger("TextFitting")


class FitStrategy(Enum):
    """Estratégias de ajuste de texto."""
    SHRINK = "shrink"       # Reduz tamanho da fonte
    TRUNCATE = "truncate"   # Corta com reticências
    WRAP = "wrap"           # Quebra em múltiplas linhas
    BOTH = "both"           # Combina shrink + wrap


@dataclass
class FontMetrics:
    """Métricas de fonte para cálculos."""
    family: str
    size: float
    weight: int = 400
    
    # Fatores estimados (idealmente viriam de fonte real)
    char_width_factor: float = 0.6   # Largura média / altura
    line_height_factor: float = 1.2  # Altura linha / tamanho fonte
    kerning_factor: float = 1.0      # Ajuste de kerning


@dataclass
class TextFitResult:
    """Resultado do ajuste de texto."""
    text: str
    font_size: float
    lines: List[str]
    truncated: bool
    scale_factor: float
    total_height: float
    total_width: float


class TextFittingEngine:
    """
    Motor de ajuste de texto para caixas de tamanho fixo.
    
    PASSO 34: Implementa kerning e cálculos precisos de largura.
    """
    
    MIN_FONT_SIZE = 6.0   # Mínimo legível
    MAX_SHRINK_RATIO = 0.5  # Máximo de redução (50%)
    
    # Tabela de kerning comum (pares de letras que precisam ajuste)
    KERNING_PAIRS = {
        ('A', 'V'): -0.08,
        ('A', 'W'): -0.06,
        ('A', 'Y'): -0.08,
        ('A', 'T'): -0.06,
        ('L', 'T'): -0.08,
        ('L', 'V'): -0.08,
        ('L', 'W'): -0.06,
        ('L', 'Y'): -0.08,
        ('P', 'A'): -0.06,
        ('P', 'a'): -0.04,
        ('T', 'A'): -0.06,
        ('T', 'a'): -0.06,
        ('T', 'e'): -0.06,
        ('T', 'o'): -0.06,
        ('V', 'A'): -0.08,
        ('V', 'a'): -0.06,
        ('V', 'e'): -0.04,
        ('V', 'o'): -0.04,
        ('W', 'A'): -0.06,
        ('W', 'a'): -0.04,
        ('Y', 'A'): -0.08,
        ('Y', 'a'): -0.06,
        ('Y', 'e'): -0.06,
        ('Y', 'o'): -0.06,
        ('f', 'f'): -0.02,
        ('r', 'n'): 0.02,
        ('r', 'm'): 0.02,
    }
    
    # Larguras relativas de caracteres (mono = 1.0)
    CHAR_WIDTHS = {
        'i': 0.3, 'l': 0.3, '!': 0.3, '|': 0.3, '.': 0.3, ',': 0.3,
        'I': 0.4, 'j': 0.35, 'f': 0.4, 't': 0.45, 'r': 0.45,
        ' ': 0.4,
        'm': 1.4, 'w': 1.3, 'M': 1.4, 'W': 1.5,
        '@': 1.3, '%': 1.2,
    }
    DEFAULT_CHAR_WIDTH = 0.6
    
    def __init__(self, use_kerning: bool = True):
        self.use_kerning = use_kerning
    
    def fit_text(
        self,
        text: str,
        box_width: float,
        box_height: float,
        font: FontMetrics,
        strategy: FitStrategy = FitStrategy.BOTH,
        max_lines: int = 3
    ) -> TextFitResult:
        """
        Ajusta texto para caber em uma caixa.
        
        Args:
            text: Texto a ajustar
            box_width: Largura disponível (px ou pt)
            box_height: Altura disponível
            font: Métricas da fonte
            strategy: Estratégia de ajuste
            max_lines: Máximo de linhas permitidas
            
        Returns:
            TextFitResult com texto ajustado
        """
        if not text or not text.strip():
            return TextFitResult(
                text="", font_size=font.size, lines=[],
                truncated=False, scale_factor=1.0,
                total_height=0, total_width=0
            )
        
        text = text.strip()
        current_size = font.size
        scale = 1.0
        
        # Calcular largura do texto original
        text_width = self._calculate_text_width(text, font, current_size)
        line_height = current_size * font.line_height_factor
        
        # Estratégia TRUNCATE simples
        if strategy == FitStrategy.TRUNCATE:
            if text_width > box_width:
                truncated_text = self._truncate_to_width(text, box_width, font, current_size)
                return TextFitResult(
                    text=truncated_text,
                    font_size=current_size,
                    lines=[truncated_text],
                    truncated=True,
                    scale_factor=1.0,
                    total_height=line_height,
                    total_width=self._calculate_text_width(truncated_text, font, current_size)
                )
            return TextFitResult(
                text=text, font_size=current_size, lines=[text],
                truncated=False, scale_factor=1.0,
                total_height=line_height, total_width=text_width
            )
        
        # Estratégia SHRINK
        if strategy in [FitStrategy.SHRINK, FitStrategy.BOTH]:
            # Tentar caber em uma linha reduzindo fonte
            if text_width > box_width:
                needed_scale = box_width / text_width
                
                if needed_scale >= self.MAX_SHRINK_RATIO:
                    new_size = current_size * needed_scale
                    if new_size >= self.MIN_FONT_SIZE:
                        return TextFitResult(
                            text=text,
                            font_size=new_size,
                            lines=[text],
                            truncated=False,
                            scale_factor=needed_scale,
                            total_height=new_size * font.line_height_factor,
                            total_width=box_width
                        )
        
        # Estratégia WRAP ou BOTH (se SHRINK não bastou)
        if strategy in [FitStrategy.WRAP, FitStrategy.BOTH]:
            lines = self._wrap_text(text, box_width, font, current_size, max_lines)
            
            # Verificar se cabe na altura
            total_height = len(lines) * line_height
            
            if total_height > box_height:
                # Reduzir fonte para caber
                needed_scale = box_height / total_height
                new_size = max(current_size * needed_scale, self.MIN_FONT_SIZE)
                new_line_height = new_size * font.line_height_factor
                
                # Re-wrap com fonte menor
                lines = self._wrap_text(text, box_width, font, new_size, max_lines)
                total_height = len(lines) * new_line_height
                
                return TextFitResult(
                    text='\n'.join(lines),
                    font_size=new_size,
                    lines=lines,
                    truncated=len(lines) >= max_lines,
                    scale_factor=needed_scale,
                    total_height=total_height,
                    total_width=max(self._calculate_text_width(l, font, new_size) for l in lines)
                )
            
            return TextFitResult(
                text='\n'.join(lines),
                font_size=current_size,
                lines=lines,
                truncated=len(lines) >= max_lines,
                scale_factor=1.0,
                total_height=total_height,
                total_width=max(self._calculate_text_width(l, font, current_size) for l in lines)
            )
        
        # Fallback
        return TextFitResult(
            text=text, font_size=font.size, lines=[text],
            truncated=False, scale_factor=1.0,
            total_height=line_height, total_width=text_width
        )
    
    def _calculate_text_width(
        self,
        text: str,
        font: FontMetrics,
        font_size: float
    ) -> float:
        """Calcula largura do texto com kerning."""
        if not text:
            return 0
        
        base_width = 0
        kerning_adjustment = 0
        
        for i, char in enumerate(text):
            # Largura do caractere
            char_width = self.CHAR_WIDTHS.get(char, self.DEFAULT_CHAR_WIDTH)
            base_width += char_width * font_size * font.char_width_factor
            
            # Kerning com próximo caractere
            if self.use_kerning and i < len(text) - 1:
                next_char = text[i + 1]
                pair = (char, next_char)
                
                if pair in self.KERNING_PAIRS:
                    kerning_adjustment += self.KERNING_PAIRS[pair] * font_size
        
        total_width = base_width + kerning_adjustment * font.kerning_factor
        return max(0, total_width)
    
    def _wrap_text(
        self,
        text: str,
        max_width: float,
        font: FontMetrics,
        font_size: float,
        max_lines: int
    ) -> List[str]:
        """Quebra texto em linhas que cabem na largura."""
        words = text.split()
        lines = []
        current_line = []
        current_width = 0
        space_width = self._calculate_text_width(' ', font, font_size)
        
        for word in words:
            word_width = self._calculate_text_width(word, font, font_size)
            
            # Se palavra sozinha é maior que linha, truncar
            if word_width > max_width and not current_line:
                truncated_word = self._truncate_to_width(word, max_width, font, font_size)
                lines.append(truncated_word)
                if len(lines) >= max_lines:
                    break
                continue
            
            # Se cabe na linha atual
            new_width = current_width + (space_width if current_line else 0) + word_width
            
            if new_width <= max_width:
                current_line.append(word)
                current_width = new_width
            else:
                # Nova linha
                if current_line:
                    lines.append(' '.join(current_line))
                    if len(lines) >= max_lines:
                        # Adicionar reticências se há mais texto
                        if lines:
                            lines[-1] = lines[-1].rstrip() + '...'
                        break
                
                current_line = [word]
                current_width = word_width
        
        # Última linha
        if current_line and len(lines) < max_lines:
            lines.append(' '.join(current_line))
        
        return lines
    
    def _truncate_to_width(
        self,
        text: str,
        max_width: float,
        font: FontMetrics,
        font_size: float
    ) -> str:
        """Trunca texto para caber na largura, adicionando reticências."""
        ellipsis = '...'
        ellipsis_width = self._calculate_text_width(ellipsis, font, font_size)
        target_width = max_width - ellipsis_width
        
        if target_width <= 0:
            return ellipsis
        
        current_width = 0
        result = []
        
        for char in text:
            char_width = self.CHAR_WIDTHS.get(char, self.DEFAULT_CHAR_WIDTH) * font_size * font.char_width_factor
            
            if current_width + char_width > target_width:
                break
            
            result.append(char)
            current_width += char_width
        
        return ''.join(result).rstrip() + ellipsis


# ==============================================================================
# FUNÇÕES DE CONVENIÊNCIA
# ==============================================================================

_engine: Optional[TextFittingEngine] = None


def get_text_fitting_engine() -> TextFittingEngine:
    """Retorna instância global do engine."""
    global _engine
    if _engine is None:
        _engine = TextFittingEngine()
    return _engine


def fit_text_to_box(
    text: str,
    width: float,
    height: float,
    font_family: str = "Arial",
    font_size: float = 12.0,
    strategy: str = "both"
) -> TextFitResult:
    """
    Função de conveniência para ajustar texto.
    
    Args:
        text: Texto a ajustar
        width, height: Dimensões da caixa
        font_family: Família da fonte
        font_size: Tamanho inicial
        strategy: "shrink", "truncate", "wrap" ou "both"
        
    Returns:
        TextFitResult
    """
    engine = get_text_fitting_engine()
    font = FontMetrics(family=font_family, size=font_size)
    strat = FitStrategy(strategy)
    
    return engine.fit_text(text, width, height, font, strat)

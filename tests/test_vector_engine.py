"""
AutoTabloide AI - Testes do VectorEngine
==========================================
Valida manipulação SVG, text fitting e price logic.
"""

import pytest
import sys
from pathlib import Path
from decimal import Decimal
from unittest.mock import Mock, patch, MagicMock

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.rendering.vector import VectorEngine


class TestVectorEngineBasics:
    """Testes básicos do VectorEngine."""
    
    def test_engine_initialization(self):
        """Testa inicialização do engine."""
        engine = VectorEngine(strict_fonts=False)
        
        assert engine.tree is None
        assert engine.root is None
        assert engine.slots == {}
        assert engine.strict_fonts == False
    
    def test_load_from_string(self):
        """Testa carregamento de SVG a partir de string."""
        engine = VectorEngine(strict_fonts=False)
        
        svg_content = b'''<?xml version="1.0"?>
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
            <rect id="SLOT_01" x="0" y="0" width="50" height="50"/>
            <text id="TXT_NOME">Placeholder</text>
        </svg>
        '''
        
        engine.load_from_string(svg_content)
        
        assert engine.root is not None
        assert "SLOT_01" in engine.slots
        assert "TXT_NOME" in engine.slots
    
    def test_get_viewbox(self):
        """Testa extração do viewBox."""
        engine = VectorEngine(strict_fonts=False)
        
        svg_content = b'''<?xml version="1.0"?>
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="10 20 800 600">
        </svg>
        '''
        
        engine.load_from_string(svg_content)
        vb = engine.get_viewbox()
        
        assert vb == (10.0, 20.0, 800.0, 600.0)


class TestCurrencyFormatting:
    """Testa formatação de moeda."""
    
    def test_format_currency_simple(self):
        """Testa formatação BRL simples."""
        engine = VectorEngine(strict_fonts=False)
        
        assert engine._format_currency(19.90) == "19,90"
        assert engine._format_currency(1.50) == "1,50"
        assert engine._format_currency(1000.00) == "1.000,00"
        assert engine._format_currency(None) == ""
    
    def test_split_price(self):
        """Testa separação inteiro/centavos."""
        engine = VectorEngine(strict_fonts=False)
        
        int_part, dec_part = engine._split_price("19,90")
        assert int_part == "19"
        assert dec_part == ",90"
        
        int_part, dec_part = engine._split_price("1.234,56")
        assert int_part == "1.234"
        assert dec_part == ",56"


class TestPriceLogic:
    """Testa lógica de precificação De/Por."""
    
    def test_handle_price_logic_basic(self):
        """Testa aplicação de preço básico."""
        engine = VectorEngine(strict_fonts=False)
        
        svg_content = b'''<?xml version="1.0"?>
        <svg xmlns="http://www.w3.org/2000/svg">
            <text id="TXT_PRECO_POR_01">0</text>
            <text id="TXT_PRECO_INT_01">0</text>
            <text id="TXT_PRECO_DEC_01">0</text>
        </svg>
        '''
        
        engine.load_from_string(svg_content)
        engine.handle_price_logic("01", 19.90)
        
        assert engine.slots["TXT_PRECO_POR_01"].text == "19,90"
        assert engine.slots["TXT_PRECO_INT_01"].text == "19"
        assert engine.slots["TXT_PRECO_DEC_01"].text == ",90"
    
    def test_handle_price_logic_with_discount(self):
        """Testa lógica De/Por com desconto."""
        engine = VectorEngine(strict_fonts=False)
        
        svg_content = b'''<?xml version="1.0"?>
        <svg xmlns="http://www.w3.org/2000/svg">
            <text id="TXT_PRECO_POR_01">0</text>
            <text id="TXT_PRECO_DE_01" style="display:none">0</text>
        </svg>
        '''
        
        engine.load_from_string(svg_content)
        engine.handle_price_logic("01", preco_atual=17.90, preco_ref=24.90)
        
        # Preço atual
        assert engine.slots["TXT_PRECO_POR_01"].text == "17,90"
        
        # Preço de referência deve aparecer
        de_node = engine.slots["TXT_PRECO_DE_01"]
        assert de_node.text == "De R$ 24,90"
        assert "display:inline" in de_node.get("style", "") or "display:none" not in de_node.get("style", "")
    
    def test_handle_price_logic_no_discount(self):
        """Testa ocultação de De quando não há desconto."""
        engine = VectorEngine(strict_fonts=False)
        
        svg_content = b'''<?xml version="1.0"?>
        <svg xmlns="http://www.w3.org/2000/svg">
            <text id="TXT_PRECO_POR_01">0</text>
            <text id="TXT_PRECO_DE_01" style="display:inline">0</text>
        </svg>
        '''
        
        engine.load_from_string(svg_content)
        engine.handle_price_logic("01", preco_atual=19.90, preco_ref=None)
        
        # Sem desconto, De deve estar oculto
        de_node = engine.slots["TXT_PRECO_DE_01"]
        assert "display:none" in de_node.get("style", "")


class TestAlcoholicDetection:
    """Testa detecção de categoria restrita."""
    
    def test_is_restricted_category(self):
        """Testa identificação de categorias +18."""
        engine = VectorEngine(strict_fonts=False)
        
        assert engine._is_restricted_category("Cerveja") == True
        assert engine._is_restricted_category("cerveja") == True
        assert engine._is_restricted_category("Bebida Alcoólica") == True
        assert engine._is_restricted_category("alcoolica") == True
        assert engine._is_restricted_category("Vinho") == True
        assert engine._is_restricted_category("Laticinio") == False
        assert engine._is_restricted_category("") == False
        assert engine._is_restricted_category(None) == False


class TestTextWrapping:
    """Testa quebra de linha."""
    
    @patch.object(VectorEngine, '_measure_text_width')
    def test_wrap_text_simple(self, mock_measure):
        """Testa quebra de texto simples."""
        engine = VectorEngine(strict_fonts=False)
        
        # Simula largura de 10px por caractere
        mock_measure.side_effect = lambda text, font, size: len(text) * 10
        
        # Largura máxima de 100px = ~10 caracteres
        lines = engine._wrap_text(
            "Palavra pequena e mais texto",
            font_path="test.ttf",
            font_size=12,
            max_width=100,
            allow_hyphenation=False
        )
        
        # Deve ter mais de uma linha
        assert len(lines) > 1
    
    @patch.object(VectorEngine, '_measure_text_width')
    def test_wrap_text_single_line(self, mock_measure):
        """Testa texto que cabe em uma linha."""
        engine = VectorEngine(strict_fonts=False)
        
        mock_measure.side_effect = lambda text, font, size: len(text) * 10
        
        lines = engine._wrap_text(
            "Hi",
            font_path="test.ttf",
            font_size=12,
            max_width=500,
            allow_hyphenation=False
        )
        
        assert len(lines) == 1
        assert lines[0] == "Hi"


class TestSVGOutput:
    """Testa exportação de SVG."""
    
    def test_to_string(self):
        """Testa conversão para string."""
        engine = VectorEngine(strict_fonts=False)
        
        svg_content = b'''<?xml version="1.0"?>
        <svg xmlns="http://www.w3.org/2000/svg">
            <text id="test">Hello</text>
        </svg>
        '''
        
        engine.load_from_string(svg_content)
        output = engine.to_string()
        
        assert isinstance(output, bytes)
        assert b"<svg" in output
        assert b"Hello" in output
    
    def test_calculate_hash(self):
        """Testa cálculo de hash de integridade."""
        engine = VectorEngine(strict_fonts=False)
        
        svg_content = b'''<svg xmlns="http://www.w3.org/2000/svg"><text>A</text></svg>'''
        engine.load_from_string(svg_content)
        
        hash1 = engine.calculate_hash()
        
        # Hash deve ser consistente
        hash2 = engine.calculate_hash()
        assert hash1 == hash2
        assert len(hash1) == 32  # MD5


class TestStyleUpdate:
    """Testa atualização de estilos CSS inline."""
    
    def test_update_style_new_property(self):
        """Testa adição de nova propriedade."""
        engine = VectorEngine(strict_fonts=False)
        
        svg_content = b'''<svg xmlns="http://www.w3.org/2000/svg">
            <text id="test" style="fill:red">Test</text>
        </svg>'''
        
        engine.load_from_string(svg_content)
        node = engine.slots["test"]
        
        engine._update_style(node, "font-size", "24px")
        
        style = node.get("style")
        assert "font-size:24px" in style
        assert "fill:red" in style
    
    def test_update_style_replace_property(self):
        """Testa substituição de propriedade existente."""
        engine = VectorEngine(strict_fonts=False)
        
        svg_content = b'''<svg xmlns="http://www.w3.org/2000/svg">
            <text id="test" style="font-size:12px;fill:red">Test</text>
        </svg>'''
        
        engine.load_from_string(svg_content)
        node = engine.slots["test"]
        
        engine._update_style(node, "font-size", "36px")
        
        style = node.get("style")
        assert "font-size:36px" in style
        assert "12px" not in style


# Pytest configuration
if __name__ == "__main__":
    pytest.main([__file__, "-v"])

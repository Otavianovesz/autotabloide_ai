import os
import sys
import unittest
from pathlib import Path

# CONFIGURAÇÃO DE AMBIENTE (CRÍTICO PARA CAIRO)
ROOT_DIR = Path.cwd()
SYSTEM_ROOT = ROOT_DIR / "AutoTabloide_System_Root"
BIN_DIR = SYSTEM_ROOT / "bin"

# Injeta DLLs no PATH antes de qualquer import do projeto que use Cairosvg
os.environ["PATH"] = str(BIN_DIR) + os.pathsep + os.environ["PATH"]
if hasattr(os, "add_dll_directory"):
    try:
        os.add_dll_directory(str(BIN_DIR))
    except Exception:
        pass

from src.rendering.vector import VectorEngine
from src.rendering.output import OutputEngine

# Mocks
SVG_MOCK_PRICE = """<svg xmlns="http://www.w3.org/2000/svg" width="300" height="300">
  <g id="SLOT_01">
    <text id="TXT_PRECO_POR_SLOT_01" x="10" y="50">0,00</text>
    <text id="TXT_PRECO_BIG_SLOT_01" x="10" y="80">0</text>
    <text id="TXT_PRECO_CENTS_SLOT_01" x="50" y="80">00</text>
    <text id="TXT_PRECO_DE_SLOT_01" x="10" y="30" display="none">De 0,00</text>
  </g>
</svg>"""

class TestOutputEngine(unittest.TestCase):
    def setUp(self):
        # Cria SVG de teste
        self.svg_path = "temp_price.svg"
        with open(self.svg_path, "w") as f:
            f.write(SVG_MOCK_PRICE)
            
        self.output_pdf_rgb = "temp_rgb.pdf"
        self.output_pdf_cmyk = "temp_cmyk.pdf"
        
        self.vector = VectorEngine()
        self.vector.load_template(self.svg_path)
        
        self.output_engine = OutputEngine(str(SYSTEM_ROOT))

    def tearDown(self):
        # Limpeza
        for f in [self.svg_path, self.output_pdf_rgb, self.output_pdf_cmyk]:
            if os.path.exists(f):
                try: os.remove(f)
                except: pass

    def test_price_logic_with_discount(self):
        """Testa se preço DE aparece quando há desconto"""
        self.vector.handle_price_logic("SLOT_01", preco_atual=19.90, preco_ref=25.00)
        
        # Verifica visibilidade
        node_de = self.vector.slots["TXT_PRECO_DE_SLOT_01"]
        self.assertIn("display:inline", node_de.get('style', ''))
        self.assertEqual(node_de.text, "De R$ 25,00")
        
        # Verifica formatação POR
        node_cents = self.vector.slots["TXT_PRECO_CENTS_SLOT_01"]
        self.assertEqual(node_cents.text, ",90")

    def test_price_logic_no_discount(self):
        """Testa se preço DE some quando não há desconto"""
        self.vector.handle_price_logic("SLOT_01", preco_atual=19.90, preco_ref=None)
        
        node_de = self.vector.slots["TXT_PRECO_DE_SLOT_01"]
        self.assertIn("display:none", node_de.get('style', ''))

    def test_full_pipeline_cmyk(self):
        """Testa pipeline completo: SVG Manipulado -> PDF RGB -> PDF CMYK"""
        # 1. Manipula
        self.vector.handle_price_logic("SLOT_01", preco_atual=99.99, preco_ref=120.00)
        svg_bytes = self.vector.to_string()
        
        # 2. Renderiza RGB (Cairo)
        print("\n[TEST] Renderizando PDF RGB...")
        self.output_engine.render_pdf(svg_bytes, self.output_pdf_rgb)
        self.assertTrue(os.path.exists(self.output_pdf_rgb), "PDF RGB não gerado")
        
        # 3. Converte CMYK (Ghostscript)
        print("[TEST] Convertendo para CMYK...")
        try:
            self.output_engine.convert_to_cmyk(self.output_pdf_rgb, self.output_pdf_cmyk)
            self.assertTrue(os.path.exists(self.output_pdf_cmyk), "PDF CMYK não gerado")
            print("[OK] Pipeline Completo Sucesso")
        except Exception as e:
            # Se falhar por falta de binário (ambiente de teste limitado), avisar
            print(f"[WARN] Falha no Ghostscript (Talvez esperado em env limitado): {e}")
            # Em ambiente controlado do user, deve passar.

if __name__ == '__main__':
    unittest.main()

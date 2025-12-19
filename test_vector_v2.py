import os
import unittest
from PIL import Image
from src.rendering.vector import VectorEngine

# Template SVG Mock para teste
SVG_MOCK = """<svg xmlns="http://www.w3.org/2000/svg" 
     width="500" height="500" viewBox="0 0 500 500">
  <g id="SLOT_01">
     <rect id="ALVO_IMAGEM" x="10" y="10" width="100" height="100" fill="#ccc" />
     <text id="TXT_NOME_PRODUTO" x="10" y="130" style="font-size:20px">NOME PRODUTO</text>
  </g>
</svg>
"""

class TestVectorEngineV2(unittest.TestCase):
    def setUp(self):
        # 1. Cria Template SVG
        with open("temp_mock_v2.svg", "w") as f:
            f.write(SVG_MOCK)
        
        # 2. Cria Imagem Dummy para PIL medir
        self.img_path = "temp_dummy.png"
        img = Image.new('RGB', (500, 500), color = 'red')
        img.save(self.img_path)

        self.engine = VectorEngine()
        self.engine.load_template("temp_mock_v2.svg")

    def tearDown(self):
        if os.path.exists("temp_mock_v2.svg"):
            os.remove("temp_mock_v2.svg")
        if os.path.exists(self.img_path):
            os.remove(self.img_path)

    def test_text_fitting_real(self):
        # Texto longo que deve reduzir a fonte (Original 20px)
        # Arial Default do PIL é pequena, mas vamos checar a redução logica
        long_text = "ARROZ TIPO 1 SUPER PREMIUM DO SUL EXTRA"
        
        # Max width pequeno para forçar redução
        success = self.engine.fit_text("TXT_NOME_PRODUTO", long_text, max_width_px=50, font_family_path="arial.ttf")
        self.assertTrue(success)

        # Verifica estilo atualizado
        node = self.engine.slots["TXT_NOME_PRODUTO"]
        style = node.get('style')
        
        import re
        match = re.search(r'font-size:(\d+)px', style)
        new_size = int(match.group(1)) if match else 20
        
        print(f"\n[TEST] Novo Font-Size (PIL Calculated): {new_size}px")
        self.assertLess(new_size, 20)

    def test_image_placement_matrix(self):
        # Slot 100x100, Imagem 500x500 (Dummy)
        # Scale deve ser 0.2
        
        success = self.engine.place_image("ALVO_IMAGEM", self.img_path, slot_w=100, slot_h=100)
        self.assertTrue(success)
        
        node = self.engine.slots["ALVO_IMAGEM"]
        transform = node.get('transform')
        print(f"\n[TEST] Matrix Result: {transform}")
        
        self.assertIn("matrix(0.2000", transform)

    def test_smart_slot_grid(self):
        # Testa a lógica de divisão para 2 imagens
        product_data = {
            'nome_sanitizado': 'Kit',
            'images': [self.img_path, self.img_path] # 2 imagens
        }
        
        # Injeta
        self.engine.handle_smart_slot("SLOT_01", product_data)
        
        # Verifica se ALVO_IMAGEM sumiu e ALVO_IMAGEM_0 / _1 apareceram
        self.assertTrue("ALVO_IMAGEM_0" in self.engine.slots)
        self.assertTrue("ALVO_IMAGEM_1" in self.engine.slots)
        print("\n[TEST] Grid split successful (found sub-targets)")

if __name__ == '__main__':
    unittest.main()

import os
import unittest
from src.rendering.vector import VectorEngine

# Template SVG Mock para teste
SVG_MOCK = """<svg xmlns="http://www.w3.org/2000/svg" 
     xmlns:inkscape="http://www.inkscape.org/namespaces/inkscape"
     width="500" height="500" viewBox="0 0 500 500">
  <g id="SLOT_01" inkscape:label="Slot 1">
     <rect id="ALVO_IMAGEM" x="10" y="10" width="100" height="100" fill="#ccc" />
     <text id="TXT_NOME_PRODUTO" x="10" y="130" font-size="20px" style="font-size:20px">NOME PRODUTO</text>
  </g>
</svg>
"""

class TestVectorEngine(unittest.TestCase):
    def setUp(self):
        # Cria arquivo temporário
        with open("temp_mock.svg", "w") as f:
            f.write(SVG_MOCK)
        self.engine = VectorEngine()
        self.engine.load_template("temp_mock.svg")

    def tearDown(self):
        if os.path.exists("temp_mock.svg"):
            os.remove("temp_mock.svg")

    def test_namespace_purging(self):
        # Verifica se atributos inkscape sumiram
        slot = self.engine.get_slot("SLOT_01")
        self.assertIsNotNone(slot)
        # O atributo inkscape:label deve ter sumido (ou ao menos o namespace carregado deve estar limpo)
        # Lxml as vezes preserva se o namespace map estiver lá, mas o purge deve remover atributos com ":"
        for k in slot.attrib:
            self.assertNotIn("inkscape", k)
            self.assertNotIn("}", k) # Verifica URI expandida também

    def test_text_fitting(self):
        # Texto longo que deve reduzir a fonte (Original 20px)
        long_text = "ARROZ TIPO 1 SUPER PREMIUM DO SUL"
        # Com 20px, largura estimada seria ~20 * len * 0.6 = 20 * 33 * 0.6 = 396
        # Vamos forçar um max_width pequeno de 100
        self.engine.fit_text("SLOT_01", "TXT_NOME_PRODUTO", long_text, max_width=100)
        
        # Recupera o elemento para verificar novo font-size
        # Precisamos navegar no XML string ou objeto
        root = self.engine.root
        # Acha texto
        txt_node = None
        for elem in root.iter():
            if elem.get('id') == "TXT_NOME_PRODUTO":
                txt_node = elem
                break
        
        style = txt_node.get('style')
        # Extrai font-size
        fs = self.engine._extract_style_value(style, 'font-size')
        print(f"\n[TEST] Novo Font-Size: {fs}px")
        
        self.assertLess(fs, 20.0, "Font-size deveria ter diminuído")
        self.assertGreater(fs, 1.0, "Font-size não deveria ser zero")

    def test_image_placement(self):
        # Alvo original: x=10, y=10, w=100, h=100.
        # Imagem assumida quadrada 1000x1000.
        # Scale deve ser 100/1000 = 0.1
        # Offset deve ser 0 (já que aspect ratio é igual)
        # Matrix: 0.1, 0, 0, 0.1, 10, 10
        
        self.engine.place_image("SLOT_01", "path/to/img.png")
        
        root = self.engine.root
        img_node = None
        for elem in root.iter():
            # O rect vira image e preserva ID
            if elem.get('id') == "ALVO_IMAGEM":
                img_node = elem
                break
        
        self.assertTrue(img_node.tag.endswith('image'))
        transform = img_node.get('transform')
        print(f"\n[TEST] Matrix: {transform}")
        
        self.assertIn("matrix(0.1000", transform) # Verifica escala
        self.assertIn(",10.0000", transform) # Verifica translação X (offset + x original)

if __name__ == '__main__':
    unittest.main()

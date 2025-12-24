import os
import re
import unittest
from src.rendering.vector import VectorEngine

# Template SVG Mock para teste
SVG_MOCK = """<svg xmlns="http://www.w3.org/2000/svg" 
     xmlns:inkscape="http://www.inkscape.org/namespaces/inkscape"
     width="500" height="500" viewBox="0 0 500 500">
  <g id="SLOT_01" inkscape:label="Slot 1">
     <rect id="ALVO_IMAGEM" x="10" y="10" width="100" height="100" fill="#ccc" />
     <text id="TXT_NOME_PRODUTO" x="10" y="130" font-size="20px" style="font-size:20px">NOME PRODUTO</text>
     <text id="TXT_PRECO_INT" x="10" y="160" style="font-size:24px">10</text>
     <text id="TXT_PRECO_DEC" x="50" y="160" style="font-size:12px">,90</text>
  </g>
</svg>
"""

class TestVectorEngine(unittest.TestCase):
    def setUp(self):
        # Cria arquivo temporário
        with open("temp_mock.svg", "w") as f:
            f.write(SVG_MOCK)
        # Usa strict_fonts=False para evitar erros de fonte ausente
        self.engine = VectorEngine(strict_fonts=False)
        self.engine.load_template("temp_mock.svg")

    def tearDown(self):
        if os.path.exists("temp_mock.svg"):
            os.remove("temp_mock.svg")

    def test_namespace_purging(self):
        """Verifica se atributos inkscape sumiram após purge"""
        # Usa self.engine.slots ao invés de get_slot()
        slot = self.engine.slots.get("SLOT_01")
        self.assertIsNotNone(slot, "SLOT_01 não encontrado")
        
        # O atributo inkscape:label deve ter sumido
        for k in slot.attrib:
            self.assertNotIn("inkscape", k, f"Atributo inkscape ainda presente: {k}")
        
        print("\n[TEST] Namespace purging: OK")

    def test_text_fitting(self):
        """Testa algoritmo de redução de fonte"""
        long_text = "ARROZ TIPO 1 SUPER PREMIUM DO SUL ESPECIAL"
        
        # API correta: fit_text(node_id, text, max_width_px, ...)
        result = self.engine.fit_text(
            node_id="TXT_NOME_PRODUTO",
            text=long_text,
            max_width_px=100,  # Largura pequena para forçar redução
            allow_shrink=True
        )
        
        self.assertTrue(result, "fit_text deveria retornar True")
        
        # Verifica se o texto foi atualizado
        txt_node = self.engine.slots.get("TXT_NOME_PRODUTO")
        self.assertIsNotNone(txt_node, "TXT_NOME_PRODUTO não encontrado")
        self.assertEqual(txt_node.text, long_text, "Texto não foi aplicado")
        
        # Extrai font-size do style
        style = txt_node.get('style', '')
        match = re.search(r'font-size:\s*([\d.]+)', style)
        
        if match:
            new_size = float(match.group(1))
            print(f"\n[TEST] Novo Font-Size: {new_size}px (original 20px)")
            self.assertLessEqual(new_size, 20.0, "Font-size deveria ter diminuído ou mantido")
        
        print("\n[TEST] Text fitting: OK")

    def test_price_logic(self):
        """Testa lógica de preços De/Por"""
        self.engine.handle_price_logic(
            slot_suffix="",  # Sem sufixo = global
            preco_atual=9.90,
            preco_ref=12.50  # Preço anterior
        )
        
        # Verifica se preços foram preenchidos
        int_node = self.engine.slots.get("TXT_PRECO_INT")
        dec_node = self.engine.slots.get("TXT_PRECO_DEC")
        
        self.assertIsNotNone(int_node)
        self.assertIsNotNone(dec_node)
        
        # Mostra valores
        print(f"\n[TEST] Preço INT: {int_node.text}")
        print(f"[TEST] Preço DEC: {dec_node.text}")
        
        # Verifica formato
        self.assertEqual(int_node.text, "9", f"Esperado '9', obtido '{int_node.text}'")
        self.assertIn(",90", dec_node.text, f"Esperado ',90' no centavos, obtido '{dec_node.text}'")
        
        print("\n[TEST] Price logic: OK")

    def test_slots_indexing(self):
        """Verifica se todos os slots foram indexados corretamente"""
        expected_ids = ["SLOT_01", "ALVO_IMAGEM", "TXT_NOME_PRODUTO", "TXT_PRECO_INT", "TXT_PRECO_DEC"]
        
        for slot_id in expected_ids:
            self.assertIn(slot_id, self.engine.slots, f"{slot_id} não foi indexado")
        
        print(f"\n[TEST] Slots indexados: {len(self.engine.slots)}")
        print("\n[TEST] Slots indexing: OK")

    def test_render_frame(self):
        """Testa geração de frame para exportação batch"""
        slot_data = {
            "SLOT_01": {
                "TXT_NOME_PRODUTO": "Produto Teste",
                "TXT_PRECO_INT": "5",
                "TXT_PRECO_DEC": ",99"
            }
        }
        
        svg_bytes = self.engine.render_frame(slot_data)
        
        self.assertIsInstance(svg_bytes, bytes)
        self.assertGreater(len(svg_bytes), 100, "SVG muito curto")
        self.assertIn(b"Produto Teste", svg_bytes, "Nome do produto não encontrado no SVG")
        
        print(f"\n[TEST] Frame gerado: {len(svg_bytes)} bytes")
        print("\n[TEST] Render frame: OK")


if __name__ == '__main__':
    unittest.main(verbosity=2)

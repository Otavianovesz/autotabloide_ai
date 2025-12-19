import unittest
import multiprocessing
import queue
import time
from src.ai.sentinel import SentinelProcess, GRAMMAR_GBNF

# Mock Configuration
MOCK_CONFIG = {
    "model_path": "dummy/path/to/model.gguf",
    "temp_dir": "./temp_test"
}

class TestSentinel(unittest.TestCase):
    def test_grammar_string(self):
        """Verifica se a gramática GBNF está definida e parece válida (smoke test)."""
        self.assertIn("root ::=", GRAMMAR_GBNF)
        self.assertIn("object ::=", GRAMMAR_GBNF)
        self.assertIn("string", GRAMMAR_GBNF)

    def test_process_lifecycle(self):
        """
        Testa se o processo inicia e responde a STOP.
        Nota: Como não temos o modelo, ele vai logar erro/aviso mas deve rodar o loop.
        """
        in_q = multiprocessing.Queue()
        out_q = multiprocessing.Queue()
        
        sentinel = SentinelProcess(in_q, out_q, MOCK_CONFIG)
        sentinel.start()
        
        self.assertTrue(sentinel.is_alive())
        
        # Envia STOP
        in_q.put({"type": "STOP"})
        
        # Espera terminar (timeout 2s)
        sentinel.join(timeout=3)
        
        self.assertFalse(sentinel.is_alive(), "Processo Sentinel não terminou graciosamente.")

    def test_sanitize_fallback(self):
        """Testa se o fallback (sem IA) funciona quando modelo falta."""
        in_q = multiprocessing.Queue()
        out_q = multiprocessing.Queue()
        
        sentinel = SentinelProcess(in_q, out_q, MOCK_CONFIG)
        sentinel.start()
        
        # Solicita sanitização
        task = {"type": "SANITIZE", "id": "123", "raw_text": "teste 123"}
        in_q.put(task)
        
        # Espera resultado
        try:
            result = out_q.get(timeout=3)
            self.assertEqual(result["type"], "SANITIZE_RESULT")
            self.assertEqual(result["id"], "123")
            # Sem modelo, deve retornar o original
            self.assertEqual(result["data"]["nome_sanitizado"], "teste 123")
        except queue.Empty:
            self.fail("Sentinel não respondeu ao pedido de sanitize (Fallback).")
        finally:
            in_q.put({"type": "STOP"})
            sentinel.join()

if __name__ == '__main__':
    unittest.main()

import os
import time
import json
import hashlib
import multiprocessing
import logging
from typing import Optional, Dict, Any
from queue import Empty

# Dependências Críticas (Devem ser tratadas com try/import para evitar crash no boot da UI)
try:
    from llama_cpp import Llama, LlamaGrammar
    HAS_LLAMA = True
except ImportError:
    HAS_LLAMA = False

try:
    from playwright.sync_api import sync_playwright, Playwright, Browser
    HAS_PLAYWRIGHT = True
except ImportError:
    HAS_PLAYWRIGHT = False

# Configuração de Logs do Processo Isolado
logger = logging.getLogger("Sentinel")

# Gramática GBNF para Forçar JSON Estrito (Llama-3)
# Define que o output DEVE ser um objeto com chaves específicas.
GRAMMAR_GBNF = r"""
root ::= object
object ::= "{" space pair_list "}" space
pair_list ::= pair ("," space pair)*
pair ::= string ":" space value
string ::= "\"" [^"]* "\""
value ::= string | number | "null"
number ::= [0-9]+ ("." [0-9]+)?
space ::= [ \t\n]*
"""

class TheHunter:
    """
    Agente de Navegação Autônoma (Headless Browser).
    Responsável por encontrar ativos visuais na internet selvagem.
    
    REFATORADO: Browser agora persiste entre buscas para evitar overhead 
    de iniciar/encerrar Chromium dezenas de vezes em lote.
    """
    USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    
    def __init__(self, download_path: str):
        self.download_path = download_path
        os.makedirs(download_path, exist_ok=True)
        self._playwright: Optional[Playwright] = None
        self._browser: Optional[Browser] = None
        self._is_initialized = False

    def _ensure_browser(self) -> bool:
        """Garante que o browser está iniciado. Retorna False se falhar."""
        if not HAS_PLAYWRIGHT:
            logger.error("Playwright não instalado.")
            return False
        
        if self._is_initialized and self._browser and self._browser.is_connected():
            return True
        
        try:
            logger.info("Hunter: Inicializando browser persistente...")
            self._playwright = sync_playwright().start()
            self._browser = self._playwright.chromium.launch(headless=True)
            self._is_initialized = True
            logger.info("Hunter: Browser Chromium pronto.")
            return True
        except Exception as e:
            logger.error(f"Falha ao iniciar browser: {e}")
            return False

    def shutdown(self):
        """Encerra o browser de forma limpa."""
        if self._browser:
            try:
                self._browser.close()
            except:
                pass
        if self._playwright:
            try:
                self._playwright.stop()
            except:
                pass
        self._is_initialized = False
        logger.info("Hunter: Browser encerrado.")

    def search_and_download(self, query: str) -> Optional[str]:
        """Busca imagem no Google. Abre nova aba, não novo browser."""
        if not self._ensure_browser():
            return None
        
        page = None
        try:
            context = self._browser.new_context(user_agent=self.USER_AGENT)
            page = context.new_page()
            
            # Google Images URL 
            search_url = f"https://www.google.com/search?q={query}&tbm=isch&tbs=isz:l"
            
            try:
                page.goto(search_url, timeout=15000)
            except Exception as e:
                logger.warning(f"Timeout ou erro ao carregar Google: {e}")
                return None
            
            found_src = None
            
            # Estratégia mais robusta: Pegar todas as imagens visíveis e filtrar
            # Evita seletores específicos como 'data-ri' que mudam
            try:
                # Espera carregar imagens
                page.wait_for_selector('img', timeout=5000)
                time.sleep(1) # Dar tempo para lazy load
                
                # Tenta clicar no primeiro resultado (estrutura genérica)
                first_result = page.query_selector('div[data-ri="0"]')
                if first_result:
                    first_result.click()
                    time.sleep(1.5) # Wait for side panel
                
                # Itera todas as imagens buscando uma externa
                imgs = page.query_selector_all('img')
                for img in imgs:
                    src = img.get_attribute('src')
                    if not src:
                        continue
                    # Filtrar URLs válidas (http, não são do google/gstatic)
                    if src.startswith('http') and 'google' not in src.lower() and 'gstatic' not in src.lower():
                        found_src = src
                        break
                
                if not found_src:
                    # Fallback: tenta pegar do data attribute ou srcset
                    for img in imgs:
                        srcset = img.get_attribute('data-src') or img.get_attribute('data-iurl')
                        if srcset and srcset.startswith('http'):
                            found_src = srcset
                            break

            except Exception as e:
                logger.warning(f"Erro durante extração de página: {e}")

            if found_src:
                try:
                    import requests
                    headers = {'User-Agent': self.USER_AGENT}
                    response = requests.get(found_src, headers=headers, timeout=10)
                    
                    if response.status_code == 200:
                        ext = "jpg"
                        ct = response.headers.get('content-type', '')
                        if 'png' in ct: ext = 'png'
                        elif 'webp' in ct: ext = 'webp'
                        elif 'jpeg' in ct: ext = 'jpg'
                        
                        filename = f"{hashlib.md5(query.encode()).hexdigest()}.{ext}"
                        filepath = os.path.join(self.download_path, filename)
                        
                        with open(filepath, "wb") as f:
                            f.write(response.content)
                            
                        logger.info(f"Hunter: Imagem capturada -> {filepath}")
                        return filepath
                except Exception as e:
                    logger.warning(f"Falha no download da imagem: {e}")
                
        except Exception as e:
            logger.error(f"Hunter falhou na caçada: {e}")
        finally:
            if page:
                try:
                    page.close()
                except:
                    pass
            
        return None

class SentinelProcess(multiprocessing.Process):
    """
    O 'Sidecar' Cognitivo.
    Roda em um núcleo separado da CPU para não bloquear a renderização da UI (Flet).
    """

    def __init__(self, input_queue: multiprocessing.Queue, output_queue: multiprocessing.Queue, config: Dict):
        super().__init__(name="Sentinel-AI-Core")
        self.input_queue = input_queue
        self.output_queue = output_queue
        self.config = config
        self._running = True
        self.llm: Optional[Any] = None
        self._hunter: Optional[TheHunter] = None

    def run(self):
        """Loop principal do processo isolado."""
        self._setup_logging()
        logger.info("Sentinel: Inicializando subsistemas...")

        # 1. Warmup da IA (Carregamento do Modelo)
        if HAS_LLAMA:
            model_path = self.config.get("model_path")
            if model_path and os.path.exists(model_path):
                try:
                    logger.info(f"Carregando Llama-3 de: {model_path}")
                    self.llm = Llama(
                        model_path=model_path,
                        n_ctx=2048,
                        n_gpu_layers=-1, 
                        verbose=False
                    )
                    logger.info("Sentinel: Córtex Neural Ativo.")
                except Exception as e:
                    logger.error(f"Falha crítica ao carregar modelo: {e}")
                    self.output_queue.put({"type": "ERROR", "msg": f"Falha no motor de IA: {e}"})
            else:
                logger.warning(f"Modelo não encontrado em {model_path}. Modo 'Burro' ativado.")
        else:
             logger.warning("Biblioteca llama_cpp não instalada.")

        # 2. Inicializa Hunter com browser persistente
        output_dir = self.config.get("temp_dir", "./temp")
        self._hunter = TheHunter(output_dir)

        # 3. Loop de Eventos
        while self._running:
            try:
                task = self.input_queue.get(timeout=1.0)
                
                if task["type"] == "STOP":
                    logger.info("Sentinel: Recebido comando de parada.")
                    self._running = False
                    break
                
                elif task["type"] == "SANITIZE":
                    self._handle_sanitize(task)
                
                elif task["type"] == "HUNT_IMAGE":
                    self._handle_hunt(task)

            except Empty:
                continue
            except Exception as e:
                logger.error(f"Erro no loop do Sentinel: {e}")
                self.output_queue.put({"type": "ERROR", "task_id": task.get("id"), "msg": str(e)})

        # Cleanup ao sair
        if self._hunter:
            self._hunter.shutdown()
        logger.info("Sentinel: Desligando.")

    def _handle_sanitize(self, task):
        """Executa a inferência LLM para limpar dados."""
        if not self.llm:
            result = {
                "nome_sanitizado": task.get("raw_text", ""),
                "marca": None,
                "peso": None,
                "unidade": None
            }
            self.output_queue.put({"type": "SANITIZE_RESULT", "id": task["id"], "data": result})
            return

        raw_text = task["raw_text"]
        prompt = f"""<|begin_of_text|><|start_header_id|>system<|end_header_id|>
Você é um assistente especializado em cadastro de produtos de supermercado.
Sua tarefa é extrair: nome limpo (title case), marca, peso numérico e unidade.
Entrada: {raw_text}
Responda APENAS o JSON.<|eot_id|><|start_header_id|>user<|end_header_id|>
Analise: {raw_text}<|eot_id|><|start_header_id|>assistant<|end_header_id|>"""

        try:
            grammar = LlamaGrammar.from_string(GRAMMAR_GBNF)
            
            output = self.llm(
                prompt,
                max_tokens=128,
                temperature=0.1,
                grammar=grammar,
                stop=["<|eot_id|>"]
            )
            
            json_str = output['choices'][0]['text']
            parsed_data = json.loads(json_str)
            
            self.output_queue.put({"type": "SANITIZE_RESULT", "id": task["id"], "data": parsed_data})
            
        except Exception as e:
            logger.error(f"Falha na inferência: {e}")
            self.output_queue.put({"type": "ERROR", "id": task["id"], "msg": "Erro de Inferência"})

    def _handle_hunt(self, task):
        """Invoca o Hunter para buscar imagens (browser já persistente)."""
        term = task["term"]
        
        path = self._hunter.search_and_download(term)
        
        if path:
            self.output_queue.put({"type": "HUNT_RESULT", "id": task["id"], "path": path})
        else:
            self.output_queue.put({"type": "HUNT_FAIL", "id": task["id"]})

    def _setup_logging(self):
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

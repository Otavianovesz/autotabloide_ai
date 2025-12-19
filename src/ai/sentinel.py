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
    from playwright.sync_api import sync_playwright
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
    """
    def __init__(self, download_path: str):
        self.download_path = download_path
        os.makedirs(download_path, exist_ok=True)

    def search_and_download(self, query: str) -> Optional[str]:
        if not HAS_PLAYWRIGHT:
            logger.error("Playwright não instalado.")
            return None

        user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        
        try:
            with sync_playwright() as p:
                # Launch Chromium (Headless)
                browser = p.chromium.launch(headless=True)
                context = browser.new_context(user_agent=user_agent)
                page = context.new_page()
                
                # Google Images URL (Query params para imagens grandes e fundo branco se possível)
                # tbm=isch (Image Search), tbs=isz:l (Large images)
                search_url = f"https://www.google.com/search?q={query}&tbm=isch&tbs=isz:l"
                
                try:
                    page.goto(search_url, timeout=15000)
                except Exception as e:
                    logger.warning(f"Timeout ou erro ao carregar Google: {e}")
                    browser.close()
                    return None
                
                # Espera carregar seletores de imagem
                # Nota: O seletor do Google muda. Vamos tentar pegar o primeiro resultado 'img' relevante.
                # Estratégia robusta simplificada: Clicar na primeira imagem para abrir o painel lateral
                try:
                    # Seletor genérico de thumbnail de resultado (pode mudar)
                    # Tenta clicar no primeiro div que parece ser um resultado
                    # O Google usa estruturas complexas, mas geralmente islib ou similar
                    # Vamos tentar pegar qualquer IMG dentro da área de resultados principal
                    # Fallback simples: pegar o src da primeira imagem grande que aparecer no DOM
                    
                    found_src = None
                    
                    # Tenta clicar no primeiro resultado
                    # data-ri="0" é comum para o primeiro item
                    first_result = page.query_selector('div[data-ri="0"]')
                    if first_result:
                        first_result.click()
                        time.sleep(2) # Wait for side panel
                        
                        # Tenta achar imagem grande no painel lateral
                        # Geralmente é uma img com src http (não base64 data:image)
                        # Vamos iterar imagens visíveis
                        imgs = page.query_selector_all('img')
                        for img in imgs:
                            src = img.get_attribute('src')
                            if src and src.startswith('http') and not 'google' in src and not 'gstatic' in src:
                                found_src = src
                                break
                    
                    if not found_src:
                         # Fallback bruto: Pega qualquer coisa que não seja icone
                         imgs = page.query_selector_all('div[data-ri="0"] img')
                         if imgs:
                             found_src = imgs[0].get_attribute('src')

                    if found_src:
                        import requests
                        # Download com user agent fake para evitar bloqueio do site destino
                        headers = {'User-Agent': user_agent}
                        response = requests.get(found_src, headers=headers, timeout=10)
                        
                        if response.status_code == 200:
                            ext = "jpg" # Default
                            ct = response.headers.get('content-type', '')
                            if 'png' in ct: ext = 'png'
                            elif 'webp' in ct: ext = 'webp'
                            elif 'jpeg' in ct: ext = 'jpg'
                            
                            filename = f"{hashlib.md5(query.encode()).hexdigest()}.{ext}"
                            filepath = os.path.join(self.download_path, filename)
                            
                            with open(filepath, "wb") as f:
                                f.write(response.content)
                                
                            logger.info(f"Hunter: Imagem capturada -> {filepath}")
                            browser.close()
                            return filepath
                                
                except Exception as e:
                    logger.warning(f"Erro durante extração de página: {e}")

                browser.close()
                
        except Exception as e:
            logger.error(f"Hunter falhou na caçada: {e}")
            
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
        self.llm: Optional[Any] = None # Type Any pq Llama pode não ser importado

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
                    # n_gpu_layers=-1 joga tudo para VRAM se disponível, senão CPU
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

        # 2. Loop de Eventos
        while self._running:
            try:
                # Timeout evita bloqueio infinito e permite checar _running
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

        logger.info("Sentinel: Desligando.")

    def _handle_sanitize(self, task):
        """Executa a inferência LLM para limpar dados."""
        if not self.llm:
            # Fallback se não houver IA: Retorna o original
            result = {
                "nome_sanitizado": task.get("raw_text", ""),
                "marca": None,
                "peso": None,
                "unidade": None
            }
            self.output_queue.put({"type": "SANITIZE_RESULT", "id": task["id"], "data": result})
            return

        raw_text = task["raw_text"]
        # Prompt Engenharia para Llama-3 (Instruct Format)
        prompt = f"""<|begin_of_text|><|start_header_id|>system<|end_header_id|>
Você é um assistente especializado em cadastro de produtos de supermercado.
Sua tarefa é extrair: nome limpo (title case), marca, peso numérico e unidade.
Entrada: {raw_text}
Responda APENAS o JSON.<|eot_id|><|start_header_id|>user<|end_header_id|>
Analise: {raw_text}<|eot_id|><|start_header_id|>assistant<|end_header_id|>"""

        try:
            # GBNF é a chave aqui para robustez
            grammar = LlamaGrammar.from_string(GRAMMAR_GBNF)
            
            output = self.llm(
                prompt,
                max_tokens=128,
                temperature=0.1, # Baixa criatividade, alta precisão
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
        """Invoca o Hunter para buscar imagens."""
        term = task["term"]
        output_dir = self.config.get("temp_dir", "./temp")
        
        hunter = TheHunter(output_dir)
        path = hunter.search_and_download(term)
        
        if path:
            self.output_queue.put({"type": "HUNT_RESULT", "id": task["id"], "path": path})
        else:
            self.output_queue.put({"type": "HUNT_FAIL", "id": task["id"]})

    def _setup_logging(self):
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

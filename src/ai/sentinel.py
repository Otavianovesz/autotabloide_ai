"""
AutoTabloide AI - Sentinel Process (Cognitive Sidecar)
========================================================
Processo isolado para operações cognitivas conforme Vol. IV.
REFATORADO: Protocolo de Busca em Cascata com fallbacks.
"""

import os
import time
import json
import hashlib
import multiprocessing
import logging
from pathlib import Path
from typing import Optional, Dict, Any, List, Callable
from queue import Empty

# Dependências Críticas
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

try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

# Configuração de Logs do Processo Isolado
logger = logging.getLogger("Sentinel")

# Gramática GBNF para Forçar JSON Estrito
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
    
    PROTOCOLO CAÇADOR RESILIENTE: Implementa estratégia de busca em cascata
    com múltiplos fallbacks. Se Google falhar, tenta DuckDuckGo, Bing, etc.
    Inclui verificação de integridade de imagem.
    
    Passos 25, 28-29: Usa hunter_utils para rotação UA, captcha e validação.
    """
    
    # Configurações de validação de imagem
    MIN_IMAGE_WIDTH = 300
    MIN_IMAGE_HEIGHT = 300
    MAX_FILE_SIZE_MB = 10
    
    def __init__(self, download_path: str):
        self.download_path = download_path
        os.makedirs(download_path, exist_ok=True)
        self._playwright: Optional[Playwright] = None
        self._browser: Optional[Browser] = None
        self._is_initialized = False
        
        # Integração com hunter_utils (Passos 25, 28-29)
        try:
            from src.scraping.hunter_utils import (
                get_user_agent_rotator,
                HunterImageValidator,
                detect_captcha
            )
            self._ua_rotator = get_user_agent_rotator()
            self._image_validator = HunterImageValidator()
            self._detect_captcha = detect_captcha
            logger.info("Hunter utils integrado: UA rotation, captcha detection, image validation")
        except ImportError:
            # Fallback se módulo não disponível
            self._ua_rotator = None
            self._image_validator = None
            self._detect_captcha = None
            logger.warning("hunter_utils não disponível, usando fallback")
    
    @property
    def USER_AGENT(self) -> str:
        """Retorna User-Agent (rotativo se disponível)."""
        if self._ua_rotator:
            return self._ua_rotator.get_random()
        return "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

    def _ensure_browser(self) -> bool:
        """Garante que o browser está iniciado."""
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

    # ==========================================================================
    # PROTOCOLO CAÇADOR RESILIENTE: Busca em Cascata
    # ==========================================================================

    def search_and_download(self, query: str) -> Optional[str]:
        """
        Estratégia de busca em cascata com múltiplos fallbacks.
        Tenta várias fontes até conseguir uma imagem válida.
        """
        strategies: List[Callable[[str], Optional[str]]] = [
            self._hunt_google_images_structure_a,
            self._hunt_google_images_structure_b,
            self._hunt_duckduckgo,
            self._hunt_bing_images,
        ]

        for strategy in strategies:
            try:
                logger.info(f"Hunter: Tentando estratégia {strategy.__name__} para '{query[:30]}...'")
                result = strategy(query)
                
                if result and self._verify_image_integrity(result):
                    logger.info(f"Hunter: Sucesso com {strategy.__name__}")
                    return result
                elif result:
                    logger.warning(f"Hunter: {strategy.__name__} retornou imagem inválida")
                    # Remove arquivo inválido
                    try:
                        os.remove(result)
                    except:
                        pass
                        
            except Exception as e:
                logger.warning(f"Hunter: Estratégia {strategy.__name__} falhou: {e}")
                continue

        logger.error("Hunter: Todas as estratégias falharam.")
        return None

    def _hunt_google_images_structure_a(self, query: str) -> Optional[str]:
        """Estrutura A: Google Images layout moderno."""
        if not self._ensure_browser():
            return None
        
        page = None
        try:
            context = self._browser.new_context(user_agent=self.USER_AGENT)
            page = context.new_page()
            
            search_url = f"https://www.google.com/search?q={query}&tbm=isch&tbs=isz:l"
            page.goto(search_url, timeout=15000)
            page.wait_for_selector('img', timeout=5000)
            time.sleep(1)
            
            # Tenta clicar no primeiro resultado
            first_result = page.query_selector('div[data-ri="0"]')
            if first_result:
                first_result.click()
                time.sleep(1.5)
            
            # Busca imagem de alta resolução
            found_src = self._extract_image_url(page)
            
            if found_src:
                return self._download_image(found_src, query)
                
        except Exception as e:
            logger.debug(f"Google A falhou: {e}")
        finally:
            if page:
                try:
                    page.close()
                except:
                    pass
        return None

    def _hunt_google_images_structure_b(self, query: str) -> Optional[str]:
        """Estrutura B: Google Images layout alternativo/antigo."""
        if not self._ensure_browser():
            return None
        
        page = None
        try:
            context = self._browser.new_context(user_agent=self.USER_AGENT)
            page = context.new_page()
            
            # URL alternativa
            search_url = f"https://www.google.com/search?q={query}+produto&tbm=isch"
            page.goto(search_url, timeout=15000)
            page.wait_for_selector('img', timeout=5000)
            time.sleep(1.5)
            
            # Tenta extrair de data attributes
            imgs = page.query_selector_all('img[data-iurl], img[data-src]')
            for img in imgs:
                src = img.get_attribute('data-iurl') or img.get_attribute('data-src')
                if src and src.startswith('http') and 'google' not in src.lower():
                    return self._download_image(src, query)
            
            # Fallback: qualquer imagem externa
            found_src = self._extract_image_url(page)
            if found_src:
                return self._download_image(found_src, query)
                
        except Exception as e:
            logger.debug(f"Google B falhou: {e}")
        finally:
            if page:
                try:
                    page.close()
                except:
                    pass
        return None

    def _hunt_duckduckgo(self, query: str) -> Optional[str]:
        """DuckDuckGo Images - HTML mais simples, menos bloqueios."""
        if not self._ensure_browser():
            return None
        
        page = None
        try:
            context = self._browser.new_context(user_agent=self.USER_AGENT)
            page = context.new_page()
            
            # DuckDuckGo Images
            search_url = f"https://duckduckgo.com/?q={query}&iax=images&ia=images"
            page.goto(search_url, timeout=15000)
            page.wait_for_selector('img', timeout=8000)
            time.sleep(2)  # DuckDuckGo carrega via JS
            
            # Tenta tiles de imagem
            tiles = page.query_selector_all('.tile--img img, img.tile--img__media')
            for tile in tiles[:5]:
                src = tile.get_attribute('src') or tile.get_attribute('data-src')
                if src and src.startswith('http'):
                    result = self._download_image(src, query)
                    if result:
                        return result
            
            # Fallback genérico
            found_src = self._extract_image_url(page)
            if found_src:
                return self._download_image(found_src, query)
                
        except Exception as e:
            logger.debug(f"DuckDuckGo falhou: {e}")
        finally:
            if page:
                try:
                    page.close()
                except:
                    pass
        return None

    def _hunt_bing_images(self, query: str) -> Optional[str]:
        """Bing Images - Último recurso."""
        if not self._ensure_browser():
            return None
        
        page = None
        try:
            context = self._browser.new_context(user_agent=self.USER_AGENT)
            page = context.new_page()
            
            search_url = f"https://www.bing.com/images/search?q={query}&qft=+filterui:imagesize-large"
            page.goto(search_url, timeout=15000)
            page.wait_for_selector('img', timeout=5000)
            time.sleep(1)
            
            # Bing usa .mimg para miniaturas
            imgs = page.query_selector_all('img.mimg, a.iusc img')
            for img in imgs[:5]:
                src = img.get_attribute('src') or img.get_attribute('data-src')
                if src and src.startswith('http') and 'bing' not in src.lower():
                    result = self._download_image(src, query)
                    if result:
                        return result
            
        except Exception as e:
            logger.debug(f"Bing falhou: {e}")
        finally:
            if page:
                try:
                    page.close()
                except:
                    pass
        return None

    def _extract_image_url(self, page) -> Optional[str]:
        """Extrai URL de imagem válida da página."""
        try:
            imgs = page.query_selector_all('img')
            for img in imgs:
                src = img.get_attribute('src')
                if not src:
                    continue
                # Filtrar URLs válidas
                if (src.startswith('http') and 
                    'google' not in src.lower() and 
                    'gstatic' not in src.lower() and
                    'bing' not in src.lower() and
                    not src.startswith('data:')):
                    return src
        except:
            pass
        return None

    def _download_image(self, url: str, query: str) -> Optional[str]:
        """Baixa imagem e salva no disco."""
        try:
            import requests
            headers = {'User-Agent': self.USER_AGENT}
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code != 200:
                return None
            
            # Determina extensão
            ext = "jpg"
            ct = response.headers.get('content-type', '')
            if 'png' in ct: ext = 'png'
            elif 'webp' in ct: ext = 'webp'
            elif 'jpeg' in ct: ext = 'jpg'
            
            filename = f"{hashlib.md5(query.encode()).hexdigest()}.{ext}"
            filepath = Path(self.download_path) / filename
            
            with open(filepath, "wb") as f:
                f.write(response.content)
            
            return filepath
            
        except Exception as e:
            logger.debug(f"Download falhou: {e}")
            return None

    # ==========================================================================
    # AUTOAUDITORIA VISUAL: Verificação de Integridade
    # ==========================================================================

    def _verify_image_integrity(self, path: str) -> bool:
        """
        Autoauditoria Visual: Verifica se o arquivo baixado é uma imagem válida.
        
        Checagens:
        1. Arquivo existe e tem tamanho > 0
        2. PIL consegue abrir (não corrompido)
        3. Dimensões mínimas (300x300)
        4. Não é muito grande (< 10MB)
        """
        if not HAS_PIL:
            logger.warning("PIL não instalado - pulando verificação de integridade")
            return os.path.exists(path) and os.path.getsize(path) > 0
        
        try:
            # 1. Arquivo existe
            if not os.path.exists(path):
                logger.warning("Verificação: Arquivo não existe")
                return False
            
            # 2. Tamanho do arquivo
            file_size = os.path.getsize(path)
            if file_size == 0:
                logger.warning("Verificação: Arquivo vazio (0 bytes)")
                return False
            
            if file_size > self.MAX_FILE_SIZE_MB * 1024 * 1024:
                logger.warning(f"Verificação: Arquivo muito grande ({file_size / 1024 / 1024:.1f}MB)")
                return False
            
            # 3. Validar com PIL
            with Image.open(path) as img:
                img.verify()  # Checa se não está corrompido
            
            # Reabre para checar dimensões (verify() deixa o arquivo inconsistente)
            with Image.open(path) as img:
                width, height = img.size
                
                if width < self.MIN_IMAGE_WIDTH or height < self.MIN_IMAGE_HEIGHT:
                    logger.warning(f"Verificação: Imagem muito pequena ({width}x{height})")
                    return False
            
            logger.debug(f"Verificação: Imagem válida ({width}x{height}, {file_size/1024:.1f}KB)")
            return True
            
        except Exception as e:
            logger.warning(f"Verificação: Imagem inválida - {e}")
            return False


class SentinelProcess(multiprocessing.Process):
    """
    O 'Sidecar' Cognitivo.
    Roda em um núcleo separado da CPU para não bloquear a renderização da UI.
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
        
        self._load_llm()
        self._hunter = TheHunter(self.config.get("temp_dir", "/tmp/hunter"))
        
        logger.info("Sentinel: Entrando em loop de trabalho...")
        
        while self._running:
            try:
                task = self.input_queue.get(timeout=1.0)
                
                if task.get("type") == "STOP":
                    logger.info("Sentinel: Recebido sinal de parada.")
                    self._running = False
                    break
                
                result = self._process_task(task)
                self.output_queue.put(result)
                
            except Empty:
                continue
            except Exception as e:
                logger.error(f"Sentinel: Erro no loop - {e}")
                self.output_queue.put({"status": "error", "error": str(e)})
        
        self._cleanup()
        logger.info("Sentinel: Encerrado.")

    def _setup_logging(self):
        """Configura logging para o processo filho."""
        logging.basicConfig(
            level=logging.INFO,
            format='[%(levelname)s] %(name)s: %(message)s'
        )

    def _load_llm(self):
        """
        Carrega modelo LLM se disponível.
        
        GPU AUTO-OFFLOAD (#59 Industrial Robustness):
        Calcula n_gpu_layers dinamicamente baseado em VRAM disponível.
        """
        if not HAS_LLAMA:
            logger.warning("llama-cpp-python não instalado. Sanitização via LLM desabilitada.")
            return
        
        model_path = self.config.get("model_path")
        if not model_path or not os.path.exists(model_path):
            logger.warning(f"Modelo LLM não encontrado: {model_path}")
            return
        
        # Calcular GPU layers baseado em VRAM
        n_gpu_layers = self._calculate_gpu_layers()
        
        try:
            logger.info(f"Carregando LLM: {os.path.basename(model_path)} (GPU layers: {n_gpu_layers})")
            self.llm = Llama(
                model_path=model_path,
                n_ctx=2048,
                n_gpu_layers=n_gpu_layers,
                verbose=False
            )
            logger.info("LLM carregado com sucesso.")
        except Exception as e:
            logger.error(f"Falha ao carregar LLM: {e}")
            # Tenta fallback CPU-only
            if n_gpu_layers > 0:
                logger.info("Tentando fallback CPU-only...")
                try:
                    self.llm = Llama(
                        model_path=model_path,
                        n_ctx=2048,
                        n_gpu_layers=0,
                        verbose=False
                    )
                    logger.info("LLM carregado em modo CPU-only.")
                except Exception as e2:
                    logger.error(f"Fallback CPU também falhou: {e2}")
    
    def _calculate_gpu_layers(self) -> int:
        """
        Calcula número de GPU layers baseado em VRAM disponível (#59).
        
        Heurística:
        - 0 VRAM (ou sem GPU): 0 layers (CPU only)
        - 4GB VRAM: ~20 layers
        - 6GB VRAM: ~30 layers
        - 8GB VRAM: ~35 layers
        - 12GB+ VRAM: -1 (todas as layers)
        """
        try:
            import torch
            if not torch.cuda.is_available():
                logger.info("CUDA não disponível, usando CPU")
                return 0
            
            # Pega VRAM total em GB
            total_vram_gb = torch.cuda.get_device_properties(0).total_memory / (1024**3)
            
            if total_vram_gb >= 12:
                layers = -1  # Todas as layers
            elif total_vram_gb >= 8:
                layers = 35
            elif total_vram_gb >= 6:
                layers = 30
            elif total_vram_gb >= 4:
                layers = 20
            else:
                layers = 10
            
            logger.info(f"GPU detectada: {total_vram_gb:.1f}GB VRAM -> {layers} layers")
            return layers
            
        except ImportError:
            logger.debug("PyTorch não disponível para detecção de VRAM")
        except Exception as e:
            logger.debug(f"Erro ao detectar VRAM: {e}")
        
        # Fallback: tenta usar GPU com valor conservador
        return 20

    def _process_task(self, task: Dict) -> Dict:
        """Processa uma tarefa da fila."""
        task_type = task.get("type")
        
        if task_type == "SANITIZE":
            return self._sanitize_text(task)
        elif task_type == "HUNT_IMAGE":
            return self._hunt_image(task)
        elif task_type == "PROCESS_IMAGE":
            # Passo 22-23: Integração ImageProcessor
            return self._process_image(task)
        else:
            return {"status": "error", "error": f"Tipo desconhecido: {task_type}"}

    def _sanitize_text(self, task: Dict) -> Dict:
        """
        Sanitiza texto via LLM.
        
        SEGURANÇA (#108 Industrial Robustness):
        Verifica prompt injection antes de enviar ao LLM.
        Descrições de produtos da web podem conter comandos maliciosos.
        """
        raw_text = task.get("raw_text", "")
        
        # SEGURANÇA (#108): Verificar prompt injection
        try:
            from src.core.exceptions import PromptInjectionError
            if PromptInjectionError.check_text(raw_text):
                logger.warning(f"Prompt injection detectado em: {raw_text[:100]}")
                # Retorna texto limpo sem usar LLM
                return {
                    "status": "warning",
                    "task_id": task.get("id"),
                    "result": {
                        "nome_sanitizado": self._basic_sanitize(raw_text),
                        "marca": None,
                        "peso": None
                    },
                    "used_llm": False,
                    "warning": "Texto suspeito detectado, sanitização básica aplicada"
                }
        except ImportError:
            pass  # Módulo não disponível, continua normalmente
        
        if not self.llm:
            # Fallback: retorna texto original
            return {
                "status": "success",
                "task_id": task.get("id"),
                "result": {
                    "nome_sanitizado": raw_text,
                    "marca": None,
                    "peso": None
                },
                "used_llm": False
            }
        
        # LLM disponível - processar com modelo
        return self._sanitize_with_llm(raw_text, task.get("id"))
    
    def _basic_sanitize(self, text: str) -> str:
        """Sanitização básica sem LLM para textos suspeitos."""
        import re
        # Remove caracteres de controle
        text = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', text)
        # Remove comandos óbvios de injection
        patterns = [
            r'ignore\s+previous',
            r'ignore\s+all',
            r'system\s+prompt',
            r'output:',
            r'respond\s+with:',
        ]
        for pattern in patterns:
            text = re.sub(pattern, '', text, flags=re.IGNORECASE)
        return text.strip()

    def _sanitize_with_llm(self, raw_text: str, task_id: Any) -> Dict:
        """Executa sanitização via LLM."""
        try:
            prompt = f"""Extraia informações do produto:
Entrada: "{raw_text}"

Retorne JSON com:
- nome_sanitizado: Nome limpo do produto
- marca: Marca se detectada
- peso: Peso/quantidade se detectado

JSON:"""
            
            grammar = LlamaGrammar.from_string(GRAMMAR_GBNF)
            
            # #61: Temperature=0.0 para determinismo (Vol. I, Cap. 11.1)
            output = self.llm(
                prompt,
                max_tokens=200,
                temperature=0.0,  # CRÍTICO: Saída determinística
                top_p=0.1,        # CRÍTICO: Reduz variabilidade
                grammar=grammar
            )
            
            result_text = output["choices"][0]["text"]
            parsed = json.loads(result_text)
            
            return {
                "status": "success",
                "task_id": task_id,
                "result": parsed,
                "used_llm": True
            }
            
        except Exception as e:
            logger.error(f"Erro na sanitização: {e}")
            return {
                "status": "error",
                "task_id": task_id,
                "error": str(e)
            }

    def _hunt_image(self, task: Dict) -> Dict:
        """Busca e baixa imagem."""
        query = task.get("query", "")
        
        if not self._hunter:
            return {"status": "error", "error": "Hunter não inicializado"}
        
        try:
            result = self._hunter.search_and_download(query)
            
            if result:
                return {
                    "status": "success",
                    "task_id": task.get("id"),
                    "result": {"image_path": result}
                }
            else:
                return {
                    "status": "not_found",
                    "task_id": task.get("id"),
                    "error": "Nenhuma imagem encontrada"
                }
                
        except Exception as e:
            return {
                "status": "error",
                "task_id": task.get("id"),
                "error": str(e)
            }

    def _process_image(self, task: Dict) -> Dict:
        """
        Processa imagem via ImageProcessor.
        Passo 22-23 do Checklist - Integração ImageProcessor no Sentinel.
        """
        image_path = task.get("image_path")
        remove_bg = task.get("remove_bg", False)  # Passo 23: Flag remove_bg
        
        if not image_path or not os.path.exists(image_path):
            return {"status": "error", "task_id": task.get("id"), "error": "Imagem não encontrada"}
        
        try:
            # Importa ImageProcessor
            from src.ai.vision import ImageProcessor
            processor = ImageProcessor()
            
            # Lê imagem
            with open(image_path, "rb") as f:
                image_bytes = f.read()
            
            # Processa
            result = processor.process_image(image_bytes, remove_bg=remove_bg)
            
            # Salva resultado
            output_path = image_path.replace(".", "_processed.")
            with open(output_path, "wb") as f:
                f.write(result)
            
            return {
                "status": "success",
                "task_id": task.get("id"),
                "result": {"processed_path": output_path}
            }
            
        except Exception as e:
            logger.error(f"Erro ao processar imagem: {e}")
            return {"status": "error", "task_id": task.get("id"), "error": str(e)}

    def _cleanup(self):
        """Limpeza de recursos."""
        if self._hunter:
            self._hunter.shutdown()
        if self.llm:
            del self.llm


"""
AutoTabloide AI - Motor Neural Isolado (NeuralEngine)
======================================================
Processo isolado para inferência LLM conforme Vol. IV, Cap. 1.3.
Garante que a UI nunca congele durante processamento de IA.
"""

import os
import json
import logging
import multiprocessing as mp
from pathlib import Path
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, asdict
from enum import Enum
from queue import Empty

logger = logging.getLogger("NeuralEngine")


class TaskType(str, Enum):
    """Tipos de tarefas para o motor neural."""
    SANITIZE_PRODUCT = "sanitize_product"
    EXTRACT_ENTITIES = "extract_entities"
    FUZZY_MATCH = "fuzzy_match"
    GENERATE_EMBEDDING = "generate_embedding"
    SHUTDOWN = "shutdown"


@dataclass
class NeuralTask:
    """Tarefa a ser processada pelo motor neural."""
    task_id: str
    task_type: TaskType
    payload: Dict[str, Any]
    priority: int = 0  # 0 = normal, 1 = high


@dataclass
class NeuralResult:
    """Resultado do processamento neural."""
    task_id: str
    success: bool
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    processing_time_ms: float = 0.0


# =============================================================================
# GRAMÁTICAS GBNF PARA SAÍDA DETERMINÍSTICA (Vol. IV, Cap. 1.4)
# =============================================================================

# Caminho para gramáticas customizadas
GRAMMAR_CONFIG_PATH = Path(__file__).parent.parent.parent / "AutoTabloide_System_Root" / "config"

def load_grammar_from_file(grammar_name: str = "product_schema.gbnf") -> Optional[str]:
    """Carrega gramática GBNF de arquivo externo para versionamento."""
    grammar_path = GRAMMAR_CONFIG_PATH / grammar_name
    if grammar_path.exists():
        try:
            return grammar_path.read_text(encoding="utf-8")
        except Exception as e:
            logger.warning(f"Erro ao carregar gramática {grammar_name}: {e}")
    return None

# Gramática embutida (fallback se arquivo não existir)
GRAMMAR_PRODUCT_JSON = """
root ::= object
object ::= "{" ws pair ("," ws pair)* "}" ws
pair ::= string ":" ws value
string ::= "\\\"" [a-zA-Z0-9_áéíóúâêîôûàèìòùãõçÁÉÍÓÚÂÊÎÔÛÀÈÌÒÙÃÕÇ.,;:!?()/ \\-]+ "\\\""
value ::= string | number | "null" | boolean | array
boolean ::= "true" | "false"
number ::= "-"? [0-9]+ ("." [0-9]+)?
array ::= "[" ws (value ("," ws value)*)? "]" ws
ws ::= [ \\t\\n]*
"""

# Tenta carregar do arquivo, senão usa embutida
_loaded_grammar = load_grammar_from_file()
ACTIVE_GRAMMAR = _loaded_grammar if _loaded_grammar else GRAMMAR_PRODUCT_JSON

SYSTEM_PROMPT_ETL = """Você é um algoritmo de limpeza de dados (ETL) para varejo brasileiro.
Sua única função é receber uma string de produto mal formatada e retornar JSON estruturado.

REGRAS ESTRITAS:
1. 'produto': Substantivo principal em Title Case (ex: 'Arroz', 'Sabão em Pó')
2. 'marca': Marca fabricante em Title Case. Se ausente, use null
3. 'variacao': Sabor, fragrância ou tipo (ex: 'Lavanda', 'Tipo 1'). Se ausente, use null
4. 'peso': Valor numérico padronizado (ex: '500g', '1L', '2kg')
5. 'unidade': Unidade de medida ('g', 'kg', 'ml', 'L', 'un')
6. 'promocao': Se detectar padrões como 'L4P3', extraia. Senão, null

NÃO adicione adjetivos subjetivos. NÃO corrija marcas desconhecidas.
Retorne APENAS o JSON, sem texto adicional.

Exemplo:
Entrada: "SAB OMO LAV PERF 800"
Saída: {"produto": "Sabão em Pó", "marca": "Omo", "variacao": "Lavagem Perfeita", "peso": "800g", "unidade": "g", "promocao": null}
"""


def neural_worker(
    input_queue: mp.Queue,
    output_queue: mp.Queue,
    model_path: str,
    n_gpu_layers: int = -1,
    n_ctx: int = 4096
):
    """
    Worker function que roda em processo isolado.
    Carrega o modelo UMA VEZ e processa tarefas da fila.
    
    Args:
        input_queue: Fila de entrada de tarefas
        output_queue: Fila de saída de resultados
        model_path: Caminho para o modelo GGUF
        n_gpu_layers: Camadas para GPU (-1 = todas)
        n_ctx: Tamanho do contexto
    """
    import time
    
    llm = None
    embedder = None
    
    logger.info(f"NeuralWorker iniciando... Model: {model_path}")
    
    # Tenta carregar o modelo LLM
    try:
        from llama_cpp import Llama
        
        if os.path.exists(model_path):
            llm = Llama(
                model_path=model_path,
                n_gpu_layers=n_gpu_layers,
                n_ctx=n_ctx,
                verbose=False
            )
            logger.info("Modelo LLM carregado com sucesso")
        else:
            logger.warning(f"Modelo LLM não encontrado: {model_path}")
    except ImportError:
        logger.warning("llama-cpp-python não disponível")
    except Exception as e:
        logger.error(f"Erro ao carregar LLM: {e}")
    
    # Tenta carregar o embedder (sentence-transformers)
    try:
        from sentence_transformers import SentenceTransformer
        embedder = SentenceTransformer('all-MiniLM-L6-v2')
        logger.info("Embedder sentence-transformers carregado")
    except ImportError:
        logger.warning("sentence-transformers não disponível")
    except Exception as e:
        logger.warning(f"Erro ao carregar embedder: {e}")
    
    logger.info("NeuralWorker pronto para processar tarefas")
    
    while True:
        try:
            # Aguarda tarefa (bloqueante)
            task_data = input_queue.get(timeout=1.0)
            
            if task_data is None:
                continue
                
            task = NeuralTask(**task_data)
            start_time = time.time()
            
            # Shutdown signal
            if task.task_type == TaskType.SHUTDOWN:
                logger.info("NeuralWorker recebeu SHUTDOWN")
                output_queue.put(asdict(NeuralResult(
                    task_id=task.task_id,
                    success=True,
                    result={"status": "shutdown"}
                )))
                break
            
            # Processa a tarefa
            result = process_task(task, llm, embedder)
            result.processing_time_ms = (time.time() - start_time) * 1000
            
            output_queue.put(asdict(result))
            
        except Empty:
            continue
        except Exception as e:
            logger.error(f"Erro no worker: {e}")
            if 'task' in locals():
                output_queue.put(asdict(NeuralResult(
                    task_id=task.task_id,
                    success=False,
                    error=str(e)
                )))


def process_task(task: NeuralTask, llm, embedder) -> NeuralResult:
    """Processa uma tarefa específica."""
    
    if task.task_type == TaskType.SANITIZE_PRODUCT:
        return _sanitize_product(task, llm)
    
    elif task.task_type == TaskType.EXTRACT_ENTITIES:
        return _extract_entities(task, llm)
    
    elif task.task_type == TaskType.GENERATE_EMBEDDING:
        return _generate_embedding(task, embedder)
    
    elif task.task_type == TaskType.FUZZY_MATCH:
        return _fuzzy_match(task)
    
    else:
        return NeuralResult(
            task_id=task.task_id,
            success=False,
            error=f"Tipo de tarefa desconhecido: {task.task_type}"
        )


def _sanitize_product(task: NeuralTask, llm) -> NeuralResult:
    """Limpa e estrutura descrição de produto."""
    raw_text = task.payload.get("raw_text", "")
    
    if not raw_text:
        return NeuralResult(
            task_id=task.task_id,
            success=False,
            error="raw_text vazio"
        )
    
    # Se LLM não disponível, usa fallback heurístico
    if llm is None:
        result = _sanitize_fallback(raw_text)
        return NeuralResult(
            task_id=task.task_id,
            success=True,
            result=result
        )
    
    try:
        prompt = f"{SYSTEM_PROMPT_ETL}\n\nEntrada: \"{raw_text}\"\nSaída:"
        
        response = llm.create_chat_completion(
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT_ETL},
                {"role": "user", "content": f"Entrada: \"{raw_text}\""}
            ],
            max_tokens=256,
            temperature=0.0,
            top_p=0.1
        )
        
        output = response["choices"][0]["message"]["content"]
        
        # Tenta parsear JSON
        try:
            parsed = json.loads(output)
            return NeuralResult(
                task_id=task.task_id,
                success=True,
                result=parsed
            )
        except json.JSONDecodeError:
            # Fallback se JSON inválido
            result = _sanitize_fallback(raw_text)
            result["_llm_raw"] = output
            return NeuralResult(
                task_id=task.task_id,
                success=True,
                result=result
            )
            
    except Exception as e:
        return NeuralResult(
            task_id=task.task_id,
            success=False,
            error=str(e)
        )


def _sanitize_fallback(raw_text: str) -> Dict[str, Any]:
    """Fallback heurístico quando LLM não está disponível."""
    import re
    
    text = raw_text.strip()
    
    # Extrai peso/unidade
    peso_match = re.search(r'(\d+(?:[.,]\d+)?)\s*(kg|g|ml|l|un|lt|gr)\b', text, re.IGNORECASE)
    peso = None
    unidade = None
    if peso_match:
        peso = peso_match.group(1).replace(',', '.') + peso_match.group(2).lower()
        unidade = peso_match.group(2).lower()
        if unidade == 'lt':
            unidade = 'l'
        if unidade == 'gr':
            unidade = 'g'
    
    # Remove peso do texto para limpar nome
    nome = text
    if peso_match:
        nome = text[:peso_match.start()] + text[peso_match.end():]
    
    # Title Case e limpeza
    nome = ' '.join(nome.split())  # Remove espaços duplos
    nome = nome.title()
    
    # Detecta promoção (L4P3, etc)
    promo_match = re.search(r'L\d+P\d+', text, re.IGNORECASE)
    promocao = promo_match.group(0).upper() if promo_match else None
    
    return {
        "produto": nome,
        "marca": None,
        "variacao": None,
        "peso": peso,
        "unidade": unidade,
        "promocao": promocao
    }


def _extract_entities(task: NeuralTask, llm) -> NeuralResult:
    """Extrai entidades de texto."""
    # Similar ao sanitize, mas para extração geral
    return _sanitize_product(task, llm)


def _generate_embedding(task: NeuralTask, embedder) -> NeuralResult:
    """Gera embedding vetorial para texto."""
    text = task.payload.get("text", "")
    
    if not text:
        return NeuralResult(
            task_id=task.task_id,
            success=False,
            error="text vazio"
        )
    
    if embedder is None:
        return NeuralResult(
            task_id=task.task_id,
            success=False,
            error="Embedder não disponível"
        )
    
    try:
        vector = embedder.encode(text).tolist()
        return NeuralResult(
            task_id=task.task_id,
            success=True,
            result={"embedding": vector, "dimensions": len(vector)}
        )
    except Exception as e:
        return NeuralResult(
            task_id=task.task_id,
            success=False,
            error=str(e)
        )


def _fuzzy_match(task: NeuralTask) -> NeuralResult:
    """Realiza matching fuzzy entre strings."""
    query = task.payload.get("query", "")
    candidates = task.payload.get("candidates", [])
    threshold = task.payload.get("threshold", 80)
    
    if not query or not candidates:
        return NeuralResult(
            task_id=task.task_id,
            success=False,
            error="query ou candidates vazio"
        )
    
    try:
        from rapidfuzz import fuzz, process as rf_process
        
        results = rf_process.extract(
            query,
            candidates,
            scorer=fuzz.WRatio,
            limit=5
        )
        
        matches = [
            {"text": r[0], "score": r[1], "index": r[2]}
            for r in results
            if r[1] >= threshold
        ]
        
        return NeuralResult(
            task_id=task.task_id,
            success=True,
            result={"matches": matches, "best_match": matches[0] if matches else None}
        )
        
    except ImportError:
        # Fallback simples se rapidfuzz não disponível
        from difflib import SequenceMatcher
        
        matches = []
        for i, candidate in enumerate(candidates):
            score = SequenceMatcher(None, query.lower(), candidate.lower()).ratio() * 100
            if score >= threshold:
                matches.append({"text": candidate, "score": score, "index": i})
        
        matches.sort(key=lambda x: x["score"], reverse=True)
        
        return NeuralResult(
            task_id=task.task_id,
            success=True,
            result={"matches": matches[:5], "best_match": matches[0] if matches else None}
        )


# =============================================================================
# CLASSE CONTROLADORA DO MOTOR NEURAL
# =============================================================================

class NeuralEngineController:
    """
    Controlador do Motor Neural.
    Gerencia o processo isolado e a comunicação via filas.
    
    Uso:
        controller = NeuralEngineController()
        controller.start()
        
        result = await controller.sanitize_product("SAB OMO 500")
        
        controller.stop()
    """
    
    DEFAULT_MODEL_PATH = Path(__file__).parent.parent.parent / \
        "AutoTabloide_System_Root" / "bin" / "Llama-3-8B-Instruct.Q4_K_M.gguf"
    
    def __init__(self, model_path: str = None):
        self.model_path = str(model_path or self.DEFAULT_MODEL_PATH)
        self.process: Optional[mp.Process] = None
        self.input_queue: Optional[mp.Queue] = None
        self.output_queue: Optional[mp.Queue] = None
        self._task_counter = 0
        self._pending_tasks: Dict[str, Any] = {}
        self._is_running = False
    
    @property
    def is_running(self) -> bool:
        return self._is_running and self.process is not None and self.process.is_alive()
    
    def start(self, n_gpu_layers: int = -1, n_ctx: int = 4096):
        """Inicia o processo neural worker."""
        if self.is_running:
            logger.warning("NeuralEngine já está rodando")
            return
        
        self.input_queue = mp.Queue()
        self.output_queue = mp.Queue()
        
        self.process = mp.Process(
            target=neural_worker,
            args=(self.input_queue, self.output_queue, self.model_path, n_gpu_layers, n_ctx),
            daemon=True
        )
        self.process.start()
        self._is_running = True
        
        logger.info(f"NeuralEngine iniciado (PID: {self.process.pid})")
    
    def stop(self, timeout: float = 5.0):
        """Para o processo neural worker."""
        if not self.is_running:
            return
        
        # Envia sinal de shutdown
        task_id = self._generate_task_id()
        self.input_queue.put({
            "task_id": task_id,
            "task_type": TaskType.SHUTDOWN.value,
            "payload": {},
            "priority": 0
        })
        
        # Aguarda encerramento
        self.process.join(timeout=timeout)
        
        if self.process.is_alive():
            logger.warning("Forçando término do NeuralEngine")
            self.process.terminate()
            self.process.join(timeout=1.0)
        
        self._is_running = False
        logger.info("NeuralEngine encerrado")
    
    def _generate_task_id(self) -> str:
        self._task_counter += 1
        return f"task_{self._task_counter}_{os.getpid()}"
    
    def submit_task(self, task_type: TaskType, payload: Dict[str, Any], priority: int = 0) -> str:
        """
        Submete uma tarefa para processamento.
        Retorna o task_id para rastreamento.
        """
        if not self.is_running:
            raise RuntimeError("NeuralEngine não está rodando. Chame start() primeiro.")
        
        task_id = self._generate_task_id()
        
        self.input_queue.put({
            "task_id": task_id,
            "task_type": task_type.value,
            "payload": payload,
            "priority": priority
        })
        
        return task_id
    
    def get_result(self, timeout: float = 30.0) -> Optional[NeuralResult]:
        """
        Obtém o próximo resultado da fila.
        Retorna None se timeout.
        """
        try:
            result_data = self.output_queue.get(timeout=timeout)
            return NeuralResult(**result_data)
        except Empty:
            return None
    
    async def sanitize_product_async(self, raw_text: str, timeout: float = 30.0) -> Optional[Dict]:
        """
        Sanitiza descrição de produto de forma assíncrona.
        Wrapper conveniente para uso com asyncio.
        """
        import asyncio
        
        task_id = self.submit_task(
            TaskType.SANITIZE_PRODUCT,
            {"raw_text": raw_text}
        )
        
        # Poll para resultado (evita bloqueio)
        start = asyncio.get_event_loop().time()
        while asyncio.get_event_loop().time() - start < timeout:
            try:
                result_data = self.output_queue.get_nowait()
                result = NeuralResult(**result_data)
                if result.task_id == task_id:
                    return result.result if result.success else None
            except Empty:
                await asyncio.sleep(0.1)
        
        return None
    
    async def generate_embedding_async(self, text: str, timeout: float = 10.0) -> Optional[List[float]]:
        """Gera embedding de forma assíncrona."""
        import asyncio
        
        task_id = self.submit_task(
            TaskType.GENERATE_EMBEDDING,
            {"text": text}
        )
        
        start = asyncio.get_event_loop().time()
        while asyncio.get_event_loop().time() - start < timeout:
            try:
                result_data = self.output_queue.get_nowait()
                result = NeuralResult(**result_data)
                if result.task_id == task_id:
                    return result.result.get("embedding") if result.success else None
            except Empty:
                await asyncio.sleep(0.05)
        
        return None
    
    async def fuzzy_match_async(
        self, 
        query: str, 
        candidates: List[str], 
        threshold: int = 80,
        timeout: float = 5.0
    ) -> Optional[Dict]:
        """Realiza matching fuzzy de forma assíncrona."""
        import asyncio
        
        task_id = self.submit_task(
            TaskType.FUZZY_MATCH,
            {"query": query, "candidates": candidates, "threshold": threshold}
        )
        
        start = asyncio.get_event_loop().time()
        while asyncio.get_event_loop().time() - start < timeout:
            try:
                result_data = self.output_queue.get_nowait()
                result = NeuralResult(**result_data)
                if result.task_id == task_id:
                    return result.result if result.success else None
            except Empty:
                await asyncio.sleep(0.05)
        
        return None


# Singleton global para uso em toda a aplicação
_neural_engine: Optional[NeuralEngineController] = None


def get_neural_engine() -> NeuralEngineController:
    """Obtém instância singleton do NeuralEngine."""
    global _neural_engine
    if _neural_engine is None:
        _neural_engine = NeuralEngineController()
    return _neural_engine


def initialize_neural_engine(model_path: str = None, auto_start: bool = True):
    """
    Inicializa o NeuralEngine como singleton.
    Deve ser chamado no boot da aplicação.
    """
    global _neural_engine
    _neural_engine = NeuralEngineController(model_path)
    if auto_start:
        _neural_engine.start()
    return _neural_engine


def shutdown_neural_engine():
    """Encerra o NeuralEngine singleton."""
    global _neural_engine
    if _neural_engine is not None:
        _neural_engine.stop()
        _neural_engine = None

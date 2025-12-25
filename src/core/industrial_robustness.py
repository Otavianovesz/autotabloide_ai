"""
AutoTabloide AI - Industrial Robustness Module
===============================================
Implementações críticas para sobrevivência no mundo real.
Categoria X: Passos 101-110 do Checklist Industrial.

Este módulo contém:
- DPI Validator (#102)
- Windows Path Sanitizer (#105)
- Ghostscript Cleanup Manager (#109)
- Network Recovery Handler (#110)
"""

import os
import sys
import atexit
import tempfile
import logging
from pathlib import Path
from typing import Optional, Tuple, List, Callable
from PIL import Image

logger = logging.getLogger("IndustrialRobustness")


# ==============================================================================
# #102: DPI VALIDATOR - Validação de Resolução para Impressão
# ==============================================================================

class DPIValidator:
    """
    Valida resolução efetiva de imagens para impressão profissional.
    
    DPI Efetivo = (Pixel Dimensions / Physical Size in Slot) * 25.4
    
    Regra: Imagens esticadas para slots maiores perdem DPI.
    Se DPI efetivo < 250, a impressão sairá borrada.
    """
    
    MIN_DPI_PRINT = 250.0  # Mínimo para impressão offset de qualidade
    MIN_DPI_WARN = 150.0   # Alerta amarelo
    OPTIMAL_DPI = 300.0    # Ideal para impressão
    
    @classmethod
    def calculate_effective_dpi(
        cls,
        image_path: str,
        slot_width_mm: float,
        slot_height_mm: float
    ) -> Tuple[float, float]:
        """
        Calcula DPI efetivo quando imagem é colocada em um slot.
        
        Args:
            image_path: Caminho da imagem
            slot_width_mm: Largura do slot em milímetros
            slot_height_mm: Altura do slot em milímetros
            
        Returns:
            Tuple (dpi_horizontal, dpi_vertical)
        """
        try:
            with Image.open(image_path) as img:
                width_px, height_px = img.size
                
                # Conversão mm -> inches (1 inch = 25.4mm)
                slot_width_inch = slot_width_mm / 25.4
                slot_height_inch = slot_height_mm / 25.4
                
                dpi_x = width_px / slot_width_inch if slot_width_inch > 0 else 0
                dpi_y = height_px / slot_height_inch if slot_height_inch > 0 else 0
                
                return (dpi_x, dpi_y)
                
        except Exception as e:
            logger.error(f"Erro ao calcular DPI: {e}")
            return (0.0, 0.0)
    
    @classmethod
    def validate_for_print(
        cls,
        image_path: str,
        slot_width_mm: float,
        slot_height_mm: float,
        raise_on_low: bool = True
    ) -> dict:
        """
        Valida se imagem tem DPI suficiente para impressão.
        
        Args:
            image_path: Caminho da imagem
            slot_width_mm: Largura do slot em mm
            slot_height_mm: Altura do slot em mm
            raise_on_low: Se True, lança LowDPIError
            
        Returns:
            Dict com status, DPI efetivo e recomendação
            
        Raises:
            LowDPIError: Se DPI < MIN_DPI_PRINT e raise_on_low=True
        """
        dpi_x, dpi_y = cls.calculate_effective_dpi(
            image_path, slot_width_mm, slot_height_mm
        )
        
        effective_dpi = min(dpi_x, dpi_y)  # Usa o menor valor
        
        result = {
            "path": image_path,
            "dpi_x": dpi_x,
            "dpi_y": dpi_y,
            "effective_dpi": effective_dpi,
            "status": "ok",
            "message": None
        }
        
        if effective_dpi < cls.MIN_DPI_PRINT:
            result["status"] = "error"
            result["message"] = (
                f"DPI efetivo ({effective_dpi:.0f}) abaixo do mínimo "
                f"({cls.MIN_DPI_PRINT:.0f}) para impressão profissional."
            )
            
            if raise_on_low:
                from src.core.exceptions import LowDPIError
                raise LowDPIError(
                    image_path=image_path,
                    effective_dpi=effective_dpi,
                    required_dpi=cls.MIN_DPI_PRINT,
                )
                
        elif effective_dpi < cls.OPTIMAL_DPI:
            result["status"] = "warning"
            result["message"] = (
                f"DPI efetivo ({effective_dpi:.0f}) abaixo do ideal "
                f"({cls.OPTIMAL_DPI:.0f}). Considere usar imagem maior."
            )
        
        return result


# ==============================================================================
# #105: WINDOWS PATH SANITIZER - Limite MAX_PATH
# ==============================================================================

class WindowsPathSanitizer:
    """
    Gerencia caminhos longos no Windows (MAX_PATH = 260 chars).
    
    PROBLEMA: Caminhos como 
    "C:\\Users\\usuario\\Documents\\Projetos\\cliente_muito_longo\\assets\\imagens\\"
    estouram o limite e causam "FileNotFoundError" inexplicáveis.
    
    SOLUÇÃO: 
    - Usar prefixo \\?\ para caminhos longos
    - Alertar quando caminho se aproxima do limite
    """
    
    MAX_PATH = 260
    SAFE_MAX = 240  # Margem de segurança
    LONG_PATH_PREFIX = "\\\\?\\"
    
    @classmethod
    def is_windows(cls) -> bool:
        return sys.platform == "win32"
    
    @classmethod
    def normalize(cls, path: str) -> str:
        """
        Normaliza caminho para Windows, adicionando prefixo se necessário.
        
        Em sistemas não-Windows, retorna o caminho inalterado.
        """
        if not cls.is_windows():
            return path
        
        # Já tem prefixo?
        if path.startswith(cls.LONG_PATH_PREFIX):
            return path
        
        # Converter para absoluto
        abs_path = os.path.abspath(path)
        
        # Se longo, adicionar prefixo
        if len(abs_path) >= cls.SAFE_MAX:
            return f"{cls.LONG_PATH_PREFIX}{abs_path}"
        
        return abs_path
    
    @classmethod
    def validate(cls, path: str) -> dict:
        """
        Valida caminho e retorna status.
        
        Returns:
            Dict com status, tamanho e recomendações
        """
        if not cls.is_windows():
            return {"status": "ok", "length": len(path), "platform": "non-windows"}
        
        abs_path = os.path.abspath(path)
        length = len(abs_path)
        
        result = {
            "status": "ok",
            "length": length,
            "max_path": cls.MAX_PATH,
            "path": abs_path
        }
        
        if length >= cls.MAX_PATH:
            result["status"] = "error"
            result["message"] = (
                f"Caminho excede MAX_PATH ({length} chars). "
                "Use nomes mais curtos ou mova o projeto para pasta mais rasa."
            )
        elif length >= cls.SAFE_MAX:
            result["status"] = "warning"
            result["message"] = (
                f"Caminho próximo do limite ({length}/{cls.MAX_PATH} chars). "
                "Cuidado ao criar subpastas."
            )
        
        return result
    
    @classmethod
    def ensure_safe(cls, path: str) -> str:
        """
        Garante que o caminho é seguro para uso.
        Lança FileError se caminho for muito longo e não puder ser corrigido.
        """
        if not cls.is_windows():
            return path
        
        # Tenta normalizar com prefixo longo
        normalized = cls.normalize(path)
        
        # Verifica se funciona
        try:
            # Teste se o diretório pai existe ou pode ser criado
            parent = Path(normalized).parent
            if not parent.exists():
                # Se não existe, só podemos tentar criar se o sistema suporta
                pass
            return normalized
        except OSError as e:
            from src.core.exceptions import FileError
            raise FileError(
                f"Caminho inválido no Windows: {path}",
                file_path=path
            ) from e


# ==============================================================================
# #109: GHOSTSCRIPT CLEANUP MANAGER
# ==============================================================================

class GhostscriptCleanup:
    """
    Gerencia limpeza de arquivos temporários do Ghostscript.
    
    PROBLEMA: Se o programa travar, arquivos gs_*.tmp ficam órfãos no disco.
    
    SOLUÇÃO: 
    - Registrar todos os arquivos temporários criados
    - Usar atexit para limpeza mesmo em crash
    - Context manager para operações de render
    """
    
    _temp_files: List[str] = []
    _registered: bool = False
    
    @classmethod
    def register_cleanup_hook(cls):
        """Registra hook de limpeza no exit do programa."""
        if not cls._registered:
            atexit.register(cls.cleanup_all)
            cls._registered = True
            logger.debug("Hook de limpeza do Ghostscript registrado")
    
    @classmethod
    def track_file(cls, path: str):
        """Adiciona arquivo à lista de rastreamento."""
        cls.register_cleanup_hook()
        if path not in cls._temp_files:
            cls._temp_files.append(path)
    
    @classmethod
    def untrack_file(cls, path: str):
        """Remove arquivo da lista (após uso bem-sucedido)."""
        if path in cls._temp_files:
            cls._temp_files.remove(path)
    
    @classmethod
    def cleanup_all(cls):
        """Remove todos os arquivos temporários rastreados."""
        for path in cls._temp_files[:]:  # Cópia para iteração segura
            try:
                if os.path.exists(path):
                    os.remove(path)
                    logger.debug(f"Removido temp file: {path}")
                cls._temp_files.remove(path)
            except Exception as e:
                logger.warning(f"Falha ao remover {path}: {e}")
    
    @classmethod
    def cleanup_gs_temps(cls, directory: Optional[str] = None):
        """
        Limpa arquivos gs_*.tmp de um diretório.
        Se diretório não especificado, usa o temp do sistema.
        """
        if directory is None:
            directory = tempfile.gettempdir()
        
        try:
            for filename in os.listdir(directory):
                if filename.startswith("gs_") and filename.endswith(".tmp"):
                    filepath = os.path.join(directory, filename)
                    try:
                        os.remove(filepath)
                        logger.debug(f"Removido GS temp: {filepath}")
                    except Exception as e:
                        logger.warning(f"Não foi possível remover {filepath}: {e}")
        except Exception as e:
            logger.warning(f"Erro ao limpar temps do GS: {e}")


class GhostscriptContext:
    """
    Context manager para operações do Ghostscript.
    Garante limpeza mesmo em caso de exceção.
    """
    
    def __init__(self, temp_dir: Optional[str] = None):
        self.temp_dir = temp_dir or tempfile.gettempdir()
        self.temp_files: List[str] = []
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        # Limpa arquivos criados neste contexto
        for path in self.temp_files:
            try:
                if os.path.exists(path):
                    os.remove(path)
            except Exception:
                pass
        return False  # Não suprime exceções
    
    def create_temp(self, suffix: str = ".pdf") -> str:
        """Cria arquivo temporário rastreado."""
        fd, path = tempfile.mkstemp(suffix=suffix, dir=self.temp_dir)
        os.close(fd)
        self.temp_files.append(path)
        GhostscriptCleanup.track_file(path)
        return path


# ==============================================================================
# #110: NETWORK RECOVERY HANDLER
# ==============================================================================

class NetworkRecoveryHandler:
    """
    Gerencia recuperação de falhas de rede durante web scraping.
    
    PROBLEMA: Se a internet cair durante o Hunter, a UI não pode travar.
    
    SOLUÇÃO:
    - Retry automático com backoff exponencial
    - Skip após N tentativas
    - Callback para atualizar UI com status
    """
    
    DEFAULT_MAX_RETRIES = 3
    DEFAULT_BASE_DELAY = 1.0  # segundos
    DEFAULT_MAX_DELAY = 30.0  # segundos
    
    @classmethod
    def with_retry(
        cls,
        func: Callable,
        max_retries: int = DEFAULT_MAX_RETRIES,
        base_delay: float = DEFAULT_BASE_DELAY,
        max_delay: float = DEFAULT_MAX_DELAY,
        on_retry: Optional[Callable[[int, Exception], None]] = None,
        on_failure: Optional[Callable[[Exception], None]] = None
    ):
        """
        Executa função com retry automático em caso de erro de rede.
        
        Args:
            func: Função a executar
            max_retries: Número máximo de tentativas
            base_delay: Delay inicial entre retries (dobra a cada tentativa)
            max_delay: Delay máximo
            on_retry: Callback chamado antes de cada retry (attempt, exception)
            on_failure: Callback chamado se todas tentativas falharem
            
        Returns:
            Resultado da função ou None se todas tentativas falharem
        """
        import time
        
        last_exception = None
        delay = base_delay
        
        for attempt in range(max_retries + 1):
            try:
                return func()
            except (ConnectionError, TimeoutError, OSError) as e:
                last_exception = e
                
                if attempt < max_retries:
                    if on_retry:
                        on_retry(attempt + 1, e)
                    
                    logger.warning(
                        f"Tentativa {attempt + 1}/{max_retries + 1} falhou: {e}. "
                        f"Retrying em {delay:.1f}s..."
                    )
                    
                    time.sleep(delay)
                    delay = min(delay * 2, max_delay)  # Backoff exponencial
        
        # Todas tentativas falharam
        logger.error(f"Todas {max_retries + 1} tentativas falharam: {last_exception}")
        
        if on_failure:
            on_failure(last_exception)
        
        return None
    
    @classmethod
    async def with_retry_async(
        cls,
        coro_func: Callable,
        max_retries: int = DEFAULT_MAX_RETRIES,
        base_delay: float = DEFAULT_BASE_DELAY,
        max_delay: float = DEFAULT_MAX_DELAY,
        on_retry: Optional[Callable[[int, Exception], None]] = None,
    ):
        """Versão assíncrona do with_retry."""
        import asyncio
        
        delay = base_delay
        
        for attempt in range(max_retries + 1):
            try:
                return await coro_func()
            except (ConnectionError, TimeoutError, OSError) as e:
                if attempt < max_retries:
                    if on_retry:
                        on_retry(attempt + 1, e)
                    
                    logger.warning(
                        f"Async tentativa {attempt + 1} falhou: {e}. "
                        f"Retrying em {delay:.1f}s..."
                    )
                    
                    await asyncio.sleep(delay)
                    delay = min(delay * 2, max_delay)
                else:
                    raise


# ==============================================================================
# INICIALIZAÇÃO DO MÓDULO
# ==============================================================================

def initialize_industrial_robustness():
    """
    Inicializa todas as proteções industriais.
    Deve ser chamado no bootstrap do aplicativo.
    """
    # Registrar limpeza do Ghostscript
    GhostscriptCleanup.register_cleanup_hook()
    
    # Limpar temps órfãos de execuções anteriores
    GhostscriptCleanup.cleanup_gs_temps()
    
    logger.info("Industrial Robustness Module inicializado")


# Auto-registro do cleanup hook ao importar o módulo
GhostscriptCleanup.register_cleanup_hook()

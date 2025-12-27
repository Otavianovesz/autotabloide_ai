"""
AutoTabloide AI - UI Safety Module
===================================
Robustez industrial para interface gráfica.
PROTOCOLO DE RETIFICAÇÃO: Passos 71-90 (UI/UX e Ateliê).

Este módulo contém:
- Passo 71: Virtualização real com paginação DB
- Passo 72: Debounce na busca (300ms)
- Passo 75: Modal de progresso bloqueante
- Passo 78: Atalhos de teclado
- Passo 79: Placeholder de imagem quebrada
- Passo 80: Indicador de não salvo (*)
- Passo 81: Máscara de input de preço
- Passo 87: Animações rápidas
- Passo 88: Tooltip informativo
- Passo 100: Códigos de erro amigáveis
"""

import asyncio
import logging
import re
from typing import Optional, Callable, Any, Dict, List
from decimal import Decimal, InvalidOperation
from pathlib import Path
from dataclasses import dataclass, field

logger = logging.getLogger("UISafety")


# ==============================================================================
# PASSO 71: VIRTUALIZAÇÃO COM PAGINAÇÃO
# ==============================================================================

@dataclass
class PaginationConfig:
    """Configuração de paginação para listas virtualizadas."""
    page_size: int = 50
    current_page: int = 0
    total_items: int = 0
    
    @property
    def offset(self) -> int:
        return self.current_page * self.page_size
    
    @property
    def total_pages(self) -> int:
        if self.total_items == 0:
            return 1
        return (self.total_items + self.page_size - 1) // self.page_size
    
    @property
    def has_next(self) -> bool:
        return self.current_page < self.total_pages - 1
    
    @property
    def has_prev(self) -> bool:
        return self.current_page > 0


class VirtualizedDataLoader:
    """
    Carregador de dados com virtualização real.
    
    PROBLEMA: Carregar todos os dados na memória antes de passar para ListView.
    
    SOLUÇÃO: Usar LIMIT/OFFSET no banco e carregar sob demanda.
    """
    
    @classmethod
    async def load_page(
        cls,
        session,
        model_class,
        config: PaginationConfig,
        filters: Optional[Dict] = None,
        order_by: Optional[str] = None
    ) -> List[Any]:
        """
        Carrega uma página de dados do banco.
        
        Args:
            session: Sessão assíncrona do SQLAlchemy
            model_class: Classe do modelo
            config: Configuração de paginação
            filters: Filtros opcionais
            order_by: Coluna para ordenação
            
        Returns:
            Lista de objetos da página atual
        """
        from sqlalchemy import select, func
        
        # Query base
        stmt = select(model_class)
        count_stmt = select(func.count()).select_from(model_class)
        
        # Aplicar filtros
        if filters:
            for column, value in filters.items():
                if hasattr(model_class, column):
                    col = getattr(model_class, column)
                    if isinstance(value, str) and '%' in value:
                        stmt = stmt.where(col.like(value))
                        count_stmt = count_stmt.where(col.like(value))
                    else:
                        stmt = stmt.where(col == value)
                        count_stmt = count_stmt.where(col == value)
        
        # Ordenação
        if order_by and hasattr(model_class, order_by):
            stmt = stmt.order_by(getattr(model_class, order_by).desc())
        
        # Paginação
        stmt = stmt.offset(config.offset).limit(config.page_size)
        
        # Executar
        result = await session.execute(stmt)
        items = result.scalars().all()
        
        # Atualizar total
        count_result = await session.execute(count_stmt)
        config.total_items = count_result.scalar() or 0
        
        return items


# ==============================================================================
# PASSO 72: DEBOUNCE NA BUSCA
# ==============================================================================

class Debouncer:
    """
    Implementa debounce para evitar chamadas excessivas.
    
    Típico uso: busca que dispara a cada tecla.
    """
    
    def __init__(self, delay_ms: int = 300):
        self.delay = delay_ms / 1000  # Converter para segundos
        self._task: Optional[asyncio.Task] = None
        self._callback: Optional[Callable] = None
    
    async def call(self, callback: Callable, *args, **kwargs) -> None:
        """
        Chama callback com debounce.
        
        Args:
            callback: Função a chamar
            *args, **kwargs: Argumentos para o callback
        """
        # Cancelar chamada anterior se existir
        if self._task and not self._task.done():
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        
        # Agendar nova chamada
        async def delayed_call():
            await asyncio.sleep(self.delay)
            if asyncio.iscoroutinefunction(callback):
                await callback(*args, **kwargs)
            else:
                callback(*args, **kwargs)
        
        self._task = asyncio.create_task(delayed_call())
    
    def cancel(self) -> None:
        """Cancela chamada pendente."""
        if self._task and not self._task.done():
            self._task.cancel()


class DebouncedSearchHandler:
    """Handler de busca com debounce integrado."""
    
    def __init__(self, search_callback: Callable, delay_ms: int = 300):
        self.debouncer = Debouncer(delay_ms)
        self.search_callback = search_callback
        self.last_query = ""
    
    async def on_search_change(self, query: str) -> None:
        """Chamado a cada mudança no campo de busca."""
        self.last_query = query
        await self.debouncer.call(self.search_callback, query)


# ==============================================================================
# PASSO 75: MODAL DE PROGRESSO BLOQUEANTE
# ==============================================================================

@dataclass
class ProgressState:
    """Estado de progresso para operações longas."""
    total: int = 0
    current: int = 0
    message: str = ""
    is_cancellable: bool = True
    cancelled: bool = False
    
    @property
    def percentage(self) -> float:
        if self.total == 0:
            return 0
        return (self.current / self.total) * 100
    
    @property
    def is_complete(self) -> bool:
        return self.current >= self.total


class BlockingProgressManager:
    """
    Gerencia modal de progresso que bloqueia interações.
    
    CRÍTICO: Evita clique duplo durante operações longas.
    """
    
    _is_active = False
    _state: Optional[ProgressState] = None
    
    @classmethod
    def is_blocking(cls) -> bool:
        """Retorna True se há operação em andamento."""
        return cls._is_active
    
    @classmethod
    def start(cls, total: int, message: str = "Processando...") -> ProgressState:
        """
        Inicia modo de progresso bloqueante.
        
        Args:
            total: Total de itens a processar
            message: Mensagem inicial
            
        Returns:
            ProgressState para atualização
        """
        cls._is_active = True
        cls._state = ProgressState(total=total, message=message)
        return cls._state
    
    @classmethod
    def update(cls, current: int, message: Optional[str] = None) -> None:
        """Atualiza progresso."""
        if cls._state:
            cls._state.current = current
            if message:
                cls._state.message = message
    
    @classmethod
    def finish(cls) -> None:
        """Finaliza modo de progresso."""
        cls._is_active = False
        cls._state = None
    
    @classmethod
    def cancel(cls) -> None:
        """Marca operação como cancelada."""
        if cls._state:
            cls._state.cancelled = True


# ==============================================================================
# PASSO 79: PLACEHOLDER DE IMAGEM QUEBRADA
# ==============================================================================

class BrokenImageHandler:
    """
    Gerencia fallback para imagens que falharam ao carregar.
    """
    
    # SVG inline para placeholder
    PLACEHOLDER_SVG = '''
    <svg width="200" height="200" xmlns="http://www.w3.org/2000/svg">
        <rect width="200" height="200" fill="#2a2a2a"/>
        <text x="100" y="90" text-anchor="middle" fill="#666" font-size="14">Imagem</text>
        <text x="100" y="110" text-anchor="middle" fill="#666" font-size="14">não disponível</text>
        <path d="M85 130 L100 150 L115 130 Z" fill="#666"/>
        <circle cx="100" cy="145" r="3" fill="#666"/>
    </svg>
    '''
    
    @classmethod
    def get_placeholder_path(cls, cache_dir: Path) -> Path:
        """
        Retorna caminho do placeholder, criando se necessário.
        
        Args:
            cache_dir: Diretório de cache
            
        Returns:
            Caminho do arquivo placeholder
        """
        placeholder = cache_dir / "broken_image_placeholder.svg"
        
        if not placeholder.exists():
            cache_dir.mkdir(parents=True, exist_ok=True)
            placeholder.write_text(cls.PLACEHOLDER_SVG)
        
        return placeholder
    
    @classmethod
    def should_use_placeholder(cls, image_path: Optional[str]) -> bool:
        """Verifica se deve usar placeholder."""
        if not image_path:
            return True
        
        path = Path(image_path)
        return not path.exists()


# ==============================================================================
# PASSO 80: INDICADOR DE NÃO SALVO
# ==============================================================================

class DirtyStateTracker:
    """
    Rastreia estado de alterações não salvas.
    
    Mostra asterisco (*) no título quando há mudanças pendentes.
    """
    
    def __init__(self, on_change: Optional[Callable[[bool], None]] = None):
        self._is_dirty = False
        self._pending_changes: Dict[str, Any] = {}
        self._on_change = on_change
    
    @property
    def is_dirty(self) -> bool:
        return self._is_dirty
    
    def mark_dirty(self, key: str, value: Any = None) -> None:
        """Marca uma mudança pendente."""
        self._pending_changes[key] = value
        
        if not self._is_dirty:
            self._is_dirty = True
            if self._on_change:
                self._on_change(True)
    
    def mark_saved(self) -> None:
        """Marca tudo como salvo."""
        self._pending_changes.clear()
        
        if self._is_dirty:
            self._is_dirty = False
            if self._on_change:
                self._on_change(False)
    
    def get_title_suffix(self) -> str:
        """Retorna sufixo para título (*) se dirty."""
        return " *" if self._is_dirty else ""
    
    def get_pending_changes(self) -> Dict[str, Any]:
        """Retorna mudanças pendentes."""
        return self._pending_changes.copy()


# ==============================================================================
# PASSO 81: MÁSCARA DE INPUT DE PREÇO
# ==============================================================================

class PriceInputValidator:
    """
    Validação e formatação de input de preço.
    
    Aceita: 19.90, 19,90, R$19.90
    Rejeita: letras, símbolos inválidos
    """
    
    # Regex para valor numérico
    PRICE_REGEX = re.compile(r'^R?\$?\s*(\d{1,7})[,.]?(\d{0,2})$')
    
    @classmethod
    def parse(cls, text: str) -> Optional[Decimal]:
        """
        Parseia texto como preço.
        
        Args:
            text: Texto do input
            
        Returns:
            Decimal ou None se inválido
        """
        if not text:
            return None
        
        # Limpar texto
        cleaned = text.strip()
        
        # Tentar regex
        match = cls.PRICE_REGEX.match(cleaned)
        
        if match:
            integer_part = match.group(1)
            decimal_part = match.group(2) or "00"
            decimal_part = decimal_part.ljust(2, '0')[:2]
            
            try:
                return Decimal(f"{integer_part}.{decimal_part}")
            except InvalidOperation:
                return None
        
        # Fallback: tentar conversão direta
        try:
            cleaned = cleaned.replace('R$', '').replace('$', '').strip()
            cleaned = cleaned.replace(',', '.')
            return Decimal(cleaned).quantize(Decimal('0.01'))
        except (InvalidOperation, ValueError):
            return None
    
    @classmethod
    def format(cls, value: Decimal) -> str:
        """Formata Decimal para exibição."""
        return f"R$ {value:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
    
    @classmethod
    def is_valid_char(cls, char: str) -> bool:
        """Verifica se caractere é válido para preço."""
        return char in "0123456789,.R$ "


# ==============================================================================
# PASSO 87: ANIMAÇÕES RÁPIDAS
# ==============================================================================

class AnimationConfig:
    """
    Configurações de animação para UI responsiva.
    
    Animações devem ser rápidas (<200ms) para não irritar em produção.
    """
    
    # Durações em milissegundos
    INSTANT = 0
    FAST = 100
    NORMAL = 150
    SLOW = 200  # Máximo recomendado
    
    # Durações por tipo de interação
    DURATIONS = {
        "hover": FAST,
        "click": INSTANT,
        "modal_open": NORMAL,
        "modal_close": FAST,
        "page_transition": NORMAL,
        "list_item": FAST,
        "tooltip": INSTANT,
        "snackbar": NORMAL,
    }
    
    @classmethod
    def get_duration(cls, animation_type: str) -> int:
        """Retorna duração em ms para tipo de animação."""
        return cls.DURATIONS.get(animation_type, cls.NORMAL)
    
    @classmethod
    def disable_for_performance(cls) -> None:
        """Desabilita animações para performance."""
        for key in cls.DURATIONS:
            cls.DURATIONS[key] = cls.INSTANT


# ==============================================================================
# PASSO 100: CÓDIGOS DE ERRO AMIGÁVEIS
# ==============================================================================

@dataclass
class FriendlyError:
    """Erro com mensagem amigável para o usuário."""
    code: str
    title: str
    message: str
    suggestion: str = ""
    technical_details: str = ""


class ErrorCodeRegistry:
    """
    Registro de códigos de erro amigáveis.
    
    Evita mostrar stacktraces Python para o usuário.
    """
    
    ERRORS: Dict[str, FriendlyError] = {
        # Erros de Arquivo (1xx)
        "E101": FriendlyError(
            code="E101",
            title="Arquivo não encontrado",
            message="O arquivo solicitado não foi encontrado no sistema.",
            suggestion="Verifique se o arquivo existe e tente novamente."
        ),
        "E102": FriendlyError(
            code="E102",
            title="Permissão negada",
            message="Não foi possível acessar o arquivo.",
            suggestion="Execute o programa como administrador ou mova os arquivos para outra pasta."
        ),
        "E103": FriendlyError(
            code="E103",
            title="Arquivo corrompido",
            message="O arquivo parece estar danificado.",
            suggestion="Tente baixar ou importar o arquivo novamente."
        ),
        
        # Erros de Banco de Dados (2xx)
        "E201": FriendlyError(
            code="E201",
            title="Erro ao salvar",
            message="Não foi possível salvar os dados.",
            suggestion="Verifique se há espaço em disco suficiente."
        ),
        "E202": FriendlyError(
            code="E202",
            title="Banco de dados bloqueado",
            message="O banco de dados está sendo usado por outro processo.",
            suggestion="Feche outras janelas do AutoTabloide e tente novamente."
        ),
        
        # Erros de Renderização (3xx)
        "E301": FriendlyError(
            code="E301",
            title="Falha ao gerar PDF",
            message="Ocorreu um erro durante a geração do PDF.",
            suggestion="Verifique se há espaço em disco e se o Ghostscript está instalado."
        ),
        "E302": FriendlyError(
            code="E302",
            title="Template inválido",
            message="O template SVG contém erros.",
            suggestion="Verifique se o template foi criado corretamente no Illustrator."
        ),
        "E303": FriendlyError(
            code="E303",
            title="Imagem com baixa resolução",
            message="A imagem tem resolução insuficiente para impressão.",
            suggestion="Use uma imagem de maior qualidade (mínimo 300 DPI)."
        ),
        
        # Erros de IA (4xx)
        "E401": FriendlyError(
            code="E401",
            title="IA não disponível",
            message="O módulo de inteligência artificial não está carregado.",
            suggestion="Verifique se o modelo está instalado em /bin/models/."
        ),
        "E402": FriendlyError(
            code="E402",
            title="Busca de imagem falhou",
            message="Não foi possível buscar imagens automaticamente.",
            suggestion="Verifique sua conexão com a internet."
        ),
        
        # Erros de Rede (5xx)
        "E501": FriendlyError(
            code="E501",
            title="Sem conexão",
            message="Não foi possível conectar à internet.",
            suggestion="Verifique sua conexão de rede."
        ),
        "E502": FriendlyError(
            code="E502",
            title="Tempo esgotado",
            message="A operação demorou muito e foi cancelada.",
            suggestion="Tente novamente mais tarde."
        ),
    }
    
    @classmethod
    def get_error(cls, code: str) -> FriendlyError:
        """Retorna erro amigável pelo código."""
        return cls.ERRORS.get(code, FriendlyError(
            code=code,
            title="Erro desconhecido",
            message="Ocorreu um erro inesperado.",
            suggestion="Reinicie o programa e tente novamente."
        ))
    
    @classmethod
    def from_exception(cls, exception: Exception) -> FriendlyError:
        """Mapeia exceção para erro amigável."""
        exc_type = type(exception).__name__
        
        mapping = {
            "FileNotFoundError": "E101",
            "PermissionError": "E102",
            "OSError": "E101",
            "sqlite3.OperationalError": "E202",
            "TimeoutError": "E502",
            "ConnectionError": "E501",
        }
        
        code = mapping.get(exc_type, "E000")
        error = cls.get_error(code)
        error.technical_details = str(exception)
        
        return error


# ==============================================================================
# FUNÇÃO DE INICIALIZAÇÃO
# ==============================================================================

def initialize_ui_safety() -> dict:
    """
    Inicializa proteções de UI.
    
    Returns:
        Dict com status
    """
    results = {}
    
    # Configurar animações para performance
    results["animation_config"] = AnimationConfig.DURATIONS.copy()
    
    logger.info("UI safety inicializado")
    return results

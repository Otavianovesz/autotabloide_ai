"""
AutoTabloide AI - Code Quality Utilities
===========================================
Utilitários de qualidade de código.
Passos 61-70 do Checklist v2.

Funcionalidades:
- Type hints (61-62)
- Substituição de prints por logger (63)
- Constantes centralizadas (65)
- Componentes extraídos (66-67)
- Testes mock (68-69)
"""

from typing import Optional, Dict, Any, List, Callable
import logging
import re

from src.core.logging_config import get_logger

logger = get_logger("CodeQuality")


# ============================================================================
# PASSO 65: Constantes centralizadas para strings mágicas
# ============================================================================

class SlotPatterns:
    """Padrões de ID para slots."""
    SLOT_PREFIX = "SLOT_"
    TXT_PREFIX = "TXT_"
    ALVO_PREFIX = "ALVO_"
    PRECO_PREFIX = "TXT_PRECO_"
    IMAGEM_PREFIX = "ALVO_IMAGEM_"
    BARCODE_PREFIX = "BARCODE_"
    PAGE_PREFIX = "PAGE_"
    
    @classmethod
    def is_slot(cls, id_str: str) -> bool:
        """Verifica se ID é um slot."""
        return id_str.startswith(cls.SLOT_PREFIX)
    
    @classmethod
    def is_text(cls, id_str: str) -> bool:
        """Verifica se ID é texto."""
        return id_str.startswith(cls.TXT_PREFIX)
    
    @classmethod
    def is_image(cls, id_str: str) -> bool:
        """Verifica se ID é imagem."""
        return id_str.startswith(cls.ALVO_PREFIX)
    
    @classmethod
    def is_price(cls, id_str: str) -> bool:
        """Verifica se ID é preço."""
        return id_str.startswith(cls.PRECO_PREFIX)
    
    @classmethod
    def extract_slot_number(cls, id_str: str) -> Optional[int]:
        """Extrai número do slot de um ID."""
        match = re.search(r'(\d+)', id_str)
        return int(match.group(1)) if match else None


class UIStrings:
    """Strings de UI centralizadas."""
    # Botões
    BTN_SAVE = "Salvar"
    BTN_CANCEL = "Cancelar"
    BTN_DELETE = "Excluir"
    BTN_EDIT = "Editar"
    BTN_ADD = "Adicionar"
    BTN_IMPORT = "Importar"
    BTN_EXPORT = "Exportar"
    
    # Mensagens
    MSG_SAVE_SUCCESS = "Salvo com sucesso!"
    MSG_SAVE_ERROR = "Erro ao salvar"
    MSG_DELETE_CONFIRM = "Tem certeza que deseja excluir?"
    MSG_LOADING = "Carregando..."
    MSG_NO_RESULTS = "Nenhum resultado encontrado"
    
    # Títulos
    TITLE_ATELIER = "Mesa de Montagem"
    TITLE_ESTOQUE = "Estoque de Produtos"
    TITLE_FACTORY = "Fábrica de PDFs"
    TITLE_SETTINGS = "Configurações"


class QualityThresholds:
    """Limites de qualidade."""
    MIN_IMAGE_WIDTH = 300
    MIN_IMAGE_HEIGHT = 300
    MAX_IMAGE_SIZE_MB = 10
    MIN_PRICE = 0.01
    MAX_PRICE = 100000.0
    MAX_NAME_LENGTH = 200


# ============================================================================
# PASSO 63: PrintToLoggerConverter
# ============================================================================

class PrintCapture:
    """
    Captura prints e redireciona para logger.
    Passo 63 do Checklist v2.
    """
    
    def __init__(self, logger_name: str = "PrintCapture"):
        self._logger = logging.getLogger(logger_name)
        self._original_stdout = None
    
    def write(self, text: str) -> None:
        """Captura output e loga."""
        text = text.strip()
        if text:
            # Detecta nível pelo conteúdo
            if "[ERROR]" in text.upper() or "ERROR:" in text.upper():
                self._logger.error(text)
            elif "[WARN" in text.upper() or "WARNING:" in text.upper():
                self._logger.warning(text)
            else:
                self._logger.info(text)
    
    def flush(self) -> None:
        """Flush obrigatório para compatibilidade."""
        pass


# ============================================================================
# PASSOS 66-67: Base para componentes extraídos
# ============================================================================

class BaseComponent:
    """
    Classe base para componentes de UI.
    Passos 66-67 do Checklist v2.
    """
    
    def __init__(self, page=None):
        self.page = page
        self._is_mounted = False
    
    def build(self):
        """Constrói o componente. Override nas subclasses."""
        raise NotImplementedError
    
    def did_mount(self):
        """Chamado após montagem."""
        self._is_mounted = True
    
    def did_unmount(self):
        """Chamado antes de desmontar."""
        self._is_mounted = False
    
    def update(self):
        """Atualiza o componente."""
        if hasattr(self, 'page') and self.page:
            self.page.update()


# ============================================================================
# PASSOS 68-69: Helpers para testes
# ============================================================================

class MockFactory:
    """
    Factory para criar mocks de teste.
    Passos 68-69 do Checklist v2.
    """
    
    @staticmethod
    def create_product(
        id: int = 1,
        name: str = "Produto Teste",
        price: float = 10.99,
        image: Optional[str] = None
    ) -> Dict[str, Any]:
        """Cria produto mock."""
        return {
            "id": id,
            "name": name,
            "price": price,
            "price_de": None,
            "image": image or "abc123hash",
            "quality": 100
        }
    
    @staticmethod
    def create_slot(
        slot_id: str = "SLOT_01",
        product: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Cria slot mock."""
        return {
            "slot_id": slot_id,
            "product_id": product["id"] if product else None,
            "product_name": product["name"] if product else None,
            "product_price": product["price"] if product else None,
            "product_image": product.get("image") if product else None,
            "override_name": None,
            "override_price": None
        }
    
    @staticmethod
    def create_layout(
        id: int = 1,
        name: str = "Layout Teste",
        slots: int = 12
    ) -> Dict[str, Any]:
        """Cria layout mock."""
        return {
            "id": id,
            "name": name,
            "slots": slots,
            "type": "A4",
            "pages": 1
        }


class AsyncMock:
    """
    Mock simples para funções async.
    """
    
    def __init__(self, return_value=None):
        self.return_value = return_value
        self.call_count = 0
        self.call_args = []
    
    async def __call__(self, *args, **kwargs):
        self.call_count += 1
        self.call_args.append((args, kwargs))
        return self.return_value


# ============================================================================
# Utilitários
# ============================================================================

def validate_type_hints(func: Callable) -> bool:
    """
    Verifica se função tem type hints.
    Passo 61 do Checklist v2.
    """
    import inspect
    sig = inspect.signature(func)
    
    for param in sig.parameters.values():
        if param.annotation == inspect.Parameter.empty:
            return False
    
    if sig.return_annotation == inspect.Signature.empty:
        return False
    
    return True

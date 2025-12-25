"""
AutoTabloide AI - Exceções Customizadas
=========================================
Hierarquia de exceções para tratamento específico.
Passos 73-74 do Checklist 100.

Classes:
- AutoTabloideException: Base para todas exceções do sistema
- ValidationError: Erros de validação de dados
- RenderError: Erros de renderização
- ImportError: Erros de importação
- DatabaseError: Erros de banco de dados
"""

from typing import Optional, Dict, Any


class AutoTabloideException(Exception):
    """
    Exceção base do Autotabloide AI.
    Todas as exceções customizadas herdam desta classe.
    """
    
    def __init__(
        self,
        message: str,
        code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        recoverable: bool = True
    ):
        """
        Inicializa exceção.
        
        Args:
            message: Mensagem legível para o usuário
            code: Código de erro para logging/debug
            details: Detalhes adicionais (dict)
            recoverable: Se o erro é recuperável (UI pode continuar)
        """
        super().__init__(message)
        self.message = message
        self.code = code or self.__class__.__name__
        self.details = details or {}
        self.recoverable = recoverable
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário para logging/API."""
        return {
            "error": self.__class__.__name__,
            "code": self.code,
            "message": self.message,
            "details": self.details,
            "recoverable": self.recoverable
        }
    
    def __str__(self) -> str:
        if self.details:
            return f"[{self.code}] {self.message} - {self.details}"
        return f"[{self.code}] {self.message}"


# ==============================================================================
# ERROS DE VALIDAÇÃO
# ==============================================================================

class ValidationError(AutoTabloideException):
    """Erro de validação de dados de entrada."""
    
    def __init__(
        self,
        message: str,
        field: Optional[str] = None,
        value: Optional[Any] = None,
        **kwargs
    ):
        details = kwargs.pop("details", {})
        if field:
            details["field"] = field
        if value is not None:
            details["invalid_value"] = str(value)[:100]
        
        super().__init__(message, code="VALIDATION_ERROR", details=details, **kwargs)


class PriceValidationError(ValidationError):
    """Erro específico de validação de preço."""
    
    def __init__(self, message: str, price_value: Any = None, **kwargs):
        super().__init__(
            message,
            field="price",
            value=price_value,
            **kwargs
        )


class ImageValidationError(ValidationError):
    """Erro de validação de imagem."""
    
    def __init__(self, message: str, file_path: Optional[str] = None, **kwargs):
        details = kwargs.pop("details", {})
        if file_path:
            details["file_path"] = file_path
        super().__init__(message, field="image", details=details, **kwargs)


# ==============================================================================
# ERROS DE RENDERIZAÇÃO
# ==============================================================================

class RenderError(AutoTabloideException):
    """Erro durante renderização de layout."""
    
    def __init__(
        self,
        message: str,
        layout_id: Optional[int] = None,
        slot_id: Optional[str] = None,
        **kwargs
    ):
        details = kwargs.pop("details", {})
        if layout_id:
            details["layout_id"] = layout_id
        if slot_id:
            details["slot_id"] = slot_id
        
        super().__init__(message, code="RENDER_ERROR", details=details, **kwargs)


class FontNotFoundError(RenderError):
    """Fonte requerida não encontrada."""
    
    def __init__(self, font_name: str, **kwargs):
        super().__init__(
            f"Fonte não encontrada: {font_name}",
            **kwargs
        )
        self.details["missing_font"] = font_name


class LayoutStructureError(RenderError):
    """Estrutura do layout SVG inválida."""
    
    def __init__(self, message: str, missing_element: Optional[str] = None, **kwargs):
        details = kwargs.pop("details", {})
        if missing_element:
            details["missing_element"] = missing_element
        super().__init__(message, details=details, **kwargs)


class TextOverflowError(RenderError):
    """
    Texto não cabe no slot mesmo com fontes mínimas (#104 Industrial Robustness).
    Lançada quando a busca binária retorna fonte < MIN_FONT_SIZE (6pt).
    Força intervenção humana em vez de gerar PDF ilegível.
    """
    
    def __init__(
        self,
        slot_id: str,
        text: str,
        min_font_attempted: float,
        required_width: float,
        available_width: float,
        **kwargs
    ):
        msg = (
            f"Texto não cabe no slot '{slot_id}': "
            f"'{text[:50]}...' requer {required_width:.0f}px mas slot tem {available_width:.0f}px. "
            f"Fonte mínima {min_font_attempted:.1f}pt é ilegível."
        )
        super().__init__(msg, slot_id=slot_id, recoverable=True, **kwargs)
        self.details.update({
            "text_preview": text[:100],
            "min_font_pt": min_font_attempted,
            "required_width_px": required_width,
            "available_width_px": available_width
        })


class LowDPIError(RenderError):
    """
    Imagem com DPI efetivo abaixo do mínimo para impressão (#102 Industrial Robustness).
    Lançada quando imagem esticada no slot resulta em DPI < 250.
    """
    
    def __init__(
        self,
        image_path: str,
        effective_dpi: float,
        required_dpi: float = 250.0,
        slot_id: Optional[str] = None,
        **kwargs
    ):
        msg = (
            f"Imagem com baixa resolução: '{image_path}' tem {effective_dpi:.0f} DPI efetivo "
            f"(mínimo {required_dpi:.0f} DPI para impressão profissional)."
        )
        super().__init__(msg, slot_id=slot_id, recoverable=True, **kwargs)
        self.details.update({
            "image_path": image_path,
            "effective_dpi": effective_dpi,
            "required_dpi": required_dpi
        })


# ==============================================================================
# ERROS DE IMPORTAÇÃO
# ==============================================================================

class DataImportError(AutoTabloideException):
    """Erro durante importação de dados."""
    
    def __init__(
        self,
        message: str,
        file_path: Optional[str] = None,
        row_number: Optional[int] = None,
        **kwargs
    ):
        details = kwargs.pop("details", {})
        if file_path:
            details["file_path"] = file_path
        if row_number:
            details["row_number"] = row_number
        
        super().__init__(message, code="IMPORT_ERROR", details=details, **kwargs)


class FileFormatError(DataImportError):
    """Formato de arquivo não suportado."""
    
    def __init__(self, file_path: str, expected_formats: list = None, **kwargs):
        msg = f"Formato de arquivo não suportado: {file_path}"
        if expected_formats:
            msg += f". Formatos aceitos: {', '.join(expected_formats)}"
        super().__init__(msg, file_path=file_path, **kwargs)


class ColumnMappingError(DataImportError):
    """Colunas necessárias não encontradas no arquivo."""
    
    def __init__(self, missing_columns: list, **kwargs):
        super().__init__(
            f"Colunas obrigatórias não encontradas: {', '.join(missing_columns)}",
            **kwargs
        )
        self.details["missing_columns"] = missing_columns


# ==============================================================================
# ERROS DE BANCO DE DADOS
# ==============================================================================

class DatabaseError(AutoTabloideException):
    """Erro de operação no banco de dados."""
    
    def __init__(self, message: str, operation: Optional[str] = None, **kwargs):
        details = kwargs.pop("details", {})
        if operation:
            details["operation"] = operation
        
        super().__init__(
            message,
            code="DATABASE_ERROR",
            details=details,
            recoverable=False,  # Erros de DB geralmente são graves
            **kwargs
        )


class IntegrityError(DatabaseError):
    """Violação de integridade referencial."""
    pass


class ConnectionError(DatabaseError):
    """Erro de conexão com banco."""
    pass


# ==============================================================================
# ERROS DE IA
# ==============================================================================

class AIError(AutoTabloideException):
    """Erro em operação de IA."""
    
    def __init__(self, message: str, model: Optional[str] = None, **kwargs):
        details = kwargs.pop("details", {})
        if model:
            details["model"] = model
        
        super().__init__(message, code="AI_ERROR", details=details, **kwargs)


class ModelNotFoundError(AIError):
    """Modelo de IA não encontrado."""
    
    def __init__(self, model_path: str, **kwargs):
        super().__init__(
            f"Modelo não encontrado: {model_path}",
            **kwargs
        )
        self.details["model_path"] = model_path


class InferenceError(AIError):
    """Erro durante inferência do modelo."""
    pass


class PromptInjectionError(AIError):
    """
    Tentativa de prompt injection detectada (#108 Industrial Robustness).
    Lançada quando descrições de produtos contêm comandos suspeitos para o LLM.
    """
    
    INJECTION_PATTERNS = [
        "ignore previous",
        "ignore all",
        "disregard",
        "forget your instructions",
        "system prompt",
        "you are now",
        "act as",
        "pretend to be",
        "output:",
        "respond with:",
    ]
    
    def __init__(self, detected_pattern: str, original_text: str, **kwargs):
        msg = f"Possível prompt injection detectado: padrão '{detected_pattern}' encontrado"
        super().__init__(msg, recoverable=True, **kwargs)
        self.details.update({
            "detected_pattern": detected_pattern,
            "text_preview": original_text[:200]
        })
    
    @classmethod
    def check_text(cls, text: str) -> bool:
        """Verifica se texto contém padrões de injection."""
        text_lower = text.lower()
        for pattern in cls.INJECTION_PATTERNS:
            if pattern in text_lower:
                return True
        return False
    
    @classmethod
    def sanitize_or_raise(cls, text: str) -> str:
        """Verifica e lança exceção se encontrar injection."""
        text_lower = text.lower()
        for pattern in cls.INJECTION_PATTERNS:
            if pattern in text_lower:
                raise cls(detected_pattern=pattern, original_text=text)
        return text


# ==============================================================================
# ERROS DE ARQUIVO
# ==============================================================================

class FileError(AutoTabloideException):
    """Erro de operação de arquivo."""
    
    def __init__(self, message: str, file_path: Optional[str] = None, **kwargs):
        details = kwargs.pop("details", {})
        if file_path:
            details["file_path"] = file_path
        
        super().__init__(message, code="FILE_ERROR", details=details, **kwargs)


class FileNotFoundError(FileError):
    """Arquivo não encontrado."""
    
    def __init__(self, file_path: str, **kwargs):
        super().__init__(f"Arquivo não encontrado: {file_path}", file_path=file_path, **kwargs)


class PermissionError(FileError):
    """Sem permissão para acessar arquivo."""
    
    def __init__(self, file_path: str, operation: str = "access", **kwargs):
        super().__init__(
            f"Sem permissão para {operation}: {file_path}",
            file_path=file_path,
            **kwargs
        )


# ==============================================================================
# MENSAGENS AMIGÁVEIS (Passo 94)
# ==============================================================================

FRIENDLY_MESSAGES = {
    "ConnectionRefused": "Sem conexão com a internet",
    "TimeoutError": "A operação demorou demais. Tente novamente.",
    "MemoryError": "Memória insuficiente. Feche outros programas.",
    "DiskFull": "Disco cheio. Libere espaço e tente novamente.",
    "PermissionDenied": "Sem permissão. Execute como administrador.",
    "FileInUse": "Arquivo em uso por outro programa. Feche-o e tente novamente.",
}


def get_friendly_message(error: Exception) -> str:
    """
    Converte erro técnico em mensagem amigável.
    Passo 94 do Checklist.
    
    Args:
        error: Exceção original
        
    Returns:
        Mensagem legível para o usuário
    """
    error_name = type(error).__name__
    error_msg = str(error)
    
    # Verificar mapeamento direto
    if error_name in FRIENDLY_MESSAGES:
        return FRIENDLY_MESSAGES[error_name]
    
    # Verificar por substring
    for key, friendly_msg in FRIENDLY_MESSAGES.items():
        if key.lower() in error_msg.lower():
            return friendly_msg
    
    # Se for AutoTabloideException, usar mensagem dela
    if isinstance(error, AutoTabloideException):
        return error.message
    
    # Fallback
    return f"Ocorreu um erro: {error_msg}"

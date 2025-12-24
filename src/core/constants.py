"""
AutoTabloide AI - Constantes Globais
=====================================
Conforme Auditoria Industrial: Eliminar hardcoding de strings.
Single Source of Truth para valores imutáveis do sistema.
"""

from enum import Enum, auto
from pathlib import Path
from decimal import Decimal


# ==============================================================================
# PATHS DINÂMICOS (Passo 12 - Centralização)
# ==============================================================================

# Diretório base é o pai do src/
BASE_DIR = Path(__file__).parent.parent.parent.resolve()
SYSTEM_ROOT = BASE_DIR / "AutoTabloide_System_Root"

# Paths derivados para uso em todo o sistema
DB_DIR = SYSTEM_ROOT / "database"
LOGS_DIR = SYSTEM_ROOT / "logs"
CACHE_DIR = SYSTEM_ROOT / "cache"
CONFIG_DIR = SYSTEM_ROOT / "config"
ASSETS_DIR = SYSTEM_ROOT / "assets"
FONTS_DIR = ASSETS_DIR / "fonts"
STAGING_DIR = SYSTEM_ROOT / "staging"
TEMP_DIR = SYSTEM_ROOT / "temp"


# ==============================================================================
# IDENTIDADE DO SISTEMA
# ==============================================================================

class AppInfo:
    """Informações da aplicação."""
    NAME = "AutoTabloide AI"
    VERSION = "1.0.0"
    CODENAME = "Industrial Engine"
    AUTHOR = "Otávio Novesz"


# ==============================================================================
# SISTEMA DE ARQUIVOS (Conforme Vol. I - Bunker Digital)
# ==============================================================================

class SystemPaths:
    """
    Caminhos do sistema hermético.
    Todos os paths são relativos ao ROOT que é resolvido em runtime.
    """
    # Diretórios principais
    BIN = "bin"
    CONFIG = "config"
    DATABASE = "database"
    ASSETS = "assets"
    STAGING = "staging"
    TEMP = "temp"
    LIBRARY = "library"
    WORKSPACES = "workspaces"
    SNAPSHOTS = "snapshots"
    LOGS = "logs"
    
    # Subdiretórios de assets
    ASSETS_STORE = "assets/store"
    ASSETS_THUMBS = "assets/thumbs"
    ASSETS_FONTS = "assets/fonts"
    ASSETS_ICC = "assets/icc"
    
    # Subdiretórios de library
    LIBRARY_SVG = "library/svg_source"
    LIBRARY_THUMBS = "library/thumbnails"
    
    # Arquivos críticos
    DATABASE_FILE = "database/core.db"
    SETTINGS_FILE = "config/settings.json"
    SAFE_MODE_FLAG = "config/.safe_mode"


# ==============================================================================
# BANCO DE DADOS
# ==============================================================================

class DatabaseConfig:
    """Configurações do SQLite."""
    JOURNAL_MODE = "WAL"
    SYNCHRONOUS = "NORMAL"
    CACHE_SIZE = -64000  # 64MB
    TEMP_STORE = "MEMORY"
    MMAP_SIZE = 268435456  # 256MB
    PAGE_SIZE = 4096
    BUSY_TIMEOUT = 5000  # 5 segundos


# ==============================================================================
# RENDERIZAÇÃO E IMPRESSÃO (Conforme Vol. II)
# ==============================================================================

class RenderConfig:
    """Configurações do motor de renderização."""
    # Resolução
    DPI_SCREEN = 96
    DPI_PRINT = 300
    DPI_PROOF = 150
    
    # Conversões de unidade
    MM_PER_INCH = 25.4
    PT_PER_INCH = 72.0
    
    # Sangria padrão (bleed)
    BLEED_MM = 3.0
    CROP_MARK_LENGTH_MM = 5.0
    CROP_MARK_OFFSET_MM = 3.0
    
    # Tamanhos de página em mm
    A4_WIDTH_MM = 210.0
    A4_HEIGHT_MM = 297.0
    A3_WIDTH_MM = 297.0
    A3_HEIGHT_MM = 420.0
    
    @classmethod
    def mm_to_pt(cls, mm: float) -> float:
        """Converte milímetros para pontos tipográficos."""
        return mm * cls.PT_PER_INCH / cls.MM_PER_INCH
    
    @classmethod
    def pt_to_mm(cls, pt: float) -> float:
        """Converte pontos tipográficos para milímetros."""
        return pt * cls.MM_PER_INCH / cls.PT_PER_INCH
    
    @classmethod
    def mm_to_px(cls, mm: float, dpi: int = 96) -> float:
        """Converte milímetros para pixels."""
        return mm * dpi / cls.MM_PER_INCH


class ColorMode(Enum):
    """Modos de cor para exportação."""
    RGB = "rgb"
    CMYK = "cmyk"
    AUTO = "auto"


class PDFStandard(Enum):
    """Padrões PDF/X para impressão."""
    PDFX1A = "pdfx1a"
    PDFX4 = "pdfx4"
    PDF15 = "pdf1.5"


class TrueBlack:
    """
    Valores para preto puro em impressão.
    Conforme Vol. II: Texto preto deve ser K=100%, não Rich Black.
    """
    RGB = (0, 0, 0)
    CMYK = (0, 0, 0, 100)  # C=0, M=0, Y=0, K=100
    HEX = "#000000"


# ==============================================================================
# TEXTO E TIPOGRAFIA
# ==============================================================================

class Typography:
    """Configurações tipográficas."""
    # Fontes padrão
    FONT_UI = "Roboto"
    FONT_DATA = "JetBrains Mono"
    FONT_PRICE = "Roboto Bold"
    
    # Tamanhos mínimos (em pt)
    MIN_SIZE_PRINT = 6
    MIN_SIZE_SCREEN = 10
    
    # Text fitting
    SHRINK_STEP = 0.5  # Decremento em pt para busca binária
    MIN_SHRINK_RATIO = 0.6  # Mínimo 60% do tamanho original
    LINE_HEIGHT_RATIO = 1.2


# ==============================================================================
# QUALIDADE DE DADOS (Conforme Vol. III - Semáforo)
# ==============================================================================

class QualityThresholds:
    """Limiares para o semáforo de qualidade."""
    # Resolução de imagem
    IMAGE_EXCELLENT = 800  # px
    IMAGE_ACCEPTABLE = 400  # px
    IMAGE_MINIMUM = 200  # px
    
    # Idade de dados (dias)
    PRICE_FRESH = 7
    PRICE_STALE = 30
    
    # Score BRISQUE (menor = melhor)
    BRISQUE_EXCELLENT = 30
    BRISQUE_GOOD = 50
    BRISQUE_ACCEPTABLE = 70


# ==============================================================================
# INTELIGÊNCIA ARTIFICIAL (Conforme Vol. IV)
# ==============================================================================

class AIConfig:
    """Configurações do motor de IA."""
    # Modelo LLM
    MODEL_QUANTIZATION = "Q4_K_M"
    MAX_TOKENS = 512
    TEMPERATURE = 0.1  # Baixo para determinismo
    TOP_P = 0.9
    
    # Retry e timeout
    MAX_RETRIES = 3
    RETRY_BASE_DELAY = 1.0  # segundos
    RETRY_MAX_DELAY = 30.0
    REQUEST_TIMEOUT = 60.0  # segundos
    
    # Fuzzy matching
    FUZZY_THRESHOLD_EXACT = 99
    FUZZY_THRESHOLD_HIGH = 85
    FUZZY_THRESHOLD_MEDIUM = 70


# ==============================================================================
# INTERFACE GRÁFICA (Conforme Vol. VI)
# ==============================================================================

class UIConfig:
    """Configurações da interface."""
    # Janela
    MIN_WIDTH = 1280
    MIN_HEIGHT = 720
    
    # NavigationRail
    RAIL_WIDTH_EXPANDED = 250
    RAIL_WIDTH_COLLAPSED = 72
    
    # Performance
    DEBOUNCE_MS = 300
    AUTOSAVE_DELAY_S = 3
    LAZY_LOAD_THRESHOLD = 0.8  # 80% do scroll
    PAGE_SIZE = 50
    
    # Undo/Redo
    UNDO_STACK_LIMIT = 30
    
    # Animações
    ANIMATION_DURATION_MS = 200
    PULSE_DURATION_MS = 800


# ==============================================================================
# UNIDADES DE MEDIDA (Normalização)
# ==============================================================================

class UnitPatterns:
    """
    Padrões de regex para normalização de unidades.
    Conforme Vol. IV: 'ml' minúsculo, 'L' maiúsculo.
    """
    PATTERNS = {
        r'(\d)\s*ml\b': r'\1ml',           # Mililitros sempre minúsculo
        r'(\d)\s*l\b': r'\1L',              # Litros sempre maiúsculo
        r'(\d)\s*kg\b': r'\1kg',            # Quilos minúsculo
        r'(\d)\s*g\b': r'\1g',              # Gramas minúsculo
        r'(\d)\s*un\.?\b': r'\1un',         # Unidades
        r'(\d)\s*pç\.?\b': r'\1pç',         # Peças
        r'(\d)\s*cx\.?\b': r'\1cx',         # Caixa
        r'(\d)\s*pct\.?\b': r'\1pct',       # Pacote
    }


# ==============================================================================
# MIME TYPES
# ==============================================================================

class MimeTypes:
    """Tipos MIME para arquivos."""
    PDF = "application/pdf"
    SVG = "image/svg+xml"
    PNG = "image/png"
    JPEG = "image/jpeg"
    WEBP = "image/webp"
    JSON = "application/json"
    CSV = "text/csv"
    EXCEL = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


# ==============================================================================
# MENSAGENS DE ERRO
# ==============================================================================

class ErrorMessages:
    """Mensagens de erro padronizadas."""
    DB_LOCKED = "Banco de dados bloqueado. Tente novamente."
    DB_CORRUPTED = "Banco de dados corrompido. Iniciando modo de segurança."
    FONT_NOT_FOUND = "Fonte '{}' não encontrada. Verifique instalação."
    SVG_INVALID = "Template SVG inválido: {}"
    IMAGE_CORRUPT = "Imagem corrompida ou ilegível: {}"
    NETWORK_ERROR = "Erro de rede: {}"
    AI_TIMEOUT = "Tempo limite de processamento IA excedido."
    GHOSTSCRIPT_MISSING = "Ghostscript não encontrado. Conversão CMYK indisponível."


# ==============================================================================
# MENSAGENS DE SUCESSO
# ==============================================================================

class SuccessMessages:
    """Mensagens de sucesso padronizadas."""
    PROJECT_SAVED = "Projeto salvo com sucesso."
    PDF_EXPORTED = "PDF exportado: {}"
    IMAGE_PROCESSED = "Imagem processada com sucesso."
    DATA_IMPORTED = "Dados importados: {} registros."
    BACKUP_CREATED = "Backup criado: {}"

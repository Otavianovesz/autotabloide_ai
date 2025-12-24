"""
AutoTabloide AI - Schemas de Validação (Pydantic)
==================================================
Conforme Auditoria Industrial: Validar dados de entrada/saída.
Elimina KeyError e garante tipagem forte em runtime.
"""

from __future__ import annotations
from typing import Optional, List, Dict, Any
from decimal import Decimal
from datetime import datetime
from pathlib import Path
from enum import Enum

from pydantic import (
    BaseModel, 
    Field, 
    field_validator,
    model_validator,
    ConfigDict
)


# ==============================================================================
# ENUMS DE VALIDAÇÃO
# ==============================================================================

class TipoMidiaEnum(str, Enum):
    """Tipos de mídia para layouts."""
    TABLOIDE = "TABLOIDE"
    CARTAZ_A4 = "CARTAZ_A4"
    CARTAZ_GIGANTE = "CARTAZ_GIGANTE"
    ETIQUETA = "ETIQUETA"


class StatusQualidadeEnum(int, Enum):
    """Status de qualidade do produto."""
    CRITICO = 0
    INCOMPLETO = 1
    ATENCAO = 2
    PERFEITO = 3


class TipoAcaoEnum(str, Enum):
    """Tipos de ação para auditoria."""
    CREATE = "CREATE"
    UPDATE = "UPDATE"
    DELETE = "DELETE"
    IMPORT = "IMPORT"
    PRINT = "PRINT"
    ROLLBACK = "ROLLBACK"


# ==============================================================================
# SCHEMAS DE PRODUTO
# ==============================================================================

class ProdutoBase(BaseModel):
    """Schema base de produto."""
    
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True
    )
    
    nome_sanitizado: str = Field(
        ..., 
        min_length=1, 
        max_length=200,
        description="Nome limpo e formatado do produto"
    )
    
    preco_venda: Decimal = Field(
        ...,
        gt=Decimal("0"),
        le=Decimal("999999.99"),
        decimal_places=2,
        description="Preço de venda em reais"
    )
    
    preco_referencia: Optional[Decimal] = Field(
        None,
        ge=Decimal("0"),
        le=Decimal("999999.99"),
        decimal_places=2,
        description="Preço 'De' para promoções"
    )
    
    @field_validator('preco_venda', 'preco_referencia', mode='before')
    @classmethod
    def convert_to_decimal(cls, v):
        """Converte float para Decimal."""
        if v is None:
            return v
        if isinstance(v, float):
            return Decimal(str(v))
        if isinstance(v, str):
            # Suporta formato brasileiro (vírgula)
            return Decimal(v.replace(',', '.'))
        return v


class ProdutoCreate(ProdutoBase):
    """Schema para criação de produto."""
    
    sku: Optional[str] = Field(None, max_length=50)
    codigo_barras: Optional[str] = Field(None, max_length=20)
    marca: Optional[str] = Field(None, max_length=100)
    categoria: Optional[str] = Field(None, max_length=100)
    detalhe_peso: Optional[str] = Field(None, max_length=50)
    img_hash_ref: Optional[str] = Field(None, pattern=r'^[a-f0-9]{32}$')


class ProdutoUpdate(BaseModel):
    """Schema para atualização parcial de produto."""
    
    model_config = ConfigDict(str_strip_whitespace=True)
    
    nome_sanitizado: Optional[str] = Field(None, min_length=1, max_length=200)
    preco_venda: Optional[Decimal] = Field(None, gt=Decimal("0"))
    preco_referencia: Optional[Decimal] = None
    marca: Optional[str] = None
    categoria: Optional[str] = None
    detalhe_peso: Optional[str] = None
    img_hash_ref: Optional[str] = None
    
    @field_validator('preco_venda', 'preco_referencia', mode='before')
    @classmethod
    def convert_to_decimal(cls, v):
        if v is None:
            return v
        if isinstance(v, float):
            return Decimal(str(v))
        return v


class ProdutoResponse(ProdutoBase):
    """Schema de resposta de produto."""
    
    id: int
    sku: Optional[str] = None
    codigo_barras: Optional[str] = None
    marca: Optional[str] = None
    categoria: Optional[str] = None
    detalhe_peso: Optional[str] = None
    img_hash_ref: Optional[str] = None
    status_qualidade: StatusQualidadeEnum = StatusQualidadeEnum.INCOMPLETO
    created_at: datetime
    updated_at: datetime


# ==============================================================================
# SCHEMAS DE SAÍDA DA IA
# ==============================================================================

class AISanitizationResult(BaseModel):
    """
    Schema para validar saída do LLM na sanitização.
    Conforme Vol. IV: Output JSON determinístico via GBNF.
    """
    
    model_config = ConfigDict(extra='ignore')
    
    nome: str = Field(..., min_length=1, max_length=200)
    peso: Optional[str] = Field(None, max_length=50)
    unidade: Optional[str] = Field(None, max_length=20)
    marca: Optional[str] = Field(None, max_length=100)
    
    @field_validator('nome')
    @classmethod
    def clean_nome(cls, v: str) -> str:
        """Remove espaços extras e normaliza."""
        return ' '.join(v.split())
    
    @field_validator('unidade')
    @classmethod
    def normalize_unit(cls, v: Optional[str]) -> Optional[str]:
        """Normaliza unidades (ml, L, kg)."""
        if v is None:
            return v
        # Regra do 'L' maiúsculo
        v = v.strip().lower()
        if v == 'l' or v == 'lt' or v == 'litro':
            return 'L'
        return v


class AIFuzzyMatchResult(BaseModel):
    """Schema para resultado de fuzzy matching."""
    
    produto_id: int = Field(..., gt=0)
    confianca: float = Field(..., ge=0.0, le=100.0)
    nome_sugerido: str
    
    @property
    def is_exact_match(self) -> bool:
        return self.confianca >= 99.0
    
    @property
    def is_high_confidence(self) -> bool:
        return self.confianca >= 85.0


# ==============================================================================
# SCHEMAS DE PROJETO
# ==============================================================================

class SlotDataSchema(BaseModel):
    """Schema de dados de um slot no projeto."""
    
    slot_id: str = Field(..., pattern=r'^SLOT_\d{2}$')
    produtos: List[int] = Field(default_factory=list)
    override_nome: Optional[str] = None
    override_preco: Optional[Decimal] = None
    override_preco_ref: Optional[Decimal] = None
    
    @field_validator('produtos')
    @classmethod
    def validate_produtos(cls, v: List[int]) -> List[int]:
        """Valida lista de IDs de produtos."""
        if len(v) > 5:  # Limite de produtos por slot (Kits)
            raise ValueError("Máximo de 5 produtos por slot")
        return v


class ProjetoCreate(BaseModel):
    """Schema para criação de projeto."""
    
    nome: str = Field(..., min_length=1, max_length=200)
    layout_id: int = Field(..., gt=0)
    slots: Dict[str, SlotDataSchema] = Field(default_factory=dict)


class ProjetoSnapshot(BaseModel):
    """
    Schema do snapshot imutável de projeto.
    Conforme Vol. V: Fidelidade histórica.
    """
    
    projeto_id: int
    layout_path: str
    timestamp: datetime
    slots: Dict[str, Dict[str, Any]]  # Snapshot completo
    overrides: Dict[str, Dict[str, Any]]
    
    model_config = ConfigDict(frozen=True)


# ==============================================================================
# SCHEMAS DE CONFIGURAÇÃO
# ==============================================================================

class SettingsSchema(BaseModel):
    """
    Schema para settings.json com validação.
    Permite self-healing em caso de corrupção.
    """
    
    model_config = ConfigDict(
        validate_default=True,
        extra='ignore'
    )
    
    # Caminhos
    system_root: str = Field(default="./AutoTabloide_System_Root")
    
    # Tipografia
    title_case_enabled: bool = Field(default=True)
    unit_case_uppercase: bool = Field(default=False)  # ml vs ML
    
    # IA
    ai_model_quantization: str = Field(default="Q4_K_M")
    ai_fuzzy_threshold: float = Field(default=70.0, ge=0.0, le=100.0)
    
    # Segurança
    alcohol_categories: List[str] = Field(
        default=["Bebida Alcoólica", "Cerveja", "Vinho", "Destilado"]
    )
    
    # UI
    theme_mode: str = Field(default="dark")
    autosave_enabled: bool = Field(default=True)
    autosave_delay_seconds: int = Field(default=3, ge=1, le=60)
    
    # Exportação
    default_color_mode: str = Field(default="cmyk")
    default_dpi: int = Field(default=300, ge=72, le=600)
    
    @classmethod
    def get_defaults(cls) -> 'SettingsSchema':
        """Retorna instância com valores padrão."""
        return cls()


# ==============================================================================
# SCHEMAS DE IMPORTAÇÃO
# ==============================================================================

class ImportRowSchema(BaseModel):
    """Schema para linha de importação Excel/CSV."""
    
    model_config = ConfigDict(
        str_strip_whitespace=True,
        extra='ignore'
    )
    
    descricao: str = Field(..., min_length=1, alias='Descrição')
    preco_de: Optional[Decimal] = Field(None, alias='Preço De')
    preco_por: Decimal = Field(..., gt=Decimal("0"), alias='Preço Por')
    gramatura: Optional[str] = Field(None, alias='Gramatura')
    codigo: Optional[str] = Field(None, alias='Código')
    
    @field_validator('preco_de', 'preco_por', mode='before')
    @classmethod
    def parse_price(cls, v):
        """Parse de preço com suporte a formatos BR."""
        if v is None or v == '':
            return None
        if isinstance(v, (int, float)):
            return Decimal(str(v))
        if isinstance(v, str):
            # Remove R$, espaços e converte vírgula
            cleaned = v.replace('R$', '').replace(' ', '').replace(',', '.')
            return Decimal(cleaned) if cleaned else None
        return v


# ==============================================================================
# UTILITÁRIOS DE VALIDAÇÃO
# ==============================================================================

def validate_or_default(
    data: Dict[str, Any], 
    schema: type[BaseModel],
    defaults: Optional[BaseModel] = None
) -> BaseModel:
    """
    Valida dados ou retorna defaults se inválidos.
    Implementa self-healing para configurações.
    
    Args:
        data: Dados a validar
        schema: Classe Pydantic
        defaults: Instância padrão para fallback
        
    Returns:
        Instância validada ou padrão
    """
    try:
        return schema.model_validate(data)
    except Exception:
        if defaults:
            return defaults
        if hasattr(schema, 'get_defaults'):
            return schema.get_defaults()
        return schema()

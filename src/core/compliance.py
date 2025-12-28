"""
AutoTabloide AI - Compliance Validator
======================================
PROTOCOLO DE CONVERGÊNCIA INDUSTRIAL - Fase 8
Passos 211-220: Validação de conformidade legal.

Validações:
- +18 para bebidas alcoólicas e tabaco
- De/Por (preço referência > preço atual)
- Ofertas válidas (prazo, estoque)
- Texto legal obrigatório
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set
from datetime import date, datetime
from decimal import Decimal
import logging

logger = logging.getLogger("Compliance")


# =============================================================================
# EXCEÇÕES
# =============================================================================

class ComplianceError(Exception):
    """Erro de conformidade legal."""
    pass


class PriceViolation(ComplianceError):
    """Violação de precificação."""
    def __init__(self, slot_id: str, message: str, price_de: float, price_por: float):
        self.slot_id = slot_id
        self.price_de = price_de
        self.price_por = price_por
        super().__init__(f"[{slot_id}] {message}")


class AgeRestrictionMissing(ComplianceError):
    """Falta ícone +18 em categoria restrita."""
    def __init__(self, slot_id: str, category: str):
        self.slot_id = slot_id
        self.category = category
        super().__init__(f"[{slot_id}] Categoria '{category}' requer ícone +18")


class ExpiredOffer(ComplianceError):
    """Oferta expirada."""
    def __init__(self, slot_id: str, expiry_date: date):
        self.slot_id = slot_id
        self.expiry_date = expiry_date
        super().__init__(f"[{slot_id}] Oferta expirou em {expiry_date}")


# =============================================================================
# CONFIGURAÇÃO
# =============================================================================

@dataclass
class ComplianceConfig:
    """Configuração de compliance."""
    
    # Categorias que requerem +18
    restricted_categories: Set[str] = field(default_factory=lambda: {
        "bebida alcoólica", "alcoolica", "alcoólico",
        "cerveja", "vinho", "vodka", "whisky", "whiskey",
        "cachaça", "rum", "gin", "tequila", "licor",
        "cigarro", "tabaco", "tabacaria", "fumo",
        "energético", "energy drink"
    })
    
    # Texto legal padrão
    default_legal_text: str = "Ofertas válidas enquanto durarem os estoques. Imagens meramente ilustrativas."
    
    # Validações ativas
    enforce_de_por: bool = True        # Valida De > Por
    enforce_age_icons: bool = True      # Exige ícone +18
    enforce_expiry: bool = True         # Valida data de validade
    enforce_stock: bool = False         # Valida estoque (requer integração)
    
    # Tolerâncias
    min_discount_percentage: float = 1.0  # Desconto mínimo para mostrar "De"
    max_discount_percentage: float = 90.0 # Desconto máximo (anti-fraude)


# =============================================================================
# RESULTADO DE VALIDAÇÃO
# =============================================================================

@dataclass
class ValidationResult:
    """Resultado de uma validação."""
    is_valid: bool
    errors: List[ComplianceError] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    
    @property
    def has_errors(self) -> bool:
        return len(self.errors) > 0
    
    @property  
    def has_warnings(self) -> bool:
        return len(self.warnings) > 0
    
    def add_error(self, error: ComplianceError):
        self.errors.append(error)
        self.is_valid = False
    
    def add_warning(self, message: str):
        self.warnings.append(message)


# =============================================================================
# COMPLIANCE VALIDATOR
# =============================================================================

class ComplianceValidator:
    """
    Validador de Conformidade Legal.
    
    Verifica se um layout de tabloide está em conformidade com:
    - Regulamentações de precificação
    - Restrições de idade (+18)
    - Validade de ofertas
    - Requisitos legais de texto
    """
    
    def __init__(self, config: ComplianceConfig = None):
        self.config = config or ComplianceConfig()
    
    def validate_slot(self, slot_data: Dict) -> ValidationResult:
        """
        Valida um slot individual.
        
        Args:
            slot_data: Dados do produto no slot
            
        Returns:
            ValidationResult com erros e warnings
        """
        result = ValidationResult(is_valid=True)
        slot_id = slot_data.get("slot_id", "?")
        
        # 1. Validação De/Por
        if self.config.enforce_de_por:
            self._validate_price(slot_data, result)
        
        # 2. Validação +18
        if self.config.enforce_age_icons:
            self._validate_age_restriction(slot_data, result)
        
        # 3. Validação de validade
        if self.config.enforce_expiry:
            self._validate_expiry(slot_data, result)
        
        return result
    
    def validate_layout(self, slots: List[Dict], legal_text: Optional[str] = None) -> ValidationResult:
        """
        Valida layout completo.
        
        Args:
            slots: Lista de dados de slots
            legal_text: Texto legal do layout
            
        Returns:
            ValidationResult agregado
        """
        result = ValidationResult(is_valid=True)
        
        # Valida cada slot
        for slot_data in slots:
            slot_result = self.validate_slot(slot_data)
            result.errors.extend(slot_result.errors)
            result.warnings.extend(slot_result.warnings)
        
        # Valida texto legal
        if legal_text is None or len(legal_text.strip()) < 10:
            result.add_warning("Texto legal ausente ou muito curto")
        
        result.is_valid = len(result.errors) == 0
        return result
    
    def _validate_price(self, slot_data: Dict, result: ValidationResult):
        """Valida precificação De/Por."""
        slot_id = slot_data.get("slot_id", "?")
        preco_por = slot_data.get("preco_venda_atual")
        preco_de = slot_data.get("preco_referencia")
        
        if preco_por is None:
            result.add_warning(f"[{slot_id}] Preço não definido")
            return
        
        if preco_por <= 0:
            result.add_error(PriceViolation(
                slot_id, "Preço deve ser maior que zero",
                price_de=preco_de or 0, price_por=preco_por
            ))
            return
        
        if preco_de is not None:
            if preco_de <= preco_por:
                # Violação: preço De menor ou igual ao Por
                result.add_error(PriceViolation(
                    slot_id,
                    f"Preço 'De' (R$ {preco_de:.2f}) deve ser maior que 'Por' (R$ {preco_por:.2f})",
                    price_de=preco_de, price_por=preco_por
                ))
                return
            
            # Calcula desconto
            desconto = ((preco_de - preco_por) / preco_de) * 100
            
            if desconto < self.config.min_discount_percentage:
                result.add_warning(
                    f"[{slot_id}] Desconto muito pequeno ({desconto:.1f}%), considere remover preço 'De'"
                )
            
            if desconto > self.config.max_discount_percentage:
                result.add_error(PriceViolation(
                    slot_id,
                    f"Desconto de {desconto:.1f}% parece irreal (máximo: {self.config.max_discount_percentage}%)",
                    price_de=preco_de, price_por=preco_por
                ))
    
    def _validate_age_restriction(self, slot_data: Dict, result: ValidationResult):
        """Valida restrição de idade."""
        slot_id = slot_data.get("slot_id", "?")
        categoria = slot_data.get("categoria", "").lower()
        nome = slot_data.get("nome_sanitizado", "").lower()
        has_icon = slot_data.get("has_age_icon", False)
        
        # Verifica se categoria é restrita
        is_restricted = any(cat in categoria for cat in self.config.restricted_categories)
        
        # Também verifica pelo nome do produto
        if not is_restricted:
            restricted_keywords = ["cerveja", "vinho", "vodka", "whisky", "cigarro", "tabaco"]
            is_restricted = any(kw in nome for kw in restricted_keywords)
        
        if is_restricted and not has_icon:
            result.add_error(AgeRestrictionMissing(slot_id, categoria or "detectado no nome"))
    
    def _validate_expiry(self, slot_data: Dict, result: ValidationResult):
        """Valida data de validade da oferta."""
        slot_id = slot_data.get("slot_id", "?")
        expiry = slot_data.get("data_validade")
        
        if expiry is None:
            return
        
        if isinstance(expiry, str):
            try:
                expiry = datetime.strptime(expiry, "%Y-%m-%d").date()
            except:
                return
        
        if expiry < date.today():
            result.add_error(ExpiredOffer(slot_id, expiry))
    
    def is_restricted_category(self, categoria: str) -> bool:
        """Verifica se categoria é restrita."""
        if not categoria:
            return False
        return categoria.lower() in self.config.restricted_categories
    
    def suggest_legal_text(self, slots: List[Dict]) -> str:
        """
        Gera sugestão de texto legal baseado nos slots.
        
        Returns:
            Texto legal sugerido
        """
        parts = [self.config.default_legal_text]
        
        # Verifica se há produtos +18
        has_restricted = any(
            self.is_restricted_category(s.get("categoria", ""))
            for s in slots
        )
        
        if has_restricted:
            parts.append("Venda proibida para menores de 18 anos.")
        
        # Verifica se há ofertas com prazo
        has_expiry = any(s.get("data_validade") for s in slots)
        if has_expiry:
            expiries = [s.get("data_validade") for s in slots if s.get("data_validade")]
            min_expiry = min(expiries)
            parts.append(f"Ofertas válidas até {min_expiry}.")
        
        return " ".join(parts)


# =============================================================================
# SINGLETON
# =============================================================================

_validator: Optional[ComplianceValidator] = None

def get_compliance_validator() -> ComplianceValidator:
    """Retorna instância singleton do validador."""
    global _validator
    if _validator is None:
        _validator = ComplianceValidator()
    return _validator


# =============================================================================
# HELPERS
# =============================================================================

def validate_de_por(preco_de: float, preco_por: float) -> bool:
    """
    Valida rapidamente se De/Por é válido.
    
    Returns:
        True se válido (De > Por)
    """
    if preco_de is None:
        return True  # Sem preço De é válido
    return preco_de > preco_por


def requires_age_icon(categoria: str, nome: str = "") -> bool:
    """
    Verifica se produto requer ícone +18.
    
    Returns:
        True se requer ícone
    """
    validator = get_compliance_validator()
    
    if validator.is_restricted_category(categoria):
        return True
    
    # Verifica keywords no nome
    nome_lower = nome.lower()
    keywords = ["cerveja", "vinho", "vodka", "whisky", "cigarro", "tabaco"]
    return any(kw in nome_lower for kw in keywords)

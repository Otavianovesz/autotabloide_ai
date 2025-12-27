"""
AutoTabloide AI - DPI Validator
=================================
Validação de DPI para impressão profissional.
PROTOCOLO DE RETIFICAÇÃO: Passo 45 (DPI Check forçar/avisar).

Verifica se imagens têm resolução suficiente para impressão.
"""

import logging
from typing import Optional, Tuple, Dict, List
from dataclasses import dataclass
from pathlib import Path
from enum import Enum

logger = logging.getLogger("DPIValidator")


class DPIStatus(Enum):
    """Status de validação de DPI."""
    OK = "ok"
    WARNING = "warning"
    ERROR = "error"


@dataclass
class DPICheckResult:
    """Resultado de verificação de DPI."""
    status: DPIStatus
    effective_dpi: float
    required_dpi: float
    message: str
    image_width: int = 0
    image_height: int = 0
    slot_width_mm: float = 0
    slot_height_mm: float = 0


class DPIValidator:
    """
    Validador de DPI para impressão.
    
    PASSO 45: Verifica e avisa/força DPI mínimo.
    """
    
    # Limites de DPI
    DPI_PRINT_MINIMUM = 150     # Mínimo aceitável
    DPI_PRINT_RECOMMENDED = 300 # Recomendado
    DPI_PRINT_EXCELLENT = 600   # Excelente/gráfica
    
    # DPI para diferentes usos
    DPI_WEB = 72
    DPI_SCREEN = 96
    DPI_PRINT = 300
    DPI_PROFESSIONAL = 600
    
    def __init__(self, target_dpi: int = 300):
        self.target_dpi = target_dpi
    
    def check_image(
        self,
        image_width_px: int,
        image_height_px: int,
        slot_width_mm: float,
        slot_height_mm: float,
        mode: str = "warn"  # "warn", "force", "block"
    ) -> DPICheckResult:
        """
        Verifica se imagem tem DPI suficiente.
        
        Args:
            image_width_px: Largura da imagem em pixels
            image_height_px: Altura da imagem em pixels
            slot_width_mm: Largura do slot em mm
            slot_height_mm: Altura do slot em mm
            mode: "warn" (avisa), "force" (upscale), "block" (rejeita)
            
        Returns:
            DPICheckResult
        """
        # Converter mm para polegadas
        slot_width_inch = slot_width_mm / 25.4
        slot_height_inch = slot_height_mm / 25.4
        
        # Calcular DPI efetivo (assumindo Aspect Fit)
        dpi_x = image_width_px / slot_width_inch if slot_width_inch > 0 else 0
        dpi_y = image_height_px / slot_height_inch if slot_height_inch > 0 else 0
        
        # Usar o menor (pior caso no Aspect Fit)
        effective_dpi = min(dpi_x, dpi_y) if dpi_x > 0 and dpi_y > 0 else 0
        
        # Determinar status
        if effective_dpi >= self.DPI_PRINT_RECOMMENDED:
            status = DPIStatus.OK
            message = f"DPI excelente ({effective_dpi:.0f} >= {self.DPI_PRINT_RECOMMENDED})"
        elif effective_dpi >= self.DPI_PRINT_MINIMUM:
            status = DPIStatus.WARNING
            message = f"DPI aceitável ({effective_dpi:.0f}) - pode haver perda de qualidade"
        else:
            if mode == "block":
                status = DPIStatus.ERROR
                message = f"DPI insuficiente ({effective_dpi:.0f} < {self.DPI_PRINT_MINIMUM}) - imagem rejeitada"
            else:
                status = DPIStatus.WARNING
                message = f"DPI baixo ({effective_dpi:.0f}) - considere upscale ou imagem maior"
        
        return DPICheckResult(
            status=status,
            effective_dpi=effective_dpi,
            required_dpi=self.target_dpi,
            message=message,
            image_width=image_width_px,
            image_height=image_height_px,
            slot_width_mm=slot_width_mm,
            slot_height_mm=slot_height_mm
        )
    
    def calculate_upscale_factor(
        self,
        current_dpi: float,
        target_dpi: float = None
    ) -> float:
        """
        Calcula fator de upscale necessário.
        
        Args:
            current_dpi: DPI atual
            target_dpi: DPI desejado
            
        Returns:
            Fator de escala (ex: 2.0 = dobrar)
        """
        if target_dpi is None:
            target_dpi = self.target_dpi
        
        if current_dpi <= 0:
            return 1.0
        
        return target_dpi / current_dpi
    
    def should_upscale(self, check_result: DPICheckResult) -> Tuple[bool, float]:
        """
        Decide se deve upscalar e qual fator.
        
        Args:
            check_result: Resultado da verificação
            
        Returns:
            Tuple (deve_upscalar, fator)
        """
        if check_result.effective_dpi >= self.DPI_PRINT_MINIMUM:
            return False, 1.0
        
        factor = self.calculate_upscale_factor(check_result.effective_dpi)
        
        # Limitar upscale (Real-ESRGAN funciona bem até 4x)
        max_factor = 4.0
        factor = min(factor, max_factor)
        
        return True, factor
    
    def validate_batch(
        self,
        images: List[Dict],  # {"width": px, "height": px, "slot_width": mm, "slot_height": mm}
    ) -> Dict[str, any]:
        """
        Valida lote de imagens.
        
        Returns:
            Dict com estatísticas
        """
        results = {
            "total": len(images),
            "ok": 0,
            "warnings": 0,
            "errors": 0,
            "needs_upscale": 0,
            "details": []
        }
        
        for img in images:
            result = self.check_image(
                img["width"],
                img["height"],
                img["slot_width"],
                img["slot_height"]
            )
            
            results["details"].append(result)
            
            if result.status == DPIStatus.OK:
                results["ok"] += 1
            elif result.status == DPIStatus.WARNING:
                results["warnings"] += 1
                if result.effective_dpi < self.DPI_PRINT_MINIMUM:
                    results["needs_upscale"] += 1
            else:
                results["errors"] += 1
        
        return results
    
    def get_size_for_dpi(
        self,
        slot_width_mm: float,
        slot_height_mm: float,
        target_dpi: int = None
    ) -> Tuple[int, int]:
        """
        Calcula tamanho de imagem necessário para atingir DPI.
        
        Args:
            slot_width_mm: Largura do slot
            slot_height_mm: Altura do slot
            target_dpi: DPI desejado
            
        Returns:
            Tuple (largura_px, altura_px)
        """
        if target_dpi is None:
            target_dpi = self.target_dpi
        
        width_inch = slot_width_mm / 25.4
        height_inch = slot_height_mm / 25.4
        
        width_px = int(width_inch * target_dpi)
        height_px = int(height_inch * target_dpi)
        
        return width_px, height_px


# ==============================================================================
# INSTÂNCIA GLOBAL
# ==============================================================================

_validator: Optional[DPIValidator] = None


def get_dpi_validator(target_dpi: int = 300) -> DPIValidator:
    """Retorna instância global do validador."""
    global _validator
    if _validator is None:
        _validator = DPIValidator(target_dpi)
    return _validator


def check_image_dpi(
    width_px: int,
    height_px: int,
    slot_width_mm: float,
    slot_height_mm: float
) -> DPICheckResult:
    """Função de conveniência para verificar DPI."""
    return get_dpi_validator().check_image(
        width_px, height_px, slot_width_mm, slot_height_mm
    )

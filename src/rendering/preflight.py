"""
AutoTabloide AI - Preflight Checker
====================================
PROTOCOLO DE RETIFICAÇÃO NÍVEL 0 - Fase 4 (Passo 165)
Validação prévia antes de exportar PDF.

Verifica:
- Imagens existem e têm DPI mínimo
- Fontes disponíveis
- Slots preenchidos
- Template válido
"""

from __future__ import annotations
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, field
import logging

from PIL import Image

logger = logging.getLogger("Preflight")


# =============================================================================
# PREFLIGHT RESULT
# =============================================================================

@dataclass
class PreflightIssue:
    """Um problema encontrado no preflight."""
    severity: str  # "error", "warning", "info"
    category: str  # "image", "font", "slot", "template"
    message: str
    slot_id: Optional[str] = None
    
    @property
    def icon(self) -> str:
        icons = {
            "error": "❌",
            "warning": "⚠️",
            "info": "ℹ️"
        }
        return icons.get(self.severity, "•")


@dataclass
class PreflightResult:
    """Resultado completo do preflight."""
    passed: bool = True
    issues: List[PreflightIssue] = field(default_factory=list)
    
    @property
    def error_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == "error")
    
    @property
    def warning_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == "warning")
    
    def add_error(self, category: str, message: str, slot_id: str = None):
        self.passed = False
        self.issues.append(PreflightIssue("error", category, message, slot_id))
    
    def add_warning(self, category: str, message: str, slot_id: str = None):
        self.issues.append(PreflightIssue("warning", category, message, slot_id))
    
    def add_info(self, category: str, message: str, slot_id: str = None):
        self.issues.append(PreflightIssue("info", category, message, slot_id))
    
    def get_summary(self) -> str:
        if self.passed:
            if self.warning_count > 0:
                return f"✓ Passou com {self.warning_count} avisos"
            return "✓ Tudo OK para exportar"
        return f"✗ {self.error_count} erros bloqueantes"


# =============================================================================
# PREFLIGHT CHECKER
# =============================================================================

class PreflightChecker:
    """
    Valida projeto antes de exportar PDF.
    
    Checks:
    - Imagens: existem, DPI >= 72, formato suportado
    - Fontes: disponíveis no sistema
    - Slots: pelo menos um preenchido
    - Template: arquivo existe e é válido
    """
    
    MIN_DPI = 72
    RECOMMENDED_DPI = 150
    PRINT_DPI = 300
    
    SUPPORTED_IMAGE_FORMATS = [".jpg", ".jpeg", ".png", ".webp", ".tiff", ".bmp"]
    
    def __init__(self, system_root: str = "AutoTabloide_System_Root"):
        self.system_root = Path(system_root)
        self.vault_path = self.system_root / "assets" / "store"
        self.fonts_path = self.system_root / "assets" / "fonts"
    
    def check(self, scene_data: Dict, template_path: str = None) -> PreflightResult:
        """
        Executa todas as verificações.
        
        Args:
            scene_data: Dados serializados da AtelierScene
            template_path: Caminho do template SVG
            
        Returns:
            PreflightResult com issues encontradas
        """
        result = PreflightResult()
        
        # 1. Verifica template
        if template_path:
            self._check_template(template_path, result)
        
        # 2. Verifica slots
        slots = scene_data.get("slots", [])
        self._check_slots(slots, result)
        
        # 3. Verifica imagens
        self._check_images(slots, result)
        
        # 4. Verifica fontes
        self._check_fonts(result)
        
        return result
    
    def _check_template(self, path: str, result: PreflightResult):
        """Verifica template SVG."""
        template = Path(path)
        
        if not template.exists():
            result.add_error("template", f"Template não encontrado: {template.name}")
            return
        
        if template.suffix.lower() != ".svg":
            result.add_warning("template", f"Template não é SVG: {template.suffix}")
        
        # Verifica tamanho mínimo
        if template.stat().st_size < 100:
            result.add_error("template", "Template parece vazio ou corrompido")
        
        result.add_info("template", f"Template OK: {template.name}")
    
    def _check_slots(self, slots: List[Dict], result: PreflightResult):
        """Verifica slots e produtos."""
        if not slots:
            result.add_error("slot", "Nenhum slot definido no projeto")
            return
        
        filled = 0
        empty = 0
        
        for slot in slots:
            product = slot.get("product_data")
            slot_id = slot.get("element_id", "?")
            
            if product:
                filled += 1
                
                # Verifica dados obrigatórios
                if not product.get("nome_sanitizado"):
                    result.add_warning("slot", "Produto sem nome", slot_id)
                
                price = product.get("preco_venda_atual", 0)
                if price <= 0:
                    result.add_warning("slot", "Preço zerado ou inválido", slot_id)
                elif price > 10000:
                    result.add_warning("slot", f"Preço muito alto: R$ {price:.2f}", slot_id)
            else:
                empty += 1
        
        if filled == 0:
            result.add_error("slot", "Nenhum slot preenchido - nada para exportar")
        else:
            result.add_info("slot", f"{filled} slots preenchidos, {empty} vazios")
    
    def _check_images(self, slots: List[Dict], result: PreflightResult):
        """Verifica imagens dos produtos."""
        for slot in slots:
            product = slot.get("product_data")
            if not product:
                continue
            
            slot_id = slot.get("element_id", "?")
            img_hash = product.get("img_hash_ref")
            
            if not img_hash:
                result.add_warning("image", "Produto sem imagem", slot_id)
                continue
            
            # Procura imagem no vault
            img_path = self._find_image(img_hash)
            
            if not img_path:
                result.add_warning("image", f"Imagem não encontrada: {img_hash[:8]}...", slot_id)
                continue
            
            # Verifica DPI
            try:
                with Image.open(img_path) as img:
                    width, height = img.size
                    
                    # Calcula DPI estimado (assumindo impressão ~5cm)
                    estimated_dpi = width / 2  # 2 polegadas = ~5cm
                    
                    if estimated_dpi < self.MIN_DPI:
                        result.add_error(
                            "image", 
                            f"Resolução muito baixa: {width}x{height}px", 
                            slot_id
                        )
                    elif estimated_dpi < self.RECOMMENDED_DPI:
                        result.add_warning(
                            "image",
                            f"Resolução baixa: {width}x{height}px (recomendado: {self.RECOMMENDED_DPI*2}px)",
                            slot_id
                        )
            except Exception as e:
                result.add_warning("image", f"Erro ao verificar imagem: {e}", slot_id)
    
    def _find_image(self, img_hash: str) -> Optional[Path]:
        """Localiza imagem no vault."""
        for ext in self.SUPPORTED_IMAGE_FORMATS:
            path = self.vault_path / f"{img_hash}{ext}"
            if path.exists():
                return path
        
        # Tenta subpastas
        for subdir in self.vault_path.iterdir():
            if subdir.is_dir():
                for ext in self.SUPPORTED_IMAGE_FORMATS:
                    path = subdir / f"{img_hash}{ext}"
                    if path.exists():
                        return path
        
        return None
    
    def _check_fonts(self, result: PreflightResult):
        """Verifica fontes necessárias."""
        required_fonts = [
            "Roboto-Regular.ttf",
            "Roboto-Bold.ttf",
        ]
        
        missing = []
        for font in required_fonts:
            font_path = self.fonts_path / font
            if not font_path.exists():
                missing.append(font)
        
        if missing:
            result.add_warning("font", f"Fontes não encontradas: {', '.join(missing)}")
        else:
            result.add_info("font", "Todas as fontes disponíveis")
    
    def check_quick(self, slots: List[Dict]) -> Tuple[bool, str]:
        """
        Verificação rápida para UI.
        
        Returns:
            Tuple (can_export, message)
        """
        filled = sum(1 for s in slots if s.get("product_data"))
        
        if filled == 0:
            return False, "Nenhum slot preenchido"
        
        return True, f"{filled} produtos prontos para exportar"


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def preflight_check(scene_data: Dict, template_path: str = None) -> PreflightResult:
    """Executa preflight check."""
    checker = PreflightChecker()
    return checker.check(scene_data, template_path)


def can_export(slots: List[Dict]) -> Tuple[bool, str]:
    """Verificação rápida se pode exportar."""
    checker = PreflightChecker()
    return checker.check_quick(slots)

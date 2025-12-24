"""
AutoTabloide AI - Settings View
================================
Menu de Configurações conforme Vol. VI, Cap. 1.0.1.
Persiste configurações em /config/settings.json.
"""

import flet as ft
import json
import os
from pathlib import Path
from typing import Dict, Any, Optional

# Design System
from src.ui.design_system import ColorScheme, Typography, Spacing, Animations

# Cores usando Design System
COLORS = {
    "success": ColorScheme.SUCCESS,
    "warning": ColorScheme.WARNING,
    "error": ColorScheme.ERROR,
    "info": ColorScheme.ACCENT_PRIMARY,
    "neutral": ColorScheme.TEXT_MUTED,
    "surface": ColorScheme.BG_SECONDARY,
    "surface_elevated": ColorScheme.BG_ELEVATED,
}

# Caminho padrão para configurações
DEFAULT_CONFIG_PATH = Path(__file__).parent.parent.parent.parent / \
    "AutoTabloide_System_Root" / "config" / "settings.json"


# Configurações padrão
DEFAULT_SETTINGS = {
    "general": {
        "system_root": str(Path(__file__).parent.parent.parent.parent / "AutoTabloide_System_Root"),
        "language": "pt-BR",
        "theme": "dark"
    },
    "typography": {
        "text_case": "title",  # title, upper, lower
        "unit_case": "lower",  # lower, upper (ml vs ML)
        "hyphenation": True
    },
    "legal": {
        "age_restricted_categories": [
            "Bebida Alcoólica",
            "Bebidas Alcoólicas",
            "Cerveja",
            "Vinho",
            "Destilados",
            "Cigarro",
            "Tabaco"
        ],
        "show_18_icon": True,
        "legal_text_default": "Beba com moderação."
    },
    "ai": {
        "quantization": "4bit",  # 4bit, 8bit
        "fuzzy_threshold": 85,
        "max_tokens": 256,
        "temperature": 0.0,
        "use_rag": True
    },
    "export": {
        "default_dpi": 300,
        "default_color_mode": "auto",  # auto, rgb, cmyk
        "icc_profile": "CoatedFOGRA39.icc",
        "add_crop_marks": True,
        "bleed_mm": 3
    },
    "paths": {
        "svg_source": "library/svg_source",
        "thumbnails": "library/thumbnails",
        "vault": "assets/store",
        "staging": "staging",
        "snapshots": "snapshots"
    }
}


def load_settings(config_path: Path = None) -> Dict[str, Any]:
    """Carrega configurações do arquivo JSON."""
    path = config_path or DEFAULT_CONFIG_PATH
    
    if path.exists():
        try:
            with open(path, 'r', encoding='utf-8') as f:
                loaded = json.load(f)
                # Merge com defaults (para novas chaves)
                return _deep_merge(DEFAULT_SETTINGS.copy(), loaded)
        except (json.JSONDecodeError, IOError) as e:
            print(f"[Settings] Erro ao carregar: {e}")
    
    return DEFAULT_SETTINGS.copy()


def save_settings(settings: Dict[str, Any], config_path: Path = None) -> bool:
    """Salva configurações no arquivo JSON."""
    path = config_path or DEFAULT_CONFIG_PATH
    
    try:
        # Garante que o diretório existe
        path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(settings, f, indent=2, ensure_ascii=False)
        return True
    except IOError as e:
        print(f"[Settings] Erro ao salvar: {e}")
        return False


def _deep_merge(base: Dict, override: Dict) -> Dict:
    """Merge profundo de dicionários."""
    result = base.copy()
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def get_setting(path: str, default: Any = None) -> Any:
    """
    Obtém uma configuração específica via caminho dot-notation.
    Exemplo: get_setting("ai.quantization") -> "4bit"
    """
    settings = load_settings()
    keys = path.split(".")
    value = settings
    
    for key in keys:
        if isinstance(value, dict) and key in value:
            value = value[key]
        else:
            return default
    
    return value


def set_setting(path: str, value: Any) -> bool:
    """
    Define uma configuração específica via caminho dot-notation.
    Exemplo: set_setting("ai.quantization", "8bit")
    """
    settings = load_settings()
    keys = path.split(".")
    
    # Navega até o penúltimo nível
    target = settings
    for key in keys[:-1]:
        if key not in target:
            target[key] = {}
        target = target[key]
    
    # Define o valor
    target[keys[-1]] = value
    
    return save_settings(settings)


class SettingsView(ft.UserControl):
    """
    Tela de Configurações do Sistema.
    Permite ajuste de parâmetros locais.
    """
    
    def __init__(self, page: ft.Page):
        super().__init__()
        self.page = page
        self.settings = load_settings()
        self._dirty = False
    
    def _build_section_header(self, title: str, icon: str) -> ft.Container:
        """Constrói cabeçalho de seção."""
        return ft.Container(
            content=ft.Row([
                ft.Icon(icon, color=COLORS["info"]),
                ft.Text(title, size=18, weight=ft.FontWeight.BOLD)
            ]),
            padding=ft.padding.only(top=20, bottom=10)
        )
    
    def _build_setting_row(
        self,
        label: str,
        description: str,
        control: ft.Control
    ) -> ft.Container:
        """Constrói linha de configuração."""
        return ft.Container(
            content=ft.Row([
                ft.Column([
                    ft.Text(label, size=14, weight=ft.FontWeight.W_500),
                    ft.Text(description, size=12, color=ft.colors.GREY_400)
                ], expand=True, spacing=2),
                control
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            padding=15,
            bgcolor=COLORS["surface"],
            border_radius=8,
            margin=ft.margin.only(bottom=8)
        )
    
    def _on_change(self, path: str, value: Any):
        """Callback genérico para mudança de configuração."""
        keys = path.split(".")
        target = self.settings
        for key in keys[:-1]:
            target = target[key]
        target[keys[-1]] = value
        self._dirty = True
    
    def _save_settings(self, e):
        """Salva todas as configurações."""
        if save_settings(self.settings):
            self.page.snack_bar = ft.SnackBar(
                ft.Text("Configuracoes salvas com sucesso!"),
                bgcolor=COLORS["success"]
            )
        else:
            self.page.snack_bar = ft.SnackBar(
                ft.Text("Erro ao salvar configuracoes"),
                bgcolor=COLORS["error"]
            )
        self.page.snack_bar.open = True
        self._dirty = False
        self.page.update()
    
    def _reset_to_defaults(self, e):
        """Restaura configurações padrão."""
        def confirm_reset(e):
            self.settings = DEFAULT_SETTINGS.copy()
            save_settings(self.settings)
            dialog.open = False
            self.page.update()
            # Rebuild
            self.update()
        
        dialog = ft.AlertDialog(
            title=ft.Text("Restaurar Padroes"),
            content=ft.Text("Isso ira resetar todas as configuracoes para os valores padrao. Continuar?"),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda e: setattr(dialog, 'open', False) or self.page.update()),
                ft.ElevatedButton("Restaurar", on_click=confirm_reset, bgcolor=COLORS["warning"])
            ]
        )
        self.page.dialog = dialog
        dialog.open = True
        self.page.update()
    
    def build(self):
        # ===== SEÇÃO: TIPOGRAFIA =====
        typography_section = ft.Column([
            self._build_section_header("Tipografia", ft.icons.TEXT_FIELDS),
            
            self._build_setting_row(
                "Case do Texto",
                "Como o texto dos produtos sera formatado",
                ft.Dropdown(
                    value=self.settings["typography"]["text_case"],
                    options=[
                        ft.dropdown.Option("title", "Title Case (Padrao)"),
                        ft.dropdown.Option("upper", "MAIUSCULAS"),
                        ft.dropdown.Option("lower", "minusculas"),
                    ],
                    width=200,
                    on_change=lambda e: self._on_change("typography.text_case", e.control.value)
                )
            ),
            
            self._build_setting_row(
                "Case das Unidades",
                "Formatacao de unidades de medida (ml, kg)",
                ft.Dropdown(
                    value=self.settings["typography"]["unit_case"],
                    options=[
                        ft.dropdown.Option("lower", "minusculas (ml, kg)"),
                        ft.dropdown.Option("upper", "MAIUSCULAS (ML, KG)"),
                    ],
                    width=200,
                    on_change=lambda e: self._on_change("typography.unit_case", e.control.value)
                )
            ),
            
            self._build_setting_row(
                "Hifenizacao",
                "Quebrar palavras longas com hifen",
                ft.Switch(
                    value=self.settings["typography"]["hyphenation"],
                    on_change=lambda e: self._on_change("typography.hyphenation", e.control.value)
                )
            ),
        ])
        
        # ===== SEÇÃO: RESTRIÇÕES LEGAIS =====
        categories_text = "\n".join(self.settings["legal"]["age_restricted_categories"])
        
        legal_section = ft.Column([
            self._build_section_header("Restricoes Legais (+18)", ft.icons.VERIFIED_USER),
            
            self._build_setting_row(
                "Exibir Icone +18",
                "Injetar automaticamente icone de restricao de idade",
                ft.Switch(
                    value=self.settings["legal"]["show_18_icon"],
                    on_change=lambda e: self._on_change("legal.show_18_icon", e.control.value)
                )
            ),
            
            ft.Container(
                content=ft.Column([
                    ft.Text("Categorias Restritas", size=14, weight=ft.FontWeight.W_500),
                    ft.Text("Uma categoria por linha", size=12, color=ft.colors.GREY_400),
                    ft.TextField(
                        value=categories_text,
                        multiline=True,
                        min_lines=4,
                        max_lines=8,
                        on_change=lambda e: self._on_change(
                            "legal.age_restricted_categories",
                            [c.strip() for c in e.control.value.split("\n") if c.strip()]
                        )
                    )
                ]),
                padding=15,
                bgcolor=COLORS["surface"],
                border_radius=8,
                margin=ft.margin.only(bottom=8)
            ),
        ])
        
        # ===== SEÇÃO: INTELIGÊNCIA ARTIFICIAL =====
        ai_section = ft.Column([
            self._build_section_header("Inteligencia Artificial", ft.icons.PSYCHOLOGY),
            
            self._build_setting_row(
                "Quantizacao do Modelo",
                "Qualidade vs Performance (requer reinicio)",
                ft.Dropdown(
                    value=self.settings["ai"]["quantization"],
                    options=[
                        ft.dropdown.Option("4bit", "4-bit (Mais Rapido)"),
                        ft.dropdown.Option("8bit", "8-bit (Mais Preciso)"),
                    ],
                    width=200,
                    on_change=lambda e: self._on_change("ai.quantization", e.control.value)
                )
            ),
            
            self._build_setting_row(
                "Limiar Fuzzy Matching",
                "Similaridade minima para correlacao automatica (%)",
                ft.Slider(
                    value=self.settings["ai"]["fuzzy_threshold"],
                    min=50,
                    max=100,
                    divisions=10,
                    label="{value}%",
                    on_change=lambda e: self._on_change("ai.fuzzy_threshold", int(e.control.value))
                )
            ),
            
            self._build_setting_row(
                "Usar RAG (Memoria)",
                "Aprender com correcoes humanas",
                ft.Switch(
                    value=self.settings["ai"]["use_rag"],
                    on_change=lambda e: self._on_change("ai.use_rag", e.control.value)
                )
            ),
        ])
        
        # ===== SEÇÃO: EXPORTAÇÃO =====
        export_section = ft.Column([
            self._build_section_header("Exportacao", ft.icons.PRINT),
            
            self._build_setting_row(
                "DPI Padrao",
                "Resolucao de saida para impressao",
                ft.Dropdown(
                    value=str(self.settings["export"]["default_dpi"]),
                    options=[
                        ft.dropdown.Option("150", "150 DPI (Web/Preview)"),
                        ft.dropdown.Option("300", "300 DPI (Impressao)"),
                        ft.dropdown.Option("600", "600 DPI (Alta Qualidade)"),
                    ],
                    width=200,
                    on_change=lambda e: self._on_change("export.default_dpi", int(e.control.value))
                )
            ),
            
            self._build_setting_row(
                "Modo de Cor",
                "Espaco de cor padrao para exportacao",
                ft.Dropdown(
                    value=self.settings["export"]["default_color_mode"],
                    options=[
                        ft.dropdown.Option("auto", "Automatico (Recomendado)"),
                        ft.dropdown.Option("rgb", "Forcar RGB"),
                        ft.dropdown.Option("cmyk", "Forcar CMYK"),
                    ],
                    width=200,
                    on_change=lambda e: self._on_change("export.default_color_mode", e.control.value)
                )
            ),
            
            self._build_setting_row(
                "Marcas de Corte",
                "Adicionar crop marks na exportacao",
                ft.Switch(
                    value=self.settings["export"]["add_crop_marks"],
                    on_change=lambda e: self._on_change("export.add_crop_marks", e.control.value)
                )
            ),
            
            self._build_setting_row(
                "Sangria (Bleed)",
                "Margem de sangria em milimetros",
                ft.Dropdown(
                    value=str(self.settings["export"]["bleed_mm"]),
                    options=[
                        ft.dropdown.Option("0", "0 mm (Sem sangria)"),
                        ft.dropdown.Option("3", "3 mm (Padrao)"),
                        ft.dropdown.Option("5", "5 mm"),
                    ],
                    width=200,
                    on_change=lambda e: self._on_change("export.bleed_mm", int(e.control.value))
                )
            ),
        ])
        
        # ===== BARRA DE AÇÕES =====
        action_bar = ft.Container(
            content=ft.Row([
                ft.ElevatedButton(
                    "Restaurar Padroes",
                    icon=ft.icons.RESTORE,
                    on_click=self._reset_to_defaults
                ),
                ft.Container(expand=True),
                ft.ElevatedButton(
                    "Salvar Configuracoes",
                    icon=ft.icons.SAVE,
                    style=ft.ButtonStyle(
                        bgcolor=COLORS["info"],
                        color=ft.colors.WHITE
                    ),
                    on_click=self._save_settings
                )
            ]),
            padding=ft.padding.symmetric(vertical=20)
        )
        
        # ===== LAYOUT PRINCIPAL =====
        return ft.Container(
            content=ft.Column([
                ft.Text("Configuracoes", size=28, weight=ft.FontWeight.BOLD),
                ft.Text("Ajuste os parametros do sistema", size=14, color=ft.colors.GREY_400),
                ft.Divider(height=20, color=ft.colors.GREY_800),
                
                ft.Column([
                    typography_section,
                    legal_section,
                    ai_section,
                    export_section,
                    action_bar
                ], scroll=ft.ScrollMode.AUTO, expand=True)
            ], expand=True),
            padding=30,
            expand=True
        )

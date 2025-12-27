"""
AutoTabloide AI - Rendering Safety Module
===========================================
Robustez industrial para motor de renderização.
PROTOCOLO DE RETIFICAÇÃO: Passos 31-50 (Motor Vetorial e Renderização).

Este módulo contém:
- Passo 32: CairoSVG unsafe=True verificação
- Passo 35: Overprint real no Ghostscript
- Passo 36: Verificação de perfil ICC
- Passo 38: Preto Puro K=100 (não Rich Black)
- Passo 39: Z-Index corrigido (preço sempre acima)
- Passo 40: Remoção de tags vazias
- Passo 44: Sangria configurável
- Passo 47: Suporte a emojis (filtro/substituição)
- Passo 49: Ghostscript zombie cleanup
- Passo 50: Fallback de fontes
"""

import os
import re
import sys
import signal
import logging
import subprocess
from pathlib import Path
from typing import Optional, List, Dict, Tuple
from lxml import etree

logger = logging.getLogger("RenderingSafety")


# ==============================================================================
# PASSO 32: CAIROSVG UNSAFE MODE
# ==============================================================================

class CairoSVGConfig:
    """
    Configurações para CairoSVG garantindo carregamento de imagens locais.
    
    PROBLEMA: CairoSVG por padrão não carrega imagens com href local.
    
    SOLUÇÃO: Sempre usar unsafe=True para permitir file:// URIs.
    """
    
    # Configuração padrão segura para produção
    DEFAULT_RENDER_OPTIONS = {
        "unsafe": True,  # CRÍTICO: Permite carregar imagens locais
        "dpi": 300,
        "parent_width": None,
        "parent_height": None,
    }
    
    @classmethod
    def get_render_kwargs(cls, dpi: int = 300) -> dict:
        """
        Retorna kwargs para renderização CairoSVG.
        
        Args:
            dpi: Resolução de saída
            
        Returns:
            Dict de argumentos para cairosvg.svg2png/svg2pdf
        """
        return {
            **cls.DEFAULT_RENDER_OPTIONS,
            "dpi": dpi,
        }


# ==============================================================================
# PASSO 35: OVERPRINT PARA GHOSTSCRIPT
# ==============================================================================

class OverprintManager:
    """
    Gerencia overprint para impressão profissional.
    
    Overprint é essencial para texto preto sobre cores - evita "halo branco".
    """
    
    GS_OVERPRINT_ARGS = [
        "-dOverprint=/enable",
        "-dColorConversionStrategy=/CMYK",
        "-dDeviceGrayToK=true",  # Cinza vira K puro
    ]
    
    @classmethod
    def get_gs_args_for_print(cls) -> List[str]:
        """Retorna argumentos GS para impressão com overprint."""
        return cls.GS_OVERPRINT_ARGS.copy()
    
    @classmethod
    def add_overprint_to_svg(cls, svg_root: etree.Element) -> int:
        """
        Adiciona atributos de overprint a elementos pretos no SVG.
        
        Args:
            svg_root: Elemento raiz do SVG
            
        Returns:
            Número de elementos modificados
        """
        modified = 0
        nsmap = {'svg': 'http://www.w3.org/2000/svg'}
        
        # Encontrar todos os elementos com fill ou stroke preto
        for elem in svg_root.iter():
            fill = elem.get('fill', '')
            stroke = elem.get('stroke', '')
            
            # Detectar variantes de preto
            is_black_fill = cls._is_black_color(fill)
            is_black_stroke = cls._is_black_color(stroke)
            
            if is_black_fill or is_black_stroke:
                # Adicionar estilo de overprint
                current_style = elem.get('style', '')
                overprint_style = 'overprint-fill:true;overprint-stroke:true;'
                
                if overprint_style not in current_style:
                    elem.set('style', current_style + overprint_style)
                    modified += 1
        
        return modified
    
    @classmethod
    def _is_black_color(cls, color: str) -> bool:
        """Verifica se cor é preta ou quase preta."""
        if not color:
            return False
        
        color = color.lower().strip()
        
        # Nomes diretos
        if color in ['black', '#000', '#000000', 'rgb(0,0,0)', 'rgb(0, 0, 0)']:
            return True
        
        # Hex próximo de preto
        if color.startswith('#'):
            try:
                hex_color = color[1:]
                if len(hex_color) == 3:
                    hex_color = ''.join(c*2 for c in hex_color)
                
                r = int(hex_color[0:2], 16)
                g = int(hex_color[2:4], 16)
                b = int(hex_color[4:6], 16)
                
                # Considerar preto se RGB < 30
                return r < 30 and g < 30 and b < 30
            except ValueError:
                return False
        
        return False


# ==============================================================================
# PASSO 36: VERIFICAÇÃO DE PERFIL ICC
# ==============================================================================

class ICCProfileChecker:
    """
    Verifica disponibilidade de perfis ICC para conversão CMYK.
    
    CRÍTICO: Sem perfil ICC, cores podem ficar erradas na impressão.
    """
    
    REQUIRED_PROFILES = [
        "CoatedFOGRA39.icc",  # CMYK padrão gráfico
        "sRGB.icc",           # RGB entrada
    ]
    
    FOGRA39_ALTERNATIVES = [
        "ISOcoated_v2_eci.icc",
        "ISOcoated_v2_300_eci.icc",
        "USWebCoatedSWOP.icc",
    ]
    
    @classmethod
    def check_profiles(cls, profiles_dir: Path) -> Dict[str, Optional[Path]]:
        """
        Verifica quais perfis ICC estão disponíveis.
        
        Returns:
            Dict mapeando nome do perfil para caminho (ou None se ausente)
        """
        results = {}
        
        for profile_name in cls.REQUIRED_PROFILES:
            profile_path = profiles_dir / profile_name
            
            if profile_path.exists():
                results[profile_name] = profile_path
            else:
                # Tentar alternativas para FOGRA39
                if "FOGRA" in profile_name:
                    for alt in cls.FOGRA39_ALTERNATIVES:
                        alt_path = profiles_dir / alt
                        if alt_path.exists():
                            results[profile_name] = alt_path
                            logger.info(f"Usando {alt} como alternativa a {profile_name}")
                            break
                    else:
                        results[profile_name] = None
                else:
                    results[profile_name] = None
        
        return results
    
    @classmethod
    def has_required_profiles(cls, profiles_dir: Path) -> Tuple[bool, List[str]]:
        """
        Verifica se todos os perfis necessários existem.
        
        Returns:
            Tuple (todos_presentes, lista_faltantes)
        """
        profiles = cls.check_profiles(profiles_dir)
        missing = [name for name, path in profiles.items() if path is None]
        
        return len(missing) == 0, missing


# ==============================================================================
# PASSO 38: PRETO PURO K=100
# ==============================================================================

class TrueBlackConverter:
    """
    Garante que preto seja K=100 e não Rich Black (C+M+Y+K).
    
    PROBLEMA: Converter RGB(0,0,0) para CMYK gera Rich Black (ex: 75,68,67,90),
    causando problemas de registro em text preto.
    
    SOLUÇÃO: Detectar preto e forçar K=100 sem CMY.
    """
    
    GS_TRUE_BLACK_ARGS = [
        "-dBlackText=true",            # Texto preto = K100
        "-dBlackOverprint=true",       # Overprint automático para preto
        "-dDeviceGrayToK=true",        # Cinza converte para K
        "-sColorConversionStrategyForImages=/LeaveColorUnchanged",
    ]
    
    # Regex para detectar cores pretas em SVG
    BLACK_COLOR_REGEX = re.compile(
        r'(fill|stroke)\s*[:=]\s*["\']?(#000000?|black|rgb\(0,\s*0,\s*0\))["\']?',
        re.IGNORECASE
    )
    
    @classmethod
    def get_gs_args(cls) -> List[str]:
        """Retorna argumentos GS para preto verdadeiro."""
        return cls.GS_TRUE_BLACK_ARGS.copy()
    
    @classmethod
    def count_black_elements(cls, svg_content: str) -> int:
        """
        Conta elementos com cores pretas no SVG.
        
        Args:
            svg_content: Conteúdo SVG como string
            
        Returns:
            Número de elementos pretos
        """
        return len(cls.BLACK_COLOR_REGEX.findall(svg_content))


# ==============================================================================
# PASSO 39: Z-INDEX CORRIGIDO
# ==============================================================================

class ZIndexCorrector:
    """
    Garante ordem correta de camadas no SVG.
    
    REGRA: Preço sempre acima da imagem. Texto sempre visível.
    """
    
    # Ordem de prioridade (maior = mais à frente)
    LAYER_PRIORITY = {
        "background": 0,
        "image": 10,
        "preco_de": 90,
        "preco_por": 100,
        "nome": 80,
        "marca": 70,
        "detalhe": 60,
        "icon": 95,  # +18 sempre visível
    }
    
    @classmethod
    def get_node_priority(cls, node_id: str) -> int:
        """
        Retorna prioridade de um nó baseado em seu ID.
        
        Args:
            node_id: ID do elemento SVG
            
        Returns:
            Prioridade numérica
        """
        node_id_lower = node_id.lower()
        
        for key, priority in cls.LAYER_PRIORITY.items():
            if key in node_id_lower:
                return priority
        
        return 50  # Prioridade padrão
    
    @classmethod
    def reorder_elements(cls, svg_root: etree.Element) -> int:
        """
        Reordena elementos do SVG por prioridade.
        Elementos com maior prioridade ficam por último (acima).
        
        Args:
            svg_root: Raiz do SVG
            
        Returns:
            Número de elementos reordenados
        """
        reordered = 0
        
        # Encontrar grupos principais
        for group in svg_root.iter('{http://www.w3.org/2000/svg}g'):
            children = list(group)
            
            if len(children) < 2:
                continue
            
            # Ordenar por prioridade
            def get_priority(elem):
                elem_id = elem.get('id', '')
                return cls.get_node_priority(elem_id)
            
            sorted_children = sorted(children, key=get_priority)
            
            # Verificar se precisa reordenar
            if sorted_children != children:
                for child in children:
                    group.remove(child)
                
                for child in sorted_children:
                    group.append(child)
                
                reordered += 1
        
        return reordered


# ==============================================================================
# PASSO 40: REMOÇÃO DE TAGS VAZIAS
# ==============================================================================

class EmptyTagCleaner:
    """
    Remove tags de texto vazias que podem causar artefatos.
    
    PROBLEMA: Tags como <text></text> podem renderizar como caixa vazia.
    """
    
    REMOVABLE_TAGS = [
        '{http://www.w3.org/2000/svg}text',
        '{http://www.w3.org/2000/svg}tspan',
    ]
    
    @classmethod
    def clean_empty_tags(cls, svg_root: etree.Element) -> int:
        """
        Remove tags de texto vazias.
        
        Args:
            svg_root: Raiz do SVG
            
        Returns:
            Número de tags removidas
        """
        removed = 0
        
        # Iterar em ordem reversa para remoção segura
        for tag_name in cls.REMOVABLE_TAGS:
            for elem in list(svg_root.iter(tag_name)):
                # Verificar se está vazio
                text = (elem.text or '').strip()
                
                # Verificar filhos
                has_children = len(elem) > 0
                
                if not text and not has_children:
                    parent = elem.getparent()
                    if parent is not None:
                        parent.remove(elem)
                        removed += 1
        
        return removed


# ==============================================================================
# PASSO 47: SUPORTE A EMOJIS
# ==============================================================================

class EmojiHandler:
    """
    Trata emojis em nomes de produtos para evitar crashes.
    
    PROBLEMA: Fontes tradicionais não suportam emojis e podem falhar.
    
    SOLUÇÃO: Remover ou substituir emojis por texto equivalente.
    """
    
    # Mapeamento de emojis comuns para texto
    EMOJI_MAP = {
        '🍺': '[CERVEJA]',
        '🍻': '[CERVEJA]',
        '🍷': '[VINHO]',
        '🥂': '[CHAMPAGNE]',
        '🍫': '[CHOCOLATE]',
        '🍬': '[DOCE]',
        '🍕': '[PIZZA]',
        '🍔': '[HAMBURGUER]',
        '🥩': '[CARNE]',
        '🧀': '[QUEIJO]',
        '🥛': '[LEITE]',
        '☕': '[CAFE]',
        '🍞': '[PAO]',
        '🎉': '',  # Decorativo, remover
        '✨': '',
        '🔥': '[PROMO]',
        '💥': '[OFERTA]',
        '⭐': '[DESTAQUE]',
    }
    
    # Regex para detectar emojis (ranges Unicode)
    EMOJI_REGEX = re.compile(
        "["
        "\U0001F600-\U0001F64F"  # Emoticons
        "\U0001F300-\U0001F5FF"  # Símbolos & Pictogramas
        "\U0001F680-\U0001F6FF"  # Transporte & Mapas
        "\U0001F700-\U0001F77F"  # Alchemical
        "\U0001F780-\U0001F7FF"  # Geometric Shapes Extended
        "\U0001F800-\U0001F8FF"  # Supplemental Arrows-C
        "\U0001F900-\U0001F9FF"  # Supplemental Symbols
        "\U0001FA00-\U0001FA6F"  # Chess
        "\U0001FA70-\U0001FAFF"  # Symbols and Pictographs Extended-A
        "\U00002702-\U000027B0"  # Dingbats
        "\U000024C2-\U0001F251"  # Enclosed Characters
        "]+",
        flags=re.UNICODE
    )
    
    @classmethod
    def contains_emoji(cls, text: str) -> bool:
        """Verifica se texto contém emojis."""
        return bool(cls.EMOJI_REGEX.search(text))
    
    @classmethod
    def remove_emojis(cls, text: str) -> str:
        """Remove todos os emojis do texto."""
        return cls.EMOJI_REGEX.sub('', text).strip()
    
    @classmethod
    def replace_emojis(cls, text: str) -> str:
        """Substitui emojis por texto equivalente quando possível."""
        result = text
        
        for emoji, replacement in cls.EMOJI_MAP.items():
            result = result.replace(emoji, replacement)
        
        # Remover emojis restantes não mapeados
        result = cls.EMOJI_REGEX.sub('', result)
        
        return ' '.join(result.split())  # Normalizar espaços


# ==============================================================================
# PASSO 49: GHOSTSCRIPT ZOMBIE CLEANUP
# ==============================================================================

class GhostscriptProcessManager:
    """
    Gerencia processos Ghostscript para evitar zombies.
    
    PROBLEMA: Se renderização travar, processos gswin64c.exe ficam órfãos.
    """
    
    GS_PROCESS_NAMES = ['gswin64c.exe', 'gswin32c.exe', 'gs']
    
    @classmethod
    def kill_orphan_processes(cls) -> int:
        """
        Mata processos Ghostscript órfãos.
        
        Returns:
            Número de processos mortos
        """
        killed = 0
        
        if sys.platform != 'win32':
            return killed
        
        try:
            # Usar taskkill no Windows
            for proc_name in cls.GS_PROCESS_NAMES:
                result = subprocess.run(
                    ['taskkill', '/F', '/IM', proc_name],
                    capture_output=True,
                    timeout=5
                )
                if result.returncode == 0:
                    killed += 1
                    logger.info(f"Processo {proc_name} encerrado")
                    
        except Exception as e:
            logger.debug(f"Nenhum processo GS órfão encontrado: {e}")
        
        return killed
    
    @classmethod
    def run_with_timeout(
        cls,
        cmd: List[str],
        timeout_seconds: int = 120
    ) -> Tuple[bool, str, str]:
        """
        Executa Ghostscript com timeout forçado.
        
        Args:
            cmd: Comando completo
            timeout_seconds: Timeout máximo
            
        Returns:
            Tuple (sucesso, stdout, stderr)
        """
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                timeout=timeout_seconds,
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
            )
            
            return (
                result.returncode == 0,
                result.stdout.decode('utf-8', errors='ignore'),
                result.stderr.decode('utf-8', errors='ignore')
            )
            
        except subprocess.TimeoutExpired:
            logger.error(f"Ghostscript timeout ({timeout_seconds}s)")
            cls.kill_orphan_processes()
            return False, "", f"Timeout após {timeout_seconds}s"
            
        except Exception as e:
            return False, "", str(e)


# ==============================================================================
# PASSO 50: FALLBACK DE FONTES
# ==============================================================================

class FontFallbackManager:
    """
    Gerencia substituição de fontes quando a requerida não está disponível.
    """
    
    # Pilha de fallback por tipo de fonte
    FONT_FALLBACKS = {
        'serif': ['Times New Roman', 'Georgia', 'DejaVu Serif', 'Liberation Serif'],
        'sans-serif': ['Arial', 'Helvetica', 'DejaVu Sans', 'Liberation Sans', 'Roboto'],
        'monospace': ['Courier New', 'Consolas', 'DejaVu Sans Mono', 'Liberation Mono'],
        'display': ['Impact', 'Arial Black', 'Bebas Neue', 'Oswald'],
    }
    
    # Mapeamento de fontes específicas
    SPECIFIC_FALLBACKS = {
        'helvetica': ['Arial', 'Liberation Sans', 'DejaVu Sans'],
        'helvetica neue': ['Arial', 'Helvetica', 'Liberation Sans'],
        'futura': ['Century Gothic', 'Avant Garde', 'Poppins'],
        'bebas': ['Bebas Neue', 'Impact', 'Arial Black'],
    }
    
    @classmethod
    def get_fallback(cls, font_name: str, available_fonts: List[str]) -> Optional[str]:
        """
        Retorna fonte de fallback disponível.
        
        Args:
            font_name: Nome da fonte desejada
            available_fonts: Lista de fontes disponíveis no sistema
            
        Returns:
            Nome da fonte de fallback ou None
        """
        font_lower = font_name.lower()
        available_lower = {f.lower(): f for f in available_fonts}
        
        # Verificar se a própria fonte está disponível
        if font_lower in available_lower:
            return available_lower[font_lower]
        
        # Verificar fallbacks específicos
        if font_lower in cls.SPECIFIC_FALLBACKS:
            for fallback in cls.SPECIFIC_FALLBACKS[font_lower]:
                if fallback.lower() in available_lower:
                    logger.info(f"Usando {fallback} como fallback para {font_name}")
                    return available_lower[fallback.lower()]
        
        # Tentar categorias genéricas
        for category, fallbacks in cls.FONT_FALLBACKS.items():
            for fallback in fallbacks:
                if fallback.lower() in available_lower:
                    return available_lower[fallback.lower()]
        
        # Último recurso: Arial
        if 'arial' in available_lower:
            return available_lower['arial']
        
        return None


# ==============================================================================
# FUNÇÃO DE INICIALIZAÇÃO
# ==============================================================================

def initialize_rendering_safety(system_root: Path) -> dict:
    """
    Inicializa proteções de renderização.
    
    Args:
        system_root: Diretório raiz do sistema
        
    Returns:
        Dict com status
    """
    results = {}
    
    # Verificar perfis ICC
    profiles_dir = system_root / "assets" / "profiles"
    profiles_ok, missing = ICCProfileChecker.has_required_profiles(profiles_dir)
    results["icc_profiles"] = {
        "ok": profiles_ok,
        "missing": missing
    }
    
    if not profiles_ok:
        logger.warning(f"Perfis ICC faltantes: {missing}")
    
    # Limpar processos GS órfãos
    killed = GhostscriptProcessManager.kill_orphan_processes()
    results["gs_cleanup"] = killed
    
    logger.info("Rendering safety inicializado")
    return results

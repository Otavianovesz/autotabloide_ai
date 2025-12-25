"""
AutoTabloide AI - Motor de Vetorização de Alta Fidelidade
==========================================================
Manipulação de SVG via DOM (lxml) conforme Vol. II.
Responsável por injeção de dados em templates sem quebrar estrutura.
"""

import os
import re
import math
import hashlib
import logging
from typing import Dict, Optional, Tuple, List, Union
from pathlib import Path
from lxml import etree
from PIL import ImageFont, Image

logger = logging.getLogger("VectorEngine")

# Tentativa de importar fonttools para kerning (#26)
try:
    from fontTools.ttLib import TTFont
    HAS_FONTTOOLS = True
except ImportError:
    HAS_FONTTOOLS = False

# Tentativa de importar Pyphen para hifenização (#27)
try:
    import pyphen
    HAS_PYPHEN = True
except ImportError:
    HAS_PYPHEN = False

# Namespaces SVG comuns
NAMESPACES = {
    'svg': 'http://www.w3.org/2000/svg',
    'inkscape': 'http://www.inkscape.org/namespaces/inkscape',
    'sodipodi': 'http://sodipodi.sourceforge.net/DTD/sodipodi-0.dtd',
    'xlink': 'http://www.w3.org/1999/xlink'
}

# Importa mixin de paginação
from src.rendering.page_pagination import PagePaginationMixin
# Importa mixin de melhorias (bleed, crop marks, EAN validation)
from src.rendering.vector_improvements import VectorImprovementsMixin, LRUFontCache


class VectorEngine(PagePaginationMixin, VectorImprovementsMixin):
    """
    Motor de Manipulação Vetorial de Alta Fidelidade.
    Interpreta SVG como árvore DOM XML e injeta dados com precisão.
    
    Conforme Vol. II: 
    - Aspect Fit para imagens (nunca distorce)
    - Busca binária para ajuste de fonte
    - Quebra de linha automática com hifenização
    - Suporte a tags de preço De/Por
    - Passo 31-34: Suporte a paginação via #PAGE_xx
    - Passo 35-40: Bleed, crop marks, EAN validation via VectorImprovementsMixin
    """
    
    # Caminho padrão para fontes (pode ser sobrescrito)
    DEFAULT_FONTS_PATH = Path(__file__).parent.parent.parent / "AutoTabloide_System_Root" / "assets" / "fonts"
    
    def __init__(self, strict_fonts: bool = True):
        """
        Args:
            strict_fonts: Se True, falha sem fallback quando fonte não existe.
                         Conforme Vol. II, Cap. 3.3 - Não há fallback para fonte padrão.
        """
        self.tree: Optional[etree._ElementTree] = None
        self.root: Optional[etree._Element] = None
        self.slots: Dict[str, etree._Element] = {}
        self.strict_fonts = strict_fonts
        
        # Cache de fontes (LRU seria ainda melhor)
        self._font_cache: Dict[Tuple[str, int], ImageFont.FreeTypeFont] = {}
        
        # Hifenizador PT-BR
        self._hyphenator = pyphen.Pyphen(lang='pt_BR') if HAS_PYPHEN else None

    # ==========================================================================
    # CARREGAMENTO E INDEXAÇÃO
    # ==========================================================================

    def load_template(self, template_path: str):
        """
        Carrega e higieniza template SVG.
        Remove metadados proprietários (Inkscape/Illustrator) que poluem o XML.
        
        SEGURANÇA (#103 Industrial Robustness):
        - Parser configurado com XXE Shielding
        - resolve_entities=False previne XML External Entity attacks
        - no_network=True bloqueia acesso a recursos externos
        """
        parser = self._create_secure_parser()
        self.tree = etree.parse(template_path, parser)
        self.root = self.tree.getroot()
        
        self._purge_namespaces()
        self._index_slots()
    
    def _create_secure_parser(self) -> etree.XMLParser:
        """
        Cria parser XML seguro contra XXE Injection (#103).
        
        PROTEÇÕES:
        - resolve_entities=False: Não resolve entidades externas
        - no_network=True: Bloqueia requisições de rede
        - load_dtd=False: Não carrega DTD externos
        - dtd_validation=False: Desabilita validação DTD
        
        Um SVG malicioso poderia tentar:
        <!DOCTYPE svg [<!ENTITY xxe SYSTEM "file:///etc/passwd">]>
        Este parser rejeita tais tentativas silenciosamente.
        """
        return etree.XMLParser(
            remove_blank_text=True,
            resolve_entities=False,  # CRÍTICO: Previne XXE
            no_network=True,         # CRÍTICO: Sem acesso à rede
            load_dtd=False,          # Não carrega DTD externos
            dtd_validation=False,    # Sem validação DTD
            recover=True             # Tenta recuperar de erros menores
        )
    
    def load_from_string(self, svg_content: Union[str, bytes]):
        """
        Carrega SVG a partir de string/bytes.
        
        SEGURANÇA (#103 Industrial Robustness):
        Usa o mesmo parser seguro contra XXE.
        """
        if isinstance(svg_content, str):
            svg_content = svg_content.encode('utf-8')
        
        parser = self._create_secure_parser()
        self.root = etree.fromstring(svg_content, parser)
        self.tree = etree.ElementTree(self.root)
        
        self._purge_namespaces()
        self._index_slots()

    def _purge_namespaces(self):
        """Remove atributos proprietários que não afetam renderização."""
        for elem in self.root.iter():
            for key in list(elem.attrib.keys()):
                if any(ns in key for ns in ['inkscape', 'sodipodi', 'adobe', 'pgf']):
                    del elem.attrib[key]

    def _index_slots(self):
        """
        Cria índice O(1) para acesso rápido a elementos por ID.
        Mapeia todos os elementos com IDs relevantes (SLOT_, TXT_, ALVO_, etc).
        """
        self.slots = {}
        for elem in self.root.xpath('//*[@id]'):
            id_val = elem.get('id')
            # Indexa padrões conhecidos + qualquer ID para flexibilidade
            self.slots[id_val] = elem

    def get_viewbox(self) -> Tuple[float, float, float, float]:
        """Retorna dimensões do ViewBox (min-x, min-y, width, height)."""
        viewbox = self.root.get('viewBox', '0 0 1000 1000')
        parts = [float(x) for x in viewbox.split()]
        return tuple(parts[:4]) if len(parts) >= 4 else (0, 0, 1000, 1000)

    # ==========================================================================
    # MEDIÇÃO DE TEXTO
    # ==========================================================================

    def _load_font(self, font_path: str, size: int) -> ImageFont.FreeTypeFont:
        """
        Carrega fonte com cache. Falha ruidosamente se não existir.
        Conforme Vol. II, Cap. 3.3 - Sem fallback para fonte padrão.
        """
        import logging
        logger = logging.getLogger("VectorEngine")
        
        cache_key = (font_path, size)
        
        if cache_key in self._font_cache:
            return self._font_cache[cache_key]
        
        # Resolve caminho
        resolved_path = font_path
        if not os.path.isabs(font_path):
            resolved_path = str(self.DEFAULT_FONTS_PATH / font_path)
        
        if not os.path.exists(resolved_path):
            if self.strict_fonts:
                raise FileNotFoundError(
                    f"ERRO CRÍTICO: Fonte não encontrada: '{resolved_path}'. "
                    "O sistema requer fontes explícitas para fidelidade visual. "
                    "Coloque a fonte em 'assets/fonts/' ou desative strict_fonts."
                )
            else:
                # ⚠️ AVISO: Fallback para fonte do sistema (qualidade degradada)
                logger.warning(
                    f"[FONT FALLBACK] Fonte '{font_path}' não encontrada. "
                    "Usando fallback do sistema. Qualidade visual pode ser afetada."
                )
                # Tenta várias fontes de fallback em ordem de preferência
                fallback_fonts = [
                    "DejaVuSans.ttf",      # Linux/comum
                    "arial.ttf",            # Windows
                    "Arial.ttf",            # Case sensitivity
                    "LiberationSans-Regular.ttf",  # Linux alternativo
                ]
                for fallback in fallback_fonts:
                    try:
                        font = ImageFont.truetype(fallback, size)
                        self._font_cache[cache_key] = font
                        return font
                    except IOError:
                        continue
                
                # Último recurso: fonte default do PIL
                logger.error(f"[FONT FALLBACK] Nenhuma fonte de fallback encontrada!")
                return ImageFont.load_default()
        
        try:
            font = ImageFont.truetype(resolved_path, size)
            self._font_cache[cache_key] = font
            return font
        except IOError as e:
            raise FileNotFoundError(
                f"ERRO CRÍTICO: Falha ao carregar fonte '{resolved_path}': {e}"
            ) from e

    def _measure_text_width(self, text: str, font_path: str, size: int) -> float:
        """Mede largura exata do texto usando PIL."""
        font = self._load_font(font_path, size)
        
        if hasattr(font, 'getlength'):
            return font.getlength(text)
        else:
            bbox = font.getbbox(text)
            return bbox[2] - bbox[0] if bbox else 0

    def _get_text_height(self, font_path: str, size: int) -> float:
        """Retorna altura da linha para a fonte."""
        font = self._load_font(font_path, size)
        if hasattr(font, 'getbbox'):
            bbox = font.getbbox("Ágjpy")  # Caracteres com ascendentes e descendentes
            return bbox[3] - bbox[1] if bbox else size * 1.2
        return size * 1.2

    # ==========================================================================
    # ALGORITMO DE QUEBRA DE LINHA (Vol. II, Cap. 3.4)
    # ==========================================================================

    def _hyphenate_word(self, word: str) -> List[str]:
        """Retorna possíveis pontos de hifenização de uma palavra."""
        if not self._hyphenator or len(word) < 5:
            return [word]
        
        pairs = self._hyphenator.inserted(word)
        return pairs.split('-') if pairs else [word]

    def _wrap_text(
        self, 
        text: str, 
        font_path: str, 
        font_size: int, 
        max_width: float,
        allow_hyphenation: bool = True
    ) -> List[str]:
        """
        Quebra texto em múltiplas linhas respeitando largura máxima.
        Implementa lógica de hifenização opcional para PT-BR.
        """
        words = text.split()
        lines = []
        current_line = ""
        
        for word in words:
            test_line = f"{current_line} {word}".strip()
            test_width = self._measure_text_width(test_line, font_path, font_size)
            
            if test_width <= max_width:
                current_line = test_line
            else:
                # Palavra não cabe - tenta hifenização
                if allow_hyphenation and self._hyphenator:
                    # Tenta quebrar a palavra
                    syllables = self._hyphenate_word(word)
                    
                    if len(syllables) > 1:
                        # Tenta encaixar sílabas uma a uma
                        word_part = ""
                        remaining_syllables = []
                        
                        for i, syllable in enumerate(syllables):
                            test_part = f"{current_line} {word_part}{syllable}-".strip()
                            
                            if self._measure_text_width(test_part, font_path, font_size) <= max_width:
                                word_part += syllable
                            else:
                                remaining_syllables = syllables[i:]
                                break
                        
                        if word_part and remaining_syllables:
                            current_line = f"{current_line} {word_part}-".strip()
                            lines.append(current_line)
                            current_line = "".join(remaining_syllables)
                            continue
                
                # Se não conseguiu hifenizar, quebra normal
                if current_line:
                    lines.append(current_line)
                current_line = word
        
        if current_line:
            lines.append(current_line)
        
        return lines

    # ==========================================================================
    # AJUSTE DINÂMICO DE FONTE (Vol. II, Cap. 3.2)
    # ==========================================================================

    def fit_text(
        self, 
        node_id: str, 
        text: str, 
        max_width_px: float,
        font_path: str = "Roboto-Regular.ttf",
        allow_shrink: bool = True,
        min_size_ratio: float = 0.6
    ) -> bool:
        """
        Algoritmo de Busca Binária para Ajuste de Texto.
        
        REGRA DE OURO (Vol. II, Cap. 3.4):
        - JAMAIS aumenta fonte além do tamanho original do template
        - Prioriza quebra de linha antes de reduzir fonte
        - Limite mínimo de 60% do tamanho original
        
        FAIL-FAST (#104 Industrial Robustness):
        - Se a fonte calculada for menor que MIN_FONT_SIZE_PT (6pt),
          lança TextOverflowError em vez de gerar texto ilegível.
        
        Args:
            node_id: ID do elemento de texto no SVG
            text: Texto a ser inserido
            max_width_px: Largura máxima permitida
            font_path: Caminho da fonte (relativo a assets/fonts)
            allow_shrink: Permite redução de fonte se necessário
            min_size_ratio: Proporção mínima do tamanho original (default 60%)
            
        Raises:
            TextOverflowError: Se texto requer fonte < 6pt (ilegível)
        """
        # CONSTANTE CRÍTICA (#104): Fonte mínima legível para impressão
        MIN_FONT_SIZE_PT = 6.0
        
        node = self.slots.get(node_id)
        if node is None:
            return False

        # Extrai tamanho original do template (MÁXIMO permitido)
        current_style = node.get('style', '')
        match = re.search(r'font-size:\s*([\d.]+)', current_style)
        original_size = float(match.group(1)) if match else 24.0
        
        # Calcula mínimo respeitando tanto o ratio quanto o limite absoluto
        ratio_min = int(original_size * min_size_ratio)
        absolute_min = int(MIN_FONT_SIZE_PT)
        min_size = max(ratio_min, absolute_min)  # Nunca menor que 6pt
        
        # Define texto
        node.text = text
        
        if max_width_px <= 0:
            return True
        
        # Verifica se cabe com tamanho original
        current_width = self._measure_text_width(text, font_path, int(original_size))
        
        if current_width <= max_width_px:
            # Já cabe! Mantém tamanho original (Regra de Ouro)
            return True
        
        # Não cabe - precisa ajustar
        if not allow_shrink:
            # Trunca com reticências se não pode reduzir
            truncated = text
            while self._measure_text_width(truncated + "...", font_path, int(original_size)) > max_width_px:
                truncated = truncated[:-1]
                if len(truncated) < 3:
                    break
            node.text = truncated + "..."
            return True
        
        # Busca binária para encontrar tamanho ótimo
        low, high = min_size, int(original_size)
        best_size = min_size
        
        while low <= high:
            mid = (low + high) // 2
            width = self._measure_text_width(text, font_path, mid)
            
            if width <= max_width_px:
                best_size = mid
                low = mid + 1
            else:
                high = mid - 1
        
        # FAIL-FAST CHECK (#104)
        # Verifica se mesmo no tamanho mínimo o texto cabe
        final_width = self._measure_text_width(text, font_path, best_size)
        if final_width > max_width_px and best_size <= MIN_FONT_SIZE_PT:
            # Texto IMPOSSÍVEL de caber - lançar exceção
            from src.core.exceptions import TextOverflowError
            raise TextOverflowError(
                slot_id=node_id,
                text=text,
                min_font_attempted=best_size,
                required_width=final_width,
                available_width=max_width_px
            )
        
        # Aplica novo tamanho
        self._update_style(node, 'font-size', f'{best_size}px')
        return True

    def fit_text_multiline(
        self,
        node_id: str,
        text: str,
        max_width: float,
        max_height: float,
        font_path: str = "Roboto-Regular.ttf",
        line_height_ratio: float = 1.2
    ) -> bool:
        """
        Ajuste de texto com quebra de linha automática.
        Conforme Vol. II, Cap. 3.4 - Prioriza quebra antes de redução.
        """
        node = self.slots.get(node_id)
        if node is None:
            return False
        
        # Extrai tamanho original
        current_style = node.get('style', '')
        match = re.search(r'font-size:\s*([\d.]+)', current_style)
        original_size = int(float(match.group(1)) if match else 24)
        min_size = int(original_size * 0.6)
        
        current_size = original_size
        
        # Loop de ajuste: primeiro tenta quebrar, depois reduz se necessário
        while current_size >= min_size:
            lines = self._wrap_text(text, font_path, current_size, max_width)
            line_height = current_size * line_height_ratio
            total_height = len(lines) * line_height
            
            if total_height <= max_height:
                # Cabe! Aplica as linhas
                self._apply_multiline(node, lines, current_size, line_height)
                return True
            
            # Não cabe - reduz fonte
            current_size -= 1
        
        # Último recurso: trunca
        lines = self._wrap_text(text, font_path, min_size, max_width)
        max_lines = int(max_height / (min_size * line_height_ratio))
        if len(lines) > max_lines:
            lines = lines[:max_lines]
            lines[-1] = lines[-1].rstrip() + "..."
        
        self._apply_multiline(node, lines, min_size, min_size * line_height_ratio)
        return True

    def _apply_multiline(
        self, 
        node: etree._Element, 
        lines: List[str], 
        font_size: int,
        line_height: float
    ):
        """Aplica múltiplas linhas a um elemento tspan ou text."""
        self._update_style(node, 'font-size', f'{font_size}px')
        
        # Remove tspans existentes
        for child in list(node):
            if child.tag.endswith('tspan'):
                node.remove(child)
        
        node.text = None
        
        # Obtém posição X do nó
        x = node.get('x', '0')
        base_y = float(node.get('y', '0'))
        
        # Cria tspan para cada linha
        for i, line in enumerate(lines):
            tspan = etree.SubElement(node, '{http://www.w3.org/2000/svg}tspan')
            tspan.text = line
            tspan.set('x', x)
            tspan.set('dy', f'{line_height if i > 0 else 0}')

    # ==========================================================================
    # LÓGICA DE PREÇOS (Vol. II, Cap. 4)
    # ==========================================================================

    def _format_currency(self, value: Optional[float]) -> str:
        """Formatação BRL determinística (evita locale do SO)."""
        if value is None:
            return ""
        return f"{value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

    def _split_price(self, price_str: str) -> Tuple[str, str]:
        """Separa parte inteira e centavos."""
        parts = price_str.split(',')
        if len(parts) == 2:
            return parts[0], ',' + parts[1]
        return price_str, ''

    def handle_price_logic(
        self, 
        slot_suffix: str,
        preco_atual: float, 
        preco_ref: Optional[float] = None,
        font_path: str = "Roboto-Bold.ttf",
        strict_validation: bool = True
    ):
        """
        Lógica de Negócio para Precificação Visual (De/Por).
        Suporta múltiplos formatos de tag conforme Vol. II, Cap. 4.4.
        
        VALIDAÇÃO ANTI-FRAUDE (#34/#97 Industrial Robustness):
        - Se preco_ref fornecido, DEVE ser maior que preco_atual
        - Caso contrário, lança PriceValidationError
        - Isso previne ofertas enganosas e passivo legal
        
        Tags suportadas:
        - TXT_PRECO_POR_{slot}: Preço atual formatado
        - TXT_PRECO_INT_{slot}: Parte inteira
        - TXT_PRECO_DEC_{slot}: Centavos
        - TXT_PRECO_DE_{slot}: Preço de referência (oculto se não houver)
        - TXT_PRECO_COMPLETO_{slot}: Preço completo em string única
        
        Args:
            slot_suffix: Sufixo do slot (ex: "01")
            preco_atual: Preço de venda atual
            preco_ref: Preço de referência ("De") - opcional
            font_path: Caminho da fonte
            strict_validation: Se True, lança exceção em preços inválidos
            
        Raises:
            PriceValidationError: Se preco_ref <= preco_atual (oferta inválida)
        """
        # VALIDAÇÃO ANTI-FRAUDE (#34/#97)
        if strict_validation and preco_ref is not None:
            if preco_ref <= preco_atual:
                from src.core.exceptions import PriceValidationError
                raise PriceValidationError(
                    message=(
                        f"Oferta inválida: Preço 'De' (R$ {preco_ref:.2f}) deve ser "
                        f"maior que preço 'Por' (R$ {preco_atual:.2f}). "
                        "Isso pode configurar propaganda enganosa."
                    ),
                    price_value={"de": preco_ref, "por": preco_atual}
                )
        
        suf = f"_{slot_suffix}" if slot_suffix else ""
        
        # Formatação
        str_atual = self._format_currency(preco_atual)
        str_ref = self._format_currency(preco_ref) if preco_ref else ""
        int_part, dec_part = self._split_price(str_atual)
        
        # 1. Preço POR / Atual
        self._safe_set_text(f"TXT_PRECO_POR{suf}", str_atual)
        self._safe_set_text(f"TXT_PRECO_BIG{suf}", int_part)
        
        # 2. Separação Inteiro/Centavos
        self._safe_set_text(f"TXT_PRECO_INT{suf}", int_part)
        self._safe_set_text(f"TXT_PRECO_DEC{suf}", dec_part)
        self._safe_set_text(f"TXT_PRECO_CENTS{suf}", dec_part)
        
        # 3. Preço Completo (alternativa)
        self._safe_set_text(f"TXT_PRECO_COMPLETO{suf}", f"R$ {str_atual}")
        self._safe_set_text(f"TXT_PRECO_COM{suf}", f"R$ {str_atual}")
        
        # 4. Preço DE (Condicional)
        de_id = f"TXT_PRECO_DE{suf}"
        node_de = self.slots.get(de_id)
        
        if node_de is not None:
            if preco_ref and preco_ref > preco_atual:
                # Tem desconto: Mostra e preenche
                self._update_style(node_de, 'display', 'inline')
                self._update_style(node_de, 'visibility', 'visible')
                node_de.text = f"De R$ {str_ref}"
            else:
                # Sem desconto: Oculta
                self._update_style(node_de, 'display', 'none')
                self._update_style(node_de, 'visibility', 'hidden')

    def _safe_set_text(self, node_id: str, text: str):
        """Define texto de um nó se existir."""
        node = self.slots.get(node_id)
        if node is not None:
            node.text = text

    # ==========================================================================
    # LÓGICA DE SLOTS INTELIGENTES (Vol. I, Cap. 5)
    # ==========================================================================

    def handle_smart_slot(
        self, 
        slot_id: str, 
        product_data: dict,
        font_path: str = "Roboto-Regular.ttf"
    ):
        """
        Orquestra renderização inteligente do slot.
        
        product_data: {
            'nome_sanitizado': str,
            'detalhe_peso': str,
            'categoria': str,  # Para lógica +18
            'images': [path, ...],
            'preco_venda_atual': float,
            'preco_referencia': float
        }
        """
        # Extrai sufixo do slot (ex: SLOT_01 -> 01)
        suffix = slot_id.replace('SLOT_', '')
        
        # 1. Nome do Produto
        nome = product_data.get('nome_sanitizado', '')
        peso = product_data.get('detalhe_peso', '')
        
        # Verifica se existe campo separado para unidade
        unit_id = f"TXT_UNIDADE_{suffix}"
        has_unit = unit_id in self.slots
        
        if not has_unit and peso:
            # Concatena peso ao nome se não há campo separado
            nome = f"{nome} {peso}"
        elif has_unit and peso:
            self._safe_set_text(unit_id, peso)
        
        # Aplica nome
        nome_id = f"TXT_NOME_PRODUTO_{suffix}"
        if nome_id not in self.slots:
            nome_id = "TXT_NOME_PRODUTO"  # Fallback global
        
        if nome_id in self.slots:
            self.fit_text(nome_id, nome, max_width_px=200, font_path=font_path)
        
        # 2. Preços
        preco_atual = product_data.get('preco_venda_atual')
        preco_ref = product_data.get('preco_referencia')
        
        if preco_atual:
            self.handle_price_logic(suffix, preco_atual, preco_ref)
        
        # 3. Imagens
        images = product_data.get('images', [])
        if images:
            self._handle_slot_images(suffix, images)
        
        # 4. Ícone +18 (Vol. I, Cap. 5.3)
        categoria = product_data.get('categoria', '')
        if self._is_restricted_category(categoria):
            self._inject_age_restriction_icon(slot_id)

    def _is_restricted_category(self, categoria: str) -> bool:
        """
        Verifica se categoria requer ícone +18.
        Passo 7 do Checklist v2 - Usa SettingsService para lista configurável.
        """
        if not categoria:
            return False
        
        try:
            from src.core.settings_service import get_settings
            settings = get_settings()
            return settings.is_restricted(categoria)
        except Exception:
            # Fallback se SettingsService não disponível
            restricted = [
                "bebida alcoólica", "alcoolica", "alcoólico",
                "cigarro", "tabaco", "tabacaria",
                "cerveja", "vinho", "vodka", "whisky", "cachaça"
            ]
            return categoria.lower() in restricted

    def _inject_age_restriction_icon(self, slot_id: str):
        """
        Injeta ícone de +18 no slot.
        Conforme Vol. I, Cap. 5.3 - Z-Index alto para ficar sobre outros elementos.
        """
        slot_node = self.slots.get(slot_id)
        if slot_node is None:
            return
        
        # Obtém posição do slot
        x = float(slot_node.get('x', '0'))
        y = float(slot_node.get('y', '0'))
        
        # Cria grupo para o ícone (será adicionado por último = Z-Index alto)
        icon_group = etree.SubElement(slot_node, '{http://www.w3.org/2000/svg}g')
        icon_group.set('id', f'ICON_18_{slot_id}')
        
        # Círculo vermelho
        circle = etree.SubElement(icon_group, '{http://www.w3.org/2000/svg}circle')
        circle.set('cx', str(x + 15))
        circle.set('cy', str(y + 15))
        circle.set('r', '12')
        circle.set('fill', '#FF3B30')
        
        # Texto +18
        text = etree.SubElement(icon_group, '{http://www.w3.org/2000/svg}text')
        text.set('x', str(x + 15))
        text.set('y', str(y + 19))
        text.set('text-anchor', 'middle')
        text.set('fill', 'white')
        text.set('style', 'font-size:10px;font-weight:bold;font-family:sans-serif')
        text.text = '+18'

    def _handle_slot_images(self, slot_suffix: str, images: List[str]):
        """Processa imagens do slot (única ou múltiplas)."""
        target_id = f"ALVO_IMAGEM_{slot_suffix}"
        if target_id not in self.slots:
            target_id = "ALVO_IMAGEM"  # Fallback
        
        if target_id not in self.slots:
            return
        
        target = self.slots[target_id]
        w = float(target.get('width', '100'))
        h = float(target.get('height', '100'))
        
        if len(images) == 1:
            self.place_image(target_id, images[0], w, h)
        else:
            self._apply_recursive_grid(target_id, images)

    # ==========================================================================
    # POSICIONAMENTO DE IMAGENS (Vol. II, Cap. 1.2)
    # ==========================================================================

    def place_image(
        self, 
        target_id: str, 
        img_path: str, 
        slot_w: float, 
        slot_h: float
    ) -> bool:
        """
        Posiciona imagem com Aspect Fit (nunca distorce).
        Calcula matriz de transformação afim para centralização.
        """
        node = self.slots.get(target_id)
        if node is None:
            return False

        # Link da imagem
        node.set('{http://www.w3.org/1999/xlink}href', img_path)
        node.set('href', img_path)  # SVG 2.0 compatibility
        
        # Dimensões da imagem real
        try:
            with Image.open(img_path) as img:
                w_img, h_img = img.size
        except Exception:
            w_img, h_img = 500, 500  # Fallback
        
        # Cálculo Aspect Fit (Vol. II, Cap. 1.2)
        scale = min(slot_w / w_img, slot_h / h_img)
        
        # Centralização
        tx = (slot_w - w_img * scale) / 2
        ty = (slot_h - h_img * scale) / 2
        
        # Matriz de transformação
        matrix_str = f"matrix({scale:.4f},0,0,{scale:.4f},{tx:.2f},{ty:.2f})"
        node.set('transform', matrix_str)
        
        # Reset x/y/width/height
        node.set('x', '0')
        node.set('y', '0')
        node.set('width', str(w_img))
        node.set('height', str(h_img))
        
        return True

    def _apply_recursive_grid(self, target_id: str, images: List[str]):
        """
        Divide área do alvo para múltiplas imagens (grid).
        Conforme Vol. I, Cap. 5.1 - Suporte a kits e múltiplos sabores.
        """
        target = self.slots.get(target_id)
        if target is None:
            return
        
        x = float(target.get('x', '0'))
        y = float(target.get('y', '0'))
        w = float(target.get('width', '100'))
        h = float(target.get('height', '100'))
        parent = target.getparent()
        
        # Remove target original
        parent.remove(target)
        if target_id in self.slots:
            del self.slots[target_id]
        
        # Calcula grid layout
        count = len(images)
        cols = math.ceil(math.sqrt(count))
        rows = math.ceil(count / cols)
        
        sub_w = w / cols
        sub_h = h / rows
        
        for i, img_path in enumerate(images):
            row = i // cols
            col = i % cols
            
            new_id = f"{target_id}_{i}"
            new_img = etree.Element("{http://www.w3.org/2000/svg}image")
            new_img.set('id', new_id)
            
            new_x = x + (col * sub_w)
            new_y = y + (row * sub_h)
            new_img.set('x', str(new_x))
            new_img.set('y', str(new_y))
            new_img.set('width', str(sub_w))
            new_img.set('height', str(sub_h))
            
            parent.append(new_img)
            self.slots[new_id] = new_img
            
            self.place_image(new_id, img_path, sub_w, sub_h)

    def create_clipping_path(
        self,
        clip_id: str,
        target_element_id: str,
        shape: str = "rect"
    ) -> None:
        """
        INDUSTRIAL ROBUSTNESS #38: Cria clipping path dinâmico para elemento.
        
        Usado para:
        - Imagens que precisam respeitar bordas arredondadas
        - Slots com formato irregular (círculo, polígono)
        - Prevenir overflow de conteúdo em slots
        
        Args:
            clip_id: ID único para o clipPath
            target_element_id: ID do elemento a receber o clip
            shape: "rect", "circle", "ellipse" ou caminho SVG
        """
        target = self.slots.get(target_element_id)
        if target is None:
            return
        
        x = float(target.get('x', '0'))
        y = float(target.get('y', '0'))
        w = float(target.get('width', '100'))
        h = float(target.get('height', '100'))
        
        ns = '{http://www.w3.org/2000/svg}'
        
        # Cria ou encontra defs
        defs = self.root.find(f'{ns}defs')
        if defs is None:
            defs = etree.SubElement(self.root, f'{ns}defs')
            self.root.insert(0, defs)  # defs deve ser primeiro
        
        # Cria clipPath
        clip_path = etree.SubElement(defs, f'{ns}clipPath')
        clip_path.set('id', clip_id)
        
        # Cria forma do clip
        if shape == "circle":
            cx = x + w / 2
            cy = y + h / 2
            r = min(w, h) / 2
            clip_shape = etree.SubElement(clip_path, f'{ns}circle')
            clip_shape.set('cx', str(cx))
            clip_shape.set('cy', str(cy))
            clip_shape.set('r', str(r))
        elif shape == "ellipse":
            cx = x + w / 2
            cy = y + h / 2
            clip_shape = etree.SubElement(clip_path, f'{ns}ellipse')
            clip_shape.set('cx', str(cx))
            clip_shape.set('cy', str(cy))
            clip_shape.set('rx', str(w / 2))
            clip_shape.set('ry', str(h / 2))
        else:  # rect ou fallback
            clip_shape = etree.SubElement(clip_path, f'{ns}rect')
            clip_shape.set('x', str(x))
            clip_shape.set('y', str(y))
            clip_shape.set('width', str(w))
            clip_shape.set('height', str(h))
            # Border radius se disponível
            rx = target.get('rx', '0')
            ry = target.get('ry', rx)
            clip_shape.set('rx', rx)
            clip_shape.set('ry', ry)
        
        # Aplica clip ao elemento
        target.set('clip-path', f'url(#{clip_id})')
        
        logger.debug(f"Clipping path '{clip_id}' criado para '{target_element_id}'")

    # ==========================================================================
    # TEXTOS LEGAIS (Vol. I, Cap. 5.3)
    # ==========================================================================

    def inject_legal_text(self, text: str, global_slot: bool = True):
        """
        Injeta texto legal no layout.
        
        Args:
            text: Texto legal (validade, disclaimers, etc)
            global_slot: Se True, usa TXT_LEGAL_GLOBAL; senão TXT_LEGAL
        """
        slot_id = "TXT_LEGAL_GLOBAL" if global_slot else "TXT_LEGAL"
        self._safe_set_text(slot_id, text)

    # ==========================================================================
    # UTILITÁRIOS
    # ==========================================================================

    def _update_style(self, node: etree._Element, property_name: str, value: str):
        """Atualiza propriedade CSS inline preservando outras."""
        style = node.get('style', '')
        
        if property_name in style:
            style = re.sub(f'{property_name}:[^;]+', f'{property_name}:{value}', style)
        else:
            if style and not style.endswith(';'):
                style += ';'
            style += f'{property_name}:{value}'
        
        node.set('style', style.strip(';'))

    def to_string(self) -> bytes:
        """Exporta SVG manipulado como bytes."""
        return etree.tostring(self.tree, pretty_print=True, encoding='utf-8')

    def save(self, output_path: str):
        """Salva SVG manipulado em arquivo."""
        self.tree.write(output_path, pretty_print=True, encoding='utf-8')

    def calculate_hash(self) -> str:
        """
        Calcula hash SHA-256 do SVG atual (para verificação de integridade).
        INDUSTRIAL ROBUSTNESS #107: Usa SHA-256 por segurança.
        """
        content = self.to_string()
        return hashlib.sha256(content).hexdigest()

    def render_frame(self, slot_data: dict) -> bytes:
        """
        Renderiza um frame completo com os dados fornecidos.
        Usado pela Factory para geração batch.
        
        Args:
            slot_data: Dict mapeando slot_id -> dados do produto
            
        Returns:
            SVG renderizado como bytes
        """
        # Faz deep copy da árvore para não poluir o template
        import copy
        original_tree = self.tree
        original_slots = self.slots
        
        self.tree = copy.deepcopy(original_tree)
        self.root = self.tree.getroot()
        self._index_slots()
        
        try:
            for slot_id, data in slot_data.items():
                if not data:
                    continue
                    
                # Extrai sufixo do slot
                suffix = slot_id.replace('SLOT_', '')
                
                # Nome do produto
                nome = data.get('TXT_NOME_PRODUTO', '')
                nome_id = f"TXT_NOME_PRODUTO_{suffix}"
                if nome_id in self.slots:
                    self._safe_set_text(nome_id, nome)
                elif "TXT_NOME_PRODUTO" in self.slots:
                    self._safe_set_text("TXT_NOME_PRODUTO", nome)
                
                # Unidade/Peso
                unidade = data.get('TXT_UNIDADE', '')
                unit_id = f"TXT_UNIDADE_{suffix}"
                if unit_id in self.slots:
                    self._safe_set_text(unit_id, unidade)
                elif "TXT_UNIDADE" in self.slots:
                    self._safe_set_text("TXT_UNIDADE", unidade)
                
                # Preço De (riscado)
                preco_de = data.get('TXT_PRECO_DE')
                if preco_de:
                    de_id = f"TXT_PRECO_DE_{suffix}"
                    if de_id in self.slots:
                        self._safe_set_text(de_id, preco_de)
                    elif "TXT_PRECO_DE" in self.slots:
                        self._safe_set_text("TXT_PRECO_DE", preco_de)
                
                # Preço Inteiro
                preco_int = data.get('TXT_PRECO_INT', '')
                int_id = f"TXT_PRECO_INT_{suffix}"
                if int_id in self.slots:
                    self._safe_set_text(int_id, preco_int)
                elif "TXT_PRECO_INT" in self.slots:
                    self._safe_set_text("TXT_PRECO_INT", preco_int)
                
                # Preço Decimal
                preco_dec = data.get('TXT_PRECO_DEC', '')
                dec_id = f"TXT_PRECO_DEC_{suffix}"
                if dec_id in self.slots:
                    self._safe_set_text(dec_id, preco_dec)
                elif "TXT_PRECO_DEC" in self.slots:
                    self._safe_set_text("TXT_PRECO_DEC", preco_dec)
                
                # Imagem
                img_hash = data.get('ALVO_IMAGEM')
                if img_hash:
                    alvo_id = f"ALVO_IMAGEM_{suffix}"
                    if alvo_id not in self.slots:
                        alvo_id = "ALVO_IMAGEM"
                    if alvo_id in self.slots:
                        # Placeholder para injeção de imagem
                        pass
            
            result = self.to_string()
            
        finally:
            # Restaura estado original
            self.tree = original_tree
            self.root = original_tree.getroot()
            self.slots = original_slots
        
        return result


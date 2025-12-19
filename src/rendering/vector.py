import math
import re
from typing import Dict, Optional, Tuple, List, Union
from lxml import etree
from PIL import ImageFont, Image  # Mandatório para medição precisa offline e leitura de imagem

# Namespaces que poluem o SVG gerado pelo Inkscape/Illustrator
NAMESPACES = {
    'svg': 'http://www.w3.org/2000/svg',
    'inkscape': 'http://www.inkscape.org/namespaces/inkscape',
    'sodipodi': 'http://sodipodi.sourceforge.net/DTD/sodipodi-0.dtd',
    'xlink': 'http://www.w3.org/1999/xlink'
}

class VectorEngine:
    """
    Motor de Manipulação Vetorial de Alta Fidelidade.
    Responsável por injetar dados e imagens no DOM do SVG sem quebrar a estrutura.
    """
    
    def __init__(self):
        self.tree: Optional[etree._ElementTree] = None
        self.root: Optional[etree._Element] = None
        self.slots: Dict[str, etree._Element] = {}
        # Cache de fontes para evitar I/O repetitivo durante processamento em lote
        self._font_cache = {} 

    def load_template(self, template_path: str):
        """Carrega e higieniza o template SVG (Remoção de lixo do Inkscape)"""
        parser = etree.XMLParser(remove_blank_text=True)
        self.tree = etree.parse(template_path, parser)
        self.root = self.tree.getroot()
        
        self._purge_namespaces()
        self._index_slots()

    def _purge_namespaces(self):
        """Remove atributos proprietários que não afetam a renderização final"""
        for elem in self.root.iter():
            # Remove atributos indesejados (ex: inkscape:label)
            for key in list(elem.attrib.keys()):
                if any(ns in key for ns in ['inkscape', 'sodipodi', 'adobe']):
                    del elem.attrib[key]

    def _index_slots(self):
        """
        Mapeamento O(1) de Slots.
        Busca por elementos cujos IDs começam com padrões conhecidos.
        """
        self.slots = {}
        # Otimização: XPath restrito para IDs relevantes
        for elem in self.root.xpath('//*[@id]'):
            id_val = elem.get('id')
            # Mapeia slots de Produto (SLOT_), Texto (TXT_) e Alvos de Imagem (ALVO_)
            if id_val.startswith(('SLOT_', 'TXT_', 'ALVO_')):
                self.slots[id_val] = elem

    def _measure_text_width(self, text: str, font_path: str, size: int) -> float:
        """
        Mede a largura real do texto em pixels usando PIL (Headless).
        Isso substitui a heurística falha por precisão determinística.
        """
        # Fallback para fonte padrão se o caminho não for fornecido ou inválido
        # Em produção, apontar para as fontes reais do projeto (ex: Roboto-Bold.ttf)
        cache_key = (font_path, size)
        
        if cache_key not in self._font_cache:
            try:
                # Tenta carregar a fonte real. Se falhar, usa default (o que é ruim, mas não crasha)
                font = ImageFont.truetype(font_path, size) if font_path and font_path != "arial.ttf" else ImageFont.load_default()
            except IOError:
                font = ImageFont.load_default()
            self._font_cache[cache_key] = font
        
        font = self._font_cache[cache_key]
        # getlength é mais preciso que getbbox para layout de texto corrido
        if hasattr(font, 'getlength'):
            return font.getlength(text)
        else:
            return font.getsize(text)[0] # Fallback old PIL

    def fit_text(self, 
                 node_id: str, 
                 text: str, 
                 max_width_px: float, 
                 font_family_path: str = "arial.ttf") -> bool:
        """
        Algoritmo de Busca Binária para Ajuste de Texto.
        Encontra o maior font-size possível que caiba no max_width_px.
        """
        node = self.slots.get(node_id)
        if node is None:
            return False

        # Sanitização básica para XML
        node.text = text
        
        if not max_width_px or max_width_px <= 0:
            return False

        # Limites da busca binária
        min_size = 6
        max_size = 300 # Tamanho arbitrário grande inicial
        
        # Tenta ler o tamanho atual do SVG como ponto de partida
        current_style = node.get('style', '')
        # Extração regex simples de font-size
        match = re.search(r'font-size:\s*(\d+(\.\d+)?)px', current_style)
        if match:
            max_size = float(match.group(1))
        
        # Se max_size for muito pequeno, bump para tentar achar algo melhor se possível ou trust
        if max_size < min_size: max_size = 30.0

        best_size = min_size
        
        # Loop de Busca Binária (Precisão vs Performance)
        low, high = min_size, int(max_size)
        while low <= high:
            mid = (low + high) // 2
            width = self._measure_text_width(text, font_family_path, mid)
            
            if width <= max_width_px:
                best_size = mid
                low = mid + 1
            else:
                high = mid - 1

        # Aplica o novo tamanho
        self._update_style(node, 'font-size', f'{best_size}px')
        return True

    def _update_style(self, node: etree._Element, property_name: str, value: str):
        """Atualiza uma propriedade CSS inline preservando as outras"""
        style = node.get('style', '')
        if property_name in style:
            # Substituição regex segura
            style = re.sub(f'{property_name}:[^;]+', f'{property_name}:{value}', style)
        else:
            if style and not style.endswith(';'):
                style += ';'
            style += f'{property_name}:{value}'
        node.set('style', style.strip(';'))

    def place_image(self, 
                    target_id: str, 
                    img_path: str, 
                    slot_w: float, 
                    slot_h: float) -> bool:
        """
        Calcula Matriz de Transformação Afim para posicionar imagem.
        Modo: 'ASPECT FIT' (Contém a imagem dentro do slot sem distorção).
        """
        node = self.slots.get(target_id)
        if node is None:
            return False

        # Linka a imagem (XLink href é padrão SVG 1.1, href é 2.0. Usamos ambos por segurança)
        node.set('{http://www.w3.org/1999/xlink}href', img_path)
        # Nota: O path deve ser absoluto ou relativo à pasta de execução do renderizador
        
        # Obter dimensões da imagem real (Headless via PIL)
        try:
            with Image.open(img_path) as img:
                w_img, h_img = img.size
        except Exception as e:
            # Fallback para auditoria ou se imagem não existir
            w_img, h_img = 1000, 1000 

        # Cálculo da Escala (Aspect Fit)
        scale = min(slot_w / w_img, slot_h / h_img)
        
        # Cálculo da Translação (Centralizar)
        tx = (slot_w - w_img * scale) / 2
        ty = (slot_h - h_img * scale) / 2
        
        # Aplica Transformação Matrix: matrix(scale_x, skew_y, skew_x, scale_y, trans_x, trans_y)
        # SVG Matrix padrão: [a c e]
        #                    [b d f]
        # Onde a=sx, d=sy, e=tx, f=ty
        matrix_str = f"matrix({scale:.4f},0,0,{scale:.4f},{tx:.2f},{ty:.2f})"
        node.set('transform', matrix_str)
        
        # Reseta x, y, width, height para não conflitarem com a matrix
        node.set('x', '0')
        node.set('y', '0')
        node.set('width', str(w_img)) # A matrix cuida da escala
        node.set('height', str(h_img))
        
        return True

    def save(self, output_path: str):
        self.tree.write(output_path, pretty_print=False, encoding='utf-8')

    # --- Price & Business Logic ---

    def _format_currency(self, value: Optional[float]) -> str:
        """
        Formatação determinística para BRL.
        Evita dependência de locale do SO (que pode ser instável em threads).
        """
        if value is None:
            return ""
        # Formata com 2 casas, troca ponto por vírgula, trata milhares
        return f"{value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

    def handle_price_logic(self, 
                           group_id: str, # ID do grupo ou sufixo onde estão os textos
                           preco_atual: float, 
                           preco_ref: Optional[float] = None):
        """
        Lógica de Negócio para Precificação Visual (De/Por).
        Manipula visibilidade e conteúdo baseada na existência de desconto.
        """
        # Formatação
        str_atual = self._format_currency(preco_atual)
        str_ref = self._format_currency(preco_ref) if preco_ref else ""

        # IDs esperados dentro do template (Convenção do Codex)
        # Assumindo busca global por ID único ou padrão prefixado
        # Se group_id for vazio, assume IDs globais sem sufixo
        suf = f"_{group_id}" if group_id else ""
        
        # 1. Preço POR (Sempre visível)
        # Tenta formatos comuns: TXT_PRECO_POR, TXT_PRECO_BIG, etc.
        self.fit_text(f"TXT_PRECO_POR{suf}", str_atual, 300) 
        
        # Separação Big/Cents (R$ 19 , 90)
        parts = str_atual.split(',')
        if len(parts) == 2:
            self.fit_text(f"TXT_PRECO_BIG{suf}", parts[0], 300) 
            self.fit_text(f"TXT_PRECO_CENTS{suf}", "," + parts[1], 100) 

        # 2. Preço DE (Condicional)
        de_id = f"TXT_PRECO_DE{suf}"
        node_de = self.slots.get(de_id)
        
        if node_de is not None:
            if preco_ref and preco_ref > preco_atual:
                # Tem desconto: Mostra e preenche
                self._update_style(node_de, 'display', 'inline')
                self.fit_text(de_id, f"De R$ {str_ref}", 200)
            else:
                # Não tem desconto: Oculta
                self._update_style(node_de, 'display', 'none')

        # 3. Preço COM (Ex: "R$ 19,90") - Texto completo formatado
        self.fit_text(f"TXT_PRECO_COM{suf}", f"R$ {str_atual}", 300)

    # --- High Level Logic (Kits / Units) ---
    def handle_smart_slot(self, slot_id: str, product_data: dict):
        """
        Orquestra a renderização inteligente do slot (Unidades, Multi-imagem).
        product_data: {'nome_sanitizado': str, 'detalhe_peso': str, 'images': [path], ...}
        """
        # Como o index agora indexa tudo, pegamos o g do slot para contexto se precisar, 
        # mas fit_text agora usa o ID global direto.
        # Precisamos saber IDs esperados dentro do slot.
        # Assumiremos convenção: TXT_NOME_PRODUTO, TXT_UNIDADE, ALVO_IMAGEM
        # Mas IDs em SVG devem ser únicos globalmente. 
        # Se temos multiplos slots, IDs deveriam ser TXT_NOME_PRODUTO_1 etc?
        # O modelo atual assume templates de 1 produto ou IDs fixos?
        # Codex Industrialis implica template de item único ou sistema que gera IDs únicos.
        # Vamos assumir IDs fixos para este contexto de "renderizar 1 item" ou que o slot_id ajuda a achar filhos.
        # PORÉM, self.slots é global.
        # Se o template tem SLOT_01, ele deve ter filhos com IDs únicos ou indexados.
        # O código anterior fit_text usava (parent_id, element_id) para contexto.
        # O novo código usa node_id direto.
        # Adaptação: Vamos procurar filhos no elemento slot se não acharmos no map global ou se for ambiguo.
        # Mas `_index_slots` mapeia tudo globalmente. 
        # Vamos assumir que os IDs das targets são conhecidos ou passados.
        # Simplificação: Usar TXT_NOME_PRODUTO direto se existir.
        
        # 1. Unidade
        # Verifica se TXT_UNIDADE existe no map
        unit_id = "TXT_UNIDADE" 
        nome_id = "TXT_NOME_PRODUTO"
        
        has_unit = unit_id in self.slots
        nome_final = product_data.get('nome_sanitizado', '')
        peso = product_data.get('detalhe_peso', '')

        if not has_unit and peso:
            nome_final = f"{nome_final} {peso}"
        elif has_unit and peso:
            self.fit_text(unit_id, peso, max_width_px=50) # Assumindo 50px

        # 2. Nome
        self.fit_text(nome_id, nome_final, max_width_px=200) # Assumindo 200px

        # 3. Imagens (Grid)
        images = product_data.get('images', [])
        if not images: return
        
        target_id = "ALVO_IMAGEM"
        if len(images) == 1:
            # Precisa ler dimensões do slot para passar para place_image
            t_node = self.slots.get(target_id)
            if t_node is not None:
                w = float(t_node.get('width', '100'))
                h = float(t_node.get('height', '100'))
                self.place_image(target_id, images[0], w, h)
        else:
            self._apply_recursive_grid(target_id, images)

    def _apply_recursive_grid(self, target_id: str, images: List[str]):
        """Divisão matemática do alvo."""
        target = self.slots.get(target_id)
        if target is None: return
        
        # Lê BBOX original
        x = float(target.get('x', '0'))
        y = float(target.get('y', '0'))
        w = float(target.get('width', '100'))
        h = float(target.get('height', '100'))
        parent = target.getparent()
        
        # Remove target original
        parent.remove(target)
        if target_id in self.slots: del self.slots[target_id] # Clean index
        
        # Split Horizontal
        count = len(images)
        sub_w = w / count 
        
        for i, img_path in enumerate(images):
            new_id = f"{target_id}_{i}"
            new_img = etree.Element("{http://www.w3.org/2000/svg}image")
            new_img.set('id', new_id)
            
            new_x = x + (i * sub_w)
            new_img.set('x', str(new_x))
            new_img.set('y', str(y))
            new_img.set('width', str(sub_w))
            new_img.set('height', str(h))
            
            parent.append(new_img)
            self.slots[new_id] = new_img # Re-index dynamic
            
            self.place_image(new_id, img_path, sub_w, h)

    def to_string(self) -> bytes:
        return etree.tostring(self.tree, pretty_print=True)

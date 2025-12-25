"""
AutoTabloide AI - Hunter Web Scraper (Persistent Browser)
==========================================================
Implementação conforme Vol. III, Cap. 10.1.

Web scraper com Playwright para busca de imagens.
Mantém browser persistente para evitar overhead de reconexão.
"""

import asyncio
import logging
import random
from pathlib import Path
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
from datetime import datetime, timedelta

logger = logging.getLogger("Hunter")


# Pool de User-Agents para rotação
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
]


@dataclass
class ImageSearchResult:
    """Resultado de busca de imagem."""
    url: str
    thumbnail_url: str
    source: str
    width: int = 0
    height: int = 0
    title: str = ""


class HunterConfig:
    """Configuração do Hunter."""
    BROWSER_TIMEOUT_MS = 30000
    PAGE_TIMEOUT_MS = 15000
    SCROLL_DELAY_MS = 500
    MAX_RESULTS = 20
    DOWNLOAD_TIMEOUT_S = 30
    BROWSER_IDLE_TIMEOUT_MINUTES = 10


class HunterScraper:
    """
    Scraper de imagens com browser persistente.
    
    Features:
    - Browser Playwright singleton (evita reconexão)
    - Rotação de User-Agents
    - Lazy-loading scroll para carregar mais resultados
    - Fallback entre engines (Google, DuckDuckGo)
    
    Ref: Vol. III, Cap. 10.1
    """
    
    def __init__(self, download_dir: Path = None):
        self.download_dir = download_dir or Path.cwd() / "downloads"
        self.download_dir.mkdir(parents=True, exist_ok=True)
        
        self._playwright = None
        self._browser = None
        self._context = None
        self._page = None
        self._last_activity = None
        self._lock = asyncio.Lock()
    
    async def _ensure_browser(self):
        """Garante que browser está ativo (singleton lazy)."""
        async with self._lock:
            # Verifica timeout de inatividade
            if self._last_activity:
                idle_time = datetime.now() - self._last_activity
                if idle_time > timedelta(minutes=HunterConfig.BROWSER_IDLE_TIMEOUT_MINUTES):
                    await self._close_browser()
            
            if self._browser is None or not self._browser.is_connected():
                await self._start_browser()
            
            self._last_activity = datetime.now()
    
    async def _start_browser(self):
        """Inicia browser Playwright."""
        try:
            from playwright.async_api import async_playwright
            
            logger.info("Iniciando browser Playwright...")
            
            self._playwright = await async_playwright().start()
            self._browser = await self._playwright.chromium.launch(
                headless=True,
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--no-sandbox',
                    '--disable-dev-shm-usage'
                ]
            )
            
            # Contexto com User-Agent aleatório
            self._context = await self._browser.new_context(
                user_agent=random.choice(USER_AGENTS),
                viewport={'width': 1920, 'height': 1080}
            )
            
            self._page = await self._context.new_page()
            
            logger.info("Browser Playwright iniciado com sucesso")
            
        except ImportError:
            logger.error("Playwright não instalado. Execute: pip install playwright && playwright install chromium")
            raise
        except Exception as e:
            logger.error(f"Erro ao iniciar browser: {e}")
            raise
    
    async def _close_browser(self):
        """Fecha browser de forma limpa."""
        try:
            if self._page:
                await self._page.close()
            if self._context:
                await self._context.close()
            if self._browser:
                await self._browser.close()
            if self._playwright:
                await self._playwright.stop()
            
            self._page = None
            self._context = None
            self._browser = None
            self._playwright = None
            
            logger.info("Browser fechado")
            
        except Exception as e:
            logger.warning(f"Erro ao fechar browser: {e}")
    
    def _rotate_user_agent(self):
        """Rotaciona User-Agent para evitar bloqueios."""
        if self._context:
            asyncio.create_task(self._context.set_extra_http_headers({
                'User-Agent': random.choice(USER_AGENTS)
            }))
    
    async def search_images(
        self,
        query: str,
        engine: str = "google",
        max_results: int = None
    ) -> List[ImageSearchResult]:
        """
        Busca imagens em engine de busca.
        
        Args:
            query: Termo de busca (ex: "Arroz Tio João 5kg")
            engine: "google" ou "duckduckgo"
            max_results: Máximo de resultados
        
        Returns:
            Lista de ImageSearchResult
        """
        max_results = max_results or HunterConfig.MAX_RESULTS
        
        await self._ensure_browser()
        self._rotate_user_agent()
        
        try:
            if engine == "google":
                return await self._search_google_images(query, max_results)
            elif engine == "duckduckgo":
                return await self._search_duckduckgo_images(query, max_results)
            else:
                logger.warning(f"Engine desconhecida: {engine}, usando Google")
                return await self._search_google_images(query, max_results)
                
        except Exception as e:
            logger.error(f"Erro na busca ({engine}): {e}")
            
            # Fallback para outro engine
            if engine == "google":
                logger.info("Tentando fallback para DuckDuckGo...")
                try:
                    return await self._search_duckduckgo_images(query, max_results)
                except Exception as e2:
                    logger.error(f"Fallback também falhou: {e2}")
            
            return []
    
    async def _search_google_images(
        self,
        query: str,
        max_results: int
    ) -> List[ImageSearchResult]:
        """Busca no Google Images."""
        url = f"https://www.google.com/search?q={query}&tbm=isch"
        
        await self._page.goto(url, timeout=HunterConfig.PAGE_TIMEOUT_MS)
        
        # Aguarda carregamento
        await self._page.wait_for_selector('img[data-src], img[src*="encrypted"]', timeout=5000)
        
        # Scroll para carregar mais (lazy loading)
        await self._lazy_scroll(3)
        
        # Extrai URLs de imagens
        results = await self._page.evaluate('''
            () => {
                const results = [];
                const imgs = document.querySelectorAll('div[data-id] img');
                
                for (const img of imgs) {
                    const src = img.src || img.dataset.src;
                    if (src && src.startsWith('http') && !src.includes('google.com/logos')) {
                        results.push({
                            url: src,
                            thumbnail_url: src,
                            source: 'google',
                            title: img.alt || ''
                        });
                    }
                }
                
                return results.slice(0, ''' + str(max_results) + ''');
            }
        ''')
        
        return [ImageSearchResult(**r) for r in results]
    
    async def _search_duckduckgo_images(
        self,
        query: str,
        max_results: int
    ) -> List[ImageSearchResult]:
        """Busca no DuckDuckGo Images (fallback)."""
        url = f"https://duckduckgo.com/?q={query}&iax=images&ia=images"
        
        await self._page.goto(url, timeout=HunterConfig.PAGE_TIMEOUT_MS)
        
        # Aguarda tiles de imagem
        await self._page.wait_for_selector('.tile--img', timeout=5000)
        
        # Scroll para mais
        await self._lazy_scroll(2)
        
        # Extrai
        results = await self._page.evaluate('''
            () => {
                const results = [];
                const tiles = document.querySelectorAll('.tile--img img');
                
                for (const img of tiles) {
                    const src = img.src || img.dataset.src;
                    if (src && src.startsWith('http')) {
                        results.push({
                            url: src,
                            thumbnail_url: src,
                            source: 'duckduckgo',
                            title: img.alt || ''
                        });
                    }
                }
                
                return results.slice(0, ''' + str(max_results) + ''');
            }
        ''')
        
        return [ImageSearchResult(**r) for r in results]
    
    async def _lazy_scroll(self, times: int = 3):
        """Executa scroll para trigger lazy loading."""
        for _ in range(times):
            await self._page.evaluate('window.scrollBy(0, window.innerHeight)')
            await asyncio.sleep(HunterConfig.SCROLL_DELAY_MS / 1000)
    
    async def download_image(
        self,
        url: str,
        filename: str = None
    ) -> Optional[Path]:
        """
        Baixa imagem da URL.
        
        Returns:
            Path do arquivo baixado ou None se falhou
        """
        import aiohttp
        import hashlib
        
        if not filename:
            # Gera nome único baseado na URL
            url_hash = hashlib.md5(url.encode()).hexdigest()[:12]
            # Extrai extensão da URL
            ext = '.jpg'
            if '.png' in url.lower():
                ext = '.png'
            elif '.webp' in url.lower():
                ext = '.webp'
            filename = f"img_{url_hash}{ext}"
        
        output_path = self.download_dir / filename
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    url,
                    timeout=aiohttp.ClientTimeout(total=HunterConfig.DOWNLOAD_TIMEOUT_S),
                    headers={'User-Agent': random.choice(USER_AGENTS)}
                ) as response:
                    
                    if response.status != 200:
                        logger.warning(f"HTTP {response.status} ao baixar {url}")
                        return None
                    
                    content = await response.read()
                    
                    # Valida que é realmente uma imagem
                    if len(content) < 1000:
                        logger.warning(f"Conteúdo muito pequeno, possivelmente inválido: {url}")
                        return None
                    
                    output_path.write_bytes(content)
                    logger.debug(f"Imagem baixada: {output_path.name}")
                    
                    return output_path
                    
        except Exception as e:
            logger.error(f"Erro ao baixar {url}: {e}")
            return None
    
    async def filter_noisy_images(
        self,
        image_paths: List[Path],
        max_text_ratio: float = 0.3
    ) -> List[Path]:
        """
        INDUSTRIAL ROBUSTNESS #67: Filtra imagens com muito texto/OCR.
        
        Imagens de produto que contêm muito texto (descrições, tabelas nutricionais
        cobrindo a embalagem) não são adequadas para tabloides.
        
        Usa detecção simples baseada em contraste/edges como proxy para texto.
        
        Args:
            image_paths: Lista de paths de imagens
            max_text_ratio: Ratio máximo de "área de texto" permitido (0.0-1.0)
        
        Returns:
            Lista filtrada de imagens adequadas
        """
        try:
            from PIL import Image
            import numpy as np
        except ImportError:
            logger.warning("PIL/numpy não disponível para filtro de ruído")
            return image_paths
        
        filtered = []
        
        for path in image_paths:
            try:
                with Image.open(path) as img:
                    # Converte para grayscale
                    gray = img.convert('L')
                    arr = np.array(gray)
                    
                    # Calcula variação local (edges = texto/detalhes)
                    # Alto desvio padrão local indica muito texto
                    local_std = np.std(arr)
                    
                    # Normaliza pelo range
                    text_ratio = min(local_std / 80.0, 1.0)  # 80 é limiar empírico
                    
                    if text_ratio <= max_text_ratio:
                        filtered.append(path)
                        logger.debug(f"Imagem aceita: {path.name} (text_ratio={text_ratio:.2f})")
                    else:
                        logger.info(f"Imagem rejeitada por excesso de texto: {path.name} (text_ratio={text_ratio:.2f})")
                        
            except Exception as e:
                logger.warning(f"Erro ao analisar {path}: {e}")
                # Na dúvida, mantém a imagem
                filtered.append(path)
        
        return filtered
    
    async def search_and_download(
        self,
        query: str,
        count: int = 1,
        engine: str = "google",
        filter_noisy: bool = True
    ) -> List[Path]:
        """
        Busca e baixa imagens em uma operação.
        
        INDUSTRIAL ROBUSTNESS #67: Filtra imagens com muito texto automaticamente.
        
        Args:
            query: Termo de busca
            count: Número de imagens desejadas
            engine: "google" ou "duckduckgo"
            filter_noisy: Se True, filtra imagens com excesso de texto
        
        Returns:
            Lista de paths das imagens baixadas (já filtradas)
        """
        # Busca mais que o necessário para compensar filtro
        search_multiplier = 3 if filter_noisy else 2
        results = await self.search_images(query, engine, max_results=count * search_multiplier)
        
        downloaded = []
        for result in results:
            if len(downloaded) >= count * 2:  # Baixa mais para filtrar depois
                break
            
            path = await self.download_image(result.url)
            if path:
                downloaded.append(path)
        
        # #67: Aplica filtro de ruído
        if filter_noisy and downloaded:
            downloaded = await self.filter_noisy_images(downloaded)
        
        # Retorna apenas a quantidade solicitada
        return downloaded[:count]
    
    async def shutdown(self):
        """Encerra o hunter e fecha o browser."""
        await self._close_browser()
        logger.info("Hunter encerrado")


# Singleton
_hunter: Optional[HunterScraper] = None


def get_hunter(download_dir: Path = None) -> HunterScraper:
    """Obtém instância singleton do Hunter."""
    global _hunter
    if _hunter is None:
        _hunter = HunterScraper(download_dir)
    return _hunter


async def search_product_images(
    product_name: str,
    brand: str = None,
    count: int = 3
) -> List[Path]:
    """
    Convenience function para buscar imagens de produto.
    
    Args:
        product_name: Nome do produto
        brand: Marca (opcional)
        count: Quantidade desejada
    
    Returns:
        Lista de paths das imagens baixadas
    """
    hunter = get_hunter()
    
    # Constrói query otimizada
    query = product_name
    if brand:
        query = f"{brand} {product_name}"
    
    # Adiciona termos para melhor resultado de produto
    query += " produto embalagem"
    
    return await hunter.search_and_download(query, count)

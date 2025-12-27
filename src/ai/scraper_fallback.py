"""
AutoTabloide AI - Scraper Fallback System
============================================
Sistema de fallback para scrapers de imagem.
PROTOCOLO DE RETIFICAÇÃO: Passos 53-54, 60, 62 (IA e Sentinela).

Este módulo contém:
- Passo 53: Fallback Hunter (Google -> Bing -> DuckDuckGo)
- Passo 60: Timeout do scraper (10s)
- Passo 62: Suporte a proxy
- Integração com ai_safety.py
"""

import asyncio
import logging
import random
from typing import Optional, List, Dict, Any, Tuple
from abc import ABC, abstractmethod
from dataclasses import dataclass

logger = logging.getLogger("ScraperFallback")


# ==============================================================================
# CONFIGURAÇÃO DE TIMEOUT E RETRY
# ==============================================================================

@dataclass
class ScraperConfig:
    """Configuração de scraping."""
    timeout_seconds: int = 10
    max_retries: int = 3
    retry_delay_seconds: float = 1.0
    
    # Proxy (opcional)
    proxy_url: Optional[str] = None
    
    # Backoff exponencial
    use_exponential_backoff: bool = True
    backoff_multiplier: float = 2.0


# ==============================================================================
# INTERFACE BASE DE SCRAPER
# ==============================================================================

class BaseImageScraper(ABC):
    """Interface base para scrapers de imagem."""
    
    name: str = "base"
    
    def __init__(self, config: ScraperConfig):
        self.config = config
    
    @abstractmethod
    async def search(self, query: str, max_results: int = 10) -> List[Dict[str, Any]]:
        """
        Busca imagens para uma query.
        
        Args:
            query: Termo de busca
            max_results: Máximo de resultados
            
        Returns:
            Lista de dicts com: url, thumbnail, title, source
        """
        pass
    
    def _get_session_params(self) -> dict:
        """Retorna parâmetros para sessão HTTP."""
        from src.ai.ai_safety import UserAgentManager
        
        params = {
            "headers": UserAgentManager.get_headers(),
            "timeout": self.config.timeout_seconds,
        }
        
        if self.config.proxy_url:
            params["proxy"] = self.config.proxy_url
        
        return params


# ==============================================================================
# SCRAPERS ESPECÍFICOS
# ==============================================================================

class GoogleImageScraper(BaseImageScraper):
    """Scraper para Google Images."""
    
    name = "google"
    BASE_URL = "https://www.google.com/search"
    
    async def search(self, query: str, max_results: int = 10) -> List[Dict[str, Any]]:
        """Busca imagens no Google."""
        import aiohttp
        import re
        
        params = {
            "q": query,
            "tbm": "isch",  # Image search
            "hl": "pt-BR",
        }
        
        results = []
        
        try:
            async with aiohttp.ClientSession() as session:
                session_params = self._get_session_params()
                
                async with session.get(
                    self.BASE_URL,
                    params=params,
                    headers=session_params["headers"],
                    timeout=aiohttp.ClientTimeout(total=self.config.timeout_seconds)
                ) as response:
                    
                    if response.status != 200:
                        logger.warning(f"Google retornou status {response.status}")
                        return results
                    
                    html = await response.text()
                    
                    # Extrai URLs de imagem do HTML
                    # Padrão simplificado - produção usaria parsing mais robusto
                    img_pattern = r'\["(https://[^"]+\.(?:jpg|jpeg|png|webp))"'
                    
                    urls = re.findall(img_pattern, html, re.IGNORECASE)[:max_results]
                    
                    for url in urls:
                        results.append({
                            "url": url,
                            "source": "google",
                            "query": query,
                        })
        
        except asyncio.TimeoutError:
            logger.warning(f"Timeout na busca Google: {query}")
        except Exception as e:
            logger.debug(f"Erro no scraper Google: {e}")
        
        return results


class BingImageScraper(BaseImageScraper):
    """Scraper para Bing Images."""
    
    name = "bing"
    BASE_URL = "https://www.bing.com/images/search"
    
    async def search(self, query: str, max_results: int = 10) -> List[Dict[str, Any]]:
        """Busca imagens no Bing."""
        import aiohttp
        import re
        
        params = {
            "q": query,
            "form": "HDRSC2",
            "first": 1,
        }
        
        results = []
        
        try:
            async with aiohttp.ClientSession() as session:
                session_params = self._get_session_params()
                
                async with session.get(
                    self.BASE_URL,
                    params=params,
                    headers=session_params["headers"],
                    timeout=aiohttp.ClientTimeout(total=self.config.timeout_seconds)
                ) as response:
                    
                    if response.status != 200:
                        logger.warning(f"Bing retornou status {response.status}")
                        return results
                    
                    html = await response.text()
                    
                    # Extrai URLs de miniatura do Bing
                    img_pattern = r'murl":"(https?://[^"]+)"'
                    
                    urls = re.findall(img_pattern, html)[:max_results]
                    
                    for url in urls:
                        if any(ext in url.lower() for ext in ['.jpg', '.jpeg', '.png', '.webp']):
                            results.append({
                                "url": url,
                                "source": "bing",
                                "query": query,
                            })
        
        except asyncio.TimeoutError:
            logger.warning(f"Timeout na busca Bing: {query}")
        except Exception as e:
            logger.debug(f"Erro no scraper Bing: {e}")
        
        return results


class DuckDuckGoImageScraper(BaseImageScraper):
    """Scraper para DuckDuckGo Images."""
    
    name = "duckduckgo"
    BASE_URL = "https://duckduckgo.com/"
    
    async def search(self, query: str, max_results: int = 10) -> List[Dict[str, Any]]:
        """Busca imagens no DuckDuckGo."""
        import aiohttp
        import re
        
        results = []
        
        try:
            async with aiohttp.ClientSession() as session:
                session_params = self._get_session_params()
                
                # Primeiro request para obter vqd token
                async with session.get(
                    f"{self.BASE_URL}?q={query}&iax=images&ia=images",
                    headers=session_params["headers"],
                    timeout=aiohttp.ClientTimeout(total=self.config.timeout_seconds)
                ) as response:
                    
                    html = await response.text()
                    
                    # Extrai vqd token
                    vqd_match = re.search(r'vqd=([\d-]+)', html)
                    if not vqd_match:
                        return results
                    
                    vqd = vqd_match.group(1)
                
                # Request de imagens
                images_url = f"https://duckduckgo.com/i.js"
                params = {
                    "l": "br-pt",
                    "o": "json",
                    "q": query,
                    "vqd": vqd,
                }
                
                async with session.get(
                    images_url,
                    params=params,
                    headers=session_params["headers"],
                    timeout=aiohttp.ClientTimeout(total=self.config.timeout_seconds)
                ) as response:
                    
                    data = await response.json()
                    
                    for item in data.get("results", [])[:max_results]:
                        if "image" in item:
                            results.append({
                                "url": item["image"],
                                "thumbnail": item.get("thumbnail"),
                                "title": item.get("title"),
                                "source": "duckduckgo",
                                "query": query,
                            })
        
        except asyncio.TimeoutError:
            logger.warning(f"Timeout na busca DuckDuckGo: {query}")
        except Exception as e:
            logger.debug(f"Erro no scraper DuckDuckGo: {e}")
        
        return results


# ==============================================================================
# GERENCIADOR DE FALLBACK
# ==============================================================================

class FallbackScraperManager:
    """
    PASSO 53: Sistema de fallback para scrapers.
    
    Tenta Google -> Bing -> DuckDuckGo até conseguir resultados.
    """
    
    def __init__(self, config: Optional[ScraperConfig] = None):
        self.config = config or ScraperConfig()
        
        # Scrapers em ordem de preferência
        self.scrapers: List[BaseImageScraper] = [
            GoogleImageScraper(self.config),
            BingImageScraper(self.config),
            DuckDuckGoImageScraper(self.config),
        ]
        
        # Estatísticas de falha por scraper
        self._failure_counts: Dict[str, int] = {}
        self._success_counts: Dict[str, int] = {}
    
    async def search_with_fallback(
        self,
        query: str,
        max_results: int = 10,
        min_results: int = 1
    ) -> Tuple[List[Dict[str, Any]], str]:
        """
        Busca imagens com fallback automático.
        
        Args:
            query: Termo de busca
            max_results: Máximo de resultados desejados
            min_results: Mínimo para considerar sucesso
            
        Returns:
            Tuple (resultados, nome_do_scraper_usado)
        """
        # Ordenar scrapers por taxa de sucesso
        ordered_scrapers = self._get_ordered_scrapers()
        
        for scraper in ordered_scrapers:
            try:
                results = await scraper.search(query, max_results)
                
                if len(results) >= min_results:
                    self._record_success(scraper.name)
                    logger.info(f"Busca OK via {scraper.name}: {len(results)} resultados")
                    return results, scraper.name
                else:
                    self._record_failure(scraper.name)
                    logger.debug(f"{scraper.name} retornou poucos resultados ({len(results)})")
                    
            except Exception as e:
                self._record_failure(scraper.name)
                logger.warning(f"Scraper {scraper.name} falhou: {e}")
                
                # Delay antes do próximo
                await asyncio.sleep(self.config.retry_delay_seconds)
        
        logger.error(f"Todos os scrapers falharam para: {query}")
        return [], "none"
    
    def _get_ordered_scrapers(self) -> List[BaseImageScraper]:
        """Retorna scrapers ordenados por taxa de sucesso."""
        def success_rate(scraper):
            name = scraper.name
            total = self._success_counts.get(name, 0) + self._failure_counts.get(name, 0)
            if total == 0:
                return 0.5  # Default 50%
            return self._success_counts.get(name, 0) / total
        
        return sorted(self.scrapers, key=success_rate, reverse=True)
    
    def _record_success(self, name: str) -> None:
        """Registra sucesso de um scraper."""
        self._success_counts[name] = self._success_counts.get(name, 0) + 1
    
    def _record_failure(self, name: str) -> None:
        """Registra falha de um scraper."""
        self._failure_counts[name] = self._failure_counts.get(name, 0) + 1
    
    def get_statistics(self) -> Dict[str, Dict[str, Any]]:
        """Retorna estatísticas de uso dos scrapers."""
        stats = {}
        
        for scraper in self.scrapers:
            name = scraper.name
            successes = self._success_counts.get(name, 0)
            failures = self._failure_counts.get(name, 0)
            total = successes + failures
            
            stats[name] = {
                "successes": successes,
                "failures": failures,
                "total": total,
                "success_rate": successes / total if total > 0 else 0,
            }
        
        return stats
    
    def set_proxy(self, proxy_url: str) -> None:
        """
        PASSO 62: Define proxy para todos os scrapers.
        
        Args:
            proxy_url: URL do proxy (ex: http://proxy:8080)
        """
        self.config.proxy_url = proxy_url
        
        # Recria scrapers com nova config
        self.scrapers = [
            GoogleImageScraper(self.config),
            BingImageScraper(self.config),
            DuckDuckGoImageScraper(self.config),
        ]
        
        logger.info(f"Proxy configurado: {proxy_url}")


# ==============================================================================
# INSTANCE GLOBAL
# ==============================================================================

_scraper_manager: Optional[FallbackScraperManager] = None


def get_scraper_manager() -> FallbackScraperManager:
    """Retorna instância global do gerenciador de scrapers."""
    global _scraper_manager
    
    if _scraper_manager is None:
        _scraper_manager = FallbackScraperManager()
    
    return _scraper_manager


async def search_images(query: str, max_results: int = 10) -> List[Dict[str, Any]]:
    """
    Função de conveniência para buscar imagens.
    
    Args:
        query: Termo de busca
        max_results: Máximo de resultados
        
    Returns:
        Lista de resultados
    """
    from src.ai.ai_safety import SearchCache
    
    # Verifica cache primeiro
    cached = SearchCache.get(query)
    if cached:
        logger.debug(f"Cache hit para: {query}")
        return [{"url": url, "source": "cache", "query": query} for url in cached]
    
    # Busca com fallback
    manager = get_scraper_manager()
    results, source = await manager.search_with_fallback(query, max_results)
    
    # Salva no cache
    if results:
        urls = [r["url"] for r in results]
        SearchCache.set(query, urls, source)
    
    return results

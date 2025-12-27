"""
AutoTabloide AI - SVG Cache System
====================================
Cache LRU para objetos SVG parseados.
PROTOCOLO DE RETIFICAÇÃO: Passos 31, 33 (Motor Vetorial).

Este módulo contém:
- Passo 31: Parse SVG em executor (async)
- Passo 33: Cache LRU de SVG parseados
"""

import asyncio
import hashlib
import logging
from pathlib import Path
from typing import Optional, Dict, Any, Tuple
from collections import OrderedDict
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from datetime import datetime
import threading

logger = logging.getLogger("SVGCache")


# ==============================================================================
# PASSO 33: CACHE LRU DE SVG
# ==============================================================================

@dataclass
class CachedSVG:
    """Representa um SVG em cache."""
    tree: Any  # lxml etree
    file_hash: str
    parsed_at: datetime
    size_bytes: int
    access_count: int = 0
    last_accessed: datetime = field(default_factory=datetime.now)


class SVGLRUCache:
    """
    Cache LRU para árvores SVG parseadas.
    
    PROBLEMA: Parsear SVG é caro (~50-100ms por arquivo).
    
    SOLUÇÃO: Cache em memória com evição LRU.
    """
    
    DEFAULT_MAX_SIZE = 50  # Máximo de SVGs em cache
    DEFAULT_MAX_MEMORY_MB = 100  # Limite de memória
    
    def __init__(
        self,
        max_size: int = DEFAULT_MAX_SIZE,
        max_memory_mb: int = DEFAULT_MAX_MEMORY_MB
    ):
        self.max_size = max_size
        self.max_memory_bytes = max_memory_mb * 1024 * 1024
        
        self._cache: OrderedDict[str, CachedSVG] = OrderedDict()
        self._lock = threading.RLock()
        self._current_memory = 0
        
        # Estatísticas
        self._hits = 0
        self._misses = 0
    
    def get(self, file_path: str) -> Optional[Any]:
        """
        Recupera SVG do cache se existir e não estiver stale.
        
        Args:
            file_path: Caminho absoluto do arquivo SVG
            
        Returns:
            Árvore lxml ou None
        """
        key = self._get_key(file_path)
        
        with self._lock:
            if key not in self._cache:
                self._misses += 1
                return None
            
            entry = self._cache[key]
            
            # Verificar se arquivo mudou
            current_hash = self._compute_file_hash(file_path)
            if current_hash != entry.file_hash:
                # Arquivo modificado - invalidar
                self._remove(key)
                self._misses += 1
                return None
            
            # Atualizar estatísticas de acesso (LRU)
            entry.access_count += 1
            entry.last_accessed = datetime.now()
            
            # Move para o fim (mais recente)
            self._cache.move_to_end(key)
            
            self._hits += 1
            return entry.tree
    
    def put(self, file_path: str, tree: Any) -> None:
        """
        Adiciona SVG ao cache.
        
        Args:
            file_path: Caminho do arquivo
            tree: Árvore lxml parseada
        """
        key = self._get_key(file_path)
        file_hash = self._compute_file_hash(file_path)
        
        # Estimar tamanho (aproximado)
        size_bytes = self._estimate_tree_size(tree)
        
        with self._lock:
            # Remover se já existe
            if key in self._cache:
                self._remove(key)
            
            # Garantir espaço
            self._ensure_capacity(size_bytes)
            
            # Adicionar
            entry = CachedSVG(
                tree=tree,
                file_hash=file_hash,
                parsed_at=datetime.now(),
                size_bytes=size_bytes
            )
            
            self._cache[key] = entry
            self._current_memory += size_bytes
    
    def invalidate(self, file_path: str) -> bool:
        """
        Invalida entrada específica do cache.
        
        Returns:
            True se entrada existia e foi removida
        """
        key = self._get_key(file_path)
        
        with self._lock:
            if key in self._cache:
                self._remove(key)
                return True
            return False
    
    def clear(self) -> int:
        """
        Limpa todo o cache.
        
        Returns:
            Número de entradas removidas
        """
        with self._lock:
            count = len(self._cache)
            self._cache.clear()
            self._current_memory = 0
            return count
    
    def get_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas do cache."""
        with self._lock:
            total = self._hits + self._misses
            hit_rate = self._hits / total if total > 0 else 0
            
            return {
                "entries": len(self._cache),
                "memory_mb": self._current_memory / (1024 * 1024),
                "max_size": self.max_size,
                "max_memory_mb": self.max_memory_bytes / (1024 * 1024),
                "hits": self._hits,
                "misses": self._misses,
                "hit_rate": hit_rate,
            }
    
    def _get_key(self, file_path: str) -> str:
        """Gera chave única para arquivo."""
        return str(Path(file_path).resolve())
    
    def _compute_file_hash(self, file_path: str) -> str:
        """Calcula hash do arquivo para detectar mudanças."""
        try:
            path = Path(file_path)
            if not path.exists():
                return ""
            
            # Hash rápido: tamanho + mtime
            stat = path.stat()
            content = f"{stat.st_size}:{stat.st_mtime}"
            return hashlib.md5(content.encode()).hexdigest()
        except Exception:
            return ""
    
    def _estimate_tree_size(self, tree: Any) -> int:
        """Estima tamanho da árvore em bytes."""
        try:
            from lxml import etree
            xml_bytes = etree.tostring(tree)
            return len(xml_bytes)
        except Exception:
            return 50000  # Estimativa padrão 50KB
    
    def _remove(self, key: str) -> None:
        """Remove entrada do cache (interno)."""
        if key in self._cache:
            entry = self._cache[key]
            self._current_memory -= entry.size_bytes
            del self._cache[key]
    
    def _ensure_capacity(self, needed_bytes: int) -> None:
        """Garante espaço para nova entrada evictando LRU."""
        # Evict por contagem
        while len(self._cache) >= self.max_size:
            oldest_key = next(iter(self._cache))
            self._remove(oldest_key)
        
        # Evict por memória
        while self._current_memory + needed_bytes > self.max_memory_bytes:
            if not self._cache:
                break
            oldest_key = next(iter(self._cache))
            self._remove(oldest_key)


# ==============================================================================
# PASSO 31: PARSE SVG EM EXECUTOR (ASYNC)
# ==============================================================================

class AsyncSVGParser:
    """
    Parser assíncrono de SVG usando ThreadPoolExecutor.
    
    PROBLEMA: Parse de SVG bloqueia a thread principal.
    
    SOLUÇÃO: Executar em thread pool separado.
    """
    
    def __init__(self, cache: Optional[SVGLRUCache] = None, max_workers: int = 4):
        self.cache = cache or SVGLRUCache()
        self._executor = ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix="SVGParser")
    
    async def parse_file(self, file_path: str) -> Tuple[Any, bool]:
        """
        Parseia arquivo SVG de forma assíncrona.
        
        Args:
            file_path: Caminho do arquivo SVG
            
        Returns:
            Tuple (árvore_lxml, foi_cache_hit)
        """
        # Verificar cache primeiro
        cached = self.cache.get(file_path)
        if cached is not None:
            return cached, True
        
        # Parse em background thread
        loop = asyncio.get_event_loop()
        tree = await loop.run_in_executor(
            self._executor,
            self._parse_svg_sync,
            file_path
        )
        
        # Adicionar ao cache
        if tree is not None:
            self.cache.put(file_path, tree)
        
        return tree, False
    
    async def parse_string(self, svg_content: str) -> Any:
        """
        Parseia string SVG de forma assíncrona.
        
        Args:
            svg_content: Conteúdo SVG como string
            
        Returns:
            Árvore lxml
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self._executor,
            self._parse_svg_string_sync,
            svg_content
        )
    
    async def parse_multiple(self, file_paths: list) -> list:
        """
        Parseia múltiplos arquivos em paralelo.
        
        Args:
            file_paths: Lista de caminhos
            
        Returns:
            Lista de árvores (ou None para erros)
        """
        tasks = [self.parse_file(path) for path in file_paths]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        return [
            r[0] if isinstance(r, tuple) else None
            for r in results
        ]
    
    def _parse_svg_sync(self, file_path: str) -> Optional[Any]:
        """Parse síncrono de arquivo SVG."""
        try:
            from lxml import etree
            
            parser = etree.XMLParser(
                remove_blank_text=True,
                remove_comments=True,
                recover=True
            )
            
            tree = etree.parse(file_path, parser)
            return tree.getroot()
            
        except Exception as e:
            logger.error(f"Erro ao parsear SVG {file_path}: {e}")
            return None
    
    def _parse_svg_string_sync(self, svg_content: str) -> Optional[Any]:
        """Parse síncrono de string SVG."""
        try:
            from lxml import etree
            
            parser = etree.XMLParser(
                remove_blank_text=True,
                remove_comments=True,
                recover=True
            )
            
            return etree.fromstring(svg_content.encode('utf-8'), parser)
            
        except Exception as e:
            logger.error(f"Erro ao parsear SVG string: {e}")
            return None
    
    def shutdown(self) -> None:
        """Encerra executor."""
        self._executor.shutdown(wait=False)
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas do cache."""
        return self.cache.get_stats()


# ==============================================================================
# INSTÂNCIA GLOBAL
# ==============================================================================

_svg_cache: Optional[SVGLRUCache] = None
_svg_parser: Optional[AsyncSVGParser] = None


def get_svg_cache() -> SVGLRUCache:
    """Retorna instância global do cache."""
    global _svg_cache
    if _svg_cache is None:
        _svg_cache = SVGLRUCache()
    return _svg_cache


def get_svg_parser() -> AsyncSVGParser:
    """Retorna instância global do parser."""
    global _svg_parser
    if _svg_parser is None:
        _svg_parser = AsyncSVGParser(get_svg_cache())
    return _svg_parser


async def parse_svg_async(file_path: str) -> Any:
    """
    Função de conveniência para parse assíncrono.
    
    Args:
        file_path: Caminho do SVG
        
    Returns:
        Árvore lxml
    """
    parser = get_svg_parser()
    tree, _ = await parser.parse_file(file_path)
    return tree

"""
AutoTabloide AI - Motor de RAG (Retrieval-Augmented Generation)
================================================================
Memória institucional via embeddings locais conforme Vol. IV, Cap. 2.
Permite que o sistema "aprenda" com correções humanas.
"""

import os
import json
import logging
import hashlib
import numpy as np
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger("RAGEngine")


@dataclass
class KnowledgeEntry:
    """Entrada de conhecimento no RAG."""
    id: int
    source_text: str
    sanitized_text: str
    embedding: List[float]
    metadata: Dict[str, Any]
    created_at: datetime
    usage_count: int = 0


class RAGEngine:
    """
    Motor de Retrieval-Augmented Generation.
    
    Funcionalidades:
    - Armazena correções humanas como vetores
    - Busca semântica via similaridade de cosseno
    - Gera few-shot prompts para o LLM
    
    Uso:
        rag = RAGEngine()
        
        # Adiciona conhecimento
        await rag.add_knowledge("SAB OMO 500", "Sabão em Pó Omo 500g")
        
        # Busca similar
        examples = await rag.find_similar("SABAO OMO", top_k=3)
        
        # Gera prompt com exemplos
        prompt = rag.build_few_shot_prompt("DETERG YPE 500", examples)
    """
    
    EMBEDDING_DIMENSION = 384  # all-MiniLM-L6-v2
    
    def __init__(self, db_path: Optional[str] = None):
        """
        Args:
            db_path: Caminho para o banco SQLite. Se None, usa o padrão.
        """
        if db_path:
            self.db_path = Path(db_path)
        else:
            self.db_path = Path(__file__).parent.parent.parent / \
                "AutoTabloide_System_Root" / "database" / "core.db"
        
        self._embedder = None
        self._cache: Dict[str, List[float]] = {}
    
    @property
    def embedder(self):
        """Lazy loading do modelo de embeddings."""
        if self._embedder is None:
            try:
                from sentence_transformers import SentenceTransformer
                self._embedder = SentenceTransformer('all-MiniLM-L6-v2')
                logger.info("Embedder carregado: all-MiniLM-L6-v2")
            except ImportError:
                logger.warning("sentence-transformers não disponível")
            except Exception as e:
                logger.error(f"Erro ao carregar embedder: {e}")
        return self._embedder
    
    def _compute_embedding(self, text: str) -> Optional[List[float]]:
        """Computa embedding para texto."""
        if not text:
            return None
        
        # Cache por hash do texto
        # INDUSTRIAL ROBUSTNESS #107: SHA-256
        text_hash = hashlib.sha256(text.encode()).hexdigest()
        if text_hash in self._cache:
            return self._cache[text_hash]
        
        if self.embedder is None:
            return None
        
        try:
            vector = self.embedder.encode(text).tolist()
            self._cache[text_hash] = vector
            return vector
        except Exception as e:
            logger.error(f"Erro ao computar embedding: {e}")
            return None
    
    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calcula similaridade de cosseno entre dois vetores."""
        a = np.array(vec1)
        b = np.array(vec2)
        
        dot_product = np.dot(a, b)
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)
        
        if norm_a == 0 or norm_b == 0:
            return 0.0
        
        return float(dot_product / (norm_a * norm_b))
    
    async def add_knowledge(
        self,
        source_text: str,
        sanitized_text: str,
        entity_type: str = "product",
        metadata: Optional[Dict] = None
    ) -> Optional[int]:
        """
        Adiciona conhecimento ao banco de vetores.
        
        Args:
            source_text: Texto original/bruto
            sanitized_text: Texto corrigido/sanitizado
            entity_type: Tipo de entidade (product, brand, etc)
            metadata: Metadados adicionais
            
        Returns:
            ID do registro inserido ou None se falhou
        """
        from sqlalchemy import text
        from src.core.database import AsyncSessionLocal
        
        # Gera embedding do texto fonte
        embedding = self._compute_embedding(source_text)
        if embedding is None:
            # Fallback: salva sem embedding
            embedding = [0.0] * self.EMBEDDING_DIMENSION
        
        embedding_json = json.dumps(embedding)
        metadata_json = json.dumps(metadata or {})
        
        async with AsyncSessionLocal() as session:
            try:
                result = await session.execute(
                    text("""
                        INSERT INTO knowledge_vector 
                        (entity_type, source_text, embedding_vector, metadata)
                        VALUES (:entity_type, :source_text, :embedding, :metadata)
                    """),
                    {
                        "entity_type": entity_type,
                        "source_text": source_text,
                        "embedding": embedding_json,
                        "metadata": metadata_json
                    }
                )
                await session.commit()
                
                # Retorna o ID inserido
                result = await session.execute(text("SELECT last_insert_rowid()"))
                row = result.fetchone()
                
                logger.info(f"Conhecimento adicionado: '{source_text}' -> '{sanitized_text}'")
                return row[0] if row else None
                
            except Exception as e:
                logger.error(f"Erro ao adicionar conhecimento: {e}")
                await session.rollback()
                return None
    
    async def find_similar(
        self,
        query: str,
        top_k: int = 3,
        threshold: float = 0.5,
        entity_type: Optional[str] = None
    ) -> List[Tuple[str, str, float]]:
        """
        Busca conhecimentos similares via similaridade de cosseno.
        
        Args:
            query: Texto de busca
            top_k: Número máximo de resultados
            threshold: Similaridade mínima (0-1)
            entity_type: Filtrar por tipo de entidade
            
        Returns:
            Lista de tuplas (source_text, metadata, similarity_score)
        """
        from sqlalchemy import text
        from src.core.database import AsyncSessionLocal
        
        query_embedding = self._compute_embedding(query)
        if query_embedding is None:
            return []
        
        async with AsyncSessionLocal() as session:
            try:
                # Busca todos os vetores do tipo especificado
                if entity_type:
                    result = await session.execute(
                        text("""
                            SELECT id, source_text, embedding_vector, metadata
                            FROM knowledge_vector
                            WHERE entity_type = :entity_type
                        """),
                        {"entity_type": entity_type}
                    )
                else:
                    result = await session.execute(
                        text("SELECT id, source_text, embedding_vector, metadata FROM knowledge_vector")
                    )
                
                rows = result.fetchall()
                
                # Calcula similaridades
                similarities = []
                for row in rows:
                    try:
                        stored_embedding = json.loads(row[2])
                        if len(stored_embedding) != len(query_embedding):
                            continue
                        
                        similarity = self._cosine_similarity(query_embedding, stored_embedding)
                        if similarity >= threshold:
                            metadata = json.loads(row[3]) if row[3] else {}
                            similarities.append((row[1], metadata, similarity))
                    except (json.JSONDecodeError, ValueError):
                        continue
                
                # Ordena por similaridade e retorna top_k
                similarities.sort(key=lambda x: x[2], reverse=True)
                return similarities[:top_k]
                
            except Exception as e:
                logger.error(f"Erro na busca de similaridade: {e}")
                return []
    
    async def learn_from_correction(
        self,
        original: str,
        corrected: Dict[str, Any],
        product_id: Optional[int] = None
    ):
        """
        Aprende com uma correção humana.
        
        Args:
            original: Texto original que foi corrigido
            corrected: Dicionário com dados corrigidos
            product_id: ID do produto (se aplicável)
        """
        # Monta texto sanitizado a partir do dicionário
        sanitized_parts = []
        if corrected.get("marca"):
            sanitized_parts.append(corrected["marca"])
        if corrected.get("produto"):
            sanitized_parts.append(corrected["produto"])
        if corrected.get("variacao"):
            sanitized_parts.append(corrected["variacao"])
        if corrected.get("peso"):
            sanitized_parts.append(corrected["peso"])
        
        sanitized_text = " ".join(sanitized_parts)
        
        metadata = {
            "corrected_data": corrected,
            "product_id": product_id,
            "learned_at": datetime.now().isoformat()
        }
        
        await self.add_knowledge(
            source_text=original,
            sanitized_text=sanitized_text,
            entity_type="product_correction",
            metadata=metadata
        )
        
        logger.info(f"Aprendido: '{original}' -> '{sanitized_text}'")
    
    def build_few_shot_prompt(
        self,
        query: str,
        examples: List[Tuple[str, Dict, float]],
        system_prompt: Optional[str] = None
    ) -> str:
        """
        Constrói prompt com exemplos few-shot.
        
        Args:
            query: Texto a ser processado
            examples: Lista de exemplos similares [(source, metadata, score)]
            system_prompt: Prompt de sistema customizado
            
        Returns:
            Prompt completo com exemplos
        """
        if system_prompt is None:
            system_prompt = """Você é um algoritmo de limpeza de dados (ETL) para varejo brasileiro.
Analise a entrada e extraia as informações para JSON estruturado."""
        
        prompt_parts = [system_prompt, "", "Exemplos históricos desta loja:"]
        
        for source, metadata, score in examples:
            corrected = metadata.get("corrected_data", {})
            if corrected:
                prompt_parts.append(f"Entrada: \"{source}\"")
                prompt_parts.append(f"Saída: {json.dumps(corrected, ensure_ascii=False)}")
                prompt_parts.append("")
        
        prompt_parts.append(f"Agora processe:")
        prompt_parts.append(f"Entrada: \"{query}\"")
        prompt_parts.append("Saída:")
        
        return "\n".join(prompt_parts)
    
    async def get_augmented_prompt(
        self,
        query: str,
        top_k: int = 3,
        threshold: float = 0.6
    ) -> Tuple[str, List]:
        """
        Obtém prompt aumentado com exemplos do RAG.
        Conveniência para uso direto com LLM.
        
        Args:
            query: Texto a processar
            top_k: Número de exemplos
            threshold: Similaridade mínima
            
        Returns:
            Tupla (prompt_completo, exemplos_usados)
        """
        examples = await self.find_similar(
            query,
            top_k=top_k,
            threshold=threshold,
            entity_type="product_correction"
        )
        
        prompt = self.build_few_shot_prompt(query, examples)
        return prompt, examples
    
    async def get_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas do banco de conhecimento."""
        from sqlalchemy import text
        from src.core.database import AsyncSessionLocal
        
        async with AsyncSessionLocal() as session:
            try:
                # Total de entradas
                result = await session.execute(
                    text("SELECT COUNT(*) FROM knowledge_vector")
                )
                total = result.scalar() or 0
                
                # Por tipo
                result = await session.execute(
                    text("""
                        SELECT entity_type, COUNT(*) 
                        FROM knowledge_vector 
                        GROUP BY entity_type
                    """)
                )
                by_type = {row[0]: row[1] for row in result.fetchall()}
                
                return {
                    "total_entries": total,
                    "by_type": by_type,
                    "embedding_dimension": self.EMBEDDING_DIMENSION,
                    "embedder_loaded": self._embedder is not None,
                    "cache_size": len(self._cache)
                }
                
            except Exception as e:
                logger.error(f"Erro ao obter stats: {e}")
                return {"error": str(e)}


# Singleton global
_rag_engine: Optional[RAGEngine] = None


def get_rag_engine() -> RAGEngine:
    """Obtém instância singleton do RAGEngine."""
    global _rag_engine
    if _rag_engine is None:
        _rag_engine = RAGEngine()
    return _rag_engine


async def initialize_rag_engine() -> RAGEngine:
    """Inicializa o RAGEngine e pré-aquece o embedder."""
    engine = get_rag_engine()
    
    # Pré-aquece o embedder com texto dummy
    if engine.embedder is not None:
        engine._compute_embedding("teste de inicialização")
        logger.info("RAGEngine inicializado e pré-aquecido")
    
    return engine

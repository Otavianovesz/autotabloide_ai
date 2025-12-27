"""
AutoTabloide AI - JSON Compression
====================================
Compressão de JSON para economizar espaço.
PROTOCOLO DE RETIFICAÇÃO: Passo 29 (Compressão de JSON).

Comprime campos JSON grandes no banco de dados.
"""

import logging
import json
import zlib
import base64
from typing import Optional, Any, Union

logger = logging.getLogger("JSONCompression")


class JSONCompressor:
    """
    Compressor de JSON para armazenamento.
    
    PASSO 29: Reduz tamanho de dados JSON no SQLite.
    """
    
    # Prefixo para identificar dados comprimidos
    COMPRESSED_PREFIX = "ZLIB:"
    
    # Tamanho mínimo para comprimir (bytes)
    MIN_SIZE_TO_COMPRESS = 500
    
    # Nível de compressão (1-9, 9 = máximo)
    COMPRESSION_LEVEL = 6
    
    @classmethod
    def compress(cls, data: Any) -> str:
        """
        Comprime dados para string armazenável.
        
        Args:
            data: Dados Python (dict, list, etc)
            
        Returns:
            String JSON (normal ou comprimida)
        """
        if data is None:
            return ""
        
        # Serializar para JSON
        json_str = json.dumps(data, ensure_ascii=False, separators=(',', ':'))
        
        # Verificar se vale comprimir
        if len(json_str) < cls.MIN_SIZE_TO_COMPRESS:
            return json_str
        
        try:
            # Comprimir
            compressed = zlib.compress(
                json_str.encode('utf-8'),
                level=cls.COMPRESSION_LEVEL
            )
            
            # Converter para base64
            b64 = base64.b64encode(compressed).decode('ascii')
            
            # Retornar com prefixo
            result = f"{cls.COMPRESSED_PREFIX}{b64}"
            
            # Verificar se realmente economizou
            if len(result) < len(json_str):
                savings = (1 - len(result) / len(json_str)) * 100
                logger.debug(f"JSON comprimido: {savings:.1f}% economia")
                return result
            else:
                # Não compensou, retorna original
                return json_str
            
        except Exception as e:
            logger.debug(f"Compressão falhou: {e}")
            return json_str
    
    @classmethod
    def decompress(cls, data: str) -> Any:
        """
        Descomprime string para dados Python.
        
        Args:
            data: String JSON (normal ou comprimida)
            
        Returns:
            Dados Python
        """
        if not data:
            return None
        
        try:
            # Verificar se está comprimido
            if data.startswith(cls.COMPRESSED_PREFIX):
                # Remover prefixo
                b64 = data[len(cls.COMPRESSED_PREFIX):]
                
                # Decodificar base64
                compressed = base64.b64decode(b64)
                
                # Descomprimir
                json_str = zlib.decompress(compressed).decode('utf-8')
                
                return json.loads(json_str)
            else:
                # JSON normal
                return json.loads(data)
                
        except Exception as e:
            logger.error(f"Erro ao descomprimir: {e}")
            return None
    
    @classmethod
    def estimate_savings(cls, data: Any) -> dict:
        """
        Estima economia de compressão.
        
        Returns:
            Dict com métricas
        """
        json_str = json.dumps(data, ensure_ascii=False)
        original_size = len(json_str.encode('utf-8'))
        
        try:
            compressed = zlib.compress(json_str.encode('utf-8'), level=cls.COMPRESSION_LEVEL)
            compressed_size = len(base64.b64encode(compressed))
        except Exception:
            compressed_size = original_size
        
        return {
            "original_bytes": original_size,
            "compressed_bytes": compressed_size,
            "savings_percent": (1 - compressed_size / original_size) * 100 if original_size > 0 else 0,
            "worth_compressing": compressed_size < original_size
        }


# ==============================================================================
# HELPERS PARA SQLALCHEMY
# ==============================================================================

def compress_json_field(data: Any) -> str:
    """Helper para comprimir antes de salvar."""
    return JSONCompressor.compress(data)


def decompress_json_field(data: str) -> Any:
    """Helper para descomprimir ao carregar."""
    return JSONCompressor.decompress(data)


# ==============================================================================
# COMPACTADOR DE BANCO
# ==============================================================================

class DatabaseCompactor:
    """Compacta campos JSON em tabelas existentes."""
    
    @staticmethod
    async def compact_table(
        session,
        table_name: str,
        json_column: str,
        id_column: str = "id"
    ) -> dict:
        """
        Compacta coluna JSON de uma tabela.
        
        Returns:
            Dict com estatísticas
        """
        from sqlalchemy import text
        
        stats = {
            "processed": 0,
            "compressed": 0,
            "bytes_saved": 0
        }
        
        # Ler todos os registros
        result = await session.execute(text(
            f"SELECT {id_column}, {json_column} FROM {table_name}"
        ))
        rows = result.fetchall()
        
        for row in rows:
            record_id = row[0]
            json_data = row[1]
            
            if not json_data or json_data.startswith(JSONCompressor.COMPRESSED_PREFIX):
                continue
            
            stats["processed"] += 1
            
            # Tentar comprimir
            compressed = JSONCompressor.compress(json.loads(json_data))
            
            if compressed != json_data:
                # Atualizar
                await session.execute(text(
                    f"UPDATE {table_name} SET {json_column} = :data WHERE {id_column} = :id"
                ), {"data": compressed, "id": record_id})
                
                stats["compressed"] += 1
                stats["bytes_saved"] += len(json_data) - len(compressed)
        
        await session.commit()
        
        return stats

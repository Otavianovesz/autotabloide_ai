"""
AutoTabloide AI - I/O Assíncrono
=================================
Conforme Auditoria Industrial: Async I/O para não bloquear UI.
Wrappers para operações de arquivo não-bloqueantes.
"""

from __future__ import annotations
import asyncio
import json
import shutil
from pathlib import Path
from typing import Optional, Union, Any
from concurrent.futures import ThreadPoolExecutor
import logging

logger = logging.getLogger("AutoTabloide.AsyncIO")

# Pool de threads para operações de I/O
_executor: Optional[ThreadPoolExecutor] = None


def get_executor() -> ThreadPoolExecutor:
    """Obtém pool de threads para I/O."""
    global _executor
    if _executor is None:
        _executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="AsyncIO")
    return _executor


def shutdown_executor() -> None:
    """Encerra pool de threads."""
    global _executor
    if _executor:
        _executor.shutdown(wait=False)
        _executor = None


# ==============================================================================
# OPERAÇÕES DE ARQUIVO ASSÍNCRONAS
# ==============================================================================

async def read_text(path: Union[str, Path], encoding: str = 'utf-8') -> str:
    """
    Lê arquivo de texto de forma assíncrona.
    
    Args:
        path: Caminho do arquivo
        encoding: Encoding do arquivo
        
    Returns:
        Conteúdo do arquivo como string
    """
    loop = asyncio.get_event_loop()
    
    def _read():
        with open(path, 'r', encoding=encoding) as f:
            return f.read()
    
    return await loop.run_in_executor(get_executor(), _read)


async def write_text(
    path: Union[str, Path], 
    content: str, 
    encoding: str = 'utf-8'
) -> None:
    """
    Escreve texto em arquivo de forma assíncrona.
    
    Args:
        path: Caminho do arquivo
        content: Conteúdo a escrever
        encoding: Encoding do arquivo
    """
    loop = asyncio.get_event_loop()
    
    def _write():
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with open(path, 'w', encoding=encoding) as f:
            f.write(content)
    
    await loop.run_in_executor(get_executor(), _write)


async def read_bytes(path: Union[str, Path]) -> bytes:
    """
    Lê arquivo binário de forma assíncrona.
    
    Args:
        path: Caminho do arquivo
        
    Returns:
        Conteúdo do arquivo como bytes
    """
    loop = asyncio.get_event_loop()
    
    def _read():
        with open(path, 'rb') as f:
            return f.read()
    
    return await loop.run_in_executor(get_executor(), _read)


async def write_bytes(path: Union[str, Path], content: bytes) -> None:
    """
    Escreve bytes em arquivo de forma assíncrona.
    
    Args:
        path: Caminho do arquivo
        content: Bytes a escrever
    """
    loop = asyncio.get_event_loop()
    
    def _write():
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with open(path, 'wb') as f:
            f.write(content)
    
    await loop.run_in_executor(get_executor(), _write)


async def read_json(path: Union[str, Path]) -> Any:
    """
    Lê arquivo JSON de forma assíncrona.
    
    Args:
        path: Caminho do arquivo
        
    Returns:
        Dados parseados
    """
    content = await read_text(path)
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(get_executor(), json.loads, content)


async def write_json(
    path: Union[str, Path], 
    data: Any, 
    indent: int = 2,
    ensure_ascii: bool = False
) -> None:
    """
    Escreve dados em arquivo JSON de forma assíncrona.
    
    Args:
        path: Caminho do arquivo
        data: Dados a serializar
        indent: Indentação do JSON
        ensure_ascii: Se False, permite caracteres unicode
    """
    loop = asyncio.get_event_loop()
    
    def _serialize():
        return json.dumps(data, indent=indent, ensure_ascii=ensure_ascii)
    
    content = await loop.run_in_executor(get_executor(), _serialize)
    await write_text(path, content)


# ==============================================================================
# OPERAÇÕES DE SISTEMA DE ARQUIVOS
# ==============================================================================

async def copy_file(src: Union[str, Path], dst: Union[str, Path]) -> None:
    """
    Copia arquivo de forma assíncrona.
    
    Args:
        src: Arquivo fonte
        dst: Destino
    """
    loop = asyncio.get_event_loop()
    
    def _copy():
        Path(dst).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
    
    await loop.run_in_executor(get_executor(), _copy)


async def move_file(src: Union[str, Path], dst: Union[str, Path]) -> None:
    """
    Move arquivo de forma assíncrona.
    
    Args:
        src: Arquivo fonte
        dst: Destino
    """
    loop = asyncio.get_event_loop()
    
    def _move():
        Path(dst).parent.mkdir(parents=True, exist_ok=True)
        shutil.move(src, dst)
    
    await loop.run_in_executor(get_executor(), _move)


async def delete_file(path: Union[str, Path]) -> bool:
    """
    Deleta arquivo de forma assíncrona.
    
    Args:
        path: Caminho do arquivo
        
    Returns:
        True se deletou, False se não existia
    """
    loop = asyncio.get_event_loop()
    
    def _delete():
        p = Path(path)
        if p.exists():
            p.unlink()
            return True
        return False
    
    return await loop.run_in_executor(get_executor(), _delete)


async def file_exists(path: Union[str, Path]) -> bool:
    """
    Verifica se arquivo existe de forma assíncrona.
    
    Args:
        path: Caminho do arquivo
        
    Returns:
        True se arquivo existe
    """
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(
        get_executor(), 
        lambda: Path(path).exists()
    )


async def list_files(
    directory: Union[str, Path], 
    pattern: str = "*"
) -> list[Path]:
    """
    Lista arquivos em diretório de forma assíncrona.
    
    Args:
        directory: Diretório a listar
        pattern: Padrão glob (ex: "*.pdf")
        
    Returns:
        Lista de caminhos
    """
    loop = asyncio.get_event_loop()
    
    def _list():
        return list(Path(directory).glob(pattern))
    
    return await loop.run_in_executor(get_executor(), _list)


async def get_file_size(path: Union[str, Path]) -> int:
    """
    Obtém tamanho do arquivo de forma assíncrona.
    
    Args:
        path: Caminho do arquivo
        
    Returns:
        Tamanho em bytes
    """
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(
        get_executor(),
        lambda: Path(path).stat().st_size
    )


# ==============================================================================
# CONTEXT MANAGERS ASSÍNCRONOS
# ==============================================================================

class AsyncFileReader:
    """
    Context manager para leitura de arquivo assíncrona.
    
    Uso:
        async with AsyncFileReader("file.txt") as content:
            print(content)
    """
    
    def __init__(self, path: Union[str, Path], mode: str = 'text'):
        self.path = path
        self.mode = mode
        self._content: Optional[Union[str, bytes]] = None
    
    async def __aenter__(self) -> Union[str, bytes]:
        if self.mode == 'text':
            self._content = await read_text(self.path)
        else:
            self._content = await read_bytes(self.path)
        return self._content
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self._content = None
        return False


class AsyncFileWriter:
    """
    Context manager para escrita de arquivo assíncrona.
    
    Uso:
        async with AsyncFileWriter("file.txt") as writer:
            await writer.write("content")
    """
    
    def __init__(self, path: Union[str, Path], mode: str = 'text'):
        self.path = path
        self.mode = mode
        self._buffer: list = []
    
    async def __aenter__(self) -> 'AsyncFileWriter':
        return self
    
    async def write(self, content: Union[str, bytes]) -> None:
        self._buffer.append(content)
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None and self._buffer:
            if self.mode == 'text':
                content = ''.join(self._buffer)
                await write_text(self.path, content)
            else:
                content = b''.join(self._buffer)
                await write_bytes(self.path, content)
        self._buffer.clear()
        return False

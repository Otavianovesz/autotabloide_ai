"""
AutoTabloide AI - Resilience Module
=====================================
Robustez industrial para sobrevivência no mundo real.
PROTOCOLO DE RETIFICAÇÃO: Passos 91-100 (Resiliência e Deploy).

Este módulo contém:
- Passo 2: Isolamento do Ghostscript em /bin/
- Passo 8: Verificação de DLLs Cairo
- Passo 93: Caminhos relativos no banco
- Passo 97: Tratamento de exceções SSL
- Passo 98: Encoding utf-8-sig para CSV/Excel
- Passo 25: Schema versioning básico
"""

import os
import sys
import ssl
import logging
import subprocess
from pathlib import Path
from typing import Optional, Tuple, List, Dict, Any
from contextlib import contextmanager

logger = logging.getLogger("Resilience")


# ==============================================================================
# PASSO 2: ISOLAMENTO DO GHOSTSCRIPT
# ==============================================================================

class GhostscriptIsolator:
    """
    Garante que Ghostscript seja executado do diretório /bin/ local.
    
    PROBLEMA: Se GS do sistema estiver no PATH, pode usar versão errada.
    
    SOLUÇÃO: Sempre usar caminho absoluto e verificar versão.
    """
    
    REQUIRED_VERSION = (9, 50)  # Mínimo 9.50
    
    @classmethod
    def find_local_gs(cls, system_root: Path) -> Optional[Path]:
        """
        Encontra Ghostscript local no diretório bin.
        
        Args:
            system_root: Raiz do sistema
            
        Returns:
            Caminho do executável ou None
        """
        candidates = [
            system_root / "bin" / "gs" / "gswin64c.exe",
            system_root / "bin" / "gs" / "gswin32c.exe",
            system_root / "bin" / "gswin64c.exe",
            system_root / "bin" / "gs" / "bin" / "gswin64c.exe",
        ]
        
        for candidate in candidates:
            if candidate.exists():
                return candidate
        
        return None
    
    @classmethod
    def get_version(cls, gs_path: Path) -> Optional[Tuple[int, int]]:
        """
        Obtém versão do Ghostscript.
        
        Returns:
            Tuple (major, minor) ou None se falhar
        """
        try:
            result = subprocess.run(
                [str(gs_path), "--version"],
                capture_output=True,
                timeout=5
            )
            
            if result.returncode == 0:
                version_str = result.stdout.decode().strip()
                parts = version_str.split('.')
                return (int(parts[0]), int(parts[1]))
                
        except Exception as e:
            logger.debug(f"Não foi possível obter versão do GS: {e}")
        
        return None
    
    @classmethod
    def verify_local_gs(cls, system_root: Path) -> Tuple[bool, str, Optional[Path]]:
        """
        Verifica se GS local está disponível e é versão correta.
        
        Returns:
            Tuple (ok, mensagem, caminho)
        """
        gs_path = cls.find_local_gs(system_root)
        
        if gs_path is None:
            return False, "Ghostscript não encontrado em /bin/", None
        
        version = cls.get_version(gs_path)
        
        if version is None:
            return False, f"Não foi possível verificar versão: {gs_path}", gs_path
        
        if version < cls.REQUIRED_VERSION:
            return (
                False,
                f"Versão {version[0]}.{version[1]} muito antiga. Necessário: {cls.REQUIRED_VERSION[0]}.{cls.REQUIRED_VERSION[1]}+",
                gs_path
            )
        
        return True, f"Ghostscript {version[0]}.{version[1]} encontrado", gs_path
    
    @classmethod
    def get_gs_command(cls, system_root: Path) -> List[str]:
        """
        Retorna comando base para Ghostscript com caminho absoluto.
        
        Usar isso em vez de apenas 'gswin64c' para garantir isolamento.
        """
        gs_path = cls.find_local_gs(system_root)
        
        if gs_path:
            return [str(gs_path)]
        
        # Fallback para PATH (não recomendado)
        logger.warning("Usando Ghostscript do PATH - não isolado!")
        return ["gswin64c"]


# ==============================================================================
# PASSO 8: VERIFICAÇÃO DE DLLs CAIRO
# ==============================================================================

class CairoDLLChecker:
    """
    Verifica se DLLs do Cairo estão carregando do local correto.
    
    PROBLEMA: DLLs do sistema (System32) podem conflitar com as locais.
    """
    
    REQUIRED_DLLS = [
        "libcairo-2.dll",
        "libpixman-1-0.dll",
        "libpng16-16.dll",
        "zlib1.dll",
    ]
    
    @classmethod
    def check_dlls(cls, bin_dir: Path) -> Dict[str, Dict[str, Any]]:
        """
        Verifica estado das DLLs Cairo.
        
        Returns:
            Dict com status de cada DLL
        """
        results = {}
        
        for dll_name in cls.REQUIRED_DLLS:
            dll_path = bin_dir / dll_name
            
            results[dll_name] = {
                "exists_local": dll_path.exists(),
                "local_path": str(dll_path) if dll_path.exists() else None,
                "system_conflict": cls._check_system_conflict(dll_name),
            }
        
        return results
    
    @classmethod
    def _check_system_conflict(cls, dll_name: str) -> bool:
        """Verifica se existe DLL conflitante no System32."""
        if sys.platform != "win32":
            return False
        
        system32 = Path(os.environ.get("SYSTEMROOT", "C:\\Windows")) / "System32"
        return (system32 / dll_name).exists()
    
    @classmethod
    def all_dlls_present(cls, bin_dir: Path) -> Tuple[bool, List[str]]:
        """
        Verifica se todas as DLLs necessárias estão presentes.
        
        Returns:
            Tuple (todas_presentes, lista_faltantes)
        """
        status = cls.check_dlls(bin_dir)
        missing = [name for name, info in status.items() if not info["exists_local"]]
        
        return len(missing) == 0, missing


# ==============================================================================
# PASSO 93: CAMINHOS RELATIVOS NO BANCO
# ==============================================================================

class RelativePathManager:
    r"""
    Garante que caminhos no banco sejam relativos, não absolutos.
    
    PROBLEMA: Se o projeto for movido de C:\Users\Otaviano para D:\Projetos,
    todos os caminhos absolutos quebram.
    
    SOLUÇÃO: Sempre armazenar caminhos relativos à raiz do sistema.
    """
    
    @classmethod
    def to_relative(cls, absolute_path: str, system_root: Path) -> str:
        """
        Converte caminho absoluto para relativo.
        
        Args:
            absolute_path: Caminho absoluto
            system_root: Raiz do sistema
            
        Returns:
            Caminho relativo (ou original se não for subpath)
        """
        try:
            path = Path(absolute_path)
            return str(path.relative_to(system_root))
        except ValueError:
            # Não é subpath - retorna original
            logger.warning(f"Caminho não é relativo à raiz: {absolute_path}")
            return absolute_path
    
    @classmethod
    def to_absolute(cls, relative_path: str, system_root: Path) -> str:
        """
        Converte caminho relativo para absoluto.
        
        Args:
            relative_path: Caminho relativo
            system_root: Raiz do sistema
            
        Returns:
            Caminho absoluto
        """
        # Se já é absoluto, retorna
        if Path(relative_path).is_absolute():
            return relative_path
        
        return str(system_root / relative_path)
    
    @classmethod
    def is_relative(cls, path: str) -> bool:
        """Verifica se caminho é relativo."""
        return not Path(path).is_absolute()
    
    @classmethod
    def validate_stored_path(cls, stored_path: str) -> Tuple[bool, str]:
        """
        Valida se caminho armazenado está no formato correto.
        
        Returns:
            Tuple (é_válido, mensagem)
        """
        if not stored_path:
            return True, "Caminho vazio"
        
        # Detectar sinais de caminho absoluto do Windows
        if len(stored_path) >= 2 and stored_path[1] == ':':
            return False, "Caminho absoluto Windows detectado"
        
        if stored_path.startswith('/') and not stored_path.startswith('./'):
            return False, "Caminho absoluto Unix detectado"
        
        if stored_path.startswith('C:\\') or stored_path.startswith('D:\\'):
            return False, "Caminho absoluto com drive letter"
        
        return True, "Caminho relativo válido"


# ==============================================================================
# PASSO 97: TRATAMENTO DE EXCEÇÕES SSL
# ==============================================================================

class SSLErrorHandler:
    """
    Trata erros de SSL comuns (data/hora errada no PC do cliente).
    
    PROBLEMA: SSLCertVerificationError quando relógio do sistema está errado.
    """
    
    @classmethod
    def create_tolerant_session(cls):
        """
        Cria sessão requests com SSL tolerante para diagnóstico.
        
        ATENÇÃO: Usar apenas para diagnóstico, não em produção!
        """
        import requests
        from requests.adapters import HTTPAdapter
        from urllib3.util.ssl_ import create_urllib3_context
        
        class TolerantAdapter(HTTPAdapter):
            def init_poolmanager(self, *args, **kwargs):
                ctx = create_urllib3_context()
                ctx.check_hostname = False
                ctx.verify_mode = ssl.CERT_NONE
                kwargs['ssl_context'] = ctx
                return super().init_poolmanager(*args, **kwargs)
        
        session = requests.Session()
        session.mount('https://', TolerantAdapter())
        
        return session
    
    @classmethod
    def check_system_time(cls) -> Tuple[bool, str]:
        """
        Verifica se hora do sistema está correta.
        
        Compara com servidor NTP para detectar discrepância.
        
        Returns:
            Tuple (hora_correta, mensagem)
        """
        import socket
        import struct
        from datetime import datetime
        
        try:
            # Servidor NTP público
            ntp_server = "pool.ntp.org"
            
            client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            client.settimeout(3)
            
            # Pacote NTP
            data = b'\x1b' + 47 * b'\0'
            client.sendto(data, (ntp_server, 123))
            
            data, _ = client.recvfrom(1024)
            
            if data:
                # Extrair timestamp
                t = struct.unpack('!12I', data)[10]
                t -= 2208988800  # Época NTP -> Unix
                
                ntp_time = datetime.fromtimestamp(t)
                local_time = datetime.now()
                
                diff = abs((ntp_time - local_time).total_seconds())
                
                if diff > 60:
                    return False, f"Relógio do sistema está {diff:.0f}s fora de sincronia!"
                
                return True, "Hora do sistema está correta"
            
        except Exception as e:
            return True, f"Não foi possível verificar (sem internet?): {e}"
        
        finally:
            client.close()
    
    @classmethod
    @contextmanager
    def handle_ssl_errors(cls):
        """
        Context manager que trata erros SSL com mensagem amigável.
        
        Uso:
            with SSLErrorHandler.handle_ssl_errors():
                requests.get("https://...")
        """
        try:
            yield
        except ssl.SSLCertVerificationError as e:
            time_ok, time_msg = cls.check_system_time()
            
            if not time_ok:
                raise ConnectionError(
                    f"Erro de SSL devido ao relógio do sistema incorreto. {time_msg}"
                ) from e
            else:
                raise ConnectionError(
                    "Erro de certificado SSL. O site pode ter certificado inválido."
                ) from e


# ==============================================================================
# PASSO 98: ENCODING UTF-8-SIG PARA CSV/EXCEL
# ==============================================================================

class EncodingHandler:
    """
    Garante encoding correto para arquivos CSV do Excel brasileiro.
    
    PROBLEMA: Excel salva CSV em UTF-8 com BOM ou latin1.
    """
    
    ENCODINGS_TO_TRY = [
        'utf-8-sig',   # UTF-8 com BOM (Excel)
        'utf-8',       # UTF-8 puro
        'latin1',      # ISO-8859-1 (Windows legacy)
        'cp1252',      # Windows CodePage 1252
    ]
    
    @classmethod
    def read_with_fallback(cls, file_path: Path) -> Tuple[str, str]:
        """
        Lê arquivo tentando múltiplos encodings.
        
        Args:
            file_path: Caminho do arquivo
            
        Returns:
            Tuple (conteúdo, encoding_usado)
        """
        for encoding in cls.ENCODINGS_TO_TRY:
            try:
                with open(file_path, 'r', encoding=encoding) as f:
                    content = f.read()
                return content, encoding
            except UnicodeDecodeError:
                continue
        
        # Último recurso: ignorar erros
        with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
            return f.read(), 'utf-8 (com erros)'
    
    @classmethod
    def detect_encoding(cls, file_path: Path) -> str:
        """
        Detecta encoding de um arquivo.
        
        Returns:
            Nome do encoding detectado
        """
        try:
            # Tenta chardet se disponível
            import chardet
            
            with open(file_path, 'rb') as f:
                raw = f.read(10000)
            
            result = chardet.detect(raw)
            return result.get('encoding', 'utf-8')
            
        except ImportError:
            # Sem chardet, usa heurística simples
            with open(file_path, 'rb') as f:
                raw = f.read(3)
            
            # Verifica BOM
            if raw.startswith(b'\xef\xbb\xbf'):
                return 'utf-8-sig'
            elif raw.startswith(b'\xff\xfe'):
                return 'utf-16-le'
            elif raw.startswith(b'\xfe\xff'):
                return 'utf-16-be'
            
            return 'utf-8'
    
    @classmethod
    def write_for_excel(cls, file_path: Path, content: str) -> None:
        """
        Escreve arquivo CSV compatível com Excel brasileiro.
        
        Usa UTF-8 com BOM para que Excel reconheça acentos.
        """
        with open(file_path, 'w', encoding='utf-8-sig', newline='') as f:
            f.write(content)


# ==============================================================================
# PASSO 25: SCHEMA VERSIONING BÁSICO
# ==============================================================================

class SchemaVersionManager:
    """
    Gerencia versão do schema do banco de dados.
    
    PROBLEMA: Código v2.0 pode não funcionar com banco v1.0.
    
    SOLUÇÃO: Tabela de versão + migrações automáticas.
    """
    
    CURRENT_VERSION = 1  # Versão atual do schema
    
    @classmethod
    async def get_schema_version(cls, session) -> int:
        """Retorna versão atual do schema no banco."""
        from sqlalchemy import text
        
        try:
            # Verifica se tabela existe
            result = await session.execute(text(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='schema_version'"
            ))
            
            if not result.scalar():
                return 0  # Banco antigo sem versionamento
            
            result = await session.execute(text(
                "SELECT version FROM schema_version ORDER BY applied_at DESC LIMIT 1"
            ))
            
            version = result.scalar()
            return version or 0
            
        except Exception:
            return 0
    
    @classmethod
    async def create_version_table(cls, session) -> None:
        """Cria tabela de controle de versão."""
        from sqlalchemy import text
        
        await session.execute(text("""
            CREATE TABLE IF NOT EXISTS schema_version (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                version INTEGER NOT NULL,
                description TEXT,
                applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))
        await session.commit()
    
    @classmethod
    async def set_version(cls, session, version: int, description: str = "") -> None:
        """Registra nova versão do schema."""
        from sqlalchemy import text
        
        await session.execute(text(
            "INSERT INTO schema_version (version, description) VALUES (:v, :d)"
        ), {"v": version, "d": description})
        await session.commit()
    
    @classmethod
    async def check_and_migrate(cls, session) -> Tuple[bool, str]:
        """
        Verifica versão e aplica migrações se necessário.
        
        Returns:
            Tuple (sucesso, mensagem)
        """
        current = await cls.get_schema_version(session)
        
        if current == 0:
            # Primeiro uso ou banco antigo
            await cls.create_version_table(session)
            await cls.set_version(session, cls.CURRENT_VERSION, "Inicialização")
            return True, "Schema versionado inicializado"
        
        if current == cls.CURRENT_VERSION:
            return True, f"Schema v{current} está atualizado"
        
        if current < cls.CURRENT_VERSION:
            # Precisa migração
            # TODO: Implementar migrações específicas
            logger.warning(f"Migração necessária: v{current} -> v{cls.CURRENT_VERSION}")
            return False, f"Migração de v{current} para v{cls.CURRENT_VERSION} não implementada"
        
        if current > cls.CURRENT_VERSION:
            return False, f"Banco v{current} é mais novo que código v{cls.CURRENT_VERSION}!"


# ==============================================================================
# FUNÇÃO DE INICIALIZAÇÃO
# ==============================================================================

def initialize_resilience(system_root: Path) -> dict:
    """
    Inicializa proteções de resiliência.
    
    Args:
        system_root: Diretório raiz do sistema
        
    Returns:
        Dict com status
    """
    results = {}
    
    # Verificar GS
    gs_ok, gs_msg, gs_path = GhostscriptIsolator.verify_local_gs(system_root)
    results["ghostscript"] = {
        "ok": gs_ok,
        "message": gs_msg,
        "path": str(gs_path) if gs_path else None
    }
    
    # Verificar DLLs Cairo
    bin_dir = system_root / "bin"
    dlls_ok, missing_dlls = CairoDLLChecker.all_dlls_present(bin_dir)
    results["cairo_dlls"] = {
        "ok": dlls_ok,
        "missing": missing_dlls
    }
    
    # Verificar relógio
    time_ok, time_msg = SSLErrorHandler.check_system_time()
    results["system_time"] = {
        "ok": time_ok,
        "message": time_msg
    }
    
    logger.info("Resilience module inicializado")
    return results

"""
AutoTabloide AI - Boot Safety Module
=====================================
Implementações de segurança para inicialização robusta.
PROTOCOLO DE RETIFICAÇÃO: Passos 1-15 (Fundação e Governança).

Este módulo contém:
- Passo 1: Validação de permissões de escrita
- Passo 5: Limpeza seletiva de temp_render (arquivos > 24h)
- Passo 6: Proteção de settings.json (Last Known Good Config)
- Passo 7: Log Rotation verificação (delega para logging_config)
- Passo 10: Validação de fontes no boot
- Passo 12: Detecção e correção de posição de janela
- Passo 14: Prevenção de Sleep durante jobs
- Passo 15: Crash Dumps com sys.excepthook
"""

import os
import sys
import json
import shutil
import traceback
import ctypes
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Tuple, List, Dict
from contextlib import contextmanager

logger = logging.getLogger("BootSafety")


# ==============================================================================
# PASSO 1: VALIDAÇÃO DE PERMISSÕES DE ESCRITA
# ==============================================================================

class WritePermissionValidator:
    """
    Testa permissões de escrita em diretórios críticos.
    
    PROBLEMA: Se o programa rodar em "Arquivos de Programas" sem admin,
    ele falhará silenciosamente ao tentar escrever logs ou dados.
    
    SOLUÇÃO: Testar escrita de arquivo dummy na inicialização.
    """
    
    CRITICAL_DIRS = [
        "logs",
        "database",
        "assets/store",
        "staging/downloads",
        "temp_render",
    ]
    
    @classmethod
    def validate_all(cls, system_root: Path) -> Tuple[bool, List[str]]:
        """
        Valida permissões de escrita em todos os diretórios críticos.
        
        Args:
            system_root: Caminho raiz do sistema
            
        Returns:
            Tuple (sucesso_global, lista_de_erros)
        """
        errors = []
        
        for rel_dir in cls.CRITICAL_DIRS:
            dir_path = system_root / rel_dir
            success, error = cls.test_write_permission(dir_path)
            
            if not success:
                errors.append(f"{rel_dir}: {error}")
        
        return len(errors) == 0, errors
    
    @classmethod
    def test_write_permission(cls, dir_path: Path) -> Tuple[bool, Optional[str]]:
        """
        Testa permissão de escrita em um diretório específico.
        
        Returns:
            Tuple (sucesso, mensagem_erro_se_falhou)
        """
        try:
            # Criar diretório se não existir
            dir_path.mkdir(parents=True, exist_ok=True)
            
            # Tentar criar arquivo dummy
            test_file = dir_path / ".write_test.tmp"
            
            with open(test_file, 'w') as f:
                f.write("AutoTabloide AI - Write Permission Test")
            
            # Verificar leitura
            with open(test_file, 'r') as f:
                content = f.read()
            
            # Limpar arquivo de teste
            test_file.unlink()
            
            return True, None
            
        except PermissionError:
            return False, "Permissão negada (execute como Administrador ou mova para pasta acessível)"
        except OSError as e:
            return False, f"Erro de sistema: {e}"
        except Exception as e:
            return False, f"Erro inesperado: {e}"


# ==============================================================================
# PASSO 5: LIMPEZA SELETIVA DE TEMP_RENDER
# ==============================================================================

class SelectiveTempCleaner:
    """
    Limpeza seletiva de arquivos temporários.
    
    PROBLEMA: shutil.rmtree é agressivo e pode falhar se houver locks.
    
    SOLUÇÃO: Limpeza seletiva (arquivos > 24h) com tratamento de erros.
    """
    
    DEFAULT_MAX_AGE_HOURS = 24
    
    @classmethod
    def clean_temp_render(
        cls,
        temp_dir: Path,
        max_age_hours: int = DEFAULT_MAX_AGE_HOURS,
        extensions: Optional[List[str]] = None
    ) -> Dict[str, int]:
        """
        Remove arquivos antigos do temp_render.
        
        Args:
            temp_dir: Diretório de arquivos temporários
            max_age_hours: Idade máxima em horas
            extensions: Lista de extensões a limpar (None = todas)
            
        Returns:
            Dict com estatísticas de limpeza
        """
        stats = {
            "removed": 0,
            "skipped": 0,
            "locked": 0,
            "errors": 0,
        }
        
        if not temp_dir.exists():
            temp_dir.mkdir(parents=True, exist_ok=True)
            return stats
        
        cutoff = datetime.now() - timedelta(hours=max_age_hours)
        
        for file_path in temp_dir.iterdir():
            try:
                if file_path.is_dir():
                    # Recursão para subdiretórios
                    sub_stats = cls.clean_temp_render(file_path, max_age_hours, extensions)
                    for key, value in sub_stats.items():
                        stats[key] += value
                    
                    # Remove diretório vazio
                    try:
                        if not any(file_path.iterdir()):
                            file_path.rmdir()
                    except Exception:
                        pass
                    continue
                
                # Verificar extensão
                if extensions and file_path.suffix.lower() not in extensions:
                    stats["skipped"] += 1
                    continue
                
                # Verificar idade
                mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
                if mtime >= cutoff:
                    stats["skipped"] += 1
                    continue
                
                # Tentar remover
                file_path.unlink()
                stats["removed"] += 1
                
            except PermissionError:
                stats["locked"] += 1
            except Exception as e:
                stats["errors"] += 1
                logger.debug(f"Erro ao limpar {file_path}: {e}")
        
        return stats


# ==============================================================================
# PASSO 6: PROTEÇÃO DE SETTINGS.JSON (LAST KNOWN GOOD CONFIG)
# ==============================================================================

class ConfigProtector:
    """
    Sistema de backup automático de configurações.
    
    PROBLEMA: Se o JSON corromper (ex: desligamento súbito), o app não abre.
    
    SOLUÇÃO: Manter cópia de segurança automática (Last Known Good Configuration).
    """
    
    CONFIG_FILENAME = "settings.json"
    BACKUP_FILENAME = "settings.json.bak"
    LAST_GOOD_FILENAME = "settings.json.lastgood"
    
    @classmethod
    def protect_config(cls, config_dir: Path) -> bool:
        """
        Protege arquivo de configuração com backup.
        
        Args:
            config_dir: Diretório de configurações
            
        Returns:
            True se arquivo está protegido/válido
        """
        config_file = config_dir / cls.CONFIG_FILENAME
        backup_file = config_dir / cls.BACKUP_FILENAME
        last_good_file = config_dir / cls.LAST_GOOD_FILENAME
        
        # Se config não existe, não há o que proteger
        if not config_file.exists():
            return True
        
        # Tentar ler config atual
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Config válido - fazer backup
            shutil.copy2(config_file, last_good_file)
            return True
            
        except json.JSONDecodeError:
            logger.warning("Config corrompido! Tentando restaurar backup...")
            return cls._restore_from_backup(config_file, backup_file, last_good_file)
        except Exception as e:
            logger.error(f"Erro ao proteger config: {e}")
            return False
    
    @classmethod
    def _restore_from_backup(
        cls,
        config_file: Path,
        backup_file: Path,
        last_good_file: Path
    ) -> bool:
        """Restaura config de backup se disponível."""
        # Tentar Last Known Good primeiro
        if last_good_file.exists():
            try:
                with open(last_good_file, 'r', encoding='utf-8') as f:
                    json.load(f)  # Validar JSON
                
                shutil.copy2(last_good_file, config_file)
                logger.info("Config restaurado de LastKnownGood")
                return True
            except Exception:
                pass
        
        # Tentar backup
        if backup_file.exists():
            try:
                with open(backup_file, 'r', encoding='utf-8') as f:
                    json.load(f)  # Validar JSON
                
                shutil.copy2(backup_file, config_file)
                logger.info("Config restaurado de backup")
                return True
            except Exception:
                pass
        
        # Nenhum backup válido - criar config padrão
        logger.warning("Nenhum backup válido. Criando config padrão...")
        default_config = cls._get_default_config()
        
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(default_config, f, indent=2, ensure_ascii=False)
        
        return True
    
    @classmethod
    def _get_default_config(cls) -> dict:
        """Retorna configuração padrão."""
        return {
            "version": "1.0.0",
            "theme": "dark",
            "window": {
                "x": 100,
                "y": 100,
                "width": 1400,
                "height": 900,
            },
            "render": {
                "dpi_web": 150,
                "dpi_print": 300,
                "bleed_mm": 3.0,
            },
            "ai": {
                "temperature": 0.0,
            },
            "_created": datetime.now().isoformat(),
        }
    
    @classmethod
    def save_with_backup(cls, config_dir: Path, config_data: dict) -> bool:
        """
        Salva configuração com backup automático.
        
        Args:
            config_dir: Diretório de configurações
            config_data: Dados a salvar
            
        Returns:
            True se salvo com sucesso
        """
        config_file = config_dir / cls.CONFIG_FILENAME
        backup_file = config_dir / cls.BACKUP_FILENAME
        
        try:
            # Backup do atual se existir
            if config_file.exists():
                shutil.copy2(config_file, backup_file)
            
            # Salvar atomicamente (escrever em tmp e renomear)
            temp_file = config_file.with_suffix('.tmp')
            
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=2, ensure_ascii=False)
            
            # Renomear atomicamente
            temp_file.replace(config_file)
            
            return True
            
        except Exception as e:
            logger.error(f"Erro ao salvar config: {e}")
            return False


# ==============================================================================
# PASSO 10: VALIDAÇÃO DE FONTES
# ==============================================================================

class FontValidator:
    """
    Valida fontes do sistema no boot.
    
    PROBLEMA: Fontes corrompidas podem causar crashes durante renderização.
    
    SOLUÇÃO: Tentar carregar cada fonte e listar quais estão válidas.
    """
    
    @classmethod
    def validate_fonts(cls, fonts_dir: Path) -> Tuple[List[str], List[str]]:
        """
        Valida todas as fontes em um diretório.
        
        Args:
            fonts_dir: Diretório de fontes
            
        Returns:
            Tuple (fontes_válidas, fontes_inválidas)
        """
        valid = []
        invalid = []
        
        if not fonts_dir.exists():
            return valid, invalid
        
        font_extensions = {'.ttf', '.otf', '.woff', '.woff2'}
        
        for font_file in fonts_dir.glob('**/*'):
            if font_file.suffix.lower() not in font_extensions:
                continue
            
            try:
                # Tentar ler header da fonte
                with open(font_file, 'rb') as f:
                    header = f.read(12)
                
                # Verificar assinatura básica
                # TTF/OTF: 0x00010000 ou 'true' ou 'OTTO' ou 'typ1'
                valid_headers = [
                    b'\x00\x01\x00\x00',  # TTF
                    b'true',              # OpenType
                    b'OTTO',              # CFF
                    b'typ1',              # Type 1
                    b'wOFF',              # WOFF
                    b'wOF2',              # WOFF2
                ]
                
                is_valid = any(header.startswith(h) for h in valid_headers)
                
                if is_valid:
                    valid.append(str(font_file))
                else:
                    invalid.append(str(font_file))
                    
            except Exception as e:
                invalid.append(f"{font_file}: {e}")
        
        return valid, invalid


# ==============================================================================
# PASSO 12: DETECÇÃO DE MONITOR E POSIÇÃO DE JANELA
# ==============================================================================

class WindowPositionGuard:
    """
    Garante que a janela não abra fora da tela.
    
    PROBLEMA: Se o monitor secundário for desconectado, a janela pode
    abrir em coordenadas fora do viewport visível.
    
    SOLUÇÃO: Verificar se coordenadas salvas estão dentro do viewport atual.
    """
    
    @classmethod
    def get_screen_bounds(cls) -> Tuple[int, int, int, int]:
        """
        Retorna bounds da tela principal.
        
        Returns:
            Tuple (x, y, width, height)
        """
        if sys.platform != "win32":
            return (0, 0, 1920, 1080)  # Default para não-Windows
        
        try:
            user32 = ctypes.windll.user32
            width = user32.GetSystemMetrics(0)   # SM_CXSCREEN
            height = user32.GetSystemMetrics(1)  # SM_CYSCREEN
            return (0, 0, width, height)
        except Exception:
            return (0, 0, 1920, 1080)
    
    @classmethod
    def validate_position(
        cls,
        x: int,
        y: int,
        width: int,
        height: int
    ) -> Tuple[int, int]:
        """
        Valida posição da janela, ajustando se necessário.
        
        Args:
            x, y: Posição salva
            width, height: Dimensões da janela
            
        Returns:
            Tuple (x_corrigido, y_corrigido)
        """
        screen_x, screen_y, screen_w, screen_h = cls.get_screen_bounds()
        
        # Margem mínima visível
        min_visible = 50
        
        # Verificar se janela está pelo menos parcialmente visível
        if x + width < min_visible or x > screen_w - min_visible:
            x = 100  # Reset para posição segura
            
        if y + height < min_visible or y > screen_h - min_visible:
            y = 100  # Reset para posição segura
        
        # Garantir que não excede limites
        x = max(0, min(x, screen_w - min_visible))
        y = max(0, min(y, screen_h - min_visible))
        
        return x, y


# ==============================================================================
# PASSO 14: PREVENÇÃO DE SLEEP DURANTE RENDERIZAÇÃO
# ==============================================================================

class SleepPreventer:
    """
    Impede que o Windows entre em suspensão durante jobs críticos.
    
    Usa SetThreadExecutionState para sinalizar atividade.
    """
    
    # Constantes do Windows
    ES_CONTINUOUS = 0x80000000
    ES_SYSTEM_REQUIRED = 0x00000001
    ES_DISPLAY_REQUIRED = 0x00000002
    ES_AWAYMODE_REQUIRED = 0x00000040
    
    _active = False
    
    @classmethod
    def prevent_sleep(cls) -> bool:
        """Impede suspensão do sistema."""
        if sys.platform != "win32":
            return True
        
        try:
            ctypes.windll.kernel32.SetThreadExecutionState(
                cls.ES_CONTINUOUS | cls.ES_SYSTEM_REQUIRED | cls.ES_DISPLAY_REQUIRED
            )
            cls._active = True
            logger.debug("Sleep prevention ativado")
            return True
        except Exception as e:
            logger.warning(f"Falha ao prevenir sleep: {e}")
            return False
    
    @classmethod
    def allow_sleep(cls) -> bool:
        """Permite suspensão do sistema novamente."""
        if sys.platform != "win32":
            return True
        
        try:
            ctypes.windll.kernel32.SetThreadExecutionState(cls.ES_CONTINUOUS)
            cls._active = False
            logger.debug("Sleep prevention desativado")
            return True
        except Exception as e:
            logger.warning(f"Falha ao restaurar sleep: {e}")
            return False
    
    @classmethod
    @contextmanager
    def prevent_during(cls):
        """Context manager para prevenir sleep durante uma operação."""
        cls.prevent_sleep()
        try:
            yield
        finally:
            cls.allow_sleep()


# ==============================================================================
# PASSO 15: CRASH DUMPS COM SYS.EXCEPTHOOK
# ==============================================================================

class CrashDumpHandler:
    """
    Captura e salva crashes não tratados para análise.
    
    Salva arquivo .dump com traceback completo e variáveis locais.
    """
    
    _dumps_dir: Optional[Path] = None
    _original_hook = None
    _installed = False
    
    @classmethod
    def install(cls, dumps_dir: Path) -> None:
        """
        Instala handler de crash dump.
        
        Args:
            dumps_dir: Diretório para salvar dumps
        """
        if cls._installed:
            return
        
        cls._dumps_dir = dumps_dir
        cls._dumps_dir.mkdir(parents=True, exist_ok=True)
        
        # Salvar hook original
        cls._original_hook = sys.excepthook
        
        # Instalar nosso hook
        sys.excepthook = cls._exception_handler
        cls._installed = True
        
        logger.debug("Crash dump handler instalado")
    
    @classmethod
    def _exception_handler(cls, exc_type, exc_value, exc_traceback):
        """Handler de exceção não tratada."""
        try:
            # Gerar nome do arquivo
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            dump_file = cls._dumps_dir / f"crash_{timestamp}.dump"
            
            # Coletar informações
            dump_content = [
                "=" * 80,
                f"AUTOTABLOIDE AI - CRASH DUMP",
                f"Timestamp: {datetime.now().isoformat()}",
                f"Python: {sys.version}",
                f"Platform: {sys.platform}",
                "=" * 80,
                "",
                "=== EXCEPTION ===",
                f"Type: {exc_type.__name__}",
                f"Value: {exc_value}",
                "",
                "=== TRACEBACK ===",
            ]
            
            # Traceback formatado
            tb_lines = traceback.format_exception(exc_type, exc_value, exc_traceback)
            dump_content.extend(tb_lines)
            
            # Variáveis locais do frame onde ocorreu o erro
            dump_content.append("\n=== LOCAL VARIABLES ===")
            if exc_traceback:
                frame = exc_traceback.tb_frame
                while frame.f_back:
                    frame = frame.f_back
                
                for key, value in frame.f_locals.items():
                    try:
                        dump_content.append(f"  {key} = {repr(value)[:200]}")
                    except Exception:
                        dump_content.append(f"  {key} = <unrepresentable>")
            
            # Salvar dump
            with open(dump_file, 'w', encoding='utf-8') as f:
                f.write('\n'.join(dump_content))
            
            logger.critical(f"Crash dump salvo: {dump_file}")
            
        except Exception as e:
            logger.error(f"Falha ao salvar crash dump: {e}")
        
        # Chamar hook original
        if cls._original_hook:
            cls._original_hook(exc_type, exc_value, exc_traceback)


# ==============================================================================
# PASSO 94: MODO DE RECUPERAÇÃO (3 FALHAS = SAFE MODE)
# ==============================================================================

class BootFailureTracker:
    """
    Rastreia falhas de boot para oferecer modo de recuperação.
    
    Se o app falhar 3x seguidas no boot, oferece reset de configurações.
    """
    
    FAILURE_FILE = ".boot_failures"
    MAX_FAILURES = 3
    
    @classmethod
    def record_start(cls, config_dir: Path) -> int:
        """
        Registra início de boot e retorna contagem de falhas.
        
        Returns:
            Número de falhas consecutivas
        """
        failure_file = config_dir / cls.FAILURE_FILE
        
        try:
            if failure_file.exists():
                failures = int(failure_file.read_text())
            else:
                failures = 0
            
            # Incrementar (será resetado em record_success)
            failure_file.write_text(str(failures + 1))
            
            return failures
            
        except Exception:
            return 0
    
    @classmethod
    def record_success(cls, config_dir: Path) -> None:
        """Registra boot bem-sucedido (após UI iniciar)."""
        failure_file = config_dir / cls.FAILURE_FILE
        
        try:
            if failure_file.exists():
                failure_file.unlink()
        except Exception:
            pass
    
    @classmethod
    def should_offer_recovery(cls, config_dir: Path) -> bool:
        """Verifica se deve oferecer modo de recuperação."""
        failures = cls.record_start(config_dir)
        return failures >= cls.MAX_FAILURES


# ==============================================================================
# PASSO 96: GESTÃO DE ESPAÇO EM DISCO
# ==============================================================================

class DiskSpaceGuard:
    """
    Verifica espaço em disco antes de operações pesadas.
    """
    
    MIN_SPACE_RENDER_MB = 500  # Mínimo para renderização
    MIN_SPACE_CRITICAL_MB = 100  # Crítico - operações bloqueadas
    
    @classmethod
    def get_free_space_mb(cls, path: Path) -> float:
        """Retorna espaço livre em MB no drive do path."""
        try:
            if sys.platform == "win32":
                import ctypes
                free_bytes = ctypes.c_ulonglong(0)
                ctypes.windll.kernel32.GetDiskFreeSpaceExW(
                    str(path), None, None, ctypes.byref(free_bytes)
                )
                return free_bytes.value / (1024 * 1024)
            else:
                import shutil
                total, used, free = shutil.disk_usage(path)
                return free / (1024 * 1024)
        except Exception:
            return float('inf')  # Assume infinito se não puder verificar
    
    @classmethod
    def check_for_render(cls, path: Path) -> Tuple[bool, str]:
        """
        Verifica se há espaço suficiente para renderização.
        
        Returns:
            Tuple (pode_renderizar, mensagem)
        """
        free_mb = cls.get_free_space_mb(path)
        
        if free_mb < cls.MIN_SPACE_CRITICAL_MB:
            return False, f"CRÍTICO: Apenas {free_mb:.0f}MB livres. Libere espaço imediatamente!"
        elif free_mb < cls.MIN_SPACE_RENDER_MB:
            return False, f"Espaço insuficiente ({free_mb:.0f}MB). Necessário: {cls.MIN_SPACE_RENDER_MB}MB"
        else:
            return True, f"Espaço disponível: {free_mb:.0f}MB"


# ==============================================================================
# FUNÇÃO DE INICIALIZAÇÃO PRINCIPAL
# ==============================================================================

def initialize_boot_safety(system_root: Path) -> dict:
    """
    Inicializa todas as proteções de boot.
    
    Args:
        system_root: Diretório raiz do sistema
        
    Returns:
        Dict com status de cada proteção
    """
    results = {}
    
    # Passo 1: Validar permissões de escrita
    write_ok, write_errors = WritePermissionValidator.validate_all(system_root)
    results["write_permissions"] = {
        "success": write_ok,
        "errors": write_errors
    }
    if not write_ok:
        logger.error(f"Permissões de escrita falharam: {write_errors}")
    
    # Passo 5: Limpeza seletiva de temp_render
    temp_stats = SelectiveTempCleaner.clean_temp_render(system_root / "temp_render")
    results["temp_cleanup"] = temp_stats
    logger.info(f"Temp cleanup: {temp_stats['removed']} removidos, {temp_stats['locked']} bloqueados")
    
    # Passo 6: Proteção de config
    config_ok = ConfigProtector.protect_config(system_root)
    results["config_protection"] = config_ok
    
    # Passo 10: Validação de fontes
    fonts_dir = system_root / "library" / "fonts"
    valid_fonts, invalid_fonts = FontValidator.validate_fonts(fonts_dir)
    results["fonts"] = {
        "valid": len(valid_fonts),
        "invalid": len(invalid_fonts),
        "invalid_list": invalid_fonts[:5]  # Primeiras 5
    }
    if invalid_fonts:
        logger.warning(f"{len(invalid_fonts)} fontes inválidas detectadas")
    
    # Passo 15: Instalar crash dump handler
    CrashDumpHandler.install(system_root / "logs" / "crashes")
    results["crash_handler"] = True
    
    # Passo 94: Verificar falhas de boot
    if BootFailureTracker.should_offer_recovery(system_root):
        results["recovery_mode"] = True
        logger.warning("RECOVERY MODE: Múltiplas falhas de boot detectadas!")
    else:
        results["recovery_mode"] = False
    
    # Passo 96: Verificar espaço em disco
    disk_ok, disk_msg = DiskSpaceGuard.check_for_render(system_root)
    results["disk_space"] = {
        "ok": disk_ok,
        "message": disk_msg
    }
    if not disk_ok:
        logger.warning(disk_msg)
    
    logger.info("Boot safety inicializado com sucesso")
    return results


def mark_boot_success(system_root: Path) -> None:
    """
    Marca boot como bem-sucedido.
    Deve ser chamado após a UI iniciar sem erros.
    """
    BootFailureTracker.record_success(system_root)
    logger.debug("Boot marcado como sucesso")

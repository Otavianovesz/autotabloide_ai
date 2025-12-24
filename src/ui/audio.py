"""
AutoTabloide AI - Sistema de Feedback Sonoro
=============================================
Conforme Auditoria Industrial: Audio cues para UX.
Sons de sucesso, erro, notificação.
"""

from __future__ import annotations
import os
from pathlib import Path
from typing import Optional
import logging
import threading

logger = logging.getLogger("AutoTabloide.Audio")

# Tenta importar biblioteca de som
try:
    import winsound
    HAS_WINSOUND = True
except ImportError:
    HAS_WINSOUND = False

try:
    from playsound import playsound
    HAS_PLAYSOUND = True
except ImportError:
    HAS_PLAYSOUND = False


class SoundType:
    """Tipos de som disponíveis."""
    SUCCESS = "success"
    ERROR = "error"
    WARNING = "warning"
    NOTIFICATION = "notification"
    COMPLETE = "complete"
    CLICK = "click"


class AudioFeedback:
    """
    Sistema de feedback sonoro.
    
    Usa sons do sistema Windows ou arquivos .wav personalizados.
    Executa em thread separada para não bloquear UI.
    """
    
    # Mapeamento para sons do Windows
    SYSTEM_SOUNDS = {
        SoundType.SUCCESS: "SystemAsterisk",
        SoundType.ERROR: "SystemHand",
        SoundType.WARNING: "SystemExclamation",
        SoundType.NOTIFICATION: "SystemNotification",
        SoundType.COMPLETE: "SystemAsterisk",
        SoundType.CLICK: "SystemStart",
    }
    
    # Frequências para beeps (Hz, duração ms)
    BEEP_TONES = {
        SoundType.SUCCESS: (800, 150),
        SoundType.ERROR: (300, 300),
        SoundType.WARNING: (500, 200),
        SoundType.NOTIFICATION: (600, 100),
        SoundType.COMPLETE: (1000, 200),
        SoundType.CLICK: (1200, 50),
    }
    
    def __init__(self, assets_path: Optional[Path] = None, enabled: bool = True):
        """
        Args:
            assets_path: Caminho para pasta de sons personalizados
            enabled: Se o sistema de som está ativado
        """
        self.assets_path = assets_path
        self.enabled = enabled
        self._custom_sounds: dict[str, Path] = {}
        
        if assets_path:
            self._load_custom_sounds()
    
    def _load_custom_sounds(self) -> None:
        """Carrega sons personalizados da pasta de assets."""
        if not self.assets_path or not self.assets_path.exists():
            return
        
        for sound_file in self.assets_path.glob("*.wav"):
            sound_name = sound_file.stem.lower()
            self._custom_sounds[sound_name] = sound_file
            logger.debug(f"Som carregado: {sound_name}")
    
    def play(self, sound_type: str, async_play: bool = True) -> None:
        """
        Reproduz um som.
        
        Args:
            sound_type: Tipo do som (SoundType.*)
            async_play: Se True, reproduz em thread separada
        """
        if not self.enabled:
            return
        
        if async_play:
            thread = threading.Thread(target=self._play_sound, args=(sound_type,))
            thread.daemon = True
            thread.start()
        else:
            self._play_sound(sound_type)
    
    def _play_sound(self, sound_type: str) -> None:
        """Reproduz som (interno)."""
        # 1. Tenta som personalizado
        if sound_type in self._custom_sounds:
            self._play_file(self._custom_sounds[sound_type])
            return
        
        # 2. Tenta winsound (Windows)
        if HAS_WINSOUND:
            try:
                # Tenta som do sistema
                if sound_type in self.SYSTEM_SOUNDS:
                    winsound.PlaySound(
                        self.SYSTEM_SOUNDS[sound_type],
                        winsound.SND_ALIAS | winsound.SND_ASYNC
                    )
                    return
                
                # Fallback para beep
                if sound_type in self.BEEP_TONES:
                    freq, duration = self.BEEP_TONES[sound_type]
                    winsound.Beep(freq, duration)
                    return
            except Exception as e:
                logger.debug(f"winsound falhou: {e}")
        
        logger.debug(f"Som não reproduzido: {sound_type} (sem backend disponível)")
    
    def _play_file(self, file_path: Path) -> None:
        """Reproduz arquivo de som."""
        if HAS_PLAYSOUND:
            try:
                playsound(str(file_path), block=False)
            except Exception as e:
                logger.debug(f"playsound falhou: {e}")
        elif HAS_WINSOUND:
            try:
                winsound.PlaySound(str(file_path), winsound.SND_FILENAME | winsound.SND_ASYNC)
            except Exception as e:
                logger.debug(f"winsound falhou: {e}")
    
    # Atalhos convenientes
    def success(self) -> None:
        """Som de sucesso."""
        self.play(SoundType.SUCCESS)
    
    def error(self) -> None:
        """Som de erro."""
        self.play(SoundType.ERROR)
    
    def warning(self) -> None:
        """Som de aviso."""
        self.play(SoundType.WARNING)
    
    def notify(self) -> None:
        """Som de notificação."""
        self.play(SoundType.NOTIFICATION)
    
    def complete(self) -> None:
        """Som de conclusão."""
        self.play(SoundType.COMPLETE)
    
    def click(self) -> None:
        """Som de clique."""
        self.play(SoundType.CLICK)


# Instância global
_audio: Optional[AudioFeedback] = None


def get_audio() -> AudioFeedback:
    """Obtém instância global do sistema de áudio."""
    global _audio
    if _audio is None:
        _audio = AudioFeedback()
    return _audio


def init_audio(assets_path: Path, enabled: bool = True) -> AudioFeedback:
    """Inicializa sistema de áudio com assets."""
    global _audio
    _audio = AudioFeedback(assets_path, enabled)
    return _audio


# Atalhos globais
def play_success() -> None:
    get_audio().success()

def play_error() -> None:
    get_audio().error()

def play_warning() -> None:
    get_audio().warning()

def play_notify() -> None:
    get_audio().notify()

def play_complete() -> None:
    get_audio().complete()

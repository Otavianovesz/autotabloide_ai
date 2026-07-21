"""
Som do app (FASE 1, passo 74)
=============================
UM som: exportação concluída — .wav curto e discreto, gerado na bancada
(dois tons com decaimento). **Padrão: DESLIGADO** (Config ``aparencia.som``
= "ligado" liga). Toca via ``winsound`` (app é Windows por decisão), em
modo assíncrono — nunca trava a UI.
"""

from __future__ import annotations

from pathlib import Path

_WAV = Path(__file__).resolve().parents[2] / "assets" / "sons" / "exportou.wav"


def som_ligado() -> bool:
    try:
        from app.core.database import Database
        from app.core.repositories import ConfigRepositorio
        db = Database().init()
        try:
            with db.Session() as s:
                v = str(ConfigRepositorio(s).get("aparencia.som") or "")
        finally:
            db.engine.dispose()
        return v == "ligado"
    except Exception:
        return False                     # padrão são: silêncio


def tocar_exportou() -> None:
    """Toca o "pronto!" da exportação SE o dono ligou o som."""
    if not som_ligado():
        return
    try:
        import winsound
        winsound.PlaySound(str(_WAV),
                           winsound.SND_FILENAME | winsound.SND_ASYNC)
    except Exception as e:               # som falhou ≠ exportação falhou
        print(f"aviso: som de exportação não tocou ({e})")

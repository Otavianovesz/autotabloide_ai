"""Rascunho automático (R-061, Fase 6 — Bloco D).

Rede de segurança: um snapshot silencioso do projeto aberto, gravado a cada
~2 min. É **isolado** das versões manuais (F2) e do projeto salvo — mora numa
pasta própria `rascunhos/`, NUNCA em `projetos/<uuid>/` nem em `versoes/`, e
NÃO passa por `salvar_projeto` (que criaria versão e tocaria os bytes do salvo).
Portanto o rascunho é rede, não gravação por cima (respeita a lei da F2).

O estado é o mesmo conjunto que o salvar coleta: layout + itens + validade +
mapa + overrides (dados planos JSON). Rotação: guarda os últimos N (config).
"""

from __future__ import annotations

import json
import time
from pathlib import Path

from app.core.paths import SystemRoot

PADRAO_MAX = 5


def _dir() -> Path:
    d = SystemRoot().raiz / "rascunhos"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _max_rascunhos() -> int:
    """Quantos rascunhos guardar (config da F3; molde de `_max_versoes`)."""
    try:
        from app.core.database import Database
        from app.core.repositories import ConfigRepositorio
        db = Database().init()
        try:
            with db.Session() as s:
                return int(ConfigRepositorio(s).get("rascunhos.max") or PADRAO_MAX)
        finally:
            db.engine.dispose()
    except Exception:
        return PADRAO_MAX


def _lista() -> list[Path]:
    return sorted(_dir().glob("rascunho_*.json"))


def salvar_rascunho(estado: dict, *, ts: float | None = None,
                    max_manter: int | None = None) -> Path:
    """Grava um snapshot (isolado). Devolve o arquivo. Rotaciona para N."""
    d = dict(estado)
    d["_ts"] = float(ts if ts is not None else time.time())
    arq = _dir() / f"rascunho_{int(d['_ts'] * 1000)}.json"
    arq.write_text(json.dumps(d, ensure_ascii=False), encoding="utf-8")
    n = max_manter if max_manter is not None else _max_rascunhos()
    for velho in _lista()[:-max(1, n)]:
        velho.unlink(missing_ok=True)
    return arq


def carregar_rascunho() -> dict | None:
    """O rascunho mais recente (ou None)."""
    arqs = _lista()
    if not arqs:
        return None
    try:
        return json.loads(arqs[-1].read_text(encoding="utf-8"))
    except Exception:
        return None


def ha_rascunho() -> bool:
    return bool(_lista())


def descartar_rascunhos() -> None:
    """Some com todos os rascunhos (após recuperar ou salvar de verdade)."""
    for a in _lista():
        a.unlink(missing_ok=True)


def hora_do_rascunho(estado: dict) -> str:
    """HH:MM do snapshot (para o aviso 'Recuperar o rascunho de HH:MM?')."""
    ts = estado.get("_ts")
    if not ts:
        return "?"
    return time.strftime("%H:%M", time.localtime(ts))

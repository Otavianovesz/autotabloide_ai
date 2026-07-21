"""
Lixeira de 30 dias (FASE 2, Bloco G — R-008)
============================================
Excluir sem medo: TODA exclusão da UI vira soft-delete (`excluido_em`);
os arquivos ficam no lugar até a purga. Restaurar devolve INTEIRO
(projeto com versões, produto com fotos — as pastas nunca foram tocadas).
A purga roda no boot: >30 dias → apaga linha E arquivos, com log.
"""

from __future__ import annotations

import shutil
from datetime import datetime, timedelta
from pathlib import Path

from app.core.database import Database
from app.core.models import Layout, Produto, ProjetoSalvo

DIAS_LIXEIRA = 30
_MODELOS = {"projeto": ProjetoSalvo, "produto": Produto, "layout": Layout}


def _rotulo(tipo: str, row) -> str:
    if tipo == "produto":
        return row.nome_sanitizado
    return row.nome


def excluir_suave(tipo: str, item_id: int) -> None:
    """Passo 82: marca `excluido_em` — nada é apagado do disco agora."""
    modelo = _MODELOS[tipo]
    db = Database().init()
    try:
        with db.Session() as s:
            row = s.get(modelo, item_id)
            if row is not None:
                row.excluido_em = datetime.now()
                s.commit()
    finally:
        db.engine.dispose()


def restaurar(tipo: str, item_id: int) -> None:
    """Volta INTEIRO: a linha reaparece nas listas; os arquivos nunca
    saíram do lugar (passo 86)."""
    modelo = _MODELOS[tipo]
    db = Database().init()
    try:
        with db.Session() as s:
            row = s.get(modelo, item_id)
            if row is not None:
                row.excluido_em = None
                s.commit()
    finally:
        db.engine.dispose()


def listar_lixeira() -> list[dict]:
    """Itens na lixeira com tipo, nome, quando e dias restantes."""
    db = Database().init()
    try:
        with db.Session() as s:
            saida = []
            for tipo, modelo in _MODELOS.items():
                for row in s.query(modelo).filter(
                        modelo.excluido_em.isnot(None)).all():
                    quando = row.excluido_em
                    restantes = DIAS_LIXEIRA - (datetime.now() - quando).days
                    saida.append({
                        "tipo": tipo, "id": row.id,
                        "nome": _rotulo(tipo, row),
                        "quando": quando.strftime("%d/%m/%Y %H:%M"),
                        "dias_restantes": max(0, restantes),
                    })
            saida.sort(key=lambda d: d["dias_restantes"])
            return saida
    finally:
        db.engine.dispose()


def _apagar_arquivos(tipo: str, row) -> None:
    """A purga/exclusão definitiva leva os ARQUIVOS junto."""
    if tipo == "projeto":
        from app.core.projetos import _pasta
        shutil.rmtree(_pasta(row.uuid), ignore_errors=True)
    elif tipo == "produto":
        from app.core.paths import SystemRoot
        pasta = SystemRoot().biblioteca_imagens / str(row.id)
        shutil.rmtree(pasta, ignore_errors=True)
    elif tipo == "layout":
        from app.core.paths import SystemRoot
        from app.rendering.persistencia import resolver_arte
        arte = resolver_arte(row.arquivo_fundo)
        if arte and Path(arte).exists():
            raiz = SystemRoot().layouts
            try:                        # só apaga arte DENTRO da raiz (I3)
                Path(arte).resolve().relative_to(raiz.resolve())
                Path(arte).unlink(missing_ok=True)
            except ValueError:
                pass


def excluir_agora(tipo: str, item_id: int) -> None:
    """O 'Excluir agora' da tela — linha + arquivos, sem esperar 30 dias."""
    modelo = _MODELOS[tipo]
    db = Database().init()
    try:
        with db.Session() as s:
            row = s.get(modelo, item_id)
            if row is None:
                return
            _apagar_arquivos(tipo, row)
            s.delete(row)
            s.commit()
    finally:
        db.engine.dispose()


def purgar(agora: datetime | None = None) -> list[str]:
    """Passo 85: no boot, o que passou de 30 dias morre de verdade —
    linha E arquivos. Relógio INJETÁVEL (teste do passo 88). Devolve o
    log do que purgou (I2: nunca em silêncio)."""
    agora = agora or datetime.now()
    limite = agora - timedelta(days=DIAS_LIXEIRA)
    log: list[str] = []
    db = Database().init()
    try:
        with db.Session() as s:
            for tipo, modelo in _MODELOS.items():
                for row in s.query(modelo).filter(
                        modelo.excluido_em.isnot(None),
                        modelo.excluido_em < limite).all():
                    log.append(f"{tipo}: {_rotulo(tipo, row)} "
                               f"(excluído em {row.excluido_em:%d/%m/%Y})")
                    _apagar_arquivos(tipo, row)
                    s.delete(row)
            s.commit()
    finally:
        db.engine.dispose()
    for linha in log:
        print(f"lixeira: purgado {linha}")
    return log

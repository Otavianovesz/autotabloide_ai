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


def _retrato(row) -> dict:
    """F13/B9: os campos que a limpeza de ARQUIVOS usa, capturados ANTES
    do delete/commit (depois do commit a linha está morta e expirada)."""
    return {"id": row.id, "uuid": getattr(row, "uuid", None),
            "arquivo_fundo": getattr(row, "arquivo_fundo", None)}


def _apagar_arquivos(tipo: str, retrato: dict) -> None:
    """A purga/exclusão definitiva leva os ARQUIVOS junto.

    F13/B9: recebe o RETRATO (valores), nunca a linha viva — e roda SÓ
    depois do commit. Antes, os arquivos morriam primeiro e um commit
    recusado deixava o estado meio-morto (linha viva sem arquivos)."""
    if tipo == "projeto":
        from app.core.projetos import _pasta
        shutil.rmtree(_pasta(retrato["uuid"]), ignore_errors=True)
    elif tipo == "produto":
        from app.core.paths import SystemRoot
        pasta = SystemRoot().biblioteca_imagens / str(retrato["id"])
        shutil.rmtree(pasta, ignore_errors=True)
    elif tipo == "layout":
        from app.core.paths import SystemRoot
        from app.rendering.persistencia import resolver_arte
        arte = resolver_arte(retrato["arquivo_fundo"])
        if arte and Path(arte).exists():
            raiz = SystemRoot().layouts
            try:                        # só apaga arte DENTRO da raiz (I3)
                Path(arte).resolve().relative_to(raiz.resolve())
                Path(arte).unlink(missing_ok=True)
            except ValueError:
                pass


def excluir_agora(tipo: str, item_id: int) -> None:
    """O 'Excluir agora' da tela — linha + arquivos, sem esperar 30 dias.

    F13/B9: a LINHA morre primeiro (commit); os arquivos só depois — o
    banco recusar (FK vivo) não pode deixar arquivos apagados com a
    linha viva."""
    modelo = _MODELOS[tipo]
    db = Database().init()
    try:
        with db.Session() as s:
            row = s.get(modelo, item_id)
            if row is None:
                return
            retrato = _retrato(row)
            s.delete(row)
            s.commit()
        _apagar_arquivos(tipo, retrato)
    finally:
        db.engine.dispose()


def purgar(agora: datetime | None = None) -> list[str]:
    """Passo 85: no boot, o que passou de 30 dias morre de verdade —
    linha E arquivos. Relógio INJETÁVEL (teste do passo 88). Devolve o
    log do que purgou E do que ficou (I2: nunca em silêncio).

    F13/B9 (D-06): TRANSAÇÃO POR ITEM, linha antes dos arquivos. Um
    IntegrityError (ex.: layout na lixeira com projeto VIVO apontando —
    FK sem ondelete) pula SÓ aquele item, COM relato nominal. Antes,
    UM item travado abortava a purga INTEIRA, derrubava o boot
    (editor_app._completar) e os arquivos já tinham sido apagados."""
    from sqlalchemy.exc import SQLAlchemyError

    agora = agora or datetime.now()
    limite = agora - timedelta(days=DIAS_LIXEIRA)
    log: list[str] = []
    db = Database().init()
    try:
        with db.Session() as s:
            alvos = [(tipo, row.id, _rotulo(tipo, row), row.excluido_em,
                      _retrato(row))
                     for tipo, modelo in _MODELOS.items()
                     for row in s.query(modelo).filter(
                         modelo.excluido_em.isnot(None),
                         modelo.excluido_em < limite).all()]
        for tipo, rid, rotulo, quando, retrato in alvos:
            try:
                with db.Session() as s:
                    row = s.get(_MODELOS[tipo], rid)
                    if row is None:
                        continue
                    s.delete(row)
                    s.commit()
            except SQLAlchemyError:
                log.append(
                    f"{tipo}: {rotulo} FICOU na lixeira — o banco recusou "
                    "apagar (algo vivo ainda aponta para ele; ex.: projeto "
                    "usando o layout). Nada deste item foi tocado.")
                continue
            _apagar_arquivos(tipo, retrato)
            log.append(f"{tipo}: {rotulo} "
                       f"(excluído em {quando:%d/%m/%Y})")
    finally:
        db.engine.dispose()
    for linha in log:
        print(f"lixeira: purgado {linha}")
    return log

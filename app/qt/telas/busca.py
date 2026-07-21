"""
Busca global (FASE 2, Bloco F — R-006/017)
==========================================
Um texto → {projetos, produtos, layouts}, 8 de cada, case E
acento-insensível ("acucar" acha "Açúcar"). Headless — o Início e o
Ctrl+K usam o mesmo serviço.
"""

from __future__ import annotations

import unicodedata

from app.core.database import Database

LIMITE = 8


def _norm(texto: str) -> str:
    """minúsculas sem acento (NFD, remove combinantes) — busca folgada."""
    nfd = unicodedata.normalize("NFD", texto or "")
    return "".join(c for c in nfd
                   if unicodedata.category(c) != "Mn").casefold()


def indicadores_saude() -> dict:
    """FASE 2 (passo 91): a saúde do acervo numa linha — sem foto, sem
    categoria, idade do último backup, IA configurada e alcançável.
    Roda em WORKER (passo 92): nunca no caminho do boot."""
    from datetime import datetime

    from app.core.models import Produto
    saida = {"sem_foto": 0, "sem_categoria": 0, "backup_horas": None,
             "ia_ok": False}
    db = Database().init()
    try:
        with db.Session() as s:
            from sqlalchemy import or_
            vivos = s.query(Produto).filter(Produto.excluido_em.is_(None))
            saida["sem_foto"] = vivos.filter(or_(
                Produto.caminho_imagem.is_(None),
                Produto.caminho_imagem == "")).count()
            saida["sem_categoria"] = vivos.filter(
                Produto.categoria_id.is_(None)).count()
    finally:
        db.engine.dispose()
    try:
        from pathlib import Path

        from app.core import cofre
        snaps = cofre.listar_snapshots(None)
        if snaps:
            mtime = max(Path(s_["caminho"]).stat().st_mtime for s_ in snaps)
            saida["backup_horas"] = max(
                0, int((datetime.now().timestamp() - mtime) // 3600))
    except Exception:
        pass
    try:                                 # ping curto — worker aguenta 1 s
        import urllib.request

        from app.ai.client import ConfigIA
        cfg = ConfigIA.da_config()
        url = cfg.base_url.rstrip("/") + "/models"
        with urllib.request.urlopen(url, timeout=1.0):
            saida["ia_ok"] = True
    except Exception:
        saida["ia_ok"] = False
    return saida


def buscar_global(texto: str) -> dict:
    """Grupos com até LIMITE itens cada; <2 letras devolve tudo vazio
    (passo 75 — o campo nem chama, mas o serviço também se defende)."""
    alvo = _norm(texto.strip())
    vazio = {"projetos": [], "produtos": [], "layouts": []}
    if len(alvo) < 2:
        return vazio

    from app.core import projetos as proj_srv
    resultado = dict(vazio)

    for p in proj_srv.listar_projetos():
        if alvo in _norm(p["nome"]) or alvo in _norm(p["evento"]):
            resultado["projetos"].append(p)
            if len(resultado["projetos"]) >= LIMITE:
                break

    db = Database().init()
    try:
        with db.Session() as s:
            from app.core.models import Produto
            consulta = s.query(Produto)
            if hasattr(Produto, "excluido_em"):        # Bloco G filtra
                consulta = consulta.filter(Produto.excluido_em.is_(None))
            for prod in consulta.all():
                junto = _norm(f"{prod.nome_sanitizado} "
                              f"{prod.nome_bruto} {prod.marca or ''}")
                if alvo in junto:
                    preco = ""
                    if prod.preco_atual is not None:
                        preco = f"{prod.preco_atual:.2f}".replace(".", ",")
                    resultado["produtos"].append({
                        "id": prod.id, "nome": prod.nome_sanitizado,
                        "marca": prod.marca or "",
                        "preco": preco,
                    })
                    if len(resultado["produtos"]) >= LIMITE:
                        break
            from app.rendering.persistencia import listar_layouts
            for lin in listar_layouts(s):
                if alvo in _norm(lin.nome):
                    resultado["layouts"].append({
                        "id": lin.id, "nome": lin.nome,
                        "tipo": lin.tipo_midia,
                    })
                    if len(resultado["layouts"]) >= LIMITE:
                        break
    finally:
        db.engine.dispose()
    return resultado

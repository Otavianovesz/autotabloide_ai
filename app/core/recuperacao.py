"""
Recuperação de projeto corrompido (FASE 12, Bloco A — R-137/R-138)
==================================================================
O app mora no PC do mercado e tem que se defender sozinho: se um projeto
salvo estiver CORROMPIDO (JSON quebrado, layout ausente, arte/foto sumida),
o diagnóstico fala PT-BR claro (nunca stack trace na cara do dono) e a
recuperação oferece os SNAPSHOTS BONS — as versões da F2 e o rascunho
automático da F6 — com PRÉVIA ("recuperar o de 16:32, 38 itens?"). Nada
sobrescreve em silêncio (I2); o estado corrompido vira um .bak reversível e
tudo fica logado (passo 11).
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from app.core.database import Database
from app.core.models import ProjetoSalvo
from app.core.projetos import _pasta


# --- diagnóstico honesto (passo 3) -------------------------------------------

def diagnosticar_projeto(projeto_id: int) -> list[str]:
    """Os problemas do projeto, em PT-BR simples. Lista vazia = saudável.
    Nunca levanta — o diagnóstico existe justamente para o caso quebrado."""
    problemas: list[str] = []
    db = Database().init()
    try:
        with db.Session() as s:
            row = s.get(ProjetoSalvo, projeto_id)
            if row is None:
                return ["O projeto não existe mais no banco."]
            uuid, bruto = row.uuid, row.estado_slots or ""
            overrides_bruto = row.overrides_json or "{}"
    finally:
        db.engine.dispose()

    dados = None
    try:
        dados = json.loads(bruto or "{}")
    except json.JSONDecodeError:
        problemas.append("Os dados salvos estão ilegíveis (o arquivo do "
                         "projeto foi danificado).")
    try:
        json.loads(overrides_bruto)
    except json.JSONDecodeError:
        problemas.append("Os ajustes por célula estão ilegíveis.")

    if isinstance(dados, dict) and dados:
        if not isinstance(dados.get("layout"), dict):
            problemas.append("O desenho do tabloide (layout) sumiu do "
                             "projeto.")
        else:
            try:
                from app.rendering.model import LayoutDef
                LayoutDef.from_dict(dados["layout"])
            except Exception:
                problemas.append("O desenho do tabloide (layout) está "
                                 "danificado.")
        pasta = _pasta(uuid)
        sumidas = 0
        for d in dados.get("itens", []):
            rel = d.get("imagem")
            if rel and not (pasta / rel).exists():
                sumidas += 1
        if sumidas:
            problemas.append(f"{sumidas} foto(s) congelada(s) sumiram da "
                             "pasta do projeto.")
    return problemas


# --- snapshots bons (passo 1) ------------------------------------------------

def _estado_valido(texto: str) -> dict | None:
    """O estado parseia E tem o essencial? Devolve o dict ou None."""
    try:
        dados = json.loads(texto)
    except (json.JSONDecodeError, TypeError):
        return None
    if not isinstance(dados, dict) or not isinstance(dados.get("layout"),
                                                     dict):
        return None
    try:
        from app.rendering.model import LayoutDef
        LayoutDef.from_dict(dados["layout"])
    except Exception:
        return None
    return dados


def snapshots_de_recuperacao(projeto_id: int) -> list[dict]:
    """Os candidatos BONS, do mais novo para o mais antigo — cada um com a
    prévia que o diálogo mostra: {"origem": "versão"|"rascunho", "quando",
    "itens": N, "ts"|None}. Só entra snapshot cujo estado VALIDA (não
    adianta oferecer outro lixo)."""
    db = Database().init()
    try:
        with db.Session() as s:
            row = s.get(ProjetoSalvo, projeto_id)
            if row is None:
                return []
            uuid = row.uuid
    finally:
        db.engine.dispose()

    saida: list[dict] = []
    raiz = _pasta(uuid) / "versoes"
    if raiz.exists():
        for pv in sorted((p for p in raiz.iterdir() if p.is_dir()),
                         reverse=True):
            try:
                texto = (pv / "estado.json").read_text(encoding="utf-8")
            except OSError:
                continue
            dados = _estado_valido(texto)
            if dados is None:
                continue                     # versão também quebrada: fora
            try:
                meta = json.loads((pv / "meta.json").read_text("utf-8"))
            except Exception:
                meta = {}
            saida.append({"origem": "versão", "ts": pv.name,
                          "quando": meta.get("quando", pv.name),
                          "itens": len(dados.get("itens", []))})

    # o rascunho automático (F6) só vale se é DESTE projeto (por id, I1)
    try:
        from app.core import rascunho
        estado = rascunho.carregar_rascunho()
        if (estado and estado.get("projeto_id") == projeto_id
                and isinstance(estado.get("layout"), dict)):
            saida.append({"origem": "rascunho", "ts": None,
                          "quando": rascunho.hora_do_rascunho(estado) or "?",
                          "itens": len(estado.get("itens", []))})
    except Exception:
        pass
    return saida


# --- restauração reversível e logada (passos 2 e 11) -------------------------

def _logar(msg: str) -> None:
    try:
        from app.core.paths import SystemRoot
        log = SystemRoot().logs / "recuperacoes.log"
        log.parent.mkdir(parents=True, exist_ok=True)
        with log.open("a", encoding="utf-8") as f:
            f.write(f"{datetime.now():%d/%m/%Y %H:%M:%S}  {msg}\n")
    except Exception:
        pass                                # o log nunca derruba a recuperação


def restaurar_de_snapshot(projeto_id: int, snapshot: dict) -> bool:
    """Restaura o estado do snapshot escolhido. O estado CORROMPIDO vira
    `corrompido_<agora>.bak.json` na pasta do projeto (reversível — nada é
    apagado) e a operação fica em `logs/recuperacoes.log`."""
    db = Database().init()
    try:
        with db.Session() as s:
            row = s.get(ProjetoSalvo, projeto_id)
            if row is None:
                return False
            pasta = _pasta(row.uuid)

            if snapshot["origem"] == "versão":
                pv = pasta / "versoes" / str(snapshot["ts"])
                try:
                    estado = (pv / "estado.json").read_text(encoding="utf-8")
                    overrides = (pv / "overrides.json").read_text("utf-8") \
                        if (pv / "overrides.json").exists() else "{}"
                except OSError:
                    return False
            else:                            # rascunho automático (F6)
                from app.core import rascunho
                dados = rascunho.carregar_rascunho()
                if not dados or dados.get("projeto_id") != projeto_id:
                    return False
                estado = json.dumps(
                    {"tipo": "TABLOIDE", "layout": dados.get("layout"),
                     "itens": dados.get("itens", []),
                     "validade_oferta": dados.get("validade"),
                     "mapa": dados.get("mapa", {})}, ensure_ascii=False)
                overrides = json.dumps(dados.get("overrides", {}),
                                       ensure_ascii=False)
            if _estado_valido(estado) is None:
                return False                 # nunca restaurar outro lixo

            # o corrompido vira .bak (reversível) ANTES de qualquer escrita
            pasta.mkdir(parents=True, exist_ok=True)
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            bak = pasta / f"corrompido_{ts}.bak.json"
            bak.write_text(json.dumps(
                {"estado_slots": row.estado_slots,
                 "overrides_json": row.overrides_json},
                ensure_ascii=False), encoding="utf-8")

            row.estado_slots = estado
            row.overrides_json = overrides
            s.commit()
            _logar(f"projeto {projeto_id} restaurado de "
                   f"{snapshot['origem']} ({snapshot.get('quando')}); "
                   f"corrompido guardado em {bak.name}")
            return True
    finally:
        db.engine.dispose()


# --- R-138: validação de integridade na abertura -----------------------------

def verificar_ao_abrir(raiz=None) -> dict:
    """A checagem leve do boot (R-138): o banco responde ao PRAGMA
    integrity_check? Há cadastros apontando p/ foto que sumiu? Devolve
    {"banco_ok": bool, "sem_arquivo": N, "orfas": N, "avisos": [PT-BR]}.
    Nunca levanta; falha total = aviso honesto."""
    avisos: list[str] = []
    banco_ok = True
    sem_arquivo = orfas = 0
    try:
        from sqlalchemy import text
        db = Database(raiz).init() if raiz else Database().init()
        try:
            with db.Session() as s:
                r = s.execute(text("PRAGMA integrity_check")).scalar()
                banco_ok = (str(r).lower() == "ok")
        finally:
            db.engine.dispose()
        if not banco_ok:
            avisos.append("O banco de dados acusou problema de integridade "
                          "— faça um backup e rode a verificação nas "
                          "Configurações.")
    except Exception:
        banco_ok = False
        avisos.append("Não consegui checar o banco — rode a verificação "
                      "nas Configurações.")
    try:
        from app.core.manutencao import verificar_acervo
        r = verificar_acervo(getattr(raiz, "raiz", raiz))
        sem_arquivo = len(r.get("sem_arquivo", []))
        orfas = len(r.get("orfas", []))
        if sem_arquivo:
            avisos.append(f"{sem_arquivo} produto(s) apontam para foto que "
                          "sumiu do disco.")
    except Exception:
        pass
    return {"banco_ok": banco_ok, "sem_arquivo": sem_arquivo,
            "orfas": orfas, "avisos": avisos}

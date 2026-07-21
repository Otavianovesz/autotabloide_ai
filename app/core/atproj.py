"""
Projeto num arquivo só — .atproj (FASE 12, Bloco A — R-136)
===========================================================
A pasta do projeto congelado JÁ é autossuficiente (arte + fotos com caminhos
relativos, I3). O .atproj é essa pasta + o estado num ZIP com manifesto —
um arquivo só para levar o projeto entre PCs. A importação recria o projeto
POR BAIXO (linha nova + pasta extraída), sem recongelar nada: o roundtrip é
byte a byte nos dados e as fotos seguem relativas (passos 6-7, 15).
"""

from __future__ import annotations

import json
import uuid as _uuid
import zipfile
from datetime import datetime
from pathlib import Path

from app.core.database import Database
from app.core.models import ProjetoSalvo
from app.core.projetos import _layout_id_por_nome, _pasta

FORMATO = "atproj"
VERSAO_FORMATO = 1


def exportar_atproj(projeto_id: int, destino: str | Path) -> Path:
    """Empacota o projeto (estado + overrides + a pasta congelada, SEM as
    versões — o histórico fica no PC de origem) num .atproj único."""
    db = Database().init()
    try:
        with db.Session() as s:
            row = s.get(ProjetoSalvo, projeto_id)
            if row is None:
                raise ValueError("Projeto não encontrado.")
            manifesto = {
                "formato": FORMATO, "versao": VERSAO_FORMATO,
                "nome": row.nome, "evento": row.evento,
                "criado_em": (row.criado_em.strftime("%d/%m/%Y %H:%M")
                              if row.criado_em else ""),
                "exportado_em": datetime.now().strftime("%d/%m/%Y %H:%M"),
            }
            estado = row.estado_slots or "{}"
            overrides = row.overrides_json or "{}"
            pasta = _pasta(row.uuid)
    finally:
        db.engine.dispose()

    destino = Path(destino)
    if destino.suffix.lower() != ".atproj":
        destino = destino.with_suffix(".atproj")
    destino.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(destino, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("manifesto.json",
                   json.dumps(manifesto, ensure_ascii=False, indent=2))
        z.writestr("estado.json", estado)
        z.writestr("overrides.json", overrides)
        if pasta.exists():
            for arq in sorted(pasta.rglob("*")):
                if not arq.is_file():
                    continue
                rel = arq.relative_to(pasta).as_posix()
                if rel.startswith("versoes/") or rel.endswith(".bak.json"):
                    continue             # o histórico não viaja
                z.write(arq, f"arquivos/{rel}")
    return destino


def ler_manifesto(arquivo: str | Path) -> dict | None:
    """A prévia do import ("Quintou, 38 itens, salvo em 16/07") — None se o
    arquivo não é um .atproj válido (a UI avisa, nunca estoura)."""
    try:
        with zipfile.ZipFile(arquivo) as z:
            m = json.loads(z.read("manifesto.json").decode("utf-8"))
            if m.get("formato") != FORMATO:
                return None
            if "overrides.json" not in z.namelist():
                return None              # incompleto: a prévia já recusa
            estado = json.loads(z.read("estado.json").decode("utf-8"))
            m["itens"] = len(estado.get("itens", []))
            m["paginas"] = len((estado.get("layout") or {})
                               .get("paginas", []))
            return m
    except Exception:
        return None


def importar_atproj(arquivo: str | Path) -> int:
    """Recria o projeto deste PC: linha nova (uuid PRÓPRIO — nunca colide
    com um projeto local, I1) + a pasta extraída. O estado entra byte a byte
    como veio (nada é recongelado — as fotos já são relativas à pasta)."""
    from app.core.modo import exigir_escrita
    exigir_escrita()                     # trazer projeto É escrita no acervo
    arquivo = Path(arquivo)
    with zipfile.ZipFile(arquivo) as z:
        manifesto = json.loads(z.read("manifesto.json").decode("utf-8"))
        if manifesto.get("formato") != FORMATO:
            raise ValueError("Este arquivo não é um projeto .atproj.")
        try:
            versao = int(manifesto.get("versao") or 1)
        except (TypeError, ValueError):
            versao = VERSAO_FORMATO + 1
        if versao > VERSAO_FORMATO:
            raise ValueError(
                "Este projeto foi feito numa versão MAIS NOVA do "
                "AutoTabloide — atualize o programa deste PC para trazê-lo.")
        presentes = set(z.namelist())
        faltando = [n for n in ("estado.json", "overrides.json")
                    if n not in presentes]
        if faltando:
            raise ValueError("O .atproj veio incompleto — falta "
                             + " e ".join(faltando)
                             + ". Exporte o projeto de novo no PC de origem.")
        estado = z.read("estado.json").decode("utf-8")
        overrides = z.read("overrides.json").decode("utf-8")
        dados = json.loads(estado)
        from app.rendering.model import LayoutDef
        lay = LayoutDef.from_dict(dados["layout"])   # valida antes de gravar

        novo_uuid = str(_uuid.uuid4())
        pasta = _pasta(novo_uuid).resolve()
        pasta.mkdir(parents=True, exist_ok=True)
        for nome in z.namelist():
            if not nome.startswith("arquivos/") or nome.endswith("/"):
                continue
            rel = Path(nome[len("arquivos/"):])
            # contenção por caminho CANÔNICO: barra absoluto, "..", raiz
            # sem letra de drive ("/Windows/...", que no Windows NÃO é
            # "absolute" mas ancora na raiz do drive) e link para fora
            alvo = (pasta / rel).resolve()
            if pasta != alvo and pasta not in alvo.parents:
                continue                 # zip malicioso não escapa da pasta
            alvo.parent.mkdir(parents=True, exist_ok=True)
            alvo.write_bytes(z.read(nome))

    db = Database().init()
    try:
        with db.Session() as s:
            row = ProjetoSalvo(
                nome=manifesto.get("nome") or arquivo.stem,
                uuid=novo_uuid,
                layout_id=_layout_id_por_nome(
                    s, f"Layout de {manifesto.get('nome') or arquivo.stem}",
                    lay))
            row.evento = manifesto.get("evento")
            if row.evento:
                from app.qt.telas.eventos import criar_evento
                row.evento_id = criar_evento(s, row.evento).id
            row.estado_slots = estado
            row.overrides_json = overrides
            s.add(row)
            s.commit()
            return row.id
    finally:
        db.engine.dispose()

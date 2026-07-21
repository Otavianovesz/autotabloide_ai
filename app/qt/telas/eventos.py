"""
Eventos — o serviço headless (FASE 2, Bloco A)
==============================================
O evento como entidade: cor, capa, dia da semana, ordem e notas.

- **Migração (passo 3)**: cada `evento` TEXTO distinto dos projetos vira
  linha em `Evento` (cor estável por hash do nome numa paleta fixa) e o
  `evento_id` é preenchido. Os `eventos.extras` da Config (prateleiras
  vazias criadas pelo Início) e os dias do RG-24 (`eventos.dias`) migram
  junto — NADA se perde. Idempotente: roda a cada listagem.
- **Capa (I3)**: internada em `layouts/capas/`, caminho RELATIVO no banco.
- **Excluir (passo 6)**: só vazio OU movendo os projetos — nunca órfão
  em silêncio.
"""

from __future__ import annotations

import shutil
import zlib
from pathlib import Path

from app.core.database import Database
from app.core.models import Evento, ProjetoSalvo

# paleta fixa de 12 cores (estável — o hash do nome escolhe)
PALETA_EVENTOS = [
    "#2563EB", "#16A34A", "#D97706", "#DC2626", "#7C3AED", "#0891B2",
    "#DB2777", "#65A30D", "#EA580C", "#0D9488", "#9333EA", "#B45309",
]

_DIAS = {"seg": 0, "ter": 1, "qua": 2, "qui": 3, "sex": 4,
         "sab": 5, "sáb": 5, "dom": 6}


def cor_para_nome(nome: str) -> str:
    """Cor ESTÁVEL por nome (crc32 → paleta) — igual em qualquer máquina."""
    indice = zlib.crc32(nome.strip().lower().encode("utf-8"))
    return PALETA_EVENTOS[indice % len(PALETA_EVENTOS)]


def _dia_da_config(s, nome: str) -> int | None:
    """RG-24: importa o dia configurado em `eventos.dias` (fallback legado)."""
    from app.core.repositories import ConfigRepositorio
    mapa = ConfigRepositorio(s).get("eventos.dias") or {}
    valor = next((v for k, v in mapa.items()
                  if k.strip().lower() == nome.strip().lower()), None)
    if valor is None:
        return None
    if isinstance(valor, int) and 0 <= valor <= 6:
        return valor
    return _DIAS.get(str(valor).strip().lower()[:3])


def migrar_eventos_texto(s) -> int:
    """Passo 3: eventos-texto e extras da Config viram entidades; devolve
    quantos Eventos foram criados. Idempotente e sem perda (teste 11)."""
    from app.core.repositories import ConfigRepositorio
    existentes = {e.nome.strip().lower(): e for e in s.query(Evento).all()}
    nomes: list[str] = []
    for (texto,) in (s.query(ProjetoSalvo.evento).distinct().all()):
        if texto and texto.strip():
            nomes.append(texto.strip())
    for extra in (ConfigRepositorio(s).get("eventos.extras") or []):
        if str(extra).strip():
            nomes.append(str(extra).strip())
    criados = 0
    for nome in nomes:
        chave = nome.lower()
        if chave not in existentes:
            ev = Evento(nome=nome, cor=cor_para_nome(nome),
                        dia_semana=_dia_da_config(s, nome))
            s.add(ev)
            s.flush()
            existentes[chave] = ev
            criados += 1
    # preencher evento_id dos projetos que só têm o texto
    for p in s.query(ProjetoSalvo).filter(
            ProjetoSalvo.evento_id.is_(None),
            ProjetoSalvo.evento.isnot(None)).all():
        ev = existentes.get((p.evento or "").strip().lower())
        if ev is not None:
            p.evento_id = ev.id
    return criados


def listar_eventos(s=None) -> list[dict]:
    """Eventos na ordem (ordem, nome), com a migração garantida antes."""
    if s is None:
        db = Database().init()
        try:
            with db.Session() as sess:
                dados = listar_eventos(sess)
                sess.commit()
            return dados
        finally:
            db.engine.dispose()
    migrar_eventos_texto(s)
    linhas = s.query(Evento).order_by(Evento.ordem, Evento.nome).all()
    return [{"id": e.id, "nome": e.nome, "cor": e.cor, "capa": e.capa,
             "dia_semana": e.dia_semana, "ordem": e.ordem,
             "notas": e.notas or ""} for e in linhas]


def criar_evento(s, nome: str, cor: str | None = None,
                 dia_semana: int | None = None,
                 capa_origem: str | None = None) -> Evento:
    nome = nome.strip()
    if not nome:
        raise ValueError("evento sem nome")
    ja = s.query(Evento).filter(Evento.nome.ilike(nome)).first()
    if ja is not None:
        return ja                        # criar 2× não duplica
    ev = Evento(nome=nome, cor=cor or cor_para_nome(nome),
                dia_semana=dia_semana)
    s.add(ev)
    s.flush()
    if capa_origem:
        definir_capa(s, ev.id, capa_origem)
    return ev


def _evento(s, evento_id: int) -> Evento:
    ev = s.get(Evento, evento_id)
    if ev is None:
        raise ValueError(f"evento {evento_id} não existe")
    return ev


def renomear_evento(s, evento_id: int, novo_nome: str) -> None:
    ev = _evento(s, evento_id)
    novo_nome = novo_nome.strip()
    if not novo_nome:
        raise ValueError("nome vazio")
    ev.nome = novo_nome
    # o texto de compat dos projetos acompanha (leitura antiga não mente)
    for p in s.query(ProjetoSalvo).filter_by(evento_id=ev.id).all():
        p.evento = novo_nome


def mudar_cor(s, evento_id: int, cor: str) -> None:
    _evento(s, evento_id).cor = cor


def definir_dia(s, evento_id: int, dia_semana: int | None) -> None:
    if dia_semana is not None and not 0 <= int(dia_semana) <= 6:
        raise ValueError("dia_semana fora de 0..6")
    _evento(s, evento_id).dia_semana = dia_semana


def definir_notas(s, evento_id: int, notas: str) -> None:
    _evento(s, evento_id).notas = notas or ""


def reordenar(s, ids_na_ordem: list[int]) -> None:
    for i, eid in enumerate(ids_na_ordem):
        _evento(s, eid).ordem = i


def _pasta_capas() -> Path:
    from app.core.paths import SystemRoot
    pasta = SystemRoot().layouts / "capas"
    pasta.mkdir(parents=True, exist_ok=True)
    return pasta


def definir_capa(s, evento_id: int, origem: str | None) -> None:
    """Interna a imagem em `layouts/capas/` e grava o caminho RELATIVO (I3).
    ``origem=None`` remove a capa (volta ao padrão do passo 8)."""
    ev = _evento(s, evento_id)
    if not origem:
        ev.capa = None
        return
    origem_p = Path(origem)
    if not origem_p.exists():
        raise ValueError(f"capa não encontrada: {origem}")
    destino = _pasta_capas() / f"evento_{ev.id}{origem_p.suffix.lower()}"
    shutil.copyfile(origem_p, destino)
    ev.capa = f"capas/{destino.name}"     # relativo à pasta layouts (I3)


def caminho_capa(capa_relativa: str | None) -> Path | None:
    """Resolve a capa relativa para o disco (None se não há ou sumiu)."""
    if not capa_relativa:
        return None
    from app.core.paths import SystemRoot
    caminho = SystemRoot().layouts / capa_relativa
    return caminho if caminho.exists() else None


def capa_do_evento(s, evento_id: int) -> Path | None:
    """Passo 8: a capa DEFINIDA, ou a miniatura do projeto mais recente
    do evento (padrão vivo — muda junto com a produção)."""
    ev = s.get(Evento, evento_id)
    definida = caminho_capa(ev.capa if ev else None)
    if definida is not None:
        return definida
    from app.core.projetos import _pasta
    p = (s.query(ProjetoSalvo).filter_by(evento_id=evento_id)
         .order_by(ProjetoSalvo.criado_em.desc()).first())
    if p is not None:
        mini = _pasta(p.uuid) / "miniatura.png"
        if mini.exists():
            return mini
    return None


def excluir_evento(s, evento_id: int,
                   mover_para: int | None = None) -> None:
    """Passo 6: só exclui vazio OU movendo TODOS os projetos para outro
    evento — nunca deixa projeto órfão em silêncio."""
    ev = _evento(s, evento_id)
    projetos = s.query(ProjetoSalvo).filter_by(evento_id=ev.id).all()
    if projetos:
        if mover_para is None or mover_para == evento_id:
            raise ValueError(
                f"“{ev.nome}” tem {len(projetos)} projeto(s) — escolha "
                "outro evento para recebê-los")
        destino = _evento(s, mover_para)
        for p in projetos:
            p.evento_id = destino.id
            p.evento = destino.nome
    s.delete(ev)


def mover_projeto(s, projeto_id: int, evento_id: int | None) -> None:
    """Passo 28: muda o evento de UM projeto (id + texto de compat)."""
    p = s.get(ProjetoSalvo, projeto_id)
    if p is None:
        raise ValueError(f"projeto {projeto_id} não existe")
    if evento_id is None:
        p.evento_id = None
        p.evento = None                  # vira Avulso
    else:
        ev = _evento(s, evento_id)
        p.evento_id = ev.id
        p.evento = ev.nome


def dia_do_evento_v2(s, nome_ou_id) -> int | None:
    """Passo 7: o dia agora mora no Evento; a Config antiga é fallback."""
    ev = None
    if isinstance(nome_ou_id, int):
        ev = s.get(Evento, nome_ou_id)
    elif nome_ou_id:
        ev = s.query(Evento).filter(
            Evento.nome.ilike(str(nome_ou_id).strip())).first()
    if ev is not None and ev.dia_semana is not None:
        return ev.dia_semana
    return _dia_da_config(s, str(nome_ou_id)) if nome_ou_id else None

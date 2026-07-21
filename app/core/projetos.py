"""
Projeto salvo congelado (§3.1/§6.8) — o app guarda o seu trabalho
=================================================================
Um projeto é um tabloide/cartaz **montado** cujos dados ficam **congelados**
na época: reabrir mostra idêntico, mesmo que o banco mude depois.

O que congela (tudo inline no ``estado_slots`` + cópias em disco):
- o **LayoutDef usado** (inline — editar o layout no Ateliê depois NÃO muda
  o projeto; ``layout_id`` fica só como referência de origem);
- os **itens por slot** (nome, preços de/por, unidade, +18, validade) — o
  snapshot do produto da época;
- as **imagens usadas** e a **arte de fundo**: copiadas para a pasta do
  projeto (`projetos/<uuid>/`) — trocar a foto no banco não toca o projeto;
- a validade da oferta e a data.

Precedência: override do slot > dado congelado > banco (o ``overrides_json``
por slot fica reservado para o modal de override da Mesa — F7.3).
"""

from __future__ import annotations

import json
import shutil
import uuid as _uuid
from dataclasses import dataclass, field
from pathlib import Path

from sqlalchemy import select

from app.core.database import Database
from app.core.models import Layout, ProjetoSalvo
from app.core.paths import SystemRoot
from app.rendering.model import LayoutDef


@dataclass
class ProjetoAberto:
    """Um projeto descongelado, pronto para a tela (dados planos)."""

    id: int
    nome: str
    evento: str | None
    tipo: str                       # TABLOIDE | CARTAZ
    layout: LayoutDef               # o layout DA ÉPOCA (inline)
    itens: list[dict] = field(default_factory=list)   # ItemMesa.to_dict()
    validade_oferta: str | None = None
    criado_em: str = ""
    mapa: dict = field(default_factory=dict)          # slot_id → item.uid (I1)
    overrides: dict = field(default_factory=dict)     # F7.3: slot_id → {campo: v}


def _pasta(uuid: str) -> Path:
    return SystemRoot().projetos / uuid


def _gerar_miniatura(pasta: Path, layout: LayoutDef, itens: list[dict],
                     mapa: dict | None = None,
                     overrides: dict | None = None) -> None:
    """Compõe a 1ª página em miniatura (cache do Dashboard). Nunca quebra o salvar.

    Com ``mapa`` (I1), compõe pelo casamento exato slot→uid; sem, por posição
    (legado). ``overrides`` (F7.3) entram por slot — a miniatura mostra o que
    o export mostraria. Caminhos são relativos à pasta (I3) — resolve aqui.
    """
    try:
        from app.qt.telas.servico import ItemMesa, aplicar_override, preco_decimal
        from app.rendering.compositor import DadosProduto, compor_pagina

        def _dp(d: dict) -> DadosProduto:
            from app.rendering.arranjo import ModoArranjo
            from app.rendering.compositor import ImagemSlot
            it = ItemMesa.from_dict(d)
            try:
                arranjo = ModoArranjo(it.arranjo) if it.arranjo \
                    else ModoArranjo.LEQUE
            except ValueError:
                arranjo = ModoArranjo.LEQUE
            return DadosProduto(
                it.nome, preco_por=preco_decimal(it.preco),
                preco_de=preco_decimal(it.preco_de),
                imagem_path=_resolver(pasta, it.imagem),
                imagens=[ImagemSlot(_resolver(pasta, c))
                         for c in (it.imagens or [])],       # F7.1
                modo_arranjo=arranjo,
                mais18=it.mais18,
                unidade=it.unidade,
                categoria=it.categoria)                      # F8.2 (seções)

        if mapa:
            por_uid = {d.get("uid"): d for d in itens}
            dados = {}
            for sid, uid in mapa.items():
                if uid not in por_uid:
                    continue
                dp = _dp(por_uid[uid])
                ov = (overrides or {}).get(sid)
                if ov:
                    ov = dict(ov)
                    if ov.get("imagem"):
                        ov["imagem"] = _resolver(pasta, ov["imagem"])
                    dp = aplicar_override(dp, ov)
                dados[sid] = dp
        else:
            dados = [_dp(d) for d in itens[: len(layout.paginas[0].slots) or 1]]
        fundo = _resolver(pasta, layout.paginas[0].arquivo_fundo
                          or layout.arquivo_fundo)          # miniatura = pág. 1
        img = compor_pagina(layout, layout.paginas[0], dados, fundo_path=fundo)
        img.thumbnail((360, 360))
        pasta.mkdir(parents=True, exist_ok=True)   # projeto sem imagens/arte
        img.save(pasta / "miniatura.png")
    except Exception:
        # sem miniatura ≠ sem projeto — mas a falha fica REGISTRADA (I2):
        # pode ser o primeiro sintoma de um mapa/caminho quebrado.
        import logging
        logging.getLogger(__name__).warning(
            "miniatura do projeto falhou (o salvar seguiu normal)", exc_info=True)


def _congelar_arquivo(origem: str | None, pasta: Path, rel: str) -> str | None:
    """Copia p/ a pasta do projeto e devolve o caminho **RELATIVO** (I3).

    Guarda de re-salvar (P1.2): origem já dentro da pasta → só devolve o
    relativo (nunca `SameFileError`).
    """
    if not origem or not Path(origem).exists():
        return None
    destino = pasta / rel
    try:
        if Path(origem).resolve() == destino.resolve():
            return rel
    except OSError:
        pass
    destino.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy(origem, destino)
    return rel


def _resolver(pasta: Path, caminho: str | None) -> str | None:
    """Relativo do projeto → absoluto p/ a UI (absoluto legado passa direto)."""
    if not caminho:
        return None
    p = Path(caminho)
    return str(p) if p.is_absolute() else str(pasta / p)


def _layout_id_por_nome(session, nome_layout: str, layout_def: LayoutDef) -> int:
    """Referência de origem (FK): acha o Layout pelo nome; cria se não existir."""
    row = session.execute(
        select(Layout).where(Layout.nome == nome_layout)).scalar_one_or_none()
    if row is None:
        # E-A3: a referência criada aqui também interna a arte (nada de
        # caminho de máquina no banco vivo)
        from app.rendering.persistencia import _internar_estrutura
        fundo, estrutura = _internar_estrutura(layout_def)
        row = Layout(nome=nome_layout, arquivo_fundo=fundo,
                     estrutura_json=estrutura)
        session.add(row)
        session.flush()
    return row.id


def salvar_projeto(
    nome: str,
    evento: str | None,
    tipo: str,
    layout_def: LayoutDef,
    itens: list[dict],
    validade_oferta: str | None = None,
    *,
    nome_layout: str = "Layout do projeto",
    projeto_id: int | None = None,
    mapa: dict | None = None,
    overrides: dict | None = None,
) -> int:
    """Congela e grava. ``itens`` = ``ItemMesa.to_dict()``; ``mapa`` =
    ``{slot_id → item.uid}`` (I1 — o casamento exato, não a ordem);
    ``overrides`` = F7.3, ``{slot_id → {campo: valor}}`` — a foto do override
    também congela na pasta do projeto (relativa, I3)."""
    db = Database().init()
    try:
        with db.Session() as s:
            if projeto_id is not None:
                row = s.get(ProjetoSalvo, projeto_id)
            else:
                row = ProjetoSalvo(nome=nome, uuid=str(_uuid.uuid4()),
                                   layout_id=_layout_id_por_nome(
                                       s, nome_layout, layout_def))
                s.add(row)
            row.nome = nome
            row.evento = (evento or "").strip() or None
            # FASE 2 (passo 4): a verdade é o evento_id — o Evento nasce
            # aqui se o dono digitou um nome novo; o texto fica por compat
            if row.evento:
                from app.qt.telas.eventos import criar_evento
                row.evento_id = criar_evento(s, row.evento).id
            else:
                row.evento_id = None

            pasta = _pasta(row.uuid)
            # FASE 2 (passos 57-58): ANTES do recongelamento (que
            # sobrescreve imagens/*.png), o estado anterior vira VERSÃO —
            # snapshot COMPLETO da pasta (byte-fiel). Se no fim o hash não
            # tiver mudado, a versão recém-criada é descartada (rollback).
            versao_nova = None
            if projeto_id is not None and (row.estado_slots or "").strip() \
                    not in ("", "{}"):
                versao_nova = _gravar_versao(pasta, row.estado_slots,
                                             row.overrides_json or "{}")
            # congela as imagens usadas — caminhos RELATIVOS à pasta (I3)
            itens_frios = []
            for i, item in enumerate(itens):
                frio = dict(item)
                origem = item.get("imagem")
                sufixo = Path(origem).suffix if origem else ".png"
                frio["imagem"] = _congelar_arquivo(
                    origem, pasta, f"imagens/{i:02d}{sufixo or '.png'}")
                # F7.1: as N fotos do item congelam NA ORDEM (a ordem é a do
                # desenho no slot); foto sumida no salvar já foi acusada no
                # pré-voo — aqui ela cai fora da lista congelada
                extras = []
                for k, cam in enumerate(item.get("imagens") or []):
                    suf = Path(cam).suffix if cam else ".png"
                    congelada = _congelar_arquivo(
                        cam, pasta, f"imagens/{i:02d}_{k:02d}{suf or '.png'}")
                    if congelada:
                        extras.append(congelada)
                frio["imagens"] = extras
                # F7.2: as fotos dos itens de ORIGEM do composto também
                # congelam (I3) — "separar" depois de reabrir devolve itens
                # com foto viva, não caminho de outra máquina
                origens_frias = []
                for k, origem in enumerate(item.get("origem_composto") or []):
                    org = dict(origem)
                    cam = org.get("imagem")
                    suf = Path(cam).suffix if cam else ".png"
                    org["imagem"] = _congelar_arquivo(
                        cam, pasta, f"imagens/{i:02d}_org{k}{suf or '.png'}")
                    fotos_org = []
                    for j, cx in enumerate(org.get("imagens") or []):
                        suf_j = Path(cx).suffix if cx else ".png"
                        c = _congelar_arquivo(
                            cx, pasta,
                            f"imagens/{i:02d}_org{k}_{j:02d}{suf_j or '.png'}")
                        if c:
                            fotos_org.append(c)
                    org["imagens"] = fotos_org
                    origens_frias.append(org)
                frio["origem_composto"] = origens_frias
                itens_frios.append(frio)
            # congela a arte de fundo junto do layout inline (relativa)
            lay = LayoutDef.from_dict(layout_def.to_dict())   # cópia própria
            if lay.arquivo_fundo:
                sufixo = Path(lay.arquivo_fundo).suffix or ".png"
                lay.arquivo_fundo = _congelar_arquivo(
                    lay.arquivo_fundo, pasta, f"arte{sufixo}") or lay.arquivo_fundo
            # D8.6: fundo POR PÁGINA também congela (frente+verso)
            for n_pag, pag in enumerate(lay.paginas, start=1):
                if pag.arquivo_fundo:
                    sufixo = Path(pag.arquivo_fundo).suffix or ".png"
                    pag.arquivo_fundo = _congelar_arquivo(
                        pag.arquivo_fundo, pasta,
                        f"arte_p{n_pag}{sufixo}") or pag.arquivo_fundo

            # F7.3: overrides congelam junto; foto do override vira cópia
            # relativa da pasta do projeto (mesma regra das fotos dos itens)
            overrides_frios: dict = {}
            for sid, ov in (overrides or {}).items():
                if not ov:
                    continue
                frio = dict(ov)
                origem = ov.get("imagem")
                if origem:
                    sufixo = Path(origem).suffix or ".png"
                    frio["imagem"] = _congelar_arquivo(
                        origem, pasta, f"imagens/override_{sid}{sufixo}")
                overrides_frios[sid] = frio
            row.overrides_json = json.dumps(overrides_frios, ensure_ascii=False)

            # FASE 2 (passo 36): status por CONTEÚDO — salvar por cima de
            # um exportado/publicado só volta a "rascunho" se o estado
            # MUDOU (hash); re-salvar igual não rebaixa o status à toa
            estado_antigo = row.estado_slots or ""
            row.set_slots({
                "tipo": tipo,
                "layout": lay.to_dict(),
                "itens": itens_frios,
                "validade_oferta": validade_oferta,
                "mapa": dict(mapa or {}),
            })
            import hashlib
            h_novo = hashlib.sha256(
                (row.estado_slots or "").encode("utf-8")).hexdigest()
            h_velho = hashlib.sha256(
                estado_antigo.encode("utf-8")).hexdigest()
            if projeto_id is None:
                row.status = "rascunho"
            elif h_novo != h_velho:
                row.status = "rascunho"          # conteúdo mudou de verdade
                # R-068: editar um aprovado TIRA a aprovação (a marca d'água
                # RASCUNHO volta até reaprovar). Na MESMA sessão — sem conexão
                # aninhada. Só quando o conteúdo mudou de fato (o hash).
                from app.core.repositories import ConfigRepositorio
                _repo = ConfigRepositorio(s)
                _aprov = _repo.get("projetos.aprovados") or {}
                if _aprov.pop(str(row.id), None) is not None:
                    _repo.set("projetos.aprovados", _aprov)
            if versao_nova is not None and h_novo == h_velho:
                # nada mudou: a versão criada seria ruído — descarta
                shutil.rmtree(versao_nova, ignore_errors=True)
            elif versao_nova is not None:
                _podar_versoes(pasta)            # FASE 2 (passo 59)
            _gerar_miniatura(pasta, lay, itens_frios, dict(mapa or {}),
                             overrides_frios)
            s.commit()
            return row.id
    finally:
        db.engine.dispose()


STATUS_VALIDOS = ("rascunho", "pronto", "exportado", "publicado")


# --- FASE 2, Bloco E: linha do tempo de versões (R-005) ----------------------

def _gravar_versao(pasta: Path, estado_json: str,
                   overrides_json: str = "{}") -> Path:
    """Passos 57-58: snapshot COMPLETO da pasta (arte, imagens, miniatura)
    + estado.json + overrides.json + meta.json em ``versoes/<ts>/``."""
    from datetime import datetime
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    destino = pasta / "versoes" / ts
    n = 1
    while destino.exists():              # 2 salvamentos no mesmo segundo
        n += 1
        destino = pasta / "versoes" / f"{ts}_{n}"
    destino.mkdir(parents=True)
    if pasta.exists():
        for item in pasta.iterdir():
            if item.name == "versoes":
                continue
            if item.is_dir():
                shutil.copytree(item, destino / item.name)
            else:
                shutil.copyfile(item, destino / item.name)
    (destino / "estado.json").write_text(estado_json, encoding="utf-8")
    (destino / "overrides.json").write_text(overrides_json or "{}",
                                            encoding="utf-8")
    try:
        dados = json.loads(estado_json or "{}")
    except json.JSONDecodeError:
        dados = {}
    meta = {"quando": datetime.now().strftime("%d/%m/%Y %H:%M"),
            "itens": len(dados.get("itens", [])),
            "paginas": len((dados.get("layout") or {}).get("paginas", []))}
    (destino / "meta.json").write_text(
        json.dumps(meta, ensure_ascii=False), encoding="utf-8")
    return destino


def _max_versoes() -> int:
    try:
        from app.core.repositories import ConfigRepositorio
        db = Database().init()
        try:
            with db.Session() as s:
                v = int(ConfigRepositorio(s).get("projetos.versoes_max")
                        or 10)
            return v if v >= 1 else 10
        finally:
            db.engine.dispose()
    except Exception:
        return 10


def _podar_versoes(pasta: Path) -> None:
    """Passo 59: mantém as N mais novas (a ATUAL vive fora de versoes/ —
    a poda nunca a toca)."""
    raiz = pasta / "versoes"
    if not raiz.exists():
        return
    versoes = sorted(p for p in raiz.iterdir() if p.is_dir())
    for velha in versoes[:-_max_versoes()]:
        shutil.rmtree(velha, ignore_errors=True)


def listar_versoes(projeto_id: int) -> list[dict]:
    """As versões do projeto, mais novas primeiro (ts, quando, itens,
    páginas, miniatura)."""
    db = Database().init()
    try:
        with db.Session() as s:
            row = s.get(ProjetoSalvo, projeto_id)
            if row is None:
                return []
            uuid = row.uuid
    finally:
        db.engine.dispose()
    raiz = _pasta(uuid) / "versoes"
    if not raiz.exists():
        return []
    saida = []
    for pv in sorted((p for p in raiz.iterdir() if p.is_dir()),
                     reverse=True):
        try:
            meta = json.loads((pv / "meta.json").read_text(encoding="utf-8"))
        except Exception:
            meta = {}
        mini = pv / "miniatura.png"
        saida.append({"ts": pv.name,
                      "quando": meta.get("quando", pv.name),
                      "itens": meta.get("itens", 0),
                      "paginas": meta.get("paginas", 0),
                      "miniatura": str(mini) if mini.exists() else None})
    return saida


def abrir_versao_como_novo(projeto_id: int, ts: str) -> int | None:
    """Passo 61: a ÚNICA ação sobre versão — clonar como projeto NOVO
    ("Nome (versão de DD/MM)"). Restaurar por cima é PROIBIDO (I1: o
    projeto vivo nunca é sobrescrito por versão)."""
    db = Database().init()
    try:
        with db.Session() as s:
            origem = s.get(ProjetoSalvo, projeto_id)
            if origem is None:
                return None
            pv = _pasta(origem.uuid) / "versoes" / ts
            if not pv.exists():
                return None
            estado = (pv / "estado.json").read_text(encoding="utf-8")
            try:
                overrides_da_epoca = (pv / "overrides.json").read_text(
                    encoding="utf-8")
            except OSError:
                overrides_da_epoca = "{}"    # versão de antes do campo
            try:
                meta = json.loads((pv / "meta.json").read_text(
                    encoding="utf-8"))
            except Exception:
                meta = {}
            quando = (meta.get("quando", "")or "").split(" ")[0]
            copia = ProjetoSalvo(
                nome=f"{origem.nome} (versão de {quando})",
                uuid=str(_uuid.uuid4()),
                layout_id=origem.layout_id, evento=origem.evento,
                evento_id=origem.evento_id,
                estado_slots=estado,
                overrides_json=overrides_da_epoca,
                status="rascunho",
            )
            s.add(copia)
            s.flush()
            nova = _pasta(copia.uuid)
            shutil.copytree(pv, nova)
            shutil.rmtree(nova / "versoes", ignore_errors=True)
            for extra in ("estado.json", "overrides.json", "meta.json"):
                (nova / extra).unlink(missing_ok=True)
            s.commit()
            return copia.id
    finally:
        db.engine.dispose()


def marcar_favorito(projeto_id: int, favorito: bool) -> None:
    """FASE 2 (passos 49-50): favorito sobe no evento (só ordenação de
    exibição — o mapa/vínculos não sabem que ele existe)."""
    db = Database().init()
    try:
        with db.Session() as s:
            row = s.get(ProjetoSalvo, projeto_id)
            if row is not None:
                row.favorito = bool(favorito)
                s.commit()
    finally:
        db.engine.dispose()


def duplicar_semana_passada(nome_evento: str) -> int | None:
    """FASE 2 (passos 97-98 — R-009, o gesto nº 1): clona o ÚLTIMO projeto
    do evento como rascunho de HOJE — nome "[Evento] DD/MM" com dedup,
    validade re-sugerida pelo dia da campanha (RG-24), status rascunho
    (o duplicar já garante). Devolve o id novo ou None (evento vazio)."""
    from datetime import date

    ultimo = None
    for p in listar_projetos():          # já vem mais novo primeiro
        if (p["evento"] or "").strip().lower() \
                == nome_evento.strip().lower():
            ultimo = p
            break
    if ultimo is None:
        return None

    # nome com dedup (2), (3)…
    hoje = date.today().strftime("%d/%m")
    base = f"{nome_evento} {hoje}"
    existentes = {p["nome"] for p in listar_projetos()}
    nome = base
    n = 2
    while nome in existentes:
        nome = f"{base} ({n})"
        n += 1

    novo = duplicar_projeto(ultimo["id"], nome)
    if novo is None:
        return None
    # validade re-sugerida pela campanha (ou limpa, se não há dia fixo)
    from app.qt.telas.servico import sugerir_validade
    sugestao = sugerir_validade(nome_evento)
    db = Database().init()
    try:
        with db.Session() as s:
            row = s.get(ProjetoSalvo, novo)
            dados = row.get_slots()
            dados["validade_oferta"] = sugestao
            row.set_slots(dados)
            s.commit()
    finally:
        db.engine.dispose()
    # GATE 2.5 (ordem F11.5): duplicar é um dos 4 caminhos de abertura — o
    # clone novo É o projeto em que o dono vai trabalhar; "Continuar de onde
    # parei" tem que apontar para ele (antes este caminho não registrava).
    registrar_ultimo_aberto(novo)
    return novo


def registrar_export(projeto_id: int, caminho: str) -> None:
    """FASE 2 (passo 94): o modo apresentação usa o EXPORT real quando
    existe — o app lembra onde cada projeto foi exportado."""
    try:
        from app.core.repositories import ConfigRepositorio
        db = Database().init()
        try:
            with db.Session() as s:
                repo = ConfigRepositorio(s)
                mapa = repo.get("projetos.exports") or {}
                mapa[str(projeto_id)] = str(caminho)
                repo.set("projetos.exports", mapa)
                s.commit()
        finally:
            db.engine.dispose()
    except Exception:
        pass


def export_de(projeto_id: int) -> str | None:
    """O caminho do último export do projeto, se ainda existir no disco."""
    try:
        from app.core.repositories import ConfigRepositorio
        db = Database().init()
        try:
            with db.Session() as s:
                mapa = ConfigRepositorio(s).get("projetos.exports") or {}
        finally:
            db.engine.dispose()
        caminho = mapa.get(str(projeto_id))
        if caminho and Path(caminho).exists():
            return caminho
        return None
    except Exception:
        return None


def aprovar(projeto_id: int) -> None:
    """R-068: marca o projeto como APROVADO (conferido). A exportação LIMPA (sem
    a marca d'água RASCUNHO) só é liberada depois disto. Guardado na Config
    (como os exports), sem migração de banco."""
    _set_aprovado(projeto_id, True)


def desaprovar(projeto_id: int) -> None:
    """Tira a aprovação — editar um aprovado volta a rascunho (a marca d'água
    retorna até reaprovar)."""
    _set_aprovado(projeto_id, False)


def _hash_estado_salvo(s, projeto_id: int) -> str | None:
    """OS F11.5 #24: a impressão digital da VERSÃO salva (sha256 do estado
    congelado) — a aprovação é desta versão, não do id para sempre."""
    import hashlib
    row = s.get(ProjetoSalvo, projeto_id)
    if row is None:
        return None
    return hashlib.sha256((row.estado_slots or "").encode("utf-8")).hexdigest()


def esta_aprovado(projeto_id: int | None) -> bool:
    """R-068: projeto novo/não salvo NUNCA é aprovado (nasce rascunho).
    OS F11.5 #24: a aprovação vale para a VERSÃO aprovada — se o conteúdo
    salvo mudou por QUALQUER porta (restaurar versão antiga, importar), o
    hash não bate e a marca RASCUNHO volta sozinha."""
    if projeto_id is None:
        return False
    try:
        from app.core.repositories import ConfigRepositorio
        db = Database().init()
        try:
            with db.Session() as s:
                mapa = ConfigRepositorio(s).get("projetos.aprovados") or {}
                valor = mapa.get(str(projeto_id))
                if not valor:
                    return False
                if valor is True:              # aprovação antiga (pré-#24)
                    return True
                return valor == _hash_estado_salvo(s, projeto_id)
        finally:
            db.engine.dispose()
    except Exception:
        return False


def _set_aprovado(projeto_id: int, valor: bool) -> None:
    try:
        from app.core.repositories import ConfigRepositorio
        db = Database().init()
        try:
            with db.Session() as s:
                repo = ConfigRepositorio(s)
                mapa = repo.get("projetos.aprovados") or {}
                if valor:
                    # #24: guarda o hash da versão — não um "True" eterno
                    mapa[str(projeto_id)] = (
                        _hash_estado_salvo(s, projeto_id) or True)
                else:
                    mapa.pop(str(projeto_id), None)
                repo.set("projetos.aprovados", mapa)
                s.commit()
        finally:
            db.engine.dispose()
    except Exception:
        pass


def registrar_ultimo_aberto(projeto_id: int) -> None:
    """FASE 2 (passos 47-48): a faixa "Continuar de onde parei" do Início.
    Chamado em TODO caminho de abertura (Mesa/Fábrica/dashboard/duplicar)."""
    try:
        from app.core.repositories import ConfigRepositorio
        db = Database().init()
        try:
            with db.Session() as s:
                ConfigRepositorio(s).set("inicio.ultimo_projeto",
                                         int(projeto_id))
                s.commit()
        finally:
            db.engine.dispose()
    except Exception:
        pass                             # conforto, não requisito


def ultimo_aberto() -> dict | None:
    """O resumo do último projeto aberto (ou None se sumiu/nunca houve)."""
    try:
        from app.core.repositories import ConfigRepositorio
        db = Database().init()
        try:
            with db.Session() as s:
                pid = ConfigRepositorio(s).get("inicio.ultimo_projeto")
        finally:
            db.engine.dispose()
        if not pid:
            return None
        return next((p for p in listar_projetos() if p["id"] == int(pid)),
                    None)
    except Exception:
        return None


def marcar_status(projeto_id: int, status: str) -> None:
    """FASE 2 (passos 36-37): transições — exportar marca "exportado";
    "pronto"/"publicado" são gestos humanos do botão direito."""
    if status not in STATUS_VALIDOS:
        raise ValueError(f"status inválido: {status}")
    db = Database().init()
    try:
        with db.Session() as s:
            row = s.get(ProjetoSalvo, projeto_id)
            if row is not None:
                row.status = status
                s.commit()
    finally:
        db.engine.dispose()


def abrir_projeto(projeto_id: int) -> ProjetoAberto | None:
    """Descongela: devolve o projeto EXATAMENTE como foi salvo."""
    db = Database().init()
    try:
        with db.Session() as s:
            row = s.get(ProjetoSalvo, projeto_id)
            if row is None:
                return None
            dados = row.get_slots()
            pasta = _pasta(row.uuid)
            layout = LayoutDef.from_dict(dados["layout"])
            layout.arquivo_fundo = _resolver(pasta, layout.arquivo_fundo)
            for pag in layout.paginas:                      # D8.6
                pag.arquivo_fundo = _resolver(pasta, pag.arquivo_fundo)
            itens = []
            for d in dados.get("itens", []):
                d = dict(d)
                d["imagem"] = _resolver(pasta, d.get("imagem"))
                d["imagens"] = [_resolver(pasta, c)
                                for c in (d.get("imagens") or [])]   # F7.1
                origens = []
                for origem in (d.get("origem_composto") or []):      # F7.2
                    org = dict(origem)
                    org["imagem"] = _resolver(pasta, org.get("imagem"))
                    org["imagens"] = [_resolver(pasta, c)
                                      for c in (org.get("imagens") or [])]
                    origens.append(org)
                d["origem_composto"] = origens
                itens.append(d)
            # F7.3: overrides descongelam com a foto resolvida p/ a UI
            overrides: dict = {}
            try:
                brutos = json.loads(row.overrides_json or "{}")
            except json.JSONDecodeError:
                brutos = {}
            for sid, ov in brutos.items():
                if not isinstance(ov, dict) or not ov:
                    continue
                ov = dict(ov)
                if ov.get("imagem"):
                    ov["imagem"] = _resolver(pasta, ov["imagem"])
                overrides[sid] = ov
            return ProjetoAberto(
                id=row.id,
                nome=row.nome,
                evento=row.evento,
                tipo=dados.get("tipo", "TABLOIDE"),
                layout=layout,
                itens=itens,
                validade_oferta=dados.get("validade_oferta"),
                criado_em=row.criado_em.strftime("%d/%m/%Y %H:%M")
                if row.criado_em else "",
                mapa=dados.get("mapa", {}),
                overrides=overrides,
            )
    finally:
        db.engine.dispose()


def listar_projetos() -> list[dict]:
    """Resumo plano para a UI (agrupável por evento no Dashboard)."""
    db = Database().init()
    try:
        with db.Session() as s:
            rows = s.execute(select(ProjetoSalvo).where(
                ProjetoSalvo.excluido_em.is_(None)).order_by(
                ProjetoSalvo.evento, ProjetoSalvo.criado_em.desc())).scalars()
            from datetime import datetime
            resumo = []
            for r in rows:
                mini = _pasta(r.uuid) / "miniatura.png"
                resumo.append({
                    "id": r.id, "nome": r.nome, "evento": r.evento or "",
                    "tipo": r.get_slots().get("tipo", "TABLOIDE"),
                    "criado_em": r.criado_em.strftime("%d/%m/%Y %H:%M")
                    if r.criado_em else "",
                    # RG-35: p/ a prateleira "Ofertas da semana"
                    "criado_ha_dias": ((datetime.now() - r.criado_em).days
                                       if r.criado_em else 9999),
                    "miniatura": str(mini) if mini.exists() else None,
                    # FASE 2 (passo 35): banco antigo sem a coluna → rascunho
                    "status": r.status or "rascunho",
                    "favorito": bool(getattr(r, "favorito", False)),
                })
            return resumo
    finally:
        db.engine.dispose()


def itens_das_edicoes_recentes(limite: int = 4) -> list[list[dict]]:
    """R-059: os itens (ItemMesa.to_dict) das últimas `limite` edições salvas,
    da mais ANTIGA para a mais recente — insumo do alerta de repetição.
    Só edições vivas (não excluídas)."""
    db = Database().init()
    try:
        with db.Session() as s:
            rows = s.execute(select(ProjetoSalvo).where(
                ProjetoSalvo.excluido_em.is_(None)).order_by(
                ProjetoSalvo.criado_em.desc())).scalars().all()
            edicoes = [list(r.get_slots().get("itens", []))
                       for r in rows[:limite]]
        edicoes.reverse()                 # mais antiga → mais recente
        return edicoes
    finally:
        db.engine.dispose()


def historico_edicoes(limite: int | None = None) -> list[dict]:
    """R-115/120/121 (Fase 11): as edições salvas vivas — mais ANTIGA→recente —
    com DATA e evento preservados, para a inteligência (histórico de preço,
    ranking, memória sazonal). Só leitura, não toca o acervo.

    Cada dict: {id, nome, evento, tipo, criado_em (datetime|None), itens (dicts)}.
    """
    db = Database().init()
    try:
        with db.Session() as s:
            rows = s.execute(select(ProjetoSalvo).where(
                ProjetoSalvo.excluido_em.is_(None)).order_by(
                ProjetoSalvo.criado_em.desc())).scalars().all()
            if limite:
                rows = rows[:limite]
            out = []
            for r in rows:
                dados = r.get_slots()
                out.append({
                    "id": r.id, "nome": r.nome, "evento": r.evento or "",
                    "tipo": dados.get("tipo", "TABLOIDE"),
                    "criado_em": r.criado_em,          # datetime | None
                    "itens": list(dados.get("itens", [])),
                })
        out.reverse()                                  # mais antiga → recente
        return out
    finally:
        db.engine.dispose()


def renomear_projeto(projeto_id: int, novo_nome: str,
                     novo_evento: str | None = None) -> None:
    db = Database().init()
    try:
        with db.Session() as s:
            row = s.get(ProjetoSalvo, projeto_id)
            if row is not None:
                row.nome = novo_nome
                if novo_evento is not None:
                    row.evento = novo_evento.strip() or None
                s.commit()
    finally:
        db.engine.dispose()


def duplicar_projeto(projeto_id: int, novo_nome: str) -> int | None:
    """Copiar um antigo para fazer o novo (linha + pasta de arquivos)."""
    db = Database().init()
    try:
        with db.Session() as s:
            origem = s.get(ProjetoSalvo, projeto_id)
            if origem is None:
                return None
            copia = ProjetoSalvo(
                nome=novo_nome, uuid=str(_uuid.uuid4()),
                layout_id=origem.layout_id, evento=origem.evento,
                evento_id=origem.evento_id,
                estado_slots=origem.estado_slots,
                overrides_json=origem.overrides_json,
                status="rascunho",       # FASE 2 (passo 44): cópia nasce crua
            )
            s.add(copia)
            s.flush()
            velha, nova = _pasta(origem.uuid), _pasta(copia.uuid)
            if velha.exists():
                # caminhos são RELATIVOS (I3): copiar a pasta basta — o
                # duplicado enxerga os PRÓPRIOS arquivos, nunca os do original
                shutil.copytree(velha, nova)
            s.commit()
            return copia.id
    finally:
        db.engine.dispose()


def excluir_projeto(projeto_id: int) -> None:
    """FASE 2 (passo 82): excluir da UI é SOFT — o projeto vai para a
    lixeira do Cofre por 30 dias (pasta intacta, versões junto — passo 63);
    a morte real é a purga ou o 'Excluir agora' de lá."""
    from app.core.lixeira import excluir_suave
    excluir_suave("projeto", projeto_id)

"""
Persistência de layout (checkpoint de consolidação)
===================================================
Liga o `LayoutDef` (modelo de renderização) à tabela `Layout` do banco, via
`estrutura_json`. Sem isso, o trabalho do editor seria efêmero.

**Arte de fundo (E-A3 do Bloco E, I3 na raiz):** o banco guarda a arte
RELATIVA à pasta gerenciada ``<raiz>/layouts/`` — importar arte pelo Ateliê
COPIA o arquivo para lá. Salvar interna (``internar_arte``); carregar
resolve de volta para caminho usável (``resolver_arte``); layouts antigos
com caminho de máquina migram na abertura (``migrar_artes_absolutas``).
A relativização na fronteira do pacote (portabilidade) continua como defesa
em profundidade.
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.models import Layout
from app.core.paths import SystemRoot
from app.rendering.model import LayoutDef


def _raiz(raiz) -> SystemRoot:
    if isinstance(raiz, SystemRoot):
        return raiz
    return SystemRoot(raiz) if raiz else SystemRoot()


def resolver_arte(caminho: str | None, raiz=None) -> str | None:
    """Arte do banco → caminho usável pela composição/miniatura.

    Relativo mora em ``layouts/``; absoluto legado (pré-migração) passa
    direto; relativo que NÃO existe na pasta fica como veio — o rastro
    permanece visível e o pré-voo acusa a arte sumida (I2).
    """
    if not caminho:
        return None
    p = Path(caminho)
    if p.is_absolute():
        return caminho
    interno = _raiz(raiz).layouts / caminho
    return str(interno) if interno.exists() else caminho


def internar_arte(caminho: str | None, raiz=None) -> str | None:
    """Arte de fora → cópia em ``layouts/`` + caminho RELATIVO para o banco.

    Já-relativo da pasta fica como está; absoluto que já mora na pasta só
    relativiza (sem copiar); mesmo nome com bytes diferentes ganha sufixo;
    arte sumida do disco mantém o rastro (nunca se apaga referência em
    silêncio).
    """
    if not caminho:
        return None
    pasta = _raiz(raiz).layouts
    p = Path(caminho)
    if not p.is_absolute():
        if (pasta / caminho).exists():
            return Path(caminho).as_posix()   # já é da pasta gerenciada
        # relativo ao diretório de trabalho (ex.: arte semeada) → interna
    try:
        return p.resolve().relative_to(pasta.resolve()).as_posix()
    except (ValueError, OSError):
        pass
    if not p.is_file():
        return caminho                        # sumida: o rastro fica
    pasta.mkdir(parents=True, exist_ok=True)
    destino = pasta / p.name
    n = 2
    while destino.exists() and destino.read_bytes() != p.read_bytes():
        destino = pasta / f"{p.stem}_{n}{p.suffix}"
        n += 1
    if not destino.exists():
        shutil.copy(p, destino)
    return destino.name


def _internar_estrutura(layout_def: LayoutDef, raiz=None) -> tuple[str | None, str]:
    """(arquivo_fundo internado, estrutura_json internada) — sem mutar o LayoutDef."""
    estrutura = layout_def.to_dict()          # dicts frescos: mutação é local
    if "arquivo_fundo" in estrutura:
        estrutura["arquivo_fundo"] = internar_arte(
            estrutura.get("arquivo_fundo"), raiz)
    for pag in estrutura.get("paginas", []):
        if isinstance(pag, dict) and pag.get("arquivo_fundo"):
            pag["arquivo_fundo"] = internar_arte(pag["arquivo_fundo"], raiz)
    return (internar_arte(layout_def.arquivo_fundo, raiz),
            json.dumps(estrutura, ensure_ascii=False))


def salvar_layout(
    session: Session,
    nome: str,
    layout_def: LayoutDef,
    *,
    tipo_midia: str = "TABLOIDE",
    layout_id: int | None = None,
    raiz=None,
) -> Layout:
    """Cria ou atualiza um Layout no banco a partir de um LayoutDef.

    A arte é internada (E-A3): copiada para ``layouts/`` e gravada relativa.
    O ``layout_def`` do chamador NÃO é alterado (segue usável na tela).
    """
    fundo, estrutura = _internar_estrutura(layout_def, raiz)
    if layout_id is not None:
        row = session.get(Layout, layout_id)
    else:
        row = session.execute(select(Layout).where(Layout.nome == nome)).scalar_one_or_none()
    if row is None:
        row = Layout(nome=nome, tipo_midia=tipo_midia)
        session.add(row)
    row.nome = nome
    row.arquivo_fundo = fundo
    row.estrutura_json = estrutura
    session.flush()
    return row


def carregar_layout(session: Session, layout_id: int,
                    raiz=None) -> LayoutDef | None:
    """Reconstrói o LayoutDef a partir de um Layout salvo (arte resolvida)."""
    row = session.get(Layout, layout_id)
    if row is None or not row.estrutura_json:
        return None
    from app.rendering.migracao import migrar_papeis_texto_dict
    dados = json.loads(row.estrutura_json)
    migrar_papeis_texto_dict(dados)          # RG-57: migração de carona ao abrir
    ldef = LayoutDef.from_dict(dados)
    ldef.arquivo_fundo = resolver_arte(ldef.arquivo_fundo, raiz)
    for pag in ldef.paginas:
        pag.arquivo_fundo = resolver_arte(pag.arquivo_fundo, raiz)
    return ldef


def migrar_artes_absolutas(session: Session, raiz=None) -> list[str]:
    """E-A3: layouts antigos com caminho de MÁQUINA migram para ``layouts/``.

    Roda na abertura do app; idempotente (quem já é relativo não é tocado).
    Devolve avisos nominais: o que migrou e o que não deu (arte sumida —
    o rastro antigo fica e o aviso se repete até o humano resolver).
    """
    root = _raiz(raiz)
    avisos: list[str] = []
    for row in listar_layouts(session):
        estrutura = row.get_estrutura()
        paginas = [p for p in estrutura.get("paginas", [])
                   if isinstance(p, dict)]
        caminhos = ([row.arquivo_fundo, estrutura.get("arquivo_fundo")]
                    + [p.get("arquivo_fundo") for p in paginas])
        if not any(c and Path(c).is_absolute() for c in caminhos):
            continue                          # já migrado (ou sem arte)
        mudou = False
        novo = internar_arte(row.arquivo_fundo, root)
        mudou |= novo != row.arquivo_fundo
        row.arquivo_fundo = novo
        if "arquivo_fundo" in estrutura:
            novo = internar_arte(estrutura.get("arquivo_fundo"), root)
            mudou |= novo != estrutura.get("arquivo_fundo")
            estrutura["arquivo_fundo"] = novo
        for p in paginas:
            if p.get("arquivo_fundo"):
                novo = internar_arte(p["arquivo_fundo"], root)
                mudou |= novo != p["arquivo_fundo"]
                p["arquivo_fundo"] = novo
        if mudou:
            row.estrutura_json = json.dumps(estrutura, ensure_ascii=False)
            avisos.append(f"“{row.nome}”: arte movida para a pasta do "
                          "sistema (layouts/)")
        else:
            avisos.append(f"“{row.nome}”: a arte do caminho antigo não está "
                          "no disco — mantive o rastro para você resolver")
    session.flush()
    return avisos


def listar_layouts(session: Session) -> list[Layout]:
    # FASE 2 (passo 83): a lixeira esconde os excluídos das listas
    return list(session.execute(select(Layout).where(
        Layout.excluido_em.is_(None)).order_by(Layout.nome)).scalars())


def renomear_layout(session: Session, layout_id: int, novo_nome: str) -> Layout | None:
    row = session.get(Layout, layout_id)
    if row is not None:
        row.nome = novo_nome
        session.flush()
    return row


def duplicar_layout(session: Session, layout_id: int, novo_nome: str) -> Layout | None:
    """Cópia integral (estrutura + arte + tipo) com outro nome."""
    origem = session.get(Layout, layout_id)
    if origem is None:
        return None
    copia = Layout(
        nome=novo_nome,
        arquivo_fundo=origem.arquivo_fundo,
        tipo_midia=origem.tipo_midia,
        estrutura_json=origem.estrutura_json,
    )
    session.add(copia)
    session.flush()
    return copia


def excluir_layout(session: Session, layout_id: int) -> None:
    row = session.get(Layout, layout_id)
    if row is not None:
        session.delete(row)
        session.flush()

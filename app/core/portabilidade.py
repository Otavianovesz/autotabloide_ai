"""
Portabilidade — pacote .atpkg e mesclagem com REMAP DE IDS (D-B1 / F7.4-núcleo)
===============================================================================
A promessa "trabalhar em casa e no mercado": exportar TUDO num arquivo único
(`.atpkg`, um zip) e importar noutro PC **mesclando** com o que já existe lá.

O perigo que este módulo trava (I1 aplicado ao banco): ``produto_id`` é
autoincrement — o id 12 de casa NÃO é o id 12 do mercado, e a biblioteca de
imagens é indexada por pasta ``produto_id/``. Uma mesclagem ingênua trocaria
as fotos entre produtos. Regras:

- Produto casa por **CHAVE NATURAL** (nome_sanitizado normalizado + marca),
  NUNCA por id. Produto novo ganha id NOVO no destino e a pasta da biblioteca
  é **renomeada no ato do import** conforme o remap.
- **Verificação pós-import obrigatória**: a ``atual.png`` de cada produto
  importado tem que ser BYTE-IDÊNTICA à do pacote — se não for, NADA é
  gravado (rollback + erro nominal).
- **Conflito** (mesma chave natural, dados divergentes) NUNCA se resolve em
  silêncio (I2): entra no relatório de mesclagem e o humano decide por item
  (manter local / usar do pacote / manter ambos como variantes).
- Projetos congelados viajam como estão (pasta ``projetos/<uuid>/`` é
  autossuficiente e relativa — uuid não colide).
- O pacote não carrega NENHUM caminho de máquina (I3): a arte dos layouts é
  copiada para ``layouts_arte/`` e os caminhos viram relativos na cópia do
  banco que viaja.

Fluxo em duas fases (a UI mostra o relatório entre elas):

    analise = analisar_pacote("ofertas.atpkg")      # nada é gravado
    ...humano decide os conflitos...
    rel = aplicar_importacao(analise, decisoes)     # grava com verificação
    analise.fechar()
"""

from __future__ import annotations

import json
import shutil
import sqlite3
import tempfile
import unicodedata
import zipfile
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal, InvalidOperation
from enum import Enum
from pathlib import Path
from typing import Callable

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker

from app.core.cofre import _backup_sqlite
from app.core.paths import SystemRoot

VERSAO_SCHEMA = 1
_SEM_PROGRESSO: Callable[[str], None] = lambda _msg: None


def _root(raiz: SystemRoot | Path | str | None) -> SystemRoot:
    if isinstance(raiz, SystemRoot):
        return raiz
    return SystemRoot(raiz).criar_estrutura() if raiz else SystemRoot().criar_estrutura()


# --- chave natural (I1: identidade, nunca id) -------------------------------------

def _norm(txt: str | None) -> str:
    """minúsculo, sem acento, espaços colapsados — a identidade textual."""
    s = unicodedata.normalize("NFD", (txt or "").strip().lower())
    s = "".join(c for c in s if not unicodedata.combining(c))
    return " ".join(s.split())


def chave_natural(nome: str | None, marca: str | None) -> tuple[str, str]:
    return (_norm(nome), _norm(marca))


# --- exportar ----------------------------------------------------------------------

def _relativizar_layouts_no_pacote(banco: Path, staging: Path,
                                   root: SystemRoot) -> list[str]:
    """Troca a arte dos layouts por cópias em layouts_arte/ NA CÓPIA do banco.

    Desde a E-A3 o banco vivo guarda a arte RELATIVA à pasta ``layouts/`` da
    raiz (resolvida aqui pela ``root`` de ORIGEM); caminho absoluto legado
    ainda é aceito. No pacote, tudo vira ``layouts_arte/`` (I3 — nada de
    caminho de máquina). Devolve avisos (arte sumida).
    """
    avisos: list[str] = []
    destino_artes = staging / "layouts_arte"
    conn = sqlite3.connect(str(banco))
    try:
        rows = conn.execute(
            "SELECT id, nome, arquivo_fundo, estrutura_json FROM layouts").fetchall()
        for lid, nome, fundo_col, estrutura_json in rows:
            try:
                estrutura = json.loads(estrutura_json or "{}")
            except json.JSONDecodeError:
                estrutura = {}
            mapa: dict[str, str] = {}          # caminho original → token relativo
            seq = 0

            def _token(caminho: str | None) -> str | None:
                nonlocal seq
                if not caminho:
                    return None
                if caminho.startswith("layouts_arte/"):
                    return caminho             # já relativizado (re-export)
                if caminho in mapa:
                    return mapa[caminho]
                p = Path(caminho)
                if not p.is_absolute():        # E-A3: relativo à raiz de origem
                    p = root.layouts / caminho
                if not p.is_file():
                    avisos.append(
                        f"layout “{nome}”: arte “{p.name}” não está no disco — "
                        "o layout viaja sem essa arte")
                    mapa[caminho] = None
                    return None
                seq += 1
                token = f"layouts_arte/l{lid}_{seq}{p.suffix.lower() or '.png'}"
                destino_artes.mkdir(parents=True, exist_ok=True)
                shutil.copy(p, staging / token)
                mapa[caminho] = token
                return token

            novo_col = _token(fundo_col)
            if "arquivo_fundo" in estrutura:
                estrutura["arquivo_fundo"] = _token(estrutura.get("arquivo_fundo"))
            for pag in estrutura.get("paginas", []):
                if isinstance(pag, dict) and pag.get("arquivo_fundo"):
                    pag["arquivo_fundo"] = _token(pag.get("arquivo_fundo"))
            conn.execute(
                "UPDATE layouts SET arquivo_fundo=?, estrutura_json=? WHERE id=?",
                (novo_col, json.dumps(estrutura, ensure_ascii=False), lid))
        conn.commit()
    finally:
        conn.close()
    return avisos


def _contagens(banco: Path) -> dict[str, int]:
    conn = sqlite3.connect(f"file:{banco.as_posix()}?mode=ro", uri=True)
    try:
        def _n(t: str) -> int:
            try:
                return conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
            except sqlite3.OperationalError:
                return 0
        return {"produtos": _n("produtos"), "aliases": _n("produto_aliases"),
                "categorias": _n("categorias"), "layouts": _n("layouts"),
                "projetos": _n("projetos_salvos"), "config": _n("config")}
    finally:
        conn.close()


def exportar_pacote(destino: str | Path,
                    raiz: SystemRoot | Path | str | None = None,
                    progresso: Callable[[str], None] = _SEM_PROGRESSO) -> Path:
    """Empacota banco + biblioteca + fontes + projetos num .atpkg (zip)."""
    root = _root(raiz)
    if not root.caminho_banco.exists():
        raise FileNotFoundError("não há banco para exportar ainda")
    destino = Path(destino)
    if destino.suffix.lower() != ".atpkg":
        destino = destino.with_suffix(".atpkg")

    with tempfile.TemporaryDirectory(prefix="atpkg_exp_") as tmp:
        staging = Path(tmp)
        progresso("Copiando o banco (cópia consistente)…")
        banco_pkg = staging / "banco" / "core.db"
        _backup_sqlite(root.caminho_banco, banco_pkg)
        progresso("Relativizando a arte dos layouts (I3)…")
        avisos = _relativizar_layouts_no_pacote(banco_pkg, staging, root)

        contagens = _contagens(banco_pkg)
        pastas_produto = [p for p in sorted(root.biblioteca_imagens.iterdir())
                          if p.is_dir() and p.name.isdigit()] \
            if root.biblioteca_imagens.exists() else []
        contagens["imagens"] = len(pastas_produto)
        fontes = [f for f in root.fontes.iterdir() if f.is_file()] \
            if root.fontes.exists() else []
        contagens["fontes"] = len(fontes)
        manifesto = {
            "formato": "atpkg",
            "versao_schema": VERSAO_SCHEMA,
            "criado_em": datetime.now().isoformat(timespec="seconds"),
            "contagens": contagens,
            "avisos": avisos,
        }

        progresso("Gravando o pacote…")
        destino.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(destino, "w", zipfile.ZIP_DEFLATED) as z:
            z.writestr("manifesto.json",
                       json.dumps(manifesto, ensure_ascii=False, indent=2))
            z.write(banco_pkg, "banco/core.db")
            artes = staging / "layouts_arte"
            if artes.exists():
                for f in sorted(artes.iterdir()):
                    z.write(f, f"layouts_arte/{f.name}")
            for pasta in pastas_produto:           # só pastas de produto (id/)
                for f in sorted(pasta.rglob("*")):
                    if f.is_file():
                        rel = f.relative_to(root.biblioteca_imagens).as_posix()
                        z.write(f, f"biblioteca_imagens/{rel}")
            for f in fontes:
                z.write(f, f"fontes/{f.name}")
            if root.projetos.exists():
                for f in sorted(root.projetos.rglob("*")):
                    if f.is_file():
                        rel = f.relative_to(root.projetos).as_posix()
                        z.write(f, f"projetos/{rel}")
    return destino


# --- analisar (fase 1: nada é gravado) ---------------------------------------------

class Decisao(str, Enum):
    MANTER_LOCAL = "manter_local"
    USAR_PACOTE = "usar_pacote"
    MANTER_AMBOS = "manter_ambos"        # produto vira variante no destino


@dataclass
class Conflito:
    """Mesma chave natural, dados divergentes — o humano decide (I2)."""

    id_decisao: str                      # "produto:<nome>|<marca>" | "layout:<nome>"
    tipo: str                            # "produto" | "layout"
    rotulo: str                          # nome legível para a UI
    campos: list[str]                    # o que diverge ("preço", "foto"…)
    local: dict = field(default_factory=dict)     # valores locais (exibição)
    pacote: dict = field(default_factory=dict)    # valores do pacote (exibição)
    id_local: int = 0
    id_origem: int = 0


@dataclass
class AnalisePacote:
    """Resultado da fase 1 — alimenta o relatório de mesclagem da UI."""

    caminho: str = ""
    manifesto: dict = field(default_factory=dict)
    novos: list[dict] = field(default_factory=list)       # produtos só do pacote
    identicos: list[str] = field(default_factory=list)    # nomes já iguais aqui
    conflitos: list[Conflito] = field(default_factory=list)
    projetos_novos: list[dict] = field(default_factory=list)   # {uuid, nome}
    projetos_existentes: int = 0
    layouts_novos: list[str] = field(default_factory=list)
    fontes_novas: list[str] = field(default_factory=list)
    config_novas: list[str] = field(default_factory=list)
    config_diferentes: list[str] = field(default_factory=list)  # mantidas locais
    avisos: list[str] = field(default_factory=list)
    _tmp: tempfile.TemporaryDirectory | None = None
    _dir: Path | None = None
    _raiz: str | None = None

    @property
    def dir(self) -> Path:
        if self._dir is None:
            raise RuntimeError("análise já fechada")
        return self._dir

    def fechar(self) -> None:
        if self._tmp is not None:
            self._tmp.cleanup()
            self._tmp = None
            self._dir = None

    def __enter__(self) -> "AnalisePacote":
        return self

    def __exit__(self, *exc) -> None:
        self.fechar()


def _sessao_pacote(banco: Path):
    eng = create_engine(f"sqlite:///{banco}", future=True)
    return eng, sessionmaker(bind=eng, class_=Session, expire_on_commit=False)


def _plano_produto(p, nome_categoria: str | None) -> dict:
    """Produto ORM → dicionário plano e comparável (independe da sessão)."""
    return {
        "id": p.id,
        "nome": p.nome_sanitizado,
        "nome_bruto": p.nome_bruto,
        "marca": p.marca,
        "sabor": p.sabor,
        "peso_valor": str(p.peso_valor.normalize()) if p.peso_valor is not None else None,
        "peso_unidade": p.peso_unidade,
        "categoria": nome_categoria,
        "preco": str(p.preco_atual) if p.preco_atual is not None else None,
        "validade": p.validade_item.isoformat() if p.validade_item else None,
        "alcool": bool(p.bebida_alcoolica),
        "mais18": bool(p.selo_mais18),
        "marca_propria": bool(p.marca_propria),
        "caminho_imagem": p.caminho_imagem,
    }


def _decimal(txt: str | None) -> Decimal | None:
    if txt is None:
        return None
    try:
        return Decimal(txt)
    except InvalidOperation:
        return None


def _bytes_ou_none(caminho: Path) -> bytes | None:
    return caminho.read_bytes() if caminho.is_file() else None


def _foto_local(root: SystemRoot, caminho_imagem: str | None) -> Path | None:
    if not caminho_imagem:
        return None
    p = Path(caminho_imagem)
    return p if p.is_absolute() else root.biblioteca_imagens / p


def _campos_divergentes(local: dict, pacote: dict,
                        foto_local: bytes | None,
                        foto_pacote: bytes | None) -> list[str]:
    """Compara o que importa para o operador — cada divergência é nominal."""
    difere: list[str] = []
    if _decimal(local["preco"]) != _decimal(pacote["preco"]):
        difere.append("preço")
    if foto_local != foto_pacote:
        difere.append("foto")
    if _norm(local["categoria"]) != _norm(pacote["categoria"]):
        difere.append("categoria")
    if _norm(local["sabor"]) != _norm(pacote["sabor"]):
        difere.append("sabor")
    peso_l = (_decimal(local["peso_valor"]), _norm(local["peso_unidade"]))
    peso_p = (_decimal(pacote["peso_valor"]), _norm(pacote["peso_unidade"]))
    if peso_l != peso_p:
        difere.append("peso")
    if local["validade"] != pacote["validade"]:
        difere.append("validade")
    for campo, nome in (("alcool", "bebida alcoólica"), ("mais18", "selo +18"),
                        ("marca_propria", "marca própria")):
        if local[campo] != pacote[campo]:
            difere.append(nome)
    return difere


def _estrutura_sem_arte(estrutura_json: str | None) -> str:
    """Estrutura do layout SEM os caminhos de arte (que diferem por máquina)."""
    try:
        e = json.loads(estrutura_json or "{}")
    except json.JSONDecodeError:
        return estrutura_json or "{}"
    e.pop("arquivo_fundo", None)
    for pag in e.get("paginas", []):
        if isinstance(pag, dict):
            pag.pop("arquivo_fundo", None)
    return json.dumps(e, ensure_ascii=False, sort_keys=True)


def analisar_pacote(caminho: str | Path,
                    raiz: SystemRoot | Path | str | None = None,
                    progresso: Callable[[str], None] = _SEM_PROGRESSO) -> AnalisePacote:
    """Fase 1: abre o pacote e compara com o destino. NADA é gravado."""
    from app.core.database import Database
    from app.core.models import Categoria, Config, Layout, Produto, ProjetoSalvo

    caminho = Path(caminho)
    if not caminho.is_file():
        raise FileNotFoundError(f"pacote não encontrado: {caminho}")
    root = _root(raiz)

    tmp = tempfile.TemporaryDirectory(prefix="atpkg_imp_")
    analise = AnalisePacote(caminho=str(caminho), _tmp=tmp, _dir=Path(tmp.name),
                            _raiz=str(root.raiz))
    try:
        progresso("Abrindo o pacote…")
        with zipfile.ZipFile(caminho) as z:
            for nome in z.namelist():   # zip-slip: nada fora da pasta temporária
                p = Path(nome)
                if p.is_absolute() or ".." in p.parts:
                    raise ValueError(f"pacote com caminho suspeito: {nome!r}")
            z.extractall(analise.dir)
        man = analise.dir / "manifesto.json"
        if not man.is_file() or not (analise.dir / "banco" / "core.db").is_file():
            raise ValueError("isto não parece um pacote .atpkg (sem manifesto/banco)")
        analise.manifesto = json.loads(man.read_text(encoding="utf-8"))
        if analise.manifesto.get("formato") != "atpkg":
            raise ValueError("manifesto inválido — não é um pacote .atpkg")
        if int(analise.manifesto.get("versao_schema", 0)) > VERSAO_SCHEMA:
            raise ValueError(
                "pacote de uma versão MAIS NOVA do AutoTabloide — "
                "atualize o app antes de importar")
        analise.avisos.extend(analise.manifesto.get("avisos", []))

        progresso("Comparando com o banco daqui…")
        eng_p, Sess_p = _sessao_pacote(analise.dir / "banco" / "core.db")
        db_l = Database(root).init()
        try:
            with Sess_p() as sp, db_l.Session() as sl:
                cat_p = {c.id: c.nome for c in sp.execute(select(Categoria)).scalars()}
                cat_l = {c.id: c.nome for c in sl.execute(select(Categoria)).scalars()}
                locais: dict[tuple[str, str], dict] = {}
                for p in sl.execute(select(Produto).where(Produto.excluido_em.is_(None))).scalars():
                    locais[chave_natural(p.nome_sanitizado, p.marca)] = \
                        _plano_produto(p, cat_l.get(p.categoria_id))

                for p in sp.execute(select(Produto).where(Produto.excluido_em.is_(None))).scalars():
                    plano = _plano_produto(p, cat_p.get(p.categoria_id))
                    chave = chave_natural(p.nome_sanitizado, p.marca)
                    local = locais.get(chave)
                    if local is None:
                        analise.novos.append(plano)
                        continue
                    foto_p = _bytes_ou_none(
                        analise.dir / "biblioteca_imagens" / str(p.id) / "atual.png")
                    fl = _foto_local(root, local["caminho_imagem"])
                    foto_l = _bytes_ou_none(fl) if fl else None
                    campos = _campos_divergentes(local, plano, foto_l, foto_p)
                    if not campos:
                        analise.identicos.append(plano["nome"])
                        continue
                    analise.conflitos.append(Conflito(
                        id_decisao=f"produto:{chave[0]}|{chave[1]}",
                        tipo="produto",
                        rotulo=plano["nome"] + (f" ({plano['marca']})"
                                                if plano["marca"] else ""),
                        campos=campos,
                        local={"preço": local["preco"] or "—",
                               "categoria": local["categoria"] or "—",
                               "validade": local["validade"] or "—"},
                        pacote={"preço": plano["preco"] or "—",
                                "categoria": plano["categoria"] or "—",
                                "validade": plano["validade"] or "—"},
                        id_local=local["id"], id_origem=plano["id"],
                    ))

                # layouts: chave natural = nome
                lay_l = {_norm(r.nome): r for r in
                         sl.execute(select(Layout).where(Layout.excluido_em.is_(None))).scalars()}
                for r in sp.execute(select(Layout).where(Layout.excluido_em.is_(None))).scalars():
                    existente = lay_l.get(_norm(r.nome))
                    if existente is None:
                        analise.layouts_novos.append(r.nome)
                        continue
                    if (_estrutura_sem_arte(r.estrutura_json)
                            != _estrutura_sem_arte(existente.estrutura_json)
                            or r.tipo_midia != existente.tipo_midia):
                        analise.conflitos.append(Conflito(
                            id_decisao=f"layout:{_norm(r.nome)}",
                            tipo="layout", rotulo=r.nome,
                            campos=["estrutura do layout"],
                            id_local=existente.id, id_origem=r.id))

                # projetos congelados: chave natural = uuid (não colide)
                uuids_l = {r.uuid for r in
                           sl.execute(select(ProjetoSalvo).where(ProjetoSalvo.excluido_em.is_(None))).scalars()}
                for r in sp.execute(select(ProjetoSalvo).where(ProjetoSalvo.excluido_em.is_(None))).scalars():
                    if r.uuid in uuids_l:
                        analise.projetos_existentes += 1
                    else:
                        analise.projetos_novos.append(
                            {"uuid": r.uuid, "nome": r.nome})

                # config: chave nova entra; existente fica local (reportado)
                conf_l = {c.chave: c.valor_json for c in
                          sl.execute(select(Config)).scalars()}
                for c in sp.execute(select(Config)).scalars():
                    if c.chave not in conf_l:
                        analise.config_novas.append(c.chave)
                    elif (c.valor_json or "null") != (conf_l[c.chave] or "null"):
                        analise.config_diferentes.append(c.chave)
        finally:
            eng_p.dispose()
            db_l.engine.dispose()

        # fontes: por nome de arquivo; mesmo nome com bytes diferentes = aviso
        pasta_f = analise.dir / "fontes"
        if pasta_f.is_dir():
            for f in sorted(pasta_f.iterdir()):
                local_f = root.fontes / f.name
                if not local_f.exists():
                    analise.fontes_novas.append(f.name)
                elif local_f.read_bytes() != f.read_bytes():
                    analise.avisos.append(
                        f"fonte “{f.name}” difere da local — mantida a daqui")
        return analise
    except Exception:
        analise.fechar()
        raise


# --- aplicar (fase 2: grava com verificação byte a byte) ---------------------------

@dataclass
class RelatorioImportacao:
    """O que a mesclagem fez — visível, nominal, sem silêncio (I2)."""

    produtos_novos: list[str] = field(default_factory=list)
    conflitos_resolvidos: list[tuple[str, str]] = field(default_factory=list)
    variantes_criadas: list[str] = field(default_factory=list)
    aliases_importados: int = 0
    layouts_importados: list[str] = field(default_factory=list)
    projetos_importados: list[str] = field(default_factory=list)
    projetos_pulados: int = 0
    fontes_importadas: list[str] = field(default_factory=list)
    config_importadas: list[str] = field(default_factory=list)
    fotos_verificadas: int = 0
    avisos: list[str] = field(default_factory=list)

    def resumo(self) -> str:
        partes = []
        if self.produtos_novos:
            partes.append(f"{len(self.produtos_novos)} produtos novos")
        if self.conflitos_resolvidos:
            partes.append(f"{len(self.conflitos_resolvidos)} conflitos resolvidos")
        if self.variantes_criadas:
            partes.append(f"{len(self.variantes_criadas)} variantes")
        if self.projetos_importados:
            partes.append(f"{len(self.projetos_importados)} projetos")
        if self.layouts_importados:
            partes.append(f"{len(self.layouts_importados)} layouts")
        if self.fontes_importadas:
            partes.append(f"{len(self.fontes_importadas)} fontes")
        partes.append(f"{self.fotos_verificadas} fotos verificadas byte a byte")
        return "Mesclagem concluída: " + ", ".join(partes) + "."


def _nome_variante(session, nome: str, marca: str | None) -> str:
    """Nome único p/ 'manter ambos' — a variante ganha chave natural própria."""
    from app.core.models import Produto

    existentes = {chave_natural(p.nome_sanitizado, p.marca)
                  for p in session.execute(select(Produto).where(Produto.excluido_em.is_(None))).scalars()}
    candidato, n = f"{nome} (importado)", 2
    while chave_natural(candidato, marca) in existentes:
        candidato = f"{nome} (importado {n})"
        n += 1
    return candidato


def aplicar_importacao(analise: AnalisePacote,
                       decisoes: dict[str, Decisao] | None = None,
                       raiz: SystemRoot | Path | str | None = None,
                       progresso: Callable[[str], None] = _SEM_PROGRESSO,
                       ) -> RelatorioImportacao:
    """Fase 2: grava a mesclagem. Todo conflito EXIGE decisão (nada em silêncio);
    toda foto importada é verificada BYTE A BYTE antes do commit."""
    from app.core.database import Database
    from app.core.models import (
        Categoria,
        Config,
        Layout,
        Produto,
        ProdutoAlias,
        ProjetoSalvo,
    )

    decisoes = decisoes or {}
    pendentes = [c.rotulo for c in analise.conflitos
                 if c.id_decisao not in decisoes]
    if pendentes:
        raise ValueError(
            "conflitos sem decisão (I2 — nada se resolve em silêncio): "
            + "; ".join(pendentes))

    root = _root(raiz if raiz is not None else analise._raiz)
    rel = RelatorioImportacao()
    pastas_criadas: list[Path] = []
    verificar: list[tuple[str, Path, Path]] = []   # (rotulo, no_pacote, no_destino)
    # B-fix1: substituições em produto PRÉ-EXISTENTE têm que voltar se algo
    # falhar depois — senão o banco reverte e o disco fica com a foto trocada
    # (divergência disco×banco, a classe exata de bug que esta ordem caça).
    fotos_substituidas: list[tuple[Path, Path]] = []   # (atual, backup em versoes/)
    fotos_adicionadas: list[Path] = []                 # atual criada onde não havia

    eng_p, Sess_p = _sessao_pacote(analise.dir / "banco" / "core.db")
    db_l = Database(root).init()
    try:
        with Sess_p() as sp, db_l.Session() as sl:
            cat_p = {c.id: c.nome for c in sp.execute(select(Categoria)).scalars()}

            def _categoria_id(nome_cat: str | None) -> int | None:
                if not nome_cat:
                    return None
                row = next((c for c in sl.execute(select(Categoria)).scalars()
                            if _norm(c.nome) == _norm(nome_cat)), None)
                if row is None:
                    row = Categoria(nome=nome_cat)
                    sl.add(row)
                    sl.flush()
                return row.id

            def _copiar_biblioteca(id_origem: int, id_destino: int,
                                   rotulo: str) -> str | None:
                """A pasta da biblioteca RENOMEADA conforme o remap (D-B1)."""
                origem = analise.dir / "biblioteca_imagens" / str(id_origem)
                if not origem.is_dir():
                    return None
                destino = root.biblioteca_imagens / str(id_destino)
                if destino.exists():               # variante 2×? não sobrescrever
                    shutil.rmtree(destino)
                shutil.copytree(origem, destino)
                pastas_criadas.append(destino)
                if (origem / "atual.png").is_file():
                    verificar.append(
                        (rotulo, origem / "atual.png", destino / "atual.png"))
                    return f"{id_destino}/atual.png"
                return None

            def _produto_do_pacote(pp) -> Produto:
                return Produto(
                    nome_bruto=pp.nome_bruto,
                    nome_sanitizado=pp.nome_sanitizado,
                    marca=pp.marca, sabor=pp.sabor,
                    peso_valor=pp.peso_valor, peso_unidade=pp.peso_unidade,
                    categoria_id=_categoria_id(cat_p.get(pp.categoria_id)),
                    preco_atual=pp.preco_atual, validade_item=pp.validade_item,
                    bebida_alcoolica=bool(pp.bebida_alcoolica),
                    selo_mais18=bool(pp.selo_mais18),
                    marca_propria=bool(pp.marca_propria),
                    ean=pp.ean,                          # RG-41
                    imagens_json=pp.imagens_json,        # RG-28: relativo à
                    # pasta do produto — o remap renomeia a pasta, não a lista
                )

            # remap: produto do PACOTE (id de origem) → id no DESTINO
            remap: dict[int, int] = {}
            produtos_p = {p.id: p for p in sp.execute(select(Produto).where(Produto.excluido_em.is_(None))).scalars()}
            locais_por_chave = {
                chave_natural(p.nome_sanitizado, p.marca): p
                for p in sl.execute(select(Produto).where(Produto.excluido_em.is_(None))).scalars()}

            # E-A2: o acervo pode ter mudado ENTRE analisar e aplicar —
            # revalida as chaves antes de gravar: duplicata silenciosa jamais;
            # o erro é nominal e pede re-análise.
            criados = [d["nome"] for d in analise.novos
                       if chave_natural(d["nome"], d["marca"])
                       in locais_por_chave]
            sumiram, mudaram = [], []
            for c in analise.conflitos:
                if c.tipo != "produto":
                    continue
                row = sl.get(Produto, c.id_local)
                if row is None:
                    sumiram.append(c.rotulo)
                else:
                    k = chave_natural(row.nome_sanitizado, row.marca)
                    if f"produto:{k[0]}|{k[1]}" != c.id_decisao:
                        mudaram.append(c.rotulo)
            if criados or sumiram or mudaram:
                partes = []
                if criados:
                    partes.append("criados aqui depois da análise: "
                                  + ", ".join(criados))
                if sumiram:
                    partes.append("removidos depois da análise: "
                                  + ", ".join(sumiram))
                if mudaram:
                    partes.append("renomeados depois da análise: "
                                  + ", ".join(mudaram))
                raise ValueError(
                    "o acervo mudou entre a análise e a aplicação ("
                    + "; ".join(partes) + ") — re-analise o pacote")

            # 1) produtos novos — id NOVO no destino, pasta renomeada no ato
            novos_ids = {d["id"] for d in analise.novos}
            for d in analise.novos:
                progresso(f"Importando “{d['nome']}”…")
                pp = produtos_p[d["id"]]
                novo = _produto_do_pacote(pp)
                sl.add(novo)
                sl.flush()                        # nasce o id do destino
                novo.caminho_imagem = _copiar_biblioteca(
                    pp.id, novo.id, d["nome"])
                remap[pp.id] = novo.id
                rel.produtos_novos.append(d["nome"])

            # 2) idênticos e conflitos: mapear para o produto local
            for pp in produtos_p.values():
                if pp.id in novos_ids:
                    continue
                local = locais_por_chave.get(
                    chave_natural(pp.nome_sanitizado, pp.marca))
                if local is not None:
                    remap[pp.id] = local.id

            # 3) conflitos de produto — só com decisão explícita
            for c in [c for c in analise.conflitos if c.tipo == "produto"]:
                decisao = decisoes[c.id_decisao]
                pp = produtos_p[c.id_origem]
                progresso(f"Resolvendo “{c.rotulo}” ({decisao.value})…")
                if decisao is Decisao.MANTER_LOCAL:
                    pass                           # dados locais intocados
                elif decisao is Decisao.USAR_PACOTE:
                    local = sl.get(Produto, c.id_local)
                    local.nome_bruto = pp.nome_bruto
                    local.sabor = pp.sabor
                    local.peso_valor = pp.peso_valor
                    local.peso_unidade = pp.peso_unidade
                    local.categoria_id = _categoria_id(cat_p.get(pp.categoria_id))
                    local.preco_atual = pp.preco_atual
                    local.validade_item = pp.validade_item
                    local.bebida_alcoolica = bool(pp.bebida_alcoolica)
                    local.selo_mais18 = bool(pp.selo_mais18)
                    local.ean = pp.ean                        # RG-41
                    local.imagens_json = pp.imagens_json      # RG-28
                    local.marca_propria = bool(pp.marca_propria)
                    if "foto" in c.campos:
                        foto_pkg = (analise.dir / "biblioteca_imagens"
                                    / str(pp.id) / "atual.png")
                        if foto_pkg.is_file():
                            pasta = root.biblioteca_imagens / str(local.id)
                            atual = pasta / "atual.png"
                            if not pasta.exists():
                                pasta.mkdir(parents=True)
                                pastas_criadas.append(pasta)   # rmtree cobre tudo
                            elif atual.exists():   # a antiga vira versão
                                vdir = pasta / "versoes"
                                vdir.mkdir(parents=True, exist_ok=True)
                                ts = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
                                backup = vdir / f"{ts}_pre_import.png"
                                shutil.move(str(atual), backup)
                                fotos_substituidas.append((atual, backup))
                            else:                  # pasta existia, foto não
                                fotos_adicionadas.append(atual)
                            shutil.copy(foto_pkg, atual)
                            local.caminho_imagem = f"{local.id}/atual.png"
                            verificar.append((c.rotulo, foto_pkg, atual))
                        else:                      # pacote SEM foto: não apagar
                            rel.avisos.append(
                                f"“{c.rotulo}”: o pacote não tem foto — "
                                "a foto local foi mantida")
                else:                              # MANTER_AMBOS → variante
                    variante = _produto_do_pacote(pp)
                    variante.nome_sanitizado = _nome_variante(
                        sl, pp.nome_sanitizado, pp.marca)
                    sl.add(variante)
                    sl.flush()
                    variante.caminho_imagem = _copiar_biblioteca(
                        pp.id, variante.id, variante.nome_sanitizado)
                    remap[pp.id] = variante.id     # aliases seguem a variante
                    rel.variantes_criadas.append(variante.nome_sanitizado)
                rel.conflitos_resolvidos.append((c.rotulo, decisao.value))

            # 4) aliases (aprendizado é aditivo): seguem o remap, sem duplicar
            existentes_alias = {(a.produto_id, a.alias_raw) for a in
                                sl.execute(select(ProdutoAlias)).scalars()}
            for a in sp.execute(select(ProdutoAlias)).scalars():
                destino_id = remap.get(a.produto_id)
                if destino_id is None:
                    continue
                if (destino_id, a.alias_raw) in existentes_alias:
                    continue
                sl.add(ProdutoAlias(
                    alias_raw=a.alias_raw, produto_id=destino_id,
                    confianca=a.confianca, overrides_json=a.overrides_json,
                    usos=a.usos))
                existentes_alias.add((destino_id, a.alias_raw))
                rel.aliases_importados += 1

            # 5) layouts (novos + conflitos com "usar do pacote")
            def _instalar_arte(token: str | None, nome_layout: str) -> str | None:
                """layouts_arte/xxx do pacote → arquivo em <raiz>/layouts/.

                Devolve o caminho RELATIVO à pasta gerenciada (a convenção
                do banco desde a E-A3 — nada de caminho de máquina).
                """
                if not token or not str(token).startswith("layouts_arte/"):
                    return token                   # None (sem arte) passa direto
                origem = analise.dir / token
                if not origem.is_file():
                    rel.avisos.append(
                        f"layout “{nome_layout}”: arte ausente no pacote")
                    return None
                base = _norm(nome_layout).replace(" ", "_") or "layout"
                root.layouts.mkdir(parents=True, exist_ok=True)
                destino = root.layouts / f"{base}{origem.suffix}"
                n = 2
                while destino.exists() and \
                        destino.read_bytes() != origem.read_bytes():
                    destino = root.layouts / f"{base}_{n}{origem.suffix}"
                    n += 1
                if not destino.exists():
                    shutil.copy(origem, destino)
                return destino.name

            def _layout_com_arte_instalada(r) -> tuple[str | None, str]:
                try:
                    e = json.loads(r.estrutura_json or "{}")
                except json.JSONDecodeError:
                    e = {}
                col = _instalar_arte(r.arquivo_fundo, r.nome)
                if "arquivo_fundo" in e:
                    e["arquivo_fundo"] = _instalar_arte(
                        e.get("arquivo_fundo"), r.nome)
                for pag in e.get("paginas", []):
                    if isinstance(pag, dict) and pag.get("arquivo_fundo"):
                        pag["arquivo_fundo"] = _instalar_arte(
                            pag.get("arquivo_fundo"), r.nome)
                return col, json.dumps(e, ensure_ascii=False)

            lay_l = {_norm(r.nome): r for r in
                     sl.execute(select(Layout).where(Layout.excluido_em.is_(None))).scalars()}
            novos_layouts = {_norm(n) for n in analise.layouts_novos}
            for r in sp.execute(select(Layout).where(Layout.excluido_em.is_(None))).scalars():
                chave_lay = _norm(r.nome)
                if chave_lay in novos_layouts:
                    progresso(f"Importando layout “{r.nome}”…")
                    col, estrutura = _layout_com_arte_instalada(r)
                    row = Layout(nome=r.nome, arquivo_fundo=col,
                                 tipo_midia=r.tipo_midia,
                                 estrutura_json=estrutura)
                    sl.add(row)
                    sl.flush()
                    lay_l[chave_lay] = row
                    rel.layouts_importados.append(r.nome)
                    continue
                decisao = decisoes.get(f"layout:{chave_lay}")
                if decisao in (Decisao.USAR_PACOTE, Decisao.MANTER_AMBOS):
                    if decisao is Decisao.USAR_PACOTE:
                        alvo = lay_l[chave_lay]
                        col, estrutura = _layout_com_arte_instalada(r)
                        alvo.arquivo_fundo = col
                        alvo.tipo_midia = r.tipo_midia
                        alvo.estrutura_json = estrutura
                        rel.layouts_importados.append(f"{r.nome} (atualizado)")
                    else:
                        col, estrutura = _layout_com_arte_instalada(r)
                        # E-A1: dedup como no _nome_variante — reimportar com
                        # a mesma decisão não colide nomes
                        nome_novo, n = f"{r.nome} (importado)", 2
                        while _norm(nome_novo) in lay_l:
                            nome_novo = f"{r.nome} (importado {n})"
                            n += 1
                        row = Layout(nome=nome_novo, arquivo_fundo=col,
                                     tipo_midia=r.tipo_midia,
                                     estrutura_json=estrutura)
                        sl.add(row)
                        sl.flush()
                        lay_l[_norm(nome_novo)] = row
                        rel.layouts_importados.append(nome_novo)
                    rel.conflitos_resolvidos.append((r.nome, decisao.value))
                elif decisao is Decisao.MANTER_LOCAL:
                    rel.conflitos_resolvidos.append((r.nome, decisao.value))

            # 6) projetos congelados: por uuid; pasta viaja como está (relativa)
            layouts_p = {r.id: r for r in sp.execute(select(Layout).where(Layout.excluido_em.is_(None))).scalars()}
            uuids_novos = {d["uuid"] for d in analise.projetos_novos}
            for r in sp.execute(select(ProjetoSalvo).where(ProjetoSalvo.excluido_em.is_(None))).scalars():
                if r.uuid not in uuids_novos:
                    rel.projetos_pulados += 1
                    continue
                progresso(f"Importando projeto “{r.nome}”…")
                lay_origem = layouts_p.get(r.layout_id)
                nome_lay = lay_origem.nome if lay_origem else "Layout do projeto"
                ref = lay_l.get(_norm(nome_lay))
                if ref is None:                    # referência de origem (FK)
                    ref = Layout(nome=nome_lay,
                                 tipo_midia=lay_origem.tipo_midia
                                 if lay_origem else "TABLOIDE")
                    sl.add(ref)
                    sl.flush()
                    lay_l[_norm(nome_lay)] = ref
                sl.add(ProjetoSalvo(
                    nome=r.nome, uuid=r.uuid, layout_id=ref.id,
                    evento=r.evento, estado_slots=r.estado_slots,
                    overrides_json=r.overrides_json))
                origem_pasta = analise.dir / "projetos" / r.uuid
                destino_pasta = root.projetos / r.uuid
                if origem_pasta.is_dir() and not destino_pasta.exists():
                    shutil.copytree(origem_pasta, destino_pasta)
                    pastas_criadas.append(destino_pasta)
                rel.projetos_importados.append(r.nome)

            # 7) fontes novas (mesmo nome fica a local — avisado na análise)
            for nome_fonte in analise.fontes_novas:
                origem = analise.dir / "fontes" / nome_fonte
                if origem.is_file():
                    shutil.copy(origem, root.fontes / nome_fonte)
                    rel.fontes_importadas.append(nome_fonte)

            # 8) config: só chaves que NÃO existem aqui (a local sempre vence)
            for c in sp.execute(select(Config)).scalars():
                if c.chave in analise.config_novas:
                    sl.add(Config(chave=c.chave, valor_json=c.valor_json))
                    rel.config_importadas.append(c.chave)

            # 9) VERIFICAÇÃO OBRIGATÓRIA (D-B1): byte a byte, ANTES do commit
            progresso("Verificando as fotos byte a byte…")
            for rotulo, no_pacote, no_destino in verificar:
                if _bytes_ou_none(no_pacote) != _bytes_ou_none(no_destino):
                    raise RuntimeError(
                        f"verificação pós-import FALHOU: a foto de “{rotulo}” "
                        "no destino não é byte-idêntica à do pacote — "
                        "nada foi gravado")
                rel.fotos_verificadas += 1

            rel.avisos.extend(
                f"config “{k}” difere — mantida a local"
                for k in analise.config_diferentes)
            sl.commit()
            return rel
    except Exception:
        for pasta in pastas_criadas:               # desfaz o que foi ao disco
            shutil.rmtree(pasta, ignore_errors=True)
        for atual in fotos_adicionadas:            # foto que não existia: sai
            atual.unlink(missing_ok=True)
        # B-fix1: a foto local substituída VOLTA byte a byte do backup —
        # o disco tem que contar a mesma história que o banco revertido
        for atual, backup in fotos_substituidas:
            try:
                if backup.exists():
                    atual.unlink(missing_ok=True)
                    shutil.move(str(backup), str(atual))
            except OSError:
                import logging
                logging.getLogger(__name__).warning(
                    "não consegui devolver a foto original %s ao desfazer o "
                    "import — ela está guardada em %s", atual, backup)
        raise
    finally:
        eng_p.dispose()
        db_l.engine.dispose()

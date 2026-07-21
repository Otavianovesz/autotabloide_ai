"""
Cofre — backups do banco e modo seguro (D-B2 do Bloco D / F6.6)
===============================================================
Snapshot = cópia CONSISTENTE do core.db feita pela API de backup do próprio
SQLite (atravessa o WAL com segurança, sem precisar fechar o app). Cada
snapshot é um arquivo datado em ``backups/``:

    core_20260709_153000_auto.db        (automático, na abertura do app)
    core_20260709_161200_manual.db      (pelo botão do Cofre)

Rotação: só os snapshots **automáticos** rodam (padrão 10, configurável pela
chave ``backups.rotacao`` da Config); os manuais ficam até o humano apagar.

**Modo seguro**: ``inspecionar_snapshot`` abre o snapshot SOMENTE-LEITURA e
devolve o que há dentro (contagens, data) — o banco vivo não é tocado.
Restaurar é gesto EXPLÍCITO e o banco atual NUNCA some: antes de sobrescrever
ele vira um snapshot ``pre_restauracao`` (dá para desfazer a restauração).
"""

from __future__ import annotations

import re
import sqlite3
from datetime import datetime
from pathlib import Path

from app.core.paths import SystemRoot

ROTACAO_PADRAO = 10
_NOME_SNAPSHOT = re.compile(
    r"^core_(\d{8})_(\d{6})(?:_(\d+))?_([a-z0-9_-]+)\.db$")


def _root(raiz: SystemRoot | Path | str | None) -> SystemRoot:
    if isinstance(raiz, SystemRoot):
        return raiz
    return SystemRoot(raiz).criar_estrutura() if raiz else SystemRoot().criar_estrutura()


def _backup_sqlite(origem: Path, destino: Path) -> None:
    """Cópia consistente via API de backup do SQLite (segura com WAL aberto)."""
    destino.parent.mkdir(parents=True, exist_ok=True)
    src = sqlite3.connect(str(origem))
    try:
        dst = sqlite3.connect(str(destino))
        try:
            with dst:
                src.backup(dst)
        finally:
            dst.close()
    finally:
        src.close()


def criar_snapshot(raiz: SystemRoot | Path | str | None = None,
                   rotulo: str = "manual") -> Path:
    """Cria um snapshot datado do banco vivo e devolve o caminho dele."""
    root = _root(raiz)
    if not root.caminho_banco.exists():
        raise FileNotFoundError(
            f"banco não encontrado para o snapshot: {root.caminho_banco}")
    rotulo = re.sub(r"[^a-z0-9_-]+", "_", rotulo.strip().lower()) or "manual"
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    destino = root.backups / f"core_{ts}_{rotulo}.db"
    n = 1
    while destino.exists():                       # dois no mesmo segundo
        destino = root.backups / f"core_{ts}_{n}_{rotulo}.db"
        n += 1
    _backup_sqlite(root.caminho_banco, destino)
    return destino


def listar_snapshots(raiz: SystemRoot | Path | str | None = None) -> list[dict]:
    """Snapshots existentes, do mais novo para o mais velho (dados p/ a UI)."""
    root = _root(raiz)
    itens = []
    for arq in root.backups.glob("core_*.db"):
        m = _NOME_SNAPSHOT.match(arq.name)
        if not m:
            continue
        data, hora, seq, rotulo = m.groups()
        itens.append({
            "caminho": str(arq),
            "nome": arq.name,
            "rotulo": rotulo,
            "quando": f"{data[6:8]}/{data[4:6]}/{data[:4]} "
                      f"{hora[:2]}:{hora[2:4]}:{hora[4:6]}",
            # o contador desempata snapshots do MESMO segundo (maior = mais novo)
            "ordenacao": f"{data}{hora}{int(seq or 0):04d}",
            "tamanho_kb": max(1, arq.stat().st_size // 1024),
        })
    itens.sort(key=lambda d: (d["ordenacao"], d["nome"]), reverse=True)
    return itens


def _rotacao_configurada(root: SystemRoot) -> int:
    from app.core.database import Database
    from app.core.repositories import ConfigRepositorio

    db = Database(root).init()
    try:
        with db.Session() as s:
            valor = ConfigRepositorio(s).get("backups.rotacao", ROTACAO_PADRAO)
    finally:
        db.engine.dispose()
    try:
        return max(1, int(valor))
    except (TypeError, ValueError):
        return ROTACAO_PADRAO


def snapshot_automatico(raiz: SystemRoot | Path | str | None = None) -> Path | None:
    """Snapshot 'auto' na abertura do app + rotação (só dos automáticos)."""
    root = _root(raiz)
    if not root.caminho_banco.exists():
        return None                                # primeira execução, sem banco
    caminho = criar_snapshot(root, rotulo="auto")
    manter = _rotacao_configurada(root)
    autos = [s for s in listar_snapshots(root) if s["rotulo"] == "auto"]
    for velho in autos[manter:]:                   # mais novos primeiro
        Path(velho["caminho"]).unlink(missing_ok=True)
    return caminho


def excluir_snapshot(caminho: str | Path) -> None:
    Path(caminho).unlink(missing_ok=True)


def inspecionar_snapshot(caminho: str | Path) -> dict:
    """Modo seguro: olha DENTRO do snapshot sem tocar no banco vivo.

    Abre somente-leitura e devolve contagens — é o "abrir a partir de um
    snapshot" seguro: nada é sobrescrito até o humano mandar restaurar.
    """
    caminho = Path(caminho)
    if not caminho.exists():
        raise FileNotFoundError(f"snapshot não encontrado: {caminho}")
    conn = sqlite3.connect(f"file:{caminho.as_posix()}?mode=ro", uri=True)
    try:
        def _n(tabela: str) -> int:
            try:
                return conn.execute(f"SELECT COUNT(*) FROM {tabela}").fetchone()[0]
            except sqlite3.OperationalError:
                return 0                           # snapshot de schema mais antigo
        return {
            "produtos": _n("produtos"),
            "aliases": _n("produto_aliases"),
            "categorias": _n("categorias"),
            "layouts": _n("layouts"),
            "projetos": _n("projetos_salvos"),
            "config": _n("config"),
        }
    finally:
        conn.close()


def restaurar_snapshot(caminho: str | Path,
                       raiz: SystemRoot | Path | str | None = None) -> Path:
    """Volta o banco vivo para o snapshot. O banco ATUAL nunca some:
    vira um snapshot 'pre_restauracao' antes (restauração tem desfazer).

    Devolve o caminho do snapshot 'pre_restauracao' criado.
    """
    caminho = Path(caminho)
    inspecionar_snapshot(caminho)                  # valida que é um banco legível
    root = _root(raiz)
    guarda = criar_snapshot(root, rotulo="pre_restauracao")
    _backup_sqlite(caminho, root.caminho_banco)    # snapshot → vivo (via backup API)
    return guarda

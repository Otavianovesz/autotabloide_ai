"""
Diagnóstico para suporte (R-128 — FASE 3, passo 56)
====================================================
Gera um .zip que o Otaviano pode mandar para quem for ajudar, SEM dados
sensíveis: versões, contagens do acervo, nomes das chaves de configuração
(sem valores — neles moram glossários e textos do dono) e o fim do log de
travamentos. NUNCA inclui o banco, fotos ou projetos.
"""

from __future__ import annotations

import io
import zipfile
from datetime import datetime
from pathlib import Path


def _texto_versoes() -> str:
    import platform
    import sys
    from app import __version__
    linhas = [f"AutoTabloide AI {__version__}",
              f"Python {sys.version.split()[0]}",
              f"Windows: {platform.platform()}"]
    try:
        import PySide6
        linhas.append(f"PySide6 {PySide6.__version__}")
    except Exception:
        linhas.append("PySide6: ?")
    linhas.append(f"gerado em: {datetime.now():%d/%m/%Y %H:%M}")
    return "\n".join(linhas)


def _texto_acervo() -> str:
    from app.core.database import Database
    from app.core.models import Evento, Layout, Produto, ProjetoSalvo
    db = Database().init()
    try:
        with db.Session() as s:
            n_prod = s.query(Produto).count()
            n_proj = s.query(ProjetoSalvo).count()
            n_lay = s.query(Layout).count()
            n_ev = s.query(Evento).count()
            from app.core.models import Config
            chaves = sorted(c.chave for c in s.query(Config).all())
    finally:
        db.engine.dispose()
    corpo = [f"produtos: {n_prod}", f"projetos: {n_proj}",
             f"layouts: {n_lay}", f"campanhas: {n_ev}", "",
             "chaves de configuração presentes (SÓ os nomes):"]
    corpo += [f"  - {c}" for c in chaves]
    return "\n".join(corpo)


def _fim_do_log() -> str:
    from app.core.paths import SystemRoot
    log = SystemRoot().raiz / "logs" / "travamentos.log"
    if not log.exists():
        return "(sem registros de travamento — bom sinal)"
    try:
        linhas = log.read_text(encoding="utf-8", errors="replace").splitlines()
        return "\n".join(linhas[-400:])
    except Exception as exc:
        return f"(o log não pôde ser lido: {exc})"


def gerar_diagnostico(destino_zip: str | Path) -> Path:
    """Escreve o zip e devolve o caminho. Levanta em disco cheio/afins —
    quem chama mostra o erro (I2)."""
    destino = Path(destino_zip)
    destino.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(destino, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("versoes.txt", _texto_versoes())
        try:
            z.writestr("acervo.txt", _texto_acervo())
        except Exception as exc:
            z.writestr("acervo.txt", f"(falhou: {exc})")
        z.writestr("travamentos.log", _fim_do_log())
    return destino

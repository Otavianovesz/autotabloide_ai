"""Ponto de entrada do EXECUTÁVEL empacotado (FASE 12, Bloco G).

O PyInstaller congela este arquivo; a raiz de dados do dono nasce ao lado
do executável (portátil — o acervo viaja com a pasta), a menos que a
variável AUTOTABLOIDE_ROOT diga outra coisa.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path


def _semear_raiz_nova(raiz: Path) -> None:
    """1ª execução (passo 69): a raiz nasce com as FONTES reais do
    compositor e o logo/sons — copiados da semente empacotada. Idempotente
    (só copia o que falta); nunca sobrescreve dados do dono."""
    import shutil
    semente = Path(getattr(sys, "_MEIPASS", ".")) / "semente"
    if not semente.exists():
        return
    for origem_rel, destino_rel in (("fontes", "fontes"),
                                    ("assets", "assets")):
        origem = semente / origem_rel
        destino = raiz / destino_rel
        if not origem.exists():
            continue
        destino.mkdir(parents=True, exist_ok=True)
        for arq in origem.rglob("*"):
            if not arq.is_file():
                continue
            alvo = destino / arq.relative_to(origem)
            if not alvo.exists():                 # nunca por cima do dono
                alvo.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(arq, alvo)


def main() -> int:
    if getattr(sys, "frozen", False) and not os.environ.get(
            "AUTOTABLOIDE_ROOT"):
        # congelado: a raiz de dados mora AO LADO do executável (portátil)
        raiz = Path(sys.executable).parent / "AutoTabloide_System_Root"
        os.environ["AUTOTABLOIDE_ROOT"] = str(raiz)
        from app.core.paths import SystemRoot
        SystemRoot(raiz).criar_estrutura()
        _semear_raiz_nova(raiz)
    from app.editor_app import main as _main
    return _main()


if __name__ == "__main__":
    raise SystemExit(main())

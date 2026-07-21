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
    if getattr(sys, "frozen", False):
        raiz = os.environ.get("AUTOTABLOIDE_ROOT")
        if not raiz:
            # congelado: a raiz de dados mora AO LADO DA PASTA do app
            # (irmã, não dentro) — desinstalar = apagar a pasta
            # AutoTabloide SEM levar o acervo (passo 77); portátil =
            # mover as duas pastas
            raiz = str(Path(sys.executable).parent.parent
                       / "AutoTabloide_System_Root")
        raiz = Path(raiz)
        from app.core.paths import SystemRoot
        try:
            SystemRoot(raiz).criar_estrutura()
        except OSError:
            # frota F12: extraído em Program Files (sem escrita), o boot
            # morreria criando a raiz — os dados caem no perfil do usuário
            # e um LEIA-ME diz onde (I2, nunca em silêncio)
            raiz = (Path(os.environ.get("LOCALAPPDATA", Path.home()))
                    / "AutoTabloide" / "AutoTabloide_System_Root")
            SystemRoot(raiz).criar_estrutura()
            aviso = raiz.parent / "LEIA-ME (por que os dados estão aqui).txt"
            if not aviso.exists():
                aviso.write_text(
                    "A pasta do programa não aceita escrita (ex.: Program "
                    "Files),\nentão o acervo do AutoTabloide mora aqui. "
                    "Para levar tudo num\npendrive, prefira extrair o "
                    "programa numa pasta comum (ex.: C:\\AutoTabloide).\n",
                    encoding="utf-8")
        os.environ["AUTOTABLOIDE_ROOT"] = str(raiz)
        # a semente roda SEMPRE no congelado (mesmo com raiz da env — a
        # frota pegou a raiz nova nascendo sem fontes nesse caminho)
        _semear_raiz_nova(raiz)
    from app.editor_app import main as _main
    return _main()


if __name__ == "__main__":
    raise SystemExit(main())

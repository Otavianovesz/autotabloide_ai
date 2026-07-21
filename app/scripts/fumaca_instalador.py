"""Fumaça do instalador (FASE 12, passos 78/84/90 — a parte da bancada).

O teste COMPLETO em Windows limpo é do dono (máquina de dev tem Python e
não prova nada sobre dependência faltando). Esta fumaça prova o que dá
para provar aqui, POR CONTEÚDO:

1. o exe empacotado ABRE e fica vivo (sem crash de import nos 1ºs segundos);
2. a 1ª execução cria a raiz de dados IRMÃ da pasta do app (passo 77) com
   banco, pastas e as FONTES semeadas (sem elas, acento vira caixa);
3. rodar de novo NÃO duplica nem sobrescreve (idempotente).

Fica FORA da suíte de propósito: precisa do ``dist/`` construído — na
suíte viraria skip, e skip silencioso não é verde. Rodar::

    python -m app.scripts.empacotar   (antes)
    python -m app.scripts.fumaca_instalador
"""

from __future__ import annotations

import subprocess
import sys
import time
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
EXE = RAIZ / "dist" / "AutoTabloide" / "AutoTabloide.exe"
RAIZ_DADOS = RAIZ / "dist" / "AutoTabloide_System_Root"   # IRMÃ da pasta


def _abrir_e_esperar(segundos: float) -> subprocess.Popen:
    proc = subprocess.Popen([str(EXE)], cwd=EXE.parent)
    time.sleep(segundos)
    return proc


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if not EXE.exists():
        print(f"FALHOU: {EXE} não existe — rode o empacotar antes")
        return 1

    # 1) abre e fica vivo
    proc = _abrir_e_esperar(12)
    vivo = proc.poll() is None
    if not vivo:
        print(f"FALHOU: o exe morreu no boot (código {proc.returncode})")
        return 1
    print("1) exe aberto e vivo após 12s")

    # 2) a raiz nasceu no lugar certo, com as peças
    faltas = []
    if not RAIZ_DADOS.exists():
        faltas.append("raiz irmã não criada")
    else:
        for peca in ("banco", "fontes", "biblioteca_imagens", "projetos"):
            if not (RAIZ_DADOS / peca).exists():
                faltas.append(f"pasta {peca} ausente")
        fontes = list((RAIZ_DADOS / "fontes").glob("*.ttf"))
        if not fontes:
            faltas.append("nenhuma fonte semeada (acento viraria caixa)")
        else:
            print(f"2) raiz irmã criada; {len(fontes)} fontes semeadas")
    proc.terminate()
    try:
        proc.wait(10)
    except subprocess.TimeoutExpired:
        proc.kill()
    if faltas:
        print("FALHOU: " + "; ".join(faltas))
        return 1

    # 3) idempotente: 2ª execução não recria nem duplica
    assinatura = sorted(p.name for p in (RAIZ_DADOS / "fontes").iterdir())
    proc = _abrir_e_esperar(8)
    vivo2 = proc.poll() is None
    proc.terminate()
    try:
        proc.wait(10)
    except subprocess.TimeoutExpired:
        proc.kill()
    assinatura2 = sorted(p.name for p in (RAIZ_DADOS / "fontes").iterdir())
    if not vivo2 or assinatura != assinatura2:
        print("FALHOU: 2ª execução "
              + ("morreu" if not vivo2 else "mexeu nas fontes semeadas"))
        return 1
    print("3) 2ª execução vive e não duplica nada — fumaça VERDE")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

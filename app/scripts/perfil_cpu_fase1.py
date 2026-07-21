"""
Perfil rápido de CPU (FASE 1, passo 47)
=======================================
Mede a CPU do processo (em % do TOTAL da máquina, como o Gerenciador de
Tarefas mostra) em 4 fases: idle → trocas de tela → hover animado → idle
final. O critério do caderno: troca de tela e hover ≤ 5%; o idle final
prova que nenhum timer de animação ficou vazando.

Rodar::

    python -m app.scripts.perfil_cpu_fase1
"""

from __future__ import annotations

import sys
import time


def _medir(app, processo, nucleos: int, segundos: float,
           por_tick=None, tick_ms: int = 50) -> float:
    """Roda o event loop por N segundos e devolve a CPU média (% do total)."""
    processo.cpu_percent(None)                 # zera o contador
    fim = time.monotonic() + segundos
    proxima_acao = 0.0
    while time.monotonic() < fim:
        app.processEvents()
        if por_tick is not None and time.monotonic() >= proxima_acao:
            por_tick()
            proxima_acao = time.monotonic() + 0.4   # uma ação a cada 400 ms
        time.sleep(tick_ms / 1000)
    return processo.cpu_percent(None) / nucleos


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    import psutil
    from PySide6.QtWidgets import QApplication

    from app.editor_app import montar_janela
    from app.qt.design.animacoes import (
        animacoes_ativas, instalar_vida)
    from app.qt.design.shell import TELAS
    from app.qt.design.tema import aplicar_tema

    app = QApplication.instance() or QApplication([])
    aplicar_tema(app)
    instalar_vida(app)                         # o app REAL, com as animações

    shell, editor = montar_janela()
    editor.close()
    shell.resize(1280, 800)
    shell.show()                               # janela real: paint de verdade
    for _ in range(10):
        app.processEvents()
    time.sleep(0.5)

    processo = psutil.Process()
    nucleos = psutil.cpu_count() or 1

    idle0 = _medir(app, processo, nucleos, 3.0)

    ciclo = [c for c, _r, _i in TELAS]
    estado = {"i": 0}

    def _trocar() -> None:
        estado["i"] = (estado["i"] + 1) % len(ciclo)
        shell.ir_para(ciclo[estado["i"]])

    troca = _medir(app, processo, nucleos, 6.0, por_tick=_trocar)

    # hover animado de verdade: entra/sai do véu num botão da navegação
    from app.qt.design.animacoes import _hover_entrou, _hover_saiu
    botao = shell._botoes["inicio"]
    alterna = {"dentro": False}

    def _hover() -> None:
        if alterna["dentro"]:
            _hover_saiu(botao)
        else:
            _hover_entrou(botao)
        alterna["dentro"] = not alterna["dentro"]

    hover = _medir(app, processo, nucleos, 6.0, por_tick=_hover)

    idle1 = _medir(app, processo, nucleos, 3.0)
    vivas = animacoes_ativas()

    shell.close()
    app.processEvents()

    print(f"idle inicial : {idle0:5.1f}%")
    print(f"troca de tela: {troca:5.1f}%   (1 troca a cada 400 ms)")
    print(f"hover animado: {hover:5.1f}%   (entra/sai a cada 400 ms)")
    print(f"idle final   : {idle1:5.1f}%   (animações vivas: {vivas})")
    ok = troca <= 5.0 and hover <= 5.0 and idle1 <= 1.0 and vivas == 0
    print("VEREDITO:", "DENTRO do limite (<=5%)" if ok else "ACIMA DO LIMITE")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())

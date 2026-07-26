"""F13/E2 (CA-02) — a rede de erro do exe.

Com ``console=False`` no PyInstaller, ``sys.stdout``/``sys.stderr`` são
``None``: todo ``print()`` e ``traceback.print_exc()`` viram no-op e um
erro fatal morre MUDO. Esta rede grava o traceback INTEIRO em
``<raiz>/logs/erros.log`` (o molde do vigia: append tolerante a falha —
registrar erro nunca pode criar um erro novo) e o zip de diagnóstico
passa a levá-lo (o suporte deixa de receber um zip cego).
"""

from __future__ import annotations

import sys
import traceback


def _caminho_log():
    from app.core.paths import SystemRoot
    pasta = SystemRoot().raiz / "logs"
    pasta.mkdir(parents=True, exist_ok=True)
    return pasta / "erros.log"


def registrar_erro_bruto(texto: str) -> None:
    """Append tolerante: nunca levanta (disco cheio/sem permissão só
    perde o registro, nunca derruba quem registrava)."""
    try:
        import time
        with open(_caminho_log(), "a", encoding="utf-8") as f:
            f.write(f"\n--- {time.strftime('%Y-%m-%d %H:%M:%S')} ---\n"
                    f"{texto}\n")
    except OSError:
        pass


def instalar_rede_de_erros() -> None:
    """``sys.excepthook`` → logs/erros.log, ENCADEANDO o hook anterior
    (no dev o traceback continua no console; no exe, que não tem console,
    o arquivo é o único rastro)."""
    anterior = sys.excepthook

    def _hook(tipo, valor, tb):
        registrar_erro_bruto(
            "".join(traceback.format_exception(tipo, valor, tb)))
        try:
            anterior(tipo, valor, tb)
        except Exception:
            pass

    sys.excepthook = _hook

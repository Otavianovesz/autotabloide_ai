"""
Vigia de travamento (RG-05)
===========================
Detecta a UI presa e grava a prova no log — o "watchdog de logging" da
REVISAO_GERAL.

Como funciona: um QTimer no thread da UI chama ``batimento()`` a cada
segundo ("estou vivo"); uma thread daemon confere a idade do último
batimento. Se ela passar do limite (padrão 5 s), o vigia grava UMA vez por
episódio o traceback de TODAS as threads em ``<raiz>/logs/travamentos.log``
— quando o app congelar de novo na máquina do dono, o log conta exatamente
onde estava preso.

Limitação honesta: se a UI ficar presa em código NATIVO que não solta o
GIL, a thread do vigia também para e nada é gravado — cobre os travamentos
de código Python (laços pesados, I/O no thread errado), que são os casos
reais vistos até hoje.
"""

from __future__ import annotations

import faulthandler
import threading
import time
from datetime import datetime
from pathlib import Path


class VigiaTravamento:
    """Grava traceback de todas as threads quando a UI para de "bater"."""

    def __init__(self, arquivo: Path | str, limite_s: float = 5.0):
        self.arquivo = Path(arquivo)
        self.limite_s = limite_s
        self._ultimo = time.monotonic()
        self._ja_gravou = False          # 1 dump por episódio de travamento
        self._parar = threading.Event()
        self._thread: threading.Thread | None = None

    def batimento(self) -> None:
        """Chamado pelo timer da UI — marca "estou vivo" e fecha o episódio."""
        self._ultimo = time.monotonic()
        self._ja_gravou = False

    def iniciar(self) -> "VigiaTravamento":
        self.arquivo.parent.mkdir(parents=True, exist_ok=True)
        self._thread = threading.Thread(
            target=self._rodar, daemon=True, name="vigia-travamento")
        self._thread.start()
        return self

    def parar(self) -> None:
        self._parar.set()

    # --- interno ---------------------------------------------------------------

    def _rodar(self) -> None:
        passo = max(0.1, min(2.0, self.limite_s / 2))
        while not self._parar.wait(passo):
            idade = time.monotonic() - self._ultimo
            if idade >= self.limite_s and not self._ja_gravou:
                self._ja_gravou = True
                self._gravar(idade)

    def _gravar(self, idade: float) -> None:
        try:
            with open(self.arquivo, "a", encoding="utf-8") as f:
                f.write(f"\n=== UI presa há {idade:.1f}s — "
                        f"{datetime.now():%d/%m/%Y %H:%M:%S} ===\n")
                f.flush()
                faulthandler.dump_traceback(file=f)
        except OSError:
            pass                         # o vigia nunca derruba o app

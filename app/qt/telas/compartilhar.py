"""Compartilhar direto (R-064, Fase 8 — Bloco A).

HONESTIDADE (I2): o app NÃO controla o WhatsApp. O SO não dá uma API garantida
de "enviar para a conversa X". O que o Windows garante e o que entregamos:

  1. **Copiar imagem** — a peça vai para a área de transferência, pronta para
     colar (Ctrl+V) na conversa do WhatsApp Web/Desktop. É o caminho mais curto
     e 100% confiável.
  2. **Abrir a pasta do arquivo** — o Explorer abre já com o arquivo selecionado,
     para arrastar/anexar.
  3. **Abrir com…** — deixa o Windows oferecer os apps (inclui o WhatsApp
     Desktop, se instalado) — melhor esforço, depende do SO.

Nunca prometemos o que o SO não faz. A UI diz isso ao dono.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

LIMITACAO_SO = (
    "O app não controla o WhatsApp diretamente (o Windows não permite). "
    "O jeito mais rápido é “Copiar imagem” e colar (Ctrl+V) na conversa; "
    "ou “Abrir a pasta” e arrastar o arquivo."
)


def copiar_imagem(caminho: str | Path) -> bool:
    """Coloca a imagem na área de transferência (pronta para colar na conversa).
    Devolve True se conseguiu. Exige uma QApplication viva."""
    try:
        from PySide6.QtGui import QImage
        from PySide6.QtWidgets import QApplication
        app = QApplication.instance()
        if app is None:
            return False
        img = QImage(str(caminho))
        if img.isNull():
            return False
        QApplication.clipboard().setImage(img)
        return True
    except Exception:
        return False


def abrir_pasta(caminho: str | Path) -> bool:
    """Abre o Explorer com o ARQUIVO selecionado (Windows), ou a pasta (outros
    SOs). Melhor esforço; devolve True se disparou o comando."""
    p = Path(caminho)
    try:
        if sys.platform.startswith("win"):
            # /select destaca o arquivo dentro da pasta
            subprocess.Popen(["explorer", "/select,", str(p)])
        elif sys.platform == "darwin":
            subprocess.Popen(["open", "-R", str(p)])
        else:
            subprocess.Popen(["xdg-open", str(p.parent)])
        return True
    except Exception:
        return False


def abrir_com(caminho: str | Path) -> bool:
    """"Abrir com…" — deixa o Windows oferecer os apps (inclui o WhatsApp
    Desktop, se instalado). Melhor esforço, depende do SO."""
    p = Path(caminho)
    try:
        if sys.platform.startswith("win"):
            os.startfile(str(p), "openas")     # o diálogo "Abrir com…"  # noqa: S606
            return True
        if sys.platform == "darwin":
            subprocess.Popen(["open", str(p)])
            return True
        subprocess.Popen(["xdg-open", str(p)])
        return True
    except Exception:
        return False

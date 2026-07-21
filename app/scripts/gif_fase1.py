"""
GIF da checagem 48 (FASE 1, Bloco D)
====================================
Grava ~20 s do app REAL navegando (crossfade de telas, skeleton, toast,
diálogo com véu + scale-in, hover animado) em ``saida_fase1/animacoes.gif``
e depois PROVA "Reduzir animações": com a Config em "reduzidas", nenhuma
animação entra em voo durante as mesmas ações.

Rodar::

    python -m app.scripts.gif_fase1
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

FPS = 10                      # 10 quadros/s — leve e mostra o movimento
ESCALA = 0.6                  # 1280×800 → 768×480 no GIF


def _qimg_para_pil(qimg):
    from PIL import Image
    from PySide6.QtGui import QImage
    qimg = qimg.convertToFormat(QImage.Format.Format_RGBA8888)
    buf = qimg.constBits().tobytes()
    img = Image.frombytes("RGBA", (qimg.width(), qimg.height()), buf,
                          "raw", "RGBA", qimg.bytesPerLine())
    return img.convert("RGB")


def _config_animacoes(valor: str | None) -> str | None:
    """Lê/grava a Config ``aparencia.animacoes``; devolve o valor anterior."""
    from app.core.database import Database
    from app.core.repositories import ConfigRepositorio
    db = Database().init()
    try:
        with db.Session() as s:
            cfg = ConfigRepositorio(s)
            anterior = cfg.get("aparencia.animacoes")
            if valor is not None:
                cfg.set("aparencia.animacoes", valor)
                s.commit()
            return anterior
    finally:
        db.engine.dispose()


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    from PySide6.QtGui import QGuiApplication
    from PySide6.QtWidgets import QApplication

    from app.editor_app import montar_janela
    from app.qt.design.animacoes import (
        _hover_entrou, _hover_saiu, animacoes_ativas, instalar_vida,
        recarregar_config)
    from app.qt.design.tema import aplicar_tema
    from app.qt.design.toast import mostrar_toast

    saida = Path("saida_fase1")
    saida.mkdir(exist_ok=True)

    app = QApplication.instance() or QApplication([])
    aplicar_tema(app)
    instalar_vida(app)
    _config_animacoes("ligadas")
    recarregar_config()

    shell, editor = montar_janela()
    editor.close()
    shell.resize(1280, 800)
    shell.show()
    shell.raise_()
    for _ in range(10):
        app.processEvents()
    time.sleep(0.6)

    # --- roteiro dos 20 s: (t, ação) -----------------------------------------
    contexto: dict = {}

    def _abrir_dialogo() -> None:
        from app.qt.telas.curadoria_dialog import CuradoriaDialog
        dlg = CuradoriaDialog("Doce de Banana Val 250g", [],
                              tokens_perdidos=["VAL"], parent=shell)
        dlg.resize(680, 480)
        dlg.show()                       # não-modal: o roteiro segue
        contexto["dlg"] = dlg

    def _fechar_dialogo() -> None:
        dlg = contexto.pop("dlg", None)
        if dlg is not None:
            dlg.reject()

    botao_nav = shell._botoes["atelie"]
    roteiro = [
        (1.5, lambda: shell.ir_para("atelie")),
        (3.0, lambda: shell.ir_para("almoxarifado")),
        (4.5, lambda: shell.ir_para("mesa")),
        (6.0, lambda: shell.ir_para("fabrica")),
        (7.5, lambda: shell.ir_para("cofre")),
        (9.0, lambda: shell.ir_para("configuracoes")),
        (10.5, lambda: mostrar_toast(shell, "Fase 1: tema, animações e "
                                            "polimento", "sucesso")),
        (12.0, lambda: shell.ir_para("inicio")),   # skeleton + crossfade
        (13.5, _abrir_dialogo),                    # véu + fade/scale-in
        (16.5, _fechar_dialogo),
        (17.2, lambda: _hover_entrou(botao_nav)),
        (17.9, lambda: _hover_saiu(botao_nav)),
        (18.6, lambda: _hover_entrou(botao_nav)),
        (19.3, lambda: _hover_saiu(botao_nav)),
    ]

    def _quadro_composto():
        """shell.grab() (janela exata, sem desktop) + o corpo do diálogo
        colado por cima na posição real — o grab de widget não vê janelas
        sobrepostas. Limite honesto: windowOpacity do diálogo não aparece
        em grab (composição do SO); o scale-in da geometria aparece."""
        base = _qimg_para_pil(shell.grab().toImage())
        dlg = contexto.get("dlg")
        if dlg is not None and dlg.isVisible():
            corpo = _qimg_para_pil(dlg.grab().toImage())
            pos = dlg.geometry().topLeft() - shell.geometry().topLeft()
            base.paste(corpo, (max(0, pos.x()), max(0, pos.y())))
        return base

    quadros = []
    inicio = time.monotonic()
    proximo_quadro = 0.0

    while (agora := time.monotonic() - inicio) < 20.0:
        app.processEvents()
        while roteiro and agora >= roteiro[0][0]:
            roteiro.pop(0)[1]()
        if agora >= proximo_quadro:
            quadros.append(_quadro_composto())
            proximo_quadro = agora + 1.0 / FPS
        time.sleep(0.01)

    _fechar_dialogo()

    # --- monta o GIF ----------------------------------------------------------
    w = int(quadros[0].width * ESCALA)
    h = int(quadros[0].height * ESCALA)
    quadros = [q.resize((w, h)) for q in quadros]
    destino = saida / "animacoes.gif"
    quadros[0].save(destino, save_all=True, append_images=quadros[1:],
                    duration=int(1000 / FPS), loop=0, optimize=True)
    print(f"GIF: {destino.resolve()}  ({len(quadros)} quadros, "
          f"{destino.stat().st_size / 1_048_576:.1f} MB)")

    # --- prova de "Reduzir animações": as MESMAS ações, zero em voo ----------
    _config_animacoes("reduzidas")
    recarregar_config()
    pico = 0
    for chave in ("atelie", "mesa", "cofre", "inicio", "configuracoes",
                  "inicio"):
        shell.ir_para(chave)
        for _ in range(5):
            app.processEvents()
            pico = max(pico, animacoes_ativas())
    mostrar_toast(shell, "Reduzidas: instantâneo", "info")
    _abrir_dialogo()
    for _ in range(10):
        app.processEvents()
        pico = max(pico, animacoes_ativas())
    _fechar_dialogo()
    _hover_entrou(botao_nav)
    _hover_saiu(botao_nav)
    for _ in range(5):
        app.processEvents()
        pico = max(pico, animacoes_ativas())
    print(f"Reduzidas: pico de animações em voo = {pico} "
          f"({'PROVADO instantâneo' if pico == 0 else 'FALHOU'})")

    _config_animacoes("ligadas")     # devolve o padrão
    recarregar_config()
    shell.close()
    app.processEvents()
    return 0 if pico == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())

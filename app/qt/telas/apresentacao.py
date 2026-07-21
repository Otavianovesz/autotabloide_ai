"""
Modo apresentação (FASE 2, passos 93-94 — R-011)
================================================
Tela cheia com as peças do evento — para o pai aprovar sem ver o app:
fundo preto, ←/→ navegam, Esc sai. Usa o EXPORT (PNG) quando existe;
senão a miniatura grande com o aviso "não exportado" (nunca mente).
"""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QDialog, QLabel, QVBoxLayout

from app.qt.design import tokens as t


class ApresentacaoDialog(QDialog):
    """``pecas`` = [{nome, caminho, exportado(bool)}] — já resolvidos."""

    def __init__(self, titulo: str, pecas: list[dict], parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Apresentação — {titulo}")
        self._pecas = pecas
        self._indice = 0
        self.setStyleSheet("background: #000000;")

        self._imagem = QLabel()
        self._imagem.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._rodape = QLabel("")
        self._rodape.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._rodape.setStyleSheet(
            "color: #9AA0AA; background: transparent; font-size: 10pt;")

        lay = QVBoxLayout(self)
        lay.setContentsMargins(t.ESP_3, t.ESP_3, t.ESP_3, t.ESP_2)
        lay.addWidget(self._imagem, 1)
        lay.addWidget(self._rodape)
        self._mostrar()

    def abrir_tela_cheia(self) -> None:
        self.showFullScreen()

    def _mostrar(self) -> None:
        if not self._pecas:
            self._imagem.setText("Nenhuma peça neste evento.")
            self._imagem.setStyleSheet("color: #9AA0AA;")
            self._rodape.setText("Esc sai")
            return
        peca = self._pecas[self._indice]
        pm = QPixmap(peca["caminho"]) if peca["caminho"] else QPixmap()
        if not pm.isNull():
            alvo = self.size() * 0.94
            self._imagem.setPixmap(pm.scaled(
                alvo, Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation))
        else:
            self._imagem.setText("(sem imagem)")
            self._imagem.setStyleSheet("color: #9AA0AA;")
        aviso = "" if peca["exportado"] else \
            "  ·  ⚠ não exportado (mostrando a miniatura)"
        self._rodape.setText(
            f"{peca['nome']}   ·   {self._indice + 1}/{len(self._pecas)}"
            f"{aviso}   ·   ← → navegam · Esc sai")

    def keyPressEvent(self, ev) -> None:  # noqa: N802 (Qt)
        if ev.key() in (Qt.Key.Key_Escape,):
            self.reject()
        elif ev.key() in (Qt.Key.Key_Right, Qt.Key.Key_Space):
            self._indice = (self._indice + 1) % max(1, len(self._pecas))
            self._mostrar()
        elif ev.key() == Qt.Key.Key_Left:
            self._indice = (self._indice - 1) % max(1, len(self._pecas))
            self._mostrar()
        else:
            super().keyPressEvent(ev)

    def resizeEvent(self, ev) -> None:  # noqa: N802 (Qt)
        super().resizeEvent(ev)
        self._mostrar()                  # re-escala a peça ao tamanho novo


def pecas_do_evento(nome_evento: str) -> list[dict]:
    """Passo 94: export real quando existe; senão a miniatura com aviso."""
    from app.core import projetos
    pecas = []
    for p in projetos.listar_projetos():
        if (p["evento"] or "").strip().lower() != nome_evento.strip().lower():
            continue
        exportado = projetos.export_de(p["id"])
        pecas.append({
            "nome": p["nome"],
            "caminho": exportado or p.get("miniatura"),
            "exportado": exportado is not None,
        })
    return pecas

"""Exportar bem — perfis + fila em lote + compartilhar (R-065/066/064, Fase 8).

O dono escolhe "WhatsApp", "Impressão" ou "Stories" (ou vários de uma vez) e
manda; o app cuida do número (px/dpi/formato). A fila em lote roda em worker,
mostra progresso por item e um erro NÃO derruba os outros (I2). A marca d'água
RASCUNHO vale até a aprovação. Ao fim, oferece "Copiar imagem" / "Abrir pasta".

Worker encerra no ``done()`` (lei "verde com crash no exit NÃO é verde").
"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog, QFileDialog, QHBoxLayout, QLabel, QListWidget, QListWidgetItem,
    QPushButton, QVBoxLayout,
)

from app.qt.design import tokens as t
from app.qt.design.carregando import OverlayOcupado
from app.qt.design.componentes import EstadoVazio
from app.qt.design.toast import mostrar_toast
from app.qt.telas import compartilhar
from app.qt.workers import GerenciadorTrabalhos, TrabalhadorFila


def _slug(nome: str) -> str:
    return "".join(c if c.isalnum() else "_" for c in nome).strip("_").lower()


class ExportarDialog(QDialog):
    def __init__(self, mesa, parent=None):
        super().__init__(parent or mesa)
        self.mesa = mesa
        self.setWindowTitle("Exportar — perfis e lote")
        self.setMinimumWidth(440)
        self._trabalhos = GerenciadorTrabalhos()
        self._gerados: list[str] = []
        self._erros: list[tuple[str, str]] = []

        from app.rendering.perfis import perfis_configurados
        self._perfis = perfis_configurados()

        titulo = QLabel("Escolha um ou mais perfis e exporte de uma vez")
        titulo.setProperty("papel", "titulo")

        self.lista = QListWidget()
        for p in self._perfis:
            li = QListWidgetItem(f"{p.nome}  ·  {p.formato}")
            li.setFlags(li.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            li.setCheckState(Qt.CheckState.Checked if p.nome.startswith("WhatsApp")
                             else Qt.CheckState.Unchecked)
            self.lista.addItem(li)

        self._nota = QLabel(
            "A peça sai com “RASCUNHO” até você aprovar o projeto."
            if not mesa.esta_aprovado() else "Projeto aprovado — sai limpo.")
        self._nota.setProperty("papel", "legenda")
        self._nota.setWordWrap(True)

        exportar = QPushButton("Exportar os selecionados…")
        exportar.setProperty("tipo", "primario")
        exportar.setToolTip("Gera todos os perfis marcados de uma vez — "
                            "um erro não derruba os outros")
        exportar.clicked.connect(self._exportar)
        fechar = QPushButton("Fechar")
        fechar.setToolTip("Fecha sem exportar")
        fechar.clicked.connect(self.reject)
        rod = QHBoxLayout()
        rod.addStretch(1)
        rod.addWidget(fechar)
        rod.addWidget(exportar)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(t.ESP_4, t.ESP_4, t.ESP_4, t.ESP_4)
        lay.setSpacing(t.ESP_2)
        lay.addWidget(titulo)
        if self._perfis:
            lay.addWidget(self.lista, 1)
        else:                        # sem perfis: estado vazio com craft, não
            self.lista.hide()        # um retângulo branco mudo
            lay.addWidget(EstadoVazio(
                "impressora", "Nenhum perfil configurado",
                "Crie perfis de exportação nas Configurações."), 1)
        lay.addWidget(self._nota)
        lay.addLayout(rod)
        self._overlay = OverlayOcupado(self)

    def _selecionados(self):
        return [p for i, p in enumerate(self._perfis)
                if self.lista.item(i).checkState() == Qt.CheckState.Checked]

    def _exportar(self):
        if getattr(self, "_ocupado", False):     # reentrância: uma fila por vez
            return
        perfis = self._selecionados()
        if not perfis:
            mostrar_toast(self, "Marque ao menos um perfil.")
            return
        pasta = QFileDialog.getExistingDirectory(self, "Salvar as exportações em…")
        if not pasta:
            return
        self._overlay.mostrar("Compondo as páginas…")     # feedback antes do freeze
        # compõe TODAS as páginas UMA vez (na thread da UI); a fila só resiza por
        # perfil. Multipágina NÃO se perde: cada perfil grava _p1.._pN (I2).
        paginas = self.mesa.paginas_compostas()
        if not paginas:
            self._overlay.esconder()
            mostrar_toast(self, "Nada para exportar.", tipo="erro")
            return
        if not self.mesa.esta_aprovado():
            from app.rendering.marca_dagua import carimbar_rascunho
            paginas = [carimbar_rascunho(p) for p in paginas]
        base = Path(pasta)
        self._gerados, self._erros = [], []

        from app.rendering.perfis import exportar_com_perfil
        pares = [(p.nome, p) for p in perfis]

        def _um(perfil):
            if len(paginas) == 1:
                return [str(exportar_com_perfil(
                    paginas[0], base / _slug(perfil.nome), perfil))]
            return [str(exportar_com_perfil(
                pg, base / f"{_slug(perfil.nome)}_p{i}", perfil))
                for i, pg in enumerate(paginas, 1)]

        fila = TrabalhadorFila(pares, _um)
        fila.item_pronto.connect(lambda _n, cams: self._gerados.extend(cams))
        fila.item_falhou.connect(
            lambda n, m: self._erros.append((n, m)))       # I2: não derruba a fila
        fila.fila_terminou.connect(lambda p=str(pasta): self._fim(p))
        self._overlay.mostrar("Exportando os perfis…")
        self._ocupado = True                     # a partir daqui, uma fila roda
        self._trabalhos.rodar(fila)

    def _fim(self, pasta: str):
        self._ocupado = False
        self._overlay.esconder()
        if not self._gerados:
            mostrar_toast(self, "Nenhum arquivo saiu.", tipo="erro")
            return
        extra = (f" · {len(self._erros)} com erro" if self._erros else "")
        mostrar_toast(self, f"{len(self._gerados)} arquivo(s) em "
                            f"{Path(pasta).name}{extra}", tipo="sucesso")
        # R-064: compartilhar o primeiro (copiar imagem se PNG/JPG + abrir pasta)
        primeiro = self._gerados[0]
        if primeiro.lower().endswith((".png", ".jpg", ".jpeg")):
            compartilhar.copiar_imagem(primeiro)
        compartilhar.abrir_pasta(primeiro)

    def done(self, resultado: int) -> None:  # noqa: N802 (Qt)
        self._trabalhos.encerrar()
        super().done(resultado)

"""Publicar além do encarte (R-139/140/141/142, Fase 8 — Blocos C/D).

Um hub só: Oferta do Dia (1 produto herói), carrossel (N cards), Story e vídeo —
tudo reusando o compositor (social = outro LayoutDef, a MESMA cadeia produto→
slot). O MP4 é opcional: sem ffmpeg, avisa e não trava (I2). A marca d'água
RASCUNHO vale aqui também até a aprovação.

Worker com encerramento no ``done()`` (lei "verde com crash no exit NÃO é
verde"): nenhum trabalho vivo quando o diálogo fecha.
"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtWidgets import (
    QComboBox, QDialog, QFileDialog, QHBoxLayout, QLabel, QPushButton,
    QRadioButton, QVBoxLayout,
)

from app.qt.design import tokens as t
from app.qt.design.carregando import OverlayOcupado
from app.qt.design.toast import mostrar_toast
from app.qt.workers import GerenciadorTrabalhos, Trabalhador


class PublicarDialog(QDialog):
    """Gera os formatos sociais/vídeo do projeto atual da Mesa."""

    def __init__(self, mesa, parent=None):
        super().__init__(parent or mesa)
        self.mesa = mesa
        self.setWindowTitle("Publicar — social e vídeo")
        self.setMinimumWidth(460)
        self._trabalhos = GerenciadorTrabalhos()

        titulo = QLabel("Levar a oferta às redes, ao story e ao Status")
        titulo.setProperty("papel", "titulo")

        self.rb_oferta = QRadioButton("Oferta do Dia (1 produto em destaque)")
        self.rb_oferta.setToolTip("Um card quadrado com o produto herói — "
                                  "o formato do WhatsApp/Instagram")
        self.rb_carrossel = QRadioButton("Carrossel (1 card por produto)")
        self.rb_carrossel.setToolTip("Um card por item da oferta, na ordem "
                                     "da estante")
        self.rb_story = QRadioButton("Story / Reels (vertical)")
        self.rb_story.setToolTip("Formato vertical de tela cheia (9:16)")
        self.rb_video = QRadioButton("Vídeo do tabloide (páginas em MP4)")
        self.rb_video.setToolTip("As páginas do encarte viram um vídeo curto — "
                                 "precisa do componente “ffmpeg”")
        self.rb_oferta.setChecked(True)

        self.combo_item = QComboBox()
        for it in mesa._itens:
            self.combo_item.addItem(it.nome, it.uid)
        self.combo_item.setToolTip("Qual produto vai no destaque/Story")

        self._nota = QLabel("")
        self._nota.setProperty("papel", "legenda")
        self._nota.setWordWrap(True)
        self._atualizar_nota()
        for rb in (self.rb_oferta, self.rb_carrossel, self.rb_story, self.rb_video):
            rb.toggled.connect(self._atualizar_nota)

        gerar = QPushButton("Gerar e salvar…")
        gerar.setProperty("tipo", "primario")
        gerar.setToolTip("Compõe o formato escolhido e salva na pasta que "
                         "você indicar")
        gerar.clicked.connect(self._gerar)
        fechar = QPushButton("Fechar")
        fechar.setToolTip("Fecha sem gerar")
        fechar.clicked.connect(self.reject)
        rodape = QHBoxLayout()
        rodape.addStretch(1)
        rodape.addWidget(fechar)
        rodape.addWidget(gerar)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(t.ESP_4, t.ESP_4, t.ESP_4, t.ESP_4)
        lay.setSpacing(t.ESP_2)
        lay.addWidget(titulo)
        for rb in (self.rb_oferta, self.rb_carrossel, self.rb_story, self.rb_video):
            lay.addWidget(rb)
        lay.addSpacing(t.ESP_2)
        rotulo_destaque = QLabel("Produto do destaque:")
        rotulo_destaque.setProperty("papel", "legenda")
        lay.addWidget(rotulo_destaque)
        lay.addWidget(self.combo_item)
        lay.addWidget(self._nota)
        lay.addLayout(rodape)

        self._overlay = OverlayOcupado(self)

    def _atualizar_nota(self, *_):
        so_item = self.rb_oferta.isChecked() or self.rb_story.isChecked()
        self.combo_item.setEnabled(so_item)
        if self.rb_video.isChecked():
            from app.rendering.video import ffmpeg_disponivel
            if ffmpeg_disponivel() is None:
                self._nota.setText("⚠️ O vídeo (MP4) precisa do componente "
                                   "“ffmpeg”, que não está instalado. Os outros "
                                   "formatos funcionam normalmente.")
                return
        if not self.mesa.esta_aprovado():
            self._nota.setText("A peça sai com a marca “RASCUNHO” até você "
                               "aprovar o projeto (na Mesa).")
        else:
            self._nota.setText("Projeto aprovado — sai limpo.")

    # --- geração (em worker; done() encerra) --------------------------------

    def _item_escolhido(self):
        uid = self.combo_item.currentData()
        for it in self.mesa._itens:
            if it.uid == uid:
                return it
        return self.mesa._itens[0] if self.mesa._itens else None

    def _avisos_pre_voo(self, modo: str, item) -> list[str]:
        """GATE 3 da ordem F11.5 (I2): o social ganha o MESMO pré-voo do
        export da Mesa — item sem foto ou sem preço entendido AVISA antes de
        ir pro feed/Story (antes saía calado, a degradação silenciosa que o
        projeto proíbe)."""
        from app.qt.telas import servico
        alvo = ([item] if modo in ("oferta", "story") and item is not None
                else self.mesa._itens)
        avisos: list[str] = []
        for it in alvo:
            nome = (it.nome or "?").strip() or "?"
            if not (it.imagem or it.imagens):
                avisos.append(f"“{nome}”: sem foto")
            if servico.preco_decimal(it.preco) is None and not it.multi_preco:
                avisos.append(f"“{nome}”: sem preço (ou preço não entendido)")
        return avisos

    def _gerar(self):
        if not self.mesa._itens:
            mostrar_toast(self, "Não há itens na oferta.", tipo="erro")
            return
        modo = ("oferta" if self.rb_oferta.isChecked() else
                "carrossel" if self.rb_carrossel.isChecked() else
                "story" if self.rb_story.isChecked() else "video")
        # GATE 3: pré-voo ANTES de qualquer exportação social (o dono decide)
        from app.qt.telas.prevoo import confirmar_pre_voo
        if not confirmar_pre_voo(
                self, self._avisos_pre_voo(modo, self._item_escolhido()),
                "Publicar"):
            return
        pasta = QFileDialog.getExistingDirectory(self, "Salvar a publicação em…")
        if not pasta:
            return
        marca = not self.mesa.esta_aprovado()
        item = self._item_escolhido()
        mesa = self.mesa

        def _trabalho(st):
            from app.rendering.export import exportar_png
            from app.rendering.marca_dagua import carimbar_rascunho
            from app.rendering.social import compor_carrossel, compor_social
            from app.rendering.video import gerar_video_paginas
            base = Path(pasta)
            aviso = None
            gerados: list[str] = []
            if modo == "video":
                st("Compondo as páginas…")
                imgs = mesa.paginas_compostas()
                if marca:
                    imgs = [carimbar_rascunho(im) for im in imgs]
                st("Gerando o vídeo…")
                mp4, aviso = gerar_video_paginas(imgs, base / "tabloide.mp4")
                if mp4 is not None:
                    gerados.append(str(mp4))
            elif modo == "carrossel":
                st("Compondo os cards…")
                dados = [mesa._dados_de(it) for it in mesa._itens]
                cards = compor_carrossel(dados)
                for i, im in enumerate(cards, 1):
                    if marca:
                        im = carimbar_rascunho(im)
                    p = exportar_png(im, base / f"card_{i:02d}.png", 96)
                    gerados.append(str(p))
            else:
                st("Compondo o destaque…")
                fmt = "oferta_do_dia" if modo == "oferta" else "story"
                im = compor_social(fmt, mesa._dados_de(item))
                if marca:
                    im = carimbar_rascunho(im)
                nome = "oferta_do_dia.png" if modo == "oferta" else "story.png"
                gerados.append(str(exportar_png(im, base / nome, 96)))
            return gerados, aviso, str(pasta)

        trab = Trabalhador(_trabalho)
        trab.status.connect(self._overlay.mostrar)
        trab.ok.connect(self._pronto)
        trab.erro.connect(lambda m: (self._overlay.esconder(),
                                     mostrar_toast(self, m, tipo="erro")))
        self._trabalhos.rodar(trab)

    def _pronto(self, resultado):
        self._overlay.esconder()
        gerados, aviso, pasta = resultado
        if not gerados:
            mostrar_toast(self, aviso or "Nada foi gerado.", tipo="erro")
            return
        extra = f" — {aviso}" if aviso else ""
        mostrar_toast(self, f"{len(gerados)} arquivo(s) em {Path(pasta).name}"
                            f"{extra}", tipo="sucesso")
        # R-064: compartilhar o primeiro gerado (copiar imagem / abrir pasta)
        from app.qt.telas import compartilhar
        if gerados[0].lower().endswith(".png"):
            compartilhar.copiar_imagem(gerados[0])
        compartilhar.abrir_pasta(gerados[0])

    def done(self, resultado: int) -> None:  # noqa: N802 (Qt)
        # lei exit-0: nenhum worker vivo quando o diálogo fecha
        self._trabalhos.encerrar()
        super().done(resultado)

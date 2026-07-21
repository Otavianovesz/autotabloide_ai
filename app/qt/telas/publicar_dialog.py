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


def _rect_preco_story_px() -> tuple[int, int, int, int] | None:
    """#49/#50: o retângulo (px) da região "Preço por" do layout Story — a
    animação pulsa SÓ ali. None se a região não for achada (degrada para o
    respiro global, I2 sem drama)."""
    try:
        from app.rendering.model import PapelPreco, TipoRegiao
        from app.rendering.social import layout_social
        from app.rendering.units import mm_para_px
        lay = layout_social("story")
        for reg in lay.paginas[0].slots[0].regioes:
            if (reg.tipo == TipoRegiao.PRECO
                    and reg.papel_preco == PapelPreco.POR):
                r = reg.rect
                return (int(mm_para_px(r.x_mm, lay.dpi)),
                        int(mm_para_px(r.y_mm, lay.dpi)),
                        int(mm_para_px(r.larg_mm, lay.dpi)),
                        int(mm_para_px(r.alt_mm, lay.dpi)))
    except Exception:
        pass
    return None


def _compor_publicacao(mesa, modo: str, base: Path, marca: bool, item,
                       itens_sel, st, *, fundo: str | None = None,
                       story_mp4: bool = False, seg_por_pagina: float = 2.5,
                       fade: bool = False):
    """O miolo do Publicar, SEM widgets (roda no worker e nos testes): compõe
    o formato pedido e devolve (gerados, aviso, pasta). A marca RASCUNHO vale
    em TODA porta — PNG e MP4 (a lição da 2ª porta esquecida)."""
    from app.rendering.export import exportar_png
    from app.rendering.marca_dagua import carimbar_rascunho
    from app.rendering.social import compor_carrossel, compor_social
    from app.rendering.video import gerar_video_paginas, gerar_video_story
    aviso = None
    gerados: list[str] = []
    if modo == "video":
        st("Compondo as páginas…")
        imgs = mesa.paginas_compostas()
        if marca:
            imgs = [carimbar_rascunho(im) for im in imgs]
        st("Gerando o vídeo…")
        mp4, aviso = gerar_video_paginas(
            imgs, base / "tabloide.mp4", seg_por_pagina=seg_por_pagina,
            fade_s=0.5 if fade else 0.0)
        if mp4 is not None:
            gerados.append(str(mp4))
    elif modo == "carrossel":
        st("Compondo os cards…")
        dados = [mesa._dados_de(it) for it in itens_sel]
        cards = compor_carrossel(dados, fundo=fundo)
        for i, im in enumerate(cards, 1):
            if marca:
                im = carimbar_rascunho(im)
            p = exportar_png(im, base / f"card_{i:02d}.png", 96)
            gerados.append(str(p))
    else:
        st("Compondo o destaque…")
        fmt = {"oferta": "oferta_do_dia", "story": "story",
               "faixa": "faixa"}[modo]
        im = compor_social(fmt, mesa._dados_de(item), fundo)
        if marca:
            im = carimbar_rascunho(im)
        gerados.append(str(exportar_png(im, base / f"{fmt}.png", 96)))
        if modo == "story" and story_mp4:
            st("Gerando o MP4 do Story…")
            mp4, aviso = gerar_video_story(im, base / "story.mp4",
                                           pulso_rect=_rect_preco_story_px())
            if mp4 is not None:
                gerados.append(str(mp4))
    return gerados, aviso, str(base)


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
        self.rb_carrossel.setToolTip("Um card por item — escolha e ordene "
                                     "quem entra na lista abaixo")
        self.rb_story = QRadioButton("Story / Reels (vertical)")
        self.rb_story.setToolTip("Formato vertical de tela cheia (9:16)")
        # OS F11.5 #7 (R-145): a FAIXA (banner 1920×1080) ganha a porta de UI
        self.rb_faixa = QRadioButton("Faixa / banner (1920×1080)")
        self.rb_faixa.setToolTip("Banner horizontal — capa de grupo, site, TV "
                                 "da loja")
        self.rb_video = QRadioButton("Vídeo do tabloide (páginas em MP4)")
        self.rb_video.setToolTip("As páginas do encarte viram um vídeo curto — "
                                 "precisa do componente “ffmpeg”")
        self.rb_oferta.setChecked(True)

        self.combo_item = QComboBox()
        for it in mesa._itens:
            self.combo_item.addItem(it.nome, it.uid)
        self.combo_item.setToolTip("Qual produto vai no destaque/Story/faixa")
        # OS F11.5 #32: o item SELECIONADO na estante da Mesa já vem escolhido
        try:
            linha = mesa.lista.currentRow()
            if 0 <= linha < len(mesa._itens):
                ix = self.combo_item.findData(mesa._itens[linha].uid)
                if ix >= 0:
                    self.combo_item.setCurrentIndex(ix)
        except Exception:
            pass

        # OS F11.5 #35: seleção E ordem do carrossel — lista com checkbox
        # (quem entra) e arrastar (em que ordem); só aparece no modo carrossel
        from PySide6.QtCore import Qt
        from PySide6.QtWidgets import QAbstractItemView, QListWidget
        self.lista_carrossel = QListWidget()
        self.lista_carrossel.setToolTip(
            "Marque quem entra no carrossel e arraste para mudar a ordem")
        self.lista_carrossel.setDragDropMode(
            QAbstractItemView.DragDropMode.InternalMove)
        self.lista_carrossel.setDefaultDropAction(Qt.DropAction.MoveAction)
        self.lista_carrossel.setMaximumHeight(160)
        for it in mesa._itens:
            from PySide6.QtWidgets import QListWidgetItem
            li = QListWidgetItem(it.nome)
            li.setFlags(li.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            li.setCheckState(Qt.CheckState.Checked)
            li.setData(Qt.ItemDataRole.UserRole, it.uid)
            self.lista_carrossel.addItem(li)
        self.lista_carrossel.hide()

        # OS F11.5 #37 (R-139): o MP4 animado do Story (opcional, se ffmpeg)
        from PySide6.QtWidgets import QCheckBox, QDoubleSpinBox
        self.chk_story_mp4 = QCheckBox("Também gerar o MP4 animado "
                                       "(o preço pulsa — para o Status)")
        self.chk_story_mp4.setToolTip("Além do PNG, um vídeo curto com a "
                                      "animação do preço — precisa do ffmpeg")
        self.chk_story_mp4.hide()
        # OS F11.5 #52: duração por página + fade no vídeo-tabloide
        self.spin_seg = QDoubleSpinBox()
        self.spin_seg.setRange(0.5, 15.0)
        self.spin_seg.setSingleStep(0.5)
        self.spin_seg.setValue(2.5)
        self.spin_seg.setSuffix(" s por página")
        self.spin_seg.setToolTip("Quanto tempo cada página fica na tela")
        self.chk_fade = QCheckBox("Transição suave (fade) entre páginas")
        self.chk_fade.setChecked(True)
        self.spin_seg.hide()
        self.chk_fade.hide()

        self._nota = QLabel("")
        self._nota.setProperty("papel", "legenda")
        self._nota.setWordWrap(True)

        # OS F11.5 #85/#94: "Abrir com…" (WhatsApp Desktop entra pela porta do
        # Windows) + a LIMITAÇÃO honesta visível — nunca prometer automação
        from app.qt.telas import compartilhar
        self.btn_abrir_com = QPushButton("Abrir com… (WhatsApp)")
        self.btn_abrir_com.setToolTip(compartilhar.LIMITACAO_SO)
        self.btn_abrir_com.setEnabled(False)
        self.btn_abrir_com.clicked.connect(self._abrir_com)
        self._lbl_limitacao = QLabel(compartilhar.LIMITACAO_SO)
        self._lbl_limitacao.setProperty("papel", "legenda")
        self._lbl_limitacao.setWordWrap(True)

        self._radios = (self.rb_oferta, self.rb_carrossel, self.rb_story,
                        self.rb_faixa, self.rb_video)
        self._atualizar_nota()
        for rb in self._radios:
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
        rodape.addWidget(self.btn_abrir_com)
        rodape.addStretch(1)
        rodape.addWidget(fechar)
        rodape.addWidget(gerar)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(t.ESP_4, t.ESP_4, t.ESP_4, t.ESP_4)
        lay.setSpacing(t.ESP_2)
        lay.addWidget(titulo)
        for rb in self._radios:
            lay.addWidget(rb)
        lay.addWidget(self.lista_carrossel)
        lay.addWidget(self.chk_story_mp4)
        lay.addWidget(self.spin_seg)
        lay.addWidget(self.chk_fade)
        lay.addSpacing(t.ESP_2)
        rotulo_destaque = QLabel("Produto do destaque:")
        rotulo_destaque.setProperty("papel", "legenda")
        lay.addWidget(rotulo_destaque)
        lay.addWidget(self.combo_item)
        lay.addWidget(self._nota)
        lay.addWidget(self._lbl_limitacao)
        lay.addLayout(rodape)

        self._overlay = OverlayOcupado(self)

    def _abrir_com(self):
        from app.qt.telas import compartilhar
        alvo = getattr(self, "_ultimo_gerado", None)
        if alvo:
            compartilhar.abrir_com(alvo)

    def _atualizar_nota(self, *_):
        so_item = (self.rb_oferta.isChecked() or self.rb_story.isChecked()
                   or self.rb_faixa.isChecked())
        self.combo_item.setEnabled(so_item)
        self.lista_carrossel.setVisible(self.rb_carrossel.isChecked())
        from app.rendering.video import ffmpeg_disponivel as _ff
        self.chk_story_mp4.setVisible(self.rb_story.isChecked()
                                      and _ff() is not None)
        self.spin_seg.setVisible(self.rb_video.isChecked())
        self.chk_fade.setVisible(self.rb_video.isChecked())
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

    def _itens_do_carrossel(self):
        """#35: os itens MARCADOS, na ordem ATUAL da lista (por uid, I1)."""
        from PySide6.QtCore import Qt
        por_uid = {it.uid: it for it in self.mesa._itens}
        saida = []
        for i in range(self.lista_carrossel.count()):
            li = self.lista_carrossel.item(i)
            if li.checkState() == Qt.CheckState.Checked:
                it = por_uid.get(li.data(Qt.ItemDataRole.UserRole))
                if it is not None:
                    saida.append(it)
        return saida

    def _modo(self) -> str:
        return ("oferta" if self.rb_oferta.isChecked() else
                "carrossel" if self.rb_carrossel.isChecked() else
                "story" if self.rb_story.isChecked() else
                "faixa" if self.rb_faixa.isChecked() else "video")

    def _gerar(self):
        if not self.mesa._itens:
            mostrar_toast(self, "Não há itens na oferta.", tipo="erro")
            return
        modo = self._modo()
        itens_sel = (self._itens_do_carrossel() if modo == "carrossel"
                     else self.mesa._itens)
        if modo == "carrossel" and not itens_sel:
            mostrar_toast(self, "Marque ao menos um produto para o carrossel.",
                          tipo="erro")
            return
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
        story_mp4 = self.chk_story_mp4.isChecked() and self.chk_story_mp4.isVisible()
        seg = float(self.spin_seg.value())
        fade = bool(self.chk_fade.isChecked())
        # OS F11.5 #40: a ARTE do projeto atravessa até os cards sociais
        fundo = mesa._fundo if getattr(mesa, "_fundo", None) else None

        def _trabalho(st):
            return _compor_publicacao(
                mesa, modo, Path(pasta), marca, item, itens_sel, st,
                fundo=fundo, story_mp4=story_mp4, seg_por_pagina=seg,
                fade=fade)

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
        # R-064: compartilhar o primeiro gerado (copiar imagem / abrir pasta);
        # #85: "Abrir com…" acorda apontando para ele
        self._ultimo_gerado = gerados[0]
        self.btn_abrir_com.setEnabled(True)
        from app.qt.telas import compartilhar
        if gerados[0].lower().endswith(".png"):
            compartilhar.copiar_imagem(gerados[0])
        compartilhar.abrir_pasta(gerados[0])

    def done(self, resultado: int) -> None:  # noqa: N802 (Qt)
        # lei exit-0: nenhum worker vivo quando o diálogo fecha
        self._trabalhos.encerrar()
        super().done(resultado)

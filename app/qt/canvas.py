"""
Canvas base do editor (F5.1)
============================
Um ``QGraphicsView`` que mostra o **preview renderizado pelo compositor Pillow**
(F2) como um pixmap. O Qt só cuida de ver: zoom (roda), pan (arrastar), réguas
em mm. A seleção/alças vêm na F5.2.

Coordenadas da cena = pixels da imagem composta (no DPI do layout). Então
cena↔mm é só uma conversão pelo DPI — consistente com o resto do sistema.
"""

from __future__ import annotations

from PySide6.QtCore import QPointF, QRectF, Qt, Signal
from PySide6.QtGui import QColor, QImage, QPainter, QPen, QPixmap, QRadialGradient
from PySide6.QtWidgets import (
    QGraphicsItem,
    QGraphicsLineItem,
    QGraphicsPixmapItem,
    QGraphicsScene,
    QGraphicsView,
    QGridLayout,
    QWidget,
)
from PIL import Image

from app.qt.design import tokens as t
from app.qt.itens import RegiaoItem
from app.rendering.compositor import DadosProduto, compor_pagina
from app.rendering.model import LayoutDef
from app.rendering.units import mm_para_px, px_para_mm


def pil_para_qpixmap(img: Image.Image) -> QPixmap:
    """Converte uma imagem Pillow em QPixmap (com cópia própria dos bytes)."""
    img = img.convert("RGBA")
    qimg = QImage(img.tobytes("raw", "RGBA"), img.width, img.height, QImage.Format.Format_RGBA8888)
    return QPixmap.fromImage(qimg.copy())


# RG-05: o zoom por roda não tinha limite — girando para baixo a escala caía
# a <2% (página invisível, "canvas cinza") e cada repaint custava segundos.
# A janela [5%, 800%] mantém a página sempre visível e o paint barato.
ESCALA_MIN = 0.05
ESCALA_MAX = 8.0

# Espaçamentos possíveis das marcas da régua (mm) e o respiro mínimo entre
# marcas na tela. Escolher o passo pelo zoom mantém a régua legível e o
# laço de pintura pequeno em QUALQUER escala (RG-05: com passo fixo de
# 10 mm, zoom mínimo = milhares de marcas por pintura — a régua virava um
# borrão e o paint, segundos).
PASSOS_REGUA_MM = (10, 20, 50, 100, 200, 500, 1000, 2000, 5000,
                   10000, 20000, 50000)
_MIN_PX_ENTRE_MARCAS = 36


def passo_da_regua(px_por_mm: float) -> int:
    """Espaçamento das marcas (mm) para a régua ficar legível neste zoom."""
    for passo in PASSOS_REGUA_MM:
        if px_por_mm * passo >= _MIN_PX_ENTRE_MARCAS:
            return passo
    return PASSOS_REGUA_MM[-1]


class CanvasView(QGraphicsView):
    """Mostra o preview composto; interação de visualização apenas."""

    transformou = Signal()       # zoom/pan/resize (para as réguas)
    editou = Signal(object)      # uma região foi editada (para o painel de camadas)
    selecao_mudou = Signal(object)  # a região selecionada mudou (para propriedades)
    medidas = Signal(str)        # R-041: X/Y/L/A em mm ao vivo (mover/redimensionar)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._scene = QGraphicsScene(self)
        self.setScene(self._scene)
        self._scene.selectionChanged.connect(self._emitir_selecao)
        self._bg: QGraphicsPixmapItem | None = None
        self._itens: list[RegiaoItem] = []
        self._layout: LayoutDef | None = None
        self._dados: DadosProduto | None = None
        self._fundo = None

        self._guias: list = []
        self._historico = None         # criado no carregar (F5.10)
        self._area_transferencia: dict | None = None   # região copiada (Ctrl+C)
        self._estilo_copiado = None      # R-031: retrato do estilo (conta-gotas)
        self.mapa: dict[str, str] = {}   # slot_id → item.uid (I1; D5: versiona junto)
        # F7.3 (B do Bloco E): override de CONTEÚDO por slot — slot_id →
        # {campo: valor}. Identidade, nunca posição (I1); versiona no histórico.
        self.overrides: dict[str, dict] = {}
        self.ao_restaurar = None         # callback pós-undo (a Mesa realimenta dados)
        self.ao_override = None          # callable(slot_id) → a Mesa abre o modal
        self.ao_soltar_imagem = None     # R-038: callable(slot_id, caminho) → Mesa
        self.setAcceptDrops(True)        # R-038: arrastar PNG/JPG sobre a célula
        self._pagina_atual = 0           # D8.4: UMA página por vez, navegável
        # RG-55 (Fase 4): a região efetivamente CLICADA. Com o trio da célula
        # selecionado (RG-15), é ela que o painel mostra — nunca "órfão" (I2).
        self._primaria = None
        self._raio_x = False             # R-040: modo estrutura (sem a arte)
        self._arte_travada = True        # R-039: a arte de fundo é protegida
        self._ajuste_pendente = False    # RG-05: fit pedido antes do 1º layout real
        self.guia_z = False              # RG-42: sobreposição do padrão Z de leitura
        self.setDragMode(QGraphicsView.DragMode.RubberBandDrag)  # seleção múltipla; espaço = pan
        # RG-11: barras SEMPRE visíveis (o dono não sabia que dava para rolar)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        self.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setFrameShape(QGraphicsView.Shape.NoFrame)

    def drawBackground(self, painter: QPainter, rect: QRectF) -> None:
        """Mesa de trabalho: fundo dos tokens + vinheta sutil + sombra da página."""
        painter.fillRect(rect, QColor(t.CANVAS_FUNDO))
        pagina = self._scene.sceneRect()
        if pagina.isEmpty():
            return
        # vinheta: escurece de leve longe da página (foco no trabalho)
        raio = max(pagina.width(), pagina.height()) * 1.6
        grad = QRadialGradient(pagina.center(), raio)
        vin = QColor(t.CANVAS_VINHETA)
        vin.setAlpha(0)
        grad.setColorAt(0.55, vin)
        vin = QColor(t.CANVAS_VINHETA)
        vin.setAlpha(110)
        grad.setColorAt(1.0, vin)
        painter.fillRect(rect, grad)
        # sombra suave sob a página (camadas concêntricas com alpha caindo)
        sombra = QColor(t.PAGINA_SOMBRA)
        painter.setPen(Qt.PenStyle.NoPen)
        escala = max(self.transform().m11(), 1e-6)   # espessura constante na tela
        for i, alpha in enumerate((26, 18, 12, 7, 3), start=1):
            sombra.setAlpha(alpha)
            painter.setBrush(sombra)
            d = i * 1.6 / escala
            painter.drawRoundedRect(pagina.adjusted(-d, -d * 0.4, d, d * 1.6),
                                    d, d)
        # R-028 (reauditoria F4): a grade magnética agora APARECE — linhas
        # finas nos múltiplos do passo, sobre a página, quando ligada (antes
        # o snap existia mas era invisível)
        pag = self._pagina() if self._layout is not None else None
        if pag is not None and pag.grade_magnetica and pag.grade_passo_mm > 0:
            passo_px, _ = self.mm_para_cena(pag.grade_passo_mm, 0)
            if passo_px >= 2:
                caneta = QPen(QColor(t.GUIA_SNAP), 0)
                caneta.setCosmetic(True)
                cor = QColor(t.GUIA_SNAP)
                cor.setAlpha(60)
                caneta.setColor(cor)
                painter.setPen(caneta)
                painter.setBrush(Qt.BrushStyle.NoBrush)
                x = 0.0
                while x <= pagina.width():
                    painter.drawLine(QPointF(x, 0), QPointF(x, pagina.height()))
                    x += passo_px
                y = 0.0
                while y <= pagina.height():
                    painter.drawLine(QPointF(0, y), QPointF(pagina.width(), y))
                    y += passo_px

    def drawForeground(self, painter: QPainter, rect: QRectF) -> None:
        """RG-42: guia Z opcional — o caminho do olho (pesquisa §1) por cima
        da página, SÓ no editor (nunca vai para a exportação)."""
        super().drawForeground(painter, rect)
        if not self.guia_z or self._scene.sceneRect().isEmpty():
            return
        p = self._scene.sceneRect()
        esc = max(self.transform().m11(), 1e-6)
        cor = QColor(t.GUIA_SNAP)
        cor.setAlpha(120)
        painter.setPen(QPen(cor, 3.0 / esc, Qt.PenStyle.DashLine))
        m = p.width() * 0.08
        topo, base = p.top() + p.height() * 0.12, p.bottom() - p.height() * 0.12
        painter.drawLine(p.left() + m, topo, p.right() - m, topo)
        painter.drawLine(p.right() - m, topo, p.left() + m, base)
        painter.drawLine(p.left() + m, base, p.right() - m, base)

    def alternar_guia_z(self) -> None:
        self.guia_z = not self.guia_z
        self.viewport().update()

    # --- carregar / atualizar o preview ---------------------------------------

    def carregar(self, layout: LayoutDef, dados: DadosProduto, fundo_path=None) -> None:
        self._layout, self._dados, self._fundo = layout, dados, fundo_path
        self._pagina_atual = 0
        self._scene.clear()
        self._bg = None
        self._itens = []
        self._guias = []          # scene.clear() já removeu os itens de guia
        self._guias_usuario = []
        self._compor_fundo()
        self._scene.setSceneRect(self._bg.boundingRect())
        self._construir_itens()
        self._redesenhar_guias_usuario()     # R-027: guias persistidas
        self.ajustar()
        from app.qt.historico import Historico
        self._historico = Historico()
        # baseline {layout, mapa, overrides}
        self._historico.registrar(layout, self.mapa, self.overrides)

    def atualizar(self, dados: DadosProduto | None = None) -> None:
        """Re-renderiza pelo compositor (WYSIWYG) quando os dados mudam."""
        if dados is not None:
            self._dados = dados
        self._compor_fundo()

    # --- páginas (D8.4) ----------------------------------------------------------

    def _pagina(self):
        """A página ATUAL — todo o canvas opera sobre ela (D8.4)."""
        return self._layout.paginas[self._pagina_atual]

    @property
    def pagina_atual(self) -> int:
        return self._pagina_atual

    def total_paginas(self) -> int:
        return len(self._layout.paginas) if self._layout else 0

    def ir_para_pagina(self, i: int) -> None:
        if self._layout is None:
            return
        i = max(0, min(i, len(self._layout.paginas) - 1))
        if i == self._pagina_atual:
            return
        self._pagina_atual = i
        self._scene.clearSelection()
        self._compor_fundo()
        self._scene.setSceneRect(self._bg.boundingRect())
        self._construir_itens()
        self.ajustar()
        self.editou.emit(None)

    def adicionar_pagina_arte(self, caminho_arte: str) -> None:
        """Página nova com a própria arte/detecção (D8.1: ids uuid, únicos)."""
        from app.rendering.grade import adicionar_pagina_de_arte

        adicionar_pagina_de_arte(self._layout, caminho_arte)
        self._registrar_hist()
        self.ir_para_pagina(len(self._layout.paginas) - 1)

    def remover_pagina_atual(self) -> bool:
        """D8.4: remove a página; itens dela voltam à estante (mapa perde as
        entradas). Undo restaura página E mapa juntos (D5)."""
        if self._layout is None or len(self._layout.paginas) <= 1:
            return False
        pagina = self._pagina()
        ids = {s.id for s in pagina.slots}
        self._layout.paginas.remove(pagina)
        for sid in ids:
            self.mapa.pop(sid, None)
        self._pagina_atual = min(self._pagina_atual,
                                 len(self._layout.paginas) - 1)
        self._registrar_hist()
        if callable(self.ao_restaurar):
            self.ao_restaurar()
        self._compor_fundo()
        self._scene.setSceneRect(self._bg.boundingRect())
        self._construir_itens()
        self.ajustar()
        self.editou.emit(None)
        return True

    def duplicar_pagina_atual(self) -> None:
        """R-030: duplica a página atual. Slots e regiões ganham IDENTIDADE
        NOVA (ids únicos D8.1, uids frescos I1) e a cópia nasce SEM vínculo de
        grupo (células independentes) — nada compartilha estado com o original."""
        if self._layout is None:
            return
        import uuid

        from app.rendering.model import Pagina
        nova = Pagina.from_dict(self._pagina().to_dict())
        for s in nova.slots:
            s.id = f"celula_{uuid.uuid4().hex[:8]}"
            s.mestre, s.ref_grupo = False, None
            for r in s.regioes:
                r.uid = uuid.uuid4().hex
                r.de_mestre, r.ref_mestre, r.overrides = False, None, set()
        self._layout.paginas.insert(self._pagina_atual + 1, nova)
        self._registrar_hist()
        self.ir_para_pagina(self._pagina_atual + 1)

    def mover_pagina(self, de: int, para: int) -> bool:
        """R-030: reordena páginas arrastando a miniatura (a ordem reflete no
        PDF). Devolve True se moveu."""
        if self._layout is None:
            return False
        n = len(self._layout.paginas)
        if not (0 <= de < n) or not (0 <= para < n) or de == para:
            return False
        pag = self._layout.paginas.pop(de)
        self._layout.paginas.insert(para, pag)
        self._registrar_hist()
        self._pagina_atual = para
        self.ir_para_pagina(para)
        return True

    def _compor_fundo(self) -> None:
        """Recompõe o preview (fundo) pelo compositor Pillow — sem tocar nas alças."""
        if self._layout is None or self._dados is None:
            return
        # D8.2: o _fundo explícito (legado) só vale na página 1; nas demais a
        # arte é da própria página (pagina.arquivo_fundo, via compositor)
        fundo = self._fundo if self._pagina_atual == 0 else None
        img = compor_pagina(self._layout, self._pagina(), self._dados, fundo_path=fundo)
        pm = pil_para_qpixmap(img)
        if self._bg is None:
            self._bg = self._scene.addPixmap(pm)
            self._bg.setZValue(0)
        else:
            self._bg.setPixmap(pm)
        # R-039: o cadeado CONSOME o estado — a arte só é selecionável quando
        # destravada (nunca movível: é fundo de página inteira, decisão travada)
        self._bg.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable,
                         not self.arte_travada())

    def recompor(self) -> None:
        self._compor_fundo()

    def ajustar(self) -> None:
        """Enquadra a página inteira na viewport.

        RG-05: com o boot em duas fases as telas carregam ANTES de aparecer;
        o fitInView com viewport ainda sem layout (dezenas de px) deixava a
        escala microscópica ("Zoom 2%"). Sem tamanho real, o fit fica
        pendente e acontece no primeiro show/resize de verdade.
        """
        if self._bg is None:
            return
        vp = self.viewport()
        if vp.width() < 80 or vp.height() < 80:
            self._ajuste_pendente = True
            return
        self._ajuste_pendente = False
        # FASE 1 (passo 46): zoom/pan animado curto (160 ms) até o
        # enquadramento — o corte seco desorientava na troca de página.
        # Técnica: fit seco → capturar o alvo → voltar → animar até lá.
        from app.qt.design.animacoes import animacoes_ligadas, registrar
        t_antes = self.transform()
        c_antes = self.mapToScene(self.viewport().rect().center())
        self.fitInView(self._bg, Qt.AspectRatioMode.KeepAspectRatio)
        # janela WA_DontShowOnScreen = captura de foto: o grab precisa do
        # enquadramento FINAL, nunca de um quadro no meio do movimento
        if (not animacoes_ligadas() or not self.isVisible()
                or self.window().testAttribute(
                    Qt.WidgetAttribute.WA_DontShowOnScreen)):
            self.transformou.emit()
            return
        s_alvo = self.transform().m11()
        c_alvo = self.mapToScene(self.viewport().rect().center())
        s0 = t_antes.m11()
        if abs(s_alvo - s0) < 1e-6 and \
                (c_alvo - c_antes).manhattanLength() < 1.0:
            self.transformou.emit()      # já estava enquadrado
            return
        anterior = getattr(self, "_anim_ajuste", None)
        if anterior is not None:
            anterior.stop()
        self.setTransform(t_antes)
        self.centerOn(c_antes)
        from PySide6.QtCore import QEasingCurve, QVariantAnimation
        from PySide6.QtGui import QTransform
        anim = QVariantAnimation(self)
        anim.setDuration(160)
        anim.setStartValue(0.0)
        anim.setEndValue(1.0)
        anim.setEasingCurve(QEasingCurve.Type.OutCubic)

        def _quadro(f) -> None:
            f = float(f)
            s = s0 + (s_alvo - s0) * f
            self.setTransform(QTransform().scale(s, s))
            self.centerOn(c_antes.x() + (c_alvo.x() - c_antes.x()) * f,
                          c_antes.y() + (c_alvo.y() - c_antes.y()) * f)
            self.transformou.emit()      # o zoom do rodapé acompanha vivo

        def _fechar() -> None:           # fecha EXATO no enquadramento
            if self._bg is not None:     # layout pode ter sido fechado no meio
                self.fitInView(self._bg, Qt.AspectRatioMode.KeepAspectRatio)
            self.transformou.emit()

        anim.valueChanged.connect(_quadro)
        anim.finished.connect(_fechar)
        self._anim_ajuste = anim
        registrar(anim)
        anim.start()

    def escala_atual(self) -> float:
        return self.transform().m11()

    def showEvent(self, event) -> None:
        super().showEvent(event)
        if self._ajuste_pendente:
            self.ajustar()

    # --- regiões / alças interativas ------------------------------------------

    def regioes(self) -> list:
        if self._layout is None:
            return []
        return [reg for slot in self._pagina().slots for reg in slot.regioes]

    def _construir_itens(self) -> None:
        for it in self._itens:
            self._scene.removeItem(it)
        self._itens = []
        for reg in self.regioes():
            w, h = self.mm_para_cena(reg.rect.larg_mm, reg.rect.alt_mm)
            item = RegiaoItem(reg, w, h, self)
            x, y = self.mm_para_cena(reg.rect.x_mm, reg.rect.y_mm)
            item.setPos(x, y)
            item.setZValue(10)
            item.setVisible(reg.visivel)
            item.setToolTip(self.legenda_de_grupo(reg))   # RG-56 passo 21
            self._scene.addItem(item)
            self._itens.append(item)

    def legenda_de_grupo(self, reg) -> str:
        """Passo 21: a legenda PT-BR simples do estado agrupável (tooltip do
        badge). Mestra/Cópia/Solta — com o N verdadeiro de ajustes na cópia."""
        estado = self.estado_de_grupo(reg)
        if estado == "mestra":
            return "Mestra: as edições replicam nas cópias."
        if estado == "copia":
            n = self.ajustes_da_regiao(reg)
            if n:
                return f"Cópia: {n} ajuste{'s' if n > 1 else ''} próprio" \
                       f"{'s' if n > 1 else ''} (não segue a mestra nisso)."
            return "Cópia: segue a mestra (sem ajustes próprios)."
        return "Solta: sem grupo."

    def reconstruir_itens(self) -> None:
        self._construir_itens()

    def _commit_regiao(self, item: RegiaoItem) -> None:
        """Ao soltar: muta o modelo (mm) e recompõe pelo Pillow (WYSIWYG)."""
        r = item.rect_cena()
        reg = item.regiao
        reg.rect.x_mm, reg.rect.y_mm = self.cena_para_mm(r.x(), r.y())
        reg.rect.larg_mm, reg.rect.alt_mm = self.cena_para_mm(r.width(), r.height())
        self._apos_edicao(reg, "rect")
        self._registrar_hist()
        self._compor_fundo()
        self.editou.emit(reg)

    # --- histórico (F5.10): desfazer/refazer + copiar/colar ---------------------

    def _registrar_hist(self) -> None:
        if self._historico is not None and self._layout is not None:
            self._historico.registrar(self._layout, self.mapa, self.overrides)

    def set_override(self, slot_id: str, ov: dict | None) -> None:
        """F7.3: define/limpa o override de conteúdo do slot (1 estado de undo).

        Passa pelo MESMO caminho do undo (``ao_restaurar``): a Mesa realimenta
        a composição já com a precedência override > item > banco.
        """
        if ov:
            self.overrides[slot_id] = dict(ov)
        else:
            self.overrides.pop(slot_id, None)
        self._registrar_hist()
        if callable(self.ao_restaurar):
            self.ao_restaurar()
        self._compor_fundo()
        self.viewport().update()         # o indicador aparece/some na hora

    def trocar_conteudo_slots(self, sid_a: str, sid_b: str) -> bool:
        """R-057 (Fase 6): TROCA os itens de duas células — troca de uid no
        mapa (I1: identidade, não posição). Os OVERRIDES ficam no SLOT (o dono
        ajustou AQUELA célula, passo 65). Undo unificado (molde do set_override)."""
        if sid_a == sid_b:
            return False
        ua, ub = self.mapa.get(sid_a), self.mapa.get(sid_b)
        for sid, uid in ((sid_a, ub), (sid_b, ua)):
            if uid is None:
                self.mapa.pop(sid, None)
            else:
                self.mapa[sid] = uid
        self._registrar_hist()
        if callable(self.ao_restaurar):
            self.ao_restaurar()
        self._compor_fundo()
        self.viewport().update()
        return True

    def reatribuir_mapa(self, novo_mapa: dict) -> None:
        """R-055 (Fase 6): reordenar a estante re-atribui o mapa slot→uid na
        nova ordem (por uid, I1). Undo unificado."""
        self.mapa = dict(novo_mapa)
        self._registrar_hist()
        if callable(self.ao_restaurar):
            self.ao_restaurar()
        self._compor_fundo()
        self.viewport().update()

    def _aplicar_estado(self, layout, mapa: dict, overrides: dict) -> None:
        """Troca {layout, mapa, overrides} pelo estado do histórico.

        D5: o mapa volta JUNTO — desfazer a remoção de uma célula restaura o
        slot E a entrada do mapa; B3: o override do slot idem (desfazer um
        override restaura o anterior). ``ao_restaurar`` deixa a tela dona dos
        dados (Mesa) realimentar a composição por mapa.
        """
        self._layout = layout
        self.mapa = mapa
        self.overrides = overrides
        # D8.4: o undo pode restaurar um layout com MENOS páginas — clampa
        self._pagina_atual = min(self._pagina_atual, len(layout.paginas) - 1)
        if callable(self.ao_restaurar):
            self.ao_restaurar()          # a Mesa refaz _dados pelo mapa novo
        self._compor_fundo()
        self._construir_itens()
        self._redesenhar_guias_usuario()   # R-027: guias voltam com o undo
        self.editou.emit(None)
        self.selecao_mudou.emit(None)

    def desfazer(self) -> bool:
        estado = self._historico.desfazer() if self._historico else None
        if estado is None:
            return False
        self._aplicar_estado(*estado)
        return True

    def refazer(self) -> bool:
        estado = self._historico.refazer() if self._historico else None
        if estado is None:
            return False
        self._aplicar_estado(*estado)
        return True

    def ir_para_estado(self, i: int) -> bool:
        """R-042 (histórico visual): salta direto para o estado ``i`` — volta
        layout E mapa E overrides juntos (undo unificado, D5/B3)."""
        estado = self._historico.ir_para(i) if self._historico else None
        if estado is None:
            return False
        self._aplicar_estado(*estado)
        return True

    def historico_total(self) -> int:
        return self._historico.total() if self._historico else 0

    def historico_indice(self) -> int:
        return self._historico.indice() if self._historico else -1

    def miniatura_pagina(self, i: int, lado: int = 140):
        """R-030: QPixmap da página ``i`` (composta pelo compositor)."""
        if self._layout is None or not (0 <= i < len(self._layout.paginas)):
            return None
        fundo = self._fundo if i == 0 else None
        img = compor_pagina(self._layout, self._layout.paginas[i],
                            self._dados, fundo_path=fundo)
        return pil_para_qpixmap(img).scaled(
            lado, lado, Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation)

    def miniatura_estado(self, i: int, lado: int = 100):
        """R-042: QPixmap do estado ``i`` do histórico (sem mover o cursor)."""
        if self._historico is None:
            return None
        est = self._historico.estado_em(i)
        if est is None:
            return None
        layout, _mapa, _ov = est
        pag = layout.paginas[min(self._pagina_atual, len(layout.paginas) - 1)]
        img = compor_pagina(layout, pag, self._dados)
        return pil_para_qpixmap(img).scaled(
            lado, lado, Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation)

    def atualizar_dados(self, dados, *, compor: bool = True) -> None:
        """Troca os dados compostos SEM resetar o histórico (pós-undo/remoção)."""
        self._dados = dados
        if compor:
            self._compor_fundo()

    # --- grupos livres (F5.6) ----------------------------------------------------

    def _avisar(self, texto: str) -> None:
        """Aviso leve na janela (C2: recusa NUNCA é silenciosa)."""
        try:
            from app.qt.design.toast import mostrar_toast
            mostrar_toast(self, texto, tipo="erro")
        except Exception:
            pass                          # sem janela (headless): só recusa

    def agrupar_selecao(self):
        """C2: SÓ regiões livres (avulsas) viram grupo replicável.

        Recusa com aviso: regiões derivadas (a propagação recriaria o conteúdo
        na célula — duplicação silenciosa) e regiões de um mestre (a propagação
        as removeria de TODAS as cópias — destruição em grade).
        """
        from app.rendering.grade import agrupar_como_mestre, slots_do_grupo

        itens = self.selecionados()
        if len(itens) < 1:
            return None
        regs = [it.regiao for it in itens]
        slots = {id(self._slot_de(r)) for r in regs}
        if len(slots) != 1:
            self._avisar("Agrupar: selecione regiões do mesmo lugar "
                         "(as selecionadas estão em células diferentes).")
            return None
        # passo 22 (lei da casa, reavaliada porque a fase mexe em agrupamento):
        # SELO e TEXTO_LEGAL são decorativos/automáticos — nunca viram mestre
        from app.rendering.grade import TIPOS_CONTEUDO
        if any(r.tipo not in TIPOS_CONTEUDO for r in regs):
            self._avisar("Agrupar: selo e texto legal não entram no grupo "
                         "replicável — só imagem, nome, preço e unidade.")
            return None
        origem = self._slot_de(regs[0])
        if origem.ref_grupo is not None or any(r.ref_mestre for r in regs):
            self._avisar("Essas regiões são cópias de um grupo — edite o "
                         "grupo-mestre (ou restaure da mestra) em vez de reagrupar.")
            return None
        if origem.mestre:
            n = len(slots_do_grupo(self._pagina(), origem))
            self._avisar("Essas regiões já são de um mestre"
                         + (f" com {n} cópia(s)" if n else "")
                         + " — carimbe cópias em vez de reagrupar.")
            return None
        novo = agrupar_como_mestre(self._pagina(), regs, origem,
                                   mapa=self.mapa)   # C5.3: limpa a origem vazia
        self._registrar_hist()
        self._compor_fundo()
        self._construir_itens()
        self.editou.emit(None)
        return novo

    def carimbar_grupo(self, mestre_id: str, ancora_mm: tuple):
        """Carimba uma cópia do grupo na âncora (D4)."""
        from app.rendering.grade import carimbar_copia

        mestre = next((s for s in self._pagina().slots
                       if s.id == mestre_id and s.mestre), None)
        if mestre is None:
            return None
        copia = carimbar_copia(self._pagina(), mestre, ancora_mm)
        self._registrar_hist()
        self._compor_fundo()
        self._construir_itens()
        self.editou.emit(None)
        return copia

    def remover_celula(self, slot_id: str) -> bool:
        """D3: remove a célula; o item volta a 'fora da grade' (mapa perde a
        entrada); vizinhos NÃO se movem; mestre removido promove a cópia
        mais antiga. Tudo desfazível como UM estado (D5)."""
        from app.rendering.grade import remover_slot

        slot = remover_slot(self._pagina(), slot_id)
        if slot is None:
            return False
        self.mapa.pop(slot_id, None)
        self._registrar_hist()
        if callable(self.ao_restaurar):
            self.ao_restaurar()
        self._compor_fundo()
        self._construir_itens()
        self.editou.emit(None)
        return True

    # --- RG-56 (Fase 4): agrupar/desagrupar VISÍVEL e REVERSÍVEL ---------------

    def estado_de_grupo(self, reg) -> str:
        """O estado agrupável da região — 'mestra' | 'copia' | 'solta'. Fonte
        ÚNICA de verdade para o menu de contexto, o badge e a legenda."""
        slot = self._slot_de(reg)
        if slot is None:
            return "solta"
        if slot.mestre:
            return "mestra"
        if slot.ref_grupo is not None:
            return "copia"
        return "solta"

    def ajustes_da_regiao(self, reg) -> int:
        """Passo 19: quantos ajustes de ESTILO/GEOMETRIA a cópia tem próprios
        (os que "Restaurar da mestra" desfaz). É o MESMO N do menu — badge,
        legenda e menu batem (o override de CONTEÚDO do slot, F7.3, tem
        indicador e ação próprios: o pontinho violeta e "Restaurar do item")."""
        return len(reg.overrides)

    def desagrupar_regiao(self, reg) -> bool:
        """RG-56: dissolve o grupo da região (mestre + cópias viram SOLTOS),
        cada um com seus valores atuais — nada se perde (passo 23). UM único
        estado de undo: mapa + layout andam juntos (passo 24; ids preservados,
        I1). Devolve False se a região não está agrupada."""
        from app.rendering.grade import desagrupar_grupo

        slot = self._slot_de(reg)
        if slot is None:
            return False
        grupo = desagrupar_grupo(self._pagina(), slot)
        if not grupo:
            return False
        self._registrar_hist()
        self._compor_fundo()
        self._construir_itens()
        self.editou.emit(None)
        return True

    def editar_como_mestra(self, reg) -> None:
        """Passo 17: seleciona a célula-mestre (o trio) e avisa que o que se
        editar aqui replica nas cópias — torna a edição da mestra consciente."""
        slot = self._slot_de(reg)
        if slot is None or not slot.mestre:
            return
        self._primaria = reg
        for it in self._itens:                       # identidade, nunca valor (I1)
            it.setSelected(any(it.regiao is r for r in slot.regioes))
        self._emitir_selecao()
        try:
            from app.qt.design.toast import mostrar_toast
            mostrar_toast(self, "Editando a célula-mestre — o que você mudar "
                                "aqui replica nas cópias.")
        except Exception:
            pass                          # headless: só seleciona

    def abrir_tutorial_agrupar(self, primeira_vez: bool = False) -> None:
        """Passos 25-26: o microtutorial de 3 telas do agrupamento. Abre
        sozinho na 1ª vez que o dono agrupa (``primeira_vez``, com memória em
        Config) e fica sempre acessível pelo menu Ajuda."""
        try:
            from app.qt.design.tutorial_agrupar import mostrar_tutorial_agrupar
            mostrar_tutorial_agrupar(self, so_se_primeira_vez=primeira_vez)
        except Exception:
            pass                          # headless: nunca derruba o gesto

    def copiar_selecao(self) -> bool:
        reg = self.selecionada()
        if reg is None:
            return False
        self._area_transferencia = reg.to_dict()
        return True

    def colar(self):
        """Cola a região copiada no slot da seleção atual (ou no primeiro)."""
        if self._area_transferencia is None or self._layout is None:
            return None
        from app.rendering.model import Regiao

        # C1 vale para colar também: sem seleção, nunca cair no mestre da grade
        alvo = self._slot_para_novas_regioes()
        copia = Regiao.from_dict(self._area_transferencia)
        import uuid
        copia.uid = uuid.uuid4().hex        # identidade própria (I1)
        copia.ref_mestre = None
        copia.rect.x_mm += 4
        copia.rect.y_mm += 4
        copia.overrides = set()
        copia.de_mestre = alvo.mestre       # colou na mestra → replica
        alvo.regioes.append(copia)
        self._apos_edicao(copia, None)
        self._registrar_hist()
        self._compor_fundo()
        self._construir_itens()
        for it in self._itens:
            it.setSelected(it.regiao is copia)
        self.editou.emit(copia)
        return copia

    # --- célula-mestre (F5.5): propagação e overrides ---------------------------

    def eh_mestre(self, reg) -> bool:
        """A região pertence à célula-mestre?"""
        slot = self._slot_de(reg)
        return bool(slot is not None and slot.mestre)

    def _apos_edicao(self, reg, attr: str | None) -> None:
        """Depois de editar uma região: propaga (mestra) ou marca override (célula)."""
        from app.rendering.grade import ATRIBUTOS_ESTILO, propagar_mestre

        slot = self._slot_de(reg)
        if slot is None or self._layout is None:
            return
        if slot.mestre:
            propagar_mestre(self._pagina())
            self._reconstruir_depois()   # a geometria das outras células mudou
        elif (slot.origem_mm is not None and reg.de_mestre and attr
              and (attr in ATRIBUTOS_ESTILO or attr == "rect")):
            reg.overrides.add(attr)      # o ajuste local vence a mestra e persiste

    def _reconstruir_depois(self) -> None:
        """Reconstrói os itens no próximo ciclo (seguro dentro de eventos de item)."""
        from PySide6.QtCore import QTimer

        QTimer.singleShot(0, self._construir_itens)

    # --- estilos nomeados (F5.7) --------------------------------------------------

    def definir_estilo_layout(self, estilo) -> int:
        """Cria/atualiza um estilo e re-aplica no layout inteiro (1 estado de undo)."""
        from app.rendering.estilos import definir_estilo
        from app.rendering.grade import propagar_mestre

        n = definir_estilo(self._layout, estilo)
        propagar_mestre(self._pagina())   # mestres re-estilizados propagam
        self._registrar_hist()
        self._compor_fundo()
        self._construir_itens()
        self.editou.emit(None)
        return n

    def restaurar_estilo(self, reg) -> bool:
        """Descarta os ajustes da instância; volta a seguir o estilo nomeado."""
        from app.rendering.estilos import restaurar_do_estilo

        if not restaurar_do_estilo(self._layout, reg):
            return False
        self._apos_edicao(reg, None)
        self._registrar_hist()
        self._compor_fundo()
        self.editou.emit(reg)
        return True

    def restaurar_da_mestra(self, reg) -> None:
        """Limpa os overrides da região: ela volta a seguir a célula-mestre."""
        from app.rendering.grade import propagar_mestre

        reg.overrides.clear()
        propagar_mestre(self._pagina())
        self._registrar_hist()
        self._compor_fundo()
        self._construir_itens()
        self.editou.emit(reg)

    # --- ações do painel de camadas -------------------------------------------

    def set_visivel(self, reg, visivel: bool) -> None:
        reg.visivel = visivel
        self._registrar_hist()
        self._compor_fundo()
        for it in self._itens:
            if it.regiao is reg:
                it.setVisible(visivel)
        self.editou.emit(reg)

    def set_travado(self, reg, travado: bool) -> None:
        reg.travado = travado
        self._registrar_hist()
        for it in self._itens:
            if it.regiao is reg:
                it.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, not travado)
        self.editou.emit(reg)

    def mover_regiao(self, reg, delta: int) -> None:
        """Reordena a região no slot (z-order na composição)."""
        for slot in self._pagina().slots:
            if reg in slot.regioes:
                i = slot.regioes.index(reg)
                j = i + delta
                if 0 <= j < len(slot.regioes):
                    slot.regioes[i], slot.regioes[j] = slot.regioes[j], slot.regioes[i]
                    self._registrar_hist()
                    self._compor_fundo()
                    self.editou.emit(reg)
                return

    def resolver_selecao(self, ponto):
        """RG-55 (passo 9): a região CONCRETA no topo do z naquele ponto de
        cena. ``self._scene.items(ponto)`` já vem em ordem de empilhamento
        (topo → base); a 1ª RegiaoItem visível é a que o clique atinge.
        Cópia de grade resolve para a PRÓPRIA cópia (cada RegiaoItem embrulha
        a sua região) — nunca "some na mestra". None se não há região ali."""
        for it in self._scene.items(ponto):
            if isinstance(it, RegiaoItem) and it.isVisible():
                return it.regiao
        return None

    def selecionada(self):
        """A região que o PAINEL mostra.

        RG-15: o 1º clique numa célula acende o TRIO inteiro (para mover a
        célula). RG-55 (passo 11, decisão travada): o painel NUNCA fica
        órfão — mostra a região efetivamente CLICADA (a primária), esteja o
        trio selecionado ou não. Uma região só (clique já colapsado, ou
        região solta) devolve ela mesma, como sempre."""
        itens = [it for it in self._scene.selectedItems()
                 if isinstance(it, RegiaoItem)]
        if len(itens) == 1:
            return itens[0].regiao
        if not itens:
            self._primaria = None
            return None
        # multi-seleção (o trio do grupo): mostra a primária SE ela está no
        # conjunto selecionado; senão neutro (rubber-band de regiões avulsas).
        # Comparação por IDENTIDADE (I1) — Regiao é dataclass mutável.
        if self._primaria is not None and any(
                it.regiao is self._primaria for it in itens):
            return self._primaria
        return None

    def nomes_dos_itens(self) -> list[str]:
        """RG-25: os nomes dos produtos compostos agora (p/ a dica da IA)."""
        from app.rendering.compositor import DadosProduto
        d = self._dados
        if isinstance(d, dict):
            return [v.nome for v in d.values()
                    if isinstance(v, DadosProduto) and v.nome]
        if isinstance(d, (list, tuple)):
            return [v.nome for v in d if isinstance(v, DadosProduto) and v.nome]
        return [d.nome] if isinstance(d, DadosProduto) and d.nome else []

    def tamanho_efetivo_pt(self, reg) -> float | None:
        """RG-18: o tamanho que o desenho REALMENTE usa (o ajuste só-reduz) —
        None quando não se aplica (imagem/selo/preço, que tem fitting próprio)."""
        from app.rendering.model import TipoRegiao as TR
        if self._layout is None or reg.tipo not in (
                TR.NOME, TR.UNIDADE, TR.TEXTO_LEGAL):
            return None
        d = self._dados
        if isinstance(d, dict):          # Mesa: dados por slot
            slot = self._slot_de(reg)
            d = d.get(slot.id) if slot is not None else None
        from app.rendering.compositor import (
            DadosProduto, nome_com_unidade, texto_composto_legal,
        )
        if not isinstance(d, DadosProduto):
            d = DadosProduto("")
        if reg.tipo == TR.NOME:
            texto = nome_com_unidade(d.nome, d.unidade, False)
        elif reg.tipo == TR.UNIDADE:
            texto = d.unidade or ""
        else:
            texto = texto_composto_legal(reg, d)   # RG-57: pelo papel
        if not texto:
            return None
        from app.core.paths import SystemRoot
        from app.rendering.text_fit import ajustar_texto
        dpi = self._layout.dpi
        aj = ajustar_texto(texto, SystemRoot().fontes / reg.fonte,
                           mm_para_px(reg.rect.larg_mm, dpi),
                           mm_para_px(reg.rect.alt_mm, dpi),
                           reg.tamanho_max_pt, dpi, reg.tamanho_min_pt)
        return aj.tamanho_pt

    def _contexto_regiao(self, reg) -> dict:
        """RG-55 (instrumentação): o estado que o log precisa provar sobre
        uma região — mestra/cópia, rotação, z na lista do slot."""
        slot = self._slot_de(reg)
        regs = slot.regioes if slot is not None else []
        return {
            "uid": reg.uid,
            "tipo": reg.tipo.value,
            "mestre": bool(slot is not None and slot.mestre),
            "copia": bool(slot is not None and (slot.ref_grupo is not None
                                                or reg.ref_mestre is not None
                                                or reg.de_mestre)),
            "rotacao": reg.rotacao_graus,
            # z por IDENTIDADE (I1), não por valor
            "z": next((i for i, r in enumerate(regs) if r is reg), -1),
        }

    def conteudo_da_regiao(self, reg) -> str:
        """R-026 (raio-x com valores): o CONTEÚDO atual que a região desenha —
        nome sanitizado, preço formatado, unidade, foto/selo — para o painel
        conferir sem caçar no desenho. '' quando não se aplica."""
        from app.rendering.model import TipoRegiao as TR
        d = self._dados
        if isinstance(d, dict):
            slot = self._slot_de(reg)
            d = d.get(slot.id) if slot is not None else None
        from app.rendering.compositor import (
            DadosProduto, _reais_centavos, nome_com_unidade,
            texto_composto_legal,
        )
        from app.rendering.model import PapelPreco
        if not isinstance(d, DadosProduto):
            d = DadosProduto("")
        if reg.tipo == TR.NOME:
            return nome_com_unidade(d.nome, d.unidade, False) or "(sem nome)"
        if reg.tipo == TR.PRECO:
            valor = (d.preco_de if reg.papel_preco == PapelPreco.DE
                     else d.preco_por)
            if valor is None:
                return "(sem preço)"
            reais, centavos = _reais_centavos(valor)
            moeda = "R$ " if reg.mostrar_moeda else ""
            return f"{moeda}{reais},{centavos}"
        if reg.tipo == TR.UNIDADE:
            return d.unidade or "(sem unidade)"
        if reg.tipo == TR.TEXTO_LEGAL:
            return texto_composto_legal(reg, d).strip() or "(sem texto)"
        if reg.tipo == TR.IMAGEM:
            cam = d.imagem_path
            return (cam.rsplit("/", 1)[-1].rsplit("\\", 1)[-1]
                    if cam else "(sem foto)")
        if reg.tipo == TR.SELO:
            return "selos automáticos/manuais"
        return ""

    def _emitir_selecao(self) -> None:
        sel = self.selecionada()
        from app.qt.design import diag_selecao
        if diag_selecao.ligado():
            n = len([it for it in self._scene.selectedItems()
                     if isinstance(it, RegiaoItem)])
            diag_selecao.anotar(
                "selecao_emitida", n_selecionados=n,
                uid=(sel.uid if sel is not None else None),
                # painel órfão = há item(ns) selecionado(s) mas selecionada()
                # devolve None (o sintoma exato do RG-55: painel "Nada
                # selecionado" com região destacada na lista de camadas)
                painel_orfao=bool(n >= 1 and sel is None))
        self.selecao_mudou.emit(sel)

    def _slot_para_novas_regioes(self):
        """C1 (ORDEM_F5_6 §6): a região nova respeita o CONTEXTO.

        Com seleção → o slot da seleção (na mestra replica; numa cópia é adição
        própria). Sem seleção → um slot AVULSO da página (``livre_<uuid8>``,
        sem âncora) — nunca cair no mestre da grade por acidente.
        """
        sel = self.selecionada()
        if sel is not None:
            slot = self._slot_de(sel)
            if slot is not None:
                return slot
        import uuid
        from app.rendering.model import Slot
        pagina = self._pagina()
        livre = next((s for s in pagina.slots
                      if s.id.startswith("livre_") and not s.mestre
                      and s.ref_grupo is None), None)
        if livre is None:
            livre = Slot(f"livre_{uuid.uuid4().hex[:8]}")
            pagina.slots.append(livre)
        return livre

    def adicionar_regiao(self, tipo, *, papel_texto=None, texto_fixo=None):
        """Cria uma região nova (padrão no centro) e a seleciona (ferramenta F5.3).

        Destino pela regra C1: slot da seleção, ou slot livre. Na mestra a
        região nasce replicável e **propaga**; num slot livre nasce livre.

        RG-57: um TEXTO_LEGAL pode nascer já com o PAPEL escolhido e o texto
        inicial (o diálogo nomeado passa esses valores). Sem modal aqui — os
        testes chamam direto e a UI resolve o papel antes de chamar.
        """
        from app.rendering.model import Regiao, Retangulo

        lw, lh = self._layout.largura_mm, self._layout.altura_mm
        slot = self._slot_para_novas_regioes()
        reg = Regiao(tipo, Retangulo(lw * 0.4, lh * 0.4, lw * 0.2, lh * 0.08),
                     nome=tipo.value.title())
        if papel_texto is not None:
            reg.papel_texto = papel_texto
        if texto_fixo is not None:
            reg.texto_fixo = texto_fixo
        if slot.mestre:
            reg.de_mestre = True     # nasce replicável
        slot.regioes.append(reg)
        self._apos_edicao(reg, None)
        self._registrar_hist()
        self._compor_fundo()
        self._construir_itens()
        for it in self._itens:
            it.setSelected(it.regiao is reg)
        self.editou.emit(reg)
        return reg

    def centralizar_na_arte(self, reg) -> None:
        """R-032: centraliza a região na caixa da arte (a página inteira, no
        cartaz). Só move o rect — conteúdo e vínculo intactos (I1)."""
        if self._layout is None:
            return
        lw, lh = self._layout.largura_mm, self._layout.altura_mm
        reg.rect.x_mm = max(0.0, (lw - reg.rect.larg_mm) / 2)
        reg.rect.y_mm = max(0.0, (lh - reg.rect.alt_mm) / 2)
        self.notificar_edicao(reg, "rect")
        self._construir_itens()       # a alça reposiciona no novo rect

    # --- R-038: arrastar um arquivo de imagem sobre a célula -----------------

    _EXT_IMAGEM = (".png", ".jpg", ".jpeg", ".webp", ".bmp")

    def _caminho_imagem_do_evento(self, ev) -> str | None:
        md = ev.mimeData()
        if not md.hasUrls():
            return None
        for url in md.urls():
            cam = url.toLocalFile()
            if cam and cam.lower().endswith(self._EXT_IMAGEM):
                return cam
        return None

    def dragEnterEvent(self, ev) -> None:  # noqa: N802 (Qt)
        if (ev.mimeData().hasFormat(self._MIME_TROCA)
                or self._caminho_imagem_do_evento(ev) is not None):
            ev.acceptProposedAction()
        else:
            super().dragEnterEvent(ev)

    def dragMoveEvent(self, ev) -> None:  # noqa: N802 (Qt)
        if (ev.mimeData().hasFormat(self._MIME_TROCA)
                or self._caminho_imagem_do_evento(ev) is not None):
            ev.acceptProposedAction()
        else:
            super().dragMoveEvent(ev)

    _MIME_TROCA = "application/x-autotabloide-trocar-slot"

    def dropEvent(self, ev) -> None:  # noqa: N802 (Qt)
        # OS F11.5 #36 (R-057): o drop do gesto Alt+arrastar → TROCA as células
        if ev.mimeData().hasFormat(self._MIME_TROCA):
            origem = bytes(ev.mimeData().data(self._MIME_TROCA)).decode()
            self.soltar_troca(self.mapToScene(ev.position().toPoint()), origem)
            ev.acceptProposedAction()
            return
        cam = self._caminho_imagem_do_evento(ev)
        if cam is None:
            super().dropEvent(ev)
            return
        ponto = self.mapToScene(ev.position().toPoint())
        self.soltar_imagem(ponto, cam)
        ev.acceptProposedAction()

    def soltar_troca(self, ponto_cena, sid_origem: str) -> bool:
        """OS F11.5 #36 (R-057): o fim do gesto "arrastar um item SOBRE o
        outro" — resolve o slot alvo pelo ponto e TROCA os dois pelo mapa de
        uid (I1; o undo unificado já vive em trocar_conteudo_slots)."""
        alvo = self._slot_no_ponto(ponto_cena)
        if alvo is None or alvo.id == sid_origem:
            return False
        if not self.mapa.get(alvo.id) or not self.mapa.get(sid_origem):
            return False                        # troca é entre células OCUPADAS
        if self.trocar_conteudo_slots(sid_origem, alvo.id):
            self._avisar_info("Itens trocados de célula (Ctrl+Z desfaz).")
            return True
        return False

    def iniciar_troca_por_arrasto(self, ponto_cena) -> bool:
        """OS F11.5 #36: Alt+arrastar numa célula OCUPADA inicia o gesto de
        troca (QDrag com o id do slot; o drop em outra célula ocupada troca)."""
        from PySide6.QtCore import QMimeData
        from PySide6.QtGui import QDrag
        slot = self._slot_no_ponto(ponto_cena)
        if slot is None or not self.mapa.get(slot.id):
            return False
        mime = QMimeData()
        mime.setData(self._MIME_TROCA, slot.id.encode())
        drag = QDrag(self)
        drag.setMimeData(mime)
        drag.exec(Qt.DropAction.MoveAction)
        return True

    def mousePressEvent(self, ev) -> None:  # noqa: N802 (Qt)
        # OS F11.5 #36: Alt+arrastar numa célula OCUPADA inicia a TROCA
        # (Alt não conflita: seleção/movimento seguem sem modificador)
        if (ev.button() == Qt.MouseButton.LeftButton
                and ev.modifiers() & Qt.KeyboardModifier.AltModifier
                and self.iniciar_troca_por_arrasto(
                    self.mapToScene(ev.position().toPoint()))):
            return
        super().mousePressEvent(ev)

    def _slot_no_ponto(self, ponto_cena):
        """O slot cuja região está no topo do z sob o ponto (mesmo picking da
        seleção, Fase 4). None se não há região ali."""
        reg = self.resolver_selecao(ponto_cena)
        return self._slot_de(reg) if reg is not None else None

    def soltar_imagem(self, ponto_cena, caminho) -> str | None:
        """R-038: solta uma foto sobre a célula → troca a imagem do ITEM
        daquele slot, POR uid (I1: resolvido pela ligação slot→uid, não pela
        posição). A Mesa (``ao_soltar_imagem``) confirma a substituição e
        aplica o override. Devolve o uid alvo (None se não há imagem ali)."""
        from app.rendering.model import TipoRegiao as _TR
        slot = self._slot_no_ponto(ponto_cena)
        if slot is None or not any(r.tipo == _TR.IMAGEM for r in slot.regioes):
            return None
        uid = self.mapa.get(slot.id)     # I1: o item vinculado ao slot, por uid
        if callable(self.ao_soltar_imagem):
            self.ao_soltar_imagem(slot.id, str(caminho))
        return uid

    # --- R-031: conta-gotas de estilo ---------------------------------------

    def copiar_estilo(self, reg) -> None:
        """Guarda um retrato do estilo visual da região (imune a edições
        posteriores dela)."""
        from app.rendering.model import Regiao
        self._estilo_copiado = Regiao.from_dict(reg.to_dict())

    def tem_estilo_copiado(self) -> bool:
        return self._estilo_copiado is not None

    def colar_estilo(self, regioes) -> int:
        """R-031: aplica o estilo copiado a todas as regiões dadas — só estilo,
        nunca geometria/conteúdo (respeita os estilos nomeados F5.7). Devolve
        quantas regiões mudaram."""
        if self._estilo_copiado is None or not regioes:
            return 0
        from app.rendering.estilos import copiar_estilo_visual
        mudou = 0
        for destino in regioes:
            if copiar_estilo_visual(self._estilo_copiado, destino):
                mudou += 1
                self._apos_edicao(destino, "estilo_colado")
        if mudou:
            self._registrar_hist()
            self._compor_fundo()
            self.editou.emit(regioes[0])
        return mudou

    # --- R-048/R-044: modelos de célula -------------------------------------

    def carimbar_modelo(self, modelo, x_mm=None, y_mm=None,
                        larg_mm=None, alt_mm=None):
        """R-048: carimba um modelo de célula na caixa-alvo (padrão: a página
        inteira). Os campos entram com o estilo salvo; o CONTEÚDO vem do item
        do slot. As regiões nascem com uid fresco (I1)."""
        if self._layout is None:
            return []
        from app.rendering.modelos import carimbar_modelo as _carimbar
        x_mm = 0.0 if x_mm is None else x_mm
        y_mm = 0.0 if y_mm is None else y_mm
        larg_mm = larg_mm if larg_mm is not None else self._layout.largura_mm
        alt_mm = alt_mm if alt_mm is not None else self._layout.altura_mm
        novas = _carimbar(modelo, x_mm, y_mm, larg_mm, alt_mm)
        if not novas:
            return []
        slot = self._slot_para_novas_regioes()
        slot.regioes.extend(novas)
        self._apos_edicao(novas[0], None)
        self._registrar_hist()
        self._compor_fundo()
        self._construir_itens()
        self.editou.emit(novas[0])
        return novas

    def salvar_selecao_como_modelo(self, nome: str) -> bool:
        """R-048: salva as regiões SELECIONADAS (ou todas do slot ativo) como
        um modelo de célula reutilizável."""
        from app.rendering.modelos import capturar_modelo, salvar_modelo
        regs = [it.regiao for it in self.selecionados()]
        if not regs:
            slot = self._slot_para_novas_regioes()
            regs = list(slot.regioes)
        if not regs or not nome.strip():
            return False
        salvar_modelo(capturar_modelo(nome.strip(), regs))
        return True

    def definir_papel_texto(self, reg, papel) -> None:
        """RG-57 (passo 11): recategoriza um TEXTO_LEGAL para outro papel SEM
        apagar/recriar — o texto_fixo é preservado; o compositor reinterpreta
        pelo novo papel. Recompõe (prévia ao vivo) e repinta o badge."""
        reg.papel_texto = papel
        self.notificar_edicao(reg, "papel_texto")
        for it in self._itens:               # o badge do item reflete na hora
            it.update()

    def notificar_edicao(self, reg, attr: str | None = None) -> None:
        """Recompõe após uma edição de propriedade (chamado pelo painel).

        ``attr`` identifica o que mudou: na mestra dispara a propagação; numa
        célula da grade vira override (precedência local).
        """
        self._apos_edicao(reg, attr)
        if attr == "rotacao_graus":      # RG-12: contornos giram na hora
            for it in self._itens:       # (todos: a propagação da mestra
                it.aplicar_rotacao()     # muda as derivadas também)
        self._registrar_hist()
        self._compor_fundo()
        self.editou.emit(reg)

    def contextMenuEvent(self, event) -> None:
        """Área vazia: menu de carimbo (F5.6). Sobre uma região, o item cuida."""
        if self.itemAt(event.pos()) is not None or self._layout is None:
            super().contextMenuEvent(event)
            return
        from PySide6.QtWidgets import QMenu

        from app.qt.design.icones import icone
        from app.rendering.grade import mestres

        ms = [m for m in mestres(self._pagina()) if m.regioes]
        if not ms:
            return
        cena = self.mapToScene(event.pos())
        ancora = self.cena_para_mm(cena.x(), cena.y())
        menu = QMenu(self)
        acoes = {}
        for m in ms:
            rotulo = m.id.replace("celula_", "célula ").replace("grupo_", "grupo ")
            acoes[menu.addAction(icone("duplicar", tamanho=16),
                                 f"Carimbar cópia de “{rotulo}” aqui")] = m.id
        escolha = menu.exec(event.globalPos())
        if escolha in acoes:
            self.carimbar_grupo(acoes[escolha], ancora)

    # --- pan com espaço + zoom -------------------------------------------------

    def keyPressEvent(self, event) -> None:
        if event.key() == Qt.Key.Key_Space:
            self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        if (event.key() == Qt.Key.Key_0
                and event.modifiers() & Qt.KeyboardModifier.ControlModifier):
            self.ajustar()               # RG-05: Ctrl+0 = saída do zoom perdido
            return
        # RG-06: o menu de contexto sempre PROMETEU "Excluir · Del" — agora a
        # tecla cumpre (e Backspace idem), onde quer que o canvas viva
        if event.key() in (Qt.Key.Key_Delete, Qt.Key.Key_Backspace):
            selecao = [it.regiao for it in self._itens if it.isSelected()]
            if selecao:
                self.excluir_regioes(selecao)
                return
        # R-041 (passo 76): setas empurram 1 mm; Shift+seta, 0,1 mm
        setas = {Qt.Key.Key_Left: (-1, 0), Qt.Key.Key_Right: (1, 0),
                 Qt.Key.Key_Up: (0, -1), Qt.Key.Key_Down: (0, 1)}
        if event.key() in setas:
            passo = (0.1 if event.modifiers() & Qt.KeyboardModifier.ShiftModifier
                     else 1.0)
            dx, dy = setas[event.key()]
            if self.nudge_selecao(dx * passo, dy * passo):
                return
        super().keyPressEvent(event)

    def keyReleaseEvent(self, event) -> None:
        if event.key() == Qt.Key.Key_Space:
            self.setDragMode(QGraphicsView.DragMode.RubberBandDrag)
        super().keyReleaseEvent(event)

    def zoom(self, fator: float) -> None:
        """Multiplica a escala, sempre dentro de [ESCALA_MIN, ESCALA_MAX]."""
        alvo = max(ESCALA_MIN, min(ESCALA_MAX, self.escala_atual() * fator))
        fator_real = alvo / self.escala_atual()
        if abs(fator_real - 1.0) > 1e-9:
            self.scale(fator_real, fator_real)
        self.transformou.emit()

    def zoom_mais(self) -> None:
        self.zoom(1.2)

    def zoom_menos(self) -> None:
        self.zoom(1 / 1.2)

    def zoom_100(self) -> None:
        """R-029 (passo 69): zoom em 100% (1 px de cena = 1 px de tela),
        dentro do clamp são."""
        from PySide6.QtGui import QTransform
        s = max(ESCALA_MIN, min(ESCALA_MAX, 1.0))
        self.setTransform(QTransform().scale(s, s))
        self.transformou.emit()

    def zoom_para_selecao(self) -> bool:
        """R-029 (passo 68): enquadra a região selecionada preenchendo a
        tela (com uma folga). Sem seleção → False (nada a enquadrar)."""
        it = next((i for i in self._itens if i.isSelected()), None)
        if it is None:
            return False
        r = it.mapRectToScene(it.boundingRect())
        margem = max(r.width(), r.height()) * 0.15 + 4
        r.adjust(-margem, -margem, margem, margem)
        self.fitInView(r, Qt.AspectRatioMode.KeepAspectRatio)
        # respeita o clamp (não deixa a região minúscula estourar o MAX)
        if self.escala_atual() > ESCALA_MAX:
            from PySide6.QtGui import QTransform
            self.setTransform(QTransform().scale(ESCALA_MAX, ESCALA_MAX))
            self.centerOn(r.center())
        self.transformou.emit()
        return True

    def nivel_zoom_pct(self) -> int:
        """O zoom atual em %, com clamp são (herda a cura da Onda 2)."""
        return round(max(ESCALA_MIN, min(ESCALA_MAX, self.escala_atual())) * 100)

    # --- R-040: modo raio-x (só as regiões, sem a arte) -----------------------

    def set_raio_x(self, ligado: bool) -> None:
        """R-040 (passo 73): esconde a arte de fundo e mostra só os
        retângulos das regiões (pintados por papel) — enxergar a estrutura."""
        self._raio_x = bool(ligado)
        if self._bg is not None:
            self._bg.setVisible(not self._raio_x)
        for it in self._itens:
            it.update()
        self.viewport().update()

    def raio_x_ligado(self) -> bool:
        return bool(getattr(self, "_raio_x", False))

    # --- R-039: cadeado da arte de fundo --------------------------------------

    def set_arte_travada(self, travada: bool) -> None:
        """R-039/072: a arte de fundo é protegida (travada por padrão) — não
        se seleciona nem se move sem querer. Destravar é gesto CONSCIENTE, com
        aviso. Por decisão travada do projeto a arte é o fundo de página
        inteiro (o Illustrator faz só a arte), então ela nunca é um objeto
        móvel — o cadeado é a proteção/clareza dessa regra."""
        self._arte_travada = bool(travada)
        if self._bg is not None:          # consome o estado na hora (R-039)
            self._bg.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable,
                             not travada)
            if travada and self._bg.isSelected():
                self._bg.setSelected(False)
        if not travada:
            # OS F11.5 #72 (opção b): a decisão travada é arte = FUNDO de
            # página (nunca objeto móvel). O aviso agora diz o que o gesto
            # FAZ — liberar a seleção para conferir/medir — sem prometer
            # movimento que não existe.
            self._avisar_info(
                "Arte destravada: agora dá para SELECIONÁ-LA (conferir e "
                "medir). Ela continua fixa como fundo da página — "
                "reposicionar a arte é trabalho do Illustrator (decisão do "
                "projeto).")

    def arte_travada(self) -> bool:
        return bool(getattr(self, "_arte_travada", True))

    def _avisar_info(self, texto: str) -> None:
        try:
            from app.qt.design.toast import mostrar_toast
            mostrar_toast(self, texto)
        except Exception:
            pass

    # --- R-041: empurrar com as setas (1 mm / 0,1 mm) -------------------------

    def nudge_selecao(self, dx_mm: float, dy_mm: float) -> bool:
        """Passo 76: move a(s) região(ões) selecionada(s) por um delta EXATO
        em mm (seta = 1 mm; Shift+seta = 0,1 mm). Um estado de undo."""
        itens = [i for i in self._itens if i.isSelected()
                 and not i.regiao.travado]
        if not itens:
            return False
        dx_px, dy_px = self.mm_para_cena(dx_mm, dy_mm)
        for it in itens:
            it.setPos(it.x() + dx_px, it.y() + dy_px)
            self._commit_regiao_sem_hist(it)
        self._registrar_hist()
        self._compor_fundo()
        self.editou.emit(itens[0].regiao)
        return True

    def _commit_regiao_sem_hist(self, item) -> None:
        """Grava a geometria do item no modelo SEM registrar histórico (o
        nudge agrupa vários itens num só estado de undo)."""
        r = item.rect_cena()
        reg = item.regiao
        reg.rect.x_mm, reg.rect.y_mm = self.cena_para_mm(r.x(), r.y())
        reg.rect.larg_mm, reg.rect.alt_mm = self.cena_para_mm(r.width(), r.height())
        self._apos_edicao(reg, "rect")

    # --- snapping (guias magnéticas) ------------------------------------------

    def alvos_snap(self, item_movel) -> tuple[list, list]:
        """R-027/028 (passo 61): o serviço ÚNICO de snap — bordas/centro da
        página + bordas das outras regiões (alinhamento inteligente da Onda 3)
        + as GUIAS do usuário + a GRADE magnética (se ligada). Uma fonte só,
        sem duplicar a matemática."""
        w, h = self._scene.width(), self._scene.height()
        ax, ay = [0.0, w / 2, w], [0.0, h / 2, h]     # bordas/centro da página
        for it in self._itens:
            if it is item_movel or not it.isVisible():
                continue
            r = it.rect_cena()
            ax += [r.left(), r.center().x(), r.right()]
            ay += [r.top(), r.center().y(), r.bottom()]
        pag = self._pagina() if self._layout is not None else None
        if pag is not None:
            # guias do usuário (R-027) — coord em mm relativa → cena
            for orient, coord_mm in pag.guias:
                cx, cy = self.mm_para_cena(coord_mm, coord_mm)
                (ax if orient == "x" else ay).append(cx if orient == "x" else cy)
            # grade magnética (R-028): linhas a cada passo, se ligada
            if pag.grade_magnetica and pag.grade_passo_mm > 0:
                passo_px, _ = self.mm_para_cena(pag.grade_passo_mm, 0)
                if passo_px >= 1:
                    n_x = int(w / passo_px) + 1
                    n_y = int(h / passo_px) + 1
                    ax += [i * passo_px for i in range(n_x + 1)]
                    ay += [i * passo_px for i in range(n_y + 1)]
        return ax, ay

    def mostrar_guias(self, guias) -> None:
        for g in self._guias:
            self._scene.removeItem(g)
        self._guias = []
        caneta = QPen(QColor(t.GUIA_SNAP), 0, Qt.PenStyle.DashLine)
        w, h = self._scene.width(), self._scene.height()
        for tipo, coord in guias:
            linha = (self._scene.addLine(coord, 0, coord, h, caneta) if tipo == "x"
                     else self._scene.addLine(0, coord, w, coord, caneta))
            linha.setZValue(20)
            self._guias.append(linha)

    # --- R-027/028 (Fase 4): guias do usuário + grade magnética ----------------

    def adicionar_guia(self, orient: str, coord_mm: float) -> None:
        """R-027: cria uma guia persistente (mm relativa — I3), redesenha e
        registra no histórico (some/volta com desfazer)."""
        pag = self._pagina()
        pag.guias.append((orient, round(float(coord_mm), 2)))
        self._registrar_hist()
        self._redesenhar_guias_usuario()
        self.editou.emit(None)

    def remover_guia(self, orient: str, coord_mm: float, tol: float = 0.5) -> None:
        pag = self._pagina()
        pag.guias[:] = [g for g in pag.guias
                        if not (g[0] == orient and abs(g[1] - coord_mm) <= tol)]
        self._registrar_hist()
        self._redesenhar_guias_usuario()
        self.editou.emit(None)

    def limpar_guias(self) -> None:
        pag = self._pagina()
        if not pag.guias:
            return
        pag.guias.clear()
        self._registrar_hist()
        self._redesenhar_guias_usuario()
        self.editou.emit(None)

    def set_grade_magnetica(self, ligada: bool) -> None:
        """R-028: liga/desliga o snap à grade (persiste por layout)."""
        self._pagina().grade_magnetica = bool(ligada)
        self._registrar_hist()
        self.viewport().update()
        self.editou.emit(None)

    def set_grade_passo(self, passo_mm: float) -> None:
        self._pagina().grade_passo_mm = max(0.5, float(passo_mm))
        self._registrar_hist()
        self.viewport().update()
        self.editou.emit(None)

    def _redesenhar_guias_usuario(self) -> None:
        """Desenha as guias persistentes como linhas MOVÍVEIS (GuiaItem)."""
        for g in getattr(self, "_guias_usuario", []):
            if g.scene() is self._scene:
                self._scene.removeItem(g)
        self._guias_usuario = []
        if self._layout is None:
            return
        w, h = self._scene.width(), self._scene.height()
        for orient, coord_mm in list(self._pagina().guias):
            coord_px, _ = self.mm_para_cena(coord_mm, 0)
            gi = GuiaItem(self, orient, coord_mm, coord_px, w, h)
            self._scene.addItem(gi)
            self._guias_usuario.append(gi)

    # --- duplicar / excluir região --------------------------------------------

    def _slot_de(self, reg):
        for slot in self._pagina().slots:
            if reg in slot.regioes:
                return slot
        return None

    def duplicar_regiao(self, reg) -> None:
        from app.rendering.model import Regiao

        slot = self._slot_de(reg)
        if slot is None:
            return
        copia = Regiao.from_dict(reg.to_dict())
        import uuid
        copia.uid = uuid.uuid4().hex     # identidade própria (I1)
        copia.ref_mestre = None
        copia.rect.x_mm += 4
        copia.rect.y_mm += 4
        copia.nome = (reg.nome or reg.tipo.value.title()) + " cópia"
        copia.overrides = set()
        copia.de_mestre = slot.mestre    # duplicada na mestra também propaga
        slot.regioes.append(copia)
        self._apos_edicao(copia, None)
        self._registrar_hist()
        self._compor_fundo()
        self._construir_itens()
        for it in self._itens:
            it.setSelected(it.regiao is copia)
        self.editou.emit(copia)

    def excluir_regiao(self, reg) -> None:
        self.excluir_regioes([reg])

    def excluir_regioes(self, regs) -> None:
        """RG-06: exclui a seleção INTEIRA como UM gesto (1 estado de undo) —
        é o que Delete/Backspace chamam; o menu de contexto usa o singular."""
        mudou = False
        propaga = False
        for reg in list(regs):
            slot = self._slot_de(reg)
            if slot and reg in slot.regioes:
                slot.regioes.remove(reg)
                mudou = True
                propaga = propaga or slot.mestre
        if not mudou:
            return
        if propaga:                      # some da mestra → some das células
            from app.rendering.grade import propagar_mestre
            propagar_mestre(self._pagina())
        self._registrar_hist()
        self._compor_fundo()
        self._construir_itens()
        self.editou.emit(None)

    # --- alinhar / distribuir (na seleção) ------------------------------------

    def selecionados(self) -> list:
        return [it for it in self._itens if it.isSelected()]

    def _aplicar_posicoes(self, itens, posicoes) -> None:
        for it, (nx, ny) in zip(itens, posicoes):
            it.regiao.rect.x_mm, it.regiao.rect.y_mm = self.cena_para_mm(nx, ny)
        self._registrar_hist()
        self._compor_fundo()
        self._construir_itens()   # reposiciona a partir do modelo (sem brigar com snap)
        self.editou.emit(None)

    def alinhar_selecionadas(self, modo: str) -> None:
        from app.qt.alinhamento import alinhar

        itens = self.selecionados()
        if len(itens) < 2:
            return
        rects = [(it.x(), it.y(), it._w, it._h) for it in itens]
        self._aplicar_posicoes(itens, alinhar(rects, modo))

    def distribuir_selecionadas(self, eixo: str) -> None:
        from app.qt.alinhamento import distribuir

        itens = self.selecionados()
        if len(itens) < 3:
            return
        rects = [(it.x(), it.y(), it._w, it._h) for it in itens]
        self._aplicar_posicoes(itens, distribuir(rects, eixo))

    def distribuir_espacado(self, eixo: str, espaco_mm: float) -> None:
        """R-033: distribui a seleção com espaçamento FIXO em mm (borda a
        borda), no MESMO serviço da distribuição/alinhamento (sem duplicar)."""
        from app.qt.alinhamento import distribuir_espacamento

        itens = self.selecionados()
        if len(itens) < 2:
            return
        ex, ey = self.mm_para_cena(espaco_mm, espaco_mm)
        espaco = ex if eixo == "h" else ey
        rects = [(it.x(), it.y(), it._w, it._h) for it in itens]
        # OS F11.5 #60: a distribuição respeita as GUIAS e a GRADE magnética
        # da página (em coords de cena), como o arrasto já respeita
        pagina = self._pagina() if self._layout is not None else None
        guias_cena: list[tuple] = []
        grade_cena = None
        if pagina is not None:
            for orient, mm in (pagina.guias or []):
                cx, cy = self.mm_para_cena(mm, mm)
                guias_cena.append((orient, cx if orient == "x" else cy))
            if pagina.grade_magnetica and pagina.grade_passo_mm:
                gx, _gy = self.mm_para_cena(pagina.grade_passo_mm,
                                            pagina.grade_passo_mm)
                grade_cena = gx
        lim, _ = self.mm_para_cena(2.0, 2.0)
        self._aplicar_posicoes(itens, distribuir_espacamento(
            rects, eixo, espaco, grade_passo=grade_cena,
            guias=tuple(guias_cena), limiar=lim))

    # --- conversões cena<->mm --------------------------------------------------

    def cena_para_mm(self, x_px: float, y_px: float) -> tuple[float, float]:
        dpi = self._layout.dpi
        return px_para_mm(x_px, dpi), px_para_mm(y_px, dpi)

    def mm_para_cena(self, x_mm: float, y_mm: float) -> tuple[float, float]:
        dpi = self._layout.dpi
        return mm_para_px(x_mm, dpi), mm_para_px(y_mm, dpi)

    # --- interação -------------------------------------------------------------

    def wheelEvent(self, event) -> None:
        """RG-11 (paridade Illustrator, confirmado pelo dono): roda = rolagem
        vertical · Ctrl+roda = horizontal · Alt+roda = zoom (com o limite do
        RG-05). Era roda=zoom — o gesto de rolar despencava a escala."""
        mods = event.modifiers()
        if mods & Qt.KeyboardModifier.AltModifier:
            # com Alt o Qt entrega o delta no eixo X
            delta = event.angleDelta().x() or event.angleDelta().y()
            self.zoom(1.15 if delta > 0 else 1 / 1.15)
            return
        if mods & Qt.KeyboardModifier.ControlModifier:
            barra = self.horizontalScrollBar()
            barra.setValue(barra.value() - event.angleDelta().y())
            return
        super().wheelEvent(event)        # rolagem vertical de sempre

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        if (self._ajuste_pendente
                and self.viewport().width() >= 80
                and self.viewport().height() >= 80):
            self.ajustar()               # RG-05: o fit adiado do boot acontece aqui
        self.transformou.emit()

    def scrollContentsBy(self, dx: int, dy: int) -> None:
        super().scrollContentsBy(dx, dy)
        self.transformou.emit()


class Regua(QWidget):
    """Régua em mm (topo ou lateral), sincronizada com o zoom/pan do canvas."""

    ESPESSURA = 22

    def __init__(self, view: CanvasView, horizontal: bool, parent=None):
        super().__init__(parent)
        self.view = view
        self.horizontal = horizontal
        if horizontal:
            self.setFixedHeight(self.ESPESSURA)
        else:
            self.setFixedWidth(self.ESPESSURA)
        view.transformou.connect(self.update)

    def mousePressEvent(self, event) -> None:
        # R-027: arrastar A PARTIR da régua cria uma guia (some no release)
        if self.view._layout is not None:
            self._arrastando = True
            self.grabMouse()

    def mouseReleaseEvent(self, event) -> None:
        if not getattr(self, "_arrastando", False):
            return
        self._arrastando = False
        self.releaseMouse()
        if self.view._layout is None:
            return
        gp = event.globalPosition().toPoint()
        vp = self.view.viewport()
        cena = self.view.mapToScene(vp.mapFromGlobal(gp))
        dpi = self.view._layout.dpi
        if self.horizontal:              # régua do topo → guia horizontal ('y')
            coord_mm = px_para_mm(cena.y(), dpi)
            orient, limite = "y", self.view._layout.altura_mm
        else:                            # régua da esquerda → guia vertical ('x')
            coord_mm = px_para_mm(cena.x(), dpi)
            orient, limite = "x", self.view._layout.largura_mm
        if 0 <= coord_mm <= limite:      # soltou DENTRO da página → cria
            self.view.adicionar_guia(orient, coord_mm)

    def paintEvent(self, _event) -> None:
        p = QPainter(self)
        p.fillRect(self.rect(), QColor(t.SUPERFICIE))
        # borda que separa a régua da mesa
        p.setPen(QColor(t.BORDA))
        if self.horizontal:
            p.drawLine(0, self.height() - 1, self.width(), self.height() - 1)
        else:
            p.drawLine(self.width() - 1, 0, self.width() - 1, self.height())
        if self.view._layout is None:
            p.end()
            return
        fonte = p.font()
        fonte.setPointSizeF(7)
        p.setFont(fonte)
        dpi = self.view._layout.dpi
        vp = self.view.viewport()
        ini = self.view.mapToScene(0, 0)
        fim = self.view.mapToScene(vp.width(), vp.height())

        if self.horizontal:
            mm0, mm1 = px_para_mm(ini.x(), dpi), px_para_mm(fim.x(), dpi)
        else:
            mm0, mm1 = px_para_mm(ini.y(), dpi), px_para_mm(fim.y(), dpi)

        # RG-05: passo adaptativo ao zoom (e teto duro) — a régua nunca mais
        # desenha milhares de marcas num paint quando a escala despenca
        px_por_mm = mm_para_px(1, dpi) * max(self.view.transform().m11(), 1e-9)
        passo = passo_da_regua(px_por_mm)
        m = int(mm0 // passo * passo)
        marcas = 0
        while m <= mm1 and marcas < 600:
            marcas += 1
            cena = mm_para_px(m, dpi)
            if self.horizontal:
                x = self.view.mapFromScene(cena, 0).x()
                p.setPen(QColor(t.BORDA_FORTE))
                p.drawLine(x, self.height() - 6, x, self.height() - 1)
                p.setPen(QColor(t.TEXTO_3))
                p.drawText(x + 3, self.height() - 8, str(m))
            else:
                y = self.view.mapFromScene(0, cena).y()
                p.setPen(QColor(t.BORDA_FORTE))
                p.drawLine(self.width() - 6, y, self.width() - 1, y)
                p.setPen(QColor(t.TEXTO_3))
                p.drawText(2, y - 3, str(m))
            m += passo
        p.end()


class GuiaItem(QGraphicsLineItem):
    """R-027: uma guia do usuário — linha movível ao longo do seu eixo.
    Arrastar de volta para FORA da página remove a guia (persiste no modelo)."""

    def __init__(self, canvas, orient: str, coord_mm: float, coord_px: float,
                 w: float, h: float):
        if orient == "x":
            super().__init__(0, 0, 0, h)      # linha vertical
            self.setPos(coord_px, 0)
        else:
            super().__init__(0, 0, w, 0)      # linha horizontal
            self.setPos(0, coord_px)
        self.canvas = canvas
        self.orient = orient
        self.coord_mm = coord_mm
        self._w, self._h = w, h
        caneta = QPen(QColor(t.GUIA_SNAP), 0)
        caneta.setCosmetic(True)
        self.setPen(caneta)
        self.setZValue(19)                    # abaixo do feedback de snap (20)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges, True)
        self.setCursor(Qt.CursorShape.SizeHorCursor if orient == "x"
                       else Qt.CursorShape.SizeVerCursor)

    def itemChange(self, change, value):
        # trava o movimento no eixo perpendicular (guia só desliza num sentido)
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionChange:
            if self.orient == "x":
                return QPointF(value.x(), 0)
            return QPointF(0, value.y())
        return super().itemChange(change, value)

    def mouseReleaseEvent(self, event) -> None:
        super().mouseReleaseEvent(event)
        from app.rendering.units import px_para_mm
        dpi = self.canvas._layout.dpi
        antigo = self.coord_mm
        if self.orient == "x":
            novo_mm = px_para_mm(self.pos().x(), dpi)
            limite = self.canvas._layout.largura_mm
        else:
            novo_mm = px_para_mm(self.pos().y(), dpi)
            limite = self.canvas._layout.altura_mm
        self.canvas.remover_guia(self.orient, antigo)
        if 0 <= novo_mm <= limite:            # dentro da página: reposiciona
            self.canvas.adicionar_guia(self.orient, novo_mm)
        # fora da página: só removeu (arrastou de volta para a régua)


class EditorCanvas(QWidget):
    """Canvas + réguas (topo e esquerda). É a fundação do editor (F5.1)."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.canvas = CanvasView(self)
        self.regua_topo = Regua(self.canvas, horizontal=True, parent=self)
        self.regua_esq = Regua(self.canvas, horizontal=False, parent=self)

        grade = QGridLayout(self)
        grade.setContentsMargins(0, 0, 0, 0)
        grade.setSpacing(0)
        canto = QWidget()
        canto.setFixedSize(Regua.ESPESSURA, Regua.ESPESSURA)
        canto.setProperty("papel", "reguaCanto")
        canto.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        grade.addWidget(canto, 0, 0)
        grade.addWidget(self.regua_topo, 0, 1)
        grade.addWidget(self.regua_esq, 1, 0)
        grade.addWidget(self.canvas, 1, 1)

    def carregar(self, layout: LayoutDef, dados: DadosProduto, fundo_path=None) -> None:
        self.canvas.carregar(layout, dados, fundo_path)

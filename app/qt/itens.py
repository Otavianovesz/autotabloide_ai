"""
Item interativo de região (F5.2/F5.4 + sistema de design)
=========================================================
Alça leve do Qt sobre o preview: mover (com **snapping** a guias), redimensionar
(cantos), e **menu de botão direito** (duplicar/excluir/travar). Ao soltar, o
canvas muta o modelo e recompõe pelo Pillow (WYSIWYG).

Craft da seleção (tokens do design):
- repouso: contorno tracejado discreto (região descobrível, sem gritar);
- hover: contorno sólido no azul-claro ANTES do clique;
- selecionado: contorno sólido primário + alças estilo Figma (miolo branco,
  borda primária) que crescem levemente sob o mouse;
- cursores certos: seta diagonal em cada canto, mover no corpo.
"""

from __future__ import annotations

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QBrush, QColor, QPen
from PySide6.QtWidgets import QGraphicsItem, QMenu

from app.qt.alinhamento import snap
from app.qt.design import tokens as t
from app.qt.design.icones import icone


def cota_entre_rects(rect: tuple, outros: list[tuple]) -> float | None:
    """OS F11.5 #77 (R-041): a menor distância em mm até a região VIZINHA
    alinhada — gap horizontal quando há sobreposição vertical, gap vertical
    quando há sobreposição horizontal; 0 quando sobrepostas; None sem
    vizinha alinhada. Puro (testável por valor)."""
    x, y, w, h = rect
    melhor: float | None = None
    for ox, oy, ow, oh in outros:
        if oy < y + h and oy + oh > y:          # alinhadas na vertical
            if ox >= x + w:
                g = ox - (x + w)
            elif ox + ow <= x:
                g = x - (ox + ow)
            else:
                g = 0.0
            melhor = g if melhor is None else min(melhor, g)
        if ox < x + w and ox + ow > x:          # alinhadas na horizontal
            if oy >= y + h:
                g = oy - (y + h)
            elif oy + oh <= y:
                g = y - (oy + oh)
            else:
                g = 0.0
            melhor = g if melhor is None else min(melhor, g)
    return melhor

LIMIAR_SNAP = 6.0  # px de cena

# R-040: uma cor por PAPEL no modo raio-x (estrutura sem a arte)
def _cores_papel():
    from app.rendering.model import TipoRegiao as TR
    return {
        TR.IMAGEM: t.SELECAO, TR.NOME: t.SUCESSO, TR.PRECO: t.ACENTO,
        TR.UNIDADE: t.GUIA_SNAP, TR.SELO: t.ALERTA, TR.TEXTO_LEGAL: t.TEXTO_3,
    }

# cursor por canto: 0=TL 1=TR 2=BL 3=BR (diagonais corretas)
_CURSOR_CANTO = {
    0: Qt.CursorShape.SizeFDiagCursor, 3: Qt.CursorShape.SizeFDiagCursor,
    1: Qt.CursorShape.SizeBDiagCursor, 2: Qt.CursorShape.SizeBDiagCursor,
}


class RegiaoItem(QGraphicsItem):
    TAM = 9
    MIN = 10

    def __init__(self, regiao, largura: float, altura: float, canvas):
        super().__init__()
        self.regiao = regiao
        self._w = largura
        self._h = altura
        self.canvas = canvas
        self._resize = None
        self._fixo = None
        self._hover = False
        self._hover_grupo = False        # RG-15: o trio da célula acende junto
        self._colapsar_no_release = False
        self._pos_press = None
        self._alca_hover: int | None = None
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, not regiao.travado)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges, True)
        self.setAcceptHoverEvents(True)
        self.aplicar_rotacao()           # RG-12: o contorno acompanha o desenho

    def aplicar_rotacao(self) -> None:
        """RG-12: gira o item de seleção em torno do centro — hover/clique
        casam com o conteúdo girado. Posição do modelo (x/y) não muda."""
        self.setTransformOriginPoint(self._w / 2, self._h / 2)
        self.setRotation(self.regiao.rotacao_graus % 360)

    # --- geometria -------------------------------------------------------------

    def boundingRect(self) -> QRectF:
        m = self.TAM
        return QRectF(-m, -m, self._w + 2 * m, self._h + 2 * m)

    def _cantos(self):
        return [(0, 0), (self._w, 0), (0, self._h), (self._w, self._h)]

    def rect_cena(self) -> QRectF:
        return QRectF(self.x(), self.y(), self._w, self._h)

    def _escala_view(self) -> float:
        """Escala atual da view (para traço/alças de tamanho constante na tela)."""
        views = self.scene().views() if self.scene() else []
        return max(views[0].transform().m11(), 1e-6) if views else 1.0

    def _paint_raio_x(self, painter) -> None:
        esc = self._escala_view()
        cor = QColor(_cores_papel().get(self.regiao.tipo, t.SELECAO))
        preench = QColor(cor)
        preench.setAlpha(70 if self.isSelected() else 45)
        painter.setPen(QPen(cor, (2.0 if self.isSelected() else 1.2) / esc))
        painter.setBrush(QBrush(preench))
        painter.drawRect(QRectF(0, 0, self._w, self._h))
        f = painter.font()
        f.setPixelSize(max(6, int(9 / esc)))
        painter.setFont(f)
        painter.setPen(QPen(cor, 1.0 / esc))
        painter.drawText(QRectF(3 / esc, 2 / esc, self._w, self._h),
                         Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft,
                         self.regiao.nome or self.regiao.tipo.value)

    def _paint_badge_papel(self, painter) -> None:
        """RG-57 (passos 5-6): badge PERMANENTE do papel do texto legal —
        cor + ícone + nome, no canto inferior-esquerdo (fora do M/C do topo e
        dos pontinhos de override do topo-direito). Reconhecível de relance."""
        from app.rendering.model import TipoRegiao as _TR
        if self.regiao.tipo != _TR.TEXTO_LEGAL:
            return
        from PySide6.QtCore import QSize
        from app.qt.design.icones import icone
        from app.qt.design.papel_texto_ui import badge_de_papel
        rotulo, cor, nome_ic = badge_de_papel(self.regiao.papel_texto)
        esc = self._escala_view()
        alt = 14 / esc
        pad = 4 / esc
        ic = 10 / esc
        gap = 3 / esc
        f = painter.font()
        f.setPixelSize(max(6, int(9 / esc)))
        f.setBold(True)
        painter.setFont(f)
        larg_txt = painter.fontMetrics().horizontalAdvance(rotulo)
        larg = pad + ic + gap + larg_txt + pad
        x, y = 1 / esc, self._h - alt - 1 / esc
        painter.setPen(QPen(QColor(t.ALCA_PREENCHIMENTO), 1.0 / esc))
        painter.setBrush(QBrush(QColor(cor)))
        painter.drawRoundedRect(QRectF(x, y, larg, alt), 3 / esc, 3 / esc)
        pm = icone(nome_ic, cor="#ffffff", tamanho=12).pixmap(QSize(24, 24))
        painter.drawPixmap(QRectF(x + pad, y + (alt - ic) / 2, ic, ic),
                           pm, QRectF(pm.rect()))
        painter.setPen(QPen(QColor("#ffffff"), 1.0 / esc))
        painter.drawText(
            QRectF(x + pad + ic + gap, y, larg_txt + 2 / esc, alt),
            Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, rotulo)

    def _emitir_medidas(self) -> None:
        """R-041 (passo 75/77): X/Y/L/A da região em mm + a COTA até a borda
        da arte mais próxima — ao vivo, enquanto move/redimensiona."""
        r = self.rect_cena()
        x_mm, y_mm = self.canvas.cena_para_mm(r.x(), r.y())
        w_mm, h_mm = self.canvas.cena_para_mm(r.width(), r.height())
        lay = self.canvas._layout
        cota = ""
        if lay is not None:
            dir_ = lay.largura_mm - (x_mm + w_mm)
            base = lay.altura_mm - (y_mm + h_mm)
            cota = (f"  ·  ←{x_mm:.0f}  →{max(dir_, 0):.0f}  "
                    f"↑{y_mm:.0f}  ↓{max(base, 0):.0f} mm")
        # OS F11.5 #77: a cota até a REGIÃO vizinha mais próxima (alinhada),
        # ao vivo — além das 4 bordas da arte
        outros = []
        for it in self.canvas._itens:
            if it is self:
                continue
            ro = it.rect_cena()
            ox_mm, oy_mm = self.canvas.cena_para_mm(ro.x(), ro.y())
            ow_mm, oh_mm = self.canvas.cena_para_mm(ro.width(), ro.height())
            outros.append((ox_mm, oy_mm, ow_mm, oh_mm))
        viz = cota_entre_rects((x_mm, y_mm, w_mm, h_mm), outros)
        if viz is not None:
            cota += f"  ·  ⇄ vizinha {viz:.0f} mm"
        self.canvas.medidas.emit(
            f"X {x_mm:.0f}  Y {y_mm:.0f}  ·  L {w_mm:.0f}  A {h_mm:.0f} mm{cota}")

    def paint(self, painter, option, widget=None) -> None:
        # R-040 (raio-x): sem a arte, pinta a região por PAPEL (uma cor por
        # tipo) com o rótulo — enxergar a estrutura e a sobreposição
        if self.canvas.raio_x_ligado():
            self._paint_raio_x(painter)
            return
        sel = self.isSelected()
        esc = self._escala_view()
        if sel:
            caneta = QPen(QColor(t.SELECAO), 1.6 / esc)
        elif self._hover and not self.regiao.travado:
            caneta = QPen(QColor(t.SELECAO_HOVER), 1.4 / esc)
        elif self._hover_grupo and not self.regiao.travado:
            # RG-15: o resto do trio acende junto (mais leve que o hover)
            cor = QColor(t.SELECAO_HOVER)
            cor.setAlpha(160)
            caneta = QPen(cor, 1.2 / esc)
        else:
            # célula-mestre em âmbar (identificável de relance); demais em azul
            cor = QColor(t.ACENTO if self.canvas.eh_mestre(self.regiao) else t.SELECAO)
            cor.setAlpha(150 if self.canvas.eh_mestre(self.regiao) else 110)
            caneta = QPen(cor, 1.0 / esc, Qt.PenStyle.DashLine)
        painter.setPen(caneta)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRect(QRectF(0, 0, self._w, self._h))

        # RG-19: a região SELO aparecia VAZIA no editor — placeholder que
        # explica o comportamento multifunção (só aqui; o export não muda)
        from app.rendering.model import TipoRegiao as _TR
        if self.regiao.tipo == _TR.SELO:
            fonte_ph = painter.font()
            fonte_ph.setPointSizeF(max(6.0, 8.5 / esc))
            painter.setFont(fonte_ph)
            cor_ph = QColor(t.TEXTO_3)
            cor_ph.setAlpha(200)
            painter.setPen(QPen(cor_ph, 1.0 / esc))
            painter.drawText(
                QRectF(2, 2, self._w - 4, self._h - 4),
                Qt.AlignmentFlag.AlignCenter | Qt.TextFlag.TextWordWrap,
                "SELO\n(+18 e “Qualidade” entram\naqui automaticamente)")

        if sel and not self.regiao.travado:
            # alças estilo Figma: miolo branco, borda primária; cresce no hover
            for i, (cx, cy) in enumerate(self._cantos()):
                lado = (self.TAM + (2 if i == self._alca_hover else 0)) / esc
                painter.setPen(QPen(QColor(t.ALCA_BORDA), 1.4 / esc))
                painter.setBrush(QBrush(QColor(t.ALCA_PREENCHIMENTO)))
                painter.drawRect(QRectF(cx - lado / 2, cy - lado / 2, lado, lado))

        # RG-56 (passo 20): BADGE permanente do estado agrupável — óbvio de
        # relance. Âmbar "M" = mestra · violeta "C" = cópia · solta = nada
        # (o contorno neutro já basta). Só na 1ª região da célula (canto
        # superior-esquerdo do slot), para não repetir em todo o trio.
        estado = self.canvas.estado_de_grupo(self.regiao)
        if estado in ("mestra", "copia") and self._e_ancora_do_slot():
            cor_b = QColor(t.ACENTO if estado == "mestra" else t.GUIA_SNAP)
            letra = "M" if estado == "mestra" else "C"
            lado = 13 / esc
            painter.setPen(QPen(QColor(t.ALCA_PREENCHIMENTO), 1.0 / esc))
            painter.setBrush(QBrush(cor_b))
            painter.drawRoundedRect(QRectF(1 / esc, 1 / esc, lado, lado),
                                    3 / esc, 3 / esc)
            f = painter.font()
            f.setPixelSize(max(6, int(9 / esc)))
            f.setBold(True)
            painter.setFont(f)
            painter.setPen(QPen(QColor("#ffffff"), 1.0 / esc))
            painter.drawText(QRectF(1 / esc, 1 / esc, lado, lado),
                             Qt.AlignmentFlag.AlignCenter, letra)

        # indicador de override: pontinho âmbar (a célula tem ajuste próprio)
        if self.regiao.overrides and not self.canvas.eh_mestre(self.regiao):
            r = 3.5 / esc
            painter.setPen(QPen(QColor(t.ALCA_PREENCHIMENTO), 1.0 / esc))
            painter.setBrush(QBrush(QColor(t.ACENTO)))
            painter.drawEllipse(QPointF(self._w - 2 * r, 2 * r), r, r)

        # F7.3 (B2): pontinho VIOLETA = o SLOT tem override de conteúdo
        # (nome/preço/foto trocados só nesta célula — 3ª aparição do padrão)
        slot_ov = self.canvas._slot_de(self.regiao)
        if slot_ov is not None and self.canvas.overrides.get(slot_ov.id):
            r = 3.5 / esc
            painter.setPen(QPen(QColor(t.ALCA_PREENCHIMENTO), 1.0 / esc))
            painter.setBrush(QBrush(QColor(t.GUIA_SNAP)))
            painter.drawEllipse(QPointF(self._w - 4.5 * r, 2 * r), r, r)

        # RG-57 (passos 5-6): badge do papel do texto legal (só TEXTO_LEGAL)
        self._paint_badge_papel(painter)

    # --- snapping ao mover -----------------------------------------------------

    def itemChange(self, change, value):
        if (
            change == QGraphicsItem.GraphicsItemChange.ItemPositionChange
            and self.scene() is not None
            and self._resize is None
            and not self.regiao.travado
        ):
            # R-028 (passo 63): segurar Alt SUSPENDE o snap (posição livre)
            from PySide6.QtWidgets import QApplication
            if QApplication.keyboardModifiers() & Qt.KeyboardModifier.AltModifier:
                self.canvas.mostrar_guias([])
                return super().itemChange(change, value)
            ax, ay = self.canvas.alvos_snap(self)
            nx, ny, guias = snap((value.x(), value.y(), self._w, self._h), ax, ay, LIMIAR_SNAP)
            self.canvas.mostrar_guias(guias)
            return QPointF(nx, ny)
        if (change == QGraphicsItem.GraphicsItemChange.ItemPositionHasChanged
                and self.scene() is not None):
            self._emitir_medidas()          # R-041: X/Y/L/A ao vivo ao mover
        return super().itemChange(change, value)

    # --- célula como grupo (RG-15) ----------------------------------------------

    def _irmas(self) -> list["RegiaoItem"]:
        """Os itens das OUTRAS regiões do mesmo slot (o resto do trio)."""
        slot = self.canvas._slot_de(self.regiao)
        if slot is None:
            return []
        return [it for it in self.canvas._itens
                if it is not self and it.regiao in slot.regioes]

    def _e_ancora_do_slot(self) -> bool:
        """A 1ª região do slot — onde o badge de grupo aparece UMA vez (RG-56
        passo 20), não repetido em todo o trio."""
        slot = self.canvas._slot_de(self.regiao)
        return bool(slot is not None and slot.regioes
                    and slot.regioes[0] is self.regiao)

    def _selecao_por_clique(self, com_modificador: bool, ponto_cena=None) -> None:
        """RG-15 ("clico e dá errado"): o 1º clique numa célula seleciona o
        TRIO inteiro; o 2º clique (sem arrastar) entra na região. Chamado
        APÓS a seleção padrão do Qt; Ctrl/Shift preservam o gesto multi.
        DENTRO da célula ISOLADA (duplo clique, estilo Illustrator) o clique
        é DIRETO na peça — o trio não acende nem colapsa."""
        self._colapsar_no_release = False
        from app.qt.design import diag_selecao
        if com_modificador or not self.isSelected():
            if diag_selecao.ligado():
                diag_selecao.anotar(
                    "clique_ignorado", **self.canvas._contexto_regiao(self.regiao),
                    com_modificador=com_modificador, estava_selecionada=self.isSelected())
            return
        # RG-55 (passos 9-12): a PRIMÁRIA (o que o painel mostra) é a região
        # CONCRETA no topo do z sob o clique, resolvida por `resolver_selecao`
        # — o mesmo picking dos passos 9-12, no caminho de produção. Sem ponto
        # (chamadas legadas), cai na própria região.
        prim = (self.canvas.resolver_selecao(ponto_cena)
                if ponto_cena is not None else None)
        self.canvas._primaria = prim if prim is not None else self.regiao
        # Isolamento de CÉLULA: cada peça edita sozinha (RG-55 intacto — a
        # primária já é a região clicada; o painel a mostra)
        if self.canvas.celula_isolada(self.canvas._slot_de(self.regiao)):
            if diag_selecao.ligado():
                diag_selecao.anotar(
                    "clique_isolado", **self.canvas._contexto_regiao(self.regiao))
            return
        irmas = self._irmas()
        if not irmas:
            if diag_selecao.ligado():
                diag_selecao.anotar(
                    "clique_solta", **self.canvas._contexto_regiao(self.regiao))
            return
        grupo_ja_ativo = any(it.isSelected() for it in irmas)
        if diag_selecao.ligado():
            diag_selecao.anotar(
                "clique_grupo", **self.canvas._contexto_regiao(self.regiao),
                tinha_irmas=True, grupo_ja_ativo=grupo_ja_ativo,
                # seleciona o TRIO (multi-seleção); com a cura do RG-55 o
                # painel mostra a PRIMÁRIA (nunca órfão), não None
                vai_selecionar_trio=not grupo_ja_ativo)
        if grupo_ja_ativo:
            # o grupo já estava ativo: marcar p/ entrar na região no release
            # (no release, porque o clique também pode ser o início de um
            # arrasto do grupo inteiro — aí a seleção fica)
            self._colapsar_no_release = True
        else:
            for it in irmas:             # 1º clique: a célula vira o grupo
                it.setSelected(True)

    def _colapsar_se_clique_parado(self) -> None:
        """RG-15: 2º clique SEM arrasto = entrar na região (o grupo colapsa).
        Se houve arrasto, o grupo fica (mover a célula inteira é gesto)."""
        parado = self.pos() == self._pos_press
        if self._colapsar_no_release and parado:
            from app.qt.design import diag_selecao
            if diag_selecao.ligado():
                diag_selecao.anotar(
                    "colapso_no_release", **self.canvas._contexto_regiao(self.regiao))
            for it in self._irmas():
                it.setSelected(False)
            self.setSelected(True)
        self._colapsar_no_release = False

    def _marcar_hover_grupo(self, ligado: bool) -> None:
        # dentro da célula isolada o trio não acende nem no hover — cada
        # peça é uma peça (o véu já conta a história do resto)
        if self.canvas.celula_isolada(self.canvas._slot_de(self.regiao)):
            return
        for it in self._irmas():
            it._hover_grupo = ligado
            it.update()

    # --- hover (realce + cursores) ---------------------------------------------

    def hoverEnterEvent(self, event) -> None:
        self._hover = True
        self._marcar_hover_grupo(True)   # RG-15: o trio acende junto
        self.update()
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event) -> None:
        self._hover = False
        self._alca_hover = None
        self._marcar_hover_grupo(False)
        self.unsetCursor()
        self.update()
        super().hoverLeaveEvent(event)

    def hoverMoveEvent(self, event) -> None:
        alca = self._handle_em(event.pos()) if self.isSelected() else None
        if alca != self._alca_hover:
            self._alca_hover = alca
            self.update()
        if self.regiao.travado:
            self.unsetCursor()
        elif alca is not None:
            self.setCursor(_CURSOR_CANTO[alca])
        else:
            self.setCursor(Qt.CursorShape.SizeAllCursor)
        super().hoverMoveEvent(event)

    # --- interação -------------------------------------------------------------

    def _handle_em(self, pos):
        for i, (cx, cy) in enumerate(self._cantos()):
            if abs(pos.x() - cx) <= self.TAM and abs(pos.y() - cy) <= self.TAM:
                return i
        return None

    def mousePressEvent(self, event) -> None:
        # RG-12: região girada não redimensiona pelas alças (a matemática do
        # arrasto assume item reto) — mover funciona; tamanho pelo painel
        if not self.regiao.travado and not (self.regiao.rotacao_graus % 360):
            h = self._handle_em(event.pos())
            if h is not None:
                self._resize = h
                opostos = {0: (self._w, self._h), 1: (0, self._h), 2: (self._w, 0), 3: (0, 0)}
                self._fixo = self.mapToScene(*opostos[h])
                event.accept()
                return
        super().mousePressEvent(event)
        # RG-15: depois da seleção padrão do Qt, aplica a regra da célula
        self._pos_press = self.pos()
        mods = event.modifiers() & (Qt.KeyboardModifier.ControlModifier
                                    | Qt.KeyboardModifier.ShiftModifier)
        # RG-55: a PRIMÁRIA (o que o painel mostra) é resolvida pelo picking
        # de produção `resolver_selecao` NO PONTO do clique — a mesma função
        # dos passos 9-12, agora no caminho REAL (não só em teste).
        self._selecao_por_clique(bool(mods), event.scenePos())

    def mouseMoveEvent(self, event) -> None:
        if self._resize is not None:
            m = event.scenePos()
            x0, y0 = self._fixo.x(), self._fixo.y()
            self.prepareGeometryChange()
            self.setPos(min(x0, m.x()), min(y0, m.y()))
            self._w = max(self.MIN, abs(m.x() - x0))
            self._h = max(self.MIN, abs(m.y() - y0))
            self.update()
            self._emitir_medidas()          # R-041: L/A ao vivo ao redimensionar
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event) -> None:
        self._resize = None
        super().mouseReleaseEvent(event)
        self.canvas.mostrar_guias([])
        self._colapsar_se_clique_parado()
        self.canvas._commit_regiao(self)

    def mouseDoubleClickEvent(self, event) -> None:
        """O gesto do Illustrator: duplo clique ENTRA no grupo/célula (modo
        de isolamento — cada peça edita sozinha; Esc sai). O press do duplo
        já rodou a seleção normal; aqui só empilhamos o nível e desarmamos o
        colapso do RG-15 (senão os dois gestos brigariam no release)."""
        if (event.button() == Qt.MouseButton.LeftButton
                and not event.modifiers()
                and self.canvas.isolar_por_duplo_clique(self.regiao)):
            self._colapsar_no_release = False
            event.accept()
            return
        super().mouseDoubleClickEvent(event)

    def montar_menu_contexto(self):
        """Constrói o menu de contexto da região e o mapa ação→callable. UMA
        fonte de verdade (RG-56 passo 15): usada pelo clique e pela foto dos
        3 estados, sem divergir. Devolve (menu, acoes)."""
        def _agrupar():
            self.setSelected(True)
            self.canvas.agrupar_selecao()
            self.canvas.abrir_tutorial_agrupar(primeira_vez=True)   # passo 26

        slot = self.canvas._slot_de(self.regiao)
        menu = QMenu()
        acoes = {}                       # QAction → callable(sem args)

        a_cop = menu.addAction(icone("duplicar", tamanho=16), "Copiar")
        a_cop.setShortcut("Ctrl+C")
        acoes[a_cop] = lambda: (self.setSelected(True),
                                self.canvas.copiar_selecao())
        a_col = menu.addAction(icone("duplicar", tamanho=16), "Colar")
        a_col.setShortcut("Ctrl+V")
        a_col.setEnabled(self.canvas._area_transferencia is not None)
        acoes[a_col] = self.canvas.colar
        a_dup = menu.addAction(icone("duplicar", tamanho=16), "Duplicar")
        a_dup.setShortcut("Ctrl+D")
        acoes[a_dup] = lambda: self.canvas.duplicar_regiao(self.regiao)
        a_del = menu.addAction(icone("lixeira", tamanho=16), "Excluir")
        a_del.setShortcut("Del")
        acoes[a_del] = lambda: self.canvas.excluir_regiao(self.regiao)
        menu.addSeparator()
        if self.regiao.travado:
            a_trav = menu.addAction(icone("cadeado_aberto", tamanho=16), "Destravar")
        else:
            a_trav = menu.addAction(icone("cadeado", tamanho=16), "Travar")
        acoes[a_trav] = lambda: self.canvas.set_travado(
            self.regiao, not self.regiao.travado)

        # Modo de isolamento (estilo Illustrator) — RG-56: todo estado tem o
        # inverso a UM clique; o menu ensina o gesto do duplo clique. A
        # condição BATE com a capacidade real do gesto (achado da frota:
        # oferecer "isolar" onde o isolar não faz nada é clique morto, I2):
        # grupo com 2+ células OU célula com 2+ peças.
        if self.canvas.em_isolamento():
            a_sair = menu.addAction(icone("restaurar", tamanho=16),
                                    "Sair do isolamento")
            a_sair.setShortcut("Esc")
            acoes[a_sair] = lambda: self.canvas.sair_isolamento(tudo=True)
        elif slot is not None:
            from app.rendering.grade import mestre_do_slot, slots_do_grupo
            pagina = self.canvas._pagina()
            mestre = mestre_do_slot(pagina, slot)
            grupo_2mais = (mestre is not None
                           and len(slots_do_grupo(pagina, mestre)) >= 1)
            if grupo_2mais or len(slot.regioes) >= 2:
                a_iso = menu.addAction(icone("grade", tamanho=16),
                                       "Entrar no grupo (isolar)")
                a_iso.setToolTip("Edita cada peça sozinha, com o resto da "
                                 "página fora de foco — o duplo clique faz "
                                 "o mesmo; Esc sai")
                acoes[a_iso] = lambda: self.canvas.isolar_por_duplo_clique(
                    self.regiao)

        # R-031 (Fase 5): conta-gotas de estilo — copia SÓ estilo (nunca
        # geometria/conteúdo); colar vale na seleção inteira (lote).
        menu.addSeparator()
        a_cop_est = menu.addAction(icone("duplicar", tamanho=16), "Copiar estilo")
        a_cop_est.setToolTip("Copia fonte, tamanho, cor, contorno e pílula — "
                             "só o estilo, não move nem troca o conteúdo")
        acoes[a_cop_est] = lambda: self.canvas.copiar_estilo(self.regiao)
        a_col_est = menu.addAction(icone("duplicar", tamanho=16),
                                   "Colar estilo na seleção")
        a_col_est.setEnabled(self.canvas.tem_estilo_copiado())
        acoes[a_col_est] = lambda: self.canvas.colar_estilo(
            [i.regiao for i in self.canvas.selecionados()] or [self.regiao])

        # RG-57 (passo 11): recategorizar o PAPEL do texto legal sem apagar e
        # recriar — o texto se preserva; o compositor reinterpreta pelo papel.
        from app.rendering.model import TipoRegiao as _TRp
        if self.regiao.tipo == _TRp.TEXTO_LEGAL:
            from app.qt.design.papel_texto_ui import ORDEM_PAPEIS, ROTULO_PAPEL
            menu.addSeparator()
            sub = menu.addMenu(icone("paragrafo", tamanho=16), "Papel do texto")
            for p in ORDEM_PAPEIS:
                a_p = sub.addAction(ROTULO_PAPEL[p])
                a_p.setCheckable(True)
                a_p.setChecked(self.regiao.papel_texto == p)
                acoes[a_p] = (lambda pp=p:
                              self.canvas.definir_papel_texto(self.regiao, pp))

        if self.regiao.overrides and not self.canvas.eh_mestre(self.regiao):
            menu.addSeparator()
            n = len(self.regiao.overrides)
            a_rest = menu.addAction(
                icone("restaurar", tamanho=16),
                f"Restaurar da mestra ({n} ajuste{'s' if n > 1 else ''})")
            a_rest.setToolTip("Descarta os ajustes locais; volta a seguir a mestra")
            acoes[a_rest] = lambda: self.canvas.restaurar_da_mestra(self.regiao)

        # override de CONTEÚDO por slot (F7.3 — só na Mesa, que liga ao_override)
        if callable(self.canvas.ao_override) and slot is not None:
            menu.addSeparator()
            a_ov = menu.addAction(icone("propriedades", tamanho=16),
                                  "Conteúdo desta célula (override)…")
            a_ov.setToolTip("Nome/preço/foto só NESTA célula — "
                            "o item da estante não muda")
            acoes[a_ov] = lambda sid=slot.id: self.canvas.ao_override(sid)
            if self.canvas.overrides.get(slot.id):
                n = len(self.canvas.overrides[slot.id])
                a_ov_rest = menu.addAction(
                    icone("restaurar", tamanho=16),
                    f"Restaurar do item ({n} campo{'s' if n > 1 else ''})")
                a_ov_rest.setToolTip("Descarta o override; a célula volta a "
                                     "seguir o item da estante")
                acoes[a_ov_rest] = lambda sid=slot.id: \
                    self.canvas.set_override(sid, None)

        # --- RG-56 (Fase 4): agrupar/desagrupar VISÍVEL e reversível ---
        # SEMPRE a ação pertinente ao estado (passo 15); todo estado tem o
        # inverso a UM clique (passo 27).
        from app.rendering.grade import TIPOS_CONTEUDO
        menu.addSeparator()
        estado = self.canvas.estado_de_grupo(self.regiao)
        if estado == "solta":
            # passo 16 + 22 (lei da casa): só CONTEÚDO de produto vira mestre
            if self.regiao.tipo in TIPOS_CONTEUDO:
                a_grupo = menu.addAction(icone("grade", tamanho=16),
                                         "Agrupar como replicável")
                a_grupo.setToolTip("As regiões selecionadas viram uma "
                                   "célula-mestre — edições nela repetem "
                                   "nas cópias.")
                acoes[a_grupo] = _agrupar
        elif estado == "mestra":                 # passo 17
            a_desagr = menu.addAction(icone("grade", tamanho=16), "Desagrupar")
            a_desagr.setToolTip("Dissolve o grupo: cada célula vira "
                                "independente, com os valores atuais "
                                "(nada se perde).")
            acoes[a_desagr] = lambda: self.canvas.desagrupar_regiao(self.regiao)
            a_edit = menu.addAction(icone("propriedades", tamanho=16),
                                    "Editar como mestra")
            a_edit.setToolTip("Seleciona a célula-mestre — o que você mudar "
                              "aqui replica nas cópias.")
            acoes[a_edit] = lambda: self.canvas.editar_como_mestra(self.regiao)
        elif estado == "copia":                  # passo 18
            a_desagr = menu.addAction(icone("grade", tamanho=16), "Desagrupar")
            a_desagr.setToolTip("Dissolve o grupo: cada célula vira "
                                "independente, com os valores atuais "
                                "(nada se perde).")
            acoes[a_desagr] = lambda: self.canvas.desagrupar_regiao(self.regiao)
            # o "Restaurar da mestra (N ajustes)" da cópia já sai acima
            # (overrides de estilo/geometria); o "Restaurar do item" cobre
            # os overrides de CONTEÚDO (F7.3)
        if slot is not None and (slot.ref_grupo is not None
                                 or (slot.mestre and slot.origem_mm)):
            a_celula = menu.addAction(icone("lixeira", tamanho=16),
                                      "Remover esta célula")
            a_celula.setToolTip("O item volta à estante ('fora da grade'); "
                                "as vizinhas não se movem")
            acoes[a_celula] = lambda sid=slot.id: self.canvas.remover_celula(sid)
        return menu, acoes

    def contextMenuEvent(self, event) -> None:
        menu, acoes = self.montar_menu_contexto()
        escolha = menu.exec(event.screenPos())
        if escolha in acoes:
            acoes[escolha]()

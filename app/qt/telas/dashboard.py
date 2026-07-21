"""
Dashboard — a casa do app (F6.1)
================================
Tela de chegada: **projetos salvos em pastas por evento** ("Terça do Pão"),
cada um com miniatura, nome, tipo e data — prateleiras horizontais por evento.
Duplo-clique reabre **idêntico** (congelado); botão direito: abrir/duplicar/
renomear/excluir. Ações rápidas: novo tabloide / cartaz / layout.

Recarrega ao aparecer (``showEvent``) — reflete o que acabou de ser salvo.
"""

from __future__ import annotations

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QColor, QIcon, QPixmap
from PySide6.QtWidgets import (
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMenu,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from app.core import projetos
from app.qt.design import tokens as t
from app.qt.design.componentes import EstadoVazio
from app.qt.design.icones import icone
from app.qt.design.toast import mostrar_toast

_MINIATURA = 150
_ICONE_TIPO = {"TABLOIDE": "grade", "CARTAZ": "impressora"}


from app.qt.design.componentes import SombraHoverDelegate


class _CartaoCapa(QWidget):
    """FASE 3 (RG-59, passos 1-8): o cartão de evento como CAPA cheia —
    cover + gradiente escuro + nome sobreposto + chips translúcidos +
    borda-superior fina na cor do evento. Sem capa: gradiente da cor com
    a inicial grande (nunca retângulo vazio). Hover: zoom 1.03 (200 ms)
    + elevação da Fase 1."""

    ALTURA = 150

    def __init__(self, titulo: str, cor: str, capa: QPixmap,
                 chips: list[str], ao_abrir, parent=None):
        super().__init__(parent)
        self._titulo = titulo
        self._cor = cor
        self._capa = capa
        self._chips = [c for c in chips if c]
        self._ao_abrir = ao_abrir
        self._zoom = 1.0
        self._anim = None
        self.setMinimumWidth(320)
        self.setFixedHeight(self.ALTURA)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def mousePressEvent(self, ev) -> None:  # noqa: N802 (Qt)
        if ev.button() == Qt.MouseButton.LeftButton:
            self._ao_abrir()

    def _animar_zoom(self, alvo: float) -> None:
        from app.qt.design.animacoes import animacoes_ligadas, registrar
        if self._anim is not None:
            self._anim.stop()
        if not animacoes_ligadas() or self.window().testAttribute(
                Qt.WidgetAttribute.WA_DontShowOnScreen):
            self._zoom = alvo
            self.update()
            return
        from PySide6.QtCore import QEasingCurve, QVariantAnimation
        anim = QVariantAnimation(self)
        anim.setDuration(200)
        anim.setStartValue(self._zoom)
        anim.setEndValue(alvo)
        anim.setEasingCurve(QEasingCurve.Type.OutCubic)

        def _passo(v):
            self._zoom = float(v)
            self.update()
        anim.valueChanged.connect(_passo)
        self._anim = anim
        registrar(anim)
        anim.start()

    def enterEvent(self, ev) -> None:  # noqa: N802 (Qt)
        self._animar_zoom(1.03)
        from PySide6.QtWidgets import QGraphicsDropShadowEffect

        from PySide6.QtGui import QColor
        sombra = QGraphicsDropShadowEffect(self)
        blur, dy, alfa = t.SOMBRA_2
        sombra.setBlurRadius(blur)
        sombra.setOffset(0, dy)
        cor = QColor(t.SOMBRA)
        cor.setAlpha(alfa)
        sombra.setColor(cor)
        self.setGraphicsEffect(sombra)

    def leaveEvent(self, ev) -> None:  # noqa: N802 (Qt)
        self._animar_zoom(1.0)
        self.setGraphicsEffect(None)

    def paintEvent(self, ev) -> None:  # noqa: N802 (Qt)
        from PySide6.QtCore import QRectF
        from PySide6.QtGui import (
            QColor, QFont, QLinearGradient, QPainter, QPainterPath)
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        r = QRectF(self.rect())
        caminho = QPainterPath()
        caminho.addRoundedRect(r, t.RAIO_CARTAO, t.RAIO_CARTAO)
        p.setClipPath(caminho)

        if not self._capa.isNull():
            # COVER com zoom do hover: escala cobre o retângulo inteiro
            pw, ph = self._capa.width(), self._capa.height()
            esc = max(r.width() / pw, r.height() / ph) * self._zoom
            lw, lh = pw * esc, ph * esc
            # âncora no TOPO quando a imagem é mais alta (tabloide
            # vertical): o corte mostra o CABEÇALHO da arte — a marca da
            # campanha, não produtos aleatórios do miolo
            y = 0.0 if lh > r.height() else (r.height() - lh) / 2
            p.drawPixmap(
                QRectF((r.width() - lw) / 2, y, lw, lh),
                self._capa, QRectF(0, 0, pw, ph))
        else:                            # passo 6: gradiente + inicial
            grad = QLinearGradient(0, 0, r.width(), r.height())
            grad.setColorAt(0, QColor(self._cor))
            escura = QColor(self._cor).darker(160)
            grad.setColorAt(1, escura)
            p.fillRect(r, grad)
            inicial = (self._titulo[:1] or "?").upper()
            fonte_i = QFont(t.FONTE_UI[0])
            fonte_i.setPixelSize(int(r.height() * 0.72))
            fonte_i.setWeight(QFont.Weight.Bold)
            p.setFont(fonte_i)
            p.setPen(QColor(255, 255, 255, 46))
            p.drawText(r.adjusted(0, -6, -12, 0),
                       Qt.AlignmentFlag.AlignRight
                       | Qt.AlignmentFlag.AlignVCenter, inicial)

        # gradiente escuro de baixo pra cima (legibilidade — passo 2)
        veu = QLinearGradient(0, r.height() * 0.35, 0, r.height())
        veu.setColorAt(0, QColor(0, 0, 0, 0))
        veu.setColorAt(1, QColor(0, 0, 0, 185))
        p.fillRect(r, veu)

        # borda-superior fina na cor (passo 5)
        p.fillRect(QRectF(0, 0, r.width(), 3), QColor(self._cor))

        # nome sobreposto com sombra suave (passo 3)
        fonte_n = QFont(t.FONTE_UI[0])
        fonte_n.setPointSizeF(12)
        fonte_n.setWeight(QFont.Weight.DemiBold)
        p.setFont(fonte_n)
        base_y = r.height() - 14
        p.setPen(QColor(0, 0, 0, 160))
        p.drawText(QRectF(15, 0, r.width() - 30, base_y + 1),
                   Qt.AlignmentFlag.AlignLeft
                   | Qt.AlignmentFlag.AlignBottom, self._titulo)
        p.setPen(QColor("#FFFFFF"))
        p.drawText(QRectF(14, 0, r.width() - 30, base_y),
                   Qt.AlignmentFlag.AlignLeft
                   | Qt.AlignmentFlag.AlignBottom, self._titulo)

        # chips translúcidos no canto inferior-direito (passos 4-5)
        fonte_c = QFont(t.FONTE_UI[0])
        fonte_c.setPointSizeF(7.5)
        fonte_c.setWeight(QFont.Weight.DemiBold)
        p.setFont(fonte_c)
        fm = p.fontMetrics()
        x = r.width() - 10
        for texto in reversed(self._chips):
            larg = fm.horizontalAdvance(texto) + 14
            chip = QRectF(x - larg, r.height() - 30, larg, 20)
            x -= larg + 6
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QColor(0, 0, 0, 130))
            p.drawRoundedRect(chip, 10, 10)
            p.setPen(QColor(self._cor).lighter(150))
            p.drawText(chip, Qt.AlignmentFlag.AlignCenter, texto)
        p.end()


class _DelegateProjeto(SombraHoverDelegate):
    """FASE 2 (passo 29): a elevação da Fase 1 + o PONTINHO de status no
    canto do cartão do projeto (cinza rascunho · azul pronto · verde
    exportado · roxo publicado — o tooltip explica)."""

    def __init__(self, lista, cor_status):
        super().__init__(lista)
        self._cor_status = cor_status

    def paint(self, painter, option, index):  # noqa: N802 (Qt)
        super().paint(painter, option, index)
        dados = index.data(Qt.ItemDataRole.UserRole)
        if not isinstance(dados, dict):
            return
        # FASE 2 (passo 38): CHIP de status (pill com texto) no canto
        from PySide6.QtGui import QColor, QFont, QPainter
        status = dados.get("status") or "rascunho"
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        fonte = QFont(t.FONTE_UI[0])
        fonte.setPointSizeF(7)
        fonte.setWeight(QFont.Weight.DemiBold)
        painter.setFont(fonte)
        fm = painter.fontMetrics()
        texto = status.upper()
        larg = fm.horizontalAdvance(texto) + 12
        r = option.rect
        pill = r.adjusted(r.width() - larg - 8, 8, -8,
                          -(r.height() - 8 - fm.height() - 6))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(self._cor_status(status)))
        painter.drawRoundedRect(pill, 7, 7)
        painter.setPen(QColor("#FFFFFF"))
        painter.drawText(pill, Qt.AlignmentFlag.AlignCenter, texto)
        # FASE 2 (passo 49): a estrela do favorito (o gesto vive no menu —
        # lista é estática por lei RG-10, sem alvo de clique por item)
        if dados.get("favorito"):
            fonte_estrela = QFont(t.FONTE_UI[0])
            fonte_estrela.setPointSizeF(11)
            painter.setFont(fonte_estrela)
            painter.setPen(QColor(t.ACENTO))
            painter.drawText(r.adjusted(8, 6, 0, 0),
                             Qt.AlignmentFlag.AlignLeft
                             | Qt.AlignmentFlag.AlignTop, "★")
        painter.restore()


class DashboardTela(QWidget):
    """ao_abrir_projeto(projeto_id) · ao_novo(destino: 'mesa'|'fabrica'|'atelie')."""

    def __init__(self, ao_abrir_projeto=None, ao_novo=None, parent=None):
        super().__init__(parent)
        self.ao_abrir_projeto = ao_abrir_projeto
        self.ao_novo = ao_novo

        # --- zona 1 (FASE 2, passos 15-16/26): saudação + data + busca +
        # ações rápidas ------------------------------------------------------
        topo = QWidget()
        topo.setObjectName("barraFerramentas")
        vt = QVBoxLayout(topo)
        vt.setContentsMargins(t.ESP_4, t.ESP_2, t.ESP_4, t.ESP_2)
        vt.setSpacing(t.ESP_1)
        linha1 = QHBoxLayout()
        linha1.setSpacing(t.ESP_2)
        self._saudacao = QLabel("")
        self._saudacao.setProperty("papel", "titulo")
        self._data_lbl = QLabel("")
        self._data_lbl.setProperty("papel", "legenda")
        from PySide6.QtWidgets import QLineEdit
        self.campo_busca = QLineEdit()
        self.campo_busca.setPlaceholderText(
            "Buscar projeto, produto ou layout…  ·  Ctrl+K")
        self.campo_busca.setMinimumWidth(260)
        self.campo_busca.setMaximumWidth(420)
        self.campo_busca.setClearButtonEnabled(True)
        # FASE 2 (passos 72/75): dropdown de resultados com debounce 250 ms
        from PySide6.QtCore import QTimer
        self.ao_resultado_busca = None   # callable(tipo, dado) — editor_app
        self._dropdown = QListWidget(self)
        self._dropdown.setWindowFlags(Qt.WindowType.ToolTip)
        self._dropdown.itemClicked.connect(self._resultado_clicado)
        self._dropdown.hide()
        self._debounce_busca = QTimer(self)
        self._debounce_busca.setSingleShot(True)
        self._debounce_busca.setInterval(250)
        self._debounce_busca.timeout.connect(self._buscar_global)
        self.campo_busca.textChanged.connect(
            lambda _t: self._debounce_busca.start())
        self.campo_busca.returnPressed.connect(self._buscar_enter)
        linha1.addWidget(self._saudacao)
        linha1.addSpacing(t.ESP_2)
        linha1.addWidget(self._data_lbl)
        linha1.addStretch(1)
        linha1.addWidget(self.campo_busca)
        linha2 = QHBoxLayout()
        linha2.setSpacing(t.ESP_2)
        novo_tab = QPushButton(" Novo tabloide")
        novo_tab.setIcon(icone("grade", cor=t.ACENTO_TEXTO, tamanho=16))
        novo_tab.setProperty("tipo", "primario")
        novo_tab.clicked.connect(lambda: self._novo("mesa"))
        novo_cart = QPushButton(" Novo cartaz")
        novo_cart.setIcon(icone("impressora", tamanho=16))
        novo_cart.clicked.connect(lambda: self._novo("fabrica"))
        novo_lay = QPushButton(" Novo layout")
        novo_lay.setIcon(icone("camadas", tamanho=16))
        novo_lay.clicked.connect(lambda: self._novo("atelie"))
        # ("Novo evento" mudou para a aba Eventos — onde as campanhas moram)
        # R-150 (FASE 12): a porta CLARA do Modo Pai — grande, nomeada,
        # lembrada por perfil (sai-se por dentro dele, também claro)
        self.btn_modo_pai = QPushButton(" Modo simples")
        self.btn_modo_pai.setIcon(icone("check_circulo", tamanho=16))
        self.btn_modo_pai.setToolTip(
            "A visão à prova de erro: só ver o que está pronto, aprovar, "
            "imprimir e enviar — ideal para o PC da loja")
        self.btn_modo_pai.clicked.connect(self._entrar_modo_pai)
        self._resumo = QLabel("")
        self._resumo.setProperty("papel", "legenda")
        linha2.addWidget(novo_tab)
        linha2.addWidget(novo_cart)
        linha2.addWidget(novo_lay)
        linha2.addWidget(self.btn_modo_pai)
        linha2.addStretch(1)
        linha2.addWidget(self._resumo)
        vt.addLayout(linha1)
        vt.addLayout(linha2)
        self._atualizar_saudacao()

        # --- home: zona destaque (17-18) + grade de eventos (19/23) ----------
        self._pratileiras = QWidget()      # nome mantido (testes/lado de fora)
        self._coluna = QVBoxLayout(self._pratileiras)
        self._coluna.setContentsMargins(t.ESP_4, t.ESP_3, t.ESP_4, t.ESP_4)
        self._coluna.setSpacing(t.ESP_3)

        rolagem = QScrollArea()
        rolagem.setWidgetResizable(True)
        rolagem.setWidget(self._pratileiras)
        rolagem.setFrameShape(QScrollArea.Shape.NoFrame)

        # --- visão do evento (passo 20): a prateleira mora DENTRO do cartão --
        self._visao_evento = QWidget()
        self._visao_lay = QVBoxLayout(self._visao_evento)
        self._visao_lay.setContentsMargins(t.ESP_4, t.ESP_3, t.ESP_4, t.ESP_4)
        self._visao_lay.setSpacing(t.ESP_3)

        from PySide6.QtWidgets import QStackedWidget
        self._pilha = QStackedWidget()
        self._pilha.addWidget(rolagem)             # 0 = home
        self._pilha.addWidget(self._visao_evento)  # 1 = dentro do evento

        # FASE 2 (passos 91-92): faixa de saúde no rodapé, calculada em
        # WORKER (nunca no boot); "…" até os números chegarem
        self._saude_lbl = QLabel("Verificando o acervo…")
        self._saude_lbl.setProperty("papel", "legenda")
        self._saude_lbl.setContentsMargins(t.ESP_4, t.ESP_1, t.ESP_4,
                                           t.ESP_1)
        self.ao_indicador = None         # callable(chave) — editor_app liga
        self._saude_lbl.linkActivated.connect(self._indicador_clicado)

        # Auditoria do dono (20/07, 2ª rodada): o Início é SÓ o dashboard
        # ("Visão geral"); os grupos de ofertas (a `_pilha`) moram na aba
        # PRÓPRIA "Eventos" — a EventosTela ADOTA a pilha (mesmos objetos,
        # mesmos métodos daqui; nada dos testes/fluxos muda). Até a adoção,
        # a pilha fica FILHA OCULTA daqui (a árvore continua íntegra p/ os
        # testes de conteúdo; oculta = nunca pinta por cima da Visão geral).
        self._pilha.setParent(self)
        self._pilha.hide()
        raiz = QVBoxLayout(self)
        raiz.setContentsMargins(0, 0, 0, 0)
        raiz.setSpacing(0)
        raiz.addWidget(topo)
        raiz.addWidget(self._construir_visao_geral(), 1)
        raiz.addWidget(self._saude_lbl)
        self.recarregar()
        # a saúde NÃO roda no construtor: worker em tela invisível é a
        # lição da F7.1 (thread viva derruba teste/encerramento) — vai no
        # showEvent, e re-atualiza a cada volta ao Início

    # --- Visão geral (o dashboard do dono) ----------------------------------------

    def _construir_visao_geral(self) -> QWidget:
        """A aba-painel: cartões COLORIDOS de número (clicáveis — cada um leva
        pro seu lugar), "retomar de onde parou" com miniaturas e a saúde do
        acervo em barras semânticas. Os DADOS chegam por worker no showEvent —
        nasce com "—" e nunca pesa o boot."""
        from PySide6.QtWidgets import QProgressBar, QScrollArea

        from app.qt.design.componentes import Painel
        w = QWidget()
        v = QVBoxLayout(w)
        v.setContentsMargins(t.ESP_4, t.ESP_3, t.ESP_4, t.ESP_4)
        v.setSpacing(t.ESP_3)

        # cartões de número — pintados (cor viva por assunto, acompanham o
        # tema porque leem os tokens NA PINTURA), clicáveis
        self._cartoes_numero: dict[str, _CartaoIndicador] = {}
        linha = QHBoxLayout()
        linha.setSpacing(t.ESP_3)
        for chave, rotulo, nome_icone, cor_chave in (
                ("produtos", "Produtos no acervo", "caixa", "PRIMARIA"),
                ("com_foto", "Com foto", "imagem", "SUCESSO"),
                ("edicoes", "Edições salvas", "cofre", "ACENTO"),
                ("evento", "Próximo evento", "calendario", "INFO")):
            card = _CartaoIndicador(
                rotulo, nome_icone, cor_chave,
                ao_clicar=lambda c=chave: self._indicador_clicado(c))
            self._cartoes_numero[chave] = card
            linha.addWidget(card, 1)
        v.addLayout(linha)

        # retomar de onde parou (últimas edições, com MINIATURA)
        self._lista_retomar = QListWidget()
        self._lista_retomar.setMaximumHeight(200)
        self._lista_retomar.setIconSize(QSize(56, 42))
        self._lista_retomar.setToolTip("Duplo-clique reabre a edição")
        self._lista_retomar.itemDoubleClicked.connect(self._retomar_clicado)
        v.addWidget(Painel("Retomar de onde parou", "abrir",
                           self._lista_retomar))

        # saúde do acervo em barras (reusa a inteligência SÓ-LEITURA da F11)
        corpo_saude = QWidget()
        vs = QVBoxLayout(corpo_saude)
        vs.setContentsMargins(t.ESP_2, t.ESP_2, t.ESP_2, t.ESP_2)
        vs.setSpacing(t.ESP_1)
        self._barras_saude: dict[str, QProgressBar] = {}
        for chave, rotulo in (("pct_foto", "Com foto"),
                              ("pct_preco", "Com preço"),
                              ("pct_categoria", "Com categoria"),
                              ("pct_ean", "Com código de barras")):
            rot = QLabel(rotulo)
            rot.setProperty("papel", "legenda")
            barra = QProgressBar()
            barra.setValue(0)
            barra.setFormat("…")
            self._barras_saude[chave] = barra
            vs.addWidget(rot)
            vs.addWidget(barra)
        v.addWidget(Painel("Saúde do acervo", "check_circulo", corpo_saude))
        v.addStretch(1)

        rolagem = QScrollArea()
        rolagem.setWidgetResizable(True)
        rolagem.setWidget(w)
        rolagem.setFrameShape(QScrollArea.Shape.NoFrame)
        return rolagem

    def _retomar_clicado(self, item) -> None:
        pid = item.data(Qt.ItemDataRole.UserRole)
        if pid is not None and callable(self.ao_abrir_projeto):
            self.ao_abrir_projeto(pid)

    def _atualizar_visao_geral(self) -> None:
        """Worker: junta os números da visão geral (acervo, edições, evento)."""
        from app.qt.workers import GerenciadorTrabalhos, Trabalhador
        if not hasattr(self, "_trabalhos_saude"):
            self._trabalhos_saude = GerenciadorTrabalhos()

        def _rodar(_st):
            from app.core import projetos
            from app.qt.telas import inteligencia
            saude = inteligencia.saude_acervo()
            lista = projetos.listar_projetos()
            return {"saude": saude, "projetos": lista[:6],
                    "total_projetos": len(lista)}

        trab = Trabalhador(_rodar)
        trab.ok.connect(self._visao_geral_chegou)
        self._trabalhos_saude.rodar(trab)

    def _visao_geral_chegou(self, d: dict) -> None:
        s = d.get("saude") or {}
        self._cartoes_numero["produtos"].set_valor(str(s.get("total", 0)))
        self._cartoes_numero["com_foto"].set_valor(
            f"{s.get('pct_foto', 0)}%")
        self._cartoes_numero["edicoes"].set_valor(
            str(d.get("total_projetos", 0)))
        # o próximo evento: o de dia_semana mais perto de hoje (círculo de 7)
        try:
            from datetime import datetime
            com_dia = [e for e in self._eventos()
                       if e.get("dia_semana") is not None]
            if com_dia:
                hoje = datetime.now().weekday()
                prox = min(com_dia,
                           key=lambda e: (e["dia_semana"] - hoje) % 7)
                self._cartoes_numero["evento"].set_valor(prox["nome"])
            else:
                self._cartoes_numero["evento"].set_valor("—")
        except Exception:
            self._cartoes_numero["evento"].set_valor("—")
        for chave, barra in self._barras_saude.items():
            pct = int(s.get(chave, 0))
            barra.setValue(pct)
            barra.setFormat(f"{pct}%")
            # barra SEMÂNTICA: verde saudável, âmbar atenção, vermelho urgente
            cor = (t.SUCESSO if pct >= 80
                   else t.ALERTA if pct >= 50 else t.PERIGO)
            barra.setStyleSheet(
                "QProgressBar::chunk{background:%s;border-radius:4px;}" % cor)
        self._lista_retomar.clear()
        for p in d.get("projetos", []):
            rotulo = (f"{p['nome']}   —   {p['tipo'].title()}"
                      f" · {p['criado_em']}")
            mini = p.get("miniatura")
            ic = (QIcon(mini) if mini
                  else icone("grade" if p["tipo"] == "TABLOIDE"
                             else "impressora", tamanho=16))
            item = QListWidgetItem(ic, rotulo)
            item.setData(Qt.ItemDataRole.UserRole, p["id"])
            self._lista_retomar.addItem(item)

    def _atualizar_saude(self) -> None:
        from app.qt.workers import GerenciadorTrabalhos, Trabalhador
        if not hasattr(self, "_trabalhos_saude"):
            self._trabalhos_saude = GerenciadorTrabalhos()

        def _rodar(_st):
            from app.qt.telas.busca import indicadores_saude
            return indicadores_saude()

        trab = Trabalhador(_rodar)
        trab.ok.connect(self._saude_chegou)
        self._trabalhos_saude.rodar(trab)

    def _saude_chegou(self, d: dict) -> None:
        partes = []
        if d.get("sem_foto"):
            partes.append(f'<a href="sem_foto">{d["sem_foto"]} sem foto</a>')
        if d.get("sem_categoria"):
            partes.append(f'<a href="sem_categoria">{d["sem_categoria"]} '
                          "sem categoria</a>")
        if d.get("backup_horas") is not None:
            partes.append(f'<a href="backup">backup há '
                          f'{d["backup_horas"]}h</a>')
        ia = "ligada" if d.get("ia_ok") else "desligada"
        partes.append(f'<a href="ia">IA local {ia}</a>')
        self._saude_lbl.setText("  ·  ".join(partes))

    def _indicador_clicado(self, chave: str) -> None:
        """Cada indicador leva PARA ONDE RESOLVE (o editor_app navega)."""
        if callable(self.ao_indicador):
            self.ao_indicador(chave)

    def _atualizar_saudacao(self) -> None:
        """Passo 16: saudação pela hora + data por extenso em PT-BR."""
        from datetime import datetime
        agora = datetime.now()
        if 5 <= agora.hour < 12:
            oi = "Bom dia"
        elif 12 <= agora.hour < 18:
            oi = "Boa tarde"
        else:
            oi = "Boa noite"
        self._saudacao.setText(f"{oi}, Otaviano")
        dias = ["segunda-feira", "terça-feira", "quarta-feira",
                "quinta-feira", "sexta-feira", "sábado", "domingo"]
        meses = ["janeiro", "fevereiro", "março", "abril", "maio", "junho",
                 "julho", "agosto", "setembro", "outubro", "novembro",
                 "dezembro"]
        self._data_lbl.setText(
            f"{dias[agora.weekday()]}, {agora.day} de "
            f"{meses[agora.month - 1]} de {agora.year}")

    # --- dados ---------------------------------------------------------------------

    def showEvent(self, event) -> None:      # reflete o que acabou de ser salvo
        self.recarregar()
        self._atualizar_saude()          # FASE 2 (passo 92): só com tela viva
        self._atualizar_visao_geral()    # a aba-painel (worker, nunca no boot)
        super().showEvent(event)

    def recarregar(self) -> None:
        """FASE 1 (passo 43): skeleton pulsante no lugar da coluna enquanto
        os projetos (e as miniaturas, no disco) carregam de verdade.

        Tela invisível (construção, testes) carrega direto — skeleton em
        tela que ninguém vê seria só atraso."""
        if not self.isVisible():
            self._recarregar_agora()
            return
        if getattr(self, "_recarregando", False):
            return
        self._recarregando = True
        while self._coluna.count():
            filho = self._coluna.takeAt(0)
            if filho.widget():
                filho.widget().deleteLater()
        from app.qt.design.componentes import Skeleton
        esqueleto = Skeleton(linhas=3, altura_linha=96)
        self._coluna.addWidget(esqueleto)
        self._coluna.addStretch(1)
        if self.layout() is not None:
            self.layout().activate()
        esqueleto.repaint()              # garante o frame antes da carga
        from PySide6.QtCore import QTimer
        QTimer.singleShot(0, self._recarregar_agora)

    def _recarregar_agora(self) -> None:
        """FASE 2 (Bloco B): home = destaque ("Produzir hoje"/"Esta
        semana") + GRADE de cartões de evento (★ semana antes, Avulsos ao
        fim). A prateleira antiga vive DENTRO da visão do evento."""
        self._recarregando = False
        self._atualizar_saudacao()
        while self._coluna.count():
            filho = self._coluna.takeAt(0)
            if filho.widget():
                filho.widget().deleteLater()

        lista = projetos.listar_projetos()
        eventos = self._eventos()
        self._projetos = lista             # cache da rodada (visão/menus)
        self._resumo.setText(f"{len(lista)} projeto(s) salvos" if lista else "")
        if not lista and not eventos:
            # passo 25: hero de boas-vindas com os 3 cartões-caminho
            from app.qt.design.boas_vindas import _CAMINHOS, cartao_caminho
            hero = EstadoVazio(
                "casa", "Bem-vindo ao AutoTabloide AI",
                "Por onde você quer começar?")
            self._coluna.addWidget(hero)
            linha = QHBoxLayout()
            linha.addStretch(1)
            for nome_ic, rotulo, texto, destino in _CAMINHOS:
                linha.addWidget(cartao_caminho(
                    nome_ic, rotulo, texto,
                    lambda d=destino: self._novo(d)))
                linha.addSpacing(t.ESP_3)
            linha.addStretch(1)
            caixa = QWidget()
            caixa.setLayout(linha)
            self._coluna.addWidget(caixa)
            self._coluna.addStretch(1)
            return

        # --- FASE 2 (passo 47): continuar de onde parei -----------------------
        ultimo = projetos.ultimo_aberto()
        if ultimo is not None:
            faixa = QWidget()
            faixa.setProperty("papel", "cartao")
            faixa.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
            faixa.setCursor(Qt.CursorShape.PointingHandCursor)
            faixa.setToolTip("Reabrir direto de onde você parou")
            faixa.mousePressEvent = (
                lambda _ev, pid=ultimo["id"]:
                self.ao_abrir_projeto(pid)
                if callable(self.ao_abrir_projeto) else None)
            hf = QHBoxLayout(faixa)
            hf.setContentsMargins(t.ESP_3, t.ESP_1, t.ESP_3, t.ESP_1)
            hf.setSpacing(t.ESP_2)
            mini = QLabel()
            if ultimo.get("miniatura"):
                mini.setPixmap(QPixmap(ultimo["miniatura"]).scaled(
                    40, 40, Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation))
            rot = QLabel(f"Continuar de onde parei: "
                         f"<b>{ultimo['nome']}</b>")
            seta = QLabel("→")
            seta.setProperty("papel", "legenda")
            hf.addWidget(mini)
            hf.addWidget(rot, 1)
            hf.addWidget(seta)
            self._coluna.addWidget(faixa)

        # --- destaque (17-18) -------------------------------------------------
        destaque = self._zona_destaque(eventos, lista)
        if destaque is not None:
            self._coluna.addWidget(destaque)
        # FASE 2 (passos 39-41): agenda da semana (7 colunas) — recolhe
        # para a linha de chips quando a semana não tem projeto
        agenda = self._agenda_semana(eventos, lista)
        if agenda is not None:
            self._coluna.addWidget(agenda)

        # --- grade (19/21/22/23) ---------------------------------------------
        linha_titulo = QHBoxLayout()
        titulo_grade = QLabel("SEUS EVENTOS")
        titulo_grade.setProperty("papel", "secao")
        linha_titulo.addWidget(titulo_grade)
        filtro_ev = getattr(self, "_filtro_evento", None)
        if filtro_ev:                    # passo 40: filtro ativo é VISÍVEL
            limpar = QPushButton(f"filtrando: {filtro_ev} ✕")
            limpar.setProperty("tipo", "fantasma")
            limpar.setToolTip("Limpar o filtro do evento")
            limpar.clicked.connect(lambda: self._filtrar_grade(filtro_ev))
            linha_titulo.addWidget(limpar)
        # FASE 2 (passo 42): filtro rápido por STATUS
        linha_titulo.addStretch(1)
        filtro_st = getattr(self, "_filtro_status", None)
        for rotulo, valor in [("Todos", None), ("Rascunhos", "rascunho"),
                              ("Prontos", "pronto"),
                              ("Exportados", "exportado"),
                              ("Publicados", "publicado")]:
            b = QPushButton(rotulo)
            b.setProperty("tipo", "fantasma")
            if valor == filtro_st:
                b.setStyleSheet(f"color: {t.PRIMARIA}; font-weight: 700;")
            b.clicked.connect(
                lambda _=False, v=valor: self._filtrar_status(v))
            linha_titulo.addWidget(b)
        caixa_titulo = QWidget()
        caixa_titulo.setLayout(linha_titulo)
        self._coluna.addWidget(caixa_titulo)
        if filtro_st:
            lista = [p for p in lista
                     if (p.get("status") or "rascunho") == filtro_st]
        if filtro_ev:
            eventos = [e for e in eventos if e["nome"] == filtro_ev]
            lista = [p for p in lista
                     if (p["evento"] or "").strip().lower()
                     == filtro_ev.strip().lower()]
        grade_caixa = QWidget()
        from PySide6.QtWidgets import QGridLayout
        self._grade = QGridLayout(grade_caixa)
        self._grade.setContentsMargins(0, 0, 0, 0)
        self._grade.setSpacing(t.ESP_3)

        por_evento: dict[str, list[dict]] = {}
        for p in lista:
            por_evento.setdefault((p["evento"] or "").strip() or "Avulsos",
                                  []).append(p)

        cartoes: list[QWidget] = []
        semana = [p for p in lista if p.get("criado_ha_dias", 9999) <= 7]
        if semana:                          # passo 21: ★ antes dos eventos
            cartoes.append(self._cartao_semana(semana))
        for ev in eventos:                  # passo 19: um cartão por evento
            cartoes.append(self._cartao_evento(
                ev, por_evento.get(ev["nome"], [])))
        avulsos = por_evento.get("Avulsos", [])
        if avulsos:                         # passo 22: neutro, ao fim
            cartoes.append(self._cartao_avulsos(avulsos))

        self._cartoes = cartoes
        self._fluir_grade()
        self._coluna.addWidget(grade_caixa)
        self._coluna.addStretch(1)
        # passo 31: entrada em cascata (60 ms por cartão; reduzidas = seco)
        if self.isVisible():
            from app.qt.design.animacoes import cascata
            cascata(cartoes)

    def _eventos(self) -> list[dict]:
        try:
            from app.qt.telas.eventos import listar_eventos
            return listar_eventos()
        except Exception:
            return []

    def _fluir_grade(self) -> None:
        """Passo 23: 2 colunas até 1600 px, 3 acima — refluí no resize."""
        if not hasattr(self, "_grade"):
            return
        colunas = 3 if self.width() >= 1600 else 2
        while self._grade.count():
            self._grade.takeAt(0)
        for i, cartao in enumerate(getattr(self, "_cartoes", [])):
            self._grade.addWidget(cartao, i // colunas, i % colunas)
        for c in range(colunas):
            self._grade.setColumnStretch(c, 1)

    def resizeEvent(self, ev) -> None:  # noqa: N802 (Qt)
        super().resizeEvent(ev)
        antes = getattr(self, "_colunas_grade", None)
        agora = 3 if self.width() >= 1600 else 2
        if antes != agora:
            self._colunas_grade = agora
            self._fluir_grade()

    def _cabecalho_evento(self, titulo: str, n: int,
                          destaque: bool = False) -> QWidget:
        """RG-35: cabeçalho com faixa de cor estável por evento + contagem
        + o dia da campanha quando configurado (RG-24)."""
        from app.rendering.secoes import cor_da_categoria
        caixa = QWidget()
        hl = QHBoxLayout(caixa)
        hl.setContentsMargins(0, t.ESP_1, 0, 0)
        hl.setSpacing(t.ESP_2)
        faixa = QLabel()
        cor = t.ALERTA if destaque else cor_da_categoria(titulo)
        faixa.setFixedSize(5, 18)
        faixa.setStyleSheet(f"background: {cor}; border-radius: 2px;")
        rotulo = QLabel(titulo.upper())
        rotulo.setProperty("papel", "secao")
        contagem = QLabel(f"· {n}")
        contagem.setProperty("papel", "legenda")
        hl.addWidget(faixa)
        hl.addWidget(rotulo)
        hl.addWidget(contagem)
        from app.qt.telas.servico import dia_do_evento
        dia = dia_do_evento(titulo)
        if dia is not None:
            nomes = ["segunda", "terça", "quarta", "quinta", "sexta",
                     "sábado", "domingo"]
            lbl_dia = QLabel(f"· toda {nomes[dia]}")
            lbl_dia.setProperty("papel", "legenda")
            hl.addWidget(lbl_dia)
        hl.addStretch(1)
        # FASE 2 (passo 10): botão direito no evento — Renomear · Cor ·
        # Capa · Dia · Notas · Excluir (no cabeçalho até o cartão do B)
        if not destaque:
            caixa.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
            caixa.customContextMenuRequested.connect(
                lambda pos, nm=titulo, w=caixa:
                self._menu_evento(nm, w.mapToGlobal(pos)))
        return caixa

    def _menu_evento(self, nome: str, pos_global) -> None:
        """Menu do evento (passo 10) — opera o serviço de eventos."""
        if nome == "Avulsos":
            return                       # agrupador sintético, não entidade
        from PySide6.QtWidgets import QInputDialog, QMenu

        from app.core.database import Database
        from app.qt.telas import eventos as ev_srv
        db = Database().init()
        try:
            with db.Session() as s:
                ev = next((e for e in ev_srv.listar_eventos(s)
                           if e["nome"].strip().lower()
                           == nome.strip().lower()), None)
                s.commit()
        finally:
            db.engine.dispose()
        if ev is None:
            return

        menu = QMenu(self)
        a_editar = menu.addAction(icone("propriedades", tamanho=16),
                                  "Editar (nome · cor · dia · capa)…")
        a_notas = menu.addAction(icone("texto", tamanho=16), "Notas…")
        # FASE 2 (passo 97): o gesto nº 1 também mora no cartão do evento
        a_dup_semana = menu.addAction(icone("duplicar", tamanho=16),
                                      "Duplicar semana passada")
        # FASE 2 (passo 93): tela cheia para o pai aprovar
        a_apresentar = menu.addAction(icone("olho", tamanho=16),
                                      "Modo apresentação")
        menu.addSeparator()
        a_del = menu.addAction(icone("lixeira", tamanho=16), "Excluir…")
        escolha = menu.exec(pos_global)
        if escolha is None:
            return
        if escolha is a_dup_semana:      # passo 97
            self._duplicar_semana(ev)
            return
        if escolha is a_apresentar:      # passo 93: fora da sessão de banco
            from app.qt.telas.apresentacao import (
                ApresentacaoDialog, pecas_do_evento)
            dlg = ApresentacaoDialog(nome, pecas_do_evento(nome),
                                     parent=self)
            dlg.abrir_tela_cheia()
            dlg.exec()
            return
        db = Database().init()
        try:
            with db.Session() as s:
                if escolha is a_editar:
                    from app.qt.telas.evento_dialog import EventoDialog
                    dlg = EventoDialog(self, nome=ev["nome"], cor=ev["cor"],
                                       dia_semana=ev["dia_semana"],
                                       titulo="Salvar evento")
                    if dlg.exec() != EventoDialog.DialogCode.Accepted:
                        return
                    novo_nome, cor, dia, capa = dlg.valores()
                    if novo_nome != ev["nome"]:
                        ev_srv.renomear_evento(s, ev["id"], novo_nome)
                    ev_srv.mudar_cor(s, ev["id"], cor)
                    ev_srv.definir_dia(s, ev["id"], dia)
                    if capa:
                        ev_srv.definir_capa(s, ev["id"], capa)
                elif escolha is a_notas:
                    texto, ok = QInputDialog.getMultiLineText(
                        self, f"Notas de “{ev['nome']}”",
                        "Lembretes do evento (ex.: “quinta que vem é "
                        "feriado”):", ev["notas"])
                    if not ok:
                        return
                    ev_srv.definir_notas(s, ev["id"], texto)
                elif escolha is a_del:
                    self._excluir_evento(s, ev)
                s.commit()
        finally:
            db.engine.dispose()
        self.recarregar()

    def _excluir_evento(self, s, ev: dict) -> None:
        """Passo 6 na UI: vazio exclui com verbo; com projetos, escolhe o
        evento de destino — nunca órfão em silêncio."""
        from PySide6.QtWidgets import QInputDialog

        from app.core.models import ProjetoSalvo
        from app.qt.design.componentes import confirmar_destrutivo
        from app.qt.telas import eventos as ev_srv
        n = (s.query(ProjetoSalvo)
             .filter_by(evento_id=ev["id"]).count())
        if n == 0:
            if confirmar_destrutivo(
                    self, "Excluir evento",
                    f"“{ev['nome']}” está vazio e será removido.",
                    "Excluir evento"):
                ev_srv.excluir_evento(s, ev["id"])
            return
        outros = [e for e in ev_srv.listar_eventos(s)
                  if e["id"] != ev["id"]]
        if not outros:
            mostrar_toast(self, "Crie outro evento antes — os "
                                f"{n} projeto(s) precisam de um destino.",
                          tipo="erro")
            return
        nomes = [e["nome"] for e in outros]
        destino, ok = QInputDialog.getItem(
            self, "Excluir evento",
            f"“{ev['nome']}” tem {n} projeto(s). Mover para:",
            nomes, 0, False)
        if not ok:
            return
        alvo = next(e for e in outros if e["nome"] == destino)
        if confirmar_destrutivo(
                self, "Excluir evento",
                f"Os {n} projeto(s) vão para “{destino}” e "
                f"“{ev['nome']}” será removido.",
                f"Mover {n} e excluir"):
            ev_srv.excluir_evento(s, ev["id"], mover_para=alvo["id"])

    def _eventos_extras(self) -> list[str]:
        """FASE 2: eventos (ENTIDADES) ainda sem projeto — a prateleira
        vazia continua visível até o Início novo do Bloco B assumir.
        A migração dos `eventos.extras` antigos acontece no listar."""
        try:
            from app.core import projetos as proj
            from app.qt.telas.eventos import listar_eventos
            evs = listar_eventos()
            com_projeto = {(p["evento"] or "").strip().lower()
                           for p in proj.listar_projetos()}
            return [e["nome"] for e in evs
                    if e["nome"].strip().lower() not in com_projeto]
        except Exception:
            return []

    def _novo_evento(self) -> None:
        """FASE 2 (passo 9): o evento nasce ENTIDADE — nome, cor da paleta,
        dia da campanha e capa opcionais (era um texto solto na Config)."""
        from app.qt.telas.evento_dialog import EventoDialog
        dlg = EventoDialog(self)
        if dlg.exec() != EventoDialog.DialogCode.Accepted:
            return
        nome, cor, dia, capa = dlg.valores()
        from app.core.database import Database
        from app.qt.telas.eventos import criar_evento, definir_capa
        db = Database().init()
        try:
            with db.Session() as s:
                ev = criar_evento(s, nome, cor=cor, dia_semana=dia)
                if capa:
                    definir_capa(s, ev.id, capa)
                s.commit()
        finally:
            db.engine.dispose()
        self.recarregar()

    # --- FASE 2, Bloco B: destaque, cartões e a visão do evento ---------------

    def _zona_destaque(self, eventos: list[dict],
                       lista: list[dict]):
        """Passos 17-18: 'Produzir hoje' no dia da campanha; senão 'Esta
        semana' com chips dos próximos dias com evento."""
        from datetime import date
        hoje = date.today().weekday()
        de_hoje = [e for e in eventos if e.get("dia_semana") == hoje]
        if de_hoje:
            ev = de_hoje[0]
            caixa = QWidget()
            caixa.setProperty("papel", "cartao")
            caixa.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
            hl = QHBoxLayout(caixa)
            hl.setContentsMargins(t.ESP_4, t.ESP_3, t.ESP_4, t.ESP_3)
            hl.setSpacing(t.ESP_3)
            faixa = QLabel()
            faixa.setFixedSize(6, 44)
            faixa.setStyleSheet(
                f"background: {ev['cor']}; border-radius: 3px;")
            # FASE 2 (passo 52): a NOTA do evento aparece na hora certa
            texto_destaque = f"<b>Produzir hoje:</b> {ev['nome']}"
            if (ev.get("notas") or "").strip():
                nota = ev["notas"].strip().splitlines()[0]
                texto_destaque += (f'<br><span style="color:{t.ALERTA}">'
                                   f"✎ {nota}</span>")
            rotulo = QLabel(texto_destaque)
            btn_dup = QPushButton(" Duplicar semana passada")
            btn_dup.setIcon(icone("duplicar", cor=t.ACENTO_TEXTO, tamanho=16))
            btn_dup.setProperty("tipo", "primario")
            btn_dup.setToolTip("Clona o último projeto do evento como "
                               "rascunho de hoje — só trocar os preços")
            btn_dup.clicked.connect(lambda: self._duplicar_semana(ev))
            btn_zero = QPushButton("Começar do zero")
            btn_zero.clicked.connect(lambda: self._novo("mesa"))
            hl.addWidget(faixa)
            hl.addWidget(rotulo, 1)
            hl.addWidget(btn_dup)
            hl.addWidget(btn_zero)
            return caixa
        return None                      # a agenda (39-41) cuida da semana

    def _agenda_semana(self, eventos: list[dict], lista: list[dict]):
        """Passo 39: 7 colunas dom–sáb com os eventos nos seus dias e os
        chips dos projetos da SEMANA CORRENTE; passo 40: clicar filtra a
        grade; passo 41: semana sem projeto recolhe para a linha de chips."""
        from datetime import date
        com_dia = [e for e in eventos if e.get("dia_semana") is not None]
        if not com_dia:
            return None
        hoje = date.today().weekday()
        semana = [p for p in lista if p.get("criado_ha_dias", 9999) <= 6]
        por_evento_semana: dict[str, list[dict]] = {}
        for p in semana:
            chave = (p["evento"] or "").strip().lower()
            por_evento_semana.setdefault(chave, []).append(p)
        tem_projeto = any(
            por_evento_semana.get(e["nome"].strip().lower())
            for e in com_dia)
        if not tem_projeto:
            return self._linha_chips_semana(com_dia, hoje)   # passo 41

        caixa = QWidget()
        caixa.setProperty("papel", "cartao")
        caixa.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        hl = QHBoxLayout(caixa)
        hl.setContentsMargins(t.ESP_3, t.ESP_2, t.ESP_3, t.ESP_2)
        hl.setSpacing(t.ESP_2)
        nomes_curto = ["seg", "ter", "qua", "qui", "sex", "sáb", "dom"]
        # colunas na ordem do calendário PT-BR: dom → sáb
        for dia in [6, 0, 1, 2, 3, 4, 5]:
            col = QVBoxLayout()
            col.setSpacing(2)
            rot = QLabel(nomes_curto[dia].upper())
            rot.setProperty("papel", "legenda")
            if dia == hoje:
                rot.setStyleSheet(
                    f"color: {t.PRIMARIA}; font-weight: 700;")
                rot.setText(f"{nomes_curto[dia].upper()} · hoje")
            col.addWidget(rot)
            for ev in [e for e in com_dia if e["dia_semana"] == dia]:
                btn = QPushButton(ev["nome"])
                btn.setProperty("tipo", "fantasma")
                btn.setStyleSheet(
                    f"color: {ev['cor']}; font-weight: 600; text-align: left;")
                btn.clicked.connect(
                    lambda _=False, nm=ev["nome"]: self._filtrar_grade(nm))
                col.addWidget(btn)
                for p in por_evento_semana.get(
                        ev["nome"].strip().lower(), [])[:3]:
                    chip = QLabel(f"· {p['nome']}")
                    chip.setProperty("papel", "legenda")
                    chip.setToolTip(f"{p['nome']} — status: "
                                    f"{p.get('status') or 'rascunho'}")
                    col.addWidget(chip)
            col.addStretch(1)
            hl.addLayout(col, 1)
        return caixa

    def _linha_chips_semana(self, com_dia: list[dict], hoje: int):
        nomes_dias = ["seg", "ter", "qua", "qui", "sex", "sáb", "dom"]
        caixa = QWidget()
        hl = QHBoxLayout(caixa)
        hl.setContentsMargins(0, 0, 0, 0)
        hl.setSpacing(t.ESP_2)
        rot = QLabel("Esta semana:")
        rot.setProperty("papel", "legenda")
        hl.addWidget(rot)
        proximos = sorted(com_dia,
                          key=lambda e: (e["dia_semana"] - hoje) % 7)
        for ev in proximos[:5]:
            chip = QPushButton(
                f"{nomes_dias[ev['dia_semana']]} · {ev['nome']}")
            chip.setProperty("tipo", "fantasma")
            chip.setStyleSheet(f"color: {ev['cor']}; font-weight: 600;")
            chip.clicked.connect(
                lambda _=False, e=ev: self._abrir_evento_por_nome(e["nome"]))
            hl.addWidget(chip)
        hl.addStretch(1)
        return caixa

    def _duplicar_semana(self, ev: dict) -> None:
        """FASE 2 (passo 97 — R-009): o gesto nº 1 da rotina — clona o
        último projeto do evento como rascunho de hoje e ABRE na Mesa."""
        from app.qt.design.carregando import cursor_espera
        with cursor_espera():
            novo = projetos.duplicar_semana_passada(ev["nome"])
        if novo is None:
            mostrar_toast(self, f"“{ev['nome']}” ainda não tem projeto "
                                "para duplicar — comece do zero.",
                          tipo="erro")
            return
        projetos.registrar_ultimo_aberto(novo)
        if callable(self.ao_abrir_projeto):
            self.ao_abrir_projeto(novo)
        mostrar_toast(self, "Duplicado! Troque os preços pelo duplo-clique "
                            "— modo planilha vem na Fase 7.")

    # --- FASE 2, Bloco F: busca global no Início ------------------------------

    def _buscar_global(self) -> None:
        texto = self.campo_busca.text().strip()
        if len(texto) < 2:               # passo 75: <2 letras não dispara
            self._dropdown.hide()
            return
        from app.qt.design.paleta_comandos import popular_resultados
        from app.qt.telas.busca import buscar_global
        popular_resultados(self._dropdown, buscar_global(texto))
        pos = self.campo_busca.mapToGlobal(
            self.campo_busca.rect().bottomLeft())
        self._dropdown.setFixedWidth(
            max(self.campo_busca.width(), 380))
        altura = min(self._dropdown.count(), 12) * 26 + 8
        self._dropdown.setFixedHeight(max(altura, 40))
        self._dropdown.move(pos)
        self._dropdown.show()
        self._dropdown.raise_()

    def _buscar_enter(self) -> None:
        """Enter abre o PRIMEIRO resultado selecionável (passo 73)."""
        for i in range(self._dropdown.count()):
            item = self._dropdown.item(i)
            if item.flags() & Qt.ItemFlag.ItemIsEnabled:
                self._resultado_clicado(item)
                return

    def _resultado_clicado(self, item) -> None:
        par = item.data(Qt.ItemDataRole.UserRole)
        self._dropdown.hide()
        if par is None:
            return
        tipo, dado = par
        if tipo == "projetos":
            if callable(self.ao_abrir_projeto):
                self.ao_abrir_projeto(dado["id"])
        elif callable(self.ao_resultado_busca):
            self.ao_resultado_busca(tipo, dado)
        else:                            # sem navegação ligada: avisa
            mostrar_toast(self, f"“{dado['nome']}” — abra a tela "
                                f"correspondente para ver.", tipo="info")

    def hideEvent(self, ev) -> None:  # noqa: N802 — dropdown nunca órfão
        self._dropdown.hide()
        super().hideEvent(ev)

    def _filtrar_grade(self, nome_evento: str) -> None:
        """Passo 40: clique num dia da agenda filtra a grade para o evento
        (um chip 'limpar' desfaz); clicar de novo no mesmo, limpa."""
        atual = getattr(self, "_filtro_evento", None)
        self._filtro_evento = (None if atual == nome_evento else nome_evento)
        self.recarregar()

    def _filtrar_status(self, status: str | None) -> None:
        """Passo 42: Todos · Rascunhos · Prontos · Exportados · Publicados."""
        self._filtro_status = status
        self.recarregar()

    def _cor_status(self, status: str) -> str:
        # OS F11.5 #6: "publicado" vem do TOKEN tematizado (era hex solto —
        # bypass do design system; no escuro o violeta clareia junto)
        return {"rascunho": t.TEXTO_3, "pronto": t.PRIMARIA,
                "exportado": t.SUCESSO,
                "publicado": t.PUBLICADO}.get(status, t.TEXTO_3)

    def _capa_pixmap(self, ev: dict, itens: list[dict]) -> QPixmap:
        """Capa definida > miniatura do projeto mais recente (passo 8)."""
        from app.qt.telas.eventos import caminho_capa
        caminho = caminho_capa(ev.get("capa"))
        if caminho is None and itens:
            mini = itens[0].get("miniatura")
            caminho = mini if mini else None
        return QPixmap(str(caminho)) if caminho else QPixmap()

    def _montar_cartao(self, titulo: str, cor: str, capa: QPixmap,
                       legenda: str, extra: str, ao_abrir,
                       menu_evento: str | None = None) -> QWidget:
        """FASE 3 (RG-59): capa em COVER cheia com overlay — os textos
        viram chips translúcidos sobre a imagem."""
        chips = [legenda, extra]
        cartao = _CartaoCapa(titulo, cor, capa, chips, ao_abrir)
        if menu_evento:                    # menu do evento (F2 passo 10)
            cartao.setContextMenuPolicy(
                Qt.ContextMenuPolicy.CustomContextMenu)
            cartao.customContextMenuRequested.connect(
                lambda pos, nm=menu_evento, w=cartao:
                self._menu_evento(nm, w.mapToGlobal(pos)))
        return cartao

    def _resumo_projetos(self, itens: list[dict]) -> str:
        if not itens:
            return "nenhum projeto ainda"
        ultimo = itens[0].get("criado_em", "")
        return f"{len(itens)} projeto(s) · último em {ultimo}"

    def _cartao_evento(self, ev: dict, itens: list[dict]) -> QWidget:
        nomes_dias = ["toda segunda", "toda terça", "toda quarta",
                      "toda quinta", "toda sexta", "todo sábado",
                      "todo domingo"]
        extra = (nomes_dias[ev["dia_semana"]]
                 if ev.get("dia_semana") is not None else "")
        # FASE 2 (passo 51): ícone de nota quando há texto (clique abre)
        if (ev.get("notas") or "").strip():
            extra = (extra + "   " if extra else "") + "✎ tem nota"
        cartao = self._montar_cartao(
            ev["nome"], ev["cor"], self._capa_pixmap(ev, itens),
            self._resumo_projetos(itens), extra,
            lambda nm=ev["nome"]: self._abrir_evento_por_nome(nm),
            menu_evento=ev["nome"])
        if (ev.get("notas") or "").strip():
            cartao.setToolTip(f"Notas de {ev['nome']}:\n{ev['notas']}")
        return cartao

    def _cartao_semana(self, semana: list[dict]) -> QWidget:
        capa = QPixmap(semana[0]["miniatura"]) if semana[0].get(
            "miniatura") else QPixmap()
        return self._montar_cartao(
            "★ Ofertas da semana", t.ALERTA, capa,
            f"{len(semana)} projeto(s) nos últimos 7 dias", "",
            lambda: self._abrir_visao("★ Ofertas da semana", t.ALERTA,
                                      semana))

    def _cartao_avulsos(self, avulsos: list[dict]) -> QWidget:
        capa = QPixmap(avulsos[0]["miniatura"]) if avulsos[0].get(
            "miniatura") else QPixmap()
        return self._montar_cartao(
            "Avulsos", t.BORDA_FORTE, capa,
            self._resumo_projetos(avulsos), "",
            lambda: self._abrir_visao("Avulsos", t.BORDA_FORTE, avulsos))

    def _abrir_evento_por_nome(self, nome: str) -> None:
        itens = [p for p in getattr(self, "_projetos", [])
                 if (p["evento"] or "").strip().lower()
                 == nome.strip().lower()]
        ev = next((e for e in self._eventos()
                   if e["nome"].strip().lower() == nome.strip().lower()),
                  None)
        cor = ev["cor"] if ev else t.BORDA_FORTE
        self._abrir_visao(nome, cor, itens, nome_evento=nome)

    def _abrir_visao(self, titulo: str, cor: str, itens: list[dict],
                     nome_evento: str | None = None) -> None:
        """Passo 20: a prateleira antiga, agora POR DENTRO do cartão."""
        while self._visao_lay.count():
            filho = self._visao_lay.takeAt(0)
            if filho.widget():
                filho.widget().deleteLater()
        topo = QHBoxLayout()
        topo.setSpacing(t.ESP_2)
        voltar = QPushButton(" Início")
        voltar.setIcon(icone("seta_cima", tamanho=14))
        voltar.setProperty("tipo", "fantasma")
        voltar.clicked.connect(lambda: self._pilha.setCurrentIndex(0))
        faixa = QLabel()
        faixa.setFixedSize(5, 18)
        faixa.setStyleSheet(f"background: {cor}; border-radius: 2px;")
        rotulo = QLabel(titulo.upper())
        rotulo.setProperty("papel", "secao")
        contagem = QLabel(f"· {len(itens)}")
        contagem.setProperty("papel", "legenda")
        topo.addWidget(voltar)
        topo.addSpacing(t.ESP_2)
        topo.addWidget(faixa)
        topo.addWidget(rotulo)
        topo.addWidget(contagem)
        topo.addStretch(1)
        caixa_topo = QWidget()
        caixa_topo.setLayout(topo)
        if nome_evento:
            caixa_topo.setContextMenuPolicy(
                Qt.ContextMenuPolicy.CustomContextMenu)
            caixa_topo.customContextMenuRequested.connect(
                lambda pos, nm=nome_evento, w=caixa_topo:
                self._menu_evento(nm, w.mapToGlobal(pos)))
        self._visao_lay.addWidget(caixa_topo)
        if itens:
            self._visao_lay.addWidget(self._prateleira(itens, grade=True), 1)
        else:
            self._visao_lay.addWidget(EstadoVazio(
                "caixa", "Nenhum projeto neste evento",
                "Salve um projeto com este evento na Mesa\n"
                "ou mova um existente (botão direito → Mover)."), 1)
        self._pilha.setCurrentIndex(1)

    def _prateleira(self, itens: list[dict], grade: bool = False) -> QListWidget:
        """``grade=True`` (visão do evento): quebra linha e preenche a
        altura; False: a faixa horizontal clássica."""
        lista = QListWidget()
        lista.setViewMode(QListWidget.ViewMode.IconMode)
        lista.setMovement(QListWidget.Movement.Static)   # RG-10: sem drag
        lista.setFlow(QListWidget.Flow.LeftToRight)
        lista.setWrapping(grade)
        lista.setIconSize(QSize(_MINIATURA, _MINIATURA))
        lista.setSpacing(t.ESP_2)
        if not grade:
            lista.setFixedHeight(_MINIATURA + 74)
        lista.setResizeMode(QListWidget.ResizeMode.Adjust)
        lista.setHorizontalScrollMode(QListWidget.ScrollMode.ScrollPerPixel)
        lista.setItemDelegate(_DelegateProjeto(lista, self._cor_status))
        lista.itemDoubleClicked.connect(self._abrir)   # passo 27: preservado
        lista.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        lista.customContextMenuRequested.connect(
            lambda pos, li=lista: self._menu(li, pos))
        # FASE 2 (passo 49): favoritos SOBEM dentro do evento (só exibição)
        itens = sorted(itens, key=lambda p: not p.get("favorito"))
        for p in itens:
            item = QListWidgetItem(f'{p["nome"]}\n{p["tipo"].title()} · {p["criado_em"]}')
            item.setData(Qt.ItemDataRole.UserRole, p)
            pm = QPixmap(p["miniatura"]) if p["miniatura"] else QPixmap()
            if pm.isNull():
                item.setIcon(icone(_ICONE_TIPO.get(p["tipo"], "grade"), tamanho=48))
            else:
                item.setIcon(QIcon(pm.scaled(
                    _MINIATURA, _MINIATURA, Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation)))
            status = p.get("status") or "rascunho"
            explica = {
                "rascunho": "ainda em edição",
                "pronto": "conferido — pronto para exportar",
                "exportado": "PNG/PDF gerado",
                "publicado": "enviado (WhatsApp/impresso) — gesto seu",
            }.get(status, "")
            item.setToolTip(f'{p["nome"]} — abrir idêntico (congelado)\n'
                            f"Status: {status} ({explica})")
            lista.addItem(item)
        return lista

    # --- ações ------------------------------------------------------------------------

    def _novo(self, destino: str) -> None:
        if callable(self.ao_novo):
            self.ao_novo(destino)

    def _entrar_modo_pai(self) -> None:
        """R-150: entra no Modo Pai e LEMBRA a escolha (o próximo boot já
        abre nele — o PC da loja nasce simples)."""
        from app.qt.telas.modo_pai import lembrar_modo_pai
        lembrar_modo_pai(True)
        if callable(self.ao_novo):
            self.ao_novo("modo_pai")

    def _abrir(self, item: QListWidgetItem) -> None:
        p = item.data(Qt.ItemDataRole.UserRole)
        if callable(self.ao_abrir_projeto):
            self.ao_abrir_projeto(p["id"])

    def _menu(self, lista: QListWidget, pos) -> None:
        item = lista.itemAt(pos)
        if item is None:
            return
        p = item.data(Qt.ItemDataRole.UserRole)
        menu = QMenu(self)
        a_abrir = menu.addAction(icone("abrir", tamanho=16), "Abrir")
        a_dup = menu.addAction(icone("duplicar", tamanho=16),
                               "Duplicar (nova edição)")
        a_ren = menu.addAction(icone("texto", tamanho=16), "Renomear…")
        # FASE 2 (passo 49): favoritar (a ★ sobe o projeto no evento)
        fav = bool(p.get("favorito"))
        a_fav = menu.addAction("★ Tirar dos favoritos" if fav
                               else "★ Favoritar")
        # FASE 2 (passo 37): pronto/publicado são GESTOS HUMANOS (publicado
        # = "enviei no WhatsApp"); exportado é automático no exportar
        status = p.get("status") or "rascunho"
        a_pronto = menu.addAction(icone("check_circulo", tamanho=16),
                                  "Marcar como pronto")
        a_pronto.setEnabled(status != "pronto")
        a_publicado = menu.addAction(icone("check_circulo", tamanho=16),
                                     "Marcar como publicado")
        a_publicado.setEnabled(status != "publicado")
        # FASE 2 (passo 60): a linha do tempo de versões
        a_versoes = menu.addAction(icone("restaurar", tamanho=16),
                                   "Versões…")
        # FASE 2 (passo 28): mover o projeto para outro evento
        sub_mover = menu.addMenu(icone("cofre", tamanho=16),
                                 "Mover para evento…")
        eventos = self._eventos()
        acoes_mover = {}
        for ev in eventos:
            if ev["nome"].strip().lower() != (p["evento"] or "").strip().lower():
                acoes_mover[sub_mover.addAction(ev["nome"])] = ev["id"]
        if p["evento"]:
            acoes_mover[sub_mover.addAction("(sem evento — Avulsos)")] = None
        menu.addSeparator()
        a_del = menu.addAction(icone("lixeira", tamanho=16), "Excluir")
        escolha = menu.exec(lista.mapToGlobal(pos))
        if escolha is a_versoes:
            from app.qt.telas.versoes_dialog import VersoesDialog
            dlg = VersoesDialog(p["id"], p["nome"], parent=self)
            dlg.exec()
            if dlg.novo_id is not None:
                projetos.registrar_ultimo_aberto(dlg.novo_id)
                self.recarregar()
            return
        if escolha is a_fav:
            projetos.marcar_favorito(p["id"], not fav)
            self.recarregar()
            return
        if escolha is a_pronto or escolha is a_publicado:
            projetos.marcar_status(
                p["id"], "pronto" if escolha is a_pronto else "publicado")
            self.recarregar()
            return
        if escolha in acoes_mover:
            from app.core.database import Database
            from app.qt.telas.eventos import mover_projeto
            db = Database().init()
            try:
                with db.Session() as s:
                    mover_projeto(s, p["id"], acoes_mover[escolha])
                    s.commit()
            finally:
                db.engine.dispose()
            self.recarregar()
            return
        if escolha == a_abrir:
            self._abrir(item)
        elif escolha == a_dup:
            nome, ok = QInputDialog.getText(
                self, "Duplicar projeto", "Nome da nova edição:",
                text=f'{p["nome"]} (nova)')
            if ok and nome.strip():
                novo = projetos.duplicar_projeto(p["id"], nome.strip())
                if novo is not None:     # FASE 2 (passo 48): 4º caminho
                    projetos.registrar_ultimo_aberto(novo)
                self.recarregar()
        elif escolha == a_ren:
            nome, ok = QInputDialog.getText(self, "Renomear", "Novo nome:",
                                            text=p["nome"])
            if ok and nome.strip():
                projetos.renomear_projeto(p["id"], nome.strip())
                self.recarregar()
        elif escolha == a_del:
            from app.qt.design.componentes import confirmar_destrutivo
            if confirmar_destrutivo(              # passo 78: verbo no botão
                    self, "Excluir projeto",
                    f'“{p["nome"]}” será apagado. Não tem volta.',
                    "Excluir projeto"):
                projetos.excluir_projeto(p["id"])
                self.recarregar()


class _CartaoIndicador(QWidget):
    """Cartão de número da Visão geral: chip de ícone COLORIDO + número
    grande + rótulo. Pintado à mão lendo os tokens NA HORA (acompanha o
    tema claro/escuro sem stylesheet fixo). Clicável (cursor de mão)."""

    def __init__(self, rotulo: str, nome_icone: str, cor_chave: str,
                 ao_clicar=None, parent=None):
        super().__init__(parent)
        self._rotulo = rotulo
        self._nome_icone = nome_icone
        self._cor_chave = cor_chave          # nome do token (ex.: "SUCESSO")
        self._valor = "—"
        self._ao_clicar = ao_clicar
        self._hover = False
        self.setMinimumHeight(84)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setToolTip(f"{rotulo} — clique para abrir")

    def set_valor(self, valor: str) -> None:
        self._valor = valor or "—"
        self.update()

    # o rótulo/valor p/ testes (paridade com QLabel.text())
    def text(self) -> str:
        return self._valor

    def mousePressEvent(self, ev) -> None:  # noqa: N802 (Qt)
        if callable(self._ao_clicar):
            self._ao_clicar()

    def enterEvent(self, ev) -> None:  # noqa: N802 (Qt)
        self._hover = True
        self.update()

    def leaveEvent(self, ev) -> None:  # noqa: N802 (Qt)
        self._hover = False
        self.update()

    def paintEvent(self, ev) -> None:  # noqa: N802 (Qt)
        from PySide6.QtCore import QRectF
        from PySide6.QtGui import QFont, QPainter

        cor = QColor(getattr(t, self._cor_chave, t.PRIMARIA))
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        r = QRectF(0.5, 0.5, self.width() - 1, self.height() - 1)
        fundo = QColor(t.SUPERFICIE)
        if self._hover:
            fundo = QColor(t.SUPERFICIE_2)
        p.setPen(QColor(t.BORDA))
        p.setBrush(fundo)
        p.drawRoundedRect(r, t.RAIO_CARTAO, t.RAIO_CARTAO)
        # a barrinha viva no topo (a cor do assunto)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(cor)
        p.drawRoundedRect(QRectF(1, 1, self.width() - 2, 4), 2, 2)
        # chip do ícone
        lado = 36
        cx, cy = t.ESP_3, (self.height() - lado) // 2 + 2
        chip = QColor(cor)
        chip.setAlpha(36)
        p.setBrush(chip)
        p.drawRoundedRect(QRectF(cx, cy, lado, lado), 9, 9)
        icone(self._nome_icone, cor=cor.name(), tamanho=20).paint(
            p, cx + 8, cy + 8, 20, 20)
        # número grande + rótulo
        x_txt = cx + lado + t.ESP_3
        p.setPen(QColor(t.TEXTO))
        f = QFont(t.FONTE_UI[0])
        f.setPointSizeF(t.TAM_TITULO + 3)
        f.setWeight(QFont.Weight.Bold)
        p.setFont(f)
        p.drawText(QRectF(x_txt, cy - 4, self.width() - x_txt - 8, lado * 0.62),
                   Qt.AlignmentFlag.AlignVCenter, self._valor)
        p.setPen(QColor(t.TEXTO_3))
        f2 = QFont(t.FONTE_UI[0])
        f2.setPointSizeF(t.TAM_LEGENDA + 0.5)
        p.setFont(f2)
        p.drawText(QRectF(x_txt, cy + lado * 0.55, self.width() - x_txt - 8,
                          lado * 0.5),
                   Qt.AlignmentFlag.AlignVCenter, self._rotulo)
        p.end()


class EventosTela(QWidget):
    """A aba EVENTOS (auditoria do dono, 20/07): os grupos de ofertas — a
    grade de campanhas + prateleiras + visão do evento — que moravam no
    Início. Esta tela ADOTA a `_pilha` do Dashboard: são os MESMOS objetos e
    os mesmos métodos (nenhum fluxo/teste do dashboard muda), só a casa é
    outra. "Novo evento" mora aqui (onde as campanhas vivem)."""

    def __init__(self, dash: DashboardTela, parent=None):
        super().__init__(parent)
        self._dash = dash

        barra = QWidget()
        barra.setObjectName("barraFerramentas")
        hb = QHBoxLayout(barra)
        hb.setContentsMargins(t.ESP_4, t.ESP_2, t.ESP_4, t.ESP_2)
        hb.setSpacing(t.ESP_2)
        titulo = QLabel("Ofertas por evento")
        titulo.setProperty("papel", "titulo")
        # R-148 (FASE 12): o lembrete LOCAL das datas comemorativas — some
        # com a chave `calendario.lembretes` desligada (nunca intrusivo)
        self.lembrete_datas = QLabel("")
        self.lembrete_datas.setProperty("papel", "legenda")
        btn_calendario = QPushButton(" Calendário do ano…")
        btn_calendario.setIcon(icone("calendario", tamanho=16))
        btn_calendario.setToolTip(
            "As datas que movem o varejo (Páscoa, Dia das Mães, Black "
            "Friday…) — cada uma vira um evento com um clique")
        btn_calendario.clicked.connect(self._abrir_calendario)
        novo_evt = QPushButton(" Novo evento")
        novo_evt.setIcon(icone("calendario", cor=t.ACENTO_TEXTO, tamanho=16))
        novo_evt.setProperty("tipo", "primario")
        novo_evt.setToolTip("Cria a campanha (“Quintou”, “Sexta Verde”…) "
                            "com cor, dia da semana e capa")
        novo_evt.clicked.connect(dash._novo_evento)
        hb.addWidget(titulo)
        hb.addWidget(self.lembrete_datas)
        hb.addStretch(1)
        hb.addWidget(btn_calendario)
        hb.addWidget(novo_evt)

        raiz = QVBoxLayout(self)
        raiz.setContentsMargins(0, 0, 0, 0)
        raiz.setSpacing(0)
        raiz.addWidget(barra)
        raiz.addWidget(dash._pilha, 1)     # adota a pilha (reparent)
        dash._pilha.show()                 # (nascia oculta no dashboard)

    def showEvent(self, event) -> None:  # noqa: N802 (Qt)
        # o dashboard está oculto quando esta aba abre → recarrega direto
        # (o guard de skeleton dele já resolve isso sozinho)
        self._dash.recarregar()
        self._atualizar_lembrete_datas()
        super().showEvent(event)

    def _atualizar_lembrete_datas(self) -> None:
        """R-148: “Vem aí: Dia dos Pais (10/08, faltam 20 dias)” — local e
        desligável; falha de leitura só silencia o lembrete."""
        try:
            from app.core import calendario
            if not calendario.lembretes_ligados():
                self.lembrete_datas.setText("")
                return
            proximas = calendario.proximas_datas(dias=30)
            if not proximas:
                self.lembrete_datas.setText("")
                return
            d = proximas[0]
            quando = d["data"].strftime("%d/%m")
            falta = ("é HOJE" if d["faltam"] == 0
                     else f"faltam {d['faltam']} dia(s)")
            self.lembrete_datas.setText(
                f"  ·  Vem aí: {d['nome']} ({quando}, {falta})")
        except Exception:
            self.lembrete_datas.setText("")

    def _abrir_calendario(self) -> None:
        """R-148: o calendário promocional do ano — criar o evento é 1 clique."""
        from app.qt.telas.calendario_dialog import CalendarioDialog
        dlg = CalendarioDialog(self)
        dlg.exec()
        self._dash.recarregar()            # o evento novo aparece na hora
        self._atualizar_lembrete_datas()
